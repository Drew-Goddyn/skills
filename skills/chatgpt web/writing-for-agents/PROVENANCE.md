# Provenance and adaptation: writing-for-agents

Original author: **Matt Pocock**. Original copyright: **Copyright (c) 2026 Matt Pocock**. These are unofficial ChatGPT adaptations prepared at the user's request, not an upstream release or an endorsement by Matt Pocock.

- Repository: https://github.com/mattpocock/skills
- Revision: `3cca18b368ae95cdbdebbff572ccafa662551015`
- Commit date: **2026-09-04 08:43:27 UTC**
- Source folder: `skills/productivity/writing-for-agents/`
- Retrieved: **2026-09-11, America/Vancouver**
- Pinned source: https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/writing-for-agents

Retain the original [MIT license](LICENSE). Preserve source attribution, including the Michael Feathers and Ousterhout references where present. Source file bytes were checked against GitHub's Git blob hashes before adaptation. See [SOURCE.json](SOURCE.json) for the inventory, original hashes, and adapted hashes. See [UPSTREAM-CHANGES.patch](UPSTREAM-CHANGES.patch) for the exact changes to upstream files. The license, icon, and these provenance files are packaging additions, so they do not appear as changes to files inside the upstream skill folder.

## Required compatibility changes

- Add the ChatGPT execution boundary and attribution; the original main writing guidance remains byte-for-byte intact after that inserted section. Original name, trigger description, display name, and short description are unchanged.
- Add a target-compatibility section to SKILL-MECHANICS.md and label its original invocation model. Preserve every original paragraph and example, but prevent unsupported disable-model-invocation, zero-context-cost, and router restrictions from being presented as ChatGPT guarantees.
- Use the installed skill-creator for actual ChatGPT authoring/packaging and api_tool resource loading, not an assumed coding-agent Skill tool.
- Preserve the real-context-boundary requirement: a same-session pass or inline resource load is not an independent agent or a context reset.

## Optional behavioral changes

**None applied.** No shortened interviews, reduced design counts, softened engineering principles, generic-advice rewrite, or new mandatory review stages. The unavailable-subagent fallback (where applicable) loses independent exploration; it does not claim equivalent independence.

## Packaging and relationship

One skill per archive. Original skill identifier and display name retained. All files in the selected upstream folder are included. No executable scripts, local checkout, secrets, or external-agent orchestration are bundled. Build Loop remains a separately installed skill and is unchanged; the compatibility section delegates workflow to it rather than copying it.

Project files such as `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`, `AGENTS.md`, and `CLAUDE.md` are runtime inputs/output targets. Fenced template links describe example target repositories, not missing package files. Resolve those against inspected project evidence at use time.

## Validation boundary

Local packaging, resource-link checks, source-preservation checks, and a same-assistant representative walkthrough were performed. Actual ChatGPT import/security scan, installed invocation, private or unpushed project state, sub-agent execution, and independent behavioral evaluation were not verified. Creation of this archive is not installation.

## Repository import

Published under `skills/chatgpt web/writing-for-agents/` in [Drew-Goddyn/skills](https://github.com/Drew-Goddyn/skills) from the supplied `writing-for-agents.zip`. Skill instructions and references are unchanged from that archive. The export includes an icon and additional icon/product/invocation fields in `agents/openai.yaml`; the original display name and short description are retained. Updated `SOURCE.json` and `UPSTREAM-CHANGES.patch` to account for that exported UI metadata and recorded the icon as a packaging addition. The validation boundary above describes the original adaptation; this repository import does not establish ChatGPT installation or behavioral validation.
