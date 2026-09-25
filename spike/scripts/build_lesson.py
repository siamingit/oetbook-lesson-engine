"""Run one lesson through the whole pipeline, stopping only at the maintainer's
review gates, and resuming from where it stopped (docs/03-RUNBOOK.md).

    .venv/Scripts/python spike/scripts/build_lesson.py <lesson_dir> --status
    .venv/Scripts/python spike/scripts/build_lesson.py <lesson_dir> --budget 40
    .venv/Scripts/python spike/scripts/build_lesson.py <lesson_dir> --approve narration --by NAME

Every stage has a test for "done and passing"; a stage that passes is
skipped, so running the command again continues from the first stage that
does not. The run stops at:
  - a GATE the maintainer has not approved (source, narration, final; ADR
    005), with what to review and how to approve. The keyterms and screens
    steps are approved by the agent when their checks pass, recorded in
    gates.json as the agent's and appended to <lesson>/analysis/decisions.md;
  - a stage that fails, with its output in <lesson>/analysis/runner.log;
  - a paid stage whose estimated cost would take the lesson's model spend
    (Anthropic + Gemini, measured from the saved responses) over --budget.
Model stages run as direct calls with prompt caching; --batch runs each as one
batch at half price, only for an unattended run the maintainer asked for.
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
    "narration": "generated/lesson-preview/silent/player.html and "
                 "analysis/narration/lesson-review/index.html: the narration with QA pass 1; "
                 "fixes go through write_narration.py --states --brief, then one QA pass on "
                 "the rewritten states",
    "final": "generated/lesson-player/player.html: the finished lesson, and by ear every "
             "term the terms check did not hear as written (analysis/terms_failures.json; "
             "spike/out/lexicon-review/index.html); a new lexicon entry is approved with "
             "lexicon.py --approve TERM --by NAME",
}
# Estimated model cost per unit at FULL price, from Grammar 1 (docs/03-RUNBOOK.md,
# baseline); batched stages are charged at half (batch()).
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


def agent_approves(L: Path, name: str, why: str, reverse: str) -> None:
    """A step the agent approves when its checks pass (ADR 005): recorded in
    gates.json as the agent's, and in the lesson's decision log."""
    g = gates(L)
    if name in g:
        return
    g[name] = {"by": "agent (ADR 005): checks pass", "on": f"{datetime.datetime.now():%Y-%m-%d %H:%M}"}
    (L / "analysis" / "gates.json").write_text(json.dumps(g, indent=1), encoding="utf-8")
    log_decision(L, f"{name} step approved by the agent", why,
                 "ADR 005: keyterms and screens are approved by the agent when their checks pass",
                 reverse)


def log_decision(L: Path, what: str, why: str, rule: str, reverse: str) -> None:
    """Append one decision to the lesson's decision log (ADR 005)."""
    p = L / "analysis" / "decisions.md"
    head = "" if p.exists() else (f"# Decision log: {L.name}\n\nDecisions made without asking "
                                  "under ADR 005. The maintainer reviews them at the gates and "
                                  "may reverse any.\n")
    with p.open("a", encoding="utf-8") as f:
        f.write(head + f"\n## {datetime.datetime.now():%Y-%m-%d %H:%M} {what}\n\n- Why: {why}\n"
                f"- Rule: {rule}\n- To reverse: {reverse}\n")


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
            import llm
            total += llm.raw_cost(json.loads(p.read_text(encoding="utf-8")))
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
    intro = paths.intro_section(info)
    return info, ([intro] if intro else []) + list(info["sections"])


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
    if not paths.intro_section(json.loads(sp.read_text(encoding="utf-8"))):
        raise Stop("GATE 'source': the deck has no contents slide, so the lesson has no "
                   "introduction yet: name the title slide with build_sections.py --title-page "
                   "PAGE (docs/00-PRODUCT.md §2a)")
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
        raise Stop(f"keyterms: write {curated} from keyterms_candidates.json (the agent curates "
                   "it, methodology §12), then re-run")
    kt = L / "analysis" / "keyterms.json"
    if not kt.exists() or kt.stat().st_mtime < curated.stat().st_mtime:
        run(L, [str(HERE / "build_keyterms.py"), str(L)], "build keyterms")
    agent_approves(L, "keyterms", "keyterms.json built from keyterms_curated.txt and verified "
                   "against the deck by build_keyterms.py",
                   "edit analysis/keyterms_curated.txt and delete analysis/scribe_v2_response.json "
                   "to transcribe again (Scribe, paid)")


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


def batch(L, stage: str, pending: int, unit_est: float, a) -> None:
    """One model stage for every pending unit, within the budget
    (run_batch_stage.py): direct calls with prompt caching by default, or with
    --batch one batch at half price, for an unattended run (docs/03-RUNBOOK.md,
    "Cost controls"). A batch already submitted is collected first, never paid
    for twice."""
    if pending == 0 and not (L / "analysis" / "batches" / f"{stage}.json").exists():
        return
    if a.batch:
        afford(L, a.budget, pending * unit_est * 0.5, f"{stage}: {pending} units in one batch")
        run(L, [str(HERE / "run_batch_stage.py"), str(L), "--stage", stage],
            f"{stage}, one batch of {pending}")
    else:
        afford(L, a.budget, pending * unit_est, f"{stage}: {pending} direct calls")
        run(L, [str(HERE / "run_batch_stage.py"), str(L), "--stage", stage, "--direct"],
            f"{stage}, {pending} direct calls")


def stage_understanding(L, a):
    info, secs = sections(L)
    if secs and secs[0].get("span") and secs[0]["span"][1] is None:
        raise Stop("the introduction's source is the recording's opening (no contents slide), "
                   "and where the opening ends is not set: read analysis/transcript.txt and set "
                   f"it with build_sections.py {L} --intro-range 0 SECONDS")
    pages = sorted({p for s in secs for p in s["pages"]})
    todo = [p for p in pages if not (paths.understanding_dir(L, p) / "understanding.json").exists()]
    batch(L, "understanding", len(todo), EST["understanding"], a)


def stage_screens(L, a):
    info, secs = sections(L)
    body = [s for s in secs if not s.get("intro")]
    todo = [s for s in body if not audit_ok(paths.screens_dir_for(L, s["pages"]) / "screens.json")]
    try:
        batch(L, "screens", len(todo), EST["screens"], a)
    except Stop as e:
        todo = [s for s in body if not audit_ok(paths.screens_dir_for(L, s["pages"]) / "screens.json")]
        if not todo:
            raise
        raise Stop(str(e) + "\nSections not passing: " + ", ".join(s["title"] for s in todo)
                   + ". Fix by override, or re-write one with write_screens.py --pages ... "
                     "--call (a direct call); re-running the runner runs the rest again.")
    run(L, [str(HERE / "build_lesson_boards.py"), str(L)], "title and contents boards")
    run(L, [str(HERE / "build_lesson_preview.py"), str(L)], "screens preview")
    agent_approves(L, "screens", "every section's screens audit passes (no fail findings); "
                   "the boards are reviewed with the narration in the silent preview",
                   "fix a board by override in the section's overrides.json and re-render with "
                   "write_screens.py --render, or re-write the section with write_screens.py "
                   "--pages ... --call")


def stage_narration(L, a):
    info, secs = sections(L)
    todo = [s for s in secs if not audit_ok(paths.narration_dir_for(L, s["pages"]) / "narration.json")]
    batch(L, "narration", len(todo), EST["narration"], a)
    qa = [s for s in secs
          if not (paths.narration_dir_for(L, s["pages"]) / "qa" / "qa_pass1.json").exists()]
    batch(L, "qa1", len(qa), EST["qa"], a)
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
    fp = L / "analysis" / "terms_failures.json"
    if failures:
        # ADR 005: the lexicon gate is folded into the final gate. These terms
        # are synthesised with the voice's default (--accept-terms, below) and
        # judged by the maintainer's ear there.
        new = not fp.exists() or json.loads(fp.read_text(encoding="utf-8")) != failures
        fp.write_text(json.dumps(failures, ensure_ascii=False, indent=1), encoding="utf-8")
        if new:
            log_decision(L, "terms not heard as written go to the final gate",
                         "the ear did not hear these as written: "
                         + "; ".join(f"{k}: {', '.join(v)}" for k, v in failures.items())
                         + ". They are synthesised with the voice's default and listed for the "
                           "maintainer's ear at the final gate",
                         "ADR 005 (pronunciation is the maintainer's ear, at the final gate); "
                         "methodology §20",
                         "add an entry to spike/lexicon.json, have the maintainer approve it, and "
                         "re-run: the cache re-makes only the clips that contain the term")
    elif fp.exists():
        fp.unlink()


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
                cmd.append("--accept-terms")     # judged by ear at the final gate (ADR 005)
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
    # The last step of every build (ADR 006): the course index, rebuilt whole,
    # outside the repository (docs/05-COURSE-INDEX.md). Again on every run, so
    # it also records the final gate once approved.
    print(run(L, [str(HERE / "build_course_index.py"), str(L)], "course index").strip())
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
    ap.add_argument("--batch", action="store_true",
                    help="batch mode at half price, only for an unattended run the maintainer "
                         "asked for (up to 24 hours per stage); default: direct calls")
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
