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


MARKING = {"key_points": ["the frame: I am writing to refer"],
           "rule": "A referral opens with I am writing to refer.",
           "common_errors": [{"wrong": "the request frame", "why": "The plan says refer."}]}
AI_TEXT = dict(TEXT, scoring=dict(TEXT["scoring"], method="ai"), marking=MARKING, version=2)
AI_SELF = dict(SELFCHECK, scoring={"method": "ai"}, version=2,
               marking={"key_points": ["the frame", "his title and full name: Mr Tom Hale", "his age: a 16-year-old"],
                        "rule": "The opening gives the frame, who the patient is and what you ask.",
                        "common_errors": [{"wrong": "no article before the age", "why": "A countable noun needs a or an."}]})

# matching (ADR 054): the item 900000 with three pairs 900002-900004 (issued for the point in setUp), one distractor
O = [f"oa-writing-900000-o{n}" for n in range(1, 5)]


def pair(n, pid, key, wrong=3, **kw):
    return {"pair_id": f"oa-writing-{pid}", "number": n, "prompt": ["refer", "request", "advise"][n - 1],
            "scoring": {"key_option_id": O[key]},
            "feedback": {"key": "The **verb** and its noun.",
                         "options": {O[wrong]: {"why_wrong": "Not with this verb.", "root_cause": "word-match",
                                                "correct": "the right noun"}}},
            "tags": {"practises": ["writing.language.vocabulary"]}, "status": "active", **kw}


MATCH = {"item_id": "oa-writing-900000", "type": "matching", "numbers": [1, 3],
         "title": "Match each verb with its noun.", "left_heading": "Verb", "right_heading": "Noun",
         "options": [{"option_id": o, "text": t} for o, t in zip(O, ["a patient", "a review", "rest", "a form"])],
         "display_order": [O[2], O[0], O[3], O[1]], "shuffle_allowed": True, "reuse_options": False,
         "pairs": [pair(1, 900002, 1), pair(2, 900003, 2), pair(3, 900004, 0)],
         "tags": {"practises": ["writing.language.vocabulary"]}, "version": 1, "status": "active"}


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
            # AI-assisted marking (contracts 1.14.0): the two fields go together, and no common error is a form
            (board(), {"frame": dict(POINT, items=[dict(TEXT, scoring=dict(TEXT["scoring"], method="ai"))])}, "MARKING-AI"),
            (board(), {"frame": dict(POINT, items=[dict(TEXT, marking=MARKING)])}, "MARKING-AI"),
            (board(), {"frame": dict(POINT, items=[dict(AI_TEXT, marking=dict(MARKING, common_errors=[
                {"wrong": "I'm writing to refer", "why": "x"}]))])}, "accepted form"),
            (board(), {"frame": dict(POINT, items=[dict(AI_TEXT, marking=dict(MARKING, key_points=[]))])}, "key_points"),
            (board(), {"frame": dict(POINT, items=[dict(AI_TEXT, marking=dict(MARKING, common_errors=[
                {"wrong": "x", "why": "y", "fix": "z"}]))])}, "common_errors"),
            (board(), {"frame": dict(POINT, items=[dict(TEXT, scoring=dict(TEXT["scoring"], method="exact"))])}, "scoring.method"),
            (board(pause_text="practice: whole"), {"whole": dict(POINT, items=[dict(SELFCHECK, scoring={"method": "ai"})])},
             "MARKING-AI"),
            (board(pause_text="practice: whole"), {"whole": dict(POINT, items=[dict(AI_SELF, marking=dict(
                AI_SELF["marking"], common_errors=[{"wrong": SELFCHECK["model"], "why": "x"}]))])}, "the model"),
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

    def test_ai_marking_is_built_and_hashed(self):
        """Contracts 1.14.0: `scoring.method: "ai"` and `marking` are carried whole, and are content (a new
        hash, so a new item version); a self-check takes {method: ai} with its marking."""
        bd = board()
        self.assertTrue(pp.attach(self.lesson({"frame": dict(POINT, items=[AI_TEXT])}), [bd]))
        it = bd["states"][0]["practice"][0]["items"][0]
        self.assertEqual((it["scoring"]["method"], it["marking"], it["version"]), ("ai", MARKING, 2))
        self.assertNotEqual(pp.content_hash(TEXT), pp.content_hash(AI_TEXT))
        self.assertNotEqual(pp.content_hash(AI_TEXT), pp.content_hash(dict(AI_TEXT, marking=dict(MARKING, rule="Other."))))
        bd = board(pause_text="practice: whole")
        self.assertTrue(pp.attach(self.lesson({"whole": dict(POINT, items=[AI_SELF])}), [bd]))
        it = bd["states"][0]["practice"][0]["items"][0]
        self.assertEqual((it["scoring"], it["marking"]["key_points"][1]), ({"method": "ai"}, "his title and full name: Mr Tom Hale"))
        self.assertNotEqual(pp.content_hash(SELFCHECK), pp.content_hash(AI_SELF))

    def test_an_errorspot_is_built(self):
        bd = board()
        self.assertTrue(pp.attach(self.lesson({"frame": dict(POINT, items=[ERRSPOT])}), [bd]))
        self.assertEqual(bd["states"][0]["practice"][0]["items"][0]["type"], "errorspot")

    def issue_pairs(self):
        self.assertEqual([pp.issue(LESSON, "frame", f"pair-{n}") for n in (1, 2, 3)],
                         ["oa-writing-900002", "oa-writing-900003", "oa-writing-900004"])

    def test_a_matching_item_is_built(self):
        self.issue_pairs()
        bd = board()
        self.assertTrue(pp.attach(self.lesson({"frame": dict(POINT, items=[MATCH])}), [bd]))
        it = bd["states"][0]["practice"][0]["items"][0]
        self.assertEqual(it["type"], "matching")
        for pr in it["pairs"]:
            self.assertEqual(pr["content_hash"], pp.content_hash({k: v for k, v in pr.items() if k != "content_hash"}))
        # a pair's tags stay out of the hashes, its prompt is in them
        self.assertEqual(pp.hashed(MATCH)["content_hash"], pp.hashed(dict(MATCH, pairs=[
            dict(pr, tags={"practises": ["writing.language.grammar"]}) for pr in MATCH["pairs"]]))["content_hash"])
        self.assertNotEqual(pp.hashed(MATCH)["content_hash"], pp.hashed(dict(MATCH, pairs=[
            dict(MATCH["pairs"][0], prompt="send")] + MATCH["pairs"][1:]))["content_hash"])
        # a withdrawn pair keeps the hash it was withdrawn with, and is not a unit
        stub = {"pair_id": "oa-writing-900004", "status": "withdrawn", "content_hash": "sha256:" + "0" * 64,
                "withdrawal": {"reason_code": "wrong-key", "reason": "x", "date": "2026-11-12", "package_version": 1}}
        w = pp.hashed(dict(MATCH, pairs=MATCH["pairs"][:2] + [stub], options=MATCH["options"]))
        self.assertEqual(w["pairs"][2]["content_hash"], stub["content_hash"])
        self.assertEqual([u["pair_id"] for u in pp._units(w)], ["oa-writing-900002", "oa-writing-900003"])

    def test_matching_refusals(self):
        self.issue_pairs()
        P = MATCH["pairs"]
        three = dict(MATCH, options=MATCH["options"][:3], display_order=[O[2], O[0], O[1]],
                     pairs=[pair(1, 900002, 1, wrong=0), pair(2, 900003, 2, wrong=0), pair(3, 900004, 0, wrong=1)])
        ten = [{"option_id": f"oa-writing-900000-o{n}", "text": f"t{n}"} for n in range(1, 11)]
        cases = [
            (dict(MATCH, pairs=P[:1]), "2 to 8 pairs"),
            (dict(MATCH, options=ten, display_order=[o["option_id"] for o in ten][::-1]), "3 to 9 options"),
            (dict(MATCH, pairs=[P[0], pair(2, 900003, 1), P[2]]), "REUSE-OPTIONS"),            # o2 the key of two
            (three, "REUSE-OPTIONS"),                                                          # no distractor
            (dict(MATCH, pairs=[pair(1, 900002, 0), pair(2, 900003, 1), pair(3, 900004, 2)]), "KEY-LEAK"),
            (dict(MATCH, pairs=[dict(P[0], feedback={"key": "x", "options": {}})] + P[1:]), "FEEDBACK"),
            (dict(MATCH, pairs=[pair(1, 900002, 1, wrong=1)] + P[1:]), "feedback on the key"),
            (dict(MATCH, display_order=O[:3]), "permutation"),
            (dict(MATCH, pairs=P[:2] + [dict(P[2], pair_id="oa-writing-900009")]), "not issued"),
            (dict(MATCH, pairs=[dict(P[0], tags={})] + P[1:]), "practises"),
        ]
        for item, why in cases:
            with self.subTest(why=why):
                with self.assertRaises(SystemExit) as e:
                    pp.attach(self.lesson({"frame": dict(POINT, items=[item])}), [board()])
                self.assertIn(why, str(e.exception))
        # with reuse_options, one option may be the key of two pairs and no distractor is needed
        bd = board()
        self.assertTrue(pp.attach(self.lesson({"frame": dict(POINT, items=[dict(
            MATCH, reuse_options=True, pairs=[P[0], pair(2, 900003, 1), P[2]])])}), [bd]))

    def test_the_package_check_walks_pair_ids(self):
        f = lp.Findings()
        lp.check_practice({"format_version": "1.23", "boards": [{"states": [{"id": "s1", "utterances": [], "practice": [
            {"items": [dict(MATCH, pairs=[dict(MATCH["pairs"][0], pair_id="oa-writing-990002")])]}]}]}]}, f)
        self.assertEqual(sorted(set(f.codes("error"))), ["LP-FIXTURE"])

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


class MatchingContract(unittest.TestCase):
    """Against the pinned contracts (1.22.0): the engine hashes the golden matching item (an exercises
    item) as the factory does, and the item the engine builds is a practice item of the bundle schema."""

    @classmethod
    def setUpClass(cls):
        import os
        try:
            cls.c = lp.load(fetch_missing=False)
        except SystemExit:
            if os.environ.get("OETBOOK_CONTRACTS_OPTIONAL") == "1":
                raise unittest.SkipTest("skipped: contracts not available in CI")
            raise

    def golden(self):
        g = json.loads(self.c.files["examples/exercise-types/golden.json"])

        def walk(o):
            if isinstance(o, dict):
                if o.get("type") == "matching":
                    yield o
                for v in o.values():
                    yield from walk(v)
            elif isinstance(o, list):
                for v in o:
                    yield from walk(v)
        return next(walk(g))

    def test_the_golden_hashes(self):
        g = self.golden()
        h = pp.hashed(g)
        self.assertEqual(h["content_hash"], g["content_hash"])
        self.assertEqual([x["content_hash"] for x in h["pairs"]], [x["content_hash"] for x in g["pairs"]])

    def test_the_built_item_is_a_practice_item(self):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        schemas = [json.loads(b) for n, b in self.c.files.items() if n.startswith("schemas/") and n.endswith(".json")]
        reg = Registry().with_resources((x["$id"], Resource.from_contents(x)) for x in schemas)
        v = Draft202012Validator({"$ref": "https://oetacademy.uk/contracts/v1/lesson-bundle.schema.json#/$defs/practiceItem"},
                                 registry=reg)
        self.assertEqual([e.message for e in v.iter_errors(pp.hashed(MATCH))], [])


if __name__ == "__main__":
    unittest.main()


class PracticePointNotes(unittest.TestCase):
    """ADR 046 amendment (3): a practice point's task line and answer (added blocks marked
    `practice_point`) are not counted against the board's note limits."""

    def board(self, marked: bool):
        import write_screens as ws
        notes = [{**ws.BLOCK_DEFAULTS, "type": "plain", "text": f"Note {n}."} for n in range(4)]
        extra = [{**ws.BLOCK_DEFAULTS, "type": "plain", "text": t, "added": True,
                  **({"practice_point": "key"} if marked else {})} for t in ("Your turn.", "Answer.")]
        topics = [{"title": "T", "thoughts": [{"purpose": "p", "blocks": notes},
                                               {"purpose": "q", "blocks": extra}]}]
        blocks = ws.assign_ids(topics)
        return ws, blocks, ws.lay_out(topics, blocks, "S")

    def test_marked_blocks_are_not_counted(self):
        ws, blocks, boards = self.board(marked=True)
        self.assertEqual(ws.counted_notes(list(blocks), blocks), ["k01", "k02", "k03", "k04"])
        self.assertEqual(len(boards[0]["states"]), 1)
        self.assertEqual(boards[0]["states"][0]["working"], ["k01", "k02", "k03", "k04", "k05", "k06"])

    def test_unmarked_blocks_are_counted(self):
        ws, blocks, boards = self.board(marked=False)
        self.assertEqual(len(ws.counted_notes(list(blocks), blocks)), 6)
        self.assertEqual(len(boards[0]["states"]), 2)
