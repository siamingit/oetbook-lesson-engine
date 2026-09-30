"""Overlap check: no block overlaps another block or its text, in any state.

    .venv/Scripts/python spike/scripts/check_overlap.py <lesson_dir> --dir <player folder>

Rule (maintainer, 2026-09-30; docs/adr/020-no-overlap.md), after Grammar 8
showed a timeline drawn over a table's text and a timeline whose labels were
drawn over each other: in every state, at phone-landscape and laptop width,

  - no two blocks shown at the same moment overlap (their boxes intersect by
    more than the tolerance in both directions), and
  - inside a block, no piece of text is drawn over another (a diagram's labels,
    a table cell's words): every line of every text is measured, and two lines
    from different texts that intersect fail.

The player is driven, in headless Edge, to every moment at which something on a
board appears or goes, as in check_overflow.py, with the camera's zoom undone.
No screenshot is interpreted: every figure is geometry the browser reports.
Marks are drawn in an overlay (design system §8a) and are not blocks; they are
not measured here.
"""

import argparse
import json
import re
import subprocess
import shutil
import atexit
import tempfile
from pathlib import Path

EDGE_PROFILE = tempfile.mkdtemp(prefix="oet-edge-")
atexit.register(shutil.rmtree, EDGE_PROFILE, True)

EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
WIDTHS = {"phone": 812, "laptop": 1120}
TOLERANCE_PX = 2.0

HARNESS = r"""
<script>
(function () {
  window.__lockWidth = __WIDTH__;
  fit();
  camEl.classList.remove("glide");
  const style = document.createElement("style");
  style.textContent = "*{transition:none!important;animation:none!important}";
  document.head.appendChild(style);
  const TOL = __TOL__;
  function shown(el) {
    if (!el.isConnected || getComputedStyle(el).display === "none") return false;
    return el.dataset.layer === "fixed" || el.classList.contains("on");
  }
  function visible(el) {
    for (let e = el; e && e !== document.body; e = e.parentElement) {
      const cs = getComputedStyle(e);
      if (cs.display === "none" || cs.visibility === "hidden" || parseFloat(cs.opacity) < 0.05) return false;
    }
    return true;
  }
  function cross(a, b) {
    const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    return (w > TOL && h > TOL) ? [w, h] : null;
  }
  // every line of every visible text inside a block: [text node index, rect]
  function textLines(el) {
    const out = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let n, k = 0;
    while ((n = walker.nextNode())) {
      if (!n.textContent.trim() || !visible(n.parentElement)) continue;
      const rg = document.createRange();
      rg.selectNodeContents(n);
      for (const r of rg.getClientRects()) if (r.width > 1 && r.height > 1) out.push([k, r, n.textContent.trim().slice(0, 40)]);
      k++;
    }
    return out;
  }
  const blocksOut = [], textOut = [];
  const seenB = new Set(), seenT = new Set();
  let samples = 0;
  for (const bd of boards) {
    const times = new Set([bd.start + 0.001]);
    for (const s of bd.states) {
      times.add(s.start + 0.001); times.add(s.end - 0.001);
      if (s.erase) times.add(s.erase.time - 0.001);
      for (const t of Object.values(s.reveal || {})) times.add(t + 0.001);
    }
    for (const t of Object.values(bd.reveal || {})) times.add(t + 0.001);
    for (const t of Object.values(bd.pinned || {})) times.add(t + 0.001);
    for (const t of [...times].filter(t => t >= bd.start && t < bd.until).sort((a, b) => a - b)) {
      lastRenderT = null;
      renderFrame(t);
      samples++;
      const keep = camEl.style.transform;
      camEl.style.transform = "none";
      const els = [...blockEls].filter(([, el]) => shown(el) && visible(el));
      const rects = els.map(([id, el]) => [id, el, el.getBoundingClientRect()]);
      for (let i = 0; i < rects.length; i++) {
        for (let j = i + 1; j < rects.length; j++) {
          const [a, ea, ra] = rects[i], [b, eb, rb] = rects[j];
          if (ea.contains(eb) || eb.contains(ea)) continue;
          const c = cross(ra, rb);
          const key = bd.id + "|" + [a, b].sort().join("|");
          if (c && !seenB.has(key)) {
            seenB.add(key);
            blocksOut.push({ board: bd.id, a, b, t, state: (stateAt(bd, t) || {}).id || null,
                             w: +c[0].toFixed(1), h: +c[1].toFixed(1) });
          }
        }
      }
      for (const [id, el] of els) {
        const lines = textLines(el).sort((p, q) => p[1].top - q[1].top);
        for (let i = 0; i < lines.length; i++) {
          for (let j = i + 1; j < lines.length && lines[j][1].top < lines[i][1].bottom; j++) {
            if (lines[i][0] === lines[j][0]) continue;
            const c = cross(lines[i][1], lines[j][1]);
            // two lines of text overlap only when they share most of a line's
            // height: adjacent lines touch in their leading, which is not overlap
            if (!c || c[1] < 0.4 * Math.min(lines[i][1].height, lines[j][1].height)) continue;
            const key = bd.id + "|" + id + "|" + lines[i][2] + "|" + lines[j][2];
            if (!seenT.has(key)) {
              seenT.add(key);
              textOut.push({ board: bd.id, block: id, t, state: (stateAt(bd, t) || {}).id || null,
                             texts: [lines[i][2], lines[j][2]], w: +c[0].toFixed(1), h: +c[1].toFixed(1) });
            }
          }
        }
      }
      camEl.style.transform = keep;
    }
  }
  const pre = document.createElement("pre");
  pre.id = "overlap-result";
  pre.textContent = JSON.stringify({ width: window.innerWidth, frame: Math.round(frame.getBoundingClientRect().width),
                                     samples, blocks: blocksOut, text: textOut });
  document.body.appendChild(pre);
})();
</script>
"""


def run(player: Path, width: int) -> dict:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the overlap check needs a browser")
    harness = player.with_name("player_overlap.html")
    html = player.read_text(encoding="utf-8")
    script = HARNESS.replace("__WIDTH__", str(width)).replace("__TOL__", str(TOLERANCE_PX))
    harness.write_text(html.replace("</body>", script + "</body>"), encoding="utf-8")
    r = subprocess.run([edge, "--headless=new", "--user-data-dir=" + EDGE_PROFILE, "--disable-gpu",
                        f"--window-size={width + 200},{int(width * 0.75)}",
                        "--virtual-time-budget=60000", "--dump-dom", harness.resolve().as_uri()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="overlap-result">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("the harness produced no result; the player did not run")
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")
                      .replace("&lt;", "<").replace("&gt;", ">"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--dir", type=Path, required=True, help="a built player folder, e.g. generated/lesson-player")
    ap.add_argument("--show", type=int, default=20, help="findings to print per width")
    a = ap.parse_args()
    report, failures = {}, 0
    mmss = lambda t: f"{int(t // 60)}:{int(t % 60):02d}"
    for name, width in WIDTHS.items():
        res = run(a.dir / "player.html", width)
        report[name] = res
        failures += len(res["blocks"]) + len(res["text"])
        print(f"{name} ({res['frame']}px frame): {res['samples']} moments measured; "
              f"{len(res['blocks'])} block overlap(s), {len(res['text'])} text overlap(s)")
        for o in res["blocks"][:a.show]:
            print(f"  BLOCKS {o['a']} and {o['b']} at {mmss(o['t'])} ({o['state']}): "
                  f"{o['w']} x {o['h']} px")
        for o in res["text"][:a.show]:
            print(f"  TEXT in {o['block']} at {mmss(o['t'])} ({o['state']}): {o['texts'][0]!r} over "
                  f"{o['texts'][1]!r}, {o['w']} x {o['h']} px")
    (a.dir / "overlap_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if failures:
        raise SystemExit(f"overlap check failed: {failures} finding(s); see {a.dir / 'overlap_check.json'}")
    print("overlap check passed: no block over another block or its text, no text over text")


if __name__ == "__main__":
    main()
