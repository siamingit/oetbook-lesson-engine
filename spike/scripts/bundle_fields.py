"""List every field path and type value in the approved lessons' bundles, and
check that a format changelog covers every one that 1.12 does not have.

    python spike/scripts/bundle_fields.py                 # the check
    python spike/scripts/bundle_fields.py --list          # every path, by version

The baseline is what the approved 1.12 bundles hold (bundle.json and
text.json). Every path, JSON type and enumerated value found in a newer
approved bundle and not in the baseline must be listed in the changelog's
`fields` block (docs/bundle-format-changelog.md), with the version that
introduced it; a listed version later than the earliest bundle holding the
path is an error too. Read-only: it writes nothing.

Paths: `blocks.*` is any block; `[]` any element of a list; `*` any key of a
map keyed by ids (a board's or a state's `reveal`, a board's `pinned`).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

LESSONS = Path(r"C:\OET\lessons")
REPO_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = REPO_ROOT / "docs" / "bundle-format-changelog.md"
BASELINE = "1.12"

# maps keyed by ids, not by field names
ID_MAPS = {"bundle.blocks", "bundle.boards[].reveal", "bundle.boards[].pinned",
           "bundle.boards[].states[].reveal"}
# keys whose string values are an enumeration: a new value is a format change
ENUM_KEYS = {"type", "kind", "text_type", "style", "role", "flow", "provenance",
             "verdict", "cls", "family", "side", "zoom", "from_class", "to_class"}


def vkey(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def jtype(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    return "object"


def walk(v, path: str, paths: dict, values: dict) -> None:
    paths[path].add(jtype(v))
    if isinstance(v, dict):
        for k, x in v.items():
            sub = f"{path}.*" if path in ID_MAPS else f"{path}.{k}"
            if path not in ID_MAPS and k in ENUM_KEYS and isinstance(x, str):
                values[sub].add(x)
            walk(x, sub, paths, values)
    elif isinstance(v, list):
        for x in v:
            walk(x, f"{path}[]", paths, values)


def approved_lessons(lib: Path) -> list[Path]:
    out = []
    for d in sorted(lib.iterdir()):
        gates = d / "analysis" / "gates.json"
        bundle = d / "generated" / "lesson-player" / "bundle.json"
        if not (gates.exists() and bundle.exists()):
            continue
        final = json.loads(gates.read_text(encoding="utf-8")).get("final")
        if final and final.get("by"):
            out.append(d)
    return out


def collect(lessons: list[Path]):
    """{path: {version: [lesson, ...]}}, {path: {jtype: min version}},
    {(path, value): {version: [lesson, ...]}}"""
    where = defaultdict(lambda: defaultdict(list))
    types = defaultdict(dict)
    vwhere = defaultdict(lambda: defaultdict(list))
    for d in lessons:
        folder = d / "generated" / "lesson-player"
        bundle = json.loads((folder / "bundle.json").read_text(encoding="utf-8"))
        ver = bundle["format_version"]
        for name, root in (("bundle", bundle),
                           ("text", json.loads((folder / "text.json").read_text(encoding="utf-8")))):
            paths, values = defaultdict(set), defaultdict(set)
            walk(root, name, paths, values)
            for p, ts in paths.items():
                where[p][ver].append(d.name)
                for t in ts:
                    old = types[p].get(t)
                    if old is None or vkey(ver) < vkey(old):
                        types[p][t] = ver
            for p, vs in values.items():
                for v in vs:
                    vwhere[(p, v)][ver].append(d.name)
    return where, types, vwhere


def listed() -> list[tuple[str, str, str, object]]:
    """The changelog's `fields` block, one entry a line: `<version> <path>` (a new
    path), `<version> <path> : <JSON type>` (a new type on an older path),
    `<version> <path> = <JSON value>` (a new enumerated value) or
    `<version> <path> ~ <JSON string, a regular expression>` (free-text values
    that match it). Returns [(version, kind, path, what)]."""
    text = CHANGELOG.read_text(encoding="utf-8")
    m = re.search(r"```fields\n(.*?)```", text, re.S)
    if not m:
        sys.exit(f"no ```fields block in {CHANGELOG}")
    out = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        ver, rest = line.split(None, 1)
        for sep, kind in ((" = ", "value"), (" ~ ", "pattern"), (" : ", "type")):
            if sep in rest:
                p, w = rest.split(sep, 1)
                out.append((ver, kind, p.strip(), w.strip() if kind == "type" else json.loads(w)))
                break
        else:
            out.append((ver, "path", rest.strip(), None))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="print every path not in the baseline")
    ap.add_argument("--lessons", default=str(LESSONS), help="the lesson library")
    a = ap.parse_args()

    lessons = approved_lessons(Path(a.lessons))
    where, types, vwhere = collect(lessons)
    base_paths = {p for p, vs in where.items() if BASELINE in vs}
    base_types = {(p, t) for p, ts in types.items() for t, v in ts.items() if v == BASELINE}
    base_values = {k for k, vs in vwhere.items() if BASELINE in vs}

    def first(vs: dict) -> str:
        return min(vs, key=vkey)

    def lessons_of(vs: dict) -> str:
        return ", ".join(sorted({l for ls in vs.values() for l in ls}))

    new_paths = {p: where[p] for p in where if p not in base_paths}
    new_types = {(p, t): v for p, ts in types.items() for t, v in ts.items()
                 if p in base_paths and (p, t) not in base_types}
    new_values = {k: vwhere[k] for k in vwhere if k not in base_values}

    versions = sorted({v for vs in where.values() for v in vs}, key=vkey)
    print(f"{len(lessons)} approved lessons; versions {', '.join(versions)}")
    print(f"not in {BASELINE}: {len(new_paths)} paths, {len(new_types)} types widened, "
          f"{len(new_values)} enumerated values")

    if a.list:
        for p in sorted(new_paths, key=lambda p: (vkey(first(new_paths[p])), p)):
            print(f"{first(new_paths[p])} {p}   [{lessons_of(new_paths[p])}]")
        for (p, t), v in sorted(new_types.items(), key=lambda x: (vkey(x[1]), x[0])):
            print(f"{v} {p} : {t}")
        for (p, val), vs in sorted(new_values.items(), key=lambda x: (vkey(first(x[1])), x[0])):
            print(f"{first(vs)} {p} = {json.dumps(val)}   [{lessons_of(vs)}]")
        return 0

    doc = listed()
    doc_paths = {p: v for v, k, p, _ in doc if k == "path"}
    doc_types = {(p, w): v for v, k, p, w in doc if k == "type"}
    doc_values = {(p, w): v for v, k, p, w in doc if k == "value"}
    doc_patterns = [(p, re.compile(w), v) for v, k, p, w in doc if k == "pattern"]

    def value_version(p: str, val: str):
        if (p, val) in doc_values:
            return doc_values[(p, val)]
        return next((v for q, rx, v in doc_patterns if q == p and rx.search(val)), None)

    problems = []
    for p, vs in new_paths.items():
        if p not in doc_paths:
            problems.append(f"uncovered path: {first(vs)} {p}")
        elif vkey(doc_paths[p]) > vkey(first(vs)):
            problems.append(f"listed as {doc_paths[p]} but in a {first(vs)} bundle: {p}")
    for (p, t), v in new_types.items():
        if (p, t) not in doc_types:
            problems.append(f"uncovered type: {v} {p} : {t}")
        elif vkey(doc_types[(p, t)]) > vkey(v):
            problems.append(f"listed as {doc_types[(p, t)]} but in a {v} bundle: {p} : {t}")
    for (p, val), vs in new_values.items():
        lv = value_version(p, val)
        if lv is None:
            # a provenance is not printed: a free-text one may hold lesson words
            shown = "" if p.endswith(".provenance") else f" = {json.dumps(val)}"
            problems.append(f"uncovered value: {first(vs)} {p}{shown} (in {lessons_of(vs)})")
        elif vkey(lv) > vkey(first(vs)):
            problems.append(f"listed as {lv} but in a {first(vs)} bundle: {p} = {json.dumps(val)}")
    unused = [f"{v} {p}" for p, v in doc_paths.items() if p not in where]
    unused += [f"{v} {p} = {json.dumps(val)}" for (p, val), v in doc_values.items()
               if (p, val) not in vwhere]
    for u in sorted(unused, key=lambda x: (vkey(x.split()[0]), x)):
        print(f"listed, in no approved bundle: {u}")
    for x in problems:
        print(x)
    print(f"uncovered: {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
