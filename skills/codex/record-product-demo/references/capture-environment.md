# Check the environment before new capture

Before recording or rehearsing the target app, establish its environment,
account kind, data provenance and browser-profile mode from the brief, source or
seed, visible environment/account indicators, and task configuration. Use a
separate task-only browser for any permitted inspection. Existing authorization
carries forward; known invented data in an authorized local/test environment can
proceed without another routine approval.

Stop capture and ask for clarification if any of these facts remain unresolved,
if production indicators are present, or if the browser uses a personal profile
or attaches to an existing browser. Keep the observed concern in the request:
for example, “The localhost page is labelled PRODUCTION. Which local/test
instance with invented data should I record?” A localhost URL alone establishes
neither the account nor the data source. Known invented client names remain
invented even when they look realistic; unexplained realistic records require
provenance, not a guess based on names.

For browser capture, use the existing evidence `environment` object with these
explicit observations. Pass it to every `Demo.record` call, including rehearsal:

| Field | What to establish |
| --- | --- |
| `kind` | `local` or `test`; production and unknown targets stop capture. |
| `url` | Actual target URL. Check environment banners and domain context separately. |
| `signed_in_account_kind` | `test` or `demo`; use `none` only when no login exists. Never record credentials or invent a signed-in account. |
| `conditions` | Concrete observations and their sources: brief authorization, environment indicators, account state, fixture/seed provenance, and the task profile configuration. Empty findings alone do not establish that inspection occurred. |
| `authorized_for_capture` | `true` only when the task authorizes recording this local/test target. Unknown stays null. |
| `data_provenance` | `invented` with its source explained in `conditions`; unresolved or real data stops capture. |
| `browser_profile_mode` | `task_only` after checking configuration. Personal, attached or unknown profiles stop capture. Use the tool's supported per-run settings; do not change global installations. |
| `production_indicators` | Observed concerns as strings; `[]` only after checking. Null means unknown, not clear. |

```python
# Populate from current observations, not from the URL or a previous preflight.
observed = task_evidence['environment']
with demo.record('rehearsal.webm', environment=observed):
    ...
```

The helper evaluates supplied facts before recorder startup. It cannot recognize
banners, authenticate an account, inspect a profile configuration, or classify
private data. Recheck observations when the target, account, dataset or profile
changes. Native/engine capture follows the same local/test and invented-data
decision guidance; record browser-profile mode as not applicable when there is
no browser. `Demo` is the browser helper, not a guard around other capture tools
or direct native commands.

New take records retain their existing shape with optional `capture_request`
context: requested FPS, the supplied `environment`, and an `environment_check`
decision with reasons. A blocked attempt writes a failed take with
`failure_stage: environment_check`, null timing, empty events/recorder facts and
an actionable error, then raises. Its `video` is the requested path, not an
existing reel. Deliver that diagnostic and the clarification request; do not
fabricate a complete reel evidence file. Startup failures after an allowed
decision still use `failure_stage: recorder_start`. Earlier take records stay
unchanged.

For a delivered reel, copy the observed facts to the existing `environment`
fields and reference the original take records; preserve the capture settings
reference. This decision establishes eligibility from those observations, not
completed privacy review, continuous viewing, or publication approval.

The trusted bundled preflight contains invented motion graphics and no account
or application data. It remains allowed in a verified task-only profile. Pass
`--browser-profile-mode task_only` to `preflight.py` after configuring that
profile; the flag reports the caller's check, it does not configure or inspect
the browser. An omitted/unknown mode stops before any browser command and saves
the failed take diagnostic. A passing preflight proves nothing about the target
app's environment: establish that app separately before its rehearsal or take.

Edit-only work retains source provenance and outstanding privacy limitations.
It does not need new capture observations or a fictitious allowed decision.
