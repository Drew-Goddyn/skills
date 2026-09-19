# Start a task-local recording driver

Use this starter for a form that creates an identifiable result: prepare other
fields, type one decisive value, submit, then reveal the new result. It uses the
existing helpers and evidence format. For another flow, adapt `prepare()` and
`perform()` in the task-local copy; keep installed/copied shared helpers unchanged.

Copy [record_walkthrough.py](../templates/record_walkthrough.py) and
[walkthrough-inputs.json](../templates/walkthrough-inputs.json) into task scratch.
Fill the inputs from the brief, app and [environment observations](capture-environment.md).
The blank input intentionally cannot record. Select the skill directory explicitly:

```sh
python3 task/record_walkthrough.py --skill /path/to/record-product-demo \
  --inputs task/walkthrough-inputs.json --phase rehearsal --output task/rehearsal
# Inspect the actual rehearsal before the take; retain both outputs.
python3 task/record_walkthrough.py --skill /path/to/record-product-demo \
  --inputs task/walkthrough-inputs.json --phase take --output task/take
```

The selected location may be an authorized source checkout or a pinned task
copy. No installation is needed. The driver imports that exact `scripts/demo.py`
by file path and saves selected-file hashes, its own source and inputs. This
identifies uncommitted/copied bytes without inventing a clean Git revision.

Configure a task-only browser using the supported per-run settings in
[browser capture](browser-capture.md); keep Chrome's sandbox enabled. The unique
session name does not establish profile safety. Establish the target's account,
invented data and environment before setup, even when the URL is localhost.
Each phase uses the existing environment decision and recorder lifecycle.
Blocked observations save the helper's failed-take diagnostic before any browser
command. Startup/flow errors still fail; cleanup closes only the driver's session,
leaving the app server caller-owned. Failed/partial outputs are retained.

When capture settings are unverified, run the bundled moving preflight separately
in the configured task profile. Its result checks that synthetic fixture, never
the app's eligibility. Inspect the actual app rehearsal too. Neither a passing
preflight nor an application assertion proves the decisive action survived capture.

## Inputs and adaptation

- `url` is the authorized starting/reset URL and must equal `environment.url`.
  A reset must be authorized for this invented-data fixture; the driver makes no
  generic reset or cleanup mutations. Supply environment observations unchanged.
- `selectors` names the ready/open controls, decisive action field, submit control,
  simple result-collection selector, stable identity attribute and a neutral blur
  target. Result identities must be unique and nonempty. The starter asserts one
  newly identified result, never chooses the first existing row.
- `values.prefill` contains selector/value pairs for unrelated fields. `action`
  is typed through `Demo.type`; keep it out of prefill. `result_contains` lists
  the expected text in the newly identified result. This is an app assertion,
  not persistence replay or visual review.
- `labels` names context, action, submit and result beats. `holds` gives context,
  completed-action and result reading seconds. Change them to suit the brief.
- `viewport` supplies width/height; this helper requests 30 fps at scale 1.
  `brief` carries text, audience, takeaway, duration bounds and sound policy.
  Required sound uses the required-audio check; this starter does not add sound.
- `source` records the actual app/fixture revision, or null plus an explanation.
  Extra provenance such as fixture hashes remains in the copied source record.

The repository's development fixture and `template-invoice.json` demonstrate
these inputs. Invoice content stays outside the shared starter. Set its URL to
your task-owned fixture server and verify the profile observations before use.

## Inspect the generated delivery

A completed phase retains `reel.mp4`, the original `reel.take.json`, raw media
checker output/command, setup/cleanup/source facts and initial `evidence.json`.
The driver validates that record and returns `recorded_pending_review` when
capture and media checks pass. This is not a successful-delivery claim. A failed
media check with known picture measurements retains truthful evidence; unknown
picture timing leaves diagnostics without a fictitious measured reel record.

Beat references point to original driver events. Encoded-video times and clock
alignment stay unknown. Generate interval sheets with the existing frame tool,
inspect the native frames and necessary neighbors, and preserve the initial
record before adding attributed findings in a new delivery copy. Follow the
[evidence guide](evidence.md) for final-output times, privacy coverage and handoff.
Application assertions never fill in decisive findings, continuous viewing,
listening, privacy or human review. Missing inspection remains diagnostic.

`python3 <skill>/scripts/test_record_walkthrough.py -v` exercises supplied inputs,
real helper failure records and evidence construction with stubbed browser/media
operations. Those tests do not establish live capture or fresh-agent adoption.
