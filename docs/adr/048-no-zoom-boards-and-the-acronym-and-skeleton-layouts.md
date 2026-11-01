# 048 — A board marked no-zoom; the `acronym` and `skeleton` layouts; `block_accents`

Date: 2026-11-01
Status: **Accepted**: the owner's authorisation of 2026-11-01, in chat, after the agent's stop report on his
addendum for writing-07-organisation v2 ("make the three shared changes, small and guarded"). How each is
carried is the agent's under that authorisation (ADR 005).

## Context

- The owner reviewed Writing 7 v1 and asked for three things on two boards: the ISBAR table drawn after his own
  slide (each letter large, bold and in colour in its own narrow column, the part's name in bold beside it);
  no zoom on that board, since the style C zoom (rule 55) pushed part of its sentences off screen and he wants
  the whole table in view at every moment, the spotlight and the marker alone showing the row; and his
  "Request" slide brought back: two letters side by side as skeletons, the opening written out with the purpose
  words in colour, the body as short dashed lines, the request expanded at the end in colour.
- None of the three could be done in a lesson's own files. The style C zoom is written for every Writing table
  shown whole or set at 2.8% or less, with one exemption, the paper beside the letter (ADR 045), and no
  per-board setting; the fourteen layouts of §7j draw no first cell as a large letter; nothing draws dashed
  lines that are not words, and the only inline colours are the marker and the strike, green being reserved
  for "right" (§5).

## Options considered

1. Build the boards with what exists: a bold three-column table, still zoomed; the skeletons as a `pair`.
   Rejected by the owner's addendum: the zoom is the complaint, and the skeleton's dashes would be words.
2. A bundle field for "no zoom" (a new format). Not needed: the zoom is data the builder writes (an `effects`
   entry); a board with none, shown whole (`fit`, rule 52), already stays whole in every renderer.
3. Three small, guarded additions to the builder and the stylesheet, documented in the design system and the
   bundle's rule 55, proven to change no built lesson (chosen).

## Decision

1. **`boards_nozoom`** (sections.json): a list of board ids, each a board named in `boards_fit` as `"whole"`
   (else refused), in a style C lesson (else refused). The builder writes no `zoom` entry for such a board
   (`style_c.effects`, its `nozoom`); shown whole, it stays whole at every moment on every device, and its
   spotlight (rule 11) and its marks alone show the line being taught. Rule 55's text says so; the bundle's
   format does not change.
2. **The `acronym` layout** (§7j): a table of two columns whose first cell is a letter, a colon and the part's
   name ("I: Introduce and identify"; else refused). The letter is wrapped in its own span and drawn large,
   bold and in the key-word amber in a narrow column, the name in bold beside it; the colon stays in the words,
   drawn at no size (as the contents board's separators are, ADR 043). First used on Writing 7's ISBAR board,
   shown whole and marked no-zoom.
3. **The `skeleton` layout** (§7j): a table of two columns, two letters side by side, a paragraph a row. A
   paragraph written out is shown in full; an empty cell with a written paragraph below it in its column is
   drawn as three short dashed lines by the stylesheet (`data-dash`, never a word); the last paragraph written
   out of each letter (`data-end`, the request expanded) is set in the Purpose criterion's colour; each letter
   opens with a paragraph written out (else refused). A letter that ends earlier leaves its sheet short.
4. **`block_accents`** (sections.json): `{"<bundle block id>": ["phrase", ...]}`, the words a layout sets in its
   accent colour, on a block whose layout draws them (`skeleton`; else refused). Each phrase is found exactly
   once in the block's words, never split by a tag (else refused), and wrapped in a span `acc`, drawn in the
   Purpose colour. The words never change (checked as for every layout). Green stays reserved for "right"
   (the owner, 2026-11-01).
5. **Where the rules live**: the two layouts' rules are appended only to the stylesheet of a lesson that uses
   them (`style_c.LAYOUT_CSS`, as the phase 2 forms, ADR 043 amendment (3)); the shared stylesheet and bundle
   1.22 are unchanged (rule 53 already names `lay-<layout>`), so the site has nothing to do.

## Consequences

- Proven on every built lesson, rendered before and after the change and compared byte for byte
  (`render_compare.py`), in the pull request that carries this record.
- A lesson wanting a table whole and still (a table whose rows are seen together) names it in `boards_fit` and
  `boards_nozoom`; the paper beside the letter keeps its own exemption (ADR 045).
- The "Creative board design" record of the same day, if it adds layouts, adds them beside these.
