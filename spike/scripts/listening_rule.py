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
thought only where the board changes.
  - THE VOCABULARY PANEL (owner, 2026-10-14; ADR 031). The instructor teaches \
every difficult word, verb, phrase and expression of a recording: its meaning \
in simple English, a synonym or two and an example. On every Listening board, \
after the pause-and-try prompt and the answer, teach the transcript's own \
words in its panel (under the transcript's box): medical terms, everyday verbs \
and phrasal verbs, idioms and spoken expressions, and above all the PARAPHRASE \
PAIRS, a word of a question, an option or the notes that the speaker says \
differently. Each is a gloss {"type": "gloss", "label": "PANEL Row <N>", \
"kind": "medical" | "verb" | "phrase" | "idiom" | "word" | "paraphrase", \
"term": "<the words as the speaker says them in transcript row N>", \
"explanation": "<the meaning: plain English, at most 8 words>", "synonym": \
"<one or two synonyms, separated by a comma>", "text": "<ONE short example \
sentence of YOUR OWN, at most 14 words, using the term; never a sentence or \
four words in a row of a transcript or a question>", "left": "<a paraphrase \
pair only: the question's, option's or notes' words, exactly as printed>"}. \
Code finds the term in row N, adds the button that plays the sentence it is \
said in, and shows a pair or an answer word only once its answer is taught. \
At most 2 panel items a thought; a thought "Row <N>: ..." (the row of the \
first) after the answer's. A word of the word bank's list keeps its own gloss \
(above): never a panel item. No register words (formal, informal, common, \
natural, polite...).\
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
pause the lesson, try to find the answer themselves, then play it again (never \
the words "pause the", which a check forbids: "stop here", "press pause"); it \
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
them (a keyword pair on a question board).
  - THE VOCABULARY PANEL (owner, 2026-10-14; ADR 031). Never over a recording: \
teach the panel's items in the states after the pause-and-try prompt and the \
answer, each as a gloss moment (above): reveal the item and say the word, \
`highlight` it in the transcript as you say it (the box shows its line), its \
meaning, its synonyms (a paraphrase pair: the words the question prints), its \
example (`highlight` the term in the item before you read it). In Listening, a \
medical term in the panel IS explained, simply: the instructor teaches every \
clinical word in English. Where it helps, tell the learner once that the \
small button plays the sentence again. VARY THE WORDING as for the prompts: no \
teaching sentence twice in the lesson, no near copy, no frame repeated with \
other words in it ("Here is a useful verb: ..." twice fails); a check fails the \
lesson on any.\
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


# ---- the vocabulary panel (owner, 2026-10-14; ADR 031) ----

PANEL_LABEL = re.compile(r"^PANEL\s+Row\s+(\d+)$", re.I)
PANEL_KINDS = ("medical", "verb", "phrase", "idiom", "word", "paraphrase")
PANEL_MAX = 2                 # panel items one thought teaches; the panel shows fewer where they do not fit
PANEL_MEANING_WORDS = 10      # the prompt asks for at most 8
PANEL_EXAMPLE_WORDS = 16      # the prompt asks for at most 14
PANEL_SHINGLE = 4             # an example sharing this many words in a row with a transcript is copied
SENTENCE_END = re.compile(r"[.?!][\"'”’)\]]*$")


def _norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def _same_word(a: str, b: str) -> bool:
    """A word of a term and a word said: the same, or one an inflection of the
    other (a common start of all but the last three letters, four at least)."""
    if a == b:
        return True
    n = min(len(a), len(b))
    p = next((i for i in range(n) if a[i] != b[i]), n)
    return n >= 4 and p >= max(4, n - 3)


def _find(words: list[str], phrase: str, lo: int = 0, hi: int | None = None) -> tuple[int, int] | None:
    q = [_norm(x) for x in phrase.split() if _norm(x)]
    a = [_norm(x) for x in words]
    hi = len(a) if hi is None else hi
    for i in range(lo, hi - len(q) + 1):
        if q and all(_same_word(x, a[i + j]) for j, x in enumerate(q)):
            return i, i + len(q) - 1
    return None


def _sentence(words: list[str], counts: list[int], k: int) -> tuple[int, int]:
    """The sentence word k is said in: from the word after the last sentence end
    (or its row's start) to the next sentence end (or its row's end)."""
    starts, n = [], 0
    for c in counts:
        starts.append(n)
        n += c
    row = max(r for r, s in enumerate(starts) if s <= k)
    a, z = starts[row], starts[row] + counts[row] - 1
    i = k
    while i > a and not SENTENCE_END.search(words[i - 1]):
        i -= 1
    j = k
    while j < z and not SENTENCE_END.search(words[j]):
        j += 1
    return i, j


def answers_of(ps: dict, st: dict) -> list[tuple[str, str]]:
    """The extract's answers, as (kind, text): each question's evidence (a quote
    of the transcript) and its key option, each gap's accepted forms."""
    out = []
    for it in practice_set.items(ps).values():
        if st["stimulus_id"] not in (it.get("stimulus_ids") or []):
            continue
        if it.get("evidence"):
            out.append(("evidence", it["evidence"]))
        if it["type"] == "choice" and it.get("scoring"):
            out.append(("key", practice_set.answer_key(it)["answer"]))
        for g in practice_set.gaps_of(it):
            out += [("gap", a) for a in g["scoring"]["accepted"]]
            if g.get("evidence"):
                out.append(("evidence", g["evidence"]))
    return out


def question_texts(ps: dict, st: dict) -> list[tuple[str, str]]:
    """Where a paraphrase pair's printed side may be: ("question", a stem or an
    option), then ("notes", a note form's line) of the extract's items."""
    qs, notes = [], []
    for it in practice_set.items(ps).values():
        if st["stimulus_id"] not in (it.get("stimulus_ids") or []):
            continue
        if it.get("stem"):
            qs.append(("question", it["stem"]))
        qs += [("question", o["text"]) for o in it.get("options") or []]
        notes += [("notes", g["prompt"]) for g in practice_set.gaps_of(it)]
        notes += [("notes", g["heading"]) for g in practice_set.gaps_of(it) if g.get("heading")]
    return qs + notes


def panel_item(ps: dict, st: dict, b: dict) -> list[str]:
    """A vocabulary-panel item (ADR 031): a gloss labelled "PANEL Row N" on a
    Listening board, the words said in row N of the board's transcript. Sets
    its `panel` ({kind, row, word, to, pair, after_answer}: the words' indices
    in the transcript, as the player counts them), its `heard` (the sentence it
    is said in, as two times in the extract's own file, from the word times)
    and its synonym line; returns what is wrong with it."""
    import word_times
    bad = []
    m = PANEL_LABEL.match((b.get("label") or "").strip())
    words, counts = word_times.words_of(st)
    row = int(m.group(1)) - 1 if m else -1
    if not 0 <= row < len(counts):
        return [f"label {b.get('label')!r}: the transcript has rows 1-{len(counts)}"]
    kind = (b.get("kind") or "").strip().lower()
    if kind not in PANEL_KINDS:
        bad.append(f"kind {b.get('kind')!r}: one of {', '.join(PANEL_KINDS)}")
    first = sum(counts[:row])
    at = _find(words, b.get("term") or "", first, first + counts[row])
    if not at:
        other = _find(words, b.get("term") or "")
        where = (f"; it is said in row {next(r for r in range(len(counts)) if sum(counts[:r + 1]) > other[0]) + 1}"
                 if other else "; it is not in the transcript")
        return bad + [f"{b.get('term')!r} is not said in row {row + 1}{where}: a panel word is the speaker's own"]
    syns = [x.strip() for x in re.split(r"[;,]", b.get("synonym") or "") if x.strip()]
    if not 1 <= len(syns) <= 2:
        bad.append(f"synonym {b.get('synonym')!r}: one or two, separated by a comma")
    if len((b.get("explanation") or "").split()) > PANEL_MEANING_WORDS:
        bad.append(f"meaning of {len(b['explanation'].split())} words; at most 8")
    ex = [_norm(x) for x in (b.get("text") or "").split() if _norm(x)]
    if not ex or len(ex) > PANEL_EXAMPLE_WORDS:
        bad.append(f"example of {len(ex)} words; one short sentence of at most 14")
    said = [_norm(x) for x in words if _norm(x)]
    grams = {tuple(said[i:i + PANEL_SHINGLE]) for i in range(len(said) - PANEL_SHINGLE + 1)}
    for _, t in question_texts(ps, st):
        q = [_norm(x) for x in t.split() if _norm(x)]
        grams |= {tuple(q[i:i + PANEL_SHINGLE]) for i in range(len(q) - PANEL_SHINGLE + 1)}
    # the example uses the term: a run of words wholly inside it is not a copy
    own = _find(ex, b.get("term") or "")
    inside = lambda i: bool(own) and own[0] <= i and i + PANEL_SHINGLE - 1 <= own[1]
    if any(tuple(ex[i:i + PANEL_SHINGLE]) in grams and not inside(i) for i in range(len(ex) - PANEL_SHINGLE + 1)):
        bad.append("the example copies words of the recording or a question: write a sentence of your own")
    pair = (b.get("left") or "").strip() or None
    pair_in = None
    if kind == "paraphrase":
        pair_in = next((w for w, t in question_texts(ps, st) if pair and _find(t.split(), pair)), None)
        if not pair_in:
            bad.append(f"paraphrase of {pair!r}: `left` is the words of a question, an option or the "
                       "notes, as printed")
    elif pair:
        bad.append("`left` is only for a paraphrase pair")
    # an answer, or a pair that leads to one, is shown only once its answer is
    # taught (ADR 031): never during a recording before it
    after = kind == "paraphrase"
    term = [_norm(x) for x in words[at[0]:at[1] + 1]]
    for k, t in answers_of(ps, st):
        if k == "evidence":
            ev = word_times.find_quote(words, t, practice_set.speakers_of(st))
            after |= bool(ev and ev[0] <= at[1] and at[0] <= ev[1])
        else:
            # the answer inside the term, or the term inside the answer
            a = [_norm(x) for x in t.split() if _norm(x)]
            short, long_ = (a, term) if len(a) <= len(term) else (term, a)
            after |= bool(short) and any(long_[i:i + len(short)] == short
                                         for i in range(len(long_) - len(short) + 1))
    w = word_times.for_stimulus(st)
    if w:
        s0, s1 = _sentence(words, counts, at[0])
        seg = practice_set.segment(st, "extract")
        b["heard"] = {"file": Path(practice_set.extract_audio(st)["path"]).name, "stimulus": st["stimulus_id"],
                      "start": round(max(seg["start_s"], w["times"][s0][0] - word_times.ROW_PAD_S), 3),
                      "end": round(min(seg["end_s"], w["times"][s1][1] + 0.1), 3)}
    b["panel"] = {"kind": kind, "row": row, "word": at[0], "to": at[1], "pair": pair, "after_answer": after}
    b["icon"] = None                   # a panel item has no picture: the panel has no room for one
    if pair_in:
        b["synonym"] = f"{pair} (in the {pair_in})" + (f"; similar: {', '.join(syns)}" if syns else "")
    else:
        b["synonym"] = ", ".join(syns)
    return bad


def vocab_explanations(boards: list[dict], blocks: dict) -> list[tuple[str, str, set]]:
    """A narration's vocabulary explanations (ADR 031), (utterance id, words
    said, the item's own words): each utterance that reveals a panel item or a
    part of one."""
    out = []
    for bd in boards:
        for s in bd["states"]:
            for u in s["utterances"]:
                ids = {(c.get("block") or "").split(".")[0] for c in u.get("cues") or [] if c.get("type") == "reveal"}
                own = set()
                for i in ids:
                    b = blocks.get(i) or {}
                    if b.get("panel"):
                        for k in ("term", "explanation", "synonym", "text"):
                            own |= set(re.findall(r"[a-z0-9']+", (b.get(k) or "").lower()))
                if own:
                    from write_narration import spoken
                    out.append((u["id"], spoken(u["text_with_cues"]), own))
    return out


def _frame(words: list[str], own: set) -> list[str]:
    """A sentence with the item's own words taken out: its frame ("_" for each run)."""
    out = []
    for w in words:
        x = "_" if w in own else w
        if not (x == "_" and out and out[-1] == "_"):
            out.append(x)
    return out


def vocab_findings(mine: list[tuple[str, str, set]], others: list[tuple[str, str, set]] = ()) \
        -> list[tuple[str, str]]:
    """(utterance id, what) for each vocabulary explanation of `mine` with a
    sentence that another's repeats or nearly repeats (ADR 031): the same rule as
    the pause-and-try prompts, on the sentences and on their frames (the item's
    own words taken out, four words of frame or more), so "Here is a useful
    verb: X." twice fails whatever X is."""
    out = []
    for i, (uid, text, own) in enumerate(mine):
        for vid, other, own2 in list(mine[:i]) + list(others):
            hit = None
            for a in _sentences(text):
                for b in _sentences(other):
                    fa, fb = _frame(a, own), _frame(b, own2)
                    if (len(a) >= 3 and near_copy(a, b)) or (
                            sum(x != "_" for x in fa) >= 4 and sum(x != "_" for x in fb) >= 4 and near_copy(fa, fb)):
                        hit = (a, b)
                        break
                if hit:
                    break
            if hit:
                out.append((uid, f"vocabulary explanation repeats the pattern of {vid}: {' '.join(hit[0])!r} / "
                                 f"{' '.join(hit[1])!r}: word each one fresh (ADR 031)"))
                break
    return out


def lesson_vocab(lesson: Path, skip: str | None = None) -> list[tuple[str, str, set]]:
    """Every narrated section's vocabulary explanations, but the section `skip`."""
    out = []
    for f in sorted((Path(lesson) / "analysis" / "narration").glob("*/narration.json")):
        if f.parent.name == skip:
            continue
        sp = Path(lesson) / "analysis" / "screens" / f.parent.name / "screens.json"
        if not sp.exists():
            continue
        scr = json.loads(sp.read_text(encoding="utf-8"))
        blocks = {b["id"]: b for t in scr.get("topics") or [] for h in t["thoughts"] for b in h["blocks"]}
        d = json.loads(f.read_text(encoding="utf-8"))
        out += [(f"{f.parent.name}:{uid}", t, own) for uid, t, own in vocab_explanations(d.get("boards") or [], blocks)]
    return out


def main() -> None:
    lesson = Path(sys.argv[1])
    if "--prompts" in sys.argv:
        found = prompt_findings(lesson_prompts(lesson))
        for uid, what in found:
            print(f"FAIL {uid}: {what}")
        vfound = vocab_findings(lesson_vocab(lesson))
        for uid, what in vfound:
            print(f"FAIL {uid}: {what}")
        n = len(lesson_prompts(lesson))
        print(f"{n} pause-and-try prompt(s); {len(found)} repeated or near copies; "
              f"{len(lesson_vocab(lesson))} vocabulary explanation(s); {len(vfound)} repeated or near copies")
        sys.exit(1 if found or vfound else 0)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
