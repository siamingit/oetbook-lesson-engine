"""The board is measured where the learner sees it: above the control bar, on a
small phone's frame, and with a wider device font (maintainer, 2026-10-08).

    .venv/Scripts/python -m unittest spike.tests.test_visible_area

The player of Reading 3 as built in commit dd65ec6 (bundle 1.16, before the
fix) is kept as a fixture in its lesson folder, generated/lesson-player-dd65ec6:
on a phone held landscape (915x412) its last extract lines and a callout were
under the control bar, and the checks of that commit passed it. The checks as
fixed must fail it, and pass the lesson's current player. Lesson content is not
in git, so the test is skipped where the lesson folder or Edge is missing (CI).
Slow: each check drives the player in headless Edge at three frame sizes.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LESSON = Path(r"C:\OET\lessons\reading-03-part-b")
FIXTURE = LESSON / "generated" / "lesson-player-dd65ec6"
CURRENT = LESSON / "generated" / "lesson-player"
EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
CHECKS = ["check_overflow", "check_overlap", "check_lens", "check_wide_font"]


def check(name: str, folder: Path) -> int:
    r = subprocess.run([sys.executable, str(ROOT / "spike" / "scripts" / f"{name}.py"), str(LESSON),
                        "--dir", str(folder)], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=3600)
    return r.returncode


@unittest.skipUnless(FIXTURE.is_dir() and any(Path(e).exists() for e in EDGE),
                     "needs the Reading 3 lesson folder, its dd65ec6 fixture and Edge")
class VisibleArea(unittest.TestCase):
    def test_checks_fail_the_dd65ec6_player(self):
        for name in CHECKS:
            with self.subTest(check=name):
                self.assertNotEqual(check(name, FIXTURE), 0, f"{name} passed the player that hid lines")

    def test_checks_pass_the_current_player(self):
        for name in CHECKS:
            with self.subTest(check=name):
                self.assertEqual(check(name, CURRENT), 0, f"{name} failed the current player")


if __name__ == "__main__":
    unittest.main()
