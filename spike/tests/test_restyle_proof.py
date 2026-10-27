"""restyle_proof.py (ADR 043): a restyle may change the look, the effects, the
format and the fit, and nothing else; every other change is caught."""

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import restyle_proof as rp   # noqa: E402

ITEM = ('<div class="blk citem" data-id="k1"><span class="cnum" data-n="1"></span><div><div class="ct">'
        'Commas</div><div class="cs">Overview · Practice</div></div></div>')
TABLE = ('<div class="blk tbl core" data-id="k2" style="--tf:2cqh"><table><thead><tr><th>Note</th>'
         '<th>Wrong</th></tr></thead><tbody><tr data-row="0"><td data-col="0">a</td><td data-col="1">b</td>'
         '</tr></tbody></table></div>')
UTT = {"id": "u1", "text": "First, commas.", "audio_file": "../p/audio/x.wav", "start": 1.0, "end": 3.0,
       "cues": [{"type": "underline", "block": "k1", "text": "Overview", "time": 1.5}]}


def bundle(fmt="1.21"):
    return {"format": "oetbook-lesson-bundle", "format_version": fmt,
            "lesson": {"id": "x", "title": "T"}, "sections": [{"id": "page-3", "title": "Introduction"}],
            "blocks": {"k1": {"id": "k1", "type": "contents_item", "text": "Commas", "html": ITEM},
                       "k2": {"id": "k2", "type": "table", "font": 2.0, "html": TABLE}},
            "boards": [{"id": "t2", "start": 0.0, "until": 9.0, "tight": 0, "states": [
                {"id": "t2.s1", "start": 0.0, "until": 9.0, "working": ["k1", "k2"], "reveal": {"k1": 0.5},
                 "clears": [], "utterances": [copy.deepcopy(UTT)]}]}]}


def write(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, (bytes, bytearray)):
        p.write_bytes(data)
    else:
        p.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


def make_lesson(root: Path) -> Path:
    L = root / "grammar-99-x"
    write(L / "analysis/sections.json", {"lesson": {"title": "T", "type": "grammar"}, "sections": []})
    write(L / "analysis/decisions.md", "# Decisions\n\n## 2026-10-01 First\n- What: x\n")
    write(L / "analysis/screens/page-3/screens.json",
          {"lesson_title": {"title": "T", "type": "grammar"}, "section": {"intro": True}, "boards": []})
    write(L / "analysis/narration/page-3/narration.json", {"utterances": [UTT]})
    write(L / "analysis/fit.json", {"clears": {}})
    for d in ("generated/lesson-player", "generated/lesson-preview/silent"):
        b = bundle()
        write(L / d / "bundle.json", b)
        write(L / d / "text.json", {"format_version": "1.21", "sections": [{"id": "page-3", "text": "Commas"}]})
        write(L / d / "timeline.json", {"boards": b["boards"]})
        write(L / d / "audio_index.json", {"u1": {"start": 1.0, "end": 3.0}})
        write(L / d / "blocks.css", ".blk{}")
        write(L / d / "player.html", "<html></html>")
    write(L / "generated/p/audio/x.wav", b"RIFF-audio")
    write(L / "source/slides.pdf", b"%PDF")
    return L


def restyle(L: Path) -> None:
    """What the restyle may do (ADR 043)."""
    s = json.loads((L / "analysis/sections.json").read_text(encoding="utf-8"))
    s["lesson"].update(style="c", style_by="agent")
    write(L / "analysis/sections.json", s)
    sc = json.loads((L / "analysis/screens/page-3/screens.json").read_text(encoding="utf-8"))
    sc["lesson_title"].update(style="c", style_by="agent")
    write(L / "analysis/screens/page-3/screens.json", sc)
    write(L / "analysis/fit.json", {"clears": {"t2.s1": []}, "fonts": {"k2": 2.4}})
    with open(L / "analysis/decisions.md", "a", encoding="utf-8") as f:
        f.write("\n## 2026-10-27 Restyled\n- What: style C\n")
    for d in ("generated/lesson-player", "generated/lesson-preview/silent"):
        b = json.loads((L / d / "bundle.json").read_text(encoding="utf-8"))
        b["format_version"] = "1.22"
        b["lesson"]["style"] = "c"
        b["blocks"]["k1"]["html"] = ITEM.replace(
            '<div class="cs">Overview · Practice</div>',
            '<div class="cs parts"><span class="cp">Overview</span> · <span class="cp">Practice</span></div>')
        b["blocks"]["k2"]["html"] = TABLE.replace("--tf:2cqh", "--tf:2.4cqh").replace(
            "<th>Wrong</th>", '<th data-tone="wrong">Wrong</th>').replace(
            '<td data-col="1">', '<td data-col="1" data-tone="wrong">')
        b["blocks"]["k2"]["font"] = 2.4
        st = b["boards"][0]["states"][0]
        st["effects"] = [{"type": "lift", "block": "k1", "time": 0.5, "until": 3.6}]
        st["clears"] = [{"time": 2.0, "blocks": ["k2"]}]
        b["boards"][0]["tight"] = 1
        b["boards"][0]["split"] = 52            # a question board's columns, from the fit
        st["overlay"] = ["k2"]
        write(L / d / "bundle.json", b)
        t = json.loads((L / d / "text.json").read_text(encoding="utf-8"))
        t["format_version"] = "1.22"
        write(L / d / "text.json", t)
        write(L / d / "timeline.json", {"boards": b["boards"]})
        write(L / d / "blocks.css", ".blk{} .frame{background:#fff}")
        write(L / d / "player.html", "<html>style c</html>")
        write(L / d / "overflow_check.json", {"ok": True})


class Proof(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="oet-proof-"))
        self.L = make_lesson(self.root)
        self.snap = self.root / "before"
        rp.snapshot(self.L, self.snap)
        restyle(self.L)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def result(self):
        return rp.compare(self.snap, self.L)

    def test_a_restyle_passes(self):
        r = self.result()
        self.assertTrue(r["ok"], r["failures"])
        self.assertIn("generated/lesson-player: effect lift", r["allowed"])
        self.assertIn("generated/lesson-player format_version 1.21 -> 1.22", r["allowed"])

    def edit_bundle(self, fn):
        p = self.L / "generated/lesson-player/bundle.json"
        b = json.loads(p.read_text(encoding="utf-8"))
        fn(b)
        write(p, b)

    def assertCaught(self, why):
        r = self.result()
        self.assertFalse(r["ok"])
        self.assertTrue(any(why in f for f in r["failures"]), r["failures"])

    def test_narration_text_caught(self):
        self.edit_bundle(lambda b: b["boards"][0]["states"][0]["utterances"][0].update(text="Second, commas."))
        self.assertCaught("state t2.s1: state field 'utterances' changed")

    def test_a_cue_time_caught(self):
        self.edit_bundle(lambda b: b["boards"][0]["states"][0]["utterances"][0]["cues"][0].update(time=1.6))
        self.assertCaught("'utterances' changed")

    def test_board_timing_caught(self):
        self.edit_bundle(lambda b: b["boards"][0]["states"][0].update(until=9.5))
        self.assertCaught("'until' changed")

    def test_words_on_a_board_caught(self):
        self.edit_bundle(lambda b: b["blocks"]["k1"].update(html=b["blocks"]["k1"]["html"].replace(
            "Practice", "Exercises")))
        self.assertCaught("block k1: its words changed")

    def test_html_beyond_style_c_caught(self):
        self.edit_bundle(lambda b: b["blocks"]["k1"].update(html=b["blocks"]["k1"]["html"].replace(
            'class="ct"', 'class="ct big"')))
        self.assertCaught("block k1: its html changed beyond what style C adds")

    def test_a_block_id_caught(self):
        self.edit_bundle(lambda b: b.update(blocks={("k9" if k == "k2" else k): v for k, v in b["blocks"].items()}))
        self.assertCaught("block ids or their order changed")

    def test_audio_caught(self):
        write(self.L / "generated/p/audio/x.wav", b"RIFF-other")
        self.assertCaught("file changed: generated/p/audio/x.wav")

    def test_narration_file_caught(self):
        write(self.L / "analysis/narration/page-3/narration.json", {"utterances": []})
        self.assertCaught("narration/page-3/narration.json")

    def test_source_caught(self):
        write(self.L / "source/slides.pdf", b"%PDF-2")
        self.assertCaught("file changed: source/slides.pdf")

    def test_an_earlier_decision_caught(self):
        p = self.L / "analysis/decisions.md"
        p.write_text(p.read_text(encoding="utf-8").replace("- What: x", "- What: y"), encoding="utf-8")
        self.assertCaught("an earlier entry changed")

    def test_a_section_config_change_caught(self):
        s = json.loads((self.L / "analysis/sections.json").read_text(encoding="utf-8"))
        s["sections"] = [{"title": "New"}]
        write(self.L / "analysis/sections.json", s)
        self.assertCaught("changed beyond lesson.style")

    def test_timeline_caught(self):
        p = self.L / "generated/lesson-player/timeline.json"
        t = json.loads(p.read_text(encoding="utf-8"))
        t["boards"][0]["start"] = 0.2
        write(p, t)
        self.assertCaught("timeline.json: changed beyond the effects and the fit")

    def test_audio_index_caught(self):
        write(self.L / "generated/lesson-player/audio_index.json", {"u1": {"start": 1.1, "end": 3.0}})
        self.assertCaught("audio_index.json")

    def test_no_effects_caught(self):
        self.edit_bundle(lambda b: b["boards"][0]["states"][0].pop("effects"))
        self.assertCaught("no effects in a style C bundle")

    def test_a_stale_silent_preview_compared_with_its_re_render(self):
        # the lesson's silent preview older than its narration: the restyled one
        # is compared with the re-render by the code before the change
        rendered = self.root / "rendered" / self.L.name
        b = bundle()
        b["boards"][0]["states"][0]["utterances"][0]["text"] = "First, commas!"
        for name, data in (("bundle.json", b), ("text.json", json.loads(
                (self.snap / "files/generated/lesson-preview/silent/text.json").read_text(encoding="utf-8"))),
                ("timeline.json", {"boards": b["boards"]}), ("audio_index.json", {"u1": {"start": 1.0, "end": 3.0}})):
            write(rendered / "files/generated/lesson-preview/silent" / name, data)
        p = self.L / "generated/lesson-preview/silent/bundle.json"
        nb = json.loads(p.read_text(encoding="utf-8"))
        nb["boards"][0]["states"][0]["utterances"][0]["text"] = "First, commas!"
        write(p, nb)
        write(self.L / "generated/lesson-preview/silent/timeline.json", {"boards": nb["boards"]})
        self.assertFalse(rp.compare(self.snap, self.L)["ok"])
        r = rp.compare(self.snap, self.L, rendered)
        self.assertTrue(r["ok"], r["failures"])


if __name__ == "__main__":
    unittest.main()
