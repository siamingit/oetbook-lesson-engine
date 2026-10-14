# 034 — Listening: the owner's spelling line, and asides that speak to everyone

Date: 2026-10-14
Status: **Accepted** by the owner in chat, 2026-10-14, in the brief for the session that
builds listening-03-part-b ("Two small fixes first (Listening 01 and 02)"). It adds to
[ADR 033](033-owner-review-listening-01-02-narration.md); nothing there changes. How it
is carried was chosen by the agent under that brief; the owner may reverse it.

## Context

After approving listening-01-overview and listening-02-part-a, the owner asked for two
wording changes:

- Listening 02 said at gap 19, after the answer: "The name of a medicine must be spelt
  correctly." That is stronger than the fact sheet: marks *may* be lost for spelling
  mistakes, and minor variations may be accepted (docs/listening-facts.md, fact 10).
- The handwriting joke in both lessons spoke to "the doctors"; the course is for every
  healthcare profession.

## Options considered

- Change the two lessons only: the next lessons (Parts B and C) could make the same claim
  or the same joke again.
- Change the two lessons and carry both wordings into the Listening rule (chosen).

## Decision (owner, 2026-10-14)

1. Where an answer's spelling matters, a Listening lesson says it in the owner's words:
   "Spell it carefully — a spelling mistake can cost you the mark." Never that a word
   "must be spelt correctly".
2. A joke or an aside speaks to every learner ("So, everyone, please take care with your
   handwriting!"), never to one profession.

## How it is carried

- listening-02-part-a, gap 19 (pages 15-17, utterance t1.s15.u3): "The name of a medicine
  must be spelt correctly." becomes "Spell it carefully — a spelling mistake can cost you
  the mark." Its on-screen note ("Spell the medicine correctly.") is unchanged.
- The handwriting joke: listening-02-part-a page 6 (t1.s2.u2) "So, everyone, please take
  care with your handwriting!"; listening-01-overview page 5 (t1.s2.u5) "And please write
  clearly, everyone! ...".
- Each is a narration override (the section's `overrides.json`, with its guard and this
  decision named); only those three clips were voiced again (Rupert, voices.py defaults),
  their word times taken from the new synthesis; the players were rebuilt and every
  check run. The lessons' approvals stand (owner, 2026-10-14).
- `listening_rule.py`: the narration rule carries both points for every later Listening
  lesson; the QA rule reports "must be spelt correctly" and an aside aimed at one
  profession. docs/listening-facts.md fact 10 names the owner's line.

## Consequences

- No built lesson other than the two changes: the rule is prompt text, read only when a
  Listening section is narrated or reviewed.
- To reverse: a new ADR; remove the overrides and re-run the runner (the cache re-makes
  only those clips).
