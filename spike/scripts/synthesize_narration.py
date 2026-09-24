"""Synthesise every utterance of a page's narration with Cartesia Sonic 3.6,
under the pronunciation lexicon, with a phoneme check on every lexicon term.

    .venv/Scripts/python spike/scripts/synthesize_narration.py <lesson_dir> --page 13 \
        [--speed 0.6] [--accept-terms]

Reads:  <lesson_dir>/analysis/narration/page-<N>/narration.json
        <lesson_dir>/generated/page-<N>/boards/terms_check.json   (check_terms.py, fresh)
        spike/lexicon.json
Writes: <lesson_dir>/generated/page-<N>/boards/audio/*.wav
        <lesson_dir>/generated/page-<N>/boards/audio_index.json

Pronunciation (methodology §20):
  - The lexicon file is the source of truth. The build refuses to run unless
    the Cartesia dictionary equals it (lexicon.require_synced), and every
    index entry records the lexicon version and the terms it applied, which
    check_board_page.py verifies: audio synthesised without the lexicon fails
    the build.
  - The cache key includes the lexicon entries the utterance contains, so
    changing a pronunciation re-synthesises exactly the utterances with that
    term, and nothing else.
  - Every synthesis asks Cartesia for phoneme timestamps, and every lexicon
    term in the utterance is checked against its expected phoneme pattern.
    A term whose alias did not take effect fails the build with the
    utterance id. This is the fine instrument for a vowel; ear.py is the
    coarse one, by transcription.
  - The page's new terms must have been heard first (check_terms.py): the
    build refuses without a terms check newer than the narration and with no
    failures, unless --accept-terms says the maintainer has seen them.

The voice, model, SSE call and WAV writing are shared with synthesize_audio.py.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from cartesia import Cartesia

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lexicon                                                        # noqa: E402
import paths                                                          # noqa: E402
from synthesize_audio import (MODEL_ID, SAMPLE_RATE, VOICE_ID, VOICE_NAME,  # noqa: E402
                              api_key, write_wav)
from write_narration import spoken                                    # noqa: E402


def cache_key(text: str, speed: float, salt: str, dict_id: str) -> str:
    basis = f"{text}|{VOICE_ID}|{MODEL_ID}|{speed:.3f}|{dict_id}|{salt}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]


def synthesize(client: Cartesia, text: str, speed: float, dict_id: str) -> dict:
    """Cartesia SSE with word and phoneme timestamps, under the lexicon."""
    events = client.tts.sse(
        model_id=MODEL_ID, transcript=text, voice={"id": VOICE_ID}, language="en",
        add_timestamps=True, add_phoneme_timestamps=True,
        generation_config={"speed": speed}, pronunciation_dict_id=dict_id,
        output_format={"container": "raw", "encoding": "pcm_s16le", "sample_rate": SAMPLE_RATE},
    )
    pcm = bytearray()
    words, word_start, word_end, phonemes = [], [], [], []
    for ev in events:
        if ev.type == "chunk":
            if ev.audio:
                pcm.extend(ev.audio)
        elif ev.type == "timestamps":
            words.extend(ev.word_timestamps.words)
            word_start.extend(ev.word_timestamps.start)
            word_end.extend(ev.word_timestamps.end)
        elif ev.type == "phoneme_timestamps":
            phonemes.extend(ev.phoneme_timestamps.phonemes)
        elif ev.type == "error":
            raise RuntimeError(f"Cartesia error: {ev}")
    return {"pcm": bytes(pcm), "words": words, "word_start": word_start,
            "word_end": word_end, "phonemes": " ".join(phonemes)}


def require_terms_check(out_dir: Path, narration_path: Path, accept: bool) -> dict:
    p = out_dir / "terms_check.json"
    if not p.exists():
        raise SystemExit("REFUSED: no terms check for this page. Run check_terms.py first, "
                         "so a term the voice cannot say is found before the build.")
    tc = json.loads(p.read_text(encoding="utf-8"))
    if tc["checked_at"] < narration_path.stat().st_mtime:
        raise SystemExit("REFUSED: terms_check.json is older than narration.json. Re-run "
                         "check_terms.py.")
    if tc["failures"] and not accept:
        raise SystemExit("REFUSED: the terms check heard these wrongly: "
                         + ", ".join(tc["failures"]) + ". Add them to spike/lexicon.json "
                         "and re-run check_terms.py, or pass --accept-terms.")
    return tc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--speed", type=float, default=0.6)
    parser.add_argument("--accept-terms", action="store_true",
                        help="build although the terms check listed failures")
    args = parser.parse_args()

    narration_path = paths.narration_dir(args.lesson_dir, args.page) / "narration.json"
    narr = json.loads(narration_path.read_text(encoding="utf-8"))
    if narr["page"] != args.page:
        raise SystemExit(f"narration under page-{args.page} reports page {narr['page']}")
    out_dir = paths.boards_dir(args.lesson_dir, args.page)
    audio_dir = out_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "audio_index.json"

    client = Cartesia(api_key=api_key())
    lex = lexicon.require_synced(client)
    dict_id = lex["cartesia"]["dict_id"]
    require_terms_check(out_dir, narration_path, args.accept_terms)

    old_index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    by_hash = {e["hash"]: e for e in old_index.values() if (out_dir / e["file"]).exists()}

    index: dict = {}
    blocked: dict[str, list[str]] = {}    # unapproved term -> utterances needing new audio
    synthesized = cached = total_chars = 0
    total_duration_s = 0.0
    phoneme_failures: list[str] = []

    for bd in narr["boards"]:
        for s in bd["states"]:
            for u in s["utterances"]:
                text = spoken(u["text_with_cues"])
                terms = lexicon.terms_in(text, lex)
                salt = lexicon.cache_salt(text, lex)
                key = cache_key(text, args.speed, salt, dict_id)
                known = by_hash.get(key)
                if known:
                    # The key already carries every pronunciation decision the
                    # utterance depends on (the salt), so a cached clip is valid
                    # whatever the lexicon version now says.
                    index[u["id"]] = {**known, "id": u["id"]}
                    cached += 1
                    total_duration_s += known["duration_s"]
                    continue
                # New audio is never made with a pronunciation the maintainer
                # has not approved by ear (methodology §20). A cached clip that
                # contains an unapproved term is left as it is.
                unapproved = lexicon.unapproved_in(text, lex)
                if unapproved:
                    for t in unapproved:
                        blocked.setdefault(t, []).append(u["id"])
                    continue
                wav_path = audio_dir / f"{key}.wav"
                result = synthesize(client, text, args.speed, dict_id)
                write_wav(wav_path, result["pcm"])
                duration_s = len(result["pcm"]) / 2 / SAMPLE_RATE
                problems = [p for p in (lexicon.phoneme_check(t, result["phonemes"], lex)
                                        for t in terms) if p]
                for p in problems:
                    phoneme_failures.append(f"{u['id']}: {p}")
                entry = {
                    "id": u["id"], "hash": key, "voice": VOICE_NAME, "voice_id": VOICE_ID,
                    "model": MODEL_ID, "speed": args.speed,
                    "pronunciation_dict_id": dict_id,
                    "lexicon_version": lex["version"], "lexicon_terms": terms,
                    "phoneme_check": "fail" if problems else ("ok" if terms else "n/a"),
                    "phonemes": result["phonemes"],
                    "file": f"audio/{wav_path.name}", "text": text,
                    "words": result["words"], "word_start": result["word_start"],
                    "word_end": result["word_end"], "duration_s": duration_s,
                    "characters": len(text),
                }
                index[u["id"]] = entry
                by_hash[key] = entry
                synthesized += 1
                total_chars += len(text)
                total_duration_s += duration_s

    if blocked:
        # Keep the previous index entries for the blocked utterances so the
        # build stays complete; report and fail, nothing new is written for them.
        for t, ids in blocked.items():
            for uid in ids:
                if uid in old_index:
                    index[uid] = old_index[uid]
        print("REFUSED to make new audio with unapproved lexicon terms: "
              + "; ".join(f"{t} in {ids}" for t, ids in blocked.items())
              + ". Approve on the review page, then lexicon.py --approve TERM --by NAME.")

    keep = {e["file"] for e in index.values()}
    orphans = [p for p in audio_dir.glob("*.wav") if f"audio/{p.name}" not in keep]
    for p in orphans:
        p.unlink()
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"synthesized: {synthesized}")
    print(f"reused from cache: {cached}")
    print(f"orphaned files removed: {len(orphans)}")
    print(f"characters sent this run: {total_chars}")
    print(f"total audio duration: {total_duration_s:.1f}s ({total_duration_s / 60:.2f} min)")
    print(f"lexicon v{lex['version']}: "
          f"{sum(1 for e in index.values() if e['lexicon_terms'])} utterances contain a "
          f"lexicon term; phoneme check "
          f"{'FAILED' if phoneme_failures else 'passed'}")
    print(f"wrote {index_path}")
    for f in phoneme_failures:
        print("FAIL: " + f)
    if phoneme_failures:
        raise SystemExit(f"{len(phoneme_failures)} lexicon term(s) did not take effect")
    if blocked:
        raise SystemExit(f"{sum(len(v) for v in blocked.values())} utterance(s) need audio but "
                         "contain an unapproved lexicon term")


if __name__ == "__main__":
    main()
