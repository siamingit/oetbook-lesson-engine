# 025 — Lesson ids are lower case

Date: 2026-10-01
Status: **Accepted** by the maintainer in chat, 2026-10-01: "Lesson IDs must be
lower case (the website's contract rule). Rename vocabulary-02-Collocations to
vocabulary-02-collocations and vocabulary-03-Collocations-2 to
vocabulary-03-collocations-2 [...] Make lower-case IDs a rule for all future
lessons in the engine's docs and validation. Rebuild both lessons; their
approvals stand (no content change)."

## Context

A lesson's id is its folder's name (docs/04-LESSON-BUNDLE.md §4), and nothing
checked its form. Two vocabulary folders were created with capitals, so their
bundles, their `refs` (Vocabulary 3 refers to Vocabulary 2) and the course
index carried mixed-case ids. The website (oetacademy-web) requires lower-case
lesson ids before it imports the approved lessons.

## Decision

- **The rule**: a lesson id, and so the lesson folder's name, is lower case.
  It applies to every lesson, built or new.
- **The check**: `paths.lesson_id` refuses a folder whose name is not lower
  case. The runner calls it before any stage, the player before it writes a
  bundle, and the course index for every lesson folder, so a mixed-case folder
  stops the build before anything is spent and never reaches a bundle or the
  index. A reference to a lesson id that is not in the index was already
  refused (docs/05-COURSE-INDEX.md §3).
- **The two lessons**: the folders were renamed; the ids in the files the
  pipeline reads (narration, understanding, screens, sections, review pages)
  were rewritten with each file's time kept, so no stage became stale; run
  logs, saved batch requests, superseded replies and the decision logs keep
  the old name as written. Both were rebuilt with the runner, no budget and
  `--no-new-qa`: `bundle.json` and `text.json` (player and silent preview) are
  identical to the approved build apart from the id, so their gates stand.
- No format version: no field changes. An id's form is now constrained.

## Consequences

- The two lessons' ids changed once, which §4 lists among the changes that
  change an id. Anything that stored the old ids (none published) must use the
  new ones.
- The backup drive holds the two folders under their old names. The backup's
  mirror (robocopy, docs/03-RUNBOOK.md step 19) matches names without regard
  to case on exFAT, so it may keep the old capitals while mirroring the
  contents; a lesson restored from it under an old name is refused by the
  check until its folder is renamed.
