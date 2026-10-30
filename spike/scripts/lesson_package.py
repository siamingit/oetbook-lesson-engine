"""The site's lesson-package contract: the pinned contracts release, and the check of a package
folder against it (ADR 039 and its amendment of 2026-10-23; oetacademy-web ADR-0005 §10,
ADR-0034 Amendment 13, ENGINE-GAPS G6 and G7).

    .venv/Scripts/python spike/scripts/lesson_package.py --fetch
        download the pinned release (gh) and check its SHA-256
    .venv/Scripts/python spike/scripts/lesson_package.py <package folder>
        check a package folder; exit 1 on any error

The contracts release is private (oetacademy-web) and this repository is public, so it is never
committed (owner, 2026-10-23): spike/publish/contracts.lock.json names the release and its zip's
SHA-256. The zip is kept in %LOCALAPPDATA%\\oetacademy-contracts\\ (or $OETBOOK_CONTRACTS_DIR), and
its hash is checked every time it is read; every schema and data file is read from the zip in
memory, never from an unpacked copy.

The check is the three schemas (jsonschema, draft 2020-12, every schema registered by its `$id`,
nothing fetched) and then the rules the schemas cannot express, as the site's validator states
them (oetacademy-web packages/shared/src/contracts/lesson.ts at contracts 1.8.0, and the three
rules contracts 1.9.0 add for bundle 1.21: `LP-FIT`, `LP-PROVENANCE`, `LP-HEARD`; from 1.10.0 a
manifest names taxonomy v2 or v3, its keys checked against the version it names; and the three
contracts 1.12.0 add for bundle 1.22: `LP-STYLE`, `LP-EFFECTS`, `LP-CELLS`; and of the rules
contracts 1.13.0 add for bundle 1.23, the practice points' place and IDs: `LP-PRACTICE` (in part),
`LP-ID-BLOCK`, `LP-FIXTURE`), with its codes (`LP-...`), plus one of the engine's own: no file
reference in the package points outside it (`PUB-OUTSIDE`). The site validates again at import and
refuses a package with any error; a 1.23 package is also run through the site's own validator
(`pnpm contracts:validate lesson <folder> --refuse-fixtures`, docs/03-RUNBOOK.md step 18b), which
checks the practice items in full.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LOCK = REPO / "spike" / "publish" / "contracts.lock.json"

CONTRACT_FILES = ("manifest.json", "bundle.json", "text.json", "blocks.css")
LESSON_ID = re.compile(r"^[a-z]+-[0-9]{2,3}-[a-z0-9]+(-[a-z0-9]+)*$")
M4A_PATH = re.compile(r"^audio/[a-z0-9][a-z0-9-]*\.m4a$")
MP3_PATH = re.compile(r"^audio/[0-9a-f]{16}\.mp3$")
IMAGE_PATH = re.compile(r"^images/[a-z0-9][a-z0-9-]*\.(png|svg)$")
PROVENANCE = {"source-derived", "adapted", "corrected", "authored", "maintainer", "release"}
SESSION_RULES_FROM = (1, 8, 0)       # contracts 1.8.0: audio kinds, taxonomy and tag list required
TAG_LIST_FROM_TAXONOMY = 2           # the tag list's first taxonomy; a manifest names it or a later one
                                     # up to the list's own (v3 from contracts 1.10.0)
TIME_TOLERANCE_S = 0.001
CLIP_TOLERANCE_S = 0.05
MIN_AUDIO_KBPS = 64                  # narration, ADR-0005 §8; 10% slack, as the site allows
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
UNSAFE_HTML = [re.compile(p, re.I) for p in (
    r"<script|<iframe|<object|<embed|<link|<meta", r"\son[a-z]+\s*=", r"javascript:",
    r"\b(src|href|xlink:href)\s*=\s*[\"']?\s*(https?:|//)", r"url\(\s*[\"']?\s*(https?:|//)")]


# --- The pinned contracts ---------------------------------------------------------------------

def lock() -> dict:
    return json.loads(LOCK.read_text(encoding="utf-8"))


def cache_dir() -> Path:
    if os.environ.get("OETBOOK_CONTRACTS_DIR"):
        return Path(os.environ["OETBOOK_CONTRACTS_DIR"])
    base = os.environ.get("LOCALAPPDATA")
    return (Path(base) if base else Path.home() / ".cache") / "oetacademy-contracts"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(lk: dict | None = None) -> Path:
    """Downloads the pinned release's zip with gh, unless a copy with the right hash is there."""
    lk = lk or lock()
    target = cache_dir() / lk["asset"]
    if target.exists() and sha256_file(target) == lk["sha256"]:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["gh", "release", "download", lk["tag"], "--repo", lk["repository"],
                        "--pattern", lk["asset"], "--dir", str(target.parent), "--clobber"], check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        raise SystemExit(f"REFUSED: the pinned contracts {lk['tag']} could not be downloaded ({e}); "
                         f"nothing is packaged or published without them")
    got = sha256_file(target)
    if got != lk["sha256"]:
        target.unlink()
        raise SystemExit(f"REFUSED: {lk['asset']} has SHA-256 {got}, the lock says {lk['sha256']}; "
                         f"the download was deleted and nothing was published")
    return target


class Contracts:
    """The pinned release, read from its verified zip."""

    def __init__(self, files: dict[str, bytes], version: str):
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
        self.version = version
        self.files = files
        schemas = {n: json.loads(b) for n, b in files.items()
                   if n.startswith("schemas/") and n.endswith(".json")}
        registry = Registry().with_resources(
            (s["$id"], Resource.from_contents(s)) for s in schemas.values())
        self._validators = {
            name: Draft202012Validator(schemas[f"schemas/{name}.schema.json"], registry=registry,
                                       format_checker=Draft202012Validator.FORMAT_CHECKER)
            for name in ("lesson-manifest", "lesson-bundle", "lesson-text")}
        tags = json.loads(files["data/session-section-tags.json"])
        self.tag_keys = list(tags["keys"])
        self.tag_taxonomy = dict(tags["taxonomy"])
        # Every taxonomy version the release holds, by number, its hash from its own bytes (as the
        # site's taxonomy-versions.ts). A manifest names one of them (contracts 1.10.0: v2 or v3).
        self.taxonomies: dict[int, dict] = {}
        for n, raw in files.items():
            m = re.fullmatch(r"taxonomy/v(\d+)\.json", n)
            if m:
                tax = json.loads(raw)
                self.taxonomies[int(m[1])] = {
                    "ref": {"id": tax["taxonomy"], "version": int(m[1]), "sha256": sha256_bytes(raw)},
                    "nodes": {x["key"]: x for x in tax["nodes"]},
                    "criteria": {c["key"] for group in tax["criteria"].values() for c in group}}
        tv = self.tag_taxonomy["version"]
        if tv not in self.taxonomies or self.taxonomies[tv]["ref"] != self.tag_taxonomy:
            raise SystemExit(f"REFUSED: taxonomy/v{tv}.json does not have the SHA-256 the tag list names")
        self.taxonomy = self.taxonomies[tv]["nodes"]
        self.criteria = self.taxonomies[tv]["criteria"]
        prof = json.loads(files["data/professions.json"])
        self.professions = {p["id"] for p in prof["professions"] if p.get("active", True)}

    def validator(self, name: str):
        return self._validators[name]

    def taxonomy_ref(self, version: int) -> dict:
        """The `taxonomy` a manifest names for taxonomy `version` of this release."""
        if version not in self.taxonomies:
            raise SystemExit(f"REFUSED: contracts {self.version} hold no taxonomy v{version}")
        return dict(self.taxonomies[version]["ref"])

    def label(self, key: str) -> str | None:
        node = self.taxonomy.get(key)
        return node["label"] if node else None


def load(fetch_missing: bool = True) -> Contracts:
    lk = lock()
    path = cache_dir() / lk["asset"]
    if not path.exists():
        if not fetch_missing:
            raise SystemExit(f"REFUSED: the pinned contracts {lk['tag']} are not in {path.parent}; "
                             f"run lesson_package.py --fetch")
        path = fetch(lk)
    data = path.read_bytes()
    got = sha256_bytes(data)
    if got != lk["sha256"]:
        raise SystemExit(f"REFUSED: {path} has SHA-256 {got}, the lock says {lk['sha256']}")
    with zipfile.ZipFile(path) as z:
        files = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
    version = files["VERSION"].decode().strip()
    if version != lk["version"]:
        raise SystemExit(f"REFUSED: the zip is contracts {version}, the lock pins {lk['version']}")
    return Contracts(files, version)


# --- Findings ---------------------------------------------------------------------------------

class Findings:
    """Problems found, one line per kind: many occurrences of one problem are counted, with a few
    examples, so the report on a real lesson stays readable (as the site's Tally)."""

    def __init__(self):
        self._groups: dict[tuple, dict] = {}

    def add(self, severity: str, code: str, where: str, message: str, example: str | None = None):
        g = self._groups.setdefault((severity, code, where, message),
                                    {"count": 0, "examples": []})
        g["count"] += 1
        if example is not None and len(g["examples"]) < 4:
            g["examples"].append(example)

    def error(self, code, where, message, example=None):
        self.add("error", code, where, message, example)

    def warning(self, code, where, message, example=None):
        self.add("warning", code, where, message, example)

    def extend(self, other: "Findings"):
        for (sev, code, where, msg), g in other._groups.items():
            mine = self._groups.setdefault((sev, code, where, msg), {"count": 0, "examples": []})
            mine["count"] += g["count"]
            mine["examples"] = (mine["examples"] + g["examples"])[:4]

    @property
    def items(self) -> list[dict]:
        return [{"severity": s, "code": c, "where": w, "message": m, **g}
                for (s, c, w, m), g in self._groups.items()]

    def codes(self, severity: str) -> list[str]:
        return sorted({c for (s, c, _, _) in self._groups if s == severity})

    @property
    def ok(self) -> bool:
        return not self.codes("error")

    def lines(self) -> list[str]:
        out = []
        for x in sorted(self.items, key=lambda x: (x["severity"] != "error", x["code"])):
            n = f" ({x['count']}x)" if x["count"] > 1 else ""
            ex = f": {', '.join(x['examples'])}" if x["examples"] else ""
            out.append(f"  {x['severity']} {x['code']} {x['where']}: {x['message']}{n}{ex}")
        return out


# --- The check of a package folder --------------------------------------------------------------

def version_tuple(v: str) -> tuple:
    return tuple(int(x) for x in v.split("."))


def outside(p: str) -> bool:
    return p.startswith(("/", "\\", "..")) or "/../" in p or "\\" in p or bool(re.match(r"^[a-z]:", p, re.I))


def html_audio(html: str, button: str | None = None) -> list[str]:
    """The data-audio paths a block's html names (its buttons, rules 34 and 45)."""
    out = []
    for m in re.finditer(r"<[a-z][^>]*\bdata-audio\s*=\s*[\"']([^\"']*)[\"'][^>]*>", html, re.I):
        if not button or re.search(rf"\bclass\s*=\s*[\"'][^\"']*\b{button}\b", m.group(0)):
            out.append(m.group(1))
    return out


def heard_file(block: dict) -> str | None:
    """A gloss's heard sentence's file; a bare name (Listening 2, changelog §12 item 2) is taken
    from the html's "hear it in the recording" button, as the site does."""
    heard = block.get("heard")
    if not heard:
        return None
    if "/" in heard["file"]:
        return heard["file"]
    named = html_audio(block.get("html") or "", "gl-heard")
    return named[0] if named else heard["file"]


def utterances_of(bundle: dict) -> list[dict]:
    return [u for b in bundle["boards"] for s in b["states"] for u in s["utterances"]]


def schema_check(contracts: Contracts, name: str, doc, f: Findings, code: str, where: str) -> bool:
    errors = list(contracts.validator(name).iter_errors(doc))
    for e in errors[:20]:
        f.error(code, where, "does not match the schema", f"{e.json_path}: {e.message[:160]}")
    if len(errors) > 20:
        f.error(code, where, f"{len(errors) - 20} more schema errors")
    return not errors


def check_bundle(b: dict, folder: Path, f: Findings) -> None:
    where = "bundle.json"
    if not LESSON_ID.match(b["lesson"]["id"]):
        f.error("LP-LESSON-ID", where, "lesson id does not match <type>-<nn>-<slug>", b["lesson"]["id"])
    if b["meta"].get("silent"):
        f.error("LP-SILENT", where, "a silent preview is never published")

    states = [s for x in b["boards"] for s in x["states"]]
    utts = [u for s in states for u in s["utterances"]]
    for kind, ids in (("section", [s["id"] for s in b["sections"]]), ("board", [x["id"] for x in b["boards"]]),
                      ("state", [s["id"] for s in states]), ("utterance", [u["id"] for u in utts])):
        seen = set()
        for i in ids:
            if i in seen:
                f.error("LP-ID-DUPLICATE", where, f"duplicate {kind} id", i)
            seen.add(i)
    for key, block in b["blocks"].items():
        if block.get("id") != key:
            f.error("LP-ID-DUPLICATE", where, "block key differs from its id", key)

    section_ids = {s["id"] for s in b["sections"]}
    boards = {x["id"]: x for x in b["boards"]}

    def is_block(i):
        return i in b["blocks"] or re.sub(r"\.\d+$", "", i) in b["blocks"]

    for s in b["sections"]:
        for i in s["boards"]:
            if i not in boards:
                f.error("LP-REF-BROKEN", where, "section lists an unknown board", f"{s['id']} -> {i}")
            elif boards[i]["section"] != s["id"]:
                f.error("LP-REF-BROKEN", where, "board is listed by another section", f"{s['id']} -> {i}")
    listed = {i for s in b["sections"] for i in s["boards"]}
    for x in b["boards"]:
        if x["section"] not in section_ids:
            f.error("LP-REF-BROKEN", where, "board names an unknown section", x["id"])
        if x["id"] not in listed:
            f.error("LP-REF-BROKEN", where, "board is in no section's list", x["id"])
        for i in x["fixed"]:
            if not is_block(i):
                f.error("LP-REF-BROKEN", where, "unknown fixed block", f"{x['id']} -> {i}")
        if x.get("table") and not is_block(x["table"]):
            f.error("LP-REF-BROKEN", where, "unknown table block", f"{x['id']} -> {x['table']}")
        listen = x.get("listen")
        if listen:
            named = [listen["block"], listen.get("form")] + [s.get("block") for s in listen["sections"]] \
                + [i["block"] for i in (listen.get("panel") or {}).get("items", [])]
            for i in named:
                if i and not is_block(i):
                    f.error("LP-REF-BROKEN", where, "listen names an unknown block", f"{x['id']} -> {i}")
            state_ids = {s["id"] for s in x["states"]}
            for item in (listen.get("panel") or {}).get("items", []):
                if item["state"] not in state_ids:
                    f.error("LP-REF-BROKEN", where, "a panel item names a state of another board", item["state"])
        for s in x["states"]:
            for i in s["working"] + (s.get("overlay") or []):
                if not is_block(i):
                    f.error("LP-REF-BROKEN", where, "unknown working block", f"{s['id']} -> {i}")
            for u in s["utterances"]:
                for c in u["cues"]:
                    for i in (c.get("block"), c.get("to_block")):
                        if i and not is_block(i):
                            f.error("LP-REF-BROKEN", where, "cue names an unknown block", f"{u['id']} -> {i}")
                for r in u["refs"]:
                    if r["lesson"] == b["lesson"]["id"] and r["section"] is not None \
                            and r["section"] not in section_ids:
                        f.error("LP-REF-BROKEN", where, "reference to an unknown section of this lesson", u["id"])

    secs = b["sections"]
    if secs and abs(secs[0]["start"]) > TIME_TOLERANCE_S:
        f.error("LP-TIME-ORDER", where, "the first section must start at 0", secs[0]["id"])
    for i, s in enumerate(secs):
        end = secs[i + 1]["start"] if i + 1 < len(secs) else b["meta"]["total_duration_s"]
        if s["end"] < s["start"] or abs(s["end"] - end) > TIME_TOLERANCE_S:
            f.error("LP-TIME-ORDER", where, "a section must end where the next one starts", s["id"])
    last = 0.0
    for u in utts:
        if u["end"] < u["start"] or u["start"] + TIME_TOLERANCE_S < last:
            f.error("LP-TIME-ORDER", where, "utterances must play in order", u["id"])
        last = max(last, u["start"])

    for block in b["blocks"].values():
        if any(p.search(block.get("html") or "") for p in UNSAFE_HTML):
            f.error("LP-HTML-UNSAFE", where, "block html has a script, handler or external resource", block["id"])

    files = set()

    def check_path(p, at, mp3, field):
        files.add(p)
        if outside(p):
            f.error("LP-AUDIO-OUTSIDE", where, f"{field} points outside the package", f"{at}: {p}")
        elif not (MP3_PATH if mp3 else M4A_PATH).match(p):
            f.error("LP-AUDIO-PATH", where, f"{field} must be {'audio/<hash>.mp3' if mp3 else 'audio/<name>.m4a'}",
                    f"{at}: {p}")
        if not p.endswith(".mp3" if mp3 else ".m4a"):
            f.error("LP-AUDIO-FORMAT", where, "a recording or clip is the source's MP3" if mp3
                    else "narration is AAC in .m4a", f"{at}: {p}")

    for u in utts:
        check_path(u["audio_file"], u["id"], u.get("kind") == "exam", "audio_file")
        if u.get("kind") == "exam" and not ((u.get("clip_in") or 0) < (u.get("clip_out") or 0)):
            f.error("LP-CLIP-RANGE", where, "a recording's clip_out must be after its clip_in", u["id"])
    for block in b["blocks"].values():
        html = block.get("html") or ""
        say = (block.get("audio") or {}).get("file")
        heard = heard_file(block)
        if say:
            check_path(say, block["id"], True, "audio.file")
        if heard:
            check_path(heard, block["id"], True, "heard.file")
        if block.get("heard") and not block["heard"]["start"] < block["heard"]["end"]:
            f.error("LP-CLIP-RANGE", where, "a heard sentence must end after it starts", block["id"])
        named = html_audio(html)
        own = [p for p in (say, heard) if p]
        if any(p not in own for p in named) or (say and say not in html_audio(html, "gl-say")) \
                or (heard and heard not in html_audio(html, "gl-heard")):
            f.error("LP-AUDIO-HTML", where, "block html must name exactly its audio.file (gl-say) "
                    "and heard file (gl-heard)", block["id"])
    for p in sorted(files):
        if not outside(p) and not (folder / p).is_file():
            f.error("LP-AUDIO-MISSING", where, "audio file not found", p)

    # contracts 1.9.0: from bundle 1.21 the stray data of the changelog's §12 is gone, so a
    # provenance outside the format's values and a heard sentence in any other form are errors
    strict = version_tuple(b["format_version"]) >= (1, 21)
    for x in list(b["blocks"].values()) + utts:
        if x.get("provenance") not in PROVENANCE:
            if strict:
                f.error("LP-PROVENANCE", where, "provenance must be one of the format's values", x["id"])
            else:
                f.warning("LP-PROVENANCE-UNKNOWN", where, "provenance outside the format's values "
                          "(accepted, never shown)", x["id"])
    if strict:
        for block in b["blocks"].values():
            heard = block.get("heard")
            if heard and (set(heard) != {"file", "start", "end"} or not str(heard["file"]).startswith("audio/")):
                f.error("LP-HEARD", where, "heard must be exactly {file, start, end}, its file under audio/",
                        block["id"])

    for x in b["boards"]:
        table = b["blocks"].get(x["table"]) if x.get("table") else None
        rows = len((table or {}).get("rows") or [])
        for s in x["states"]:
            if s.get("doc") is not None and not ((table or {}).get("map")
                                                 and s["doc"] < len(table["map"]["docs"])):
                f.error("LP-LAYOUT", where, "state doc is not a text of the board's map", s["id"])
            if s.get("view") and (not table or any(r >= rows for r in s["view"]["rows"])):
                f.error("LP-LAYOUT", where, "state view names a row the board's table lacks", s["id"])
        listen = x.get("listen")
        if not listen:
            continue
        words = sum(listen["row_words"])
        at = f"{x['id']} listen"
        if len(listen["times"]) != words:
            f.error("LP-LISTEN", where, "times must hold one entry per word of row_words", at)
        last = 0.0
        for start, end in listen["times"]:
            if end < start or start + TIME_TOLERANCE_S < last:
                f.error("LP-LISTEN", where, "word times must be in order, each ending after it starts", at)
                break
            last = start
        if any(s["to"] < s["from"] or s["to"] >= words for s in listen["sections"]):
            f.error("LP-LISTEN", where, "a section's words lie outside the transcript", at)
        if any(i["to"] < i["word"] or i["to"] >= words for i in (listen.get("panel") or {}).get("items", [])):
            f.error("LP-LISTEN", where, "a panel item's words lie outside the transcript", at)

    for block in b["blocks"].values():
        html = block.get("html") or ""
        srcs = re.findall(r"\bsrc\s*=\s*[\"']([^\"']+)[\"']", html, re.I)
        image = block.get("image")
        if block["type"] == "picture" and not image:
            f.error("LP-PICTURE-IMAGE", where, "a picture block must carry an image", block["id"])
        if block.get("size") is not None and block["type"] != "picture":
            f.error("LP-PICTURE-SIZE", where, "only a picture block has a size", block["id"])
        if not image:
            if srcs:
                f.error("LP-IMAGE-HTML", where, "block html shows a file but has no image", block["id"])
            continue
        p = image["file"]
        if block["type"] not in ("gloss", "picture"):
            f.error("LP-IMAGE-BLOCK", where, "only gloss and picture blocks carry an image", block["id"])
        if outside(p):
            f.error("LP-IMAGE-OUTSIDE", where, "image.file points outside the package", f"{block['id']}: {p}")
        elif not IMAGE_PATH.match(p):
            f.error("LP-IMAGE-PATH", where, "image.file must be images/<name>.png or .svg", f"{block['id']}: {p}")
        if len(srcs) != 1 or srcs[0] != p:
            f.error("LP-IMAGE-HTML", where, "block html must show exactly its image.file", block["id"])
        if outside(p) or not (folder / p).is_file():
            f.error("LP-IMAGE-MISSING", where, "image file not found", p)
        else:
            check_image(folder / p, p, f)


def png_has_chunk(data: bytes, name: bytes) -> bool:
    at = 8
    while at + 8 <= len(data):
        length = int.from_bytes(data[at:at + 4], "big")
        kind = data[at + 4:at + 8]
        if kind == name:
            return True
        if kind in (b"IDAT", b"IEND"):
            return False
        at += 12 + length
    return False


def check_image(path: Path, p: str, f: Findings) -> None:
    data = path.read_bytes()
    if p.endswith(".png"):
        if data[:8] != PNG_SIGNATURE:
            f.error("LP-IMAGE-FORMAT", "bundle.json", "not a PNG file", p)
        elif data[25] not in (4, 6) and not png_has_chunk(data, b"tRNS"):
            f.error("LP-IMAGE-OPAQUE", "bundle.json", "an image PNG must be transparent (alpha channel)", p)
    else:
        svg = data.decode("utf-8", "replace")
        if not re.search(r"<svg[\s>]", svg, re.I):
            f.error("LP-IMAGE-FORMAT", "bundle.json", "not an SVG file", p)
        elif re.search(r"<script|<foreignobject|javascript:|\son[a-z]+\s*=|\b(href|xlink:href|src)\s*=\s*[\"']\s*"
                       r"(https?:|//)|url\(\s*[\"']?\s*(https?:|//)", svg, re.I):
            f.error("LP-IMAGE-UNSAFE", "bundle.json", "SVG has a script, handler or external reference", p)


def check_text(t: dict, b: dict, f: Findings) -> None:
    if "style" in t["lesson"] and version_tuple(t["format_version"]) < (1, 22):
        f.error("LP-STYLE", "text.json", "lesson.style is a field of format 1.22 and later")
    if t["lesson"]["id"] != b["lesson"]["id"]:
        f.error("LP-TEXT-MISMATCH", "text.json", "lesson id differs from bundle.json")
    key = [(s["id"], s["title"], s["start"], s["end"]) for s in t["sections"]]
    if key != [(s["id"], s["title"], s["start"], s["end"]) for s in b["sections"]]:
        f.error("LP-TEXT-MISMATCH", "text.json", "sections differ from bundle.json")


def check_listed(folder: Path, file: dict, f: Findings, prefix: str, where: str) -> bool:
    path = folder / file["path"]
    if outside(file["path"]) or not path.is_file():
        f.error(f"{prefix}-MISSING", where, "listed file not found", file["path"])
        return False
    if path.stat().st_size != file["bytes"] or sha256_file(path) != file["sha256"]:
        f.error(f"{prefix}-HASH", where, "file does not match its bytes and sha256", file["path"])
    return True


def check_manifest(m: dict, folder: Path, c: Contracts, f: Findings) -> None:
    where = "manifest.json"
    d, cur = version_tuple(m["contracts_version"]), version_tuple(c.version)
    if d[0] != cur[0] or d > cur:
        f.error("LP-CONTRACTS-VERSION", where, f"contracts {m['contracts_version']} is not of the pinned "
                f"{c.version}'s major version, or is newer")
    session_rules = d >= SESSION_RULES_FROM
    tax = m.get("taxonomy")
    if session_rules and not tax:
        f.error("LP-TAXONOMY-REQUIRED", f"{where} taxonomy", "a manifest of contracts 1.8.0 or later names "
                "its taxonomy version")
    # The version the manifest names, if this release has it with the same bytes (contracts 1.10.0:
    # v2 or v3, each key also a key of the version named).
    named = None
    if tax:
        got = c.taxonomies.get(tax["version"])
        if not got:
            f.error("LP-TAXONOMY-UNKNOWN", f"{where} taxonomy", f"taxonomy v{tax['version']} is not in this "
                    "contracts release")
        elif tax["sha256"] != got["ref"]["sha256"] or tax["id"] != got["ref"]["id"]:
            f.error("LP-TAXONOMY-HASH", f"{where} taxonomy", f"sha256 differs from taxonomy v{tax['version']} "
                    "in this release")
        else:
            named = got
    listed_version = tax and TAG_LIST_FROM_TAXONOMY <= tax["version"] <= c.tag_taxonomy["version"]
    allowed = set(c.tag_keys) if listed_version else set()
    nodes_of = named["nodes"] if named else {}
    criteria_of = named["criteria"] if named else set()

    def professions_ok(p, at):
        if p != "all" and any(x not in c.professions for x in p):
            f.error("LP-PROFESSION-UNKNOWN", at, "unknown profession", str(p))

    professions_ok(m["lesson"]["professions"], f"{where} lesson.professions")
    for s in m["sections"]:
        at = f"{where} sections[{s['id']}]"
        for key in s["teaches"]:
            node = nodes_of.get(key)
            if session_rules and tax and key not in allowed:
                f.error("LP-TEACHES-NOT-ALLOWED", f"{where} sections", "not on the session section tag list "
                        f"(taxonomy v{TAG_LIST_FROM_TAXONOMY} to v{c.tag_taxonomy['version']})", f"{s['id']}: {key}")
            if not named:
                continue
            if not node:
                f.error("LP-TOPIC-UNKNOWN", at, f"not a key of taxonomy v{tax['version']}", key)
            elif node.get("status") == "retired":
                f.error("LP-TOPIC-RETIRED", at, "retired in the taxonomy", key)
        nodes = [nodes_of[k] for k in s["teaches"] if k in nodes_of]
        if not s["intro"] and not s["teaches"]:
            f.error("LP-TEACHES-EMPTY", at, "a teaching section needs at least one topic it teaches")
        elif nodes and all(n["level"] == "skill" for n in nodes):
            f.warning("LP-TEACHES-BROAD", f"{where} sections", "tagged with a skill only", s["id"])
        for k in s["criteria"] if named else []:
            if k not in criteria_of:
                f.error("LP-CRITERION-UNKNOWN", at, "not a criterion key of the taxonomy", k)
        professions_ok(s["professions"], at)
        lp = m["lesson"]["professions"]
        if lp != "all" and (s["professions"] == "all" or not set(s["professions"]) <= set(lp)):
            f.error("LP-PROFESSIONS-OUTSIDE", at, "section professions must be within the lesson's")

    current = {s["id"] for s in m["sections"]}
    for r in m["retired_sections"]:
        at = f"{where} retired_sections[{r['id']}]"
        if r["id"] in current:
            f.error("LP-RETIRED-REUSED", at, "a retired section id is reused")
        if r["retired_in"] > m["lesson"]["package_version"]:
            f.error("LP-RETIRED-VERSION", at, "retired_in is after this package version")
        for i in r["replaced_by"]:
            if i not in current:
                f.error("LP-RETIRED-TARGET", at, "replaced_by is not a section", i)

    for file in m["files"].values():
        check_listed(folder, file, f, "LP-FILE", f"{where} files")
    paths = set()
    for file in m["media"]:
        if file["path"] in paths:
            f.error("LP-MEDIA-DUPLICATE", f"{where} media", "listed twice", file["path"])
        paths.add(file["path"])
        dur = file.get("duration_s")
        if file["mime"] == "audio/mp4" and dur and file["bytes"] * 8 / dur / 1000 < MIN_AUDIO_KBPS * 0.9:
            f.error("LP-AUDIO-BITRATE", f"{where} media", f"audio must be AAC at {MIN_AUDIO_KBPS} kb/s",
                    f"{file['path']}: {round(file['bytes'] * 8 / dur / 1000)} kb/s")
        if session_rules and file["mime"].startswith("audio/") and not file.get("kind"):
            f.error("LP-MEDIA-KIND", f"{where} media", "every audio file has a kind", file["path"])
        if file["mime"] == "audio/mpeg" and file["path"] != f"audio/{file['sha256'][:16]}.mp3":
            f.error("LP-AUDIO-NAME", f"{where} media", "an MP3 is named audio/<the first 16 hex of its "
                    "sha256>.mp3", file["path"])
        ex = file.get("exam")
        if ex and (not ex["stimulus"].startswith(ex["set"] + "-") or ex["set"][7:9].upper() != ex["part"]):
            f.error("LP-EXAM-SOURCE", f"{where} media", "exam.set must start exam.stimulus, and exam.part "
                    "be the set's part", file["path"])
        check_listed(folder, file, f, "LP-MEDIA", f"{where} media")


def check_manifest_against_bundle(m: dict, b: dict, f: Findings) -> None:
    where = "manifest.json"
    L = m["lesson"]
    for field, mine, theirs in (("lesson.id", L["id"], b["lesson"]["id"]),
                                ("lesson.title", L["title"], b["lesson"]["title"]),
                                ("lesson.description", L["description"], b["lesson"].get("description")),
                                ("lesson.bundle_format_version", L["bundle_format_version"], b["format_version"])):
        if mine != theirs:
            f.error("LP-MANIFEST-MISMATCH", where, f"{field} differs from bundle.json")
    if abs(L["duration_s"] - b["meta"]["total_duration_s"]) > TIME_TOLERANCE_S:
        f.error("LP-MANIFEST-MISMATCH", where, "lesson.duration_s differs from bundle.json")

    def key(s):
        return (s["id"], s["title"], s["intro"], s["start"], s["end"])
    if [key(s) for s in m["sections"]] != [key(s) for s in b["sections"]]:
        f.error("LP-MANIFEST-MISMATCH", where, "sections (id, title, intro, start, end, order) differ from bundle.json")

    boards = {x["id"]: x for x in b["boards"]}
    bsec = {s["id"]: s for s in b["sections"]}
    for s in m["sections"]:
        bs = bsec.get(s["id"])
        if not bs:
            continue
        at = f"{where} sections[{s['id']}]"
        bds = [boards[i] for i in bs["boards"] if i in boards]
        shown = {i for x in bds for i in x["fixed"] + [w for st in x["states"] for w in st["working"]]}
        expected = {i for i in shown if (b["blocks"].get(i) or {}).get("type") in ("term_box", "gloss")}
        listed = {t["block"] for t in s["terms"]}
        if expected != listed:
            f.error("LP-TERMS-MISMATCH", at, "terms must list every term box and gloss shown in the section "
                    f"(missing {len(expected - listed)}, unknown {len(listed - expected)})")
        spoken = sorted((u["id"], r["lesson"], r["section"]) for x in bds for st in x["states"]
                        for u in st["utterances"] for r in u["refs"])
        declared = sorted((r["utterance"], r["lesson"], r["section"]) for r in s["references"])
        if spoken != declared:
            f.error("LP-REFERENCES-MISMATCH", at, "references must equal the refs of the section's utterances")

    media = {x["path"]: x for x in m["media"]}
    used = set()

    def audio_of(path, kind):
        used.add(path)
        file = media.get(path)
        mime = "audio/mp4" if kind == "narration" else "audio/mpeg"
        return file if file and file["mime"] == mime and file.get("kind", "narration") == kind else None

    def too_long(end, file):
        return end > (file.get("duration_s") or 0) + CLIP_TOLERANCE_S

    for u in utterances_of(b):
        kind = "exam" if u.get("kind") == "exam" else "narration"
        file = audio_of(u["audio_file"], kind)
        if not file:
            f.error("LP-AUDIO-UNLISTED", where, f"audio_file not in manifest media as {kind}", u["id"])
            continue
        if u.get("clip_out") is not None and too_long(u["clip_out"], file):
            f.error("LP-CLIP-RANGE", where, "clip_out is beyond the clip's duration", u["id"])
        ex = u.get("exam")
        if ex and ex["sha256"] != file["sha256"]:
            f.error("LP-EXAM-HASH", where, "exam.sha256 differs from the file's sha256", u["id"])
        if ex and file.get("exam") and ex["stimulus"] != file["exam"]["stimulus"]:
            f.error("LP-EXAM-SOURCE", where, "exam.stimulus differs from the file's", u["id"])
    for block in b["blocks"].values():
        if block.get("audio") and not audio_of(block["audio"]["file"], "pronunciation"):
            f.error("LP-AUDIO-UNLISTED", where, "audio.file not in manifest media as a pronunciation clip", block["id"])
        heard = heard_file(block)
        if heard and block.get("heard"):
            file = audio_of(heard, "exam")
            if not file:
                f.error("LP-AUDIO-UNLISTED", where, "heard.file not in manifest media as an exam recording", block["id"])
            elif too_long(block["heard"]["end"], file):
                f.error("LP-CLIP-RANGE", where, "heard.end is beyond the file's duration", block["id"])
        if block.get("image"):
            used.add(block["image"]["file"])
            file = media.get(block["image"]["file"])
            if not file or not file["mime"].startswith("image/"):
                f.error("LP-IMAGE-UNLISTED", where, "image.file not in manifest media as an image", block["id"])
    for p in media:
        if p not in used:
            f.warning("LP-MEDIA-UNUSED", where, "media not used by any utterance or block", p)


REF_ATTR = re.compile(r"\b(data-audio|src|href|xlink:href|poster|srcset)\s*=\s*[\"']([^\"']*)[\"']", re.I)
CSS_URL = re.compile(r"url\(\s*[\"']?([^\"')]*)")


def references(bundle: dict, css: str) -> list[tuple[str, str]]:
    """Every file a package names: the bundle's path fields, every reference attribute in a block's
    html, every url() of the stylesheet. data: URIs are inline, not files."""
    out = []
    for u in utterances_of(bundle):
        out.append((u["id"], u["audio_file"]))
    for block in bundle["blocks"].values():
        for field in ("audio", "heard", "image"):
            if block.get(field):
                out.append((f"{block['id']}.{field}", block[field]["file"]))
        for m in REF_ATTR.finditer(block.get("html") or ""):
            out.append((f"{block['id']} html {m.group(1)}", m.group(2)))
        for m in CSS_URL.finditer(block.get("html") or ""):
            out.append((f"{block['id']} html url()", m.group(1)))
    for m in CSS_URL.finditer(css):
        out.append(("blocks.css url()", m.group(1)))
    return [(at, p) for at, p in out if not p.startswith(("data:", "#"))]


def check_fit(bundle: dict, f: Findings) -> None:
    """LP-FIT (contracts 1.9.0; the engine's PUB-FIT before them, ADR 041): a board's `fit` is
    "whole", on a table board the camera may zoom (rule 13; not a question, Listening or map board),
    in a bundle of 1.21 or later."""
    for x in bundle["boards"]:
        if "fit" not in x:
            continue
        table = bundle["blocks"].get(x.get("table") or "") or {}
        if x["fit"] != "whole":
            f.error("LP-FIT", "bundle.json", "a board's fit must be \"whole\"", x["id"])
        if not table or x.get("split") or x.get("listen") or table.get("map"):
            f.error("LP-FIT", "bundle.json", "fit on a board that is not a table board the camera may zoom", x["id"])
        if version_tuple(bundle["format_version"]) < (1, 21):
            f.error("LP-FIT", "bundle.json", "fit in a bundle before format 1.21", x["id"])


def table_cell(table: dict | None, row: int, col: int | None) -> bool:
    """A body cell of a table block: its row exists and, where the row lists its cells, the column."""
    rows = (table or {}).get("rows") or []
    if row >= len(rows):
        return False
    return col is None or not isinstance(rows[row], list) or col < len(rows[row])


def check_style(bundle: dict, f: Findings) -> None:
    """LP-STYLE, LP-EFFECTS, LP-CELLS (contracts 1.12.0, bundle 1.22; the site's `checkStyle`): a
    lesson in style C has `effects` on every state and only then; each effect lies inside its state,
    in time order, on a block of its board, a zoom on the board's table and a row of it; a focus
    entry's `cells` only with a row and inside the board's table. Before 1.22 none of the three
    fields is allowed. Each rule broken is its own finding, as the site reports it."""
    where = "bundle.json"
    at122 = version_tuple(bundle["format_version"]) >= (1, 22)
    style = "style" in bundle["lesson"]
    if style and not at122:
        f.error("LP-STYLE", where, "lesson.style is a field of bundle format 1.22 and later", "lesson")
    for x in bundle["boards"]:
        table = bundle["blocks"].get(x["table"]) if x.get("table") else None
        own = set(x.get("fixed") or []) | set(x.get("pinned") or {}) | ({x["table"]} if x.get("table") else set())
        own |= {i for s in x["states"] for i in (s.get("working") or []) + (s.get("overlay") or [])}
        for s in x["states"]:
            effects = s.get("effects")
            if effects is None:
                if style and at122:
                    f.error("LP-STYLE", where, "a style C lesson has effects on every state", s["id"])
                continue
            if not at122:
                f.error("LP-EFFECTS", where, "effects is a field of bundle format 1.22 and later", s["id"])
                continue
            if not style:
                f.error("LP-STYLE", where, "a state has effects only in a style C lesson", s["id"])
            last = float("-inf")
            for i, e in enumerate(effects):
                at = f"{s['id']} effects[{i}]"
                if e["time"] + TIME_TOLERANCE_S < last:
                    f.error("LP-EFFECTS", where, "effects are in time order", at)
                last = max(last, e["time"])
                if not e["time"] < e["until"] or e["time"] + TIME_TOLERANCE_S < s["start"] \
                        or e["until"] > s["until"] + TIME_TOLERANCE_S:
                    f.error("LP-EFFECTS", where, "an effect starts before it ends, both inside its state "
                            "(start <= time < until <= until)", at)
                if e["block"] not in own:
                    f.error("LP-EFFECTS", where, "an effect names a block of its board", at)
                if e["type"] == "zoom":
                    if not x.get("table") or e["block"] != x["table"]:
                        f.error("LP-EFFECTS", where, "a zoom's block is the board's table", at)
                    elif e.get("row") is None or not table_cell(table, e["row"], e.get("col")):
                        f.error("LP-EFFECTS", where, "a zoom names a row (and column) of the table", at)
        for i, entry in enumerate(x.get("focus") or []):
            if "cells" not in entry:
                continue
            at = f"{x['id']} focus[{i}]"
            if not at122:
                f.error("LP-CELLS", where, "cells is a field of bundle format 1.22 and later", at)
            elif entry.get("row") is None:
                f.error("LP-CELLS", where, "cells only on a focus entry with a row", at)
            elif not table or any(not table_cell(table, r, c) for r, c in entry["cells"]):
                f.error("LP-CELLS", where, "every cell lies inside the board's table", at)


PRACTICE_ID = re.compile(r"^oa-[a-z]+-([0-9]{6})(-[oc][0-9]+)?$")


def check_practice(bundle: dict, f: Findings) -> None:
    """LP-PRACTICE (its first half: practice points only from 1.23), LP-ID-BLOCK and LP-FIXTURE
    (contracts 1.13.0): every ID of a practice item (the item, its parts, options and self-check
    points) is in the lesson engine's block, 900000-989999; a fixture ID (990000-999999) is refused,
    as the site refuses it in production. The rest of the practice rules are the site's validator's."""
    where = "bundle.json"
    at123 = version_tuple(bundle["format_version"]) >= (1, 23)

    def ids(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("item_id", "gap_id", "option_id", "point_id") and isinstance(v, str):
                    yield v
                else:
                    yield from ids(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from ids(v)

    for bd in bundle.get("boards", []):
        for s in bd.get("states", []):
            cues = [c for u in s.get("utterances", []) for c in u.get("cues", [])]
            if not at123 and (s.get("practice") or any("practice" in c for c in cues)):
                f.error("LP-PRACTICE", where, "practice is a field of bundle format 1.23 and later", s["id"])
            for p in s.get("practice") or []:
                for i in ids(p.get("items")):
                    m = PRACTICE_ID.match(i)
                    n = int(m[1]) if m else -1
                    if 990000 <= n <= 999999:
                        f.error("LP-FIXTURE", where, "a practice item has a fixture ID (refused in production)", i)
                    elif not 900000 <= n <= 989999:
                        f.error("LP-ID-BLOCK", where, "a practice item's ID is outside the engine's block "
                                "(900000-989999)", i)


def check_inside(bundle: dict, css: str, folder: Path, f: Findings) -> None:
    """PUB-OUTSIDE (the engine's own): every reference resolves to a file inside the package."""
    for at, p in references(bundle, css):
        if outside(p) or re.match(r"^[a-z]+:", p, re.I) or not (folder / p).is_file():
            f.error("PUB-OUTSIDE", "package", "a reference points outside the package or to no file in it",
                    f"{at}: {p}")


def validate_package(folder: Path, contracts: Contracts) -> Findings:
    """Every check of a package folder; reports everything it can find."""
    f = Findings()
    docs = {}
    for name, schema, code in (("manifest.json", "lesson-manifest", "LP-MANIFEST"),
                               ("bundle.json", "lesson-bundle", "LP-BUNDLE"),
                               ("text.json", "lesson-text", "LP-TEXT")):
        p = folder / name
        if not p.is_file():
            f.error(f"{code}-MISSING", name, "file not found")
            continue
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            f.error("JSON-INVALID", name, f"not valid JSON: {e}")
            continue
        if schema_check(contracts, schema, doc, f, f"{code}-SCHEMA", name):
            docs[name] = doc
    css_path = folder / "blocks.css"
    if not css_path.is_file():
        f.error("LP-STYLESHEET-MISSING", "blocks.css", "file not found")
    m, b, t = docs.get("manifest.json"), docs.get("bundle.json"), docs.get("text.json")
    if b:
        check_bundle(b, folder, f)
        if t:
            check_text(t, b, f)
        check_inside(b, css_path.read_text(encoding="utf-8") if css_path.is_file() else "", folder, f)
        check_fit(b, f)
        check_style(b, f)
        check_practice(b, f)
    if m:
        check_manifest(m, folder, contracts, f)
        if b:
            check_manifest_against_bundle(m, b, f)
    listed = set(CONTRACT_FILES) | {x["path"] for x in (m or {}).get("media", [])}
    extra = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")
                   if p.is_file() and p.relative_to(folder).as_posix() not in listed)
    if extra:
        f.warning("LP-UNLISTED-FILE", "package", "files not part of the package are ignored and never published",
                  ", ".join(extra[:6]))
    return f


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", nargs="?", type=Path, help="a package folder to check")
    ap.add_argument("--fetch", action="store_true", help="download the pinned contracts and check their hash")
    a = ap.parse_args()
    if a.fetch:
        print(f"contracts {lock()['version']}: {fetch()} (SHA-256 checked)")
    if a.folder:
        f = validate_package(a.folder, load())
        print("\n".join(f.lines()) or "  no findings")
        print(f"{'PASS' if f.ok else 'FAIL'}: errors {f.codes('error')}, warnings {f.codes('warning')}")
        sys.exit(0 if f.ok else 1)
    if not a.fetch:
        ap.print_help()


if __name__ == "__main__":
    main()
