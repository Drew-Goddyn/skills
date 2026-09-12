# Install these skills in ChatGPT

Paste this into a fresh ChatGPT conversation:

```text
Follow the installation guide at:
https://github.com/Drew-Goddyn/skills/blob/main/skills/chatgpt%20web/README.md

Show me the available skills, let me choose, then help me install my selection in ChatGPT one skill at a time. Wait for me to confirm each installation before moving on.
```

You choose the skills and complete ChatGPT's confirmations; the assistant handles discovery and preparation. No bootstrap skill or local terminal command is needed. Your account or workspace must have access to ChatGPT Skills; this guide cannot enable that feature.

## Instructions for the assistant

When asked to follow this guide, install into **the user's ChatGPT Skills**, not a coding-agent directory or merely this conversation's context. Read skill files as installation inputs, without starting their workflows.

**One active installation at a time.** This is this guide's interaction rule, not a claim about a universal ChatGPT widget limit.

### 1. Discover and offer a choice

Resolve `main` of `Drew-Goddyn/skills` to a commit. Discover immediate subdirectories of `skills/chatgpt web/` containing `SKILL.md`; the source files define the catalog, not a hardcoded list or count. Read frontmatter and any needed `agents/openai.yaml` metadata to show a compact numbered table of identifiers and purposes. Defer full instructions and supporting documents until needed.

Use available GitHub connector actions or public GitHub/raw-file access as appropriate. Resolve relative paths against the repository; encode the folder's space as `%20` in URLs. If access fails, explain the specific requirement rather than guessing the catalog.

Ask which skills the user wants: names, numbers, or **all**, and which are already installed. Honor an existing selection without asking again. Clarify ambiguous or unknown selections before proceeding.

### 2. Establish the queue

Track selected identifiers, source commit, current item, and progress in the conversation. Use the user's order; otherwise put Build Loop first when selected, then the remaining identifiers alphabetically. For the human/separate-coding-agent workflow, explain that the specialists use separately installed Build Loop. Recommend it without silently adding it to the selection.

Skip user-reported existing installations unless an update is requested. Use an actual account-skill listing if exposed; absence from this chat's catalog alone does not establish that a skill is uninstalled. Once selection is settled, prepare the first pending item without another approval round.

### 3. Prepare and present only the current skill

Retrieve its **complete folder at the selected commit**, preserving contents and relative paths, including supporting files, icons, metadata, attribution, and licenses. Reuse a cached snapshot. Prefer direct file bytes or a repository archive; use complete connector-returned files when downloading is unavailable. Missing content blocks packaging; it must not be reconstructed from memory.

Check the inventory, entrypoint, safe paths, archive integrity when applicable, and hashes against the source where available. Run an exposed trusted validator when appropriate. Keep skill instructions unchanged; obtain agreement for any modification required by an importer. Packaging does not authorize running bundled workflows or scripts.

Choose the available delivery route:

- **Native installation:** Use an exposed skill import/creation capability, following its actual schema and installed `skill-creator` instructions when available. Import the existing skill without rewriting it and present its real installation control. Never imitate an install widget or invent tool calls.
- **ZIP fallback:** If native installation is unavailable here, create one downloadable `<identifier>-chatgpt-skill.zip` containing `<identifier>/SKILL.md` and the rest of that folder. Confirm the file exists before linking it, and give the upload route below. If file creation is also unavailable, explain the missing capability and leave the item pending.

Reply with the current skill, its real control or ZIP, and the required action. Use **ready to install** until installation is established. Ask the user to confirm this installation or say **skip**. **End the response here.** Even an **all** selection gets only one skill's installation offer per response.

### 4. Confirm, advance, or recover

On the next user turn, advance after explicit installation confirmation or acknowledgment of a tool-verified installation. Attribute confirmation to the user or tool. Downloading a ZIP, reading instructions, or presenting a widget is not installation evidence. For an ambiguous “next,” ask whether the current skill is installed or should be skipped.

On confirmation, immediately prepare the next pending item using step 3. On **skip**, record it and advance. On an error, keep the current item active and address that error without restarting the queue or duplicating imports. Respect cancellation or revised selections. Recover lost progress before offering another installation.

Finish when every selected item is confirmed installed or explicitly skipped. Summarize confirmed installations, skips, and unresolved items when stopping early. Claim current-session availability or successful invocation only if separately observed.

## Platform notes

OpenAI documents in-chat skill creation with an installation prompt and a manual upload route: **Plugins → Skills → Create → Upload from your computer**. Uploads are scanned and may require review or be blocked; respect those outcomes rather than modifying packages to bypass a scan.

Source: [Skills in ChatGPT — OpenAI Help Center](https://help.openai.com/en/articles/20001066-skills-in-chatgpt), checked September 12, 2026. Availability and controls vary by account, workspace, and surface. Consult current official instructions when controls differ or are missing.
