# 030 — The Listening board: one layout, a transcript that follows the recording, word times (bundle 1.19)

Date: 2026-10-13
Status: **Accepted** (the decisions) by the owner in chat, 2026-10-13, in the brief
"Implement the owner's Listening layout decisions in the engine and prepare a review
preview". It **amends [ADR 029](029-listening-lessons.md)**: where the two differ, this
one holds. How each decision is carried ("How it is carried") was chosen by the agent
under that brief; the owner may reverse it. Four points wait for the owner's word
("For the owner").

## Context

ADR 029 showed a Listening transcript covered until its question was solved, then
whole (Part B) or a part at a time (Parts A and C, a long Part C section in two
parts), followed by a row spotlight driven by the release's admin-only turn times; the
Part A note form had a full-width board of its own. The owner reviewed that plan and
replaced it: one board layout for every Listening part, the transcript on screen
whenever a recording plays and following it word by word.

## Options considered

- Keep ADR 029's covered transcript and parts, with turn times: rejected by the owner.
- Per-line times from the exercises repository (issue #34): would serve the rows, not
  the words; still open, no longer needed.
- Word times from speech-to-text, lined up with the release's own words: chosen by the
  owner. The words a student sees stay the release's; only the times are measured.

## Decision (owner, 2026-10-13)

1. **One layout for Parts A, B and C.** Left (about 58%): a transcript box of fixed size
   and fixed type, never below the text floor. Right (about 42%): the questions: Part
   A the note form; Part B the stem and its three options; Part C the current question
   and its three options, always the one the audio is covering. The box shows about 8
   to 10 lines and moves smoothly, line by line, keeping the line being said about the
   third or fourth from its top; never a strip of one or two lines. The transcript is
   justified (the last line of each paragraph set left), hyphenated if the word gaps are
   ugly at 590, 812 and 1120 px. Speakers' labels stay at the start of each turn. These
   boards have no board picture. This replaces the Part C section in two parts and the
   full-width note-form board. Part C follows its sections: the engine knows where
   each starts and ends (the part of the talk covering one question; a new one begins
   where the speaker signposts the next point).
2. **The follow marker.** While a recording plays, a thin line moves under the word
   being said, with a small caret in the left margin at its line. No word is recoloured
   or highlighted. This replaces the line highlight on replay.
3. **Word times** for every recording of sample-tests-v2 (la, lb, lc-0001) by ElevenLabs
   speech-to-text (AGENTS.md §4; the owner is told only above $5), lined up with the
   release's own transcript, stored as word index to start and end, never the words.
   The release's admin turn times are not used anywhere (issue #34 stays open, no
   longer blocking).
4. **The transcript is visible from the first play**: a teaching lesson, not a test.
   No "covered until replay" for Listening.
5. **Pause-and-try prompts**: in Parts B and C after each question, in Part A after each
   heading group of the note form (not after every gap), the narration invites the
   learner to pause the lesson, try to find the answer, then play it again. The wording
   varies: never the same sentence twice in a lesson, no near copy. The rule is in the
   Listening narration prompt, and a check fails a lesson on a repeat or near copy.
6. **The fact sheet** (docs/listening-facts.md, verified by the chat on oet.com): pen or
   pencil for Part A and a 2B pencil for Parts B and C (paper test), verified; the
   targets 20/24, 4/6 and 8/12 only as "the instructor's suggested targets", with
   oet.com's grade B note (at least 30 of 42 marks, varying slightly by test); never
   teach that abbreviations are accepted in Part A, nor that the instructions' time is
   extra reading time (only the official 30 seconds to look at the Part A notes).

## How it is carried

### Word times and sections (`spike/word_times/`, `word_times.py`)

- `word_times.py --transcribe` runs Scribe v2 (word timestamps, English, no
  diarisation, no audio events) on the ten extract files, sha256-checked against the
  release; the raw responses, which hold words, stay in `data/listening-word-times/`
  (gitignored). Cost: 307 credits, about $0.11 (2026-10-13).
- `--align` lines the recognised words up with the transcript's words by string
  matching only (lower case, letters and digits; difflib's matching blocks; a run that
  differs shares its run's time by word length; a word with nothing heard takes its
  neighbours' gap), times inside the extract segment. 98.7% to 100% of each extract's
  words matched one to one.
- `spike/word_times/sample-tests-v2.json`: per extract, the audio's and the
  transcript's sha256 (times are used only where both match), each row's word count,
  and `[start, end]` per word index. A transcript's **words** are its rows in order,
  each row's text with its speaker's label taken off, split on white space (the player
  counts the same way).
- `spike/word_times/sample-tests-v2.sections.json`: per extract, each section's first
  word: Part C a question's, Part A a heading group's, Part B the whole extract. The
  agent chose them from the transcripts (a sub-agent, 2026-10-13), where the speaker
  signposts the next point; `--check` proves every question's (and gap's) evidence
  lies inside its own section.
- `practice_set.row_times` and every span come from the word times: a row starts 0.15 s
  before its first word; the narration's spans gain `"question N"` and `"heading K"`
  (a section, from its first word to the next section's). The screens prompt lists
  each extract's sections by rows.

### The Listening board (bundle 1.19)

- Any board whose fixed layer holds a transcript is a Listening board: its bundle
  board has `listen` (the transcript's block, the extract, `split` 58, `lines` 10,
  `font` 3.4 (% of the frame's height, fixed; body is 3.2, the floor 2.6),
  `hyphens`, each row's word count, each word's times, and the sections, each with
  the question block it shows or the note form's heading row). A section's question
  not on the board is built from the release for it.
- The transcript's block is drawn as its page's header and a window (`lt-win`) over
  its rows (`lt-scr`), with the marker and the caret: in the block's own html, so a
  renderer that rebuilds a block keeps it. The rows sit on one line grid (no space
  between rows, line height a whole number of pixels) and the window moves by whole
  lines, so no line is ever cut. While a recording of the board's extract plays, the
  word being said is found from the times; its line is the fourth of the box (higher
  at the start, lower at the end); the marker is under it. Otherwise the box shows a
  state's row ("Row N:" on a Part B or C board), else where the last recording ended.
- The question column: while a recording plays, the question of the section the word
  is in, in place of the board's own question blocks; otherwise the states' blocks.
  A Part A board's table is its note form (its rows, its typed gaps, its spotlight):
  measured, the form does not fit its column whole at a readable size (551 px against a
  469 px board at 2.6%, 812 px frame), so it is set at 2.8% in a window of whole rows
  (a row partly outside is not drawn), which moves to the heading of the section being
  heard, or to the gap being filled (under its heading where both fit); room is kept
  under it for the board's notes.
- Justified, the measured word gaps were up to 3.8 spaces (a quarter over 2) at all
  three widths: the transcript is hyphenated (CSS, its own lang), which the browser does
  with its English hyphenation data; with the data Edge holds on the owner's machine,
  Part C's widest gap is 2.5 spaces (11% over 2) at 812 px.
- The camera never moves on a Listening board; the guard never sets the transcript or
  the form smaller (their type is fixed); a board picture is never planned for one.
- **The silent preview plays the recordings**: the silent clock follows the
  release's file while a recording plays (held while it loads), so the narration gate
  hears them.
- ADR 029's covered transcript, its parts and map ("Covered:", "Para", "Map" on a
  transcript fail the screens audit), its row spotlight (`exam_focus`) and its
  admin turn times are gone.

### Prompts (decision 5)

`listening_rule.py`'s narration prompt carries when and how to prompt; a prompt is an
utterance ending with a `pause` whose `text` is "try it first". The narration audit
compares every sentence of a section's prompts with each other and with every other
narrated section's; `listening_rule.py <L> --prompts` checks a whole lesson. A
repeat or a near copy (one word swapped, or 80% of the words alike in order, for a
sentence of four words or more) fails.

### The review preview

`listening_prototype.py <folder outside the repository> --checks` builds three lessons
of one board each from the real set (Part A extract 1 and its form; Part B's longest
extract and its question; Part C extract 1 and its questions 31 to 36) through the real
free stages, and runs the overflow, overlap, lens, wide-font, question-number,
structure and audio checks. It replaces ADR 029's placeholder prototype (word times
exist only for the released transcripts). `check_lens.py` now measures a Listening
board at every state and every half second of each recording: no cut line, the box's
type and lines, the marker, the line and the question; it reports the word gaps.

## For the owner

1. **Hyphenation depends on the browser.** Edge and Chrome download English
   hyphenation data into a profile; a browser without it justifies with no hyphens
   (gaps up to 3.8 spaces). Keep justified text, or set the transcript left?
2. **Part A's form is in a window of whole rows**, moving with the recording (above):
   it does not fit whole at a readable size. Is that the note form you want?
3. **The box's size**: 10 lines at 3.4% of the frame, about 60% of the board's
   height; the space under it is empty.
4. **Six section boundaries had a second valid place** (Part C extract 1, questions 32
   and 35; extract 2, questions 39 and 42; Part A extract 1, "Vaccinations"; extract
   2, "Plan"); the agent's choice is in the sections file and can be moved by word index.

## Consequences

- Bundle 1.19 for a Listening lesson (docs/04-LESSON-BUNDLE.md, rules 46 to 48): a
  board's `listen`; a transcript's and a form's html with their window. Every other
  lesson keeps its format: the 16 built lessons render identical before and after
  (render_compare, 812 and 1120 px), their data files byte-identical.
- docs/listening-facts.md is verified; facts 20 to 23 are ruled as above.
- To reverse: drop `listen` from the bundle (the transcript then draws as a page) and
  record a new ADR; the decisions are the owner's.
