# 006 — Cross-lesson references and the course index

Date: 2026-09-25
Status: **Accepted** by the maintainer in chat, 2026-09-25. The bundle change
is format version 1.1 of docs/04-LESSON-BUNDLE.md; the index is
docs/05-COURSE-INDEX.md.

## Context

The teacher often points to other sessions of the course: "this was taught in
session one, verb tenses", "if active and passive is still hard, review grammar
sessions one and two". Until now docs/00-PRODUCT.md §6 forbade any reference to
the source, and these pointers were dropped with the rest. Grammar 2 lost two
that way: the introduction's recap of "the first session", and the pointer on
page 8 back to lesson 1's tables of active and passive forms (the page 8
ledger ruling of 2026-09-24).

The pointers are useful teaching. They tell the student where a point they
need was taught. What makes a reference to the source wrong is that it points
at something the student does not have: the recording, the class, "the last
session". Another lesson of the product is something the student does have.

To keep the pointers, the pipeline has to know what each lesson teaches. Nothing
records that across lessons: each lesson knows only itself. The website and its
AI chat will need the same knowledge later: which topic is taught in which
lesson, and in which original session.

## Options considered

1. **Keep the rule and drop every pointer.** Simple, but it loses teaching,
   and a student who is weak on the passive is never told where to review it.
2. **Keep the pointers as spoken text only.** The student hears "the lesson
   Verb Tenses", but the website cannot link it, and a lesson that is later
   retitled or reordered leaves the audio pointing at a name that no longer
   matches.
3. **Keep them, and state each as data: the target lesson's id and section
   id** (this decision). The website makes the link; an id survives a new
   title or a new position in the course.

For the record of what each lesson teaches:

1. **Read each lesson's bundle when needed.** Every consumer would have to
   open every bundle and know the pipeline's analysis files for what the
   bundle does not hold (objectives, the original recording).
2. **One course index, built from every lesson** (this decision).

## Decision

**References.** A reference to the original recording stays forbidden ("in the
last session", "this video", "the class"). A reference to another lesson of the
product is allowed and wanted ("You learned this in the lesson Verb Tenses").

- The understanding stage detects the teacher's references to other sessions
  and resolves each against the course index to a lesson id and, where the
  teacher was specific, a section id. What it cannot resolve is recorded as
  unresolved and is not narrated.
- The narration keeps every resolved reference, naming the lesson by its
  title. Where a point clearly depends on an earlier lesson, it may add a short
  review pointer of its own, sparingly, as `authored`; the audit lists every
  one for the reviewer.
- Every utterance that makes a reference carries it as data: `refs`, a list of
  `{lesson, section}` (bundle format 1.1). The audit checks that each id exists
  in the course index.
- The screens are unchanged: the reference is spoken, and the website shows the
  link.

**The course index.** One index of every lesson's content, built by code from
the lessons and their analysis, never by a model:
`<library>/course/course-index.json`, beside the lessons folder, with a
Markdown version generated from it. It is rebuilt, whole, as the last step of
every lesson build. Lessons not yet built appear by title, from their folders
and from the library inventory.

**The index lives outside the repository.** The repository is public, and the
index holds the product's full teaching content. The repository holds only its
format description, docs/05-COURSE-INDEX.md.

## Consequences

- docs/00-PRODUCT.md §6 names the distinction; §2a's "no references to the
  source" for the introduction means the recording, not other lessons.
- Bundle format 1.1 adds `refs` to every utterance in `bundle.json` and to every
  narration entry in `text.json` (an empty list when there is none). A 1.0 reader
  ignores it; every 1.0 bundle stays readable. Lessons 1 and 2 are rebuilt at
  1.1.
- A reference is spoken audio. If the target lesson is retitled, the id still
  resolves, but the spoken title is stale until the utterance is rewritten and
  re-synthesised. The course index lists every reference with its utterance, so
  the stale ones can be found.
- A reference to a lesson that is not yet built resolves to the lesson only
  (no section), and the audit warns: the student does not have it until it is
  published.
- The understanding and narration prompts change, and so does the narration's
  response schema (`refs` on every utterance). Lessons already built keep their
  saved responses; a missing `refs` reads as none.
- Lesson ids are the lesson folders' names (docs/04-LESSON-BUNDLE.md §4). Whether
  that name is the public id is still open (§10 there); a reference holds
  whatever the id is.
- Grammar 2's two dropped references are restored as references to lesson 1,
  by rewriting only the two states concerned; the page 8 ledger ruling that
  dropped the pointer is superseded by a new one.
