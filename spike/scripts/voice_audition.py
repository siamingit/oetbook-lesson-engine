"""One-off female voice audition for the Reading and Listening lessons. Not
part of the pipeline.

Synthesises the same sample of about 30 seconds with each candidate voice, at
the lesson speed (1.0), and reports the measured words per minute. Writes to
C:\\OET\\voice-audition\\reading\\ (maintainer, 2026-10-05); no lesson uses
these voices until the maintainer chooses one by ear and an ADR records it.

    .venv/Scripts/python spike/scripts/voice_audition.py
    .venv/Scripts/python spike/scripts/voice_audition.py --slower

`--slower` (maintainer, 2026-10-06: Courtney, but about 155 words a minute is
too fast): the same text with Courtney at about 145, 135 and 125 words a
minute. Measured on 2026-10-06, Cartesia's lowest speed setting (0.6) gives
Courtney about 140 words a minute, and below about 0.85 the rate barely moves
and varies from run to run. So 145 is made with the speed setting alone (the
closest of a few takes), and 135 and 125 from one take at the lowest setting
with longer pauses between sentences: silence added in the middle of each
pause the voice already makes after a sentence, until the clip's measured rate
is the target. Every clip is checked for distortion: samples at full scale,
clicks (a jump between samples far above the clip's own), and words stretched
out of proportion (each word's length against the same word at speed 1.0, from
Cartesia's word timestamps, for words of 0.3 s or more at speed 1.0).
"""

import json
import re
import statistics
import sys
import wave
from array import array
from pathlib import Path

from cartesia import Cartesia

from tts_voice_samples import api_key

MODEL_ID = "sonic-3.6"
SPEED = 1.0
OUT_DIR = Path(r"C:\OET\voice-audition\reading")

SAMPLE = (
    "Hello, and welcome. In Part A of the Reading test, you have fifteen "
    "minutes for four short texts. First, skim all four texts quickly. Then "
    "scan for the key words in each question. For example, a patient with "
    "C-O-P-D may take an anticoagulant. Read the warnings carefully: a "
    "contraindication tells you when a treatment must not be given. And "
    "watch for hypoglycaemia, or low blood sugar, after insulin. Copy each "
    "answer exactly as it appears in the text."
)

# Cartesia library voices, language en, gender feminine, country GB, chosen
# from their descriptions as calm and clear for a teacher (listed 2026-10-05).
VOICES = {
    "courtney": "16a4052e-1f11-47ac-95f5-9330bee062f9",
    "imogen": "5a93ae96-9e3e-4b9d-8575-5f62b7de6d0f",
    "julia": "273f9ef7-9fc2-4def-88bb-ab108c6249ca",
    "victoria": "dc30854e-e398-4579-9dc8-16f6cb2c19b9",
}


def words(text: str) -> int:
    # "C-O-P-D" is one word as spoken
    return len(re.findall(r"[A-Za-z][A-Za-z'-]*", text))


def wav_seconds(path: Path) -> float:
    # a streamed WAV's header carries a placeholder length: measure the data
    with wave.open(str(path)) as w:
        bytes_per_second = w.getframerate() * w.getnchannels() * w.getsampwidth()
    data = path.read_bytes()
    return (len(data) - data.index(b"data") - 8) / bytes_per_second


def main() -> None:
    client = Cartesia(api_key=api_key())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = []
    for name, voice_id in VOICES.items():
        path = OUT_DIR / f"{name}_reading-audition.wav"
        response = client.tts.generate(
            model_id=MODEL_ID,
            transcript=SAMPLE,
            voice={"id": voice_id},
            language="en",
            generation_config={"speed": SPEED},
            output_format={"container": "wav", "encoding": "pcm_s16le",
                           "sample_rate": 44100},
        )
        response.write_to_file(path)
        seconds = wav_seconds(path)
        wpm = words(SAMPLE) / seconds * 60
        report.append({"voice": name, "id": voice_id, "file": path.name,
                       "seconds": round(seconds, 2), "wpm": round(wpm, 1)})
        print(f"{name}: {seconds:.1f} s, {wpm:.0f} words a minute -> {path}")
    (OUT_DIR / "audition.json").write_text(json.dumps(
        {"model": MODEL_ID, "speed": SPEED, "text": SAMPLE,
         "characters_each": len(SAMPLE), "words": words(SAMPLE),
         "voices": report}, indent=1), encoding="utf-8")


COURTNEY = VOICES["courtney"]
SAMPLE_RATE = 44100
SPEED_FLOOR = 0.6           # Cartesia's lowest generation_config.speed
SPEEDS_145 = [0.80, 0.77, 0.83, 0.74, 0.86, 0.71]
TOLERANCE = 1.5             # words a minute


def sse(client: Cartesia, speed: float) -> dict:
    """Courtney at `speed`, as raw PCM with word timestamps."""
    events = client.tts.sse(
        model_id=MODEL_ID, transcript=SAMPLE, voice={"id": COURTNEY}, language="en",
        add_timestamps=True, generation_config={"speed": speed},
        output_format={"container": "raw", "encoding": "pcm_s16le", "sample_rate": SAMPLE_RATE})
    pcm, said, start, end = bytearray(), [], [], []
    for ev in events:
        if ev.type == "chunk" and ev.audio:
            pcm.extend(ev.audio)
        elif ev.type == "timestamps":
            said += ev.word_timestamps.words
            start += ev.word_timestamps.start
            end += ev.word_timestamps.end
        elif ev.type == "error":
            raise RuntimeError(f"Cartesia error: {ev}")
    return measured({"speed": speed, "pcm": bytes(pcm), "words": said,
                     "start": start, "end": end})


def measured(clip: dict) -> dict:
    clip["seconds"] = len(clip["pcm"]) / 2 / SAMPLE_RATE
    clip["wpm"] = words(SAMPLE) / clip["seconds"] * 60
    return clip


def save(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)


def sentence_ends(clip: dict) -> list[int]:
    """Indexes of the words that end a sentence, the last word excepted."""
    return [i for i, w in enumerate(clip["words"][:-1]) if w.endswith(".")]


def with_pauses(clip: dict, target: float) -> dict:
    """The clip with the same silence added after every sentence but the last,
    in the middle of the pause already there, so its rate is `target`. The
    word timestamps move with the audio."""
    ends = sentence_ends(clip)
    extra = words(SAMPLE) / target * 60 - clip["seconds"]
    each = max(0, round(extra / len(ends) * SAMPLE_RATE))
    pcm, start, end = bytearray(), list(clip["start"]), list(clip["end"])
    at, shift = 0, 0.0
    for i in ends:
        cut = round((clip["end"][i] + clip["start"][i + 1]) / 2 * SAMPLE_RATE)
        pcm += clip["pcm"][at * 2:cut * 2] + bytes(each * 2)
        at = cut
        shift += each / SAMPLE_RATE
        for j in range(i + 1, len(start)):
            start[j] = clip["start"][j] + shift
            end[j] = clip["end"][j] + shift
    pcm += clip["pcm"][at * 2:]
    return measured({**clip, "pcm": bytes(pcm), "start": start, "end": end,
                     "pause_added_s": round(each / SAMPLE_RATE, 3)})


def distortion(clip: dict, ref: dict) -> dict:
    """What a slowed voice can do wrong that a number can catch. The ear
    decides; this says where to listen."""
    a = array("h", clip["pcm"])
    full = sum(1 for x in a if abs(x) >= 32700)
    jumps = [abs(a[i] - a[i - 1]) for i in range(1, len(a))]
    typical = statistics.quantiles(jumps, n=1000)[-1]            # the 99.9th percentile
    clicks = sum(1 for j in jumps if j > max(4 * typical, 8000))
    # each word's length against the same word at speed 1.0; the timestamps
    # come in steps of about 0.08 s, so a short word cannot be judged
    same = clip["words"] == ref["words"]
    stretch = []
    if same:
        for i, w in enumerate(clip["words"]):
            d0 = ref["end"][i] - ref["start"][i]
            if d0 >= 0.3:
                stretch.append((w, (clip["end"][i] - clip["start"][i]) / d0, d0))
    ratios = [r for _, r, _ in stretch]
    med = statistics.median(ratios) if ratios else None
    outliers = [{"word": w, "x_speed1": round(r, 2), "seconds_at_speed1": round(d0, 2)}
                for w, r, d0 in stretch if med and r > 1.5 * med]
    gaps = [round(clip["start"][i + 1] - clip["end"][i], 2) for i in sentence_ends(clip)]
    return {"samples_at_full_scale": full, "clicks": clicks,
            "words_match_speed1": same, "words_judged": len(stretch),
            "median_word_length_x_speed1": round(med, 2) if med else None,
            "longest_word_x_speed1": round(max(ratios), 2) if ratios else None,
            "words_stretched_over_1.5x_median": outliers,
            "pauses_after_sentences_s": gaps}


def entry(target: int, clip: dict, ref: dict, how: str) -> dict:
    path = OUT_DIR / f"courtney_{target}wpm.wav"
    save(path, clip["pcm"])
    check = distortion(clip, ref)
    print(f"{path}: {how}; {clip['seconds']:.2f} s, {clip['wpm']:.1f} words a minute; "
          f"{check['samples_at_full_scale']} at full scale, {check['clicks']} clicks, "
          f"median word x{check['median_word_length_x_speed1']}, longest "
          f"x{check['longest_word_x_speed1']}, "
          f"{len(check['words_stretched_over_1.5x_median'])} stretched")
    return {"target_wpm": target, "file": path.name, "how": how, "speed": clip["speed"],
            **({"pause_added_s": clip["pause_added_s"]} if "pause_added_s" in clip else {}),
            "seconds": round(clip["seconds"], 2), "wpm": round(clip["wpm"], 1), "check": check}


def slower() -> None:
    client = Cartesia(api_key=api_key())
    calls = []

    def take(speed: float, purpose: str) -> dict:
        got = sse(client, speed)
        calls.append({"speed": speed, "wpm": round(got["wpm"], 1), "purpose": purpose})
        print(f"  speed {speed:.2f} ({purpose}): {got['wpm']:.1f} words a minute")
        return got

    ref = take(1.0, "reference")
    best = None
    for speed in SPEEDS_145:
        got = take(speed, "145 wpm")
        if best is None or abs(got["wpm"] - 145) < abs(best["wpm"] - 145):
            best = got
        if abs(got["wpm"] - 145) <= TOLERANCE:
            break
    floor = take(SPEED_FLOOR, "the lowest setting, for 135 and 125 wpm")
    clips = [entry(145, best, ref, f"speed setting {best['speed']}"),
             *(entry(t, with_pauses(floor, t), ref,
                     f"speed setting {SPEED_FLOOR} ({floor['wpm']:.1f} wpm) and longer pauses "
                     "between sentences") for t in (135, 125))]
    record = OUT_DIR / "audition.json"
    data = json.loads(record.read_text(encoding="utf-8"))
    old = data.get("courtney_slower") or {}
    data["courtney_slower"] = {
        "date": "2026-10-06", "model": MODEL_ID, "voice": COURTNEY,
        "method": "Cartesia SSE with word timestamps, no pronunciation dictionary; wpm = "
                  "words of the text / length of the whole clip. The speed setting alone "
                  "cannot go below about 140 wpm (see first_search): 135 and 125 add silence "
                  "after each sentence of the take at the lowest setting",
        "reference_speed1": {"seconds": round(ref["seconds"], 2), "wpm": round(ref["wpm"], 1)},
        "floor_take": {"speed": SPEED_FLOOR, "seconds": round(floor["seconds"], 2),
                       "wpm": round(floor["wpm"], 1), "check": distortion(floor, ref)},
        "clips": clips, "calls": calls,
        "first_search": old.get("first_search") or old.get("calls"),
        "characters_billed": len(SAMPLE) * len(calls)}
    record.write_text(json.dumps(data, indent=1), encoding="utf-8")


if __name__ == "__main__":
    slower() if "--slower" in sys.argv else main()
