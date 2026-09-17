# Tock: improve the reusable toolkit

Turn demonstrated recording friction into one bounded improvement within the requested scope. App-specific selectors, fixtures, camera choices, and story content stay in task scratch. A successful reel can justify investigating a technique; it does not establish that the technique is safe to promote into the shared workflow.

## Handoff and owner

Use the recording evidence's `toolkit` section as the work record:

- `status`: `pending`, `running`, `improved`, `no_change`, or `blocked`.
- `friction`: the recorder's issue records and linked evidence.
- `owner`: the actual maintenance task or agent identifier, or `current_task` when working in place.
- `scope`: shared toolkit or the user-requested local experiment.
- `result`: changed files, checks and their output paths, the verified tool version, and how the next demo reaches the improvement. For `no_change` or `blocked`, record the evidence and reason; a blocked pass also names the next action needed.

When delegation is available and permitted, assign one maintenance subtask to a fresh agent. Supply this skill, the work record, relevant drivers and raw artifacts, the allowed edit scope, and the verification criteria. Give it ownership of the affected toolkit files and require an implemented result or a justified no-change decision. Otherwise, perform the same bounded pass in the current task. Use a standalone task only when the user has authorized its creation.

The recorder owns the reel and cleanup; the maintainer owns the selected toolkit improvement and its checks. Record the owner before handing off so pending work is recoverable.

## Make the smallest useful change

Inspect the relevant shared helpers and their callers alongside the run evidence. Select one concrete source of repeated work or failure.

Prefer improving an existing helper or default. Combine overlapping helpers when the observed callers demonstrate the same need; inspect and update those callers before removing an entrypoint. Promote a new technique only after successful use. Update its entrypoint, usage, limits, tested version, and reproducible check in `techniques.json` in the same change, so subsequent drivers discover and use it.

Repeated clarity problems can also justify a reusable story technique. Its entrypoint may be a reference describing when it helps, what must remain visible, and its common failure. Link the successful reel and first-watch response in its check. Promote the demonstrated treatment through the same manifest; keep app-specific story content in the run evidence.

Use repeated adaptations in the supplied run history to justify consolidation within the selected problem.

For example, a capture that freezes after a long hold can justify improving the shared preflight to exercise motion, a hold, and renewed motion. The handoff should include the failing capture and the working reproduction so the maintainer can demonstrate that the revised check catches the failure.

## Verify and close

Establish the original failure or repeated work from the saved evidence or a minimal reproduction. For executable helpers, run the affected checks and replay the triggering sequence through the shared entrypoint after the change. For story techniques, apply the documented technique to the triggering flow and compare fresh first-watch responses for the original and revised reels. Use a local fixture when it exercises the same property. Any live application actions must remain within the handoff's authorization. If a changed recording or encode needs visual verification, use the playback requirements in the skill's check-and-deliver step.

For a shared update, mark `improved` only when the change is applied, the relevant checks pass, and the next normal demo can reach it through the shared helper or manifest. Save the proof in `toolkit.result`. Notes in scratch and proposed patches alone do not meet that condition.

For a requested local experiment, preserve the starting version and failed artifacts, then implement and freeze the smallest candidate. Test it with a fresh agent on another example and a representative original use case, supplying the request and raw inputs before the builder's conclusions. Record experiment completion separately from adoption readiness. A completed negative evaluation is a valid bounded outcome; leave the shared toolkit unchanged when promotion is unsupported or outside the request.

Mark `no_change` when the evidence supports keeping the shared toolkit as it is, such as an isolated app quirk with no useful generalization. Mark unresolved permission or verification gaps `blocked`; retain the owner and next action. A ready reel can still be delivered with that maintenance status stated accurately.

Close the pass after its selected problem is resolved. Report the practical benefit in one sentence, such as: "The preflight now checks motion after a pause, so the next demo can catch this freeze before recording the real flow."
