# Drew’s Skills

Personal agent skills for ChatGPT and supported coding agents, using the [Agent Skills format](https://agentskills.io).

## Skills

| Category | Skill | Purpose |
| --- | --- | --- |
| Codex | [Record Demos and Trailers](skills/codex/record-product-demo/SKILL.md) | Record and edit video demos, screen recordings of web apps, and game showcases, with evidence and review handoffs. Requires Python 3 and FFmpeg/ffprobe; browser capture uses agent-browser, and contact sheets need Pillow >=10.1. |
| ChatGPT web | [Build Loop](skills/chatgpt%20web/build-loop/SKILL.md) | An ongoing thinking and review partner for human-directed work with a separate coding agent. |
| ChatGPT web | [Codebase Design](skills/chatgpt%20web/codebase-design/SKILL.md) | Design deep modules, interfaces, and testable seams. |
| ChatGPT web | [Domain Modeling](skills/chatgpt%20web/domain-modeling/SKILL.md) | Refine project terminology, glossaries, and architectural decisions. |
| ChatGPT web | [Writing for Agents](skills/chatgpt%20web/writing-for-agents/SKILL.md) | Write skills and other documents consumed by agents. |
| ChatGPT web | [Grilling](skills/chatgpt%20web/grilling/SKILL.md) | Stress-test a plan, decision, or idea through rounds of questions. |

The four specialist skills complement Build Loop: they supply design, domain-modeling, writing, and interview guidance while Build Loop handles coordination with the human and separate coding agent. Install Build Loop separately when using that workflow.

Publishing the source here does not install it in a ChatGPT account or publish it in ChatGPT's plugin directory.

## Install

### ChatGPT web

Use the [ChatGPT installation guide](skills/chatgpt%20web/README.md) in a fresh chat to choose skills and install them one at a time. It is ordinary Markdown, not another skill to install.

### Codex

Install Record Demos and Trailers globally for Codex:

```sh
npx skills add Drew-Goddyn/skills --skill record-product-demo --agent codex --global
```

### Coding agents

These CLI commands target supported coding agents, not a ChatGPT account.

For supported coding agents, run from the project where you want to use the skills:

```sh
npx skills add Drew-Goddyn/skills
```

List available skills without installing:

```sh
npx skills add Drew-Goddyn/skills --list
```

Install Build Loop:

```sh
npx skills add Drew-Goddyn/skills --skill build-loop
```

To install it globally for Codex:

```sh
npx skills add Drew-Goddyn/skills --skill build-loop --agent codex --global
```

Update installed skills:

```sh
npx skills update
```

## Add a skill

Create `skills/<category>/<skill-name>/SKILL.md`, for example `skills/chatgpt web/build-loop/SKILL.md`. Use a lowercase name with digits or hyphens as needed, and match the folder name to the frontmatter `name`.

Start with this structure, replacing the example with the actual capability and instructions:

```markdown
---
name: skill-name
description: Describe what this skill does and when an agent should use it.
---

# Skill Name

Describe the desired outcome, the instructions needed to achieve it, and how to check the result.
```

Keep each skill self-contained. Add `scripts/`, `references/`, or `assets/` inside its folder only when needed, and reference supporting files from `SKILL.md` using relative paths.

To bring in an existing skill, copy its complete folder into `skills/`, preserve its attribution and license, and replace any dependencies on its original checkout with portable resources or documented prerequisites.

From this repository’s root, check discovery before committing:

```sh
npx skills add . --list
```

Confirm the expected name and description appear, check supporting paths, and try the skill on a representative task. Discovery alone does not validate the skill’s behavior.

Commit and push the finished skill. No package manifest, build, deployment, or npm publication is needed for this repository layout.

## Credits

**Codebase Design**, **Domain Modeling**, **Writing for Agents**, and **Grilling** are unofficial adaptations of [Matt Pocock’s skills](https://github.com/mattpocock/skills), based on upstream revision [`3cca18b`](https://github.com/mattpocock/skills/commit/3cca18b368ae95cdbdebbff572ccafa662551015). These versions are adapted for ChatGPT web’s environment and use alongside Build Loop, including resource access, repository-evidence boundaries, and handoffs to a separate coding agent.

Original copyright: **Copyright (c) 2026 Matt Pocock**. Each adapted skill retains the original MIT `LICENSE`, source inventory, and upstream comparison patch. The adaptation notes are available for [Codebase Design](skills/chatgpt%20web/codebase-design/PROVENANCE.md), [Domain Modeling](skills/chatgpt%20web/domain-modeling/PROVENANCE.md), [Writing for Agents](skills/chatgpt%20web/writing-for-agents/PROVENANCE.md), and [Grilling](skills/chatgpt%20web/grilling/PROVENANCE.md). These adaptations are not an upstream release or an endorsement by Matt Pocock.

## skills.sh

The repository is the installation source. According to the [skills.sh FAQ](https://skills.sh/docs/faq), skills appear in the directory through installation telemetry when users install them with `npx skills add`; there is no separate submission step. This setup alone does not establish a directory listing.

See the [CLI documentation](https://github.com/vercel-labs/skills#install-a-skill) for installation options and the [Agent Skills specification](https://agentskills.io/specification) for the file format.
