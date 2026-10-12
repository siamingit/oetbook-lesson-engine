# 011 — Every block fits the board: the fit, clears inside a state, tight boards

Date: 2026-09-27
Status: **Accepted** by the maintainer in chat, 2026-09-27 ("every block must fit
fully inside the board in every state, while text still never moves between
states. If a board cannot satisfy both, re-plan its layout ... never let content
overflow"). Bundle format 1.8 (docs/04-LESSON-BUNDLE.md); the rule is
docs/02-DESIGN-SYSTEM.md §8b.

## Context

The maintainer found a note on Grammar 5 (7:22) pushed under the player
controls, with a large empty gap above it. A new check (`check_overflow.py`,
every board state measured in the player at phone and laptop width) found the
same fault on every built lesson: 128 blocks outside the board in Grammar 1,
19 in Grammar 2, 18 in Grammar 3, 8 in Grammar 4, 45 in Grammar 5, most by 5 to
10% of the board's height and some by up to 38%.

Three causes:

1. **A pinned block took room from the start of its board.** The player drew
   every pinned block (a slide's result sentence, a definition pill) from the
   board's first moment, invisible until revealed, so that nothing moved when
   it appeared. A result revealed late reserved its room in every earlier
   state: the gap the maintainer saw.
2. **The layout never counted a pinned block after its reveal.** Pins are
   decided by the board style, after the layout; a pinned block carried into
   later states was on the board but not in their planned height.
3. **The layout plans with estimated heights.** A drawn block can be taller
   than its estimate (a header that wraps, a clause diagram, a note beside a
   table row), and a fixed or pinned block holds its lowest place on the board
   (§8a), which leaves room the estimate does not see.

Re-planning the states of a lesson already narrated would change which
utterances belong to which state, and so the narration and its audio; the
maintainer asked for screens only, no audio.

## Options considered

1. **Plan the layout with the pins counted, and re-plan every lesson.** Done for
   new sections; for the narrated ones it re-planned boards in all five lessons
   (measured), which the narration cannot follow without new audio.
2. **Smaller type, or a camera that scrolls.** The design system forbids smaller
   type outside tables (§3), and a scroll leaves blocks outside the board.
3. **Fit the drawn boards, without changing a state or a word** (this decision).

## Decision

- **A pinned block takes room from the start of the state it appears in**, not
  from the board's start (renderer). Within its state it is there, unseen, from
  the state's start, so nothing moves when it appears.
- **The layout counts a pinned block in every later state of its board**
  (`write_screens.lay_out`, for a section not yet narrated; a narrated section
  keeps the plan its narration was written against, methodology §18).
- **The fit** (`fit_boards.py`, the first step of the player stage) drives the
  player, built without any fit, through every state, note by note in the order
  the narration reveals them, at phone and then laptop width:
  - when a note appears and something lies outside the board, the notes of the
    state shown before it are **cleared** as it appears (bundle: a state's
    `clears`), as a teacher wipes the board to write the next thing. A fixed or
    pinned block is never cleared. A note that the narration still marks,
    points at or reads later in the state is never cleared;
  - a board still outside after clearing is made **tight**, on the whole board
    from its start so nothing moves between its states: level 1 halves the gap
    between blocks, level 2 also halves the blocks' vertical padding (bundle: a
    board's `tight`);
  - a table board whose table alone does not fit gets **smaller table text**,
    to no less than the floor for tables (1.9% of the frame's height; §7,
    Tables) (bundle: the table block's `font`, as since 1.2).
  The plan is written to `<lesson>/analysis/fit.json`, read by
  `build_lesson_player.py`, and made from scratch on every run.
- **Checks.** `check_overflow.py` fails any block outside the board or clipped,
  in any state, at phone or laptop width, and any label drawn in capitals;
  `check_layout.py` measures the words shown (not those waiting for their
  reveal, or cleared); `check_board_page.py` fails a clear that takes a pinned
  block, and a mark, a point or a reading on a block after it is cleared.
- **Labels in sentence case.** A label written in capitals ("GRAMMAR TERM") is
  put in sentence case when parsed, acronyms kept; the screens audit fails a
  label in capitals; the screens prompt's examples are in sentence case; a
  category card's header is no longer drawn in capitals.

## Consequences

- Bundle 1.8: a state's `clears` (`[{time, blocks}]`), a board's `tight` (0, 1
  or 2), renderer rules 21 to 23. A 1.7 renderer ignores them and draws the
  lesson as before: some states then overflow.
- No narration, audio, id or time changes. Every lesson's screens re-render
  with the same boards and states; only labels change case.
- A clear is not spoken: the narration of a lesson already built does not say
  "let me clean the board". For a new lesson the layout, which now counts pins,
  plans erasures the narration knows about, and the fit only corrects what the
  estimates missed.
- A board fitted tight looks slightly denser than the others. A board that
  still does not fit at level 2 fails the build and needs a screen change.

## Amendment, 2026-10-11: the player's guard on every board of every lesson

Decided by the maintainer in the brief of 2026-10-11 ("extend the player's runtime
guard (built for Part B) to every board type ... Pictures are scaled to fit, never
cropped ... Record the rule in the design system and an ADR amendment: the runtime
guard applies to every board in every lesson"). How it is carried was chosen by the
agent under that brief; the maintainer may reverse it.

### Context

The fixed visible-area checks of 2026-10-08 (ADR 026, second review) measure the
board between the header and the control bar at three frames: a phone held
landscape (915x412, a 590 px frame whose controls keep 44 px, 13% of its height),
phone-landscape (812 px) and laptop (1120 px). The fit (this record) measured only
the last two for every lesson fitted before 2026-10-08. On the 590 px frame, where
the controls take relatively more of the frame, they found content of 14 built
lessons a few pixels under the control bar or past the board's foot: 140 blocks
outside the board and 50 under the control bar, every one at that frame only
(text blocks 2 to 15 px, the board pictures of Reading 2, Grammar 8 and Vocabulary
1 to 3, Reading 2's map 10.8 px on its 20 question boards). Reading 1's picture at
9:05 (118 px past the right edge in the table zoom) was already fixed by the camera
change of 2026-10-08 once the player is rebuilt. The same can happen on any device
whose font is wider than the fit's. Part B and Part C question boards had their
own guard (ADR 026, 2026-10-08); no other board had one.

### Options considered

1. Re-fit every lesson with the small phone frame (`fit_boards.py --small-phone`).
   Rejected: the fit's plan is one for all frames (clears, tight, table size), so
   it would change the lessons at 812 and 1120 px too, and it does not cover
   device fonts.
2. Scale every board at a small frame by a fixed factor. Rejected: it changes
   boards that fit, and a fixed factor knows nothing of fonts.
3. **A guard in the player for every board, measured on the device** (chosen):
   it changes only a board that does not fit, on the device where it does not fit.

### Decision

- **Every board other than a question board** is measured by the player on the
  device when it is first drawn and again whenever the frame's size or the fonts
  change, at the moments `check_overflow.py` measures (each state's start and
  end, each reveal, each pinned block, each erase), as that check measures them
  (the camera's zoom undone, except on a table board whose camera has moved,
  where its notes must be in view as shown). Where any block shown would lie
  outside the board (under the header or the control bar, or past an edge), or
  whose words would spill out of it (a long word in a narrow table cell):
  - first the board's **pictures** are set smaller, scaled whole and never
    cropped, to no less than 10% of the frame (design system §7e), where that
    makes the board fit or brings it closer;
  - then **every block of the board** is set smaller together (CSS zoom, in
    steps of 0.5%), its layout and proportions kept, until everything fits, never
    below the floors: body text 2.6% of the frame (the floor of the Part B guard's
    question column), a table's text 1.9% (the tables' floor: a table stops there
    while the other blocks go on), a picture 10% (it keeps that size as the board
    shrinks). A step that brings nothing closer is not kept: the best size found
    is drawn.
  The sizes hold for the whole board, so nothing moves between its states
  (design system §8a). Where the board fits, the guard changes nothing. A Part B
  or Part C question board keeps its own guard.
- **No data change**: the bundle is unchanged (renderer rule 41,
  docs/04-LESSON-BUNDLE.md). The fit runs with the guard off, as before.
- **Checks.** `check_wide_font.py` now forces Verdana on every board of every
  lesson at the three frames (question boards as before; every other board at
  the overflow check's moments, with its camera rule) and reports each board the
  guard set smaller; the runner runs it for every lesson, not only Reading.

### Consequences

- On a frame where everything fits (the reference player at 812 and 1120 px),
  every built lesson draws exactly as before: proved by `render_compare.py`
  (below). On a smaller frame, or with a wider font, a board that would not fit
  is drawn slightly smaller.
- The first drawing of a board measures it, once per frame size and fonts: in
  headless Edge on this machine typically 5 to 30 ms a board; a table board with
  many moments takes longer (Grammar 3's largest, 111 moments, about 1.4 s at
  every frame, Grammar 6's and Vocabulary 1's largest 0.3 to 1 s), when the
  board first appears. Open: measuring ahead of the board, so no board waits.
- A board that does not fit even at the floors is reported by the checks, never
  hidden: it needs a screen change or the maintainer's ruling.

### Results (2026-10-11, the 16 built lessons)

- **Before** (the current player code, every lesson rebuilt with it): at the
  590 px frame 140 blocks outside the board and 50 under the control bar, in 14
  lessons; at 812 and 1120 px none.
- **After**: `check_overflow.py`, `check_overlap.py` and `check_lens.py` pass every
  lesson at 590, 812 and 1120 px. At 590 px the guard sets 89 boards smaller in 13
  lessons (Reading 3, 4 and 5 were fitted for that frame and need nothing): the
  whole board at 94% to 99% (body text 3.0% to 3.17% of the frame), or only its
  pictures at 75% to 97% of their size. `check_wide_font.py` (Verdana, every
  board) passes 15 lessons at the three frames, and Grammar 6 at 812 and 1120 px.
- **Not fitted**: Grammar 6, board pages-07-08_t2 (18:30 to 27:32), with Verdana
  at 590 px only: its table, already at the tables' floor (1.9%) and tight, is
  251 px tall in a 245 px board while it shows whole, 1.3 to 6.3 px over the
  board's foot at 32 moments. With the default fonts it fits. Left to the
  maintainer (a table's text below 1.9% under the guard on a small frame, or a
  shorter table); the floor is not broken.
- **Unchanged**: `render_compare.py` (before and after, every lesson): 16 of 16
  identical at 812 and 1120 px: 468 data files byte for byte (bundle, text,
  timeline, audio index, fit), 113,532 moments drawn and in the DOM identically,
  no board's timing changed. Every lesson's 9,058 audio, narration and player
  data files hash-identical (8,464 clips, 8,650 utterances with their text, times
  and clips, every board's and state's times). No paid call; no audio made.

## Amendment, 2026-10-12: one table shown whole, boards measured ahead, phone text size

Decided by the owner in the brief of 2026-10-12. How the first two are carried was
chosen by the agent under that brief; the owner may reverse it.

### Grammar 6, board pages-07-08_t2: the table whole, below its floor (owner)

A per-board exception, not a rule change (design system §7, Tables). On this board
only (18:30 to 27:32) the table's auto zoom is removed: the camera never zooms onto
the active cell, and never pans the table up to its notes, so the whole table is in
view at every moment. The player's guard sets the board smaller as far as the whole
table and its notes need to fit; the table's text may go below 1.9% of the frame,
and the other blocks stop at the body floor (2.6%), as the guard's search goes on
with the table alone. On this board the guard keeps the largest size that fits (in
steps of 0.5%), not the first found. Carried in the reference player only
(`TABLE_FREE`, by lesson and board id): the bundle is unchanged, and the fit
(`fit_boards.py`, guard off) plans the board as before. A renderer that draws from
the bundle alone does not know of the exception.

### Boards measured ahead

The guard measured a board the first time it was drawn, so a large board waited as
it appeared (measured 2026-10-12 in headless Edge: up to 1.14 s, Grammar 3 page-8 at
the 590 px frame; 0.79 to 0.90 s on Grammar 3, 6, 8 and Vocabulary 1). Now the
player measures every board other than a question board ahead, from the board after
the one shown on, in a hidden copy of the page (the same frame size, viewport, styles
and fonts), one moment or one state's layout at a time in idle time, and hands the
sizes to the page. The copy runs the same guard code, so the sizes are the same;
only when they are measured changes. A board not yet measured (a jump far ahead, a
frame just resized) is measured as it is drawn, as before; so is every board where
the copy's frame does not match the page's (it stops), and in a measuring harness,
where the copy does not start (`__lockWidth` without `__measureAheadOn`). The first
board shown is measured at load, as before. A question board keeps its own guard,
which measures when the board is drawn.

### Phone board text size: no change (owner)

The site chat (siamingit/oetacademy-web) reported board text too small on phones
(about 5 to 6 px held upright, about 9 to 10 px in fullscreen sideways) and offered
three options: (1) a minimum text size, (2) a readability zoom for ordinary text,
(3) a phone layout variant. Owner decision, 2026-10-12: none of them for now; board
text sizing on phones stays as it is. Nothing is needed from the site side
(siamingit/oetacademy-web#91).

### Results (2026-10-12, the 16 built lessons)

- **Grammar 6, pages-07-08_t2**: no zoom and no pan at any frame. At 590 px the board
  is set at 91.5% with the default fonts (table text 1.74% of the frame, about 5.8
  px) and 89.0% with Verdana (1.69%, about 5.6 px); at 812 px 97% and 92.5%; at 1120
  px 100% and 93.5%. The table and its notes are whole inside the board at every
  moment.
- **Measured ahead**: in a hidden copy, every board other than a question board of
  every lesson, at 590, 812 and 1120 px, with the default fonts and with Verdana
  (96 runs): every board measured ahead, and every size identical to the board
  measured as drawn. In a browser window of 915x412: Grammar 3's boards all measured
  within 25 s of opening, Grammar 6's within 30 s; the longest step 10 to 14 ms; a
  board's change now 0.3 to 68 ms (its drawing; Grammar 3's page-8, 1.14 s before).
- **Unchanged**: `render_compare.py` (before and after, every lesson, 812 and 1120
  px): 15 of 16 identical, and every data file of all 16 byte for byte, no timing
  changed. Grammar 6 differs only on pages-07-08_t2 (the zoom gone, the board
  smaller at 812 px), and, carried from it, the hidden reading pointer's resting
  place at the first three moments of pages-09-10_t1 at 812 px, and an empty style
  attribute the old zoom left on the board element. 13,019 audio, narration and data
  files hash-identical. `check_overflow.py`, `check_overlap.py`, `check_lens.py` and
  `check_wide_font.py` pass all 16 lessons at the three frames. No paid call; no
  audio made.
