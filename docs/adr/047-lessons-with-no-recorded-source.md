# 047 — Lessons with no recorded source; the general Writing course order; Writing 8 as the first authored Writing session

Date: 2026-10-31
Status: **Accepted**: the owner's decisions of 2026-10-31, in his brief for writing-08-reading-the-task and in
his approval in chat of its plan (the "continue" of 2026-10-31, which also approved the engine change below and
asked for this ADR). The engine design (decision 3) is the agent's under that approval (ADR 005).

## Context

- The owner added a new session to the general Writing course: reading the Writing Task and the case notes, and
  choosing what goes into the letter. He has no recording of it. Every earlier lesson, Listening 05 included
  (ADR 037), was built from a recording and a deck in `source/`; the authored sections of ADR 018 sat beside
  sections taught from the recording.
- The engine assumed a source in four places: the preflight pack (`preflight_pack.py` needs `source/video.mp4`
  and `source/slides.pdf`), `build_sections.py` (it reads the deck on every full run), the introduction
  (`paths.intro_section`: the contents slide's interval, or the title slide with the recording's opening), and the
  runner's source stages (audio, keyterms, transcription, slide timeline, annotations, understanding).
- The owner's method for this session is in his profession recordings (C:\New OET\projects\29\29.mp4, Nursing;
  C:\New OET\projects\31\31.mp4, Medicine) and his handout wp:957; the plan cites them by mm:ss
  (`C:\OET\lessons\writing-08-reading-the-task\PLAN.md`, outside the repository because it quotes the private
  samples).

## Options considered

- **A placeholder video or deck in `source/`** (a blank recording, a one-page deck) so the engine runs unchanged.
  Rejected: it is false provenance. The course index and the site would show a recording and a deck the lesson
  was never made from, and every check that reads the source would check nothing.
- **A second pipeline for authored lessons.** Rejected: every stage after understanding is the same, and two
  pipelines drift.
- **A small guarded change** (chosen): a lesson whose config says it has no source skips the stages that read a
  source, and every lesson with a source keeps exactly its current path.

## Decision

1. **The general Writing course order** (the owner, 2026-10-31):
   1. Overview (writing-01-overview)
   2. Assessment Criteria (writing-02-assessment-criteria)
   3. Letter Structure (writing-03-letter-structure)
   4. Reading the Task and the Case Notes (writing-08-reading-the-task, this new session)
   5. The Opening Paragraph (writing-04-introduction)
   6. Information Flow (writing-05-information-flow)
   7. Organisation (writing-07-organisation), which will also teach planning the paragraphs and the request and
      closing paragraph
   8. Word Order (writing-06-word-order)

   Writing one complete letter from start to finish goes to each profession's own course, not the general
   course. Lesson IDs never change (AGENTS.md §10b): the order is the course's, not the IDs'.
2. **writing-08-reading-the-task is the first authored Writing session.** It teaches reading the Writing Task
   first (who the reader is, why you write, what you ask), then reading the case notes with that reader in mind,
   and deciding what is relevant, what to leave out and how much detail to keep. Grouping and ordering belong to
   Organisation (session 7): this session only points to them. Every section, block and utterance is `authored`
   (ADR 018); the owner's method is followed as found in his recordings, his rules taught in the first person as
   his advice (ADR 040 decision 3), and only the facts of docs/writing-facts.md stated as OET's. Its samples are
   cited at oetacademy-exercises 5320d19, as Writing 3 and 4 do (ADR 040 decision 1). The release
   `writing-speaking-v1` holds the same texts byte for byte; moving the course to the release is a separate, later
   decision.
3. **A lesson with no recorded source** (the engine change):
   - It starts with `build_sections.py <L> --no-source "TITLE" --by NAME`, refused where `source/` exists or a
     config already does. The config records `lesson.source` `"none"`, the maintainer's title, no contents slide
     and an `intro` of source "authored"; its sections are all added with `--add-section` (ADR 018). A full re-run
     of `build_sections.py`, which would read a deck, is refused.
   - Its introduction is authored: `paths.intro_section` gives it the slot just below the authored sections'
     (page 100, folders `page-100`), with no recording span. Its plan is the agent's
     (`analysis/understanding/page-100/understanding.json`), like every section's.
   - The runner (`build_lesson.py`) skips the preflight pack, audio, keyterms, transcription, slide timeline and
     annotations; the understanding stage never calls a model and stops if a plan is missing. Its source gate is
     the maintainer's approval of the lesson's plan, recorded with `--approve source`; the description and the
     tense setting are needed as for any lesson.
   - The title and contents boards (`build_lesson_boards.py`) carry the title as the maintainer's, `authored`,
     and never name a deck. Both course indexes write "Original session: none" for a lesson with neither a
     recording nor a deck.
   - Every other stage is unchanged.
4. **Proof that no built lesson moved** (runbook, "Changing shared code"): every built lesson rendered before and
   after the change with `render_compare.py` and compared. Writing 3 and Writing 5 were being built in other
   sessions at the same time, so both snapshots rendered one frozen copy of the library (taken 2026-10-31 23:17)
   instead of `C:\OET\lessons`, whose guard would have stopped on their writes; the result is in the pull request.

## Consequences

- A lesson can be built from the owner's method alone, with honest provenance: no recording, no deck, every block
  and utterance `authored`, and the course index saying so.
- The paid source stages cost nothing for such a lesson; its model spend is QA and images only, as for the
  agent-authored Writing lessons.
- The runbook's step table still describes a lesson with a source; this ADR is where the no-source path is
  written down until the runbook is next revised.
- Reversible: a config without `lesson.source` `"none"` takes the old path in every changed function.
