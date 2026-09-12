# Drew’s Skills

Personal agent skills, installable with the [skills CLI](https://github.com/vercel-labs/skills) and compatible with the [Agent Skills format](https://agentskills.io).

## Skills

| Category | Skill | Purpose |
| --- | --- | --- |
| ChatGPT web | [Build Loop](skills/chatgpt%20web/build-loop/SKILL.md) | An ongoing thinking and review partner for human-directed work with a separate coding agent. |

Build Loop includes its interface metadata, icon, and review examples. The category identifies its intended use; the uploaded skill's existing product metadata is preserved.

Publishing the source here does not install it in a ChatGPT account or publish it in ChatGPT's plugin directory.

## Install

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

## skills.sh

The repository is the installation source. According to the [skills.sh FAQ](https://skills.sh/docs/faq), skills appear in the directory through installation telemetry when users install them with `npx skills add`; there is no separate submission step. This setup alone does not establish a directory listing.

See the [CLI documentation](https://github.com/vercel-labs/skills#install-a-skill) for installation options and the [Agent Skills specification](https://agentskills.io/specification) for the file format.
