---
name: web-design-guidelines
description: Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site against best practices".
metadata:
  author: vercel
  version: "1.0.0"
  argument-hint: <file-or-pattern>
---

# Web Interface Guidelines

Review files for compliance with Web Interface Guidelines.

## How It Works

1. Read the vendored guidelines file (see Guidelines Source)
2. Read the specified files (or prompt user for files/pattern)
3. Check against all rules in that guidelines file
4. Output findings in the terse `file:line` format

## Guidelines Source

Project note (ADR 048): this repository installs the rules as a local file, so the review runs with no network call. Read `references/web-interface-guidelines-command.md` (vendored from https://github.com/vercel-labs/web-interface-guidelines `command.md`, commit 434b7f9, 2026-10-05). It contains all the rules and the output format. Do not fetch the URL; a newer copy is vendored by a new commit that records its upstream commit in `.claude/skills/README.md`.

## Usage

When a user provides a file or pattern argument:
1. Read the vendored guidelines file named above
2. Read the specified files
3. Apply all rules from that guidelines file
4. Output findings using the format specified in the guidelines

If no files specified, ask the user which files to review.
