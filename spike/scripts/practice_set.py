"""A practice set in a Reading or Listening lesson (docs/adr/026-reading-lessons.md,
docs/adr/029-listening-lessons.md).

    .venv/Scripts/python spike/scripts/practice_set.py <lesson_dir> --set oa-set-ra-0001
    .venv/Scripts/python spike/scripts/practice_set.py <lesson_dir> --teach-pages 7,9
    .venv/Scripts/python spike/scripts/practice_set.py <lesson_dir> --check
    .venv/Scripts/python spike/scripts/practice_set.py <lesson_dir> --lesson-items oa-reading-000027,... --by NAME

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

A Listening set (ADR 029; bundle 1.18) is read from the release the owner
pinned for Listening (sample-tests-v2, 2026-10-13), never another:
  - an audio extract's TRANSCRIPT is a document too, one row per released line
    (a speaker's turn, or a further paragraph of a talk), its text type
    `transcript`;
  - a Part A gap-fill item is the NOTE FORM: a document of type `form`, a
    heading row for each of its headings and a numbered row for each gap, the
    gap's answer (its first accepted form) a typed part of the row, so the
    lesson fills the gap after "try it first" (ADR 009 gaps; no learner typing);
  - the extract's audio is copied into the lesson unchanged, its sha256 checked
    (`copy_exam_audio`), and a span of it is named by `exam_span`.
"""

import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

RELEASES_DIR = Path(os.environ.get("LOCALAPPDATA", r"C:\Users\siava\AppData\Local")) / \
    "oetacademy-exercises" / "releases"


def release_path(name: str) -> Path:
    """The local copy of an exercises release's package."""
    return RELEASES_DIR / name / f"oa-pkg-{name}" / "package.json"


RELEASE = release_path("pilot-v1")           # Reading (ADR 026)
# Listening (ADR 029; owner, 2026-10-13): the release pinned for every Listening
# lesson, and the sets of sample test 1 it holds. A set is imported only from it.
LISTENING_PIN = {"release": "sample-tests-v2", "package_id": "oa-pkg-sample-tests", "package_version": 2,
                 "sets": ("oa-set-la-0001", "oa-set-lb-0001", "oa-set-lc-0001")}
EXAM_AUDIO_DIR = "exam-audio"                # <lesson>/generated/exam-audio/ (bundle 1.18)
HASH_EXCLUDE = {"version", "content_hash", "status", "withdrawal", "tags", "admin"}


def _strip(obj):
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in HASH_EXCLUDE}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def _h_legacy(obj) -> str:
    """The content hash of the releases before RFC 8785 (pilot-v1): Python's
    sorted, compact JSON."""
    return "sha256:" + hashlib.sha256(json.dumps(_strip(obj), sort_keys=True, separators=(",", ":"),
                                                 ensure_ascii=False).encode("utf-8")).hexdigest()


def _jcs_number(x) -> str:
    """A number as ECMAScript writes it (RFC 8785 §3.2.2.3): an integral float
    such as 49.0 is 49; no exponent between 1e-6 and 1e21 (exercises repo,
    analysis/release.py `_jcs_number`)."""
    if isinstance(x, int):
        return str(x)
    if x == 0:
        return "0"
    sign, x = ("-", -x) if x < 0 else ("", x)
    m = re.fullmatch(r"(\d+)(?:\.(\d+))?(?:e([+-]\d+))?", repr(x))
    ip, fp, ex = m.group(1), m.group(2) or "", int(m.group(3) or 0)
    digits = (ip + fp).lstrip("0")
    point = len(ip) + ex - (len(ip + fp) - len((ip + fp).lstrip("0")))
    digits = digits.rstrip("0") or "0"
    k, n = len(digits), point
    if k <= n <= 21:
        out = digits + "0" * (n - k)
    elif 0 < n <= 21:
        out = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        out = "0." + "0" * (-n) + digits
    else:
        e = n - 1
        out = digits[0] + ("." + digits[1:] if k > 1 else "") + "e" + ("+" if e >= 0 else "-") + str(abs(e))
    return sign + out


def _jcs(obj) -> str:
    """RFC 8785 canonical JSON, as the exercises repository hashes it."""
    if obj is None:
        return "null"
    if obj is True:
        return "true"
    if obj is False:
        return "false"
    if isinstance(obj, (int, float)):
        return _jcs_number(obj)
    if isinstance(obj, str):
        return json.dumps(obj, ensure_ascii=False)
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(_jcs(v) for v in obj) + "]"
    return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + _jcs(obj[k])
                          for k in sorted(obj, key=lambda k: k.encode("utf-16-be"))) + "}"


def _h(obj) -> str:
    """The release's content hash (exercises repo, analysis/release.py `h`):
    RFC 8785 canonical JSON, bookkeeping fields left out."""
    return "sha256:" + hashlib.sha256(_jcs(_strip(obj)).encode("utf-8")).hexdigest()


def check_hashes(s: dict) -> list[str]:
    """Every text's and item's content hash, by the release's rule: RFC 8785
    (every release since it was adopted), else the earlier rule (pilot-v1)."""
    bad = []
    for p in s["parts"]:
        sh = {}
        for x in p["stimuli"]:
            sh[x["stimulus_id"]] = x["content_hash"]
            if x["content_hash"] not in (_h(x), _h_legacy(x)):
                bad.append(x["stimulus_id"])
        for i in p["items"]:
            obj = {"item": i, "stimuli": [sh[k] for k in i["stimulus_ids"]]}
            if i["content_hash"] not in (_h(obj), _h_legacy(obj)):
                bad.append(i["item_id"])
    return bad


def path(lesson: Path) -> Path:
    return Path(lesson) / "analysis" / "practice_set.json"


def load(lesson: Path) -> dict | None:
    p = path(lesson)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def release_for(lesson: Path) -> Path:
    """The release a lesson's set is imported from: the pinned Listening release
    for a Listening lesson (ADR 029), pilot-v1 for every other (ADR 026)."""
    import lesson_type
    return release_path(LISTENING_PIN["release"]) if lesson_type.of(lesson) == "listening" else RELEASE


def import_set(lesson: Path, set_id: str) -> dict:
    release = release_for(lesson)
    pkg = json.loads(release.read_text(encoding="utf-8"))
    listening = release == release_path(LISTENING_PIN["release"])
    if listening and ((pkg.get("package_id"), pkg.get("package_version"))
                      != (LISTENING_PIN["package_id"], LISTENING_PIN["package_version"])
                      or set_id not in LISTENING_PIN["sets"]):
        raise SystemExit(f"REFUSED: a Listening lesson imports only {', '.join(LISTENING_PIN['sets'])}, "
                         f"from {LISTENING_PIN['package_id']} version {LISTENING_PIN['package_version']} "
                         f"(ADR 029): asked for {set_id} from {pkg.get('package_id')} version "
                         f"{pkg.get('package_version')}")
    s = next((x for x in pkg["sets"] if x["set_id"] == set_id), None)
    if not s:
        raise SystemExit(f"{set_id} is not in the release {release}")
    bad = check_hashes(s)
    if bad:
        raise SystemExit(f"REFUSED: content hashes do not match the release for {bad}")
    out = {"format": "oetbook-practice-set", "adr": "029" if listening else "026",
           "release": {"package_id": pkg["package_id"], "package_version": pkg["package_version"],
                       "created_at": pkg["created_at"], "source": pkg["source"], "file": str(release)},
           "set_id": set_id, "title": s["title"], "release_status": s.get("release_status"),
           "sensitivity": pkg.get("sensitivity"), "parts": s["parts"],
           "note": "Copied from the release, hashes checked; shown exactly as released "
                   f"(ADR {'029' if listening else '026'}). Lesson data only: never in git."}
    path(lesson).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def stimuli(ps: dict) -> dict:
    return {x["stimulus_id"]: x for p in ps["parts"] for x in p["stimuli"]}


def items(ps: dict) -> dict:
    return {i["item_id"]: i for p in ps["parts"] for i in p["items"]}


def part_code(ps: dict, item: dict) -> str | None:
    """The part of the test an item belongs to: RA, RB or RC; LA, LB or LC."""
    return next((p.get("code") for p in ps["parts"]
                 if any(i["item_id"] == item["item_id"] for i in p["items"])), None)


def number(ps: dict, item: dict) -> int:
    """The number a question carries in this lesson. From Reading Part C (1)
    on, a lesson numbers the questions it teaches from 1 in the order taught
    (ADR 026 amendment of 2026-10-08; `numbering: lesson`, the items in
    `lesson_items`), never by the release's number; the item ID is unchanged.
    A lesson without it keeps the release's number (Reading 2 and 3)."""
    if ps.get("numbering") == "lesson" and item["item_id"] in ps["lesson_items"]:
        return ps["lesson_items"].index(item["item_id"]) + 1
    return release_number(item)         # not taught in this lesson: never shown


def release_number(item: dict) -> int:
    """An item's number in the release: a gap-fill item's first gap's (ADR 029)."""
    return item["number"] if "number" in item else item["numbers"][0]


def group_of(ps: dict, item: dict) -> dict | None:
    for p in ps["parts"]:
        for g in p.get("question_groups") or []:
            if g["first"] <= release_number(item) <= g["last"]:
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
    stem; a short-answer or completion item's prompt; a gap-fill item's title.
    Wording as released."""
    if item["type"] == "gapfill":
        return item["title"]
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
    return {"type": "plain", "text": question_text(ps, item), "exercise_item": number(ps, item),
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
        return (f"QUESTION {item['item_id']} (number {number(ps, item)}, "
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
    return (f"QUESTION {item['item_id']} (number {number(ps, item)}, {(item.get('admin') or {}).get('kind')}): "
            f"{question_text(ps, item)}\n  key: {k['answer']} (accepted: {' / '.join(k['accepted'])})"
            + (f"\n  evidence in the text: {item['evidence']}" if item.get("evidence") else "")
            + (f"\n  the release's reason for the key: {fb['key']}" if fb.get("key") else "")
            + "".join(f"\n  a wrong answer and why (release): {w}" for w in wrong))


# ---- Listening (ADR 029; bundle 1.18) ----

def is_audio(st: dict) -> bool:
    return st.get("type") == "audio-extract"


def is_gapfill(item: dict) -> bool:
    return item.get("type") == "gapfill"


def speakers_of(st: dict) -> list[str]:
    return [s["label"] for s in st.get("speakers") or [] if s.get("label")]


def transcript_lines(st: dict) -> list[str]:
    return [line for line in st["transcript"]["text"].split("\n") if line.strip()]


def transcript_parts(st: dict) -> list[dict]:
    """A transcript's rows in order, one per released line: a `turn` (a line
    that opens with a speaker's label; `speaker` that label) or a `para` (a
    further paragraph of the same speaker's talk). The row's text is the line
    exactly as released, the label included."""
    labels = sorted(speakers_of(st), key=len, reverse=True)
    out = []
    for line in transcript_lines(st):
        who = next((x for x in labels if line.startswith(x + ":")), None)
        out.append({"kind": "turn" if who else "para", "text": line, "mark": None,
                    **({"speaker": who} if who else {})})
    return out


def transcript_block(st: dict) -> dict:
    """An extract's transcript as a document (bundle 1.18, `text_type`
    "transcript"): a core table of one column, one row per released line."""
    ps = transcript_parts(st)
    if [p["text"] for p in ps] != transcript_lines(st):
        raise SystemExit(f"{st['stimulus_id']}: the rows are not the released transcript")
    return {"type": "table", "header": [st["label"]], "rows": [[p["text"]] for p in ps],
            "doc": {"stimulus": st["stimulus_id"], "label": st["label"], "title": "",
                    "text_type": "transcript",
                    "parts": [{"kind": p["kind"], "mark": None,
                               **({"speaker": p["speaker"]} if p.get("speaker") else {})} for p in ps]},
            "provenance": "source-derived",
            "note": f"transcript of {st['stimulus_id']} as released (ADR 029); built by code, "
                    "never written by the model"}


GAP = "____"


def gaps_of(item: dict) -> list[dict]:
    return sorted(item.get("gaps") or [], key=lambda g: g["number"])


def gap_key(g: dict) -> dict:
    acc = g["scoring"]["accepted"]
    return {"answer": acc[0], "accepted": acc}


def form_block(ps: dict, item: dict) -> dict:
    """A Part A gap-fill item as its NOTE FORM (bundle 1.18, `text_type` "form"):
    a document of one column, its header the item's title, a heading row for
    each heading (in gap order) and a numbered row for each gap (`mark` its
    exam number, ADR 029). The row is the gap's prompt with its first accepted
    form in place of the blank, and that form is a typed part, a gap (bundle
    1.6), filled by the lesson after "try it first"."""
    rows, parts, typed = [], [], []
    heading = None
    for g in gaps_of(item):
        if g.get("heading") and g["heading"] != heading:
            heading = g["heading"]
            rows.append([heading])
            parts.append({"kind": "heading", "mark": None})
        if g["prompt"].count(GAP) != 1:
            raise SystemExit(f"{g['gap_id']}: a gap's prompt has exactly one blank")
        ans = gap_key(g)["answer"]
        typed.append({"row": len(rows), "col": 0, "start": g["prompt"].index(GAP), "text": ans})
        rows.append([g["prompt"].replace(GAP, ans)])
        parts.append({"kind": "num", "mark": str(g["number"]), "gap": g["gap_id"]})
    return {"type": "table", "header": [item["title"]], "rows": rows, "typed": typed,
            "doc": {"stimulus": item["stimulus_ids"][0], "item": item["item_id"], "label": item["title"],
                    "title": "", "text_type": "form", "parts": parts},
            "provenance": "source-derived",
            "note": f"the note form of {item['item_id']} as released, each gap's first accepted form "
                    "typed by the lesson (ADR 029); built by code, never written by the model"}


def form_for_prompt(ps: dict, item: dict) -> str:
    """A Part A item for the screens stage: the form's rows as the board shows
    them, each gap with its number, its key and the release's own reasons."""
    b = form_block(ps, item)
    by_id = {g["gap_id"]: g for g in item["gaps"]}
    lines = []
    for n, (row, part) in enumerate(zip(b["rows"], b["doc"]["parts"]), 1):
        if part["kind"] == "heading":
            lines.append(f"  row {n}: [heading] {row[0]}")
            continue
        g = by_id[part["gap"]]
        k, fb = gap_key(g), g.get("feedback") or {}
        lines.append(f"  row {n}: [gap {g['number']}, {g['gap_id']}] {g['prompt']}\n"
                     f"     key: {k['answer']} (accepted: {' / '.join(k['accepted'])}; at most "
                     f"{(g.get('response') or {}).get('max_words')} words)"
                     + (f"\n     evidence in the transcript: {g['evidence']}" if g.get("evidence") else "")
                     + (f"\n     the release's reason for the key: {fb['key']}" if fb.get("key") else "")
                     + "".join(f"\n     a wrong answer and why (release): '{w['answer']}': {w['why_wrong']}"
                               for w in fb.get("wrong_answers") or []))
    return (f"NOTE FORM {item['item_id']} (gaps {item['numbers'][0]}-{item['numbers'][-1]}; its extract "
            f"{item['stimulus_ids'][0]}), its rows as the board shows them:\n" + "\n".join(lines))


def extract_audio(st: dict) -> dict:
    return st["audio"]


def segment(st: dict, kind: str) -> dict | None:
    return next((s for s in extract_audio(st).get("segments") or [] if s["kind"] == kind), None)


def row_times(ps: dict, stimulus_id: str) -> list[float | None]:
    """Each transcript row's start in the extract file, from the word times
    (word_times.py, ADR 030: speech-to-text times lined up with the release's own
    words); every row None where there are none. The release's admin turn times
    are not used (owner, 2026-10-13)."""
    import word_times
    st = stimuli(ps)[stimulus_id]
    return word_times.row_times(st) or [None] * len(transcript_parts(st))


def section_rows(st: dict) -> list[dict]:
    """An extract's sections (word_times.sections_for, ADR 030), each with the
    rows it runs over (from 0): a question's (Parts B, C) or a heading's (Part A)."""
    import word_times
    firsts = word_times.row_first_words(st)
    row_of = lambda w: max(n for n, f in enumerate(firsts) if f <= w)
    return [{**s, "rows": [row_of(s["from"]), row_of(s["to"])]} for s in word_times.sections_for(st)]


def transcript_for_prompt(ps: dict, st: dict) -> str:
    """An extract for the screens stage: its rows as the board shows them, and
    the part of the recording each question (or each heading of a note form)
    is answered from."""
    parts = transcript_parts(st)
    rows = "\n".join(f"  row {n}: " + p["text"] for n, p in enumerate(parts, 1))
    its = items(ps)
    secs = []
    for s in section_rows(st):
        who = (f"question {number(ps, its[s['item']])}" if s.get("item") in its
               else f"heading {s['heading']} (gaps from {s['first_gap']})" if s.get("heading") else "")
        secs.append(f"  {who}: rows {s['rows'][0] + 1}-{s['rows'][1] + 1}")
    return (f"TRANSCRIPT {st['stimulus_id']} ({st['label']}; {len(parts)} rows; reading time "
            f"{st.get('reading_time_s')} s), its rows as the board shows them:\n{rows}"
            + ("\n  Its sections (where each is answered; a replay of one is \"question N\" or "
               "\"heading K\"):\n" + "\n".join(secs) if secs else ""))


SPAN = re.compile(r"lines?\s+(\d+)(?:\s*[-–]\s*(\d+))?")
SECTION_SPAN = re.compile(r"(question|heading)\s+(\d+)")


def exam_span(ps: dict, stimulus_id: str, span: str) -> dict:
    """A span of an extract's audio file (bundle 1.18, a `play` cue's `with`):
    "exam" plays it as the test does, from the announcement through the reading
    time and the tone to the extract's end; "extract" from its first word to its
    end; "lines N-M" (or "line N") the transcript's rows N to M, from row N's
    start to the next timed row's start (or the extract's end), for a replay;
    "question N" (the exam's number) or "heading K" (a note form's K-th
    heading) a section (ADR 030), from its first word to the next section's.
    Row and section times are the word times' (word_times.py, ADR 030).
    The audio is never changed: a span is two times in the file."""
    st = stimuli(ps)[stimulus_id]
    ext = segment(st, "extract")
    if not ext:
        raise ValueError(f"{stimulus_id}: the release gives no extract segment")
    rows = None
    s = " ".join((span or "").strip().lower().split())
    m2 = SECTION_SPAN.fullmatch(s)
    if s == "exam":
        a, z = (segment(st, "announcement") or ext)["start_s"], ext["end_s"]
    elif s == "extract":
        a, z = ext["start_s"], ext["end_s"]
    elif m2:
        k = int(m2.group(2))
        its = items(ps)
        secs = section_rows(st)
        sec = next((x for x in secs if (m2.group(1) == "question" and x.get("item") in its
                                        and number(ps, its[x["item"]]) == k)
                    or (m2.group(1) == "heading" and x.get("heading") == k)), None)
        if not sec:
            raise ValueError(f"span {span!r}: {stimulus_id} has no such section")
        import word_times
        wt = word_times.for_stimulus(st)["times"]
        a = max(ext["start_s"], wt[sec["from"]][0] - word_times.ROW_PAD_S)
        after = [x for x in secs if x["from"] > sec["from"]]
        z = (max(ext["start_s"], wt[after[0]["from"]][0] - word_times.ROW_PAD_S) if after else ext["end_s"])
        rows = sec["rows"]
    else:
        m = SPAN.fullmatch(s)
        if not m:
            raise ValueError(f"span {span!r}: write 'exam', 'extract', 'lines N-M', 'question N' or 'heading K'")
        n1, n2 = int(m.group(1)), int(m.group(2) or m.group(1))
        times = row_times(ps, stimulus_id)
        if not 1 <= n1 <= n2 <= len(times):
            raise ValueError(f"span {span!r}: the transcript has rows 1-{len(times)}")
        if times[n1 - 1] is None:
            raise ValueError(f"span {span!r}: row {n1} has no time in the release")
        a = times[n1 - 1]
        z = next((x for x in times[n2:] if x is not None), ext["end_s"])
        rows = [n1 - 1, n2 - 1]
    a_ = extract_audio(st)
    return {"stimulus": stimulus_id, "label": st["label"], "span": s, "rows": rows,
            "clip_in": round(a, 3), "clip_out": round(z, 3),
            "file": Path(a_["path"]).name, "sha256": a_["sha256"], "duration_s": a_.get("duration_s")}


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_exam_audio(lesson: Path, stimulus_id: str) -> Path:
    """Copy an extract's audio file into the lesson (generated/exam-audio/),
    byte for byte, its sha256 checked against the release's before and after.
    The engine never re-encodes, trims or changes the level of release audio
    (ADR 029): a span is played by its two times in the file."""
    ps = load(lesson)
    a = extract_audio(stimuli(ps)[stimulus_id])
    src = Path(ps["release"]["file"]).parent / a["path"]
    dest = Path(lesson) / "generated" / EXAM_AUDIO_DIR / Path(a["path"]).name
    if dest.exists() and _sha256(dest) == a["sha256"]:
        return dest
    if not src.exists() or _sha256(src) != a["sha256"]:
        raise SystemExit(f"REFUSED: {src} is missing or does not match the release's sha256 for {stimulus_id}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    if _sha256(dest) != a["sha256"]:
        raise SystemExit(f"REFUSED: the copy of {src} does not match its sha256")
    return dest


def check_listening(ps: dict) -> list[str]:
    """A Listening set's own checks: every transcript's rows are its released
    lines, every word has a time (word_times.py, ADR 030; never the release's
    admin turn times) and the extract its sections, and every gap's prompt has
    one blank."""
    import word_times
    bad = []
    for st in stimuli(ps).values():
        if not is_audio(st):
            continue
        rows = transcript_parts(st)
        if [p["text"] for p in rows] != transcript_lines(st):
            bad.append(st["stimulus_id"] + " (transcript rows)")
        if not word_times.for_stimulus(st):
            bad.append(st["stimulus_id"] + " (no word times for this transcript and audio)")
        elif not word_times.sections_for(st):
            bad.append(st["stimulus_id"] + " (no sections)")
        if not segment(st, "extract"):
            bad.append(st["stimulus_id"] + " (no extract segment)")
    for it in items(ps).values():
        if is_gapfill(it) and any(g["prompt"].count(GAP) != 1 for g in it.get("gaps") or []):
            bad.append(it["item_id"] + " (gap prompts)")
    return bad


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
    if "--lesson-items" in sys.argv:
        # the questions this lesson teaches, in the order taught: numbered
        # from 1 (ADR 026 amendment of 2026-10-08)
        ids = [x.strip() for x in sys.argv[sys.argv.index("--lesson-items") + 1].split(",") if x.strip()]
        unknown = [i for i in ids if i not in items(ps)]
        if unknown or len(set(ids)) != len(ids):
            raise SystemExit(f"--lesson-items: unknown or repeated items {unknown or ids}")
        by = sys.argv[sys.argv.index("--by") + 1] if "--by" in sys.argv else "maintainer"
        import datetime
        ps.update(numbering="lesson", lesson_items=ids, numbering_by=f"{by} {datetime.date.today()}")
        path(lesson).write_text(json.dumps(ps, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"questions numbered in this lesson: 1-{len(ids)} ({ids[0]} to {ids[-1]})")
    bad = check_hashes({"parts": ps["parts"]})
    for st in stimuli(ps).values():
        if not is_audio(st) and not verbatim(st["body"], parts(st["body"])):
            bad.append(st["stimulus_id"] + " (parts)")
    bad += check_listening(ps)
    if bad:
        raise SystemExit(f"practice set check failed: {bad}")
    print(f"{ps['set_id']}: hashes and document parts verified")


if __name__ == "__main__":
    main()
