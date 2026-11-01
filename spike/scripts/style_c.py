"""Style C, "soft notebook": the lesson look the owner chose on 2026-10-26 (ADR 042),
revised after his review of the same day (ADR 042, amendment of 2026-10-26).

A lesson is in style C when its `analysis/sections.json` says so (`lesson.style`
"c", set by `build_sections.py --style c`). Nothing else turns it on, so every
lesson built before keeps its look byte for byte (its blocks.css, its bundle and
its player) until the owner decides otherwise.

What this module holds:

- `CSS`: the look, appended to the lesson's own `blocks.css` (write_screens.frame_css).
  Every rule keys on the classes and attributes the block html carries and the
  ones every player already sets (`.on`, `.spot`, `tr.focus`, `td.active`,
  `.v-right`, `data-layer` / `data-oa-layer`), plus one class a 1.22 player sets
  from the bundle (`fx-lift`, rule 54). The site plays the static look, the
  layouts included, with no change of its own.
- `tone_html`: a table's column label takes the colour of what it means (Wrong in
  red, Accurate or Right in green), as a `data-tone` attribute on its `<th>`.
- `layout_html`: the board layouts (docs/02-DESIGN-SYSTEM.md §7j) and the six
  criteria's colours, as classes and attributes on the block html, with nothing
  added that a reader or a mark could count as a word.
- `effects`: when a block is lifted and when the view zooms onto a line of a
  document, from the bundle's own times (docs/02-DESIGN-SYSTEM.md §8g, "Where
  each effect is used"); written into each state as `effects` (bundle 1.22).
- `font_css`: IBM Plex Sans for the reference player, embedded from a pinned,
  hash-checked local copy (the site serves its own copy of the same font).
"""

import base64
import hashlib
import html as _html
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


# The look a style C lesson takes (ADR 050): `lesson.look` in its sections.json.
# "teal", the owner's Canva patterns of 2026-11-01, is the base of every lesson
# built or redesigned from then on; a lesson with no look keeps style C's own,
# byte for byte. The bundle does not change: the look is the lesson's stylesheet.
LOOKS = ("teal",)


def look_of(lesson) -> str | None:
    """The lesson's look: `lesson.look` in its sections.json (a style C lesson
    only), or None."""
    if not lesson:
        return None
    p = Path(lesson) / "analysis" / "sections.json"
    if not p.exists():
        return None
    try:
        v = (json.loads(p.read_text(encoding="utf-8")).get("lesson") or {}).get("look")
    except (ValueError, OSError):
        return None
    if v is None:
        return None
    if v not in LOOKS:
        raise SystemExit(f"REFUSED: sections.json lesson.look {v!r} is not a look ({', '.join(LOOKS)})")
    if style_of(lesson) != "c":
        raise SystemExit("REFUSED: sections.json lesson.look in a lesson that is not in style C")
    return v


# ---------------------------------------------------------------------------
# Colour, by meaning (docs/02-DESIGN-SYSTEM.md §1a; the owner's review of
# 2026-10-26: the handouts' tones). Each pair is the ink and its soft tint.
# ---------------------------------------------------------------------------
# right or keep: the handouts' olive green ("modal"), 26.8 (CIEDE2000) from the
# adjective's word-class teal and 26.2 and 21.3 from the "up to now" tense teals,
# so it no longer collides with either (the open item of ADR 042)
RIGHT = ("#556b00", "#eef3d2")
WRONG = ("#b42318", "#fdecea")           # wrong or leave out: the site's danger
GLOSS = ("#8a5300", "#fdf0d5")           # a word card, the key word: the handouts' gloss amber
MARK = "#ffe19c"                          # the marker band, a lighter amber
# The six OET Writing criteria, each with its own colour and its monogram, as on
# the owner's slides (a circle with P, C, C&C, G&S, O&L or L). Four are the
# handouts' tones, two the site's own (its rose and its band teal): the six that
# differ most from each other (15.7 or more) and at least 20 from right, wrong
# and the gloss amber.
CRITERIA = {
    "Purpose": ("purpose", "P", "#1d5fb4", "#e2eefb"),                    # the handouts' blue ("past")
    "Content": ("content", "C", "#be185d", "#fce7f1"),                    # the site's rose
    "Conciseness and Clarity": ("cc", "C&C", "#0f766e", "#d7f0ec"),       # the handouts' teal ("teach")
    "Genre and Style": ("gs", "G&S", "#9d1f8f", "#fbe7f6"),               # the handouts' magenta ("prog")
    "Organisation and Layout": ("ol", "O&L", "#0e4a55", "#dcecef"),       # the site's band teal
    "Language": ("lang", "L", "#5b3fc4", "#ece6fb"),                      # the handouts' violet ("test")
}
CRIT_KEY = {name: k for name, (k, *_rest) in CRITERIA.items()}
CRIT_MONO = {k: m for _n, (k, m, *_r) in CRITERIA.items()}
CRITERION_LABEL = "The criterion"        # a term box naming its section's criterion


def _crit_css() -> str:
    roots = "".join(f"--k-{k}:{ink};--ks-{k}:{soft};" for k, _m, ink, soft in CRITERIA.values())
    sets = "\n".join(f'[data-crit="{k}"]{{--k:var(--k-{k});--ks:var(--ks-{k})}}'
                     for k, *_r in CRITERIA.values())
    return ".frame{" + roots + "}\n" + sets + "\n"


# ---------------------------------------------------------------------------
# The look (docs/02-DESIGN-SYSTEM.md §1a). Sizes are shares of the frame's
# height, as everywhere (§4): pixels at a 720 px frame, so 6 px is .8cqh, 16 px
# 2.2cqh, 20 px 2.8cqh, 24 px 3.3cqh, 44 px 6.1cqh. Body text keeps its 3.2% and
# its floors (§3, §8b). Rules that hold text never become flex or grid
# containers of that text (a marked phrase would become an item of its own and
# move, §8a): only rows (`tr`) and their cells are laid out.
# ---------------------------------------------------------------------------
CSS = r"""
/* --- Style C, "soft notebook" (ADR 042 and its amendment of 2026-10-26;
   docs/02-DESIGN-SYSTEM.md §1a, §7j) --- */
.frame{--sc-ink:#1c1733;--sc-muted:#4a4466;--sc-muted2:#6b6585;--sc-faint:#a49fbc;
  --sc-paper:#f8f4ec;--sc-note:#f3f4f7;--sc-line:#e7e5ee;--sc-mark:""" + MARK + r""";
  --sc-right:""" + RIGHT[0] + r""";--sc-right-bg:""" + RIGHT[1] + r""";
  --sc-wrong:""" + WRONG[0] + r""";--sc-wrong-bg:""" + WRONG[1] + r""";
  --sc-gloss:""" + GLOSS[0] + r""";--sc-gloss-bg:""" + GLOSS[1] + r""";
  --sc-active:#fff0c4;
  --sc-shadow:0 .8cqh 2.8cqh rgba(20,32,31,.12);
  --k:#3d3a52;--ks:#efeef4;
  background:#fff;color:var(--sc-ink);border-color:#e4e3ea;
  font-family:var(--font-plex,"IBM Plex Sans"),system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
""" + _crit_css() + r"""
.hdr{background:#fff;border-bottom:0;font-weight:700;color:var(--sc-ink)}
.body{background:#fff}
.ctl{background:#fff;border-top:0;color:var(--sc-muted)}
.ctl .bar{background:var(--sc-line)}
#cam{box-sizing:border-box}
/* notes on a soft neutral tint; the board's own sentences (its fixed layer, a
   slide's sentence) on paper; no borders, no left bars */
.plain.role-note,.plain.beside{background:var(--sc-note);border:0;border-radius:2.8cqh;padding:1.6cqh 2.4cqw}
.plain.role-slide{background:var(--sc-paper);border:0;
  color:var(--sc-ink);border-radius:3.3cqh;padding:2.2cqh 2.8cqw;font-weight:400;line-height:1.5}
.plain.role-note[data-layer="fixed"],.plain.role-note[data-oa-layer="fixed"]{background:var(--sc-paper)}
.ltitle{font-weight:700;color:var(--sc-ink);letter-spacing:-.005em}
/* a wrong and a right sentence: the tint and ink of their meaning, the cross or
   tick in a solid round badge (colour is never the only signal, §5) */
.row{border-left:0;border-radius:2.2cqh;align-items:center}
.err{background:var(--sc-wrong-bg);color:var(--sc-wrong)}
.ans{background:var(--sc-right-bg);color:var(--sc-right)}
.row .verdict{width:4.6cqh;height:4.6cqh;border-radius:50%;font-weight:700;font-size:2.5cqh;color:#fff}
.err .verdict{background:var(--sc-wrong)} .ans .verdict{background:var(--sc-right)}
.row.result{background:var(--sc-right-bg);border:0;color:var(--sc-ink);border-radius:2.8cqh}
.row.result .verdict{background:var(--sc-right);color:#fff}
/* callouts: a note card with a soft badge; a warning in the red of "leave out",
   a key rule in the amber of the key point */
.callout{background:var(--sc-note);border-left:0;border-radius:2.8cqh;color:var(--sc-ink)}
.callout.warning,.callout.key_rule{background:var(--sc-note);color:var(--sc-ink)}
.badge-c{width:4.6cqh;height:4.6cqh;border-radius:50%;font-weight:700}
.warning .badge-c{background:var(--sc-wrong-bg);color:var(--sc-wrong)}
.key_rule .badge-c{background:var(--sc-gloss-bg);color:var(--sc-gloss)}
/* a word card, "Meaning", "Word": the handouts' gloss amber, a small chip */
.defpill{background:var(--sc-gloss-bg);color:var(--sc-ink);border-radius:2.8cqh;
  padding:1.3cqh 2.2cqw 1.3cqh 1.3cqh;font-size:2.9cqh;gap:1.6cqw}
.defpill .defterm{background:var(--sc-gloss);color:#fff;font-weight:700;border-radius:1.4cqh;padding:.5cqh 1.4cqw}
.gl{background:var(--sc-gloss-bg);color:var(--sc-ink);border-left:0;border-radius:2.8cqh}
.gl-txt::before{content:"Word";display:inline-block;background:var(--sc-gloss);color:#fff;
  font-size:1.9cqh;line-height:1.3;font-weight:700;border-radius:1.4cqh;padding:.3cqh 1cqw;margin-bottom:.8cqh}
.gl-w{font-weight:700;color:var(--sc-gloss)}
.gl-m::before,.gl-x::before{color:#a7783a}
.gl-pic{background:#fff;border-radius:2cqh;padding:.8cqh;box-sizing:border-box}
/* a term with its tag: a note card, the tag a small neutral chip */
.term.tnote,.term.role-note{background:var(--sc-note);border-left:0;border-radius:2.8cqh;color:var(--sc-ink)}
.term .lbl,.term.tnote .lbl{display:inline-block;background:#e6e5ee;color:var(--sc-muted);
  font-size:1.9cqh;line-height:1.3;font-weight:700;letter-spacing:.01em;border-radius:1.4cqh;padding:.3cqh 1cqw;
  margin-bottom:.6cqh}
.term .t{font-weight:600}
/* the criterion of the section (a term box "The criterion"): its own colour and
   its monogram in a circle, as on the owner's slides */
.defpill.crit{background:var(--ks);padding-left:8.4cqh;min-height:6.2cqh;box-sizing:border-box}
.defpill.crit .defterm{background:none;color:var(--k);padding:0;border-radius:0}
.term.crit{background:var(--ks);padding-left:9.4cqh;padding-top:1.2cqh;padding-bottom:1.2cqh;
  min-height:8cqh;box-sizing:border-box}
.term.crit .lbl{background:#fff;color:var(--k);margin:0 1cqw .2cqh 0;vertical-align:.15em}
.term.crit .t{display:inline;color:var(--k);font-weight:700}
.crit::before{content:attr(data-mono);position:absolute;left:1.3cqh;top:50%;width:5.8cqh;height:5.8cqh;
  margin-top:-2.9cqh;border-radius:50%;background:var(--k);color:#fff;font-weight:700;font-size:2.6cqh;
  line-height:5.8cqh;text-align:center;letter-spacing:-.02em}
.term.crit::before{left:1.8cqh;width:6.2cqh;height:6.2cqh;margin-top:-3.1cqh;line-height:6.2cqh}
.crit[data-mono-len="3"]::before{font-size:1.9cqh}
/* change cards */
.chg{background:var(--sc-note);border:0;border-radius:2.8cqh}
.chg .chg-cap{color:var(--sc-muted2);font-weight:600}
/* the badge is placed in its card; a side note keeps the place the player gives it */
.crit:not(.beside){position:relative}
.chg-arrow path{stroke:var(--sc-faint)}
/* a table: a solid header row in the colour of its section's criterion (ink
   elsewhere), white words in sentence case, tinted body rows */
.tbl:not(.core){background:transparent;border-radius:2.2cqh;overflow:hidden;padding:0}
.tbl:not(.core) table{border-collapse:separate;border-spacing:0}
.tbl th,.tbl.core th,.tbl.core.role-slide th{background:var(--k);color:#fff;border:0;font-weight:600;
  text-transform:none;letter-spacing:0;padding:1cqh 1.6cqw;vertical-align:bottom}
.tbl td,.tbl.core td{background:var(--ks);border:0;border-top:max(1px,.25cqh) solid #fff;padding:1cqh 1.6cqw}
/* a header cell in a tense family's colour keeps it: the summary table's past,
   present and future (design system §5a, §7 Tables; ADR 043) */
.tbl th:is(.fam-past,.fam-past_to_now,.fam-now,.fam-future),
.tbl.core th:is(.fam-past,.fam-past_to_now,.fam-now,.fam-future),
.tbl.core.role-slide th:is(.fam-past,.fam-past_to_now,.fam-now,.fam-future){background:var(--f);color:var(--f-on)}
.tbl th:first-child{border-top-left-radius:2.2cqh} .tbl th:last-child{border-top-right-radius:2.2cqh}
.tbl tbody tr:last-child td:first-child{border-bottom-left-radius:2.2cqh}
.tbl tbody tr:last-child td:last-child{border-bottom-right-radius:2.2cqh}
.tbl th[data-tone="wrong"]::before,.tbl th[data-tone="right"]::before{display:inline-block;width:2.6cqh;
  height:2.6cqh;margin-right:.8cqw;border-radius:50%;background:#fff;font-size:1.7cqh;line-height:2.6cqh;
  text-align:center;font-weight:700;vertical-align:.1em}
.tbl th[data-tone="wrong"]::before{content:"\2715";color:var(--sc-wrong)}
.tbl th[data-tone="right"]::before{content:"\2713";color:var(--sc-right)}
.tbl td[data-tone="wrong"]{background:var(--sc-wrong-bg);color:var(--sc-wrong)}
.tbl td[data-tone="right"],.tbl td[data-tone="right"] .tw{background:var(--sc-right-bg);color:var(--sc-right)}
/* a slide's table, the board's core: the spotlight fades the rows not being
   taught to half and lifts the row being taught as one row, with a soft neutral
   shadow and a very small scale, inside the table's edges (rule 11 in style C) */
.tbl.core,.tbl.core.role-slide{background:transparent;border:0;border-radius:0;overflow:visible;
  padding:.6cqh .8cqw}
.tbl.core table{border-collapse:separate;border-spacing:0}
.tbl.core tbody tr{transition:transform .25s cubic-bezier(.2,.7,.2,1),filter .25s ease,box-shadow .25s ease,opacity .25s ease}
.tbl.core.spot tbody tr:not(.focus) td{opacity:.5}
.tbl.core.spot tbody tr.focus{position:relative;z-index:1;filter:drop-shadow(0 .6cqh 1.2cqh rgba(20,32,31,.14));
  transform:scale(calc(1 + .004 * var(--sc-motion, 1)))}
.tbl.core td.active,.tbl.core.spot tbody tr.focus td.active{background:var(--sc-active);box-shadow:none}
/* a document (a Reading text, a Listening transcript; `doc`) is a page on paper,
   its paragraphs with no rule between them, so a transcript's lines stay on
   their grid; the paragraph being taught keeps the paper (the spotlight and the
   lift show it), so a keyword pair's colour, multiplied with what is under it,
   is the same on the text as on its question (ADR 043) */
.tbl.core.doc td{background:var(--sc-paper);border-top:0}
/* and keeps its page's measure: no room added around it or in its title row,
   so its text takes no more lines than before, and the Reading and Listening
   boards keep the sizes their fit and guard found (§7g, §7h) */
.tbl.core.doc.role-slide{padding:0}
.tbl.core.doc.role-slide th{padding:.9cqh 1.4cqw}
.tbl.core.doc td.active,.tbl.core.doc.spot tbody tr.focus td.active{background:var(--sc-paper)}
.tbl.core .tw{color:var(--sc-ink)}
/* typed text keeps its width while it is typed (§8a, ADR 043): the player splits
   it into a typed and an untyped half, and kerning or a ligature across that
   split would change the line's width by a fraction of a pixel, enough to wrap a
   word in IBM Plex. Set without either, the halves add up to the whole. A table
   with a layout (§7j) is checked with its layout */
.tbl.core:not(.lay) .tw{font-kerning:none;font-variant-ligatures:none}
/* the clause diagram's comma after a dependent clause is drawn in weight 500
   when the clauses are joined; IBM Plex's 500 face has its own line metrics,
   so the comma has that weight from the start, unseen (§8a, ADR 043) */
.cl-piece.dep.first .cl-text::after{font-weight:500}
/* a word longer than its narrow column (a wider device font, §8b) breaks inside
   its cell rather than running out of the table; at the lesson's own font no
   word is that long (ADR 043) */
.tbl.core:not(.lay) td{overflow-wrap:break-word}
/* a question board's column (Reading Part B and C, Listening) is narrow: its
   notes keep a narrow side padding, so they take no more lines than before
   (§7g, §7h; ADR 043) */
#cam:is(.qboard,.lboard) > .blk:is(.plain.role-note,.plain.beside,.callout,.term.tnote,.term.role-note){
  padding:1.1cqh 1cqw}
/* there a word card is told by its amber and its word, without the "Word" chip
   on a line of its own */
#cam:is(.qboard,.lboard) .gl-txt::before{content:none}
.tbl.core td.v-wrong{opacity:.45;color:var(--sc-wrong)}
.tbl.core td.v-right{background:var(--sc-right-bg)}
.tbl.core td.v-right::after{background:var(--sc-right);border-radius:50%}
/* the contents board: every part on one board, in two columns of tinted rows
   beside the board's picture (design system §2, a short list fits on one
   board); a criterion's number in its own colour */
#cam:has(> .blk.citem){column-gap:1.6cqw;row-gap:1.3cqh}
#cam:has(> .blk.citem):has(> .blk.pic){padding-left:24cqh}
#cam:has(> .blk.citem) > .blk.pic{position:absolute;left:0;top:0;margin:0}
#cam > .blk.citem{flex:0 0 calc(50% - .8cqw);box-sizing:border-box;background:var(--ks);border-radius:2.2cqh;
  padding:1.3cqh 1.4cqw;align-items:center;gap:1.4cqw;line-height:1.3}
.citem .cnum{width:6.1cqh;height:6.1cqh;border-radius:50%;font-size:2.6cqh;font-weight:700;margin-top:0;
  background:#fff;color:var(--k)}
.citem[data-crit] .cnum{background:var(--k);color:#fff}
.citem .ct{font-weight:600;font-size:3cqh}
.citem .cs{font-size:2.2cqh;color:var(--sc-muted2)}
.citem .cs:empty{display:none}
/* a category's sections, each on its own line under the category's heading
   (ADR 043): the parts the narration names, all on the one board. The "·"
   between them stays in the words and is drawn at no size */
#cam > .blk.citem:has(> div > .cs.parts){align-items:flex-start}
.citem .cs.parts{font-size:0;line-height:0;margin-top:.6cqh}
.citem .cs.parts .cp{display:block;position:relative;font-size:2.3cqh;line-height:1.3;color:var(--sc-muted);
  padding:.25cqh 0 .25cqh 2.2cqh}
.citem .cs.parts .cp::before{content:"";position:absolute;left:.3cqh;top:calc(.25cqh + .65em - .45cqh);
  width:.9cqh;height:.9cqh;border-radius:50%;background:var(--k);opacity:.55}

/* ---- Board layouts (docs/02-DESIGN-SYSTEM.md §7j): a table read as tiles,
   scorecards, cards, steps, a flow, bins, a fix, a stack, case notes, changes,
   a checklist or a letter; a comparison as two options side by side. Only the
   rows and cells are laid out; the words, their order and every hook
   (data-row, data-col, data-typed) are the table's own. ---- */
.tbl.lay table,.tbl.lay thead,.tbl.lay tbody{display:block;width:100%}
.tbl.lay colgroup{display:none}
.tbl.lay tr{display:block}
.tbl.lay td{display:block;border:0;border-radius:0;background:none;padding:0}
.tbl.lay thead tr{display:block}
.tbl.core.lay.spot tbody tr:not(.focus) td{opacity:1}
.tbl.core.lay.spot tbody tr:not(.focus){opacity:.5}
.tbl.core.lay.spot tbody tr.focus{filter:none;box-shadow:var(--sc-shadow);
  transform:translateY(calc(-.3cqh * var(--sc-motion, 1))) scale(calc(1 + .004 * var(--sc-motion, 1)))}
/* a tile, a card or a scorecard has room around it: it grows a little more */
.tbl.core.lay.spot:is(.lay-tiles,.lay-checklist,.lay-scores,.lay-cards,.lay-steps) tbody tr.focus{
  transform:translateY(calc(-.3cqh * var(--sc-motion, 1))) scale(calc(1 + .015 * var(--sc-motion, 1)))}
.tbl.lay td.active,.tbl.core.lay.spot tbody tr.focus td.active{background:var(--sc-active);
  box-shadow:0 0 0 .7cqh var(--sc-active);border-radius:.6cqh}
.tbl.lay th:first-child,.tbl.lay th:last-child,.tbl.lay tbody tr:last-child td:first-child,
.tbl.lay tbody tr:last-child td:last-child{border-radius:0}
.tbl.lay td::before{display:block}
/* a caption from the column's label (an attribute, never a word) */
.tbl.lay td[data-label]::before{content:attr(data-label);font-size:2.1cqh;line-height:1.3;font-weight:600;
  color:var(--sc-muted2);margin-bottom:.4cqh}
/* tiles: the six criteria, each its own colour and monogram */
.tbl.lay.lay-tiles thead,.tbl.lay.lay-checklist thead{display:none}
.tbl.lay.lay-tiles tbody,.tbl.lay.lay-checklist tbody{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1.8cqh 1.4cqw}
.tbl.lay.lay-tiles.n2 tbody,.tbl.lay.lay-checklist.n2 tbody,.tbl.lay.lay-tiles.n4 tbody{grid-template-columns:repeat(2,minmax(0,1fr))}
.tbl.lay.lay-tiles tr{background:var(--ks);border-radius:2.8cqh;padding:1.8cqh 1.6cqw 2cqh;position:relative}
.tbl.lay.lay-tiles td[data-col="0"],.tbl.lay.lay-tiles td:first-child{position:relative;padding-left:7.6cqh;
  min-height:6.2cqh;font-weight:700;color:var(--k);padding-top:1.1cqh;box-sizing:border-box}
.tbl.lay.lay-tiles td:first-child::after{content:attr(data-mono);position:absolute;left:0;top:0;width:6.2cqh;
  height:6.2cqh;border-radius:50%;background:var(--k);color:#fff;font-size:2.6cqh;line-height:6.2cqh;
  text-align:center;font-weight:700}
.tbl.lay.lay-tiles td[data-mono-len="3"]::after{font-size:1.9cqh}
.tbl.lay.lay-tiles td:nth-child(2){margin-top:1cqh;color:var(--sc-ink)}
.tbl.lay.lay-tiles td::before{content:none}
/* a checklist: what is checked, then the word for it, large */
.tbl.lay.lay-checklist tr{background:var(--ks);border-radius:2.8cqh;padding:1.6cqh 1.8cqw}
.tbl.lay.lay-checklist td:first-child{font-weight:600;color:var(--sc-muted)}
.tbl.lay.lay-checklist td:nth-child(2){font-size:calc(var(--tf, 3.2cqh) * 1.35);line-height:1.2;font-weight:700;color:var(--k)}
.tbl.lay.lay-checklist td::before{content:none}
/* scorecards: one card a row, side by side; its points as a bar of dots, those
   needed for grade B filled */
.tbl.lay.lay-scores thead{display:none}
.tbl.lay.lay-scores tbody{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.8cqh 1.8cqw}
.tbl.lay.lay-scores tr{display:grid;grid-template-columns:1fr 1fr;column-gap:1.6cqw;row-gap:1.4cqh;
  background:var(--ks);border-radius:2.8cqh;padding:2cqh 2cqw}
.tbl.lay.lay-scores td:first-child{grid-column:1 / -1;font-weight:700;color:var(--k)}
.tbl.lay.lay-scores td:nth-child(n+2){font-size:calc(var(--tf, 3.2cqh) * 1.9);line-height:1.1;font-weight:700;color:var(--k)}
.tbl.lay.lay-scores td:nth-child(n+2)::before{font-size:2.1cqh;font-weight:600;color:var(--sc-muted2);margin-bottom:.6cqh}
.tbl .pts{display:flex;flex-wrap:wrap;gap:1cqh;margin-top:1.4cqh}
.tbl .pts i{display:block;width:3.6cqh;height:3.6cqh;border-radius:50%;box-sizing:border-box;
  border:.45cqh solid var(--k);background:#fff}
.tbl .pts i.on{background:var(--k)}
.tbl .kset{display:flex;gap:.8cqh;margin-top:1cqh}
.tbl .kset i{display:block;width:2.6cqh;height:2.6cqh;border-radius:.8cqh;background:var(--k)}
/* cards: the rows side by side; a two-column table's first cell is the card's
   heading, further cells carry their column's label */
.tbl.lay.lay-cards thead,.tbl.lay.lay-steps thead{display:none}
.tbl.lay.lay-cards tbody,.tbl.lay.lay-steps tbody{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1.6cqh 1.6cqw}
.tbl.lay.lay-cards.n2 tbody,.tbl.lay.lay-steps.n2 tbody{grid-template-columns:repeat(2,minmax(0,1fr))}
.tbl.lay.lay-cards.n4 tbody,.tbl.lay.lay-steps.n4 tbody{grid-template-columns:repeat(4,minmax(0,1fr))}
.tbl.lay.lay-cards tr,.tbl.lay.lay-steps tr{background:var(--ks);border-radius:2.4cqh;padding:1.6cqh 1.6cqw;position:relative}
.tbl.lay.lay-cards td:first-child,.tbl.lay.lay-steps td:first-child{font-weight:700;color:var(--k);margin-bottom:.6cqh}
.tbl.lay.lay-cards td:first-child::before,.tbl.lay.lay-steps td:first-child::before{content:none}
.tbl.lay.lay-cards td+td{margin-top:.8cqh}
.tbl.lay.lay-cards td[data-tone]{display:inline-block;font-weight:700;border-radius:1.4cqh;padding:.2cqh 1.2cqw .2cqh .9cqw}
.tbl.lay.lay-cards td[data-tone]::before{content:none}
.tbl.lay.lay-cards td[data-tone="right"]{background:var(--sc-right-bg);color:var(--sc-right)}
.tbl.lay.lay-cards td[data-tone="wrong"]{background:var(--sc-wrong-bg);color:var(--sc-wrong)}
.tbl.lay.lay-cards td[data-tone].active,.tbl.core.lay.spot.lay-cards tbody tr.focus td[data-tone].active{
  box-shadow:0 0 0 .5cqh var(--sc-active)}
.tbl.lay.lay-cards td[data-tone="right"].active{background:var(--sc-right-bg)}
.tbl.lay.lay-cards td[data-tone="wrong"].active{background:var(--sc-wrong-bg)}
.tbl.lay.lay-cards td[data-tone="right"]::after{content:" \2713"} .tbl.lay.lay-cards td[data-tone="wrong"]::after{content:" \2715"}
/* steps: cards joined by arrows, in order */
.tbl.lay.lay-steps tbody{column-gap:4.6cqh}
.tbl.lay.lay-steps tr:not(:last-child)::after{content:"";position:absolute;top:50%;right:-3.6cqh;margin-top:-1.3cqh;
  border-top:1.3cqh solid transparent;border-bottom:1.3cqh solid transparent;border-left:2.2cqh solid var(--k)}
.tbl.lay.lay-steps td.num{display:inline-block;width:4.6cqh;height:4.6cqh;border-radius:50%;background:var(--k);
  color:#fff;text-align:center;line-height:4.6cqh;margin-right:1cqw;vertical-align:middle}
.tbl.lay.lay-steps td.num+td{display:inline;font-weight:600}
.tbl.lay.lay-steps td+td{color:var(--sc-ink);font-weight:400}
.tbl.lay.lay-steps td+td::before{content:none}
/* a flow: a letter's parts or steps one under the other, each with its label as
   a tab, a chevron from one to the next */
.tbl.lay.lay-flow thead{display:none}
.tbl.lay.lay-flow tbody{display:flex;flex-direction:column;gap:1cqh}
.tbl.lay.lay-flow tr{display:grid;grid-template-columns:16% minmax(0,1fr);column-gap:1.4cqw;
  background:var(--sc-paper);border-radius:2.2cqh;padding:.8cqh 1.6cqw .8cqh 1cqw;position:relative}
.tbl.lay.lay-flow td:first-child{align-self:start;justify-self:start;background:var(--ks);color:var(--k);font-weight:700;
  border-radius:1.2cqh;padding:.1cqh .9cqw}
.tbl.lay.lay-flow tr:not(:last-child)::after{content:"";position:absolute;left:calc(1cqw + 3.4cqh);bottom:.6cqh;
  border-left:1.5cqh solid transparent;border-right:1.5cqh solid transparent;border-top:2cqh solid var(--k)}
.tbl.lay.lay-flow td:first-child::before,.tbl.lay.lay-flow td+td::before{content:none}
/* bins: keep, keep briefly or leave out; each case note's answer is typed into
   its lane */
.tbl.lay.lay-bins thead tr,.tbl.lay.lay-bins tbody tr{display:grid;grid-template-columns:40% 20% 20% 20%;column-gap:0}
.tbl.lay.lay-bins tbody{display:flex;flex-direction:column;gap:1cqh}
.tbl.lay.lay-bins th{background:none;color:var(--sc-muted2);padding:.4cqh 1.6cqw;font-size:2.2cqh;border-radius:0}
.tbl.lay.lay-bins th+th{grid-column:2 / 5;text-align:center}
.tbl.lay.lay-bins th .lanes{display:grid;grid-template-columns:1fr 1fr 1fr;margin-top:.6cqh}
.tbl.lay.lay-bins th .lanes i{display:block;font-style:normal;font-weight:700;font-size:2.4cqh;color:var(--sc-right)}
.tbl.lay.lay-bins th .lanes i::before{content:attr(data-l)}
.tbl.lay.lay-bins th .lanes i:last-child{color:var(--sc-wrong)}
.tbl.lay.lay-bins tbody tr{border-radius:2.2cqh;overflow:hidden;
  background:linear-gradient(90deg,var(--sc-paper) 0 40%,var(--sc-right-bg) 40% 60%,#f6f9e8 60% 80%,var(--sc-wrong-bg) 80%)}
.tbl.lay.lay-bins td{padding:1.1cqh 1.6cqw}
.tbl.lay.lay-bins td::before{content:none}
.tbl.lay.lay-bins td[data-bin]{text-align:center;font-weight:700}
.tbl.lay.lay-bins td[data-bin="keep"]{grid-column:2;color:var(--sc-right)}
.tbl.lay.lay-bins td[data-bin="brief"]{grid-column:3;color:var(--sc-right)}
.tbl.lay.lay-bins td[data-bin="out"]{grid-column:4;color:var(--sc-wrong)}
.tbl.lay.lay-bins td[data-bin] .tw{color:inherit}
/* a fix: the case note, the wrong sentence, an arrow, the right one */
.tbl.lay.lay-fix table{display:table;border-collapse:separate;border-spacing:0 .7cqh}
.tbl.lay.lay-fix thead{display:table-header-group} .tbl.lay.lay-fix tbody{display:table-row-group}
.tbl.lay.lay-fix tr,.tbl.lay.lay-fix thead tr{display:table-row} .tbl.lay.lay-fix td{display:table-cell}
.tbl.lay.lay-fix colgroup{display:table-column-group}
.tbl.lay.lay-fix th{font-size:2.4cqh;padding:.6cqh 1.4cqw}
.tbl.lay.lay-fix th:first-child{border-radius:2.2cqh 0 0 2.2cqh} .tbl.lay.lay-fix th:last-child{border-radius:0 2.2cqh 2.2cqh 0}
.tbl.lay.lay-fix td{padding:.8cqh 1.4cqw;background:var(--ks);vertical-align:middle}
.tbl.lay.lay-fix td[data-tone="wrong"]{background:var(--sc-wrong-bg)}
.tbl.lay.lay-fix td[data-tone="right"]{background:var(--sc-right-bg)}
.tbl.lay.lay-fix td:first-child{border-radius:2.2cqh 0 0 2.2cqh;font-weight:600;color:var(--k)}
.tbl.lay.lay-fix td:last-child{border-radius:0 2.2cqh 2.2cqh 0}
.tbl.lay.lay-fix td[data-tone="wrong"]{position:relative}
.tbl.lay.lay-fix td[data-tone="wrong"]::after{content:"";position:absolute;right:-.9cqh;top:50%;margin-top:-1.1cqh;
  z-index:1;border-top:1.1cqh solid transparent;border-bottom:1.1cqh solid transparent;
  border-left:1.6cqh solid var(--sc-right)}
.tbl.lay.lay-fix td::before{content:none}
.tbl.core.lay.lay-fix.spot tbody tr.focus{filter:drop-shadow(0 .6cqh 1.2cqh rgba(20,32,31,.14));box-shadow:none;
  transform:scale(calc(1 + .004 * var(--sc-motion, 1)))}
/* changes: from the case notes to the letter, an arrow between */
.tbl.lay.lay-change table{display:table;border-collapse:separate;border-spacing:0 .7cqh}
.tbl.lay.lay-change thead{display:table-header-group} .tbl.lay.lay-change tbody{display:table-row-group}
.tbl.lay.lay-change tr,.tbl.lay.lay-change thead tr{display:table-row} .tbl.lay.lay-change td{display:table-cell}
.tbl.lay.lay-change colgroup{display:table-column-group}
.tbl.lay.lay-change th{background:none;color:var(--k);font-size:2.2cqh;padding:0 1.6cqw}
.tbl.lay.lay-change td{padding:.8cqh 1.4cqw;background:var(--ks);vertical-align:middle}
.tbl.lay.lay-change td:first-child{border-radius:2.2cqh 0 0 2.2cqh;font-weight:700;color:var(--k);position:relative;
  padding-right:4cqh}
.tbl.lay.lay-change td:first-child::after{content:"";position:absolute;right:1.2cqh;top:50%;margin-top:-1.2cqh;
  border-top:1.2cqh solid transparent;border-bottom:1.2cqh solid transparent;border-left:1.8cqh solid var(--k)}
.tbl.lay.lay-change td:last-child{border-radius:0 2.2cqh 2.2cqh 0;background:#fff;box-shadow:inset 0 0 0 .35cqh var(--ks)}
.tbl.lay.lay-change td::before{content:none}
/* a stack: the parts of a letter top to bottom, the counted part taller */
.tbl.lay.lay-stack thead{display:none}
.tbl.lay.lay-stack tbody{display:flex;flex-direction:column;gap:1cqh}
.tbl.lay.lay-stack tr{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;column-gap:2cqw;
  background:var(--sc-note);border-radius:2.2cqh;padding:1cqh 1.8cqw}
.tbl.lay.lay-stack tr[data-yes]{background:var(--ks);padding-top:2.6cqh;padding-bottom:2.6cqh}
.tbl.lay.lay-stack td::before{content:none}
.tbl.lay.lay-stack td+td{font-weight:700;border-radius:1.4cqh;padding:.3cqh 1.4cqw;background:#fff;color:var(--sc-muted2)}
.tbl.lay.lay-stack tr[data-yes] td+td{background:var(--k);color:#fff}
.tbl.lay.lay-stack td+td.active,.tbl.core.lay.spot.lay-stack tbody tr.focus td+td.active{background:#fff;
  box-shadow:0 0 0 .5cqh var(--sc-active);border-radius:1.4cqh}
.tbl.lay.lay-stack tr[data-yes] td+td.active,.tbl.core.lay.spot.lay-stack tbody tr[data-yes].focus td+td.active{
  background:var(--k)}
/* case notes: a card on paper, its heading as a tab, a line a note */
.tbl.lay.lay-notes{background:var(--sc-paper);padding:1.4cqh 2cqw 1.6cqh;border-radius:2.4cqh}
.tbl.lay.lay-notes th{display:inline-block;background:var(--ks);color:var(--k);font-size:2.2cqh;padding:.2cqh 1cqw;
  border-radius:1.2cqh;margin-bottom:.6cqh}
.tbl.lay.lay-notes td{position:relative;padding:.25cqh 0 .25cqh 2.6cqh}
.tbl.lay.lay-notes td::before{content:"";position:absolute;left:.4cqh;top:50%;width:1cqh;height:1cqh;margin-top:-.5cqh;
  border-radius:50%;background:var(--k)}
/* a letter: the whole letter on paper, each part's name a tab in its margin */
.tbl.lay.lay-letter{background:var(--sc-paper);border-radius:2.4cqh;padding:1.2cqh 1.4cqw}
.tbl.lay.lay-letter table{display:table;border-collapse:separate;border-spacing:0 .5cqh}
.tbl.lay.lay-letter thead{display:table-header-group} .tbl.lay.lay-letter tbody{display:table-row-group}
.tbl.lay.lay-letter tr,.tbl.lay.lay-letter thead tr{display:table-row} .tbl.lay.lay-letter td{display:table-cell}
.tbl.lay.lay-letter colgroup{display:table-column-group}
.tbl.lay.lay-letter th{background:none;color:var(--sc-muted2);padding:0 1.2cqw .4cqh}
.tbl.lay.lay-letter td{padding:.6cqh 1.2cqw;background:none}
.tbl.lay.lay-letter td:first-child{color:var(--k);font-weight:600}
.tbl.lay.lay-letter td::before{content:none}
.tbl.core.lay.lay-letter.spot tbody tr.focus{filter:drop-shadow(0 .5cqh 1cqh rgba(20,32,31,.14));box-shadow:none;
  transform:scale(calc(1 + .004 * var(--sc-motion, 1)))}
.tbl.core.lay.lay-letter.spot tbody tr.focus td{background:#fff}
.tbl.core.lay.lay-letter.spot tbody tr.focus td:first-child{border-radius:1.4cqh 0 0 1.4cqh}
.tbl.core.lay.lay-letter.spot tbody tr.focus td:last-child{border-radius:0 1.4cqh 1.4cqh 0}
/* two options side by side (a comparison that is not a change), numbered */
.chg.lay-vs{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:1.2cqh 1.6cqw;align-items:stretch;
  background:none;padding-left:0;padding-right:0}
.chg.lay-vs .chg-cap{grid-column:1 / -1}
.chg.lay-vs .chg-arrow{display:none}
.chg.lay-vs .chg-from,.chg.lay-vs .chg-to{position:relative;display:block;background:var(--ks);border-radius:2.4cqh;
  padding:1.3cqh 1.6cqw 1.3cqh 6.2cqh;font-weight:500}
.chg.lay-vs .chg-from::before,.chg.lay-vs .chg-to::before{position:absolute;left:1.4cqh;top:1.3cqh;width:3.8cqh;
  height:3.8cqh;border-radius:50%;background:var(--k);color:#fff;font-weight:700;font-size:2.2cqh;
  line-height:3.8cqh;text-align:center}
.chg.lay-vs .chg-from::before{content:"1"} .chg.lay-vs .chg-to::before{content:"2"}

/* motion (§8g): a new block fades in and rises a little; a lifted block grows a
   very little and takes the soft neutral shadow (rule 54, the class fx-lift a
   1.22 player sets from the bundle). Every motion is 150 to 400 ms, eased,
   never bouncy; none under reduced motion. --sc-motion is 0 only in the
   engine's measuring checks, which measure the board at rest. */
@keyframes sc-rise{from{opacity:0;transform:translateY(1.2cqh)}to{opacity:1;transform:none}}
.blk.on:not([data-layer="fixed"]):not([data-oa-layer="fixed"]){animation:sc-rise .3s cubic-bezier(.2,.7,.2,1) backwards}
.blk{transition:opacity .25s ease,transform .25s cubic-bezier(.2,.7,.2,1),box-shadow .25s ease !important}
.blk.fx-lift{z-index:2;transform:scale(calc(1 + .01 * var(--sc-motion, 1)));
  box-shadow:var(--sc-shadow)}
.blk.fx-lift:not(.beside){position:relative}
.citem.fx-lift{transform:scale(calc(1 + .02 * var(--sc-motion, 1)))}
.chg.lay-vs.fx-lift{box-shadow:none}
.chg.lay-vs.fx-lift .chg-from,.chg.lay-vs.fx-lift .chg-to{box-shadow:var(--sc-shadow)}
@media (prefers-reduced-motion: reduce){
  .blk.on:not([data-layer="fixed"]):not([data-oa-layer="fixed"]){animation:none}
  .blk{transition:opacity .25s ease !important}
  .blk.fx-lift,.tbl.core.spot tbody tr.focus,.tbl.core.lay.spot tbody tr.focus{transform:none}
  .tbl.core tbody tr{transition:none}
}
"""

# The spotlight by cell (rule 11, 1.22; ADR 043 decision 17), appended to the
# stylesheet of a lesson that has a table whose rows do not pair their cells (a
# word and its meaning, shuffled; build_lesson_player.cell_focus), and only
# there. A player sets `cellspot` on the table and `lit` on each cell the focus
# entry's `cells` lists, and no row `focus`.
CELL_CSS = r"""
/* the spotlight by cell (rule 11; ADR 043): the cells lit (the word being
   taught and the meaning its arrow reaches) at full strength, in the soft amber
   of the cell being taught; every other cell, the one beside the word included,
   at half */
.tbl.core.spot.cellspot tbody tr td{opacity:.5}
.tbl.core.spot.cellspot tbody tr td.lit{opacity:1;background:var(--sc-active,#fff0c4)}
"""

# A column label's meaning, by its words (sentence case in the data). Only labels
# that say right or wrong take a colour (§5).
TONE_WORDS = {"wrong": ("wrong", "wrong version", "not accurate", "inaccurate", "leave out", "avoid"),
              "right": ("accurate", "right", "correct", "right version", "correct version", "better",
                        "keep")}
# a cell's own words in a column that says whether a note goes into the letter
IN_LETTER = ("in the letter?", "in the letter")
CELL_TONES = {"yes": "right", "keep": "right", "keep, briefly": "right", "keep briefly": "right",
              "no": "wrong", "leave out": "wrong"}
TH = re.compile(r"<th>([^<]*)</th>")
TD = re.compile(r'<td data-col="(\d+)"')


def tone_html(html: str) -> str:
    """A table's column labels that say wrong or right take `data-tone`, so the
    stylesheet draws them in red or green with a cross or a tick; on a core table
    each cell of that column takes it too (its `data-col`), so the wrong
    sentences are in the red of "wrong" and the right ones in the green of
    "right". No word changes."""
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
# Board layouts (docs/02-DESIGN-SYSTEM.md §7j): named per block in the lesson's
# sections.json (`block_layouts`, by bundle block id), drawn by the stylesheet
# from a class on the block (`lay lay-<name>`) and attributes on its rows and
# cells. Nothing is added that is a word: labels and monograms are attributes the
# stylesheet draws, dots and lanes are empty elements, hidden from readers.
# ---------------------------------------------------------------------------
LAYOUTS = {
    # name: (block types, core table only, columns allowed or None)
    "tiles": (("table",), False, None),
    "checklist": (("table",), False, (2,)),
    "scores": (("table",), True, (3,)),
    "cards": (("table",), False, None),
    "steps": (("table",), False, (2,)),
    "flow": (("table",), True, (2,)),
    "bins": (("table",), True, (2,)),
    "fix": (("table",), True, (2, 3)),
    "change": (("table",), False, (2,)),
    "stack": (("table",), False, (2,)),
    "notes": (("table",), False, (1,)),
    "letter": (("table",), True, (1, 2)),
    "pair": (("table",), False, (4,)),
    "paper": (("table",), False, (2, 3)),
    "vs": (("comparison",), False, None),
    "acronym": (("table",), False, (2,)),
    "skeleton": (("table",), False, (2,)),
    # ADR 048 (the Word Order redesign, 2026-11-01): forms drawn for what a board teaches
    "pieces": (("table",), False, None),      # a sentence as its pieces in a row, each under its label
    "place": (("table",), False, (3,)),       # the paper beside the part's place on a letter of dashed lines
    "tags": (("table",), False, (2,)),        # a sentence on paper, the note on it as a tag at its end
    "front": (("table",), False, (3,)),       # the kind, the phrase that opens the sentence, the rest
    "sides": (("table",), False, (3,)),       # one case, its two versions side by side
    "chips": (("table",), False, None),       # short phrases as chips in a row (a word bank), row by row
    # ADR 050 (the teal look): the owner's eleven Canva patterns, each a layout
    "wrongright": (("table",), False, (2,)),            # 1  the wrong sentence, a curved arrow, the right one
    "coded": (("table",), False, None),                 # 2  a sentence as coloured parts, each with its label
    "opener": (("table",), False, (3,)),                # 2  the kind, the opening phrase in colour, the rest
    "timeline": (("table",), False, (2, 3)),            # 3  rounded markers on a line
    "columns": (("table",), False, (2, 3, 4)),          # 4  rounded columns under coloured heads
    "parts": (("table",), False, (2,)),                 # 5  a letter, its parts named in pills beside it
    "badges": (("table", "category_card"), False, (1, 2)),  # 6  key points as round badges, a note under each
    "ruled": (("table",), False, (1, 2)),               # 7  a paragraph on ruled paper, in a learner's hand
    "beforeafter": (("table",), False, (2,)),           # 8  before and after, the words of each counted
    "choices": (("table",), False, None),               # 9  short phrases as coloured choice pills
    "path": (("table",), False, (1, 2)),                # 10 numbered steps on a curved path
    "compare": (("comparison", "table"), False, (2,)),  # 11 two things side by side, each framed, its head a pill
}
# The teal look's layouts (ADR 050), their rules appended only where used
ADR050_LAYOUTS = ("wrongright", "coded", "opener", "timeline", "columns", "parts", "badges", "ruled",
                  "beforeafter", "choices", "path", "compare")
# a row's colour, in turn (ADR 050): amber, blue, lilac, coral, teal
T_ROW_COLOURS = ("opener", "timeline", "parts", "badges", "path")
# three of a kind (badges on cards) take teal, amber and coral first, as on the owner's slides
T_TRIO = (4, 0, 3, 1, 2)
# ADR 050 amendment (1) (the owner's review of Word Order draft.3, 2026-11-01): a letter on its parts longer than
# this flows in two columns, so its words keep their full size (rule 1); a note in the teacher's hand is short, about
# 15 words at most (rule 2): a longer one is set in print (class `t-print`)
PARTS_FLOW_CHARS = 700
HAND_WORDS = 15
HAND_TYPES = ("plain", "callout", "category_card")
# a comparison's head: the words up to the first colon, when that is a short lead
COMPARE_HEAD = re.compile(r"^([^:<]{3,90}:)( )(.+)$", re.S)
WORD = re.compile(r"[A-Za-z0-9À-ɏ]+(?:['’.\-/&][A-Za-z0-9À-ɏ]+)*")
# a `place` layout's letter column names the part's place after a colon ("Her letter: the request")
PLACE_NAMES = ("opening", "body", "request", "closing")
# The paper (ADR 045): the line every Writing paper opens its notes with (fact
# 44), set in bold on the paper, and the labels of its Writing Task box
PAPER_TODAY = "Assume that today's date is"
PAPER_TASK = ("writing task", "in your answer")
PAPER_SKIP_MAX = 4
PAPER_BESIDE = 'data-paper="beside"'
# an acronym's row opens with its letter, a colon and the part's name ("I: Introduce and identify")
ACRONYM_CELL = re.compile(r"^[A-Z]: \S")
# the layouts that draw `block_accents` (the words set in the layout's accent colour)
ACCENT_LAYOUTS = ("skeleton", "compare")
BINS = {"keep": "keep", "keep, briefly": "brief", "keep briefly": "brief", "leave out": "out"}
BIN_LANES = (("keep", "Keep"), ("brief", "Keep briefly"), ("out", "Leave out"))
TAGS = re.compile(r"<[^>]+>")


def check_layout(bid: str, b: dict, layout: str) -> str | None:
    """Why a block cannot take a layout, or None when it can."""
    if layout not in LAYOUTS:
        return f"{layout!r} is not a layout ({', '.join(LAYOUTS)})"
    types, core, cols = LAYOUTS[layout]
    if b.get("type") not in types:
        return f"{bid} is a {b.get('type')}; the layout {layout!r} is for {', '.join(types)}"
    if core and not b.get("core"):
        return f"the layout {layout!r} is for a board's own table, and {bid} is a table written while teaching"
    if b.get("doc") or b.get("map"):
        return f"{bid} is a document or a map, drawn as a page"
    ncol = len(b.get("header") or (b.get("rows") or [[]])[0])
    if cols and b.get("type") == "table" and ncol not in cols:
        return f"the layout {layout!r} is for a table of {' or '.join(map(str, cols))} columns; {bid} has {ncol}"
    if layout == "bins":
        bad = [r for r in b.get("rows") or [] if r[1].strip().lower() not in BINS]
        if bad:
            return f"bins: a row's answer is not one of {', '.join(BINS)}: {bad[0][1]!r}"
    if layout == "scores":
        if any(not (r[1].strip().isdigit() and r[2].strip().isdigit()) for r in b.get("rows") or []):
            return "scores: each row's second and third cells are numbers (scored out of, needed)"
    if layout == "acronym":
        bad = [r for r in b.get("rows") or [] if not ACRONYM_CELL.match(r[0].strip())]
        if bad:
            return f"acronym: a row's first cell is a letter, a colon and the part's name ('I: Introduce'): {bad[0][0]!r}"
    if layout == "skeleton":
        if any(not (b.get("rows") or [[""]])[0][c].strip() for c in (0, 1)):
            return "skeleton: each letter opens with a paragraph written out (its first row)"
    return None


def _text(html: str) -> str:
    return _html.unescape(TAGS.sub("", html))


def _add_root(html: str, classes: str = "", attrs: str = "") -> str:
    """Classes and attributes on the block's own element (its first tag)."""
    m = re.match(r'<div class="([^"]*)"', html)
    if not m:
        return html
    cls = m.group(1) + ((" " + classes) if classes else "")
    return '<div class="' + cls + '"' + attrs + html[m.end():]


def _crit_attr(key: str) -> str:
    mono = CRIT_MONO[key]
    return f' data-crit="{key}" data-mono="{_html.escape(mono)}"' + (
        f' data-mono-len="{len(mono)}"' if len(mono) >= 3 else "")


def _rows_split(body: str) -> list[str]:
    return re.findall(r"<tr[^>]*>.*?</tr>", body, re.S)


def _cells(tr: str) -> list[str]:
    return re.findall(r"<td[^>]*>.*?</td>", tr, re.S)


def _table_html(b: dict, html: str, layout: str) -> str:
    header = b.get("header") or []
    rows = b.get("rows") or []
    core = bool(b.get("core"))
    # each cell its column's label, for the layouts that show one above it
    labelled = layout in ("scores", "pieces", "coded") or (layout == "cards" and len(header) >= 3) or \
        (layout == "choices" and header and all(h.strip() for h in header))

    def cell_attrs(c: int, txt: str) -> str:
        out = ""
        if labelled and (c >= 1 or layout in ("pieces", "coded", "choices")) and c < len(header) and header[c].strip():
            out += f' data-label="{_html.escape(header[c], quote=True)}"'
        if layout == "coded":
            out += f' data-c="{c % 5}"'
        if layout == "beforeafter":
            out += f' data-count="{len(WORD.findall(_text(txt)))}"'
        return out

    head_m = re.search(r"<thead>.*?</thead>", html, re.S)
    body_m = re.search(r"<tbody>(.*?)</tbody>", html, re.S)
    if not body_m:
        return html
    trs = _rows_split(body_m.group(1))
    if len(trs) != len(rows):
        return html
    named = {CRIT_KEY.get(r[0].strip()) for r in rows} - {None}
    # a skeleton: in each column (a letter), the last paragraph written out
    last_txt = [max([r for r, row in enumerate(rows) if row[c].strip()] or [-1]) for c in range(len(rows[0]) if rows else 0)] \
        if layout == "skeleton" else []
    new_trs = []
    in_task = False
    for r, (tr, row) in enumerate(zip(trs, rows)):
        tds = _cells(tr)
        open_tr = re.match(r"<tr[^>]*", tr).group(0)
        key = CRIT_KEY.get(row[0].strip()) if row else None
        if key and layout in ("tiles", "scores", "checklist", "letter"):
            open_tr += _crit_attr(key)
        if layout == "stack" and len(row) > 1 and row[1].strip().lower() == "yes":
            open_tr += ' data-yes=""'
        if layout in T_ROW_COLOURS:
            open_tr += f' data-c="{r % 5}"'
        skip = 0
        if layout == "paper" and len(row) > 1:
            # a row with no label goes on in the box of the row above it
            in_task = _paper_task(row) or (in_task and not row[0].strip())
            open_tr += _paper_row_attrs(row, in_task)
            # a label of more lines than its lines (a heading over its first
            # label, "PATIENT DETAILS:" over "Name:") sets the lines beside the
            # labels they belong to
            skip = min(PAPER_SKIP_MAX, max(0, row[0].count(" / ") - row[1].count(" / ")))
        new_tds = []
        for c, (td, txt) in enumerate(zip(tds, row)):
            m = re.match(r"<td([^>]*)>(.*)</td>$", td, re.S)
            attrs, inner = m.group(1), m.group(2)
            attrs += cell_attrs(c, txt)
            if layout == "tiles" and c == 0 and key:
                attrs += f' data-mono="{_html.escape(CRIT_MONO[key])}"' + (
                    ' data-mono-len="3"' if len(CRIT_MONO[key]) >= 3 else "")
            if layout == "steps" and c == 0 and txt.strip().isdigit():
                attrs = ' class="num"' + attrs
            if layout == "bins" and c == 1:
                attrs += f' data-bin="{BINS[txt.strip().lower()]}"'
            if skip and c >= 1:
                attrs += f' data-skip="{skip}"'
            if layout == "acronym" and c == 0:
                # the letter, the colon (drawn at no size) and the part's name, each in its own span: the words,
                # their order and the colon stay exactly as they are
                am = re.match(r"^([A-Z])(: )(.*)$", inner, re.S)
                if am:
                    inner = ('<span class="ac-l">' + am.group(1) + '</span><span class="ac-s">' + am.group(2)
                             + '</span><span class="ac-n">' + am.group(3) + "</span>")
            if layout == "skeleton":
                if not txt.strip() and r < last_txt[c]:
                    attrs += ' data-dash=""'            # a paragraph not written out: dashed lines
                elif txt.strip() and r == last_txt[c] and r > 0:
                    attrs += ' data-end=""'             # the letter's last paragraph written out: the request expanded
                elif not txt.strip() and r > last_txt[c]:
                    attrs += ' data-after=""'           # past the letter's end: its sheet has ended
            if layout == "choices":
                attrs += f' data-c="{(r * len(row) + c) % 5}"'
            if layout == "parts" and c == 1 and not txt.strip():
                attrs += ' data-dash=""'                # a part not written out: grey lines, never a word
            if layout in ("cards", "stack") and c >= 1 and header and \
                    header[c].strip().lower() in IN_LETTER and txt.strip().lower() in CELL_TONES:
                attrs += f' data-tone="{CELL_TONES[txt.strip().lower()]}"'
            if layout == "scores" and c == 0:
                total, need = int(row[1]), int(row[2])
                inner += ('<span class="pts" aria-hidden="true">' + '<i class="on"></i>' * need
                          + "<i></i>" * max(0, total - need) + "</span>")
                if not key:
                    # "each of the other five": the criteria the other rows do not name
                    others = [k for k, *_r in CRITERIA.values() if k not in named]
                    if others and len(others) < len(CRITERIA):
                        inner = inner.replace('<span class="pts"', '<span class="kset" aria-hidden="true">'
                                              + "".join(f'<i data-crit="{k}"></i>' for k in others)
                                              + '</span><span class="pts"', 1)
            new_tds.append(f"<td{attrs}>{inner}</td>")
        new_trs.append(open_tr + ">" + "".join(new_tds) + "</tr>")
    html = html[:body_m.start(1)] + "".join(new_trs) + html[body_m.end(1):]
    if layout == "bins" and head_m:
        lanes = ('<span class="lanes" aria-hidden="true">'
                 + "".join(f'<i data-l="{_html.escape(lab)}"></i>' for _k, lab in BIN_LANES) + "</span>")
        ths = list(re.finditer(r"<th[^>]*>(.*?)</th>", html, re.S))
        if len(ths) >= 2:
            t = ths[1]
            html = html[:t.end(1)] + lanes + html[t.end(1):]
    n = len(rows)
    size = " n2" if n in (2,) or (layout in ("tiles", "checklist") and n == 4) else " n4" if n == 4 else ""
    if layout == "paper":
        # a sheet of the paper (its label and its lines), or each row a piece of
        # it beside the part of the letter it feeds (a third column)
        form = "beside" if len(header or (rows or [[]])[0]) == 3 else "sheet"
        return _add_root(html, "lay lay-paper", " " + PAPER_BESIDE if form == "beside" else ' data-paper="sheet"')
    if layout == "place":
        # the paper beside the letter (ADR 045), the part of the letter drawn in
        # its place on a small letter of dashed lines (the owner's Request slide,
        # ADR 048): the place is named after a colon in the letter column's label
        tail = header[2].rsplit(":", 1)[-1].strip().lower().split() if len(header) == 3 and ":" in header[2] else []
        place = tail[-1] if tail else "body"          # "Her letter: the request" names the request
        if place not in PLACE_NAMES:
            place = "body"
        return _add_root(html, "lay lay-paper lay-place", f" {PAPER_BESIDE} data-place=\"{place}\"")
    if layout in ADR050_LAYOUTS:
        html = _add_root(html, "lay lay-" + layout + size, _teal_root_attrs(layout, header, rows))
        if layout == "path":
            i = html.index(">") + 1
            html = html[:i] + path_curve(n) + html[i:]
        return html
    return _add_root(html, "lay lay-" + layout + size)


def _teal_root_attrs(layout: str, header: list, rows: list) -> str:
    """The attributes a teal layout's table takes on its own element (ADR 050): how many columns,
    which column is narrow (a column of short labels or places), whether a bank is named by its
    first header cell only; and, for a path, the curve its steps sit on (an empty drawing)."""
    ncol = len(header or (rows or [[]])[0])
    out = f' data-cols="{ncol}" data-n="{len(rows)}"'
    if layout == "columns" and ncol >= 2:
        longest = [max([len(_text(r[c]).strip()) for r in rows] + [len(_text(header[c]).strip()) if header else 0])
                   for c in range(ncol)]
        if longest[0] <= 16 and max(longest[1:]) > 30:
            out += ' data-cw="first"'
        elif longest[-1] <= 40 and max(longest[:-1]) > 50:
            out += ' data-cw="last"'
    if layout == "choices" and header and not all(h.strip() for h in header) and header[0].strip():
        out += ' data-titled=""'
    if layout == "parts" and sum(len(_text(r[-1])) for r in rows) > PARTS_FLOW_CHARS:
        out += ' data-flow="2"'
    return out


def path_curve(n: int) -> str:
    """The curve a path's steps sit on (ADR 050, the owner's pattern 10): an empty drawing, the
    steps' centres alternately low and high in a box 1000 by 300, joined by smooth curves."""
    if n < 1:
        return ""
    pts = [((i + 0.5) * 1000 / n, 220 if i % 2 == 0 else 80) for i in range(n)]
    d = f"M{pts[0][0]:.0f} {pts[0][1]}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        h = (x1 - x0) / 2
        d += f" C{x0 + h:.0f} {y0} {x1 - h:.0f} {y1} {x1:.0f} {y1}"
    return ('<svg class="t-curve" viewBox="0 0 1000 300" preserveAspectRatio="none" aria-hidden="true" '
            f'focusable="false"><path d="{d}"/></svg>')


def _paper_task(row: list[str]) -> bool:
    return row[0].strip().lower().startswith(PAPER_TASK)


def _paper_row_attrs(row: list[str], in_task: bool) -> str:
    """A row of the paper: its date line set in bold as the paper sets it, a row
    of its Writing Task box, a row with no part of the letter beside it."""
    out = ""
    if row[1].strip().startswith(PAPER_TODAY):
        out += ' data-today=""'
    if in_task:
        out += ' data-task=""'
    if len(row) == 3 and not row[2].strip():
        out += ' data-solo=""'
    return out


# The layouts and forms added in phase 2 (ADR 043 amendment (3)): their rules go
# into the stylesheet of a lesson that uses them only (as CELL_CSS), so every
# other lesson's stylesheet stays as it is. Each form is told by its columns
# (`:has`), so the block's html carries nothing new.
FIX2 = ".tbl.lay.lay-fix:has(thead th:nth-child(2):last-child)"
LETTER1 = ".tbl.lay.lay-letter:has(thead th:only-child)"
LAYOUT_CSS = {
    "fix2": r"""
/* a fix of two columns, the wrong sentence and the right one (no case note):
   the wrong one on red with its cross, an arrow, the right one on green with its
   tick, typed in (§7j) */
""" + FIX2 + r""" td:first-child{font-weight:400;color:var(--sc-wrong)}
""" + FIX2 + r""" td:last-child{padding-left:2.2cqw}
""" + FIX2 + r""" tbody tr:last-child td:first-child{border-radius:2.2cqh 0 0 2.2cqh}
""" + FIX2 + r""" tbody tr:last-child td:last-child{border-radius:0 2.2cqh 2.2cqh 0}
""" + FIX2 + r""" .tw{font-kerning:none;font-variant-ligatures:none;background:none}
""" + FIX2 + r""" td{overflow-wrap:break-word}
""" + FIX2 + r""" thead th+th{box-shadow:-1px 0 0 var(--k)}
""",
    "letter1": r"""
/* a letter of one column, a text with gaps (§7 Tables): the whole letter on
   paper, its greeting at the top, a paragraph a row, its closing last; the
   paragraph being taught a white sheet lifted on the paper (§7j) */
""" + LETTER1 + r"""{padding:1.6cqh 2cqw}
""" + LETTER1 + r""" th{color:var(--sc-ink);font-weight:600;font-size:inherit;padding:0 1.2cqw .6cqh;text-align:left}
""" + LETTER1 + r""" td:first-child{color:var(--sc-ink);font-weight:400}
.tbl.core""" + LETTER1[4:] + r""".spot tbody tr.focus td:first-child{border-radius:1.4cqh}
""" + LETTER1 + r""" .tw{font-kerning:none;font-variant-ligatures:none}
""" + LETTER1 + r""" td{overflow-wrap:break-word}
""",
    "pair": r"""
/* a pair: a table of four columns, two lists of one kind side by side (the
   countable nouns and the uncountable), drawn as two tables with a gap between,
   as on the slide; a row is still taught as one row (§7j) */
.tbl.lay.lay-pair table{display:table;width:100%;border-collapse:separate;border-spacing:0}
.tbl.lay.lay-pair thead{display:table-header-group} .tbl.lay.lay-pair tbody{display:table-row-group}
.tbl.lay.lay-pair tr,.tbl.lay.lay-pair thead tr{display:table-row}
.tbl.lay.lay-pair td{display:table-cell;background:var(--ks);border-top:max(1px,.25cqh) solid #fff;
  padding:1cqh 1.6cqw;overflow-wrap:break-word}
.tbl.lay.lay-pair colgroup{display:table-column-group}
.tbl.lay.lay-pair td::before{content:none}
.tbl.lay.lay-pair td:is([data-col="0"],[data-col="2"]){font-weight:600}
/* the gap is taken from the first list's wider column, so no narrow column
   loses room (the table's columns are fixed) */
.tbl.lay.lay-pair :is(th:nth-child(2),td[data-col="1"]){border-right:3cqw solid transparent;background-clip:padding-box}
.tbl.lay.lay-pair th:nth-child(1){border-top-left-radius:2.2cqh}
.tbl.lay.lay-pair th:nth-child(2){border-top-right-radius:calc(3cqw + 2.2cqh) 2.2cqh}
.tbl.lay.lay-pair th:nth-child(3){border-top-left-radius:2.2cqh}
.tbl.lay.lay-pair th:nth-child(4){border-top-right-radius:2.2cqh}
.tbl.lay.lay-pair tbody tr:last-child td[data-col="0"],
.tbl.core.lay.lay-pair.spot tbody tr.focus:last-child td.active[data-col="0"]{border-radius:0 0 0 2.2cqh}
.tbl.lay.lay-pair tbody tr:last-child td[data-col="1"],
.tbl.core.lay.lay-pair.spot tbody tr.focus:last-child td.active[data-col="1"]{
  border-radius:0 0 calc(3cqw + 2.2cqh) 0 / 0 0 2.2cqh 0}
.tbl.lay.lay-pair tbody tr:last-child td[data-col="2"],
.tbl.core.lay.lay-pair.spot tbody tr.focus:last-child td.active[data-col="2"]{border-radius:0 0 0 2.2cqh}
.tbl.lay.lay-pair tbody tr:last-child td[data-col="3"],
.tbl.core.lay.lay-pair.spot tbody tr.focus:last-child td.active[data-col="3"]{border-radius:0 0 2.2cqh 0}
.tbl.lay.lay-pair td.active,.tbl.core.lay.lay-pair.spot tbody tr.focus td.active{box-shadow:none;border-radius:0;
  background-clip:padding-box}
.tbl.core.lay.lay-pair.spot tbody tr.focus{filter:drop-shadow(0 .6cqh 1.2cqh rgba(20,32,31,.14));box-shadow:none;
  transform:scale(calc(1 + .004 * var(--sc-motion, 1)))}
""",
    "paper": r"""
/* the paper (ADR 045; §7j): a Writing paper as the learner meets it in the
   exam, one look wherever a lesson quotes it. White, a hairline edge, a soft
   shadow; the paper's labels in their own column in bold, its lines beside
   them, its date line in bold and its Writing Task box grey, as on the paper.
   Of two columns a sheet of the paper; of three, each row a piece of that sheet,
   an arrow, and the part of the letter it feeds on the letter's cream */
.tbl.lay.lay-paper table{display:table;width:100%;border-collapse:separate;border-spacing:0;table-layout:auto}
.tbl.lay.lay-paper thead{display:table-header-group} .tbl.lay.lay-paper tbody{display:table-row-group}
.tbl.lay.lay-paper tr,.tbl.lay.lay-paper thead tr{display:table-row}
.tbl.lay.lay-paper td,.tbl.lay.lay-paper th{display:table-cell}
.tbl.lay.lay-paper colgroup{display:table-column-group}
.tbl.lay.lay-paper td::before{content:none}
.tbl.lay.lay-paper td{vertical-align:top;line-height:1.35;overflow-wrap:break-word;color:var(--sc-ink)}
.tbl.lay.lay-paper td:first-child{font-weight:700;white-space:nowrap}
/* a label is one line beside its line, so the column takes the longest label
   (the table sized by its content); a heading alone on its row may wrap */
.tbl.lay.lay-paper td:first-child:has(+ td:empty){white-space:normal}
.tbl.lay.lay-paper tr[data-today] td:nth-child(2){font-weight:700}
.tbl.lay.lay-paper td[data-skip]::before{content:"";display:block}
.tbl.lay.lay-paper td[data-skip="1"]::before{height:1.35em} .tbl.lay.lay-paper td[data-skip="2"]::before{height:2.7em}
.tbl.lay.lay-paper td[data-skip="3"]::before{height:4.05em} .tbl.lay.lay-paper td[data-skip="4"]::before{height:5.4em}
.tbl.lay.lay-paper .tw{font-kerning:none;font-variant-ligatures:none}
.tbl.lay.lay-paper th{background:none;color:var(--sc-muted2);font-size:2.1cqh;line-height:1.3;font-weight:600;
  padding:0 .9cqw .7cqh;text-align:left;white-space:nowrap;vertical-align:bottom;border-radius:0}
/* a sheet */
.tbl.lay.lay-paper[data-paper="sheet"]{background:#fff;border:max(1px,.14cqh) solid #d7d4e0;border-radius:.7cqh;
  box-shadow:0 .5cqh 1.8cqh rgba(20,32,31,.10);padding:1.2cqh 1.4cqw 1.4cqh}
.tbl.lay.lay-paper[data-paper="sheet"] td{padding:.55cqh .9cqw;border-top:max(1px,.12cqh) solid #ecebf1;border-radius:0}
.tbl.lay.lay-paper[data-paper="sheet"] tbody tr:first-child td{border-top:0}
.tbl.lay.lay-paper[data-paper="sheet"] tr[data-task] td{background:#f1f1f6;border-top-color:#f1f1f6}
.tbl.lay.lay-paper[data-paper="sheet"] tr:not([data-task]) + tr[data-task] td{border-top:max(1px,.14cqh) solid #c9c6d4}
/* each row a piece of the sheet, an arrow, the part of the letter */
.tbl.lay.lay-paper[data-paper="beside"] table{border-spacing:0 .8cqh}
.tbl.lay.lay-paper[data-paper="beside"] td{padding:.6cqh .9cqw}
/* the label column as wide as its longest label; the paper's lines and the
   letter share the rest evenly, so neither is squeezed */
.tbl.lay.lay-paper[data-paper="beside"] col{width:auto!important}
.tbl.lay.lay-paper[data-paper="beside"] td:first-child{width:1%}
.tbl.lay.lay-paper[data-paper="beside"] td:nth-child(2),.tbl.lay.lay-paper[data-paper="beside"] td:nth-child(3){width:50%}
.tbl.lay.lay-paper[data-paper="beside"] td:is(:first-child,:nth-child(2)){background:#fff;
  border-top:max(1px,.14cqh) solid #d7d4e0;border-bottom:max(1px,.14cqh) solid #d7d4e0;
  box-shadow:0 .5cqh .9cqh -.4cqh rgba(20,32,31,.16)}
.tbl.lay.lay-paper[data-paper="beside"] td:first-child{border-left:max(1px,.14cqh) solid #d7d4e0;
  border-radius:.7cqh 0 0 .7cqh}
.tbl.lay.lay-paper[data-paper="beside"] td:nth-child(2){border-right:max(1px,.14cqh) solid #d7d4e0;
  border-radius:0 .7cqh .7cqh 0;position:relative}
.tbl.lay.lay-paper[data-paper="beside"] tr[data-task] td:is(:first-child,:nth-child(2)){background:#f1f1f6}
.tbl.lay.lay-paper[data-paper="beside"] td:nth-child(2)::after{content:"";position:absolute;right:-2.6cqh;top:50%;
  margin-top:-1.1cqh;border-top:1.1cqh solid transparent;border-bottom:1.1cqh solid transparent;
  border-left:1.6cqh solid var(--k)}
.tbl.lay.lay-paper[data-paper="beside"] td:nth-child(3){background:var(--sc-paper);border-left:3.6cqh solid transparent;
  background-clip:padding-box;border-radius:5cqh 1.4cqh 1.4cqh 5cqh / 1.4cqh;padding-left:1.2cqw}
.tbl.lay.lay-paper[data-paper="beside"] th:nth-child(3){padding-left:calc(3.6cqh + 1.2cqw)}
.tbl.lay.lay-paper[data-paper="beside"] tr[data-solo] td:nth-child(2)::after{content:none}
.tbl.lay.lay-paper[data-paper="beside"] tr[data-solo] td:nth-child(3){background:none}
/* the part being named lit, the others at half; a sheet's lit as with a marker */
.tbl.core.lay.lay-paper.spot tbody tr.focus{filter:drop-shadow(0 .5cqh 1cqh rgba(20,32,31,.14));box-shadow:none;
  transform:scale(calc(1 + .004 * var(--sc-motion, 1)))}
.tbl.core.lay.lay-paper[data-paper="sheet"].spot tbody tr.focus td{background:var(--sc-active)}
.tbl.lay.lay-paper td.active,.tbl.core.lay.lay-paper.spot tbody tr.focus td.active{background:var(--sc-active);
  box-shadow:none}
.tbl.core.lay.lay-paper[data-paper="beside"].spot tbody tr.focus td:nth-child(3).active{background:var(--sc-active);
  background-clip:padding-box}
""",
    "acronym": r"""
/* an acronym's parts (ISBAR; §7j): a row a part, on a tinted band; its letter large, bold and in the key-word
   amber in its own narrow column, the part's name in bold beside it, the colon between them drawn at no size
   (it stays in the words); the part's text in the row. The spotlight lifts the row being taught and fades the
   others; the marker marks its words */
.tbl.lay.lay-acronym tbody{display:flex;flex-direction:column;gap:.8cqh}
.tbl.lay.lay-acronym thead tr,.tbl.lay.lay-acronym tbody tr{display:grid;grid-template-columns:28% minmax(0,1fr);column-gap:0}
.tbl.lay.lay-acronym thead tr{margin-bottom:.4cqh}
.tbl.lay.lay-acronym th:first-child{border-radius:2.2cqh 0 0 2.2cqh} .tbl.lay.lay-acronym th:last-child{border-radius:0 2.2cqh 2.2cqh 0}
.tbl.lay.lay-acronym tbody tr{background:var(--ks);border-radius:2.2cqh}
.tbl.lay.lay-acronym td{padding:1cqh 1.6cqw;overflow-wrap:break-word;color:var(--sc-ink);align-self:center}
.tbl.lay.lay-acronym td::before{content:none}
.tbl.lay.lay-acronym td:first-child{display:grid;grid-template-columns:calc(var(--tf,3.2cqh) * 2.1) minmax(0,1fr);
  column-gap:1.2cqw;align-items:center;padding-right:.6cqw}
.tbl.lay.lay-acronym .ac-l{grid-area:1 / 1;font-size:calc(var(--tf,3.2cqh) * 2.1);line-height:1;font-weight:800;
  color:var(--sc-gloss);text-align:center;letter-spacing:-.02em}
.tbl.lay.lay-acronym .ac-s{grid-area:1 / 2;font-size:0;line-height:0}
.tbl.lay.lay-acronym .ac-n{grid-area:1 / 2;font-weight:700;line-height:1.2}
.tbl.lay.lay-acronym .tw{font-kerning:none;font-variant-ligatures:none}
.tbl.lay.lay-acronym td.active,.tbl.core.lay.lay-acronym.spot tbody tr.focus td.active{background:var(--sc-active);
  box-shadow:none;border-radius:0 2.2cqh 2.2cqh 0}
.tbl.lay.lay-acronym td:first-child.active,.tbl.core.lay.lay-acronym.spot tbody tr.focus td:first-child.active{
  border-radius:2.2cqh 0 0 2.2cqh}
""",
    "skeleton": r"""
/* letter skeletons (§7j): two letters side by side, each a sheet on the letter's cream, a paragraph a row.
   A paragraph the lesson reads is written out: the opening, with its purpose words (`block_accents`) in the
   Purpose colour; the last paragraph written out of each letter (the request expanded) in that colour. A
   paragraph not written out is three short dashed lines, drawn by the stylesheet, never a word */
.tbl.lay.lay-skeleton table{display:table;width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed}
.tbl.lay.lay-skeleton thead{display:table-header-group} .tbl.lay.lay-skeleton tbody{display:table-row-group}
.tbl.lay.lay-skeleton tr,.tbl.lay.lay-skeleton thead tr{display:table-row}
.tbl.lay.lay-skeleton td,.tbl.lay.lay-skeleton th{display:table-cell}
.tbl.lay.lay-skeleton colgroup{display:table-column-group}
.tbl.lay.lay-skeleton col{width:50%!important}
.tbl.lay.lay-skeleton th{background:none;color:var(--sc-muted2);font-size:2.2cqh;line-height:1.3;font-weight:600;
  padding:0 1.6cqw .6cqh;text-align:left;vertical-align:bottom;border-radius:0}
.tbl.lay.lay-skeleton td{background:var(--sc-paper);vertical-align:top;padding:.6cqh 1.6cqw;line-height:1.4;
  color:var(--sc-ink);overflow-wrap:break-word;border-top:0;border-radius:0}
.tbl.lay.lay-skeleton td::before{content:none}
/* the gap between the sheets is taken from the first (the columns are fixed) */
.tbl.lay.lay-skeleton :is(th:first-child,td:first-child){border-right:3cqw solid transparent;background-clip:padding-box}
.tbl.lay.lay-skeleton tbody tr:first-child td{padding-top:1.5cqh;border-radius:1.4cqh 1.4cqh 0 0}
.tbl.lay.lay-skeleton tbody tr:last-child td{padding-bottom:1.5cqh;border-radius:0 0 1.4cqh 1.4cqh}
.tbl.lay.lay-skeleton .tw{font-kerning:none;font-variant-ligatures:none}
/* a paragraph not written out: dashed lines over the whole of its cell (at least two), so a paragraph beside
   a long one is as long: thin lines down the cell, cut into dashes by stripes of the paper over them */
.tbl.lay.lay-skeleton td[data-dash]{background:
  repeating-linear-gradient(90deg,transparent 0 .9cqw,var(--sc-paper) .9cqw 1.5cqw) content-box,
  repeating-linear-gradient(180deg,transparent 0 .6em,var(--sc-faint) .6em calc(.6em + .26cqh),transparent calc(.6em + .26cqh) 1.35em) content-box,
  var(--sc-paper) padding-box}
.tbl.lay.lay-skeleton td[data-dash]::before{content:"";display:block;height:2.7em}
/* past a letter's end its sheet has ended: the cell above it closes the sheet */
.tbl.lay.lay-skeleton td[data-after]{background:none}
.tbl.lay.lay-skeleton tbody tr:has(+ tr td[data-col="0"][data-after]) td[data-col="0"],
.tbl.lay.lay-skeleton tbody tr:has(+ tr td[data-col="1"][data-after]) td[data-col="1"]{padding-bottom:1.5cqh;
  border-radius:0 0 1.4cqh 1.4cqh}
/* the purpose words, and the request expanded at the end */
.tbl.lay.lay-skeleton .acc{color:var(--k-purpose);font-weight:600}
.tbl.lay.lay-skeleton td[data-end]{color:var(--k-purpose)}
/* the paragraph being taught lit, the others at half */
.tbl.core.lay.lay-skeleton.spot tbody tr.focus{filter:drop-shadow(0 .5cqh 1cqh rgba(20,32,31,.14));box-shadow:none;
  transform:scale(calc(1 + .004 * var(--sc-motion, 1)))}
.tbl.lay.lay-skeleton td.active,.tbl.core.lay.lay-skeleton.spot tbody tr.focus td.active{background:var(--sc-active);
  box-shadow:none;background-clip:padding-box}
""",
}
LAYOUT_CSS.update({
    "pieces": r"""
/* pieces (ADR 048): a sentence as its pieces in a row, each a chip under its
   label (who, what, where, when, why), read left to right as the sentence is;
   the labels are the header's words, drawn above the chips */
.tbl.lay.lay-pieces thead{display:none}
.tbl.lay.lay-pieces tbody{display:flex;flex-direction:column;gap:1.6cqh}
.tbl.lay.lay-pieces tr{display:flex;flex-wrap:wrap;gap:1cqh 1cqw;align-items:flex-start;padding:0}
.tbl.lay.lay-pieces td{display:block;position:relative;max-width:100%;margin-top:3.1cqh;background:var(--ks);
  color:var(--sc-ink);border-radius:1.8cqh;padding:1cqh 1.6cqw;overflow-wrap:break-word;
  font-size:calc(var(--tf, 3.2cqh) * 1.12);line-height:1.3;min-width:6cqw;min-height:1.3em;box-sizing:border-box}
.tbl.lay.lay-pieces td::before{content:none}
.tbl.lay.lay-pieces td[data-label]::before{content:attr(data-label);display:block;position:absolute;left:1cqw;
  top:-2.9cqh;margin:0;font-size:2.3cqh;line-height:1.2;font-weight:700;letter-spacing:.04em;color:var(--k);
  white-space:nowrap}
.tbl.lay.lay-pieces td.active,.tbl.core.lay.lay-pieces.spot tbody tr.focus td.active{background:var(--sc-active);
  box-shadow:none;border-radius:1.6cqh}
.tbl.core.lay.lay-pieces.spot tbody tr.focus{box-shadow:none;transform:none}
""",
    "place": r"""
/* the paper beside the part's place (ADR 048, the owner's Request slide): the
   part of the letter on a small white letter whose other lines are dashes, in
   its place (data-place: opening, body, request, closing) */
.tbl.lay.lay-place[data-paper="beside"] td:nth-child(3){background:#fff;border:max(1px,.14cqh) solid #d7d4e0;
  border-left:3.6cqh solid transparent;background-clip:padding-box;border-radius:.7cqh;
  box-shadow:0 .5cqh .9cqh -.4cqh rgba(20,32,31,.16);padding:1cqh 1.4cqw 1.2cqh}
.tbl.lay.lay-place td:nth-child(3)::before,.tbl.lay.lay-place td:nth-child(3)::after{content:"";display:block;
  background:repeating-linear-gradient(90deg,#c9c6d4 0 1.1cqw,transparent 1.1cqw 1.8cqw);
  -webkit-mask:repeating-linear-gradient(180deg,#000 0 .26cqh,transparent .26cqh 2.3cqh);
  mask:repeating-linear-gradient(180deg,#000 0 .26cqh,transparent .26cqh 2.3cqh)}
.tbl.lay.lay-place td:nth-child(3)::before{margin-bottom:1cqh;width:60%}
.tbl.lay.lay-place td:nth-child(3)::after{margin-top:1cqh}
.tbl.lay.lay-place[data-place="opening"] td:nth-child(3)::before{height:4.6cqh;width:38%}
.tbl.lay.lay-place[data-place="opening"] td:nth-child(3)::after{height:11.5cqh}
.tbl.lay.lay-place[data-place="body"] td:nth-child(3)::before{height:6.9cqh}
.tbl.lay.lay-place[data-place="body"] td:nth-child(3)::after{height:6.9cqh}
.tbl.lay.lay-place[data-place="request"] td:nth-child(3)::before{height:11.5cqh;width:100%}
.tbl.lay.lay-place[data-place="request"] td:nth-child(3)::after{height:4.6cqh;width:30%}
.tbl.lay.lay-place[data-place="closing"] td:nth-child(3)::before{height:13.8cqh;width:100%}
.tbl.lay.lay-place[data-place="closing"] td:nth-child(3)::after{content:none}
.tbl.lay.lay-place tr[data-solo] td:nth-child(3){background:none;border:0;box-shadow:none}
.tbl.lay.lay-place tr[data-solo] td:nth-child(3)::before,.tbl.lay.lay-place tr[data-solo] td:nth-child(3)::after{content:none}
.tbl.core.lay.lay-place.spot tbody tr.focus td:nth-child(3).active{background:var(--sc-active);background-clip:padding-box}
""",
    "tags": r"""
/* tags (ADR 048): a sentence on paper, the note on it (where a word sits) as a
   tag in the section's colour at its end */
.tbl.lay.lay-tags thead{display:none}
.tbl.lay.lay-tags tbody{display:flex;flex-direction:column;gap:1cqh}
.tbl.lay.lay-tags tr{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,32%);align-items:center;column-gap:1.4cqw;
  background:var(--sc-paper);border-radius:2.2cqh;padding:1cqh 1.6cqw}
.tbl.lay.lay-tags td::before{content:none}
.tbl.lay.lay-tags td:first-child{color:var(--sc-ink);overflow-wrap:break-word}
.tbl.lay.lay-tags td+td{justify-self:end;font-weight:700;color:var(--k);background:var(--ks);border-radius:1.4cqh;
  padding:.5cqh 1.2cqw;text-align:center;overflow-wrap:break-word}
.tbl.lay.lay-tags td.active,.tbl.core.lay.lay-tags.spot tbody tr.focus td.active{background:var(--sc-active);box-shadow:none}
.tbl.core.lay.lay-tags.spot tbody tr.focus{filter:drop-shadow(0 .5cqh 1cqh rgba(20,32,31,.14));box-shadow:none;
  transform:scale(calc(1 + .004 * var(--sc-motion, 1)))}
""",
    "front": r"""
/* a phrase first (ADR 048): the kind as a chip, the phrase that opens the
   sentence bold in the section's colour with its comma, then the rest of the
   sentence, so the two parts of the sentence are seen */
.tbl.lay.lay-front thead{display:none}
.tbl.lay.lay-front tbody{display:flex;flex-direction:column;gap:1cqh}
.tbl.lay.lay-front tr{display:grid;grid-template-columns:auto auto minmax(0,1fr);align-items:baseline;column-gap:1cqw;
  background:var(--sc-paper);border-radius:2.2cqh;padding:1cqh 1.6cqw}
.tbl.lay.lay-front td::before{content:none}
.tbl.lay.lay-front td:first-child{background:var(--ks);color:var(--k);font-weight:700;border-radius:1.2cqh;
  padding:.2cqh 1cqw;font-size:2.4cqh;align-self:center;white-space:nowrap}
.tbl.lay.lay-front td:nth-child(2){font-weight:700;color:var(--k);max-width:42cqw;overflow-wrap:break-word}
.tbl.lay.lay-front td:nth-child(3){color:var(--sc-ink);overflow-wrap:break-word}
.tbl.lay.lay-front td.active,.tbl.core.lay.lay-front.spot tbody tr.focus td.active{background:var(--sc-active);
  box-shadow:0 0 0 .5cqh var(--sc-active);border-radius:.8cqh}
.tbl.core.lay.lay-front.spot tbody tr.focus{filter:drop-shadow(0 .5cqh 1cqh rgba(20,32,31,.14));box-shadow:none;
  transform:scale(calc(1 + .004 * var(--sc-motion, 1)))}
""",
    "sides": r"""
/* two places (ADR 048): one case, its two versions side by side under the
   column labels (at the start with a comma, at the end with none) */
.tbl.lay.lay-sides thead{display:block}
.tbl.lay.lay-sides thead tr,.tbl.lay.lay-sides tbody tr{display:grid;grid-template-columns:13% minmax(0,1fr) minmax(0,1fr);
  column-gap:1.2cqw;align-items:start}
.tbl.lay.lay-sides th{background:none;color:var(--sc-muted2);font-size:2.1cqh;line-height:1.3;font-weight:600;
  padding:0 1.2cqw .4cqh;text-align:left;border-radius:0}
.tbl.lay.lay-sides th:first-child{visibility:hidden}
.tbl.lay.lay-sides tbody{display:flex;flex-direction:column;gap:1cqh}
.tbl.lay.lay-sides tbody tr{background:var(--sc-note);border-radius:2.2cqh;padding:1cqh 1.2cqw}
.tbl.lay.lay-sides td::before{content:none}
.tbl.lay.lay-sides td:first-child{justify-self:start;background:var(--ks);color:var(--k);font-weight:700;
  border-radius:1.2cqh;padding:.1cqh .9cqw;font-size:2.2cqh}
.tbl.lay.lay-sides td+td{background:var(--sc-paper);border-radius:1.6cqh;padding:.8cqh 1.2cqw;color:var(--sc-ink);
  overflow-wrap:break-word}
.tbl.lay.lay-sides td:nth-child(3){background:#fff;box-shadow:inset 0 0 0 max(1px,.25cqh) var(--ks)}
.tbl.lay.lay-sides td.active,.tbl.core.lay.lay-sides.spot tbody tr.focus td.active{background:var(--sc-active);box-shadow:none}
.tbl.core.lay.lay-sides.spot tbody tr.focus{filter:drop-shadow(0 .5cqh 1cqh rgba(20,32,31,.14));box-shadow:none;
  transform:scale(calc(1 + .004 * var(--sc-motion, 1)))}
""",
    "chips": r"""
/* chips (ADR 048): a table of short phrases as chips in a row (a word bank),
   row by row, its first header cell the bank's name */
.tbl.lay.lay-chips thead{display:block}
.tbl.lay.lay-chips th+th{display:none}
.tbl.lay.lay-chips th{background:none;color:var(--sc-muted2);font-size:2.1cqh;line-height:1.3;font-weight:600;
  padding:0 .4cqw .6cqh;text-align:left;border-radius:0}
.tbl.lay.lay-chips tbody{display:flex;flex-wrap:wrap;gap:1cqh 1cqw}
.tbl.lay.lay-chips tr{display:contents}
.tbl.lay.lay-chips td::before{content:none}
.tbl.lay.lay-chips td{background:var(--ks);color:var(--k);font-weight:600;border-radius:1.6cqh;padding:.7cqh 1.4cqw}
.tbl.lay.lay-chips td.active,.tbl.core.lay.lay-chips.spot tbody tr.focus td.active{background:var(--sc-active);box-shadow:none}
.tbl.core.lay.lay-chips.spot tbody tr.focus{box-shadow:none;transform:none}
""",
})
ADR048_LAYOUTS = ("pieces", "place", "tags", "front", "sides", "chips")

# The teal look's patterns (ADR 050; docs/02-DESIGN-SYSTEM.md §7k): the owner's Canva patterns 1 to 11 of
# 2026-11-01. Rounded shapes, circles and pills, colour that names a part, no hard shadow; each appended only
# to the stylesheet of a lesson that uses it. Every colour falls back to the teal look's own, so a pattern
# drawn in a lesson without the look still reads. The words, their order and every hook stay the table's.
_T = ("--t-teal:#0b6e6d;--t-ink:#173d3c;--t-amber:#e2a72e;--t-coral:#e57063;--t-blue:#9ecfd8;"
      "--t-lilac:#b8a6d6;--t-teal-s:#e5f0ef;--t-amber-s:#fbf0d5;--t-coral-s:#fce7e3;--t-blue-s:#e1f1f4;"
      "--t-lilac-s:#eee8f6;--t-pen:#c4362f")
LAYOUT_CSS.update({
    "tset": r"""
/* the teal look's colours in turn (ADR 050): amber, blue, lilac, coral, teal, each with its soft tint and
   the ink that reads on it; the look's own values where the lesson has no look */
.lay,.lay-compare,.lay-badges{""" + _T + r"""}
.frame :is(.lay,.lay-badges) [data-c="0"],.frame .lay-badges[data-c="0"]{--c:var(--t-amber);--cs:var(--t-amber-s);--con:var(--t-ink)}
.frame :is(.lay,.lay-badges) [data-c="1"],.frame .lay-badges[data-c="1"]{--c:var(--t-blue);--cs:var(--t-blue-s);--con:var(--t-ink)}
.frame :is(.lay,.lay-badges) [data-c="2"],.frame .lay-badges[data-c="2"]{--c:var(--t-lilac);--cs:var(--t-lilac-s);--con:var(--t-ink)}
.frame :is(.lay,.lay-badges) [data-c="3"],.frame .lay-badges[data-c="3"]{--c:var(--t-coral);--cs:var(--t-coral-s);--con:var(--t-ink)}
.frame :is(.lay,.lay-badges) [data-c="4"],.frame .lay-badges[data-c="4"]{--c:var(--t-teal);--cs:var(--t-teal-s);--con:#fff}
/* typed words keep their width while they are typed (§8a) */
.tbl.lay:is(.lay-wrongright,.lay-coded,.lay-opener,.lay-timeline,.lay-columns,.lay-parts,.lay-badges,.lay-ruled,
  .lay-beforeafter,.lay-choices,.lay-path,.lay-compare) .tw{font-kerning:none;font-variant-ligatures:none}
.tbl.lay:is(.lay-wrongright,.lay-coded,.lay-opener,.lay-timeline,.lay-columns,.lay-parts,.lay-badges,.lay-ruled,
  .lay-beforeafter,.lay-choices,.lay-path,.lay-compare) td{overflow-wrap:break-word}
/* the pieces of a teal pattern enter in reading order as the board opens (§8g, ADR 050): a row, a pill or a
   step after another, 70 ms apart, each in 0.4 s; never under reduced motion, never in a measuring check */
@keyframes t-in{from{opacity:0;transform:scale(.97)}to{opacity:1;transform:none}}
@keyframes t-pop{from{opacity:0;transform:scale(.86)}to{opacity:1;transform:none}}
.tbl.lay:is(.lay-wrongright,.lay-opener,.lay-timeline,.lay-columns,.lay-parts,.lay-badges,.lay-ruled,
  .lay-beforeafter,.lay-path) tbody tr{animation:t-in .4s cubic-bezier(.2,.7,.2,1) backwards;transform-origin:50% 0}
.tbl.lay:is(.lay-coded,.lay-choices) td{animation:t-pop .4s cubic-bezier(.2,.7,.2,1) backwards}
.tbl.lay tbody tr:nth-child(2),.tbl.lay:is(.lay-coded,.lay-choices) td:nth-child(2){animation-delay:.07s}
.tbl.lay tbody tr:nth-child(3),.tbl.lay:is(.lay-coded,.lay-choices) td:nth-child(3){animation-delay:.14s}
.tbl.lay tbody tr:nth-child(4),.tbl.lay:is(.lay-coded,.lay-choices) td:nth-child(4){animation-delay:.21s}
.tbl.lay tbody tr:nth-child(5),.tbl.lay:is(.lay-coded,.lay-choices) td:nth-child(5){animation-delay:.28s}
.tbl.lay tbody tr:nth-child(6),.tbl.lay:is(.lay-coded,.lay-choices) td:nth-child(6){animation-delay:.35s}
.tbl.lay tbody tr:nth-child(n+7){animation-delay:.42s}
.tbl.lay.lay-choices tr:nth-child(2) td{animation-delay:.18s} .tbl.lay.lay-choices tr:nth-child(n+3) td{animation-delay:.32s}
@media (prefers-reduced-motion: reduce){.tbl.lay tbody tr,.tbl.lay td{animation:none}}
""",
    "wrongright": r"""
/* 1. wrong and right (ADR 050): a row a pair; the wrong sentence in plain ink, a curved arrow in the
   teacher's red pen, the right sentence in bold teal. The narration's pen circles mark the error */
.tbl.lay.lay-wrongright table{display:block}
.tbl.lay.lay-wrongright thead tr,.tbl.lay.lay-wrongright tbody tr{display:grid;
  grid-template-columns:minmax(0,1fr) 7.5cqw minmax(0,1.08fr);align-items:center}
.tbl.lay.lay-wrongright th{background:none;color:var(--t-pen);font-size:2.2cqh;line-height:1.3;font-weight:700;
  letter-spacing:.08em;text-transform:uppercase;padding:0 0 .8cqh;border-radius:0;text-align:left}
.tbl.lay.lay-wrongright th:first-child{grid-column:1} .tbl.lay.lay-wrongright th:last-child{grid-column:3;color:var(--t-teal)}
.tbl.lay.lay-wrongright th[data-tone]::before{display:none}
.tbl.lay.lay-wrongright tbody{display:flex;flex-direction:column}
.tbl.lay.lay-wrongright tbody tr{padding:1.5cqh 0;border-top:max(1px,.16cqh) solid #e2e8e6}
.tbl.lay.lay-wrongright tbody tr:first-child{border-top:0;padding-top:.4cqh}
.tbl.lay.lay-wrongright td,.tbl.lay.lay-wrongright td[data-tone]{background:none;padding:.4cqh .6cqw;border-radius:1cqh}
.tbl.lay.lay-wrongright td:first-child{grid-column:1;color:var(--t-ink)}
.tbl.lay.lay-wrongright td:last-child{grid-column:3;position:relative;color:var(--t-teal);font-weight:700}
.tbl.lay.lay-wrongright td:last-child .tw{color:var(--t-teal)}
/* the curved arrow: a quarter of an ellipse from the wrong down and round to the right, its head */
.tbl.lay.lay-wrongright td:last-child::before{content:"";display:block;position:absolute;left:-6.6cqw;top:50%;
  width:4.8cqw;height:4.2cqh;margin-top:-4.4cqh;box-sizing:border-box;border:max(2px,.42cqh) solid transparent;
  border-left-color:var(--t-pen);border-bottom-color:var(--t-pen);border-bottom-left-radius:100%;pointer-events:none}
.tbl.lay.lay-wrongright td:last-child::after{content:"";position:absolute;left:-2.2cqw;top:50%;margin-top:-1.2cqh;
  border-top:1cqh solid transparent;border-bottom:1cqh solid transparent;border-left:1.5cqh solid var(--t-pen)}
.tbl.lay.lay-wrongright td.active,.tbl.core.lay.lay-wrongright.spot tbody tr.focus td.active{background:var(--sc-active);
  box-shadow:none}
.tbl.core.lay.lay-wrongright.spot tbody tr.focus{box-shadow:none;transform:none}
""",
    "coded": r"""
/* 2. a sentence as coloured parts (ADR 050): each part a rounded tile in its colour, its label a pill of the
   same colour above it, read left to right as the sentence is; a part is typed in as the narration reaches it */
.tbl.lay.lay-coded table{display:block}
.tbl.lay.lay-coded thead{display:none}
.tbl.lay.lay-coded tbody{display:flex;flex-direction:column;gap:2.4cqh}
.tbl.lay.lay-coded tr{display:flex;flex-wrap:nowrap;gap:1.6cqh 1.2cqw;align-items:stretch}
.tbl.lay.lay-coded tbody tr td:nth-child(n){position:relative;flex:1 1 auto;min-width:10cqw;overflow-wrap:normal;max-width:100%;margin-top:5.4cqh;
  background:var(--c);color:var(--con);border-radius:2.8cqh;padding:2.4cqh 1.8cqw;font-weight:700;
  font-size:calc(var(--tf,3.2cqh) * 1.12);line-height:1.25;text-align:center;box-sizing:border-box;min-height:11cqh}
.tbl.lay.lay-coded td .tw{color:inherit}
.tbl.lay.lay-coded td[data-label]::before{content:attr(data-label);display:block;position:absolute;left:0;right:0;
  top:-5.4cqh;margin:0 auto;width:max-content;max-width:100%;box-sizing:border-box;background:var(--c);color:var(--con);
  font-size:2.2cqh;line-height:1.2;font-weight:800;letter-spacing:.08em;text-transform:uppercase;border-radius:999px;
  padding:.9cqh 1.6cqw;white-space:nowrap}
.tbl.lay.lay-coded td.active,.tbl.core.lay.lay-coded.spot tbody tr.focus td.active{background:var(--c);
  box-shadow:0 0 0 .6cqh var(--sc-active)}
.tbl.core.lay.lay-coded.spot tbody tr.focus{box-shadow:none;transform:none}
""",
    "opener": r"""
/* 2. a phrase first (ADR 050): each sentence its kind as a small pill, the phrase that opens it in a tile of
   that colour, then the rest of the sentence in plain ink; the colour names the kind */
.tbl.lay.lay-opener table{display:block}
.tbl.lay.lay-opener thead{display:none}
.tbl.lay.lay-opener tbody{display:flex;flex-direction:column;gap:1.8cqh}
.tbl.lay.lay-opener tr{display:grid;grid-template-columns:auto minmax(0,1fr);column-gap:1.4cqw;row-gap:.7cqh;
  align-items:center}
.tbl.lay.lay-opener tbody tr td:first-child{grid-column:1;grid-row:1;justify-self:start;background:var(--c);color:var(--con);
  font-size:2.1cqh;line-height:1.2;font-weight:800;letter-spacing:.08em;text-transform:uppercase;border-radius:999px;
  padding:.7cqh 1.4cqw}
.tbl.lay.lay-opener tbody tr td:nth-child(2){grid-column:1;grid-row:2;align-self:stretch;background:var(--cs);color:var(--t-ink);
  font-weight:700;border-radius:2.2cqh;padding:1.1cqh 1.4cqw;max-width:36cqw;box-shadow:inset .8cqh 0 0 var(--c)}
.tbl.lay.lay-opener td:nth-child(3){grid-column:2;grid-row:2;color:var(--t-ink)}
.tbl.lay.lay-opener td.active,.tbl.core.lay.lay-opener.spot tbody tr.focus td.active{background:var(--sc-active);
  box-shadow:none}
.tbl.core.lay.lay-opener.spot tbody tr.focus{box-shadow:none;transform:none}
""",
    "timeline": r"""
/* 3. a timeline (ADR 050): each row a round marker on a teal line, in its colour, its words under it and a
   handwritten note under those; read left to right in time order */
.tbl.lay.lay-timeline table{display:block}
.tbl.lay.lay-timeline thead{display:none}
.tbl.lay.lay-timeline tbody{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(0,1fr);column-gap:2cqw}
.tbl.lay.lay-timeline tr{display:flex;flex-direction:column;align-items:center;position:relative;text-align:center}
.tbl.lay.lay-timeline tr:not(:last-child)::after{content:"";position:absolute;left:50%;top:6.5cqh;width:calc(100% + 2cqw);
  height:max(2px,.9cqh);margin-top:-.45cqh;background:var(--t-teal);z-index:0}
.tbl.lay.lay-timeline tbody tr td:first-child{position:relative;z-index:1;width:13cqh;height:13cqh;border-radius:50%;
  background:var(--c);color:var(--con);font-weight:800;font-size:3.4cqh;line-height:13cqh;white-space:nowrap;
  overflow:hidden;padding:0}
.tbl.lay.lay-timeline td:nth-child(2){margin-top:2.4cqh;font-weight:800;font-size:3cqh;color:var(--t-ink)}
.tbl.lay.lay-timeline td:nth-child(3){margin-top:1cqh;font-family:var(--t-hand,cursive);font-size:3.4cqh;line-height:normal;
  color:var(--t-ink2,#536866)}
.tbl.core.lay.lay-timeline.spot tbody tr.focus{box-shadow:none;transform:none}
""",
    "columns": r"""
/* 4. rounded columns (ADR 050): each column's head a solid pill (teal, amber, coral, blue), its cells soft
   pills of the same colour under it; a row is still taught as one row */
.tbl.lay.lay-columns table{display:block}
.tbl.lay.lay-columns thead tr,.tbl.lay.lay-columns tbody tr{display:grid;column-gap:1.6cqw;align-items:stretch;
  grid-template-columns:repeat(var(--cn,2),minmax(0,1fr))}
.tbl.lay.lay-columns[data-cols="3"]{--cn:3} .tbl.lay.lay-columns[data-cols="4"]{--cn:4}
.tbl.lay.lay-columns[data-cols="2"][data-cw="first"] tr{grid-template-columns:24% minmax(0,1fr)}
.tbl.lay.lay-columns[data-cols="2"][data-cw="last"] tr{grid-template-columns:minmax(0,1fr) 30%}
.tbl.lay.lay-columns[data-cols="3"][data-cw="first"] tr{grid-template-columns:15% minmax(0,1fr) minmax(0,1fr)}
.tbl.lay.lay-columns[data-cols="3"][data-cw="last"] tr{grid-template-columns:minmax(0,1fr) minmax(0,1fr) 22%}
.tbl.lay.lay-columns[data-cols="4"][data-cw="first"] tr{grid-template-columns:13% repeat(3,minmax(0,1fr))}
.tbl.lay.lay-columns[data-cols="4"][data-cw="last"] tr{grid-template-columns:repeat(3,minmax(0,1fr)) 18%}
.tbl.lay.lay-columns thead tr{margin-bottom:1.4cqh}
.tbl.lay.lay-columns thead tr th:nth-child(n){border-radius:999px;padding:1.3cqh 1.4cqw;text-align:center;font-weight:800;font-size:2.4cqh;
  line-height:1.2;letter-spacing:.06em;text-transform:uppercase;color:#fff;background:var(--t-teal)}
.tbl.lay.lay-columns th:nth-child(2){background:var(--t-amber);color:var(--t-ink)}
.tbl.lay.lay-columns th:nth-child(3){background:var(--t-coral);color:var(--t-ink)}
.tbl.lay.lay-columns th:nth-child(4){background:var(--t-blue);color:var(--t-ink)}
.tbl.lay.lay-columns th[data-tone]::before{display:none}
.tbl.lay.lay-columns tbody{display:flex;flex-direction:column;gap:1.3cqh}
.tbl.lay.lay-columns tbody tr td:nth-child(n){border-radius:2.6cqh;padding:1.3cqh 1.6cqw;color:var(--t-ink);background:var(--t-teal-s);
  align-self:stretch}
.tbl.lay.lay-columns td:nth-child(2){background:var(--t-amber-s)} .tbl.lay.lay-columns td:nth-child(3){background:var(--t-coral-s)}
.tbl.lay.lay-columns td:nth-child(4){background:var(--t-blue-s)}
.tbl.lay.lay-columns td[data-tone]{color:var(--t-ink)}
.tbl.lay.lay-columns[data-cw="first"] td:first-child,.tbl.lay.lay-columns[data-cw="last"] td:last-child{font-weight:700;
  text-align:center;align-content:center}
.tbl.lay.lay-columns td.active,.tbl.core.lay.lay-columns.spot tbody tr.focus td.active{background:var(--sc-active);
  box-shadow:none}
.tbl.core.lay.lay-columns.spot tbody tr.focus{box-shadow:none;transform:scale(calc(1 + .004 * var(--sc-motion, 1)))}
""",
    "parts": r"""
/* 5. a letter and its parts (ADR 050): the letter one white sheet with a teal edge, each part's name a pill in
   its colour beside its paragraph, a line from the pill to the sheet; a part not written out is grey lines */
.tbl.lay.lay-parts table{display:block}
.tbl.lay.lay-parts thead tr,.tbl.lay.lay-parts tbody tr{display:grid;grid-template-columns:18% minmax(0,1fr);column-gap:2.4cqw}
.tbl.lay.lay-parts th{background:none;color:var(--sc-muted2,#5d7270);font-size:2.2cqh;line-height:1.3;font-weight:700;
  padding:0 2cqw .8cqh;text-align:left;border-radius:0}
.tbl.lay.lay-parts th:first-child{text-align:right;padding-right:0}
.tbl.lay.lay-parts tbody tr td:first-child{align-self:center;justify-self:end;position:relative;background:var(--c);color:var(--con);
  font-weight:700;font-size:2.4cqh;line-height:1.2;border-radius:999px;padding:.9cqh 1.6cqw;text-align:center}
.tbl.lay.lay-parts td:first-child::after{content:"";display:block;position:absolute;left:100%;top:50%;width:2.4cqw;
  height:max(2px,.32cqh);margin-top:max(-1px,-.16cqh);background:var(--t-teal)}
.tbl.lay.lay-parts td:last-child{background:#fff;border-left:max(2px,.36cqh) solid var(--t-teal);
  border-right:max(2px,.36cqh) solid var(--t-teal);padding:.9cqh 1.6cqw;line-height:1.34;color:var(--t-ink)}
.tbl.lay.lay-parts tbody tr:first-child td:last-child{border-top:max(2px,.36cqh) solid var(--t-teal);
  border-radius:1.6cqh 1.6cqh 0 0;padding-top:1.8cqh}
.tbl.lay.lay-parts tbody tr:last-child td:last-child{border-bottom:max(2px,.36cqh) solid var(--t-teal);
  border-radius:0 0 1.6cqh 1.6cqh;padding-bottom:1.8cqh}
.tbl.lay.lay-parts td[data-dash]::before{content:"";display:block;height:2.6em;background:
  repeating-linear-gradient(180deg,transparent 0 .55em,var(--t-teal-s) .55em 1.05em,transparent 1.05em 1.3em)}
/* a long letter (data-flow="2", ADR 050 amendment (1)): its words at full size, the paragraphs flowing down two
   columns of one sheet, in reading order; each part's name a pill at the start of its paragraph */
.tbl.lay.lay-parts[data-flow="2"]{position:relative;background:#fff;border:max(2px,.36cqh) solid var(--t-teal);
  border-radius:1.8cqh;padding:0 1.3cqw;margin-top:1.4cqh}
.tbl.lay.lay-parts[data-flow="2"] table{padding:2cqh 0 .3cqh}
.tbl.lay.lay-parts[data-flow="2"] thead tr{display:block}
.tbl.lay.lay-parts[data-flow="2"] th:first-child{display:none}
.tbl.lay.lay-parts[data-flow="2"] th:last-child{display:block;position:absolute;left:1.6cqw;top:-1.6cqh;padding:.3cqh 1.2cqw;
  line-height:1.2;text-align:left;color:#fff;background:var(--t-teal);border-radius:999px}
.tbl.lay.lay-parts[data-flow="2"] tbody{display:block;column-count:2;column-gap:2.4cqw;
  column-rule:max(1px,.18cqh) solid var(--t-teal-s)}
.tbl.lay.lay-parts[data-flow="2"] tbody tr{display:block;orphans:2;widows:2;padding:0 0 .6cqh}
.tbl.lay.lay-parts[data-flow="2"] tbody tr td:first-child{float:left;justify-self:auto;align-self:auto;
  margin:.1cqh .8cqw 0 0;padding:.3cqh 1.1cqw;font-size:2.4cqh;line-height:1.1}
.tbl.lay.lay-parts[data-flow="2"] td:first-child::after{content:none}
.tbl.lay.lay-parts[data-flow="2"] tbody tr td:last-child{display:block;border:0;border-radius:1.2cqh;padding:0;
  line-height:1.2;background:none}
.tbl.lay.lay-parts[data-flow="2"] tbody tr td:last-child.active{background:var(--sc-active);box-shadow:0 0 0 .8cqh var(--sc-active)}
.tbl.lay.lay-parts td.active,.tbl.core.lay.lay-parts.spot tbody tr.focus td.active{box-shadow:none}
.tbl.lay.lay-parts td:last-child.active,.tbl.core.lay.lay-parts.spot tbody tr.focus td:last-child.active{
  background:var(--sc-active)}
.tbl.core.lay.lay-parts.spot tbody tr.focus{box-shadow:none;transform:none}
""",
    "badges": r"""
/* 6. key points as round badges (ADR 050): each a solid circle in its colour holding the point, a handwritten
   note under it; on a recap board the cards stand side by side */
.tbl.lay.lay-badges table{display:block}
.tbl.lay.lay-badges thead{display:none}
.tbl.lay.lay-badges tbody{display:flex;flex-wrap:wrap;justify-content:center;gap:2.6cqh 4cqw}
.tbl.lay.lay-badges tr{display:flex;flex-direction:column;align-items:center;flex:0 1 28%;text-align:center}
.tbl.lay.lay-badges tbody tr td:first-child{display:grid;place-content:center;width:25cqh;height:25cqh;border-radius:50%;
  background:var(--c);color:var(--con);font-weight:800;font-size:3.4cqh;line-height:1.2;padding:2.6cqh;box-sizing:border-box}
.tbl.lay.lay-badges td:nth-child(2){margin-top:2.2cqh;font-family:var(--t-hand,cursive);font-size:3.9cqh;line-height:normal;
  color:var(--t-pen)}
.tbl.core.lay.lay-badges.spot tbody tr.focus{box-shadow:none;transform:none}
#cam:has(> .card.lay-badges){justify-content:center;align-content:center;column-gap:4cqw}
#cam > .card.lay-badges{flex:0 1 30%;background:none;border:0;overflow:visible;padding:0;display:flex;
  flex-direction:column;align-items:center;text-align:center}
.card.lay-badges .cardhd{display:grid;place-content:center;width:24cqh;height:24cqh;border-radius:50%;
  background:var(--c);color:var(--con);font-size:3.5cqh;line-height:1.15;font-weight:800;letter-spacing:0;
  text-transform:none;padding:2.4cqh;box-sizing:border-box}
.card.lay-badges .cardbd{display:block;padding:2.2cqh 0 0;font-family:var(--t-hand,cursive);font-size:4cqh;line-height:normal;
  font-weight:500;color:var(--t-ink)}
#cam > .card.lay-badges.on:not([data-layer="fixed"]):not([data-oa-layer="fixed"]){animation-name:t-pop}
""",
    "ruled": r"""
/* 7. a paragraph on ruled paper (ADR 050): a white sheet with blue rules and a red margin, the lines in print
   (a learner's sentences are never in the hand: amendment (1), rule 2), their numbers in the margin; the
   narration's pen circles the errors, a sticky note advises */
.tbl.lay.lay-ruled{background:#fff;border-radius:1.6cqh;padding:2.2cqh 2.4cqw 2.6cqh;
  box-shadow:0 .6cqh 2.2cqh rgba(11,60,59,.08)}
.tbl.lay.lay-ruled table{display:table;width:100%;border-collapse:collapse;table-layout:fixed}
.tbl.lay.lay-ruled thead{display:table-header-group} .tbl.lay.lay-ruled tbody{display:table-row-group}
.tbl.lay.lay-ruled tr,.tbl.lay.lay-ruled thead tr{display:table-row} .tbl.lay.lay-ruled td,.tbl.lay.lay-ruled th{display:table-cell}
.tbl.lay.lay-ruled colgroup{display:table-column-group}
.tbl.lay.lay-ruled[data-cols="2"] col:first-child{width:7%!important} .tbl.lay.lay-ruled[data-cols="2"] col:last-child{width:93%!important}
.tbl.lay.lay-ruled th{background:none;color:var(--sc-muted2,#5d7270);font-size:2.2cqh;line-height:1.3;font-weight:700;
  text-align:left;padding:0 1.2cqw 1.4cqh;border-radius:0;vertical-align:bottom}
.tbl.lay.lay-ruled td{background:none;vertical-align:top;color:var(--t-ink);
  font-size:max(calc(var(--tf,3.2cqh) * 1.1),3.2cqh);line-height:1.7;font-weight:400;padding:0 1.2cqw;
  background-image:repeating-linear-gradient(180deg,transparent 0 calc(1.7em - max(1px,.18cqh)),
    var(--t-rule,#c9e2e8) calc(1.7em - max(1px,.18cqh)) 1.7em);background-origin:content-box;background-clip:content-box}
.tbl.lay.lay-ruled[data-cols="2"] td:first-child{font-size:2.6cqh;
  line-height:calc(max(calc(var(--tf,3.2cqh) * 1.1),3.2cqh) * 1.7);color:var(--sc-muted2,#5d7270);text-align:right;padding-right:1.4cqw;
  border-right:max(1px,.2cqh) solid #f1b5ae;background-image:none}
.tbl.lay.lay-ruled td.active,.tbl.core.lay.lay-ruled.spot tbody tr.focus td.active{background-color:var(--sc-active);
  box-shadow:none}
.tbl.core.lay.lay-ruled.spot tbody tr.focus{filter:none;box-shadow:none;transform:none}
""",
    "beforeafter": r"""
/* 8. before and after (ADR 050): two panels side by side, the before on coral, the after on teal, their heads
   in capitals; each sentence with its word count in a circle of the panel's colour, so the saving is seen */
.tbl.lay.lay-beforeafter table{display:block}
.tbl.lay.lay-beforeafter thead tr,.tbl.lay.lay-beforeafter tbody tr{display:grid;
  grid-template-columns:minmax(0,1fr) minmax(0,1fr);column-gap:3cqw}
.tbl.lay.lay-beforeafter th{background:var(--t-coral-s);color:#b8352a;font-size:3.1cqh;line-height:1.2;font-weight:800;
  letter-spacing:.08em;text-transform:uppercase;padding:2.2cqh 2.2cqw 1.2cqh;border-radius:2.8cqh 2.8cqh 0 0;text-align:left}
.tbl.lay.lay-beforeafter th:last-child{background:var(--t-teal-s);color:var(--t-teal)}
.tbl.lay.lay-beforeafter th[data-tone]::before{display:none}
.tbl.lay.lay-beforeafter td,.tbl.lay.lay-beforeafter td[data-tone]{position:relative;background:var(--t-coral-s);
  color:var(--t-ink);padding:1.4cqh 2cqw 1.4cqh calc(2.4cqw + 13.6cqh);min-height:15cqh;border-radius:0;
  border-top:max(1px,.3cqh) solid #fff}
.tbl.lay.lay-beforeafter td:last-child,.tbl.lay.lay-beforeafter td:last-child[data-tone]{background:var(--t-teal-s)}
.tbl.lay.lay-beforeafter td .tw{color:var(--t-ink)}
.tbl.lay.lay-beforeafter tbody tr:last-child td{border-radius:0 0 2.8cqh 2.8cqh;padding-bottom:2.4cqh}
.tbl.lay.lay-beforeafter td[data-count]::before{content:attr(data-count);display:block;
  position:absolute;left:2cqw;top:1.6cqh;width:12.4cqh;height:12.4cqh;border-radius:50%;background:var(--t-coral);
  color:#0c2524;font-weight:800;font-size:5cqh;line-height:1;text-align:center;padding-top:2.1cqh;box-sizing:border-box;
  margin:0}
.tbl.lay.lay-beforeafter td[data-count]::after{content:"words";display:block;position:absolute;left:2cqw;
  top:calc(1.6cqh + 7.7cqh);width:12.4cqh;text-align:center;font-weight:800;font-size:2.4cqh;line-height:1;
  color:#0c2524}
.tbl.lay.lay-beforeafter td:last-child[data-count]::before{background:var(--t-teal);color:#fff}
.tbl.lay.lay-beforeafter td:last-child[data-count]::after{color:#fff}
.tbl.lay.lay-beforeafter td.active,.tbl.core.lay.lay-beforeafter.spot tbody tr.focus td.active{
  background-color:var(--sc-active);box-shadow:none}
.tbl.core.lay.lay-beforeafter.spot tbody tr.focus{box-shadow:none;transform:none}
""",
    "choices": r"""
/* 9. choice pills (ADR 050): short phrases as solid pills, each in its colour; their labels above them when
   every column has one, or the bank's name above them all */
.tbl.lay.lay-choices table{display:block}
.tbl.lay.lay-choices thead{display:none}
.tbl.lay.lay-choices[data-titled] thead{display:block}
.tbl.lay.lay-choices[data-titled] th+th{display:none}
.tbl.lay.lay-choices th{background:none;color:var(--t-pen);font-family:var(--t-hand,cursive);font-size:3.6cqh;
  line-height:normal;font-weight:700;text-transform:none;letter-spacing:0;padding:0 .4cqw 1.2cqh;text-align:left;border-radius:0}
.tbl.lay.lay-choices tbody{display:flex;flex-wrap:wrap;gap:1.8cqh 1.4cqw;align-items:flex-end}
.tbl.lay.lay-choices tr{display:contents}
.tbl.lay.lay-choices tbody tr td:nth-child(n){position:relative;background:var(--c);color:var(--con);font-weight:700;border-radius:999px;
  padding:1.3cqh 2.4cqw;text-align:center}
.tbl.lay.lay-choices td[data-label]{margin-top:4cqh}
.tbl.lay.lay-choices td[data-label]::before{content:attr(data-label);display:block;position:absolute;left:0;right:0;
  top:-3.6cqh;margin:0;font-size:2.1cqh;line-height:1.2;font-weight:800;letter-spacing:.06em;text-transform:uppercase;
  color:var(--sc-muted2,#5d7270);white-space:nowrap;text-align:center}
.tbl.lay.lay-choices td.active,.tbl.core.lay.lay-choices.spot tbody tr.focus td.active{background:var(--c);
  box-shadow:0 0 0 .6cqh var(--sc-active)}
""",
    "path": r"""
/* 10. steps on a curved path (ADR 050): each row a numbered circle in its colour, alternately low and high on
   a teal curve (an empty drawing), its name under it in bold and a handwritten note */
.tbl.lay.lay-path{position:relative}
.tbl.lay.lay-path .t-curve{position:absolute;left:0;top:0;width:100%;height:30cqh;overflow:visible;pointer-events:none}
.tbl.lay.lay-path .t-curve path{fill:none;stroke:var(--t-teal);stroke-width:.7;stroke-linecap:round}
.tbl.lay.lay-path table{display:block;position:relative}
.tbl.lay.lay-path thead{display:none}
.tbl.lay.lay-path tbody{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(0,1fr);column-gap:1.6cqw;
  counter-reset:t-step}
.tbl.lay.lay-path tr{display:flex;flex-direction:column;align-items:center;text-align:center;counter-increment:t-step}
.tbl.lay.lay-path tr::before{content:counter(t-step);display:block;width:13cqh;height:13cqh;border-radius:50%;
  background:var(--c);color:var(--con);font-weight:800;font-size:5cqh;line-height:13cqh;text-align:center;
  margin-top:15.5cqh;flex:none}
.tbl.lay.lay-path tr:nth-child(even)::before{margin-top:1.5cqh}
.tbl.lay.lay-path td:first-child{margin-top:1.8cqh;font-weight:800;font-size:3cqh;line-height:1.2;color:var(--t-ink)}
.tbl.lay.lay-path td:nth-child(2){margin-top:1cqh;font-family:var(--t-hand,cursive);font-size:3.4cqh;line-height:normal;
  color:var(--t-pen)}
.tbl.core.lay.lay-path.spot tbody tr.focus{box-shadow:none;transform:none}
""",
    "compare": r"""
/* 11. two things compared side by side (ADR 050): each framed in its colour, teal and coral, with rounded
   corners; its head (a comparison's words up to the first colon, or a table's column label) a solid pill, the
   rest under it */
.chg.lay-compare{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:1.4cqh 2.6cqw;align-items:stretch;
  background:none;padding:.8cqh 0 0;border:0;box-shadow:none}
.chg.lay-compare:is([data-layer="fixed"],[data-oa-layer="fixed"]){font-size:4.2cqh;line-height:1.35}
.chg.lay-compare:is([data-layer="fixed"],[data-oa-layer="fixed"]) :is(.chg-from,.chg-to){padding:2.4cqh 2.4cqw 3cqh}
.chg.lay-compare .chg-cap{grid-column:1 / -1;font-family:var(--t-hand,cursive);font-size:3.8cqh;line-height:1.3;
  font-weight:700;color:var(--t-pen)}
.chg.lay-compare .chg-arrow{display:none}
.chg.lay-compare .chg-from,.chg.lay-compare .chg-to{display:block;background:#fff;color:var(--t-ink);
  border:max(2px,.4cqh) solid var(--t-teal);border-radius:2.8cqh;padding:1.8cqh 2cqw 2.2cqh;font-weight:400}
.chg.lay-compare .chg-to{border-color:var(--t-coral)}
.chg.lay-compare .cmp-h{display:block;background:var(--t-teal-s);color:var(--t-teal);font-weight:700;border-radius:999px;
  padding:.9cqh 1.6cqw;margin-bottom:1.6cqh;text-align:center;line-height:1.25}
.chg.lay-compare .chg-to .cmp-h{background:var(--t-coral-s);color:#a8392c}
.chg.lay-compare.fx-lift{box-shadow:none}
.chg.lay-compare.fx-lift :is(.chg-from,.chg-to){box-shadow:var(--sc-shadow)}
/* as a table: two cards side by side, each its place's head, its example sentences one under another (the
   words a sentence puts in that place ringed in the teacher's red pen: `block_accents`) and, in its last row,
   the rule in his hand (the owner's Word Order slide 3; ADR 050 amendment (1)) */
.tbl.lay.lay-compare table{display:block}
.tbl.lay.lay-compare thead tr,.tbl.lay.lay-compare tbody tr{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);
  column-gap:3cqw}
.tbl.lay.lay-compare thead tr th:nth-child(n){background:var(--t-teal-s);color:var(--t-teal);border-radius:2.8cqh 2.8cqh 0 0;
  padding:2.4cqh 2.4cqw 1.6cqh;text-align:left;font-size:3.6cqh;line-height:1.22;font-weight:800;letter-spacing:0;
  text-transform:none;margin:0}
.tbl.lay.lay-compare th:last-child{background:var(--t-amber-s);color:#7a4f00}
.tbl.lay.lay-compare th[data-tone]::before{display:none}
.tbl.lay.lay-compare tbody{display:block}
.tbl.lay.lay-compare tbody tr td:nth-child(n){background:var(--t-teal-s);color:var(--t-ink);border-radius:0;padding:1.1cqh 2.4cqw;
  text-align:left;font-weight:400;font-size:max(var(--tf,3.2cqh),3.2cqh);line-height:1.38}
.tbl.lay.lay-compare tbody tr td:last-child{background:var(--t-amber-s)}
.tbl.lay.lay-compare tbody tr:last-child td:nth-child(n){border-radius:0 0 2.8cqh 2.8cqh;padding-top:2.4cqh;padding-bottom:2.8cqh;
  font-family:var(--t-hand,cursive);font-size:calc(3.2cqh * 1.3);line-height:normal;font-weight:700;color:var(--t-teal)}
.tbl.lay.lay-compare tbody tr:last-child td:last-child{color:#7a4f00}
.tbl.lay.lay-compare .acc{display:inline-block;white-space:nowrap;font-weight:700;color:var(--t-ink);line-height:1.2;
  padding:.35cqh .7cqw;margin:-.35cqh -.2cqw;border:max(2px,.38cqh) solid var(--t-pen);border-radius:50%}
.tbl.lay.lay-compare td.active,.tbl.core.lay.lay-compare.spot tbody tr.focus td.active{background:var(--sc-active);
  box-shadow:none}
.tbl.core.lay.lay-compare.spot tbody tr.focus{box-shadow:none;transform:none}
""",
})
ROOT_CLASS = re.compile(r'^<div class="([^"]*)"')


def layout_css(blocks: dict) -> str:
    """The rules of the phase 2 layouts and forms a lesson's blocks use (ADR 043
    amendment (3)), in a fixed order; "" for a lesson that uses none."""
    used = set()
    for b in blocks.values():
        m = ROOT_CLASS.match(b.get("html") or "")
        cls = set(m.group(1).split()) if m else set()
        if "lay" not in cls:
            continue
        ncol = len(b.get("header") or (b.get("rows") or [[]])[0])
        if "lay-fix" in cls and ncol == 2:
            used.add("fix2")
        if "lay-letter" in cls and ncol == 1:
            used.add("letter1")
        if "lay-pair" in cls:
            used.add("pair")
        if "lay-paper" in cls:
            used.add("paper")
        if "lay-acronym" in cls:
            used.add("acronym")
        if "lay-skeleton" in cls:
            used.add("skeleton")
        for k in ADR048_LAYOUTS:
            if "lay-" + k in cls:
                used.add(k)
    # the teal look's layouts (ADR 050): a comparison or a recap card carries its layout as a class with no `lay`
    for b in blocks.values():
        m = ROOT_CLASS.match(b.get("html") or "")
        cls = set(m.group(1).split()) if m else set()
        for k in ADR050_LAYOUTS:
            if "lay-" + k in cls:
                used.update(("tset", k))
    return "".join(LAYOUT_CSS[k] for k in LAYOUT_CSS if k in used)


def compare_heads(html: str) -> str:
    """A comparison drawn as two framed things side by side (ADR 050, the owner's pattern 11): the
    words of each side up to its first colon, when they are a short lead, wrapped in a span `cmp-h`
    (drawn as the side's pill head) and the rest in `cmp-b`. The words and the space between stay."""
    def one(m):
        inner = m.group(2)
        hm = COMPARE_HEAD.match(inner)
        if not hm:
            return m.group(0)
        return (m.group(1) + '<span class="cmp-h">' + hm.group(1) + "</span>" + hm.group(2)
                + '<span class="cmp-b">' + hm.group(3) + "</span>" + m.group(3))
    return re.sub(r'(<span class="chg-(?:from|to)">)(.*?)(</span>)', one, html, flags=re.S)


CONTENTS_SEP = " · "          # between a category's sections (build_lesson_boards.py)
CS = re.compile(r'<div class="cs">(.*?)</div>', re.S)


def contents_parts(html: str) -> str:
    """A contents item that lists two or more sections under its category: each
    section wrapped in its own `cp` span, so the stylesheet sets them one under
    the other (ADR 043). The words and the separators between them stay exactly
    as they are; an item with one section or none is unchanged."""
    m = CS.search(html)
    if not m or CONTENTS_SEP not in m.group(1):
        return html
    parts = m.group(1).split(CONTENTS_SEP)
    if any(not p.strip() for p in parts):
        return html
    inner = CONTENTS_SEP.join(f'<span class="cp">{p}</span>' for p in parts)
    return html[:m.start()] + '<div class="cs parts">' + inner + "</div>" + html[m.end():]


def accent_html(b: dict, html: str, phrases: list[str]) -> str:
    """The words a layout sets in its accent colour (sections.json `block_accents`,
    by bundle block id: a skeleton's purpose words): each phrase, found once in the
    block's html as it stands, wrapped in a span `acc`. A phrase found no times or
    more than once, or split by a tag, stops the build."""
    for p in phrases:
        needle = _html.escape(str(p), quote=False)
        hits = [m.start() for m in re.finditer(re.escape(needle), html)
                if html.rfind("<", 0, m.start()) <= html.rfind(">", 0, m.start())]
        if len(hits) != 1:
            raise SystemExit(f"REFUSED: sections.json block_accents: {p!r} is found {len(hits)} time(s) in the words "
                             f"of {b.get('id')}; once is needed")
        i = hits[0]
        html = html[:i] + '<span class="acc">' + needle + "</span>" + html[i + len(needle):]
    return html


def layout_html(b: dict, html: str, section_title: str | None, layout: str | None = None,
                accents: list[str] | None = None, look: str | None = None) -> str:
    """A style C block's html with its layout and its criterion's colour:

    - every block of a section named after one of the six criteria takes that
      criterion (`data-crit`), so its tables, its criterion card and its tints
      are in that criterion's colour;
    - a term box "The criterion" becomes the criterion's card: its colour and its
      monogram (`crit`, `data-mono`);
    - a contents item named after a criterion takes the criterion's colour;
    - a block with a `layout` (sections.json `block_layouts`) takes `lay
      lay-<layout>` and the attributes that layout reads;
    - its `accents` (sections.json `block_accents`), on a layout that draws them
      (ACCENT_LAYOUTS), each wrapped in a span `acc`;
    - in the teal look, a note the look sets in the teacher's hand that is longer
      than HAND_WORDS words takes `t-print`: it is set in print (ADR 050
      amendment (1), rule 2).

    The block's words, their order and its hooks never change (checked)."""
    before = _text(html)
    crit = CRIT_KEY.get((section_title or "").strip())
    t = b.get("type")
    if t == "picture":
        return html
    if t == "contents_item":
        if CRIT_KEY.get((b.get("text") or "").strip()):
            html = _add_root(html, attrs=_crit_attr(CRIT_KEY[b["text"].strip()]))
        html = contents_parts(html)
    elif crit:
        if t == "term_box" and (b.get("label") or "").strip() == CRITERION_LABEL:
            html = _add_root(html, "crit", _crit_attr(crit))
        else:
            html = _add_root(html, attrs=f' data-crit="{crit}"')
    if layout:
        why = check_layout(b.get("id", "?"), b, layout)
        if why:
            raise SystemExit("REFUSED: sections.json block_layouts: " + why)
        if t == "table":
            html = _table_html(b, html, layout)
        elif layout == "compare":
            html = _add_root(compare_heads(html), "lay-compare")
        elif layout == "badges":
            # a recap's cards as round badges (ADR 050), each its colour in turn, by its place among the
            # section's blocks (its id ends in its number: "_k02" is the second)
            km = re.search(r"_k(\d+)$", b.get("id") or "")
            i = int(km.group(1)) - 1 if km else 0
            html = _add_root(html, "lay-badges", f' data-c="{T_TRIO[i % 5]}"')
        else:
            html = _add_root(html, "lay-" + layout)
    if accents:
        if layout not in ACCENT_LAYOUTS:
            raise SystemExit(f"REFUSED: sections.json block_accents: {b.get('id')} has the layout {layout!r}, which "
                             f"draws no accent ({', '.join(ACCENT_LAYOUTS)})")
        html = accent_html(b, html, accents)
    if look == "teal" and t in HAND_TYPES and \
            len(WORD.findall(str(b.get("text") or ""))) > HAND_WORDS:
        html = _add_root(html, "t-print")
    if _text(html) != before:
        raise SystemExit(f"REFUSED: the layout of {b.get('id')} would change its words")
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


# The lesson types whose tables are documents, a letter or case notes, which the
# zoom is for (ADR 042 decision 4; ADR 043): Writing's. In any other lesson a
# table keeps rule 13's auto zoom, Grammar 6's board shown whole keeps the owner's
# "no zoom" (ADR 011 amendment of 2026-10-12), and a Reading or Listening text
# keeps its own lens, map, covering and transcript (ADR 026, ADR 030).
ZOOM_TYPES = ("writing",)


def zooms(lesson) -> bool:
    """Whether the lesson's documents take the style C zoom (ZOOM_TYPES)."""
    import lesson_type
    return lesson_type.of(lesson) in ZOOM_TYPES


def effects(boards: list[dict], blocks: dict, zoom: bool = True, nozoom=()) -> None:
    """Write each state's `effects` (bundle 1.22), in time order:

    lift  a block grows a very little, with the soft shadow, from `time` to
          `until` (rule 54):
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
          takes the view on from there (rule 55). Only where `zoom` is true: a
          lesson whose tables are documents (`zooms`, ADR 043), and never on a
          board in `nozoom` (sections.json `boards_nozoom`, ADR 049): a board
          shown whole that stays whole at every moment; its spotlight and its
          marks alone show the line being taught.
    """
    for bd in boards:
        fixed_txt = [i for i in bd["fixed"] if blocks[i]["type"] not in ("table", "picture", "lesson_title")]
        tbl = bd.get("table")
        doc = None
        # the paper beside the letter (ADR 045) is never zoomed: a zoom onto one
        # cell would take the piece of the paper or the part of the letter it
        # feeds out of view, and the two are shown to be seen together
        if zoom and tbl and bd.get("id") not in nozoom and not bd.get("split") and not bd.get("listen") \
                and not blocks[tbl].get("map") and PAPER_BESIDE not in (blocks[tbl].get("html") or ""):
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
                    # the sentence that names it: the one whose cues hold its
                    # reveal (its first word can be said a little before the
                    # sentence's recorded start, inside the last one's tail;
                    # ADR 043 decision 16); else the sentence it falls in
                    ends = [u["end"] for u in s["utterances"]
                            if any(c["type"] == "reveal" and c.get("block") == w for c in u["cues"])] \
                        or [u["end"] for u in s["utterances"] if u["start"] <= at + 1e-6 <= u["end"] + 0.5]
                    # a category whose sections the narration names one by one
                    # (a mark on each, after its reveal): until the last is named
                    # (ADR 043)
                    ends += [u["end"] for u in s["utterances"]
                             if any(c.get("block") == w and c["type"] not in ("reveal", "pause")
                                    and c["time"] > at + 1e-6 for c in u["cues"])]
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
# The teal look (ADR 050; docs/02-DESIGN-SYSTEM.md §1b): the owner's Canva patterns of 2026-11-01. Appended
# after style C's own rules (and the layouts') to the stylesheet of a lesson whose sections.json names it, so
# every other lesson's stylesheet is unchanged. Teal with warm accents on a warm white ground; rounded shapes;
# the teacher's notes in a hand, his advice on sticky notes, his marks in red pen; the contents board a path.
# ---------------------------------------------------------------------------
TEAL = {"teal": "#0b6e6d", "ink": "#173d3c", "ground": "#faf8f4", "amber": "#e2a72e", "coral": "#e57063",
        "blue": "#9ecfd8", "lilac": "#b8a6d6", "pen": "#c4362f", "sticky": "#f7e27f"}
HAND = 1.3          # the hand's size against body text: Caveat's x-height is about 0.4 em, IBM Plex's 0.52
LOOK_CSS = {"teal": r"""
/* --- The teal look (ADR 050; docs/02-DESIGN-SYSTEM.md §1b): teal with soft warm accents, light and airy;
   rounded shapes, no hard shadows; the teacher's hand for his notes, sticky notes for his advice, red pen for
   his marks. Style C's rules, effects and bundle stay; these come after them. --- */
.frame{--t-teal:""" + TEAL["teal"] + r""";--t-teal-d:#095a59;--t-ink:""" + TEAL["ink"] + r""";--t-ink2:#536866;
  --t-ground:""" + TEAL["ground"] + r""";--t-amber:""" + TEAL["amber"] + r""";--t-coral:""" + TEAL["coral"] + r""";
  --t-blue:""" + TEAL["blue"] + r""";--t-lilac:""" + TEAL["lilac"] + r""";
  --t-teal-s:#e5f0ef;--t-amber-s:#fbf0d5;--t-coral-s:#fce7e3;--t-blue-s:#e1f1f4;--t-lilac-s:#eee8f6;
  --t-pen:""" + TEAL["pen"] + r""";--t-sticky:""" + TEAL["sticky"] + r""";--t-rule:#c9e2e8;
  --t-hand:var(--font-hand,"Caveat"),"Ink Free","Bradley Hand","Segoe Print","Chalkboard SE",cursive;
  --sc-ink:var(--t-ink);--sc-muted:var(--t-ink2);--sc-muted2:#5d7270;--sc-faint:#9fb3b1;--sc-paper:#fff;
  --sc-note:var(--t-teal-s);--sc-line:#e2e8e6;--sc-right:var(--t-teal);--sc-right-bg:var(--t-teal-s);
  --sc-wrong:#b8352a;--sc-wrong-bg:var(--t-coral-s);--sc-gloss:#9a6406;--sc-gloss-bg:var(--t-amber-s);
  --sc-active:#fdefc6;--sc-shadow:0 .8cqh 2.6cqh rgba(11,60,59,.12);--k:var(--t-teal);--ks:var(--t-teal-s);
  background:var(--t-ground);color:var(--t-ink);border-color:#e6e2d8}
.hdr,.body,.ctl{background:var(--t-ground)}
.hdr{font-weight:800;color:var(--t-ink);letter-spacing:-.012em}
.ltitle{font-size:9cqh;line-height:1.05;font-weight:800;color:var(--t-ink);letter-spacing:-.025em}
/* the teacher's notes, written while he teaches, in his hand: no card, his ink, a size that reads as body
   text does (§3); the board's own sentences stay in print */
.plain.role-note:not([data-layer="fixed"]):not([data-oa-layer="fixed"]){background:none;border:0;
  padding:.4cqh .6cqw;font-family:var(--t-hand);font-size:calc(3.2cqh * """ + str(HAND) + r""");line-height:normal;
  font-weight:500;color:var(--t-ink)}
.plain.role-slide,.plain.role-note[data-layer="fixed"],.plain.role-note[data-oa-layer="fixed"]{background:#fff;
  box-shadow:0 .4cqh 1.6cqh rgba(11,60,59,.07)}
/* his advice on a sticky note: yellow, soft corners, a very small tilt, his hand */
.callout,.callout.warning,.callout.key_rule{background:var(--t-sticky);color:var(--t-ink);border:0;
  border-radius:.6cqh 2.6cqh 2.6cqh 2.6cqh;rotate:-.6deg;box-shadow:0 .7cqh 1.6cqh -.4cqh rgba(80,64,0,.22);
  font-family:var(--t-hand);font-size:calc(3.2cqh * """ + str(HAND) + r""");line-height:normal;font-weight:500}
.callout .badge-c,.key_rule .badge-c,.warning .badge-c{background:var(--t-ink);color:var(--t-sticky);
  font-family:var(--font-plex,"IBM Plex Sans"),system-ui,sans-serif;font-size:2.4cqh;width:4cqh;height:4cqh}
/* a grammar term: a white card ringed in lilac, its tag a lilac pill */
.term.tnote,.term.role-note{background:#fff;box-shadow:inset 0 0 0 max(1px,.32cqh) var(--t-lilac-s);border-radius:2.6cqh}
.term .lbl,.term.tnote .lbl{background:var(--t-lilac);color:var(--t-ink);border-radius:999px;padding:.3cqh 1.2cqw}
/* a word card: amber */
.gl{background:var(--t-amber-s);border-radius:2.6cqh} .gl-txt::before{background:var(--t-amber);color:var(--t-ink);border-radius:999px}
.gl-w{color:#7a4f00}
/* a wrong sentence: white, ringed in coral, its mark a coral badge; a right one teal */
.row.err{background:#fff;color:var(--t-ink);box-shadow:inset 0 0 0 max(1px,.32cqh) var(--t-coral-s);border-radius:999px}
.err .verdict{background:var(--t-coral);color:#fff}
.row.ans,.row.result{background:var(--t-teal-s);color:var(--t-teal)} .ans .verdict,.row.result .verdict{background:var(--t-teal)}
/* a comparison and a change card: white, rounded */
.chg{background:#fff;box-shadow:0 .4cqh 1.6cqh rgba(11,60,59,.07);border-radius:2.6cqh}
/* the contents board: a path of numbered circles, each in its colour in turn, one under the other, joined by
   a teal line (the owner's pattern 10, set vertically) */
#cam > .blk.citem{flex:0 0 100%;background:none;padding:.2cqh 1cqw 2.5cqh;margin-bottom:-2.5cqh;position:relative;gap:2cqw;
  box-sizing:border-box}
.citem .cnum{position:relative;z-index:1;width:6.8cqh;height:6.8cqh;font-size:3cqh;font-weight:800;
  background:var(--c,var(--t-teal));color:var(--con,#fff)}
.citem .ct{font-weight:700;font-size:3.7cqh;color:var(--t-ink)}
#cam:has(> .blk.citem){row-gap:2.5cqh}
#cam > .blk.citem::before,#cam > .blk.citem::after{content:"";position:absolute;left:calc(1cqw + var(--t-cr,3.4cqh) - .3cqh);
  width:.6cqh;background:var(--t-teal);z-index:0}
#cam > .blk.citem::before{top:0;height:calc(50% - 1.25cqh)}
#cam > .blk.citem::after{top:calc(50% - 1.25cqh);bottom:0}
#cam > .blk.citem:first-child::before,#cam > .blk.citem:last-child::after{content:none}
#cam > .blk.citem:nth-child(5n+1){--c:var(--t-amber);--con:var(--t-ink)}
#cam > .blk.citem:nth-child(5n+2){--c:var(--t-blue);--con:var(--t-ink)}
#cam > .blk.citem:nth-child(5n+3){--c:var(--t-lilac);--con:var(--t-ink)}
#cam > .blk.citem:nth-child(5n+4){--c:var(--t-coral);--con:var(--t-ink)}
#cam > .blk.citem:nth-child(5n){--c:var(--t-teal);--con:#fff}
.citem.fx-lift{box-shadow:none;transform:translateX(calc(.6cqw * var(--sc-motion, 1)))}
/* the teacher's red pen (§8): a circle is his ring, an underline and a strike his line; the marker stays */
:is(#marks,.oa-marks) .m-circle{border:max(2px,.42cqh) solid var(--t-pen)!important;border-radius:50%!important;
  box-shadow:0 0 0 max(1px,.08cqh) rgba(196,54,47,.25)!important}
:is(#marks,.oa-marks) .m-line,:is(#marks,.oa-marks) .m-tick{background:var(--t-pen)!important;border-radius:999px!important}
:is(#marks,.oa-marks) .m-strike{background:var(--t-pen)!important;border-radius:999px!important}
/* a fixed block enters as its board opens (§8g, ADR 050); the teal layouts' pieces enter in reading order */
@keyframes t-enter{from{opacity:0;transform:scale(.98)}to{opacity:1;transform:none}}
.blk:is([data-layer="fixed"],[data-oa-layer="fixed"]):not(.lay){animation:t-enter .45s cubic-bezier(.2,.7,.2,1) backwards}
@media (prefers-reduced-motion: reduce){.blk:is([data-layer="fixed"],[data-oa-layer="fixed"]){animation:none}}

/* --- Readable on a phone (ADR 050 amendment (1); the owner's review of Word Order draft.3, 2026-11-01;
   docs/02-DESIGN-SYSTEM.md §7k). In the 1600x900 frame, running text at least 26 px (2.9cqh) and a label at least
   20 px (2.3cqh); a hand note at 1.3 times that. Where a board does not fit at that size, its layout changes; its
   text is never set smaller (check_text_size.py). A layout's rules come after the look's, so each rule here is
   written under .frame to outrank them. --- */
.frame{--t-ink-d:#0c2524;--t-label:2.4cqh;--t-run:2.9cqh;--t-wash:rgba(250,248,244,.6)}
/* 1. no table set under the running size, whatever the fit chose; no label under the label size */
.frame .tbl.core table{font-size:max(var(--tf,2.6cqh),var(--t-run))}
.frame .tbl.lay td[data-label]::before,.frame .tbl.lay.lay-paper th,.frame .tbl.lay.lay-wrongright th,
.frame .tbl.lay.lay-parts th,.frame .tbl.lay.lay-ruled th,.frame .term .lbl,.frame .term.tnote .lbl,
.frame .gl-txt::before,.frame .gl-x::before,.frame .gl-m::before,.frame .tbl.lay.lay-coded td[data-label]::before,
.frame .tbl.lay.lay-choices td[data-label]::before,.frame .tbl.lay.lay-opener tbody tr td:first-child,
.frame .tbl.lay.lay-parts tbody tr td:first-child{font-size:var(--t-label)}
/* the paper and the letter beside it at a size that fills the board (the owner: "make the paper and the letter
   larger"), the paper's words in ink */
.frame .tbl.lay.lay-paper table{font-size:max(var(--tf,2.6cqh),3.9cqh);line-height:1.36}
.frame .tbl.lay.lay-paper td{color:var(--t-ink)}
.frame .tbl.lay.lay-paper th{color:var(--t-ink2)}
.frame .tbl.lay.lay-place[data-place="opening"] td:nth-child(3)::after{height:6.9cqh}
.frame .tbl.lay.lay-place[data-place="request"] td:nth-child(3)::before{height:6.9cqh}
/* 2. the hand is for short notes (about 15 words at most) and labels: a longer note is in print */
.frame .blk.t-print:is(.plain,.callout){font-family:var(--font-plex,"IBM Plex Sans"),system-ui,sans-serif;font-size:3.2cqh;
  line-height:1.42;font-weight:400}
.frame .card.lay-badges.t-print .cardbd{font-family:var(--font-plex,"IBM Plex Sans"),system-ui,sans-serif;font-size:3.2cqh;
  line-height:1.38;font-weight:400}
/* 5. a row the spotlight is not on keeps its words as they are, at full contrast: only its ground is lighter */
.frame .tbl.core.spot tbody tr:not(.focus) td,.frame .tbl.core.lay.spot tbody tr:not(.focus),
.frame .tbl.core.spot.cellspot tbody tr td{opacity:1}
.frame .tbl.core.spot:not(.lay-ruled) tbody tr:not(.focus) td,
.frame .tbl.core.spot.cellspot:not(.lay-ruled) tbody tr td:not(.lit){background-image:linear-gradient(var(--t-wash),var(--t-wash))}
.frame .tbl.core.spot tbody tr:not(.focus)[data-c],.frame .tbl.core.spot tbody tr:not(.focus) td[data-c]{--con:var(--t-ink-d)}
/* words on coral, and on a mid teal, in the darkest ink or in white (4.5:1 or more) */
.frame.frame :is(.lay,.lay-badges) [data-c="3"],.frame.frame .lay-badges[data-c="3"]{--con:var(--t-ink-d)}
.frame #cam > .blk.citem:nth-child(5n+4){--con:var(--t-ink-d)}
.frame .err .verdict{background:#b8352a}
/* 6. a mark never hides the words it marks: on a coloured tile the marker's band would sit on them, so the
   narration marks there with the pen's circle or line, under or around the words (the lesson's cue overrides) */
/* 7. a heading never leaves one or two words alone on its last line */
.frame :is(.hdr,.ltitle,th,.cmp-h,.cardhd,.citem .ct,.chg-cap,.lbl){text-wrap:balance}
/* 4. use the frame: six to eight contents items in two columns that fill the board, read down the first column
   and then the second (`order`; the site fixes #cam as a wrapping row, so the items are set half wide); each
   column's own line */
.frame #cam:has(> .blk.citem:nth-child(6)) > .blk.citem{flex:0 0 calc(50% - 1cqw);min-height:17.5cqh;align-items:center;
  gap:1.8cqw;--t-cr:5.5cqh}
.frame #cam:has(> .blk.citem:nth-child(6)) .citem .cnum{width:11cqh;height:11cqh;font-size:5cqh}
.frame #cam:has(> .blk.citem:nth-child(6)) .citem .ct{font-size:4.1cqh;line-height:1.2}
/* six: three rows */
.frame #cam:has(> .blk.citem:nth-child(6)):not(:has(> .blk.citem:nth-child(7))) > .blk.citem:nth-child(1){order:1}
.frame #cam:has(> .blk.citem:nth-child(6)):not(:has(> .blk.citem:nth-child(7))) > .blk.citem:nth-child(2){order:3}
.frame #cam:has(> .blk.citem:nth-child(6)):not(:has(> .blk.citem:nth-child(7))) > .blk.citem:nth-child(3){order:5}
.frame #cam:has(> .blk.citem:nth-child(6)):not(:has(> .blk.citem:nth-child(7))) > .blk.citem:nth-child(4){order:3}
.frame #cam:has(> .blk.citem:nth-child(6)):not(:has(> .blk.citem:nth-child(7))) > .blk.citem:nth-child(5){order:5}
.frame #cam:has(> .blk.citem:nth-child(6)):not(:has(> .blk.citem:nth-child(7))) > .blk.citem:nth-child(6){order:7}
.frame #cam:has(> .blk.citem:nth-child(6)):not(:has(> .blk.citem:nth-child(7))) > .blk.citem:nth-child(3)::after,
.frame #cam:has(> .blk.citem:nth-child(6)):not(:has(> .blk.citem:nth-child(7))) > .blk.citem:nth-child(4)::before{content:none}
/* seven or eight: four rows */
.frame #cam:has(> .blk.citem:nth-child(7)) > .blk.citem:nth-child(1){order:1}
.frame #cam:has(> .blk.citem:nth-child(7)) > .blk.citem:nth-child(2){order:3}
.frame #cam:has(> .blk.citem:nth-child(7)) > .blk.citem:nth-child(3){order:5}
.frame #cam:has(> .blk.citem:nth-child(7)) > .blk.citem:nth-child(4){order:7}
.frame #cam:has(> .blk.citem:nth-child(7)) > .blk.citem:nth-child(5){order:2}
.frame #cam:has(> .blk.citem:nth-child(7)) > .blk.citem:nth-child(6){order:4}
.frame #cam:has(> .blk.citem:nth-child(7)) > .blk.citem:nth-child(7){order:6}
.frame #cam:has(> .blk.citem:nth-child(7)) > .blk.citem:nth-child(8){order:8}
.frame #cam:has(> .blk.citem:nth-child(7)) > .blk.citem:nth-child(4)::after,
.frame #cam:has(> .blk.citem:nth-child(7)) > .blk.citem:nth-child(5)::before{content:none}
.frame .tbl.lay.lay-coded tbody{gap:7cqh}
.frame .tbl.lay.lay-coded tbody tr td:nth-child(n){font-size:calc(max(var(--tf,3.2cqh),3.2cqh) * 1.2);min-height:19cqh;
  padding:3cqh 1.8cqw;margin-top:6.4cqh;align-content:center}
.frame .tbl.lay.lay-coded tbody tr td:not(:last-child){flex:0 0 auto;min-width:11cqw}
.frame .tbl.lay.lay-coded tbody tr td:last-child{flex:1 1 0}
.frame .tbl.lay.lay-coded td[data-label]::before{top:-6.2cqh;font-size:2.6cqh}
.frame .tbl.lay.lay-choices tbody tr td:nth-child(n){font-size:max(var(--tf,3.2cqh),3.9cqh);padding:1.7cqh 2.6cqw}
.frame .tbl.lay.lay-choices td[data-label]{margin-top:4.6cqh}
.frame .tbl.lay.lay-choices[data-titled] tbody tr td:nth-child(n){font-size:max(var(--tf,3.2cqh),3.1cqh);padding:.55cqh 2.2cqw}
.frame .tbl.lay.lay-choices[data-titled] thead{float:left;margin:1.1cqh 1.6cqw 0 0}
.frame .tbl.lay.lay-choices[data-titled] th{padding:0}
/* a note and the word card it brings side by side, so a board's letter keeps its size */
.frame #cam > .blk.plain:has(+ .blk.gl){flex:1 1 46%;max-width:50%}
.frame #cam > .blk.plain + .blk.gl{flex:1 1 44%}
.frame .gl-w{font-size:3.2cqh}
/* a word card's "Word" chip beside its word, not on a line of its own */
.frame .gl-txt::before{float:left;margin:.6cqh 1.2cqw 0 0}
.frame .tbl.lay.lay-choices td[data-label]::before{top:-4.2cqh}
.frame .tbl.lay.lay-paper[data-paper="sheet"] table{font-size:max(var(--tf,2.6cqh),4cqh)}
.frame .tbl.lay.lay-paper[data-paper="sheet"]{padding:1.8cqh 1.8cqw 2cqh}

/* --- ADR 050 amendment (2) (the site's player; the owner's addendum, 2026-11-01) --- */
/* a tilted sticky note keeps clear of the board's right edge */
.frame #cam > .callout{flex:0 0 96%;max-width:96%}
/* a sticky note the player sets beside a table (its width the player's) stands straight: tilted, it passes the edge */
.frame .callout.beside{rotate:none}
/* one face for a set of equals: a recap's cards all in print when any of them is longer than a short note */
.frame #cam:has(> .card.lay-badges.t-print) > .card.lay-badges .cardbd{font-family:var(--font-plex,"IBM Plex Sans"),system-ui,
  sans-serif;font-size:3.2cqh;line-height:1.38;font-weight:400}
/* headings and labels in coloured rounded boxes (the owner's Canva samples) */
.frame .hdr .t{background:var(--t-teal-s);color:var(--t-teal-d);border-radius:999px;padding:.7cqh 2cqw;line-height:1.25}
.frame .hdr .t:empty{background:none;padding:0}
.frame .blk.ltitle{background:var(--t-teal);color:#fff;border-radius:2.8cqh;padding:3.2cqh 3.4cqw;
  box-shadow:0 .8cqh 2.4cqh -.6cqh rgba(11,60,59,.35)}
.frame #cam:has(> .blk.ltitle) > .blk.plain.role-note:not(.t-print){background:var(--t-blue-s);border-radius:2.4cqh;
  padding:1.4cqh 2cqw}
.frame #cam:has(> .blk.ltitle) > .blk.plain.role-note.t-print{background:#fff;border-radius:2.4cqh;padding:1.6cqh 2.2cqw;
  box-shadow:inset .8cqh 0 0 var(--t-coral),0 .4cqh 1.6cqh rgba(11,60,59,.07)}
.frame #cam:has(> .blk.ltitle) > .blk.plain.role-slide{background:var(--t-teal-s);border-radius:2.4cqh;box-shadow:none}
.frame .tbl.lay.lay-paper th{display:table-cell}
.frame .tbl.lay.lay-paper th:not(:empty){background:var(--t-teal);color:#fff;border-radius:999px 999px 999px 999px;
  padding:.5cqh 1.4cqw;font-weight:700}
.frame .tbl.lay.lay-paper th:nth-child(3):not(:empty){background:var(--t-amber);color:var(--t-ink-d)}
.frame .tbl.lay.lay-paper thead tr{border-spacing:0}
.frame .tbl.lay.lay-paper tbody td:first-child{color:var(--t-teal-d)}
.frame .tbl.lay.lay-paper[data-paper="beside"] tbody td:first-child,.frame .tbl.lay.lay-paper[data-paper="sheet"] tbody td:first-child{
  background:var(--t-teal-s)}
.frame .tbl.lay.lay-wrongright th{border-radius:999px;padding:.5cqh 1.4cqw;justify-self:start;color:#fff;background:var(--t-pen)}
.frame .tbl.lay.lay-wrongright th:last-child{background:var(--t-teal);color:#fff}
.frame .tbl.lay.lay-ruled th{background:var(--t-teal-s);color:var(--t-teal-d);border-radius:999px}
.frame .tbl.lay.lay-beforeafter th{background:var(--t-coral);color:var(--t-ink-d)}
.frame .tbl.lay.lay-beforeafter th:last-child{background:var(--t-teal);color:#fff}
.frame .tbl.lay.lay-compare thead tr th:nth-child(n){margin:1.4cqh 1.4cqw .4cqh;border-radius:2cqh;background:#cfe5e3;
  padding:1.6cqh 1.6cqw}
.frame .tbl.lay.lay-compare thead tr th:last-child{background:#f7dfa8}
.frame .tbl.lay.lay-compare thead tr{background:none}
.frame .tbl.lay.lay-compare thead tr th:nth-child(n){box-shadow:0 0 0 1.4cqh var(--t-teal-s)}
.frame .tbl.lay.lay-compare thead tr th:last-child{box-shadow:0 0 0 1.4cqh var(--t-amber-s)}
/* the paper of a sheet (the paper alone, as on board 3 of Word Order) larger, to use the board */
.frame .tbl.lay.lay-paper[data-paper="sheet"] table{font-size:max(var(--tf,2.6cqh),4.5cqh)}
.frame .card.lay-badges .cardhd{width:31cqh;height:31cqh;font-size:3.4cqh;padding:2cqh;text-wrap:balance;hyphens:none}
"""}


def look_css(lesson) -> str:
    """The look's rules for a lesson whose sections.json names one (ADR 050); "" for any other."""
    look = look_of(lesson)
    return LOOK_CSS[look] if look else ""


# ---------------------------------------------------------------------------
# IBM Plex Sans for the reference player (player.html only; never in the bundle),
# and the teal look's hand, Caveat (ADR 050), the same way.
# ---------------------------------------------------------------------------
HAND_LOCK = REPO / "spike" / "fonts" / "caveat.lock.json"


def font_dir(lock_path: Path = FONT_LOCK) -> Path:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "oet-fonts"
    return base / f"{lock['package'].split('/')[-1]}-{lock['version']}"


def fetch_fonts(lock_path: Path = FONT_LOCK) -> Path:
    """Download the pinned font files into the local cache, each checked against
    the lock's SHA-256; a file that does not match is refused and removed."""
    import urllib.request
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    d = font_dir(lock_path)
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


def _faces(lock_path: Path) -> list[str]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    d = font_dir(lock_path)
    out = []
    for f in lock["files"]:
        p = d / f["name"]
        if not p.exists():
            raise SystemExit(f"REFUSED: {p} is missing: run spike/scripts/style_c.py --fetch-fonts")
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() != f["sha256"]:
            raise SystemExit(f"REFUSED: {p} does not match the lock's SHA-256")
        out.append(f"@font-face{{font-family:\"{lock['family']}\";font-style:normal;font-display:block;"
                   f"font-weight:{f['weight']};unicode-range:{lock['unicode_range'][f['subset']]};"
                   f"src:url(data:font/woff2;base64,{base64.b64encode(data).decode()}) format(\"woff2\")}}")
    return out


def font_css(look: str | None = None) -> str:
    """@font-face rules for IBM Plex Sans 400 to 700, latin and latin-ext, the
    files embedded as data: URLs (a file:// page cannot load a font beside it);
    for a lesson in the teal look, Caveat 500 and 700 too (its teacher's hand).
    Refused when a file is missing or does not match its pinned hash: run
    `style_c.py --fetch-fonts` once."""
    out = "/* IBM Plex Sans (SIL OFL 1.1), the reference player's copy (ADR 042) */\n" + "\n".join(_faces(FONT_LOCK)) + "\n"
    if look == "teal":
        out += "/* Caveat (SIL OFL 1.1), the teal look's hand, the reference player's copy (ADR 050) */\n" \
               + "\n".join(_faces(HAND_LOCK)) + "\n"
    return out


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--fetch-fonts"]:
        print(f"fonts in {fetch_fonts()} and {fetch_fonts(HAND_LOCK)}")
    else:
        raise SystemExit("usage: style_c.py --fetch-fonts")
