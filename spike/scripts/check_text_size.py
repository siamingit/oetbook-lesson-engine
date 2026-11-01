"""Readability check: no text on a board is smaller than the minimum, and every line of text stands out from
what is behind it.

    .venv/Scripts/python spike/scripts/check_text_size.py <lesson_dir> --dir <player folder>

Rules (the owner's review of Word Order draft.3, 2026-11-01; ADR 050 amendment (1); docs/02-DESIGN-SYSTEM.md
§7k, "Readable on a phone"):
  1. In the 1600x900 frame, running text is at least 26 px and a label at least 20 px, so that it stays readable
     on a phone. The size is the size drawn: the font size times every scale the board, its fit and its camera
     put on it. A line in the teacher's hand counts at its size divided by 1.3 (style_c.HAND: Caveat's x-height
     against IBM Plex's), so a hand note reads as body text does. A label is a table's head (th), a text set in
     capitals, a pseudo-element's words (a label drawn from a header, a count, a step's number), or a piece of
     at most four words (a pill, a tile, a line number); anything longer is running text.
  2. Every line of text has a contrast of at least 4.5:1 with what is behind it (WCAG 2 AA), counted after every
     opacity it is drawn under: a row dimmed by the spotlight must stay readable (dimmed with a lighter ground,
     never by greying its words out).
The harness is the player itself (as check_wide_font.py): it drives the player to every moment a board changes
(each state's start and end, each reveal, each pinned block) with its camera as it is, and measures every line
of text in the board and the board's heading; no screenshot is interpreted. It writes text_size_check.json beside
the player and fails on any finding.
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
WIDTH = 1600            # the 1600x900 frame the rule is written for
FRAME_H = 900
RUNNING_PX, LABEL_PX = 26.0, 20.0
CONTRAST = 4.5
HAND = 1.3              # style_c.HAND
LABEL_WORDS = 4
TOL_PX = 0.25
EMPTY = 0.4            # rule 4: no more than 40% of the board's height or width left empty at its fullest

HARNESS = r"""
<script>
(function () { try {
  window.__lockWidth = __WIDTH__;
  const style = document.createElement("style");
  style.textContent = "*{transition:none!important;animation:none!important}.frame{--sc-motion:0}.frame .blk{transition:none!important}";
  document.head.appendChild(style);
  fit();
  camEl.classList.remove("glide");
  const R = { run: __RUN__, label: __LABEL__, contrast: __CONTRAST__, hand: __HAND__, words: __WORDS__, tol: __TOL__, empty: __EMPTY__ };
  const body = camEl.parentElement;
  const k = __FRAMEH__ / frame.getBoundingClientRect().height;      // frame px to the 1600x900 frame
  function area() {
    const r = body.getBoundingClientRect(), cs = getComputedStyle(body);
    return { left: r.left + parseFloat(cs.paddingLeft), top: r.top + parseFloat(cs.paddingTop),
             right: r.right - parseFloat(cs.paddingRight), bottom: r.bottom - parseFloat(cs.paddingBottom) };
  }
  function shown(el) {
    if (!el.isConnected || getComputedStyle(el).display === "none") return false;
    return el.dataset.layer === "fixed" || el.classList.contains("on");
  }
  // the scale an element is drawn at (every transform above it, the camera's too)
  function scaleOf(el) {
    let e = el;
    while (e && !(e.offsetWidth > 0)) e = e.parentElement;
    if (!e) return 1;
    return e.getBoundingClientRect().width / e.offsetWidth;
  }
  function rgba(s) {
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(parseFloat);
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
  }
  const over = (c, b, a) => [0, 1, 2].map(i => c[i] * a + b[i] * (1 - a));
  function lum(c) {
    const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
  }
  function ratio(a, b) { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
  // the text's colour and its ground as drawn: every background from the frame down, then every opacity
  // group from the text back up (an opacity fades a group's ground and its words into what is behind it)
  function drawn(el, color) {
    const chain = [];
    for (let e = el; e && e !== document.documentElement; e = e.parentElement) { chain.unshift(e); if (e === frame) break; }
    let behind = [255, 255, 255];
    const layers = [];
    for (const e of chain) {
      const cs = getComputedStyle(e);
      const b = rgba(cs.backgroundColor);
      const before = behind;
      if (b && b[3] > 0) behind = over(b, behind, b[3]);
      // a plain wash over the ground (a gradient of one colour, the spotlight's lighter ground)
      const g = cs.backgroundImage.match(/^linear-gradient\((rgba?\([^)]*\)), (rgba?\([^)]*\))\)$/);
      if (g && g[1] === g[2]) { const w = rgba(g[1]); if (w[3] > 0) behind = over(w, behind, w[3]); }
      layers.push({ before, after: behind, op: parseFloat(cs.opacity) });
    }
    const c = rgba(color);
    let fg = over(c, behind, c[3]), bg = behind;
    for (let i = layers.length - 1; i >= 0; i--) {
      const L = layers[i];
      if (L.op < 1) { fg = over(fg, L.before, L.op); bg = over(bg, L.before, L.op); }
    }
    let op = 1;
    for (const L of layers) op *= L.op;
    return { fg, bg, op, alpha: c[3] };
  }
  function words(s) { return s.trim().split(/\s+/).filter(Boolean).length; }
  function pieceOf(el) {
    for (let e = el; e && e !== camEl; e = e.parentElement) {
      const d = getComputedStyle(e).display;
      if (d !== "inline" && d !== "contents") return e;
    }
    return el;
  }
  const isHand = cs => /caveat|segoe print|bradley hand|chalkboard|cursive/i.test(cs.fontFamily.split(",")[0]);
  const found = new Map();
  const minimum = new Map();
  function add(kind, bd, id, t, text, info) {
    const key = kind + "|" + bd.id + "|" + id + "|" + text;
    const old = found.get(key);
    if (old && old.value <= info.value) return;
    found.set(key, Object.assign({ kind, board: bd.id, block: id, t: +t.toFixed(3), text }, info));
  }
  function measure(bd, t, id, el, A) {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n; (n = walker.nextNode());) {
      if (!n.data.trim()) continue;
      const p = n.parentElement;
      const cs = getComputedStyle(p);
      if (cs.visibility === "hidden") continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      const rs = [...rg.getClientRects()].filter(q => q.width > 0 && q.height > 0
        && q.right > A.left && q.left < A.right && q.bottom > A.top && q.top < A.bottom);
      if (!rs.length) continue;
      const d = drawn(p, cs.color);
      if (d.alpha === 0 || d.op < 0.02) continue;              // not drawn yet (a typed word to come, a block on its way)
      const piece = pieceOf(p);
      const pcs = getComputedStyle(piece);
      const label = piece.tagName === "TH" || !!p.closest("th") || cs.textTransform === "uppercase"
                    || words(piece.innerText || piece.textContent) <= R.words;
      const hand = isHand(cs);
      const px = parseFloat(cs.fontSize) * scaleOf(p) * k;
      const eq = hand ? px / R.hand : px;
      const need = label ? R.label : R.run;
      const text = n.data.trim().slice(0, 48);
      const mk = bd.id + "|" + (label ? "label" : "running");
      if (!minimum.has(mk) || minimum.get(mk).px > eq) minimum.set(mk, { board: bd.id, kind: label ? "label" : "running", px: +eq.toFixed(1), text });
      if (eq < need - R.tol) add(label ? "small label" : "small text", bd, id, t, text,
                                  { value: +eq.toFixed(1), need, hand, font: +px.toFixed(1) });
      const c = ratio(d.fg, d.bg);
      if (c < R.contrast) add("low contrast", bd, id, t, text, { value: +c.toFixed(2), need: R.contrast,
                              fg: d.fg.map(Math.round), bg: d.bg.map(Math.round), opacity: +d.op.toFixed(2) });
    }
    // words drawn by the stylesheet (a label from a header, a count, a step's number): labels
    for (const e of [el, ...el.querySelectorAll("*")]) {
      for (const pseudo of ["::before", "::after"]) {
        const ps = getComputedStyle(e, pseudo);
        let c = ps.content;
        if (!c || c === "none" || c === "normal" || ps.display === "none") continue;
        let text = "";
        const re = /"((?:[^"\\]|\\.)*)"|attr\(([\w-]+)\)|counter\(/g;
        for (let m; (m = re.exec(c));) text += m[1] != null ? m[1] : m[2] ? (e.getAttribute(m[2]) || "") : "1";
        text = text.replace(/\\A/g, " ").trim();
        if (!text) continue;
        const r = e.getBoundingClientRect();
        if (!(r.right > A.left && r.left < A.right && r.bottom > A.top && r.top < A.bottom)) continue;
        if (getComputedStyle(e).visibility === "hidden") continue;
        const px = parseFloat(ps.fontSize) * scaleOf(e) * k;
        const eq = isHand(ps) ? px / R.hand : px;
        const mk = bd.id + "|label";
        if (!minimum.has(mk) || minimum.get(mk).px > eq) minimum.set(mk, { board: bd.id, kind: "label", px: +eq.toFixed(1), text });
        if (eq < R.label - R.tol) add("small label", bd, id, t, text + " (" + pseudo + ")",
                                      { value: +eq.toFixed(1), need: R.label, font: +px.toFixed(1) });
      }
    }
  }
  // rule 7: a heading that wraps leaves no line of one or two words
  const HEADS = "th,.cmp-h,.cardhd,.citem .ct,.chg-cap,.lbl,.ltitle,#hdrTitle";
  function headings(bd, t, id, el, A) {
    for (const h of [el, ...el.querySelectorAll(HEADS)].filter(e => e.matches(HEADS))) {
      const r = h.getBoundingClientRect();
      if (!r.width || !(r.right > A.left && r.left < A.right && r.bottom > A.top && r.top < A.bottom)) continue;
      const lines = [];
      const walker = document.createTreeWalker(h, NodeFilter.SHOW_TEXT);
      for (let n; (n = walker.nextNode());) {
        for (const m of n.data.matchAll(/\S+/g)) {
          const rg = document.createRange(); rg.setStart(n, m.index); rg.setEnd(n, m.index + m[0].length);
          const q = rg.getBoundingClientRect();
          if (!q.width) continue;
          const line = lines.find(l => Math.abs(l.top - q.top) < q.height / 2);
          if (line) line.n++; else lines.push({ top: q.top, n: 1 });
        }
      }
      if (lines.length > 1 && lines.some(l => l.n <= 2))
        add("heading wrap", bd, id, t, (h.innerText || "").replace(/\s+/g, " ").trim().slice(0, 60),
            { value: Math.min(...lines.map(l => l.n)), need: 3, lines: lines.length });
    }
  }
  // rule 4: at its fullest moment, a board leaves no more than 40% of its height or width empty
  const fill = new Map();
  function filled(bd, t, A) {
    let top = Infinity, bottom = -Infinity, left = Infinity, right = -Infinity;
    for (const [id, el] of blockEls) {
      if (!shown(el) || el.classList.contains("cleared")) continue;
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height || r.bottom < A.top || r.top > A.bottom) continue;
      top = Math.min(top, r.top); bottom = Math.max(bottom, r.bottom);
      left = Math.min(left, r.left); right = Math.max(right, r.right);
    }
    if (top === Infinity) return;
    const H = A.bottom - A.top, W = A.right - A.left;
    const gap = Math.max((top - A.top) / H, (A.bottom - bottom) / H, (left - A.left) / W, (A.right - right) / W);
    const old = fill.get(bd.id);
    if (!old || gap < old.gap) fill.set(bd.id, { gap, t, height: (bottom - top) / H, width: (right - left) / W });
  }
  let samples = 0;
  const hdr = document.querySelector(".frame .hdr");
  for (const bd of boards) {
    const times = new Set([bd.start + 0.001]);
    for (const s of bd.states) {
      times.add(s.start + 0.001); times.add(s.end - 0.001);
      for (const t of Object.values(s.reveal || {})) times.add(t + 0.001);
      if (s.erase) times.add(s.erase.time - 0.001);
    }
    for (const t of Object.values(bd.pinned || {})) times.add(t + 0.001);
    for (const t of Object.values(bd.reveal || {})) times.add(t + 0.001);
    for (const t of [...times].filter(t => t >= bd.start && t < bd.until).sort((a, b) => a - b)) {
      lastRenderT = null;
      renderFrame(t);
      samples++;
      const A = area();
      const st = stateAt(bd, t);
      for (const [id, el] of blockEls) {
        if (!shown(el)) continue;
        if (el.classList.contains("cleared")) continue;
        if (id === bd.table && st && st.veil) continue;
        measure(bd, t, id, el, A);
        headings(bd, t, id, el, A);
      }
      const H = hdr.getBoundingClientRect();
      const HA = { left: H.left, top: H.top, right: H.right, bottom: H.bottom };
      measure(bd, t, "(heading)", hdr.querySelector("#hdrTitle") || hdr, HA);
      headings(bd, t, "(heading)", hdr.querySelector("#hdrTitle") || hdr, HA);
      filled(bd, t, A);
    }
  }
  for (const [b, f] of fill) {
    if (f.gap > R.empty) add("empty half", { id: b }, "(board)", f.t, "the board at its fullest",
                             { value: +(f.gap * 100).toFixed(0), need: R.empty * 100,
                               height: +(f.height * 100).toFixed(0), width: +(f.width * 100).toFixed(0) });
  }
  const pre = document.createElement("pre");
  pre.id = "size-result";
  pre.textContent = JSON.stringify({ frame: Math.round(frame.getBoundingClientRect().width), scale: +k.toFixed(4), samples,
                                     findings: [...found.values()], minimum: [...minimum.values()],
                                     fill: [...fill].map(([b, f]) => ({ board: b, empty: +(f.gap * 100).toFixed(0), t: +f.t.toFixed(2) })) });
  document.body.appendChild(pre);
} catch (e) {
  const pre = document.createElement("pre");
  pre.id = "size-result";
  pre.textContent = JSON.stringify({ error: String(e && e.stack || e) });
  document.body.appendChild(pre);
} })();
</script>
"""


def run(player: Path) -> dict:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the readability check needs a browser")
    harness = player.with_name("player_size.html")
    html = player.read_text(encoding="utf-8")
    script = (HARNESS.replace("__WIDTH__", str(WIDTH)).replace("__FRAMEH__", str(FRAME_H))
              .replace("__RUN__", str(RUNNING_PX)).replace("__LABEL__", str(LABEL_PX))
              .replace("__CONTRAST__", str(CONTRAST)).replace("__HAND__", str(HAND))
              .replace("__WORDS__", str(LABEL_WORDS)).replace("__TOL__", str(TOL_PX))
              .replace("__EMPTY__", str(EMPTY)))
    harness.write_text(html.replace("</body>", script + "</body>"), encoding="utf-8")
    r = subprocess.run([edge, "--headless=new", "--do-not-de-elevate", "--user-data-dir=" + EDGE_PROFILE, "--disable-gpu",
                        f"--window-size={WIDTH + 200},{int(WIDTH * 0.75)}", "--mute-audio",
                        "--virtual-time-budget=60000", "--dump-dom", harness.resolve().as_uri()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="size-result">(.*?)</pre>', r.stdout, re.S)
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
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--dir", type=Path, required=True, help="a built player folder, e.g. generated/lesson-player")
    ap.add_argument("--show", type=int, default=40, help="findings to print")
    a = ap.parse_args()
    res = run(a.dir / "player.html")
    f = res["findings"]
    print(f"{res['frame']}px frame (x{res['scale']} to 1600x900): {res['samples']} moments; {len(f)} finding(s); "
          f"running text >= {RUNNING_PX:g}px, labels >= {LABEL_PX:g}px, contrast >= {CONTRAST:g}:1")
    order = {"small text": 0, "small label": 1, "low contrast": 2, "heading wrap": 3, "empty half": 4}
    for x in sorted(f, key=lambda x: (order[x["kind"]], x["board"], x["t"]))[:a.show]:
        if x["kind"] == "low contrast":
            extra = f"{x['value']}:1 (rgb{tuple(x['fg'])} on rgb{tuple(x['bg'])}, opacity {x['opacity']})"
        elif x["kind"] == "heading wrap":
            extra = f"{x['lines']} lines, one of {x['value']} word(s)"
        elif x["kind"] == "empty half":
            extra = f"{x['value']}% left empty (content {x['height']}% high, {x['width']}% wide)"
        else:
            extra = f"{x['value']}px, needs {x['need']:g}" + (" (hand, at its size / 1.3)" if x.get("hand") else "")
        print(f"  {x['kind'].upper()} {x['board']} at {mmss(x['t'])} {x['block']}: {x['text']!r} {extra}")
    (a.dir / "text_size_check.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    if f:
        raise SystemExit(f"readability check failed: {len(f)} finding(s); see {a.dir / 'text_size_check.json'}")
    print("readability check passed: every text at its minimum size or larger, every line at 4.5:1 or more, no "
          "heading leaves one or two words on a line, no board leaves a large part of itself empty")


if __name__ == "__main__":
    main()
