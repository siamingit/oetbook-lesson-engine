"""A lesson with no recorded source (ADR 047): its config, its authored
introduction, and the runner skipping the source stages."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import build_lesson                        # noqa: E402
import paths                               # noqa: E402


def sections(L: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / "build_sections.py"), str(L), *args],
                          capture_output=True, text=True, encoding="utf-8")


class NoSourceConfig(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.L = Path(self.tmp.name) / "writing-99-test"
        self.L.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def config(self) -> dict:
        return json.loads((self.L / "analysis" / "sections.json").read_text(encoding="utf-8"))

    def test_made_once_with_authored_sections_and_intro(self):
        r = sections(self.L, "--no-source", "A Title", "--by", "tester")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sections(self.L, "--add-section", "1", "First", "--by", "t").returncode, 0)
        self.assertEqual(sections(self.L, "--add-section", "2", "Closing", "--kind", "closing").returncode, 0)
        info = self.config()
        self.assertTrue(paths.no_source(info))
        self.assertEqual(info["lesson"]["title"], "A Title")
        self.assertEqual([s["pages"] for s in info["sections"]], [[101], [102]])
        intro = paths.intro_section(info)
        self.assertEqual(intro, {"title": "Introduction", "pages": [paths.NO_SOURCE_INTRO_PAGE],
                                 "intro": True})
        self.assertEqual(paths.section_tag(intro["pages"]), "page-100")
        self.assertTrue(build_lesson.no_source(self.L))
        # made only once, and never over a lesson that has a source
        self.assertNotEqual(sections(self.L, "--no-source", "Again").returncode, 0)

    def test_no_deck_read_again(self):
        sections(self.L, "--no-source", "A Title")
        before = (self.L / "analysis" / "sections.json").read_bytes()
        r = sections(self.L)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no source", r.stdout + r.stderr)
        self.assertEqual((self.L / "analysis" / "sections.json").read_bytes(), before)

    def test_refused_where_a_source_exists(self):
        (self.L / "source").mkdir()
        r = sections(self.L, "--no-source", "A Title")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.L / "analysis" / "sections.json").exists())

    def test_source_stages_skipped(self):
        sections(self.L, "--no-source", "A Title")
        for stage in (build_lesson.stage_audio, build_lesson.stage_keyterm_candidates,
                      build_lesson.stage_keyterms, build_lesson.stage_transcribe,
                      build_lesson.stage_slides, build_lesson.stage_annotations):
            self.assertIsNone(stage(self.L, None))
        self.assertFalse((self.L / "analysis" / "runner.log").exists())


class LessonsWithASource(unittest.TestCase):
    def test_intro_unchanged(self):
        self.assertEqual(paths.intro_section({"contents_page": 3}),
                         {"title": "Introduction", "pages": [3], "intro": True})
        info = {"lesson": {"page": 2}, "intro": {"from_s": 0.0, "to_s": 46.0}}
        self.assertEqual(paths.intro_section(info),
                         {"title": "Introduction", "pages": [2], "intro": True, "span": [0.0, 46.0]})
        self.assertFalse(paths.no_source(info))


if __name__ == "__main__":
    unittest.main()
