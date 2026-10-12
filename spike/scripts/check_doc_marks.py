"""Every phrase of a document that the narration reads or quotes is marked when
it is spoken (maintainer, 2026-10-06; ADR 026).

    .venv/Scripts/python spike/scripts/check_doc_marks.py <lesson_dir>              # the finished player
    .venv/Scripts/python spike/scripts/check_doc_marks.py <lesson_dir> --narration  # before synthesis

A document is a practice-set text (a core table with `doc`, bundle 1.13), on a
board of its own or in a map of the four texts. For every utterance spoken
while a document is on screen, the spoken words are compared with each part of
the document (each row): a run of words the narration shares with a part is a
QUOTE when it holds two content words or more ("check the dressing", "step
four"), or is a whole short part (a one-word heading such as "Discharge"). A
run with one content word ("if the nurse is") is a common phrase, not a quote. Numbers compare as
words ("Step 2" and "step two"), an initialism spelled with hyphens as the
letters ("E-C-G" and "ECG").

Each quote must have a mark, a `highlight` or a keyword pair (`match1` to
`match3`), whose words share a content word with it, timed to the moment the
quote is spoken: in the finished player, the mark's time from 1.5 s before the
quote's first word to 0.3 s after its last (the voice's own word timings); with
`--narration`, before the clips exist, the mark's cue marker placed at most
three words before the quote's first word or inside it. A mark covers its own
whole phrase, so the window before the quote is longer by the mark's words
(0.4 s, or one word, a word): "six point zero to six point four" under one mark. A quote with no such
mark fails the check, with its time in the lesson. Words that are also words of
a question on the board are the question read aloud, not the text: they are not
a quote of the text (where they match the text, they are a keyword pair and are
marked as one).

The table's header (its label and title) is not a part: reading a text's title
names it, it does not read from it.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths  # noqa: E402

MARKS = {"highlight", "match1", "match2", "match3",
         # a Part C lesson's opinion-signal marks (bundle 1.17) mark what they cover
         "sig_opinion", "sig_hedge", "sig_judge", "sig_main", "sig_aside"}
LEAD_S, TAIL_S, LEAD_WORDS = 1.5, 0.3, 3
STOP = set("""a an the and or but of to in on at for from by with as is are was were be been
this that these those it its you your we our they their he she his her i me my not no do does
did so if then than there here what which who when where how all any each one some such into out
up down over after before about can will would should may might must just only also very too
look see find take make use get go keep need say says said know""".split())
# "before" and "after" are stop words for the content test: "after surgery" is
# one content word

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def num_words(n: int) -> list[str]:
    if n < 20:
        return [ONES[n]]
    if n < 100:
        return [TENS[n // 10]] + ([ONES[n % 10]] if n % 10 else [])
    if n < 1000:
        rest = n % 100
        return [ONES[n // 100], "hundred"] + (["and"] + num_words(rest) if rest else [])
    if n < 10000:
        rest = n % 1000
        return num_words(n // 1000) + ["thousand"] + (num_words(rest) if rest else [])
    return [str(n)]


def tokens(text: str) -> list[str]:
    """Lower-case words, numbers as words, a hyphen-spelled initialism as one word."""
    text = re.sub(r"\b((?:[A-Za-z]-){1,}[A-Za-z])\b",
                  lambda m: m.group(1).replace("-", "") if all(len(p) == 1 for p in m.group(1).split("-"))
                  else m.group(1), text)
    out = []
    for w in re.findall(r"\d+(?:\.\d+)?|[A-Za-z]+(?:'[A-Za-z]+)?", text):
        if w[0].isdigit():
            whole, _, dec = w.partition(".")
            out += num_words(int(whole))
            if dec:
                out += ["point"] + [ONES[int(d)] for d in dec]
        else:
            out.append(w.lower())
    return out


def content(ws) -> set[str]:
    return {w for w in ws if len(w) >= 3 and w not in STOP}


def dedupe(runs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """One quote per stretch of speech: overlapping runs keep the longest."""
    runs = sorted(set(runs), key=lambda r: (r[0], -(r[1] - r[0])))
    kept = []
    for r in runs:
        if kept and r[0] < kept[-1][1]:
            if r[1] - r[0] > kept[-1][1] - kept[-1][0]:
                kept[-1] = r
            continue
        kept.append(r)
    return kept


def quotes(spoken: list[str], part: list[str]) -> list[tuple[int, int]]:
    """Maximal runs [i, j) of the spoken words that occur in the part, kept when
    they are a quote (see the module's docstring)."""
    out = []
    n, m = len(spoken), len(part)
    best = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if spoken[i] == part[j]:
                best[i][j] = best[i + 1][j + 1] + 1
    for i in range(n):
        for j in range(m):
            k = best[i][j]
            if not k or (i and j and spoken[i - 1] == part[j - 1]):
                continue                      # not the start of a maximal run
            run = spoken[i:i + k]
            c = content(run)
            whole = k == m and m <= 4 and c
            if len(c) >= 2 or whole:
                out.append((i, i + k))
    return dedupe(out)


def docs_of(block_ids: list[str], blocks: dict) -> list[dict]:
    """The documents among a board's blocks; a map of the texts (bundle 1.14)
    is each of its texts, with its own rows."""
    out = []
    for bid in block_ids:
        b = blocks.get(bid) or {}
        if b.get("doc"):
            out.append(b)
        for d in (b.get("map") or {}).get("docs") or []:
            out.append({"doc": d, "rows": b["rows"][d["first"]:d["first"] + d["count"]]})
    return out


def in_questions(run: list[str], questions: list[list[str]]) -> bool:
    """The run is words of a question on the board: reading the question aloud
    is not reading the text, even where a heading of the text has the word."""
    k = len(run)
    return any(q[i:i + k] == run for q in questions for i in range(len(q) - k + 1))


def questions_of(block_ids: list[str], blocks: dict) -> list[list[str]]:
    """The words that are read from something other than the text: a
    question's wording and (bundle 1.15) each of its options, and a word-bank
    gloss's word and example. Reading them is not reading the text, even where
    the text has the same words."""
    out = []
    for b in block_ids:
        x = blocks.get(b) or {}
        if x.get("question"):
            out.append(tokens(x.get("text") or ""))
            out += [tokens(o["text"]) for o in x["question"].get("options") or []]
            if x["question"].get("options_later"):
                # 1.17, a Part C question: its reason labels are read from the question
                out += [tokens(it.get("text") or "") for it in x.get("items") or [] if it.get("text")]
        elif x.get("vocab") or x.get("lexicon"):      # a word-bank gloss (screens; bundle)
            out += [tokens(x.get(k) or "") for k in ("term", "text")]
            if x.get("synonym") is not None and x.get("explanation"):
                # its meaning and synonym too (found on Part C, 2026-10-08: a gloss's
                # meaning read aloud shared two words with the text)
                out += [tokens(x.get(k) or "") for k in ("explanation", "synonym")]
    return out


NOTE_TYPES = ("plain", "callout", "answer_row", "term_box")


def notes_of(block_ids: list[str], blocks: dict) -> list[list[str]]:
    """The words of the notes shown in a state of a Part C question board (1.17:
    the learner's own answer, the paraphrase note), read from the note on the
    board, not from the text, even where the note repeats the text's words."""
    out = []
    for b in block_ids:
        x = blocks.get(b) or {}
        if x.get("type") in NOTE_TYPES and not x.get("question") and x.get("text"):
            out.append(tokens(x["text"]))
    return out


def part_c_board(block_ids: list[str], blocks: dict) -> bool:
    return any(((blocks.get(b) or {}).get("question") or {}).get("options_later") for b in block_ids)


def board_blocks(bd: dict) -> list[str]:
    """Every block a board shows in any state: a pinned question stays from
    its reveal, so it is read in later states too."""
    out = list(bd["fixed"])
    for st in bd["states"]:
        out += [i for i in st["working"] if i not in out]
    return out


def utterance_quotes(text_with_cues: str, cues: list[dict], docs: list[dict],
                     questions: list[list[str]] = ()) -> tuple[int, list[str]]:
    """Before synthesis: the quotes of an utterance, and those with no mark
    whose cue marker stands at most LEAD_WORDS words before them or in them."""
    spoken, marker_at = [], {}
    for piece in re.split(r"(\{\{c\d+\}\})", text_with_cues):
        m = re.fullmatch(r"\{\{(c\d+)\}\}", piece)
        if m:
            marker_at[m.group(1)] = len(spoken)
        else:
            spoken += tokens(piece)
    marks = [c for c in cues if c["type"] in MARKS]
    label = {}
    for doc in docs:
        for p in parts(doc):
            for r in quotes(spoken, p):
                label.setdefault(r, doc["doc"]["label"])
    runs = [r for r in dedupe(list(label)) if not in_questions(spoken[r[0]:r[1]], questions)]
    bad = []
    for i, j in runs:
        words = content(spoken[i:j])
        # a mark covers its whole phrase: from its marker to the end of its words
        if not any(i - LEAD_WORDS - len(tokens(c.get("text") or "")) <= marker_at.get(c["id"], -99) <= j - 1
                   and content(tokens(c.get("text") or "")) & words for c in marks):
            bad.append(f"\"{' '.join(spoken[i:j])}\" ({label[(i, j)]})")
    return len(runs), bad


def parts(doc: dict) -> list[list[str]]:
    return [tokens(" ".join(r)) for r in doc["rows"]]


def mmss(s: float) -> str:
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


def check_player(lesson: Path) -> tuple[int, list[str]]:
    d = lesson / "generated" / "lesson-player"
    bundle = json.loads((d / "bundle.json").read_text(encoding="utf-8"))
    t = json.loads((d / "timeline.json").read_text(encoding="utf-8"))
    blocks = bundle["blocks"]
    url = "file:///" + str(d / "player.html").replace("\\", "/")
    indexes: dict[Path, dict] = {}
    found, failures = 0, []
    for bd in t["boards"]:
        for st in bd["states"]:
            docs = docs_of(bd["fixed"] + st["working"], blocks)
            if not docs:
                continue
            for u in st["utterances"]:
                if not u.get("audio_file"):
                    raise SystemExit(f"{u['id']} has no audio: run on a narrated player, or use --narration")
                clip = (d / u["audio_file"]).resolve()
                ip = clip.parent.parent / "audio_index.json"
                if ip not in indexes:
                    indexes[ip] = {e["file"]: e for e in json.loads(ip.read_text(encoding="utf-8")).values()}
                e = indexes[ip][f"audio/{clip.name}"]
                # the voice's words, each with its time in the lesson
                spoken, at = [], []
                for w, a, b in zip(e["words"], e["word_start"], e["word_end"]):
                    for tok in tokens(w):
                        spoken.append(tok)
                        at.append((u["start"] + a - (u.get("clip_in") or 0), u["start"] + b - (u.get("clip_in") or 0)))
                marks = [c for c in u["cues"] if c["type"] in MARKS]
                label = {}
                for doc in docs:
                    for p in parts(doc):
                        for r in quotes(spoken, p):
                            label.setdefault(r, doc["doc"]["label"])
                qs = questions_of(board_blocks(bd), blocks)
                if part_c_board(board_blocks(bd), blocks):      # 1.17: the state's notes too
                    qs += notes_of(bd["fixed"] + st["working"], blocks)
                for i, j in [r for r in dedupe(list(label)) if not in_questions(spoken[r[0]:r[1]], qs)]:
                            found += 1
                            doc_label = label[(i, j)]
                            t0, t1 = at[i][0], at[j - 1][1]
                            words = content(spoken[i:j])
                            # a mark covers its whole phrase (about 0.4 s a word)
                            ok = any(t0 - LEAD_S - 0.4 * len(tokens(c.get("text") or "")) <= c["time"] <= t1 + TAIL_S
                                     and content(tokens(c.get("text") or "")) & words for c in marks)
                            if not ok:
                                failures.append(f"{u['id']}: \"{' '.join(spoken[i:j])}\" ({doc_label}) "
                                                f"unmarked  {url}?t={int(t0)} ({mmss(t0)})")
    return found, failures


def check_narration(lesson: Path) -> tuple[int, list[str]]:
    info = json.loads((lesson / "analysis" / "sections.json").read_text(encoding="utf-8"))
    found, failures = 0, []
    for sec in info["sections"]:
        pages = sec["pages"]
        sp = paths.screens_dir_for(lesson, pages) / "screens.json"
        np_ = paths.narration_dir_for(lesson, pages) / "narration.json"
        if not sp.exists() or not np_.exists():
            continue
        sc = json.loads(sp.read_text(encoding="utf-8"))
        na = json.loads(np_.read_text(encoding="utf-8"))
        blocks = {b["id"]: b for tp in sc["topics"] for h in tp["thoughts"] for b in h["blocks"]}
        plan = {bd["id"]: bd for bd in sc["boards"]}
        for nb in na["boards"]:
            bd = plan.get(nb["id"])
            if not bd:
                continue
            for s in nb["states"]:
                working = next((x["working"] for x in bd["states"] if x["id"] == s["id"]), [])
                docs = docs_of(bd["fixed"] + working, blocks)
                if not docs:
                    continue
                qs = questions_of(board_blocks(bd), blocks)
                if part_c_board(board_blocks(bd), blocks):      # 1.17: the state's notes too
                    qs += notes_of(bd["fixed"] + working, blocks)
                for u in s["utterances"]:
                    n, bad = utterance_quotes(u["text_with_cues"], u["cues"], docs, qs)
                    found += n
                    failures += [f"{paths.section_tag(pages)} {u['id']}: {x} unmarked" for x in bad]
    return found, failures


def main() -> int:
    lesson = Path(sys.argv[1])
    found, failures = (check_narration if "--narration" in sys.argv else check_player)(lesson)
    for f in failures:
        print("FAIL " + f)
    print(f"{lesson.name}: {found} document phrase(s) spoken, {found - len(failures)} marked, "
          f"{len(failures)} unmarked")
    if failures:
        print("doc marks check FAILED: every phrase of a document read aloud needs a highlight or "
              "keyword pair timed to it")
        return 1
    print("doc marks check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
