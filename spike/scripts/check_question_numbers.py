"""Check that a built lesson's question numbers agree (ADR 026 amendment of
2026-10-08): the lesson's first practice-set question is 1, and every
question number the narration speaks is one shown on that board
(question_numbers.py).

    .venv/Scripts/python spike/scripts/check_question_numbers.py <lesson_dir> --dir <player folder>

Reads the bundle only; changes nothing. A lesson with no practice-set
question passes.
"""

import argparse
import json
from pathlib import Path

import question_numbers as qn


def check(bundle: dict) -> tuple[list[int], list[dict]]:
    blocks = bundle["blocks"] if isinstance(bundle["blocks"], dict) else {b["id"]: b for b in bundle["blocks"]}
    taught = qn.lesson_numbers(blocks)
    findings = []
    if taught:
        # the first question the lesson shows, in board order
        first = None
        for bd in bundle["boards"]:
            ids = list(bd.get("fixed") or []) + list(bd.get("pinned") or {}) \
                + [i for s in bd["states"] for i in s["working"]]
            nums = [int(blocks[i]["exercise_item"]) for i in ids
                    if (blocks.get(i) or {}).get("question") and blocks[i].get("exercise_item") is not None]
            if nums:
                first = (bd["id"], min(nums))
                break
        if first and first[1] != 1:
            findings.append({"where": first[0], "what": f"the lesson's first question is {first[1]}, not 1"})
        for bd in bundle["boards"]:
            findings += qn.board_findings(bd, blocks, taught)
    return taught, findings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--dir", type=Path, required=True, help="a built player folder, e.g. generated/lesson-player")
    a = ap.parse_args()
    bundle = json.loads((a.dir / "bundle.json").read_text(encoding="utf-8"))
    taught, findings = check(bundle)
    if not taught:
        print("question-number check passed: no practice-set question in this lesson")
        return
    for f in findings:
        print(f"  NUMBER {f['where']}: {f['what']}")
    if findings:
        raise SystemExit(f"question-number check failed: {len(findings)} finding(s)")
    print(f"question-number check passed: questions {taught[0]}-{taught[-1]}, the first is 1, "
          "every spoken number shown on its board")


if __name__ == "__main__":
    main()
