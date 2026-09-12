---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

## ChatGPT compatibility

Use this interview discipline alongside the separately installed **Build Loop**. For Build Loop work, load its catalog entry if not already loaded (currently `skills://build-loop/skill.md`). Let Build Loop govern coordination, permissions, and builder handoffs; use Grilling for the interview and its final confirmation. Do not make this interview a mandatory phase of unrelated Build Loop work. Confirmation of shared understanding is not authorization to implement or publish.

Read installed skills and bundled Markdown with `api_tool.read_resource`, using catalog-provided resource roots; follow returned continuations. Discover connector actions with `api_tool.list_resources` and use their actual schemas. ChatGPT is the thinking and review partner; Codex owns the local implementation. Normally return intended repository changes to the builder. A draft is not a repository edit. Make a direct repository write only when explicitly requested, after reading the current artifact and avoiding conflicting writers.

Adapted from Matt Pocock. See [PROVENANCE.md](PROVENANCE.md) for revision and changes, [LICENSE](LICENSE) for the original MIT notice, and [VALIDATION.md](VALIDATION.md) for checks and limitations.

## Interview

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs an environment fact, use a real available sub-agent tool for a permitted read-only investigation if supported; otherwise read accessible evidence synchronously with the available tools. Identify the repository and inspected revision. ChatGPT's sandbox and a remote branch are not Codex's local checkout or unpushed changes. For local-only evidence, prepare a read-only builder investigation request through Build Loop instead of asking the human to diagnose the code. A prepared request is pending, not dispatched or running; distinguish inspected evidence from builder reports and unknown state. Claim sub-agent work or independent review only when it actually occurred.

With a real running exploration, keep only its downstream questions waiting and ask the rest of the frontier now. Without one, complete accessible synchronous reads, then ask the whole remaining eligible frontier. A pending builder request remains an unsettled prerequisite, not background work; leave its downstream decisions blocked while asking unrelated questions. An empty eligible frontier with unresolved prerequisites does not satisfy the completion rule below. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
