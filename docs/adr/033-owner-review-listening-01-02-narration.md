# 033 — The owner's review of Listening 01 and 02: the first person, the grade B line, the gap-by-gap preview, talking with the learner

Date: 2026-10-14
Status: **Accepted** by the owner in chat, 2026-10-14, in the brief "Revise Listening
lessons 01 and 02 after the owner's review" ("Owner review results (record them in a
new ADR that amends ADR 032)"). It **amends [ADR 032](032-listening-owner-answers-numbering-stable-ids.md)**
and, through it, ADR 030 decision 6 (the fact sheet's rulings): where they differ, this
one holds. How each decision is carried ("How it is carried") was chosen by the agent
under that brief; the owner may reverse it.

## Context

The owner reviewed listening-01-overview and listening-02-part-a, built overnight to the
final gate (PRs #16 and #17). The narration spoke of "the instructor's suggested
targets" (ADR 030 decision 6; PR #16 had let that one phrase past the audit's ban on
"instructor"), gave grade B in two sentences, previewed the Part A gaps quickly, and
read the boards rather than talking with the learner.

## Options considered

- Keep the third-person wording of fact 22: rejected by the owner; the narrator is the
  instructor.
- A rapport rule only for Listening: rejected; the owner wants it for every lesson type
  from now on, without changing the 16 finished lessons.
- Recognising rapport talk by its wording (a list of phrases): fragile, and it would
  sweep up teaching sentences. Chosen: the narration marks each rapport utterance in its
  reviewer note, and the audit compares those.

## Decision (owner, 2026-10-14)

1. **First person, never "the instructor".** The narrator is the instructor. A score
   target is the teacher's own recommendation, in the first person ("I'd recommend
   aiming for 20 out of 24 in Part A."), on boards and in narration. PR #16's exception
   for "the instructor's suggested targets" is removed: the ban on "instructor" applies
   to every lesson again. Amends ADR 030 decision 6 and docs/listening-facts.md fact 22.
2. **Grade B wording.** One sentence: "Grade B usually needs about 30 of the 42
   Listening marks." No separate sentence about tests varying. Amends the fact sheet's
   presentation of facts 18 and 22.
3. **Previewing before a recording.** In a Part A preview, slow down: for each gap, the
   kind of word or phrase that fits (part of speech; the kind of information, such as a
   symptom, a body part, a medicine, a time, a number with a unit; the clues in the
   words around the gap), with one or two example words of that kind. An example word
   is never the answer, an accepted form of it, or anything that gives it away
   (AGENTS.md §4, the leak check). A clear pause between gaps; it must not feel rushed.
   For Part B and C lessons, the same for the stem and the options: what to listen for,
   and how the options might be paraphrased.
4. **Talk with the learner** (every lesson type from now on; the 16 finished lessons
   are not touched). The narration sounds like the owner talking to a student, as in his
   own sessions (the transcripts; ANALYSIS.md §3), adapted to English, not translated:
   transitions between boards and topics, short questions to the learner,
   encouragement, the mistakes his students commonly make, short check-ins and recaps.
   No rapport sentence repeated or nearly repeated in a lesson; no empty filler; no
   personal story beyond what the owner tells in his own sessions.
5. **Approved as built**: lesson 01 in general, its link changes and the podcast
   addresses on its board; lesson 02's four original replacement exercises; the
   twelve medical explanations the owner listed (named in the two lessons'
   `analysis/decisions.md`, outside the repository: some are practice-set answers,
   which never enter git, AGENTS.md §4); the Extract 2 replays; "colour / color"; lesson 02's contents category names; the lesson lengths
   (no padding; items 3 and 4 make them a little longer).
6. **Recorded for later** (no work now): the Listening narration prompt switches to
   practice numbering at listening-03-part-b (ADR 032); Reading 5 is renumbered to
   9–16 after the Listening course is finished.
   **The Reading 5 renumbering is CANCELLED** (owner, 2026-10-22): practice questions in
   every lesson start at 1 and the real exam's number is said once per section (ADR 035,
   amendment of 2026-10-16), so Reading 5 stays 1–8. See ADR 035's amendment of 2026-10-22.

## How it is carried

- `write_screens.py`: `without_allowed()` and its phrase are removed (PR #16 reverted):
  "instructor" is a fixed forbid on screen and in speech in every lesson.
- `listening_rule.py`: the screens and narration rules carry decisions 1 and 2 in the
  owner's words; `NARRATION_PART_A` carries the gap-by-gap preview, `NARRATION_QUESTION`
  the reading of a Part B or C stem and options (decision 3); the QA rule reports a
  third-person teacher, another grade B line and a giveaway example word.
- **The preview check** (`listening_rule.preview_findings`, in the narration audit of a
  Listening lesson): an utterance that says a gap's accepted form or accepted
  misspelling, as whole words, in a state before the one that types that gap fails
  (the finding never prints the answer); a note form's preview with fewer `pause` cues
  than gaps before its recording ("exam") fails.
- **Rapport** (`write_narration.RAPPORT`, given to the narration stage of every lesson
  type): the rule above, and each utterance that carries rapport talk has a reviewer
  `note` beginning "RAPPORT: " and naming its kind. The narration audit compares every
  rapport sentence of three words or more with every other rapport sentence of the
  lesson (this section's and every narrated section's) by the pause-and-try prompts'
  rule (ADR 030: a repeat, one word swapped, or 80% alike in order) and fails a repeat,
  a near copy, or filler ("without further ado", "dive in", "awesome", "amazing"...).
  `listening_rule.py <L> --prompts` reports it with the prompts and the vocabulary
  explanations. Lessons narrated before this ADR have no RAPPORT notes, so nothing in
  them changes.
- docs/listening-facts.md: facts 18 and 22 are presented as above.

## Consequences

- listening-01-overview and listening-02-part-a are re-narrated, previewed and voiced
  again with these rules; the owner's final gate stays.
- The 16 finished lessons are unchanged: no rapport notes, no Listening rules; they
  render identical before and after (render_compare).
- The narration prompt of every lesson type is longer by the rapport rule; future
  lessons will be a little longer.
- To reverse: a new ADR. The decisions are the owner's.
