# 015 — Generated illustrations for glosses, and no pointing at them

Date: 2026-09-27
Status: **Accepted** by the maintainer in chat, 2026-09-27: realistic generated
images replace the gloss line drawings; after two rounds of samples, "Style
approved. One fix first: skin tones must look natural; keep the soft palette for
clothing and objects only". Supersedes the picture part of
docs/adr/013-gloss-moments-and-teacher-openings.md (its gloss moment stands).
The rule is docs/02-DESIGN-SYSTEM.md §7b; the data is docs/04-LESSON-BUNDLE.md,
format 1.11.

## Context

ADR 013 drew a concrete word's gloss as a line drawing from a small catalogue in
code. The maintainer found them childish and asked for realistic generated
images: no stock photos, nothing from the internet; Google's image models with
the Gemini key already used for QA, if they serve.

The first samples (photographic, on a light-grey background) were rejected as
too photographic and with backgrounds. The second (a clean medical-education
illustration, subject only, transparent) were approved, with one fix: skin in
natural tones, the soft palette for clothing and objects only.

## Options considered

1. **Keep the line drawings.** Rejected by the maintainer.
2. **Stock or web images.** Excluded by the maintainer.
3. **Generated illustrations** (this decision): Gemini API image model
   `gemini-3.1-flash-image` (Nano Banana 2), the official docs' choice for
   realistic images (checked 2026-09-27); price $0.50 per million input tokens and
   $60 per million image output tokens (pricing page last updated 2026-09-24;
   about $0.067 for a 1K image by the list price, measured $0.08-0.10 per image
   from the reply's token counts); Google claims no ownership of generated
   content; the Prohibited Use Policy applies; paid-tier prompts are not used to
   improve products; every image carries an invisible SynthID watermark.

For the transparent background: the model draws on a plain white background and
the background is removed locally. rembg, as the maintainer suggested, installs
but cannot load on this machine: its scikit-image dependency is blocked by the
machine's application-control policy, which is not bypassed. The same
segmentation model rembg uses (ISNet, `isnet-general-use.onnx`) runs directly on
onnxruntime, which loads.

## Decision

- **Style guide** (docs/02-DESIGN-SYSTEM.md §7b; `gloss_images.STYLE`, version 3):
  a clean, professional medical-education illustration, semi-realistic with soft
  shading, not a photograph and not childish; skin in natural tones; a
  restrained palette of soft blues, teal and slate grey for clothing and objects
  only; the subject only, isolated, no background, scenery, floor, shadow or
  clutter; no text; nothing graphic or gory (a lightly grazed palm, no blood);
  consistent across the course.
- **Pipeline** (`spike/scripts/gloss_images.py`): the brief and the style guide
  make one prompt; one square image on white; ISNet matte, firmed; the white
  taken out of the edge pixels (so the edge sits clean on any board colour);
  specks under 0.5 % of the subject dropped; trimmed to the subject, 512 px on
  the longer side; saved as a 256-colour PNG with alpha (about 30-50 KB). The
  model's own image is kept so a cut can be redone free; each image's record
  keeps prompt, model, tokens, cost, alt text and an edge report.
- **Cache**: an image's key is a hash of the model, the style version and the
  brief; an unchanged prompt is never generated twice. An image the maintainer
  approved for a brief (`approved` in its record) is kept for that brief when
  the style guide moves on.
- **Data**: a gloss's `icon` is its image brief, "alt text | what to draw", for a
  concrete word where a picture helps; abstract words keep the example only. The
  screens render finds the image in the cache and sets the block's `image`
  {`file`, `alt`}; the html names it by a token each page resolves to its own
  relative path. Images live in `<lesson>/generated/images/`, records in
  `<lesson>/analysis/images/`: never in git.
- **Runner**: a new stage, `images`, after screens: generates the missing
  images within the budget, then re-renders the sections, free. `spent()` counts
  every image's recorded cost, failed ones included.
- **Narration never points at a picture** ("as you can see in the picture",
  "look at the image", "in this picture", "the drawing shows"): the image
  appears while the word is explained, and that is enough. The gloss moment
  reveals the image right after the meaning, with nothing said about it; the
  narration audit fails a pointing phrase anywhere in a lesson.

## Consequences

- A new dependency, onnxruntime (MIT; installed with the maintainer's leave),
  and a model file in `data/models/` (gitignored), downloaded from rembg's
  releases.
- Bundle 1.11: a gloss's `image`; renderer rule 26. A 1.10 reader shows the
  block's `html`, which already carries the image.
- Lessons 1-5's glosses become ADR 013 glosses with images where the word is
  concrete, in the same run (maintainer).
- The line-drawing catalogue of ADR 013 is removed.
