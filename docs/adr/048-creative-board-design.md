# 048 — Creative board design: every board laid out for what it teaches, with design skills and a critique before voicing

Date: 2026-11-01
Status: **Accepted**: the owner's brief of 2026-11-01 ("Install design skills for the lesson engine, make board
design a creative step"), given in chat with its rules; the engine mechanics (decisions 7 and 8) are the agent's
under that brief (ADR 005).

## Context

- Style C (ADR 042 and its amendment (2)) gave the lessons one look: the ground, white cards, colour by meaning,
  the marker, the lift and the zoom. Its board layouts (docs/02-DESIGN-SYSTEM.md §7j; runbook step 11b) were meant to
  carry "the imagination of the owner's own decks" over, "a visual in place of a plain table wherever the content
  allows". In practice the step became a fill-in: a session looks at the slide, picks the nearest of fifteen named
  layouts for the table, and leaves everything else as a table under a dark header with notes beneath. The owner's
  review of the Writing drafts (2026-11-01): the graphic design is simple, repetitive and tiring, and worse with
  each lesson. Word Order (writing-06-word-order, draft.1) has sixteen boards; eleven are tables under a header, four
  of them the same two-column table, and three boards end with a third of the frame empty.
- His own slides do better with less: the ISBAR slide of Writing 7's deck (page 7) gives each letter of the
  initialism its own tall coloured column with its word beside it and its questions in a row; his "Request" slide
  (page 8) shows two letter skeletons side by side, the purpose words in green, the body as dashed lines. Each
  slide is drawn for the one thing it teaches.
- Claude Code loads skills from a project's `.claude/skills/`. Published design skills exist that encode what the
  sessions lack: a structural-variety discipline and an anti-slop test (Hallmark), a scored critique with evidence
  (the `critique` template of nexu-io/open-design), the animation decision framework of Emil Kowalski
  (`emil-design-eng`, and `design-motion-principles` for three designers' perspectives), a searchable local set of
  styles, palettes, type pairings and UX rules (`ui-ux-pro-max`, with its `slides` sub-skill), and Vercel's Web
  Interface Guidelines. Anthropic's `frontend-design` skill is already available in every session.

## Options considered

- **Leave step 11b as it is and ask for more layouts per lesson.** Rejected: the step is the problem. A choice
  from a fixed list, made table by table after the content is set, cannot produce a board designed for its point.
- **Hand the boards to a design model (an image model, or a second drafting pass by a model given the deck).**
  Rejected: a picture of a board is not a board (no ids, no cues, no fit, no phone); a second model pass costs
  money per section and still designs from a list.
- **Make the layout a design decision of the session, taken with design skills, checked by a critique, and
  recorded** (chosen). The engine already separates words from presentation (§7j, "presentation only"); what
  changes is who decides the form, with what knowledge, and what proves it before the lesson is voiced.

## Decision

1. **The skills** are installed at project level, `.claude/skills/`, pinned to upstream commits recorded in
   `.claude/skills/README.md` (source, commit, licence, and every line the repository changed), so every lesson
   session has them:

   | Skill | From | Use in a lesson session |
   |---|---|---|
   | `frontend-design` | Anthropic (built in) | the design pass: aesthetic direction, typography, "not a template" |
   | `hallmark` | nexu-io/open-design | structural variety, the slop test, the pre-emit self-critique, anti-patterns |
   | `critique` ("Design Critique") | nexu-io/open-design | the five-dimension scored review of the contact sheet (decision 6) |
   | `emil-design-eng` ("Design Engineering") | nexu-io/open-design (from emilkowalski/skills) | should it animate, easing, the invisible details |
   | `design-motion-principles` | kylezantos | the motion audit of reveals, lifts, zooms and typing |
   | `ui-ux-pro-max`, `slides` | nextlevelbuilder | the local search of UX rules, type and colour reasoning; slide layout patterns as reading |
   | `web-design-guidelines` | vercel-labs/agent-skills | a review of the player's markup against the vendored Web Interface Guidelines |

   **When**: at step 11b, before any board is laid out, the session loads `frontend-design`, `hallmark`,
   `ui-ux-pro-max` and `emil-design-eng` and reads Hallmark's `references/structure.md`, `slop-test.md` and
   `anti-patterns.md`; before the contact sheet it loads `critique` and `design-motion-principles`. **How far**:
   their judgement, never their defaults. A skill's page templates, themes, fonts, colour catalogues, hero and
   landing structures, chart libraries and generated files (`design.md`, `.hallmark/`, `design-system/`, a
   persisted master file) are not used; nothing of theirs is written into the repository or a lesson folder except
   the contact sheet and the critique of decision 6. Style C's tokens are locked (decision 2). The skills call no
   network (the Vercel rules are vendored; Hallmark's `study <URL>` verb is not used) and run nothing on install.

2. **Style C stays the base.** The look of ADR 042 as amended by the owner's review of 2026-10-26 (amendment (2)):
   the ground and the white cards, the handouts' colours by meaning and the six criteria's, the marker behind the
   words, the no-outline lift, the zoom, the motion of §8g. Nothing in this record changes a colour, a font, a
   size floor, an effect or the bundle format. **What changes is the layout of each board**: it is a creative design
   decision of the session, taken for that board, not a template filled in.

3. **Every board is designed for what it teaches.** Before a board's blocks are written the session names the one
   thing the board teaches and chooses the form that shows it: a flow (steps, a chevron down a letter's parts), a
   before/after (the wrong form beside the right one, the change marked), a letter skeleton with its parts in colour
   (the owner's Request slide), a column of coloured initials with their words (his ISBAR slide), a timeline, a paper
   excerpt with marks (ADR 045), a diagram (the clause diagram, a sentence drawn as pieces), a comparison, an
   illustration that carries the point (a scene the sentence describes, drawn in the approved style, ADR 015), or a
   form of its own that the engine's blocks and layouts can draw. **A plain table or a plain text block is allowed
   only when nothing else teaches the point better**, and the reason is logged in `analysis/decisions.md` beside the
   board. A table that is the right form is still drawn as the handouts draw one (§1a).

4. **Variety is a rule, not a hope.** No two boards in a row share the same layout. Across a lesson the range is
   wide: the contact sheet (decision 6) shows every board side by side, and a lesson whose boards read as one form
   repeated fails its own critique. The title and contents boards and the closing board count as boards.

5. **The owner's slides are the starting point, matched or bettered.** For each board the session still looks at
   the matching slide of the lesson's own deck (step 11b), but now for its visual idea, which it carries over in
   style C and improves where it can; where the deck has only text, it designs from the content. His ISBAR slide and
   his Request slide are the reference for what "designed" means: one strong visual idea per board, colour that
   means something, the structure visible before a word is read. Never the deck's decoration or any official OET
   content (methodology §18).

6. **A contact sheet and a critique before voicing.** Before the narration is synthesised (step 15), and for a lesson
   redesigned after voicing before its player is packaged, the session renders every board at its fullest state, in
   order, as one contact sheet (`analysis/design/contact-sheet.png`, laptop frame, numbered), runs the `critique` skill
   on it (the five dimensions, each scored with evidence that names boards; Keep, Fix, Quick wins), fixes what it
   finds, re-renders the sheet, and keeps the final sheet and the critique (`analysis/design/critique.md`, the scores
   before and after) in the lesson's analysis folder. The build report links both. A critique whose Hierarchy or
   Innovation score is under 5 is not a pass: the boards are redesigned, not the score argued.

7. **The rules that hold stay.** Dense content stays on one board (ADR 011, ADR 042 decision 3, the declared splits
   of §2). Every board is readable on a phone: the fit and the small-phone frame (ADR 011, §8b), the player's guard.
   Nothing hides the paper: every piece of a paper is shown whole beside the part it feeds (ADR 045), never zoomed,
   never overlaid. A practice point's pop-up is never covered and covers nothing a learner must read while it is open
   (ADR 046). No decorative icon anywhere: every graphic, picture and mark helps understanding, or it is not on the
   board (ADR 021 already asks a board's picture to be meaningful; a picture that only fills a corner is dropped from
   that board). Marks are drawn whole and never touch (§8); nothing about a board's state moves a word (§8a); no
   word of the narration says where something is (§8c). A layout is presentation only (§7j): it never changes a
   block's words, order, id, cue or state, so a redesign keeps a voiced lesson's narration and audio, and only its
   cues are re-timed to the new boards.

8. **How a new form reaches the engine.** A layout a lesson needs and the engine cannot draw is added to the shared
   style code (`style_c.py`: a row in `LAYOUTS`, its rules in `LAYOUT_CSS`, emitted only into the stylesheet of a
   lesson that uses it; an effect in the effects builder where motion is part of the form), with its row in
   docs/02-DESIGN-SYSTEM.md §7j, in its own small pull request, proven by the render comparison of every built lesson
   before and after (runbook, "Changing shared code"). A lesson picks it in `sections.json` `block_layouts` as any
   layout. The site plays it with no change of its own (the lesson's stylesheet); a form that needs the site's player
   is a bundle change and a new ADR amendment, not a layout.

## Consequences

- docs/03-RUNBOOK.md step 11b is the design step: load the skills, design each board for its point, no two in a row
  alike, log every plain table, make the contact sheet and run the critique before step 15. docs/01-METHODOLOGY.md
  §18 and docs/02-DESIGN-SYSTEM.md §7j point here.
- **This record changes no built lesson by itself**: it adds skills and documents. Proven by the render comparison
  of every built lesson before and after the change (`render_compare.py` snapshots `before-adr048` on origin/main at
  cabce5c and `after-adr048` on this change, 2026-11-01): **28 of 28 identical**, 838 data files byte for byte
  (bundles, texts, stylesheets, timelines, fits) and 174,846 moments at the phone and laptop frames drawn identically,
  with no board timing difference (Writing 5, being built in another session, has no player yet).
- Word Order (writing-06-word-order) is the first lesson redesigned under this record, in one run after it: every
  board, the narration and its audio unchanged, the cues re-timed, its practice points with their IDs, a before/after
  contact sheet in `C:\OET\course\design-samples\`, and a new draft on the site (draft.2). The layouts it needs are
  decision 8's separate pull request. The Writing 5 and 7 drafts are redesigned when the owner has seen Word Order and
  decided.
- A session takes longer at step 11b (designing, the contact sheet, the critique and its fixes: an hour or two, no
  model cost; the critique is the session's own reading of the sheet). The skills add about 4 MB of text to the
  repository (`ui-ux-pro-max`'s data is 3.2 MB).
- Open, for the owner: whether the frame ground returns to the lilac of ADR 042 decision 2 (his brief of 2026-11-01
  names "lilac ground"; his review of 2026-10-26 set it white, amendment (2) decision 2). This record keeps white
  until he says.
- To reverse: a new ADR; remove `.claude/skills/` and the three pointers. No lesson built before it changes.
