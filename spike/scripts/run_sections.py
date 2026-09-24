"""Build the screens of every section of a lesson, one after another, within
a budget, and stop at the first failure rather than fix it silently.

    .venv/Scripts/python spike/scripts/run_sections.py <lesson_dir> --budget 9.0 [--skip 13]

For each section in lesson order (analysis/sections.json), skipping those
named and those already built (a screens.json whose audit has no failures):
run write_screens.py --pages ... --call, read the cost from the raw response,
and record cost, boards, erase points, element counts, audit result and deck
defects applied in analysis/screens/sections_report.json.

Stops, with the reason on stdout, when: a section's audit fails (the model's
output does not meet a rule, or a rule does not fit the section), the model
call fails, or the next call would exceed the budget. A stopped run leaves
no section half-written: a section is either fully rendered or absent.
"""

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

RATE_IN, RATE_OUT = 5, 25          # $ per million tokens, as the stages print it
EST_PER_SECTION = 0.75             # the guard before a call, from page-13 runs


def cost_of(raw: dict) -> float:
    u = raw.get("usage") or {}
    return (u.get("input_tokens", 0) * RATE_IN + u.get("output_tokens", 0) * RATE_OUT) / 1e6


def summarise(lesson: Path, pages: list[int]) -> dict | None:
    out_dir = paths.screens_dir_for(lesson, pages)
    sp = out_dir / "screens.json"
    if not sp.exists():
        return None
    d = json.loads(sp.read_text(encoding="utf-8"))
    raw = json.loads((out_dir / "raw_response.json").read_text(encoding="utf-8"))
    blocks = [b for t in d["topics"] for h in t["thoughts"] for b in h["blocks"]]
    fails = [f for f in d["audit"] if f["severity"] == "fail"]
    warns = [f for f in d["audit"] if f["severity"] == "warn"]
    return {"pages": pages, "section": d["section"]["title"], "cost": round(cost_of(raw), 3),
            "boards": len(d["boards"]),
            "erase_points": sum(len(b["erasures"]) for b in d["boards"]),
            "blocks": len(blocks),
            "types": dict(collections.Counter(b["type"] for b in blocks)),
            "tags": sum(len(b.get("tags") or []) for b in blocks),
            "icons": sum(1 for b in blocks if b.get("icon")),
            "audit": {"failures": len(fails), "warnings": len(warns),
                      "fail_text": [f["what"] for f in fails][:6]},
            "defects_applied": [c["original"] for c in d.get("corrections", [])],
            "dropped": len(d.get("dropped", [])), "unresolved": len(d.get("unresolved", []))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--budget", type=float, required=True, help="dollars for this run")
    ap.add_argument("--skip", default="", help="comma-separated pages whose sections are skipped")
    args = ap.parse_args()
    skip = {int(p) for p in args.skip.split(",") if p.strip()}
    sections = json.loads((args.lesson_dir / "analysis" / "sections.json").read_text(encoding="utf-8"))["sections"]
    report_path = args.lesson_dir / "analysis" / "screens" / "sections_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {"sections": []}
    spent = 0.0
    py = sys.executable

    for sec in sections:
        pages = sec["pages"]
        if set(pages) & skip:
            print(f"skip pages {pages}: {sec['title']!r}")
            continue
        # A saved response with no screens.json (a run killed between the call
        # and the render) is re-rendered for free before anything is paid for.
        out_dir = paths.screens_dir_for(args.lesson_dir, pages)
        if (out_dir / "raw_response.json").exists() and not (out_dir / "screens.json").exists():
            subprocess.run([py, str(Path(__file__).with_name("write_screens.py")), str(args.lesson_dir),
                            "--pages", ",".join(str(p) for p in pages), "--render"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        done = summarise(args.lesson_dir, pages)
        if done and done["audit"]["failures"] == 0:
            print(f"already built pages {pages}: {sec['title']!r}")
            continue
        if spent + EST_PER_SECTION > args.budget:
            print(f"STOP: budget. Spent ${spent:.2f} of ${args.budget:.2f}; the next section "
                  f"({sec['title']!r}) would exceed it.")
            break
        print(f"=== pages {pages}: {sec['title']!r}")
        r = subprocess.run([py, str(Path(__file__).with_name("write_screens.py")), str(args.lesson_dir),
                            "--pages", ",".join(str(p) for p in pages), "--call"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = "\n".join(r.stdout.splitlines()[-14:])
        print(tail)
        s = summarise(args.lesson_dir, pages)
        if s:
            spent += s["cost"]
            report["sections"] = [x for x in report["sections"] if x["pages"] != pages] + [s]
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        if r.returncode != 0 or not s or s["audit"]["failures"]:
            print(f"STOP: pages {pages} did not pass ("
                  + (("audit: " + "; ".join(s["audit"]["fail_text"])) if s else r.stderr[-600:])
                  + "). Nothing further was built.")
            break
    print(f"spent this run: ${spent:.2f}")


if __name__ == "__main__":
    main()
