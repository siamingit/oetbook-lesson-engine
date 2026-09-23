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
and the utterance carrying it is marked `maintainer`.

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

## 18. Slide redesign — a required stage, not yet built

The international product **cannot reuse the Persian-branded deck**. Only
the teaching content carries over: the exercise sentences, their answers,
and the structure of each page. The artwork, branding, byline and Persian
text do not.

This is a **missing pipeline stage**, not a defect in an existing one.
Nothing in `spike/` produces an international slide, and the current
page-13 player renders the *Persian-branded* deck page because that is the
only deck that exists. That is a stand-in, not the output.

What the stage must produce, at minimum:

- A slide per page, in the international design, carrying the same
  teaching content as the source page.
- Per-word geometry for that new slide, since cue targets
  (`slide_phrase`) are resolved against real text positions — see §6 and
  §7. A redesign that ships only images would break annotation targeting
  and force the geometry back to hand-authored coordinates.
- Stable identity between source page and redesigned page, so an existing
  script and timeline still apply after a redesign.

Not yet built, not yet designed, and deliberately not started. See §4
("Slides carry Persian-market branding") for what is wrong with the
current deck, and §15 question 10.

### Known limitation: cue geometry is hardcoded to page 13's layout

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
  fix where it belongs — the redesign, which is rewriting the deck anyway.

So: one register per lesson, `<lesson>/analysis/deck_defects.json`, listing
page, the text as printed, the correction, what is wrong, which QA finding
raised it, and when. It is a **lesson-level** artefact, not a page-level one
— the deck spans pages, and §19's boundary rule puts it with the lesson.

This register is an input to this stage. A redesign that does not clear it
has not finished.

Until then the typo reaches the student, and that is the correct trade:
a visible defect in one printed phrase, against a script that lies about
what the slide says.

### The board has no mobile layout, and that belongs to this stage

§17a puts written items on a board beside the slide. On a phone that does
not work: a 16:9 slide and a board cannot sit side by side at phone width,
and stacking them either shrinks the slide past readability or pushes the
board off-screen while the student is meant to be reading it.

This must be solved **as part of the slide redesign**, not separately. The
reason is that the board only exists because the current deck is full — a
redesigned slide can carry its own space for written items, which changes
what the board is for and whether it remains a separate region at all.
Designing a responsive layout for the board now would be designing around a
deck that is being replaced.

Recorded, not acted on.
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

