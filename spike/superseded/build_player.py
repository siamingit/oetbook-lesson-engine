"""Inject a page's bundle.json into the player template.

The bundle is embedded as a JS constant (not fetched) so the page works when
opened directly from disk -- file:// fetch() of a sibling JSON file is
blocked by same-origin rules in some browsers, but <audio src> and <img src>
are not, so audio and the slide image stay separate files.

    .venv/Scripts/python spike/scripts/build_player.py <lesson_dir>

Reads:  <lesson_dir>/generated/page-<N>/bundle.json
        spike/scripts/player_template.html
Writes: <lesson_dir>/generated/page-<N>/player.html
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    args = parser.parse_args()

    out_dir = paths.generated_dir(args.lesson_dir, args.page)
    if not out_dir.exists():
        raise SystemExit(f"nothing built for page {args.page}: {out_dir} missing")

    bundle = json.loads((out_dir / "bundle.json").read_text(encoding="utf-8"))
    template = (REPO_ROOT / "spike" / "scripts" / "player_template.html").read_text(encoding="utf-8")

    title = f"Page {bundle['meta']['page']} – {bundle['meta']['lesson']}"
    html = template.replace("__TITLE__", title)
    bundle_js = json.dumps(bundle, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("__BUNDLE_JSON__", bundle_js)

    out_path = out_dir / "player.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
