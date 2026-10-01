# 023 — A length budget before the first drafts

Date: 2026-10-01
Status: **Accepted** by the maintainer in chat, 2026-10-01: the mechanism the
agent proposed after the cost analysis, with the maintainer's decisions on the
target (its natural length by default, an override for a shorter lesson),
warnings only, and thoughts instead of boards.

## Context

In Grammar 8 and Vocabulary 1-3, whole-section rewrites cost $33.76 of $89.90
of model spend; about $30 of it was the 30 September cuts of Vocabulary 1 and 2,
whose first drafts came out far longer than the maintainer wanted (Vocabulary 2:
a 95:29 silent preview against about 70-75 minutes). Nothing told the screens
and narration models how long a section should be before their first drafts;
lengths were cut afterwards with `LENGTH:` rulings, at the price of a second
draft.

Measured on the 83 finished sections of the first 11 lessons (2026-10-01):

- a section's speech is about **3.8 + 0.37 x its source teaching minutes** (the
  sum of its understanding beats' durations), for grammar and vocabulary alike
  (3.80 + 0.367 and 3.81 + 0.371); median error 16-17% a section; summed per
  lesson, within about 10% for 8 of the 11 lessons. The introduction is about
  2.0 minutes;
- the silent preview plays 1.10 x the speech in a grammar lesson and 1.19 x in a
  vocabulary lesson (medians; Grammar 7, 2.17, left out as an outlier);
- a thought carries a median of 45 spoken words (grammar), 35 (vocabulary);
- a board is a topic, and its states are derived by code from the density rule
  (docs/02-DESIGN-SYSTEM.md §2), so a board count is not the model's to aim at;
  the thought is the unit the screens model writes.

## Options considered

1. Keep cutting after the first drafts (the cost above).
2. A fixed target per lesson type.
3. **The lesson's natural length from its content, shared out per section and
   given to the models before the first drafts** (this decision).

## Decision

- **The target**, `lesson.length_target_min` in `sections.json`, in minutes of
  lesson as the silent preview plays it, with `length_target_source`:
  - `natural` by default: the sum of every section's natural speech, times the
    play ratio. Teaching minutes exist only after understanding, so the runner
    writes it there (step 9b), not at the source gate; it keeps it in step with
    the understanding until screens are drafted. The source gate says so.
  - `override`: `build_sections.py <L> --length-target MINUTES`, the
    maintainer's, for a lesson to be shorter; kept until set again.
  Both print the natural length beside each section's source teaching minutes.
  The runner stops only if no target can be written.
- **The budget** (step 9b, free): `length_budget.py <L>` writes
  `analysis/length_budget.json`. The target's speech is shared in proportion to
  each section's natural speech, the introduction keeping its own 2.0 minutes.
  Per section: speech minutes, words (x 147, the rate the fit used), thoughts
  (words / 45 or 35); in a vocabulary lesson, a cap on full key-word moments
  (ADR 019): half the section's time at about 30 s a moment, a starting value
  to calibrate on the next vocabulary lesson.
- **The agent may change a section's share**, with a reason, logged in the
  lesson's `decisions.md` (ADR 005): `length_budget.py <L> --set TAG --minutes M
  --reason TEXT`; `--clear` removes it. The other sections share what is left.
- **The prompts**: screens and narration add a LENGTH BUDGET block to the
  section's message, after the cached system prompt (minutes, words, and for
  screens thoughts; the key-word cap in a vocabulary lesson). Their system
  prompts carry one sentence: keep to the budget, compress repetition, never
  drop a teaching beat; the screens prompt adds that a board still ends only
  when its topic ends. A state rewrite and QA are not given the budget.
- **Checks warn, never fail**: screens warns when a section's thoughts are more
  than 30% off its budget, narration when its spoken words are more than 20%
  over. A failing audit would make the runner rewrite the section, the spend
  this exists to avoid. The narration gate shows every such warning beside the
  silent preview's length against the target, not only the log.
- A lesson without `length_budget.json` (every lesson built before this ADR)
  keeps its requests and audits unchanged; the runner writes no budget for a
  lesson whose screens and narration all pass.

## Consequences

- A lesson's length follows its content by default; the maintainer sets a
  number only for a shorter lesson.
- The models still decide what to say; the budget is guidance, and the gate is
  where length is judged. The estimates are measured, with a section's error
  about 16%; the constants live in `length_budget.py` and are re-measured as
  lessons are added.
- The vocabulary key-word cap is unproven and is to be calibrated on the next
  vocabulary lesson.
- A section with no recorded teaching (pages the recording never reaches,
  planned by the agent; an authored section, ADR 018) has no beat times, so its
  natural speech is the fit's floor, 3.8 minutes (Vocabulary 3's pages 13 and 14
  took 5.1 and 7.5). The natural length prints it marked; the agent sets such a
  section's share with a reason where it needs more.
- To reverse: delete a lesson's `length_budget.json` (its prompts and audits
  revert), or remove the runner's step 9b and record a new ADR.
