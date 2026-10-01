# Player rendering rules: bundle format 1.12

The rules a lesson player applies to show a lesson from its bundle. They hold
for **lesson bundle format 1.12** (`bundle.json`: `"format":
"oetbook-lesson-bundle"`, `"format_version": "1.12"`), stated 2026-10-01.

This document is for the website's own repository, so it is self-contained.
The player reads `bundle.json`, `text.json`, `blocks.css`, the audio clips and
the image files, and needs nothing else. Fields are named by their place in
`bundle.json` (§1).

## 0. Scope

- **These are the only rules.** Every time and every target they use is in the
  bundle. A player never works out lesson content for itself. If it needs
  something the bundle does not state, the bundle is wrong, and the fix is a
  new format version from the engine, not logic in the player.
- **Blocks are drawn by their `html`**, styled by `blocks.css`. A player may
  instead draw a block from its data, as long as it keeps the block's word
  order and its hooks (§4). The player itself draws what changes over time:
  reveals, marks, word marks, the reading pointer, typing, the table spotlight
  and verdicts, diagram motion, zoom and pan.
- **How things move is the player's choice**, within §3 and §5.
- **Format versions.** Each rule names the version that introduced it, and
  the version that last changed it if any. A 1.x bundle older than a rule has
  no data for that rule. Rules 19 and 28 have no data and apply to every
  bundle. Rules 12 and 13 changed in 1.12; the 1.12 text below is the one that
  applies.

| Rule | Since | Changed | Subject |
|---|---|---|---|
| 1–5, 7–9 | 1.0 | | clock, board, state, working block, diagram part, tense chip, reading pointer, pause |
| 6 | 1.0 | 1.6 (marks in table cells) | marks |
| 10 | 1.2 | 1.6 (gaps) | typed parts |
| 11 | 1.2 | | spotlight |
| 12 | 1.2 | **1.12** (under the table) | side notes |
| 13 | 1.2 | **1.12** (pan) | auto zoom |
| 14–17 | 1.3 | | pinned blocks, word marks, folded blocks, trimmed clips |
| 18 | 1.6 | | verdicts |
| 19 | 2026-09-26, no data | | nothing moves a word |
| 20 | 1.7 | | clause diagram |
| 21–23 | 1.8 | | a pinned block's room, clears, tight boards |
| 24 | 1.9 | | relative and participle clauses |
| 25 | 1.10 | | gloss |
| 26 | 1.11 | | a gloss's image |
| 27 | 1.12 | | a board's picture |
| 28 | 1.12, no data | | nothing over anything |

## 1. The fields the rules use

Times are seconds from the start of the lesson, rounded to milliseconds. "The
board" is an entry of `boards[]`, "the state" an entry of its `states[]`, "the
utterance" an entry of the state's `utterances[]`, and "the cue" an entry of
the utterance's `cues[]`. Block ids index `blocks{}`.

| Field | Meaning |
|---|---|
| `boards[].start` / `.end` / `.until` | the board appears / its last speech ends / the next board appears (or the lesson ends) |
| `boards[].title` | the header text while the board is shown |
| `boards[].fixed` | the fixed layer's block ids, in order |
| `boards[].reveal` | `{part id: time}` for every part of every fixed-layer diagram |
| `boards[].table` | on a table board, its core table's block id; otherwise null |
| `boards[].focus` | on a table board, the spotlight `[{time, row, col}]`, in time order |
| `boards[].verdicts` | on a choice-table board, `[{row, col, verdict, time}]`, in time order |
| `boards[].pinned` | `{block id: time}`: working blocks that stay once revealed |
| `boards[].wordmarks` | `[{block, text, cls, time, row?, col?}]` |
| `boards[].tight` | 0, 1 or 2 |
| `states[].working` | the working layer's block ids, in order |
| `states[].start` / `.end` / `.until` | its first speech starts / its last speech ends / its working layer and marks disappear |
| `states[].erase` | `{time, blocks}` when the state ends in an erase, otherwise null |
| `states[].row` | on a table board, the row this state teaches, or null |
| `states[].clears` | `[{time, blocks}]`, in time order |
| `states[].reveal` | `{id: time}` for every working block and every part of a working diagram |
| `utterances[].start` / `.end` | when it plays |
| `utterances[].audio_file` | its clip, relative to `bundle.json` |
| `utterances[].clip_in` / `.clip_out` | the part of the clip played, in seconds into the file |
| `utterances[].reading` | `[{block, words: [[k, start, end], …]}]`: board words read aloud, as word `k` of `block` |
| `cues[].type` | `reveal`, `pause`, `type`, or a mark: `underline`, `highlight`, `circle`, `strike`, `bracket`, `point`, `arrow`, `replace` |
| `cues[].time` / `.time_end` | when it takes effect (already a short lead before its word) / the end of its word; for a pause the end of the silence; for a `type` the end of the typing |
| `cues[].block`, `.text` | the block (or diagram part, for a reveal) it acts on; a mark's phrase inside that block |
| `cues[].to_block`, `.to_text` | an arrow's end |
| `cues[].with` | a replace mark's correction |
| `cues[].seconds` | a pause's length |
| `cues[].typed`, `.row`, `.col`, `.to_row`, `.to_col` | a `type` cue's typed part and its cell; a mark's cell, an arrow end's cell, on a core table |
| `blocks{}.type` | `plain`, `error_row`, `answer_row`, `term_box`, `comparison`, `callout`, `category_card`, `timeline`, `table`, `clauses`, `gloss`, `picture`, `contents_item`, `lesson_title` |
| `blocks{}.items` | a diagram's parts in order: `timeline` (`period`, `point`, `now`, `arrow`, `marker`, `series`, `pointer`, `callout`), `clauses` (below, rules 20 and 24), `gloss` (`meaning`, `picture`, `example`). Part id: `<block id>.<part>` |
| `blocks{}.tags` | tense chips `[{text, family, label}]` |
| `blocks{}.core` | true for a table board's whole table |
| `blocks{}.typed` | a core table's typed parts `[{row, col, start, text}]`; the index is the part's number |
| `blocks{}.verdicts` | on a choice table, each body cell's verdict |
| `blocks{}.beside` | a side note on a table board: `{block, row}` (row null: the whole table) |
| `blocks{}.fold_into` | the block this one is part of |
| `blocks{}.image` | `{file, alt}`: a PNG, relative to `bundle.json` |
| `blocks{}.size` | a picture's side in cqh; null for 20 |
| `blocks{}.html` | the block drawn, styled by `blocks.css` |
| `lesson.tense_colours` | true only in a lesson about tenses |
| `meta.reading_hold_s` | how long the reading pointer stays on the last word read (2.5 in every current lesson) |

Rows and columns count from 0, the header not counted.

## 2. The rules

1. **The clock** (1.0). While an utterance plays, the lesson time is its
   `start` plus the audio's position. Between utterances, a timer runs to the
   next `start`. Seeking to `t` plays the utterance containing `t` from
   `t - start`, or waits for the next one.
2. **The board** (1.0) at `t` is the last board whose `start` ≤ `t`. Its fixed
   blocks are shown whole for the whole board, and the header shows its
   `title`.
3. **The state** (1.0) at `t` is the last state whose `start` ≤ `t`, while
   `t` < its `until`. From `until` to the next state's `start` the working
   layer is empty.
4. **A working block** (1.0) is shown while its state is current and `t` ≥
   `state.reveal[id]`.
5. **A diagram part** (1.0) is shown while its block is shown and `t` ≥ its
   reveal time: `board.reveal` for a fixed diagram, whose parts stay through
   every erasure; `state.reveal` for a working one.
6. **A mark** (1.0; cells 1.6) is shown from its `time` until its state's
   `until`, on `text` as it occurs in its block's words. The engine checks
   before publishing that the phrase is there. A mark with `row` and `col` is
   drawn on `text` inside that table cell, and an arrow's end with `to_row` and
   `to_col` on `to_text` inside that cell. A mark may cross elements inside
   the block, such as a tense chip. An arrow joins `text` in `block` to
   `to_text` in `to_block`. A replace strikes `text` and writes `with` above
   it. Mark looks: §3.
7. **A tense chip** (1.0) sits under the first occurrence of each tag's `text`
   in each text field of its block, labelled `label`, in its family colour
   (§3). The block's `html` already draws it. When `lesson.tense_colours` is
   false, the chip keeps its label and is drawn neutral.
8. **The reading pointer** (1.0) is on the latest `reading` word whose start
   ≤ `t`, until that word's end plus `meta.reading_hold_s`. Otherwise it is
   on the latest `point` mark still shown, and otherwise hidden. Word `k` of a
   block is its k-th whitespace-separated token that contains a letter or a
   digit, counted through the block's text in document order (§4).
9. **A pause** (1.0) is silence of `seconds` after its utterance, already
   included in the next `start`.
10. **A typed part** (1.2; gaps 1.6) of a core table is hidden before its
    `type` cue's `time` and typed in from `time` to `time_end`: the share of
    its characters shown grows evenly. After `time_end` it is shown whole. It
    keeps its final size while hidden, so the table never reflows. While
    typing it may be split in the player's DOM, but for rule 8 it still counts
    as one text. A typed part with the class `gap` (a gap in a printed
    sentence) is drawn as a blank line of fixed width before its cue, and its
    answer is typed onto that line. Typed text is in the blue of teacher
    emphasis.
11. **The spotlight** (1.2) on a table board is the latest `focus` entry whose
    `time` ≤ `t`. Rows other than `row` are dimmed and the cell (`row`, `col`)
    is highlighted in translucent amber. With `col` null the row alone is in
    focus; with `row` null nothing is dimmed.
12. **A side note** (1.2; changed in 1.12), a working block with `beside`, is
    shown by rule 4. It is drawn under the table, and under anything else in
    the board's flow, in the order its state lists the notes, never over the
    table or any text. `beside.row` names the row it is about; the spotlight
    shows that row, not the note's position. A diagram side note (a timeline
    or a clause diagram) is as wide as the table. A board's picture on a table
    board sits at the right under the table, with the notes to its left.
    Before 1.12 a side note was drawn next to its row, over the other rows.
13. **Auto zoom** (1.2; pan added in 1.12) is the player's. When a core
    table's text on screen is smaller than 14 px, the view zooms onto the
    highlighted cell (or the row) and its visible side notes, and follows the
    typing. At 14 px or more there is no zoom. Where the visible side notes run
    past the board, the view pans the table up, unzoomed, until they are in
    view. Under `prefers-reduced-motion` the view moves without animation.
14. **A pinned block** (1.3) is shown from its time in `pinned` until the
    board's `until`, through every erasure.
15. **Word marks** (1.3; cells 1.4) are drawn under the cues' marks, from
    their `time` to the board's `until`. `text` in `block` is marked `cls`:
    a word class, in its colour (§3), or `slide-underline`, the slide's own
    underline. With `row` and `col`, `text` is marked inside that table cell
    only.
16. **A folded block** (1.3), one with `fold_into`, is not drawn. It is in no
    board's `fixed`, and no cue names it.
17. **A trimmed clip** (1.3) plays from `clip_in`: the lesson time is the
    utterance's `start` plus the audio's position minus `clip_in` (rule 1),
    and the utterance ends at `clip_out`.
18. **A verdict** (1.6) on a choice table's cell is shown from its `time`
    until the board's `until`, through every change of the spotlight. A
    `wrong` cell is faded. A `right` cell carries a tick on the pale green of
    "correct". A `possible` cell (also acceptable, or right only in some
    context) is left as it is. The table ends the board as a summary of the
    answers.
19. **Nothing moves a word** (2026-09-26; no data). Nothing a player draws
    for a moment (spotlight, marks, word marks, verdicts, typing, reveals)
    ever moves a word of the board: a word, once on a board, stays exactly
    where it is until the board ends or its note is erased.
    - Spotlight and active styling (row focus, the active cell, a verdict)
      use opacity, background, `outline` or `box-shadow` only, never a change
      of border width, padding, margin, font or size.
    - Marks are drawn in an overlay layer, never inline. A phrase may be
      wrapped so it can be found, but the ring, line, tint or bracket is drawn
      over it, measured from where the words already are.
    - Every phrase a mark or a word mark will take is wrapped when the state
      is drawn, and marks only switch on and off. A wrapper added later
      splits the text into runs and can re-break a line.
    - Typed answers have their final width reserved from the start. The
      typing cursor takes no room in the line.
    - Fixed and pinned blocks hold their place. Where a state's working
      blocks come before them in the board's flow, each is held at the lowest
      place it takes in any state of the board.
    - The frame's size never depends on what is shown around it, since every
      size in the frame is a share of its height (§5).
20. **A clause diagram** (1.7), block type `clauses`, is a diagram: its parts
    are revealed by rule 5.
    - A piece (`dependent`, `independent`) and a bridge (a `glue` with
      `piece` null) are shown from their reveal.
    - A `glue`, `subject` or `verb` part is a phrase already shown in its
      piece. It takes its look from its reveal: the glue chip, the S or V
      label, the verb blue.
    - From the `join`'s reveal, the tab stands in the notch, and a dependent
      piece that comes first shows its comma.
    - None of it moves a word (rule 19): the pieces never move, only the tab
      and its neck. The S and V labels sit in the line's own leading, the glue
      chip is a background and a shadow, and the comma's room is reserved from
      the start. Looks: §3.
21. **A pinned block's room** (1.8). A pinned block takes room on its board
    from the start of the state in which it appears (its time in `pinned`),
    and none in earlier states. Within its state it is there, unseen, until
    its time.
22. **A clear** (1.8). From a clear's `time` to its state's `until`, its
    `blocks` are not drawn and take no room, and the blocks after them close
    up. None of those blocks was shown before the clear, and every fixed or
    pinned block holds its place (rule 19).
23. **A tight board** (1.8). With `tight` 1, the vertical gap between the
    board's blocks is halved. With 2, the blocks' own vertical padding is
    halved too. It applies to the whole board, from its start. With rules 19
    to 22, every block shown then lies inside the board, at phone-landscape
    and laptop widths.
24. **Relative and participle clauses** (1.9), more `clauses` parts:
    - A `defining` or `nondefining` part is a phrase already shown in its
      piece (its commas included when it has them). It takes its look from its
      reveal: the clause's magenta tint, with a dashed edge and coloured commas
      (non-defining) or a solid edge pinned at both ends (defining).
    - A `remove` part is a line under the pieces, its room reserved from the
      start, shown from its reveal. When `keeps` is true, `text` is on the
      green of "correct" with a tick; when false, on the red of "wrong" with a
      cross. From then the set-in clause is faded.
    - A `link` part draws, from its reveal, an arc over the words from the
      phrase of part `from` (the main clause's subject) to its own phrase,
      with a head.
    - A `dangling` part draws the same arc broken, with a red cross where it
      breaks.
    - The arcs are drawn over the board like marks (rule 19), measured from
      where the words are.
25. **A gloss** (1.10) is a block whose word shows from its reveal. Its parts
    (`meaning`, `picture`, `example`) are revealed by rule 5, each with its
    room reserved from the start. A `picture` part is the gloss's image.
26. **A gloss's image** (1.11). `image.file` is a transparent PNG, relative to
    the folder of `bundle.json` (`../images/<hash>.png`), the same file the
    block's `html` shows, with `image.alt` as its alt text. The player shows
    it from its part's reveal, with a short fade (none under reduced motion).
    The narration never points at it.
27. **A board's picture** (1.12) is a working block of type `picture` with no
    words: always the first entry of its board's first state's `working`. Its
    `image` is as in rule 26. It is drawn in a square box whose side is `size`
    cqh (20 when `size` is null), with the image fitted inside it. It is shown
    from its state's `start` (its time in the state's `reveal`) until the
    state is erased or a clear takes it, like any note (rule 22). No cue names
    it, and the narration never points at it.
28. **Nothing over anything** (1.12; no data). In every state, no block is
    drawn over another block or its text, and no text over other text, at any
    screen width. This covers a diagram's labels and a table's cells too. The
    engine checks it on every lesson at phone-landscape and laptop widths. A
    player that draws timelines from their data rather than using `html` must
    set marker labels that would meet on further lines under the axis, as the
    `html` does.

**A seek** shows the correct state for that moment at once, with no replay of
reveals, motion or typing.

## 3. Looks the player draws

The block `html` and `blocks.css` carry every block's own look. These are the
looks of what the player draws over time, and the colours a player needs if
it draws blocks from data.

### Colours

One meaning per colour, in every lesson. **Red and green mean only wrong and
correct**: nothing else uses them. Colour is never the only signal: a wrong
or correct mark also carries a cross or a tick.

| Colour | Meaning | Fill | Accent | Text on the fill |
|---|---|---|---|---|
| Red | wrong, error | `#FCEBEB` | `#E24B4A` | `#501313` |
| Green | correct, answer | `#EAF3DE` | `#639922` | `#173404` |
| Blue | teacher emphasis, typed answers, marks | `#E6F1FB` | `#185FA5` | `#042C53` |
| Amber | highlight over text, the spotlight's cell | `#FAC775`, translucent | | inherits |

Neutrals: body text `#2C2C2A`, secondary text `#888780`, hairlines `#E8E6DF`,
controls `#5F5E5A`. The board's background is white.

### Marks (rule 6)

A mark appears shortly before the word it belongs to; its `time` already
includes that lead.

| Mark | Look |
|---|---|
| `underline` | 2–3 px, blue, directly under the phrase |
| `highlight` | amber, translucent, never hiding the text |
| `circle` | a thin blue ellipse around the phrase (one to three words), stopping short of the nearest letter or digit on either side |
| `strike` | a red line through the phrase |
| `bracket` | under a span, blue, with end ticks |
| `arrow` | a thin blue curve with a head, from `text` to `to_text` |
| `replace` | the phrase struck in red, `with` written above it in a handwriting-style face (the only second typeface) |
| `point` | moves the reading pointer to the phrase, where it stays (rule 8) |

- A mark whose phrase wraps onto two lines is drawn complete on every line,
  never as two open halves.
- No mark touches neighbouring text.
- Marks belong to the working layer and disappear with it.

### Word-class colours (rule 15)

Text in the colour, on a soft tint of it:

| `cls` | Colour | Tint |
|---|---|---|
| `verb` | `#084191` | `rgba(8,65,145,.10)` |
| `noun` (also `noun phrase`) | `#916308` | `rgba(145,99,8,.12)` |
| `adjective`, `adverb` | `#1F7A73` | `rgba(31,122,115,.11)` |
| `clause` (also `phrase`) | `#CB0BAB` | `rgba(203,11,171,.09)` |
| `slide-underline` | an underline, max(2 px, 0.3 cqh) thick, offset 0.22 em; no colour change | none |

### Tense family colours (rule 7)

Only when `lesson.tense_colours` is true. Otherwise tense chips, timelines and
table headers are drawn neutral.

| `family` | Colour | Text on it | Accent |
|---|---|---|---|
| `past` | `#EF9F27` | `#412402` | `#854F0B` |
| `past_to_now` | `#1D9E75` | `#04342C` | `#0F6E56` |
| `now` | `#7F77DD` | `#26215C` | `#534AB7` |
| `future` | `#D4537E` | `#4B1528` | `#993556` |

### Spotlight and verdicts (rules 11, 18)

- **Spotlight:** the row in focus is at full strength, and the other rows are
  dimmed by opacity. The highlighted cell gets translucent amber. At the end
  of each row the whole table shows again, which is a `focus` entry with
  `row` null.
- **Verdicts:** a `wrong` cell is faded. A `right` cell gets a tick on the
  green fill `#EAF3DE`. A `possible` cell is unchanged.

### Clause diagram (rules 20, 24)

| Part | Look |
|---|---|
| `dependent` | a piece in magenta `#CB0BAB` on a pale tint, labelled "Dependent clause", with a tab on the side facing the other piece |
| `independent` | a piece in slate `#475569`, labelled "Independent clause", with a notch where a dependent piece joins it |
| `glue` | the joining word on orange `#F7A531`: a chip on the word inside its piece, or a bridge between two independent pieces |
| `subject`, `verb` | a small "S" (neutral) or "V" (verb blue `#084191`) above the phrase; the verb takes the verb blue |
| `join` | the tab slides across the gap into the notch; a dependent piece that comes first shows its comma; a bridge reaches out to both pieces |
| `nondefining` | set into the slate piece on the magenta tint, with a dashed magenta edge; its coloured commas are its edges |
| `defining` | set in the same way, with no commas, a solid edge and a slate pin at each end |
| `remove` | the line under the pieces: green with a tick when `keeps`, red with a cross when not |
| `link` | an arc over the words, with a head, from the subject to the participle |
| `dangling` | the same arc broken, with a red cross at the break |

### Reading pointer (rule 8)

A small round pointer that moves word by word along the text being read, in
time with the speech. It rests (hidden) when nothing is read or pointed at.

## 4. Word order and hooks

Cues and the reading pointer depend on these, whether the player shows `html`
as it is or draws the block from its data.

- **Word order.** A block's words appear in the order its `html` has them:
  - a term box: label, term, explanation;
  - a comparison: label, left, right;
  - a card: label, text;
  - a table: the header, then its rows;
  - a diagram: its label, its parts' labels in order, then each series legend.

  Badges, icons, chip labels and diagram glyphs are never text. They are
  drawn from attributes or CSS, so they are not counted as words (rule 8).
- **Hooks in the `html`:**
  - `data-id="<block id>"` on the block's element;
  - `data-part="<part id>"` on each diagram part;
  - on a core table: `data-row` on each body row, `data-col` on each cell,
    and `data-typed="<index in typed>"` on each typed part, holding its final
    text;
  - a typed part inside printed words (a gap) also carries the class `gap`.

## 5. Frame, motion and reduced motion

- **The frame** is a fixed 16:9 rectangle with a white background, never a
  scrolling canvas. All lesson content stays inside it. Every size in
  `blocks.css` is a share of the frame's height or width (`cqh`, `cqw`), so the
  frame must be a CSS size container, and its size must not depend on
  anything around it (rule 19). The reference layout gives the header about
  8% of the height, the board about 84% and the controls about 8%, with 5% of
  the width as a side margin. The page around the frame may have its own
  panels and controls; they never draw inside it.
- **Motion** is short and never lags the speech. In the reference player,
  blocks fade in (about 0.25 s) and diagram parts are drawn as a teacher
  draws: an arrow grows from its start to its head, a tick drops into place,
  the marks of an event series appear one after another (about 0.7 s at most
  for the whole series), a callout box opens and its pointer reaches the
  line, and a label writes itself in.
- **Under `prefers-reduced-motion`**, parts and images appear without motion
  or fade, typed answers appear whole at their cue, and the zoom and pan move
  without animation (rule 13).
