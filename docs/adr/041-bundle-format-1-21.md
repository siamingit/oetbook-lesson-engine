# 041 — Bundle format 1.21: a board shown whole, and the approved bundles' stray data cleaned up

Date: 2026-10-23
Status: **Accepted** by the owner in chat, 2026-10-23 (the brief "Release lesson-bundle format 1.21":
a per-board flag meaning "show this board in full, never auto-zoom", the Grammar 6 special case moved
out of the player into the data, the clean-up of the approved bundles' inconsistent fields, a
changelog entry for the site, no visible change, no package published). The field's name, where the
lessons state it and how the version is chosen were decided by the agent under that brief (ADR 005);
the owner may reverse any of them.

## Context

- **Grammar 6's table board.** On `grammar-06-clause`, board `pages-07-08_t2` (18:30 to 27:32), the
  owner decided on 2026-10-12 that the whole table shows at every moment: no camera zoom onto the
  active cell, no pan to the notes, and the player's guard sets the table below its 1.9% floor on the
  device as far as the whole table and its notes need ([ADR 011](011-boards-fit.md), amendment of
  2026-10-12). The reference player knew it by a constant naming the lesson and the board
  (`TABLE_FREE` in `board_player_template.html`); the bundle did not say it, so a website drawing from
  the bundle alone zooms that board like any table board (docs/bundle-format-changelog.md §10;
  [ADR 039](039-publish-to-oetacademy-sessions.md), "Found while recording this", item 6). That breaks
  the contract's first rule: everything a page needs is stated in the bundle
  (docs/04-LESSON-BUNDLE.md §1).
- **Data outside the format** in four approved bundles (docs/bundle-format-changelog.md §12): a
  free-text `provenance` on the title board's description in Reading 5 and Listening 5; Listening 2's
  `heard` with a bare file name and an extra `stimulus`; the build field `_tokens` on the 36
  code-built section questions of Listening 4 and of Listening 5. The site's importer tolerates them
  (ADR 039 amendment, answer 6), and their clean-up was left to this session.
- **The site's contract** pinned by the engine, `contracts-v1.8.0`, accepts bundle formats 1.8 to
  1.20 in `bundle.json`, `text.json` and the manifest's `bundle_format_version` (enumerations), and
  lets an unknown board field through.

## Options considered

- **The field.** `"fit": "whole"` on the board, absent otherwise (chosen); `"noZoom": true` (the
  bundle's names are lower case with underscores, and "no zoom" says only half of it: the board is
  also set smaller than the tables' floor to stay whole); `"zoom": "none"` (a state's `zoom` already
  means something else on a map board, 1.14). A string leaves room for another value later without a
  new field. "Whole" is the word the contract already uses for this ("shown whole", rules 36, 37).
- **Where a lesson states it.** In the lesson's `analysis/sections.json`, `boards_fit`, by board id
  (chosen: the owner's per-lesson decisions already live there, such as `diagram_pages`; the builder
  refuses a name that is not such a board, so a regenerated section cannot lose it silently); in the
  section's `screens.json` (rewritten by every `--render`); in the fit (`fit.json` is measured, not
  decided).
- **The version of a bundle changed by the clean-up.** The cleaned bundles are valid at their own
  versions (1.17, 1.20): what they lost was never in the format. The brief asks for every changed
  bundle at 1.21. Making 1.21 the format of a whole kind of lesson (every Listening lesson, every
  Part C lesson) would change Listening 1 and 3 and Reading 4 the next time they are rebuilt, though
  nothing in them changes. So the version is raised only where the lesson says so: `sections.json`
  `lesson.bundle_format` (chosen).

## Decision

1. **Bundle format 1.21** adds one optional board field, `fit`. Its one value, `"whole"`: the board
   is shown whole on every device at every moment. The renderer never zooms the view onto a cell or
   a row, nor pans the table up to its notes (rule 13 does not apply); where the board does not fit
   the device, the guard (rule 41) sets the board smaller, the table's text below its 1.9% floor if it
   must (the other blocks stop at 2.6%), at the largest size that fits. Absent: as before. Only on a
   table board the camera may zoom (a board with `table`; not a question board, a Listening board or
   a map board, which never zoom). This is rule 52 of the contract.
2. **Grammar 6's board carries it**: `sections.json` `boards_fit: {"pages-07-08_t2": "whole"}`. The
   reference player reads the board's `fit`; the constant naming the lesson and board is gone. The
   fit (`fit_boards.py`, guard off) plans the board as before.
3. **The clean-up**, in the builder, so every bundle written from now on is clean:
   - a title board's description written by the agent (`description_status` "agent (...)" in
     `sections.json`) has `provenance` `authored`, its record kept as the block's review note
     (`build_lesson_boards.py`); a provenance is always one of the format's values;
   - a gloss's `heard` is `{file, start, end}`, `file` relative to the bundle's folder
     (`../exam-audio/<file>`), in every Listening lesson (a Part A lesson wrote the bare name and the
     extract's id before);
   - a section's code-built question carries no build field (`_tokens`).
4. **The version rule.** A lesson's format stays the one its kind is written in (1.12, 1.13, 1.14,
   1.16, 1.17, 1.20), except: a lesson with a board that has `fit` is 1.21, and a lesson whose
   `sections.json` declares `lesson.bundle_format` "1.21" is 1.21. Reading 5, Listening 2, Listening
   4 and Listening 5, whose bundles the clean-up changes, declare it; with Grammar 6 they are the five
   lessons rebuilt at 1.21. Every other lesson's bundle stays byte for byte. A 1.21 bundle never
   holds the data of changelog §12.
5. **Checks.** The structural check (`check_board_page.py`) and the package check
   (`lesson_package.py`, the engine's code `PUB-FIT`) fail a `fit` with another value, on a board that
   is not a zoomable table board, or in a bundle before 1.21; `bundle_fields.py` counts `fit` as an
   enumeration; the changelog's field index lists `boards[].fit` and its value.
6. **Release.** The format's changelog entry is in docs/bundle-format-changelog.md (§9a); the text
   for the site's copy of it is docs/integration/1.21-changelog-for-site.md. From 1.21 on, a format
   version is tagged `bundle-format-v<version>` on the commit that releases it.

## Consequences

- Nothing a learner sees or hears changes in any approved lesson: proven before and after on all 21
  (pixel screenshots, the render comparison, the data files). The five rebuilt lessons keep their
  final approval.
- **The site's contract `contracts-v1.8.0` refuses 1.21** (the three enumerations above), so none of
  the five can be packaged for the site until it releases contracts that accept 1.21 and the engine
  pins them (a new amendment of ADR 039). Until then the published v1 packages of Reading 5 and
  Listening 2, 4 and 5 stay as they are, with the data the site tolerates.
- When the site accepts 1.21: Grammar 6 is published as package version 2 with the other ten Grammar
  and Vocabulary lessons (ADR 039, decision 5), and Reading 5, Listening 2, 4 and 5 are republished as
  package version 2.
- To reverse decision 2: remove `boards_fit` from Grammar 6's `sections.json` and rebuild the player
  (`build_lesson_player.py`, free); the board then zooms like any table board. To reverse the version
  rule for one lesson: remove its `lesson.bundle_format` and rebuild.
