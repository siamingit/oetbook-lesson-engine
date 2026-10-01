"""The lesson's length budget (ADR 023): the lesson's natural length, from its
content, and each section's share of the lesson's length target, given to the
screens and narration prompts before their first drafts.

    .venv/Scripts/python spike/scripts/length_budget.py <lesson_dir>
    .venv/Scripts/python spike/scripts/length_budget.py <lesson_dir> \
        --set pages-09-10 --minutes 9 --reason TEXT [--by NAME]
    .venv/Scripts/python spike/scripts/length_budget.py <lesson_dir> --clear pages-09-10 --reason TEXT

Free: arithmetic on the understanding, no model call. Reads sections.json (the
target, lesson.length_target_min, written by build_sections.py: the natural
length by default, the maintainer's --length-target where set) and every
section's understanding.json. Writes analysis/length_budget.json.

The arithmetic, measured on the 83 finished sections of the first 11 lessons
(2026-10-01, ADR 023):
  - a section's natural speech is 3.8 + 0.37 x its source teaching minutes (the
    sum of its understanding beats' durations); median error 16-17% a section,
    within about 10% a lesson for 8 of the 11; the introduction about 2.0 min;
  - the lesson's length, as the silent preview plays it, is the speech times
    1.10 (grammar) or 1.19 (vocabulary): pauses, gaps, reading holds;
  - speech minutes are words / 147, the rate the fit was measured with;
  - a thought carries about 45 spoken words (grammar), 35 (vocabulary).
A section with no recorded teaching has no beat times (ADR 024): an untaught
deck page, planned by the agent, gets the median of the type's recorded
sections (6.7 min of speech, grammar; 6.0, vocabulary); an authored section
(ADR 018) the fit's floor, 3.8 min (Grammar 7's nine averaged 3.9).
The target's speech is shared out in proportion to the sections' natural
speech, the introduction keeping its own. A vocabulary section gets a cap on
full key-word moments (ADR 019): half its time at about 30 s a moment, a
starting value to calibrate on the next vocabulary lesson.

--set fixes one section's speech minutes (the agent's change, with a reason,
logged in the lesson's decisions.md, ADR 005); the other sections share what
is left. --clear removes it. Both are kept across re-runs.

The budget is guidance. The screens and narration audits WARN when a section
is off it (thoughts more than 40% off, words more than 30% over; ADR 024: about
5% of approved sections each), never fail:
a failing audit makes the runner rewrite the section, which is the spend this
exists to avoid. The narration gate shows every warning beside the lesson's
estimated length against its target.
"""

import datetime
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths                                                    # noqa: E402

FIT_A, FIT_B = 3.8, 0.37            # speech minutes = A + B x source teaching minutes
INTRO_SPEECH_MIN = 2.0              # median of the 11 introductions
WPM = 147                           # words a minute, the conversion the fit used
PLAY_RATIO = {"grammar": 1.10, "vocabulary": 1.19}       # silent preview / speech
WORDS_PER_THOUGHT = {"grammar": 45, "vocabulary": 35}
KEYWORD_SHARE, KEYWORD_SECONDS = 0.5, 30                  # vocabulary: full moments
UNTAUGHT_SPEECH_MIN = {"grammar": 6.7, "vocabulary": 6.0}  # ADR 024: median recorded section
THOUGHTS_OFF, WORDS_OVER = 0.40, 0.30                     # the audits' warning limits (ADR 024)


def kind(L: Path) -> str:
    import vocabulary_rule
    return "vocabulary" if vocabulary_rule.is_vocabulary(L) else "grammar"


def all_sections(L: Path) -> tuple[dict, list[dict]]:
    info = json.loads((L / "analysis" / "sections.json").read_text(encoding="utf-8"))
    intro = paths.intro_section(info)
    return info, ([intro] if intro else []) + list(info["sections"])


def teaching_minutes(L: Path, pages: list[int]) -> float | None:
    """The sum of the section's understanding beats' durations, or None while
    a page has no understanding. An authored section (ADR 018) has none: 0."""
    total = 0.0
    for p in pages:
        if paths.is_added(p):
            continue
        u = paths.understanding_dir(L, p) / "understanding.json"
        if not u.exists():
            return None
        for b in json.loads(u.read_text(encoding="utf-8"))["beats"]:
            if b.get("start") is not None and b.get("end") is not None:
                total += b["end"] - b["start"]
    return total / 60


def natural(L: Path) -> dict:
    """The lesson's natural length: per section, its source teaching minutes and
    natural speech; in total, speech and lesson minutes. Refuses while a
    section has no understanding."""
    info, secs = all_sections(L)
    k = kind(L)
    rows, missing = [], []
    for s in secs:
        if s.get("intro"):
            rows.append({"tag": paths.section_tag(s["pages"]), "title": s["title"],
                         "pages": s["pages"], "intro": True, "teaching_min": None,
                         "natural_speech_min": INTRO_SPEECH_MIN})
            continue
        t = teaching_minutes(L, s["pages"])
        if t is None:
            missing.append(s["pages"])
            continue
        untaught = t == 0 and not all(paths.is_added(p) for p in s["pages"])
        authored = t == 0 and not untaught
        rows.append({"tag": paths.section_tag(s["pages"]), "title": s["title"],
                     "pages": s["pages"], "intro": False, "teaching_min": round(t, 2),
                     "natural_speech_min": (UNTAUGHT_SPEECH_MIN[k] if untaught
                                            else round(FIT_A + FIT_B * t, 2)),
                     **({"untaught": True} if untaught else {}),
                     **({"authored": True} if authored else {})})
    if missing:
        raise SystemExit(f"no natural length yet: pages {missing} have no understanding "
                         "(the length follows the understanding's teaching beats)")
    speech = sum(r["natural_speech_min"] for r in rows)
    return {"kind": k, "sections": rows, "speech_min": round(speech, 1),
            "lesson_min": round(speech * PLAY_RATIO[k], 1)}


def print_natural(nat: dict) -> None:
    print(f"{'section':<14} {'source teaching min':>19} {'natural speech min':>18}  title")
    for r in nat["sections"]:
        t = "-" if r["teaching_min"] is None else f"{r['teaching_min']:.1f}"
        note = ("  [untaught deck page: the type's median recorded section (ADR 024)]"
                if r.get("untaught") else
                "  [authored section: the fit's floor (ADR 024)]" if r.get("authored") else "")
        print(f"{r['tag']:<14} {t:>19} {r['natural_speech_min']:>18.1f}  {r['title']}{note}")
    src = sum(r["teaching_min"] or 0 for r in nat["sections"])
    print(f"natural length: about {nat['lesson_min']:.0f} min of lesson ({nat['speech_min']:.0f} min "
          f"of speech, x{PLAY_RATIO[nat['kind']]} for a {nat['kind']} lesson) from {src:.0f} min "
          "of source teaching")


def budget_path(L: Path) -> Path:
    return L / "analysis" / "length_budget.json"


def build(L: Path) -> dict:
    info, _ = all_sections(L)
    lesson = info["lesson"]
    target = lesson.get("length_target_min")
    if not target:
        raise SystemExit("REFUSED: the lesson has no length target (sections.json "
                         "lesson.length_target_min). Set the natural one with build_sections.py "
                         f"{L} --length-target natural, or a shorter one with --length-target MINUTES")
    nat = natural(L)
    k = nat["kind"]
    old = json.loads(budget_path(L).read_text(encoding="utf-8")) if budget_path(L).exists() else {}
    overrides = old.get("overrides", {})
    tags = {r["tag"] for r in nat["sections"]}
    stale = sorted(set(overrides) - tags)
    if stale:
        raise SystemExit(f"REFUSED: overrides name sections the lesson no longer has: {stale}; "
                         "--clear them")
    speech_target = target / PLAY_RATIO[k]
    fixed = sum(overrides[r["tag"]]["speech_min"] if r["tag"] in overrides else r["natural_speech_min"]
                for r in nat["sections"] if r["intro"] or r["tag"] in overrides)
    shared = [r for r in nat["sections"] if not r["intro"] and r["tag"] not in overrides]
    free = speech_target - fixed
    if shared and free <= 0:
        raise SystemExit(f"REFUSED: the target ({target} min) leaves no time for the sections "
                         "without an override; lower an override or raise the target")
    scale = free / sum(r["natural_speech_min"] for r in shared) if shared else 1.0
    out = []
    for r in nat["sections"]:
        if r["tag"] in overrides:
            m = overrides[r["tag"]]["speech_min"]
        elif r["intro"]:
            m = r["natural_speech_min"]
        else:
            m = r["natural_speech_min"] * scale
        words = round(m * WPM)
        row = dict(r, speech_min=round(m, 2), words=words,
                   override=overrides.get(r["tag"]))
        if not r["intro"]:
            row["thoughts"] = max(1, round(words / WORDS_PER_THOUGHT[k]))
            if k == "vocabulary":
                row["keyword_moments_max"] = max(1, math.floor(m * 60 * KEYWORD_SHARE
                                                               / KEYWORD_SECONDS))
        out.append(row)
    result = {
        "purpose": "Each section's share of the lesson's length target, given to the screens "
                   "and narration prompts before their first drafts; the audits warn when a "
                   "section is off it (ADR 023, spike/scripts/length_budget.py).",
        "made": f"{datetime.datetime.now():%Y-%m-%d %H:%M}",
        "kind": k,
        "target": {"lesson_min": target, "source": lesson.get("length_target_source"),
                   "by": lesson.get("length_target_by"),
                   "speech_min": round(speech_target, 1)},
        "natural": {"lesson_min": nat["lesson_min"], "speech_min": nat["speech_min"]},
        "constants": {"fit": [FIT_A, FIT_B], "intro_speech_min": INTRO_SPEECH_MIN,
                      "untaught_speech_min": UNTAUGHT_SPEECH_MIN[k], "wpm": WPM,
                      "play_ratio": PLAY_RATIO[k], "words_per_thought": WORDS_PER_THOUGHT[k],
                      **({"keyword_share": KEYWORD_SHARE, "keyword_seconds": KEYWORD_SECONDS}
                         if k == "vocabulary" else {})},
        "sections": out,
        "overrides": overrides,
    }
    budget_path(L).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


def print_budget(b: dict) -> None:
    t = b["target"]
    print(f"target {t['lesson_min']} min of lesson ({t['source']}), {t['speech_min']} min of "
          f"speech; natural {b['natural']['lesson_min']} min")
    for r in b["sections"]:
        extra = "" if r["intro"] else f"  thoughts {r['thoughts']:>3}"
        if "keyword_moments_max" in r:
            extra += f"  full key-word moments <= {r['keyword_moments_max']}"
        print(f"  {r['tag']:<14} {r['speech_min']:5.1f} min  {r['words']:5} words{extra}"
              + ("  (override)" if r["override"] else "") + f"  {r['title']}")


# ---------------------------------------------------------------------------
# Used by the stages
# ---------------------------------------------------------------------------

def for_section(L: Path, pages: list[int]) -> dict | None:
    """The section's budget, or None: a lesson built before ADR 023 has none,
    and its requests and audits are unchanged."""
    if not budget_path(L).exists():
        return None
    b = json.loads(budget_path(L).read_text(encoding="utf-8"))
    tag = paths.section_tag(pages)
    row = next((r for r in b["sections"] if r["tag"] == tag), None)
    return dict(row, target=b["target"]) if row else None


def prompt_block(L: Path, pages: list[int], stage: str) -> str | None:
    """The LENGTH BUDGET block for the section's message (after the cached
    system prompt, so the cache is unaffected). QA is never given it."""
    r = for_section(L, pages)
    if r is None:
        return None
    t = r["target"]
    parts = [f"LENGTH BUDGET for this section: about {r['speech_min']:.1f} minutes of speech, "
             f"about {r['words']} words of narration"]
    if stage == "screens" and not r["intro"]:
        parts.append(f"about {r['thoughts']} thoughts")
    text = ", ".join(parts) + ". "
    if "keyword_moments_max" in r:
        text += (f"Full key-word moments (the vocabulary rule) for at most "
                 f"{r['keyword_moments_max']} words: the words this slide itself teaches first; "
                 "a short gloss alone for the rest. ")
    text += (f"This is the section's share of the lesson's length, {t['lesson_min']:g} minutes "
             f"({'its natural length, from its content' if t['source'] == 'natural' else 'set by the maintainer'}).")
    return text


def findings(L: Path, pages: list[int], thoughts: int | None = None,
             words: int | None = None) -> list[dict]:
    """Warnings, never failures, for a section off its budget."""
    r = for_section(L, pages)
    if r is None:
        return []
    out = []
    if thoughts is not None and not r["intro"] and r.get("thoughts"):
        if abs(thoughts - r["thoughts"]) > THOUGHTS_OFF * r["thoughts"]:
            out.append({"severity": "warn", "where": "length",
                        "what": f"{thoughts} thoughts against a budget of about {r['thoughts']} "
                                f"(more than {THOUGHTS_OFF:.0%} off; ADR 023, 024)"})
    if words is not None and words > (1 + WORDS_OVER) * r["words"]:
        out.append({"severity": "warn", "where": "length",
                    "what": f"{words} spoken words against a budget of about {r['words']} "
                            f"(more than {WORDS_OVER:.0%} over; ADR 023, 024)"})
    return out


def gate_summary(L: Path) -> str:
    """For the narration gate: the lesson's estimated length (the silent
    preview) against its target, and every length warning of every section."""
    if not budget_path(L).exists():
        return ""
    b = json.loads(budget_path(L).read_text(encoding="utf-8"))
    t = b["target"]
    tl = L / "generated" / "lesson-preview" / "silent" / "timeline.json"
    est = (json.loads(tl.read_text(encoding="utf-8"))["meta"]["total_duration_s"] / 60
           if tl.exists() else None)
    sec = round(est * 60) if est is not None else 0
    head = (f"LENGTH: the silent preview plays {sec // 60}:{sec % 60:02d}"
            if est is not None else "LENGTH: no silent preview yet")
    lines = [head + f" against a target of {t['lesson_min']:g} min ({t['source']}"
             + (f", {(est - t['lesson_min']) / t['lesson_min']:+.0%}" if est is not None else "")
             + ")"]
    _, secs = all_sections(L)
    for s in secs:
        for stage, f in (("screens", paths.screens_dir_for(L, s["pages"]) / "screens.json"),
                         ("narration", paths.narration_dir_for(L, s["pages"]) / "narration.json")):
            if not f.exists():
                continue
            for x in json.loads(f.read_text(encoding="utf-8")).get("audit", []):
                if x.get("where") == "length":
                    lines.append(f"  WARN {s['title']} ({stage}): {x['what']}")
    if len(lines) == 1:
        lines.append("  every section within its budget")
    return "\n".join(lines)


def main() -> None:
    L = Path(sys.argv[1])
    arg = lambda n: sys.argv[sys.argv.index(n) + 1] if n in sys.argv else None
    if "--set" in sys.argv or "--clear" in sys.argv:
        tag = arg("--set") or arg("--clear")
        reason = arg("--reason")
        if not reason:
            raise SystemExit("--set and --clear need --reason (logged in decisions.md, ADR 005)")
        b = json.loads(budget_path(L).read_text(encoding="utf-8")) if budget_path(L).exists() else {}
        ov = b.get("overrides", {})
        if tag not in {paths.section_tag(s["pages"]) for s in all_sections(L)[1]}:
            raise SystemExit(f"no section {tag!r} in this lesson")
        from build_lesson import log_decision
        if "--set" in sys.argv:
            m = float(arg("--minutes"))
            ov[tag] = {"speech_min": m, "reason": reason, "by": arg("--by") or "agent",
                       "on": f"{datetime.datetime.now():%Y-%m-%d %H:%M}"}
            log_decision(L, f"Length budget: {tag} set to {m:g} min of speech", reason,
                         "ADR 023: the agent may change a section's budget with a reason",
                         f"length_budget.py {L} --clear {tag} --reason TEXT")
        else:
            ov.pop(tag, None)
            log_decision(L, f"Length budget: override of {tag} removed", reason,
                         "ADR 023", f"length_budget.py {L} --set {tag} --minutes M --reason TEXT")
        b["overrides"] = ov
        budget_path(L).write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    print_budget(build(L))
    print(f"wrote {budget_path(L)}")


if __name__ == "__main__":
    main()
