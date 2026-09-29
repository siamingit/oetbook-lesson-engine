# 019 — Vocabulary lessons: every key word gets a full moment, and the vocabulary is widened

Date: 2026-09-29
Status: **Accepted** (the rule) by the maintainer in chat, 2026-09-29, in the
brief for night run 1: "New general rule for all vocabulary lessons (ADR +
design system + narration rules), to apply in these lessons". How it is carried
below (existing block types, one prompt module, the medical-term meaning) was
chosen by the agent under that request; the maintainer may reverse it.

## Context

The first vocabulary lessons (vocabulary-01 word forms, vocabulary-02 verb +
noun collocations, vocabulary-03 adjective + noun collocations) are built from
recordings that list words and give one or two examples each. The gloss rule
(docs/00-PRODUCT.md §3, docs/02-DESIGN-SYSTEM.md §7b; ADR 013, ADR 015) explains
a hard general word in a short moment with one example. For a lesson whose whole
point is words, the maintainer asked for more:

- every key word gets a full gloss moment: a simple meaning, a pause, a
  generated image for a concrete word, and two or three examples, one from a
  medical letter (Writing) and one from talking to a patient (Speaking);
- the vocabulary is widened: the word family, common collocations, and
  near-synonyms with the difference in use ("dull pain" and "aching pain");
- general English is targeted too, not only medical terms: the adjectives,
  nouns and verbs learners need to build sentences in OET Speaking and Writing;
- more examples in every section (role example, provenance authored);
- A2-B1 language.

## Options considered

1. **A new block type for a vocabulary moment** (several examples, a word
   family, collocations in one block). A schema and bundle change for every
   renderer.
2. **The existing blocks, in a fixed order** (this decision): the gloss block
   carries the meaning, the image and the Writing example; an answer row
   carries the Speaking example; a term box labelled "Word family" or
   "Collocations", and a comparison for a near-synonym, carry the widening.
   No schema, no bundle version.

## Decision

- A lesson is a vocabulary lesson when its id's first word is `vocabulary`
  (the course index's `type`). `spike/scripts/vocabulary_rule.py` holds the rule
  text the screens, narration and QA prompts add for such a lesson; other
  lessons' requests are unchanged.
- **Key words** are the words and collocations a section teaches, plus the
  everyday adjectives, nouns and verbs needed to use them in a sentence.
- **Screens**: each key word, where it is first taught, gets a gloss block
  (meaning in about five plain words; example from a medical letter; image brief
  when concrete), then an answer row with an example said to a patient, then,
  where it helps, a "Word family" term box, a "Collocations" term box, or a
  near-synonym comparison. Every section gets more examples of its own. Every
  such block is `authored`, with a note naming this rule.
- **A key word that is specialist medical terminology** (haematemesis, melaena)
  is not given a dictionary meaning: the learners know it (docs/00-PRODUCT.md
  §3). Its meaning part is the plain wording a patient understands ("vomiting
  blood"), which is what the Speaking example needs. Outside key words, the rule
  "never gloss medical words" is unchanged.
- **Narration**: the gloss moment as in §7b; the Speaking example read and
  marked with a short lead-in that it is said to a patient; word family and
  collocations read item by item; a near-synonym difference said in one
  sentence. No register claims unless the slide or a ruling says so.
- **QA**: told the rule, so a key word's patient-friendly gloss is not a
  finding; it checks that every added example, word family, collocation and
  difference is true English.
- **What may be added** under this rule: facts about English words (forms,
  collocations, differences in use, examples). Never a clinical fact, an exam
  fact, a grammar rule the source does not state, or a register judgement.

## Consequences

- A vocabulary lesson is longer: about 20-30 seconds more per key word. A
  section with many key words gives the full moment to the words it teaches and
  a gloss alone to the rest; the lesson length is checked at the narration
  gate against the maintainer's limit (night run 1: about 75 minutes).
- More gloss images per lesson (about $0.08-0.10 each, ADR 015).
- More authored content for the reviewer: every added block and utterance is
  labelled `authored` and noted, so it is visible at the gate.
- The grammar lessons are unaffected: their requests are built as before
  (checked with a free dry run of screens, narration and QA on Grammar 7).
