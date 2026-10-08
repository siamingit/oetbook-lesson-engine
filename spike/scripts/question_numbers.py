"""Question numbers: what a board shows and what the narration says (ADR 026
amendment of 2026-10-08).

A lesson numbers the questions it teaches from 1, in the order taught
(practice_set.number). A number the narration speaks ("question eight",
"questions one to eight") must be one the board shows at that moment: a
question block's badge (`exercise_item`), or a row of a word recap grouped by
question. On a board that shows no question number, it must be a number of a
question the lesson teaches. A lesson with no practice-set question has
nothing to check.

Used by the narration audit (write_narration.py, per section) and by the
runner's player step (check_question_numbers.py, the whole lesson, where the
lesson's first question must also be 1).
"""

import re

UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
         "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
         "eighteen", "nineteen"]
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}


def word_number(w: str) -> int | None:
    """'eight' -> 8, 'twenty-two' -> 22, '22' -> 22; None for anything else."""
    w = w.lower().strip()
    if w.isdigit():
        return int(w)
    if w in UNITS:
        return UNITS.index(w)
    if w in TENS:
        return TENS[w]
    m = re.fullmatch(r"(twenty|thirty|forty|fifty)[- ](one|two|three|four|five|six|seven|eight|nine)", w)
    return TENS[m.group(1)] + UNITS.index(m.group(2)) if m else None


NUM = (r"(?:\d{1,2}|(?:twenty|thirty|forty|fifty)(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?"
       r"|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|ten"
       r"|one|two|three|four|five|six|seven|eight|nine)")
SPOKEN = re.compile(r"\bquestions?\s+(?:number\s+)?(" + NUM + r")(?:\s*(?:to|-|through|and)\s*(" + NUM + r"))?\b",
                    re.I)


def spoken_numbers(text: str) -> list[tuple[int, str]]:
    """Every question number a sentence speaks, with the words that say it."""
    out = []
    for m in SPOKEN.finditer(text or ""):
        for g in (m.group(1), m.group(2)):
            n = word_number(g) if g else None
            if n is not None:
                out.append((n, m.group(0)))
    return out


def shown_numbers(ids: list[str], blocks: dict) -> set[int]:
    """The question numbers these blocks show: a question's badge, a grouped
    word recap's rows."""
    out = set()
    for i in ids:
        b = blocks.get(i) or {}
        if b.get("question") and b.get("exercise_item") is not None:
            out.add(int(b["exercise_item"]))
        for n, _ in ((b.get("vocab_table") or {}).get("groups") or []):
            out.add(int(n))
    return out


def lesson_numbers(blocks: dict) -> list[int]:
    """The numbers of the practice-set questions in these blocks."""
    return sorted({int(b["exercise_item"]) for b in blocks.values()
                   if b.get("question") and b.get("exercise_item") is not None})


def board_findings(board: dict, blocks: dict, taught: list[int]) -> list[dict]:
    """A board's spoken question numbers against the numbers it shows. `board`
    has `fixed`, `states` (each with `working` and `utterances`, an utterance's
    text in `text` or `text_with_cues`) and may have `pinned`."""
    findings = []
    if not taught:
        return findings
    ids = list(board.get("fixed") or []) + list(board.get("pinned") or {})
    ids += [i for s in board.get("states") or [] for i in s.get("working") or []]
    shown = shown_numbers(ids, blocks)
    for s in board.get("states") or []:
        for u in s.get("utterances") or []:
            text = re.sub(r"\{\{[^}]*\}\}", "", u.get("text") or u.get("text_with_cues") or "")
            for n, said in spoken_numbers(text):
                if shown and n not in shown:
                    findings.append({"where": u["id"], "what": f"{said!r} is spoken; the board shows "
                                     f"question {', '.join(str(x) for x in sorted(shown))}"})
                elif not shown and n not in taught:
                    findings.append({"where": u["id"], "what": f"{said!r} is spoken; the lesson's "
                                     f"questions are {taught[0]}-{taught[-1]}"})
    return findings
