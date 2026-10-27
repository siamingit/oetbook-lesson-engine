"""Prove that restyling a built lesson changed its look only (ADR 043).

    .venv/Scripts/python spike/scripts/restyle_proof.py snapshot <lesson_dir> <before_dir>
    (restyle the lesson: build_sections.py --style c, then the free stages)
    .venv/Scripts/python spike/scripts/restyle_proof.py compare <before_dir> <lesson_dir>
        [--rendered <render_compare snapshot>/<lesson>] [--report FILE]
    .venv/Scripts/python spike/scripts/restyle_proof.py extend <lesson_dir> <before_dir>
        (adds a data file a snapshot lacks, only while the lesson's file is still the one it recorded)

`snapshot` records the lesson as it is: the SHA-256 of every file (a recording,
`source/video.*`, by its size and time only) and a copy of the data files the
proof reads in depth. It writes only into <before_dir>.

`compare` fails unless the lesson differs from the snapshot only in what a
restyle may change (ADR 043): `lesson.style` in sections.json; the look
(`blocks.css`, the players, the classes, attributes and empty or wrapping
elements style C adds to a block's html, `ATTRS` and `CLASS_TOKENS` below); the bundle's
`effects`, its format version and `lesson.style`; and the fit (fit.json, a
table's `font`, a picture's `size`, a state's `clears` and `overlay`, a board's `tight`, a
question board's `split`); and a table's spotlight by cell (a focus entry's `cells`).
Everything else must be identical: narration text, cues, every audio file and
its timing, board and state times, ids, section titles and order, the words on
every board and their order, glosses, images and practice items. Deterministic,
no model, no network. Exit 1 on any difference that is not allowed.
"""

import copy
import hashlib
import html as _html
import json
import os
import re
import shutil
import sys
from pathlib import Path

VIDEO = {".mp4", ".mkv", ".mov", ".webm"}
# the data files read in depth (copied by `snapshot`)
DEEP = ["analysis/sections.json", "analysis/decisions.md", "analysis/fit.json", "analysis/fit-silent.json",
        "generated/lesson-player/bundle.json", "generated/lesson-player/text.json",
        "generated/lesson-player/timeline.json", "generated/lesson-player/audio_index.json",
        "generated/lesson-preview/silent/bundle.json", "generated/lesson-preview/silent/text.json",
        "generated/lesson-preview/silent/timeline.json", "generated/lesson-preview/silent/audio_index.json"]
DEEP_GLOBS = ["analysis/screens/**/screens.json", "analysis/narration/**/narration.json",
              "analysis/screens/lesson-boards.json"]
# files a restyle may rewrite (their content is checked below where it matters)
MAY_CHANGE = [
    r"analysis/sections\.json",                      # lesson.style only (checked)
    r"analysis/fit(-silent)?\.json",                 # the fit
    r"analysis/decisions\.md",                       # entries appended only (checked)
    r"analysis/screens/lesson-preview/index\.html",  # the screens preview page (the look)
    r"generated/lesson-player/(bundle|text|timeline)\.json",  # checked in depth
    r"generated/lesson-preview/silent/(bundle|text|timeline|audio_index)\.json",
    r"analysis/screens/[^/]+/screens\.json",        # the introduction's only, lesson.style only (checked)
    r"generated/lesson-player/(blocks\.css|player\.html)",
    r"generated/lesson-preview/silent/(blocks\.css|player\.html)",
    r"generated/lesson-player/[a-z_]+_check\.json",  # the checks' own reports
    r"generated/lesson-preview/silent/[a-z_]+_check\.json",
    r"analysis/[a-z_]+_check\.json",
]
MAY_CHANGE_RE = re.compile("^(?:" + "|".join(MAY_CHANGE) + ")$")

# What style C may add to a block's html (style_c.py): attributes, class tokens,
# and elements that hold no words (empty decorative ones) or only wrap words
# already there (a contents item's parts, `cp`).
ATTRS = ("data-tone", "data-crit", "data-mono", "data-mono-len", "data-label", "data-bin", "data-yes", "data-l")
CLASS_TOKENS = re.compile(r"^(lay|lay-[a-z]+|n2|n4|crit|num|parts)$")
ATTR_RE = re.compile(r'\s(?:' + "|".join(re.escape(a) for a in ATTRS) + r')="[^"]*"')
CLASS_RE = re.compile(r'class="([^"]*)"')
EMPTY_DECOR = re.compile(r'<span class="(?:pts|kset|lanes)" aria-hidden="true">(?:<i[^>]*></i>)*</span>')
CP_RE = re.compile(r'<span class="cp">(.*?)</span>', re.S)
FIT_TF = re.compile(r"--tf:[0-9.]+cqh")
FIT_PH = re.compile(r'\sstyle="--ph:[0-9.]+cqh"')     # a picture set smaller by the fit


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(L: Path) -> dict:
    out = {}
    for dirpath, _dirs, files in os.walk(L):
        for f in files:
            p = Path(dirpath) / f
            rel = p.relative_to(L).as_posix()
            st = p.stat()
            if p.suffix.lower() in VIDEO and rel.startswith("source/"):
                out[rel] = f"size:{st.st_size}:mtime:{st.st_mtime_ns}"
            else:
                out[rel] = sha(p)
    return out


def deep_files(L: Path) -> list[str]:
    rels = [r for r in DEEP if (L / r).exists()]
    for g in DEEP_GLOBS:
        rels += [p.relative_to(L).as_posix() for p in L.glob(g)]
    return sorted(set(rels))


def snapshot(L: Path, out: Path) -> None:
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"REFUSED: {out} is not empty (a snapshot is never overwritten)")
    (out / "files").mkdir(parents=True, exist_ok=True)
    for rel in deep_files(L):
        t = out / "files" / rel
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(L / rel, t)
    m = manifest(L)
    (out / "manifest.json").write_text(json.dumps({"lesson": L.name, "files": m}, indent=0), encoding="utf-8")
    print(f"{L.name}: snapshot of {len(m)} files in {out}")


def extend(L: Path, out: Path) -> None:
    """Copy into a snapshot a data file it lacks (a file DEEP gained after the
    snapshot was taken), only while the lesson's file is still exactly the one
    the snapshot's manifest recorded."""
    m = json.loads((out / "manifest.json").read_text(encoding="utf-8"))["files"]
    n = 0
    for rel in deep_files(L):
        t = out / "files" / rel
        if t.exists():
            continue
        if m.get(rel) != sha(L / rel):
            raise SystemExit(f"REFUSED: {L.name}/{rel} changed since the snapshot; it cannot be added")
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(L / rel, t)
        n += 1
    print(f"{L.name}: {n} file(s) added to the snapshot, each matching its recorded SHA-256")


# ---------------------------------------------------------------------------
# the comparison
# ---------------------------------------------------------------------------
def norm_html(h: str) -> str:
    """A block's html with everything style C may add taken away, and the fit's
    text size replaced by a placeholder."""
    h = EMPTY_DECOR.sub("", h)
    h = CP_RE.sub(lambda m: m.group(1), h)
    h = ATTR_RE.sub("", h)

    def cls(m):
        toks = [t for t in m.group(1).split() if not CLASS_TOKENS.match(t)]
        return 'class="' + " ".join(toks) + '"'
    h = CLASS_RE.sub(cls, h)
    return FIT_PH.sub("", FIT_TF.sub("--tf:*", h))


TAGS = re.compile(r"<[^>]+>")


def words(h: str) -> str:
    return _html.unescape(TAGS.sub("", h))


class Proof:
    def __init__(self):
        self.fails: list[str] = []
        self.allowed: dict[str, int] = {}

    def fail(self, msg: str):
        self.fails.append(msg)

    def allow(self, what: str, n: int = 1):
        self.allowed[what] = self.allowed.get(what, 0) + n


def diff_keys(a: dict, b: dict, where: str, allowed: set, p: Proof, label: str) -> None:
    for k in sorted(set(a) | set(b)):
        if k in allowed:
            continue
        if a.get(k, "<absent>") != b.get(k, "<absent>"):
            p.fail(f"{where}: {label} field {k!r} changed")


def check_sections(a: dict, b: dict, p: Proof) -> None:
    la, lb = dict(a.get("lesson") or {}), dict(b.get("lesson") or {})
    if lb.get("style") != "c":
        p.fail("sections.json: lesson.style is not \"c\"")
    for k in ("style", "style_by"):
        if k not in la:
            lb.pop(k, None)
    if la != lb:
        p.fail("sections.json: lesson changed beyond style")
    ra = {k: v for k, v in a.items() if k != "lesson"}
    rb = {k: v for k, v in b.items() if k != "lesson"}
    if ra != rb:
        p.fail("sections.json: changed beyond lesson.style: "
               + ", ".join(k for k in sorted(set(ra) | set(rb)) if ra.get(k) != rb.get(k)))
    else:
        p.allow("sections.json lesson.style")


def check_bundle(a: dict, b: dict, p: Proof, where: str) -> None:
    if b.get("format_version") != "1.22":
        p.fail(f"{where}: format_version {b.get('format_version')!r}, not 1.22")
    elif a.get("format_version") != "1.22":
        p.allow(f"{where} format_version {a.get('format_version')} -> 1.22")
    diff_keys(a, b, where, {"format_version", "lesson", "boards", "blocks"}, p, "top-level")
    la, lb = dict(a.get("lesson") or {}), dict(b.get("lesson") or {})
    if lb.pop("style", None) != "c":
        p.fail(f"{where}: lesson.style is not \"c\"")
    la.pop("style", None)
    if la != lb:
        p.fail(f"{where}: lesson changed beyond style: "
               + ", ".join(k for k in sorted(set(la) | set(lb)) if la.get(k) != lb.get(k)))
    # blocks: the same ids, the same fields, the same words; html only as style C draws it
    ba, bb = a.get("blocks") or {}, b.get("blocks") or {}
    if list(ba) != list(bb):
        p.fail(f"{where}: block ids or their order changed")
    for bid in ba:
        if bid not in bb:
            continue
        x, y = ba[bid], bb[bid]
        diff_keys(x, y, f"{where} block {bid}", {"html", "font", "size"}, p, "block")
        if x.get("font") != y.get("font"):
            p.allow(f"{where}: a table's text size (the fit)")
        if x.get("size") != y.get("size"):
            p.allow(f"{where}: a picture's size (the fit)")
        hx, hy = x.get("html") or "", y.get("html") or ""
        if words(hx) != words(hy):
            p.fail(f"{where} block {bid}: its words changed")
        elif norm_html(hx) != norm_html(hy):
            p.fail(f"{where} block {bid}: its html changed beyond what style C adds")
        elif hx != hy:
            p.allow(f"{where}: block html with style C's classes and attributes")
    # boards and states: identical but for the fit and the effects
    da, db = a.get("boards") or [], b.get("boards") or []
    if [d["id"] for d in da] != [d["id"] for d in db]:
        p.fail(f"{where}: board ids or their order changed")
        return
    for x, y in zip(da, db):
        diff_keys(x, y, f"{where} board {x['id']}", {"states", "tight", "split", "focus"}, p, "board")
        if norm_focus(x.get("focus")) != norm_focus(y.get("focus")):
            p.fail(f"{where} board {x['id']}: board field 'focus' changed beyond the spotlight by cell")
        elif x.get("focus") != y.get("focus"):
            p.allow(f"{where}: a table spotlit by cell (1.22)")
        if x.get("tight") != y.get("tight"):
            p.allow(f"{where}: a board's tightness (the fit)")
        if x.get("split") != y.get("split"):
            p.allow(f"{where}: a question board's column split (the fit)")
        sa, sb = x.get("states") or [], y.get("states") or []
        if [s["id"] for s in sa] != [s["id"] for s in sb]:
            p.fail(f"{where} board {x['id']}: state ids or their order changed")
            continue
        for s, t in zip(sa, sb):
            diff_keys(s, t, f"{where} state {s['id']}", {"effects", "clears", "overlay"}, p, "state")
            if (s.get("clears") or []) != (t.get("clears") or []):
                p.allow(f"{where}: a state's clears (the fit)")
            if s.get("overlay") != t.get("overlay"):
                p.allow(f"{where}: a gloss over the question column (the fit)")
            fx = t.get("effects")
            if fx is None:
                p.fail(f"{where} state {s['id']}: no effects in a style C bundle")
            else:
                if s.get("effects") not in (None, fx):
                    p.allow(f"{where}: a state's effects rewritten")
                for e in fx:
                    p.allow(f"{where}: effect {e['type']}")


def check_text(a: dict, b: dict, p: Proof, where: str) -> None:
    a, b = copy.deepcopy(a), copy.deepcopy(b)
    for d in (a, b):
        d.pop("format_version", None)
        if isinstance(d.get("lesson"), dict):
            d["lesson"].pop("style", None)
    if a != b:
        p.fail(f"{where}: changed beyond its format version")


def strip(x, keys: tuple):
    """A copy of a JSON value without the named keys, at any depth."""
    if isinstance(x, dict):
        return {k: strip(v, keys) for k, v in x.items() if k not in keys}
    if isinstance(x, list):
        return [strip(v, keys) for v in x]
    return x


def norm_focus(focus: list | None) -> list:
    """A board's spotlight as rule 11 states it without the cells (1.22, ADR 043
    decision 17): `cells` taken away, and an entry that only repeats the row and
    cell before it (one added where an arrow's target lights) dropped."""
    out = []
    for f in focus or []:
        g = {k: v for k, v in f.items() if k != "cells"}
        if out and (out[-1]["row"], out[-1]["col"]) == (g["row"], g["col"]):
            continue
        out.append(g)
    return out


def with_norm_focus(x):
    if isinstance(x, dict):
        return {k: (norm_focus(v) if k == "focus" else with_norm_focus(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [with_norm_focus(v) for v in x]
    return x


def check_timeline(a: dict, b: dict, p: Proof, where: str) -> None:
    """A timeline mirrors the bundle's boards and states: identical but for each
    state's `effects` (added), and what the fit writes: a state's `clears` and
    `overlay`, a board's `tight` and a question board's `split`."""
    FIT = ("effects", "clears", "tight", "split", "overlay")
    a, b = with_norm_focus(a), with_norm_focus(b)
    if strip(a, FIT) != strip(b, FIT):
        p.fail(f"{where}: changed beyond the effects and the fit")
    elif strip(a, ("effects",)) != strip(b, ("effects",)):
        p.allow(f"{where}: a state's clears or a board's tightness (the fit)")


def check_intro_screens(a: dict, b: dict, p: Proof, where: str) -> None:
    """The introduction's screens.json (build_lesson_boards.py) carries the
    lesson's config as `lesson_title`: it may gain lesson.style, nothing else."""
    if not (a.get("section") or {}).get("intro"):
        p.fail(f"{where}: a section's screens changed")
        return
    a, b = copy.deepcopy(a), copy.deepcopy(b)
    for k in ("style", "style_by"):
        if k not in (a.get("lesson_title") or {}):
            (b.get("lesson_title") or {}).pop(k, None)
    if a != b:
        p.fail(f"{where}: the introduction's boards changed beyond lesson.style")


def decisions_ok(before: bytes, after: bytes) -> bool:
    return after.startswith(before.rstrip(b"\r\n"))


SILENT = "generated/lesson-preview/silent"


def compare(before: Path, L: Path, rendered: Path | None = None) -> dict:
    """The proof. `rendered` is the lesson's folder in a render_compare snapshot
    taken on the code before the change (its `files/`): where the lesson's own
    silent preview was older than its narration (docs/03-RUNBOOK.md, "Known
    items"), the restyled preview is compared with that re-render, since the
    restyle re-renders it from the current narration too."""
    p = Proof()
    snap = json.loads((before / "manifest.json").read_text(encoding="utf-8"))
    if snap["lesson"] != L.name:
        raise SystemExit(f"REFUSED: the snapshot is of {snap['lesson']}, not {L.name}")
    ma, mb = snap["files"], manifest(L)
    changed = []
    for rel in sorted(set(ma) | set(mb)):
        if ma.get(rel) == mb.get(rel):
            continue
        if rel not in mb:
            p.fail(f"file removed: {rel}")
        elif not MAY_CHANGE_RE.match(rel):
            p.fail(f"file {'added' if rel not in ma else 'changed'}: {rel}")
        else:
            changed.append(rel)
    files = before / "files"

    def load(root: Path, rel: str):
        f = root / rel
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    # the deep files that must not change at all (screens, narration, the
    # contents board, the narration's audio index): byte for byte
    for rel in deep_files(L):
        if rel in ma and ma[rel] != mb.get(rel) and not MAY_CHANGE_RE.match(rel):
            p.fail(f"changed: {rel}")
    for rel in changed:
        if re.fullmatch(r"analysis/screens/[^/]+/screens\.json", rel):
            check_intro_screens(load(files, rel), load(L, rel), p, rel)
    if (files / "analysis/sections.json").exists():
        check_sections(load(files, "analysis/sections.json"), load(L, "analysis/sections.json"), p)
    base = {}
    stale = []
    for d in ("generated/lesson-player", SILENT):
        for name in ("bundle.json", "text.json", "timeline.json", "audio_index.json"):
            rel = f"{d}/{name}"
            src = files
            if rendered is not None and (rendered / "files" / rel).exists() \
                    and (files / rel).exists() and sha(rendered / "files" / rel) != sha(files / rel):
                if d != SILENT:
                    p.fail(f"{rel}: the lesson's file differs from its re-render by the code before "
                           f"the change (render_compare)")
                else:
                    stale.append(rel)
                    src = rendered / "files"
            base[rel] = src
    if stale:
        p.allow("silent preview older than its narration: compared with its re-render before the change",
                len(stale))
    for d in ("generated/lesson-player", SILENT):
        rel = d + "/bundle.json"
        if (base[rel] / rel).exists():
            check_bundle(load(base[rel], rel), load(L, rel), p, d)
        rel = d + "/text.json"
        if (base[rel] / rel).exists():
            check_text(load(base[rel], rel), load(L, rel), p, rel)
        rel = d + "/timeline.json"
        if (base[rel] / rel).exists():
            check_timeline(load(base[rel], rel), load(L, rel), p, rel)
        rel = d + "/audio_index.json"
        if (base[rel] / rel).exists() and (L / rel).exists() \
                and sha(base[rel] / rel) != sha(L / rel):
            p.fail(f"{rel}: changed (the narration's audio and its timing)")
    if "analysis/decisions.md" in changed:
        if not decisions_ok((files / "analysis/decisions.md").read_bytes(),
                            (L / "analysis/decisions.md").read_bytes()):
            p.fail("analysis/decisions.md: an earlier entry changed (entries may only be appended)")
    for rel in changed:
        p.allow("file rewritten: " + rel)
    report = {"lesson": L.name, "ok": not p.fails, "files_compared": len(set(ma) | set(mb)),
              "files_changed": changed, "failures": p.fails, "allowed": p.allowed}
    return report


def main() -> None:
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "snapshot":
        snapshot(Path(a[1]), Path(a[2]))
    elif len(a) >= 3 and a[0] == "extend":
        extend(Path(a[1]), Path(a[2]))
    elif len(a) >= 3 and a[0] == "compare":
        r = compare(Path(a[1]), Path(a[2]),
                    Path(a[a.index("--rendered") + 1]) if "--rendered" in a else None)
        if "--report" in a:
            Path(a[a.index("--report") + 1]).write_text(json.dumps(r, indent=1), encoding="utf-8")
        print(f"{r['lesson']}: {'PASS' if r['ok'] else 'FAIL'}: {r['files_compared']} files compared, "
              f"{len(r['files_changed'])} rewritten as allowed; {len(r['failures'])} differences not allowed")
        for k, v in sorted(r["allowed"].items()):
            print(f"  allowed: {k} x{v}")
        for f in r["failures"][:50]:
            print("  FAIL " + f)
        if not r["ok"]:
            raise SystemExit(1)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
