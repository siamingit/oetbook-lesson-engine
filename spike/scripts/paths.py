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

from pathlib import Path


def page_tag(page: int) -> str:
    return f"page-{page}"


def understanding_dir(lesson: Path, page: int) -> Path:
    return lesson / "analysis" / "understanding" / page_tag(page)


def script_dir(lesson: Path, page: int) -> Path:
    return lesson / "analysis" / "script" / page_tag(page)


def generated_dir(lesson: Path, page: int) -> Path:
    return lesson / "generated" / page_tag(page)


def screens_dir(lesson: Path, page: int) -> Path:
    return lesson / "analysis" / "screens" / page_tag(page)
