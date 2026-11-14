# ADR 053 — Speaking lessons: a patient's line, and speaking practice points

Date: 2026-11-09/10 (the owner's brief of 2026-11-09, "Build the first Speaking lessons overnight"; decided by the
agent while the owner was asleep, as the brief asked)

Status: Accepted for building and review. **Nothing it adds is published**: a lesson with speaking units is refused
by `publish_lesson.py`, as a package and as a draft, until the site's contracts have speaking units.

## Context

The Speaking course (ANALYSIS.md, issue #189, answered 2026-11-09) needs two things no other course has:

1. A second voice in the narration. The owner chose the patients' voices on 2026-11-09 (ADR 027 amendment of
   2026-11-09, issue #190): Gemma and Archie on sonic-3.6 at speed 0.8; the emotion setting only where the role card
   makes the patient worried or upset; Rupert stays the teacher, unchanged.
2. The learner speaks. The owner (#189, decision 8): every "your turn" gap is a speaking pop-up, with Skip after about
   5 s.

The site has a Speaking Coach prototype (oetacademy-web, branch feat/speaking-coach-prototype,
packages/shared/drafts/speaking): a DRAFT of contracts 1.21.0 with three item types, `speak_repeat`, `speak_respond`
and `roleplay`. It is not released, and the site's lesson player cannot play speaking units. The brief: "Do NOT
release, and do NOT publish drafts to the site (it cannot show speaking units yet)", and "Lines with no speaker field
stay teacher, so every built lesson must render identically before and after."

## Decision

### 1. A narration line may be a patient's (`speaker`, `emotion`)

- In `gen_narration.py` a line is written `P(text, note, who="patient_f"|"patient_m", emotion="worried"|"upset")`;
  narration.json carries `speaker` and, only where the card gives the feeling, `emotion`. A line with neither is the
  teacher's, exactly as before; the fields exist only in a lesson whose type has `speakers` (lesson_type.py: the
  `speaking` type). `write_narration.speaker_findings` fails a speaker in any other lesson, an unknown speaker, or a
  feeling on a teacher's line.
- `voices.SPEAKERS`: patient_f = Gemma (62ae83ad-4f6a-430b-af41-a9bede9286ca), patient_m = Archie
  (ef191366-f52f-447a-a398-ed8c0f2943a1), both sonic-3.6 at speed 0.8. `voices.EMOTIONS`: worried → Cartesia's
  `anxious`, upset → `frustrated`. synthesize_narration.py voices a patient's line with them; every other line is
  voiced as before.
- The bundle (format **1.24**, a draft; only a lesson with a patient's line or a speaking point is 1.24, every other
  lesson stays 1.23) carries `speaker` on the utterance. The engine's player labels a patient's caption
  "patient · …" with a teal edge; timing estimates use the patient's slower speed.
- `qa_narration.py` sends the speaker with each line, so the line reviewer reads a patient's line as the patient's.

### 2. A dialogue board (ADR 050 amendment (14))

The teal look has a `dialogue` layout: a two-column table (who, line) drawn as speech bubbles, the patient's on one
side and the candidate's on the other, who speaks above each. The patient side is found by the label's first word
(`style_c.DIALOGUE_PATIENT`: patient, carer, parent, mother, father, mum, dad, son, daughter, wife, husband,
partner, relative, Mr, Mrs, Ms, Miss; anything else is the candidate). Contrast 4.5:1 or more and the label above the bubble (padding-top) are measured by
check_text_size.py, as every teal board.

### 3. Speaking practice points, behind one mapping module

- A Speaking lesson's practice.json (ADR 046) may hold items of the draft's three types. Everything that knows the
  draft's shape is in `speaking_items.py` (`check`, `browser_view`, `to_contract`), with a byte-for-byte copy of the
  draft schema in `spike/speaking/draft-1.21.0/`. When the contract is released or changes, that module changes and
  nothing else.
- IDs come from the practice ID registry, skill `speaking`, range from **970000** (engine `oa-speaking-NNNNNN`,
  contract `oa-speak-NNNNNN`, the same number).
- `synthesize_speaking.py` voices each item's lines (the model in Rupert's voice; the patient's prompt in the
  patient's voice and feeling; a slow take at **0.75** for `speak_repeat`) into `generated/speaking-audio/`, local
  only; the mapping fills the contract's audio fields from it. A `roleplay` item's patient card stays on the site's
  server: the engine's player shows the candidate's card only.
- The site's voice names: `gb-m-rupert`, `gb-f-gemma`, `gb-m-archie` (`speaking_items.SITE_VOICE`).
- The engine's player (1.24) opens a speaking pop-up at the point's pause: the prompt (and the patient's line, with
  Hear the patient), Listen and Slowly, **Record** with playback on this device only (nothing is kept or sent; the
  site gives the feedback), **Skip after about 5 s** (`SP_SKIP_S = 5`, the owner's decision 8), then the model and
  what a good answer has.
- The validator (`practice_points.py` through `speaking_items.check`) checks every item: type, IDs in the registry's
  range, the speaker and feeling, the model answer, and the contract form against the draft schema.
- The counting rule for points stays ADR 046 amendment (2) ("one of a series", by judgement).

### 4. Nothing reaches the site

- `speaking_items.RELEASED = False`. `publish_lesson.build` refuses any lesson with speaking units, as a package and
  as a draft, while it is False.
- `check_site_player.py --stub-speaking` (the brief: "the speaking units may be stubbed for this check") builds the
  package without them (`publish_lesson.stub_speaking`: a patient's line as a plain line, speaking points dropped,
  format 1.23) under `spike/out/site-player-stub/`, named `-stub`, never in the lesson and never released, and plays
  it in the site's own player.
- The pinned session section tag list (contracts 1.20.0, spike/publish/contracts.lock.json) has **no speaking keys**, so a speaking lesson's sections
  cannot carry tags the contracts accept (`LP-TEACHES-NOT-ALLOWED`, `LP-TEACHES-EMPTY`). For the stub alone these two
  are warnings (`publish_lesson.STUB_SET_ASIDE`); a real package still fails them. The speaking lessons' tags are
  proposed (keys of taxonomy v2, the Speaking course's) and approved with each lesson's final approval.

## Options considered

1. **Write to the site's draft contract directly** (no mapping module). Refused: the draft will change before it is
   released, and every change would touch the narration, the player and the publisher.
2. **Voice the patient's lines in a separate audio track.** Refused: one narration with a speaker per line keeps the
   captions, the timeline and the ear check as they are.
3. **Publish drafts with speaking units stripped.** Refused by the brief: the site cannot show speaking units, and a
   speaking lesson without them is not the lesson.

## Consequences

- Every built lesson renders the same before and after. Render proof, 2026-11-10: `render_compare.py` snapshot
  before-speak (main 93ec33f) against after-speak, all 29 lessons in C:\OET\lessons. The first compare found 21
  identical and the 8 Writing (teal) lessons different in `blocks.css` only (0 moments drawn differently): the three
  dialogue rules had been put in the teal look's always-on CSS. They moved to the end of `LAYOUT_CSS["dialogue"]`,
  so they are written only in a lesson that uses the layout (after the look's own wash rule, as before). The 8 were
  snapshotted again (after-speak2); with the 21 unchanged ones (the look's CSS reaches teal lessons only) the
  compare is **29 of 29 IDENTICAL**: every data file, every moment drawn, every board's timing.
- Release blockers, until the site acts: contracts with speaking units released (then `RELEASED = True` and the
  mapping checked against the released schema); speaking keys on the session section tag list; the site's player
  playing format 1.24 (`speaker` on a line, speaking pop-ups).
- To reverse: lines without `speaker` and a practice.json without speaking items build exactly as before; remove the
  `speakers` lesson type to refuse the fields again.

## Amendment (1), 2026-11-14: the site-player check runs on the real speaking packages

Context: since contracts 1.27.0 (ADR 055) every speaking item type is in the released contracts, and the speaking
lessons are built as real draft packages. Decision 4's `check_site_player.py --stub-speaking` is now a trap: the
practice-rule audit (issue #207, Batch 1 report) ran it on Speaking 1-3 as this ADR said; the check passed, but
publish refused its report, because the report fingerprints the stub's bundle (`package_fingerprint`) and publish
compares it with the package it sends (`publish_lesson.py`, the runbook 18c gate).

Decision: run `check_site_player.py` on a speaking lesson's real package, draft or release, with no flag, as for
every other lesson (runbook 18c). `--stub-speaking` stays only as a diagnostic: it checks how the site's player
draws the lesson without its speaking units, and its report never clears publish. Nothing else in decision 4
changes, and no code behaves differently: only the flag's help text says this now.

To reverse: restore the help text; the flag and `publish_lesson.stub_speaking` are unchanged.
