"""The publish step (ADR 039 amendment of 2026-10-23): a package built from a made-up lesson
passes the pinned contracts; it is byte for byte the same when built again; a package that fails a
check is not written; content names never collide; no reference leaves the package; the narration's
timing is checked against its masters (and a file whose priming is not trimmed fails); an exam
file's source comes from the release data only; versions and retired sections (G5); the release's
dry run creates nothing.

The made-up lesson is the contracts' own example lesson (examples/lesson/grammar-99-example),
turned back into the engine's local form (WAV masters in section folders, ../ paths) and given an
exam recording, a heard sentence and a pronunciation clip. Needs ffmpeg and the pinned contracts
(lesson_package.py --fetch). The contracts are private and CI has no token for them (owner,
2026-10-23): CI sets OETBOOK_CONTRACTS_OPTIONAL=1, and the tests that need them are skipped there
("skipped: contracts not available in CI"); everywhere else a missing contract fails the tests.

    .venv/Scripts/python -m unittest spike/tests/test_publish_lesson.py
"""

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
import zipfile
from pathlib import Path
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lesson_package as lp  # noqa: E402
import publish_lesson as pub  # noqa: E402

SKIPPED = "skipped: contracts not available in CI"
if os.environ.get("OETBOOK_CONTRACTS_OPTIONAL") == "1":
    try:
        CONTRACTS = lp.load(fetch_missing=False)
    except SystemExit:
        CONTRACTS = None
else:
    CONTRACTS = lp.load(fetch_missing=False)
needs_contracts = unittest.skipIf(CONTRACTS is None, SKIPPED)
EXAMPLE = "examples/lesson/grammar-99-example/"
LESSON = "grammar-99-example"


def write_wav(path: Path, seconds: float, seed: int) -> None:
    """A speech-like signal: 50 ms of silence, then modulated tones and noise."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * pub.RATE)) / pub.RATE
    sig = sum(np.sin(2 * np.pi * f * t) * (0.5 + 0.5 * np.sin(2 * np.pi * m * t))
              for f, m in zip(rng.uniform(150, 2000, 6), rng.uniform(2, 7, 6)))
    sig = sig / np.abs(sig).max() * 0.4 + rng.normal(0, 0.02, len(t))
    sig[: int(0.05 * pub.RATE)] = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(pub.RATE)
        w.writeframes((np.clip(sig, -1, 1) * 32767).astype("<i2").tobytes())


def write_mp3(path: Path, seconds: float, seed: int) -> None:
    wav = path.with_suffix(".src.wav")
    write_wav(wav, seconds, seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "128k",
                    "-map_metadata", "-1", "-fflags", "+bitexact", str(path)], check=True)
    wav.unlink()


def made_up_library() -> Path:
    """<root>/lessons/grammar-99-example, its course folder with section tags; returns the lesson."""
    root = Path(tempfile.mkdtemp())
    L = root / "lessons" / LESSON
    player = L / "generated" / "lesson-player"
    player.mkdir(parents=True)
    b = json.loads(CONTRACTS.files[EXAMPLE + "bundle.json"])
    t = json.loads(CONTRACTS.files[EXAMPLE + "text.json"])
    b["format_version"] = t["format_version"] = "1.20"
    utts = lp.utterances_of(b)
    # Two masters with one name in two section folders (the engine's names repeat), one per clip.
    locals_ = ["../page-1/boards/audio/3f1c0a9d2b7e.wav", "../page-2/boards/audio/8a44d2c19e05.wav",
               "../page-2b/boards/audio/8a44d2c19e05.wav"]
    for i, (u, rel, secs) in enumerate(zip(utts, locals_, (4.7, 4.1, 3.6))):
        u["audio_file"] = rel
        write_wav((player / rel).resolve(), secs, seed=i)
    # An exam recording (1.18), from the release data.
    exam = L / "generated" / "exam-audio" / "oa-set-la-0099-e1.000000000000.mp3"
    write_mp3(exam, 1.0, seed=7)
    sha = lp.sha256_file(exam)
    last = b["boards"][1]["states"][0]["utterances"]
    last.append({"id": last[-1]["id"] + ".x", "kind": "exam", "text": None, "provenance": "release",
                 "audio_file": "../exam-audio/" + exam.name, "start": 13.8, "end": 14.4,
                 "clip_in": 0.1, "clip_out": 0.7, "cues": [], "refs": [], "reading": [],
                 "exam": {"stimulus": "oa-set-la-0099-e1", "label": "Extract 1", "span": "exam",
                          "rows": None, "release": "oa-pkg-made-up v1", "sha256": sha}})
    # A gloss with a pronunciation clip (1.15) and a heard sentence with a bare file name (as
    # Listening 2's, changelog §12 item 2); its image back at ../images/.
    write_mp3(L / "generated" / "vocab-audio" / "schedule.mp3", 0.6, seed=8)
    g = b["blocks"]["page-2_k03"]
    svg = g["image"]["file"]
    (L / "generated" / "images").mkdir(parents=True)
    (L / "generated" / "images" / Path(svg).name).write_bytes(CONTRACTS.files[EXAMPLE + svg])
    g["html"] = g["html"].replace(f'src="{svg}"', f'src="../images/{Path(svg).name}"')
    g["image"]["file"] = f"../images/{Path(svg).name}"
    g["audio"] = {"file": "../vocab-audio/schedule.mp3", "seconds": 0.6}
    g["heard"] = {"file": exam.name, "stimulus": "oa-set-la-0099-e1", "start": 0.2, "end": 0.6}
    g["html"] = g["html"].replace("</div>", '<button type="button" class="gl-say" data-audio='
                                  '"../vocab-audio/schedule.mp3" aria-label="Hear schedule"></button>'
                                  f'<button type="button" class="gl-heard" data-audio="../exam-audio/{exam.name}" '
                                  'data-start="0.2" data-end="0.6"></button></div>', 1)
    (player / "bundle.json").write_text(json.dumps(b, indent=2), encoding="utf-8")
    (player / "text.json").write_text(json.dumps(t, indent=2), encoding="utf-8")
    (player / "blocks.css").write_bytes(CONTRACTS.files[EXAMPLE + "blocks.css"])
    (L / "analysis").mkdir()
    (L / "analysis" / "gates.json").write_text(json.dumps(
        {"final": {"by": "Siavash", "on": "2026-10-01 10:00"}}), encoding="utf-8")
    (L / "analysis" / "practice_set.json").write_text(json.dumps({
        "set_id": "oa-set-la-0099", "release": {"package_id": "oa-pkg-made-up", "package_version": 1},
        "parts": [{"code": "LA", "stimuli": [{"stimulus_id": "oa-set-la-0099-e1", "audio": {"sha256": sha}}]}]}),
        encoding="utf-8")
    write_tags(L, {"page-1": [], "page-2": ["grammar.verb-tenses.present-perfect"]})
    return L


def write_tags(L: Path, tags: dict, approved=None) -> None:
    course = L.parents[1] / "course"
    course.mkdir(exist_ok=True)
    (course / "section-tags.json").write_text(json.dumps({
        "format": "oetbook-section-tags", "taxonomy": CONTRACTS.tag_taxonomy,
        "courses": {"grammar": {"approved": approved}},
        "lessons": {L.name: {"sections": [{"id": k, "teaches": v} for k, v in tags.items()]}}}), encoding="utf-8")


def quiet(*_):
    pass


@needs_contracts
class BuiltPackage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L = made_up_library()
        cls.report = pub.build(cls.L, CONTRACTS, workers=2, log=quiet)
        cls.folder = Path(cls.report["folder"])
        cls.manifest = json.loads((cls.folder / "manifest.json").read_text(encoding="utf-8"))
        cls.bundle = json.loads((cls.folder / "bundle.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.L.parents[1])

    def test_passes_the_pinned_contracts(self):
        self.assertEqual(self.report["validation"]["errors"], [])
        again = lp.validate_package(self.folder, CONTRACTS)
        self.assertTrue(again.ok, again.lines())

    def test_manifest(self):
        m = self.manifest["lesson"]
        self.assertEqual(self.manifest["contracts_version"], "1.10.0")
        self.assertEqual(self.manifest["taxonomy"], CONTRACTS.taxonomy_ref(2))       # a Grammar lesson: v2
        self.assertEqual(m["approved"], {"by": "siavash", "on": "2026-10-01"})
        self.assertEqual(m["package_version"], 1)
        self.assertEqual(m["professions"], "all")
        self.assertTrue(all(s["criteria"] == [] and s["professions"] == "all" for s in self.manifest["sections"]))
        self.assertEqual([s["teaches"] for s in self.manifest["sections"]],
                         [[], ["grammar.verb-tenses.present-perfect"]])

    def test_audio_kinds_and_names(self):
        kinds = {}
        for x in self.manifest["media"]:
            kinds[x.get("kind", x["mime"])] = kinds.get(x.get("kind", x["mime"]), 0) + 1
        self.assertEqual(kinds, {"narration": 3, "exam": 1, "pronunciation": 1, "image/svg+xml": 1})
        self.assertEqual(self.report["basename_collisions_resolved"], ["8a44d2c19e05.wav"])
        paths = [x["path"] for x in self.manifest["media"]]
        self.assertEqual(len(paths), len(set(paths)))
        exam = next(x for x in self.manifest["media"] if x.get("kind") == "exam")
        self.assertEqual(exam["exam"], {"set": "oa-set-la-0099", "part": "LA", "stimulus": "oa-set-la-0099-e1",
                                        "release": "oa-pkg-made-up v1"})
        src = self.L / "generated" / "exam-audio" / "oa-set-la-0099-e1.000000000000.mp3"
        self.assertEqual((self.folder / exam["path"]).read_bytes(), src.read_bytes())

    def test_paths_rewritten_inside_the_package(self):
        text = (self.folder / "bundle.json").read_text(encoding="utf-8")
        self.assertNotIn("../", text)
        g = self.bundle["blocks"]["page-2_k03"]
        self.assertEqual(lp.html_audio(g["html"], "gl-say"), [g["audio"]["file"]])
        self.assertEqual(lp.html_audio(g["html"], "gl-heard"), [g["heard"]["file"]])
        for at, p in lp.references(self.bundle, ""):
            self.assertTrue((self.folder / p).is_file(), f"{at}: {p}")

    def test_narration_timing(self):
        self.assertLessEqual(self.report["worst_start_ms"], 10)
        self.assertLessEqual(self.report["worst_length_ms"], 10)

    def test_zip_holds_the_folder_at_its_root(self):
        with zipfile.ZipFile(self.report["zip"]) as z:
            self.assertEqual(z.read("manifest.json"), (self.folder / "manifest.json").read_bytes())
            self.assertIn("bundle.json", z.namelist())

    def test_same_inputs_same_bytes(self):
        first = self.report["zip_sha256"]
        shutil.rmtree(pub.package_dir(self.L) / "audio-cache")      # encode again too
        again = pub.build(self.L, CONTRACTS, workers=2, log=quiet)
        self.assertEqual(again["zip_sha256"], first)
        self.assertEqual(again["manifest_sha256"], self.report["manifest_sha256"])


@needs_contracts
class Refusals(unittest.TestCase):
    def setUp(self):
        self.L = made_up_library()

    def tearDown(self):
        shutil.rmtree(self.L.parents[1])

    def assert_nothing_written(self):
        out = pub.package_dir(self.L)
        left = [p.name for p in out.iterdir() if p.name != "audio-cache"] if out.exists() else []
        self.assertEqual(left, [])

    def test_a_failing_package_is_not_written(self):
        write_tags(self.L, {"page-1": [], "page-2": ["speaking"]})         # not on the session tag list
        with self.assertRaises(pub.Refused) as e:
            pub.build(self.L, CONTRACTS, workers=2, log=quiet)
        self.assertIn("LP-TEACHES-NOT-ALLOWED", str(e.exception))
        self.assert_nothing_written()

    def test_exam_source_only_from_the_release_data(self):
        ps = self.L / "analysis" / "practice_set.json"
        doc = json.loads(ps.read_text(encoding="utf-8"))
        doc["parts"][0]["stimuli"] = []
        ps.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaises(pub.Refused) as e:
            pub.build(self.L, CONTRACTS, workers=2, log=quiet)
        self.assertIn("PUB-EXAM-SOURCE", str(e.exception))
        self.assert_nothing_written()

    def test_exam_release_only_from_the_release_data(self):
        ps = self.L / "analysis" / "practice_set.json"
        doc = json.loads(ps.read_text(encoding="utf-8"))
        del doc["release"]
        ps.write_text(json.dumps(doc), encoding="utf-8")
        with self.assertRaises(pub.Refused) as e:
            pub.build(self.L, CONTRACTS, workers=2, log=quiet)
        self.assertIn("names no release", str(e.exception))
        self.assert_nothing_written()

    def test_no_final_gate(self):
        (self.L / "analysis" / "gates.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(pub.Refused):
            pub.build(self.L, CONTRACTS, workers=2, log=quiet)

    def test_release_dry_run_creates_nothing(self):
        pub.build(self.L, CONTRACTS, workers=2, log=quiet)
        calls = []

        def fake_gh(*args):
            calls.append(args)
            return "[]"
        with mock.patch.object(pub, "gh", fake_gh), mock.patch.object(pub.lp, "load", lambda: CONTRACTS):
            blocked = pub.release(self.L, dry_run=True, log=quiet)      # tags proposed, not approved
            self.assertEqual(len(blocked["blockers"]), 1)
            with self.assertRaises(pub.Refused):
                pub.release(self.L, dry_run=False, log=quiet)
            write_tags(self.L, {"page-1": [], "page-2": ["grammar.verb-tenses.present-perfect"]},
                       approved={"by": "siavash", "on": "2026-10-23"})
            plan = pub.release(self.L, dry_run=True, log=quiet)
        self.assertEqual(plan["blockers"], [])
        self.assertEqual(plan["tag"], f"{LESSON}-v1")
        self.assertEqual([a["name"] for a in plan["assets"]], ["manifest.json", f"{LESSON}-v1.zip"])
        self.assertEqual(plan["repository"], "siamingit/oetacademy-sessions")
        self.assertFalse(any("create" in c for c in calls))
        self.assertFalse(pub.record_path(self.L).exists())

    def test_release_checked_on_github_before_it_is_recorded(self):
        pub.build(self.L, CONTRACTS, workers=2, log=quiet)
        write_tags(self.L, {"page-1": [], "page-2": ["grammar.verb-tenses.present-perfect"]},
                   approved={"by": "siavash", "on": "2026-10-23"})
        tag = f"{LESSON}-v1"
        folder, zpath = pub.package_dir(self.L) / tag, pub.package_dir(self.L) / f"{tag}.zip"
        assets = [{"name": p.name, "size": p.stat().st_size, "digest": f"sha256:{lp.sha256_file(p)}"}
                  for p in (folder / "manifest.json", zpath)]

        def fake_gh(view):
            def run(*args):
                if args[:2] == ("release", "list"):
                    return "[]"
                if args[:2] == ("release", "view"):
                    return json.dumps(view)
                return ""
            return run
        good = {"tagName": tag, "assets": assets, "isDraft": False, "isPrerelease": False,
                "publishedAt": "2026-10-23T10:00:00Z", "url": "https://example.invalid/" + tag}
        bad = dict(good, assets=[dict(assets[0]), dict(assets[1], digest="sha256:" + "0" * 64)])
        with mock.patch.object(pub.lp, "load", lambda: CONTRACTS):
            with mock.patch.object(pub, "gh", fake_gh(bad)):
                with self.assertRaises(pub.Refused):
                    pub.release(self.L, dry_run=False, log=quiet)
            self.assertFalse(pub.record_path(self.L).exists())
            with mock.patch.object(pub, "gh", fake_gh(good)):
                pub.release(self.L, dry_run=False, log=quiet)
        record = json.loads(pub.record_path(self.L).read_text(encoding="utf-8"))
        self.assertEqual([r["tag"] for r in record["releases"]], [tag])


class Checks(unittest.TestCase):
    def test_name_collision_fails(self):
        f = lp.Findings()
        pub.assign_names({"../a/x.wav": "ab" * 8 + "00" * 24, "../b/x.wav": "ab" * 8 + "11" * 24}, "m4a", f)
        self.assertEqual(f.codes("error"), ["PUB-NAME-COLLISION"])
        f = lp.Findings()
        names = pub.assign_names({"../a/x.wav": "11" * 32, "../b/x.wav": "22" * 32}, "m4a", f)
        self.assertTrue(f.ok)
        self.assertEqual(len(set(names.values())), 2)

    @needs_contracts
    def test_reference_outside_the_package_fails(self):
        L = made_up_library()
        try:
            r = pub.build(L, CONTRACTS, workers=2, log=quiet)
            folder = Path(r["folder"])
            b = json.loads((folder / "bundle.json").read_text(encoding="utf-8"))
            g = b["blocks"]["page-2_k03"]
            g["html"] = g["html"].replace(f'data-audio="{g["audio"]["file"]}"', 'data-audio="../vocab-audio/x.mp3"')
            (folder / "bundle.json").write_text(json.dumps(b), encoding="utf-8")
            f = lp.validate_package(folder, CONTRACTS)
            self.assertIn("PUB-OUTSIDE", f.codes("error"))
            self.assertIn("LP-AUDIO-HTML", f.codes("error"))
        finally:
            shutil.rmtree(L.parents[1])

    def test_untrimmed_priming_fails_the_timing_check(self):
        d = Path(tempfile.mkdtemp())
        try:
            write_wav(d / "m.wav", 2.0, seed=3)
            pub.encode(d / "m.wav", d / "ok.m4a")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(d / "ok.m4a"), "-c", "copy",
                            "-use_editlist", "0", str(d / "bad.m4a")], check=True)
            good, bad = pub.timing(d / "m.wav", d / "ok.m4a"), pub.timing(d / "m.wav", d / "bad.m4a")
            f = lp.Findings()
            pub.timing_findings(good, "ok", f)
            # An older decoder skips the priming but not the edit list's end trim (CI's ffmpeg 6.1
            # decodes this file 20 ms long; 9.0 exactly): the length check catches it, so only
            # the start and the edit list are asserted for the good file here.
            self.assertFalse({"PUB-AUDIO-START", "PUB-AUDIO-EDITLIST", "PUB-AUDIO-MATCH"} & set(f.codes("error")),
                             f.lines())
            self.assertGreater(good["priming_samples"], 0)
            f = lp.Findings()
            pub.timing_findings(bad, "bad", f)
            self.assertIn("PUB-AUDIO-START", f.codes("error"))
            self.assertIn("PUB-AUDIO-EDITLIST", f.codes("error"))
        finally:
            shutil.rmtree(d)

    def test_versions(self):
        empty = {"releases": []}
        self.assertEqual(pub.next_version("reading-01-overview", empty), 1)
        self.assertEqual(pub.next_version("grammar-01-verb-tenses", empty), 2)
        self.assertEqual(pub.next_version("x-01-y", {"releases": [{"package_version": 1}, {"package_version": 2}]}), 3)

    def test_retired_sections(self):
        L = Path(tempfile.mkdtemp()) / "x-01-y"
        (L / "analysis").mkdir(parents=True)
        record = {"releases": [{"package_version": 1, "sections": ["page-1", "page-2"], "retired_sections": []}]}
        with self.assertRaises(pub.Refused):
            pub.retirements(L, record, ["page-1", "page-3"], 2)
        (L / "analysis" / "publish_retired.json").write_text('{"page-2": ["page-3"]}', encoding="utf-8")
        self.assertEqual(pub.retirements(L, record, ["page-1", "page-3"], 2),
                         [{"id": "page-2", "retired_in": 2, "replaced_by": ["page-3"]}])
        record["releases"].append({"package_version": 2, "sections": ["page-1", "page-3"],
                                   "retired_sections": [{"id": "page-2", "retired_in": 2, "replaced_by": ["page-3"]}]})
        self.assertEqual(pub.retirements(L, record, ["page-1", "page-3"], 3)[0]["retired_in"], 2)
        shutil.rmtree(L.parent)


class PinnedContracts(unittest.TestCase):
    def test_a_zip_with_another_hash_is_refused(self):
        d = Path(tempfile.mkdtemp())
        try:
            with zipfile.ZipFile(d / lp.lock()["asset"], "w") as z:
                z.writestr("VERSION", "1.8.0\n")
            with mock.patch.dict("os.environ", {"OETBOOK_CONTRACTS_DIR": str(d)}):
                with self.assertRaises(SystemExit) as e:
                    lp.load(fetch_missing=False)
            self.assertIn("SHA-256", str(e.exception))
        finally:
            shutil.rmtree(d)

    def test_the_lock_pins_1_10_0(self):
        lk = lp.lock()
        self.assertEqual((lk["tag"], lk["sha256"]), ("contracts-v1.10.0",
                         "3bf0d421ec35590087d2514b6554ac8a7aa4afdfc12a222aa6932b7ab8442420"))

    @needs_contracts
    def test_the_loaded_contracts_are_1_10_0(self):
        self.assertEqual(CONTRACTS.version, "1.10.0")
        self.assertEqual(CONTRACTS.tag_taxonomy, {"id": "oetacademy-topics", "version": 3, "sha256":
                         "2742d1c707a59215fa5f07e240a48fceb8ab2f5318c829a617e10ea7fff3814c"})
        self.assertEqual(CONTRACTS.taxonomy_ref(2)["sha256"],
                         "f3ef57ae8243acc24eeee4ef79efcc9426fe5d3f1fd404d8aaf8984d2a434761")


@needs_contracts
class TaxonomyPerCourse(unittest.TestCase):
    """ADR 039 amendment of 2026-10-26: Writing manifests name taxonomy v3, every other course v2;
    the check takes v2 or v3 (contracts 1.10.0), each key checked against the version named."""

    def manifest(self, version, keys):
        return {"contracts_version": CONTRACTS.version, "taxonomy": CONTRACTS.taxonomy_ref(version),
                "lesson": {"professions": "all", "package_version": 1}, "files": {}, "media": [],
                "retired_sections": [],
                "sections": [{"id": "page-2", "intro": False, "teaches": keys, "criteria": [], "professions": "all"}]}

    def codes(self, m):
        f = lp.Findings()
        lp.check_manifest(m, Path(tempfile.gettempdir()), CONTRACTS, f)
        return f.codes("error")

    def test_course_versions(self):
        self.assertEqual(pub.manifest_taxonomy("writing-01-overview", CONTRACTS), CONTRACTS.taxonomy_ref(3))
        for lesson in ("grammar-01-verb-tenses", "vocabulary-01-word-forms", "reading-01-overview",
                       "listening-01-overview"):
            self.assertEqual(pub.manifest_taxonomy(lesson, CONTRACTS), CONTRACTS.taxonomy_ref(2))

    def test_v2_and_v3_both_accepted(self):
        self.assertEqual(self.codes(self.manifest(2, ["writing.content"])), [])
        self.assertEqual(self.codes(self.manifest(3, ["writing.language.word-order"])), [])

    def test_a_v3_key_under_v2_is_unknown(self):
        self.assertEqual(self.codes(self.manifest(2, ["writing.language.word-order"])), ["LP-TOPIC-UNKNOWN"])

    def test_a_version_or_hash_not_in_the_release(self):
        m = self.manifest(2, ["grammar"])
        m["taxonomy"] = dict(m["taxonomy"], version=99)
        self.assertIn("LP-TAXONOMY-UNKNOWN", self.codes(m))
        m = self.manifest(2, ["grammar"])
        m["taxonomy"] = dict(m["taxonomy"], sha256="0" * 64)
        self.assertIn("LP-TAXONOMY-HASH", self.codes(m))
        m = self.manifest(1, ["grammar"])                                   # in the release, before the list
        self.assertIn("LP-TEACHES-NOT-ALLOWED", self.codes(m))

    def test_tags_file_refuses_a_key_its_course_version_lacks(self):
        L = made_up_library()
        try:
            write_tags(L, {"page-1": [], "page-2": ["writing.language.grammar"]})      # a Grammar lesson: v2
            bundle = json.loads((L / "generated" / "lesson-player" / "bundle.json").read_text(encoding="utf-8"))
            with self.assertRaises(pub.Refused) as e:
                pub.lesson_tags(L, bundle, CONTRACTS)
            self.assertIn("taxonomy v2", str(e.exception))
        finally:
            shutil.rmtree(L.parents[1])


if __name__ == "__main__":
    unittest.main()
