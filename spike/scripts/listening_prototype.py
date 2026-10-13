"""A Listening prototype lesson on placeholder data (docs/adr/029-listening-lessons.md).

    .venv/Scripts/python spike/scripts/listening_prototype.py <library_dir> [--checks]

Builds `<library_dir>/listening-90-prototype/` (never in git, never in C:\\OET\\lessons)
and runs it through the real free stages: the screens and narration are rendered
from replies written here (no model call), the fit, the silent preview, and with
--checks the overflow, overlap, lens and wide-font checks at the three frames.
It proves the three Listening layouts of bundle 1.18 (ADR 029):

  - Part A: the note form as a table board, its gaps filled by the lesson;
  - Part B: a question board in two columns, the transcript covered, then whole;
  - Part C: a question board whose transcript is shown a section at a time;

and a recording in the lesson's clock (a `play` cue), the spotlight following
the transcript while it plays.

The data is a PLACEHOLDER of the pinned release's sets (practice_set.LISTENING_PIN):
every word of a transcript, note form or question is replaced by a made-up word
of the same length (digits by digits, punctuation kept), so each board is as
dense as the real one and no set wording is copied. Speakers are "Speaker 1"
and "Speaker 2". The worst cases of the analysis are used: Part A extract 1's
form, Part B's longest extract (e3), and Part C's longest question section (the
longest run of interview turns under about 280 words). The audio is the real
extract's file, copied unchanged (the spans and turn times are the release's
numbers). Nothing is printed but counts and the checks' results.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import practice_set  # noqa: E402

HERE = Path(__file__).resolve().parent
LESSON = "listening-90-prototype"
CONS, VOW = "bdfgklmnprstv", "aeiou"


def pseudo_word(w: str, salt: int) -> str:
    """A made-up word of the same shape: letters by letters (case kept),
    digits by digits, everything else kept."""
    out, n = [], salt
    for ch in w:
        if ch.isalpha():
            pool = VOW if len(out) % 2 else CONS
            c = pool[n % len(pool)]
            out.append(c.upper() if ch.isupper() else c)
            n += 7
        elif ch.isdigit():
            out.append(str((int(ch) + 3) % 10))
        else:
            out.append(ch)
    return "".join(out)


def pseudo(text: str, salt: int = 0, keep: tuple[str, ...] = ()) -> str:
    """A placeholder of a line: each word a made-up word of its length;
    the strings in `keep` (a gap's blank) are kept as they are."""
    parts = re.split("(" + "|".join(re.escape(k) for k in keep) + ")", text) if keep else [text]
    out = []
    for p in parts:
        if p in keep:
            out.append(p)
        else:
            out.append(re.sub(r"\S+", lambda m: pseudo_word(m.group(0), salt + m.start()), p))
    return "".join(out)


def speakers_map(st: dict) -> dict[str, str]:
    return {lab: f"Speaker {n}" for n, lab in enumerate(practice_set.speakers_of(st), 1)}


def placeholder_stimulus(st: dict, new_id: str) -> dict:
    sp = speakers_map(st)
    lines = []
    for n, p in enumerate(practice_set.transcript_parts(st)):
        if p.get("speaker"):
            rest = p["text"][len(p["speaker"]) + 1:]
            lines.append(sp[p["speaker"]] + ":" + pseudo(rest, n * 31))
        else:
            lines.append(pseudo(p["text"], n * 31))
    return {"stimulus_id": new_id, "type": "audio-extract", "label": st["label"],
            "speakers": [{"label": v} for v in sp.values()],
            "transcript": {"format": "oa-transcript-v1", "text": "\n".join(lines)},
            "audio": {k: st["audio"][k] for k in ("path", "media_type", "sha256", "bytes", "duration_s", "segments")},
            "reading_time_s": st.get("reading_time_s"),
            "admin": {"turn_starts_s": list((st.get("admin") or {}).get("turn_starts_s") or [])}}


def placeholder_gapfill(it: dict, new_id: str, stim_id: str) -> dict:
    gaps = []
    for g in practice_set.gaps_of(it):
        ans = pseudo(practice_set.gap_key(g)["answer"], g["number"] * 13)
        gaps.append({"gap_id": f"{new_id}-g{g['number']:02d}", "number": g["number"],
                     "heading": pseudo(g["heading"], 5) if g.get("heading") else None,
                     "prompt": pseudo(g["prompt"], g["number"] * 17, keep=(practice_set.GAP,)),
                     "response": {"max_words": 3}, "scoring": {"accepted": [ans]},
                     "feedback": {"key": "placeholder", "wrong_answers": []}})
    return {"item_id": new_id, "type": "gapfill", "numbers": [g["number"] for g in gaps],
            "stimulus_ids": [stim_id], "title": pseudo(it["title"], 3), "gaps": gaps}


def placeholder_choice(it: dict, new_id: str, stim_id: str) -> dict:
    opts = [{"option_id": f"{new_id}-o{n}", "text": pseudo(o["text"], n * 11)}
            for n, o in enumerate(it["options"], 1)]
    old = [o["option_id"] for o in it["options"]]
    key = opts[old.index(it["scoring"]["key_option_id"])]["option_id"]
    order = [opts[old.index(x)]["option_id"] for x in (it.get("display_order") or old)]
    return {"item_id": new_id, "number": it["number"], "type": "choice", "stimulus_ids": [stim_id],
            "stem": pseudo(it["stem"], 7), "options": opts, "display_order": order,
            "scoring": {"key_option_id": key},
            "feedback": {"key": "placeholder", "options": {o["option_id"]: {"why_wrong": "placeholder"}
                                                           for o in opts if o["option_id"] != key}}}


def words(line: str) -> int:
    return len(line.split())


def longest_section(st: dict, limit: int = 280) -> tuple[int, int]:
    """The longest run of neighbouring turns (rows, from 1) under `limit` words:
    the worst case of a Part C question's section on its board."""
    rows = [words(p["text"]) for p in practice_set.transcript_parts(st)]
    best = (1, 1, 0)
    for a in range(len(rows)):
        n = 0
        for b in range(a, len(rows)):
            n += rows[b]
            if n > limit:
                break
            if n > best[2]:
                best = (a + 1, b + 1, n)
    return best[0], best[1]


def block(**kw) -> dict:
    b = {"type": "plain", "text": None, "label": None, "term": None, "explanation": None, "left": None,
         "right": None, "family": None, "kind": None, "icon": None, "items": None, "header": None,
         "rows": None, "tags": None, "exercise_item": None, "anchor": False, "provenance": "authored",
         "from_beats": ["b1"], "note": "listening prototype: placeholder"}
    b.update(kw)
    return b


def note(text: str) -> dict:
    return block(text=text, role="note")


def reply(topics: list[dict]) -> dict:
    out = {"topics": topics, "corrections": [], "replacements": [], "dropped": [], "unresolved": []}
    return {"content": [{"type": "text", "text": json.dumps(out)}]}


def utt(text: str, cues: list[dict] | None = None) -> dict:
    cues = cues or []
    for n, c in enumerate(cues, 1):
        c.setdefault("id", f"c{n}")
        for k in ("block", "text", "to_block", "to_text", "with", "seconds"):
            c.setdefault(k, None)
    return {"text_with_cues": text, "cues": cues, "provenance": "authored", "note": "", "refs": []}


def build(library: Path) -> Path:
    real = json.loads(practice_set.release_path(practice_set.LISTENING_PIN["release"]).read_text(encoding="utf-8"))
    sets = {s["set_id"]: s for s in real["sets"]}
    la, lb, lc = (sets[k]["parts"][0] for k in practice_set.LISTENING_PIN["sets"])
    a_st, a_it = la["stimuli"][0], la["items"][0]
    b_st = max(lb["stimuli"], key=lambda st: words(st["transcript"]["text"]))
    b_it = next(i for i in lb["items"] if i["stimulus_ids"] == [b_st["stimulus_id"]])
    c_st = lc["stimuli"][0]
    c_it = next(i for i in lc["items"] if i["stimulus_ids"] == [c_st["stimulus_id"]])
    sa, sb, sc = "oa-set-lx-9901-e1", "oa-set-lx-9901-e2", "oa-set-lx-9901-e3"
    ps = {"format": "oetbook-practice-set", "adr": "029",
          "release": {"package_id": "placeholder of " + real["package_id"], "package_version": real["package_version"],
                      "created_at": real["created_at"], "source": "placeholder",
                      "file": str(practice_set.release_path(practice_set.LISTENING_PIN["release"]))},
          "set_id": "oa-set-lx-9901", "title": "Listening prototype (placeholder data)",
          "parts": [{"code": "LA", "stimuli": [placeholder_stimulus(a_st, sa)],
                     "items": [placeholder_gapfill(a_it, "oa-listening-990043", sa)]},
                    {"code": "LB", "stimuli": [placeholder_stimulus(b_st, sb)],
                     "items": [placeholder_choice(b_it, "oa-listening-990027", sb)]},
                    {"code": "LC", "stimuli": [placeholder_stimulus(c_st, sc)],
                     "items": [placeholder_choice(c_it, "oa-listening-990031", sc)]}],
          "teach_pages": [101, 102, 103],
          "note": "placeholder data for the Listening layouts (listening_prototype.py): no set wording"}
    L = library / LESSON
    if L.exists():
        # a fresh build every time: a section already narrated would keep its old plan
        if not (L / ".listening-prototype").exists():
            raise SystemExit(f"REFUSED: {L} exists and is not a prototype this script made")
        shutil.rmtree(L)
    L.mkdir(parents=True)
    (L / ".listening-prototype").write_text("made by listening_prototype.py; safe to delete", encoding="utf-8")
    for d in ("analysis/screens/added-01", "analysis/screens/added-02", "analysis/screens/added-03",
              "analysis/narration/added-01", "analysis/narration/added-02", "analysis/narration/added-03"):
        (L / d).mkdir(parents=True, exist_ok=True)
    (L / "analysis" / "practice_set.json").write_text(json.dumps(ps, indent=1), encoding="utf-8")
    titles = ["Part A: the note form", "Part B: a question", "Part C: a question"]
    (L / "analysis" / "sections.json").write_text(json.dumps({
        "lesson": {"title": "Listening prototype", "page": None, "status": "maintainer", "type": "listening",
                   "type_by": "listening_prototype.py", "description": "Placeholder data only.",
                   "description_status": "maintainer", "tense_lesson": False},
        "contents_page": None, "diagram_pages": [],
        "added": [{"page": 101 + n, "title": t, "by": "listening_prototype.py"} for n, t in enumerate(titles)],
        "sections": [{"pages": [101 + n], "title": t, "status": "maintainer", "added": True}
                     for n, t in enumerate(titles)]}, indent=1), encoding="utf-8")
    for n in range(3):
        u = L / "analysis" / "understanding" / f"page-{101 + n}"
        u.mkdir(parents=True, exist_ok=True)
        (u / "understanding.json").write_text(json.dumps({
            "authored_plan": "placeholder", "beats": [{"id": "b1", "start": None, "end": None,
                                                        "learning_objective": "placeholder",
                                                        "teaching_point": "placeholder", "provenance": "authored",
                                                        "confidence": "high", "evidence": {}}],
            "non_teaching": [], "source_errors": [], "persian_dependent": [], "cross_references": [],
            "unknowns": []}), encoding="utf-8")
    # a picture on every board (ADR 021), but the note form's: the form is its
    # board's picture (ADR 029; the form does not fit with one, even at 10%)
    (L / "analysis" / "pictures.json").write_text(json.dumps({"sections": {
        "added-01": [{"topic": 2, "brief": "a placeholder picture | a placeholder"}],
        **{f"added-0{n}": [{"topic": 1, "brief": "a placeholder picture | a placeholder"}] for n in (2, 3)}}}),
        encoding="utf-8")

    # ---- Part A: the note form, the recording, the gaps filled ----
    form = practice_set.form_block(ps, ps["parts"][0]["items"][0])
    kinds = [p["kind"] for p in form["doc"]["parts"]]
    gap_rows = [n + 1 for n, k in enumerate(kinds) if k == "num"]
    th = [{"purpose": "Table: the headings", "blocks": [block(type="table", label="oa-listening-990043", anchor=True),
                                                        note("Read the headings first.")]}]
    th += [{"purpose": f"Row {r}: gap", "blocks": [note("What kind of word is missing here?")]}
           for n, r in enumerate(gap_rows)]
    th += [{"purpose": "Table: listen", "blocks": [note("Now listen once.")]},
           {"purpose": "Table: try it first", "blocks": [note("Try it first: write each answer.")]}]
    th += [{"purpose": f"Row {r}: the answer", "blocks": [note(f"Gap {k + 1}: said by the patient.")]}
           for k, r in enumerate(gap_rows)]
    tr = practice_set.transcript_block(ps["parts"][0]["stimuli"][0])
    n_rows = len(tr["rows"])
    cut = [1, n_rows // 4, n_rows // 2, 3 * n_rows // 4, n_rows]
    th2 = [{"purpose": "Covered: the transcript", "blocks": [block(type="table", label=sa, anchor=True),
                                                             note("The words you heard.")]}]
    th2 += [{"purpose": f"Para {cut[k] + (k > 0)}-{cut[k + 1]}: heading {k + 1}", "blocks": [note("The answers are here.")]}
            for k in range(4)]
    (L / "analysis" / "screens" / "added-01" / "raw_response.json").write_text(json.dumps(reply([
        {"title": "The note form", "from_beats": ["b1"], "thoughts": th},
        {"title": "The transcript", "from_beats": ["b1"], "thoughts": th2}])), encoding="utf-8")

    def parts_for(item: dict) -> tuple[list[str], str]:
        """A question's parts as the screens model writes them, from the key."""
        letter = {o["option"]: o["letter"] for o in practice_set.options_of(item)}
        key = letter[item["scoring"]["key_option_id"]]
        outs = [f"out|{x}|It is said, but it is not the answer." for x in sorted(set(letter.values()) - {key})]
        return outs + [f"key|{key}"], key

    # ---- Part B: two columns, the transcript covered, then whole ----
    b_parts, b_key = parts_for(ps["parts"][1]["items"][0])
    c_parts, c_key = parts_for(ps["parts"][2]["items"][0])
    (L / "analysis" / "screens" / "added-02" / "raw_response.json").write_text(json.dumps(reply([
        {"title": "Question 27", "from_beats": ["b1"], "thoughts": [
            {"purpose": "Covered: the question", "blocks": [
                block(type="table", label=sb, anchor=True),
                block(label="oa-listening-990027", items=b_parts)]},
            {"purpose": "Covered: listen", "blocks": [note("Listen once.")]},
            {"purpose": "Covered: try it first", "blocks": [note("Try it first: which option is right?")]},
            {"purpose": "Covered: the answer", "blocks": [block(type="answer_row", text=f"Answer: {b_key}")]},
            {"purpose": "Row 2: the keywords", "blocks": [note("The same idea in other words.")]},
            {"purpose": "Table: replay", "blocks": [note("Listen to it again.")]}]}])), encoding="utf-8")

    # ---- Part C: a section at a time ----
    c_tr = practice_set.transcript_block(ps["parts"][2]["stimuli"][0])
    a1, a2 = longest_section(ps["parts"][2]["stimuli"][0])
    sec_words = [words(r[0]) for r in c_tr["rows"][a1 - 1:a2]]
    m1 = a1 - 1 + min(range(1, len(sec_words)), key=lambda k: abs(sum(sec_words[:k]) - sum(sec_words[k:])))
    (L / "analysis" / "screens" / "added-03" / "raw_response.json").write_text(json.dumps(reply([
        {"title": "Question 31", "from_beats": ["b1"], "thoughts": [
            {"purpose": "Covered: the question", "blocks": [
                block(type="table", label=sc, anchor=True),
                block(label="oa-listening-990031", items=c_parts)]},
            {"purpose": "Covered: the answer", "blocks": [block(type="answer_row", text=f"Answer: {c_key}")]},
            {"purpose": "Map: where we are", "blocks": [note("The part with the answer.")]},
            # a section too long to show whole is shown as two neighbouring parts (ADR 029)
            {"purpose": f"Para {a1}-{m1}: the section, first part", "blocks": [note("The question's topic starts here.")]},
            {"purpose": f"Para {m1 + 1}-{a2}: the section, second part", "blocks": [note("The speaker changes her mind here.")]},
            {"purpose": "Table: replay", "blocks": [note("Listen to this part again.")]}]}])), encoding="utf-8")
    print(f"placeholder lesson written: {L}; Part A form {len(form['rows'])} rows, transcript {n_rows} rows; "
          f"Part B transcript {sum(words(r[0]) for r in practice_set.transcript_block(ps['parts'][1]['stimuli'][0])['rows'])} "
          f"words; Part C section rows {a1}-{a2} of {len(c_tr['rows'])}")
    return L


def narrate(L: Path) -> None:
    """The narration replies, written to the states the screens stage laid out."""
    ps = practice_set.load(L)
    for tag in ("added-01", "added-02", "added-03"):
        scr = json.loads((L / "analysis" / "screens" / tag / "screens.json").read_text(encoding="utf-8"))
        blocks = {b["id"]: b for t in scr["topics"] for h in t["thoughts"] for b in h["blocks"]}
        out = []
        for bd in scr["boards"]:
            states = []
            table = blocks.get(bd.get("table") or "") or {}
            doc = table.get("doc") or {}
            q = next((b for b in blocks.values() if b.get("question") and b["id"] in
                      [w for s in bd["states"] for w in s["working"]]), None)
            filling = False
            for s in bd["states"]:
                us = []
                for wid in s["working"]:
                    wb = blocks[wid]
                    if wb["type"] == "picture":
                        continue
                    if q and wid == q["id"]:
                        us.append(utt("{{c1}}Here is the question, with its three options.",
                                      [{"type": "reveal", "block": wid}]))
                    else:
                        us.append(utt("{{c1}}Here is a note on the board.", [{"type": "reveal", "block": wid}]))
                    if wb["type"] == "answer_row" and q:
                        # the wrong options ruled out, then the answer ticked: the question's parts
                        us.append(utt(" ".join("{{c%d}}This option goes." % (k + 1) if p["kind"] == "out"
                                               else "{{c%d}}This is the answer." % (k + 1)
                                               for k, p in enumerate(q["items"])),
                                      [{"type": "reveal", "block": f"{q['id']}.{p['part']}"} for p in q["items"]]))
                row = s.get("row")
                if filling and doc.get("text_type") == "form" and row is not None:
                    ty = next((t for t in table["typed"] if t["row"] == row), None)
                    if ty:
                        us.append(utt("The answer is this. {{c1}}It goes here.",
                                      [{"type": "type", "block": table["id"], "text": ty["text"]}]))
                if any("try it first" in (blocks[w].get("text") or "").lower() for w in s["working"]):
                    filling = True
                if not us:
                    us.append(utt("Look at the board."))
                states.append({"state": s["id"], "utterances": us})
            # the recording: played in the state after the listen note, as the test plays it
            view = None
            for st, s in zip(states, bd["states"]):
                view = s.get("view") or view
                texts = [(blocks[w].get("text") or "").lower() for w in s["working"]]
                if any("listen" in x and "again" not in x for x in texts):
                    stim = doc.get("stimulus")
                    st["utterances"].append(utt("Now listen to the recording.{{c1}}",
                                                [{"type": "play", "text": stim, "with": "exam"}]))
                if any("again" in x for x in texts):
                    # the part on screen (a section view), else the turns read
                    rows = view["rows"] if view and not view["map"] else [1, 3]
                    span = f"lines {rows[0] + 1}-{rows[-1] + 1}"
                    st["utterances"].append(utt("Listen again to this part.{{c1}}",
                                                [{"type": "play", "text": doc["stimulus"], "with": span}]))
                if any("try it first" in (blocks[w].get("text") or "").lower() for w in s["working"]):
                    st["utterances"].append(utt("Stop and choose now.{{c1}}",
                                                [{"type": "pause", "seconds": 4, "text": "try it first"}]))
            out.append({"board": bd["id"], "states": states})
        raw = {"content": [{"type": "text", "text": json.dumps({"boards": out, "unresolved": []})}]}
        (L / "analysis" / "narration" / tag / "raw_response.json").write_text(json.dumps(raw), encoding="utf-8")


def run(args: list[str]) -> str:
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print(f"$ {Path(args[0]).name} {' '.join(a for a in args[2:] if not a.startswith(str(Path('C:/'))))}: "
          f"exit {r.returncode}: " + " | ".join(tail))
    return r.stdout + r.stderr


def main() -> None:
    library = Path(sys.argv[1])
    L = build(library)
    for p in (101, 102, 103):
        run([str(HERE / "write_screens.py"), str(L), "--pages", str(p), "--render"])
    narrate(L)
    for p in (101, 102, 103):
        run([str(HERE / "write_narration.py"), str(L), "--pages", str(p), "--render"])
    run([str(HERE / "fit_boards.py"), str(L), "--silent", "--small-phone"])
    run([str(HERE / "build_lesson_player.py"), str(L), "--silent"])
    if "--checks" in sys.argv:
        d = str(L / "generated" / "lesson-preview" / "silent")
        for c in ("check_board_page.py", "check_overflow.py", "check_overlap.py", "check_lens.py", "check_wide_font.py",
                  "check_question_numbers.py", "check_layout.py"):
            run([str(HERE / c), str(L), "--dir", d])


if __name__ == "__main__":
    main()
