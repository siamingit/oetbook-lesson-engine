# 046 — Practice points: the learner writes in the middle of a lesson (bundle format 1.23)

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

## Amendment (1), 2026-10-30: the owner's try and the site's answer; format 1.23 released

### Context

- **The owner tried the prototype** on 2026-10-30 and approved it ("wonderful"): the pop-up, the word-by-word method and
  the method figures of docs/01-METHODOLOGY.md §25 (about one practice point per piece of a sentence, 20 to 60 seconds of
  teaching between points). Recorded on engine issue #67 and oetacademy-web #201.
- **The site accepted the contract** (oetacademy-web #201 and #200, 2026-10-30; its ADR-0038, ADR-0031 Amendment 1,
  ADR-0032 Amendment 2): bundle format 1.23 as written, rules 56 and 57; contracts `contracts-v1.13.0` (PR #202); the
  site's player plays 1.23 (PR #203, merged 2026-10-30 12:54 UTC: "You may publish sessions at 1.23").
- The site's decisions, which change this ADR:
  1. **Nothing is stored** (the owner's decision): no attempts, no `item_responses`, no scores, no mastery or study-plan
     input, no statistics, no flag queue; the items are not registered in the site's `content_ids`. Marking happens in
     the learner's browser. "Again" (an answered point reached again) lasts one page load.
  2. **The engine's ID block is 900000-989999, in every skill** (`oa-<skill>-NNNNNN`), for items, parts, options and
     self-check points. Permanent and unique within a bundle and across all the engine's bundles; the site checks only
     within one bundle, so uniqueness across bundles is the engine's to keep. Fixture IDs (990000-999999) are refused in
     production (`LP-FIXTURE`); an ID outside the block is refused (`LP-ID-BLOCK`).
  3. **`oet-typed-form-v1` is accepted** as decision 3 proposed it, with the site's test vectors
     (`test-vectors/oet-typed-form-v1.json`): one final mark only is dropped ("a 47-year-old.." stays wrong).
  4. **`selfcheck` is accepted** (#200): `$defs/selfcheckItem` in the non-exam profile; the interim `check` stays valid
     in 1.23, and the site asks the engine to move to `selfcheck`.
  5. No container and no attempt mode are needed while nothing is stored.

### Decision

1. **Format 1.23 is released** (no longer "proposed"): docs/04-LESSON-BUNDLE.md and the changelog's §9c are its
   specification as the site accepted it. The tag `bundle-format-v1.23` is made on the merge commit of this change.
2. **IDs (replaces decision 6).** Every item and part ID is issued by the engine's registry, `spike/practice/ids.json`
   (format `oetbook-practice-ids` version 1, in the repository): one entry per ID, `{id, lesson, point, slot, issued}`.
   Each lesson has its own range of the block, assigned by the owner and set once with `practice_points.reserve`
   (Writing 4 900000-900999, Grammar 1 950000-950999, Grammar 2 951000-951999; ranges never overlap and never change).
   `practice_points.issue(lesson, point, slot)` returns the ID already issued for that slot or the next number of the
   lesson's own range, so a lesson's generator can be re-run without moving an ID and never reaches into another
   lesson's range; a lesson with no range is refused. Entries are never removed: a dropped point
   keeps its IDs, which are never issued again; an ID never moves to another lesson or point. Numbers are unique across
   skills. The builder refuses an ID outside the block or not issued for that lesson and point, so a fixture ID can no
   longer be built. Option and self-check point IDs are `<item id>-o<n>` and `<item id>-c<n>` (not registered: they
   belong to their item).
3. **A whole sentence is a `selfcheck` item (replaces decision 4's interim form).** The builder refuses a point's
   `check`; the reference player renders `selfcheck` (the sentence box; after Check the learner's sentence beside the
   model, the points as tick boxes, the feedback key). It keeps rendering a `check` it is given, since the format allows
   it. The reference player and the builder also take **`errorspot`** (ADR-0032; decision 2 named it): the learner taps
   the wrong word and types the right words, for finding and fixing a mistake in a wrong version of an opening.
4. **Nothing is recorded (replaces decision 7).** The bundle has no attempt or recording field (it never had one); the
   reference player no longer keeps attempts (`window.__practiceAttempts` is gone), only the page's memory of what was
   answered, for "Again". Decision 5's place for AI marking is the `selfcheck`'s reserved `scoring.method` `"ai"` (the
   site refuses it until a marking model exists).
5. **`oet-typed-form-v1`**: the reference player follows the site's definition (one final mark dropped) and passes all 27
   of the site's vectors (`spike/tests/test_typed_form_vectors.py`, run against the pinned zip).
6. **Contracts 1.13.0 are pinned** (ADR 039 amendment of 2026-10-30). Before release, a 1.23 package is also checked with
   the site's own validator at the pinned tag, `pnpm contracts:validate lesson <package folder> --refuse-fixtures`: 0
   errors (docs/03-RUNBOOK.md step 18b). The engine's own check ports `LP-ID-BLOCK`, `LP-FIXTURE` and the first half of
   `LP-PRACTICE`; the site's validator checks the items in full.
7. **The method of docs/01-METHODOLOGY.md §25 is confirmed** by the owner's try: it is the method, no longer a proposal.

### Consequences

- Code: `practice_points.py` (the block, the registry, `selfcheck` and `errorspot`, the interim `check` refused), the
  reference player (`selfcheck`, `errorspot`, no attempt log, one final mark), `lesson_package.py` (`check_practice`), the lock; tests
  `test_practice_points` and `test_typed_form_vectors`.
- The prototype in `C:\OET\lessons\_practice-points-prototype` (fixture IDs, the interim `check`) cannot be rebuilt with
  this code; it stays as it is, a record of the owner's try. Writing 4 is rebuilt whole with practice points next.
- Proof: render_compare before and after on every built lesson, and restyle_proof on every published lesson (ADR 043's
  standing rule), recorded in the pull request.
- To reverse: a new amendment; IDs issued stay issued.

## Amendment (2), 2026-10-31: how many points: one of a series, and never instead of teaching

### Context

- The owner played Writing 4's first draft (`writing-04-introduction-v1-draft.1`, 41 points) in the site's player on
  2026-10-31 (engine issue #72): "far too many: every topic it opens, it gives a practice." The markers crowd the
  progress bar. He expected about a half to a third of them, with no fixed number and no fixed spacing: "it depends
  entirely on the lesson's topic and its points." He does not choose them one by one.
- Two more rules from him: where the lesson works through several items of the same kind, only one is practice,
  usually the last, after the learner has seen the method on the others; and a point never replaces teaching: after it
  the lesson gives the whole explanation it would give without it (the reason, the rule, the common mistake), even when
  the learner was right.

### Decision

1. **The method figures of amendment (1) are replaced** (about one point per piece of a sentence, 20 to 60 seconds of
   teaching between points, one every two to four minutes). The rule is docs/01-METHODOLOGY.md §25, "How many: one of a
   series", for every lesson with practice points: no fixed count or spacing, the agent's judgement by topic; one of a
   series, usually the last; a point never replaces teaching; at least one whole-sentence self-check where a sentence is
   built in full. Every decision is logged point by point in the lesson's decision log.
2. **An item that stops being a point** is taught again: the teacher builds it on screen with its explanation; its task
   line, pop-up and pause are taken out. The narration after a kept point is the full teaching, the same for every
   learner (decision 8 and rule 57 unchanged: the answer is shown and said in the next utterance or the one after).
3. **Retired IDs.** The registry stays append only: an ID whose point a lesson no longer has keeps its row in
   `spike/practice/ids.json`, which gains the field `retired` (the date it was retired); a retired ID is never issued or
   used again, and a new item takes a new number of the lesson's range. Nothing else in the format changes (still
   `oetbook-practice-ids` version 1; the engine's code does not read the field; a lesson's generator refuses a retired ID).
4. **Writing 4** is the first lesson under the rule: 10 of its 41 points kept (its decision log, 2026-10-31), 48 of its
   63 IDs retired, sent as `writing-04-introduction-v1-draft.2`. **Grammar 1 and Grammar 2 are not changed now**: the
   owner is reviewing their drafts, and the rule is applied to them after his review.

### Consequences

- docs/01-METHODOLOGY.md §25 rewritten (the rule; "Writing a point" gains the full teaching and the taught item); the
  registry's `about` names the `retired` field.
- No change to the engine's or the player's code, the bundle format or the contracts.
- To reverse: a new amendment; retired IDs stay retired.
