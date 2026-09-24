"""Assemble a page's board bundle: timeline plus the content of every block.

build_bundle.py adapted to the board model. There is no geometry to resolve:
a cue targets a block id, or a phrase inside a block by its text, and the
player lays the board out and finds the phrase in the block it drew. Nothing
here measures a PDF, and nothing is hardcoded per page (methodology §18, §19).

Each block travels as its data plus the HTML the screens preview renders it
with (write_screens.block_html), so the player and the preview cannot drift.

    .venv/Scripts/python spike/scripts/build_board_bundle.py <lesson_dir> --page 13

Reads:  <lesson_dir>/analysis/screens/page-<N>/screens.json
        <lesson_dir>/generated/page-<N>/boards/timeline.json
Writes: <lesson_dir>/generated/page-<N>/boards/bundle.json

Prints the visual-density figures (methodology §17a): count and spacing of
visual events, the longest stretch with nothing happening on screen, and
every stretch over fifteen seconds. A reveal, a mark, a pointer move, an
erase and a board change all count as something happening.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths                                   # noqa: E402
from write_screens import block_html, block_text_runs, is_exercise_board   # noqa: E402

VISUAL_GAP_LIMIT_S = 15.0

# ---------------------------------------------------------------------------
# The pointer follows reading (docs/02-DESIGN-SYSTEM.md §8). Deterministic:
# spoken words with Cartesia timings are matched against the words of every
# block on the board, and each matched run drives the pointer word by word.
# The player finds word k of a block in the DOM it drew, by the same
# tokenisation: whitespace split, non-alphanumerics dropped, empties skipped.
# ---------------------------------------------------------------------------
MIN_RUN = 3                    # matched block words for a run starting at a block's first word
MIN_RUN_MID = 4                # ...and for one starting mid-block, where chance overlaps
                               # of common words ("the patient receives") otherwise pull
                               # the pointer into a note that is not being read
MAX_NUMBER_WORDS = 8           # spoken words one digit token may stand for

# The block text has digits ("2010", "25", "10/08/2014"); speech has words. A
# block token containing a digit matches a run of number-ish spoken words.
UNITS = ("zero one two three four five six seven eight nine ten eleven twelve "
         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen").split()
TENS = "twenty thirty forty fifty sixty seventy eighty ninety".split()
ORDINALS = ("first second third fourth fifth sixth seventh eighth ninth tenth eleventh "
            "twelfth thirteenth fourteenth fifteenth sixteenth seventeenth eighteenth "
            "nineteenth twentieth thirtieth").split()
MONTHS = ("january february march april may june july august september october "
          "november december").split()
NUMBERISH = set(UNITS + TENS + ORDINALS + MONTHS
                + "hundred thousand million and of the a oh point".split())


def norm(token: str) -> str:
    return re.sub(r"[^a-z0-9]", "", token.lower())


def numberish(token: str) -> bool:
    if not token:
        return False
    if token in NUMBERISH or token.isdigit():
        return True
    for tens in TENS:
        rest = token[len(tens):]
        if token.startswith(tens) and (rest in UNITS or rest in ORDINALS):
            return True
    return False


def block_tokens(b: dict) -> list[str]:
    """Words of a block in the order its html emits them (write_screens.
    block_text_runs), which is the order the player counts them in."""
    out = []
    for run in block_text_runs(b):
        for w in run.split():
            n = norm(w)
            if n:
                out.append(n)
    return out


def match_run(spoken: list[str], i: int, btoks: list[str], j: int) -> list[tuple[int, int, int]]:
    """Pairs (block word, first spoken word, last spoken word) for the longest
    match starting at spoken i and block j."""
    pairs = []
    while i < len(spoken) and j < len(btoks):
        if spoken[i] == btoks[j]:
            pairs.append((j, i, i))
            i += 1
            j += 1
        elif any(ch.isdigit() for ch in btoks[j]) and numberish(spoken[i]):
            s0 = i
            while i < len(spoken) and numberish(spoken[i]) and i - s0 < MAX_NUMBER_WORDS:
                i += 1
            pairs.append((j, s0, i - 1))
            j += 1
        else:
            break
    return pairs


def reading_runs(words: list[str], starts: list[float], ends: list[float],
                 utt_start: float, candidates: dict[str, list[str]]) -> list[dict]:
    """Greedy left to right: at each spoken word, the longest matching run over
    every candidate block; runs shorter than MIN_RUN block words are not
    reading, just shared vocabulary."""
    spoken = [norm(w) for w in words]
    runs = []
    i = 0
    while i < len(spoken):
        best: list[tuple[int, int, int]] = []
        best_block = None
        if spoken[i]:
            for bid, btoks in candidates.items():
                for j, tok in enumerate(btoks):
                    if tok == spoken[i] or (any(ch.isdigit() for ch in tok)
                                            and numberish(spoken[i])):
                        pairs = match_run(spoken, i, btoks, j)
                        if len(pairs) > len(best):
                            best, best_block = pairs, bid
        if len(best) >= (MIN_RUN if best and best[0][0] == 0 else MIN_RUN_MID):
            runs.append({"block": best_block,
                         "words": [[bj, round(utt_start + starts[s0], 3),
                                    round(utt_start + ends[s1], 3)]
                                   for bj, s0, s1 in best]})
            i = best[-1][2] + 1
        else:
            i += 1
    return runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    args = parser.parse_args()

    screens = json.loads((paths.screens_dir(args.lesson_dir, args.page) / "screens.json")
                         .read_text(encoding="utf-8"))
    out_dir = paths.boards_dir(args.lesson_dir, args.page)
    timeline = json.loads((out_dir / "timeline.json").read_text(encoding="utf-8"))

    blocks = {b["id"]: b for t in screens["topics"] for h in t["thoughts"]
              for b in h["blocks"]}
    used = {i for bd in timeline["boards"] for i in bd["fixed"]}
    used |= {i for bd in timeline["boards"] for s in bd["states"] for i in s["working"]}
    missing = sorted(used - set(blocks))
    if missing:
        raise SystemExit(f"timeline refers to blocks not in screens.json: {missing}")

    bundle_blocks = {}
    for i in sorted(used):
        b = blocks[i]
        bundle_blocks[i] = {**{k: b.get(k) for k in ("id", "type", "label", "text", "term",
                                                       "explanation", "left", "right",
                                                       "family", "kind", "icon", "items",
                                                       "header", "rows", "provenance")},
                            "html": block_html(b)}

    audio_index = json.loads((out_dir / "audio_index.json").read_text(encoding="utf-8"))
    tokens = {i: block_tokens(blocks[i]) for i in used}

    n_cues = 0
    n_read_utts = n_read_words = 0
    for bd in timeline["boards"]:
        # An exercise topic shows only the item number; the player hides the
        # topic number in its header (docs/02-DESIGN-SYSTEM.md §7a).
        bd["exercise"] = is_exercise_board(bd["fixed"], blocks)
        for s in bd["states"]:
            candidates = {i: tokens[i] for i in list(bd["fixed"]) + list(s["working"])}
            for u in s["utterances"]:
                for c in u["cues"]:
                    n_cues += 1
                    # A reveal may name a diagram PART, "k07.3": its block is k07.
                    base = str(c.get("block")).split(".")[0]
                    if c["type"] != "pause" and base not in bundle_blocks:
                        raise SystemExit(f"{u['id']}/{c['id']}: cue on unknown block "
                                         f"{c.get('block')!r}")
                    if c["type"] == "arrow" and (c.get("to_block") or c.get("block")) \
                            not in bundle_blocks:
                        raise SystemExit(f"{u['id']}/{c['id']}: arrow to unknown block")
                entry = audio_index[u["id"]]
                u["reading"] = reading_runs(entry["words"], entry["word_start"],
                                            entry["word_end"], u["start"], candidates)
                if u["reading"]:
                    n_read_utts += 1
                    n_read_words += sum(len(r["words"]) for r in u["reading"])

    bundle = {
        "meta": {**timeline["meta"], "screens_raw_id": screens.get("raw_id"),
                 "lesson_title": (screens.get("lesson_title") or {}).get("title"),
                 # The contents list shows sections only (docs/00-PRODUCT.md §1).
                 # One page is one section; a lesson-wide player will list them all.
                 "sections": [{"title": screens["section"]["title"],
                               "pages": screens["section"]["pages"],
                               "start": timeline["boards"][0]["start"]}]},
        "blocks": bundle_blocks,
        "boards": timeline["boards"],
        "events": timeline["events"],
    }
    bundle_path = out_dir / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")

    # A cue, an event, or the reading pointer moving to a word: all count as
    # something happening on screen.
    visual = sorted([c["time"] for bd in timeline["boards"] for s in bd["states"]
                     for u in s["utterances"] for c in u["cues"] if c["type"] != "pause"]
                    + [e["time"] for e in timeline["events"]]
                    + [w[1] for bd in timeline["boards"] for s in bd["states"]
                       for u in s["utterances"] for r in u["reading"] for w in r["words"]])
    total = timeline["meta"]["total_duration_s"]
    marks = [0.0] + visual + [total]
    gaps = [(marks[i + 1] - marks[i], marks[i], marks[i + 1]) for i in range(len(marks) - 1)]
    longest, at_from, at_to = max(gaps)
    over = [g for g in gaps if g[0] > VISUAL_GAP_LIMIT_S]

    n_utts = sum(len(s["utterances"]) for bd in timeline["boards"] for s in bd["states"])
    marks: dict[str, int] = {}
    for bd in timeline["boards"]:
        for s in bd["states"]:
            for u in s["utterances"]:
                for c in u["cues"]:
                    marks[c["type"]] = marks.get(c["type"], 0) + 1
    print(f"blocks {len(bundle_blocks)} | cues {n_cues} | events {len(timeline['events'])}")
    print("cues by type: " + ", ".join(f"{k} {v}" for k, v in sorted(marks.items())))
    print(f"reading pointer: {n_read_utts} of {n_utts} utterances read from the board, "
          f"{n_read_words} words followed")
    print(f"visual events: {len(visual)} over {total / 60:.1f} min = one every "
          f"{total / max(1, len(visual)):.1f}s")
    print(f"longest stretch with nothing on screen: {longest:.1f}s "
          f"({at_from:.1f}s -> {at_to:.1f}s)")
    if over:
        print(f"OVER {VISUAL_GAP_LIMIT_S:.0f}s: {len(over)} stretch(es): "
              + ", ".join(f"{g:.1f}s at {a:.0f}s" for g, a, _ in over[:8]))
    print(f"wrote {bundle_path}")


if __name__ == "__main__":
    main()
