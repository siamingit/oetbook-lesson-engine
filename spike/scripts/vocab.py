"""The vocabulary layer of a Reading Part B or C lesson (docs/adr/026-reading-lessons.md
§2; bundle 1.15).

    .venv/Scripts/python spike/scripts/vocab.py <lesson_dir> --sync
    .venv/Scripts/python spike/scripts/vocab.py <lesson_dir> --briefs FILE
    .venv/Scripts/python spike/scripts/vocab.py <lesson_dir> --check

The only source of words, meanings, synonyms, examples and pronunciation audio
is the exercises repository's word bank (`vocab/lexicon.json`, with
`vocab/occurrences/<set>.json`; its `docs/vocab/README.md`), read-only. The
engine writes no definition of its own: a missing field is an issue in the
exercises repository, never filled here.

Words are named by their `lx:` IDs, which are provisional (oetacademy-web#51).
So the engine keeps ONE mapping file, `<library>/course/vocab-ids.json`
(outside the repository, like the course index): each word has a stable
engine key (`w:` and the ID it was first seen with), its current `lx:` ID,
the IDs it had before, and the engine's own image brief for its gloss
picture. Lesson data stores the engine key; the `lx:` ID written in a bundle
is read from the file. When the IDs change, the file is updated
(`--sync` keeps keys and records the old IDs) and the lessons are rebuilt
from it with no model call.

`--sync` adds every word of the lesson's practice set to the file;
`--briefs FILE` sets image briefs ({"<lx: ID or key>": "alt | what to draw"});
`--check` fails when a word of the set has no meaning, synonym, example,
audio file or image brief.
"""

import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import practice_set                                              # noqa: E402

EXERCISES = Path(os.environ.get("OETACADEMY_EXERCISES",
                                str(Path.home() / "projects" / "oetacademy-exercises")))
AUDIO_TOKEN = "@@vocab-audio@@"          # resolved per page, like the gloss images
AUDIO_DIR = "vocab-audio"                # <lesson>/generated/vocab-audio/


def ids_path(lesson: Path) -> Path:
    from build_course_index import course_dir
    return course_dir(Path(lesson)) / "vocab-ids.json"


def bank() -> tuple[dict, dict]:
    """The lexicon entries by ID, and the lexicon's audio block."""
    lx = json.loads((EXERCISES / "vocab" / "lexicon.json").read_text(encoding="utf-8"))
    return {e["id"]: e for e in lx["entries"]}, lx.get("audio") or {}


def occurrences(set_id: str) -> list[dict]:
    p = EXERCISES / "vocab" / "occurrences" / f"{set_id}.json"
    return json.loads(p.read_text(encoding="utf-8"))["occurrences"] if p.exists() else []


def load_ids(lesson: Path) -> dict:
    p = ids_path(lesson)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"format": "oetbook-vocab-ids", "adr": "026",
            "purpose": "The one mapping from the engine's word keys to the word bank's lx: IDs "
                       "(provisional, oetacademy-web#51), with the engine's image brief for each "
                       "word's gloss picture. Lesson data stores the key; a bundle's lx: ID is read "
                       "from here. Never in git.",
            "id_status": "provisional - pending site decision (oetacademy-web#51)",
            "words": {}}


def save_ids(lesson: Path, data: dict) -> None:
    p = ids_path(lesson)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def key_of(lesson: Path, ref: str) -> str | None:
    """The engine key for an lx: ID (current or earlier) or a key."""
    words = load_ids(lesson)["words"]
    ref = (ref or "").strip()
    if ref in words:
        return ref
    for k, w in words.items():
        if ref == w["lexicon_id"] or ref in (w.get("previous_ids") or []):
            return k
    return None


def lexicon_id(lesson: Path, key: str) -> str | None:
    w = load_ids(lesson)["words"].get(key)
    return w["lexicon_id"] if w else None


def set_id(lesson: Path) -> str | None:
    ps = practice_set.load(lesson)
    return ps["set_id"] if ps else None


def sync(lesson: Path) -> dict:
    """Add every word the lesson's set uses to the mapping file; keep every
    key, brief and earlier ID."""
    sid = set_id(lesson)
    if not sid:
        raise SystemExit("no practice set in this lesson")
    lex, _ = bank()
    data = load_ids(lesson)
    added = 0
    for o in occurrences(sid):
        lid = o["lexicon_id"]
        if key_of(lesson, lid) or any(w["lexicon_id"] == lid for w in data["words"].values()):
            continue
        e = lex[lid]
        data["words"]["w:" + lid.removeprefix("lx:")] = {
            "lexicon_id": lid, "previous_ids": [], "headword": e["headword"],
            "part_of_speech": e["part_of_speech"], "image_brief": None,
            "first_set": sid}
        added += 1
        save_ids(lesson, data)
    save_ids(lesson, data)
    return {"added": added, "words": len(data["words"])}


def entry(lesson: Path, key: str) -> dict:
    lid = lexicon_id(lesson, key)
    if not lid:
        raise KeyError(f"{key}: not in {ids_path(lesson)}")
    lex, _ = bank()
    if lid not in lex:
        raise KeyError(f"{key}: {lid} is not in the word bank")
    return lex[lid]


def set_words(lesson: Path) -> dict[str, list[dict]]:
    """The set's words by text id (t1...), in the order they first occur:
    [{key, lexicon_id, headword, where: [...]}]."""
    sid = set_id(lesson)
    out: dict[str, list[dict]] = {}
    for o in occurrences(sid or ""):
        k = key_of(lesson, o["lexicon_id"])
        loc = o["location"]
        where = ("text" if loc["kind"] == "text" else
                 "question" if loc["kind"] == "stem" else f"option {loc.get('option')}")
        words = out.setdefault(o["text_id"], [])
        w = next((x for x in words if x["key"] == k), None)
        if not w:
            w = {"key": k, "lexicon_id": o["lexicon_id"], "where": []}
            words.append(w)
        w["where"].append({"in": where, "surface": o["surface"]})
    return out


def text_of(lesson: Path, text_id: str) -> str:
    """A set text's stimulus ID from its local id (t1 -> oa-set-rb-0001-t1)."""
    return f"{set_id(lesson)}-{text_id}"


def words_for_prompt(lesson: Path) -> str:
    """The set's words for the screens stage, by text, with the word bank's
    meaning and synonym so the model can teach them; never to be copied into
    a block: code builds every word block from its ID."""
    lex, _ = bank()
    lines = []
    for tid, words in set_words(lesson).items():
        lines.append(f"WORDS OF {text_of(lesson, tid)} (pre-teach them, gloss them where they "
                     "occur, recap them):")
        for w in words:
            e = lex[w["lexicon_id"]]
            seen = "; ".join(f"{x['in']}: '{x['surface']}'" for x in w["where"])
            lines.append(f"  {w['lexicon_id']} = {e['headword']} ({e['part_of_speech']}): "
                         f"{e['definition']} | synonym: {(e.get('synonyms') or ['-'])[0]} | {seen}")
    return "\n".join(lines)


def words_for_prompt_part_c(lesson: Path, text_ids: list[str] | None = None) -> str:
    """A Part C set's words for the screens stage (bundle 1.17), by the question
    whose pre-teaching board teaches each (question_words), with every place the
    word occurs, so it is glossed again there; never to be copied into a block."""
    lex, _ = bank()
    ps = practice_set.load(lesson)
    items = practice_set.items(ps)
    where: dict[tuple[str, str], list[str]] = {}
    for o in occurrences(set_id(lesson) or ""):
        loc = o["location"]
        at = (f"text paragraph {loc['paragraph']}" if loc["kind"] == "text" else
              "the question" if loc["kind"] == "stem" else f"option {loc.get('option')}")
        if loc["kind"] != "text":
            at += f" of question {practice_set.number(ps, items[loc['item_id']])}"
        where.setdefault((o["text_id"], o["lexicon_id"]), []).append(f"{at}: '{o['surface']}'")
    lines = []
    for item, keys in question_words(lesson).items():
        it = items[item]
        tid = it["stimulus_ids"][0].rsplit("-", 1)[-1]
        if text_ids and tid not in text_ids:
            continue
        lines.append(f"WORDS FOR QUESTION {practice_set.number(ps, it)} ({item}; its text {it['stimulus_ids'][0]}), "
                     "pre-taught on that question's PRE-TEACHING board, in this order:"
                     + ("" if keys else " none (no pre-teaching board for this question)"))
        for k in keys:
            lid = lexicon_id(lesson, k)
            e = lex[lid]
            lines.append(f"  {lid} = {e['headword']} ({e['part_of_speech']}): {e['definition']} | synonym: "
                         f"{(e.get('synonyms') or ['-'])[0]} | occurs in "
                         + "; ".join(where.get((tid, lid), [])))
    return "\n".join(lines)


def audio_file(e: dict) -> str | None:
    a = e.get("audio") or {}
    return Path(a["file"]).name if a.get("file") else None


def gloss_block(lesson: Path, key: str) -> dict:
    """A word-bank gloss (bundle 1.15): the word, its meaning, a synonym and its
    example from the word bank, the engine's image brief, its lx: ID and its
    pronunciation clip. Built by code from the ID; never written by the model."""
    e = entry(lesson, key)
    w = load_ids(lesson)["words"][key]
    a = e.get("audio") or {}
    return {"type": "gloss", "term": e["headword"], "explanation": e["definition"],
            "synonym": (e.get("synonyms") or [None])[0], "text": e["example"],
            "icon": w.get("image_brief"), "vocab": key,
            "audio": ({"file": audio_file(e), "seconds": a.get("seconds")} if audio_file(e) else None),
            "provenance": "source-derived",
            "note": f"word bank {w['lexicon_id']} (oetacademy-exercises vocab/lexicon.json): meaning, "
                    "synonym and example as the bank gives them; built by code (ADR 026 §2)"}


def match_block(lesson: Path, keys: list[str]) -> dict:
    """The instructor's word-to-meaning matching table (format c): the words in
    the order given, their meanings from the word bank in another order (each
    moved one place on), so the learner matches them."""
    es = [entry(lesson, k) for k in keys]
    meanings = [e["definition"] for e in es]
    if len(meanings) > 1:
        meanings = meanings[1:] + meanings[:1]
    return {"type": "table", "header": ["Word", "Meaning"],
            "rows": [[f"{e['headword']} ({e['part_of_speech']})", m] for e, m in zip(es, meanings)],
            "vocab_table": {"kind": "match", "words": keys},
            "provenance": "source-derived",
            "note": "word-to-meaning matching (the instructor's format c), built by code from the "
                    "word bank: " + ", ".join(lexicon_id(lesson, k) for k in keys)}


def recap_block(lesson: Path, keys: list[str]) -> dict:
    """The word-recap board's table: each word of the text, its meaning and a
    synonym, from the word bank."""
    es = [entry(lesson, k) for k in keys]
    return {"type": "table", "header": ["Word", "Meaning", "Synonym"],
            "rows": [[e["headword"], e["definition"], (e.get("synonyms") or [""])[0]] for e in es],
            "vocab_table": {"kind": "recap", "words": keys},
            "provenance": "source-derived",
            "note": "word recap, built by code from the word bank: "
                    + ", ".join(lexicon_id(lesson, k) for k in keys)}


def question_words(lesson: Path) -> dict[str, list[str]]:
    """A Part C text's words by the question whose pre-teaching board teaches
    them (ADR 026, Part C; bundle 1.17), each word once a text, at its first
    occurrence: a word of a paragraph goes to the paragraph's question; where
    two questions share the paragraph, to the later one when the word is in
    that question's evidence; a word of a stem or an option to its question.
    {item id: [key, ...]}, the items in number order."""
    ps = practice_set.load(lesson) or {"parts": []}
    items = practice_set.items(ps)
    out: dict[str, list[str]] = {i: [] for i in sorted(items, key=lambda i: items[i]["number"])}
    seen: dict[str, set] = {}
    for o in occurrences(set_id(lesson) or ""):
        loc = o["location"]
        if loc["kind"] == "text":
            ids = loc.get("paragraph_item_ids") or []
            later = [i for i in ids[1:] if o["surface"].lower() in (items[i].get("evidence") or "").lower()]
            item = later[-1] if later else ids[0]
        else:
            item = loc["item_id"]
        k = key_of(lesson, o["lexicon_id"])
        got = seen.setdefault(o["text_id"], set())
        if k in got:
            continue
        got.add(k)
        out.setdefault(item, []).append(k)
    return out


def recap_grouped_block(lesson: Path, groups: list[tuple[int, list[str]]]) -> dict:
    """A long text's word recap (Part C, bundle 1.17): one row per question,
    its words each with a synonym from the word bank, so the forty to fifty
    words of a Part C text stay whole on one board. `groups` is [(question
    number, [key, ...]), ...]."""
    rows, words = [], []
    for n, keys in groups:
        es = [entry(lesson, k) for k in keys]
        rows.append([str(n), "; ".join(f"{e['headword']} ({(e.get('synonyms') or [''])[0]})" for e in es)])
        words += keys
    return {"type": "table", "header": ["Question", "Words (a synonym)"], "rows": rows,
            "vocab_table": {"kind": "recap_grouped", "words": words,
                            "groups": [[n, list(keys)] for n, keys in groups]},
            "provenance": "source-derived",
            "note": "word recap by question, built by code from the word bank: "
                    + ", ".join(lexicon_id(lesson, k) for k in words)}


def recap_groups_for_text(lesson: Path, text_id: str) -> list[tuple[int, list[str]]]:
    """A Part C text's words grouped by question number (question_words),
    the number the question carries in this lesson (practice_set.number)."""
    ps = practice_set.load(lesson)
    items = practice_set.items(ps)
    return [(practice_set.number(ps, items[i]), keys) for i, keys in question_words(lesson).items()
            if keys and items[i]["stimulus_ids"][0].rsplit("-", 1)[-1] == text_id]


def keys_from_label(lesson: Path, label: str) -> tuple[list[str], list[str]]:
    """The keys an "MATCH lx:a, lx:b" or "RECAP ..." label names, and the
    references it names that are not in the mapping."""
    refs = [x.strip() for x in label.split(None, 1)[1].replace(",", " ").split()] if " " in label else []
    keys, bad = [], []
    for r in refs:
        k = key_of(lesson, r)
        (keys if k else bad).append(k or r)
    return keys, bad


def copy_audio(lesson: Path) -> int:
    """Copy the pronunciation clips of the set's words into the lesson
    (generated/vocab-audio/); the word bank's audio lives outside its repo."""
    lex, audio = bank()
    root = Path(audio.get("root") or "")
    out = Path(lesson) / "generated" / AUDIO_DIR
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for words in set_words(lesson).values():
        for w in words:
            e = lex[w["lexicon_id"]]
            a = e.get("audio") or {}
            if not a.get("file"):
                continue
            src = root / a["file"]
            dst = out / Path(a["file"]).name
            if src.exists() and (not dst.exists() or dst.stat().st_size != src.stat().st_size):
                shutil.copy2(src, dst)
                n += 1
    return n


def check(lesson: Path) -> list[str]:
    lex, audio = bank()
    root = Path(audio.get("root") or "")
    ids = load_ids(lesson)["words"]
    bad = []
    for words in set_words(lesson).values():
        for w in words:
            if not w["key"]:
                bad.append(f"{w['lexicon_id']}: not in {ids_path(lesson)} (run --sync)")
                continue
            e = lex.get(w["lexicon_id"]) or {}
            for f in ("definition", "example"):
                if not (e.get(f) or "").strip():
                    bad.append(f"{w['lexicon_id']}: no {f} in the word bank (an issue for the exercises repo)")
            if not e.get("synonyms"):
                bad.append(f"{w['lexicon_id']}: no synonym in the word bank (an issue for the exercises repo)")
            a = e.get("audio") or {}
            if not a.get("file") or not (root / a["file"]).exists():
                bad.append(f"{w['lexicon_id']}: no pronunciation audio file")
            if not (ids[w["key"]].get("image_brief") or "").strip():
                bad.append(f"{w['lexicon_id']}: no image brief in {ids_path(lesson)}")
    return sorted(set(bad))


def main() -> None:
    lesson = Path(sys.argv[1])
    if "--sync" in sys.argv:
        print(sync(lesson))
    if "--briefs" in sys.argv:
        briefs = json.loads(Path(sys.argv[sys.argv.index("--briefs") + 1]).read_text(encoding="utf-8"))
        data = load_ids(lesson)
        for ref, brief in briefs.items():
            k = key_of(lesson, ref)
            if not k:
                raise SystemExit(f"{ref}: not in the mapping")
            data["words"][k]["image_brief"] = brief
        save_ids(lesson, data)
        print(f"{len(briefs)} image briefs set in {ids_path(lesson)}")
    if "--copy-audio" in sys.argv:
        print(f"{copy_audio(lesson)} clips copied")
    bad = check(lesson)
    for b in bad:
        print("MISSING: " + b)
    if bad:
        raise SystemExit(f"{len(bad)} gap(s) in the vocabulary layer")
    print(f"vocabulary layer complete: {sum(len(w) for w in set_words(lesson).values())} words in "
          f"{len(set_words(lesson))} texts")


if __name__ == "__main__":
    main()
