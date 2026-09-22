"""Extract ASR-ready audio from a lesson video.

Usage: python extract_audio.py <lesson_dir>

Reads  <lesson_dir>/source/video.mp4  (never modified)
Writes <lesson_dir>/analysis/audio.mp3  mono / 16 kHz / 64 kbps
"""

import json
import subprocess
import sys
from pathlib import Path


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def main() -> None:
    lesson = Path(sys.argv[1])
    src = lesson / "source" / "video.mp4"
    analysis = lesson / "analysis"
    analysis.mkdir(exist_ok=True)
    dst = analysis / "audio.mp3"

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "libmp3lame", "-b:a", "64k", str(dst)],
        check=True,
    )

    print(json.dumps({
        "audio": str(dst),
        "source_duration_s": round(probe_duration(src), 3),
        "audio_duration_s": round(probe_duration(dst), 3),
        "audio_bytes": dst.stat().st_size,
    }, indent=2))


if __name__ == "__main__":
    main()
