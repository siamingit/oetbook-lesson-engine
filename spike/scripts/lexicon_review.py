"""The lexicon review page: every lexicon term, playable alone and inside a
sentence from a lesson, with the default rendering beside it and the
phonemes shown, for the maintainer to approve or reject by ear.

    .venv/Scripts/python spike/scripts/lexicon_review.py <lesson_dir> --page 13

Reads:  spike/lexicon.json
        <lesson_dir>/generated/page-<N>/boards/audio_index.json (sentences and
        their clips, when the page contains the term)
Writes: spike/out/lexicon-review/index.html and its WAVs (gitignored)

For each term, three clips:
  alone     the term in the carrier "The word is X.", under the lexicon
  sentence  every utterance of the page that contains the term, as built
  default   the carrier with no dictionary, for comparison
Approval is not recorded by the page (it is static): the maintainer runs
`lexicon.py --approve TERM --by NAME` or `--reject TERM --why "..."`, and the
page shows the current state. Only the maintainer's ear is evidence
(methodology §20).
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lexicon                                                       # noqa: E402
import paths                                                         # noqa: E402
from extract_understanding import esc                                # noqa: E402
from synthesize_audio import MODEL_ID, VOICE_ID, api_key, write_wav  # noqa: E402
from synthesize_narration import synthesize                          # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "out" / "lexicon-review"
CARRIER = "The word is {term}."
PROBES: Path | None = None       # set in main() to the page's term_probes folder

CSS = """
body{font:15px/1.5 system-ui,sans-serif;background:#f4f3ef;color:#2C2C2A;margin:0;padding:24px 28px 60px;max-width:1100px}
h1{font-size:20px} h2{font-size:17px;margin:32px 0 6px;display:flex;gap:10px;align-items:center}
.st{font-size:11px;padding:2px 8px;border-radius:3px;letter-spacing:.05em;text-transform:uppercase}
.st.ok{background:#EAF3DE;color:#173404} .st.no{background:#FCEBEB;color:#501313}
.meta{color:#6b6a64;font-size:13px;margin-bottom:10px}
table{border-collapse:collapse;width:100%;background:#fff;font-size:13.5px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid #e3e1d9;vertical-align:top}
th{color:#6b6a64;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em}
code{font-size:12.5px} audio{width:260px;vertical-align:middle}
.ph{font-family:Consolas,monospace;font-size:12.5px;color:#4a4944}
.how{background:#fff;border:1px solid #d6d4cc;padding:10px 14px;margin:14px 0}
"""


def fibrosis_like(term: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", term.lower())


def render_clip(client, text: str, dict_id: str | None, path: Path) -> dict:
    if path.with_suffix(".json").exists():
        return json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    # A probe made by check_terms.py under the same carrier and lexicon serves
    # as the "alone, lexicon" clip; it saves a synthesis when credit is short.
    if dict_id and PROBES:
        for cand in (PROBES / ("lex_" + path.name.split("_alone")[0] + ".wav"),
                     PROBES / (path.name.split("_alone")[0] + ".wav")):
            if cand.exists():
                path.write_bytes(cand.read_bytes())
                info = {"file": path.name, "phonemes": "(from check_terms probe; no phonemes kept)",
                        "chars": 0}
                path.with_suffix(".json").write_text(json.dumps(info), encoding="utf-8")
                return info
    try:
        return _render_clip(client, text, dict_id, path)
    except Exception as e:                      # a quota or network failure must not
        return {"file": None, "phonemes": "", "chars": 0,   # hide the clips that exist
                "error": str(e)[:200]}


def _render_clip(client, text: str, dict_id: str | None, path: Path) -> dict:
    if dict_id:
        r = synthesize(client, text, 0.6, dict_id)
    else:
        ev = client.tts.sse(model_id=MODEL_ID, transcript=text, voice={"id": VOICE_ID},
                            language="en", add_timestamps=True, add_phoneme_timestamps=True,
                            generation_config={"speed": 0.6},
                            output_format={"container": "raw", "encoding": "pcm_s16le",
                                           "sample_rate": 44100})
        pcm, ph = bytearray(), []
        for e in ev:
            if e.type == "chunk" and e.audio:
                pcm.extend(e.audio)
            elif e.type == "phoneme_timestamps":
                ph += list(e.phoneme_timestamps.phonemes)
        r = {"pcm": bytes(pcm), "phonemes": " ".join(ph)}
    write_wav(path, r["pcm"])
    info = {"file": path.name, "phonemes": r["phonemes"], "chars": len(text)}
    path.with_suffix(".json").write_text(json.dumps(info), encoding="utf-8")
    return info


def word_duration(words, starts, ends, term: str) -> str:
    for w, s0, s1 in zip(words, starts, ends):
        if term.lower() in w.lower() or w.startswith("<<"):
            return f"{s1 - s0:.2f} s"
    return ""


def render_candidate(client, term: str, cand: dict, sentence: str, lex: dict) -> list[dict]:
    """Two clips for one candidate, alone and in the lesson sentence, each with
    the word's duration from Cartesia's own timestamps. An `alias` candidate
    is tried through a temporary dictionary holding only that alias; an
    `inline` candidate replaces the word in the transcript with the markup."""
    slug = fibrosis_like(term) + "_" + cand["id"]
    out = []
    for label, text in (("alone", CARRIER.format(term=term)), ("sentence", sentence)):
        path = OUT / f"{slug}_{label}.wav"
        meta = path.with_suffix(".json")
        if meta.exists():
            out.append(json.loads(meta.read_text(encoding="utf-8")))
            continue
        try:
            if cand["kind"] == "inline":
                spoken = re.sub(re.escape(term), cand["value"], text, flags=re.I)
                r = synthesize(client, spoken, 0.6, lex["cartesia"]["dict_id"])
            else:
                tmp = client.pronunciation_dicts.create(
                    name="lexicon-candidate", items=[{"text": term, "alias": cand["value"],
                                                     "case_sensitive": False}])
                try:
                    r = synthesize(client, text, 0.6, tmp.id)
                finally:
                    client.pronunciation_dicts.delete(tmp.id)
            write_wav(path, r["pcm"])
            info = {"file": path.name, "label": label, "text": text, "phonemes": r["phonemes"],
                    "duration": word_duration(r["words"], r["word_start"], r["word_end"], term),
                    "chars": len(text)}
        except Exception as ex:
            info = {"file": None, "label": label, "text": text, "phonemes": "", "duration": "",
                    "chars": 0, "error": str(ex)[:200]}
        if info.get("file"):
            meta.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
        out.append(info)
    return out


def audio_or_reason(clip: dict) -> str:
    if clip.get("file"):
        return '<audio controls src="' + clip["file"] + '"></audio>'
    return '<span class="st no">not made: ' + esc(clip.get("error") or "unknown") + "</span>"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lesson_dir", type=Path)
    parser.add_argument("--page", type=int, required=True)
    args = parser.parse_args()
    lex = lexicon.load()
    from cartesia import Cartesia
    client = Cartesia(api_key=api_key())
    lexicon.require_synced(client, lex)
    dict_id = lex["cartesia"]["dict_id"]
    OUT.mkdir(parents=True, exist_ok=True)

    out_dir = paths.boards_dir(args.lesson_dir, args.page)
    global PROBES
    PROBES = out_dir / "term_probes"
    index_path = out_dir / "audio_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}

    chars = 0
    sections = []
    for term, e in sorted(lex["entries"].items()):
        slug = fibrosis_like(term)
        alone = render_clip(client, CARRIER.format(term=term), dict_id, OUT / f"{slug}_alone.wav")
        default = render_clip(client, CARRIER.format(term=term), None, OUT / f"{slug}_default.wav")
        chars += alone.get("chars", 0) + default.get("chars", 0)
        rows = []
        for uid, ent in index.items():
            if term.lower() in ent["text"].lower():
                src = out_dir / ent["file"]
                dst = OUT / f"{slug}_{uid}.wav"
                if not dst.exists():
                    dst.write_bytes(src.read_bytes())
                dur = ""
                for w, s0, s1 in zip(ent["words"], ent["word_start"], ent["word_end"]):
                    if term.lower() in w.lower():
                        dur = f"{s1 - s0:.2f} s"
                rows.append((uid, ent["text"], dst.name, dur, ent.get("phonemes", "")))
        cand_html = ""
        if e.get("candidates"):
            crow = []
            for cand in e["candidates"]:
                clips = render_candidate(client, term, cand, e.get("candidate_sentence")
                                         or CARRIER.format(term=term), lex)
                chars += sum(c.get("chars", 0) for c in clips)
                crow.append("<tr><td><b>" + esc(cand["id"]) + "</b> " + esc(cand["kind"])
                            + "<br><code>" + esc(cand["value"]) + "</code><br><span class=meta>"
                            + esc(cand.get("why") or "") + ("<br><b>" + esc(cand["result"]) + "</b>" if cand.get("result") else "") + "</span></td>"
                            + "".join("<td>" + audio_or_reason(c) + "<br>" + esc(c.get("duration") or "")
                                      + '<br><span class="ph">' + esc(c.get("phonemes", "")[:90]) + "</span></td>"
                                      for c in clips) + "</tr>")
            cand_html = ('<h3 style="font-size:15px;margin:14px 0 4px">Candidates, for the maintainer to '
                         'choose by ear</h3><div class="meta">word duration under each clip; sentence: '
                         + esc(e.get("candidate_sentence") or "") + "</div><table><tr><th>candidate</th>"
                         "<th>alone</th><th>in the sentence</th></tr>" + "".join(crow) + "</table>")
        status = ('<span class="st ok">approved by ' + esc(e.get("approved_by") or "") + "</span>"
                  if e.get("approved") else '<span class="st no">not approved</span>')
        kind = e.get("kind", "alias")
        body = ('<div class="meta">' + ("approved as the voice's default rendering, no entry sent"
                                        if kind == "default" else
                                        "alias <code>" + esc(e["alias"] or "") + "</code>")
                + " &middot; target "
                + esc(e.get("target") or e.get("ipa") or "") + "</div>"
                + "<table><tr><th>clip</th><th>text</th><th>play</th><th>word</th><th>phonemes</th></tr>"
                + "<tr><td>alone, lexicon</td><td>" + esc(CARRIER.format(term=term))
                + "</td><td>" + audio_or_reason(alone) + "</td><td></td>"
                + '<td class="ph">' + esc(alone["phonemes"]) + "</td></tr>"
                + "<tr><td>alone, default voice</td><td>" + esc(CARRIER.format(term=term))
                + "</td><td>" + audio_or_reason(default) + "</td><td></td>"
                + '<td class="ph">' + esc(default["phonemes"]) + "</td></tr>"
                + "".join("<tr><td>" + esc(uid) + "</td><td>" + esc(text)
                          + '</td><td><audio controls src="' + f + '"></audio></td><td>' + dur
                          + '</td><td class="ph">' + esc(ph[:160]) + "</td></tr>"
                          for uid, text, f, dur, ph in rows)
                + "</table>" + cand_html)
        sections.append("<h2>" + esc(term) + " " + status + "</h2>" + body)

    # Voice speed: one lesson utterance at several settings, each measured
    # (speed_probe.py). The clip nearest each target pace is marked.
    speed_html = ""
    sp_path = OUT / "speed_probes.json"
    if sp_path.exists():
        sp = json.loads(sp_path.read_text(encoding="utf-8"))
        picks = {}
        for target in (145, 150, 155):
            best = min(sp["settings"], key=lambda p: abs(p["wpm"] - target))
            picks.setdefault(best["speed"], []).append(target)
        rows = "".join(
            "<tr" + (' style="background:#EAF3DE"' if p["speed"] in picks else "") + "><td>"
            + f"{p['speed']:.3f}" + (" (current lesson setting)" if p.get("current") else "")
            + "</td><td><b>" + f"{p['wpm']:.0f}" + "</b> wpm</td><td>" + f"{p['duration_s']:.2f} s"
            + "</td><td>" + ", ".join(f"nearest to {t}" for t in picks.get(p["speed"], []))
            + '</td><td><audio controls src="' + p["file"] + '"></audio></td></tr>'
            for p in sorted(sp["settings"], key=lambda p: p["wpm"]))
        speed_html = (
            '<h2>Voice speed</h2><div class="meta">One lesson utterance (' + esc(sp["utterance"])
            + ", page " + str(sp["page"]) + ", " + str(sp["words"]) + " words): <i>" + esc(sp["text"])
            + "</i></div>"
            '<div class="how">Pace is measured on each clip: words divided by audio length. The same '
            "setting varies by several words per minute from one synthesis to the next, and above "
            "about 0.9 the pace levels off near 155, so a setting is a target, not a guarantee. The "
            "rows marked green are the clips nearest 145, 150 and 155 words per minute. Choose by "
            "ear; the whole lesson's pace is measured again after synthesis. Rebuild the silent "
            "preview at the chosen pace with<br><code>.venv/Scripts/python "
            "spike/scripts/build_silent_preview.py &lt;lesson_dir&gt; --wpm N</code></div>"
            "<table><tr><th>setting</th><th>pace</th><th>length</th><th></th><th>play</th></tr>"
            + rows + "</table>")

    html = ('<!doctype html><meta charset="utf-8"><title>Lexicon review</title><style>' + CSS
            + "</style><h1>Pronunciation lexicon &mdash; review by ear</h1>"
            + '<div class="meta">spike/lexicon.json v' + str(lex["version"]) + " &middot; voice "
            + esc(VOICE_ID) + " &middot; sentences from page " + str(args.page) + "</div>"
            + '<div class="how">Listen to each term alone and in its sentences. Then record your '
              "verdict:<br><code>.venv/Scripts/python spike/scripts/lexicon.py --approve TERM --by NAME</code>"
              "<br><code>.venv/Scripts/python spike/scripts/lexicon.py --reject TERM --why \"...\"</code>"
              "<br>An unapproved term blocks synthesis of any page that contains it.</div>"
            + speed_html + "".join(sections))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print(str(OUT / "index.html"))
    print(f"terms: {len(lex['entries'])} | characters synthesised this run: {chars}")


if __name__ == "__main__":
    main()
