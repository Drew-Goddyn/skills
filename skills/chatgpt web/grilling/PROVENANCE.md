# Provenance and adaptation: grilling

Original author: **Matt Pocock**. Original copyright: **Copyright (c) 2026 Matt Pocock**. This is an unofficial ChatGPT adaptation prepared at the user's request, not an upstream release or endorsement.

- Repository: https://github.com/mattpocock/skills
- Revision: `3cca18b368ae95cdbdebbff572ccafa662551015`
- Commit date: **2026-09-04 08:43:27 UTC**
- Source folder: `skills/productivity/grilling/`
- Pinned source: https://github.com/mattpocock/skills/tree/3cca18b368ae95cdbdebbff572ccafa662551015/skills/productivity/grilling

Both upstream files are included. The folder inventory and complete file contents were read from GitHub earlier in this conversation at the revision above. This packaging turn reused those contents, verifying their exact Git blob hashes; a direct raw download was unavailable because container DNS failed. The repository's original [MIT notice](LICENSE) is included unchanged. See [SOURCE.json](SOURCE.json) for the source inventory and original/adapted hashes, and [UPSTREAM-CHANGES.patch](UPSTREAM-CHANGES.patch) for the exact reversible changes to upstream files.

## Required compatibility changes

Add a short execution-context section: use actual ChatGPT skill/resource loading and connector schemas; keep Build Loop separate and unchanged; normally delegate repository changes to Codex rather than assuming checkout access or write permission.

Replace the assumed parallel sub-agent dispatch with capability-aware factual investigation. Without a real sub-agent, perform accessible reads synchronously. A local-only fact requires a read-only builder investigation request, explicitly pending until evidence arrives. Keep unrelated questions eligible; do not equate a frontier blocked on missing evidence with an exhaustive interview. This fallback cannot reproduce parallel exploration and does not claim it does.

## Preserved behavior

The name, trigger description, display name, and short description are unchanged. Every part of the upstream interview outside the environment-facts paragraph is unchanged: relentless interviewing, design trees, whole-frontier rounds, the exact question-format example, recommended answers, waiting for human decisions, recomputing the frontier, exhaustive completion, and explicit confirmation of shared understanding before acting.

## Optional behavioral changes

**None applied.** No question or round caps, timeboxes, one-question-at-a-time rewrite, weakened completion rule, explicit-mention-only trigger, or automatic extra phase in Build Loop.

## Packaging and verification

One skill per archive. No executable scripts, credentials, local project checkout, or copy of Build Loop is bundled. ChatGPT installation is a separate user action. See [VALIDATION.md](VALIDATION.md) for the proportionate local checks, a same-assistant manual walkthrough, and unverified runtime behavior.

## Repository import

Published under `skills/chatgpt web/grilling/` in [Drew-Goddyn/skills](https://github.com/Drew-Goddyn/skills) from the supplied `grilling.zip`. The skill instructions, interface metadata, icon, MIT license, and historical validation record are unchanged from that archive. The export includes an icon and additional icon/product/invocation fields in `agents/openai.yaml`; `SOURCE.json` and `UPSTREAM-CHANGES.patch` now account for those fields, with the icon recorded as a packaging addition. `VALIDATION.md` records the original adaptation checks before that export, rather than tests of this repository import or installed ChatGPT behavior.
