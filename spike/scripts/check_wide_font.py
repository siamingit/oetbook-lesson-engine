"""Wide-font check: no board hides anything when the learner's device draws a
wider font than the one the fit measured.

    .venv/Scripts/python spike/scripts/check_wide_font.py <lesson_dir> --dir <player folder> [--font Verdana]

Rule (maintainer, 2026-10-08; ADR 026 amendment of that date): the player's text
is drawn in the device's own font (`system-ui`), so a board fitted with one font
can be cut with another. On a Part B question board (bundle 1.16, rule 36) the
player guards against it: on the device, it sets the extract smaller (never
below 2.6% of the frame), gives the question column more room, and as a last
resort sets the question column smaller, until both columns fit. This check
proves the guard instead of assuming it: it forces a wide font on the whole
frame (Verdana, about as wide as DejaVu Sans, which Linux browsers draw for
`system-ui`), drives the player to every moment of every Part B question board
at the small phone, phone-landscape and laptop frames, and fails any block, or
any line of text, that lies outside the board area (under the header or the
control bar) or outside its own block where that block clips. A line under a
gloss drawn over the question column (its state's `overlay`) is hidden by the
gloss rule and is not a finding. It reports what the guard chose per board.

Every other board (maintainer, 2026-10-11: the player's guard applies to every
board of every lesson) is driven to the moments check_overflow.py measures (each
state's start and end, each reveal, each pinned block, each erase), with the
same camera rule: the board unzoomed, except a table board whose camera has
moved, where its notes must be in view as it shows them. A block outside the
board, or a line of text outside the board or outside its own block where that
block clips, fails. It reports each board the guard set smaller, and by how much.

The harness is the player itself, as in check_overflow.py: no screenshot is
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
# as check_overflow.py: a phone held landscape (915x412), phone-landscape, laptop
WIDTHS = {"small phone": 590, "phone": 812, "laptop": 1120}
TOLERANCE_PX = 1.0

HARNESS = r"""
<script>
(function () { try {
  window.__lockWidth = __WIDTH__;
  const style = document.createElement("style");
  style.textContent = "*{transition:none!important;animation:none!important}.frame{--sc-motion:0}.frame .blk{transition:none!important}"
    + ".frame,.frame *{font-family:" + __FONT__ + "!important}";
  document.head.appendChild(style);
  fit();
  camEl.classList.remove("glide");
  if (typeof guardReset === "function") guardReset();   // the fonts changed: the guard measures again
  const TOL = __TOL__;
  // a player built before bundle 1.16 has no Part B question board (and no isQBoard)
  const qb = bd => typeof isQBoard === "function" && isQBoard(bd);
  const body = camEl.parentElement;
  function area() {
    const r = body.getBoundingClientRect(), cs = getComputedStyle(body);
    return { left: r.left + parseFloat(cs.paddingLeft), top: r.top + parseFloat(cs.paddingTop),
             right: r.right - parseFloat(cs.paddingRight), bottom: r.bottom - parseFloat(cs.paddingBottom) };
  }
  function shown(el) {
    if (!el.isConnected || getComputedStyle(el).display === "none") return false;
    return el.dataset.layer === "fixed" || el.classList.contains("on");
  }
  function outside(q, W) {
    const s = [];
    if (q.top < W.top - TOL) s.push("top");
    if (q.bottom > W.bottom + TOL) s.push("bottom");
    if (q.left < W.left - TOL) s.push("left");
    if (q.right > W.right + TOL) s.push("right");
    return s;
  }
  const hidden = [], seen = new Set(), guards = [], fitted = [];
  let samples = 0;
  for (const bd of boards) {
    const isQ = qb(bd);
    const times = new Set([bd.start + 0.001]);
    for (const s of bd.states) {
      times.add(s.start + 0.001); times.add(s.end - 0.001);
      for (const t of Object.values(s.reveal || {})) times.add(t + 0.001);
      if (isQ) {
        for (const c of s.clears || []) times.add(c.time + 0.001);
        for (const u of s.utterances) for (const c of u.cues) times.add(c.time + 0.001);
      } else if (s.erase) times.add(s.erase.time - 0.001);
    }
    for (const t of Object.values(bd.pinned || {})) times.add(t + 0.001);
    if (isQ) for (const f of bd.focus || []) times.add(f.time + 0.001);
    else for (const t of Object.values(bd.reveal || {})) times.add(t + 0.001);
    // 1.19 (ADR 030): on a Listening board, each section's start while a recording plays
    if (typeof isLBoard === "function" && isLBoard(bd)) for (const t of listenMoments(bd)) times.add(t);
    for (const t of [...times].filter(t => t >= bd.start && t < bd.until).sort((a, b) => a - b)) {
      lastRenderT = null;
      renderFrame(t);
      samples++;
      // as check_overflow.py: every other board unzoomed, except a table board
      // whose camera has moved, where only its notes are measured, as shown
      const keep = camEl.style.transform;
      const viewed = !isQ && bd.table && keep && keep !== "none";
      if (!isQ && !viewed) camEl.style.transform = "none";
      const A = area();
      const st = stateAt(bd, t);
      const overs = [...camEl.querySelectorAll(".blk.over.on:not(.cleared)")];
      for (const [id, el] of [...blockEls, ...(typeof lsecEls === "object" ? lsecEls : []), ...(typeof lpanEls === "object" ? lpanEls : [])]) {
        if (!shown(el)) continue;
        if (viewed && !el.classList.contains("beside")) continue;
        if (id === bd.table && st && st.veil) continue;       // covered: its words are not shown yet
        const r = el.getBoundingClientRect();
        if (!r.width && !r.height) continue;
        const add = (what, sides, px) => {
          const key = bd.id + "|" + id + "|" + what;
          if (seen.has(key)) return;
          seen.add(key);
          hidden.push({ board: bd.id, block: id, t: +t.toFixed(3), state: st ? st.id : null, what, sides, px: +px.toFixed(1) });
        };
        const bs = outside(r, A);
        if (bs.length) add("the block", bs, Math.max(A.top - r.top, r.bottom - A.bottom, A.left - r.left, r.right - A.right));
        const clips = /(hidden|clip|auto|scroll)/.test(getComputedStyle(el).overflowY);
        const own = { left: r.left + el.clientLeft, top: r.top + el.clientTop,
                      right: r.left + el.clientLeft + el.clientWidth, bottom: r.top + el.clientTop + el.clientHeight };
        const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        for (let n; (n = walker.nextNode());) {
          if (!n.data.trim()) continue;
          const rg = document.createRange(); rg.selectNodeContents(n);
          for (const q of rg.getClientRects()) {
            if (!q.width || !q.height) continue;
            if (overs.some(o => !o.contains(n) && (() => { const g = o.getBoundingClientRect();
                  return q.right > g.left && q.left < g.right && q.bottom > g.top && q.top < g.bottom; })())) continue;
            let W = clips ? { left: Math.max(A.left, own.left), top: Math.max(A.top, own.top),
                              right: Math.min(A.right, own.right), bottom: Math.min(A.bottom, own.bottom) } : A;
            // the map of the texts (bundle 1.14) shows its lines through its lens
            // window of whole lines, by design: a line wholly outside it (hidden,
            // or in a faded cue band) is not shown; a line in it is measured
            // against it (the window as check_lens.py takes it)
            // 1.19 (ADR 030): a Listening box (and a note form's window) shows its
            // lines through a window of whole lines, as the map's lens does
            const box = n.parentElement && n.parentElement.closest(".lt-win");
            if (box && el.contains(box)) {
              if (getComputedStyle(n.parentElement).visibility === "hidden") continue;
              const v = box.getBoundingClientRect();
              if (q.bottom <= v.top + 1 || q.top >= v.bottom - 1) continue;
              W = { left: Math.max(W.left, v.left), top: Math.max(W.top, v.top),
                    right: Math.min(W.right, v.right), bottom: Math.min(W.bottom, v.bottom) };
            }
            const lens = n.parentElement && n.parentElement.closest(".dmap-view");
            if (lens && el.contains(lens)) {
              const R = lens.getBoundingClientRect(), sc = lens.offsetHeight ? R.height / lens.offsetHeight : 1;
              const set = lens.dataset.lensTop != null;
              const v = { top: R.top + (lens.clientTop + (set ? +lens.dataset.lensTop : 0)) * sc,
                          bottom: R.top + (lens.clientTop + (set ? +lens.dataset.lensBottom : lens.clientHeight)) * sc,
                          left: R.left + lens.clientLeft * sc, right: R.left + (lens.clientLeft + lens.clientWidth) * sc };
              if (q.bottom <= v.top + 1 || q.top >= v.bottom - 1 || q.right <= v.left || q.left >= v.right) continue;
              W = { left: Math.max(W.left, v.left), top: Math.max(W.top, v.top),
                    right: Math.min(W.right, v.right), bottom: Math.min(W.bottom, v.bottom) };
            }
            const s = outside(q, W);
            if (s.length) add("line " + JSON.stringify(n.data.trim().slice(0, 40)), s,
                              Math.max(W.top - q.top, q.bottom - W.bottom, W.left - q.left, q.right - W.right));
          }
        }
      }
      camEl.style.transform = keep;
    }
    if (isQ) {
      const g = bd._guard || { split: bd.split, font: blocks[bd.table].font, zoom: 1 };
      guards.push({ board: bd.id, split: g.split, font: g.font, zoom: g.zoom, bundle_split: bd.split,
                    bundle_font: blocks[bd.table].font });
    } else if ((bd._fitZoom || 1) !== 1 || (bd._fitPic || 1) !== 1) {
      // 2026-10-11: a board the guard set smaller, with its pictures' share of their size
      fitted.push({ board: bd.id, zoom: bd._fitZoom || 1, pic: bd._fitPic || 1 });
    }
  }
  const pre = document.createElement("pre");
  pre.id = "wide-result";
  pre.textContent = JSON.stringify({ frame: Math.round(frame.getBoundingClientRect().width),
                                     ctl: Math.round(document.querySelector(".frame .ctl").getBoundingClientRect().height),
                                     samples, hidden, guards, fitted });
  document.body.appendChild(pre);
} catch (e) {
  const pre = document.createElement("pre");
  pre.id = "wide-result";
  pre.textContent = JSON.stringify({ error: String(e && e.stack || e) });
  document.body.appendChild(pre);
} })();
</script>
"""


def run(player: Path, width: int, font: str) -> dict:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the wide-font check needs a browser")
    harness = player.with_name("player_wide.html")
    html = player.read_text(encoding="utf-8")
    script = (HARNESS.replace("__WIDTH__", str(width)).replace("__TOL__", str(TOLERANCE_PX))
              .replace("__FONT__", json.dumps(font)))
    harness.write_text(html.replace("</body>", script + "</body>"), encoding="utf-8")
    r = subprocess.run([edge, "--headless=new", "--do-not-de-elevate", "--user-data-dir=" + EDGE_PROFILE, "--disable-gpu",
                        f"--window-size={width + 200},{int(width * 0.75)}", "--mute-audio",
                        "--virtual-time-budget=60000", "--dump-dom", harness.resolve().as_uri()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="wide-result">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("the harness produced no result; the player did not run")
    res = json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")
                     .replace("&lt;", "<").replace("&gt;", ">"))
    if "error" in res:
        raise SystemExit("the harness failed in the player: " + res["error"])
    return res


def mmss(s: float) -> str:
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--dir", type=Path, required=True, help="a built player folder, e.g. generated/lesson-player")
    ap.add_argument("--font", default="Verdana", help="the wide font forced on the frame")
    ap.add_argument("--show", type=int, default=15, help="findings to print per width")
    a = ap.parse_args()
    report, failures = {}, 0
    for name, width in WIDTHS.items():
        res = run(a.dir / "player.html", width, a.font)
        report[name] = res
        failures += len(res["hidden"])
        print(f"{name} ({res['frame']}px frame, controls {res['ctl']}px), {a.font}: {res['samples']} moments; "
              f"{len(res['hidden'])} hidden")
        fitted = res.get("fitted", [])
        if fitted:
            print(f"  the guard set {len(fitted)} other board(s) smaller: "
                  + ", ".join(f"{f['board']} {round(f['zoom'] * 100, 1)}%"
                              + (f" (pictures {round(f['pic'] * 100)}%)" if f["pic"] != 1 else "")
                              for f in fitted))
        for g in res["guards"]:
            print(f"  {g['board']}: the extract {g['split']}% (bundle {g['bundle_split']}%) at {g['font']}% "
                  f"(bundle {g['bundle_font']}%), the question column at {round((g['zoom'] or 1) * 100)}%")
        for h in res["hidden"][:a.show]:
            print(f"  HIDDEN {h['board']} at {mmss(h['t'])}: {h['what']} of {h['block']} past the "
                  f"{'/'.join(h['sides'])} by {h['px']}px")
    (a.dir / "wide_font_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if failures:
        raise SystemExit(f"wide-font check failed: {failures} finding(s); see {a.dir / 'wide_font_check.json'}")
    print(f"wide-font check passed: with {a.font}, nothing on any board is hidden or under the controls")


if __name__ == "__main__":
    main()
