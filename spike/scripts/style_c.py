"""Style C, "soft notebook": the lesson look the owner chose on 2026-10-26 (ADR 042).

A lesson is in style C when its `analysis/sections.json` says so (`lesson.style`
"c", set by `build_sections.py --style c`). Nothing else turns it on, so every
lesson built before keeps its look byte for byte (its blocks.css, its bundle and
its player) until the owner decides otherwise.

What this module holds:

- `CSS`: the look, appended to the lesson's own `blocks.css` (write_screens.frame_css).
  Every rule keys on the classes and attributes the block html carries and the
  ones every player already sets (`.on`, `.spot`, `tr.focus`, `td.active`,
  `.v-right`, `data-layer` / `data-oa-layer`), plus one class a 1.22 player sets
  from the bundle (`fx-lift`, rule 54). The site plays the static look with no
  change of its own.
- `tone_html`: a table's column label takes the colour of what it means (Wrong in
  red, Accurate or Right in teal), as a `data-tone` attribute on its `<th>`.
- `effects`: when a block is lifted and when the view zooms onto a line of a
  document, from the bundle's own times (docs/02-DESIGN-SYSTEM.md §8g, "Where
  each effect is used"); written into each state as `effects` (bundle 1.22).
- `font_css`: IBM Plex Sans for the reference player, embedded from a pinned,
  hash-checked local copy (the site serves its own copy of the same font).
"""

import base64
import hashlib
import json
import os
import re
from pathlib import Path

STYLES = ("c",)
FORMAT_VERSION = "1.22"            # bundle format of a style C lesson (ADR 042)
REPO = Path(__file__).resolve().parents[2]
FONT_LOCK = REPO / "spike" / "fonts" / "ibm-plex-sans.lock.json"


def style_of(lesson) -> str | None:
    """The lesson's style: `lesson.style` in its sections.json, or None (the look
    of every lesson built before 2026-10-26)."""
    if not lesson:
        return None
    p = Path(lesson) / "analysis" / "sections.json"
    if not p.exists():
        return None
    try:
        v = (json.loads(p.read_text(encoding="utf-8")).get("lesson") or {}).get("style")
    except (ValueError, OSError):
        return None
    if v is None:
        return None
    if v not in STYLES:
        raise SystemExit(f"REFUSED: sections.json lesson.style {v!r} is not a style ({', '.join(STYLES)})")
    return v


# ---------------------------------------------------------------------------
# The look (issue #46; docs/02-DESIGN-SYSTEM.md §1a). Sizes are shares of the
# frame's height, as everywhere (§4): the issue's pixels are at a 720 px frame,
# so 16 px is 2.2cqh, 20 px 2.8cqh, 24 px 3.3cqh, 44 px 6.1cqh, 12 px 1.7cqh,
# 10 px 1.4cqh. Body text keeps its 3.2% and its floors (§3, §8b).
# ---------------------------------------------------------------------------
CSS = """
/* --- Style C, "soft notebook" (ADR 042; docs/02-DESIGN-SYSTEM.md §1a) --- */
.frame{--sc-ground:#f3f0fb;--sc-ink:#1c1733;--sc-muted:#4a4466;--sc-muted2:#6b6585;--sc-faint:#a49fbc;
  --sc-line:#eeeaf7;--sc-amber:#ffd27a;--sc-mk-teal:#b8ece4;--sc-mk-blue:#c8dcfa;
  --sc-wrong:#b83b28;--sc-wrong-bg:#fde5e0;--sc-right:#0f766e;--sc-right-bg:#d7f0ec;
  --sc-violet:#5b3fc4;--sc-violet-bg:#ece6fb;--sc-amber-ink:#8a5300;--sc-amber-bg:#ffe9c7;
  --sc-blue:#1d5fb4;--sc-blue-bg:#e2eefb;--sc-lilac:#c9bdf5;
  --sc-shadow:0 1.4cqh 4.2cqh rgba(91,63,196,.18);
  background:var(--sc-ground);color:var(--sc-ink);border-color:#e4def5;
  font-family:var(--font-plex,"IBM Plex Sans"),system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.hdr{background:var(--sc-ground);border-bottom:0;font-weight:700;color:var(--sc-ink)}
.body{background:var(--sc-ground)}
.ctl{background:var(--sc-ground);border-top:0;color:var(--sc-muted)}
.ctl .bar{background:#e4def5}
#cam{box-sizing:border-box}
/* notes and slide sentences: white cards on the ground, no borders, no left bars */
.plain.role-note,.plain.beside{background:#fff;border:0;border-radius:2.8cqh;padding:1.6cqh 2.4cqw}
.plain.role-slide{background:#fff;border:0;color:var(--sc-ink);border-radius:3.3cqh;padding:2.2cqh 2.8cqw;
  font-weight:400;line-height:1.5}
.ltitle{font-weight:700;color:var(--sc-ink);letter-spacing:-.005em}
/* a wrong and a right sentence: the tint and ink of their meaning, the cross or
   tick kept in a soft square (colour is never the only signal, §5) */
.row{border-left:0;border-radius:2.2cqh;align-items:center}
.err{background:var(--sc-wrong-bg);color:var(--sc-wrong)}
.ans{background:var(--sc-right-bg);color:var(--sc-right)}
.row .verdict{width:4.6cqh;height:4.6cqh;border-radius:1.3cqh;background:#fff;font-weight:700;font-size:2.6cqh}
.err .verdict{background:#fff;color:var(--sc-wrong)} .ans .verdict{background:#fff;color:var(--sc-right)}
.row.result{background:#fff;border:0;color:var(--sc-ink);border-radius:2.8cqh}
.row.result .verdict{background:var(--sc-right-bg);color:var(--sc-right)}
/* callouts: a white card with a soft badge; a warning in the red of "leave out",
   a key rule in the amber of the key point */
.callout{background:#fff;border-left:0;border-radius:2.8cqh;color:var(--sc-ink)}
.callout.warning,.callout.key_rule{background:#fff;color:var(--sc-ink)}
.badge-c{width:4.6cqh;height:4.6cqh;border-radius:1.3cqh;font-weight:700}
.warning .badge-c{background:var(--sc-wrong-bg);color:var(--sc-wrong)}
.key_rule .badge-c{background:var(--sc-amber-bg);color:var(--sc-amber-ink)}
/* the definition, "Meaning" and "Word": a dark card, white text, an amber chip */
.defpill{background:var(--sc-ink);color:#fff;border-radius:2.8cqh;padding:1.3cqh 2.2cqw 1.3cqh 1.3cqh;
  font-size:2.9cqh;gap:1.6cqw}
.defpill .defterm{background:var(--sc-amber);color:var(--sc-ink);font-weight:700;border-radius:1.4cqh;
  padding:.5cqh 1.4cqw}
.gl{background:var(--sc-ink);color:#fff;border-left:0;border-radius:2.8cqh}
.gl-txt::before{content:"Word";display:inline-block;background:var(--sc-amber);color:var(--sc-ink);
  font-size:1.9cqh;line-height:1.3;font-weight:700;border-radius:1.4cqh;padding:.3cqh 1cqw;margin-bottom:.8cqh}
.gl-w{font-weight:700}
.gl-m::before,.gl-x::before{color:var(--sc-faint)}
.gl-pic{background:#fff;border-radius:2cqh;padding:.8cqh;box-sizing:border-box}
/* a term with its tag: a white card, the tag a small violet chip in sentence case */
.term.tnote,.term.role-note{background:#fff;border-left:0;border-radius:2.8cqh;color:var(--sc-ink)}
.term .lbl,.term.tnote .lbl{display:inline-block;background:var(--sc-violet-bg);color:var(--sc-violet);
  font-size:1.9cqh;line-height:1.3;font-weight:700;letter-spacing:.01em;border-radius:1.4cqh;padding:.3cqh 1cqw;
  margin-bottom:.6cqh}
.term .t{font-weight:600}
/* change cards */
.chg{background:#fff;border:0;border-radius:2.8cqh}
.chg .chg-cap{color:var(--sc-muted2);font-weight:600}
.chg-arrow path{stroke:var(--sc-faint)}
/* a small table written while teaching: a white card, its column labels in
   letter-spaced capitals (§6 as amended by ADR 042) */
.tbl:not(.core){background:#fff;border-radius:2.8cqh;overflow:hidden;padding:.6cqh 0}
.tbl:not(.core) th{background:transparent;color:var(--sc-muted2);font-size:2.1cqh;font-weight:700;
  letter-spacing:.06em;text-transform:uppercase;padding:.8cqh 2cqw}
.tbl:not(.core) td{border-bottom:0;border-top:1px solid var(--sc-line)}
/* a slide's table, the board's core: column labels above white row cards on the
   ground; the spotlight lifts the row being taught and fades the others to half
   (rule 11 in style C: §7, Tables) */
.tbl.core,.tbl.core.role-slide{background:transparent;border:0;border-radius:0;overflow:visible}
.tbl.core table{border-collapse:separate;border-spacing:0 .8cqh}
.tbl.core th,.tbl.core.role-slide th{background:transparent;color:var(--sc-muted2);border:0;
  font-size:2.1cqh;line-height:1.25;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
  padding:.2cqh 1.6cqw 0;vertical-align:bottom}
.tbl th[data-tone="wrong"],.tbl.core.role-slide th[data-tone="wrong"]{color:var(--sc-wrong)}
.tbl th[data-tone="right"],.tbl.core.role-slide th[data-tone="right"]{color:var(--sc-right)}
.tbl.core td[data-tone="wrong"]{color:var(--sc-wrong)}
.tbl.core td[data-tone="right"],.tbl.core td[data-tone="right"] .tw{color:var(--sc-right)}
.tbl.core td{background:#fff;border:0;padding:1cqh 1.6cqw}
.tbl.core td:first-child{border-radius:2.2cqh 0 0 2.2cqh} .tbl.core td:last-child{border-radius:0 2.2cqh 2.2cqh 0}
.tbl.core td:only-child{border-radius:2.2cqh}
.tbl.core tbody tr{transition:transform .25s cubic-bezier(.2,.7,.2,1),box-shadow .25s ease}
.tbl.core.spot tbody tr:not(.focus) td{opacity:.5}
.tbl.core.spot tbody tr.focus{position:relative;z-index:1;box-shadow:var(--sc-shadow);
  transform:scale(calc(1 + .015 * var(--sc-motion, 1)))}
.tbl.core.spot tbody tr.focus td{box-shadow:inset 0 .35cqh 0 var(--sc-lilac),inset 0 -.35cqh 0 var(--sc-lilac)}
.tbl.core.spot tbody tr.focus td:first-child{box-shadow:inset .35cqh .35cqh 0 var(--sc-lilac),inset 0 -.35cqh 0 var(--sc-lilac)}
.tbl.core.spot tbody tr.focus td:last-child{box-shadow:inset -.35cqh .35cqh 0 var(--sc-lilac),inset 0 -.35cqh 0 var(--sc-lilac)}
.tbl.core.spot tbody tr.focus td:only-child{box-shadow:inset 0 0 0 .35cqh var(--sc-lilac)}
.tbl.core.spot tbody tr.focus td[data-tone="wrong"]{background:var(--sc-wrong-bg)}
.tbl.core td.active,.tbl.core.spot tbody tr.focus td.active{background:#fff4dc;box-shadow:inset 0 0 0 .3cqh var(--sc-amber)}
.tbl.core .tw{color:var(--sc-blue)}
.tbl.core td.v-wrong{opacity:.45;color:var(--sc-wrong)}
.tbl.core td.v-right{background:var(--sc-right-bg)}
.tbl.core td.v-right::after{background:var(--sc-right);border-radius:.9cqh}
/* the contents board: every part on one board, in two columns of white rows
   beside the board's picture (design system §2, a short list fits on one
   board); each number a soft square in one of five tints, in turn */
#cam:has(> .blk.citem){padding-left:24cqh;column-gap:1.6cqw;row-gap:1.3cqh}
#cam:has(> .blk.citem) > .blk.pic{position:absolute;left:0;top:0;margin:0}
#cam > .blk.citem{flex:0 0 calc(50% - .8cqw);box-sizing:border-box;background:#fff;border-radius:2.2cqh;
  padding:1.3cqh 1.4cqw;align-items:center;gap:1.4cqw;line-height:1.3}
.citem .cnum{width:6.1cqh;height:6.1cqh;border-radius:1.7cqh;font-size:2.6cqh;font-weight:700;margin-top:0;
  background:var(--sc-violet-bg);color:var(--sc-violet)}
.citem .cnum[data-n="2"],.citem .cnum[data-n="7"],.citem .cnum[data-n="12"]{background:var(--sc-amber-bg);color:var(--sc-amber-ink)}
.citem .cnum[data-n="3"],.citem .cnum[data-n="8"],.citem .cnum[data-n="13"]{background:var(--sc-right-bg);color:var(--sc-right)}
.citem .cnum[data-n="4"],.citem .cnum[data-n="9"],.citem .cnum[data-n="14"]{background:var(--sc-wrong-bg);color:var(--sc-wrong)}
.citem .cnum[data-n="5"],.citem .cnum[data-n="10"],.citem .cnum[data-n="15"]{background:var(--sc-blue-bg);color:var(--sc-blue)}
.citem .ct{font-weight:600;font-size:3cqh}
.citem .cs{font-size:2.2cqh;color:var(--sc-muted2)}
.citem .cs:empty{display:none}
/* motion (§8g): a new block fades in and rises a little; a lifted block grows
   a little and takes the shadow and a lilac outline (rule 54, the class
   fx-lift a 1.22 player sets from the bundle). Every motion is 150 to 400 ms,
   eased, never bouncy; none under reduced motion. --sc-motion is 0 only in the
   engine's measuring checks, which measure the board at rest. */
@keyframes sc-rise{from{opacity:0;transform:translateY(1.2cqh)}to{opacity:1;transform:none}}
.blk.on:not([data-layer="fixed"]):not([data-oa-layer="fixed"]){animation:sc-rise .3s cubic-bezier(.2,.7,.2,1) backwards}
.blk{transition:opacity .25s ease,transform .25s cubic-bezier(.2,.7,.2,1),box-shadow .25s ease !important}
.blk.fx-lift{position:relative;z-index:2;transform:scale(calc(1 + .02 * var(--sc-motion, 1)));
  box-shadow:var(--sc-shadow);outline:.4cqh solid var(--sc-lilac);outline-offset:0}
@media (prefers-reduced-motion: reduce){
  .blk.on:not([data-layer="fixed"]):not([data-oa-layer="fixed"]){animation:none}
  .blk{transition:opacity .25s ease !important}
  .blk.fx-lift,.tbl.core.spot tbody tr.focus{transform:none}
  .tbl.core tbody tr{transition:none}
}
"""

# A column label's meaning, by its words (sentence case in the data; drawn in
# capitals). Only labels that say right or wrong take a colour (§5).
TONE_WORDS = {"wrong": ("wrong", "wrong version", "not accurate", "inaccurate", "leave out", "avoid"),
              "right": ("accurate", "right", "correct", "right version", "correct version", "better",
                        "keep")}
TH = re.compile(r"<th>([^<]*)</th>")
TD = re.compile(r'<td data-col="(\d+)"')


def tone_html(html: str) -> str:
    """A table's column labels that say wrong or right take `data-tone`, so the
    stylesheet draws them in red or teal (issue #46: "Wrong in #b83b28, Accurate /
    right in #0f766e"); on a core table each cell of that column takes it too
    (its `data-col`), so the wrong sentences are in the red of "wrong" and the
    right ones in the teal of "right". No word changes."""
    if "<th>" not in html:
        return html
    tones = {}

    def one(m):
        w = m.group(1).strip().lower()
        n = len(tones_seen)
        tones_seen.append(None)
        for tone, words in TONE_WORDS.items():
            if w in words:
                tones[n] = tone
                return f'<th data-tone="{tone}">{m.group(1)}</th>'
        return m.group(0)
    tones_seen: list = []
    html = TH.sub(one, html)
    if tones:
        html = TD.sub(lambda m: (m.group(0) + f' data-tone="{tones[int(m.group(1))]}"')
                      if int(m.group(1)) in tones else m.group(0), html)
    return html


# ---------------------------------------------------------------------------
# Effects with data (bundle 1.22, rules 54 and 55). Everything else that moves in
# style C moves on data every bundle already has (the spotlight, reveals, marks,
# erases and clears; rule 53). See docs/02-DESIGN-SYSTEM.md §8g for why these and
# not more.
# ---------------------------------------------------------------------------
LIFT_LEAD = 0.15        # s before the first word read
LIFT_HOLD = 0.6         # s after the last word read, then it settles
LIFT_JOIN = 1.5         # reading runs this close on one block are one lift
LIFT_MIN = 0.8          # s; a shorter lift is not worth the motion
ZOOM_BODY = 3.2         # cqh: a document line is brought up to body size (§4)
ZOOM_SMALL = 2.8        # cqh: a document set this small or smaller (or shown whole) is zoomed
ZOOM_HOLD = 0.4         # s the view stays on the line after its sentence ends
ZOOM_MIN = 0.5          # s; a shorter zoom is not worth the motion


def _r(x: float) -> float:
    return round(x + 0.0, 3)


def effects(boards: list[dict], blocks: dict) -> None:
    """Write each state's `effects` (bundle 1.22), in time order:

    lift  a block grows a little, with the shadow and the lilac outline, from
          `time` to `until` (rule 54):
          - each item of the contents board, from when it is named (its reveal)
            until the next is named; the last until the end of what is said with
            it, at most to its state's end;
          - on a board whose fixed layer holds two or more sentences or cards that
            are not a table, each of them while the narration reads it aloud (its
            reading runs, from just before the first word to just after the last,
            runs under 1.5 s apart joined).
    zoom  the view zooms onto the words `text` in row `row` (cell `col`) of the
          core table `block`, a document set well under body size (its `font`
          2.8 or less, or a board shown whole), from a mark the narration draws on
          that line until it moves on to a note (the next block revealed) or the
          sentence ends (0.4 s held), and back out; a later mark on the table
          takes the view on from there (rule 55).
    """
    for bd in boards:
        fixed_txt = [i for i in bd["fixed"] if blocks[i]["type"] not in ("table", "picture", "lesson_title")]
        tbl = bd.get("table")
        doc = None
        if tbl and not bd.get("split") and not bd.get("listen") and not blocks[tbl].get("map"):
            f = blocks[tbl].get("font")
            if bd.get("fit") == "whole" or (f is not None and f <= ZOOM_SMALL):
                doc = tbl
        for s in bd["states"]:
            fx = []
            # the contents board's items, each lifted while it is named
            items = sorted(((at, w) for w, at in s["reveal"].items()
                            if w in blocks and blocks[w]["type"] == "contents_item"), key=lambda x: x[0])
            for n, (at, w) in enumerate(items):
                if n + 1 < len(items):
                    until = items[n + 1][0]
                else:
                    ends = [u["end"] for u in s["utterances"] if u["start"] <= at + 1e-6 <= u["end"] + 0.5]
                    until = min(s["until"], (max(ends) if ends else at + 2.0) + LIFT_HOLD)
                if until - at >= LIFT_MIN:
                    fx.append({"type": "lift", "block": w, "time": _r(at), "until": _r(until)})
            # two or more fixed sentences or cards: each lifted while it is read
            if len(fixed_txt) >= 2:
                for b in fixed_txt:
                    spans = []
                    for u in s["utterances"]:
                        for r in u.get("reading") or []:
                            if r["block"] == b and r["words"]:
                                spans.append([r["words"][0][1] - LIFT_LEAD, r["words"][-1][2] + LIFT_HOLD])
                    spans.sort()
                    joined = []
                    for a, z in spans:
                        if joined and a - joined[-1][1] < LIFT_JOIN:
                            joined[-1][1] = max(joined[-1][1], z)
                        else:
                            joined.append([a, z])
                    for a, z in joined:
                        a, z = max(a, s["start"]), min(z, s["until"])
                        if z - a >= LIFT_MIN:
                            fx.append({"type": "lift", "block": b, "time": _r(a), "until": _r(z)})
            # a document's line zoomed while the narration is on it: from a mark on
            # the line until the narration moves on to a note (the next block
            # revealed), or its sentence ends; the next mark takes the view on
            if doc:
                reveals = sorted(at for w, at in s["reveal"].items() if w in s["working"])
                zs = []
                for u in s["utterances"]:
                    for c in u["cues"]:
                        if c.get("block") != doc or c["type"] in ("reveal", "pause", "type", "play") \
                                or c.get("row") is None:
                            continue
                        until = min([s["until"], u["end"] + ZOOM_HOLD]
                                    + [at for at in reveals if at > c["time"] + 1e-6])
                        zs.append({"type": "zoom", "block": doc, "row": c["row"], "col": c.get("col"),
                                   "text": c.get("text"), "time": max(c["time"], s["start"]), "until": until})
                zs.sort(key=lambda e: e["time"])
                for a, b in zip(zs, zs[1:]):
                    a["until"] = min(a["until"], b["time"])
                for e in zs:
                    if e["until"] - e["time"] >= ZOOM_MIN:
                        fx.append({**e, "time": _r(e["time"]), "until": _r(e["until"])})
            fx.sort(key=lambda e: (e["time"], e["type"], e["block"]))
            s["effects"] = fx


# ---------------------------------------------------------------------------
# IBM Plex Sans for the reference player (player.html only; never in the bundle).
# ---------------------------------------------------------------------------
def font_dir() -> Path:
    lock = json.loads(FONT_LOCK.read_text(encoding="utf-8"))
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "oet-fonts"
    return base / f"{lock['package'].split('/')[-1]}-{lock['version']}"


def fetch_fonts() -> Path:
    """Download the pinned font files into the local cache, each checked against
    the lock's SHA-256; a file that does not match is refused and removed."""
    import urllib.request
    lock = json.loads(FONT_LOCK.read_text(encoding="utf-8"))
    d = font_dir()
    d.mkdir(parents=True, exist_ok=True)
    for f in lock["files"]:
        p = d / f["name"]
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"]:
            url = lock["base_url"] + f["name"]
            with urllib.request.urlopen(url, timeout=60) as r:       # noqa: S310 (a pinned https URL)
                data = r.read()
            if hashlib.sha256(data).hexdigest() != f["sha256"]:
                raise SystemExit(f"REFUSED: {url} does not match the lock's SHA-256")
            p.write_bytes(data)
    return d


def font_css() -> str:
    """@font-face rules for IBM Plex Sans 400 to 700, latin and latin-ext, the
    files embedded as data: URLs (a file:// page cannot load a font beside it).
    Refused when a file is missing or does not match its pinned hash: run
    `style_c.py --fetch-fonts` once."""
    lock = json.loads(FONT_LOCK.read_text(encoding="utf-8"))
    d = font_dir()
    out = []
    for f in lock["files"]:
        p = d / f["name"]
        if not p.exists():
            raise SystemExit(f"REFUSED: {p} is missing: run spike/scripts/style_c.py --fetch-fonts")
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() != f["sha256"]:
            raise SystemExit(f"REFUSED: {p} does not match the lock's SHA-256")
        out.append("@font-face{font-family:\"IBM Plex Sans\";font-style:normal;font-display:block;"
                   f"font-weight:{f['weight']};unicode-range:{lock['unicode_range'][f['subset']]};"
                   f"src:url(data:font/woff2;base64,{base64.b64encode(data).decode()}) format(\"woff2\")}}")
    return "/* IBM Plex Sans (SIL OFL 1.1), the reference player's copy (ADR 042) */\n" + "\n".join(out) + "\n"


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--fetch-fonts"]:
        print(f"fonts in {fetch_fonts()}")
    else:
        raise SystemExit("usage: style_c.py --fetch-fonts")
