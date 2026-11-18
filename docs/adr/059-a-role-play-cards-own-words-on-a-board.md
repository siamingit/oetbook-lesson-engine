# ADR 059 — A role-play card's own words on a board

Date: 2026-11-18 (the maintainer's decision on #249, comment 6991577533, on Medicine Speaking 2).

Status: Accepted. It adds one optional field to a screens block, read only by the screens audit
(`write_screens.py`). The field never reaches the bundle, which carries only its listed block fields. A lesson
without the field is audited exactly as before. It changes no bundle format, no player, no stage and no other
check. It amends the register rule of methodology §17b for this one case.

## Context

Medicine Speaking 2 (A Whole Role-Play, #249) shows the cards of our own set oa-ss-med-0008 word for word. Card
two's task 2 describes the condition as "very common". The screens audit reads "common" as a register claim (methodology §17b), and it fails a
non-maintainer block that says it. Released documents (`doc`, `map`, a question, the word bank's words) are
already exempt (ADR 026), because they are quoted, not judged. A role-play card had no such exemption. So the
board showed "one spot, ..., no effect", and the owner was asked about it.

The maintainer, 2026-11-18, on #249: "Card two, task 2 (124): show the card word for word ("very common", no
"..."). Your recommended engine change is approved: the screens audit exempts a card's own words, with an ADR and
a render proof."

## Decision

1. **A block may carry `set_card`.** The value names the set and the card the block quotes word for word, such as
   `"set_card": "oa-ss-med-0008 RP2"`. It has the shape `oa-ss-<profession>-<nnnn> RP1` or `RP2` (`CARD_REF`). Any
   other value fails the audit. It is not called `card`: `board_style.derive` already sets and clears a block's
   `card` (a change card), so a field of that name would be wiped before the audit and would fail every change
   card. The first render proof showed this (grammar-01 failed); the field was renamed and the proof run again.
2. **The register check skips such a block,** as it skips a released document. A card's "very common" is a clinical
   fact about a condition. The lesson quotes it; the teacher does not judge a word by it.
3. **Nothing else is lifted.** The forbidden phrases, the non-Latin check and every other check still apply to
   the block. The teacher's own words about the card (narration, notes, other blocks) are checked as before.
4. **The author vouches for the words.** The engine has no copy of the sets, so it cannot compare the text. The
   block's note says it is the card word for word, and the owner's final review shows the board. A block that
   paraphrases a card must not carry `set_card`.

## Proof that the live lessons are unchanged

`render_compare.py` (snapshot before, snapshot after, compare) on 27 of the 43 built lessons in the library (the
five Medicine lessons, being renamed and rebuilt at the time, are not among the 43). "Before" ran with the scripts
at main (d44e4f3), from a separate worktree. "After" ran with this change. The result is under Consequences.

The other 16 already fail on main, before this change, in write_narration's audit, on a clash with another
lesson's words that it reads from the course index and the other lessons' configs:

- "the introduction opens with the same sentence as ...": grammar-04-articles, speaking-03-starting,
  speaking-04-asking-questions, speaking-05-taking-a-history, speaking-06-patient-concerns,
  speaking-10-sounding-clear, speaking-11-keeping-going, speaking-12-empathy-and-reassurance;
- "the closing's goodbye is speaking-02-reading-the-card's": listening-02-part-a;
- "names the lesson '...' without its refs": speaking-01-the-test, speaking-02-reading-the-card,
  speaking-07-persuading, speaking-08-explaining, speaking-09-giving-advice, speaking-13-angry-or-upset,
  speaking-14-ending.

A snapshot stops at its first failing lesson, so the proof ran in three parts (8, 8 and 11 lessons). The last 18
were screened first, with write_narration `--render` at main on a scratch copy of the library. None of the 16
carries `set_card` (searched), so both changed lines take the same path for them as before (issue #262): the new audit check
and the new `released` clause act only on a block with `set_card`.

## Consequences

- Medicine Speaking 2's board 124 shows card two's task 2 word for word, with "very common".
- Any later lesson that shows one of our own role-play cards can mark the card's blocks with `set_card`.
- The proof: 27 of 27 lessons IDENTICAL (data files, every fingerprinted moment drawn and DOM text, board timing; reports compare-before-after, compare-before2-after2, compare-before3-after3). The 43 built lessons' 164,824 files were unchanged in size and time across the runs; the snapshots' ALARM listed only files of the Medicine lessons other sessions were building.
