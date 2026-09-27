"""Where a page's artefacts live.

Every artefact belongs to exactly one page of one lesson, and nothing is
shared across either boundary -- methodology §19. Before this module the
scripts all took `--page N` but wrote to fixed per-lesson paths, so running
a second page overwrote the first one's understanding, script and model
response, and the applied-edit ledger silently mixed two pages' beats under
the same ids.

`generated/page-NN/` already worked this way; this makes the analysis side
match it rather than inventing a second convention.
"""

import datetime
from pathlib import Path


def keep_superseded(path: Path) -> None:
    """A saved model reply that is about to be replaced was paid for. It is
    kept beside the new one as <stem>.superseded-<time><suffix>, which the
    runner's spend check (build_lesson.spent: raw_response*.json and
    qa/qa_*.json) still counts, so the runner's total always matches what was
    spent (maintainer, 2026-09-27, after two replaced screens drafts of
    Grammar 5 were overwritten and left out of its total). Every stage that
    writes a reply calls this first; nothing is ever deleted."""
    if path.exists():
        stamp = f"{datetime.datetime.now():%Y%m%d-%H%M%S}"
        target = path.with_name(f"{path.stem}.superseded-{stamp}{path.suffix}")
        n = 1
        while target.exists():
            n += 1
            target = path.with_name(f"{path.stem}.superseded-{stamp}-{n}{path.suffix}")
        path.rename(target)


def page_tag(page: int) -> str:
    return f"page-{page}"


def understanding_dir(lesson: Path, page: int) -> Path:
    return lesson / "analysis" / "understanding" / page_tag(page)


def script_dir(lesson: Path, page: int) -> Path:
    return lesson / "analysis" / "script" / page_tag(page)


def generated_dir(lesson: Path, page: int) -> Path:
    return lesson / "generated" / page_tag(page)


def lesson_label(lesson: Path) -> str:
    """The lesson's title for prompts and page headings: the deck title
    recorded in analysis/sections.json, or the lesson folder's name before
    sections exist. Until 2026-09-24 the prompts said "Grammar 1 - Verb
    Tenses" whatever the lesson."""
    import json
    p = lesson / "analysis" / "sections.json"
    if p.exists():
        title = (json.loads(p.read_text(encoding="utf-8")).get("lesson") or {}).get("title")
        if title:
            return title
    return lesson.name


def deck_pages(lesson: Path) -> int:
    import pypdfium2 as pdfium
    return len(pdfium.PdfDocument(str(lesson / "source" / "slides.pdf")))


def screens_dir(lesson: Path, page: int) -> Path:
    return lesson / "analysis" / "screens" / page_tag(page)


def narration_dir(lesson: Path, page: int) -> Path:
    return lesson / "analysis" / "narration" / page_tag(page)


def boards_dir(lesson: Path, page: int) -> Path:
    """Built output for the board model: audio, timeline, bundle, player.
    Beside the old deck-page build in generated/page-NN/, not over it."""
    return lesson / "generated" / page_tag(page) / "boards"


def section_tag(pages: list[int]) -> str:
    """page-NN for a one-page section (page 13 was built that way);
    pages-NN-MM for a section taught across several slides."""
    pages = sorted(pages)
    if len(pages) == 1:
        return page_tag(pages[0])
    return "pages-" + "-".join(f"{p:02d}" for p in pages)


def screens_dir_for(lesson: Path, pages: list[int]) -> Path:
    """Screens are written per SECTION, so a multi-page section never
    collides with a one-page one."""
    return lesson / "analysis" / "screens" / section_tag(pages)


def narration_dir_for(lesson: Path, pages: list[int]) -> Path:
    """Narration is written per section too; it follows the screens."""
    return lesson / "analysis" / "narration" / section_tag(pages)


def boards_dir_for(lesson: Path, pages: list[int]) -> Path:
    return lesson / "generated" / section_tag(pages) / "boards"


def intro_section(info: dict) -> dict | None:
    """The lesson's introduction as a section (docs/00-PRODUCT.md §2a), or
    None. Stored with the contents slide's page, whose interval is its source;
    in a deck with no contents slide, with the title slide's page, its source
    the recording's opening, whatever slide is on screen (sections.json
    `intro`, maintainer 2026-09-24), carried here as `span`."""
    cp = info.get("contents_page")
    if cp:
        return {"title": "Introduction", "pages": [cp], "intro": True}
    it, tp = info.get("intro"), (info.get("lesson") or {}).get("page")
    if it and tp:
        return {"title": "Introduction", "pages": [tp], "intro": True,
                "span": [it["from_s"], it["to_s"]]}
    return None
