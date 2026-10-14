# 032 — Listening: the owner's answers to ADR 031, practice question numbers, permanent lesson ids

Date: 2026-10-14
Status: **Accepted** by the owner in chat, 2026-10-14, in the brief for the overnight
build of listening-01-overview and listening-02-part-a ("Owner decisions taken
tonight (record them in a new ADR that amends ADR 031)"). It **amends
[ADR 031](031-listening-vocabulary-panel.md)**, and through it ADR 029 decision 4
(question numbers): where they differ, this one holds.

## Context

ADR 031 left four questions for the owner (PR #14, "For the owner"). Separately, the
website (oetacademy-web PR #98) numbers the practice questions of Parts B and C from 1
within each part, not with the real exam's numbers, and the exercises repository
(oetacademy-exercises #37) is to deliver a practice rendition of the audio that
matches that numbering. ADR 029 decision 4 kept the exam's numbers (Part B 25-30, Part
C 31-42) because the release audio announces them. Lesson folders and ids are linked
from the handouts repository (oetacademy-handouts) and the site.

## Options considered

- Keep the exam's numbers in Parts B and C (ADR 029 decision 4): rejected by the owner;
  the site and the sessions must say the same number.
- Practice numbers only, never the exam's: rejected; a learner should know where the
  questions sit in the real test.
- Practice numbers, with the real numbering said once per part as context: chosen.

## Decision (owner, 2026-10-14)

1. **The answers to ADR 031's questions** (all accepted as carried):
   1. On a 590 px phone the vocabulary panel shows one item at a time; there is no
      phone-specific layout.
   2. The whole-form view during the reading time stays a view of the same Listening
      board, not a board of its own.
   3. A word of the word bank keeps its own gloss and never appears in the panel.
   4. Panel items are written by the model (`authored`), and Listening narration
      explains medical terms. The owner spot-checks the medical explanations at each
      lesson's final approval.
2. **Question numbers** (amends ADR 029 decision 4):
   - Sessions refer to Part B and Part C questions by their practice number: 1-6 for
     Part B, 1-12 for Part C.
   - The real exam's numbering is said once per part, as context, for example "in the
     real test these are questions 25 to 30".
   - Part A stays 1-24 (the practice and the exam numbers are the same).
   - When oetacademy-exercises #37 delivers the practice audio rendition, it replaces
     the release audio in each Listening lesson and the word times are re-run before
     that lesson's final approval. This is on the final-approval checklist of every
     Listening lesson (docs/03-RUNBOOK.md, the final gate).
3. **Lesson ids are permanent.** A lesson's folder name and its id never change once
   made: the handouts repository and the site link to them. The rule is in AGENTS.md
   (§10b). ADR 025's renames (2026-10-01) were before any outside link existed and are
   not a precedent.

## Consequences

- No Listening lesson built before this ADR teaches Part B or C questions, so none
  changes. The engine's question numbering for Parts B and C (`practice_set.py`,
  `check_question_numbers.py`, the narration prompt) is changed when
  listening-03-part-b is built; until then `check_question_numbers.py` still allows the
  exam's numbers in a Listening lesson.
- The audio swap (decision 2) changes a Listening lesson's recordings and word times,
  and so its timing: the lesson is re-checked (the Listening checks, the audio checks)
  before its final approval, as for any audio change.
- Reading Part C lessons are not changed by this ADR (they already number their
  questions from 1 per lesson, ADR 026 amendment of 2026-10-08).
- To reverse: a new ADR. The decisions are the owner's.
