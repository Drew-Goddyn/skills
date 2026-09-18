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
