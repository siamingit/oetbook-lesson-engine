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
}
# The paper (ADR 045): the line every Writing paper opens its notes with (fact
# 44), set in bold on the paper, and the labels of its Writing Task box
PAPER_TODAY = "Assume that today's date is"
PAPER_TASK = ("writing task", "in your answer")
PAPER_SKIP_MAX = 4
PAPER_BESIDE = 'data-paper="beside"'
# an acronym's row opens with its letter, a colon and the part's name ("I: Introduce and identify")
ACRONYM_CELL = re.compile(r"^[A-Z]: \S")
# the layouts that draw `block_accents` (the words set in the layout's accent colour)
ACCENT_LAYOUTS = ("skeleton",)
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
    if cols and ncol not in cols:
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
    labelled = layout in ("scores",) or (layout == "cards" and len(header) >= 3)

    def cell_attrs(c: int, txt: str) -> str:
        out = ""
        if labelled and c >= 1 and c < len(header):
            out += f' data-label="{_html.escape(header[c], quote=True)}"'
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
    return _add_root(html, "lay lay-" + layout + size)


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
    return "".join(LAYOUT_CSS[k] for k in LAYOUT_CSS if k in used)


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
                accents: list[str] | None = None) -> str:
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
      (ACCENT_LAYOUTS), each wrapped in a span `acc`.

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
        else:
            html = _add_root(html, "lay-" + layout)
    if accents:
        if layout not in ACCENT_LAYOUTS:
            raise SystemExit(f"REFUSED: sections.json block_accents: {b.get('id')} has the layout {layout!r}, which "
                             f"draws no accent ({', '.join(ACCENT_LAYOUTS)})")
        html = accent_html(b, html, accents)
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
          board in `nozoom` (sections.json `boards_nozoom`, ADR 048): a board
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
