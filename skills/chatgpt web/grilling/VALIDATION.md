# Validation: Grilling ChatGPT adaptation

## Scope

Local package checks plus one same-assistant manual walkthrough of the adapted instructions. This is not an installed-runtime test, independent review, or a live interview with the user. All dialogue and builder evidence below are explicitly synthetic fixtures.

## Local checks

- Run the supplied skill-creator validator and packager successfully.
- Check required frontmatter and UI metadata, one entrypoint, safe archive paths, no symlinks, archive integrity, and the upload size bound.
- Resolve every local Markdown resource link in the package; treat the separately installed Build Loop as an external skill dependency whose entrypoint was actually loaded in this conversation.
- Verify original file bytes against the pinned GitHub blob hashes. Retain UI metadata and the MIT notice unchanged.
- Reverse the exact change patch and recover the original SKILL.md byte-for-byte. Check that the original interview text outside the environment-facts replacement is unchanged, including the example and final confirmation rule.
- Verify Build Loop's files and the three previously delivered archives remain unchanged during packaging.

The recorded execution result is a pass for each check above. These checks do not establish production behavior or acceptance by ChatGPT's importer.

## Representative usage: missing local evidence

**Fixture input:** Stress-test an export decision. The goal is human-readable offline review of notes. All requirements outside three named choices are already settled for this fixture: Markdown versus JSON; inclusion of archived notes; and inclusion of attachments only if the existing unpushed exporter supports them. That last fact is only available in Codex's local checkout. No sub-agent tool is available.

**Manual first-round output:**

The attachment decision depends on local evidence I have not inspected. This is a request to paste, not work already dispatched.

**Send to the existing Codex session:**

> Read-only investigation: inspect the current export implementation in your working checkout and report whether it supports attachments. Include relevant paths, revision, and working-tree state; distinguish tested behavior from code inspection. Do not edit, commit, push, or implement export changes.

❓ **Q1** - **Export format**: Should the initial export be human-readable Markdown or structured JSON?

➡️ Markdown for this fixture's human-reading goal; JSON would favor programmatic reuse.

---

❓ **Q2** - **Archived notes**: Should the initial export include archived notes?

➡️ Exclude them so the export reflects the active collection.

**Manual check:** Both eligible decisions are asked, with recommendations, and the response stops for the user's answers. The attachment question is not asked prematurely. No fact is invented and no background job is claimed.

**Fixture answers:** Markdown; exclude archived notes. The builder has not replied.

**Manual next-state output:** The format and archived-note decisions are settled. The attachment decision remains blocked on the pending local investigation, so the interview is not complete even though no question is currently eligible.

**Synthetic builder evidence arrives:** The fixture builder reports attachment support at a named local snapshot with an unpushed change. This is attributed builder evidence, not an independently verified remote revision.

**Manual next-round output:**

❓ **Q3** - **Attachments**: Given the builder-reported support, should attachments be included in the initial export?

➡️ Keep the first export text-only for the stated reading goal; including attachments adds packaging requirements that would need further decisions.

**Fixture answer:** Keep it text-only.

**Manual closing output:** The fixture's decisions are Markdown, active notes only, and no attachments. All branches in the stated fixture are resolved. Please confirm that this matches our shared understanding before we act on the plan.

**Manual check:** New evidence unblocks the dependent decision; the user still decides. The final confirmation is requested, not assumed. No implementation or repository write occurs. Choosing attachments instead would open its dependent decisions rather than completing early.

## Not verified

ChatGPT upload/security scan; installed catalog discovery or invocation; independent model evaluation; real sub-agent execution; real builder transport or evidence; private or unpushed project state. The synchronous fallback does not reproduce parallel exploration. Packaging is not installation.
