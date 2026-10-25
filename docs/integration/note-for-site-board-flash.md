# The board flash: a note for the site's player

Written 2026-10-25 for the oetacademy-web chat. No bundle data changes; no format
version changes. It concerns only how a player draws a board.

## What the owner saw

In Writing 1 (`writing-01-overview`), on the case-notes board (from 9:46) and the
model-letter board (from 14:04), the whole case-notes page went pale for about a
sixth of a second and came back, like a camera flash. It happened whenever the
narration moved on to a new point (a new state), when the notes were erased, and
above all when side notes were cleared to make room (a state's `clears`).

## The cause

It was in the engine's reference player only. At every new state, erase and clear,
the player rebuilt the inside of every block on the board from its `html`, the
board's fixed table included, then set the spotlight (rule 11), the verdicts
(rule 18), the word colours (rule 15) and the drawn diagram parts (rule 5) again.
Between the rebuild and the re-styling it read the layout, so the browser styled
the new cells first in their reset look: with the spotlight on (`.spot`) but no row
in focus yet, every cell took the dimmed opacity, 0.3. Then the row in focus was set
again, and `blocks.css`'s transition on table cells (`opacity .35s,
background-color .35s`) faded it back up. On a table whose focus row is the whole
page, as Writing 1's case notes are (one row, three columns), the whole page
dimmed and returned.

Measured frame by frame in headless Edge at 55 frames a second: the case-notes
table fell to 7% of its normal ink for 10 or 11 frames (110 to 170 ms) at 10:50,
13:02 and 16:43, and to 65% at 17:05. The same reset replayed other transitions and
animations elsewhere: word colours (`.wm`, 0.5 s), a choice table's verdicts, a
question's struck and ticked options (`.qo`, 0.3 s), the map's panels (`.dpanel`,
0.4 s), and the drawing of a timeline's parts. 19 of the 22 built lessons had it,
at 2,178 of their 5,725 state changes, erases and clears.

## Can the site's player have the same fault?

Yes, if it does what the engine's player did. Nothing in the bundle asks a player
to redraw the core: no field, rule or state means "draw the board's fixed blocks
again". A state lists only its working blocks; the fixed blocks (`boards[].fixed`)
and the pinned ones (`boards[].pinned`) are the board's own for its whole time. So
the site's player has the flash only if it recreates the fixed or pinned blocks'
elements when the state changes (for example a component keyed on the state, a
list re-rendered from the state, or `innerHTML` set again), or re-applies their
look from a reset one while `blocks.css`'s transitions are active. Check it at a
clear on Writing 1's case-notes board (`page-8_t1`, 13:02) and at any new state on
a table board whose row in focus does not change (Grammar 6 from 18:30).

## The rule a player must follow

**Core content is never redrawn within a board.** For as long as a board is shown,
its fixed blocks and its pinned blocks (once shown) stay on screen untouched: the
same elements, the same look. Only what changes at a moment may change: a highlight
moves (the spotlight, the active cell), a mark, a note or a part appears, a verdict
is set, notes fade out when erased or cleared. Nothing that stays the same may
disappear, dim, blink, be faded in again or be drawn in motion again, and no image
that stays may be loaded or decoded again. A move to a new board may use the
player's normal board transition.

If a player does rebuild a block's elements (the engine's reference player still
does, to re-wrap the phrases its marks will take), the new elements must take the
old look before the browser first styles them, so that every transition runs only
from the old look to the new one. The engine's player now carries over the row in
focus, the active cell, each verdict, each drawn diagram part, each map panel in
focus, each paragraph marked on a Part C map, each word colour already shown and
the images themselves.

## What changed in the engine

Only `spike/scripts/board_player_template.html` (the reference player). The bundle,
the text, the stylesheet and the audio of every lesson are unchanged. Every board
change of all 22 built lessons was screenshot before and after at the 590 px and
1120 px frames and compared pixel by pixel: 21,414 of 21,514 identical, the rest
different only in anti-aliasing (a timeline part now shown drawn where the old redraw
replayed its drawing). Frame-by-frame captures of Writing 1 at the owner's moments
show no blank frame after the fix.
