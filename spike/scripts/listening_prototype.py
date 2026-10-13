"""The Listening boards on the real practice set, for review (docs/adr/030-listening-board-layout.md).

    .venv/Scripts/python spike/scripts/listening_prototype.py <out_dir> [--checks]

Builds three lessons of one board each in <out_dir>, which must be outside git
(the owner's review folder is C:\\OET\\lessons\\_listening-preview), from the pinned
release (practice_set.LISTENING_PIN), through the real free stages: the screens
and narration are rendered from replies written here (no model call), then the
fit and the silent preview, and with --checks the overflow, overlap, lens and
wide-font checks (590, 812 and 1120 px) and the review-page audio check:

  - part-a: Part A extract 1, its transcript and its note form (gaps 1-12);
  - part-b: Part B's longest extract, its transcript and its question;
  - part-c: Part C extract 1, its transcript and its questions (31-36), the
    question shown following the recording's sections.

Each board says one line (a subtitle; no narration voice is made) and plays its
extract from the first word; the silent preview plays the release's own audio,
and the transcript's box and its marker follow the word times (word_times.py).
ADR 029's prototype on placeholder data is replaced: word times exist only for
the released transcripts. The folders hold the release's wording: they never go
into git. Nothing is printed but counts and the checks' results.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import practice_set  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
MARK = ".listening-preview"


def block(**kw) -> dict:
    b = {"type": "plain", "text": None, "label": None, "term": None, "explanation": None, "left": None,
         "right": None, "family": None, "kind": None, "icon": None, "items": None, "header": None,
         "rows": None, "tags": None, "exercise_item": None, "anchor": True, "provenance": "authored",
         "from_beats": ["b1"], "note": "listening preview"}
    b.update(kw)
    return b


def reply(obj: dict) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(obj)}]}


def utt(text: str, cues: list[dict]) -> dict:
    for n, c in enumerate(cues, 1):
        c.setdefault("id", f"c{n}")
        for k in ("block", "text", "to_block", "to_text", "with", "seconds"):
            c.setdefault(k, None)
    return {"text_with_cues": text, "cues": cues, "provenance": "authored", "note": "", "refs": []}


def words(st: dict) -> int:
    return len(st["transcript"]["text"].split())


def parts_of(ps: dict, item: dict) -> list[str]:
    """A question's parts as the screens stage reads them: the wrong options
    ruled out, then the key (never revealed on these boards)."""
    letter = {o["option"]: o["letter"] for o in practice_set.options_of(item)}
    key = letter[item["scoring"]["key_option_id"]]
    return [f"out|{x}|not the answer" for x in sorted(set(letter.values()) - {key})] + [f"key|{key}"]


def build(out_dir: Path, name: str, set_id: str, title: str) -> tuple[Path, dict]:
    L = out_dir / name
    if L.exists():
        if not (L / MARK).exists():
            raise SystemExit(f"REFUSED: {L} exists and is not a preview this script made")
        shutil.rmtree(L)
    (L / "analysis" / "screens" / "added-01").mkdir(parents=True)
    (L / "analysis" / "narration" / "added-01").mkdir(parents=True)
    (L / MARK).write_text("made by listening_prototype.py; safe to delete", encoding="utf-8")
    (L / "analysis" / "sections.json").write_text(json.dumps({
        "lesson": {"title": title, "page": None, "status": "maintainer", "type": "listening",
                   "type_by": "listening_prototype.py", "description": "A review preview of one board.",
                   "description_status": "maintainer", "tense_lesson": False},
        "contents_page": None, "diagram_pages": [],
        "added": [{"page": 101, "title": title, "by": "listening_prototype.py"}],
        "sections": [{"pages": [101], "title": title, "status": "maintainer", "added": True}]}, indent=1),
        encoding="utf-8")
    ps = practice_set.import_set(L, set_id)
    ps["teach_pages"] = [101]
    practice_set.path(L).write_text(json.dumps(ps, ensure_ascii=False, indent=1), encoding="utf-8")
    u = L / "analysis" / "understanding" / "page-101"
    u.mkdir(parents=True)
    (u / "understanding.json").write_text(json.dumps({
        "authored_plan": "preview", "beats": [{"id": "b1", "start": None, "end": None,
                                                "learning_objective": "preview", "teaching_point": "preview",
                                                "provenance": "authored", "confidence": "high", "evidence": {}}],
        "non_teaching": [], "source_errors": [], "persian_dependent": [], "cross_references": [],
        "unknowns": []}), encoding="utf-8")
    # no board picture on a Listening board (ADR 030)
    (L / "analysis" / "pictures.json").write_text(json.dumps({"sections": {}}), encoding="utf-8")
    return L, ps


def screens(L: Path, blocks: list[dict], gap_rows: list[tuple[int, str]]) -> None:
    """One board: the transcript and the question column; on a Part A board a
    thought per gap after the recording, its row's state, with a short note."""
    thoughts = [{"purpose": "Table: the recording", "blocks": blocks}]
    thoughts += [{"purpose": f"Row {r}: gap {m}", "blocks": [block(text=f"Gap {m}.", role="note", anchor=False)]}
                 for r, m in gap_rows]
    (L / "analysis" / "screens" / "added-01" / "raw_response.json").write_text(json.dumps(reply({
        "topics": [{"title": "Listen", "from_beats": ["b1"], "thoughts": thoughts}],
        "corrections": [], "replacements": [], "dropped": [], "unresolved": []})), encoding="utf-8")


def narrate(L: Path, stimulus: str, label: str) -> None:
    """The recording, from its first word, in the board's first state; on a
    Part A board each gap's answer typed in its row's state (a subtitle each)."""
    scr = json.loads((L / "analysis" / "screens" / "added-01" / "screens.json").read_text(encoding="utf-8"))
    bd = scr["boards"][0]
    blocks = {b["id"]: b for t in scr["topics"] for h in t["thoughts"] for b in h["blocks"]}
    form = blocks.get(bd.get("table") or "")
    states = []
    for n, st in enumerate(bd["states"]):
        us = []
        for wid in st["working"]:
            us.append(utt(f"{{{{c1}}}}{blocks[wid].get('text') or 'Look.'}", [{"type": "reveal", "block": wid}]))
        if n == 0:
            us.append(utt(f"Listen to {label}.{{{{c1}}}}", [{"type": "play", "text": stimulus, "with": "extract"}]))
        ty = next((x for x in (form or {}).get("typed") or [] if x["row"] == st.get("row")), None)
        if ty:
            us.append(utt("{{c1}}Here.", [{"type": "type", "block": form["id"], "text": ty["text"]}]))
        states.append({"state": st["id"], "utterances": us or [utt("Look.", [])]})
    out = {"boards": [{"board": bd["id"], "states": states}], "unresolved": []}
    (L / "analysis" / "narration" / "added-01" / "raw_response.json").write_text(json.dumps(reply(out)),
                                                                                  encoding="utf-8")


def run(args: list[str]) -> tuple[int, str]:
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = (r.stdout + r.stderr).strip()
    tail = out.splitlines()[-3:]
    print(f"$ {Path(args[0]).name} {' '.join(a for a in args[2:] if not a.startswith(str(Path('C:/'))))}: "
          f"exit {r.returncode}: " + " | ".join(tail))
    return r.returncode, out


def main() -> None:
    out_dir = Path(sys.argv[1]).resolve()
    if REPO in out_dir.parents or out_dir == REPO:
        raise SystemExit("REFUSED: the preview holds the release's wording; build it outside the repository")
    real = json.loads(practice_set.release_path(practice_set.LISTENING_PIN["release"]).read_text(encoding="utf-8"))
    sets = {s["set_id"]: s for s in real["sets"]}
    la, lb, lc = (sets[k]["parts"][0] for k in practice_set.LISTENING_PIN["sets"])
    a_st, a_it = la["stimuli"][0], la["items"][0]
    b_st = max(lb["stimuli"], key=words)
    b_it = next(i for i in lb["items"] if i["stimulus_ids"] == [b_st["stimulus_id"]])
    c_st = lc["stimuli"][0]
    c_its = [i for i in lc["items"] if i["stimulus_ids"] == [c_st["stimulus_id"]]]
    plan = [("part-a", "oa-set-la-0001", "Listening preview: Part A", a_st,
             [block(type="table", label=a_st["stimulus_id"]), block(type="table", label=a_it["item_id"])]),
            ("part-b", "oa-set-lb-0001", "Listening preview: Part B", b_st,
             [block(type="table", label=b_st["stimulus_id"]), block(label=b_it["item_id"], items=None)]),
            ("part-c", "oa-set-lc-0001", "Listening preview: Part C", c_st,
             [block(type="table", label=c_st["stimulus_id"]), block(label=c_its[0]["item_id"], items=None)])]
    built = []
    for name, set_id, title, st, blocks in plan:
        L, ps = build(out_dir, name, set_id, title)
        for b in blocks:
            if b["type"] == "plain":
                b["items"] = parts_of(ps, practice_set.items(ps)[b["label"]])
        gap_rows = []
        for b in blocks:
            it = practice_set.items(ps).get(b["label"])
            if b["type"] == "table" and it and practice_set.is_gapfill(it):
                fb = practice_set.form_block(ps, it)
                gap_rows = [(n + 1, p["mark"]) for n, p in enumerate(fb["doc"]["parts"]) if p["kind"] == "num"]
        screens(L, blocks, gap_rows)
        run([str(HERE / "write_screens.py"), str(L), "--pages", "101", "--render"])
        narrate(L, st["stimulus_id"], st["label"])
        run([str(HERE / "write_narration.py"), str(L), "--pages", "101", "--render"])
        run([str(HERE / "fit_boards.py"), str(L), "--silent", "--small-phone"])
        run([str(HERE / "build_lesson_player.py"), str(L), "--silent"])
        player = L / "generated" / "lesson-preview" / "silent" / "player.html"
        print(f"{name}: {st['stimulus_id']}, {words(st)} words; {player.as_uri() if player.exists() else 'NOT BUILT'}")
        built.append(L)
    if "--checks" in sys.argv:
        fails = 0
        for L in built:
            d = str(L / "generated" / "lesson-preview" / "silent")
            for c in ("check_board_page.py", "check_overflow.py", "check_overlap.py", "check_lens.py",
                      "check_wide_font.py", "check_question_numbers.py"):
                code, _ = run([str(HERE / c), str(L), "--dir", d])
                fails += code != 0
            code, _ = run([str(HERE / "check_review_page.py"), str(Path(d) / "player.html")])
            fails += code != 0
        print(f"checks: {fails} failed")
        sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
