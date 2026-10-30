"""Practice points (bundle 1.23, ADR 046): attached to the pauses that name them, with
their items in the site's contract and the fallback in the timeline; a lesson without
analysis/practice.json is untouched."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_lesson_player as blp  # noqa: E402
import practice_points as pp  # noqa: E402

TEXT = {"item_id": "oa-writing-990001", "type": "text", "number": 1, "prompt": "____ Mr Tom Hale …",
        "response": {"max_words": 6, "copy_from_source": False},
        "scoring": {"accepted": ["I am writing to refer", "I'm writing to refer"], "marking_scheme": "oet-typed-form-v1"},
        "feedback": {"key": "A referral.", "wrong_answers": [
            {"answer": "I refer", "why_wrong": "Too short.", "root_cause": "partial", "correct": "I am writing to refer"}]},
        "tags": {"practises": ["writing.purpose.introduction"]}, "version": 1, "status": "active"}
POINT = {"task": "Type the words a referral starts with.",
         "excerpt": {"sample": "invented", "title": "The paper", "rows": [{"label": "Plan:", "lines": ["Refer to the clinic"]}]},
         "items": [TEXT]}


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


class PracticePoints(unittest.TestCase):
    def lesson(self, points):
        d = Path(tempfile.mkdtemp()) / "writing-99-example"
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
            (board(), {"frame": dict(POINT, items=[dict(TEXT, item_id="oa-writing-000001")])}, "fixture block"),
            (board(), {"frame": dict(POINT, items=[dict(TEXT, type="essay")])}, "approved type"),
        ]
        for bd, points, why in cases:
            with self.subTest(why=why), self.assertRaises(SystemExit) as e:
                pp.attach(self.lesson(points), [bd])
            self.assertIn(why, str(e.exception))

    def test_the_format_version(self):
        self.assertEqual(pp.FORMAT_VERSION, "1.23")
        self.assertEqual(blp.format_version("writing-04-x", newer=pp.FORMAT_VERSION), "1.23")
        self.assertEqual(blp.NEWEST_FORMAT_VERSION, "1.23")


if __name__ == "__main__":
    unittest.main()
