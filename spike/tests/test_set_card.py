"""ADR 059: a block's `set_card` names the role-play card it quotes word for word."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import board_style                  # noqa: E402
import write_screens as ws          # noqa: E402


class SetCard(unittest.TestCase):
    def test_reference_shape(self):
        for good in ("oa-ss-med-0008 RP2", "oa-ss-nur-0001 RP1"):
            self.assertTrue(ws.CARD_REF.fullmatch(good), good)
        for bad in ("oa-ss-med-0008", "oa-ss-med-0008 RP3", "oa-ss-med-08 RP1", "card two", ""):
            self.assertIsNone(ws.CARD_REF.fullmatch(bad), bad)

    def test_board_style_keeps_set_card(self):
        # board_style.derive clears a block's derived `card`; the ADR 059 field must survive it
        b = {"id": "k01", "type": "table", "header": ["Candidate card", "Tasks"],
             "rows": [["Task 1", "Explain condition (very common)"]], "set_card": "oa-ss-med-0008 RP2"}
        boards = [{"fixed": [], "states": [{"working": ["k01"]}]}]
        board_style.derive(boards, {"k01": b}, "A test")
        self.assertEqual(b.get("set_card"), "oa-ss-med-0008 RP2")


if __name__ == "__main__":
    unittest.main()
