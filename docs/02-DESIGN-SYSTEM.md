# Design System — Lesson Screens

How a lesson screen looks. Binding for every lesson.

Agreed with the maintainer 2026-09-22 against a worked example of the
Grammar 1 error-correction content, reviewed at both desktop and phone
width.

This document covers the teaching surface only. Product brand, name,
domain and logo are not decided and **do not appear on lesson screens**.

---

## 1. The frame

- **Fixed 16:9.** Never a scrolling canvas.
- Fills the viewport in fullscreen. On a phone: landscape.
- All content sits inside the frame. No side panel, no board, nothing
  outside it.
- Background: **white**.
- Mood: **clinical and serious**. Calm, precise, uncluttered. Not
  playful, not decorative.

### Vertical division

| Band | Height | Contains |
|---|---|---|
| Header | ~8% | Topic number, topic title |
| Content | ~84% | Everything being taught |
| Controls | ~8% | Play/pause, progress, elapsed time |

The header is deliberately small. The student reads it once; they look
at the content for minutes. Content gets the room.

### Margins

5% of frame width on each side. Phone screens have rounded corners and
intrusions; content must not sit at the edge.

---

## 2. Sizing is relative, never fixed

Every size is expressed as a proportion of the frame, not in pixels.
The same screen must hold together on a laptop and on a phone in
landscape.

Reference proportions, as a share of frame height:

| Element | Share |
|---|---|
| Body text | ~3.2% |
| Topic title | ~4% |
| Small label (e.g. "NEW WORD") | ~2.4% |
| Block padding | ~1.8% vertical, ~2.5% horizontal |
| Gap between blocks | ~2.5% |

Line height 1.35 for body text in blocks.

---

## 3. Density limit

**Maximum six content blocks per screen.** Fewer for long sentences.

The binding test is **phone-landscape width, not desktop**. If a screen
is not comfortably readable there, the content splits across two
screens. It is never solved by reducing the type size.

A topic may run across several screens. It must not break mid-thought:
carry enough context onto the next screen to stay coherent.

---

## 4. Colour

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
Never reuse a colour for a second purpose.

**Colour is never the only signal.** Every coloured block also carries a
non-colour marker: a ✕ or ✓ icon and a left accent bar. Required for
colour-blind students and for viewing in bright light.

**Tint, not saturation.** Blocks use a pale fill with a 2–3px left accent
bar, never a strong coloured background. Text stays fully legible.

**Text on a tint uses the darkest stop of the same family.** Never black,
never grey.

---

## 5. Typography

- One sans-serif family throughout.
- **Two weights only:** regular and medium. Never heavy.
- **Sentence case** everywhere. Never Title Case, never all caps —
  except small labels, which may be caps with wide letter-spacing at
  small size.
- No italics for emphasis; use colour and underline, which match how a
  teacher marks a board.

---

## 6. Content blocks

| Block | Use |
|---|---|
| Error row | A wrong sentence. Red tint, ✕, left bar. |
| Answer row | A correct sentence. Green tint, ✓, left bar. |
| Term box | A new word or phrase, with its explanation. Blue tint, small label above. |
| Comparison | Two items side by side. Equal columns, hairline between. |
| Plain block | Statement or rule with no correctness value. No tint. |

### Tables

Tables are taught, not displayed.

- Rows appear in time with the narration, not all at once.
- A row not yet reached is shown at reduced opacity, not hidden — the
  student can see where the explanation is going.
- The row being discussed is at full opacity.
- A table too large for one screen splits across screens by meaning, at
  a natural boundary — never mid-row, never mid-idea.

---

## 7. Marks

Clean, re-authored. Never copies of the instructor's ink.

| Mark | Appearance |
|---|---|
| Underline | 2–3px, blue, directly under the phrase |
| Highlight | Amber, translucent, never hides the text |
| Circle | Thin blue ellipse around the phrase |
| Strike | Red line through the phrase |
| Pointer | Moves to a phrase and stays; never wanders |
| Typed text | Appears character by character in time with speech |

A mark appears shortly **before** the word it belongs to, so the student
sees it and then hears about it — as in a real classroom.

---

## 8. Controls

- Play/pause, a progress bar, elapsed time. Nothing else on the bar.
- Contents list reachable from the header, giving every topic in the
  lesson; the student can jump forward or back and return to where
  playback had reached.
- **On touch, every control is at least 44px.** The control band grows
  proportionally on small screens to allow it.
- Controls are neutral grey. They are not part of the teaching and must
  not compete with it.

---

## 9. Never on a lesson screen

- Logo, product name, domain
- Any branding
- Decoration with no teaching purpose: gradients, shadows, illustrations,
  background images
- More than the four colours above
- Type smaller than the stated proportions
