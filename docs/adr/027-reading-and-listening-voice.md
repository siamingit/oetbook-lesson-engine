# 027 — The voice of Reading and Listening lessons: Courtney, about 135 words a minute

Date: 2026-10-06
Status: **Accepted** by the maintainer in chat, 2026-10-06: "Reading voice:
Courtney at 135 wpm (the audition file courtney_135wpm.wav: slowest speed
setting plus added sentence pauses). Record in a new ADR the voice, the rate and
how it is produced (speed setting and pause lengths), as the voice for all
Reading and Listening lessons."

## Context

Grammar and Vocabulary lessons are narrated by Cartesia's Rupert (British,
chosen 2026-09-22) at speed 1.0, chosen by ear on 2026-09-24 (methodology §23).
For the Reading course the maintainer wanted a female voice. On 2026-10-05
four British voices read the same 78-word sample (Courtney, Imogen, Julia,
Victoria) at about 155 words a minute; the maintainer chose Courtney but found
155 too fast, and asked for 145, 135 and 125 (2026-10-06).

Measured on that sample (`spike/scripts/voice_audition.py --slower`, model
`sonic-3.6`, recorded in `C:\OET\voice-audition\reading\audition.json`):

- Cartesia's speed setting runs from 0.6 to 1.5. Courtney at 1.0 read the sample
  at 160.7 to 165.7 words a minute; at 0.83, 144.1; at the lowest setting, 0.6,
  139.6 to 143.7 over four takes. Below about 0.85 the rate barely moves and
  varies from take to take, so the speed setting alone cannot reach 135. The
  same floor was measured for Rupert in 2026-09 (0.6, 140.3 words a minute;
  `synthesize_audio.py`).
- 135 was made from a take at 0.6 (143.7 words a minute, 32.56 s) with 0.301 s of
  silence added in the middle of the pause after each of its seven sentences
  but the last: 34.67 s, 135.0 words a minute. The pauses after sentences went
  from 0.37-0.55 s to 0.68-0.85 s.
- No take had samples at full scale or clicks; word lengths grew evenly (median
  1.14-1.16 times their length at speed 1.0).

## Options considered

1. Courtney at 145 (speed setting alone, 0.83).
2. **Courtney at 135: the lowest speed setting and longer pauses between
   sentences** (this decision, by the maintainer's ear).
3. Courtney at 125: the same with 0.70 s added.
4. Cartesia `<break>` tags in the text, in place of silence added after
   synthesis. Not used: Cartesia's documentation says a break tag splits the
   generation and can make the speech less natural, and the clip the
   maintainer chose was made with silence added after synthesis.

## Decision

- **Every Reading and Listening lesson** (a lesson id beginning `reading` or
  `listening`) is narrated by **Courtney**, Cartesia voice
  `16a4052e-1f11-47ac-95f5-9330bee062f9`, model `sonic-3.6`, under the
  pronunciation lexicon like every lesson.
- **Speed setting 0.6** (`generation_config.speed`).
- **0.30 s of silence added after every sentence of a clip but its last**: a
  word that ends in `.`, `?` or `!`, the cut made in the middle of the pause
  the voice already makes there. The word timestamps move with the audio, so
  marks, the reading pointer and the ear stay in time. The gaps between clips
  are the player's, as for every lesson.
- Grammar and Vocabulary lessons keep Rupert at 1.0 with nothing added.

Carried by `spike/scripts/voices.py` (the voice by lesson type and
`add_sentence_pauses`), read by `synthesize_narration.py` and `check_terms.py`
(the terms are probed in the lesson's own voice and speed). The cache key of a
clip includes the voice and, for a voice with added pauses, the pause length;
the key of every clip already made is unchanged (6,258 clips of the 11 built
lessons recomputed equal, 2026-10-06).

## Consequences

- About 135 words a minute is measured on a sample read straight through. A
  lesson's own pace also depends on its sentences and on the gaps between
  clips, so the finished lessons are measured, not assumed, and the rate is
  reported at the final gate.
- Reading lessons run longer than a lesson at Rupert's pace of about 155: the
  silent preview's timing (an estimate at 149.5 words a minute) is shorter
  than the narrated lesson.
- Lexicon entries were approved by ear with Rupert. Their aliases are phonetic
  and apply to any voice, and the phoneme check runs on every clip, but how a
  term sounds in Courtney's voice is judged again by the maintainer at each
  Reading lesson's final gate.
- To change the rate: change `sentence_pause_s` or `speed` in `voices.py` and
  record a new ADR; the cache then makes every Reading clip again.

## Amendment, 2026-10-06: Rupert for every lesson; the delivery rule; the monotony check

Recorded at the maintainer's request after the delivery audition: "switch the
Reading and Listening lessons to Rupert. Do not use Courtney."

### The voice

- **Rupert is the voice of every lesson**, Reading and Listening included,
  with exactly the provider and settings of the approved Grammar and
  Vocabulary lessons: Cartesia `sonic-3.6`, voice
  `0ad65e7f-006c-47cf-bd31-52279d487913`, speed 1.0, nothing added to the clip,
  under the pronunciation lexicon. **The choice of a female voice for Reading
  and Listening (Courtney, above) is withdrawn.** `voices.py` gives every
  lesson type Rupert; Courtney's settings stay only for the audition record.
- **Why.** The maintainer found Courtney's delivery monotonous, "like someone
  reading from a script". Measured on question one of Reading lesson 2
  (`delivery_audition.py`, C:\OET\voice-audition\reading\delivery\): her
  median pitch variation was 3.20 semitones as narrated (speed 0.6) and 3.26 at
  speed 1.0 with the same script; a teacher-style script raised it to 3.53,
  and Cartesia's emotion setting to 3.63 at most (in a probe, the emotion
  settings lowered it). Rupert's approved lessons measure 4.32 to 4.46. The
  audition files are kept for the record.

### The delivery rule

- **Reading and Listening lessons are delivered like an engaged teacher, never
  as monotonous reading** (maintainer). The narration stage's DELIVERY rule
  (`write_narration.py`, given to Reading and Listening lessons only), as in
  the audition's variant v2: short questions to the learner and their
  answers, signposting, weight on the key point, varied sentence length, a
  brief reaction when the answer is found. It changes how things are said, not
  what is taught.
- **Longer lessons are accepted**: there is no length cap for this style.
- **Added teaching points.** A teaching point or a generalisation the
  instructor did not make may stay when it is accurate and consistent with
  his method. The narration marks each (an utterance note starting
  "ADDED: "), and every one is listed for the maintainer at the final gate.

### The monotony check

- `pitch_check.py` measures each clip's pitch variation (the standard
  deviation of its pitch, in semitones about the clip's own median, from an
  autocorrelation pitch track every 10 ms). The baseline is 660 clips of the
  eleven lessons approved with Rupert: median 4.42, 10th percentile 3.71,
  25th percentile 4.07.
- **A lesson fails if its median clip is below 4.07; every clip below 3.71 is
  flagged** for the maintainer's ear, with its time. The runner runs it on
  every lesson's finished player (`pitch_check.json`). The eleven approved
  lessons all pass (medians 4.32 to 4.46); about one clip in ten is flagged in
  each, by the baseline's own definition.
- It is a signal for the ear, not a judge of it; the final gate stays the
  maintainer's.
