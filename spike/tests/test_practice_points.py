"""Practice points (bundle 1.23, ADR 046 and its amendment of 2026-10-30): attached to the
pauses that name them, with their items in the site's contract, their IDs in the engine's block
and issued by the registry, and the fallback in the timeline; a lesson without
analysis/practice.json is untouched."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_lesson_player as blp  # noqa: E402
import lesson_package as lp  # noqa: E402
import practice_points as pp  # noqa: E402

LESSON = "writing-99-example"
TEXT = {"item_id": "oa-writing-900000", "type": "text", "number": 1, "prompt": "____ Mr Tom Hale …",
        "response": {"max_words": 6, "copy_from_source": False},
        "scoring": {"accepted": ["I am writing to refer", "I'm writing to refer"], "marking_scheme": "oet-typed-form-v1"},
        "feedback": {"key": "A referral.", "wrong_answers": [
            {"answer": "I refer", "why_wrong": "Too short.", "root_cause": "partial", "correct": "I am writing to refer"}]},
        "tags": {"practises": ["writing.purpose.introduction"]}, "version": 1, "status": "active"}
POINT = {"task": "Type the words a referral starts with.",
         "excerpt": {"sample": "invented", "title": "The paper", "rows": [{"label": "Plan:", "lines": ["Refer to the clinic"]}]},
         "items": [TEXT]}
SELFCHECK = {"item_id": "oa-writing-900001", "type": "selfcheck", "number": 1,
             "prompt": "Write the whole opening about Mr Tom Hale, in one sentence.",
             "response": {"max_words": 40, "copy_from_source": False, "size": "sentence"},
             "model": "I am writing to refer Mr Tom Hale, a 16-year-old student, for assessment.",
             "points": [{"point_id": "oa-writing-900001-c1", "text": "The frame", "tags": {"practises": ["writing.purpose.introduction"]}},
                        {"point_id": "oa-writing-900001-c2", "text": "The age", "tags": {"practises": ["writing.mechanics.punctuation"]}}],
             "scoring": {"method": "self-check"}, "feedback": {"key": "The frame, who and what you ask."},
             "tags": {"practises": ["writing.purpose.introduction"]}, "version": 1, "status": "active"}


def utt(uid, cues):
    return {"id": uid, "cues": cues}


def board(pause_text="practice: frame", seconds=8.0, answer=True):
    after = [{"id": "c1", "type": "type", "time": 12.0}] if answer else []
    return {"id": "page-5_t1", "section": "page-5", "states": [
        {"id": "page-5_t1.s1", "utterances": [
            utt("page-5_t1.s1.u1", [{"id": "c1", "type": "reveal", "time": 1.0},
                                    {"id": "c2", "type": "pause", "text": pause_text, "seconds": seconds,
                                     "time": 3.0, "time_end": 3.0 + seconds}]),
            utt("page-5_t1.s1.u2", after)]}]}


ERRSPOT = {"item_id": "oa-writing-900000", "type": "errorspot", "number": 1,
           "sentence": "I am referring Mrs Ann Lee, 42 years old cleaner, for assessment.",
           "scoring": {"error_words": {"first": 6, "last": 8}},
           "correction": {"response": {"max_words": 3, "copy_from_source": False},
                          "scoring": {"accepted": ["a 42-year-old"], "marking_scheme": "oet-typed-form-v1"}},
           "feedback": {"key": "The age before a noun: **a 42-year-old**.",
                        "wrong_words": [{"word": 9, "why_wrong": "Cleaner is right.", "root_cause": "wrong-referent",
                                         "correct": "a 42-year-old cleaner"}],
                        "wrong_corrections": [{"answer": "a 42 year old", "why_wrong": "Hyphens.", "root_cause": "wrong-form",
                                               "correct": "a 42-year-old"}]},
           "tags": {"practises": ["writing.language.grammar"]}, "version": 1, "status": "active"}


class PracticePoints(unittest.TestCase):
    def setUp(self):
        # a registry of the test's own: the repository's is never written by a test
        self.saved = pp.REGISTRY
        pp.REGISTRY = Path(tempfile.mkdtemp()) / "ids.json"
        pp.reserve(LESSON, 900000, 900999)
        self.assertEqual(pp.issue(LESSON, "frame", "item"), "oa-writing-900000")
        self.assertEqual(pp.issue(LESSON, "whole", "item"), "oa-writing-900001")

    def tearDown(self):
        pp.REGISTRY = self.saved

    def lesson(self, points):
        d = Path(tempfile.mkdtemp()) / LESSON
        (d / "analysis").mkdir(parents=True)
        if points is not None:
            (d / "analysis" / "practice.json").write_text(json.dumps(
                {"format": "oetbook-practice-points", "version": 1, "points": points}), encoding="utf-8")
        return d

    def test_a_lesson_without_the_file_is_untouched(self):
        bd = board()
        before = json.dumps(bd, sort_keys=True)
        self.assertFalse(pp.attach(self.lesson(None), [bd]))
        self.assertEqual(json.dumps(bd, sort_keys=True), before)

    def test_a_point_is_attached_to_its_pause(self):
        bd = board()
        self.assertTrue(pp.attach(self.lesson({"frame": POINT}), [bd]))
        s = bd["states"][0]
        p = s["practice"][0]
        self.assertEqual((p["id"], p["time"], p["resume"], p["utterance"], p["cue"]),
                         ("page-5_pp-frame", 3.0, 11.0, "page-5_t1.s1.u1", "c2"))
        self.assertEqual(s["utterances"][0]["cues"][1]["practice"], "page-5_pp-frame")
        self.assertRegex(p["items"][0]["content_hash"], r"^sha256:[0-9a-f]{64}$")

    def test_the_hash_ignores_tags_and_version(self):
        a = dict(TEXT)
        b = dict(TEXT, tags={"practises": ["writing.language.grammar"]}, version=2)
        self.assertEqual(pp.content_hash(a), pp.content_hash(b))
        self.assertNotEqual(pp.content_hash(a), pp.content_hash(dict(TEXT, prompt="____ Ms Ann Lee …")))

    def test_refusals(self):
        cases = [
            (board(pause_text="practice: other"), {"frame": POINT}, "names practice point"),
            (board(seconds=1.0), {"frame": POINT}, "fallback's pause"),
            (board(answer=False), {"frame": POINT}, "shows the answer"),
            (board(), {"frame": POINT, "spare": POINT}, "no pause names"),
            (board(), {"frame": dict(POINT, items=[dict(TEXT, item_id="oa-writing-000001")])}, "engine's block"),
            (board(), {"frame": dict(POINT, items=[dict(TEXT, item_id="oa-writing-990001")])}, "engine's block"),
            (board(), {"frame": dict(POINT, items=[dict(TEXT, item_id="oa-writing-900007")])}, "not issued"),
            (board(), {"frame": dict(POINT, items=[dict(TEXT, item_id="oa-writing-900001")])}, "not issued"),
            (board(), {"frame": dict(POINT, items=[dict(TEXT, type="essay")])}, "approved type"),
            (board(), {"frame": dict(POINT, check={"marking": "self", "model": "x", "points": []})}, "interim check"),
            (board(), {"frame": dict(POINT, items=[dict(ERRSPOT, scoring={"error_words": {"first": 2, "last": 8}})])}, "ERRORSPOT-SPAN"),
            (board(), {"frame": dict(POINT, items=[dict(ERRSPOT, feedback=dict(ERRSPOT["feedback"], wrong_words=[
                {"word": 7, "why_wrong": "x", "root_cause": "wrong-referent", "correct": "x"}]))])}, "ERRORSPOT-WRONG-WORD"),
            (board(), {"frame": dict(POINT, items=[dict(SELFCHECK, item_id="oa-writing-900000")])}, "SELFCHECK-POINT"),
            (board(), {"frame": dict(POINT, items=[dict(SELFCHECK, item_id="oa-writing-900000",
                                                        points=SELFCHECK["points"][:1])])}, "2 to 10 points"),
        ]
        for bd, points, why in cases:
            with self.subTest(why=why), self.assertRaises(SystemExit) as e:
                pp.attach(self.lesson(points), [bd])
            self.assertIn(why, str(e.exception))

    def test_a_selfcheck_is_built(self):
        bd = board(pause_text="practice: whole")
        self.assertTrue(pp.attach(self.lesson({"whole": dict(POINT, items=[SELFCHECK])}), [bd]))
        it = bd["states"][0]["practice"][0]["items"][0]
        self.assertEqual(it["type"], "selfcheck")
        # the points' tags stay out of the hash, their text is in it
        tagged = dict(SELFCHECK, points=[dict(x, tags={"practises": ["writing.language.grammar"]}) for x in SELFCHECK["points"]])
        self.assertEqual(pp.content_hash(SELFCHECK), pp.content_hash(tagged))
        self.assertNotEqual(pp.content_hash(SELFCHECK), pp.content_hash(
            dict(SELFCHECK, points=[dict(SELFCHECK["points"][0], text="Other"), SELFCHECK["points"][1]])))

    def test_an_errorspot_is_built(self):
        bd = board()
        self.assertTrue(pp.attach(self.lesson({"frame": dict(POINT, items=[ERRSPOT])}), [bd]))
        self.assertEqual(bd["states"][0]["practice"][0]["items"][0]["type"], "errorspot")

    def test_the_registry_issues_once_and_never_moves(self):
        self.assertEqual(pp.issue(LESSON, "frame", "item"), "oa-writing-900000")       # the same slot, the same id
        with self.assertRaises(SystemExit):                                                # a lesson with no range
            pp.issue("writing-98-other", "frame", "item")
        pp.reserve("grammar-98-other", 950000, 950999)
        self.assertEqual(pp.issue("grammar-98-other", "frame", "item", "grammar"), "oa-grammar-950000")
        self.assertEqual(pp.issue(LESSON, "next", "item"), "oa-writing-900002")       # its own range, not max + 1
        with self.assertRaises(SystemExit):                                                # ranges never overlap
            pp.reserve("writing-97-other", 900500, 901500)
        with self.assertRaises(SystemExit):                                                # nor change
            pp.reserve(LESSON, 900000, 900499)
        self.assertEqual(pp.issued(LESSON), {"oa-writing-900000": "frame", "oa-writing-900001": "whole",
                                             "oa-writing-900002": "next"})
        d = json.loads(pp.REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual([e["id"] for e in d["ids"]], ["oa-writing-900000", "oa-writing-900001", "oa-grammar-950000",
                                                       "oa-writing-900002"])
        d["ids"].append(dict(d["ids"][0], slot="again"))                                  # a number issued twice
        pp.REGISTRY.write_text(json.dumps(d), encoding="utf-8")
        with self.assertRaises(SystemExit):
            pp.issue(LESSON, "frame", "item")

    def test_the_repository_registry(self):
        if self.saved.exists():
            pp.check_registry(json.loads(self.saved.read_text(encoding="utf-8")))

    def test_the_package_check_refuses_fixture_ids(self):
        def bundle(version, item_id):
            return {"format_version": version, "boards": [{"states": [{"id": "s1", "utterances": [],
                    "practice": [{"items": [{"item_id": item_id, "options": [{"option_id": item_id + "-o1"}]}]}]}]}]}
        for version, item_id, codes in (("1.23", "oa-writing-900000", []), ("1.23", "oa-writing-990000", ["LP-FIXTURE"]),
                                        ("1.23", "oa-writing-500000", ["LP-ID-BLOCK"]), ("1.22", "oa-writing-900000", ["LP-PRACTICE"])):
            f = lp.Findings()
            lp.check_practice(bundle(version, item_id), f)
            self.assertEqual(sorted(set(f.codes("error"))), codes, (version, item_id))

    def test_the_format_version(self):
        self.assertEqual(pp.FORMAT_VERSION, "1.23")
        self.assertEqual(blp.format_version("writing-04-x", newer=pp.FORMAT_VERSION), "1.23")
        self.assertEqual(blp.NEWEST_FORMAT_VERSION, "1.23")


if __name__ == "__main__":
    unittest.main()
