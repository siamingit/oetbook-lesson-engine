# 043 — The 22 published lessons move to style C: phase 1, the general look

Date: 2026-10-27
Status: **Accepted**: the owner's decision of 2026-10-26, given in chat and passed in the brief "Restyle
the 22 published lessons in style C, phase 1 (the general look)". It **supersedes the part of
[ADR 042](042-style-c-and-motion.md) that keeps the 22 published lessons in their earlier look** (decision
1's "the 22 published lessons have none, and their `blocks.css`, bundles and players stay byte for byte as
they are", and the consequence "Restyling the 22 published lessons is the owner's later decision"). How it
is carried, and the rule changes below, were decided by the agent under that brief (ADR 005); the owner may
reverse any of them.

## Context

- ADR 042 made style C the look of Writing 2 and of every lesson after it, and left the 22 published
  lessons (Grammar 1–8, Vocabulary 1–3, Writing 1, Reading 1–5, Listening 1–5) in their look, as the
  owner's later decision.
- On 2026-10-26 the owner decided: all 22 move to style C, in two phases. **Phase 1**, the general look,
  for all 22 at once: `lesson.style` "c", the colours, the white ground, the marker, the lift, the motion
  effects (design system §8g) and the contents on one board, as ADR 042 and its amendment (2) give them.
  **Phase 2**, the creative per-board layouts of runbook step 11b (`block_layouts`, each board beside the
  matching slide of the owner's deck, design system §7j), lesson by lesson in later sessions, Grammar and
  Vocabulary first, Reading and Listening last.
- Grammar and Vocabulary are live as package version 3, with the 72 errata corrections of issue #43; each
  lesson folder holds that state (its `text.json` is byte for byte the released v3 package's).
- The restyled lessons are bundle format 1.22, which the site accepts only once oetacademy-web issue #173
  is done and the engine pins contracts that accept it (ADR 042, Consequences). The versions on the site
  stay as they are until then.

## Options considered

- **All 22 at once, or lesson by lesson.** At once for the look (one code change, one proof, one review);
  lesson by lesson for the layouts (phase 2), which need each deck looked at (the owner's order).
- **How to prove a restyle changed only the look.** The render comparison of "Changing shared code" proves
  a code change moves no lesson; it cannot prove a lesson that is meant to change changed only as allowed.
  A per-lesson proof that reads the lesson's data before and after (chosen: `restyle_proof.py`, below).
- **The approval.** The owner's final gate for each of 22 lessons (his time, for a change that alters no
  teaching); or the chat on his behalf, as for the errata (ADR 005 amendment of 2026-10-26) (chosen, his
  decision).

## Decision

1. **The 22 published lessons are restyled in style C, phase 1.** Each gets `lesson.style` "c"
   (`build_sections.py <L> --style c`) and is rebuilt by the free stages only: the title and contents
   boards, the fit (silent preview and player), the silent preview, the lesson player, the screens preview.
   No paid stage runs and no model is called. No `block_layouts` are set: they are phase 2.
2. **What a restyle may change, and nothing else**: `sections.json` `lesson.style`; the look
   (`blocks.css`, the players, the classes, attributes and elements style C adds to a block's html, which
   hold no new words); the bundle's `effects`, its `lesson.style` and its format (1.22); and the fit (a
   table's text size, a picture's size, a state's `clears`, a board's tightness). **Never**: narration text,
   audio files and their timing, cue times, board and state times, lesson, section, block and state ids,
   section titles, the order of sections and boards, any teaching content (the words on the boards and
   their order, glosses, images, practice items and their numbering); `source/` stays read-only.
3. **The proof**, for every restyled lesson: `spike/scripts/restyle_proof.py snapshot` before the restyle
   (the SHA-256 of every file of the lesson but its recording, and a copy of its data files), `compare`
   after it. It fails on any file changed that a restyle may not change, and reads the data in depth:
   `sections.json` only `lesson.style`; the bundle's and the timeline's every board, state, utterance, cue
   and block identical but for the effects, the format, the fit and the html's style C additions (the
   html's words compared exactly, the html compared with those additions taken away); `text.json` only its
   format version; `audio_index.json` identical; every screens and narration file identical (the
   introduction's screens only gain the lesson config's `style`); the decision log only appended to. Where
   a lesson's silent preview was older than its narration (docs/03-RUNBOOK.md, "Known items"), the restyled
   preview is compared with its re-render by the code before the change (the render comparison's "before"
   snapshot), since the restyle re-renders it from the current narration too. Tested in
   `spike/tests/test_restyle_proof.py`.
4. **The approval** (owner, 2026-10-26). A restyled version changes no teaching content, no section and no
   id, so its final approval is given by **the chat on the owner's behalf**, as for errata corrections (ADR
   005 amendment of 2026-10-26). When the chat approves after reading the agent's report, the agent records
   each lesson's final gate with `build_lesson.py <L> --approve final --by siavash` and writes in its
   `decisions.md` that the chat approved it on the owner's behalf under this ADR. As in the errata
   amendment, the approval it replaces is first kept in `analysis/gates.json` under
   `final_before_restyle_2026_10_27`, its `by` and `on` exactly as they were, with `superseded` and `why`.
   Until then the restyled version's final approval is pending. The section tags do not change, and their
   recorded approvals stand.

### Rule changes (decided by the agent under the brief; each logged in every lesson it touches)

5. **A contents item lists its category's sections one under the other** (changes ADR 042 decision 3's
   drawing, not its rule). The contents board's items are the deck's categories, each with its sections
   (`build_lesson_boards.py`; the board's "parts" ADR 042 counts are these items: 5, 2, 3, 3 and 3 in the
   five lessons whose narration names 13 to 17 sections). In style C each section of an item that lists
   two or more is wrapped in a `<span class="cp">` inside `<div class="cs parts">`; the words and the
   " · " between them stay exactly as they are (the separator is drawn at no size), and `blocks.css` sets
   the sections one under the other under the category's heading, in two columns of items, on one board,
   never cleared. Bundle 1.22's rule 53 lists `cp` and `parts` among the html a style C block may carry
   (amended, not raised: no 1.22 lesson is published).
6. **The last category stays lifted while its sections are named.** A contents item is lifted from its
   reveal until the next is named (ADR 042 decision 4); the last until the end of what is said with it,
   which now includes every later utterance with a mark on the item (its sections named one by one).
7. **The zoom is for the documents of a Writing lesson** (narrows ADR 042 decision 4 and design system
   §8g, "a document set well under body size"): `style_c.ZOOM_TYPES`, the letters and case notes the owner
   named. In every other lesson a table keeps rule 13's auto zoom, Grammar 6's board shown whole keeps the
   owner's "no camera zoom" (ADR 011 amendment of 2026-10-12), and a Reading or Listening text keeps its
   own lens, map, covering and transcript box (ADR 026, ADR 030): where a style C zoom and an existing
   Reading lens or zoom would act on the same moment, the Reading behaviour is kept, always. Writing 1's
   case notes and model letter (shown whole, ADR 041) take the zoom, as Writing 2's letter does.
8. **A document is a page on paper** (design system §1a, "the board's own sentences … a letter, case
   notes: paper"): a Reading text or a Listening transcript (`doc`) has its paragraphs on paper `#f8f4ec`
   with no rule between them (so a transcript's lines stay on their grid), and the paragraph being taught
   keeps the paper, shown by the spotlight and the lift. In style C a keyword pair's colour (`match1` to
   `match3`) is multiplied with what is under it, so on the soft amber of an active cell it would no longer
   be the colour of its other half on the question.
9. **Tense colours stay** (design system §5a, §7 Tables): a table's header cell in a tense family's colour
   keeps it in style C (Grammar 1's summary table: past, present, future).
10. **No word moves while a board is drawn** (§8a): in a table with no layout, typed text is set without
    kerning or ligatures, so the player's split into a typed and an untyped half adds up to the whole line
    (Grammar 3's layout check found a word that wrapped mid-typing in IBM Plex); a table with a layout
    (§7j) is checked with its layout (phase 2). The clause diagram's comma after a dependent clause has
    its weight 500 from the start, unseen, since IBM Plex's 500 face has its own line metrics (Grammar 7's
    lines dropped 1 px when the clauses were joined).
11. **A contents board with no picture** uses the whole board: the room for the picture is kept only when
    the board has one.
12. **A document keeps its page's measure** (§7g, §7h): style C adds no padding around a Reading text or
    a Listening transcript, nor to its title row, so its text takes no more lines than before and the
    question board's fit and guard keep the sizes they found (Reading 5's Part C board `t14` overflowed
    with Verdana at the small phone until this).
13. **A question board's column is narrow** (Reading Part B and C, Listening): its notes keep a small
    padding (1.1% of the frame's height, 1% of its width), and a word card there has no "Word" chip on a
    line of its own (the card's amber and its word say what it is; Listening 3's board `page-14_t2`
    overflowed at the small phone until this).
14. **A word longer than its narrow column** breaks inside its cell (`overflow-wrap: break-word`) rather
    than running out of the table; at the lesson's own font no word is that long (Reading 3's Synonym
    column with Verdana).
15. **The marks check** applies style C's marker rule (the band multiplied with the words, under 40% of
    the line) to the highlights drawn; a highlight whose phrase is not shown at that moment draws no band
    and covers nothing (82 of Reading 4's, the same before and after).

## Amendment — 2026-10-27 (2): the last contents item lifted; matching tables spotlit by cell

Status: **Accepted**: the chat's brief of 2026-10-27, after it read the report (issue #51) and accepted
phase 1 on the owner's behalf; the second fix is the owner's report of the same day. How each is carried
was decided by the agent under the brief (ADR 005).

16. **The last contents item is lifted while it is named** (the first item under "Found" below, now
    decided). Its lift ends at the end of the sentence whose cues hold its reveal (else, as before, the
    sentence its reveal falls in), plus the hold, and later marks on it as decision 6 says. Rebuilt:
    Grammar 1 and 2, Vocabulary 2, Writing 1, Reading 1 and 5, Listening 1 and 3, and Writing 2 (its
    "Closing"; the chat permitted it: no narration, audio, id, time or teaching content changes, and
    Writing 2 also takes the rules this ADR appended to style C's shared stylesheet). Writing 2 keeps its
    final approval of 2026-10-26; the rebuild is approved by the chat on the owner's behalf under this ADR.
17. **A table whose rows do not pair their cells is spotlit by cell** (rule 11, amended; bundle 1.22
    amended, not raised). The owner found on Reading Part C (2), board `pages-13-14-15_t1` at 6:01, that
    the spotlight lit the word's row (its wrong meaning beside it) and dimmed the right meaning its arrow
    reached: a teaching error, in the published 1.21 version too. The rule, for every lesson now and
    later: where the narration draws an arrow from a cell of a board's table to a cell of another row
    (detected from the bundle's own cues, `build_lesson_player.cross_arrows`), each `focus` entry lists
    the cells lit, `cells`: the word's cell, every cell its arrows have reached by then (from the arrow's
    time, never before) and the cell being read; every other cell is dimmed. Found in 39 boards of six
    lessons (Reading 3, 4 and 5, Listening 3, 4 and 5); no other kind of board marks a row the spotlight
    is not on. **The site's player must change**: it sets `cellspot` and `lit` from `cells`
    (docs/integration/1.22-changelog-for-site.md, "Amended 2026-10-27 (2)"); the look is in the lesson's
    `blocks.css`, appended only in a lesson that has such a table (`style_c.CELL_CSS`), so every other
    lesson's stylesheet is unchanged. `check_board_page.py` checks every `cells`.
18. **The proof** (`restyle_proof.py`) allows a focus entry's `cells`, and an entry repeating the row and
    cell before it, as the spotlight by cell, and a state's effects rewritten; everything else as before.
19. **Final approvals** (decision 4): recorded on 2026-10-27 for the 22 restyled lessons, after both
    fixes passed, by the chat on the owner's behalf.

## Found while carrying this, not decided here

- **The last contents item is often not lifted** (`style_c.effects`, ADR 042 decision 4). When an item's
  reveal falls in the half second after the previous sentence ends (its first word is said just before
  its sentence's recorded start), the code reads it as said with that sentence and lifts it for under
  0.8 s, which is dropped. Writing 2's "Closing" is one; so is the last item in most of the 22 lessons
  (decision 6 covers those whose sections are named after it). The fix (the end of the sentence whose cues
  hold the item's reveal) would change Writing 2, which this phase must leave as it is: for the owner or
  the chat, with Writing 2's next rebuild.
- **The site must be told** of the amendment of 1.22 (decision 5, the `cp` spans; the 22 lessons' new
  package versions): docs/integration/1.22-changelog-for-site.md is updated; the comment on oetacademy-web
  issue #173 is for the chat to send.

## Consequences

- The 22 lessons are bundle format 1.22. They are not packaged or published in this phase: their versions
  on the site stay as they are until oetacademy-web #173 is done and the engine pins contracts that accept
  1.22 (a new amendment of ADR 039); they are then published as new package versions, which the site holds
  for acceptance.
- Writing 2 is unchanged (the render comparison, below), and every rule above that would change it was
  scoped so it does not.
- The public course index records each lesson's bundle format; it is rebuilt (ADR 038).
- Phase 2 (`block_layouts`, lesson by lesson) follows in later sessions, with the same proof.
- To reverse for one lesson: remove `lesson.style` (and `style_by`) from its `sections.json` and rebuild
  its boards, fit, silent preview and player (free); it returns to its earlier look and format, byte for
  byte as the snapshot of this phase shows.

## Amendment — 2026-10-27 (3): phase 2, a trial on Grammar 4

Status: **Accepted**: the chat's brief of 2026-10-27, "Restyle phase 2, trial on one lesson: the creative
board layouts for grammar-04-articles", to be worked through on the agent's own decisions (ADR 005). The
owner looks at the result and decides whether the other 21 published lessons follow. Grammar 4's final
approval is not changed: the restyled version's approval is his.

20. **The proof allows the board layouts.** `restyle_proof.py compare` allows `sections.json`
    `block_layouts` (a map of block id to layout name) beside `lesson.style`, and nothing else new there;
    the bundle is read in depth as before (every block's words and their order, every id, time, cue and
    state), so a layout that moved a word still fails. Phase 2 compares against a snapshot taken just
    before the layouts are named.
21. **One new layout and two new forms** (design system §7j), from Grammar 4's slides: `pair`, a table of
    four columns that is two lists side by side, drawn as two tables with a gap (slide 6); a `fix` of two
    columns, the wrong sentence and the right one with no case note (slides 7 and 8); a `letter` of one
    column, a text with gaps, its greeting at the top (slide 15). Their rules are appended only to the
    stylesheet of a lesson that uses them (`style_c.LAYOUT_CSS`, as `CELL_CSS`), and each form is told by
    its columns (`:has`), so the html carries no new class or attribute, bundle 1.22 is unchanged (rule 53
    already names `lay-<layout>`) and the site has nothing to do. Every other lesson, Writing 2 included,
    is unchanged (the render comparison).
22. **Found, not changed**: in the shared stylesheet the last row of a `fix` of three columns has square
    bottom corners (`.tbl.lay tbody tr:last-child td:last-child` outranks the layout's own radius), in
    Writing 2 and in Grammar 4's "Specific nouns". Fixing it in the shared rules would change Writing 2,
    which this trial leaves as it is; the two-column form has the fix in its own rules. For the owner, with
    the next change that may touch Writing 2.

## Amendment — 2026-10-27 (4): phase 2 stops at Grammar 4; the 23 style C lessons are published

Status: **Accepted**: the owner's decisions of 2026-10-27, given in chat and passed in the brief "Pin the site's
contracts 1.12.0 (bundle format 1.22) and publish the 23 style C lessons". How each is carried was decided by the
agent under that brief (ADR 005). It **supersedes** this record's consequence "Phase 2 (`block_layouts`, lesson
by lesson) follows in later sessions" and the context's plan for phase 2 in the other lessons.

### Context

- The phase 2 trial on Grammar 4 (amendment (3); report issue #54) put board layouts on 6 of its 14 boards. It
  estimated about 14.75 hours of work for the other 21 lessons, plus about 45 minutes for each batch of new
  layouts.
- The site released contracts that accept bundle 1.22 (`contracts-v1.12.0`, pinned by ADR 039's amendment of
  2026-10-27), and its player plays 1.22 in production since 2026-10-27 18:30 UTC (oetacademy-web #173, closed).

### Decision (owner, 2026-10-27)

23. **Phase 2 is not done for the other 21 lessons.** The gain was too small for the time. They are published
    with their phase 1 look. Board layouts (runbook step 11b) stay the rule for lessons built in style C from
    now on (ADR 042 amendment (2), decision 5); only the restyle of the published lessons stops at phase 1.
24. **Grammar 4 keeps its phase 2 trial layouts.** They change no teaching content, no section and no id
    (`restyle_proof.py` passed), so the chat approves that version on the owner's behalf under this ADR
    (decision 4). Its final gate is recorded with `build_lesson.py <L> --approve final --by siavash`. The
    approval it replaces (siavash, 2026-10-27 09:37) is first kept unchanged in `gates.json` under
    `final_before_layouts_2026_10_27`, with `superseded` and `why`. Its `decisions.md` says that the chat
    approved the phase 2 trial version on the owner's behalf under this ADR, on 2026-10-27.
25. **All 23 style C lessons are published now**: Writing 2 as package version 1, and the 22 restyled lessons
    each as its next package version, at bundle 1.22. The site takes the 22 new versions live at once, each
    replacing the current version in its courses. Writing 2 goes live as a session in no course yet.

### How it is carried (agent, under the brief; ADR 005)

- **The section tags of Reading 1–5, Listening 1–5 and Writing 1.** Each of these 11 lessons is covered by its
  course's approval (Reading and Listening, siavash, 2026-10-23; Writing, siavash, 2026-10-26). Under ADR 039's
  amendment of 2026-10-26 (2), that approval covers only lessons whose final gate came on or before its date,
  and the restyle recorded their final gates again on 2026-10-27 (decision 4). Without a further step the
  release would refuse them. Their tags are unchanged: every section's `teaches` is exactly that of the
  lesson's released package. So each lesson's own tag approval was recorded with its final approval, as
  runbook step 18b says (`publish_lesson.py <L> --approve-tags --by "chat (owner's delegation)"`). The course
  approvals are not changed. Grammar, Vocabulary (approved per lesson with the errata of 2026-10-26) and
  Writing 2 (approved with its final gate) already had their own.
- **The zooms of Writing 1 and 2 against the site's player.** The site's player gives no zoom for a `zoom`
  whose `col` is null on a table as wide as the board (rule 55's 92% width limit; its last comment on #173).
  Every zoom of both lessons was measured in the reference player at three frames (40 entries). None has `col`
  null, and every phrase is found in its cell, so none zooms in the reference player but not on the site.
  Nothing was changed. In Writing 1, 5 of the 30 entries give no zoom in either player at any frame, because
  the side note shown with the line makes the view too wide or too tall for a scale of 1.03. One more zooms
  only at the phone frames, 1.03 at the phone, on the threshold. These are logged in the lesson's decision log
  for the owner; making them zoom would mean changing rule 55 or leaving a note out of the view.
- **Decision 22** (the square bottom corners of a three-column `fix`'s last row, in Writing 2 and Grammar 4) is
  published as it is; it stays for the next change that may touch Writing 2.

### Consequences

- The 23 lessons are released in `siamingit/oetacademy-sessions`, each with its release recorded in its
  `analysis/publish.json`. The course indexes are rebuilt.
- Grammar 4 is the only published lesson with board layouts.
- To reverse decision 23 or 25: a new amendment; the decisions are the owner's. To return Grammar 4 to its
  phase 1 look: `C:\OET\lessons\_restyle-review\phase2-trial\grammar-04-before\restore_phase1.sh`, its final
  gate recorded again, and a new package version.
