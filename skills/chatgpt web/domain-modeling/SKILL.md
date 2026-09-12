---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a CONTEXT.md, or recording or editing an ADR.
---

# Domain Modeling

## ChatGPT compatibility

Use this specialist guidance alongside the installed **Build Loop**, not as a replacement. For Build Loop work, load its catalog entry if not already loaded (currently `skills://build-loop/skill.md`). Let Build Loop govern coordination, authorization, handoffs, and stopping; use this skill for its subject matter. The human decides; Codex owns the local implementation.

Read bundled Markdown with `api_tool.read_resource`, resolving relative links against this skill's installed resource root as reported by the catalog; follow returned continuations. Discover connector actions with `api_tool.list_resources` and use their actual schemas. Identify the repository and revision for repository reads. ChatGPT's sandbox and a remote branch are not Codex's local checkout or unpushed changes: use accessible artifacts and ask the builder for missing local evidence, clearly distinguishing inspected, reported, and unknown state.

Normally return intended repository changes for the builder to apply. A draft here is not a repository edit. Perform a direct repository write only when explicitly requested, after reading the current artifact and checking for a competing writer. Repository paths mentioned below are project inputs or output targets, not bundled resources. Keep the substantive guidance below intact when applying these environment rules.

Adapted from Matt Pocock. See [PROVENANCE.md](PROVENANCE.md) for revision and changes, and [LICENSE](LICENSE) for the original MIT notice.

Actively build and sharpen the project's domain model as you design. This is the *active* discipline: challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely *reading* `CONTEXT.md` for vocabulary is not this skill: that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

## File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Prepare new files lazily: only when you have something to write. If repository evidence establishes that no `CONTEXT.md` exists, draft one when the first term is resolved and give the builder the intended path and contents. If no `docs/adr/` exists, have the builder create it only when the first ADR is needed. Unknown repository state is not evidence that a file is absent.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account': do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the accessible code at the identified revision agrees; request builder evidence for local-only changes. State what you could not inspect. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible. Which is right?"

### Capture CONTEXT.md updates inline

When a term is resolved, draft the exact intended `CONTEXT.md` update right there, with its target path. Don't batch these up: capture them as they happen. Label it pending repository application and include it in the next useful builder handoff; do not claim the file was updated without a write result or attributed builder evidence. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

`CONTEXT.md` should be totally devoid of implementation details. Do not treat `CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse**: the cost of changing your mind later is meaningful
2. **Surprising without context**: a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).
