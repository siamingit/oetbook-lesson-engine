# 009 — Choice tables, gaps in a printed text, and marks in table cells

Date: 2026-09-25
Status: **Accepted** by the maintainer in chat, 2026-09-25, at the start of
Grammar 4 (Articles): bundle format 1.6 for cell verdicts ("fade the wrong
columns and mark the right one with a tick") and a blank line for a gap not yet
typed. The rule is docs/02-DESIGN-SYSTEM.md §7, "Tables"; the data is
docs/04-LESSON-BUNDLE.md, format 1.6.

## Context

Grammar 4 teaches articles from three kinds of slide that ADR 007's table
board did not fully cover:

- **Choice tables.** Pages 12-14 give, per row, versions of one sentence
  ("a left knee operation" / "the left knee operation" / "left knee
  operation") and the class says which is right. Nothing is typed: the teacher
  ticks and crosses cells. A table board could spotlight the row and strike a
  wrong article, but a cell could not be faded and nothing could draw a tick.
- **A text with gaps.** Page 15 is a referral letter with 13 blanks. ADR 007
  already types answers into gaps of a printed sentence, but a part not yet
  typed was invisible space: the student could not see where the gaps were.
- **Repeated phrases.** A mark found its phrase at the first place it occurs
  in the block. In a choice table every cell of a row shares most of its words,
  and the letter repeats "temperature of" and "pulse rate of": a mark meant for
  one cell could land in another.

## Options considered

1. **Existing tools only.** Spotlight the row, highlight the right cell in
   amber, strike the wrong articles. No format change, but no tick and no fade,
   and the highlight moves on as the narration moves.
2. **A new narration cue for verdicts.** Changes the narration's reply schema.
3. **Verdicts as data, their times derived** (this decision). The screens
   stage carries each cell's verdict inside the existing `rows` strings, as ADR
   007 carries typed parts; the bundle builder states when each shows, from the
   narration's own marks. No schema change.

## Decision

Option 3, for every lesson.

- **Choice tables.** The screens model ends each body cell of a choice table
  with `{{right}}`, `{{wrong}}` or `{{possible}}` (also acceptable, or correct
  only in some context); `write_screens.unverdict_rows` moves them into the
  table block's `verdicts`. The audit requires a verdict on every body cell and
  at least one right cell per row, and nothing typed. The narration strikes the
  words that make a wrong cell wrong and circles those that make a right cell
  right; it never strikes a right or possible cell (audit). The builder states
  each verdict's time: a wrong cell fades at its first strike, or when its row
  is settled (the row's last speech ends); the right cell takes its tick at its
  first circle, or when the row's last wrong cell fades; a possible cell is
  marked when the row is settled. They stay until the board ends, so the whole
  table ends as a summary of the answers.
- **Gaps.** A typed part inside printed words (its cell has letters or digits
  outside its typed parts) is a gap: its html carries the class `gap`, drawn as
  a blank line of fixed width with the answer typed onto it. A typed part that
  fills its cell (an answer column) is unchanged: invisible until typed.
- **Marks in cells.** A mark on a core table names the cell it lands in
  (`row`, `col`): the first cell of the state's row that holds its phrase, else
  the first cell of the table. The narration audit fails a phrase found in more
  than one cell of the state's row (on a choice table; a warning elsewhere).
  The renderer draws the mark in that cell; an arrow's end names its cell the
  same way (`to_row`, `to_col`). Where a phrase is in more than one cell of
  the row, the section's narration `overrides.json` names the cell
  (`{"cues": {"<utterance id>/<cue id>": {"expect", "row", "col", "to_row",
  "to_col", "note"}}}`), applied on every render like the screens'
  overrides; nothing spoken changes, so no audio does. Grammar 3's three such
  marks were named this way at the maintainer's word (2026-09-25) and its
  player rebuilt at 1.6, audio and every time unchanged.
- **A text with gaps is a table of one column.** Page 15's letter is taught as
  a table board: its greeting as the header, a row per paragraph, the closing
  last. The spotlight moves paragraph by paragraph, each gap is typed in place,
  side notes give the reasons, and the whole letter shows again at the end.
  This uses ADR 007 as it is.
- Colours: the tick is the green of "correct" on the correct cell's pale green
  fill; a wrong cell is faded, not red (red stays with the narration's strike).

## Consequences

- Bundle format 1.6 (docs/04-LESSON-BUNDLE.md): a table block's `verdicts`; a
  board's `verdicts` with times; a mark cue's `row` and `col` on a core table;
  the `gap` class; renderer rules 6, 10 and 18. A 1.5 reader ignores them: it
  shows the table without fades or ticks, a gap as blank space, and a mark at
  the phrase's first occurrence.
- Grammar 1 and 2 are not rebuilt. Grammar 3's player was rebuilt at 1.6
  (maintainer, 2026-09-25): every utterance, audio file, time and cue is as
  before, and its typed parts after printed words ("suggest → suggestive of")
  now show as gaps. The screens and narration audits of all three still pass
  (checked by re-rendering every section, files restored).
- The structural check verifies that each mark's cell (and an arrow end's
  cell) holds its phrase and that a board's verdicts are its table's, shown
  within the board.
- Fixed with it, as bug fixes: the register audit's "sound" matches only a verb
  that judges a word ("sounds formal"), not "a vowel sound"; a contents item's
  height estimate matches its drawing (a deck with no contents slide has no
  section list under each item).
- The narration prompt's table rule no longer assumes Grammar 3's column order
  (case note, formal expression, sentence).
