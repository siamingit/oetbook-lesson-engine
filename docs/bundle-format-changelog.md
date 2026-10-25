# Lesson bundle format changelog: 1.12 to 1.21

For the oetacademy-web team, before the site accepts bundle formats 1.13 to 1.20.
Written 2026-10-22; format 1.21 added 2026-10-23 (§9a). It is complete on its own: it does not assume access to the
engine's repository. The 1.12 contract the site already implements is the
engine's "Player rendering rules: bundle format 1.12" (rules 1 to 28, sent
2026-10-01) and "Lesson bundle 1.12: what changed since 1.11"; this page lists
everything after them.

## Summary

Formats 1.13 to 1.20 add the Reading and Listening lessons. Every change is
additive at the JSON level: no field is removed or renamed, and no field changes
type, except that three fields that were always set may now be null: a
question's answer part has `text` null (1.15), a recording's utterance has
`text` null (1.18) and a `play` cue has `block` null (1.18). A lesson's `format_version` names the newest
features the engine may write for that kind of lesson, so it says which rules a
player needs: Grammar and Vocabulary lessons stay 1.12; Reading lessons are 1.13
to 1.17 by part; every Listening lesson is 1.20. Formats 1.15, 1.18 and 1.19
were never the format of an approved lesson, but most of what they added is in
the 1.16 and 1.20 lessons, so the site needs all of them. Nearly everything new
is required: a player that ignores it plays a broken or wrong lesson
(classification below). Two lessons carry a newer format label but use none of
its features: Reading 1 (1.13) and Listening 1 (1.20) differ from a 1.12 bundle
only by extra fields that are always null, plus their own `blocks.css`. Three
kinds of file are new beside the lesson player: the exam recordings (MP3, 1.18),
the word bank's pronunciation clips (MP3, 1.15) and per-lesson stylesheets
(`blocks.css` is no longer one shared copy per format).

Format 1.21 (2026-10-23, §9a) adds one optional board field, `fit` (a board shown
whole, never zoomed: Grammar 6's one exception, until then known only to the reference
player), and ends the stray data of §12: the five lessons that had either were
rebuilt at 1.21 with nothing visible changed. Unlike 1.13 to 1.20, a lesson is 1.21
only where it uses the field or was rebuilt by the clean-up; every other lesson keeps
its version.

**Releases.** From 1.21 on, each format version is released as a git tag of the
engine's repository, `bundle-format-v<version>` (`bundle-format-v1.21`), on the commit
that merges it. Formats 1.0 to 1.20 have no tag.

| Version | Date | Main change | Required or optional | Approved lessons using it |
|---|---|---|---|---|
| 1.13 | 2026-10-05 | Reading: a practice-set text drawn as a document (`doc`), a practice-set question (`question`), keyword-pair marks `match1` to `match3`, a side note pinned under the table | **Required** (the data fields alone are optional; the marks, the pinned note and the stylesheet are required) | Features: R2–R5, L2–L5. Label only, no feature used: R1 |
| 1.14 | 2026-10-06 | The map of four texts on one board, with a zoom inside it (`map`; a state's `doc`, `zoom`) | **Required** | R2 |
| 1.15 | 2026-10-06 | Part B: a question with options struck out and ticked, the covered text (`veil`), word-bank glosses with a synonym and a pronunciation button, word tables. Also the "lens" (1.15 only) | **Required**, except the lens (never in an approved bundle) | No lesson is 1.15. Features: R3–R5, L2–L5 (`veil`: R3 only) |
| 1.16 | 2026-10-08 | The Part B question board in two columns, the extract whole (`split`, `overlay`), replacing the lens | **Required** | R3, R4, R5 |
| 1.17 | 2026-10-08 | Part C: the text as a map or a paragraph (`view`), options shown later, the attitude `scale`, opinion-signal marks, bold in released texts | **Required** (bold, `target`, `recap_grouped`: optional) | R4, R5 (`recap_grouped` also L4, L5) |
| 1.18 | 2026-10-13 | Listening: the exam recordings played in the lesson's clock (`kind: "exam"`, cue `play`), transcripts and note forms, a "hear it in the recording" button | **Required** | No lesson is 1.18. Features: L2–L5 |
| 1.19 | 2026-10-13 | The Listening board (`listen`): a transcript box that follows the recording by word times; the question column follows the recording | **Required** | No lesson is 1.19. Features: L2–L5 |
| 1.20 | 2026-10-14 | The vocabulary panel under the transcript, the whole note form during the reading time, no hyphenation | **Required** | L2–L5. Label only, no feature used: L1 |
| 1.21 | 2026-10-23 | A board shown whole, never zoomed (`fit`); the clean-up of §12's data | **Required** (`fit`, rule 52) | G6 (`fit`). Rebuilt by the clean-up, no new feature used: R5, L2, L4, L5 |

## 1. How to read this page

### The approved lessons

| Short | Lesson id | `format_version` | Final approval |
|---|---|---|---|
| G1–G8 | `grammar-01-verb-tenses` … `grammar-08-paraphrasing` | 1.12; G6 1.21 from 2026-10-23 (§9a) | 2026-09-27 to 2026-10-01 |
| V1–V3 | `vocabulary-01-word-forms`, `vocabulary-02-collocations`, `vocabulary-03-collocations-2` | 1.12 | 2026-10-01 |
| R1 | `reading-01-overview` | 1.13 | 2026-10-06 |
| R2 | `reading-02-part-a` | 1.14 | 2026-10-06 |
| R3 | `reading-03-part-b` | 1.16 | 2026-10-07 (built at 1.15; rebuilt at 1.16 on 2026-10-08 and the approval confirmed that day) |
| R4 | `reading-04-part-c` | 1.17 | 2026-10-11 |
| R5 | `reading-05-part-c-2` | 1.21 (1.17 until 2026-10-23, §9a) | 2026-10-11 |
| L1 | `listening-01-overview` | 1.20 | 2026-10-17 |
| L2 | `listening-02-part-a` | 1.21 (1.20 until 2026-10-23, §9a) | 2026-10-14 |
| L3 | `listening-03-part-b` | 1.20 | 2026-10-16 |
| L4 | `listening-04-part-c` | 1.21 (1.20 until 2026-10-23, §9a) | 2026-10-17 |
| L5 | `listening-05-part-c-2` | 1.21 (1.20 until 2026-10-23, §9a) | 2026-10-21 |

### Required and optional

- **Required**: a player that ignores it plays the lesson wrongly or broken:
  something is missing, unreadable, cut off, in the wrong place, or a control
  does nothing.
- **Optional**: the lesson plays correctly if the player ignores it. Most
  optional items are data that the block's `html` already draws, or
  identifiers kept for traceability.
- "Data optional" with "look required" means: the field itself need not be
  read, because the block's `html` and the lesson's `blocks.css` draw it, but a
  player must use that `html` and that `blocks.css`.

### Where this was taken from

Every statement here was checked against: the bundle builder and the reference
player in the engine's code, their git history (`git log -p`), the engine's
ADRs 026 and 029 to 037, the engine's bundle contract, and the 21 approved
bundles under `C:\OET\lessons\<lesson>\generated\lesson-player\`. A script
(`spike/scripts/bundle_fields.py`) walks every approved bundle and fails if any
field path, JSON type or enumerated value not in the 1.12 bundles is missing
from the index at the end of this page (§13). Its result is in §12.

### Paths

`blocks.*` is any block of the `blocks` map. `boards[]` is any board,
`boards[].states[]` any state, `…utterances[]` any utterance, `…cues[]` any
cue. The JSON examples use invented placeholder content and ids.

## 2. Changes that apply from 1.13 on, whatever the version

- **`format_version`** is the same string in `bundle.json` and `text.json`
  (`"1.13"` … `"1.20"`). The engine's contract still says text.json is
  `"1.12"`; that is out of date.
- **`blocks.css` is per lesson, not per format.** From 1.13 a lesson's
  stylesheet is the 1.12 stylesheet, unchanged, followed by the sections its
  features need: Reading (1.13), map (1.14), Part B (1.15/1.16), Part C (1.17),
  Listening (1.18 to 1.20). The 21 approved lessons have eight different
  stylesheets; the five 1.20 lessons have four. Always use the package's own
  `blocks.css`; a shared copy per format is wrong. (The engine's contract still
  says the stylesheet is identical for every lesson at one format; that is out
  of date.)
- **Some rules need player CSS that is not in `blocks.css`.** The layouts of
  the map board, the two-column question board and the Listening board, the
  transcript box, the vocabulary panel and the "recording" label are drawn by
  the reference player's own styles. Their measures are given in the rules
  below.
- **New files beside the lesson player** (all relative to `bundle.json`, like
  `../images/`): `../exam-audio/<extract id>.<12 hex>.mp3`, the exercises
  release's own recording, byte for byte (1.18); `../vocab-audio/<word>.mp3`,
  the word bank's pronunciation clip (1.15). Both are named in the data and in
  the block `html` (`data-audio`, below). See §11 for audio.
- **New fields are written on every block of a lesson that may use them**,
  `null` where they do not apply: every block of a Reading or Listening lesson
  has `doc` and `question`; of a lesson with a map (R2), `map`; of a Part B or C
  lesson (R3–R5, L3–L5), `synonym`, `audio`, `lexicon` and `vocab_table`; of a
  Listening lesson (L1–L5), `synonym`, `heard` and `panel`. A player must accept
  the extra null fields. Board and state fields (`split`,
  `listen`, `veil`, `view`, `overlay`, `doc`, `zoom`) are absent where they do
  not apply.
- **The guard on every board** (rule 41) is a player rule from 2026-10-11 with
  no data; it applies to 1.12 lessons too (§10).

## 3. Format 1.13 — Reading: practice-set texts, questions, keyword pairs

2026-10-05 (engine ADR 026). The format of R1. Its features are used by R2–R5 and
L2–L5 (those lessons are at later versions, which include 1.13).

### Added

**`blocks.*.doc`**, on a core `table` block that is a practice-set text (a
"document"): `{stimulus, label, title, text_type, parts}`.

- `stimulus`: the text's id in the exercises release. `label` ("Text A") and
  `title`: as released.
- `text_type`: `table`, `guideline`, `protocol`, `notes`, `email`, `memo`,
  `policy`, `extract`; 1.15 adds `procedure`, `manual`, `notice`; 1.17 adds
  `article`; 1.18 adds `transcript`, `form`.
- `parts`: one entry per row of the table, `{kind, mark}`. `kind`: `heading`,
  `para`, `bullet`, `num`, `thead`, `trow`. `mark`: a `num` row's number as a
  string ("1"), else null. A `thead` or `trow` row is a row of a small table
  inside the text; its cells are joined by `" | "` in the row's text.
- The block is an ordinary core table (1.2): one column, `header` one cell (the
  label), each row's text the released line.

```json
"page-5_k10": {
  "id": "page-5_k10", "type": "table", "role": "slide", "core": true,
  "header": ["Text A"], "rows": [["Placeholder heading"], ["First placeholder step."], ["Second placeholder step."]],
  "col_widths": [100], "font": 2.4, "typed": null, "beside": null,
  "doc": {"stimulus": "oa-reading-990001", "label": "Text A", "title": "Placeholder title",
          "text_type": "guideline",
          "parts": [{"kind": "heading", "mark": null}, {"kind": "num", "mark": "1"}, {"kind": "num", "mark": "2"}]},
  "question": null,
  "html": "<div class=\"blk role-slide tbl core doc doc-guideline\" data-id=\"page-5_k10\" …><table>…<th data-kind=\"Guideline\">Text A</th>…<tr data-row=\"1\" class=\"dp dp-num\"><td data-col=\"0\" data-mark=\"1\">First placeholder step.</td></tr>…</table></div>"
}
```

**`blocks.*.question`**, on a `plain` block that is a practice-set question:
`{item, kind, max_words}`. `item`: the question's id in the exercises release.
`kind`: `matching`, `short-answer`, `sentence-completion` (1.15 adds `choice`).
`max_words`: the word limit, or null. The block's `text` is the question as
released. Its `exercise_item` is its number in the lesson, counted from 1 in
the order taught (from 2026-10-08; no new field). On a table board the question
is usually a side note (`beside`, row null) that is pinned (`pin` true, and in
the board's `pinned`).

```json
"page-6_k14": {
  "id": "page-6_k14", "type": "plain", "role": "slide", "text": "Which text says placeholder?",
  "exercise_item": 1, "pin": true, "beside": {"block": "page-6_k10", "row": null},
  "doc": null,
  "question": {"item": "oa-reading-990014", "kind": "matching", "max_words": null},
  "html": "<div class=\"blk role-slide q\" data-id=\"page-6_k14\" data-item=\"oa-reading-990014\"><span class=\"qn\" data-n=\"1\"></span><span class=\"qt\">Which text says placeholder?</span></div>"
}
```

**Cue types `match1`, `match2`, `match3`** (rule 30): a keyword pair. Same
fields as a `highlight` mark (`block`, `text`, and `row`/`col` on a table).

```json
{"id": "c3", "type": "match1", "block": "page-6_k14", "text": "placeholder", "row": null, "col": null,
 "time": 812.40, "time_end": 812.95, "word_index": 4, "anchor_word": "placeholder"}
```

**A pinned side note** (no new field): from 1.13 a working block can be both
pinned (in the board's `pinned`) and a side note (`beside`). No 1.12 bundle
has one.

### Rules (player behaviour)

- **Rule 29, a practice-set text.** A core table with `doc` is a table board
  (rules 10 to 13) drawn as a page. The header shows the text type as a tag
  (`blocks.css`: `th::before { content: attr(data-kind) }`, never a word of the
  block). A `heading` row is set as a heading; a `bullet` row gets a bullet and
  a `num` row its number (`content: attr(data-mark) "."`), both from the
  stylesheet, so they are not words for the reading pointer (rule 8). A
  `thead` or `trow` row is drawn as a grid whose cells are the parts of the
  row's text between `" | "`; the separators stay in the text, hidden (`.dsep`).
- **Rule 30, a keyword pair.** `match1`, `match2`, `match3` are drawn like a
  highlight (over the words, never moving them), in sky blue `#0688F9`, violet
  `#A860FB` or yellow `#F9E806` at 55% opacity (reference player:
  `rgba(…, .55)`, `mix-blend-mode: multiply`). Marks of one type on one board
  are one pair: a question's words and the text's words that match them. The
  colour means only "these words correspond".
- **A pinned side note** stays under the table, first, before the current
  state's side notes, from its time in `pinned` to the board's end, through
  every erase and between states. It keeps one width for the whole board: the
  table's width minus the board's picture's declared size (`size`, else 20%
  of the frame's height) and the gap, so its words never move when the picture
  goes.
- **The question block** draws its number in a round badge from `data-n`
  (stylesheet), not a word.

### Required or optional

| Feature | Class | Why | Lessons |
|---|---|---|---|
| `format_version` "1.13" in both files | Required | to accept the bundle | R1 |
| `doc` data | Optional (data) | the `html` draws the document | R2–R5, L2–L5 |
| Document look (rule 29) from the `html` and the lesson's `blocks.css` | **Required** | without it a numbered list has no numbers, a table inside a text has no grid, and the text type is not shown | R2–R5, L2–L5 |
| `question` data | Optional (data) | identifies the release item; the `html` draws the question | R2–R5, L3–L5 |
| Question badge (stylesheet) | **Required** | the question's number exists only in `data-n` | R2–R5, L3–L5 |
| Cues `match1`–`match3` (rule 30) | **Required** | the pairs are what the narration teaches on every question board; an unknown cue type also fails the site's 1.12 schema | `match1`: R2–R5, L3–L5; `match2`: R2–R5, L4, L5; `match3`: R2, R3 |
| Pinned side note | **Required** | a 1.12 player places only the current state's side notes, so the pinned question would vanish after its first state | R2–R5, L3–L5 |

R1 uses none of these: its blocks have `doc` and `question` null, and its
cues are 1.12 types. It plays correctly in a 1.12 player that accepts the
format string and the null fields, with its own `blocks.css`.

## 4. Format 1.14 — the map of the texts

2026-10-06 (ADR 026, the Part A question method). Used by R2 only.

### Added

**`blocks.*.map`**, on a core `table` that shows the four Part A texts at once:
`{docs: [{stimulus, label, title, text_type, parts, header, first, count}]}`,
one entry per text in order. Each entry is the text as `doc` gives it, its
header line (`header`, a string), and the table rows it holds (`first`, from 0,
and `count`). The table's `rows` are every text's rows in that order; its
`header` is one label for the whole.

**`boards[].states[].doc`** (on a map board only): the text in view, its index
in `map.docs`, or null for all four. **`boards[].states[].zoom`**: null,
`"doc"` or `"row"`. Both are absent on other boards.

```json
"map": {"docs": [
  {"stimulus": "oa-reading-990001", "label": "Text A", "title": "Placeholder", "text_type": "table",
   "parts": [{"kind": "thead", "mark": null}, {"kind": "trow", "mark": null}], "header": "Text A Placeholder", "first": 0, "count": 2},
  {"stimulus": "oa-reading-990002", "label": "Text B", "title": "Placeholder", "text_type": "notes",
   "parts": [{"kind": "heading", "mark": null}, {"kind": "bullet", "mark": null}], "header": "Text B Placeholder", "first": 2, "count": 2}
]}
```

```json
"states": [
  {"id": "page-9_t1.s1", "doc": null, "zoom": null, "row": null, "…": "…"},
  {"id": "page-9_t1.s2", "doc": 1, "zoom": null, "row": null},
  {"id": "page-9_t1.s3", "doc": 1, "zoom": "doc", "row": null},
  {"id": "page-9_t1.s4", "doc": 1, "zoom": "row", "row": 3}
]
```

### Rule 31, a map of the texts

- **Layout.** A map board is two columns: the map on the left (reference
  player: a grid, the map 58% of the board's width, column gap 2% of the frame's
  width), and every other block of the board (the question, notes, glosses,
  picture) in a column beside it, never under or over it. The map block is a
  fixed-height frame (77% of the frame's height) holding the four texts as
  small pages in a 2×2 grid; each page is scaled to the largest size at which
  it fits its quarter whole. The map is not readable at that size, on purpose;
  the table text floor does not apply to it.
- **States.** `doc` set: that text is bright, the others dimmed (reference:
  opacity 0.18). `zoom: "doc"`: that text alone, at a document's size (2.4% of
  the frame's height). `zoom: "row"`: that text alone, with the state's `row`
  set larger (1.75 times) and brought to the middle of the map's frame, the
  other rows dimmed (the spotlight, rule 11).
- **Whole lines only** (2026-10-07): a zoomed map never shows part of a line.
  The window's edges lie between two lines; where more text lies above or
  below, about half a line of it shows under a soft fade, as a cue.
- **Marks and the pointer** inside the map are drawn only where the map's
  frame shows them.
- **The camera does not move** on a map board (rule 13 does not apply); the
  map moves inside its own frame, smoothly (0.6 s), or at once after a seek or
  under reduced motion. The map's words move by design (rule 19 does not apply
  to them).

### Required or optional

| Feature | Class | Why | Lessons |
|---|---|---|---|
| `map`, the map board layout | **Required** | without it the four texts are drawn as one long table that does not fit the board | R2 |
| A state's `doc` and `zoom` | **Required** | the zoom is the only place the text is readable; the narration reads it there | R2 |
| `blocks.css` map section | **Required** | the map's frame and grid | R2 |

## 5. Format 1.15 — Part B questions, the covered text, the word bank

2026-10-06 (ADR 026, the Part B question method and the vocabulary layer). R3
was approved at 1.15 on 2026-10-07, then rebuilt at 1.16 the next day (the
lens replaced by two columns) and re-approved; so no approved bundle is 1.15.
Everything below except the lens is in the 1.16 and later lessons.

### Added

**`question.options`**, on a Part B (or C, or Listening B and C) question:
`[{letter, option, text}]`; `letter` "A" to "D", `option` the option's id in
the release, `text` as released. Such a question has `kind: "choice"`.

**The question's parts** (`items`, revealed by rule 5): `{kind, text, option, part}`.
`kind: "out"`: option `option` (a letter) is ruled out, `text` its short
reason label. `kind: "key"`: option `option` is the answer, `text` null. The
question is pinned, and the reveal times of its parts are in the **board's**
`reveal` (in 1.12 that map held only parts of fixed diagrams).

```json
"question": {"item": "oa-reading-990031", "kind": "choice", "max_words": null,
  "options": [{"letter": "A", "option": "oa-reading-990031-o1", "text": "Placeholder option one."},
              {"letter": "B", "option": "oa-reading-990031-o2", "text": "Placeholder option two."},
              {"letter": "C", "option": "oa-reading-990031-o3", "text": "Placeholder option three."}]},
"items": [{"kind": "out", "option": "A", "text": "placeholder reason", "part": 1},
          {"kind": "out", "option": "C", "text": "placeholder reason", "part": 2},
          {"kind": "key", "option": "B", "text": null, "part": 3}]
```

and on the board: `"reveal": {"page-8_k11.1": 1702.35, "page-8_k11.2": 1730.10, "page-8_k11.3": 1744.80}`.

**`boards[].states[].veil`** (a Part B question board): true while the text
(the board's `table`) is covered, false once it appears. Absent on other boards.

**Word-bank glosses** (a `gloss` block, 1.10, from the exercises repository's
word bank):

- `synonym`: one synonym, also a gloss part of `kind: "synonym"` shown under
  the meaning;
- `audio`: `{file, seconds}`, the word bank's pronunciation clip (an MP3),
  relative to the bundle's folder (`../vocab-audio/<word>.mp3`), played only
  when the learner taps the gloss's button;
- `lexicon`: the word's `lx:` id in the word bank (provisional ids).

```json
"page-8_k03": {
  "id": "page-8_k03", "type": "gloss", "role": "note", "term": "placeholder", "explanation": "a made-up meaning",
  "items": [{"kind": "meaning", "text": "a made-up meaning", "part": 1},
            {"kind": "picture", "text": null, "part": 2},
            {"kind": "synonym", "text": "stand-in", "part": 3},
            {"kind": "example", "text": "A placeholder sentence.", "part": 4}],
  "synonym": "stand-in", "lexicon": "lx:placeholder",
  "audio": {"file": "../vocab-audio/placeholder.mp3", "seconds": 1.2},
  "html": "<div class=\"blk role-note gl glv\" data-id=\"page-8_k03\">…<button type=\"button\" class=\"gl-say\" data-audio=\"../vocab-audio/placeholder.mp3\" aria-label=\"Hear placeholder\"></button>…<div class=\"pt gl-s\" data-part=\"page-8_k03.3\">stand-in</div>…</div>"
}
```

**`blocks.*.vocab_table`**, on a core table built from the word bank:
`{kind, lexicon}`, `kind` `match` (words and meanings in another order, to
match) or `recap`; `lexicon` the `lx:` ids of its rows in order. It is an
ordinary table.

**Document types** `procedure`, `manual`, `notice` (each has its own look in
`blocks.css`, as do `email` and `policy`).

**Removed in 1.16, never in an approved bundle:** a board's `lens` and
`lens_from`, and rule 35 (the text read through a window that followed the
reading). A player need not support them.

### Rules

- **Rule 32, a Part B question.** A `plain` block whose `question` has
  `options` shows its wording, then each option with its letter in a small
  circle (a stylesheet attribute `data-l`, never a word) and, under each
  option, room for a reason label, kept from the start so nothing moves. An
  `out` part strikes its option through in red on pale red and shows its reason
  label after a cross; a `key` part ticks its option on pale green. The block is
  pinned; its parts are timed by the board's `reveal` and stay to the board's
  end. (The looks are in `blocks.css`, keyed on the part's `on` class: the
  player only has to switch the parts on.)
- **Rule 33, a covered text.** While the current state's `veil` is true, the
  board's table is drawn covered: its words hidden, its type tag shown, its
  size kept (`blocks.css`: class `veiled` on the table block, set by the
  player). No mark, point or reading is on it in such a state.
- **Rule 34, a pronunciation clip.** A gloss with `audio` shows a round button
  with no words (in its `html`, `<button class="gl-say" data-audio="…">`).
  Tapping it plays the clip. The lesson's own clock never plays it. The
  reference player pauses the lesson while the clip plays, then resumes; one
  clip at a time.

### Required or optional

| Feature | Class | Why | Lessons |
|---|---|---|---|
| `question.options`, `kind: "choice"`, parts `out` and `key` (rule 32) | **Required** | without them the answer is never shown: no option is struck or ticked | R3–R5, L3–L5 |
| A pinned block's parts timed by the board's `reveal` | **Required** | the parts are not in any state's `reveal` | R3–R5, L3–L5 |
| `veil` (rule 33) | **Required** | the question is taught with the text covered on purpose ("try it first"); shown early, the text gives the evidence away | R3 |
| Gloss `audio` and its button (rule 34) | **Required** | the button is in the `html`; ignored, it is a control that does nothing. The clips must be shipped (§11) | R3–R5, L3–L5 |
| Gloss `synonym` and part `synonym` | Optional (data); look required | drawn by the `html` and `blocks.css` as a gloss part (rule 5) | R3–R5, L2–L5 |
| `lexicon`, `vocab_table` | Optional | identifiers; the tables are ordinary tables | R3–R5, L3–L5 |
| Document types `procedure`, `manual`, `notice` (and `email`, `policy`) looks | Optional | the page and its type tag (1.13) are what matter; the genre looks are decoration in `blocks.css` | R3 |
| `lens`, `lens_from`, rule 35 | Not needed | in no approved bundle | none |

## 6. Format 1.16 — the Part B question board in two columns

2026-10-08 (ADR 026 amendment of that date). The format of R3; R4 and R5 use it
too.

### Added and changed

- **`boards[].split`** (a number, per cent): on a question board, the share of
  the board's width of the column that holds the board's table (the
  practice-set text), drawn whole. Absent on other boards.
- **`boards[].states[].overlay`** (a list of block ids, often empty): the
  glosses of this state drawn over the foot of the question column because
  they do not fit in it. Absent on other boards.
- **Changed meaning, no new field:** a gloss in `overlay` goes as a `clears`
  entry (1.8), at the moment before anything of the question under it is read
  or marked. The board's `focus` (1.2) has row null until the whole extract has
  been shown once uncovered.
- **Removed:** `lens`, `lens_from` (1.15 only).

```json
{"id": "page-8_t2", "table": "page-8_k10", "split": 54,
 "pinned": {"page-8_k11": 1690.20},
 "focus": [{"time": 1690.20, "row": null, "col": null}, {"time": 1712.80, "row": 0, "col": null}],
 "states": [
   {"id": "page-8_t2.s1", "veil": true, "overlay": [], "clears": [], "…": "…"},
   {"id": "page-8_t2.s4", "veil": false, "overlay": ["page-8_k15"],
    "clears": [{"time": 1760.05, "blocks": ["page-8_k15"]}]}
 ]}
```

### Rule 36, a question board in two columns

- **Layout.** The board's table (the text) is drawn whole as a page, at the
  table's `font`, in a column `split` per cent of the board's width, from the
  board's top. Every other block (the question, its options and labels, notes,
  glosses, the picture) is drawn in a column beside it, in the board's order
  (reference: the question column is padded `split` + 2% of the frame's width
  from the left). Nothing scrolls, zooms or hides any line of the text once it
  is uncovered; the camera does not move (rule 13 does not apply); no word
  moves (rule 19).
- **The spotlight** (rule 11) on the text dims the other rows only slightly
  (to 60%), so they stay readable, and draws no highlighted cell. The player
  sets the class `qtext` on the text's block; `blocks.css` does the rest.
- **An overlay gloss** is drawn over the foot of the question column (reference:
  absolute, at the column's bottom, the column's width, above the other blocks),
  never over the text or another note. Its top edge is raised so that it lies
  between two lines of what it covers, never through one. While it is shown, a
  mark or the pointer under it is not drawn.
- **The guard** (2026-10-08). `split` and `font` were measured with the
  reference player's fonts and frames. A player whose frame or fonts leave less
  room (a small screen whose controls keep 44 px, a wider font) measures on the
  device whenever the frame's size or the fonts change, and keeps nothing hidden:
  first the text smaller, never below 2.6% of the frame's height (and a wider
  column for it if it still does not fit); then the text's column narrower where
  the question column does not hold its blocks at every moment (each state's
  start, each reveal, each clear); as a last resort the question column smaller,
  to the same floor. Nothing scrolls. On the frames the engine measured, the
  guard changes nothing.

### Required or optional

| Feature | Class | Why | Lessons |
|---|---|---|---|
| `split` and the two-column layout, with the guard | **Required** | in one flow, the text and the question do not fit the board; the owner rejected exactly that ("the whole text is not visible and it scrolls") | R3, R4, R5 |
| `overlay` | **Required** | those glosses do not fit under the question; drawn in flow they run past the board | R3, R4, R5 |
| The light spotlight on the text (`qtext`) | **Required** | with the ordinary spotlight the other paragraphs are too faint to read | R3, R4, R5 |

## 7. Format 1.17 — Part C: the map or paragraph view, the scale, opinion signals

2026-10-08 (ADR 026, the Part C question method). The format of R4 and R5.

### Added

- **`boards[].states[].view`**, on a Part C question board (a board with
  `split` whose states carry `view`): `{map, rows}`. `map` true: the whole text
  as a map, too small to read, the paragraphs in `rows` (from 0) marked, or none.
  `map` false: only the paragraphs `rows`, whole. Absent on other boards.
- **Block type `scale`** (an attitude scale): `left`, `text`, `right`: the
  labels of its negative end, middle and positive end. `items`: its parts in
  order, `{kind, option, at, part}`: `marker` (the view the evidence read so far
  points to, at `at` on 0 to 100 from the negative end, `option` null); `out`
  or `key` (option `option`'s letter placed at `at`, struck or ticked). It is
  usually pinned and a side note.
- **`question.options_later`** (true) with a first part of `kind: "options"`:
  the options are shown only from that part's reveal.
- **`question.target`** (a string): the in-context words the stem prints in
  bold.
- **`doc.parts[].bold`** (a list of strings): the phrases of that row the
  release prints in bold, in order; absent where there are none. The block's
  `html` already wraps them (`<span class="dbold">`).
- **`vocab_table.kind: "recap_grouped"`** with `groups`: `[[question number,
  [lx: id, …]], …]`: one row per question, its words each with a synonym.
- **Cue types** `sig_opinion`, `sig_hedge`, `sig_judge`, `sig_main`,
  `sig_aside` (rule 38), with the fields of an `underline`.
- **Document type `article`.**

```json
"pages-10-11_k48": {
  "id": "pages-10-11_k48", "type": "scale", "role": "note", "pin": true,
  "beside": {"block": "pages-10-11_k14", "row": null},
  "left": "Doubtful", "text": "Neutral", "right": "Keen",
  "items": [{"kind": "marker", "option": null, "at": 60, "part": 1},
            {"kind": "out", "option": "A", "at": 10, "part": 2},
            {"kind": "marker", "option": null, "at": 85, "part": 3},
            {"kind": "key", "option": "C", "at": 85, "part": 4}],
  "html": "<div class=\"blk role-note scl\" data-id=\"pages-10-11_k48\">…<i class=\"pt scl-mk\" data-part=\"pages-10-11_k48.1\" style=\"--at:60%\"></i>…<i class=\"pt scl-op scl-out lane0\" data-l=\"A\" …></i>…</div>"
}
```

```json
"question": {"item": "oa-reading-990027", "kind": "choice", "max_words": null, "options_later": true,
             "target": "placeholder words", "options": [ "…" ]},
"items": [{"kind": "options", "option": null, "text": null, "part": 1},
          {"kind": "out", "option": "A", "text": "placeholder reason", "part": 2},
          {"kind": "key", "option": "C", "text": null, "part": 3}]
```

```json
"states": [
  {"id": "pages-10-11_t3.s1", "view": {"map": true, "rows": []}},
  {"id": "pages-10-11_t3.s2", "view": {"map": true, "rows": [2]}},
  {"id": "pages-10-11_t3.s3", "view": {"map": false, "rows": [2]}},
  {"id": "pages-10-11_t3.s4", "view": {"map": false, "rows": [2, 3]}}
]
```

```json
{"id": "c2", "type": "sig_hedge", "block": "pages-10-11_k14", "text": "may well", "row": 2, "col": 0,
 "time": 2010.12, "time_end": 2010.70}
```

### Rules

- **Rule 37, a Part C question board.** Two columns as rule 36, the text in the
  first. `view.map` true: the whole text at the largest size at which it fits
  its column whole (too small to read; the table floor does not apply;
  reference: searched between 0.3% and 3.2% of the frame's height, then 95% of
  it), the rows of `rows` marked (pale blue with a blue edge) and the others
  faded. `view.map` false: only the rows of `rows`, whole, at the table's `font`,
  with a position cue in the header, "Paragraph 3 of 7" or "Paragraphs 3 and 4
  of 7" (set by the player as `data-pos`, drawn by `blocks.css`, never a word);
  nothing scrolls. The guard of rule 36 measures every paragraph view the board
  has. The text's words move between the map and a paragraph by design (rule
  19 holds within each view). A state with no `view` keeps the board's first
  view.
- **Options later.** A question with `options_later` shows its options only
  from the reveal of its `options` part. Their room, and their reason labels'
  room, is taken from the start of the state in which that part is revealed
  (as a pinned block's room, rule 21), never before, so an option's words never
  move once shown. Reference: the player sets the classes `optroom` and
  `rsnroom` on the question from that state's start; without them `blocks.css`
  keeps the options hidden.
- **Rule 38, opinion-signal marks.** Drawn over the words like any mark:
  `sig_opinion` a solid underline, indigo `#2B006B`; `sig_hedge` a dashed
  underline, teal `#006B60`; `sig_judge` a dotted underline, maroon `#6B0020`;
  `sig_main` an underline with end ticks, brown `#6B4B00`; each with a small
  label above the phrase's first line, white on the same colour: "opinion
  word", "hedge", "judgement", "main clause". `sig_aside` dims its phrase under
  a white veil (55%), with no label. Every block that any of these marks names
  is set with line height 1.75 for its whole board (class `opx`, set by the
  player from the board's start), so a label lies between two lines and nothing
  moves when it comes.
- **Rule 39, an attitude scale.** A line labelled `left`, `text` and `right` at
  its two ends and its middle. Its parts are revealed by rule 5 (a pinned
  scale's from the board's `reveal`, to the board's end). Of its `marker`
  parts only the latest revealed shows, at `at` per cent along the line; an
  `out` part shows the option's letter at `at`, struck; a `key` part, ticked.
  Letters are attributes, never words; every part's room is kept from the
  start. (All of this is in the `html` and `blocks.css`.)
- **Rule 40, bold in a released text.** A row's `bold` phrases and a question's
  `target` are set in the medium weight where they first occur (already in
  the `html`); only the type changes, never a word.

### Required or optional

| Feature | Class | Why | Lessons |
|---|---|---|---|
| `view` (rule 37) | **Required** | the whole article does not fit its column at a readable size; the map and the paragraph view are how it is taught | R4, R5 |
| `options_later` and the `options` part | **Required** | with the 1.17 `blocks.css`, options stay hidden unless the player sets their room | R4, R5 |
| Block type `scale` (rule 39) | **Required** | an unknown block type fails the site's schema; drawn from `html`, it needs its parts switched on | R4 |
| Cues `sig_*` and the `opx` line height (rule 38) | **Required** | the signals are the lesson's teaching; without the line height, the labels cover the line above | R4, R5 (`sig_aside`: R5 only) |
| `bold`, `target` (rule 40) | Optional (data) | the `html` already sets the bold | R4, R5 |
| `recap_grouped`, `groups` | Optional | an ordinary table | R4, R5, L4, L5 |
| Document type `article` look | Optional | decoration in `blocks.css` | R4, R5 |

## 8. Format 1.18 — Listening: recordings in the clock, transcripts, note forms

2026-10-13 (ADR 029). No approved lesson is 1.18: the Listening lessons were
built after 1.20. Everything here except rule 44 is in every 1.20 lesson that
plays a recording (L2–L5).

### Added

**A recording**: an utterance of `kind: "exam"` that plays the exercises
release's own audio inside the lesson's timeline.

- `id`: the id of the utterance holding its `play` cue, plus `.x`.
- `text`: **null** (in 1.12 always a string). `provenance`: `"release"`.
- `audio_file`: `../exam-audio/<extract id>.<12 hex>.mp3`, the release's file
  unchanged. Several recordings can name the same file, each a different span.
- `clip_in`, `clip_out`: the span, in seconds into that file (rule 17). A span
  can start far into the file.
- `cues`: empty. `refs`: empty. `reading`: empty.
- `exam`: `{stimulus, label, span, rows, release, sha256}`: the extract's id, its
  label ("Extract 1"), the span's name (`"exam"`: from the announcement through
  the reading time and the tone to the extract's end; `"extract"`;
  `"lines N-M"`; from 1.19 `"question N"` and `"heading N"`), the transcript rows
  it holds (`[first, last]`, from 0, or null for a whole extract), the release
  ("oa-pkg-sample-tests v2"), and the file's sha256.

**Cue type `play`**, the last cue of the utterance just before the recording
(a short spoken cue such as "Now listen to Extract 1."): `block` **null**,
`text` the extract's id, `with` the span's name, `time` and `time_end` the
recording's start and end.

**A pause's `reading_time`** (true): a pause that is the exam's reading time,
up to 95 seconds (every other pause 0.5 to 10). Defined, but in no approved
bundle: the `"exam"` span includes the reading time.

```json
{"id": "page-12_t1.s6.u2", "text": "Now listen to the placeholder extract.", "provenance": "authored",
 "audio_file": "../page-12/boards/audio/0a1b2c3d4e5f.wav", "start": 1290.10, "end": 1292.00,
 "cues": [{"id": "c1", "type": "play", "block": null, "text": "oa-set-xx-0001-e1", "with": "exam",
           "time": 1292.40, "time_end": 1585.37, "word_index": 4, "anchor_word": "extract"}], "…": "…"},
{"id": "page-12_t1.s6.u2.x", "kind": "exam", "text": null, "provenance": "release",
 "audio_file": "../exam-audio/oa-set-xx-0001-e1.0123456789ab.mp3",
 "start": 1292.40, "end": 1585.37, "clip_in": 0.25, "clip_out": 293.22,
 "cues": [], "refs": [], "reading": [],
 "exam": {"stimulus": "oa-set-xx-0001-e1", "label": "Extract 1", "span": "exam", "rows": null,
          "release": "oa-pkg-sample-tests v2", "sha256": "0123456789ab…"}}
```

**Two document types** (on a core table's `doc`):

- `transcript`: an extract's transcript. `doc.stimulus` the extract's id.
  `parts` kinds `turn` (a line that opens with a speaker's label; `speaker` that
  label, e.g. "Nurse") and `para` (a further paragraph of a talk). Each row is
  the released line, the label included.
- `form`: a Part A note form. `doc.stimulus` the extract, `doc.item` its gap-fill
  item. `parts` kinds `heading` and `num` (`mark` the gap's number, `gap` the
  gap's id). The block's `typed` (1.2) holds each gap's answer, typed in by the
  lesson's `type` cues (rule 10, gaps 1.6). The learner never types.

```json
"doc": {"stimulus": "oa-set-xx-0001-e1", "item": "oa-listening-990007", "label": "Extract 1",
        "title": "Placeholder notes", "text_type": "form",
        "parts": [{"kind": "heading", "mark": null},
                  {"kind": "num", "mark": "1", "gap": "oa-listening-990008"}]}
```

```json
"doc": {"stimulus": "oa-set-xx-0001-e2", "label": "Extract 2", "title": "Placeholder", "text_type": "transcript",
        "parts": [{"kind": "turn", "mark": null, "speaker": "Doctor"},
                  {"kind": "turn", "mark": null, "speaker": "Patient"}]}
```

**`blocks.*.heard`**, on a gloss: `{file, start, end}`: the sentence of a
recording the word is said in, as two times in the extract's own file
(`../exam-audio/…mp3`). The `html` holds a second button:
`<button class="gl-heard" data-audio="../exam-audio/….mp3" data-start="38.82" data-end="40.31">`.

**`text.json`**: a recording is not narration and is not in `narration`; a
transcript or note form on a board is in `board_text` like any document.

### Rules

- **Rule 42, a note form.** A core table whose `doc.text_type` is `form` is a
  document (rule 29): a `heading` row as a heading, a `num` row with its gap
  number as a badge (a stylesheet attribute); each gap a typed part with the
  class `gap`, drawn as a blank line of fixed width until its `type` cue.
- **Rule 43, a recording.** An utterance of `kind: "exam"` plays by rules 1 and
  17: its `audio_file` from `clip_in` to `clip_out`. While the lesson time is
  inside it, the player shows that a recording is playing, over no word.
  Reference: a pill in the header, "Recording · Extract 1" (`exam.label`),
  white on blue `#185FA5` with a pulsing white dot (no pulse under reduced
  motion), `aria-live="polite"`, and a blue outline inside the board's edge
  (`box-shadow: inset 0 0 0 max(2px, .4cqh) #185FA5`). The narration never speaks
  over a recording.
- **Rule 44** (1.18 only, replaced by rule 46 in 1.19): the transcript followed
  by the row spotlight. Not needed.
- **Rule 45, a heard word.** A gloss with `heard` shows a second round button
  with no words; tapping it plays `file` from `start` to `end`, as rule 34
  plays a pronunciation clip (the lesson pauses, then resumes; the lesson's
  clock never plays it).

### Required or optional

| Feature | Class | Why | Lessons |
|---|---|---|---|
| Recordings: `kind`, `exam`, `text` null, `provenance` "release", MP3 `audio_file`, a far `clip_in` | **Required** | the extracts are the lesson's practice material; a 1.12 parser refuses `text` null | L2–L5 |
| Cue `play` (`block` null) | **Required** to accept | an unknown cue type fails the site's 1.12 schema; the recording itself is timed by its utterance | L2–L5 |
| The recording state (rule 43) | **Required** | a rule of the format (owner's decision, ADR 029); without it the board gives no sign that a recording, not the teacher, is speaking | L2–L5 |
| `heard` and its button (rule 45) | **Required** | the button is in the `html` | L2–L5 |
| Transcript and form looks, the form's gap badges (rule 42) | **Required** | the gap numbers exist only in the stylesheet attribute | L2–L5 (form: L2) |
| `doc.item`, `parts[].gap`, `parts[].speaker` | Optional | identifiers; the `html` draws the speaker label | L2–L5 |
| `reading_time` | Accept only | in no approved bundle | none |

## 9. Formats 1.19 and 1.20 — the Listening board

1.19: 2026-10-13 (ADR 030). 1.20: 2026-10-14 (ADR 031). No approved lesson is
1.19. Every Listening lesson is 1.20. L2 is Part A (a note form, two
extracts); L3 Part B (six extracts); L4 and L5 Part C (one extract each). L1
has no recording and uses none of this.

### Added in 1.19

**`boards[].listen`**, on a Listening board (a board whose fixed layer holds a
transcript): absent on other boards.

| Field | Meaning |
|---|---|
| `block` | the transcript's block (a core table, `text_type` `transcript`) |
| `stimulus` | the extract's id |
| `form` | the note form's block on a Part A board, else null |
| `split` | the transcript column's share of the board's width, per cent (1.20: 62) |
| `lines` | the lines the transcript's box shows (10) |
| `font` | the transcript's type, per cent of the frame's height, fixed (1.20: 3.1) |
| `hyphens` | whether the transcript is hyphenated (1.20: false) |
| `form_font` | Part A only: the note form's type, fixed (2.8) |
| `form_room` | Part A only: the room kept under the note form for the board's notes, per cent of the frame's height |
| `row_words` | each transcript row's word count |
| `times` | each word's `[start, end]`, in seconds of the extract's own file. A word is a run of non-space characters of the rows in order, with each speaker's label left out |
| `sections` | `[{from, to, rows, block, row}]`: the extract's sections, words `from` to `to` (inclusive), the rows they run over; `block` the question block shown while a recording is in this section, or null; `row` (Part A) the note form's heading row of this section, or null |

A section's `block` can be a question block that is **in no board layer**
(neither `fixed`, `working` nor `pinned`): the engine builds it from the
release for this purpose (L4 and L5 have 36 such blocks, ids ending
`_sec-<item id>`). From 2026-10-14 a section whose question is pinned on the
board has `block` null (the pinned question is already shown).

The transcript's `html` carries its box: a header table (`lt-head`), a window
(`lt-win`) holding the scrolling rows (`lt-scr`), a marker (`lt-mk`) and a caret
(`lt-caret`). The note form's `html` has the same window.

```json
"listen": {"block": "page-10_k05", "stimulus": "oa-set-xx-0001-e1", "form": null,
  "split": 62, "lines": 10, "font": 3.1, "hyphens": false,
  "row_words": [22, 18, 31],
  "times": [[0.82, 1.10], [1.10, 1.41], [1.45, 1.90], "…"],
  "sections": [{"from": 0, "to": 70, "rows": [0, 2], "block": null, "row": null}],
  "panel": {"font": 2.8, "max": 2,
            "items": [{"block": "page-10_k17", "word": 16, "to": 19, "after_answer": false, "state": "page-10_t2.s11"}]}}
```

and on a Part A board also `"form": "pages-12_k02", "form_font": 2.8, "form_room": 14, "reading": {"font": 3.0}`.

### Added in 1.20

- **`listen.panel`**: `{font, max, items}`: the vocabulary panel's type (per
  cent of the frame's height, fixed: 2.8), the most items it shows, and its
  items in the order they are said, `{block, word, to, after_answer, state}`:
  the gloss, its first and last word in the transcript (indexes into `times`),
  whether it may show during a recording only once its teaching state has
  begun, and that state's id.
- **`listen.reading`** (Part A only): `{font}`: the note form's type while the
  reading time plays (3.0).
- **`blocks.*.panel`**, on a gloss that is a panel item: `{kind, row, word, to,
  pair, after_answer}`: `kind` `medical`, `verb`, `phrase`, `idiom`, `word` or
  `paraphrase`; the transcript row it is said in (from 0); its first and last
  word; a paraphrase pair's printed side (the words of the question, an option
  or the notes), else null; and `after_answer`. Its `synonym` (1.15) is the line
  the item shows; its `heard` (1.18) the sentence it is said in. Such a gloss
  also has the block `kind` equal to `panel.kind` and a `label` "Panel row N";
  neither is drawn. A panel item has no picture.
- **Values:** the transcript is never hyphenated (`hyphens` false), its column
  62%, its type 3.1% (1.19: 58% and 3.4%, hyphenated).

```json
"page-10_k19": {
  "id": "page-10_k19", "type": "gloss", "role": "note", "kind": "paraphrase", "label": "Panel row 4",
  "term": "placeholder", "explanation": "a made-up meaning", "synonym": "stand-in (in the question)",
  "items": [{"kind": "meaning", "text": "a made-up meaning", "part": 1},
            {"kind": "synonym", "text": "stand-in (in the question)", "part": 2},
            {"kind": "example", "text": "A placeholder sentence.", "part": 3}],
  "heard": {"file": "../exam-audio/oa-set-xx-0001-e1.0123456789ab.mp3", "start": 51.47, "end": 55.16},
  "panel": {"kind": "paraphrase", "row": 4, "word": 61, "to": 62, "pair": "stand-in", "after_answer": true},
  "html": "<div class=\"blk role-note gl lvoc lv-pair\" data-id=\"page-10_k19\">…</div>"
}
```

### Rules

- **Rule 46, a Listening board** (replaces rule 44). Two columns: the
  transcript in the first, `split` per cent of the board's width, from the
  board's top; every other block in the second, in flow (reference: padded
  `split` + 2% of the frame's width from the left). The transcript is its
  page's header and a window of `lines` lines. Its type is `font` per cent of
  the frame's height and is fixed: never set smaller by the guard (rule 41).
  Reference measures: type in px = frame height × `font` / 100; line height =
  that × 1.5, rounded to a whole pixel; window height = `lines` × line height;
  rows justified, the last line of each paragraph set left, cell padding 0
  1.4cqw on the right and 1.4cqw + 1.1em on the left; all rows on one line grid
  (no space between rows). The window moves by whole lines only and never shows
  part of a line. The transcript is never covered. The camera never moves on
  the board. A Listening board has no board picture.
- **Rule 47, following a recording.** While the lesson time is inside a
  recording whose `exam.stimulus` is the board's `listen.stimulus`, the word
  being said is the last word whose start (`times[k][0]`) is at or before
  `clip_in` + (lesson time − the utterance's `start`); before the span's first
  word, that first word. The window moves so that this word's line is the
  fourth from the top, or as near as the transcript's start and end allow
  (reference: offset = max(0, min(line − 3, total lines − `lines`)) lines;
  smooth, 0.45 s, none after a seek or under reduced motion). A thin line is
  drawn under the word being said (reference: blue `#185FA5`, max(2px, .32cqh)
  high, 1 px under the word, gliding 0.14 s along its line) and a small caret in
  the left margin at its line (a blue triangle .55em wide). No word is
  recoloured or highlighted. The marker and caret show only once the first word
  of the span has been said. Outside a recording the window shows: the line of
  the panel item being taught (rule 50); else, when the board's table is the
  transcript, the state's `row`; else where the last recording on the board
  ended; else the top. No marker then.
- **Rule 48, the question column follows the sections.** While a recording
  plays, the section holding the word being said shows its `block` (when not
  null) in place of the board's own question blocks, at the top of the column.
  On a Part A board the note form is the board's table (its spotlight and
  typing as rules 10 and 11), drawn at `form_font` (fixed) in a window that ends
  `form_room` per cent of the frame's height above the board's foot, showing
  whole rows only (a row partly outside is not drawn); the window moves to the
  section's heading `row` while a recording plays, or otherwise to the state's
  gap (under its heading where both fit), never past the form's end.
- **Rule 49, the vocabulary panel** (1.20). Drawn in the transcript's column,
  under its window (reference: a gap of 1.5% of the frame's height), down to the
  board's foot, its type `panel.font`, fixed. Its items are glosses with
  `panel`, each with its "hear it in the recording" button (rule 45). A state's
  own panel items are drawn there, not in the question column. Only whole items
  are drawn, at most `max`, the newest last; an item that does not fit is not
  drawn, the oldest first. Reference look: compact, the word in the medium
  weight, the button, the meaning, then "· Similar: " and the synonym line (a
  paraphrase pair, class `lv-pair`: "· Same as: ") as one paragraph, the example
  under it.
- **Rule 50, what the panel shows.** While a recording of the board's extract
  plays: a copy of each item whose `word` has been said (rule 47), every part
  shown, the newest last; an item with `after_answer` only once its `state` has
  begun. Otherwise: the current state's own panel items as they are revealed
  (rule 4). While a state's panel item is revealed and no recording plays, the
  transcript window shows the line of its `word` (rule 47's place, no marker).
- **Rule 51, the reading time** (1.20). On a board with `listen.reading`, while
  a recording of its extract plays and none of its words has been said yet (the
  announcement, the reading time and the tone), the board shows the note form
  alone, every row, the width of the board, at `reading.font`; smaller, to
  `form_font` and then 2.6%, only where it would not fit. The transcript, the
  panel and every other block wait. From the first word on, rules 46 to 50.

### Required or optional

| Feature | Class | Why | Lessons |
|---|---|---|---|
| `listen`, the transcript box and rules 46–47 | **Required** | without them the transcript (up to about 300 words) is one long table: it does not fit, and nothing shows where the recording is | L2–L5 |
| `times`, `row_words` | **Required** | the only source of where each word is said | L2–L5 |
| `sections` and their blocks (rule 48) | **Required** | the question being answered is shown only from here; 36 such blocks in L4, L5 are in no board layer | L4, L5 (`block`); L2 (`row`) |
| The Part A form window (`form`, `form_font`, `form_room`) | **Required** | the form does not fit its column whole | L2 |
| `listen.panel`, a gloss's `panel` (rules 49–50) | **Required** | the panel items are taught by the narration; in the question column they do not fit | L2–L5 |
| `listen.reading` (rule 51) | **Required** | the reading time exists to read the whole note form, as in the exam (owner's decision) | L2 |
| `hyphens`, `split`, `font` values | **Required** (as data) | the box's measures | L2–L5 |
| A gloss's block `kind`, `label` "Panel row N" | Optional | not drawn | L2–L5 |

L1 has `heard` and `panel` null on every block, no recording, and no
Listening board: it plays correctly in a 1.12 player that accepts the format
string, the null fields and its own `blocks.css`.

## 9a. Format 1.21 — a board shown whole; the stray data cleaned up

2026-10-23 (engine ADR 041), released as the tag `bundle-format-v1.21` of the engine's
repository. One optional board field, and the end of the data §12 lists. Grammar 6 is
the only lesson that uses the field.

### Added: `boards[].fit`

| Field | Type | Values | Meaning | When absent |
|---|---|---|---|---|
| `boards[].fit` | string, optional | `"whole"` (the only value) | The board is shown whole on every screen size, at every moment: the player never zooms the view onto a cell or a row of its table, and never pans the table up to its notes (rule 13 does not apply). Where the board does not fit the device, the guard (rule 41) sets the whole board smaller, as far as it needs, keeping the largest size that fits; the table's text may go below its 1.9% floor, every other block stops at 2.6%. | rules 13 and 41 as before |

It is only on a table board on which rule 13 could zoom: a board whose `table` is not
null, with no `split` (a question board), no `listen` (a Listening board), and whose
table has no `map`. Those three never zoom anyway. The engine's checks refuse it
anywhere else, with another value, or in a bundle before 1.21.

```json
{"id": "page-9_t2", "section": "page-9", "table": "page-9_k04", "tight": 2,
 "focus": [{"time": 1110.35, "row": 0, "col": null}, "…"],
 "fit": "whole", "states": ["…"]}
```

### Rule 52, a board shown whole

On a board whose `fit` is `"whole"`, rule 13 does not apply: no camera zoom onto the
highlighted cell or row, and no pan to the side notes, so the whole board, its table
and every note shown, is in view at every moment. The spotlight (rule 11), typing
(rule 10), marks and verdicts are drawn as on any table board. Where the board does not
fit the device, the guard of rule 41 sets the board smaller as far as it needs: the
table's text may go below its 1.9% floor (the reference player bounds its search at a
quarter of the board's size), the other blocks stop at the 2.6% body floor, and the
board keeps the largest size that fits, in steps of 0.5% (reference: once a size that
fits is found, a halving search between it and the last size that did not). The size
holds for the whole board. The fit the bundle states (`clears`, `tight`, the table's
`font`) was planned as for any table board; only the device's guard and the camera
differ.

Measured in the reference player on Grammar 6's board, default fonts: at a 590 px
frame the board at 91.5% (table text 1.74% of the frame's height, about 5.8 px), at 812
px 97%, at 1120 px 100% (no change). With Verdana forced: 89.0%, 92.5% and 93.5%.

**Where it is used:** Grammar 6 (`grammar-06-clause`), board `pages-07-08_t2`, 18:30 to
27:32: the owner's decision of 2026-10-12, until now the exception §10 described as
"not in the bundle". From 1.21 the bundle states it: a player needs no list of lesson
and board ids.

### Changed in the data: the clean-up

From 1.21 the engine writes none of the data §12 lists, in any bundle. Five approved
lessons were rebuilt at 1.21 on 2026-10-23. Their `bundle.json` and `text.json` differ
from the earlier build only in the fields below; nothing they show or play changed
(every board at 590 and 1120 px compared pixel by pixel before and after, every audio
file, time and text compared byte for byte). They keep their final approval.

| Lesson | Field | Before | After |
|---|---|---|---|
| G6 `grammar-06-clause` | `format_version` (`bundle.json` and `text.json`) | `"1.12"` | `"1.21"` |
| G6 | `boards[]` `pages-07-08_t2`: `fit` | absent | `"whole"` |
| R5 `reading-05-part-c-2` | `format_version` (both files) | `"1.17"` | `"1.21"` |
| R5 | `blocks["page-3_k04"].provenance` (the title board's description) | free text beginning `"agent ("` | `"authored"` |
| L2 `listening-02-part-a` | `format_version` (both files) | `"1.20"` | `"1.21"` |
| L2 | `heard` on its 20 word-bank glosses | `{file: "<extract id>.<12 hex>.mp3", stimulus, start, end}`, the file a bare name | `{file: "../exam-audio/<extract id>.<12 hex>.mp3", start, end}`: the path relative to the bundle's folder, as in L3 to L5; `stimulus` gone; `start` and `end` and the block's `html` unchanged |
| L4 `listening-04-part-c` | `format_version` (both files) | `"1.20"` | `"1.21"` |
| L4 | `_tokens` on the 36 section-question blocks (ids ending `_sec-oa-listening-…`) | `[]` | gone |
| L5 `listening-05-part-c-2` | `format_version` (both files) | `"1.20"` | `"1.21"` |
| L5 | `blocks["page-3_k04"].provenance` (the title board's description) | free text beginning `"agent ("` | `"authored"` |
| L5 | `_tokens` on the 36 section-question blocks | `[]` | gone |

No other lesson changed: the other 16 approved bundles are byte for byte as before, at
their own versions (1.12, 1.13, 1.14, 1.16, 1.17, 1.20). A lesson is written at 1.21
when it has a board with `fit`, or when it declares 1.21 because the clean-up rebuilt
it; every other lesson keeps its version until it is rebuilt.

### Can a site that knows only 1.20 read 1.21?

- **The JSON is additive.** Nothing the format documents is removed, renamed or changes
  type. `_tokens` and `heard.stimulus` were never part of the format; `heard.file` now
  has the documented form. A 1.21 bundle is valid 1.20 data plus one optional board
  field.
- **The contract refuses it.** In the site's contracts `contracts-v1.8.0`,
  `format_version` is an enumeration of `"1.8"` to `"1.20"` in
  `schemas/lesson-bundle.schema.json` and `schemas/lesson-text.schema.json`, and so is the
  manifest's `lesson.bundle_format_version` in `schemas/lesson-manifest.schema.json`. A
  1.21 package therefore fails the schema check (`LP-BUNDLE-SCHEMA`, `LP-TEXT-SCHEMA`,
  `LP-MANIFEST-SCHEMA`), at the engine's publish step and at the site's import. The
  board definition allows unknown fields, so `fit` itself passes.
- **Played by a 1.20 player** (if the version check were relaxed): R5, L2, L4 and L5
  play exactly as their 1.20 or 1.17 versions do. G6 plays, but its board
  `pages-07-08_t2` is zoomed and panned like any table board, which is not how the owner
  approved it. Reading 1.21 is safe; playing G6 as approved needs rule 52.
- **The §12 tolerances stay.** The v1 packages of R5, L2, L4 and L5 released on
  2026-10-23 are 1.17 and 1.20 bundles that still hold that data; keep accepting it for
  bundles before 1.21.

### What the site must do

1. **Contracts** (a new release, for example `contracts-v1.9.0`): add `"1.21"` to the
   three enumerations above; add `fit` to the board definition as an optional
   `{"enum": ["whole"]}`. Optionally, for bundles of 1.21 or later, the stricter forms
   now guaranteed: a block's and an utterance's `provenance` one of `source-derived`,
   `adapted`, `corrected`, `authored`, `maintainer`, `release`; `heard` exactly
   `{file, start, end}` with `file` under the package's `audio/`.
2. **Player**: rule 52. Its spotlight, typing, marks and verdicts are unchanged.
3. **Tell the engine** the release's tag and its zip's SHA-256: the engine pins it (a new
   amendment of its ADR 039), and only then packages and publishes any 1.21 lesson.
4. **Field index** (§13): `1.21 bundle.boards[].fit` and `1.21 bundle.boards[].fit = "whole"`.

### The packages that follow, once the site accepts 1.21

| Lesson | Package version | Why |
|---|---|---|
| G6 `grammar-06-clause` | 2 | first engine package of the Grammar and Vocabulary lessons (version 1 was imported by hand on 2026-10-01); the other ten Grammar and Vocabulary lessons are version 2 too, at 1.12 |
| R5 `reading-05-part-c-2` | 2 | its data changed (v1 released 2026-10-23) |
| L2 `listening-02-part-a` | 2 | its data changed (v1 released 2026-10-23) |
| L4 `listening-04-part-c` | 2 | its data changed (v1 released 2026-10-23); the practice-audio swap after oetacademy-exercises #37 is then version 3 |
| L5 `listening-05-part-c-2` | 2 | as L4 |

Nothing else changes for the other published lessons (R1 to R4, L1, L3): their v1
packages stay as they are.

## 10. Player changes with no format version

These apply to every format, 1.12 included, so they also concern the eleven
lessons the site already holds.

- **Rule 41, every board fits the device** (2026-10-11). The fit (`clears`,
  `tight`, a table's `font`, a picture's `size`) was measured with the
  reference player's fonts on its phone and laptop frames. A player whose frame
  or fonts leave less room (a small screen whose controls keep 44 px, a wider
  font) measures each board other than a question board on the device, before
  or when it is first drawn and whenever the frame's size or the fonts change,
  at every state's start and end, every reveal, every pinned block and every
  erase. Where a block shown would lie outside the board, or its words spill
  out of it, it sets the board's pictures smaller (whole, to no less than 10% of
  the frame), then every block of the board smaller together, its layout kept,
  to no less than 2.6% of the frame for body text and 1.9% for a table's text (a
  table stops at its floor, the others go on), until it fits. The size holds for
  the whole board. Where the board fits, nothing changes. Never applied to a
  Listening board's transcript, note form or panel (fixed type).
- **Boards measured ahead** (2026-10-12): how the reference player avoids a
  wait when a large board appears (it measures the next boards in a hidden copy
  of the page). A performance choice, not a rule.
- **One exception not in the bundle** (owner, 2026-10-12): on
  `grammar-06-clause`, board `pages-07-08_t2` only, the camera never zooms onto
  the table's cell nor pans to its notes; the guard sets the board smaller as
  far as the whole table and its notes need, the table's text below its 1.9%
  floor if needed (the other blocks stop at 2.6%), keeping the largest size
  that fits. Until 1.21 the reference player knew it by lesson and board id and
  the bundle did not say it. **From 1.21 the bundle states it**: the board's
  `fit` `"whole"`, rule 52 (§9a); the reference player reads only the field.
- **Phone text size**: no change (owner, 2026-10-12; the site's issue #91).
- **Nothing that stays is redrawn visibly** (owner, 2026-10-25; rule 19). At a new
  state, an erase or a clear, a board's fixed blocks and its pinned blocks keep their
  look: only what changes at that moment changes, and no transition or drawing motion
  is replayed on what stays. The reference player had a flash here (it rebuilt every
  block and set the spotlight again from a reset look, so a table in focus dimmed and
  faded back); see the engine's docs/integration/note-for-site-board-flash.md.

## 11. Audio and other files

| Use | Since | Where named | File | Played |
|---|---|---|---|---|
| Narration | 1.0 | an utterance's `audio_file` | `../<section>/boards/audio/<hash>.wav`, a master; the site's package carries it as AAC `.m4a` | by the lesson's clock |
| Exam recording | 1.18 | a recording's `audio_file` (with `clip_in`, `clip_out`) | `../exam-audio/<extract id>.<12 hex>.mp3`, the exercises release's file byte for byte (sha256 in `exam.sha256`); 1.1 to 6.5 MB each | by the lesson's clock, rule 43 |
| Heard sentence | 1.18 | a gloss's `heard` and its `html` (`data-audio`, `data-start`, `data-end`) | the same exam files | on tap only, rule 45 |
| Pronunciation clip | 1.15 | a gloss's `audio` and its `html` (`data-audio`) | `../vocab-audio/<word>.mp3`, the word bank's clip; 0.5 to 2.3 MB of clips a lesson | on tap only, rule 34 |
| Board picture, gloss image | 1.11, 1.12 | `image.file` and the `html`'s `src` | `../images/<hash>.png` | — |

- **Times are the files' own.** Every time into an exam file (`clip_in`,
  `clip_out`, `heard.start`, `heard.end`, `listen.times`) is seconds into the
  release's MP3 as the browser decodes it. A published copy in another format
  must keep each file's start and length exactly (no added or removed leading
  silence), or every word time shifts.
- **Paths appear in the `html` too.** A publish step that moves or renames the
  audio must rewrite `data-audio` in the block `html` as well as `audio.file`,
  `heard.file` and `audio_file`, as images already require (`image.file` and
  `src`).
- Per lesson: L2 uses 2 exam files, L3 6, L4 1, L5 1; L1 none. Pronunciation
  clips: R3–R5, L3–L5.

## 12. What the approved bundles hold that is not in the format

Found by the cross-check and by reading the bundles. None changes how a lesson
plays in the reference player; a strict validator will see them. **Ended by 1.21**
(§9a): the engine writes none of them from 2026-10-23, and the four lessons that held
them (R5, L2, L4, L5) were rebuilt at 1.21 without them. Their v1 packages, released on
2026-10-23 at 1.17 and 1.20, still hold them until they are republished, so a site
keeps accepting them in bundles before 1.21.

1. **`_tokens`** (an empty list) on the code-built section-question blocks, 36
   in L4 and 36 in L5: a build field that should have been removed. Ignore it.
2. **L2's `heard`** is `{file, stimulus, start, end}` with `file` a bare name
   (`oa-set-la-0001-e1.<hash>.mp3`), not `../exam-audio/…`; L3 to L5 have the
   documented `{file, start, end}`. L2's `html` (`data-audio`) has the correct
   path. A player should take the path from the `html`, or prefix
   `../exam-audio/` when `file` has no folder; ignore `stimulus`.
3. **`provenance` outside its list**: one block in R5 and one in L5 have a
   free-text `provenance` beginning "agent (" instead of `authored`. Provenance
   is for review only and never shown; the site's 1.12 schema refuses it.
4. **Blocks in no board layer**: 36 in L4 and 36 in L5, the section questions of
   rule 48. By design (1.19); a validator that requires every block to be in a
   layer must allow blocks named by `listen.sections[].block`.

### The cross-check

`python spike/scripts/bundle_fields.py` (in the engine's repository; it reads
the lesson library and writes nothing). On 2026-10-22: 21 approved lessons,
formats 1.12, 1.13, 1.14, 1.16, 1.17 and 1.20; not in the 1.12 bundles: 120
field paths, 3 widened types and 68 enumerated values; **uncovered: 0**. Every
one is in the index below, with the version that introduced it. On 2026-10-23,
after 1.21 (§9a): formats 1.12, 1.13, 1.14, 1.16, 1.17, 1.20 and 1.21; 119 paths,
3 widened types and 69 values (`_tokens` and `heard.stimulus` gone, `fit` and its
value added, and Grammar 6's clause-diagram kinds `link` and `dangling`, 1.9, no
longer in a 1.12 bundle); **uncovered: 0**.

## 13. Index of every field path, type and value not in the 1.12 bundles

Read by the cross-check. One entry a line: `<version> <path>` (a new path),
`<path> : <type>` (a new JSON type on a 1.12 path), `<path> = <value>` (a new
value of an enumerated field), `<path> ~ <pattern>` (free-text values matching
a regular expression). Entries in no approved bundle are listed for
completeness.

```fields
# before 1.13, in the 1.12 contract: values only Grammar 6 holds, which is 1.21
# from 2026-10-23 (§9a), so they are no longer in a 1.12 bundle
1.9 bundle.blocks.*.items[].kind = "dangling"
1.9 bundle.blocks.*.items[].kind = "link"
# 1.13
1.13 bundle.blocks.*.doc
1.13 bundle.blocks.*.doc.label
1.13 bundle.blocks.*.doc.parts
1.13 bundle.blocks.*.doc.parts[]
1.13 bundle.blocks.*.doc.parts[].kind
1.13 bundle.blocks.*.doc.parts[].kind = "bullet"
1.13 bundle.blocks.*.doc.parts[].kind = "heading"
1.13 bundle.blocks.*.doc.parts[].kind = "num"
1.13 bundle.blocks.*.doc.parts[].kind = "para"
1.13 bundle.blocks.*.doc.parts[].kind = "thead"
1.13 bundle.blocks.*.doc.parts[].kind = "trow"
1.13 bundle.blocks.*.doc.parts[].mark
1.13 bundle.blocks.*.doc.stimulus
1.13 bundle.blocks.*.doc.text_type
1.13 bundle.blocks.*.doc.text_type = "email"
1.13 bundle.blocks.*.doc.text_type = "extract"
1.13 bundle.blocks.*.doc.text_type = "guideline"
1.13 bundle.blocks.*.doc.text_type = "memo"
1.13 bundle.blocks.*.doc.text_type = "notes"
1.13 bundle.blocks.*.doc.text_type = "policy"
1.13 bundle.blocks.*.doc.text_type = "protocol"
1.13 bundle.blocks.*.doc.text_type = "table"
1.13 bundle.blocks.*.doc.title
1.13 bundle.blocks.*.question
1.13 bundle.blocks.*.question.item
1.13 bundle.blocks.*.question.kind
1.13 bundle.blocks.*.question.kind = "matching"
1.13 bundle.blocks.*.question.kind = "sentence-completion"
1.13 bundle.blocks.*.question.kind = "short-answer"
1.13 bundle.blocks.*.question.max_words
1.13 bundle.boards[].states[].utterances[].cues[].type = "match1"
1.13 bundle.boards[].states[].utterances[].cues[].type = "match2"
1.13 bundle.boards[].states[].utterances[].cues[].type = "match3"
# 1.14
1.14 bundle.blocks.*.map
1.14 bundle.blocks.*.map.docs
1.14 bundle.blocks.*.map.docs[]
1.14 bundle.blocks.*.map.docs[].count
1.14 bundle.blocks.*.map.docs[].first
1.14 bundle.blocks.*.map.docs[].header
1.14 bundle.blocks.*.map.docs[].label
1.14 bundle.blocks.*.map.docs[].parts
1.14 bundle.blocks.*.map.docs[].parts[]
1.14 bundle.blocks.*.map.docs[].parts[].kind
1.14 bundle.blocks.*.map.docs[].parts[].kind = "bullet"
1.14 bundle.blocks.*.map.docs[].parts[].kind = "heading"
1.14 bundle.blocks.*.map.docs[].parts[].kind = "num"
1.14 bundle.blocks.*.map.docs[].parts[].kind = "para"
1.14 bundle.blocks.*.map.docs[].parts[].kind = "thead"
1.14 bundle.blocks.*.map.docs[].parts[].kind = "trow"
1.14 bundle.blocks.*.map.docs[].parts[].mark
1.14 bundle.blocks.*.map.docs[].stimulus
1.14 bundle.blocks.*.map.docs[].text_type
1.14 bundle.blocks.*.map.docs[].text_type = "guideline"
1.14 bundle.blocks.*.map.docs[].text_type = "notes"
1.14 bundle.blocks.*.map.docs[].text_type = "protocol"
1.14 bundle.blocks.*.map.docs[].text_type = "table"
1.14 bundle.blocks.*.map.docs[].title
1.14 bundle.boards[].states[].doc
1.14 bundle.boards[].states[].zoom
1.14 bundle.boards[].states[].zoom = "doc"
1.14 bundle.boards[].states[].zoom = "row"
# 1.15
1.15 bundle.blocks.*.audio
1.15 bundle.blocks.*.audio.file
1.15 bundle.blocks.*.audio.seconds
1.15 bundle.blocks.*.doc.text_type = "manual"
1.15 bundle.blocks.*.doc.text_type = "notice"
1.15 bundle.blocks.*.doc.text_type = "procedure"
1.15 bundle.blocks.*.items[].kind = "key"
1.15 bundle.blocks.*.items[].kind = "out"
1.15 bundle.blocks.*.items[].kind = "synonym"
1.15 bundle.blocks.*.items[].option
1.15 bundle.blocks.*.items[].text : null
1.15 bundle.blocks.*.lexicon
1.15 bundle.blocks.*.question.kind = "choice"
1.15 bundle.blocks.*.question.options
1.15 bundle.blocks.*.question.options[]
1.15 bundle.blocks.*.question.options[].letter
1.15 bundle.blocks.*.question.options[].option
1.15 bundle.blocks.*.question.options[].text
1.15 bundle.blocks.*.synonym
1.15 bundle.blocks.*.vocab_table
1.15 bundle.blocks.*.vocab_table.kind
1.15 bundle.blocks.*.vocab_table.kind = "match"
1.15 bundle.blocks.*.vocab_table.kind = "recap"
1.15 bundle.blocks.*.vocab_table.lexicon
1.15 bundle.blocks.*.vocab_table.lexicon[]
1.15 bundle.boards[].lens
1.15 bundle.boards[].lens_from
1.15 bundle.boards[].states[].veil
# 1.16
1.16 bundle.boards[].split
1.16 bundle.boards[].states[].overlay
1.16 bundle.boards[].states[].overlay[]
# 1.17
1.17 bundle.blocks.*.doc.parts[].bold
1.17 bundle.blocks.*.doc.parts[].bold[]
1.17 bundle.blocks.*.doc.text_type = "article"
1.17 bundle.blocks.*.items[].kind = "options"
1.17 bundle.blocks.*.question.options_later
1.17 bundle.blocks.*.question.target
1.17 bundle.blocks.*.type = "scale"
1.17 bundle.blocks.*.vocab_table.groups
1.17 bundle.blocks.*.vocab_table.groups[]
1.17 bundle.blocks.*.vocab_table.groups[][]
1.17 bundle.blocks.*.vocab_table.groups[][][]
1.17 bundle.blocks.*.vocab_table.kind = "recap_grouped"
1.17 bundle.boards[].states[].utterances[].cues[].type = "sig_aside"
1.17 bundle.boards[].states[].utterances[].cues[].type = "sig_hedge"
1.17 bundle.boards[].states[].utterances[].cues[].type = "sig_judge"
1.17 bundle.boards[].states[].utterances[].cues[].type = "sig_main"
1.17 bundle.boards[].states[].utterances[].cues[].type = "sig_opinion"
1.17 bundle.boards[].states[].view
1.17 bundle.boards[].states[].view.map
1.17 bundle.boards[].states[].view.rows
1.17 bundle.boards[].states[].view.rows[]
# not the format: free-text provenance on one block of R5 and one of L5 (§12, item 3);
# in no approved bundle from 1.21 (§9a), kept for the v1 packages
1.17 bundle.blocks.*.provenance ~ "^agent \\("
# 1.18
1.18 bundle.blocks.*.doc.item
1.18 bundle.blocks.*.doc.parts[].gap
1.18 bundle.blocks.*.doc.parts[].kind = "turn"
1.18 bundle.blocks.*.doc.parts[].speaker
1.18 bundle.blocks.*.doc.text_type = "form"
1.18 bundle.blocks.*.doc.text_type = "transcript"
1.18 bundle.blocks.*.heard
1.18 bundle.blocks.*.heard.end
1.18 bundle.blocks.*.heard.file
1.18 bundle.blocks.*.heard.start
1.18 bundle.boards[].states[].utterances[].cues[].block : null
1.18 bundle.boards[].states[].utterances[].cues[].reading_time
1.18 bundle.boards[].states[].utterances[].cues[].type = "play"
1.18 bundle.boards[].states[].utterances[].exam
1.18 bundle.boards[].states[].utterances[].exam.label
1.18 bundle.boards[].states[].utterances[].exam.release
1.18 bundle.boards[].states[].utterances[].exam.rows
1.18 bundle.boards[].states[].utterances[].exam.rows[]
1.18 bundle.boards[].states[].utterances[].exam.sha256
1.18 bundle.boards[].states[].utterances[].exam.span
1.18 bundle.boards[].states[].utterances[].exam.stimulus
1.18 bundle.boards[].states[].utterances[].kind
1.18 bundle.boards[].states[].utterances[].kind = "exam"
1.18 bundle.boards[].states[].utterances[].provenance = "release"
1.18 bundle.boards[].states[].utterances[].text : null
# 1.19
1.19 bundle.boards[].listen
1.19 bundle.boards[].listen.block
1.19 bundle.boards[].listen.font
1.19 bundle.boards[].listen.form
1.19 bundle.boards[].listen.form_font
1.19 bundle.boards[].listen.form_room
1.19 bundle.boards[].listen.hyphens
1.19 bundle.boards[].listen.lines
1.19 bundle.boards[].listen.row_words
1.19 bundle.boards[].listen.row_words[]
1.19 bundle.boards[].listen.sections
1.19 bundle.boards[].listen.sections[]
1.19 bundle.boards[].listen.sections[].block
1.19 bundle.boards[].listen.sections[].from
1.19 bundle.boards[].listen.sections[].row
1.19 bundle.boards[].listen.sections[].rows
1.19 bundle.boards[].listen.sections[].rows[]
1.19 bundle.boards[].listen.sections[].to
1.19 bundle.boards[].listen.split
1.19 bundle.boards[].listen.stimulus
1.19 bundle.boards[].listen.times
1.19 bundle.boards[].listen.times[]
1.19 bundle.boards[].listen.times[][]
# 1.20
1.20 bundle.blocks.*.kind = "idiom"
1.20 bundle.blocks.*.kind = "medical"
1.20 bundle.blocks.*.kind = "paraphrase"
1.20 bundle.blocks.*.kind = "phrase"
1.20 bundle.blocks.*.kind = "verb"
1.20 bundle.blocks.*.kind = "word"
1.20 bundle.blocks.*.panel
1.20 bundle.blocks.*.panel.after_answer
1.20 bundle.blocks.*.panel.kind
1.20 bundle.blocks.*.panel.kind = "idiom"
1.20 bundle.blocks.*.panel.kind = "medical"
1.20 bundle.blocks.*.panel.kind = "paraphrase"
1.20 bundle.blocks.*.panel.kind = "phrase"
1.20 bundle.blocks.*.panel.kind = "verb"
1.20 bundle.blocks.*.panel.kind = "word"
1.20 bundle.blocks.*.panel.pair
1.20 bundle.blocks.*.panel.row
1.20 bundle.blocks.*.panel.to
1.20 bundle.blocks.*.panel.word
1.20 bundle.boards[].listen.panel
1.20 bundle.boards[].listen.panel.font
1.20 bundle.boards[].listen.panel.items
1.20 bundle.boards[].listen.panel.items[]
1.20 bundle.boards[].listen.panel.items[].after_answer
1.20 bundle.boards[].listen.panel.items[].block
1.20 bundle.boards[].listen.panel.items[].state
1.20 bundle.boards[].listen.panel.items[].to
1.20 bundle.boards[].listen.panel.items[].word
1.20 bundle.boards[].listen.panel.max
1.20 bundle.boards[].listen.reading
1.20 bundle.boards[].listen.reading.font
# not the format: a build field (§12, item 1) and L2's extra heard field (§12, item 2);
# in no approved bundle from 1.21 (§9a), kept for the v1 packages
1.20 bundle.blocks.*._tokens
1.20 bundle.blocks.*.heard.stimulus
# 1.21
1.21 bundle.boards[].fit
1.21 bundle.boards[].fit = "whole"
```
