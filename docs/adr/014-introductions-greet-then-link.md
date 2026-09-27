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
