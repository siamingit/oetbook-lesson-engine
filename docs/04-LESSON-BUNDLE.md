# Lesson Bundle — the contract between pipeline and website

What the pipeline hands to the website for each lesson, file by file and field
by field. Written 2026-09-24, before the website exists, so that the lessons
built now never need rebuilding for it.

**Format version 1.0. Status: Accepted** by the maintainer, 2026-09-24
(docs/adr/004-lesson-bundle-contract.md). A change to it is a new format version
(§3), recorded in a new ADR.

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
| `format_version` | string | `"1.0"` |
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
| `type` | `plain`, `error_row`, `answer_row`, `term_box`, `comparison`, `callout`, `category_card`, `timeline`, `table`, `contents_item`, `lesson_title` (docs/02-DESIGN-SYSTEM.md §7) |
| `text` | the text of `plain`, `error_row`, `answer_row`, `callout`, `category_card` (body), `contents_item` (the category; in a lesson with no contents slide, the section's title, and its `explanation` is null), `lesson_title` |
| `label` | a small label: `term_box` ("NEW WORD"), `comparison`, `category_card` (header), `timeline`; on a `contents_item`, its number |
| `term`, `explanation` | `term_box`; `explanation` also carries a `contents_item`'s section list |
| `left`, `right` | `comparison` |
| `family` | tense family, `past`, `past_to_now`, `now`, `future`: `category_card`, `timeline`, `table` header |
| `col_families` | `table`: one family (or null) per header column |
| `kind` | `callout`: `warning` or `key_rule` |
| `icon` | `term_box`: a clinical icon name from the design system's list, or null |
| `header`, `rows` | `table`: header cells; rows of cells |
| `items` | `timeline`: its diagram parts in order (below) |
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
  carries `data-part="<part id>"`.

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
| `states` | the working-layer states in order |

### `states[]`

| Field | Meaning |
|---|---|
| `id` | state id |
| `working` | block ids of this state's working layer, in order |
| `start`, `end` | its first speech starts, its last speech ends |
| `until` | its working layer and marks disappear: the erase, or the board's `until` |
| `erase` | `{time, blocks}` when the state ends in an erase, otherwise null |
| `reveal` | `{id: time}` for every working block and every part of a working diagram |
| `utterances` | what is said in this state, in order |

### `utterances[]`

| Field | Meaning |
|---|---|
| `id` | utterance id |
| `text` | exactly what the voice says |
| `provenance` | as for blocks; for review |
| `audio_file` | the clip, relative to `bundle.json` (§8) |
| `start`, `end` | when it plays; `end - start` is the clip's length |
| `cues` | reveals, marks and pauses anchored in this utterance |
| `reading` | `[{block, words: [[k, start, end], …]}]`: the words of the board this utterance reads aloud, as word `k` of `block` (§5, rules) |

### `cues[]`

| Field | Meaning |
|---|---|
| `id` | cue id, within the utterance |
| `type` | `reveal`, `pause`, or a mark: `underline`, `highlight`, `circle`, `strike`, `bracket`, `point`, `arrow`, `replace` (docs/02-DESIGN-SYSTEM.md §8) |
| `time` | when it takes effect: a lead before its word, or for a pause the end of the utterance |
| `time_end` | the end of its word; for a pause, the end of the silence |
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
   verify it is there). It
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

How things move is the renderer's, within docs/02-DESIGN-SYSTEM.md: how a
diagram part is drawn in motion (§7a), mark styles (§8), the frame's layout, and
reduced motion. A seek shows the correct state at once, with no replay.

---

## 6. `text.json`

The lesson as clean text, for search, the AI chat and accessibility. It carries
no cues and no provenance.

| Field | Meaning |
|---|---|
| `format`, `format_version` | `"oetbook-lesson-text"`, `"1.0"` |
| `lesson` | the same object as `bundle.json`'s `lesson` |
| `sections[]` | `{id, title, category, start, end, narration_text, board_text, boards}` |
| `sections[].narration_text` | everything said in the section, one paragraph per board |
| `sections[].board_text` | every block's words, one block per paragraph |
| `sections[].boards[]` | `{id, start, board_text: [{block, text}], narration: [{id, start, text}]}` |

- **Narration as spoken:** exactly the text the voice says, so numbers are
  words ("two thousand and ten") where the board shows digits ("2010").
- **Board text:** the words of every block the board shows. The fixed layer comes
  first, then each state's working blocks in order, each block once. A table
  gives one row per line, cells separated by ` | `. Chip labels and badges are
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
