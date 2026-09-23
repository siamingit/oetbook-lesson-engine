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
| `write_screens.py` **.venv** | `analysis/understanding/page-<N>/understanding.json`, `analysis/deck_defects.json`, `analysis/script/page-<N>/script.json` and `applied.jsonl` (maintainer rulings), `source/slides.pdf` (text layer only), `.env` | `analysis/screens/page-<N>/raw_response.json`, `screens.json`, `checks/index.html` |
| `write_script.py` **.venv** | `analysis/understanding/understanding.json`, `analysis/slides/slide_timeline.json`, `source/slides.pdf`, `.env` | `analysis/script/raw_response.json`, `script.json`, `checks/` |
| `qa_script.py` **.venv** | `analysis/script/script.json`, `analysis/understanding/understanding.json` (exercise sentences only), `source/slides.pdf`, `.env` | `analysis/script/qa/qa_gemini.json`, `qa/raw_response.json` |
| `synthesize_audio.py` | `analysis/script/script.json`, `.env` | `generated/page-<N>/audio/*.wav`, `audio_index.json` |
| `build_timeline.py` | `analysis/script/script.json`, `generated/page-<N>/audio_index.json` | `generated/page-<N>/timeline.json` |
| `build_bundle.py` **.venv** | `analysis/script/script.json`, `generated/page-<N>/timeline.json`, `source/slides.pdf` | `generated/page-<N>/slide.png`, `bundle.json` |
| `build_player.py` | `generated/page-<N>/bundle.json`, `player_template.html` | `generated/page-<N>/player.html` |

### Options

- `transcribe.py --dry-run` sends every form field **except** the audio. No
  audio reaches the API, so nothing is billed. Use it to check API-key
  permissions and field encoding before paying for a run.
- `transcribe.py --audio PATH --out-dir PATH` transcribes an excerpt and
  writes it elsewhere, so a probe does not overwrite a full run.
- `make_transcript.py --offset SECONDS` shifts timestamps so an excerpt reads
  in whole-lesson time.
- `extract_understanding.py`, `write_screens.py`, `write_script.py` and
  `qa_script.py` all take `--page N`, and none calls the API without `--call`.
  Without it they assemble the request and print it, which costs nothing —
  always read the prompt before paying for it. `write_script.py --render` and
  `write_screens.py --render` rebuild their review pages from the saved
  response, also free; for `write_screens.py` that re-runs the board layout
  and the audit too, so a density-rule change never needs a model call.
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

## Screen content: the board model

`write_screens.py` sits between understanding and script writing
(`docs/00-PRODUCT.md` §2: screen content is settled before narration is
written). It authors what the student reads, from the understanding and the
deck's text layer; it is never given the deck image, so there is no layout
to copy. Deck defects from `analysis/deck_defects.json` are corrected here.

The model writes topics made of thoughts made of blocks, and marks each
topic's fixed layer. Everything after that is arithmetic
(`docs/02-DESIGN-SYSTEM.md` §2):

- **One board per topic.** The fixed layer stays for the whole topic; working
  notes accumulate thought by thought and are erased, between thoughts, when
  the next thought would not fit. Erase points are derived, never authored.
- **Ids never depend on layout.** Blocks are `k01..` in document order, so a
  re-layout never renumbers them and a narration cue keeps its target.
- **The audit is deterministic** and fails the run: exercise sentences
  verbatim against the PDF text layer, no forbidden phrases (the product's
  never-appear list plus the ledger's `forbid` phrases), no Persian script,
  no register claim outside a maintainer block, three to seven topics, the
  introduction showing every exercise item, sentence case, and no thought
  bigger than the board.

**Provenance is traced, not trusted.** The applied-edit ledger's `require`
phrases are the only maintainer-authored text on disk, so a block marked
`maintainer` must contain one of them; model-written text that carries a
ruling is `adapted`. This check exists because the first run marked 24 of 65
blocks `maintainer` on the strength of carrying a ruling, and one of those
was an invented sentence.

The old script and ledger for a page are read as **rulings**, not wording:
the maintainer's decisions carry forward, the sentences that carried them
do not.

## QA scope

`qa_script.py` reports only objectively wrong things: a grammar rule that is
factually incorrect or overgeneralised, an ungrammatical sentence in the
script's own English, spoken text not matching on-screen text, or references
to things that do not exist in the product.

QA does **not** report better ways to teach, tone, register, word choice, or
what content should be included. If it is not demonstrably wrong, it is not a
finding.

**One exception, added deliberately: student level.** QA also flags any
sentence a B1 learner would struggle with, and gives a simpler version.
This is not the word-choice judgement banned above — it is measured against
a stated level (A2-B1, `docs/01-METHODOLOGY.md` §17), not against the
reviewer's preference. The line: a sentence that is already plain is not a
finding because the reviewer would have phrased it differently; a sentence
is a finding only when its *English* is harder than the *grammar point* it
teaches. Clinical vocabulary is never a finding, and a grammar term the
script has already defined in plain words is never a finding. A simpler
version may not drop a teaching point to become shorter.

Maximum two passes per slide: one to find defects, one to confirm the fixes
introduced none.

## The applied-edit ledger

`analysis/script/applied.jsonl` records every fix spliced into a script, outside
the file it edits, so a silently dropped edit shows up as a failed check.

It records two different things about each fix, because they fail differently:

| Field | Survives a beat splice | Survives a full regeneration |
|---|---|---|
| `utterances` — id → text hash | yes | **no** |
| `forbid` / `require` — phrases | yes | yes |

The id-and-hash half only means anything within one generation of the script. A
full regeneration issues a fresh id for every utterance at once, so every record
looks stale, every check fires, and the natural response — prune the noise —
throws away the record that the fix was ever made. That is exactly what happened
on page 13: a regeneration dropped three previously-applied fixes and one
teaching point, and the ledger was no help.

So each record also carries the *substance* of its fix as plain phrases:
`forbid` must not appear in the new script, `require` must. Those survive any
amount of renumbering and rewording. Write them in the brief:

```
FORBID: coursebook
REQUIRE: presents with
SUMMARY: no coursebook: the student has only this lesson
```

Matching is case-insensitive substring, over spoken text and cue text, never
regex — these are written by whoever writes the brief, and a pattern that needs
escaping is a pattern that will be got wrong. Choose a phrase that cannot occur
innocently: `video` is safe on this product, `come back` is not, because "we
will come back to the passive" is a legitimate sentence.

`raw_response.json`'s message `id` marks the generation. Beat splices rewrite
that file's text block but leave its id, so the id changes only when a whole new
script is generated; `--render` records a `regenerate-all` marker when it sees a
new one. Records from an older generation stop being id-checked and keep being
substance-checked.

A `FIX LOST` finding **fails the run** — non-zero exit, after the script and
review page are written so the failure can be read. It means a defect someone
already fixed is back, and nothing downstream should be built on it.

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

## Page audio, timeline and the player

Voice: **Rupert** (British, Cartesia voice library id
`0ad65e7f-006c-47cf-bd31-52279d487913`), chosen 2026-09-22 by the maintainer
from three candidates against two page-13 lines, one with a medical term.
Model: Cartesia Sonic 3.6. This is a per-task choice, not yet an ADR-level
decision — ADR 002 records only the provider/model.

**Speed.** The students are non-native speakers; target was roughly 130-140
wpm against Rupert's default of 144 wpm. Measured on the full 56-utterance
page-13 script (real word counts and durations, not a short sample):
default (1.0) → 167.5 wpm, 0.94 → 149.7 wpm, 0.85 → 146.1 wpm, 0.6 (the
API's floor) → 140.3 wpm. `generation_config.speed` does not scale delivery
linearly, and the requested 130-140 wpm range is not reachable through speed
alone — 0.6, the slowest Cartesia allows, is the closest available and is
`synthesize_audio.py`'s default.

**Pronunciation.** Checked by requesting phoneme timestamps
(`add_phoneme_timestamps`) alongside the audio and comparing the returned
IPA to the dictionary pronunciation — not by ear; nothing here has heard the
audio. `hypothyroidism` and `coronary` come out correct by default
(`coronary` as /kɔːrənɛri/, the American variant, which is a legitimate
dictionary form, not an error, so it was left alone per the QA-scope rule
above: not objectively wrong, not a finding). `fibrosis` was wrong — Sonic
read its first syllable as short /ɪ/ ("fih-") instead of the correct
diphthong /aɪ/ ("fye-"). Fixed with a Cartesia pronunciation dictionary
(`pronunciation_dicts.create`), account id `pdict_hvpmosZ9jAfyXDWFdaknq2`,
using a plain "sounds-like" alias (`"fye-BROH-sis"`) rather than Cartesia's
inline IPA markup (`<<...>>`) — the IPA markup produced garbled audio in
testing (it was read as literal text rather than parsed as phonemes; the
sounds-like alias is confirmed correct via the same phoneme-timestamp check).

**Gaps.** `build_timeline.py` places a longer silence between beats than
between utterances within a beat, so one teaching point lands before the
next begins. Both are tunable CLI flags; the defaults used to build page 13
are `--utterance-gap 0.4` (seconds, within a beat) and `--beat-gap 1.2`
(seconds, between beats).

**A pypdfium2 text-layer calibration gotcha.** `extract_annotations.word_boxes()`
(reused by `build_bundle.py` for `slide_phrase` cues) reports word boxes from
`get_charbox()`, which agrees with `get_bounds()` on the page's own text
objects — but both run about 7pt above where the glyphs actually land in
this deck's *rendered* output. Confirmed by pixel-scanning the rendered
`slide.png` for real ink on three independent samples (a body-text row, a
different body-text row, and the white title text): x matched exactly, y
was consistently ~6.5-8pt low, not a scale error. Path and image objects
(the row bars) don't have this problem — `get_bounds()` on those already
matches the render exactly. Likely a substituted/non-embedded font: the
renderer draws with different metrics than the text layer reports.
`build_bundle.py` corrects this with a documented constant
(`TEXT_Y_CORRECTION = 7.0`) rather than touching the shared function; if a
future lesson's deck shows misaligned underlines/highlights, re-measure
per methodology §5 rather than assuming the same deck's fonts.

**Cues, the board, and the fifteen-second rule.** Methodology §17a replaced an
earlier "use cues sparingly" rule after the first built page measured one
visual event every 25.7 seconds, with a 56-second stretch of nothing. Three
cue types carry the new rule:

| Cue | Target kind | What it does |
|---|---|---|
| `write` | `board_note` | writes a word, phrase or example on the board |
| `compare` | `comparison` | two items side by side (`left`, `right`) |
| `pause` | `thinking_pause` | silence for thinking, `seconds` long |

Written items go on a **board beside the slide**, not onto the slide. The
source deck is full, and it is due for replacement anyway (§18), so putting
authored text on the artwork would mean fighting for space on a page that is
about to be thrown away. The board lays itself out in the player, so
`build_bundle.py` resolves no geometry for these — only the slide-anchored
kinds need boxes.

A `pause` cue governs the silence *after* the utterance it sits in, clamped
to 0.5-10s, and never shortens the structural gap it sits in. Its own
`word_index` does not time it, which is why a marker fused to the end of the
last word (`today.{{c2}}`) has to parse — `split_cues` accepts a marker
anywhere in a token, and a marker with no word after it belongs to the last
word. Before that, such a marker was silently left in the spoken text and its
cue was reported as having no marker at all.

`--cue-lead` (default 0.35s) fires every other cue slightly *before* its word,
so the mark appears and then the words arrive, as in a classroom.

`build_bundle.py` prints the visual-density figures on every run — event
count, average spacing, the longest stretch with nothing on screen, and every
stretch over fifteen seconds. Arithmetic, so no reviewer has to time it.

**The audio element is the player's clock.** While an utterance plays, lesson
time is that utterance's start plus the element's `currentTime`, and cue
timings are read from it; the next utterance starts on the element's `ended`
event. Nothing advances time on its own, so if audio stalls the lesson waits
for it instead of running on in silence. The single exception is the gap
between utterances, where there is no audio to read a time from and no cue
can fire: that is a timer, and it is the only one.

An earlier version ran the timeline on a wall clock and merely told the
audio when to start. It failed in a way worth remembering: wall-clock time
drifted a few milliseconds past an utterance's start between animation
frames, the "which utterance is next" lookup then returned the one *after*
it, and that utterance was skipped and never played — while cues, subtitles
and the scrubber carried on as though it had. Deriving time from the thing
that actually makes sound removes the whole class of bug.

**`bundle.json`.** Built by `build_bundle.py`, one file per page, merging the
timeline, resolved cue geometry, and audio references so `player.html` needs
no other input at runtime (it's embedded inline as a JS constant, not
fetched, so the page still works when opened directly from disk — some
browsers block `fetch()` of a sibling file over `file://`). This format is
**spike-only and not the final schema** (AGENTS.md §2) — row-box positions
for `answer_box`/`annotation_note` are hardcoded per-deck pixel constants
measured from this one PDF, and beat→row assignment (`BEAT_ROW` in
`build_bundle.py`) is a hand-built table read off this lesson's learning
objectives. Neither generalises to a different deck layout without rework.

**The audio cache is content-addressed.** A WAV is named for the hash of its
own text plus voice, model, speed and pronunciation dictionary —
`audio/<hash>.wav` — and the utterance id is a label on the index entry, not
the key. This matters because a full script regeneration issues fresh
utterance ids for everything: audio keyed by id would be thrown away
wholesale on every rewrite, including for lines whose words never changed.
Audio the current script no longer refers to is deleted on the next run, so
the folder cannot silently accumulate orphans.

**Cost.** Cartesia bills roughly 1 credit per character (published pricing;
this account's actual $/credit rate is not exposed by the API and was not
independently confirmed — unlike `USD_PER_1000_CREDITS` in `transcribe.py`,
there is no maintainer-confirmed constant here). `synthesize_audio.py` prints
characters sent and reuses from the cache on every re-run, so re-running
after a wording change costs only for the utterances that changed. Note what
that does *not* buy you: a regeneration that rewrites every line pays for
every line, because every line genuinely changed.

## Key handling

The API key is passed to curl on **stdin** (`curl --config -`), never as a
command-line argument, so it does not appear in the process list. Keep it
that way if these scripts are edited.
