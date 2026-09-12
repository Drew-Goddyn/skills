# Build Loop examples

Use these illustrative cases to calibrate judgment, not as required stages. They are not records of completed tests.

## Contents

- [A coherent task can proceed without ceremony](#a-coherent-task-can-proceed-without-ceremony)
- [A reaction may need conversation before code](#a-reaction-may-need-conversation-before-code)
- [A confident diagnosis can still be wrong](#a-confident-diagnosis-can-still-be-wrong)
- [Evidence should match the experience and the claim](#evidence-should-match-the-experience-and-the-claim)
- [A fresh session is a tool, not a ritual](#a-fresh-session-is-a-tool-not-a-ritual)
- [Consolidation is an option, not unfinished acceptance](#consolidation-is-an-option-not-unfinished-acceptance)
- [Repeated repairs can signal a mistaken approach](#repeated-repairs-can-signal-a-mistaken-approach)
- [Ready means no more agent work](#ready-means-no-more-agent-work)

## A coherent task can proceed without ceremony

**Situation:** The human has selected a per-channel setting to disable weekly summaries without untracking projects. Scope and ordinary publication permissions are already clear.

**Useful move:** Give a complete brief with the desired setting, preserved tracking, visible confirmation, failure behavior, and evidence that disabling summaries does not untrack projects. Let the builder inspect the current configuration, implement, and verify. Do not request a separate plan just to approve filenames.

If inspection later reveals a confirmed regression, continue the same session with a bounded repair. For example, where ordinary pushes are already authorized:

**Send to the existing Codex session for this PR:**

```text
Continue the current PR; preserve its scope and user-facing flow.

The inspected error path rolls back the saved preference when the confirmation message fails. Preserve the successfully saved setting independently of confirmation delivery. Do not redesign unrelated notification handling.

Add a regression for a successful save followed by failed confirmation, covering both the stored preference and the reported outcome. Run relevant tests and required repository checks. Push normally under the existing authorization; do not merge or deploy.

Report the resulting behavior, revision, checks actually run, and remaining limitations.
```

**Avoid:** Making a mission document for the repair, prescribing every code edit, or adding unrelated cleanup.

## A reaction may need conversation before code

**Situation:** The human says, "It includes everything I asked for, but this report feels like a wall of text. I'm not sure what's wrong."

**Useful move:** Inspect the report and help locate the mismatch. When the sample gives everything equal prominence, a useful response is: "I think the issue is hierarchy rather than missing content. I'd lead with decisions and actions and move the supporting detail below. Is that the problem, or is there simply too much detail?"

Once the desired change is clear, send the corresponding assignment. Identify a refinement of the earlier brief as a changed requirement, not evidence that the builder failed to follow it.

If the human also reports telling Codex to auto-publish while the agreed scope was preview-only, reconcile that conflict explicitly. Recommend pausing possible external sends while the human settles the decision; do not claim to have stopped the agent. State which instruction the next brief supersedes.

**Avoid:** Reflexively dispatching "make it shorter," defending the output because tests pass, or treating a tentative idea as permission to publish.

## A confident diagnosis can still be wrong

**Situation:** A reviewer suspects that generic search intercepts explicit Slack-search requests. The builder reports thousands of passing tests, but neither statement settles the routing question.

**Useful move:** Inspect the dispatch order and relevant tests through available repository access. Without access, identify that limitation and ask for the narrow evidence needed. If still unresolved, send an investigation rather than assume a defect:

```text
Continue the existing PR. Validate whether generic search can intercept an explicit Slack-search request in the current dispatch path before changing code.

If confirmed, make a bounded routing correction with a regression at the dispatch boundary. Preserve existing aliases and generic-search behavior. If the current order already prevents interception, show the path and covering evidence and leave correct code unchanged.

Run relevant checks and required repository validation for any changes. Keep the established publication boundary. Report your conclusion, supporting paths and revision, checks actually run, and any remaining uncertainty.
```

If the evidence disproves the concern, withdraw it. Neither confidence nor a large test count substitutes for examining the relevant path.

**Avoid:** Requiring a patch to vindicate the reviewer, or ordering repeated reviews until one agrees.

## Evidence should match the experience and the claim

**Situation:** A settings-screen change needs human judgment; local preview and synthetic data are available.

**Useful move:** Include a small set of actual rendered screenshots, or a visual-review ZIP, in the assignment. Cover the changed flow and important states with an index identifying the captured revision or worktree, reproduction context, and simulated or untested behavior. Prefer existing tooling. Inspect the images, and seek behavior-level evidence when still images cannot establish an interaction.

The same discipline applies to provenance: if revision A was live-tested and revision B changes only comments, inspect that difference. Keep the live evidence attributed to A and explain its relevance to unchanged behavior; do not claim live testing happened on B or automatically repeat it. Required checks on B remain required.

If proving real delivery requires an unauthorized production message, identify the gap and needed authorization. Do not send it or label a replay as live delivery.

**Avoid:** Treating a green build as visual approval, building screenshot infrastructure for its own sake, or asserting that inaccessible artifacts were reviewed.

## A fresh session is a tool, not a ritual

**Situation A:** A related regression remains and the builder has useful context. Continue that session, naming its PR and the remaining delta. A failed test or third round does not justify a reset.

**Situation B:** The builder repeatedly follows a superseded requirement despite a clear correction. Recommend a fresh session, have the human stop or hand off the old writer, and supply a compact brief with the controlling decision, current branch/PR and revision, open work, evidence, and authorization. A new conversation does not require a replacement PR.

**Situation C:** A consequential uncertainty merits fresh scrutiny. Give a separate reviewer a focused, read-only question and evidence without prescribing a conclusion. Keep implementation with the builder; fresh context is not proof of independence or correctness.

When only the thinking-partner session is new, recover the current PR and compare changes since the last review. Do not reset both conversations or repeat completed work.

## Consolidation is an option, not unfinished acceptance

**Situation:** A feature is ready for QA. Recent assignments required reconstructing the same fragile replay setup twice, and related work is likely to need it again.

**Useful response:** "The feature has no remaining implementation blocker. Before the next related change, I recommend making that replay setup reusable: it has already cost us repeated setup work. Keep application behavior unchanged and bound the work to the repeated setup. That is a separate improvement, not a condition of accepting this PR."

Use existing authorization if it covers the work; otherwise present the choice before dispatching it. Invite the builder's specific observations, not a mandatory list of debt.

A boundary can also justify a small investigation with no preselected fix: "Determine whether the two workaround paths can share setup without hiding their different failure behavior; report the tradeoff before any broader rewrite." A finding that duplication is appropriate is a valid result. Reflection may also end with no worthwhile work to assign.

**Avoid:** "It's the cleanup round; find something to refactor," postponing a real correctness bug to cool-down, or manufacturing a retrospective artifact after every patch.

## Repeated repairs can signal a mistaken approach

**Situation:** Successive fixes keep moving failures between neighboring cases because the selected heuristic cannot express the distinction the feature needs.

**Useful move:** Stop treating each symptom as an isolated patch. Summarize what the failures reveal, inspect or request a bounded investigation of the premise, and recommend a simpler approach or explicit scope decision. Carry forward required safety and acceptance boundaries. Do not claim certainty that the architecture is wrong merely because several rounds occurred.

**Avoid:** Adding another special case automatically, imposing an arbitrary maximum round count, or weakening assertions until CI passes.

## Ready means no more agent work

**Situation:** The inspected repair resolves the last blocker; required checks pass. The human said manual QA would happen later. Optional naming changes have no material benefit.

**Useful response:** "The remaining blocker is resolved and required checks pass on the reviewed head. I would stop iterating. The PR is ready for your review; manual QA remains outstanding before final acceptance. No further Codex changes are needed."

Reflection does not change this result unless it reveals an actual reason to act. Do not merge or deploy without authorization. A requested PR-description polish can be done directly through an available connector, after reading the current description, rather than reopening implementation.

**Avoid:** Appending a cleanup assignment, printing an empty dispatch template, or announcing full validation while required human QA is outstanding.
