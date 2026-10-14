"""Prove that a change to shared code leaves the built lessons unchanged.

    .venv/Scripts/python spike/scripts/render_compare.py snapshot before [LESSON,LESSON,...]
    (change the code)
    .venv/Scripts/python spike/scripts/render_compare.py snapshot after [LESSON,LESSON,...]
    .venv/Scripts/python spike/scripts/render_compare.py compare before after

Maintainer, 2026-10-05, on bundle 1.13 (ADR 026): "render all 11 before and
after the change and run an automated comparison (rendered output and
timings). If any lesson differs, stop and tell me before changing it."

`snapshot` re-renders every built lesson (a lesson with
generated/lesson-player/bundle.json) with the free stages only, as the runner
does after a gate: the title and contents boards, every section's screens and
narration (`--render`, no model call), the fit and the silent preview, the fit
and the lesson player. It copies every data file they write, and takes a
fingerprint of both players in headless Edge: at every moment a board changes
(the moments check_layout.py measures), at phone and laptop width, the frame's
DOM and, for every element shown, its box, opacity, colours and transform, and
the camera. `compare` diffs the data files byte for byte and the fingerprints
moment by moment. The player's own HTML is not compared as bytes, since the
template is the code that changes; what it draws is.

Read-only (owner, 2026-10-14, after a stale backup of 00:29 was restored over
the 16 finished lessons): the renders write into the lesson they are given, so
`snapshot` copies the library (every lesson folder but its video, and the
course folder) to spike/out/render-compare/work/<name>/ and renders and
fingerprints the copies there, then deletes them. Nothing is ever written under
C:\\OET\\lessons: every write and every lesson path given to a render is checked
(`guard`), and the lessons' files are listed (size and time) before and after a
snapshot, which stops loudly if any changed. There is no backup and no restore.
A stale `backup/` (the old commands' folder), a copy left by an unfinished run
or a snapshot of the same name stops the run before anything is copied or
rendered; old backups are kept in spike/out/render-compare/_stale/, never
restored. Output: spike/out/render-compare/ (gitignored).
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import paths
from check_layout import EDGE, EDGE_PROFILE, WIDTHS

HERE = Path(__file__).resolve().parent
PY = sys.executable
LESSONS = Path(r"C:\OET\lessons")
REPO = HERE.parents[1]
OUT = REPO / "spike" / "out" / "render-compare"
WORK = OUT / "work"                    # the snapshots' temporary copies of the library
VIDEO = {".mp4", ".mkv", ".mov", ".webm"}   # the source recording: no render reads it
DATA = ["generated/lesson-player/bundle.json", "generated/lesson-player/text.json",
        "generated/lesson-player/blocks.css", "generated/lesson-preview/silent/bundle.json",
        "generated/lesson-preview/silent/text.json", "generated/lesson-preview/silent/blocks.css",
        "generated/lesson-player/timeline.json", "generated/lesson-player/audio_index.json",
        "generated/lesson-preview/silent/timeline.json", "generated/lesson-preview/silent/audio_index.json",
        "analysis/fit.json", "analysis/fit-silent.json", "analysis/lesson-boards.json"]
PLAYERS = {"player": "generated/lesson-player/player.html",
           "silent": "generated/lesson-preview/silent/player.html"}

HARNESS = r"""
<script>
(function () {
  window.__lockWidth = __WIDTH__;
  fit();
  camEl.classList.remove("glide");
  const st = document.createElement("style");
  st.textContent = "*{transition:none!important;animation:none!important}";
  document.head.appendChild(st);
  function h(s) {            // FNV-1a, two lanes, as hex
    let a = 0x811c9dc5, b = 0x01000193 ^ s.length;
    for (let i = 0; i < s.length; i++) {
      const c = s.charCodeAt(i);
      a = Math.imul(a ^ c, 16777619) >>> 0;
      b = Math.imul(b ^ c, 2246822519) >>> 0;
    }
    return a.toString(16).padStart(8, "0") + b.toString(16).padStart(8, "0");
  }
  const F = frame.getBoundingClientRect();
  const r1 = v => Math.round(v * 10) / 10;
  function geometry() {
    const parts = [getComputedStyle(camEl).transform];
    for (const el of frame.querySelectorAll("*")) {
      const r = el.getBoundingClientRect();
      if (!r.width && !r.height) continue;
      const cs = getComputedStyle(el);
      if (cs.display === "none" || cs.visibility === "hidden") continue;
      parts.push([el.tagName, el.getAttribute("class") || "", r1(r.left - F.left), r1(r.top - F.top),
                  r1(r.width), r1(r.height), cs.opacity, cs.color, cs.backgroundColor,
                  cs.borderColor, cs.outlineStyle, cs.boxShadow, cs.transform,
                  cs.fontSize, cs.fontWeight].join("|"));
    }
    return h(parts.join("\n"));
  }
  const out = [];
  for (const bd of boards) {
    const times = new Set([bd.start + 0.001]);
    for (const s of bd.states) {
      times.add(s.start + 0.001); times.add(s.end - 0.001);
      if (s.erase) times.add(s.erase.time - 0.001);
      for (const c of s.clears || []) times.add(c.time + 0.001);
      for (const u of s.utterances) for (const c of u.cues) {
        times.add(c.time + 0.001);
        if (c.time_end) times.add(c.time_end + 0.001);
        if (c.type === "type") times.add((c.time + c.time_end) / 2);
      }
    }
    for (const f of bd.focus || []) times.add(f.time + 0.001);
    for (const v of bd.verdicts || []) times.add(v.time + 0.001);
    for (const w of bd.wordmarks || []) times.add(w.time + 0.001);
    const moments = [];
    for (const t of [...times].filter(t => t >= bd.start && t < bd.until).sort((a, b) => a - b)) {
      lastRenderT = null;
      renderFrame(t);
      moments.push([+t.toFixed(3), geometry(), h(frame.innerHTML)]);
    }
    out.push({ board: bd.id, start: bd.start, until: bd.until, moments });
  }
  const pre = document.createElement("pre");
  pre.id = "fp-result";
  pre.textContent = JSON.stringify({ frame: Math.round(F.width), boards: out });
  document.body.appendChild(pre);
})();
</script>
"""


def built(root: Path | None = None) -> list[Path]:
    return sorted(p for p in (root or LESSONS).iterdir()
                  if (p / "generated" / "lesson-player" / "bundle.json").exists())


def under(path, root: Path) -> bool:
    a = os.path.normcase(os.path.abspath(path))
    b = os.path.normcase(os.path.abspath(root))
    return a == b or a.startswith(b.rstrip("\\/") + os.sep)


def guard(path: Path) -> Path:
    """Every path this script writes, and every lesson it hands to a render, goes
    through here: never one under the finished lessons."""
    if under(path, LESSONS):
        raise SystemExit(f"REFUSED: render_compare never writes under {LESSONS} ({path}); "
                         f"it renders copies in {WORK}")
    return path


def stale(name: str) -> list[str]:
    """What stops a snapshot before anything is copied or rendered."""
    found = []
    if (OUT / "backup").exists():
        found.append(f"{OUT / 'backup'}: a backup left by the old backup/restore commands. "
                     f"Never restore it: move it into {OUT / '_stale'} (a clearly named folder)")
    if WORK.exists() and any(WORK.iterdir()):
        found.append(f"{WORK}: a copy of the library left by a run that did not finish, or "
                     f"one still running. If no render_compare is running, delete it (it is "
                     f"only a copy)")
    if (OUT / name).exists():
        found.append(f"{OUT / name}: a snapshot of that name exists: choose another name, or "
                     f"move the old one into {OUT / '_stale'}")
    return found


def manifest() -> dict:
    """Every file under the lessons, with its size and time: the proof that a
    snapshot wrote nothing there."""
    out, root = {}, LESSONS
    for dirpath, _, files in os.walk(root):
        for f in files:
            p = os.path.join(dirpath, f)
            st = os.stat(p)
            out[os.path.relpath(p, root)] = (st.st_size, st.st_mtime_ns)
    return out


def library_copy(name: str, only: list[str]) -> Path:
    """The lessons folder of a copy of the library, outside the lessons: each
    built lesson (or each named) whole but its video; of every other lesson its
    config only (the narration reads the other lessons' configs); the course
    folder (the course index, the word IDs)."""
    lib = guard(WORK / name)
    dest = guard(lib / "lessons")
    dest.mkdir(parents=True)
    skip = lambda d, names: [n for n in names if Path(n).suffix.lower() in VIDEO]  # noqa: E731
    keep = {L.name for L in built() if not only or L.name in only}
    for L in sorted(p for p in LESSONS.iterdir() if p.is_dir()):
        if L.name in keep:
            shutil.copytree(L, guard(dest / L.name), ignore=skip)
        elif (L / "analysis" / "sections.json").exists():
            t = guard(dest / L.name / "analysis" / "sections.json")
            t.parent.mkdir(parents=True)
            shutil.copy2(L / "analysis" / "sections.json", t)
    if (LESSONS.parent / "course").is_dir():
        shutil.copytree(LESSONS.parent / "course", guard(lib / "course"))
    return dest


def run(args: list[str], L: Path, log) -> None:
    for a in args:
        if os.path.isabs(a):
            guard(Path(a))
    r = subprocess.run([PY, *args], capture_output=True, text=True, encoding="utf-8", cwd=REPO,
                       errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    log.write(f"$ {' '.join(args)}\n{r.stdout[-3000:]}{r.stderr[-3000:]}\n")
    if r.returncode:
        raise SystemExit(f"{L.name}: {Path(args[0]).name} failed (exit {r.returncode}); see the log")


def fingerprint(player: Path, width: int) -> dict:
    edge = next(e for e in EDGE if Path(e).exists())
    harness = guard(player.with_name("player_fp.html"))
    html = player.read_text(encoding="utf-8")
    harness.write_text(html.replace("</body>", HARNESS.replace("__WIDTH__", str(width)) + "</body>"),
                       encoding="utf-8")
    r = subprocess.run([edge, "--headless=new", "--do-not-de-elevate", "--user-data-dir=" + EDGE_PROFILE, "--disable-gpu",
                        f"--window-size={width + 200},{int(width * 0.75)}", "--virtual-time-budget=60000",
                        "--dump-dom", harness.resolve().as_uri()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    harness.unlink(missing_ok=True)
    m = re.search(r'<pre id="fp-result">(.*?)</pre>', r.stdout, re.S)
    if not m:
        raise SystemExit(f"no fingerprint from {player}")
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&")
                      .replace("&lt;", "<").replace("&gt;", ">"))


def sections(L: Path) -> list[dict]:
    info = json.loads((L / "analysis" / "sections.json").read_text(encoding="utf-8"))
    secs = [s for s in info["sections"] if not s.get("intro")]
    intro = paths.intro_section(info)
    return ([intro] if intro else []) + secs


def snapshot(name: str, only: list[str]) -> None:
    found = stale(name)
    if found:
        raise SystemExit("STOPPED: nothing was copied, rendered or restored.\n  "
                         + "\n  ".join(found))
    dest = guard(OUT / name)
    before = manifest()
    work = library_copy(name, only)
    try:
        for L in built(work):
            render_one(L, dest)
    finally:
        shutil.rmtree(guard(WORK / name))
    after = manifest()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    if changed:
        raise SystemExit(f"ALARM: {len(changed)} file(s) under {LESSONS} changed while the snapshot "
                         f"ran (render_compare writes only to copies: another process, or a bug "
                         f"here). First: {changed[:5]}")
    print(f"{name}: no file under {LESSONS} changed", flush=True)


def render_one(L: Path, dest: Path) -> None:
    """Render and fingerprint one lesson of the copy (L is never a finished lesson)."""
    guard(L)
    d = guard(dest / L.name)
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "render.log", "w", encoding="utf-8") as log:
        run([str(HERE / "build_lesson_boards.py"), str(L)], L, log)
        for s in sections(L):
            pp = ",".join(str(p) for p in s["pages"])
            if not s.get("intro"):
                run([str(HERE / "write_screens.py"), str(L), "--pages", pp, "--render"], L, log)
            run([str(HERE / "write_narration.py"), str(L), "--pages", pp, "--render"], L, log)
        run([str(HERE / "fit_boards.py"), str(L), "--silent"], L, log)
        run([str(HERE / "build_silent_preview.py"), str(L)], L, log)
        run([str(HERE / "fit_boards.py"), str(L)], L, log)
        run([str(HERE / "build_lesson_player.py"), str(L)], L, log)
    for f in [*(L / "analysis" / "screens").rglob("screens.json"),
              *(L / "analysis" / "narration").rglob("narration.json"),
              *(L / p for p in DATA)]:
        if f.exists():
            t = d / "files" / f.relative_to(L)
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, t)
    fp = {}
    for which, rel in PLAYERS.items():
        if (L / rel).exists():
            for wname, width in WIDTHS.items():
                fp[f"{which}/{wname}"] = fingerprint(L / rel, width)
    (d / "fingerprint.json").write_text(json.dumps(fp), encoding="utf-8")
    moments = sum(len(b["moments"]) for v in fp.values() for b in v["boards"])
    print(f"{L.name}: rendered; {moments} moments fingerprinted", flush=True)


def compare(a: str, b: str) -> None:
    A, B = OUT / a, OUT / b
    report, differ = {}, 0
    for la in sorted(p for p in A.iterdir() if p.is_dir()):
        lb = B / la.name
        r = {"files_compared": 0, "files_differ": [], "files_missing": [],
             "moments_compared": 0, "geometry_differ": [], "dom_differ": 0, "timings_differ": []}
        fa = {f.relative_to(la / "files"): f for f in (la / "files").rglob("*") if f.is_file()}
        fb = {f.relative_to(lb / "files"): f for f in (lb / "files").rglob("*") if f.is_file()}
        for rel in sorted(set(fa) | set(fb)):
            if rel not in fa or rel not in fb:
                r["files_missing"].append(str(rel))
                continue
            r["files_compared"] += 1
            if fa[rel].read_bytes() != fb[rel].read_bytes():
                r["files_differ"].append(str(rel))
        pa = json.loads((la / "fingerprint.json").read_text(encoding="utf-8"))
        pb = json.loads((lb / "fingerprint.json").read_text(encoding="utf-8"))
        for key in sorted(set(pa) | set(pb)):
            ba = {x["board"]: x for x in pa.get(key, {}).get("boards", [])}
            bb = {x["board"]: x for x in pb.get(key, {}).get("boards", [])}
            for bid in sorted(set(ba) | set(bb)):
                xa, xb = ba.get(bid), bb.get(bid)
                if not xa or not xb or (xa["start"], xa["until"]) != (xb["start"], xb["until"]) \
                        or [m[0] for m in xa["moments"]] != [m[0] for m in xb["moments"]]:
                    r["timings_differ"].append(f"{key} {bid}")
                    continue
                for ma, mb in zip(xa["moments"], xb["moments"]):
                    r["moments_compared"] += 1
                    if ma[1] != mb[1]:
                        r["geometry_differ"].append(f"{key} {bid} t={ma[0]}")
                    if ma[2] != mb[2]:
                        r["dom_differ"] += 1
        same = not (r["files_differ"] or r["files_missing"] or r["geometry_differ"] or r["timings_differ"])
        r["identical"] = same
        differ += not same
        report[la.name] = r
        print(f"{la.name}: {'IDENTICAL' if same else 'DIFFERS'}: {r['files_compared']} data files "
              f"({len(r['files_differ'])} differ, {len(r['files_missing'])} missing); "
              f"{r['moments_compared']} moments ({len(r['geometry_differ'])} drawn differently, "
              f"{r['dom_differ']} DOM text differs); {len(r['timings_differ'])} board timing differences")
    (OUT / f"compare-{a}-{b}.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"{len(report) - differ} of {len(report)} lessons identical; report {OUT / f'compare-{a}-{b}.json'}")
    if differ:
        raise SystemExit(1)


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd in ("backup", "restore"):
        raise SystemExit(f"REFUSED: render_compare no longer backs up or restores (owner, "
                         f"2026-10-14): it renders copies in {WORK} and never writes under "
                         f"{LESSONS}. Run `snapshot NAME` before and after the change, then "
                         f"`compare`.")
    elif cmd == "snapshot":
        snapshot(sys.argv[2], sys.argv[3].split(",") if len(sys.argv) > 3 else [])
    elif cmd == "compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
