# Gameplay capture

Use this when the subject includes gameplay, camera movement, or an engine-rendered sequence. Choose the capture surface from the actual game: browser capture for a browser build, engine recording or an available game-window recorder for a native build. Browser helpers are not a prerequisite for native recording.

Establish the brief and [target environment](capture-environment.md) before an
app rehearsal or capture. For a native build, record browser-profile mode as not
applicable with a reason, keeping the environment, account and data observations.
The browser helper cannot enforce a decision for an engine recorder; apply the
same decision before starting it. Browser builds follow [browser capture](browser-capture.md).

## Use the running game's facilities

Read the project's launch and capture instructions. Prefer its existing recorder, replay, camera, and input facilities. For Godot, use the available `godot` skill when engine-specific launch or Movie Maker guidance is needed; otherwise inspect the installed engine's version and help. Keep version-specific commands with the task rather than copying them into a general capture recipe.

Record the engine or browser version, renderer, viewport/output dimensions, capture settings, scene state, and action sequence. Distinguish live capture from engine-rendered offline output. Offline frames can represent real game behavior without proving real-time performance. Preserve the input method: engine events, replayed actions, and actual window input establish different things about controls.

Use a short rehearsal in the actual scene to inspect representative movement and effects before committing to a long take. Retain raw frames and their timestamps when the chosen recorder provides them. Assess capture gaps during active motion separately from intentional stillness.

## Frame the mechanic

Discover what is legible and appealing in the game, then frame its action and consequence together. For a trailer, build anticipation and escalation around things the game can actually do. For a mechanics demo, leave enough context to understand cause and effect. Let the brief determine how many shots and how long they need.

Keep permitted camera, HUD, and recording controls local and reversible. Gameplay changes need their own authorization. Use the game's real physics, effects, AI, and results; document staging or input automation that affects what the footage demonstrates.

Retain a reproducible scene/reset procedure, action timing, and camera settings. A later soundtrack or title revision can use the saved footage. Use [post-production](post-production.md) when assembling or altering the presentation.

Keep the chosen recorder's failure diagnostics and source facts. After capture or
rendering, follow the [media-check and delivery workflow](../SKILL.md#3-prepare-the-delivered-encode-and-evidence).
Inspect action and result in the delivered encode and use final-output video
times for review targets. Unknown relationships to input or driver clocks remain
unknown; they do not prevent direct video-time inspection.
