"""The Listening-lesson rule (docs/adr/029-listening-lessons.md; owner, 2026-10-13):
what the screens, narration and QA prompts add for a lesson of type listening
(lesson_type.py), as reading_rule.py does for Reading (ADR 026) and
vocabulary_rule.py for vocabulary lessons (ADR 019).

A Listening lesson teaches the pinned release's sets (practice_set.py,
sample-tests-v2): code builds every transcript, note form and question from
its ID, exactly as released, and the release's own audio plays inside the
lesson's clock (a narration `play` cue; bundle 1.18). Exam facts come only from
the beats, the rulings and the verified fact sheet (docs/listening-facts.md,
once the owner has verified it).
"""

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
  - QUESTION NUMBERS ARE THE EXAM'S (owner, 2026-10-13): Part A gaps 1-24, Part B \
questions 25-30, Part C questions 31-42, because the recordings announce them. \
Never renumber them from 1.
  - THE LEARNER NEVER TYPES. A Part A note form is shown on a board and the \
lesson fills each gap after "try it first".
  - A WORD ON A BOARD is never a transcript's: you never copy, quote in a block \
of your own, shorten or paraphrase a transcript, a note form or a question.\
"""

SCREENS_SET = """\
THE PRACTICE SET OF THIS LESSON (ADR 029). Its recordings' transcripts, its note \
forms and its questions are listed below, by ID, exactly as the board will show \
them. CODE BUILDS THEM; the release's own audio plays in the lesson (the \
narration starts it).
  - A TRANSCRIPT: write {"type": "table", "label": "<the extract's stimulus ID>", \
"anchor": true}, with NO header and NO rows. Its rows are the released lines \
(a speaker's turn, or a paragraph of a talk), numbered as listed. It is the \
fixed layer of a board of its own (a TABLE BOARD). A transcript stays COVERED \
until the question it answers has been solved (owner, 2026-10-13): those \
thoughts are named "Covered: ...". Then it is shown in PARTS, never scrolled: \
a thought named "Para N-M: ..." shows rows N to M whole (a heading's section of \
a Part A conversation, or the section of the recording a Part B or C question \
is answered from; one row is "Para N: ..."); "Map: ..." shows the whole \
transcript, too small to read, to say where we are ("Map PN: ..." marks row \
N). A Part B transcript is short and is shown whole once uncovered (thoughts \
"Row N: ..." on the rows read).
  - A PART A NOTE FORM: write {"type": "table", "label": "<the gap-fill item \
ID>", "anchor": true}, with NO header and NO rows. Its rows are listed below: a \
row for each heading and a numbered row for each gap. It is the fixed layer of \
a TABLE BOARD: one "Row N: ..." thought per gap, in order. Code types each gap's \
answer in its exact form; the narration types it.
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
thought only where the board changes (a new part of the transcript).\
"""

PART_A_METHOD = """\
THE PART A LESSON (owner, 2026-10-13; ADR 029). For each extract (gaps 1-12 and \
13-24), in this order:
  1. VOCABULARY WARM-UP, the instructor's method on this set's vocabulary \
(owner, 2026-10-13): a few short sentences of your own, each with one gap, whose \
missing words are words the learner will hear in this set's recordings (medical \
and everyday words); the learner predicts each missing word from the grammar \
and the words around it, then it is shown. Never a sentence of a transcript or \
a form, and never a word that answers a gap of the form. Then a SHORT \
PREDICTION DRILL on the form's stems: the kind of word each gap needs (a body \
part, a medicine, a length of time, a job, a feeling, a number with a unit).
  2. THE NOTE FORM BOARD (its fixed layer the form; it has NO board picture: the \
form is its picture, and the two do not fit together): "Table: ..." the \
headings first (what the conversation will cover, in order); then "Row N: ..." \
for each gap, the stem read and the kind of word predicted (one short plain \
note each); "Table: listen": the recording plays once (the narration plays it); \
"Table: try it first": ONE short plain note inviting the learner to write each \
answer before it is shown; then one "Row N: ..." thought per gap where the \
lesson fills it, each with ONE short plain note (where the answer was said, or \
why a tempting wrong answer is wrong, from the release's reason). A row \
thought with no block is lost: every row thought has its note.
  3. THE TRANSCRIPT, by heading: a board whose fixed layer is the transcript, \
"Covered: ..." first, then one "Para N-M: ..." thought per heading, the rows \
that hold that heading's gaps, each answer's words found where they are said.\
"""

PART_B_METHOD = """\
THE PART B LESSON (owner, 2026-10-13; ADR 029). For each extract, in this order:
  1. PRE-TEACHING board (MATCH table, a gloss per word), as Reading Part B.
  2. QUESTION board, its fixed layer the TRANSCRIPT: "Covered: the question" (the \
question block only); "Covered: ..." a gloss of each listed word of the stem or \
options; "Covered: listen": the recording plays once, with its real reading \
time; "Covered: try it first": ONE short plain note; "Covered: the answer": \
an answer_row "Answer: <letter>"; then the transcript appears, whole: "Row N: \
..." on the turns that hold the keywords and the answer (a word of the list \
glossed again in the row thought where it is said); ONE plain note naming the \
paraphrase on the answer's row; "Table: replay": the part of the recording that \
holds the answer is played again.
  3. WORD-RECAP board (RECAP table), as Reading Part B.\
"""

PART_C_METHOD = """\
THE PART C LESSON (owner, 2026-10-13; ADR 029). For each extract: a board of its \
six stems (the questions' blocks, read in the 90 seconds of reading time: \
keywords, the kind of answer, the opinion question); the recording played once \
in full, with its real reading time; then, for each question in order: its \
PRE-TEACHING board (the words of its section), then its QUESTION board, its \
fixed layer the TRANSCRIPT: "Covered: the question" (the question block only); \
"Covered: the answer" (an answer_row "Answer: <letter>"); then "Para N-M: ..." \
the rows of the question's section, whole (the turns from the cue to the \
evidence; a section too long to fit is shown as two neighbouring parts, one \
after the other); the section replayed; the keyword pairs, the paraphrase and \
each wrong option ruled out. After the last question, the WORD-RECAP board \
("RECAP <stimulus ID>").
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
"lines N-M" (transcript rows N to M, a replay of one part). Each extract is \
heard ONCE in full with its real reading time ("exam") before it is discussed; \
in Parts B and C the part that answers each question is replayed ("lines N-M") \
when that question is discussed.
  - A pause of the exam's reading time, where a recording is not played with \
it: a `pause` whose `text` begins "reading time", its `seconds` the extract's \
reading time.
  - Quote a transcript only as it is printed, and mark the words as you say \
them (a keyword pair on a question board).\
"""

NARRATION_PART_A = """\
THE PART A NOTE FORM (ADR 029): on the form board, read each stem and say the \
kind of word the gap needs; play the recording ("exam"); try it first: invite \
the learner to write each answer, then a `pause` of 4 seconds; then for each gap \
in order, in its row's state, say the answer and `type` it, its `text` exactly \
the answer as the row prints it, and, where the release gives one, why a \
tempting wrong answer is wrong.\
"""

NARRATION_QUESTION = """\
A PART B OR C QUESTION BOARD (ADR 029): while the transcript is COVERED, read \
the question and its three options, A, B and C, word for word, marking their \
keywords with `match1` and `match2` on the question block; play the recording; \
try it first (a `pause` of 4 seconds); say the answer. Only then is the \
transcript shown: read the part that holds the answer, the keyword pairs \
between the option and the transcript in one match type, the paraphrase \
bridge, each wrong option ruled out (reveal its part as you give the reason), \
the tick last. In a covered state read nothing from the transcript and mark \
nothing in it. On the paper test, Parts B and C answers are shaded with a 2B \
pencil.\
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
match mark pair whose two places do not say the same thing.\
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
