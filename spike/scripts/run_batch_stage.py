"""Run one model stage for every pending unit of a lesson as ONE batch, wait,
and render each result exactly as a direct call would (docs/03-RUNBOOK.md,
"Cost controls").

    .venv/Scripts/python spike/scripts/run_batch_stage.py <lesson_dir> --stage STAGE [--dry-run]
    STAGE: understanding | screens | narration | qa1 | qa2

  understanding  every page the lesson needs (the contents slide and every
                 section's pages) without an understanding.json
  screens        every section whose screens.json is missing or fails its audit
  narration      the introduction and every section whose narration is missing
                 or fails its audit
  qa1, qa2       a whole-section QA pass (Gemini batch mode) for every narrated
                 section that has not had it

Anthropic stages go through the Message Batches API, QA through Gemini batch
mode: both at half price (prices and sources in llm.py). Each request is built
by the stage's own request_params() or gemini_request(), so a batch request
and a direct call are the same request; the stable system prompt is cached
with the 1-hour TTL, as Anthropic recommends for batches.

--dry-run builds every request, checks its shape locally (the Gemini request
through the SDK's own types), and prints the count, the size and an estimated
cost. No API call.

Resumable: the batch id is saved in <lesson>/analysis/batches/<stage>.json the
moment it is submitted; a later run waits for that batch instead of paying for
another. Single-section rewrites at a gate stay direct calls
(write_narration.py --states, write_screens.py --pages ... --call,
qa_narration.py --states), where waiting for a batch would slow the maintainer.
"""

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm                                                       # noqa: E402
import paths                                                     # noqa: E402

# Grammar 1's measured output per unit, for the dry-run estimate (tokens).
TYPICAL_OUT = {"understanding": 9000, "screens": 18000, "narration": 17000, "qa": 10000}


def tag(pages: list[int]) -> str:
    return paths.section_tag(pages)


def sections(L: Path) -> tuple[dict, list[dict]]:
    info = json.loads((L / "analysis" / "sections.json").read_text(encoding="utf-8"))
    cp = info.get("contents_page")
    intro = [{"title": "Introduction", "pages": [cp], "intro": True}] if cp else []
    return info, intro + list(info["sections"])


def audit_ok(p: Path) -> bool:
    return p.exists() and not any(f["severity"] == "fail"
                                  for f in json.loads(p.read_text(encoding="utf-8"))["audit"])


def jobs_for(L: Path, stage: str, include_done: bool = False) -> list[dict]:
    """The pending units of a stage: custom_id, the request, where the reply
    goes, and how to render it afterwards."""
    info, secs = sections(L)
    jobs = []
    if stage == "understanding":
        import extract_understanding as eu
        pages = sorted({p for s in secs for p in s["pages"]})
        for p in pages:
            if (paths.understanding_dir(L, p) / "understanding.json").exists() and not include_done:
                continue
            data = eu.gather(L, p)
            jobs.append({"custom_id": f"page-{p}", "provider": "anthropic",
                         "params": eu.request_params(eu.build_messages(data), "1h"),
                         "out": paths.understanding_dir(L, p) / "raw_response.json",
                         "render": (lambda p=p: eu.render(L, p))})
    elif stage == "screens":
        import write_screens as ws
        for s in secs:
            if s.get("intro"):
                continue               # the opening boards are built by code
            d = paths.screens_dir_for(L, s["pages"])
            if audit_ok(d / "screens.json") and not include_done:
                continue
            data = ws.gather(L, s["pages"])
            jobs.append({"custom_id": tag(s["pages"]), "provider": "anthropic",
                         "params": ws.request_params(ws.build_messages(data), "1h"),
                         "out": d / "raw_response.json",
                         "render": (lambda s=s, data=data: ws.render(L, s["pages"][0], data))})
    elif stage == "narration":
        import write_narration as wn
        for s in secs:
            d = paths.narration_dir_for(L, s["pages"])
            if audit_ok(d / "narration.json") and not include_done:
                continue
            if not audit_ok(paths.screens_dir_for(L, s["pages"]) / "screens.json"):
                raise SystemExit(f"REFUSED: {s['title']!r} has no passing screens; narration "
                                 "is never written on failing screens")
            data = wn.gather(L, s["pages"])
            jobs.append({"custom_id": tag(s["pages"]), "provider": "anthropic",
                         "params": wn.request_params(wn.build_messages(data), "1h"),
                         "out": d / "raw_response.json",
                         "render": (lambda s=s, data=data: wn.render(L, s["pages"][0], data))})
    elif stage in ("qa1", "qa2"):
        import qa_narration as qn
        n = int(stage[-1])
        for s in secs:
            d = paths.narration_dir_for(L, s["pages"])
            if not audit_ok(d / "narration.json") or ((d / "qa" / f"qa_pass{n}.json").exists()
                                                      and not include_done):
                continue
            prep = qn.prepare(L, s["pages"], n)
            out = prep["out"] / f"batch_pass{n}.json"
            jobs.append({"custom_id": tag(s["pages"]), "provider": "gemini",
                         "request": qn.gemini_request(prep["text"]), "out": out,
                         "render": (lambda prep=prep, out=out: finish_qa(qn, prep, out))})
    else:
        raise SystemExit(f"unknown stage {stage!r}")
    return jobs


def finish_qa(qn, prep: dict, out: Path) -> int:
    rec = json.loads(out.read_text(encoding="utf-8"))
    u = rec["usage"]
    qn.finish(prep, rec["text"], {"input": u["prompt_tokens"], "output": u["output_tokens"],
                                  "thought": u["thought_tokens"], "cached": u["cached_tokens"]},
              True, json.dumps(rec, ensure_ascii=False, indent=1))
    return 0


def dry_run(stage: str, jobs: list[dict]) -> None:
    """Build and check every request; no API call."""
    size = 0
    est = 0.0
    for j in jobs:
        if j["provider"] == "gemini":
            from google.genai import types
            types.InlinedRequest.model_validate(j["request"])       # local shape check
            body = json.dumps(j["request"])
            tokens_in = len(body) / 3.6
            est += llm.gemini_cost(int(tokens_in), TYPICAL_OUT["qa"], 0, batch=True)
        else:
            body = json.dumps(j["params"], default=str)
            # text at ~3.6 characters a token; an image is billed by its
            # pixels, not its base64 length (about 1,600 tokens at this size)
            chars = sum(len(b["text"]) for b in j["params"]["system"])
            images = 0
            for m in j["params"]["messages"]:
                for c in (m["content"] if isinstance(m["content"], list) else [{"text": m["content"]}]):
                    if c.get("type") == "image":
                        images += 1
                    else:
                        chars += len(c.get("text") or "")
            tokens_in = chars / 3.6 + images * 1600
            est += llm.anthropic_cost({"input_tokens": int(tokens_in),
                                       "output_tokens": TYPICAL_OUT[stage]}, batch=True)
            assert j["params"]["system"][0].get("cache_control"), "system prompt not cached"
            assert "stream" not in j["params"], "a batch request cannot stream"
        size += len(body)
        print(f"  {j['custom_id']:<14} {len(body) / 1024:7.0f} KB  ~{tokens_in:7.0f} input tokens")
    print(f"{len(jobs)} requests, {size / 1e6:.2f} MB; estimated ${est:.2f} at batch prices "
          f"(output estimated from Grammar 1; uncached input). No API call made.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="with --dry-run: build requests for finished units too (a free test)")
    ap.add_argument("--poll", type=int, default=60)
    a = ap.parse_args()
    L = a.lesson_dir
    state_path = L / "analysis" / "batches" / f"{a.stage}.json"

    resuming = state_path.exists() and not json.loads(state_path.read_text(encoding="utf-8")).get("collected")
    jobs = jobs_for(L, a.stage, include_done=a.all and a.dry_run)
    if not jobs and not resuming:
        print(f"{a.stage}: nothing pending")
        return
    print(f"{a.stage}: {len(jobs)} pending")
    if a.dry_run:
        dry_run(a.stage.rstrip("12") if a.stage.startswith("qa") else a.stage, jobs)
        return

    t0 = time.time()
    if jobs and jobs[0]["provider"] == "gemini":
        from google import genai
        import qa_narration as qn
        client = genai.Client(api_key=qn.api_key())
        outcome = llm.run_gemini_batch(client, qn.MODEL, jobs, state_path, a.poll)
    else:
        import anthropic
        from extract_understanding import api_key
        client = anthropic.Anthropic(api_key=api_key())
        outcome = llm.run_anthropic_batch(client, jobs, state_path, a.poll)
    print(f"batch ended after {(time.time() - t0) / 60:.1f} min")

    failed = []
    for j in jobs:
        res = outcome.get(j["custom_id"], "not in the batch results")
        if res != "ok":
            failed.append(f"{j['custom_id']}: {res}")
            continue
        try:
            rc = j["render"]()
        except SystemExit as e:
            rc = e.code
        if rc:
            failed.append(f"{j['custom_id']}: audit failed after rendering (see its preview)")

    # the batch's cost and the cache's effect, from the saved replies
    cost = saving = 0.0
    cache_read = cache_write = 0
    for j in jobs:
        if not j["out"].exists():
            continue
        rec = json.loads(j["out"].read_text(encoding="utf-8"))
        if j["provider"] == "anthropic":
            u = rec.get("usage") or {}
            cost += llm.raw_cost(rec)
            saving += llm.cache_saving(u, batch=True)
            cache_read += u.get("cache_read_input_tokens", 0) or 0
            cache_write += u.get("cache_creation_input_tokens", 0) or 0
        else:
            u = rec["usage"]
            cost += llm.gemini_cost(u["prompt_tokens"], u["output_tokens"] + u["thought_tokens"],
                                    u["cached_tokens"], batch=True)
            cache_read += u["cached_tokens"]
    print(f"cost ${cost:.2f} at batch prices | cache: {cache_write:,} tokens written, "
          f"{cache_read:,} read, net saving ${saving:.3f}")
    done = state_path.with_name(f"{a.stage}-{datetime.datetime.now():%Y%m%d-%H%M}.json")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state.update(cost_usd=round(cost, 4), cache_read_tokens=cache_read,
                 cache_write_tokens=cache_write, cache_saving_usd=round(saving, 4), failed=failed)
    done.write_text(json.dumps(state, indent=1), encoding="utf-8")
    state_path.unlink()
    for f in failed:
        print("FAILED " + f)
    if failed:
        raise SystemExit(f"{len(failed)} unit(s) did not pass; see above")


if __name__ == "__main__":
    main()
