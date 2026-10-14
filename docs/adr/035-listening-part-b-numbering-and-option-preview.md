# 035 — Listening Part B: practice numbers in the engine, the option-by-option preview, and how the session maps onto the practice set

Date: 2026-10-14
Status: **Accepted** (the decisions) by the owner in chat, 2026-10-14, in the brief for
the session that builds listening-03-part-b ("Numbering: Part B questions are numbered 1
to 6, as on the website. Say the real test question number once per section. The
script-writing prompt must use this numbering from Listening 03 onwards"; "Before each
play: for each option, explain what to listen for, with examples (never the real
answer), with pauses between questions"). It carries [ADR 032](032-listening-owner-answers-numbering-stable-ids.md)
decision 2 into the engine and extends [ADR 033](033-owner-review-listening-01-02-narration.md)
decision 3 to Parts B and C. How each is carried, and the mapping of the session onto the
practice set, were chosen by the agent under that brief; the owner may reverse them.

## Context

ADR 032 decided that Parts B and C are numbered by their practice numbers (1-6, 1-12),
the real exam's number said once as context, and left the engine (`practice_set.py`,
`check_question_numbers.py`, the narration prompt) to change when Part B was built. Until
now a Part B question block showed the release's number (25-30), the prompts said
"question numbers are the exam's", and a spoken "question twenty-five" on a board showing
1 would have failed nothing but also been allowed nowhere.

ADR 033 slowed down the Part A preview (gap by gap, with a pause and example words that are
never the answer) and asked for "the same for the stem and the options" in Parts B and C;
nothing checked it.

The source session (listening-03-part-b, 90 minutes) teaches Part B on a complete
third-party Part B recording (its questions 25-30, the deck's questions 1-6) and on two
official sample questions, all excluded (ADR 029 decision 1). Each of the six worked
questions carries a skill of its own (a time word against what is already arranged; a
paraphrase and "not given"; two speakers; the real reading time; answering without the
technical words; what the speaker is doing).

## Options considered

For the numbering:

1. `practice_set.py --lesson-items` (Reading Part C's per-lesson numbering): a manual
   step per lesson, and Part C (1), which teaches questions 37-42, would number them 1-6,
   not the website's 7-12.
2. **The practice number computed from the set** (chosen): a Part B or C question's place
   in its part, for every Listening lesson, with no manual step.

For the real test's number: never spoken (rejected by ADR 032), or spoken anywhere
(confusing beside the board's number), or **spoken in a sentence that names the real test
or the recording** (chosen: the release audio announces it, so the learner hears it).

For the session's six worked questions: teach the practice questions in the deck's
question order but out of number order, matching each skill to the extract that shows it
best (a section order the engine does not allow: sections follow the deck's pages);
or **practice questions 1-6 on deck pages 10-15 in order, each page's general method
applied to its question, and a skill that fits another question carried there with the
understanding stage's `--page-also`** (chosen).

## Decision

1. **Practice numbers in the engine** (owner, ADR 032). `practice_set.number` gives a
   Listening Part B or C question its place in its part (`PRACTICE_NUMBERED`, LB and LC):
   Part B 1-6, Part C 1-12; Part A's gaps stay 1-24. `practice_set.exam_number` is the
   real test's number, `exam_numbers(ps)` the map. The question block's badge, the spans
   ("question N"), the word recap's question column, the screens prompt and the narration's
   numbers all follow. Reading lessons are unchanged.
2. **The real test's number, once per question, as context** (owner). The narration says it
   once for each Part B or C question in a sentence that names the real test or the
   recording ("In the real test, this is question twenty-five: that is the number you will
   hear in the recording."). `question_numbers.board_findings` allows a spoken number that
   is the real test's number of a question the board shows only in such a sentence; the
   narration audit and `check_question_numbers.py` pass it the set's map. A Listening
   lesson's first question need not be 1 (Part C (1) starts at 7).
3. **The option-by-option preview** (owner; extends ADR 033 decision 3). Before a Part B or
   C recording plays in full, the narration takes each option in turn: what it means, what
   to listen for, one or two example words a speaker might use, and a pause of 2-3 seconds
   ("thinking about option B"). An example is never the transcript's words for the answer.
   `listening_rule.question_preview_findings` (narration audit): fewer pauses than options
   before the recording fails; no pause-and-try prompt between the recording and the
   answer fails; a word of the item's released evidence (five letters or more, not printed
   in the stem, the options or the rubric, not an everyday word) in the narrator's own
   words before the key is ticked fails (the finding never prints the word).
4. **The session on the practice set** (agent, under the brief). Deck pages 10-15 teach
   practice questions 1-6 in order. Two of the teacher's worked points are carried, with
   `--page-also`, to the question whose recording shows them: "both speakers must hold the
   view" (deck question 3) to question 5, an "agree" question; "I'd = I would" (deck
   question 4) to question 6, whose speaker gives advice with "I'd". The official
   sample questions are replaced by original examples; the third-party distractor table
   by the lesson's own table of six kinds of tempting wrong option, each tied to the
   practice questions whose release reasons show it.
5. **Not taught** (agent; ADR 029 decision 9, AGENTS.md §5): the instruction before Part B
   as extra reading time (as fact 21 for Part A); "superficial options are usually wrong,
   complex ones right" (a heuristic that can mislead); "uses an informal expression" as a
   sign of a wrong option (a register claim, docs/01-METHODOLOGY.md §17b); what Part B
   "assesses" in the deck's words (not on the fact sheet). His figures are taught as the
   fact sheet's, never mentioning the error: about 45 seconds a recording (he says a
   minute), 15 seconds of reading time (30 and 20), 42 questions (38), three options in
   Part C (four).

## Consequences

- No built lesson changes: Listening 01 has no set, Listening 02 is Part A, Reading keeps the
  release's or the lesson's numbers. Proved with render_compare on the 18 built lessons.
- The review preview (`listening_prototype.py`, outside git) says "question three" for
  Part B and gives each option a pause; its checks pass.
- listening-04-part-c inherits the numbering, the real-test sentence and the preview audit.
- To reverse: `PRACTICE_NUMBERED = ()` restores the release's numbers; drop the call to
  `question_preview_findings`; a new ADR.

## Amendment, 2026-10-14: a word-bank word glossed again on a Listening board has no picture

Found on listening-03-part-b's silent preview: a word-bank gloss (ADR 026 §2: glossed again
where the word is said or printed) drawn in a Listening board's question column, under the
question and its options, ran up to 50 px past the board's foot at all three frames (39
findings). On a board with a transcript, `write_screens.expand_practice` now gives such a
gloss no picture part (as a panel item has none, ADR 031): its meaning, synonym and example
stay, its picture is on the word's matching board and recap. A Listening lesson's narration
reveals three parts there, not four. Agent's carrying choice under the owner's brief; no
built lesson has such a gloss (Listening 02 is Part A). To reverse: drop the branch in
`expand_practice`.


## Amendment, 2026-10-14: a one-line reminder where the full gloss does not fit

Found on listening-03-part-b's wide-font check (Verdana forced, 590 px small phone): even
without its picture, a word-bank gloss under a Part B question could run a few pixels past
the board's foot after the player's guard had set the question column to its floor. Where
that happens, the screens author may give the word, on the Listening board only, a one-line
reminder of the word bank's meaning (a plain note, "word: meaning") in place of the full
gloss, and the narration says that meaning once. The full gloss (meaning, synonym, example,
picture) stays on the word's matching board just before the Listening board, and on the
recap after it. Used for three words in listening-03-part-b. The authoring prompt is not
changed: this is a fit fallback, chosen when a check fails, not a default. Agent's carrying
choice under the owner's brief. To reverse: give the word its full gloss again and shorten
other notes on that board.

## Amendment, 2026-10-14: no copy of a pinned question while a recording plays

Found by the layout check on listening-03-part-b's voiced player: while a recording played,
the player hid a Part B board's question and drew a copy of it (the section's question, bundle
1.19) at the column's top without the room kept for its reasons, so the question and the note
under it moved by up to 93 px (462 word moves, every Part B board). `listen_board` in
`build_lesson_player.py` now gives a section no question block when its question is pinned
on the board: that question is already in the column for the whole board, so the recording
shows it where it is. A section whose question is not on the board, or is a state's own
block (Part C), keeps the copy as before. Proved by render_compare on every built lesson.
To reverse: drop the `pinned` test in `listen_board`.
