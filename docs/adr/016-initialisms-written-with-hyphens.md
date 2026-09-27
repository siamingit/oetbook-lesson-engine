# 016 — Initialisms are written with hyphens for the voice

Date: 2026-09-27
Status: **Accepted** (the rule) by the maintainer in chat, 2026-09-27:
"Initialisms such as COPD, MRI, CT, ECG, GP, IV must be spoken quickly and
naturally, as one word-group, like a native speaker ... New rule for future
lessons only (do not change lessons 1-6)." The written form below was chosen by
measurement; the maintainer's ear on the probe clips confirms or reverses it.
The measurements are docs/01-METHODOLOGY.md §20, "Initialisms are written with
hyphens".

## Context

In the built lessons, initialisms were spoken letter by letter with long gaps.
Two causes: the lexicon's COPD alias was "C. O. P. D.", and the narration writer
spelled initialisms with spaces ("G P", "C A D", "M R I", "B M I."). Each space
or full stop between letters is a pause.

## Options considered

Each form was synthesised in the same carrier sentence at the lesson speed, with
no dictionary (`spike/scripts/initialism_probe.py`, 454 characters in all), and
measured from Cartesia's word and phoneme timestamps and Scribe's transcript.

1. **"C. O. P. D."** (the old alias): letters, a pause after each; COPD 2.88 s.
2. **"C O P D"** (the writer's form): letters, shorter pauses; COPD 1.84 s.
3. **"C.O.P.D."**: read as a word ("copd"); "I.V." read "roman four".
4. **"COPD"** (plain capitals): fast, but COPD and ECG read as words, IV as
   "roman four", OT close to "ought". MRI, GP and CT were letters.
5. **"C-O-P-D"** (this decision): letters as one group, no gap; COPD 1.76 s,
   and I-V, O-T, E-C-G, G-P, C-T all letters, as fast as plain capitals.

## Decision

- The narration writes an initialism as its capital letters joined by hyphens:
  "C-O-P-D", "M-R-I", "G-P", "I-V", "E-C-G". The screen keeps "COPD".
- The one exception is a lexicon term approved as the voice's default ("OET"),
  written as it is.
- The narration audit (`write_narration.initialism_findings`) fails an
  initialism with spaces or full stops between its letters, joined by full
  stops, or in plain capitals, and names the hyphenated form to write.
- For lessons built after Grammar 1-6. Grammar 1-6 are not changed: for them the
  audit only reports (`LESSONS_BEFORE_INITIALISM_RULE`).
- `check_terms.py` hears every hyphenated initialism of a new lesson before it
  is built, like any other term.

## Consequences

- A new lesson says its initialisms quickly and as letters; it never sends the
  text "COPD", so the lexicon's COPD alias does not apply to it.
- The lexicon's COPD alias stays "C. O. P. D." while Grammar 1-6 keep their
  clips: the audio cache key carries the alias, so changing it would
  re-synthesise every COPD clip of those lessons at their next build. Retire it
  when the maintainer has those clips rebuilt.
- `lesson_text.json`'s narration shows "C-O-P-D" where the board shows "COPD"
  (docs/04-LESSON-BUNDLE.md), as it shows numbers in words.
- Grammar 1-6 still have initialisms the voice may misread (plain "COPD" through
  the old alias, "US" for ultrasound, "IV"); the audit lists them as warnings
  whenever one of those sections is rendered again.
