"""Question numbers and authored-section placement (ADR 026 and ADR 018
amendments of 2026-10-08)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_sections                      # noqa: E402
import question_numbers as qn              # noqa: E402


class SpokenNumbers(unittest.TestCase):
    def test_words_digits_and_ranges(self):
        said = [n for n, _ in qn.spoken_numbers(
            "Question eight first. Then questions one to three, and question twenty-two; question 5.")]
        self.assertEqual(said, [8, 1, 3, 22, 5])

    def test_other_numbers_are_not_questions(self):
        self.assertEqual(qn.spoken_numbers("Row seven, and nine tablets a day."), [])

    def test_board_check(self):
        blocks = {"q": {"question": {"item": "x"}, "exercise_item": 3},
                  "n": {"type": "plain"}}
        board = {"fixed": [], "states": [{"working": ["q", "n"], "utterances": [
            {"id": "u1", "text": "Question three."}, {"id": "u2", "text": "Like question two."}]}]}
        found = qn.board_findings(board, blocks, [1, 2, 3])
        self.assertEqual([f["where"] for f in found], ["u2"])
        bare = {"fixed": [], "states": [{"working": ["n"], "utterances": [
            {"id": "u3", "text": "Before question nine, the words."}]}]}
        self.assertEqual([f["where"] for f in qn.board_findings(bare, blocks, [1, 2, 3])], ["u3"])


class Placement(unittest.TestCase):
    def test_review_before_practice_closing_last(self):
        deck = [{"pages": [13, 14, 15], "title": "Practice"}]
        added = [{"page": 101, "title": "Review", "kind": "review", "before": 13},
                 {"page": 102, "title": "Closing", "kind": "closing"}]
        out = build_sections.place_sections(deck, added)
        self.assertEqual([s["pages"] for s in out], [[101], [13, 14, 15], [102]])
        self.assertEqual(out[0]["kind"], "review")

    def test_without_placement_after_the_deck(self):
        deck = [{"pages": [5], "title": "B"}, {"pages": [4], "title": "A"}]
        out = build_sections.place_sections(deck, [{"page": 101, "title": "Extra"}])
        self.assertEqual([s["pages"] for s in out], [[4], [5], [101]])


if __name__ == "__main__":
    unittest.main()
