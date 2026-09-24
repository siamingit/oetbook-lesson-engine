"""Run one lesson through the whole pipeline, stopping only at the maintainer's
review gates, and resuming from where it stopped (docs/03-RUNBOOK.md).

    .venv/Scripts/python spike/scripts/build_lesson.py <lesson_dir> --status
    .venv/Scripts/python spike/scripts/build_lesson.py <lesson_dir> --budget 40
    .venv/Scripts/python spike/scripts/build_lesson.py <lesson_dir> --approve screens --by NAME

Every stage has a test for "done and passing"; a stage that passes is
skipped, so running the command again continues from the first stage that
does not. The run stops at:
  - a GATE the maintainer has not approved (source, keyterms, screens,
    narration, lexicon, final), with what to review and how to approve;
  - a stage that fails, with its output in <lesson>/analysis/runner.log;
  - a paid stage whose estimated cost would take the lesson's model spend
    (Anthropic + Gemini, measured from the saved responses) over --budget.
Paid stages never run without --budget (AGENTS.md: paid calls are approved).
Approvals are recorded in <lesson>/analysis/gates.json with who and when.

Nothing here decides content. The runner only orders the stages that exist,
checks their outputs, and refuses to go past a gate or a failure.
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paths                                                      # noqa: E402

PY = sys.executable
GATES = {
    "source": "the preflight pack (analysis/preflight/preflight_pack.zip): deck pages, "
              "text or image, templates, section titles, video frames and specs; plus the "
              "lesson description (build_sections.py --description) and the diagram "
              "slides (--diagram-pages)",
    "keyterms": "analysis/keyterms_candidates.json: write analysis/keyterms_curated.txt, the "
                "terms the transcription is told to listen for",
    "screens": "analysis/screens/lesson-preview/index.html: every board of the lesson",
    "narration": "generated/lesson-preview/silent/player.html and "
                 "analysis/narration/lesson-review/index.html: the narration with QA pass 1; "
                 "fixes go through write_narration.py --states --brief, then one QA pass on "
                 "the rewritten states",
    "lexicon": "spike/out/lexicon-review/index.html: terms the ear did not hear, and any new "
               "lexicon entry; approve with lexicon.py --approve TERM --by NAME",
    "final": "generated/lesson-player/player.html: the finished lesson",
}
# Estimated model cost per unit, from Grammar 1 (docs/03-RUNBOOK.md, baseline).
EST = {"understanding": 0.40, "screens": 0.75, "narration": 0.65, "qa": 0.15}


class Stop(Exception):
    pass


def log(L: Path, text: str) -> None:
    with (L / "analysis" / "runner.log").open("a", encoding="utf-8") as f:
        f.write(text + "\n")


def run(L: Path, args: list[str], what: str) -> str:
    """Run a pipeline script; its output goes to runner.log. A non-zero exit
    stops the run."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    cmd = [PY, "-u"] + args
    log(L, f"\n=== {datetime.datetime.now():%Y-%m-%d %H:%M} {what}\n$ {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, cwd=HERE.parents[1])
    log(L, r.stdout + r.stderr)
    if r.returncode != 0:
        raise Stop(f"{what} failed (exit {r.returncode}). Last output:\n"
                   + "\n".join((r.stdout + r.stderr).strip().splitlines()[-12:])
                   + f"\nFull output: {L / 'analysis' / 'runner.log'}")
    return r.stdout


def gates(L: Path) -> dict:
    p = L / "analysis" / "gates.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def require_gate(L: Path, name: str) -> None:
    if name not in gates(L):
        raise Stop(f"GATE '{name}': review {GATES[name]}.\nThen: .venv/Scripts/python "
                   f"spike/scripts/build_lesson.py {L} --approve {name} --by NAME")


def spent(L: Path) -> float:
    """Model spend so far, measured from the saved responses: Anthropic
    (understanding, screens, narration and its splices) and Gemini (QA)."""
    total = 0.0
    for p in (L / "analysis").rglob("raw_response*.json"):
        if "qa" in p.parts:
            continue
        try:
            u = json.loads(p.read_text(encoding="utf-8")).get("usage") or {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if "input_tokens" in u:
            total += (u["input_tokens"] * 5 + u.get("output_tokens", 0) * 25) / 1e6
    for p in (L / "analysis").rglob("qa/qa_*.json"):
        total += json.loads(p.read_text(encoding="utf-8")).get("meta", {}).get("cost_usd", 0)
    return total


def afford(L: Path, budget: float | None, estimate: float, what: str) -> None:
    if budget is None:
        raise Stop(f"{what} is a paid stage (about ${estimate:.2f}). Run with --budget USD "
                   "to allow model spend for this lesson.")
    s = spent(L)
    if s + estimate > budget:
        raise Stop(f"BUDGET: {what} would cost about ${estimate:.2f}; spent ${s:.2f} of "
                   f"${budget:.2f}. Raise --budget to continue.")


def sections(L: Path) -> tuple[dict, list[dict]]:
    info = json.loads((L / "analysis" / "sections.json").read_text(encoding="utf-8"))
    secs = list(info["sections"])
    cp = info.get("contents_page")
    intro = [{"title": "Introduction", "pages": [cp]}] if cp else []
    return info, intro + secs


def audit_ok(p: Path) -> bool:
    if not p.exists():
        return False
    return not any(f["severity"] == "fail" for f in json.loads(p.read_text(encoding="utf-8"))["audit"])


def pp(pages: list[int]) -> str:
    return ",".join(str(p) for p in pages)


# ---------------------------------------------------------------------------
# Stages, in order. Each: (name, done?, do).
# ---------------------------------------------------------------------------

def stage_preflight(L, a):
    """The preflight pack (preflight_pack.py): thumbnails, text or image pages,
    template groups, section headings with anything needing a title flagged,
    video frames and specs, in one small zip for review in chat. The source
    gate waits on it; the pack is rebuilt when the sections change."""
    pack = L / "analysis" / "preflight" / "preflight_pack.zip"
    sp = L / "analysis" / "sections.json"
    if not pack.exists() or (sp.exists() and sp.stat().st_mtime > pack.stat().st_mtime):
        print(run(L, [str(HERE / "preflight_pack.py"), str(L)], "preflight pack").strip())
    facts = json.loads((L / "analysis" / "preflight.json").read_text(encoding="utf-8"))
    if facts.get("needs_title"):
        raise Stop(f"GATE 'source': sections without a title, pages {facts['needs_title']}. "
                   "Set each with build_sections.py --set PAGE \"TITLE\"; the pack is rebuilt "
                   f"on the next run. Pack: {pack}")
    if "source" not in gates(L):
        raise Stop(f"GATE 'source': review the preflight pack {pack} (summary.md inside), "
                   "set the lesson description (build_sections.py --description) and the "
                   "diagram slides (--diagram-pages).\nThen: .venv/Scripts/python "
                   f"spike/scripts/build_lesson.py {L} --approve source --by NAME")


def stage_audio(L, a):
    if not (L / "analysis" / "audio.mp3").exists():
        run(L, [str(HERE / "extract_audio.py"), str(L)], "extract audio")


def stage_keyterm_candidates(L, a):
    if not (L / "analysis" / "keyterms_candidates.json").exists():
        run(L, [str(HERE / "extract_keyterms.py"), str(L)], "keyterm candidates")


def stage_keyterms(L, a):
    curated = L / "analysis" / "keyterms_curated.txt"
    if not curated.exists():
        raise Stop(f"GATE 'keyterms': write {curated} from keyterms_candidates.json, then "
                   f"--approve keyterms")
    require_gate(L, "keyterms")
    kt = L / "analysis" / "keyterms.json"
    if not kt.exists() or kt.stat().st_mtime < curated.stat().st_mtime:
        run(L, [str(HERE / "build_keyterms.py"), str(L)], "build keyterms")


def stage_transcribe(L, a):
    if not (L / "analysis" / "scribe_v2_response.json").exists():
        if a.budget is None:
            raise Stop("transcription (Scribe, about $0.30 per hour of video) is paid: run with "
                       "--budget USD")
        run(L, [str(HERE / "transcribe.py"), str(L)], "transcribe (Scribe v2)")
    if not (L / "analysis" / "transcript.txt").exists():
        run(L, [str(HERE / "make_transcript.py"), str(L / "analysis")], "readable transcript")


def stage_slides(L, a):
    if (L / "analysis" / "slides" / "slide_timeline.json").exists():
        return
    st = str(HERE / "build_slide_timeline.py")
    run(L, [st, str(L)], "slide timeline, stage 1 (decodes the video)")
    run(L, [st, str(L), "--stage2"], "slide timeline, stage 2 (decodes the video)")
    run(L, [st, str(L), "--score-max", "0.035", "--margin-min", "0.04",
            "--margin-min-stage2", "0.05"], "slide timeline, resolve")


def stage_annotations(L, a):
    if not (L / "analysis" / "annotations" / "annotation_events.json").exists():
        run(L, [str(HERE / "extract_annotations.py"), str(L)], "annotations")


def stage_sections(L, a):
    p = L / "analysis" / "sections.json"
    if not p.exists():
        run(L, [str(HERE / "build_sections.py"), str(L)], "sections from the deck")
    info = json.loads(p.read_text(encoding="utf-8"))
    need = [s["pages"] for s in info["sections"] if s.get("status") == "needs-title"]
    if need:
        raise Stop(f"sections without a title, pages {need}: set each with "
                   "build_sections.py --set PAGE \"TITLE\"")


def stage_understanding(L, a):
    info, secs = sections(L)
    pages = sorted({p for s in secs for p in s["pages"]})
    todo = [p for p in pages if not (paths.understanding_dir(L, p) / "understanding.json").exists()]
    for p in todo:
        afford(L, a.budget, EST["understanding"], f"understanding of page {p}")
        run(L, [str(HERE / "extract_understanding.py"), str(L), "--page", str(p), "--call"],
            f"understanding, page {p}")


def stage_screens(L, a):
    info, secs = sections(L)
    body = secs[1:] if info.get("contents_page") else secs
    todo = [s for s in body if not audit_ok(paths.screens_dir_for(L, s["pages"]) / "screens.json")]
    if todo:
        afford(L, a.budget, EST["screens"], "screens of the next section")
        remaining = max(0.0, a.budget - spent(L))
        run(L, [str(HERE / "run_sections.py"), str(L), "--budget", f"{remaining:.2f}"],
            "screens, section by section")
        todo = [s for s in body if not audit_ok(paths.screens_dir_for(L, s["pages"]) / "screens.json")]
        if todo:
            raise Stop("screens not complete for: " + ", ".join(s["title"] for s in todo)
                       + ". See analysis/screens/sections_report.json and runner.log.")
    run(L, [str(HERE / "build_lesson_boards.py"), str(L)], "title and contents boards")
    run(L, [str(HERE / "build_lesson_preview.py"), str(L)], "screens preview")
    require_gate(L, "screens")


def stage_narration(L, a):
    info, secs = sections(L)
    cp = info.get("contents_page")
    if cp:
        nd = paths.narration_dir_for(L, [cp])
        if not audit_ok(nd / "narration.json"):
            afford(L, a.budget, EST["narration"] / 3, "introduction narration")
            run(L, [str(HERE / "write_narration.py"), str(L), "--pages", str(cp), "--call"],
                "introduction narration")
        if not (nd / "qa" / "qa_pass1.json").exists():
            afford(L, a.budget, EST["qa"] / 2, "introduction QA pass 1")
            run(L, [str(HERE / "qa_narration.py"), str(L), "--pages", str(cp), "--call",
                    "--pass", "1"], "introduction QA pass 1")
    body = secs[1:] if cp else secs
    todo = [s for s in body
            if not audit_ok(paths.narration_dir_for(L, s["pages"]) / "narration.json")
            or not (paths.narration_dir_for(L, s["pages"]) / "qa" / "qa_pass1.json").exists()]
    if todo:
        afford(L, a.budget, EST["narration"] + EST["qa"], "narration of the next section")
        run(L, [str(HERE / "run_narration.py"), str(L)], "narration and QA pass 1, section by section")
    run(L, [str(HERE / "build_silent_preview.py"), str(L)], "silent preview")
    run(L, [str(HERE / "build_narration_review.py"), str(L)], "narration review page")
    require_gate(L, "narration")


def stage_terms(L, a):
    info, secs = sections(L)
    failures = {}
    for s in secs:
        nd = paths.narration_dir_for(L, s["pages"]) / "narration.json"
        tc = paths.boards_dir_for(L, s["pages"]) / "terms_check.json"
        if not tc.exists() or tc.stat().st_mtime < nd.stat().st_mtime:
            if a.budget is None:
                raise Stop("the terms check synthesises and transcribes probes (a few "
                           "thousand characters): run with --budget USD")
            try:
                run(L, [str(HERE / "check_terms.py"), str(L), "--pages", pp(s["pages"])],
                    f"terms check, {s['title']}")
            except Stop:
                pass           # failures are listed below, for the lexicon gate
        if tc.exists():
            f = json.loads(tc.read_text(encoding="utf-8")).get("failures") or []
            if f:
                failures[s["title"]] = f
    if failures:
        (L / "analysis" / "terms_failures.json").write_text(
            json.dumps(failures, ensure_ascii=False, indent=1), encoding="utf-8")
        if "lexicon" not in gates(L):
            raise Stop("GATE 'lexicon': the ear did not hear these as written: "
                       + "; ".join(f"{k}: {', '.join(v)}" for k, v in failures.items())
                       + ".\nAdd real mispronunciations to spike/lexicon.json (lexicon_review.py "
                       "to hear them), then --approve lexicon; sections whose failures are "
                       "only transcription artefacts are then built with --accept-terms.")


def stage_audio_build(L, a):
    info, secs = sections(L)
    fails = json.loads((L / "analysis" / "terms_failures.json").read_text(encoding="utf-8")) \
        if (L / "analysis" / "terms_failures.json").exists() else {}
    for s in secs:
        from write_narration import spoken
        n = json.loads((paths.narration_dir_for(L, s["pages"]) / "narration.json").read_text(encoding="utf-8"))
        ip = paths.boards_dir_for(L, s["pages"]) / "audio_index.json"
        idx = json.loads(ip.read_text(encoding="utf-8")) if ip.exists() else {}
        need = [u["id"] for bd in n["boards"] for st in bd["states"] for u in st["utterances"]
                if (idx.get(u["id"]) or {}).get("text") != spoken(u["text_with_cues"])]
        if need:
            if a.budget is None:
                raise Stop("synthesis (Cartesia) is paid: run with --budget USD")
            cmd = [str(HERE / "synthesize_narration.py"), str(L), "--pages", pp(s["pages"])]
            if s["title"] in fails:
                cmd.append("--accept-terms")     # the lexicon gate has been approved
            run(L, cmd, f"synthesis, {s['title']} ({len(need)} utterances)")
        ear = paths.boards_dir_for(L, s["pages"]) / "ear.json"
        if not ear.exists() or ear.stat().st_mtime < ip.stat().st_mtime:
            try:
                run(L, [str(HERE / "ear.py"), str(L), "--pages", pp(s["pages"]), "--recompare"],
                    f"ear, {s['title']}")
            except Stop as e:
                log(L, f"EAR FAILURE (reported at the final gate): {e}")


def stage_player(L, a):
    run(L, [str(HERE / "build_lesson_player.py"), str(L)], "whole-lesson player")
    d = str(L / "generated" / "lesson-player")
    run(L, [str(HERE / "check_board_page.py"), str(L), "--dir", d], "structural check")
    run(L, [str(HERE / "check_marks.py"), str(L), "--dir", d], "mark check")
    require_gate(L, "final")


STAGES = [("preflight", stage_preflight), ("audio", stage_audio),
          ("keyterm candidates", stage_keyterm_candidates), ("keyterms", stage_keyterms),
          ("transcription", stage_transcribe), ("slide timeline", stage_slides),
          ("annotations", stage_annotations), ("sections", stage_sections),
          ("understanding", stage_understanding), ("screens", stage_screens),
          ("narration", stage_narration), ("terms check", stage_terms),
          ("audio and ear", stage_audio_build), ("player and checks", stage_player)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--budget", type=float, help="model spend allowed for this lesson, USD")
    ap.add_argument("--approve", choices=sorted(GATES))
    ap.add_argument("--by", default="maintainer")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    L = a.lesson_dir
    (L / "analysis").mkdir(parents=True, exist_ok=True)

    if a.approve:
        g = gates(L)
        g[a.approve] = {"by": a.by, "on": f"{datetime.datetime.now():%Y-%m-%d %H:%M}"}
        (L / "analysis" / "gates.json").write_text(json.dumps(g, indent=1), encoding="utf-8")
        print(f"gate '{a.approve}' approved by {a.by}")
        return
    if a.status:
        print(f"model spend so far: ${spent(L):.2f}"
              + (f" of ${a.budget:.2f}" if a.budget else ""))
        print("gates approved: " + (", ".join(f"{k} ({v['by']}, {v['on']})"
                                              for k, v in gates(L).items()) or "none"))
        return

    for name, fn in STAGES:
        try:
            print(f"- {name}", flush=True)
            fn(L, a)
        except Stop as e:
            print(f"\nSTOPPED at {name}:\n{e}")
            print(f"model spend so far: ${spent(L):.2f}")
            sys.exit(2)
    print(f"\nlesson complete: {L / 'generated' / 'lesson-player' / 'player.html'}")
    print(f"model spend: ${spent(L):.2f}")


if __name__ == "__main__":
    main()
