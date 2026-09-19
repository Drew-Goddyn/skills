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

Read [the technique manifest](../techniques.json) before writing a driver. Import the existing browser helpers into a task-local script and use native commands for unsupported interactions. The manifest owns entrypoints, prerequisites, limitations, and executable checks.

Use `agent-browser` for browser interaction and viewport recording. Follow the installed executable's help. Put it on `PATH`, or set `DEMO_BROWSER` to an executable path or command name; the override takes precedence. Put FFmpeg's `ffmpeg` and `ffprobe` on `PATH` too. Tools are not searched in platform-specific installation directories. Use a short task-specific `AGENT_BROWSER_SOCKET_DIR` if the default is unwritable or the socket path is too long. A blocked launch calls for the supported scoped escalation, preserving the failure.

Run the moving preflight when the recorder or settings are not yet verified for this task. After configuring and checking the task-only profile, pass `--browser-profile-mode task_only`; this records the caller's selection and does not inspect or configure the browser. Match the take's format and inspect actual output dimensions, including device scale. The fixture tests motion, an idle hold, and resumed motion; it does not establish the target app's environment, the completeness of a different flow or the capture rate of a busy game.

Use the task rehearsal to inspect its characteristic action. For a form, confirm that the decisive typing, click, saved result, and reading hold survived capture. For animation or a browser game, sample the actual scene under the planned camera movement and rendering load. Encoded frame rate alone does not establish source cadence. Choose an alternative only after a relevant comparison supports it, and preserve the original failure.

## Keep the result readable

Keep consequential typing and scrolling continuous. As an initial walkthrough rhythm, allow about 0.7 seconds of context and 1.5–2 seconds for a decisive value; adjust against the actual reading task. Retake unintentionally coarse or missing action rather than hiding it with an edit.

Use the manifest's focus ring when the target would otherwise be missed. Move it to the same value at a handoff and clear it before navigation or scrolling. Existing product emphasis may be sufficient; compare an uncued rehearsal when the ring's benefit is uncertain.

Rehearse the exact driver, then restore the starting state or use a fresh identified fixture for the take. Keep ordinary walkthrough action at normal speed. For presentation edits requested by the brief, follow [post-production](post-production.md).
