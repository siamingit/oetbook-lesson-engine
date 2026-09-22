"""Match every moment of a lesson video to a page of its slide deck.

Usage:
  .venv/Scripts/python build_slide_timeline.py <lesson_dir>
      Stage 1. Render pages, sample frames, score every frame against every
      page, write analysis/slides/slide_scores.json and print the score and
      margin distributions. Choose thresholds from those percentiles.

  .venv/Scripts/python build_slide_timeline.py <lesson_dir> \
      --score-max S --margin-min M [--no-checks]
      Stage 2. Re-use the cached scores, build intervals, flag low-confidence
      ones, write analysis/slides/slide_timeline.json and the visual checks.

Deterministic. No AI, no API calls (methodology §7).

Method (methodology §3, §4, §8):
  - render each PDF page to video resolution with pypdfium2
  - sample one video frame every 2 s
  - score frame against page by trimmed-mean absolute difference of
    contrast-normalised greyscale, discarding the worst 30% of cells so that
    pen ink, typed text and cursor cannot dominate the comparison
  - merge consecutive samples into intervals; runs under 5 s are transitions
  - flag intervals whose score is poor or whose margin over the runner-up is
    thin: those mean deck and recording disagree, or something is on screen
    that is not in the deck
"""

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont

SAMPLE_SECONDS = 2.0      # methodology §3
MIN_INTERVAL_SECONDS = 5.0  # shorter runs are transitions, not slides
GRID_W, GRID_H = 160, 90  # stage 1 comparison resolution
KEEP_FRACTION = 0.70      # fraction of cells kept by the trimmed mean
RENDER_W = 1280

# Stage 2. Pages built from the same template differ only in their content, which
# is a small part of the frame, so a whole-frame comparison cannot separate them.
# Stage 2 re-scores such frames at full resolution inside only those regions where
# the candidate pages actually differ from each other.
# Triggered per candidate PAIR, not by transitive clustering: page-pair distances
# form a continuum, so union-find at any useful threshold chains most of the deck
# into one group, whose discriminative mask is the whole frame -- which is just
# stage 1 again.
PAIR_SIMILARITY = 0.12       # stage-1 distance below which two pages share a template
PIXEL_DELTA = 25             # greyscale difference that counts as real content difference
MIN_MASK_PIXELS = 500        # below this there is nothing to discriminate on

# Diagnosing a poor match score. Content typed or drawn during the lesson lands
# on parts of the slide that are empty in the deck; a deck/video version mismatch
# changes pixels where the deck already has content. "Empty" means no local
# detail, so an unfilled coloured table row counts as empty just like white space.
DETAIL_LEVEL = 20         # morphological gradient above which a deck pixel has content
DETAIL_MARGIN = 9         # dilation, so pixels just beside deck content are not "empty"
BLANK_MAJORITY = 0.5      # fraction of differing pixels in empty areas to call it live content
# Where the differing pixels fall is not enough on its own: a frame compared
# against the wrong page also differs mostly over that page's empty areas.
# Measured on Grammar 1, correctly matched intervals differ over 1-10% of the
# frame, while a deliberately wrong page differs over 57-89%. Anything above this
# is the page being wrong, wherever the pixels land.
MISMATCH_AREA = 0.35      # fraction of the frame differing that means wrong page

SEEK_DECODE_WINDOW = 3.0  # seconds decoded before a wanted frame, for accurate seeking

CHECK_W = 480             # width of each of the three review panels
LABEL_H = 34


def opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def video_info(path: Path) -> tuple[float, int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "format=duration", "-show_entries", "stream=width,height",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    data = json.loads(out)
    stream = data["streams"][0]
    return float(data["format"]["duration"]), stream["width"], stream["height"]


def render_pages(pdf: Path) -> list[np.ndarray]:
    """Full-resolution greyscale render of every page, for matching."""
    return [np.asarray(img.convert("L")) for img in render_pages_colour(pdf)]


def render_pages_colour(pdf: Path) -> list[Image.Image]:
    """Full-resolution colour render, for human review.

    Matching is greyscale, but a reviewer comparing a colour video frame against
    a greyscale deck panel would see a difference that is not really there.
    """
    doc = pdfium.PdfDocument(pdf)
    return [doc[i].render(scale=RENDER_W / doc[i].get_width()).to_pil().convert("RGB")
            for i in range(len(doc))]


def normalise(a: np.ndarray) -> np.ndarray:
    a = a.astype(np.float32)
    return (a - a.mean()) / (a.std() + 1e-6)


def frame_stream(video: Path):
    """Yield sampled frames as (GRID_H, GRID_W) uint8 arrays.

    ffmpeg downscales with flags=area, the same pixel-area algorithm cv2 uses
    for the page renders, so both sides of the comparison are resampled alike.
    """
    cmd = ["ffmpeg", "-v", "error", "-i", str(video),
           "-vf", f"fps={1 / SAMPLE_SECONDS},scale={GRID_W}:{GRID_H}:flags=area,format=gray",
           "-f", "rawvideo", "-"]
    size = GRID_W * GRID_H
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, dtype=np.uint8).reshape(GRID_H, GRID_W)
    proc.stdout.close()
    proc.wait()


def score_all(video: Path, pages: list[np.ndarray]) -> list[dict]:
    grid = np.stack([
        normalise(cv2.resize(p, (GRID_W, GRID_H), interpolation=cv2.INTER_AREA)).ravel()
        for p in pages
    ])
    keep = int(grid.shape[1] * KEEP_FRACTION)

    samples = []
    for index, frame in enumerate(frame_stream(video)):
        diff = np.abs(grid - normalise(frame).ravel())
        scores = np.partition(diff, keep, axis=1)[:, :keep].mean(axis=1)
        order = np.argsort(scores)
        best, second = int(order[0]), int(order[1])
        samples.append({
            # ffmpeg's fps filter emits the frame at the CENTRE of each output
            # window, not its start. Verified against accurate-seek grabs: index*2
            # is wrong by a second, index*2+1 matches. Getting this wrong puts every
            # interval boundary a second early and would silently misalign the
            # timeline against transcript timestamps.
            "t": round(index * SAMPLE_SECONDS + SAMPLE_SECONDS / 2, 3),
            "page": best + 1,
            "score": round(float(scores[best]), 5),
            "second_page": second + 1,
            "second_score": round(float(scores[second]), 5),
            "margin": round(float(scores[second] - scores[best]), 5),
        })
    return samples


def pair_distances(pages: list[np.ndarray]) -> np.ndarray:
    """Stage-1 distance between every pair of pages. 0-based."""
    grid = [normalise(cv2.resize(p, (GRID_W, GRID_H), interpolation=cv2.INTER_AREA)).ravel()
            for p in pages]
    keep = int(grid[0].size * KEEP_FRACTION)
    n = len(pages)
    out = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(i + 1, n):
            diff = np.abs(grid[i] - grid[j])
            out[i, j] = out[j, i] = float(np.partition(diff, keep)[:keep].mean())
    return out


def discriminative_mask(pages: list[np.ndarray], a: int, b: int) -> np.ndarray:
    """Pixels where two pages actually differ from each other."""
    return np.abs(pages[a].astype(np.int16) - pages[b].astype(np.int16)) > PIXEL_DELTA


def stage2_scores(frame: np.ndarray, pages: list[np.ndarray],
                  candidates: list[int], mask: np.ndarray) -> dict[int, float]:
    """Trimmed-mean distance inside the discriminative region only."""
    fn = normalise(frame)[mask]
    keep = max(1, int(fn.size * KEEP_FRACTION))
    out = {}
    for p in candidates:
        diff = np.abs(normalise(pages[p])[mask] - fn)
        out[p + 1] = float(np.partition(diff, keep - 1)[:keep].mean())
    return out


def full_frame_stream(video: Path, width: int, height: int):
    """Yield sampled frames at full resolution, same sample times as stage 1."""
    cmd = ["ffmpeg", "-v", "error", "-i", str(video),
           "-vf", f"fps={1 / SAMPLE_SECONDS},format=gray", "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    size = width * height
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, dtype=np.uint8).reshape(height, width)
    proc.stdout.close()
    proc.wait()


def percentiles(values: list[float], points=(1, 5, 10, 25, 50, 75, 90, 95, 99)) -> dict:
    arr = np.asarray(values)
    return {f"p{p}": round(float(np.percentile(arr, p)), 5) for p in points}


def resolve(s: dict) -> tuple[int, float, float, str]:
    """Final page for a sample: (page, match score, margin, which stage decided).

    Stage-2 samples keep the stage-1 score of the page stage 2 chose, since that
    is the honest "how well does the whole frame match this page" number. The
    stage-2 margin is the confidence in the page's identity within its template
    cluster, and is not comparable to a stage-1 margin.
    """
    st2 = s.get("stage2")
    if st2 and st2.get("resolvable"):
        score = s["second_score"] if st2["page"] == s["second_page"] else s["score"]
        return st2["page"], score, st2["margin"], "stage2"
    if st2:
        return s["page"], s["score"], 0.0, "unresolvable"
    return s["page"], s["score"], s["margin"], "stage1"


def build_intervals(samples: list[dict], duration: float) -> list[dict]:
    for s in samples:
        s["_page"], s["_score"], s["_margin"], s["_stage"] = resolve(s)

    runs = []
    for s in samples:
        if runs and runs[-1]["page"] == s["_page"]:
            runs[-1]["samples"].append(s)
        else:
            runs.append({"page": s["_page"], "samples": [s]})

    def span(run):
        return len(run["samples"]) * SAMPLE_SECONDS

    def mean_score(run):
        return float(np.mean([s["_score"] for s in run["samples"]]))

    # absorb transitions into whichever neighbour matches better
    while len(runs) > 1:
        short = [i for i, r in enumerate(runs) if span(r) < MIN_INTERVAL_SECONDS]
        if not short:
            break
        i = min(short, key=lambda i: span(runs[i]))
        left = runs[i - 1] if i > 0 else None
        right = runs[i + 1] if i + 1 < len(runs) else None
        target = left if right is None else right if left is None else (
            left if mean_score(left) <= mean_score(right) else right)
        times = [s["t"] for s in runs[i]["samples"]]
        target.setdefault("absorbed", []).append({
            "page": runs[i]["page"],
            "start": round(times[0], 3),
            "end": round(times[-1] + SAMPLE_SECONDS, 3),
            "samples": len(times),
        })
        target["absorbed"] += runs[i].get("absorbed", [])
        target["samples"] = sorted(target["samples"] + runs[i]["samples"],
                                   key=lambda s: s["t"])
        runs.pop(i)
        merged = [runs[0]]
        for r in runs[1:]:
            if r["page"] == merged[-1]["page"]:
                merged[-1]["samples"] += r["samples"]
                merged[-1].setdefault("absorbed", []).extend(r.get("absorbed", []))
            else:
                merged.append(r)
        runs = merged

    intervals = []
    for i, run in enumerate(runs):
        times = [s["t"] for s in run["samples"]]
        # A sample at t represents the window [t - half, t + half], so a boundary
        # sits half a sample period before the first sample of the next run.
        half = SAMPLE_SECONDS / 2
        start = 0.0 if i == 0 else times[0] - half
        end = (runs[i + 1]["samples"][0]["t"] - half if i + 1 < len(runs)
               else duration)
        # Aggregates describe this interval's own page. Samples absorbed from a
        # shorter neighbouring run keep their own identity in "absorbed" and must
        # not drag the host interval's score or margins around.
        own = [s for s in run["samples"] if s["_page"] == run["page"]] or run["samples"]
        by_stage = {st: [s for s in own if s["_stage"] == st]
                    for st in ("stage1", "stage2", "unresolvable")}
        interval = {
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3),
            "page": run["page"],
            "samples": len(run["samples"]),
            "resolved_by": ("stage2" if by_stage["stage2"] and not by_stage["stage1"]
                            else "stage1" if not by_stage["stage2"] else "mixed"),
            # last sample actually showing this page; absorbed runs are excluded, so
            # sampling "the end of the interval" cannot land on a transition frame
            "last_own_sample": round(max(s["t"] for s in own), 3),
            "mean_score": round(float(np.mean([s["_score"] for s in own])), 5),
            "worst_score": round(max(s["_score"] for s in own), 5),
            "worst_sample": round(max(own, key=lambda s: s["_score"])["t"], 3),
            "unresolvable_samples": len(by_stage["unresolvable"]),
            "absorbed": run.get("absorbed", []),
        }
        for st in ("stage1", "stage2"):
            interval[f"min_margin_{st}"] = (
                round(min(s["_margin"] for s in by_stage[st]), 5) if by_stage[st] else None)
        intervals.append(interval)
    return intervals


def clock(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def blank_areas(page: np.ndarray) -> np.ndarray:
    """Deck pixels carrying no content: locally uniform, whatever their colour."""
    gradient = cv2.morphologyEx(page, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8))
    content = cv2.dilate((gradient > DETAIL_LEVEL).astype(np.uint8),
                         np.ones((DETAIL_MARGIN, DETAIL_MARGIN), np.uint8))
    return content == 0


def diagnose_low_score(video: Path, page: np.ndarray, interval: dict) -> dict:
    """Separate live lesson content from a genuine deck/video disagreement.

    Sampled at the interval's worst-scoring frame, which is what raised the flag.
    The last frame is not a safe choice: an instructor who clears annotations
    before moving on leaves a clean slide at the end of the interval.
    """
    at = interval["worst_sample"]
    frame = np.asarray(grab_frame(video, at).convert("L"))
    if frame.shape != page.shape:
        frame = cv2.resize(frame, (page.shape[1], page.shape[0]),
                           interpolation=cv2.INTER_AREA)
    differing = np.abs(frame.astype(np.int16) - page.astype(np.int16)) > PIXEL_DELTA
    total = int(differing.sum())
    in_blank = int((differing & blank_areas(page)).sum())
    fraction = in_blank / total if total else 0.0
    area = total / differing.size
    return {
        "sampled_at": round(at, 3),
        "differing_pixels": total,
        "fraction_of_frame_differing": round(area, 4),
        "fraction_over_empty_deck_areas": round(fraction, 4),
        "verdict": ("possible_mismatch" if area > MISMATCH_AREA
                    else "heavy_live_content" if fraction >= BLANK_MAJORITY
                    else "possible_mismatch"),
    }


def margin_label(iv: dict) -> str:
    if iv["min_margin_stage2"] is not None:
        return (f"stage-2 margin {iv['min_margin_stage2']:.3f}"
                + (f" (+stage-1 {iv['min_margin_stage1']:.3f})"
                   if iv["min_margin_stage1"] is not None else ""))
    return f"margin {iv['min_margin_stage1']:.3f}"


def grab_frame(video: Path, at: float) -> Image.Image:
    """Frame at a given time, seeking accurately.

    A single -ss before -i is a fast seek to the nearest keyframe and can land
    seconds away. Where the screen is changing -- live typing, annotation -- that
    returns a different moment than the one being analysed. Seeking to a few
    seconds earlier and decoding forward costs little and lands on the right frame.
    """
    pre = min(SEEK_DECODE_WINDOW, at)
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{at - pre:.3f}", "-i", str(video),
         "-ss", f"{pre:.3f}", "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
        check=True, capture_output=True,
    ).stdout
    import io
    return Image.open(io.BytesIO(out)).convert("RGB")


def write_checks(video: Path, pdf: Path, intervals: list[dict],
                 out_dir: Path) -> None:
    pages = render_pages_colour(pdf)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.load_default(size=15)
    except TypeError:
        font = ImageFont.load_default()

    panel_h = round(CHECK_W * pages[0].height / pages[0].width)
    gap = 6
    for n, iv in enumerate(intervals):
        last = iv["last_own_sample"]
        middle = (iv["start"] + last) / 2
        panels = [
            (grab_frame(video, middle), f"video @ {clock(middle)} (middle)"),
            (grab_frame(video, last), f"video @ {clock(last)} (end of interval)"),
            (pages[iv["page"] - 1], f"deck page {iv['page']} (clean)"),
        ]

        canvas = Image.new("RGB", (CHECK_W * 3 + gap * 2, panel_h + LABEL_H), "#1a1a1a")
        draw = ImageDraw.Draw(canvas)
        for i, (img, caption) in enumerate(panels):
            x = i * (CHECK_W + gap)
            canvas.paste(img.resize((CHECK_W, panel_h)), (x, LABEL_H))
            draw.text((x + 6, LABEL_H + 4), caption, fill="#9aa0a6", font=font)

        flag = "  LOW CONFIDENCE: " + ", ".join(iv["flags"]) if iv["low_confidence"] else ""
        draw.text((6, 9),
                  f"{clock(iv['start'])}-{clock(iv['end'])}   page {iv['page']}   "
                  f"score {iv['mean_score']:.3f}   {margin_label(iv)}{flag}",
                  fill="#ff6b6b" if iv["low_confidence"] else "#e8e8e8", font=font)
        canvas.save(out_dir / f"{n:03d}_p{iv['page']:02d}.png")

    low = sum(1 for iv in intervals if iv["low_confidence"])
    rows = []
    for n, iv in enumerate(intervals):
        cls = " low" if iv["low_confidence"] else ""
        badge = (f'<span class="badge">{" / ".join(iv["flags"])}</span>'
                 if iv["low_confidence"] else "")
        rows.append(f"""  <figure class="shot{cls}">
    <figcaption><b>{clock(iv['start'])} – {clock(iv['end'])}</b>
      &nbsp; page {iv['page']} &nbsp; score {iv['mean_score']:.3f}
      &nbsp; {margin_label(iv)} &nbsp; {iv['duration']:.0f}s
      &nbsp; <span class="by">resolved by {iv['resolved_by']}</span> {badge}</figcaption>
    <img src="{n:03d}_p{iv['page']:02d}.png" loading="lazy" alt="interval {n}">
  </figure>""")

    html = f"""<!doctype html>
<meta charset="utf-8">
<title>Slide timeline check</title>
<style>
  body {{ background:#141414; color:#e8e8e8; font:14px system-ui,sans-serif; margin:0 auto; padding:24px; max-width:1400px; }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .meta {{ color:#9aa0a6; margin-bottom:24px; }}
  .shot {{ margin:0 0 28px; }}
  .shot img {{ width:100%; height:auto; display:block; border:2px solid #2a2a2a; }}
  .shot.low img {{ border-color:#ff6b6b; }}
  figcaption {{ padding:6px 0; }}
  .badge {{ background:#ff6b6b; color:#141414; font-weight:700; padding:2px 8px; border-radius:3px; }}
  .by {{ color:#9aa0a6; }}
</style>
<h1>Slide timeline check</h1>
<div class="meta">{len(intervals)} intervals, {low} flagged low confidence.
Each row: the frame from the middle of the interval, the frame at its end with
annotations accumulated, and the clean deck page it was matched to.</div>
{chr(10).join(rows)}
"""
    (out_dir / "index.html").write_text(html, encoding="utf-8")


def run_stage2(video: Path, pdf: Path, scores_path: Path,
               width: int, height: int) -> None:
    """Re-score template-sharing candidates inside their differing regions."""
    cached = json.loads(scores_path.read_text(encoding="utf-8"))
    samples = cached["samples"]
    pages = render_pages(pdf)
    dist = pair_distances(pages)

    def pair_of(s):
        a, b = s["page"] - 1, s["second_page"] - 1
        return (a, b) if dist[a, b] < PAIR_SIMILARITY else None

    masks: dict[tuple[int, int], np.ndarray] = {}
    todo = {i for i, s in enumerate(samples) if pair_of(s)}
    used = sorted({tuple(sorted(pair_of(s))) for s in samples if pair_of(s)})
    print(f"candidate pairs sharing a template (stage-1 distance < {PAIR_SIMILARITY}):")
    for a, b in used:
        mask = discriminative_mask(pages, a, b)
        masks[(a, b)] = mask
        pixels = int(mask.sum())
        print(f"  pages {a + 1:2d} vs {b + 1:2d}: distance {dist[a, b]:.4f}, "
              f"{pixels:6d} discriminative pixels ({100 * pixels / mask.size:5.2f}% of frame)"
              f"{'  -- NO discriminative region' if pixels < MIN_MASK_PIXELS else ''}")
    print(f"\n{len(todo)} of {len(samples)} samples need stage 2")

    resolved = 0
    for index, frame in enumerate(full_frame_stream(video, width, height)):
        if index >= len(samples) or index not in todo:
            continue
        s = samples[index]
        a, b = pair_of(s)
        mask = masks[tuple(sorted((a, b)))]
        candidates = [a, b]
        if int(mask.sum()) < MIN_MASK_PIXELS:
            s["stage2"] = {"candidates": [a + 1, b + 1], "resolvable": False}
            continue
        scores = stage2_scores(frame, pages, candidates, mask)
        ranked = sorted(scores.items(), key=lambda kv: kv[1])
        s["stage2"] = {
            "candidates": [a + 1, b + 1],
            "resolvable": True,
            "page": ranked[0][0],
            "score": round(ranked[0][1], 5),
            "runner_up": ranked[1][0],
            "margin": round(ranked[1][1] - ranked[0][1], 5),
            "changed": ranked[0][0] != s["page"],
        }
        resolved += 1

    cached["template_pairs"] = [[a + 1, b + 1, round(float(dist[a, b]), 5)] for a, b in used]
    cached["stage2_parameters"] = {
        "pair_similarity": PAIR_SIMILARITY,
        "pixel_delta": PIXEL_DELTA,
        "min_mask_pixels": MIN_MASK_PIXELS,
    }
    scores_path.write_text(json.dumps(cached, indent=1), encoding="utf-8")

    changed = sum(1 for s in samples if s.get("stage2", {}).get("changed"))
    margins = [s["stage2"]["margin"] for s in samples if s.get("stage2", {}).get("resolvable")]
    print(f"stage 2 scored {resolved} samples, changed the page on {changed}")
    if margins:
        print("\nstage-2 margin distribution:")
        for k, v in percentiles(margins).items():
            print(f"  {k:>4}  {v:.4f}")
    unresolvable = [s for s in samples if s.get("stage2", {}).get("resolvable") is False]
    if unresolvable:
        pairs = sorted({tuple(s["stage2"]["candidates"]) for s in unresolvable})
        print(f"\n{len(unresolvable)} samples whose candidate pages are identical "
              f"and cannot be separated by pixels: pairs {pairs}")


def main() -> None:
    lesson = Path(sys.argv[1])
    video = lesson / "source" / "video.mp4"
    pdf = lesson / "source" / "slides.pdf"
    out_dir = lesson / "analysis" / "slides"
    out_dir.mkdir(parents=True, exist_ok=True)
    scores_path = out_dir / "slide_scores.json"

    duration, width, height = video_info(video)
    score_max = opt("--score-max")
    margin_min = opt("--margin-min")

    if "--stage2" in sys.argv:
        run_stage2(video, pdf, scores_path, width, height)
        return

    if score_max is None or margin_min is None:
        pages = render_pages(pdf)
        print(f"video {width}x{height}  {clock(duration)}  |  deck {len(pages)} pages")
        print(f"sampling every {SAMPLE_SECONDS:g}s, comparing at {GRID_W}x{GRID_H}, "
              f"keeping best {KEEP_FRACTION:.0%} of cells")
        samples = score_all(video, pages)
        scores_path.write_text(json.dumps({
            "video": str(video), "pdf": str(pdf),
            "duration": duration, "pages": len(pages),
            "sample_seconds": SAMPLE_SECONDS, "grid": [GRID_W, GRID_H],
            "keep_fraction": KEEP_FRACTION,
            "samples": samples,
        }, indent=1), encoding="utf-8")

        print(f"\n{len(samples)} samples -> {scores_path}\n")
        print("match score (lower is better):")
        for k, v in percentiles([s["score"] for s in samples]).items():
            print(f"  {k:>4}  {v:.4f}")
        print("\nmargin over runner-up (higher is better):")
        for k, v in percentiles([s["margin"] for s in samples]).items():
            print(f"  {k:>4}  {v:.4f}")
        print("\nRe-run with --score-max S --margin-min M to build the timeline.")
        return

    score_max, margin_min = float(score_max), float(margin_min)
    margin_min_stage2 = float(opt("--margin-min-stage2", "0.05"))
    cached = json.loads(scores_path.read_text(encoding="utf-8"))
    intervals = build_intervals(cached["samples"], duration)
    rendered = render_pages(pdf)
    for iv in intervals:
        reasons = []
        if iv["mean_score"] > score_max:
            iv["low_score_diagnosis"] = diagnose_low_score(
                video, rendered[iv["page"] - 1], iv)
            reasons.append(f"low_score: {iv['low_score_diagnosis']['verdict']}")
        if iv["min_margin_stage1"] is not None and iv["min_margin_stage1"] < margin_min:
            reasons.append("thin stage-1 margin")
        if iv["min_margin_stage2"] is not None and iv["min_margin_stage2"] < margin_min_stage2:
            reasons.append("thin stage-2 margin")
        if iv["unresolvable_samples"]:
            reasons.append("identical candidate pages")
        iv["low_confidence"] = bool(reasons)
        iv["flags"] = reasons

    dist = pair_distances(rendered)

    seen = {iv["page"] for iv in intervals}
    won_any = {s["_page"] for s in cached["samples"]}
    all_pages = range(1, cached["pages"] + 1)
    # A page that won samples but never held the screen for MIN_INTERVAL_SECONDS
    # was absorbed as a transition. That is not the same as never appearing.
    unmatched = [p for p in all_pages if p not in won_any]
    only_short = [p for p in all_pages if p in won_any and p not in seen]
    # A page identical to an earlier one can never win: argmin takes the lower index.
    identical = {p: [j + 1 for j in range(len(rendered))
                     if j + 1 != p and dist[p - 1, j] < 1e-4]
                 for p in unmatched}
    identical = {p: v for p, v in identical.items() if v}
    # reported, never used to decide: decks normally advance in order
    backwards = [{"at": iv["start"], "from": intervals[i - 1]["page"], "to": iv["page"]}
                 for i, iv in enumerate(intervals)
                 if i and iv["page"] < intervals[i - 1]["page"]]

    timeline = {
        "video": str(video), "pdf": str(pdf),
        "video_size": [width, height], "duration": round(duration, 3),
        "pages": cached["pages"],
        "method": ("trimmed-mean absolute difference of contrast-normalised "
                   "greyscale; deterministic, no AI"),
        "parameters": {
            "sample_seconds": SAMPLE_SECONDS, "grid": [GRID_W, GRID_H],
            "keep_fraction": KEEP_FRACTION,
            "min_interval_seconds": MIN_INTERVAL_SECONDS,
            "score_max": score_max, "margin_min": margin_min,
            "margin_min_stage2": margin_min_stage2,
            "pair_similarity": PAIR_SIMILARITY,
            "pixel_delta": PIXEL_DELTA,
        },
        "template_pairs": cached.get("template_pairs", []),
        "intervals": intervals,
        "pages_never_on_screen": unmatched,
        "pages_only_in_short_runs": only_short,
        "pages_identical_to_another": identical,
        "page_order_regressions": backwards,
    }
    (out_dir / "slide_timeline.json").write_text(
        json.dumps(timeline, indent=1), encoding="utf-8")

    if "--no-checks" not in sys.argv:
        write_checks(video, pdf, intervals, out_dir / "checks")

    print(f"{len(intervals)} intervals, "
          f"{sum(1 for i in intervals if i['low_confidence'])} low confidence")
    print(f"pages never on screen: {unmatched or 'none'}"
          + (f"  (identical to: {identical})" if identical else ""))
    print(f"pages only in short runs, absorbed: {only_short or 'none'}")
    print(f"{out_dir / 'slide_timeline.json'}")


if __name__ == "__main__":
    main()
