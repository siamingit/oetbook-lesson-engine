"""The narration voice of a lesson (ADR 027 and its amendment).

Every lesson is narrated by Rupert at speed 1.0, with nothing added to the
clip: the voice, provider and settings of the approved Grammar and Vocabulary
lessons (maintainer, 2026-09-22 and 2026-09-24; methodology §23). The female
voice first chosen for Reading and Listening (Courtney, 2026-10-06) was
withdrawn the same day (ADR 027 amendment); COURTNEY stays here only for the
audition record (delivery_audition.py), never for a lesson.
"""

from pathlib import Path

RUPERT = {"name": "rupert", "id": "0ad65e7f-006c-47cf-bd31-52279d487913",
          "speed": 1.0, "sentence_pause_s": 0.0}
# withdrawn 2026-10-06 (ADR 027 amendment): for the auditions' record only
COURTNEY = {"name": "courtney", "id": "16a4052e-1f11-47ac-95f5-9330bee062f9",
            "speed": 0.6, "sentence_pause_s": 0.30}

BY_TYPE: dict[str, dict] = {}                  # every lesson type: Rupert (ADR 027 amendment)

# The Speaking course's patients (ADR 027 amendment 2026-11-09, ADR 053): a narration line
# with a `speaker` field is said by its patient, in sonic-3.6 at speed 0.8; a line without
# one is the teacher's, in the lesson's voice, so nothing made before changes.
GEMMA = {"name": "gemma", "id": "62ae83ad-4f6a-430b-af41-a9bede9286ca",
         "speed": 0.8, "sentence_pause_s": 0.0}
ARCHIE = {"name": "archie", "id": "ef191366-f52f-447a-a398-ed8c0f2943a1",
          "speed": 0.8, "sentence_pause_s": 0.0}
SPEAKERS = {"patient_f": GEMMA, "patient_m": ARCHIE}
# A patient's feeling, from the role card, as the voice's emotion setting (ADR 053): only
# where the card makes the patient worried or upset; every other line is a plain take.
EMOTIONS = {"worried": "anxious", "upset": "frustrated"}


def voice_for(speaker: str | None, lesson_voice: dict) -> dict:
    """The voice of one narration line: its patient's, or the lesson's own."""
    if speaker is None or speaker == "teacher":
        return lesson_voice
    if speaker not in SPEAKERS:
        raise ValueError(f"unknown speaker {speaker!r}: one of teacher, {', '.join(SPEAKERS)}")
    return SPEAKERS[speaker]


def emotion_for(feeling: str | None) -> str | None:
    """The voice's emotion setting for a patient's feeling, or None for a plain take."""
    if feeling is None:
        return None
    if feeling not in EMOTIONS:
        raise ValueError(f"unknown emotion {feeling!r}: one of {', '.join(EMOTIONS)}")
    return EMOTIONS[feeling]

SENTENCE_END = (".", "?", "!")


def for_lesson(lesson: Path) -> dict:
    """The voice of a lesson, from its type (lesson_type.py)."""
    import lesson_type
    return BY_TYPE.get(lesson_type.of(lesson), RUPERT)


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
