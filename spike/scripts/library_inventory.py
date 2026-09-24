"""Inventory a folder of lesson videos: per file its duration, resolution,
bitrates and size, with likely duplicates, written to a CSV, and totals at the
end. Free: ffprobe and a partial file hash, no API.

    python spike/scripts/library_inventory.py <folder> [--out inventory.csv] [--workers 4]

Walks <folder> recursively for video files (.mp4 .mov .mkv .avi .m4v .webm .wmv
.flv .mpg .mpeg .ts). For each: ffprobe's format and streams, and a hash of
the file's size plus its first and last 4 MB (whole-file hashing of a library
of two-hour recordings would take hours; this is enough to tell copies apart).

Duplicates, two kinds:
  same file        same size and same partial hash: a copy. The CSV names the
                   first copy found; its size counts as reclaimable space.
  likely duplicate same duration (within 2 seconds) and same resolution, but a
                   different file: probably the same recording re-encoded or
                   re-exported. Reported, never assumed.

The CSV (default spike/out/library_inventory.csv, or --out) has one row per
file, then a blank row and the totals. Totals are also printed. Nothing in the
scanned folder is changed or written.
"""

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

VIDEO = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm", ".wmv", ".flv", ".mpg", ".mpeg", ".ts"}
CHUNK = 4 * 1024 * 1024
DURATION_TOLERANCE_S = 2.0
FIELDS = ["path", "file", "size_mb", "duration_s", "duration", "width", "height", "fps",
          "video_codec", "video_kbps", "audio_codec", "audio_kbps", "audio_hz", "channels",
          "total_kbps", "partial_hash", "duplicate_kind", "duplicate_of", "error"]


def hms(t: float) -> str:
    t = int(round(t))
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


def partial_hash(p: Path, size: int) -> str:
    h = hashlib.sha256(str(size).encode())
    with p.open("rb") as f:
        h.update(f.read(CHUNK))
        if size > 2 * CHUNK:
            f.seek(size - CHUNK)
            h.update(f.read(CHUNK))
    return h.hexdigest()[:16]


def kbps(v) -> int | None:
    try:
        return round(int(v) / 1000)
    except (TypeError, ValueError):
        return None


def probe(p: Path, root: Path) -> dict:
    size = p.stat().st_size
    row = {"path": str(p.relative_to(root)), "file": p.name, "size_mb": round(size / 1e6, 1),
           "error": ""}
    try:
        row["partial_hash"] = partial_hash(p, size)
    except OSError as e:
        row["error"] = f"read: {e}"
    r = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json",
                        str(p)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        row["error"] = (row["error"] + " ffprobe: " + r.stderr.strip()[-200:]).strip()
        return row
    d = json.loads(r.stdout or "{}")
    fmt = d.get("format", {})
    dur = float(fmt.get("duration") or 0)
    row.update(duration_s=round(dur, 1), duration=hms(dur), total_kbps=kbps(fmt.get("bit_rate")))
    for st in d.get("streams", []):
        if st.get("codec_type") == "video" and "width" not in row:
            num, _, den = (st.get("avg_frame_rate") or "0/1").partition("/")
            fps = float(num) / float(den) if den and float(den) else None
            row.update(width=st.get("width"), height=st.get("height"),
                       fps=round(fps, 2) if fps else None, video_codec=st.get("codec_name"),
                       video_kbps=kbps(st.get("bit_rate")))
        elif st.get("codec_type") == "audio" and "audio_codec" not in row:
            row.update(audio_codec=st.get("codec_name"), audio_kbps=kbps(st.get("bit_rate")),
                       audio_hz=st.get("sample_rate"), channels=st.get("channels"))
    return row


def mark_duplicates(rows: list[dict]) -> None:
    by_hash: dict[tuple, dict] = {}
    for r in rows:
        key = (r.get("size_mb"), r.get("partial_hash"))
        if r.get("partial_hash") and key in by_hash:
            r["duplicate_kind"], r["duplicate_of"] = "same file", by_hash[key]["path"]
        elif r.get("partial_hash"):
            by_hash[key] = r
    firsts = [r for r in rows if not r.get("duplicate_kind") and r.get("duration_s")]
    for i, r in enumerate(firsts):
        for o in firsts[:i]:
            if (abs(r["duration_s"] - o["duration_s"]) <= DURATION_TOLERANCE_S
                    and (r.get("width"), r.get("height")) == (o.get("width"), o.get("height"))):
                r["duplicate_kind"], r["duplicate_of"] = "likely duplicate", o["path"]
                break


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    root = a.folder.resolve()
    if not root.is_dir():
        raise SystemExit(f"not a folder: {root}")
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO)
    if not files:
        raise SystemExit(f"no video files under {root}")
    print(f"{len(files)} video files under {root}; probing...", flush=True)
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        rows = list(ex.map(lambda p: probe(p, root), files))
    mark_duplicates(rows)

    ok = [r for r in rows if not r.get("error")]
    total_s = sum(r.get("duration_s") or 0 for r in ok)
    total_gb = sum(r["size_mb"] for r in rows) / 1000
    same = [r for r in rows if r.get("duplicate_kind") == "same file"]
    likely = [r for r in rows if r.get("duplicate_kind") == "likely duplicate"]
    resolutions: dict[str, int] = {}
    for r in ok:
        k = f"{r.get('width')}x{r.get('height')}"
        resolutions[k] = resolutions.get(k, 0) + 1
    unique_s = sum(r.get("duration_s") or 0 for r in ok if r.get("duplicate_kind") != "same file")
    totals = [
        ("files", len(rows)),
        ("files that could not be read", len(rows) - len(ok)),
        ("total size (GB)", round(total_gb, 2)),
        ("total duration", hms(total_s)),
        ("total duration without exact copies", hms(unique_s)),
        ("exact copies (same file)", len(same)),
        ("space in exact copies (GB)", round(sum(r["size_mb"] for r in same) / 1000, 2)),
        ("likely duplicates (same length and resolution)", len(likely)),
        ("resolutions", "; ".join(f"{k}: {v}" for k, v in sorted(resolutions.items(),
                                                                  key=lambda kv: -kv[1]))),
    ]

    out = a.out or (Path(__file__).resolve().parents[1] / "out" / "library_inventory.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
        f.write("\n")
        tw = csv.writer(f)
        tw.writerow(["TOTALS"])
        for k, v in totals:
            tw.writerow([k, v])
    for k, v in totals:
        print(f"{k}: {v}")
    for r in same + likely:
        print(f"  {r['duplicate_kind']}: {r['path']}  ->  {r['duplicate_of']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
