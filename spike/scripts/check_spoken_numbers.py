"""Check every question number the voice actually says (owner, 2026-10-16;
ADR 035 amendment): each narration clip of a built lesson is transcribed with
Scribe, and the question numbers heard are checked against the script and the
board on screen at that moment.

    .venv/Scripts/python spike/scripts/check_spoken_numbers.py <lesson_dir> [--dir <player folder>] [--out FILE]

For every narration utterance of the player's bundle (the recordings are the
release's, never checked here):
  - the question numbers heard ("question seven", "questions one to six", "the
    last question, number six", digits too) are the ones the script says, in
    order: a clip that says another number than its script fails;
  - each number heard passes the question-number rule on its board
    (question_numbers.board_findings): a practice number is one the board shows
    (or, on a board that shows none, one the lesson teaches, numbered from 1),
    and the real test's number is said only in a sentence that names the real
    test or the recording, and only the number of the question on that board.

Scribe is given no keyterms and no forced language (as ear.py). Transcripts are
kept in the report by clip file and its sha256, so a run after a re-voice
transcribes only the clips that changed. The cost is read from the response
headers (credits). Paid (ElevenLabs Scribe; AGENTS.md §4, owner 2026-10-16);
run from the main checkout, where .env is.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import question_numbers as qn                            # noqa: E402
from transcribe import ENDPOINT, MODEL, api_key          # noqa: E402

WORKERS = 4


def scribe(path: Path, key: str) -> tuple[dict, int | None]:
    """Scribe's reply for one clip, and its cost in credits (a response header)."""
    with tempfile.TemporaryDirectory() as tmp:
        hdr = Path(tmp) / "headers.txt"
        cmd = ["curl", "-sS", "--fail-with-body", "--max-time", "300", "--retry", "4", "--retry-delay", "5",
               "--config", "-", "-D", str(hdr), "-F", f"model_id={MODEL}", "-F", f"file=@{path}", ENDPOINT]
        r = subprocess.run(cmd, input=f'header = "xi-api-key: {key}"\n', capture_output=True,
                           text=True, encoding="utf-8")
        if r.returncode != 0:
            raise SystemExit(f"curl failed for {path.name}: {r.stdout[:300]} {r.stderr[:300]}")
        cost = None
        for line in hdr.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("character-cost:"):
                try:
                    cost = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
        return json.loads(r.stdout), cost


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mmss(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}"


def check(bundle: dict, heard: dict[str, str], exam_of: dict[int, int] | None) -> tuple[list[dict], list[dict]]:
    """Every utterance that says a question number (in its script or as heard),
    and the findings: a number heard that is not the script's, and the
    question-number rule run on the heard words."""
    blocks = bundle["blocks"] if isinstance(bundle["blocks"], dict) else {b["id"]: b for b in bundle["blocks"]}
    taught = qn.lesson_numbers(blocks)
    rows, findings = [], []
    for bd in bundle["boards"]:
        ids = list(bd.get("fixed") or []) + list(bd.get("pinned") or {}) \
            + [i for s in bd["states"] for i in s.get("working") or []]
        shown = sorted(qn.shown_numbers(ids, blocks))
        heard_board = {"fixed": bd.get("fixed"), "pinned": bd.get("pinned"), "states": []}
        for s in bd["states"]:
            us = []
            for u in s["utterances"]:
                if u.get("kind") == "exam" or not u.get("text"):
                    continue
                said = [n for n, _ in qn.spoken_numbers(u["text"])]
                got = heard.get(u["id"])
                if got is None:
                    findings.append({"where": u["id"], "at": mmss(u["start"]), "what": "no transcript"})
                    continue
                got_n = [n for n, _ in qn.spoken_numbers(got)]
                if said or got_n:
                    rows.append({"id": u["id"], "at": mmss(u["start"]), "board": bd["id"], "shown": shown,
                                 "script": u["text"], "heard": got, "said": said, "heard_numbers": got_n})
                if said != got_n:
                    findings.append({"where": u["id"], "at": mmss(u["start"]),
                                     "what": f"the script says {said}, the voice was heard saying {got_n}: {got!r}"})
                us.append({"id": u["id"], "text": got})
            heard_board["states"].append({"working": s.get("working") or [], "utterances": us})
        for f in qn.board_findings(heard_board, blocks, taught, exam_of):
            at = next((r["at"] for r in rows if r["id"] == f["where"]), "")
            findings.append({"where": f["where"], "at": at, "what": "as heard: " + f["what"]})
    return rows, findings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--dir", type=Path, help="the player folder (default generated/lesson-player)")
    ap.add_argument("--out", type=Path, help="the report (default <player folder>/spoken_numbers_check.json)")
    a = ap.parse_args()
    pdir = a.dir or a.lesson_dir / "generated" / "lesson-player"
    out = a.out or pdir / "spoken_numbers_check.json"
    bundle = json.loads((pdir / "bundle.json").read_text(encoding="utf-8"))
    old = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    cache = {c["sha256"]: c for c in (old.get("clips") or {}).values()}
    clips: dict[str, dict] = {}
    todo = []
    for bd in bundle["boards"]:
        for s in bd["states"]:
            for u in s["utterances"]:
                if u.get("kind") == "exam" or not u.get("audio_file"):
                    continue
                f = (pdir / u["audio_file"]).resolve()
                h = sha(f)
                if h in cache:
                    clips[u["id"]] = dict(cache[h], file=str(f))
                else:
                    todo.append((u["id"], f, h))
    key = api_key() if todo else None
    credits = 0

    def run(job):
        uid, f, h = job
        r, cost = scribe(f, key)
        return uid, {"file": str(f), "sha256": h, "heard": r.get("text", ""), "credits": cost}

    with ThreadPoolExecutor(WORKERS) as pool:
        for k, (uid, c) in enumerate(pool.map(run, todo), 1):
            clips[uid] = c
            credits += c["credits"] or 0
            if k % 25 == 0:
                print(f"  transcribed {k} of {len(todo)}", flush=True)
    import lesson_type
    import practice_set
    ps = practice_set.load(a.lesson_dir) if lesson_type.has(a.lesson_dir, "exam_numbers") else None
    import check_question_numbers as cqn
    exam_of = practice_set.exam_numbers(ps, cqn.shown_items(bundle)) if ps else None
    rows, findings = check(bundle, {u: c["heard"] for u, c in clips.items()}, exam_of)
    report = {"model": MODEL, "lesson": a.lesson_dir.name, "clips": clips, "numbers": rows,
              "findings": findings, "transcribed_now": len(todo), "credits_now": credits,
              "exam_of": exam_of}
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        print(f"  {r['at']:>8}  {r['id']:<28} board {r['shown'] or '-'}  said {r['said']}  heard {r['heard_numbers']}")
    for f in findings:
        print(f"  NUMBER {f['at']} {f['where']}: {f['what']}")
    print(f"{len(clips)} clips ({len(todo)} transcribed now, {credits} credits); {len(rows)} utterances say a "
          f"question number; report {out}")
    if findings:
        raise SystemExit(f"spoken-number check failed: {len(findings)} finding(s)")
    print("spoken-number check passed: every question number heard is the script's and its board's")


if __name__ == "__main__":
    main()
