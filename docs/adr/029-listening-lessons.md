# 029 — Listening lessons: the pinned sets, the recordings in the lesson, transcripts and note forms (bundle 1.18)

Date: 2026-10-13
Status: **Accepted** (the decisions) by the owner in chat, 2026-10-13, in the brief
for the Listening engine session ("OWNER DECISIONS (2026-10-13) — record all of them
in a new Listening ADR"). How each is carried ("How it is carried" below) was chosen
by the agent under that brief, from the analysis of 2026-10-13
(`C:\OET\lessons\_listening-analysis\ANALYSIS.md`, outside the repository); the
owner may reverse it. Three points are the agent's and wait for the owner's word
(below, "For the owner").

## Context

The Listening course has four lessons from four recorded sessions:
listening-01-overview, -02-part-a, -03-part-b and -04-part-c. In the sessions the
instructor taught on third-party material only (official OET samples and others),
and played that audio in class. ADR 026 governs Reading only; nothing in the engine
could play a recording inside a lesson, show a transcript, fill a note form or read
a Listening set (the practice-set script crashed on one). Features were switched on
by a lesson id beginning `reading`.

## Decision (owner, 2026-10-13)

1. **Practice material.** The exercises release `sample-tests-v2` is pinned for
   Listening: sets `oa-set-la-0001`, `oa-set-lb-0001`, `oa-set-lc-0001` (sample test
   1). All practice audio played in the original sessions is third-party and
   excluded; the forbidden-terms lists are built from the exam-audio spans of the
   transcripts.
2. **The recordings in the lesson.** Exam audio plays inside the lesson's timeline,
   with a visible "recording" state on the board and a short spoken cue before each
   clip. Each extract plays once in full with the real exam reading time before it;
   in Parts B and C the relevant section is replayed for each question; vocabulary
   gets a tap-to-replay "hear it in the recording" button. The engine never changes
   release audio (no loudness change).
3. **Transcripts** stay covered until the question they answer has been solved, then
   are revealed in parts (split by heading or question section), highlighted in sync
   with the audio. Nothing scrolls.
4. **Question numbers keep the exam's numbers** (Part A 1-24, Part B 25-30, Part C
   31-42), because the release audio announces them. An explicit exception, for
   Listening only, to the rule that a lesson numbers its questions from 1 in the
   order taught (ADR 026 amendment of 2026-10-08).
5. **Part A: no learner typing.** The note form is a table board; after "try it
   first" the lesson fills each gap.
6. **Part A vocabulary warm-up**: the teacher's warm-up method, on the vocabulary of
   the new practice set, plus a short prediction drill on the Part A stems.
7. **Part C is two lessons**: C(1) = the method and the presentation (questions
   37-42); C(2) = a short method review and the interview (31-36). The interview has
   no source teaching: it is an authored section (ADR 018) that carries the
   teacher's presentation method over, flagged for the owner's approval at the
   silent preview.
8. **Purpose questions** are taught in words on questions 25 and 26; no item is
   invented.
9. **Teacher errors** ("4 options" in Part C, "38 questions", an echocardiogram
   called an ECG, "30 s" of reading time in Part B, the wrong glosses the analysis
   lists) are taught in their correct form, never mentioning the error.
10. **Parts B and C vocabulary** as in Reading (meaning, an image where possible, a
    synonym, the explanation) plus the "hear it in the recording" button. A Gemini
    image budget of about $6 for the Listening course is approved in principle; the
    exact figure is confirmed at each lesson's start.
11. **listening-01-overview is the first lesson of the Listening course**: a welcome,
    why Listening matters, no lesson count, no list of other lessons, no reference to
    the Persian site or series.
12. **Sessions**: this engine session first; then 01 and 02 together to the
    narration gate, then their audio and final gate; then 03; then 04 split in two.

Exam facts come only from a fact sheet the chat verifies on oet.com
(`docs/listening-facts.md`, a draft until then); it is recorded as an amendment of
this ADR once verified.

## How it is carried

### The lesson type (all lessons)

Features are switched on by a lesson's **type**, a field of its config
(`analysis/sections.json`, `lesson.type`; `build_sections.py --type`; written when
the config is first made, from the first word of the id), never by an id prefix
(`spike/scripts/lesson_type.py`). A config made before 2026-10-13 has no type and
takes its id's first word, so every built lesson behaves exactly as before.
`lesson_type.FEATURES` names what each type turns on: Reading the practice set,
keyword pairs, the doc-marks rule, the lens and question-number checks and the
delivery rule; Listening all of these and the recordings (`exam_audio`), the
reading-time pause, the exam's question numbers and the runner's source-terms check.

### The practice set (decision 1)

`practice_set.py` imports a Listening set only from the pinned release (package
`oa-pkg-sample-tests` version 2) and only the three sets above. The release hashes
its content with RFC 8785 canonical JSON since pilot-v1; the engine now checks both
rules (Part A's hashes did not match the old one). It builds:

- a **transcript** as a document (`text_type` `transcript`): one row per released
  line, a speaker's turn (`turn`, its `speaker`) or a further paragraph of a talk
  (`para`); the row is the line exactly as released, the label included;
- a Part A gap-fill item as its **note form** (`text_type` `form`): a heading row per
  heading, a numbered row per gap (its exam number), the gap's first accepted form a
  typed part of the row (bundle 1.6's gap): the lesson types it in (decision 5);
- a question with its three options as Reading Part B's (bundle 1.15), its options
  shown from the start (in the test the options are read in the reading time);
- the extract's **audio**, copied into the lesson (`generated/exam-audio/`) byte for
  byte, its sha256 checked against the release's before and after; a span of it is
  two times in the file (`exam_span`: "exam" from the announcement through the real
  reading time and the tone to the extract's end; "extract"; "lines N-M", the rows'
  turn times). Release audio is never re-encoded, trimmed or levelled.

The row times are the release's `turn_starts_s`, an admin field: an issue in the
exercises repository asks for per-line times for learner use. Part C extract 2 is
one turn of eight paragraphs with one time, so its paragraphs cannot be replayed one
by one, nor followed by the spotlight, until then.

### The recordings in the clock (decision 2; bundle 1.18)

The narration starts a recording with a **`play` cue** (a Listening lesson's reply
schema only): `text` the extract's ID, `with` the span, its marker on the last word
of a short utterance that is the spoken cue ("Now listen to Extract 1."). The
timeline lays the span an utterance gap after that utterance as an utterance of its
own, `kind` "exam", id `<utterance>.x`, `provenance` "release", its `audio_file` the
copied file and `clip_in`/`clip_out` the span; nothing is said over it. The player
shows the recording state while it plays: a "Recording · Extract N" label in the
header and an outline round the board, drawn over nothing. The narration audit fails
a play cue outside a Listening lesson, on an extract not in the set, with a span the
release cannot give, not last in its utterance, in an utterance with a pause, or
after a spoken cue whose last sentence has more than 12 words.

**The reading time** is inside the "exam" span, so no pause is needed for it. Where
a lesson plays an extract from its first word instead, a pause whose `text` begins
"reading time" may last up to 95 s (the longest reading time, Part C's 90.3 s, and a
margin; the audit allows the set's longest plus 1 s), in a Listening lesson only;
every other pause keeps 0.5 to 10 s.

### Transcripts and the spotlight (decision 3)

A transcript board's thoughts are "Covered: ..." first (the board's `veil`, bundle
1.15) until the question is solved, then the transcript whole (Part B) or in parts
(Parts A and C): "Para N-M: ..." shows rows N to M whole (a heading's section, or a
question's), "Map: ..." the whole transcript too small to read (bundle 1.17's
`view`, with any number of neighbouring rows). While a recording of the board's own
transcript plays, the spotlight (`focus`) follows its rows from their times and
returns, when it ends, to where it was; never while the transcript is covered.

### Numbers, forms, the interview, the words (decisions 4 to 10)

- `check_question_numbers.py` does not require a Listening lesson's first question
  to be 1; a spoken number must still be one its board shows (`question_numbers.py`).
  In an authored section of a Listening lesson a question keeps its exam number (the
  interview of Part C (2)).
- The Listening rule module (`spike/scripts/listening_rule.py`), added to the
  screens, narration and QA prompts as `reading_rule.py` is for Reading, carries
  decisions 2 to 11 and each part's method.
- **Words**: `vocab.py` reads a Listening set's transcript locations (by turn and
  paragraph) and gives a heard word `heard` (bundle 1.18): the sentence it is said
  in, as two times in the extract's own file (the word bank's sentence times, padded
  0.15 s before and 0.1 s after); the gloss shows a second button that plays it.
- **"Recording"** is a word a Listening lesson may say and show (it names the set's
  audio); every other lesson still may not (docs/00-PRODUCT.md §6).

### Bundle 1.18 (Listening lessons only; additive)

An utterance's `kind` ("exam") and `exam` (`stimulus`, `label`, `span`, `rows`,
`release`, `sha256`), `provenance` "release" and `text` null; the cue type `play`; a
pause's `reading_time`; a doc's `text_type` `transcript` (parts `turn` with
`speaker`, and `para`) and `form` (its parts `heading` and `num` with `gap`, its
`typed` gaps); a gloss's `heard` (`file`, `start`, `end`). text.json leaves the
recordings out (they are not narration). docs/04-LESSON-BUNDLE.md, rules 42 to 45.
Every other lesson keeps its format, byte for byte.

### Layouts, measured on placeholder data

`spike/scripts/listening_prototype.py` builds a lesson of placeholder data (every
word of the pinned sets replaced by a made-up word of the same length) through the
real free stages, and the checks measure it at 590, 812 and 1120 px, with Verdana:

- **Part A note form** (16 rows): a table board, fitted at the tables' floor and
  zoomed by the camera as any table board (ADR 007); **with no board picture**;
- **Part A transcript by heading** and **Part B** (the longest extract, 164 words):
  two columns, the transcript whole at 3.0% and 3.2% of the frame;
- **Part C** (the longest interview section, about 280 words): too long to be whole
  in its column even at 2.6% (460 px against a 353 px board at 812 px), so a section
  over about 180 words is shown as **two neighbouring parts**, one after the other
  (here at 2.85%);
- every block inside the board, nothing over anything, no word moving, every line of
  a transcript on its page, at every moment.

## For the owner

1. **The Part A note form board carries no board picture** (an exception to ADR
   021): with one it does not fit, even with the picture at its 10% floor and the
   form at the tables' floor. The form is the board's picture.
2. **A long Part C section is shown in two parts**, never smaller than 2.6% and never
   scrolled.
3. **The release's admin turn times** drive the replays and the spotlight until
   per-line times are released for learners (issue in the exercises repository).

## Consequences

- Reading and every other built lesson are unchanged: the 16 built lessons render
  identical before and after (render_compare, 812 and 1120 px), their audio and data
  files hash-identical.
- The answer check (`check_release_answers.py`) now also looks for every Part A gap
  answer (and accepted misspelling) and any run of 8 words of a release's
  transcript in a committed file, never printing either.
- A Listening lesson's bundle carries the release's audio files (about 7 to 13 MB a
  part); the web format for audio is still open (docs/04-LESSON-BUNDLE.md §8).
- To reverse a carrying choice: change `lesson_type.FEATURES` or drop the 1.18 fields
  and record a new ADR. The decisions are the owner's.
