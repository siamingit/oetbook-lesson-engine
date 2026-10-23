"""Bundle format 1.21 (ADR 041): a board shown whole (`fit`), the version rule, and
the data the 1.20 builder wrote outside the format (changelog §12)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_lesson_boards as blb   # noqa: E402
import build_lesson_player as blp   # noqa: E402
import lesson_package as lp         # noqa: E402


def boards():
    blocks = {"t": {"type": "table", "map": None}, "m": {"type": "table", "map": {"docs": []}}}
    bds = [{"id": "a_t1", "table": "t"},                         # a table board
           {"id": "a_t2", "table": None},                        # no table
           {"id": "a_t3", "table": "t", "split": 55},            # a question board
           {"id": "a_t4", "table": "t", "listen": {"block": "t"}},  # a Listening board
           {"id": "a_t5", "table": "m"}]                         # a map board
    return bds, blocks


class Version(unittest.TestCase):
    def test_kind_versions_unchanged(self):
        self.assertEqual(blp.format_version("grammar-06-clause"), "1.12")
        self.assertEqual(blp.format_version("reading-05-part-c-2", part_c=True), "1.17")
        self.assertEqual(blp.format_version("listening-02-part-a", listening=True), "1.20")

    def test_newer_wins_only_when_later(self):
        self.assertEqual(blp.format_version("grammar-06-clause", newer="1.21"), "1.21")
        self.assertEqual(blp.format_version("listening-04-part-c", listening=True, newer="1.21"), "1.21")
        self.assertEqual(blp.format_version("listening-04-part-c", listening=True, newer="1.13"), "1.20")
        self.assertEqual(blp.format_version("reading-01-overview", newer=None), "1.13")

    def test_declared_format(self):
        self.assertIsNone(blp.declared_format({"lesson": {}}))
        self.assertEqual(blp.declared_format({"lesson": {"bundle_format": "1.21"}}), "1.21")
        with self.assertRaises(SystemExit):
            blp.declared_format({"lesson": {"bundle_format": "1.22"}})


class Fit(unittest.TestCase):
    def test_a_table_board_takes_its_fit(self):
        bds, blocks = boards()
        blp.board_fits({"boards_fit": {"a_t1": "whole"}}, bds, blocks)
        self.assertEqual(bds[0]["fit"], "whole")
        self.assertTrue(all("fit" not in b for b in bds[1:]))

    def test_no_config_no_field(self):
        bds, blocks = boards()
        blp.board_fits({}, bds, blocks)
        self.assertTrue(all("fit" not in b for b in bds))

    def test_refused(self):
        for bid in ("a_t2", "a_t3", "a_t4", "a_t5", "a_t9"):
            bds, blocks = boards()
            with self.assertRaises(SystemExit, msg=bid):
                blp.board_fits({"boards_fit": {bid: "whole"}}, bds, blocks)
        bds, blocks = boards()
        with self.assertRaises(SystemExit):
            blp.board_fits({"boards_fit": {"a_t1": "full"}}, bds, blocks)

    def test_a_sample_build_skips_a_board_it_does_not_hold(self):
        bds, blocks = boards()
        blp.board_fits({"boards_fit": {"a_t9": "whole"}}, bds, blocks, sample=True)
        self.assertTrue(all("fit" not in b for b in bds))

    def test_the_package_check(self):
        bundle = {"format_version": "1.21", "blocks": {"t": {"type": "table"}},
                  "boards": [{"id": "a_t1", "table": "t", "fit": "whole"}]}
        f = lp.Findings()
        lp.check_fit(bundle, f)
        self.assertTrue(f.ok)
        for bad in ({"format_version": "1.20"}, {"boards": [{"id": "a_t1", "table": None, "fit": "whole"}]},
                    {"boards": [{"id": "a_t1", "table": "t", "fit": "full"}]}):
            f = lp.Findings()
            lp.check_fit({**bundle, **bad}, f)
            self.assertEqual(f.codes("error"), ["PUB-FIT"], bad)


class Provenance(unittest.TestCase):
    def test_a_description_by_the_agent_is_authored(self):
        prov, note = blb.description_provenance("agent (owner brief 2026-10-17): the lesson's parts")
        self.assertEqual(prov, "authored")
        self.assertIn("agent (owner brief 2026-10-17)", note)

    def test_a_listed_provenance_is_kept(self):
        self.assertEqual(blb.description_provenance("maintainer"),
                         ("maintainer", "The maintainer's one-line description (sections.json)."))
        self.assertEqual(blb.description_provenance(None)[0], "authored")


if __name__ == "__main__":
    unittest.main()
