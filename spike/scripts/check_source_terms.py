"""Terms from material that must never reach a lesson (maintainer, 2026-10-05).

    .venv/Scripts/python spike/scripts/check_source_terms.py <lesson_dir>

The instructor taught Reading on texts the product may not use (official OET
samples, and a practice set on a course website). Only the method carries
over (docs/adr/026-reading-lessons.md). `<lesson>/analysis/forbidden_source_terms.json`
lists the distinctive terms of those texts: {"terms": [...], "sources": [...]}.
This check searches every board and every utterance the lesson has (screens,
narration, the silent preview's and the player's text.json), whole words, case
aside, and fails on any hit, naming the file and the block or utterance.

The longer terms are also forbidden phrases in the page ledgers, so the
screens and narration audits stop a draft that uses one before it is kept.
"""

import json
import re
import sys
from pathlib import Path


BLOCK_TEXT = ("text", "label", "term", "explanation", "left", "right", "header", "rows", "items")


def strings(obj, where=""):
    if isinstance(obj, str):
        yield where, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from strings(v, f"{where}/{k}")
    elif isinstance(obj, list):
        for n, v in enumerate(obj):
            yield from strings(v, f"{where}/{n}")


def learner_text(name: str, d: dict):
    """What a learner reads or hears: every block's words (screens), every
    utterance's words (narration), and the bundle's text.json whole. Ids,
    reviewer notes and the reviewer's records are not the lesson."""
    if name == "screens.json":
        for t in d["topics"]:
            for h in t["thoughts"]:
                for b in h["blocks"]:
                    for k in BLOCK_TEXT:
                        if b.get(k):
                            yield from strings(b[k], f"/{b['id']}/{k}")
    elif name == "narration.json":
        for bd in d["boards"]:
            for st in bd["states"]:
                for u in st["utterances"]:
                    yield from strings(u.get("text_with_cues") or u.get("text") or "", f"/{u['id']}")
    else:
        # text.json: its words only, never its ids
        for where, s in strings(d):
            if where.rsplit("/", 1)[-1] in ("text", "narration_text", "board_text", "title",
                                            "description") or re.search(r"/(text|words)/\d+$", where):
                yield where, s


def main() -> None:
    L = Path(sys.argv[1])
    spec = json.loads((L / "analysis" / "forbidden_source_terms.json").read_text(encoding="utf-8"))
    rx = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(re.escape(t) for t in spec["terms"]) + r")(?![A-Za-z0-9])", re.I)
    files = [*(L / "analysis" / "screens").rglob("screens.json"),
             *(L / "analysis" / "narration").rglob("narration.json"),
             *[L / "generated" / d / "text.json" for d in ("lesson-preview/silent", "lesson-player")]]
    hits, checked = [], 0
    for f in files:
        if not f.exists():
            continue
        checked += 1
        for where, s in learner_text(f.name, json.loads(f.read_text(encoding="utf-8"))):
            for m in rx.finditer(s):
                hits.append(f"{f.relative_to(L)} {where}: {m.group(0)!r} in {s[:90]!r}")
    report = {"terms": len(spec["terms"]), "files_checked": checked, "hits": hits}
    (L / "analysis" / "source_terms_check.json").write_text(json.dumps(report, indent=1, ensure_ascii=False),
                                                            encoding="utf-8")
    for h in hits[:40]:
        print("FOUND", h)
    if hits:
        raise SystemExit(f"source-terms check failed: {len(hits)} hit(s) of {len(spec['terms'])} terms "
                         f"in {checked} files")
    print(f"source-terms check passed: none of {len(spec['terms'])} terms in {checked} files")


if __name__ == "__main__":
    main()
