---
name: dream-loop-fast
description: 'Build a game, app, or 3D scene to match a dreamed target screenshot, with Sonnet and Haiku doing the work and a few Opus director calls steering it.'
disable-model-invocation: true
---

# Dream Loop Fast

A bundled Claude Code workflow that re-implements the Pro workflow of [dream-loop](https://github.com/achimala/dream-loop). Codex generates a target screenshot. An Opus director turns it into a build plan and a list of shared assets, which are built once, in parallel. Each round, one Sonnet builder works from the plan and a short scene file (`SCENE.md`) on its branch, Haiku captures the result, and a Sonnet judge scores it against the target. A version replaces the current best when the judge rules it no further from the target overall and it scores within half a point of the best score so far. The director checks in again after the first kept build and when progress slows. The run leaves the best version on a `<tag>/best` branch and never changes the checked-out branch or tracked files.

## Run it

1. If the user gave no build request, ask for one; the workflow cannot start without it.
2. Tell the user in one line that the run is long, creates `dream/*` branches and a `.dream-loop/` folder in the project, and asks for permission each time Codex or Chromium runs outside the sandbox, unless they allow it through `/sandbox`.
3. Call the Workflow tool with `scriptPath` set to this skill's base directory followed by `/scripts/dream-loop-fast.js`. Pass the text the user typed after the command as `args`, unchanged, as a string; it becomes the build request. When the user names options, pass a JSON object with `request` plus those options instead. The options are documented at the top of the script. To run again in a project that already has `dream/*` branches, pass a new `tag`.
4. Relay the returned result as described below. The run is done when the user has the outcome and knows where the best version lives.

If the Workflow tool is unavailable, tell the user this skill needs Claude Code workflows and stop.

## Relaying the result

If the workflow throws instead of returning, relay its message: setup refused the project, there was no way to get a target image, or the director's plan failed (resuming the run retries it). Otherwise the result is an object:

- `leaks`: a non-empty list means those branches contain an API key value and must be deleted before anything is pushed; lead with it. `null` means the wrap-up failed and branches were not checked; say so.
- `status`: `done` (reached `doneScore` and the frame-rate floor), `stalled` (an optimize round failed, or four rounds passed without a gain), `max-rounds`, `budget`, or `failing` (two rounds in a row produced no verdict). Give it with `score` out of 10. A score of -1 means nothing was ever judged. When `peak.score` is higher than `score`, name `peak.branch` as the highest-scoring version.
- `branch`, `checkout`, `screenshot`: where the best version lives and what it looks like. `branch` is null when the wrap-up failed or no product was ever kept; for an existing product with no kept version, it points at the starting commit.
- `fps` with `fpsMeasured`: when `fpsMeasured` is false, say the frame rate was not verified because captures rendered in software.
- `topGaps`: the judge's remaining gaps, described by what is wrong in the scene.
- `plans`: the director's plan and each revision. `opusCalls`, `library`, and `falJobsUsed` show how much direction and asset work the run used.
- `history`: one entry per round with its score, whether it was kept, the builder's summary, and the director's priority when it checked in. Summarize in a sentence unless the user asks for detail. When `logWritten` is true, the full record is in `.dream-loop/runs/<tag>/run.json`.

## Prerequisites

- Claude Code with the Workflow tool and access to Opus, Sonnet, and Haiku; git; Node 18 or later. The first run installs Playwright into `.dream-loop/harness` and its Chromium build into Playwright's shared browser cache.
- The project folder is empty, new, or the top level of a clean git repo. An existing product must be a static web app (an `index.html` served from a folder). Setup checks this before changing anything and refuses otherwise.
- The Codex CLI, logged in, for every generated image: the target, asset cutouts, textures, and backdrops. It runs outside Claude's sandbox. Without Codex, pass `target` with an existing image; builders then make textures in code.
- Optional: Blender, for modeling architecture, props, and kit pieces.
- Optional: fal.ai, for turning cutouts of organic hero objects such as characters into 3D models. It is the only paid service, and the workflow caps jobs with `falJobs`. To keep the key away from the agents, start the bundled relay with the key injected by 1Password and pass its URL as `falRelay`:

  ```sh
  FAL_KEY='op://<vault>/<item>/<field>' op run -- node "<this skill>/scripts/fal-relay.mjs"
  ```

  It listens on `http://127.0.0.1:4791`, sends the key only to fal, and refuses jobs past `RELAY_CAP` (default 9). Set `RELAY_LEDGER` to a file path to log each job. Stop it when the run ends. Without the relay, the workflow uses `FAL_KEY` or `FAL_API_KEY` from the environment.
- A "+Nk" token budget is enforced between rounds but counts output tokens only. To compare cost with another system, use gateway usage.

## Credits

Re-implements the Pro workflow of [achimala/dream-loop](https://github.com/achimala/dream-loop/tree/9bddb901f7d071cfefdd21e264267c757177a9df) by Anshu Chimala ([@anshuc](https://x.com/anshuc)), revision `9bddb90`. The loop structure, judging rubric, and stall rules follow it; no upstream code is included. The original MIT notice is in [LICENSE](LICENSE).
