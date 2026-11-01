# 050 — The teal look: the owner's Canva patterns as the base of every board

Date: 2026-11-01
Status: **Accepted**: the owner's brief of 2026-11-01 ("Rebuild the boards of Word Order as a full lesson in a new
visual style, as the trial for all lessons"), given in chat with its rules and his reference images; how each
pattern is carried by the engine is the agent's under that brief (ADR 005).

## Context

- ADR 048 made board layout a design step and kept **style C as the base** (its decision 2): the white ground, the
  handouts' colours by meaning, the marker, the lift and the zoom. The owner reviewed Word Order's draft.2, redesigned
  under it, and rejected the result as routine: the boards still read as tables and cards in one neutral look.
- He then drew the look he wants in Canva: twelve pattern slides (`C:\OET\course\design-samples\canva\patterns\`,
  exported from his deck "OET Writing Lesson Boards") and five Word Order slides (`...\canva\word-order\`, "OET Word
  Order"). He likes patterns 1 to 11 and rejects 12 (a single rule in a large box). In his words: a teal brand base
  (#0b6e6d) with soft warm accents (amber, coral, soft blue, lilac), light, airy and uncluttered; rounded shapes,
  circles and pills, soft corners, no sharp blocks and no hard offset shadows; the teacher's hand (a handwriting face
  for his notes, red-pen circles and underlines around mistakes, sticky notes); the parts of a sentence colour-coded,
  each with a small label; diagrams, arrows, timelines, flows, columns and comparisons instead of plain tables; no
  large photographs or background images; motion in reading order and in time with the narration.
- The engine already separates the words from their look (ADR 042: the look is the lesson's `blocks.css`; ADR 048
  decision 8: a form is a layout in `style_c.py`, its rules appended only where used). The site plays a lesson's
  stylesheet as it is, scoped to its player (its ADR-0023 §4), and keeps any `data-*` attribute, class and simple SVG
  path a block carries (its sanitiser). So a new look needs no bundle change, provided it adds nothing the site's
  player must do.

## Options considered

1. **Re-tune style C's tokens for everyone.** Rejected: it would change all 28 built lessons at once, and their
   boards were not designed for the patterns; the owner asked for a trial on one lesson first.
2. **A new bundle style ("d")** the site would have to know. Rejected: a contract change on both sides for what is
   only a stylesheet.
3. **A look over style C, named per lesson, and the patterns as layouts** (chosen): `lesson.look` "teal" in a
   lesson's `analysis/sections.json` appends the look's rules after style C's; the eleven patterns are layouts
   (`block_layouts`) whose rules are appended only to a lesson that uses them. The bundle's format does not
   change (`style` stays "c"); every lesson without the look is byte for byte as it was.

## Decision

1. **The teal look replaces "style C stays the base"** (ADR 048 decision 2) for every lesson built or redesigned from
   now on: such a lesson sets `lesson.look` to `"teal"` (`style_c.look_of`; refused in a lesson not in style C, or for
   a look that does not exist). Style C's engine stays under it: the spotlight, the lift, the zoom, the marks, the
   effects and the bundle. Its rules (`style_c.LOOK_CSS["teal"]`; docs/02-DESIGN-SYSTEM.md §1b):
   - **Colour**: teal `#0b6e6d` and its ink `#173d3c` on a warm white ground `#faf8f4`; the accents amber `#e2a72e`,
     coral `#e57063`, soft blue `#9ecfd8`, lilac `#b8a6d6`, each with a soft tint; "right" is teal, "wrong" coral and
     red; the six criteria keep their colours (ADR 042).
   - **The teacher's hand**: a note written while teaching (a working `plain` note) is set in his hand, Caveat, at 1.3
     times body size (its x-height matches IBM Plex's at body size, §3); his advice (a callout) on a yellow sticky note
     in his hand, tilted 0.6 degrees; his marks in red pen: a **circle** is his red ring, an **underline** and a
     **strike** his red line; the marker stays amber. The board's own sentences stay in print.
   - **Rounded and soft**: pills, circles, radii of 2.2 to 2.8% of the frame; only soft, low shadows.
   - **The contents board** is a path of numbered circles in turn's colours, joined by a teal line (pattern 10, set
     vertically).
   - **Motion** (§8g): a fixed block enters as its board opens; a pattern's pieces (rows, tiles, pills, steps) enter
     in reading order, 70 ms apart, each in 0.4 s; never under reduced motion, never in a measuring check. The
     narration's own reveals, typing and marks keep their times.
2. **The eleven patterns are layouts** (`style_c.LAYOUTS`, `ADR050_LAYOUTS`; docs/02-DESIGN-SYSTEM.md §7k), each
   parameterised by the table it draws (its columns, its rows, its header) and nothing else:

   | Pattern (the owner's slide) | Layout | Draws |
   |---|---|---|
   | 1 Wrong and right | `wrongright` | a table of two columns: the wrong sentence in plain ink, a curved red-pen arrow, the right one in bold teal |
   | 2 A colour-coded sentence with labels | `coded`, `opener` | the parts as coloured tiles, each under a pill of its label; or a sentence's kind, its opening phrase in a tile of that colour, then the rest |
   | 3 A timeline with rounded markers | `timeline` | each row a round marker in its colour on a teal line, its words and a handwritten note under it |
   | 4 Keep, shorten or leave out | `columns` | two to four rounded columns under solid pill heads, their cells soft pills of the same colour |
   | 5 A letter skeleton with labelled parts | `parts` | the letter one sheet with a teal edge, each part's name a pill in its colour joined to its paragraph; a part not written out as grey lines |
   | 6 Key tips as round badges | `badges` | each point a solid circle with a handwritten note under it; a recap's category cards as badges side by side |
   | 7 A paragraph on ruled paper, red pen, a sticky note | `ruled` | the lines on ruled paper with a red margin, in a learner's hand, their numbers in the margin (the narration's pen marks the errors, the callout is the sticky) |
   | 8 Before and after with word counts | `beforeafter` | two panels, coral and teal, each sentence with its word count in a circle (counted from its words) |
   | 9 A gap with choice pills | `choices` | short phrases as solid pills in turn's colours, under their labels or the bank's name in the hand |
   | 10 Numbered steps on a curved path | `path` | numbered circles alternately low and high on a teal curve (an empty drawing, never a word) |
   | 11 Two letters compared | `compare` | two things side by side, framed in teal and coral, each head (a comparison's words up to the first colon, or a column's label) a pill |

   As every layout (§7j): presentation only; the words, their order, the ids, cues and states never change
   (`layout_html` checks it); a counted number, a label drawn from a header, a step's number and the curve are drawn by
   the stylesheet from attributes, never words.
3. **Variety is the rule** (ADR 048 decision 4, kept and made concrete): every lesson uses a varied mix of the
   patterns; no two boards in a row share a pattern (the title, contents and closing boards count); a pattern may
   vary its arrangement between lessons (the path set vertically on a contents board, the columns two or three wide,
   the badges in a row or as recap cards). Each board's pattern is logged in the lesson's decision log with the slide
   it follows, and the contact sheet and critique of ADR 048 decision 6 check it.
4. **What stays**: dense content on one board (ADR 011); a phone can read every board (the fit, the small phone frame,
   the guard, §8b); the paper is never hidden and keeps its forms (`paper`, `place`; ADR 045); a pop-up is never
   covered (ADR 046); no decoration: a small clean illustration only where it explains (ADR 021). The rejected pattern
   12 is not built.
5. **The hand on the site.** The reference player embeds Caveat from a pinned, hash-checked local copy
   (`spike/fonts/caveat.lock.json`), as it does IBM Plex Sans. The site's policy allows fonts only from itself
   (`font-src 'self'`), so a font in the lesson's stylesheet cannot load there; until the site serves Caveat (as it
   serves Plex, its ADR-0030) and names it `--font-hand`, its player draws the hand in the device's own (Segoe Print,
   Bradley Hand, then the cursive face). This is the one place the site's draft differs from the reference player.

## Consequences

- **No built lesson changes**: a lesson without `lesson.look` takes none of the look's rules, and a layout's rules
  reach only a lesson that uses it. Proven by the render comparison of every built lesson before and after the change
  (runbook, "Changing shared code"; `render_compare.py` snapshots `before-adr050` and `before-adr050r` on main at
  7247039, `after-adr050` and `after-adr050r` on this change, 2026-11-01): **28 of 28 identical**, 850 data files byte
  for byte (bundles, texts, stylesheets, timelines, fits) and 167,252 moments at the phone and laptop frames drawn
  identically, with no board timing difference. Reading 5 is outside the proof, as it was for ADR 049: it does not
  render on main (its closing audit fails because Writing 5 and 7 share its goodbye "Well done.").
- Word Order (writing-06-word-order) is the trial: every board redesigned with the patterns, its narration, audio and
  practice points unchanged, a side-by-side PNG of each board with the pattern it follows in
  `C:\OET\course\design-samples\word-order-v2\`, and a new draft on the site. The other lessons move to the look when
  the owner has seen it.
- **Not done here, for the owner**: (a) the pen circle is drawn whole at its time, not drawn on in motion: a mark is
  redrawn by both players on every frame, so a drawing-on needs a change to each player's mark code (rule 53, the
  marker sweep's way) and to the site; (b) the site does not serve the hand yet (decision 5); (c) the display face
  of his slides (a wide geometric sans) is not used: titles stay in IBM Plex Sans, the site's face (the owner
  agreed, 2026-11-01).
- **Asked of the site** (2026-11-01, label from-lesson-engine): siamingit/oetacademy-web#227, serve Caveat as
  `--font-hand` (a font is not a media type the package contract allows, and `font-src 'self'` refuses a `data:`
  font); siamingit/oetacademy-web#228, draw a circle on in motion in a lesson whose `lesson.look` is "teal" (0.4 s
  from the mark's time, rule 53's way), with the data the engine would send.
- To reverse: remove `lesson.look` from a lesson (its stylesheet returns to style C's); remove the look and the
  layouts from `style_c.py`. No lesson built before this record changes either way.
