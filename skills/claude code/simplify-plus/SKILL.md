---
name: simplify-plus
description: 'Cleanup review for any scope in Claude Code (a commit, PR, branch, path, tool, or the whole repo), with a skeptic filter and one checked local commit per chunk.'
disable-model-invocation: true
---

# Simplify Plus

A bundled Claude Code workflow that does what `/simplify` does at any scope. It splits the scope into chunks, reviews each for reuse, quality, efficiency and altitude, checks for duplication across chunks, drops findings a skeptic rejects, then applies the rest one chunk at a time. A chunk is committed locally only when the repo's checks pass, and undone when they fail. The workflow never pushes, switches branches or rewrites history.

## Run it

1. Call the Workflow tool with `scriptPath` set to this skill's base directory followed by `/scripts/simplify-plus.js`. Pass the text the user typed after the command as `args`, unchanged, as a string. With no text, omit `args`; the workflow then reviews the current branch against its base.
2. Relay the returned report as described below. The run is done when the user has the outcome and any decision the report asks of them.

If the Workflow tool is unavailable, tell the user this skill needs Claude Code workflows and stop. The split, skeptic and undo steps live in the workflow, so a manual review would skip them.

## Relaying the report

The report is an object. Its keys decide what to show:

- `tooBig`: the scope is larger than one run covers. Show the message and each `plan` entry (target, size in lines, what it covers, whether it `fits` one run), then ask which target to run next.
- `nothing`: show the message and the `howToTarget` hint.
- `refused` or `error`: show the message.
- `reviewOnly`: show `stoppedBecause`, the `coverage` line, and the kept findings by chunk.
- Otherwise it was a fix run. Lead with `coverage`, then the commits, any `flagged` commits (they touched tests or check configuration, so the user should look at them), `reverted` chunks with the failing check, skipped findings, and `halted` if set.

Describe findings and edits by what the code does, with file names as a trailing detail.

## Arguments

Free text such as `PR 1234`, `the last 3 commits`, `tools/importer review only`, or `the whole repo, run make test`. A JSON object also works: `{"target": "...", "base": "main", "test": "npm test", "reviewOnly": true}`.

## Prerequisites

Claude Code with the Workflow tool, git, and the GitHub CLI (`gh`) for PR targets. Fixing needs a clean working tree, a checked-out branch, the target checked out, and a check command, either documented in the repo's CLAUDE.md or named in the arguments. Without those the run stops after review and says why.
