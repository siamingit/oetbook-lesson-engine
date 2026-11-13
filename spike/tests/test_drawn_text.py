"""ADR 056: every word a board shows is drawn in playback, and every gloss card shows its whole meaning and
its example. A write-in never holds its last clip (the engine's player, and the stylesheet line that makes
any other player draw such a part whole); check_drawn_text.py compares each gloss card, as drawn, word for
word with its source. The browser run itself needs Edge and is proved on the built lessons, not here."""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_drawn_text as cdt  # noqa: E402
import write_screens as ws  # noqa: E402

TEMPLATE = Path(__file__).resolve().parents[1] / "scripts" / "board_player_template.html"
SRC = {"added-02_k06": {"type": "gloss", "term": "reassure", "explanation": "To help someone feel less worried.",
                        "text": "The nurse reassures the patient."}}


def moment(meaning, example, t=332.0, on_example=True):
    return {"block": "added-02_k06", "board": "added-02_t1", "state": "added-02_t1.s6", "t": t, "erase": False,
            "term": {"on": True, "words": ["reassure"]},
            "meaning": {"on": True, "words": meaning.split()},
            "example": {"on": True, "words": example.split()} if on_example else {"on": False}}


class WriteInTest(unittest.TestCase):
    def test_no_write_in_holds_its_last_clip(self):
        html = TEMPLATE.read_text(encoding="utf-8")
        uses = re.findall(r"animation:\s*write-in[^;]*;", html)
        self.assertTrue(uses)
        for u in uses:
            self.assertNotRegex(u, r"\bboth\b", u)
            self.assertNotRegex(u, r"\bforwards\b", u)
        self.assertRegex(html, r"\.gl-m\.on:not\(\.settled\), \.gl-x\.on:not\(\.settled\) \{ animation: write-in "
                               r"[^;]*backwards;")

    def test_override_only_where_a_write_in_part_is(self):
        gloss = '<div class="blk gl"><div class="gl-h"><span class="pt gl-m" data-part="k.1">x</span></div></div>'
        self.assertEqual(ws.write_in_css([None, "<div class='blk'>x</div>", gloss]), ws.WRITE_IN_CSS)
        self.assertEqual(ws.write_in_css(['<div class="blk tbl"><table></table></div>', None]), "")
        # a class name that only starts the same is not a part
        self.assertEqual(ws.write_in_css(['<div class="gl-mx">x</div>']), "")
        self.assertIn("animation-fill-mode:backwards!important", ws.WRITE_IN_CSS)
        for sel in (".gl-m", ".gl-x", ".cl-piece", ".cl-rm"):
            self.assertIn(sel, ws.WRITE_IN_CSS)


class CompareGlossesTest(unittest.TestCase):
    def test_whole_card_passes(self):
        self.assertEqual(cdt.compare_glosses(SRC, [moment("To help someone feel less worried.",
                                                          "The nurse reassures the patient.")]), [])

    def test_owners_cut_card_fails_word_for_word(self):
        bad = cdt.compare_glosses(SRC, [moment("To help someone feel less", "The nurse reassures the patient.")])
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["part"], "meaning")
        self.assertEqual(bad[0]["drawn"], "To help someone feel less")
        self.assertEqual(bad[0]["source"], "To help someone feel less worried.")

    def test_a_part_not_drawn_yet_is_compared_later(self):
        early = moment("To help someone feel less worried.", "", t=310.0, on_example=False)
        late = moment("To help someone feel less worried.", "The nurse reassures the patient.")
        self.assertEqual(cdt.compare_glosses(SRC, [early, late]), [])
        never = cdt.compare_glosses(SRC, [early])
        self.assertEqual([(g["part"], g["drawn"]) for g in never], [("example", "(never drawn)")])

    def test_a_word_split_by_a_mark_is_whole(self):
        split = moment("To help someone feel less worried.", "The nurse reassures the patient .")
        split["term"]["words"] = ["reass", "ure"]
        self.assertEqual(cdt.compare_glosses(SRC, [split]), [])

    def test_a_cut_example_fails(self):
        bad = cdt.compare_glosses(SRC, [moment("To help someone feel less worried.", "The nurse reassures")])
        self.assertEqual([g["part"] for g in bad], ["example"])


if __name__ == "__main__":
    unittest.main()
