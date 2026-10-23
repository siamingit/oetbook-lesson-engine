# 040 — Writing course: content decisions, the pinned samples, and authored sessions

Date: 2026-10-23
Status: **Accepted** by the owner in chat, 2026-10-23, in the brief for the analysis of Writing
Sessions 4–7 ("Record these decisions (already made; do not ask again)"). The decisions are the
owner's; how they are recorded and cross-referenced was chosen by the agent under that brief.
No Writing lesson is built yet; no engine, player or bundle change follows from this record.

## Context

The Persian Writing course («کورس رایتینگ OET») has seven sessions. The first analysis
(Sessions 1–3) ended with fourteen open decisions; the analysis of Sessions 4–7 (same day) found
that Session 7 and the four decks of Sessions 4–7 are not on this computer, that the sessions
leave several skills untaught (reading the task and the notes, planning the paragraphs, the
requests, one complete letter), and that the six Writing samples of oetacademy-exercises are still
in no release. The analysis is outside the repository (`C:\OET\lessons\_writing-analysis\ANALYSIS.md`,
§11 there carries the same decisions); the exam facts the lessons may state are
[docs/writing-facts.md](../writing-facts.md).

## Options considered

The owner settled each question in the brief; the alternatives were those of the first analysis's
decision list: wait for a Writing release or pin a commit; show the assessor keys or only teach
from them; drop the teacher's unofficial rules or keep them as his advice; teach one meaning of
"purpose" or both; copy or rebuild OET's criteria table; "Dear Doctor" or "Dear Sir or Madam" for
an unnamed reader; mention or omit regulator rules; keep or drop other professions' examples;
leave the gaps untaught or author new sessions.

## Decision

1. **Our Writing samples.** The six sets (oa-ws-med-0001, -0002, -0003, oa-ws-nur-0001, -0002,
   -0003) are used as they stand on oetacademy-exercises `main` at commit **`5320d19`**
   (`5320d19f0ab81dfccf8e5e62a4918ef83898561d`, "Merge pull request #57 from siamingit/ws-w14",
   2026-10-23). That commit is the pinned source. When the exercises repository releases Writing,
   the lessons switch to the release.
2. **Assessor keys.** Learners never see an assessor key as a document. A lesson may teach its
   reasoning (what to keep, shorten or leave out, and why) in the teacher's voice.
3. **The owner's unofficial rules** are kept and taught as the teacher's advice, in the first
   person (ADR 033 decision 1), never as OET rules: never "firstly / secondly / finally";
   "fortunately / unfortunately" at most once; if the notes give no date, the exam date; his
   word-count rule; and the rules found in Sessions 4–6, listed in docs/writing-facts.md, "The
   owner's other teaching rules". None is worded as a register claim (docs/01-METHODOLOGY.md §17b).
4. **Purpose.** OET's definition is taught as the definition: the purpose is stated clearly in the
   introduction and expanded later in the letter (writing-facts facts 18 and 30). The owner's
   "expand the purpose in the next paragraph" is taught as his practical method.
5. **Closing.** "Please do not hesitate to contact me if you have any questions" is taught as one
   acceptable closing sentence, alongside "Thank you for …"; neither is required.
6. **Criteria board.** An own-words table built from docs/writing-facts.md, plus a link to OET's
   official criteria document; never a copy of OET's table.
7. **Unnamed reader.** "Dear Sir or Madam … Yours faithfully" (and "Dear Dr Surname … Yours
   sincerely" for a named reader). "Dear Doctor" is not taught; nor, therefore, is Session 4's
   "Dear Nurse", "Dear Doctor" or another job title when the reader's name is not given.
8. **The UK nursing regulator's C+ rule** for Writing is left out of the lessons: regulator rules
   change and would date the lessons (writing-facts fact 29).
9. **Other professions' examples.** The radiographer example is kept briefly, in words only; the
   complaint-reply example is dropped.
10. **Wrong figures are taught correctly**: each of the five criteria other than Purpose is scored
    out of 7 on its own; grade A is 450–500; there is no C minus; grade B compares with IELTS
    7.0–7.5; the letter is signed with the job title, as docs/writing-facts.md states (fact 25).
11. **New authored sessions** are allowed where the Persian sessions leave a gap. They follow the
    owner's teaching method and style, use our own samples, and are authored lessons in the sense
    of ADR 018 (every block and utterance `authored`). They need the owner's approval of the course
    plan before they are built.

## Consequences

- The Writing lessons can be planned on a fixed sample text. A later Writing release may differ
  from `5320d19` (two word-count changes are requested: oetacademy-exercises #59); switching to
  it is a source change, re-checked at each lesson's gates.
- A new Nursing sample with an unnamed allied health reader is requested
  (oetacademy-exercises #58), so decision 7 can be taught on our own material.
- The course plan proposed in the analysis (eleven lessons: seven recorded, Session 7 still
  missing, and four new authored sessions) waits for the owner's approval under decision 11. No
  `curated.json` entry, lesson folder for a new session, or course-index change is made before it.
- docs/writing-facts.md gains facts 30–43 (verified on oet.com and OET's Writing guide, 2026-10-23),
  the Sessions 4–6 claims, and the owner's other teaching rules; its rows for the rules ruled here
  now point to this record.
- To reverse a decision: a new ADR. The decisions are the owner's.
