# 039 — Publishing lessons to oetacademy-sessions: the engine adopts the site's package contract

Date: 2026-10-22
Status: **Accepted** by the owner in chat, 2026-10-22 (the brief "Bundle format changelog 1.12 →
1.20, and ADR 039"). The seven decisions below are the owner's; this record does not reopen them.
The publish step itself (ENGINE-GAPS G1 to G7) is not built by this ADR: it is a later session,
blocked by decision 7.

## Context

- **The site's contract.** OETacademy imports a lesson as a *package*: a folder with
  `manifest.json`, `bundle.json`, `text.json`, `blocks.css`, `audio/<hash>.m4a` and `images/…`
  (oetacademy-web ADR-0005, contracts 1.7.0 today). Its ADR-0034 (accepted 2026-10-17) has the
  engine publish each package version as a GitHub release in the private, releases-only
  repository `siamingit/oetacademy-sessions`; a pipeline imports approved packages every six
  hours, never places a lesson in a course, and holds a new version of a lesson a human imported
  until the owner accepts it. Its `docs/contracts/ENGINE-GAPS.md` lists what the engine must add:
  G1 a publish step, G2 web audio, G2b images, G3 the manifest, G4 topic tags, G5 permanent
  section ids, G6 validation, G7 pinned contracts, G8 the rendering rules.
- **The engine has no publish step.** The eleven Grammar and Vocabulary lessons on the site were
  imported by hand on 2026-10-01 as package version 1, by the site's development builder. The
  ten Reading and Listening lessons are approved but not on the site.
- **Formats.** Contracts 1.7.0 accept `bundle_format_version` 1.8 to 1.12 only. The approved
  lessons are 1.12 (Grammar 1–8, Vocabulary 1–3), 1.13 (Reading 1), 1.14 (Reading 2), 1.16
  (Reading 3), 1.17 (Reading 4, 5) and 1.20 (Listening 1–5). The site adds 1.13 to 1.20 once it
  has a precise changelog: [docs/bundle-format-changelog.md](../bundle-format-changelog.md),
  written with this ADR.
- **Exam audio.** A Listening lesson plays the exercises release's own MP3 recordings inside its
  timeline (ADR 029, bundle 1.18), from `generated/exam-audio/`, byte for byte. The site's
  package accepts audio only as `audio/<name>.m4a`.
- **The approval.** The site's pipeline imports a package only when `lesson.approved.by` is
  `siavash` (ADR-0034 §2). The engine's `analysis/gates.json` records the final gate of the 21
  approved lessons as `siavash` (Grammar 1–8, Vocabulary 1–3, Reading 4 and 5, Listening 2),
  `Siavash` (Listening 1, 3, 4, 5), `maintainer (in chat 2026-10-06)` (Reading 1, 2) and
  `maintainer (in chat 2026-10-07)` (Reading 3).
- **Open in the engine's docs** until now: "Audio for the web" (docs/04-LESSON-BUNDLE.md §8 and
  §10, item 1) and whether the lesson folder's name is the public id (§10, item 2).

## Options considered

- **Where to publish** (the site's ADR-0034, Q1): a releases-only repository (chosen by the
  owner on 2026-10-17, and adopted here); releases in the engine's own repository; an R2 inbox.
- **Exam audio in a package**: reference the site's own exercise audio from the lesson, or carry
  every extract in the package. Carried (decision 2).
- **The approval's spelling**: rewrite `gates.json`, or write the owner's identifier when the
  manifest is written. Written in the manifest (decision 3); no lesson file changes.

## Decision (owner, 2026-10-22)

1. **The engine adopts the site's package contract**: oetacademy-web ADR-0034 and ENGINE-GAPS G1
   to G8. Packages are released in `siamingit/oetacademy-sessions`: one release per package
   version, tagged `<lesson id>-v<package_version>`, with exactly two assets, `manifest.json` and
   `<lesson id>-v<package_version>.zip`.
2. **Every exam extract a lesson plays is carried in the package** as `audio/<hash>.m4a`, like
   narration. The manifest marks each such file as an exam extract and records its source
   exercise set and part. The site's own exercise audio is never referenced.
3. **`lesson.approved.by` is written as `"siavash"` for all 21 approved lessons.** The owner gave
   final approval to all of them; the variant spellings in `gates.json` (`Siavash`,
   `maintainer (in chat …)`) are the same approval.
4. **Section tags**: topic-level where a section clearly teaches one topic, skill-level
   otherwise, from the same taxonomy as the exercises and the handouts. The site sends the
   allowed tag list. The engine proposes tags per section, and the owner approves them once per
   course.
5. **Publish order**: Reading 1–5 first, then Listening, then the eleven Grammar and Vocabulary
   lessons as package version 2.
6. **Listening 03, 04 and 05 publish now with the current exam audio.** After
   oetacademy-exercises #37 lands, they are republished as a new package version of the same
   lessons; the site holds a new version for the owner to accept. Listening 01 and 02 do not
   depend on #37.
7. **Open items, blocking the build of the publish step**: the site's contracts release that
   supports formats 1.13 to 1.20 (the engine pins that version, G7), and the allowed tag list
   (decision 4). Also needed: a token that can write releases to `siamingit/oetacademy-sessions`.

## How it is carried

- **Audio for the web** is decided: the site's ENGINE-GAPS G2, AAC-LC in `.m4a`, mono, 44.1 kHz,
  64 kb/s, each clip keeping its length and start, every `audio_file` rewritten to
  `audio/<hash>.m4a` in the published `bundle.json`. The WAV masters stay local, as before
  (docs/04-LESSON-BUNDLE.md §8 and §10).
- **The exam extracts** (decision 2) are encoded the same way. The lesson's own copy in
  `generated/exam-audio/` stays the release's file, byte for byte, as ADR 029 requires; the
  package holds an encoding of it, as it holds one of each narration master. Nothing else
  changes: no trim, no loudness change. Every time into an extract (`clip_in`, `clip_out`, a
  gloss's `heard`, a Listening board's word times) is a time in that file, so the encoding must
  keep its start exactly.
- **The lesson id** is the folder's name and is permanent (AGENTS.md §10b; the site's G5): this
  closes docs/04-LESSON-BUNDLE.md §10, item 2.
- **Decision 6 amends [ADR 032](032-listening-owner-answers-numbering-stable-ids.md) decision 2**
  for Listening 03, 04 and 05: the practice rendition of the audio is no longer a condition of
  their final approval (already given); it becomes a later package version. A Listening lesson
  approved after #37 is delivered uses the practice rendition, as ADR 032 says.
- **The final gate** in docs/03-RUNBOOK.md now says what follows it (publishing, once the step
  exists) and no longer makes #37 a condition for Listening 03 to 05.
- No lesson, bundle, gate record or code changes with this ADR.

## Found while recording this, not decided here

These are for the owner and the site; they are listed, not settled.

1. **The word bank's pronunciation clips** are a third kind of audio, beside narration and the
   exam extracts: `../vocab-audio/<word>.mp3`, copied from the exercises repository's word bank,
   played when the learner taps a gloss's speaker button (bundle 1.15). Reading 3–5 and
   Listening 3–5 use them. Decision 2 names exam extracts only, and the site's package accepts
   audio only as `audio/*.m4a`, so how these clips are carried is open.
2. **The manifest has no field for decision 2.** In contracts 1.7.0 a `media` entry may hold only
   `path`, `sha256`, `size`, `mime` and `duration_s` (`unevaluatedProperties: false`), so marking
   an exam extract with its set and part needs a contracts change, alongside the 1.13–1.20
   release.
3. **Paths inside the block `html`.** The speaker and "hear it in the recording" buttons name
   their audio in the block `html` (`data-audio`), so the publish step must rewrite those paths
   too, as it rewrites an image's `src`.
4. **What the approved bundles hold that the format does not** (the changelog, §12): a free-text
   `provenance` on one block each of Reading 5 and Listening 5, which the site's 1.12 schema
   refuses; Listening 2's `heard.file` without its folder; an internal field `_tokens` on 72
   blocks of Listening 4 and 5. Either the site accepts them or those lessons are rebuilt.
5. **`criteria` and `professions`** (G4) are not part of decision 4. The site's first import of
   Grammar 1 used `criteria` empty and `professions` `"all"`.
6. **Grammar 6's table board** `pages-07-08_t2` is shown whole by an exception the reference
   player knows by lesson and board id (ADR 011 amendment of 2026-10-12); the bundle does not
   say it (the changelog, §10).

## Consequences

- The site can review formats 1.13 to 1.20 from the changelog alone, and the engine has a script
  (`spike/scripts/bundle_fields.py`) that fails when an approved bundle holds a field the
  changelog does not list; it is run again at every format change.
- The publish step (G1 to G7) is built in a later session, once decision 7's items exist: it
  writes the package and the manifest, encodes the audio, validates against the pinned
  contracts, and creates the release.
- The eleven Grammar and Vocabulary lessons start at package version 2, which the site holds for
  the owner to accept (its ADR-0034, Q3).
- Listening 03, 04 and 05 will each have a second package version after #37.
- To reverse a decision: a new ADR. The decisions are the owner's.

## Amendment — 2026-10-23: the site's answers, and the publish step built

Status: **Accepted** by the owner in chat, 2026-10-22 (the site chat's answers, given in the brief
"build the publish step"), with two choices asked the same day (below). **It supersedes decision 2
where they differ**, and closes decision 7's first two items. The publish step (ENGINE-GAPS G1 to G7)
is built: `spike/scripts/publish_lesson.py` and `spike/scripts/lesson_package.py`.

### The owner's answers (2026-10-22)

1. **Contracts pinned: `contracts-v1.8.0`**, its zip's SHA-256
   `d98a94223c9915b845dd8ba4434c577deaff2e94c75583ddd00964f42a13f3dd` (checked: it matches). It
   accepts bundle formats 1.8 to 1.20.
2. **Audio** (replaces decision 2's "every exam extract as `audio/<hash>.m4a`"). Every audio file in
   the manifest has a `kind`:
   - `narration`: AAC `.m4a`, 64 kb/s, named by content hash;
   - `exam` and `pronunciation`: the **original MP3 files, byte for byte, never re-encoded**, named
     `audio/<the first 16 hex characters of the file's SHA-256>.mp3`. Every word time (`clip_in`,
     `clip_out`, `heard.start`/`end`, `listen.times`) is seconds into the original MP3; the site
     checks the hash against `exam.sha256`. `.mp3` is allowed for these two kinds only;
   - an `exam` file carries `exam: {set, part, stimulus, release}` (`part` `LA`, `LB` or `LC`), taken
     from the exercises release data, never guessed;
   - the `data-audio` of the block html (the speaker and "hear it" buttons) is rewritten to the
     package's paths, and after packaging no `data-audio`, `src` or file reference may point outside
     the package. This settles "Found while recording this", items 1 to 3.
3. **`lesson.professions` is `"all"`; every section has `criteria: []`** (item 5).
4. **The manifest names its taxonomy version.** Each section's `teaches` comes from the pinned
   contracts' `data/session-section-tags.json` (taxonomy v2): a topic key where the section clearly
   teaches one topic, otherwise a skill key; an introduction none. The owner approves the proposed
   tags once per course (decision 4; decision 7's tag list).
5. **Narration names collide across section folders** (Reading 3, Listening 3 to 5, Grammar 3 and 7,
   Vocabulary 3: one name, different audio). In the package every file has a unique name; content
   naming does it, and a check fails on any collision.
6. **The bundle quirks** of the changelog's §12 are tolerated by the site's importer (item 4). Their
   clean-up, and format 1.21's "show whole, no zoom" board flag (item 6), are a later session.
7. **Order**: Reading 1–5, then Listening, then the eleven Grammar and Vocabulary lessons as package
   version 2 (decision 5). Reading packages are package version 1.
8. **`lesson.approved` is `{"by": "siavash", "on": <the final gate's date in gates.json>}`** for every
   approved lesson (decision 3).

### Asked in chat, 2026-10-23

- **The dependency** `jsonschema==4.26.0` (MIT) is pinned in `requirements.txt` for G6's schema
  check (owner: yes).
- **Where the pinned contracts live.** The contracts release is in the private oetacademy-web and
  this repository is public, so the release is **not** committed (G7 says "keep it in the engine
  repo"; the owner chose otherwise): `spike/publish/contracts.lock.json` holds its tag and SHA-256;
  the zip is downloaded with `gh` into `%LOCALAPPDATA%\oetacademy-contracts\` and its hash checked
  every time it is read, every file read from the zip in memory. **Contract validation runs
  locally, at publish time**: `--package` and `--release` stop if the contracts are missing or their
  hash does not match; **CI skips it because the contracts repository is private** (owner,
  2026-10-23: no `CONTRACTS_READ_TOKEN`; the tests that need the contracts are skipped there, the
  others run).

### Decided by the agent under the brief (ADR 005; the owner may reverse any)

- **Narration names**: `audio/<the first 16 hex of the WAV master's SHA-256>.m4a`, the master's hash
  rather than the encoding's, so a name follows its content and two identical masters are one file.
- **The encoder's priming.** ffmpeg's AAC encoder adds 1024 samples (23.2 ms) of priming; its MP4
  muxer writes an edit list that skips them and plays exactly the master's length. For every
  narration file the step checks that edit list (one entry, its length the master's within 10 ms)
  and decodes the file as a browser does (the edit list applied) and compares it with the master:
  start (by cross-correlation) and length within 10 ms, or the package fails. Encoding is
  bit-exact (`-fflags +bitexact`, no metadata), so the same masters give the same bytes.
- **Where things are written**, all outside git: the package and its zip in
  `<L>/generated/package/<id>-v<n>/` and `<id>-v<n>.zip` (with an encoding cache and a report); the
  record of releases, package versions and published section ids (G5) in `<L>/analysis/publish.json`,
  written only by a release; the section tags, proposed and approved per course, in
  `<library>/course/section-tags.json`, beside the course index, with its review page
  `section-tags-review.html`. A section published once and gone later needs its replacements in
  `<L>/analysis/publish_retired.json`, or the package is refused.
- **The checks** are the three schemas and every rule of the site's validator (ADR-0005 §10 and
  ADR-0034 Amendment 13, codes `LP-…`, ported from its code at contracts 1.8.0), plus the engine's
  own (`PUB-…`): names, references inside the package, audio timing, the exam source in the release
  data, the zip. A package with any error is not written. The Reading packages were also checked
  with the site's own validator, run locally from its code: the same result.
- **A release** checks the package again, the course's tags approved, the zip's `manifest.json`
  byte-identical to the asset, and that the sessions repository holds exactly the versions the
  record lists; then `gh release create` (published, two assets), and checks the release it made.

### Consequences

- Decision 7: the contracts release and the tag list exist; publishing waits only for the owner's
  approval of each course's tags (and the write token is the owner's `gh` login).
- `docs/04-LESSON-BUNDLE.md` §8 said exam extracts are carried as `.m4a`; corrected to this
  amendment.
- To reverse: a new amendment. The answers are the owner's.
