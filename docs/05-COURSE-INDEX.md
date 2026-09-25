# Course Index — what every lesson teaches

One index of the content of every lesson, so the system knows what was taught
where. Written 2026-09-25 (docs/adr/006-cross-lesson-references-and-course-index.md).

It serves now: the understanding stage resolves the teacher's references to
other sessions against it, and the narration audit checks every reference's ids
in it (docs/00-PRODUCT.md §6a). It serves later: the website and its AI chat,
which must know which topic is taught in which lesson and in which original
session.

**Format `oetbook-course-index`, version 1.0.**

---

## 1. Where it lives, and why not here

```
<library>/lessons/<lesson id>/...        the lessons (for example C:\OET\lessons\)
<library>/course/course-index.json       the index (this format)
<library>/course/course-index.md         the same, for people to read, generated from the JSON
<library>/course/library_inventory.csv   the library inventory, if one has been made (§5)
```

`<library>` is the folder that holds the `lessons` folder: for
`C:\OET\lessons\grammar-02-verb-use` the index is `C:\OET\course\`.

**The index never enters this repository.** The repository is public, and the
index holds the product's full teaching content: every lesson's narration and
board text. This document is its format description, and the only part of it
that is kept here.

---

## 2. How it is built

```
.venv/Scripts/python spike/scripts/build_course_index.py <lesson_dir or lessons_dir>
```

- By code, from files on disk, never by a model (AGENTS.md §8). Free, seconds.
- Rebuilt whole each time, from every lesson folder: it is never edited by hand
  and never patched one lesson at a time. The same inputs give a byte-identical
  file.
- **The last step of every lesson build.** The runner (`build_lesson.py`)
  rebuilds it after the lesson player and its checks, before the final gate,
  and again on every later run.
- Nothing in it is new content: every field is copied from a lesson's bundle,
  its analysis, or its source folder, and says where from (§4).

---

## 3. `course-index.json`

### Top level

| Field | Meaning |
|---|---|
| `format`, `format_version` | `"oetbook-course-index"`, `"1.0"` |
| `lessons` | every lesson folder, in id order (§3, `lessons[]`) |
| `references` | every reference from one lesson to another, flattened (§3, `references[]`) |
| `library` | the library inventory's recordings, each matched to its lesson folder where there is one (§5); empty when there is no inventory |

### `lessons[]`

| Field | Meaning |
|---|---|
| `id` | the lesson id: the lesson folder's name (docs/04-LESSON-BUNDLE.md §4) |
| `title` | the lesson title (`sections.json`); null before the deck is read |
| `short_title` | the title after its last colon ("Verb Tenses" from "Grammar for OET: Verb Tenses"): the name the narration says aloud |
| `description` | the maintainer's one line, or null |
| `type` | the lesson type, from the id's first word: `grammar`, `reading`, `listening`, `writing`, `speaking`, `vocabulary` |
| `status` | `built` (a lesson bundle exists) or `not built` |
| `final_gate` | `{by, on}` when the maintainer approved the finished lesson (`analysis/gates.json`), otherwise null |
| `source` | the original session it came from: `recording` (path in the lesson folder), `duration_s`, `partial_hash` (the library inventory's hash of the file, so the two can be matched), `deck`, `deck_pages` |
| `bundle` | built lessons: `{path, format_version, duration_s}` |
| `categories` | as in the bundle's `lesson.categories` |
| `sections` | built lessons: every section in lesson order (below); otherwise empty |

### `sections[]`

| Field | Meaning | From |
|---|---|---|
| `id`, `title`, `category`, `intro`, `pages`, `start`, `end` | as in the bundle | `bundle.json` |
| `recording` | `[{page, from_s, to_s}]`: where in the original recording each of its pages was taught | the understanding's beats and non-teaching spans |
| `objectives` | the learning objective of every teaching beat | the understanding |
| `teaching_points` | what each beat teaches, as the understanding stage read the original session | the understanding |
| `rules` | every rule on the boards: `[{block, kind, text}]`, `kind` `key_rule` or `warning` | the bundle's callouts |
| `key_terms` | every term box except glosses: `[{block, label, term, explanation}]` | the bundle's term boxes |
| `glossed_words` | every gloss of a hard general word: `[{block, word, gloss}]` | the bundle's term boxes labelled `WORD` (docs/00-PRODUCT.md §3) |
| `refs` | references this section makes: `[{utterance, lesson, section, provenance}]` | the bundle's `refs` |
| `referenced_by` | references other lessons make to this section: `[{lesson, section, utterance}]` | the other lessons' `refs` |
| `narration_text` | everything said, as spoken | `text.json` |
| `board_text` | every block's words | `text.json` |

`objectives` and `teaching_points` describe the original session (they may say
"the instructor"); they are the pipeline's reading of the source, not text the
student sees. What the English lesson says is `narration_text` and `board_text`.

A lesson's `referenced_by` for the lesson as a whole (a reference with no
section) is on the lesson: `lessons[].referenced_by`, same shape.

### `references[]`

`{from: {lesson, section, utterance}, to: {lesson, section}, provenance, text}`:
one per reference, `text` the utterance as spoken. `provenance` is the
utterance's: `source-derived` or `adapted` for the teacher's own reference,
`authored` for a review pointer the narration added (docs/00-PRODUCT.md §6a).
`to.section` is null for a reference to a whole lesson. Every `to` resolves to a
lesson in `lessons`; the build fails if one does not.

---

## 4. Provenance

The index carries what each lesson already holds. It adds no teaching, rewords
nothing and judges nothing. Where a field comes from:

| Source | Fields |
|---|---|
| `generated/lesson-player/bundle.json` | sections, rules, key terms, glosses, references, categories, duration |
| `generated/lesson-player/text.json` | narration and board text |
| `analysis/sections.json` | title, description, and a lesson not yet built |
| `analysis/understanding/page-N/understanding.json` | objectives, teaching points, recording spans |
| `analysis/gates.json` | the final gate |
| `source/` | the recording, the deck |

---

## 5. Lessons not yet built

Every lesson folder appears, built or not. A folder with no bundle is `not
built`, with its title when the deck has been read (`sections.json`) and null
otherwise, and its source recording.

The whole library appears through the **library inventory**
(`library_inventory.py <video folder> --out <library>/course/library_inventory.csv`).
Each recording in it is listed in `library[]` as `{title, path, duration_s,
partial_hash, lesson}`: `title` is the file's name without its extension, and
`lesson` the id of the lesson folder whose recording has the same partial hash,
or null for a session no lesson has been made from yet. Exact copies in the
inventory are left out. A recording with no lesson has no id, so nothing can
refer to it until its lesson folder exists.

---

## 6. `course-index.md`

The same content for a person: per lesson its title, type, status, source and
description; per section its objectives, rules, key terms, glosses and
references in both directions, then its narration and board text; then the
library. Generated from the JSON at the same time; never edited.

---

## 7. Open

| # | Question | Status |
|---|---|---|
| 1 | The course order of the lessons. The index lists them by id, and "an earlier lesson" (a review pointer's target) is one whose id sorts first | not decided; lesson ids number the lessons within a type |
| 2 | Whether the website reads this file or its own copy of it | decided when the site is built |
