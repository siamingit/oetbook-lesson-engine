# 020 — No block overlaps another block or its text

Date: 2026-09-30
Status: **Accepted** (the rule) by the maintainer in chat, 2026-09-30: "as a
general rule: no block may overlap another block or its text in any state. Add
an overlap check next to the layout and overflow checks, and run it on lessons
1-7 too (fix anything it finds; screens only)." How it is carried below was
chosen by the agent under that request; the maintainer may reverse it.

## Context

Grammar 8's silent preview showed two faults: at about 4:20 a timeline, a side
note on the table board "Paraphrasing in eight steps", was drawn on top of the
table's text; at about 34:34 the timeline "Mrs Wright's events in time" was
tiny and its labels were drawn over each other.

Both came from rules, not accidents. A table board's side notes were drawn
"next to their row, over the other rows" (ADR 007, bundle rule 12), with a
maximum width of 58%, so a timeline side note was squeezed into a small box
over the table. And a timeline's marker labels were centred on their ticks
with nothing to stop two labels from meeting. No check measured overlap: the
overflow check (ADR 011) measures blocks against the board, not against each
other. Run on lessons 1-7, the new check found 850 overlaps (both widths), all
side notes over table rows (Grammar 3-6).

## Decision

- **The rule**, for every lesson, every state, phone-landscape and laptop
  width: no block overlaps another block, and no text is drawn over other
  text (docs/02-DESIGN-SYSTEM.md §8d; bundle rule 28).
- **Side notes go under the table**, in the order their state lists them,
  never over its rows; the row is shown by the spotlight, not by where the
  note sits. A diagram side note has the table's width. Where the notes do
  not fit under the table, the fit (ADR 011) clears earlier notes, makes the
  board tight, then makes the table's text smaller, to the tables' floor
  (1.9% of the frame's height); only then does the table board's camera pan
  the table up, unzoomed, so the notes are in view, as the zoom already does
  on a small screen (bundle rules 12, 13).
- **Timeline marker labels** that would meet are set on further lines under
  the axis (lanes, `write_screens.marker_lanes`), and the diagram's height
  grows to hold them.
- **The check**: `check_overlap.py`, beside `check_layout.py` and
  `check_overflow.py`. It drives the player to every moment a board changes,
  at both widths, and fails any two shown blocks whose boxes intersect and any
  two lines of text inside one block that intersect. The runner runs it on the
  finished player and, with the fit and the overflow check, on the silent
  preview before the narration gate (`fit_boards.py --silent`).
- Bundle 1.12 (rules 12, 13 changed, rule 28 added). No field changes.

## Consequences

- Lessons 1-7 were rebuilt, screens only (the fit, the player; no narration or
  audio changed): every structural, mark, layout, overflow and overlap check
  passes. Grammar 3-6's side notes now sit under their tables; on Grammar 6's
  densest board the view pans to them.
- The overflow check and the fit measure a table board's notes as its camera
  shows them where the camera has moved (under zoom or pan the table itself
  may leave the view; the notes may not).
- The silent preview is now fitted and checked like the finished player, so
  what the maintainer sees at the narration gate is what the final gate will
  show.
