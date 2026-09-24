"""One narration review page for the whole lesson: every narrated section in
lesson order under its category, each board state drawn as the player draws
it with its utterances, cues and audit findings beside it, and the QA
findings of each pass under the section.

    .venv/Scripts/python spike/scripts/build_narration_review.py <lesson_dir>

Reads:  <lesson_dir>/analysis/sections.json
        <lesson_dir>/analysis/screens/<section folder>/screens.json
        <lesson_dir>/analysis/narration/<section folder>/narration.json, qa/qa_pass<N>.json
Writes: <lesson_dir>/analysis/narration/lesson-review/index.html

Static, no audio. A section without narration is listed with a note, so the
page always shows the whole lesson. The frame CSS, block renderer and state
renderer are the pipeline's own, so nothing here is drawn twice.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths                                                          # noqa: E402
from extract_understanding import esc                                 # noqa: E402
from write_narration import NARR_CSS, SPEAKING_WPM, spoken, state_html  # noqa: E402
from write_screens import FRAME_CSS, PAGE_CSS                         # noqa: E402


def qa_html(out_dir: Path) -> str:
    html = ""
    for n in (1, 2):
        qp = out_dir / "qa" / f"qa_pass{n}.json"
        if not qp.exists():
            html += f'<p class="meta">QA pass {n}: not run</p>'
            continue
        q = json.loads(qp.read_text(encoding="utf-8"))
        fs = sorted(q["findings"], key=lambda f: ["critical", "major", "minor"].index(f["severity"]))
        html += ('<div class="find"><b>QA pass ' + str(n) + ":</b> " + str(len(fs)) + " findings, $"
                 + format(q["meta"]["cost_usd"], ".2f") + "<ul>"
                 + "".join('<li class="' + ("fail" if f["severity"] != "minor" else "warn")
                           + '"><code>' + esc(f["utterance_id"]) + "</code> <b>" + esc(f["severity"])
                           + "</b> " + esc(f["check"]) + ": " + esc(f["issue"])
                           + ' <i style="color:#6b6a64">fix: ' + esc(f["proposed_fix"]) + "</i></li>"
                           for f in fs)
                 + "</ul></div>")
    return html


def main() -> None:
    lesson = Path(sys.argv[1])
    sec = json.loads((lesson / "analysis" / "sections.json").read_text(encoding="utf-8"))
    cats = sec.get("categories") or [{"title": None, "sections": [s["title"] for s in sec["sections"]]}]
    by_title = {s["title"]: s for s in sec["sections"]}

    body = ""
    built = missing = 0
    tot_utt = tot_words = 0
    tot_cost = 0.0
    for c in cats:
        body += "<h2 style='margin-top:48px'>" + esc(c["title"] or "Sections") + "</h2>"
        for st in c["sections"]:
            s = by_title[st]
            out_dir = paths.narration_dir_for(lesson, s["pages"])
            np_ = out_dir / "narration.json"
            sp = paths.screens_dir_for(lesson, s["pages"]) / "screens.json"
            body += ("<h3 style='font-size:16px;margin:26px 0 8px'>" + esc(st)
                     + " <span class=meta>slides " + ", ".join(str(p) for p in s["pages"]) + "</span></h3>")
            if not np_.exists() or not sp.exists():
                body += '<p class="meta"><i>not narrated yet</i></p>'
                missing += 1
                continue
            d = json.loads(np_.read_text(encoding="utf-8"))
            scr = json.loads(sp.read_text(encoding="utf-8"))
            blocks = {b["id"]: b for t in scr["topics"] for h in t["thoughts"] for b in h["blocks"]}
            raw = json.loads((out_dir / "raw_response.json").read_text(encoding="utf-8"))
            usage = raw.get("usage") or {}
            cost = __import__("llm").raw_cost(raw)
            cost += sum(x.get("cost", 0) for x in (d.get("inputs") or {}).get("splices", []))
            utts = [u for bd in d["boards"] for st_ in bd["states"] for u in st_["utterances"]]
            words = sum(len(spoken(u["text_with_cues"]).split()) for u in utts)
            fails = [f for f in d["audit"] if f["severity"] == "fail"]
            warns = [f for f in d["audit"] if f["severity"] == "warn"]
            body += ('<p class="meta">' + str(len(d["boards"])) + " boards, " + str(len(utts))
                     + " utterances, " + str(words) + " words (about "
                     + format(words / SPEAKING_WPM, ".1f") + " min), audit "
                     + (f"{len(fails)} failures, " if fails else "clean, ") + str(len(warns))
                     + " warnings, $" + format(cost, ".2f") + "</p>")
            body += qa_html(out_dir)
            topic_no = {bd["id"]: n for n, bd in enumerate(d["boards"], 1)}
            for bd in d["boards"]:
                body += "<h4 style='margin:22px 0 6px'>Board " + str(topic_no[bd["id"]]) + "</h4>"
                for n, st_ in enumerate(bd["states"], 1):
                    body += state_html(bd, st_, n, blocks, topic_no[bd["id"]], d["audit"])
            built += 1
            tot_utt += len(utts)
            tot_words += words
            tot_cost += cost

    html = ('<!doctype html><meta charset="utf-8"><title>Narration review</title><style>' + PAGE_CSS
            + FRAME_CSS + NARR_CSS + ":root{--w:812px} .scr{margin:18px 0}</style>"
            + "<h1>" + esc(sec["lesson"]["title"] or "Lesson") + " &mdash; narration review</h1>"
            + '<div class="meta">' + str(built) + " sections narrated, " + str(missing) + " not yet; "
            + str(tot_utt) + " utterances, " + str(tot_words) + " words (about "
            + format(tot_words / SPEAKING_WPM, ".0f") + " min of speech), $" + format(tot_cost, ".2f")
            + " of narration calls. Static review, no audio: each board state is shown complete; in the "
              "lesson its working notes and diagram parts appear at their reveal cues.</div>"
            + '<div class="tog">Frame width: <button class="on" onclick="w(this,812)">phone landscape 812</button>'
              '<button onclick="w(this,1120)">laptop 1120</button></div>'
            + body
            + "<script>function w(b,px){document.documentElement.style.setProperty('--w',px+'px');"
              "for(const x of document.querySelectorAll('.tog button'))x.classList.remove('on');b.classList.add('on')}</script>")
    out = lesson / "analysis" / "narration" / "lesson-review" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"{built} sections narrated, {missing} not yet")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
