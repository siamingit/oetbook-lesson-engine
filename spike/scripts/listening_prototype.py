"""The Listening boards on the real practice set, for review (docs/adr/030-listening-board-layout.md,
docs/adr/031-listening-vocabulary-panel.md).

    .venv/Scripts/python spike/scripts/listening_prototype.py <out_dir> [--checks]

Builds three lessons in <out_dir>, which must be outside git (the owner's review
folder is C:\\OET\\lessons\\_listening-preview), from the pinned release
(practice_set.LISTENING_PIN), through the real free stages: the screens and
narration are rendered from replies written here (no model call), then the fit
and the silent preview, and with --checks the overflow, overlap, lens and
wide-font checks (590, 812 and 1120 px), the review-page audio check and the
narration's variety check (pause-and-try prompts and vocabulary explanations):

  - part-a: Part A extract 1, its transcript and its note form (gaps 1-12), the
    recording played with its reading time (the form whole meanwhile);
  - part-b: Part B's longest extract, its transcript and its question;
  - part-c: Part C extract 1 and questions 31 and 32, a board each.

What each board shows and says is read from <out_dir>/preview-content.json:
the steps (a thought and its state each), the vocabulary panel's items and the
lines that teach them (ADR 031). That file and the folders hold the release's
wording, so they never go into git. No narration voice is made: the lines are
subtitles; the silent preview plays the release's own audio, and the
transcript's box and its marker follow the word times (word_times.py).
Nothing is printed but counts and the checks' results.
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
CONTENT = "preview-content.json"   # in <out_dir>: the boards' steps, the panel items, the lines (ADR 031)


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


def resolve(spec: dict, ps: dict, st: dict) -> dict:
    """A block of the content file as the screens stage's reply writes it."""
    key = spec["key"]
    if key == "transcript":
        return block(type="table", label=st["stimulus_id"])
    if key == "form":
        it = next(i for i in practice_set.items(ps).values()
                  if practice_set.is_gapfill(i) and st["stimulus_id"] in i["stimulus_ids"])
        return block(type="table", label=it["item_id"])
    if "question" in spec:
        it = practice_set.items(ps)[spec["question"]]
        letter = {o["option"]: o["letter"] for o in practice_set.options_of(it)}
        k = letter[it["scoring"]["key_option_id"]]
        why = spec.get("reasons") or {}
        return block(label=it["item_id"], anchor=False,
                     items=[f"out|{x}|{why.get(x, 'not the answer')}" for x in sorted(set(letter.values()) - {k})]
                     + [f"key|{k}"])
    if "panel" in spec:
        w = spec["panel"]
        return block(type="gloss", label=f"PANEL Row {w['row']}", term=w["term"], kind=w["kind"],
                     explanation=w["explanation"], synonym=w["synonym"], text=w["text"], left=w.get("left"),
                     anchor=False, note="listening preview: a vocabulary panel item (ADR 031)")
    return block(text=spec["note"], role="note", anchor=False)


def screens(L: Path, content: dict, ps: dict, st: dict) -> None:
    """The boards of the content file: one topic each, a thought per step."""
    topics = [{"title": "Listen", "from_beats": ["b1"],
               "thoughts": [{"purpose": step["purpose"], "blocks": [resolve(x, ps, st) for x in step.get("blocks", [])]}
                            for step in bd["steps"]]}
              for bd in content["boards"]]
    (L / "analysis" / "screens" / "added-01" / "raw_response.json").write_text(json.dumps(reply({
        "topics": topics, "corrections": [], "replacements": [], "dropped": [], "unresolved": []})), encoding="utf-8")


def narrate(L: Path, content: dict, st: dict) -> None:
    """The narration of the content file, a state per step: its utterances, each
    cue's block named by its key in the content file ("@key", or "@key.N" for a
    part), the recording by "@stimulus", a gap's typed answer by "@typed"."""
    scr = json.loads((L / "analysis" / "screens" / "added-01" / "screens.json").read_text(encoding="utf-8"))
    by_id = {b["id"]: b for t in scr["topics"] for h in t["thoughts"] for b in h["blocks"]}
    boards = []
    for bd, cb, t in zip(scr["boards"], content["boards"], scr["topics"]):
        keys = {}
        for h, step in zip(t["thoughts"], cb["steps"]):
            for b, spec in zip(h["blocks"], step.get("blocks", [])):
                keys[spec["key"]] = b["id"]
        if len(bd["states"]) != len(cb["steps"]):
            raise SystemExit(f"{L.name}: {len(bd['states'])} states for {len(cb['steps'])} steps: a step is a state")
        form = by_id.get(bd.get("table") or "")
        states = []
        for s, step in zip(bd["states"], cb["steps"]):
            us = []
            for u in step["say"]:
                cues = []
                for c in u["cues"]:
                    c = dict(c)
                    if c.get("block"):
                        k, _, part = c["block"].lstrip("@").partition(".")
                        c["block"] = keys[k] + (f".{part}" if part else "")
                    if c.get("text") == "@stimulus":
                        c["text"] = st["stimulus_id"]
                    if c.get("text") == "@typed":
                        c["text"] = next(x["text"] for x in form["typed"] if x["row"] == s["row"])
                    cues.append(c)
                us.append(utt(u["text"], cues))
            states.append({"state": s["id"], "utterances": us})
        boards.append({"board": bd["id"], "states": states})
    (L / "analysis" / "narration" / "added-01" / "raw_response.json").write_text(
        json.dumps(reply({"boards": boards, "unresolved": []})), encoding="utf-8")


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
    cfile = out_dir / CONTENT
    if not cfile.exists():
        raise SystemExit(f"REFUSED: {cfile} is missing: the boards, the panel items and the lines that "
                         "teach them are written there, outside git, as they hold the release's words")
    content = json.loads(cfile.read_text(encoding="utf-8"))
    real = json.loads(practice_set.release_path(practice_set.LISTENING_PIN["release"]).read_text(encoding="utf-8"))
    sets = {s["set_id"]: s for s in real["sets"]}
    la, lb, lc = (sets[k]["parts"][0] for k in practice_set.LISTENING_PIN["sets"])
    plan = [("part-a", "oa-set-la-0001", "Listening preview: Part A", la["stimuli"][0]),
            ("part-b", "oa-set-lb-0001", "Listening preview: Part B", max(lb["stimuli"], key=words)),
            ("part-c", "oa-set-lc-0001", "Listening preview: Part C", lc["stimuli"][0])]
    built = []
    for name, set_id, title, st in plan:
        L, ps = build(out_dir, name, set_id, title)
        screens(L, content[name], ps, st)
        run([str(HERE / "write_screens.py"), str(L), "--pages", "101", "--render"])
        narrate(L, content[name], st)
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
            code, _ = run([str(HERE / "listening_rule.py"), str(L), "--prompts"])
            fails += code != 0
        print(f"checks: {fails} failed")
        sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
