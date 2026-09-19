# Browser capture

Use this for browser interfaces and browser games. Engine or gameplay concerns additionally belong in [gameplay capture](gameplay-capture.md).

## Choose the browser flow

Complete the [environment check](capture-environment.md) before an app rehearsal
or capture. Pass the observed environment to each `Demo.record` call; missing
context stops recorder startup. Use a task-only profile and retain the diagnostic
if the target, account or data provenance needs clarification.

For an ordinary walkthrough without a more specific brief, start with a silent 15–30 second reel, a fixed 1440 × 900 viewport, and one useful outcome. A small form change can be just context, input, and the saved result. Fill unrelated fields before recording. Let the requested presentation override these defaults.

Use synthetic values in the real local or test flow. Track the record the application creates instead of selecting the first row. Assert the decisive result in the UI, including persistence when that is the claim. These observations establish the demonstrated environment's behavior.

## Select and check capture

Read [the technique manifest](../techniques.json) before writing a driver. Start from the [runnable driver template](recording-driver.md) for a form-to-result flow, or import the existing browser helpers into a task-local script and use native commands for unsupported interactions. The manifest owns entrypoints, prerequisites, limitations, and executable checks.

Use `agent-browser` for browser interaction and viewport recording. Follow the installed executable's help. Put it on `PATH`, or set `DEMO_BROWSER` to an executable path or command name; the override takes precedence. Put FFmpeg's `ffmpeg` and `ffprobe` on `PATH` too. Tools are not searched in platform-specific installation directories. Use a short task-specific `AGENT_BROWSER_SOCKET_DIR` if the default is unwritable or the socket path is too long. A blocked launch calls for the supported scoped escalation, preserving the failure.

Run the moving preflight when the recorder or settings are not yet verified for this task. Configure and check the task-only profile before passing `--browser-profile-mode task_only`; the flag records that supplied observation. Match the take's format and inspect actual output dimensions, including device scale. Keep the fixture's motion/hold/resumed-motion result separate from the target-app environment decision and app rehearsal. Reject settings that fail preflight; inspect the actual flow under representative load before using them for the take.

Use the task rehearsal to inspect its characteristic action. For a form, confirm that the decisive typing, click, saved result, and reading hold survived capture. For animation or a browser game, inspect source timestamps or distinct captured states under the planned camera movement and rendering load; encoded frame rate alone leaves source cadence unverified. Choose an alternative only after a relevant comparison supports it, and preserve the original failure.

## Preserve the take and failure record

Use a fresh session with `Demo.record(name, environment=observed)`; it requests
30 fps on the current page in tested agent-browser 0.37.1. Each attempt retains
the requested video path, FPS and environment decision. A blocked environment
has `failure_stage: environment_check` and makes no recorder call. Recorder-start
failure uses `failure_stage: recorder_start`, null timing and empty events/recorder
facts. Both remain failed attempts with a requested path, not a produced reel.

Startup and flow errors propagate after diagnostic recording/cleanup. If writing
the start-failure diagnostic also fails, the startup error stays primary and the
file error is chained. Successful takes retain their existing events and recorder
facts. Keep all useful failures and clean up only task-owned resources.

Driver events start after the recorder-start response and use the driver clock.
Leave unknown alignment unresolved. Find video-time review targets in the actual
encode using [frames and contact sheets](beat-frames.md), then follow the
[verify-and-deliver workflow](../SKILL.md#4-inspect-the-actual-encode-and-record-findings).
No automatic driver-clock mapping is supported.

## Keep the result readable

Keep consequential typing and scrolling continuous. As an initial walkthrough rhythm, allow about 0.7 seconds of context and 1.5–2 seconds for a decisive value; adjust against the actual reading task. Retake unintentionally coarse or missing action rather than hiding it with an edit.

Use the manifest's focus ring when the target would otherwise be missed. Move it to the same value at a handoff and clear it before navigation or scrolling. Existing product emphasis may be sufficient; compare an uncued rehearsal when the ring's benefit is uncertain.

Rehearse the exact driver, then restore the starting state or use a fresh identified fixture for the take. Keep ordinary walkthrough action at normal speed. For presentation edits requested by the brief, follow [post-production](post-production.md).
