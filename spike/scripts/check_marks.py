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
import shutil
import atexit
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

# Headless Edge runs with its own profile, removed on exit: with the default one,
# a run could be handed to an Edge window already open and never return
# (the layout check's 900 s time-outs on Grammar 6, 2026-09-27).
EDGE_PROFILE = tempfile.mkdtemp(prefix="oet-edge-")
atexit.register(shutil.rmtree, EDGE_PROFILE, True)

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
    // Only a neighbour on the same line can touch: a fragment of a wrapped mark
    // and the last word of the line above share a strip of their glyph boxes
    // when the line height is tight (table cells, 1.3), without touching.
    const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (overlapY < 0.5 * Math.min(a.height, b.height)) return false;
    return !(a.right <= b.left || b.right <= a.left);
  }
  function neighbourRects(pieces) {
    // The nearest letters or digits before and after the mark's phrase, walking
    // the block's text as the player does: punctuation beside a phrase is not a
    // neighbouring word, and a neighbour inside another wrapper is still found.
    const root = pieces[0].closest(".blk") || pieces[0].parentElement;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let prev = null, next = null, seen = false, node;
    while ((node = walker.nextNode())) {
      if (pieces.some(p => p.contains(node))) { seen = true; continue; }
      if (!seen) { const m = node.data.match(/([A-Za-z0-9]+)[^A-Za-z0-9]*$/); if (m) prev = [node, m.index, m[1].length]; }
      else { const m = node.data.match(/^[^A-Za-z0-9]*([A-Za-z0-9]+)/);
             if (m) { next = [node, m.index + m[0].length - m[1].length, m[1].length]; break; } }
    }
    const rects = [];
    for (const x of [prev, next]) {
      if (!x) continue;
      const r = document.createRange();
      r.setStart(x[0], x[1]); r.setEnd(x[0], x[1] + x[2]);
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
    if (typeof positionMarks === "function") positionMarks();   // marks are drawn in the overlay
    const marks = marksByState.get(s.id);
    for (const c of marks) {
      const want = c.type === "arrow" ? 2 : 1;
      for (let j = 0; j < want; j++) {
        // each mark's wrapper, by its cue (every phrase is wrapped ahead of time)
        const w = WRAPS.get(c.type === "arrow" ? c._uid + (j ? ">" : "<") : c._uid);
        const span = w && w.first;
        const rec = { state: s.id, cue: c.id, type: c.type, block: c.block, text: j ? c.to_text : c.text };
        if (!span) { rec.found = false; out.push(rec); continue; }
        rec.found = true;
        const frags = w.spans.flatMap(p => [...p.getClientRects()]);
        rec.fragments = new Set(frags.map(f => Math.round(f.top))).size;   // lines, not pieces
        // a ring (drawn in the overlay since 2026-09-26) is measured as drawn;
        // a line or a tint is measured on its phrase, as before
        const shapes = c.type === "circle" && span.dataset.mk !== undefined
          ? [...document.querySelectorAll('#marks [data-mk="' + span.dataset.mk + '"]')] : [];
        const drawn = shapes.length ? shapes.map(e => e.getBoundingClientRect()) : frags;
        const box = span.getBoundingClientRect();
        const cs = getComputedStyle(span);
        rec.overlap = neighbourRects(w.spans).some(n => drawn.some(f => rectsTouch(f, n)));
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
    r = subprocess.run([edge, "--headless=new", "--user-data-dir=" + EDGE_PROFILE, "--disable-gpu", f"--window-size={width + 200},{int(width * 0.75)}",
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
