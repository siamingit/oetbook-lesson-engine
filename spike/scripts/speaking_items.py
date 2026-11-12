"""Speaking practice items (ADR 053, ADR 054): the one place that knows the site's speaking contract.

A Speaking lesson's practice points (analysis/practice.json, ADR 046) may hold items of three
Speaking Coach types: speak_repeat, speak_respond and roleplay.

  speak_repeat    RELEASED in contracts 1.22.0 (handout.schema.json $defs/speakRepeatItem): a
                  session's practice point carries it, its two recordings narration files of the
                  package (release_item; publish_lesson.py).
  speak_respond,  still the site's DRAFT (oetacademy-web, packages/shared/drafts/speaking, draft of
  roleplay        contracts 1.21.0; a copy in spike/speaking/draft-1.21.0/): checked against it
                  (to_contract, contract_findings) and played by the lesson's own player only; a
                  draft publish leaves their points out, and a final release refuses them.

    check(item, where)          the engine's form of an item is valid (build time)
    browser_view(item, audio)   what the lesson's own player is given (bundle 1.24)
    release_item(item, n)       a speak_repeat in the released contract's shape (publish)
    to_contract(item, audio)    a draft type in the draft contract's shape

The engine's form of an item (in practice.json):
  item_id   "oa-speaking-NNNNNN", issued by the practice ID registry for skill "speaking"; the
            released item's item_id is the same; the draft's `id` is "oa-speak-NNNNNN"
  audio     never written by hand: synthesize_speaking.py makes the recordings
            (generated/speaking-audio/), and publish fills the contract's audio fields
  speak_repeat    `profession` (the draft's; released, it goes to tags.facets.profession) and
                  `tags` {practises: [taxonomy keys]}, needed to publish; `pass_score` (the
                  draft's) is ignored: the released item has none
  speak_respond   `patient_speaker` patient_f or patient_m (the patient's voice) and, where the
                  card makes the patient worried or upset, `patient_emotion`
  roleplay        `patient_speaker` likewise; the patient card stays server-side
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE.parent / "speaking" / "draft-1.21.0" / "speaking.schema.json"

DRAFT_OF = "1.21.0"
CONTRACT_FORMAT = "oetacademy-speaking-items"
RELEASED_IN = "1.22.0"
RELEASED_TYPES = ("speak_repeat",)   # in the site's contracts (1.22.0); the others are the draft's
TYPES = ("speak_repeat", "speak_respond", "roleplay")
SKILL = "speaking"               # the registry's skill: oa-speaking-NNNNNN
ENGINE_ID_RE = re.compile(r"^oa-speaking-([0-9]{6})$")
CONTRACT_PREFIX = "oa-speak-"
SPEAKERS = ("patient_f", "patient_m")
FEELINGS = ("worried", "upset")
# The site's voice names (draft: <accent>-<f|m>-<name>) for the engine's voices (voices.py)
SITE_VOICE = {"rupert": "gb-m-rupert", "gemma": "gb-f-gemma", "archie": "gb-m-archie"}
SLOW_SPEED = 0.75                # the slow take: 0.75 of the normal speed, every sound kept (1.22.0)
CHUNKS_MAX = 6
# a speak_repeat as practice.json holds it: these fields, nothing else
REPEAT_FIELDS = {"item_id", "type", "profession", "focus", "shown", "spoken", "chunks", "target_sounds",
                 "tags", "pass_score", "version"}

# The recordings each type needs, made by synthesize_speaking.py: role -> (what is said, who)
#   who: "teacher" (Rupert) or "patient" (the item's patient_speaker)
ROLES = {
    "speak_repeat": {"normal": ("spoken", "teacher"), "slow": ("spoken", "teacher")},
    "speak_respond": {"patient": ("patient_line", "patient"), "model": ("model_answer", "teacher")},
    "roleplay": {},
}

ENGINE_ONLY = {"item_id", "patient_speaker", "patient_emotion"}


def is_speaking(item: dict) -> bool:
    return item.get("type") in TYPES


def is_released(item: dict) -> bool:
    """A type the site's contracts carry (speak_repeat, 1.22.0), in either form."""
    return item.get("type") in RELEASED_TYPES


def is_contract_form(item: dict) -> bool:
    """A released item already in the contract's shape (release_item), as a package holds it."""
    return is_released(item) and item.get("scoring") == {"method": "pronunciation"} \
        and isinstance((item.get("audio") or {}).get("normal"), str)


def contract_id(engine_id: str) -> str:
    m = ENGINE_ID_RE.match(engine_id or "")
    if not m:
        raise ValueError(f"{engine_id!r} is not a speaking item id (oa-speaking-NNNNNN)")
    return CONTRACT_PREFIX + m.group(1)


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


# ---------------------------------------------------------------- the released form (1.22.0)

def audio_paths(item_id: str) -> dict[str, str]:
    """The package paths of a speak_repeat's two narration files."""
    m = ENGINE_ID_RE.match(item_id or "")
    if not m:
        raise ValueError(f"{item_id!r} is not a speaking item id (oa-speaking-NNNNNN)")
    return {"normal": f"audio/speak-{m.group(1)}-normal.m4a", "slow": f"audio/speak-{m.group(1)}-slow.m4a"}


def _final_mark_off(s: str) -> str:
    return re.sub(r"[.?!]$", "", s or "")


def repeat_findings(it: dict, where: str) -> list[str]:
    """The rules of a speak_repeat the schema cannot say (RP-SPEAK-CHUNKS, -NUMBERS, -AUDIO), and the
    engine's own RP-SHOWN, on either form of the item."""
    out = []
    spoken = it.get("spoken") or ""
    if " ".join(it.get("chunks") or []) != _final_mark_off(spoken):
        out.append(f"{where}: RP-SPEAK-CHUNKS: the chunks joined with single spaces are not `spoken` "
                   "without its final . ? or !")
    if re.search(r"[0-9]", spoken):
        out.append(f"{where}: RP-SPEAK-NUMBERS: `spoken` has a digit; write numbers as they are said")
    if _final_mark_off(it.get("shown") or "").lower() != _final_mark_off(spoken).lower():
        out.append(f"{where}: RP-SHOWN: `shown` is not `spoken` (ignoring case and the final mark): the "
                   "learner says what they read")
    a = it.get("audio")
    if isinstance(a, dict) and a.get("normal") == a.get("slow"):
        out.append(f"{where}: RP-SPEAK-AUDIO: normal and slow are the same file")
    return out


def release_item(item: dict, number: int = 1, version: int = 1) -> dict:
    """A speak_repeat in the released contract's shape (handout $defs/speakRepeatItem), hashed: no
    pass_score and no profession (the profession goes to tags.facets.profession, admin-only)."""
    import practice_points as pp
    where = item.get("item_id")
    if not is_released(item):
        raise SystemExit(f"REFUSED: speaking item {where}: {item.get('type')!r} is not in the site's "
                         f"contracts ({', '.join(RELEASED_TYPES)} only, {RELEASED_IN})")
    tags = json.loads(json.dumps(item.get("tags") or {}))
    if not tags.get("practises"):
        raise SystemExit(f"REFUSED: speaking item {where}: no tags.practises; write the taxonomy keys it "
                         "practises in analysis/practice.json (for example speaking.language.intelligibility)")
    if item.get("profession"):
        profs = tags.setdefault("facets", {}).setdefault("profession", [])
        if item["profession"] not in profs:
            profs.append(item["profession"])
    c = {"item_id": item["item_id"], "type": "speak_repeat", "number": number}
    if item.get("focus"):
        c["focus"] = item["focus"]
    c.update({"shown": item["shown"], "spoken": item["spoken"], "chunks": list(item["chunks"])})
    if item.get("target_sounds"):
        c["target_sounds"] = list(item["target_sounds"])
    c.update({"audio": audio_paths(item["item_id"]), "scoring": {"method": "pronunciation"},
              "tags": tags, "version": version, "status": "active"})
    problems = repeat_findings(c, c["item_id"])
    if problems:
        raise SystemExit("REFUSED: " + "; ".join(problems))
    return pp.hashed(c)


# ---------------------------------------------------------------- the contract form

def to_contract(item: dict, audio: dict[str, dict] | None = None) -> dict:
    """A draft type's item (speak_respond, roleplay) in the draft contract's shape. `audio`: role -> {path, sha256, bytes, duration_s,
    voice} for the package's mp3 files; without it (a check before any recording is made) each
    file is a placeholder of the right shape, so the schema's other rules are still checked."""
    t = item["type"]
    c = {k: v for k, v in item.items() if k not in ENGINE_ONLY}
    c = {"type": t, "id": contract_id(item["item_id"]), **{k: v for k, v in c.items() if k != "type"}}

    def file(role: str, who: str) -> dict:
        if audio and role in audio:
            a = audio[role]
            return {"path": a["path"], "media_type": "audio/mpeg", "sha256": a["sha256"],
                    "bytes": a["bytes"], "duration_s": a["duration_s"], "voice": a["voice"]}
        return {"path": f"audio/speaking/{c['id']}.{role}.mp3", "media_type": "audio/mpeg",
                "sha256": "0" * 64, "bytes": 1, "duration_s": 1.0 if role != "slow" else 1.5,
                "voice": site_voice(who)}

    if t == "speak_repeat":
        c["audio"] = {"normal": file("normal", "teacher"), "slow": file("slow", "teacher")}
    elif t == "speak_respond":
        c["patient_voice"] = site_voice(item["patient_speaker"])
        c["patient_audio"] = file("patient", item["patient_speaker"])
    elif t == "roleplay":
        c["patient"] = {**c["patient"], "voice": site_voice(item["patient_speaker"])}
    return c


def site_voice(who: str) -> str:
    import voices
    v = voices.voice_for(None if who == "teacher" else who, voices.RUPERT)
    return SITE_VOICE[v["name"]]


def contract_doc(items: list[dict]) -> dict:
    return {"format": CONTRACT_FORMAT, "draft_of": DRAFT_OF, "items": items}


def contract_findings(doc: dict) -> list[str]:
    """The draft schema, and the rules it cannot say (RP-SPEAK-*), on a contract document."""
    import jsonschema
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    out = [f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}"
           for e in jsonschema.Draft202012Validator(schema).iter_errors(doc)]
    for n, it in enumerate(doc.get("items") or []):
        where = it.get("id", f"items/{n}")
        if it.get("type") == "speak_repeat":
            spoken = it.get("spoken", "")
            if " ".join(it.get("chunks") or []) != re.sub(r"[.?!]$", "", spoken):
                out.append(f"{where}: RP-SPEAK-CHUNKS: the chunks joined with spaces are not "
                           "`spoken` without its final . ? or !")
            if re.search(r"[0-9]", spoken):
                out.append(f"{where}: RP-SPEAK-NUMBERS: `spoken` has a digit; write numbers as they are said")
            a = it.get("audio") or {}
            nrm, slw = a.get("normal") or {}, a.get("slow") or {}
            if nrm.get("path") == slw.get("path") or nrm.get("voice") != slw.get("voice") \
                    or not (slw.get("duration_s", 0) > nrm.get("duration_s", 0)):
                out.append(f"{where}: RP-SPEAK-AUDIO: normal and slow must be different files in one "
                           "voice, the slow one longer")
    return out


# ---------------------------------------------------------------- the engine's check

def check(item: dict, where: str) -> None:
    """Refuses an item the engine cannot use, or its contract would refuse: the released rules for a
    speak_repeat (the schema itself is checked at publish), the draft for the other types."""
    def bad(msg):
        raise SystemExit(f"REFUSED: speaking item {where}: {msg}")
    t = item.get("type")
    if t not in TYPES:
        bad(f"type {t!r}: one of {', '.join(TYPES)}")
    if not ENGINE_ID_RE.match(item.get("item_id") or ""):
        bad(f"item_id {item.get('item_id')!r}: oa-speaking-NNNNNN, issued by the registry")
    if t in ("speak_respond", "roleplay"):
        if item.get("patient_speaker") not in SPEAKERS:
            bad(f"patient_speaker {item.get('patient_speaker')!r}: one of {', '.join(SPEAKERS)}")
    if item.get("patient_emotion") is not None:
        if t != "speak_respond" or item["patient_emotion"] not in FEELINGS:
            bad(f"patient_emotion {item['patient_emotion']!r}: on a speak_respond only, one of "
                f"{', '.join(FEELINGS)}")
    if t == "speak_respond" and not item.get("model_answer"):
        bad("a speak_respond needs its model_answer: the lesson shows a model (ADR 053)")
    if "audio" in item or "patient_audio" in item or "id" in item:
        bad("audio and the contract id are made by the engine, never written in practice.json")
    if t == "speak_repeat":
        _check_repeat(item, bad)
        return
    problems = contract_findings(contract_doc([to_contract(item)]))
    if problems:
        bad("the draft contract refuses it: " + "; ".join(problems[:4]))


def _check_repeat(item: dict, bad) -> None:
    extra = set(item) - REPEAT_FIELDS
    if extra:
        bad(f"fields a speak_repeat does not have: {', '.join(sorted(extra))}")
    for k in ("shown", "spoken"):
        if not isinstance(item.get(k), str) or not item[k].strip():
            bad(f"`{k}` is a sentence")
    ch = item.get("chunks")
    if not isinstance(ch, list) or not 1 <= len(ch) <= CHUNKS_MAX \
            or not all(isinstance(c, str) and c.strip() for c in ch):
        bad(f"`chunks` is 1 to {CHUNKS_MAX} sense groups")
    ts = item.get("target_sounds")
    if ts is not None and (not isinstance(ts, list) or len(set(ts)) != len(ts)
                           or not all(isinstance(x, str) and 1 <= len(x) <= 4 for x in ts)):
        bad("`target_sounds` is a list of distinct IPA phonemes, 1 to 4 characters each")
    tags = item.get("tags")
    if tags is not None and (not isinstance(tags, dict) or not tags.get("practises")):
        bad("`tags` has `practises`: taxonomy keys")
    problems = repeat_findings(item, item["item_id"])
    if problems:
        bad("; ".join(problems))


# ---------------------------------------------------------------- the lesson player's view

def browser_view(item: dict, audio_rel: dict[str, str] | None) -> dict:
    """What the lesson's own player is given for the pop-up (bundle 1.24): the learner's side of
    the item and the paths of its recordings (`audio_rel`, role -> path from the player; None in
    the silent preview, which has none). A role-play's patient card never reaches the browser
    (RP-SPEAK-ROLEPLAY-HIDDEN). Nothing here marks: the pop-up shows the model (ADR 054)."""
    t = item["type"]
    v = {"type": t, "item_id": item["item_id"]}
    if t != "speak_repeat":
        v["contract_id"] = contract_id(item["item_id"])
    if t == "speak_repeat":
        v.update({k: item[k] for k in ("focus", "shown", "spoken", "chunks") if k in item})
    elif t == "speak_respond":
        v.update({k: item[k] for k in ("prompt", "patient_line", "key_points", "model_answer",
                                       "prepare_s", "max_s")})
    else:
        v.update({k: item[k] for k in ("title", "setting", "candidate", "prepare_s", "talk_s")})
    if audio_rel:
        v["audio"] = {r: audio_rel[r] for r in recordings(item) if r in audio_rel}
    return v
