"""The site-player check's verdicts (ADR 050 amendment (9)): a spill, the site's guard and a moment still loading
fail in every lesson; a text under the teal look's minimum or contrast fails in a teal lesson only, and is listed
as not applied in a lesson in another look."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_site_player as csp   # noqa: E402
import style_c                    # noqa: E402

SMALL = {"kind": "small text", "block": "s_k01", "text": "a line", "value": 17.1}
LABEL = {"kind": "small label", "block": "s_k02", "text": "Since:", "value": 18.9}
DIM = {"kind": "low contrast", "block": "s_k01", "text": "a line", "value": 3.11}


def moment(**kw):
    return {"name": "board-01", "board": "s_t1", "found": [], **kw}


def lesson(look=None) -> Path:
    d = Path(tempfile.mkdtemp(prefix="oet-site-"))
    (d / "analysis").mkdir()
    info = {"lesson": {"title": "T", "type": "grammar", "style": "c"}, "sections": []}
    if look:
        info["lesson"]["look"] = look
    (d / "analysis" / "sections.json").write_text(json.dumps(info), encoding="utf-8")
    return d


class Verdicts(unittest.TestCase):
    def test_teal_fails_on_readability(self):
        fails, kept = csp.verdicts([moment(found=[SMALL, LABEL, DIM])], teal=True)
        self.assertEqual(len(fails), 3)
        self.assertEqual(kept, [])
        self.assertIn("small text 17.1 in s_k01", fails[0])

    def test_another_look_lists_readability_as_not_applied(self):
        fails, kept = csp.verdicts([moment(found=[SMALL, LABEL, DIM])], teal=False)
        self.assertEqual(fails, [])
        self.assertEqual(len(kept), 3)
        self.assertIn("low contrast 3.11 in s_k01", kept[2])

    def test_spills_guard_and_loading_fail_in_every_look(self):
        res = [moment(why="s_k03 spills"), moment(fit="zoom 0.81", why="s_k11 below 58.0"), moment(loading=True)]
        for teal in (True, False):
            fails, kept = csp.verdicts(res, teal=teal)
            self.assertEqual(len(fails), 3, teal)
            self.assertEqual(kept, [])
            self.assertIn("spills", fails[0])
            self.assertIn("draws the board smaller (zoom 0.81", fails[1])
            self.assertIn("Loading", fails[2])

    def test_a_guard_fault_still_fails_beside_readability_not_applied(self):
        fails, kept = csp.verdicts([moment(fit="zoom 0.81", why="x", found=[SMALL])], teal=False)
        self.assertEqual(len(fails), 1)
        self.assertEqual(len(kept), 1)

    def test_the_look_is_read_from_the_lesson(self):
        self.assertEqual(style_c.look_of(lesson("teal")), "teal")
        self.assertNotEqual(style_c.look_of(lesson()), "teal")



class InstallLock(unittest.TestCase):
    """Checks run side by side (runbook 18c) take turns at the fetch and at each commit's install."""

    def setUp(self):
        self.old, csp.WORK = csp.WORK, Path(tempfile.mkdtemp(prefix="oet-site-lock-"))

    def tearDown(self):
        csp.WORK = self.old

    def test_lock_held_then_freed(self):
        with csp.install_lock("web-abc"):
            self.assertTrue((csp.WORK / "web-abc.lock").exists())
        self.assertFalse((csp.WORK / "web-abc.lock").exists())

    def test_a_held_lock_makes_the_other_run_wait_and_give_up(self):
        with csp.install_lock("fetch"):
            with self.assertRaises(SystemExit):
                with csp.install_lock("fetch", wait_s=0):
                    pass
            self.assertTrue((csp.WORK / "fetch.lock").exists())

    def test_a_left_over_lock_is_taken(self):
        (csp.WORK / "fetch.lock").write_text("999999")
        os.utime(csp.WORK / "fetch.lock", (0, 0))
        with csp.install_lock("fetch", stale_s=60):
            pass
        self.assertFalse((csp.WORK / "fetch.lock").exists())


if __name__ == "__main__":
    unittest.main()
