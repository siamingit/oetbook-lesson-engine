# 018 — Authored sections: teaching with no slide and no recording

Date: 2026-09-29
Status: **Accepted** (the request) by the maintainer in chat, 2026-09-29, on
Grammar 7 (Punctuation): "Add a second part, 'Other punctuation in OET letters',
as proper authored sections, each with its own boards ... Move the current short
notes (a–g) into these sections instead of leaving them on the comma boards."
The way it is carried below (slots, plan file, `drop`) was chosen by the agent
under that request; the maintainer may reverse it.

## Context

A lesson's sections were its deck's slides (docs/00-PRODUCT.md §1,
methodology §22), and every stage keyed on deck pages: the understanding read
the recording's span of a page, the screens stage the page's text layer, the
bundle a section's `pages`. Grammar 7's recording teaches commas; the maintainer
asked for a second part that the recording does not cover at all: full stops,
semicolons and colons, apostrophes, hyphens and numbers, capital letters,
brackets and other marks, dates and units, case-note abbreviations and a final
practice. Its content had first been added as short notes on the comma boards
(the coverage additions a–g); the maintainer found that not enough.

## Options considered

1. **More notes on the comma boards.** Rejected by the maintainer.
2. **A new kind of section with its own schema and stages** (a section with no
   pages, its own stage for a plan). Touches every stage and the bundle.
3. **A slot per authored section, above every deck page** (this decision): the
   section behaves as a one-page section whose page has no slide and whose
   "understanding" is the agent's written plan, so every stage runs unchanged
   apart from a few guards.

## Decision

- **Slots.** An authored section N takes the page slot 100 + N
  (`paths.ADDED_BASE`, `paths.is_added`); its folders and its section id are
  `added-NN` (`paths.section_tag`); its plan and rulings live in
  `understanding/page-10N/` and `script/page-10N/` like any page's. It is added
  with `build_sections.py <L> --add-section N "TITLE" --by NAME` (kept across
  re-runs, `sections.json` `added`) and comes after the deck's sections. Its title
  is the maintainer's; its status `maintainer`, with `added: true`.
- **The plan.** Its `understanding.json` is written by the agent: beats (a
  learning objective and a teaching point each, with the examples to use), no
  recording times, provenance `authored`, and a top-level `authored_plan` saying
  so. The understanding stage finds it done and never calls a model for it.
- **Screens and narration.** The slot has no slide (`build_sections.slide_text`
  returns nothing; the deck is opened only for a diagram page). The screens
  prompt says the section is authored: one board, a short explanation,
  medical-letter examples right and wrong, the plan's practice item and its
  answer. Every block is `authored` (role example or note; no exercise item);
  every utterance is `authored`. All other rules and audits apply unchanged.
- **Moving content out of a written section.** A section's `overrides.json`
  `drop` (`{"blocks": [ids], "note"}`) takes blocks out: they leave their
  thoughts; in a narrated section's kept plan, a state left empty goes, and only
  at the end of its board, so no state or id is renumbered; the narration of a
  state that goes is dropped with it (`screens.json` `taken_out`). A state that
  keeps some blocks has its narration rewritten (`write_narration.py --states`).
- **Parts.** Where a lesson has authored sections, its two parts are
  categories (`--categories`): the recorded part titled by the agent, the
  authored part by the maintainer; each category's provenance says so. The
  contents board shows the parts.
- **Bundle.** No new field and no new version: an authored section's `pages` is
  empty (it covers no deck page) and its id is `added-NN`
  (docs/04-LESSON-BUNDLE.md §4). The course index lists it with no recording
  span.

## Consequences

- A lesson can now teach what its recording does not, with every block and
  utterance labelled `authored`, so a reviewer sees at once what came from the
  source and what did not. docs/00-PRODUCT.md §1's "one section per slide" holds
  for the recorded part; authored sections are the exception, and only at the
  maintainer's request.
- Lessons 1-6 are unaffected: every section's screens and narration re-render
  byte-identical with the new code (checked 2026-09-29, files restored).
- Code: `paths.py`, `build_sections.py`, `write_screens.py` (drop, the authored
  prompt and provenance, the deck opened only for diagrams), `write_narration.py`
  (taken-out states, authored provenance), `build_lesson_player.py` (empty
  `pages`), `build_course_index.py` (beats without times).
