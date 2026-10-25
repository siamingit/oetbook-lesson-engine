"""The public course index: what each lesson teaches, and where (docs/adr/038-public-course-index.md).

    .venv/Scripts/python spike/scripts/build_public_course_index.py <lesson_dir or lessons_dir>
    .venv/Scripts/python spike/scripts/build_public_course_index.py --check <lessons_dir>
    .venv/Scripts/python spike/scripts/build_public_course_index.py --verify

Writes docs/course-index.json (schema docs/course-index.schema.json) and
docs/course-index.md, whole, from every built lesson in the lessons folder (a
lesson folder names its lessons folder, C:\\OET\\lessons). This index is in the
public repository, so it holds summaries and ids only: no narration, no board
text beyond its titles, rules and terms, no practice-set text, answers or
word-bank meanings (ADR 026), no Listening panel words (ADR 031). The full
index, with every word of every lesson, stays outside the repository
(build_course_index.py, docs/05-COURSE-INDEX.md).

By code only, from files on disk (AGENTS.md §8):

  - the bundle (generated/lesson-player/bundle.json): sections, boards, times,
    rules, terms, glosses, practice questions, references;
  - each section's screens (analysis/screens/<section>/screens.json): the
    topic title of each board and the purpose of each thought, its teaching
    points, timed by the blocks the thought shows;
  - analysis/sections.json, gates.json, preflight.json, practice_set.json and
    the source recording;
  - docs/listening-facts.md, for the text of each Listening fact;
  - spike/course_index/curated.json, the one reviewed file written by hand:
    where each OET fact and exam method is taught (by utterance or board id),
    what the docs record about each source session, topics that continue in
    another lesson, and topics for the topic index that no board names.

Times are resolved from ids on every build, so a re-voiced lesson needs no
edit. The same inputs give byte-identical files.

--check builds in memory and fails when the committed files differ (the
index is out of date with the lesson data). --verify needs no lesson data
(CI): the JSON against its schema, the Markdown against the JSON, every lesson
of the curated file in the index and back, and every reference resolved.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
JSON_OUT = DOCS / "course-index.json"
MD_OUT = DOCS / "course-index.md"
SCHEMA = DOCS / "course-index.schema.json"
CURATED = ROOT / "spike" / "course_index" / "curated.json"
FACTS_MD = DOCS / "listening-facts.md"

FORMAT = "oetbook-public-course-index"
SCHEMA_VERSION = "1.1"           # 1.1 (2026-10-25): the Writing course
COURSES = [("grammar", "Grammar"), ("vocabulary", "Vocabulary"),
           ("reading", "Reading"), ("listening", "Listening"), ("writing", "Writing")]
PRACTICE_COURSES = ("reading", "listening")

# A thought's or a board's label may open with the layout's own words (ADR 007,
# ADR 026, ADR 029): they say where it sits, not what it teaches.
LAYOUT = re.compile(r"^(?:Table|Covered|Merged|Split|Fixed layer|Map(?: P\d+(?:-\d+)?)?|Paras? \d+(?:-\d+)?"
                    r"|Row [A-Z]?\d+|Text [A-D]|Zoom [A-D])\s*:\s*")
FIXED = re.compile(r"^(?:(?:Put|Show) )?(.+?) (?:on the board )?as the fixed layer\.?$")
# On a board that solves a practice question, a letter naming an option or a
# text could give the key away (ADR 026): it is replaced.
LETTERS = [(re.compile(r"\b[Oo]ptions [A-D](?:,? (?:and|or) [A-D])?\b"), "options"),
           (re.compile(r"\b[Oo]ption [A-D]\b"), "an option"),
           (re.compile(r"\b(?:[Tt]exts?|Zoom) [A-D]\d*\b"), "the text"),
           (re.compile(r"\b[A-D] is (out|the answer|right|correct|wrong|ruled out)\b"),
            r"an option is \1")]
WITHHELD_TITLE = "(title withheld: it names a practice answer)"
QUESTION_WORD = re.compile(r"\b([Ii]tems?|[Qq]uestions?) (\d+)\b")
# Term boxes whose label names a concept go into the topic index; those that
# teach a new word or phrase go into the vocabulary.
CONCEPT_LABELS = {"form", "grammar term", "new term", "grammar word", "term", "grammar", "time words",
                  "punctuation mark", "punctuation", "signal word", "signal words", "question type",
                  "joining words", "joining word", "linking word", "linking words", "reading word",
                  "reading skill", "usage", "key word", "key term", "key idea", "listen for", "tense",
                  "name", "method", "rule", "memory word", "relative pronoun", "relative pronouns",
                  "word endings", "prefix", "short form", "abbreviation", "abbreviations",
                  "case-note short form", "word class", "articles", "style", "new form", "step",
                  "step 1", "step 2", "step 3", "step 4", "step 5", "technique 1", "technique 2"}
WORD_LABELS = {"new word", "new words", "new phrase", "phrase", "word", "word to learn",
               "phrase to learn", "useful phrase", "useful verb", "case note word"}
NOT_A_TOPIC = re.compile(r"^(?:Introduction|Closing|Practice\b|(?:Question|Questions|Item|Text|Texts|Extract) \d)")


def read(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def mmss(t: float | None) -> str | None:
    if t is None:
        return None
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def at(t: float) -> dict:
    return {"start_s": round(t, 3), "start": mmss(t)}


def clean(text: str) -> str:
    prev = None
    text = (text or "").strip()
    while prev != text:
        prev = text
        text = LAYOUT.sub("", text, count=1).strip()
    m = FIXED.match(text)
    return m.group(1) if m else text


def neutral(text: str) -> str:
    for pat, rep in LETTERS:
        text = pat.sub(rep, text)
    return text


def norm_key(text: str) -> str:
    t = re.sub(r"[\"'‘’“”]", "", text.casefold())
    return re.sub(r"\s+", " ", t).strip(" .,:;!?")


# ---------------------------------------------------------------------------
# Inputs outside the lessons
# ---------------------------------------------------------------------------

def listening_facts() -> dict[int, str]:
    """Fact number -> the fact as docs/listening-facts.md states it."""
    out = {}
    for line in FACTS_MD.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            out[int(m.group(1))] = m.group(2)
    return out


def curated() -> dict:
    return read(CURATED)


_ANSWERS: dict[str, tuple] = {}
RUN = 6          # this many words in a row of a set's own wording is the set's text (ADR 026)
ID_KEYS = {"item_id", "stimulus_id", "set_id", "option_id", "gap_id", "id", "content_hash"}


def set_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in ID_KEYS:
                yield from set_strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from set_strings(v)


def own_answers(set_id: str) -> tuple[list, set, set]:
    """A practice set, from the local release copies: every answer form
    (check_release_answers.answers) as whole-word patterns, every run of RUN
    words of its wording (texts, transcripts, stems, options, feedback), and
    its texts' titles. A lesson's line that names an answer or holds such a run
    is left out of the index: it is the set's content (ADR 026). With no local
    release holding the set, nothing can be checked, and the build stops."""
    if set_id not in _ANSWERS:
        import check_release_answers as cra
        forms, runs, titles, found = [], set(), set(), False
        for p in cra.local_packages():
            for s in read(p).get("sets") or []:
                if s.get("set_id") != set_id:
                    continue
                found = True
                forms += [a for _, _, a in cra.answers(s)]
                for text in set_strings(s):
                    w = cra.norm(text).split()
                    runs.update(tuple(w[k:k + RUN]) for k in range(len(w) - RUN + 1))
                for st in (st for part in s.get("parts") or [] for st in part.get("stimuli") or []):
                    if st.get("title"):        # "Text 1: Stopping ...", with and without its label
                        titles.add(cra.norm(st["title"]))
                        titles.add(cra.norm(re.sub(r"^[^:]*:\s*", "", st["title"])))
        if not found:
            raise SystemExit(f"REFUSED: no local exercises release holds {set_id}; its answers cannot "
                             f"be kept out of the public index")
        _ANSWERS[set_id] = ([re.compile(r"(?<![a-z0-9])" + re.escape(a) + r"(?![a-z0-9])")
                             for a in dict.fromkeys(forms)], runs, titles)
    return _ANSWERS[set_id]


# ---------------------------------------------------------------------------
# One lesson
# ---------------------------------------------------------------------------

class Lesson:
    """A built lesson's data, with every id resolved to its time."""

    def __init__(self, L: Path):
        import paths
        self.L = L
        self.id = paths.lesson_id(L)
        self.bundle = read(L / "generated" / "lesson-player" / "bundle.json")
        self.blocks = self.bundle["blocks"]
        self.boards = {b["id"]: b for b in self.bundle["boards"]}
        self.sections = {s["id"]: s for s in self.bundle["sections"]}
        self.course = self.id.split("-")[0]
        self.reveal: dict[str, float] = {}
        self.block_board: dict[str, str] = {}
        self.utterances: dict[str, dict] = {}
        for bd in self.bundle["boards"]:
            for i in bd["fixed"]:
                self._seen(i, bd["start"], bd["id"])
            for s in bd["states"]:
                for i, t in (s.get("reveal") or {}).items():
                    if i in self.blocks:
                        self._seen(i, t, bd["id"])
                for u in s["utterances"]:
                    self.utterances[u["id"]] = {"board": bd["id"], "section": bd["section"], **u}
        for i, b in self.blocks.items():          # a folded block is shown inside another
            if i not in self.reveal and b.get("fold_into") in self.reveal:
                self._seen(i, self.reveal[b["fold_into"]], self.block_board[b["fold_into"]])
        self.practice_boards = {bid for bid, bd in self.boards.items() if self._practice_board(bd)}
        self.ps = None
        if (L / "analysis" / "practice_set.json").exists():
            import practice_set
            self.ps = practice_set.load(L)
        self.answers, self.runs, self.text_titles = own_answers(self.ps["set_id"]) if self.ps else ([], set(), set())
        self.withheld = 0
        self.renumber = self._renumber()

    def names_answer(self, text: str) -> bool:
        """True for a line that names an answer of the lesson's set or quotes its wording."""
        import check_release_answers as cra
        low = cra.norm(text or "")
        if any(p.search(low) for p in self.answers):
            return True
        w = low.split()
        return any(tuple(w[k:k + RUN]) in self.runs for k in range(len(w) - RUN + 1))

    def section_title(self, title: str) -> str:
        """"Practice: Text 2 — <the release's title of the text>" keeps its first part."""
        import check_release_answers as cra
        head, sep, tail = title.partition(" — ")
        return head if sep and cra.norm(tail) in self.text_titles else title

    def keep(self, text: str) -> bool:
        """False, and counted, for a line that names an answer of the lesson's set."""
        if self.names_answer(text):
            self.withheld += 1
            return False
        return True

    def must_not_name_answer(self, text: str, what: str) -> None:
        if self.names_answer(text):
            raise SystemExit(f"REFUSED: {self.id}: {what} names an answer of {self.ps['set_id']}; "
                             f"reword it (the public index never holds an answer, ADR 026)")

    def _seen(self, i: str, t: float, board: str) -> None:
        if i not in self.reveal or t < self.reveal[i]:
            self.reveal[i] = t
            self.block_board[i] = board

    def _practice_board(self, bd: dict) -> bool:
        if self.course not in PRACTICE_COURSES:
            return False
        if bd.get("listen"):
            return True
        ids = list(bd["fixed"]) + [i for s in bd["states"] for i in s["working"]]
        return any(self.blocks[i].get("question") or
                   (self.blocks[i].get("doc") or {}).get("text_type") == "form" for i in ids)

    def _renumber(self) -> dict[int, int]:
        """A lesson that numbers its questions from 1 (ADR 026 amendment of
        2026-10-08) still names some boards by the real test's number ("Item
        7"); the index uses the lesson's number, as the learner sees it."""
        if not self.ps or self.ps.get("numbering") != "lesson":
            return {}
        import practice_set
        items = practice_set.items(self.ps)
        return {practice_set.exam_number(items[i]): practice_set.number(self.ps, items[i])
                for i in self.ps["lesson_items"]}

    def label(self, text: str, board: str | None) -> str:
        text = clean(text)
        if self.renumber:
            text = QUESTION_WORD.sub(lambda m: f"{m.group(1)} {self.renumber.get(int(m.group(2)), int(m.group(2)))}", text)
        if board in self.practice_boards:
            text = neutral(text)
        return text

    def section_blocks(self, sec: dict) -> list[str]:
        ids = []
        for bid in sec["boards"]:
            bd = self.boards[bid]
            for i in list(bd["fixed"]) + [i for s in bd["states"] for i in s["working"]]:
                if i not in ids:
                    ids.append(i)
        return sorted(ids, key=lambda i: (self.reveal.get(i, 1e9), ids.index(i)))

    def resolve(self, ref: str) -> dict:
        """An anchor of the curated file: an utterance, block, board or section id."""
        if ref in self.utterances:
            u = self.utterances[ref]
            return {"section": u["section"], "board": u["board"], "utterance": ref, **at(u["start"])}
        if ref in self.boards:
            b = self.boards[ref]
            return {"section": b["section"], "board": ref, **at(b["start"])}
        if ref in self.reveal:
            return {"section": self.boards[self.block_board[ref]]["section"],
                    "board": self.block_board[ref], "block": ref, **at(self.reveal[ref])}
        if ref in self.sections:
            return {"section": ref, **at(self.sections[ref]["start"])}
        raise SystemExit(f"REFUSED: {self.id}: curated anchor {ref!r} is not an utterance, block, "
                         f"board or section of the lesson (spike/course_index/curated.json)")


def section_kind(L: Lesson, sec: dict, config: dict) -> str:
    if sec["intro"]:
        return "intro"
    if not sec["pages"]:
        import paths
        for a in config.get("added") or []:
            if paths.section_tag([a["page"]]) == sec["id"]:
                return a.get("kind") or "authored"
        return "authored"
    return "deck"


def topics_of(L: Lesson, sec: dict) -> list[dict]:
    screens = read(L.L / "analysis" / "screens" / sec["id"] / "screens.json")
    tops = {t["id"]: t for t in screens["topics"]}
    out = []
    for bid in sec["boards"]:
        t = tops[bid.rsplit("_", 1)[1]]
        points = []
        for n, th in enumerate(t["thoughts"]):
            ids = [f"{sec['id']}_{b['id']}" for b in th.get("blocks") or []]
            shown = [i for i in ids if i in L.reveal and L.block_board.get(i) == bid]
            if not shown:
                continue                       # taken out of the lesson, or shown on no board of its own
            first = min(shown, key=lambda i: L.reveal[i])
            text = L.label(th.get("purpose") or "", bid)
            if text and L.keep(text):
                points.append((L.reveal[first], n, {"text": text, "block": first, **at(L.reveal[first])}))
        points.sort(key=lambda p: (p[0], p[1]))
        kept = []
        for _, _, p in points:                  # one line for a run of the same point
            if not kept or kept[-1]["text"] != p["text"]:
                kept.append(p)
        title = L.label(t.get("title") or "", bid)
        if not L.keep(title):
            title = WITHHELD_TITLE
        out.append({"board": bid, "title": title, **at(L.boards[bid]["start"]), "points": kept})
    return out


def section_entry(L: Lesson, sec: dict, config: dict) -> dict:
    import practice_set
    rules, terms, wrong, practice = [], [], [], []
    seen_q = set()
    for i in L.section_blocks(sec):
        b = L.blocks[i]
        if i not in L.reveal:
            continue
        board = L.block_board[i]
        when = at(L.reveal[i])
        if b["type"] == "callout":
            text = L.label(b.get("text") or "", board)
            if L.keep(text):
                rules.append({"block": i, "kind": "warning" if b.get("kind") == "warning" else "rule",
                              "text": text, **when})
        elif b["type"] == "term_box" and b.get("label") != "WORD":
            term = L.label(b.get("term") or "", board)
            if L.keep(f"{b.get('label')} {term}"):
                terms.append({"block": i, "label": b.get("label"), "term": term, **when})
        elif b["type"] == "error_row" and L.course not in PRACTICE_COURSES:
            wrong.append({"block": i, "text": b.get("text"), **when})
        elif b.get("question") and L.ps:
            item = b["question"]["item"]
            if item in seen_q:
                continue
            seen_q.add(item)
            it = practice_set.items(L.ps)[item]
            practice.append({"item": item, "kind": b["question"].get("kind"),
                             "number": b.get("exercise_item"),
                             "real_test_number": practice_set.exam_number(it),
                             "board": board, **when})
        elif (b.get("doc") or {}).get("text_type") == "form":
            item = b["doc"].get("item")
            if item in seen_q:
                continue
            seen_q.add(item)
            gaps = [{"gap": p.get("gap"), "number": int(p["mark"])}
                    for p in b["doc"]["parts"] if p.get("kind") == "num"]
            practice.append({"item": item, "kind": "note-form", "number": None, "real_test_number": None,
                             "gaps": gaps, "board": board, **when})
    refs = []
    for bid in sec["boards"]:
        for s in L.boards[bid]["states"]:
            for u in s["utterances"]:
                for r in u.get("refs") or []:
                    refs.append({"utterance": u["id"], "lesson": r["lesson"], "section": r.get("section"),
                                 "provenance": u.get("provenance"), **at(u["start"])})
    title = L.section_title(sec["title"])
    title = title if L.keep(title) else WITHHELD_TITLE
    return {"id": sec["id"], "title": title, "kind": section_kind(L, sec, config),
            "pages": sec["pages"], "category": sec.get("category"),
            **at(sec["start"]), "end_s": round(sec["end"], 3),
            "topics": topics_of(L, sec), "rules": rules, "terms": terms,
            "wrong_examples": wrong, "practice": practice, "refs": refs}


def vocabulary_of(L: Lesson) -> tuple[list[dict], int]:
    """Every glossed word and word-bank item, at its first moment in the lesson;
    and how many Listening panel words are left out (ADR 031: never in git)."""
    out, seen, panel = [], set(), set()
    for i in sorted(L.reveal, key=lambda i: (L.reveal[i], i)):
        b = L.blocks[i]
        if b["type"] == "gloss" and b.get("panel"):
            panel.add(norm_key(b.get("term") or ""))
            continue
        new_word = b["type"] == "term_box" and (b.get("label") or "").casefold() in WORD_LABELS
        if not (b["type"] == "gloss" or new_word or (b["type"] == "term_box" and b.get("label") == "WORD")):
            continue
        key = b.get("lexicon") or norm_key(b.get("term") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        if not L.keep(b.get("term") or ""):
            continue
        bd = L.block_board[i]
        kind = "word-bank" if b.get("lexicon") else "new-word" if new_word else "gloss"
        out.append({"word": (b.get("term") or "").strip(), "kind": kind,
                    "lexicon": b.get("lexicon"), "section": L.boards[bd]["section"], "block": i,
                    **at(L.reveal[i])})
    return out, len(panel)


def practice_set_of(L: Lesson) -> dict | None:
    if not L.ps:
        return None
    rel = L.ps.get("release") or {}
    recs = {}
    for u in L.utterances.values():
        if u.get("kind") == "exam":
            e = u["exam"]
            r = recs.setdefault(e["stimulus"], {"stimulus": e["stimulus"], "label": e.get("label"),
                                                "plays": 0, **at(u["start"])})
            r["plays"] += 1
            if u["start"] < r["start_s"]:
                r.update(at(u["start"]))
    numbering = L.ps.get("numbering") or ("practice" if L.course == "listening" else "release")
    return {"set": L.ps["set_id"],
            "release": {"package_id": rel.get("package_id") or rel.get("id"),
                        "package_version": rel.get("package_version") or rel.get("version")},
            "numbering": numbering,
            "recordings": sorted(recs.values(), key=lambda r: r["start_s"])}


def deck_exercises_of(L: Lesson) -> list[dict]:
    if L.course in PRACTICE_COURSES:
        return []
    out = []
    for sec in L.bundle["sections"]:
        nums = sorted({L.blocks[i]["exercise_item"] for i in L.section_blocks(sec)
                       if L.blocks[i].get("exercise_item") and not L.blocks[i].get("question")})
        if nums:
            out.append({"section": sec["id"], "items": nums})
    return out


def source_of(L: Lesson) -> dict:
    from library_inventory import partial_hash
    pf = L.L / "analysis" / "preflight.json"
    pf = read(pf) if pf.exists() else {}
    video, deck = L.L / "source" / "video.mp4", L.L / "source" / "slides.pdf"
    return {"folder": "source",
            "recording": "source/video.mp4" if video.exists() else None,
            "recording_duration_s": (pf.get("video") or {}).get("duration_s"),
            "recording_partial_hash": partial_hash(video, video.stat().st_size) if video.exists() else None,
            "deck": "source/slides.pdf" if deck.exists() else None,
            "deck_pages": pf.get("deck_pages"),
            "same_recording_as": [], "note": None}


def lesson_entry(L: Lesson, cur: dict, facts_text: dict) -> dict:
    config = read(L.L / "analysis" / "sections.json")
    gates = L.L / "analysis" / "gates.json"
    final = read(gates).get("final") if gates.exists() else None
    meta = cur.get("lessons", {}).get(L.id, {})
    src = source_of(L)
    src["note"] = meta.get("session")
    sections = [section_entry(L, s, config) for s in L.bundle["sections"]]
    vocab, panel = vocabulary_of(L)
    facts = []
    for f in meta.get("facts") or []:
        key = f["fact"]
        text = facts_text.get(key) if isinstance(key, int) else (cur.get("facts") or {}).get(key)
        if not text:
            raise SystemExit(f"REFUSED: {L.id}: fact {key!r} has no text (docs/listening-facts.md or "
                             f"the curated file's facts)")
        # a Listening fact's text is the public fact sheet's; the curated words are checked
        L.must_not_name_answer(f.get("note") or "" if isinstance(key, int) else f"{text} {f.get('note') or ''}",
                               f"fact {key!r}")
        facts.append({"fact": key, "text": text, "note": f.get("note"), **L.resolve(f["at"])})
    methods = []
    for m in meta.get("methods") or []:
        L.must_not_name_answer(f"{m['name']} {m['text']}", f"method {m['name']!r}")
        methods.append({"name": m["name"], "text": m["text"], **L.resolve(m["at"])})
    for x in [meta.get("session") or ""] + [t["topic"] for t in meta.get("topics") or []] + \
            [c["why"] for c in meta.get("continues_in") or []]:
        L.must_not_name_answer(x, "a curated line")
    nxt = [{"lesson": a["next"], "why": "the closing names it as the next lesson", "source": "closing"}
           for a in config.get("added") or [] if a.get("kind") == "closing" and a.get("next")]
    nxt += [{"lesson": c["lesson"], "why": c["why"], "source": "curated"} for c in meta.get("continues_in") or []
            if c["lesson"] not in {n["lesson"] for n in nxt}]
    return {"id": L.id, "folder": L.L.name, "title": L.bundle["lesson"]["title"],
            "description": L.bundle["lesson"].get("description"),
            "course": L.course, "order": int(L.id.split("-")[1]),
            "length_s": round(L.bundle["meta"]["total_duration_s"], 3),
            "length": mmss(L.bundle["meta"]["total_duration_s"]),
            "bundle_format": L.bundle["format_version"],
            "status": "approved" if final else "built",
            "approval": {"by": final["by"], "on": final["on"]} if final else None,
            "source": src,
            "categories": [{"id": c["id"], "title": c["title"], "sections": c["sections"]}
                           for c in L.bundle["lesson"].get("categories") or []],
            "sections": sections,
            "facts": sorted(facts, key=lambda f: f["start_s"]),
            "methods": sorted(methods, key=lambda m: m["start_s"]),
            "vocabulary": vocab,
            "withheld": {"listening_panel_words": panel, "lines_naming_an_answer": L.withheld},
            "practice_set": practice_set_of(L), "deck_exercises": deck_exercises_of(L),
            "links": {"refers_to": [], "referred_to_by": [], "continues_in": nxt, "continues_from": []},
            "topics": [{"topic": t["topic"], **L.resolve(t["at"])} for t in meta.get("topics") or []]}


# ---------------------------------------------------------------------------
# The whole index
# ---------------------------------------------------------------------------

def lessons_dir_of(target: Path) -> Path:
    target = target.resolve()
    return target.parent if (target / "analysis").is_dir() else target


def built_lessons(lessons_dir: Path) -> list[Path]:
    known = {c for c, _ in COURSES}
    return [p for p in sorted(lessons_dir.iterdir())
            if p.is_dir() and not p.name.startswith("_") and p.name.split("-")[0] in known
            and (p / "generated" / "lesson-player" / "bundle.json").exists()]


def build(lessons_dir: Path) -> dict:
    cur = curated()
    facts_text = listening_facts()
    entries = [lesson_entry(Lesson(L), cur, facts_text) for L in built_lessons(lessons_dir)]
    order = {c: n for n, (c, _) in enumerate(COURSES)}
    entries.sort(key=lambda e: (order[e["course"]], e["order"], e["id"]))
    by_id = {e["id"]: e for e in entries}

    by_hash: dict[str, list[str]] = {}
    for e in entries:
        h = e["source"]["recording_partial_hash"]
        if h:
            by_hash.setdefault(h, []).append(e["id"])
    for e in entries:
        h = e["source"]["recording_partial_hash"]
        e["source"]["same_recording_as"] = [i for i in by_hash.get(h, []) if i != e["id"]] if h else []

    for e in entries:                       # references, both ways
        seen = set()
        for s in e["sections"]:
            for r in s["refs"]:
                tgt = by_id.get(r["lesson"])
                if not tgt:
                    raise SystemExit(f"REFUSED: {e['id']} {r['utterance']} refers to {r['lesson']!r}, "
                                     f"which is not a built lesson")
                if r["section"] and not any(x["id"] == r["section"] for x in tgt["sections"]):
                    raise SystemExit(f"REFUSED: {e['id']} {r['utterance']} refers to section "
                                     f"{r['section']!r} of {r['lesson']}, which it does not have")
                key = (r["lesson"], r["section"])
                if key not in seen:
                    seen.add(key)
                    e["links"]["refers_to"].append({"lesson": r["lesson"], "section": r["section"],
                                                    "from_section": s["id"], "utterance": r["utterance"],
                                                    "start_s": r["start_s"], "start": r["start"]})
                    tgt["links"]["referred_to_by"].append({"lesson": e["id"], "section": s["id"],
                                                           "to_section": r["section"],
                                                           "utterance": r["utterance"],
                                                           "start_s": r["start_s"], "start": r["start"]})
        for c in e["links"]["continues_in"]:
            if c["lesson"] not in by_id:
                raise SystemExit(f"REFUSED: {e['id']} continues in {c['lesson']!r}, which is not a built lesson")
            by_id[c["lesson"]]["links"]["continues_from"].append({"lesson": e["id"], "why": c["why"],
                                                                  "source": c["source"]})

    courses = [{"id": c, "title": t, "lessons": [e["id"] for e in entries if e["course"] == c]}
               for c, t in COURSES]
    index = {"format": FORMAT, "schema_version": SCHEMA_VERSION,
             "about": "What each lesson teaches, and where. Generated by "
                      "spike/scripts/build_public_course_index.py; never edited by hand "
                      "(docs/adr/038-public-course-index.md).",
             "courses": courses, "lessons": entries, "topic_index": topic_index(entries)}
    index["totals"] = totals(index)
    return index


def topic_index(entries: list[dict]) -> list[dict]:
    """Topics and terms -> the lessons and moments that teach them: every
    section title that names a topic, every term on a term box, and the
    curated topics; the first moment in each lesson."""
    found: dict[str, dict] = {}

    def add(name: str, e: dict, where: dict, kind: str) -> None:
        name = name.strip().rstrip(".")
        key = norm_key(name)
        if not key:
            return
        t = found.setdefault(key, {"topic": name, "key": key, "entries": {}})
        cur = t["entries"].get(e["id"])
        if cur is None or where["start_s"] < cur["start_s"]:
            t["entries"][e["id"]] = {"lesson": e["id"], "section": where["section"],
                                     "start_s": where["start_s"], "start": where["start"],
                                     "source": kind}

    for e in entries:
        for s in e["sections"]:
            if s["kind"] not in ("intro", "closing") and not NOT_A_TOPIC.match(s["title"]) \
                    and s["title"] != WITHHELD_TITLE:
                add(s["title"], e, {"section": s["id"], "start_s": s["start_s"], "start": s["start"]}, "section")
            for t in s["terms"]:
                if (t["label"] or "").casefold() in CONCEPT_LABELS and "," not in t["term"] \
                        and len(t["term"].split()) <= 6 and not t["term"][:1].isdigit():
                    add(t["term"], e, {"section": s["id"], "start_s": t["start_s"], "start": t["start"]}, "term")
        for t in e.pop("topics"):
            add(t["topic"], e, t, "curated")
    order = {e["id"]: n for n, e in enumerate(entries)}
    return [{"topic": t["topic"], "key": t["key"],
             "entries": sorted(t["entries"].values(), key=lambda x: (order[x["lesson"]], x["start_s"]))}
            for t in sorted(found.values(), key=lambda t: (t["key"], t["topic"]))]


def totals(index: dict) -> dict:
    ls = index["lessons"]
    secs = [s for e in ls for s in e["sections"]]
    return {"lessons": len(ls), "sections": len(secs),
            "topics": sum(len(s["topics"]) for s in secs),
            "teaching_points": sum(len(t["points"]) for s in secs for t in s["topics"]),
            "rules": sum(1 for s in secs for r in s["rules"] if r["kind"] == "rule"),
            "warnings": sum(1 for s in secs for r in s["rules"] if r["kind"] == "warning"),
            "terms": sum(len(s["terms"]) for s in secs),
            "wrong_examples": sum(len(s["wrong_examples"]) for s in secs),
            "facts": sum(len(e["facts"]) for e in ls),
            "methods": sum(len(e["methods"]) for e in ls),
            "vocabulary": sum(len(e["vocabulary"]) for e in ls),
            "vocabulary_word_bank": sum(1 for e in ls for v in e["vocabulary"] if v["kind"] == "word-bank"),
            "practice_items": sum(len(s["practice"]) for s in secs),
            "references": sum(len(e["links"]["refers_to"]) for e in ls),
            "topic_index": len(index["topic_index"]),
            "withheld_panel_words": sum(e["withheld"]["listening_panel_words"] for e in ls),
            "withheld_answer_lines": sum(e["withheld"]["lines_naming_an_answer"] for e in ls)}


def to_json(index: dict) -> str:
    return json.dumps(index, ensure_ascii=False, indent=1) + "\n"


# ---------------------------------------------------------------------------
# The Markdown, generated from the JSON alone
# ---------------------------------------------------------------------------

def md_text(s: str | None) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().replace("<", "&lt;")


def markdown(ix: dict) -> str:
    titles = {e["id"]: e["title"] for e in ix["lessons"]}
    sec_titles = {(e["id"], s["id"]): s["title"] for e in ix["lessons"] for s in e["sections"]}
    t = ix["totals"]

    def where(lesson: str, section: str | None) -> str:
        s = sec_titles.get((lesson, section))
        return f"{titles.get(lesson, lesson)} (`{lesson}`)" + (f", \"{s}\"" if s else "")

    out = ["# Course index", "",
           "What each lesson teaches, and where. Generated from `docs/course-index.json` by "
           "`spike/scripts/build_public_course_index.py`; never edit it by hand. Schema: "
           f"`docs/course-index.schema.json`, version {ix['schema_version']}; decision: "
           "`docs/adr/038-public-course-index.md`.", "",
           f"{t['lessons']} lessons, {t['sections']} sections, {t['topics']} board topics, "
           f"{t['teaching_points']} teaching points, {t['rules']} rules and {t['warnings']} warnings, "
           f"{t['terms']} terms, {t['facts']} OET facts, {t['methods']} methods, "
           f"{t['vocabulary']} vocabulary items ({t['vocabulary_word_bank']} from the word bank), "
           f"{t['practice_items']} practice questions and note forms, {t['references']} links to "
           f"other lessons, {t['topic_index']} topics in the topic index.", "",
           "Times are minutes:seconds into the lesson's player. Ids (lessons, sections, boards, "
           "blocks, utterances) are the lesson bundle's (docs/04-LESSON-BUNDLE.md §4).", ""]
    for c in ix["courses"]:
        out += [f"- {c['title']}: " + ", ".join(f"[{titles[i]}](#{i})" for i in c["lessons"])]
    for c in ix["courses"]:
        out += ["", "---", "", f"# {c['title']}", ""]
        out += ["| # | Lesson | Lesson ID | Length | Sections | Approved |", "|---|---|---|---|---|---|"]
        for e in (x for x in ix["lessons"] if x["course"] == c["id"]):
            ap = f"{e['approval']['on']} ({e['approval']['by']})" if e["approval"] else "not yet"
            out.append(f"| {e['order']} | {md_text(e['title'])} | `{e['id']}` | {e['length']} | "
                       f"{len(e['sections'])} | {md_text(ap)} |")
        for e in (x for x in ix["lessons"] if x["course"] == c["id"]):
            out += lesson_md(e, where)
    out += ["", "---", "", "# Topic index", "",
            "Each topic or term, then each lesson that teaches it and the first moment there.", ""]
    for tp in ix["topic_index"]:
        out.append(f"- **{md_text(tp['topic'])}**: " + "; ".join(
            f"`{x['lesson']}` {x['start']}" for x in tp["entries"]))
    return "\n".join(out) + "\n"


def lesson_md(e: dict, where) -> list[str]:
    src = e["source"]
    out = ["", f"<a id=\"{e['id']}\"></a>", "", f"## {e['order']}. {md_text(e['title'])}", "",
           f"- Lesson ID and folder: `{e['id']}` (folder `{e['folder']}`); course {e['course']}, "
           f"lesson {e['order']}; length {e['length']}; bundle format {e['bundle_format']}",
           "- Status: " + (f"approved by {md_text(e['approval']['by'])}, {e['approval']['on']}"
                           if e["approval"] else "built, final gate not approved")]
    if e["description"]:
        out.append(f"- Description: {md_text(e['description'])}")
    rec = (f"`{src['recording']}`, {mmss(src['recording_duration_s'])} long, partial hash "
           f"`{src['recording_partial_hash']}`" if src["recording"] else "no recording")
    out.append(f"- Original session: folder `{src['folder']}`: {rec}; deck `{src['deck']}`, "
               f"{src['deck_pages']} pages"
               + (f"; the same recording as {', '.join('`' + i + '`' for i in src['same_recording_as'])}"
                  if src["same_recording_as"] else ""))
    out.append(f"  - {md_text(src['note'])}" if src["note"] else
               "  - The docs record nothing more about this session than its recording and deck.")
    if e["withheld"]["lines_naming_an_answer"]:
        out.append(f"- Left out: {e['withheld']['lines_naming_an_answer']} lines that name an answer of "
                   "the lesson's practice set or quote its wording (ADR 026)")
    if e["categories"]:
        out.append("- Parts: " + "; ".join(md_text(c["title"]) for c in e["categories"]))
    out += ["", "### Sections", ""]
    for s in e["sections"]:
        out += [f"#### {s['start']} {md_text(s['title'])} (`{s['id']}`, {s['kind']})", ""]
        for tp in s["topics"]:
            out.append(f"- {tp['start']} **{md_text(tp['title'])}**")
            out += [f"  - {p['start']} {md_text(p['text'])}" for p in tp["points"]]
        for kind, head in (("rule", "Rules on the boards"), ("warning", "Warnings (common mistakes)")):
            rs = [r for r in s["rules"] if r["kind"] == kind]
            if rs:
                out += ["", f"*{head}*", ""] + [f"- {r['start']} {md_text(r['text'])}" for r in rs]
        if s["wrong_examples"]:
            out += ["", "*Wrong sentences corrected*", ""]
            out += [f"- {w['start']} {md_text(w['text'])}" for w in s["wrong_examples"]]
        if s["terms"]:
            out += ["", "*Terms*: " + "; ".join(
                f"{md_text(x['term'])} ({md_text(x['label'])}, {x['start']})" for x in s["terms"])]
        if s["practice"]:
            out += ["", "*Practice*: " + "; ".join(practice_md(p) for p in s["practice"])]
        out.append("")
    if e["facts"]:
        out += ["### OET facts", ""]
        for f in e["facts"]:
            num = f"fact {f['fact']}" if isinstance(f["fact"], int) else f"`{f['fact']}`"
            out.append(f"- {f['start']} ({num}) {md_text(f['text'])}"
                       + (f" *({md_text(f['note'])})*" if f["note"] else ""))
        out.append("")
    if e["methods"]:
        out += ["### Exam methods and strategies", ""]
        out += [f"- {m['start']} **{md_text(m['name'])}**: {md_text(m['text'])}" for m in e["methods"]]
        out.append("")
    if e["vocabulary"] or e["withheld"]["listening_panel_words"]:
        out += ["### Vocabulary", "", "First moment each word is taught. Word-bank items carry their "
                "`lx:` ID; their meanings stay in the exercises repository.", ""]
        out += [f"- {v['start']} {md_text(v['word'])}" + (f" (`{v['lexicon']}`)" if v["lexicon"] else "")
                for v in e["vocabulary"]]
        if e["withheld"]["listening_panel_words"]:
            out.append(f"- Also {e['withheld']['listening_panel_words']} words of the recordings' "
                       "vocabulary panel, not listed here (ADR 031: some are answers).")
        out.append("")
    ps = e["practice_set"]
    if ps or e["deck_exercises"]:
        out += ["### Practice material", ""]
        if ps:
            out.append(f"- Practice set `{ps['set']}`, release `{ps['release']['package_id']}` version "
                       f"{ps['release']['package_version']}; numbering: {ps['numbering']}")
            for r in ps["recordings"]:
                out.append(f"  - {r['start']} recording `{r['stimulus']}` ({md_text(r['label'])}), "
                           f"played {r['plays']} times")
        for d in e["deck_exercises"]:
            out.append(f"- Deck exercise, section `{d['section']}`: items {', '.join(map(str, d['items']))}")
        out.append("")
    ln = e["links"]
    if any(ln.values()):
        out += ["### Links to other lessons", ""]
        out += [f"- {r['start']} refers to {where(r['lesson'], r['section'])} (in `{r['utterance']}`)"
                for r in ln["refers_to"]]
        out += [f"- referred to by {where(r['lesson'], r['section'])} at {r['start']}"
                + (f", about section `{r['to_section']}`" if r["to_section"] else "") for r in ln["referred_to_by"]]
        out += [f"- continues in {where(c['lesson'], None)}: {md_text(c['why'])}" for c in ln["continues_in"]]
        out += [f"- continues from {where(c['lesson'], None)}: {md_text(c['why'])}" for c in ln["continues_from"]]
        out.append("")
    return out


def practice_md(p: dict) -> str:
    if p["kind"] == "note-form":
        nums = [g["number"] for g in p["gaps"]]
        return f"note form `{p['item']}`, gaps {min(nums)}-{max(nums)} ({p['start']})"
    real = f", question {p['real_test_number']} in the real test" if p["real_test_number"] != p["number"] else ""
    return f"question {p['number']} `{p['item']}`{real} ({p['start']})"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def validate(value, schema: dict, root: dict | None = None, path: str = "$") -> list[str]:
    """The subset of JSON Schema that docs/course-index.schema.json uses."""
    root = root or schema
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        return validate(value, root["$defs"][name], root, path)
    errs = []
    types = schema.get("type")
    if types:
        types = [types] if isinstance(types, str) else types
        ok = {"string": isinstance(value, str), "null": value is None,
              "boolean": isinstance(value, bool),
              "integer": isinstance(value, int) and not isinstance(value, bool),
              "number": isinstance(value, (int, float)) and not isinstance(value, bool),
              "array": isinstance(value, list), "object": isinstance(value, dict)}
        if not any(ok[t] for t in types):
            return [f"{path}: {type(value).__name__} is not {'/'.join(types)}"]
    if "const" in schema and value != schema["const"]:
        errs.append(f"{path}: {value!r} is not {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        errs.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema \
            and value < schema["minimum"]:
        errs.append(f"{path}: {value} is under {schema['minimum']}")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                errs.append(f"{path}: {k!r} is missing")
        props = schema.get("properties", {})
        for k, v in value.items():
            if k in props:
                errs += validate(v, props[k], root, f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: {k!r} is not in the schema")
    if isinstance(value, list) and "items" in schema:
        for n, v in enumerate(value):
            errs += validate(v, schema["items"], root, f"{path}[{n}]")
    return errs


def verify(json_path: Path = JSON_OUT, md_path: Path = MD_OUT, curated_path: Path = CURATED) -> list[str]:
    """What CI can check with no lesson data. An empty list when all is well."""
    errs = []
    if not json_path.exists() or not md_path.exists():
        return [f"{json_path.name} or {md_path.name} is missing: run build_public_course_index.py"]
    ix = read(json_path)
    errs += validate(ix, read(SCHEMA))
    if errs:
        return errs[:40]
    if json_path.read_text(encoding="utf-8") != to_json(ix):
        errs.append(f"{json_path.name} is not in the generator's form: rebuild it, never edit it")
    if md_path.read_text(encoding="utf-8") != markdown(ix):
        errs.append(f"{md_path.name} is not generated from {json_path.name}: rebuild both")
    if ix["totals"] != totals(ix):
        errs.append("totals do not match the lessons")
    ids = [e["id"] for e in ix["lessons"]]
    cur = set((read(curated_path).get("lessons") or {}).keys())
    errs += [f"lesson {i} has a curated entry but is not in the index" for i in sorted(cur - set(ids))]
    errs += [f"lesson {i} is in the index but has no curated entry (spike/course_index/curated.json)"
             for i in ids if i not in cur]
    if len(ids) != len(set(ids)):
        errs.append("a lesson id appears twice")
    courses = {c: [] for c, _ in COURSES}
    for e in ix["lessons"]:
        courses[e["course"]].append(e)
        if e["id"] != e["folder"]:
            errs.append(f"{e['id']}: its folder is {e['folder']!r} (ADR 032: the id is the folder's name)")
        if not e["id"].startswith(f"{e['course']}-{e['order']:02d}-"):
            errs.append(f"{e['id']}: course {e['course']} and order {e['order']} do not match its id")
    for c in ix["courses"]:
        if c["lessons"] != [e["id"] for e in courses[c["id"]]]:
            errs.append(f"course {c['id']}: its lesson list does not match the lessons")
    by_id = {e["id"]: e for e in ix["lessons"]}
    for e in ix["lessons"]:
        secs = {s["id"] for s in e["sections"]}
        for tm in moments(e):
            if tm["start_s"] > e["length_s"] + 0.5 or tm["start"] != mmss(tm["start_s"]):
                errs.append(f"{e['id']}: a moment {tm['start']} ({tm['start_s']}) is outside the lesson or misprinted")
        for r in e["links"]["refers_to"]:
            tgt = by_id.get(r["lesson"])
            if not tgt or (r["section"] and r["section"] not in {s["id"] for s in tgt["sections"]}):
                errs.append(f"{e['id']}: a reference to {r['lesson']} {r['section']} does not resolve")
        for f in e["facts"] + e["methods"] + e["vocabulary"]:
            if f["section"] not in secs:
                errs.append(f"{e['id']}: section {f['section']} is not in the lesson")
    for tp in ix["topic_index"]:
        for x in tp["entries"]:
            if x["lesson"] not in by_id:
                errs.append(f"topic {tp['topic']!r}: lesson {x['lesson']} is not in the index")
    return errs


def moments(e: dict):
    for s in e["sections"]:
        yield s
        for tp in s["topics"]:
            yield tp
            yield from tp["points"]
        yield from s["rules"]
        yield from s["terms"]
        yield from s["wrong_examples"]
        yield from s["practice"]
    yield from e["facts"]
    yield from e["methods"]
    yield from e["vocabulary"]


def write(index: dict) -> bool:
    j, m = to_json(index), markdown(index)
    changed = False
    for p, text in ((JSON_OUT, j), (MD_OUT, m)):
        if not p.exists() or p.read_text(encoding="utf-8") != text:
            p.write_text(text, encoding="utf-8", newline="\n")
            changed = True
    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path, nargs="?", help="a lesson folder, or the lessons folder")
    ap.add_argument("--check", action="store_true",
                    help="build in memory; fail when docs/course-index.* differ from the lesson data")
    ap.add_argument("--verify", action="store_true",
                    help="check the committed index alone (no lesson data; CI)")
    a = ap.parse_args()
    if a.verify:
        errs = verify()
        for x in errs:
            print(f"FAIL: {x}")
        print("public course index: " + ("FAILED" if errs else "verified"))
        sys.exit(1 if errs else 0)
    if not a.target:
        ap.error("a lesson folder or the lessons folder is needed")
    index = build(lessons_dir_of(a.target))
    t = index["totals"]
    summary = (f"{t['lessons']} lessons, {t['sections']} sections, {t['topics']} topics, "
               f"{t['teaching_points']} teaching points, {t['vocabulary']} vocabulary items, "
               f"{t['topic_index']} index topics")
    if a.check:
        same = JSON_OUT.exists() and MD_OUT.exists() and \
            JSON_OUT.read_text(encoding="utf-8") == to_json(index) and \
            MD_OUT.read_text(encoding="utf-8") == markdown(index)
        print(f"public course index ({summary}): " + ("up to date" if same else
              "OUT OF DATE with the lesson data: run build_public_course_index.py and commit docs/course-index.*"))
        sys.exit(0 if same else 1)
    changed = write(index)
    print(f"public course index: {summary}; docs/course-index.json and .md "
          + ("CHANGED: commit them" if changed else "unchanged"))


if __name__ == "__main__":
    main()
