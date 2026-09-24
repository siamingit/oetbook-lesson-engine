"""Model calls shared by the stages: prices, cost arithmetic, prompt caching,
and the batch submit-wait-collect loop for Anthropic and Gemini.

Prices were looked up on 2026-09-24 and are recorded in docs/03-RUNBOOK.md
("Cost controls") with their sources:

  Claude Opus 5 (platform.claude.com/docs/en/about-claude/pricing)
    input $5, output $25, 5-minute cache write $6.25, 1-hour cache write $10,
    cache read $0.50 per million tokens. Message Batches: 50% on input and
    output; caching multipliers stack with the batch discount.
  Gemini 3.1 Pro Preview (ai.google.dev/gemini-api/docs/pricing, "last updated
    2026-09-24"), prompts up to 200k: input $2, output $12 (thinking billed as
    output), cached input $0.20 per million. Batch: input $1, output $6.

A batch saves half of everything. Caching saves 90% of the stable prefix's
input price on a hit, and costs 1.25x (5 minutes) or 2x (1 hour) on a write;
Anthropic applies cache hits inside a batch on a best-effort basis, and
recommends the 1-hour cache there.
"""

import json
import time
from pathlib import Path

# $ per million tokens
OPUS = {"input": 5.00, "output": 25.00, "write_5m": 6.25, "write_1h": 10.00, "read": 0.50}
GEMINI_PRO = {"input": 2.00, "output": 12.00, "cached": 0.20}
BATCH_DISCOUNT = 0.5          # Anthropic and Gemini batch modes, input and output


def system_blocks(text: str, ttl: str = "5m") -> list[dict]:
    """The stage's stable system prompt as one cached block. It is the same
    for every section of a stage, so every call after the first reads it at
    0.1x (Opus 5 caches prefixes of 512 tokens or more). Batches use the
    1-hour TTL, direct calls the 5-minute one."""
    cc = {"type": "ephemeral"} if ttl == "5m" else {"type": "ephemeral", "ttl": "1h"}
    return [{"type": "text", "text": text, "cache_control": cc}]


def anthropic_cost(usage: dict, batch: bool = False) -> float:
    """Dollars for one Anthropic response's usage, counting cache writes by
    TTL and cache reads, halved for a batch."""
    u = usage or {}
    cc = u.get("cache_creation") or {}
    w1h = cc.get("ephemeral_1h_input_tokens", 0) or 0
    w5m = cc.get("ephemeral_5m_input_tokens")
    if w5m is None:
        w5m = (u.get("cache_creation_input_tokens", 0) or 0) - w1h
    d = (u.get("input_tokens", 0) * OPUS["input"] + u.get("output_tokens", 0) * OPUS["output"]
         + w5m * OPUS["write_5m"] + w1h * OPUS["write_1h"]
         + (u.get("cache_read_input_tokens", 0) or 0) * OPUS["read"]) / 1e6
    return d * (BATCH_DISCOUNT if batch else 1.0)


def raw_cost(raw: dict) -> float:
    """Cost of a saved Anthropic response (raw_response*.json): its usage, at
    the batch price when the file records that it came from a batch."""
    return anthropic_cost(raw.get("usage") or {}, (raw.get("_billing") or {}).get("mode") == "batch")


def cache_saving(usage: dict, batch: bool = False) -> float:
    """What the cache saved on this response against sending the same tokens
    uncached (negative when a write cost more than it saved)."""
    u = usage or {}
    cc = u.get("cache_creation") or {}
    w1h = cc.get("ephemeral_1h_input_tokens", 0) or 0
    w5m = (u.get("cache_creation_input_tokens", 0) or 0) - w1h
    read = u.get("cache_read_input_tokens", 0) or 0
    d = (read * (OPUS["input"] - OPUS["read"]) - w5m * (OPUS["write_5m"] - OPUS["input"])
         - w1h * (OPUS["write_1h"] - OPUS["input"])) / 1e6
    return d * (BATCH_DISCOUNT if batch else 1.0)


def gemini_cost(input_tokens: int, output_tokens: int, cached_tokens: int = 0,
                batch: bool = False) -> float:
    """Dollars for one Gemini 3.1 Pro response. `output_tokens` includes
    thinking. Cached input is billed at the cached rate, the rest at input."""
    f = BATCH_DISCOUNT if batch else 1.0
    return ((input_tokens - cached_tokens) * GEMINI_PRO["input"] * f
            + cached_tokens * GEMINI_PRO["cached"]
            + output_tokens * GEMINI_PRO["output"] * f) / 1e6


# ---------------------------------------------------------------------------
# Anthropic Message Batches
# ---------------------------------------------------------------------------

def run_anthropic_batch(client, jobs: list[dict], state_path: Path, poll_s: int = 60,
                        log=print) -> dict:
    """Submit one Message Batch for `jobs` ({custom_id, params, out}), wait
    for it, and write each succeeded message to its `out` path in the shape a
    direct call writes (Message.to_json()), plus `_billing` so costs are
    counted at the batch price. Returns {custom_id: "ok" | reason}.

    Resumable: the batch id is written to `state_path` right after
    submission; a run that finds an unfinished state file waits for that batch
    instead of submitting again, so a killed run never pays twice."""
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    if state and state.get("collected"):
        state = None
    if state is None:
        from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
        from anthropic.types.messages.batch_create_params import Request
        reqs = [Request(custom_id=j["custom_id"], params=MessageCreateParamsNonStreaming(**j["params"]))
                for j in jobs]
        batch = client.messages.batches.create(requests=reqs)
        state = {"provider": "anthropic", "batch_id": batch.id, "submitted": time.time(),
                 "jobs": {j["custom_id"]: str(j["out"]) for j in jobs}, "collected": False}
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
        log(f"batch {batch.id} submitted: {len(jobs)} requests")
    else:
        log(f"batch {state['batch_id']} already submitted; waiting for it")
    bid = state["batch_id"]
    while True:
        b = client.messages.batches.retrieve(bid)
        if b.processing_status == "ended":
            break
        rc = b.request_counts
        log(f"  {b.processing_status}: {rc.processing} processing, {rc.succeeded} done "
            f"({(time.time() - state['submitted']) / 60:.0f} min)")
        time.sleep(poll_s)
    outcome = {}
    for r in client.messages.batches.results(bid):
        out = Path(state["jobs"][r.custom_id])
        if r.result.type == "succeeded":
            msg = r.result.message
            if msg.stop_reason == "max_tokens":
                outcome[r.custom_id] = "cut off at the output cap; nothing written"
                continue
            d = json.loads(msg.to_json())
            d["_billing"] = {"mode": "batch", "batch_id": bid}
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            outcome[r.custom_id] = "ok"
        elif r.result.type == "errored":
            outcome[r.custom_id] = f"errored: {r.result.error}"
        else:
            outcome[r.custom_id] = r.result.type             # canceled / expired (not billed)
    state["collected"] = True
    state["outcome"] = outcome
    state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
    return outcome


# ---------------------------------------------------------------------------
# Gemini batch mode (inline requests, under 20 MB)
# ---------------------------------------------------------------------------

GEMINI_DONE = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}


def run_gemini_batch(client, model: str, jobs: list[dict], state_path: Path, poll_s: int = 60,
                     log=print) -> dict:
    """Submit one Gemini batch job of inline requests ({custom_id, request,
    out}), wait, and write each response to `out` as JSON: the response text,
    its usage metadata and `_billing`. Inline responses come back in request
    order; the order is kept in the state file. Resumable like the Anthropic
    batch."""
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    if state and state.get("collected"):
        state = None
    if state is None:
        job = client.batches.create(model=model, src=[j["request"] for j in jobs],
                                    config={"display_name": state_path.stem})
        state = {"provider": "gemini", "job_name": job.name, "submitted": time.time(),
                 "order": [j["custom_id"] for j in jobs],
                 "jobs": {j["custom_id"]: str(j["out"]) for j in jobs}, "collected": False}
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
        log(f"gemini batch {job.name} submitted: {len(jobs)} requests")
    else:
        log(f"gemini batch {state['job_name']} already submitted; waiting for it")
    while True:
        job = client.batches.get(name=state["job_name"])
        st = job.state.name if hasattr(job.state, "name") else str(job.state)
        if st in GEMINI_DONE:
            break
        log(f"  {st} ({(time.time() - state['submitted']) / 60:.0f} min)")
        time.sleep(poll_s)
    outcome = {}
    if st != "JOB_STATE_SUCCEEDED":
        for cid in state["order"]:
            outcome[cid] = st
    else:
        for cid, ir in zip(state["order"], job.dest.inlined_responses):
            if getattr(ir, "error", None) or not ir.response:
                outcome[cid] = f"errored: {getattr(ir, 'error', None)}"
                continue
            um = ir.response.usage_metadata
            rec = {"text": ir.response.text,
                   "usage": {"prompt_tokens": um.prompt_token_count or 0,
                             "output_tokens": (um.candidates_token_count or 0),
                             "thought_tokens": (um.thoughts_token_count or 0),
                             "cached_tokens": (um.cached_content_token_count or 0)},
                   "_billing": {"mode": "batch", "job": state["job_name"]}}
            out = Path(state["jobs"][cid])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            outcome[cid] = "ok"
    state["collected"] = True
    state["outcome"] = outcome
    state_path.write_text(json.dumps(state, indent=1), encoding="utf-8")
    return outcome
