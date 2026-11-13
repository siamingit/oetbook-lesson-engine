"""Speaking practice items (ADR 053, ADR 054, ADR 055): the one place that knows the site's speaking contract.

A Speaking lesson's practice points (analysis/practice.json, ADR 046) hold items of three Speaking Coach
types, each released in the site's contracts and carried by a session's practice point, alone in it
(LP-PRACTICE-ITEM):

  speak_repeat    contracts 1.22.0 (handout.schema.json $defs/speakRepeatItem): say a line after the
                  model; two narration files, normal and slow
  speak_respond   contracts 1.25.0 ($defs/speakRespondPracticeItem): answer the patient's line; one
                  narration file, the patient's line; cues the site ticks by their match words
  roleplay        contracts 1.26.0 ($defs/rolePlayPracticeItem): talk with the patient, played by the
                  site's AI from the patient card; no recording

    check(item, where)          the engine's form of an item is valid (build time)
    browser_view(item, audio)   what the lesson's own player is given (bundle 1.24)
    release_item(item, n)       an item in the released contract's shape (publish)
    cue_said(match, text)       the site's cue rule, as the engine reads it (RP-SPEAK-CUES)

The engine's form of an item (in practice.json):
  item_id   "oa-speaking-NNNNNN", issued by the practice ID registry for skill "speaking"; the
            released item's item_id is the same
  audio     never written by hand: synthesize_speaking.py makes the recordings
            (generated/speaking-audio/), and publish fills the contract's audio fields
  every type      `profession` (released, it goes to tags.facets.profession, admin-only) and `tags`
                  {practises: [taxonomy keys]}, needed to publish
  speak_repeat    `pass_score` (the old draft's) is ignored: the released item has none
  speak_respond   `prompt` (released: task), `patient_line`, `patient_speaker` patient_f or patient_m
                  (the patient's voice) and, where the card makes the patient worried or upset,
                  `patient_emotion`; `cues` [{text, match, example}], `model_answer`, `max_s`;
                  `prepare_s` is the lesson's own pop-up's only
  roleplay        `title` (the point's excerpt's, not the item's), `length` short or whole, `setting`,
                  `patient_speaker`, `candidate` {role (the job), role_line (released: card.role),
                  background, tasks}, `patient` {name, role, persona, emotion, opening, hidden,
                  concern}: the patient card stays server-side; `prepare_s`, `talk_s` the pop-up's only
"""

from __future__ import annotations

import json
import re

CONTRACT_FORMAT = "oetacademy-speaking-items"
RELEASED_IN = {"speak_repeat": "1.22.0", "speak_respond": "1.25.0", "roleplay": "1.26.0"}
RELEASED_TYPES = tuple(RELEASED_IN)          # every type is in the site's contracts
TYPES = ("speak_repeat", "speak_respond", "roleplay")
SKILL = "speaking"               # the registry's skill: oa-speaking-NNNNNN
ENGINE_ID_RE = re.compile(r"^oa-speaking-([0-9]{6})$")
SPEAKERS = ("patient_f", "patient_m")
FEELINGS = ("worried", "upset")
SITE_PATIENT_VOICE = {"patient_f": "patient-f", "patient_m": "patient-m"}   # Gemma, Archie (ADR 027)
SLOW_SPEED = 0.75                # the slow take: 0.75 of the normal speed, every sound kept (1.22.0)
CHUNKS_MAX = 6
CUES = (2, 4)
MATCH_MAX = 12
MATCH_RE = re.compile(r"^[a-z']+\*?( [a-z']+\*?)*$")
MAX_S = (10, 90)
TASKS = {"short": (2, 3), "whole": (3, 6)}  # RP-ROLEPLAY-TASKS
HIDDEN = (1, 4)
# a speak_repeat as practice.json holds it: these fields, nothing else
REPEAT_FIELDS = {"item_id", "type", "profession", "focus", "shown", "spoken", "chunks", "target_sounds",
                 "tags", "pass_score", "version"}
RESPOND_FIELDS = {"item_id", "type", "profession", "focus", "prompt", "patient_line", "patient_speaker",
                  "patient_emotion", "cues", "prepare_s", "max_s", "model_answer", "tags", "version"}
ROLEPLAY_FIELDS = {"item_id", "type", "profession", "focus", "title", "length", "setting", "patient_speaker",
                   "candidate", "patient", "prepare_s", "talk_s", "tags", "version"}

# The recordings each type needs, made by synthesize_speaking.py: role -> (what is said, who)
#   who: "teacher" (Rupert) or "patient" (the item's patient_speaker)
ROLES = {
    "speak_repeat": {"normal": ("spoken", "teacher"), "slow": ("spoken", "teacher")},
    "speak_respond": {"patient": ("patient_line", "patient"), "model": ("model_answer", "teacher")},
    "roleplay": {},
}
# The released item's audio fields: contract role -> the recording it is encoded from. A speak_respond's
# model answer is read by the site's own voice (contracts 1.25.0); its recording is the pop-up's only.
CONTRACT_AUDIO = {
    "speak_repeat": {"normal": "normal", "slow": "slow"},
    "speak_respond": {"normal": "patient"},
    "roleplay": {},
}
PATH_ROLE = {"normal": "normal", "slow": "slow", "patient": "patient"}


def is_speaking(item: dict) -> bool:
    return item.get("type") in TYPES


def is_released(item: dict) -> bool:
    """A type the site's contracts carry, in either form."""
    return item.get("type") in RELEASED_TYPES


def is_contract_form(item: dict) -> bool:
    """A speaking item already in the contract's shape (release_item), as a package holds it."""
    return is_released(item) and isinstance(item.get("content_hash"), str) and item.get("status") == "active"


def recordings(item: dict) -> dict[str, dict]:
    """role -> {text, who, slow} for each recording the item needs (synthesize_speaking.py)."""
    out = {}
    for role, (field, who) in ROLES[item["type"]].items():
        text = item.get(field)
        if not text:
            continue                                   # an optional field the item does not have
        out[role] = {"text": text, "who": item.get("patient_speaker") if who == "patient" else "teacher",
                     "emotion": item.get("patient_emotion") if who == "patient" else None,
                     "slow": role == "slow"}
    return out


# ---------------------------------------------------------------- the cue rule (RP-SPEAK-CUES)
# The engine's reading of the site's rule, as the schema's speakCue.match describes it: plain lower-case
# words (contractions opened, small numbers in words, a break where a sentence ends); a phrase's words in
# order with at most two words between, never across a break; a final * any ending, a plural s always;
# a phrase without a negation never just after not, no, never or without (three words back, to a break).

NEGATIONS = frozenset({"not", "no", "never", "without"})
GAP = 2
NEG_REACH = 3
BREAK = "|"
SMALL_NUMBERS = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six",
                 "7": "seven", "8": "eight", "9": "nine", "10": "ten", "12": "twelve", "20": "twenty",
                 "24": "twenty four", "48": "forty eight"}


def cue_words(text: str) -> list[str]:
    s = re.sub(r"[’‘`]", "'", (text or "").lower())
    s = re.sub(r"\bcan't\b|\bcannot\b", "can not", s)
    s = re.sub(r"\bwon't\b", "will not", s)
    s = re.sub(r"\bshan't\b", "shall not", s)
    s = re.sub(r"n't\b", " not", s)
    s = re.sub(r"\d+", lambda m: SMALL_NUMBERS.get(m.group(0), " "), s)
    s = re.sub(r"[.!?;]+", f" {BREAK} ", s)
    s = re.sub(r"[^a-z'| ]+", " ", s)
    return [w for w in (t.strip("'") for t in s.split()) if w]


def _word_ok(pattern: str, word: str) -> bool:
    if pattern.endswith("*"):
        return word.startswith(pattern[:-1])
    return word in (pattern, pattern + "s")


def _negated(words: list[str], i: int) -> bool:
    for k in range(i - 1, max(i - NEG_REACH, 0) - 1, -1):
        if words[k] == BREAK:
            return False
        if words[k] in NEGATIONS:
            return True
    return False


def phrase_said(phrase: str, words: list[str]) -> bool:
    parts = phrase.lower().split()
    if not parts:
        return False
    guarded = not NEGATIONS.intersection(parts)
    for i, w in enumerate(words):
        if not _word_ok(parts[0], w) or (guarded and _negated(words, i)):
            continue
        at = i
        for p in parts[1:]:
            nxt = next((k for k in range(at + 1, min(at + 2 + GAP, len(words)))
                        if words[k] != BREAK and _word_ok(p, words[k])), None)
            stop = next((k for k in range(at + 1, min(at + 2 + GAP, len(words))) if words[k] == BREAK), None)
            if nxt is None or (stop is not None and stop < nxt):
                break
            at = nxt
        else:
            return True
    return False


def cue_said(match: list[str], text: str) -> bool:
    words = cue_words(text)
    return any(phrase_said(p, words) for p in match)


# ---------------------------------------------------------------- the released form

def audio_paths(item_id: str, kind: str = "speak_repeat") -> dict[str, str]:
    """The package paths of an item's narration files: contract role -> path."""
    m = ENGINE_ID_RE.match(item_id or "")
    if not m:
        raise ValueError(f"{item_id!r} is not a speaking item id (oa-speaking-NNNNNN)")
    return {role: f"audio/speak-{m.group(1)}-{PATH_ROLE[rec]}.m4a" for role, rec in CONTRACT_AUDIO[kind].items()}


def _final_mark_off(s: str) -> str:
    return re.sub(r"[.?!]$", "", s or "")


def repeat_findings(it: dict, where: str) -> list[str]:
    """The rules of a speak_repeat the schema cannot say (RP-SPEAK-CHUNKS, -NUMBERS, -AUDIO) and
    RP-SPEAK-SHOWN (contracts 1.26.0: shown reads word for word as spoken; only capitals and the final
    . ? or ! may differ), on either form of the item."""
    out = []
    spoken = it.get("spoken") or ""
    if " ".join(it.get("chunks") or []) != _final_mark_off(spoken):
        out.append(f"{where}: RP-SPEAK-CHUNKS: the chunks joined with single spaces are not `spoken` "
                   "without its final . ? or !")
    if re.search(r"[0-9]", spoken):
        out.append(f"{where}: RP-SPEAK-NUMBERS: `spoken` has a digit; write numbers as they are said")
    plain = lambda s: re.sub(r"[.?!]+$", "", (s or "").strip()).lower()  # noqa: E731
    if plain(it.get("shown")) != plain(spoken):
        out.append(f"{where}: RP-SPEAK-SHOWN: `shown` does not read word for word as `spoken` (only capitals "
                   "and the final mark may differ): the learner says what they read")
    a = it.get("audio")
    if isinstance(a, dict) and a.get("normal") == a.get("slow"):
        out.append(f"{where}: RP-SPEAK-AUDIO: normal and slow are the same file")
    return out


def respond_findings(it: dict, where: str) -> list[str]:
    """A speak_respond's rules the schema cannot say, on either form: RP-SPEAK-CUES (the model answer
    says every cue, each cue's example says its own cue, by the cue's match words) and RP-SPEAK-NUMBERS
    (no digit in patient_line, model_answer or an example); the cues' shape too."""
    out = []
    cues = it.get("cues")
    if not isinstance(cues, list) or not CUES[0] <= len(cues) <= CUES[1]:
        return [f"{where}: `cues` is {CUES[0]} to {CUES[1]} cues {{text, match, example}}"]
    model = it.get("model_answer") or ""
    for n, c in enumerate(cues, 1):
        if not isinstance(c, dict) or set(c) != {"text", "match", "example"} \
                or not all(isinstance(c[k], str) and c[k].strip() for k in ("text", "example")):
            out.append(f"{where}: cue {n} is {{text, match, example}}, each a text")
            continue
        m = c["match"]
        if not isinstance(m, list) or not 1 <= len(m) <= MATCH_MAX or len(set(m)) != len(m) \
                or not all(isinstance(p, str) and len(p) <= 60 and MATCH_RE.match(p) for p in m):
            out.append(f"{where}: cue {n} ({c['text']!r}): `match` is 1 to {MATCH_MAX} different lower-case words "
                       "or phrases ([a-z'], a final * for any ending)")
            continue
        if not cue_said(m, model):
            out.append(f"{where}: RP-SPEAK-CUES: the model answer does not say cue {n} ({c['text']!r}) by its "
                       "match words")
        if not cue_said(m, c["example"]):
            out.append(f"{where}: RP-SPEAK-CUES: cue {n}'s example ({c['example']!r}) does not say its cue by "
                       "its match words")
        if re.search(r"[0-9]", c["example"]):
            out.append(f"{where}: RP-SPEAK-NUMBERS: cue {n}'s example has a digit")
    for k in ("patient_line", "model_answer"):
        if re.search(r"[0-9]", it.get(k) or ""):
            out.append(f"{where}: RP-SPEAK-NUMBERS: `{k}` has a digit; write numbers as they are said")
    return out


def roleplay_findings(it: dict, where: str) -> list[str]:
    """A role-play's rules the schema cannot say, on either form: RP-ROLEPLAY-TASKS (two or three tasks
    for a short one, three to six for a whole one) and RP-SPEAK-NUMBERS (no digit in the opening)."""
    out = []
    tasks = (it.get("card") or it.get("candidate") or {}).get("tasks") or []
    lo, hi = TASKS.get(it.get("length"), (0, -1))
    if not lo <= len(tasks) <= hi:
        out.append(f"{where}: RP-ROLEPLAY-TASKS: a {it.get('length')!r} role-play has {lo} to {hi} tasks, "
                   f"this one {len(tasks)}")
    if re.search(r"[0-9]", (it.get("patient") or {}).get("opening") or ""):
        out.append(f"{where}: RP-SPEAK-NUMBERS: the patient's opening has a digit; write numbers as they are said")
    return out


def _tags(item: dict) -> dict:
    where = item.get("item_id")
    tags = json.loads(json.dumps(item.get("tags") or {}))
    if not tags.get("practises"):
        raise SystemExit(f"REFUSED: speaking item {where}: no tags.practises; write the taxonomy keys it "
                         "practises in analysis/practice.json (for example speaking.language.intelligibility)")
    if item.get("profession"):
        profs = tags.setdefault("facets", {}).setdefault("profession", [])
        if item["profession"] not in profs:
            profs.append(item["profession"])
    return tags


def release_item(item: dict, number: int = 1, version: int = 1) -> dict:
    """An item in the released contract's shape, hashed: no engine-only field (pass_score, prepare_s,
    talk_s, patient_speaker, title); the profession goes to tags.facets.profession, admin-only."""
    import practice_points as pp
    where = item.get("item_id")
    t = item.get("type")
    if not is_released(item):
        raise SystemExit(f"REFUSED: speaking item {where}: {t!r} is not in the site's contracts "
                         f"({', '.join(RELEASED_TYPES)})")
    tags = _tags(item)
    c = {"item_id": item["item_id"], "type": t, "number": number}
    if item.get("focus"):
        c["focus"] = item["focus"]
    if t == "speak_repeat":
        c.update({"shown": item["shown"], "spoken": item["spoken"], "chunks": list(item["chunks"])})
        if item.get("target_sounds"):
            c["target_sounds"] = list(item["target_sounds"])
        c.update({"audio": audio_paths(item["item_id"], t), "scoring": {"method": "pronunciation"}})
        problems = repeat_findings(c, where)
    elif t == "speak_respond":
        c.update({"task": item["prompt"], "patient_line": item["patient_line"],
                  "audio": audio_paths(item["item_id"], t),
                  "cues": [{"text": x["text"], "match": list(x["match"]), "example": x["example"]}
                           for x in item["cues"]],
                  "model_answer": item["model_answer"], "max_s": item["max_s"], "scoring": {"method": "ai"}})
        problems = respond_findings(c, where)
    else:
        cand, pat = item["candidate"], item["patient"]
        card = {"setting": item["setting"], "role": cand["role_line"]}
        if cand.get("background"):
            card["background"] = cand["background"]
        card["tasks"] = list(cand["tasks"])
        c.update({"length": item["length"], "card": card,
                  "patient": {"name": pat["name"], "role": pat["role"], "opening": pat["opening"],
                              "voice": SITE_PATIENT_VOICE[item["patient_speaker"]]},
                  "patient_card": {"persona": pat["persona"], "emotion": pat["emotion"],
                                   "concern": pat["concern"], "hidden": list(pat["hidden"])},
                  "scoring": {"method": "ai"}})
        problems = roleplay_findings(c, where)
    c.update({"tags": tags, "version": version, "status": "active"})
    if problems:
        raise SystemExit("REFUSED: " + "; ".join(problems))
    return pp.hashed(c)


# ---------------------------------------------------------------- the engine's check

def check(item: dict, where: str) -> None:
    """Refuses an item the engine cannot use, or the site's contracts would refuse: each type's fields
    and the released rules (the schema itself is checked at publish)."""
    def bad(msg):
        raise SystemExit(f"REFUSED: speaking item {where}: {msg}")
    t = item.get("type")
    if t not in TYPES:
        bad(f"type {t!r}: one of {', '.join(TYPES)}")
    if not ENGINE_ID_RE.match(item.get("item_id") or ""):
        bad(f"item_id {item.get('item_id')!r}: oa-speaking-NNNNNN, issued by the registry")
    if "audio" in item or "patient_audio" in item or "id" in item:
        bad("audio and the contract id are made by the engine, never written in practice.json")
    if t in ("speak_respond", "roleplay"):
        if item.get("patient_speaker") not in SPEAKERS:
            bad(f"patient_speaker {item.get('patient_speaker')!r}: one of {', '.join(SPEAKERS)}")
    if item.get("patient_emotion") is not None:
        if t != "speak_respond" or item["patient_emotion"] not in FEELINGS:
            bad(f"patient_emotion {item['patient_emotion']!r}: on a speak_respond only, one of "
                f"{', '.join(FEELINGS)}")
    tags = item.get("tags")
    if tags is not None and (not isinstance(tags, dict) or not tags.get("practises")):
        bad("`tags` has `practises`: taxonomy keys")
    if t == "speak_repeat":
        _check_repeat(item, bad)
    elif t == "speak_respond":
        _check_respond(item, bad)
    else:
        _check_roleplay(item, bad)


def _text(item: dict, k: str) -> bool:
    return isinstance(item.get(k), str) and bool(item[k].strip())


def _check_repeat(item: dict, bad) -> None:
    extra = set(item) - REPEAT_FIELDS
    if extra:
        bad(f"fields a speak_repeat does not have: {', '.join(sorted(extra))}")
    for k in ("shown", "spoken"):
        if not _text(item, k):
            bad(f"`{k}` is a sentence")
    ch = item.get("chunks")
    if not isinstance(ch, list) or not 1 <= len(ch) <= CHUNKS_MAX \
            or not all(isinstance(c, str) and c.strip() for c in ch):
        bad(f"`chunks` is 1 to {CHUNKS_MAX} sense groups")
    ts = item.get("target_sounds")
    if ts is not None and (not isinstance(ts, list) or len(set(ts)) != len(ts)
                           or not all(isinstance(x, str) and 1 <= len(x) <= 4 for x in ts)):
        bad("`target_sounds` is a list of distinct IPA phonemes, 1 to 4 characters each")
    problems = repeat_findings(item, item["item_id"])
    if problems:
        bad("; ".join(problems))


def _check_respond(item: dict, bad) -> None:
    extra = set(item) - RESPOND_FIELDS
    if extra:
        bad(f"fields a speak_respond does not have: {', '.join(sorted(extra))}")
    for k in ("prompt", "patient_line", "model_answer"):
        if not _text(item, k):
            bad(f"`{k}` is a text (a speak_respond needs its model answer: the lesson shows it, ADR 053)")
    if not isinstance(item.get("max_s"), int) or not MAX_S[0] <= item["max_s"] <= MAX_S[1]:
        bad(f"`max_s` is {MAX_S[0]} to {MAX_S[1]} seconds")
    problems = respond_findings(item, item["item_id"])
    if problems:
        bad("; ".join(problems))


def _check_roleplay(item: dict, bad) -> None:
    extra = set(item) - ROLEPLAY_FIELDS
    if extra:
        bad(f"fields a roleplay does not have: {', '.join(sorted(extra))}")
    if item.get("length") not in TASKS:
        bad(f"`length` is one of {', '.join(TASKS)}")
    if not _text(item, "setting"):
        bad("`setting` is a text")
    cand, pat = item.get("candidate"), item.get("patient")
    if not isinstance(cand, dict) or not _text(cand, "role") or not _text(cand, "role_line") \
            or not isinstance(cand.get("tasks"), list) or not all(isinstance(x, str) and x.strip() for x in cand["tasks"]):
        bad("`candidate` is {role, role_line (the card's one sentence: who you are, who you talk to), "
            "background, tasks}")
    if cand.get("background") is not None and not _text(cand, "background"):
        bad("`candidate.background` is a text")
    if not isinstance(pat, dict) or not all(_text(pat, k) for k in ("name", "role", "persona", "emotion", "opening",
                                                                       "concern")):
        bad("`patient` is {name, role, persona, emotion, opening, hidden, concern}, each a text")
    hid = pat.get("hidden")
    if not isinstance(hid, list) or not HIDDEN[0] <= len(hid) <= HIDDEN[1] \
            or not all(isinstance(x, str) and x.strip() for x in hid):
        bad(f"`patient.hidden` is {HIDDEN[0]} to {HIDDEN[1]} facts the patient gives only when asked")
    problems = roleplay_findings(item, item["item_id"])
    if problems:
        bad("; ".join(problems))


# ---------------------------------------------------------------- the lesson player's view

def browser_view(item: dict, audio_rel: dict[str, str] | None) -> dict:
    """What the lesson's own player is given for the pop-up (bundle 1.24): the learner's side of
    the item and the paths of its recordings (`audio_rel`, role -> path from the player; None in
    the silent preview, which has none). A role-play's patient card never reaches the browser
    (RP-SPEAK-ROLEPLAY-HIDDEN). Nothing here marks: this page cannot hear the learner (ADR 054)."""
    t = item["type"]
    v = {"type": t, "item_id": item["item_id"]}
    if t == "speak_repeat":
        v.update({k: item[k] for k in ("focus", "shown", "spoken", "chunks") if k in item})
    elif t == "speak_respond":
        v.update({k: item[k] for k in ("prompt", "patient_line") if k in item})
        v["key_points"] = [c["text"] for c in item["cues"]]
        v.update({k: item[k] for k in ("model_answer", "prepare_s", "max_s") if k in item})
    else:
        v.update({k: item[k] for k in ("title", "setting") if k in item})
        v["candidate"] = {k: item["candidate"][k] for k in ("role", "background", "tasks") if k in item["candidate"]}
        v.update({k: item[k] for k in ("prepare_s", "talk_s") if k in item})
    if audio_rel:
        v["audio"] = {r: audio_rel[r] for r in recordings(item) if r in audio_rel}
    return v
