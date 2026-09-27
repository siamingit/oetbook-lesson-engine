# 013 — Gloss moments and teacher-like openings

Date: 2026-09-27
Status: **Accepted** by the maintainer in chat, 2026-09-27: "Two changes, as
general rules for future lessons, tested first on lesson 6 only": hard-word
glosses get real teaching time, and lesson introductions open like a real
teacher. The rules are docs/02-DESIGN-SYSTEM.md §7b and §7a, docs/00-PRODUCT.md
§2a and §3; the data is docs/04-LESSON-BUNDLE.md, format 1.10.

## Context

**Glosses.** Since 2026-09-25 a hard general word (docs/00-PRODUCT.md §3) was
glossed on the board as "schedule (= plan a time)" and said in one sentence:
two or three seconds. For a learner at A2-B1 that is too quick to learn the
word. The maintainer asked for about fifteen seconds per gloss: the word shown
and said, a pause, a simple meaning spoken and shown, a simple drawing where the
word is concrete, one short example sentence, a pause.

**Introductions.** Every lesson opened with the same sentence, "Hello, and
welcome.", then "This lesson is called Grammar for OET: ...". The course index
shows lessons 1 to 5 all open with it. The maintainer asked for an opening like
a real teacher's, different in every lesson: a link to the previous lesson, a
real problem from a letter, or a question; why the topic matters for the
student's letters, and what they will be able to do by the end.

## Options considered

For the gloss:

1. **A longer narration over the one-line gloss.** No schema change, but
   nothing new on the board to look at for fifteen seconds: the design system
   says every teaching moment gets a visual anchor.
2. **A gloss block drawn part by part** (this decision): the word, its meaning,
   a picture, an example, each revealed as it is said, like a diagram's parts.
   No new field in the model's reply: `term`, `explanation`, `text` and `icon`
   already exist; the block type list gains `gloss`.

For the pictures: the model never draws (docs/02-DESIGN-SYSTEM.md §7a), so a
picture is a curated line drawing in code, named by the model like an icon.

For the openings: a prompt rule alone would drift back to one template, so the
narration audit checks the first sentence against every other lesson's in the
course index.

## Decision

- **The gloss block** (`gloss`, bundle 1.10): `term`, `explanation` (the
  meaning), `text` (one example sentence that uses the word), `icon` (a gloss
  picture or none); its parts, in order: meaning, picture (when it has one),
  example. The word shows with the block. The pale yellow note card, the word a
  little above body size, the picture in neutral slate line work beside the
  text, drawn line by line; every part's room reserved from the start (§8a).
  The screens audit fails a picture not in the catalogue and an example that
  does not use the word; a gloss's meaning is exempt from sentence case, as the
  one-line gloss's was.
- **Gloss pictures** (`write_screens.GLOSS_PICTURES`): grazed-palm,
  cleaning-wound, orderly-wheelchair, clumsy-dropping. Concrete words only; an
  abstract word gets an example sentence only. The catalogue grows as lessons
  need it, each drawing checked in the player. The design system's "no
  illustrations" gains this one exception.
- **The gloss moment in the narration**: the block revealed as the word is
  first said, the word said clearly, a pause of about a second; the meaning,
  the picture (one short sentence on what it shows) and the example revealed
  and said in order; a pause of about a second and a half. The narration audit
  (`gloss_moment_findings`) fails a gloss whose parts are not all revealed in
  order in one state, with fewer than two pauses, or estimated under ten
  seconds (words at 150 a minute plus pauses), and warns under thirteen.
- **Openings**: the introduction prompt asks for a teacher's opening, never a
  template, and is given the previous lesson (`build_course_index.previous_lesson`)
  and every other lesson's first sentence (`openings`). The narration audit
  fails an introduction whose first sentence is a stock greeting on its own or
  "This lesson is called Grammar for OET: ...", or equals another lesson's
  first sentence (case and punctuation aside).
- The rules on which words are glossed are unchanged.

## Consequences

- Lessons 1-5 are not changed now (maintainer). Their screens re-render
  byte-identical with the new code (checked 2026-09-27, files restored); their
  one-line glosses stay. Their introductions all open with "Hello, and
  welcome.", so each will fail the new opening audit when its narration is next
  rendered or rewritten: rewriting their openings is a later, separate task.
- A lesson is longer by about ten to fifteen seconds per gloss: in Grammar 6,
  thirteen glosses.
- A gloss's example sentence is the agent's or the screens model's, never the
  source's: the block stays `adapted`, with a note saying the example is
  authored.
- Bundle 1.10: the block type `gloss` and rule 25. A 1.9 reader shows the
  block's `html` with `blocks.css` and reveals its parts by rule 5, without the
  line-by-line drawing.
