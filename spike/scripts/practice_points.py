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

IDs (ADR 046 amendment of 2026-10-30; the site's ADR-0031 Amendment 1). The engine's block is
900000-989999, in every skill. Every item and part ID the engine uses is issued by `issue` and kept
in the registry `spike/practice/ids.json` (in the repository): one entry per ID, naming the lesson,
the point and the slot it was issued for. An ID is issued once, never reused, and never moves to
another lesson or point; a point that is dropped keeps its entries. `attach` refuses an ID that is
outside the block or that the registry did not issue for that lesson and point, so a fixture ID
(990000-999999, which the site refuses in production) can no longer be built.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "spike" / "practice" / "ids.json"
REGISTRY_FORMAT = "oetbook-practice-ids"

FORMAT_VERSION = "1.23"            # bundle format of a lesson with practice points (ADR 046)
FILE_FORMAT = "oetbook-practice-points"
PAUSE_PREFIX = "practice: "
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
ITEM_ID_RE = re.compile(r"^oa-(reading|listening|grammar|vocabulary|writing|speaking)-[0-9]{6}$")
# the site's ID blocks (ADR-0031 Amendment 1): the lesson engine's is 900000-989999 in every skill;
# 990000-999999 are examples and fixtures, refused in production (LP-FIXTURE).
BLOCK_LOW, BLOCK_HIGH = 900000, 989999
SLOT_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
PAUSE_MIN, PAUSE_MAX = 3.0, 10.0   # s: the fallback's pause (every pause is 0.5 to 10, §5)
TYPES = {"choice", "text", "gapfill", "wordbank", "ordering",   # approved: ADR-0031 §3, ADR-0032
         "selfcheck", "errorspot"}                              # selfcheck: contracts 1.13.0 (site #200)
SCHEMES = {"oet-typed-v1", "oet-typed-form-v1"}                 # both accepted, contracts 1.13.0
ROOT_CAUSES = {"word-match", "mentioned-not-asked", "partial", "overgeneralisation", "reversal",
               "wrong-referent", "world-knowledge", "speaker-confusion", "unaccepted-proposal",
               "sound-alike", "wrong-text", "form-change", "spelling", "too-much", "wrong-form",
               "wrong-rule"}
HASH_EXCLUDE = {"version", "content_hash", "status", "withdrawal", "tags", "admin"}
SELFCHECK_MAX_WORDS = 40


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


# ---------------------------------------------------------------- the ID registry

def registry() -> dict:
    if not REGISTRY.exists():
        return {"format": REGISTRY_FORMAT, "version": 1,
                "about": "Every practice item and part ID the lesson engine has issued (ADR 046 amendment of "
                         "2026-10-30): the engine's block is 900000-989999 in every skill (oetacademy-web "
                         "ADR-0031 Amendment 1). Each lesson has its own range of the block (`ranges`, set by "
                         "practice_points.reserve, as the owner assigns them); every ID a lesson uses is issued inside "
                         "it. Append only: an ID is never reused and never moves to another lesson or point. Written "
                         "by practice_points.issue.",
                "block": [BLOCK_LOW, BLOCK_HIGH], "ranges": {}, "ids": []}
    d = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if d.get("format") != REGISTRY_FORMAT or d.get("version") != 1:
        raise SystemExit(f"REFUSED: {REGISTRY} is not {REGISTRY_FORMAT} version 1")
    check_registry(d)
    return d


def check_registry(d: dict) -> None:
    """Every lesson's range inside the block, no two overlapping; every entry inside its lesson's range,
    its number unique across skills, its slot named once."""
    ranges = d.get("ranges") or {}
    spans = sorted((lo, hi, les) for les, (lo, hi) in ranges.items())
    for i, (lo, hi, les) in enumerate(spans):
        if not BLOCK_LOW <= lo <= hi <= BLOCK_HIGH:
            raise SystemExit(f"REFUSED: the ID range of {les} is outside the engine's block")
        if i and lo <= spans[i - 1][1]:
            raise SystemExit(f"REFUSED: the ID ranges of {spans[i - 1][2]} and {les} overlap")
    nums, slots = set(), set()
    for e in d["ids"]:
        n = int(e["id"][-6:])
        if not ITEM_ID_RE.match(e["id"]) or not BLOCK_LOW <= n <= BLOCK_HIGH:
            raise SystemExit(f"REFUSED: registry entry {e['id']} is outside the engine's block")
        lo, hi = ranges.get(e["lesson"], (None, None))
        if lo is None or not lo <= n <= hi:
            raise SystemExit(f"REFUSED: registry entry {e['id']} is outside the range of {e['lesson']}")
        if n in nums:
            raise SystemExit(f"REFUSED: registry number {n} issued twice")
        k = (e["lesson"], e["point"], e["slot"])
        if k in slots:
            raise SystemExit(f"REFUSED: registry slot {k} issued twice")
        nums.add(n)
        slots.add(k)


def _write(d: dict) -> None:
    check_registry(d)
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def reserve(lesson: str, low: int, high: int) -> None:
    """Gives `lesson` its range of the block (the owner assigns them: Writing 4 900000-900999, Grammar 1
    950000-950999, Grammar 2 951000-951999). A range once set never changes."""
    d = registry()
    ranges = d.setdefault("ranges", {})
    if lesson in ranges:
        if ranges[lesson] != [low, high]:
            raise SystemExit(f"REFUSED: {lesson} already has the range {ranges[lesson]}")
        return
    ranges[lesson] = [low, high]
    _write(d)


def issue(lesson: str, point: str, slot: str, skill: str = "writing") -> str:
    """The ID of `slot` (an item or a part, named by the lesson's own words) of practice point
    `point` of `lesson`: the one already issued, or the next number of the lesson's own range after
    the highest it has issued, recorded."""
    if not KEY_RE.match(point) or not SLOT_RE.match(slot):
        raise SystemExit(f"REFUSED: practice ID slot {point!r} {slot!r}: lower case, digits and hyphens")
    d = registry()
    for e in d["ids"]:
        if (e["lesson"], e["point"], e["slot"]) == (lesson, point, slot):
            if not e["id"].startswith(f"oa-{skill}-"):
                raise SystemExit(f"REFUSED: {e['id']} was issued for another skill")
            return e["id"]
    if lesson not in (d.get("ranges") or {}):
        raise SystemExit(f"REFUSED: {lesson} has no ID range in {REGISTRY.name} (practice_points.reserve)")
    lo, hi = d["ranges"][lesson]
    n = max([lo - 1] + [int(e["id"][-6:]) for e in d["ids"] if e["lesson"] == lesson]) + 1
    if n > hi:
        raise SystemExit(f"REFUSED: the ID range of {lesson} is used up")
    new = f"oa-{skill}-{n:06d}"
    d["ids"].append({"id": new, "lesson": lesson, "point": point, "slot": slot,
                     "issued": datetime.date.today().isoformat()})
    _write(d)
    return new


def issued(lesson: str) -> dict[str, str]:
    """ID -> point, for every ID the registry issued for `lesson`."""
    return {e["id"]: e["point"] for e in registry()["ids"] if e["lesson"] == lesson}


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


def check_item(item: dict, where: str, seen: set[str], ids_issued: dict[str, str] | None = None,
               point: str | None = None) -> None:
    """The rules of the site's item contract that a mistake here would break (the site's own
    validator is the authority, ADR-0027 Amendment 2): ids in the engine's block, issued by the
    registry for this lesson and point, unique; the approved types; a key among the item's
    options; a typed unit's scheme and feedback; a self-check's model and points; tags."""
    def bad(msg):
        raise SystemExit(f"REFUSED: practice item {where}: {msg}")
    t = item.get("type")
    if t not in TYPES:
        bad(f"type {t!r} is not an approved type ({', '.join(sorted(TYPES))})")
    ids = [item["item_id"]] + [g["gap_id"] for g in item.get("gaps") or []]
    for i in ids:
        if not ITEM_ID_RE.match(i):
            bad(f"id {i!r} is not an item id")
        if not BLOCK_LOW <= int(i[-6:]) <= BLOCK_HIGH:
            bad(f"id {i!r} is outside the engine's block ({BLOCK_LOW}-{BLOCK_HIGH})")
        if ids_issued is not None and ids_issued.get(i) != point:
            bad(f"id {i!r} was not issued for this lesson's point {point!r} (spike/practice/ids.json)")
        if i in seen:
            bad(f"id {i!r} is used twice")
        seen.add(i)
    if t == "selfcheck":
        _check_selfcheck(item, bad)
        return
    if t == "errorspot":
        _check_errorspot(item, bad)
        return
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


def _check_errorspot(item: dict, bad) -> None:
    """`errorspot` (ADR-0032): one error span of at most 4 words in a sentence of at most 40; each listed
    wrong tap outside it, once; a correction typed under a known scheme, its wrong corrections listed."""
    words = item["sentence"].split(" ")
    sp = item["scoring"]["error_words"]
    if len(words) > 40 or "  " in item["sentence"]:
        bad("an errorspot sentence has at most 40 words, single spaces (ERRORSPOT-SENTENCE)")
    if not 1 <= sp["first"] <= sp["last"] <= len(words) or sp["last"] - sp["first"] >= 4:
        bad("the error span lies inside the sentence and is at most 4 words (ERRORSPOT-SPAN)")
    taps = [w["word"] for w in item["feedback"].get("wrong_words") or []]
    if len(set(taps)) != len(taps) or any(not 1 <= n <= len(words) or sp["first"] <= n <= sp["last"] for n in taps):
        bad("each wrong tap is listed once, inside the sentence and outside the span (ERRORSPOT-WRONG-WORD)")
    corr = item.get("correction")
    if bool(corr) != ("wrong_corrections" in item["feedback"]):
        bad("wrong_corrections is given exactly when the item has a correction (ERRORSPOT-CORRECTION)")
    if corr and (corr["scoring"].get("marking_scheme") not in SCHEMES or not corr["scoring"].get("accepted")):
        bad("a correction is typed: accepted forms under a known marking scheme")
    if not (item.get("tags") or {}).get("practises"):
        bad("an errorspot needs practises tags")


def _check_selfcheck(item: dict, bad) -> None:
    """`selfcheck` (contracts 1.13.0, site #200): a sentence box, the model and 2 to 10 points."""
    if "____" in item["prompt"]:
        bad("a self-check's prompt has no ____ (SENTENCE-PROMPT)")
    r = item["response"]
    if r.get("size") != "sentence" or not 1 <= r.get("max_words", 0) <= SELFCHECK_MAX_WORDS:
        bad(f"a self-check's response is a sentence box of at most {SELFCHECK_MAX_WORDS} words")
    if len(item["model"].split()) > r["max_words"]:
        bad("the model is longer than max_words (MAX-WORDS)")
    pts = item["points"]
    if not 2 <= len(pts) <= 10:
        bad("a self-check has 2 to 10 points")
    ids = [p["point_id"] for p in pts]
    if len(set(ids)) != len(ids) or any(not re.fullmatch(re.escape(item["item_id"]) + r"-c[1-9][0-9]*", i)
                                        for i in ids):
        bad("self-check point ids are <item id>-c<n>, once each (SELFCHECK-POINT)")
    if any(not (p.get("tags") or {}).get("practises") for p in pts) or not (item.get("tags") or {}).get("practises"):
        bad("a self-check and each of its points need practises tags")
    if item["scoring"] != {"method": "self-check"} or not item["feedback"].get("key"):
        bad("a self-check's scoring is {method: self-check}, with a feedback key")


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
    ids_issued = issued(L.name)
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
                        check_item(it, f"{key} #{n}", seen_ids, ids_issued, key)
                    if not 1 <= len(items) <= 3:
                        raise SystemExit(f"REFUSED: practice point {key!r}: 1 to 3 items (a handout's practice step)")
                    point = {"id": pid, "time": c["time"], "resume": c["time_end"],
                             "utterance": u["id"], "cue": c["id"], "task": p["task"],
                             "excerpt": p["excerpt"], "items": items}
                    if p.get("check"):         # valid in 1.23, but a whole sentence is a selfcheck item
                        raise SystemExit(f"REFUSED: practice point {key!r}: the interim check is retired; "
                                         "write the sentence as a selfcheck item (ADR 046 amendment (1))")
                    s.setdefault("practice", []).append(point)
                    c["practice"] = pid
    missing = sorted(set(pts) - used)
    if missing and not sample:
        raise SystemExit(f"REFUSED: practice points no pause names: {', '.join(missing)}")
    return bool(used)

