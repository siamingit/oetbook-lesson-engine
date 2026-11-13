"""Make the recordings of a Speaking lesson's practice items (ADR 053), with Cartesia Sonic 3.6
under the pronunciation lexicon, as synthesize_narration.py makes the narration's.

    .venv/Scripts/python spike/scripts/synthesize_speaking.py <lesson_dir> [--dry-run]

(ffmpeg on the PATH; its atempo filter is in every build.)

Reads:  <lesson_dir>/analysis/practice.json      (the speaking items, speaking_items.py)
        spike/lexicon.json
Writes: <lesson_dir>/generated/speaking-audio/<item_id>.<role>.wav
        <lesson_dir>/generated/speaking-audio/index.json
            {"format": "oetbook-speaking-audio", "version": 1,
             "items": {item_id: {role: {file, hash, voice, voice_id, model, speed, [emotion],
                                        text, duration_s, characters, lexicon_terms, phoneme_check,
                                        [method, tempo, from]}}}}

Each item's recordings are those speaking_items.ROLES names: a speak_repeat's model sentence in the
teacher's voice at its speed, and the slow take; a speak_respond's patient line in the patient's
voice (patient_speaker, sonic-3.6 at 0.8, with the item's feeling where it has one) and its model
answer in the teacher's. A role-play has none here: the site's patient speaks.

The slow take is never synthesised (ADR 054): it is the normal take stretched by ffmpeg's atempo
filter to SLOW_SPEED of its tempo, the pitch and every sound kept (SLOW_FILTER; the owner chose atempo
over rubberband by ear on 2026-11-13: it sounds more natural; C:/OET/scratch/speaking-build/slow-compare/
CHOICE.md). Cartesia's own slow speed hardly slowed a sentence (1.00 to 1.07 of its length); this makes
it about 1/0.75 of it (1.32-1.33). Its entry has `method`, `tempo`
and `from` (the normal file), and a hash made of the normal take's hash and the filter, so it is
made again exactly when the normal take or the filter changes. It costs no characters.

As the narration's: a recording is reused while its words, voice, speed, feeling and every
pronunciation it depends on are unchanged (synthesize_narration.cache_key); new audio is never made
with a lexicon term not yet approved by ear; every lexicon term is checked in the phonemes; a run
over JOB_CHARACTERS_LIMIT stops. --dry-run makes nothing and sends nothing: it lists what a run
would make and its characters.

The site's own files (mp3, with sha256, bytes and duration in the contract) are made from these when
the contracts are released (speaking_items.to_contract); until then the lesson's own player plays
these recordings in its pop-up. A speak_repeat's two takes go to the site as narration .m4a files
(publish_lesson.py, contracts 1.22.0).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lexicon                                                        # noqa: E402
import practice_points                                                # noqa: E402
import speaking_items                                                 # noqa: E402
import voices                                                         # noqa: E402

FORMAT = "oetbook-speaking-audio"
SLOW_FILTER = f"atempo={speaking_items.SLOW_SPEED:g}"


def out_dir(L: Path) -> Path:
    return L / "generated" / "speaking-audio"


def items_of(L: Path) -> list[dict]:
    """Every speaking item of the lesson's practice points, in the file's order."""
    pts = practice_points.load(L) or {}
    return [it for p in pts.values() for it in p["items"] if speaking_items.is_speaking(it)]


def plan(L: Path, lesson_voice: dict) -> list[dict]:
    """One entry per recording: item id, role, text, voice, speed, emotion, file name; a slow take
    also `from`, the normal take's file it is stretched from (never synthesised)."""
    out = []
    for it in items_of(L):
        for role, r in speaking_items.recordings(it).items():
            v = voices.voice_for(None if r["who"] == "teacher" else r["who"], lesson_voice)
            e = {"item": it["item_id"], "role": role, "text": r["text"], "voice": v,
                 "speed": round(v["speed"], 3), "emotion": voices.emotion_for(r["emotion"]),
                 "file": f"{it['item_id']}.{role}.wav"}
            if r["slow"]:
                e["from"] = f"{it['item_id']}.normal.wav"
            out.append(e)
    return out


def slow_hash(normal_hash: str) -> str:
    return hashlib.sha256(f"{normal_hash}|ffmpeg|{SLOW_FILTER}".encode("utf-8")).hexdigest()


def wav_seconds(p: Path) -> float:
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def stretch(src: Path, dst: Path) -> None:
    """The slow take: `src` at SLOW_SPEED of its tempo, the pitch kept (ffmpeg atempo)."""
    tmp = dst.with_name(dst.stem + ".part.wav")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", SLOW_FILTER, "-c:a", "pcm_s16le",
                        str(tmp)], capture_output=True, text=True)
    if r.returncode:
        tmp.unlink(missing_ok=True)
        raise SystemExit(f"the slow take of {src.name} was not made. ffmpeg said: {r.stderr.strip()[-300:]}")
    tmp.replace(dst)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="list what a run would make; send nothing")
    ap.add_argument("--allow-large-job", action="store_true")
    args = ap.parse_args()
    L = args.lesson_dir.resolve()
    lesson_voice = voices.for_lesson(L)
    todo = plan(L, lesson_voice)
    if not todo:
        raise SystemExit(f"{L.name}: no speaking items with recordings in analysis/practice.json")
    d = out_dir(L)
    idx_path = d / "index.json"
    old = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"items": {}}
    by_hash = {e["hash"]: e for roles in old.get("items", {}).values() for e in roles.values()
               if (d / e["file"]).exists()}

    from synthesize_narration import JOB_CHARACTERS_LIMIT, cache_key

    def partition(lex: dict):
        dict_id = lex["cartesia"]["dict_id"]
        blocked, make, keep, slow = [], [], [], []
        hashes = {}
        for r in todo:
            if "from" in r:
                slow.append(r)
                continue
            salt = lexicon.cache_salt(r["text"], lex)
            r["hash"] = cache_key(r["text"], r["speed"], salt, dict_id, r["voice"], r["emotion"])
            r["terms"] = lexicon.terms_in(r["text"], lex)
            hashes[(r["item"], r["file"])] = r["hash"]
            if r["hash"] in by_hash:
                keep.append(r)
                continue
            un = lexicon.unapproved_in(r["text"], lex)
            if un:
                blocked.append(f"{r['item']}.{r['role']}: {', '.join(un)}")
                continue
            make.append(r)
        for r in slow:                      # made from the normal take; reused while it is unchanged
            nh = hashes.get((r["item"], r["from"]))
            r["hash"] = slow_hash(nh) if nh else None
            (keep if r["hash"] in by_hash else make).append(r)
        return dict_id, blocked, make, keep

    lex = lexicon.load()
    dict_id, blocked, make, keep = partition(lex)
    synth = [r for r in make if "from" not in r]
    client = sn = None
    if synth and not args.dry_run:
        import synthesize_narration as sn
        from cartesia import Cartesia
        from synthesize_audio import api_key
        client = Cartesia(api_key=api_key())
        lex = lexicon.require_synced(client)
        dict_id, blocked, make, keep = partition(lex)
        synth = [r for r in make if "from" not in r]
    chars = sum(len(r["text"]) for r in synth)
    print(f"{len(todo)} recordings: {len(keep)} reused, {len(synth)} to synthesise ({chars} characters), "
          f"{len(make) - len(synth)} slow takes to stretch, {len(blocked)} blocked")
    if args.dry_run:
        for r in make:
            how = f"stretched from {r['from']} ({SLOW_FILTER})" if "from" in r else \
                f"{r['voice']['name']} {r['speed']:g}{' ' + r['emotion'] if r['emotion'] else ''}"
            print(f"  {r['file']}: {how}: {r['text'][:70]}")
        for b in blocked:
            print("  BLOCKED " + b)
        return
    if chars > JOB_CHARACTERS_LIMIT and not args.allow_large_job:
        raise SystemExit(f"REFUSED: {chars:,} characters, over {JOB_CHARACTERS_LIMIT:,}: tell the maintainer first")

    d.mkdir(parents=True, exist_ok=True)
    failures = []
    made = {}
    if synth:
        from synthesize_audio import MODEL_ID, SAMPLE_RATE, write_wav
    for r in synth:
        res = sn.synthesize_with_retry(client, r["text"], r["speed"], dict_id, r["file"], r["voice"], r["emotion"])
        write_wav(d / r["file"], res["pcm"])
        probs = [p for p in (lexicon.phoneme_check(t, res["phonemes"], lex) for t in r["terms"]) if p]
        failures += [f"{r['file']}: {p}" for p in probs]
        made[r["hash"]] = {
            "file": r["file"], "hash": r["hash"], "voice": r["voice"]["name"], "voice_id": r["voice"]["id"],
            "model": MODEL_ID, "speed": r["speed"], **({"emotion": r["emotion"]} if r["emotion"] else {}),
            "pronunciation_dict_id": dict_id, "lexicon_version": lex["version"], "lexicon_terms": r["terms"],
            "phoneme_check": "fail" if probs else ("ok" if r["terms"] else "n/a"),
            "text": r["text"], "duration_s": round(len(res["pcm"]) / 2 / SAMPLE_RATE, 3),
            "characters": len(r["text"])}
        print(f"  made {r['file']} ({made[r['hash']]['duration_s']:.1f} s)", flush=True)
    normal_hash = {(x["item"], x["file"]): x["hash"] for x in todo if "from" not in x}
    for r in make:
        if "from" not in r:
            continue
        h = normal_hash.get((r["item"], r["from"]))
        src = (made.get(h) or by_hash.get(h)) if h else None
        if src is None:
            continue                                   # its normal take is blocked: nothing for it
        stretch(d / src["file"], d / r["file"])
        made[r["hash"]] = {
            "file": r["file"], "hash": r["hash"], "voice": src["voice"], "voice_id": src["voice_id"],
            "model": src["model"], "speed": round(src["speed"] * speaking_items.SLOW_SPEED, 3),
            "method": f"ffmpeg {SLOW_FILTER}", "tempo": speaking_items.SLOW_SPEED, "from": src["file"],
            **({"pronunciation_dict_id": src["pronunciation_dict_id"]} if "pronunciation_dict_id" in src else {}),
            **({"lexicon_version": src["lexicon_version"]} if "lexicon_version" in src else {}),
            "lexicon_terms": src.get("lexicon_terms", []), "phoneme_check": src.get("phoneme_check", "n/a"),
            "text": r["text"], "duration_s": round(wav_seconds(d / r["file"]), 3), "characters": 0}
        print(f"  stretched {r['file']} ({made[r['hash']]['duration_s']:.1f} s)", flush=True)
    items: dict = {}
    for r in todo:
        e = (made.get(r["hash"]) or by_hash.get(r["hash"])) if r.get("hash") else None
        if e is None:
            continue                                   # blocked: nothing for it
        if e["file"] != r["file"]:
            # the same words for another item or role: its own copy, so each item's files stand alone
            import shutil
            shutil.copyfile(d / e["file"], d / r["file"])
            e = {**e, "file": r["file"]}
        items.setdefault(r["item"], {})[r["role"]] = e
    wanted = {e["file"] for roles in items.values() for e in roles.values()}
    for p in d.glob("*.wav"):
        if p.name not in wanted:
            p.unlink()
    idx_path.write_text(json.dumps({"format": FORMAT, "version": 1, "items": items}, indent=2,
                                   ensure_ascii=False), encoding="utf-8")
    print(f"characters sent this run: {chars}; wrote {idx_path}")
    for f in failures:
        print("FAIL: " + f)
    if failures:
        raise SystemExit(f"{len(failures)} lexicon term(s) did not take effect")
    if blocked:
        raise SystemExit("blocked by unapproved lexicon terms: " + "; ".join(blocked))


if __name__ == "__main__":
    main()
