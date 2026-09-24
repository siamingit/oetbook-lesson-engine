"""The automatic ear: transcribe synthesised English audio with Scribe and
compare it with what the script says.

    .venv/Scripts/python spike/scripts/ear.py <lesson_dir> --page 13

Reads:  <lesson_dir>/generated/page-<N>/boards/audio_index.json and its WAVs
Writes: <lesson_dir>/generated/page-<N>/boards/ear.json

For every utterance: Scribe's transcript, a word-level agreement figure, and
for every lexicon term the script contains, whether the transcript contains
it. A lexicon term in the script but not heard is a FAILURE, reported with
the utterance id, and the exit code is non-zero.

Scribe is given no keyterms and no forced language: a reviewer that is told
what to hear will hear it. Scribe is a coarse ear: it decides what word was
said, not how a vowel was coloured, so a mispronounced term can still be
transcribed correctly. The phoneme check in synthesize_narration.py is the
fine instrument for a vowel; this one catches a term that came out as a
different word.

The API key goes to curl on stdin (--config -), never on the command line.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lexicon                                          # noqa: E402
import paths                                            # noqa: E402
from transcribe import ENDPOINT, MODEL, api_key         # noqa: E402


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


# Numbers: the script is written for the ear ("two thousand and ten", "the
# tenth of August"); Scribe writes digits ("2010", "10th of August"). Both
# sides are normalised to digits before they are compared, so a number is
# never a false disagreement.
UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten "
                                    "eleven twelve thirteen fourteen fifteen sixteen seventeen "
                                    "eighteen nineteen".split())}
TENS = {w: 10 * (i + 2) for i, w in enumerate("twenty thirty forty fifty sixty seventy "
                                              "eighty ninety".split())}
ORDINALS = {"first": 1, "second": 2, "third": 3, "fifth": 5, "eighth": 8, "ninth": 9,
            "twelfth": 12, "twentieth": 20, "thirtieth": 30}
for _w, _v in list(UNITS.items()) + list(TENS.items()):
    if _w not in ("zero", "one", "two", "three", "five", "eight", "nine", "twelve", "twenty",
                  "thirty") and _v:
        ORDINALS.setdefault(_w + "th", _v)
ORDINALS.update({"fourth": 4, "sixth": 6, "seventh": 7, "tenth": 10, "eleventh": 11,
                 "thirteenth": 13, "fourteenth": 14, "fifteenth": 15, "sixteenth": 16,
                 "seventeenth": 17, "eighteenth": 18, "nineteenth": 19})


def suffix(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def numbers_to_digits(text: str) -> list[str]:
    """Tokens with spoken numbers collapsed to digits: 'two thousand and ten'
    -> '2010', 'twenty-five' -> '25', 'tenth' -> '10th'. 'and' joins a number
    only when it sits between two number words."""
    raw = [t for t in re.split(r"\s+", text) if t]
    toks: list[str] = []
    for t in raw:
        toks += [p for p in t.lower().replace("-", " ").split() if p]
    out: list[str] = []
    total = cur = 0
    active = False
    ordinal = False

    def flush():
        nonlocal total, cur, active, ordinal
        if active:
            n = total + cur
            out.append(str(n) + (suffix(n) if ordinal else ""))
        total = cur = 0
        active = ordinal = False

    i = 0
    while i < len(toks):
        w = norm(toks[i])
        nxt = norm(toks[i + 1]) if i + 1 < len(toks) else ""
        if w in UNITS or w in TENS:
            cur += UNITS.get(w, TENS.get(w))
            active = True
        elif w == "hundred" and active:
            cur = (cur or 1) * 100
        elif w == "thousand" and active:
            total += (cur or 1) * 1000
            cur = 0
        elif w in ORDINALS and (active or True):
            cur += ORDINALS[w]
            active = ordinal = True
            flush()
        elif w == "and" and active and (nxt in UNITS or nxt in TENS or nxt in ORDINALS):
            pass
        else:
            flush()
            if w:
                out.append(w)
        i += 1
    flush()
    return out


def transcribe_file(path: Path, key: str) -> dict:
    cmd = ["curl", "-sS", "--fail-with-body", "--max-time", "300", "--config", "-",
           "-F", f"model_id={MODEL}", "-F", f"file=@{path}", ENDPOINT]
    r = subprocess.run(cmd, input=f'header = "xi-api-key: {key}"\n', capture_output=True,
                       text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit(f"curl failed for {path.name}: {r.stdout[:300]} {r.stderr[:300]}")
    return json.loads(r.stdout)


def agreement(script: str, heard: str) -> float:
    """Share of script words found in the transcript, in order. Rough: the ear
    is for terms; this figure only flags an utterance that came out badly."""
    s = numbers_to_digits(script)
    h = numbers_to_digits(heard)
    i = 0
    hit = 0
    for w in s:
        try:
            i = h.index(w, i) + 1
            hit += 1
        except ValueError:
            pass
    return hit / max(1, len(s))


def listen(lesson: Path, page: int, only_terms: bool = False, reuse: bool = False) -> dict:
    lex = lexicon.load()
    out_dir = paths.boards_dir(lesson, page)
    index = json.loads((out_dir / "audio_index.json").read_text(encoding="utf-8"))
    key = api_key()
    previous: dict[str, dict] = {}
    if reuse and (out_dir / "ear.json").exists():
        old = json.loads((out_dir / "ear.json").read_text(encoding="utf-8"))
        previous = {r["id"]: r for r in old["utterances"]}
    results = []
    failures = []
    for uid, e in index.items():
        terms = lexicon.terms_in(e["text"], lex)
        if only_terms and not terms:
            continue
        # --recompare reuses a transcript already on disk for the same audio
        # file, so a change to the comparison costs no transcription.
        prev = previous.get(uid)
        if prev and prev.get("file") == e["file"]:
            heard = {"text": prev["heard"], "language_code": prev.get("language"),
                     "language_probability": prev.get("language_probability")}
        else:
            heard = transcribe_file(out_dir / e["file"], key)
        text = heard.get("text", "")
        heard_norm = " " + " ".join(norm(w) for w in text.split()) + " "
        missing = [t for t in terms if " " + norm(t) + " " not in heard_norm
                   and norm(t) not in heard_norm.replace(" ", "")]
        r = {"id": uid, "file": e["file"], "terms": terms, "missing": missing, "heard": text,
             "agreement": round(agreement(e["text"], text), 3),
             "language": heard.get("language_code"),
             "language_probability": heard.get("language_probability")}
        results.append(r)
        for t in missing:
            failures.append(f"{uid}: lexicon term {t!r} not heard; Scribe heard: {text!r}")
        print(f"  {uid:>10}  agree {r['agreement']:.0%}  terms {terms}  "
              f"{'MISSING ' + str(missing) if missing else ''}")
    report = {"model": MODEL, "lexicon_version": lex["version"], "utterances": results,
              "failures": failures}
    (out_dir / "ear.json").write_text(json.dumps(report, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--only-terms", action="store_true",
                        help="transcribe only utterances that contain a lexicon term")
    parser.add_argument("--recompare", action="store_true",
                        help="reuse transcripts in ear.json for unchanged audio files")
    args = parser.parse_args()
    report = listen(args.lesson_dir, args.page, args.only_terms, args.recompare)
    low = [r for r in report["utterances"] if r["agreement"] < 0.8]
    print(f"heard {len(report['utterances'])} utterances; "
          f"{len(low)} below 80% word agreement")
    for r in low:
        print(f"  LOW {r['id']} {r['agreement']:.0%}: heard {r['heard']!r}")
    for f in report["failures"]:
        print("FAIL: " + f)
    if report["failures"]:
        raise SystemExit(f"{len(report['failures'])} lexicon term(s) not heard")
    print("ear: every lexicon term in the script was heard")


if __name__ == "__main__":
    main()
