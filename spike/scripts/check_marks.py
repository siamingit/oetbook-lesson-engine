"""Mark check: draw every board state with all its marks, at phone-landscape
and laptop width, in a real browser, and measure.

    .venv/Scripts/python spike/scripts/check_marks.py <lesson_dir> --page 13

Reads:  <lesson_dir>/generated/page-<N>/boards/player.html (its bundle and CSS)
Writes: <lesson_dir>/generated/page-<N>/boards/marks_check.json

For every mark cue, at each width:
  overlap      FAIL if the mark's box touches a neighbouring word's box
  wrapped      reported if the mark breaks across lines (its fragments are
               each drawn complete by box-decoration-break: clone, but a
               wrapped circle still reads as two rings)
  not found    FAIL if the phrase could not be located in its block (for
               example a phrase that crosses a tense-tag boundary)

The harness is the player itself: it is loaded in headless Edge with a
script that walks every state, applies its marks exactly as playback would,
measures with getClientRects, and writes the result into the document, which
is then read back with --dump-dom. No screenshot is interpreted; every figure
is geometry the browser reports.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
WIDTHS = {"phone": 812, "laptop": 1120}

HARNESS = r"""
<script>
(function () {
  window.__lockWidth = __WIDTH__;
  fit();
  const out = [];
  function rectsTouch(a, b) {
    return !(a.right <= b.left || b.right <= a.left || a.bottom <= b.top || b.bottom <= a.top);
  }
  function neighbourRects(span) {
    // The word before and the word after the mark, as ranges in the same block.
    const rects = [];
    for (const dir of ["prev", "next"]) {
      let node = dir === "prev" ? span.previousSibling : span.nextSibling;
      while (node && node.nodeType !== 3) node = dir === "prev" ? node.previousSibling : node.nextSibling;
      if (!node) continue;
      const text = node.data;
      const m = dir === "prev" ? text.match(/(\S+)\s*$/) : text.match(/^\s*(\S+)/);
      if (!m) continue;
      const start = dir === "prev" ? m.index : m.index + m[0].length - m[1].length;
      const r = document.createRange();
      r.setStart(node, start); r.setEnd(node, start + m[1].length);
      for (const rr of r.getClientRects()) rects.push(rr);
    }
    return rects;
  }
  for (const bd of boards) for (const s of bd.states) {
    drawBoard(bd, s, false);
    for (const id of s.working) { const el = blockEls.get(id); if (el) el.classList.add("on"); }
    for (const [id, el] of blockEls) el.style.transition = "none";
    // Apply every mark of the state at once, as at the end of the state.
    drawnMarks = "";
    applyMarks(s, 1e9, false);
    const marks = marksByState.get(s.id);
    const spans = [...boardEl.querySelectorAll(".mk")];
    let k = 0;
    for (const c of marks) {
      const want = c.type === "arrow" ? 2 : 1;
      for (let j = 0; j < want; j++) {
        const span = spans[k++];
        const rec = { state: s.id, cue: c.id, type: c.type, block: c.block, text: j ? c.to_text : c.text };
        if (!span) { rec.found = false; out.push(rec); continue; }
        rec.found = true;
        const frags = [...span.getClientRects()];
        rec.fragments = frags.length;
        const box = span.getBoundingClientRect();
        const cs = getComputedStyle(span);
        rec.overlap = neighbourRects(span).some(n => frags.some(f => rectsTouch(f, n)));
        rec.width = Math.round(box.width);
        out.push(rec);
      }
    }
  }
  const pre = document.createElement("pre");
  pre.id = "marks-result";
  pre.textContent = JSON.stringify({ width: window.innerWidth, frame: Math.round(frame.getBoundingClientRect().width), marks: out });
  document.body.appendChild(pre);
})();
</script>
"""


def run(player: Path, width: int) -> dict:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the mark check needs a browser")
    harness = player.with_name("player_marks.html")
    html = player.read_text(encoding="utf-8")
    harness.write_text(html.replace("</body>", HARNESS.replace("__WIDTH__", str(width)) + "</body>"),
                       encoding="utf-8")
    r = subprocess.run([edge, "--headless=new", "--disable-gpu", f"--window-size={width + 200},{int(width * 0.75)}",
                        "--virtual-time-budget=4000", "--dump-dom",
                        harness.resolve().as_uri()], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="marks-result">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("the harness produced no result; the player did not run")
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")
                      .replace("&lt;", "<").replace("&gt;", ">"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int)
    parser.add_argument("--dir", type=Path, help="a built player folder, e.g. generated/lesson-player")
    args = parser.parse_args()
    out_dir = args.dir or paths.boards_dir(args.lesson_dir, args.page)
    player = out_dir / "player.html"

    report = {}
    failures = []
    wrapped = []
    for name, width in WIDTHS.items():
        res = run(player, width)
        report[name] = res
        for m in res["marks"]:
            where = f"{m['state']}/{m['cue']} {m['type']} {m['text']!r} at {name}"
            if not m["found"]:
                failures.append(f"{where}: phrase not found in block {m['block']}")
            elif m["overlap"]:
                failures.append(f"{where}: touches a neighbouring word")
            elif m["fragments"] > 1:
                wrapped.append(f"{where}: breaks across {m['fragments']} lines")
        print(f"{name} ({res['frame']}px frame): {len(res['marks'])} mark fragments checked")

    report["failures"] = failures
    report["wrapped"] = wrapped
    (out_dir / "marks_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    for w in wrapped:
        print("WRAPPED: " + w)
    for f in failures:
        print("FAIL: " + f)
    if failures:
        raise SystemExit(f"{len(failures)} mark problem(s)")
    print(f"mark check passed; {len(wrapped)} mark(s) wrap across lines")


if __name__ == "__main__":
    main()
