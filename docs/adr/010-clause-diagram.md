# 010 — The clause diagram: sentences drawn as puzzle pieces

Date: 2026-09-27
Status: **Accepted** by the maintainer in chat, 2026-09-27, at the coverage
review of Grammar 5 (Complex sentences): "The clause diagram block (ADR 010,
bundle 1.7, design system) approved as you described: pieces stay still, the
tab slides into the notch; dependent = clause magenta, independent = neutral
slate, glue = orange, V = verb blue." The rule is docs/02-DESIGN-SYSTEM.md §7d;
the data is docs/04-LESSON-BUNDLE.md, format 1.7.

## Context

Grammar 5 teaches how clauses join: a dependent clause cannot stand alone, an
independent clause can, a joining word (the teacher's "glue") joins them, and
the comma follows a dependent clause that comes first. The maintainer asked for
this lesson to be visually strong and supplied a reference,
`docs/prototypes/p5-complex-sentence-prototype.html`: two puzzle pieces that
join, "although" as a glue chip, the sentence coloured by clause with subject
and verb labels, and the stand-alone test. The maintainer asked that any new
block be a general rule, usable in later lessons.

No block could show it. A comparison or a change card shows two things side by
side, not two parts of one sentence that fit together; a timeline is a time
axis. The screens model never draws (design system §7a): a diagram is data that
code draws.

## Options considered

1. **Existing blocks only**: the sentence as a plain block with word marks
   (clause colours) and notes. No pieces, no join; the idea "one part cannot
   stand alone" is only said, never seen.
2. **A drawing per lesson** (hand-made SVG). Not data, not audited, and not
   reusable: a later lesson would redraw it.
3. **A new diagram block drawn by code from parts** (this decision), like the
   timeline: the model lists the parts, code draws them, the narration reveals
   them one by one.

For the join, the prototype slides the two pieces together. That moves every
word of the sentence, which docs/02-DESIGN-SYSTEM.md §8a forbids ("nothing
about a board's state moves any text"). The pieces therefore stay still and the
dependent piece's tab slides across the fixed gap into the independent piece's
notch.

For colour, no new hue fits the palette: every candidate measured (CIEDE2000)
too close to a word-class colour or to red or green (violet to verb 16 and to
clause 19; orange to noun 16 and to red 18). The diagram uses colours whose
meaning already fits.

## Decision

A new block type, `clauses`, for every lesson (docs/02-DESIGN-SYSTEM.md §7d):

- **Parts**, in teaching order, each revealed by the narration like a
  timeline part (`<block id>.<n>`): `dependent` and `independent` pieces (one
  or two, in sentence order, with their words), `glue` (the joining word: a
  chip inside a piece, or, between two independent pieces, a bridge), `subject`
  and `verb` (an S or V label over a phrase of a piece), and `join` (last: the
  tab slides into the notch, and the comma shows when the dependent clause
  comes first). At most ten parts.
- **Look**: a dependent piece in the word-class clause magenta (`#CB0BAB`) on a
  pale tint, with a tab facing the other piece; an independent piece in neutral
  slate (`#475569`) with a notch; the glue in the orange of the maintainer's
  pills (`#F7A531`), which his own slide uses for "glue"; the V label and its
  verb in the verb blue (`#084191`); the S label neutral. Kind labels
  ("Dependent clause", "Independent clause") in small sentence case.
- **Nothing moves a word**: the S and V labels sit in the line's own leading,
  the glue chip is a background and a shadow, the comma's room is reserved, and
  only the tab and its neck move (§8a). The motion is the renderer's.
- **Role**: `slide` when it is the fixed layer (the slide's own diagram),
  `example` otherwise.
- **Pipeline**: `write_screens.py` (prompt, `clause_items`, audit, height,
  html, CSS), `write_narration.py` (parts shown to the model, the reveal
  audit), `qa_narration.py` (parts shown to the reviewer),
  `build_lesson_player.py` (format 1.7, reveal times of the parts),
  `check_board_page.py` (a part reveal on a clause diagram),
  `board_player_template.html` (motion).
- **Bundle 1.7**: the block type `clauses`, its `items` (`{kind, text, piece,
  part}`), and renderer rule 20. A 1.6 reader that shows the block's `html`
  with `blocks.css` and reveals its `data-part` elements by rule 5 draws it
  whole, without the join's motion.

## Consequences

- Lessons 1-4 are unaffected: every section's screens re-render byte-identical
  with the new code (checked 2026-09-27, files restored), and their bundles stay
  at their format until rebuilt.
- The glue orange is the definition pill's orange. On a board they meet, the
  pill names the grammar term and the chip marks the joining word; the
  maintainer accepted the colour for the glue.
- The independent clause is neutral slate, not a word-class colour, so the
  colour-clash audit is unchanged.
- A later lesson on relative clauses, conditionals or reported speech can draw
  its clauses the same way.
