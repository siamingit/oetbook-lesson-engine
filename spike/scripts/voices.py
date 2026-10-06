"""The narration voice of a lesson, chosen by its type (ADR 027).

Grammar and Vocabulary lessons keep Rupert at speed 1.0 (maintainer,
2026-09-22 and 2026-09-24; methodology §23), with nothing added to the clip,
so their cache keys and audio are unchanged. Reading and Listening lessons
use Courtney at about 135 words a minute (maintainer, 2026-10-06, by ear from
C:\\OET\\voice-audition\\reading\\courtney_135wpm.wav): Cartesia's lowest
speed setting, 0.6, which gives her about 140-144 words a minute, and 0.30 s
of silence added after every sentence of a clip but its last.
"""

from pathlib import Path

RUPERT = {"name": "rupert", "id": "0ad65e7f-006c-47cf-bd31-52279d487913",
          "speed": 1.0, "sentence_pause_s": 0.0}
COURTNEY = {"name": "courtney", "id": "16a4052e-1f11-47ac-95f5-9330bee062f9",
            "speed": 0.6, "sentence_pause_s": 0.30}

BY_TYPE = {"reading": COURTNEY, "listening": COURTNEY}

SENTENCE_END = (".", "?", "!")


def for_lesson(lesson: Path) -> dict:
    """The voice of a lesson, from the first word of its id (docs/04-LESSON-BUNDLE.md §4)."""
    return BY_TYPE.get(Path(lesson).name.split("-")[0].lower(), RUPERT)


def add_sentence_pauses(pcm: bytes, words: list[str], start: list[float], end: list[float],
                        pause_s: float, sample_rate: int) -> tuple[bytes, list[float], list[float]]:
    """`pause_s` of silence after every word that ends a sentence, the clip's
    last word excepted, cut into the middle of the pause the voice already
    makes there. 16-bit mono PCM. The word timestamps move with the audio."""
    samples = round(pause_s * sample_rate)
    ends = [i for i, w in enumerate(words[:-1]) if w.rstrip("\"')]").endswith(SENTENCE_END)]
    if not samples or not ends:
        return pcm, list(start), list(end)
    out, start2, end2 = bytearray(), list(start), list(end)
    at = 0
    for n, i in enumerate(ends, 1):
        cut = min(round((end[i] + start[i + 1]) / 2 * sample_rate), len(pcm) // 2)
        out += pcm[at * 2:cut * 2] + bytes(samples * 2)
        at = cut
        last = ends[n] if n < len(ends) else len(words) - 1
        for j in range(i + 1, last + 1):
            start2[j] = start[j] + n * samples / sample_rate
            end2[j] = end[j] + n * samples / sample_rate
    out += pcm[at * 2:]
    return bytes(out), start2, end2
