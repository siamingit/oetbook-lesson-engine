"""Publishing an approved lesson to the site (ADR 039 and its amendment of 2026-10-23;
oetacademy-web ADR-0005, ADR-0034 §2 and Amendment 13, ENGINE-GAPS G1 to G7).

    .venv/Scripts/python spike/scripts/publish_lesson.py <L> --package
    .venv/Scripts/python spike/scripts/publish_lesson.py <L> --release --dry-run
    .venv/Scripts/python spike/scripts/publish_lesson.py <L> --release
    .venv/Scripts/python spike/scripts/publish_lesson.py <L> --status
    .venv/Scripts/python spike/scripts/publish_lesson.py <L> --approve-tags --by NAME
    .venv/Scripts/python spike/scripts/publish_lesson.py <L> --tags-page

--package writes the lesson's next package version, <L>/generated/package/<id>-v<n>/ and
<id>-v<n>.zip (the folder at the zip's root), from the lesson player's bundle:

- bundle.json, every path rewritten into the package (an utterance's `audio_file`, a gloss's
  `audio.file`, `heard.file` and `image.file`, and the html's `data-audio` and `src`); text.json and
  blocks.css byte for byte;
- narration: each WAV master encoded to AAC-LC .m4a, mono, 44.1 kHz, 64 kb/s, named
  audio/<the first 16 hex of the master's SHA-256>.m4a, so two different masters never share a name
  (the engine's names repeat across section folders); each file's decoded start and length are
  checked against its master, within 10 ms, and its MP4 edit list must trim the encoder's priming;
- exam recordings and pronunciation clips: the original MP3, byte for byte, named
  audio/<the first 16 hex of its SHA-256>.mp3; an exam file's source (set, part, extract, release)
  is taken from the lesson's copy of the exercises release (analysis/practice_set.json), never
  inferred from a name;
- images: the files a block names, keeping their names, in images/;
- manifest.json (contracts 1.8.0): lesson.approved {"by": "siavash", "on": the final gate's date};
  professions "all" and criteria [] everywhere; each section's `teaches` from
  <library>/course/section-tags.json (proposed by the agent, approved by the owner once per course);
  terms and references restating the boards; retired sections carried and added (G5).

The package is checked against the pinned contracts (lesson_package.py) and by the engine's own
checks (names, references inside the package, audio timing); a package with any error is not
written. The same inputs give byte-identical files and zip.

--release publishes the package built for the next version as a release of
siamingit/oetacademy-sessions, tag <id>-v<n>, with exactly two assets (manifest.json and the zip),
after checking it again, the owner's approval of the course's tags, and the repository's releases.
It records the release in <L>/analysis/publish.json, the lesson's package versions and published
section ids. --dry-run prints what it would create and changes nothing.
"""

import argparse
import concurrent.futures
import copy
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_course_index                                         # noqa: E402
import lesson_package as lp                                       # noqa: E402
import paths                                                      # noqa: E402

SESSIONS_REPO = "siamingit/oetacademy-sessions"
OWNER = "siavash"                     # lesson.approved.by for every approved lesson (ADR 039, decision 3)
# Imported by hand on the site as package version 1 (ENGINE-GAPS G3): the engine starts them at 2.
SITE_IMPORTED = {
    "grammar-01-verb-tenses", "grammar-02-verb-use", "grammar-03-nominalization", "grammar-04-articles",
    "grammar-05-complex-compound", "grammar-06-clause", "grammar-07-punctuation", "grammar-08-paraphrasing",
    "vocabulary-01-word-forms", "vocabulary-02-collocations", "vocabulary-03-collocations-2"}
RATE = 44100
ENCODE = ["-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", "-ac", "1",
          "-ar", str(RATE), "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart"]
TIMING_TOLERANCE_S = 0.010
LAG_WINDOW_S = 0.05
ZIP_WARN = 700 * 1024 * 1024          # tell the owner (ADR-0034, requests, item 8)
ZIP_LIMIT = 1024 * 1024 * 1024        # the site refuses a larger zip
ZIP_DATE = (1980, 1, 1, 0, 0, 0)


class Refused(Exception):
    pass


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(p: Path, doc, indent=2) -> bytes:
    data = (json.dumps(doc, indent=indent, ensure_ascii=False) + "\n").encode("utf-8")
    p.write_bytes(data)
    return data


def package_dir(L: Path) -> Path:
    return L / "generated" / "package"


def record_path(L: Path) -> Path:
    return L / "analysis" / "publish.json"


def tags_path(L: Path) -> Path:
    return build_course_index.course_dir(L) / "section-tags.json"


def load_record(L: Path) -> dict:
    p = record_path(L)
    if p.exists():
        return read_json(p)
    return {"format": "oetbook-publish-record", "format_version": "1.0", "lesson": L.name, "releases": []}


def next_version(lesson: str, record: dict) -> int:
    done = [r["package_version"] for r in record["releases"]]
    if done:
        return max(done) + 1
    return 2 if lesson in SITE_IMPORTED else 1


def final_gate(L: Path) -> dict:
    gates = read_json(L / "analysis" / "gates.json")
    final = gates.get("final")
    if not final or not final.get("on"):
        raise Refused(f"{L.name} has no final gate in analysis/gates.json: only an approved lesson is published")
    return {"by": OWNER, "on": final["on"][:10]}


# --- Audio ------------------------------------------------------------------------------------

def ffmpeg_version() -> str:
    out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True).stdout
    return out.splitlines()[0]


def encode(master: Path, target: Path) -> None:
    tmp = target.with_name(target.name + ".part.m4a")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(master), *ENCODE, str(tmp)], check=True)
    tmp.replace(target)


def decode(path: Path) -> np.ndarray:
    """The file as a browser plays it: ffmpeg applies the MP4 edit list, as browsers do."""
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
                          "-ar", str(RATE), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(pcm, dtype="<f4").astype(np.float64)


def mp4_boxes(data: bytes, start: int, end: int):
    at = start
    while at + 8 <= end:
        size = int.from_bytes(data[at:at + 4], "big")
        kind = data[at + 4:at + 8].decode("latin1")
        head = 8
        if size == 1:
            size, head = int.from_bytes(data[at + 8:at + 16], "big"), 16
        elif size == 0:
            size = end - at
        yield kind, at + head, at + size
        at += size


def edit_list(path: Path) -> dict:
    """The audio track's edit list: how many samples the decoder skips (the encoder's priming)
    and how long the edited track plays, in seconds."""
    data = path.read_bytes()
    out = {"movie_timescale": None, "media_timescale": None, "entries": []}
    for kind, s, e in mp4_boxes(data, 0, len(data)):
        if kind != "moov":
            continue
        for k2, s2, e2 in mp4_boxes(data, s, e):
            if k2 == "mvhd":
                v = data[s2]
                out["movie_timescale"] = int.from_bytes(data[s2 + (20 if v else 12):s2 + (24 if v else 16)], "big")
            if k2 != "trak":
                continue
            for k3, s3, e3 in mp4_boxes(data, s2, e2):
                if k3 == "mdia":
                    for k4, s4, e4 in mp4_boxes(data, s3, e3):
                        if k4 == "mdhd":
                            v = data[s4]
                            out["media_timescale"] = int.from_bytes(
                                data[s4 + (20 if v else 12):s4 + (24 if v else 16)], "big")
                if k3 == "edts":
                    for k4, s4, e4 in mp4_boxes(data, s3, e3):
                        if k4 == "elst":
                            v, n = data[s4], int.from_bytes(data[s4 + 4:s4 + 8], "big")
                            at = s4 + 8
                            for _ in range(n):
                                if v:
                                    dur = int.from_bytes(data[at:at + 8], "big")
                                    media = int.from_bytes(data[at + 8:at + 16], "big", signed=True)
                                    at += 20
                                else:
                                    dur = int.from_bytes(data[at:at + 4], "big")
                                    media = int.from_bytes(data[at + 4:at + 8], "big", signed=True)
                                    at += 12
                                out["entries"].append({"segment_duration": dur, "media_time": media})
    return out


def lag_samples(master: np.ndarray, decoded: np.ndarray) -> tuple[int, float]:
    """The shift of `decoded` against `master` that lines them up best (positive: decoded later),
    within LAG_WINDOW_S, and how well they match there (normalised correlation)."""
    n = len(master) + len(decoded)
    size = 1 << (n - 1).bit_length()
    c = np.fft.irfft(np.fft.rfft(decoded, size) * np.conj(np.fft.rfft(master, size)), size)
    w = int(LAG_WINDOW_S * RATE)
    lags = np.r_[np.arange(0, w + 1), np.arange(-w, 0)]
    vals = np.r_[c[:w + 1], c[-w:]]
    i = int(np.argmax(vals))
    energy = float(np.sqrt((master * master).sum() * (decoded * decoded).sum()))
    return int(lags[i]), (float(vals[i]) / energy if energy else 1.0)


def timing(master: Path, m4a: Path) -> dict:
    """Decoded start and length of an encoded narration file against its WAV master."""
    x, d = decode(master), decode(m4a)
    lag, corr = lag_samples(x, d)
    el = edit_list(m4a)
    entries = el["entries"]
    played = (entries[0]["segment_duration"] / el["movie_timescale"]) if len(entries) == 1 and el["movie_timescale"] else None
    return {"start_s": lag / RATE, "duration_s": len(d) / RATE, "master_s": len(x) / RATE,
            "duration_diff_s": (len(d) - len(x)) / RATE, "correlation": corr,
            "priming_samples": entries[0]["media_time"] if len(entries) == 1 else None,
            "edit_list_s": played}


def timing_findings(t: dict, name: str, f: lp.Findings) -> None:
    if abs(t["start_s"]) > TIMING_TOLERANCE_S:
        f.error("PUB-AUDIO-START", "audio", "a narration file's decoded start differs from its master by more "
                "than 10 ms", f"{name}: {t['start_s'] * 1000:+.1f} ms")
    if abs(t["duration_diff_s"]) > TIMING_TOLERANCE_S:
        f.error("PUB-AUDIO-LENGTH", "audio", "a narration file's decoded length differs from its master by more "
                "than 10 ms", f"{name}: {t['duration_diff_s'] * 1000:+.1f} ms")
    if t["correlation"] < 0.9:
        f.error("PUB-AUDIO-MATCH", "audio", "a narration file does not sound like its master",
                f"{name}: correlation {t['correlation']:.3f}")
    if t["priming_samples"] is None or t["edit_list_s"] is None \
            or abs(t["edit_list_s"] - t["master_s"]) > TIMING_TOLERANCE_S:
        f.error("PUB-AUDIO-EDITLIST", "audio", "a narration file's MP4 edit list does not trim the encoder's "
                "priming to the master's length", name)


# --- Building the package -------------------------------------------------------------------------

def assign_names(sources: dict[str, str], ext: str, f: lp.Findings) -> dict[str, str]:
    """Package names by content: {source path: its SHA-256} to {source path: audio/<16 hex>.<ext>}.
    Fails (PUB-NAME-COLLISION) on two different contents under one name."""
    names = {src: f"audio/{sha[:16]}.{ext}" for src, sha in sources.items()}
    by_name: dict[str, set] = {}
    for src, name in names.items():
        by_name.setdefault(name, set()).add(sources[src])
    for name, shas in by_name.items():
        if len(shas) > 1:
            f.error("PUB-NAME-COLLISION", "audio", "two different files would share one name in the package", name)
    return names


def exam_sources(L: Path) -> tuple[dict[str, dict], str | None]:
    """{SHA-256 of an extract's audio: {set, part, stimulus}} and the release, from the lesson's
    copy of the exercises release (practice_set.json, hashes checked when it was copied)."""
    p = L / "analysis" / "practice_set.json"
    if not p.exists():
        return {}, None
    ps = read_json(p)
    out = {}
    for part in ps.get("parts", []):
        for s in part.get("stimuli", []):
            audio = s.get("audio") or {}
            if audio.get("sha256"):
                out[audio["sha256"]] = {"set": ps["set_id"], "part": part["code"], "stimulus": s["id"]}
    rel = ps.get("release") or {}
    release = f"{rel['package_id']} v{rel['package_version']}" if rel.get("package_id") else None
    return out, release


def section_terms(bundle: dict, section: dict) -> list[dict]:
    boards = {b["id"]: b for b in bundle["boards"]}
    shown = []
    for bid in section["boards"]:
        b = boards[bid]
        for i in b["fixed"] + [w for s in b["states"] for w in s["working"]]:
            if i not in shown:
                shown.append(i)
    out = []
    for i in shown:
        blk = bundle["blocks"].get(i) or {}
        if blk.get("type") in ("term_box", "gloss"):
            out.append({"block": i, "kind": "gloss" if blk["type"] == "gloss"
                        or str(blk.get("label")).lower() == "word" else "key-term",
                        "term": blk.get("term"), "explanation": blk.get("explanation")})
    return out


def section_references(bundle: dict, section: dict) -> list[dict]:
    boards = {b["id"]: b for b in bundle["boards"]}
    return [{"utterance": u["id"], "lesson": r["lesson"], "section": r["section"]}
            for bid in section["boards"] for s in boards[bid]["states"] for u in s["utterances"]
            for r in u["refs"]]


def lesson_tags(L: Path, bundle: dict, contracts: lp.Contracts) -> tuple[dict[str, list], dict | None]:
    """{section id: teaches} from <library>/course/section-tags.json, and the course's approval."""
    p = tags_path(L)
    if not p.exists():
        raise Refused(f"no section tags: {p} does not exist (propose them, the owner approves them once per course)")
    doc = read_json(p)
    if doc.get("taxonomy") != contracts.tag_taxonomy:
        raise Refused(f"{p} names taxonomy {doc.get('taxonomy')}, the pinned tag list {contracts.tag_taxonomy}")
    entry = doc.get("lessons", {}).get(L.name)
    if not entry:
        raise Refused(f"{p} has no tags for {L.name}")
    tags = {s["id"]: s["teaches"] for s in entry["sections"]}
    ids = [s["id"] for s in bundle["sections"]]
    if sorted(tags) != sorted(ids):
        raise Refused(f"{p}: the tags of {L.name} name sections {sorted(set(tags) ^ set(ids))} that the "
                      f"bundle does not have, or miss ones it has")
    course = doc.get("courses", {}).get(L.name.split("-")[0]) or {}
    return tags, course.get("approved")


def retirements(L: Path, record: dict, current: list[str], version: int) -> list[dict]:
    """G5: every section id published before and gone now, with what replaced it. A newly retired
    id needs its replacements from <L>/analysis/publish_retired.json ({"<id>": [ids]})."""
    retired = list(record["releases"][-1]["retired_sections"]) if record["releases"] else []
    done = {r["id"] for r in retired}
    published = []
    for r in record["releases"]:
        for s in r["sections"]:
            if s not in published:
                published.append(s)
    gone = [s for s in published if s not in current and s not in done]
    if gone:
        p = L / "analysis" / "publish_retired.json"
        decided = read_json(p) if p.exists() else {}
        missing = [s for s in gone if s not in decided]
        if missing:
            raise Refused(f"published sections {missing} are gone: name what replaced each in {p} "
                          f"({{\"<id>\": [\"<current id>\", ...]}}, [] when dropped)")
        retired += [{"id": s, "retired_in": version, "replaced_by": decided[s]} for s in gone]
    return retired


def fingerprint(manifest: dict) -> str:
    m = copy.deepcopy(manifest)
    m["lesson"].pop("package_version", None)
    return hashlib.sha256(json.dumps(m, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def write_zip(folder: Path, target: Path) -> None:
    """The package folder at the zip's root; fixed dates, order and attributes, so the same
    folder always gives the same bytes."""
    tmp = target.with_name(target.name + ".part")
    files = sorted(p for p in folder.rglob("*") if p.is_file())
    with zipfile.ZipFile(tmp, "w") as z:
        for p in files:
            info = zipfile.ZipInfo(p.relative_to(folder).as_posix(), ZIP_DATE)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            media = p.suffix in (".m4a", ".mp3", ".png")
            info.compress_type = zipfile.ZIP_STORED if media else zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes(), compresslevel=None if media else 9)
    tmp.replace(target)


def check_zip(zpath: Path, folder: Path, f: lp.Findings) -> None:
    with zipfile.ZipFile(zpath) as z:
        names = sorted(z.namelist())
        files = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())
        if names != files:
            f.error("PUB-ZIP", "zip", "the zip does not hold exactly the package folder at its root")
        elif any(z.read(n) != (folder / n).read_bytes() for n in names):
            f.error("PUB-ZIP", "zip", "a file in the zip differs from the package folder")
    size = zpath.stat().st_size
    if size > ZIP_LIMIT:
        f.error("PUB-ZIP-SIZE", "zip", "the site refuses a zip over 1 GiB", f"{size} bytes")
    elif size > ZIP_WARN:
        f.warning("PUB-ZIP-SIZE", "zip", "over 700 MB: tell the owner before publishing", f"{size} bytes")


def build(L: Path, contracts: lp.Contracts, workers: int | None = None, log=print) -> dict:
    """Writes the lesson's next package and its zip, or nothing if any check fails."""
    lesson = paths.lesson_id(L)
    player = L / "generated" / "lesson-player"
    bundle = read_json(player / "bundle.json")
    if bundle["lesson"]["id"] != lesson:
        raise Refused(f"the bundle's lesson id {bundle['lesson']['id']} is not the folder's name {lesson}")
    if bundle["meta"].get("silent"):
        raise Refused("a silent preview is never published")
    approved = final_gate(L)
    record = load_record(L)
    version = next_version(lesson, record)
    tags, tags_approved = lesson_tags(L, bundle, contracts)
    retired = retirements(L, record, [s["id"] for s in bundle["sections"]], version)

    out = package_dir(L)
    out.mkdir(parents=True, exist_ok=True)
    stage = out / f".staging-{lesson}-v{version}"
    if stage.exists():
        shutil.rmtree(stage)
    (stage / "audio").mkdir(parents=True)
    f = lp.Findings()
    try:
        report = _assemble(L, player, bundle, contracts, stage, version, approved, tags, retired, workers, f, log)
        f.extend(lp.validate_package(stage, contracts))
        manifest = read_json(stage / "manifest.json")
        if record["releases"] and record["releases"][-1].get("fingerprint") == fingerprint(manifest):
            shutil.rmtree(stage)
            last = record["releases"][-1]["package_version"]
            log(f"{lesson}: unchanged since package version {last}; nothing to publish")
            return {"lesson": lesson, "unchanged_since": last}
        if not f.ok:
            raise Refused("the package fails its checks and was not written:\n" + "\n".join(f.lines()))
        final, zpath = out / f"{lesson}-v{version}", out / f"{lesson}-v{version}.zip"
        write_zip(stage, zpath)
        check_zip(zpath, stage, f)
        if not f.ok:
            zpath.unlink()
            raise Refused("the zip fails its checks and was not written:\n" + "\n".join(f.lines()))
        if final.exists():
            shutil.rmtree(final)
        stage.rename(final)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    files = [p for p in final.rglob("*") if p.is_file()]
    report.update({
        "lesson": lesson, "package_version": version, "folder": str(final), "zip": str(zpath),
        "zip_bytes": zpath.stat().st_size, "zip_sha256": lp.sha256_file(zpath),
        "manifest_sha256": lp.sha256_file(final / "manifest.json"), "fingerprint": fingerprint(manifest),
        "files": len(files), "folder_bytes": sum(p.stat().st_size for p in files),
        "tags_approved": tags_approved,
        "validation": {"errors": f.codes("error"), "warnings": f.codes("warning"), "lines": f.lines()}})
    write_json(out / f"{lesson}-v{version}.report.json", report)
    return report


def _assemble(L, player, bundle, contracts, stage, version, approved, tags, retired, workers, f, log) -> dict:
    pub = copy.deepcopy(bundle)
    utts = lp.utterances_of(pub)
    media = []

    # Narration: one .m4a per distinct master, named by the master's content.
    masters = {}
    for u in utts:
        if u.get("kind") != "exam" and u["audio_file"] not in masters:
            masters[u["audio_file"]] = lp.sha256_file((player / u["audio_file"]).resolve())
    names = assign_names(masters, "m4a", f)
    basenames: dict[str, set] = {}
    for rel, sha in masters.items():
        basenames.setdefault(Path(rel).name, set()).add(sha)
    collided = sorted(n for n, s in basenames.items() if len(s) > 1)

    cache = package_dir(L) / "audio-cache"
    stamp = {"ffmpeg": ffmpeg_version(), "args": ENCODE}
    if (cache / "encoder.json").exists() and read_json(cache / "encoder.json") != stamp:
        shutil.rmtree(cache)
    cache.mkdir(parents=True, exist_ok=True)
    write_json(cache / "encoder.json", stamp)
    jobs = {}
    for rel, name in names.items():
        jobs.setdefault(name, (player / rel).resolve())

    def one(item):
        name, master = item
        cached = cache / Path(name).name
        if not cached.exists():
            encode(master, cached)
        shutil.copyfile(cached, stage / name)
        return name, master, timing(master, stage / name)

    timings = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers or os.cpu_count() or 4) as ex:
        for i, (name, master, t) in enumerate(ex.map(one, sorted(jobs.items())), 1):
            timings[name] = t
            timing_findings(t, name, f)
            if i % 100 == 0:
                log(f"  narration {i}/{len(jobs)}")
    for name in sorted(jobs):
        p = stage / name
        media.append({"path": name, "sha256": lp.sha256_file(p), "bytes": p.stat().st_size,
                      "mime": "audio/mp4", "duration_s": round(timings[name]["duration_s"], 6),
                      "kind": "narration"})
    for u in utts:
        if u.get("kind") != "exam":
            u["audio_file"] = names[u["audio_file"]]

    # MP3s: exam recordings and pronunciation clips, byte for byte, named by their own hash.
    sources, release = exam_sources(L)
    mp3s: dict[str, str] = {}

    def mp3(rel: str, kind: str, at: str) -> str:
        if rel in mp3s:
            return mp3s[rel]
        src = (player / rel).resolve()
        if not src.is_file():
            f.error("PUB-SOURCE-MISSING", "audio", "a file the bundle names does not exist", f"{at}: {rel}")
            mp3s[rel] = rel
            return rel
        data = src.read_bytes()
        sha = lp.sha256_bytes(data)
        name = f"audio/{sha[:16]}.mp3"
        entry = {"path": name, "sha256": sha, "bytes": len(data), "mime": "audio/mpeg",
                 "duration_s": mp3_duration(src), "kind": kind}
        if kind == "exam":
            source = sources.get(sha)
            if not source:
                f.error("PUB-EXAM-SOURCE", "audio", "an exam file is in no stimulus of the release data "
                        "(analysis/practice_set.json)", f"{at}: {rel}")
            else:
                entry["exam"] = dict(source, **({"release": release} if release else {}))
        if not (stage / name).exists():
            (stage / name).write_bytes(data)
            media.append(entry)
        mp3s[rel] = name
        return name

    for u in utts:
        if u.get("kind") == "exam":
            ex = u.get("exam") or {}
            old = u["audio_file"]
            u["audio_file"] = mp3(old, "exam", u["id"])
            got = next((m for m in media if m["path"] == u["audio_file"]), None)
            if got and got.get("exam"):
                if ex.get("stimulus") != got["exam"]["stimulus"]:
                    f.error("PUB-EXAM-SOURCE", "audio", "the recording's extract is not the release data's for "
                            "its file", u["id"])
                if ex.get("release") and release and ex["release"] != release:
                    f.error("PUB-EXAM-SOURCE", "audio", "the recording's release is not the release data's", u["id"])
    for block in pub["blocks"].values():
        html = block.get("html") or ""
        if block.get("heard"):
            old = lp.heard_file(block)
            if "/" not in old:
                old = f"../exam-audio/{old}"
            new = mp3(old, "exam", block["id"])
            html = html.replace(f'data-audio="{old}"', f'data-audio="{new}"')
            block["heard"]["file"] = new
        if block.get("audio"):
            old = block["audio"]["file"]
            new = mp3(old, "pronunciation", block["id"])
            html = html.replace(f'data-audio="{old}"', f'data-audio="{new}"')
            block["audio"]["file"] = new
        if block.get("image"):
            old = block["image"]["file"]
            new = f"images/{Path(old).name}"
            src = (player / old).resolve()
            if not src.is_file():
                f.error("PUB-SOURCE-MISSING", "images", "an image the bundle names does not exist", f"{block['id']}: {old}")
            elif not (stage / new).exists():
                (stage / "images").mkdir(exist_ok=True)
                shutil.copyfile(src, stage / new)
                media.append({"path": new, "sha256": lp.sha256_file(stage / new), "bytes": (stage / new).stat().st_size,
                              "mime": "image/svg+xml" if new.endswith(".svg") else "image/png"})
            html = html.replace(f'src="{old}"', f'src="{new}"')
            block["image"]["file"] = new
        block["html"] = html
    media.sort(key=lambda m: m["path"])

    # The player files.
    files = {"bundle": write_json(stage / "bundle.json", pub),
             "text": (player / "text.json").read_bytes(), "stylesheet": (player / "blocks.css").read_bytes()}
    (stage / "text.json").write_bytes(files["text"])
    (stage / "blocks.css").write_bytes(files["stylesheet"])

    title = pub["lesson"]["title"]
    manifest = {
        "format": "oetacademy-lesson-package",
        "contracts_version": contracts.version,
        "taxonomy": contracts.tag_taxonomy,
        "lesson": {"id": pub["lesson"]["id"], "package_version": version, "title": title,
                   "short_title": build_course_index.short_title(title),
                   "description": pub["lesson"].get("description"), "professions": "all",
                   "duration_s": pub["meta"]["total_duration_s"], "bundle_format_version": pub["format_version"],
                   "approved": approved},
        "files": {k: {"path": p, "sha256": lp.sha256_bytes(files[k]), "bytes": len(files[k])}
                  for k, p in (("bundle", "bundle.json"), ("text", "text.json"), ("stylesheet", "blocks.css"))},
        "media": media,
        "sections": [{"id": s["id"], "title": s["title"], "intro": s["intro"], "start": s["start"], "end": s["end"],
                      "teaches": tags[s["id"]], "criteria": [], "professions": "all",
                      "terms": section_terms(pub, s), "references": section_references(pub, s)}
                     for s in pub["sections"]],
        "retired_sections": retired,
    }
    write_json(stage / "manifest.json", manifest)

    worst_start = max(timings.values(), key=lambda t: abs(t["start_s"]), default=None)
    worst_len = max(timings.values(), key=lambda t: abs(t["duration_diff_s"]), default=None)
    kinds: dict[str, int] = {}
    for m in media:
        k = m.get("kind") or "image"
        kinds[k] = kinds.get(k, 0) + 1
    return {"media_by_kind": kinds, "narration_masters": len(masters),
            "narration_files": len(jobs), "basename_collisions_resolved": collided,
            "priming_samples": sorted({t["priming_samples"] for t in timings.values()}, key=str),
            "worst_start_ms": round(abs(worst_start["start_s"]) * 1000, 3) if worst_start else None,
            "worst_length_ms": round(abs(worst_len["duration_diff_s"]) * 1000, 3) if worst_len else None}


def mp3_duration(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


# --- Releasing ------------------------------------------------------------------------------------

def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def remote_versions(lesson: str) -> dict[int, str]:
    out = json.loads(gh("release", "list", "--repo", SESSIONS_REPO, "--limit", "1000", "--json", "tagName"))
    found = {}
    for r in out:
        m = re.fullmatch(re.escape(lesson) + r"-v(\d+)", r["tagName"])
        if m:
            found[int(m.group(1))] = r["tagName"]
    return found


def release(L: Path, dry_run: bool, log=print) -> dict:
    lesson = paths.lesson_id(L)
    record = load_record(L)
    version = next_version(lesson, record)
    tag = f"{lesson}-v{version}"
    folder, zpath = package_dir(L) / tag, package_dir(L) / f"{tag}.zip"
    if not folder.is_dir() or not zpath.is_file():
        raise Refused(f"package version {version} is not built: run --package first")
    contracts = lp.load()
    f = lp.validate_package(folder, contracts)
    check_zip(zpath, folder, f)
    if not f.ok:
        raise Refused("the package fails its checks:\n" + "\n".join(f.lines()))
    manifest = read_json(folder / "manifest.json")
    bundle = read_json(L / "generated" / "lesson-player" / "bundle.json")
    if manifest["lesson"]["approved"] != final_gate(L):
        raise Refused("the manifest's approval is not the lesson's final gate")
    tags, tags_approved = lesson_tags(L, bundle, contracts)
    blockers = []
    if not tags_approved:
        blockers.append(f"the section tags of the {lesson.split('-')[0]} course are not approved by the owner "
                        f"({tags_path(L)})")
    if any(s["teaches"] != tags[s["id"]] for s in manifest["sections"]):
        blockers.append("the package's tags are not the ones in the tags file: run --package again")
    with open(folder / "manifest.json", "rb") as a, zipfile.ZipFile(zpath) as z:
        if a.read() != z.read("manifest.json"):
            raise Refused("the asset manifest.json is not byte-identical to the zip's")
    remote = remote_versions(lesson)
    recorded = {r["package_version"] for r in record["releases"]}
    if set(remote) != recorded:
        raise Refused(f"{SESSIONS_REPO} holds versions {sorted(remote)} of {lesson}, the record "
                      f"{record_path(L)} says {sorted(recorded)}: stop and reconcile by hand")
    notes = (f"{manifest['lesson']['title']}: package version {version}, bundle format "
             f"{manifest['lesson']['bundle_format_version']}, contracts {manifest['contracts_version']}. "
             f"Final approval: {manifest['lesson']['approved']['by']}, {manifest['lesson']['approved']['on']}.")
    cmd = ["release", "create", tag, str(folder / "manifest.json"), str(zpath), "--repo", SESSIONS_REPO,
           "--title", tag, "--notes", notes, "--target", "main", "--latest=false"]
    plan = {"repository": SESSIONS_REPO, "tag": tag, "draft": False, "prerelease": False,
            "assets": [{"name": "manifest.json", "bytes": (folder / "manifest.json").stat().st_size,
                        "sha256": lp.sha256_file(folder / "manifest.json")},
                       {"name": zpath.name, "bytes": zpath.stat().st_size, "sha256": lp.sha256_file(zpath)}],
            "notes": notes, "command": "gh " + " ".join(f'"{c}"' if " " in c else c for c in cmd),
            "remote_versions": sorted(remote), "warnings": f.codes("warning"), "blockers": blockers}
    if dry_run:
        log("DRY RUN: nothing is created. It would run:\n  " + plan["command"])
        log(json.dumps({k: v for k, v in plan.items() if k != "command"}, indent=2))
        for b in blockers:
            log(f"BLOCKED: {b}")
        return plan
    if blockers:
        raise Refused("; ".join(blockers))
    gh(*cmd)
    view = json.loads(gh("release", "view", tag, "--repo", SESSIONS_REPO, "--json",
                         "assets,isDraft,isPrerelease,publishedAt,url"))
    names = sorted(a["name"] for a in view["assets"])
    if names != sorted(["manifest.json", zpath.name]) or view["isDraft"] or view["isPrerelease"]:
        raise Refused(f"the release {tag} was created but is not as planned: {view}; tell the owner, never edit it")
    if manifest["lesson"]["approved"]["on"] > view["publishedAt"][:10]:
        raise Refused(f"the approval date is after the release's {view['publishedAt']}; tell the owner")
    record["releases"].append({
        "package_version": version, "tag": tag, "url": view["url"], "published_at": view["publishedAt"],
        "manifest_sha256": plan["assets"][0]["sha256"], "zip_sha256": plan["assets"][1]["sha256"],
        "zip_bytes": plan["assets"][1]["bytes"], "fingerprint": fingerprint(manifest),
        "sections": [s["id"] for s in manifest["sections"]], "retired_sections": manifest["retired_sections"]})
    write_json(record_path(L), record)
    log(f"released {view['url']}")
    return plan


def approve_tags(L: Path, by: str) -> None:
    p = tags_path(L)
    doc = read_json(p)
    course = L.name.split("-")[0]
    entry = doc.setdefault("courses", {}).setdefault(course, {})
    entry["approved"] = {"by": by, "on": datetime.date.today().isoformat()}
    write_json(p, doc)
    print(f"the {course} course's section tags approved by {by}")


def tags_page(L: Path) -> Path:
    """One page for the owner: every lesson's sections with the proposed tag, its label in the
    taxonomy and, where the choice is not obvious, one line of reasoning. Written beside the tags
    file, outside git."""
    import html as h
    p = tags_path(L)
    doc = read_json(p)
    c = lp.load()
    rows = []
    for lesson, entry in doc["lessons"].items():
        course = doc.get("courses", {}).get(lesson.split("-")[0]) or {}
        state = (f"approved by {course['approved']['by']} on {course['approved']['on']}"
                 if course.get("approved") else "proposed, not approved")
        title = lesson
        player = build_course_index.library_of(L) / "lessons" / lesson / "generated" / "lesson-player" / "bundle.json"
        if player.exists():
            title = read_json(player)["lesson"]["title"]
        rows.append(f'<tr class="lesson"><th colspan="4">{h.escape(title)} <span class="id">{lesson}</span>'
                    f' <span class="state">{state}</span></th></tr>')
        for s in entry["sections"]:
            keys = s["teaches"] or [None]
            tag = "<br>".join(f"<code>{k}</code>" if k else "<i>none (introduction)</i>" for k in keys)
            label = "<br>".join(h.escape(c.label(k) or "NOT A KEY") if k else "" for k in keys)
            why = h.escape(s.get("reason") or "") if s["teaches"] and s.get("reason") else ""
            rows.append(f'<tr><td>{h.escape(s["title"])} <span class="id">{s["id"]}</span></td>'
                        f'<td>{tag}</td><td>{label}</td><td class="why">{why}</td></tr>')
    out = p.with_name("section-tags-review.html")
    out.write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Section tags review</title>
<style>
:root {{ --bg:#fff; --fg:#1b1b1b; --muted:#666; --line:#ddd; --band:#f2f5f8; --code:#0b5277; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#16181b; --fg:#e8e8e8; --muted:#9a9a9a; --line:#33373c;
  --band:#22262b; --code:#8cc8ec; }} }}
body {{ background:var(--bg); color:var(--fg); font:15px/1.45 "Segoe UI", system-ui, sans-serif; margin:0; padding:24px 16px; }}
main {{ max-width:1100px; margin:0 auto; }}
h1 {{ font-size:22px; margin:0 0 6px; }}
p {{ margin:4px 0 12px; color:var(--muted); }}
table {{ border-collapse:collapse; width:100%; }}
th, td {{ text-align:left; vertical-align:top; padding:7px 10px; border-bottom:1px solid var(--line); }}
thead th {{ font-size:13px; color:var(--muted); font-weight:600; }}
tr.lesson th {{ background:var(--band); font-size:16px; padding-top:12px; }}
.id {{ color:var(--muted); font-size:12px; font-weight:400; margin-left:6px; }}
.state {{ float:right; font-size:13px; font-weight:400; color:var(--muted); }}
code {{ color:var(--code); font:13px Consolas, monospace; }}
.why {{ color:var(--muted); font-size:14px; }}
@media (max-width:700px) {{ td, th {{ display:block; border:0; padding:3px 6px; }} tr {{ display:block;
  border-bottom:1px solid var(--line); padding:6px 0; }} thead {{ display:none; }} .state {{ float:none; display:block; }} }}
</style></head><body><main>
<h1>Section tags for the site: proposed</h1>
<p>What each section teaches, as the site's manifest will say it (<code>sections[].teaches</code>). Keys come only from
the pinned contracts' session section tag list (contracts {c.version}, taxonomy v{c.tag_taxonomy['version']}): a topic
where a section clearly teaches one, otherwise the skill; an introduction none. A reason is given where the choice is
not obvious. To approve, say so in chat, or name the changes (lesson, section, key). Data:
<code>{h.escape(str(p))}</code>.</p>
<table><thead><tr><th>Section</th><th>Proposed tag</th><th>Label in the taxonomy</th><th>Why</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody></table></main></body></html>
""", encoding="utf-8")
    return out


def status(L: Path) -> None:
    record = load_record(L)
    v = next_version(L.name, record)
    print(f"{L.name}: released {[r['tag'] for r in record['releases']] or 'none'}; next package version {v}")
    folder = package_dir(L) / f"{L.name}-v{v}"
    print(f"  built: {folder if folder.is_dir() else 'not yet'}")
    try:
        bundle = read_json(L / "generated" / "lesson-player" / "bundle.json")
        _, approved = lesson_tags(L, bundle, lp.load())
        print(f"  tags: {'approved ' + json.dumps(approved) if approved else 'proposed, not approved'}")
    except Refused as e:
        print(f"  tags: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lesson", type=Path)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--package", action="store_true")
    mode.add_argument("--release", action="store_true")
    mode.add_argument("--status", action="store_true")
    mode.add_argument("--approve-tags", action="store_true")
    mode.add_argument("--tags-page", action="store_true", help="write the owner's review page of the tags")
    ap.add_argument("--dry-run", action="store_true", help="--release: print what it would create")
    ap.add_argument("--by", help="--approve-tags: who approved")
    ap.add_argument("--workers", type=int)
    a = ap.parse_args()
    L = a.lesson.resolve()
    try:
        if a.package:
            r = build(L, lp.load(), a.workers)
            if "unchanged_since" not in r:
                print(f"{r['lesson']} v{r['package_version']}: {r['zip_bytes'] / 1e6:.1f} MB zip, {r['files']} files, "
                      f"media {r['media_by_kind']}; worst narration start {r['worst_start_ms']} ms, length "
                      f"{r['worst_length_ms']} ms; tags {'approved' if r['tags_approved'] else 'proposed'}")
                print("\n".join(r["validation"]["lines"]) or "  no findings")
                print(f"PASS: {r['zip']}")
        elif a.release:
            release(L, a.dry_run)
        elif a.approve_tags:
            if not a.by:
                ap.error("--approve-tags needs --by")
            approve_tags(L, a.by)
        elif a.tags_page:
            print(f"file:///{tags_page(L).as_posix()}")
        else:
            status(L)
    except Refused as e:
        print(f"REFUSED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
