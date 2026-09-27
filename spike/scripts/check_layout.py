"""Layout-stability check: nothing about a board's state may move any text.

    .venv/Scripts/python spike/scripts/check_layout.py <lesson_dir> --dir <player folder>

Rule (docs/02-DESIGN-SYSTEM.md §8a, maintainer 2026-09-26): a spotlight, a
mark, a verdict or a typed answer never moves a word. For every board the
player is driven, in headless Edge, to every moment at which something on it
changes (each state, each cue and its end, each change of the spotlight, each
verdict), and the position of every word shown on the board is measured at
each (a block not yet revealed, or cleared, is not on the board). A word that is found at two positions on one board fails,
at phone-landscape or laptop width.

Positions are taken inside the board with the camera's transform undone (it is
a translate and a scale about the board's corner), so the camera, which zooms a
table board by design, is not counted as a move.
A word is the first character of each whitespace-separated token of the
block's text, found through the text nodes however marks or typing split them.

The harness is the player itself, as in check_marks.py: no screenshot is
interpreted; every figure is geometry the browser reports.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
WIDTHS = {"phone": 812, "laptop": 1120}
TOLERANCE_PX = 0.5

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
  // Every token's first character, in layout px inside the board: the block's
  // offset in #cam plus the character's place in the block, unscaled.
  function tokens(el) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const nodes = []; let text = "", node;
    while ((node = walker.nextNode())) { nodes.push([node, text.length]); text += node.data; }
    if (!el.getBoundingClientRect().width) return [];
    // the camera is translate + scale about (0, 0): undo it exactly
    const tf = getComputedStyle(camEl).transform;
    const sc = tf && tf !== "none" ? new DOMMatrix(tf).a : 1;
    const C = camEl.getBoundingClientRect();
    const out = [];
    const re = /\S+/g; let m, n = 0;
    while ((m = re.exec(text))) {
      if (!/[a-z0-9]/i.test(m[0])) continue;
      let i = 0; while (i + 1 < nodes.length && nodes[i + 1][1] <= m.index) i++;
      const [tn, start] = nodes[i];
      const r = document.createRange();
      r.setStart(tn, m.index - start); r.setEnd(tn, m.index - start + 1);
      const rr = r.getClientRects()[0];
      if (rr) out.push([n, m[0], (rr.left - C.left) / sc, (rr.top - C.top) / sc]);
      n++;
    }
    return out;
  }
  const moves = [];
  let samples = 0;
  for (const bd of boards) {
    const times = new Set([bd.start + 0.001]);
    for (const s of bd.states) {
      times.add(s.start + 0.001); times.add(s.end - 0.001);
      if (s.erase) times.add(s.erase.time - 0.001);
      for (const u of s.utterances) for (const c of u.cues) {
        times.add(c.time + 0.001);
        if (c.time_end) times.add(c.time_end + 0.001);
        if (c.type === "type") times.add((c.time + c.time_end) / 2);
      }
    }
    for (const f of bd.focus || []) times.add(f.time + 0.001);
    for (const v of bd.verdicts || []) times.add(v.time + 0.001);
    for (const w of bd.wordmarks || []) times.add(w.time + 0.001);
    const seen = new Map();   // "block|n" -> [x, y, t, word]
    const moved = new Set();
    for (const t of [...times].filter(t => t >= bd.start && t < bd.until).sort((a, b) => a - b)) {
      lastRenderT = null;
      renderFrame(t);
      samples++;
      for (const [id, el] of blockEls) {
        // a word counts once it is on the board: a block shown, not one
        // waiting for its reveal, cleared, or pinned in a later state
        if (!el.isConnected || getComputedStyle(el).display === "none") continue;
        if (!(el.dataset.layer === "fixed" || el.classList.contains("on"))) continue;
        for (const [n, word, x, y] of tokens(el)) {
          const key = id + "|" + n;
          const was = seen.get(key);
          if (!was) { seen.set(key, [x, y, t, word]); continue; }
          if ((Math.abs(was[0] - x) > TOL || Math.abs(was[1] - y) > TOL) && !moved.has(key)) {
            moved.add(key);
            moves.push({ board: bd.id, block: id, n, word, t0: was[2], t1: t,
                         dx: +(x - was[0]).toFixed(1), dy: +(y - was[1]).toFixed(1),
                         state: (stateAt(bd, t) || {}).id || null });
          }
        }
      }
    }
  }
  const pre = document.createElement("pre");
  pre.id = "layout-result";
  pre.textContent = JSON.stringify({ width: window.innerWidth, frame: Math.round(frame.getBoundingClientRect().width),
                                     samples, moves });
  document.body.appendChild(pre);
})();
</script>
"""


def run(player: Path, width: int) -> dict:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the layout check needs a browser")
    harness = player.with_name("player_layout.html")
    html = player.read_text(encoding="utf-8")
    script = HARNESS.replace("__WIDTH__", str(width)).replace("__TOL__", str(TOLERANCE_PX))
    harness.write_text(html.replace("</body>", script + "</body>"), encoding="utf-8")
    r = subprocess.run([edge, "--headless=new", "--disable-gpu", f"--window-size={width + 200},{int(width * 0.75)}",
                        "--virtual-time-budget=60000", "--dump-dom", harness.resolve().as_uri()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="layout-result">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("the harness produced no result; the player did not run")
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")
                      .replace("&lt;", "<").replace("&gt;", ">"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--dir", type=Path, required=True, help="a built player folder, e.g. generated/lesson-player")
    ap.add_argument("--show", type=int, default=12, help="moves to print per width")
    a = ap.parse_args()
    report, failures = {}, 0
    for name, width in WIDTHS.items():
        res = run(a.dir / "player.html", width)
        report[name] = res
        moves = res["moves"]
        failures += len(moves)
        boards = sorted({m["board"] for m in moves})
        print(f"{name} ({res['frame']}px frame): {res['samples']} moments measured; "
              f"{len(moves)} word(s) moved on {len(boards)} board(s)")
        for m in moves[:a.show]:
            print(f"  MOVED {m['board']} {m['block']} word {m['n']} {m['word']!r}: "
                  f"{m['dx']:+}px, {m['dy']:+}px between {m['t0']:.2f}s and {m['t1']:.2f}s ({m['state']})")
    (a.dir / "layout_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if failures:
        raise SystemExit(f"layout check failed: {failures} word move(s); see {a.dir / 'layout_check.json'}")
    print("layout check passed: no word moves between states")


if __name__ == "__main__":
    main()
