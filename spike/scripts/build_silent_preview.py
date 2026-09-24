"""A SILENT preview player for the whole lesson: no audio and no Cartesia call,
on a timeline estimated from word counts.

    .venv/Scripts/python spike/scripts/build_silent_preview.py <lesson_dir> [--wpm 155]

The same as build_lesson_player.py --silent (one code path for both players);
kept under this name because the review notes and README refer to it.
Writes <lesson_dir>/generated/lesson-preview/silent/player.html.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_lesson_player import build   # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--wpm", type=float, default=149.5,
                    help="default 149.5: the lesson's measured pace at the chosen speed, 1.0")
    args = ap.parse_args()
    build(args.lesson_dir, silent=True, wpm=args.wpm)


if __name__ == "__main__":
    main()
