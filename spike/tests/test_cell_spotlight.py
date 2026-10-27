"""The spotlight by cell (ADR 043 decision 17, rule 11, bundle 1.22): on a table
whose rows do not pair their cells (a word and its meaning, shuffled), the word's
cell and the meaning its arrow reaches are lit, never the meaning beside the word
(the owner's report, 2026-10-27; invented words)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_lesson_player as blp   # noqa: E402
import style_c                      # noqa: E402

TABLE = {"id": "k01", "header": ["Word", "Meaning"],
         "rows": [["promptly (adverb)", "Kept apart from other patients."],
                  ["isolated (adjective)", "Quickly and without delay."]]}


def board(to_row=1):
    arrow = {"type": "arrow", "block": "k01", "text": "promptly (adverb)", "to_block": "k01",
             "to_text": "x", "time": 5.0, "row": 0, "col": 0, "to_row": to_row, "to_col": 1}
    return {"id": "t1", "table": "k01", "states": [
        {"id": "t1.s1", "start": 0.0, "until": 2.0, "utterances": []},
        {"id": "t1.s2", "start": 2.0, "until": 9.0, "row": 0,
         "utterances": [{"start": 2.2, "end": 8.0, "cues": [arrow]}]}],
        "focus": [{"time": 0.0, "row": None, "col": None}, {"time": 2.0, "row": 0, "col": None},
                  {"time": 5.0, "row": 0, "col": 0}, {"time": 7.0, "row": to_row, "col": 1},
                  {"time": 9.0, "row": None, "col": None}]}


class CellSpotlight(unittest.TestCase):
    def test_the_word_and_the_meaning_its_arrow_reaches_are_lit(self):
        f = blp.cell_focus(board(), TABLE)
        self.assertEqual(f, [
            {"time": 0.0, "row": None, "col": None},
            {"time": 2.0, "row": 0, "col": None, "cells": [[0, 0]]},            # the word, before its arrow
            {"time": 5.0, "row": 0, "col": 0, "cells": [[0, 0], [1, 1]]},       # the arrow drawn: its meaning lit
            {"time": 7.0, "row": 1, "col": 1, "cells": [[0, 0], [1, 1]]},       # the meaning read
            {"time": 9.0, "row": None, "col": None}])
        # the meaning beside the word is never lit
        self.assertFalse(any([0, 1] in e.get("cells", []) for e in f))

    def test_a_table_whose_rows_pair_keeps_its_row_spotlight(self):
        b = board(to_row=0)                 # the arrow stays in its row
        self.assertEqual(blp.cell_focus(b, TABLE), b["focus"])

    def test_the_stylesheet_dims_every_cell_but_those_lit(self):
        self.assertIn(".tbl.core.spot.cellspot tbody tr td{opacity:.5}", style_c.CELL_CSS)
        self.assertIn("td.lit{opacity:1", style_c.CELL_CSS)
        self.assertNotIn("cellspot", style_c.CSS)       # only in a lesson that has such a table

    def test_the_player_sets_lit_cells_and_no_row(self):
        tpl = (Path(__file__).resolve().parents[1] / "scripts" / "board_player_template.html").read_text(
            encoding="utf-8")
        self.assertIn('el.classList.toggle("cellspot", !!cells)', tpl)
        self.assertIn('td.classList.toggle("lit"', tpl)
        self.assertIn('tr.classList.toggle("focus", !cells &&', tpl)


if __name__ == "__main__":
    unittest.main()
