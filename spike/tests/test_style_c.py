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
import lesson_package as lp         # noqa: E402
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


class Layouts(unittest.TestCase):
    """The board layouts and the criteria's colours (ADR 042, amendment of
    2026-10-26): classes and attributes only, never a word added or moved."""

    def core(self, header, rows, typed=()):
        import write_screens
        b = {"id": "p_k01", "type": "table", "core": True, "header": header, "rows": rows,
             "typed": list(typed), "font": 3.2}
        return b, write_screens.block_html(b)

    def words(self, h):
        import re
        return re.sub(r"<[^>]+>", " ", h).split()

    def test_tiles_take_each_criterions_colour_and_monogram(self):
        b, h = self.core(["Criterion", "What it asks"], [["Purpose", "Why."], ["Genre and Style", "How."]])
        out = style_c.layout_html(b, h, "The six criteria", "tiles")
        self.assertIn("lay lay-tiles", out)
        self.assertIn('data-row="0" data-crit="purpose" data-mono="P"', out)
        self.assertIn('data-crit="gs" data-mono="G&amp;S" data-mono-len="3"', out)
        self.assertEqual(self.words(out), self.words(h))

    def test_scores_draw_points_as_empty_elements(self):
        b, h = self.core(["Criterion", "Scored out of", "For grade B, at least"],
                         [["Purpose", "3", "2"], ["Each of the other five criteria", "7", "5"]])
        out = style_c.layout_html(b, h, "How your letter is scored", "scores")
        self.assertEqual(out.count('<i class="on"></i>'), 7)
        self.assertEqual(out.count("<i></i>"), 3)
        self.assertEqual(out.count('<i data-crit="'), 5)          # the other five criteria
        self.assertIn('data-label="Scored out of"', out)
        self.assertEqual(self.words(out), self.words(h))

    def test_bins_place_each_answer_in_its_lane(self):
        rows = [["2011 – wrist", "Leave out"], ["2016 – hypertension", "Keep, briefly"]]
        b, h = self.core(["Case note", "In the letter"], rows,
                         [{"row": 0, "col": 1, "start": 0, "text": "Leave out"},
                          {"row": 1, "col": 1, "start": 0, "text": "Keep, briefly"}])
        out = style_c.layout_html(b, h, "Conciseness and Clarity", "bins")
        self.assertIn('data-bin="out"', out)
        self.assertIn('data-bin="brief"', out)
        self.assertIn('data-l="Keep briefly"', out)
        self.assertIn('data-typed="0"', out)
        self.assertEqual(self.words(out), self.words(h))

    def test_a_layout_for_the_wrong_block_is_refused(self):
        b, h = self.core(["A", "B"], [["x", "y"]])
        with self.assertRaises(SystemExit):
            style_c.layout_html(b, h, None, "scores")             # three columns of numbers
        with self.assertRaises(SystemExit):
            style_c.layout_html(b, h, None, "vs")                 # a comparison's
        with self.assertRaises(SystemExit):
            style_c.layout_html(b, h, None, "nothing")

    def test_the_criterion_card_and_the_section_colour(self):
        term = {"id": "p_k02", "type": "term_box", "label": "The criterion", "term": "Immediately apparent",
                "explanation": "At once.", "style": "pill"}
        import write_screens
        h = write_screens.block_html(term)
        out = style_c.layout_html(term, h, "Purpose")
        self.assertIn('crit" data-crit="purpose" data-mono="P"', out)
        note = {"id": "p_k03", "type": "plain", "text": "A note."}
        self.assertIn('data-crit="purpose"', style_c.layout_html(note, write_screens.block_html(note), "Purpose"))
        self.assertNotIn("data-crit", style_c.layout_html(note, write_screens.block_html(note), "Closing"))

    def test_right_no_longer_collides(self):
        from board_style import colour_distance, WORD_COLOURS, TENSE_COLOURS
        self.assertGreaterEqual(colour_distance(style_c.RIGHT[0], WORD_COLOURS["adjective"]), 20)
        for header, accent in TENSE_COLOURS.values():
            self.assertGreaterEqual(colour_distance(style_c.RIGHT[0], header), 20)
            self.assertGreaterEqual(colour_distance(style_c.RIGHT[0], accent), 20)
        inks = [ink for _k, _m, ink, _s in style_c.CRITERIA.values()]
        for ink in inks:
            for meaning in (style_c.RIGHT[0], style_c.WRONG[0], style_c.GLOSS[0]):
                self.assertGreaterEqual(colour_distance(ink, meaning), 19.95)

    def test_no_lilac(self):
        for lilac in ("#f3f0fb", "#c9bdf5", "rgba(91,63,196"):
            self.assertNotIn(lilac, style_c.CSS)

    def test_phase_2_forms_and_their_rules_only_where_used(self):
        # ADR 043 amendment (3): a fix of two columns, a letter of one, a pair of
        # lists; their rules in the stylesheet of a lesson that uses them only
        fix, hf = self.core(["Wrong", "Right"], [["x y", "x a y."]], [{"row": 0, "col": 1, "start": 0, "text": "x a y."}])
        letter, hl = self.core(["Dear Doctor,"], [["I am writing ____ about."], ["Yours faithfully,"]])
        pair, hp = self.core(["Countable", "Examples", "Uncountable", "Examples"], [["Tests", "MRI", "Gases", "Oxygen"]])
        out = {}
        for b, h, lay in ((fix, hf, "fix"), (letter, hl, "letter"), (pair, hp, "pair")):
            o = style_c.layout_html(b, h, "Articles", lay)
            self.assertIn("lay lay-" + lay, o)
            self.assertEqual(self.words(o), self.words(h))
            out[lay] = {**b, "html": o}
        self.assertEqual(style_c.layout_css({}), "")
        self.assertEqual(style_c.layout_css({"f": out["fix"]}), style_c.LAYOUT_CSS["fix2"])
        self.assertEqual(style_c.layout_css({"l": out["letter"], "p": out["pair"]}),
                         style_c.LAYOUT_CSS["letter1"] + style_c.LAYOUT_CSS["pair"])
        # Writing 2's forms (a fix of three columns, a letter of two) take none
        fix3, h3 = self.core(["Case note", "Wrong", "Accurate"], [["n", "w", "r"]])
        let2, h2 = self.core(["Part", "The letter"], [["Date", "21 October"]])
        self.assertEqual(style_c.layout_css({
            "a": {**fix3, "html": style_c.layout_html(fix3, h3, "Content", "fix")},
            "b": {**let2, "html": style_c.layout_html(let2, h2, None, "letter")}}), "")
        with self.assertRaises(SystemExit):           # a pair is a table of four columns
            style_c.layout_html(fix, hf, None, "pair")
        for k in style_c.LAYOUT_CSS.values():          # never in the shared stylesheet
            self.assertNotIn(k.strip(), style_c.CSS)

    def test_the_paper_a_sheet_and_beside_the_letter(self):
        # ADR 045: a sheet of a Writing paper (label, lines), and pieces of it
        # beside the letter (label, lines, letter); no word changes
        sheet, hs = self.core(["A paper", ""], [
            ["Notes:", "Assume that today's date is 1 May 2026."],
            ["HEADING: / Name: / Born:", "Mr A / 1 Jan 1950"],
            ["Writing Task:", "Write a letter."]])
        o = style_c.layout_html(sheet, hs, None, "paper")
        self.assertIn('lay lay-paper" data-paper="sheet"', o)
        self.assertIn('data-row="0" data-today=""', o)
        self.assertIn('data-row="2" data-task=""', o)
        self.assertIn('<td data-col="1" data-skip="1">', o)
        self.assertEqual(self.words(o), self.words(hs))
        beside, hb = self.core(["A paper", "", "The letter"], [
            ["Plan:", "Letter re:", ""], ["", "visit 1 May", "Please visit on 1 May."]],
            [{"row": 1, "col": 2, "start": 0, "text": "Please visit on 1 May."}])
        o2 = style_c.layout_html(beside, hb, None, "paper")
        self.assertIn('data-paper="beside"', o2)
        self.assertIn('data-row="0" data-solo=""', o2)
        self.assertNotIn('data-row="1" data-solo', o2)
        self.assertEqual(self.words(o2), self.words(hb))
        # a piece written while teaching (not the board's own table) takes it too
        import write_screens
        note = {"id": "p_k05", "type": "table", "header": ["A paper", ""], "rows": [["Plan:", "visit 1 May"]]}
        o3 = style_c.layout_html(note, write_screens.block_html(note), None, "paper")
        self.assertIn('data-paper="sheet"', o3)
        with self.assertRaises(SystemExit):           # a paper has two or three columns
            style_c.layout_html(*self.core(["One"], [["x"]]), None, "paper")
        self.assertEqual(style_c.layout_css({"s": {**sheet, "html": o}}), style_c.LAYOUT_CSS["paper"])
        self.assertNotIn(style_c.LAYOUT_CSS["paper"].strip(), style_c.CSS)

    def test_an_acronym_letter_and_name_in_their_own_spans(self):
        # ADR 049: "I: Introduce and identify" drawn as the letter large in its own
        # column and the name beside it; the colon stays in the words, at no size
        b, h = self.core(["Part", "The letter"], [["I: Introduce and identify", "I am writing."],
                                                    ["S: Situation", "Bruises appeared."]])
        o = style_c.layout_html(b, h, None, "acronym")
        self.assertIn("lay lay-acronym", o)
        self.assertIn('<td data-col="0"><span class="ac-l">I</span><span class="ac-s">: </span>'
                      '<span class="ac-n">Introduce and identify</span></td>', o)
        self.assertEqual(style_c._text(o), style_c._text(h))       # the colon stays in the words
        self.assertEqual(style_c.layout_css({"a": {**b, "html": o}}), style_c.LAYOUT_CSS["acronym"])
        with self.assertRaises(SystemExit):           # a row that does not open with its letter
            style_c.layout_html(*self.core(["Part", "The letter"], [["Introduce", "x"]]), None, "acronym")

    def test_a_skeleton_dashes_ends_and_accents(self):
        # ADR 049: two letters side by side; an empty paragraph with text below it
        # is dashed lines, the last paragraph written out is the request expanded,
        # the purpose words (block_accents) are wrapped once; no word changes
        b, h = self.core(["Mr A's letter", "Mrs B's letter"], [
            ["I am writing to ask for care.", "She returns home; please go on with her care."],
            ["", ""], ["", "Please check her leg."], ["Please advise before 6 pm.", ""]])
        o = style_c.layout_html(b, h, None, "skeleton", ["to ask for care", "go on with her care"])
        self.assertIn("lay lay-skeleton", o)
        self.assertIn('<td data-col="0" data-dash=""></td><td data-col="1" data-dash=""></td>', o)
        self.assertIn('<tr data-row="2"><td data-col="0" data-dash=""></td><td data-col="1" data-end="">', o)
        self.assertIn('<tr data-row="3"><td data-col="0" data-end="">Please advise', o)
        self.assertIn('<td data-col="1" data-after=""></td></tr></tbody>', o)   # past a letter's end: its sheet has ended
        self.assertIn('I am writing <span class="acc">to ask for care</span>.', o)
        self.assertIn('please <span class="acc">go on with her care</span>.', o)
        self.assertEqual(style_c._text(o), style_c._text(h))
        self.assertEqual(style_c.layout_css({"s": {**b, "html": o}}), style_c.LAYOUT_CSS["skeleton"])
        with self.assertRaises(SystemExit):           # a phrase not in the words
            style_c.layout_html(b, h, None, "skeleton", ["to request"])
        with self.assertRaises(SystemExit):           # a phrase found twice
            style_c.layout_html(b, h, None, "skeleton", ["care"])
        with self.assertRaises(SystemExit):           # an accent on a layout that draws none
            style_c.layout_html(*self.core(["Part", "L"], [["I: A", "x"]]), None, "acronym", ["x"])
        with self.assertRaises(SystemExit):           # a letter must open with a paragraph written out
            style_c.layout_html(*self.core(["A", "B"], [["", "x"], ["y", ""]]), None, "skeleton")


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

    def test_no_zoom_on_the_paper_beside_the_letter(self):
        # ADR 045: a zoom onto one cell would take the piece of the paper or the
        # part of the letter out of view; a sheet of the paper is still zoomed
        boards, blocks = bundle()
        blocks["doc"]["html"] = '<div class="blk tbl core lay lay-paper" data-paper="beside">'
        style_c.effects(boards, blocks)
        self.assertEqual(boards[2]["states"][0]["effects"], [])
        boards, blocks = bundle()
        blocks["doc"]["html"] = '<div class="blk tbl core lay lay-paper" data-paper="sheet">'
        style_c.effects(boards, blocks)
        self.assertEqual([e["type"] for e in boards[2]["states"][0]["effects"]], ["zoom"])

    def test_no_zoom_on_a_board_marked_no_zoom(self):
        # ADR 049: a board shown whole that the lesson marks no-zoom keeps its
        # spotlight and marks and takes no zoom; every other board as before
        boards, blocks = bundle()
        style_c.effects(boards, blocks, nozoom={"x_t3"})
        self.assertEqual(boards[2]["states"][0]["effects"], [])
        self.assertEqual(len(boards[0]["states"][0]["effects"]), 2)
        boards, blocks = bundle()
        style_c.effects(boards, blocks, nozoom={"x_t1"})
        self.assertEqual([e["type"] for e in boards[2]["states"][0]["effects"]], ["zoom"])

    def test_no_zoom_where_the_tables_are_not_documents(self):
        # ADR 043: the zoom is for a Writing lesson's letter or case notes; a
        # Grammar table keeps rule 13's auto zoom, a Reading text its own lens
        boards, blocks = bundle()
        style_c.effects(boards, blocks, zoom=False)
        self.assertEqual(boards[2]["states"][0]["effects"], [])
        self.assertEqual(len(boards[0]["states"][0]["effects"]), 2)    # the lifts stay
        self.assertTrue(style_c.zooms(lesson()))                       # a writing lesson
        other = lesson()
        info = json.loads((other / "analysis" / "sections.json").read_text(encoding="utf-8"))
        info["lesson"]["type"] = "grammar"
        (other / "analysis" / "sections.json").write_text(json.dumps(info), encoding="utf-8")
        self.assertFalse(style_c.zooms(other))

    def test_the_last_item_lifted_when_its_reveal_falls_in_the_last_sentences_tail(self):
        # ADR 043 decision 16: its first word said just before its sentence's
        # recorded start, inside the 0.5 s after the previous sentence ends
        boards, blocks = bundle()
        s = boards[0]["states"][0]
        s["utterances"] = [{"start": 0.5, "end": 3.7, "cues": [], "reading": []},
                           {"start": 4.2, "end": 6.0, "reading": [],
                            "cues": [{"type": "reveal", "block": "c2", "time": 4.0}]}]
        style_c.effects(boards, blocks)
        self.assertEqual(s["effects"][-1], {"type": "lift", "block": "c2", "time": 4.0, "until": 6.6})

    def test_the_last_category_lifted_while_its_sections_are_named(self):
        # ADR 043: a category whose sections the narration names one by one stays
        # lifted until the last is named, not only through its reveal
        boards, blocks = bundle()
        s = boards[0]["states"][0]
        s["utterances"].append({"start": 6.4, "end": 8.5, "reading": [],
                                "cues": [{"type": "underline", "block": "c2", "text": "x", "time": 7.0}]})
        style_c.effects(boards, blocks)
        self.assertEqual(s["effects"][-1], {"type": "lift", "block": "c2", "time": 4.0, "until": 9.1})


class ContentsParts(unittest.TestCase):
    ITEM = ('<div class="blk citem" data-id="k1"><span class="cnum" data-n="1"></span><div><div class="ct">'
            'Commas</div><div class="cs">Overview · Lists and series · Practice</div></div></div>')

    def test_each_section_on_its_own_line_no_word_changes(self):
        h = style_c.layout_html({"type": "contents_item", "text": "Commas"}, self.ITEM, None)
        self.assertIn('<div class="cs parts"><span class="cp">Overview</span> · <span class="cp">Lists and '
                      'series</span> · <span class="cp">Practice</span></div>', h)
        self.assertEqual(style_c._text(h), style_c._text(self.ITEM))

    def test_one_section_or_none_unchanged(self):
        for cs in ("", "Overview"):
            item = self.ITEM.replace("Overview · Lists and series · Practice", cs)
            self.assertEqual(style_c.layout_html({"type": "contents_item", "text": "Commas"}, item, None), item)


class PackageCheck(unittest.TestCase):
    """LP-STYLE, LP-EFFECTS and LP-CELLS, ported from the site's validator at contracts 1.12.0."""

    def bundle(self, version="1.22", style=True):
        b = {"format_version": version, "lesson": {"id": "writing-99-example"},
             "blocks": {"t": {"id": "t", "type": "table", "rows": [["a", "b"], ["c", "d"]]},
                        "k": {"id": "k", "type": "note"}},
             "boards": [{"id": "x_t1", "table": "t", "fixed": [], "pinned": {},
                         "focus": [{"time": 1.0, "row": None, "col": None},
                                   {"time": 2.0, "row": 0, "col": 0, "cells": [[0, 0], [1, 1]]}],
                         "states": [{"id": "x_t1.s1", "start": 1.0, "until": 9.0, "working": ["k"],
                                     "effects": [{"type": "lift", "block": "k", "time": 2.0, "until": 3.0},
                                                 {"type": "zoom", "block": "t", "row": 1, "col": None,
                                                  "text": None, "time": 4.0, "until": 9.0}]}]}]}
        if style:
            b["lesson"]["style"] = "c"
        return b

    def codes(self, b):
        f = lp.Findings()
        lp.check_style(b, f)
        return f.codes("error")

    def test_a_good_1_22_bundle(self):
        self.assertEqual(self.codes(self.bundle()), [])

    def test_style_and_effects_go_together(self):
        b = self.bundle()
        del b["boards"][0]["states"][0]["effects"]
        self.assertEqual(self.codes(b), ["LP-STYLE"])
        self.assertEqual(self.codes(self.bundle(style=False)), ["LP-STYLE"])

    def test_before_1_22_none_of_the_fields(self):
        self.assertEqual(self.codes(self.bundle("1.21")), ["LP-CELLS", "LP-EFFECTS", "LP-STYLE"])
        b = self.bundle("1.21", style=False)
        del b["boards"][0]["states"][0]["effects"]
        del b["boards"][0]["focus"][1]["cells"]
        self.assertEqual(self.codes(b), [])

    def test_effects(self):
        for change in (lambda e: e[1].update(time=1.5),            # out of order
                       lambda e: e[0].update(until=2.0),           # ends as it starts
                       lambda e: e[1].update(until=9.5),           # past the state
                       lambda e: e[0].update(block="elsewhere"),   # not a block of the board
                       lambda e: e[1].update(block="k"),           # a zoom not on the table
                       lambda e: e[1].update(row=2),               # no such row
                       lambda e: e[1].update(col=2)):              # no such column
            b = self.bundle()
            change(b["boards"][0]["states"][0]["effects"])
            self.assertEqual(self.codes(b), ["LP-EFFECTS"])

    def test_cells(self):
        for entry in ({"time": 2.0, "row": None, "col": None, "cells": [[0, 0]]},
                      {"time": 2.0, "row": 0, "col": 0, "cells": [[0, 0], [2, 0]]},
                      {"time": 2.0, "row": 0, "col": 0, "cells": [[0, 2]]}):
            b = self.bundle()
            b["boards"][0]["focus"][1] = entry
            self.assertEqual(self.codes(b), ["LP-CELLS"], entry)

    def test_text_style_only_from_1_22(self):
        b = self.bundle()
        for version, want in (("1.22", []), ("1.21", ["LP-STYLE"])):
            f = lp.Findings()
            lp.check_text({"format_version": version, "lesson": {"id": b["lesson"]["id"], "style": "c"},
                           "sections": []}, {"lesson": b["lesson"], "sections": []}, f)
            self.assertEqual(f.codes("error"), want)


if __name__ == "__main__":
    unittest.main()


class ADR048Layouts(unittest.TestCase):
    """ADR 048: the six layouts of the Word Order redesign are classes on the table and rules appended
    only to a lesson that uses them; a place reads the part's place from the letter column's label."""

    def _table(self, header, rows, core=True):
        body = "".join("<tr>" + "".join(f'<td data-col="{c}">{x}</td>' for c, x in enumerate(r)) + "</tr>" for r in rows)
        html = ('<div class="blk tbl' + (" core" if core else "") + '" data-id="x"><table><thead><tr>'
                + "".join(f"<th>{h}</th>" for h in header) + "</tr></thead><tbody>" + body + "</tbody></table></div>")
        return {"id": "x", "type": "table", "header": header, "rows": rows, "core": core, "html": html}

    def test_adr048_layouts(self):
        cases = {
            "pieces": (["Who", "What"], [["I", "visited him"]]),
            "place": (["Her paper", "", "Her letter: the request"], [["Plan:", "a line", "a sentence"]]),
            "tags": (["The sentence", "The place"], [["I would also go", "after would"]]),
            "front": (["Kind", "The phrase first", "Then the sentence"], [["Time", "On Monday,", "she came."]]),
            "sides": (["Purpose", "At the start", "At the end"], [["Date", "On Monday, she came.", "She came on Monday."]]),
            "chips": (["The bank", ""], [["a", "b"], ["c", "d"]]),
        }
        for lay, (header, rows) in cases.items():
            b = self._table(header, rows)
            out = style_c.layout_html(b, b["html"], None, lay)
            self.assertIn("lay-" + lay, out, lay)
            self.assertEqual(style_c._text(out), style_c._text(b["html"]), lay)
            css = style_c.layout_css({"x": {**b, "html": out}})
            self.assertIn(style_c.LAYOUT_CSS[lay], css, lay)
            self.assertEqual(style_c.layout_css({"x": b}), "", lay)
        b = self._table(*cases["place"])
        out = style_c.layout_html(b, b["html"], None, "place")
        self.assertIn('data-place="request"', out)
        self.assertIn("lay-paper", out)
        self.assertIn(style_c.PAPER_BESIDE, out)
        b = self._table(["Her paper", "", "Her letter"], [["Plan:", "a line", "a sentence"]])
        self.assertIn('data-place="body"', style_c.layout_html(b, b["html"], None, "place"))
        # a working table may take pieces and chips; the place needs three columns
        b = self._table(["Who", "What"], [["I", "visited him"]], core=False)
        self.assertIn("lay-pieces", style_c.layout_html(b, b["html"], None, "pieces"))
        self.assertIsNotNone(style_c.check_layout("x", self._table(["a", "b"], [["1", "2"]]), "place"))



def teal_lesson(look="teal", style="c") -> Path:
    d = lesson(style)
    p = d / "analysis" / "sections.json"
    info = json.loads(p.read_text(encoding="utf-8"))
    info["lesson"]["look"] = look
    p.write_text(json.dumps(info), encoding="utf-8")
    return d


class TealLook(unittest.TestCase):
    """ADR 050: the teal look is the lesson's stylesheet, only where sections.json names it; its eleven patterns
    are layouts whose rules are appended only to a lesson that uses them, and no word of a block changes."""

    def _table(self, header, rows, core=True):
        return ADR048Layouts._table(self, header, rows, core)

    def test_only_a_style_c_lesson_that_names_it(self):
        import write_screens
        self.assertIsNone(style_c.look_of(lesson("c")))
        self.assertEqual(style_c.look_of(teal_lesson()), "teal")
        with self.assertRaises(SystemExit):
            style_c.look_of(teal_lesson("pink"))
        with self.assertRaises(SystemExit):
            style_c.look_of(teal_lesson(style=None))
        self.assertEqual(style_c.look_css(lesson("c")), "")
        css = write_screens.frame_css(teal_lesson())
        self.assertTrue(css.endswith(style_c.CSS + style_c.LOOK_CSS["teal"]))
        self.assertIn("--t-teal:#0b6e6d", css)

    def test_the_eleven_patterns(self):
        cases = {
            "wrongright": (["As written", "Put right"], [["Also she came.", "She also came."]]),
            "coded": (["Who", "What", "When"], [["I", "saw him", "today"]]),
            "opener": (["Kind", "The phrase first", "Then the sentence"], [["Time", "On Monday,", "she came."]]),
            "timeline": (["Date", "Event", "Note"], [["8", "Admitted", "bed"], ["9", "Angiogram", "scan"]]),
            "columns": (["Kind", "At the start", "At the end"], [["Date", "On Monday, she came in at last.",
                                                                  "She came in on Monday at last."]]),
            "parts": (["Part", "The letter"], [["The opening", "I am writing to refer her."], ["The request", ""]]),
            "badges": (["Tip", "Note"], [["Be clear", "One idea at a time."]]),
            "ruled": (["Line", "The paragraph"], [["1", "She was seen."], ["2", "Also she came."]]),
            "beforeafter": (["Before", "After"], [["I am writing this letter to refer her.", "I am referring her."]]),
            "choices": (["The bank", ""], [["also", "then"], ["often", "later"]]),
            "path": (["Step", "Note"], [["Read", "Who reads it?"], ["Plan", "Choose."], ["Write", "Go."]]),
            "compare": (["Referral", "Discharge"], [["Reason", "Admission"]]),
        }
        self.assertEqual(set(cases), set(style_c.ADR050_LAYOUTS))
        for lay, (header, rows) in cases.items():
            b = self._table(header, rows)
            out = style_c.layout_html(b, b["html"], None, lay)
            self.assertIn("lay-" + lay, out, lay)
            self.assertEqual(style_c._text(out), style_c._text(b["html"]), lay)
            css = style_c.layout_css({"x": {**b, "html": out}})
            self.assertIn(style_c.LAYOUT_CSS[lay], css, lay)
            self.assertIn(style_c.LAYOUT_CSS["tset"], css, lay)
            self.assertEqual(style_c.layout_css({"x": b}), "", lay)

    def test_what_each_pattern_reads(self):
        lay = lambda header, rows, name: style_c.layout_html(*(lambda b: (b, b["html"]))(self._table(header, rows)),  # noqa: E731
                                                              None, name)
        out = lay(["Before", "After"], [["One two three four.", "One two."]], "beforeafter")
        self.assertIn('data-count="4"', out)
        self.assertIn('data-count="2"', out)
        out = lay(["Who", "What"], [["I", "saw him"]], "coded")
        self.assertIn('data-label="Who" data-c="0"', out)
        self.assertIn('data-c="1"', out)
        self.assertIn("data-titled", lay(["The bank", ""], [["a", "b"]], "choices"))
        self.assertNotIn("data-titled", lay(["Who, what", "Why"], [["a", "b"]], "choices"))
        self.assertIn('data-cw="first"', lay(["Kind", "At the start", "At the end"],
                                             [["Date", "On Monday, she came in at last.", "x"]], "columns"))
        out = lay(["Step", "Note"], [["a", "b"], ["c", "d"], ["e", "f"]], "path")
        self.assertIn('<svg class="t-curve"', out)
        self.assertIn('d="M167 220 C333 220 333 80 500 80 C667 80 667 220 833 220"', out)
        self.assertIn('data-dash=""', lay(["Part", "Letter"], [["Opening", "Dear Dr X"], ["Body", ""]], "parts"))
        self.assertIsNotNone(style_c.check_layout("x", self._table(["a", "b", "c"], [["1", "2", "3"]]), "wrongright"))

    def test_a_comparison_its_heads_and_recap_cards(self):
        html = ('<div class="blk role-example chg stacked" data-id="x"><span class="chg-cap">Two places</span>'
                '<span class="chg-from">At the start, with a comma: On examination, she was well.</span>'
                '<svg class="chg-arrow" viewBox="0 0 30 14" aria-hidden="true"><path d="M2 7 H26"/></svg>'
                '<span class="chg-to">No colon here at all</span></div>')
        b = {"id": "x", "type": "comparison", "html": html}
        out = style_c.layout_html(b, html, None, "compare")
        self.assertIn('<span class="cmp-h">At the start, with a comma:</span> <span class="cmp-b">On examination',
                      out)
        self.assertIn('<span class="chg-to">No colon here at all</span>', out)
        self.assertEqual(style_c._text(out), style_c._text(html))
        self.assertIn(style_c.LAYOUT_CSS["compare"], style_c.layout_css({"x": {**b, "html": out}}))
        card = '<div class="blk role-note card fam-none" data-id="s_k02"><div class="cardhd">A</div></div>'
        out = style_c.layout_html({"id": "s_k02", "type": "category_card"}, card, None, "badges")
        self.assertIn('lay-badges" data-c="0"', out)
        self.assertIn(style_c.LAYOUT_CSS["badges"], style_c.layout_css({"s_k02": {"html": out}}))

    def test_readable_on_a_phone(self):
        """ADR 050 amendment (1): a hand note over 15 words is set in print in the teal look only; a long letter on
        its parts flows in two columns; the comparison of two places rings its accents; no word changes."""
        long = "My advice: put a time first only at the start of a sentence. Inside a joined sentence, keep it in its place."
        html = '<div class="blk role-note callout key_rule" data-id="x"><span class="badge-c">i</span>' + long + '</div>'
        b = {"id": "x", "type": "callout", "text": long}
        self.assertIn("t-print", style_c.layout_html(b, html, None, None, None, "teal"))
        self.assertNotIn("t-print", style_c.layout_html(b, html, None))            # no look: as before
        short = {"id": "x", "type": "callout", "text": "Keep the verb and its object together."}
        self.assertNotIn("t-print", style_c.layout_html(short, html, None, None, None, "teal"))
        para = "She was seen in clinic, and she was well. " * 5
        lay = lambda header, rows, name, acc=None: style_c.layout_html(  # noqa: E731
            *(lambda b: (b, b["html"]))(self._table(header, rows)), None, name, acc)
        self.assertIn('data-flow="2"', lay(["Part", "Letter"], [["Opening", para], ["Body", para], ["End", para],
                                                               ["Close", para]], "parts"))
        self.assertNotIn('data-flow', lay(["Part", "Letter"], [["Opening", "Dear Dr X"]], "parts"))
        out = lay(["At the start", "At the end"], [["On Monday, she came.", "She came on Monday."],
                                                    ["Comes first", "Comes after"]], "compare", ["On Monday,", "on Monday"])
        self.assertIn('<span class="acc">On Monday,</span>', out)
        self.assertIn('<span class="acc">on Monday</span>', out)
        with self.assertRaises(SystemExit):
            lay(["a", "b"], [["x y", "x y"]], "compare", ["x y"])                 # found twice: refused
        self.assertIn(".frame .tbl.core table{font-size:max(var(--tf,2.6cqh),var(--t-run))}", style_c.LOOK_CSS["teal"])
