# ADR 055 — Every speaking point in the site's released items (contracts 1.27.0)

Date: 2026-11-13 (the owner's follow-up brief of 2026-11-13).

Status: Accepted. It amends ADR 054 decision 7 (a Speaking draft carried only its speak_repeat and matching points)
and ADR 053 (the engine's own draft form of speak_respond and roleplay is gone). It replaces the pin of ADR 054:
contracts 1.27.0 in place of 1.22.0 (ADR 039: a new lock is a new decision).

## Context

The site released the other two spoken types and turned them on for every signed-in learner (oetacademy-web
#275): speak_repeat in contracts 1.22.0, speak_respond in 1.25.0 and roleplay in 1.26.0. Contracts 1.27.0
(#304, ADR-0034 Amendment 23 there) put the skill `speaking` and its 31 keys of taxonomy v3 on the session
section tag list. Until then a Speaking package could not pass LP-TEACHES-NOT-ALLOWED.

The owner's brief:
- "Map every speaking point in Speaking 1-3 to the released items."
- speak_respond: "task, patient_line, audio.normal (the patient's recording, listed as narration), cues (2 to 4,
  each with text, match and example), model_answer, max_s, scoring ai. No marking."
- "Run the contracts' own cueSaid / cueWords check before packaging: every cue said by the model answer, and
  each example says its own cue." "No digits in patient_line, model_answer or examples."
- roleplay: "length short (2 or 3 tasks) or whole (3 to 6 tasks)", the card, the patient (voice patient-f /
  patient-m "as in ADR 027: Gemma or Archie as the card says") and the patient card ("hidden (1 to 4 facts the
  patient gives only when asked)"). "No digits in the opening."
- speak_repeat: "RP-SPEAK-SHOWN now applies (shown reads word for word as spoken)."
- "Keep the owner's fuller role-play cards: the scenario in two or three full lines. If the schema's background
  is too short for that, ask the site on #275 to allow it."
- "No speaking point is left out any more."
- "Keep the local pop-up honest, as it is now: it cannot hear the learner."

The engine had written speak_respond with `key_points` (ideas to say, never checked) and roleplay in a draft
form of its own (ADR 053). Neither is the site's form.

## Options

1. **The cue check.**
   - (a) Copy the site's matcher (its TypeScript) into the engine. The site's contracts are private and this
     repository is public, so its code cannot be copied here.
   - (b) Write the engine's own matcher from the rule as the schema states it (lower case match words; a phrase's
     words in order with at most two words between; a final `*` for any ending, a plural s otherwise; numbers
     said as words; never across a sentence break; a negation up to three words before a word unsays it), and
     cross-check it against the site's own code outside the repository.
2. **key_points.**
   - (a) Keep every key point as a cue. Some are not said by the model answer ("Use simple words", "No long
     introduction"); a cue the answer does not say is refused (RP-SPEAK-CUES).
   - (b) Rewrite each item's ideas as two to four cues the model answer says, each with match words and an
     example; a key point that is advice on manner, not something said, is dropped.
3. **The role-play's background.**
   - (a) Shorten it to the schema's "one or two short sentences".
   - (b) Keep the owner's card whole. The schema has no length limit for it; only its description is shorter.

## Decision

1. **Every speaking point goes to the site.** speaking_items.py builds the released form of all three types
   (`release_item`); a Speaking draft and a final release carry every point. A type the contracts do not carry
   would still be left out of a draft and refused in a final release, as in ADR 054.
2. **speak_respond** (contracts 1.25.0): `task` (the point's prompt), `patient_line`, `audio.normal` (the patient's
   recording, one narration file of the package), 2 to 4 `cues` (text, match, example), `model_answer`, `max_s`,
   `scoring: {method: "ai"}`, `tags` (`practises` from the item, the profession as a facet). The model answer is
   read by the site's own voice, so it has no recording here. `prepare_s` and `key_points` are gone. No marking:
   the site ticks the cues and gives light feedback.
3. **roleplay** (contracts 1.26.0): `length` (all five are `whole`: four tasks each), `card` (setting, role in one
   sentence, background, tasks), `patient` (name, role "the patient", opening, voice `patient-f` for Gemma and
   `patient-m` for Archie, ADR 027 amendment of 2026-11-09), `patient_card` (persona, emotion, concern, 1 to 4
   hidden facts), `scoring: {method: "ai"}`, `tags`. The schema has no title, so the role-play's title stays in
   its point's excerpt. It has no recordings: the site's patient voice says every line. `prepare_s` and `talk_s`
   are gone.
4. **The cue rule** is the engine's own (option 1b): `cue_words`, `phrase_said` and `cue_said` in
   speaking_items.py. It was cross-checked in scratch against the site's `cueSaid` and `cueWords` on every cue of
   Speaking 1-3, against every text of its item and ten traps: 952 cue checks, 0 differences, and the same word
   lists. The site's code stays out of this repository.
5. **Checks before packaging.** speaking_items.check refuses, and lesson_package checks again in the package
   (LP-, as RP- in a release):
   - RP-SPEAK-CUES: the model answer says every cue, and each example says its own cue, by the match words;
   - RP-SPEAK-NUMBERS: no digit in `spoken`, `patient_line`, `model_answer`, an example or the opening;
   - RP-SPEAK-SHOWN: `shown` reads word for word as `spoken` (only capitals and the final . ? or ! differ);
   - RP-ROLEPLAY-TASKS: two or three tasks for a short role-play, three to six for a whole one;
   - a spoken item is the only item of its practice point (LP-PRACTICE-ITEM).
6. **key_points became cues** (option 2b). Advice that is not said was dropped: "Use simple words", "No long
   introduction", "Add no title", "Use 'you'", "No title", "A short answer", "A warm, short greeting", "Reassure
   her". A match phrase is written as the rule reads it: "not worry", never "don't worry".
7. **The owner's cards stay whole** (option 3b): three or four sentences, 29 to 42 words. Each card's `role` is
   one new sentence (the job and who the learner talks to), and each persona gained how the patient speaks, as
   the schema asks.
8. **The pin: contracts 1.27.0**, `oetacademy-contracts-1.27.0.zip`, SHA-256
   752a0ab789359dea2a1d844db018db705544c2492f5f635f69e10ba53490b42e, as the site posted on #304. Bundle format
   stays 1.23.
9. **The local pop-up is unchanged:** it plays the patient, shows the cues and the model answer, and marks nothing.
   It cannot hear the learner.

## Consequences

- Speaking 1-3 go to the site as drafts with every point: 22 speak_repeat, 29 speak_respond, 5 roleplay and the
  one matching point of Speaking 1.
- The rebuilt players differ from the last build only in their practice entries: no clip, time or board changed.
- 21 of the 29 model answers are under the schema's described "about 15 to 45 words" (5 to 14 words), and the five
  cards' backgrounds are longer than its "one or two short sentences". Neither is a schema limit; both are asked
  on #275.
- Every key of taxonomy v2 and v3 is now on the tag list, so the test of LP-TEACHES-NOT-ALLOWED takes a key off
  the list for its run.
- Nothing built for another course changes: the new code runs only for spoken items (the render proof is in the
  report of #202).

To reverse: pin 1.22.0 again and put `RELEASED_TYPES` back to speak_repeat alone; a Speaking draft then leaves its
other points out, as in ADR 054.
