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
from build_board_bundle import block_tokens, norm, reading_runs   # noqa: E402
from build_board_timeline import lay_timeline                     # noqa: E402
from write_narration import spoken                                # noqa: E402
import board_style                                                # noqa: E402
from write_screens import (FRAME_CSS, TAG_LABELS, block_html,     # noqa: E402
                           block_text_runs, is_exercise_board)

REPO_ROOT = Path(__file__).resolve().parents[2]

FORMAT_VERSION = "1.10"             # docs/04-LESSON-BUNDLE.md; 1.1 refs, 1.2 table boards, 1.3 board style, 1.4 table cells, 1.5 tense colours by lesson, 1.6 choice tables and marks in cells, 1.7 the clause diagram, 1.8 clears and table fit, 1.9 relative and participle clauses in the clause diagram, 1.10 the gloss block
READING_HOLD_S = 2.5               # the pointer stays on the last word read this long
# Everything block_html draws from; pipeline notes (anchor, from_beats, note,
# relabelled, ruling) stay in screens.json.
BLOCK_FIELDS = ("id", "type", "label", "text", "term", "explanation", "left", "right",
                "family", "col_families", "kind", "icon", "items", "header", "rows",
                "tags", "exercise_item", "provenance",
                # 1.2, table boards (ADR 007)
                "core", "col_widths", "font", "typed", "beside",
                # 1.3, kinds of content and the board style (ADR 008)
                "role", "style", "card", "pin", "fold_into", "flow", "band",
                # 1.6, choice tables (ADR 009)
                "verdicts")


def block_data(b: dict) -> dict:
    """A block's data as the bundle carries it: every field its html is drawn
    from, each tense tag with the label printed on its chip."""
    d = {k: b.get(k) for k in BLOCK_FIELDS}
    tags = [dict(t, label=TAG_LABELS[t["family"]]) for t in (b.get("tags") or [])
            if t.get("text") and t.get("family") in TAG_LABELS]
    d["tags"] = tags or None
    return d


# A clip's own silence before its first sound and after its last is not part
# of the lesson's timing (maintainer, 2026-09-25): each clip plays from
# `clip_in` to `clip_out`, found in its signal, and every gap and pause the
# timeline lays out stays exactly as it is. No audio is re-made.
TRIM_DB = -40.0          # sound is anything louder than this, in 10 ms windows
TRIM_KEEP_IN = 0.03      # seconds kept before the first sound
TRIM_KEEP_OUT = 0.05     # and after the last


def trim_clip(path: Path, e: dict) -> None:
    """Set the entry's clip_in and clip_out from the WAV's signal, and make its
    duration and word times the trimmed clip's. Never cuts into a word."""
    import wave
    import numpy as np
    with wave.open(str(path), "rb") as w:
        sr, n = w.getframerate(), w.getnframes()
        a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    win = int(sr * 0.01)
    env = np.array([np.abs(a[i:i + win]).max() for i in range(0, max(1, len(a) - win), win)])
    loud = np.where(env > 10 ** (TRIM_DB / 20))[0]
    dur = n / sr
    if not len(loud) or not e.get("word_start"):
        e.update(clip_in=0.0, clip_out=round(dur, 3))
        return
    cin = min(max(0.0, loud[0] * 0.01 - TRIM_KEEP_IN), e["word_start"][0])
    cout = max(min(dur, (loud[-1] + 1) * 0.01 + TRIM_KEEP_OUT), min(dur, e["word_end"][-1]))
    e["clip_in"], e["clip_out"] = round(cin, 3), round(cout, 3)
    e["duration_s"] = round(cout - cin, 3)
    e["word_start"] = [round(x - cin, 3) for x in e["word_start"]]
    e["word_end"] = [round(x - cin, 3) for x in e["word_end"]]


def table_cells(b: dict) -> list[tuple[int, int]]:
    """(row, column) of each word of a table, in block_tokens order; the header
    is row -1. What the reading pointer reads tells the spotlight which cell."""
    cells = [(-1, c, x) for c, x in enumerate(b.get("header") or [])]
    cells += [(r, c, x) for r, row in enumerate(b.get("rows") or []) for c, x in enumerate(row)]
    return [(r, c) for r, c, x in cells if x for w in x.split() if norm(w)]


def table_cell_of(table: dict, text: str, row: int | None) -> tuple[int, int] | None:
    """The cell a mark on a table lands in (bundle 1.6): the first cell of the
    state's row that holds the phrase, else the first cell of the table that
    does; None when only the header holds it."""
    rows = table.get("rows") or []
    if not text:
        return None
    order = ([row] if row is not None and row < len(rows) else []) + list(range(len(rows)))
    for r in order:
        for k, x in enumerate(rows[r]):
            if text in x:
                return (r, k)
    return None


def table_verdicts(bd: dict, table: dict) -> list[dict]:
    """A choice table's verdicts with the time each shows (bundle 1.6): a wrong
    cell fades at its first strike, or when its row is settled (the row's last
    speech ends) if never struck; the right cell takes its tick at its first
    circle, or when the row's last wrong cell fades; a possible cell is marked
    when the row is settled. From then until the board's `until`."""
    vs = table.get("verdicts") or []
    if not vs:
        return []
    strikes: dict[tuple[int, int], float] = {}
    circles: dict[tuple[int, int], float] = {}
    settle: dict[int, float] = {}
    for s in bd["states"]:
        if s.get("row") is not None:
            settle[s["row"]] = max(settle.get(s["row"], 0.0), s["end"])
        for u in s["utterances"]:
            for c in u["cues"]:
                if c.get("block") != table["id"] or c.get("row") is None:
                    continue
                if c["type"] == "strike":
                    strikes.setdefault((c["row"], c["col"]), c["time"])
                elif c["type"] == "circle":
                    circles.setdefault((c["row"], c["col"]), c["time"])
    last = bd["states"][-1]["end"] if bd["states"] else bd["start"]
    out = []
    for r in sorted({v["row"] for v in vs}):
        end = settle.get(r, last)
        row_vs = [v for v in vs if v["row"] == r]
        fades = []
        for v in row_vs:
            if v["verdict"] == "wrong":
                t = min(strikes.get((r, v["col"]), end), end)
                fades.append(t)
                out.append({"row": r, "col": v["col"], "verdict": "wrong", "time": round(t, 3)})
        for v in row_vs:
            if v["verdict"] == "right":
                t = circles.get((r, v["col"]))
                if t is None or t > end:
                    t = max(fades) if fades else end
                out.append({"row": r, "col": v["col"], "verdict": "right", "time": round(t, 3)})
            elif v["verdict"] == "possible":
                out.append({"row": r, "col": v["col"], "verdict": "possible", "time": round(end, 3)})
    return sorted(out, key=lambda x: (x["time"], x["row"], x["col"]))


def table_focus(bd: dict, table: dict, cells: list[tuple[int, int]]) -> list[dict]:
    """The spotlight of a table board, stated for the renderer (bundle 1.2): at
    each time, the row in focus and the cell highlighted, or null for the
    whole table. A row's state brings its row into focus; the cell follows
    what is read aloud, typed or marked in the table; when a row ends, before
    another row or at the board's end, the whole table shows again."""
    tid = table["id"]
    ev: list[tuple[float, int | None, int | None]] = []
    states = bd["states"]
    for n, s in enumerate(states):
        row = s.get("row")
        ev.append((s["start"], row, None))
        for u in s["utterances"]:
            for run in u.get("reading") or []:
                if run["block"] == tid:
                    for k, t0, _ in run["words"]:
                        r, c = cells[k]
                        if r >= 0:
                            ev.append((t0, r, c))
            for c in u["cues"]:
                if c.get("block") != tid or c["type"] in ("reveal", "pause"):
                    continue
                if c["type"] == "type" or c.get("row") is not None:     # 1.6: a mark names its cell
                    ev.append((c["time"], c["row"], c["col"]))
                    continue
                hits = [(r, k) for r, rw in enumerate(table.get("rows") or [])
                        for k, x in enumerate(rw) if c.get("text") and c["text"] in x]
                hits.sort(key=lambda h: h[0] != row)
                if hits:
                    ev.append((c["time"], hits[0][0], hits[0][1]))
        nxt = states[n + 1].get("row") if n + 1 < len(states) else "end"
        if row is not None and nxt != row:
            ev.append((s["until"], None, None))
    ev.sort(key=lambda e: e[0])
    out: list[dict] = []
    for t, r, c in ev:
        if out and (out[-1]["row"], out[-1]["col"]) == (r, c):
            continue
        out.append({"time": round(t, 3), "row": r, "col": c})
    return out


def diagram_parts(b: dict) -> list[str]:
    """Part ids of a diagram block, as its html names them (data-part)."""
    if b["type"] not in ("timeline", "clauses", "gloss"):
        return []
    return [f"{b['id']}.{it.get('part', 0)}" for it in b.get("items") or []]


def block_plain(b: dict) -> str:
    """A block's words as plain text: its text runs one per line, a table one
    row per line with cells separated by ' | '."""
    if b["type"] == "table":
        lines = [" | ".join(b.get("header") or [])] + [" | ".join(r) for r in b.get("rows") or []]
        lines = [x.replace(" / ", "; ") for x in lines]
        return "\n".join(x for x in lines if x.strip(" |"))
    return "\n".join(board_style.display_runs(b, block_text_runs))


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
                        "narration": [{"id": u["id"], "start": u["start"], "text": u["text"],
                                       "refs": u["refs"]}
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


def build(L: Path, silent: bool, wpm: float = 135.0, only: list[str] | None = None,
          out: str | None = None, use_fit: bool = True) -> Path:
    info, secs = lesson_sections(L)
    if only:
        # a sample of some sections (a design review), in its own folder
        secs = [s for s in secs if paths.section_tag(s["pages"]) in only]
        info = dict(info, categories=[])
    out_dir = L / "generated" / (out or ("lesson-preview/silent" if silent else "lesson-player"))
    out_dir.mkdir(parents=True, exist_ok=True)

    boards_all, blocks_all, audio_index, section_marks = [], {}, {}, []
    # 1.8: the fit (fit_boards.py): where a state's notes are cleared so the
    # next one fits the board, and a table's text size where the table did not
    fit_path = L / "analysis" / "fit.json"
    fit = json.loads(fit_path.read_text(encoding="utf-8")) if use_fit and fit_path.exists() else {}
    table_of: dict[str, str] = {}
    links_of: dict[str, tuple] = {}
    row_of: dict[str, int | None] = {}
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
        # a table board's table and each state's row (screens.json, ADR 007)
        for sb in scr["boards"]:
            links_of[pre + sb["id"]] = (
                [dict(x, block=pre + x["block"], card=(pre + x["card"]) if x.get("card") else None)
                 for x in sb.get("wordlinks") or []],
                [dict(x, block=pre + x["block"]) for x in sb.get("slidemarks") or []])
            if sb.get("table"):
                table_of[pre + sb["id"]] = pre + sb["table"]
            for ss in sb["states"]:
                row_of[pre + ss["id"]] = ss.get("row")
        for bid, b in blocks.items():
            nb = copy.deepcopy(b)
            nb["id"] = pre + bid
            if nb.get("beside"):
                nb["beside"] = {"block": pre + nb["beside"]["block"], "row": nb["beside"]["row"]}
            if nb.get("fold_into"):
                nb["fold_into"] = pre + nb["fold_into"]
            if not nb.get("role") and nb["type"] == "plain":
                nb["role"] = "slide"        # the title board's description: the lesson's own words
            if not info["lesson"].get("tense_lesson"):
                nb["tense_neutral"] = True
            if nb["id"] in (fit.get("fonts") or {}):
                nb["font"] = fit["fonts"][nb["id"]]      # 1.8: smaller, so the table fits
            blocks_all[pre + bid] = {**block_data(nb), "html": block_html(nb),
                                     "_tokens": block_tokens(b)}     # display words (1.3)
        section_marks.append({"id": tag, "title": sec["title"], "pages": pages,
                              "intro": bool(sec.get("intro")),
                              "first_board": None, "boards": []})
        for bd in narr["boards"]:
            nbd = {"id": pre + bd["id"], "title": bd["title"],
                   "fixed": [pre + i for i in bd["fixed"] if not blocks[i].get("fold_into")],
                   "states": []}
            for s in bd["states"]:
                ns = {"id": pre + s["id"], "working": [pre + i for i in s["working"]],
                      "erase_after": ({"blocks": [pre + i for i in s["erase_after"]["blocks"]]}
                                      if s.get("erase_after") else None),
                      "utterances": []}
                for u in s["utterances"]:
                    nu = copy.deepcopy(u)
                    nu["id"] = pre + u["id"]
                    for c in nu["cues"]:
                        for key, tkey in (("block", "text"), ("to_block", "to_text")):
                            if not c.get(key):
                                continue
                            b0 = blocks.get(c[key].split(".")[0])
                            if b0 and b0.get("fold_into") and c.get(tkey):
                                host = blocks[b0["fold_into"]]
                                hit = board_style._stem_find(host["text"], c[tkey])
                                c["retargeted_from"] = pre + c[key]
                                c[key] = b0["fold_into"]
                                c[tkey] = hit or c[tkey]
                            elif b0:
                                c[tkey] = board_style.display_phrase(b0, c.get(tkey))
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

    if not silent:
        for e in audio_index.values():
            trim_clip(out_dir / e["file"], e)
    narr_all = {"lesson": L.name, "boards": boards_all}
    gaps = {"utterance_gap_s": 0.4, "state_gap_s": 1.2, "board_gap_s": 1.5, "cue_lead_s": 0.35}
    boards_out, events, total = lay_timeline(narr_all, audio_index, gaps["utterance_gap_s"],
                                             gaps["state_gap_s"], gaps["board_gap_s"],
                                             gaps["cue_lead_s"])

    tokens = {i: b.pop("_tokens") for i, b in blocks_all.items()}
    for bd in boards_out:
        for s in bd["states"]:
            for u in s["utterances"]:
                e = audio_index[u["id"]]
                u["clip_in"], u["clip_out"] = e.get("clip_in"), e.get("clip_out")   # 1.3
    # A type cue names the typed part it types (its index in the table's
    # `typed`, and that part's row and column): the first part with its text
    # not yet typed on the board, as the narration audit counted them.
    for bd in boards_out:
        done: dict[str, list[int]] = {}
        for s in bd["states"]:
            for u in s["utterances"]:
                for c in u["cues"]:
                    if c["type"] != "type":
                        continue
                    typed = blocks_all[c["block"]].get("typed") or []
                    got = done.setdefault(c["block"], [])
                    i = next(k for k, ty in enumerate(typed) if ty["text"] == c["text"] and k not in got)
                    got.append(i)
                    c.update(typed=i, row=typed[i]["row"], col=typed[i]["col"])
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
        # 1.2: a table board's table, each state's row, and the spotlight
        bd["table"] = table_of.get(bd["id"])
        for s in bd["states"]:
            s["row"] = row_of.get(s["id"]) if bd["table"] else None
        # 1.6: a mark on the table names the cell it lands in, the state's row
        # first, as the narration audit requires its phrase to be in one cell
        if bd["table"]:
            tb = blocks_all[bd["table"]]
            for s in bd["states"]:
                for u in s["utterances"]:
                    for c in u["cues"]:
                        if c.get("block") == bd["table"] and c["type"] not in ("reveal", "pause", "type") \
                                and c.get("row") is None:
                            rc = table_cell_of(tb, c.get("text") or "", s["row"])
                            if rc:
                                c.update(row=rc[0], col=rc[1])
                        if c["type"] == "arrow" and (c.get("to_block") or c.get("block")) == bd["table"] \
                                and c.get("to_row") is None:
                            rc = table_cell_of(tb, c.get("to_text") or "", s["row"])
                            if rc:
                                c.update(to_row=rc[0], to_col=rc[1])
        bd["focus"] = (table_focus(bd, blocks_all[bd["table"]], table_cells(blocks_all[bd["table"]]))
                       if bd["table"] else [])
        bd["verdicts"] = table_verdicts(bd, blocks_all[bd["table"]]) if bd["table"] else []
        # 1.3: a pinned block stays from its reveal to the board's end; a
        # word mark colours a changing word by its word class from the moment
        # its change card appears or the word is first marked, whichever is
        # first (never before its block is on the board); the slide's own
        # underline is there from the start
        bd["pinned"] = {i: s["reveal"][i] for s in bd["states"] for i in s["working"]
                        if blocks_all[i].get("pin") and i in s["reveal"]}
        # 1.8: a tight board, from the fit: 0, or 1 (half the gap between
        # blocks), or 2 (and half the blocks' vertical padding)
        bd["tight"] = int((fit.get("tight") or {}).get(bd["id"], 0))
        # 1.8: a clear inside a state, from the fit: as `before` appears, the
        # working blocks shown before it are cleared (never a pinned one)
        for s in bd["states"]:
            s["clears"], gone = [], set()
            for c in (fit.get("clears") or {}).get(s["id"], []):
                at = s["reveal"].get(c)
                if at is None:
                    print(f"WARN fit: {s['id']} clears before {c}, which it does not reveal")
                    continue
                ids = [w for w in s["working"] if w not in bd["pinned"] and w not in gone
                       and s["reveal"].get(w, at) < at]
                if ids:
                    s["clears"].append({"time": at, "blocks": ids})
                    gone.update(ids)
            s["clears"].sort(key=lambda c: c["time"])
        links, smarks = links_of.get(bd["id"], ([], []))
        shown = {i: bd["start"] for i in bd["fixed"]}
        for s in bd["states"]:
            for i, at in s["reveal"].items():
                shown.setdefault(i, at)
        marks = [(c, u) for s in bd["states"] for u in s["utterances"] for c in u["cues"]
                 if c["type"] not in ("reveal", "pause", "type")]
        wm = []
        types = [c for s in bd["states"] for u in s["utterances"] for c in u["cues"] if c["type"] == "type"]
        for x in links:
            if x["block"] not in shown or (x.get("card") and x["card"] not in shown):
                continue
            first = [c["time"] for c, _ in marks if c.get("block") == x["block"] and c.get("text")
                     and (c["text"].lower() in x["text"].lower() or x["text"].lower() in c["text"].lower())]
            cand = first + ([shown[x["card"]]] if x.get("card") else [])
            if x.get("row") is not None:
                # a word in a table cell: coloured when its typing ends if it is typed,
                # otherwise when its row is first typed into, or first marked
                cell = blocks_all[x["block"]]["rows"][x["row"]][x["col"]]
                pos = cell.find(x["text"])
                typed = [c for c in types if c["block"] == x["block"] and c["row"] == x["row"]
                         and c["col"] == x["col"]]
                cover = [c for c in typed if (blocks_all[x["block"]]["typed"][c["typed"]]["start"] <= pos
                         < blocks_all[x["block"]]["typed"][c["typed"]]["start"]
                         + len(blocks_all[x["block"]]["typed"][c["typed"]]["text"]))]
                if cover:
                    cand = [cover[0]["time_end"]]
                else:
                    cand += [c["time"] for c in types if c["block"] == x["block"] and c["row"] == x["row"]]
                    cand += [f["time"] for f in bd.get("focus") or [] if f["row"] == x["row"]][:1]
            at = min(cand) if cand else shown[x["block"]]
            w = {"block": x["block"], "text": x["text"], "cls": x["cls"],
                 "time": round(max(shown[x["block"]], at), 3)}
            if x.get("row") is not None:
                w.update(row=x["row"], col=x["col"])
            wm.append(w)
        wm += [{"block": x["block"], "text": x["text"], "cls": "slide-underline", "time": bd["start"]}
               for x in smarks if x["block"] in shown]
        bd["wordmarks"] = sorted(wm, key=lambda x: x["time"])


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
              # 1.5: tense colours are drawn only in a lesson about tenses
              "tense_colours": bool(info["lesson"].get("tense_lesson")),
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
    ap.add_argument("--sections", help="build only these sections (tags, comma-separated): a sample")
    ap.add_argument("--out", help="folder under generated/ for a sample build")
    args = ap.parse_args()
    if bool(args.sections) != bool(args.out):
        raise SystemExit("--sections and --out go together: a sample never replaces the lesson's player")
    build(args.lesson_dir, args.silent, args.wpm,
          args.sections.split(",") if args.sections else None, args.out)


if __name__ == "__main__":
    main()
