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
    text of the set (a matching item's "Text B", which says nothing).

Words are compared as lower-case runs of letters and digits, whole words only,
so "Nil-by-mouth" matches "nil by mouth". It reports the file, the line
and the item ID with the form's place, NEVER the answer itself, since the log
of a public repository's CI is public. A form so generic that the repository
needs it in its own words ("ECG") is exempted by item ID and form number in
spike/ci/answer_check_exempt.json, with the reason; the exemption also never
names the answer. With no release, or no answer found, the check fails: it
never passes by finding nothing to compare.
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


def answers(package: dict) -> list[tuple[str, str, str]]:
    """(item id, form, normalised answer) for every answer of a release."""
    out = []
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
    packages = [Path(p) for p in sys.argv[1:]] or local_packages()
    if not packages:
        print("FAIL: no release package found; nothing was checked")
        return 1
    found = []
    for p in packages:
        found += answers(json.loads(p.read_text(encoding="utf-8")))
    if not found:
        print("FAIL: the releases hold no answer; the format may have changed")
        return 1
    spec = json.loads(EXEMPT.read_text(encoding="utf-8")) if EXEMPT.exists() else {}
    exempt = {(e["item"], e["form"]) for e in spec.get("exempt") or []}
    files = tracked_files()
    hits = find(found, files, exempt)
    print(f"{len(packages)} release(s), {len(found)} answers, {len(exempt)} exempt, "
          f"{len(files)} tracked files")
    for h in hits:
        print("FAIL: " + h)
    if hits:
        print("An answer of a practice set is in a committed file (ADR 026). Remove it, or, "
              "if the words are generic and needed, exempt that item's form in "
              "spike/ci/answer_check_exempt.json with the reason.")
        return 1
    print("no answer of any release is in a committed file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
