"""Check that a built lesson's question numbers agree (ADR 026 amendment of
2026-10-08; ADR 035 amendment of 2026-10-16): the lesson's practice-set
questions are numbered from 1, in every lesson type (a Listening lesson
included: its practice numbers start at 1 within the lesson), with no number
missing or given to two questions, and every question number the narration
speaks is one shown on that board (question_numbers.py).

    .venv/Scripts/python spike/scripts/check_question_numbers.py <lesson_dir> --dir <player folder>

Reads the bundle only; changes nothing. A lesson with no practice-set
question passes.
"""

import argparse
import json
from pathlib import Path

import question_numbers as qn


def check(bundle: dict, exam_numbers: bool = False,
          exam_of: dict[int, int] | None = None) -> tuple[list[int], list[dict]]:
    """`exam_numbers`: a Listening lesson, whose Part B and C questions carry
    their practice numbers (ADR 032), numbered from 1 within the lesson like
    every other lesson's (ADR 035 amendment of 2026-10-16: Part C (1) is 1-6,
    never 7-12). `exam_of`: each Part B or C practice number's real-test
    number, which may be spoken as context (question_numbers.board_findings)."""
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
        missing = sorted(set(range(1, max(taught) + 1)) - set(taught))
        if missing:
            findings.append({"where": "lesson", "what": f"the lesson's questions are {taught[0]}-{taught[-1]}, "
                             f"without {', '.join(map(str, missing))}: they run from 1 with none missing"})
        items_of: dict[int, set] = {}
        for b in blocks.values():
            if b.get("question") and b.get("exercise_item") is not None and (b["question"] or {}).get("item"):
                items_of.setdefault(int(b["exercise_item"]), set()).add(b["question"]["item"])
        for n, its in sorted(items_of.items()):
            if len(its) > 1:
                findings.append({"where": "lesson", "what": f"question {n} is the number of {len(its)} "
                                 f"different questions ({', '.join(sorted(its))})"})
        for bd in bundle["boards"]:
            findings += qn.board_findings(bd, blocks, taught, exam_of)
    return taught, findings


def shown_items(bundle: dict) -> set[str]:
    """The practice-set items the lesson's question blocks show."""
    blocks = bundle["blocks"] if isinstance(bundle["blocks"], dict) else {b["id"]: b for b in bundle["blocks"]}
    return {b["question"]["item"] for b in blocks.values()
            if b.get("question") and (b["question"] or {}).get("item")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--dir", type=Path, required=True, help="a built player folder, e.g. generated/lesson-player")
    a = ap.parse_args()
    bundle = json.loads((a.dir / "bundle.json").read_text(encoding="utf-8"))
    import lesson_type
    exam_numbers = lesson_type.has(a.lesson_dir, "exam_numbers")
    import practice_set
    ps = practice_set.load(a.lesson_dir) if exam_numbers else None
    taught, findings = check(bundle, exam_numbers,
                             practice_set.exam_numbers(ps, shown_items(bundle)) if ps else None)
    if not taught:
        print("question-number check passed: no practice-set question in this lesson")
        return
    for f in findings:
        print(f"  NUMBER {f['where']}: {f['what']}")
    if findings:
        raise SystemExit(f"question-number check failed: {len(findings)} finding(s)")
    print(f"question-number check passed: questions {taught[0]}-{taught[-1]}, the first is 1, "
          + ("practice numbers (ADR 032, ADR 035), " if exam_numbers else "")
          + "every spoken number shown on its board")


if __name__ == "__main__":
    main()
