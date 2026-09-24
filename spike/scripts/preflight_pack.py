"""The source preflight pack: a small zip the maintainer reviews in chat before
a lesson is built (docs/03-RUNBOOK.md, gate "source").

    .venv/Scripts/python spike/scripts/preflight_pack.py <lesson_dir>

Reads:  <lesson_dir>/source/slides.pdf, <lesson_dir>/source/video.mp4
        <lesson_dir>/analysis/sections.json (built here by build_sections.py
        when it does not exist yet)
Writes: <lesson_dir>/analysis/preflight/      contact sheet, thumbnails, frames,
                                              summary.md
        <lesson_dir>/analysis/preflight.json  the same facts, for the runner
        <lesson_dir>/analysis/preflight/preflight_pack.zip   under 4 MB

In the pack:
  - a thumbnail of every deck page, and one contact sheet of them all;
  - which pages have a text layer and which are images (no text to read, so
    their words come from the understanding stage's reading of the render);
  - groups of pages that share a template, from the header band and the
    background at the page edges (a heuristic; the contact sheet is the check);
  - the section headings read from the deck by position, with every section
    that needs a title flagged, the lesson title and the contents slide;
  - six frames sampled across the video;
  - the recording's technical specs from ffprobe.
Deterministic and free: no model, no API.
"""

import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

THUMB_W = 360
SHEET_COLS = 5
FRAMES = 6
MAX_ZIP = 4 * 1024 * 1024
TEMPLATE_DIFF = 14.0          # mean absolute difference, 0-255, of the signature


def jpeg(img: Image.Image, quality: int = 72) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def border_signature(img: Image.Image) -> np.ndarray:
    """The page's template: the header band (top sixth) and thin strips down
    both edges, which carry the background colour, in colour at 96x54. Content
    reaches the bottom and the sides of many slides, so only these regions
    are compared. Tuned on Grammar 1: it separates the branding pages, the
    teal-bar pages and the orange-bar pages. A heuristic, reported as such."""
    a = np.asarray(img.convert("RGB").resize((96, 54)), dtype=np.float32)
    return np.concatenate([a[:9].reshape(-1), a[9:, :3].reshape(-1), a[9:, -3:].reshape(-1)])


def template_groups(sigs: dict[int, np.ndarray]) -> list[list[int]]:
    groups: list[tuple[np.ndarray, list[int]]] = []
    for page, s in sigs.items():
        for ref, members in groups:
            if float(np.abs(ref - s).mean()) < TEMPLATE_DIFF:
                members.append(page)
                break
        else:
            groups.append((s, [page]))
    return [m for _, m in groups]


def probe(video: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json",
                        str(video)], capture_output=True, text=True)
    if r.returncode != 0:
        return {"error": r.stderr[-300:]}
    d = json.loads(r.stdout)
    fmt = d.get("format", {})
    out = {"file": video.name, "size_mb": round(int(fmt.get("size", 0)) / 1e6, 1),
           "duration_s": round(float(fmt.get("duration", 0)), 1),
           "bit_rate_kbps": round(int(fmt.get("bit_rate", 0)) / 1000)}
    for st in d.get("streams", []):
        if st.get("codec_type") == "video":
            num, _, den = (st.get("avg_frame_rate") or "0/1").partition("/")
            out["video"] = {"codec": st.get("codec_name"), "width": st.get("width"),
                            "height": st.get("height"),
                            "fps": round(float(num) / float(den or 1), 2) if float(den or 1) else None,
                            "bit_rate_kbps": round(int(st.get("bit_rate", 0) or 0) / 1000)}
        elif st.get("codec_type") == "audio":
            out["audio"] = {"codec": st.get("codec_name"), "sample_rate": st.get("sample_rate"),
                            "channels": st.get("channels"),
                            "bit_rate_kbps": round(int(st.get("bit_rate", 0) or 0) / 1000)}
    return out


def frame_at(video: Path, t: float) -> bytes | None:
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.1f}", "-i", str(video),
                        "-frames:v", "1", "-vf", "scale=480:-2", "-f", "image2pipe",
                        "-vcodec", "mjpeg", "-q:v", "5", "-"], capture_output=True)
    return r.stdout if r.returncode == 0 and r.stdout else None


def clock(t: float) -> str:
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{int(t % 60):02d}"


def build(L: Path) -> Path:
    import pypdfium2 as pdfium
    src = L / "source"
    missing = [n for n in ("video.mp4", "slides.pdf") if not (src / n).exists()]
    if missing:
        raise SystemExit(f"source files missing: {missing} in {src}")
    out = L / "analysis" / "preflight"
    out.mkdir(parents=True, exist_ok=True)

    # sections, headings by position (build_sections.py), when not built yet
    sp = L / "analysis" / "sections.json"
    if not sp.exists():
        subprocess.run([sys.executable, str(Path(__file__).with_name("build_sections.py")), str(L)],
                       check=True, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    sections = json.loads(sp.read_text(encoding="utf-8"))

    doc = pdfium.PdfDocument(str(src / "slides.pdf"))
    pages, thumbs, sigs = [], {}, {}
    for i in range(len(doc)):
        page = doc[i]
        tp = page.get_textpage()
        chars = tp.count_chars()
        img = page.render(scale=THUMB_W / page.get_width()).to_pil()
        thumbs[i + 1] = img
        sigs[i + 1] = border_signature(img)
        pages.append({"page": i + 1, "text_chars": chars,
                      "layer": "text" if chars >= 20 else "image (no text layer)"})
    groups = template_groups(sigs)

    # contact sheet: every page, numbered
    tw, th = thumbs[1].size
    rows = (len(thumbs) + SHEET_COLS - 1) // SHEET_COLS
    sheet = Image.new("RGB", (SHEET_COLS * (tw + 8) + 8, rows * (th + 26) + 8), "white")
    from PIL import ImageDraw
    draw = ImageDraw.Draw(sheet)
    for n, img in thumbs.items():
        r, c = divmod(n - 1, SHEET_COLS)
        x, y = 8 + c * (tw + 8), 8 + r * (th + 26)
        sheet.paste(img.convert("RGB"), (x, y + 18))
        kind = "text" if pages[n - 1]["text_chars"] >= 20 else "IMAGE"
        draw.text((x, y + 2), f"page {n}  ({kind})", fill=(40, 40, 40))

    video = probe(src / "video.mp4")
    dur = video.get("duration_s") or 0
    frames = []
    for k in range(FRAMES):
        t = dur * (0.05 + 0.9 * k / max(1, FRAMES - 1))
        data = frame_at(src / "video.mp4", t)
        if data:
            frames.append((t, data))

    heads = [{"pages": s["pages"], "title": s.get("title") or "", "heading": s.get("heading"),
              "status": s.get("status"), "needs_title": s.get("status") == "needs-title",
              "why": s.get("why")} for s in sections["sections"]]
    facts = {"lesson_title": sections["lesson"].get("title"),
             "title_page": sections["lesson"].get("page"),
             "contents_page": sections.get("contents_page"),
             "deck_pages": len(doc), "pages": pages,
             "image_pages": [p["page"] for p in pages if p["text_chars"] < 20],
             "template_groups": groups, "sections": heads,
             "needs_title": [h["pages"] for h in heads if h["needs_title"]],
             "video": video, "frames_at_s": [round(t, 1) for t, _ in frames]}
    (L / "analysis" / "preflight.json").write_text(json.dumps(facts, ensure_ascii=False, indent=1),
                                                   encoding="utf-8")

    md = [f"# Preflight: {L.name}", "",
          f"Lesson title read from the deck: **{facts['lesson_title']}** (page {facts['title_page']}); "
          f"contents slide: page {facts['contents_page']}.", "",
          "## Recording", "",
          f"- {video.get('file')}: {clock(dur)}, {video.get('size_mb')} MB, "
          f"{video.get('bit_rate_kbps')} kbps overall",
          f"- video: {json.dumps(video.get('video'))}",
          f"- audio: {json.dumps(video.get('audio'))}",
          f"- frames in `frames/` at: " + ", ".join(clock(t) for t, _ in frames), "",
          "## Deck", "",
          f"{len(doc)} pages; `contact_sheet.jpg` shows them all, `pages/` one by one.", "",
          "| page | layer |", "|---|---|"]
    md += [f"| {p['page']} | {p['layer']} |" for p in pages]
    md += ["", "Image pages have no text layer: their words are read from the render by the "
               "understanding stage, and exercise sentences on them are checked against that "
               "reading.", "",
           "## Templates", "",
           "Pages that share a template (header band and background; a heuristic "
           "from the page render, so check it against the contact sheet):", ""]
    md += [f"- group {n}: pages {', '.join(map(str, g))}" for n, g in enumerate(groups, 1)]
    md += ["", "## Sections, headings read from the deck", "",
           "| pages | title | printed heading | status |", "|---|---|---|---|"]
    for h in heads:
        flag = "**NEEDS A TITLE**: " + (h["why"] or "") if h["needs_title"] else (h["status"] or "")
        md.append(f"| {', '.join(map(str, h['pages']))} | {h['title']} | {h['heading'] or ''} | {flag} |")
    md += ["", "To review: every title, the lesson's one-line description "
               "(`build_sections.py --description`), and which slides teach with a diagram "
               "(`--diagram-pages`). Set a missing title with `build_sections.py --set PAGE \"TITLE\"`.",
           "Then approve: `build_lesson.py <lesson> --approve source --by NAME`."]
    (out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    def write_zip(quality: int) -> Path:
        z = out / "preflight_pack.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("summary.md", "\n".join(md) + "\n")
            zf.writestr("preflight.json", json.dumps(facts, ensure_ascii=False, indent=1))
            zf.writestr("contact_sheet.jpg", jpeg(sheet, quality))
            for n, img in thumbs.items():
                zf.writestr(f"pages/page-{n:02d}.jpg", jpeg(img, quality))
            for t, data in frames:
                zf.writestr(f"frames/frame-{clock(t).replace(':', '-')}.jpg", data)
        return z

    for q in (72, 55, 40):
        z = write_zip(q)
        if z.stat().st_size <= MAX_ZIP:
            break
    print(f"preflight pack: {z} ({z.stat().st_size / 1e6:.2f} MB) | {len(doc)} pages, "
          f"{len(facts['image_pages'])} image pages, {len(groups)} template groups, "
          f"{len(heads)} sections, {len(facts['needs_title'])} needing a title, "
          f"{len(frames)} frames")
    return z


if __name__ == "__main__":
    build(Path(sys.argv[1]))
