"""Build the deterministic playback timeline for a page of boards.

build_timeline.py adapted to narration.json. Every timestamp comes from
Cartesia's word-level timing plus silence parameters, never authored by hand
(methodology §6). A cue marker's position in text_with_cues gives a word
index into the utterance's spoken words, which is exactly what Cartesia's
word-timestamp list aligns to one for one; the build refuses to continue if
the two lists disagree.

    .venv/Scripts/python spike/scripts/build_board_timeline.py <lesson_dir> --page 13 \
        [--utterance-gap 0.4] [--state-gap 1.2] [--board-gap 1.5] [--cue-lead 0.35]

Reads:  <lesson_dir>/analysis/narration/page-<N>/narration.json
        <lesson_dir>/generated/page-<N>/boards/audio_index.json
Writes: <lesson_dir>/generated/page-<N>/boards/timeline.json

Events, all derived:
  board   a board begins: its title and fixed layer appear. At 0 for the
          first; for the rest, after the previous board's last utterance,
          its pause if any, and the board gap.
  erase   a state's working layer is cleared: after the state's last
          utterance and its pause, so a pause placed there is honoured
          before the notes vanish. The next state's speech starts a state
          gap later, on the clean board.
A pause cue governs the silence after its utterance and never shortens the
gap it sits in. A reveal or mark fires a cue lead before its word.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths                                   # noqa: E402
from write_narration import MARKER, spoken     # noqa: E402


def marker_positions(text_with_cues: str) -> tuple[list[str], dict[str, int]]:
    """Cue id -> index of the word the marker sits before. A marker with no
    word after it belongs to the last word (spike/README.md, pause markers)."""
    words: list[str] = []
    positions: dict[str, int] = {}
    for token in text_with_cues.split():
        for m in MARKER.finditer(token):
            positions[m.group(1)] = len(words)
        bare = MARKER.sub("", token).strip()
        if bare:
            words.append(bare)
    for cid, pos in positions.items():
        if pos >= len(words):
            positions[cid] = max(0, len(words) - 1)
    return words, positions


def lay_timeline(narr: dict, audio_index: dict, utterance_gap: float = 0.4,
                 state_gap: float = 1.2, board_gap: float = 1.5,
                 cue_lead: float = 0.35) -> tuple[list[dict], list[dict], float]:
    """Boards, events and total duration from a narration and its audio
    index. Shared by the real build (Cartesia timings) and the silent
    preview (estimated timings), so both play on the same rules."""
    t = 0.0
    boards_out = []
    events = []
    n_boards = len(narr["boards"])
    for bi, bd in enumerate(narr["boards"]):
        events.append({"type": "board", "time": round(t, 3), "board": bd["id"]})
        board_start = t
        states_out = []
        n_states = len(bd["states"])
        for si, s in enumerate(bd["states"]):
            state_start = t
            utts_out = []
            pause_after = 0.0
            for ui, u in enumerate(s["utterances"]):
                entry = audio_index[u["id"]]
                words, positions = marker_positions(u["text_with_cues"])
                if entry["words"] != words or words != spoken(u["text_with_cues"]).split():
                    raise SystemExit(
                        f"{u['id']}: Cartesia word list does not match the spoken "
                        "words; cue alignment is not safe. Re-run "
                        "synthesize_narration.py.")
                utt_start = t
                utt_end = t + entry["duration_s"]
                pause_after = 0.0
                cues_out = []
                for c in u["cues"]:
                    wi = positions.get(c["id"])
                    if wi is None:
                        raise SystemExit(f"{u['id']}/{c['id']}: no marker in the text")
                    if c["type"] == "pause":
                        seconds = min(10.0, max(0.5, float(c.get("seconds") or 2.0)))
                        pause_after = max(pause_after, seconds)
                        cues_out.append({"id": c["id"], "type": "pause",
                                         "text": c.get("text"), "seconds": seconds,
                                         "word_index": wi,
                                         "time": round(utt_end, 3),
                                         "time_end": round(utt_end + seconds, 3)})
                        continue
                    at = utt_start + entry["word_start"][wi] - cue_lead
                    cues_out.append({"id": c["id"], "type": c["type"],
                                     "block": c.get("block"), "text": c.get("text"),
                                     "to_block": c.get("to_block"), "to_text": c.get("to_text"),
                                     "with": c.get("with"),
                                     "word_index": wi, "anchor_word": words[wi],
                                     "time": round(max(0.0, at), 3),
                                     "time_end": round(utt_start + entry["word_end"][wi], 3)})
                utts_out.append({"id": u["id"], "text": entry["text"],
                                 "provenance": u["provenance"],
                                 "audio_file": entry["file"],
                                 "start": round(utt_start, 3), "end": round(utt_end, 3),
                                 "cues": cues_out})
                t = utt_end
                if ui < len(s["utterances"]) - 1:
                    t += max(utterance_gap, pause_after)

            state_end = t                      # speech ends here; the pause follows
            erase = None
            if si < n_states - 1:
                erase_at = t + pause_after
                erase = {"time": round(erase_at, 3), "blocks": list(s["working"])}
                events.append({"type": "erase", "time": erase["time"],
                               "state": s["id"], "blocks": list(s["working"])})
                t = erase_at + state_gap
            elif bi < n_boards - 1:
                t = t + pause_after + board_gap
            else:
                t = t + pause_after            # the lesson ends after the last pause
            states_out.append({"id": s["id"], "working": list(s["working"]),
                               "start": round(state_start, 3), "end": round(state_end, 3),
                               "utterances": utts_out, "erase": erase})
        boards_out.append({"id": bd["id"], "title": bd["title"], "fixed": list(bd["fixed"]),
                           "start": round(board_start, 3), "end": round(state_end, 3),
                           "states": states_out})

    return boards_out, events, t


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--utterance-gap", type=float, default=0.4,
                         help="silence between utterances within a state (default 0.4)")
    parser.add_argument("--state-gap", type=float, default=1.2,
                         help="silence after an erase before the next state speaks "
                              "(default 1.2)")
    parser.add_argument("--board-gap", type=float, default=1.5,
                         help="silence between a board's last utterance (and pause) "
                              "and the next board's first (default 1.5)")
    parser.add_argument("--cue-lead", type=float, default=0.35,
                         help="seconds a cue fires before its word (default 0.35)")
    args = parser.parse_args()

    page = args.page
    narr = json.loads((paths.narration_dir(args.lesson_dir, page) / "narration.json")
                      .read_text(encoding="utf-8"))
    out_dir = paths.boards_dir(args.lesson_dir, page)
    audio_index = json.loads((out_dir / "audio_index.json").read_text(encoding="utf-8"))

    boards_out, events, t = lay_timeline(narr, audio_index, args.utterance_gap,
                                         args.state_gap, args.board_gap, args.cue_lead)

    first = next(iter(audio_index.values()))
    timeline = {
        "meta": {"lesson": narr["lesson"], "page": page,
                 "utterance_gap_s": args.utterance_gap, "state_gap_s": args.state_gap,
                 "board_gap_s": args.board_gap, "cue_lead_s": args.cue_lead,
                 "voice": first["voice"], "model": first["model"], "speed": first["speed"],
                 "total_duration_s": round(t, 3)},
        "boards": boards_out,
        "events": events,
    }
    out_path = out_dir / "timeline.json"
    out_path.write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")
    n_utt = sum(len(s["utterances"]) for b in boards_out for s in b["states"])
    print(f"boards: {len(boards_out)} | states: "
          f"{sum(len(b['states']) for b in boards_out)} | utterances: {n_utt} | "
          f"erase events: {sum(1 for e in events if e['type'] == 'erase')}")
    print(f"total duration: {t:.1f}s ({t / 60:.2f} min)")
    print(f"utterance gap {args.utterance_gap}s, state gap {args.state_gap}s, board gap "
          f"{args.board_gap}s, cue lead {args.cue_lead}s")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
