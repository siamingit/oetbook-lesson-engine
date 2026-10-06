"""The Reading-lesson rule (docs/adr/026-reading-lessons.md; maintainer,
2026-10-05): what the screens, narration and QA prompts add for a lesson whose
type is reading (its id's first word, as in the course index), as
vocabulary_rule.py does for vocabulary lessons (ADR 019).

A Reading lesson that teaches a practice set gets the set's texts and
questions by ID (practice_set.py): code builds them, the model never writes
them, and they are shown exactly as released.
"""

import re
from pathlib import Path

import practice_set


def is_reading(lesson: Path) -> bool:
    return Path(lesson).name.split("-")[0].lower() == "reading"


NOTE = "reading rule (ADR 026)"

# The keyword-pair marks (ADR 026, bundle 1.13): one colour per pair, meaning
# only "these words correspond". Drawn at 55% over the text.
MATCH_COLOURS = {"match1": "#0688F9", "match2": "#A860FB", "match3": "#F9E806"}
MATCH_TYPES = list(MATCH_COLOURS)

SCREENS = """\
READING LESSON (docs/adr/026-reading-lessons.md; maintainer, 2026-10-05). This \
lesson teaches the OET READING test, not grammar. Where these instructions speak \
of grammar terms, exercise sentences or letters, read them as the reading \
strategies, the texts and the questions this section teaches. The rules below \
ADD to the rest of these instructions; everything else holds (A2-B1 wording, \
DO NOT ADD TEACHING, NEVER JUDGE REGISTER, one board per slide, the board style).
  - EXAM FACTS. Only the facts in the beats and in the MAINTAINER RULINGS. Where \
a ruling corrects the source (a grade, a time, a number of questions or texts), \
teach the ruling's version as plain fact and never mention the error.
  - RICHER THAN THE SLIDE. Every graphic helps understanding: a TIMELINE for time \
(the 60 minutes of the test, the 15 minutes of Part A; give every part a family \
as usual: this is not a tense lesson, so every family is drawn neutral), a COMPARISON for a before-and-after or a \
conversion (a score to a grade), a small TABLE for a map of parts and skills, a \
timeline of points or category cards for a path of steps. One graphic per idea; \
never decoration. A graphic is a block on its slide's ONE board, like any other: \
a path of four steps is one board whose steps are revealed one by one, never a \
board per step (TOPICS ARE BOARDS, AND A BOARD IS A SLIDE).
  - SMALL TABLES. A table you write has two columns, or at most three rows: a \
table of three or more columns and four or more rows is a SUMMARY TABLE, which \
must be the first board's whole fixed layer. A map of four texts is two \
columns ("Text" | "What it covers"); a score plan is two ("Part" | "Correct \
answers to aim for").
  - A LIGHT FIXED LAYER. Anchor only the slide's own short content, at most \
about four short lines (a list of tips or of dos and don'ts is anchored as one \
plain block per item, and the explanations are notes). A list longer than \
that is split BY MEANING into two boards at most, never more: a slide of dos \
and don'ts is "Split: dos" and "Split: don'ts".
  - OFFICIAL OET SAMPLE TEXTS NEVER APPEAR: no text, title, sentence, \
paraphrase or description of one, even where the beats quote the source's \
examples. The instructor's TEACHING carries over (his strategies, his \
explanations, his order) and is applied to this lesson's own practice set where \
the section has one.
  - PAPER-ONLY ADVICE (a pen, underlining, crossing out instead of erasing) is \
advice for the paper test: say so on the block ("On the paper test, ..."). Never \
name a tool of the computer test.
  - PEN, PENCIL, NEVER A HIGHLIGHTER (maintainer, 2026-10-06, verified on \
oet.com). Reading and Listening Part A: a pen or a pencil. Parts B and C: the \
answer is shaded with a 2B pencil, and on paper only a shaded circle counts (no \
tick, cross or circling). Mechanical pens and pencils, highlighters and \
correction fluid are not allowed. Nothing in a lesson suggests a highlighter \
for the test, in words or in a picture: the highlight on a board is only how \
the lesson shows the words.
  - NEVER ADVISE TAKING A MOCK TEST FIRST (maintainer, 2026-10-06): no block \
tells the learner to take a mock test, a practice test or any full test before \
studying, even where the beats do; record such a beat under `dropped`.
  - NO GLOSS inside a practice set's texts or questions: they are shown exactly \
as released. The gloss rule applies to your own teaching blocks only.\
"""

SCREENS_SET = """\
THE PRACTICE SET OF THIS LESSON (ADR 026). Its texts and questions are listed \
below, by ID. They are shown EXACTLY as released: you never copy, quote in a \
block of your own, shorten, reorder or paraphrase them. CODE BUILDS THEM:
  - A TEXT is a DOCUMENT: write a block {"type": "table", "label": "<its \
stimulus ID>", "anchor": true}, with NO header and NO rows (code fills them \
from the release). It is the fixed layer of a TABLE BOARD of its own, and its \
ROWS are the document's parts as numbered below: teach it with thoughts whose \
`purpose` starts "Row N: " (N as listed) or "Table: " for the whole text, as on \
any table board. The SKIMMING PATH is a sequence of row thoughts, ONE FOR EACH \
PART THAT WILL BE READ ALOUD (maintainer, 2026-10-06): every heading, first \
sentence, list item, table row or bold line the instructor skims gets its own \
row thought, in reading order (four headings are four row thoughts); the \
narration reads a part only in its own row thought. A SCANNING path is a row \
thought on the part that holds the answer. Nothing is typed into a document. Side notes go under it as on any \
table board, at most one or two short ones per thought.
  - A QUESTION is written {"type": "plain", "label": "<its item ID>", "anchor": \
false}, with NO text: code writes its number and its wording. Put it in the \
FIRST thought of its board (purpose "Table: the question"); it stays on the \
board to the end. Then the row thought(s) where its keywords are found, then \
the answer as an answer_row in the EXACT form the text gives (the key below), \
and, where the release gives one, a note on why a tempting wrong answer is \
wrong (its reason, in your plain words). One board per question: its fixed \
layer is the DOCUMENT that holds the answer (for a matching question, the key's \
text). Its `title` is "Item <number>: <item ID>". (Part A questions use the \
MAP instead: see THE PART A QUESTION METHOD.)
  - BOARDS. A section that demonstrates skimming has one board per text, in \
order A to D, each with its document as the fixed layer. A section that works \
through the questions has, in this order: the slide's own board; where its \
beats skim the texts again before the questions, one board per text; one short \
board (plain blocks only) that names the three question groups and how many \
minutes each gets; one board per question, in question order. Any teaching that \
comes after the last question (a conclusion, study advice) is the last \
question board's final thoughts, never a board of its own. These boards are \
this section's exercise items: the audit counts them like exercise items. Every \
beat is used or recorded under `dropped`: a beat about how the instructor \
solved one practice question becomes the same move on the matching question of \
this set.
  - KEYWORDS ON SCREEN are marked by the narration (same-colour pairs), not \
written as blocks: never write a block that lists the question's keywords \
again.\
"""

NARRATION = """\
READING LESSON (ADR 026; maintainer, 2026-10-05). This lesson teaches the OET \
Reading test. These rules ADD to the others.
  - EXAM FACTS only from the beats and the rulings; a ruling's corrected fact is \
said as plain fact, never "not B+" or "the slide is wrong".
  - Paper-only advice is said as advice for the paper test. Never describe a \
tool of the computer test.
  - Never advise taking a mock test, or any full practice test, before \
studying (maintainer, 2026-10-06).
  - Never suggest a highlighter for the test: highlighters are not allowed. \
Part A: a pen or a pencil. Parts B and C: shade the answer's circle with a 2B \
pencil; only a shaded circle counts (maintainer, 2026-10-06, from oet.com). The \
highlight on the board is how this lesson shows words, not a tool.
  - Official OET sample texts are never named, quoted or described.
  - A practice-set text or question on the board is read EXACTLY as printed when \
you read it aloud (quote it word for word, or do not quote it).\
"""

PART_A_METHOD = """\
THE PART A QUESTION METHOD (maintainer, 2026-10-06; ADR 026). Every Part A \
question board teaches the instructor's method in five steps, so the learner \
searches before the answer is shown. Its fixed layer is the MAP of the four \
texts: write {"type": "table", "label": "MAP", "anchor": true} with NO header \
and NO rows (code draws the four texts small, side by side: too small to read, \
on purpose). Never put a text's stimulus ID on a question board: the map \
replaces it. Its thoughts, in this order:
  1. "Table: the question": the question block, nothing else.
  2. "Table: try it first": ONE short plain note inviting the learner to find \
the answer first ("Try it first: which text has the answer?").
  3. "Text <letter>: ...": ONE or TWO short plain notes: from the question's \
keywords, which text must hold the answer, and why the others are ruled out \
(the instructor's "eliminating texts" move), e.g. "Only Text D is about \
checks after treatment." The other texts dim.
  4. "Zoom <letter>: ...": ONE short plain note naming where in that text to \
look (its heading or section). The map zooms into that text.
  5. "Row <letter><N>: ..." (N as that text's rows are numbered below, e.g. \
"Row D3: ..."): the part that holds the answer, as on a table board: the row \
thought(s) where the keywords are found, then the answer as an answer_row in \
the EXACT form, and where the release gives one, a note on why a tempting wrong \
answer is wrong.
For a matching question, the text of steps 3 to 5 is the key's text. One board \
per question, in question order; its `title` is "Item <number>: <item ID>".\
"""

PART_B_METHOD = """\
THE PART B LESSON (maintainer, 2026-10-06; ADR 026, the Part B question method and \
the vocabulary layer). For Part B this REPLACES the QUESTION and BOARDS paragraphs \
above (the document, keyword and gloss rules stay). Every text of the set that this \
section teaches gets THREE \
BOARDS, in this order: its PRE-TEACHING board, its QUESTION board, its WORD-RECAP \
board. The words of each text are listed below under WORDS OF <stimulus ID>, by \
their lx: IDs. Code builds every word block from its ID (meaning, synonym, example \
and picture from the word bank): you never write a meaning, synonym or example of \
your own.
  1. PRE-TEACHING BOARD (the instructor's word-to-meaning matching table). Its \
fixed layer: {"type": "table", "label": "MATCH <lx: ID> <lx: ID> ...", "anchor": \
true}, the text's word IDs in the order listed, with NO header and NO rows (code \
writes the words in column 1 and their meanings in column 2 in another order, so \
the learner matches them). Thoughts: "Table: ..." with ONE plain note inviting the \
learner to match each word with its meaning first; then one "Row N: ..." thought \
per word, in row order, holding ONE block: that word's gloss, written {"type": \
"gloss", "label": "<its lx: ID>"} with nothing else in it. Where a MAINTAINER \
RULING names a collocation pair (an adjective or adverb with the noun or verb it \
goes with, as the text prints them) or an attributive-noun chain (adjective + \
qualifier noun + head noun, from an option) for this text, add after the word \
rows ONE "Table: ..." thought with a small table of one row in the instructor's \
format, its cells the text's own words exactly as printed (header \
["Adjective", "Noun"], or ["Adjective", "Qualifier noun", "Head noun"]), and one \
plain note: for a chain, that the qualifier is a NOUN used as a modifier, never \
an adjective.
  2. QUESTION BOARD. Its fixed layer is the DOCUMENT of the text ({"type": \
"table", "label": "<stimulus ID>", "anchor": true}). Its thoughts, in order:
     a. "Covered: the question": ONLY the question block, {"type": "plain", \
"label": "<item ID>", "items": [...]}, with NO text. Its `items` rule the wrong \
options out and tick the answer, in this order: "out|<letter>|<reason label>" for \
EACH WRONG option (the label at most 12 plain words, A2-B1, saying why it is \
wrong, based on the release's own reason for that option, never adding a fact), \
then "key|<letter>" for the answer. The text stays COVERED in every "Covered:" \
thought, as the instructor covers it until the question and the options are read.
     b. "Covered: ..." thoughts, one per word of the question or the options that \
the word list names (where: question / option X), each holding that word's gloss \
({"type": "gloss", "label": "<lx: ID>"}).
     c. "Covered: try it first": ONE short plain note inviting the learner to \
choose before the text appears ("Try it first: which option is right?").
     d. Then the text appears: "Row N: ..." thoughts on the parts that hold the \
keywords and the answer, in reading order; each word the list names in the text \
is glossed again in the row thought of the part where it occurs (one gloss per \
thought). Then, on the row that holds the answer, ONE plain note naming the \
paraphrase: how the text's words and the right option say the same thing. Where \
the release's reason for a wrong option points at a part of the text, a row \
thought there may hold ONE short plain note.
     e. "Table: the answer": an answer_row "Answer: <letter>", and nothing else.
  3. WORD-RECAP BOARD. Its fixed layer: {"type": "table", "label": "RECAP <lx: \
ID> ...", "anchor": true}, the same IDs as the pre-teaching board, NO header and \
NO rows (code writes word, meaning, synonym). ONE thought, "Table: recap", with \
ONE plain note ("The words of Text N").
  Every board keeps the board style. No board of the section shows anything of an \
official OET sample text or of the instructor's own practice texts.\
"""

NARRATION_PART_B = """\
THE PART B LESSON (maintainer, 2026-10-06; ADR 026). These rules ADD to the others.
  - PRE-TEACHING BOARD: first invite the learner to match the words with their \
meanings, then a `pause` of 3 seconds. Then, row by row: say the word, draw an \
`arrow` from the word in its row (`text` the word as the table prints it) to its \
meaning (`to_text` a phrase of the meaning as the table prints it), then the \
word's gloss moment (the gloss rule: the word, a pause, its meaning, its synonym, \
its example, a pause). A small collocation or chain table is read cell by cell, \
each cell marked, and the note said: the qualifier is a noun used as a modifier.
  - QUESTION BOARD, the eight steps of the Part B question method, in order:
     1. The question (a COVERED state: the text cannot be seen): read the question \
word for word and mark its keywords with `match1` (and `match2`) on the question \
block.
     2. The options (QAT: Question, Answers, then Text), still COVERED: read each \
option, A, B and C, word for word, naming its letter, and `underline` its keywords \
in the question block, as the instructor underlines them. Reveal the glosses of \
the option and question words as you meet them (gloss moments).
     3. Try it first, still COVERED: invite the learner to pause the lesson and \
choose an option, then end the state with a `pause` of 4 seconds.
     4. The text appears (the first uncovered state): say so, and read the parts \
you need, each phrase marked.
     5. Keyword pairs: mark a keyword of the question or of an option and the \
words of the text that match it with ONE match type, the question's or the \
option's words first (`match1`, `match2`, `match3`; at most three pairs a board). \
Gloss again each listed word of the text where it occurs.
     6. The paraphrase bridge: the text's wording and the right option's wording \
in ONE match type, and one sentence on how they say the same thing.
     7. Rule each wrong option out: reveal its part (`<question id>.<n>`, the \
option struck and its reason label shown) as you give the reason in a short \
sentence that agrees with the label.
     8. Confirm the answer: reveal the tick part and say the letter and the option.
     In a COVERED state read nothing from the text and mark nothing in it; the \
question block stays on the board for the whole board (it is pinned), so steps 5 \
to 8 mark it and reveal its parts in later states.
  - WORD-RECAP BOARD: read each word and its meaning, row by row, each word \
`highlight`ed as you say it, briskly; a closing sentence links to the next text.
  - On the paper test, Part B answers are shaded with a 2B pencil; only a shaded \
circle counts. Never suggest a highlighter.\
"""

NARRATION_SET = """\
KEYWORD PAIRS (ADR 026, bundle 1.13). Three extra mark types draw a pair of \
places in ONE colour, meaning "these words correspond": `match1` (sky blue), \
`match2` (violet), `match3` (yellow). On a question board:
  - mark each KEYWORD of the question with a match type, and the WORDS IN THE \
TEXT that match it with THE SAME type, in the same state: question first, then \
the text ("The question says 'breathlessness'. {{c1}}In Text B, we find \
{{c2}}shortness of breath."). Use match1 for the first pair on the board, match2 for \
the second, match3 for a third; at most three pairs a board.
  - THE PARAPHRASE BRIDGE: when the answer is found, mark the text's wording \
and the answer's wording with one match type, and say in one sentence how they \
say the same thing.
  - Use `highlight` (amber) for nothing on a question board: keywords and \
their matches are match marks.
  - On a skimming board, mark the parts you skim (a heading, a first sentence, \
a number) with `highlight`, as the instructor highlights them, in reading \
order, as the spotlight moves: that is the skimming path. Never `underline` or \
`circle` on a skimming board.
  - The answer is said and shown in its EXACT form from the text ("nil by \
mouth", "twice daily"), and a wrong form is named only where the release gives \
it as a tempting wrong answer.
  - EVERY WORD YOU READ FROM A TEXT IS MARKED (maintainer, 2026-10-06; checked \
by code: a draft that breaks it fails). Each time you read aloud or quote words \
printed in a text (a heading, a step, a number, a list item, the words that \
hold the answer), put a mark cue on EXACTLY those words as the text prints \
them, its marker JUST BEFORE you say them: `highlight` on a skimming board, the \
pair's type (match1 to match3) on a question board. One mark per phrase: three \
headings read are three marks. Never read words of a text without their mark; \
to avoid a mark, do not read them. On a skimming board, read each part in the \
state whose row is that part.
  - THE MAP (Part A question boards): the fixed layer is the map of the four \
texts, and each state says what it shows (`map`). Narrate the five steps: (1) \
the question: read it word for word and mark its keywords with match types on \
the question block; (2) try it first: invite the learner to pause the lesson \
and find where the answer is, then end the state with a `pause` cue of 4 \
seconds; (3) the text: say which text must hold the answer and rule the others \
out from the keywords; read nothing from the texts here, they are too small; \
(4) the zoom: say where in the text you are going and highlight that heading \
as you name it; (5) the part: the keyword pairs between the question and the \
text, the paraphrase bridge and the answer in its exact form, as on any \
question board.\
"""

QA_PART_B = """\
PART B (ADR 026; bundle 1.15). Word glosses, matching tables and recap tables are \
built from the exercises repository's word bank: their meanings, synonyms and \
examples are not findings. Report a wrong option's reason label that does not \
agree with the text, a paraphrase bridge whose two places do not say the same \
thing, and any reading of the text while it is covered.\
"""

QA = """\
READING LESSON (ADR 026). The lesson teaches the OET Reading test. The \
practice set's texts and questions (blocks built from the release, shown \
exactly as released) are not findings: never suggest changing their wording. \
The exam facts in the maintainer rulings are correct (OET grades A, B, C+, C, \
D, E; target Grade B, 350; Reading 60 minutes, Part A 15 minutes separately, \
Parts B and C 45 minutes; every question one mark). Report any official OET \
sample text named, quoted or described, any claim about a tool of the computer \
test, any advice to take a mock test first, any suggestion of a highlighter \
for the test, and any match mark pair whose two places do not say the same thing.\
"""


def intro_first(text: str) -> str:
    """The first lesson of the Reading course (ADR 026 §4; ADR 014 amendment):
    why reading matters, not why grammar matters."""
    text = text.replace("notes: why grammar matters, the lesson's", "notes: why reading matters, the lesson's")
    return re.sub(
        r"  2\. Explains simply why grammar matters in the OET letter:.*?No grade or score promises\.",
        "  2. Explains simply why reading matters: at work, healthcare professionals "
        "read guidelines, policies, notes and emails, and must find the right "
        "information quickly and exactly; and Reading is one of the four parts of "
        "OET. No grade or score promises.", text, flags=re.S)


def intro(text: str) -> str:
    """Any other Reading lesson's introduction: why the topic matters for the
    learner's reading, not their letters; never a second welcome to the course."""
    return (text.replace("why this topic matters for the student's letters",
                     "why this topic matters for the student's reading at work and in OET")
            + "\nREADING COURSE (ADR 026 §4): this lesson continues the Reading course. "
              "Open warmly and in your own words, but do not welcome the learner to "
              "the course again.")


def set_text(lesson: Path, pages: list[int]) -> str:
    """The practice set, by ID, for a section that teaches it, or ''."""
    ps = practice_set.load(lesson)
    if not ps:
        return ""
    if not section_teaches_set(lesson, pages):
        # another section of the lesson may name the set's texts (their labels,
        # titles and types), never quote them
        return (f"THIS LESSON'S PRACTICE SET ({ps['set_id']}, ADR 026), taught in another section. "
                "Where this section needs an example of the four texts, name them by label, "
                "title and type only; never quote them:\n" + "\n".join(
                    f"  {st['label']}: {st.get('title') or '(no title)'}; a {st.get('text_type') or 'text'}"
                    for st in practice_set.stimuli(ps).values()))
    part_a = any(p.get("code") == "RA" for p in ps.get("parts") or [])
    part_b = any(p.get("code") == "RB" for p in ps.get("parts") or [])
    out = [SCREENS_SET] + ([PART_A_METHOD] if part_a else []) + ([PART_B_METHOD] if part_b else []) \
        + [f"PRACTICE SET {ps['set_id']}:"]
    out += [practice_set.document_for_prompt(st) for st in practice_set.stimuli(ps).values()]
    out += [practice_set.question_for_prompt(ps, it) for it in practice_set.items(ps).values()]
    if part_b:
        import vocab                         # the word bank's words, by ID (ADR 026 §2)
        out.append(vocab.words_for_prompt(lesson))
    return "\n\n".join(out)


def is_part_b(lesson: Path) -> bool:
    ps = practice_set.load(lesson) or {}
    return any(p.get("code") == "RB" for p in ps.get("parts") or [])


def section_teaches_set(lesson: Path, pages: list[int]) -> bool:
    """The sections that teach the set: practice_set.json `teach_pages`, set
    by the agent with practice_set.py --teach-pages and logged (ADR 005)."""
    ps = practice_set.load(lesson) or {}
    return bool(set(ps.get("teach_pages") or []) & set(pages))
