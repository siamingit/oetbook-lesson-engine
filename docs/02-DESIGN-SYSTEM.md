# Design System — Lesson Screens

How a lesson screen looks and behaves. Binding for every lesson.

Agreed with the maintainer against worked examples from Grammar 1,
reviewed at desktop and phone width. Revised 2026-09-23 after the first
build produced sixteen titled screens for one topic and the maintainer
identified the layout model as wrong.

This document covers the teaching surface only. Product brand, name,
domain and logo are not decided and **never appear on lesson screens**.

**Two looks** (owner, 2026-10-26; docs/adr/042-style-c-and-motion.md). Writing 2 and every
lesson built after it are drawn in **style C, "soft notebook"** (§1a) with its board layouts (§7j)
and its motion (§8g), as revised at the owner's review of Writing 2 the same day; a
lesson is in style C when its `sections.json` says so (`lesson.style` "c"), and a lesson config
made from 2026-10-26 on is written with it. The 22 lessons published before it keep the look
they were built in, which the rest of this document describes where style C does not change it;
restyling them is the owner's later decision. Where a rule below differs between the two, both
are given.

---

## 1. The frame

- **Fixed 16:9.** Never a scrolling canvas.
- Fills the viewport in fullscreen. On a phone: landscape.
- All content sits inside the frame. No side panel, no board beside the
  slide, nothing outside it.
- This governs the **lesson frame itself**. The website page around the
  frame may have its own panels and controls (contents, progress, resume,
  an AI chat); they are the page's, not the lesson's, and never draw inside
  the frame. Clarified 2026-09-24 (docs/00-PRODUCT.md §1,
  docs/04-LESSON-BUNDLE.md).
- Background: **white**, the header and the board too, in every lesson (style C's lilac ground
  was dropped at the owner's review of 2026-10-26, §1a, to match the site).
- Mood: **clinical and precise, and visually rich**. Calm, uncluttered,
  never playful. Colour, badges, cards and timelines are used freely,
  and **colour always carries meaning**: nothing on a board is
  decoration. Revised 2026-09-23, approved against a mockup, to bring the
  boards closer to the instructor's original decks.

### 1a. Style C, "soft notebook"

The owner's choice of 2026-10-26 (issue #46; ADR 042), for the contents board and every teaching
board of Writing 2 and every lesson after it, and, from 2026-10-27, of the 22 lessons published before
it (ADR 043: phase 1, the general look; the per-board layouts of §7j follow lesson by lesson), **revised the same day after his review of Writing 2**
(ADR 042, amendment of 2026-10-26 (2)): a white ground, the handouts' colours by meaning, the marker
behind the words, a lift with a soft neutral shadow and no outline, and board layouts drawn from his
own slides (§7j). Warm and varied, like the handouts on the site, never playful. Pixel values are at a
720 px frame; the stylesheet sets them as shares of the frame (§4): 6 px is 0.8% of its height, 16 px
2.2%, 20 px 2.8%, 24 px 3.3%, 44 px 6.1%. The values live in `spike/scripts/style_c.py` (`CSS`, and the
colours `RIGHT`, `WRONG`, `GLOSS`, `MARK`, `CRITERIA`), appended to the lesson's own `blocks.css`.

| Role | Value |
|---|---|
| Ground | **white**: the frame, the header band, the board and the controls (no lilac ground, to match the site's theme). Cards and rows are told apart by their soft tints and their spacing |
| Ink | `#1c1733`; muted `#4a4466` / `#6b6585`; faint `#a49fbc` |
| Notes | a soft neutral tint `#f3f4f7`, radius 16 to 24 px (rows 16, cards 20, big panels 24), **no borders, no left-border cards** |
| The board's own sentences (a slide's sentence, a fixed sentence, a letter, case notes) | paper `#f8f4ec` |
| A document (a Reading text, a Listening transcript) | a page on paper `#f8f4ec`, its paragraphs with no rule between them, with no room added around it (its text takes no more lines than before; on a question board the column's notes keep a small padding and a word card no "Word" chip); the paragraph being taught keeps the paper and is shown by the spotlight and the lift, so a keyword pair's colour is the same on the text as on its question (ADR 043) |
| A table | a **solid header row** in the colour of its section's criterion (ink `#3d3a52` in a section that is not a criterion), **white words** in sentence case; **tinted body rows** in that colour's soft tint |
| A tense family's colour | kept: a table's header cell in a tense family's colour (Grammar 1's summary table) keeps it (§5a; ADR 043) |
| Right or keep | olive `#556b00` on `#eef3d2`, with a tick ✓ (the handouts' "modal" tone) |
| Wrong or leave out | red `#b42318` on `#fdecea`, with a cross ✕ (the site's danger); struck through in `#b42318` as it is named (§8g) |
| A word card, "Meaning", "Word", the key word | the handouts' gloss amber: `#8a5300` on `#fdf0d5`; a small "Word" chip in `#8a5300` with white words |
| Marker highlight (key words) | a light amber band `#ffe19c` behind the lower 38% of the line, `linear-gradient(transparent 62%, #ffe19c 62%)`, multiplied with the words so the letters stay as dark as they are (§8) |
| The six criteria | each its own colour and its monogram in a circle, as on the owner's slides (table below) |
| Number badge | a 44 px circle: on the contents board a criterion's number in its colour with white words, the others in ink on white; a cross or a tick in the red or the olive |
| Small chips | a note's tag on `#e6e5ee` in muted ink; the criterion's tag on white in the criterion's colour |
| Type | IBM Plex Sans (the site's font), 400 to 700: titles and badges 700, terms and labels 600 or 700, text 400 |
| Lift | only on the active element (a row, a tile, a card or a block being taught, §8g): a soft neutral shadow `0 6px 20px rgba(20,32,31,0.12)` and a very small scale (0.4% for a full-width row, 1 to 2% for a tile, card or contents item), inside the table's or the board's edges; **no outline**. A lifted row lifts as one row: its cells keep their own tints, nothing is repainted |

**The six criteria's colours** (used the same way everywhere in a lesson: the criterion's card, its
section's tables and tints, its contents item, its tile; the monogram is the non-colour signal):

| Criterion | Monogram | Ink / soft tint | From |
|---|---|---|---|
| Purpose | P | `#1d5fb4` / `#e2eefb` | the handouts' blue ("past") |
| Content | C | `#be185d` / `#fce7f1` | the site's rose |
| Conciseness and Clarity | C&C | `#0f766e` / `#d7f0ec` | the handouts' teal ("teach") |
| Genre and Style | G&S | `#9d1f8f` / `#fbe7f6` | the handouts' magenta ("prog") |
| Organisation and Layout | O&L | `#0e4a55` / `#dcecef` | the site's band teal |
| Language | L | `#5b3fc4` / `#ece6fb` | the handouts' violet ("test") |

Chosen by measured difference (CIEDE2000), as the word classes were (§7c): the six that differ most
from each other (15.7 or more) and at least 20 from right, wrong and the gloss amber. The handouts'
"practice" red (4.1 from wrong), "pf" brown (8.5 from the gloss amber) and the site's success green
(15.1 from the olive of right) are not used. A section is a criterion's when its title is the
criterion's name (`style_c.CRITERIA`); a term box labelled "The criterion" in it is drawn as the
criterion's card.

**Colour still carries meaning** (§5): olive = right or keep, red = wrong or leave out, amber = a
word card or the key word, and each criterion its own colour. A cross or a tick still goes with every
wrong or right sentence (colour is never the only signal). A callout's warning takes the red badge, a
key rule the amber one.

**Right no longer collides** (the open item of ADR 042, settled at the owner's review): the olive of
right is 26.8 from the adjective's word-class teal, 26.2 from the "up to now" tense teal and 21.3 from
its accent (§7c asks 20). What remains: the teal of Conciseness and Clarity is 1.8 from the adjective
teal and 17.2 from the "up to now" teal, so the structural check fails a lesson that draws the
criteria's colours together with an adjective or adverb word mark or tense colours.

**What stays**: the 16:9 frame, its bands and margins; one board per topic, several per section; the
section title alone in the header; the board style's kinds of content (§7c) and their flows; every
size as a share of the frame, with its floors; nothing moves a word, every block fits, nothing over
anything (§8a, §8b, §8d).

### 1b. The teal look (ADR 050)

The owner's Canva patterns of 2026-11-01 (`C:\OET\course\design-samples\canva\`), the base of every lesson
built or redesigned from that day: a lesson names it in `analysis/sections.json` `lesson.look` ("teal"), and its
`blocks.css` takes `style_c.LOOK_CSS["teal"]` after style C's rules. Style C's engine stays under it (the spotlight,
lift, zoom, marks, effects and the bundle); a lesson without the look is unchanged.

| Role | Value |
|---|---|
| Ground | warm white `#faf8f4`: the frame, header, board and controls; white cards and paper on it |
| Brand and ink | teal `#0b6e6d`; ink `#173d3c`, muted `#536866` |
| Accents (in turn: a part, a row, a pill) | amber `#e2a72e`, soft blue `#9ecfd8`, lilac `#b8a6d6`, coral `#e57063`, teal; each with its soft tint (`#fbf0d5`, `#e1f1f4`, `#eee8f6`, `#fce7e3`, `#e5f0ef`) |
| Right, wrong | right teal; wrong coral and red (`#b8352a` ink); the six criteria keep their colours (§1a) |
| The teacher's notes | a working note in his hand, Caveat 500, at 1.3 times body size (its x-height matches IBM Plex's at body size, §3), no card, in ink |
| His advice | a callout on a yellow sticky note `#f7e27f`, soft corners, tilted 0.6 degrees, in his hand |
| His pen (§8) | a circle is a red ring `#cf3f3f`; an underline and a strike a red line; the marker stays amber |
| Shapes | pills and circles; radii 2.2 to 2.8% of the frame; only soft, low shadows; never a hard offset shadow |
| The contents board | a path of numbered circles in turn's colours, joined by a teal line (the owner's pattern 10, set vertically) |
| Motion (§8g) | a fixed block enters as its board opens; a pattern's pieces enter in reading order, 70 ms apart, 0.4 s each |
| The board's own sentences, titles | IBM Plex Sans, as in §1a (the site's face) |

The hand is embedded in the reference player from `spike/fonts/caveat.lock.json`; the site does not serve it yet
(its policy loads fonts from itself only), so its player draws the hand in the device's own until it does (ADR 050
decision 5).

### Vertical division

| Band | Height | Contains |
|---|---|---|
| Header | ~8% | The section title, and nothing else |
| Content | ~84% | The board |
| Controls | ~8% | Play/pause, progress, elapsed time |

The header is deliberately small. The student reads it once; they look
at the content for minutes.

### Margins

5% of frame width on each side. Phone screens have rounded corners and
intrusions; content must not sit at the edge.

---

## 2. The board — the central model

**A lesson is a sequence of boards. One board per topic, several boards
per section.** A board has no title: the header shows the section it
belongs to (docs/00-PRODUCT.md §1, lesson structure).

A board is what the original slide was: a stable surface the teacher
works on, and keeps working on, for as long as that topic lasts. It is
not a page that fills up and gets replaced.

Getting this wrong produces a lesson with a new title every thirty
seconds and a student who cannot tell where they are.

### Two layers

```
FIXED LAYER      the topic's own content
                 written once, stays until the topic ends

WORKING LAYER    notes and marks the teacher adds while explaining
                 accumulates, is erased, accumulates again
```

**The fixed layer** is the equivalent of the slide. On an exercise
topic it is the sentence under discussion. On an explanatory topic it is
the table, the forms, or the examples the topic is about. It is authored
once and **never erased while the topic is active**.

**The working layer** is everything the teacher adds while talking: a
side point, a definition, an alternative answer, an underline, a written
example. These are transient by nature. They appear, they do their work,
and they go.

### Erasure

When the working layer fills the space available, **the working layer is
erased** and filling continues in the cleared space.

- The fixed layer is untouched. The title does not change. The topic
  does not change.
- Erasure is an event in the lesson, like a cue. The narration knows it
  happens.
- Erasure is not a failure of planning. It is how a teacher uses a
  board, and the source lessons do it constantly — one recording showed
  fifteen distinct erase moments, one clearing 134 marks at once.

### Boards end with topics

A board ends when its topic ends. Never before, never for reasons of
space.

### The header

For every board in every lesson, the header shows **the section title and
nothing else**: the heading of the original slide, corrected for deck
defects. No board title, ever; no topic number. An exercise board
identifies itself by the item badge on its sentence. Recorded 2026-09-23
after the five boards of page 13 each took their own title, when they are
one section: "Verb tense - Error correction".

### Boards per section

Decided by the maintainer 2026-09-24, replacing the earlier "three to seven
topics per page" rule. A slide stays as it was unless it is too heavy; notes
are written in the free space and erased when it fills; a new page is never
brought, so the main content does not change.

- **One board per original slide**, and one per authored section (ADR 018). Teaching beats become working-layer
  states with erasures, never boards.
- **Exception, exercise slides:** an introduction board showing all the
  items, then one board per item, as on page 13.
- **Exception, oversized fixed content:** a board is split only when its
  fixed content cannot fit the frame at phone-landscape width, and then
  **by meaning** (past / present / future), never by beat. **A table is
  never split** (§7, Tables; 2026-09-25): it stays whole on one board and
  is read with row focus and auto zoom. Grammar 1's split tense table was
  built before this rule and is kept as accepted. **One exception** (ADR 045 amendment (1)): a table
  that cannot be read whole at body size may be divided by its rows over a declared split, each part a
  table alone; the split is judged at body size and stands only where the table is oversized there.

**A short list fits on one board** (owner, 2026-10-26; ADR 042). A list of up to about ten items,
such as a lesson's contents (up to 12 parts), is on one board, in two columns if needed, and is never
cleared to make room. In style C the contents board is two columns of tinted rows beside the board's
picture (the whole board where it has none); an item that lists two or more of its category's sections
sets them one under the other under the category's heading (ADR 043: the sections the narration names,
13 to 17 in five lessons, all on the one board). The screens stage (`build_lesson_boards.py`) fails a style C lesson with more than 12 parts
(group its sections into categories); the structural check (`check_board_page.py`) fails a style C
lesson whose contents items are cleared, and warns on a lesson built before.

The audit fails a section with more boards than it has slides, unless each
extra board is an exercise item or a declared split of oversized fixed
content whose combined fixed layers exceed the frame. A split has as few
parts as that content needs: the audit allows the fixed content divided by
the room for a fixed layer, rounded up, and fails more (added 2026-09-24
after a Verb tenses run made 17 boards of two slides by anchoring a few
example sentences on each). What is fixed is what the slide itself shows —
its table, its diagram, its exercise sentence, its list of forms; example
sentences, term boxes, rules and contrasts written while teaching are
working notes even when several thoughts refer to them. A diagram slide is
one diagram on one board. The sections built before this rule whose splits
the maintainer accepted as built (Usage: perfect tenses, Time markers,
Signal words, Active vs passive, Passive forms; `sections.json`,
`boards_accepted`) keep their boards; the count is a warning there. A
topic in the screens model is one board's worth of teaching and carries no
title the student sees.

---

## 3. Density

The working layer holds **at most about four notes at once** before it
needs erasing. The fixed layer counts against the space it occupies.

The binding test is **phone-landscape width, not desktop**. If a board
is not comfortably readable there, erase sooner. It is never solved by
reducing the type size, with one exception: a table board, whose table
may be set smaller to stay whole and is zoomed into instead (§7, Tables).

When a board's fixed layer is heavy (a table part, a sentence with its
answers) and a single thought's notes do not fit beside it, the layout
writes them one note per state, erasing between: notes are written in the
free space and erased when it fills. The build reports every such split.
The hard limit is the content band itself; a board over the working budget
but inside the band is reported as tight. Recorded 2026-09-24, from the
merged page 7 board and the split page 6 table.

---

## 4. Sizing is relative, never fixed

Every size is a proportion of the frame, not pixels. The same board must
hold together on a laptop and on a phone in landscape.

| Element | Share of frame height |
|---|---|
| Body text | ~3.2% |
| Topic title | ~4% |
| Small label | ~2.4% |
| Block padding | ~1.8% vertical, ~2.5% horizontal |
| Gap between blocks | ~2.5% |

Line height 1.35 for body text in blocks.

---

## 5. Colour

Three content colours, one highlight, and the colours of the board style
(§7c: slide boxes, word classes, the definition pill, notes). No more, except
in a Reading lesson, which adds the three keyword-pair colours (§8e), and a
Reading Part C lesson, which adds the four opinion-signal colours (§8f).

| Colour | Meaning | Fill | Accent bar | Text |
|---|---|---|---|---|
| Red | Wrong, error | `#FCEBEB` | `#E24B4A` | `#501313` |
| Green | Correct, answer | `#EAF3DE` | `#639922` | `#173404` |
| Blue | Teacher emphasis, new term | `#E6F1FB` | `#185FA5` | `#042C53` |
| Amber | Highlight over text | `#FAC775` | — | inherits |

Neutrals:

| Use | Colour |
|---|---|
| Body text | `#2C2C2A` |
| Secondary text, labels | `#888780` |
| Hairlines | `#E8E6DF` |
| Controls | `#5F5E5A` |

### Rules

**One meaning per colour, across all lessons.** Green always means
correct. A student learns the code in two lessons without being told.
**Red and green are reserved for wrong and correct** (maintainer,
2026-09-25): nothing else on any board uses them, not a word class, not a
pill.

**Colour is never the only signal.** Every coloured block also carries a
non-colour marker: a ✕ or ✓ icon and a left accent bar. Required for
colour-blind students and for bright-light viewing.

**Tint, not saturation.** Pale fill with a 2–3px left accent bar, never
a strong coloured background. Text stays fully legible.

**Text on a tint uses the darkest stop of the same family.** Never
black, never grey.

### 5a. Tense family colours

Fixed across every lesson. Colour follows **where the time reference
sits**, not the tense name.

| Family | Tenses | Header | Text on it | Accents |
|---|---|---|---|---|
| Past | simple past, past continuous, past perfect | `#EF9F27` orange | `#412402` | `#854F0B` |
| Past up to now | present perfect, present perfect continuous | `#1D9E75` teal | `#04342C` | `#0F6E56` |
| Now | present simple, present continuous | `#7F77DD` purple | `#26215C` | `#534AB7` |
| Future | all future forms | `#D4537E` pink | `#4B1528` | `#993556` |

Family colours appear **only** on category cards, timelines and table
headers, never on error or answer rows, and **only in a tense lesson**
(§7c): elsewhere tense labels are drawn neutral. Present-perfect teal and
"correct" green must never be confused; that is why they differ.

---

## 6. Typography

- One sans-serif family throughout. Style C: IBM Plex Sans, the site's own font (§1a); the
  reference player embeds a pinned copy (`spike/fonts/ibm-plex-sans.lock.json`).
- **Two weights only:** regular and medium. Never heavy. Style C: 400 to 700 (§1a).
- **Sentence case** everywhere. Every block, and every side of a
  comparison, starts with a capital.
- Style C: a table's column labels were letter-spaced capitals until the owner's review of
  2026-10-26; since then they are white words in sentence case on the solid header row (§1a), as
  every other label. The overflow check still checks their words only where a stylesheet draws them
  in capitals (ADR 042).
- Small labels are in sentence case, never in capitals (2026-09-25; §7c). A
  label written in capitals is put in sentence case when parsed (acronyms
  kept), the screens audit fails one that is not, and the overflow check fails
  one drawn in capitals, by its text or by its style (2026-09-27).
- No italics for emphasis; use colour and underline, as a teacher marks
  a board.

---

## 7. Content blocks

| Block | Use | Layer |
|---|---|---|
| Error row | A wrong sentence. Red tint, ✕, left bar. | usually fixed |
| Answer row | A correct sentence. Green tint, ✓, left bar. | working |
| Term box | A new word or phrase with its explanation. Blue tint, small label. | working |
| Gloss | A hard general English word, taught as a moment of about fifteen seconds: the word, its meaning, a generated illustration when the word is concrete, one example sentence (§7b; ADR 013, ADR 015). The block type `gloss`; before 2026-09-27 a term box labelled WORD, drawn on one line. | working |
| Comparison | Two items side by side. Equal columns, hairline between. | working |
| Plain block | A statement or rule with no correctness value. | either |
| Category card | Coloured header strip with a label, and a body. For tense families and for comparing categories. Header in the family colour, or neutral grey for a category that is not a tense. | working |
| Timeline | A diagram on a time axis: tense arrows, reference markers, event series, pointer arrows, callout boxes (and plain points and periods), each in a family colour. Structured data only; code draws it, part by part as the narration reveals them (§7a). | working, or fixed on a diagram slide |
| Callout | Two kinds only. Warning: red circle with "!" on an amber tint. Key rule: blue circle with "i" on a blue tint. | working |
| Table | A slide's table, whole, taught row by row (§7, Tables); or a small tense table with its header row coloured by family. | fixed when it is the slide's content; a small table written while teaching is working |
| Clause diagram | A sentence as puzzle pieces: a dependent and an independent clause, the joining word as glue, S and V labels, the join (§7d; 2026-09-27); a relative clause set into its sentence, its removal test, the subject link of a participle clause (2026-09-27, ADR 012). Structured data only; code draws it, part by part. | fixed when it is the slide's content; otherwise working |

An answer row never stands alone: it is accompanied by a plain or term
block saying why it is right.

### 7a. Graphic elements

Rendered by code, chosen by the screens model from a fixed catalogue.
The model never draws.

- **Number badge**: a filled circle with the topic number in the header,
  and with the item number on an exercise sentence.
- **Verdict badge**: a large filled red circle with ✕ on every error row,
  a green circle with ✓ on every answer row. These replace the small
  icons.
- **Category card**, **timeline**, **callout** and **table**, as in the
  block table above.
- **Icon**: one small outline icon, **only inside a term box whose term is
  a clinical object or procedure — an organ, an instrument, a procedure, a
  medication — beside that word**. Never for a general word, even in a term
  box: "experience", "present", "admit", "trigger", "case notes" get none.
  Nowhere else either: an icon beside an instruction or a rule is
  decoration, and the audit fails it. From a curated list held in code
  (stethoscope, heart monitor, surgery, pill, syringe, thermometer, heart,
  lungs, hospital bed, inhaler). The model names a concept; code maps it to
  the drawing. Narrowed 2026-09-23 after page 13 carried a pencil beside
  its instruction and a clock beside "work at your own pace"; narrowed
  again 2026-09-24 after "Experience" carried a person icon, when the
  general-word icons (patient, pen, flag, calendar, clock…) left the list.
- **Tense tag**: a small chip in the tense family colour, placed directly
  under a verb or a time marker inside a sentence, labelled "past", "up to
  now", "now" or "future". On an exercise item the clash becomes visible:
  "was diagnosed" tagged orange past, "since 2010" tagged teal up to now.
  In the corrected answer both carry the same family. **This is the main
  graphic element of any tense lesson.** The model names the phrase and the
  family; code places the chip. The intro's exercise sentences are not
  tagged, so the student can find the fault unaided; the sentence is tagged
  when it is analysed, and every answer is tagged.
- **Number badge on an exercise topic**: the header shows the topic title
  only, and the item's own badge carries the number. A topic number beside
  an item number reads as two different numbers for one thing.

#### The diagram grammar

Decided by the maintainer 2026-09-24, from his own slides 5 and 11: the
timeline of points and periods was too plain. The timeline is extended
into a diagram grammar, still drawn by code from structured data, never
by an image model. A diagram is a time axis (0–100) and a list of
**parts**, each in a tense family colour where it has one:

- **Tense arrow**: a labelled segment in its family colour with an
  arrowhead; dashed when the family is future. An arrow that overlaps an
  earlier one on the line (present simple across now beside present
  perfect up to now) is drawn in a second lane under the axis, its label
  after the head, so two spans never draw over each other; the audit
  notes it.
- **Reference marker**: a vertical tick with a label below it — "Now",
  "admission", "discharge", "2012".
- **Event series**: repeated marks along the line, one per event (× for
  each cigarette), with a distinct final mark ("X!") and a one-line legend
  under the diagram naming one mark and the final one.
- **Pointer arrow**: a short arrow from a label to a position on the line,
  to point at one moment ("before admission").
- **Callout box**: an example sentence in a box tinted with its family
  colour, attached to a point on the line by a triangle pointer, below the
  line or above it. At most three per diagram, never two overlapping on
  one side.
- The original **period**, **point** and **now** parts remain for a plain
  timeline.

Every part is addressed as `<block id>.<n>` in listed order, so the
narration reveals parts one by one. At most ten parts per diagram. Glyphs
(marks, legend keys, arrowheads) are CSS content, never text, so the
reading pointer and the marks only ever meet real words: a part's label
and a callout's sentence.

For a slide whose teaching is carried by a diagram (the maintainer names
them in `sections.json`, `diagram_pages`: 5 and 11 in Grammar 1), the
screens model is shown the slide image as a reference for the diagram's
**teaching idea only** — which events sit where, what each arrow, tick,
mark and box says — and rebuilds that idea in this grammar. It never
copies decoration (illustrations, circles, background shapes), layout,
colours or wording beyond the exercise sentences.

**Drawn, not just shown.** Diagram parts are revealed one by one by the
narration, and each part is drawn in motion as the teacher speaks, the way
a teacher draws on a board: an arrow grows from its start to its head; a
tick drops into place; the marks of an event series appear one after
another in a steady rhythm; a callout box opens and its pointer reaches
the line; a label writes itself in. Each motion is short, well under a
second (the longest, a full event series, is capped at about 0.7 s), so it
never lags the speech. When the student seeks or jumps, the diagram shows
its correct state for that moment immediately, with no replay. A part of a
fixed-layer diagram stays for the rest of the board, through every
erasure. Under `prefers-reduced-motion`, parts appear without motion.

Rules:

- Every graphic element carries meaning, never decoration. The audit cannot
  judge meaning, so the catalogue itself is narrow.
- Every explanation of a tense choice gets a timeline or tense tags, not one
  timeline per page. The audit warns on a board state that explains a tense
  choice with neither.
- At most one timeline and two icons per board state. The layout erases
  sooner rather than exceed either.
- No photographs, no illustrations, with two exceptions: a gloss's generated
  illustration of a concrete word (§7b; ADR 015), and the board's picture
  (§7e; ADR 021).
- Every element stays legible at phone-landscape width.
- Narration reveals and marks these like any block, and the reading
  pointer follows the text inside them.

### Tables

Tables are taught, not displayed. Revised 2026-09-25 by the maintainer
for every lesson (docs/adr/007-table-boards.md), replacing the earlier
rule that a table too large for the frame is split by meaning. The
reference implementation of the behaviour is
`docs/prototypes/table-board-prototype.html` (its answers and narration
are placeholders, not lesson content).

**A table is core content: shown whole, on one board, never split by
row.** When a slide's content is a table, that table is the fixed layer
of one board, with every row, whatever its size. It is taught row by
row on that board:

- **Row focus is a spotlight.** The row being discussed is at full
  strength and the other rows are dimmed. The cell being discussed gets
  the glass highlight (amber, translucent), moving through the row as
  the teaching does: notes, then formal expression, then sentence.
  **A table whose rows do not pair their cells is spotlit by cell**
  (owner's report, 2026-10-27; ADR 043 decision 17; bundle rule 11): a
  matching table, its words in one column and their meanings shuffled in
  the other, taught by an arrow from each word to its meaning in another
  row. When a word is taught, its cell and the cell its arrow reaches (from
  the moment the arrow is drawn) are lit and highlighted, and every other
  cell, the meaning beside the word included, is dimmed: a row is never
  lit as a pair it is not. Detected from the lesson's data (an arrow from a
  cell to a cell of another row), for every lesson.
- **Answers are typed live into empty cells**, character by character
  in time with the narration (§8, typed text), in the blue of teacher
  emphasis. Every cell's final size is reserved from the start, so the
  table never reflows while typing. What is typed is what the teacher
  wrote in that cell in the recording, never invented.
- **Side notes** (a gloss, a word-form change, a short term or rule)
  appear under the table, never over its rows (revised 2026-09-30, ADR 020;
  they were drawn next to the row, over the dimmed rows), and are erased
  once they have been spoken; the spotlight shows which row they belong to.
  Where they do not fit, earlier notes are cleared, the board made tight,
  the table's text made smaller to its floor, and only then the view pans
  the table up to them. They are the board's working layer; a table board
  has no other fixed block.
- **At the end of each row, the whole table shows again**, no row
  dimmed, before the next row comes into focus.
- **Auto zoom.** When the table's text on screen is smaller than 14 px,
  the camera zooms onto the active cell, with its side notes, and
  follows the typing. At 14 px or more there is no zoom. Under
  `prefers-reduced-motion`, the camera moves without animation and
  typed answers appear whole at their cue.
- **Type size.** A table's text starts at body size (3.2% of the frame's height; 2.6% before 2026-09-25, §7c)
  and is reduced, to no less than 1.9%, only as far as the whole table
  needs to fit the content band. This is the one exception to "never
  solved by reducing the type size" (§3): auto zoom keeps a small table
  readable, and splitting it would break the rule above. A table that
  does not fit even at 1.9% fails the audit; its cells must be shorter.
  *Owner decision, 2026-10-12: a per-board exception, not a rule change.* On
  Grammar 6's board pages-07-08_t2 (18:30 to 27:32) only, the auto zoom is
  removed (no camera zoom onto the cell, no pan to the notes), and the player's
  guard (§8b) sets the table smaller than 1.9% on the device, as far as the
  whole table and its notes need to fit the board. Everywhere else the floor
  stands. From bundle 1.21 the bundle states it: the board's `fit` "whole"
  (docs/04-LESSON-BUNDLE.md, rule 52; ADR 041).

- **Choice tables** (maintainer, 2026-09-25; docs/adr/009). Where each row
  gives versions of one sentence to choose between ("Indefinite / Definite
  / Zero"), nothing is typed. As the narration settles a row, each wrong
  cell fades as its wrong words are struck, and the right cell takes a tick
  on the pale green of "correct" as it is circled. A version that is also
  acceptable, or right only in some context, is neither faded nor ticked; the
  narration says when it can be used. The fades and ticks stay to the end of
  the board, so the whole table ends as a summary of the answers.
- **Gaps.** A typed part inside a printed sentence is a gap: a blank line of
  fixed width, whatever the answer's length, with the answer typed onto it.
  An answer that fills its own cell is not drawn until it is typed.
- **A text with gaps** (a letter to complete) is taught as a table of one
  column: its greeting as the header, a row per paragraph, its closing last.
  The spotlight moves paragraph by paragraph.
- A mark on a table is drawn in one cell: the cell of the row being taught
  that holds its words.

A small table written while teaching (a working note, not the slide's
own content) stays small: at most four columns and five rows.

- **A summary table opens its section, whole, on one board.** Decided by
  the maintainer 2026-09-24 for the tense table of Verb tenses (slides 5
  and 6): a section whose core is a summary table opens with the whole
  table on one board, as a quick overview, condensed to fit at
  phone-landscape width — columns past / present / future, each header in
  its family colour; rows simple / continuous / perfect / perfect
  continuous; each cell only the verb form ("smoked", "was smoking", "had
  smoked", "had been smoking"). The detail follows on the boards after
  it. It is never split. The audit fails a section that has a summary
  table (three or more columns, four or more rows) not in the fixed layer
  of its first board, and warns on a cell longer than a verb form.

---

### 7b. Gloss

**Revised 2026-09-27 (maintainer; docs/adr/013-gloss-moments-and-teacher-openings.md):
a gloss is a teaching moment, not an aside.** The rules below on which words
are glossed stand; how a gloss is shown and spoken changes, for every lesson
from Grammar 6 on (lessons built before keep their one-line glosses until
rebuilt):

- **Data:** the block type `gloss`: `term` the word as it appears,
  `explanation` its meaning (a simpler synonym or a few plain words, about
  five), `text` one short example sentence that uses the word, in a medical
  context where natural, and `icon` a picture from the gloss catalogue when
  the word is concrete, else none. Its parts, revealed by the narration in
  this order: the meaning, the picture (when there is one), the example.
- **Look:** the pale yellow note card; the word a little above body size in
  the medium weight, with "= meaning" beside it on the same line; the example
  under it, after a small "Example:"; the image beside them, fading in as it is
  revealed (compact since 2026-09-27: a gloss on a board with a heavy fixed
  layer overflowed with the word, meaning and label on lines of their own). Every
  part's room is reserved from the start, so nothing moves (§8a).
- **Images** (revised 2026-09-27, docs/adr/015-gloss-images.md, replacing
  ADR 013's line drawings): a generated illustration, only where the word is
  concrete and a picture helps understanding; an abstract word keeps the
  example sentence only. The gloss's `icon` is its image brief, "alt text |
  what to draw", subject only. The model never draws on the board: code
  generates the image from the brief and the style guide
  (`spike/scripts/gloss_images.py`), cached by the brief like audio clips.
- **Image style guide** (`gloss_images.STYLE`): a clean, professional
  medical-education illustration, semi-realistic with soft shading and clean
  edges; a modern, calm, nursing-textbook look; not a photograph and not
  childish. Skin in natural, realistic tones; a restrained palette of soft
  blues, teal and slate grey for clothing and objects only, so it sits well
  on the white board and the pale yellow note. The subject only, isolated:
  no background, scenery, floor, shadow or clutter (only the palm; only the
  orderly and the patient, no corridor). No text in the image. Nothing graphic
  or gory: a lightly grazed palm, never blood or an open wound. The same style
  in every lesson.
- **Image pipeline:** drawn by the model on plain white; the background
  removed locally (rembg's ISNet model on onnxruntime), the white taken out of
  the edge pixels, specks dropped, trimmed to the subject; a transparent PNG,
  512 px on its longer side, 256 colours (about 30-50 KB), with alt text. Its
  edges are checked (an edge report per image; looked at on a checkerboard and
  on a dark background when the style changes).
- **Narration:** about fifteen seconds: the block revealed as the word is
  first said, the word said clearly on its own, a pause of about a second; the
  meaning revealed and said; the image revealed right after the meaning, with
  nothing said about it; the example revealed and read; a pause of about a
  second and a half; then the lesson goes on. **The narration never points at
  a picture** ("as you can see in the picture", "look at the image", "in this
  picture", "the drawing shows"): the image appears while the word is
  explained, and that is enough; the narration audit fails a pointing phrase. The narration audit fails a gloss whose parts
  are not all revealed in order in one state, or whose moment has fewer than
  two pauses or is estimated under ten seconds (words at 150 a minute plus
  pauses), and warns under thirteen.

**Vocabulary lessons** (maintainer, 2026-09-29; docs/adr/019-vocabulary-lessons.md).
In a lesson whose type is vocabulary, every key word (a word or collocation the
section teaches, and the everyday adjectives, nouns and verbs needed to use it)
gets a full moment where it is first taught, in existing blocks, in this order:
the gloss (meaning, image when concrete, an example from a medical letter); an
answer row with an example said to a patient; then, where it helps, a note
"Word family", a note "Collocations", and a near-synonym as a comparison with
the difference in use. Every section adds examples of its own. All of it is
`authored` (role example or note). A key word that is a medical term is glossed
with the plain words a patient would understand, never a dictionary meaning.
A2-B1 throughout; no register claims.

The rules as they were for the one-line gloss, kept for lessons built before:

Recorded 2026-09-25 (docs/00-PRODUCT.md §3, "Hard general words are
glossed"). A gloss explains a hard **general** English word the first time
it appears: never a medical word (specialist terminology such as
hypothyroidism or warfarin; "deteriorate" and "commence" are general words,
docs/00-PRODUCT.md §3), never a grammar term (grammar terms get a term box
with a plain definition, as before).

- **Data:** a term box with the label `WORD`, the word as it appears as its
  `term`, and the gloss as its `explanation`: a simpler synonym or a few
  plain words, no more than about five ("plan a time"; "a change to make it
  work better"). No icon. No new block type and no new field: the bundle
  contract is unchanged, and a renderer that knows nothing of glosses still
  shows the label, the word and its gloss.
- **Look:** on one line, "schedule (= plan a time)": the word in the
  **medium** weight, the gloss in the **regular** weight inside "(= ...)".
  Since 2026-09-25 a gloss is a note (§7c): the pale yellow note card, with
  no label above it. No new weight.
- **Layer:** working, like any note, placed where the word first appears
  and revealed as the narration says it.
- **Narration:** one short sentence as it appears: "Schedule means to plan a
  time for something."
- **Not overloaded:** only a word a learner at A2-B1 is likely not to know.
  A word glossed once is not glossed again later in the section.

### 7c. Kinds of content and the board style

**This is the standard for every board of every lesson** (maintainer,
2026-09-25). No board is built in the style before it: the screens audit
and the structural check fail any block drawn the old way (a term box in the
old blue box with a capitals label, a plain two-column comparison, a block
with no kind). AGENTS.md makes it binding.

Decided by the maintainer 2026-09-25 for every lesson (docs/adr/008-board-style.md),
from his own slides; reference `docs/prototypes/p4-board-style-prototype.html`
(style direction, not content). A board shows at a glance what kind of
content each thing is, and a change as a flow from one sentence to another.
Colour and shape appear only where they say what the content is.

**Three kinds of content** (each block's `role`, set by a rule; an override
may correct it):

| Kind | What | Look |
|---|---|---|
| Slide | The deck's own sentences, tables and main examples; a sentence written into a box the slide leaves for it | A rounded slide box, **never erased**: the source sentence sky blue (`#EAF4FC`, edge `#C9E0F3`), the result peach (`#FFF1E2`, edge `#F6D2A8`) with its green tick; a slide table has a sky header and rounded corners. Medium weight |
| Example | An extra example the teacher gives | A change card, or a correct or wrong sentence with a smaller radius: clearly secondary |
| Note | Side notes, glosses, rules, explanations | The pale yellow note card (`#FFF8DC`, gold edge `#E0AE12`), shown then erased; callouts keep their badges |

A slide block that appears during the teaching (the result written into the
slide's box) is **pinned**: once revealed it stays until the board ends,
through every erasure. So is the definition pill.

**The flow of a change.** Where a board changes one sentence into another:

1. **Definition pill** at the top: the grammar term being taught, in a white
   tag, and its definition, on the orange pill of the maintainer's header
   pills (`#F7A531`). It replaces the term box with a capitals label.
2. **Source sentence** in its slide box. A part the slide marks (the
   underlined clause) stays **inside its sentence**, underlined, never as a
   separate box; its marks are drawn there.
3. **Process pill** (the process's name, neutral slate `#475569`) with a
   chevron above and below, beside the first **change card** of a run.
4. **Change cards**, one per change: "from → to", each side with its word
   class under it in small type ("verb", "noun", "clause", "noun phrase").
   Every comparison is drawn as a change card: side by side when the sides
   are short, stacked (from above, to below) when they are sentences. Plain
   two-column comparisons and capitals labels are no longer used.
5. **Result sentence** in its slide box, pinned.
6. Notes last.

The order on the board follows the flow whatever order the blocks were
revealed in.

**Colour by grammatical role.** The words that change are marked in the
source sentence in their word-class colour, and the same colour links them to
their change card and to the result: a word takes its colour when it is first
marked or its change card appears, and keeps it for the rest of the board;
the result's words take theirs when the result appears. The slide's own
underlines and highlights are kept.

| Word class | Colour |
|---|---|
| Verb | deep blue `#084191` |
| Noun, noun phrase | amber-brown `#916308` |
| Adjective, adverb | teal `#1F7A73` |
| Clause, phrase | magenta `#CB0BAB` |

Text in the colour on a soft tint of it. Chosen by measured colour
difference (CIEDE2000): 33.7 or more between any two, 28 or more from red
and green, text contrast about 4.5:1 or better on white. Two colours are
close to a tense colour (noun to the past accent, adjective to the "up to
now" teal), so **the screens audit fails a board where a word-class colour
and a tense colour it is close to (difference under 20) appear together**,
and any word-class colour within 20 of red or green.

**Table boards** (extension of 2026-09-25) keep §7 "Tables" and take the
same style:

- **Words that change are coloured in their cells, by word class:** the
  source word in the notes column and before the arrow in the change column,
  the new form after the arrow and in the sentence. A cell's word is marked
  in that cell only. A typed word takes its colour when its typing ends; a
  printed word when its row is first typed into, or when it is first marked.
- **A side note that only states a word change is a change card:** "The
  adjective 'sensitive' becomes the noun 'sensitivity'" is drawn as
  sensitive (adjective) → sensitivity (noun); a note stating two changes is
  one card with two lines. It is shown beside its row and erased as before. A
  note that says anything more stays a note.
- **Other term boxes are note cards:** the yellow note card with the term
  in the medium weight and its tag in small sentence case ("Pronunciation",
  "Abbreviation"). The definition pill is for a board that is not a table.
- **The table** has the sky header with a firmer edge under it, and rounded
  outer corners, as a slide box. Table text starts at body size (3.2% of the
  frame's height) and is reduced only as far as the whole table needs to fit.

**Word classes** come from what the section itself says: its change cards
("Analyse (verb)"), its notes ("The adjective 'sensitive' becomes the noun
'sensitivity'", "Symptomatic, asymptomatic and afebrile are all
adjectives"), the table's header ("Nouns → Verbs"), then word endings
(-tion, -ity: noun; -ive, -ous: adjective; -ise, -ate: verb). A word is
matched only in its own forms (analyse, analysed), never by a shared stem
(assess is not assessment). A word nothing classes stays uncoloured; a
phrase that begins with a preposition ("on a daily basis") is not a noun
phrase and stays uncoloured.

**Word-class colours are the same everywhere; tense colours only in tense
lessons** (maintainer, 2026-09-25, replacing per-board alternates). A lesson
is a tense lesson when the maintainer says so at the source gate
(`build_sections.py --tense-lesson yes`; Grammar 1 and 2 are). Only a tense
lesson draws the tense family colours (§5a). In any other lesson, a tense
label keeps its words ("up to now", "now") and is drawn neutral, as are
timelines, category cards and table headers that would carry a family
colour. The audit fails a tense colour in a lesson that is not about tenses,
and, in a tense lesson, a board where a word-class colour and a tense colour
it shows are too close (difference under 20).

**A word's class from grammar.** Where the section does not say a word's
class, the grammar of its change can: a noun made from a verb by its suffix
(-ion, -ment, -ance, -ence, -al) makes its base a verb (interact →
interaction, assess → assessment, comply → compliance, adhere →
adherence), and one made from an adjective (-ity, -iety, -ness) makes its
base an adjective (anxious → anxiety); the same in the other direction for a
noun turned back into a verb (removal → remove). A word is left uncoloured
only when its class is truly ambiguous: a participle such as "confused" can
be an adjective or a verb.

**The introduction** keeps its title and contents items, which list every section
of the lesson by name, authored ones included (docs/00-PRODUCT.md §2a); its description is
a slide box, the lesson's own words. Its title board also shows what the
narration describes (ADR 014, 2026-09-27): the lesson's own intro blocks from
sections.json `intro_board` (a note linking to the previous lesson, a change
card from short sentences to one clear sentence), revealed as they are said.
A course's first lesson links to no other lesson, and no board anywhere shows
a course map, a lesson count or a list of lessons: the course is still growing
(ADR 014 amendment; the screens audit fails a lesson count).

**Presentation only.** The board style changes no block's text, no id, no
cue and no state: narration and audio are unaffected. A cue on a folded
part lands on the same words in its sentence; a cue on a change card's
"Analysis (noun)" lands on "Analysis" (the class is a tag, not words).

### 7d. The clause diagram

Decided by the maintainer 2026-09-27 for every lesson (docs/adr/010-clause-diagram.md),
from `docs/prototypes/p5-complex-sentence-prototype.html` (direction, not
content). A sentence is drawn as **puzzle pieces**, to show how clauses join.
Like the timeline it is structured data drawn by code, part by part as the
narration reveals it (§7a); the screens model never draws.

| Part | Look |
|---|---|
| Dependent clause | A piece in the clause magenta (`#CB0BAB`, the word-class colour of a clause) on a pale tint, labelled "Dependent clause", with a **tab** on the side facing the other piece: it cannot stand alone |
| Independent clause | A piece in neutral slate (`#475569`), labelled "Independent clause", with a **notch** where a dependent piece joins it: it can stand alone |
| Glue | The joining word, on the orange of the maintainer's pills (`#F7A531`): a chip on the word inside its piece ("Although"), or a bridge between two independent pieces ("and") |
| Subject, verb | A small "S" (neutral) or "V" (verb blue `#084191`) above the phrase; the verb takes the verb blue |
| Join | Last: the tab slides across the gap into the notch; when the dependent clause comes first, its comma shows. On a compound sentence the bridge reaches out to both pieces |

- One or two pieces, in the order the sentence has them. Piece text is the
  sentence's own words, or, for a pattern, the names of its parts
  ("subordinator + dependent clause").
- **Compound and complex** read at a glance: two complete slate pieces bridged
  by an orange "and" is a compound sentence; a magenta piece that plugs into a
  slate one is a complex sentence.
- **Nothing moves a word** (§8a). The pieces never move: only the tab and its
  neck do. The S and V labels sit in the line's own leading, the glue chip is a
  background and a shadow, and the comma's room is reserved from the start.
- At most ten parts. The slide's own diagram is the board's fixed layer
  (role slide); one drawn while teaching is an example.
- The stand-alone test is drawn with the ordinary rows: the independent
  clause alone as a correct sentence, the dependent clause alone as a wrong one.

**Relative and participle clauses** (maintainer, 2026-09-27;
docs/adr/012-relative-and-participle-clauses.md). Five more parts, for every lesson:

| Part | Look |
|---|---|
| Non-defining clause | Set into its sentence inside the slate piece, on the magenta tint with a **dashed** magenta edge; its commas, coloured, are its edges: it can be taken out. The piece's label adds "Non-defining relative clause inside" |
| Defining clause | Set in the same way with no commas, a **solid** edge and a slate pin at each end: it is fixed in place |
| Removal test | Last: the clause fades and the sentence without it is written on a line under the pieces: green with a tick, "Without the clause: still a full sentence" (non-defining); red with a cross, "Without the clause: we lose who or what we mean" (defining) |
| Subject link | An arc over the words, from the main clause's S to the participle ("Mr P" to "complaining"): one subject shared by both clauses |
| Dangling participle | The same arc broken, with a red cross where it breaks: the main clause's subject is not the participle's; drawn only on a sentence shown as wrong |

Nothing moves a word (§8a): the set-in clause is styled in place, the removal
line's room is reserved from the start, and the arcs are drawn over the board
like marks, measured from where the words are.

### 7e. A picture on every board

Decided by the maintainer 2026-09-30 for every lesson (docs/adr/021-a-picture-on-every-board.md).
Every board has at least one relevant generated image in the approved style
(§7b): the patient in the case notes, a clinic scene, or a picture of the
concept. Meaningful, never decorative; never over text.

- **The brief** is the agent's, one per board, in `analysis/pictures.json`
  ("alt text | what to draw"), written from the board's content; the exercise
  items of one exercise share one picture.
- **The block** `picture` opens the board: the first note of its first state,
  shown from the state's start with no cue, erased with that state or cleared
  by the fit when a later note needs its room (§8b). A square, 20% of the
  frame's height (smaller, to no less than 10%, where the fit finds the board
  too full, or where the player's guard finds it too full on the device, §8b),
  in the board's flow; on a table board at the right under the
  table, the side notes beside it on its left. Always scaled whole, never cropped.
- **The narration never points at it**, as for a gloss's image.

### 7f. The map of the texts (Reading, Part A questions)

ADR 026, the Part A question method; bundle 1.14, rule 31.

- **What it is.** The four Part A texts at once, each a small page, in a grid
  of two by two, in the board's left column; the question and its notes are a
  column beside it. It is a map: too small to read on purpose. Its words are
  read only once the map zooms.
- **Steps, one per state.** All four texts; the chosen text bright and the
  others dimmed; that text alone, at a document's size; its part that holds the
  answer set larger in the middle of the map's frame, the other parts dimmed.
  The zoom is inside the map's own frame (a lens), so the question and its
  keyword marks stay in view.
- **Exempt from the table text floor.** The 1.9% floor of §7, Tables, does not
  apply: the map's pages are scaled to their quarter and need not be readable
  until the zoom (maintainer, 2026-10-06).
- **Exempt from "nothing moves a word"** (§8a): the lens moves the map's words
  by design, as the camera does a table's; the layout check leaves the map
  out. Every other block on a map board is held to §8a.
- Marks, keyword pairs and the pointer inside the map are drawn only where the
  map's frame shows them.
- **Whole lines only** (maintainer, 2026-10-07): a zoomed map never cuts a line;
  where the text goes on above or below, the next line shows faded, as a cue, as
  the Part B lens did (§7g; `check_lens.py`).

### 7g. A Part B question, the covered text, and the word bank's glosses (Reading)

ADR 026, the Part B question method and the vocabulary layer; bundle 1.15, rules
32 to 34; the two-column question board, bundle 1.16, rule 36.

- **The question with its options.** Under the question, options A to C, each
  with its letter in a small circle. A wrong option, when ruled out, is struck
  through in red on the pale red of "wrong", with a short reason label under
  it after a cross; the answer takes a tick on the pale green of "correct". The
  room of every label and tick is kept from the start, so nothing moves.
- **The covered text.** While the question, the options and "try it first" are
  taught, the text's page shows only its type tag on a hatched grey cover, at
  its full size, as the instructor covers the text; then it appears.
- **Document looks by genre** (stylesheet only, no words added): an email as a
  mail window; a procedure with a document-control band; a guideline with a
  blue edge; a manual on a dark header with a dashed edge; a policy with a
  formal black rule; a notice pinned on a pale yellow sheet.
- **A word-bank gloss**: the gloss card (§7b) with the word's synonym under its
  meaning ("Synonym:"), and a small round speaker button beside the word that
  the learner taps to hear it (never played by the lesson itself).
- **Word tables**: the matching table (Word | Meaning) and the recap table (Word |
  Meaning | Synonym) are table boards (§7, Tables).
- **The lens** (maintainer, 2026-10-07; **superseded on 2026-10-08** by the two
  columns below, kept as history: Reading 3 was built with it in bundle 1.15): on
  a question board the text kept its own frame; once it was uncovered, the whole
  extract showed once, then the lines being read were set at body size in that
  frame, the rest dimmed, as Part A's map zooms (§7f), whole lines only.
- **Two columns, the extract whole** (maintainer, 2026-10-08; ADR 026 amendment of
  that date). Once uncovered, the whole extract is visible at every moment: no
  lens, no scrolling, no hidden line. The extract is a fixed page (its type tag
  and look kept) in one column; the question, its options, reason labels and
  tick, the notes, the glosses and the board's picture are a column beside it.
  The question column gets the room it needs at body size; the extract takes the
  rest, at the largest size at which it fits whole, from body size (3.2% of the
  frame) to no less than 2.6% (the table exception of §3 and §7, with a higher
  floor); it need not be the larger share. The reading is followed by the
  spotlight: the paragraph being read at full strength, the others at 60%, still
  readable, with no amber cell (§8e); the marks, pairs and pointer as before. The
  whole extract shows undimmed first, until the end of the first sentence said
  once it is uncovered. Only a gloss may go over the question column, at its
  foot, its top edge between two lines, briefly, and never while the part of the
  question it covers is read or marked; never over the extract (§8d). The camera
  does not zoom these boards. The board is the room between the header and the
  control bar, which keeps 44 px on a small screen (2026-10-08). The fit
  measures the phone and laptop frames with Segoe UI, Arial and Roboto; on a
  smaller frame or with a wider device font the player's guard keeps everything
  whole: the extract smaller (never below 2.6%), the question column wider, and
  as a last resort the question column smaller, to the same floor. Checked by
  `check_lens.py` (every line of the extract on its page and on the board after
  it is uncovered), `check_overflow.py` and `check_overlap.py` (nothing under
  the control bar), at a phone held landscape (915x412), phone-landscape and
  laptop frames, and `check_wide_font.py` (Verdana forced). Part C will follow
  the same principle.

### 7h. A Part C question board and the attitude scale (Reading)

ADR 026, the Part C question method (amendment of 2026-10-08); bundle 1.17, rules 37
to 40.

- **Two columns, as Part B's (§7g)**: the text in one, the question, its options,
  labels and tick, the notes, the glosses, a scale and the board's picture in the
  other, with the same split rule, floor, fit, guard and checks.
- **The text, a map or a paragraph.** First the whole text as a map, every paragraph,
  too small to read on purpose (exempt from the table floor, as Part A's map, §7f), the
  paragraph that holds the answer marked in pale blue with a blue edge, the others
  faded. Then only that paragraph (or two neighbours where the answer needs both),
  whole, at the largest size from body size to 2.6% at which it fits, with a position
  cue in the header ("Paragraph 3 of 7") and the text's type tag. Never scrolled, never
  a lens window. A Part C text is an article: a page with a navy top rule.
- **The options come later (QTA).** The question shows its stem alone, in-context
  words in bold as the test prints them; its options appear when the paragraph has
  been read, their room (with their reason labels') taken from the start of that
  state (as a pinned block's, §8b), so the question column has room for the reading
  before them and an option's words never move once shown.
- **The attitude scale**: on a question about the writer's or a person's attitude or
  view only. A grey line labelled at its two ends and its middle in words fitted to the
  question ("Sceptical", "Neutral", "Enthusiastic"); a blue marker moves along it as the
  evidence is read (the latest place only); each option's letter is placed on it, in a
  small circle, struck on the pale red of "wrong" when ruled out, filled in green with
  the tick colour when chosen. Two letters closer than a tenth of the line take two
  lanes, above and below it, so they never meet. Pinned once shown.
- **Words a phrase read takes** on a Part C question board: the amber highlight, and
  keyword pairs `match1` and `match2` only (the yellow `match3` is too close to the
  amber, §8e).

### 7i. Listening: the note form, transcripts and recordings

ADR 029; bundle 1.18, rules 42 to 45. Amended by ADR 030 (bundle 1.19, rules 46 to
48): the Listening board below replaces the covered transcript, its parts, the row
spotlight and the full-width note-form board. Amended by ADR 031 (bundle 1.20, rules
49 to 51): no hyphenation, a smaller transcript, the vocabulary panel, the whole note
form in the reading time.

- **The Listening board** (ADR 030): one layout for Parts A, B and C. The transcript
  in a box on the left (62% of the board; ADR 031), the questions on the right: Part A
  the note form, Part B the question and its options, Part C the question the
  recording is covering. The box is fixed: ten lines at 3.1% of the frame (never below
  the 2.6% floor), justified (each paragraph's last line set left), never hyphenated:
  no word is broken across two lines (ADR 031), its
  speakers' labels at the start of their turns, its rows on one line grid so no line
  is ever cut. While a recording plays it moves smoothly, line by line, the line
  being said the fourth from its top; a thin blue line runs under the word being
  said and a small blue caret marks its line in the left margin; no word is
  recoloured or highlighted. It is on screen whenever a recording plays, the first
  time too. A Part A note form is set at 2.8% in a window of whole rows that moves to
  the heading being heard, or to the gap being filled. No board picture. The box and
  the form's window are exempt from "nothing moves a word" (§8a), as the map's lens
  is: they move their rows by design, and the form is shown whole in the reading
  time; `check_lens.py` measures them instead (`check_layout.py` leaves them out,
  2026-10-14). Every other block on a Listening board is held to §8a.
- **The vocabulary panel** (ADR 031): under the transcript's box, in its column, at
  2.8% (fixed). Each item is a gloss (§7b colours) drawn compact: the word in the
  medium weight, the "hear it in the recording" button, "= meaning", "· Similar:"
  and its synonyms (a paraphrase pair: "· Same as:" and the question's or the notes'
  words first) flowing as one paragraph, the example under them. While a recording
  plays the items appear as the marker passes their word, the newest last; while the
  narration teaches one, the box shows the line it is said in and the term is
  highlighted there. Whole items only: where they do not fit, fewer, never smaller.
- **The reading time before a Part A extract** (ADR 031): the note form alone, every
  row, the width of the board, at 3.0% (to the floor where needed); the transcript and
  the panel wait for the first word.
- **The Part A note form** is a page with a blue top rule, its tag "Notes", a heading
  row per heading, a row per gap with the gap's exam number as a small blue badge (a
  stylesheet attribute, never a word). Each gap is a blank line of fixed width (§7,
  Gaps) until the lesson types its answer; the learner never types. The spotlight
  walks the rows. On a Listening board (above) it is the board's table, in the
  question column.
- **A transcript** is a page with a slate left edge and the tag "Transcript"; each
  turn's speaker label is set in the medium weight and navy, nothing more. On a
  Listening board (above) it is the box. (ADR 029's covered transcript, its parts and
  the row spotlight are replaced by ADR 030.)
- **A recording playing** (the practice set's own audio, in the lesson's clock): a
  "Recording · Extract N" label in the header, white on blue with a pulsing dot (no
  pulse under reduced motion), and a blue outline inside the board's edge, drawn over
  nothing; nothing else changes and no word moves. On a Listening board the box
  follows the word being said (above). A short spoken cue always
  comes first ("Now listen to Extract 1."); the narration never speaks over it.
- **A heard word**: a word-bank gloss of a word heard in a recording has a second
  round button beside the speaker button, white with a blue edge and three bars,
  that plays the sentence of the recording the word is said in (never by itself).

### 7j. Board layouts (style C)

Decided by the owner at his review of Writing 2 on 2026-10-26 (ADR 042, amendment (2)): the boards
are laid out with the imagination of his own decks, a visual in place of a plain table wherever the
content allows. **For each board, look at the matching slide of the lesson's own deck and carry its
visual idea over** in style C (never its decoration, never official OET content). Use a table only
where a table really is the clearest form; then it is drawn as the handouts draw one (§1a: a solid
header row in the section's colour, white words, tinted rows).

**From 2026-11-01 the layout of every board is a creative design decision** (ADR 048,
docs/adr/048-creative-board-design.md): the session designs each board for the one thing it teaches, no two boards
in a row alike, a plain table or text block only where nothing teaches the point better (the reason logged), the
owner's own slides the starting point to match or better, and a scored critique of the lesson's contact sheet
before voicing. The rows below are the forms the engine draws today; a form a lesson needs and the engine cannot
draw is added here, in `style_c.LAYOUT_CSS`, in its own pull request with the render proof (ADR 048 decision 8).

A layout is presentation only: it never changes a block's words, their order, an id, a cue, a state
or the narration (§7c, "Presentation only"). It is named per block in the lesson's
`analysis/sections.json`, `block_layouts` (`{"<bundle block id>": "<layout>"}`, the bundle's block ids,
as `boards_fit` names boards), and drawn by `style_c.layout_html` as classes and attributes on the
block's html (`lay lay-<layout>`, `data-crit`, `data-label`, `data-bin`, empty decorative elements),
styled by the lesson's `blocks.css`. Nothing is added that a reader or a mark could count as a word:
labels and monograms are attributes the stylesheet draws, dots and lanes are empty elements hidden
from screen readers. The builder refuses a layout on a block that cannot take it, and a change of
words (checked). Only the rows and the cells of a table are laid out, never an element that holds
text directly (a marked phrase would become an item of its own and move, §8a). The table's hooks
(`data-row`, `data-col`, `data-typed`), its spotlight, its typing, its zoom and its fit work as on any
table board.

| Layout | For | What the learner sees | First used (Writing 2, the slide it follows) |
|---|---|---|---|
| `tiles` | a table of a few items of one kind, each a name and a line | tiles in a grid of three (two for four), each in its own colour with its monogram where it is a criterion; the tile being taught lifts, the others fade | The six criteria (slide 4: six coloured circles) |
| `scores` | a table of scores: a name, out of how many, how many needed | a scorecard a row, side by side: its points as a bar of dots, those needed filled, and the two numbers large with their labels; "the other five" carries the five criteria's colours | How your letter is scored (slide 5: the yellow card "2/3 for Purpose, 5/7 for all other criteria") |
| `cards` | a short table read as parallel parts | the rows as cards side by side; a two-column table's first cell is the card's heading, further cells carry their column's label; "Yes" and "No" in a column "In the letter?" as a tick or cross chip | The opening's three parts (slide 6); one note, two readers (slide 9) |
| `steps` | a two-column table in order: steps, or times | cards left to right joined by arrows; a step's number as a round badge | What you read first (slide 9); the verbs' times, in hospital, today, next (slide 14) |
| `flow` | a letter's parts or a paragraph plan, top to bottom | the parts one under the other on paper, each named in its margin, a chevron from one to the next | The opening, the next paragraph, the last (slide 7: the chevron down) |
| `bins` | notes sorted into keep, keep briefly or leave out | three lanes beside each note, Keep, Keep briefly and Leave out; each note's answer is typed into its lane (the lane's room is there from the start, empty, so nothing gives the answer away) | Medical history (slide 13: ticks and crosses beside the lines) |
| `fix` | a note, a wrong version, the right one; or only a wrong version and the right one (two columns, ADR 043 amendment (3)) | a row a case: the note, the wrong sentence on red with a cross, an arrow, the right one on green with a tick, typed in | Discharge plan, wrong, accurate (slide 11); two columns: Grammar 4's "Wrong, Right" (slides 7 and 8) |
| `change` | from one form to another | the first form, an arrow, the second | Abbreviations, case notes to letter (slide 17) |
| `stack` | the parts of a letter, one of them singled out | the parts stacked, the one that counts larger and in the section's colour | What is counted (slide 12: the letter beside "180–200 words") |
| `notes` | a short list of case notes | a case-notes card on paper, its heading as a tab, a dot a line | Social background (slide 15) |
| `letter` | a whole letter by its parts; or a text with gaps, a table of one column (§7 Tables, ADR 043 amendment (3)) | the letter on paper, each part's name in its margin; the zoom brings the line being taught to body size (a Writing lesson's, ADR 043 decision 7). Of one column: its greeting at the top, a paragraph a row, its closing last, the paragraph being taught a white sheet on the paper | The whole letter (slide 18); one column: Grammar 4's gap fill (slide 15) |
| `checklist` | what is checked and the word for it | tiles, the word for it large in the section's colour | Language: meaning clear, vocabulary precise (slide 19) |
| `vs` | a comparison of two options (not a change) | the two side by side, numbered 1 and 2 | Two openings (his try-it) |
| `pair` | a table of four columns that is two lists of one kind side by side (a name and its examples, twice) | two tables with a gap between, each its own header; a row is still taught as one row, across both (ADR 043 amendment (3)) | Grammar 4's countable and uncountable nouns (slide 6: two tables side by side) |
| `paper` | a Writing paper, or a piece of it: two columns (the paper's label, its lines); or the paper beside the letter: three (the label, the lines, the part of the letter they feed) (ADR 045) | two columns: a sheet of the paper, as in the exam: white, a hairline edge, a soft shadow, the labels bold in their own column, the date line bold, the Writing Task box grey. Three: each row a piece of that sheet, an arrow, the part of the letter on the letter's cream; never zoomed, so both stay in view | Writing 3: the guided look at the paper, the map board (slide 5) and every board that quotes a paper |
| `acronym` | the parts of an acronym, a table of two columns: a letter, a colon and the part's name ("I: Introduce and identify"), and the part's text (ADR 049) | a row a part, on a tinted band: the letter large, bold and in the key-word amber in its own narrow column, the part's name in bold beside it (the colon stays in the words, drawn at no size), the text in the row; the spotlight lifts the part being taught and the marker marks its words; shown whole and marked no-zoom, so the whole table stays in view | Writing 7: the ISBAR approach (the owner's "ISBAR APPROACH" slide) |
| `skeleton` | two letters side by side, a table of two columns, a paragraph a row: written out where the lesson reads it, empty where not (ADR 049) | each letter a sheet on the letter's cream: a paragraph written out in full (the opening, its purpose words in the Purpose colour: `block_accents`), a paragraph not written out as three short dashed lines drawn by the stylesheet (never a word), the last paragraph written out of each letter (the request expanded) in the Purpose colour; a letter that ends earlier leaves its sheet short | Writing 7: where the request goes (the owner's "Request" slide) |
| `pieces` | a sentence as its pieces: a header naming each piece (who, what, where, when, why), one or more rows of the pieces themselves; a board's own table or one written while teaching | the pieces as chips in a row, read left to right as the sentence is, each under its label in the section's colour; a chip is typed into as the narration reaches it; a second row (another sentence) sits under the first. A scrambled sentence's labels show its disorder before a word is heard (ADR 048) | Word Order's redesign (2026-11-01): the formula built piece by piece (the owner's slide p5, "Who + what + where + when + why"); the paper's sentence scrambled; the answer to a practice point |
| `place` | the paper beside the letter (ADR 045), three columns, where the letter column's label names the part's place after a colon ("Her letter: the request"; opening, body, request or closing) | as `paper` beside, but the part of the letter is drawn in its place on a small white letter whose other lines are dashes: the opening at the head, the request near the foot (the owner's Request slide, Writing 7's deck p8). Never zoomed (its board is shown whole) | Word Order: the request from the plan; the opening from the setting line |
| `tags` | a two-column table of a sentence and a note on it (where a word sits in it) | each sentence on paper, its note as a tag in the section's colour at its end; the narration underlines the words the tag is about | Word Order: where also, then and a frequency adverb go |
| `front` | a sentence in two pieces: its kind, the phrase that opens it (up to its comma), the rest (three columns) | the kind as a chip, the opening phrase bold in the section's colour with its comma, then the rest of the sentence in plain, so the two parts are seen; the words are the sentence's own | Word Order: a time, a context, a reason and a contrast at the start of a sentence (the owner's slide p9) |
| `sides` | one case and its two versions: three columns (the case, the first place, the second) | the case as a chip, the two versions side by side under the two column labels, the left on paper, the right white; the pair is read together, so its board is shown whole | Word Order: a phrase at the start with a comma, or at the end with none (the owner's six-column table, p13) |
| `chips` | short phrases, in any number of columns (a word bank) | the cells as chips in a row, row by row, under the bank's name (the first header cell); nothing of its order gives an answer away | Word Order: the bank of a letter with gaps (the owner's slide p16, the band above the letter) |

The forms and the layouts added in phase 2 and after (a `fix` of two columns, a `letter` of one, `pair`,
`paper`, `acronym`, `skeleton`, and ADR 048's `pieces`, `place`, `tags`, `front`, `sides` and `chips`) are drawn by rules appended to the stylesheet of a lesson that uses them only
(`style_c.LAYOUT_CSS`), as the cell spotlight's are, so no other lesson's stylesheet changes; each form is
told by its columns, so the block's html carries nothing new.

### 7k. The teal look's patterns (ADR 050)

The owner's Canva patterns 1 to 11, each a layout named in `block_layouts` like any other (its rules appended only to
a lesson that uses it; their colours fall back to the teal look's own). Every lesson in the teal look uses a varied
mix of them, **no two boards in a row share a pattern** (the title, contents and closing boards count), and a pattern
may vary its arrangement between lessons. The pattern of each board is logged with the slide it follows.

| Layout | Pattern | Takes | Drawn as |
|---|---|---|---|
| `wrongright` | 1 Wrong and right | a table of two columns (wrong or as written; right or put right) | each pair a row: the wrong sentence in plain ink, a curved red-pen arrow, the right one in bold teal; the narration's pen circles mark the error |
| `coded` | 2 A colour-coded sentence | a header naming each part; one or more rows of parts | each part a rounded tile in its colour, its label a pill of that colour above it, read left to right; typed in as the narration reaches it |
| `opener` | 2 (a phrase first) | three columns: the kind, the phrase that opens the sentence, the rest | the kind a small pill, the opening phrase in a tile of that colour, then the rest in plain |
| `timeline` | 3 A timeline | two or three columns: the marker (a date, a number), the event, a note | round markers in turn's colours on a teal line, the event under each in bold, the note in the hand |
| `columns` | 4 Keep, shorten or leave out | two to four columns | solid pill heads (teal, amber, coral, blue), each column's cells soft pills of its colour; a column of short labels or places narrow (`data-cw`) |
| `parts` | 5 A letter's parts | two columns: the part's name, its paragraph (empty where not written out) | one white sheet with a teal edge, each name a pill in its colour joined to its paragraph by a line; an empty paragraph as grey lines |
| `badges` | 6 Key tips as badges | one or two columns (the point, a note); or a recap's category cards | solid circles holding the point, a note in the hand under each; cards side by side |
| `ruled` | 7 A paragraph on ruled paper | one or two columns (the line's number, the line) | a white sheet with blue rules and a red margin, the lines in a learner's hand, the numbers in the margin |
| `beforeafter` | 8 Before and after | two columns (before, after) | two panels, coral and teal, their heads in capitals; each sentence with its word count in a circle (counted from its words, `data-count`) |
| `choices` | 9 Choice pills | short phrases, any columns | solid pills in turn's colours; each under its label when every column has one, else under the bank's name in the hand |
| `path` | 10 Steps on a curved path | one or two columns (the step, a note) | numbered circles alternately low and high on a teal curve (an empty drawing), the step in bold, the note in the hand |
| `compare` | 11 Two compared | a comparison; or a table of two columns | two things side by side, framed in teal and coral; each head (a comparison's words up to its first colon, `cmp-h`; or the column's label) a pill, the rest under it |

**Readable on a phone** (ADR 050 amendment (1); the owner's review of Word Order draft.3, 2026-11-01). Seven rules
for every board of a lesson in the teal look, checked on every board by `check_text_size.py` (the runner runs it on
the silent preview and the player):

1. **Minimum size**: in the 1600x900 frame, running text at least 26 px (2.9% of the frame) and a label at least 20 px
   (2.3%; the look sets labels at 2.4%); a line in the hand counts at its size divided by 1.3. Where content does not
   fit at that size, change the layout (two columns, fewer lines shown, the spotlight): never shrink the text. A
   table is never set under 2.9% (the fit's floor in this look); a long letter on its parts flows in two columns.
2. **The hand** only for the teacher's short notes (about 15 words at most) and labels; a longer note (`t-print`),
   a learner's sentences, a letter or a paragraph in print, the red pen's marks on top.
3. **No illustration unless it explains the point** (replaces ADR 021's picture on every board, in this look).
4. **Use the frame**: no board with a large empty half (the check: at its fullest, no more than 40% of its height
   or width empty); size the content up, or use the room for the example the narration gives.
5. **Dimmed rows readable**: the spotlight dims a row with a lighter ground (a wash of the ground over its cells), never
   by greying its words; every line at 4.5:1 or more.
6. **Marks never hide words**: an underline under the words, a circle around them; on a solid tile or pill the
   narration marks with the pen's circle or line, never the marker's band.
7. **Headings**: never one or two words alone on a line (`text-wrap: balance`, and room enough).

**On the site's player too** (ADR 050 amendment (2)): every board is checked on the site's own player
(`check_site_player.py`, runbook step 18c), which measures a board while it enters, does not serve the hand yet, and
keeps its own rules above the lesson's. So: a piece enters by growing inside its box, never from outside it; the hand
takes the line height of the face that draws it; nothing is drawn outside its block (a line between items lives inside
the items); no rule relies on changing what the site's `player.css` sets (`#cam`'s display, direction, wrapping and
gaps; a tight board's table padding).

**One face per set of equals** (the owner, 2026-11-01): items side by side as equals (recap cards, columns, pills,
steps) share face, size and weight: print for the set when any item is longer than a short note.

**Headings and labels in coloured rounded boxes** (the owner, 2026-11-01): the title in a teal band, the title
board's opening lines each in its own box, the paper's labels as solid pills, row labels on a soft tint, WRONG/RIGHT
and AS WRITTEN/PUT RIGHT as solid pills or panels, comparison heads as boxes, the board's title in a soft band.

Pattern 11 as a table (`compare`, two columns): two cards, each its place's head, its example sentences one under
another with the words in that place ringed in the pen (`block_accents`), its last row the rule in the hand.

**Accents and boards marked no-zoom** (ADR 049). `block_accents` (`{"<bundle block id>": ["phrase", ...]}`) names the words a layout sets in its accent colour: each phrase is found exactly once in the block's words, never split by a tag, and wrapped in a span `acc`, by a layout that draws it (`skeleton`: the purpose words, in the Purpose colour; green stays reserved for "right", §5); the words never change. `boards_nozoom` (`["<board id>", ...]`) names boards shown whole (`boards_fit` "whole") on which the style C zoom is not written either (§8g, rule 55): the whole table stays in view at every moment on every device, and the spotlight and the marks alone show the line being taught. For a table whose rows are to be seen together, as the ISBAR parts on one letter.

**The paper** (owner, 2026-10-27; ADR 045). A Writing lesson shows the paper wherever a board draws on it,
and always in this one look, so the learner knows it at once:

- **A guided look first.** Before a lesson takes a letter apart from a paper the learner has not seen, an
  authored section (ADR 018) walks through that paper once, whole, in its order and at a readable size:
  the date line, the setting, the patient details, the case notes and their sections, the discharge plan,
  the Writing Task box at the end, each lit by the spotlight as the teacher names it. Where the paper does
  not fit the frame, it is paged by its own parts (declared splits, §2: as many as its size needs).
- **Then the paper beside the letter.** Every board that says a part of the letter comes from the paper
  shows that piece of the paper (layout `paper`, three columns) beside the part of the letter it feeds,
  paired in time with the narration; a piece the narration names while teaching is a sheet in the working
  layer (two columns). Real text only, read from the sample's paper, never retyped. A line from inside a
  section carries its section's label; a heading over its first label ("PATIENT DETAILS:" over "Name:")
  sets the lines beside the labels they belong to; a row with no part of the letter is a piece of the paper
  alone.
- **Nothing named that is not on screen.** The narration never names a part of the paper, or points to a
  part of a letter, that is not on the board at that moment: a board that names one shows it, or does not
  name it (ADR 045 decision 5).
- The label column is as wide as its longest label; the paper's lines and the letter share the rest
  evenly. A sheet is zoomed as any Writing document (ADR 043 decision 7); the paper beside the letter is
  never zoomed, since a zoom onto one cell would take its pair out of view. Each such board is a board shown whole
  (`boards_fit` "whole", rule 52), so no device's camera zooms it either (ADR 045 amendment (1)). Where its
  pairs are too many to be read on one board, its table is divided by its rows over a declared split (§2).

**The criterion's card.** In a lesson about the OET Writing criteria, each section named after a
criterion takes the criterion's colour on all its blocks, and its term box "The criterion" is drawn as
the owner's slides draw a criterion: the monogram in a circle of the criterion's colour beside a pill
in its tint, the criterion's words in its colour.

Considered and not used in Writing 2: **a letter with notes beside the lines it discusses, with
arrows** (the owner's example). Notes on a table board go under the table (rule 12, ADR 020); putting
them beside it needs a new rule of the bundle and of the site's player, and it would narrow the letter,
which on a phone is already smaller than body size. The zoom brings the line being discussed to body
size instead, and the spotlight shows which line a note is about.

## 8. Marks

Clean and re-authored. Never copies of the instructor's ink.

| Mark | Appearance |
|---|---|
| Underline | 2–3px, blue, directly under the phrase |
| Highlight | Amber, translucent, never hides the text |
| Circle | Thin blue ellipse around the phrase |
| Strike | Red line through the phrase |
| Pointer | Moves to a phrase and stays; never wanders |
| Typed text | Appears character by character in time with speech |
| Arrow | From one phrase to another, to show a relationship: a verb and the time marker it clashes with, the two halves of a contrast. Thin blue curve with a head. |
| Bracket | Under a span of a sentence, blue, with end ticks |
| Replace | The wrong phrase struck through in red, the correction written above it in a handwriting-style face. The one place a second typeface appears. |
| Keyword pair (Reading lessons only) | `match1`, `match2`, `match3`: a highlight in sky blue `#0688F9`, violet `#A860FB` or yellow `#F9E806`, at 55% over the text. See §8e. |

A mark appears shortly **before** the word it belongs to, so the student
sees it and then hears about it.

**Style C** (ADR 042, revised at the owner's review of 2026-10-26): a highlight is the marker band of
§1a, a light amber `#ffe19c` behind the lower 38% of the line, swept in from left to right over 0.3 s;
a strike is `#b42318`, drawn from left to right over 0.25 s as the wrong phrase is named (§8g). The
other marks keep their blue. **The band is drawn behind the letters, never over them**: it is
multiplied with what is under it, so a letter stays as dark as it is and only its ground takes the
amber, on any card and in a lifted row. A multiply reaches the words only when nothing between the
band and the frame makes a group of its own (a positioned element with a z-index, an opacity under 1,
a transform, a filter): the band of 2026-10-26 sat in a marks layer with a z-index, so it was laid flat
over the lower part of the glyphs, and the owner saw the words covered. `check_marks.py` fails a style
C highlight whose band is not multiplied, is in such a group, or is taller than 40% of its line.

### The pointer follows reading

When the narration reads aloud text that is on the board, the pointer
moves along it **word by word, in time with speech**. This is derived, not
authored: the voice's word timings are matched against the words of the
blocks on the board, and each matched run drives the pointer. An explicit
point cue still works as before. The pointer rests when nothing is being
read or pointed at.

### Every reading and every relationship gets a mark

Every sentence read aloud and every relationship explained gets a mark.
The kind of mark fits what is being shown: a relationship is an arrow, a
wrong word is a strike or a replace, a key phrase is a circle or an
underline, a span is a bracket. On an error-correction page almost every
item is a clash between two parts of one sentence, and an arrow between
them shows it better than two separate underlines. Added 2026-09-23 after
the first board player used two kinds of mark six times in ten minutes.

### Marks are drawn whole and never touch their neighbours

- A mark whose phrase wraps onto two lines is drawn complete on every line
  (`box-decoration-break: clone`), never as two open halves.
- A circle is for one to three words. A longer span gets an underline or a
  bracket; the narration audit warns otherwise.
- A circle never overlaps the adjacent word: drawn in the overlay (§8a), its
  ring stops short of the nearest letter or digit on either side on its line
  (punctuation beside the phrase may sit inside it). Until 2026-09-26 the ring
  was inline padding and margin, which moved the words after it (§8a).
- The build measures every mark in a real browser at phone-landscape and
  laptop width (`check_marks.py`): a mark that touches neighbouring text
  fails the build, and a mark that breaks across lines is reported.

Found 2026-09-23 on page 13, board 3: "before he quit" circled as two open
halves, touching "years" and "before".

Marks belong to the working layer and are erased with it.

### 8a. Nothing about a board's state moves any text

Decided by the maintainer 2026-09-26, for every lesson, after the p15 letter
of Grammar 4 was seen re-wrapping ("runny nose" breaking differently) as the
spotlight, marks and typing changed. A word, once on a board, stays exactly
where it is until the board ends or its note is erased.

- **Spotlight and active styling** (row focus, the active cell, a verdict) use
  opacity, background, `outline` or `box-shadow` only: never a change of
  border width, padding, margin, font or size.
- **Marks are drawn in an overlay layer, never inline.** The phrase is wrapped
  only to be found; the ring, line, tint or bracket is drawn over it, measured
  from where the words already are.
- **Typed answers have their final width reserved from the start** (§7,
  Tables); the typing cursor takes no room in the line.
- **The frame's size never depends on what is shown around it**: a longer
  caption or review line under the frame must not shrink it, since every size
  in the frame is a share of its height.
- **Checked, not eyeballed**: `check_layout.py` drives the player to every
  moment at which a board changes and measures every word, at phone-landscape
  and laptop width; a word found at two positions on one board fails the build.
- **Style C's lift and zoom are not moves** (ADR 042): a lift scales the whole element about its
  centre and a zoom moves the camera; nothing reflows, re-wraps or changes size, and the element
  settles back. The checks measure the board at rest (`--sc-motion: 0`).

- **A block's text never changes structure while its board is shown**: every
  phrase a mark or a word colour will take is wrapped when the state is drawn,
  and marks only switch on and off. A wrapper, even one with no style, splits
  the text into runs shaped apart, which can re-break a line that fitted to a
  fraction of a pixel.
- **Fixed and pinned blocks hold their place**: where a state's working blocks
  come before them in the board's flow (change cards before a result), each is
  held at the lowest place it takes in any state of the board.
- **Nothing that stays is redrawn visibly** (owner, 2026-10-25, after the case-notes
  board of Writing 1 blanked like a camera flash at every new state, erase and clear).
  A board's core content stays on screen untouched for the whole topic; only what
  changes changes: a highlight moves, a note or a pop-up appears, side notes fade out
  when erased or cleared. Nothing that stays may disappear, dim, blink, fade in again
  or be drawn in motion again, and no image that stays is loaded again. A move to a new
  board may use the normal board transition. The reference player rebuilds a block's
  inside at a new state to re-wrap its phrases, so the new nodes take the old look (the
  row in focus, the active cell, verdicts, drawn parts, word colours, images) before the
  browser first styles them (docs/integration/note-for-site-board-flash.md).

The causes found and fixed on 2026-09-26, by the check:
1. The player's frame shrank when the review line under it wrapped: every
   word rescaled by a pixel or more, enough to re-break lines (Grammar 4's
   letter).
2. A circle's inline border, padding and margin pushed the words after it,
   and a note sized by its content grew and was placed again.
3. The typing cursor was an inline box.
4. The board area (`#cam`) was sized by what it held, so every block's width
   changed with the notes beside it (Grammar 1's tables).
5. A category card's text sat directly in a flex container with a gap, so a
   marked phrase became a flex item of its own (Grammar 1 and 2).
6. A mark's wrapper was a span, which the timeline's label styles reached.
7. A state's change cards, drawn before they appear, pushed the result below
   them down (Grammar 3, pages 4-5).
8. Wrapping a phrase when its word colour came on re-broke a line that fitted
   by 0.25 px (Grammar 3, page 7).

Before the fixes the check found 3,497 word moves on Grammar 4 alone; after
them, none in any of the four lessons.

### 8b. Every block fits the board

Decided by the maintainer 2026-09-27 (docs/adr/011-boards-fit.md), after a note
on Grammar 5 was pushed under the player controls. Every block shown lies fully
inside the board, in every state, at phone-landscape and laptop width, while
no word moves between states (§8a). Where a board cannot hold both, its layout
is re-planned, never left to overflow:

- **A pinned block takes room from the start of the state it appears in**, not
  from the board's start.
- **The layout counts a pinned block in every later state** of its board.
- **The fit**, measured in the player (`fit_boards.py`): where a note would
  not fit, the notes shown before it in its state are **cleared** as it appears
  (never a fixed or pinned block, never a note the narration still marks or
  reads); a board still too full is made **tight** on the whole board (half the
  gaps between blocks, then half the blocks' vertical padding); a table alone
  too tall gets smaller text, to the tables' floor (§7, Tables).
- **Checked, not eyeballed**: `check_overflow.py` fails any block outside the
  board or clipped, and any label drawn in capitals (§6).
- **On the device, the player's guard fits every board** (maintainer,
  2026-10-11; ADR 011 amendment of that date). The fit measures the phone and
  laptop frames with the fonts of the machine it runs on; a smaller frame (a
  phone held landscape, 915x412, whose controls keep 44 px, §9) or a wider
  device font can leave a block under the header or the control bar, or past an
  edge. On every board of every lesson the player measures again on the device,
  ahead of the board while the lesson plays (2026-10-12; else when the board is
  first drawn) and whenever the frame's size or the fonts change, at the moments
  `check_overflow.py` measures. Where any block would lie
  outside the board, or a word would spill out of its block: first the board's
  pictures are set smaller, scaled whole and never cropped, to no less than 10%
  of the frame (§7e), where that helps; then every block of the board together,
  its layout and proportions kept, until everything fits, never below the
  floors: body text 2.6% of the frame (as the Part B question column, §7g), a
  table's text 1.9% (§7, Tables; a table stops there while the other blocks go
  on; one board excepted, owner 2026-10-12, §7, Tables), a picture 10%.
  The size holds for the whole board, so nothing moves between its states
  (§8a). Where the board fits, the guard changes nothing. A Part B or Part C
  question board keeps its own guard (§7g, §7h). `check_wide_font.py` proves it,
  with Verdana forced on every board at the three frames.

### 8c. The narration never says where something is

Decided by the maintainer 2026-09-27, after lesson 5's narration said "on the
left you can see the case notes, and on the right, one sentence" over a board
that stacks them. The boards are laid out anew, not as the original slides, and
differently on a phone and a laptop. So the narration never locates a thing by
its position (left, right, top, bottom, above, below, this side, side by side):
it names it by its label, header or words ("in the case notes", "in the
sentence", "in the Wrong column", "in the green answer").

A position word is used only where the board's layout keeps it on every
screen: a table's columns (left to right) and rows (top to bottom), the two
pieces of one clause diagram, the two sides of a change card drawn side by side
(or, stacked, one above the other), and a timeline's axis (the past to the left
of now). Even there, a column's header is better than its side. The narration
audit fails any other position word (`write_narration.position_findings`); a
number "below 38" and a "left knee" are not positions.

---

### 8d. Nothing is drawn over anything

Decided by the maintainer 2026-09-30, for every lesson (docs/adr/020-no-overlap.md),
after Grammar 8 showed a timeline over a table's text and a timeline's labels
over each other. In every state, at phone-landscape and laptop width, no block
overlaps another block, and no text is drawn over other text (a diagram's
labels, a table's cells). Side notes go under their table (§7, Tables);
timeline marker labels that would meet take further lines under the axis.
One exception (maintainer, 2026-10-08; §7g): on a Part B question board, a gloss
that does not fit beside the question is drawn over the foot of the question
column, briefly, never over the extract or another note.

- **Checked, not eyeballed**: `check_overlap.py` drives the player to every
  moment at which a board changes and measures every block and every line of
  text; any overlap fails the build. It runs on the finished player and on the
  silent preview before the narration gate.

### 8e. Reading lessons: keyword pairs and the skimming path

ADR 026; bundle 1.13 (docs/04-LESSON-BUNDLE.md rules 29 and 30).

- **A pair shares one colour, and the colour means only "these words
  correspond".** A question's keywords and the words in the text that match
  them take the same pair mark, in the same state, the question first. When
  the answer is found, the text's wording and the answer's wording take one
  pair colour (the paraphrase bridge). At most three pairs a board: `match1`
  for the first, `match2` for the second, `match3` for a third.
- **The colours were chosen by measured difference** (CIEDE2000), as the word
  classes were (§7c): 25.3 or more between any two, and 26 or more from red
  and green and their tints, so a pair never reads as right or wrong.
- **On a question board the amber highlight is not used**: the yellow pair is
  only 14.9 from it, so keywords and their matches are always pair marks.
- **Every phrase read from a text is marked** (maintainer, 2026-10-06): a
  `highlight`, or a keyword pair on a question board, on exactly the words
  read, timed to the moment they are spoken. One mark per phrase.
  `check_doc_marks.py` checks it against the voice's word timings.
- **The skimming path is highlighted** (maintainer, 2026-10-06: "use yellow
  highlighting, as the instructor does"). On a skimming board (a practice-set
  text with no question) the parts skimmed, such as a heading, a first sentence
  or a number, take the `highlight` mark in reading order as the spotlight
  moves, never an underline or a circle. A skimming board has no pairs, so the
  highlight and the yellow pair never meet on one board.
- Pair marks are refused outside Reading lessons by the narration audit.

### 8f. Reading Part C: opinion-signal marks

ADR 026 (amendment of 2026-10-08); bundle 1.17, rule 38.

| Mark | Kind | Colour | Line | Label |
|---|---|---|---|---|
| `sig_opinion` | an opinion word: believe, think, argue, claim, say | indigo `#2B006B` | solid | opinion word |
| `sig_hedge` | a hedge: likely, probably, may, seems | teal `#006B60` | dashed | hedge |
| `sig_judge` | a word of emotion or judgement: unfortunately, worryingly | maroon `#6B0020` | dotted | judgement |
| `sig_main` | the main clause that holds the view | brown `#6B4B00` | with end ticks | main clause |
| `sig_aside` | a subordinate clause beside it | none: dimmed under a white veil | none | none |

- **Colour never carries the meaning alone**: each kind has its own line pattern and a
  small label, white on its colour, above the phrase's first line.
- **Chosen by measured difference** (CIEDE2000), as the word classes and the keyword
  pairs were: 28.8 or more between any two, and from the keyword pairs, the amber
  highlight, red, green, their tints and the marks' blue; dark enough for white label
  text (4.5:1 or better).
- **Room for the label**: a block that a signal mark names keeps line height 1.75 on its
  whole board, so the label sits between two lines and nothing moves when it comes
  (§8a).
- The narration says what each signal shows, and whose view a reported verb gives
  ("patients say", "some doctors argue") when it is not the writer's.

### 8g. Motion and effects (style C)

Decided by the owner on 2026-10-26 (issue #46; ADR 042): fade, zoom or enlarge, shrink and the like,
so the learner sees where to look. **Every motion is short (150 to 400 ms), eased, never bouncy, tied
to the narration's own times like a reveal, and switched off under `prefers-reduced-motion`.** A seek
shows the correct state at once.

| Effect | What it does | Driven by |
|---|---|---|
| Soft appear | a new block fades in and rises 1.2% of the frame (0.3 s) | its reveal; `blocks.css` |
| Fade | on a table board, the rows other than the one being taught at half strength | the spotlight (rule 11); `blocks.css` |
| Lift | the element being discussed takes a soft neutral shadow and grows a very little (0.4% for a full-width row, 1% for a block, 1.5% for a tile or a card, 2% for a contents item), inside the table's or the board's edges, with no outline, and settles back when the narration moves on (0.25 s); a row lifts as one row, its cells keep their tints (owner's review, 2026-10-26) | a table row: the spotlight; a block: the state's `effects` (bundle 1.22, rule 54) |
| Zoom | the view zooms onto a line of a document while the narration is on it, and back out (0.35 s), at the scale that sets the line at body size, never above 2.2, only as far as every note shown stays in view | the state's `effects` (rule 55) |
| Strike drawn | a strike is drawn across the wrong phrase from left to right as it is named (0.25 s) | the strike's time (rule 53) |
| Marker sweep | a highlight sweeps in from left to right (0.3 s) | the highlight's time (rule 53) |
| Shrink | a note that goes, by an erase or a clear, fades and shrinks (0.25 s); a cleared note's room closes up instead of jumping | the erase and the clear (rule 53) |

**Where each effect is used.** Where it helps the learner follow, not everywhere; the builder writes
the effects with data (`style_c.effects`), deterministically:

- **Every board**: soft appear for its notes; shrink for notes that go. A fixed block never moves.
- **The contents board**: each item soft-appears and is **lifted while it is named**, from its reveal
  until the next is named (the last until the end of what is said with it, its sections named one by
  one included, ADR 043). At the end every item is at rest.
- **A table board** (case notes, a letter, a criteria table): the row being taught is **lifted**, the
  others **faded**; at each row's end the whole table shows again (§7, Tables).
- **A document set well under body size** (its text 2.8% or less, or a board shown whole), in a
  Writing lesson (a letter, case notes; ADR 043): the **zoom**, from a mark the narration draws on a line until it moves on to a note or its sentence
  ends; a later mark takes the view on. Where the line is as wide as the board, or a note shown would
  leave the view, the zoom is as small as it must be, or none. A board the lesson marks no-zoom
  (`boards_nozoom`, ADR 049) takes none: shown whole, it stays whole, its spotlight and marks alone showing
  the line.
- **A board with two or more fixed sentences or cards** (two openings side by side, an opening and
  its comparison): each is **lifted while the narration reads it**.
- **Wrong phrases**: the **strike is drawn** as each is named. **Key words**: the **marker sweeps**
  in.
- Never: on a picture, on a gloss's parts (they are written in, as before), or two lifts at once.
- **The teal look** (ADR 050, §1b): a fixed block **enters** as its board opens (it fades in and rises 1.6% of the
  frame, 0.45 s), and a pattern's pieces (§7k: rows, tiles, pills, steps) enter **in reading order**, 70 ms apart,
  0.4 s each, before the narration reaches them; its marks are the teacher's red pen (a circle drawn whole at its
  time: drawing it on in motion needs both players, ADR 050).
- **Not the style C zoom** (ADR 043): a Grammar or Vocabulary table keeps rule 13's auto zoom (Grammar
  6's board shown whole keeps no zoom, the owner's 2026-10-12 exception); a Reading text keeps its lens,
  map and covering, a Listening transcript its box (ADR 026, ADR 030).

## 9. Controls

- Play/pause, progress bar, elapsed time. Nothing else inside the frame;
  the website page around it may carry more (§1).
- Contents list reachable from the header, one entry per **section**,
  never per board or topic. The
  student can jump forward or back and return to where playback reached.
- **On touch, every control is at least 44px.** The control band grows
  proportionally on small screens. The board is what lies above it: the fit and the
  checks measure the board between the header and the control band as drawn,
  on a phone held landscape (915x412) too (2026-10-08). Where a board does not
  fit there, the player's guard fits it on the device (§8b; 2026-10-11).
- Controls are neutral grey and must not compete with the teaching.

---

## 10. Never on a lesson screen

- Logo, product name, domain, any branding
- A per-screen title. Titles belong to topics, not to units of space.
- Decoration with no teaching purpose: gradients, shadows,
  illustrations, photographs, background images. Style C's marker band and the shadow of the
  active element (§1a) carry meaning: where to look
- Colours other than the four content colours, the four family colours
  and the board style's colours (§7c), and in style C its own (§1a: the handouts' tones by meaning,
  the six criteria's colours)
- Type smaller than the stated proportions
- Board shorthand. "One moment + since 2010 = clash" is a note to
  oneself, not prose an elementary student reads.
- A caution about tone or register. That belongs to narration.
