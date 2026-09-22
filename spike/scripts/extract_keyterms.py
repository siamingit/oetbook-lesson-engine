"""Extract English keyterm candidates from a lesson's slide PDF text layer.

Usage: python extract_keyterms.py <lesson_dir> [limit]

Reads  <lesson_dir>/source/slides.pdf  (never modified)
Writes <lesson_dir>/analysis/keyterms_candidates.json

The PDF text layer is mixed Persian/English. Persian script and bidi control
characters are stripped, leaving Latin text. Candidates are contiguous runs of
content words (stopwords and tokens shorter than 3 characters break a run),
capped at the Scribe v2 keyterm limits of 5 words and 50 characters.

This produces *candidates only*. A human then writes the approved list into
analysis/keyterms_curated.txt, which build_keyterms.py turns into the
keyterms.json that is actually sent -- slide text contains typos, and a
misspelled keyterm biases the ASR toward the wrong spelling.
"""

import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RULE = "v1: latin-only, stopwords dropped, content runs of 1-5 words, <=50 chars"

MAX_WORDS = 5
MAX_CHARS = 50
MIN_TOKEN_LEN = 3

STOPWORDS = {
    "the", "and", "for", "but", "not", "you", "your", "yours", "our", "ours",
    "his", "her", "hers", "its", "their", "theirs", "them", "they", "she",
    "him", "who", "whom", "whose", "which", "that", "this", "these", "those",
    "there", "here", "when", "where", "what", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "than",
    "too", "very", "can", "will", "just", "should", "would", "could", "may",
    "might", "must", "shall", "have", "has", "had", "having", "been", "being",
    "was", "were", "are", "is", "am", "be", "did", "does", "doing", "done",
    "with", "without", "from", "into", "onto", "upon", "over", "under",
    "again", "further", "then", "once", "about", "against", "between",
    "through", "during", "before", "after", "above", "below", "out", "off",
    "down", "because", "while", "until", "also", "yet", "still", "however",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "now", "new", "old", "own", "same", "see", "use", "used", "using",
    "make", "makes", "made", "let", "lets", "get", "gets", "got", "put",
    "example", "examples", "note", "notes", "page", "slide", "slides",
}

BIDI = "".join(chr(c) for c in
               [0x061C, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D,
                0x202E, 0x2066, 0x2067, 0x2068, 0x2069, 0x200B, 0x200C, 0x200D])
NON_LATIN = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]+")
TOKEN = re.compile(r"[A-Za-z][A-Za-z'’-]*")


def pdf_text(pdf: Path) -> str:
    out = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    return out.stdout


def latin_segments(text: str) -> list[str]:
    text = text.translate({ord(c): " " for c in BIDI})
    text = NON_LATIN.sub(" | ", text)
    text = re.sub(r"[^A-Za-z'’\-\s]+", " | ", text)
    return [seg for seg in re.split(r"[|\n]", text) if seg.strip()]


def is_content(token: str) -> bool:
    return len(token) >= MIN_TOKEN_LEN and token.lower() not in STOPWORDS


def candidates(segments: list[str]) -> tuple[Counter, dict[str, Counter]]:
    counts: Counter = Counter()
    casings: dict[str, Counter] = {}

    def record(words: list[str]) -> None:
        phrase = " ".join(words)
        if len(phrase) > MAX_CHARS:
            return
        key = phrase.lower()
        counts[key] += 1
        casings.setdefault(key, Counter())[phrase] += 1

    for seg in segments:
        run: list[str] = []
        for token in TOKEN.findall(seg) + [None]:
            if token is not None and is_content(token):
                run.append(token)
                continue
            if run:
                for word in run:
                    record([word])
                if 2 <= len(run) <= MAX_WORDS:
                    record(run)
                run = []
    return counts, casings


def main() -> None:
    lesson = Path(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    pdf = lesson / "source" / "slides.pdf"
    analysis = lesson / "analysis"
    analysis.mkdir(exist_ok=True)

    counts, casings = candidates(latin_segments(pdf_text(pdf)))

    ranked = sorted(
        counts.items(),
        key=lambda kv: (-(kv[0].count(" ") > 0), -kv[1], kv[0]),
    )
    selected = ranked[:limit]

    def surface(key: str) -> str:
        return casings[key].most_common(1)[0][0]

    payload = {
        "source_pdf": str(pdf),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rule": RULE,
        "candidate_count": len(counts),
        "limit": limit,
        "reviewed": False,
        "keyterms": [surface(k) for k, _ in selected],
        "frequencies": {surface(k): n for k, n in selected},
    }

    dst = analysis / "keyterms_candidates.json"
    dst.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{dst}  ({len(payload['keyterms'])} of {len(counts)} candidates)")


if __name__ == "__main__":
    main()
