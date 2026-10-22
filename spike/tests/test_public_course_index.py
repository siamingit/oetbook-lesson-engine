"""The public course index (docs/adr/038-public-course-index.md): the builder on a
made-up lesson (teaching points, times, layout words, curated anchors, the topic
index), the wording rules for practice boards, the checks CI runs on the committed
index (and that they fail when it is incomplete or edited by hand), and, where the
lesson library is on this machine, that the committed index is up to date with it.

    .venv/Scripts/python -m unittest discover -s spike/tests
"""

import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_public_course_index as ix  # noqa: E402

LIBRARY = Path(r"C:\OET\lessons")


def made_up_library() -> tuple[Path, Path]:
    """One built grammar lesson of two sections, and a curated file for it."""
    root = Path(tempfile.mkdtemp())
    L = root / "lessons" / "grammar-01-made-up"
    for d in ("analysis/screens/page-3", "analysis/screens/page-4", "generated/lesson-player", "source"):
        (L / d).mkdir(parents=True)
    (L / "source" / "video.mp4").write_bytes(b"not a video" * 10)
    blocks = {
        "page-3_k01": {"id": "page-3_k01", "type": "lesson_title", "text": "Made up"},
        "page-4_k01": {"id": "page-4_k01", "type": "table"},
        "page-4_k02": {"id": "page-4_k02", "type": "callout", "kind": "key_rule", "text": "A rule."},
        "page-4_k03": {"id": "page-4_k03", "type": "term_box", "label": "Grammar term", "term": "Present perfect"},
        "page-4_k04": {"id": "page-4_k04", "type": "error_row", "text": "He have gone."},
        "page-4_k05": {"id": "page-4_k05", "type": "gloss", "term": "persistent"},
        "page-4_k06": {"id": "page-4_k06", "type": "term_box", "label": "New word", "term": "undergo"},
    }
    bundle = {
        "format": "oetbook-lesson-bundle", "format_version": "1.12",
        "lesson": {"id": L.name, "title": "Grammar for OET: Made Up", "description": "One line.",
                   "categories": []},
        "sections": [
            {"id": "page-3", "title": "Introduction", "pages": [3], "intro": True, "category": None,
             "start": 0.0, "end": 10.0, "boards": ["page-3_t1"]},
            {"id": "page-4", "title": "Present perfect", "pages": [4], "intro": False, "category": None,
             "start": 10.0, "end": 75.5, "boards": ["page-4_t1"]}],
        "meta": {"total_duration_s": 75.5},
        "blocks": blocks,
        "boards": [
            {"id": "page-3_t1", "section": "page-3", "start": 0.0, "fixed": ["page-3_k01"],
             "states": [{"id": "page-3_t1.s1", "working": [], "reveal": {},
                         "utterances": [{"id": "page-3_t1.s1.u1", "start": 0.5, "provenance": "authored",
                                         "refs": []}]}]},
            {"id": "page-4_t1", "section": "page-4", "start": 10.0, "fixed": ["page-4_k01"],
             "states": [{"id": "page-4_t1.s1", "working": ["page-4_k02", "page-4_k03", "page-4_k04",
                                                           "page-4_k05", "page-4_k06"],
                         "reveal": {"page-4_k02": 30.25, "page-4_k03": 12.0, "page-4_k04": 61.9,
                                    "page-4_k05": 40.0, "page-4_k06": 50.0},
                         "utterances": [{"id": "page-4_t1.s1.u1", "start": 11.0, "provenance": "adapted",
                                         "refs": []},
                                        {"id": "page-4_t1.s1.u2", "start": 31.4, "provenance": "adapted",
                                         "refs": []}]}]}],
    }
    (L / "generated" / "lesson-player" / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    screens = {
        "page-3": {"topics": [{"id": "t1", "title": "Title board", "thoughts": [
            {"purpose": "the lesson title", "blocks": [{"id": "k01"}]}]}]},
        "page-4": {"topics": [{"id": "t1", "title": "Split: the present perfect", "thoughts": [
            {"purpose": "Put the tense table on the board as the fixed layer", "blocks": [{"id": "k01"}]},
            {"purpose": "Row 2: the rule", "blocks": [{"id": "k02"}]},
            {"purpose": "Table: the term", "blocks": [{"id": "k03"}]},
            {"purpose": "a thought taken out of the lesson", "blocks": [{"id": "k99"}]},
            {"purpose": "A wrong sentence", "blocks": [{"id": "k04"}]}]}]},
    }
    for sec, s in screens.items():
        (L / "analysis" / "screens" / sec / "screens.json").write_text(json.dumps(s), encoding="utf-8")
    (L / "analysis" / "sections.json").write_text(json.dumps({"lesson": {}, "added": []}), encoding="utf-8")
    (L / "analysis" / "gates.json").write_text(json.dumps({"final": {"by": "Owner", "on": "2026-10-21 22:01"}}),
                                               encoding="utf-8")
    (L / "analysis" / "preflight.json").write_text(json.dumps({"deck_pages": 5, "video": {"duration_s": 99.0}}),
                                                   encoding="utf-8")
    cur = root / "curated.json"
    cur.write_text(json.dumps({"facts": {"writing-made-up": "A made-up writing fact."}, "lessons": {L.name: {
        "session": "A made-up session.",
        "facts": [{"fact": "writing-made-up", "at": "page-4_t1.s1.u2"}],
        "methods": [{"name": "A method", "text": "Its line.", "at": "page-4_t1"}],
        "continues_in": [], "topics": [{"topic": "the made-up topic", "at": "page-4_k05"}]}}}), encoding="utf-8")
    return root / "lessons", cur


class Build(unittest.TestCase):
    def setUp(self):
        self.lessons, self.cur = made_up_library()
        with mock.patch.object(ix, "CURATED", self.cur):
            self.index = ix.build(self.lessons)
        self.lesson = self.index["lessons"][0]
        self.sec = self.lesson["sections"][1]

    def test_lesson_fields(self):
        e = self.lesson
        self.assertEqual((e["id"], e["course"], e["order"], e["length"], e["status"]),
                         ("grammar-01-made-up", "grammar", 1, "1:15", "approved"))
        self.assertEqual(e["approval"], {"by": "Owner", "on": "2026-10-21 22:01"})
        self.assertEqual(e["source"]["note"], "A made-up session.")
        self.assertEqual(e["source"]["recording_duration_s"], 99.0)
        self.assertEqual(self.index["courses"][0]["lessons"], ["grammar-01-made-up"])

    def test_teaching_points_cleaned_timed_and_in_order(self):
        topic = self.sec["topics"][0]
        self.assertEqual(topic["title"], "the present perfect")
        self.assertEqual([(p["text"], p["start"]) for p in topic["points"]],
                         [("the tense table", "0:10"), ("the term", "0:12"), ("the rule", "0:30"),
                          ("A wrong sentence", "1:01")])

    def test_rules_terms_wrong_sentences_and_vocabulary(self):
        self.assertEqual([(r["kind"], r["text"], r["start"]) for r in self.sec["rules"]],
                         [("rule", "A rule.", "0:30")])
        self.assertEqual([t["term"] for t in self.sec["terms"]], ["Present perfect", "undergo"])
        self.assertEqual([w["text"] for w in self.sec["wrong_examples"]], ["He have gone."])
        self.assertEqual([(v["word"], v["kind"], v["start"]) for v in self.lesson["vocabulary"]],
                         [("persistent", "gloss", "0:40"), ("undergo", "new-word", "0:50")])

    def test_curated_anchors_resolve_to_times(self):
        f = self.lesson["facts"][0]
        self.assertEqual((f["fact"], f["text"], f["utterance"], f["start"]),
                         ("writing-made-up", "A made-up writing fact.", "page-4_t1.s1.u2", "0:31"))
        self.assertEqual(self.lesson["methods"][0]["start"], "0:10")

    def test_topic_index(self):
        keys = {t["key"]: t["entries"][0]["source"] for t in self.index["topic_index"]}
        self.assertEqual(keys, {"present perfect": "section", "the made-up topic": "curated"})

    def test_an_unknown_anchor_stops_the_build(self):
        cur = json.loads(self.cur.read_text(encoding="utf-8"))
        cur["lessons"]["grammar-01-made-up"]["methods"][0]["at"] = "page-9_t1"
        self.cur.write_text(json.dumps(cur), encoding="utf-8")
        with mock.patch.object(ix, "CURATED", self.cur), self.assertRaises(SystemExit):
            ix.build(self.lessons)

    def test_same_inputs_same_bytes(self):
        with mock.patch.object(ix, "CURATED", self.cur):
            self.assertEqual(ix.to_json(ix.build(self.lessons)), ix.to_json(self.index))


class Wording(unittest.TestCase):
    def test_layout_words_go(self):
        self.assertEqual(ix.clean("Table: Row 2: withdrawn"), "withdrawn")
        self.assertEqual(ix.clean("Table: Zoom D: the first heading"), "the first heading")
        self.assertEqual(ix.clean("Fixed layer: the three participle forms"), "the three participle forms")
        self.assertEqual(ix.clean("Show the two continuous passive rows as the fixed layer"),
                         "the two continuous passive rows")
        self.assertEqual(ix.clean("Step 2: read the text"), "Step 2: read the text")

    def test_letters_that_could_give_a_key_away(self):
        self.assertEqual(ix.neutral("why option C is wrong"), "why an option is wrong")
        self.assertEqual(ix.neutral("options A and B are out"), "options are out")
        self.assertEqual(ix.neutral("Text B holds the answer"), "the text holds the answer")
        self.assertEqual(ix.neutral("So B is out"), "So an option is out")

    def test_minutes_and_seconds_round_down(self):
        self.assertEqual((ix.mmss(59.9), ix.mmss(60), ix.mmss(7132.4)), ("0:59", "1:00", "118:52"))


class CommittedIndex(unittest.TestCase):
    """What CI checks, with no lesson data."""

    def copy(self) -> tuple[dict, Path, Path]:
        d = Path(tempfile.mkdtemp())
        return json.loads(ix.JSON_OUT.read_text(encoding="utf-8")), d / "i.json", d / "i.md"

    def write(self, data: dict, j: Path, m: Path) -> None:
        j.write_text(ix.to_json(data), encoding="utf-8")
        m.write_text(ix.markdown(data), encoding="utf-8")

    def test_the_committed_index_verifies(self):
        self.assertEqual(ix.verify(), [])

    def test_markdown_edited_by_hand_fails(self):
        data, j, m = self.copy()
        self.write(data, j, m)
        m.write_text(m.read_text(encoding="utf-8").replace("# Grammar", "# Grammar!", 1), encoding="utf-8")
        self.assertTrue(any("not generated" in e for e in ix.verify(j, m)))

    def test_a_lesson_missing_from_the_index_fails(self):
        data, j, m = self.copy()
        gone = data["lessons"].pop()
        for c in data["courses"]:
            c["lessons"] = [i for i in c["lessons"] if i != gone["id"]]
        for t in data["topic_index"]:
            t["entries"] = [x for x in t["entries"] if x["lesson"] != gone["id"]]
        data["topic_index"] = [t for t in data["topic_index"] if t["entries"]]
        data["totals"] = ix.totals(data)
        self.write(data, j, m)
        errs = ix.verify(j, m)
        self.assertEqual(errs, [f"lesson {gone['id']} has a curated entry but is not in the index"])

    def test_a_field_the_schema_does_not_know_fails(self):
        data, j, m = self.copy()
        bad = copy.deepcopy(data)
        bad["lessons"][0]["narration_text"] = "words"
        self.write(bad, j, m)
        self.assertTrue(any("not in the schema" in e for e in ix.verify(j, m)))

    def test_no_narration_or_board_text_field(self):
        data, _, _ = self.copy()
        self.assertFalse({"narration_text", "board_text"} & set(ix.to_json(data).split('"')))


@unittest.skipUnless(LIBRARY.is_dir() and os.environ.get("LOCALAPPDATA"),
                     "the lesson library is not on this machine (CI): the up-to-date check runs locally")
class UpToDate(unittest.TestCase):
    def test_the_committed_index_matches_the_lesson_data(self):
        built = ix.build(LIBRARY)
        self.assertEqual(ix.to_json(built), ix.JSON_OUT.read_text(encoding="utf-8"),
                         "docs/course-index.json is out of date: run build_public_course_index.py "
                         "C:\\OET\\lessons and commit docs/course-index.*")


if __name__ == "__main__":
    unittest.main()
