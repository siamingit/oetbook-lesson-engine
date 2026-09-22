# 001 — Imaging toolchain

Date: 2026-09-22
Status: Accepted

## Context

Two pipeline stages need to turn PDFs and video into pixels and compare them:

- **Slide timeline** (methodology §3, §8) — render each deck page, sample video
  frames, match each frame to a page, and flag stretches where deck and
  recording disagree.
- **Annotation extraction** (methodology §5) — baseline subtraction, connected
  component labelling, blob filtering, per-event bounding boxes and colours.

Methodology §4 adds a third need: high-resolution page rendering for **image
slides**, whose text is a pasted raster with no PDF text layer, and per-word
geometry for text slides so annotation targets can be resolved by bbox
intersection rather than by a model.

The machine has `ffmpeg`, `pdftotext` and `curl`, and the spike scripts have so
far been standard-library only. It has **no PDF rasteriser at all** — no
`pdftoppm`, `pdftocairo`, `pdfimages`, Ghostscript, `mutool` or ImageMagick.
Nothing can currently turn a PDF page into an image.

This is not one stage's problem. Choosing per-stage would mean choosing twice,
and probably inconsistently. The decision is made once, here.

## Options considered

### A. poppler (`pdftoppm`) as a system tool

Same toolchain as the `pdftotext` already in use, and what methodology §4
assumes. Keeps Python dependency-free.

Rejected: solves rendering only. Annotation extraction needs array maths,
connected component labelling and morphology, which is not reasonable to write
by hand against raw bytes. It would leave a second toolchain decision open,
which is the thing this ADR exists to avoid. It also needs a system-level
install that is awkward to reproduce across machines, where a virtual
environment is not.

### B. PyMuPDF

Renders pages and returns text with geometry in one package, and is the most
capable single option.

**Rejected on licence.** PyMuPDF is AGPL-3.0. This is a commercial product.
Commercial licences are sold, but taking on a strong-copyleft dependency for
a core pipeline stage is a liability when permissive alternatives do the same
job.

### C. pypdfium2 + numpy + Pillow + opencv-python-headless *(chosen)*

Covers everything both stages need, under permissive licences, installed into a
project virtual environment rather than system-wide.

## Decision

A project virtual environment at `.venv` (already gitignored), with exact
versions pinned in `requirements.txt` at the repository root:

| Package | Version | Licence | Role |
|---|---|---|---|
| `pypdfium2` | 5.13.0 | BSD-3-Clause / Apache-2.0 (PDFium itself BSD-style) | Render PDF pages; text with geometry |
| `numpy` | 2.5.3 | BSD-3-Clause (bundled parts 0BSD, MIT, Zlib, CC0-1.0) | Array maths for frame comparison and baseline subtraction |
| `Pillow` | 12.3.0 | MIT-CMU | Image IO and basic manipulation |
| `opencv-python-headless` | 5.0.0.93 | Apache-2.0 | Connected components, morphology, resampling |

All four install on Python 3.12 / win_amd64, which is what this machine runs
(3.12.10). `numpy` 2.5.3 requires Python >=3.12; `opencv-python-headless`
ships `cp37-abi3` Windows wheels, which cover 3.12.

`headless` is chosen deliberately: the pipeline never opens a GUI window, and
the headless wheels omit the Qt dependency, which on Linux non-headless wheels
is LGPLv3.

**PyMuPDF is not to be added to this project.**

## Consequences

The spike scripts stop being standard-library only. Every script that needs
imaging must run under `.venv`, and `spike/README.md` is updated to say so.
Scripts that need no imaging (`extract_audio.py`, `transcribe.py`,
`make_transcript.py`) keep working under a bare interpreter, since they shell
out to `ffmpeg` and `curl`.

`pdftotext` stays a system dependency for keyterm extraction. pypdfium2 could
replace it later, but no reason to churn working code now.

Pinning exact versions means upgrades are deliberate. Re-pin only with a
reason, and re-check licences when doing so.

### Licence obligation to track

`opencv-python-headless` wheels **bundle FFmpeg under LGPLv2.1**. The OpenCV
code itself is Apache-2.0, but the shipped binary is not purely Apache-2.0.
pypdfium2 similarly requires that PDFium's licence and its dependency licences
travel with binary distributions.

Neither is a blocker for use, and neither is strong copyleft. Both carry
attribution and — for LGPL — relinking obligations *if binaries are
redistributed*. This project's current shape is a build pipeline whose output
is structured content, not shipped software, so redistribution of these
binaries is not currently in scope.

`UNKNOWN`: whether any future packaging of this pipeline redistributes these
binaries, and what attribution the product then owes. Flag it before shipping
anything that embeds them. This ADR records the licences; it is not legal
advice and no lawyer has reviewed it.

`UNKNOWN`: whether `opencv-python-headless` is needed at all. It is included
because methodology §5's connected-component labelling is genuinely awkward
without it. If the annotation stage ends up implemented with numpy alone, drop
it in a superseding ADR rather than leaving an unused dependency in place.
