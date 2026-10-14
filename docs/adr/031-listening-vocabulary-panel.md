# 031 — The Listening board, revised: no split words, a smaller transcript, a vocabulary panel, the whole note form in the reading time (bundle 1.20)

Date: 2026-10-14
Status: **Accepted** (the decisions) by the owner in chat, 2026-10-14, after reviewing
the PR #13 previews, in the brief "Revise the Listening layout per the owner's
review". It **amends [ADR 030](030-listening-board-layout.md)**: where the two
differ, this one holds. How each decision is carried ("How it is carried") was
chosen by the agent under that brief; the owner may reverse it. Some points wait for
the owner's word ("For the owner").

## Context

The owner reviewed the three ADR 030 previews (Part A extract 1, Part B's longest
extract, Part C extract 1). Hyphenation broke words across lines, the transcript's
type was a little large, the space under the transcript box was empty, and the Part A
note form was only ever seen through a moving window. The owner's own teaching, in
the source sessions, explains every difficult word, verb, phrase and expression
while the class listens (ANALYSIS.md §3: the meaning in English, a synonym, an
example; "a good expression, note it down"; he says "synonym" for a paraphrase).

## Options considered

- Keep hyphenation (ADR 030), or set the transcript left: rejected by the owner. Kept
  justified, with no hyphenation, and the gaps reduced by the type and the column.
- The vocabulary panel only as notes beside the questions: rejected: the question
  column is the question's or the note form's.
- The whole note form as a board of its own before the Listening board, playing the
  reading time as a separate recording: possible, but it cuts the release's
  recording in two and asks the screens stage for an extra board per extract. Chosen
  instead: a view of the Listening board itself while its recording is in the
  reading time (below). From the learner's side it is a board of its own.

## Decision (owner, 2026-10-14)

1. **No split words.** The transcript is never hyphenated: no word is broken across
   two lines. It stays justified, the last line of each paragraph set left. The
   gaps are reduced by a slightly smaller type and a wider column (58% to 62%).
2. **Type.** The transcript is a little smaller than 3.4% of the frame's height: 3.1%,
   never under the 2.6% floor. The box keeps ten lines.
3. **A vocabulary panel** in the space under the transcript's box. As the owner
   teaches during listening, the lessons teach every difficult word, verb, phrase and
   expression of a recording, each with a short plain-English meaning, one or two
   synonyms, one short ORIGINAL example sentence (never a transcript's) and the
   "hear it in the recording" button that plays the sentence it is said in. Items
   come from the transcript: medical terms; everyday verbs and phrasal verbs; idioms
   and spoken expressions; and above all the paraphrase pairs, a word of a question,
   an option or the notes that the speaker says differently. The narration never
   talks over a recording: it teaches the items after the pause-and-try prompt and
   the answer; while a recording plays the panel quietly shows items as the marker
   passes them. Teaching sentences never repeat within a lesson, nor nearly (the
   prompts' rule), and the narration audit checks them. A panel word that is also an
   answer follows AGENTS.md §4 (the leak check stays clean). The panel passes every
   fit check; where items do not fit, fewer are shown, never smaller than the floor.
4. **The Part A note form, whole.** In the 30 seconds before each Part A extract, the
   whole note form, full width, no picture. During the extract, the moving window of
   heading groups (ADR 030) stays.
5. **Section boundaries**: the six reviewed boundaries stay as they are (ADR 030,
   "For the owner" 4, answered).

## How it is carried

### The transcript (bundle 1.20)

`build_lesson_player.py`: `LISTEN_SPLIT` 62, `LISTEN_FONT` 3.1, `LISTEN_HYPHENS` False;
the box keeps 10 lines. Measured by `check_lens.py` on the previews (no hyphenation,
widest gap between two words of a justified line, as a multiple of a normal space,
590 / 812 / 1120 px): Part A 2.68 / 2.73 / 2.78; Part B 2.76 / 2.82 / 2.86; Part C 2.97 /
3.26 / 3.31 (ADR 030, at 58% and 3.4% unhyphenated: up to 3.8).

### The panel (bundle 1.20)

- **A panel item** is a gloss written by the screens stage as `{"type": "gloss",
  "label": "PANEL Row N", "kind", "term", "explanation", "synonym", "text", "left"}`
  (listening_rule.py's SCREENS_SET): `kind` one of medical, verb, phrase, idiom,
  word, paraphrase; `left` a pair's printed side, exactly as the question, an option
  or the notes print it. Code (`listening_rule.panel_item`, from write_screens.py's
  practice-set step) finds the term in transcript row N (word by word; an
  inflection matches), and sets its `panel` `{kind, row, word, to, pair,
  after_answer}`, its `heard` (the sentence it is said in, from the word times,
  padded as a row is) and its synonym line (a pair: "<left> (in the question)" or
  "(in the notes)", then its synonyms). No picture. The screens audit fails an item
  whose term is not said in row N, a meaning over 10 words, an example over 16
  words or sharing four words in a row with a transcript or a question (the term's
  own words excepted), not one or two synonyms, a pair whose `left` is not printed,
  or a thought teaching more than 2 items (`PANEL_MAX`).
- **Answers.** An item is `after_answer` when it is a paraphrase pair, when its words
  lie in a question's released evidence, or when it holds a key or a gap's accepted
  form (or lies inside one). The player shows it during a recording only once the
  state that teaches it has begun; `check_lens.py` fails one shown earlier. The
  panel's words live in the lesson folders, never in the repository; the release
  answers check (CI and local) is unchanged.
- **The player** draws the panel under the transcript's box, in its column, its type
  fixed at 2.8% (`listen.panel.font`). While a recording of the board's extract
  plays, it shows the items whose word the marker has passed (the newest last);
  otherwise the items the current state teaches. Only whole items are drawn, at most
  `listen.panel.max`; an item that does not fit is not drawn (the oldest first); in a
  state the fit clears the older item before the next appears. While an item is
  taught, the transcript's box shows the line it is said in, so its highlight is
  seen. The guard never sets a panel item smaller.
- **The narration** (listening_rule.py's NARRATION) teaches each item as a gloss moment
  (ADR 013) after the prompt and the answer, highlighting the term in the transcript,
  and, in Listening, explains a medical term (the owner teaches every clinical word
  in English). `vocab_findings` fails a teaching sentence that repeats or nearly
  repeats another of the lesson, or whose frame (the item's own words taken out, four
  words or more left) repeats another's: in the narration audit and in
  `listening_rule.py <L> --prompts`.
- A word of the word bank's list (Parts B and C, ADR 026 §2) keeps its bank gloss and
  is never a panel item, so no word has two meanings in a lesson.

### The whole note form in the reading time

A Part A Listening board's `listen.reading` (`{font: 3.0}`): while a recording of the
board's extract plays and none of its words has been said yet (the announcement, the
reading time and the tone of the "exam" span), the board shows the note form alone,
the width of the board, every row, at 3.0% of the frame or smaller to the floor where
it would not fit (measured: 2.8% at 812 and 1120 px, 2.6% at 590); the transcript,
the panel and the notes are hidden. From the first word on, the ADR 030 layout and
the form's moving window. `check_lens.py` fails a reading-time moment where the form
is not whole, not full width, under the floor, or shown with another block.

### The fit

`fit_boards.py` never sets a Listening board's transcript or note form smaller (it
had set the Part C transcript's header to 1.9% when a question column did not fit).

### The review preview

`listening_prototype.py <out_dir> --checks` now reads each board's steps, its panel
items and the lines that teach them from `<out_dir>/preview-content.json` (outside
git: it holds the release's words), plays Part A and Part B with their reading time
("exam"), and adds Part C question 32 as a second board. Its checks add the narration
variety check.

## For the owner

1. **Panel items per board.** At 2.8% the panel holds one item at 590 px, one or two at
   812 px (by the items' length) and two at 1120 px, measured on the previews. Fewer
   items are shown where fewer fit, never smaller. Is one item at a time on a small
   phone acceptable, or should the panel also use the empty space under a Part B or C
   question?
2. **The reading-time view** is a view of the Listening board (one recording, as
   released), not a separate board. Confirm.
3. **Word-bank words** keep their bank gloss and never appear in the panel (one
   meaning per word). Confirm, or let the panel repeat them.
4. **Provenance.** A panel item's meaning, synonyms and example are written by the
   model (`authored`), in the owner's way of teaching; the narration explains medical
   terms in Listening lessons, which other lessons never do. Confirm.

## Consequences

- Bundle 1.20 for a Listening lesson (docs/04-LESSON-BUNDLE.md, rules 49 to 51): a
  board's `listen.panel` and `listen.reading`, a gloss's `panel` and `synonym`. Every
  other lesson keeps its format: the 16 built lessons render identical before and
  after (render_compare, 812 and 1120 px), their data files byte-identical.
- docs/02-DESIGN-SYSTEM.md §7i and docs/03-RUNBOOK.md describe the panel and the
  reading-time view.
- To reverse: hyphens and the type are constants in build_lesson_player.py; drop
  `listen.panel` and `listen.reading` (and the screens rule) and record a new ADR.
