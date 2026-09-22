"""Build the Scribe keyterm list from a hand-curated term file.

Usage: python build_keyterms.py <lesson_dir>

Reads  <lesson_dir>/analysis/keyterms_curated.txt   the approved list, edited by a human
       <lesson_dir>/source/slides.pdf               to verify each term
Writes <lesson_dir>/analysis/keyterms.json          what transcribe.py sends

Curation stays human (docs/01-METHODOLOGY.md §12) — this script only verifies
and records provenance, it never invents or drops a term.

Format of keyterms_curated.txt, one term per line:

    # lines starting with # are comments
    past participle
    time markers      # corrected: slides read "Time Makers"
    osteoarthritis    # image-verified: timeline slide, pasted image, no text layer

Provenance is assigned from the note, or from the PDF text layer when there is
no note:

    corrected:        -> corrected
    image-verified:   -> source-derived (slide image, visually verified)
    found in text     -> source-derived
    not found         -> authored
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Scribe v2 keyterm limits
MAX_TERMS = 1000
MAX_CHARS = 50
MAX_WORDS = 5
FORBIDDEN = set("<>{}[]\\")

BIDI = "".join(chr(c) for c in
               [0x061C, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D,
                0x202E, 0x2066, 0x2067, 0x2068, 0x2069, 0x200B, 0x200C, 0x200D])
NON_LATIN = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]+")


def haystacks(pdf: Path) -> tuple[str, str]:
    raw = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
                         check=True, capture_output=True, text=True,
                         encoding="utf-8").stdout
    raw = raw.translate({ord(c): " " for c in BIDI})
    full = re.sub(r"\s+", " ", raw).lower()
    latin = re.sub(r"\s+", " ", NON_LATIN.sub(" ", raw)).lower()
    return full, latin


def parse(path: Path) -> list[tuple[str, str]]:
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        term, _, note = line.partition("#")
        entries.append((term.strip(), note.strip()))
    return entries


def validate(terms: list[str]) -> None:
    problems = []
    if len(terms) > MAX_TERMS:
        problems.append(f"{len(terms)} terms exceeds the {MAX_TERMS} limit")
    for t in terms:
        if len(t) > MAX_CHARS:
            problems.append(f"{t!r} is {len(t)} characters (limit {MAX_CHARS})")
        if len(t.split()) > MAX_WORDS:
            problems.append(f"{t!r} is {len(t.split())} words (limit {MAX_WORDS})")
        if FORBIDDEN & set(t):
            problems.append(f"{t!r} contains an unsupported character")
    seen = {t.lower() for t in terms}
    if len(seen) != len(terms):
        problems.append("the list contains duplicates (case-insensitive)")
    if problems:
        raise SystemExit("keyterms_curated.txt is not sendable:\n  " + "\n  ".join(problems))


def main() -> None:
    lesson = Path(sys.argv[1])
    curated = lesson / "analysis" / "keyterms_curated.txt"
    pdf = lesson / "source" / "slides.pdf"
    dst = lesson / "analysis" / "keyterms.json"

    entries = parse(curated)
    validate([t for t, _ in entries])
    full, latin = haystacks(pdf)

    terms = []
    for term, note in entries:
        low = term.lower()
        found = "verbatim" if low in full else "verbatim-across-persian" if low in latin else "absent"

        entry = {"term": term, "in_pdf_text_layer": found}
        if note.lower().startswith("corrected:"):
            entry["provenance"] = "corrected"
            entry["note"] = note.split(":", 1)[1].strip()
        elif note.lower().startswith("image-verified:"):
            entry["provenance"] = "source-derived (slide image, visually verified)"
            entry["note"] = note.split(":", 1)[1].strip()
        else:
            entry["provenance"] = "source-derived" if found != "absent" else "authored"
            if note:
                entry["note"] = note
        terms.append(entry)

    payload = {
        "source_pdf": str(pdf),
        "curated_from": str(curated),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rule": ("terms approved by hand in keyterms_curated.txt; this file records "
                 "verification against the slides.pdf text layer and assigns provenance. "
                 "Absence from the text layer is not absence from the slides -- some "
                 "slides are pasted images (docs/01-METHODOLOGY.md §4)."),
        "keyterms": [e["term"] for e in terms],
        "terms": terms,
    }
    dst.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    counts: dict[str, int] = {}
    for e in terms:
        counts[e["provenance"]] = counts.get(e["provenance"], 0) + 1
    print(f"{dst}  ({len(terms)} keyterms)")
    for provenance, n in sorted(counts.items()):
        print(f"  {n:>3}  {provenance}")
    unverified = [e["term"] for e in terms if e["provenance"] == "authored"]
    if unverified:
        print(f"  not found in the PDF text layer and unannotated: {', '.join(unverified)}")


if __name__ == "__main__":
    main()
