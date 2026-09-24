"""Write the narration of every built section of a lesson, one after another,
each followed by the first QA pass, and stop at the first failure rather than
fix it silently.

    .venv/Scripts/python spike/scripts/run_narration.py <lesson_dir> [--skip 13] [--only 7,8]

For each section in lesson order (analysis/sections.json) whose screens exist
and pass their audit, skipping those named and those already narrated (a
narration.json whose audit has no failures): run write_narration.py --pages
... --call, then qa_narration.py --pages ... --call --pass 1, and record cost,
utterances, words, cues by type, audit result and QA findings by severity in
analysis/narration/sections_report.json.

Stops, with the reason on stdout, when: a section's narration audit fails,
a call fails (including an exhausted API credit), or the section's screens
are missing or failing. A stopped run leaves no section half-written: a
section's narration is either fully rendered or absent.

The second QA pass is not run here: it follows the maintainer's brief for the
first pass's findings (write_narration.py --states ... --brief FILE), which is
a judgement, not a loop (methodology §18).
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


def cost_of(raw: dict) -> float:
    import llm
    return llm.raw_cost(raw)       # cache writes/reads and the batch discount included


def summarise(lesson: Path, pages: list[int]) -> dict | None:
    out_dir = paths.narration_dir_for(lesson, pages)
    np = out_dir / "narration.json"
    if not np.exists():
        return None
    d = json.loads(np.read_text(encoding="utf-8"))
    raw = json.loads((out_dir / "raw_response.json").read_text(encoding="utf-8"))
    utts = [u for bd in d["boards"] for s in bd["states"] for u in s["utterances"]]
    cues = collections.Counter(c["type"] for u in utts for c in u["cues"])
    words = sum(len(u["text_with_cues"].split()) for u in utts)
    fails = [f for f in d["audit"] if f["severity"] == "fail"]
    warns = [f for f in d["audit"] if f["severity"] == "warn"]
    splices = sum(s.get("cost", 0) for s in (d.get("inputs") or {}).get("splices", []))
    qa = {}
    for n in (1, 2):
        qp = out_dir / "qa" / f"qa_pass{n}.json"
        if qp.exists():
            q = json.loads(qp.read_text(encoding="utf-8"))
            qa[f"pass{n}"] = {"cost": q["meta"]["cost_usd"],
                              **dict(collections.Counter(f["severity"] for f in q["findings"]))}
    return {"pages": pages, "section": (d.get("section") or {}).get("title"),
            "cost": round(cost_of(raw) + splices, 3),
            "boards": len(d["boards"]),
            "utterances": len(utts), "words": words,
            "cues": dict(cues),
            "audit": {"failures": len(fails), "warnings": len(warns),
                      "fail_text": [f["what"] for f in fails][:6]},
            "qa": qa}


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable] + args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--skip", default="", help="comma-separated pages whose sections are skipped")
    ap.add_argument("--only", default="", help="comma-separated pages; only their sections")
    args = ap.parse_args()
    skip = {int(p) for p in args.skip.split(",") if p.strip()}
    only = {int(p) for p in args.only.split(",") if p.strip()}
    sections = json.loads((args.lesson_dir / "analysis" / "sections.json").read_text(encoding="utf-8"))["sections"]
    report_path = args.lesson_dir / "analysis" / "narration" / "sections_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {"sections": []}
    here = Path(__file__).resolve().parent
    spent = 0.0

    def record(pages):
        s = summarise(args.lesson_dir, pages)
        if s:
            report["sections"] = [x for x in report["sections"] if x["pages"] != pages] + [s]
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        return s

    for sec in sections:
        pages = sec["pages"]
        pp = ",".join(str(p) for p in pages)
        if set(pages) & skip or (only and not set(pages) & only):
            print(f"skip pages {pages}: {sec['title']!r}")
            continue
        sp = paths.screens_dir_for(args.lesson_dir, pages) / "screens.json"
        if not sp.exists():
            print(f"STOP: pages {pages} have no screens.")
            break
        scr = json.loads(sp.read_text(encoding="utf-8"))
        if any(f["severity"] == "fail" for f in scr["audit"]):
            print(f"STOP: pages {pages} screens fail their audit; narration is not written on "
                  "failing screens.")
            break
        done = summarise(args.lesson_dir, pages)
        if done and done["audit"]["failures"] == 0:
            print(f"already narrated pages {pages}: {sec['title']!r}")
            if "pass1" not in done["qa"]:
                print(f"=== QA pass 1, pages {pages}")
                r = run([str(here / "qa_narration.py"), str(args.lesson_dir), "--pages", pp,
                         "--call", "--pass", "1"])
                print("\n".join(r.stdout.splitlines()[-12:]))
                record(pages)
                if r.returncode != 0:
                    print(f"STOP: QA pass 1 failed for pages {pages}: {r.stderr[-600:]}")
                    break
            continue
        print(f"=== narration, pages {pages}: {sec['title']!r}")
        r = run([str(here / "write_narration.py"), str(args.lesson_dir), "--pages", pp, "--call"])
        print("\n".join(r.stdout.splitlines()[-16:]))
        s = record(pages)
        if s:
            spent += s["cost"]
        if r.returncode != 0 or not s or s["audit"]["failures"]:
            print(f"STOP: pages {pages} did not pass ("
                  + (("audit: " + "; ".join(s["audit"]["fail_text"])) if s else r.stderr[-800:])
                  + "). Nothing further was written.")
            break
        print(f"=== QA pass 1, pages {pages}")
        r = run([str(here / "qa_narration.py"), str(args.lesson_dir), "--pages", pp,
                 "--call", "--pass", "1"])
        print("\n".join(r.stdout.splitlines()[-12:]))
        s = record(pages)
        if r.returncode != 0:
            print(f"STOP: QA pass 1 failed for pages {pages}: {r.stderr[-600:]}")
            break
    print(f"narration spent this run: ${spent:.2f} (Anthropic); QA costs are in the report")


if __name__ == "__main__":
    main()
