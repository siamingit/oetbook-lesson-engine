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

Categories, the contents slide's groupings a level above sections
(docs/00-PRODUCT.md §1), are maintainer data like those titles:

    .venv/Scripts/python spike/scripts/build_sections.py <lesson_dir> --categories FILE

FILE is JSON: [{"title": "...", "sections": ["section title", ...]}, ...] in
the contents slide's order, the maintainer's translation. They are stored once,
as the top-level `categories` list, and kept across re-runs; each section's
`category` is written from that list every time, never kept on its own. A
write that would lose a category - a category naming a section the lesson no
longer has, or a section carrying a category the list does not back - is
refused and nothing is written. --set carries a retitled section's place in
its category with it.

The title slide is the page before the contents slide. A deck with no
contents slide has it named by the maintainer, and its lesson introduction
(docs/00-PRODUCT.md §2a) is sourced from the recording's opening, whatever
slide is on screen, and stored with the title slide's page (maintainer,
2026-09-24):

    .venv/Scripts/python spike/scripts/build_sections.py <lesson_dir> --title-page 3
    .venv/Scripts/python spike/scripts/build_sections.py <lesson_dir> --intro-range 0 240

--title-page records `lesson.page_by` and, with no contents slide, the
top-level `intro` ({source, from_s, to_s}); --intro-range sets its range in
seconds once the transcript shows where the opening ends.

A page the timeline splits into several intervals, with off-deck material
between them, is read by the understanding stage as one span (Grammar 2 page
8, maintainer 2026-09-24), with what is on screen off the deck recorded:

    .venv/Scripts/python spike/scripts/build_sections.py <lesson_dir> --page-span 8 3014 4046
    .venv/Scripts/python spike/scripts/build_sections.py <lesson_dir> --off-deck 8 3708 3816 "a web page"

stored as the top-level `page_spans` ({page: {from_s, to_s, off_deck: [{from_s,
to_s, what}], by}}).

Every maintainer record survives a full re-run or stops it: titles (--set),
the description (--description), diagram pages (--diagram-pages), the title
slide and introduction range (--title-page, --intro-range), accepted
board splits (--accept-boards, kept for a section covering exactly the same
slides) and categories. A re-run that would drop any of them, or any field it
does not itself write, is refused with the list of what would be lost, and
nothing is written.
"""

import datetime
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


def fragmented(text: str) -> bool:
    """A text layer pypdfium2 returns one glyph per line, with no spaces
    (Grammar 2, page 7: "T\\r\\nh\\r\\ne\\r\\nd..."): most lines are one or
    two characters long."""
    lines = [l for l in text.splitlines() if l.strip()]
    return len(lines) >= 10 and sorted(len(l.strip()) for l in lines)[len(lines) // 2] <= 2


def slide_text(pdf: Path, page: int) -> str:
    """A deck page's text layer, as the understanding and screens stages read
    it: pypdfium2's, unless that comes out fragmented, when pdftotext (poppler,
    already used by the keyterm stages) reads the same layer with its words
    and spaces intact. A page pypdfium2 reads whole is returned unchanged."""
    import pypdfium2 as pdfium
    tp = pdfium.PdfDocument(str(pdf))[page - 1].get_textpage()
    text = tp.get_text_range(0, tp.count_chars())
    if not fragmented(text):
        return text
    import subprocess
    r = subprocess.run(["pdftotext", "-enc", "UTF-8", "-f", str(page), "-l", str(page),
                        str(pdf), "-"], capture_output=True, text=True, encoding="utf-8",
                       check=True)
    return r.stdout.replace("\f", "").strip() + "\n"


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


def categorise(info: dict, previous_sections: list[dict]) -> None:
    """Write each section's `category` from the category list, the one place
    the maintainer's categories are stored. Refuses, before anything is
    written, a list naming a section the lesson does not have or naming one
    twice, and a section of `previous_sections` whose category the list does
    not back: either would lose maintainer data silently."""
    cats = info.get("categories") or []
    titles = {s["title"] for s in info["sections"]}
    of: dict[str, str] = {}
    for c in cats:
        for t in c["sections"]:
            if t not in titles:
                raise SystemExit(f"REFUSED: category {c['title']!r} lists the section {t!r}, "
                                 "which this lesson does not have (a heading or title changed?). "
                                 "Nothing written. Fix the category with --categories, or the "
                                 "title with --set, then re-run.")
            if t in of:
                raise SystemExit(f"REFUSED: the section {t!r} is in two categories, {of[t]!r} "
                                 f"and {c['title']!r}. Nothing written.")
            of[t] = c["title"]
    for s in previous_sections:
        if s.get("category") and s["category"] != of.get(s["title"]):
            raise SystemExit(f"REFUSED: the section {s['title']!r} has the category "
                             f"{s['category']!r}, which the category list does not give it "
                             f"({of.get(s['title'])!r}). Nothing written. Record the "
                             "categories with --categories first.")
    for s in info["sections"]:
        if s["title"] in of:
            s["category"] = of[s["title"]]
        else:
            s.pop("category", None)
    if cats:
        free = [s["title"] for s in info["sections"] if s["title"] not in of]
        if free:
            print("note: sections in no category: " + ", ".join(repr(t) for t in free))


def nothing_lost(previous: dict, out: dict) -> None:
    """Refuses a full re-run that would drop anything already recorded: a
    maintainer title, a board-split acceptance or a category that no longer
    lands on its section, or any field of the file, the lesson or a section
    that the re-run does not write (a hand-recorded field is kept or it stops
    the run, never lost). Only `why`, the hint on an untitled section, is
    re-derived. A section with no maintainer data whose slides were regrouped
    is simply rebuilt from the deck."""
    lost = [f"the field {k!r}" for k in previous if k not in out]
    lost += [f"the lesson's {k!r}" for k in previous.get("lesson") or {} if k not in out["lesson"]]
    new = {s["pages"][0]: s for s in out["sections"]}
    for s in previous.get("sections", []):
        where = f"pages {s['pages']} ({s['title']!r})"
        t = new.get(s["pages"][0])
        held = [k for k in ("boards_accepted", "category") if s.get(k)]
        if s.get("status") == "maintainer":
            held.insert(0, "maintainer title")
        if t is None:
            if held:
                lost.append(f"{where}: {', '.join(held)}; no section starts on page "
                            f"{s['pages'][0]} any more")
            continue
        lost += [f"{where}: the field {k!r}" for k in s
                 if k not in t and k not in ("why", "boards_accepted")]   # the latter below
        if s.get("status") == "maintainer" and t["title"] != s["title"]:
            lost.append(f"{where}: its maintainer title")
        if s.get("boards_accepted") and t.get("boards_accepted") != s["boards_accepted"]:
            lost.append(f"{where}: the maintainer's acceptance of its board splits; the "
                        f"section now covers pages {t['pages']} (re-accept with --accept-boards)")
    if lost:
        raise SystemExit("REFUSED: this re-run would lose recorded data. Nothing written.\n  "
                         + "\n  ".join(dict.fromkeys(lost)))


def write(out_path: Path, info: dict) -> None:
    out_path.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")


INTRO_SOURCE = ("the recording's opening, whatever slide is on screen: the deck has no "
                "contents slide (maintainer, 2026-09-24)")


def main() -> None:
    lesson = Path(sys.argv[1])
    out_path = lesson / "analysis" / "sections.json"
    previous = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    today = datetime.date.today().isoformat()

    if "--intro-range" in sys.argv:
        # The introduction's source in a deck with no contents slide: the
        # recording from FROM to TO seconds, whatever slide is on screen.
        if "intro" not in previous:
            raise SystemExit("no introduction range to set: it exists only for a deck with no "
                             "contents slide, after --title-page")
        i = sys.argv.index("--intro-range")
        a, b = float(sys.argv[i + 1]), float(sys.argv[i + 2])
        if not 0 <= a < b:
            raise SystemExit(f"bad range {a}-{b}")
        by = sys.argv[sys.argv.index("--by") + 1] if "--by" in sys.argv else "maintainer"
        previous["intro"].update(from_s=a, to_s=b, range_by=f"{by} {today}")
        write(out_path, previous)
        print(f"introduction source: the recording {a:.0f}-{b:.0f} s ({by})")
        return
    if "--page-span" in sys.argv or "--off-deck" in sys.argv:
        # A page whose teaching the timeline splits into several intervals,
        # with off-deck material between (Grammar 2 page 8, maintainer
        # 2026-09-24): its understanding reads the recording from FROM to TO
        # as one span. --off-deck records what is on screen in a stretch of it
        # that is not the deck, so the model is told.
        by = sys.argv[sys.argv.index("--by") + 1] if "--by" in sys.argv else "maintainer"
        spans = previous.setdefault("page_spans", {})
        if "--page-span" in sys.argv:
            i = sys.argv.index("--page-span")
            page, a, b = sys.argv[i + 1], float(sys.argv[i + 2]), float(sys.argv[i + 3])
            if not 0 <= a < b:
                raise SystemExit(f"bad range {a}-{b}")
            spans[page] = {**spans.get(page, {"off_deck": []}), "from_s": a, "to_s": b,
                           "by": f"{by} {today}"}
            print(f"page {page}: understanding reads the recording {a:.0f}-{b:.0f} s ({by})")
        else:
            i = sys.argv.index("--off-deck")
            page, a, b, what = (sys.argv[i + 1], float(sys.argv[i + 2]), float(sys.argv[i + 3]),
                                sys.argv[i + 4])
            if page not in spans or not spans[page]["from_s"] <= a < b <= spans[page]["to_s"]:
                raise SystemExit("an off-deck stretch lies inside a page span set with --page-span")
            spans[page]["off_deck"].append({"from_s": a, "to_s": b, "what": what})
            print(f"page {page}: off deck {a:.0f}-{b:.0f} s: {what}")
        write(out_path, previous)
        return
    if "--title-page" in sys.argv:
        # The title slide, named by the maintainer where no contents slide
        # follows it to find it by. It is not a section; the lesson title is
        # read from it. The deck is then re-read below.
        if not previous:
            raise SystemExit("run without --title-page first")
        n = int(sys.argv[sys.argv.index("--title-page") + 1])
        previous["lesson"].update(page=n, page_by=f"maintainer {today}")
        if not previous.get("contents_page") and "intro" not in previous:
            previous["intro"] = {"source": INTRO_SOURCE, "from_s": 0.0, "to_s": None}

    if "--categories" in sys.argv:
        # The contents slide's groupings, translated by the maintainer
        # (docs/00-PRODUCT.md §1). Kept across re-runs like a maintainer title.
        if not previous:
            raise SystemExit("run without --categories first")
        src = Path(sys.argv[sys.argv.index("--categories") + 1])
        given = json.loads(src.read_text(encoding="utf-8"))
        cp = previous.get("contents_page")
        prov = ("source-derived: the deck's own contents slide"
                + (f" (page {cp})" if cp else "") + ", translated and corrected by the "
                f"maintainer, {datetime.date.today().isoformat()}")
        previous["categories"] = [{**c, "sections": list(c["sections"]),
                                   "provenance": c.get("provenance") or prov} for c in given]
        categorise(previous, [])
        write(out_path, previous)
        print(f"categories set (maintainer): {len(given)}")
        for c in previous["categories"]:
            print(f"  {c['title']!r}: {', '.join(repr(t) for t in c['sections'])}")
        return

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
                old = s["title"]
                s.update(title=title, status="maintainer", corrected_from=None)
                s.pop("why", None)
                # The section keeps its place in its category under its new title.
                for c in previous.get("categories") or []:
                    c["sections"] = [title if t == old else t for t in c["sections"]]
                categorise(previous, [])
                write(out_path, previous)
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
    if previous.get("lesson", {}).get("page_by"):                  # --title-page
        title_page = pages[previous["lesson"]["page"] - 1]
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
                      "maintainer (--set) before its pages can be built. Categories are the "
                      "deck's own contents-slide groupings, a level above sections "
                      "(docs/00-PRODUCT.md §1).",
           "lesson": {"title": lesson_title, "page": title_page["page"] if title_page else None,
                      **({"page_by": previous["lesson"]["page_by"]}
                         if previous.get("lesson", {}).get("page_by") else {}),
                      "status": previous.get("lesson", {}).get("status", "from-deck"),
                      "description": previous.get("lesson", {}).get("description"),
                      "description_status": previous.get("lesson", {}).get("description_status")},
           "contents_page": contents_page,
           **({"intro": previous["intro"]} if "intro" in previous else {}),
           **({"page_spans": previous["page_spans"]} if "page_spans" in previous else {}),
           "diagram_pages": previous.get("diagram_pages", []),
           "sections": sections}
    if "categories" in previous:
        out["categories"] = previous["categories"]
    categorise(out, previous.get("sections", []))       # refuses before anything is written
    # Board splits the maintainer accepted (--accept-boards) stay with a
    # section that covers exactly the same slides; for any other grouping the
    # acceptance was of different boards and is not carried.
    prev_first = {s["pages"][0]: s for s in previous.get("sections", [])}
    for s in sections:
        p = prev_first.get(s["pages"][0])
        if p and p.get("boards_accepted") and p["pages"] == s["pages"]:
            s["boards_accepted"] = p["boards_accepted"]
    nothing_lost(previous, out)                         # refuses before anything is written
    write(out_path, out)
    print(f"lesson title: {lesson_title!r} (slide {out['lesson']['page']}); contents slide {contents_page}")
    for s in sections:
        flag = "" if s["status"] in ("ok", "maintainer") else "   <-- NEEDS TITLE: " + s["why"]
        tag = " [maintainer]" if s["status"] == "maintainer" else ""
        print(f"  pages {s['pages']}: {s['title']!r}{tag}"
              + (f" (printed {s['corrected_from']!r})" if s["corrected_from"] else "") + flag)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
