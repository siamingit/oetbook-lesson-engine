"""The lesson voice and its added sentence pauses (ADR 027).

    .venv/Scripts/python -m unittest discover -s spike/tests
"""

import sys
import unittest
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import voices  # noqa: E402

RATE = 1000     # samples a second, small numbers for the test


def clip(seconds: float) -> bytes:
    return array("h", [1000] * round(seconds * RATE)).tobytes()


class VoiceByLessonType(unittest.TestCase):
    def test_reading_and_listening_are_courtney(self):
        for name in ("reading-02-part-a", "listening-01-overview"):
            self.assertIs(voices.for_lesson(Path("C:/x") / name), voices.COURTNEY)

    def test_other_lessons_keep_rupert(self):
        for name in ("grammar-04-articles", "vocabulary-01-word-forms"):
            self.assertIs(voices.for_lesson(Path(name)), voices.RUPERT)
        self.assertEqual(voices.RUPERT["speed"], 1.0)
        self.assertEqual(voices.RUPERT["sentence_pause_s"], 0.0)

    def test_courtney_as_decided(self):
        self.assertEqual(voices.COURTNEY["speed"], 0.6)
        self.assertEqual(voices.COURTNEY["sentence_pause_s"], 0.30)


class SentencePauses(unittest.TestCase):
    words = ["Hello.", "Skim", "first?", "Then", "scan."]
    start = [0.0, 1.0, 1.5, 3.0, 3.5]
    end = [0.5, 1.4, 2.0, 3.4, 4.0]

    def test_pause_after_each_sentence_but_the_last(self):
        pcm, s, e = voices.add_sentence_pauses(clip(4.2), self.words, self.start, self.end,
                                               0.3, RATE)
        self.assertEqual(len(pcm), len(clip(4.2)) + 2 * 2 * 300)   # two pauses of 300 samples
        self.assertEqual(s[:1], self.start[:1])
        self.assertAlmostEqual(s[1], 1.3)        # after "Hello."
        self.assertAlmostEqual(e[2], 2.3)
        self.assertAlmostEqual(s[3], 3.6)        # after "first?", both pauses
        self.assertAlmostEqual(e[4], 4.6)

    def test_silence_is_cut_into_the_pause(self):
        pcm, _, _ = voices.add_sentence_pauses(clip(4.2), self.words, self.start, self.end,
                                               0.3, RATE)
        a = array("h", pcm)
        cut = round((0.5 + 1.0) / 2 * RATE)       # the middle of the pause after "Hello."
        self.assertEqual(set(a[cut:cut + 300]), {0})
        self.assertEqual(a[cut - 1], 1000)

    def test_no_pause_changes_nothing(self):
        raw = clip(4.2)
        pcm, s, e = voices.add_sentence_pauses(raw, self.words, self.start, self.end, 0.0, RATE)
        self.assertEqual((pcm, s, e), (raw, self.start, self.end))

    def test_one_sentence_changes_nothing(self):
        raw = clip(1.0)
        pcm, s, _ = voices.add_sentence_pauses(raw, ["One", "sentence."], [0, 0.5],
                                               [0.4, 0.9], 0.3, RATE)
        self.assertEqual((pcm, s), (raw, [0, 0.5]))


if __name__ == "__main__":
    unittest.main()
