"""A table divided by its rows over a declared split (ADR 045 amendment (1)): judged at
the size a table is read at, body size, not by its count of rows; every other split
as before."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import write_screens as ws  # noqa: E402

LONG = "A long line of a paper beside the long sentence of a letter that it feeds, " * 2


def table(bid, rows):
    return {"id": bid, "type": "table", "anchor": True, "header": ["Paper", "", "Letter"],
            "rows": [[f"L{r}:", LONG, LONG + " / " + LONG] for r in range(rows)]}


def topic(tid, title, block):
    return {"id": tid, "title": title, "split": None, "from_beats": ["p5.b1"],
            "thoughts": [{"purpose": "Table: x", "blocks": [block]}]}


class TableSplit(unittest.TestCase):
    def test_a_table_split_by_its_rows_stands_when_it_cannot_be_read_whole(self):
        a, b = table("k1", 3), table("k2", 2)
        topics = [topic("t1", "Split: rows 1 to 3", a), topic("t2", "Split: rows 4 and 5", b)]
        blocks = {"k1": a, "k2": b}
        self.assertTrue(ws.table_rows_split(topics))
        self.assertEqual(ws.merge_unjustified_splits(topics, blocks, [5]), [])
        self.assertEqual(len(topics), 2)

    def test_a_small_table_split_is_merged_as_before(self):
        a, b = ({**table(k, 1), "rows": [["a", "b", "c"]]} for k in ("k1", "k2"))
        topics = [topic("t1", "Split: one", a), topic("t2", "Split: two", b)]
        merges = ws.merge_unjustified_splits(topics, {"k1": a, "k2": b}, [5])
        self.assertEqual(len(merges), 1)
        self.assertEqual(len(topics), 1)

    def test_a_split_with_other_blocks_keeps_the_old_measure(self):
        a = table("k1", 3)
        note = {"id": "k2", "type": "plain", "anchor": True, "text": "A note."}
        topics = [topic("t1", "Split: the table", a), topic("t2", "Split: the note", note)]
        self.assertFalse(ws.table_rows_split(topics))


class SplitByOverride(unittest.TestCase):
    """ADR 050 amendment (10): a narrated table board divided by its rows (overrides.json
    `split`), the kept plan divided where a state begins."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.tb = {"id": "k1", "type": "table", "header": ["A", "B"],
                   "rows": [[f"r{r}", "x"] for r in range(1, 5)],
                   "typed": [{"row": 0, "col": 1}, {"row": 3, "col": 1}]}
        self.topics = [{"id": "t1", "title": "Rows", "split": None, "from_beats": ["p1.b1"],
                        "thoughts": [{"id": f"t1.{i}", "purpose": f"Row {i}: x",
                                      "blocks": [self.tb] if i == 1 else []} for i in range(1, 5)]}]
        self.blocks = {"k1": self.tb}
        self.spec = {"topic": "t1", "at_thought": "t1.3", "rows": 2, "table": "k1", "id": "k2",
                     "titles": ["Split: rows 1 and 2", "Split: rows 3 and 4"]}

    def tearDown(self):
        self.tmp.cleanup()

    def split(self, **change):
        (self.out / "overrides.json").write_text(json.dumps({"split": [{**self.spec, **change}]}),
                                                 encoding="utf-8")
        return ws.split_topics(self.out, self.topics, self.blocks, [])

    def test_the_rows_after_the_thought_are_a_table_of_their_own(self):
        done = self.split()
        self.assertEqual(done[0]["new_topic"], "t2")
        one, two = self.topics
        self.assertEqual([h["id"] for h in one["thoughts"]], ["t1.1", "t1.2"])
        self.assertEqual([h["purpose"] for h in two["thoughts"]], ["Row 1: x", "Row 2: x"])
        new = two["thoughts"][0]["blocks"][0]
        self.assertEqual((new["id"], new["rows"], new["split_rows"]),
                         ("k2", [["r3", "x"], ["r4", "x"]], {"first": 2, "of": 4}))
        self.assertEqual((self.tb["rows"], self.tb["split_rows"]),
                         ([["r1", "x"], ["r2", "x"]], {"first": 0, "of": 4}))
        self.assertEqual((self.tb["typed"], new["typed"]), ([{"row": 0, "col": 1}], [{"row": 1, "col": 1}]))
        self.assertEqual((one["split"], two["split"]), ("rows 1 and 2", "rows 3 and 4"))
        self.assertIs(self.blocks["k2"], new)

    def test_a_split_that_would_move_a_taught_row_is_refused(self):
        for change in ({"rows": 3}, {"at_thought": "t1.1"}, {"id": "k1"},
                       {"titles": ["rows 1 and 2", "Split: rows 3 and 4"]}, {"table": "k9"}):
            with self.subTest(change=change), self.assertRaises(SystemExit):
                self.tearDown()
                self.setUp()
                self.split(**change)

    def test_the_kept_plan_is_divided_where_a_state_begins(self):
        splits = self.split()
        states = [{"id": f"t1.s{i}", "thoughts": [f"t1.{i}"], "row": i - 1} for i in range(1, 5)]
        erasures = [{"after_thought": f"t1.{i}", "before_thought": f"t1.{i + 1}"} for i in range(1, 4)]
        saved = [{"id": "t1", "states": states, "erasures": erasures, "fixed": ["k1"]}]
        planned = [{"id": "t1", "label": "rows 1 and 2", "fixed": ["k1"], "fixed_height": 0.42,
                    "table": "k1", "states": []},
                   {"id": "t2", "label": "rows 3 and 4", "fixed": ["k2"], "fixed_height": 0.42,
                    "table": "k2", "states": []}]
        ws.split_plan(saved, splits, planned)
        one, two = saved
        self.assertEqual([s["id"] for s in one["states"]], ["t1.s1", "t1.s2"])
        self.assertEqual([(s["id"], s["row"]) for s in two["states"]], [("t2.s1", 0), ("t2.s2", 1)])
        self.assertEqual(two["split_from"], {"board": "t1", "table": "k1",
                                             "states": {"t2.s1": "t1.s3", "t2.s2": "t1.s4"}})
        self.assertEqual(len(one["erasures"]) + len(two["erasures"]), 2)    # none across the split
        self.assertEqual((two["fixed"], two["table"], one["label"]), (["k2"], "k2", "rows 1 and 2"))
        self.assertEqual({s["fill"] for s in one["states"] + two["states"]}, {round(0.42 / ws.CONTENT_BAND, 3)})
        ws.split_plan(saved, splits, planned)       # a plan already divided is left as it is
        self.assertEqual(len(saved), 2)


if __name__ == "__main__":
    unittest.main()
