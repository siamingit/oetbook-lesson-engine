"""Synthesise every utterance in a page script with Cartesia Sonic 3.6.

Cached by text + voice + model + speed + pronunciation dictionary, so an
unchanged utterance is never re-synthesised. The cache is content-addressed
on purpose: a full script regeneration issues fresh utterance ids, and audio
keyed by id would be thrown away wholesale on every rewrite even where the
words never changed. The id is a label on the entry, not the key.

Writes one WAV file per distinct utterance text plus an index of word-level
timestamps. Audio no longer referenced by the script is deleted.

    .venv/Scripts/python spike/scripts/synthesize_audio.py <lesson_dir> [--speed 0.94]

The page number comes from script.json's own meta.page field.

Reads:  <lesson_dir>/analysis/script/script.json
Writes: <lesson_dir>/generated/page-<N>/audio/*.wav
        <lesson_dir>/generated/page-<N>/audio_index.json
"""

import argparse
import hashlib
import json
import sys
import wave
from pathlib import Path

from cartesia import Cartesia

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]

MODEL_ID = "sonic-3.6"
VOICE_NAME = "rupert"
VOICE_ID = "0ad65e7f-006c-47cf-bd31-52279d487913"  # British, chosen 2026-09-22

# Fixes Sonic 3.6's default mispronunciation of "fibrosis" (reads the first
# syllable as short /I/ instead of the correct diphthong /aI/ -- confirmed by
# inspecting phoneme timestamps). Created once in the Cartesia account as
# "page13-pronunciation"; the id is account-specific, not portable.
PRONUNCIATION_DICT_ID = "pdict_hvpmosZ9jAfyXDWFdaknq2"

SAMPLE_RATE = 44100


def api_key() -> str:
    for line in (REPO_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            if name.strip() == "CARTESIA_API_KEY":
                return value.strip().strip('"').strip("'")
    raise SystemExit("CARTESIA_API_KEY not found in .env")


def cache_key(text: str, speed: float) -> str:
    basis = f"{text}|{VOICE_ID}|{MODEL_ID}|{speed:.3f}|{PRONUNCIATION_DICT_ID}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]


def synthesize(client: Cartesia, text: str, speed: float) -> dict:
    """Call Cartesia's SSE endpoint and collect audio + word timestamps."""
    events = client.tts.sse(
        model_id=MODEL_ID,
        transcript=text,
        voice={"id": VOICE_ID},
        language="en",
        add_timestamps=True,
        generation_config={"speed": speed},
        pronunciation_dict_id=PRONUNCIATION_DICT_ID,
        output_format={
            "container": "raw",
            "encoding": "pcm_s16le",
            "sample_rate": SAMPLE_RATE,
        },
    )
    pcm = bytearray()
    words: list[str] = []
    word_start: list[float] = []
    word_end: list[float] = []
    for event in events:
        if event.type == "chunk":
            audio = event.audio
            if audio:
                pcm.extend(audio)
        elif event.type == "timestamps":
            words.extend(event.word_timestamps.words)
            word_start.extend(event.word_timestamps.start)
            word_end.extend(event.word_timestamps.end)
        elif event.type == "error":
            raise RuntimeError(f"Cartesia error: {event}")
    return {
        "pcm": bytes(pcm),
        "words": words,
        "word_start": word_start,
        "word_end": word_end,
    }


def write_wav(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)  # pcm_s16le
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--speed", type=float, default=0.6,
                         help="Cartesia generation_config.speed, 0.6-1.5 (default 0.6). "
                              "Measured on the full page-13 script: 1.0 -> 167.5 wpm, "
                              "0.94 -> 149.7 wpm, 0.85 -> 146.1 wpm, 0.6 (the API floor) "
                              "-> 140.3 wpm. The 130-140 wpm target is not reachable "
                              "through speed alone; 0.6 is the closest available.")
    args = parser.parse_args()

    page = args.page
    script_path = paths.script_dir(args.lesson_dir, page) / "script.json"
    script = json.loads(script_path.read_text(encoding="utf-8"))
    if script["meta"]["page"] != page:
        raise SystemExit(f"script under page-{page} reports page "
                         f"{script['meta']['page']}")

    out_dir = paths.generated_dir(args.lesson_dir, page)
    audio_dir = out_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "audio_index.json"

    old_index: dict = {}
    if index_path.exists():
        old_index = json.loads(index_path.read_text(encoding="utf-8"))

    # Everything already synthesised, keyed by content rather than by id, so a
    # renamed utterance still finds its audio.
    by_hash = {entry["hash"]: entry for entry in old_index.values()
               if (out_dir / entry["file"]).exists()}

    client = Cartesia(api_key=api_key())

    index: dict = {}
    synthesized = 0
    cached = 0
    total_chars = 0
    total_duration_s = 0.0

    for beat in script["beats"]:
        for utt in beat["utterances"]:
            utt_id = utt["id"]
            text = utt["text"]
            key = cache_key(text, args.speed)

            known = by_hash.get(key)
            if known:
                index[utt_id] = {**known, "id": utt_id}
                cached += 1
                total_duration_s += known["duration_s"]
                continue

            wav_path = audio_dir / f"{key}.wav"
            result = synthesize(client, text, args.speed)
            write_wav(wav_path, result["pcm"])
            duration_s = len(result["pcm"]) / 2 / SAMPLE_RATE  # 16-bit mono

            entry = {
                "id": utt_id,
                "hash": key,
                "voice": VOICE_NAME,
                "voice_id": VOICE_ID,
                "model": MODEL_ID,
                "speed": args.speed,
                "pronunciation_dict_id": PRONUNCIATION_DICT_ID,
                "file": f"audio/{wav_path.name}",
                "text": text,
                "words": result["words"],
                "word_start": result["word_start"],
                "word_end": result["word_end"],
                "duration_s": duration_s,
                "characters": len(text),
            }
            index[utt_id] = entry
            by_hash[key] = entry
            synthesized += 1
            total_chars += len(text)
            total_duration_s += duration_s

    # Drop audio the current script no longer refers to.
    keep = {entry["file"] for entry in index.values()}
    orphans = [p for p in audio_dir.glob("*.wav") if f"audio/{p.name}" not in keep]
    for path in orphans:
        path.unlink()

    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"synthesized: {synthesized}")
    print(f"reused from cache: {cached}")
    print(f"orphaned files removed: {len(orphans)}")
    print(f"characters sent this run: {total_chars}")
    print(f"total audio duration: {total_duration_s:.1f}s ({total_duration_s / 60:.2f} min)")
    print(f"wrote {index_path}")


if __name__ == "__main__":
    main()
