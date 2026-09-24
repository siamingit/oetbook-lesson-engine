"""The lesson's structure from the deck: one section per slide heading.

    .venv/Scripts/python spike/scripts/build_sections.py <lesson_dir>
    .venv/Scripts/python spike/scripts/build_sections.py <lesson_dir> --set 11 "Perfect tenses on a timeline"

Reads:  <lesson_dir>/source/slides.pdf              (text with geometry)
        <lesson_dir>/analysis/deck_defects.json     (heading corrections)
Writes: <lesson_dir>/analysis/sections.json

docs/00-PRODUCT.md §1: a lesson is titled from the deck's own title slide;
its sections are the deck's slides, each titled with that slide's own
heading corrected for registered deck defects; boards are steps inside a
section with no titles of their own. Consecutive slides that share a heading
are one section.

A heading is read BY POSITION, not by text order: among the text lines whose
top sits in the top 18% of the page, the one set in the largest type (ties
to the higher line). Reading order failed on this deck twice: a table's
first cell came before the heading on pages 6-10, and a body line came
first on page 18.

Titles are normalised deterministically: register corrections applied,
" - " becomes ": ", and sentence case with all-caps tokens (OET) kept.

A slide with no heading, or whose printed heading is wrong for its content,
is titled by the maintainer with --set, recorded with status "maintainer"
and kept across re-runs. Until then it has status "needs-title" and blocks
the screens stage for its pages.
"""

import json
import re
import sys
from pathlib import Path

NON_LATIN = re.compile(r"[؀-ۿ]")
TOP_BAND = 0.18


def page_lines(page) -> list[tuple[float, float, float, str]]:
    """(top as a fraction from the page top, glyph height fraction, left x
    fraction, text) for every non-blank text line of a page."""
    W, H = page.get_width(), page.get_height()
    tp = page.get_textpage()
    text = tp.get_text_range(0, tp.count_chars())
    out, start = [], 0
    for i, ch in enumerate(text + "\n"):
        if ch in "\r\n":
            if i > start and text[start:i].strip():
                boxes = [tp.get_charbox(k) for k in range(start, i) if not text[k].isspace()]
                if boxes:
                    top = max(b[3] for b in boxes)
                    bottom = min(b[1] for b in boxes)
                    left = min(b[0] for b in boxes)
                    out.append((1 - top / H, (top - bottom) / H, left / W, text[start:i].strip()))
            start = i + 1
    return out


BAR = (0.03, 0.115)      # the template's header bar, as fractions from the page top


def heading_of(page) -> str | None:
    """The slide's heading: a line whose top sits inside the header bar wins;
    otherwise the largest-type line in the top band, ties to the higher line.
    Page 15 of Grammar 1 has a body line in larger type below the bar; page
    12 has no bar and its heading at 12%, level with a body mock-up."""
    cands = [l for l in page_lines(page) if l[0] <= TOP_BAND and not NON_LATIN.search(l[3])]
    if not cands:
        return None
    in_bar = [l for l in cands if BAR[0] <= l[0] <= BAR[1]]
    pool = in_bar or cands
    pool.sort(key=lambda l: (-round(l[1], 3), l[0]))
    return pool[0][3]


def latin_lines(page) -> list[str]:
    return [l[3] for l in page_lines(page) if not NON_LATIN.search(l[3])]


def correct(h: str, page: int, defects: list[dict]) -> tuple[str, str | None]:
    for d in defects:
        if d["page"] == page and d["printed"] in h:
            return h.replace(d["printed"], d["correction"]), d["printed"]
    return h, None


def title_from(h: str) -> str:
    """Deterministic title form: ' - ' to ': ', sentence case, all-caps tokens kept."""
    h = re.sub(r"\s+-\s+", ": ", h.strip())
    words = h.split(" ")
    out = []
    for i, w in enumerate(words):
        if len(w) >= 2 and w.isupper():
            out.append(w)
        else:
            out.append(w.lower())
    t = " ".join(out)
    return t[:1].upper() + t[1:]


def main() -> None:
    lesson = Path(sys.argv[1])
    out_path = lesson / "analysis" / "sections.json"
    previous = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}

    if "--description" in sys.argv:
        # The title board's one-line description, in the maintainer's words
        # (docs/00-PRODUCT.md §2a). Kept across re-runs like a maintainer title.
        if not previous:
            raise SystemExit("run without --description first")
        text = sys.argv[sys.argv.index("--description") + 1]
        previous["lesson"]["description"] = text
        previous["lesson"]["description_status"] = "maintainer"
        out_path.write_text(json.dumps(previous, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"lesson description set (maintainer): {text!r}")
        return
    if "--diagram-pages" in sys.argv:
        # Slides whose teaching is carried by a diagram: write_screens.py shows
        # their image to the model as a reference for the diagram's idea
        # (docs/02-DESIGN-SYSTEM.md §7a). Named by the maintainer.
        if not previous:
            raise SystemExit("run without --diagram-pages first")
        pages_ = sorted(int(p) for p in sys.argv[sys.argv.index("--diagram-pages") + 1].split(","))
        previous["diagram_pages"] = pages_
        out_path.write_text(json.dumps(previous, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"diagram pages set (maintainer): {pages_}")
        return
    if "--accept-boards" in sys.argv:
        # The maintainer accepted these sections' board splits as built
        # (2026-09-24, "the multi-board sections are accepted as split");
        # the audit's split-count rule then warns instead of failing them.
        if not previous:
            raise SystemExit("run without --accept-boards first")
        pages_ = {int(p) for p in sys.argv[sys.argv.index("--accept-boards") + 1].split(",")}
        for s in previous["sections"]:
            if set(s["pages"]) & pages_:
                s["boards_accepted"] = "maintainer 2026-09-24"
        out_path.write_text(json.dumps(previous, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"board splits accepted by the maintainer for pages {sorted(pages_)}")
        return
    if "--set" in sys.argv:
        i = sys.argv.index("--set")
        page, title = int(sys.argv[i + 1]), sys.argv[i + 2]
        if not previous:
            raise SystemExit("run without --set first")
        for s in previous["sections"]:
            if page in s["pages"]:
                s.update(title=title, status="maintainer", corrected_from=None)
                s.pop("why", None)
                out_path.write_text(json.dumps(previous, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"set pages {s['pages']} to {title!r} (maintainer)")
                return
        raise SystemExit(f"page {page} is in no section")

    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(lesson / "source" / "slides.pdf"))
    reg_path = lesson / "analysis" / "deck_defects.json"
    defects = json.loads(reg_path.read_text(encoding="utf-8"))["defects"] if reg_path.exists() else []
    kept = {s["pages"][0]: s for s in previous.get("sections", []) if s.get("status") == "maintainer"}

    pages = []
    for i in range(len(doc)):
        page = doc[i]
        pages.append({"page": i + 1, "heading": heading_of(page), "latin": latin_lines(page)})

    # The contents slide is the one whose heading names contents; the title
    # slide is the page before it, and the deck's lesson title is that page's
    # Latin lines joined. Branding pages (the first, and any page whose Latin
    # text only repeats the first page's) are not sections.
    contents = next((p for p in pages if p["heading"] and "content" in p["heading"].lower()), None)
    contents_page = contents["page"] if contents else None
    title_page = next((p for p in pages if contents and p["page"] == contents["page"] - 1), None)
    lesson_title = ": ".join(title_page["latin"]) if title_page and title_page["latin"] else None
    branding = set(pages[0]["latin"])
    if previous.get("lesson", {}).get("status") == "maintainer":
        lesson_title = previous["lesson"]["title"]

    sections = []
    for p in pages:
        if title_page and p["page"] in (title_page["page"], contents_page):
            continue
        if p["page"] == 1 or (p["latin"] and set(p["latin"]) <= branding and not p["heading"]):
            continue                                      # branding, front or back
        h = p["heading"]
        if not h and not p["latin"]:
            if p["page"] in (1, len(pages)):
                continue                                  # branding pages
        if h and sections and sections[-1]["heading"] and h.lower() == sections[-1]["heading"].lower() \
                and p["page"] == sections[-1]["pages"][-1] + 1:
            sections[-1]["pages"].append(p["page"])
            continue
        if h:
            corrected, was = correct(h, p["page"], defects)
            sections.append({"pages": [p["page"]], "heading": h, "title": title_from(corrected),
                             "corrected_from": was, "status": "ok"})
        elif p["latin"]:
            sections.append({"pages": [p["page"]], "heading": None, "title": "",
                             "corrected_from": None, "status": "needs-title",
                             "why": "no heading in the header band; set a title by hand"})
        else:
            if any(NON_LATIN.search(l[3]) for l in page_lines(doc[p["page"] - 1])):
                continue                                  # a Persian-only page: branding
            sections.append({"pages": [p["page"]], "heading": None, "title": "",
                             "corrected_from": None, "status": "needs-title",
                             "why": "no text layer on this slide; set a title by hand"})
    for s in sections:
        k = kept.get(s["pages"][0])
        if k:
            s.update(title=k["title"], status="maintainer", corrected_from=None)
            s.pop("why", None)

    out = {"purpose": "Lesson structure from the deck (docs/00-PRODUCT.md §1). Sections are "
                      "slides, titled by their header-band headings corrected for deck defects "
                      "and normalised; a section with status needs-title must be titled by the "
                      "maintainer (--set) before its pages can be built.",
           "lesson": {"title": lesson_title, "page": title_page["page"] if title_page else None,
                      "status": previous.get("lesson", {}).get("status", "from-deck"),
                      "description": previous.get("lesson", {}).get("description"),
                      "description_status": previous.get("lesson", {}).get("description_status")},
           "contents_page": contents_page,
           "diagram_pages": previous.get("diagram_pages", []),
           "sections": sections}
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"lesson title: {lesson_title!r} (slide {out['lesson']['page']}); contents slide {contents_page}")
    for s in sections:
        flag = "" if s["status"] in ("ok", "maintainer") else "   <-- NEEDS TITLE: " + s["why"]
        tag = " [maintainer]" if s["status"] == "maintainer" else ""
        print(f"  pages {s['pages']}: {s['title']!r}{tag}"
              + (f" (printed {s['corrected_from']!r})" if s["corrected_from"] else "") + flag)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
