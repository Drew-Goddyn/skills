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

Deliver each playable reel in its own folder with its measured duration and size and a fixed `evidence.json` beside it. For every delivery, fill the [versioned template](templates/evidence.json) using the [evidence field guide](references/evidence.md), then run `python3 <skill>/scripts/check_evidence.py <delivery>/evidence.json`. Reference existing take records and raw checker reports, preserving warnings and review gaps. Evidence validation checks structure and consistency; it does not establish clarity, privacy, or fitness to publish. Include created-record IDs or scene/action setup and cleanup evidence. Stop only the sessions and services started for this task.

After the media check, run `python3 <skill>/scripts/beat_frames.py <delivery>/evidence.json <delivery>/frames-review` to generate [encoded beat frames and contact sheets](references/beat-frames.md). Inspect the relevant sheets and native frames, then record a finding for every decisive beat under `review.beat_findings` using the [field guide](references/evidence.md#decisive-frame-findings-and-the-watch-list). Name the inspecting author and supporting index samples. A midpoint is only a sample: inspect neighboring frames when needed to establish the action, or leave the finding unresolved. Unknown timing is not proof that the action is absent. Keep these findings distinct from continuous viewing, listening, and privacy review.

Save a short, beat-linked `review.watch_list` with final-output ranges and their existing precision; unknown times stay null. Revalidate the evidence, then run `python3 <skill>/scripts/review_delivery.py <delivery>/evidence.json <delivery>/handoff`. Include its timestamped watch list and four optional viewer-feedback questions in the response. The user need not watch or answer before an independent agent reviews the package; unanswered questions neither block delivery nor establish human review. Missing, unreviewed, unresolved or not-visible decisive moments prevent an unqualified successful-delivery claim: deliver a diagnostic package naming the blockers, or correct the implicated take within the authorized scope. A structurally valid incomplete record remains useful evidence. The helper summarizes recorded findings; it does not perform inspection or approve publication.

Include a small review ZIP with the response: reel, brief, evidence, raw checks, indexes, timestamped sheets, native frames and watch list. Keep assessment separate so the reviewer can inspect visuals first. Preserve original takes, edit maps, checker warnings, limitations and reviewer attribution; never replace earlier evidence to make a delivery appear complete. Include only the relevant invented or authorized data.

Record reusable friction under `toolkit` as it occurs. If it warrants maintenance, follow the linked guide within the authorized scope and report that outcome separately from the reel. Otherwise record `toolkit.status: no_change` with the reason.
