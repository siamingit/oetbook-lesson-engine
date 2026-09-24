"""Resolve every cue's geometry and assemble the page-13 lesson bundle.

Three kinds of cue target, three kinds of geometry:

- `slide_phrase`  -- looked up directly in the PDF's own text layer (pypdfium2
  word boxes, reused from extract_annotations.word_boxes). This is exact:
  the phrase is real text at a real position, never guessed.
- `answer_box`    -- the blank green bar under the row's wrong sentence.
- `annotation_note` -- a note in the right margin, level with that row.

For the last two there is no PDF text to search for (the content is
English-authored, not present on the slide), so their geometry is a fixed
box per row. The four rows' pixel boxes below were measured once from the
PDF's own page objects (each red/green bar is a type=5 image object) at
1440x810 -- see the numbers next to ROW_RED/ROW_GREEN. Row assignment for
answer_box/annotation_note cues comes from BEAT_ROW, a table of which beat
discusses which numbered sentence (from each beat's learning_objective:
b2-b4 = item 1, b5-b8 = item 2, b9-b10 = item 3, b11-b16 = item 4).

    .venv/Scripts/python spike/scripts/build_bundle.py <lesson_dir>

Reads:  <lesson_dir>/analysis/script/script.json
        <lesson_dir>/generated/page-<N>/timeline.json
        <lesson_dir>/source/slides.pdf
Writes: <lesson_dir>/generated/page-<N>/slide.png
        <lesson_dir>/generated/page-<N>/bundle.json
"""

import argparse
import json
import string
import sys
from pathlib import Path

import pypdfium2 as pdfium

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_annotations import word_boxes  # noqa: E402
import paths  # noqa: E402

RENDER_WIDTH = 1440  # == the PDF page width in points, so 1px == 1pt

# pypdfium2's text-layer boxes (get_charbox, and get_bounds on text objects --
# both agree with each other) run ~7pt above where the glyphs actually land in
# this deck's own rendered output: pixel-scanning the rendered slide.png for
# real ink gives a y-range consistently ~6.5-8pt below what the text layer
# reports, on three independent samples (a "since 2010" row, "Paul", and the
# white title text) -- x is exact, only y is off, and by a roughly constant
# amount, not a scale error. Likely a substituted/non-embedded font: the
# renderer draws with different metrics than the text layer reports. Path and
# image objects (the row bars below) don't need this -- get_bounds() on those
# already matches the render exactly.
TEXT_Y_CORRECTION = 7.0

# Methodology §17a: the longest stretch of speech allowed with nothing on screen.
VISUAL_GAP_LIMIT_S = 15.0

# Measured from the PDF's page objects (type=5 image bars) at 1440x810.
ROW_RED = [
    (138.6, 179.2, 1187.9, 234.3),
    (138.6, 323.1, 1187.9, 378.1),
    (138.6, 467.2, 1187.9, 522.2),
    (138.6, 611.0, 1187.9, 666.1),
]
ROW_GREEN = [
    (138.6, 242.0, 1187.9, 297.1),
    (138.6, 385.8, 1187.9, 440.9),
    (138.6, 529.9, 1187.9, 585.0),
    (138.6, 673.8, 1187.9, 728.8),
]
# Right margin, level with each row's combined red+green span.
ROW_NOTE = [(1200.0, red[1], 1430.0, green[3]) for red, green in zip(ROW_RED, ROW_GREEN)]

BEAT_ROW = {
    "b1": None,
    "b2": 0, "b3": 0, "b4": 0,
    "b5": 1, "b6": 1, "b7": 1, "b8": 1,
    "b9": 2, "b10": 2,
    "b11": 3, "b12": 3, "b13": 3, "b14": 3, "b15": 3, "b16": 3,
}


def strip_punct(word: str) -> str:
    return word.strip(string.punctuation)


def match_phrase(words: list[dict], target: str) -> list[float]:
    """Find `target`'s tokens as a contiguous run in `words`; return their bbox."""
    target_tokens = target.split()
    norm_target = [strip_punct(t) for t in target_tokens]
    n = len(target_tokens)
    for i in range(len(words) - n + 1):
        window = words[i:i + n]
        if [strip_punct(w["text"]) for w in window] == norm_target:
            x0 = min(w["box"][0] for w in window)
            y0 = min(w["box"][1] for w in window)
            x1 = max(w["box"][2] for w in window)
            y1 = max(w["box"][3] for w in window)
            return [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)]
    raise SystemExit(f"slide_phrase not found in PDF text layer: {target!r}")


def resolve_cue(target: dict, beat_id: str, words: list[dict]) -> dict:
    kind = target["kind"]
    if kind == "slide_phrase":
        return {"kind": kind, "box": match_phrase(words, target["text"])}

    # Written items have no home on this deck -- it is full, and it is due for
    # replacement anyway (methodology §18), so they go on a board beside the
    # slide instead of onto the artwork. The board lays itself out in the
    # player, so there is no geometry to resolve here.
    if kind == "board_note":
        return {"kind": kind, "text": target["text"]}
    if kind == "comparison":
        return {"kind": kind, "text": target["text"],
                "left": target.get("left") or "", "right": target.get("right") or ""}
    if kind == "thinking_pause":
        return {"kind": kind, "text": target["text"],
                "seconds": target.get("seconds")}

    row = BEAT_ROW.get(beat_id)
    if row is None:
        raise SystemExit(f"{beat_id}: {kind} cue has no row (not one of the four items)")

    box_source = ROW_GREEN if kind == "answer_box" else ROW_NOTE
    x0, y0, x1, y1 = box_source[row]
    # answer_box/annotation_note text isn't on the slide -- it's authored
    # content the player types out, so it has to travel with the geometry.
    return {"kind": kind, "row": row, "box": [x0, y0, x1, y1], "text": target["text"]}


def render_slide(pdf_path: Path, page_index: int, out_path: Path) -> None:
    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[page_index]
    scale = RENDER_WIDTH / page.get_width()
    img = page.render(scale=scale).to_pil().convert("RGB")
    img.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    args = parser.parse_args()

    page = args.page
    page_index = page - 1        # the deck is 1-based; pdfium is 0-based
    script = json.loads((paths.script_dir(args.lesson_dir, page) / "script.json")
                         .read_text(encoding="utf-8"))
    out_dir = paths.generated_dir(args.lesson_dir, page)
    timeline = json.loads((out_dir / "timeline.json").read_text(encoding="utf-8"))

    pdf_path = args.lesson_dir / "source" / "slides.pdf"
    pages = word_boxes(pdf_path, RENDER_WIDTH)
    words = pages[page_index]
    for w in words:
        w["box"][1] += TEXT_Y_CORRECTION
        w["box"][3] += TEXT_Y_CORRECTION

    render_slide(pdf_path, page_index, out_dir / "slide.png")

    n_cues = 0

    # Cross-reference timeline cues (which carry timing) with script.json cues
    # (which carry type/target) by beat/utterance/cue id.
    raw_cues = {}
    for beat in script["beats"]:
        for utt in beat["utterances"]:
            for cue in utt["cues"]:
                raw_cues[(beat["id"], utt["id"], cue["id"])] = cue

    for beat in timeline["beats"]:
        for utt in beat["utterances"]:
            for cue in utt["cues"]:
                raw = raw_cues[(beat["id"], utt["id"], cue["id"])]
                geometry = resolve_cue(raw["target"], beat["id"], words)
                cue["type"] = raw["type"]
                cue.update(geometry)
                n_cues += 1

    bundle = {
        "meta": {
            **timeline["meta"],
            "slide_image": "slide.png",
            "slide_width": RENDER_WIDTH,
            "slide_height": round(RENDER_WIDTH * 810 / 1440),
        },
        "row_boxes": {
            "red": ROW_RED,
            "green": ROW_GREEN,
            "note": ROW_NOTE,
        },
        "beats": timeline["beats"],
    }

    bundle_path = out_dir / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")

    # Methodology §17a: never more than about fifteen seconds of speech with
    # nothing happening on screen. Arithmetic, so no reviewer has to time it.
    events = sorted(c["time"] for beat in timeline["beats"]
                    for u in beat["utterances"] for c in u["cues"])
    total = timeline["meta"]["total_duration_s"]
    marks = [0.0] + events + [total]
    gaps = [(marks[i + 1] - marks[i], marks[i], marks[i + 1])
            for i in range(len(marks) - 1)]
    longest, at_from, at_to = max(gaps)
    over = [g for g in gaps if g[0] > VISUAL_GAP_LIMIT_S]

    print(f"resolved {n_cues} cues")
    print(f"visual events: {len(events)} over {total / 60:.1f} min "
          f"= one every {total / max(1, len(events)):.1f}s")
    print(f"longest stretch with nothing on screen: {longest:.1f}s "
          f"({at_from:.1f}s -> {at_to:.1f}s)")
    if over:
        print(f"OVER {VISUAL_GAP_LIMIT_S:.0f}s: {len(over)} stretch(es) — "
              + ", ".join(f"{g:.1f}s at {a:.0f}s" for g, a, _ in over[:8]))
    print(f"wrote {out_dir / 'slide.png'}")
    print(f"wrote {bundle_path}")


if __name__ == "__main__":
    main()
