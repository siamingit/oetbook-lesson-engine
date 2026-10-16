# 036 — Listening Part C: the six questions read first, as a table built from the release

Date: 2026-10-16
Status: **Accepted** (the agent's carrying choice) under the owner's brief of 2026-10-16
for listening-04-part-c ("Analyse the whole session in depth ... so the lesson carries
exactly how the owner teaches and solves Part C questions"; "Make executive decisions
yourself wherever ... they clearly improve the lesson; log them; record any new lasting
decision as an ADR"). It adds to [ADR 029](029-listening-lessons.md) and
[ADR 030](030-listening-board-layout.md); nothing there changes. The owner may reverse it.

## Context

In the Part C session the instructor's first step, before any recording, is to read the
six questions of the extract in the 90 seconds of reading time: he covers every option
with yellow ink, reads the stems one by one, underlines and circles their keywords, says
what kind of answer each asks for and which one asks for the speaker's view, and only
then plays the extract (15:14-22:00 of the session; the Gemini video log of
2026-10-16). The official Part C guide gives the same order (docs/listening-facts.md,
fact 27: read all the questions quickly first, then the options).

`listening_rule.PART_C_METHOD` asked for "a board of its six stems (the questions'
blocks ...)", but no block could show it:

- a question block (bundle 1.15) is pinned on its board and always shows its three
  options, and the screens audit requires it to rule out the wrong options and tick the
  key: six of them on one board give the answers away and do not fit;
- the screens stage may never copy, quote or paraphrase a question in a block of its own
  (the Listening rule), so the stems cannot be typed as notes.

## Options considered

1. **No stems board**: read each stem only on its own question board. Loses the
   instructor's first step, the overview of the talk's six parts that tells the learner
   where each question starts.
2. **Six question blocks over three boards.** They show the options (which the
   instructor hides) and must carry their answers.
3. **A table of the six stems, built by code from the release** (this decision): the
   board the instructor's slide was, with the options covered.

## Decision

- The screens stage writes `{"type": "table", "label": "STEMS <the extract's stimulus
  ID>", "anchor": true}`. Code (`practice_set.stems_block`, called from
  `write_screens.expand_practice`) builds it as a table of one row per question of the
  extract, in order: its number in the lesson (`practice_set.number`: the practice number,
  ADR 032) and its stem exactly as released. Never an option, a key or a reason.
- It is an ordinary core table (ADR 007): one "Row N: ..." thought per question, the
  spotlight on the row being read, the narration's marks (underlines, circles) on the
  stems' keywords, a picture beside it (ADR 021).
- **No bundle change**: a table block with `header` and `rows`, as since 1.2. A renderer
  that draws tables draws it.
- `listening_rule.PART_C_METHOD` names the label, so a model-written Part C lesson gets
  the same board.

## Consequences

- Every built lesson is unchanged: no built lesson has a STEMS label (proved by
  `render_compare.py` before and after, every built lesson).
- listening-04-part-c uses it on "The six questions, then the whole talk".
- To reverse: drop the branch in `expand_practice` and the sentence in
  `PART_C_METHOD`; a lesson that used it then fails its screens audit on that label
  (an unknown practice reference) until its board is rewritten.
