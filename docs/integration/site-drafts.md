# Drafts: a lesson in the site's player before the final gate

Written 2026-10-31 from the site's ADR-0039 (oetacademy-web, "Draft sessions, reviewed in the site's
own player before they are published", accepted 2026-10-30) and the owner's brief of 2026-10-31.
The engine's record of the decision: ADR 039 amendment of 2026-10-31; the step: runbook 18a.

## What the site gives

An admin-only page, `https://app.oetacademy.uk/admin/session-drafts`, that plays a session's newest
draft in the site's real learner player (the same session view, practice points with Try again and
Show answer, the progress bar's markers, Samin, the theme, a phone's width). Learners never see a
draft: drafts live in their own table and are never a lesson, a course item or a search entry, and
nothing played there is recorded. Each draft shows as **Ingested**, or **Rejected** with the reason
(the importer's message, then each finding as `where: message (code)`).

## What the engine sends

| | Draft | Final (unchanged) |
|---|---|---|
| Repository | `siamingit/oetacademy-sessions` | the same |
| Release | pre-release | published release, not a pre-release |
| Tag | `<lesson id>-v<package_version>-draft.<n>` | `<lesson id>-v<package_version>` |
| Version | the one it will be published as (one above the live one; 1 if not live) | the same |
| `n` | 1, 2, 3 … one above the lesson's drafts already there | — |
| Assets | `manifest.json` and the zip (any name ending `.zip`), its manifest byte-identical | the same |
| `lesson.approved` | `{"by": "draft", "on": "<build date>"}` | `{"by": "siavash", "on": "<final gate date>"}` |
| Checks before sending | the pinned contracts; from 1.23 the site's validator, 0 errors | the same |

`publish_lesson.py <L> --package --draft`, then `--release --draft --dry-run` and `--release --draft`,
which ends by starting the site's drafts-only run:

    gh workflow run content-pipeline.yml -R siamingit/oetacademy-web --ref main -f source=drafts

About three to five minutes later the draft is on the admin page. If the command is refused, tell the
owner: the site's six-hourly check starts the run anyway.

## Rules both sides keep

- A draft never becomes the final. The final is a new build released under the final tag; never edit
  or promote a draft release. A draft with the wrong approval sent as a final is refused by the site
  (`not-approved`) and never goes live.
- The site checks only a session's newest draft, once; a draft of a version already live is ignored.
- When the final is imported the site deletes the session's draft of that version or older. The old
  draft pre-releases may then be deleted from the sessions repository; final releases never are.
- A rejected draft opens no issue on the site: read the reason on the admin page and send a new draft.

## The engine's preview player

It no longer has to match the site's. The owner reviews in the site's player; the engine's player
(`generated/lesson-player/player.html`) stays the engine's own check of a build (fit, marks, layout),
and a difference between the two is not a defect to fix in the engine.
