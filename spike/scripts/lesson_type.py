"""A lesson's type, and the features a type turns on (docs/adr/029-listening-lessons.md).

A lesson's type is a field of its lesson config: `analysis/sections.json`,
`lesson.type`, set by `build_sections.py --type` (and, when the file is first
made, from the first word of the lesson's id). A lesson whose config has no
type yet (every lesson built before 2026-10-13) takes the first word of its id,
as the course index does (docs/05-COURSE-INDEX.md, `type`), so it behaves
exactly as before. Features are switched on by type, never by an id prefix.
"""

import json
from pathlib import Path

TYPES = ("grammar", "vocabulary", "reading", "listening", "writing", "speaking")

# What each type turns on. A feature not listed for a type is off for it.
#   practice_set     the lesson teaches an exercises release's set by ID: texts,
#                    questions and answers built by code (ADR 026, ADR 029)
#   keyword_pairs    the match1-match3 marks (ADR 026, bundle 1.13)
#   doc_marks        every phrase of a set's text read aloud is marked (check_doc_marks.py)
#   practice_checks  the runner's lens and question-number checks
#   delivery         the narration's DELIVERY rule (ADR 027 amendment)
#   exam_audio       release audio played in the lesson clock, `play` cues (ADR 029, bundle 1.18)
#   reading_time     a pause marked as reading time may be as long as the exam's (ADR 029)
#   exam_numbers     questions keep their set's numbers, not from 1 in the lesson: Part A
#                    gaps 1-24, Parts B and C their practice numbers (ADR 029, ADR 032)
#   source_terms     the runner runs check_source_terms.py (ADR 029; by hand for Reading)
#   vocabulary_rule  the vocabulary rule (ADR 019)
FEATURES = {
    "vocabulary": {"vocabulary_rule"},
    "reading": {"practice_set", "keyword_pairs", "doc_marks", "practice_checks", "delivery"},
    "listening": {"practice_set", "keyword_pairs", "doc_marks", "practice_checks", "delivery",
                  "exam_audio", "reading_time", "exam_numbers", "source_terms"},
}


def from_id(lesson) -> str:
    """The first word of a lesson's id (its folder's name)."""
    return Path(lesson).name.split("-")[0].lower()


def of(lesson) -> str:
    """The lesson's type: its config's `lesson.type`, else the first word of its id."""
    p = Path(lesson) / "analysis" / "sections.json"
    if p.exists():
        try:
            t = (json.loads(p.read_text(encoding="utf-8")).get("lesson") or {}).get("type")
        except (ValueError, OSError):
            t = None
        if t:
            return str(t).lower()
    return from_id(lesson)


def has(lesson, feature: str) -> bool:
    return feature in FEATURES.get(of(lesson), set())
