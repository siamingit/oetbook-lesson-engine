"""Word timings of the Listening recordings (ADR 030, amending ADR 029).

    .venv/Scripts/python spike/scripts/word_times.py --dry-run      # free: checks the key and fields
    .venv/Scripts/python spike/scripts/word_times.py --transcribe   # paid: Scribe on each extract
    .venv/Scripts/python spike/scripts/word_times.py --align        # free: writes the committed timings
    .venv/Scripts/python spike/scripts/word_times.py --sections <choice.json>   # free: the sections file
    .venv/Scripts/python spike/scripts/word_times.py --check        # free: the committed files still fit

The transcript a student sees is the release's own; speech-to-text gives only
the times. Each extract of the pinned sets (practice_set.LISTENING_PIN) is
transcribed once by ElevenLabs Scribe, word by word (AGENTS.md §4: no
approval needed under $5 a job); the raw response, which holds the words, is
kept outside git (data/listening-word-times/, gitignored). `--align` lines the
recognised words up with the release transcript's words and writes, per
extract, only each word's index and its start and end in the extract's own
audio file: never a word, so the public repository holds no set wording.

A transcript's WORDS (the index the times are by, and the one the player
counts in the same way): the transcript's rows in order (practice_set
.transcript_parts), each row's text with a speaker's label ("Nurse:") taken
off, split on white space. A label is not a word: it is not spoken.

Alignment is by string matching only (AGENTS.md §8): both sides lower-cased
and cut to letters and digits, then difflib's longest matching blocks. A
release word matched one to one takes its recognised word's times; a run of
release words against a run of recognised words that differ ("twenty-five"
heard as "25") shares the run's time by the words' lengths; a release word
with nothing heard against it takes the gap between its neighbours. Every
word's time is checked to rise and to sit inside the extract's segment.
The release's admin-only turn times are not used (owner, 2026-10-13).
"""

import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import practice_set                                       # noqa: E402

REPO = Path(__file__).resolve().parents[2]
RAW_DIR = REPO / "data" / "listening-word-times"            # gitignored: holds the words
TIMES_FILE = REPO / "spike" / "word_times" / "sample-tests-v2.json"
MODEL = "scribe_v2"
ENDPOINT = "https://api.elevenlabs.io/v1/speech-to-text"
MAX_USD_PER_JOB = 5.0                                      # AGENTS.md §4


def release() -> tuple[dict, Path]:
    p = practice_set.release_path(practice_set.LISTENING_PIN["release"])
    pkg = json.loads(p.read_text(encoding="utf-8"))
    if (pkg["package_id"], pkg["package_version"]) != (practice_set.LISTENING_PIN["package_id"],
                                                       practice_set.LISTENING_PIN["package_version"]):
        raise SystemExit(f"REFUSED: {p} is not the pinned Listening release")
    return pkg, p


def extracts(pkg: dict) -> list[dict]:
    """The audio extracts of the pinned sets, in set order."""
    out = []
    for s in pkg["sets"]:
        if s["set_id"] in practice_set.LISTENING_PIN["sets"]:
            for part in s["parts"]:
                out += [st for st in part["stimuli"] if practice_set.is_audio(st)]
    return out


def words_of(st: dict) -> tuple[list[str], list[int]]:
    """A transcript's words, as the player counts them, and how many each row has."""
    out, counts = [], []
    for p in practice_set.transcript_parts(st):
        text = p["text"][len(p["speaker"]) + 1:] if p.get("speaker") else p["text"]
        w = text.split()
        out += w
        counts.append(len(w))
    return out, counts


def transcript_sha(st: dict) -> str:
    return hashlib.sha256(st["transcript"]["text"].encode("utf-8")).hexdigest()


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


# ---- speech-to-text (paid) ----

def curl_cmd(with_file: Path | None, headers: Path | None = None, body: Path | None = None) -> list[str]:
    cmd = ["curl", "-sS", "--fail-with-body", "--max-time", "900", "--config", "-", "-X", "POST", ENDPOINT,
           "-H", "Accept: application/json", "-F", f"model_id={MODEL}", "-F", "language_code=en",
           "-F", "timestamps_granularity=word", "-F", "diarize=false", "-F", "tag_audio_events=false"]
    if with_file:
        cmd += ["-F", f"file=@{with_file}", "-D", str(headers), "-o", str(body)]
    return cmd


def transcribe(dry: bool) -> None:
    from transcribe import api_key, header_cost, USD_PER_1000_CREDITS
    key = api_key()
    cfg = f'header = "xi-api-key: {key}"\n'
    pkg, p = release()
    if dry:
        r = subprocess.run(curl_cmd(None), input=cfg, capture_output=True, text=True)
        print("DRY RUN (no file):", (r.stdout or r.stderr)[:400])
        return
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for st in extracts(pkg):
        src = p.parent / st["audio"]["path"]
        if practice_set._sha256(src) != st["audio"]["sha256"]:
            raise SystemExit(f"REFUSED: {src} does not match the release's sha256")
        body, headers = RAW_DIR / f"{st['stimulus_id']}.json", RAW_DIR / f"{st['stimulus_id']}.headers.txt"
        if body.exists():
            print(f"{st['stimulus_id']}: already transcribed")
            continue
        r = subprocess.run(curl_cmd(src, headers, body), input=cfg, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"{st['stimulus_id']}: curl failed {r.returncode}: {r.stdout[:300]} {r.stderr[:300]}")
        c = header_cost(headers) or 0
        total += c
        usd = c * USD_PER_1000_CREDITS / 1000
        print(f"{st['stimulus_id']}: {st['audio']['duration_s']:.0f} s, {c} credits (${usd:.3f})")
        if usd > MAX_USD_PER_JOB:
            raise SystemExit("STOP: one job cost more than $5 (AGENTS.md §4): tell the owner")
    print(f"total: {total} credits = ${total * USD_PER_1000_CREDITS / 1000:.2f}")


# ---- alignment (free) ----

def heard(st: dict) -> list[dict]:
    """The recognised words inside the extract's segment (not the announcement)."""
    raw = json.loads((RAW_DIR / f"{st['stimulus_id']}.json").read_text(encoding="utf-8"))
    seg = practice_set.segment(st, "extract")
    return [w for w in raw["words"] if w.get("type") == "word" and norm(w["text"])
            and seg["start_s"] - 0.5 <= w["start"] and w["end"] <= seg["end_s"] + 0.5]


def align(st: dict) -> dict:
    words, counts = words_of(st)
    hw = heard(st)
    a, b = [norm(w) for w in words], [norm(w["text"]) for w in hw]
    times: list[list[float] | None] = [None] * len(words)
    matched = 0
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                times[i1 + k] = [hw[j1 + k]["start"], hw[j1 + k]["end"]]
            matched += i2 - i1
        elif op == "replace":
            t0, t1 = hw[j1]["start"], hw[j2 - 1]["end"]
            lens = [max(1, len(a[i])) for i in range(i1, i2)]
            x = t0
            for k, n in enumerate(lens):
                y = t0 + (t1 - t0) * sum(lens[:k + 1]) / sum(lens)
                times[i1 + k] = [x, y]
                x = y
    # a release word with nothing heard against it: the gap between its neighbours
    seg = practice_set.segment(st, "extract")
    k = 0
    while k < len(times):
        if times[k] is not None:
            k += 1
            continue
        e = k
        while e < len(times) and times[e] is None:
            e += 1
        t0 = times[k - 1][1] if k else seg["start_s"]
        t1 = times[e][0] if e < len(times) else seg["end_s"]
        step = (t1 - t0) / (e - k)
        for n in range(k, e):
            times[n] = [t0 + step * (n - k), t0 + step * (n - k + 1)]
        k = e
    times = [[round(s, 3), round(max(s, z), 3)] for s, z in times]
    for n in range(1, len(times)):
        if times[n][0] < times[n - 1][0]:
            raise SystemExit(f"{st['stimulus_id']}: word {n}'s time goes back")
    return {"audio_sha256": st["audio"]["sha256"], "transcript_sha256": transcript_sha(st),
            "row_words": counts, "words": len(words), "matched": matched,
            "times": times}


def write_aligned() -> None:
    pkg, _ = release()
    out = {"format": "oetbook-word-times", "version": 1, "adr": "030",
           "release": {"name": practice_set.LISTENING_PIN["release"], "package_id": pkg["package_id"],
                       "package_version": pkg["package_version"]},
           "words": "a transcript's rows in order, a speaker's label taken off, split on white space "
                    "(word_times.words_of); times in seconds in the extract's own audio file",
           "stt": {"provider": "ElevenLabs", "model": MODEL, "use": "times only; the words are the release's"},
           "stimuli": {}}
    for st in extracts(pkg):
        al = align(st)
        out["stimuli"][st["stimulus_id"]] = al
        print(f"{st['stimulus_id']}: {al['words']} words, {al['matched']} matched one to one "
              f"({100 * al['matched'] / al['words']:.1f}%)")
    TIMES_FILE.parent.mkdir(parents=True, exist_ok=True)
    TIMES_FILE.write_text(json.dumps(out, separators=(",", ":")).replace('"times":', '\n"times":')
                          .replace('},"', '},\n"') + "\n", encoding="utf-8")
    print(f"written {TIMES_FILE}")


# ---- reading the committed file ----

_cache: dict = {}


def load() -> dict:
    if "f" not in _cache:
        _cache["f"] = json.loads(TIMES_FILE.read_text(encoding="utf-8")) if TIMES_FILE.exists() else {}
    return _cache["f"]


def for_stimulus(st: dict) -> dict | None:
    """An extract's word times, or None when the file has none for it or they
    were made from another transcript or another audio file."""
    w = (load().get("stimuli") or {}).get(st["stimulus_id"])
    if not w or w["audio_sha256"] != st["audio"]["sha256"] or w["transcript_sha256"] != transcript_sha(st):
        return None
    return w


def row_first_words(st: dict) -> list[int]:
    """The index of each transcript row's first word."""
    _, counts = words_of(st)
    out, k = [], 0
    for n in counts:
        out.append(k)
        k += n
    return out


ROW_PAD_S = 0.15            # a row's span starts this long before its first word (as a heard word's)


def row_times(st: dict) -> list[float] | None:
    """Each transcript row's start in the extract's file, from its first word's
    time (padded ROW_PAD_S before, never before the extract's start); None
    without word times. Replaces the release's admin turn times (owner, 2026-10-13)."""
    w = for_stimulus(st)
    if not w:
        return None
    seg = practice_set.segment(st, "extract")
    return [round(max(seg["start_s"], w["times"][k][0] - ROW_PAD_S), 3) for k in row_first_words(st)]


# ---- sections (ADR 030): the part of a talk covering one question ----
#
# Part C: a question's section runs from where the speaker signposts its point
# to where the next one is signposted; the first takes the talk's opening.
# Part A: a heading group's (the note form's heading and its gaps), from where
# the conversation turns to that heading. Part B: the whole extract. Chosen by
# the agent from the transcript (2026-10-13), stored as word indices only
# (never words), each checked to hold its own questions' evidence.

SECTIONS_FILE = REPO / "spike" / "word_times" / "sample-tests-v2.sections.json"


def sections_raw() -> dict:
    if "s" not in _cache:
        _cache["s"] = json.loads(SECTIONS_FILE.read_text(encoding="utf-8")) if SECTIONS_FILE.exists() else {}
    return _cache["s"]


def sections_for(st: dict) -> list[dict]:
    """An extract's sections in order, each {from, to (inclusive word indices),
    and its `item` (Parts B, C) or `heading` and `first_gap` (Part A)}; [] with none."""
    rows = (sections_raw().get("stimuli") or {}).get(st["stimulus_id"]) or []
    w = for_stimulus(st)
    if not rows or not w:
        return []
    n = len(w["times"])
    return [{**r, "to": (rows[k + 1]["from"] - 1 if k + 1 < len(rows) else n - 1)} for k, r in enumerate(rows)]


def find_quote(words: list[str], quote: str, labels: list[str] = ()) -> tuple[int, int] | None:
    """Where a quote of the transcript (an item's evidence) is, as word indices:
    its fragments (cut at "..." and at a speaker's label, which is not a word)
    each found, the first from its first word to the last's last; None unless
    every fragment of two words or more is found, in order."""
    for lab in sorted(labels, key=len, reverse=True):
        quote = quote.replace(lab + ":", " ... ")
    a = [norm(x) for x in words]
    at, start = None, 0
    for frag in re.split(r"\.\.\.|…", quote):
        q = [norm(x) for x in frag.split() if norm(x)]
        if len(q) < 2:
            continue
        hit = next((i for i in range(start, len(a) - len(q) + 1) if a[i:i + len(q)] == q), None)
        if hit is None:
            return None
        at = (at[0] if at else hit, hit + len(q) - 1)
        start = hit + len(q)
    return at


def check_sections(pkg: dict) -> list[str]:
    bad = []
    for s in pkg["sets"]:
        if s["set_id"] not in practice_set.LISTENING_PIN["sets"]:
            continue
        for part in s["parts"]:
            for st in part["stimuli"]:
                secs = sections_for(st)
                its = [i for i in part["items"] if i["stimulus_ids"] == [st["stimulus_id"]]]
                if not secs:
                    bad.append(f"{st['stimulus_id']}: no sections")
                    continue
                if secs[0]["from"] != 0 or any(b["from"] <= a["from"] for a, b in zip(secs, secs[1:])):
                    bad.append(f"{st['stimulus_id']}: sections do not start at 0 and rise")
                words, _ = words_of(st)
                for it in its:
                    if practice_set.is_gapfill(it):
                        heads = [x["first_gap"] for x in secs]
                        for g in practice_set.gaps_of(it):
                            k = max(n for n, f in enumerate(heads) if f <= g["number"])
                            at = find_quote(words, g.get("evidence") or "", practice_set.speakers_of(st))
                            if g.get("evidence") and not at:
                                bad.append(f"gap {g['number']}: its evidence is not found in the transcript")
                            elif at and not (secs[k]["from"] <= at[0] and at[1] <= secs[k]["to"]):
                                bad.append(f"gap {g['number']}: its evidence is outside its heading's section")
                    else:
                        sec = next((x for x in secs if x.get("item") == it["item_id"]), None)
                        at = find_quote(words, it.get("evidence") or "", practice_set.speakers_of(st))
                        if not sec:
                            bad.append(f"{it['item_id']}: no section")
                        elif it.get("evidence") and not at:
                            bad.append(f"{it['item_id']}: its evidence is not found in the transcript")
                        elif at and not (sec["from"] <= at[0] and at[1] <= sec["to"]):
                            bad.append(f"{it['item_id']}: its evidence is outside its section")
    return bad


def import_sections(path: Path) -> None:
    """Write the committed sections file from a choice file ({stimulus: [{item
    or heading and first_gap, from, why}]}); `why` (it may quote) is left out.
    Part B extracts get one section each, the whole extract."""
    pkg, _ = release()
    choice = json.loads(path.read_text(encoding="utf-8"))
    out = {"format": "oetbook-listening-sections", "version": 1, "adr": "030",
           "words": "word indices as in sample-tests-v2.json (word_times.words_of); a section runs to the "
                    "word before the next one's `from`",
           "by": "the agent, 2026-10-13: a new section where the speaker signposts the next point "
                 "(Part C), or where the conversation turns to the next heading (Part A); each checked to "
                 "hold its questions' evidence (word_times.py --check)",
           "stimuli": {}}
    for s in pkg["sets"]:
        if s["set_id"] not in practice_set.LISTENING_PIN["sets"]:
            continue
        for part in s["parts"]:
            for st in part["stimuli"]:
                if st["stimulus_id"] in choice:
                    out["stimuli"][st["stimulus_id"]] = [{k: v for k, v in r.items() if k != "why"}
                                                         for r in choice[st["stimulus_id"]]]
                elif part.get("code") == "LB":
                    it = next(i for i in part["items"] if i["stimulus_ids"] == [st["stimulus_id"]])
                    out["stimuli"][st["stimulus_id"]] = [{"item": it["item_id"], "from": 0}]
    SECTIONS_FILE.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    _cache.pop("s", None)
    print(f"written {SECTIONS_FILE}")


def check() -> list[str]:
    pkg, _ = release()
    bad = []
    for st in extracts(pkg):
        w = for_stimulus(st)
        if not w:
            bad.append(f"{st['stimulus_id']}: no word times for this transcript and audio")
            continue
        words, counts = words_of(st)
        seg = practice_set.segment(st, "extract")
        if counts != w["row_words"] or len(w["times"]) != len(words):
            bad.append(f"{st['stimulus_id']}: the word count differs")
        if any(not (seg["start_s"] - 0.6 <= s <= z <= seg["end_s"] + 0.6) for s, z in w["times"]):
            bad.append(f"{st['stimulus_id']}: a time outside the extract")
    return bad + check_sections(pkg)


def main() -> None:
    if "--dry-run" in sys.argv:
        transcribe(dry=True)
    elif "--transcribe" in sys.argv:
        transcribe(dry=False)
    elif "--align" in sys.argv:
        write_aligned()
    elif "--sections" in sys.argv:
        import_sections(Path(sys.argv[sys.argv.index("--sections") + 1]))
    elif "--check" in sys.argv:
        bad = check()
        print("\n".join(bad) or "word times: every extract fits its transcript and audio")
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
