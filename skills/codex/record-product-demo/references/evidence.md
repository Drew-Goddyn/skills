# Delivery evidence, version 1

Every reel gets its own delivery folder containing the reel and `evidence.json`.
Copy [the template](../templates/evidence.json), fill its empty fields, and run:

```sh
python3 <skill>/scripts/check_evidence.py <delivery>/evidence.json
```

Python's standard library is sufficient. Exit 0 means the record's structure,
local references, and stated consistency passed. Exit 1 reports the first useful
field error. Neither result judges the video. A truthful record of a failed
media check or unavailable visual review can be structurally valid. The validator
does not decode media, listen, inspect frames, detect private information, or
verify another reviewer's claims. Deliver the actual media-check and review
results separately from this structural result.

All reference paths are relative to the delivery folder, stay inside it, and
must exist. Copy needed inputs into that folder for a portable handoff. Keep
credentials, profiles, and unrelated material out. Preserve originals. If a
copied report needs path sanitization, record the original/copy hashes and exact
fields changed; never remove warnings, violations, or review gaps. Source-code
identifiers and historical paths *inside* raw records are provenance, not paths
the validator follows. Explain any unbundled historical attachments.

| Field | Contract |
| --- | --- |
| `schema_version` | Integer `1`. The blank template is deliberately incomplete. Map legacy evidence explicitly; rejection of an older format says nothing about its video. |
| `reel` | Relative filename, SHA-256, measured seconds and bytes. Use the media report's `picture.duration_seconds` when non-null, otherwise `duration_seconds`; copy the value without rounding. Hash and size are checked against the delivered file. |
| `brief` | Original brief file, audience, takeaway, decisive moments, min/max seconds (`null` if unspecified), and `forbid`, `allow`, or `require` sound policy. Preserve different briefs for different edits. |
| `environment` | Kind, URL (`null` for no URL), signed-in account kind (never credentials), and relevant conditions/versions. For new capture, include the [pre-capture observations](capture-environment.md): authorization, data provenance, profile mode and production indicators; preserve the decision in the original take's `capture_request`. Explicitly say when context is inherited from source footage. Edit-only work needs no invented capture decision. |
| `source` | Revision or `null`, note naming what that revision identifies and any missing application revision, and a provenance file. Include source/fixture hashes there when Git is unavailable. |
| `production` | `capture`, `edit_only`, or `capture_and_edit`. Capture modes reference capture settings and explain context. Edit-only uses `capture: null`; capture-only uses `edit: null`. |
| `takes` | IDs, `new_capture` or `source_capture` roles, and references to the original take JSON, including useful failed takes. Do not rewrite its schema, outcome, timing, or pending-review field. A new capture needs a new-capture record; an edit need not invent one. |
| `beats` | Unique id, kind, label, decisive boolean, separate driver/video times, alignment, and timing note. See clock rules below. |
| `checks` | Unique id, kind, `performed`, `not_run`, or `unavailable`, raw JSON report or `null`, and context naming command/options/tool revision and limitations. Include kind `media` even when unavailable. No copied pass/fail summary: the raw result and warnings remain authoritative and are echoed in validator output. A performed media check's available measurements and audio policy must agree with the reel/brief. Save checker startup/parse failures too (`status: error`, `error` message, emitted on stderr); these establish no measurements. State the independent measurement source in context if the checker errored. |
| `review` | Separate `agent_frames`, `continuous_watch`, `listening`, and `human` records. Each uses `status`, descriptive `coverage`, and evidence paths; `performed` requires evidence. Other states are `not_performed`, `unavailable`, `not_applicable`, with an explanation. Human evidence contains actual answers and provenance, or states they were not collected. `watch_list` names review targets with encoded-video ranges (or `null` and explanation) and labels; it is not proof of watching. |
| `privacy` | Explicit coverage/status/evidence plus findings: safe description, encoded-video range or `null`, timing note and supporting samples. Sampled review adds author/relay, inspected samples and sheets; see below. Empty findings alone never means reviewed or safe. |
| `limitations` | Remaining gaps as text, including missing watch/listen coverage or unknown timing. |
| `reproduction` | Setup/scene/action context, created-record IDs if any, and cleanup using the coverage/status/evidence contract. Edit-only work may state cleanup is not applicable because it started no sessions. |
| `toolkit` | Status (`pending`, `running`, `improved`, `no_change`, `blocked`), friction entries with issue/evidence, actual owner or `current_task`, scope, and result. Result records reason, changed source-file identifiers, check-output paths, verified tool version, normal discovery route, and next action. `improved` requires changes/checks/version/discovery; unfinished work requires next action. `no_change` requires a reason. Empty friction is not an assertion that a tooling review occurred. Ordinary recording logs friction as pending and keeps skill copies unchanged; only an explicitly authorized maintenance assignment follows the [source-maintenance guide](toolkit-maintenance.md). Proposed, locally tested, reviewed/published and installed states stay distinct in result context; a patch alone is not improved. |

Credit a review to its author and identify any relay separately. An agent-authored
assessment relayed by a human remains agent review; keep it distinct from the
recording agent's own inspection. When no direct human viewing result was
collected, use `review.human.status: unavailable` and say the result is
uncollected, without claiming that person never watched. Keep sample-selection
decisions separate from viewing evidence. Explain corrected attribution in the
new record while preserving inherited raw prose. The validator does not infer
authorship from text.

## Clocks and edits

`driver_time: {"take": "take-1", "event_index": 2}` points to the existing take's
`events[2].at` in seconds. It does not copy or reinterpret that timestamp as video
time. Use `null` when unavailable. For each beat, `video_time` is either `null`
or `{"seconds": [start, end], "precision": "exact|sampled|approximate", "basis": "..."}`.
Video seconds are relative to the start of the delivered encode, never wall time.
Ranges may be points. State `alignment: unknown` unless there is evidence linking
the driver and video clocks. `approximate` and `verified` require both clocks and
a basis in `timing_note`. Frame observations can be known while alignment is
unknown. Asynchronous recorder startup is not an established zero offset.

Generate beat frames and interval contact sheets with the [encoded-frame
tool](beat-frames.md). It consumes these final-output video times, preserves
unknown alignment, and writes a separate index without changing the evidence.
Keep the extracted frames and sheet coverage distinct from review findings.

For edits, `production.edit` has `settings` (original edit/render record), `inputs`
(media entries with `id`, path, SHA-256, duration and size), and `timeline`:

```json
{
  "status": "known",
  "basis": "Source frames 30–90 at 30 fps, cut to output frames 0–60 at 30 fps; end exclusive.",
  "segments": [
    {"input": "source", "source_seconds": [1, 3], "output_seconds": [0, 2], "speed": 1}
  ]
}
```

This map relates encoded source and output clocks, independently of driver
alignment. Use nonoverlapping segments for representable trims/retiming; explain
any gaps (for example titles) in `basis` and preserve all transforms in settings.
For unavailable maps or transforms this small representation cannot express,
use `status: unknown`, an explanation, and an empty segments list. Never invent a
linear mapping for a transition or changing speed. The validator checks ranges,
references, order, and speed/span arithmetic (1e-9 numerical representation
precision, not a codec tolerance). It does not inspect the edit or infer maps.

## Decisive frame findings and the watch list

After the media check and extraction, inspect the relevant sheets and native
frames yourself. An extracted file or a populated thumbnail is not a visibility
finding. Use neighboring frames when a midpoint cannot establish a change; if
coverage is insufficient, record `unresolved`. Missing timing never proves an
action absent. Record only what the selected frames support, including where a
single result frame cannot establish motion, smoothness or first-watch pacing.

Version 1 optionally adds `review.beat_findings`. Older records without it remain
structurally valid, but do not establish decisive-frame review readiness. Each
entry has one existing `beat_id` and these fields:

| Field | Contract |
| --- | --- |
| `status` | `supported`, `not_visible`, `unresolved`, or `unreviewed`. The first two require known encoded timing plus inspected native samples and their sheets. `not_visible` is a review finding within the stated coverage, not an extractor inference. |
| `author` | `{ "kind": "agent|human", "name": "actual inspecting author" }`; null only for `unreviewed`. A script's synthetic pixel assertion must identify itself as such, not as human review. |
| `relay` | Same actor shape when someone relays the finding; otherwise null. A human relay never changes an agent author's identity. |
| `observation` | What is visible, missing or unresolved, naming the decisive content rather than merely saying a file exists. |
| `coverage` | Which frames/sheets were inspected and what they cannot establish. Keep native inspection separate from thumbnail-only context and earlier reviewers' claims. |
| `samples` | References of the form `{ "index": "frames-review/frames.index.json", "sample_id": "beat-0002" }`. Neighboring beat or interval samples may support a sequence. Use the index's decoded timestamps and paths; do not copy competing timing facts. Missing/unresolved index entries can support an unresolved finding, never a visibility verdict. |
| `sheets` | Inspected sheet paths relative to the delivery. A visibility finding needs a sheet containing each supporting sample. `unreviewed` has empty samples/sheets, even when extracted material exists. |

For example, a sampled result finding can reference `beat-0002`, describe the
saved value and identifier visible there, and limit coverage to that native
frame. Typing usually needs several successive frames. Use the existing
extractor with denser intervals or a separate extraction-input copy containing
additional encoded-time targets. Keep that input, its index and frames; leave
the primary beat timing, original take records and edit map unchanged. Reference
the additional samples in the finding. The index binds to the reel hash and
retains its input-evidence hash. Keep that input snapshot before adding findings
to the delivery evidence; adding findings need not rewrite an extraction index.

For each decisive beat, add a watch-list row with `beat_id`, `label`,
`video_seconds`, `precision`, and `note`. Copy the beat's final-output range and
precision exactly; use null for both when timing is unknown. A row may explain
the need for another look or a coverage gap. An exact decoded sample timestamp
does not make an approximate or sampled beat exact. Existing unlinked rows remain
valid historical evidence but do not fulfill this handoff's linked targets.

```sh
python3 <skill>/scripts/check_evidence.py <delivery>/evidence.json
python3 <skill>/scripts/review_delivery.py <delivery>/evidence.json <delivery>/handoff
```

The second command writes `HANDOFF.md` and `review-readiness.json` to a **new**
directory without changing inputs. Include the short timestamped watch list in
the response and both files in the review ZIP. Exit 0 / `ready_for_review` means
all designated decisive beats have supported findings, linked targets and a
passing recorded media check, with no known privacy finding. An unperformed
privacy review can still accompany a useful review package, prominently marked
unreviewed. Ready does not mean successful delivery, completed
viewing or acceptance. Exit 1 / `diagnostic_only` names unreviewed, not-visible,
missing or unresolved moments, missing targets, and unsuccessful/unperformed
media checks, as well as any known privacy finding. Deliver that diagnostic record with its blockers; do not describe
the reel as an unqualified success. Exit 2 is a structural/reference error or an
unwritable/existing output path.

Copy the handoff's four optional viewer-feedback questions into the response
alongside the watch list and review ZIP, including for diagnostic packages. They
ask about the action/result, moments needing another look, screen content that
should not be public, and suitability for a pull request. The user need not watch
or answer before an independent agent reviews the package. Unanswered questions
do not affect readiness or count as performed human review. Keep an uncollected
human result explicit; if feedback later arrives, record its actual author and
coverage, with any relay separate. A relayed agent assessment remains agent
review. The questions themselves establish no viewing or privacy clearance.

The evidence validator checks author fields, index/reel identity, referenced
frame hashes, sheet membership, and linked watch timing. It cannot verify who
actually inspected an image or judge its meaning. Visibility findings must also
agree with the corresponding agent/human coverage status. A truthful
failed/incomplete
finding can pass structural validation. The handoff preserves raw check results,
warnings and coverage limitations; it never promotes frame inspection to a
continuous watch, listening result, human viewing result or privacy clearance.

## Sampled privacy review

Inspect the final encode's beat and whole-reel interval sheets and their native
frames for unintended names/contact details, credentials or tokens, notifications
and internal URLs. Use the brief and known data provenance: an intended invented
client name is not automatically a privacy defect. Apply this to edit-only work
as well. A passing capture-environment check says nothing about the final frames.

Use the existing `privacy` block. Version 1 optionally adds these fields; older
records remain structurally valid without inventing new inspection evidence:

- `author` and `relay`: the same actor shape as beat findings. Credit the actual
  inspector; an agent finding relayed by a person stays agent review. Use null
  for both when inspection is unperformed or unavailable.
- `samples`: the existing `{index, sample_id}` references for **native frames
  actually inspected**, including relevant beat and interval samples.
- `sheets`: paths of inspected sheets containing those samples. `performed`
  sampled review needs its author, samples, sheets and an evidence report.
  Other statuses use empty samples/sheets. Extracted or missing placeholders
  cannot count as inspected images.
- `coverage`: describe the sampling interval, actual inspected times/count,
  uninspected or unresolved material and any limits on reading small text. The
  referenced index retains requested/decoded times and extraction coverage;
  extraction coverage is not inspection coverage. Missing samples stay gaps.
- `findings`: keep `description`, `video_seconds` and `timing_note`; add `samples`
  referencing supporting inspected frames. Use a concise concern and location,
  such as "unintended token in upper-right notification; value omitted", without
  transcribing sensitive values. Known ranges use the **delivered-output** clock
  and include supporting frame timestamps. A sampled point does not establish
  onset or duration. Use null with an explanation when timing is unresolved.
  A relayed concern with no available inspection can retain an empty samples
  list and unavailable review status; the concern still prevents clean delivery.

The validator checks references, frame identity, sheet membership, attribution
fields and supplied timing consistency. It cannot check an author's claim to
have inspected a frame or detect private content. A truthful incomplete or
failing privacy record remains structurally valid. An empty findings array is
only "no findings in inspected samples" when an attributed sample review is
recorded; historical performed records without that detail are not upgraded.

`review_delivery.py` preserves the privacy block and resolves sample timestamps
in its JSON and handoff. Known findings produce `diagnostic_only`, including
concerns with unknown times. Missing review is prominently unreviewed. Sampled
review with no findings can remain `ready_for_review`, always with the warning
that content between inspected samples can be missed. Neither outcome is privacy
clearance, publication approval or a requirement for human viewing before review.

The helper writes metadata only; it does not copy or sanitize media. Preserve
real flagged reels/frames locally, then share only specifically authorized
material. If that authorization is absent, send the generated metadata diagnostic
after checking its descriptions for sensitive values. Explain omitted files in
the package index; keep the complete reference-valid evidence local rather than
presenting the limited package as a full portable delivery. For authorized
invented fixtures, the complete visual evidence can accompany the diagnostic.

## Toolkit follow-up in the handoff

The delivery helper includes the existing `toolkit` block unchanged in
`review-readiness.json` and summarizes its status, owner, scope, friction, source
changes/checks, version/discovery and next action in `HANDOFF.md`. This reports
the supplied state; it does not verify maintenance claims, grant authority, or
infer review, publication or installation. The [maintenance guide](toolkit-maintenance.md#use-the-existing-toolkit-record)
defines the statuses. A pending or blocked optional improvement can accompany
a ready review package. Existing capture/media, decisive-frame and privacy
blockers remain effective; toolkit status cannot turn them into a success.
