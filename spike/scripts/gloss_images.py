"""Illustrations for glosses (ADR 015): generated, cut out, cached, costed.

    .venv/Scripts/python spike/scripts/gloss_images.py <lesson_dir> --brief "..." --alt "..." [--call]

A gloss whose word is concrete carries an image brief: one short description
of what the picture shows. This script turns the brief and the course's style
guide (STYLE, docs/02-DESIGN-SYSTEM.md §7b) into one prompt and asks Google's
image model (Gemini API, the key already used for QA) for one illustration on
a plain white background; then, locally, it removes the background (the ISNet
segmentation model that rembg uses, run on onnxruntime: rembg itself cannot
load on this machine, whose application-control policy blocks a scikit-image
library it imports), takes the white out of the edge pixels so they sit clean
on any board colour, drops stray specks, trims to the subject and writes:

    <lesson>/generated/images/<key>.png      the subject on a transparent background
    <lesson>/analysis/images/<key>.json      prompt, model, usage, cost, alt, edge check

The key is a hash of the model, the style version and the brief, so an
unchanged prompt is never generated twice (like the audio cache); a new brief
or style makes a new image. The runner counts every record's cost. Without
--call nothing is sent: the prompt and the cache state are printed. The key is
read from .env and never printed.
"""

import datetime
import hashlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO = Path(__file__).resolve().parents[2]
MODEL = "gemini-3.1-flash-image"      # Nano Banana 2: the docs' choice for realistic images (2026-09-27)
# Price, Gemini API pricing page (last updated 2026-09-24), standard paid tier:
# $0.50 per million input tokens, $60 per million image output tokens. The
# record keeps the measured tokens, so the cost is what the reply says.
PRICE_IN, PRICE_OUT = 0.50 / 1e6, 60.0 / 1e6
SIZE = 512                            # px, the longer side of the trimmed subject
MATTE = REPO / "data" / "models" / "isnet-general-use.onnx"   # rembg's ISNet, gitignored
STYLE_VERSION = "3"
STYLE = (
    "A clean, professional medical-education illustration of {brief}. Semi-realistic, with "
    "soft shading and clean edges; a modern, calm look like an illustration in a nursing "
    "textbook. Not a photograph, and not cartoonish or childish. Skin in natural, realistic "
    "human skin tones, never tinted blue, grey or teal. A restrained palette of soft blues, "
    "teal and slate grey for clothing and objects only, sitting well on a pale cream or white "
    "page. Show the subject only, isolated and centred, with nothing around it: no background, "
    "no scenery, no floor, no cast shadow, no clutter. A plain, flat, solid pure white "
    "background. No text, letters, numbers, labels, logos or watermarks. Nothing graphic or "
    "gory: no blood, no open or deep wounds, no distress."
)


def api_key() -> str:
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        name, sep, value = line.partition("=")
        if sep and name.strip() == "GEMINI_API_KEY":
            return value.strip().strip('"')
    raise SystemExit("GEMINI_API_KEY not found in .env")


def image_key(brief: str) -> str:
    return hashlib.sha256(f"{MODEL}|{STYLE_VERSION}|{brief.strip()}".encode()).hexdigest()[:16]


def paths_for(lesson: Path, key: str) -> tuple[Path, Path]:
    return (lesson / "generated" / "images" / f"{key}.png",
            lesson / "analysis" / "images" / f"{key}.json")


_session = None


def matte(im):
    """The subject's alpha, 0-1, from ISNet (rembg's isnet-general-use)."""
    global _session
    import numpy as np
    import onnxruntime as ort
    from PIL import Image
    if _session is None:
        if not MATTE.exists():
            raise SystemExit(f"{MATTE} is missing: download rembg's isnet-general-use.onnx there")
        _session = ort.InferenceSession(str(MATTE), providers=["CPUExecutionProvider"])
    x = np.asarray(im.convert("RGB").resize((1024, 1024), Image.LANCZOS), dtype=np.float32)
    x = x / max(1.0, float(x.max())) - 0.5
    pred = _session.run(None, {_session.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0][0, 0]
    pred = (pred - pred.min()) / max(1e-6, float(pred.max() - pred.min()))
    m = Image.fromarray((pred * 255).astype("uint8"), "L").resize(im.size, Image.LANCZOS)
    return np.asarray(m, dtype=np.float32) / 255.0


def cut_out(data: bytes) -> tuple:
    """The subject on a transparent background, trimmed; and an edge report."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    im = Image.open(io.BytesIO(data)).convert("RGB")
    rgb = np.asarray(im, dtype=np.float32)
    border = np.concatenate([rgb[:8].reshape(-1, 3), rgb[-8:].reshape(-1, 3),
                             rgb[:, :8].reshape(-1, 3), rgb[:, -8:].reshape(-1, 3)])
    bg = np.median(border, axis=0)                      # the plain background's colour
    a = matte(im)
    a = np.clip((a - 0.08) / 0.84, 0.0, 1.0)            # firm the matte: no faint haze, solid core
    # keep the subject: drop specks smaller than 0.5 % of the largest part
    lab, n = ndimage.label(a > 0.02)
    removed = 0
    if n:
        sizes = ndimage.sum(np.ones_like(a), lab, range(1, n + 1))
        kept = [i + 1 for i, s in enumerate(sizes) if s >= 0.005 * sizes.max()]
        removed = n - len(kept)
        a = np.where(np.isin(lab, kept), a, 0.0)
    # take the background out of the edge pixels: I = a*C + (1-a)*B, so C = (I - (1-a)B) / a
    soft = (a > 0.02) & (a < 0.98)
    c = rgb.copy()
    c[soft] = np.clip((rgb[soft] - (1 - a[soft, None]) * bg) / a[soft, None], 0, 255)
    rgba = np.dstack([c, a * 255]).astype("uint8")
    out = Image.fromarray(rgba, "RGBA")
    ys, xs = np.nonzero(a > 0.02)
    pad = 12
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad),
           min(im.width, xs.max() + pad + 1), min(im.height, ys.max() + pad + 1))
    out = out.crop(box)
    scale = SIZE / max(out.size)
    out = out.resize((max(1, round(out.width * scale)), max(1, round(out.height * scale))), Image.LANCZOS)
    # edge report: how much of the outline is soft, and how close its colour
    # still is to the background (a halo would be close)
    al = np.asarray(out, dtype=np.float32)
    edge = (al[..., 3] > 5) & (al[..., 3] < 250)
    near_bg = float(np.mean(np.linalg.norm(al[edge][:, :3] - bg, axis=1) < 18)) if edge.any() else 0.0
    report = {"background": [round(float(v)) for v in bg], "parts": int(n - removed),
              "specks_removed": int(removed), "edge_pixels": int(edge.sum()),
              "edge_near_background": round(near_bg, 3)}
    return out, report


def save_png(out, path: Path) -> None:
    """Web-optimised: 256 colours with their alpha, dithered, optimised (a
    512 px illustration comes to about 30-50 KB instead of 150-250 KB)."""
    from PIL import Image
    out.quantize(colors=256, method=Image.Quantize.FASTOCTREE,
                 dither=Image.Dither.FLOYDSTEINBERG).save(path, "PNG", optimize=True)


def generate(lesson: Path, brief: str, alt: str, call: bool) -> dict:
    """The image for one brief: from the cache, or generated when `call`."""
    key = image_key(brief)
    img, rec = paths_for(lesson, key)
    if img.exists() and rec.exists():
        return {**json.loads(rec.read_text(encoding="utf-8")), "cached": True}
    kept = approved_for(lesson, brief)
    if kept:
        return {**kept, "cached": True}
    prompt = STYLE.format(brief=brief.strip().rstrip("."))
    if not call:
        return {"key": key, "prompt": prompt, "cached": False, "sent": False}
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key())
    r = client.models.generate_content(
        model=MODEL, contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="1:1")))
    data = next((p.inline_data.data for c in (r.candidates or []) for p in (c.content.parts or [])
                 if getattr(p, "inline_data", None) and p.inline_data.data), None)
    u = r.usage_metadata
    tin, tout = (u.prompt_token_count or 0), (u.candidates_token_count or 0)
    cost = round(tin * PRICE_IN + tout * PRICE_OUT, 6)
    record = {"key": key, "brief": brief, "alt": alt, "prompt": prompt, "model": MODEL,
              "style_version": STYLE_VERSION, "input_tokens": tin, "output_tokens": tout,
              "cost": cost, "created": datetime.datetime.now().isoformat(timespec="seconds"),
              "file": img.name}
    rec.parent.mkdir(parents=True, exist_ok=True)
    if data is None:
        # paid for, but nothing came back: the cost is still recorded
        record["failed"] = "no image in the reply"
        rec.with_name(f"{key}.failed.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
        raise SystemExit(f"no image returned for {brief!r} (cost ${cost} recorded)")
    raw = lesson / "analysis" / "images" / f"{key}.source.png"   # the model's own image, for re-cutting free
    raw.write_bytes(data)
    out, report = cut_out(data)
    img.parent.mkdir(parents=True, exist_ok=True)
    save_png(out, img)
    record.update(bytes=img.stat().st_size, size=list(out.size), edges=report)
    rec.write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")
    return {**record, "cached": False}


def find(lesson: Path, brief: str) -> dict | None:
    """The image for a brief, if one is on disk: the current style's, or one the
    maintainer approved for this very brief. Never generates."""
    img, rec = paths_for(lesson, image_key(brief))
    if img.exists() and rec.exists():
        return json.loads(rec.read_text(encoding="utf-8"))
    return approved_for(lesson, brief)


def approved_for(lesson: Path, brief: str) -> dict | None:
    """An image the maintainer approved for this very brief under an earlier
    style (its record carries `approved`): kept, never regenerated because the
    style guide moved on (ADR 015)."""
    d = lesson / "analysis" / "images"
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        if p.name.endswith((".failed.json",)):
            continue
        r = json.loads(p.read_text(encoding="utf-8"))
        if r.get("approved") and r.get("brief", "").strip() == brief.strip() \
                and (d.parent.parent / "generated" / "images" / r["file"]).exists():
            return r
    return None


def spent(lesson: Path) -> float:
    """Every image this lesson paid for, failed ones included."""
    d = lesson / "analysis" / "images"
    return sum(json.loads(p.read_text(encoding="utf-8")).get("cost") or 0
               for p in d.glob("*.json")) if d.exists() else 0.0


def main() -> None:
    lesson = Path(sys.argv[1])
    opt = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    call = "--call" in sys.argv
    if opt("--brief"):
        out = generate(lesson, opt("--brief"), opt("--alt") or opt("--brief").split("|")[0].strip(), call)
        print(json.dumps({k: v for k, v in out.items() if k != "prompt"}, indent=1))
        if not call and not out.get("cached"):
            print("prompt:", out["prompt"])
        return
    if "--all" in sys.argv:
        # every gloss's image brief in the lesson's screens (the runner's images stage)
        n = 0
        for f in sorted((lesson / "analysis" / "screens").glob("*/screens.json")):
            d = json.loads(f.read_text(encoding="utf-8"))
            for t in d["topics"]:
                for h in t["thoughts"]:
                    for b in h["blocks"]:
                        brief = (b.get("icon") or "").strip() if b.get("type") == "gloss" else ""
                        if brief and not find(lesson, brief):
                            out = generate(lesson, brief, brief.split("|")[0].strip(), call)
                            n += 1
                            print(f"{f.parent.name} {b['id']} {b['term']!r}: "
                                  + (f"${out.get('cost')}" if call else "to generate"))
        # every board's picture (ADR 021), from the agent's briefs
        pp = lesson / "analysis" / "pictures.json"
        pics = json.loads(pp.read_text(encoding="utf-8")).get("sections", {}) if pp.exists() else {}
        for tag, entries in sorted(pics.items()):
            for e in entries:
                brief = (e.get("brief") or "").strip()
                if brief and not find(lesson, brief):
                    out = generate(lesson, brief, brief.split("|")[0].strip(), call)
                    n += 1
                    print(f"{tag} board {e['topic']} picture: "
                          + (f"${out.get('cost')}" if call else "to generate"))
        print(f"{n} image(s) {'generated' if call else 'missing'}; images spent ${spent(lesson):.2f}")
        return
    raise SystemExit("give --brief (and --alt), --all, or see the module docstring")


if __name__ == "__main__":
    main()
