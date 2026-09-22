"""Render a readable transcript from a raw Scribe v2 response.

Usage: python make_transcript.py <dir_with_response> [--offset SECONDS]

Reads  <dir>/scribe_v2_response.json
Writes <dir>/transcript.txt

Lines break on pauses between words. --offset shifts timestamps so an excerpt
reads in whole-lesson time rather than from zero.
"""

import json
import sys
from pathlib import Path

GAP = 0.7          # seconds of silence that starts a new line
MAX_WORDS = 25     # hard wrap so a monologue does not become one endless line


def clock(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def main() -> None:
    src_dir = Path(sys.argv[1])
    offset = float(sys.argv[sys.argv.index("--offset") + 1]) if "--offset" in sys.argv else 0.0
    data = json.loads((src_dir / "scribe_v2_response.json").read_text(encoding="utf-8"))

    lines: list[tuple[float, list[str]]] = []
    start = None
    buf: list[str] = []
    prev_end = None

    for w in data["words"]:
        if w.get("type") != "word":
            continue
        if start is None:
            start = w["start"]
        elif (w["start"] - prev_end > GAP) or len(buf) >= MAX_WORDS:
            lines.append((start, buf))
            start, buf = w["start"], []
        buf.append(w["text"])
        prev_end = w["end"]
    if buf:
        lines.append((start, buf))

    header = [
        f"language: {data.get('language_code')} "
        f"(confidence {data.get('language_probability', 0):.3f})",
        f"audio duration: {data.get('audio_duration_secs')} s",
        f"words: {sum(1 for w in data['words'] if w.get('type') == 'word')}",
        f"transcription id: {data.get('transcription_id')}",
    ]
    if offset:
        header.append(f"timestamps offset by {clock(offset)} (excerpt of a longer lesson)")

    body = "\n".join(f"[{clock(s + offset)}]  {' '.join(words)}" for s, words in lines)
    dst = src_dir / "transcript.txt"
    dst.write_text("\n".join(header) + "\n\n" + body + "\n", encoding="utf-8")
    print(f"{dst}  ({len(lines)} lines)")


if __name__ == "__main__":
    main()
