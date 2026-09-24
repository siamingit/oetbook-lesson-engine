"""One preview page for the whole lesson: the title and contents boards, then
every built section's boards in lesson order under its category and section
title, each board in every state of its working layer.

    .venv/Scripts/python spike/scripts/build_lesson_preview.py <lesson_dir>

Reads:  <lesson_dir>/analysis/sections.json
        <lesson_dir>/analysis/screens/lesson-boards.json
        <lesson_dir>/analysis/screens/<page or pages folder>/screens.json
Writes: <lesson_dir>/analysis/screens/lesson-preview/index.html

Static, no audio. A section that is not built yet is listed with a note, so
the page always shows the whole lesson's structure. The frame CSS and block
renderer are write_screens's, so a board here is drawn exactly as the player
draws it.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths                                                          # noqa: E402
from extract_understanding import esc                                 # noqa: E402
from write_screens import FRAME_CSS, PAGE_CSS, block_html, is_exercise_board   # noqa: E402


def frame(title: str, inner: str) -> str:
    return ('<div class="frame"><div class="hdr">' + esc(title) + '</div><div class="body">'
            + inner + '</div><div class="ctl"><span>▶</span><span class="bar"></span>'
              "<span>0:00</span></div></div>")


def title_board_html(tb: dict) -> str:
    desc = (esc(tb["description"]) if tb.get("description")
            else '<span style="color:#888780">' + esc(tb["description_note"]) + "</span>")
    inner = ('<div style="margin-top:14cqh;font-size:6cqh;font-weight:500;line-height:1.2">'
             + esc(tb["title"]) + '</div><div style="margin-top:3cqh;font-size:3.2cqh">' + desc + "</div>")
    return frame("", inner)


def contents_board_html(cb: dict) -> str:
    items = ""
    for n, c in enumerate(cb["categories"], 1):
        items += ('<div class="blk plain" style="display:block"><span class="num" style="display:inline-flex;'
                  'align-items:center;justify-content:center;width:3.6cqh;height:3.6cqh;border-radius:50%;'
                  'background:#5F5E5A;color:#fff;font-size:2.2cqh;margin-right:1.5cqw">' + str(n)
                  + "</span>" + esc(c["title"] or "") + '<div style="font-size:2.4cqh;color:#888780;'
                  'margin-left:5cqw;margin-top:.4cqh">' + esc(" · ".join(c["sections"])) + "</div></div>")
    return frame(cb["heading"], items)


def state_frames(d: dict) -> str:
    blocks = {b["id"]: b for t in d["topics"] for h in t["thoughts"] for b in h["blocks"]}
    out = ""
    for bd in d["boards"]:
        for n, s in enumerate(bd["states"], 1):
            inner = ("".join(block_html(blocks[i]) for i in bd["fixed"])
                     + "".join(block_html(blocks[i]) for i in s["working"]))
            note = (f"{bd['id']} · {esc(bd.get('label') or '')} · state {n} of {len(bd['states'])}"
                    f" · fill {s['fill']:.0%}")
            out += ('<section class="scr">' + frame(bd["title"], inner)
                    + '<div class="side"><h3>' + note + "</h3></div></section>")
    return out


def main() -> None:
    lesson = Path(sys.argv[1])
    sec = json.loads((lesson / "analysis" / "sections.json").read_text(encoding="utf-8"))
    lb_path = lesson / "analysis" / "screens" / "lesson-boards.json"
    lb = json.loads(lb_path.read_text(encoding="utf-8")) if lb_path.exists() else None
    cats = sec.get("categories") or [{"title": None, "sections": [s["title"] for s in sec["sections"]]}]
    by_title = {s["title"]: s for s in sec["sections"]}

    body = ""
    built = missing = 0
    if lb:
        body += "<h2>Title board</h2>" + '<section class="scr">' + title_board_html(lb["title"]) + "</section>"
        body += "<h2>Contents board</h2>" + '<section class="scr">' + contents_board_html(lb["contents"]) + "</section>"
    for c in cats:
        body += "<h2 style='margin-top:48px'>" + esc(c["title"] or "Sections") + "</h2>"
        for st in c["sections"]:
            s = by_title[st]
            sp = paths.screens_dir_for(lesson, s["pages"]) / "screens.json"
            body += ("<h3 style='font-size:16px;margin:26px 0 8px'>" + esc(st)
                     + " <span class=meta>slides " + ", ".join(str(p) for p in s["pages"]) + "</span></h3>")
            if not sp.exists():
                body += '<p class="meta"><i>not built yet</i></p>'
                missing += 1
                continue
            d = json.loads(sp.read_text(encoding="utf-8"))
            fails = sum(1 for f in d["audit"] if f["severity"] == "fail")
            body += ('<p class="meta">' + str(len(d["boards"])) + " boards, "
                     + str(sum(len(b["erasures"]) for b in d["boards"])) + " erase points, audit "
                     + (f"{fails} failures" if fails else "clean") + "</p>")
            body += state_frames(d)
            built += 1

    html = ('<!doctype html><meta charset="utf-8"><title>Lesson preview</title><style>' + PAGE_CSS
            + FRAME_CSS + ":root{--w:812px} .scr{margin:18px 0}</style>"
            + "<h1>" + esc(sec["lesson"]["title"] or "Lesson") + " &mdash; every board</h1>"
            + '<div class="meta">' + str(built) + " sections built, " + str(missing)
            + " not yet. Static preview, no audio; every board in every state of its working layer, "
              "in lesson order under its category and section.</div>"
            + '<div class="tog">Frame width: <button class="on" onclick="w(this,812)">phone landscape 812</button>'
              '<button onclick="w(this,1120)">laptop 1120</button></div>'
            + body
            + "<script>function w(b,px){document.documentElement.style.setProperty('--w',px+'px');"
              "for(const x of document.querySelectorAll('.tog button'))x.classList.remove('on');b.classList.add('on')}</script>")
    out = lesson / "analysis" / "screens" / "lesson-preview" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"{built} sections built, {missing} not yet")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
