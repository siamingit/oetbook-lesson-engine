"""One-off voice comparison for page 13. Not part of the pipeline.

Synthesises a fixed pair of page-13 utterances with each candidate voice so
the maintainer can listen and choose. Writes to spike/out/, never to the
lesson folder.

    .venv/Scripts/python spike/scripts/tts_voice_samples.py
"""

from pathlib import Path

from cartesia import Cartesia

REPO_ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = REPO_ROOT / "spike" / "out" / "voice_samples"


def api_key() -> str:
    for line in (REPO_ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            if name.strip() == "CARTESIA_API_KEY":
                return value.strip().strip('"').strip("'")
    raise SystemExit("CARTESIA_API_KEY not found in .env")

MODEL_ID = "sonic-3.6"

# id, text — from <lesson_dir>/analysis/script/script.json, page 13
UTTERANCES = [
    ("u74", "Now let's practise. Four sentences here, and every one of them "
            "has a fault in the verb tense."),
    ("u48", "The patient was diagnosed with hypothyroidism since two "
            "thousand and ten."),
]

# candidate British English voices from the Cartesia library (voices?language=en-GB)
VOICES = {
    "clive": "b24f41fd-00a3-4cd8-992a-a0c9f13f3ef1",
    "courtney": "16a4052e-1f11-47ac-95f5-9330bee062f9",
    "rupert": "0ad65e7f-006c-47cf-bd31-52279d487913",
}


def main() -> None:
    client = Cartesia(api_key=api_key())
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for voice_name, voice_id in VOICES.items():
        for utt_id, text in UTTERANCES:
            out_path = OUT_DIR / f"{voice_name}_{utt_id}.wav"
            response = client.tts.generate(
                model_id=MODEL_ID,
                transcript=text,
                voice={"id": voice_id},
                language="en",
                output_format={
                    "container": "wav",
                    "encoding": "pcm_s16le",
                    "sample_rate": 44100,
                },
            )
            response.write_to_file(out_path)
            print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
