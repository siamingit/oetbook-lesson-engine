"""Inject a page's board bundle into the board player template.

build_player.py adapted to the board model. The bundle is embedded as a JS
constant so the page works when opened from disk; audio stays as separate
files, which <audio src> may load over file://. The frame CSS is injected from
write_screens.py so the player, the screens preview and the narration preview
draw a block identically.

    .venv/Scripts/python spike/scripts/build_board_player.py <lesson_dir> --page 13

Reads:  <lesson_dir>/generated/page-<N>/boards/bundle.json
        spike/scripts/board_player_template.html
Writes: <lesson_dir>/generated/page-<N>/boards/player.html

Open the result in a browser. `player.html?t=95` opens it paused at 95
seconds, which is how the build screenshots a moment for review.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths                                   # noqa: E402
from write_screens import FRAME_CSS            # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    args = parser.parse_args()

    out_dir = paths.boards_dir(args.lesson_dir, args.page)
    bundle = json.loads((out_dir / "bundle.json").read_text(encoding="utf-8"))
    template = (REPO_ROOT / "spike" / "scripts" / "board_player_template.html"
                ).read_text(encoding="utf-8")

    title = f"Page {bundle['meta']['page']} - {bundle['meta']['lesson']}"
    html = (template.replace("__TITLE__", title)
            .replace("/*__FRAME_CSS__*/", FRAME_CSS)
            .replace("__BUNDLE_JSON__",
                     json.dumps(bundle, ensure_ascii=False).replace("</", "<\\/")))
    out_path = out_dir / "player.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
