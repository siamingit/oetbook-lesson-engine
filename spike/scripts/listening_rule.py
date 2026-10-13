"""The Listening-lesson rule (docs/adr/029-listening-lessons.md, amended by
docs/adr/030-listening-board-layout.md; owner, 2026-10-13):
what the screens, narration and QA prompts add for a lesson of type listening
(lesson_type.py), as reading_rule.py does for Reading (ADR 026) and
vocabulary_rule.py for vocabulary lessons (ADR 019).

A Listening lesson teaches the pinned release's sets (practice_set.py,
sample-tests-v2): code builds every transcript, note form and question from
its ID, exactly as released, and the release's own audio plays inside the
lesson's clock (a narration `play` cue; bundle 1.18). Exam facts come only from
the beats, the rulings and the verified fact sheet (docs/listening-facts.md).
Every board with a transcript is a Listening board (ADR 030, bundle 1.19).

    .venv/Scripts/python spike/scripts/listening_rule.py <lesson_dir> --prompts

checks a lesson's pause-and-try prompts (ADR 030): no sentence twice, nor a
near copy of another (exit 1 on a finding).
"""

import difflib
import json
import re
import sys
from pathlib import Path

import lesson_type
import practice_set


def is_listening(lesson: Path) -> bool:
    """A lesson of type listening (lesson_type.py: its config's type, else its id's first word)."""
    return lesson_type.of(lesson) == "listening"


NOTE = "listening rule (ADR 029)"

SCREENS = """\
LISTENING LESSON (docs/adr/029-listening-lessons.md; owner, 2026-10-13). This \
lesson teaches the OET LISTENING test, not grammar. Where these instructions \
speak of grammar terms, exercise sentences or letters, read them as the \
listening strategies, the recordings, the note forms and the questions this \
section teaches. The rules below ADD to the rest of these instructions; \
everything else holds (A2-B1 wording, DO NOT ADD TEACHING, NEVER JUDGE \
REGISTER, the board style, a picture on every board).
  - EXAM FACTS. Only the facts in the beats and in the MAINTAINER RULINGS. Where \
the source is wrong (a number of options, of questions, a reading time, a wrong \
meaning of a word), teach the ruling's version as plain fact and never mention \
the error.
  - THE INSTRUCTOR'S PRACTICE MATERIAL NEVER APPEARS. Every recording, form, \
question and transcript he used in the sessions is third-party (official OET \
samples and others): no title, name of a speaker or patient, sentence, \
paraphrase or description of one, even where the beats quote it. His TEACHING \
carries over (his strategies, his explanations, his order) and is applied to \
this lesson's own practice set.
  - NOTHING ABOUT A WEBSITE, A COURSE SERIES OR A PERSIAN AUDIENCE: no site, \
dashboard, shop, podcast plug, other course or "later sessions"; never a lesson \
count or a list of the other lessons.
  - NEVER ADVISE TAKING A MOCK TEST FIRST, and never suggest a highlighter for \
the test. Listening Part A: a pen or a pencil. Parts B and C on paper: the \
answer's circle is shaded with a 2B pencil. Paper-only advice is said to be \
for the paper test; never name a tool of the computer test.
  - THE FACT SHEET'S RULINGS (owner, 2026-10-13; docs/listening-facts.md): a \
target of 20 of 24 (Part A), 4 of 6 (Part B) or 8 of 12 (Part C) is only ever \
"the instructor's suggested target", and where one is given, say that grade B \
typically needs at least 30 of the 42 marks, varying slightly from test to \
test. NEVER teach that abbreviations are accepted in Part A (teach writing the \
words heard), and NEVER teach that the instructions' time can be used as extra \
reading time: teach only the 30 seconds to look at the Part A notes before \
each extract.
  - QUESTION NUMBERS ARE THE EXAM'S (owner, 2026-10-13): Part A gaps 1-24, Part B \
questions 25-30, Part C questions 31-42, because the recordings announce them. \
Never renumber them from 1.
  - THE LEARNER NEVER TYPES. A Part A note form is shown on a board and the \
lesson fills each gap after "try it first".
  - A WORD ON A BOARD is never a transcript's: you never copy, quote in a block \
of your own, shorten or paraphrase a transcript, a note form or a question.\
"""

SCREENS_SET = """\
THE PRACTICE SET OF THIS LESSON (ADR 029, ADR 030). Its recordings' \
transcripts, its note forms and its questions are listed below, by ID, exactly \
as the board will show them. CODE BUILDS THEM; the release's own audio plays in \
the lesson (the narration starts it).
  - A LISTENING BOARD (owner, 2026-10-13; ADR 030): every board with a \
transcript has ONE layout, for Parts A, B and C: the transcript in a box on \
the left (about 58% of the width; about ten lines of fixed size, moving line by \
line with the recording, a marker under the word being said) and the questions \
on the right (Part A: the note form; Part B: the question and its three \
options; Part C: the question being taught, and while a recording plays, the \
question its section is about). It has NO board picture. Write no pictures \
for it.
  - A TRANSCRIPT: write {"type": "table", "label": "<the extract's stimulus ID>", \
"anchor": true}, with NO header and NO rows. Its rows are the released lines \
(a speaker's turn, or a paragraph of a talk), numbered as listed. It is on \
screen from the board's start, whenever a recording plays, the first time too: \
NEVER covered, never shown in parts or as a map (no "Covered:", "Para:" or \
"Map:" thoughts). On a Part B or C board a thought "Row N: ..." shows row N in \
the box (the rows read, the keywords, the answer); "Table: ..." is about the \
whole board.
  - THE SECTIONS: each extract's transcript lists where each question (or each \
heading of a note form) is answered: its SECTION, from where the speaker \
signposts that point to where the next one is signposted. A replay of one is \
the narration's "question N" or "heading K".
  - A PART A NOTE FORM: write {"type": "table", "label": "<the gap-fill item \
ID>", "anchor": true}, with NO header and NO rows, on the SAME board as its \
extract's transcript (both anchors): the form is the board's table. Its rows \
are listed below: a row for each heading and a numbered row for each gap. One \
"Row N: ..." thought per gap, in order. Code types each gap's answer in its \
exact form; the narration types it.
  - A QUESTION (Parts B and C): {"type": "plain", "label": "<its item ID>", \
"anchor": false, "items": [...]}, with NO text: code writes its number (the \
exam's), its stem and its three options, shown from the start (in the test, \
the options are read in the reading time). Its `items` rule the wrong options \
out and tick the answer, in this order: "out|<letter>|<reason label>" for each \
WRONG option (at most 12 plain words, A2-B1, based on the release's own reason \
for that option, never adding a fact), then "key|<letter>". Put it in the FIRST \
thought of its board; it stays to the board's end.
  - WORDS (Parts B and C): as in Reading (ADR 026 §2): the pre-teaching table \
{"type": "table", "label": "MATCH <lx: ID> ..."}, a gloss {"type": "gloss", \
"label": "<lx: ID>"} where each listed word is taught and again where it occurs \
in a transcript, a question or an option, and the recap {"type": "table", \
"label": "RECAP <lx: ID> ..."} (for Part C, "RECAP <stimulus ID>"). A gloss of a \
word heard in a recording gets a button that plays the sentence it is heard \
in: code adds it.
  - THE RECORDING plays while the board stays as it is: give the moment its own \
thought only where the board changes.\
"""

PART_A_METHOD = """\
THE PART A LESSON (owner, 2026-10-13; ADR 029, ADR 030). For each extract (gaps \
1-12 and 13-24), in this order:
  1. VOCABULARY WARM-UP, the instructor's method on this set's vocabulary \
(owner, 2026-10-13): a few short sentences of your own, each with one gap, whose \
missing words are words the learner will hear in this set's recordings (medical \
and everyday words); the learner predicts each missing word from the grammar \
and the words around it, then it is shown. Never a sentence of a transcript or \
a form, and never a word that answers a gap of the form. Then a SHORT \
PREDICTION DRILL on the form's stems: the kind of word each gap needs (a body \
part, a medicine, a length of time, a job, a feeling, a number with a unit).
  2. THE LISTENING BOARD (the transcript and the note form, both anchors; no \
board picture): "Table: ..." the headings first (what the conversation will \
cover, in order); "Table: listen": the recording plays once, with the 30 \
seconds to look at the notes; after EACH HEADING'S GROUP of gaps, a \
pause-and-try prompt (the narration's); then one "Row N: ..." thought per gap \
where the lesson fills it, each with ONE short plain note (where the answer was \
said, or why a tempting wrong answer is wrong, from the release's reason). A \
row thought with no block is lost: every row thought has its note.\
"""

PART_B_METHOD = """\
THE PART B LESSON (owner, 2026-10-13; ADR 029, ADR 030). For each extract, in \
this order:
  1. PRE-TEACHING board (MATCH table, a gloss per word), as Reading Part B.
  2. THE LISTENING BOARD (the transcript, anchor; the question in its first \
thought): "Table: the question" (the question block); a gloss of each listed \
word of the stem or options; "Table: listen": the recording plays once, with \
its real reading time, the transcript on screen; a pause-and-try prompt (the \
narration's); "Table: the answer": an answer_row "Answer: <letter>"; "Row N: \
..." on the turns that hold the keywords and the answer (a word of the list \
glossed again in the row thought where it is said); ONE plain note naming the \
paraphrase on the answer's row; "Table: replay": the question's section is \
played again.
  3. WORD-RECAP board (RECAP table), as Reading Part B.\
"""

PART_C_METHOD = """\
THE PART C LESSON (owner, 2026-10-13; ADR 029, ADR 030). For each extract: a \
board of its six stems (the questions' blocks, read in the 90 seconds of \
reading time: keywords, the kind of answer, the opinion question); the \
recording played once in full, with its real reading time, on a LISTENING \
BOARD (the transcript, and the first question: while it plays, the question \
column follows the sections); then, for each question in order: its \
PRE-TEACHING board (the words of its section), then its LISTENING BOARD (the \
transcript, anchor; the question in its first thought): "Table: the question"; \
a pause-and-try prompt (the narration's); "Table: the answer" (an answer_row \
"Answer: <letter>"); "Row N: ..." on the rows of the question's section (from \
the signpost to the evidence); the section replayed ("question N"); the keyword \
pairs, the paraphrase and each wrong option ruled out. After the last question, \
the WORD-RECAP board ("RECAP <stimulus ID>").
  An INTERVIEW extract has no source teaching (owner, 2026-10-13): it carries \
the instructor's presentation method over, and it is an authored section \
(ADR 018), flagged for the owner at the silent preview.\
"""

NARRATION = """\
LISTENING LESSON (ADR 029; owner, 2026-10-13). This lesson teaches the OET \
Listening test. These rules ADD to the others.
  - EXAM FACTS only from the beats and the rulings; a ruling's corrected fact is \
said as plain fact, never "not four options" or "the slide is wrong".
  - Never name, quote or describe the instructor's practice recordings, forms or \
questions, a website, a course series or a Persian audience. Never advise a \
mock test first; never suggest a highlighter.
  - The fact sheet's rulings: a score target is only "the instructor's suggested \
target" (20 of 24, 4 of 6, 8 of 12), and grade B typically needs at least 30 of \
42 marks, varying slightly from test to test; never say abbreviations are \
accepted in Part A (the learner writes the words heard); never call the \
instructions' time extra reading time (only the 30 seconds to look at the Part \
A notes before each extract).
  - Question numbers are the exam's (gaps 1-24, questions 25-42): say them as \
the board shows them.
  - THE RECORDINGS. The release's own audio plays inside the lesson, started by \
a `play` cue: {"type": "play", "text": "<the extract's stimulus ID>", "with": \
"<span>", "block": null, "to_block": null, "to_text": null, "seconds": null}, \
its marker on the LAST word of a SHORT utterance that is the spoken cue ("Now \
listen to Extract 1." or "Listen again to this part."; at most 12 words in its \
last sentence). The recording starts when the utterance ends; the board shows \
that a recording is playing; you never speak over it, and that utterance has \
no pause. Spans: "exam" (the extract as the test plays it: the announcement, \
the real reading time, the tone, the extract), "extract" (from its first word), \
"lines N-M" (transcript rows N to M), "question N" (the section of the talk \
that answers question N) or "heading K" (the section of a note form's K-th \
heading). Each extract is heard ONCE in full with its real reading time \
("exam") before it is discussed; in Parts B and C each question's section is \
replayed ("question N") when that question is discussed. The transcript is on \
screen whenever a recording plays (the first time too) and follows it.
  - PAUSE-AND-TRY PROMPTS (owner, 2026-10-13; ADR 030). In Parts B and C after \
EACH QUESTION is read (before its answer), and in Part A after EACH HEADING'S \
GROUP of gaps (never after every gap), one utterance invites the learner to \
pause the lesson, try to find the answer themselves, then play it again; it \
ends with a `pause` cue of 4 seconds whose `text` is "try it first". VARY THE \
WORDING: never the same sentence twice in the lesson, and no near copy (the \
same sentence with one word swapped, or the same pattern reworded slightly). \
Write each one fresh, in a different shape: a question to the learner, an \
instruction, a challenge, a reason to try. A check fails the lesson on any \
repeat or near copy.
  - A pause of the exam's reading time, where a recording is not played with \
it: a `pause` whose `text` begins "reading time", its `seconds` the extract's \
reading time.
  - Quote a transcript only as it is printed, and mark the words as you say \
them (a keyword pair on a question board).\
"""

NARRATION_PART_A = """\
THE PART A NOTE FORM (ADR 029, ADR 030): on its Listening board, read each \
stem and say the kind of word the gap needs; play the recording ("exam"); after \
each heading's group a pause-and-try prompt (above), replaying that group's \
section ("heading K") where it helps; then for each gap in order, in its row's \
state, say the answer and `type` it, its `text` exactly the answer as the row \
prints it, and, where the release gives one, why a tempting wrong answer is \
wrong.\
"""

NARRATION_QUESTION = """\
A PART B OR C LISTENING BOARD (ADR 029, ADR 030): read the question and its \
three options, A, B and C, word for word, marking their keywords with `match1` \
and `match2` on the question block; play the recording (the transcript is on \
screen and follows it); a pause-and-try prompt (above); say the answer; read \
the part of the transcript that holds it, the keyword pairs between the option \
and the transcript in one match type, the paraphrase bridge, each wrong option \
ruled out (reveal its part as you give the reason), the tick last; replay the \
question's section ("question N"). On the paper test, Parts B and C answers \
are shaded with a 2B pencil.\
"""

QA = """\
LISTENING LESSON (ADR 029). The lesson teaches the OET Listening test. The \
practice set's transcripts, note forms and questions (blocks built from the \
release, shown exactly as released) are not findings: never suggest changing \
their wording. Question numbers are the exam's (1-24, 25-30, 31-42), never \
renumbered. Report any recording, form, question or speaker of the \
instructor's own practice material named, quoted or described; any reference \
to a website, a course series or a Persian audience; any exam fact not in the \
rulings; any claim about a tool of the computer test; any advice to take a mock \
test first or to use a highlighter; narration spoken over a recording; and any \
match mark pair whose two places do not say the same thing; and any \
pause-and-try prompt that repeats another's sentence or pattern.\
"""


def intro_first(text: str) -> str:
    """The first lesson of the Listening course (owner, 2026-10-13; ADR 014
    amendment): why listening matters, not why grammar matters."""
    import re
    text = text.replace("notes: why grammar matters, the lesson's", "notes: why listening matters, the lesson's")
    return re.sub(
        r"  2\. Explains simply why grammar matters in the OET letter:.*?No grade or score promises\.",
        "  2. Explains simply why listening matters: at work, healthcare professionals "
        "listen to patients, colleagues and handovers, and must catch the right "
        "information exactly; and Listening is one of the four parts of OET. No grade "
        "or score promises.", text, flags=re.S)


def intro(text: str) -> str:
    """Any other Listening lesson's introduction: why the topic matters for the
    learner's listening; never a second welcome to the course."""
    return (text.replace("why this topic matters for the student's letters",
                         "why this topic matters for the learner's listening at work and in OET")
            + "\nLISTENING COURSE (ADR 029): this lesson continues the Listening course. "
              "Open warmly and in your own words, but do not welcome the learner to "
              "the course again.")


def codes(lesson: Path) -> set[str]:
    ps = practice_set.load(lesson) or {}
    return {p.get("code") for p in ps.get("parts") or []}


def section_teaches_set(lesson: Path, pages: list[int]) -> bool:
    ps = practice_set.load(lesson) or {}
    return bool(set(ps.get("teach_pages") or []) & set(pages))


def set_text(lesson: Path, pages: list[int]) -> str:
    """The practice set, by ID, for a section that teaches it, or its
    recordings named only, for another section; '' with no set."""
    ps = practice_set.load(lesson)
    if not ps:
        return ""
    stims = practice_set.stimuli(ps)
    if not section_teaches_set(lesson, pages):
        return (f"THIS LESSON'S PRACTICE SET ({ps['set_id']}, ADR 029), taught in another section. "
                "Where this section needs an example, name its recordings by label only; never "
                "quote them:\n" + "\n".join(f"  {st['label']}" for st in stims.values()))
    c = codes(lesson)
    out = [SCREENS_SET] + ([PART_A_METHOD] if "LA" in c else []) + ([PART_B_METHOD] if "LB" in c else []) \
        + ([PART_C_METHOD] if "LC" in c else []) + [f"PRACTICE SET {ps['set_id']}:"]
    out += [practice_set.transcript_for_prompt(ps, st) for st in stims.values() if practice_set.is_audio(st)]
    for it in practice_set.items(ps).values():
        out.append(practice_set.form_for_prompt(ps, it) if practice_set.is_gapfill(it)
                   else practice_set.question_for_prompt(ps, it))
    if "LB" in c:
        import vocab                         # the word bank's words, by ID (ADR 026 §2)
        out.append(vocab.words_for_prompt(lesson))
    if "LC" in c:
        import vocab
        out.append(vocab.words_for_prompt_part_c(lesson))
    return "\n\n".join(out)


def narration_text(lesson: Path, scr: dict) -> str:
    """What the narration stage adds for a Listening section: the rule, and the
    Part A form's or a question board's steps where the section has them."""
    blocks = [b for t in scr.get("topics") or [] for h in t["thoughts"] for b in h["blocks"]]
    out = [NARRATION]
    if any((b.get("doc") or {}).get("text_type") == "form" for b in blocks):
        out.append(NARRATION_PART_A)
    if any((b.get("question") or {}).get("options") for b in blocks):
        out.append(NARRATION_QUESTION)
    return "\n\n".join(out)


# ---- pause-and-try prompts (owner, 2026-10-13; ADR 030) ----

PROMPT_PAUSE = "try it first"     # the `text` of the pause that ends a pause-and-try prompt
NEAR_RATIO = 0.8                  # two sentences of four words or more this alike are near copies


def prompts(boards: list[dict]) -> list[tuple[str, str]]:
    """A narration's pause-and-try prompts, (utterance id, words said): each
    utterance with a `pause` cue whose text begins "try it first"."""
    from write_narration import spoken
    out = []
    for bd in boards:
        for s in bd["states"]:
            for u in s["utterances"]:
                if any(c.get("type") == "pause" and (c.get("text") or "").strip().lower().startswith(PROMPT_PAUSE)
                       for c in u.get("cues") or []):
                    out.append((u["id"], spoken(u["text_with_cues"])))
    return out


def _sentences(text: str) -> list[list[str]]:
    return [w for w in (re.findall(r"[a-z0-9']+", x.lower()) for x in re.split(r"(?<=[.?!])\s+", text)) if w]


def near_copy(a: list[str], b: list[str]) -> bool:
    """The same sentence, or a near copy: one word swapped, or (four words or
    more) alike by NEAR_RATIO of their words in order."""
    if a == b:
        return True
    if len(a) == len(b) and len(a) >= 3 and sum(x != y for x, y in zip(a, b)) <= 1:
        return True
    return min(len(a), len(b)) >= 4 and difflib.SequenceMatcher(a=a, b=b, autojunk=False).ratio() >= NEAR_RATIO


def prompt_findings(mine: list[tuple[str, str]], others: list[tuple[str, str]] = ()) -> list[tuple[str, str]]:
    """(utterance id, what) for each prompt of `mine` with a sentence that is
    another prompt's (of `mine`, or of `others`: the lesson's other sections)."""
    out = []
    for i, (uid, text) in enumerate(mine):
        for vid, other in list(mine[:i]) + list(others):
            hit = next(((a, b) for a in _sentences(text) for b in _sentences(other) if near_copy(a, b)), None)
            if hit:
                same = hit[0] == hit[1]
                out.append((uid, f"pause-and-try prompt {'repeats' if same else 'nearly repeats'} {vid}: "
                                 f"{' '.join(hit[0])!r} / {' '.join(hit[1])!r}: word each one fresh (ADR 030)"))
                break
    return out


def lesson_prompts(lesson: Path, skip: str | None = None) -> list[tuple[str, str]]:
    """Every narrated section's prompts (analysis/narration/<tag>/narration.json),
    but the section `skip`."""
    out = []
    for f in sorted((Path(lesson) / "analysis" / "narration").glob("*/narration.json")):
        if f.parent.name == skip:
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        out += [(f"{f.parent.name}:{uid}", t) for uid, t in prompts(d.get("boards") or [])]
    return out


def main() -> None:
    lesson = Path(sys.argv[1])
    if "--prompts" in sys.argv:
        found = prompt_findings(lesson_prompts(lesson))
        for uid, what in found:
            print(f"FAIL {uid}: {what}")
        n = len(lesson_prompts(lesson))
        print(f"{n} pause-and-try prompt(s); {len(found)} repeated or near copies")
        sys.exit(1 if found else 0)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
