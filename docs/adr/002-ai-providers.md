# 002 — AI providers

Date: 2026-09-22
Status: Accepted

## Context

Methodology §7 fixes where models are allowed to sit: Persian ASR, text on image
slides, cross-modal interpretation, teaching intent, English rewriting, and
correcting language errors. Everything on either side of that — slide geometry,
segmentation, annotation extraction, timeline generation — is arithmetic and must
stay deterministic.

That middle band still needs providers chosen, and until now none were written
down. AGENTS.md §3 requires that choosing an AI model or provider be a recorded
decision rather than something inferred from whatever the code happens to call.

## Options considered

Per-capability comparison testing on this project's own material was considered
and **deliberately not done**. Building a fair harness — a reference transcript
for word error rate, a rubric for teaching-intent quality, listener trials for
voice — is a project in itself, and the maintainer judged that it would cost more
than it would change the decision at this stage.

The alternative taken is to select on independent published benchmarks and
reputation, accept the risk, and re-open any choice that fails in use. Nothing
here is a one-way door: all four are API calls behind small adapters.

## Decision

| Capability | Provider and model | Status |
|---|---|---|
| Speech to text | **ElevenLabs Scribe v2** | In use |
| Understanding, English writing | **Claude Opus 5** (`claude-opus-5`) | Being tested now |
| Video understanding | **Gemini 3.1 Pro** | Not used yet |
| Text to speech | **Cartesia Sonic 3.6** | Not used yet |

Basis: independent published benchmarks and the maintainer's judgement. The
maintainer chose not to run comparison tests on this project's material.

**Scribe v2 is the only one with evidence from this project.** It has been
measured on Grammar 1 (methodology §13, §14): correct language detection on
code-switched Persian/English, high model confidence, and a cost of $0.56 for a
two-hour lesson. That is a measurement of *this* material, not a benchmark claim.

## Consequences

Each provider is reached through its own small adapter in `spike/scripts/`, so a
replacement is a contained change. ElevenLabs is called over HTTP with `curl`;
Claude will use the official `anthropic` Python SDK, which is a new dependency
and needs its own approval before it is added to `requirements.txt`.

Four providers means four sets of credentials in `.env`, four billing
relationships, and four independent points of failure or deprecation. Costs are
tracked per stage in methodology §14.

`UNKNOWN`: whether Gemini 3.1 Pro or Cartesia Sonic 3.6 suit this material. They
are recorded here as decisions of intent, not validated choices, and neither has
been called.

Cartesia is consistent with methodology §11. That section's "native professional
voice" means a **stock native-English synthetic voice** rather than a cross-lingual
clone of the instructor — the objection is to a Persian-accented clone teaching
English pronunciation, not to synthesis itself. It does not imply hiring a human
voice actor. A stock Cartesia voice satisfies it; instructor identity is preserved
through name, face and on-camera introductions instead.

`UNKNOWN`: how good Claude Opus 5's teaching-intent extraction is on Persian
code-switched lessons. That is what the current one-slide test exists to find
out, and this ADR should be revisited once it has been reviewed.

No benchmark figures are reproduced in this document. Quoting numbers that were
not measured here would be exactly the kind of confident wrong fact AGENTS.md §5
warns against; the basis is recorded as what it is — published benchmarks plus
maintainer judgement.
