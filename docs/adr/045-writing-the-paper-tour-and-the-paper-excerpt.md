# 045 — Writing: a guided look at the paper, and the paper beside the letter (layout `paper`)

Date: 2026-10-27
Status: **Accepted**: the owner's decision of 2026-10-27 after his review of Writing 3 (writing-03-letter-structure),
approved in chat in two steps and passed on in the chat's brief. The design (how the decision is drawn, decisions
3 to 6 below) is the agent's under that brief (ADR 005), for the owner's final gate. It adds a layout to
[ADR 042](042-style-c-and-motion.md) amendment (2) and docs/02-DESIGN-SYSTEM.md §7j.

## Context

- Writing 3's board "The parts of a letter" mapped the paper to the letter as a list of labels ("At the top",
  "The Writing Task", "The patient details", "The case notes", "The discharge plan"). The owner: "This style is
  not good: the learner has not seen the Writing paper at all yet. It will be hard to design, but it must be
  done."
- The same runs through the lesson: the date, the address, the Re line, the body and the request all come from
  the paper, so the learner must see the paper wherever a board refers to it.
- In class the owner taught with the paper in front of the learners (Session 1, its walk through the paper,
  the lesson Overview's page 8; Session 2 15:52, read the task first).

## Options considered

- **A layout already in §7j.** `change` draws a note, an arrow and its letter form, but not as a paper; `notes`
  draws case notes as a card with a dot a line, not with the paper's labels in their own column; `letter` is the
  letter. None draws the exam paper as the learner meets it, and none can keep a piece of it beside the letter
  in one look. Rejected: a new layout.
- **The whole paper on one board**, shown whole (map-sized) and read with the zoom: one board, but the paper is
  not readable at a glance and the zoom shows one line at a time. Rejected for paging (the owner: "page through
  it in parts, or use zooms").
- **Paging the paper** by its own parts, each part near body size (chosen).
- **The map board in two pages** (the top of the letter, the body): tried; the engine keeps a table of five rows
  on one board (a split must be oversized fixed content, judged before the table is fitted). Kept one board.

## Decision

1. **A guided look at the paper, once, before the letter** (the owner). An authored section (ADR 018),
   "The Writing paper", placed before the first section that refers to the paper: the main sample's whole paper,
   in its order, at a readable size, its layout kept recognisable; walked through part by part in the teacher's
   voice (the date line, the setting, the patient details, the case notes and their sections, the discharge plan,
   the Writing Task box at the end), each part lit (the row spotlight) as it is named. Where the whole paper does
   not fit the frame, it is paged by its own parts: declared splits of oversized fixed content (§2), as many as
   its size needs and no more (Writing 3: seven).
2. **The paper beside the letter** (the owner), in one fixed look, on every board that draws on a paper: the
   matching piece of the paper (the main sample's, or the other samples' where those are used) beside the part of
   the letter it feeds, paired in time with the narration (the spotlight lights the pair; where the letter's part
   is typed, it is typed as the narration names it). Real text, read from the sample's `paper.md`, never retyped.
3. **The layout `paper`** (docs/02-DESIGN-SYSTEM.md §7j) draws both, one look:
   - of two columns (the paper's label, its lines): **a sheet of the paper**, white, a hairline edge, a soft
     shadow, a rule between its parts; the labels bold in their own column, as the paper sets them; the date line
     ("Assume that today's date is …") bold, as on the paper; the Writing Task box grey. Used for the tour, and
     for a piece of the paper written while teaching (a table in the working layer);
   - of three columns (the paper's label, its lines, the letter): **each row a piece of that sheet, an arrow, and
     the part of the letter it feeds**, on the letter's cream. A row whose letter cell is empty is a piece of the
     paper alone (a line that names the letter, above the points it lists).
   - A line from inside a section carries its section's label, as the tour showed it. A heading over its first
     label ("PATIENT DETAILS:" over "Name:") sets the lines beside the labels they belong to. The label column is
     as wide as its longest label (a label is one line beside its line); a heading alone on its row may wrap.
4. **No zoom on the paper beside the letter.** The style C zoom (ADR 042 decision 4) onto one cell would take the
   piece of the paper or the part of the letter out of view; the two are shown to be seen together. A sheet is
   zoomed as any document of a Writing lesson.
5. **Nothing is named that is not on screen.** The learner never hears the name of a part of the paper that is
   not on screen, and no part of a letter is pointed to before it is shown: a board that names one shows it (a
   sheet in its working layer, or the paper beside the letter), or its narration does not name it. Checked board
   by board in each Writing lesson that uses a paper, and logged with its mm:ss.
6. **Presentation only.** The layout is classes and attributes on the table's html (`lay lay-paper`,
   `data-paper`, `data-today`, `data-task`, `data-solo`, `data-skip`, an empty `::before` as tall as a line); no
   word, order, id, cue or state changes (checked by `style_c.layout_html`). Its rules are appended to the
   stylesheet of a lesson that uses it only (`style_c.LAYOUT_CSS["paper"]`), as ADR 043 amendment (3)'s, so no
   other lesson's stylesheet, bundle or player changes. The bundle format is unchanged (the beside form only has
   no zoom effect). The site plays it with no change of its own (the lesson's own stylesheet).

## Consequences

- docs/02-DESIGN-SYSTEM.md §7j: the layout's row and "The paper"; docs/03-RUNBOOK.md step 11b names it and the
  guided look.
- Every later Writing lesson (Writing 4 onwards) quotes the paper the same way: the layout `paper`, real text, a
  guided look where the lesson is the first to use a paper the learner has not seen.
- Proof (the standing rule, ADR 043): `render_compare.py` on every built lesson before and after the change, every
  one identical; `restyle_proof.py` on every published lesson, nothing changed.
- Known limit, for the owner: a board whose pairs take many lines (Writing 3's map board, five pairs, one of them
  the address) is set small by the fit, since a table is made smaller before the board's picture is (§7e, §8b);
  with the zoom off there, it is small on a phone. Two pages would need the split rule to judge a table after it
  is fitted (an engine change for every lesson), or fewer pairs on the board.
- Not now (the owner): a "see the whole paper" button; it would need the site.
- To reverse: a new ADR.

## Amendment (1), 2026-10-28: the paper beside the letter, readable on a phone

Context: at the owner's final listen of Writing 3 the map board's five pairs were set at 2.0% of the frame
(readable on a laptop, too small on a phone; the known limit above). The owner approved the lesson and asked
for a look-only fix, approved by the chat on his behalf (ADR 005, ADR 043): readable at the phone frames, no
spoken word changed. Two further findings while fixing it: the fit's order (decision kept: a table is made
smaller before the board's picture) was not the limit, the table's own height was; and at the phone frames,
where a table's text is under 14 px, rule 13's camera zoomed onto the active cell of the paper beside the letter
and took the letter out of view (decision 4 held for the style C zoom only).

Decision:
1. **A table divided by its rows.** A declared split (§2) whose every part's fixed layer is one table and
   nothing else is judged at the size a table is read at, body size (as `fit_table` first sets it), not by its
   count of rows; a table that cannot be read whole at that size keeps its parts, each shown whole, the
   audit's limits unchanged (as many parts as its size needs). Every other split is measured as before
   (`write_screens.table_rows_split`). No built lesson had a split of that kind merged, so none changes.
2. **The paper beside the letter is a board shown whole.** Each board whose table is the paper beside the
   letter is named in the lesson's `boards_fit` as `"whole"` (rule 52, bundle 1.21): never zoomed or panned on
   any device, by the reference player and the site alike. Decision 4 now holds on every frame.
3. Writing 3: the map board in two pages (pairs 1-3, then 4-5), its type 3.0% and 3.2% at every frame (was
   2.0%); the six boards of the paper beside the letter shown whole. No spoken word changed.

Proof: render_compare before and after on every built lesson; restyle_proof on every published lesson.
