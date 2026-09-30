"""The vocabulary-lesson rule (docs/adr/019-vocabulary-lessons.md; maintainer,
2026-09-29): what the screens, narration and QA prompts add for a lesson whose
type is vocabulary. A lesson's type is the first word of its id, as in the
course index (docs/05-COURSE-INDEX.md, `type`).

Nothing here changes a schema or the bundle: every addition is made of the
existing block types (gloss, answer_row, term_box, comparison, plain), each
`authored` with a note naming this rule.
"""

from pathlib import Path


def is_vocabulary(lesson: Path) -> bool:
    return Path(lesson).name.split("-")[0].lower() == "vocabulary"


NOTE = "vocabulary rule (ADR 019)"

SCREENS = """\
VOCABULARY LESSON (docs/adr/019-vocabulary-lessons.md; maintainer, 2026-09-29). \
This is a vocabulary lesson. Its KEY WORDS are the words and collocations this \
section teaches (the words on its slide and in its beats that the student is \
meant to learn and use), plus the everyday adjectives, nouns and verbs a learner \
needs to build sentences with them in OET Writing and Speaking. The rules below \
ADD to the rest of these instructions; where they allow you to add teaching, \
that is this rule's permission, and everything else still holds (no clinical \
facts, exam facts or grammar rules the source does not state; NEVER JUDGE \
REGISTER unless the slide or a ruling says so; A2-B1 wording). Every block you \
add under this rule is `authored`, role example or note, with the note \
"vocabulary rule (ADR 019): ...". \
  - A FULL GLOSS MOMENT FOR EVERY KEY WORD, the first time it is taught in this \
section: a block of type gloss, alone in its own thought: `term` the word or \
collocation, `explanation` its simple meaning in at most about five plain words, \
`text` an example from a MEDICAL LETTER (Writing: third person, a referral or \
discharge letter's style, "Mr Jones reported a dull pain in his lower back."), \
`icon` an image brief when the word is concrete and a picture helps (a bruised \
arm, a drip), else null. A key word that is specialist medical terminology \
(haematemesis, melaena) is not given a dictionary meaning: its `explanation` is \
the plain words a patient would understand ("vomiting blood"), because that is \
what the student needs when speaking to a patient. \
  - A SECOND EXAMPLE, FROM SPEAKING, right after each key word's gloss, in the \
next thought: an answer_row with the key word in a sentence said TO A PATIENT \
(second person, friendly, simple: "Do you have a dull pain, or is it sharp?"). \
A third example (Writing or Speaking) only where the word has a second common \
use worth showing. Every example uses the key word itself, correctly. \
  - WIDEN THE VOCABULARY, one short note each, in its own thought after the \
examples, only where it helps this word and the section has room: its WORD \
FAMILY as a term_box labelled "Word family" ("inflame (verb), inflamed \
(adjective), inflammation (noun)"); its COMMON COLLOCATIONS as a term_box \
labelled "Collocations" (three or four, "severe pain, sharp pain, relieve \
pain"); a NEAR-SYNONYM with the difference in use as a comparison, each side a \
short phrase that reads on its own ("Dull pain: a mild, aching pain" | "Sharp \
pain: sudden and strong, like a knife"). Only facts about English words that \
are certainly true; never a register claim; never a clinical fact. \
  - MORE EXAMPLES IN EVERY SECTION: wherever the section teaches a word, a form \
or a pattern with only the slide's own examples, add at least one answer_row of \
your own, from a medical letter or from talking to a patient. \
  - WORDS, NOT GRAMMAR (maintainer, 2026-09-30, after QA found rules stated \
too broadly: "a verb goes with one noun only", "passive means we do not say \
who"): this rule lets you add facts about WORDS only - their forms, \
collocations, differences in use, examples. It never lets you add a grammar \
explanation (the passive, articles, countable nouns, prepositions, verb forms, \
'to' + verb). Where the source explains grammar, carry only what it says, \
narrowly and truly: "often", "here", "in this sentence", never "always", \
"only", "never" unless it is always true. \
  - ONE KEY WORD, ONE SHORT LIST (maintainer, 2026-09-30): where a slide gives \
one word and a list of words that go with it (a verb and its nouns), the one \
word is the key word and gets the full moment; the list is ONE term_box \
labelled with its word class ("Nouns"), each item with a few plain words, and \
no gloss block, image or example row of its own. A word from the list gets a \
gloss only if it is hard for an A2-B1 learner, and then a plain gloss. \
  - ONE BOARD PER SLIDE STILL HOLDS: every block you add under this rule is a \
WORKING note (`anchor: false`), in its own thought, erased as the board fills; \
it never makes a new topic. The fixed layer stays the slide's own content, kept \
small (a slide's list of words or example sentences is the fixed layer; a \
matching list of words and definitions is ONE table: see TABLE BOARDS). A \
gloss's example sentence must contain the glossed words exactly as written in \
`term`. Every block's text starts with a capital letter. \
  - Do not overload one board: one key word's moment (gloss, second example, \
at most two widening notes) is one run of thoughts, erased before the next key \
word begins. When a section has many key words (more than about eight), give \
the full moment to the ones the section actually teaches and a gloss alone to \
the rest; never drop a slide's own teaching to make room."""

NARRATION = """\
VOCABULARY LESSON (docs/adr/019-vocabulary-lessons.md; maintainer, 2026-09-29). \
The boards give every key word a full gloss moment and more: \
  - Each key word's GLOSS is said exactly as the GLOSS rule says (the word, a \
pause, the meaning, the picture with nothing said about it, the Writing example \
read, a pause). A key word that is a medical term is not explained as a \
dictionary word: say that its meaning part is how you would say it to a \
patient ("To a patient, you can say 'vomiting blood'."). \
  - The SPEAKING EXAMPLE that follows (an answer row said to a patient) is read \
aloud and marked, with a short lead-in that says it is what you might say to a \
patient; then a short pause. \
  - A WORD FAMILY or COLLOCATIONS note is read and marked item by item; a \
NEAR-SYNONYM comparison is read side by side, and the difference in use said in \
one short sentence. \
  - Every added example is read aloud when it appears. \
  - WORDS, NOT GRAMMAR (maintainer, 2026-09-30): never add a grammar \
explanation the boards do not show (the passive, articles, countable nouns, \
prepositions, verb forms). Say a rule only as narrowly as it is true: "here", \
"in this sentence", "often"; never "always", "only" or "never" unless it is \
always true. \
  - Keep the pace: one idea per sentence, A2-B1 words, no stacked explanations. \
Never say how formal, common or natural a word is unless the board or a ruling \
says so."""

def intro_first(text: str) -> str:
    """The first-lesson introduction (ADR 014 amendment) was written for the
    grammar course. For the first lesson of the vocabulary course it says why
    vocabulary matters instead, with no claim about how OET assesses it (the
    maintainer's ruling covers grammar only)."""
    old = ("  2. Explains simply why grammar matters in the OET letter: the reader is \n"
           "another health professional who needs clear, exact information, and grammar \n"
           "is part of how the letter is assessed. No grade or score promises.")
    old = old.replace(" \n", " ")
    new = ("  2. Explains simply why vocabulary matters for OET: the right words make a "
           "letter clear and exact for the health professional who reads it, and help "
           "the learner talk clearly with patients. No claim about how OET marks it, no "
           "grade or score promises.")
    if old not in text:
        raise SystemExit("vocabulary_rule.intro_first: the first-lesson prompt changed; update it")
    return text.replace(old, new).replace("why grammar matters", "why vocabulary matters")


QA = """\
THIS IS A VOCABULARY LESSON (docs/adr/019-vocabulary-lessons.md). Its key words \
are taught with a full gloss moment, a Writing example, a Speaking example \
(said to a patient), and notes on word family, collocations and near-synonyms, \
all marked authored. A gloss on a key word that is a medical term, whose \
meaning part is the patient-friendly wording, is required here, not a finding. \
DO check that every added example uses the key word correctly and naturally, \
that each word family, collocation and near-synonym difference is true English, \
and that nothing claims a register the source did not state: report a wrong \
one as `major`, a false one as `critical`."""
