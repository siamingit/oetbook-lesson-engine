# 046 — Practice points: the learner writes in the middle of a lesson (bundle format 1.23, proposed)

Date: 2026-10-29
Status: **Accepted for the engine and its preview player; bundle format 1.23 proposed to the site.** The owner's plan
and design of 2026-10-29 (passed on in the chat's brief): Writing 4 is held; the lesson player gains practice points;
the site's player follows; Writing 4 is rebuilt with word-by-word teaching and practice points; Writing 1-3 later. The
way it is carried (decisions 4 to 11) is the agent's under that brief (ADR 005). Format 1.23 is not released, and no
lesson is published in it, until the site has answered its issue (oetacademy-web #201) and the owner
has tried the prototype. A change after the site's answer is an amendment of this ADR, before any lesson uses it.

## Context

- The owner did not approve Writing 4 as built: "learners don't learn to write this way". He wants teaching word by word,
  sentence by sentence, as his own Session 4 does it (87 minutes; `_writing-analysis/ANALYSIS.md` §2.4, §3.7: rule, simple
  sentences, "pause the video and try", his model typed, the grammar named, a second item faster), and practice in the
  middle of the lesson where the learner writes: type "I am writing to refer …", then "a 16-year-old …", and build the
  opening sentence of a letter piece by piece.
- Until now a "try it first" moment was a pause of up to 10 seconds (§5, rule 9; ADR 033): the learner does nothing.
- The site already has a practice contract for its handouts (oetacademy-web ADR-0031, ADR-0032): items `choice`, `text`,
  `gapfill` and the six types of ADR-0032; answer before Continue; feedback at once; contractions and spelling variants as
  accepted forms; tap first on phones; one item store, one ID registry, attempts in `set_attempts` and `item_responses`.

## Options considered

1. **Keep the pause and say "pause the video".** Nothing is checked, nothing is recorded. Rejected by the owner.
2. **Exercises after the lesson** (handout steps or a set). Not in the middle of the teaching; the owner wants the
   learner to write each piece before the teacher shows it.
3. **A parallel item format inside the bundle.** A second contract for the site to validate, store and mark. Rejected
   by the brief: reuse the site's item contract.
4. **Practice points (this decision):** a moment of the lesson's clock where a player that knows them stops the lesson and
   opens the site's own items over the board; a player that does not plays the pause and the answer as before.

## Decision

1. **What the learner meets** (the owner's design). The teacher gives the task in his voice ("Your turn: …"). A pop-up
   opens over the lesson; the board behind it is dimmed and the lesson stays paused. It holds the task, the piece of the
   paper the learner writes from (the paper excerpt of ADR 045) and the item. The learner answers; Check marks it there and
   then: the right answer and a short reason, written, not voiced. The learner must answer, right or wrong, before
   Continue; there is no second try. Continue closes the pop-up and the lesson goes on from the same point. Laptop: a card
   over the dimmed board, the paper beside the answer. Phone: the whole screen, the paper above the answer. Tap first; no
   sideways scroll; 44 px targets. This is a blocking pop-up, which the site's general UI rule (its AGENTS.md §3, "no
   blocking pop-ups") would not choose: **the owner chose it himself** for practice points.
2. **The items are the site's.** Each point holds one to three items (a handout practice step's limit) in the site's item
   contract, non-exam profile (oetacademy-web ADR-0031 §3), of the approved types: `choice`, `text` (with `response.size`
   `"short"` or `"sentence"`, ADR-0032 §8), `gapfill`, `wordbank` and `ordering` (ADR-0032; `matching`, `grouping`,
   `errorspot` may be used the same way). They are embedded in the bundle, as ADR-0031 §4 embeds a handout's ("embed,
   don't reference"), with their `content_hash` (the factory's rule: JCS without version, content_hash, status,
   withdrawal, tags and admin; the site recomputes it). The prototype's items validate against the site's
   `handout.schema.json` `$defs/item` (contracts 1.12.0).
3. **Typed parts are checked by accepted forms**, contractions and both spellings listed (ADR-0032 Amendment 1, E1). The
   site's scheme `oet-typed-v1` turns hyphens into spaces and drops a first "a", "an" or "the", so it would mark
   "47 year old" right for "a 47-year-old": exactly what writing practice teaches. **A second scheme is proposed,
   `oet-typed-form-v1`**: lower-case, curly apostrophes straight, dashes as hyphens, spaces collapsed, a final full stop,
   comma, colon or semicolon dropped; every word, hyphen and article kept. The reference player implements both.
4. **A whole sentence** is a `text` item of size `"sentence"` (the closest approved type) and, on its practice point, a
   **self-check list** (`check`): the model sentence and its key points (for example: the frame; the title and full name;
   the age with hyphens and an article; the problem; what is asked), each with an id (`<item id>-c<n>`) and `practises`
   tags. After Check the learner's sentence is shown beside the model, and the learner ticks the points they got. A new
   type that carries the list inside the item, **`selfcheck`, is proposed to the site** (oetacademy-web #200, ADR-0027
   Amendment 1). Until it is approved the bundle uses the `text` item and the point's `check`.
5. **A place for AI marking, not built.** `check.marking` is `"self"`; the value `"ai"` is kept for the owner's
   Writing-correction model, which will read the stored sentence and return the ticks (or more) itself. The typed
   scheme's `ai_grading` line is the other place it plugs in. Nothing here calls a model.
6. **IDs.** Every item and part has a permanent ID of the shared registry (ADR-0031 §2, §4), `oa-writing-NNNNNN`, and
   `practises` tags of the site's taxonomy (v3 keys). The engine has no ID block yet: one is asked of the site. Until it has
   one the builder writes and accepts **fixture IDs only (990000-999999)**, which the site's importers refuse in production,
   so no prototype item can reach a learner. The registry's container for a lesson's items is the site's to name (proposed:
   the lesson, by its permanent id).
7. **Attempts, not a test.** Each Check records one attempt per scored unit (an item, a gap, a bank gap), as a handout's
   practice step does (ADR-0031 §5: mode `practice`, feedback released at once, the answer final); the self-check list
   records the points ticked. A practice point is never scored as a test. The reference player keeps the attempts in
   memory only (`window.__practiceAttempts`); storing them is the site's.
8. **Narration.** The task is voiced before the pop-up. After Continue the next utterance may take up the right answer,
   the same for every learner. The audio never depends on what the learner typed: no clip, time or id changes with an
   answer.
9. **Bundle format 1.23** (docs/04-LESSON-BUNDLE.md; docs/bundle-format-changelog.md §9c): a state's `practice` (its
   points: `id`, `time`, `resume`, `utterance`, `cue`, `task`, `excerpt`, `items`, optional `check`) and a pause cue's
   `practice` (the point it is); rules 56 and 57. Additive: a lesson is written in 1.23 only when it has practice points;
   every other lesson keeps its format byte for byte.
10. **The fallback is in the timeline** (rule 57). A practice point is an ordinary pause of 3 to 10 seconds named
    "practice: KEY"; the board shows the task while it lasts; one of the next two utterances shows the answer (a reveal or
    a typing cue) and says it. A player without practice points (the site's player before it builds 1.23, whose section
    cut copies fields by name) plays exactly that: the task, a short pause, the answer. The builder refuses a point whose
    pause or answer is missing.
11. **Where points come from.** A lesson's `analysis/practice.json` (format `oetbook-practice-points`, version 1:
    `{points: {KEY: {task, excerpt, items, check?}}}`) and its narration's pauses "practice: KEY"
    (`spike/scripts/practice_points.py`, called by `build_lesson_player.py`). A lesson without the file is built exactly as
    before. The excerpt is the paper's own lines and labels (ADR 045), read from the sample, never retyped.
12. **The method** for Writing lessons (how many points, how much teaching between them, how the owner's step-by-step
    teaching is followed) is docs/01-METHODOLOGY.md §25.

## Consequences

- Prototype (not the lesson): "Five questions" of Writing 4 rebuilt word by word in a scratch copy, with six points of six
  kinds (a typed frame, a two-gap name and age, a choice of detail, a word bank for the request, an ordering for "why now",
  the whole sentence with its self-check list); the lesson in `C:\OET\lessons\writing-04-introduction` is unchanged.
- Code: `practice_points.py` (new), `build_lesson_player.py` (1.23 when a lesson has points), the reference player
  (`board_player_template.html`: the pop-up, created only when a point opens; nothing changes for a lesson without points),
  `render_compare.py` (a copy's read-only files are removed too, so its guard runs; Writing 4's samples are read only).
- Proof (ADR 043's standing rule): render_compare before and after on every built lesson, restyle_proof on every published
  lesson: identical. Unit test `test_practice_points`.
- The site: oetacademy-web #201 for the format, the pop-up and the attempts, and #200 for the proposed `selfcheck` type; the
  proposed scheme `oet-typed-form-v1` and the engine's ID block are asked in the first.
- Not now: AI marking; a retry; practice points in a Grammar, Reading or Listening lesson (the format allows them; the
  method is written for Writing first); Writing 4 rebuilt as a whole (after the owner has tried the prototype and the site
  has answered).
- To reverse: a new ADR; a lesson without `analysis/practice.json` is as before.
