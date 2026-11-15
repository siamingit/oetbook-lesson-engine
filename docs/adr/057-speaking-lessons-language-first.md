# ADR 057 — Speaking lessons: language first, a vocabulary section, and varied practice

Date: 2026-11-15 (the owner's rule for every Speaking lesson, issue #212, comment 6891943431).

Status: Accepted. It applies to every Speaking lesson: the ones being built, the rebuilds, and the next versions
of Speaking 1-3. It changes no engine code, no stage and no format. It amends how ADR 053 and ADR 054 lessons
are authored. It does not change the owner's practice rule (oetacademy-web #275, ADR 053 amendment (1)), which
still holds for every point.

## Context

The owner, 2026-11-15, in his words (translated), on #212:

> "The goal of the Speaking classes is not only to teach tips. The main goal is learning words, verbs, phrases
> and many different sentences that can be used in different scenarios across all the professions. The learner
> must hear lots of sentences, and learn grammar and vocabulary in the middle of them. Remember, teaching words
> and vocabulary is one of our principles."

> "Practice must not be limited to speaking. There should be a vocabulary and verbs section in the lessons, with
> practice and examples. The teacher should teach patiently, and not move quickly past the examples and the new
> phrases."

The first Speaking lessons (Speaking 1-3, Sounding Clear, Asking Questions v1) taught the owner's tips, with one
or two example sentences each, and practised them almost only with `speak_repeat` and `speak_respond`. Asking
Questions v1 ran 18 minutes, but the owner's source session for its content (S3, first half) runs 43 minutes.
The owner's own view: "18 minutes is far too short".

## Decision

The rule, as the owner wrote it, and how a lesson follows it with the engine as it is:

1. **Language is the main content.** The tips frame the lesson. Its core is the language the learner can use.
   For each thing a lesson teaches, a **bank of model sentences**: usually 6-12, all different, natural and
   useful. They come from many professions and settings: nurse, doctor, pharmacist, physiotherapist, dentist,
   occupational therapist, speech pathologist, radiographer and others, on a ward, in a clinic, a GP
   surgery, a pharmacy or a patient's home. Patients' lines vary too: worried and calm, short and long.
   - *How:* a bank is a board table (one row per sentence, with a column for who says it, where). The narration
     reads each row once, with a highlight, and then a pause cue of about 1-1.5 s
     (`[[p 1.2|taking it in]]`). A table too long for one board is split into declared parts, as any board.
2. **A vocabulary and verbs section in every lesson,** with its own section(s), placed where the words are first
   needed: verbs, phrases for time and frequency, lay words next to medical words, collocations, and word
   families (*advise / advice*, *swell / swollen / swelling*, *breathe / breath*). For every item the teacher
   says it, says what it means in plain English, gives a clinical example (and a second, from another
   profession, where it helps), and pauses.
   - *How:* the WORD gloss moment (ADR 013) or a term box, or a table of word, meaning and example read row by
     row with the bank's pause.
3. **Grammar where a sentence shows it.** A short, practical note, with the sentence on the board, tied to the
   sentences just heard: question forms, the present perfect for "how long", *could* and *would* for
   politeness, *going to* and *will*, imperatives in advice, the past simple for when it started.
4. **The teacher is patient.** Say each new phrase, explain it, give the example, pause. Come back to the
   important ones later in the lesson, in a new sentence. A calm B1 pace, short sentences. More examples, fewer
   tips.
5. **Practice is varied, not only speaking.** Every item type the site releases: `choice`, `matching` (at most 5
   pairs), `gapfill`, `wordbank`, `ordering` (words into a question, steps into order), `errorspot`, and typed
   short answers (`text`), above all for the vocabulary and verbs. Speaking points (`speak_repeat`,
   `speak_respond`) stay for the lines said aloud. Every point keeps the owner's practice rule: small, testing
   the thing just taught; no end review; a few words of pop-up text, the teacher saying the task; no whole
   role-play; no scroll at 915x412. More language means more points, which is welcome.
6. **Length follows the content:** most lessons about 30-45 minutes of narration. No padding, and no repetition
   for its own sake. Every minute teaches language or practises it.
7. **Everything else stays:** every OET fact on docs/speaking-facts.md as VERIFIED; never name an app or say
   "video call"; our own cases only; the patient-name rule; the voices Rupert, Gemma and Archie (ADR 027,
   amendment of 2026-11-09); the teal look, one entrance per page and the contents line (ADR 054); the
   full-card model.

A lesson built from one of the owner's sessions covers that session's teaching in full: every question,
phrase, example and explanation, in English, unless the fact sheet shows it is wrong (then it is a question for
the owner). The lesson's decisions.md keeps a table of his minute, what he teaches, and where it is in the
lesson or why it is not.

## Consequences

- Lessons are about twice as long as the first Speaking lessons, with about twice as many points, and spend
  about twice the Cartesia characters (still far below the single-job limit of ~2M).
- Changed or removed points are retired in `spike/practice/ids.json` (ADR 046 amendment (2)), never reused.
- No engine change: every item type and the pause cue already exist. If a lesson finds one is needed, it stops
  and reports.
- First applied in the rework of Asking Questions (speaking-04-asking-questions, v1 draft.2).
