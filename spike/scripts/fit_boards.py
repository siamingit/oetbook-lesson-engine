"""Fit every board to the board area: where to clear a state's notes, and a
table's text size, measured in the real player.

    .venv/Scripts/python spike/scripts/fit_boards.py <lesson_dir>

Rule (maintainer, 2026-09-27; docs/adr/011-boards-fit.md): every block lies
inside the board in every state, and no word moves between states. The layout
stage plans states from estimated heights; the drawn heights can be taller (a
wrapped header, a clause diagram, a note beside a table row). So the plan is
checked where it is drawn: the player is driven, in headless Edge, through
every state, note by note in the order the narration reveals them. When a note
appears and something shown lies outside the board, the notes of the state
shown before it are cleared as it appears, as a teacher wipes the board to
write the next thing (a fixed or pinned block is never cleared, and holds its
place). A board whose note still does not fit after clearing is made tight,
on the whole board so nothing moves between its states: first half the gap
between its blocks, then also half the blocks' own vertical padding. When a board's fixed content alone does not fit (a table), the
table's text is made smaller, to no less than the design system's floor for
tables (1.9% of the frame's height).

Run at phone-landscape width first, then at laptop width with the phone's plan
applied; the union is written to <lesson>/analysis/fit.json:

    {"clears": {"<state id>": ["<block id>", ...]},   # clear before each
     "fonts": {"<block id>": <text size, cqh>},
     "tight": {"<board id>": 1 or 2},                # 1: half the gaps; 2: and half the padding
     "unfit": [...]}                                  # what still does not fit

build_lesson_player.py reads it into the bundle (format 1.8: a state's
`clears`, a table block's `font`); check_overflow.py proves the result.
Nothing spoken changes, no audio is made, and every id stays the same.
"""

import argparse
import json
import re
import shutil
import subprocess
import atexit
import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_lesson_player import build          # noqa: E402
from write_screens import has_part_b, has_part_c    # noqa: E402

# Headless Edge runs with its own profile, removed on exit: with the default one,
# a run could be handed to an Edge window already open and never return
# (the layout check's 900 s time-outs on Grammar 6, 2026-09-27).
EDGE_PROFILE = tempfile.mkdtemp(prefix="oet-edge-")
atexit.register(shutil.rmtree, EDGE_PROFILE, True)

EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
WIDTHS = {"phone": 812, "laptop": 1120}
# the frame the reference player draws in a phone held landscape, 915x412: its
# controls keep 44 px, 13% of this frame, so the board is shorter (maintainer,
# 2026-10-08). Fitted for every lesson fitted from 2026-10-08 on, and a lesson
# opted in with --small-phone; a lesson fitted before keeps its plan until then
SMALL_PHONE = {"small phone": 590}
# 1.16: a Part B question board is also fitted with the fonts other devices draw
# for `system-ui` (Arial standing for Helvetica and San Francisco, Roboto for
# Android); a wider font is the player's guard's (check_wide_font.py)
QBOARD_FONTS = ["Arial", "Roboto"]
TOLERANCE_PX = 1.0
TABLE_FONT_MIN = 1.9          # cqh: docs/02-DESIGN-SYSTEM.md §7, Tables
# 1.16, a Part B question board (ADR 026, 2026-10-08): the extract's share of the
# board's width, per cent, tried from the widest down (the question column takes
# the room it needs, the extract the rest); its size, body size down to a floor
QBOARD_SPLITS = list(range(75, 34, -1))
QBOARD_FONT = 3.2             # cqh: body size (docs/02-DESIGN-SYSTEM.md §4)
QBOARD_FONT_MIN = 2.6         # cqh: the maintainer's floor for the extract

HARNESS = r"""
<script>
(function () {
  window.__lockWidth = __WIDTH__;
  window.__noGuard = true;            // 1.16: the fit measures the board itself, not the player's guard
  const style = document.createElement("style");
  style.textContent = "*{transition:none!important;animation:none!important}"
    + (__FONT__ ? ".frame,.frame *{font-family:" + __FONT__ + "!important}" : "");
  document.head.appendChild(style);
  fit();
  camEl.classList.remove("glide");
  const TOL = __TOL__, FMIN = __FMIN__, INIT = __INIT__, PMAX = __PMAX__, PMIN = __PMIN__;
  const SPLITS = __SPLITS__, QTOP = __QTOP__, QMIN = __QMIN__, QONLY = __QONLY__, NOQ = __NOQ__;
  const body = camEl.parentElement;
  function area() {
    const r = body.getBoundingClientRect(), cs = getComputedStyle(body);
    return { t: r.top + parseFloat(cs.paddingTop), b: r.bottom - parseFloat(cs.paddingBottom),
             l: r.left + parseFloat(cs.paddingLeft), r: r.right - parseFloat(cs.paddingRight) };
  }
  // what lies outside the board now: [block id, px], the camera's zoom undone
  function outside() {
    const keep = camEl.style.transform;
    // as check_overflow.py: a table board's notes as its camera shows them
    const bd = drawnBoard || null;
    const viewed = bd && panOk.has(bd.id) && bd.table && keep && keep !== "none";
    if (!viewed) camEl.style.transform = "none";
    const A = area(), out = [];
    for (const [id, el] of blockEls) {
      if (viewed && !el.classList.contains("beside")) continue;
      if (columnOnly && bd && id === bd.table) continue;    // 1.16: the question column alone
      if (!el.isConnected || getComputedStyle(el).display === "none") continue;
      if (!(el.dataset.layer === "fixed" || el.classList.contains("on"))) continue;
      const r = el.getBoundingClientRect();
      if (!r.width && !r.height) continue;
      // clipped: only a block that hides what overflows it (as check_overflow)
      const clip = /(hidden|clip|auto|scroll)/.test(getComputedStyle(el).overflowY)
                   ? el.scrollHeight - el.clientHeight : 0;
      const px = Math.max(A.t - r.top, r.bottom - A.b, A.l - r.left, r.right - A.r, clip);
      if (px > TOL) out.push([id, px]);
    }
    camEl.style.transform = keep;
    return out;
  }
  function show(t) { lastRenderT = null; renderFrame(t); }
  const fonts = Object.assign({}, INIT.fonts || {});
  // a pass for the Part B question boards only keeps every other board's plan
  const clears = QONLY || NOQ ? Object.assign({}, INIT.clears || {}) : {}, unfit = [];
  // a table's text size, set on the block and on its drawing
  function setFont(bd, id, f) {
    fonts[id] = +f.toFixed(2);
    blocks[id].font = fonts[id];
    blocks[id].html = blocks[id].html.replace(/--tf:[0-9.]+cqh/, "--tf:" + fonts[id] + "cqh");
    const el = blockEls.get(id);
    if (el) el.style.setProperty("--tf", fonts[id] + "cqh");
  }
  for (const [id, f] of Object.entries(fonts)) if (blocks[id]) {
    blocks[id].font = f; blocks[id].html = blocks[id].html.replace(/--tf:[0-9.]+cqh/, "--tf:" + f + "cqh");
  }
  const tight = Object.assign({}, INIT.tight || {});
  // a board's picture (ADR 021) drawn smaller, to no less than PMIN, where the
  // board does not fit with it at full size; kept for the whole board
  const pics = Object.assign({}, INIT.pics || {});
  function setPic(id, h) {
    pics[id] = +h.toFixed(1);
    blocks[id].size = pics[id];
    blocks[id].html = blocks[id].html.replace(/ style="--ph:[0-9.]+cqh"/, "")
                                     .replace('class="blk pic"', 'style="--ph:' + pics[id] + 'cqh" class="blk pic"');
    const el = blockEls.get(id);
    if (el) el.style.setProperty("--ph", pics[id] + "cqh");
  }
  for (const [id, h] of Object.entries(pics)) if (blocks[id]) setPic(id, h);
  function resetPic(id) {
    delete pics[id];
    blocks[id].size = null;
    blocks[id].html = blocks[id].html.replace(/ style="--ph:[0-9.]+cqh"/, "");
    const el = blockEls.get(id);
    if (el) el.style.removeProperty("--ph");
  }
  // 1.16: a Part B question board's split, the glosses drawn over its question
  // column, and when each of those goes (ADR 026, 2026-10-08)
  const splits = Object.assign({}, INIT.splits || {});
  const overlay = {}, ends = {}, qboards = {};
  let columnOnly = false;
  // boards where the camera may pan to show a table's notes: only after the
  // table's text is at its floor and the notes still do not fit (ADR 020)
  const panOk = new Set();
  function fitBoard(bd) {
    const unfitBefore = unfit.length;
    const qb = isQBoard(bd);
    for (const s of bd.states) {
      s.clears = []; delete clears[s.id];
      if (qb) {                          // 1.16: the plan the phone's width made, then this width's
        s.overlay = [...((INIT.overlay || {})[s.id] || [])];
        overlay[s.id] = s.overlay; delete ends[s.id];
      }
    }
    drawnBoard = null;
    // 1. the fixed content alone: a table too tall gets smaller text (a Part B
    // question board's extract is sized with its split, fitQBoard)
    for (const s of qb ? [] : bd.states.slice(0, 1)) {
      show(Math.max(bd.start, s.start) + 0.001);
      let over = outside().filter(([id]) => bd.fixed.includes(id));
      for (const [id] of over) {
        const b = blocks[id];
        if (b.type !== "table" || !b.core) { unfit.push({ board: bd.id, state: s.id, block: id, why: "fixed block" }); continue; }
        let f = b.font || 2.6;
        while (f > FMIN && outside().some(([i]) => i === id)) {
          setFont(bd, id, Math.max(FMIN, f - 0.05)); f = fonts[id];
          drawnBoard = null; show(Math.max(bd.start, s.start) + 0.001);
        }
        if (outside().some(([i]) => i === id)) unfit.push({ board: bd.id, state: s.id, block: id, why: "table at the smallest size" });
      }
    }
    // 2. each state, note by note in reveal order
    for (const s of bd.states) {
      const pinned = bd.pinned || {};
      const init = (INIT.clears || {})[s.id] || [];
      const notes = s.working.filter(id => !(id in pinned) && s.reveal[id] !== undefined)
                             .sort((a, b) => s.reveal[a] - s.reveal[b]);
      const gone = new Set();
      // a note the narration still marks, points at or reads after `at` is
      // still needed: nothing is cleared then
      const needed = (ids, at) => s.utterances.some(u =>
        u.cues.some(c => c.time >= at && c.type !== "reveal" && c.type !== "pause"
                    && (ids.includes(String(c.block || "").split(".")[0]) || ids.includes(c.to_block)))
        || (u.reading || []).some(r => ids.includes(r.block) && r.words.some(w => w[1] >= at)));
      const clearBefore = (n) => {
        const at = s.reveal[n];
        const ids = s.working.filter(w => !(w in pinned) && !gone.has(w) && s.reveal[w] !== undefined && s.reveal[w] < at);
        if (!ids.length || needed(ids, at)) return false;
        s.clears.push({ time: at, blocks: ids });
        ids.forEach(w => gone.add(w));
        (clears[s.id] = clears[s.id] || []).push(n);
        drawnState = null;
        return true;
      };
      for (const n of notes) {
        if (init.includes(n)) clearBefore(n);
        const t = Math.max(s.reveal[n], s.start) + 0.001;     // a cue's lead can come before its state
        if (t >= s.until) continue;
        // 1.16: a gloss over the question column goes when the next note
        // appears, which would otherwise sit under it
        if (qb && s.overlay.some(o => !gone.has(o) && s.reveal[o] < s.reveal[n]) && !clearBefore(n))
          unfit.push({ board: bd.id, state: s.id, block: n, why: "a gloss over the question column is still needed as the next note appears" });
        show(t);
        if (!outside().length) continue;
        if (!(clears[s.id] || []).includes(n) && clearBefore(n)) show(t);
        let still = outside();
        // 1.16: a gloss that does not fit beside the question is drawn over the
        // question column's foot, never over the extract or another note
        if (still.length && qb && blocks[n].type === "gloss" && !s.overlay.includes(n)) {
          s.overlay.push(n);
          drawnState = null; show(t);
          still = outside();
          const o = blockEls.get(n).getBoundingClientRect();
          for (const [id, el] of blockEls) {
            if (id === n || id in pinned || !(el.dataset.layer === "fixed" || el.classList.contains("on"))
                || getComputedStyle(el).display === "none") continue;
            const r = el.getBoundingClientRect();
            if (r.right > o.left + TOL && r.left < o.right - TOL && r.bottom > o.top + TOL && r.top < o.bottom - TOL)
              unfit.push({ board: bd.id, state: s.id, block: n, why: "a gloss over the question column would cover " + id });
          }
        }
        if (still.length) unfit.push({ board: bd.id, state: s.id, block: n, why: "outside after clearing",
                                        items: still.map(([i, px]) => [i, Math.round(px)]) });
      }
      if (qb) endOverlays(bd, s, needed, gone);
    }
    return unfit.length > unfitBefore;
  }
  // 1.16: a gloss over the question column is shown briefly: it goes before
  // anything of the question under it is read or marked, and never while the
  // narration still needs it (maintainer, 2026-10-08)
  function endOverlays(bd, s, needed, gone) {
    const qs = Object.keys(bd.pinned || {});
    for (const g of s.overlay) {
      if (gone.has(g)) continue;
      const from = s.reveal[g];
      const moments = [];
      for (const u of s.utterances) {
        for (const c of u.cues) if (qs.includes(c.block) && c.type !== "reveal" && c.type !== "pause"
                                    && c.time >= from && c.time < s.until) moments.push([c.time, c]);
        for (const r of u.reading || []) if (qs.includes(r.block))
          for (const w of r.words) if (w[1] >= from && w[1] < s.until) moments.push([w[1], null, r.block, w[0]]);
      }
      moments.sort((a, b) => a[0] - b[0]);
      for (const [at, c, rb, k] of moments) {
        show(at + 0.001);
        const ge = blockEls.get(g);
        if (!ge || !ge.classList.contains("on") || ge.classList.contains("cleared")) break;
        const o = ge.getBoundingClientRect();
        const hit = r => r.right > o.left && r.left < o.right && r.bottom > o.top && r.top < o.bottom;
        let rects = [];
        if (c) { const w = WRAPS.get(c._uid) || WRAPS.get(c._uid + "<"); rects = w ? w.spans.flatMap(sp => [...sp.getClientRects()]) : []; }
        else { const r = wordRect(blockEls.get(rb), k); rects = r ? [r] : []; }
        if (!rects.some(hit)) continue;
        if (needed([g], at))
          unfit.push({ board: bd.id, state: s.id, block: g, why: "a gloss over the question column is still needed when what it covers is read or marked", t: at });
        (ends[s.id] = ends[s.id] || []).push([g, +at.toFixed(3)]);
        s.clears.push({ time: +at.toFixed(3), blocks: [g] });
        s.clears.sort((a, b) => a.time - b.time);
        gone.add(g);
        drawnState = null;
        break;
      }
    }
  }
  // 1.16: a Part B question board's split and extract size (maintainer,
  // 2026-10-08). The question column gets the room it needs at body size: the
  // narrowest column that holds the question and every note (only a gloss may
  // go over it). The extract takes the rest, at the largest size at which it
  // fits whole, from body size down to the floor; it need not be the larger share.
  function extractFits(bd) {
    drawnBoard = null; show(bd.start + 0.001);
    if (!isPCBoard(bd)) return !outside().some(([i]) => i === bd.table);
    // 1.17: a Part C text, a paragraph at a time: each paragraph view whole
    const seen = new Set();
    for (const s of bd.states) {
      if (!s.view || s.view.map || seen.has(s.view.rows.join(","))) continue;
      seen.add(s.view.rows.join(","));
      show(s.start + 0.001);
      if (outside().some(([i]) => i === bd.table)) return false;
    }
    return true;
  }
  function fitQBoard(bd) {
    const tid = bd.table, n0 = unfit.length;
    const pid = (bd.states[0] || { working: [] }).working.find(i => blocks[i] && blocks[i].type === "picture");
    const given = splits[bd.id];
    const tried = [];
    let use = null;
    columnOnly = true;
    let cands = given ? SPLITS.filter(x => x <= given) : SPLITS;
    if (isPCBoard(bd) && cands.length > 2) {
      // 1.17: a Part C board's question column is long; its split is found by
      // halving (the column that fits at a share fits at every smaller one), then
      // tried from there as below; a Part B board is fitted share by share as built
      let lo = 0, hi = cands.length - 1;          // cands run from the widest extract down
      const fitsAt = sp => { bd.split = sp; bd.tight = 2; const n = unfit.length;
                             fitBoard(bd); const ok = unfit.length === n; unfit.length = n; return ok; };
      if (fitsAt(cands[hi])) {
        while (lo < hi) { const mid = (lo + hi) >> 1; if (fitsAt(cands[mid])) hi = mid; else lo = mid + 1; }
        cands = cands.slice(Math.max(0, lo - 1));
      }
    }
    for (const sp of cands) {
      bd.split = sp;
      // the question column, as any board: clears, then tight, then a smaller picture
      if (pid && !(INIT.pics || {})[pid]) resetPic(pid);
      bd.tight = given ? (tight[bd.id] || 0) : 0;
      while (fitBoard(bd) && bd.tight < 2) { unfit.length = n0; bd.tight += 1; }
      while (unfit.length > n0 && pid && (blocks[pid].size || PMAX) > PMIN + 1e-6) {
        unfit.length = n0;
        setPic(pid, Math.max(PMIN, (blocks[pid].size || PMAX) - 2));
        drawnBoard = null;
        fitBoard(bd);
      }
      const ok = unfit.length === n0;
      tried.push({ split: sp, tight: bd.tight, column: ok ? "fits" : unfit.slice(n0).map(u => [u.block, u.why]) });
      unfit.length = n0;
      if (ok) { use = { split: sp, tight: bd.tight, pic: pid ? blocks[pid].size : null }; break; }
    }
    columnOnly = false;
    if (!use) {
      unfit.push({ board: bd.id, why: "no split holds the question column at body size", tried });
      use = { split: SPLITS[SPLITS.length - 1], tight: 2, pic: pid ? PMIN : null };
    }
    bd.split = use.split; splits[bd.id] = use.split;
    bd.tight = use.tight;
    if (use.tight) tight[bd.id] = use.tight; else delete tight[bd.id];
    if (pid) { if (use.pic) setPic(pid, use.pic); else resetPic(pid); }
    // the extract: the largest size at which it fits whole in the rest
    let f = given ? Math.min(QTOP, fonts[tid] || QTOP) : QTOP;
    setFont(bd, tid, f);
    while (!extractFits(bd) && f > QMIN + 1e-6) { f = Math.max(QMIN, +(f - 0.05).toFixed(2)); setFont(bd, tid, f); }
    const whole = extractFits(bd);
    drawnBoard = null;
    fitBoard(bd);                        // the plan for the split chosen
    if (!whole) {
      const el = blockEls.get(tid), A = area();
      unfit.push({ board: bd.id, block: tid, why: "the extract does not fit whole at " + QMIN + "% in the column the question leaves it",
                   split: use.split, extract_px: el ? Math.round(el.getBoundingClientRect().height) : null,
                   board_px: Math.round(A.b - A.t) });
    }
    qboards[bd.id] = { split: use.split, font: f, whole, tight: use.tight, tried };
  }
  for (const bd of boards) {
    if (isQBoard(bd) && NOQ) continue;      // the small phone: the player's guard fits it there
    if (isQBoard(bd)) { fitQBoard(bd); continue; }        // 1.16: its own columns
    if (QONLY) continue;
    bd.tight = tight[bd.id] || 0;
    const n0 = unfit.length;
    // still outside after clearing: the board is made tighter, level by level,
    // and fitted again (1: half the gaps; 2: and half the blocks' padding)
    while (fitBoard(bd) && bd.tight < 2) {
      unfit.length = n0;
      bd.tight += 1; tight[bd.id] = bd.tight;
    }
    // ADR 020: notes go under a table, never over it; where they still do not
    // fit, the table's text is made smaller, to the tables' floor, for the
    // whole board (so no word moves between its states)
    const tid = bd.table && blocks[bd.table] && blocks[bd.table].core ? bd.table : null;
    while (unfit.length > n0 && tid && (blocks[tid].font || 2.6) > FMIN + 1e-6) {
      unfit.length = n0;
      setFont(bd, tid, Math.max(FMIN, (blocks[tid].font || 2.6) - 0.1));
      drawnBoard = null;
      fitBoard(bd);
    }
    const pid = (bd.states[0] || { working: [] }).working.find(i => blocks[i] && blocks[i].type === "picture");
    while (unfit.length > n0 && pid && (blocks[pid].size || PMAX) > PMIN + 1e-6) {
      unfit.length = n0;
      setPic(pid, Math.max(PMIN, (blocks[pid].size || PMAX) - 2));
      drawnBoard = null;
      fitBoard(bd);
    }
    if (unfit.length > n0 && tid) {
      unfit.length = n0;
      panOk.add(bd.id);
      drawnBoard = null;
      fitBoard(bd);
    }
  }
  const pre = document.createElement("pre");
  pre.id = "fit-result";
  pre.textContent = JSON.stringify({ clears, fonts, unfit, tight, pics, splits, overlay, ends, qboards });
  document.body.appendChild(pre);
})();
</script>
"""


def run(player: Path, width: int, init: dict, font: str = "", qonly: bool = False,
        noq: bool = False) -> dict:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the fit needs a browser")
    harness = player.with_name("player_fit.html")
    html = player.read_text(encoding="utf-8")
    script = (HARNESS.replace("__WIDTH__", str(width)).replace("__TOL__", str(TOLERANCE_PX))
              .replace("__FMIN__", str(TABLE_FONT_MIN)).replace("__SPLITS__", json.dumps(QBOARD_SPLITS))
              .replace("__QTOP__", str(QBOARD_FONT)).replace("__QMIN__", str(QBOARD_FONT_MIN))
              .replace("__FONT__", json.dumps(font)).replace("__QONLY__", "true" if qonly else "false")
              .replace("__NOQ__", "true" if noq else "false").replace("__PMAX__", "20").replace("__PMIN__", "10").replace("__INIT__", json.dumps(init)))
    harness.write_text(html.replace("</body>", script + "</body>"), encoding="utf-8")
    r = subprocess.run([edge, "--headless=new", "--user-data-dir=" + EDGE_PROFILE, "--disable-gpu", f"--window-size={width + 200},{int(width * 0.75)}",
                        "--virtual-time-budget=60000", "--dump-dom", harness.resolve().as_uri()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
    harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="fit-result">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit("the harness produced no result; the player did not run")
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")
                      .replace("&lt;", "<").replace("&gt;", ">"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--silent", action="store_true",
                    help="fit the silent preview (no audio yet: the narration gate); the plan "
                         "keys on state and block ids, so the final fit replaces it")
    ap.add_argument("--small-phone", action="store_true",
                    help="also fit the small phone frame (915x412) for a lesson fitted before "
                         "2026-10-08; recorded in fit.json, so later runs keep it")
    a = ap.parse_args()
    out = a.lesson_dir / "analysis" / "fit.json"
    prev = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
    # the small phone frame: every lesson fitted from 2026-10-08 on (no plan yet),
    # one fitted with it before, or one opted in; a lesson fitted before keeps its
    # plan (and so its board) until the maintainer asks
    small = a.small_phone or prev is None or "small phone" in (prev.get("frames") or [])
    frames = {**(SMALL_PHONE if small else {}), **WIDTHS}
    # 1.16: a lesson with Part B question boards fits them also with the other
    # devices' fonts, before each frame's own pass; on the small phone frame its
    # question boards are left to the player's guard (the question column at
    # body size does not leave the extract room at 2.6% there; ADR 026,
    # 2026-10-08), every other board is fitted
    # 1.17: a Part C lesson's question boards are two columns too, fitted the same way
    part_b = has_part_b(a.lesson_dir) or has_part_c(a.lesson_dir)
    passes = []
    for name, width in frames.items():
        small_frame = name in SMALL_PHONE
        if part_b and not small_frame:
            passes += [(f"{name}, {f}", width, f, True, False) for f in QBOARD_FONTS]
        passes.append((name, width, "", False, part_b and small_frame))
    # measured on a player built without any fit, so the plan is made from
    # scratch every time (a table already made smaller would look as if it fitted)
    folder = build(a.lesson_dir, silent=a.silent, out="lesson-fit", use_fit=False)
    plan: dict = {"clears": {}, "fonts": {}, "tight": {}, "pics": {}}
    unfit: list = []
    ends: dict = {}
    qboards: dict = {}
    for name, width, font, qonly, noq in passes:
        res = run(folder / "player.html", width, plan, font, qonly, noq)
        plan = {"clears": res["clears"], "fonts": res["fonts"], "tight": res["tight"],
                "pics": res.get("pics") or {}}
        if res.get("splits"):
            # 1.16: a Part B question board's split and the glosses over its
            # question column; a gloss goes at the earlier of the widths' ends
            plan["splits"] = res["splits"]
            plan["overlay"] = {k: v for k, v in res["overlay"].items() if v}
            for sid, es in res["ends"].items():
                for g, at in es:
                    ends.setdefault(sid, {})[g] = min(at, ends.get(sid, {}).get(g, at))
            qboards[name] = res["qboards"]
        if small:                             # every frame and font: what any of them could not fit
            unfit += [u for u in res["unfit"] if u not in unfit]
        else:
            unfit = res["unfit"]              # the last width saw every earlier plan applied
        n = sum(len(v) for v in res["clears"].values())
        print(f"{name}: {n} clear(s) in {len(res['clears'])} state(s), {len(res['fonts'])} table size(s), "
              f"{len(res['tight'])} tight board(s), "
              f"{len(res['unfit'])} still outside")
        for bid, q in (res.get("qboards") or {}).items():
            print(f"  {bid}: the extract {q['split']}% of the width at {q['font']}% of the frame, "
                  f"tight {q['tight']}{'' if q['whole'] else ', NOT WHOLE'}; the question column first holds "
                  f"everything at {q['split']}% ({len(q['tried'])} split(s) tried)")
    shutil.rmtree(folder, ignore_errors=True)
    doc = {"purpose": "Where a state's notes are cleared so the next fits the board, and a table's text "
                      "size where it did not fit (fit_boards.py; ADR 011). Read by build_lesson_player.py.",
           "clears": dict(sorted(plan["clears"].items())), "fonts": dict(sorted(plan["fonts"].items())),
           "pics": dict(sorted(plan["pics"].items())),
           "tight": dict(sorted(plan["tight"].items())),
           "unfit": unfit}
    if small:
        doc["frames"] = list(frames)
    if plan.get("splits"):                      # 1.16: written only for a lesson with Part B questions
        doc["purpose"] += (" On a Part B question board: the extract's share of the width (splits), the "
                           "glosses drawn over the question column (overlay) and when each goes (ends).")
        doc["splits"] = dict(sorted(plan["splits"].items()))
        doc["overlay"] = dict(sorted(plan["overlay"].items()))
        doc["ends"] = {sid: sorted([g, at] for g, at in v.items()) for sid, v in sorted(ends.items())}
        doc["qboards"] = qboards
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    keys = ("clears", "fonts", "tight", "pics", "splits", "overlay", "ends", "frames")
    changed = prev is None or {k: prev.get(k) for k in keys} != {k: doc.get(k) for k in keys}
    print(f"wrote {out}" + (" (changed: rebuild the player)" if changed else " (unchanged)"))
    for u in unfit:
        print("  UNFIT", json.dumps(u, ensure_ascii=False))


if __name__ == "__main__":
    main()
