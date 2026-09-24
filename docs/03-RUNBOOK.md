# Runbook — building one lesson

The complete ordered procedure to turn one recorded Persian lesson into its
English interactive lesson. Written 2026-09-24, after Grammar 1 was built end
to end; its measured costs and times are the baseline below.

Everything here runs from the repository root with `.venv/Scripts/python`.
`<L>` is the lesson folder, for example `C:\OET\lessons\grammar-02-...`.

---

## One command

```
.venv/Scripts/python spike/scripts/build_lesson.py <L> --budget 45
```

It runs every stage in order, skips anything already done and passing, and
stops at:

- a **review gate** not yet approved, saying what to review and how to approve;
- a **failure**, with the last lines of output (all output is in
  `<L>/analysis/runner.log`);
- a **paid stage** that would take the lesson's model spend over `--budget`.
  Without `--budget` no paid stage runs at all.

Run the same command again after each gate or fix: it resumes where it
stopped. Approve a gate with:

```
.venv/Scripts/python spike/scripts/build_lesson.py <L> --approve GATE --by NAME
.venv/Scripts/python spike/scripts/build_lesson.py <L> --status
```

Approvals are recorded in `<L>/analysis/gates.json` with who and when. Model
spend is measured from the saved responses (Anthropic and Gemini), never
estimated after the fact.

The runner orders the stages and checks them; it decides no content. Fixes at
a gate (overrides, briefs, rulings, lexicon entries) are made by hand or with
the stage scripts below, then the runner continues.

---

## Before the first lesson

- `.env` holds `ELEVENLABS_API_KEY` (Scribe), `ANTHROPIC_API_KEY` (Claude
  Opus 5), `GEMINI_API_KEY` (QA) and `CARTESIA_API_KEY` (voice).
- `.venv` is installed from `requirements.txt`; `ffmpeg`, `ffprobe` and
  Microsoft Edge (the mark check drives it headless) are on the machine.
- `spike/lexicon.json` is synced to Cartesia:
  `.venv/Scripts/python spike/scripts/lexicon.py --verify`.

The lesson folder:

```
<L>/source/video.mp4     the recording (read-only)
<L>/source/slides.pdf    the Canva deck export (read-only)
<L>/analysis/            everything generated about the lesson
<L>/generated/           audio and players
```

---

## Baseline: Grammar 1 (Verb Tenses)

2 h 05 min recording, 19-page deck, 13 sections plus the introduction, 62
boards, 991 utterances. The finished lesson plays in **120 minutes** (106 of
speech) at **149.5 words per minute**.

| Stage | Measured cost | Measured time |
|---|---|---|
| Transcription, Scribe v2 | $0.56 (1,548 credits) | UNKNOWN (not recorded) |
| Understanding, 15 pages | $5.72, mean $0.38 a page | about 2 min a page (page 4) |
| Screens, 13 sections | $7.60 kept; $6.76 more on rejected attempts while the rules were being made | about 5 min for the largest section |
| Narration, 14 sections | $7.77 first drafts; $4.00 of state rewrites after review | about 10 min for the largest section |
| Language QA, Gemini | $4.94 over all passes | 1 to 2 min a pass |
| Terms check probes | 3,146 Cartesia characters, 131 Scribe clips | 3 min |
| Synthesis, Cartesia | 84,766 characters (plus 886 for one later ruling) | 40 min for 988 clips, no quota retries |
| Ear, Scribe | about 106 min of audio; cost UNKNOWN (not recorded) | ran alongside synthesis |
| Player, structural and mark checks | free | under a minute |

Model spend on disk for Grammar 1 is $71.13, but most of that is
development: the superseded slide-based path, rejected screen attempts and
repeated rules changes. At full price, **a new lesson built on the finished
pipeline would need about $30 of model spend** (understanding ~$6, screens ~$8, narration
~$8 plus rewrites ~$3, QA ~$5); set `--budget` with a margin, for example 45.
Cartesia is billed in characters on the account's plan: about 85,000 per
two-hour lesson. Its price in dollars depends on the plan and is UNKNOWN here.

With the batch mode below, the same work is **estimated at about $14 of model
spend**. That figure is an estimate, not a measurement, until lesson 2 runs;
see "Cost controls".

---

## The procedure

Gates are marked **GATE**. Costs are Grammar 1's.

| # | Stage | Command (the runner runs these) | Reads | Writes | Cost |
|---|---|---|---|---|---|
| 1 | Source preflight pack | `preflight_pack.py <L>` (runs `build_sections.py` first if needed) | `source/` | `analysis/preflight/preflight_pack.zip` (under 4 MB: contact sheet and thumbnails, text or image pages, template groups, section headings with anything needing a title flagged, six video frames, the recording's specs, `summary.md`), `analysis/preflight.json`, `analysis/sections.json` | free, seconds |
| | **GATE source** | the maintainer reviews the pack in chat, sets every missing title, the lesson description and the diagram slides | | | |
| 2 | Audio | `extract_audio.py <L>` | `source/video.mp4` | `analysis/audio.mp3` | free |
| 3 | Keyterm candidates | `extract_keyterms.py <L>` | `source/slides.pdf` | `analysis/keyterms_candidates.json` | free |
| | **GATE keyterms** | the maintainer writes `analysis/keyterms_curated.txt` | | | |
| 4 | Keyterms | `build_keyterms.py <L>` | curated list, deck | `analysis/keyterms.json` | free |
| 5 | Transcription | `transcribe.py <L>`, then `make_transcript.py <L>/analysis` | audio, keyterms | `scribe_v2_response.json`, `transcript.txt` | $0.56 |
| 6 | Slide timeline | `build_slide_timeline.py <L>`, `--stage2`, then `--score-max 0.035 --margin-min 0.04 --margin-min-stage2 0.05` | video, deck | `analysis/slides/slide_timeline.json` | free |
| 7 | Annotations | `extract_annotations.py <L>` | video, deck, timeline | `analysis/annotations/annotation_events.json` | free |
| 8 | Sections | `build_sections.py <L>` (already built by the preflight); `--set PAGE "TITLE"`, `--description "..."`, `--diagram-pages 5,11`, `--categories FILE` at the source gate | deck, `deck_defects.json` | `analysis/sections.json` | free |
| 9 | Understanding | one batch: `run_batch_stage.py <L> --stage understanding` (direct, one page: `extract_understanding.py <L> --page N --call`) for the contents slide and every section's pages | transcript, timeline, annotations, deck | `analysis/understanding/page-N/understanding.json` | $0.38 a page |
| 10 | Screens | one batch: `run_batch_stage.py <L> --stage screens` (direct, one section: `write_screens.py <L> --pages ... --call`) | understanding, deck text, `deck_defects.json`, ledgers | `analysis/screens/<section>/screens.json` | about $0.60 a section |
| 11 | Opening boards and preview | `build_lesson_boards.py <L>`, `build_lesson_preview.py <L>` | sections, screens | `lesson-boards.json`, the introduction's `screens.json`, `analysis/screens/lesson-preview/index.html` | free |
| | **GATE screens** | the maintainer reviews every board in the lesson preview | | | |
| 12 | Narration | one batch each: `run_batch_stage.py <L> --stage narration` (the introduction and every section), then `--stage qa1` (Gemini batch mode) | screens, understanding, ledgers | `analysis/narration/<section>/narration.json`, `qa/qa_pass1.json` | about $0.60 a section, QA $0.15 a pass |
| 13 | Silent preview and review page | `build_silent_preview.py <L>`, `build_narration_review.py <L>` | narration, screens | `generated/lesson-preview/silent/player.html`, `analysis/narration/lesson-review/index.html` | free |
| | **GATE narration** | the maintainer watches the silent preview and reads the QA findings | | | |
| 14 | Terms check | `check_terms.py <L> --pages ...` per section | narration, screens, keyterms, lexicon | `generated/<section>/boards/terms_check.json`, shared `generated/term_probes/` | a few thousand characters |
| | **GATE lexicon** | only when the ear did not hear a term as written: `lexicon_review.py`, then `lexicon.py --approve TERM --by NAME` | | | |
| 15 | Synthesis | `synthesize_narration.py <L> --pages ...` per section (speed 1.0; `--accept-terms` after the lexicon gate) | narration, lexicon, terms check | `generated/<section>/boards/audio/`, `audio_index.json` | about 85,000 characters a lesson |
| 16 | Ear | `ear.py <L> --pages ... --recompare` per section | audio, lexicon, terms check | `generated/<section>/boards/ear.json` | Scribe, about 106 min of audio |
| 17 | Lesson player and checks | `build_lesson_player.py <L>`, `check_board_page.py <L> --dir <L>/generated/lesson-player`, `check_marks.py <L> --dir ...` | every section's narration, screens and audio | `generated/lesson-player/`: the lesson bundle (`bundle.json`, `text.json`, `blocks.css`; docs/04-LESSON-BUNDLE.md), `player.html` (its reference renderer), `marks_check.json` | free |
| | **GATE final** | the maintainer plays the finished lesson | | | |

---

## Cost controls

Recorded 2026-09-24, before lesson 2. Prices looked up that day, not assumed:

| | Standard | Batch | Cache |
|---|---|---|---|
| Claude Opus 5, per million tokens | $5 in, $25 out | $2.50 in, $12.50 out (50%) | write $6.25 (5 min) or $10 (1 hour); read $0.50 |
| Gemini 3.1 Pro Preview, per million tokens (prompts up to 200k) | $2 in, $12 out (thinking billed as output) | $1 in, $6 out (50%) | cached input $0.20 |

Sources: platform.claude.com/docs/en/about-claude/pricing and
.../build-with-claude/batch-processing; ai.google.dev/gemini-api/docs/pricing
("last updated 2026-09-24"), .../batch-mode and .../caching. The Anthropic
batch discount and the caching multipliers stack. Anthropic batches: up to
100,000 requests or 256 MB, most done within an hour, at most 24 hours, results
kept 29 days, no streaming; cache hits inside a batch are best effort and the
1-hour cache is recommended there. Gemini batches: 24-hour target, inline
requests up to 20 MB; implicit caching is automatic from 4,096 tokens on Gemini
3.1 Pro.

**Batch.** Every non-interactive model stage runs as one batch for the whole
lesson: understanding, screens, narration and whole-section QA passes
(`run_batch_stage.py`, which the runner calls). The batch id is saved the moment
it is submitted, so a stopped run waits for the same batch and never pays twice.
Single-section rewrites at a gate stay direct calls, where waiting would slow
the maintainer: `write_narration.py --states --brief`, `write_screens.py
--pages ... --call`, `qa_narration.py --states`.

**Prompt caching.** Each stage's stable system prompt now comes first as a
cached block (1-hour cache in a batch, 5-minute in a direct call); the page's
own data follows it. Before this, every call showed `cache_read_input_tokens =
0`. What caching can save is small, and the numbers say why: output dominates.
On Grammar 1's page 12 the screens call took 20,148 input and 15,995 output
tokens, the narration call 15,752 and 18,683, so output is about 80% of each
call's cost. The cached prefixes are about 5,200 tokens (screens), 3,100
(narration) and 1,000 (understanding), estimated at 3.6 characters a token: at
most about 2 cents saved per screens call. The QA prompt, about 1,700 tokens,
is below Gemini's 4,096-token minimum and cannot cache.

Each request's closing task instruction stays after the page's data on
purpose, since instructions read best after the material. It is short, so
leaving it outside the cached prefix costs almost nothing.

**Measured on lesson 2: pending.** `run_batch_stage.py` prints each batch's
cost and the cache's effect (tokens written, tokens read, net saving) and keeps
them in `analysis/batches/<stage>-<time>.json`. The first stage of lesson 2 is
the measurement; this section and the baseline are updated from it.

Estimated at batch prices from Grammar 1's token counts (`run_batch_stage.py
--dry-run --all` on Grammar 1): understanding $2.23, screens $3.41, narration
$3.38, QA pass 1 $0.99, about $10 of first drafts; with direct rewrites at a
gate (about $3 on Grammar 1) and later QA passes, **about $14 a lesson**, against
$30 at full price.

A dry run is free: `run_batch_stage.py <L> --stage STAGE --dry-run` builds
every pending request, checks its shape (the Gemini request through the SDK's
own types) and prints the count, size and estimate.

## At each gate

**source.** Review `analysis/preflight/preflight_pack.zip` (small enough to
share in chat; `summary.md` inside explains it). Check that the image pages
are the ones you expect, that the template groups make sense against the
contact sheet (the grouping is a heuristic), and that the frames and specs
are the right recording. Every section needs a title; a slide with no heading is titled with
`build_sections.py --set`. Give the lesson its one-line description
(`--description`, the maintainer's own words) and name the slides whose
teaching is a diagram (`--diagram-pages`), which the screens model is then
shown as a reference for the idea only. Where the deck has a contents slide,
record its categories in the maintainer's translation with `--categories FILE`
(JSON: `[{"title": ..., "sections": [section title, ...]}]`, in the slide's
order); they are kept across re-runs, and a re-run that would lose one stops.

**keyterms.** Write `analysis/keyterms_curated.txt` from the candidates: the
clinical and grammar terms Scribe should listen for.

**screens.** Review every board in `analysis/screens/lesson-preview/index.html`.
A fix to on-screen text is an override in the section's `overrides.json`
(with an `expect` guard and a note naming the decision); re-render with
`write_screens.py <L> --pages ... --render`, free. A screen edit must not move
a board's layout (methodology §18, too-broad rules). A decision in the
maintainer's own words goes into the page's ledger
(`analysis/script/page-N/applied.jsonl`) as `require` and `forbid` phrases.

**narration.** Watch `generated/lesson-preview/silent/player.html` and read
`analysis/narration/lesson-review/index.html`. Fix only the states concerned:
write a brief and run `write_narration.py <L> --pages ... --states ... --brief
FILE --call`, then one QA pass on those states:
`qa_narration.py <L> --pages ... --states ... --name decisions --call`. A QA
finding that is about on-screen text is a screens decision; a narrower true
rule is applied to screen and narration together unless it contradicts a
maintainer ruling (methodology §18).

**lexicon.** Only real mispronunciations belong in the lexicon. Many "not
heard" terms are transcription artefacts: homophones ("patient's" and
"patience"), American spelling ("recognize"), digits for number words. Hear
candidates on `spike/out/lexicon-review/index.html`; a term is approved only
by the maintainer's ear (methodology §20). Approving the gate lets sections
whose failures are all artefacts build with `--accept-terms`.

**final.** Play `generated/lesson-player/player.html`. The ear's report per
section is `generated/<section>/boards/ear.json`: lexicon terms not heard
fail; clinical words not heard as written and clips below 80% agreement are
listed for the maintainer's ear. Never re-synthesise speculatively
(methodology §23): change the text or the lexicon, and the cache re-makes
exactly the clips that changed.

---

## When something fails

- **A stage exits non-zero.** The runner stops and prints the last lines; the
  whole output is in `analysis/runner.log`. Fix the cause and re-run.
- **A model reply is cut off** (`REFUSED: ... output cap`). Nothing is
  written; the stage's `MAX_TOKENS` is too small for the section.
- **An audit fails.** The section is not built; `screens.json` or
  `narration.json` lists the findings. Fix by override or brief, never by
  editing the model's raw response.
- **Cartesia returns 402 or 429.** Synthesis waits and retries for about six
  minutes, then stops naming the utterance; clips already made are kept and
  reused on the next run.
- **A hidden or background run dies silently.** Set `PYTHONIOENCODING=utf-8`:
  a script printing Persian to a non-UTF-8 pipe dies after its paid call; its
  saved response is rendered for free with `--render`.
