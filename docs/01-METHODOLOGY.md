# Methodology — Extracting Structure from Recorded Lessons

What we have tested, what worked, what failed, and what is still unknown.

These findings are about **method**, not about any one lesson. Per-lesson
numbers belong in generated manifests, not in this file.

First measured on 2026-09-05 against one sample lesson (Grammar 1 — Verb
Tenses) plus its Canva PDF export. Updated 2026-09-22 with first ASR
results and measured cost.

Note: the video analysed on 2026-09-05 turned out to be an **older
recording** of Grammar 1. The lesson was later re-recorded after the deck
was corrected. Figures marked *(old recording)* come from that older file.
The current source for Grammar 1 is the newer recording.

One sample is not proof that a method generalises. Treat every finding as
provisional until it has been checked on a second and third lesson.

---

## 1. What the source material is

Confirmed by the maintainer:

1. Slides authored in **Canva**
2. Displayed fullscreen
3. A **separate desktop annotation tool** draws and types over them
4. The whole screen is captured to MP4 while the instructor speaks Persian

So each video frame decomposes as:

```
frame  =  static Canva slide  +  annotation layer
```

This decomposition is what makes the whole approach possible.

### Recording quality varies between lessons

| | Old recording | Current recording |
|---|---|---|
| Resolution | 1280 × 720 | 1280 × 720 |
| Video bitrate | 193 kbps | 478 kbps |
| Audio | AAC stereo | AAC stereo 48 kHz, 256 kbps |

Recording settings are not uniform across the library. Every stage must
read the actual properties of each file, never assume them.

---

## 2. What FAILED

Record failures. They are as valuable as successes and stop future
sessions from repeating them.

### Standard scene detection

`ffmpeg -filter:v "select='gt(scene,0.15)'"` returned **zero** cuts
across a full-length lesson *(old recording)*.

Cause: slides share a consistent template — same header bar, same logo,
same background — so consecutive slides are numerically similar. Frame
difference heuristics are not a usable slide-boundary signal here.

**Do not use scene detection on this content.**

### OCR from video frames

Not attempted, and should not be. Video is 720p with lossy compression;
small body text is degraded.

Where slide text is needed, take it from the Canva PDF — from its text
layer where one exists, or from a high-resolution render of the PDF page
where the slide is an image. See section 4.

---

## 3. What WORKED — slide segmentation by perceptual hash

Method:

1. Sample one frame every 2 s at low resolution
2. Compute a perceptual hash per frame
3. Start a new segment when hash distance from the current segment
   anchor exceeds a threshold (12 worked on the sample)

This correctly grouped a slide together with all the annotations drawn
on it, while still separating genuinely different slides.

Segments shorter than ~5 s are transitions, not slides. Filter them out.

### Structural consequence

On the sample, a single slide carried up to 15 minutes of speech and
dozens of annotations.

**The slide is not the unit of teaching.** A data model shaped as
`Lesson → Slide → {audio, annotations, timeline}` puts a container where
a leaf should be.

An intermediate unit is needed — one teaching point, a few utterances of
narration, and the annotations belonging to it. A slide is the backdrop
for several consecutive such units.

`OPEN DECISION`: the name and fields of this unit are not decided.

---

## 4. PARTLY WORKED — Canva PDF as the slide source of truth

Tested by exporting the sample deck from Canva to PDF.

### Text slides — worked

- Real embedded text layer, not raster
- `pdftotext -bbox` returns **per-word bounding boxes**
- 164 words with coordinates on a single content page
- Page geometry 1440 × 810 pt against video 1280 × 720 px — both exactly
  16:9, so video↔PDF coordinate conversion is a single scalar (× 0.8889)
- The text layer mixes Persian (right-to-left) and English. English terms
  extract cleanly once bidi control characters are stripped.

For these slides, annotation targets can be resolved **geometrically**:

```
ink event bbox  ∩  PDF word bbox  →  the phrase being annotated
```

No OCR. No vision model guessing what was underlined. This is arithmetic.

### Image slides — text layer absent

Some slides contain **pasted images of text** (screenshots placed inside
Canva). On the sample this includes the tense timeline slide and the
case-notes error-correction slide. Their PDF pages carry no text layer
for that content. Found when terms clearly visible on those slides —
e.g. osteoarthritis, asthma, COPD, petit mal epileptic seizure — could
not be found in the extracted PDF text.

Consequence: for image slides, geometric target resolution has no word
boxes to intersect with.

`UNKNOWN`: how to obtain words and positions on image slides. Candidate:
text recognition on a high-resolution render of the PDF page (not on
video frames). Untested.

`UNKNOWN`: what proportion of slides across the library are image slides.

### Rendering

Published slides can be rendered from Canva exports at any resolution, so
the English output can be visually sharper than the recorded original.

### Slides carry Persian-market branding

The deck includes the OETbook.ir logo, Persian text ("آنلاین OET",
instructor byline), and a Persian copyright slide. These must be replaced
for the international product. The intended route is an international
Canva template, applied and re-exported together with spelling
corrections. The template itself is not yet decided; that the deck must be
redesigned is decided, and is a required pipeline stage — see §18.

---

## 5. What WORKED — annotation extraction by baseline subtraction

Method:

1. Take the first frame of a slide segment as the clean baseline
2. For each later frame, mark pixels differing from baseline beyond a
   threshold
3. Label connected components; discard blobs below a minimum area
4. Merge events occurring within a few seconds of each other
5. Record time, bounding box, and mean colour per event

On the sample this produced dozens of discrete, timestamped annotation
events for a single slide, and the isolated annotation layer was visually
verified as clean — pen strokes, typed text and cursor separated from the
slide background with no bleed. *(old recording — to be re-checked on the
current recording)*

### Preconditions

This works because of three properties of the source. If any fails on a
future lesson, the method may not hold:

1. **Screen capture** — no camera noise, no motion, no lighting change
2. **Slides static for long stretches** — a valid baseline exists
3. **High-saturation ink on flat backgrounds**

`UNKNOWN`: whether all three hold across the whole library. Must be
verified per lesson, not assumed.

### Cursor separation

Cursor and ink both appear in the difference layer. They separate by
**persistence**: ink accumulates monotonically, cursor is transient.

Multiple cursor shapes were observed (arrow with coloured halo, move
crosshair, I-beam caret), so shape matching is not a reliable
discriminator. Persistence is.

### Annotation classes observed

| Class | Description |
|---|---|
| Pen ink | Multiple colours. Underlines, circles, crosses, arrows, handwritten words |
| Live typing | Text entered character-by-character during the lesson, including typos and mid-word states |
| Reveal | Large single-frame appearance of a block of content |

---

## 6. What WORKED — deterministic timeline generation

Not yet implemented, but the mechanism is established and requires no
model inference.

Text-to-speech APIs can return **word- or character-level timing**
alongside the audio. If the English script is authored with inline cue
markers, each marker's position maps directly to a timestamp.

```
script with cue markers  →  TTS  →  per-word timings  →  timeline
```

### Rule that follows from this

**The timeline is derived, never authored.**

No human and no agent edits timeline values directly. Humans edit the
script and the cues; the timeline is recomputed. Any design that lets a
timeline be hand-adjusted reintroduces exactly the manual work this
project exists to eliminate.

A further benefit: changing one sentence re-synthesises and re-times only
that sentence.

---

## 7. Boundary between AI and deterministic code

```
DETERMINISTIC
  Canva PDF        → slide text + per-word geometry (text slides only)
  perceptual hash  → slide segmentation, video↔deck matching
  baseline diff    → annotation events with time and bbox
  bbox intersect   → which phrase each annotation targets
  text diff        → deck/video version mismatch check
  TTS timestamps   → timeline

AI
  Persian ASR
  text on image slides (method UNKNOWN)
  cross-modal interpretation — why was this underlined?
  teaching intent and learning objectives
  English rewriting (adaptation, not translation)
  correcting language errors present in the source

DETERMINISTIC
  SVG annotation rendering over Canva slide images
```

AI sits only in the middle. Both ends are arithmetic.

If a model is about to be used for something geometry, arithmetic, string
matching or signal processing can do, that is a design error.

---

## 8. Version mismatch between deck and recording

Discovered on the sample: the Canva PDF and the video showed **different
text** for the same slide. The deck had been edited after recording to
fix an error still visible in the video.

Resolved for Grammar 1: the video analysed was an older recording, and a
newer recording made after the correction is now the source. The
maintainer reports this affects only one or two lessons.

### Consequence

The pipeline must not assume deck and video match.

Required: a **health check** stage. For each slide, compare PDF text
against text visible in the corresponding video frame. On mismatch, stop
and report rather than proceeding.

This is a plain text diff. It costs almost nothing and prevents a class
of silent errors that would be invisible during English review.

Related risk: the library may contain **multiple recordings of the same
lesson**. Batch processing must not silently pick an old one.

---

## 9. Speech is the primary source, slides are context

On the sample, content was typed live that had no relationship to the
slide — a spontaneous example invented to illustrate a grammar point.

A slide-first pipeline would discard this class of content entirely, and
it carries real teaching value.

**Order of authority: speech first, annotations second, slide text third.**

---

## 10. Source contains language errors

The sample deck contains English errors in teaching material — including
in tense names ("prefect", "past participate"), a slide title ("Time
Makers" for Time Markers), and example sentences.

The maintainer confirms grammatical, spelling and pronunciation errors
occur in the recorded sessions. This is normal for live teaching.

### Consequence — fidelity and correctness are in tension

An instruction to preserve the teaching faithfully will reproduce these
errors in the English output.

The pipeline therefore needs a **`correction` stage explicitly separate
from `adaptation`**, and a native-English reviewer with OET knowledge as
a publishing gate.

### Rule: record first, correct later

Transcription records what was actually said, errors included. Correction
happens in a later stage, and every correction is stored as original
text, corrected text, and reason, for the maintainer to approve.

Caution: error-correction slides contain **deliberately wrong sentences**
as teaching material. These must never be "corrected".

`UNKNOWN`: who performs native-English review.

---

## 11. Audio

Measured *(old recording)*: approximately 17 dB SNR, peak-limited.

`UNKNOWN`: SNR of the current recording. Not yet measured.

The instructor's voice does not appear in the English output, so the
instructor's pronunciation errors do not carry over.

Separately, cross-lingual voice clones are documented to carry the
source-language accent. A Persian-accented synthetic voice teaching
English pronunciation to international healthcare workers is a product
contradiction, not a cosmetic issue.

`RECOMMENDATION (not yet decided)`: use a native professional voice.
Preserve instructor identity through name, face and on-camera
introductions rather than synthetic voice.

---

## 12. ASR keyterms

Scribe v2 accepts a list of keyterms that bias recognition toward
expected vocabulary. Rules established on Grammar 1:

- **Curate, do not dump.** Common English words (patient, past, time)
  gain nothing and a long list risks the model "hearing" terms that were
  not said. Keep grammar terminology and clinical vocabulary — the words
  ASR is most likely to get wrong inside Persian speech.
- **Never feed slide typos.** A misspelled keyterm biases the transcript
  toward the misspelling. Typos found in the deck must be excluded or
  corrected.
- **Every keyterm carries provenance:** `source-derived` (found in the PDF
  text layer), `source-derived (slide image, visually verified)`,
  `corrected` (spelling fixed, with a note), or `authored` (not in the
  source).
- The keyterm list is saved alongside the transcript so every run is
  traceable.

### Keyterms bias, they do not force

Measured on Grammar 1: 45 keyterms sent, 42 observed in the transcript.
The corrected keyterm "time markers" never appeared — the instructor said
"time maker" aloud 10 times, and the transcript kept what was said.

This is the correct behaviour for fidelity. It also means **keyterms
cannot fix errors the instructor spoke**. Those survive into the
transcript and must be caught by the correction stage (section 10).

---

## 13. ASR results — Scribe v2

Measured on Grammar 1, current recording, 2026-09-22.

Settings: batch (not realtime), word-level timestamps, diarization off,
language **not** forced (auto-detect), 45 curated keyterms. Audio
extracted to mono 16 kHz MP3 first.

| | |
|---|---|
| Duration | 7510 s (2 h 05 m) — matches source exactly, not truncated |
| Words | 14,486 |
| Latin-script words | 23.5% |
| Detected language | Persian, confidence 0.977 |
| Mean log-probability | −0.037 |
| Low-confidence words (logprob < −1.0) | 18 (0.1%) |
| Turnaround | 220 s |

Qualitative, spot-checked by the maintainer:

- English terms inside Persian speech are transcribed in Latin script and
  spelled correctly, including forms with Persian suffixes attached
  ("point of timeش", "writingتون")
- Fillers and repetitions are preserved — consistent with "record first,
  correct later"

`LIMITATION`: accuracy has **not** been measured against a reference
transcript. There is no word error rate. The evidence is model confidence
plus a maintainer spot-check.

### Reviewing transcripts

- Persian text is unreadable in left-to-right editors and terminals.
  Human review needs a right-to-left view (e.g. an HTML page).
- Review must use **contiguous** passages. Scattered sample lines look
  incoherent even when transcription is accurate, because teaching speech
  depends on what is on screen at that moment.

---

## 14. Cost — measured

| Stage | Measured |
|---|---|
| ASR, Scribe v2, 2 h 05 m lesson | 1,548 credits = **$0.56** |

Rate: pay-as-you-go top-up, $10 = 27,472 credits (≈ $0.364 per 1,000).

**Do not budget from free-tier runs.** On the free tier the same audio
consumed about 6.5× more credits per minute. A cost projection made from
the free-tier probe was wrong by that factor.

Transcription is not a meaningful cost driver for this project.

---

## 15. Open questions

| # | Question | Status |
|---|---|---|
| 1 | Do Canva designs exist for all lessons? | UNKNOWN |
| 2 | Does Canva PDF export give text with geometry? | **PARTLY** — yes for text slides, no for image slides |
| 3 | Total video hours across the library? | UNKNOWN |
| 4 | Do the three ink-extraction preconditions hold across all lessons? | UNKNOWN |
| 5 | ASR accuracy on code-switched Persian/English speech? | **LARGELY ANSWERED** — high confidence and spot-check good; no formal WER (section 13) |
| 6 | Does the source contain L1-contrastive teaching (Persian-vs-English explanations)? Such content needs replacement, not translation | UNKNOWN |
| 7 | Who reviews the English output? | UNKNOWN |
| 8 | How to get words and positions on image slides? | UNKNOWN |
| 9 | What proportion of slides are image slides? | UNKNOWN |
| 10 | International branding for the slides | **Required stage, not yet built** — §18; the design itself is still undecided |

---

## 16. What has NOT been established

- ASR word error rate against a reference transcript.
- No model has been asked to interpret the transcript together with
  slides and annotation events. Whether teaching intent can be recovered
  reliably is untested — now the highest-priority unknown.
- Annotation extraction has not been re-run on the current recording.
- Methods were validated on one lesson only.
- Costs are measured for ASR only.

---

## 17. Student level — a content rule

**Students are healthcare professionals with elementary general English,
roughly A2 to B1. They know clinical vocabulary; they do not have advanced
general English.**

This is a property of the audience, not a style preference, and it binds
every stage that produces English the student reads or hears.

- Use the simplest words that carry the meaning. Everyday English, not
  academic English.
- Short sentences, one idea each. No subordinate clauses stacked together.
- Medical and grammar terms are fine: *hypothyroidism*, *present perfect*,
  *past participle*. Difficult general English is not.
- Define a grammar term the first time it appears, in plain words.
- Explain by showing an example first, then naming the rule.

The failure this prevents is subtle: a script can be factually correct,
well-organised and still unusable, because the *explanation* is harder
English than the *grammar point* it is explaining. A learner who cannot
read the explanation cannot reach the teaching.

This does not license dropping content. Simplifying is a change of
wording, never a change of syllabus — every teaching point in the source
survives at the simpler level.

### Where this is enforced

- **Script writing** — the rule is stated in `write_script.py`'s prompt.
- **QA** — `qa_script.py` checks it and reports any sentence a B1 learner
  would struggle with, together with a simpler version. This is the one
  style-shaped thing QA may report; see `spike/README.md`, "QA scope".
  It is admissible because it is measurable against a stated level, not a
  matter of taste.

---

## 17a. Visual density — a content rule

Measured on the first built page: 24 cues across roughly ten minutes is one
visual event every twenty-five seconds. A viewer disengages. The earlier rule
in the script-writing prompt was too cautious — it optimised against clutter,
and bought flatness instead.

The problem was never the number of marks. It was marks that carry no meaning.
The corrected rule is not "more marks" but "nothing taught without something
to look at".

**Every teaching moment gets a visual anchor.**

- A new word or phrase you teach is written on screen, not only spoken. Write
  it, pause, then explain it.
- An extra example given aloud is written on screen as it is said.
- A key term, a form, or a rule worth remembering is written down.
- A contrast between two things is shown as two things side by side.
- Never let more than about fifteen seconds of speech pass with nothing
  happening on screen. If a stretch has nothing to show, that is a sign the
  explanation itself needs an example.

**Deliberate pauses are part of teaching.**

- After asking the student a question, pause long enough for them to think,
  and mark it.
- After writing something new, pause so the eye can catch up before speaking
  again.
- Pause lengths are cues, not fixed gaps.

**Timing.** A cue fires shortly before the word it belongs to, not on it, so
the student sees it and then hears about it, as in a real classroom. The
script places a cue on a word; the lead is applied deterministically when the
timeline is built, and is not authored.

### Consequences for the pipeline

- Cue types for writing on screen, pausing, and showing two items side by side
  (`write`, `pause`, `compare`).
- A written-on-screen item needs somewhere to go that is not the slide. The
  source deck is full, and it is due for replacement anyway (§18), so written
  items go on a board beside the slide rather than onto the artwork.
- The fifteen-second rule is measurable, so it is checked by arithmetic rather
  than by review: the build reports the longest stretch with nothing on screen.

---

## 17b. Register claims — a content rule

**Never state how formal, informal, common, rare, natural or preferred a word
or phrase is, unless the source says so.** Teach what is correct and what is
wrong. If register genuinely matters for OET, it comes from the maintainer
as a ruling; the utterance carrying it is `adapted` with a note naming the
ruling, and `maintainer` only if its whole wording is the maintainer's (see
"Provenance `maintainer`" below).

### Provenance `maintainer` — tightened 2026-09-24

`maintainer` is only for text whose **whole wording** the maintainer
supplied: every sentence of it lies inside one of the ledger's `require`
phrases, which are the only maintainer-authored text on disk. Text the model
writes that carries a ruling is always `adapted`, with a note naming the
ruling, even when it contains the maintainer's words. The earlier rule (it
must *contain* a required phrase) let the model label seven page-17 lines
`maintainer` because each said "an antacid".

Both builds apply it: `write_screens.py` after the overrides and
`write_narration.py` in `assemble()` relabel a `maintainer` block or utterance
that fails the test to `adapted`, add the note, and record `relabelled`; the
audits fail any `maintainer` label that is not wholly the maintainer's words.
On Grammar 1 this relabelled 13 blocks and 20 utterances. Two remain
`maintainer`: the lesson description on the title board, and page 13's
"'Suffers from' is correct English, but it sounds emotional, and that can
cost you marks.", which the maintainer's brief of 2026-09-23 said quotes his
own words and which the page 13 ledger now holds whole.

Found on page 14, whose critical QA findings were all of this kind:

- "Usually is more conversational. You see it less in medical writing."
- "Occasionally and on some occasions are very formal, so they belong mainly
  in your writing."
- "Two of them are formal: currently, and at the moment."

None is in the source. None is true. "Usually", "occasionally" and "at the
moment" are ordinary English, at home in an OET letter.

### Why this needed its own rule

§7 already forbids adding teaching, and page 13's wrong content still got
through a different way — there the model carried a wrong rule **out of the
source** and stated it too broadly. Page 14 is the opposite failure: the
model **invented** a rule the source never contained.

A register claim slips through the "do not add teaching" instinct because it
does not feel like teaching. It reads as an aside, a helpful native-speaker
nudge, while being exactly as confident and exactly as false as an invented
grammar rule — and more dangerous in one respect: a student told that a normal
word is too informal will avoid a word they needed, losing marks in the very
direction the advice was trying to protect.

The material invites it. A page about signal words and time expressions is
*about* word choice, so register commentary feels like the natural next
sentence. Expect this failure on any vocabulary or word-choice page.

Enforced in `write_script.py`'s prompt ("NEVER JUDGE REGISTER") and as QA
check 8, `register-claim`, reported at `critical`.

---

## 18. Screen content — the stage that replaced the slide redesign

The international product **cannot reuse the Persian-branded deck**. Only
the teaching content carries over: the exercise sentences, their answers,
and the structure of each page. The artwork, branding, byline and Persian
text do not.

This section originally planned a *slide redesign*: a new deck in an
international template, re-exported from Canva with per-word geometry so
the existing cue targeting could keep working. **That plan is superseded.**
Review of the first ten built pages (2026-09-23) found that the lessons had
been written against the Persian deck, so deck typos and branding carried
through and the narration in places explained an error a corrected deck
would not contain. The fix is not a better deck; it is a stage that authors
the screen content before any narration is written — `docs/00-PRODUCT.md`
§2.

### What exists

`spike/scripts/write_screens.py`, run between understanding and script
writing. Inputs: the page's understanding, the deck's PDF text layer (as the
verbatim source of exercise sentences, never as artwork), the lesson's
deck-defect register, and the maintainer's rulings from the superseded
script's ledger. It is not given the deck image, so there is no layout to
reproduce.

It follows the **board model** of `docs/02-DESIGN-SYSTEM.md` §2: one board
per topic, a fixed layer that stays for the whole topic, and a working layer
of notes that accumulates and is erased when the board fills. The model
authors topics, thoughts and blocks and marks the fixed layer; the layout —
which notes share a board, where the working layer is erased — is
arithmetic, derived from the density rule, and re-run without a model call.
Erase points are events the narration will know about, like cues.

What this changes for the rest of the pipeline:

- **Geometry is the renderer's.** Every block carries an id (`k01..`) that
  never depends on layout; a narration cue targets a block, a part of a
  block, or a phrase within it by text. Nothing stores coordinates, so the
  per-word PDF geometry the redesign plan needed is not needed at all.
- **Deck defects are corrected here**, from the register, and teaching that
  existed only because the deck was wrong is dropped. The register remains
  the record.
- **The script stage must be rewritten against `screens.json`.** The
  existing `write_script.py`, and everything downstream of it, still work
  from the deck page and its `slide_phrase` cues. The ten pages built that
  way are superseded and kept only until the new stage is proven.

First run on page 13: five boards, eleven erase points, fifty-eight blocks,
four model calls to converge on the rules now in the prompt and audit
(topic count, provenance tracing, no invented rejected forms, no board
shorthand, no register caution on screen, the introduction showing the full
set of items, sentence case, answers explained). Each rule was added as a
deterministic check first and verified to fail the previous run before the
next call.

### Superseded: cue geometry is hardcoded to page 13's layout

*Describes the deck-page path that the board model replaces. Kept because
the code and the ten superseded pages still exist.*

`build_bundle.py` carries page 13's four-item exercise layout as module
constants — `ROW_RED`, `ROW_GREEN`, `ROW_NOTE`, measured once from that
page's own bars, and `BEAT_ROW`, a hand-built table of which beat discusses
which numbered sentence. `answer_box` and `annotation_note` cues are placed
from those tables and nothing else.

Any page whose exercise layout differs has no valid geometry. It does not
render wrongly — `BEAT_ROW.get()` returns `None` and the build stops with
"cue has no row" — but it stops.

Page 14 did not hit this, and that was luck rather than design: it is a
reference page with no answer boxes, so it emitted no cue of either kind and
the tables were never consulted. The next exercise page with a different
number of items, or items in different places, will fail.

**Not fixed now, and deliberately not.** The fix is not a better table. It
is that a redesigned slide should **emit its geometry** — the redesign knows
where it put the answer boxes, so it can publish their coordinates alongside
the page instead of leaving a later stage to measure them from a render and
hardcode the result. Measuring positions out of a finished PDF is a
workaround for a deck that was not designed to be annotated; §18 removes the
need for it.

Until then: page 13 works, other exercise layouts fail loudly, and no new
per-page constants should be added to paper over it.

### Deck defects are recorded, not fixed in passing

Some defects QA finds are not in the script — they are printed on the
slide. Page 14 has `all day, for 3 years., since 1990`: a stray full stop
before the comma, on the deck itself.

There are three wrong ways to handle that and one right one.

- **Fixing it in the script** breaks the verbatim rule. A `slide_phrase`
  cue must quote the slide exactly, because it is matched against the PDF
  text layer to find where to draw. A "corrected" quotation matches
  nothing.
- **Fixing it in `source/`** is forbidden: source inputs are read-only, and
  the deck is re-exported from Canva, so an edit would be overwritten.
- **Ignoring it** ships the typo and loses the finding.
- **Recording it** keeps the script honest, keeps the finding, and puts the
  fix where it belongs — the screen-content stage, which authors the screen
  afresh.

So: one register per lesson, `<lesson>/analysis/deck_defects.json`, listing
page, the text as printed, the correction, what is wrong, which QA finding
raised it, and when. It is a **lesson-level** artefact, not a page-level one
— the deck spans pages, and §19's boundary rule puts it with the lesson.

This register is an input to `write_screens.py`: each entry for the page is
applied, the block is marked `corrected`, and the audit fails if the printed
form is still on screen. On the superseded deck-page path the typo reaches
the student, and that was the correct trade there: a visible defect in one
printed phrase, against a script that lies about what the slide says.

### The slide image is shown for diagram slides only, as an idea

The rule that the screens model is never given the deck image (§18, "authored,
never copied") has one exception, recorded 2026-09-24: a slide whose teaching
is carried by a diagram. Slides 5 and 11 of Grammar 1 teach with drawn
timelines — arrows, ticks, a series of × marks with a final "X!", pointer
arrows, example boxes — and the text layer alone loses which events sit where.
For those pages, named by the maintainer (`sections.json`, `diagram_pages`),
`write_screens.py` renders the page from the PDF at modest size and passes it
with an instruction to read the diagram's teaching idea only and rebuild it in
the diagram grammar (design system §7a). Nothing else changes: the image is
data, decoration is never copied, and the exercise sentences still come from
the text layer verbatim. The image costs about 1,500 input tokens.

### Narration follows the section, and diagrams are drawn part by part

`write_narration.py` and `qa_narration.py` take `--pages` like the screens
stage and write to `analysis/narration/<section folder>/`; page 13 keeps its
`page-13` folder. The narration model sees a diagram's parts by id
(`k07.3`) and reveals each with its own cue; the audit checks every part is
drawn once, in order, and that a fixed-layer diagram's parts are spread over
the board rather than dumped in its first state. `run_narration.py` writes
every section in lesson order with its first QA pass and stops at the first
failure; `build_narration_review.py` builds one review page for the lesson.

Three findings from the first whole-lesson run, 2026-09-24:

- The model aimed some marks at a diagram part ("circle on k02.3"). Only a
  reveal addresses a part; a mark is found as a phrase inside the block the
  player drew. `assemble()` now resolves a mark's part id to its diagram
  block, records it on the cue (`part_normalised`), and the phrase is still
  audited against the block's text.
- The register audit matched single words only, and page 14's narration
  said "Usually is standard English", "Sometimes is everyday English" and
  "The other day belongs to speaking". QA caught them; the pattern now
  includes those phrasings. A register word printed on the board ("rarely"
  as a signal word) is vocabulary, not a claim, and is exempt.
- The QA reviewer was not shown tense tags, and reported every "the label
  says past" as speech about nothing on screen. The payload now lists each
  tag as it reads on screen, and the narration model is given the chip's
  printed label ("up to now"), not the family key ("past_to_now").

Most QA findings that survive two passes are about the on-screen text the
narration reads aloud (a rule on a callout, a definition in a term box).
Those are screens decisions for the maintainer; a narration rewrite cannot
fix them without making speech and screen disagree.

### The introduction is a section built by code, narrated like any other

The lesson's opening (docs/00-PRODUCT.md §2a) needs no model for its boards:
`build_lesson_boards.py` writes the title board and the contents board as a
section's `screens.json` beside the contents slide's page, one revealable
block per category (a compact "contents item": number, category, its
sections; five category cards did not fit the frame). Its source is the
understanding of the contents slide's interval (Grammar 1: page 4, 6.7
minutes of framing and agenda). `write_narration.py` recognises it by
`section.intro` and adds the introduction rules: a plain greeting, no name,
one to two minutes, every category revealed as it is named, no reference to
the session, the course or the recording; the audit checks the length and
the source words. The maintainer's lesson description is a `require` phrase
in that page's ledger, so the title board's description block is
`maintainer`; an utterance that reads it inside its own words is `adapted`.

The narration never names interface parts. "Chip" and "tag" (for the tense
labels) appeared in 80 utterances written before the rule; `assemble()`
replaces them with "coloured label", records it on the utterance, and the
audit fails any that survives. "Question tag" is grammar and is left alone.

### Too-broad rules — policy (maintainer, 2026-09-24)

When QA finds a rule too broad and its fix narrows the rule, the fix is
applied to the screen and the narration together, unless it contradicts a
maintainer ruling or loses the teaching point. A narrower true rule never
misleads; a broad one does.

How it is applied: the screen text changes by `overrides.json` (with an
`expect` guard and a note naming the decision), the narration of only the
affected states is rewritten from a brief (`write_narration.py --states`),
and those states alone get one QA pass (`qa_narration.py --states ...
--name decisions`, written to `qa/qa_decisions.json`, never over pass 1 or
2). A screen edit must not move a board's layout: the build compares every
board's states and working blocks before and after, and a longer text that
shifts an erase point is reworded until it fits (the Verb tenses
"experience" box, 2026-09-24). Maintainer wording that replaces a rule goes
into the page's ledger as a `require` phrase, the old wording as `forbid`.

### Resolved: the board beside the slide had no mobile layout

§17a put written items on a board *beside* the slide, because the deck was
full. On a phone that could not work: a 16:9 slide and a side board cannot
share phone width. The board model resolves it by removing the slide: the
board *is* the content area of the frame, the topic's own content is its
fixed layer, and written items are its working layer. There is no second
region to lay out.
---

## 19. Artefacts are per page, per lesson, and shared across neither

**Every artefact belongs to exactly one page of exactly one lesson. Nothing
is shared across either boundary.**

```
<lesson>/analysis/understanding/page-NN/    understanding, raw response, checks
<lesson>/analysis/script/page-NN/           script, raw responses, ledger, qa
<lesson>/generated/page-NN/                 audio, timeline, bundle, slide, player
```

This was not true until page 14 was attempted. Every script took `--page N`
and then wrote to a fixed per-lesson path, so a second page silently
overwrote the first one's understanding, script and model response. Three
things made it worse than a simple overwrite:

- The applied-edit ledger had no page. Its `REQUIRE` phrases are sentences
  from one page, so checking them against another page's script reports
  every one as a lost fix, and the build stops for entirely wrong reasons.
- Beat ids repeat across pages (`b1`-`b16` on both), so a ledger keyed on
  beat alone reads page 14's `b1` as superseding page 13's.
- `build_bundle.py` had the page number hardcoded (`PAGE_INDEX = 12`), and
  `build_player.py` picked its page by globbing and taking the last
  directory. Both would silently build the wrong page rather than fail.

Ids stay short within a page (`b1`, `u42`) and are **scoped** by page rather
than made globally unique: the ledger records page and beat together, and
every path carries the page. An id is only ever compared with ids from the
same page.

The rule generalises upward: what is true between two pages of a lesson is
true between two lessons. A constant that names one deck, one account
resource, or one page is a defect waiting for the second input, whether that
input is the next page or the next lesson.

### Values that are not safe outside what they were measured on

Recorded from an audit of the model-calling scripts after page 6 truncated.
None is fixed; each is a thing to check before trusting it on new material.

**`TEXT_Y_CORRECTION = 7.0` is a measurement of one deck's fonts.** It
compensates for pypdfium2's text layer sitting ~7pt above where the glyphs
actually render in this deck — almost certainly a substituted, non-embedded
font. Another deck, or this deck re-exported with fonts embedded, will have a
different offset or none at all. **It must be measured per deck, never
assumed**, by the method in `spike/README.md`: pixel-scan the rendered slide
for real ink and compare against the reported boxes. Getting it wrong does
not fail — underlines and highlights simply sit a few points off the words
they belong to.

**The pronunciation dictionary is account-wide, and its contents are not in
the audio cache key.** One Cartesia dictionary (`page13-pronunciation`)
serves every page of every lesson, and `cache_key()` includes its *id* but
not its *contents*. So adding a term to fix a new word leaves every existing
cached clip untouched — the cache cannot tell that the dictionary changed.
This will bite the first time a term is added: the fix will appear to do
nothing for already-synthesised audio.

**`write_script.MAX_TOKENS = 32000` has little headroom on the longest
pages.** Page 6 (18.7 min of source, 19 beats) used 22,142 output tokens,
69% of the cap. Page 15 carries ~17% more source. It may exceed it. That is
acceptable as it stands, because a truncated reply now fails loudly at the
call site rather than being written and read back as a parse error later.

### What the boundary costs: audio is cached per page

The TTS cache lives in `generated/page-NN/`, so it is per page. A sentence
that appears on two pages is synthesised — and paid for — twice. Measured on
page 14: 50 utterances, zero reuse from page 13, 4,703 characters billed.

**Left as it is.** The waste is small, because pages repeat whole sentences
rarely, and the alternative is a lesson-wide or library-wide audio store,
which is a shared mutable thing sitting exactly on the boundary this section
exists to defend. Paying twice for a rare duplicate is cheaper than the class
of defect that a shared cache invites.

Revisit only with a measurement: if duplicate spend across a real lesson is
material, it is worth the care a shared store would need.

---


## 20. Pronunciation — the lexicon, the cache, and two ears

Found 2026-09-23 when the maintainer heard "fibrosis" mispronounced in the
page 13 board player, after the fix had been "confirmed" from phoneme data.

### What the investigation found

The board synthesis script does apply the Cartesia pronunciation dictionary
on every call, and its cache never reused audio made without it (the board
build has its own cache folder, created with the dictionary from the first
run). Cartesia's phoneme timestamps for all nine "fibrosis" utterances in
the current build show the correct diphthong (`f aɪ b ɹ`), and the same
text synthesised with no dictionary shows the short vowel (`f ɪ b ɹ`). So
the dictionary was in effect for the build on disk. What the maintainer
heard is not explained by the pipeline state; the likeliest candidates are
the superseded deck-page player, which has its own audio, or a difference
between what the phoneme timestamps report and what the voice renders.
Neither could be settled without listening, which is what the ear below is
for. The one real defect found on the way: the dictionary entry was
case-sensitive, so a sentence-initial "Fibrosis" would not have matched.

### The rule: the lexicon is a file

`spike/lexicon.json` is the single source of truth for pronunciations,
British English, versioned in git. `lexicon.py --sync` writes it to
Cartesia; nothing is ever edited in Cartesia directly, and a synthesis
script refuses to run while the dictionary there differs from the file
(`lexicon.require_synced`). Every audio index entry records the lexicon
version and the terms it applied; `check_board_page.py` fails a build in
which any clip lacks that record.

**The cache key contains the lexicon entries the utterance uses.** Changing
a pronunciation therefore re-synthesises exactly the utterances that contain
that term, and nothing else. This replaces the earlier key, which carried the
dictionary's id but not its contents, so a changed entry left every cached
clip untouched (§19).

### Two ears, because one is not enough

- **Phoneme check**, fine. Every synthesis asks Cartesia for phoneme
  timestamps, and each lexicon term is checked against its expected and
  rejected phoneme patterns. This discriminates a vowel; it is the
  instrument that catches "fih-brosis". A failure names the utterance and
  fails the build.
- **Scribe**, coarse (`ear.py`). Every clip is transcribed with no keyterms
  and no forced language, and compared with the script: a lexicon term in
  the script but not heard is a failure with the utterance id, and the
  word-level agreement of every utterance is reported. Scribe decides what
  word was said, not how a vowel was coloured, so a mispronounced term can
  still transcribe correctly; this ear catches a term that came out as a
  different word, and gross failures.

### A fix made from phoneme reports caused the error

Heard by the maintainer 2026-09-24, on the lexicon review page: the voice's
**default** rendering of "fibrosis", with no dictionary entry at all, is
correct. The alias "fye-BROH-sis" added on 2026-09-22 was made from Cartesia's
phoneme reports without anyone listening, and it introduced the error the
maintainer later heard, in every clip. Phoneme reports are not evidence
either way: they report what the alias asked for, and they reported the
default as "wrong" by a pattern that was itself a guess. **Only the
maintainer's ear approves.** The lexicon now has a kind for this outcome:
an `approved default` entry sends nothing to Cartesia, records the approval,
and salts the cache key so the change re-synthesises exactly the utterances
that contain the term.

### New terms are heard before the lesson is built

`check_terms.py` extracts a page's clinical and uncommon terms (the lesson's
curated keyterms, any word of nine or more letters, any word with a clinical
ending), drops those already in the lexicon, synthesises each alone in a
carrier sentence and transcribes it. Terms the ear does not hear back are
listed for the maintainer, and the synthesis script refuses to run without a
fresh terms check that has no failures. Failures are found before the build,
never after. The heuristic over-collects ordinary long words; each costs a
few characters.

## 21. Marks are measured, not eyeballed

Found on page 13, board 3: a circle around "before he quit" wrapped onto two
lines and rendered as two open halves, and touched the words either side.

- Every line fragment of a mark is drawn complete (`box-decoration-break:
  clone`), and a circle carries real padding and margin so it never touches
  a neighbour. The narration prompt keeps circles to one to three words; a
  longer span gets an underline or a bracket, and the audit warns otherwise.
- `check_marks.py` loads the built player in headless Edge at phone-landscape
  and laptop width, applies every state's marks as playback would, and
  measures with the browser's own geometry: a mark that touches a
  neighbouring word fails the build, a mark that wraps is reported, and a
  phrase that cannot be found in its block fails. No screenshot is
  interpreted.

### The ear is not evidence of pronunciation

Recorded 2026-09-23. The maintainer heard "fibrosis" wrong, in two
different ways, in a build where the phoneme check had passed every
utterance and Scribe had heard every one as "fibrosis". Neither instrument
is proof of pronunciation:

- ASR is built to understand a mispronounced word, especially with
  "cystic" in front of it. Scribe catches a term that came out as a
  different word ("OET" as "oat") and nothing finer. Keep it for that.
- Cartesia's phoneme timestamps report the phonemes the alias asked for,
  not what the voice rendered. In the page-13 build all nine "fibrosis"
  clips carried the alias phonemes, yet the word's duration fell into two
  groups (about 1.1 s mid-sentence, 1.55 s sentence-final): the same alias,
  two realisations.

**The only proof of pronunciation is the maintainer's ear.** So:

- `lexicon_review.py` builds a page with every lexicon term playable alone
  and inside one sentence from a lesson, with the default rendering beside
  it and the phonemes shown. The maintainer approves or rejects each.
- Approval is recorded in `spike/lexicon.json` (`lexicon.py --approve
  TERM --by NAME`). A term is used in a lesson only after approval; an
  unapproved lexicon term in a page's text blocks synthesis.
- The target for each entry is written in the file in British IPA with
  stress ("fibrosis": /faɪˈbrəʊsɪs/, stress on the second syllable), so an
  alias is judged against something stated.

## 22. Lesson structure comes from the deck

Revised 2026-09-23, reversing the earlier product rule that contents came
from the teaching content rather than slide boundaries. A lesson is titled
from the deck; its sections are the slides, titled by their headings
corrected for registered deck defects, consecutive equal headings merged;
boards are untitled steps inside a section. `build_sections.py` reads the
headings and writes `analysis/sections.json`; a heading that is not a
title (a table's column labels, an image slide) is listed for the
maintainer and blocks the screens stage until titled. The screens audit
fails a board with its own title and a section title that does not trace
to a slide heading or a maintainer entry. On Grammar 1 the deck gives 12
sections; three need the maintainer's title (the tense table on pages 6
and 7–10, the timeline on page 11).

## 23. Audio budget

Cartesia credit is limited, and most of it so far went on rebuilding page
13 several times. The rule, recorded 2026-09-23:

- Audio is synthesised only after the narration is approved and every
  lexicon term on the page is approved by the maintainer's ear.
- Never re-synthesise a page speculatively. A rewording that has not been
  reviewed is not a reason to spend credit; the content-addressed cache
  makes a real change cheap, a speculative one is pure waste.
- Probes for the lexicon review page are made once per candidate and kept.

### Next on "fibrosis" — recorded, not acted on

The maintainer heard all nine clips wrong. The target is /faɪˈbroʊ.sɪs/,
stress on the second syllable. Cartesia's reported phonemes already match,
so the fault is stress and rhythm: the word lasts 1.0–1.6 s, far too long
for three syllables, and the hyphenated respelling "fye-BROH-sis" is
probably read as three chunks. When credit is available: check Cartesia's
documentation for a phoneme or IPA entry form that carries a stress mark,
make three or four candidate entries, render each alone and in a sentence,
add them to the lexicon review page, and stop for the maintainer to choose.

### Voice speed is a target, not a setting (measured 2026-09-24)

The maintainer found the delivery slightly slow. Page 13 at the lesson's
setting (0.6) measures about 136 words per minute of speech. One 26-word
utterance was synthesised at eleven settings (`speed_probe.py`):

| setting | 0.6 | 0.65 | 0.7 | 0.75 | 0.85 | 0.875 | 0.9 | 0.925 | 0.95 | 1.0 | 1.2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| words per minute | 137 | 137 | 141 | 138 | 148 | 152 | 144 | 157 | 157 | 155 | 157 |

The response is flat and noisy below about 0.75, steeper to about 0.9, and
levels off near 155 above it; run-to-run variation is several words per
minute, so a higher setting can come out slower. A chosen setting is
therefore a target: the lesson's pace is measured again after synthesis,
and the silent preview's estimate (`build_silent_preview.py --wpm`) follows
the measured pace, not the setting.

The maintainer chose 1.0 by ear. Grammar 1 was synthesised whole at 1.0
(991 utterances, 84,766 characters, no quota retries needed) and measures
**149.5 words per minute of speech** across the lesson: below the single
utterance's 155, because longer utterances with lists and numbers run
slower. The whole lesson plays in 120 minutes, 106 of them speech.

### Building the whole lesson (2026-09-24)

- `synthesize_narration.py`, `check_terms.py`, `ear.py` take `--pages` (a
  section). Synthesis retries a transient error (402, 429, timeouts) with
  backoff for about six minutes, writes its index every ten clips, and
  stops naming the utterance if the error persists: an utterance is never
  skipped silently. Term probes are shared by the whole lesson.
- The ear also listens for every clinical and uncommon word of the section
  (from the terms check), not only lexicon terms, and lists any not heard as
  written. Most such lines are formats, not faults: digits for number words,
  American spellings, "timeline" for "time line".
- `build_lesson_player.py` builds one player for the lesson (introduction
  first, contents menu) from each section's audio index; ids are prefixed
  per section and audio stays in its section's folder. The structural check
  and the mark check take `--dir` for it. The structural check learned
  diagram parts; the mark check found that the player could not mark a
  phrase split by a coloured label or an earlier mark (13 marks drew
  nothing), fixed in `wrapPhrase`.

