# 008 — The board style: kinds of content, change flows, word-class colours

Date: 2026-09-25
Status: **Accepted** by the maintainer in chat, 2026-09-25, against a sample of
Grammar 3's pages 4-5 built from the reference
`docs/prototypes/p4-board-style-prototype.html`. The bundle change is format
1.3 of docs/04-LESSON-BUNDLE.md. The rule is docs/02-DESIGN-SYSTEM.md §7c.

## Context

The maintainer's slides separate what the slide says from what the teacher
adds: the slide's sentences sit in coloured rounded boxes, a changing word is
coloured in its sentence, an underline stays inside the sentence it marks, a
header pill names the topic. The boards did not: a slide sentence, a
teacher's example and a note all looked alike, a marked clause was repeated as
a separate box, and a change ("analyse" to "analysis") was a plain two-column
comparison under a capitals label.

A first sample only recoloured the boxes; the maintainer rejected it as too
plain and supplied the prototype as the style direction.

## Options considered

1. **Recolour by kind only** (the first sample). Separates the kinds, but a
   change still reads as a table, not as a change.
2. **A new block vocabulary written by the screens model** (flows, change
   cards as block types). Would change the reply schema, which is at its
   grammar limit, and would mean writing every section again, with new
   narration and audio.
3. **Derive the style from the blocks that exist** (this decision). Every
   comparison is already a change; every slide sentence is already known
   (its text is printed on the slide); the words that change are already
   named on the cards. A rule can draw them as a flow, with no model call and
   no change to text, ids, cues or narration.

## Decision

Option 3, for every lesson, as docs/02-DESIGN-SYSTEM.md §7c describes:

- each block has a **role**, slide, example or note, set by a rule (text
  printed on the slide, a board's table, a printed exercise sentence: slide;
  a correct or wrong sentence not printed, or a comparison of two sentences:
  example; everything else: note); an override corrects the rule where it is
  wrong, as for text;
- slide content is never erased: a slide block revealed during the teaching,
  and the definition pill, are **pinned** until the board ends;
- a change is drawn as a **flow**: definition pill, source sentence, process
  pill beside the change cards, result, notes;
- a slide block whose text is part of another slide block on the board is
  **folded** into it: not drawn, its cues retargeted to the same words in the
  sentence it belongs to;
- **word-class colours** link a changing word in the source to its card and
  to the result. Red and green stay reserved for wrong and correct; the four
  colours were chosen by measured difference (CIEDE2000), and the screens
  audit fails a board where two colours on it are too alike;
- labels are in sentence case; the orange pill of the maintainer's slides is
  kept; the font is unchanged.

The code is `spike/scripts/board_style.py`, used by the screens stage and the
bundle builder; the reference renderer draws pinned blocks and word marks.

## Consequences

- Bundle format 1.3: a block's `role`, `style`, `card`, `pin`, `fold_into`,
  `flow` and `band`; a board's `pinned` and `wordmarks`; a cue's phrase
  retargeted where a block is folded or a card's class is a tag. A 1.2 reader
  ignores them and still shows every block.
- Narration and audio are unchanged by the style: a lesson built before it
  takes it by re-rendering its screens and rebuilding its player, with no
  model call and no synthesis. Grammar 1 and 2 are not rebuilt now.
- The screens model is unchanged. Where the rule classifies a block wrongly
  (Grammar 3: a "Before / After" statement taken for an example), an override
  corrects it and is logged.
- Two word-class colours are close to tense accents. A tense lesson that
  colours word classes on a board with those tense colours fails its audit;
  the fix then is a different board, not a different colour.
- Table text now starts at body size and shrinks only to fit (§7 "Tables"):
  a small slide table no longer reads smaller than the notes beside it.
