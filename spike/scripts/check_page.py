"""Structural check on a built page. Fast, deterministic, no browser.

This replaces the full playthrough for bulk runs. The playthrough plays the
lesson in real time, so it costs a lesson-length of wall clock per page, and
it is the only step in the pipeline that is not deterministic: muted headless
playback stalls intermittently (3 completed, 2 stalled across pages 13-14,
different points each time, re-probes of those points always passing). A
stalled run is not evidence of a broken build, which makes it a poor gate.

What this checks instead, in under a second:

  audio      every utterance has a file, and the file's real duration matches
             the timeline's duration for it
  timeline   monotonic, no overlaps, and every gap is one the builder could
             have produced (utterance gap, beat gap, or a pause cue)
  cues       every cue resolved to the geometry its kind requires, and sits
             inside the segment
  orphans    no audio file left behind that nothing references

    .venv/Scripts/python spike/scripts/check_page.py <lesson_dir> --page 14
    .venv/Scripts/python spike/scripts/check_page.py <lesson_dir> --page 14 --playthrough

`--playthrough` additionally runs the real browser playthrough. Off by
default, kept because it is the only check that proves audio actually plays.
"""

import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

TOLERANCE_S = 0.02      # WAV frame rounding against the timeline's rounded seconds


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def check(lesson: Path, page: int) -> list[str]:
    out_dir = paths.generated_dir(lesson, page)
    bundle = json.loads((out_dir / "bundle.json").read_text(encoding="utf-8"))
    meta = bundle["meta"]
    problems: list[str] = []

    utterances = [u for b in bundle["beats"] for u in b["utterances"]]
    if not utterances:
        return ["no utterances in bundle"]

    referenced = set()
    for utt in utterances:
        path = out_dir / utt["audio_file"]
        referenced.add(utt["audio_file"])
        if not path.exists():
            problems.append(f"{utt['id']}: audio missing ({utt['audio_file']})")
            continue
        planned = utt["end"] - utt["start"]
        actual = wav_duration(path)
        if abs(planned - actual) > TOLERANCE_S:
            problems.append(f"{utt['id']}: timeline says {planned:.3f}s, "
                            f"audio is {actual:.3f}s")

    # Gaps the builder could legitimately have produced.
    allowed = {meta["utterance_gap_s"], meta["beat_gap_s"]}
    pauses = {round(c.get("seconds") or 0.0, 3)
              for u in utterances for c in u["cues"] if c["kind"] == "thinking_pause"}
    allowed |= pauses

    for a, b in zip(utterances, utterances[1:]):
        gap = round(b["start"] - a["end"], 3)
        if gap < -TOLERANCE_S:
            problems.append(f"{a['id']} -> {b['id']}: overlap of {-gap:.3f}s")
        elif not any(abs(gap - g) <= TOLERANCE_S for g in allowed):
            problems.append(f"{a['id']} -> {b['id']}: gap {gap:.3f}s is not an "
                            f"utterance gap, a beat gap, or a pause")

    last_end = utterances[-1]["end"]
    if abs(meta["total_duration_s"] - last_end) > TOLERANCE_S:
        problems.append(f"total_duration_s {meta['total_duration_s']} does not match "
                        f"the last utterance's end {last_end}")

    required = {
        "slide_phrase": ("box",),
        "answer_box": ("box", "text"),
        "annotation_note": ("box", "text"),
        "board_note": ("text",),
        "comparison": ("left", "right"),
        "thinking_pause": ("seconds",),
    }
    n_cues = 0
    for utt in utterances:
        for cue in utt["cues"]:
            n_cues += 1
            kind = cue.get("kind")
            if kind not in required:
                problems.append(f"{utt['id']}/{cue['id']}: unknown cue kind {kind!r}")
                continue
            for field in required[kind]:
                if cue.get(field) in (None, "", []):
                    problems.append(f"{utt['id']}/{cue['id']}: {kind} cue has no "
                                    f"{field}")
            if kind == "slide_phrase" and isinstance(cue.get("box"), list) \
                    and len(cue["box"]) != 4:
                problems.append(f"{utt['id']}/{cue['id']}: box is not 4 numbers")
            if not (0 <= cue["time"] <= meta["total_duration_s"] + TOLERANCE_S):
                problems.append(f"{utt['id']}/{cue['id']}: fires at {cue['time']}s, "
                                f"outside the lesson")

    for path in sorted((out_dir / "audio").glob("*.wav")):
        if f"audio/{path.name}" not in referenced:
            problems.append(f"orphan audio file: {path.name}")

    for name in ("slide.png", "player.html", "timeline.json"):
        if not (out_dir / name).exists():
            problems.append(f"missing {name}")

    print(f"page {page}: {len(utterances)} utterances, {n_cues} cues, "
          f"{meta['total_duration_s'] / 60:.1f} min")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--playthrough", action="store_true",
                         help="also play the page through in a real browser "
                              "(slow, and intermittently stalls -- see module docstring)")
    args = parser.parse_args()

    problems = check(args.lesson_dir, args.page)
    for p in problems:
        print("FAIL: " + p)
    if problems:
        raise SystemExit(f"{len(problems)} structural problem(s)")
    print("structural check passed")

    if args.playthrough:
        harness = Path(__file__).resolve().parents[2] / "spike" / "scripts" / "playthrough.py"
        if not harness.exists():
            raise SystemExit(f"playthrough harness not found at {harness}")
        raise SystemExit(subprocess.call(
            [sys.executable, str(harness), str(args.lesson_dir), str(args.page)]))


if __name__ == "__main__":
    main()
