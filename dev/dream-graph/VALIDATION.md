# Dream Graph validation and evidence

## October 14, 2026 revision

Based on `Drew-Goddyn/skills` main at `2dbbaff4462a779e06e55d9dede2c8fbcd7a6bbc`. The revision changes the skill's workflow and supporting prose together. [REVISION.md](REVISION.md) records the source dispositions and design choices.

This is an instruction redesign with executed structural checks and author-performed decision walkthroughs. No independent fresh-context review, new Dream, runtime playback, hands-on trial, absent-human reenactment, or comparative benchmark was performed for this candidate. Earlier supplied reviews assessed the prior revision, not this new candidate.

### Checks performed

- The installed skill-creator validator accepted the frontmatter, name, and description.
- The unchanged repository `validate.py` passed on the complete ten-file candidate skill: entrypoint count/length, local Markdown reference closure, portable paths, metadata fields, upstream license identity, and four decision rows.
- Four negative checks corrupted separate temporary copies: removed a linked reference, added an escaping local dependency, removed metadata, and removed READY's decision row. Each was rejected; the intact candidate still passed.
- Frontmatter and agent metadata were parsed as YAML. The frontmatter contains only `name` and `description`; required UI fields remain present.
- Unchanged license, agent metadata, and Imagine toolbox bytes match the pinned GitHub blob identities. The existing validator also matches its pinned blob. The historical visitor example is preserved byte-for-byte as the prefix of the extended file.
- The standard skill packager produced a single-skill `skill.zip`. All ten member paths and their bytes were checked against the candidate folder; the archive contains no sibling skill or authoring documents.
- Cross-file review and the walkthroughs below were performed by the author in the same context. They are reasoning checks, not automated semantic verification or independent review.

Direct cloning from the container failed DNS resolution. The local candidate was staged from pinned files read through the GitHub connector; it is not the user's local checkout or a complete repository clone. `npx skills add . --list` was attempted from that staging root with npm offline mode and failed with `ENOTCACHED`, because the skills package was not cached. CLI discovery is **not verified for this revision**. No user checkout was inspected or modified.

Run structural checks from a complete checkout:

```sh
python dev/dream-graph/validate.py
npx skills add . --list
```

The Python script requires Python 3.10 or newer and the standard library. It checks document structure, not instruction following, state recovery, rendered behavior, or creative quality. The CLI command requires the skills package to be available.

### Author-performed decision walkthroughs

These scenarios exercise the written decision interface by reasoning, not by running an agent or inventing an actual active Dream record.

| Scenario | Outcome supported by the revised text | Governing location |
| --- | --- | --- |
| A chosen cozy fishing scene has unresolved implementation details. | Start realization from the choice; no forced concept audition. | Main entry; brief |
| The request is exploration only. | Return alternatives/probes; no implied build. | Main step 2 |
| A failed Rule is traced to one wrong transform. | Permit a local correction without labeling foundation debt. | Main repair branch; CONTEXT |
| Direct evidence shows a representation cannot satisfy a required state. | Qualify a replacement immediately; two failed repairs are not prerequisites. | Main repair branch; assets |
| Targeted fixes repeat without new explanatory evidence. | Diagnose, choose a coherent alternative, or PAUSE; recurrence does not invent a Rule. | Main repair branch |
| The reviewer asks for a newly desired feature. | Treat it as a nonblocking opportunity unless scope changes. | Review findings |
| A newly observed failure belongs to the original encounter but lacks a brief ID. | Explain the connection; keep a material challenge open rather than exploiting the omission. | Main gap response; review findings |
| A narrow visual correction already has a baseline capture and explicit delta. | Use that target and affected checks without regenerating an image or reopening direction. | Main target and loop |
| A human-only required check is unavailable. | Continue useful independent work; otherwise PAUSE. No unsupported READY. | Authority; decisions; example |
| The human explicitly waives a missing check. | READY only if other obligations hold, with the waiver and unverified property disclosed. | Decisions; example |
| A binding quality is known to fail. | A missing-check waiver does not erase it; scope/quality changes need explicit authority. | Decisions; review closure |
| A small post-review edit affects shared camera or timing. | Invalidate potentially affected evidence and broaden follow-up when impact is uncertain. | Review closure |
| An earlier review recommended CONTINUE on a binding failure. | Account for the material objection on the handoff candidate before READY. A historical review is insufficient. | Review closure |
| The current candidate is rougher than the best checkpoint, with an older accepted baseline. | Preserve all three roles and recover the right one without implying acceptance. | Active record; checkpoint definitions |
| All required observations are met, but final acceptance is pending. | READY on that candidate; the accepted baseline does not advance automatically. | Decisions; illustrative state |
| A defect is reported after READY and no repair allowance remains. | Reopen it and PAUSE; do not automatically REJECT the idea or invent more work. | Decisions; example |
| A gym passes its capability checks. | Charge the same allowance and return to the actual encounter; capability success alone is not readiness. | Gym reference |
| An old record calls every Rule failure foundation debt. | Preserve history and reassess the cause when relevant, without hiding the unresolved requirement. | Provenance migration |
| An accepted candidate is ready to retain, but merge permission is absent. | Keep acceptance distinct from repository integration authority. | Main retention |

### What remains unverified

Actual use may still reveal late review, poor impact analysis, stale state, excessive conservatism, or a weak encounter that appears to satisfy the brief. Structural success does not settle these risks. Observe them during the next substantive Dream the human already wants, using its ordinary target comparisons, work record, review, and acceptance response. Do not create additional benchmark commissions to satisfy this document.

No claim is made that the illustrative record has been used to resume a real session, that all agents follow the new branch conditions, or that the package improves creative quality or cost relative to another workflow.

## Historical evidence, kept distinct

The [original rebuild validation at the inspected base](https://github.com/Drew-Goddyn/skills/blob/2dbbaff4462a779e06e55d9dede2c8fbcd7a6bbc/dev/dream-graph/VALIDATION.md) records the earlier reconstruction from `cbd91c80ba25af3834735ba8f6a128e9a964f28a`, publication rebased onto `7780255c2f936ca4fc5dc9501ef8fe3b0f1266e4`, structural and negative checks, packaging, author scenario reasoning, preserved concurrent README work, and an unsuccessful offline CLI-discovery attempt. It explicitly reports no fresh-agent runtime trial of that rebuild.

[PR #4](https://github.com/Drew-Goddyn/skills/pull/4), merged October 12, 2026, added Rules, foundation debt, and three-timescale motion review after that validation account. Its body reports an earlier-version unattended observation stall, a Scooper foundation-rebuild experience, and successful CLI discovery. Those author reports were read; underlying runtime evidence was not replayed or independently inspected here. They neither validate this revision nor justify claiming that no prior runtime use ever occurred.

The pinned visitor history in the skill's worked example remains evidence for the design motivation, with its original limits. The added filled brief, active record, review, graph, and READY/PAUSE transitions are expressly illustrative, not historical test results.
