# Product Definition — English Interactive Lesson

What we are building. Everything else in this repository serves this
document. When a pipeline decision and this document disagree, this
document wins.

Written 2026-09-22, after building ten pages of Grammar 1 and reviewing
them with the maintainer. It exists because its absence caused four
rebuild cycles: visual density, student level, pipeline order, and page
classification were all discovered by review rather than defined up front.

---

## 1. What a lesson is

One recorded Persian session becomes **one English lesson**.

A lesson is an interactive page, not a video file and not a slide deck.
It plays: narration in English, with content appearing on screen in time
with the speech.

### Frame

- **Fixed 16:9.** Not a scrolling canvas.
- Can go fullscreen.
- On a phone: landscape, filling the screen.
- Content lives inside the frame. There is no side panel, no board
  beside the slide, nothing outside the 16:9 area.
- That rule is about the **lesson frame itself**: the lesson's teaching
  content never spills out of it. The website page the frame sits on is a
  different thing, and may have panels and controls around it: a contents
  panel, progress, resume, an AI chat about the lesson. Clarified by the
  maintainer 2026-09-24; the page is built later, around the lesson bundle
  (docs/04-LESSON-BUNDLE.md).

### Boards within a lesson

A lesson is a sequence of **boards**. One board per topic.

A board is what the original slide was: a stable surface the teacher
works on for as long as the topic lasts. It is not a page that fills up
and is replaced.

Each board has two layers:

- A **fixed layer** — the topic's own content, authored once, never
  erased while the topic is active. On an exercise topic this is the
  sentence under discussion; on an explanatory topic it is the table,
  forms or examples the topic is about.
- A **working layer** — the notes and marks added while explaining.
  These accumulate, are erased when the space fills, and accumulate
  again in the cleared space.

Erasing the working layer never changes the title, the topic, or the
fixed layer. It is how a teacher uses a board, and the source lessons do
it constantly.

A board ends when its topic ends — never because space ran out.

A topic is a unit of navigation, not a unit of space. Three to seven per
page of source material. Never one per teaching beat.

### Lesson structure

Revised 2026-09-23. An earlier version of this section said the contents
list is derived from the teaching content, not from slide boundaries. That
is reversed: **the maintainer's slide titles are his structure for the
lesson, and they win.**

- **Lesson**: titled from the deck's own lesson title.
- **Sections**: one per original slide, titled with that slide's own
  heading, corrected for registered deck defects ("Time Makers" → "Time
  Markers", "Passive vs Active from" → "form"). Two consecutive slides
  that share a heading are one section.
- **Boards**: steps inside a section. They have **no titles of their
  own**, ever.

Where the deck has a **contents slide**, its groupings are a level above
sections: **category → section → boards**. The categories are the
maintainer's own, translated and corrected, recorded as source-derived
from that slide, and they order the contents menu and the contents board.
Grammar 1's contents slide gives five: verb tenses and their uses; simple
past and present perfect with time markers; signal words and verb tenses;
active and passive; practice writing case notes. A deck without a contents
slide has sections only. Recorded 2026-09-24.

A slide whose heading is not a title for its content (a table's column
labels, an image slide with no text) is listed for the maintainer to
title, never guessed.

### Contents and navigation

Every lesson has a **contents list** of its sections, and nothing
smaller. The student can move forward and back between sections freely,
and return to where playback had reached.

---

## 2. Content is authored, never copied

Screens are built as web content: real text, laid out for this product.

The original deck is a **source of teaching content only**. Its images
are not used as backgrounds, its layout is not reproduced, and its text
is not pasted in.

This follows from a defect found in review: deck typos were carried into
the lessons, and in places the narration explained an error that a
corrected deck would no longer contain.

### Order

```
Persian recording
      ↓
transcript, teaching content, annotation evidence
      ↓
corrected, redesigned screen content      ← first
      ↓
English narration written from it         ← second
```

Screen content is settled **before** the narration is written. Writing
narration against uncorrected material produces lessons that must be
rebuilt.

### Errors in the source

- Deck errors are corrected when the screen is authored, and recorded in
  the lesson's deck-defect register.
- Deliberately wrong sentences used as exercise material are **not**
  errors. They are content and are reproduced exactly.
- Teaching that exists only because the deck was wrong — the instructor
  pointing out a typo aloud — is dropped, not translated. It teaches
  nothing once the error is gone.

---

## 2a. Title and contents boards

Two boards are not written from a single page of source material.

- **Title board** — the lesson title and a one-line description, in
  English. The description is the maintainer's own words, recorded in
  `sections.json` (`build_sections.py --description`) with provenance
  `maintainer`; for Grammar 1: "Learn the verb tenses, when to use each
  one, and how to use them in your OET writing." (2026-09-24).
- **What you will learn** — built from the topic titles of every board
  in the lesson.

Both are generated after all other boards exist, since the second
depends on them. Neither carries Persian, a logo or a product name.

They teach nothing, but they prepare the student for the lesson, so they
are part of it.

### Every lesson opens with a narrated introduction

Decided by the maintainer 2026-09-24, after the silent preview of Grammar 1
jumped straight into verb tenses. His recorded sessions always open with a
greeting, what the lesson covers, and a quick walk through the contents
while the contents are on screen. A rule for every lesson:

- The lesson opens with the **title board** and the **contents board**,
  both narrated.
- The narration greets the student, says what the lesson is about, and
  walks through the categories. Each category on the contents board is a
  block that is revealed as it is named.
- Short: about one to two minutes.
- The voice is not the instructor's. It never gives the instructor's name
  and never speaks as him: a plain greeting.
- The source is the understanding of the contents slide's interval, written
  under the same rules as every section: student level, provenance, visual
  anchors, no references to the source. Two QA passes.

---

## 3. Students

Healthcare professionals preparing for OET. **Elementary general
English, roughly A2–B1.**

They know clinical vocabulary. They do not have advanced general English.

- Simplest words that carry the meaning. Everyday English, not academic.
- Short sentences, one idea each.
- Medical and grammar terms are fine: hypothyroidism, present perfect,
  past participle. Difficult general English is not.
- A grammar term is defined in plain words the first time it appears.
- Show an example first, then name the rule.

---

## 4. Teaching feel

The lesson must feel like a teacher teaching, not a narrated document.

### Every teaching moment has a visual anchor

- A new word or phrase is **written on screen**, not only spoken. Write
  it, pause, then explain it.
- An extra example given aloud appears on screen as it is said.
- A key term, form or rule worth remembering is written down.
- A contrast between two things is shown as two things, side by side.
- Never more than about fifteen seconds of speech with nothing
  happening on screen. A stretch with nothing to show means the
  explanation itself needs an example.

### Pauses are teaching

- After a question to the student, a pause long enough to think.
- After writing something new, a pause for the eye to catch up.
- Pause lengths are chosen per moment, not fixed.

### Timing

A mark appears shortly **before** the word it belongs to, so the student
sees it and then hears about it — as in a real classroom.

### Marks

Clean and re-authored, never copies of the instructor's ink. Translucent
highlight that does not hide text. Precise underlines. Typed text
appearing in time with speech. A pointer that moves only when pointing
at something, and otherwise stays still.

---

## 5. Voice

A stock native British English voice, not a clone of the instructor.

Reasons: source audio is not of cloning quality, and a cross-lingual
clone carries the source-language accent — a Persian-accented voice
teaching English pronunciation to international healthcare workers is a
product contradiction.

- Pace around 130–140 words per minute. These are non-native listeners.
- Medical terms pronounced correctly; a pronunciation dictionary where
  the voice gets one wrong.
- The same voice across every lesson. It becomes the product's voice.

`OPEN`: how the instructor's identity is carried instead — his name and
face on the page, and possibly intros recorded in his own voice.

---

## 6. What must never appear

- Any reference to the original recording: "the video", "pause the
  video", "this session", "the class"
- Any reference to Persian, translation, or an original lesson
- Any pointer to material the student does not have: a coursebook,
  another product
- Claims about how formal, common, natural or preferred a word is,
  unless the instructor said so. Teach what is correct and what is
  wrong. Register advice comes from the maintainer and is marked as
  such.
- Grammar rules, exam facts or clinical facts not in the source, unless
  supplied by the maintainer
- Persian-market branding: the OETbook.ir logo, Persian text, the
  Persian copyright slide

---

## 7. Branding

The international product is a rebrand. Visual style is new.

`OPEN`: the brand, name and domain for the international product are not
decided. Screen design cannot be finalised until they are.

---

## 8. Not in scope yet

Recorded as deliberate exclusions, not oversights:

- **Exercises and practice.** A separate, later product. Lessons are
  watch-and-listen for now. The data model should not block them.
- Student accounts, progress tracking, payments
- The marketing site
- Video export

---

## 9. Open decisions

| # | Decision | Status |
|---|---|---|
| 1 | International brand, name and domain | not decided — blocks screen design |
| 2 | How screen content is authored: generated from a design system, or hand-made | not decided |
| 3 | Who reviews the English before publishing | not decided — see below |
| 4 | How the instructor's identity is carried without his voice | not decided |

### On review

Ten pages produced 41 critical QA findings — about four per page of
content that would have been wrong for a student. Automated QA caught
them, but the second pass was never clean on any page, so the last fixes
on every page remain unreviewed by any model.

A native-English reviewer with OET knowledge is **not optional**. Until
that is resourced, no lesson should be published.
