"""How a board shows what kind of content each block is, and how a change flows
(maintainer, 2026-09-25; reference docs/prototypes/p4-board-style-prototype.html).

Presentation only: block text, ids, cues and the layout's states are never
changed here, so narration and audio stay as they are. Everything is derived
from screens.json by rules, and an override may set a block's `style` or `role`.

  pill      a term box that defines a grammar term, on a board that is not a
            table board: drawn as a pill at the top of the board, and kept
            there for the rest of the board once it appears (`pin`)
  card      a comparison: a CHANGE CARD, "from -> to", each side with its word
            class when the reply gives one ("Analyse (verb)", or a label
            "A whole clause becomes one noun phrase"); the class is drawn from
            data, never as words, so "(verb)" is not text on screen
  result    a correct sentence that is slide content: the slide's result box,
            kept for the rest of the board once it appears (`pin`)
  (fold)    a slide block whose text is part of another slide block on the
            board (the clause the slide underlines) is not drawn: its text is
            marked inside the sentence it belongs to (`fold_into`)

A board with a transformation flow orders its blocks as the flow reads: the
pill, the source sentence, the change cards with the process pill beside them,
the result, then notes (`flow`). Word links (`board["wordlinks"]`) tie a
changing word in the source to its change card and to the result, coloured by
word class; the bundle builder gives each a time.
"""

import re

from extract_understanding import esc

GLOSS_LABEL = "WORD"
WORD_CLASSES = ["noun phrase", "verb phrase", "adjective", "adverb", "clause", "phrase",
                "verb", "noun"]
CLASS_KEY = {"noun phrase": "noun", "verb phrase": "verb", "phrase": "clause"}
SIDE_TAG = re.compile(r"^(\w+):\s+")
PAREN_CLASS = re.compile(r"\s*\((" + "|".join(WORD_CLASSES) + r")\)\s*$", re.I)
BECOMES = re.compile(r"\b(?:a |an |one |whole )*(" + "|".join(WORD_CLASSES) + r")\b.*?\bbecomes?\b"
                     r"(?: a| an| one)*\s+(" + "|".join(WORD_CLASSES) + r")\b", re.I)
FLOW_ORDER = {"pill": 0, "source": 1, "card": 2, "result": 4, "note": 6}

# Word-class colours (maintainer, 2026-09-25): red and green are reserved for
# wrong and correct across the course, so no word class uses them. Chosen by
# CIEDE2000 distance: 33.7 or more between any two, 28 or more from red and
# green; text contrast on white about 4.5:1 or better (L* 50 or less).
WORD_COLOURS = {"verb": "#084191", "noun": "#916308", "adjective": "#1F7A73",
                "adverb": "#1F7A73", "clause": "#CB0BAB"}
RESERVED = {"wrong": "#E24B4A", "correct": "#639922"}
# the tense family colours a board can show (docs/02-DESIGN-SYSTEM.md §5a)
TENSE_COLOURS = {"past": ("#EF9F27", "#854F0B"), "past_to_now": ("#1D9E75", "#0F6E56"),
                 "now": ("#7F77DD", "#534AB7"), "future": ("#D4537E", "#993556")}
MIN_DISTANCE = 20.0      # CIEDE2000: two colours on one board must differ this much


def _lab(h: str) -> tuple[float, float, float]:
    import math                                                    # noqa: F401
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    t = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    return 116 * t(y) - 16, 500 * (t(x) - t(y)), 200 * (t(y) - t(z))


def colour_distance(c1: str, c2: str) -> float:
    """CIEDE2000 difference between two hex colours."""
    import math
    L1, a1, b1 = _lab(c1)
    L2, a2, b2 = _lab(c2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1 = math.degrees(math.atan2(b1, a1p)) % 360
    h2 = math.degrees(math.atan2(b2, a2p)) % 360
    dL, dC, dh = L2 - L1, C2p - C1p, h2 - h1
    if C1p * C2p == 0:
        dh = 0
    elif dh > 180:
        dh -= 360
    elif dh < -180:
        dh += 360
    dH = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lb, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    hb = (h1 + h2) / 2 if abs(h1 - h2) <= 180 else (h1 + h2 + 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hb - 30)) + 0.24 * math.cos(math.radians(2 * hb))
         + 0.32 * math.cos(math.radians(3 * hb + 6)) - 0.2 * math.cos(math.radians(4 * hb - 63)))
    SL = 1 + 0.015 * (Lb - 50) ** 2 / math.sqrt(20 + (Lb - 50) ** 2)
    SC, SH = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    RT = (-2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
          * math.sin(math.radians(60 * math.exp(-((hb - 275) / 25) ** 2))))
    return math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH))


def board_colour_clashes(word_classes: set[str], families: set[str]) -> list[str]:
    """Pairs of colours on one board that are too alike: two word classes, a
    word class and a tense family shown with it, or a word class and red or
    green. Empty when the board reads clearly."""
    out = []
    keys = sorted({CLASS_KEY.get(c, c) for c in word_classes if CLASS_KEY.get(c, c) in WORD_COLOURS})
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if WORD_COLOURS[a] != WORD_COLOURS[b] and \
                    colour_distance(WORD_COLOURS[a], WORD_COLOURS[b]) < MIN_DISTANCE:
                out.append(f"word classes {a} and {b}")
        for name, c in RESERVED.items():
            if colour_distance(WORD_COLOURS[a], c) < MIN_DISTANCE:
                out.append(f"word class {a} and {name} ({c})")
        for fam in families:
            for c in TENSE_COLOURS.get(fam, ()):
                d = colour_distance(WORD_COLOURS[a], c)
                if d < MIN_DISTANCE:
                    out.append(f"word class {a} ({WORD_COLOURS[a]}) and tense colour {fam} ({c}), "
                               f"difference {d:.1f}")
    return out


def parse_side(text: str) -> tuple[str, str | None]:
    """'Analyse (verb)' -> ('Analyse', 'verb'); text without a class unchanged."""
    m = PAREN_CLASS.search(text or "")
    if m:
        return (text[:m.start()]).strip(), m.group(1).lower()
    return (text or "").strip(), None


def card_of(b: dict) -> dict:
    """A comparison as a change card: its two sides as shown, and their word
    classes from the sides or the label."""
    left, lc = parse_side(b.get("left"))
    right, rc = parse_side(b.get("right"))
    m = BECOMES.search(b.get("label") or "")
    if m and not (lc or rc):
        lc, rc = m.group(1).lower(), m.group(2).lower()
    words = max(len(left.split()), len(right.split()))
    label_shown = bool(b.get("label")) and not m and not (lc or rc)
    return {"from": left, "from_class": lc, "to": right, "to_class": rc,
            "stacked": words > 6, "label": b.get("label") if label_shown else None}


def display_runs(b: dict, base_runs) -> list[str]:
    """The block's words as the board shows them, in document order (the
    reading pointer counts these): a pill drops its label, a change card its
    word classes and the label they replace, a gloss its label."""
    style = b.get("style")
    if style == "pill":
        return [x for x in (b.get("term"), b.get("explanation")) if x]
    if style == "card":
        c = b["card"]
        return [x for x in (c["label"], c["from"], c["to"]) if x]
    if b["type"] == "term_box" and b.get("label") == GLOSS_LABEL:
        return [x for x in (b.get("term"), b.get("explanation")) if x]
    return base_runs(b)


def display_phrase(b: dict, phrase: str | None) -> str | None:
    """A cue's phrase on a change card, without the word class it no longer
    shows as text ('Analysis (noun)' -> 'Analysis')."""
    if phrase and b.get("style") == "card":
        return parse_side(phrase)[0]
    return phrase


def _stem_find(text: str, word: str) -> str | None:
    """The word, or a phrase, in `text` as `text` writes it: a phrase case
    insensitively; a single word also inflected ('Analyse' finds 'analysed')."""
    low = text.lower()
    w = word.lower().strip(" .")
    if not w:
        return None
    if " " in w:
        i = low.find(w)
        return text[i:i + len(w)] if i >= 0 else None
    stem = w[:max(4, len(w) - 2)]
    for m in re.finditer(r"[A-Za-z'’-]+", text):
        if m.group(0).lower().startswith(stem):
            return m.group(0)
    return None


def _block_texts(b: dict) -> list[str]:
    if b["type"] == "table":
        return [c for r in (b.get("rows") or []) for c in r if c]
    return [x for x in (b.get("text"),) if x]


def derive(boards: list[dict], blocks: dict, section_title: str) -> None:
    """Set each block's `style`, `card`, `pin`, `fold_into`, `flow` and `band`,
    and each board's `wordlinks`, from the laid-out boards."""
    for b in blocks.values():
        for k in ("style", "card", "pin", "fold_into", "flow", "band"):
            if k != "style" or not b.get("style_override"):
                b.pop(k, None)
    pills = []
    for bd in boards:
        table_board = bool(bd.get("table"))
        ids = list(bd["fixed"]) + [i for s in bd["states"] for i in s["working"]]
        for i in ids:
            b = blocks[i]
            if b["type"] == "term_box" and b.get("label") != GLOSS_LABEL and not table_board:
                b["style"] = "pill"
                pills.append(b)
            elif b["type"] == "comparison":
                b["style"] = "card"
                b["card"] = card_of(b)
            elif b["type"] == "answer_row" and b.get("role") == "slide" and not table_board:
                b["style"] = "result"
            if i not in bd["fixed"] and b.get("style") in ("pill", "result"):
                b["pin"] = True
        # a slide sentence's part shown again on its own is folded into it
        slides = [blocks[i] for i in bd["fixed"] if blocks[i].get("role") == "slide"
                  and blocks[i]["type"] == "plain"]
        for b in slides:
            for host in slides:
                if host is not b and (b.get("text") or "").strip(" .").lower() in \
                        (host.get("text") or "").lower():
                    b["fold_into"] = host["id"]
                    break
    process = pills[0]["term"] if pills else None
    for bd in boards:
        table_board = bool(bd.get("table"))
        on_board = [blocks[i] for i in list(bd["fixed"]) + [i for s in bd["states"] for i in s["working"]]]
        sources = [b for b in on_board if b.get("role") == "slide" and b.get("style") != "result"
                   and not b.get("fold_into")]
        results = [b for b in on_board if b.get("style") == "result"]
        links, marks = [], []
        for c in [b for b in on_board if b.get("style") == "card"]:
            card = c["card"]
            for side, pool in (("from", sources), ("to", results + (sources if table_board else []))):
                cls = card[side + "_class"]
                if not cls:
                    continue
                for host in pool:
                    hit = next((h for h in (_stem_find(t, card[side]) for t in _block_texts(host)) if h), None)
                    if hit:
                        links.append({"block": host["id"], "text": hit,
                                      "cls": CLASS_KEY.get(cls, cls), "card": c["id"], "side": side})
                        break
        for b in on_board:
            if b.get("fold_into"):
                host = blocks[b["fold_into"]]
                hit = _stem_find(host["text"], b["text"].strip(" ."))
                if hit:
                    marks.append({"block": host["id"], "text": hit, "kind": "underline"})
        bd["wordlinks"] = links
        bd["slidemarks"] = marks
        flow = not table_board and bool(links) and bool(sources)
        for b in on_board:
            if flow:
                b["flow"] = ("pill" if b.get("style") == "pill" else
                             "card" if b.get("style") == "card" else
                             "result" if b.get("style") == "result" else
                             "source" if b.get("role") == "slide" else "note")
        # the process pill leads each run of change cards in a state
        if flow and process:
            change = lambda b: b.get("style") == "card" and bool(b["card"].get("from_class"))
            for s in bd["states"]:
                prev = False
                for i in s["working"]:
                    if change(blocks[i]) and not prev:
                        blocks[i]["band"] = process
                    prev = change(blocks[i])


def card_html(b: dict, bid: str) -> str:
    c = b["card"]
    arrow = ('<svg class="chg-arrow" viewBox="0 0 30 14" aria-hidden="true">'
             '<path d="M2 7 H26 M20 2 L27 7 L20 12"/></svg>')

    def side(text, cls, which):
        m = SIDE_TAG.match(text)
        inner = (('<span class="chg-tag">' + esc(m.group(0).strip()) + "</span> "
                  + esc(text[m.end():])) if m else esc(text))
        wc = (' data-wc="' + esc(cls) + '"') if cls else ""
        key = (" wc-" + esc(CLASS_KEY.get(cls, cls))) if cls else ""
        return '<span class="chg-' + which + key + '"' + wc + ">" + inner + "</span>"

    cap = ('<span class="chg-cap">' + esc(c["label"]) + "</span>") if c["label"] else ""
    band = (' data-process="' + esc(b["band"]) + '"') if b.get("band") else ""
    return ('<div class="blk chg' + (" stacked" if c["stacked"] else "") + (" band" if b.get("band") else "")
            + '"' + bid + band + ">" + cap + side(c["from"], c["from_class"], "from") + arrow
            + side(c["to"], c["to_class"], "to") + "</div>")


def pill_html(b: dict, bid: str) -> str:
    return ('<div class="blk defpill"' + bid + '><span class="defterm">' + esc(b["term"])
            + '</span><span class="defexp">' + esc(b.get("explanation") or "") + "</span></div>")


def style_html(b: dict, bid: str) -> str | None:
    """The block drawn in its board style, or None for the ordinary drawing."""
    if b.get("style") == "card" and b.get("card"):
        return card_html(b, bid)
    if b.get("style") == "pill":
        return pill_html(b, bid)
    if b["type"] == "term_box" and b.get("label") == GLOSS_LABEL:
        # a gloss without its capitals label: "excessive (= too much)"
        return ('<div class="blk term gloss"' + bid + '><div class="t">' + esc(b["term"])
                + ' <span class="g">(= ' + esc(b["explanation"]) + ")</span></div></div>")
    return None


def classes(b: dict) -> str:
    """Extra classes on a block's element: its role, its style, its place in a flow."""
    out = []
    if b.get("role"):
        out.append("role-" + b["role"])
    if b.get("style") == "result":
        out.append("result")
    if b.get("flow"):
        out.append("flow-" + b["flow"])
    return " ".join(out)


# The board style (docs/02-DESIGN-SYSTEM.md §7c). Colours: slide boxes sky
# (source) and peach (result), as on the maintainer's slides; word classes from
# WORD_COLOURS (verb deep blue, noun amber-brown, adjective and adverb teal,
# clause and phrase magenta), each as text colour on a soft tint; the process
# pill neutral slate; notes on a pale yellow note card.
STYLE_CSS = """
.frame{--src:#EAF4FC;--src-edge:#C9E0F3;--src-ink:#0E2A45;--res:#FFF1E2;--res-edge:#F6D2A8;
  --pill:#F7A531;--pill-ink:#3B2300;--proc:#0B5277;--notebg:#FFF8DC;--noteedge:#E0AE12;
  --proc-pill:#475569;
  --wc-verb:#084191;--wc-verb-soft:rgba(8,65,145,.10);--wc-clause:#CB0BAB;--wc-clause-soft:rgba(203,11,171,.09);
  --wc-noun:#916308;--wc-noun-soft:rgba(145,99,8,.12);--wc-adjective:#1F7A73;--wc-adjective-soft:rgba(31,122,115,.11)}
.body,#cam{flex-direction:row;flex-wrap:wrap;align-content:flex-start;column-gap:2cqw}
.body>.blk,#cam>.blk{flex:0 0 100%}
/* the slide's own sentences: sky source boxes, peach result box with its tick */
.plain.role-slide{background:var(--src);border:max(1px,.2cqh) solid var(--src-edge);color:var(--src-ink);
  border-radius:3cqh;padding:2.2cqh 3cqw;font-weight:500;line-height:1.5}
.row.result{background:var(--res);border:max(1px,.2cqh) solid var(--res-edge);color:#2C2C2A;border-radius:3cqh;
  padding:2.2cqh 3cqw;font-weight:500}
.row.result .verdict{background:#639922}
.row.role-example{border-radius:1.4cqh}
/* the definition pill, at the top of its board */
.defpill{display:inline-flex;align-items:center;gap:1.6cqw;background:var(--pill);color:var(--pill-ink);
  border-radius:999px;padding:1.1cqh 2.6cqw 1.1cqh 1cqh;font-size:2.8cqh;line-height:1.35}
.defpill .defterm{background:#fff;color:var(--proc);font-weight:500;border-radius:999px;padding:.5cqh 1.8cqw;flex:none}
.body>.defpill,#cam>.defpill{flex:0 1 auto;max-width:100%}
/* change cards: from -> to, each side's word class drawn from data */
.chg{display:flex;align-items:center;gap:1.2cqw;background:#fff;border:max(1px,.2cqh) solid #DCE6EF;
  border-radius:2cqh;padding:1.3cqh 1.8cqw;font-size:2.9cqh;line-height:1.3}
.body>.chg,#cam>.chg{flex:0 1 auto}
.chg.stacked{flex-direction:column;align-items:flex-start;gap:.6cqh}
.body>.chg.stacked,#cam>.chg.stacked{flex:0 0 100%}
.chg.stacked .chg-arrow{transform:rotate(90deg);margin-left:1cqw}
.chg .chg-from{font-weight:500} .chg .chg-to{font-weight:500}
.chg [data-wc]{display:inline-flex;flex-direction:column}
.chg [data-wc]::after{content:attr(data-wc);font-size:1.9cqh;font-weight:400;color:#5A6B7E;line-height:1.2}
.chg .chg-tag{font-size:2.1cqh;font-weight:500;color:#5A6B7E}
.chg{flex-wrap:wrap}
.chg .chg-cap{flex:0 0 100%;font-size:2.2cqh;color:#5A6B7E}
.chg.stacked .chg-cap{flex:none}
.chg-arrow{width:3.6cqh;height:1.7cqh;flex:none}
.chg-arrow path{fill:none;stroke:#9AAEC2;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round}
.chg .wc-verb{color:var(--wc-verb)} .chg .wc-clause{color:var(--wc-clause)} .chg .wc-noun{color:var(--wc-noun)}
.chg .wc-adjective,.chg .wc-adverb{color:var(--wc-adjective)}
/* the process pill with its chevrons, beside the first change card of a run */
.chg.band{position:relative;margin-left:21cqw}
.chg.band::before{content:attr(data-process);position:absolute;right:calc(100% + 3.5cqw);top:50%;
  transform:translateY(-50%);background:var(--proc-pill);color:#fff;font-weight:500;font-size:2.6cqh;
  border-radius:999px;padding:.9cqh 2.4cqw;white-space:nowrap}
.chg.band::after{content:"";position:absolute;right:calc(100% + 3.5cqw);top:50%;width:14cqw;height:12cqh;
  transform:translate(0,-50%);pointer-events:none;
  background:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 44 22'%3E%3Cpath d='M6 5 L22 17 L38 5' fill='none' stroke='%230B5277' stroke-width='7' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center top/4.4cqh 2.2cqh no-repeat,
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 44 22'%3E%3Cpath d='M6 5 L22 17 L38 5' fill='none' stroke='%230B5277' stroke-width='7' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center bottom/4.4cqh 2.2cqh no-repeat}
/* notes: a pale yellow note card, shown then erased */
.plain.role-note{background:var(--notebg);border-left:max(3px,.6cqh) solid var(--noteedge);border-radius:1.4cqh;
  padding:1.4cqh 2.4cqw}
.term.role-note{border-radius:0 1.4cqh 1.4cqh 0}
.term.gloss{background:var(--notebg);border-left-color:var(--noteedge);color:#2C2C2A}
/* word marks: a changing word takes its word-class colour, and the slide's
   own underline stays inside its sentence */
.wm{border-radius:.3cqh;transition:background-color .5s,color .5s}
.wm.wc-verb{color:var(--wc-verb);background:var(--wc-verb-soft)}
.wm.wc-clause{color:var(--wc-clause);background:var(--wc-clause-soft)}
.wm.wc-noun{color:var(--wc-noun);background:var(--wc-noun-soft)}
.wm.wc-adjective,.wm.wc-adverb{color:var(--wc-adjective);background:var(--wc-adjective-soft)}
.wm.slide-underline{text-decoration:underline;text-decoration-thickness:max(2px,.3cqh);text-underline-offset:.22em;
  padding:0;background:none}
/* a slide's table: its header in the source colour, rounded like the slide boxes */
.tbl.core th{text-transform:none;letter-spacing:normal;font-size:inherit}
.tbl.core.role-slide{border:max(1px,.2cqh) solid var(--src-edge);border-radius:2cqh;overflow:hidden}
.tbl.core.role-slide table{border-style:hidden}
.tbl.core.role-slide th{background:var(--src);color:var(--src-ink);border-color:var(--src-edge)}
/* labels in sentence case, never in capitals */
.lbl{text-transform:none;letter-spacing:.01em}
/* a flow reads top to bottom: pill, source, change cards, result, notes */
.flow-pill{order:0} .flow-source{order:1} .flow-card{order:2} .flow-result{order:4} .flow-note{order:6}
@media (prefers-reduced-motion: reduce){.wm{transition:none}}
"""
