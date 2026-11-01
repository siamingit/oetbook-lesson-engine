"""Site-player check: the lesson's package played by the SITE's own lesson player, not the engine's reference player.

    .venv/Scripts/python spike/scripts/check_site_player.py <lesson_dir> [--package DIR] [--clone PATH] [--ref main]
        [--boards] [--width 1600]

Why (the owner, 2026-11-01, after Word Order draft.4): the site plays a lesson with its own player
(siamingit/oetacademy-web, packages/lesson-player). Its server cuts and sanitises each section and puts the lesson's
blocks.css inside `.oa-lesson` in the cascade layer `oa-lesson`, below the player's own rules, which therefore win
over any lesson rule on the same property whatever its specificity; its guard measures a board while it enters and
treats a block whose words lie outside it ("spills") as a board that never fits. Draft.4 passed every check on the
engine's player and drew tables a quarter of their size on the site. This check is required for every lesson
(docs/03-RUNBOOK.md, step 17b).

What it does, all locally and read-only towards the site: exports the site's code at `--ref` from a local clone
(`git archive`, after `git fetch`), installs its locked dependencies there (pnpm, once per commit), copies the harness
in spike/site_player/ into it, prepares the package exactly as the site's server prepares a draft (cutSection,
scopeLessonStylesheet), bundles the site's LessonPlayer with esbuild, serves it on 127.0.0.1 and drives it in headless
Edge to every state's fullest moment (`--boards`: each board's fullest state only). At each it records the site
guard's verdict (data-oa-fit, data-oa-whole and why), measures every line of text as check_text_size.py does (26 px
running, 20 px labels in the 1600x900 frame, a hand line at its size / 1.3; contrast 4.5:1) and takes a screenshot.
Fails on: any block that spills; any board the site's guard draws smaller than its own size; any text under its
minimum or under 4.5:1. Writes <lesson>/generated/site-player/ (site_player_check.json and one PNG per moment).
"""

import argparse
import functools
import http.server
import json
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
HARNESS = REPO / "spike" / "site_player"
WORK = REPO / "spike" / "out" / "site-player"
RULES = {"run": 26.0, "label": 20.0, "contrast": 4.5, "hand": 1.3, "words": 4, "tol": 0.25}
NODE = shutil.which("node") or "node"
PNPM = shutil.which("pnpm") or "pnpm"
GIT = shutil.which("git") or "git"


def sh(cmd, cwd=None, timeout=1800) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode:
        raise SystemExit(f"FAILED: {' '.join(map(str, cmd))}\n{(r.stdout + r.stderr)[-3000:]}")
    return r.stdout


def fingerprint(pkg: Path) -> str:
    """The package as the site's player draws it: its bundle and its stylesheet, byte for byte (publish_lesson.py
    --release checks a passing report against the package it sends)."""
    import hashlib
    h = hashlib.sha256()
    for name in ("bundle.json", "blocks.css"):
        h.update((pkg / name).read_bytes())
    return h.hexdigest()


def site_code(clone: Path, ref: str) -> tuple[Path, str]:
    """The site's code at `ref`, exported from the local clone once per commit, its dependencies installed."""
    sh([GIT, "fetch", "-q", "origin", ref], cwd=clone)
    commit = sh([GIT, "rev-parse", "--short", "FETCH_HEAD"], cwd=clone).strip()
    web = WORK / f"web-{commit}"
    if not (web / "node_modules").exists():
        if web.exists():
            shutil.rmtree(web)
        web.mkdir(parents=True)
        archive = WORK / f"web-{commit}.tar"
        sh([GIT, "archive", "-o", str(archive), "FETCH_HEAD"], cwd=clone)
        import tarfile
        with tarfile.open(archive) as tf:
            tf.extractall(web, filter="data")
        archive.unlink()
        sh([PNPM, "install", "--frozen-lockfile", "--ignore-scripts"], cwd=web, timeout=3600)
    return web, commit


def esbuild(web: Path) -> Path:
    found = sorted((web / "node_modules" / ".pnpm").glob("esbuild@*/node_modules/esbuild/bin/esbuild"))
    if not found:
        raise SystemExit("esbuild is not among the site's installed packages")
    return found[-1]


def moments(bundle: dict, boards_only: bool) -> list[dict]:
    out = []
    for i, bd in enumerate(bundle["boards"], 1):
        best = None
        for si, s in enumerate(bd["states"], 1):
            t = round(max(s["start"] + 0.2, min(s["end"], s.get("until", s["end"])) - 0.3), 2)
            m = {"t": t, "name": f"b{i:02d}-s{si:02d}", "board": bd["id"]}
            n = len(s.get("working") or []) + len(bd.get("fixed") or [])
            if not boards_only:
                out.append(m)
            if best is None or n >= best[0]:
                best = (n, m)
        if boards_only:
            out.append({**best[1], "name": f"board-{i:02d}"})
    return out


def serve(root: Path) -> tuple[http.server.ThreadingHTTPServer, int]:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        """Quiet, and with byte ranges for the clips (a media request without them is held open, and a long
        session runs out of connections: the player then waits on "Loading" for its next section)."""
        def log_message(self, *args):
            pass

        def send_head(self):
            rng = self.headers.get("Range")
            path = Path(self.translate_path(self.path))
            if not rng or not path.is_file():
                return super().send_head()
            size = path.stat().st_size
            a, _, b = rng.replace("bytes=", "").partition("-")
            start = int(a or 0)
            end = min(int(b) if b else size - 1, size - 1)
            f = open(path, "rb")
            f.seek(start)
            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(str(path)))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(end - start + 1))
            self.end_headers()
            self._left = end - start + 1
            return f

        def copyfile(self, source, outputfile):
            left = getattr(self, "_left", None)
            if left is None:
                return super().copyfile(source, outputfile)
            outputfile.write(source.read(left))
    handler = functools.partial(Quiet, directory=str(root))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--package", type=Path, help="the package folder (default: the lesson's draft package)")
    ap.add_argument("--clone", type=Path, default=Path(r"C:\Users\siava\projects\oetacademy-web-c1130"),
                    help="a local clone of siamingit/oetacademy-web (only fetched and archived)")
    ap.add_argument("--ref", default="main")
    ap.add_argument("--boards", action="store_true", help="each board's fullest state only")
    ap.add_argument("--width", type=int, default=1600)
    a = ap.parse_args()
    L = a.lesson_dir
    # the lesson's newest draft package: the highest version (a lesson with a released v1 has a v1-draft beside its
    # v2-draft, and "v1" sorts first)
    drafts = sorted((L / "generated" / "package").glob("*-draft"),
                    key=lambda p: int((re.search(r"-v(\d+)-draft$", p.name) or [0, 0])[1]))
    pkg = a.package or (drafts[-1] if drafts else None)
    if not pkg or not (pkg / "bundle.json").exists():
        raise SystemExit("no package: build it first (publish_lesson.py --package --draft)")
    web, commit = site_code(a.clone, a.ref)
    h = web / "apps" / "web" / "harness"
    if h.exists():
        shutil.rmtree(h)
    shutil.copytree(HARNESS, h)
    sys.path.insert(0, str(HERE))
    import style_c
    (h / "fonts.css").write_text(style_c.font_css(None), encoding="utf-8")
    print(sh([NODE, "prep.ts", str(pkg), "out"], cwd=h).strip().splitlines()[-1])
    sh([NODE, str(esbuild(web)), "entry.tsx", "--bundle", "--outfile=out/app.js", "--loader:.css=css", "--jsx=automatic",
        "--format=esm", "--define:process.env.NODE_ENV=\"production\""], cwd=h)
    if (pkg / "audio").exists():
        shutil.copytree(pkg / "audio", h / "pkg" / "audio")
    bundle = json.loads((pkg / "bundle.json").read_text(encoding="utf-8"))
    ms = moments(bundle, a.boards)
    out = L / "generated" / "site-player"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "moments.json").write_text(json.dumps(ms), encoding="utf-8")
    httpd, port = serve(h)
    try:
        r = subprocess.run([NODE, str(HARNESS / "probe.mjs"), f"http://127.0.0.1:{port}/index.html", str(out / "moments.json"),
                            str(a.width), str(out), json.dumps(RULES)], text=True, encoding="utf-8", errors="replace",
                           timeout=7200)
    finally:
        httpd.shutdown()
    if r.returncode:
        raise SystemExit("the site player's probe failed")
    res = json.loads((out / "probe.json").read_text(encoding="utf-8"))
    fails = []
    for m in res:
        if m.get("loading"):
            fails.append(f"{m['name']} {m['board']}: the site's player still shows Loading: nothing was measured")
        if "spills" in (m.get("why") or ""):
            fails.append(f"{m['name']} {m['board']}: a block spills ({m['why']}), so the site's guard never fits the board")
        if m.get("fit"):
            fails.append(f"{m['name']} {m['board']}: the site's guard draws the board smaller ({m['fit']}; {m.get('why')})")
        for f in m["found"]:
            fails.append(f"{m['name']} {m['board']}: {f['kind']} {f['value']} in {f['block']}: {f['text']!r}")
    report = {"site_commit": commit, "package": str(pkg), "package_fingerprint": fingerprint(pkg), "width": a.width,
              "moments": len(res), "every_state": not a.boards, "failures": fails, "rules": RULES}
    (out / "site_player_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"site player (oetacademy-web {commit}) at {a.width}px: {len(res)} moment(s), {len(fails)} failure(s)")
    for f in fails[:40]:
        print("  " + f)
    if fails:
        raise SystemExit(f"site-player check failed: {len(fails)} finding(s); see {out / 'site_player_check.json'}")
    print("site-player check passed: every board drawn at its own size on the site's player, no block spills, every "
          "text at its minimum or larger and at 4.5:1 or more")


if __name__ == "__main__":
    main()
