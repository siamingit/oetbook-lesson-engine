"""Make the recordings of a Speaking lesson's practice items (ADR 053), with Cartesia Sonic 3.6
under the pronunciation lexicon, as synthesize_narration.py makes the narration's.

    .venv/Scripts/python spike/scripts/synthesize_speaking.py <lesson_dir> [--dry-run]

Reads:  <lesson_dir>/analysis/practice.json      (the speaking items, speaking_items.py)
        spike/lexicon.json
Writes: <lesson_dir>/generated/speaking-audio/<item_id>.<role>.wav
        <lesson_dir>/generated/speaking-audio/index.json
            {"format": "oetbook-speaking-audio", "version": 1,
             "items": {item_id: {role: {file, hash, voice, voice_id, model, speed, [emotion],
                                        text, duration_s, characters, lexicon_terms, phoneme_check}}}}

Each item's recordings are those speaking_items.ROLES names: a speak_repeat's model sentence in the
teacher's voice at its speed and again slowly (SLOW_SPEED of it); a speak_respond's patient line in
the patient's voice (patient_speaker, sonic-3.6 at 0.8, with the item's feeling where it has one)
and its model answer in the teacher's. A role-play has none here: the site's patient speaks.

As the narration's: a recording is reused while its words, voice, speed, feeling and every
pronunciation it depends on are unchanged (synthesize_narration.cache_key); new audio is never made
with a lexicon term not yet approved by ear; every lexicon term is checked in the phonemes; a run
over JOB_CHARACTERS_LIMIT stops. --dry-run makes nothing and sends nothing: it lists what a run
would make and its characters.

The site's own files (mp3, with sha256, bytes and duration in the contract) are made from these when
the contracts are released (speaking_items.to_contract); until then the lesson's own player plays
these recordings in its pop-up.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lexicon                                                        # noqa: E402
import practice_points                                                # noqa: E402
import speaking_items                                                 # noqa: E402
import voices                                                         # noqa: E402

FORMAT = "oetbook-speaking-audio"


def out_dir(L: Path) -> Path:
    return L / "generated" / "speaking-audio"


def items_of(L: Path) -> list[dict]:
    """Every speaking item of the lesson's practice points, in the file's order."""
    pts = practice_points.load(L) or {}
    return [it for p in pts.values() for it in p["items"] if speaking_items.is_speaking(it)]


def plan(L: Path, lesson_voice: dict) -> list[dict]:
    """One entry per recording: item id, role, text, voice, speed, emotion, file name."""
    out = []
    for it in items_of(L):
        for role, r in speaking_items.recordings(it).items():
            v = voices.voice_for(None if r["who"] == "teacher" else r["who"], lesson_voice)
            speed = v["speed"] * (speaking_items.SLOW_SPEED if r["slow"] else 1.0)
            out.append({"item": it["item_id"], "role": role, "text": r["text"], "voice": v,
                        "speed": round(speed, 3), "emotion": voices.emotion_for(r["emotion"]),
                        "file": f"{it['item_id']}.{role}.wav"})
    return out


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

    if args.dry_run:
        lex = lexicon.load()
        dict_id = lex["cartesia"]["dict_id"]
    else:
        import synthesize_narration as sn
        from cartesia import Cartesia
        from synthesize_audio import api_key
        client = Cartesia(api_key=api_key())
        lex = lexicon.require_synced(client)
        dict_id = lex["cartesia"]["dict_id"]
    from synthesize_narration import JOB_CHARACTERS_LIMIT, cache_key

    blocked, make, keep = [], [], []
    for r in todo:
        salt = lexicon.cache_salt(r["text"], lex)
        r["hash"] = cache_key(r["text"], r["speed"], salt, dict_id, r["voice"], r["emotion"])
        r["terms"] = lexicon.terms_in(r["text"], lex)
        if r["hash"] in by_hash:
            keep.append(r)
            continue
        un = lexicon.unapproved_in(r["text"], lex)
        if un:
            blocked.append(f"{r['item']}.{r['role']}: {', '.join(un)}")
            continue
        make.append(r)
    chars = sum(len(r["text"]) for r in make)
    print(f"{len(todo)} recordings: {len(keep)} reused, {len(make)} to make ({chars} characters), "
          f"{len(blocked)} blocked")
    if args.dry_run:
        for r in make:
            print(f"  {r['file']}: {r['voice']['name']} {r['speed']:g}"
                  f"{' ' + r['emotion'] if r['emotion'] else ''}: {r['text'][:70]}")
        for b in blocked:
            print("  BLOCKED " + b)
        return
    if chars > JOB_CHARACTERS_LIMIT and not args.allow_large_job:
        raise SystemExit(f"REFUSED: {chars:,} characters, over {JOB_CHARACTERS_LIMIT:,}: tell the maintainer first")

    d.mkdir(parents=True, exist_ok=True)
    from synthesize_audio import MODEL_ID, SAMPLE_RATE, write_wav
    failures = []
    made = {}
    for r in make:
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
    items: dict = {}
    for r in todo:
        e = made.get(r["hash"]) or by_hash.get(r["hash"])
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
