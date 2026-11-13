"""Drawn-text check: every word a board shows is drawn, as playback draws it.

    .venv/Scripts/python spike/scripts/check_drawn_text.py <lesson_dir> --dir <player folder>

Rule (the owner, 2026-11-13, after Speaking 2's gloss cards showed
"reassure = To help someone feel less" and "shift = The hours you work on",
while the narration said the whole meaning): every gloss card shows its whole
meaning and its example, and no word of any part is cut (ADR 056).

The other checks seek: after a seek a part is drawn settled, with no motion, so
a fault in a part's motion never shows to them. This check plays: the player is
driven, in headless Edge, from the lesson's start to its end in steps of
0.5 s (below the player's 0.75 s jump), so every part is drawn in motion as in
playback. At the end of every state, and just before an erase, every running
motion is finished and every word of every block shown is hit-tested at its
centre: a word the browser does not paint there (clipped, covered, hidden) is
cut. A gloss card's term, meaning and example, as drawn, are then compared word
for word with the gloss's source in the bundle (term, explanation, text).

Each moment is measured twice: as the camera shows the board, and with its
zoom undone (as check_overflow.py measures). A word is drawn when either pass
paints it; cut when a pass has it in the board's view and neither paints it; a
word out of view in both (a table the camera pans) is counted, not measured.
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
# the frames of check_overflow.py: a gloss wraps by the frame's own units, but a
# line can still break at a different word on another frame
WIDTHS = {"small phone": 590, "phone": 812, "laptop": 1120}
STEP_S = 0.5

HARNESS = r"""
<script>
(function () {
  window.__lockWidth = __WIDTH__;
  fit();
  camEl.classList.remove("glide");
  const style = document.createElement("style");
  // hit-testing needs pointer events on the words; nothing else is changed
  style.textContent = ".frame .blk, .frame .blk *{pointer-events:auto!important}";
  document.head.appendChild(style);
  const STEP = __STEP__;
  let VIEW = null;
  function shown(el) {
    if (!el.isConnected || getComputedStyle(el).display === "none") return false;
    return el.dataset.layer === "fixed" || el.classList.contains("on");
  }
  // a point outside the visible box of a scrolling ancestor (a window whose
  // content is taller or wider than it), up to the block itself
  function scrolledOut(par, root, x, y) {
    const top = root.closest(".blk") || root;
    for (let e = par; e; e = e.parentElement) {
      const cs = getComputedStyle(e);
      if (cs.overflow !== "visible" && (e.scrollHeight > e.clientHeight + 1 || e.scrollWidth > e.clientWidth + 1)) {
        const q = e.getBoundingClientRect();
        if (x < q.left || x > q.right || y < q.top || y > q.bottom) return true;
      }
      if (e === top) break;
    }
    return false;
  }
  // the words of an element's text: 1 painted at its centre, 0 cut, 2 not measured
  function words(root, skip) {
    const out = [];
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) {
      if (skip && skip(n)) continue;
      const par = n.parentElement;
      if (!par || !par.checkVisibility({ visibilityProperty: true })) continue;
      const re = /\S+/g;
      let m;
      while ((m = re.exec(n.data))) {
        const r = document.createRange();
        r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length);
        // each line box of the word on its own: a hyphenated word may wrap
        const rects = [...r.getClientRects()].filter(q => q.width && q.height);
        if (!rects.length) continue;
        let st = 1, why = "";
        for (const q of rects) {
          const x = q.left + q.width / 2, y = q.top + q.height / 2;
          // out of the board's view (a table the camera pans), or scrolled out of
          // a window by design (a text's lens, a transcript's window: check_lens.py)
          if (x < VIEW.l || y < VIEW.t || x > VIEW.r || y > VIEW.b || scrolledOut(par, root, x, y)) {
            if (st === 1) st = 2;
            continue;
          }
          const hit = document.elementsFromPoint(x, y);
          if (hit.some(h => h === par || par.contains(h))) continue;
          st = 0;
          const anc = [];
          for (let e = par; e && e !== document.body; e = e.parentElement) {
            const cs = getComputedStyle(e);
            if (cs.clipPath !== "none" || cs.overflow !== "visible") anc.push(e.tagName + "." + [...e.classList].join(".") + "{" + cs.clipPath + "|" + cs.overflow + "}");
          }
          why = Math.round(x) + "," + Math.round(y) + " " + (hit[0] ? hit[0].tagName + "." + [...hit[0].classList].join(".") : "nothing") + " " + anc.join(" < ");
        }
        // a word painted in one of its boxes and out of view in another is drawn
        out.push([m[0], st, why]);
      }
    }
    return out;
  }
  // the moments measured: each state's end, and just before each erase
  const marks = [];
  for (const bd of boards) for (const s of bd.states) {
    marks.push({ t: Math.min(s.end, bd.until) - 0.01, bd, s });
    if (s.erase && s.erase.time > s.start) marks.push({ t: s.erase.time - 0.01, bd, s, erase: true });
  }
  marks.sort((a, b) => a.t - b.t);
  const cut = [], gloss = [];
  let unmeasured = 0; const unmeasured_sample = [];
  let samples = 0, t = 0, mi = 0;
  lastRenderT = null;
  renderFrame(0);
  while (mi < marks.length) {
    const next = marks[mi].t;
    while (t + STEP < next) { t += STEP; renderFrame(t); }
    t = next; renderFrame(t);
    const mk = marks[mi++];
    if (boardAt(t) !== mk.bd) continue;
    document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} });
    samples++;
    // measured twice: as the camera shows the board, and with its zoom undone
    // (as check_overflow.py measures); a word is drawn when either pass paints
    // it, cut when a pass has it in view and neither paints it
    const passes = [];
    const keep = camEl.style.transform;
    for (const undo of [false, true]) {
      if (undo) camEl.style.transform = "none";
      const vr = camEl.parentElement.getBoundingClientRect();
      VIEW = { l: Math.max(vr.left, 0), t: Math.max(vr.top, 0), r: Math.min(vr.right, innerWidth),
               b: Math.min(vr.bottom, innerHeight) };
      const res = new Map();
      for (const [id, el] of blockEls) {
        if (!shown(el)) continue;
        // a part not drawn yet is not measured; every other text of the block is
        const skip = n => { const p = n.parentElement && n.parentElement.closest("[data-part]");
                            return !!(p && el.contains(p) && !p.classList.contains("on")); };
        const g = {};
        if (el.classList.contains("gl")) for (const [k, sel] of [["term", ".gl-w"], ["meaning", ".gl-m"], ["example", ".gl-x"]]) {
          const p = el.querySelector(sel);
          g[k] = !p ? null : (p.dataset.part && !p.classList.contains("on")) ? { on: false } : { on: true, ws: words(p) };
        }
        res.set(id, { el, ws: words(el, skip), g });
      }
      passes.push(res);
    }
    camEl.style.transform = keep;
    const merge = (a, b) => a.map((w, i) => {
      const v = b[i];
      if (!v || v[0] !== w[0]) return w;
      if (w[1] === 1 || v[1] === 1) return [w[0], 1, ""];
      if (w[1] === 0) return w;
      return v;
    });
    for (const [id, A] of passes[0]) {
      const B = passes[1].get(id) || A;
      const ws = merge(A.ws, B.ws);
      const lost = ws.filter(w => w[1] === 0).map(w => w[0]);
      unmeasured += ws.filter(w => w[1] === 2).length;
      if (ws.some(w => w[1] === 2) && unmeasured_sample.length < 12) unmeasured_sample.push(id + " " + t.toFixed(0) + " " + ws.filter(w => w[1] === 2).slice(0, 3).map(w => w[0] + "@" + w[2]).join(" | "));
      if (lost.length) cut.push({ board: mk.bd.id, state: mk.s.id, block: id, t, erase: !!mk.erase,
                                  words: ws.map(w => w[0] + (w[1] === 0 ? "[CUT:" + w[2] + "]" : "")).join(" "),
                                  lost });
      if (A.el.classList.contains("gl")) {
        const part = k => { const x = A.g[k], y = B.g[k];
          if (!x || !x.on) return x;
          return { on: true, words: merge(x.ws, y && y.on ? y.ws : x.ws).filter(w => w[1] !== 0).map(w => w[0]) }; };
        gloss.push({ board: mk.bd.id, state: mk.s.id, block: id, t, erase: !!mk.erase,
                     term: part("term"), meaning: part("meaning"), example: part("example") });
      }
    }
  }
  const pre = document.createElement("pre");
  pre.id = "drawn-result";
  pre.textContent = JSON.stringify({ width: window.innerWidth, frame: Math.round(frame.getBoundingClientRect().width),
                                     end: marks.length ? marks[marks.length - 1].t : 0, played: t, samples, unmeasured, unmeasured_sample, cut, gloss });
  document.body.appendChild(pre);
})();
</script>
"""


def run(player: Path, width: int) -> dict:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the drawn-text check needs a browser")
    harness = player.with_name("player_drawn.html")
    html = player.read_text(encoding="utf-8")
    script = HARNESS.replace("__WIDTH__", str(width)).replace("__STEP__", str(STEP_S))
    harness.write_text(html.replace("</body>", script + "</body>"), encoding="utf-8")
    try:
        r = subprocess.run([edge, "--headless=new", "--do-not-de-elevate", "--user-data-dir=" + EDGE_PROFILE,
                            "--disable-gpu", f"--window-size={width + 200},{width + 200}",
                            "--virtual-time-budget=60000", "--dump-dom", harness.resolve().as_uri()],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    finally:
        harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="drawn-result">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("the harness produced no result; the player did not run")
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")
                      .replace("&lt;", "<").replace("&gt;", ">"))


def words_of(text: str) -> list:
    return (text or "").split()


def mmss(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def compare_glosses(blocks: dict, gloss: list) -> list:
    """Each gloss card's parts as drawn, word for word against its source.

    A part not drawn yet at a moment is not compared there; a part never drawn
    by the card's last moment is a finding."""
    found, last = [], {}
    for g in gloss:
        src = blocks.get(g["block"]) or {}
        want = {"term": src.get("term"), "meaning": src.get("explanation"), "example": src.get("text")}
        for k, w in want.items():
            got = g.get(k)
            if w is None or got is None or not got.get("on"):
                continue
            # letter for letter, spaces aside: a mark or a bold word splits a word's text into nodes
            # ("sluice" and "."), and each node's words come apart; a word lost is still a difference
            if "".join(got["words"]) != "".join(words_of(w)):
                found.append({"block": g["block"], "board": g["board"], "state": g["state"], "t": g["t"],
                              "part": k, "source": w, "drawn": " ".join(got["words"])})
        last[g["block"]] = g
    for bid, g in last.items():
        src = blocks.get(bid) or {}
        for k, key in (("meaning", "explanation"), ("example", "text")):
            got = g.get(k)
            if src.get(key) and (got is None or not got.get("on")):
                found.append({"block": bid, "board": g["board"], "state": g["state"], "t": g["t"],
                              "part": k, "source": src[key], "drawn": "(never drawn)"})
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--dir", type=Path, required=True, help="a built player folder, e.g. generated/lesson-player")
    ap.add_argument("--widths", default=",".join(WIDTHS), help="frames to play, comma-separated names")
    ap.add_argument("--show", type=int, default=20, help="findings to print per frame")
    a = ap.parse_args()
    bundle = json.loads((a.dir / "bundle.json").read_text(encoding="utf-8"))
    raw = bundle.get("blocks") or {}
    blocks = raw if isinstance(raw, dict) else {b["id"]: b for b in raw if isinstance(b, dict) and b.get("id")}
    n_gloss = sum(1 for b in blocks.values() if b.get("type") == "gloss")
    report, failures = {}, 0
    for name in [w.strip() for w in a.widths.split(",") if w.strip()]:
        res = run(a.dir / "player.html", WIDTHS[name])
        if res["played"] < res["end"] - 0.001:
            raise SystemExit(f"{name}: the play-through stopped at {mmss(res['played'])} of {mmss(res['end'])}")
        bad = compare_glosses(blocks, res["gloss"])
        res["gloss_findings"] = bad
        report[name] = res
        failures += len(res["cut"]) + len(bad)
        print(f"{name} ({res['frame']}px frame): played to {mmss(res['played'])}, {res['samples']} moments; "
              f"{len(res['cut'])} block(s) with cut words, {len(bad)} gloss part(s) not drawn whole "
              f"({n_gloss} gloss card(s)); {res['unmeasured']} word(s) out of the board's view, not measured")
        for c in res["cut"][:a.show]:
            print(f"  CUT {c['board']} {c['block']} at {mmss(c['t'])} ({c['state']}): {c['words'][:200]}")
        for g in bad[:a.show]:
            print(f"  GLOSS {g['block']} {g['part']} at {mmss(g['t'])} ({g['state']}): "
                  f"drawn {g['drawn']!r}, source {g['source']!r}")
    (a.dir / "drawn_text_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    if failures:
        raise SystemExit(f"drawn-text check failed: {failures} finding(s); see {a.dir / 'drawn_text_check.json'}")
    print("drawn-text check passed: every word drawn in playback, every gloss whole")


if __name__ == "__main__":
    main()
