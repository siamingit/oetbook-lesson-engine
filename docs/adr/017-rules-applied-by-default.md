# 017 — Every decided rule is applied by default to a new lesson

Date: 2026-09-27
Status: **Accepted** by the maintainer in chat, 2026-09-27: "Before lesson 7,
verify that every rule decided in the recent work is recorded as a general rule
for all future lessons, and is applied by default when a new lesson is built ...
Fix anything missing or recorded as lesson-specific."

## Context

An audit of the rules decided for Grammar 1-6 (ADRs 007-016, design system
§5a, §7c, §8a-§8c, sentence-case labels, cost tracking, AGENTS.md §11a) found
each recorded in `docs/` and enforced by an audit or check, with five gaps:

1. **People's names that sound like other words** were decided once, for one
   lesson: Grammar 5's "Yuri Nation" (heard "urination") became "David Harper"
   in that lesson's deck-defect register. No general rule, no check.
2. **Whether a lesson is about tenses** (only a tense lesson draws tense
   colours) was asked for in the runbook but not by the runner: a lesson with
   it unset silently drew neutral labels.
3. **The title board's own blocks** (ADR 014: the board shows what the
   introduction says) came from `build_sections.py --intro-board`; a lesson
   without them built a title board with the title and description only.
4. **The deck's tables** (ADR 007, `slide_tables.json`) were an agent step with
   nothing to stop a lesson that skipped it.
5. **Gate messages** named files by relative path, not as the full `file:///`
   URLs AGENTS.md §11a requires; and the QA prompt still described a gloss's
   picture as "a simple line drawing" (ADR 015 replaced it).

## Options considered

1. Record the gaps and rely on the agent to remember them. Rejected: the point
   of the audit is that a new lesson needs no memory.
2. **Make each a rule in `docs/` and a stop or check in code** (this decision).

## Decision

- **Names** (docs/00-PRODUCT.md §2): a person's name that, spoken, sounds like
  another word or phrase, or could embarrass or distract a learner, is renamed
  with a plain, plausible name, on screen and in speech, through the deck-defect
  register. `lexicon.person_names` finds names (a title with a surname, a full
  name in brackets, after "name is" / "Name:"); the preflight pack lists them
  for the source gate; the terms check hears each one in "The patient's name is
  ..." and records a name heard as other words in `name_failures`, logged and
  listed at the final gate; QA reports one as a major finding.
- **Tense lesson**: the runner stops at the source gate until
  `build_sections.py --tense-lesson yes|no` is set. Never a default.
- **Intro board**: the runner stops at the screens stage, before the title
  board is built, until `--intro-board` is set.
- **Tables**: the runner stops before understanding (while it has pages to
  read) until `analysis/slide_tables.json` exists; a deck with no table has an
  empty `tables` list.
- **Gates** print the files to review as full `file:///` URLs.
- The QA prompt describes a gloss's picture as ADR 015 has it.

## Consequences

- Grammar 1-6 are not affected: each has its tense setting and intro board, and
  its understanding is complete, so the new stops do not fire for them.
- Lesson 7 onward: every rule is applied by default or stops the runner with
  the step to take. The name check over-collects a little (a capitalised pair in
  brackets such as "(Blood Test)" is heard as a name); each costs a few
  characters.
