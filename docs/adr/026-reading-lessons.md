# 026 — Reading lessons: practice sets, vocabulary and visual design

Date: 2026-10-05
Status: **Accepted** (the rules) by the maintainer in chat, 2026-10-05, in the
brief for Reading lessons 1 and 2: "Write this ADR and add it to the ADR index.
It governs all four Reading lessons." The brief named it ADR 025; that number
was already taken (lower-case lesson ids), so it is 026. How the rules are
carried ("How it is carried" below) was chosen by the agent under that request;
the maintainer may reverse it.

## Context

The Reading course has four lessons: an overview (reading-01-overview) and one
lesson for each part of the test (Parts A, B and C). In the recorded sessions
the instructor taught Parts A to C on official OET sample texts. Those texts
belong to OET and must not reach the product.

The product has its own practice sets, written and checked in the exercises
repository (`siamingit/oetacademy-exercises`, private) and released as
`pilot-v1`. The same sets are the learners' Practice Test 1. The exercises
repository also holds a vocabulary layer for the Part B and Part C sets: a word
bank with meanings, synonyms, examples and pronunciation audio, and the places
where each word occurs.

Nothing in the engine could teach from a text that is not on the deck. No
block could show a realistic document, and no mark could link the words of a
question to the words of a text. A Reading lesson also needs richer visuals
than the source decks, which are mostly lists on coloured cards.

This repository is public and the exercises repository is private. So set
text, question wording and word-bank content never enter this repository.
Only their IDs do.

## Options considered

For the texts:

1. **Keep the official samples.** Rejected by the maintainer: they are OET's
   material.
2. **Write new texts per lesson.** Rejected: they would be unchecked, and they
   would differ from Practice Test 1.
3. **Teach the released sets, unchanged** (this decision).

For how a set reaches the boards:

1. **The screens model copies the texts into its reply.** Every board would
   repeat about 200 words of output, and a verbatim check would have to catch
   every slip.
2. **Code builds the text and question blocks from the release by ID; the
   model names the ID** (this decision). The wording cannot drift, and the
   model writes only the teaching around it.

## Decision

### 1. Practice sets

- The texts and questions of Reading Parts A, B and C come **only** from the
  exercises repository, release `pilot-v1` (local copy:
  `%LOCALAPPDATA%\oetacademy-exercises\releases\pilot-v1`):
  - Part A: `oa-set-ra-0001`;
  - Part B: `oa-set-rb-0001`;
  - Part C: `oa-set-rc-0001`, texts `t1` and `t2`.
- **Shown exactly as released.** No text, question or option is rewritten,
  shortened, reordered or paraphrased. The sets stay unchanged as Practice
  Test 1.
- **Questions are referred to only by their IDs** (`oa-reading-000007`) in all
  lesson data, scripts and reports.
- **The exercises repository is read-only for the engine.** Any need (a
  missing field, an error found, data required) is a GitHub issue in
  `siamingit/oetacademy-exercises`, with a clear title, the IDs involved and
  what is needed.
- **Official OET sample texts never appear in an English lesson**: no text,
  screenshot, paraphrase or book cover. The instructor's teaching carries over
  and is applied to the new sets: his strategies, his explanations and the
  order he teaches in.

### 2. Vocabulary (Parts B and C only)

- Vocabulary is a primary focus of the Part B and Part C lessons. The only
  source is the exercises repository's word bank (`vocab/lexicon.json`, with
  `vocab/occurrences/<set>.json` for where each word occurs; read
  `docs/vocab/README.md` there first). The engine writes no word list and no
  definition of its own.
- Words are referred to by their `lx:` IDs. These are provisional
  (oetacademy-web#51), so the engine keeps them in **one mapping file** (see
  "How it is carried") that is easy to update.
- For every word:
  - it is pre-taught on a board before the text it belongs to;
  - it is glossed again where it appears in the text, a question or an option;
  - it is in a word-recap board at the end of that text.
- **A gloss shows** the meaning, a synonym and the short example, all from the
  word bank, and a background-free image made by this engine with Gemini (ADR
  015's style). An abstract word gets a small illustrative scene, extending ADR
  015's "concrete words only" for this vocabulary layer. Images are the
  engine's own assets, keyed by `lx:` ID.
- **Where the word bank lacks** a meaning, a synonym or an example, the engine
  writes none: it opens an issue in the exercises repository and lists it in
  its report. Checked 2026-10-05: all 112 entries that `oa-set-rb-0001` and
  `oa-set-rc-0001` use have all three, and an audio file.
- **Pronunciation audio.** `docs/vocab/README.md` describes the word-bank
  audio as pronunciation audio (Cartesia `sonic-3.6`, voice Imogen, speed
  1.0, one MP3 per spoken headword), so it is used for that. How it is played
  in a lesson is settled when Part B is built, and reported then.
- **Glossed words are recorded in the course index**, with their `lx:` IDs
  and the lesson and section that teach them.
- **Part A has no vocabulary layer.** No gloss is added to the Part A set's
  texts or questions. The word table the instructor taught in his Part A
  session stays as part of his teaching. The general gloss rule
  (docs/00-PRODUCT.md §3) applies only to the lesson's own teaching boards and
  narration.

### 3. Visual design

- **Richer than the source decks**: diagrams, timelines, realistic document
  mock-ups (memo, email, policy, guideline, table layouts) and annotated
  highlights. Every graphic must help understanding; none is decoration.
- **Paraphrase bridge.** When a question is solved, the wording in the text and
  the wording in the correct answer take one shared colour. Each wrong option
  is ruled out visibly, with a short reason label.
- **Keyword matching.** A question's keywords and the matching words in the
  text are highlighted in the same colour.
- **Board layout by part:**
  - Part C (long texts): one paragraph and its question per board, plus a
    whole-text map board that shows which paragraph is active;
  - Part B: the full extract and its question on one board;
  - Part A: each of the four texts as a realistic document, with the skimming
    and scanning paths shown visually.
- The existing rules still apply: a table whole on one board with the
  spotlight (ADR 007), the board style and word-class colours (ADR 008), one
  relevant picture per board (ADR 021), no references to left or right or to
  the picture (design system §8c, ADR 015), initialisms written "C-O-P-D" in
  the narration (ADR 016).

### 4. Every Reading lesson

- **The first lesson of the Reading course** (reading-01-overview) welcomes the
  learner to the course. It explains why reading matters for healthcare
  professionals (guidelines, policies, notes and emails at work) and for OET.
  It gives no course map, no lesson count and no list of lessons (ADR 014
  amendment, applied to the Reading course). Every other Reading lesson opens
  warmly, links on and does not welcome the learner to the course again.
- **Exam facts supplied by the maintainer** (2026-10-05), taught as the correct
  version without mentioning the source's error:
  - OET has no "B+" grade: the grades are A, B, C+, C, D and E, and the target
    is Grade B, 350;
  - about 30 of 42 correct answers usually corresponds to Grade B, but grade
    boundaries vary slightly between test sessions; 15 of 20 is a guide for
    Part A within that target;
  - Reading lasts 60 minutes. Part A has 15 minutes, timed separately, and
    Parts B and C share 45 minutes;
  - Part A has 4 short texts and 20 questions: matching, sentence completion
    and short answer;
  - Part B has 6 short workplace texts of 100-150 words, with one 3-option
    question each;
  - Part C has 2 long texts of about 800 words, with 16 questions of 4 options;
  - every question carries one mark.
- **Paper-only advice** (a pen, underlining, crossing out instead of erasing)
  is presented as advice for the paper test. No on-screen tool of the computer
  test is claimed unless it is verified on oet.com, and the verification is
  reported.

## How it is carried

Chosen by the agent under the maintainer's request.

- **The set in the lesson.** A script reads the set from the local release
  copy, checks every text's and item's `content_hash` against the release, and
  writes `<lesson>/analysis/practice_set.json`: the release id, the set, its
  texts and items as released, and the hashes. It is never in git. The screens
  stage of a section that teaches the set is given the texts and items by ID.
- **Blocks built by code** (bundle format 1.13, docs/04-LESSON-BUNDLE.md; the
  maintainer approved building it on 2026-10-05, with a before-and-after proof
  on every built lesson):
  - a **document**: the screens model writes a `table` block whose label is a
    stimulus ID and nothing else; code (`practice_set.py`,
    `write_screens.expand_practice`) replaces it with the text as a core table
    of one column carrying `doc`: one row per part (a heading, a paragraph, a
    list item, a row of a table inside the text), each the released line with
    only its list marker taken off, which the stylesheet draws. So every table
    board rule applies to it (ADR 007: the spotlight, zoom, marks in a row), and
    the skimming path is the spotlight walking the parts. It is always the
    fixed layer of a board of its own, drawn as a page with a type tag (Table,
    Guideline, Protocol, Notes; Email, Memo, Policy, Extract for Parts B and C).
  - a **question**: a `plain` block whose label is an item ID; code writes its
    number and its wording as released and the `question` field. It opens its
    board and stays (role slide, pinned).
  - **answers in the exact form**: an answer row the model writes for an item
    is replaced by code with the release's accepted form: a sentence to
    complete shows the released sentence with its gap filled, a short answer
    "Answer: " and the form, a matching item the text's label. A reason a wrong
    option is ruled out comes from the release's own feedback where it has one.
  - Part C's whole-text **map** is built with Part C.
- **Keyword pairs**: three mark types, `match1`, `match2`, `match3`, drawn as a
  highlight in sky blue `#0688F9`, violet `#A860FB` or yellow `#F9E806` at 55%
  over the text, put on a question's (or answer's) words and on the text's words
  that match them. A pair shares one colour, which means only "these words
  correspond". Chosen by measured difference (CIEDE2000) as ADR 008 chose its
  colours: 25.3 or more between any two, 26 or more from red and green and their
  tints; the yellow is 14.9 from the amber highlight, so on a question board the
  narration uses pairs, never the amber highlight. Reading lessons only (the
  narration audit fails them elsewhere).
- **The instructor's method from off-deck teaching**: where the instructor
  teaches on material that is not the deck (Part A: a whole practice set solved
  on a course website, 36:15-80:13), the understanding stage reads it as part
  of the page it belongs to (`sections.json` `page_spans[page].also`,
  `build_sections.py --page-also`; maintainer, 2026-10-05), so the method
  carries over and is applied to the product's own set.
- **Nothing of the excluded material reaches a lesson**: each lesson lists the
  distinctive terms of what it may not use (`analysis/forbidden_source_terms.json`);
  `check_source_terms.py` fails on any of them in what a learner reads or
  hears, and the longer terms are also forbidden phrases in the page ledgers.
- **The word-ID mapping file** lives with the course index, outside the
  repository: `<library>/course/vocab-ids.json`. Every `lx:` ID the engine
  writes is read from it. When oetacademy-web#51 changes the IDs, the file is
  updated and the affected lessons are rebuilt from it with no model call.
- **The lesson type** `reading` (a lesson id beginning `reading`) adds a reading
  rule module to the screens, narration and QA prompts, as
  `vocabulary_rule.py` does for vocabulary lessons (ADR 019). It carries the
  rules above, including no gloss inside the Part A set and never an official
  sample text. The first-lesson introduction rule (ADR 014 amendment) takes its
  reasons from the lesson's type, not always from grammar.

## Consequences

- The Overview lesson needs nothing new. Its timeline, score converter, skills
  map and success path are drawn with existing blocks (timeline, change card,
  table).
- The Part A lesson needs bundle 1.13 and its renderer rules. Lessons built
  before it keep their format, and their screens must re-render
  byte-identical with the new code, checked before the change is used.
- The lessons show every answer of `oa-set-ra-0001`, `oa-set-rb-0001` and
  `oa-set-rc-0001`, which are also Practice Test 1. The release says keys and
  the vocabulary layer's glosses are shown only after the learner submits.
  Whether a learner must submit Practice Test 1 before watching these lessons
  is the website's decision. This ADR records the tension; it does not settle
  it.
- Set content is in lesson folders and bundles only, never in git. Reports and
  logs use IDs.
- To reverse a carrying decision: drop the reading rule module and the 1.13
  blocks and record a new ADR. The rules themselves are the maintainer's.

## Amendment, 2026-10-06: the review of Reading lessons 1 and 2

Added at the maintainer's request in the review of reading-01-overview and
reading-02-part-a ("Add this to ADR 026 as a rule"; "Record this distinction
in ADR 026"). The rules above stand; these are added to them.

- **No mock test first** (maintainer's rule). A Reading lesson never advises
  the learner to take a mock test, or any full practice test, before
  studying, even where the instructor did. Carried by the reading rule module
  (screens, narration and QA prompts); the Overview lesson's advice was taken
  out.
- **Glosses in Parts B and C** (maintainer's distinction). The word bank's
  rule that glosses are shown only after the learner submits applies to the
  exercise player on the website, not to lessons. Lessons pre-teach and gloss
  the words as §2 says. This settles the glosses half of the tension recorded
  under Consequences; whether a learner must submit Practice Test 1 before
  seeing its answers in a lesson is still the website's decision.
- **Part C method** (maintainer's teaching point, for the Overview and the
  Part C lesson). Part C questions follow the order of the text. The learner
  works paragraph by paragraph: reads the question, then the paragraph it
  refers to, then answers. The Part C lesson teaches this method in full;
  "read the whole text first" is not taught.
- **Part A time split** (maintainer's fact). In the order of the set and of the
  test: skim the four texts 3 minutes, matching questions 2, short answers 5,
  sentence completion 5; 15 minutes in all.
- **Skimming is highlighted** (maintainer, Part A: "use yellow highlighting,
  as the instructor does, instead of underlining and circling"). On a skimming
  board the narration marks the skimming path with the `highlight` mark, never
  `underline` or `circle`. Applying it to every Reading lesson's skimming
  boards, through the reading rule module, is the agent's choice under that
  request. The mark is the design system's one highlight, amber `#FAC775`
  (docs/02-DESIGN-SYSTEM.md §8); a truer yellow would be a change to the design
  system for every lesson, and would sit close to the yellow keyword pair
  `match3`.
- **Kept as built** (maintainer agreed): the two exam claims the agent could
  not verify stay out of the lessons (that markers accept other wordings, and
  that underlining on the answer booklet is not allowed), and the Part A
  lesson keeps "many students answer 17 or 18 of the 20 correctly" beside the
  guide of 15 of 20.

## Amendment, 2026-10-06: the Part A question method, and every phrase read is marked

Added at the maintainer's request in the review of reading-02-part-a ("Record
this method in ADR 026 as the Part A question method").

### Every phrase of a text that is read aloud is marked

- **The rule** (maintainer). Every phrase of a practice-set text that the
  narration reads or quotes while the text is on screen has a mark, a
  `highlight` or a keyword pair, timed to the moment it is spoken.
- **Why it was broken.** The narration (effort `high`) read several parts of
  a text in one sentence and marked only the first (three numbered steps of
  a protocol named in one sentence, one mark), and the screens plan gave each
  skimming board two or three stops while the narration read three to six
  parts. No rule required a mark for each part read, and nothing checked it.
  The screens stage's effort (ADR 022, `medium`) did not cause it: four drafts
  of the Skimming section on a copy, two at `high` and two at `medium`, planned
  the same number of stops (one to three per text either way).
- **How it is carried.** The reading rule tells the screens stage to give each
  part that will be read its own row (stop), and the narration to mark every
  phrase it reads from a text, one mark per phrase. The narration audit fails a
  draft that reads a text's words with no mark on them, before any audio is
  made, and `check_doc_marks.py` checks the finished player against the voice's
  own word timings (the runner's player step). A quote is a run of words shared
  with a part of the text holding two content words, or a whole short part (a
  heading); words that are also the question's are the question read aloud.

### The Part A question method

- **The method** (maintainer). Each of the 20 Part A questions is solved in
  five steps, so the learner always searches before the answer is shown:
  1. a **map** shows all four texts at once, too small to read on purpose;
  2. the question appears and the instructor reads it; its keywords are
     marked;
  3. **try it first**: the instructor invites the learner to pause and find
     where the answer is, then a few seconds of silence (4 s);
  4. **eliminating texts**: from the keywords, the instructor says which text
     must hold the answer and rules the others out; the other texts dim and
     the chosen one stays bright;
  5. a **zoom** into that text, then into the exact part (section or table
     row), readable on a phone; the keyword pairs light up in shared colours
     and the answer is found in its exact form.
- **How it is carried** (bundle 1.14, additive; docs/04-LESSON-BUNDLE.md). The
  map is one table block with `map`: the four texts' parts as its rows, in
  order, and where each text starts, so the spotlight, the marks and the
  pairs find a part as on any table. Each state of a map board carries `doc`
  (the text chosen) and `zoom` (null, "doc" or "row"). The player draws the
  four texts as small pages in a two-by-two grid, beside a column for the
  question and its notes, and zooms the map inside its own frame (a lens), so
  the question stays in view: "doc" shows the chosen text alone at a
  document's size, "row" sets that part larger, in the middle of the frame,
  the other parts dimmed. The screens model writes the map as a placeholder
  ({"type": "table", "label": "MAP"}) and thoughts named "Text D:", "Zoom D:"
  and "Row D3:"; code builds the map from the release.
- **Exemptions**, recorded as the maintainer asked: the map is exempt from the
  table text floor (1.9% of the frame, docs/02-DESIGN-SYSTEM.md §7, Tables):
  it is not shrunk to fit, its pages are scaled to their quarter and are not
  meant to be read; and from the layout check's "no word moves" (§8a): the
  lens moves the map's words by design, as the camera does a table's.
- **Parts B and C.** The Part B lesson keeps one text per question board. The
  Part C lesson will consider the same pattern: the whole-text map, then a
  zoom to the paragraph.

## Amendment, 2026-10-06: Reading lesson 2's word table; pens, pencils and highlighters

Added at the maintainer's request in the review of reading-02-part-a.

### Reading lesson 2's word table (an exception for this lesson only)

- **The exception** (maintainer). In reading-02-part-a only, the instructor's
  eight words are replaced by about ten words that the engine selects from the
  texts of `oa-set-ra-0001`: words that are hard, or common and important in
  healthcare reading, medical terms included, preferring words the learner
  needs for the questions. The engine writes their meanings itself, one plain
  English meaning a word, simple and accurate, reviewed by QA. The word bank
  does not cover Part A; no issue is opened in the exercises repository.
- **Taught the instructor's way**, at the same point of the lesson as his
  table: his Word | Meaning table, a spotlight on each row as it is taught,
  and for each word a short example quoted exactly from the set's text where
  the word appears.
- **The rule stays in force**: Part A has no vocabulary layer from the
  exercises repository (§2). This exception is not a vocabulary layer and
  does not apply to any other lesson.
- **How it is carried.** The words, meanings and examples are in the lesson's
  `analysis/word_table_2026-10-06.json` (not in git: the examples are set
  text), and the deck's transcribed table keeps what the deck prints, with
  `replaced` recording the table the board shows; the screens audit holds the
  board to the replacement.

### Pens, pencils and highlighters (verified on oet.com by the maintainer)

- Reading and Listening Part A: a pen or a pencil may be used. The Part A
  lesson keeps the instructor's pen advice.
- Parts B and C: the answer is shaded with a 2B pencil, and on paper only a
  shaded circle counts: no tick, cross or circling. For the Part B and Part C
  lessons.
- Mechanical pens and pencils, highlighters and correction fluid are not
  allowed.
- **No lesson may suggest using a highlighter in the paper test**, in words
  or in a picture. The highlight on a board is only the lesson's display.
  Carried by the reading rule (screens, narration and QA prompts).

## Amendment, 2026-10-06: the Part B question method, the vocabulary layer built, bundle 1.15

Added at the maintainer's request in the brief for Reading lesson 3 ("Part B
question method (new; record it in ADR 026)") and approved with bundle 1.15 at
its source gate (2026-10-06).

### The Part B question method

- **The method** (maintainer). Each Part B question is solved in eight steps,
  so the learner reads the question and the options before the text (QAT:
  Question, Answers, Text), and searches before the answer is shown:
  1. the question appears and is read; its keywords are marked;
  2. the three options are read, with their keywords marked (underlined, as
     the instructor underlines them);
  3. **try it first**: the learner is invited to pause and choose, then a few
     seconds of silence (4 s);
  4. the extract appears: the whole text and the question on one board. Until
     then the text is **covered** (its type tag shown, its room kept), as the
     instructor covers it in yellow while he reads the question and options;
  5. keyword pairs light up in shared colours (`match1` to `match3`);
  6. the paraphrase bridge links the text's wording to the correct option;
  7. each wrong option is ruled out: struck through, with a short reason label
     based on the release's own feedback for that option (at most 12 words in
     the prompt, 14 in the audit; A2-B1; QA checks it against the text);
  8. the answer is confirmed: a tick on the option.
- Every phrase read from a text is marked (the rule of 2026-10-06 and
  `check_doc_marks.py`); nothing is read or marked in a covered text.
- **Boards of a Part B text**, in order: its pre-teaching board, its question
  board, its word-recap board (below).

### The vocabulary layer, as built

- **The mapping file** `<library>/course/vocab-ids.json` exists
  (`vocab.py --sync`): each word has a stable engine key (`w:` and the ID first
  seen), its current `lx:` ID, its earlier IDs and the engine's image brief for
  its gloss picture (`vocab.py --briefs`). Screens store the key; a bundle's
  `lx:` ID is read from the file at build time.
- **Pre-teaching board**: the instructor's word-to-meaning matching table
  (format c), built by code from the word bank (the words in order, their
  meanings moved one place on), taught row by row: an arrow from the word to
  its meaning, then the word's gloss. The instructor's other two formats are
  used where the set's own words fit them (maintainer, 2026-10-06): a
  collocation pair (a) and an attributive-noun chain (b; the qualifier is a
  noun used as a modifier), each a one-row table of the text's own words.
- **Gloss** (bundle 1.15): the word, its meaning, a synonym and the example,
  all from the word bank, the engine's own background-free image, and the word
  bank's pronunciation clip on a button the learner taps (no autoplay, so no
  second voice in the narration; maintainer, 2026-10-06). The clips are copied
  into the lesson (`generated/vocab-audio/`). A word is glossed where it is
  pre-taught and again wherever it occurs in the text, the question or an
  option.
- **Word-recap board**: a table of each word, its meaning and a synonym, built
  by code from the word bank, at the end of each text.
- `vocab.py --check` fails a word with no meaning, synonym, example, audio
  file or image brief; a gap in the word bank is an issue in the exercises
  repository, never filled by the engine (none for oa-set-rb-0001).

### How it is carried (bundle 1.15)

- A question block of a Part B item carries `question.options` (`{option,
  letter, text}`, in the release's display order) and parts (`items`):
  `{kind: "out", option, text}` for each wrong option, then `{kind: "key",
  option}`. The screens model writes them as strings on the question
  placeholder ("out|B|reason", "key|A"); code checks them against the release's
  key. The question is pinned, so its parts may be revealed in later states:
  the bundle puts their times in the board's `reveal`, where they stay.
- A thought named "Covered: ..." on a Part B question board makes a covered
  state (a state's `veil`); covered thoughts come first.
- Gloss blocks and word tables are placeholders the model names by `lx:` ID
  ({"type": "gloss", "label": "lx:..."}, {"type": "table", "label": "MATCH
  lx:... lx:..."} or "RECAP ..."); code builds them.
- New document types `procedure`, `manual`, `notice`, and a page look for each
  of the six genres, drawn by the stylesheet only (no word added).
- Everything is added only to a lesson whose set has a Part B (format 1.15,
  `PART_B_CSS`); Reading 1 and 2 and every other lesson are unchanged, checked
  by rendering all 13 built lessons before and after.

### The Part B lens (maintainer, 2026-10-07)

- **Why.** On a question board the whole text, the question with its three
  options and the glosses share one board, so the fit sets the text at the
  table floor (1.9% of the frame: about 12 px on a laptop, 8.7 px on a phone),
  and the camera cannot zoom a one-column page (a full-width row fits at 1x).
  The maintainer, at the silent-player review: "build the lens, as in Part A's
  map. It zooms onto the paragraph or lines being read, readable on a phone. Do
  not shorten the glosses."
- **The lens.** The text keeps the room it takes unzoomed, as a frame of its
  own. While the text is uncovered and the spotlight has a row, the text is set
  at body size (3.2% of the frame, readable on a phone) inside that frame, the
  row being read is brought to the middle, and the others are dimmed; the
  lens centres on the latest phrase marked in the text, so a paragraph longer
  than the frame shows the words being read. Marks and the pointer are drawn
  only where the frame shows them. The camera does not zoom on such a board.
- **Carried by** a board's `lens` (bundle 1.15, rule 35), set by the builder on
  every Part B question board; the row is the spotlight's (`focus`, rule 11),
  which follows what is read and marked. The player's `applyDocLens`.
- **Exemptions, as for the map** (maintainer: "as in Part A's map"): the lensed
  text's words move by design, so the layout check leaves them out (§8a); the
  frame hides the text beyond it, so the overflow check and the fit do not count
  it as clipped.
