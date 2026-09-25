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

- **One board per original slide.** Teaching beats become working-layer
  states with erasures, never boards.
- **Exception, exercise slides:** an introduction board showing all the
  items, then one board per item, as on page 13.
- **Exception, oversized fixed content:** a board is split only when its
  fixed content cannot fit the frame at phone-landscape width, such as the
  full tense table on page 6, and then **by meaning** (past / present /
  future), never by beat.

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
reducing the type size.

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

Three content colours, one highlight. No more.

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
headers, never on error or answer rows. Present-perfect teal and
"correct" green must never be confused; that is why they differ.

---

## 6. Typography

- One sans-serif family throughout.
- **Two weights only:** regular and medium. Never heavy.
- **Sentence case** everywhere. Every block, and every side of a
  comparison, starts with a capital.
- Small labels may be caps with wide letter-spacing at small size.
- No italics for emphasis; use colour and underline, as a teacher marks
  a board.

---

## 7. Content blocks

| Block | Use | Layer |
|---|---|---|
| Error row | A wrong sentence. Red tint, ✕, left bar. | usually fixed |
| Answer row | A correct sentence. Green tint, ✓, left bar. | working |
| Term box | A new word or phrase with its explanation. Blue tint, small label. | working |
| Gloss | A hard general English word with a very short gloss beside it (§7b). A term box labelled WORD, drawn on one line. | working |
| Comparison | Two items side by side. Equal columns, hairline between. | working |
| Plain block | A statement or rule with no correctness value. | either |
| Category card | Coloured header strip with a label, and a body. For tense families and for comparing categories. Header in the family colour, or neutral grey for a category that is not a tense. | working |
| Timeline | A diagram on a time axis: tense arrows, reference markers, event series, pointer arrows, callout boxes (and plain points and periods), each in a family colour. Structured data only; code draws it, part by part as the narration reveals them (§7a). | working, or fixed on a diagram slide |
| Callout | Two kinds only. Warning: red circle with "!" on an amber tint. Key rule: blue circle with "i" on a blue tint. | working |
| Table | A tense table with its header row coloured by family. | working, or fixed on an explanatory topic |

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
- No photographs, no illustrations.
- Every element stays legible at phone-landscape width.
- Narration reveals and marks these like any block, and the reading
  pointer follows the text inside them.

### Tables

Tables are taught, not displayed.

- Rows appear in time with the narration, not all at once.
- A row not yet reached is shown at reduced opacity, not hidden.
- The row being discussed is at full opacity.
- A table too large for the frame is split by meaning at a natural
  boundary — never mid-row, never mid-idea. A split table is a fixed
  layer that changes with the topic, not an erasure.
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

Recorded 2026-09-25 (docs/00-PRODUCT.md §3, "Hard general words are
glossed"). A gloss explains a hard **general** English word the first time
it appears: never a clinical word, never a grammar term (grammar terms get
a term box with a plain definition, as before).

- **Data:** a term box with the label `WORD`, the word as it appears as its
  `term`, and the gloss as its `explanation`: a simpler synonym or a few
  plain words, no more than about five ("plan a time"; "a change to make it
  work better"). No icon. No new block type and no new field: the bundle
  contract is unchanged, and a renderer that knows nothing of glosses still
  shows the label, the word and its gloss.
- **Look:** on one line, "schedule (= plan a time)": the word in the
  **medium** weight, the gloss in the **regular** weight inside "(= ...)".
  The term box's own blue family (§5, "Blue: teacher emphasis, new term"),
  with its small label above. No new weight and no new colour.
- **Layer:** working, like any note, placed where the word first appears
  and revealed as the narration says it.
- **Narration:** one short sentence as it appears: "Schedule means to plan a
  time for something."
- **Not overloaded:** only a word a learner at A2-B1 is likely not to know.
  A word glossed once is not glossed again later in the section.

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
- A circle carries horizontal padding and margin, so it never overlaps the
  adjacent word.
- The build measures every mark in a real browser at phone-landscape and
  laptop width (`check_marks.py`): a mark that touches neighbouring text
  fails the build, and a mark that breaks across lines is reported.

Found 2026-09-23 on page 13, board 3: "before he quit" circled as two open
halves, touching "years" and "before".

Marks belong to the working layer and are erased with it.

---

## 9. Controls

- Play/pause, progress bar, elapsed time. Nothing else inside the frame;
  the website page around it may carry more (§1).
- Contents list reachable from the header, one entry per **section**,
  never per board or topic. The
  student can jump forward or back and return to where playback reached.
- **On touch, every control is at least 44px.** The control band grows
  proportionally on small screens.
- Controls are neutral grey and must not compete with the teaching.

---

## 10. Never on a lesson screen

- Logo, product name, domain, any branding
- A per-screen title. Titles belong to topics, not to units of space.
- Decoration with no teaching purpose: gradients, shadows,
  illustrations, photographs, background images
- Colours other than the four content colours and the four family
  colours above
- Type smaller than the stated proportions
- Board shorthand. "One moment + since 2010 = clash" is a note to
  oneself, not prose an elementary student reads.
- A caution about tone or register. That belongs to narration.
