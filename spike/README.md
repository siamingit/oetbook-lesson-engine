# spike/

Throwaway exploration code. Nothing here is an approved pipeline stage.
See `AGENTS.md` §2 — code in `spike/` proves nothing and decides nothing.

These scripts produced the first ASR run on Grammar 1, recorded in
`docs/01-METHODOLOGY.md` §13.

## Requirements

On `PATH`: `ffmpeg`, `ffprobe`, `pdftotext` (poppler), `curl`, `python` 3.12.
No third-party Python packages — standard library only.

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

| Script | Reads | Writes |
|---|---|---|
| `extract_audio.py` | `source/video.mp4` | `analysis/audio.mp3` — mono, 16 kHz, 64 kbps MP3 |
| `extract_keyterms.py` | `source/slides.pdf` | `analysis/keyterms_candidates.json` — ranked suggestions, **not** sent to the API |
| `build_keyterms.py` | `analysis/keyterms_curated.txt`, `source/slides.pdf` | `analysis/keyterms.json` — verified, provenance-tagged, sent to the API |
| `transcribe.py` | `analysis/audio.mp3`, `analysis/keyterms.json`, `.env` | `analysis/scribe_v2_response.json` (raw, unmodified), `analysis/scribe_v2_response.headers.txt` |
| `make_transcript.py` | `analysis/scribe_v2_response.json` | `analysis/transcript.txt` — readable, timestamped |

### Options

- `transcribe.py --dry-run` sends every form field **except** the audio. No
  audio reaches the API, so nothing is billed. Use it to check API-key
  permissions and field encoding before paying for a run.
- `transcribe.py --audio PATH --out-dir PATH` transcribes an excerpt and
  writes it elsewhere, so a probe does not overwrite a full run.
- `make_transcript.py --offset SECONDS` shifts timestamps so an excerpt reads
  in whole-lesson time.

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

## Key handling

The API key is passed to curl on **stdin** (`curl --config -`), never as a
command-line argument, so it does not appear in the process list. Keep it
that way if these scripts are edited.
