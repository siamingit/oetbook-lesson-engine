"""Transcribe a lesson's audio with ElevenLabs Scribe v2 (batch).

Usage: python transcribe.py <lesson_dir> [--dry-run] [--audio PATH] [--out-dir PATH]

Reads  <lesson_dir>/analysis/audio.mp3        (or --audio)
       <lesson_dir>/analysis/keyterms.json    (built by build_keyterms.py)
Writes <out_dir>/scribe_v2_response.json      raw API response, unmodified
       <out_dir>/scribe_v2_response.headers.txt

--dry-run sends every form field EXCEPT the audio file. No audio reaches the API,
so nothing is billed; it only checks API-key permissions and field encoding.

Language is deliberately not set: the speech is Persian with English terms mixed in,
so the model must auto-detect rather than be forced into one language.

The API key goes to curl through stdin (--config -), never on the command line,
so it does not appear in the process list.
"""

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://api.elevenlabs.io/v1/speech-to-text"
SUBSCRIPTION = "https://api.elevenlabs.io/v1/user/subscription"
MODEL = "scribe_v2"
USD_PER_1000_CREDITS = 0.364   # maintainer's top-up rate: $10 = 27,472 credits
REPO = Path(__file__).resolve().parents[2]


def api_key() -> str:
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            if name.strip() == "ELEVENLABS_API_KEY":
                return value.strip().strip('"').strip("'")
    raise SystemExit("ELEVENLABS_API_KEY not found in .env")


def credits_used(key: str) -> int | None:
    """Credits consumed this billing period, or None if the key cannot read it."""
    req = urllib.request.Request(SUBSCRIPTION, headers={"xi-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["character_count"]
    except urllib.error.HTTPError:
        return None   # key lacks the user_read permission


def header_cost(headers: Path) -> int | None:
    values = [line.split(":", 1)[1].strip()
              for line in headers.read_text(encoding="utf-8").splitlines()
              if line.lower().startswith("character-cost:")]
    return int(values[-1]) if values else None


def opt(name: str, default: str | None = None) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main() -> None:
    lesson = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv
    analysis = lesson / "analysis"
    audio = Path(opt("--audio", str(analysis / "audio.mp3")))
    out_dir = Path(opt("--out-dir", str(analysis)))
    out_dir.mkdir(parents=True, exist_ok=True)
    keyterms = json.loads((analysis / "keyterms.json").read_text(encoding="utf-8"))["keyterms"]

    body = out_dir / "scribe_v2_response.json"
    headers = out_dir / "scribe_v2_response.headers.txt"
    key = api_key()
    config = f'header = "xi-api-key: {key}"\n'

    cmd = [
        "curl", "-sS", "--fail-with-body", "--max-time", "7200", "--config", "-",
        "-X", "POST", ENDPOINT,
        "-H", "Accept: application/json",
        "-F", f"model_id={MODEL}",
        "-F", "timestamps_granularity=word",
        "-F", "diarize=false",
        "-w", "\\nHTTP %{http_code} in %{time_total}s\\n",
    ]
    for term in keyterms:
        cmd += ["-F", f"keyterms={term}"]

    if dry_run:
        print(f"DRY RUN: {len(keyterms)} keyterms, no file attached")
        result = subprocess.run(cmd, input=config, capture_output=True, text=True)
        print(result.stdout[:2000] or result.stderr[:2000])
        return

    cmd += ["-F", f"file=@{audio}", "-D", str(headers), "-o", str(body)]
    print(f"POST {ENDPOINT}  model={MODEL}  keyterms={len(keyterms)}  "
          f"audio={audio.stat().st_size / 1e6:.1f} MB")

    before = credits_used(key)
    result = subprocess.run(cmd, input=config, capture_output=True, text=True)
    print(result.stdout or result.stderr)
    if result.returncode != 0:
        raise SystemExit(f"curl failed with code {result.returncode}")
    after = credits_used(key)

    charged = header_cost(headers)
    if charged is None and None not in (before, after):
        charged = after - before

    print(f"credits before   : {before if before is not None else 'unavailable (key lacks user_read)'}")
    print(f"credits after    : {after if after is not None else 'unavailable (key lacks user_read)'}")
    if charged is not None:
        print(f"credits used     : {charged}")
        print(f"cost             : ${charged * USD_PER_1000_CREDITS / 1000:.2f} "
              f"at ${USD_PER_1000_CREDITS:.3f} per 1,000 credits")
        if None not in (before, after) and after - before != charged:
            print(f"WARNING: header says {charged} credits, "
                  f"subscription delta says {after - before}")
    else:
        print("credits used     : UNKNOWN - no character-cost header and no subscription access")

    print(f"transcription id : {json.loads(body.read_text(encoding='utf-8')).get('transcription_id')}")


if __name__ == "__main__":
    main()
