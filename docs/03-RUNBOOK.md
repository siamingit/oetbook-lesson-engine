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
repeated rules changes. **A new lesson built on the finished pipeline should
need about $30 of model spend** (understanding ~$6, screens ~$8, narration
~$8 plus rewrites ~$3, QA ~$5); set `--budget` with a margin, for example 45.
Cartesia is billed in characters on the account's plan: about 85,000 per
two-hour lesson. Its price in dollars depends on the plan and is UNKNOWN here.

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
| 8 | Sections | `build_sections.py <L>` (already built by the preflight); `--set PAGE "TITLE"`, `--description "..."`, `--diagram-pages 5,11` at the source gate | deck, `deck_defects.json` | `analysis/sections.json` | free |
| 9 | Understanding | `extract_understanding.py <L> --page N --call` for the contents slide and every section's pages | transcript, timeline, annotations, deck | `analysis/understanding/page-N/understanding.json` | $0.38 a page |
| 10 | Screens | `run_sections.py <L> --budget USD` (each section: `write_screens.py <L> --pages ... --call`) | understanding, deck text, `deck_defects.json`, ledgers | `analysis/screens/<section>/screens.json` | about $0.60 a section |
| 11 | Opening boards and preview | `build_lesson_boards.py <L>`, `build_lesson_preview.py <L>` | sections, screens | `lesson-boards.json`, the introduction's `screens.json`, `analysis/screens/lesson-preview/index.html` | free |
| | **GATE screens** | the maintainer reviews every board in the lesson preview | | | |
| 12 | Narration | `write_narration.py <L> --pages <contents> --call` (introduction), `run_narration.py <L>` (every section, with QA pass 1) | screens, understanding, ledgers | `analysis/narration/<section>/narration.json`, `qa/qa_pass1.json` | about $0.60 a section, QA $0.15 a pass |
| 13 | Silent preview and review page | `build_silent_preview.py <L>`, `build_narration_review.py <L>` | narration, screens | `generated/lesson-preview/silent/player.html`, `analysis/narration/lesson-review/index.html` | free |
| | **GATE narration** | the maintainer watches the silent preview and reads the QA findings | | | |
| 14 | Terms check | `check_terms.py <L> --pages ...` per section | narration, screens, keyterms, lexicon | `generated/<section>/boards/terms_check.json`, shared `generated/term_probes/` | a few thousand characters |
| | **GATE lexicon** | only when the ear did not hear a term as written: `lexicon_review.py`, then `lexicon.py --approve TERM --by NAME` | | | |
| 15 | Synthesis | `synthesize_narration.py <L> --pages ...` per section (speed 1.0; `--accept-terms` after the lexicon gate) | narration, lexicon, terms check | `generated/<section>/boards/audio/`, `audio_index.json` | about 85,000 characters a lesson |
| 16 | Ear | `ear.py <L> --pages ... --recompare` per section | audio, lexicon, terms check | `generated/<section>/boards/ear.json` | Scribe, about 106 min of audio |
| 17 | Lesson player and checks | `build_lesson_player.py <L>`, `check_board_page.py <L> --dir <L>/generated/lesson-player`, `check_marks.py <L> --dir ...` | every section's narration, screens and audio | `generated/lesson-player/player.html`, `marks_check.json` | free |
| | **GATE final** | the maintainer plays the finished lesson | | | |

---

## At each gate

**source.** Review `analysis/preflight/preflight_pack.zip` (small enough to
share in chat; `summary.md` inside explains it). Check that the image pages
are the ones you expect, that the template groups make sense against the
contact sheet (the grouping is a heuristic), and that the frames and specs
are the right recording. Every section needs a title; a slide with no heading is titled with
`build_sections.py --set`. Give the lesson its one-line description
(`--description`, the maintainer's own words) and name the slides whose
teaching is a diagram (`--diagram-pages`), which the screens model is then
shown as a reference for the idea only.

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
