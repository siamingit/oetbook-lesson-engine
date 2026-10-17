# 037 — Listening Part C (2): an all-authored lesson on the interview, and the interviewer as a signpost

Date: 2026-10-17
Status: **Accepted** (the agent's carrying choices) under the owner's brief of 2026-10-17 for Part C
(2) ("Use the folder name and lesson ID already planned ... if none is planned, create one consistent
with the existing names, log the choice, and never change it afterwards"; "Make executive decisions
yourself where the docs answer them; log them; record lasting decisions as ADRs"). It carries
[ADR 029](029-listening-lessons.md) decision 7 and adds to [ADR 035](035-listening-part-b-numbering-and-option-preview.md)'s
amendment on one-line reminders; nothing there changes. The owner may reverse any of it.

## Context

ADR 029 decision 7 splits Part C in two: Part C (1), the method and the presentation (built as
`listening-04-part-c`), and Part C (2), "a short method review and the interview ... The interview has
no source teaching: it is an authored section (ADR 018) that carries the teacher's presentation method
over, flagged for the owner's approval at the silent preview." No folder or lesson id was planned.
The interview (oa-set-lc-0001, extract 1) has six questions, numbered 1-6 in the lesson (ADR 035
amendment of 2026-10-16), and owner-reviewed section boundaries (ADR 031 decision 5).

The owner's Part C session teaches only a presentation; the interview format is printed on one slide
and never discussed. The fact sheet's one interview-specific line is fact 28: "In an interview, it
could be the interviewer's question" that signals the next question.

## Decision

1. **The lesson.** `listening-05-part-c-2`, "OET Listening: Part C (2)", after Reading's
   `reading-05-part-c-2` and the Listening numbering. Permanent (AGENTS.md §10b). It is built from part
   of `listening-04-part-c`'s source, as the runbook says: a byte copy of the source and of the source
   stages' files; nothing is moved out of Part C (1).
2. **Every section is authored.** The lesson teaches no deck page: its config's `groups` is empty, its
   introduction comes from the recording's opening (the greeting), and nine authored sections follow
   (ADR 018): a method review (kind review), the six questions with the whole interview, one section
   per question (pre-teaching board and Listening board, as Part C (1)), and a closing. Each plan carries
   the owner's Part C method as Part C (1) recovered it, and only the fact sheet's facts.
3. **The interviewer as a signpost, as fact 28 says it: "can", not "always".** The lesson teaches that
   the interviewer's words can show where the next part starts, and that the questions' keywords decide.
   It shows the three cases this interview has: a question that opens the part (questions 1-4); an
   interviewer's question that does not start a new practice question (row 3, inside question 1's part);
   a part that starts inside the guest's reply with a linking word (question 5's "But"); and a part
   opened by the interviewer's statement, not a question (question 6). The answers are in the guest's
   replies.
4. **One-line reminders, chosen, not for every word.** On a Part C Listening board the word bank's words
   of that part are recalled as one-line reminders (ADR 035 amendment) from the first draft, since the
   full gloss does not fit beside a Part C question with a wide font (measured on Listening 03 and 04),
   and only for the two or three words that carry the answer or a trap. Every word keeps its full gloss
   on its matching board and its row in the recap.
5. **More than seven word-bank words for one question are pre-taught on two matching boards.** Question 6's
   part (to the end of the interview) holds ten; they are taught five and five, both before the replay.

## Consequences

- No engine or player code changes; every built lesson is unchanged (nothing shared was touched).
- A lesson with no deck section is possible with the existing code: `build_sections.py` writes no deck
  section for an empty grouping, and the runner, the understanding stage (the introduction's span only)
  and the length budget (a target set by the agent: an authored lesson has no source minutes) accept it.
- The review section has no fixed layer, so the screens layout puts its three topics on one board with
  its working layer erased between them (write_screens.one_board_per_slide); its board picture is one.
- To reverse: decisions 3 to 5 are wording and screens choices in the lesson's replies (re-author and
  re-render); decisions 1 and 2 are the owner's to change (AGENTS.md §10b).
