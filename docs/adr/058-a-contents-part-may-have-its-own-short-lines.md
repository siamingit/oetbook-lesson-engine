# ADR 058 — A contents part may have its own short lines

Date: 2026-11-15 (the owner's review of Speaking 4 Asking Questions v1-draft.2, issue #212).

Status: Accepted. It adds one optional field to a category in a lesson's `analysis/sections.json`, read by
`build_lesson_boards.py` and `check_board_page.py`. A lesson without that field builds and is checked exactly as
before. It changes no bundle format, no player, no stage and no other check. It amends ADR 042 (the contents
board lists every section) and leaves ADR 054 (the contents line) as it is.

## Context

The owner, 2026-11-15, on the contents board ("What you will learn") of Asking Questions v1-draft.2:

> "Too many parts and lines: the numbers are out of order (4 above 3), and one column is empty. Fix it by
> grouping, not by a new board. Use at most 7 parts, each with at most 4 short lines, in two columns ordered 1
> to 7, like S2 and S3. The sections stay as they are; only the contents groups them."

The lesson has 35 sections. The contents board lists each part with its sections' titles, one per line (ADR
042: every section is listed, and `check_board_page.py` fails a board that leaves one out). Seven parts of four
lines hold 28 lines, so 35 section titles cannot fit, however they are grouped. The only way to meet both rules
is to let one short line stand for two sections that belong together, such as "Checking meaning" for "Asking
what they mean" and "Checking they understand".

## Decision

1. **A category may give its own short lines.** In `analysis/sections.json`, a category may carry
   `lines: [{"text": "...", "sections": ["...", ...]}, ...]`. Each line is the words shown under the part and the
   sections it stands for. The contents item then shows those lines instead of the section titles.
2. **The lines must account for the category exactly.** Together, the lines hold the category's sections, each
   once and in order. There are at most 4 lines (`CONTENTS_LINES_MAX`). A line is never empty, always stands for
   at least one section, and carries no " · " (the line separator). `build_lesson_boards.py` refuses anything
   else.
3. **Every section is still listed.** A section counts as listed on the contents board when its title is shown,
   as before, or when its category's own lines are shown, exactly as sections.json gives them.
   `check_board_page.py` checks this on the built player. A board that shows other words for a part with
   `lines` still fails.
4. **Seven parts at most stays an authoring rule.** The owner's "at most 7 parts" is how a Speaking lesson's
   contents is grouped, as in Speaking 2 and 3. The engine's limit (`CONTENTS_MAX = 12`) is unchanged, so no
   live lesson is affected.

## Proof that the live lessons are unchanged

`build_lesson_boards.main()` and `check_board_page.check()` were run on all 32 lessons in the library
(C:\OET\lessons), once with the scripts at main (dc3d9cf) and once with this change. Every file write was
captured in memory and hashed, so no lesson was touched. Both runs give the same result:

- all 32 builds succeed;
- the 64 files they would write have identical hashes;
- `check_board_page` finds no problem on any of the 32 players.

No live lesson has `lines`, so the new path is used only by Asking Questions.

## Consequences

- Asking Questions groups its 35 sections into 7 parts of 4 lines, numbered 1 to 7 in two columns. The
  sections, their order and their narration are unchanged, and only the introduction's contents walk-through
  is rewritten to match the parts.
- The player's contents menu still lists the sections under their category, as before.
- Any later lesson with more sections than the contents board can list one per line can use `lines`, under the
  same checks.

## Amendment (1), 2026-11-15: Asking Questions uses 15 lines, not 28

The Consequences above say Asking Questions groups its 35 sections into "7 parts of 4 lines". That was the first
try, and it did not fit. The contents board sets its parts in a wrapping row, two at a time: part 1 beside part 5,
part 2 beside part 6, part 3 beside part 7, then part 4 alone. Each row is as tall as the taller part in it, so the
column 1 to 4 only fits when few parts are tall. With 28 lines, and again with 16 lines (two parts of 3 lines,
beside parts 1 and 2), the fit cleared parts 1 to 3 before part 4 entered, and `check_board_page.py` failed the
board (ADR 042: the contents fits on one board).

The lesson as built for v1-draft.3 has 7 parts, six of 2 lines and one of 3: 15 lines in all, as Speaking 2 (15 lines, one
part of 3). Each line stands for one to four sections of its part, such as "Checking and summing up" for "Asking
what they mean", "Checking they understand", "Summing up" and "Asking for more". The decision is unchanged: at most
4 lines a part is the engine's limit (`CONTENTS_LINES_MAX`), and how many a lesson uses is an authoring choice, made
so the board fits. A lesson of 7 parts fits when at most one part has 3 lines. Nothing in the engine changes with
this amendment.
