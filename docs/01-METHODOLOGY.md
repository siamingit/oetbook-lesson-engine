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
corrections. Not yet decided.

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
| 10 | International branding for the slides | Not decided |

---

## 16. What has NOT been established

- ASR word error rate against a reference transcript.
- No model has been asked to interpret the transcript together with
  slides and annotation events. Whether teaching intent can be recovered
  reliably is untested — now the highest-priority unknown.
- Annotation extraction has not been re-run on the current recording.
- Methods were validated on one lesson only.
- Costs are measured for ASR only.