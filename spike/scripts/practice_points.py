"""Practice points (bundle format 1.23, ADR 046): the learner answers in the middle of a lesson.

A practice point is a moment of the lesson's clock where a player that knows them stops the
lesson, dims the board and opens a pop-up over it: the task, the piece of the paper the learner
writes from (the paper excerpt of ADR 045) and one to three items in the site's own item contract
(oetacademy-web ADR-0031 §3, the non-exam profile; ADR-0032). The learner answers; the answer is
checked in the pop-up (the right answer and a short reason, written); Continue closes it and the
lesson resumes from the same point.

Where they come from. A lesson that has practice points has `analysis/practice.json`
(`{"format": "oetbook-practice-points", "version": 1, "points": {KEY: POINT}}`). The narration
marks each point with a pause whose text is "practice: KEY" (the pause of the fallback below).
`attach` finds every such pause in the built boards and gives its state a `practice` entry and
the cue a `practice` field naming it. A lesson without the file is built exactly as before.

The fallback (rule 57). The pause is part of the ordinary timeline: the task is voiced before it,
the board shows the task while it lasts (3 to 10 seconds), and the next utterance shows the answer
(a reveal or a typing cue) and takes it up in words, the same for every learner. A player that
does not know practice points plays exactly that. `attach` refuses a point whose pause or answer
is not there.

The audio never depends on what the learner typed: nothing here changes a clip or a time.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

FORMAT_VERSION = "1.23"            # bundle format of a lesson with practice points (ADR 046)
FILE_FORMAT = "oetbook-practice-points"
PAUSE_PREFIX = "practice: "
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
ITEM_ID_RE = re.compile(r"^oa-(reading|listening|grammar|vocabulary|writing|speaking)-[0-9]{6}$")
# the site's ID blocks (ADR-0031 §2): 990000-999999 are examples and fixtures, never published.
# The engine has no block of its own yet (asked of the site, ADR 046); until it has one, only
# fixture IDs are written, so nothing here can reach a learner by mistake.
FIXTURE_LOW = 990000
PAUSE_MIN, PAUSE_MAX = 3.0, 10.0   # s: the fallback's pause (every pause is 0.5 to 10, §5)
TYPES = {"choice", "text", "gapfill", "wordbank", "ordering"}   # approved: ADR-0031 §3, ADR-0032
SCHEMES = {"oet-typed-v1", "oet-typed-form-v1"}                 # the second proposed (ADR 046)
ROOT_CAUSES = {"word-match", "mentioned-not-asked", "partial", "overgeneralisation", "reversal",
               "wrong-referent", "world-knowledge", "speaker-confusion", "unaccepted-proposal",
               "sound-alike", "wrong-text", "form-change", "spelling", "too-much", "wrong-form",
               "wrong-rule"}
HASH_EXCLUDE = {"version", "content_hash", "status", "withdrawal", "tags", "admin"}
CHECK_MARKING = ("self",)          # a sentence's self-check list; "ai" is kept for later (ADR 046)


def path(L: Path) -> Path:
    return L / "analysis" / "practice.json"


def load(L: Path) -> dict | None:
    """The lesson's practice points by key, or None for a lesson that has none."""
    p = path(L)
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    if d.get("format") != FILE_FORMAT or d.get("version") != 1:
        raise SystemExit(f"REFUSED: {p} is not {FILE_FORMAT} version 1")
    pts = d.get("points") or {}
    for k in pts:
        if not KEY_RE.match(k):
            raise SystemExit(f"REFUSED: practice point key {k!r}: lower case, digits and hyphens")
    return pts


# ---------------------------------------------------------------- content hash (the factory's rule)

def _strip(obj):
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in HASH_EXCLUDE}
    if isinstance(obj, list):
        return [_strip(v) for v in obj]
    return obj


def content_hash(obj) -> str:
    """`sha256:` and the SHA-256 of the object's JCS form without version, content_hash, status,
    withdrawal, tags and admin (oetacademy-exercises release-format §4; the site recomputes it on
    import). The items hold strings, booleans and integers only, for which this is JCS."""
    if _has_float(obj):
        raise SystemExit("REFUSED: a practice item holds a number that is not an integer")
    s = json.dumps(_strip(obj), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()


def _has_float(obj) -> bool:
    if isinstance(obj, float):
        return True
    if isinstance(obj, dict):
        return any(_has_float(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_float(v) for v in obj)
    return False


def hashed(item: dict) -> dict:
    """The item with its parts' and its own content_hash set (each part hashed alone)."""
    item = json.loads(json.dumps(item))
    for g in item.get("gaps") or []:
        g["content_hash"] = content_hash(g)
    item["content_hash"] = content_hash(item)
    return item


# ---------------------------------------------------------------- the item contract, as far as it is checked here

def _units(item: dict) -> list[dict]:
    return item.get("gaps") if item["type"] in ("gapfill", "wordbank") else [item]


def check_item(item: dict, where: str, seen: set[str]) -> None:
    """The rules of the site's item contract that a mistake here would break (the site's own
    validator is the authority, ADR-0027 Amendment 2): ids in the fixture block, unique; the
    approved types; a key among the item's options; a typed unit's scheme and feedback; tags."""
    def bad(msg):
        raise SystemExit(f"REFUSED: practice item {where}: {msg}")
    t = item.get("type")
    if t not in TYPES:
        bad(f"type {t!r} is not an approved type ({', '.join(sorted(TYPES))})")
    ids = [item["item_id"]] + [g["gap_id"] for g in item.get("gaps") or []]
    for i in ids:
        if not ITEM_ID_RE.match(i):
            bad(f"id {i!r} is not an item id")
        if int(i[-6:]) < FIXTURE_LOW:
            bad(f"id {i!r} is outside the fixture block: the engine has no block of its own yet (ADR 046)")
        if i in seen:
            bad(f"id {i!r} is used twice")
        seen.add(i)
    opts = {o["option_id"] for o in item.get("options") or []}
    for o in opts:
        if not o.startswith(item["item_id"] + "-o"):
            bad(f"option {o!r} is not {item['item_id']}-o<n>")
    for u in _units(item):
        if not (u.get("tags") or {}).get("practises"):
            bad("a unit with no practises tags")
        if t in ("text", "gapfill"):
            sc = u["scoring"]
            if sc.get("marking_scheme") not in SCHEMES:
                bad(f"marking scheme {sc.get('marking_scheme')!r}")
            if not sc.get("accepted"):
                bad("a typed unit with no accepted form")
            for w in u["feedback"]["wrong_answers"]:
                if w["root_cause"] not in ROOT_CAUSES:
                    bad(f"root cause {w['root_cause']!r}")
            if t == "gapfill" and u["prompt"].count("____") != 1:
                bad("a gap's prompt has exactly one ____")
        if t in ("choice", "wordbank"):
            key = u["scoring"]["key_option_id"]
            if key not in opts:
                bad(f"key {key!r} is not an option of the item")
            fb = u["feedback"]["options"]
            if key in fb or not set(fb) <= opts:
                bad("feedback on the key, or on an option the item does not have")
    if t == "ordering":
        orders = item["scoring"]["accepted_orders"]
        if any(sorted(o) != sorted(opts) for o in orders) or item["display_order"] in orders:
            bad("an accepted order is not a permutation of the options, or the start is one")


def check_check(chk: dict, where: str) -> None:
    """A sentence's self-check list (ADR 046): the model, its points, each with its id and tags."""
    if chk.get("marking") not in CHECK_MARKING:
        raise SystemExit(f"REFUSED: practice point {where}: check marking {chk.get('marking')!r}")
    if not chk.get("model") or not chk.get("points"):
        raise SystemExit(f"REFUSED: practice point {where}: a check needs a model and its points")
    ids = [p["id"] for p in chk["points"]]
    if len(set(ids)) != len(ids) or any(not (p.get("practises")) for p in chk["points"]):
        raise SystemExit(f"REFUSED: practice point {where}: check points need unique ids and tags")


# ---------------------------------------------------------------- attaching the points to the timeline

def _answer_shown(utts: list[dict], i: int) -> bool:
    """The fallback: an utterance after the pause shows something (a reveal or a typing cue)."""
    return any(c["type"] in ("reveal", "type") for u in utts[i + 1:i + 3] for c in u["cues"])


def attach(L: Path, boards: list[dict], sample: bool = False) -> bool:
    """Give each state the practice points of its pauses (`state.practice`) and each such pause
    the point's id (`cue.practice`). True when the lesson has any. Refuses a pause that names no
    point, a point no pause names (unless a sample build), a pause outside 3 to 10 seconds, and a
    point whose answer the next utterances do not show (the fallback, rule 57)."""
    pts = load(L)
    if pts is None:
        return False
    used, seen_ids = set(), set()
    for bd in boards:
        utts = [u for s in bd["states"] for u in s["utterances"]]
        for s in bd["states"]:
            for u in s["utterances"]:
                for c in u["cues"]:
                    if c["type"] != "pause" or not str(c.get("text") or "").startswith(PAUSE_PREFIX):
                        continue
                    key = c["text"][len(PAUSE_PREFIX):].strip()
                    if key not in pts:
                        raise SystemExit(f"REFUSED: pause {u['id']} {c['id']} names practice point {key!r}, "
                                         "not in analysis/practice.json")
                    if key in used:
                        raise SystemExit(f"REFUSED: practice point {key!r} is named by two pauses")
                    if not (PAUSE_MIN <= float(c["seconds"]) <= PAUSE_MAX):
                        raise SystemExit(f"REFUSED: practice point {key!r}: its pause is {c['seconds']} s "
                                         f"(the fallback's pause is {PAUSE_MIN:g} to {PAUSE_MAX:g})")
                    if not _answer_shown(utts, utts.index(u)):
                        raise SystemExit(f"REFUSED: practice point {key!r}: no reveal or typing in the two "
                                         "utterances after its pause (the fallback shows the answer, rule 57)")
                    used.add(key)
                    p = pts[key]
                    pid = f"{bd['section']}_pp-{key}"
                    items = [hashed(it) for it in p["items"]]
                    for n, it in enumerate(items, 1):
                        check_item(it, f"{key} #{n}", seen_ids)
                    if not 1 <= len(items) <= 3:
                        raise SystemExit(f"REFUSED: practice point {key!r}: 1 to 3 items (a handout's practice step)")
                    point = {"id": pid, "time": c["time"], "resume": c["time_end"],
                             "utterance": u["id"], "cue": c["id"], "task": p["task"],
                             "excerpt": p["excerpt"], "items": items}
                    if p.get("check"):
                        check_check(p["check"], key)
                        point["check"] = p["check"]
                    s.setdefault("practice", []).append(point)
                    c["practice"] = pid
    missing = sorted(set(pts) - used)
    if missing and not sample:
        raise SystemExit(f"REFUSED: practice points no pause names: {', '.join(missing)}")
    return bool(used)

