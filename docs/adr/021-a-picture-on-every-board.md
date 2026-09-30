# 021 — A picture on every board

Date: 2026-09-30
Status: **Accepted** (the rule) by the maintainer in chat, 2026-09-30: "every
board has at least one relevant generated image in the approved style (e.g. the
patient in the case notes, a clinic scene, or a picture of the concept).
Meaningful, never decorative; never over text. Apply it to these four lessons."
How it is carried below was chosen by the agent under that request; the
maintainer may reverse it.

## Context

Generated illustrations were used only inside glosses (ADR 015), for concrete
hard words. Most boards had no picture at all: a table of case notes, a set of
exercise sentences, a rule. The maintainer asked for a picture on every board,
in the approved style, that means something on that board.

## Options considered

1. **The screens model writes a picture block per topic.** A change to the
   model's reply schema (at its size limit), and the model would have to guess
   what is worth drawing on every board.
2. **A picture in the fixed layer.** It takes room from every state, and the
   boards are already full: most vocabulary boards were near the content band.
3. **The agent writes one brief per board; the picture opens the board** (this
   decision): the first note of the board's first state, shown from the state's
   start with no cue, erased like any note.

## Decision

- **The step**: after the screens, the agent writes `analysis/pictures.json`,
  one brief per board, "alt text | what to draw", from the board's content: the
  patient of its case notes, the scene, or the concept. The runner stops at
  the images stage until the file exists (docs/03-RUNBOOK.md step 10b).
- **The block**: code adds a block of type `picture` (`icon` the brief; no
  words; role note) as the board's first note, with an id after the section's
  last; in a narrated section it joins the kept plan's first state, so no
  other id, state or utterance changes. `gloss_images.py` draws it in the
  approved style (ADR 015, docs/02-DESIGN-SYSTEM.md §7b), cached by the brief;
  the exercise items of one exercise share one picture.
- **Shown**: from the first state's start until that state is erased, or until
  the fit clears it because a later note needs its room (ADR 011). Drawn in
  the board's flow, a square 20% of the frame's height, made smaller by the
  fit, to no less than 10%, where the board does not fit with it (its size is
  kept for the whole board: fit.json `pics`, the bundle's `size`); on a table board at
  the right under the table, the side notes to its left. Never over text
  (ADR 020). The narration never points at it; the narration model is not
  shown it.
- **Bundle 1.12**: the block type `picture` and rule 27.

## Consequences

- About one image per board, $0.08-0.10 each; exercise items share theirs.
- Every board opens with a picture while its topic is introduced; on a dense
  board it gives way to the notes, as a teacher's board fills.
- A lesson built before this rule has no pictures until its `pictures.json` is
  written and it is rebuilt (screens only; no audio changes).
