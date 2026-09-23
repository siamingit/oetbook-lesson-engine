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
- Background: **white**.
- Mood: **clinical and serious**. Calm, precise, uncluttered. Not
  playful, not decorative.

### Vertical division

| Band | Height | Contains |
|---|---|---|
| Header | ~8% | Topic number, topic title |
| Content | ~84% | The board |
| Controls | ~8% | Play/pause, progress, elapsed time |

The header is deliberately small. The student reads it once; they look
at the content for minutes.

### Margins

5% of frame width on each side. Phone screens have rounded corners and
intrusions; content must not sit at the edge.

---

## 2. The board — the central model

**A lesson is a sequence of boards. One board per topic.**

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

### Topics

A topic is **a unit of navigation** — an entry in the contents list the
student can jump to.

- Three to seven topics per page of source material.
- Never one topic per teaching beat.
- On an exercise page: the introduction, then one topic per exercise
  item. Everything about an item — spotting the fault, the explanation,
  every accepted answer, and the rule drawn from it — belongs to that
  item's topic.
- The introduction shows the full set of exercise items before they are
  worked through one by one, so the student can attempt them first.

---

## 3. Density

The working layer holds **at most about four notes at once** before it
needs erasing. The fixed layer counts against the space it occupies.

The binding test is **phone-landscape width, not desktop**. If a board
is not comfortably readable there, erase sooner. It is never solved by
reducing the type size.

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
| Comparison | Two items side by side. Equal columns, hairline between. | working |
| Plain block | A statement or rule with no correctness value. | either |

An answer row never stands alone: it is accompanied by a plain or term
block saying why it is right.

### Tables

Tables are taught, not displayed.

- Rows appear in time with the narration, not all at once.
- A row not yet reached is shown at reduced opacity, not hidden.
- The row being discussed is at full opacity.
- A table too large for the frame is split by meaning at a natural
  boundary — never mid-row, never mid-idea. A split table is a fixed
  layer that changes with the topic, not an erasure.

---

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

A mark appears shortly **before** the word it belongs to, so the student
sees it and then hears about it.

Marks belong to the working layer and are erased with it.

---

## 9. Controls

- Play/pause, progress bar, elapsed time. Nothing else.
- Contents list reachable from the header, one entry per topic. The
  student can jump forward or back and return to where playback reached.
- **On touch, every control is at least 44px.** The control band grows
  proportionally on small screens.
- Controls are neutral grey and must not compete with the teaching.

---

## 10. Never on a lesson screen

- Logo, product name, domain, any branding
- A per-screen title. Titles belong to topics, not to units of space.
- Decoration with no teaching purpose: gradients, shadows,
  illustrations, background images
- More than the four colours above
- Type smaller than the stated proportions
- Board shorthand. "One moment + since 2010 = clash" is a note to
  oneself, not prose an elementary student reads.
- A caution about tone or register. That belongs to narration.
