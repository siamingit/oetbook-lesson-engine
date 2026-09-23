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

### Contents and navigation

Every lesson has a **contents list**, derived automatically from the
teaching content — not from the original slide boundaries.

The student can move forward and back between topics freely, and return
to where playback had reached.

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
  English.
- **What you will learn** — built from the topic titles of every board
  in the lesson.

Both are generated after all other boards exist, since the second
depends on them. Neither carries Persian, a logo or a product name.

They teach nothing, but they prepare the student for the lesson, so they
are part of it.

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
