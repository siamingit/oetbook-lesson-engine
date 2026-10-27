# 042 — Style C, "soft notebook": the lesson look from Writing 2 on, short lists on one board, and motion (bundle 1.22)

Date: 2026-10-26
Status: **Accepted**, amended the same day after the owner's review of Writing 2 (amendment (2), at
the end). **Partly superseded by [ADR 043](043-restyle-published-lessons-style-c.md)** (2026-10-27): the
22 published lessons are restyled in style C, and the zoom of decision 4 is for Writing's documents. The owner's decision of 2026-10-26, given in chat and recorded as
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

## Amendment — 2026-10-26 (2): the owner's review of Writing 2

Status: **Accepted**: the owner's decisions, given in chat on 2026-10-26 after he looked at Writing 2
in style C (the brief "revise style C after the owner's review, and rebuild Writing 2"). How each is
carried was decided by the agent under that brief (ADR 005); the owner may reverse any of it. This
amendment replaces decision 2's colours, its marker, its shadow and its outline, decision 4's lift
look, and the open item of the consequences; everything else above stands.

### Context

- The owner finds style C better overall. On screenshots of "The six criteria" and "How your letter is
  scored" he marked five problems:
  1. the marker highlight is too thick and covers the words;
  2. the background must be white, to match the site's theme;
  3. no purple or pink outline on lifted or active boxes: the lifted "Purpose" row reached past the
     table's left and right edges, and only its first cell was tinted;
  4. more colours, taken from the handouts' palette by meaning, and the clash of right with the
     word-class and tense colours settled;
  5. more creative board layouts, like his own Persian decks: a visual in place of a plain table where
     the content allows, each board following the matching slide of the lesson's own deck.
- The cause of 1: the band was multiplied (`mix-blend-mode`) inside the player's marks layer, and that
  layer has a z-index. A positioned element with a z-index is a group of its own (a stacking context),
  so the band blended with nothing under it and was laid flat, `#ffd27a`, over the lower 42% of the
  glyphs. The site's player draws its marks the same way (`.oa-marks`, z-index 6).

### Options considered

- **The marker.** As the phrase wrapper's own background, under its words (a change of method for the
  site, which draws every mark in an overlay); or the overlay kept, with nothing between the band and
  the frame making a group of its own, so the multiply reaches the words (chosen: one rule in each
  player; each mark keeps its place above the side notes by its own z-index).
- **Right or keep.** The site's success green `#1f6b3a`: 16.0 (CIEDE2000) from the adjective's
  word-class teal and 8.1 from the "up to now" tense accent, no better than the teal it replaces. The
  handouts' olive ("modal") `#556b00`: 26.8 from the adjective teal, 26.2 from the "up to now" teal and
  21.3 from its accent (chosen; the design system asks 20).
- **The six criteria's colours.** The handouts' ten tones and the site's own, the six that differ most
  from each other and at least 20 from right, wrong and the gloss amber (chosen: the handouts' blue,
  teal, magenta and violet, the site's rose and its band teal; 15.7 or more between any two). Left out:
  the handouts' "practice" red (4.1 from wrong), "pf" brown (8.5 from the gloss amber), the site's
  success green (15.1 from the olive of right). Each criterion also carries its monogram, so colour is
  never the only signal.
- **The layouts.** New block types (a new schema and a new renderer on the site); or the same blocks
  and data, laid out by the lesson's own `blocks.css` from classes and attributes on the block's html
  (chosen: no bundle field, nothing for the site's player, which draws the html the bundle gives and
  styles it with the lesson's stylesheet). Named per block in the lesson's `sections.json`,
  `block_layouts`, as boards are in `boards_fit` (ADR 041).
- **A letter with notes and arrows beside its lines** (the owner's example). Notes on a table board go
  under the table (rule 12, ADR 020): beside it needs a new rule of the bundle and of the site's player,
  and a narrower letter, which on a phone is already under body size. Not used: the zoom brings the
  line discussed to body size and the spotlight shows which line a note is about
  (docs/02-DESIGN-SYSTEM.md §7j).

### Decision

1. **The marker** is a light amber band `#ffe19c` behind the lower 38% of the line
   (`linear-gradient(transparent 62%, #ffe19c 62%)`), multiplied with what is under it, so the letters
   stay as dark as they are. The reference player's marks layer forms no group of its own in style C.
   `check_marks.py` fails a style C highlight whose band is not multiplied, sits inside a group, or is
   taller than 40% of its line.
2. **White**: the frame, the header, the board and the controls. Notes on a soft neutral tint
   `#f3f4f7`; the board's own sentences (a slide's sentence, a fixed sentence) on paper `#f8f4ec`.
3. **The lift** has no outline: a soft neutral shadow, `0 6px 20px rgba(20,32,31,0.12)` at a 720 px
   frame, and a very small scale (0.4% for a full-width row, 1% for a block, 1.5% for a tile or a card,
   2% for a contents item), inside the table's or the board's edges. A lifted row lifts as one row: its
   shadow is the row's, its cells keep their own tints, nothing is repainted. The active cell keeps a
   soft amber (rule 11).
4. **Colour by meaning** (docs/02-DESIGN-SYSTEM.md §1a): right or keep olive `#556b00` on `#eef3d2`
   with a tick; wrong or leave out red `#b42318` on `#fdecea` with a cross; a word card, "Meaning",
   "Word" and the key word in the gloss amber `#8a5300` on `#fdf0d5` (no dark card); a table with a solid
   header row in its section's colour and white words in sentence case (no capitals), its body rows in
   that colour's tint. The six criteria, each its colour and its monogram, used the same way everywhere
   in a lesson (the criterion's card, its section's tables and tints, its contents item, its tile):

   | Criterion | Monogram | Ink / tint | From |
   |---|---|---|---|
   | Purpose | P | `#1d5fb4` / `#e2eefb` | the handouts' blue ("past") |
   | Content | C | `#be185d` / `#fce7f1` | the site's rose |
   | Conciseness and Clarity | C&C | `#0f766e` / `#d7f0ec` | the handouts' teal ("teach") |
   | Genre and Style | G&S | `#9d1f8f` / `#fbe7f6` | the handouts' magenta ("prog") |
   | Organisation and Layout | O&L | `#0e4a55` / `#dcecef` | the site's band teal |
   | Language | L | `#5b3fc4` / `#ece6fb` | the handouts' violet ("test") |

   A section is a criterion's when its title is the criterion's name; its term box "The criterion" is
   drawn as the criterion's card: the monogram in a circle beside a pill in the criterion's tint, as on
   the owner's slides.
5. **Board layouts** (docs/02-DESIGN-SYSTEM.md §7j): tiles, scorecards, cards, steps, a flow, bins, a
   fix, changes, a stack, case notes, a letter, a checklist, two options side by side; for each board,
   the matching slide of the lesson's deck is looked at and its visual idea carried over. A layout never
   changes a word, its order, an id, a cue or a state (`style_c.layout_html` refuses one that would).
6. **Bundle format 1.22 is amended, not raised**: no 1.22 lesson is published and the site has not yet
   built 1.22. Rule 53: the marker's colour and height, and that its multiply must reach the words; the
   strike `#b42318`. Rule 54: the lift's look, in `blocks.css`, with no outline. No field is added or
   removed; the site need not set a frame ground. The changelog §9b and the text for the site say so;
   the site is told on its issue #173.
7. **Checks.** Besides `check_marks.py` (1): the structural check's colour rule is narrowed. Right is no
   longer teal, so a style C lesson may draw tense colours and adjective or adverb word marks; a lesson
   that draws the criteria's colours may not, since the teal of Conciseness and Clarity is 1.8 from the
   adjective teal and 17.2 from the "up to now" teal.

### Consequences

- Writing 2 is rebuilt with all of the above (block layouts on 15 blocks of 14 boards). No narration,
  audio, id or time changed. The fit is better than before: three pictures that had to be cleared stay,
  one board needs no tightening, two tables are set larger (The six criteria at 3.2% of the frame, the
  Purpose letter at 3.0%). Because the Purpose letter is now set near body size, its seven zooms are no
  longer needed (the zoom is for a document at 2.8% or less, decision 4).
- The 22 published lessons are unchanged: proven by the render comparison before and after the change (docs/03-RUNBOOK.md, "Changing shared code"; `render_compare.py` snapshots `before-sc2` on the code of main at 5ba130a and `after-sc2` on this change, 2026-10-26): **22 of 22 identical**, 662 data files byte for byte (bundles, texts, stylesheets, timelines, fits) and 150,072 moments at the phone and laptop frames drawn identically, with no board timing difference.
- To reverse a layout for one board: remove its block from `block_layouts` and rebuild the player
  (free); the table is drawn as the handouts draw a table. The colours, the marker and the lift are
  `style_c.py`'s, and only a lesson in style C takes them.
