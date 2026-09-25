"""The whole lesson in one player: the introduction, then every section in
lesson order, with the contents menu.

    .venv/Scripts/python spike/scripts/build_lesson_player.py <lesson_dir>
    .venv/Scripts/python spike/scripts/build_lesson_player.py <lesson_dir> --silent [--wpm 155]

Reads:  <lesson_dir>/analysis/sections.json
        <lesson_dir>/analysis/screens/<section>/screens.json
        <lesson_dir>/analysis/narration/<section>/narration.json
        <lesson_dir>/generated/<section>/boards/audio_index.json and its WAVs (not --silent)
Writes: <lesson_dir>/generated/lesson-player/        player.html, bundle.json,
                                                     timeline.json, audio_index.json
        <lesson_dir>/generated/lesson-preview/silent/ the same, with --silent

With audio, every utterance's timing is the voice's own (Cartesia word
timestamps, the section's audio index); an utterance with no audio stops the
build. With --silent, each utterance's duration is estimated from its word
count at --wpm and nothing is played. Either way everything else is the
real pipeline's own code: the timeline is laid out by
build_board_timeline.lay_timeline (the same gaps, pause handling, erase
events and cue lead), the reading runs by build_board_bundle.reading_runs,
the blocks by write_screens.block_html, and the page is
board_player_template.html.

Block, board, state and utterance ids repeat from section to section (every
section has a k01), so every id is prefixed with its section tag here
("pages-05-06_k01", "page-13_t2.s3"). A diagram part keeps its suffix
("page-11_k02.3"), which is how the player finds it. Audio files stay in
their section's folder; the player refers to them by relative path.

bundle.json is the lesson bundle, the contract between this pipeline and the
website (docs/04-LESSON-BUNDLE.md). Everything a renderer needs is stated in
it: the sections and categories, which section each board belongs to, when
every working block and diagram part appears and until when, the reading
pointer's hold. The player is a reference renderer and works nothing out for
itself. text.json is the clean text of every section, blocks.css the
stylesheet the blocks' html is written against.
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
from write_screens import (FRAME_CSS, TAG_LABELS, block_html,     # noqa: E402
                           block_text_runs, is_exercise_board)

REPO_ROOT = Path(__file__).resolve().parents[2]

FORMAT_VERSION = "1.0"             # docs/04-LESSON-BUNDLE.md
READING_HOLD_S = 2.5               # the pointer stays on the last word read this long
# Everything block_html draws from; pipeline notes (anchor, from_beats, note,
# relabelled, ruling) stay in screens.json.
BLOCK_FIELDS = ("id", "type", "label", "text", "term", "explanation", "left", "right",
                "family", "col_families", "kind", "icon", "items", "header", "rows",
                "tags", "exercise_item", "provenance")


def block_data(b: dict) -> dict:
    """A block's data as the bundle carries it: every field its html is drawn
    from, each tense tag with the label printed on its chip."""
    d = {k: b.get(k) for k in BLOCK_FIELDS}
    tags = [dict(t, label=TAG_LABELS[t["family"]]) for t in (b.get("tags") or [])
            if t.get("text") and t.get("family") in TAG_LABELS]
    d["tags"] = tags or None
    return d


def diagram_parts(b: dict) -> list[str]:
    """Part ids of a diagram block, as its html names them (data-part)."""
    if b["type"] != "timeline":
        return []
    return [f"{b['id']}.{it.get('part', 0)}" for it in b.get("items") or []]


def block_plain(b: dict) -> str:
    """A block's words as plain text: its text runs one per line, a table one
    row per line with cells separated by ' | '."""
    if b["type"] == "table":
        lines = [" | ".join(b.get("header") or [])] + [" | ".join(r) for r in b.get("rows") or []]
        return "\n".join(x for x in lines if x.strip(" |"))
    return "\n".join(block_text_runs(b))


def text_export(lesson: dict, sections: list[dict], boards: list[dict], blocks: dict) -> dict:
    """The lesson as clean text, per section: the narration as spoken and the
    words on the board, with no cues and no provenance (docs/04-LESSON-BUNDLE.md)."""
    by_id = {bd["id"]: bd for bd in boards}
    out = []
    for sec in sections:
        bds = []
        for bid in sec["boards"]:
            bd = by_id[bid]
            ids: list[str] = []
            for i in list(bd["fixed"]) + [i for s in bd["states"] for i in s["working"]]:
                if i not in ids:
                    ids.append(i)
            bds.append({"id": bid, "start": bd["start"],
                        "board_text": [{"block": i, "text": block_plain(blocks[i])} for i in ids],
                        "narration": [{"id": u["id"], "start": u["start"], "text": u["text"]}
                                      for s in bd["states"] for u in s["utterances"]]})
        out.append({"id": sec["id"], "title": sec["title"], "category": sec["category"],
                    "start": sec["start"], "end": sec["end"],
                    "narration_text": "\n\n".join(" ".join(n["text"] for n in b["narration"])
                                                  for b in bds),
                    "board_text": "\n\n".join(x["text"] for b in bds for x in b["board_text"]),
                    "boards": bds})
    return {"format": "oetbook-lesson-text", "format_version": FORMAT_VERSION,
            "lesson": lesson, "sections": out}


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


def lesson_sections(L: Path) -> tuple[dict, list[dict]]:
    """The introduction (paths.intro_section: with the contents slide's page,
    or the title slide's in a deck with none), then the sections in lesson
    order (docs/00-PRODUCT.md §2a)."""
    info = json.loads((L / "analysis" / "sections.json").read_text(encoding="utf-8"))
    intro = []
    it = paths.intro_section(info)
    if it and (paths.narration_dir_for(L, it["pages"]) / "narration.json").exists():
        intro = [{"title": "Introduction", "pages": it["pages"], "intro": True}]
    return info, intro + info["sections"]


def build(L: Path, silent: bool, wpm: float = 135.0) -> Path:
    info, secs = lesson_sections(L)
    out_dir = L / "generated" / ("lesson-preview/silent" if silent else "lesson-player")
    out_dir.mkdir(parents=True, exist_ok=True)

    boards_all, blocks_all, audio_index, section_marks = [], {}, {}, []
    missing: list[str] = []
    for sec in secs:
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
        sec_index = {}
        if not silent:
            ip = paths.boards_dir_for(L, pages) / "audio_index.json"
            sec_index = json.loads(ip.read_text(encoding="utf-8")) if ip.exists() else {}
        pre = tag + "_"
        blocks = {b["id"]: b for t in scr["topics"] for h in t["thoughts"] for b in h["blocks"]}
        for bid, b in blocks.items():
            nb = copy.deepcopy(b)
            nb["id"] = pre + bid
            blocks_all[pre + bid] = {**block_data(nb), "html": block_html(nb),
                                     "_tokens": block_tokens(b)}
        section_marks.append({"id": tag, "title": sec["title"], "pages": pages,
                              "intro": bool(sec.get("intro")),
                              "first_board": None, "boards": []})
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
                    if silent:
                        audio_index[nu["id"]] = estimate(spoken(u["text_with_cues"]).split(), wpm)
                    else:
                        e = sec_index.get(u["id"])
                        if not e or e.get("text") != spoken(u["text_with_cues"]):
                            missing.append(nu["id"])
                            continue
                        # the audio stays in its section's folder
                        audio_index[nu["id"]] = {**e, "id": nu["id"],
                                                 "file": f"../{tag}/boards/{e['file']}"}
                nbd["states"].append(ns)
            if section_marks[-1]["first_board"] is None:
                section_marks[-1]["first_board"] = nbd["id"]
            section_marks[-1]["boards"].append(nbd["id"])
            boards_all.append(nbd)
    if missing:
        raise SystemExit(f"REFUSED: {len(missing)} utterance(s) have no audio, or audio made "
                         f"from other text: {', '.join(missing[:12])}"
                         + (" ..." if len(missing) > 12 else ""))

    narr_all = {"lesson": L.name, "boards": boards_all}
    gaps = {"utterance_gap_s": 0.4, "state_gap_s": 1.2, "board_gap_s": 1.5, "cue_lead_s": 0.35}
    boards_out, events, total = lay_timeline(narr_all, audio_index, gaps["utterance_gap_s"],
                                             gaps["state_gap_s"], gaps["board_gap_s"],
                                             gaps["cue_lead_s"])

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
                u["audio_file"] = e["file"]
                n_read += bool(u["reading"])
    used = {i for bd in boards_out for i in bd["fixed"]} | \
           {i for bd in boards_out for s in bd["states"] for i in s["working"]}

    # Visibility, stated rather than left to the renderer. A fixed block shows
    # from its board's start until the board's `until`; a working block from
    # its reveal until its state's `until` (the erase, or the board's end); a
    # diagram part from its own reveal, or with its block when it has no cue
    # of its own, and a part of a fixed diagram stays through every erasure.
    # A mark lasts from its cue until its state's `until`.
    board_section = {b: m["id"] for m in section_marks for b in m["boards"]}
    for bi, bd in enumerate(boards_out):
        bd["section"] = board_section[bd["id"]]
        bd["until"] = boards_out[bi + 1]["start"] if bi + 1 < len(boards_out) else round(total, 3)
        fixed_rev: dict[str, float] = {}
        for s in bd["states"]:
            cues = [c for u in s["utterances"] for c in u["cues"] if c["type"] == "reveal"]
            s_rev: dict[str, float] = {}
            for c in cues:
                target = fixed_rev if c["block"].split(".")[0] in bd["fixed"] else s_rev
                target.setdefault(c["block"], c["time"])
            s["reveal"] = {}
            for wid in s["working"]:
                if wid in s_rev:
                    s["reveal"][wid] = s_rev[wid]
                    for p in diagram_parts(blocks_all[wid]):
                        s["reveal"][p] = s_rev.get(p, s_rev[wid])
            s["until"] = s["erase"]["time"] if s["erase"] else bd["until"]
        bd["reveal"] = {p: fixed_rev.get(p, bd["start"])
                        for fid in bd["fixed"] for p in diagram_parts(blocks_all[fid])}

    # Categories and their sections as the contents board shows them
    # (build_lesson_boards.py): sections.json's category list, by section title.
    cat_ids = {c["title"]: f"c{n}" for n, c in enumerate(info.get("categories") or [], 1)}
    cat_of: dict[str, str] = {}
    for c in info.get("categories") or []:
        for title in c["sections"]:
            if not any(m["title"] == title for m in section_marks):
                raise SystemExit(f"REFUSED: category {c['title']!r} lists a section {title!r} "
                                 "that is not in the lesson")
            cat_of[title] = c["title"]
    for m in section_marks:
        m["category_title"] = cat_of.get(m["title"])
    sections_out = []
    for n, m in enumerate(section_marks):
        start = starts[m["first_board"]]
        end = starts[section_marks[n + 1]["first_board"]] if n + 1 < len(section_marks) else round(total, 3)
        sections_out.append({"id": m["id"], "title": m["title"], "pages": m["pages"],
                             "intro": m["intro"], "category": cat_ids.get(m["category_title"]),
                             "start": start, "end": end, "boards": m["boards"]})
    lesson = {"id": L.name, "title": info["lesson"]["title"],
              "description": info["lesson"].get("description"),
              "categories": [{"id": cid, "title": title,
                              "sections": [s["id"] for s in sections_out if s["category"] == cid]}
                             for title, cid in cat_ids.items()]}

    first = next(iter(audio_index.values()))
    meta = {"silent": silent, **gaps, "wpm": wpm if silent else None,
            "voice": first.get("voice"), "model": first.get("model"), "speed": first.get("speed"),
            "total_duration_s": round(total, 3), "reading_hold_s": READING_HOLD_S}
    bundle = {"format": "oetbook-lesson-bundle", "format_version": FORMAT_VERSION,
              "lesson": lesson, "sections": sections_out, "meta": meta,
              "stylesheet": "blocks.css", "text": "text.json",
              "blocks": {i: b for i, b in blocks_all.items() if i in used},
              "boards": boards_out, "events": events}
    (out_dir / "bundle.json").write_text(json.dumps(bundle, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    (out_dir / "blocks.css").write_text(FRAME_CSS.strip() + "\n", encoding="utf-8")
    (out_dir / "text.json").write_text(
        json.dumps(text_export(lesson, sections_out, boards_out, blocks_all),
                   ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "timeline.json").write_text(json.dumps({"meta": meta, "boards": boards_out,
                                                       "events": events}, ensure_ascii=False,
                                                      indent=1), encoding="utf-8")
    (out_dir / "audio_index.json").write_text(json.dumps(audio_index, ensure_ascii=False,
                                                         indent=1), encoding="utf-8")
    template = (REPO_ROOT / "spike" / "scripts" / "board_player_template.html").read_text(encoding="utf-8")
    title = ("SILENT PREVIEW - " if silent else "") + info["lesson"]["title"]
    html = (template.replace("__TITLE__", title)
            .replace("/*__FRAME_CSS__*/", FRAME_CSS)
            .replace("__BUNDLE_JSON__", json.dumps(bundle, ensure_ascii=False).replace("</", "<\\/")))
    (out_dir / "player.html").write_text(html, encoding="utf-8")

    n_utt = sum(len(s["utterances"]) for bd in boards_out for s in bd["states"])
    cues = sum(len(u["cues"]) for bd in boards_out for s in bd["states"] for u in s["utterances"])
    speech = sum(e["duration_s"] for e in audio_index.values())
    words = sum(len(e["words"]) for e in audio_index.values())
    print(f"sections {len(section_marks)} | boards {len(boards_out)} | utterances {n_utt} | "
          f"cues {cues} | erase events {sum(1 for e in events if e['type'] == 'erase')}")
    print(("estimated at " + f"{wpm:g} wpm: " if silent else "with audio: ")
          + f"{total / 60:.1f} min in all, {speech / 60:.1f} min of speech, "
          f"{words / speech * 60:.1f} words per minute of speech | reading pointer on "
          f"{n_read} of {n_utt} utterances")
    for m in sections_out:
        mm, ss = divmod(int(m["start"]), 60)
        print(f"  {mm:3d}:{ss:02d}  {m['id']:<12} {m['title']}")
    print(f"wrote {out_dir / 'player.html'}")
    return out_dir


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--silent", action="store_true")
    ap.add_argument("--wpm", type=float, default=135.0)
    args = ap.parse_args()
    build(args.lesson_dir, args.silent, args.wpm)


if __name__ == "__main__":
    main()
