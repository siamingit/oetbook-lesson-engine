"""Run one model stage for every pending unit of a lesson, and render each
result exactly as a single-unit call would (docs/03-RUNBOOK.md, "Cost
controls"). With --direct (the runner's default since 2026-09-24): direct calls
with the 5-minute prompt cache, four at a time, the first alone until its reply
starts so that the rest read the cache it wrote. Without it: ONE batch at half
price, for an unattended run the maintainer asked for.

    .venv/Scripts/python spike/scripts/run_batch_stage.py <lesson_dir> --stage STAGE [--direct] [--dry-run]
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
    intro = paths.intro_section(info)
    return info, ([intro] if intro else []) + list(info["sections"])


def audit_ok(p: Path) -> bool:
    return p.exists() and not any(f["severity"] == "fail"
                                  for f in json.loads(p.read_text(encoding="utf-8"))["audit"])


def jobs_for(L: Path, stage: str, include_done: bool = False, ttl: str = "1h") -> list[dict]:
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
                         "params": eu.request_params(eu.build_messages(data), ttl),
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
                         "params": ws.request_params(ws.build_messages(data), ttl),
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
                         "params": wn.request_params(wn.build_messages(data), ttl),
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
                         "request": qn.gemini_request(prep["text"]), "out": out, "prep": prep,
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


DIRECT_WORKERS = 4        # direct calls in flight at once


def run_direct(L: Path, stage: str, jobs: list[dict]) -> None:
    """Every pending unit as a direct call, a few at a time, at full price with
    the 5-minute prompt cache: the default (docs/03-RUNBOOK.md, "Cost
    controls"). Each reply is written where a batch would write it, then
    rendered, one at a time, exactly as after a batch."""
    import threading
    from concurrent.futures import ThreadPoolExecutor
    t0 = time.time()

    def call(j: dict, started: "threading.Event | None" = None) -> str:
        try:
            if j["provider"] == "gemini":
                import qa_narration as qn
                qn.call_direct(j["prep"])
                return "ok"
            import anthropic
            from extract_understanding import api_key
            client = anthropic.Anthropic(api_key=api_key(), max_retries=5)
            with client.messages.stream(**j["params"]) as st:
                for _ in st:
                    # the first event means the prompt, and so the cache, is written
                    if started is not None and not started.is_set():
                        started.set()
                msg = st.get_final_message()
            if msg.stop_reason == "max_tokens":
                return "cut off at the output cap; nothing written"
            j["out"].parent.mkdir(parents=True, exist_ok=True)
            if j["out"].exists():
                # A reply being replaced was paid for: kept under a name the
                # runner's spend check (raw_response*.json) still counts.
                j["out"].rename(j["out"].with_name(
                    f"raw_response.superseded-{datetime.datetime.now():%Y%m%d-%H%M%S}.json"))
            j["out"].write_text(msg.to_json(), encoding="utf-8")
            return "ok"
        except SystemExit as e:
            return f"refused: {e}"
        except Exception as e:                          # noqa: BLE001 - reported per unit
            return f"error: {type(e).__name__}: {e}"
        finally:
            if started is not None:
                started.set()

    print(f"{stage}: {len(jobs)} direct calls, {DIRECT_WORKERS} at a time", flush=True)
    with ThreadPoolExecutor(DIRECT_WORKERS) as ex:
        first = None
        rest = jobs
        if len(jobs) > 1 and jobs[0]["provider"] == "anthropic":
            # Warm the prompt cache: calls that start together each write the
            # cached system prompt before any can read it (Grammar 2: every
            # stage wrote the cache and read almost nothing). The first call
            # goes alone until its reply starts streaming, when its prompt,
            # and so the cache, has been processed; the rest then read it.
            # Waiting for the whole first reply could outlast the 5-minute cache.
            started = threading.Event()
            first = ex.submit(call, jobs[0], started)
            started.wait()
            print(f"  cache warmed by {jobs[0]['custom_id']}; "
                  f"{len(jobs) - 1} more calls start now", flush=True)
            rest = jobs[1:]
        futures = [ex.submit(call, j) for j in rest]
        outcome = {}
        if first is not None:
            outcome[jobs[0]["custom_id"]] = first.result()
        outcome.update({j["custom_id"]: f.result() for j, f in zip(rest, futures)})
    print(f"calls ended after {(time.time() - t0) / 60:.1f} min", flush=True)

    failed = []
    for j in jobs:
        res = outcome[j["custom_id"]]
        if res != "ok":
            failed.append(f"{j['custom_id']}: {res}")
            continue
        if j["provider"] == "gemini":
            continue                                   # call_direct wrote and rendered it
        try:
            rc = j["render"]()
        except SystemExit as e:
            rc = e.code
        if rc:
            failed.append(f"{j['custom_id']}: audit failed after rendering (see its preview)")

    cost = saving = 0.0
    cache_read = cache_write = 0
    for j in jobs:
        if outcome[j["custom_id"]] != "ok":
            continue
        if j["provider"] == "anthropic":
            rec = json.loads(j["out"].read_text(encoding="utf-8"))
            u = rec.get("usage") or {}
            cost += llm.raw_cost(rec)
            saving += llm.cache_saving(u)
            cache_read += u.get("cache_read_input_tokens", 0) or 0
            cache_write += u.get("cache_creation_input_tokens", 0) or 0
        else:
            n = int(stage[-1])
            qa = json.loads((j["prep"]["out"] / f"qa_pass{n}.json").read_text(encoding="utf-8"))
            cost += qa.get("meta", {}).get("cost_usd", 0)
    print(f"cost ${cost:.2f} at full price | cache: {cache_write:,} tokens written, "
          f"{cache_read:,} read, net saving ${saving:.3f}")
    rec_path = L / "analysis" / "batches" / f"{stage}-direct-{datetime.datetime.now():%Y%m%d-%H%M}.json"
    rec_path.parent.mkdir(parents=True, exist_ok=True)
    rec_path.write_text(json.dumps({"mode": "direct", "outcome": outcome, "cost_usd": round(cost, 4),
                                    "cache_read_tokens": cache_read,
                                    "cache_write_tokens": cache_write,
                                    "cache_saving_usd": round(saving, 4), "failed": failed},
                                   indent=1), encoding="utf-8")
    for f in failed:
        print("FAILED " + f)
    if failed:
        raise SystemExit(f"{len(failed)} unit(s) did not pass; see above")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson_dir", type=Path)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="with --dry-run: build requests for finished units too (a free test)")
    ap.add_argument("--poll", type=int, default=60)
    ap.add_argument("--direct", action="store_true",
                    help="direct calls with the 5-minute cache instead of one batch")
    a = ap.parse_args()
    L = a.lesson_dir
    state_path = L / "analysis" / "batches" / f"{a.stage}.json"

    resuming = state_path.exists() and not json.loads(state_path.read_text(encoding="utf-8")).get("collected")
    ttl = "5m" if a.direct and not resuming else "1h"
    jobs = jobs_for(L, a.stage, include_done=a.all and a.dry_run, ttl=ttl)
    if not jobs and not resuming:
        print(f"{a.stage}: nothing pending")
        return
    print(f"{a.stage}: {len(jobs)} pending")
    if a.dry_run:
        dry_run(a.stage.rstrip("12") if a.stage.startswith("qa") else a.stage, jobs)
        return
    if a.direct and not resuming:
        run_direct(L, a.stage, jobs)
        return
    if a.direct:
        # A batch already submitted is collected first (it may have finished,
        # or be cancelled): a reply it produced is paid for and is never asked
        # for twice. What it did not produce then goes as direct calls.
        print(f"{a.stage}: collecting the batch already submitted before any direct call")

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
    if a.direct:
        rest = jobs_for(L, a.stage, ttl="5m")
        if rest:
            run_direct(L, a.stage, rest)
            return
    for f in failed:
        print("FAILED " + f)
    if failed:
        raise SystemExit(f"{len(failed)} unit(s) did not pass; see above")


if __name__ == "__main__":
    main()
