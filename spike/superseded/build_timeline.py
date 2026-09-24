"""Build the deterministic playback timeline for a page from synthesised audio.

Every timestamp comes from Cartesia's word-level timing plus two silence
parameters -- never authored by hand. A cue's `word_index` (assigned in
write_script.py's split_cues) indexes the utterance's `text.split()` tokens,
which is exactly what Cartesia's word-timestamp list aligns to one-for-one
(verified against audio_index.json for all 56 page-13 utterances).

    .venv/Scripts/python spike/scripts/build_timeline.py <lesson_dir> \
        [--utterance-gap 0.4] [--beat-gap 1.2]

Reads:  <lesson_dir>/analysis/script/script.json
        <lesson_dir>/generated/page-<N>/audio_index.json
Writes: <lesson_dir>/generated/page-<N>/timeline.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--utterance-gap", type=float, default=0.4,
                         help="Silence in seconds between utterances within a "
                              "beat (default 0.4s -- a natural breath pause).")
    parser.add_argument("--beat-gap", type=float, default=1.2,
                         help="Silence in seconds between beats (default 1.2s "
                              "-- longer than the utterance gap so one teaching "
                              "point lands before the next beat begins).")
    parser.add_argument("--cue-lead", type=float, default=0.35,
                         help="Seconds a cue fires BEFORE the word it belongs to "
                              "(default 0.35s), so the student sees the mark and "
                              "then hears about it, as in a real classroom.")
    args = parser.parse_args()

    if args.beat_gap < args.utterance_gap:
        raise SystemExit("--beat-gap must be >= --utterance-gap")

    page = args.page
    script_path = paths.script_dir(args.lesson_dir, page) / "script.json"
    script = json.loads(script_path.read_text(encoding="utf-8"))

    out_dir = paths.generated_dir(args.lesson_dir, page)
    audio_index = json.loads((out_dir / "audio_index.json").read_text(encoding="utf-8"))

    t = 0.0
    beats_out = []
    for bi, beat in enumerate(script["beats"]):
        beat_start = t
        utterances_out = []
        for ui, utt in enumerate(beat["utterances"]):
            utt_id = utt["id"]
            entry = audio_index[utt_id]
            duration = entry["duration_s"]
            words = entry["words"]
            word_start = entry["word_start"]
            word_end = entry["word_end"]

            if words != utt["text"].split():
                raise SystemExit(
                    f"{utt_id}: Cartesia word list no longer matches text.split() "
                    "-- word_index cue alignment is not safe. Re-run synthesize_audio.py."
                )

            utt_start = t
            utt_end = t + duration

            cues_out = []
            pause_after = 0.0
            for cue in utt["cues"]:
                wi = cue["word_index"]
                if not (0 <= wi < len(word_start)):
                    raise SystemExit(f"{utt_id}/{cue['id']}: word_index {wi} out of range")

                if cue["type"] == "pause":
                    # A pause is the silence after this utterance, not a mark on
                    # a word, so its own word_index does not time it.
                    seconds = cue["target"].get("seconds") or 2.0
                    seconds = min(10.0, max(0.5, float(seconds)))
                    pause_after = max(pause_after, seconds)
                    cues_out.append({
                        "id": cue["id"], "type": cue["type"], "target": cue["target"],
                        "word_index": wi, "anchor_word": cue["anchor_word"],
                        "time": round(utt_end, 3),
                        "time_end": round(utt_end + seconds, 3),
                        "seconds": seconds,
                    })
                    continue

                # Lead: the mark lands slightly before the word, never before the
                # utterance's own first word minus the lead (it may sit in the
                # preceding silence, which is where a pause puts it to good use).
                at = utt_start + word_start[wi] - args.cue_lead
                cues_out.append({
                    "id": cue["id"],
                    "type": cue["type"],
                    "target": cue["target"],
                    "word_index": wi,
                    "anchor_word": cue["anchor_word"],
                    "time": round(max(0.0, at), 3),
                    "time_end": round(utt_start + word_end[wi], 3),
                })

            utterances_out.append({
                "id": utt_id,
                "text": utt["text"],
                "provenance": utt["provenance"],
                "audio_file": entry["file"],
                "start": round(utt_start, 3),
                "end": round(utt_end, 3),
                "cues": cues_out,
            })

            t = utt_end
            beat_end = utt_end          # the beat ends with its last utterance,
            is_last_utt_in_beat = ui == len(beat["utterances"]) - 1
            is_last_beat = bi == len(script["beats"]) - 1
            if not (is_last_utt_in_beat and is_last_beat):
                gap = args.beat_gap if is_last_utt_in_beat else args.utterance_gap
                # A pause cue governs its own silence, but never shortens the
                # structural gap it sits in.
                t += max(gap, pause_after)

        beats_out.append({
            "id": beat["id"],
            "learning_objective": beat["learning_objective"],
            "start": round(beat_start, 3),
            "end": round(beat_end, 3),   # ...not with the silence that follows it
            "utterances": utterances_out,
        })

    timeline = {
        "meta": {
            "lesson": script["meta"]["lesson"],
            "page": page,
            "utterance_gap_s": args.utterance_gap,
            "beat_gap_s": args.beat_gap,
            "cue_lead_s": args.cue_lead,
            "voice": next(iter(audio_index.values()))["voice"],
            "model": next(iter(audio_index.values()))["model"],
            "speed": next(iter(audio_index.values()))["speed"],
            "total_duration_s": round(t, 3),
        },
        "beats": beats_out,
    }

    out_path = out_dir / "timeline.json"
    out_path.write_text(json.dumps(timeline, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"beats: {len(beats_out)}")
    print(f"total duration: {t:.1f}s ({t / 60:.2f} min)")
    print(f"utterance gap: {args.utterance_gap}s, beat gap: {args.beat_gap}s, "
          f"cue lead: {args.cue_lead}s")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
