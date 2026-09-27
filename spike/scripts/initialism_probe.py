"""Hear how the voice says an initialism in different written forms, for the
maintainer to choose by ear (2026-09-27: COPD and MRI were spoken letter by
letter with long gaps).

    .venv/Scripts/python spike/scripts/initialism_probe.py

Each form goes into the same carrier sentence and is synthesised once at the
lesson speed, with NO pronunciation dictionary, so what is heard is the
written form alone (the lexicon's COPD alias would otherwise rewrite it).
Measured, never assumed: from Cartesia's word timestamps, the span of the
initialism (first letter's start to last letter's end) and the longest gap
between its letters; from its phoneme timestamps, whether it was said as
letters or as a word; and Scribe's transcript. Phonemes and Scribe are
pointers, not proof (methodology §20): the maintainer's ear decides. A form
already in probes.json is not paid for again.

Writes: spike/out/initialism-probe/<form>.wav and probes.json
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ear import transcribe_file                                          # noqa: E402
from synthesize_audio import MODEL_ID, VOICE_ID, api_key, write_wav      # noqa: E402
from synthesize_narration import SAMPLE_RATE                             # noqa: E402
from transcribe import api_key as scribe_key                             # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "out" / "initialism-probe"
SPEED = 1.0                                      # the lesson speed
# a carrier sentence per pair of initialisms: (text, (word before, word after) each)
CARRIERS = {
    "copd-mri": ("She has {0} and needs an {1} scan today.", (("has", "and"), ("an", "scan"))),
    "iv-ot": ("Give the drug by {0} and then call the {1} team.", (("by", "and"), ("the", "team"))),
    "gp-ecg-ct": ("Her {0} ordered an {1} and a {2} scan.", (("her", "ordered"), ("an", "and"), ("a", "scan"))),
}
FORMS = {                                        # name: carrier, (initialisms)
    "dots-spaced": ("copd-mri", ("C. O. P. D.", "M. R. I.")),  # the lexicon's COPD alias until 2026-09-27
    "spaced": ("copd-mri", ("C O P D", "M R I")),              # how the narration writer spelled them
    "dots-joined": ("copd-mri", ("C.O.P.D.", "M.R.I.")),
    "hyphens": ("copd-mri", ("C-O-P-D", "M-R-I")),
    "capitals": ("copd-mri", ("COPD", "MRI")),                 # the voice's own reading
    "iv-ot-capitals": ("iv-ot", ("IV", "OT")),                 # 'OT' was heard as 'ought' (Grammar 2)
    "iv-ot-dots-joined": ("iv-ot", ("I.V.", "O.T.")),
    "iv-ot-hyphens": ("iv-ot", ("I-V", "O-T")),
    "gp-ecg-ct-capitals": ("gp-ecg-ct", ("GP", "ECG", "CT")),
    "gp-ecg-ct-hyphens": ("gp-ecg-ct", ("G-P", "E-C-G", "C-T")),
}


def synth(client, text: str) -> dict:
    events = client.tts.sse(
        model_id=MODEL_ID, transcript=text, voice={"id": VOICE_ID}, language="en",
        add_timestamps=True, add_phoneme_timestamps=True, generation_config={"speed": SPEED},
        output_format={"container": "raw", "encoding": "pcm_s16le", "sample_rate": SAMPLE_RATE})
    pcm, words, ws, we, ph, ps = bytearray(), [], [], [], [], []
    for ev in events:
        if ev.type == "chunk" and ev.audio:
            pcm.extend(ev.audio)
        elif ev.type == "timestamps":
            words += ev.word_timestamps.words
            ws += ev.word_timestamps.start
            we += ev.word_timestamps.end
        elif ev.type == "phoneme_timestamps":
            ph += ev.phoneme_timestamps.phonemes
            ps += ev.phoneme_timestamps.start
        elif ev.type == "error":
            raise RuntimeError(f"Cartesia error: {ev}")
    return {"pcm": bytes(pcm), "words": words, "start": ws, "end": we, "ph": ph, "ph_start": ps}


def span(r: dict, before: str, after: str, frm: int = 0) -> dict:
    """The initialism's timing: the words between the carrier words `before`
    and `after` (searched from word `frm`), and the phonemes said in that time
    (letters or a word)."""
    w = [re.sub(r"[^a-z]", "", x.lower()) for x in r["words"]]
    i = w.index(before, frm) + 1
    j = w.index(after, i)
    gaps = [r["start"][k + 1] - r["end"][k] for k in range(i, j - 1)]
    t0, t1 = r["start"][i], r["end"][j - 1]
    return {"tokens": r["words"][i:j], "span_s": round(t1 - t0, 3),
            "max_gap_s": round(max(gaps), 3) if gaps else 0.0,
            "phonemes": " ".join(p for p, t in zip(r["ph"], r["ph_start"]) if t0 - 0.01 <= t < t1),
            "next": j}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    store = OUT / "probes.json"
    probes = json.loads(store.read_text(encoding="utf-8")) if store.exists() else {}
    client = skey = None
    chars = 0
    for name, (cid, pair) in FORMS.items():
        carrier, around = CARRIERS[cid]
        text = carrier.format(*pair)
        if probes.get(name, {}).get("text") == text:
            continue
        if client is None:
            from cartesia import Cartesia
            client, skey = Cartesia(api_key=api_key()), scribe_key()
        r = synth(client, text)
        said, frm = {}, 0
        for t, a in zip(pair, around):      # in order: a carrier word may come twice
            said[t] = span(r, *a, frm)
            frm = said[t].pop("next")
        wav = OUT / f"{name}.wav"
        write_wav(wav, r["pcm"])
        chars += len(text)
        probes[name] = {"text": text, "file": str(wav), "characters": len(text),
                        "duration_s": round(len(r["pcm"]) / 2 / SAMPLE_RATE, 3),
                        "said": said,
                        "heard": transcribe_file(wav, skey).get("text", "")}
        store.write_text(json.dumps(probes, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"characters sent this run: {chars}")
    for name, p in probes.items():
        print(f"{name:18} {p['duration_s']:5.2f} s | heard: {p['heard']}")
        for t, x in p["said"].items():
            print(f"    {t:12} {x['span_s']:.2f} s, longest gap {x['max_gap_s']:.2f} s: {x['phonemes']}")


if __name__ == "__main__":
    main()
