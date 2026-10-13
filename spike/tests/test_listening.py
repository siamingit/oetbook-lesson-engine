"""Listening lessons (docs/adr/029-listening-lessons.md; bundle 1.18): the lesson
type and its features, the practice set's transcripts, note forms and audio
spans, the Listening rule module, the play cue in the timeline, and the
practice-set loader on the three pinned Listening sets (only where the local
release copy exists: it is private, so CI runs the made-up set alone).

    .venv/Scripts/python -m unittest discover -s spike/tests
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_board_timeline as bt   # noqa: E402
import build_lesson_player as blp   # noqa: E402
import lesson_type                  # noqa: E402
import listening_rule               # noqa: E402
import practice_set as P            # noqa: E402
import write_narration as wn        # noqa: E402
import write_screens as ws          # noqa: E402


def lesson(name: str, ltype: str | None = None, ps: dict | None = None) -> Path:
    L = Path(tempfile.mkdtemp()) / name
    (L / "analysis").mkdir(parents=True)
    if ltype is not None:
        (L / "analysis" / "sections.json").write_text(json.dumps({"lesson": {"title": "x", "type": ltype}}),
                                                      encoding="utf-8")
    if ps is not None:
        (L / "analysis" / "practice_set.json").write_text(json.dumps(ps), encoding="utf-8")
    return L


# A made-up Listening set: one extract (a turn, a turn, then a further paragraph
# of the second speaker's turn), its gap-fill item, and a 3-option item
SEGMENTS = [{"kind": "silence", "start_s": 0, "end_s": 0.25}, {"kind": "announcement", "start_s": 0.25, "end_s": 8.0},
            {"kind": "reading-time", "start_s": 8.0, "end_s": 23.3}, {"kind": "start-tone", "start_s": 23.3, "end_s": 24.0},
            {"kind": "extract", "start_s": 25.0, "end_s": 60.0}]
STIM = {"stimulus_id": "oa-set-lx-0001-e1", "type": "audio-extract", "label": "Extract 1",
        "speakers": [{"label": "Nurse"}, {"label": "Mr Plon"}],
        "transcript": {"format": "oa-transcript-v1",
                       "text": "Nurse: Morning, how is the zibble today?\nMr Plon: Sore since Tuesday.\n"
                               "It wakes me at night."},
        "audio": {"path": "audio/x/e1.mp3", "sha256": "0" * 64, "duration_s": 60.25, "segments": SEGMENTS},
        "reading_time_s": 15.3, "admin": {"turn_starts_s": [25.0, 31.5]}}
GAPFILL = {"item_id": "oa-listening-990001", "type": "gapfill", "numbers": [1, 2], "stimulus_ids": [STIM["stimulus_id"]],
           "title": "Patient notes", "gaps": [
               {"gap_id": "g1", "number": 1, "heading": "Pain", "prompt": "started on ____",
                "scoring": {"accepted": ["Tuesday"]}},
               {"gap_id": "g2", "number": 2, "heading": "Sleep", "prompt": "____ at night",
                "scoring": {"accepted": ["wakes him", "wakes"]}}]}
CHOICE = {"item_id": "oa-listening-990025", "number": 25, "type": "choice", "stimulus_ids": [STIM["stimulus_id"]],
          "stem": "What is the problem?", "options": [{"option_id": "o1", "text": "pain"}, {"option_id": "o2", "text": "cough"},
                                                      {"option_id": "o3", "text": "fever"}],
          "scoring": {"key_option_id": "o1"}}
SET = {"set_id": "oa-set-lx-0001", "release": {"file": "x", "package_id": "p", "package_version": 1},
       "parts": [{"code": "LA", "stimuli": [STIM], "items": [GAPFILL]},
                 {"code": "LB", "stimuli": [], "items": [CHOICE]}],
       "teach_pages": [5]}


class LessonType(unittest.TestCase):
    def test_from_the_config(self):
        self.assertEqual(lesson_type.of(lesson("reading-09-x", "listening")), "listening")

    def test_a_lesson_built_before_the_field_keeps_its_id_type(self):
        for name, t in (("reading-02-part-a", "reading"), ("grammar-01-verb-tenses", "grammar"),
                        ("vocabulary-01-word-forms", "vocabulary"), ("listening-01-overview", "listening")):
            self.assertEqual(lesson_type.of(lesson(name)), t)

    def test_features_by_type_not_by_id(self):
        L = lesson("reading-09-x", "listening")
        self.assertTrue(lesson_type.has(L, "exam_audio"))
        self.assertFalse(lesson_type.has(lesson("reading-02-part-a"), "exam_audio"))
        self.assertTrue(lesson_type.has(lesson("reading-02-part-a"), "practice_set"))
        self.assertFalse(lesson_type.has(lesson("grammar-01-x"), "practice_set"))
        self.assertTrue(listening_rule.is_listening(L))

    def test_reading_and_listening_features_differ_only_by_listening_additions(self):
        r, l = lesson_type.FEATURES["reading"], lesson_type.FEATURES["listening"]
        self.assertTrue(r <= l)
        self.assertEqual(l - r, {"exam_audio", "reading_time", "exam_numbers", "source_terms"})


class ListeningSet(unittest.TestCase):
    def test_transcript_rows_are_the_released_lines(self):
        parts = P.transcript_parts(STIM)
        self.assertEqual([p["kind"] for p in parts], ["turn", "turn", "para"])
        self.assertEqual(parts[1]["speaker"], "Mr Plon")
        b = P.transcript_block(STIM)
        self.assertEqual([r[0] for r in b["rows"]], STIM["transcript"]["text"].split("\n"))
        self.assertEqual(b["doc"]["text_type"], "transcript")

    def test_row_times_from_turns(self):
        self.assertEqual(P.row_times(SET, STIM["stimulus_id"]), [25.0, 31.5, None])

    def test_the_note_form(self):
        f = P.form_block(SET, GAPFILL)
        self.assertEqual([r[0] for r in f["rows"]], ["Pain", "started on Tuesday", "Sleep", "wakes him at night"])
        self.assertEqual([p["kind"] for p in f["doc"]["parts"]], ["heading", "num", "heading", "num"])
        self.assertEqual([p["mark"] for p in f["doc"]["parts"] if p["kind"] == "num"], ["1", "2"])
        for ty in f["typed"]:
            self.assertEqual(f["rows"][ty["row"]][0][ty["start"]:ty["start"] + len(ty["text"])], ty["text"])
        self.assertEqual(f["doc"]["text_type"], "form")
        self.assertIn("key: Tuesday", P.form_for_prompt(SET, GAPFILL))

    def test_spans(self):
        self.assertEqual((P.exam_span(SET, STIM["stimulus_id"], "exam")["clip_in"],
                          P.exam_span(SET, STIM["stimulus_id"], "exam")["clip_out"]), (0.25, 60.0))
        self.assertEqual(P.exam_span(SET, STIM["stimulus_id"], "extract")["clip_in"], 25.0)
        s = P.exam_span(SET, STIM["stimulus_id"], "lines 1-1")
        self.assertEqual((s["clip_in"], s["clip_out"], s["rows"]), (25.0, 31.5, [0, 0]))
        s = P.exam_span(SET, STIM["stimulus_id"], "Line 2")
        self.assertEqual((s["clip_in"], s["clip_out"]), (31.5, 60.0))
        for bad in ("lines 3", "lines 2-9", "some"):
            with self.assertRaises(ValueError):
                P.exam_span(SET, STIM["stimulus_id"], bad)

    def test_numbers(self):
        self.assertEqual(P.release_number(GAPFILL), 1)
        self.assertEqual(P.number(SET, CHOICE), 25)
        self.assertEqual(P.check_listening(SET), [])

    def test_rfc8785_hash(self):
        # an integral float hashes as an integer, as the exercises repository writes it
        self.assertEqual(P._jcs({"b": 49.0, "a": [0.5, 1e21, 1e-7]}), '{"a":[0.5,1e+21,1e-7],"b":49}')
        x = {"stimulus_id": "s", "audio": {"end_s": 49.0}}
        self.assertEqual(P.check_hashes({"parts": [{"stimuli": [dict(x, content_hash=P._h(x))], "items": []}]}), [])
        self.assertEqual(P.check_hashes({"parts": [{"stimuli": [dict(x, content_hash=P._h_legacy(x))], "items": []}]}), [])


class Rule(unittest.TestCase):
    def test_set_text_for_a_section_that_teaches_it(self):
        L = lesson("listening-09-x", "listening", SET)
        import vocab                  # the word bank is private: not on CI
        with mock.patch.object(vocab, "words_for_prompt", return_value="WORDS"):
            text = listening_rule.set_text(L, [5])
        self.assertIn("WORDS", text)
        self.assertIn("TRANSCRIPT oa-set-lx-0001-e1", text)
        self.assertIn("NOTE FORM oa-listening-990001", text)
        self.assertIn("QUESTION oa-listening-990025 (number 25", text)
        self.assertNotIn("Morning", listening_rule.set_text(L, [6]))

    def test_narration_text_follows_the_boards(self):
        form = {"topics": [{"thoughts": [{"blocks": [{"doc": {"text_type": "form"}}]}]}]}
        self.assertIn("NOTE FORM", listening_rule.narration_text(Path("."), form))
        self.assertNotIn("QUESTION BOARD", listening_rule.narration_text(Path("."), form))

    def test_first_lesson_welcome(self):
        self.assertIn("why listening matters", listening_rule.intro_first(wn.INTRO_FIRST))

    def test_the_play_cue_is_a_listening_lessons_only(self):
        enum = lambda s: s["properties"]["boards"]["items"]["properties"]["states"]["items"]["properties"][
            "utterances"]["items"]["properties"]["cues"]["items"]["properties"]["type"]["enum"]
        self.assertIn("play", enum(wn.schema_for(lesson("listening-09-x"))))
        self.assertNotIn("play", enum(wn.schema_for(lesson("reading-02-part-a"))))
        self.assertIs(wn.schema_for(lesson("grammar-01-x")), wn.SCHEMA)

    def test_recording_is_a_word_of_a_listening_lesson(self):
        self.assertNotIn("recording", ws.fixed_forbids(lesson("listening-09-x")))
        self.assertIn("recording", ws.fixed_forbids(lesson("reading-02-part-a")))

    def test_parts_b_and_c_of_either_skill(self):
        L = lesson("listening-09-x", "listening", SET)
        self.assertTrue(ws.has_part_b(L) and ws.has_listening_set(L))
        self.assertFalse(ws.has_part_c(L))
        self.assertIn(".doc-transcript", ws.frame_css(L))
        self.assertNotIn(".doc-transcript", ws.frame_css(lesson("reading-02-part-a")))


class Timeline(unittest.TestCase):
    def narr(self, cues, text):
        return {"boards": [{"id": "t1", "title": "x", "fixed": [], "states": [
            {"id": "t1.s1", "working": [], "utterances": [
                {"id": "t1.s1.u1", "text_with_cues": text, "cues": cues, "provenance": "authored"},
                {"id": "t1.s1.u2", "text_with_cues": "Done.", "cues": [], "provenance": "authored"}]}]}]}

    def index(self, words_1):
        return {"t1.s1.u1": {"text": " ".join(words_1), "words": words_1, "word_start": [0.0] * len(words_1),
                             "word_end": [0.5] * len(words_1), "duration_s": 2.0, "file": "a.wav"},
                "t1.s1.u2": {"text": "Done.", "words": ["Done."], "word_start": [0.0], "word_end": [0.5],
                             "duration_s": 1.0, "file": "b.wav"}}

    def test_a_play_cue_lays_the_recording_after_its_utterance(self):
        cue = {"id": "c1", "type": "play", "text": "s1", "with": "lines 2-3"}
        clip = {"audio_file": "../exam-audio/e1.mp3", "clip_in": 31.5, "clip_out": 41.5,
                "exam": {"stimulus": "s1", "label": "Extract 1", "span": "lines 2-3", "rows": [1, 2]}}
        boards, _, total = bt.lay_timeline(self.narr([cue], "Listen again.{{c1}}"),
                                           self.index(["Listen", "again."]), exam=lambda c: clip)
        us = boards[0]["states"][0]["utterances"]
        self.assertEqual([u["id"] for u in us], ["t1.s1.u1", "t1.s1.u1.x", "t1.s1.u2"])
        x = us[1]
        self.assertEqual((x["kind"], x["start"], x["end"], x["clip_in"], x["clip_out"]), ("exam", 2.4, 12.4, 31.5, 41.5))
        self.assertEqual((us[0]["cues"][0]["time"], us[0]["cues"][0]["time_end"]), (2.4, 12.4))
        self.assertEqual(us[2]["start"], 12.8)
        self.assertAlmostEqual(total, 13.8)

    def test_a_play_cue_needs_its_audio(self):
        with self.assertRaises(SystemExit):
            bt.lay_timeline(self.narr([{"id": "c1", "type": "play", "text": "s1", "with": "exam"}], "Listen.{{c1}}"),
                            self.index(["Listen."]))

    def test_reading_time_pause_and_every_other_pause(self):
        long_ = {"id": "c1", "type": "pause", "seconds": 90.3, "text": "reading time", "reading_time": True}
        boards, _, _ = bt.lay_timeline(self.narr([long_], "Read now.{{c1}}"), self.index(["Read", "now."]))
        self.assertEqual(boards[0]["states"][0]["utterances"][0]["cues"][0]["seconds"], 90.3)
        plain = {"id": "c1", "type": "pause", "seconds": 90.3, "text": "reading time"}
        boards, _, _ = bt.lay_timeline(self.narr([plain], "Read now.{{c1}}"), self.index(["Read", "now."]))
        self.assertEqual(boards[0]["states"][0]["utterances"][0]["cues"][0]["seconds"], 10.0)


class Bundle(unittest.TestCase):
    def test_format(self):
        self.assertEqual(blp.format_version("listening-02-part-a", part_b=True, listening=True), "1.18")
        self.assertEqual(blp.format_version("reading-03-part-b", part_b=True), "1.16")
        self.assertEqual(blp.format_version("grammar-01-verb-tenses"), "1.12")

    def test_the_spotlight_follows_the_recording(self):
        table = {"doc": {"stimulus": "s1", "text_type": "transcript"}}
        exam = {"id": "u.x", "kind": "exam", "start": 100.0, "end": 120.0, "clip_in": 30.0, "clip_out": 50.0,
                "exam": {"stimulus": "s1"}}
        bd = {"states": [{"utterances": [exam]}]}
        focus = [{"time": 90.0, "row": 4, "col": None}]
        out = blp.exam_focus(bd, table, focus, {"s1": [25.0, 35.0, 45.0, None, 60.0]})
        self.assertEqual([(f["time"], f["row"]) for f in out], [(90.0, 4), (100.0, 0), (105.0, 1), (115.0, 2),
                                                              (120.0, 4)])
        bd["states"][0]["veil"] = True
        self.assertEqual(blp.exam_focus(bd, table, focus, {"s1": [25.0, 35.0]}), focus)

    def test_a_recording_is_not_narration_in_text_json(self):
        bd = {"id": "b", "start": 0, "fixed": [], "states": [{"working": [], "utterances": [
            {"id": "u1", "start": 0, "text": "Listen.", "refs": []},
            {"id": "u1.x", "kind": "exam", "start": 1, "text": None, "refs": []}]}]}
        out = blp.text_export({"id": "listening-09-x"}, [{"id": "s", "title": "t", "category": None, "start": 0,
                                                          "end": 2, "boards": ["b"]}], [bd], {}, listening=True)
        self.assertEqual([n["id"] for n in out["sections"][0]["boards"][0]["narration"]], ["u1"])
        self.assertEqual(out["format_version"], "1.18")


RELEASE = P.release_path(P.LISTENING_PIN["release"])


@unittest.skipUnless(RELEASE.exists(), "the pinned Listening release is private; only on a machine with its copy")
class PinnedSets(unittest.TestCase):
    """The practice-set loader on the three Listening sets of sample-tests-v2."""

    def test_every_set_imports_and_builds(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            for sid in P.LISTENING_PIN["sets"]:
                L = tmp / ("listening-90-" + sid.split("-")[2])
                (L / "analysis").mkdir(parents=True)
                ps = P.import_set(L, sid)
                self.assertEqual(P.check_hashes({"parts": ps["parts"]}), [])
                self.assertEqual(P.check_listening(ps), [])
                for st in P.stimuli(ps).values():
                    self.assertTrue(P.is_audio(st))
                    self.assertEqual([r[0] for r in P.transcript_block(st)["rows"]], P.transcript_lines(st))
                    for span in ("exam", "extract"):
                        s = P.exam_span(ps, st["stimulus_id"], span)
                        self.assertTrue(0 <= s["clip_in"] < s["clip_out"] <= st["audio"]["duration_s"])
                for it in P.items(ps).values():
                    if P.is_gapfill(it):
                        f = P.form_block(ps, it)
                        self.assertEqual(len(f["typed"]), 12)
                    else:
                        self.assertEqual(len(P.question_block(ps, it)["question"]["options"]), 3)
                        self.assertFalse(P.question_block(ps, it)["question"].get("options_later"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_only_the_pinned_sets(self):
        L = Path(tempfile.mkdtemp()) / "listening-90-x"
        (L / "analysis").mkdir(parents=True)
        with self.assertRaises(SystemExit):
            P.import_set(L, "oa-set-la-0002")


if __name__ == "__main__":
    unittest.main()
