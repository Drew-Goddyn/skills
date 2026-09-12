# Skill mechanics

The skill-specific branch of [`writing-for-agents`](SKILL.md): what changes when the document is a skill (frontmatter, the invocation choice, and router skills). Everything else about writing it is the universal reference in `SKILL.md`.

## ChatGPT target compatibility

Treat the invocation and router mechanics below as the **upstream runtime model**, not guarantees about ChatGPT. Preserve the design choice between agent discovery and explicit human invocation, but implement it with the target runtime's verified controls.

For ChatGPT skill creation or packaging, load the installed **skill-creator** through its catalog URI and follow its current schema and validator. In this environment, keep required lowercase `name` and nonempty `description` frontmatter plus `agents/openai.yaml` UI metadata. The supplied validator does not accept `disable-model-invocation`; do not copy that upstream key into ChatGPT frontmatter. Retain the trigger branches for model-discoverable skills such as this one.

When explicit-only use is requested, express that trigger boundary in the description/instructions unless a supported target control is verified. This wording is behavioral guidance, not proof that metadata is hidden, context cost is zero, or other skills are technically unable to load the resource. Use `api_tool.read_resource` with the installed catalog URI for skill loading; do not assume a coding-agent `Skill` tool exists. A router may refer to discoverable installed skills according to their actual triggers; the upstream prohibition is specific to the upstream invocation model.

For documents intended for Codex or another coding agent, verify that target's actual controls rather than imposing ChatGPT packaging rules. Preserve the distinction in the main skill between a real context boundary and an inline load: without actual sub-agent support, only a genuine handoff to a separate session provides that separation. Do not describe another pass in the same conversation as independent review or background work.

## Invocation (upstream runtime model)

Two choices, trading the two loads:

- A **model-invoked** skill keeps a `description`, so the agent can fire it autonomously, and other skills can reach it. You can still type its name: model-invocation always _includes_ user reach; a description only ever adds agent discovery, never removes the human's. The description is the skill's top-level context pointer, forced to stay loaded at all times: permanent context load in exchange for discoverability. A model-invoked skill whose content is all reference is also one home for shared reference: another skill can invoke it, so reference needed by several skills lives in one place. Mechanics: omit `disable-model-invocation`, and write a model-facing description carrying the trigger branches (the pointer-writing rules in `SKILL.md` apply in full).
- A **user-invoked** skill strips the description from the agent's reach: only the human typing its name can invoke it, and no other skill can. Zero context load, but it spends cognitive load: you are the index that must remember it exists. Mechanics: set `disable-model-invocation: true`; the `description` becomes human-facing: a one-line summary, trigger lists stripped.

Pick model-invocation only when the agent must reach the skill on its own, or another skill must. If it only ever fires by hand, make it user-invoked and pay no context load.

Shared reference that two user-invoked skills both need can live in neither: with no descriptions, neither can fire the other. Push it to a plain file outside the skill system: external reference any skill can point at.

## Splitting by invocation

The invocation cut of splitting (the sequence cut lives in `SKILL.md`): split off a model-invoked skill when you have a distinct leading word that should trigger it on its own (a trigger word you actually use in your prompts), or another skill must reach it. You pay context load for the new always-loaded description, so that independent reach has to be worth it.

## Router skills

When user-invoked skills multiply past what you can remember, that piled-up cognitive load is cured by a **router skill**: one user-invoked skill that names the others and when to reach for each, so the human has one skill to remember instead of many. It can only hint, never fire them: user-invoked skills have no description, so nothing but the human can reach them.
