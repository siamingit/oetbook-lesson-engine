"""The two boards not written from a page of source material: the title
board and the contents board (docs/00-PRODUCT.md §2a).

    .venv/Scripts/python spike/scripts/build_lesson_boards.py <lesson_dir>

Reads:  <lesson_dir>/analysis/sections.json
Writes: <lesson_dir>/analysis/screens/lesson-boards.json

Deterministic: no model. The title board carries the deck's lesson title.
Its one-line description is UNKNOWN until the maintainer writes one, and is
rendered as a visible placeholder rather than invented. The contents board
lists the deck's categories, each with its sections, in lesson order.
Both are generated after the sections exist and follow their titles.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def write_intro_screens(lesson: Path, sec: dict, boards: dict) -> None:
    """The title and contents boards as a narratable section, the lesson's
    introduction (docs/00-PRODUCT.md §2a, "Every lesson opens with a narrated
    introduction"). Same format as a section's screens.json, so the narration,
    QA and players treat it like any section; written by code, not a model.

      t1  title board: the lesson title fixed; the description a note the
          narration reveals when it says what the lesson is about
      t2  contents board: one block per category, each revealed as it is named

    Stored with the contents slide's page (paths.screens_dir_for), because the
    understanding of that slide's interval is the narration's source."""
    import paths
    from write_screens import BUDGET, block_height, stack_height
    page = sec.get("contents_page")
    tb, cb = boards["title"], boards["contents"]
    und = paths.understanding_dir(lesson, page) / "understanding.json"
    beats = ([b["id"] for b in json.loads(und.read_text(encoding="utf-8"))["beats"]]
             if und.exists() else [])

    def blk(bid, typ, text, explanation=None, label=None, prov="source-derived", note=""):
        return {"id": bid, "type": typ, "text": text, "label": label, "term": None,
                "explanation": explanation, "left": None, "right": None, "family": None,
                "kind": None, "icon": None, "items": None, "header": None, "rows": None,
                "tags": None, "exercise_item": None, "anchor": typ == "lesson_title",
                "provenance": prov, "from_beats": beats, "note": note}

    title = blk("k01", "lesson_title", tb["title"],
                note="The deck's lesson title, slide " + str(sec["lesson"].get("page")))
    desc = blk("k02", "plain", tb["description"] or "",
               prov=tb.get("description_provenance") or "authored",
               note="The maintainer's one-line description (sections.json).")
    items = [blk(f"k{n + 2:02d}", "contents_item", c["title"], " · ".join(c["sections"]),
                 label=str(n), note="Category " + str(n) + " of the contents slide, with its sections")
             for n, c in enumerate(cb["categories"], 1)]
    blocks = {b["id"]: b for b in [title, desc] + items}
    topics = [
        {"id": "t1", "title": "Title board", "from_beats": beats, "split": None,
         "thoughts": [{"id": "t1.1", "purpose": "the lesson title, then what the lesson is about",
                       "blocks": [title, desc]}]},
        {"id": "t2", "title": "Contents board", "from_beats": beats, "split": None,
         "thoughts": [{"id": "t2.1", "purpose": "each category, revealed as it is named",
                       "blocks": items}]},
    ]

    def state(sid, fixed, working):
        h = stack_height(list(fixed) + list(working), blocks)
        return {"id": sid, "working": list(working), "notes": len(working),
                "height": round(h, 3), "fill": round(h / BUDGET, 3), "thoughts": [sid.split(".")[0] + ".1"]}
    out_boards = [
        {"id": "t1", "title": "", "label": "Title board", "fixed": ["k01"],
         "fixed_height": round(block_height(title), 3),
         "states": [state("t1.s1", ["k01"], ["k02"])], "erasures": []},
        {"id": "t2", "title": cb["heading"], "label": "Contents board", "fixed": [],
         "fixed_height": 0.0,
         "states": [state("t2.s1", [], [b["id"] for b in items])], "erasures": []},
    ]
    findings = []
    for bd in out_boards:
        for s in bd["states"]:
            if s["height"] > 0.84:
                findings.append({"severity": "fail", "where": s["id"],
                                 "what": f"board height {s['height']:.0%} exceeds the content band"})
    screens = {"lesson_title": sec["lesson"], "lesson": lesson.name, "page": page, "pages": [page],
               "section": {"title": "Introduction", "pages": [page], "intro": True},
               "model": None, "raw_id": None,
               "layout": "Written by build_lesson_boards.py, not a model: the title board and the "
                         "contents board, one state each.",
               "topics": topics, "boards": out_boards, "overrides": [], "merged_splits": [],
               "corrections": [], "replacements": [], "dropped": [], "unresolved": [],
               "audit": findings}
    d = paths.screens_dir_for(lesson, [page])
    d.mkdir(parents=True, exist_ok=True)
    (d / "screens.json").write_text(json.dumps(screens, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"introduction boards: {d / 'screens.json'} | contents board fill "
          f"{out_boards[1]['states'][0]['height']:.0%} of frame | "
          f"{len(findings)} failures | beats from understanding: {len(beats)}")


def main() -> None:
    lesson = Path(sys.argv[1])
    sec = json.loads((lesson / "analysis" / "sections.json").read_text(encoding="utf-8"))
    title = sec["lesson"]["title"]
    cats = sec.get("categories") or [{"title": None, "sections": [s["title"] for s in sec["sections"]]}]
    desc = sec["lesson"].get("description")
    boards = {
        "title": {"id": "lesson.title", "kind": "title", "title": title,
                  "description": desc,
                  "description_provenance": (sec["lesson"].get("description_status") or "maintainer")
                                            if desc else None,
                  "description_note": None if desc else
                                      "UNKNOWN: a one-line English description of the lesson is "
                                      "to be written by the maintainer; rendered as a placeholder "
                                      "until then (docs/00-PRODUCT.md §2a).",
                  "provenance": "source-derived: the deck's title slide, page "
                                + str(sec["lesson"].get("page"))
                                + ("; description: maintainer's own words (sections.json)"
                                   if desc else "")},
        "contents": {"id": "lesson.contents", "kind": "contents",
                     "heading": "What you will learn",
                     "categories": [{"title": c["title"], "sections": c["sections"]} for c in cats],
                     "provenance": "source-derived: the deck's contents slide, page "
                                   + str(sec.get("contents_page")) + ", translated and corrected "
                                   "by the maintainer; section titles from sections.json"},
    }
    out = lesson / "analysis" / "screens" / "lesson-boards.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(boards, ensure_ascii=False, indent=1), encoding="utf-8")
    write_intro_screens(lesson, sec, boards)
    print(f"title board: {title!r}; contents board: {len(cats)} categories, "
          f"{sum(len(c['sections']) for c in cats)} sections")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
