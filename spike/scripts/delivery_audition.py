"""One-off delivery audition for the Reading voice (maintainer, 2026-10-06: the
delivery "sounds like someone reading from a script"). Not part of the pipeline.

    .venv/Scripts/python spike/scripts/delivery_audition.py

The same passage, question one of reading-02-part-a (23:38), in several
deliveries, each a speed setting, a pause after each sentence, an emotion
setting (Cartesia `generation_config.emotion`) and a script: the lesson's own,
or a rewrite under the narration stage's DELIVERY rule. Each utterance is
synthesised on its own under the pronunciation lexicon, as in a lesson, and the
passage is joined with the player's gaps: 0.4 s between utterances, 1.2 s
between states, and the 4 s of the "try it first" pause. Writes
C:\\OET\\voice-audition\\reading\\delivery\\ and delivery.json there: each
passage's length, its pace and its pitch variation (pitch_check.py).
"""

import json
import re
import wave
from pathlib import Path

from cartesia import Cartesia

import lexicon
import pitch_check
import voices
from synthesize_audio import MODEL_ID, SAMPLE_RATE, api_key
from write_narration import spoken

OUT = Path(r"C:\OET\voice-audition\reading\delivery")
LESSON = Path(r"C:\OET\lessons\reading-02-part-a")
REWRITE = Path(__file__).resolve().parents[1] / "out" / "delivery-test" / "reading-02-part-a"
BOARD = "t7"
GAP_U, GAP_S, TRY_PAUSE = 0.4, 1.2, 4.0

VARIANTS = [
    {"name": "v1_speed1.0_pause0.6_original", "speed": 1.0, "pause": 0.6, "emotion": None, "script": "original",
     "what": "near-natural speed 1.0, 0.6 s after each sentence, no emotion setting, the lesson's script"},
    {"name": "v2_speed1.0_pause0.6_teacher", "speed": 1.0, "pause": 0.6, "emotion": None, "script": "teacher",
     "what": "speed 1.0, 0.6 s pauses, no emotion setting, the teacher-style script"},
    {"name": "v3_speed1.0_pause0.6_teacher_enthusiastic", "speed": 1.0, "pause": 0.6, "emotion": "enthusiastic",
     "script": "teacher", "what": "speed 1.0, 0.6 s pauses, emotion 'enthusiastic', the teacher-style script"},
    {"name": "v4_speed0.9_pause0.5_teacher_confident", "speed": 0.9, "pause": 0.5, "emotion": "confident",
     "script": "teacher", "what": "speed 0.9, 0.5 s pauses, emotion 'confident', the teacher-style script"},
]


def states(lesson: Path) -> list[list[str]]:
    na = json.loads((lesson / "analysis/narration/page-9/narration.json").read_text(encoding="utf-8"))
    bd = next(b for b in na["boards"] if b["id"] == BOARD)
    return [[spoken(u["text_with_cues"]) for u in s["utterances"]] for s in bd["states"]]


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", text))


def syllables(text: str) -> int:
    n = 0
    for w in re.findall(r"[A-Za-z][A-Za-z'-]*", text):
        if re.fullmatch(r"([A-Za-z]-)+[A-Za-z]", w):          # an initialism, letter by letter
            n += len(w.split("-")) * 1
            continue
        g = re.findall(r"[aeiouy]+", w.lower())
        n += max(1, len(g) - (1 if w.lower().endswith("e") and len(g) > 1 and not w.lower().endswith(("le", "ee")) else 0))
    return n


def synth(client, text: str, v: dict, dict_id: str) -> bytes:
    cfg = {"speed": v["speed"], **({"emotion": v["emotion"]} if v["emotion"] else {})}
    ev = client.tts.sse(model_id=MODEL_ID, transcript=text, voice={"id": voices.COURTNEY["id"]}, language="en",
                        add_timestamps=True, generation_config=cfg, pronunciation_dict_id=dict_id,
                        output_format={"container": "raw", "encoding": "pcm_s16le", "sample_rate": SAMPLE_RATE})
    pcm, w, a, b = bytearray(), [], [], []
    for e in ev:
        if e.type == "chunk" and e.audio:
            pcm.extend(e.audio)
        elif e.type == "timestamps":
            w += e.word_timestamps.words
            a += e.word_timestamps.start
            b += e.word_timestamps.end
        elif e.type == "error":
            raise RuntimeError(str(e))
    out, _, _ = voices.add_sentence_pauses(bytes(pcm), w, a, b, v["pause"], SAMPLE_RATE)
    return out


def save(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)


def silence(s: float) -> bytes:
    return bytes(2 * round(s * SAMPLE_RATE))


def join(clips: list[list[bytes]]) -> bytes:
    out = bytearray()
    for n, st in enumerate(clips):
        for k, c in enumerate(st):
            out += c
            if k < len(st) - 1:
                out += silence(GAP_U)
        if n == 1:                                    # the "try it first" state ends in its pause
            out += silence(TRY_PAUSE)
        if n < len(clips) - 1:
            out += silence(GAP_S)
    return bytes(out)


def measure(name: str, what: str, pcm: bytes, script: list[list[str]], clip_files: list[Path], extra: dict) -> dict:
    text = " ".join(" ".join(s) for s in script)
    secs = len(pcm) / 2 / SAMPLE_RATE
    speech = secs - GAP_U * sum(len(s) - 1 for s in script) - GAP_S * (len(script) - 1) - TRY_PAUSE
    sc = [s for s in (pitch_check.score(p) for p in clip_files) if s]
    sm = pitch_check.summary(sc)
    return {"name": name, "file": name + ".wav", "what": what, **extra,
            "seconds": round(secs, 1), "words": words(text),
            "wpm_overall": round(words(text) / secs * 60, 1),
            "wpm_speaking": round(words(text) / speech * 60, 1),
            "syllables_per_s_speaking": round(syllables(text) / speech, 2),
            "pitch_sd_median": sm["pitch_sd_median"], "pitch_range_median": sm["pitch_range_median"]}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "clips").mkdir(exist_ok=True)
    client = Cartesia(api_key=api_key())
    dict_id = lexicon.require_synced(client)["cartesia"]["dict_id"]
    scripts = {"original": states(LESSON), "teacher": states(REWRITE)}
    report, chars = [], 0
    # the lesson as narrated now, from its own clips
    na = json.loads((LESSON / "analysis/narration/page-9/narration.json").read_text(encoding="utf-8"))
    idx = json.loads((LESSON / "generated/page-9/boards/audio_index.json").read_text(encoding="utf-8"))
    bd = next(b for b in na["boards"] if b["id"] == BOARD)
    files = [[LESSON / "generated/page-9/boards" / idx[u["id"]]["file"] for u in s["utterances"]] for s in bd["states"]]
    def pcm_of(p):
        with wave.open(str(p)) as w:
            return w.readframes(w.getnframes())
    cur = join([[pcm_of(p) for p in st] for st in files])
    save(OUT / "v0_current.wav", cur)
    report.append(measure("v0_current", "the lesson as narrated now: speed 0.6, 0.30 s pauses, no emotion setting, "
                          "the lesson's script (reference)", cur, scripts["original"], [p for st in files for p in st],
                          {"speed": 0.6, "pause": 0.3, "emotion": None, "script": "original"}))
    for v in VARIANTS:
        clips, paths = [], []
        for n, st in enumerate(scripts[v["script"]]):
            row = []
            for k, text in enumerate(st):
                pcm = synth(client, text, v, dict_id)
                chars += len(text)
                p = OUT / "clips" / f"{v['name']}_{n + 1}_{k + 1}.wav"
                save(p, pcm)
                row.append(pcm)
                paths.append(p)
            clips.append(row)
        pcm = join(clips)
        save(OUT / f"{v['name']}.wav", pcm)
        report.append(measure(v["name"], v["what"], pcm, scripts[v["script"]], paths,
                              {k: v[k] for k in ("speed", "pause", "emotion", "script")}))
        print(json.dumps(report[-1]))
    base = json.loads(pitch_check.BASELINE.read_text(encoding="utf-8"))
    (OUT / "delivery.json").write_text(json.dumps(
        {"date": "2026-10-06", "voice": "courtney", "model": MODEL_ID, "passage": "reading-02-part-a, question one (t7)",
         "gaps": {"between_utterances": GAP_U, "between_states": GAP_S, "try_it_first_pause": TRY_PAUSE},
         "pitch_baseline_rupert": {k: base[k] for k in ("clips", "pitch_sd_median", "pitch_sd_p10", "pitch_sd_p25")},
         "characters_billed": chars, "variants": report}, indent=1), encoding="utf-8")
    print(json.dumps(report[0]))
    print("characters", chars)


if __name__ == "__main__":
    main()
