"""The course index: what every lesson teaches, and where (docs/05-COURSE-INDEX.md).

    .venv/Scripts/python spike/scripts/build_course_index.py <lesson_dir or lessons_dir>
        [--inventory CSV]

Rebuilds <library>/course/course-index.json and course-index.md, whole, from
every lesson folder in <library>/lessons/. <library> is the folder that holds
the lessons folder (C:\\OET for C:\\OET\\lessons\\grammar-02-verb-use). The
index stays OUTSIDE the repository: it holds the product's full teaching
content, and the repository is public (docs/adr/006).

By code only, from files on disk (AGENTS.md §8): the bundle and text.json of
a built lesson, its sections.json, its understanding, its gates, and its
source folder. Nothing is reworded; every field says where it came from.
The same inputs give a byte-identical file.

The library inventory (library_inventory.py --out <library>/course/
library_inventory.csv, or --inventory) adds every recording of the library by
title, matched to its lesson folder by the inventory's partial hash.

catalogue() is the index as the model stages see it: the other lessons, their
sections and objectives, so that a reference can be resolved to ids
(extract_understanding.py) and checked (write_narration.py).
"""

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths                                                      # noqa: E402

FORMAT_VERSION = "1.0"
TYPES = ("grammar", "reading", "listening", "writing", "speaking", "vocabulary")


def library_of(path: Path) -> Path:
    """<library> for a lesson folder or the lessons folder itself."""
    path = path.resolve()
    if (path / "source").is_dir() or (path / "analysis").is_dir() or (path / "sources").is_dir():
        return path.parent.parent
    return path.parent


def course_dir(lesson_or_lessons: Path) -> Path:
    return library_of(lesson_or_lessons) / "course"


def index_path(lesson_or_lessons: Path) -> Path:
    return course_dir(lesson_or_lessons) / "course-index.json"


def load(lesson_or_lessons: Path) -> dict | None:
    p = index_path(lesson_or_lessons)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def short_title(title: str | None) -> str | None:
    return title.rsplit(":", 1)[-1].strip() if title else None


def read(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def partial_hash(p: Path) -> str:
    from library_inventory import partial_hash as ph
    return ph(p, p.stat().st_size)


def duration(p: Path) -> float | None:
    import subprocess
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                        "default=nw=1:nk=1", str(p)], capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 1)
    except ValueError:
        return None


def source_of(L: Path) -> dict:
    src = L / "source" if (L / "source").is_dir() else L / "sources"
    video, deck = src / "video.mp4", src / "slides.pdf"
    out = {"recording": None, "duration_s": None, "partial_hash": None,
           "deck": None, "deck_pages": None}
    if video.exists():
        out.update(recording=str(video.relative_to(L)).replace("\\", "/"),
                   duration_s=duration(video), partial_hash=partial_hash(video))
    if deck.exists():
        import pypdfium2 as pdfium
        out.update(deck=str(deck.relative_to(L)).replace("\\", "/"),
                   deck_pages=len(pdfium.PdfDocument(str(deck))))
    return out


def understanding(L: Path, pages: list[int]) -> tuple[list, list, list]:
    """Objectives, teaching points and recording spans of a section's pages."""
    objectives, points, spans = [], [], []
    for p in pages:
        f = paths.understanding_dir(L, p) / "understanding.json"
        if not f.exists():
            continue
        u = read(f)
        times = [(b["start"], b["end"]) for b in u.get("beats") or []] + \
                [(n["start"], n["end"]) for n in u.get("non_teaching") or []]
        if times:
            spans.append({"page": p, "from_s": round(min(t[0] for t in times), 1),
                          "to_s": round(max(t[1] for t in times), 1)})
        for b in u.get("beats") or []:
            objectives.append(b["learning_objective"])
            points.append(b["teaching_point"])
    return objectives, points, spans


def built_lesson(L: Path, info: dict, entry: dict) -> None:
    d = L / "generated" / "lesson-player"
    bundle, text = read(d / "bundle.json"), read(d / "text.json")
    entry["bundle"] = {"path": "generated/lesson-player/bundle.json",
                       "format_version": bundle["format_version"],
                       "duration_s": bundle["meta"]["total_duration_s"]}
    entry["categories"] = bundle["lesson"]["categories"]
    texts = {s["id"]: s for s in text["sections"]}
    blocks = bundle["blocks"]
    boards = {b["id"]: b for b in bundle["boards"]}
    for sec in bundle["sections"]:
        ids: list[str] = []
        refs = []
        for bid in sec["boards"]:
            bd = boards[bid]
            for i in list(bd["fixed"]) + [i for s in bd["states"] for i in s["working"]]:
                if i not in ids:
                    ids.append(i)
            for s in bd["states"]:
                for u in s["utterances"]:
                    for r in u.get("refs") or []:
                        refs.append({"utterance": u["id"], "lesson": r["lesson"],
                                     "section": r.get("section"),
                                     "provenance": u["provenance"], "text": u["text"]})
        bl = [blocks[i] for i in ids]
        objectives, points, spans = understanding(L, sec["pages"])
        entry["sections"].append({
            "id": sec["id"], "title": sec["title"], "category": sec["category"],
            "intro": sec["intro"], "pages": sec["pages"],
            "start": sec["start"], "end": sec["end"],
            "recording": spans, "objectives": objectives, "teaching_points": points,
            "rules": [{"block": b["id"], "kind": b["kind"], "text": b["text"]}
                      for b in bl if b["type"] == "callout"],
            "key_terms": [{"block": b["id"], "label": b["label"], "term": b["term"],
                           "explanation": b["explanation"]}
                          for b in bl if b["type"] == "term_box" and b.get("label") != "WORD"],
            "glossed_words": [{"block": b["id"], "word": b["term"], "gloss": b["explanation"]}
                              for b in bl if b["type"] == "term_box" and b.get("label") == "WORD"],
            "refs": refs, "referenced_by": [],
            "narration_text": texts[sec["id"]]["narration_text"],
            "board_text": texts[sec["id"]]["board_text"]})


def lesson_entry(L: Path) -> dict:
    sp = L / "analysis" / "sections.json"
    info = read(sp) if sp.exists() else {}
    title = (info.get("lesson") or {}).get("title")
    first = L.name.split("-")[0]
    gp = L / "analysis" / "gates.json"
    final = read(gp).get("final") if gp.exists() else None
    entry = {"id": L.name, "title": title, "short_title": short_title(title),
             "description": (info.get("lesson") or {}).get("description"),
             "type": first if first in TYPES else None,
             "status": "not built", "final_gate": final, "source": source_of(L),
             "bundle": None, "categories": [], "sections": [], "referenced_by": []}
    if (L / "generated" / "lesson-player" / "bundle.json").exists():
        entry["status"] = "built"
        built_lesson(L, info, entry)
    return entry


def inventory(csv_path: Path | None, lessons: list[dict]) -> list[dict]:
    if not csv_path or not csv_path.exists():
        return []
    by_hash = {e["source"]["partial_hash"]: e["id"] for e in lessons if e["source"]["partial_hash"]}
    out = []
    with csv_path.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if not row.get("file") or row.get("duplicate_kind") == "same file":
                continue
            out.append({"title": Path(row["file"]).stem, "path": row["path"],
                        "duration_s": float(row["duration_s"]) if row.get("duration_s") else None,
                        "partial_hash": row.get("partial_hash") or None,
                        "lesson": by_hash.get(row.get("partial_hash"))})
    return sorted(out, key=lambda r: r["path"])


def build(target: Path, inventory_csv: Path | None = None) -> Path:
    lib = library_of(target)
    lessons_dir = lib / "lessons"
    folders = sorted(p for p in lessons_dir.iterdir() if p.is_dir())
    lessons = [lesson_entry(L) for L in folders]

    by_id = {e["id"]: e for e in lessons}
    refs_out = []
    for e in lessons:
        for s in e["sections"]:
            for r in s["refs"]:
                tgt = by_id.get(r["lesson"])
                if not tgt:
                    raise SystemExit(f"REFUSED: {e['id']} {r['utterance']} refers to lesson "
                                     f"{r['lesson']!r}, which is not in {lessons_dir}")
                src = {"lesson": e["id"], "section": s["id"], "utterance": r["utterance"]}
                if r["section"]:
                    ts = next((x for x in tgt["sections"] if x["id"] == r["section"]), None)
                    if not ts:
                        raise SystemExit(f"REFUSED: {e['id']} {r['utterance']} refers to section "
                                         f"{r['section']!r} of {r['lesson']}, which it does not have")
                    if src not in ts["referenced_by"]:
                        ts["referenced_by"].append(src)
                elif src not in tgt["referenced_by"]:
                    tgt["referenced_by"].append(src)
                refs_out.append({"from": src, "to": {"lesson": r["lesson"], "section": r["section"]},
                                 "provenance": r["provenance"], "text": r["text"]})
    for e in lessons:
        for s in e["sections"]:
            for r in s["refs"]:
                r.pop("text", None)

    out_dir = lib / "course"
    out_dir.mkdir(parents=True, exist_ok=True)
    inv = inventory_csv or out_dir / "library_inventory.csv"
    index = {"format": "oetbook-course-index", "format_version": FORMAT_VERSION,
             "lessons": lessons, "references": refs_out, "library": inventory(inv, lessons)}
    jp = out_dir / "course-index.json"
    jp.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out_dir / "course-index.md").write_text(markdown(index), encoding="utf-8")
    built = [e for e in lessons if e["status"] == "built"]
    print(f"course index: {len(lessons)} lessons ({len(built)} built), "
          f"{sum(len(e['sections']) for e in built)} sections, {len(refs_out)} references, "
          f"{len(index['library'])} library recordings")
    print(f"wrote {jp} and course-index.md")
    return jp


# ---------------------------------------------------------------------------
# The human-readable version, generated from the JSON
# ---------------------------------------------------------------------------

def hms(t: float | None) -> str:
    if t is None:
        return "?"
    t = int(round(t))
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


def markdown(ix: dict) -> str:
    titles = {e["id"]: e["title"] or e["id"] for e in ix["lessons"]}
    sec_titles = {(e["id"], s["id"]): s["title"] for e in ix["lessons"] for s in e["sections"]}

    def where(r: dict) -> str:
        t = titles.get(r["lesson"], r["lesson"])
        s = sec_titles.get((r["lesson"], r.get("section")))
        return f"{t}" + (f", section \"{s}\" (`{r['section']}`)" if s else " (the whole lesson)")

    out = ["# Course index", "",
           "Generated from course-index.json by build_course_index.py; never edit by hand "
           "(format: docs/05-COURSE-INDEX.md in the lesson engine repository).", "",
           "| Lesson | Type | Status | Sections | Length | Original recording |",
           "|---|---|---|---|---|---|"]
    for e in ix["lessons"]:
        out.append(f"| {e['title'] or '(title not read yet)'} (`{e['id']}`) | {e['type'] or '?'} | "
                   f"{e['status']}{', final gate approved' if e['final_gate'] else ''} | "
                   f"{len(e['sections']) or ''} | "
                   f"{hms(e['bundle']['duration_s']) if e['bundle'] else ''} | "
                   f"{e['source']['recording'] or '?'}, {hms(e['source']['duration_s'])} |")
    for e in ix["lessons"]:
        out += ["", "---", "", f"## {e['title'] or e['id']}", "",
                f"- Id: `{e['id']}`; type: {e['type'] or 'UNKNOWN'}; status: {e['status']}"
                + (f"; final gate approved by {e['final_gate']['by']}, {e['final_gate']['on']}"
                   if e["final_gate"] else "; final gate not approved"),
                f"- Original recording: `{e['source']['recording']}`, "
                f"{hms(e['source']['duration_s'])}; deck `{e['source']['deck']}`, "
                f"{e['source']['deck_pages']} pages"]
        if e["description"]:
            out.append(f"- Description: {e['description']}")
        if e["categories"]:
            out.append("- Categories: " + "; ".join(c["title"] for c in e["categories"]))
        for r in e["referenced_by"]:
            out.append(f"- Referred to by {titles.get(r['lesson'])}, `{r['utterance']}`")
        for s in e["sections"]:
            out += ["", f"### {s['title']} (`{s['id']}`)", "",
                    f"Lesson time {hms(s['start'])} to {hms(s['end'])}; original recording "
                    + ", ".join(f"page {x['page']} {hms(x['from_s'])} to {hms(x['to_s'])}"
                                for x in s["recording"]) + "."]
            if s["objectives"]:
                out += ["", "**Objectives** (from the original session)", ""]
                out += [f"- {o}" for o in s["objectives"]]
            if s["rules"]:
                out += ["", "**Rules on the boards**", ""]
                out += [f"- {r['text']}" + (" (warning)" if r["kind"] == "warning" else "")
                        for r in s["rules"]]
            if s["key_terms"]:
                out += ["", "**Key terms**", ""]
                out += [f"- {t['term']}: {t['explanation']} ({t['label']})" for t in s["key_terms"]]
            if s["glossed_words"]:
                out += ["", "**Glossed words**", ""]
                out += [f"- {g['word']} (= {g['gloss']})" for g in s["glossed_words"]]
            if s["refs"]:
                out += ["", "**Refers to**", ""]
                out += [f"- {where(r)}, in `{r['utterance']}` ({r['provenance']})" for r in s["refs"]]
            if s["referenced_by"]:
                out += ["", "**Referred to by**", ""]
                out += [f"- {titles.get(r['lesson'])}, `{r['utterance']}`" for r in s["referenced_by"]]
            out += ["", "**Narration**", "", s["narration_text"], "",
                    "**Board text**", "", "```", s["board_text"], "```"]
    if ix["references"]:
        out += ["", "---", "", "## All references", ""]
        for r in ix["references"]:
            out.append(f"- {titles.get(r['from']['lesson'])} `{r['from']['utterance']}` -> "
                       f"{where(r['to'])} ({r['provenance']}): \"{r['text']}\"")
    out += ["", "---", "", "## Library", ""]
    if ix["library"]:
        out += ["| Recording | Length | Lesson |", "|---|---|---|"]
        out += [f"| {r['title']} | {hms(r['duration_s'])} | {r['lesson'] or 'no lesson yet'} |"
                for r in ix["library"]]
    else:
        out.append("No library inventory: only the lesson folders are listed.")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# For the model stages
# ---------------------------------------------------------------------------

def catalogue(L: Path) -> list[dict]:
    """The other lessons as a model sees them: id, titles, status, and for a
    built lesson its sections by id and title. Empty before any index. Titles
    only: with objectives, one lesson took 13,700 characters of every
    understanding call, which a library of sixty lessons cannot afford."""
    ix = load(L)
    if not ix:
        return []
    out = []
    for e in ix["lessons"]:
        if e["id"] == L.name:
            continue
        out.append({"lesson": e["id"], "title": e["title"], "short_title": e["short_title"],
                    "status": e["status"],
                    "sections": [{"section": s["id"], "title": s["title"]}
                                 for s in e["sections"] if not s["intro"]]})
    return out


def check_ref(cat: list[dict], lesson: str | None, section: str | None) -> str | None:
    """None when {lesson, section} resolves in the catalogue, else why not."""
    e = next((x for x in cat if x["lesson"] == lesson), None)
    if not e:
        return f"lesson {lesson!r} is not in the course index"
    if section and not any(s["section"] == section for s in e["sections"]):
        return f"lesson {lesson!r} has no section {section!r}"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path, help="a lesson folder, or the lessons folder")
    ap.add_argument("--inventory", type=Path,
                    help="the library inventory CSV (default <library>/course/library_inventory.csv)")
    a = ap.parse_args()
    build(a.target, a.inventory)


if __name__ == "__main__":
    main()
