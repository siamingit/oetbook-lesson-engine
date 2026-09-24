"""A SILENT preview player for the whole lesson: every section in order, played
on an estimated timeline, with no audio and no Cartesia call.

    .venv/Scripts/python spike/scripts/build_silent_preview.py <lesson_dir> [--wpm 135]

Reads:  <lesson_dir>/analysis/sections.json
        <lesson_dir>/analysis/screens/<section>/screens.json
        <lesson_dir>/analysis/narration/<section>/narration.json
Writes: <lesson_dir>/generated/lesson-preview/silent/player.html (+ bundle.json)

Each utterance's duration is estimated from its word count at --wpm (the
target pace; default 135, change it when the voice speed is chosen), spread
over its words by length, so the reading pointer walks the words at a
plausible rate. From there everything is the real pipeline's own code: the
timeline is laid out by build_board_timeline.lay_timeline (the same gaps,
pause handling, erase events and cue lead), the reading runs by
build_board_bundle.reading_runs, the blocks by write_screens.block_html, and
the page is board_player_template.html, which runs on a timer instead of
audio when the bundle is marked silent. The narration shows as subtitles.

Block, board, state and utterance ids repeat from section to section (every
section has a k01), so every id is prefixed with its section tag here
("pages-05-06_k01", "page-13_t2.s3"). A diagram part keeps its suffix
("page-11_k02.3"), which is how the player finds it.
"""

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths                                                      # noqa: E402
from build_board_bundle import block_tokens, reading_runs         # noqa: E402
from build_board_timeline import lay_timeline                     # noqa: E402
from write_narration import spoken                                # noqa: E402
from write_screens import FRAME_CSS, block_html, is_exercise_board  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]

def estimate(words: list[str], wpm: float) -> dict:
    """Word starts and ends for one utterance at `wpm`, each word's share of
    the time proportional to its length plus a fixed gap."""
    duration = len(words) * 60.0 / wpm
    weights = [len(w) + 2 for w in words] or [1]
    total = sum(weights)
    starts, ends, t = [], [], 0.0
    for w in weights:
        d = duration * w / total
        starts.append(round(t, 3))
        ends.append(round(t + d * 0.85, 3))
        t += d
    return {"text": " ".join(words), "words": words, "word_start": starts, "word_end": ends,
            "duration_s": round(duration, 3), "file": None,
            "voice": "none (silent preview)", "model": "estimate", "speed": None}

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--wpm", type=float, default=135.0)
    args = ap.parse_args()
    L = args.lesson_dir

    sec_info = json.loads((L / "analysis" / "sections.json").read_text(encoding="utf-8"))
    lesson_title = sec_info["lesson"]["title"]

    boards_all, blocks_all, audio_index, section_marks = [], {}, {}, []
    # The lesson opens with its narrated introduction, the title and contents
    # boards (docs/00-PRODUCT.md §2a), stored with the contents slide's page.
    intro = []
    cp = sec_info.get("contents_page")
    if cp and (paths.narration_dir_for(L, [cp]) / "narration.json").exists():
        intro = [{"title": "Introduction", "pages": [cp]}]
    for sec in intro + sec_info["sections"]:
        pages = sec["pages"]
        tag = paths.section_tag(pages)
        narr_p = paths.narration_dir_for(L, pages) / "narration.json"
        scr_p = paths.screens_dir_for(L, pages) / "screens.json"
        if not narr_p.exists() or not scr_p.exists():
            raise SystemExit(f"REFUSED: section {sec['title']!r} has no narration or screens")
        narr = json.loads(narr_p.read_text(encoding="utf-8"))
        scr = json.loads(scr_p.read_text(encoding="utf-8"))
        fails = [f for f in narr["audit"] if f["severity"] == "fail"]
        if fails:
            raise SystemExit(f"REFUSED: {sec['title']!r} narration fails its audit: "
                             + "; ".join(f["what"] for f in fails[:3]))
        pre = tag + "_"
        blocks = {b["id"]: b for t in scr["topics"] for h in t["thoughts"] for b in h["blocks"]}
        for bid, b in blocks.items():
            nb = copy.deepcopy(b)
            nb["id"] = pre + bid
            blocks_all[pre + bid] = {**{k: nb.get(k) for k in (
                "id", "type", "label", "text", "term", "explanation", "left", "right",
                "family", "kind", "icon", "items", "header", "rows", "provenance")},
                "html": block_html(nb), "_tokens": block_tokens(b)}
        section_marks.append({"title": sec["title"], "pages": pages, "first_board": None})
        for bd in narr["boards"]:
            nbd = {"id": pre + bd["id"], "title": bd["title"],
                   "fixed": [pre + i for i in bd["fixed"]], "states": []}
            for s in bd["states"]:
                ns = {"id": pre + s["id"], "working": [pre + i for i in s["working"]],
                      "erase_after": ({"blocks": [pre + i for i in s["erase_after"]["blocks"]]}
                                      if s.get("erase_after") else None),
                      "utterances": []}
                for u in s["utterances"]:
                    nu = copy.deepcopy(u)
                    nu["id"] = pre + u["id"]
                    for c in nu["cues"]:
                        for key in ("block", "to_block"):
                            if c.get(key):
                                c[key] = pre + c[key]
                    ns["utterances"].append(nu)
                    audio_index[nu["id"]] = estimate(spoken(u["text_with_cues"]).split(), args.wpm)
                nbd["states"].append(ns)
            if section_marks[-1]["first_board"] is None:
                section_marks[-1]["first_board"] = nbd["id"]
            boards_all.append(nbd)

    narr_all = {"lesson": L.name, "boards": boards_all}
    boards_out, events, total = lay_timeline(narr_all, audio_index)

    # Reading runs, exercise flags, section starts: as build_board_bundle does.
    tokens = {i: b.pop("_tokens") for i, b in blocks_all.items()}
    starts = {bd["id"]: bd["start"] for bd in boards_out}
    n_read = 0
    for bd in boards_out:
        bd["exercise"] = is_exercise_board(bd["fixed"], blocks_all)
        for s in bd["states"]:
            cands = {i: tokens[i] for i in list(bd["fixed"]) + list(s["working"])}
            for u in s["utterances"]:
                e = audio_index[u["id"]]
                u["reading"] = reading_runs(e["words"], e["word_start"], e["word_end"],
                                            u["start"], cands)
                u["audio_file"] = None
                n_read += bool(u["reading"])
    used = {i for bd in boards_out for i in bd["fixed"]} | \
           {i for bd in boards_out for s in bd["states"] for i in s["working"]}
    bundle = {
        "meta": {"lesson": L.name, "page": "whole lesson", "silent": True, "wpm": args.wpm,
                 "lesson_title": lesson_title, "total_duration_s": round(total, 3),
                 "sections": [{"title": m["title"], "pages": m["pages"],
                               "start": starts[m["first_board"]]} for m in section_marks]},
        "blocks": {i: b for i, b in blocks_all.items() if i in used},
        "boards": boards_out,
        "events": events,
    }
    out_dir = L / "generated" / "lesson-preview" / "silent"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    template = (REPO_ROOT / "spike" / "scripts" / "board_player_template.html").read_text(encoding="utf-8")
    html = (template.replace("__TITLE__", "SILENT PREVIEW - " + lesson_title)
            .replace("/*__FRAME_CSS__*/", FRAME_CSS)
            .replace("__BUNDLE_JSON__", json.dumps(bundle, ensure_ascii=False).replace("</", "<\\/")))
    (out_dir / "player.html").write_text(html, encoding="utf-8")

    n_utt = sum(len(s["utterances"]) for bd in boards_out for s in bd["states"])
    cues = sum(len(u["cues"]) for bd in boards_out for s in bd["states"] for u in s["utterances"])
    print(f"sections {len(section_marks)} | boards {len(boards_out)} | utterances {n_utt} | "
          f"cues {cues} | erase events {sum(1 for e in events if e['type'] == 'erase')}")
    print(f"estimated at {args.wpm:g} wpm: {total / 60:.1f} min | reading pointer on "
          f"{n_read} of {n_utt} utterances")
    for m in bundle["meta"]["sections"]:
        mm, ss = divmod(int(m["start"]), 60)
        print(f"  {mm:3d}:{ss:02d}  {m['title']}")
    print(f"wrote {out_dir / 'player.html'}")

if __name__ == "__main__":
    main()
