---
name: 1password
description: Use 1Password CLI for secret access and troubleshoot repeated biometric prompts. Apply when a task needs 1Password items, op:// references, or API keys known to be stored in 1Password; reuse native authorization across related commands.
---

# 1Password

Use the local `op` CLI with the existing desktop app integration. This workflow
applies to personal and work accounts across projects. Access only the items
needed for the current task; credential access does not authorize their use for
unrelated actions.

## Reuse authorization

1. Prefer the task's existing live terminal for related secret access. In Codex,
   create one if needed with `exec_command`, `cmd: "/bin/zsh -f"`, `tty: true`,
   and `login: false`. Retain its `session_id` and send subsequent commands through
   `write_stdin`. A new PTY per short command still requires new authorization.
   Ordinary work can use its usual tools; isolation or concurrent work can justify
   another terminal and its initial approval. Share the terminal only within the
   task, with commands trusted to access the selected account.
2. Select the account from the task/configuration, using `op account list` if
   needed. Set and export `OP_ACCOUNT` in the retained shell to pin the account
   for both direct CLI calls and application subprocesses. Use `--account` for
   deliberate per-command overrides. Prefer an account ID when sign-in addresses
   are shared. Personal work must not
   silently use the work account. An unpinned command can use the account most
   recently signed in from another terminal.
3. Tell the user an approval may appear at the first needed access. Let that
   command authorize, or use `op signin --account "$OP_ACCOUNT" >/dev/null` for
   an explicit preflight with desktop integration. Continue after success and
   reuse that terminal for subsequent reads, checks, and restarts. Avoid redundant
   authentication probes and global sign-outs between commands.
4. Keep temporary shells alive while related credential work continues. Preserve
   the shell when restarting its application child; close it when no longer
   needed. Manage running services according to the task's requested lifecycle.

On macOS, native authorization is per terminal and account, extends to child
processes, expires after 10 minutes of inactivity, and has a 12-hour maximum.
Locking 1Password revokes it. A new task/terminal or another account can need its
own approval; this skill does not provide a global 30-minute cache.
[Source: authorization model](https://www.1password.dev/cli/app-integration-security).

## Keep secrets with their consumer

Prefer `op run` to inject only the required references into the command's
environment, for example after choosing the real reference and executable:

```sh
SERVICE_API_KEY='op://vault/item/field' op run --account "$OP_ACCOUNT" -- ./command
```

Use `--env-file` when the existing project file is compatible. Preserve an
application's own loader when it resolves references itself; wrapping it in
`op run` does not guarantee it will stop rereading them.
[Source: command environment injection](https://www.1password.dev/cli/reference/commands/run).

Pass `op read` output directly to its consumer when environment injection does not
fit. Keep resolved values out of tool output, shell tracing, command arguments,
and shell startup files; keep `op run` masking enabled. Avoid exporting resolved
keys into the reusable parent shell. App locking does not erase keys already
passed to a running process, so limit their lifetime to the work that needs them.
Keep existing lock/expiry settings. Do not add plaintext caches, saved session
tokens, keepalive jobs, or a different authentication mode to suppress prompts.

## If prompts repeat or access fails

- Check the same live terminal and pinned account are still in use, and whether
  the app locked or authorization expired. A prompt for every reference during
  one load is a problem to investigate. Stop after a failed or dismissed approval
  and inspect the error before retrying.
- If the sandbox blocks desktop IPC, request the execution access needed for that
  specific credential operation through the runner's approval mechanism. Keep
  an elevated terminal limited to the approved sequence and unrelated work
  sandboxed. Establish the permitted terminal before authorizing; a replacement
  terminal needs its own approval. Use native CLI troubleshooting before browser
  sign-in or account reconfiguration.
- Verify reuse only when it needs diagnosis: repeat `op signin` in the retained
  terminal, report status without secrets, and confirm prompt count with the user
  if needed. Fast responses alone do not prove prompt suppression. Sign-in success
  does not prove access to a particular item or that the application works.
