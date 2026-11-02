# 051 — Line QA by an independent Claude reviewer subagent; Gemini kept for video

Date: 2026-11-02
Status: **Accepted**: the owner's decision of 2026-11-01, in chat ("Replace Gemini line QA with an independent
Claude reviewer ... to cut cost"); how the reviewer is given its material and how its findings are filed is the
agent's under that brief (ADR 005).

## Context

- Every new or changed line of narration and on-screen text has had an independent language review, the "line
  QA", since Grammar 1 (methodology §18; runbook step 12 and the narration gate): a reviewer that is not told
  what the source taught judges what the student hears and sees, board by board, against a fixed checklist of
  ten checks (`spike/scripts/qa_narration.py`, `SYSTEM`), and returns findings as JSON (utterance id, severity,
  check, issue, proposed fix, confidence). The findings are handled by hand: each is fixed, or rejected with its
  reason in the lesson's `decisions.md`. One pass on every section, one "decisions" pass on the rewritten
  states, two passes at most.
- The reviewer has been Gemini 3.1 Pro Preview, called over the API (ADR 002 named Gemini for video
  understanding; the QA use was added on 2026-09-24 when the slide-based reviewer was retired). It is paid:
  $4.94 over Grammar 1's passes, about $0.60 a lesson for pass 1 and about $0.15 a pass since, $0.80 plus $0.53
  on Word Order. The reviewer's independence rests on what it is given, not on who it is: the payload is blind
  (no transcript, no understanding beats, no provenance, no rulings; only a `maintainer` flag for check 8).
- The lessons are now built inside Claude Code sessions, which can start a subagent: a fresh context that knows
  nothing of the build and is given only what its prompt names. That is the same blindness the Gemini payload
  was designed for, at no API cost.
- Gemini is still the project's only video model: the screen log of a source recording
  (`video_understanding/`, runbook step 1 to 9) and, if ever needed, an image. Nothing else uses it.

## Options considered

1. **Keep Gemini for the line QA.** Rejected by the owner: it is the one recurring paid review that a Claude
   Code session can do itself.
2. **The build's own session reviews its lines.** Rejected: the session wrote them, knows the source and the
   rulings, and would defend them. The payload rule (a reviewer told what the source taught defends the source's
   mistakes) applies to the session too.
3. **A Claude API call from the script** (`anthropic` SDK, as the writing stages). Rejected: it is still a paid
   call, and the owner's decision is to cut that cost; the Anthropic budget rule (AGENTS.md §3) would apply.
4. **An independent reviewer subagent, started fresh inside Claude Code, given the request only** (chosen).
   The script builds the same request Gemini was sent, as one file; the session starts the `line-reviewer`
   subagent (`.claude/agents/line-reviewer.md`: `Read` only, told to read that file and nothing else) on it;
   the subagent returns the findings JSON; the script files it in the same shape as a Gemini review, checked
   against the schema. Nothing is paid.

## Decision

1. **The line QA's reviewer is the Claude Code `line-reviewer` subagent**, started fresh for every review with
   no context from the build. It is given one request file and nothing else: the checklist (the same `SYSTEM`
   text Gemini was sent, which carries the house rules on student level, visual density, register claims and
   product fit, methodology §17, §17a, §17b), the lesson type's QA rules where one applies (vocabulary, reading,
   listening), **the Writing fact sheet (`docs/writing-facts.md`) for a Writing lesson** (new: a claim about the
   exam that contradicts the sheet is a `critical` finding under check 3), the lines with their lesson context
   (the blind payload, unchanged), and the reply's schema. It returns findings in the same format; nothing else.
2. **Findings are handled exactly as before**: each one fixed, or rejected with its reason in the lesson's
   `decisions.md`; the rewritten states get one "decisions" pass; two passes at most (methodology §18).
3. **The mechanics.** `qa_narration.py --call` writes `qa/request_<label>.md` and stops with exit status 3
   ("review pending"); the session runs the subagent on the file, saves its reply, and files it with
   `qa_narration.py --ingest REPLY.json`, which checks the reply against the findings schema (a reply outside it
   is refused and nothing is filed), keeps a replaced review as before (`paths.keep_superseded`), and writes
   `qa/qa_<label>.json` with `meta.reviewer: "claude"`, `cost_usd: 0`. `run_batch_stage.py --stage qa1|qa2`
   writes every pending section's request, lists them and stops with the same status; `build_lesson.py` runs it
   as a free stage (no budget, no uncommitted-code guard) and stops at it until every reply is filed, then
   resumes. `--out DIR` writes a request and its findings elsewhere, for a review of a lesson that must not be
   touched.
4. **Gemini stays for video understanding, and for an image if one is ever needed.** The Gemini line QA code
   stays in `qa_narration.py` and the runners, **off by default**: `qa_narration.py --reviewer gemini --call`,
   `run_batch_stage.py --reviewer gemini`, `build_lesson.py --qa-reviewer gemini` (logged in the decision log as
   the maintainer's instruction). ADR 002's table is unchanged; this record is where the QA reviewer is decided.
5. **The proof** (decision 4 of the owner's brief): the new reviewer was run on Word Order's closing lines, the
   section Gemini reviewed on 2026-11-01, in two states, and its findings set beside Gemini's. The results are
   in the pull request's report (issue labelled `chat-review`) and summarised under Consequences.

## Consequences

- The line QA costs nothing and runs where the lesson is built. The runbook's cost tables keep Gemini's measured
  figures as history; a lesson built from here on records `$0.00` for its reviews.
- Independence comes from the fresh context and the blind request, not from a different vendor. The reviewer
  and the writing stages are both Claude models; the narration is written by Claude Opus 5 over the API, the
  reviewer runs on the session's model. If a family-wide blind spot is suspected, the Gemini review is one flag
  away.
- A review is no longer a batch of API calls that runs unattended: the session must start one subagent per
  section and file its reply. On a nine-section lesson that is nine subagents at the narration stage. The
  requests are written in one go, so they can be reviewed in parallel.
- The reply is checked against the schema but not metered: `meta` records zero tokens, so the runner's
  near-cap check and spend total ignore it by construction.
- The `line-reviewer` agent definition is read by Claude Code at start-up: a session that was already running
  when the file was added does not see it until restarted. The proof below was run with a general-purpose
  subagent given the definition's own instructions, for that reason.
- The Writing fact sheet is now part of a Writing lesson's review request, for both reviewers; it was not part
  of Gemini's. A Gemini review asked for from here on is therefore not byte for byte the review of 2026-11-01.
- The runbook (step 12, the narration gate, "Before the first lesson", "Cost controls") and methodology §18 are
  updated with this record. `GEMINI_API_KEY` is needed only for the screen log and images.

### The proof: Word Order's closing (added-01, three utterances), 2026-11-02

Run with `qa_narration.py <L> --pages 101 --call --out <scratch>` (the lesson folder read only), the request for
the lines as first written made from it by restoring card k02's wording of 2026-11-01, one fresh subagent per
state, each reply filed with `--ingest --out <scratch>` (schema check passed, `cost_usd` 0).

| State of the lines | Gemini (2026-11-01) | The line-reviewer subagent (2026-11-02) |
|---|---|---|
| As first written (before the QA fixes) | 1 minor: on screen "Also and then" reads as a conjunction; add quotation marks (fixed as "The words also and then") | 2 minor: "also and then after the first helping verb" is half the rule (no helping verb: before the main verb; the lesson teaches that elsewhere, the recap drops it), medium; "read each one back with these questions in mind" while the cards are rules, not questions, medium |
| As approved (after the fixes) | 0 findings (the "decisions" pass) | 2 minor: "these questions" again, medium; the highlight on "not obvious" (card k03) is timed on the farewell utterance, not on the sentence that speaks of it, low |

Neither reviewer reported anything false; neither flagged the exercise list or the fact sheet. The two reviewers
found different things on the same lines: Gemini the quotation marks, the subagent the half rule and the
speech-screen fit. The subagent's three findings on the approved lines are listed for the owner in the pull
request's report, not applied: Word Order is released, and whether its closing is re-voiced is his call.
