---
name: dream-loop-fast
description: 'Build a game, app, or 3D scene to match a dreamed target screenshot, with many cheap Sonnet and Haiku rounds instead of a few expensive ones.'
disable-model-invocation: true
---

# Dream Loop Fast

A bundled Claude Code workflow that re-implements the Pro workflow of [dream-loop](https://github.com/achimala/dream-loop). Codex generates a target screenshot of the finished product. Sonnet builders then work toward it on separate git branches, three in parallel per round after a single first build. A Haiku panel picks the closest candidate, and a Sonnet judge scores it against the target and lists the gaps for the next round. A candidate replaces the current best when the judge rules it no further from the target overall and it scores within half a point of the best score so far. The run ends at the target score, on a stall, at the round limit, when a token budget runs low, or after two rounds in a row produce no verdict. It leaves the best version on a `<tag>/best` branch and never changes the checked-out branch or tracked files.

## Run it

1. If the user gave no build request, ask for one; the workflow cannot start without it.
2. Tell the user in one line that the run is long, creates `dream/*` branches and a `.dream-loop/` folder in the project, and asks for permission each time Codex runs outside the sandbox to make images, unless they allow it through `/sandbox`.
3. Call the Workflow tool with `scriptPath` set to this skill's base directory followed by `/scripts/dream-loop-fast.js`. Pass the text the user typed after the command as `args`, unchanged, as a string; it becomes the build request. When the user names options, pass a JSON object with `request` plus those options instead. The options are documented at the top of the script. To run again in a project that already has `dream/*` branches, pass a new `tag`.
4. Relay the returned result as described below. The run is done when the user has the outcome and knows where the best version lives.

If the Workflow tool is unavailable, tell the user this skill needs Claude Code workflows and stop. The parallel builds, selection, and keep-or-discard gate live in the workflow.

## Relaying the result

If the workflow throws instead of returning, relay its message: setup refused the project, or there was no way to get a target image. Otherwise the result is an object:

- `leaks`: a non-empty list means those branches contain an API key value and must be deleted before anything is pushed; lead with it. `null` means the wrap-up failed and branches were not checked; say so.
- `status`: `done` (reached `doneScore` and the frame-rate floor), `stalled` (a bold or optimize round failed), `max-rounds`, `budget`, or `failing` (two rounds in a row produced no verdict). Give it with `score` out of 10. A score of -1 means nothing was ever judged. When `peak.score` is higher than `score`, name `peak.branch` as the highest-scoring version.
- `branch`, `checkout`, `screenshot`: where the best version lives and what it looks like. `branch` is null when the wrap-up failed or no product was ever kept; for an existing product with no kept candidate, it points at the starting commit.
- `fps` with `fpsMeasured`: when `fpsMeasured` is false, say the frame rate was not verified because captures rendered in software.
- `topGaps`: the judge's remaining gaps, described by what is wrong in the scene.
- `target`, `dreamGenerator`: the target image and what made it.
- `bakeoff`: present when `compareWith` was given, the run did not end on `budget`, and a version was kept. Report both tallies and that the referees are the same model families that built and judged this side.
- `history` and `rounds`: one entry per round. Summarize in a sentence unless the user asks for detail. When `logWritten` is true, the full record is in `.dream-loop/runs/<tag>/run.json`.

## Prerequisites

- Claude Code with the Workflow tool, git, and Node 18 or later. The first run installs Playwright into `.dream-loop/harness` and its Chromium build into Playwright's shared browser cache.
- The project folder is empty, new, or the top level of a clean git repo. An existing product must be a static web app (an `index.html` served from a folder). Setup checks this before changing anything and refuses otherwise.
- The Codex CLI, logged in, for every generated image: the target, asset cutouts, and textures. It runs outside Claude's sandbox. Without Codex, pass `target` with an existing image; builders then make textures in code.
- Optional: Blender, for modeling architecture and hard-edged objects. Optional: `FAL_KEY` or `FAL_API_KEY`, for turning cutouts of organic objects such as characters and trees into 3D models through fal.ai. That is the only paid service. Builders are told to stay under a per-pass job limit; nothing enforces it.

## Credits

Re-implements the Pro workflow of [achimala/dream-loop](https://github.com/achimala/dream-loop/tree/9bddb901f7d071cfefdd21e264267c757177a9df) by Anshu Chimala ([@anshuc](https://x.com/anshuc)), revision `9bddb90`. The loop structure, judging rubric, and stall rules follow it; no upstream code is included. The original MIT notice is in [LICENSE](LICENSE).
