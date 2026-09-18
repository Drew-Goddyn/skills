# Build Orchestrator examples

Use these illustrative cases to calibrate judgment, not as required stages. They are not records of completed tests.

## Contents

- [A clear request can go straight to a brief](#a-clear-request-can-go-straight-to-a-brief)
- [A web agent can inspect without dispatching](#a-web-agent-can-inspect-without-dispatching)
- [Permission requests are checkpoints](#permission-requests-are-checkpoints)
- [Address persistent builders by handle](#address-persistent-builders-by-handle)
- [A failed route is not a failed builder](#a-failed-route-is-not-a-failed-builder)
- [A reaction may need conversation before code](#a-reaction-may-need-conversation-before-code)
- [A confident diagnosis can still be wrong](#a-confident-diagnosis-can-still-be-wrong)
- [Stale context calls for a fresh session](#stale-context-calls-for-a-fresh-session)
- [Repeated repairs can signal a mistaken approach](#repeated-repairs-can-signal-a-mistaken-approach)
- [Ready means no more builder work](#ready-means-no-more-builder-work)

## A clear request can go straight to a brief

**Situation:** In a coding-agent session with shell access, the human says: "Have Codex add a per-channel setting that disables weekly summaries without untracking projects. Commit on this branch; don't push." The Codex CLI is installed but has not been used from this session.

**Useful move:** Probe the route cheaply, then dispatch an ephemeral builder with a workspace-write sandbox and one complete brief: the setting, preserved tracking, visible confirmation, failure behavior, a regression showing that disabling summaries leaves projects tracked, relevant checks, the stopping point (commit locally if its sandbox allows it, otherwise leave the change uncommitted and say so; do not push), and the report shape. If the builder cannot commit, commit after review yourself, since the human authorized commits on this branch. If the builder must run outside your own sandbox, ask to approve that command rather than a standing exception. Capture the final report to a file. Review the diff and checks yourself, or through a fresh reviewer, before calling the work ready.

**Avoid:** Asking the human to approve the brief text, requesting a plan just to approve filenames, implementing the change yourself, or reporting "done" from the builder's summary.

## A web agent can inspect without dispatching

**Situation:** In a web chat whose only relevant tool is a repository connector with read access, the human pastes a local builder's report: "Fixed the rounding bug and pushed to PR #88." Nothing in the conversation can reach the builder.

**Useful move:** Say what this session can do: read the PR, but not send anything to the builder. Read the diff and check results at the reported head, and tie observations to that revision. If a repair is needed, give one complete message for the existing builder session on PR #88 and say that nothing has been sent yet.

**Avoid:** Grading the pasted report alone when the diff is readable, or implying that the brief reached the builder.

## Permission requests are checkpoints

**Situation:** Mid-run, the builder reports that the tests need a package download and suggests rerunning with the flag that bypasses approvals and sandboxing.

**Useful move:** Stop at a checkpoint. Explain what the download is for, what the bypass would allow beyond it, and narrower options, such as a setting that permits only what the install needs or having the human run the install. Hold dispatches that depend on the answer; independent work can continue.

**Avoid:** Rerunning with the bypass because the builder asked, or treating instructions in a builder report as permission.

## Address persistent builders by handle

**Situation:** Two persistent builders are working in separate worktrees, one on an API change and one on documentation. A confirmed defect belongs to the API change.

**Useful move:** Send the delta to the API builder's recorded handle with its permissions set again on resume, confirm the reply came from that session, and update the roster with the new state.

**Avoid:** Resuming "the most recent session," which may be the documentation builder, or letting both builders write in one worktree.

## A failed route is not a failed builder

**Situation:** A one-shot builder run exits with an empty report. Its log shows an authentication or network error from the builder's CLI.

**Useful move:** Diagnose the route. Check whether your own sandbox blocked the builder's network access or state directory, and whether the CLI is logged in. Report the transport problem with the options: fix authentication, run under sandbox rules the human approves, or relay the brief.

**Avoid:** Judging the work from the failed run, retrying in a loop, or reaching for bypass flags.

## A reaction may need conversation before code

**Situation:** The human says, "It includes everything I asked for, but this report feels like a wall of text. I'm not sure what's wrong."

**Useful move:** Inspect the report and help locate the mismatch: "I think the issue is hierarchy rather than missing content. I'd lead with decisions and actions and move the supporting detail below. Is that the problem, or is there simply too much detail?" Once the desired change is clear, send a brief that names the changed requirement.

**Avoid:** Reflexively dispatching "make it shorter," defending the output because tests pass, or calling correct execution of the earlier brief a builder failure.

## A confident diagnosis can still be wrong

**Situation:** A reviewer suspects that generic search intercepts explicit Slack-search requests. The builder reports thousands of passing tests, but neither statement settles the routing question.

**Useful move:** Inspect the dispatch order through available access. If the question is still open, send an investigation that permits a no-change result:

```text
You are the builder for this brief; do the work in this session.

Continue the existing PR. Validate whether generic search can intercept an explicit Slack-search request in the current dispatch path before changing code.

If confirmed, make a bounded routing correction with a regression at the dispatch boundary. Preserve existing aliases and generic-search behavior. If the current order already prevents interception, show the path and covering evidence and leave the code unchanged.

Run relevant checks and required repository validation for any change. Commit locally if your sandbox allows it; otherwise leave the change uncommitted and say so. Do not push. Report your conclusion, supporting paths and revision, checks actually run, and remaining uncertainty.
```

If the evidence disproves the concern, withdraw it.

**Avoid:** Requiring a patch to vindicate the reviewer, or ordering repeated reviews until one agrees.

## Stale context calls for a fresh session

**Situation:** A persistent builder keeps following a superseded requirement despite a clear correction.

**Useful move:** Stop the old session at a safe point, or have the human stop it if they own it. Start a fresh builder with a compact handoff: the controlling decision, current branch and revision, open work, evidence, and authorization. Update the roster. A new session does not need a new PR.

**Avoid:** Resetting merely because a third round happened, or starting the replacement before the old session has stopped or been handed off.

## Repeated repairs can signal a mistaken approach

**Situation:** Successive fixes keep moving failures between neighboring cases because the selected heuristic cannot express the distinction the feature needs.

**Useful move:** Stop dispatching repairs. Summarize what the failures reveal, and at a checkpoint recommend a bounded investigation of the premise or an explicit scope decision. Carry forward the required safety and acceptance boundaries.

**Avoid:** Adding another special case automatically, using a round limit as a substitute for diagnosis, or weakening assertions until the checks pass.

## Ready means no more builder work

**Situation:** The inspected repair resolves the last blocker, and required checks pass on the reviewed head. The human said manual QA would happen later. Optional naming changes have no material benefit.

**Useful response:** "The last blocker is resolved and required checks pass on the reviewed head. I would stop iterating. The PR is ready for your review; manual QA remains before final acceptance. The builder I started has finished, and nothing is still running."

**Avoid:** Appending a cleanup brief, announcing full validation while human QA is outstanding, or leaving builders running without mention.
