# 050 — The teal look: the owner's Canva patterns as the base of every board

Date: 2026-11-01
Status: **Accepted**: the owner's brief of 2026-11-01 ("Rebuild the boards of Word Order as a full lesson in a new
visual style, as the trial for all lessons"), given in chat with its rules and his reference images; how each
pattern is carried by the engine is the agent's under that brief (ADR 005).

## Context

- ADR 048 made board layout a design step and kept **style C as the base** (its decision 2): the white ground, the
  handouts' colours by meaning, the marker, the lift and the zoom. The owner reviewed Word Order's draft.2, redesigned
  under it, and rejected the result as routine: the boards still read as tables and cards in one neutral look.
- He then drew the look he wants in Canva: twelve pattern slides (`C:\OET\course\design-samples\canva\patterns\`,
  exported from his deck "OET Writing Lesson Boards") and five Word Order slides (`...\canva\word-order\`, "OET Word
  Order"). He likes patterns 1 to 11 and rejects 12 (a single rule in a large box). In his words: a teal brand base
  (#0b6e6d) with soft warm accents (amber, coral, soft blue, lilac), light, airy and uncluttered; rounded shapes,
  circles and pills, soft corners, no sharp blocks and no hard offset shadows; the teacher's hand (a handwriting face
  for his notes, red-pen circles and underlines around mistakes, sticky notes); the parts of a sentence colour-coded,
  each with a small label; diagrams, arrows, timelines, flows, columns and comparisons instead of plain tables; no
  large photographs or background images; motion in reading order and in time with the narration.
- The engine already separates the words from their look (ADR 042: the look is the lesson's `blocks.css`; ADR 048
  decision 8: a form is a layout in `style_c.py`, its rules appended only where used). The site plays a lesson's
  stylesheet as it is, scoped to its player (its ADR-0023 §4), and keeps any `data-*` attribute, class and simple SVG
  path a block carries (its sanitiser). So a new look needs no bundle change, provided it adds nothing the site's
  player must do.

## Options considered

1. **Re-tune style C's tokens for everyone.** Rejected: it would change all 28 built lessons at once, and their
   boards were not designed for the patterns; the owner asked for a trial on one lesson first.
2. **A new bundle style ("d")** the site would have to know. Rejected: a contract change on both sides for what is
   only a stylesheet.
3. **A look over style C, named per lesson, and the patterns as layouts** (chosen): `lesson.look` "teal" in a
   lesson's `analysis/sections.json` appends the look's rules after style C's; the eleven patterns are layouts
   (`block_layouts`) whose rules are appended only to a lesson that uses them. The bundle's format does not
   change (`style` stays "c"); every lesson without the look is byte for byte as it was.

## Decision

1. **The teal look replaces "style C stays the base"** (ADR 048 decision 2) for every lesson built or redesigned from
   now on: such a lesson sets `lesson.look` to `"teal"` (`style_c.look_of`; refused in a lesson not in style C, or for
   a look that does not exist). Style C's engine stays under it: the spotlight, the lift, the zoom, the marks, the
   effects and the bundle. Its rules (`style_c.LOOK_CSS["teal"]`; docs/02-DESIGN-SYSTEM.md §1b):
   - **Colour**: teal `#0b6e6d` and its ink `#173d3c` on a warm white ground `#faf8f4`; the accents amber `#e2a72e`,
     coral `#e57063`, soft blue `#9ecfd8`, lilac `#b8a6d6`, each with a soft tint; "right" is teal, "wrong" coral and
     red; the six criteria keep their colours (ADR 042).
   - **The teacher's hand**: a note written while teaching (a working `plain` note) is set in his hand, Caveat, at 1.3
     times body size (its x-height matches IBM Plex's at body size, §3); his advice (a callout) on a yellow sticky note
     in his hand, tilted 0.6 degrees; his marks in red pen: a **circle** is his red ring, an **underline** and a
     **strike** his red line; the marker stays amber. The board's own sentences stay in print.
   - **Rounded and soft**: pills, circles, radii of 2.2 to 2.8% of the frame; only soft, low shadows.
   - **The contents board** is a path of numbered circles in turn's colours, joined by a teal line (pattern 10, set
     vertically).
   - **Motion** (§8g): a fixed block enters as its board opens; a pattern's pieces (rows, tiles, pills, steps) enter
     in reading order, 70 ms apart, each in 0.4 s; never under reduced motion, never in a measuring check. The
     narration's own reveals, typing and marks keep their times.
2. **The eleven patterns are layouts** (`style_c.LAYOUTS`, `ADR050_LAYOUTS`; docs/02-DESIGN-SYSTEM.md §7k), each
   parameterised by the table it draws (its columns, its rows, its header) and nothing else:

   | Pattern (the owner's slide) | Layout | Draws |
   |---|---|---|
   | 1 Wrong and right | `wrongright` | a table of two columns: the wrong sentence in plain ink, a curved red-pen arrow, the right one in bold teal |
   | 2 A colour-coded sentence with labels | `coded`, `opener` | the parts as coloured tiles, each under a pill of its label; or a sentence's kind, its opening phrase in a tile of that colour, then the rest |
   | 3 A timeline with rounded markers | `timeline` | each row a round marker in its colour on a teal line, its words and a handwritten note under it |
   | 4 Keep, shorten or leave out | `columns` | two to four rounded columns under solid pill heads, their cells soft pills of the same colour |
   | 5 A letter skeleton with labelled parts | `parts` | the letter one sheet with a teal edge, each part's name a pill in its colour joined to its paragraph; a part not written out as grey lines |
   | 6 Key tips as round badges | `badges` | each point a solid circle with a handwritten note under it; a recap's category cards as badges side by side |
   | 7 A paragraph on ruled paper, red pen, a sticky note | `ruled` | the lines on ruled paper with a red margin, in a learner's hand, their numbers in the margin (the narration's pen marks the errors, the callout is the sticky) |
   | 8 Before and after with word counts | `beforeafter` | two panels, coral and teal, each sentence with its word count in a circle (counted from its words) |
   | 9 A gap with choice pills | `choices` | short phrases as solid pills in turn's colours, under their labels or the bank's name in the hand |
   | 10 Numbered steps on a curved path | `path` | numbered circles alternately low and high on a teal curve (an empty drawing, never a word) |
   | 11 Two letters compared | `compare` | two things side by side, framed in teal and coral, each head (a comparison's words up to the first colon, or a column's label) a pill |

   As every layout (§7j): presentation only; the words, their order, the ids, cues and states never change
   (`layout_html` checks it); a counted number, a label drawn from a header, a step's number and the curve are drawn by
   the stylesheet from attributes, never words.
3. **Variety is the rule** (ADR 048 decision 4, kept and made concrete): every lesson uses a varied mix of the
   patterns; no two boards in a row share a pattern (the title, contents and closing boards count); a pattern may
   vary its arrangement between lessons (the path set vertically on a contents board, the columns two or three wide,
   the badges in a row or as recap cards). Each board's pattern is logged in the lesson's decision log with the slide
   it follows, and the contact sheet and critique of ADR 048 decision 6 check it.
4. **What stays**: dense content on one board (ADR 011); a phone can read every board (the fit, the small phone frame,
   the guard, §8b); the paper is never hidden and keeps its forms (`paper`, `place`; ADR 045); a pop-up is never
   covered (ADR 046); no decoration: a small clean illustration only where it explains (ADR 021). The rejected pattern
   12 is not built.
5. **The hand on the site.** The reference player embeds Caveat from a pinned, hash-checked local copy
   (`spike/fonts/caveat.lock.json`), as it does IBM Plex Sans. The site's policy allows fonts only from itself
   (`font-src 'self'`), so a font in the lesson's stylesheet cannot load there; until the site serves Caveat (as it
   serves Plex, its ADR-0030) and names it `--font-hand`, its player draws the hand in the device's own (Segoe Print,
   Bradley Hand, then the cursive face). This is the one place the site's draft differs from the reference player.

## Consequences

- **No built lesson changes**: a lesson without `lesson.look` takes none of the look's rules, and a layout's rules
  reach only a lesson that uses it. Proven by the render comparison of every built lesson before and after the change
  (runbook, "Changing shared code"; `render_compare.py` snapshots `before-adr050` and `before-adr050r` on main at
  7247039, `after-adr050` and `after-adr050r` on this change, 2026-11-01): **28 of 28 identical**, 850 data files byte
  for byte (bundles, texts, stylesheets, timelines, fits) and 167,252 moments at the phone and laptop frames drawn
  identically, with no board timing difference. Reading 5 is outside the proof, as it was for ADR 049: it does not
  render on main (its closing audit fails because Writing 5 and 7 share its goodbye "Well done.").
- Word Order (writing-06-word-order) is the trial: every board redesigned with the patterns, its narration, audio and
  practice points unchanged, a side-by-side PNG of each board with the pattern it follows in
  `C:\OET\course\design-samples\word-order-v2\`, and a new draft on the site. The other lessons move to the look when
  the owner has seen it.
- **Not done here, for the owner**: (a) the pen circle is drawn whole at its time, not drawn on in motion: a mark is
  redrawn by both players on every frame, so a drawing-on needs a change to each player's mark code (rule 53, the
  marker sweep's way) and to the site; (b) the site does not serve the hand yet (decision 5); (c) the display face
  of his slides (a wide geometric sans) is not used: titles stay in IBM Plex Sans, the site's face (the owner
  agreed, 2026-11-01).
- **Asked of the site** (2026-11-01, label from-lesson-engine): siamingit/oetacademy-web#227, serve Caveat as
  `--font-hand` (a font is not a media type the package contract allows, and `font-src 'self'` refuses a `data:`
  font); siamingit/oetacademy-web#228, draw a circle on in motion in a lesson whose `lesson.look` is "teal" (0.4 s
  from the mark's time, rule 53's way), with the data the engine would send.
- To reverse: remove `lesson.look` from a lesson (its stylesheet returns to style C's); remove the look and the
  layouts from `style_c.py`. No lesson built before this record changes either way.

## Amendment (1), 2026-11-01: readable on a phone (the owner's review of Word Order draft.3)

The owner liked the look of draft.3 and found many graphic and layout faults, and text too small to read. His brief
(2026-11-01, in chat) set seven general rules, to be recorded here and in the design system and checked on every
board, and a fix for boards 02, 04, 06, 07, 10, 12, 13 and 15.

**The rules** (every lesson in the teal look; docs/02-DESIGN-SYSTEM.md §7k, "Readable on a phone"):

1. **Minimum text size.** In the 1600x900 frame, running text at least 26 px and a label at least 20 px, so it stays
   readable on a phone. Where content does not fit at that size the layout changes (two columns, fewer lines shown,
   the spotlight); the text is never set smaller.
2. **The hand only for short notes.** The handwriting face only for the teacher's short notes (about 15 words at most)
   and labels; learner sentences, letters and paragraphs in print, with the red pen's marks on top.
3. **No illustration unless it explains the point.** This replaces ADR 021's "a picture on every board" for a lesson in
   the teal look: a board has a picture only where the picture explains.
4. **Use the frame.** No board with a large empty half: the content sized up, or the space used for the example the
   narration gives.
5. **Dimmed rows stay readable.** A row the spotlight is not on keeps a contrast of at least 4.5:1: it is dimmed by a
   lighter ground, never by greying its words out.
6. **A mark never hides its words.** An underline below the words, a circle around them; never a band across words
   on a coloured tile.
7. **No orphaned heading words.** A heading never wraps with one or two words alone on a line.

**How the engine carries them** (`style_c.py`, the look's rules appended after style C's; the layouts' rules outranked
by writing each under `.frame`):

- (1) a table is never set under 2.9% of the frame (26 px), whatever the fit chose; labels at 2.4% (21.6 px); the fit
  (`fit_boards.py`) takes 2.9% as a teal lesson's table floor (1.9% for every other lesson, unchanged), so a board
  that does not fit has its notes cleared or is reported unfit instead of shrinking. A long letter on its parts
  (`parts`, more than 700 characters) flows in two columns of one sheet, each part's name a pill at its paragraph's
  start (`data-flow="2"`). The paper and the letter beside it are set at 3.5% (a sheet at 3.8%), in ink.
- (2) `layout_html(..., look)`: in the teal look a plain note, an advice note or a recap card longer than 15 words takes
  `t-print` and is set in print; the ruled paper's paragraph (pattern 7) is in print.
- (3) a lesson's own `analysis/pictures.json` (the briefs kept under `removed`).
- (4) the contents board in two columns over the whole board; the coloured parts (pattern 2) as large tiles; the
  choice pills larger; a note and the word card it brings side by side.
- (5) the spotlight's half opacity is replaced by a wash of the ground (60%) over the cells not lit; their words keep
  their colour; words on coral in the darkest ink (#0c2524), the pen's red deepened to #c4362f (5.1:1 on the ground).
- (6) per lesson, as before, by cue overrides (a marker band on a solid tile becomes the pen's circle or line).
  `write_narration.py`: an utterance override may also add a phrase mark where the voice names it, its spoken words
  unchanged (so no clip changes), every existing cue marker kept in order.
- (7) `text-wrap: balance` on headings, table heads, comparison heads, card heads and contents titles; recap badges
  large enough for their heads.
- Pattern 11 as a table (`compare`): two cards side by side (teal and amber), each its place's head, its example
  sentences one under another with the words in that place ringed in the pen (`block_accents`, now drawn by `compare`
  as well as `skeleton`), and in its last row the rule in the hand (the owner's Word Order slide 3). Pattern 8's word
  counts in larger circles (12.4% of the frame, the count at 5%).

**The check.** `spike/scripts/check_text_size.py` (the readability check) drives the player to every moment a board
changes at the 1600x900 frame and fails any text under its minimum (a hand line counted at its size / 1.3), any line of
text under 4.5:1 against what is drawn behind it (every opacity and wash counted), any wrapped heading with a line of
one or two words, and any board that at its fullest leaves more than 40% of its height or width empty. The runner runs
it on the silent preview and on the player of every lesson in the teal look, after the wide-font check (the owner:
"check them on every board").

**The public course index** (`build_public_course_index.py`) now also leaves out a line that quotes eight words in a
row of the lesson's own samples (its papers, model letters and keys, read from the private exercises repository): board
10's sticky note puts a model letter's sentence right, and a board's rules are listed in the index. Six words of a sample
are too common to tell ("in the task and the plan"); eight is the release check's length for a transcript. No other
lesson's entry changes.

**Consequences.** Only a lesson in the teal look changes (the look's rules, the ADR 050 layouts and the teal fit floor
reach no other lesson). Proven by the render comparison (runbook, "Changing shared code"): `render_compare.py`
snapshots `after-teal2` and `after-teal2r` on this change against ADR 050's `after-adr050` and `after-adr050r` (main's
code is unchanged since them and no lesson file changed, 2026-11-01): **27 of 27 other lessons identical**, 820 data
files byte for byte and 165,020 moments at the phone and laptop frames drawn identically, with no board timing
difference; Word Order differs, as intended. Reading 5 is outside the proof, as before (it does not render on main). Writing 6 is rebuilt as
draft.4 under these rules; its narration, audio and practice points are unchanged (95 utterances, every spoken word
the same as draft.3).

## Amendment (2), 2026-11-01: what the site's player does with a lesson, and the owner's addendum

**What happened.** Draft.4 passed every engine check and was unreadable on the site: the boards shown whole drew their
tables at a quarter of their size and the contents ran off the board. The engine's checks run on its reference player;
the site plays a lesson with its own (siamingit/oetacademy-web, `packages/lesson-player`), and three of its rules differ
in effect (read in its code at b08a7a7, and reproduced by rendering draft.4 with that player locally):

1. **Its guard measures a board while it enters.** The teal look's pieces rose into place from 1.6% of the frame below
   (`translateY`); during that, a table's rows lie outside its block, and the guard treats a block whose content runs
   outside it ("spills") as a board that does not fit at any size. On a board shown whole (rule 52) its search then
   runs to its floor, a quarter of the board's size. (The reference player's measuring runs without animation.)
2. **The hand is not served there** (#227), and the device's hand (Segoe Print on Windows) is taller than Caveat: at the
   look's fixed line height a note's words ran outside its block, the same spill.
3. **Its own rules come last.** The site puts the lesson's stylesheet inside `.oa-lesson`, in the cascade layer
   `oa-lesson` below the player's own rules, so a property the player sets (on `#cam`: display, direction, wrapping,
   gaps; on a tight board's table: its padding) cannot be changed by the lesson, whatever its specificity, while on the
   reference player a more specific lesson rule wins. The contents' two-column grid on `#cam` therefore never applied,
   and the contents' line, drawn past each item, was another spill.

**Decision (engine side, bundle 1.23 unchanged).** (a) A teal piece enters by growing from 97% of its size inside its
box (`scale`, top-anchored), never by moving from outside it; a fixed block from 98%. (b) Every line in the hand takes
the line height of the face that draws it (`normal`), and the hand's fallbacks start with Ink Free, the most compact
handwriting face Windows ships. (c) The contents in two columns by the items' own widths and `order` (read down the
first column, then the second), its line drawn inside each item; nothing sets a property of `#cam`. (d) The tilted
sticky note keeps clear of the board's right edge. (e) No rule of the look may rely on overriding a property the site's
player sets (the list is the site's `player.css`). (f) **Required check:** `check_site_player.py` plays the package
with the site's own player and fails on a spill, a board the site draws smaller, or text under the minimum or 4.5:1
(runbook step 18c); its screenshots go beside the engine player's in every report, and `publish_lesson.py
--release` (draft or final, every lesson) refuses a package the check has not passed on, at every state, byte for byte
(its bundle and stylesheet).

**Proof.** Render comparison `after-teal3`/`after-teal3r` on this change against ADR 050's `after-adr050`/`after-adr050r`
(no lesson file changed since): **27 of 27 other lessons identical**; Word Order differs, as intended. Writing 6 draft.5
on the site's own player: 66 of 66 states pass.

**The owner's addendum (2026-11-01), rules for every lesson:**

1. **One face per set of equals.** Items side by side as equals (recap cards, columns, pills, steps) use the same face,
   size and weight: print for a set when any item is longer than a short note, the hand only when every item is one.
2. **Headings and labels in coloured rounded boxes**, as in the owner's Canva samples: the title board's title in a
   teal band and its opening lines each in its own box (the link to the earlier lesson and the lesson's topic on a soft
   blue, the problem from a letter on white with a coral edge, the description on soft teal); the paper's labels
   ("Mrs Holden's paper", "Her letter") as solid pills, its row labels ("Notes:") on soft teal; WRONG and RIGHT, AS
   WRITTEN and PUT RIGHT as solid pills or panels; the comparison's heads as boxes inside their cards; the board's
   title in a soft teal band in the header. The look's colours, rounded corners, 4.5:1 and the minimum sizes hold.
3. **A board's content uses the board** (rule 4, applied to the paper alone: a sheet at 4.5% of the frame).

## Amendment (3), 2026-11-01: Writing 7 in the teal look (the owner's ISBAR and Request boards; a path and a timeline that use the board)

**Context.** The owner's brief of 2026-11-01: redesign every board of Writing 7 (Organising the Letter) in the teal
look, as Word Order was; its ISBAR board and its Request board are his own designs (ADR 049: `acronym`, never zoomed;
`skeleton`), to be kept and only brought into the look. Built under amendments (1) and (2), four things in the shared
code fell short: the two ADR 049 layouts had no rules in the look (they drew in style C's amber and cream); the
`path` (pattern 10) set its handwritten notes at 23.5 px, under rule 1's 26 px, and like the `timeline` (pattern 3)
left most of a board empty (rule 4); the timeline's markers are 13% circles that clip anything longer than a number
("15 to 21 October"), and a lit marker in teal turned white on the spotlight's yellow (1.15:1); the criterion's
monogram ("O&L") was a 17 px label; and the contents title "The request and closing paragraph" (five words) wraps
into a line of two words at the contents' size (rule 7) whatever its balance.

**Decision** (`style_c.py`; bundle unchanged; no rule reaches a lesson that does not use what it draws):

1. `layout_css(blocks, look)`: in the teal look, a lesson that uses `acronym` or `skeleton` also takes
   `acronym_teal` / `skeleton_teal`. ISBAR: each part a white band, its letter large and bold on a solid rounded tile
   in its colour in turn (pattern 2's amber, blue, lilac, coral, teal), the name bold beside it, the heads as pills.
   The letter skeletons: two white sheets framed in teal and coral (pattern 11), their names as pills (the first cut
   inside the gap its cell carries), a paragraph not written out as pattern 5's grey lines, the purpose words and the
   request expanded at the end in the Purpose colour (ADR 049, unchanged).
2. The `path`: larger circles on a taller curve, the step at 3.6% and the note in the hand at 3.9% (27 px counted);
   five steps or more keep the first geometry with the words at their minimums. The `timeline`: a marker longer than a
   number is a pill; a lit marker keeps its colour, ringed; four markers or more read down the board, each on a teal
   line beside its words (the pattern set vertically, as the contents path is; decision 3: a pattern may vary its
   arrangement).
3. `crit_teal`, emitted in the teal look where a criterion's card is used: the monogram in a larger circle, at 2.5%
   for three letters (22.5 px).
4. `ct-one`: in the teal look, a contents title of five words or fewer and more than 28 characters takes the class,
   and a contents board that has one sets every title one step smaller (3.5%, one size for the set: the owner's
   addendum, rule 1) with smaller circles, so the title keeps its line. No built lesson's title but Writing 7's is one.

**Consequences.** Only Writing 7 changes: it is the one built lesson that uses `acronym`, `skeleton`, `path` or
`timeline` as a table layout, a criterion card in the teal look, or a long contents title in the teal look.
Proven by the render comparison (runbook, "Changing shared code"): `render_compare.py` snapshots `before-w07t` on main
at 16d44a8 and `after-w07t` on this change, 2026-11-01, Writing 7 as it stands before its redesign (no look): **28 of 28
built lessons identical**, 850 data files byte for byte and 167,268 moments at the phone and laptop frames drawn
identically, with no board timing difference. Reading 5 is outside the proof, as before (it does not render on main).
Writing 7 is then rebuilt in the look: every engine check, the readability check (0 findings) and the site's player.

**On the site's player** (the same day, check_site_player.py on Writing 7's draft package): the site's guard counts
every note of a state from the state's start and has a shorter room than the reference player, so two boards were
drawn smaller there: the letter skeletons (0.98) and the paper beside a long letter, Mr Talbot's three requests (0.94).
(5) In the teal look, a letter of more than 330 characters beside its paper (`PAPER_LONG_CHARS`, the third column)
takes `paper-long` and is set, with its paper, at 3.3% of the frame (29.7 px, over rule 1's 26 px) instead of the
look's 3.9%; its rule is emitted only where used. Today only that board: every other built letter beside its paper is
shorter in a teal lesson (Writing 3 has a longer one, outside the look). (6) The skeletons' grey lines a little closer
and their sheets' top and foot a little tighter. The check also took the lesson's oldest draft package when a released
v1 kept its draft folder (fixed in its own pull request: the newest draft).
Proven by the render comparison: `before-w07s` (main's code) and `after-w07s` (this change), 2026-11-01, with Writing 7
in the teal look: **27 of 28 other built lessons identical** (823 data files, 164,110 moments), no board timing
difference; Writing 7 differs, as intended (its stylesheet, bundle and text: 7 files, 308 moments of boards 07 and 20).

## Amendment (4), 2026-11-01: long pieces fit without shrinking (Writing 5's redesign)

**Context.** Writing 5 (Information Flow) was redesigned in the teal look under the owner's brief of 2026-11-01 (Word
Order as the model). Its readability check (`check_text_size.py`) on the silent preview found two places where a
pattern or the paper could not be drawn at rule 1's sizes, so the player's guard shrank the whole board (a third, the
path's and the timeline's notes in the hand, was put right by amendment (3) the same day):

- a table of a label and its words with nine rows (the nine families of signal words) in `columns` was taller than
  the board at the look's table floor;
- the look's paper sheet is set at 4.5% of the frame (the owner's addendum (3): a sheet uses the board). That suits a
  short piece of the paper. A page of eight dated entries, with the note under it, cannot fit at that size.

**Decision** (rule 1: where content does not fit, the layout changes and the text is never set smaller):

1. A table of two columns and eight rows or more in `columns` is drawn in two halves side by side, read down the first
   half and then the second (`data-flow="2"`). Each row keeps its label and its words, the label column at 30% of its
   half. The columns' names are not drawn, because the labels name each row.
2. A sheet of the paper with six rows or more, in a lesson in the teal look, takes the fit's size and is never set under
   the look's table floor of 2.9% (`data-long`). A shorter sheet stays at 4.5%.
3. The paper beside the letter at the long letter's size (amendment (3)'s `paper-long`, 3.3% of the frame, 29.7 px),
   **chosen for a block** with the layout `paperlong`, in the teal look only. The site's player has a shorter room than
   the reference player. On Writing 5's draft package (`check_site_player.py`) four boards were drawn at 91 to 96%:
   each is a paper beside a letter whose paper and letter together run past 330 characters. Those boards are named, not
   matched by length, because a rule on that length would also reach Writing 6's and Writing 7's built boards.

Each rule is written only into a lesson that has such a block: the attribute is set by `layout_html`, and
`layout_css` appends `columns2`, `sheetlong` or `paper_long` only where it finds one. No other lesson's bundle or stylesheet changes,
Word Order's included.

**Consequences.** No other built lesson changes. Proven by the render comparison (runbook, "Changing shared code"): `render_compare.py` snapshots `before-w5p` and `before-w5pr` on main at 8ea1f17, then `after-w5p` and `after-w5pr` on this change, 2026-11-02: **27 of 27 other built lessons identical**, 820 data files byte for byte and 163,572 moments at the phone and laptop frames drawn identically, with no board timing difference. Word Order and Writing 7 are among them. Reading 5 is outside the proof, as before. Writing 5 is outside it as well: it is the lesson this change is for, and it names `paperlong`, which main's code does not have. No other built lesson has a block any rule reaches: Writing 7's sheets have three rows, its `columns` table five, and no lesson but Writing 5 names `paperlong`. An earlier form of the change, without `paperlong` (on main at c9ffabd, Writing 5 not yet redesigned), was proven the same way: 28 of 28 identical.
Writing 5 is redrawn under these rules. On the engine's player the readability check finds 0 findings in 356 moments; on the site's player `check_site_player.py` finds 0 failures in 112 moments.