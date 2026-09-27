# Lesson Bundle — the contract between pipeline and website

What the pipeline hands to the website for each lesson, file by file and field
by field. Written 2026-09-24, before the website exists, so that the lessons
built now never need rebuilding for it.

**Format version 1.8. Status: Accepted** by the maintainer: 1.0 on 2026-09-24
(docs/adr/004-lesson-bundle-contract.md); 1.1, references to other lessons, on
2026-09-25 (docs/adr/006-cross-lesson-references-and-course-index.md); 1.2,
table boards, on 2026-09-25 (docs/adr/007-table-boards.md); 1.3, the board style
and trimmed clips, on 2026-09-25 (docs/adr/008-board-style.md); 1.4, the style on
table boards and per-board colours, the same day (ADR 008, extension); 1.5, tense
colours by lesson, the same day (ADR 008, second extension); 1.6, choice tables,
gaps and marks in table cells, the same day (docs/adr/009-choice-tables-and-gaps.md); 1.7,
the clause diagram, on 2026-09-27 (docs/adr/010-clause-diagram.md); 1.8, clears
and tight boards so every block fits, the same day (docs/adr/011-boards-fit.md).
A change to it is a new format version (§3), recorded in a new ADR.

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-09-24 | first version |
| 1.1 | 2026-09-25 | `refs` on every utterance (§5) and every narration entry of `text.json` (§6): the other lessons the utterance refers to, by id |
| 1.2 | 2026-09-25 | table boards (docs/02-DESIGN-SYSTEM.md §7, "Tables"): a table block's `core`, `typed`, `col_widths`, `font`; a working block's `beside`; the `type` cue; a board's `table` and `focus`; a state's `row`; rules 10 to 13 (§5) |
| 1.3 | 2026-09-25 | the board style (docs/02-DESIGN-SYSTEM.md §7c): a block's `role`, `style`, `card`, `pin`, `fold_into`, `flow`, `band`; a board's `pinned` and `wordmarks`; an utterance's `clip_in` and `clip_out`; rules 14 to 17 |
| 1.4 | 2026-09-25 | a word mark may name a table cell (`row`, `col`); a board's `palette` (ADR 008, extension) |
| 1.5 | 2026-09-25 | the lesson's `tense_colours`; a board's `palette` is no longer written (word-class colours are the same everywhere; ADR 008, second extension) |
| 1.6 | 2026-09-25 | choice tables: a table block's `verdicts`, a board's `verdicts` with times; a mark on a core table names its cell (`row`, `col`), an arrow's end its cell (`to_row`, `to_col`); a typed part inside printed words carries the class `gap`; rules 6, 10 and 18 (ADR 009) |
| 1.7 | 2026-09-27 | the clause diagram: the block type `clauses`, its `items` (`{kind, text, piece, part}`); rule 20 (ADR 010) |
| 1.8 | 2026-09-27 | every block fits the board: a state's `clears`, a board's `tight`; a table's `font` may be set by the fit; rules 21 to 23 (ADR 011) |

---

## 1. The rule

The website renders a lesson from its bundle and nothing else. Everything a page
needs to show the lesson is stated in the bundle as data: what is on the board at
every moment, what the student hears, the contents, the text. The website
decides how things look and behave around the lesson (docs/00-PRODUCT.md §1: the
page may have panels and controls outside the lesson frame). It never works out
lesson content from the pipeline's rules.

If the website finds it needs something the bundle does not state, the bundle is
wrong. The fix is a new format version from the pipeline, never logic in the
website that re-derives it.

**The current player is a reference renderer only.**
`generated/lesson-player/player.html` (from `spike/scripts/board_player_template.html`)
shows that the bundle is complete and correct; it is not the website, and none of
its layout, controls, review subtitle or silent-preview banner is part of the
contract. It reads the bundle and computes nothing the bundle does not state; the
only rules it applies are the ones in §5 below.

---

## 2. Files

One folder per lesson: `<lesson>/generated/lesson-player/`.

| File | Contract | What it is |
|---|---|---|
| `bundle.json` | **yes** | the lesson: structure, blocks, boards, timing, cues, reading pointer |
| `text.json` | **yes** | the clean text of every section (§6) |
| `blocks.css` | **yes** | the stylesheet each block's `html` is written against (§7) |
| audio, `../<section>/boards/audio/<hash>.wav` | **yes** | one clip per utterance, named in `bundle.json` (§8) |
| `player.html` | no | the reference renderer, with the bundle embedded |
| `timeline.json`, `audio_index.json` | no | build intermediates: the timeline is repeated in `bundle.json`; the audio index holds per-word timings and voice settings the website does not need |
| `marks_check.json` | no | the mark check's report |

`generated/lesson-preview/silent/` holds the same files for the silent preview
(`meta.silent` true, no audio). A silent bundle is for review and is never
published.

---

## 3. Versions

Both JSON files carry `format` (`oetbook-lesson-bundle`, `oetbook-lesson-text`)
and `format_version`, `"MAJOR.MINOR"`.

- **Minor** (1.0 → 1.1): fields are added. A reader of 1.x ignores fields it
  does not know, and every 1.x bundle stays readable.
- **Major** (1.x → 2.0): a field is removed, renamed or changes meaning. The
  website refuses a major version it does not know. Moving the library to a new
  major version is a deliberate rebuild, recorded in an ADR.

The website must not read anything a bundle does not declare. A field not
described here is not part of the contract, even if it is present.

---

## 4. Identifiers

Every id is a deterministic function of the lesson's approved content. None
depends on time, audio, build order or the run that built it. Rebuilding the
bundle produces a byte-identical file (checked on Grammar 1, 2026-09-24: two
rebuilds identical, and every section, board, state, utterance, block and cue id
identical to the build before this format).

| Id | Example | Made from | Scope |
|---|---|---|---|
| lesson | `grammar-01-verb-tenses` | the lesson folder's name | library |
| section | `page-13`, `pages-05-06` | the deck pages it covers | lesson |
| category | `c2` | its position on the deck's contents slide | lesson |
| block | `page-13_k07` | section + the block's place in the section's screen content, in document order (`k01`, `k02`, …) | lesson |
| diagram part | `page-11_k02.3` | block + the part's number in the diagram | lesson |
| board | `page-13_t2` | section + the topic's number in the screen content | lesson |
| state | `page-13_t2.s3` | board + the state's number in the board's layout | lesson |
| utterance | `page-13_t2.s3.u4` | state + the utterance's number in that state | lesson |
| cue | `c2` | its number in its utterance | utterance |

### What changes an id, and what does not

Ids do **not** change when:

- the bundle is rebuilt;
- audio is re-synthesised (a lexicon change, a new voice speed); times change, ids do not;
- screens or narration are re-rendered from their saved model responses;
- on-screen text is corrected by an override (a screen edit must not move a
  board's layout: methodology §18, too-broad rules).

Ids **do** change when the content they name is replaced:

- a narration rewrite of some states (`write_narration.py --states`) renumbers the
  utterances of a state that gains or loses one, and no others;
- regenerating a section's screens or narration from a new model response issues
  new board, state, block and utterance ids **for that section only**;
- a change to the layout rules that moves an erase point renumbers the states,
  and so the utterances, of the boards it moves;
- a change of deck that regroups pages changes section ids.

### What the website should key on

- **Resume position:** utterance id plus seconds into that utterance, with the
  section id as a fallback when the utterance no longer exists. Never a bare
  lesson time: times move when audio is re-made.
- **Progress:** section ids.
- **Chat citations and deep links:** utterance ids for what was said, block ids
  for what was on the board.

---

## 5. `bundle.json`

Times are seconds from the start of the lesson, rounded to milliseconds.

### Top level

| Field | Type | Meaning |
|---|---|---|
| `format` | string | `"oetbook-lesson-bundle"` |
| `format_version` | string | `"1.8"` |
| `lesson` | object | the lesson (below) |
| `sections` | array | the sections in lesson order, the introduction first |
| `meta` | object | how the timeline was built |
| `stylesheet` | string | `"blocks.css"`, relative to `bundle.json` |
| `text` | string | `"text.json"`, relative to `bundle.json` |
| `blocks` | object | every block shown in the lesson, by id |
| `boards` | array | the boards in playing order |
| `events` | array | board changes and erasures in time order |

### `lesson`

| Field | Meaning |
|---|---|
| `id` | the lesson id |
| `title` | the lesson title, from the deck |
| `description` | one line in the maintainer's own words (docs/00-PRODUCT.md §2a); may be null |
| `tense_colours` | 1.5. True in a lesson about tenses: only then do tense labels, timelines, category cards and table headers carry tense family colours; otherwise every block's `html` draws them neutral (docs/02-DESIGN-SYSTEM.md §7c) |
| `categories` | `[{id, title, sections: [section id, …]}]`, in the order of the deck's contents slide, exactly as the contents board shows them. Empty for a deck with no contents slide. The introduction is in no category |

### `sections[]`

| Field | Meaning |
|---|---|
| `id` | the section id |
| `title` | the section title: the slide heading, corrected, or the maintainer's title |
| `pages` | the deck pages it covers (for traceability, not for display) |
| `intro` | true for the introduction (the title board and the contents board) |
| `category` | category id, or null |
| `start`, `end` | the section plays from `start` until the next section's `start` (`end`) |
| `boards` | its board ids in playing order |

The contents list is `sections`, grouped by `lesson.categories`, one entry per
section and nothing smaller (docs/00-PRODUCT.md §1). Choosing a section seeks to
its `start`.

### `meta`

| Field | Meaning |
|---|---|
| `total_duration_s` | the lesson's length |
| `reading_hold_s` | how long the reading pointer stays on the last word read (§5, rules) |
| `silent` | true for a silent preview; never publish one |
| `wpm` | the estimate's words per minute, silent preview only; otherwise null |
| `voice`, `model`, `speed` | the voice the audio was made with |
| `utterance_gap_s`, `state_gap_s`, `board_gap_s`, `cue_lead_s` | the silences and cue lead the timeline was laid out with. Informational: every time in the bundle already includes them |

### `blocks{id}`

A block is one thing on a board. Each carries its data and its rendered `html`.

| Field | Meaning |
|---|---|
| `id` | block id |
| `type` | `plain`, `error_row`, `answer_row`, `term_box`, `comparison`, `callout`, `category_card`, `timeline`, `table`, `clauses` (1.7), `contents_item`, `lesson_title` (docs/02-DESIGN-SYSTEM.md §7) |
| `text` | the text of `plain`, `error_row`, `answer_row`, `callout`, `category_card` (body), `contents_item` (the category; in a lesson with no contents slide, the section's title, and its `explanation` is null), `lesson_title` |
| `label` | a small label: `term_box` ("NEW WORD"; "WORD" marks a gloss of a hard general word, which the reference player draws on one line as "term (= explanation)", docs/02-DESIGN-SYSTEM.md §7b), `comparison`, `category_card` (header), `timeline`; on a `contents_item`, its number |
| `term`, `explanation` | `term_box`; `explanation` also carries a `contents_item`'s section list |
| `left`, `right` | `comparison` |
| `family` | tense family, `past`, `past_to_now`, `now`, `future`: `category_card`, `timeline`, `table` header |
| `col_families` | `table`: one family (or null) per header column |
| `kind` | `callout`: `warning` or `key_rule` |
| `icon` | `term_box`: a clinical icon name from the design system's list, or null |
| `header`, `rows` | `table`: header cells; rows of cells. A cell's text is its final text, typed parts included; " / " in a cell is a line break |
| `core` | 1.2. `table`: true when the table is a table board's whole table, taught row by row; otherwise null |
| `typed` | 1.2. `table`: the parts of cells typed live, `[{row, col, start, text}]`: row and column from 0, `start` the part's offset in the cell's text. Its index in this list is the part's number. Null when nothing is typed |
| `col_widths` | 1.2. core `table`: each column's share of the width, per cent |
| `font` | 1.2. core `table`: its text size, in hundredths of the frame's height |
| `role` | 1.3. What kind of content the block is: `slide` (the deck's own), `example` (added by the teacher) or `note` |
| `style` | 1.3. How the board draws it, when not the ordinary way: `pill` (a definition pill), `card` (a change card), `result` (the slide's result box) |
| `card` | 1.3. A change card's sides as shown: `{from, from_class, to, to_class, stacked, label}`; a class is `verb`, `noun`, `noun phrase`, `adjective`, `adverb`, `clause` or `phrase`, or null; `label` is shown only when no class replaces it |
| `pin` | 1.3. True for a working block that stays, once revealed, until its board ends |
| `fold_into` | 1.3. The block this one is part of: it is not drawn, and every cue on it is given to that block (§5, `cues`) |
| `flow` | 1.3. Its place in a change's flow on its board: `pill`, `source`, `card`, `result` or `note`; the board shows them in that order |
| `band` | 1.3. On the first change card of a run, the process pill's text ("Nominalisation") |
| `verdicts` | 1.6. A choice table (a core `table` whose rows offer versions of one sentence to choose between): each body cell's verdict, `[{row, col, verdict}]`, `verdict` `right`, `wrong` or `possible` (also acceptable, or correct only in some context). Null for any other table |
| `beside` | 1.2. a working block drawn beside a table row: `{block, row}`, the table and the row (from 0), or row null for a note about the whole table; otherwise null |
| `items` | `timeline`: its diagram parts in order (below). 1.7, `clauses`: its parts in order, `{kind, text, piece, part}`: `kind` `dependent` or `independent` (a piece, `text` its words), `glue` (the joining word; `piece` the piece it is in, from 1, or null for a bridge between two independent pieces), `subject` or `verb` (a label over `text` in `piece`), or `join`; the part id is `<block id>.<part>` |
| `tags` | tense tags: `[{text, family, label}]`; `label` is what the chip says ("up to now") |
| `exercise_item` | the item number an exercise sentence carries in its badge, or null |
| `provenance` | `source-derived`, `adapted`, `corrected`, `authored` or `maintainer` (AGENTS.md §9). For review; the student is not shown it |
| `html` | the block drawn by the pipeline, styled by `blocks.css` |

A diagram part (`items[]`): `kind` (`period`, `point`, `now`, `arrow`, `marker`,
`series`, `pointer`, `callout`), `part` (its number: the part id is
`<block id>.<part>`), `label`, `family`, and by kind `at` (0–100 along the axis),
`from` and `to`, `count` and `final` (a series), `side` (a callout, `above` or
`below`).

The website may show `html` as it is, or draw the block from its data. Either way
two things must hold, because cues and the reading pointer depend on them:

- **Word order.** A block's words appear in the order `html` has them: a term
  box's label, term, explanation; a comparison's label, left, right; a card's
  label, text; a table's header, then its rows; a diagram's label, its parts'
  labels in order, then each series legend. Badges, icons, chip labels and
  diagram glyphs are never text: they are drawn from attributes or CSS, so they
  are not counted as words.
- **Hooks.** The block's element carries `data-id="<block id>"`; each diagram part
  carries `data-part="<part id>"`. In a core table (1.2), each body row carries
  `data-row`, each cell `data-col`, and each typed part is an element
  `data-typed="<its index in typed>"` holding its final text. 1.6: a typed
  part inside printed words (a gap in a sentence) also carries the class `gap`.

### `boards[]`

| Field | Meaning |
|---|---|
| `id` | board id |
| `section` | the section it belongs to |
| `title` | the header text while this board is shown: the section title; on the introduction, empty for the title board and "What you will learn" for the contents board |
| `fixed` | block ids of the fixed layer, in order |
| `start` | the board appears |
| `end` | its last speech ends |
| `until` | the next board appears (or the lesson ends) |
| `exercise` | true when the board is one exercise item |
| `reveal` | `{part id: time}` for every part of every fixed-layer diagram |
| `table` | 1.2. On a table board, the id of its table; otherwise null |
| `pinned` | 1.3. `{block: time}`: the working blocks that stay, from their reveal to the board's `until` |
| `wordmarks` | 1.3. `[{block, text, cls, time}]`: from `time` to the board's `until`, `text` in `block` is marked `cls`, a word class (its colour, docs/02-DESIGN-SYSTEM.md §7c) or `slide-underline` (the slide's own underline). 1.4: with `row` and `col`, `text` is marked inside that table cell only |
| `palette` | 1.4 only. Not written from 1.5: every word class has one colour everywhere. A reader treats it as absent |
| `focus` | 1.2. On a table board, the spotlight in time order: `[{time, row, col}]`, from each `time` the row in focus and the cell highlighted (both from 0; `col` null for the row alone; `row` null for the whole table, nothing dimmed). Empty on other boards |
| `tight` | 1.8. How tightly the board is set so its fullest state fits (ADR 011): 0, 1 (half the gap between blocks) or 2 (and half the blocks' vertical padding), on the whole board |
| `verdicts` | 1.6. On a board whose table is a choice table, `[{row, col, verdict, time}]` in time order: from `time` to the board's `until`, the cell shows its verdict (rule 18). A wrong cell's time is its first strike, or the end of its row's last speech; a right cell's is its first circle, or when its row's last wrong cell fades; a possible cell's is the end of its row's last speech. Empty otherwise |
| `states` | the working-layer states in order |

### `states[]`

| Field | Meaning |
|---|---|
| `id` | state id |
| `working` | block ids of this state's working layer, in order |
| `start`, `end` | its first speech starts, its last speech ends |
| `until` | its working layer and marks disappear: the erase, or the board's `until` |
| `erase` | `{time, blocks}` when the state ends in an erase, otherwise null |
| `row` | 1.2. On a table board, the row this state teaches (from 0), or null for the whole table; null on other boards |
| `clears` | 1.8. `[{time, blocks}]` in time order: from `time`, the working `blocks` are cleared (not drawn) for the rest of the state, so the note revealed at `time` fits the board (ADR 011). Never a pinned block. Empty when nothing is cleared |
| `reveal` | `{id: time}` for every working block and every part of a working diagram |
| `utterances` | what is said in this state, in order |

### `utterances[]`

| Field | Meaning |
|---|---|
| `id` | utterance id |
| `text` | exactly what the voice says |
| `provenance` | as for blocks; for review |
| `audio_file` | the clip, relative to `bundle.json` (§8) |
| `start`, `end` | when it plays; `end - start` is the part of the clip played |
| `clip_in`, `clip_out` | 1.3. The part of the clip played, in seconds into the file: its silence before the first sound and after the last is left out. Null in a silent preview |
| `cues` | reveals, marks and pauses anchored in this utterance |
| `refs` | 1.1. The other lessons this utterance refers to, `[{lesson, section}]` (below); an empty list when it refers to none |
| `reading` | `[{block, words: [[k, start, end], …]}]`: the words of the board this utterance reads aloud, as word `k` of `block` (§5, rules) |

### `refs[]` (1.1)

A reference to another lesson of the product (docs/00-PRODUCT.md §6a): the
utterance names that lesson aloud ("You learned this in the lesson Verb
Tenses"), and the website may show it as a link.

| Field | Meaning |
|---|---|
| `lesson` | the target lesson's id (§4) |
| `section` | the target section's id in that lesson, or null when the reference is to the lesson as a whole, or the lesson is not yet built |

Both are ids, never titles: a retitled or reordered lesson still resolves. An id
the website does not know (a lesson not yet published) is shown as plain speech,
without a link. What each lesson and section is, and which references point at
it, is in the course index (docs/05-COURSE-INDEX.md), which is not published
with the bundle.

### `cues[]`

| Field | Meaning |
|---|---|
| `id` | cue id, within the utterance |
| `type` | `reveal`, `pause`, `type` (1.2), or a mark: `underline`, `highlight`, `circle`, `strike`, `bracket`, `point`, `arrow`, `replace` (docs/02-DESIGN-SYSTEM.md §8) |
| `time` | when it takes effect: a lead before its word, or for a pause the end of the utterance |
| `time_end` | the end of its word; for a pause, the end of the silence; for a `type`, the end of the typing |
| `retargeted_from` | 1.3. Not in the bundle: a cue on a folded block names the block it is folded into, with its phrase as that block writes it, and a cue on a change card names the phrase without its word class ("Analysis", not "Analysis (noun)") |
| `typed`, `row`, `col` | 1.2. A `type` cue: the typed part it types (its index in the table's `typed`), and that part's row and column. 1.6: a mark cue on a board's core table also carries `row` and `col`, the cell it is drawn in: the first cell of its state's row that holds its phrase, else the first cell of the table that does, unless the narration names the cell (its `overrides.json`); an arrow whose end is in the table carries `to_row` and `to_col` the same way |
| `block` | the block (or diagram part, for a reveal) it acts on; null for a pause |
| `text` | a mark's phrase inside `block`; a pause's description, for review |
| `to_block`, `to_text` | an arrow's end |
| `with` | a replace mark's correction |
| `seconds` | a pause's length |
| `word_index`, `anchor_word` | the spoken word the cue sits on; informational |

### `events[]`

`{type: "board", time, board}` when a board appears, and
`{type: "erase", time, state, blocks}` when a working layer is erased. They repeat
what the boards state, in one time-ordered list.

### Rules a renderer applies

These are the only rules. Every time and target they use is in the bundle.

1. **The clock.** While an utterance plays, the lesson time is its `start` plus
   the audio's position. Between utterances, a timer runs to the next `start`.
   Seeking to `t` plays the utterance containing `t` from `t - start`, or waits
   for the next one.
2. **The board** at `t` is the last board whose `start` ≤ `t`. Its fixed blocks
   are shown whole for the whole board, and the header shows its `title`.
3. **The state** at `t` is the last state whose `start` ≤ `t`, while `t` <
   its `until`. From `until` to the next state's `start` the working layer is empty.
4. **A working block** is shown while its state is current and `t` ≥
   `state.reveal[id]`.
5. **A diagram part** is shown while its block is shown and `t` ≥ its reveal time:
   `board.reveal` for a fixed diagram, whose parts stay through every erasure;
   `state.reveal` for a working one.
6. **A mark** is shown from its `time` until its state's `until`, on `text` as
   it occurs in its block's words (the narration audit and `check_marks.py`
   verify it is there); a mark with `row` and `col` (1.6) is drawn on `text`
   inside that table cell, and an arrow's end with `to_row` and `to_col` on
   `to_text` inside that cell. It
   may cross elements inside the block, such as a tense chip. An arrow joins `text` in `block` to `to_text` in
   `to_block`. A replace strikes `text` and writes `with` above it.
7. **A tense chip** sits under the first occurrence of each tag's `text` in each
   text field of its block, labelled `label`, in its family colour.
8. **The reading pointer** is on the latest `reading` word whose start ≤ `t`,
   until that word's end plus `meta.reading_hold_s`; otherwise on the latest
   `point` mark still shown; otherwise hidden. Word `k` of a block is its k-th
   whitespace-separated token that contains a letter or a digit, counted through
   the block's text in document order.
9. **A pause** is silence of `seconds` after its utterance, already included in
   the next `start`.
10. **A typed part** (1.2) of a core table is hidden before its `type` cue's
    `time`, typed in from `time` to `time_end` (the share of its characters
    shown grows evenly), and shown whole after. It keeps its final size while
    hidden, so the table never reflows. While typing it may be split in the
    renderer's DOM; for rule 8 it is still counted as one text. 1.6: a part
    with the class `gap` is drawn as a blank line of fixed width before its cue,
    and its answer is typed onto that line.
11. **The spotlight** (1.2) on a table board is the latest `focus` entry whose
    `time` ≤ `t`: rows other than `row` are dimmed and the cell (`row`, `col`)
    is highlighted; with `row` null nothing is dimmed.
12. **A side note** (1.2), a working block with `beside`, is shown by rule 4 and
    drawn next to its row, over the other rows, not in the flow of the board.
13. **Auto zoom** (1.2) is the renderer's: when a core table's text on screen
    is smaller than 14 px, the view zooms onto the highlighted cell (or the row)
    and its visible side notes; otherwise the view is not zoomed. Under
    `prefers-reduced-motion`, without animation.
14. **A pinned block** (1.3) is shown from its time in `pinned` until the board's
    `until`, through every erasure.
15. **Word marks** (1.3) are drawn under the cues' marks, from their `time` to
    the board's `until`.
16. **A folded block** (1.3) is not drawn; it is in no board's `fixed` and no
    cue names it.
17. **A trimmed clip** (1.3) plays from `clip_in`: lesson time is the utterance's
    `start` plus the audio's position minus `clip_in` (rule 1), and the utterance
    ends at `clip_out`.
18. **A verdict** (1.6) on a choice table's cell is shown from its `time` until
    the board's `until`, through every change of the spotlight: a `wrong` cell
    is faded, a `right` cell carries a tick on the green of "correct", a
    `possible` cell is left as it is (docs/02-DESIGN-SYSTEM.md §7, "Tables").
19. **Nothing moves a word** (2026-09-26; no data change): whatever a renderer
    draws for a moment, spotlight, marks, verdicts or typing, it never moves a
    word of the board. Marks are drawn over the words, never inline; active
    styling never changes a border width, padding or size; the frame's size
    does not depend on the page around it (docs/02-DESIGN-SYSTEM.md §8a).
20. **A clause diagram** (1.7) is a diagram: its parts are revealed by rule 5.
    A piece (`dependent`, `independent`) and a bridge are shown from their
    reveal; a `glue`, `subject` or `verb` part is a phrase already shown in its
    piece that takes its look from its reveal (the glue chip, the S or V label,
    the verb blue); from the `join`'s reveal the tab stands in the notch and a
    dependent piece that comes first shows its comma. None of it moves a word
    (rule 19; docs/02-DESIGN-SYSTEM.md §7d).
21. **A pinned block's room** (1.8): a pinned block takes room on its board from
    the start of the state in which it appears (its time in `pinned`), and none
    in earlier states; within its state it is there, unseen, until its time.
22. **A clear** (1.8): from a clear's `time` to its state's `until`, its
    `blocks` are not drawn and take no room; the blocks after them close up (none
    of them was shown before the clear, and every fixed or pinned block holds its
    place, rule 19).
23. **A tight board** (1.8): with `tight` 1 the vertical gap between the board's
    blocks is halved; with 2 the blocks' own vertical padding is halved too; on
    the whole board, from its start. With rules 19 to 22, every block shown lies
    inside the board (docs/02-DESIGN-SYSTEM.md §8b).

How things move is the renderer's, within docs/02-DESIGN-SYSTEM.md: how a
diagram part is drawn in motion (§7a), mark styles (§8), the frame's layout, and
reduced motion. A seek shows the correct state at once, with no replay.

---

## 6. `text.json`

The lesson as clean text, for search, the AI chat and accessibility. It carries
no cues and no provenance.

| Field | Meaning |
|---|---|
| `format`, `format_version` | `"oetbook-lesson-text"`, `"1.8"` |
| `lesson` | the same object as `bundle.json`'s `lesson` |
| `sections[]` | `{id, title, category, start, end, narration_text, board_text, boards}` |
| `sections[].narration_text` | everything said in the section, one paragraph per board |
| `sections[].board_text` | every block's words, one block per paragraph |
| `sections[].boards[]` | `{id, start, board_text: [{block, text}], narration: [{id, start, text, refs}]}`; `refs` (1.1) as in `bundle.json` |

- **Narration as spoken:** exactly the text the voice says, so numbers are
  words ("two thousand and ten") where the board shows digits ("2010").
- **Board text:** the words of every block the board shows. The fixed layer comes
  first, then each state's working blocks in order, each block once. A table
  gives one row per line, cells separated by ` | `, and a line break inside a
  cell as `; `. Chip labels and badges are
  not words and are not included; they are in `bundle.json`.
- The text repeats wherever the lesson repeats it: an exercise sentence appears on
  the introduction board and again on its own board.
- Ids and `start` times are those of `bundle.json`, so a search hit or a chat
  answer can link to the moment it came from.

---

## 7. `blocks.css`

The stylesheet the blocks' `html` is written against: block types, colours,
family colours, diagrams and tense chips, all sized in container units of the
16:9 frame (docs/02-DESIGN-SYSTEM.md §4). It also holds the reference frame's
own layout (`.frame`, `.hdr`, `.body`); the website keeps the block rules and may
replace those. It is identical for every lesson built at one format version, so
the website can serve one shared copy.

The styles for marks, the pointer and diagram motion are the renderer's, not
the bundle's (docs/02-DESIGN-SYSTEM.md §7a, §8). The reference renderer's are in
`board_player_template.html`.

---

## 8. Audio

Each utterance names one clip in `audio_file`, relative to `bundle.json`: a WAV,
mono, 44.1 kHz, 16-bit, in its section's folder, named by a hash of its text,
voice settings and pronunciations, so a changed text always gets a new file
(methodology §19–20). Grammar 1's audio is about 540 MB.

The bundle's times are the clips' own. A published copy may be re-encoded
as long as each clip keeps its length.

**Audio for the web — `OPEN`, recorded by the maintainer 2026-09-24.** The WAV
clips are the masters: they stay local, with the lesson, and are never
published as they are. A compressed format for the website is chosen when the
site is built, together with where the clips are hosted and whether a published
bundle rewrites `audio_file` or maps it. Until then no lesson is re-encoded, and
choosing the format later needs no rebuild of any bundle.

---

## 9. Deliberately not in the bundle

- **The student's state:** progress, resume position, chat history. The
  website's, keyed by the ids in §4.
- **The pipeline's records:** understanding, rulings, QA findings, audits,
  provenance notes, model responses. They stay in `<lesson>/analysis/` and are
  never published.
- **Branding, the brand and the domain:** not decided (docs/00-PRODUCT.md §7), and
  never inside the lesson frame.
- **Exercises:** a later product (docs/00-PRODUCT.md §8). A later minor version
  can add them beside the boards without changing anything here.

---

## 10. Open

| # | Question | Status |
|---|---|---|
| 1 | Audio for the web: the compressed format, where clips are hosted, and whether a published bundle rewrites `audio_file` or maps it | open: WAV masters stay local; decided when the site is built (§8) |
| 2 | Whether the lesson folder's name is the lesson's public id | not decided; it is stable |
