# 028 — Cartesia on the Scale plan: synthesis is not rationed, and runs in parallel

Date: 2026-10-06
Status: **Accepted** by the maintainer in chat, 2026-10-06 ("Provider update ...
Record this in the project docs ... New rules ... Apply this from now on,
including the current Part B lesson"). Amends ADR 003 (the lesson budget) and
methodology §23 (the audio budget) for Cartesia only.

## Context

Cartesia (ADR 002; the voice of every lesson, ADR 027) was on the Startup plan:
1.25 million characters a month and 5 concurrent TTS requests. Its credit was
the reason for methodology §23's rules (audio only after the narration is
approved; never re-synthesise speculatively) and part of every lesson's budget
(ADR 003), and synthesis ran one clip at a time.

On 2026-10-06 the account moved to the **Scale** plan through the Cartesia
Startups grant, free for 12 months (until about October 2027):

- **8 million characters a month** (previously 1.25 million), with 2x rollover;
- **15 concurrent TTS requests** and 60 concurrent STT requests on Scale, per
  Cartesia's documentation ("Concurrency limits and timeouts",
  docs.cartesia.ai/use-the-api/concurrency-limits-and-timeouts, read
  2026-10-06; Startup 5, Pro 3, Free 2, Enterprise custom); over the limit the
  API returns `429 Too Many Requests`. Each HTTP or SSE request is one context.
- Measured on the account the same day: 15 simultaneous requests, then 20,
  all succeeded with no 429 (short sentences of about 1 s each, overlapping).
  So the account is above Startup's 5. The engine uses the documented 15; it
  does not rely on the account accepting more.

A lesson uses about 85,000 characters (docs/03-RUNBOOK.md); the month's quota
holds about 90 lessons.

## Decision (maintainer's rules)

- **Cartesia cost or quota is no longer a reason to economise or to ask for
  budget approval.** Re-takes, audition samples, several variants of a section
  and re-runs go ahead without asking. Cartesia characters are not part of a
  lesson's `--budget`, and the runner no longer asks for one before synthesis.
- **Synthesis runs in parallel**, up to the plan's concurrency, so overnight
  runs finish sooner. Retries with backoff stay for rate-limit (402, 429) and
  server (5xx) errors and timeouts, with jitter so parallel workers do not
  retry in step.
- **The maintainer is told** only if a single job would use more than about
  2 million characters in a month, or if usage rises abnormally.
- **Anthropic and Gemini budgets are unchanged**, with all their rules. So is
  Scribe (ElevenLabs), which the terms check and the ear use: the terms check
  still needs a budget, since its probes are transcribed by Scribe.

## How it is carried

- `synthesize_narration.py`: `TTS_CONCURRENCY = 15`; a section's clips are made
  by a pool of that many workers (`--workers` to divide them between runs side
  by side, whose 429s the retries otherwise absorb). The audio index is
  assembled in narration order, so it is byte-identical to a run made one clip
  at a time: checked on all 122 narrated sections of the 13 built lessons with
  Cartesia stubbed out (120 identical; Grammar 7's pages 11-12 and 13 differ in
  the same way with the old code, because states taken out under ADR 018 are
  still in their indexes). Cache keys are unchanged, so no clip is remade.
- A run that would send more than 2,000,000 characters stops and says so
  (`JOB_CHARACTERS_LIMIT`; `--allow-large-job` once the maintainer has been told).
- `build_lesson.py`: synthesis no longer requires `--budget`.
- Abnormal usage: the engine has no view of the account's monthly usage. Each
  run prints the characters it sent, and the runner logs them; the agent
  reports a run that sends far more than a lesson's usual 85,000.

## Consequences

- Methodology §23's "never re-synthesise speculatively" and "Cartesia credit is
  limited" no longer hold for credit reasons. The pipeline's order is unchanged:
  a lesson is still synthesised after the narration gate, because that is where
  its words are approved; and a new lexicon entry is still used only after the
  maintainer's ear approves it (methodology §20).
- `check_terms.py` probes stay sequential: they are a few thousand characters,
  and each is transcribed by Scribe in turn.
- When the grant ends (about October 2027) the plan, its quota and these rules
  are reviewed in a new ADR.
- To reverse: set `TTS_CONCURRENCY` to 1, restore the runner's budget check,
  and record a new ADR.
