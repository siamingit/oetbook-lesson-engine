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

# Headless Edge runs with its own profile, removed on exit: with the default one,
# a run could be handed to an Edge window already open and never return
# (the layout check's 900 s time-outs on Grammar 6, 2026-09-27).
EDGE_PROFILE = tempfile.mkdtemp(prefix="oet-edge-")
atexit.register(shutil.rmtree, EDGE_PROFILE, True)

EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
WIDTHS = {"phone": 812, "laptop": 1120}
TOLERANCE_PX = 1.0
TABLE_FONT_MIN = 1.9          # cqh: docs/02-DESIGN-SYSTEM.md §7, Tables

HARNESS = r"""
<script>
(function () {
  window.__lockWidth = __WIDTH__;
  fit();
  camEl.classList.remove("glide");
  const style = document.createElement("style");
  style.textContent = "*{transition:none!important;animation:none!important}";
  document.head.appendChild(style);
  const TOL = __TOL__, FMIN = __FMIN__, INIT = __INIT__, PMAX = __PMAX__, PMIN = __PMIN__;
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
  const clears = {}, unfit = [];
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
  // boards where the camera may pan to show a table's notes: only after the
  // table's text is at its floor and the notes still do not fit (ADR 020)
  const panOk = new Set();
  function fitBoard(bd) {
    const unfitBefore = unfit.length;
    for (const s of bd.states) { s.clears = []; delete clears[s.id]; }
    drawnBoard = null;
    // 1. the fixed content alone: a table too tall gets smaller text
    for (const s of bd.states.slice(0, 1)) {
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
        show(t);
        if (!outside().length) continue;
        if (!(clears[s.id] || []).includes(n) && clearBefore(n)) show(t);
        const still = outside();
        if (still.length) unfit.push({ board: bd.id, state: s.id, block: n, why: "outside after clearing",
                                        items: still.map(([i, px]) => [i, Math.round(px)]) });
      }
    }
    return unfit.length > unfitBefore;
  }
  for (const bd of boards) {
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
  pre.textContent = JSON.stringify({ clears, fonts, unfit, tight, pics });
  document.body.appendChild(pre);
})();
</script>
"""


def run(player: Path, width: int, init: dict) -> dict:
    edge = next((e for e in EDGE if Path(e).exists()), None)
    if not edge:
        raise SystemExit("Edge not found; the fit needs a browser")
    harness = player.with_name("player_fit.html")
    html = player.read_text(encoding="utf-8")
    script = (HARNESS.replace("__WIDTH__", str(width)).replace("__TOL__", str(TOLERANCE_PX))
              .replace("__FMIN__", str(TABLE_FONT_MIN)).replace("__PMAX__", "20").replace("__PMIN__", "10").replace("__INIT__", json.dumps(init)))
    harness.write_text(html.replace("</body>", script + "</body>"), encoding="utf-8")
    r = subprocess.run([edge, "--headless=new", "--user-data-dir=" + EDGE_PROFILE, "--disable-gpu", f"--window-size={width + 200},{int(width * 0.75)}",
                        "--virtual-time-budget=60000", "--dump-dom", harness.resolve().as_uri()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
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
    a = ap.parse_args()
    # measured on a player built without any fit, so the plan is made from
    # scratch every time (a table already made smaller would look as if it fitted)
    folder = build(a.lesson_dir, silent=a.silent, out="lesson-fit", use_fit=False)
    plan: dict = {"clears": {}, "fonts": {}, "tight": {}, "pics": {}}
    unfit: list = []
    for name, width in WIDTHS.items():
        res = run(folder / "player.html", width, plan)
        plan = {"clears": res["clears"], "fonts": res["fonts"], "tight": res["tight"],
                "pics": res.get("pics") or {}}
        unfit = res["unfit"]                  # the last width saw every earlier plan applied
        n = sum(len(v) for v in res["clears"].values())
        print(f"{name}: {n} clear(s) in {len(res['clears'])} state(s), {len(res['fonts'])} table size(s), "
              f"{len(res['tight'])} tight board(s), "
              f"{len(res['unfit'])} still outside")
    shutil.rmtree(folder, ignore_errors=True)
    out = a.lesson_dir / "analysis" / "fit.json"
    prev = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
    doc = {"purpose": "Where a state's notes are cleared so the next fits the board, and a table's text "
                      "size where it did not fit (fit_boards.py; ADR 011). Read by build_lesson_player.py.",
           "clears": dict(sorted(plan["clears"].items())), "fonts": dict(sorted(plan["fonts"].items())),
           "pics": dict(sorted(plan["pics"].items())),
           "tight": dict(sorted(plan["tight"].items())),
           "unfit": unfit}
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    changed = prev is None or {k: prev.get(k) for k in ("clears", "fonts", "tight", "pics")} != {k: doc[k] for k in ("clears", "fonts", "tight", "pics")}
    print(f"wrote {out}" + (" (changed: rebuild the player)" if changed else " (unchanged)"))
    for u in unfit:
        print("  UNFIT", json.dumps(u, ensure_ascii=False))


if __name__ == "__main__":
    main()
