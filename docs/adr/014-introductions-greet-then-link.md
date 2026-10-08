# 014 — Introductions greet first, then link, and the board shows what is said

Date: 2026-09-27
Status: **Accepted** by the maintainer in chat, 2026-09-27. Supersedes the
opening rule of docs/adr/013-gloss-moments-and-teacher-openings.md (its gloss
decision stands).

## Context

ADR 013 ruled out a "template opening" and the audit failed a greeting on its
own. Grammar 6's introduction was rewritten to it and opened straight with the
content, with no greeting and no welcome. The maintainer: "That is my fault:
'no template opening' did not mean 'no greeting'." The title board also showed
only the lesson title while the narration described the previous lesson and a
problem from a letter.

## Decision

For every lesson's introduction:

- **A warm greeting and welcome first**, like a teacher talking to their own
  students ("Hello again, and welcome back. I hope the course has been useful
  for you so far. Today we're going to look at another important part of
  grammar."). The wording varies from lesson to lesson; only the exact same
  first sentence as another lesson's introduction is forbidden.
- **Then** a link to the previous lesson (course index), why the topic matters
  for the student's letters, and what they will be able to do by the end.
- **A2-B1**: short sentences, simple words, a friendly tone.
- **The board shows what the narration describes**, not only the title: the
  title board carries the lesson's own intro blocks (sections.json
  `intro_board`, set with `build_sections.py --intro-board FILE`: for example a
  note linking to the previous lesson and a change card from short sentences
  to one clear sentence) and the description, each revealed as it is said.
  Existing block types only; no bundle change.
- "The course", meaning this product's course of lessons, may be named; the
  recording, a session, class, slide or video still may not
  (docs/00-PRODUCT.md §6).

**Audit** (`write_narration.py`): the introduction fails when its first
sentence is not a greeting, when "welcome" is not in its first two sentences,
or when its first sentence equals another lesson's first sentence in the
course index (case and punctuation aside). ADR 013's check against a greeting
on its own, and against "This lesson is called ...", is removed.

## Consequences

- Grammar 6's introduction is rewritten to this rule; its title board gains two
  blocks (the link to Complex sentences, and a change card from two short
  sentences to the lesson's own one-sentence version).
- Lessons 1-5 all open with "Hello, and welcome.": each passes the greeting
  checks, but no two may keep that same first sentence, so all but one fail the
  repeat check when their narration is next rendered. They are not changed now.
- A lesson with no `intro_board` has the title and the description only, as
  before; the runbook asks for the board at the introduction's narration.

## Clarification, 2026-09-27

Added by the maintainer with the update of lessons 1-5: the link to another
lesson never assumes the order in which the student takes the lessons ("The
lesson Complex sentences shows how to ...", never "In the last lesson you ...").
The link is usually to the previous lesson; the first lesson links to another.

## Amendment, 2026-09-27: the first lesson of a course

Added by the maintainer after Grammar 1's introduction said "I hope the course
has been useful for you so far" and linked to another lesson: a course's first
lesson (the first of its type in the course index) is the learner's start, so
its introduction instead

1. welcomes the learner to the whole course;
2. explains simply why grammar matters in the OET letter: the reader is another
   health professional and needs clear, exact information, and grammar is part
   of how the letter is assessed (no grade promises);
3. says why this lesson's topic is the first step ("By the end of this lesson
   ..."), and starts the lesson.

A2-B1 language, a warm tone. The title board shows what is said, from the
lesson's own blocks (`--intro-board`). The audit fails a first lesson's
introduction that assumes earlier study ("so far", "welcome back", "again", "in
the last lesson", "you learned"). Every other lesson keeps the rule above.

**No course map, no lesson count, no list of lessons** (maintainer, the same day,
replacing a course map first built into this amendment): the course is still
growing, so a first lesson's introduction has no course map, and no lesson of
any course states how many lessons the course has or lists the other lessons.
Naming one other lesson where it helps (the link above) is not a list. The
narration audit fails a lesson count ("the first of six lessons", "the course
has six lessons", "lesson 1 of 6") and an utterance that names three or more
other lessons; the screens audit fails a lesson count on a board.

## Amendment, 2026-10-08: every lesson ends with a closing

Added by the maintainer with the split of Reading Part C: no lesson stops
abruptly. Every lesson from Reading Part C (1) on ends with a short closing on
its own final board, about 30 to 60 seconds:

1. a quick recap of the two or three most important points of that lesson;
2. then a warm, creative goodbye that is different in every lesson (no fixed
   template: for example hoping the lesson was useful, encouraging practice, or
   saying the learner will be seen in the next lesson).

It may name what the next lesson is about only when that is certain (the
closing's `next` in sections.json, set from the maintainer's word); it never
states how many lessons there are or lists them. The final board stays on screen
3 seconds after the last word (`build_lesson_player.CLOSING_HOLD_S`; the
lesson's length, no new bundle field). Earlier lessons are not changed now.

Carried as an authored section of kind `closing` (ADR 018 amendment of the same
day): `build_sections.py <L> --add-section N "Closing" --kind closing [--next
LESSON_ID]`, its plan the agent's. The screens prompt asks for one board with one
state: two or three short notes and a picture. The narration prompt gives the
next lesson (or none) and every other lesson's closing; the audit fails a
closing of more than one board or over 180 words (warns outside 60-150) and a
goodbye whose sentence is one of another lesson's closing's last three.
