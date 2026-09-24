# 003 — Lesson production permissions

Date: 2026-09-24
Status: **Accepted** by the maintainer in chat, 2026-09-24. Applied to AGENTS.md
§2 and §3 the same day.

## Context

AGENTS.md §2 declares the project in EXPLORATION, and §3 requires the agent to
stop and ask before anything that costs money, any change to pipeline stages,
and any deletion or change beyond code it wrote in the session. Those rules
were right while the pipeline was being invented.

Grammar 1 has now been built end to end: understanding, screens, narration,
two QA passes, the terms check, synthesis, the ear, the whole-lesson player and
its structural and mark checks. The procedure is written down
(docs/03-RUNBOOK.md) and one command runs it, stopping at six maintainer
review gates (source, keyterms, screens, narration, lexicon, final) and at a
stated budget (`spike/scripts/build_lesson.py --budget`).

Producing lesson 2 under the exploration rules would mean asking before every
paid call, every re-run of a stage and every small fix to pipeline code. On
Grammar 1 most of those questions had one answer, and the waiting cost more
than the calls. The questions that did change decisions were about content,
schemas, providers and money beyond what was planned: those stay.

## Options considered

1. **Keep AGENTS.md as it is.** Safe, but every lesson repeats Grammar 1's
   stop-and-ask cycle for routine operations the runbook already defines.
2. **Pre-approve lesson production within a stated budget** (this proposal).
   Routine operations go ahead; everything that changes what the pipeline is,
   or spends beyond the budget, still stops.
3. **Declare the pipeline production-ready and drop §3 for lesson work.**
   Rejected: schemas, providers and the rules in docs/ are still changing, and
   the maintainer's gates are where content quality is decided.

## Decision

For **lesson production** — building a named lesson with docs/03-RUNBOOK.md —
the following are pre-approved, per lesson, once the maintainer has stated the
lesson and its budget in chat:

- **API spend up to the stated budget** for the stages in the runbook:
  Scribe (transcription, terms check, ear), Claude Opus 5 (understanding,
  screens, narration, state rewrites), Gemini 3.1 Pro (QA passes), Cartesia
  (term probes, synthesis). Spend is measured as the runner measures it; the
  agent reports it at every gate.
- **Re-runs of existing stages**, including paid re-runs within the budget:
  a stage that failed, a section whose audit failed, a state rewrite from a
  brief the maintainer approved, one QA pass on rewritten states, synthesis
  of utterances whose text or lexicon entry changed.
- **Bug fixes in pipeline code** (`spike/scripts/`) that make an existing
  stage do what the runbook and docs already say it does, for example a
  script that cannot handle a multi-page section, a check that does not know
  a block type, a crash on non-ASCII output. Each fix is named in the report
  at the next gate, with the file and what changed.

These still require the maintainer's answer in chat first, as now:

- adding, removing or upgrading a **dependency**;
- creating or changing a **schema, data model or file format**;
- choosing or switching an **AI model or provider**, or a voice;
- **any spend over the stated budget**, and any paid call outside the
  runbook's stages (probes, experiments, comparisons);
- **changes to the rules in docs/** (00-PRODUCT, 02-DESIGN-SYSTEM, the
  methodology's rules, the runbook's gates) and to AGENTS.md itself;
- new pipeline stages, or reordering stages;
- everything else in AGENTS.md §3 not listed as pre-approved above
  (credentials, `.gitignore`, git operations, deleting files the agent did
  not create, writing outside the repository other than the lesson folder).

Content decisions stay with the maintainer at the gates: a gate is never
approved by the agent, and a QA finding that changes teaching content is
reported, not applied, unless the maintainer's policy covers it (methodology
§18, too-broad rules).

## Consequences

- AGENTS.md §3 gains a short "Lesson production" exception pointing to this
  ADR, and §2's status line changes from EXPLORATION to "exploration for the
  pipeline, production for lessons built with the runbook". Both edits are
  made only when this ADR is accepted.
- The budget becomes the main control on cost. The runner refuses a paid stage
  that would exceed it; the agent may not raise it.
- A bug fix made under this permission is still a change to shared code: it
  must leave Grammar 1's audits passing, and a fix that changes a rule or a
  format is not a bug fix and needs the maintainer.
- If a lesson shows the runbook is wrong (a stage missing, a gate in the wrong
  place), that is a rules change and goes back to the maintainer.
