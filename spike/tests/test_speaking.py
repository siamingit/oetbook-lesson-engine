"""The Speaking course's engine (ADR 053, ADR 054): a narration line's speaker and feeling, the speaking
practice items behind speaking_items.py (speak_repeat in the site's contracts 1.22.0, the others still the
draft's), their recordings (the slow take stretched from the normal one), and the site's form of a Speaking
lesson's bundle: a speak_repeat point carried, the draft's types left out of a --draft and refused in a final
release. A line with no speaker is the teacher's, so nothing built before changes."""

import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lesson_package as lp  # noqa: E402
import practice_points as pp  # noqa: E402
import publish_lesson  # noqa: E402
import speaking_items as si  # noqa: E402
import style_c  # noqa: E402
import synthesize_narration as sn  # noqa: E402
import synthesize_speaking as ss  # noqa: E402
import voices  # noqa: E402
import write_narration as wn  # noqa: E402
from synthesize_audio import MODEL_ID  # noqa: E402

LESSON = "speaking-99-example"
REPEAT = {"item_id": "oa-speaking-970000", "type": "speak_repeat", "profession": "nursing",
          "focus": "Checking the patient's name", "shown": "Can I check your full name, please?",
          "spoken": "Can I check your full name, please?", "chunks": ["Can I check", "your full name, please"],
          "pass_score": 70}
RESPOND = {"item_id": "oa-speaking-970001", "type": "speak_respond", "profession": "nursing",
           "prompt": "The patient is worried. Show that you understand.", "patient_line": "I'm really scared about this.",
           "patient_speaker": "patient_f", "patient_emotion": "worried",
           "key_points": ["Name the feeling", "Offer help"], "prepare_s": 10, "max_s": 30,
           "model_answer": "I can see this is worrying for you. Let's talk it through together."}
ROLEPLAY = {"item_id": "oa-speaking-970002", "type": "roleplay", "profession": "nursing", "title": "A sore ankle",
            "setting": "A community clinic", "patient_speaker": "patient_m",
            "candidate": {"role": "Nurse", "background": "Mr Ben Cole hurt his ankle playing football.",
                          "tasks": ["Find out how it happened", "Explain rest and ice", "Reassure him"]},
            "patient": {"name": "Ben Cole", "role": "Patient", "persona": "A keen footballer, 24.",
                        "emotion": "impatient", "opening": "I need to play on Saturday.",
                        "hidden": ["He has a match on Saturday"], "concern": "Missing the match."},
            "prepare_s": 180, "talk_s": 300}

TAGGED = dict(REPEAT, tags={"practises": ["speaking.language.intelligibility"]})
EXCERPT = {"sample": LESSON, "pin": "authored for this lesson", "title": "Say it",
           "rows": [{"label": "", "lines": ["Can I check your full name, please?"]}]}


def practice_item_validator():
    """The bundle schema's practiceItem of the pinned contracts, or a skip where CI has none."""
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    try:
        c = lp.load(fetch_missing=False)
    except SystemExit:
        if os.environ.get("OETBOOK_CONTRACTS_OPTIONAL") == "1":
            raise unittest.SkipTest("skipped: contracts not available in CI")
        raise
    schemas = [json.loads(b) for n, b in c.files.items() if n.startswith("schemas/") and n.endswith(".json")]
    reg = Registry().with_resources((x["$id"], Resource.from_contents(x)) for x in schemas)
    return Draft202012Validator(
        {"$ref": "https://oetacademy.uk/contracts/v1/lesson-bundle.schema.json#/$defs/practiceItem"}, registry=reg)


def utt(uid, cues, **kw):
    return {"id": uid, "cues": cues, **kw}


def board(key="repeat-name"):
    return {"id": "page-1_t1", "section": "page-1", "states": [
        {"id": "page-1_t1.s1", "utterances": [
            utt("page-1_t1.s1.u1", [{"id": "c1", "type": "reveal", "time": 1.0},
                                    {"id": "c2", "type": "pause", "text": "practice: " + key, "seconds": 6.0,
                                     "time": 3.0, "time_end": 9.0}]),
            utt("page-1_t1.s1.u2", [{"id": "c1", "type": "reveal", "time": 10.0}])]}]}


def lesson_dir(name, lesson_type=None, points=None):
    d = Path(tempfile.mkdtemp()) / name
    (d / "analysis").mkdir(parents=True)
    if lesson_type:
        (d / "analysis" / "sections.json").write_text(json.dumps({"lesson": {"type": lesson_type}}), encoding="utf-8")
    if points is not None:
        (d / "analysis" / "practice.json").write_text(json.dumps(
            {"format": "oetbook-practice-points", "version": 1, "points": points}), encoding="utf-8")
    return d


class Voices(unittest.TestCase):
    def test_a_line_without_a_speaker_is_the_teachers(self):
        self.assertIs(voices.voice_for(None, voices.RUPERT), voices.RUPERT)
        self.assertIs(voices.voice_for("teacher", voices.RUPERT), voices.RUPERT)

    def test_the_patients(self):
        g, a = voices.voice_for("patient_f", voices.RUPERT), voices.voice_for("patient_m", voices.RUPERT)
        self.assertEqual((g["name"], g["id"], g["speed"]), ("gemma", "62ae83ad-4f6a-430b-af41-a9bede9286ca", 0.8))
        self.assertEqual((a["name"], a["id"], a["speed"]), ("archie", "ef191366-f52f-447a-a398-ed8c0f2943a1", 0.8))
        with self.assertRaises(ValueError):
            voices.voice_for("doctor", voices.RUPERT)

    def test_feelings(self):
        self.assertIsNone(voices.emotion_for(None))
        self.assertEqual((voices.emotion_for("worried"), voices.emotion_for("upset")), ("anxious", "frustrated"))
        with self.assertRaises(ValueError):
            voices.emotion_for("happy")

    def test_the_cache_key_of_a_teachers_line_is_unchanged(self):
        # the key every clip made before was cached under (ADR 027, before ADR 053)
        old = lambda text, speed, salt, d, v: hashlib.sha256(  # noqa: E731
            (f"{text}|{v['id']}|{MODEL_ID}|{speed:.3f}|{d}|{salt}"
             + (f"|pause{v['sentence_pause_s']:.2f}" if v["sentence_pause_s"] else "")).encode()).hexdigest()[:12]
        self.assertEqual(sn.cache_key("Hello there.", 1.0, "s", "d"), old("Hello there.", 1.0, "s", "d", voices.RUPERT))
        g = voices.GEMMA
        self.assertEqual(sn.cache_key("Hi.", 0.8, "s", "d", g), old("Hi.", 0.8, "s", "d", g))
        self.assertNotEqual(sn.cache_key("Hi.", 0.8, "s", "d", g, "anxious"), sn.cache_key("Hi.", 0.8, "s", "d", g))


class Narration(unittest.TestCase):
    def bds(self, **kw):
        return [{"id": "page-1_t1", "states": [{"utterances": [{"id": "u1", **kw}, {"id": "u2"}]}]}]

    def test_a_speaker_only_in_a_speaking_lesson(self):
        sp, wr = lesson_dir(LESSON, "speaking"), lesson_dir("writing-99-example", "writing")
        self.assertEqual(wn.speaker_findings(sp, self.bds(speaker="patient_f", emotion="worried")), [])
        self.assertEqual(wn.speaker_findings(wr, self.bds()), [])
        self.assertEqual(len(wn.speaker_findings(wr, self.bds(speaker="patient_f"))), 1)
        self.assertEqual(len(wn.speaker_findings(sp, self.bds(speaker="nurse"))), 1)
        self.assertEqual(len(wn.speaker_findings(sp, self.bds(speaker="patient_m", emotion="cross"))), 1)

    def test_the_schema_adds_the_fields_only_for_speaking(self):
        sp = wn.schema_for(lesson_dir(LESSON, "speaking"))
        self.assertIs(wn.schema_for(lesson_dir("writing-99-example", "writing")), wn.SCHEMA)
        self.assertIn("speaker", json.dumps(sp))


class Items(unittest.TestCase):
    def test_each_type_passes_the_draft_contract(self):
        for it in (REPEAT, RESPOND, ROLEPLAY):
            si.check(it, it["type"])
            doc = si.contract_doc([si.to_contract(it)])
            self.assertEqual(si.contract_findings(doc), [], it["type"])
        self.assertEqual(si.to_contract(REPEAT)["id"], "oa-speak-970000")
        self.assertEqual(si.to_contract(RESPOND)["patient_voice"], "gb-f-gemma")
        self.assertEqual(si.to_contract(ROLEPLAY)["patient"]["voice"], "gb-m-archie")
        for it in (REPEAT, RESPOND, ROLEPLAY):
            self.assertFalse(si.ENGINE_ONLY & set(si.to_contract(it)), it["type"])

    def test_refusals(self):
        bad = [dict(REPEAT, chunks=["Can I check", "your name"]),           # RP-SPEAK-CHUNKS
               dict(REPEAT, spoken="Take 2 tablets.", shown="Take 2 tablets.", chunks=["Take 2 tablets"]),
               {k: v for k, v in RESPOND.items() if k != "model_answer"},
               dict(RESPOND, patient_speaker="nurse"),
               dict(ROLEPLAY, patient_emotion="worried"),
               dict(REPEAT, audio={}),
               dict(REPEAT, item_id="oa-writing-970000"),
               dict(ROLEPLAY, patient=dict(ROLEPLAY["patient"], hidden=[]))]
        for n, it in enumerate(bad):
            with self.assertRaises(SystemExit, msg=n):
                si.check(it, str(n))

    def test_the_player_never_gets_the_patients_card(self):
        v = si.browser_view(ROLEPLAY, None)
        self.assertNotIn("patient", v)
        self.assertNotIn("Saturday", json.dumps(v))
        self.assertNotIn("audio", si.browser_view(REPEAT, None))
        self.assertEqual(si.browser_view(REPEAT, {"normal": "a.wav", "slow": "b.wav", "x": "c"})["audio"],
                         {"normal": "a.wav", "slow": "b.wav"})

    def test_the_recordings_each_item_needs(self):
        lesson = lesson_dir(LESSON, "speaking", {"repeat-name": {"task": "t", "excerpt": None, "items": [REPEAT]},
                                                 "feel": {"task": "t", "excerpt": None, "items": [RESPOND, ROLEPLAY]}})
        got = {(r["item"], r["role"]): (r["voice"]["name"], r["speed"], r["emotion"]) for r in ss.plan(lesson, voices.RUPERT)}
        self.assertEqual(got, {("oa-speaking-970000", "normal"): ("rupert", 1.0, None),
                               ("oa-speaking-970000", "slow"): ("rupert", 1.0, None),
                               ("oa-speaking-970001", "patient"): ("gemma", 0.8, "anxious"),
                               ("oa-speaking-970001", "model"): ("rupert", 1.0, None)})
        # the slow take is the normal one stretched (ADR 054), never a voice of its own
        slow = [r for r in ss.plan(lesson, voices.RUPERT) if r["role"] == "slow"]
        self.assertEqual([r.get("from") for r in slow], ["oa-speaking-970000.normal.wav"])


class Release(unittest.TestCase):
    """A speak_repeat in the released contract's shape (contracts 1.22.0)."""

    def test_the_released_shape(self):
        c = si.release_item(TAGGED, 1, 1)
        self.assertEqual(list(c), ["item_id", "type", "number", "focus", "shown", "spoken", "chunks", "audio",
                                   "scoring", "tags", "version", "status", "content_hash"])
        self.assertEqual(c["audio"], {"normal": "audio/speak-970000-normal.m4a", "slow": "audio/speak-970000-slow.m4a"})
        self.assertEqual(c["tags"]["facets"]["profession"], ["nursing"])
        self.assertNotIn("pass_score", c)
        self.assertNotIn("profession", c)
        self.assertEqual(c["content_hash"], pp.content_hash({k: v for k, v in c.items() if k != "content_hash"}))
        self.assertTrue(si.is_contract_form(c))
        self.assertFalse(si.is_contract_form(TAGGED))
        self.assertEqual(TAGGED.get("tags"), {"practises": ["speaking.language.intelligibility"]})   # not changed

    def test_refusals(self):
        cases = [(REPEAT, "tags.practises"),
                 (RESPOND, "not in the site's contracts"),
                 (dict(TAGGED, shown="Can I check your name?"), "RP-SHOWN"),
                 (dict(TAGGED, chunks=["Can I check", "your name"]), "RP-SPEAK-CHUNKS"),
                 (dict(TAGGED, spoken="Take 2 tablets.", shown="Take 2 tablets.", chunks=["Take 2 tablets"]),
                  "RP-SPEAK-NUMBERS")]
        for it, why in cases:
            with self.subTest(why=why):
                with self.assertRaises(SystemExit) as e:
                    si.release_item(it)
                self.assertIn(why, str(e.exception))

    def test_it_is_a_practice_item_of_the_pinned_contracts(self):
        v = practice_item_validator()
        self.assertEqual([e.message for e in v.iter_errors(si.release_item(TAGGED))], [])


class Attach(unittest.TestCase):
    def setUp(self):
        self.saved = pp.REGISTRY
        pp.REGISTRY = Path(tempfile.mkdtemp()) / "ids.json"
        pp.reserve(LESSON, 970000, 970999)
        self.assertEqual(pp.issue(LESSON, "repeat-name", "item", "speaking"), "oa-speaking-970000")

    def tearDown(self):
        pp.REGISTRY = self.saved

    def test_a_speaking_point_is_attached_as_the_learners_view(self):
        L = lesson_dir(LESSON, "speaking", {"repeat-name": {"task": "Say it.", "excerpt": None, "items": [REPEAT]}})
        bd = board()
        self.assertTrue(pp.attach(L, [bd]))
        p = bd["states"][0]["practice"][0]
        v = p["items"][0]
        self.assertNotIn("contract_id", v)          # a speak_repeat keeps its own id (contracts 1.22.0)
        self.assertEqual((v["item_id"], v["shown"], v["chunks"]), (REPEAT["item_id"], REPEAT["shown"], REPEAT["chunks"]))
        self.assertNotIn("content_hash", v)
        self.assertTrue(pp.has_speaking([bd]))

    def test_speaking_items_only_in_a_speaking_lesson_and_alone(self):
        with self.assertRaises(SystemExit):
            pp.attach(lesson_dir(LESSON, "writing", {"repeat-name": {"task": "t", "excerpt": None, "items": [REPEAT]}}),
                      [board()])
        other = {"item_id": "oa-speaking-970001", "type": "choice"}
        with self.assertRaises(SystemExit):
            pp.attach(lesson_dir(LESSON, "speaking", {"repeat-name": {"task": "t", "excerpt": None,
                                                                      "items": [REPEAT, other]}}), [board()])

    def test_an_id_the_registry_did_not_issue_is_refused(self):
        with self.assertRaises(SystemExit):
            pp.attach(lesson_dir(LESSON, "speaking", {"repeat-name": {"task": "t", "excerpt": None,
                                                                      "items": [dict(REPEAT, item_id="oa-speaking-970500")]}}),
                      [board()])


class Publish(unittest.TestCase):
    def bundle(self):
        bd = board()
        bd["states"][0]["utterances"][1].update(speaker="patient_f", emotion="worried")
        bd["states"][0]["practice"] = [{"id": "page-1_pp-x", "items": [si.browser_view(REPEAT, None)]}]
        bd["states"][0]["utterances"][0]["cues"][1]["practice"] = "page-1_pp-x"
        return {"format_version": "1.24", "lesson": {"id": LESSON}, "meta": {}, "boards": [bd], "sections": []}

    def test_speaking_units_are_found_and_stubbed(self):
        b = self.bundle()
        self.assertEqual(publish_lesson.speaking_units(b), ["format 1.24", "page-1_t1.s1.u2", "page-1_pp-x"])
        before = copy.deepcopy(b)
        s = publish_lesson.stub_speaking(b)
        self.assertEqual(b, before)
        self.assertEqual(publish_lesson.speaking_units(s), [])
        self.assertNotIn("practice", s["boards"][0]["states"][0]["utterances"][0]["cues"][1])
        self.assertEqual(s["format_version"], "1.23")

    def site_bundle(self, respond=True, excerpt=EXCERPT, repeat_items=None):
        """A bundle with a speak_repeat point (and a speak_respond point) and the lesson behind it."""
        b = self.bundle()
        st = b["boards"][0]["states"][0]
        st["practice"][0]["excerpt"] = excerpt
        if repeat_items is not None:
            st["practice"][0]["items"] = repeat_items
        points = {"x": {"task": "Say it.", "excerpt": excerpt, "items": [TAGGED]}}
        if respond:
            st["practice"].append({"id": "page-1_pp-feel", "excerpt": None, "items": [si.browser_view(RESPOND, None)]})
            st["utterances"][1]["cues"].append({"id": "c2", "type": "pause", "text": "practice: feel", "seconds": 6.0,
                                                "time": 11.0, "time_end": 17.0, "practice": "page-1_pp-feel"})
            points["feel"] = {"task": "Answer her.", "excerpt": None, "items": [RESPOND]}
        return lesson_dir(LESSON, "speaking", points), b

    def test_the_site_form(self):
        L, b = self.site_bundle()
        self.assertTrue(publish_lesson.is_speaking_bundle(b))
        before = copy.deepcopy(b)
        s, left = publish_lesson.site_form(L, b)
        self.assertEqual(b, before)
        self.assertEqual(s["format_version"], "1.23")
        self.assertNotIn("speaker", json.dumps(s))
        self.assertEqual(publish_lesson.speaking_units(s), [])
        st = s["boards"][0]["states"][0]
        self.assertEqual([p["id"] for p in st["practice"]], ["page-1_pp-x"])
        self.assertEqual(st["practice"][0]["items"], [si.release_item(TAGGED)])
        self.assertEqual(left, [{"point": "page-1_pp-feel", "key": "feel", "types": ["speak_respond"],
                                 "items": ["oa-speaking-970001"]}])
        self.assertNotIn("practice", st["utterances"][1]["cues"][1])        # its pause is a plain pause
        self.assertEqual(st["utterances"][0]["cues"][1]["practice"], "page-1_pp-x")
        self.assertEqual(publish_lesson.speak_repeat_items(s), [si.release_item(TAGGED)])
        f = lp.Findings()
        lp.check_practice(s, f)
        self.assertEqual(f.codes("error"), [])

    def test_the_site_form_refusals(self):
        for kw, why in ((dict(excerpt=None), "no excerpt"),
                        (dict(repeat_items=[si.browser_view(REPEAT, None)] * 2), "LP-PRACTICE-ITEM")):
            with self.subTest(why=why):
                L, b = self.site_bundle(respond=False, **kw)
                with self.assertRaises(publish_lesson.Refused) as e:
                    publish_lesson.site_form(L, b)
                self.assertIn(why, str(e.exception))

    def test_a_final_release_carries_every_point(self):
        L, b = self.site_bundle()
        (L / "generated" / "lesson-player").mkdir(parents=True)
        (L / "generated" / "lesson-player" / "bundle.json").write_text(json.dumps(b), encoding="utf-8")
        with self.assertRaises(publish_lesson.Refused) as e:
            publish_lesson.build(L, None, log=lambda *a: None, draft=False)
        self.assertIn("only a --draft", str(e.exception))

    def test_the_package_check_of_a_speak_repeat(self):
        good = si.release_item(TAGGED)
        cases = [([good, good], "LP-PRACTICE-ITEM"),
                 ([dict(good, chunks=["Can I check", "your name"])], "LP-SPEAK-CHUNKS"),
                 ([dict(good, spoken="Take 2 tablets.", shown="Take 2 tablets.", chunks=["Take 2 tablets"])],
                  "LP-SPEAK-NUMBERS")]
        for items, code in cases:
            with self.subTest(code=code):
                f = lp.Findings()
                lp.check_practice({"format_version": "1.23", "boards": [{"states": [{"id": "s1", "utterances": [],
                                   "practice": [{"id": "p", "items": items}]}]}]}, f)
                self.assertIn(code, f.codes("error"))


class Dialogue(unittest.TestCase):
    def test_whose_turn(self):
        for who, side in (("Patient", "patient"), ("Mrs Patel", "patient"), ("Her son", "you"), ("Son", "patient"),
                          ("Nurse", "you"), ("You", "you"), ("Dr Khan", "you")):
            self.assertEqual(style_c.dialogue_who(who), side, who)

    def test_the_learners_turn_is_a_dashed_bubble(self):
        html = ("<div class=\"blk tbl\"><table><thead><tr><th>Who</th><th>Says</th></tr></thead><tbody>"
                "<tr><td>Patient</td><td>I feel dizzy.</td></tr><tr><td>Nurse</td><td></td></tr></tbody></table></div>")
        b = {"type": "table", "header": ["Who", "Says"], "rows": [["Patient", "I feel dizzy."], ["Nurse", ""]], "html": html}
        out = style_c.layout_html(b, html, None, "dialogue")
        self.assertIn('<tr data-who="patient">', out)
        self.assertIn('<tr data-who="you"><td>Nurse</td><td data-dash=""></td>', out)
        self.assertEqual(style_c._text(out), style_c._text(html))



class StubFindingsTest(unittest.TestCase):
    """ADR 053: the stub for the site-player check sets aside the two tag errors, and only them."""

    def test_only_the_tag_errors_become_warnings(self):
        import lesson_package as lp
        f = lp.Findings()
        f.error("LP-TEACHES-NOT-ALLOWED", "sections[0]", "not on the tag list", "speaking.start")
        f.error("LP-TEACHES-NOT-ALLOWED", "sections[0]", "not on the tag list", "speaking.close")
        f.error("LP-TEACHES-EMPTY", "sections[1]", "no tags")
        f.error("LP-AUDIO-MISSING", "boards[0]", "no audio")
        f.warning("LP-SOMETHING", "boards[1]", "a warning")
        logged = []
        out = publish_lesson.stub_findings(f, logged.append)
        self.assertEqual(out.codes("error"), ["LP-AUDIO-MISSING"])
        self.assertEqual(out.codes("warning"), ["LP-SOMETHING", "LP-TEACHES-EMPTY", "LP-TEACHES-NOT-ALLOWED"])
        moved = next(i for i in out.items if i["code"] == "LP-TEACHES-NOT-ALLOWED")
        self.assertEqual((moved["count"], moved["examples"]), (2, ["speaking.start", "speaking.close"]))
        self.assertEqual(len(logged), 2)
        # the lesson's own findings are untouched: a real package still fails them
        self.assertEqual(f.codes("error"), ["LP-AUDIO-MISSING", "LP-TEACHES-EMPTY", "LP-TEACHES-NOT-ALLOWED"])


if __name__ == "__main__":
    unittest.main()
