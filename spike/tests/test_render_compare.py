"""render_compare never writes under the finished lessons (owner, 2026-10-14,
after a stale backup of 00:29 was restored over the 16 finished lessons).

    .venv/Scripts/python -m unittest spike.tests.test_render_compare

A made-up library (two lessons and a course folder) stands in for C:\\OET; the
render scripts and Edge are replaced by stand-ins that write into whatever lesson
they are given, as the real ones do. Every file write, copy, rename and delete the
snapshot makes is recorded: none may land under the made-up lessons, nor under the
real C:\\OET\\lessons, and the made-up lessons must be byte-identical afterwards.
Standard library only; runs in CI.
"""

import builtins
import hashlib
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import render_compare as rc    # noqa: E402

REAL_LESSONS = r"c:\oet\lessons"


def real_lessons(p) -> bool:
    s = str(p).replace("/", "\\").lower()
    return s == REAL_LESSONS or s.startswith(REAL_LESSONS + "\\")


def tree(root: Path) -> dict:
    return {str(f.relative_to(root)): (hashlib.sha256(f.read_bytes()).hexdigest(), f.stat().st_mtime_ns)
            for f in sorted(root.rglob("*")) if f.is_file()}


class Writes:
    """Records the target of every write-like call while active."""

    def __init__(self):
        self.targets = []
        self.patches = []

    def _wrap(self, owner, name, target_of):
        orig = getattr(owner, name)

        def wrapper(*a, **k):
            t = target_of(*a, **k)
            if t is not None:
                self.targets.append(str(t))
            return orig(*a, **k)
        self.patches.append(mock.patch.object(owner, name, wrapper))

    def __enter__(self):
        writing = lambda mode: any(c in mode for c in "wax+")         # noqa: E731
        self._wrap(builtins, "open", lambda f, mode="r", *a, **k: f if writing(mode) else None)
        self._wrap(Path, "open", lambda self_, mode="r", *a, **k: self_ if writing(mode) else None)
        for name in ("write_text", "write_bytes", "mkdir", "touch", "unlink", "rmdir"):
            self._wrap(Path, name, lambda self_, *a, **k: self_)
        for name in ("rename", "replace"):
            self._wrap(Path, name, lambda self_, target, *a, **k: target)
        for name in ("makedirs", "mkdir", "remove", "unlink", "rmdir"):
            self._wrap(os, name, lambda p, *a, **k: p)
        for name in ("rename", "replace"):
            self._wrap(os, name, lambda src, dst, *a, **k: dst)
        self._wrap(shutil, "copyfile", lambda src, dst, *a, **k: dst)
        self._wrap(shutil, "rmtree", lambda p, *a, **k: p)
        self._wrap(shutil, "move", lambda src, dst, *a, **k: dst)
        for p in self.patches:
            p.start()
        return self

    def __exit__(self, *exc):
        for p in reversed(self.patches):
            p.stop()


class ReadOnly(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rc-test-"))
        lib = self.tmp / "OET"
        self.lessons = lib / "lessons"
        L = self.lessons / "grammar-99-test"
        for rel, text in {"analysis/sections.json": '{"lesson": {}, "sections": []}',
                          "analysis/fit.json": "{}",
                          "generated/lesson-player/bundle.json": "{}",
                          "generated/lesson-player/player.html": "<html><body></body></html>",
                          "generated/lesson-preview/silent/player.html": "<html><body></body></html>",
                          "source/video.mp4": "not a video"}.items():
            (L / rel).parent.mkdir(parents=True, exist_ok=True)
            (L / rel).write_text(text, encoding="utf-8")
        other = self.lessons / "listening-99-unbuilt" / "analysis"
        other.mkdir(parents=True)
        (other / "sections.json").write_text("{}", encoding="utf-8")
        (lib / "course").mkdir()
        (lib / "course" / "course-index.json").write_text("{}", encoding="utf-8")
        self.out = self.tmp / "out"
        self.before = tree(self.lessons)
        self.given = []                       # every lesson path handed to a render or to Edge
        for p in (mock.patch.object(rc, "LESSONS", self.lessons),
                  mock.patch.object(rc, "OUT", self.out),
                  mock.patch.object(rc, "WORK", self.out / "work"),
                  mock.patch.object(rc.subprocess, "run", self.fake_subprocess_run),
                  mock.patch.object(rc, "fingerprint", self.fake_fingerprint),
                  mock.patch.object(rc, "sections", lambda L: [])):
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def fake_subprocess_run(self, cmd, **kw):
        """A render script: writes into the lesson it is given, as the real stages do."""
        L = Path(cmd[2])
        self.given.append(str(L))
        (L / "analysis" / "fit.json").write_text('{"rendered": true}', encoding="utf-8")
        (L / "generated" / "lesson-player" / "bundle.json").write_text('{"v": 2}', encoding="utf-8")
        (L / "generated" / "new-file.json").write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    def fake_fingerprint(self, player, width):
        self.given.append(str(player))
        h = rc.guard(player.with_name("player_fp.html"))
        h.write_text("harness", encoding="utf-8")
        h.unlink()
        return {"frame": width, "boards": []}

    def assert_untouched(self, writes):
        bad = [t for t in writes.targets if rc.under(t, self.lessons) or real_lessons(t)]
        self.assertEqual(bad, [], "render_compare wrote under the lessons")
        self.assertEqual(tree(self.lessons), self.before, "a lesson file changed")

    def test_snapshot_renders_copies_and_writes_nothing_under_the_lessons(self):
        with Writes() as w:
            rc.snapshot("after", [])
        self.assert_untouched(w)
        self.assertTrue(w.targets, "the recorder saw no writes at all")
        self.assertTrue(self.given)
        for g in self.given:
            self.assertFalse(rc.under(g, self.lessons) or real_lessons(g), g)
            self.assertTrue(rc.under(g, self.out / "work"), g)
        snap = self.out / "after" / "grammar-99-test"
        self.assertEqual((snap / "files" / "analysis" / "fit.json").read_text(encoding="utf-8"),
                         '{"rendered": true}')
        self.assertTrue((snap / "fingerprint.json").exists())
        self.assertFalse((self.out / "work" / "after").exists(), "the copy is deleted")

    def test_a_stale_backup_stops_before_anything_is_copied(self):
        (self.out / "backup" / "grammar-99-test" / "analysis").mkdir(parents=True)
        (self.out / "backup" / "grammar-99-test" / "analysis" / "fit.json").write_text(
            "stale", encoding="utf-8")
        with Writes() as w:
            with self.assertRaises(SystemExit) as e:
                rc.snapshot("after", [])
        self.assertIn("nothing was copied, rendered or restored", str(e.exception))
        self.assertIn("_stale", str(e.exception))
        self.assertEqual(w.targets, [])
        self.assertEqual(self.given, [])
        self.assert_untouched(w)

    def test_a_leftover_copy_or_existing_snapshot_stops(self):
        (self.out / "work" / "before").mkdir(parents=True)
        with self.assertRaises(SystemExit):
            rc.snapshot("after", [])
        shutil.rmtree(self.out / "work")
        (self.out / "after").mkdir(parents=True)
        with self.assertRaises(SystemExit):
            rc.snapshot("after", [])
        self.assertEqual(self.given, [])
        self.assertEqual(tree(self.lessons), self.before)

    def test_backup_and_restore_are_refused(self):
        for cmd in ("backup", "restore"):
            with mock.patch.object(sys, "argv", ["render_compare.py", cmd]), Writes() as w:
                with self.assertRaises(SystemExit) as e:
                    rc.main()
            self.assertIn("REFUSED", str(e.exception))
            self.assertEqual(w.targets, [])
        self.assertEqual(tree(self.lessons), self.before)

    def test_guard_refuses_any_path_under_the_lessons(self):
        for p in (self.lessons, self.lessons / "grammar-99-test" / "analysis" / "fit.json"):
            with self.assertRaises(SystemExit):
                rc.guard(p)
        self.assertEqual(rc.guard(self.out / "x"), self.out / "x")

    def test_a_change_under_the_lessons_during_a_snapshot_is_an_alarm(self):
        def intruder(cmd, **kw):
            f = self.lessons / "grammar-99-test" / "analysis" / "fit.json"
            f.write_text("changed by someone else", encoding="utf-8")
            return self.fake_subprocess_run(cmd, **kw)
        with mock.patch.object(rc.subprocess, "run", intruder):
            with self.assertRaises(SystemExit) as e:
                rc.snapshot("after", [])
        self.assertIn("ALARM", str(e.exception))


class RealPaths(unittest.TestCase):
    def test_outputs_are_outside_the_real_lessons(self):
        self.assertTrue(real_lessons(rc.LESSONS))
        for p in (rc.OUT, rc.WORK):
            self.assertFalse(real_lessons(p), p)

    def test_no_backup_or_restore_code_is_left(self):
        src = Path(rc.__file__).read_text(encoding="utf-8")
        self.assertNotIn("def restore", src)
        self.assertNotIn("def backup", src)


if __name__ == "__main__":
    unittest.main()
