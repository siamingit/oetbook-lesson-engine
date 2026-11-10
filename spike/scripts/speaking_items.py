"""Speaking practice items (ADR 053): the one place that knows the site's speaking contract.

A Speaking lesson's practice points (analysis/practice.json, ADR 046) may hold items of the
three Speaking Coach types of the site's DRAFT contract (oetacademy-web, branch
feat/speaking-coach-prototype, packages/shared/drafts/speaking, draft of contracts 1.21.0; a
copy in spike/speaking/draft-1.21.0/): speak_repeat, speak_respond and roleplay. The draft is
not released, so everything that depends on its shape is here, behind three functions:

    check(item, where)          the engine's form of an item, and its contract form, are valid
    browser_view(item, audio)   what the lesson's own player is given (bundle 1.24)
    to_contract(item, audio)    the item in the draft contract's shape, for the site

When the contract is released, or changes, this module changes and nothing else. Until then a
lesson with speaking items is never released (RELEASED, checked by publish_lesson.py).

The engine's form of an item (in practice.json) is the contract's item, with these differences:
  item_id   "oa-speaking-NNNNNN", issued by the practice ID registry for skill "speaking";
            the contract's `id` is "oa-speak-NNNNNN", the same number
  audio     never written by hand: synthesize_speaking.py makes the recordings
            (generated/speaking-audio/), and the mapping fills the contract's audio fields
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
RELEASED = False                 # the site's contracts have no speaking items yet (ADR 053)
TYPES = ("speak_repeat", "speak_respond", "roleplay")
SKILL = "speaking"               # the registry's skill: oa-speaking-NNNNNN
ENGINE_ID_RE = re.compile(r"^oa-speaking-([0-9]{6})$")
CONTRACT_PREFIX = "oa-speak-"
SPEAKERS = ("patient_f", "patient_m")
FEELINGS = ("worried", "upset")
# The site's voice names (draft: <accent>-<f|m>-<name>) for the engine's voices (voices.py)
SITE_VOICE = {"rupert": "gb-m-rupert", "gemma": "gb-f-gemma", "archie": "gb-m-archie"}
SLOW_SPEED = 0.75                # the draft: the same voice at about 0.75 of the normal speed

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


# ---------------------------------------------------------------- the contract form

def to_contract(item: dict, audio: dict[str, dict] | None = None) -> dict:
    """The item in the draft contract's shape. `audio`: role -> {path, sha256, bytes, duration_s,
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
    """Refuses an item the engine cannot use or the draft contract would refuse."""
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
    problems = contract_findings(contract_doc([to_contract(item)]))
    if problems:
        bad("the draft contract refuses it: " + "; ".join(problems[:4]))


# ---------------------------------------------------------------- the lesson player's view

def browser_view(item: dict, audio_rel: dict[str, str] | None) -> dict:
    """What the lesson's own player is given for the pop-up (bundle 1.24): the learner's side of
    the item and the paths of its recordings (`audio_rel`, role -> path from the player; None in
    the silent preview, which has none). A role-play's patient card never reaches the browser
    (RP-SPEAK-ROLEPLAY-HIDDEN)."""
    t = item["type"]
    v = {"type": t, "item_id": item["item_id"], "contract_id": contract_id(item["item_id"])}
    if t == "speak_repeat":
        v.update({k: item[k] for k in ("focus", "shown", "chunks", "pass_score")})
    elif t == "speak_respond":
        v.update({k: item[k] for k in ("prompt", "patient_line", "key_points", "model_answer",
                                       "prepare_s", "max_s")})
    else:
        v.update({k: item[k] for k in ("title", "setting", "candidate", "prepare_s", "talk_s")})
    if audio_rel:
        v["audio"] = {r: audio_rel[r] for r in recordings(item) if r in audio_rel}
    return v
