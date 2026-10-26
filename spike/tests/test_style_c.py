"""Style C (ADR 042, bundle 1.22): only a lesson that says so takes the look, the
column labels take their meaning, and the effects are written from the bundle's
own times."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_lesson_player as blp   # noqa: E402
import style_c                      # noqa: E402


def lesson(style=None) -> Path:
    d = Path(tempfile.mkdtemp(prefix="oet-style-"))
    (d / "analysis").mkdir()
    info = {"lesson": {"title": "T", "type": "writing"}, "sections": []}
    if style:
        info["lesson"]["style"] = style
    (d / "analysis" / "sections.json").write_text(json.dumps(info), encoding="utf-8")
    return d


class Style(unittest.TestCase):
    def test_only_a_lesson_that_says_so(self):
        self.assertIsNone(style_c.style_of(None))
        self.assertIsNone(style_c.style_of(lesson()))
        self.assertEqual(style_c.style_of(lesson("c")), "c")
        with self.assertRaises(SystemExit):
            style_c.style_of(lesson("d"))

    def test_stylesheet_unchanged_without_a_style(self):
        import write_screens
        self.assertEqual(write_screens.frame_css(lesson()), write_screens.FRAME_CSS)
        css = write_screens.frame_css(lesson("c"))
        self.assertTrue(css.startswith(write_screens.FRAME_CSS) and css.endswith(style_c.CSS))

    def test_versions(self):
        self.assertEqual(style_c.FORMAT_VERSION, "1.22")
        self.assertEqual(blp.format_version("writing-02-x", newer="1.22"), "1.22")
        self.assertEqual(blp.declared_format({"lesson": {"bundle_format": "1.21"}}), "1.21")
        with self.assertRaises(SystemExit):        # 1.22 comes from the style, never declared
            blp.declared_format({"lesson": {"bundle_format": "1.22"}})


class Tones(unittest.TestCase):
    TABLE = ('<table><thead><tr><th>Case note</th><th>Wrong</th><th>Accurate</th></tr></thead><tbody>'
             '<tr data-row="0"><td data-col="0">a</td><td data-col="1">b</td><td data-col="2">c</td></tr>'
             '</tbody></table>')

    def test_labels_and_their_column(self):
        h = style_c.tone_html(self.TABLE)
        self.assertIn('<th data-tone="wrong">Wrong</th>', h)
        self.assertIn('<th data-tone="right">Accurate</th>', h)
        self.assertIn('<td data-col="1" data-tone="wrong">b</td>', h)
        self.assertIn('<td data-col="2" data-tone="right">c</td>', h)
        self.assertIn('<td data-col="0">a</td>', h)

    def test_no_word_changes(self):
        import re
        words = lambda x: re.sub(r"<[^>]+>", " ", x).split()   # noqa: E731
        self.assertEqual(words(style_c.tone_html(self.TABLE)), words(self.TABLE))
        plain = '<div class="blk plain"><span>Wrong</span></div>'
        self.assertEqual(style_c.tone_html(plain), plain)


def bundle():
    blocks = {"c1": {"type": "contents_item"}, "c2": {"type": "contents_item"},
              "s1": {"type": "error_row"}, "s2": {"type": "error_row"},
              "doc": {"type": "table", "font": 1.9, "rows": [["a", "b"], ["c", "d"]], "map": None},
              "n1": {"type": "plain"}}
    contents = {"id": "x_t1", "fixed": [], "table": None, "states": [
        {"id": "x_t1.s1", "start": 0, "end": 9, "until": 10, "working": ["c1", "c2"],
         "reveal": {"c1": 1.0, "c2": 4.0},
         "utterances": [{"start": 0.5, "end": 3.5, "cues": [], "reading": []},
                        {"start": 3.8, "end": 6.0, "cues": [], "reading": []}]}]}
    pair = {"id": "x_t2", "fixed": ["s1", "s2"], "table": None, "states": [
        {"id": "x_t2.s1", "start": 10, "end": 19, "until": 20, "working": [], "reveal": {},
         "utterances": [{"start": 10, "end": 14, "cues": [],
                         "reading": [{"block": "s1", "words": [[0, 10.2, 10.5], [1, 10.5, 12.0]]}]},
                        {"start": 14.5, "end": 18, "cues": [],
                         "reading": [{"block": "s2", "words": [[0, 14.6, 15.0], [1, 15.0, 17.0]]}]}]}]}
    letter = {"id": "x_t3", "fixed": ["doc"], "table": "doc", "fit": "whole", "states": [
        {"id": "x_t3.s1", "start": 20, "end": 29, "until": 30, "working": ["n1"], "reveal": {"n1": 25.0},
         "utterances": [{"start": 20, "end": 24, "reading": [],
                         "cues": [{"type": "underline", "block": "doc", "row": 1, "col": 1, "text": "d",
                                   "time": 20.5}]}]}]}
    return [contents, pair, letter], blocks


class Effects(unittest.TestCase):
    def setUp(self):
        self.boards, self.blocks = bundle()
        style_c.effects(self.boards, self.blocks)

    def fx(self, n):
        return self.boards[n]["states"][0]["effects"]

    def test_contents_items_lifted_while_named(self):
        self.assertEqual(self.fx(0), [
            {"type": "lift", "block": "c1", "time": 1.0, "until": 4.0},
            {"type": "lift", "block": "c2", "time": 4.0, "until": 6.6}])

    def test_fixed_sentences_lifted_while_read(self):
        self.assertEqual([(e["block"], e["time"], e["until"]) for e in self.fx(1)],
                         [("s1", 10.05, 12.6), ("s2", 14.45, 17.6)])

    def test_a_small_documents_line_zoomed_until_the_note(self):
        self.assertEqual(self.fx(2), [{"type": "zoom", "block": "doc", "row": 1, "col": 1, "text": "d",
                                       "time": 20.5, "until": 24.4}])

    def test_no_zoom_on_a_document_at_body_size(self):
        boards, blocks = bundle()
        blocks["doc"]["font"] = 3.2
        boards[2].pop("fit")
        style_c.effects(boards, blocks)
        self.assertEqual(boards[2]["states"][0]["effects"], [])


if __name__ == "__main__":
    unittest.main()
