# Project skills (ADR 048, creative board design)

Design skills every lesson session loads before it lays out boards (docs/adr/048-creative-board-design.md,
decision 1; docs/03-RUNBOOK.md step 11b). Each is a vendored copy of one folder of an upstream repository, pinned
to the commit below, installed 2026-11-01 after every file was read. None runs anything on install, none calls
the network when used as the ADR says, none asks for a key. Text files are stored with LF line endings. Anthropic's
`frontend-design` skill is built into Claude Code and is not vendored.

| Folder | Upstream | Commit | Licence | Changed here |
|---|---|---|---|---|
| `ui-ux-pro-max/` | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill, `.claude/skills/ui-ux-pro-max/` (v2.15.0) | `3a13158ff1f32156cbe144108de48eda2ecaed9a` (2026-11-01) | MIT (Next Level Builder; `LICENSE` copied from the repository root) | `scripts/tests/` left out (26 files: they walk to their own repository's root and spawn subprocesses). In `SKILL.md` the plugin-only path `${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py` is written `.claude/skills/ui-ux-pro-max/scripts/search.py` (11 places) with a project note, since that variable exists only in a plugin install |
| `slides/` | same repository, `.claude/skills/slides/` | same | MIT (same `LICENSE`; the sub-skill names `claudekit` as its author) | a project note under the title: its search commands call a sibling skill, `design-system`, which is not installed (it carries a network-fetching script); the references are reading only |
| `design-motion-principles/` | https://github.com/kylezantos/design-motion-principles, `skills/design-motion-principles/` | `4a9ca879f24a361f4dca4174fe2da0f67b5ddee3` (2026-05-30) | MIT (Kyle Zantos; `LICENSE` copied from the repository root) | a project note under the title: findings go into the lesson's `analysis/design/`, never `motion-audits/`, and no browser is opened |
| `hallmark/` | https://github.com/nexu-io/open-design, `plugins/community/hallmark/` (upstream of that: Nutlope/hallmark) | `12d970eacc8971150e3c76470d2a9afe16dc2ed1` (2026-10-30) | MIT (its own `LICENSE`) | a project note under the title: judgement only; no theme, page structure, `tokens.css`, `.hallmark/`, `design.md`, stamp or `study <URL>`; the repository's rules win over its gates |
| `critique/` ("Design Critique") | same repository, `design-templates/critique/` (from alchaincyf/huashu-design) | same | Apache-2.0 (the repository's; it has no licence file of its own, so the repository's `LICENSE` is copied here) | a project note under the title: run on the contact sheet and the player's HTML, written as `analysis/design/critique.md`, no `<artifact>` block, no reviewer branding |
| `emil-design-eng/` ("Design Engineering") | same repository, `skills/emil-design-eng/` (from emilkowalski/skills at `a47903a`) | same | MIT (its own `LICENSE`, which names Matt Pocock as the copyright holder; the content is Emil Kowalski's) | a project note under the title: skip its canned initial response; style C's motion stays |
| `web-design-guidelines/` | https://github.com/vercel-labs/agent-skills, `skills/web-design-guidelines/`; its rules from https://github.com/vercel-labs/web-interface-guidelines, `command.md` | `1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62` (2026-10-27); the rules `434b7f91364665f2f733b310ec54809bf8f37937` (2026-10-05) | MIT, stated in both repositories' READMEs (agent-skills has no licence file; the rules repository's `LICENSE` is copied beside them) | upstream fetches the rules from the `main` branch of the rules repository at every use. Here they are vendored as `references/web-interface-guidelines-command.md`, pinned, and `SKILL.md` reads that file (the "Guidelines Source" and "How It Works" steps rewritten; no fetch) |

Left out and why:

- `nexu-io/open-design`'s own skill (`od-contribute`), its daemon, apps, design systems, image and video templates:
  not asked for; the critique the owner named is the `critique` template, and "Design Engineering" is
  `emil-design-eng` (its trigger words). The repository has no skill called "design-critique" or
  "design-engineering" at this commit.
- `nextlevelbuilder/ui-ux-pro-max-skill`'s other sub-skills (`design`, `design-system`, `brand`, `banner-design`,
  `ui-styling`): not asked for; `design-system` carries `fetch-background.py` (a network fetch), `ui-styling`
  bundles fonts (5.9 MB).
- `vercel-labs/agent-skills`' other skills: not asked for.
- `ui-ux-pro-max/scripts/tests/`: see the table.

Updating a skill: fetch the upstream folder at a new commit into a scratch folder, read every file, re-apply the
changes above, and record the new commit here, in one pull request.
