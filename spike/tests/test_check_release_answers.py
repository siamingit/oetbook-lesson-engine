"""check_release_answers.py on a made-up release: what counts as an answer, how
words are compared, and that a failure never prints the answer."""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_release_answers as c  # noqa: E402

PACKAGE = {"sets": [{"items": [
    {"item_id": "x-1", "type": "text", "scoring": {"accepted": ["Zorbic flux", "zorbic fluxes"]}},
    {"item_id": "x-2", "type": "choice", "scoring": {"key_option_id": "x-2-o2"},
     "options": [{"option_id": "x-2-o1", "text": "Wrong option words"},
                 {"option_id": "x-2-o2", "text": "Quillan valve rests"}]},
    {"item_id": "x-3", "type": "choice", "scoring": {"key_option_id": "x-3-o1"},
     "options": [{"option_id": "x-3-o1", "text": "Text A", "stimulus_id": "s-a"}]},
]}]}


class Answers(unittest.TestCase):
    def test_typed_forms_and_choice_keys(self):
        got = c.answers(PACKAGE)
        self.assertIn(("x-1", "accepted[0]", "zorbic flux"), got)
        self.assertIn(("x-1", "accepted[1]", "zorbic fluxes"), got)
        self.assertIn(("x-2", "key", "quillan valve rests"), got)
        self.assertNotIn("wrong option words", [a for _, _, a in got])

    def test_a_matching_key_naming_a_text_is_not_an_answer(self):
        self.assertFalse([a for a in c.answers(PACKAGE) if a[0] == "x-3"])


class Find(unittest.TestCase):
    def files(self, *texts):
        d = Path(tempfile.mkdtemp())
        out = []
        for n, t in enumerate(texts):
            p = d / f"f{n}.md"
            p.write_text(t, encoding="utf-8")
            out.append(p)
        return out

    def test_found_across_case_and_punctuation(self):
        hits = c.find(c.answers(PACKAGE), self.files("ok\nThe ZORBIC-flux here."), set())
        self.assertEqual(len(hits), 1)
        self.assertIn(":2: an answer of x-1 (accepted[0])", hits[0])

    def test_whole_words_only(self):
        self.assertEqual(c.find(c.answers(PACKAGE), self.files("zorbic fluxing"), set()), [])

    def test_exempt_form(self):
        f = self.files("zorbic flux")
        self.assertEqual(c.find(c.answers(PACKAGE), f, {("x-1", "accepted[0]")}), [])

    def test_the_answer_is_never_printed(self):
        pkg = Path(tempfile.mkdtemp()) / "package.json"
        pkg.write_text(json.dumps(PACKAGE), encoding="utf-8")
        files = self.files("a quillan valve rests here")
        out = io.StringIO()
        with mock.patch.object(c, "tracked_files", return_value=files), \
                mock.patch.object(sys, "argv", ["x", str(pkg)]), redirect_stdout(out):
            self.assertEqual(c.main(), 1)
        self.assertIn("x-2 (key)", out.getvalue())
        self.assertNotIn("quillan", out.getvalue().lower())

    def test_no_release_fails(self):
        out = io.StringIO()
        with mock.patch.object(c, "local_packages", return_value=[]), \
                mock.patch.object(sys, "argv", ["x"]), redirect_stdout(out):
            self.assertEqual(c.main(), 1)


# A made-up Listening release (ADR 029): a Part A gap-fill item, whose gaps
# carry the answers, and an extract with a transcript
TRANSCRIPT = ("Nurse: Good morning, the plorvex dressing on your left gallimer needs changing today.\n"
              "Patient: Right, and will the quindle tablets still be taken twice a day after that?")
LISTENING = {"sets": [{"parts": [{"stimuli": [
    {"stimulus_id": "s-e1", "type": "audio-extract",
     "speakers": [{"label": "Nurse"}, {"label": "Patient"}],
     "transcript": {"format": "oa-transcript-v1", "text": TRANSCRIPT}}],
    "items": [{"item_id": "g-item", "type": "gapfill", "numbers": [1, 2], "gaps": [
        {"gap_id": "g-1", "number": 1, "prompt": "Wound: ____ dressing",
         "scoring": {"accepted": ["Vexadrine gauze"], "accepted_misspellings": ["vexadrin gauze"]}},
        {"gap_id": "g-2", "number": 2, "prompt": "Pain: ____", "scoring": {"accepted": ["trelloid ache"]}}]}]}]}]}


class Listening(unittest.TestCase):
    def files(self, *texts):
        return Find.files(self, *texts)

    def test_gap_answers_and_misspellings(self):
        got = c.answers(LISTENING)
        self.assertIn(("g-1", "accepted[0]", "vexadrine gauze"), got)
        self.assertIn(("g-1", "misspelling[0]", "vexadrin gauze"), got)
        self.assertIn(("g-2", "accepted[0]", "trelloid ache"), got)

    def test_a_planted_gap_answer_is_found(self):
        hits = c.find(c.answers(LISTENING), self.files("notes\nThe answer was Vexadrine-gauze."), set())
        self.assertEqual(len(hits), 1)
        self.assertIn(":2: an answer of g-1 (accepted[0])", hits[0])

    def test_transcript_runs_leave_the_speaker_out(self):
        runs = c.transcript_runs(LISTENING)
        self.assertIn(tuple("good morning the plorvex dressing on your left".split()), runs)
        self.assertFalse(any(r[0] == "nurse" for r in runs))
        self.assertEqual(runs[tuple("good morning the plorvex dressing on your left".split())], ("s-e1", "run@0"))

    def test_a_planted_transcript_line_is_found_across_lines(self):
        hits = c.find_runs(c.transcript_runs(LISTENING),
                           self.files("intro\nwill the quindle tablets still\nbe taken twice a day"), set())
        self.assertEqual(len(hits), 1)
        self.assertIn(":2: a run of 8 words of the transcript of s-e1", hits[0])

    def test_seven_words_are_not_a_run(self):
        self.assertEqual(c.find_runs(c.transcript_runs(LISTENING),
                                     self.files("will the quindle tablets still be taken"), set()), [])

    def test_an_exempt_run(self):
        f = self.files("good morning the plorvex dressing on your left")
        self.assertEqual(c.find_runs(c.transcript_runs(LISTENING), f, {("s-e1", "run@0")}), [])

    def test_neither_answer_nor_transcript_is_printed(self):
        pkg = Path(tempfile.mkdtemp()) / "package.json"
        pkg.write_text(json.dumps({**LISTENING, "sets": LISTENING["sets"] + PACKAGE["sets"]}), encoding="utf-8")
        files = self.files("we wrote vexadrine gauze\nand the plorvex dressing on your left gallimer needs changing")
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["x", str(pkg), "--files", *map(str, files)]), redirect_stdout(out):
            self.assertEqual(c.main(), 1)
        text = out.getvalue().lower()
        self.assertIn("g-1 (accepted[0])", text)
        self.assertIn("transcript of s-e1", text)
        for word in ("vexadrine", "plorvex", "gallimer", "dressing"):
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
