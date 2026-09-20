---
name: record-product-demo
description: Record and edit video demos, screen recordings of web apps, and game showcases. Use for product walkthroughs, PR reels, and trailers. Requires Python 3 and FFmpeg/ffprobe; browser capture uses agent-browser, and contact sheets need Pillow >=10.1.
---

# Record demos and trailers

Show real behavior and its result. Let the brief determine duration, framing,
sound and editing; keep source footage, actions and presentation changes traceable.

## 1. Establish the brief and choose the branch

Record the audience, intended takeaway, decisive moments, media limits, sound
policy, source revision and capture or source-footage conditions. For before/after
claims, use corresponding revisions and equivalent inputs. Establish authorized
setup, restoration and created-record or scene identifiers. Choose beats from the
actual product or supplied footage, connecting action and result; give each hold
a purpose.

Arrange review coverage early: who can inspect native frames, watch the complete
encode at normal speed, and listen when sound matters? Record unavailable coverage
explicitly and continue with the checks available. Playback counters, thumbnails
and audio meters cannot supply a missing audiovisual judgment.

| Work | Route |
| --- | --- |
| New browser footage | [Browser capture](references/browser-capture.md); use the [starter](references/recording-driver.md) for a form-to-result flow or a task-local driver for other interactions. |
| Gameplay or engine output | [Gameplay capture](references/gameplay-capture.md); browser builds also follow browser capture. Native recording uses the project's recorder/input facilities. |
| Edit existing footage or add presentation/sound | [Post-production](references/post-production.md); retain source provenance and edit maps. Edit-only work needs no fictitious new take or environment decision. |
| A demonstrated capture/encode/playback failure | Preserve the failing output and follow [media repair](references/media.md) within the task's authorized scope. |

Use [the technique manifest](techniques.json) for supported entrypoints, tool
prerequisites and focused checks. Python 3 and FFmpeg/ffprobe are needed for media
verification; frame sheets also need Pillow >=10.1. Browser tools use `DEMO_BROWSER`
or PATH as described in the browser guide. Resolve launch restrictions through
supported per-run settings and required host approvals, preserving failures. Run
manifest commands from the selected skill directory and substitute concrete task
paths for placeholders.

## 2. Establish the environment, then capture when needed

Before target-app rehearsal or capture, follow the [environment decision](references/capture-environment.md).
Proceed with known invented data in an authorized local/test environment, a
confirmed no-login/test/demo account and a task-only browser profile where a
browser is used. Production indicators, a personal/attached profile or unresolved
environment/account/data facts stop capture and require clarification. A localhost
URL alone is insufficient. Record actual observations; realistic invented names
remain invented. Native capture follows the same eligibility guidance, with no
browser profile to invent.

For browser work, select the skill directory explicitly in the starter or import
its helpers into the task-local driver. Use the bundled moving preflight when
recorder settings are unverified for this task; check the target app separately.
Rehearse the intended action under representative load, inspect the actual
rehearsal encode, then restore the authorized starting state for the take.

Assert the application-generated result using its identity, including persistence
when claimed. Preserve the input method, camera/HUD adjustments, capture settings,
original take records and useful failed outputs. Startup failures remain failures
even when a diagnostic record exists. If no reel was produced, deliver the failure
and required next action rather than filling a fictitious reel record.

## 3. Prepare the delivered encode and evidence

For edits, retain sources and rebuildable trim/crop/title/speed/audio decisions
using [post-production](references/post-production.md). Keep picture independent
of soundtrack revisions when that is the requested boundary, and verify it with
decoded-frame comparisons. Review the final output after changes.

Give each reel its own delivery folder with `evidence.json` from the
[template](templates/evidence.json). Fill it from actual facts using the
[field guide](references/evidence.md); reference original takes and raw checker
reports, including failures and warnings. Measure duration and size. Preserve an
initial evidence copy before adding later findings; retain edit maps and history.

Run [the media checker](scripts/check_video.py) with the brief's dimensions, frame
rate, duration and size limits. Use `--audio-policy require` when sound is required;
`forbid` remains the silent default and `allow` permits silence. Keep the reported
full-range H.264 compatibility warning, or use the explicit rejection policy when
the delivery target requires it. The [media policies](references/post-production.md#render-and-review-the-changed-work)
define picture/audio timing, minimum duration, color metadata and listening limits.
A real media failure stays a blocker; a decodable output can still be inspected
for a diagnostic package.

## 4. Inspect the actual encode and record findings

Replace `<skill>` and `<delivery>` with the selected skill and delivery paths:

```sh
python3 <skill>/scripts/check_evidence.py <delivery>/evidence.json
python3 <skill>/scripts/beat_frames.py <delivery>/evidence.json <delivery>/frames-review
```

Use a new extraction directory. [Beat and interval sheets](references/beat-frames.md)
include native frames, requested/decoded timestamps and coverage. If beat video
times are unknown, start with interval samples and inspect denser samples or
neighboring native frames to locate the moments. Record directly observed
**final-output video times** with their sampling basis and precision. Driver/video
alignment stays unknown unless separately established; no offset is required for
visual review. Preserve the original driver events and source/output edit maps.

Record a finding for each decisive beat with the inspecting author, supporting
samples/sheets and unresolved coverage. A midpoint alone may miss an action;
inspect the necessary neighbors or leave the finding unresolved. Unknown timing
is not evidence that an action is absent. Follow the [finding and watch-list contract](references/evidence.md#decisive-frame-findings-and-the-watch-list).
Credit the review author and any relay separately; relayed agent review stays agent
review. Keep sample-selection decisions separate from evidence of viewing.

Inspect beat **and interval** sheets and native frames for unintended names/contact
details, credentials, notifications and internal URLs using the brief and known
provenance. Record [sampled privacy findings](references/evidence.md#sampled-privacy-review)
and actual coverage, including after edits. An intended invented name is not
itself a defect. Unperformed review stays unreviewed; even inspected samples with
no findings can miss intervening content and provide no privacy clearance.

Watch the complete delivered encode at normal speed and listen when it contains
meaningful sound, using the coverage arranged earlier. Judge clarity, continuity
and pacing against the brief; retain unavailable coverage instead of substituting
frame inspection. For requested or warranted independent review, give a fresh
viewer the reel, audience context and viewing constraints first. Preserve their
account of what happened and what needed another look before sharing the intended
takeaway and criteria. For trailers, also ask about appeal, build and finish. Revise implicated beats within scope; another first impression needs a
fresh viewer.

## 5. Produce the review or diagnostic handoff

Add a short beat-linked watch list using final-output ranges and existing precision;
unknown times stay null. Revalidate after adding findings, then generate a new handoff:

```sh
python3 <skill>/scripts/check_evidence.py <delivery>/evidence.json
python3 <skill>/scripts/review_delivery.py <delivery>/evidence.json <delivery>/handoff
```

Use the handoff's blockers and coverage honestly. Missing, unreviewed, unresolved
or not-visible decisive moments, unsuccessful/unperformed media checks, and known
privacy concerns require a diagnostic handoff. Unperformed privacy review remains
prominent but does not prevent a useful review package. Structural validity and
`ready_for_review` are not successful-delivery claims, viewing evidence or publication
approval. The [handoff contract](references/evidence.md#decisive-frame-findings-and-the-watch-list)
defines statuses and exit codes.

Include measured duration/size, the watch list and the generated four optional
viewer-feedback questions in the response. The user need not watch or answer
before an independent agent reviews the package; unanswered feedback never becomes
performed human review. Attach a small ZIP with the reel, brief, evidence, raw
checks, indexes, sheets and native frames. Keep assessment separate. Preserve real
flagged media locally and share it only when authorized; otherwise deliver a
metadata diagnostic with omitted files explained. See the [privacy sharing rule](references/evidence.md#sampled-privacy-review).

Include setup/created-record or scene details and cleanup evidence. Stop only the
sessions and services started for this task.

## Recording friction and maintenance

During ordinary recording, log reusable friction and its next action under
`toolkit`, then use existing supported capabilities where possible. App-specific
drivers, selectors and authorized task-local adaptations remain recording work;
keep installed/copied shared skills unchanged. Friction does not authorize toolkit
edits, maintenance agents or a broader assignment.

Separate, explicitly authorized maintenance follows the [source-maintenance guide](references/toolkit-maintenance.md)
in a verified source checkout, carrying forward standing authority and review
checkpoints. Keep proposed, tested, reviewed/published and installed states distinct.
Optional maintenance need not delay a usable reel; actual capture, media,
decisive-frame and privacy blockers remain blockers.
