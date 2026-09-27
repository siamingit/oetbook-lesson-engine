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
