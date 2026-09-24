# 004 — The lesson bundle is the contract between pipeline and website

Date: 2026-09-24
Status: **Accepted** by the maintainer in chat, 2026-09-24. The contract is
docs/04-LESSON-BUNDLE.md, format version 1.0.

## Context

The final product is a website. Its lesson page will be built later, around
each lesson: the player in the centre, a contents panel, progress, a resume
position, and an AI chat that answers questions about the lesson. None of that
page exists yet, but about sixty lessons will be built before it does. If the
site later needs something the pipeline did not write down, every lesson would
have to be rebuilt.

The only consumer so far was the pipeline's own player
(`board_player_template.html`). A review of it on 2026-09-24 found that it
worked out part of the lesson for itself, where a website would have had to
copy its rules:

- when a working block appears, when a diagram part is drawn, and that a
  fixed diagram's parts stay through an erasure; 9 of Grammar 1's diagram
  parts had no reveal time at all and relied on a fallback in the player;
- which section a board belongs to, found by comparing start times;
- how long the reading pointer holds (a constant in the player);
- the stylesheet the blocks' HTML is written against, which existed only
  inside the player.

The bundle also lacked data the site needs: the categories and the lesson
description (only in `sections.json`), section ids, and block fields the HTML
was drawn from but the data did not carry (tense tags and their chip labels,
exercise item numbers, table column colours).

## Options considered

1. **Let the website read the pipeline's working files** (`sections.json`,
   `screens.json`, `narration.json`, audio indexes). No new format, but the
   site would depend on pipeline internals, which change as the pipeline is
   still exploratory, and would re-implement the timeline and visibility rules.
2. **Treat the current player as the product** and embed it in the site. The
   player is a review tool: its layout, controls and review subtitle are not
   the page's design, and it would tie the site to spike code.
3. **One versioned bundle per lesson as the contract.** Everything a renderer
   needs is stated as data; the player becomes a reference renderer that proves
   the bundle is complete.

## Decision

Option 3.

- Each lesson's `generated/lesson-player/` holds its bundle: `bundle.json`,
  `text.json` (the clean text of every section, for search, the AI chat and
  accessibility) and `blocks.css`, plus the audio clips `bundle.json` names.
  Every file and field is in docs/04-LESSON-BUNDLE.md.
- Both JSON files carry `format` and `format_version`, starting at `"1.0"`. A
  minor version only adds fields; a major version is a deliberate rebuild of
  the library, recorded in a new ADR.
- Everything a renderer needs is data in the bundle; the renderer applies only
  the rules listed in the contract. If the website needs something that is not
  there, the bundle is wrong and gets a new version; the site never re-derives it.
- `player.html` is a reference renderer only, not part of the contract.
- Ids are deterministic from the lesson's approved content, and the contract
  lists what changes them. The website keys student state on them (a resume
  position is an utterance id plus an offset), never on lesson times.
- The "nothing outside the 16:9 frame" rule applies to the lesson frame; the
  website page around the frame may have its own panels and controls
  (docs/00-PRODUCT.md §1, docs/02-DESIGN-SYSTEM.md §1).
- Audio for the web is an open decision: the WAV clips are masters and stay
  local; a compressed format is chosen when the site is built.

## Consequences

- `build_lesson_player.py` writes the bundle in this format. Grammar 1 was
  rebuilt with no paid calls: every id, time, cue and reading run is identical
  to the build before, two rebuilds are byte-identical, the structural and mark
  checks pass, and the old and new players show the same thing at 1,200
  sampled moments in a headless browser.
- A change to the bundle's fields is a format change and needs the maintainer
  (AGENTS.md §3); it is recorded as a new format version and a new ADR.
- The website can be designed and built later against docs/04-LESSON-BUNDLE.md
  alone, without reading pipeline code.
- Choosing the web audio format later does not require rebuilding any bundle,
  since each clip keeps its length whatever the encoding.
