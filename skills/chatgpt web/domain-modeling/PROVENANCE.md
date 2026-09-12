# Provenance and adaptation: domain-modeling

Original author: **Matt Pocock**. Original copyright: **Copyright (c) 2026 Matt Pocock**. These are unofficial ChatGPT adaptations prepared at the user's request, not an upstream release or an endorsement by Matt Pocock.

- Repository: https://github.com/mattpocock/skills
- Revision: `3cca18b368ae95cdbdebbff572ccafa662551015`
- Commit date: **2026-09-04 08:43:27 UTC**
- Source folder: `skills/engineering/domain-modeling/`
- Retrieved: **2026-09-11, America/Vancouver**
- Pinned source: https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015/skills/engineering/domain-modeling

Retain the original [MIT license](LICENSE). Preserve source attribution, including the Michael Feathers and Ousterhout references where present. Source file bytes were checked against GitHub's Git blob hashes before adaptation. See [SOURCE.json](SOURCE.json) for the inventory, original hashes, and adapted hashes. See [UPSTREAM-CHANGES.patch](UPSTREAM-CHANGES.patch) for the exact changes to upstream files. The license, icon, and these provenance files are packaging additions, so they do not appear as changes to files inside the upstream skill folder.

## Required compatibility changes

- Add the ChatGPT execution boundary and attribution, leaving the original name, trigger description, display name, and short description unchanged.
- Replace immediate repository writes with immediate exact, path-specific drafts and an explicit pending builder application. Capture still occurs as each term is resolved, not at the end of the interview.
- Qualify code cross-checks, file absence, context selection, and ADR numbering by accessible revision or attributed builder evidence; leave local-only state unresolved.
- Preserve all glossary rules and examples, both context layouts, concrete scenario challenges, the three-part ADR gate, the compact ADR template, and every qualifying-decision example.

## Optional behavioral changes

**None applied.** No shortened interviews, reduced design counts, softened engineering principles, generic-advice rewrite, or new mandatory review stages. The unavailable-subagent fallback (where applicable) loses independent exploration; it does not claim equivalent independence.

## Packaging and relationship

One skill per archive. Original skill identifier and display name retained. All files in the selected upstream folder are included. No executable scripts, local checkout, secrets, or external-agent orchestration are bundled. Build Loop remains a separately installed skill and is unchanged; the compatibility section delegates workflow to it rather than copying it.

Project files such as `CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`, `AGENTS.md`, and `CLAUDE.md` are runtime inputs/output targets. Fenced template links describe example target repositories, not missing package files. Resolve those against inspected project evidence at use time.

## Validation boundary

Local packaging, resource-link checks, source-preservation checks, and a same-assistant representative walkthrough were performed. Actual ChatGPT import/security scan, installed invocation, private or unpushed project state, sub-agent execution, and independent behavioral evaluation were not verified. Creation of this archive is not installation.

## Repository import

Published under `skills/chatgpt web/domain-modeling/` in [Drew-Goddyn/skills](https://github.com/Drew-Goddyn/skills) from the supplied `domain-modeling.zip`. Skill instructions and references are unchanged from that archive. The export includes an icon and additional icon/product/invocation fields in `agents/openai.yaml`; the original display name and short description are retained. Updated `SOURCE.json` and `UPSTREAM-CHANGES.patch` to account for that exported UI metadata and recorded the icon as a packaging addition. The validation boundary above describes the original adaptation; this repository import does not establish ChatGPT installation or behavioral validation.
