# 022 — Effort per model stage, and output caps

Date: 2026-10-01
Status: **Accepted** by the maintainer in chat, 2026-10-01, after the cost
analysis of Grammar 8 and Vocabulary 1-3. The understanding stage's effort is a
**trial** for the next lesson only.

## Context

Every Claude stage ran Claude Opus 5 with adaptive thinking at effort `high`
(the API default) and QA ran Gemini 3.1 Pro at thinking level `high`; no
document recorded either. Across the last four lessons (Grammar 8, Vocabulary
1-3) the model spend was $89.90: screens $37.52, narration $33.95,
understanding $12.92, QA $5.51. Output and thinking tokens were 84% of it
(output is $25 per million against $5 for input; thinking is billed as output).

Per the Anthropic docs (build-with-claude/effort, .../thinking-steering-and-cost,
read 2026-10-01): effort is set per request in `output_config.effort` (`low`,
`medium`, `high`, `xhigh`, `max`; `high` on Opus 5 by default); it is soft
guidance on all output, thinking included; changing it between requests
invalidates the prompt cache. `max_tokens` is a hard cap on thinking plus text
that the model is not aware of: a lower cap saves nothing unless it is hit, and
a hit truncates the reply, which the stages refuse, so the whole call is lost.

Measured on Grammar 8, page 7, through each stage's own prompt, render and
audit, on a copy of the lesson ($4.14):

| Stage, setting | Cost per call | Thinking | Result |
|---|---|---|---|
| Screens, `high` (2 runs) | $0.529 | 8.5k | audits pass; all 28 beats |
| Screens, `medium` (2 runs) | $0.447 (-15%) | 4.3k | audits pass; 28 and 27 of 28 beats; content as complete as `high` |
| Screens, `low` (1 run) | $0.295 (-44%) | 0 | audit passes, but several teaching points packed into one note and a fragment answer row |
| Understanding, `high` | $0.625 | 5.9k | 25 beats |
| Understanding, `medium` | $0.491 (-21%) | 1.5k | 28 beats, matching the production beats; the instructor called "she" in two beats and "he" in the rest |
| QA, `high` (2 runs) | $0.199 | 14.5k | both caught a real fault (the simple present explained with a present-continuous sentence) |
| QA, `medium` / `low` (2 runs each) | $0.137 / $0.054 | 9.4k / 2.3k | neither caught it |

Run-to-run differences at `high` were as large as those between `high` and
`medium` for screens and understanding.

The largest output each stage produced in those four lessons, against its cap:
understanding 29,403 of 32,000 (92%), screens 57,617 of 64,000 (90%), narration
44,672 of 64,000 (70%), QA 17,664 of 32,000 (55%).

## Options considered

1. Keep `high` everywhere.
2. Lower effort where the measured quality held: screens and understanding.
3. Also lower QA's thinking (it is 79% of QA's cost), or screens to `low`.
4. Lower the output caps.

Also proposed and **rejected by the maintainer**: a "changes only" reply format
for screens rewrites; cutting the `note`, `purpose` and explanation fields;
time spans in place of the quoted Persian evidence in understanding; lowering
any cap.

## Decision

- **Screens** (`write_screens.py`): effort `medium`, fixed for the stage, so its
  cached system prompt stays valid from call to call.
- **Understanding** (`extract_understanding.py`): effort `medium` as a **trial
  for the next lesson only**. Its prompt now says to call the teacher "the
  instructor", never "he" or "she". After that lesson the agent reports
  understanding's cost and beat coverage against the `high` baseline, and the
  maintainer decides whether to keep it; until then it is not settled.
- **Understanding's cap**: `max_tokens` 32,000 -> 48,000. The other caps stay.
- **Narration and its state rewrites** (`write_narration.py`): effort `high`.
- **QA** (`qa_narration.py`, Gemini): thinking level `high`.
- **Caps are watched**: whenever the runner reports the lesson's spend (a stop,
  `--status`, the end), it lists every saved reply whose output reached 85% or
  more of its stage's current cap (output plus thinking for QA), so a cap is
  raised before a reply is cut off.

## Consequences

- Estimated on the four lessons' spend: screens about -$5.8, understanding
  about -$2.7 if the trial is kept; about 9-10% of the model spend.
- The measurement is one section, two runs at most per setting; the next
  lessons are the real test, and the screens audit and the gates still judge
  every draft.
- A stage's effort is one constant (`EFFORT`) beside its `MAX_TOKENS`; the
  batch path builds its requests from the same `request_params()`, so both
  paths use it.
- To reverse: set the stage's `EFFORT` back to `"high"` (or `MAX_TOKENS` back
  to 32,000) and record a new ADR.

## Amendment, 2026-10-06: understanding stays at medium

Recorded at the maintainer's request in the review of Reading lessons 1 and 2:
"Understanding stays at medium permanently." The trial above is over. The
understanding stage (`extract_understanding.py`) runs at effort `medium` for
every lesson, as screens does. To reverse: set its `EFFORT` back to `"high"`
and record a new ADR.

## Amendment, 2026-10-06: long sections are drafted in parts; the cap stays

Recorded at the maintainer's request after Reading lesson 2's Scanning section
used 63,145 of the narration stage's 64,000 output tokens (99%): "do not raise
it. Instead, let a long page's narration be drafted in chunks (e.g. per question
group) and joined, with the same audits."

- The narration cap stays at 64,000.
- A section with more than 10 boards (`CHUNK_BOARDS`, `write_narration.py`) is
  drafted in parts: consecutive runs of boards of about equal size (26 boards:
  9, 9 and 8). Each call is given the whole section as context, writes only
  its own boards, and is told how the narration just before them ends, so the
  parts read on. A part that returns other boards is refused.
- The parts are joined into one reply, which is rendered and audited exactly
  as a single draft (a joined test of Reading lesson 2's Scanning section gave
  the same boards and the same audit). Each part is kept
  (`raw_response.part-N.json`) and counted in the spend; the joined reply
  carries no usage of its own.
- A state rewrite from a brief is unchanged: it is already one call for a few
  states. The Part C lesson will need parts for its long texts.
- To reverse: set `CHUNK_BOARDS` high and record a new ADR.
