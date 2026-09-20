# Authorized toolkit maintenance

Use this guide for a separate, explicitly authorized maintenance assignment.
Recording friction alone does not create that assignment. An ongoing source
improvement session already authorized for implementation and review follows
its standing authority; it needs no repeated owner approval for assigned work.

## Recording and maintenance have different owners

During ordinary recording, preserve reusable friction and its evidence in
`toolkit`, then continue with existing supported capabilities where possible.
App-specific drivers, selectors, fixtures and authorized task-local adaptations
belong to the recording task. Keep installed and copied skill files unchanged;
recording friction does not authorize toolkit edits or maintenance agents.
The recorder owns the reel and cleanup. Optional maintenance need not delay a
usable reel; actual capture, media, decisive-frame and privacy blockers remain
blockers and require a truthful diagnostic handoff.

An authorized maintainer owns one bounded source outcome and its checks. Carry
forward the relevant failure evidence, original versions, permitted edit scope,
verification criteria and review/publication checkpoints. Delegation is a
separate action governed by that assignment, never an automatic response to
friction. Record the actual owner, or `current_task` for the task holding the
record; that label grants no additional authority.

## Verify the source before editing

Work in a Git checkout of the intended [source repository](https://github.com/Drew-Goddyn/skills),
not whichever installed or task-local copy was loaded. Verify the repository
root, remote identity, branch, HEAD and working-tree state. Record the source
basis and preserve other writers' changes. An installed/copy version can be
failure evidence; it is not the maintenance destination. Keep that original
copy unchanged so the observed failure remains reproducible.

If no source checkout is available, keep maintenance `blocked`. With sufficient
original source bytes and identity, prepare a portable patch against a separate
scratch snapshot; retain the base revision or content hashes, reproduction and
verification limits. Keep the loaded copy unchanged. A proposed patch is not an
applied or installed improvement. If the source basis is insufficient, preserve
the finding and the information needed to proceed rather than inventing a patch.
Name the missing checkout/basis and next action in the record.

## Make and verify the bounded change

Inspect the relevant shared helpers and callers alongside the saved evidence.
Establish the original failure or repeated work with a minimal reproduction.
Prefer an existing helper/default and change only what the assignment needs.
Keep application story content in task scratch. When a technique changes,
update its usage, limits, discovery route and relevant check in `techniques.json`.

Run the affected checks and reproduce the changed behavior through its shared
entrypoint. Verification must fit the assignment: source/record tests do not
establish live capture, fresh-agent compliance or audiovisual quality. Preserve
unperformed coverage. A story/recording experiment needs its own authorized
inputs, viewing coverage and run budget; it is not a prerequisite invented by
this guide. Close the bounded source outcome through the assignment's review
checkpoint and authorized commit or pull request. If review requires an
uncommitted candidate, stop at that handoff and publish after acceptance under
standing authority. Merging and installing remain separate decisions.

## Use the existing toolkit record

Use `friction` for the issue and evidence paths, `owner` for the responsible task,
and `scope` to distinguish recording-only follow-up from authorized maintenance.
Keep `result` fields as defined in the [evidence guide](evidence.md):

| Status | Meaning for this assignment |
| --- | --- |
| `pending` | Recording logged reusable friction; a maintenance assignment is still needed. Shared `changed_files` and checks stay empty when no source work occurred. Name the next action. |
| `blocked` | Authorized maintenance cannot proceed because checkout, source basis, authority or verification is unavailable. Retain any portable proposal as evidence, identify it as unapplied, and name the missing condition/next action. |
| `running` | Authorized source work or its required review/publication is unfinished. A locally tested candidate awaiting independent acceptance stays here. |
| `improved` | The bounded source change is applied, relevant checks pass, and the assignment's required review/publication steps are complete with a documented route to use it. This status does not imply installation. |
| `no_change` | Evidence supports leaving the toolkit unchanged, or no shared maintenance is needed. Give the reason; do not use it to hide unresolved reusable friction. |

In `result.reason`, distinguish proposed, applied/locally tested, independently
reviewed, and published source work from the installed version. State unknown
or unperformed stages explicitly and link supporting artifacts through the
existing friction/check references. `changed_files` names applied source edits,
not task drivers or an unapplied proposal. `checks` references actual results,
including failures and limits. `tool_version` identifies the source/candidate
that was checked; `discovery` says how the next authorized use reaches that
version and whether the installed route still points to an older version.
`next_action` keeps unfinished work recoverable. Never infer installation from a
local check, review acceptance, commit or push.

The delivery helper reports this block separately and verbatim in its JSON;
it does not schedule work, authorize edits, promote statuses or install tools.
It does not use optional maintenance status to waive or add reel-review blockers.
