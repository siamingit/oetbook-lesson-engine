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
import voices                                                         # noqa: E402
import paths                                                          # noqa: E402
from synthesize_audio import (MODEL_ID, SAMPLE_RATE,  # noqa: E402
                              api_key, write_wav)
from write_narration import spoken                                    # noqa: E402


def cache_key(text: str, speed: float, salt: str, dict_id: str,
              voice: dict = voices.RUPERT) -> str:
    basis = f"{text}|{voice['id']}|{MODEL_ID}|{speed:.3f}|{dict_id}|{salt}"
    if voice["sentence_pause_s"]:
        # only a voice with added pauses (ADR 027) adds them to the key, so
        # every clip made before stays cached under the key it has
        basis += f"|pause{voice['sentence_pause_s']:.2f}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]


def synthesize(client: Cartesia, text: str, speed: float, dict_id: str,
               voice: dict = voices.RUPERT) -> dict:
    """Cartesia SSE with word and phoneme timestamps, under the lexicon; the
    voice's sentence pauses added after (ADR 027)."""
    events = client.tts.sse(
        model_id=MODEL_ID, transcript=text, voice={"id": voice["id"]}, language="en",
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
    pcm, word_start, word_end = voices.add_sentence_pauses(
        bytes(pcm), words, word_start, word_end, voice["sentence_pause_s"], SAMPLE_RATE)
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


RETRY_WAITS_S = [5, 10, 20, 40, 60, 90, 120]   # about six minutes in all

# Cartesia Scale plan (ADR 028): 15 concurrent TTS requests (docs.cartesia.ai,
# "Concurrency limits and timeouts", read 2026-10-06); over it, 429. One run
# uses them all; runs side by side share them and the retries absorb the 429s
# (or pass --workers to divide them).
TTS_CONCURRENCY = 15
# The maintainer is told before a single job above about 2 million characters
# (ADR 028); the quota is 8 million a month.
JOB_CHARACTERS_LIMIT = 2_000_000


def synthesize_with_retry(client, text: str, speed: float, dict_id: str, uid: str,
                          voice: dict = voices.RUPERT) -> dict:
    """Cartesia returns 429 over the concurrency limit and has returned
    intermittent quota and server errors (402, 429, 5xx) that clear within a
    minute. Wait and retry with backoff, with jitter so parallel workers do not
    retry in step; any other error, or the last retry, is raised to the caller,
    which stops."""
    import random
    import time
    for n, wait in enumerate(RETRY_WAITS_S + [None], 1):
        try:
            return synthesize(client, text, speed, dict_id, voice)
        except Exception as e:
            msg = str(e).lower()
            transient = any(k in msg for k in ("402", "429", "quota", "rate", "limit",
                                               "timeout", "timed out", "500", "503", "502",
                                               "504", "connection"))
            if wait is None or not transient:
                raise
            wait = wait * random.uniform(0.8, 1.2)
            print(f"  {uid}: {str(e)[:120]} - retry {n} in {wait:.0f}s", flush=True)
            time.sleep(wait)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int)
    parser.add_argument("--pages", help="a section's pages, e.g. 5,6")
    # The lesson's voice sets the speed (voices.py, ADR 027): Rupert 1.0,
    # chosen by ear 2026-09-24 (methodology §23); Courtney 0.6 for Reading and
    # Listening. Speed is part of the cache key.
    parser.add_argument("--speed", type=float, default=None)
    parser.add_argument("--accept-terms", action="store_true",
                        help="build although the terms check listed failures")
    parser.add_argument("--workers", type=int, default=TTS_CONCURRENCY,
                        help=f"parallel Cartesia requests (the plan allows {TTS_CONCURRENCY})")
    parser.add_argument("--allow-large-job", action="store_true",
                        help=f"make more than {JOB_CHARACTERS_LIMIT:,} characters in one run "
                             "(the maintainer is told first, ADR 028)")
    args = parser.parse_args()
    pages = (sorted(int(x) for x in args.pages.split(",")) if args.pages
             else [args.page])
    voice = voices.for_lesson(args.lesson_dir)
    if args.speed is None:
        args.speed = voice["speed"]

    narration_path = paths.narration_dir_for(args.lesson_dir, pages) / "narration.json"
    narr = json.loads(narration_path.read_text(encoding="utf-8"))
    if narr.get("pages", [narr["page"]]) != pages:
        raise SystemExit(f"narration for {pages} reports pages {narr.get('pages')}")
    out_dir = paths.boards_dir_for(args.lesson_dir, pages)
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

    # Plan every utterance in narration order: a cached clip, a blocked one, or
    # a clip to make. Clips are then made in parallel (ADR 028) and the index is
    # assembled in narration order, so it is the same as a run one by one.
    plan: list[tuple[dict, str, list, str]] = []     # (utterance, text, terms, key)
    to_make: dict[str, tuple[str, str, list]] = {}   # key -> (first uid, text, terms)
    for bd in narr["boards"]:
        for s in bd["states"]:
            for u in s["utterances"]:
                text = spoken(u["text_with_cues"])
                terms = lexicon.terms_in(text, lex)
                salt = lexicon.cache_salt(text, lex)
                key = cache_key(text, args.speed, salt, dict_id, voice)
                if key not in by_hash and key not in to_make:
                    # New audio is never made with a pronunciation the maintainer
                    # has not approved by ear (methodology §20). A cached clip that
                    # contains an unapproved term is left as it is.
                    unapproved = lexicon.unapproved_in(text, lex)
                    if unapproved:
                        for t in unapproved:
                            blocked.setdefault(t, []).append(u["id"])
                        continue
                    to_make[key] = (u["id"], text, terms)
                plan.append((u, text, terms, key))

    job_chars = sum(len(t) for _, t, _ in to_make.values())
    if job_chars > JOB_CHARACTERS_LIMIT and not args.allow_large_job:
        raise SystemExit(f"REFUSED: this run would send {job_chars:,} characters, over "
                         f"{JOB_CHARACTERS_LIMIT:,}: tell the maintainer first (ADR 028), then "
                         "pass --allow-large-job.")

    def make(key: str) -> tuple[str, dict]:
        uid, text, terms = to_make[key]
        result = synthesize_with_retry(client, text, args.speed, dict_id, uid, voice)
        wav_path = audio_dir / f"{key}.wav"
        write_wav(wav_path, result["pcm"])
        problems = [p for p in (lexicon.phoneme_check(t, result["phonemes"], lex)
                                for t in terms) if p]
        return key, {
            "id": uid, "hash": key, "voice": voice["name"], "voice_id": voice["id"],
            "model": MODEL_ID, "speed": args.speed,
            **({"sentence_pause_s": voice["sentence_pause_s"]}
               if voice["sentence_pause_s"] else {}),
            "pronunciation_dict_id": dict_id,
            "lexicon_version": lex["version"], "lexicon_terms": terms,
            "phoneme_check": "fail" if problems else ("ok" if terms else "n/a"),
            "phonemes": result["phonemes"],
            "file": f"audio/{wav_path.name}", "text": text,
            "words": result["words"], "word_start": result["word_start"],
            "word_end": result["word_end"], "duration_s": len(result["pcm"]) / 2 / SAMPLE_RATE,
            "characters": len(text),
        }, problems

    def write_partial() -> None:
        # written as it goes: an interrupted run keeps what it made
        made = {e["id"]: e for k, e in by_hash.items() if k in to_make}
        partial = {**{k: v for k, v in old_index.items() if k not in made}, **made}
        index_path.write_text(json.dumps(partial, indent=2, ensure_ascii=False), encoding="utf-8")

    problems_by_key: dict[str, list] = {}
    if to_make:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        print(f"making {len(to_make)} clips, {job_chars} characters, "
              f"{max(1, args.workers)} at a time", flush=True)
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = {pool.submit(make, k): k for k in to_make}
            for f in as_completed(futures):
                try:
                    key, entry, problems = f.result()
                except Exception as e:
                    # Never skip an utterance silently: keep what is made,
                    # name what is not, and stop.
                    for other in futures:
                        other.cancel()
                    write_partial()
                    raise SystemExit(f"STOPPED at {to_make[futures[f]][0]} after retries: "
                                     f"{str(e)[:300]}. {synthesized} made this run are kept in "
                                     "the index; re-run to continue (made clips are reused).")
                by_hash[key] = entry
                problems_by_key[key] = problems
                synthesized += 1
                total_chars += entry["characters"]
                if synthesized % 10 == 0:
                    write_partial()
                    print(f"  {synthesized} made, {total_chars} characters", flush=True)

    for u, text, terms, key in plan:
        known = by_hash[key]
        # The key carries every pronunciation decision the utterance depends on
        # (the salt), so a cached clip is valid whatever the lexicon version says.
        entry = known if (key in to_make and known["id"] == u["id"]) else {**known, "id": u["id"]}
        index[u["id"]] = entry
        total_duration_s += entry["duration_s"]
        if key in to_make and known["id"] == u["id"]:
            phoneme_failures.extend(f"{u['id']}: {p}" for p in problems_by_key[key])
        else:
            cached += 1

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
