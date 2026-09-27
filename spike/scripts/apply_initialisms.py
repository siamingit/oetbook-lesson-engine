"""Rewrite a lesson's initialisms in the ADR 016 form ("C-O-P-D"), changing
nothing else: one utterance override per utterance that has an initialism in
an old form (spaces or full stops between its letters, joined by full stops,
or plain capitals), merged with an override the utterance already has.

    .venv/Scripts/python spike/scripts/apply_initialisms.py <lesson_dir>           # list
    .venv/Scripts/python spike/scripts/apply_initialisms.py <lesson_dir> --write   # write

Reads:  analysis/narration/<section>/raw_response.json and overrides.json
Writes: analysis/narration/<section>/overrides.json (`utterances`; each entry
        made here carries `initialisms`, the forms it changed)

Then re-render each section listed (write_narration.py --render) and rebuild:
the audio cache re-makes only the changed clips. The finder is the narration
audit's (write_narration.INITIALISM_FORMS); a lexicon term approved as the
voice's default (OET) is kept as written. A full stop that also ends the
sentence ("B M I." at a sentence's end) stays.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lexicon                                           # noqa: E402
from write_narration import INITIALISM_FORMS              # noqa: E402

NOTE = "ADR 016: initialisms in the hyphenated form"
SENTENCE_GOES_ON = re.compile(r"\s*($|[A-Z\"'‘“(]|\{\{c\d+\}\}\s*[A-Z])")


def hyphenate(text: str, keep: set[str]) -> tuple[str, list[tuple[str, str]]]:
    """The text with every old-form initialism hyphenated, and (old, new) pairs."""
    spans = []
    for rx, _ in INITIALISM_FORMS:
        for m in rx.finditer(text):
            if m.group(0) in keep or any(a < m.end() and m.start() < b for a, b, _ in spans):
                continue
            w = m.group(0)
            hy = "-".join(c for c in w if c.isalpha())
            if w.endswith(".") and SENTENCE_GOES_ON.match(text[m.end():]):
                hy += "."                        # the sentence's own full stop
            spans.append((m.start(), m.end(), hy))
    out, done = text, []
    for a, b, hy in sorted(spans, reverse=True):
        done.append((text[a:b], hy))
        out = out[:a] + hy + out[b:]
    return out, done[::-1]


def span(raw: str, new: str) -> tuple[str, str]:
    """The smallest word-bounded stretch of `raw` that, replaced once, gives `new`
    (the override's `expect` and its replacement)."""
    p = 0
    while p < min(len(raw), len(new)) and raw[p] == new[p]:
        p += 1
    s = 0
    while s < min(len(raw), len(new)) - p and raw[-1 - s] == new[-1 - s]:
        s += 1
    while p > 0 and raw[p - 1] != " ":
        p -= 1
    while s > 0 and raw[len(raw) - s] != " ":
        s -= 1
    for start in (p, 0):
        exp, rep = raw[start:len(raw) - s], new[start:len(new) - s]
        if raw.replace(exp, rep, 1) == new:
            return exp, rep
    raise SystemExit(f"no single stretch turns {raw!r} into {new!r}")


def main() -> None:
    L = Path(sys.argv[1])
    write = "--write" in sys.argv
    keep = {t for t, e in lexicon.load()["entries"].items() if e.get("kind") == "default"}
    total, sections = 0, []
    for od in sorted((L / "analysis" / "narration").iterdir()):
        rp = od / "raw_response.json"
        if not rp.exists():
            continue
        raw = json.loads(rp.read_text(encoding="utf-8"))
        model_out = json.loads([b["text"] for b in raw["content"] if b["type"] == "text"][-1])
        op = od / "overrides.json"
        ov = json.loads(op.read_text(encoding="utf-8")) if op.exists() else {}
        uov = ov.get("utterances") or {}
        changed = False
        for ms in (s for mb in model_out["boards"] for s in mb["states"]):
            for i, u in enumerate(ms["utterances"], 1):
                uid = f"{ms['state']}.u{i}"
                old = uov.get(uid)
                if old and old.get("initialisms"):
                    continue                     # made here on an earlier run
                base = u["text_with_cues"]
                cur = base.replace(old["expect"], old["text_with_cues"], 1) if old else base
                new, done = hyphenate(cur, keep)
                if not done:
                    continue
                exp, rep = span(base, new)
                total += len(done)
                changed = True
                print(f"{od.name:12} {uid:10} " + "; ".join(f"{a!r} -> {b!r}" for a, b in done))
                uov[uid] = {"expect": exp, "text_with_cues": rep,
                            "note": ((old or {}).get("note", "") + " " + NOTE + ": "
                                     + ", ".join(f"{a} -> {b}" for a, b in done)).strip(),
                            "initialisms": [list(x) for x in done]}
        if changed:
            sections.append(od.name)
            if write:
                ov["utterances"] = uov
                op.write_text(json.dumps(ov, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{total} initialism(s) in {len(sections)} section(s): {', '.join(sections) or '-'}"
          + ("" if write else " (listed only; --write to write the overrides)"))


if __name__ == "__main__":
    main()
