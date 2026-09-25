"""Extract timestamped annotation events from a lesson recording.

Usage:
  .venv/Scripts/python extract_annotations.py <lesson_dir> [--measure-baseline]

Geometry and timing only. No interpretation, no semantic labels (methodology §5, §7).

Reads  <lesson_dir>/source/video.mp4, source/slides.pdf
       <lesson_dir>/analysis/slides/slide_timeline.json   interval boundaries
Writes <lesson_dir>/analysis/annotations/annotation_events.json
       <lesson_dir>/analysis/annotations/checks/index.html

Baseline: per-pixel median of the first frames of each interval. Measured against
the two alternatives on four intervals (--measure-baseline): the deck render
carries 5-10k px of colour/compression residual per slide, and the first frame is
contaminated by ink left over from the previous slide.

Carry-over: the annotation tool draws on the screen, not on the slide, so ink from
the previous slide stays visible after a slide change until it is erased. Ink at an
interval start that overlaps ink at the previous interval's end is attributed to the
previous interval and never resolved against the new slide's words.
"""

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import pypdfium2 as pdfium
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_slide_timeline as timeline   # noqa: E402  accurate seek, renders, blank areas

SAMPLE_SECONDS = 1.0       # finer than the slide timeline: typing grows between slides
DIFF_THRESHOLD = 30        # max-channel difference counting as changed
OPEN_KERNEL = 3            # morphological opening, kills single-pixel noise
MIN_BLOB_AREA = 60         # px, below this is not an annotation
LINK_DILATION = 9          # px, blobs this close across frames are the same annotation

BASELINE_FRAMES = 5        # frames whose median forms the baseline
PROBE_INDEX = 10           # probe sample for --measure-baseline, clear of the baseline

MIN_EVENT_AREA = 150       # px, an annotation event must reach this size
MIN_EVENT_SAMPLES = 2      # and must survive this many consecutive samples.
                           # Without both, JPEG flicker around standing ink and the
                           # cursor's own redraw register as thousands of events.

CURSOR_MAX_AREA = 1500     # px, above this a blob is too big to be a cursor
CURSOR_AREA_CV = 0.15      # a held cursor has a near-constant footprint; ink grows
DWELL_MIN_SAMPLES = 3      # samples a stationary cursor must hold to count as a dwell
DWELL_MAX_SPREAD = 4500    # px, a dwell that wanders further than this is a move
BULK_ERASE_FRACTION = 0.5  # share of standing ink vanishing at once...
BULK_ERASE_MIN_PX = 5000   # ...but never call a few hundred stray pixels an erasure

CARRY_OVERLAP = 0.5        # share of a start-of-interval blob that must sit on the
                           # previous interval's ink to count as carry-over

TOOLBAR_MIN_AREA = 10000   # px in the bottom band that means the viewer bar is showing
CHROME_FRAMES = 40         # frames sampled across the lesson to find the bar

TEMPLATE_MAX_SIDE = 40     # px, cursor glyphs are small; ignore anything larger
TEMPLATE_MIN_SEEN = 20     # times a shape must recur among moving-cursor blobs
TEMPLATE_IOU = 0.70        # overlap with a harvested cursor shape that means cursor
TEMPLATE_KEEP = 8          # distinct shapes to keep

TARGET_UNDER_PX = 25       # an event this far below a word counts as sitting under it
TARGET_OVERLAP = 0.5       # share of event width that must overlap the word's columns


def sample_time(index: int, period: float = SAMPLE_SECONDS) -> float:
    """ffmpeg's fps filter emits the frame at the centre of each output window."""
    return index * period + period / 2


def changed_mask(frame: np.ndarray, baseline: np.ndarray) -> np.ndarray:
    diff = np.abs(frame.astype(np.int16) - baseline.astype(np.int16))
    mask = (diff.max(axis=2) if diff.ndim == 3 else diff) > DIFF_THRESHOLD
    kernel = np.ones((OPEN_KERNEL, OPEN_KERNEL), np.uint8)
    return cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, kernel).astype(bool)


def blobs_of(mask: np.ndarray, min_area: int = MIN_BLOB_AREA) -> list[dict]:
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area >= min_area:
            out.append({"bbox": [int(x), int(y), int(w), int(h)], "area": int(area),
                        "mask": labels == i})
    return out


def page_of(intervals: list[dict], t: float) -> dict | None:
    for iv in intervals:
        if iv["start"] <= t < iv["end"]:
            return iv
    return None


def in_absorbed(iv: dict, t: float) -> bool:
    """True while a short run from a different page is on screen inside this interval.

    The slide timeline absorbs runs shorter than its transition floor into the
    neighbouring interval. Those frames show a different slide, so differencing
    them against this interval's baseline -- or worse, building the baseline from
    them -- turns the other slide's own artwork into annotation events.
    """
    return any(a["start"] <= t < a["end"] for a in iv.get("absorbed", []))


def frame_stream(video: Path, width: int, height: int):
    """Sampled RGB frames, one decode pass."""
    cmd = ["ffmpeg", "-v", "error", "-i", str(video),
           "-vf", f"fps={1 / SAMPLE_SECONDS},{timeline.to_render_size(video)}format=rgb24",
           "-f", "rawvideo", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    size = width * height * 3
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 3)
    proc.stdout.close()
    proc.wait()


def find_toolbar(video: Path, pdf: Path, intervals: list[dict],
                 duration: float, height: int) -> dict | None:
    """The viewer's control bar. It auto-hides, so look for it where it is showing."""
    pages = [np.asarray(p) for p in timeline.render_pages_colour(pdf)]
    band_top = int(height * 0.85)
    boxes = []
    for i in range(CHROME_FRAMES):
        t = duration * (i + 0.5) / CHROME_FRAMES
        iv = page_of(intervals, t)
        if iv is None:
            continue
        mask = changed_mask(np.asarray(timeline.grab_frame(video, t)),
                            pages[iv["page"] - 1])
        band = np.zeros_like(mask)
        band[band_top:, :] = True
        for blob in blobs_of(mask & band, TOOLBAR_MIN_AREA):
            boxes.append(blob["bbox"])
    if not boxes:
        return None
    x = min(b[0] for b in boxes)
    y = min(b[1] for b in boxes)
    w = max(b[0] + b[2] for b in boxes) - x
    h = max(b[1] + b[3] for b in boxes) - y
    return {"bbox": [x, y, w, h], "seen_in_frames": len(boxes), "of_frames": CHROME_FRAMES}


def word_boxes(pdf: Path, width: int) -> list[list[dict]]:
    """Word boxes per page, converted from PDF points to video pixels."""
    doc = pdfium.PdfDocument(pdf)
    pages = []
    for i in range(len(doc)):
        page = doc[i]
        scale = width / page.get_width()
        page_h = page.get_height()
        tp = page.get_textpage()
        words, current, box = [], "", None
        for c in range(tp.count_chars()):
            ch = tp.get_text_range(c, 1)
            if ch.strip():
                left, bottom, right, top = tp.get_charbox(c)
                cb = [left * scale, (page_h - top) * scale,
                      right * scale, (page_h - bottom) * scale]
                box = cb if box is None else [min(box[0], cb[0]), min(box[1], cb[1]),
                                              max(box[2], cb[2]), max(box[3], cb[3])]
                current += ch
            elif current:
                words.append({"text": current, "box": [round(v, 1) for v in box]})
                current, box = "", None
        if current:
            words.append({"text": current, "box": [round(v, 1) for v in box]})
        pages.append(words)
    return pages


def targets_for(bbox: list[int], words: list[dict]) -> list[str]:
    """Words the event overlaps, plus words it sits directly under."""
    x, y, w, h = bbox
    hits = []
    for word in words:
        wx0, wy0, wx1, wy1 = word["box"]
        overlaps = not (x + w < wx0 or x > wx1 or y + h < wy0 or y > wy1)
        columns = min(x + w, wx1) - max(x, wx0)
        under = (columns >= TARGET_OVERLAP * w and 0 <= y - wy1 <= TARGET_UNDER_PX)
        if overlaps or under:
            hits.append(word["text"])
    return hits


def classify(track: dict, interval_end_t: float) -> str:
    """Ink, or a cursor that was moving or being held still.

    Ink only leaves the screen through erasure. A held cursor vanishes on its own
    and keeps a near-constant footprint, where drawn or typed ink grows.
    """
    areas = np.asarray(track["areas"], dtype=np.float32)
    lifetime = track["last_seen"] - track["first_seen"]
    if areas.max() > CURSOR_MAX_AREA:
        return "ink"
    if track["erased"]:
        return "ink"
    if track["last_seen"] >= interval_end_t - SAMPLE_SECONDS:
        return "ink"                       # still standing when the slide changed
    if len(areas) < 2:
        return "cursor_moving"
    cv = float(areas.std() / max(areas.mean(), 1e-6))
    if cv < CURSOR_AREA_CV:
        return "cursor_held"               # steady footprint, vanished without erasure
    return "ink"


def new_interval(iv: dict, index: int) -> dict:
    return {"iv": iv, "index": index, "buffer": [], "baseline": None, "tracks": [],
            "closed": [], "removals": [], "prev_mask": None, "union": None,
            "colour": None, "final_mask": None, "carry": None, "carry_mask": None,
            "static_frames": 0, "frames": 0, "noise": []}


def start_tracks(state: dict, blobs: list[dict], t: float) -> None:
    for blob in blobs:
        x, y, w, h = blob["bbox"]
        state["tracks"].append({
            "first_seen": t, "last_seen": t, "areas": [blob["area"]],
            "bbox": list(blob["bbox"]), "mask": blob["mask"], "erased": False,
            "acc_bbox": [x, y, w, h],
            "acc": blob["mask"][y:y + h, x:x + w].copy()})


def merge_bbox(a: list[int], b: list[int]) -> list[int]:
    x0, y0 = min(a[0], b[0]), min(a[1], b[1])
    x1, y1 = max(a[0] + a[2], b[0] + b[2]), max(a[1] + a[3], b[1] + b[3])
    return [x0, y0, x1 - x0, y1 - y0]


def near(a: list[int], b: list[int], pad: int = LINK_DILATION) -> bool:
    return not (a[0] + a[2] + pad < b[0] or b[0] + b[2] + pad < a[0]
                or a[1] + a[3] + pad < b[1] or b[1] + b[3] + pad < a[1])


def step(state: dict, frame: np.ndarray, t: float, excluded: np.ndarray,
         chrome: dict) -> None:
    mask = changed_mask(frame, state["baseline"]) & ~excluded
    # The viewer's control bar auto-hides, so it cannot be found by sampling a
    # handful of frames. Every frame is decoded here anyway: suppress the bar on
    # the frames where it is actually showing, and report where it was seen.
    top = chrome["band_top"]
    if mask[top:, :].sum() >= TOOLBAR_MIN_AREA:
        for blob in blobs_of(mask[top:, :], TOOLBAR_MIN_AREA):
            x, y, w, h = blob["bbox"]
            chrome["boxes"].append([x, y + top, w, h])
        mask[top:, :] = False
    blobs = blobs_of(mask)
    state["frames"] += 1

    if state["union"] is None:
        state["union"] = np.zeros(mask.shape, bool)
        state["ink_union"] = np.zeros(mask.shape, bool)
        state["colour"] = np.zeros(frame.shape, np.uint8)
    fresh = mask & ~state["union"]
    state["colour"][fresh] = frame[fresh]
    state["union"] |= mask
    state["final_mask"] = mask

    prev = state["prev_mask"]
    if prev is not None:
        removed = int((prev & ~mask).sum())
        standing = int(prev.sum())
        bulk = (removed >= BULK_ERASE_FRACTION * max(standing, 1)
                and removed >= BULK_ERASE_MIN_PX)
    else:
        bulk = False

    matched = set()
    for blob in blobs:
        hit = None
        for track in state["tracks"]:
            if near(track["bbox"], blob["bbox"]) and (track["mask"] & blob["mask"]).any():
                hit = track
                break
        if hit is None:
            start_tracks(state, [blob], t)
        else:
            hit["last_seen"] = t
            hit["areas"].append(blob["area"])
            hit["bbox"] = merge_bbox(hit["bbox"], blob["bbox"])
            hit["mask"] = blob["mask"]
            nb = merge_bbox(hit["acc_bbox"], blob["bbox"])
            if nb != hit["acc_bbox"]:
                grown = np.zeros((nb[3], nb[2]), bool)
                ox, oy, ow, oh = hit["acc_bbox"]
                grown[oy - nb[1]:oy - nb[1] + oh, ox - nb[0]:ox - nb[0] + ow] = hit["acc"]
                hit["acc"], hit["acc_bbox"] = grown, nb
            ax, ay, aw, ah = hit["acc_bbox"]
            hit["acc"] |= blob["mask"][ay:ay + ah, ax:ax + aw]
            matched.add(id(hit))

    still_open = []
    for track in state["tracks"]:
        if id(track) in matched or track["last_seen"] == t:
            still_open.append(track)
        else:
            track["erased"] = bulk or max(track["areas"]) > CURSOR_MAX_AREA
            track["gone_at"] = t
            track["bulk"] = bulk
            state["closed"].append(track)
    if len(still_open) == len(state["tracks"]) and blobs:
        state["static_frames"] += 1
    state["tracks"] = still_open
    state["prev_mask"] = mask


def detect_carry_over(state: dict, first_frame: np.ndarray, page_rgb: np.ndarray,
                      page_blank: np.ndarray, prev_end_ink: np.ndarray | None,
                      excluded: np.ndarray) -> None:
    """Ink at the interval start that was already on screen at the end of the last one."""
    state["carry"] = []
    state["carry_mask"] = np.zeros(page_blank.shape, bool)
    if prev_end_ink is None:
        return
    candidates = changed_mask(first_frame, page_rgb) & page_blank & ~excluded
    for blob in blobs_of(candidates):
        overlap = float((blob["mask"] & prev_end_ink).sum()) / blob["area"]
        if overlap >= CARRY_OVERLAP:
            state["carry"].append({"bbox": blob["bbox"], "area_px": blob["area"],
                                   "overlap_with_previous": round(overlap, 3)})
            state["carry_mask"] |= cv2.dilate(blob["mask"].astype(np.uint8),
                                              np.ones((LINK_DILATION,) * 2, np.uint8)).astype(bool)


def dominant_colour(state: dict, bbox: list[int]) -> list[int]:
    x, y, w, h = bbox
    region = state["union"][y:y + h, x:x + w]
    pixels = state["colour"][y:y + h, x:x + w][region]
    if not len(pixels):
        return [0, 0, 0]
    return [int(v) for v in np.median(pixels, axis=0)]


def crop_shape(track: dict) -> tuple[int, int, np.ndarray] | None:
    """A track's accumulated pixels, trimmed to their own bounding box."""
    acc = track.get("acc")
    if acc is None or not acc.any():
        return None
    ys, xs = np.where(acc)
    sub = acc[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = sub.shape
    if max(h, w) > TEMPLATE_MAX_SIDE:
        return None
    return w, h, sub


def shape_iou(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        return 0.0
    union = (a | b).sum()
    return float((a & b).sum() / union) if union else 0.0


def finish_interval(state: dict, words: list[dict], text_layer: str,
                    events: list[dict], dwells: list[dict], counts: dict,
                    harvest: dict) -> np.ndarray:
    iv = state["iv"]
    end_t = iv["end"]
    for track in state["tracks"]:
        track["erased"] = False
        state["closed"].append(track)
    state["tracks"] = []

    ink_boxes = []
    for track in state["closed"]:
        kind = classify(track, end_t)
        x, y, w, h = track["bbox"]
        area = int(max(track["areas"]))
        if kind == "ink" and (area < MIN_EVENT_AREA
                              or len(track["areas"]) < MIN_EVENT_SAMPLES):
            counts["noise"] = counts.get("noise", 0) + 1
            if (area < MIN_EVENT_AREA
                    and track["last_seen"] - track["first_seen"] >= 5.0):
                harvest["small_but_persistent"] += 1
            continue
        if kind == "cursor_moving":
            shape = crop_shape(track)
            if shape:
                harvest["cursor_shapes"].append(shape)
        counts[kind] = counts.get(kind, 0) + 1
        if kind == "ink":
            track["emitted_ink"] = True
            ax, ay, aw, ah = track["acc_bbox"]
            state["ink_union"][ay:ay + ah, ax:ax + aw] |= track["acc"]
            if area <= CURSOR_MAX_AREA:
                shape = crop_shape(track)
                if shape:
                    harvest["ink_shapes"].append((len(events), shape))
            ink_boxes.append(track["bbox"])
            target = targets_for(track["bbox"], words)
            events.append({
                "interval": state["index"], "page": iv["page"], "kind": "add",
                "start": round(track["first_seen"], 2),
                "end": round(track["last_seen"] if track["erased"] else end_t, 2),
                "erased": bool(track["erased"]),
                "bbox": [int(x), int(y), int(w), int(h)], "area_px": area,
                "dominant_colour": dominant_colour(state, track["bbox"]),
                "aspect_ratio": round(w / max(h, 1), 3),
                "fill_ratio": round(area / max(w * h, 1), 3),
                "page_text_layer": text_layer,
                "target_words": target if text_layer != "none" else [],
                "target": ("unresolved" if text_layer == "none" or not target
                           else "resolved"),
            })
        elif kind == "cursor_held":
            samples = len(track["areas"])
            if samples >= DWELL_MIN_SAMPLES and w * h <= DWELL_MAX_SPREAD:
                counts["dwell"] = counts.get("dwell", 0) + 1
                under = targets_for(track["bbox"], words)
                dwells.append({
                    "interval": state["index"], "page": iv["page"],
                    "start": round(track["first_seen"], 2),
                    "end": round(track["last_seen"], 2),
                    "position": [int(x + w // 2), int(y + h // 2)],
                    "area_px": area,
                    "page_text_layer": text_layer,
                    "words_under": under if text_layer != "none" else [],
                })

    # One removal per erased annotation, not per connected component per frame:
    # a removal is the disappearance of something that was tracked, so removals
    # can never outnumber the things they remove.
    for track in state["closed"]:
        if not track.get("emitted_ink") or not track["erased"]:
            continue
        x, y, w, h = track["bbox"]
        counts["remove"] = counts.get("remove", 0) + 1
        events.append({
            "interval": state["index"], "page": iv["page"], "kind": "remove",
            "start": round(track.get("gone_at", end_t), 2),
            "end": round(track.get("gone_at", end_t), 2),
            "removes_added_at": round(track["first_seen"], 2),
            "bbox": [int(x), int(y), int(w), int(h)],
            "area_px": int(max(track["areas"])),
            "bulk_erase": bool(track.get("bulk", False)),
            "page_text_layer": text_layer,
            "target_words": [], "target": "not-applicable",
        })

    final = state["final_mask"] if state["final_mask"] is not None else np.zeros(
        state["union"].shape, bool)
    return state["ink_union"] & ~final


def render_check(state: dict, erased: np.ndarray, page_rgb: np.ndarray) -> Image.Image:
    """Union of every annotation in the interval, erased regions tinted."""
    canvas = np.asarray(page_rgb).copy()
    canvas = (canvas * 0.35 + 255 * 0.65).astype(np.uint8)     # fade the slide back
    union = state["ink_union"]
    canvas[union] = state["colour"][union]
    tint = erased & union
    canvas[tint] = (canvas[tint] * 0.4 + np.array([255, 60, 60]) * 0.6).astype(np.uint8)
    return Image.fromarray(canvas)


def measure_baseline(lesson: Path) -> None:
    """Evidence for the baseline choice. Prints tables, writes nothing."""
    video = lesson / "source" / "video.mp4"
    pdf = lesson / "source" / "slides.pdf"
    data = json.loads((lesson / "analysis" / "slides" / "slide_timeline.json")
                      .read_text(encoding="utf-8"))
    intervals, duration = data["intervals"], data["duration"]
    width, height = data["video_size"]

    toolbar = find_toolbar(video, pdf, intervals, duration, height)
    excluded = np.zeros((height, width), bool)
    if toolbar:
        x, y, w, h = toolbar["bbox"]
        excluded[y:y + h, x:x + w] = True
        print("viewer control bar at " + str(toolbar["bbox"]) + ", seen in "
              + str(toolbar["seen_in_frames"]) + " of " + str(toolbar["of_frames"])
              + " sampled frames\n")

    pages_rgb = [np.asarray(p) for p in timeline.render_pages_colour(pdf)]
    pages_grey = timeline.render_pages(pdf)
    ok = ~excluded

    chosen = sorted(intervals, key=lambda iv: -iv["duration"])[:4]
    chosen += [iv for iv in intervals if iv["page"] == 18 and iv not in chosen]
    chosen.sort(key=lambda iv: iv["start"])

    def baselines(iv):
        first = np.asarray(timeline.grab_frame(video, iv["start"] + sample_time(0)))
        stack = np.stack([np.asarray(timeline.grab_frame(video, iv["start"] + sample_time(i)))
                          for i in range(BASELINE_FRAMES)])
        return first, np.median(stack, axis=0).astype(np.uint8)

    print("TABLE 1  render fidelity -- changed pixels on a probe frame "
          + format(sample_time(PROBE_INDEX), ".1f") + " s in,")
    print("         outside the " + str(BASELINE_FRAMES)
          + " frames forming baseline C")
    print("%5s %8s %15s %15s %15s" % ("page", "probe@", "A first frame",
                                      "B deck render", "C median of 5"))
    totals = np.zeros(3, dtype=np.int64)
    for iv in chosen:
        first, median = baselines(iv)
        probe_t = iv["start"] + sample_time(PROBE_INDEX)
        probe = np.asarray(timeline.grab_frame(video, probe_t))
        row = [int((changed_mask(probe, b) & ok).sum())
               for b in (first, pages_rgb[iv["page"] - 1], median)]
        totals += row
        print("%5d %8.1f %15s %15s %15s" % (iv["page"], probe_t, format(row[0], ","),
                                            format(row[1], ","), format(row[2], ",")))
    print("%5s %8s %15s %15s %15s\n" % ("total", "", format(int(totals[0]), ","),
                                        format(int(totals[1]), ","),
                                        format(int(totals[2]), ",")))

    print("TABLE 2  baseline contamination -- ink-like pixels already present,")
    print("         measured against the deck inside deck-empty areas")
    print("%5s %14s %14s  %s" % ("page", "first frame", "median of 5", "blobs in first frame"))
    for iv in chosen:
        page = iv["page"] - 1
        blank = timeline.blank_areas(pages_grey[page]) & ok
        first, median = baselines(iv)
        dirty = changed_mask(first, pages_rgb[page]) & blank
        dirty_median = changed_mask(median, pages_rgb[page]) & blank
        blobs = [b["area"] for b in blobs_of(dirty)]
        extra = (", largest " + format(max(blobs), ",") + "px") if blobs else ""
        print("%5d %14s %14s  %d blobs >= %dpx%s"
              % (iv["page"], format(int(dirty.sum()), ","),
                 format(int(dirty_median.sum()), ","), len(blobs), MIN_BLOB_AREA, extra))


def write_checks(out_dir: Path, cards: list[dict], events: list[dict],
                 dwells: list[dict]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for card in cards:
        own = [e for e in events if e["interval"] == card["index"]]
        adds = [e for e in own if e["kind"] == "add"]
        rems = [e for e in own if e["kind"] == "remove"]
        mine = [d for d in dwells if d["interval"] == card["index"]]
        lines = []
        for e in sorted(own, key=lambda e: e["start"]):
            colour = ("rgb(%d,%d,%d)" % tuple(e["dominant_colour"])
                      if e["kind"] == "add" else "#ff6b6b")
            if e["target_words"]:
                target = ", ".join(e["target_words"][:6])
            elif e["target"] == "unresolved":
                target = "<i>unresolved</i>"
            else:
                target = "&mdash;"
            erased = " (erased)" if e.get("erased") else ""
            lines.append(
                "<tr><td><span class='sw' style='background:" + colour + "'></span>"
                + e["kind"] + erased + "</td><td>"
                + timeline.clock(e["start"]) + "&ndash;" + timeline.clock(e["end"])
                + "</td><td>" + format(e["area_px"], ",") + "</td><td>"
                + str(e.get("aspect_ratio", "&mdash;")) + "</td><td>"
                + str(e.get("fill_ratio", "&mdash;")) + "</td><td>" + target
                + "</td></tr>")
        carry = ""
        if card["carry"]:
            bits = ", ".join(
                format(c["area_px"], ",") + " px (overlap "
                + format(c["overlap_with_previous"], ".0%") + ")" for c in card["carry"])
            carry = "<p class='carry'>carry-over from the previous slide: " + bits + "</p>"
        body = "".join(lines) or "<tr><td colspan=6><i>no events</i></td></tr>"
        rows.append(
            "<section><h2>" + timeline.clock(card["start"]) + " &ndash; "
            + timeline.clock(card["end"]) + " &nbsp; page " + str(card["page"])
            + " <small>" + str(len(adds)) + " added, " + str(len(rems)) + " removed, "
            + str(len(mine)) + " cursor dwells, text layer " + card["text_layer"]
            + "</small></h2>" + carry
            + "<img src='" + card["image"] + "' loading='lazy' alt='interval "
            + str(card["index"]) + "'>"
            + "<table><tr><th>kind</th><th>time</th><th>area</th><th>aspect</th>"
            + "<th>fill</th><th>words overlapped / under</th></tr>" + body
            + "</table></section>")

    style = """<style>
 body{background:#141414;color:#e8e8e8;font:14px system-ui,sans-serif;margin:0 auto;padding:24px;max-width:1280px}
 h1{font-size:20px} h2{font-size:15px;font-weight:600;margin:0 0 8px}
 h2 small{color:#9aa0a6;font-weight:400;margin-left:8px}
 section{margin:0 0 34px;border-top:1px solid #2a2a2a;padding-top:14px}
 img{width:100%;height:auto;border:1px solid #2a2a2a;display:block;margin-bottom:8px}
 table{border-collapse:collapse;width:100%;font-size:13px}
 th,td{text-align:left;padding:3px 8px;border-bottom:1px solid #222}
 th{color:#9aa0a6;font-weight:600}
 .sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;border:1px solid #444}
 .carry{color:#ffb86b;margin:0 0 8px}
 .legend{color:#9aa0a6;margin-bottom:20px}
</style>"""
    legend = ("<p class='legend'>Each image is the union of every annotation that "
              "appeared during the interval, over a faded slide. Regions tinted "
              "<span style='color:#ff6b6b'>red</span> were erased before the slide "
              "changed. Cursor dwells are listed in <code>annotation_events.json</code>, "
              "not drawn here.</p>")
    html = ("<!doctype html><meta charset='utf-8'><title>Annotation events</title>"
            + style + "<h1>Annotation events</h1>" + legend + "".join(rows))
    (out_dir / "index.html").write_text(html, encoding="utf-8")


def saturation_stats(pages_rgb: list[np.ndarray], events: list[dict]) -> dict:
    """Precondition 3: high-saturation ink on flat backgrounds."""
    ink = [cv2.cvtColor(np.uint8([[e["dominant_colour"]]]), cv2.COLOR_RGB2HSV)[0][0][1]
           for e in events if e["kind"] == "add"]
    bg = [float(np.median(cv2.cvtColor(p, cv2.COLOR_RGB2HSV)[:, :, 1])) for p in pages_rgb]
    if not ink:
        return {"ink_saturation_median": None, "deck_saturation_median": round(float(np.median(bg)), 1)}
    return {
        "ink_saturation_median": round(float(np.median(ink)), 1),
        "ink_saturation_p10": round(float(np.percentile(ink, 10)), 1),
        "deck_saturation_median": round(float(np.median(bg)), 1),
        "note": "0-255 scale; ink well above deck means the third precondition holds",
    }


def run(lesson: Path) -> None:
    video = lesson / "source" / "video.mp4"
    pdf = lesson / "source" / "slides.pdf"
    out_dir = lesson / "analysis" / "annotations"
    (out_dir / "checks").mkdir(parents=True, exist_ok=True)
    data = json.loads((lesson / "analysis" / "slides" / "slide_timeline.json")
                      .read_text(encoding="utf-8"))
    intervals, duration = data["intervals"], data["duration"]
    width, height = data["video_size"]

    excluded = np.zeros((height, width), bool)
    chrome = {"band_top": int(height * 0.85), "boxes": []}

    pages_rgb = [np.asarray(p) for p in timeline.render_pages_colour(pdf)]
    pages_grey = timeline.render_pages(pdf)
    words = word_boxes(pdf, width)
    layer = ["none" if len(w) == 0 else "partial" if len(w) < 40 else "full" for w in words]
    blanks = [timeline.blank_areas(p) for p in pages_grey]

    harvest = {"cursor_shapes": [], "ink_shapes": [], "small_but_persistent": 0}
    events: list[dict] = []
    dwells: list[dict] = []
    counts: dict[str, int] = {}
    cards: list[dict] = []
    carry_report: list[dict] = []
    noise: list[float] = []
    totals = {"static": 0, "frames": 0}

    state = None
    holder = {"prev_end_ink": None}
    prev_frame = None
    print("decoding at " + format(1 / SAMPLE_SECONDS, "g") + " fps...")

    def establish(state):
        """Build the baseline from the interval's own frames and replay them.

        A short interval whose frames are mostly absorbed from another page may
        never reach BASELINE_FRAMES, so take the median of whatever it has.
        """
        if state["baseline"] is not None or not state["buffer"]:
            return
        page = state["iv"]["page"] - 1
        state["baseline"] = np.median(
            np.stack([f for _, f in state["buffer"]]), axis=0).astype(np.uint8)
        detect_carry_over(state, state["buffer"][0][1], pages_rgb[page],
                          blanks[page], holder["prev_end_ink"], excluded)
        block = excluded | state["carry_mask"]
        for bt, bf in state["buffer"]:
            step(state, bf, bt, block, chrome)
        state["buffer"] = []

    def close(state):
        if state is None:
            return
        iv = state["iv"]
        page = iv["page"] - 1
        establish(state)
        if state["union"] is None:            # no own frames at all
            state["union"] = np.zeros((height, width), bool)
            state["ink_union"] = np.zeros((height, width), bool)
            state["colour"] = np.zeros((height, width, 3), np.uint8)
            state["carry"] = state["carry"] or []
        if state.get("last_frame") is None:
            state["last_frame"] = pages_rgb[page]
        erased = finish_interval(state, words[page], layer[page], events, dwells,
                                 counts, harvest)
        image = "%03d_p%02d.png" % (state["index"], iv["page"])
        render_check(state, erased, pages_rgb[page]).save(out_dir / "checks" / image)
        cards.append({"index": state["index"], "page": iv["page"], "start": iv["start"],
                      "end": iv["end"], "image": image, "carry": state["carry"] or [],
                      "text_layer": layer[page]})
        if state["carry"]:
            carry_report.append({"interval": state["index"], "page": iv["page"],
                                 "attributed_to_interval": state["index"] - 1,
                                 "regions": state["carry"]})
        totals["static"] += state["static_frames"]
        totals["frames"] += state["frames"]
        holder["prev_end_ink"] = (changed_mask(state["last_frame"], pages_rgb[page])
                                  & blanks[page] & ~excluded)

    for index, frame in enumerate(frame_stream(video, width, height)):
        t = sample_time(index)
        iv = page_of(intervals, t)
        if iv is None:
            continue
        if state is None or state["iv"] is not iv:
            close(state)
            state = new_interval(iv, len(cards))
        if in_absorbed(iv, t):
            state["skipped"] = state.get("skipped", 0) + 1
            continue
        state["last_frame"] = frame
        if state["baseline"] is None:
            state["buffer"].append((t, frame))
            if len(state["buffer"]) == BASELINE_FRAMES:
                establish(state)
            prev_frame = frame
            continue
        step(state, frame, t, excluded | state["carry_mask"], chrome)
        if index % 30 == 0 and prev_frame is not None and state["prev_mask"] is not None:
            quiet = ~state["prev_mask"] & ~excluded
            noise.append(float(np.abs(frame.astype(np.int16)
                                      - prev_frame.astype(np.int16))[quiet].mean()))
        prev_frame = frame
    close(state)

    # Cursor templates are harvested, never hand-specified: a blob that moved every
    # sample is certainly the cursor, so the shapes that recur among those blobs are
    # this recording's cursor glyphs. Methodology §5 warns that shape matching alone
    # is unreliable -- it is used here only to clean up after the persistence rules.
    buckets: dict[tuple[int, int], list[np.ndarray]] = {}
    for w, h, sub in harvest["cursor_shapes"]:
        buckets.setdefault((w, h), []).append(sub)
    templates = []
    for (w, h), subs in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        if len(subs) >= TEMPLATE_MIN_SEEN and len(templates) < TEMPLATE_KEEP:
            templates.append({"w": w, "h": h, "seen": len(subs),
                              "mask": np.mean(subs, axis=0) >= 0.5})
    dropped = []
    for event_index, (w, h, sub) in harvest["ink_shapes"]:
        if event_index >= len(events):
            continue
        for tpl in templates:
            if tpl["w"] == w and tpl["h"] == h and shape_iou(tpl["mask"], sub) >= TEMPLATE_IOU:
                dropped.append(event_index)
                break
    drop = set(dropped)
    events = [e for i, e in enumerate(events) if i not in drop]
    counts["cursor_by_template"] = len(drop)
    counts["ink"] = counts.get("ink", 0) - len(drop)
    print("cursor templates harvested: "
          + ", ".join("%dx%d seen %d" % (t["w"], t["h"], t["seen"]) for t in templates))
    print("ink events dropped by template match: " + str(len(drop)))
    print("blobs under " + str(MIN_EVENT_AREA) + "px dropped despite lasting >=5s: "
          + str(harvest["small_but_persistent"]))

    boxes = chrome["boxes"]
    toolbar = None
    if boxes:
        x = min(b[0] for b in boxes)
        y = min(b[1] for b in boxes)
        med = [int(np.median([b[i] for b in boxes])) for i in range(4)]
        toolbar = {"bbox": med, "frames_showing": len(boxes),
                   "note": ("median of the boxes observed; the bar sits at a fixed "
                            "place, so a union would grow whenever ink fell in the band")}
        print("viewer control bar " + str(toolbar["bbox"]) + ", showing in "
              + str(len(boxes)) + " frames")

    payload = {
        "video": str(video), "pdf": str(pdf),
        "method": ("per-interval median baseline, connected-component tracking; "
                   "geometry and timing only, no interpretation"),
        "parameters": {
            "sample_seconds": SAMPLE_SECONDS, "diff_threshold": DIFF_THRESHOLD,
            "min_blob_area": MIN_BLOB_AREA, "baseline_frames": BASELINE_FRAMES,
            "cursor_max_area": CURSOR_MAX_AREA, "cursor_area_cv": CURSOR_AREA_CV,
            "dwell_min_samples": DWELL_MIN_SAMPLES,
            "bulk_erase_fraction": BULK_ERASE_FRACTION,
            "carry_overlap": CARRY_OVERLAP,
            "target_under_px": TARGET_UNDER_PX, "target_overlap": TARGET_OVERLAP,
        },
        "masked_toolbar": toolbar,
        "frames_total": totals["frames"],
        "counts": counts,
        "cursor_templates": [{"w": t["w"], "h": t["h"], "seen": t["seen"]}
                             for t in templates],
        "small_but_persistent_dropped": harvest["small_but_persistent"],
        "carry_over": carry_report,
        "preconditions": {
            "screen_capture_noise_mean_abs_diff":
                round(float(np.mean(noise)), 4) if noise else None,
            "static_frame_fraction": round(totals["static"] / max(totals["frames"], 1), 4),
            "frames_examined": totals["frames"],
            "ink_vs_background_saturation": saturation_stats(pages_rgb, events),
        },
        "events": sorted(events, key=lambda e: e["start"]),
        "cursor_dwells": sorted(dwells, key=lambda d: d["start"]),
    }
    merged: list[dict] = []
    for d in sorted(dwells, key=lambda d: (d["interval"], d["start"])):
        last = merged[-1] if merged else None
        if (last and last["interval"] == d["interval"]
                and abs(last["position"][0] - d["position"][0]) <= 20
                and abs(last["position"][1] - d["position"][1]) <= 20
                and d["start"] - last["end"] <= 3 * SAMPLE_SECONDS):
            last["end"] = d["end"]
            last["area_px"] = max(last["area_px"], d["area_px"])
        else:
            merged.append(dict(d))
    payload["cursor_dwells"] = merged
    payload["counts"]["dwell_merged"] = len(merged)

    (out_dir / "annotation_events.json").write_text(
        json.dumps(payload, indent=1), encoding="utf-8")
    write_checks(out_dir / "checks", cards, events, dwells)

    adds = sum(1 for e in events if e["kind"] == "add")
    rems = sum(1 for e in events if e["kind"] == "remove")
    print("\nevents: %d added, %d removed" % (adds, rems))
    print("cursor: %d moving, %d held (%d dwells recorded)"
          % (counts.get("cursor_moving", 0), counts.get("cursor_held", 0),
             counts.get("dwell", 0)))
    print("carry-over: %d of %d intervals" % (len(carry_report), len(cards)))
    print(str(out_dir / "annotation_events.json"))


def main() -> None:
    lesson = Path(sys.argv[1])
    if "--measure-baseline" in sys.argv:
        measure_baseline(lesson)
        return
    run(lesson)


if __name__ == "__main__":
    main()
