# 007 — Table boards: a table is shown whole and taught row by row

Date: 2026-09-25
Status: **Accepted** by the maintainer in chat, 2026-09-25 (the rule, with a
reference prototype), and the data format it needs: bundle format 1.2
(docs/04-LESSON-BUNDLE.md) and the agent-transcribed table file for image
slides, the same day.

## Context

Grammar 3 (Nominalisation) is taught almost entirely from tables: five
slides, each a table of case notes with empty "Formal expression" and
"Sentence" columns that the teacher fills in live, row by row. The rules
until now did not fit:

- docs/02-DESIGN-SYSTEM.md §7 split a table too large for the frame "by
  meaning", and a table in the screens stage was at most four columns by
  five rows of short cells. Grammar 3's tables have up to seven rows of
  sentences.
- Nothing could type an answer into a cell, focus a row or place a note
  beside it. The earlier rule "rows appear in time with the narration" had
  no data behind it.
- The tables are pasted images with no text layer (methodology §4), so the
  screens stage had no printed text to copy them from.

## Options considered

1. **Split large tables by meaning, as before.** The student loses the
   whole table, which is the point of the slide: the same case-note-to-
   sentence method applied row after row.
2. **Show the table whole and rely on type size alone.** Seven rows of
   sentences do not read on a phone at a size that fits.
3. **Show the table whole, teach it row by row, and zoom when the text is
   too small to read** (this decision). The maintainer supplied a
   reference prototype, `docs/prototypes/table-board-prototype.html`.

For the image slides' text:

1. **Show the slide image to the screens model** (as for diagram slides).
   Nothing would check what it read.
2. **The agent transcribes each table into a lesson file**, checked cell by
   cell against a render, which the audit then holds the screen to (this
   decision).

## Decision

**The rule** (docs/02-DESIGN-SYSTEM.md §7, "Tables"; for every lesson):

- A table is core content, shown whole on one board, never split by row.
- Row focus is a spotlight: the active row at full strength, the others
  dimmed; the cell being discussed gets the glass highlight (notes, then
  formal expression, then sentence).
- Answers are typed live into empty cells, each cell's final size reserved
  from the start, so the table never reflows.
- Side notes (glosses, word-form changes) appear next to the row and are
  erased once spoken. At the end of each row the whole table shows again.
- Auto zoom: when the table's text on screen is under 14 px, the camera
  zooms onto the active cell and follows the typing; otherwise no zoom.
  `prefers-reduced-motion` is respected.

**How the pipeline carries it:**

- *Screens* (`write_screens.py`). The table block is the board's fixed
  layer. Typed answers are written inside the cells as `[[...]]` and parsed
  into `typed` ({row, col, start, text}); `rows` keeps each cell's final
  text. A thought's `purpose` begins "Row N: " (or "Table: "), and the
  layout gives each row its own state; a thought's side notes carry
  `beside` {block, row}. The table's text size is the largest from 2.6% down
  to 1.9% of the frame's height at which the whole table fits the content
  band (`font`), with column widths from the cells' lengths (`col_widths`).
  No field was added to the model's reply schema: the structured-output
  grammar is at its size limit, so the typing is carried inside the
  existing `rows` strings and the row inside `purpose`.
- *Narration* (`write_narration.py`). A new cue, `type`, types one typed
  part: `block` the table, `text` the part. The audit requires each part
  typed once, in its row's state, in order within its cell, and never
  marked before it is typed.
- *Timeline* (`build_board_timeline.py`). A `type` cue starts a cue lead
  before its word and lasts 0.045 s a character.
- *Bundle* (format 1.2, additive): the table block's `core`, `typed`,
  `col_widths`, `font`; a working block's `beside`; a `type` cue's `typed`,
  `row`, `col`; a board's `table` and `focus` (the spotlight, stated as
  times, derived from each state's row and from what is read aloud, typed or
  marked in the table); a state's `row`. The renderer applies the new rules
  10 to 13 of docs/04-LESSON-BUNDLE.md §5. Auto zoom is the renderer's
  behaviour, not data.
- *Image tables* (`analysis/slide_tables.json`, one per lesson): the agent
  transcribes each table image from a 2x render, as printed, and checks it
  cell by cell. It is appended to the page's text for the understanding and
  screens stages (`build_sections.slide_tables_text`), and the screens audit
  compares the board's printed cells with it. Defects are corrected from
  the deck-defect register, never in this file.

## Consequences

- Grammar 1 and 2 are unaffected: their screens re-render byte-identical
  (except Grammar 1 page 18, whose saved file predates a category rename
  and differs only in that name), their narration audits are unchanged, and Grammar 2's bundle rebuilds
  identical apart from the 1.2 fields (checked 2026-09-25). Grammar 1's
  split tense table stays as accepted.
- The design system's "never solved by reducing the type size" has one
  exception, a table board, whose readability is kept by the zoom.
- A table whose cells are too long to fit even at the smallest size fails
  the screens audit rather than being split.
- The spotlight is derived, never authored: the narration model cues only
  what is typed, and the build states when each row and cell is in focus.
- `slide_tables.json` is agent work that the maintainer can check at the
  source gate; its method answers methodology §4's open question for tables
  (not for other image content).
- The screens and narration prompts changed, so a table section written
  before this ADR must be written again to become a table board.
