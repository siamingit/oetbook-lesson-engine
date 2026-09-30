"""The two boards not written from a page of source material: the title
board and the contents board (docs/00-PRODUCT.md §2a).

    .venv/Scripts/python spike/scripts/build_lesson_boards.py <lesson_dir>

Reads:  <lesson_dir>/analysis/sections.json
Writes: <lesson_dir>/analysis/screens/lesson-boards.json

Deterministic: no model. The title board carries the deck's lesson title.
Its one-line description is UNKNOWN until the maintainer writes one, and is
rendered as a visible placeholder rather than invented. The contents board
lists the deck's categories, each with its sections, in lesson order; a deck
with no contents slide has no categories, and the board lists one item per
section (maintainer, 2026-09-24). Both are generated after the sections exist
and follow their titles.
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

    Stored with the introduction's page (paths.intro_section: the contents
    slide's, or the title slide's in a deck with none), because the
    understanding of that page is the narration's source."""
    import board_style
    import paths
    from write_screens import BUDGET, block_height, stack_height
    page = paths.intro_section(sec)["pages"][0]
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
    # The title board shows what the narration describes (ADR 014): the
    # lesson's own intro blocks (sections.json `intro_board`: a link to the
    # previous lesson, a problem from a letter), then the description, what
    # the student will be able to do by the end.
    extra = []
    for n, x in enumerate((sec.get("intro_board") or {}).get("blocks") or [], 2):
        b = blk(f"k{n:02d}", x["type"], x.get("text"), x.get("explanation"), x.get("label"),
                prov=x.get("provenance") or "authored", note=x.get("note") or "")
        b.update({k: x[k] for k in ("term", "left", "right") if x.get(k)})
        # the board style (ADR 008), as the screens stage derives it: a
        # comparison is a change card, a term box a note card with its tag
        b["role"] = x.get("role") or ("example" if x["type"] in ("comparison", "answer_row", "error_row")
                                      else "note")
        if x["type"] == "comparison":
            b["style"], b["card"] = "card", board_style.card_of(b)
        elif x["type"] == "term_box":
            b["style"] = "term"
        extra.append(b)
    desc = blk(f"k{len(extra) + 2:02d}", "plain", tb["description"] or "",
               prov=tb.get("description_provenance") or "authored",
               note="The maintainer's one-line description (sections.json).")
    first = len(extra) + 2
    items = [blk(f"k{n + first:02d}", "contents_item", c["title"], " · ".join(c["sections"]) or None,
                 label=str(n), prov=c.get("provenance") or "source-derived",
                 note=("Category " + str(n) + " of the contents slide, with its sections"
                       if c["sections"] else "Section " + str(n) + " of the lesson, by its title "
                       "(sections.json); the deck has no contents slide"))
             for n, c in enumerate(cb["categories"], 1)]
    # a picture on each board (ADR 021), from the agent's briefs in pictures.json
    from write_screens import load_pictures, gloss_alt
    import gloss_images
    pic_spec = {e["topic"]: e for e in (load_pictures(lesson).get("sections") or {}).get(
        paths.section_tag([page])) or [] if (e.get("brief") or "").strip()}
    pics = {}
    nxt = len(extra) + 2 + len(items) + 1
    for topic in (1, 2):
        e = pic_spec.get(topic)
        if not e:
            continue
        b = blk(f"k{nxt:02d}", "picture", None, prov="authored",
                note="ADR 021: the board's picture, brief by the agent. " + (e.get("why") or ""))
        b.update(icon=e["brief"].strip(), anchor=False, role="note")
        got = gloss_images.find(lesson, b["icon"])
        b["image"] = {"file": got["file"], "alt": got.get("alt") or gloss_alt(b)} if got else None
        pics[topic] = b
        nxt += 1
    blocks = {b["id"]: b for b in [title] + extra + [desc] + items + list(pics.values())}
    topics = [
        {"id": "t1", "title": "Title board", "from_beats": beats, "split": None,
         "thoughts": [{"id": "t1.1", "purpose": "the lesson title, then what the lesson is about",
                       "blocks": ([pics[1]] if 1 in pics else []) + [title] + extra + [desc]}]},
        {"id": "t2", "title": "Contents board", "from_beats": beats, "split": None,
         "thoughts": [{"id": "t2.1", "purpose": "each category, revealed as it is named",
                       "blocks": ([pics[2]] if 2 in pics else []) + items}]},
    ]

    def state(sid, fixed, working):
        # the board's picture is cleared by the fit when the notes need its
        # room (ADR 021), so the estimate counts the board without it
        h = stack_height([i for i in list(fixed) + list(working) if blocks[i]["type"] != "picture"], blocks)
        return {"id": sid, "working": list(working), "notes": len(working),
                "height": round(h, 3), "fill": round(h / BUDGET, 3), "thoughts": [sid.split(".")[0] + ".1"]}
    out_boards = [
        {"id": "t1", "title": "", "label": "Title board", "fixed": ["k01"],
         "fixed_height": round(block_height(title), 3),
         "states": [state("t1.s1", ["k01"], ([pics[1]["id"]] if 1 in pics else [])
                          + [b["id"] for b in extra + [desc]])], "erasures": []},
        {"id": "t2", "title": cb["heading"], "label": "Contents board", "fixed": [],
         "fixed_height": 0.0,
         "states": [state("t2.s1", [], ([pics[2]["id"]] if 2 in pics else []) + [b["id"] for b in items])],
         "erasures": []},
    ]
    findings = []
    # every section of the lesson is on the contents board by name, authored
    # ones included (maintainer, 2026-09-29; docs/00-PRODUCT.md §2a)
    for title in missing_sections([s["title"] for s in sec["sections"]], items):
        findings.append({"severity": "fail", "where": "t2",
                         "what": f"section {title!r} is not listed on the contents board"})
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
    if findings:
        raise SystemExit("introduction boards: " + "; ".join(f["what"] for f in findings))


def missing_sections(titles: list[str], items: list[dict]) -> list[str]:
    """Section titles that no contents item names: as its own item, or in a
    category's list of sections (" · ")."""
    listed = set()
    for b in items:
        listed.add(b.get("text"))
        listed.update(x.strip() for x in (b.get("explanation") or "").split(" · "))
    return [t for t in titles if t not in listed]


def main() -> None:
    lesson = Path(sys.argv[1])
    sec = json.loads((lesson / "analysis" / "sections.json").read_text(encoding="utf-8"))
    title = sec["lesson"]["title"]
    # No contents slide: one item per section, with no sections listed under it.
    # A title the maintainer set is his wording; one read from a heading is the deck's.
    cats = sec.get("categories") or [
        {"title": s["title"], "sections": [],
         "item_provenance": "maintainer" if s.get("status") == "maintainer" else "source-derived"}
        for s in sec["sections"]]
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
                     "categories": [{"title": c["title"], "sections": c["sections"],
                                     **({"provenance": c["item_provenance"]}
                                        if "item_provenance" in c else {})} for c in cats],
                     "provenance": ("source-derived: the deck's contents slide, page "
                                    + str(sec.get("contents_page")) + ", translated and corrected "
                                    "by the maintainer; section titles from sections.json")
                                   if sec.get("categories") else
                                   "the lesson's sections, by their titles in sections.json; the "
                                   "deck has no contents slide"},
    }
    out = lesson / "analysis" / "screens" / "lesson-boards.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(boards, ensure_ascii=False, indent=1), encoding="utf-8")
    write_intro_screens(lesson, sec, boards)
    print(f"title board: {title!r}; contents board: "
          + (f"{len(cats)} categories, {sum(len(c['sections']) for c in cats)} sections"
             if sec.get("categories") else f"{len(cats)} sections (no contents slide)"))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
