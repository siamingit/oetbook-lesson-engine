"""A practice set in a Reading lesson (docs/adr/026-reading-lessons.md).

    .venv/Scripts/python spike/scripts/practice_set.py <lesson_dir> --set oa-set-ra-0001
    .venv/Scripts/python spike/scripts/practice_set.py <lesson_dir> --teach-pages 7,9
    .venv/Scripts/python spike/scripts/practice_set.py <lesson_dir> --check

The texts and questions of Reading Parts A, B and C come only from the
exercises repository's release (pilot-v1), shown exactly as released. This
script copies one set from the local copy of the release into the lesson,
`analysis/practice_set.json`, after checking every text's and item's
`content_hash` against the release's own rule (canonical JSON, bookkeeping
fields left out, an item's hash covering its texts' hashes). Lesson folders
are not in git, and neither is this file: the exercises repository is private.

It also gives the screens stage what it builds from a set, by ID:
  - a text as a DOCUMENT: a core table of one column, its header the text's
    label and title, one row per part (a heading, a paragraph, a list item, a
    row of a table in the text), and a `doc` field naming the text type and
    each row's kind, so the renderer draws a realistic page (bundle 1.13);
  - an item as a QUESTION: its number and its question as the learner reads
    it (a matching item's lead-in and stem), with the item ID.
Nothing is reworded: a part is a line of the released body with only its list
marker taken off ("- ", "1. "), which the page draws; `verbatim()` proves it.
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

RELEASE = Path(os.environ.get("LOCALAPPDATA", r"C:\Users\siava\AppData\Local")) / \
    "oetacademy-exercises" / "releases" / "pilot-v1" / "oa-pkg-pilot-v1" / "package.json"
HASH_EXCLUDE = {"version", "content_hash", "status", "withdrawal", "tags", "admin"}


def _strip(obj):
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in HASH_EXCLUDE}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def _h(obj) -> str:
    """The release's content hash (exercises repo, analysis/release.py `h`)."""
    return "sha256:" + hashlib.sha256(json.dumps(_strip(obj), sort_keys=True, separators=(",", ":"),
                                                 ensure_ascii=False).encode("utf-8")).hexdigest()


def check_hashes(s: dict) -> list[str]:
    bad = []
    for p in s["parts"]:
        sh = {}
        for x in p["stimuli"]:
            sh[x["stimulus_id"]] = _h(x)
            if sh[x["stimulus_id"]] != x["content_hash"]:
                bad.append(x["stimulus_id"])
        for i in p["items"]:
            if _h({"item": i, "stimuli": [sh[k] for k in i["stimulus_ids"]]}) != i["content_hash"]:
                bad.append(i["item_id"])
    return bad


def path(lesson: Path) -> Path:
    return Path(lesson) / "analysis" / "practice_set.json"


def load(lesson: Path) -> dict | None:
    p = path(lesson)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def import_set(lesson: Path, set_id: str) -> dict:
    pkg = json.loads(RELEASE.read_text(encoding="utf-8"))
    s = next((x for x in pkg["sets"] if x["set_id"] == set_id), None)
    if not s:
        raise SystemExit(f"{set_id} is not in the release {RELEASE}")
    bad = check_hashes(s)
    if bad:
        raise SystemExit(f"REFUSED: content hashes do not match the release for {bad}")
    out = {"format": "oetbook-practice-set", "adr": "026",
           "release": {"package_id": pkg["package_id"], "package_version": pkg["package_version"],
                       "created_at": pkg["created_at"], "source": pkg["source"], "file": str(RELEASE)},
           "set_id": set_id, "title": s["title"], "release_status": s.get("release_status"),
           "sensitivity": pkg.get("sensitivity"), "parts": s["parts"],
           "note": "Copied from the release, hashes checked; shown exactly as released (ADR 026). "
                   "Lesson data only: never in git."}
    path(lesson).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def stimuli(ps: dict) -> dict:
    return {x["stimulus_id"]: x for p in ps["parts"] for x in p["stimuli"]}


def items(ps: dict) -> dict:
    return {i["item_id"]: i for p in ps["parts"] for i in p["items"]}


def part_code(ps: dict, item: dict) -> str | None:
    """The part of the test an item belongs to: RA, RB or RC."""
    return next((p.get("code") for p in ps["parts"]
                 if any(i["item_id"] == item["item_id"] for i in p["items"])), None)


def group_of(ps: dict, item: dict) -> dict | None:
    for p in ps["parts"]:
        for g in p.get("question_groups") or []:
            if g["first"] <= item["number"] <= g["last"]:
                return g
    return None


# ---- a text as a document ----

LIST_MARK = re.compile(r"^(?:- |(\d+)\. )")


def parts(body: str) -> list[dict]:
    """The text's parts in order: {kind, text, mark}. kind is heading, para,
    bullet, num (mark its number), thead or trow (a row of a table in the
    text, its cells joined by " | " as released). A heading is a paragraph's
    first line when more lines follow and it ends with no stop."""
    out = []
    for block in re.split(r"\n\s*\n", body.strip()):
        lines = [l for l in block.split("\n") if l.strip()]
        table_rows = [l for l in lines if " | " in l]
        for n, line in enumerate(lines):
            m = LIST_MARK.match(line)
            if " | " in line:
                out.append({"kind": "thead" if line == table_rows[0] else "trow", "text": line, "mark": None})
            elif m:
                out.append({"kind": "num" if m.group(1) else "bullet", "text": line[m.end():],
                            "mark": m.group(1)})
            elif n == 0 and len(lines) > 1 and not re.search(r"[.?!:]$", line.strip()):
                out.append({"kind": "heading", "text": line, "mark": None})
            else:
                out.append({"kind": "para", "text": line, "mark": None})
    return out


def verbatim(body: str, ps: list[dict]) -> bool:
    """The parts, markers put back, are the body's lines exactly."""
    lines = [l for l in body.split("\n") if l.strip()]
    back = [("- " if p["kind"] == "bullet" else f"{p['mark']}. " if p["kind"] == "num" else "") + p["text"]
            for p in ps]
    return lines == back


def doc_header(st: dict) -> str:
    return st["label"] + (": " + st["title"] if st.get("title") else "")


# Words printed in bold in a released body (the release's oa-text-v1 format:
# Reading Part C in-context targets, as the real test prints them)
BOLD = re.compile(r"\*\*(.+?)\*\*")


def unbold(text: str) -> tuple[str, list[str]]:
    """A released line with its bold markers taken off, and the phrases they
    marked, in order (bundle 1.17: a doc part's `bold`)."""
    return BOLD.sub(lambda m: m.group(1), text), BOLD.findall(text)


def doc_part(p: dict) -> dict:
    """A row's kind and marker; a row with bold words also names them (1.17).
    A text with none is exactly as before, so no earlier bundle changes."""
    out = {"kind": p["kind"], "mark": p["mark"]}
    bold = unbold(p["text"])[1]
    if bold:
        out["bold"] = bold
    return out


def document_block(st: dict) -> dict:
    """The text as a core table of one column (bundle 1.13 `doc`). A word the
    release prints in bold keeps its words in the row, the markers off, and is
    named in its part's `bold` (bundle 1.17)."""
    ps = parts(st["body"])
    if not verbatim(st["body"], ps):
        raise SystemExit(f"{st['stimulus_id']}: the parts are not the released text")
    return {"type": "table", "header": [doc_header(st)], "rows": [[unbold(p["text"])[0]] for p in ps],
            "doc": {"stimulus": st["stimulus_id"], "label": st["label"], "title": st.get("title") or "",
                    "text_type": st.get("text_type") or "text",
                    "parts": [doc_part(p) for p in ps]},
            "provenance": "source-derived",
            "note": f"practice set {st['stimulus_id']} as released (ADR 026); built by code, never written by the model"}


def document_for_prompt(st: dict) -> str:
    rows = "\n".join(f"  row {n}: [{p['kind']}] " + (f"{p['mark']}. " if p["mark"] else "") + unbold(p["text"])[0]
                     + "".join(f" [printed in bold: '{w}']" for w in unbold(p["text"])[1])
                     for n, p in enumerate(parts(st["body"]), 1))
    return (f"DOCUMENT {st['stimulus_id']} ({doc_header(st)}; a {st.get('text_type') or 'text'}), "
            f"its rows as the board shows them:\n{rows}")


# ---- an item as a question ----

def question_text(ps: dict, item: dict) -> str:
    """The question as the learner reads it: a matching item's lead-in and
    stem; a short-answer or completion item's prompt. Wording as released."""
    if item["type"] == "choice":
        g = group_of(ps, item) or {}
        lead = g.get("lead_in")
        return (lead + " " + item["stem"]) if lead else item["stem"]
    return item["prompt"]


def answer_key(item: dict) -> dict:
    """The key as released: the text letter of a matching item; the first
    accepted answer, and all accepted forms, of a typed one."""
    if item["type"] == "choice":
        k = item["scoring"]["key_option_id"]
        opt = next(o for o in item["options"] if o["option_id"] == k)
        return {"answer": opt["text"], "accepted": [opt["text"]], "stimulus": opt.get("stimulus_id")}
    acc = item["scoring"]["accepted"]
    return {"answer": acc[0], "accepted": acc, "stimulus": None}


def is_options_item(item: dict) -> bool:
    """A Part B or C question: a choice item whose options are answers (A, B,
    C...), not the texts of a Part A matching item."""
    return item["type"] == "choice" and bool(item.get("options")) and \
        not any(o.get("stimulus_id") for o in item["options"])


def options_of(item: dict) -> list[dict]:
    """The options in the order the release displays them, lettered A, B, C."""
    by_id = {o["option_id"]: o for o in item["options"]}
    order = item.get("display_order") or [o["option_id"] for o in item["options"]]
    return [{"option": oid, "letter": chr(65 + n), "text": by_id[oid]["text"]}
            for n, oid in enumerate(order)]


def question_block(ps: dict, item: dict) -> dict:
    q = {"item": item["item_id"], "kind": (item.get("admin") or {}).get("kind") or item["type"],
         "max_words": (item.get("response") or {}).get("max_words")}
    if is_options_item(item):
        # bundle 1.15 (ADR 026, Part B): the options as released, lettered
        q["options"] = options_of(item)
    if part_code(ps, item) == "RC":
        # bundle 1.17 (ADR 026, the Part C question method): the options are a
        # part revealed once the paragraph is read (QTA), and an in-context
        # target is printed in bold in the stem, as the real test prints it
        q["options_later"] = True
        if (item.get("target") or {}).get("text"):
            q["target"] = item["target"]["text"]
    return {"type": "plain", "text": question_text(ps, item), "exercise_item": item["number"],
            "question": q,
            "provenance": "source-derived",
            "note": f"practice set item {item['item_id']} as released (ADR 026); built by code"}


def question_for_prompt(ps: dict, item: dict) -> str:
    k = answer_key(item)
    fb = item.get("feedback") or {}
    if is_options_item(item):
        # a Part B question: the options by letter, the key's letter, and the
        # release's own reason for each wrong option (for the reason labels)
        opts = options_of(item)
        letter = {o["option"]: o["letter"] for o in opts}
        key = item["scoring"]["key_option_id"]
        return (f"QUESTION {item['item_id']} (number {item['number']}, "
                f"{(item.get('admin') or {}).get('question_type') or 'choice'}; its text is "
                f"{', '.join(item['stimulus_ids'])}): {question_text(ps, item)}"
                + "".join(f"\n  option {o['letter']}: {o['text']}" for o in opts)
                + f"\n  key: option {letter[key]}"
                + (f"\n  the answer's paragraph: {item['evidence_paragraph']}; question type: "
                   f"{(item.get('admin') or {}).get('question_type')}"
                   if part_code(ps, item) == "RC" and item.get("evidence_paragraph") else "")
                + (f"\n  evidence in the text: {item['evidence']}" if item.get("evidence") else "")
                + (f"\n  the release's reason for the key: {fb['key']}" if fb.get("key") else "")
                + "".join(f"\n  option {letter[oid]} is wrong (release): {w['why_wrong']}"
                          for oid, w in (fb.get("options") or {}).items() if oid in letter))
    wrong = []
    for oid, w in (fb.get("options") or {}).items():
        opt = next((o["text"] for o in item.get("options") or [] if o["option_id"] == oid), oid)
        wrong.append(f"{opt}: {w['why_wrong']}")
    for w in fb.get("wrong_answers") or []:
        wrong.append(f"'{w['answer']}': {w['why_wrong']}")
    return (f"QUESTION {item['item_id']} (number {item['number']}, {(item.get('admin') or {}).get('kind')}): "
            f"{question_text(ps, item)}\n  key: {k['answer']} (accepted: {' / '.join(k['accepted'])})"
            + (f"\n  evidence in the text: {item['evidence']}" if item.get("evidence") else "")
            + (f"\n  the release's reason for the key: {fb['key']}" if fb.get("key") else "")
            + "".join(f"\n  a wrong answer and why (release): {w}" for w in wrong))


def main() -> None:
    lesson = Path(sys.argv[1])
    if "--set" in sys.argv:
        ps = import_set(lesson, sys.argv[sys.argv.index("--set") + 1])
        n_st, n_it = len(stimuli(ps)), len(items(ps))
        print(f"wrote {path(lesson)}: {ps['set_id']}, {n_st} texts, {n_it} items, hashes match the release")
    ps = load(lesson)
    if not ps:
        raise SystemExit("no practice set in this lesson")
    if "--teach-pages" in sys.argv:
        ps["teach_pages"] = sorted(int(x) for x in sys.argv[sys.argv.index("--teach-pages") + 1].split(","))
        path(lesson).write_text(json.dumps(ps, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"sections teaching the set: pages {ps['teach_pages']}")
    bad = check_hashes({"parts": ps["parts"]})
    for st in stimuli(ps).values():
        if not verbatim(st["body"], parts(st["body"])):
            bad.append(st["stimulus_id"] + " (parts)")
    if bad:
        raise SystemExit(f"practice set check failed: {bad}")
    print(f"{ps['set_id']}: hashes and document parts verified")


if __name__ == "__main__":
    main()
