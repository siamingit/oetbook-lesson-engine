"""Structural check on a built page of boards. Fast, deterministic, no browser.

check_page.py adapted to the board model. What it checks, in under a second:

  audio      every utterance has a file, and the file's real duration matches
             the timeline's duration for it
  timeline   monotonic, no overlaps, and every gap is one the builder could
             have produced: an utterance gap, a pause, an erase followed by a
             state gap, or a board gap
  boards     every state's working blocks are revealed by a cue inside that
             state; no cue names a block that is not on the board then; erase
             events sit between states and clear exactly that state's notes
  blocks     every block a board uses is in the bundle with its html
  orphans    no audio file left behind that nothing references

    .venv/Scripts/python spike/scripts/check_board_page.py <lesson_dir> --page 13
"""

import argparse
import json
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

TOLERANCE_S = 0.02


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def check(lesson: Path, page, out_dir: Path | None = None) -> list[str]:
    # --dir checks a built player folder directly, such as the whole-lesson
    # player; its audio_file paths are relative to that folder.
    out_dir = out_dir or paths.boards_dir_for(lesson, page if isinstance(page, list) else [page])
    bundle = json.loads((out_dir / "bundle.json").read_text(encoding="utf-8"))
    meta = bundle["meta"]
    problems: list[str] = []

    seq = []          # (utterance, state, board) in order
    for bd in bundle["boards"]:
        for s in bd["states"]:
            for u in s["utterances"]:
                seq.append((u, s, bd))
    if not seq:
        return ["no utterances in bundle"]

    # Pronunciation: every clip was made under the lexicon, and every lexicon
    # term in it passed the phoneme check (methodology §20).
    index_path = out_dir / "audio_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    for u, _, _ in seq:
        e = index.get(u["id"])
        if not e:
            problems.append(f"{u['id']}: not in audio_index.json")
        elif not e.get("lexicon_version"):
            problems.append(f"{u['id']}: synthesised without the pronunciation lexicon")
        elif e.get("phoneme_check") == "fail":
            problems.append(f"{u['id']}: a lexicon term failed its phoneme check")

    referenced = set()
    for u, _, _ in seq:
        path = out_dir / u["audio_file"]
        referenced.add(u["audio_file"])
        if not path.exists():
            problems.append(f"{u['id']}: audio missing ({u['audio_file']})")
            continue
        planned = u["end"] - u["start"]
        actual = wav_duration(path)
        if abs(planned - actual) > TOLERANCE_S:
            problems.append(f"{u['id']}: timeline says {planned:.3f}s, audio is {actual:.3f}s")

    def pause_after(u: dict) -> float:
        return max([c["seconds"] for c in u["cues"] if c["type"] == "pause"] + [0.0])

    for (a, sa, ba), (b, sb, bb) in zip(seq, seq[1:]):
        gap = round(b["start"] - a["end"], 3)
        if gap < -TOLERANCE_S:
            problems.append(f"{a['id']} -> {b['id']}: overlap of {-gap:.3f}s")
            continue
        p = pause_after(a)
        if sa is sb:
            expected = [max(meta["utterance_gap_s"], p)]
        elif ba is bb:
            expected = [p + meta["state_gap_s"]]
            if not sa["erase"] or abs(sa["erase"]["time"] - (a["end"] + p)) > TOLERANCE_S:
                problems.append(f"{sa['id']}: erase event is not at the end of the state's "
                                "last utterance plus its pause")
        else:
            expected = [p + meta["board_gap_s"]]
        if not any(abs(gap - e) <= TOLERANCE_S for e in expected):
            problems.append(f"{a['id']} -> {b['id']}: gap {gap:.3f}s is not one the builder "
                            f"produces (expected {expected})")

    last_u = seq[-1][0]
    if abs(meta["total_duration_s"] - (last_u["end"] + pause_after(last_u))) > TOLERANCE_S:
        problems.append("total_duration_s does not match the last utterance's end plus "
                        "its pause")

    blocks = bundle["blocks"]
    n_cues = 0
    parts_drawn: dict[str, set] = {}
    for bd in bundle["boards"]:
        fixed = set(bd["fixed"])
        for i in bd["fixed"]:
            if i not in blocks or not blocks[i].get("html"):
                problems.append(f"{bd['id']}: fixed block {i} missing from bundle")
        for s in bd["states"]:
            working = list(s["working"])
            revealed = []
            for i in working:
                if i not in blocks or not blocks[i].get("html"):
                    problems.append(f"{s['id']}: working block {i} missing from bundle")
            for u in s["utterances"]:
                for c in u["cues"]:
                    n_cues += 1
                    if not (0 <= c["time"] <= meta["total_duration_s"] + TOLERANCE_S):
                        problems.append(f"{u['id']}/{c['id']}: fires at {c['time']}s, "
                                        "outside the lesson")
                    if c["type"] == "pause":
                        continue
                    blk = c.get("block")
                    if c["type"] == "reveal" and "." in str(blk):
                        # a diagram PART ("k07.3"): its diagram must be on the
                        # board (fixed, or a working block already revealed)
                        # and have that part; each part is drawn once per board
                        base, _, n = str(blk).rpartition(".")
                        b = blocks.get(base) or {}
                        parts = {str(it.get("part")) for it in (b.get("items") or [])}
                        if b.get("type") != "timeline" or n not in parts:
                            problems.append(f"{u['id']}/{c['id']}: reveal of {blk}, which is "
                                            "not a part of a diagram")
                        elif base not in fixed and base not in revealed:
                            problems.append(f"{u['id']}/{c['id']}: part {blk} revealed before "
                                            f"its diagram is on the board")
                        elif blk in parts_drawn.setdefault(bd["id"], set()):
                            problems.append(f"{u['id']}/{c['id']}: part {blk} drawn twice")
                        else:
                            parts_drawn[bd["id"]].add(blk)
                    elif c["type"] == "reveal":
                        if blk not in working:
                            problems.append(f"{u['id']}/{c['id']}: reveal of {blk}, not a "
                                            f"working block of {s['id']}")
                        elif blk in revealed:
                            problems.append(f"{u['id']}/{c['id']}: {blk} revealed twice")
                        else:
                            revealed.append(blk)
                    elif blk not in fixed and blk not in revealed:
                        problems.append(f"{u['id']}/{c['id']}: {c['type']} on {blk}, which "
                                        "is not on the board at that moment")
                    if c["type"] != "reveal" and not c.get("text"):
                        problems.append(f"{u['id']}/{c['id']}: {c['type']} names no phrase")
                    if c["type"] == "arrow" and not c.get("to_text"):
                        problems.append(f"{u['id']}/{c['id']}: arrow has no target phrase")
                    if c["type"] == "replace" and not c.get("with"):
                        problems.append(f"{u['id']}/{c['id']}: replace has no correction")
            for i in working:
                if i not in revealed:
                    problems.append(f"{s['id']}: {i} is never revealed")
            if s["erase"] and sorted(s["erase"]["blocks"]) != sorted(working):
                problems.append(f"{s['id']}: erase clears {s['erase']['blocks']}, not the "
                                f"state's working layer {working}")

    erases = [e for e in bundle["events"] if e["type"] == "erase"]
    expected_erases = sum(1 for bd in bundle["boards"] for s in bd["states"] if s["erase"])
    if len(erases) != expected_erases:
        problems.append(f"{len(erases)} erase events for {expected_erases} erasing states")
    board_events = [e for e in bundle["events"] if e["type"] == "board"]
    if [e["board"] for e in board_events] != [bd["id"] for bd in bundle["boards"]]:
        problems.append("board events do not match the boards in order")

    for path in sorted((out_dir / "audio").glob("*.wav")):
        if f"audio/{path.name}" not in referenced:
            problems.append(f"orphan audio file: {path.name}")
    for name in ("player.html", "timeline.json"):
        if not (out_dir / name).exists():
            problems.append(f"missing {name}")

    print(f"page {page}: {len(bundle['boards'])} boards, {len(seq)} utterances, "
          f"{n_cues} cues, {len(erases)} erase events, "
          f"{meta['total_duration_s'] / 60:.1f} min")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int)
    parser.add_argument("--pages")
    parser.add_argument("--dir", type=Path, help="a built player folder, e.g. generated/lesson-player")
    args = parser.parse_args()
    pages = ([int(x) for x in args.pages.split(",")] if args.pages else args.page)
    problems = check(args.lesson_dir, pages, args.dir)
    for p in problems:
        print("FAIL: " + p)
    if problems:
        raise SystemExit(f"{len(problems)} structural problem(s)")
    print("structural check passed")


if __name__ == "__main__":
    main()
