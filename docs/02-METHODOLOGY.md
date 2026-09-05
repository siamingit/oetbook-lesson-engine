# Methodology — Extracting Structure from Recorded Lessons

What we have tested, what worked, what failed, and what is still unknown.

These findings are about **method**, not about any one lesson. Per-lesson
numbers belong in generated manifests, not in this file.

Everything here was measured on 2026-09-05 against one sample lesson
(Grammar 1 — Verb Tenses) plus its Canva PDF export. One sample is not
proof that a method generalises. Treat every finding as provisional
until it has been checked on a second and third lesson.

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

---

## 2. What FAILED

Record failures. They are as valuable as successes and stop future
sessions from repeating them.

### Standard scene detection

`ffmpeg -filter:v "select='gt(scene,0.15)'"` returned **zero** cuts
across a full-length lesson.

Cause: slides share a consistent template — same header bar, same logo,
same background — so consecutive slides are numerically similar. Frame
difference heuristics are not a usable slide-boundary signal here.

**Do not use scene detection on this content.**

### OCR from video frames

Not attempted, and should not be. The sample video is 720p at 193 kbps.
Small body text is compression-degraded.

There is no reason to OCR video when the Canva PDF carries a real text
layer. See section 4.

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

## 4. What WORKED — Canva PDF as the slide source of truth

Tested by exporting the sample deck from Canva to PDF.

Result:

- Real embedded text layer, not raster
- `pdftotext -bbox` returns **per-word bounding boxes**
- 164 words with coordinates on a single content page
- Page geometry 1440 × 810 pt against video 1280 × 720 px — both exactly
  16:9, so video↔PDF coordinate conversion is a single scalar (× 0.8889)

### Why this matters

Annotation targets can be resolved **geometrically**:

```
ink event bbox  ∩  PDF word bbox  →  the phrase being annotated
```

No OCR. No vision model guessing what was underlined. This is arithmetic.

It also means published slides can be rendered from Canva exports at any
resolution, so the English output can be visually sharper than the
Persian original, which only exists as a low-bitrate re-encode.

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
slide background with no bleed.

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

Text-to-speech APIs can return **character-level timing** alongside the
audio. If the English script is authored with inline cue markers, each
marker's character offset maps directly to a timestamp.

```
script with cue markers  →  TTS  →  per-character timings  →  timeline
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

Established by the results above:

```
DETERMINISTIC
  Canva PDF        → slide text + per-word geometry
  perceptual hash  → slide segmentation, video↔deck matching
  baseline diff    → annotation events with time and bbox
  bbox intersect   → which phrase each annotation targets
  text diff        → deck/video version mismatch check
  TTS timestamps   → timeline

AI
  Persian ASR
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

The maintainer confirms this affects only one or two lessons, and that a
newer recording of the affected lesson exists.

### Consequence

The pipeline must not assume deck and video match.

Required: a **health check** stage. For each slide, compare PDF text
against text visible in the corresponding video frame. On mismatch, stop
and report rather than proceeding.

This is a plain text diff. It costs almost nothing and prevents a class
of silent errors that would be invisible during English review — a wrong
Persian-era slide would not look wrong to an English reviewer.

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
in tense names on a grammar slide, and in slide titles.

The maintainer confirms grammatical and pronunciation errors occur in the
recorded sessions. This is normal for live teaching.

### Consequence — fidelity and correctness are in tension

An instruction to preserve the teaching faithfully will reproduce these
errors in the English output.

The pipeline therefore needs a **`correction` stage explicitly separate
from `adaptation`**, and a native-English reviewer with OET knowledge as
a publishing gate.

Currently assessed as the largest quality risk in the project. It has no
AI component.

`UNKNOWN`: who performs native-English review.

---

## 11. Audio

Measured on the sample: approximately 17 dB SNR, peak-limited.

Adequate for ASR. **Not adequate for professional voice cloning**, which
is dominated by source audio quality.

Separately, cross-lingual voice clones are documented to carry the
source-language accent. A Persian-accented synthetic voice teaching
English pronunciation to international healthcare workers is a product
contradiction, not a cosmetic issue.

`RECOMMENDATION (not yet decided)`: use a native professional voice.
Preserve instructor identity through name, face and on-camera
introductions rather than synthetic voice.

---

## 12. Open questions

| # | Question | Status |
|---|---|---|
| 1 | Do Canva designs exist for all lessons? | UNKNOWN |
| 2 | Does Canva PDF export give text with geometry? | **ANSWERED — yes** |
| 3 | Total video hours across the library? | UNKNOWN |
| 4 | Do the three ink-extraction preconditions hold across all lessons? | UNKNOWN |
| 5 | ASR accuracy on code-switched Persian/English speech? | UNKNOWN — highest priority |
| 6 | Does the source contain L1-contrastive teaching (Persian-vs-English explanations)? Such content needs replacement, not translation | UNKNOWN |
| 7 | Who reviews the English output? | UNKNOWN |

---

## 13. What has NOT been established

- No ASR has been run. All statements about transcription quality are
  extrapolated from published benchmarks, not measured on this audio.
- No model has been asked to interpret extracted annotation events.
  Whether teaching intent can be recovered reliably is untested.
- Methods were validated on one lesson only.
- No cost figures have been measured.