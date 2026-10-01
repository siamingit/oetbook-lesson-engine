# 024 — Length budget calibration: untaught pages and warning limits

Date: 2026-10-01
Status: **Accepted** by the maintainer in chat, 2026-10-01. Amends ADR 023's
numbers: the natural speech of a section with no recorded teaching, and the
audits' warning limits. Everything else in ADR 023 stands.

## Context

A free dry run of ADR 023 on a copy of Vocabulary 3, an approved lesson, put
it at +26% over its natural target (77:27 against 61.4 min) with 9 warnings.
A budget that flags approved lessons that much would push new drafts shorter
than the maintainer accepts. Calibrated on all 11 finished lessons (read-only):

| Lesson | Type | Natural (min) | Silent preview (min) | Ratio |
|---|---|---|---|---|
| Grammar 1 | grammar | 102.6 | 120.1 | 1.17 |
| Grammar 2 | grammar | 48.7 | 50.3 | 1.03 |
| Grammar 3 | grammar | 56.1 | 48.0 | 0.86 |
| Grammar 4 | grammar | 56.5 | 57.1 | 1.01 |
| Grammar 5 | grammar | 54.8 | 52.9 | 0.97 |
| Grammar 6 | grammar | 54.1 | 50.7 | 0.94 |
| Grammar 7 | grammar | 85.2 | 83.3 | 0.98 |
| Grammar 8 | grammar | 60.6 | 54.6 | 0.90 |
| Vocabulary 1 | vocabulary | 78.4 | 77.2 | 0.98 |
| Vocabulary 2 | vocabulary | 76.1 | 69.8 | 0.92 |
| Vocabulary 3 | vocabulary | 61.4 | 77.5 | 1.26 |

- **No type bias.** Section by section, actual/natural averages 1.00 (grammar)
  and 0.99 (vocabulary). Refits, and a fit on the number of beats, did no
  better than ADR 023's (median error 16-17%). The outliers are single
  lessons: Grammar 1 (the first lesson) and Vocabulary 3, whose taught sections
  ran 14% over their natural length.
- **Sections with no recorded teaching** have no beat times, so ADR 023 gave
  them the fit's floor, 3.8 min of speech. Right for authored sections (ADR
  018): Grammar 7's nine averaged 3.9 (3.1-5.4). Low for untaught deck pages,
  planned by the agent: Vocabulary 3's pages 13 and 14 took 5.1 and 7.5. The
  median recorded section is 6.7 min of speech (grammar) and 6.0 (vocabulary).
- **The warnings came from a section's scatter, not from bias.** Across the
  approved sections, actual/budget is 0.98 (words) and 1.00 (thoughts) at the
  median. ADR 023's limits warned on 17 of 105 sections for words (more than
  20% over) and 19 of 94 for thoughts (more than 30% off); words more than 30%
  over warns on 5, thoughts more than 40% off on 6.
- Grammar 7 was wrongly reported in ADR 023 as an outlier of the play ratio
  (2.17); the measurement missed its nine `added-*` sections. Its ratio is
  1.12, and the play ratios (1.10, 1.19) stand.

## Options considered

1. A per-type multiplier on the natural length: the data shows no type bias.
2. A separate fit, by type or with the beat count: no better.
3. **A share for untaught deck pages, and limits set by the approved lessons'
   scatter** (this decision).

## Decision

- An **untaught deck page** (a section whose pages have understanding but no
  timed beats, not authored) gets the median recorded section of its lesson's
  type: **6.7 min of speech (grammar), 6.0 (vocabulary)**, instead of 3.8.
  An **authored section** (ADR 018) keeps the fit's floor, 3.8. The natural
  length marks both.
- The audits **warn** when narration's spoken words are **more than 30% over**
  the section's budget, and when screens' thoughts are **more than 40% off** it,
  about 5% of approved sections each. Still warnings only, never failures.
- No per-type multiplier.

## Consequences

- Re-run on the Vocabulary 3 copy: the target is 66.6 min (natural; +16% for
  the approved lesson) with 2 warnings, against 61.4 min and 9 before.
- Across the 11 approved lessons a warning now marks an unusual section, not
  ordinary scatter; the gate still judges length.
- The untaught share rests on two pages of one lesson; the constants live in
  `length_budget.py` and are re-measured as lessons are added.
- To reverse: restore 3.8 for every section without recorded teaching and the
  limits 30% / 20% in `length_budget.py`, and record a new ADR.
