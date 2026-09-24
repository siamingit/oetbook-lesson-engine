"""Find a page's clinical and uncommon terms, and hear every one that is not
in the lexicon before the page is synthesised.

    .venv/Scripts/python spike/scripts/check_terms.py <lesson_dir> --page 13

Reads:  <lesson_dir>/analysis/narration/page-<N>/narration.json
        <lesson_dir>/analysis/screens/page-<N>/screens.json
        <lesson_dir>/analysis/keyterms.json            (the lesson's curated terms)
        spike/lexicon.json
Writes: <lesson_dir>/generated/page-<N>/boards/terms_check.json

Candidates: the lesson's curated keyterms, plus any word of nine or more
letters, plus any word with a clinical ending (-itis, -osis, -ectomy, -aemia,
-pathy, -ology, -plasty, -scopy, -algia, -oma), minus the lexicon. Each is
synthesised alone in a carrier sentence and transcribed by Scribe; a term the
ear does not hear back is listed as a failure, for the maintainer to add to
the lexicon before the lesson is built. synthesize_narration.py refuses to
run without a fresh terms check that has no failures, unless told to accept
them.

The heuristic over-collects ordinary long words; that costs a few characters
of synthesis each and nothing else.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lexicon                                                          # noqa: E402
import paths                                                            # noqa: E402
from ear import norm, transcribe_file                                    # noqa: E402
from synthesize_audio import MODEL_ID, VOICE_ID, api_key as cartesia_key, synthesize, write_wav  # noqa: E402
from transcribe import api_key as scribe_key                            # noqa: E402
from write_narration import spoken                                      # noqa: E402
from write_screens import block_text_runs                               # noqa: E402

CLINICAL_ENDING = re.compile(r"(itis|osis|ectomy|aemia|emia|pathy|ology|plasty|scopy|algia|oma)$")
MIN_LETTERS = 9
CARRIER = "The word is {term}."
STOP = set("""sentence sentences correction corrected correctly condition conditions continuous
continues continue something different remember important explanation instruction
instructions understand questions everything grammar underline underlined highlight
highlighted following happening beginning something anything everything yourself
themselves ourselves certainly carefully possessing diagnosed diagnoses diagnosing
cigarettes yesterday tomorrow according therefore otherwise whenever wherever
sometimes exercise exercises practise practice practising introduce introduced
introduction difference differently""".split())


def candidates(lesson: Path, page: int, lex: dict) -> list[str]:
    texts = []
    pages = page if isinstance(page, list) else [page]
    narr = json.loads((paths.narration_dir_for(lesson, pages) / "narration.json").read_text(encoding="utf-8"))
    for bd in narr["boards"]:
        for s in bd["states"]:
            for u in s["utterances"]:
                texts.append(spoken(u["text_with_cues"]))
    scr = json.loads((paths.screens_dir_for(lesson, pages) / "screens.json").read_text(encoding="utf-8"))
    for t in scr["topics"]:
        for h in t["thoughts"]:
            for b in h["blocks"]:
                texts += block_text_runs(b)
    words = set()
    for text in texts:
        for w in re.findall(r"[A-Za-z][A-Za-z'-]+", text):
            n = w.lower().strip("'-")
            if (len(n) >= MIN_LETTERS or CLINICAL_ENDING.search(n)) and n not in STOP:
                words.add(n)
    kt_path = lesson / "analysis" / "keyterms.json"
    if kt_path.exists():
        kt = json.loads(kt_path.read_text(encoding="utf-8")).get("keyterms", [])
        for k in kt:
            term = k["term"] if isinstance(k, dict) else str(k)
            words.add(term.lower())
    return sorted(w for w in words if not lexicon.has_term(w, lex))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int)
    parser.add_argument("--pages", help="a section's pages, e.g. 5,6")
    parser.add_argument("--speed", type=float, default=1.0)
    args = parser.parse_args()

    lex = lexicon.load()
    pages = (sorted(int(x) for x in args.pages.split(",")) if args.pages
             else [args.page])
    terms = candidates(args.lesson_dir, pages, lex)
    out_dir = paths.boards_dir_for(args.lesson_dir, pages)
    # Probes are shared by the whole lesson (a term heard for one section is
    # heard for all) and made at the lesson speed.
    probe_dir = args.lesson_dir / "generated" / "term_probes"
    probe_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    from cartesia import Cartesia
    client = Cartesia(api_key=cartesia_key())
    lexicon.require_synced(client, lex)
    skey = scribe_key()

    results = []
    failures = []
    chars = 0
    print(f"{len(terms)} candidate terms not in the lexicon")
    for term in terms:
        wav = probe_dir / (re.sub(r"[^a-z0-9]", "_", term) + f"@{args.speed:g}.wav")
        heard_path = wav.with_suffix(".json")
        if not heard_path.exists():
            text = CARRIER.format(term=term)
            res = None
            for wait in (5, 10, 20, 40, 60, 90, 120, None):
                try:
                    res = synthesize(client, text, args.speed)
                    break
                except Exception as e:      # the per-minute quota: wait and retry
                    if wait is None:
                        raise SystemExit(f'STOPPED probing {term!r}: {str(e)[:200]}')
                    print(f'  {term}: {str(e)[:100]} - retry in {wait}s', flush=True)
                    time.sleep(wait)
            write_wav(wav, res["pcm"])
            chars += len(text)
            heard = transcribe_file(wav, skey)
            heard_path.write_text(json.dumps(heard, ensure_ascii=False), encoding="utf-8")
        heard = json.loads(heard_path.read_text(encoding="utf-8"))
        text = heard.get("text", "")
        ok = norm(term) in "".join(norm(w) for w in text.split())
        results.append({"term": term, "heard": text, "ok": ok})
        if not ok:
            failures.append(term)
        print(f"  {'ok  ' if ok else 'FAIL'} {term:<24} heard: {text!r}")

    report = {"checked_at": time.time(), "lexicon_version": lex["version"],
              "terms": results, "failures": failures, "characters_synthesised": chars}
    (out_dir / "terms_check.json").write_text(json.dumps(report, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    print(f"characters synthesised: {chars}")
    if failures:
        print("NOT HEARD, add to spike/lexicon.json before building: " + ", ".join(failures))
        raise SystemExit(len(failures))
    print("every candidate term was heard")


if __name__ == "__main__":
    main()
