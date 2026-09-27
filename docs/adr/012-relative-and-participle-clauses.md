# 012 — Relative and participle clauses in the clause diagram

Date: 2026-09-27
Status: **Accepted** by the maintainer in chat, 2026-09-27, at the coverage
review of Grammar 6 (Relative clauses and participle clauses): "Build the ADR
012 extension (bundle 1.9) as you described: embedded piece, non-defining
removal test with comma edges, defining removal giving a red line, and the
subject link arc (landing / broken with ✕). General rules, usable in future
lessons." The rule is docs/02-DESIGN-SYSTEM.md §7d; the data is
docs/04-LESSON-BUNDLE.md, format 1.9.

## Context

Grammar 6 teaches relative clauses (defining and non-defining), how to reduce
them, and participle clauses. The maintainer asked for it to be visually strong
in the style of Grammar 5's clause diagram (ADR 010), with three ideas:

- a non-defining clause as a removable piece whose commas are its edges, the
  sentence still working without it; a defining clause fixed in place, whose
  removal loses who we mean;
- reduction shown by striking the removed words and writing the reduced
  sentence as a new line;
- participle clauses shown with the subject both clauses share, and a dangling
  participle as a wrong example.

The clause diagram of ADR 010 draws one or two pieces side by side. It cannot
draw a clause **inside** a sentence ("Ms Smith, who is a 19-year-old woman,
recently tested positive"), and nothing links a participle to its subject.
Reduction needs nothing new: in a table board the removed words are struck in
the standard sentence's cell and the reduced sentence is typed in the next
column, a new line of its own.

## Options considered

1. **Existing blocks only**: a clause at the end of a sentence as two pieces,
   the removal test as a green or red row, the shared subject as an arrow mark.
   A clause in mid-sentence cannot be drawn, and the test is two unrelated
   blocks.
2. **Move the clause out of the sentence** when it is removed. Moves words,
   which docs/02-DESIGN-SYSTEM.md §8a forbids.
3. **New parts of the clause diagram, styled in place** (this decision).

## Decision

Five new part kinds of the `clauses` block, for every lesson (docs/02-DESIGN-SYSTEM.md §7d):

- `defining`, `nondefining`: a relative clause set into an independent piece,
  named by its words; the piece holds the whole sentence. Non-defining: the
  clause tint with a dashed edge, its commas coloured as its edges. Defining: a
  solid edge and a slate pin at each end, no commas. The audit fails a
  non-defining clause with no comma before it and a defining clause with one.
- `remove`: the removal test, the last part. Code writes the sentence without
  the clause (and its commas) on a line under the pieces, green with a tick
  ("still a full sentence") for a non-defining clause, red with a cross ("we
  lose who or what we mean") for a defining one; the clause fades.
- `link`, `dangling`: an arc over the words from the main clause's subject
  (a `subject` part in an independent piece) to the participle (in the
  dependent piece): whole, with a head, when they share the subject; broken
  with a red cross when they do not (a dangling participle, shown only on a
  sentence the board marks as wrong).

Nothing moves a word: the set-in clause is styled in place (colour, outline,
absolute pins), the removal line's room is reserved from the start, and the
arcs are drawn in the overlay like arrow marks, measured from the words on
every render. The model's reply is unchanged in shape: items are still strings
("nondefining|who is a 19-year-old woman", "remove", "link|complaining").

Code: `write_screens.py` (prompt, `clause_items`, `clause_edges`,
`without_clause`, audit, height, html, CSS), `write_narration.py` and
`qa_narration.py` (the parts as the models see them), `build_lesson_player.py`
(format 1.9), `board_player_template.html` (the arcs, the motions).

## Consequences

- Bundle 1.9: the part kinds above, `keeps` on a removal and `from` on a link;
  rule 24. A 1.8 reader shows the block's `html` with `blocks.css`: the set-in
  clause, its edges and the removal line appear by rule 5, but no arc is drawn.
- Lessons 1-5 are unaffected: every section's screens re-render byte-identical
  with the new code (checked 2026-09-27, files restored), and their bundles stay
  at their format until rebuilt.
- The arc is the renderer's, like an arrow mark: the website must draw it from
  the two phrases' positions, as it does for arrows.
- A later lesson on reported speech or conditionals can use the subject link
  and the set-in piece as they are.
