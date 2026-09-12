# Repository guidance

This repository distributes Drew’s reusable agent skills through the skills CLI.

- Put each skill in `skills/<skill-name>/SKILL.md`, with matching `name` and a meaningful `description` in YAML frontmatter. Keep the repository root free of a `SKILL.md` so it remains a collection.
- Keep instructions concise and specific to the skill’s task. Add supporting folders only when they are useful, and link to their files using paths relative to the skill.
- Skills must work outside this checkout. Document actual prerequisites; avoid machine-specific absolute paths and dependencies on unrelated repositories.
- Add or import the skills requested by the user. Keep incomplete authoring examples in documentation rather than publishing them as discoverable skills.
- Preserve attribution and license information when importing existing work.
- For skill changes, run `npx skills add . --list` from the repository root, confirm discovery, check supporting paths, and exercise new or changed scripts. Use a representative task when behavioral validation is needed.
- Update the README’s status when the first real skill is added. Keep installation instructions accurate. No package manifest or build pipeline is required for ordinary instruction-only skills.
