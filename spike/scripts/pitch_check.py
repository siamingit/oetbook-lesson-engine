"""The monotony check: how lively a lesson's voice is, measured by its pitch
variation (adopted by the maintainer, 2026-10-06; ADR 027 amendment). The
runner runs it on every lesson's finished player.

    .venv/Scripts/python spike/scripts/pitch_check.py <lesson_dir>         # the check
    .venv/Scripts/python spike/scripts/pitch_check.py FILE.wav [...]       # score clips
    .venv/Scripts/python spike/scripts/pitch_check.py --baseline           # re-measure Rupert's lessons

A monotonous reading keeps its pitch close to one note; a teacher's voice rises
and falls. For each clip the fundamental frequency (F0) is tracked every 10 ms
(autocorrelation on 40 ms frames, 70 to 400 Hz, a frame voiced when its
normalised autocorrelation peak is 0.5 or more and it is loud enough), turned
into semitones about the clip's own median, so a low and a high voice compare
on one scale. Two figures per clip:
  - `pitch_sd`: the standard deviation of the voiced frames, in semitones;
  - `pitch_range`: the 90th minus the 10th percentile, in semitones.
Frames more than 12 semitones from the median (octave errors) are left out.
The baseline is the distribution of `pitch_sd` over clips of the lessons the
maintainer approved with Rupert's voice (660 clips, 2026-10-06: median 4.42,
10th percentile 3.71, 25th percentile 4.07). A lesson whose median clip is
below 4.07 fails; every clip below 3.71 is listed, with its time in the
lesson, for the maintainer's ear. The thresholds are fixed here (ADR 027
amendment); --baseline measures the lessons again for information only. All
eleven approved lessons pass (medians 4.32 to 4.46). This is a signal for the
ear, not a judge of it.
"""

import json
import random
import sys
import wave
from pathlib import Path

import numpy as np

LESSONS = Path(r"C:\OET\lessons")
BASELINE = Path(__file__).resolve().parents[1] / "out" / "pitch-baseline.json"
FAIL_BELOW = 4.07          # semitones: a lesson's median clip (ADR 027 amendment)
FLAG_BELOW = 3.71          # semitones: a clip listed for the maintainer's ear
RUPERT_LESSONS = ["grammar-01-verb-tenses", "grammar-02-verb-use", "grammar-03-nominalization",
                  "grammar-04-articles", "grammar-05-complex-compound", "grammar-06-clause",
                  "grammar-07-punctuation", "grammar-08-paraphrasing", "vocabulary-01-word-forms",
                  "vocabulary-02-collocations", "vocabulary-03-collocations-2"]


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
        if w.getnchannels() > 1:
            x = x.reshape(-1, w.getnchannels()).mean(axis=1)
    return x, sr


def f0_track(x: np.ndarray, sr: int) -> np.ndarray:
    """F0 in Hz of each voiced 10 ms step (unvoiced steps left out)."""
    k = max(1, sr // 11025)                       # about 11 kHz is enough for speech F0
    x = x[: len(x) // k * k].reshape(-1, k).mean(axis=1)
    sr = sr / k
    frame, hop = int(0.04 * sr), int(0.01 * sr)
    lo, hi = int(sr / 400), int(sr / 70)
    if len(x) < frame:
        return np.array([])
    starts = np.arange(0, len(x) - frame, hop)
    frames = np.stack([x[s:s + frame] for s in starts])
    frames = frames - frames.mean(axis=1, keepdims=True)
    rms = np.sqrt((frames ** 2).mean(axis=1))
    loud = rms > 0.15 * np.percentile(rms, 95)
    n = 1 << int(np.ceil(np.log2(2 * frame)))
    spec = np.fft.rfft(frames * np.hanning(frame), n)
    ac = np.fft.irfft(spec * np.conj(spec), n)[:, :hi + 2]
    ac = ac / np.maximum(ac[:, :1], 1e-12)
    lag = lo + np.argmax(ac[:, lo:hi + 1], axis=1)
    peak = ac[np.arange(len(lag)), lag]
    voiced = loud & (peak >= 0.5)
    # parabolic interpolation around the peak
    a, b, c = (ac[np.arange(len(lag)), lag - 1], peak, ac[np.arange(len(lag)), np.minimum(lag + 1, hi + 1)])
    d = 0.5 * (a - c) / np.where(np.abs(a - 2 * b + c) > 1e-12, a - 2 * b + c, 1e-12)
    return (sr / (lag + np.clip(d, -1, 1)))[voiced]


def score(path: Path) -> dict | None:
    f0 = f0_track(*read_wav(path))
    if len(f0) < 20:
        return None
    st = 12 * np.log2(f0 / np.median(f0))
    st = st[np.abs(st) <= 12]
    return {"pitch_sd": round(float(np.std(st)), 3),
            "pitch_range": round(float(np.percentile(st, 90) - np.percentile(st, 10)), 3),
            "voiced_s": round(len(st) * 0.01, 2)}


def lesson_clips(lesson: Path) -> list[Path]:
    out = []
    for ip in sorted((lesson / "generated").glob("*/boards/audio_index.json")):
        for e in json.loads(ip.read_text(encoding="utf-8")).values():
            p = ip.parent / e["file"]
            if p.exists():
                out.append(p)
    return out


def summary(scores: list[dict]) -> dict:
    sd = np.array([s["pitch_sd"] for s in scores])
    rg = np.array([s["pitch_range"] for s in scores])
    return {"clips": len(sd), "pitch_sd_median": round(float(np.median(sd)), 3),
            "pitch_sd_p10": round(float(np.percentile(sd, 10)), 3),
            "pitch_sd_p25": round(float(np.percentile(sd, 25)), 3),
            "pitch_sd_p75": round(float(np.percentile(sd, 75)), 3),
            "pitch_range_median": round(float(np.median(rg)), 3)}


def baseline(per_lesson: int = 60, seed: int = 7) -> dict:
    """A sample of clips from each lesson approved with Rupert's voice."""
    rng = random.Random(seed)
    scores = []
    for name in RUPERT_LESSONS:
        clips = lesson_clips(LESSONS / name)
        for p in rng.sample(clips, min(per_lesson, len(clips))):
            s = score(p)
            if s:
                scores.append(s)
    b = {"voice": "rupert", "lessons": RUPERT_LESSONS, "per_lesson": per_lesson, "seed": seed,
         **summary(scores)}
    BASELINE.write_text(json.dumps(b, indent=1), encoding="utf-8")
    return b


def check_lesson(lesson: Path) -> int:
    """Every clip of the lesson's player: the median against FAIL_BELOW, each
    clip under FLAG_BELOW listed with its time; written to pitch_check.json."""
    d = lesson / "generated" / "lesson-player"
    t = json.loads((d / "timeline.json").read_text(encoding="utf-8"))
    start = {u["id"]: u["start"] for bd in t["boards"] for st in bd["states"] for u in st["utterances"]}
    url = "file:///" + str(d / "player.html").replace("\\", "/")
    rows = []
    for ip in sorted((lesson / "generated").glob("*/boards/audio_index.json")):
        tag = ip.parents[1].name
        for uid, e in json.loads(ip.read_text(encoding="utf-8")).items():
            sc = score(ip.parent / e["file"])
            if sc and f"{tag}_{uid}" in start:
                rows.append({"id": f"{tag}_{uid}", "time": start[f"{tag}_{uid}"], "text": e["text"], **sc})
    sm = summary(rows)
    flagged = sorted((r for r in rows if r["pitch_sd"] < FLAG_BELOW), key=lambda r: r["time"])
    ok = sm["pitch_sd_median"] >= FAIL_BELOW
    (d / "pitch_check.json").write_text(json.dumps(
        {"fail_below": FAIL_BELOW, "flag_below": FLAG_BELOW, **sm, "passed": ok,
         "flagged": flagged}, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in flagged:
        s_ = int(r["time"])
        print(f"FLAG {r['id']} {r['pitch_sd']} semitones  {url}?t={s_} ({s_ // 60}:{s_ % 60:02d})  {r['text'][:70]!r}")
    print(f"{lesson.name}: {sm['clips']} clips, median pitch variation {sm['pitch_sd_median']} semitones "
          f"(fails below {FAIL_BELOW}); {len(flagged)} clip(s) below {FLAG_BELOW} for the ear")
    print("pitch check " + ("passed" if ok else "FAILED: the lesson sounds monotonous"))
    return 0 if ok else 1


def main() -> None:
    if "--baseline" in sys.argv:
        print(json.dumps(baseline(), indent=1))
        return
    if len(sys.argv) == 2 and Path(sys.argv[1]).is_dir():
        raise SystemExit(check_lesson(Path(sys.argv[1])))
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    if "--lesson" in sys.argv:
        clips = lesson_clips(Path(sys.argv[sys.argv.index("--lesson") + 1]))
    else:
        clips = [Path(a) for a in sys.argv[1:]]
    scores = [s for s in (score(p) for p in clips) if s]
    sm = summary(scores)
    print(json.dumps(sm, indent=1))
    print(f"baseline (Rupert, approved): median {base['pitch_sd_median']}, p25 {base['pitch_sd_p25']}, "
          f"p10 {base['pitch_sd_p10']} semitones")
    verdict = "FAIL (monotonous)" if sm["pitch_sd_median"] < base["pitch_sd_p25"] else "pass"
    print(f"median clip {sm['pitch_sd_median']} semitones: {verdict}")


if __name__ == "__main__":
    main()
