# ADR 054 — The owner's review of Speaking 1: one entrance per board, the contents line, and speaking points as the site releases them

Date: 2026-11-12 (the owner's review of Speaking 1, 2026-11-12, points 2, 3, 4 and 7)

Status: Accepted. It amends ADR 053 (a Speaking lesson may now go to the site as a **draft**: its speak_repeat
points, and its matching point; never its speak_respond or roleplay items) and ADR 050 (the teal contents board).

## Context

The owner reviewed Speaking 1 on 2026-11-12. Four points need shared code:

- **Point 2, the flicker.** "From board 3 on" the entrance motion played again in the middle of the narration:
  the board "disappears for a moment and comes back". The local player rebuilds a block whenever a later state
  marks or erases something in it. A rebuilt teal table started its row-by-row entrance again. The site's player
  fills a block once per board, so it never did this. The owner: the entrance plays once, and later states only add
  or mark things.
- **Point 3, the contents board.** The owner asked for "one clean continuous line with all items aligned". The two
  columns share each row's height. An item beside a taller one was stretched, so its circle sat lower than the
  others and the line was drawn in two pieces around it. The item the teacher is on (`fx-lift`) moved as a whole,
  so its circle left the line.
- **Point 4, the five skills.** As each skill is explained, an example line appears on the right in a
  handwriting style. Then comes a matching practice point: five skills and five new sentences. The owner: "use the
  session practice type for matching if the pinned contracts have one; otherwise the closest released type, and
  say so in the report".
- **Point 7, the speaking points on the site.** The owner: pin contracts 1.22.0 and map every speak_repeat point to
  the released item: no pass_score and no profession; no digits in `spoken`; `shown` reads word for word as
  spoken; chunks follow the rule. The slow audio is a real slower take at about 0.75 speed, made by a
  pitch-preserving time-stretch that passes the ear check. speak_respond and roleplay stay in the lesson source and
  go in no package. The local pop-up is honest: it marks nothing. Point 8 then asks for a **draft** of Speaking 1
  on the site.

## Options

1. **Flicker.**
   - (a) Stop rebuilding blocks in the local player. This is a large change to the state engine, and every built
     lesson depends on it.
   - (b) Remember that a block has entered (`data-entered`). When a later state rebuilds it, mark it `entered`, and
     turn the entrance animation off for an entered block. (Chosen.)
2. **Contents.**
   - (a) Fixed item heights. The text would overflow on long titles.
   - (b) Align every item to the top, raise each circle onto its title's first line, set the first row lower by the
     same amount, and draw one line piece from each circle to the next. (Chosen.) A margin made each item 18 px
     taller, so Speaking 2's seven items no longer fitted and the runtime guard cleared three of them. Moving the
     words down instead ran them past the item's box; the site's guard counted that as a spill and drew Speaking 1's
     whole board smaller, in one column.
3. **Matching.**
   - (a) Wait for a speaking matching type. Contracts 1.22.0 has none.
   - (b) Use the released `matching` item (matchingItem, ADR-0032 on the site). (Chosen.)
4. **The slow take.** Measured in C:/OET/scratch/speaking-build/slow-compare/CHOICE.md:
   - (a) Cartesia's own slow speed: 1.00-1.07 times as long, so not slower.
   - (b) ffmpeg `atempo=0.75`: 1.325-1.328 times as long.
   - (c) ffmpeg `rubberband=tempo=0.75`, which keeps the pitch: exactly 1.333 times as long. (Chosen.) It passed
     the ear check: Scribe heard every slow take word for word, apart from "Doctor" written as "Dr.".

## Decision

1. **One entrance per board** (board_player_template.html). Every block is marked `data-entered` the first time
   it is drawn (in every lesson; the mark draws nothing by itself). When a later state, an erase or a clear rebuilds it, it gets the class `entered`, and
   `.frame .blk.entered.tbl.lay tbody tr, .frame .blk.entered.tbl.lay td {animation: none}`. The entrance plays
   once per board. Later states only add or mark things.
2. **The contents line** (style_c.py, for a contents board with six items or more):
   - every item is aligned to the top;
   - each circle is raised onto its title's first line (a negative top margin), and the first row is set lower by
     the same amount, so no item gets taller and no item's words run past its box;
   - the line runs unbroken from each circle's centre to the next, each piece inside its own item (`::after` from the
     circle to the item's foot, the next item's `::before` from its top to its circle);
   - with seven or eight items, a column of four pays for the lower first row with shorter items (at least 16.5cqh
     high, not 17.5cqh) and 1cqh below each item, not 2.5cqh. Without this, Speaking 2's seven items were 4 px taller
     than the small phone's board (590 px), and the fit cleared the first three;
   - `fx-lift` moves the item's words only (`.citem.fx-lift > div`), so its circle stays on the line; with reduced
     motion it moves nothing.
3. **Hand-written example lines** (style_c.py, `LAYOUT_CSS["opener_typed"]`). An opener table whose third column
   is typed live draws those lines in the teacher's hand (`--t-hand`), at 1.31em with a line height of 1 (26 px at 1600 px, the readability floor for the hand), and
   such a table's rows are 1cqh apart. At 1.34em, five rows of two hand-written lines and the task under them were
   taller than the board, and both players panned it, hiding the first skill under the title. Now it fits with no
   pan. This CSS is added only for a lesson with such a table, so no other lesson's blocks.css changes.
4. **Matching in a Speaking lesson** uses the released `matching` type (practice_points.py: 2-8 pairs, 3-9
   options, `display_order` a permutation of the options). The local player gets a matching pop-up (ppMatching)
   that marks each pair right or wrong with its feedback. This stays until the contracts add a speaking type for
   matching.
5. **Contracts 1.22.0 are pinned** (spike/publish/contracts.lock.json). A speak_repeat goes in a package in the
   released shape (speaking_items.release_item):
   - no `pass_score` and no `profession` (the profession goes to `tags.facets.profession`);
   - `shown` is the spoken line word for word (the engine's RP-SHOWN);
   - no digits in `spoken` (RP-SPEAK-NUMBERS);
   - chunks follow RP-SPEAK-CHUNKS;
   - it is the only item of its point (LP-PRACTICE-ITEM). Points that held two or three lines are split; their
     unreleased IDs are retired in spike/practice/ids.json (`retired`, 2026-11-12), never reused.

   Each speak_repeat point has an authored excerpt, because 1.22.0 requires one on every point. A Speaking lesson's
   sections carry their Speaking keys from the tags file, like any other lesson; no rule is waived. The pinned
   session section tag list has no Speaking keys yet (the site's ADR-0034 Amendment 17: "Speaking stays off the
   list"), so its package fails LP-TEACHES-NOT-ALLOWED, here and on the site, until the owner approves the
   Speaking keys for the site's list. A closing section takes the lesson's main topic, as the Writing closings do.
6. **The slow take** is the normal take through `rubberband=tempo=0.75` (synthesize_speaking.py, `SLOW_SPEED`).
   It costs no Cartesia characters and is made again only when the normal take changes.
7. **The honest pop-up.** The local page cannot hear the learner, so it marks nothing. It shows the task, the
   patient's line, Listen and Slowly. "I said it" or Skip shows the model answer, plainly, with a note that the
   site checks the answer. Continue is never blocked.
8. **A Speaking lesson may go to the site as a draft** (`publish_lesson.py --draft`, runbook 18a) once its
   package passes, that is once the site lists the Speaking keys (decision 5). Only its
   speak_repeat points and its matching point go in. speak_respond and roleplay items stay in the lesson source, are
   left out of the package, and are listed by the report. A release still waits for the owner's final gate.

## Consequences

- Every built lesson is rendered before and after (render_compare `sp-before` / `sp-after`). Decisions 1 and 2
  change what a teal lesson draws: entered rows no longer animate again, and the contents board is aligned. The
  comparison lists each lesson that differs, and the report names them. No built lesson is rebuilt or re-released
  by this ADR. Each takes the change only when it is next built, with the owner's approval.
- A note for the site: the engine's RP-SHOWN would refuse the contracts' own golden speak_repeat ("Take 2
  tablets" shown, "Take two" spoken).
- The slow take needs an ffmpeg with the `rubberband` filter. The owner's ffmpeg 9.0.1 (gyan.dev full build), which
  makes the releases, has it; synthesize_speaking.py stops with a clear message where it is missing.

To reverse:
- Decision 1: remove the `entered` class and its rule.
- Decision 2: remove the ADR 054 `#cam:has(> .blk.citem:nth-child(6))` rules (the aligned items, the raised circle,
  the lower first row, the one-piece line), and the seven-or-eight rule for shorter items, and restore `.citem.fx-lift`'s transform.
- Decision 3: remove `opener_typed`.
- Decisions 5-8: pin 1.20.0 again, and refuse speaking lessons in publish_lesson.py as ADR 053 did.
