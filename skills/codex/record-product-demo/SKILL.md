---
name: record-product-demo
description: Record and edit demos or trailers from running applications and games. Use for product walkthroughs, PR reels, and gameplay showcases.
---

# Record demos and trailers

Show real behavior in a reel suited to its audience. Let the brief determine duration, framing, sound, and editing. Keep the source footage, actions, and presentation changes distinguishable so the reel remains credible and reproducible.

## Establish the brief and review coverage

Identify what viewers should understand or want to try, and the visible behavior that supports it. Inspect the running product or supplied footage before choosing beats. Record the source revision and capture conditions. For a before/after claim, use corresponding revisions and equivalent inputs.

Before production, establish whether the available tools or reviewer can watch continuous video and, when sound matters, hear audio. Surface missing coverage early. Complete supported checks and report the remaining gap; playback counters, still images, and audio meters cannot establish an audiovisual judgment.

## Load the relevant guidance

These branches can combine. Read only those needed by the requested work:

| Work | Read |
| --- | --- |
| Capture a browser interface or browser game | [Browser capture](references/browser-capture.md) |
| Record gameplay, camera movement, or an engine-rendered sequence | [Gameplay capture](references/gameplay-capture.md); browser games also use browser capture |
| Assemble shots, add titles or sound, retime footage, or revise an existing edit | [Post-production](references/post-production.md) |
| Diagnose capture, conversion, or playback failures | [Media repair](references/media.md) |
| Resolve demonstrated reusable tooling friction or a requested skill experiment | [Toolkit maintenance](references/toolkit-maintenance.md) |

## Capture when needed

For new footage, choose beats that connect the action and its consequence. Give each hold a purpose appropriate to the brief. Establish setup and restoration within the authorized environment, then rehearse the sequence before the take. Use application-generated results and real gameplay. Preserve the input method and any camera, HUD, or timing adjustments with the capture. An edit of existing footage follows the post-production branch without repeating capture unless the revision requires it.

For each new take, verify the decisive action and result both in the application and in the recording. A successful input or assertion does not prove that the recorder retained it. Check representative motion, any intended hold, and resumed action where relevant. Preserve failed takes when diagnosing a recording problem.

## Verify and deliver

Run [the media checker](scripts/check_video.py) with the requested dimensions, rate, duration, size, and audio policy. Set `--min-duration` and `--max-duration` from the brief. Use `--audio-policy require` when the brief requires sound; silence is the default policy. See `--help` for options and [post-production](references/post-production.md#render-and-review-the-changed-work) for timing, the full-range H.264 compatibility policy, and review limits. Watch the complete delivered encode at normal playback speed, including after edits, and listen when it contains meaningful sound. Judge clarity, continuity, and pacing against the brief. Record unavailable review explicitly.

When independent review is requested or warranted, give a fresh viewer only the reel, audience context, and viewing constraints first. Ask what they understood, what happened, and where another look was needed; for a trailer, also ask what looked appealing and whether the build and finish worked. Preserve that response before sharing the intended takeaway and criteria. Revise implicated beats; a new first impression requires a fresh viewer.

Deliver the playable reel and its measured duration and size. Save JSON evidence beside it with source and output paths, capture/edit settings, beats, checks, review coverage, and limitations. Include created-record IDs or scene/action setup when needed to reproduce the take. Stop only the sessions and services started for this task.

Record reusable friction under `toolkit` as it occurs. If it warrants maintenance, follow the linked guide within the authorized scope and report that outcome separately from the reel. Otherwise record `toolkit.status: no_change` with the reason.
