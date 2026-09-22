# spike/

Throwaway exploration code. Nothing here is an approved pipeline stage.
See `AGENTS.md` §2 — code in `spike/` proves nothing and decides nothing.

These scripts produced the first ASR run on Grammar 1, recorded in
`docs/01-METHODOLOGY.md` §13.

## Requirements

On `PATH`: `ffmpeg`, `ffprobe`, `pdftotext` (poppler), `curl`, `python` 3.12.

Imaging scripts need the project virtual environment — `pypdfium2`, `numpy`,
`Pillow` and `opencv-python-headless`, pinned in `requirements.txt` at the
repository root and chosen in `docs/adr/001-imaging-toolchain.md`:

```
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

Run those scripts with `.venv/Scripts/python`, not a bare `python`. The table
below marks which ones need it; the rest shell out to `ffmpeg` and `curl` and
run on any 3.12 interpreter.

`ELEVENLABS_API_KEY` must be in `.env` at the repository root. `transcribe.py`
locates it relative to its own file, so it breaks if moved out of
`spike/scripts/`.

## Lesson folder layout

Lesson media lives outside the repository and is never committed:

```
<lesson_dir>/
  source/                       read-only inputs, never modified
    video.mp4
    slides.pdf
  analysis/                     everything below is generated,
    audio.mp3                   except keyterms_curated.txt
    keyterms_candidates.json
    keyterms_curated.txt        <- human-edited input
    keyterms.json
    scribe_v2_response.json
    scribe_v2_response.headers.txt
    transcript.txt
    slides/
      slide_scores.json         per-sample frame-to-page scores
      slide_timeline.json       intervals: which page is on screen when
      checks/index.html         side-by-side visual review of every interval
    annotations/
      annotation_events.json    ink events, erasures, cursor dwells, carry-over
      checks/index.html         per-interval annotation layer and event list
```

## Order to run

```
python spike/scripts/extract_audio.py     <lesson_dir>
python spike/scripts/extract_keyterms.py  <lesson_dir> [limit]
                                          # human writes keyterms_curated.txt
python spike/scripts/build_keyterms.py    <lesson_dir>
python spike/scripts/transcribe.py        <lesson_dir> [--dry-run]
python spike/scripts/make_transcript.py   <lesson_dir>/analysis [--offset SECONDS]
```

The slide timeline is independent of the transcript and runs in three steps,
the first two of which decode the whole video:

```
.venv/Scripts/python spike/scripts/build_slide_timeline.py <lesson_dir>
.venv/Scripts/python spike/scripts/build_slide_timeline.py <lesson_dir> --stage2
.venv/Scripts/python spike/scripts/build_slide_timeline.py <lesson_dir> \
    --score-max 0.035 --margin-min 0.04 --margin-min-stage2 0.05
```

`.venv` in the first column marks a script that needs the virtual environment.

| Script | Reads | Writes |
|---|---|---|
| `extract_audio.py` | `source/video.mp4` | `analysis/audio.mp3` — mono, 16 kHz, 64 kbps MP3 |
| `extract_keyterms.py` | `source/slides.pdf` | `analysis/keyterms_candidates.json` — ranked suggestions, **not** sent to the API |
| `build_keyterms.py` | `analysis/keyterms_curated.txt`, `source/slides.pdf` | `analysis/keyterms.json` — verified, provenance-tagged, sent to the API |
| `transcribe.py` | `analysis/audio.mp3`, `analysis/keyterms.json`, `.env` | `analysis/scribe_v2_response.json` (raw, unmodified), `analysis/scribe_v2_response.headers.txt` |
| `make_transcript.py` | `analysis/scribe_v2_response.json` | `analysis/transcript.txt` — readable, timestamped |
| `build_slide_timeline.py` **.venv** | `source/video.mp4`, `source/slides.pdf` | `analysis/slides/slide_scores.json`, `slide_timeline.json`, `checks/` |
| `extract_annotations.py` **.venv** | `source/video.mp4`, `source/slides.pdf`, `analysis/slides/slide_timeline.json` | `analysis/annotations/annotation_events.json`, `checks/` |
| `extract_understanding.py` **.venv** | `analysis/scribe_v2_response.json`, `analysis/slides/slide_timeline.json`, `analysis/annotations/annotation_events.json`, `source/slides.pdf`, `.env` | `analysis/understanding/raw_response.json`, `understanding.json`, `transcript_words.json`, `checks/` |
| `write_script.py` **.venv** | `analysis/understanding/understanding.json`, `analysis/slides/slide_timeline.json`, `source/slides.pdf`, `.env` | `analysis/script/raw_response.json`, `script.json`, `checks/` |
| `qa_script.py` **.venv** | `analysis/script/script.json`, `analysis/understanding/understanding.json` (exercise sentences only), `source/slides.pdf`, `.env` | `analysis/script/qa/qa_gemini.json`, `qa/raw_response.json` |

### Options

- `transcribe.py --dry-run` sends every form field **except** the audio. No
  audio reaches the API, so nothing is billed. Use it to check API-key
  permissions and field encoding before paying for a run.
- `transcribe.py --audio PATH --out-dir PATH` transcribes an excerpt and
  writes it elsewhere, so a probe does not overwrite a full run.
- `make_transcript.py --offset SECONDS` shifts timestamps so an excerpt reads
  in whole-lesson time.
- `extract_understanding.py`, `write_script.py` and `qa_script.py` all take
  `--page N`, and none calls the API without `--call`. Without it they assemble
  the request and print it, which costs nothing — always read the prompt before
  paying for it. `write_script.py --render` rebuilds the review page from the
  saved response, also free.
- `write_script.py --beat ID --brief FILE` rewrites one beat and leaves the rest
  untouched. Utterance ids are renumbered afterwards, because a regenerated beat
  numbers its utterances without seeing the beats it was not given and will
  otherwise collide with them.
- `qa_script.py` is deliberately blind: it is given the English script, the
  slide, and the deliberately wrong exercise sentences, and nothing else. It is
  not told what the source taught, because a reviewer that knows a line came
  from the source will defend it instead of judging it. It proposes findings and
  never writes to `script.json`.

Scribe settings are constants in `transcribe.py`: `model_id=scribe_v2`, batch
(not realtime), word-level timestamps, diarization off, and **no
`language_code`** — the speech is Persian with English mixed in, so the
language must be auto-detected, never forced.

## Curation stays human

`extract_keyterms.py` produces *candidates*. It cannot tell a term from a
typo, and the slide deck contains typos ("prefect", "past participate", "Time
Makers"). Feeding a misspelled keyterm biases the transcript toward the
misspelling — `docs/01-METHODOLOGY.md` §12.

A human writes the approved list into `analysis/keyterms_curated.txt`, one
term per line. Text after `#` is a provenance note:

```
past participle
time markers      # corrected: slides read 'Time Makers'
osteoarthritis    # image-verified: timeline / case-notes slide, no text layer
```

`build_keyterms.py` then checks each term against the PDF text layer and
assigns provenance:

| Note in the curated file | Provenance recorded |
|---|---|
| `corrected: …` | `corrected` |
| `image-verified: …` | `source-derived (slide image, visually verified)` |
| none, and found in the text layer | `source-derived` |
| none, and not found | `authored` |

A term that lands on `authored` is reported on stdout — either it belongs on
an image slide and needs an `image-verified:` note, or it genuinely is not in
the source. It also rejects the list outright if it breaks a Scribe limit
(1000 terms, 50 characters, 5 words, or the unsupported characters
`< > { } [ ] \`), since those would fail the request after the audio has
uploaded.

The curated file is an **input**, not an output. Nothing overwrites it —
`extract_keyterms.py` writes to `keyterms_candidates.json` precisely so a
re-run cannot clobber an approved list.

## Cost

`transcribe.py` calls a paid API. It reads the credit balance before and
after the call and prints credits used and dollars, converting at $0.364 per
1,000 credits (the maintainer's top-up rate, `USD_PER_1000_CREDITS` in the
script — re-confirm after any top-up at a different price).

Credits used come from the `character-cost` response header, cross-checked
against the subscription delta; a disagreement is printed as a warning.
Reading the balance needs the `user_read` permission on the API key, which is
granted separately from transcription access — without it the run still
works and cost falls back to the header alone.

A 200 response carries no `request-id`; the handle for a run is
`transcription_id`, printed at the end and stored in the response body.

Measured rates are in `docs/01-METHODOLOGY.md` §14. Credit burn per minute
differs by account tier by roughly 6.5×, so never project a paid run's cost
from a free-tier one.

## Slide timeline: why two stages

Stage 1 compares whole frames at 160×90 against every page. That fails on this
deck, because pages built from the same template differ only in their content —
pages 13 and 17 are 0.0069 apart on a scale whose median page-pair distance is
0.5714. Stage 1 put 151 samples on page 17 that belong to page 13, preferring
the wrong page by a margin of 0.003.

Stage 2 fixes that. When a frame's two best candidate pages share a template, it
diffs those two page renders at full resolution, and re-scores the frame **only
where they actually differ** — 3.05% of the frame for 13 vs 17. Margins go from
0.003 to over 1.1.

The trigger is per candidate **pair**, never a transitive cluster: page-pair
distances form a continuum, so union-find at any useful threshold chains most of
the deck into one group whose discriminative mask is the whole frame, which is
stage 1 again.

Slide order is never used to decide a page. It is reported as a consistency
check (`page_order_regressions`), so it stays available as evidence rather than
becoming a self-fulfilling assumption.

## Annotation extraction

```
.venv/Scripts/python spike/scripts/extract_annotations.py <lesson_dir> [--measure-baseline]
```

Baseline is the per-pixel median of an interval's first frames, chosen by
measurement (`--measure-baseline` reprints the evidence): against a probe frame
the deck render leaves 31,419 px of colour and compression residual and the
first frame leaves 84,846 px, where the median leaves 1,649.

Three things this recording forced, all of which contradict a plain reading of
methodology §5:

- **Ink does not only accumulate.** Most annotations are erased before the slide
  changes, so removals are events, emitted once per erased annotation.
- **Ink outlives its slide.** The tool draws on the screen, not the slide, so ink
  survives a slide change until it is erased. Such regions are attributed to the
  previous interval and never resolved against the new slide's words.
- **Frames absorbed from another page must be skipped.** The slide timeline folds
  sub-5 s runs into their neighbour; those frames show a different slide, and
  building a baseline from them turns that slide's artwork into annotation.

Cursors are separated from ink by persistence first — a moving cursor never lands
twice in the same place, and a *held* cursor keeps a constant footprint and
vanishes without an erasure, where ink grows and only leaves by being erased.
Shape matching runs last and only as cleanup, against templates harvested from
blobs that already moved every sample rather than hand-specified, because §5
records several cursor shapes in this material.

## Key handling

The API key is passed to curl on **stdin** (`curl --config -`), never as a
command-line argument, so it does not appear in the process list. Keep it
that way if these scripts are edited.
