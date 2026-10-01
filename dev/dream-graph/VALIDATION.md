# Dream Graph rebuild validation

## Scope and evidence

Rebuilt from `Drew-Goddyn/skills` at `cbd91c80ba25af3834735ba8f6a128e9a964f28a`. The change replaces the existing Dream Graph entrypoint and references, adds portable supporting guidance and metadata, and updates the Dream Graph catalog/install text in the root README. Publication was rebased onto `7780255c2f936ca4fc5dc9501ef8fe3b0f1266e4` to preserve the concurrently added Simplify Plus skill and its README entries. A neighboring installation label now explicitly names Build Orchestrator. Other skills are unchanged.

This is an instruction redesign with structural checks and author-performed scenario review. No fresh agent built or played a new experience with this revision. The historical Kip example is source evidence for the design, not a benchmark of the rebuilt skill.

## Checks performed

- The installed skill-creator validator accepted the name, description, and frontmatter.
- `python dev/dream-graph/validate.py` passed: entrypoint count and length, metadata fields, local Markdown reference closure, portable paths, upstream license identity, and the four decision rows.
- Negative checks removed a referenced file, added an escaping dependency, removed metadata, and removed a decision row. The validator rejected each corrupted temporary copy; the candidate still passed afterwards.
- Agent metadata was parsed as YAML; its display fields and default prompt were checked.
- The standard skill packager produced a single-skill `skill.zip` containing ten files. Its member paths and every file's bytes matched the source folder. No sibling skill is needed.
- The current README was reconstructed and matched its GitHub blob before applying the Dream Graph edits; the concurrent Simplify Plus additions were preserved.
- Unchanged files reconstructed locally for packaging were checked against their staged GitHub blob identities. The license matched the original upstream blob exactly.
- Direct GitHub access from the container failed DNS resolution. `npx skills add . --list` was then attempted in the partial candidate staging root with npm offline mode; it returned `ENOTCACHED` because the skills package was unavailable. CLI discovery is not verified. The GitHub connector was used for repository publication instead.

Re-run the portable structural check from the repository root:

```sh
python dev/dream-graph/validate.py
```

This script checks document structure, not semantic compliance or creative quality. It requires Python 3.10 or newer and the standard library. Run `npx skills add . --list` from a complete checkout with package access before claiming CLI discovery validation.

## Decision scenarios reviewed by the author

These are reasoning checks against the written instructions, not executed agent tests.

| Scenario | Expected behavior | Governing section |
| --- | --- | --- |
| Human has chosen the visitor and supplied a target. | Ground the baseline and realize it; no new concept audition. | Entry; step 3 |
| Human asks only to imagine the next creation. | Explore and return useful probes or alternatives; do not start an unauthorized build. | Entry; step 2 |
| The mechanic works but the target's materials and atmosphere are absent. | CONTINUE within budget; save progress without calling it complete. | Steps 4-5 |
| One beautiful frame hides an unreadable departure and return. | Review the sequence and repair the defining gap. | Step 4; review reference |
| The first crude implementation makes a promising idea feel bad. | Give the appeal a fair test, not reflexively reject the idea. | Steps 4-5 |
| A candidate improves appearance but breaks protected movement. | Keep the prior best; fix the regression before readiness. | Steps 4-5 |
| A generated detail conflicts with the existing character or real interaction. | Preserve identity and quality; resolve material conflicts explicitly. | Step 3 |
| No required motion observation or fresh reviewer is available. | Keep the claim unverified and block READY unless the human explicitly waives the requirement. | Steps 4-5; review reference |
| The effort allowance ends with a promising unfinished build. | PAUSE and hand over the best checkpoint without lowering the bar. | Entry; step 5 |
| The same defect survives meaningful attempts. | Diagnose or change approach within budget; pause without a credible next attempt. | Step 4; asset reference |
| The scoped experience meets its criteria and agreed checks. | READY for the designated acceptance decision; no automatic extra polish. | Step 5 |
| A capability test passes while the actual encounter remains weak. | Resume realization; capability success does not complete the Dream. | Capability reference |
| A rejected branch contains a demonstrated reusable gain. | Preserve its narrower status; integrate only within permission. | Step 6 |
| An attractive new idea appears before the current Dream is convincing. | Record it without evading the selected work; revisit within authorized scope. | Steps 4 and 6 |

## Design tradeoffs

Keep the core build/review/decision loop in SKILL.md rather than making the main file a router to another skill. Disclose specialized imagination moves, review details, asset diagnostics, and capability work through specific pointers. One skill remains the human-facing interface without requiring every reference on every path.

Use checkpoints for unfinished progress and baseline for accepted inheritance. Keep readiness separate from acceptance and release authority. Fresh review is required for realization by default; self-review cannot silently replace it. Remove most specialized creative terminology instead of building a larger vocabulary around the old ambiguity.

Avoid fixed idea counts, universal reviewer scores, and per-phase quotas. Retain a bounded effort allowance and concrete quality criteria. These are chosen safeguards, not evidence for an optimal iteration policy.

## Behavioral validation still needed

Use a fresh agent with working generation, runtime observation, and independent review on a bounded real task. A suitable trial is one selected small interaction with an existing visual target and baseline. Supply this skill, the ordinary brief, and an effort allowance without coaching it through the failure cases above.

Observe whether it starts building directly, uses actual target comparisons, continues beyond the first plausible prototype, improves the important gap, preserves the baseline, and stops honestly at readiness or the effort boundary. Review the actual artifact and record tool limitations and cost. One successful trial would support that trial, not establish superiority over Dream Loop; a comparative claim needs matched tasks and budgets.
