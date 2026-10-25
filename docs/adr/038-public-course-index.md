# 038 — The public course index: what each lesson teaches, in the repository, by code

Date: 2026-10-22
Status: **Accepted** by the owner in chat, 2026-10-21 (the brief "Build the course-wide content
index": one index of what is taught in which lesson, for cross-references between lessons, for the
handouts project, and later for the website and its AI chat; `docs/course-index.md` and
`docs/course-index.json` with a versioned schema; a CI check). Asked in chat the same day, because
ADR 006 keeps the course index out of this public repository, the owner chose "in the repository,
summary only". It **supersedes [ADR 006](006-cross-lesson-references-and-course-index.md)'s
"the index lives outside the repository" for this summary only**: the full index of ADR 006 (every
word of every lesson) stays outside, unchanged. How the index is carried was chosen by the agent
under the brief; the owner may reverse it.

## Context

ADR 006 made one course index (`<library>/course/course-index.json`, docs/05-COURSE-INDEX.md), built
by code as the last step of every lesson build, and kept it outside the repository because it holds
every lesson's narration and board text. Only the pipeline reads it (references, openings, the
previous lesson). The handouts repository (oetacademy-handouts) links handouts to lessons, and the
website will need to know what is taught where. Neither can read a file on the owner's machine,
and the full index holds far more than either needs.

The lesson data already holds a one-line summary of nearly everything taught: the screens stage
gives every board a topic and every thought a purpose (the thing the narration of that thought
teaches), and the bundle gives every block and utterance its time. What it does not hold is
which OET fact or exam method is taught where, and what the docs record about each source
session.

## Options considered

1. **Publish the full index (ADR 006) in the repository.** It holds the product's whole teaching
   content and the practice sets' words. Rejected: the repository is public (ADR 026).
2. **Keep the new index outside the repository as well.** Nothing public, but the handouts project
   and the website could not read it, and CI could check nothing.
3. **A summary index in the repository, built by code from the lesson data, with one reviewed
   file for what the data does not state** (this decision, the owner's choice).

## Decision

### What it holds

`docs/course-index.json` (format `oetbook-public-course-index`, schema version 1.0,
`docs/course-index.schema.json`) and `docs/course-index.md`, generated from the JSON. For every
built lesson, in course order (Grammar, Vocabulary, Reading, Listening) and lesson order:

- its id (the folder's name, permanent: AGENTS.md §10b), title, course, order, length, bundle
  format, approval (the final gate, as recorded);
- its source session: the recording and deck in `source/`, the recording's length and partial
  hash (the library inventory's identity of the file), the lessons made from the same recording,
  and what the docs record about the session (the curated file);
- every section with its title, kind (introduction, deck, authored, review, closing) and start;
  under it every board with its topic and start, and under each board its teaching points (the
  thoughts' purposes) with their starts; the section's rules and warnings (the board callouts),
  its terms (term boxes), its wrong sentences (Grammar and Vocabulary), its practice questions and
  note forms (Reading and Listening: item id, the lesson's number, the real test's number) and its
  references to other lessons;
- the OET facts it states (a Listening fact by its number in docs/listening-facts.md), the named
  exam methods it teaches, each at the utterance or board that teaches it;
- its vocabulary: every glossed word, word-bank item (by its `lx:` ID) and new word, at its first
  moment;
- its practice set (id, release, numbering, the recordings played) or its deck exercises;
- its links: the lessons it refers to and that refer to it (the bundle's `refs`), and the lessons
  it continues in or from (a closing's `next`, and the curated file).

At the end, a topic index: every section title that names a topic, every term box whose label
names a concept, and the curated topics, alphabetically, each with every lesson that teaches it
and its first moment there.

### What it never holds

Nothing of the narration or of the boards' running text; no practice-set wording, no answer, no
word-bank meaning (ADR 026: only ids); no Listening panel word (ADR 031); only counts of what is
left out (`withheld`). On a board that solves a practice question, a letter that names an option
or a text ("option C is ruled out", "Zoom D") is replaced, so no key can be read by elimination.
Any line of a lesson that names an answer of that lesson's own practice set (any accepted form
or key, from the local exercises releases, with no exemption), or quotes six words in a row of
the set's own wording (its texts, transcripts, stems, options, feedback), is left out and counted
(Listening 03 quoted its recording's words in a rule, as evidence of an answer); a section title
that would be left out says so, and a curated line that names one stops the build. A section
titled with a released text's title ("Practice: Text 2 — <title>") keeps its first part. The
Listening facts' own text is the public fact sheet's and is not filtered. A Reading lesson that numbers its
questions from 1 (ADR 026 amendment of 2026-10-08) still names some boards by the real test's
number ("Item 7"): the index uses the lesson's number. The release-answers check (CI) reads the
committed files as before; ordinary words that coincide with an answer of another set are exempted
by item id in `spike/ci/answer_check_exempt.json`, each with its reason (the owner's rule of
2026-10-12).

### How it is built

`spike/scripts/build_public_course_index.py`, by code only (AGENTS.md §8), from the bundle, each
section's screens, `sections.json`, `gates.json`, `preflight.json`, `practice_set.json` and the
source recording of every built lesson, plus `docs/listening-facts.md` and one reviewed file,
`spike/course_index/curated.json`, written by hand: per lesson, the facts and methods with the id
of the utterance or board that teaches each, the session note, continuations and extra topics.
Anchors are ids, never times, so a re-voiced lesson needs no edit; an anchor that no longer exists
stops the build. Rebuilt whole every time; the same inputs give byte-identical files. Layout
words that open a purpose ("Table:", "Row 2:", "Fixed layer:") are taken off.

### How it is checked

- `--verify` (CI, no lesson data): the JSON against its schema; the Markdown is the JSON's; the
  totals; every lesson of the curated file is in the index and every lesson of the index has a
  curated entry (so a lesson that is built and committed without one fails); ids, orders,
  references and topic entries resolve; every moment is inside its lesson.
- `--check` (where the lessons are): built in memory and compared with the committed files; it
  fails when the index is out of date with the lesson data. The unit test
  `spike/tests/test_public_course_index.py` runs it when `C:\OET\lessons` is on the machine, and
  skips it in CI, which has no lesson data.

### How it is updated

Whenever a lesson is added or changed, the runner rebuilds it after the full index, at the last
step of every build (`build_lesson.py`; docs/03-RUNBOOK.md step 18); or by hand:

```
.venv/Scripts/python spike/scripts/build_public_course_index.py C:\OET\lessons
```

A new lesson gets its entry in `spike/course_index/curated.json` (the facts, methods and session
note at least as an empty entry), then the release-answers check runs on the new files, and
`docs/course-index.*` are committed with the lesson's pull request.

## Consequences

- The handouts project and the website can read one public file, by lesson, section, board, block
  and utterance ids (docs/04-LESSON-BUNDLE.md §4), and a version tells them what changed. A
  minor version only adds fields; a major version is a new ADR.
- The teaching points are the screens stage's purposes, which describe what each thought teaches
  but are a planner's wording (for example "Define the perfect correctly"); they are short and
  faithful to the lesson, and are not student text.
- Reading 2's word table (ADR 026 amendment of 2026-10-06) is a table, not glosses, so its words
  are not in the vocabulary list; three of them are Part A answers in any case.
- The full index (ADR 006, docs/05-COURSE-INDEX.md) is unchanged and still feeds the pipeline.
- To reverse: delete `docs/course-index.*`, the CI step and the runner's call, and record a new ADR.

## Amendment, 2026-10-25: the Writing course (schema 1.1)

Under the owner's brief of 2026-10-25 for writing-01-overview ("add the curated.json entry for this
lesson ... Rebuild the course index as the runbook says"), the first Writing lesson enters the public
index, so the index gains its fifth course:

- **Schema 1.1**: `writing` is added to the course enumerations (`courses[].id`, `lessons[].course`); the
  courses' order is Grammar, Vocabulary, Reading, Listening, Writing. Nothing is removed or renamed; a
  1.0 reader that ignores the Writing course reads every other lesson as before.
- `build_public_course_index.py` lists the course (`COURSES`); nothing else in the builder changes. A
  Writing lesson's OET facts are keys of the curated file's `facts`, each worded as
  docs/writing-facts.md states it, with the fact sheet's number in brackets.
- The 21 lessons already indexed are unchanged, except that the lessons the new one refers to
  (Paraphrasing, Verb Tenses) list it under `referred_to_by` (checked by a diff of the JSON).
