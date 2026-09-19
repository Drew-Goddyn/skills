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
| `environment` | Kind, URL (`null` for no URL), signed-in account kind (never credentials), and relevant conditions/versions. Explicitly say when context is inherited from source footage. |
| `source` | Revision or `null`, note naming what that revision identifies and any missing application revision, and a provenance file. Include source/fixture hashes there when Git is unavailable. |
| `production` | `capture`, `edit_only`, or `capture_and_edit`. Capture modes reference capture settings and explain context. Edit-only uses `capture: null`; capture-only uses `edit: null`. |
| `takes` | IDs, `new_capture` or `source_capture` roles, and references to the original take JSON, including useful failed takes. Do not rewrite its schema, outcome, timing, or pending-review field. A new capture needs a new-capture record; an edit need not invent one. |
| `beats` | Unique id, kind, label, decisive boolean, separate driver/video times, alignment, and timing note. See clock rules below. |
| `checks` | Unique id, kind, `performed`, `not_run`, or `unavailable`, raw JSON report or `null`, and context naming command/options/tool revision and limitations. Include kind `media` even when unavailable. No copied pass/fail summary: the raw result and warnings remain authoritative and are echoed in validator output. A performed media check's available measurements and audio policy must agree with the reel/brief. Save checker startup/parse failures too (`status: error`, `error` message, emitted on stderr); these establish no measurements. State the independent measurement source in context if the checker errored. |
| `review` | Separate `agent_frames`, `continuous_watch`, `listening`, and `human` records. Each uses `status`, descriptive `coverage`, and evidence paths; `performed` requires evidence. Other states are `not_performed`, `unavailable`, `not_applicable`, with an explanation. Human evidence contains actual answers and provenance, or states they were not collected. `watch_list` names review targets with encoded-video ranges (or `null` and explanation) and labels; it is not proof of watching. |
| `privacy` | Same explicit coverage/status/evidence contract plus findings: description, encoded-video range or `null`, and timing note. Empty findings alone never means reviewed or safe. |
| `limitations` | Remaining gaps as text, including missing watch/listen coverage or unknown timing. |
| `reproduction` | Setup/scene/action context, created-record IDs if any, and cleanup using the coverage/status/evidence contract. Edit-only work may state cleanup is not applicable because it started no sessions. |
| `toolkit` | Status (`pending`, `running`, `improved`, `no_change`, `blocked`), friction entries with issue/evidence, actual owner or `current_task`, scope, and result. Result records reason, changed source-file identifiers, check-output paths, verified tool version, normal discovery route, and next action. `improved` requires changes/checks/version/discovery; unfinished work requires next action. `no_change` requires a reason. Empty friction is not an assertion that a tooling review occurred. See [maintenance guidance](toolkit-maintenance.md) only when relevant and authorized. |

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
passing recorded media check. It does not mean successful delivery, completed
viewing or acceptance. Exit 1 / `diagnostic_only` names unreviewed, not-visible,
missing or unresolved moments, missing targets, and unsuccessful/unperformed
media checks. Deliver that diagnostic record with its blockers; do not describe
the reel as an unqualified success. Exit 2 is a structural/reference error or an
unwritable/existing output path.

The evidence validator checks author fields, index/reel identity, referenced
frame hashes, sheet membership, and linked watch timing. It cannot verify who
actually inspected an image or judge its meaning. Visibility findings must also
agree with the corresponding agent/human coverage status. A truthful
failed/incomplete
finding can pass structural validation. The handoff preserves raw check results,
warnings and coverage limitations; it never promotes frame inspection to a
continuous watch, listening result, human viewing result or privacy clearance.
