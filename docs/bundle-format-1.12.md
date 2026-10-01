# Lesson bundle 1.12: what changed since 1.11

For the oetacademy-web team, before importing the 11 approved lessons.
Written 2026-10-01. The full contract is docs/04-LESSON-BUNDLE.md (format
1.12); this page lists only what differs from 1.11. Every count below was
measured on the 11 lessons as built today.

## Summary

- `format_version` is `"1.12"` in both `bundle.json` and `text.json`. All 11
  lessons are 1.12.
- **Data: additive only.** One new block type (`picture`) and one new block
  field (`size`). No field is removed, renamed or changes type, so a 1.11
  parser reads a 1.12 bundle.
- **Rendering: two rules changed.** On table boards, side notes now go under
  the table instead of next to their row, and nothing may be drawn over
  anything else. The data has not changed, but a player built to the 1.11
  rules would put side notes in the wrong place.
- **Two lesson ids are now lower case.** This is not a format change, but it
  breaks anything that stored the old ids.

| # | Change | Where | Kind |
|---|---|---|---|
| 1 | New block type `picture` | `bundle.json` `blocks{}` | Additive |
| 2 | New block field `size` (pictures only) | `bundle.json` `blocks{}` | Additive |
| 3 | Picture blocks are listed in `text.json` with empty text | `text.json` | Additive (no new field) |
| 4 | Side notes go under the table, not over its rows (rule 12) | player | Rendering change; no data change |
| 5 | The view pans to side notes that run past the board (rule 13) | player | Rendering change; no data change |
| 6 | Nothing is drawn over anything (rule 28) | player | New rendering rule; no data change |
| 7 | `blocks.css`: picture styles, side-note width, timeline label lines | `blocks.css` | Additive; replace the shared copy |
| 8 | Lesson ids are lower case; two lessons renamed | `lesson.id`, `refs`, folder names | Breaking for stored ids; no format change |

## 1. The `picture` block (new)

Each board gets one generated illustration that relates to its content: the
patient in the case notes, a clinic scene, or a picture of the concept. It
appears when the board opens. It has no words, and the narration never
mentions it or points at it.

### Fields

| Field | Value |
|---|---|
| `id` | a block id like any other, e.g. `page-3_k11` |
| `type` | `"picture"` |
| `image` | `{file, alt}`. `file` is a path relative to the folder holding `bundle.json`, e.g. `../images/234402f110503e5c.png`. `alt` is the alt text, a short phrase, e.g. `"A doctor writing a letter at a desk"` |
| `size` | **New in 1.12, pictures only.** The side of the picture's square box in `cqh` (hundredths of the 16:9 frame's height). `null` means 20. It is set only where the board would not fit otherwise, and never below 10. In today's lessons, 3 of 103 pictures have it, all set to 10 |
| `icon` | the pipeline's image brief, `"alt text \| what to draw"`. Production data: do not display it |
| `role` | `"note"` |
| `provenance` | `"authored"`: generated, not taken from the source lesson. For review; never shown to students |
| `beside` | on a table board, `{block: <table id>, row: null}`; otherwise `null` |
| `html` | see below |

All other block fields are `null` (`text`, `label`, `term`, `explanation`,
`items` and so on).

The `html`:

```html
<div class="blk role-note pic" data-id="page-3_k11" role="img" aria-label="A doctor writing a letter at a desk"><img class="pic-img" src="../images/234402f110503e5c.png" alt="A doctor writing a letter at a desk"></div>
```

When `size` is set, the `div` also carries `style="--ph:10.0cqh"`.

### Where it appears in the timeline (rule 27)

- It is always the **first** entry in the `working` list of its board's
  **first** state. It is never in `fixed` and never in `pinned`.
- It is revealed at the state's `start` (`state.reveal[id]` equals
  `state.start`). No cue targets it, and no `reading` entry includes it.
- It disappears at the state's `until` (the erase), or earlier when a
  `clears` entry lists it because later notes need its room. This happens 27
  times across today's lessons.
- It is drawn in the board's flow, in a square box of `size` cqh (default
  20), with the image scaled to fit inside the box (`object-fit: contain`).
  On a table board it sits at the right under the table, with the side notes
  to its left.

### The image files

- **Location:** `<lesson>/generated/images/<16 hex chars>.png`, which is
  `../images/` from `generated/lesson-player/`. The folder is **outside** the
  lesson-player folder, so the import must copy it. Gloss images (1.11) are
  in the same folder, in the same format.
- **Only copy files a bundle names.** The folder also holds earlier drafts
  that no bundle uses. Copy exactly the files named by an `image.file`, on
  both `picture` and `gloss` blocks.
- **Shared files:** the file name is a hash of the brief, so several blocks
  can name the same file (the items of one exercise share a picture). The
  103 picture blocks use 43 files.
- **Format:** PNG with an 8-bit palette (256 colours) and a transparent
  background. The subject is trimmed to its edges, so the image is not square.
- **Size:** the longer side is always 512 px. The shorter side ranges from
  185 to 512 px in today's lessons. Files measure 15–70 KB, 42 KB on average
  (picture and gloss images together). These are what the pipeline produces;
  the contract sets no limit.

### Alt text and captions

- **Alt text: yes.** It is in `image.alt`, and the `html` repeats it in the
  `img` element's `alt` and the `div` element's `aria-label`.
- **Captions: none.** There is no caption field, and nothing is drawn under
  the image.

### Which lessons have pictures

- **Grammar 8 and Vocabulary 1–3:** every board, including the title and
  contents boards.
- **Grammar 1–7: none.** These lessons were built before pictures existed and
  rebuilt to 1.12 without them. A 1.12 bundle can therefore contain no
  picture blocks at all.

## 2. `text.json`

Each picture block is listed in `sections[].boards[].board_text` as
`{"block": "<id>", "text": ""}`, and it adds an empty paragraph to
`sections[].board_text` (e.g. `"Grammar for OET: Paraphrasing\n\n\n\nThe
lesson Punctuation …"`). Skip empty entries when indexing for search or chat.

## 3. Rendering rules (no data change)

- **Rule 12, side notes (changed).** A working block with `beside` is drawn
  **under** the table, and under anything else in the board's flow, in the
  order its state lists the notes. It is never drawn over the table or over
  any text. In 1.11 a side note sat next to its row, over the other rows.
  `beside.row` still names the row. The row is now shown by the spotlight
  (`focus`), not by where the note sits. A diagram side note (timeline or
  clause diagram) is as wide as the table.
- **Rule 13, auto zoom (extended).** When the visible side notes run past the
  bottom of the board, the view pans the table up, without zooming, until
  they are in view. Under `prefers-reduced-motion` this happens without
  animation.
- **Rule 28, nothing over anything (new).** In every state, no block may be
  drawn over another block or its text, and no text over other text. The
  pipeline checks this at phone-landscape and laptop widths. If you draw
  timelines from their data rather than using `html`, put marker labels that
  would collide on extra lines under the axis. The `html` already does this.

## 4. `blocks.css`

`blocks.css` is identical for every lesson built at one format version, so
replace your shared copy with the 1.12 file. Changes:

- **New:** `.blk.pic`, the square box, sized by `--ph` (default `20cqh`), with
  no padding, border or background. `.blk.pic .pic-img` scales the image to
  fit (`object-fit: contain`).
- **Changed:** `.blk.beside` `max-width` goes from 58% to 100%. New rule
  `.blk.tl.beside, .blk.cl.beside { width: 100% }`: a diagram side note is as
  wide as the table.
- **Changed:** `.tl-marker .lab.below` now offsets by `--lane`. A timeline
  marker label that would collide is set on a further line, and the diagram
  is taller. The `html` sets `--lane:N` on the labels that need it. No data
  field changes.

## 5. Lesson ids are lower case (2026-10-01)

Lesson ids must be lower case. The engine now refuses any other at build
time and when it builds the course index. Two lessons were renamed. Their
content and approvals are unchanged: apart from the id, their `bundle.json`
and `text.json` are byte-identical to the approved build.

| Old id | New id |
|---|---|
| `vocabulary-02-Collocations` | `vocabulary-02-collocations` |
| `vocabulary-03-Collocations-2` | `vocabulary-03-collocations-2` |

The new ids appear in the folder names, `lesson.id` in both JSON files, and
Vocabulary 3's `refs` to Vocabulary 2. Every other lesson id was already
lower case.

## Unchanged

Everything else is as in 1.11, including the `gloss` block and its image
(rules 25 and 26), the ids and their stability rules, audio, and every other
block type.

## Checklist for the player and the import

1. Accept `format_version` `"1.12"` in `bundle.json` and `text.json`.
2. Render `picture` blocks: show the image from its state's `start` until its
   state's `until` or a `clears` entry that lists it, in a square box of
   `size` cqh (20 when `null`), with `image.alt` as alt text. Do not display
   `icon`.
3. Copy the files named by `image.file` (pictures and glosses) from
   `generated/images/`, and only those, keeping the relative path or mapping
   it.
4. Draw side notes under the table, never over it, and put a table board's
   picture at the right under the table.
5. Pan the table up when its visible side notes run past the board.
6. Never draw a block over another block, or text over text.
7. Skip empty `board_text` entries in `text.json`.
8. Use the lower-case ids for the two vocabulary lessons.
