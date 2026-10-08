"""Lens check: no line of text inside a lens or zoom window is clipped, and a
Part B question board's extract is whole.

    .venv/Scripts/python spike/scripts/check_lens.py <lesson_dir> --dir <player folder>

Rule (maintainer, 2026-10-07): a lens shows complete lines. Its window is
  - a Part B text's lens (bundle 1.15, rule 35): the whole-line window the
    player sets (`data-lens-top`, `data-lens-bottom`, inside the text's frame);
    the faded cue bands above and below it are not part of the window;
  - the map of the four texts (bundle 1.14, rule 31): its view (`.dmap-view`).
For every board with one, the player is driven in headless Edge to every moment
at which something on the board changes (each state, each cue and its end, each
change of the spotlight), at phone-landscape and laptop width, and every line
of text in the window's element is measured: a line that lies partly inside the
window and partly outside it (above, below or to a side) fails. A line wholly
outside the window (hidden, or in a cue band) is not a finding.

A Part B question board in two columns (bundle 1.16, rule 36; maintainer,
2026-10-08) has no lens: its extract is shown whole. At every moment after the
text is uncovered, every line of the extract must lie inside its page and inside
the board; a line outside either, wholly or in part, fails. The extract's size
is reported per board, in px and as a share of the frame's height.

The harness is the player itself, as in check_layout.py: no screenshot is
interpreted; every figure is geometry the browser reports.
"""

import argparse
import atexit
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

EDGE_PROFILE = tempfile.mkdtemp(prefix="oet-edge-")
atexit.register(shutil.rmtree, EDGE_PROFILE, True)

EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
# the frame the reference player draws in a phone held landscape, 915x412 (its
# controls keep 44 px, 13% of this frame), then phone-landscape and laptop
# (maintainer, 2026-10-08: the board measured above the control bar at every width)
WIDTHS = {"small phone": 590, "phone": 812, "laptop": 1120}
TOLERANCE_PX = 1.0

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
  // a player built before bundle 1.16 has no Part B question board (and no isQBoard)
  const qb = bd => typeof isQBoard === "function" && isQBoard(bd);
  // the window of a lens element, in client px
  function windowOf(el) {
    const r = el.getBoundingClientRect();
    const map = el.classList.contains("dmap-view");
    const sc = el.offsetHeight ? r.height / el.offsetHeight : 1;
    // the window the player set: the map's zoom (2026-10-07) or a Part B lens
    const set = el.dataset.lensTop != null && (map || el.classList.contains("lensed"));
    const top = set ? +el.dataset.lensTop : 0;
    const bot = set ? +el.dataset.lensBottom : el.clientHeight;
    return { kind: map ? "map" : "text", top: r.top + (el.clientTop + top) * sc, bottom: r.top + (el.clientTop + bot) * sc,
             left: r.left + el.clientLeft * sc, right: r.left + (el.clientLeft + el.clientWidth) * sc };
  }
  function lines(el) {
    const out = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n; (n = walker.nextNode());) {
      if (!n.data.trim()) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      for (const q of rg.getClientRects()) if (q.width > 0 && q.height > 0) out.push([q, n.data.trim().slice(0, 50)]);
    }
    return out;
  }
  const clipped = [], seen = new Set(), whole = [];
  let samples = 0, windows = 0;
  const body = camEl.parentElement;
  // 1.16: the extract of a Part B question board, whole on its page and on the
  // board at every moment after it is uncovered
  for (const bd of boards) {
    if (!qb(bd)) continue;
    const shown = bd.states.find(s => !s.veil);
    if (!shown) continue;
    const times = new Set([shown.start + 0.001]);
    for (const s of bd.states) {
      if (s.veil) continue;
      times.add(s.start + 0.001); times.add(s.end - 0.001);
      for (const u of s.utterances) for (const c of u.cues) {
        times.add(c.time + 0.001);
        if (c.time_end) times.add(c.time_end + 0.001);
      }
      for (const c of s.clears || []) times.add(c.time + 0.001);
    }
    for (const f of bd.focus || []) times.add(f.time + 0.001);
    let font = null, out = 0, n = 0;
    for (const t of [...times].filter(t => t >= shown.start && t < bd.until).sort((a, b) => a - b)) {
      lastRenderT = null;
      renderFrame(t);
      samples++;
      const el = blockEls.get(bd.table);
      if (!el) continue;
      windows++;
      const P = el.getBoundingClientRect(), B = body.getBoundingClientRect(), cs = getComputedStyle(body);
      const W = { top: Math.max(P.top + el.clientTop, B.top + parseFloat(cs.paddingTop)),
                  bottom: Math.min(P.top + el.clientTop + el.clientHeight, B.bottom - parseFloat(cs.paddingBottom)),
                  left: Math.max(P.left + el.clientLeft, B.left + parseFloat(cs.paddingLeft)),
                  right: Math.min(P.left + el.clientLeft + el.clientWidth, B.right - parseFloat(cs.paddingRight)) };
      const td = el.querySelector("tbody td");
      font = td ? parseFloat(getComputedStyle(td).fontSize) : null;
      for (const [q, text] of lines(el)) {
        n++;
        const sides = [];
        if (q.top < W.top - TOL) sides.push("top");
        if (q.bottom > W.bottom + TOL) sides.push("bottom");
        if (q.left < W.left - TOL) sides.push("left");
        if (q.right > W.right + TOL) sides.push("right");
        if (!sides.length) continue;
        out++;
        const key = bd.id + "|" + text + "|" + sides.join(",");
        if (seen.has(key)) continue;
        seen.add(key);
        clipped.push({ board: bd.id, kind: "extract", t: +t.toFixed(3), state: (stateAt(bd, t) || {}).id || null,
                       text, sides, px: +Math.max(W.top - q.top, q.bottom - W.bottom, W.left - q.left, q.right - W.right).toFixed(1) });
      }
    }
    const fh = frame.clientHeight;          // cqh: a share of the frame's inner height
    const g = bd._guard || {};             // what the player's guard chose on this frame (1.16)
    whole.push({ board: bd.id, split: g.split ?? bd.split, zoom: g.zoom ?? 1, font_px: font, font_cqh: font ? +(font / fh * 100).toFixed(2) : null,
                 bundle_font: blocks[bd.table].font, lines_measured: n, lines_outside: out });
  }
  for (const bd of boards) {
    const tb = bd.table && blocks[bd.table];
    if (!tb || !(tb.map || bd.lens)) continue;
    const times = new Set([bd.start + 0.001]);
    if (bd.lens_from) times.add(bd.lens_from + 0.001);
    for (const s of bd.states) {
      times.add(s.start + 0.001); times.add(s.end - 0.001);
      for (const u of s.utterances) for (const c of u.cues) {
        times.add(c.time + 0.001);
        if (c.time_end) times.add(c.time_end + 0.001);
      }
    }
    for (const f of bd.focus || []) times.add(f.time + 0.001);
    for (const t of [...times].filter(t => t >= bd.start && t < bd.until).sort((a, b) => a - b)) {
      lastRenderT = null;
      renderFrame(t);
      samples++;
      const el = blockEls.get(bd.table);
      if (!el) continue;
      const lensEl = tb.map ? el.querySelector(".dmap-view") : el;
      if (!lensEl || !lensEl.getBoundingClientRect().height) continue;
      windows++;
      const W = windowOf(lensEl);
      for (const [q, text] of lines(lensEl)) {
        const vin = Math.min(q.bottom, W.bottom) - Math.max(q.top, W.top);
        const hin = Math.min(q.right, W.right) - Math.max(q.left, W.left);
        if (vin <= TOL || hin <= TOL) continue;                   // wholly outside: not shown
        const sides = [];
        if (q.top < W.top - TOL) sides.push("top");
        if (q.bottom > W.bottom + TOL) sides.push("bottom");
        if (q.left < W.left - TOL) sides.push("left");
        if (q.right > W.right + TOL) sides.push("right");
        if (!sides.length) continue;
        const key = bd.id + "|" + text + "|" + Math.round(q.top - W.top) + "|" + sides.join(",");
        if (seen.has(key)) continue;
        seen.add(key);
        clipped.push({ board: bd.id, kind: W.kind, t: +t.toFixed(3), state: (stateAt(bd, t) || {}).id || null,
                       text, sides, px: +Math.max(W.top - q.top, q.bottom - W.bottom, W.left - q.left, q.right - W.right).toFixed(1) });
      }
    }
  }
  const pre = document.createElement("pre");
  pre.id = "lens-result";
  pre.textContent = JSON.stringify({ width: window.innerWidth, frame: Math.round(frame.getBoundingClientRect().width),
                                     samples, windows, clipped, whole });
  document.body.appendChild(pre);
})();
</script>
"""


def run(player: Path, width: int) -> dict:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the lens check needs a browser")
    harness = player.with_name("player_lens.html")
    html = player.read_text(encoding="utf-8")
    script = HARNESS.replace("__WIDTH__", str(width)).replace("__TOL__", str(TOLERANCE_PX))
    harness.write_text(html.replace("</body>", script + "</body>"), encoding="utf-8")
    r = subprocess.run([edge, "--headless=new", "--user-data-dir=" + EDGE_PROFILE, "--disable-gpu",
                        f"--window-size={width + 200},{int(width * 0.75)}", "--mute-audio",
                        "--virtual-time-budget=60000", "--dump-dom", harness.resolve().as_uri()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="lens-result">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("the harness produced no result; the player did not run")
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")
                      .replace("&lt;", "<").replace("&gt;", ">"))


def mmss(s: float) -> str:
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--dir", type=Path, required=True, help="a built player folder, e.g. generated/lesson-player")
    ap.add_argument("--show", type=int, default=15, help="findings to print per width")
    ap.add_argument("--report", type=Path, help="where to write the report (default: lens_check.json in --dir)")
    a = ap.parse_args()
    report, failures = {}, 0
    for name, width in WIDTHS.items():
        res = run(a.dir / "player.html", width)
        report[name] = res
        failures += len(res["clipped"])
        print(f"{name} ({res['frame']}px frame): {res['samples']} moments, {res['windows']} lens, zoom "
              f"or extract window(s) measured; {len(res['clipped'])} clipped line(s)")
        for w in res.get("whole") or []:
            print(f"  {w['board']}: the extract {w['split']}% of the width, its text {w['font_px']}px "
                  f"({w['font_cqh']}% of the frame; bundle {w['bundle_font']}), the question column at "
                  f"{round(w['zoom'] * 100)}%; {w['lines_outside']} of "
                  f"{w['lines_measured']} line measurements outside its page or the board")
        for c in res["clipped"][:a.show]:
            print(f"  CLIPPED {c['board']} ({c['kind']}) at {mmss(c['t'])}: {c['text']!r} cut at the "
                  f"{'/'.join(c['sides'])} by {c['px']}px")
    out = a.report or (a.dir / "lens_check.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if failures:
        raise SystemExit(f"lens check failed: {failures} clipped line(s); see {out}")
    print("lens check passed: every line inside a lens or zoom window is whole, and every Part B "
          "question board's extract is whole on its page")


if __name__ == "__main__":
    main()
