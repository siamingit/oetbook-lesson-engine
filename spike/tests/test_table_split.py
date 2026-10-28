"""A table divided by its rows over a declared split (ADR 045 amendment (1)): judged at
the size a table is read at, body size, not by its count of rows; every other split
as before."""

import sys
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


if __name__ == "__main__":
    unittest.main()
