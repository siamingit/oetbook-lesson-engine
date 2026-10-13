"""No answer of an exercises release in a committed file (maintainer, 2026-10-06).

    .venv/Scripts/python spike/scripts/check_release_answers.py [PACKAGE_JSON ...]

The practice sets live in the private repository siamingit/oetacademy-exercises
and are released as `package.json` packages; this repository is public, and
ADR 026 keeps set content out of it. This check reads every answer of every
release given (by default the local copies under
%LOCALAPPDATA%\\oetacademy-exercises\\releases\\*), and fails if one appears in
any file git tracks:

  - a typed item (`text`): every accepted form;
  - a choice item: the key option's text, except where the option names a
    text of the set (a matching item's "Text B", which says nothing);
  - a gap of a Listening Part A gap-fill item (ADR 029): every accepted form
    and every accepted misspelling, by the gap's ID;
  - a Listening transcript (ADR 029): any run of RUN_WORDS words of it in a row,
    across the lines of a file, by the extract's ID and the run's place.

Words are compared as lower-case runs of letters and digits, whole words only,
so "Nil-by-mouth" matches "nil by mouth". It reports the file, the line
and the item ID with the form's place, NEVER the answer or the transcript's
words, since the log of a public repository's CI is public. A form so generic
that the repository needs it in its own words ("ECG") is exempted by item ID
and form number in spike/ci/answer_check_exempt.json, with the reason (a
transcript run by the extract's ID and "run@<word>"); the exemption also never
names the answer. With no release, or no answer found, the check fails: it
never passes by finding nothing to compare.

    --files PATH ...   check these files instead of the files git tracks (a
                       planted test; the releases are then the local copies)
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXEMPT = ROOT / "spike" / "ci" / "answer_check_exempt.json"


def norm(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def items_of(obj):
    if isinstance(obj, dict):
        if "item_id" in obj and "scoring" in obj:
            yield obj
        for v in obj.values():
            yield from items_of(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from items_of(v)


def gaps_of(obj):
    """Every gap of a gap-fill item (Listening Part A): it has a `gap_id` and
    its own `scoring`, and no `item_id`."""
    if isinstance(obj, dict):
        if "gap_id" in obj and "scoring" in obj:
            yield obj
        for v in obj.values():
            yield from gaps_of(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from gaps_of(v)


def answers(package: dict) -> list[tuple[str, str, str]]:
    """(item id, form, normalised answer) for every answer of a release."""
    out = []
    for g in gaps_of(package):
        sc = g["scoring"] or {}
        for n, form in enumerate(sc.get("accepted") or []):
            out.append((g["gap_id"], f"accepted[{n}]", norm(form)))
        for n, form in enumerate(sc.get("accepted_misspellings") or []):
            out.append((g["gap_id"], f"misspelling[{n}]", norm(form if isinstance(form, str) else
                                                                   (form or {}).get("text") or "")))
    for it in items_of(package):
        sc = it["scoring"] or {}
        if it.get("type") == "text":
            for n, form in enumerate(sc.get("accepted") or []):
                out.append((it["item_id"], f"accepted[{n}]", norm(form)))
        elif sc.get("key_option_id"):
            opt = next((o for o in it.get("options") or []
                        if o.get("option_id") == sc["key_option_id"]), None)
            if opt and not opt.get("stimulus_id"):
                out.append((it["item_id"], "key", norm(opt.get("text") or "")))
    return [a for a in out if a[2]]


# A transcript's words are set content (ADR 029): any run of this many words of
# it in a row, in a committed file, fails. Eight is long enough that the
# repository's own sentences do not repeat a transcript by chance, and short
# enough to catch a quoted line.
RUN_WORDS = 8


def stimuli_of(obj):
    if isinstance(obj, dict):
        if "stimulus_id" in obj and isinstance(obj.get("transcript"), dict):
            yield obj
        for v in obj.values():
            yield from stimuli_of(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from stimuli_of(v)


def transcript_runs(package: dict) -> dict[tuple[str, ...], tuple[str, str]]:
    """Every run of RUN_WORDS words of every transcript of a release, within one
    line (a turn), a speaker's label left out: {words: (extract id, "run@<word>")}."""
    out: dict[tuple[str, ...], tuple[str, str]] = {}
    for st in stimuli_of(package):
        labels = sorted((s.get("label") or "" for s in st.get("speakers") or []), key=len, reverse=True)
        at = 0
        for line in (st["transcript"].get("text") or "").split("\n"):
            who = next((x for x in labels if x and line.startswith(x + ":")), None)
            words = norm(line[len(who) + 1:] if who else line).split()
            for k in range(len(words) - RUN_WORDS + 1):
                out.setdefault(tuple(words[k:k + RUN_WORDS]), (st["stimulus_id"], f"run@{at + k}"))
            at += len(words)
    return out


def find_runs(runs: dict[tuple[str, ...], tuple[str, str]], files: list[Path],
              exempt: set[tuple[str, str]]) -> list[str]:
    """Where a file holds a run of a transcript, across its lines: the file and
    the line where the run starts, the extract's ID and the run's place; one
    finding for each stretch of overlapping runs."""
    hits = []
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        words, line_of = [], []
        for n, line in enumerate(lines, 1):
            for w in norm(line).split():
                words.append(w)
                line_of.append(n)
        last_end = -1
        for k in range(len(words) - RUN_WORDS + 1):
            got = runs.get(tuple(words[k:k + RUN_WORDS]))
            if not got or got in exempt:
                continue
            if k > last_end:
                where = (path.relative_to(ROOT) if path.is_relative_to(ROOT) else path).as_posix()
                hits.append(f"{where}:{line_of[k]}: a run of {RUN_WORDS} words of the transcript of "
                            f"{got[0]} ({got[1]})")
            last_end = k + RUN_WORDS - 1
    return hits


def local_packages() -> list[Path]:
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "oetacademy-exercises" / "releases"
    return sorted(base.glob("*/oa-pkg-*/package.json"))


def tracked_files() -> list[Path]:
    names = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True,
                           check=True).stdout.decode("utf-8").split("\0")
    return [ROOT / n for n in names if n]


def find(answers_: list[tuple[str, str, str]], files: list[Path],
         exempt: set[tuple[str, str]]) -> list[str]:
    pats = [(i, f, re.compile(r"(?<![a-z0-9])" + re.escape(a) + r"(?![a-z0-9])"))
            for i, f, a in answers_ if (i, f) not in exempt]
    hits = []
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue                          # binary, or not on disk
        for n, line in enumerate(lines, 1):
            low = norm(line)
            for item, form, pat in pats:
                if pat.search(low):
                    where = (path.relative_to(ROOT) if path.is_relative_to(ROOT) else path).as_posix()
                    hits.append(f"{where}:{n}: "
                                f"an answer of {item} ({form})")
    return hits


def main() -> int:
    args = sys.argv[1:]
    given = []
    if "--files" in args:
        given = [Path(p) for p in args[args.index("--files") + 1:]]
        args = args[:args.index("--files")]
    packages = [Path(p) for p in args] or local_packages()
    if not packages:
        print("FAIL: no release package found; nothing was checked")
        return 1
    found, runs = [], {}
    for p in packages:
        pkg = json.loads(p.read_text(encoding="utf-8"))
        found += answers(pkg)
        for k, v in transcript_runs(pkg).items():
            runs.setdefault(k, v)
    if not found:
        print("FAIL: the releases hold no answer; the format may have changed")
        return 1
    spec = json.loads(EXEMPT.read_text(encoding="utf-8")) if EXEMPT.exists() else {}
    exempt = {(e["item"], e["form"]) for e in spec.get("exempt") or []}
    files = given or tracked_files()
    found = list(dict.fromkeys(found))            # a form in several releases is looked for once
    hits = find(found, files, exempt) + find_runs(runs, files, exempt)
    print(f"{len(packages)} release(s), {len(found)} answers, {len(runs)} transcript runs of "
          f"{RUN_WORDS} words, {len(exempt)} exempt, {len(files)} {'given' if given else 'tracked'} files")
    for h in hits:
        print("FAIL: " + h)
    if hits:
        print("An answer or transcript words of a practice set are in a committed file (ADR 026, "
              "ADR 029). Remove them, or, if the words are generic and needed, exempt that "
              "item's form in spike/ci/answer_check_exempt.json with the reason.")
        return 1
    print("no answer and no transcript words of any release are in a committed file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
