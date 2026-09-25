# 005 — Decision policy and three gates

Date: 2026-09-24
Status: **Accepted** by the maintainer in chat, 2026-09-24. Amends ADR 003's
gate list and its rule that a gate is never approved by the agent; applied to
AGENTS.md §3, docs/03-RUNBOOK.md and `spike/scripts/build_lesson.py` the same
day.

## Context

ADR 003 pre-approved routine lesson production within a budget but kept six
maintainer gates (source, keyterms, screens, narration, lexicon, final) and
left every content question to the maintainer. Building Grammar 2, the agent
asked questions the docs already answered, and questions where one option
plainly served the student better by the product's own rules. The waiting and
the reading cost the maintainer more than the decisions were worth; the
questions that did need the maintainer were about money, contracts, rules, their ear and
genuinely doubtful teaching claims.

## Options considered

1. **Keep ADR 003's six gates and ask on every content question.** Safe, but
   the maintainer reviews routine outcomes the docs already decide.
2. **Let the agent decide what the docs decide, log it, and keep three gates**
   (this decision).
3. **No gates below final.** Rejected: the silent preview is where screens and
   narration are judged together, and it is cheap to change before audio.

## Decision

**The agent decides, without asking,** whenever the docs answer the question,
or one option clearly serves the student better by the product's own rules
(docs/00-PRODUCT.md, docs/02-DESIGN-SYSTEM.md, docs/01-METHODOLOGY.md). Every
such decision is written to the lesson's decision log,
`<lesson>/analysis/decisions.md`: what was decided, why, which doc rule, and
how to reverse it. The maintainer reviews the log at the gates and may reverse
anything.

**The agent asks only for:**

- spend beyond the lesson's budget;
- a change to the bundle contract, a schema, a provider, or a rule in the docs;
- anything only the maintainer's ear or taste can settle: voice, pronunciation;
- a teaching claim whose correctness is genuinely in doubt and not settled by
  the docs.

**Three gates**, replacing ADR 003's six:

1. **source**: the preflight pack, reviewed in chat with the maintainer before
   the run;
2. **narration**: the silent preview of the whole lesson, screens and narration
   together;
3. **final**: the finished lesson with audio, including the pronunciation of
   new terms.

Keyterms and screens are no longer maintainer gates: the agent approves them
when their audits pass, and logs it. The lexicon gate is folded into the final
gate: terms the ear did not hear as written are synthesised with the voice's
default, listed for the maintainer, and judged by ear at the final gate; a new
lexicon entry is still used only after the maintainer approves it
(methodology §20).

Everything else in ADR 003 stands: the budget, the list of what still needs
the maintainer (dependencies, schemas and formats, providers and voices, spend
over budget, rules in docs/, new or reordered stages, credentials, git,
deletions), and bug fixes named at the next gate.

## Consequences

- AGENTS.md §3's lesson-production exception names this ADR, and its line "a
  review gate is never approved by the agent" now reads that the agent approves
  only the keyterms and screens steps, when their audits pass.
- The runner stops at three gates. When the screens audits all pass it records
  the approval as the agent's in `gates.json` and appends it to the decision
  log; the keyterms step likewise once `keyterms.json` builds.
- The decision log is the maintainer's review surface for everything decided
  between gates. A decision not in the log was not made under this policy.
- Synthesis now runs before the maintainer hears new terms, so a term the maintainer
  rejects at the final gate costs a re-synthesis of the clips that contain it;
  the content-addressed cache limits that to exactly those clips.

## Clarification, 2026-09-25

Added by the maintainer after the Grammar 2 narration gate, where the agent
asked about two of the teacher's OET-writing claims ("avoid continuous forms in
OET letters"; "'has taken' means the course is finished").

A rule from the teacher's own OET advice that is stated too broadly is still a
broad rule. docs/01-METHODOLOGY.md §18, "Too-broad rules — policy", already
decides it: narrow it and keep the point, on screen and in the narration
together. The agent does this without asking and logs it. "A teaching claim
whose correctness is genuinely in doubt" means one the docs and the policy do
not settle; a too-broad rule, whether it comes from the teacher's grammar or
from the teacher's exam advice, is not that.

## Clarification, 2026-09-25: remaining QA findings

Added by the maintainer after a QA pass on rewritten states found new issues
and the agent stopped to report them. When the QA findings that remain are
settled by the docs (methodology §17, student level; §17b, register; §18,
too-broad rules; the product's rules on references to the source) and the fix
fits the lesson's budget, the agent applies them without asking: briefs, state
rewrites, overrides, and one QA pass on the changed states, each logged. It
stops to ask only when a decision is genuinely the maintainer's (ADR 005's
list above), or when the maintainer has set an explicit stop for that round.
