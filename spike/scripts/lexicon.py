"""The pronunciation lexicon: one versioned file, synced to Cartesia, applied
by every synthesis script, and checked before any synthesis runs.

    .venv/Scripts/python spike/scripts/lexicon.py --show     what the file and Cartesia hold
    .venv/Scripts/python spike/scripts/lexicon.py --sync     push the file's entries to Cartesia
    .venv/Scripts/python spike/scripts/lexicon.py --verify   fail unless Cartesia matches the file

The file is spike/lexicon.json (methodology §20). Cartesia is never the source:
a dictionary edited there is overwritten by the next --sync, and a synthesis
script refuses to run while the two differ, so an entry cannot quietly be
missing from a build.

Three things the module gives a synthesis script:
  require_synced(client)   raises unless Cartesia's dictionary equals the file
  terms_in(text)           the lexicon terms an utterance contains
  cache_salt(text)         those terms with their aliases, for the audio cache
                           key: changing a pronunciation re-synthesises exactly
                           the utterances that contain the term
and one for the phoneme check: expect/reject phoneme patterns per term, so a
build can confirm from Cartesia's own phoneme timestamps that an alias took
effect (that is the discriminating test for a vowel; Scribe, the ear, is the
coarse one).
"""

import json
import re
import sys
from pathlib import Path

LEXICON_PATH = Path(__file__).resolve().parents[1] / "lexicon.json"


def load() -> dict:
    return json.loads(LEXICON_PATH.read_text(encoding="utf-8"))


def save(lex: dict) -> None:
    LEXICON_PATH.write_text(json.dumps(lex, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")


def items(lex: dict) -> list[dict]:
    """The Cartesia item list the file describes. Case-insensitive: the term
    must be said the same way at a sentence start. An entry of kind `default`
    is approved as the voice's own rendering and sends nothing."""
    return [{"text": term, "alias": e["alias"], "case_sensitive": False}
            for term, e in sorted(lex["entries"].items())
            if e.get("kind", "alias") != "default"]


def terms_in(text: str, lex: dict | None = None) -> list[str]:
    """Lexicon terms the text contains, matched without regard to case: the
    file may spell an initialism 'OET' while the check lower-cases words."""
    lex = lex or load()
    low = text.lower()
    return [t for t in sorted(lex["entries"])
            if re.search(r"\b" + re.escape(t.lower()) + r"\b", low)]


def has_term(word: str, lex: dict) -> bool:
    return word.lower() in {t.lower() for t in lex["entries"]}


def cache_salt(text: str, lex: dict | None = None) -> str:
    """The pronunciation decisions an utterance depends on. A default entry
    salts as 'default', so switching a term from an alias to the voice's own
    rendering re-synthesises exactly the utterances that contain it."""
    lex = lex or load()
    return "|".join(f"{t}={lex['entries'][t]['alias'] if lex['entries'][t].get('kind', 'alias') != 'default' else 'default'}"
                    for t in terms_in(text, lex))


def remote_items(client, dict_id: str) -> list[dict]:
    d = client.pronunciation_dicts.retrieve(dict_id)
    out = []
    for it in d.items:
        m = it.model_dump()
        # The API returns the alias under `pronunciation`; the SDK's `alias` is
        # the same field on the way in. Compare on what was said, not the name.
        out.append({"text": m.get("text"), "alias": m.get("alias") or m.get("pronunciation"),
                    "case_sensitive": bool(m.get("case_sensitive"))})
    return sorted(out, key=lambda x: x["text"])


def diff(lex: dict, client) -> list[str]:
    want = items(lex)
    have = remote_items(client, lex["cartesia"]["dict_id"])
    problems = []
    hmap = {h["text"]: h for h in have}
    for w in want:
        h = hmap.get(w["text"])
        if not h:
            problems.append(f"{w['text']!r} is in the file but not on Cartesia")
        elif h["alias"] != w["alias"]:
            problems.append(f"{w['text']!r}: file says {w['alias']!r}, Cartesia says {h['alias']!r}")
        elif h["case_sensitive"] != w["case_sensitive"]:
            problems.append(f"{w['text']!r}: case_sensitive differs")
    for h in have:
        if h["text"] not in lex["entries"]:
            problems.append(f"{h['text']!r} is on Cartesia but not in the file")
    return problems


def require_synced(client, lex: dict | None = None) -> dict:
    """Every synthesis script calls this first. A build never runs against a
    dictionary that differs from the file."""
    lex = lex or load()
    problems = diff(lex, client)
    if problems:
        raise SystemExit("REFUSED: the Cartesia pronunciation dictionary does not match "
                         "spike/lexicon.json:\n  " + "\n  ".join(problems)
                         + "\nRun: .venv/Scripts/python spike/scripts/lexicon.py --sync")
    return lex


def sync(client, lex: dict) -> None:
    cid = lex["cartesia"].get("dict_id")
    name = lex["cartesia"].get("name", "oetbook-lexicon")
    if cid:
        client.pronunciation_dicts.update(cid, items=items(lex), name=name)
    else:
        d = client.pronunciation_dicts.create(name=name, items=items(lex))
        lex["cartesia"]["dict_id"] = d.id
        save(lex)
    problems = diff(lex, client)
    if problems:
        raise SystemExit("sync did not take:\n  " + "\n  ".join(problems))


def unapproved_in(text: str, lex: dict | None = None) -> list[str]:
    """Lexicon terms in the text the maintainer has not approved by ear.
    A build never uses one (methodology §20)."""
    lex = lex or load()
    return [t for t in terms_in(text, lex) if not lex["entries"][t].get("approved")]


def approve(lex: dict, term: str, by: str, on: str) -> None:
    key = next((t for t in lex["entries"] if t.lower() == term.lower()), None)
    if not key:
        raise SystemExit(f"{term!r} is not in the lexicon")
    lex["entries"][key].update(approved=True, approved_by=by, approved_on=on)
    save(lex)


def reject(lex: dict, term: str, why: str) -> None:
    key = next((t for t in lex["entries"] if t.lower() == term.lower()), None)
    if not key:
        raise SystemExit(f"{term!r} is not in the lexicon")
    lex["entries"][key].update(approved=False, approved_by=None, approved_on=None,
                               rejected=why)
    save(lex)


def phoneme_check(term: str, phonemes: str, lex: dict) -> str | None:
    """None if the phoneme string shows the alias took effect, else why not."""
    e = lex["entries"][term]
    if e.get("reject_phonemes") and e["reject_phonemes"] in phonemes:
        return f"{term}: heard the rejected pattern {e['reject_phonemes']!r}"
    if e.get("expect_phonemes") and e["expect_phonemes"] not in phonemes:
        return f"{term}: expected pattern {e['expect_phonemes']!r} not found"
    return None


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from synthesize_audio import api_key
    from cartesia import Cartesia
    client = Cartesia(api_key=api_key())
    lex = load()
    if "--approve" in sys.argv:
        import datetime
        term = sys.argv[sys.argv.index("--approve") + 1]
        by = sys.argv[sys.argv.index("--by") + 1] if "--by" in sys.argv else "maintainer"
        approve(lex, term, by, datetime.date.today().isoformat())
        print(f"approved {term!r} by {by}")
        return
    if "--reject" in sys.argv:
        term = sys.argv[sys.argv.index("--reject") + 1]
        why = sys.argv[sys.argv.index("--why") + 1] if "--why" in sys.argv else ""
        reject(lex, term, why)
        print(f"rejected {term!r}: {why}")
        return
    if "--sync" in sys.argv:
        sync(client, lex)
        print(f"synced {len(lex['entries'])} entries to {lex['cartesia']['dict_id']}")
    elif "--verify" in sys.argv:
        require_synced(client, lex)
        print("Cartesia matches spike/lexicon.json")
    else:
        print("file:", json.dumps(items(lex), ensure_ascii=False))
        print("cartesia:", json.dumps(remote_items(client, lex["cartesia"]["dict_id"]),
                                      ensure_ascii=False))
        for p in diff(lex, client):
            print("DIFF:", p)


if __name__ == "__main__":
    main()
