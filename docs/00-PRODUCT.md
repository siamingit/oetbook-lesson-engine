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
- **Authored sections** (maintainer, 2026-09-29; docs/adr/018-authored-sections.md):
  at the maintainer's request a lesson may add sections the recording does not
  teach, after the deck's, with the maintainer's titles. Everything in them is
  `authored`, written from the agent's plan; the recorded and authored parts
  are the lesson's two categories.
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
  Their intended error is reproduced exactly; accidental typos and
  year-dependent relative times in them are corrected (methodology §24).
- Teaching that exists only because the deck was wrong — the instructor
  pointing out a typo aloud — is dropped, not translated. It teaches
  nothing once the error is gone.
- **People's names that sound like other words are renamed** (maintainer,
  2026-09-27: the patient "Yuri Nation" sounded like "urination" and became
  "David Harper"). A name that, spoken, sounds like another word or phrase,
  or could embarrass or distract a learner, is replaced by a plain, plausible
  name, on screen and in speech, through the deck-defect register. The
  preflight pack lists every name for the source gate; the terms check hears
  every name, and one heard as other words is listed at the final gate; QA
  reports one as a major finding (ADR 017).

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
- The narration always starts with a warm greeting and welcome, like a
  teacher talking to their own students ("Hello again, and welcome back. I
  hope the course has been useful for you so far. Today we're going to look
  at another important part of grammar."), in wording that varies from lesson
  to lesson; then it links to another lesson, usually the previous one (course
  index), without assuming the student has taken it, says why the
  topic matters for their letters and what they will be able to do by the
  end, and walks through the categories. Each category on the contents board
  is a block that is revealed as it is named. Short sentences, simple words, a
  friendly tone (A2-B1). The board shows what the narration describes, not
  only the title. Only the exact same opening sentence as another lesson is
  forbidden: the narration audit fails it, and an introduction that does not
  open with a greeting and a welcome (maintainer, 2026-09-27;
  docs/adr/014-introductions-greet-then-link.md, superseding ADR 013's
  opening rule).
- **The first lesson of a course** (ADR 014 amendment, 2026-09-27) welcomes the
  learner to the whole course, explains simply why grammar matters in the OET
  letter (the reader is another health professional who needs clear, exact
  information; grammar is part of how the letter is assessed; no grade
  promises), says why its topic is the first step and starts the lesson. It
  never assumes earlier study.
- **No course map, no lesson count, no list of lessons**, in any lesson: the
  course is still growing (maintainer, 2026-09-27). Naming one other lesson
  where it helps is fine; the narration and screens audits fail a lesson count,
  and the narration audit an utterance that lists three or more lessons.
- **The contents board lists every section of the lesson by name**, authored
  sections included (maintainer, 2026-09-29): as its own item, or in its
  category's list. The contents walk-through in the narration names them.
  `build_lesson_boards.py` and the structural check (`check_board_page.py`)
  fail a board that leaves one out.
- Short: about one to two minutes.
- The voice is not the instructor's. It never gives the instructor's name
  and never speaks as him.
- The source is the understanding of the contents slide's interval, written
  under the same rules as every section: student level, provenance, visual
  anchors, no references to the original recording (a reference to another
  lesson of the product is kept, §6a). Two QA passes.
- A deck with no contents slide (Grammar 2): the source is the recording's
  opening minutes, whatever slide is on screen, up to where the teacher moves
  from greeting to teaching. The contents board lists one item per section.
  Decided by the maintainer 2026-09-24.

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

### Hard general words are glossed

Decided by the maintainer 2026-09-25, for every lesson type (grammar,
reading, listening, writing, speaking, vocabulary) from lesson 3 on. In
their own sessions the teacher explains hard words to the learner; the
lessons do the same, in English.

- Wherever a **general** English word would be hard for an A2–B1 learner
  (in Grammar 2, "schedule" or "modification"), it is explained briefly the
  first time it appears.
- Each gloss is a short teaching moment of its own, about fifteen seconds
  (maintainer, 2026-09-27; docs/adr/013-gloss-moments-and-teacher-openings.md):
  the word appears on the board and the narration says it clearly and
  pauses; a simple meaning, spoken and shown; a generated illustration where
  the word is concrete and a picture helps (a grazed palm, a wound being
  cleaned; ADR 015), none for an abstract word, and never a word pointing at
  it; one short example sentence, in a medical context where
  natural; a short pause, then the lesson goes on (docs/02-DESIGN-SYSTEM.md
  §7b). Which words are glossed is unchanged.
- **Never gloss medical words**: the learners are healthcare
  professionals and know them. Grammar terms keep their own rule above.
- **What a "medical word" is** (maintainer, 2026-09-25): specialist
  terminology: diseases, drugs, procedures, anatomy, usually Latin or Greek
  in origin (hypothyroidism, colonoscopy, warfarin). General words that are
  common in clinical settings (deteriorate, commence, schedule, improve) are
  general words: they are glossed when hard for an A2–B1 learner, like any
  other general word, and QA does not flag those glosses.
- Do not overload: gloss only words a learner at this level is likely not
  to know.
- **Vocabulary lessons go further** (maintainer, 2026-09-29;
  docs/adr/019-vocabulary-lessons.md): every key word gets a full gloss moment
  with an example from a medical letter (Writing) and one said to a patient
  (Speaking); the vocabulary is widened with the word family, common
  collocations and near-synonyms with the difference in use; general English
  for building sentences is taught too; every section has more examples, all
  `authored`. A key word that is a medical term is glossed with the words a
  patient would understand (docs/02-DESIGN-SYSTEM.md §7b).

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
- Initialisms (COPD, MRI, GP, IV, ECG, CT) said quickly and naturally, the
  letters run together as one group, like a native speaker; never letter by
  letter with gaps (maintainer, 2026-09-27; every lesson). The
  narration writes them "C-O-P-D" for the voice; the screen shows "COPD"
  (ADR 016; methodology §20).
- The same voice across every lesson. It becomes the product's voice.

`OPEN`: how the instructor's identity is carried instead — his name and
face on the page, and possibly intros recorded in his own voice.

---

## 6. What must never appear

- Any reference to the original recording: "the video", "pause the
  video", "this session", "the last session", "the class"
- Any reference to Persian, translation, or an original (Persian) lesson
- Any pointer to material the student does not have: a coursebook,
  another product. Another lesson of this product is not such material
  (§6a)
- Claims about how formal, common, natural or preferred a word is,
  unless the instructor said so. Teach what is correct and what is
  wrong. Register advice comes from the maintainer and is marked as
  such.
- Grammar rules, exam facts or clinical facts not in the source, unless
  supplied by the maintainer
- Persian-market branding: the OETbook.ir logo, Persian text, the
  Persian copyright slide

## 6a. References to other lessons are kept

Decided by the maintainer 2026-09-25 (docs/adr/006). The teacher often
points to other sessions: "this was taught in session one, verb tenses",
"if active and passive is still hard, review grammar sessions one and two".
These pointers are teaching, and they are kept, as references to the
English lessons of the product.

- **Allowed and wanted:** a reference to another lesson of the product, by
  its title. "You learned this in the lesson Verb Tenses." "If the passive
  forms are still hard, look again at the lesson Verb Tenses."
- **Still forbidden (§6):** a reference to the original recording. "In the
  last session", "this video", "in class".
- The understanding stage finds the teacher's references and resolves each
  against the course index (docs/05-COURSE-INDEX.md). The narration keeps
  every one it resolved. A reference it cannot resolve is not narrated.
- Where a point clearly depends on an earlier lesson, the narration may add
  a short review pointer of its own. Sparingly: it is `authored`, and each
  one is listed for the reviewer.
- Each reference is data in the lesson bundle: the target lesson's id and
  section id, so the website can make it a link (docs/04-LESSON-BUNDLE.md,
  format 1.1). Ids, not titles, so a retitled or reordered lesson still
  resolves.
- References are spoken, not written on the boards.

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
