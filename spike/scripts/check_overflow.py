"""Overflow check: every block fits inside the board, in every state.

    .venv/Scripts/python spike/scripts/check_overflow.py <lesson_dir> --dir <player folder>

Rule (maintainer, 2026-09-27, after a note on Grammar 5's first board of
"What is a complex sentence?" was pushed under the player controls): every
block shown on a board lies fully inside the board area, at phone-landscape and
laptop width, in every state, while no word moves between states
(check_layout.py). For every board the player is driven, in headless Edge, to
every moment at which something on it appears or goes (each state's start and
end, each reveal, each pinned block, each erase), the camera's zoom is undone,
and each block shown is measured against the board area (the frame's content
band, inside its padding: what lies between the header and the control bar as
the frame draws them; on a small frame the controls keep 44 px). A block that extends outside it fails, and so does a
block whose own content is clipped (it scrolls inside itself).

It also fails a label drawn in capitals (docs/02-DESIGN-SYSTEM.md §6, §7c:
labels are in sentence case): a label element whose computed style uppercases
its text, or whose text has a word in capitals that is not an acronym.

The harness is the player itself, as in check_layout.py: no screenshot is
interpreted; every figure is geometry the browser reports.
"""

import argparse
import json
import re
import subprocess
import shutil
import atexit
import tempfile
from pathlib import Path

# Headless Edge runs with its own profile, removed on exit: with the default one,
# a run could be handed to an Edge window already open and never return
# (the layout check's 900 s time-outs on Grammar 6, 2026-09-27).
EDGE_PROFILE = tempfile.mkdtemp(prefix="oet-edge-")
atexit.register(shutil.rmtree, EDGE_PROFILE, True)

EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
# the frame the reference player draws in a phone held landscape, 915x412 (its
# controls keep 44 px, 13% of this frame), then phone-landscape and laptop
# (maintainer, 2026-10-08: the board measured above the control bar at every width)
WIDTHS = {"small phone": 590, "phone": 812, "laptop": 1120}
TOLERANCE_PX = 1.0
# words a label may keep in capitals: acronyms, never ordinary words
ACRONYMS = ["OET", "FANBOYS", "NHS", "GP", "BP", "ICU", "MRI", "CT", "ECG", "COPD", "IV", "UK",
            "US", "HIV", "ADHD", "A&E", "ED", "DVT", "TB", "BMI"]
LABELS = ".lbl, .cardhd, .cl-kind, .chg-tag, .chg-cap, .pill .tag, .tnote .lbl, th"

HARNESS = r"""
<script>
(function () {
  window.__lockWidth = __WIDTH__;
  fit();
  camEl.classList.remove("glide");
  const style = document.createElement("style");
  style.textContent = "*{transition:none!important;animation:none!important}";
  document.head.appendChild(style);
  const TOL = __TOL__, ACR = new Set(__ACR__), LABELS = __LABELS__;
  const body = camEl.parentElement;
  function area() {
    const r = body.getBoundingClientRect(), cs = getComputedStyle(body);
    return { l: r.left + parseFloat(cs.paddingLeft), t: r.top + parseFloat(cs.paddingTop),
             r: r.right - parseFloat(cs.paddingRight), b: r.bottom - parseFloat(cs.paddingBottom) };
  }
  function shown(el) {
    if (!el.isConnected || getComputedStyle(el).display === "none") return false;
    return el.dataset.layer === "fixed" || el.classList.contains("on");
  }
  function capsWord(text) {
    for (const w of text.split(/[\s/,.:;()'"\u2019-]+/)) {
      if (w.length >= 2 && /[A-Z]/.test(w) && w === w.toUpperCase() && /[A-Z]{2}/.test(w) && !ACR.has(w)) return w;
    }
    return null;
  }
  const out = [], caps = [];
  const seenOut = new Set(), seenCaps = new Set();
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
      // measure the board unzoomed; on a table board whose camera has panned
      // or zoomed to show its notes (ADR 007, ADR 020), measure what the
      // camera shows: the notes must be in view; the table itself may leave it
      const viewed = bd.table && keep && keep !== "none";
      if (!viewed) camEl.style.transform = "none";
      const A = area();
      for (const [id, el] of blockEls) {
        if (!shown(el)) continue;
        if (viewed && !el.classList.contains("beside")) continue;   // under the camera: the notes
        const r = el.getBoundingClientRect();
        if (!r.width && !r.height) continue;
        const over = { top: A.t - r.top, bottom: r.bottom - A.b, left: A.l - r.left, right: r.right - A.r };
        const worst = Object.entries(over).filter(([, v]) => v > TOL).sort((a, b) => b[1] - a[1])[0];
        const cs = getComputedStyle(el);
        // no exemption: a Part B question board's extract is shown whole (1.16;
        // its 1.15 lens, which hid the text beyond its frame, is gone)
        const clipped = /(hidden|clip|auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + TOL;
        if ((worst || clipped) && !seenOut.has(bd.id + "|" + id)) {
          seenOut.add(bd.id + "|" + id);
          out.push({ board: bd.id, block: id, t, state: (stateAt(bd, t) || {}).id || null,
                     side: worst ? worst[0] : null, px: worst ? +worst[1].toFixed(1) : 0,
                     clipped: clipped ? el.scrollHeight - el.clientHeight : 0,
                     board_h: Math.round(A.b - A.t) });
        }
        for (const lab of el.querySelectorAll(LABELS)) {
          const txt = lab.textContent.trim();
          if (!txt) continue;
          // a practice-set text's header is its title as released (ADR 026), not a
          // label the lesson writes: a code in it ("RC-12") stays as released
          if (lab.closest(".doc")) continue;
          const tt = getComputedStyle(lab).textTransform;
          const w = tt === "uppercase" ? "(text-transform: uppercase)" : capsWord(txt);
          if (w && !seenCaps.has(id + "|" + txt)) {
            seenCaps.add(id + "|" + txt);
            caps.push({ board: bd.id, block: id, t, label: txt, why: w });
          }
        }
      }
      camEl.style.transform = keep;
    }
  }
  const pre = document.createElement("pre");
  pre.id = "overflow-result";
  pre.textContent = JSON.stringify({ width: window.innerWidth, frame: Math.round(frame.getBoundingClientRect().width),
                                     samples, overflow: out, capitals: caps });
  document.body.appendChild(pre);
})();
</script>
"""


def run(player: Path, width: int) -> dict:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the overflow check needs a browser")
    harness = player.with_name("player_overflow.html")
    html = player.read_text(encoding="utf-8")
    script = (HARNESS.replace("__WIDTH__", str(width)).replace("__TOL__", str(TOLERANCE_PX))
              .replace("__ACR__", json.dumps(ACRONYMS)).replace("__LABELS__", json.dumps(LABELS)))
    harness.write_text(html.replace("</body>", script + "</body>"), encoding="utf-8")
    r = subprocess.run([edge, "--headless=new", "--user-data-dir=" + EDGE_PROFILE, "--disable-gpu", f"--window-size={width + 200},{int(width * 0.75)}",
                        "--virtual-time-budget=60000", "--dump-dom", harness.resolve().as_uri()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="overflow-result">(.*?)</pre>', r.stdout, re.S)
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
    for name, width in WIDTHS.items():
        res = run(a.dir / "player.html", width)
        report[name] = res
        failures += len(res["overflow"]) + len(res["capitals"])
        print(f"{name} ({res['frame']}px frame): {res['samples']} moments measured; "
              f"{len(res['overflow'])} block(s) outside the board, {len(res['capitals'])} label(s) in capitals")
        for o in res["overflow"][:a.show]:
            t = o["t"]
            print(f"  OUTSIDE {o['board']} {o['block']} at {int(t // 60)}:{int(t % 60):02d} ({o['state']}): "
                  + (f"{o['px']}px past the {o['side']} of a {o['board_h']}px board" if o["side"] else "")
                  + (f" clipped by {o['clipped']}px" if o["clipped"] else ""))
        for c in res["capitals"][:a.show]:
            print(f"  CAPITALS {c['board']} {c['block']}: {c['label']!r} {c['why']}")
    (a.dir / "overflow_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if failures:
        raise SystemExit(f"overflow check failed: {failures} finding(s); see {a.dir / 'overflow_check.json'}")
    print("overflow check passed: every block inside the board, every label in sentence case")


if __name__ == "__main__":
    main()
