# Design System — Lesson Screens

How a lesson screen looks and behaves. Binding for every lesson.

Agreed with the maintainer against worked examples from Grammar 1,
reviewed at desktop and phone width. Revised 2026-09-23 after the first
build produced sixteen titled screens for one topic and the maintainer
identified the layout model as wrong.

This document covers the teaching surface only. Product brand, name,
domain and logo are not decided and **never appear on lesson screens**.

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
- Background: **white**.
- Mood: **clinical and precise, and visually rich**. Calm, uncluttered,
  never playful. Colour, badges, cards and timelines are used freely,
  and **colour always carries meaning**: nothing on a board is
  decoration. Revised 2026-09-23, approved against a mockup, to bring the
  boards closer to the instructor's original decks.

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
  built before this rule and is kept as accepted.

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

- One sans-serif family throughout.
- **Two weights only:** regular and medium. Never heavy.
- **Sentence case** everywhere. Every block, and every side of a
  comparison, starts with a capital.
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
  too full), in the board's flow; on a table board at the right under the
  table, the side notes beside it on its left.
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
  been read, their room taken from the start of that state (as a pinned block's,
  §8b), so the question column has room for the reading before them.
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

- **A block's text never changes structure while its board is shown**: every
  phrase a mark or a word colour will take is wrapped when the state is drawn,
  and marks only switch on and off. A wrapper, even one with no style, splits
  the text into runs shaped apart, which can re-break a line that fitted to a
  fraction of a pixel.
- **Fixed and pinned blocks hold their place**: where a state's working blocks
  come before them in the board's flow (change cards before a result), each is
  held at the lowest place it takes in any state of the board.

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

## 9. Controls

- Play/pause, progress bar, elapsed time. Nothing else inside the frame;
  the website page around it may carry more (§1).
- Contents list reachable from the header, one entry per **section**,
  never per board or topic. The
  student can jump forward or back and return to where playback reached.
- **On touch, every control is at least 44px.** The control band grows
  proportionally on small screens. The board is what lies above it: the fit and the
  checks measure the board between the header and the control band as drawn,
  on a phone held landscape (915x412) too (2026-10-08).
- Controls are neutral grey and must not compete with the teaching.

---

## 10. Never on a lesson screen

- Logo, product name, domain, any branding
- A per-screen title. Titles belong to topics, not to units of space.
- Decoration with no teaching purpose: gradients, shadows,
  illustrations, photographs, background images
- Colours other than the four content colours, the four family colours
  and the board style's colours (§7c)
- Type smaller than the stated proportions
- Board shorthand. "One moment + since 2010 = clash" is a note to
  oneself, not prose an elementary student reads.
- A caution about tone or register. That belongs to narration.
