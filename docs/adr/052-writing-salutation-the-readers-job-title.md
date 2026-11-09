# ADR 052 — Writing: "Dear" and the reader's job title when only the job title is known

Date: 2026-11-09 (the owner's rule of 2026-11-04, given in the brief of 2026-11-09)

Status: Accepted. **Replaces ADR 040 decision 7** ("Unnamed reader"). The rest of ADR 040 stands.

## Context

ADR 040 decision 7 (2026-10-23) taught one form for a reader whose name is not given: "Dear Sir or Madam … Yours
faithfully"; "Dear Doctor", "Dear Nurse" or another job title was not taught. It rested on one OET post (writing-facts
fact 27, source LQ), which pairs "Yours faithfully" with "Dear Sir/Madam". ADR 044 (2026-10-27) recorded, without
deciding, that OET's date article names "Dear Doctor" as a sample salutation.

The handouts plan (siamingit/oetacademy-handouts, docs/plan/writing-handouts.md §8, note 37, medium) found OET's own
article on closings, "Do you end your OET letter like this?" (13 Nov 2023,
https://oet.com/post/do-you-end-your-oet-letter-like-this), read again by the agent on 2026-11-09:

- "If you do not know the name of the person we are writing to but instead have their job title, then use 'Yours
  faithfully'."
- "For example, if we start the letter 'Dear Dentist' or 'Dear Nursing Manager', then we end the letter with 'Yours
  faithfully'."
- "Using the reader's job title is preferred for healthcare letters to the more generic Sir/Madam."

So decision 7 taught as the only form the one OET calls less preferred, and Session 4's own advice (a job title when
the name is not given) was OET's.

## Options considered

1. Keep decision 7. Refused: it contradicts OET's own article.
2. Teach only "Dear" + the job title. Refused: "Dear Sir or Madam" is also correct, and it is what a writer uses when
   not even the job title is known.
3. Both, with OET's preference stated. Chosen by the owner.

## Decision (the owner, 2026-11-04)

- When only the reader's job title is known, write "Dear" + the job title (for example "Dear Ward Manager").
- "Dear Sir or Madam" is also correct, but OET prefers the job title (oet.com, "Do you end your OET letter like
  this?").
- Both close with "Yours faithfully". With a name: "Dear Dr Patel … Yours sincerely".
- Every lesson line, board, model letter, practice item and marking that teaches or applies the old rule is updated, in
  the Writing course's next release (the owner's brief of 2026-11-09). The old-text rule applies: a lesson teaches the
  rule and never mentions the earlier wording (writing-facts, "Not taught (corrected silently)").
- The house rules stand alongside it: Mr, Mrs, Ms and Dr with no full stop; the job title is written as the task gives
  it.

## Consequences

- docs/writing-facts.md: fact 27 widened (EL as a source), fact 45 added (VERIFIED, the owner's rule), and the
  Session 3 and Session 4 rows now say what the lessons teach. ADR 044's open note on "Dear Doctor" is answered here.
- A practice item or AI marking that accepts only "Dear Sir or Madam" for an unnamed reader also accepts "Dear" + the
  job title the task gives, and the feedback says OET prefers the job title.
- docs/course-index.md and its JSON (the topic `writing-unnamed-reader`) change with the Writing lessons' next course
  index pull request.
- To reverse: a new ADR. The decision is the owner's.
