"""Listening lessons (docs/adr/029-listening-lessons.md, bundle 1.18; ADR 030,
bundle 1.19; ADR 031, bundle 1.20): the lesson type and its features, the
practice set's transcripts, note forms, word times, sections and audio spans, the
Listening rule module, its pause-and-try prompt check and its vocabulary panel
(items, answers, the variety check), the play cue in the timeline, a Listening
board's `listen`, and the practice-set loader on the three pinned Listening sets
(only where the local release copy exists: it is private, so CI runs the
made-up set alone).

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
import word_times as WT             # noqa: E402
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
# its word times (14 words: 6, 3 and 5 a row; the speakers' labels are not words)
# and its sections (heading 1 from word 0, heading 2 from word 9), as word_times.py
# writes them (ADR 030)
TIMES = [[25.0 + k, 25.5 + k] for k in range(6)] + [[31.5, 31.9], [32.0, 32.4], [32.5, 33.0]] \
    + [[34.0 + k * .5, 34.4 + k * .5] for k in range(5)]
WORD_TIMES = {"stimuli": {STIM["stimulus_id"]: {
    "audio_sha256": STIM["audio"]["sha256"], "transcript_sha256": WT.transcript_sha(STIM),
    "row_words": [6, 3, 5], "words": 14, "matched": 14, "times": TIMES}}}
SECTIONS = {"stimuli": {STIM["stimulus_id"]: [{"heading": 1, "first_gap": 1, "from": 0},
                                              {"heading": 2, "first_gap": 2, "from": 9}]}}


def setUpModule():
    WT._cache.update(f=WORD_TIMES, s=SECTIONS)


def tearDownModule():
    WT._cache.clear()


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

    def test_row_times_from_the_word_times(self):
        # each row's first word, 0.15 s before, never before the extract (ADR 030:
        # the release's admin turn times are not used)
        self.assertEqual(P.row_times(SET, STIM["stimulus_id"]), [25.0, 31.35, 33.85])
        self.assertEqual(WT.words_of(STIM)[1], [6, 3, 5])
        self.assertEqual(WT.words_of(STIM)[0][6], "Sore")

    def test_word_times_must_fit_their_transcript_and_audio(self):
        other = dict(STIM, transcript={"format": "oa-transcript-v1", "text": "Nurse: Hello."})
        self.assertIsNone(WT.for_stimulus(other))
        self.assertIsNone(WT.for_stimulus(dict(STIM, audio=dict(STIM["audio"], sha256="1" * 64))))
        self.assertIsNotNone(WT.for_stimulus(STIM))

    def test_sections(self):
        secs = P.section_rows(STIM)
        self.assertEqual([(x["from"], x["to"], x["rows"]) for x in secs], [(0, 8, [0, 1]), (9, 13, [2, 2])])
        self.assertIn("heading 2 (gaps from 2): rows 3-3", P.transcript_for_prompt(SET, STIM))

    def test_a_quote_found_in_fragments(self):
        words = WT.words_of(STIM)[0]
        self.assertEqual(WT.find_quote(words, "Mr Plon: Sore since Tuesday. ... wakes me", ["Mr Plon"]), (6, 11))
        self.assertIsNone(WT.find_quote(words, "since Monday"))

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
        self.assertEqual((s["clip_in"], s["clip_out"], s["rows"]), (25.0, 31.35, [0, 0]))
        s = P.exam_span(SET, STIM["stimulus_id"], "Line 2")
        self.assertEqual((s["clip_in"], s["clip_out"]), (31.35, 33.85))
        s = P.exam_span(SET, STIM["stimulus_id"], "heading 2")
        self.assertEqual((s["clip_in"], s["clip_out"], s["rows"]), (33.85, 60.0, [2, 2]))
        self.assertEqual(P.exam_span(SET, STIM["stimulus_id"], "heading 1")["clip_out"], 33.85)
        for bad in ("lines 4", "lines 2-9", "some", "heading 3", "question 25"):
            with self.assertRaises(ValueError):
                P.exam_span(SET, STIM["stimulus_id"], bad)

    def test_numbers(self):
        self.assertEqual(P.release_number(GAPFILL), 1)
        self.assertEqual(P.number(SET, CHOICE), 25)
        self.assertEqual(P.check_listening(SET), [])
        with mock.patch.dict(WT._cache, {"f": {"stimuli": {}}}):
            self.assertEqual(P.check_listening(SET), [STIM["stimulus_id"] + " (no word times for this transcript "
                                                      "and audio)"])

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

    def test_pause_and_try_prompts_never_repeat(self):
        u = lambda i, text: {"id": i, "text_with_cues": text + "{{c1}}",
                             "cues": [{"id": "c1", "type": "pause", "seconds": 4, "text": "try it first"}]}
        boards = [{"states": [{"utterances": [
            u("a", "Pause the lesson now and try to find the answer. Then play it again."),
            u("b", "Can you hear it yourself? Stop here, have a go, and press play when you are ready."),
            {"id": "c", "text_with_cues": "Pause the lesson now and try to find the answer.", "cues": []},
            u("d", "Pause the lesson here and try to find the answer.")]}]}]
        found = listening_rule.prompt_findings(listening_rule.prompts(boards))
        self.assertEqual([x[0] for x in found], ["d"])          # one word swapped; "c" is no prompt
        self.assertIn("nearly repeats a", found[0][1])
        same = listening_rule.prompt_findings([("x", "Then play it again.")], [("other:y", "Then play it again!")])
        self.assertIn("repeats other:y", same[0][1])
        self.assertEqual(listening_rule.prompt_findings([("x", "Your turn: find answer 27.")],
                                                        [("y", "Over to you, which option fits?")]), [])

    def item(self, **kw):
        b = {"type": "gloss", "label": "PANEL Row 3", "term": "wakes me", "kind": "verb",
             "explanation": "stops my sleep", "synonym": "rouses, disturbs", "text": "The pain wakes him every night."}
        b.update(kw)
        return b, listening_rule.panel_item(SET, STIM, b)

    def test_a_panel_item(self):
        # ADR 031: the words said in row N, their sentence's span from the word
        # times, an answer's word shown only once it is taught
        b, bad = self.item()
        self.assertEqual(bad, [])
        self.assertEqual((b["panel"]["row"], b["panel"]["word"], b["panel"]["to"]), (2, 10, 11))
        self.assertTrue(b["panel"]["after_answer"])         # gap 2's accepted form "wakes" is in it
        self.assertEqual((b["heard"]["start"], b["heard"]["end"]), (33.85, 36.5))   # "It wakes me at night."
        self.assertIsNone(b["icon"])
        self.assertEqual(b["synonym"], "rouses, disturbs")
        b, bad = self.item(term="morning", label="PANEL Row 1", kind="word", text="Come back in the morning.")
        self.assertEqual(bad, [])
        self.assertFalse(b["panel"]["after_answer"])

    def test_a_panel_item_is_the_speakers_own_words(self):
        _, bad = self.item(label="PANEL Row 1")
        self.assertIn("said in row 3", bad[0])
        _, bad = self.item(label="PANEL Row 9")
        self.assertIn("rows 1-3", bad[0])
        _, bad = self.item(kind="slang", synonym="a, b, c")
        self.assertEqual(len(bad), 2)

    def test_a_panel_example_is_never_copied(self):
        _, bad = self.item(text="It wakes me at night again.")
        self.assertTrue(any("copies" in x for x in bad))
        # an idiom's own words inside the example are not a copy
        _, bad = self.item(term="wakes me at night", text="Her cough wakes me at night too.")
        self.assertFalse(any("copies" in x for x in bad))

    def test_a_paraphrase_pair(self):
        b, bad = self.item(term="Sore", label="PANEL Row 2", kind="paraphrase", synonym="painful", left="pain",
                           text="My knee is sore after the run.")
        self.assertEqual(bad, [])
        self.assertEqual(b["synonym"], "pain (in the question); similar: painful")
        self.assertTrue(b["panel"]["after_answer"])         # a pair leads to an answer
        _, bad = self.item(term="Sore", label="PANEL Row 2", kind="paraphrase", left="fever and cough",
                           text="My knee is sore after the run.")
        self.assertTrue(any("as printed" in x for x in bad))

    def test_vocabulary_explanations_never_repeat(self):
        def u(i, text, block):
            return {"id": i, "text_with_cues": "{{c1}}" + text, "cues": [{"id": "c1", "type": "reveal", "block": block}]}
        blocks = {"w1": {"panel": {"kind": "verb"}, "term": "wakes", "explanation": "stops sleep", "synonym": "rouses",
                         "text": "Noise wakes me."},
                  "w2": {"panel": {"kind": "word"}, "term": "sore", "explanation": "painful", "synonym": "aching",
                         "text": "My leg is sore."},
                  "n1": {"term": None}}
        boards = [{"states": [{"utterances": [
            u("a", "Here is a really useful verb for you: wakes.", "w1"),
            u("b", "Here is a really useful verb for you: sore.", "w2.1"),
            u("c", "Here is a really useful verb for you: sore.", "n1")]}]}]
        mine = listening_rule.vocab_explanations(boards, blocks)
        self.assertEqual([x[0] for x in mine], ["a", "b"])                  # "c" teaches no panel item
        found = listening_rule.vocab_findings(mine)
        self.assertEqual([x[0] for x in found], ["b"])                      # the same frame, another word
        self.assertEqual(listening_rule.vocab_findings(
            [("x", "Wakes means stops sleep.", {"wakes", "stops", "sleep"})],
            [("y", "Sore? Think of aching.", {"sore", "aching"})]), [])

    def test_the_rule_carries_the_owners_layout_and_facts(self):
        for text in ("NEVER covered", "NO board picture", "question N"):
            self.assertIn(text, listening_rule.SCREENS_SET)
        self.assertIn("PAUSE-AND-TRY PROMPTS", listening_rule.NARRATION)
        self.assertIn("PANEL Row <N>", listening_rule.SCREENS_SET)
        self.assertIn("THE VOCABULARY PANEL", listening_rule.NARRATION)
        self.assertIn("instructor's suggested", listening_rule.SCREENS)
        self.assertNotIn("Covered:", listening_rule.NARRATION_QUESTION)

    def test_narration_text_follows_the_boards(self):
        form = {"topics": [{"thoughts": [{"blocks": [{"doc": {"text_type": "form"}}]}]}]}
        self.assertIn("NOTE FORM", listening_rule.narration_text(Path("."), form))
        self.assertNotIn("LISTENING BOARD (ADR 029", listening_rule.narration_text(Path("."), form))

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
        self.assertEqual(blp.format_version("listening-02-part-a", part_b=True, listening=True), "1.20")
        self.assertEqual(blp.format_version("reading-03-part-b", part_b=True), "1.16")
        self.assertEqual(blp.format_version("grammar-01-verb-tenses"), "1.12")

    def test_a_listening_board(self):
        # 1.19 (ADR 030): a board with a transcript gets its `listen`: the word
        # times, the sections, and on a Part A board the form's heading rows
        L = lesson("listening-09-x", "listening", SET)
        tr, form = P.transcript_block(STIM), P.form_block(SET, GAPFILL)
        blocks_all = {"k1": dict(tr, id="k1"), "k2": dict(form, id="k2"), "k3": {"type": "plain"}}
        bd = {"id": "x_t1", "fixed": ["k1", "k2"], "states": [{"working": ["k3"]}]}
        ls = blp.listen_board(L, bd, blocks_all)
        self.assertEqual((ls["block"], ls["form"], ls["split"], ls["lines"]), ("k1", "k2", 62, 10))
        # ADR 031: never hyphenated, a little smaller than 1.19's 3.4, the form whole in the reading time
        self.assertFalse(ls["hyphens"])
        self.assertTrue(2.6 <= ls["font"] < 3.4)
        self.assertGreaterEqual(ls["reading"]["font"], 2.6)
        self.assertEqual(ls["panel"]["items"], [])
        self.assertEqual(ls["times"], TIMES)
        self.assertEqual([(x["from"], x["to"], x["row"]) for x in ls["sections"]], [(0, 8, 0), (9, 13, 2)])
        self.assertGreaterEqual(ls["font"], 2.6)
        self.assertGreaterEqual(ls["form_font"], 2.6)
        self.assertIsNone(blp.listen_board(L, {"id": "x_t2", "fixed": ["k2"], "states": []}, blocks_all))

    def test_a_boards_panel_items(self):
        # 1.20 (ADR 031): the panel's items, in the order they are said, each
        # with the state that teaches it; a panel item is no note of the board
        L = lesson("listening-09-x", "listening", SET)
        tr = P.transcript_block(STIM)
        pn = lambda w, after: {"type": "gloss", "panel": {"kind": "verb", "row": 2, "word": w, "to": w + 1,
                                                           "pair": None, "after_answer": after}}
        blocks_all = {"k1": dict(tr, id="k1"), "k5": pn(10, True), "k6": pn(6, False), "k7": {"type": "plain"}}
        bd = {"id": "x_t1", "fixed": ["k1"], "states": [{"id": "x_t1.s1", "working": ["k7"]},
                                                        {"id": "x_t1.s2", "working": ["k5", "k6"]}]}
        ls = blp.listen_board(L, bd, blocks_all)
        self.assertEqual([(x["block"], x["word"], x["after_answer"], x["state"]) for x in ls["panel"]["items"]],
                         [("k6", 6, False, "x_t1.s2"), ("k5", 10, True, "x_t1.s2")])
        self.assertEqual(ls["panel"]["max"], listening_rule.PANEL_MAX)
        self.assertGreaterEqual(ls["panel"]["font"], 2.6)
        self.assertNotIn("reading", ls)                     # no note form on the board

    def test_a_panel_item_is_drawn_for_the_panel(self):
        b = {"id": "k5", "type": "gloss", "term": "wakes me", "explanation": "stops my sleep",
             "synonym": "pain (in the question)", "text": "The pain wakes him.", "icon": None,
             "panel": {"kind": "paraphrase"}}
        html = ws.block_html(b)
        self.assertIn("gl lvoc lv-pair", html)
        self.assertNotIn("gl-pic", html)
        self.assertNotIn("lvoc", ws.block_html(dict(b, panel=None)))

    def test_a_transcript_is_drawn_in_its_box(self):
        html = ws.doc_table_html(P.transcript_block(STIM), ' data-id="k1"')
        for part in ('class="lt-head"', 'class="lt-win"', 'class="lt-scr"', 'class="lt-mk"', 'class="lt-caret"'):
            self.assertIn(part, html)
        self.assertIn('<span class="spk">Mr Plon:</span>', html)

    def test_a_recording_is_not_narration_in_text_json(self):
        bd = {"id": "b", "start": 0, "fixed": [], "states": [{"working": [], "utterances": [
            {"id": "u1", "start": 0, "text": "Listen.", "refs": []},
            {"id": "u1.x", "kind": "exam", "start": 1, "text": None, "refs": []}]}]}
        out = blp.text_export({"id": "listening-09-x"}, [{"id": "s", "title": "t", "category": None, "start": 0,
                                                          "end": 2, "boards": ["b"]}], [bd], {}, listening=True)
        self.assertEqual([n["id"] for n in out["sections"][0]["boards"][0]["narration"]], ["u1"])
        self.assertEqual(out["format_version"], "1.20")


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
                with mock.patch.dict(WT._cache, clear=True):          # the committed word times
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

    def test_the_committed_word_times_and_sections(self):
        with mock.patch.dict(WT._cache, clear=True):
            self.assertEqual(WT.check(), [])
            pkg, _ = WT.release()
            lc = next(x for x in pkg["sets"] if x["set_id"] == "oa-set-lc-0001")
            ps = {"parts": lc["parts"], "release": {}}
            for n in range(31, 37):
                s = P.exam_span(ps, "oa-set-lc-0001-e1", f"question {n}")
                self.assertLess(s["clip_in"], s["clip_out"])

    def test_only_the_pinned_sets(self):
        L = Path(tempfile.mkdtemp()) / "listening-90-x"
        (L / "analysis").mkdir(parents=True)
        with self.assertRaises(SystemExit):
            P.import_set(L, "oa-set-la-0002")


if __name__ == "__main__":
    unittest.main()
