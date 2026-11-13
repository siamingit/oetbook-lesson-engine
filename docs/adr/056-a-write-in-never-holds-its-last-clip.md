# ADR 056 — A write-in never holds its last clip, and a lesson is checked as it plays

Date: 2026-11-13 (the owner's review of Speaking 2, 2026-11-13).

Status: Accepted. It fixes how the player draws the parts of docs/02-DESIGN-SYSTEM.md §7a (that section is not
changed: a part is still drawn in motion) and adds a check to runbook steps 13 and 17.

## Context

The owner, reviewing Speaking 2: "in the "Word" gloss cards the last words of the meaning are never written on
the board, although the narration says them. 5:09: "reassure = To help someone feel less" (the word "worried" is
missing). "shift = The hours you work on" (the words "one day" are missing)." The brief: "Find the cause. [...]
Fix it so that every gloss card shows its whole meaning and its example. [...] Compare the text drawn at the end
of each card's states with the gloss's source text, word for word, and list every card that was cut. Add this
comparison as a check so that it cannot happen again."

The cause is in the player's stylesheet, not in the card, the meaning or the typing. A gloss card's meaning
(`.gl-m`) and example (`.gl-x`) are drawn with a write-in:
`animation: write-in .4s ease-out both`, a `clip-path` from `inset(0 100% 0 0)` to `inset(0 0 0 0)`. Both parts
are inline spans. When such a span wraps onto a second line, Chromium resolves its `clip-path` against the
first line's box, so the clip that the fill mode `both` holds after the animation, `inset(0 0 0 0)`, hides every
later line. The part keeps the clip for as long as it is on and not `.settled`, and the player marks a part
settled only when it turns on after a seek or long after its cue: in playback, never. So a meaning or example of
two lines lost its second line for the whole of its state, on every frame width, while the narration read it.

Every check the engine had seeks to a moment (check_layout, check_overflow, check_overlap, check_lens,
check_wide_font, render_compare). A seek settles the part, the clip is dropped, and the whole text shows. That
is why no check and no render proof ever saw it.

The site's lesson player has the same rules (its `player.css`: the gloss parts and the other write-ins, with
`both`). The site puts the lesson's `blocks.css` in a cascade layer and its own `player.css` outside it, so only
an `!important` declaration in `blocks.css` overrides it.

## Options

1. **Make the gloss parts blocks.** A block's box is the whole paragraph, so its clip is too. It changes the
   cards' HTML and every layout that measures them; the other write-ins on inline parts would stay as they are.
2. **Fill `backwards`, not `both`.** The animation still starts clipped (backwards holds the first keyframe
   during the delay) and drops its clip when it ends. Nothing is held after the motion, so nothing can hide a
   line. One word per rule; the parts' HTML and boxes do not change.
3. **Time the settle.** Mark a part settled when its write-in ends. More code in the player's loop and the same
   fault for any frame drawn before the class is added.

## Decision

1. **Option 2**, for every write-in in the engine's player (`board_player_template.html`): the gloss meaning and
   example, the change pieces and the timeline labels. A write-in may clip a part while it is drawn, never after.
2. **The site's player.** A lesson whose blocks have one of these parts carries in its `blocks.css` one rule,
   `animation-fill-mode: backwards !important` on the same parts (`write_screens.write_in_css`), so that the
   site's player, which holds the clip as the engine's did, draws them whole too. A lesson without such a part
   carries nothing new. The proper fix is in the site's own `player.css` (the same one word); that is the owner's
   call, and the site is not changed from here.
3. **check_drawn_text.py** plays the lesson through, as a learner does, not by seeking: from 0 in steps of
   0.5 s, at the small phone, phone and laptop frames. At every state's end and just before every erase it
   finishes the running motions and asks the browser, word by word, whether each word a board shows is the
   topmost thing drawn at its place (each line box of a word that wraps; once with the camera and once without
   it, so a table the camera pans is not a false finding). A word under something else, or clipped, is a
   finding. A word outside the window, or scrolled out of a reading window or a transcript (check_lens covers
   those), is counted as not measured. Each gloss card's term, meaning and example, as drawn at the card's last
   moment, are compared word for word with the gloss's source text (`term`, `explanation`, `text`); a part cut,
   or never drawn, is a finding. Any finding fails the stage.
4. The check runs on the silent preview (runbook step 13) and on the lesson player (step 17), after the overlap
   check.

## Consequences

- Speaking 1-3: 8 of the 16 gloss cards (7, 5 and 4) had lost their meaning's last words (the report of #202
  lists them, with the moment and the text before and after). They draw whole now, and the check passes on all
  three. Only meanings were cut: no example was, since every example has a block box of its own.
- The render proof (render_compare g-before against g-after, all 29 built lessons): every lesson draws the same
  at every moment it is seeked to, with no DOM text or board timing difference. The only data file that changes
  is `blocks.css` (player and silent preview), by exactly the one rule of decision 2, in the 28 lessons with such
  a part; Writing 4 has none and is identical.
- Live lessons with the same cut: 221 meanings in 7 lessons (Listening 3-5, Reading 3-5, Writing 2; the report of
  #202 lists each with its moment). The other live lessons are clean. They are not re-released: they need either
  the site's fix of its `player.css`, which mends them all at once, or a new version of each, built with this
  rule (with it, all seven pass the check).
- A lesson's player check takes a few minutes longer: the check plays the whole lesson three times.

To reverse: put `both` back in the template's write-ins, drop `write_in_css` from build_lesson_player.py and the
check from build_lesson.py's two stages. A wrapped meaning or example is cut again in playback.
