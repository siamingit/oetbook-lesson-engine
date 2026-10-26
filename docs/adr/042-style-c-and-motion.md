# 042 — Style C, "soft notebook": the lesson look from Writing 2 on, short lists on one board, and motion (bundle 1.22)

Date: 2026-10-26
Status: **Accepted**: the owner's decision of 2026-10-26, given in chat and recorded as
siamingit/oetbook-lesson-engine issue #46 (the design reference: tokens, effects and three reference
boards). How it is carried (the per-lesson style, the bundle format, which board states take which
effect, the checks) was decided by the agent under the brief "make style C the lesson look, add motion
effects, and rebuild Writing 2 in it" (ADR 005); the owner may reverse any of it.

## Context

- On 2026-10-26 the owner looked at Writing 2 (`writing-02-assessment-criteria`, built to its final
  gate, issue #45) and said the look tires the eye: white, grey, the same everywhere. He wants the colour
  variety and warmth of the handouts on the site. He compared three styles on Writing 2's own boards and
  chose style C, "soft notebook", for the contents board and every teaching board.
- He also asked for motion: fade, zoom or enlarge, shrink and the like.
- Writing 2's contents board ran over "two boards": its nine items did not fit, so the fit cleared the
  first ones to make room for the last (a state's `clears`, ADR 011).
- 22 lessons are published (Grammar 1–8, Vocabulary 1–3, Reading 1–5, Listening 1–5, Writing 1). The
  owner: they are not restyled now; that is a later decision of his.
- The site plays the lessons with its own player (oetacademy-web ADR-0023, ADR-0034). It loads each
  lesson's own `blocks.css` into a cascade layer under its player's own rules, sets the classes the
  bundle contract names (`.on`, `.spot`, `tr.focus`, `td.active`, `v-right`/`v-wrong`, `data-oa-layer`),
  draws the marks itself, removes erased notes at once and hides cleared ones at once, and accepts bundle
  formats 1.8 to 1.21 only (contracts 1.10.0).

## Options considered

- **Restyle every lesson, or only new ones.** Every lesson: the owner said no. Only new ones: chosen.
- **How a lesson says its look.** By its id or type (Writing 2 is the first Writing lesson after Writing
  1, so no rule of type fits); by a date; or by a field of its own config, `analysis/sections.json`
  `lesson.style` (chosen: it is where the owner's per-lesson decisions live, as `tense_lesson` and
  `bundle_format` do; a lesson without it keeps the look it was built in, byte for byte).
- **Where the look lives.** In the site's player (a site change for every look); or in the lesson's own
  `blocks.css`, which the contract already makes per lesson (chosen: the site plays the static look and
  the spotlight's lift with no change).
- **The effects.** All in CSS keyed on classes players already set (possible for the soft appear and the
  spotlight's lift and fade, not for a lift of a block that is not a table row, the zoom, the marks
  drawn in, or a note that shrinks as it goes: the site removes or hides those at once and redraws its
  marks every frame); or a new bundle format with the data the rest needs (chosen, 1.22).
- **The zoom's trigger.** The spotlight's whole row (a wide row cannot be zoomed without cutting it, and
  the note under the table would leave the view); every reading of the table's words (Writing 2 reads
  only 8 words of its letter aloud); or the narration's own marks on the line, until it moves on to a
  note (chosen: a mark is exactly "the narration is on this line").

## Decision

1. **Style C is the look of Writing 2 and of every lesson built after it.** A lesson is in style C when
   its `sections.json` has `lesson.style` "c" (`build_sections.py <L> --style c`); a lesson config made
   from now on is written with it. A lesson without it keeps its look; the 22 published lessons have
   none, and their `blocks.css`, bundles and players stay byte for byte as they are.
2. **The look**, exactly as issue #46 gives it (docs/02-DESIGN-SYSTEM.md §1a): the frame ground lilac
   `#f3f0fb`; ink `#1c1733`, muted `#4a4466` / `#6b6585`, faint `#a49fbc`; panels and cards white, radius
   16 to 24 px (rows 16, cards 20, big panels 24), no borders, no left-border cards; the marker highlight
   `linear-gradient(transparent 55%, #ffd27a 55%)` (teal `#b8ece4` and blue `#c8dcfa` markers named for a
   sentence of several parts that a table below names; not used yet); number badges 44 px rounded squares
   (radius 12) in five soft tints in turn; column labels 14 px, bold, letter-spaced capitals, Wrong in
   `#b83b28`, Accurate or right in `#0f766e`; wrong text `#b83b28` on `#fde5e0`; the gloss, "Meaning" and
   "Word" a dark card `#1c1733` with white text and an amber chip `#ffd27a`; small chips `#ece6fb` /
   `#5b3fc4`, radius 10; type IBM Plex Sans, 400 to 700; a shadow `0 10px 30px rgba(91,63,196,0.18)` only
   on the active element. Colour still carries meaning: teal right or keep, red wrong or leave out, amber
   the key word or the request, blue the problem, violet a label. The rules that hold are kept: the 16:9
   frame, one board per topic, the section title alone in the header, colour never the only signal (the
   cross and the tick stay), sizes as shares of the frame and their floors.
3. **A short list fits on one board.** A lesson's contents of up to 12 parts is on one board, in two
   columns if needed, never cleared to make room. In style C the contents board is two columns of white
   rows beside the board's picture. The screens stage (`build_lesson_boards.py`) fails a style C lesson
   with more than 12 parts (group them into categories); the structural check (`check_board_page.py`)
   fails a style C lesson whose contents items are cleared, and warns on an older lesson.
4. **Motion** (docs/02-DESIGN-SYSTEM.md §8g), every motion 150 to 400 ms, eased, never bouncy, none
   under `prefers-reduced-motion`:
   - **Soft appear**: a new block fades in and rises 1.2% of the frame (0.3 s). `blocks.css`.
   - **Fade**: on a table board the rows other than the one being taught at half strength (the
     spotlight, rule 11, at 50% in place of 30%). `blocks.css`.
   - **Lift**: the element being discussed grows a little, takes the shadow and a lilac outline
     `#c9bdf5`, and settles back when the narration moves on (0.25 s): the table's row in focus (1.5%,
     `blocks.css` on the spotlight) and, by the bundle's `effects`, each contents item while it is named
     and each of two or more fixed sentences or cards while it is read (2%).
   - **Zoom**: the view zooms onto a line of a document (a letter, case notes) while the narration is on
     it, then back out (0.35 s), where the document is set well under body size: from a mark the
     narration draws on the line until it moves on to a note, at the scale that sets the line at body
     size, never above 2.2 and only as far as every note shown stays in view.
   - **Strike drawn**: a strike is drawn across the wrong phrase from left to right as it is named
     (0.25 s); **marker sweep**: a highlight sweeps in from left to right (0.3 s), as a marker band.
   - **Shrink**: a note that goes, by an erase or a clear, fades and shrinks (0.25 s); a cleared note's
     room closes up instead of jumping.
5. **Bundle format 1.22**: `lesson.style` ("c") and each state's `effects` (`lift`, `zoom`), with rules
   53 to 55 (docs/04-LESSON-BUNDLE.md; docs/bundle-format-changelog.md §9b). A lesson is 1.22 only when
   it is in style C. The text for the site is docs/integration/1.22-changelog-for-site.md, sent as
   siamingit/oetacademy-web issue #173 (label `from-lesson-engine`).
6. **Checks.** The engine's measuring checks measure the board at rest (`--sc-motion: 0`, no
   transitions): a lift or a zoom moves no word in the layout. In style C a table's column labels are
   drawn in capitals by design; the overflow check checks their words only. The structural check checks
   `lesson.style` and every effect.
7. **The font.** IBM Plex Sans is the site's own font (oetacademy-web ADR-0030). `blocks.css` asks for
   `var(--font-plex, "IBM Plex Sans")`, which the site defines. The reference player embeds a pinned copy
   (Fontsource 5.2.5, SIL OFL 1.1, latin and latin-ext, 400 to 700), its SHA-256s in
   `spike/fonts/ibm-plex-sans.lock.json`, downloaded once by `style_c.py --fetch-fonts` into
   `%LOCALAPPDATA%\oet-fonts\` and never committed; the fit and every check measure with it.

## Consequences

- Writing 2 is rebuilt in style C (format 1.22). No narration, no audio and no id changed; its
  contents are on one board.
- **The site must change before Writing 2 can be published**: its contracts and player accept 1.21 at
  most, and the effects with data, the marks' looks and the shrinking notes are its player's. The request is
  oetacademy-web issue #173. Until it releases contracts that accept 1.22 and the engine pins them (a new amendment of ADR 039), Writing 2 is
  not packaged. The static look and the spotlight's lift and fade need no site change.
- The 22 published lessons are unchanged, proven by the render comparison before and after the change
  (docs/03-RUNBOOK.md, "Changing shared code"; `render_compare.py` snapshots `before-stylec` on the code
  of main at 10ba5c5 and `after-stylec` on this change, 2026-10-26): **22 of 22 identical**, 662 data
  files byte for byte (bundles, texts, stylesheets, timelines, fits) and 150,072 moments at the phone and
  laptop frames drawn identically, with no board timing difference.
- **Open, for the owner**: style C's teal of right (`#0f766e`) is 1.8 (CIEDE2000) from the word-class
  adjective teal `#1F7A73` and 17.2 from the tense teal of "up to now" (the design system asks 20). Until
  other colours are chosen, the structural check fails a style C lesson that draws an adjective or adverb
  word mark or tense colours. Writing 2 draws neither. Restyling the 22 published lessons is the owner's
  later decision.
- To reverse for one lesson: remove `lesson.style` from its `sections.json` and rebuild its boards, fit and
  player (free); it returns to its earlier look and format. To reverse the default for new lessons: a new
  ADR.
