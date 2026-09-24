"""Measure the voice's pace at chosen speed settings, on one lesson utterance,
for the maintainer to choose by ear.

    .venv/Scripts/python spike/scripts/speed_probe.py <lesson_dir> --page 13 \
        --utt t5.s1.u4 --speeds 0.7,0.8

Reads:  <lesson_dir>/generated/page-<N>/boards/audio_index.json (the text, and
        the lesson's own clip of it as the current setting)
        spike/lexicon.json (the dictionary it is synthesised under)
Writes: spike/out/lexicon-review/speed_<setting>.wav and speed_probes.json

Pace is measured, never assumed: words / audio duration * 60, from the WAV
Cartesia returns (the same measure as the lesson's audio index). Each setting
is synthesised once and kept; a setting already in speed_probes.json is not
paid for again. The lesson's existing clip is recorded as the current setting
at no cost. No lesson audio is touched.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lexicon                                                 # noqa: E402
import paths                                                   # noqa: E402
from synthesize_audio import api_key, write_wav                # noqa: E402
from synthesize_narration import SAMPLE_RATE, synthesize       # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "out" / "lexicon-review"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--page", type=int, default=13)
    ap.add_argument("--utt", required=True)
    ap.add_argument("--speeds", default="")
    args = ap.parse_args()

    boards = paths.boards_dir(args.lesson_dir, args.page)
    index = json.loads((boards / "audio_index.json").read_text(encoding="utf-8"))
    ent = index[args.utt]
    text, n = ent["text"], len(ent["words"])
    OUT.mkdir(parents=True, exist_ok=True)
    store = OUT / "speed_probes.json"
    probes = json.loads(store.read_text(encoding="utf-8")) if store.exists() else {
        "utterance": args.utt, "page": args.page, "text": text, "words": n, "settings": []}
    if probes["utterance"] != args.utt:
        raise SystemExit("speed_probes.json holds another utterance; move it aside first")

    have = {round(p["speed"], 3) for p in probes["settings"]}
    if round(ent["speed"], 3) not in have:
        cur = OUT / f"speed_{ent['speed']:.3f}.wav"
        cur.write_bytes((boards / ent["file"]).read_bytes())
        probes["settings"].append({"speed": ent["speed"], "file": cur.name,
                                   "duration_s": ent["duration_s"],
                                   "wpm": round(n / ent["duration_s"] * 60, 1),
                                   "current": True, "chars": 0})

    speeds = [float(s) for s in args.speeds.split(",") if s.strip()]
    if speeds:
        lex = lexicon.load()
        from cartesia import Cartesia
        client = Cartesia(api_key=api_key())
        lexicon.require_synced(client, lex)
        for sp in speeds:
            if round(sp, 3) in have:
                print(f"speed {sp}: already measured")
                continue
            r = synthesize(client, text, sp, lex["cartesia"]["dict_id"])
            path = OUT / f"speed_{sp:.3f}.wav"
            write_wav(path, r["pcm"])
            dur = len(r["pcm"]) / 2 / SAMPLE_RATE
            probes["settings"].append({"speed": sp, "file": path.name,
                                       "duration_s": round(dur, 3),
                                       "wpm": round(n / dur * 60, 1), "current": False,
                                       "chars": len(text)})
            have.add(round(sp, 3))
    probes["settings"].sort(key=lambda p: p["speed"])
    store.write_text(json.dumps(probes, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{args.utt}: {n} words | {text}")
    for p in probes["settings"]:
        print(f"  speed {p['speed']:.3f}: {p['duration_s']:.2f} s = {p['wpm']:.1f} wpm"
              + ("  (current lesson setting)" if p.get("current") else ""))


if __name__ == "__main__":
    main()
