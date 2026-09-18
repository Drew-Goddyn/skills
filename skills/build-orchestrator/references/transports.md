# Transport notes

Patterns and gotchas for reaching a builder directly. Agent CLIs change quickly, so confirm options against the installed tool before relying on them. Each note names its source: **exercised** means it was run on 2026-09-17, **help** means it comes from that day's `--help` output, and **tool description** means it comes from the tool's own description inside the session.

## Establish for any route

- **Start:** how to run the builder non-interactively with a brief.
- **Output:** where the complete final report lands, and where logs go.
- **Handle:** how the builder identifies its session, and how to address that session later.
- **Permissions:** what the builder can read, write, and reach on the network, who approves its actions, their defaults, and what a resumed session runs under.
- **Workspace:** working directory, extra writable directories, worktree isolation, and whether the builder can commit.
- **Completion:** blocking, background notification, or polling, and how to stop a run.
- **Nesting:** whether your own sandbox blocks the builder's network access or state directory.

Treat any setting that changes who approves the builder's actions, what it can read, write, or reach, or which hooks, trust, or policy files apply as a permission decision. The per-tool lists below are examples, not complete lists.

Use the model and effort from the human's configuration unless they choose otherwise.

## Web and cloud orchestrators

A web agent reaches builders only through the tools its conversation exposes. Check the actual tool list; a product name establishes nothing, and one workspace can have tools another lacks.

- **Local builders:** reachable from the web only through a bridge the human has set up, such as cross-session messaging, or by relay.
- **Cloud builders:** a tool that starts a cloud coding session gives you a remote builder with its own copy of the repository, and the work comes back as a branch, PR, or patch. Starting one runs the work beyond this machine and spends account resources, so it needs the human's choice. The installed CLIs show such routes: `claude --cloud` creates a cloud session, and `codex cloud` browses Codex Cloud tasks and applies their changes locally (**help**).
- **Messaging remote sessions:** in Claude Code, ListAgents says a cloud session receives your messages but cannot message any session back yet, so read its answer in its own transcript. SendMessage says a successful send means the message arrived, but cloud, Remote Control, and Desktop sessions send no notice when they hold or refuse it, so treat silence as unknown (**tool description**).
- **Repository connectors:** give inspection access even when briefs travel by relay. Posting a comment, review, or mention through a connector is an external message and needs authorization.

## In-session subagents

An in-session subagent tool starts a builder inside your session. A fresh spawn is ephemeral. Some tools can message a named subagent again with its context intact, which makes it persistent; in Claude Code, spawn with a name and continue through SendMessage (**exercised**).

Delivery timing depends on the channel. A subagent's plain-text result arrived as an idle notification only after the orchestrator's turn ended, while a reply the subagent sent through SendMessage arrived during the turn (**exercised**). When you need the answer mid-turn, tell the subagent to reply through the messaging tool.

Worktree isolation and completion notices depend on the tool. In-session subagents typically draw on your own account and usage, so they offload context rather than cost.

## Agent CLIs

In these examples, `<dir>` is a directory outside the repository, so briefs, reports, and event logs stay out of the builder's diff.

### Codex CLI (0.153.2)

- **One-shot:** `codex exec -s workspace-write -C <repo> --json -o <dir>/report.md - < <dir>/brief.md > <dir>/events.jsonl`. The `-o` file receives the final message, and redirecting the event stream keeps it out of your context (**exercised**).
- **Handle:** the first `--json` event is `thread.started` with a `thread_id` (**exercised**).
- **Resume:** `codex exec resume <thread_id> -c 'sandbox_mode="workspace-write"' --json -o <dir>/report.md - < <dir>/delta.md > <dir>/events.jsonl`. Resuming by `thread_id` continued the same context (**exercised**). A resumed session does not keep its original sandbox: a session started with `-s read-only` wrote a file when resumed with no sandbox option, and a session resumed with `-c 'sandbox_mode="read-only"'` failed a forced write with `operation not permitted` (**exercised**). The event stream does not report the effective sandbox, so set `sandbox_mode` on every resume rather than trying to confirm it. `codex exec resume` has no `-s` option; use `-c` (**help**).
- **What the sandboxes allowed:** under `-s read-only`, a forced write failed with `operation not permitted`. Under `-s workspace-write`, the builder read a file outside its workspace and wrote a file under `/tmp` outside its workspace, while `git add` and `git commit` failed because `.git/index.lock` could not be created (**exercised**). Writes to other locations were not tested. Plan for you or the human to commit after review, and do not count on workspace-write to keep reads or writes inside the repository.
- **Defaults:** a fresh `codex exec` with no `-s` wrote a file in the probe repository (**exercised**), so the default depends on version and configuration. Set `-s` explicitly.
- **Settings that need explicit authorization,** for example: `-s danger-full-access`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-bypass-hook-trust`, `--approve-for-me` (routes approval requests to automatic review), `--add-dir` (extra writable directories), `--ignore-rules`, `--ignore-user-config`, `-p`/`--profile`, and `-c` overrides that widen sandbox or approval settings (**help**). Setting the authorized sandbox again on resume is not a widening.
- **Unbacked reports:** asked to run a write under a read-only sandbox, a builder quoted a plausible `operation not permitted` error, but its event stream held no `command_execution` item for the command (**exercised**). When execution matters, check the event stream, or require output the builder cannot guess.
- **Selectors:** `--last` resumes the newest recorded session, and session listings are filtered to the current directory unless `--all` is given (**help**). It can pick the wrong builder once several have run.
- **Stdin:** when stdin is piped and a prompt argument is also given, Codex appends stdin to the prompt (**help**). Send the brief on stdin with `-`, or redirect stdin from `/dev/null`.
- `codex queue --thread <id> --message <text>` queues a message for an existing session (**help**).

### Claude Code CLI (2.1.274 to 2.1.275)

- **One-shot:** `claude -p --output-format json --permission-mode <mode> "<brief>"`. The JSON result carries `session_id`, `result`, `is_error`, `terminal_reason`, `subtype`, and `permission_denials` (**exercised**).
- **Resume:** `claude -p --resume <session_id> --permission-mode <mode> --output-format json "<delta>"` continued the same context (**exercised**). The permission mode does not carry over: a session started with `acceptEdits` resumed under the settings default when no mode was given (**exercised**). Pass the mode on every resume. To confirm the effective mode, read `permissionMode` from the `system/init` event of `--output-format stream-json --verbose`; the `json` result has no such field (**exercised**).
- **Plan mode:** told to call the Write tool under `--permission-mode plan`, the builder declined without calling it, citing plan mode. No file appeared, and `permission_denials` stayed empty because nothing was attempted (**exercised**). Tool-level enforcement was not observed.
- **Settings that need explicit authorization,** for example: `--permission-mode bypassPermissions`, `--dangerously-skip-permissions`, `--allow-dangerously-skip-permissions`, `claude agents --dangerously-skip-permissions` and that command's `--permission-mode` default for dispatched sessions, `--permission-mode auto`, `--allowedTools`, `--settings`, `--add-dir`, `--mcp-config`, and `--plugin-dir` or `--plugin-url` (**help**). In auto mode, a classifier approves actions (**tool description**). `--permission-prompts none` denies anything that would prompt. `-p` skips the workspace trust dialog, so use it only in trusted directories (**help**).
- **Failure shape:** a failed run can still print a JSON result with a `session_id`, and `subtype` can read `success`. Check `is_error` and `terminal_reason` (**exercised:** a sandboxed run exited 1 with `is_error: true`, `terminal_reason: api_error`, and `subtype: success`).
- **Background:** `claude --bg` prints an id that `claude attach`, `logs`, `stop`, and `rm` accept. `claude agents --json` lists active sessions; add `--all` to include completed background sessions. `--bg --resume <id>` on a session that is already running starts a copy, which creates a second builder in the same place (**help**).
- **Selectors:** `--continue` picks the most recent conversation in the current directory (**help**).

### Gemini CLI (0.58.0)

- **One-shot:** `gemini -p "<brief>" -o json --approval-mode auto_edit < /dev/null`. `-p` appends its prompt to any piped stdin, and `auto_edit` auto-approves edit tools (**help**).
- **Handle:** `--session-id <uuid>` sets the ID when a session starts. Help describes `--resume` as taking `latest` or an index from `--list-sessions`, which lists sessions for the current project, and `--session-file` loads a session from a JSON file (**help**). With several Gemini builders, give each its own working directory or treat them as ephemeral.
- **Sandbox:** `-s`/`--sandbox` runs Gemini in a sandbox (**help**); confirm the effective default before relying on one.
- **Settings that need explicit authorization,** for example: `--approval-mode yolo`, `-y`/`--yolo`, `--allowed-tools`, `--skip-trust`, `--policy`, `--admin-policy`, and `--include-directories` (**help**). `--approval-mode plan` is read-only (**help**).

### Cursor Agent CLI (2026.03.30)

- **One-shot:** `cursor-agent -p --output-format json --sandbox enabled "<brief>"`. Help says print mode has access to all tools, including write and shell (**help**).
- **Handle:** `cursor-agent create-chat` creates an empty chat and returns its ID, and `--resume <chatId>` resumes it. `--continue` and the `resume` command pick the previous or latest session (**help**).
- **Read-only:** `--mode plan` and `--mode ask` (**help**).
- **Settings that need explicit authorization,** for example: `--sandbox disabled`, `-f`/`--force`, `--yolo`, `--approve-mcps`, and `--trust` (**help**). `-w` starts in an isolated worktree (**help**).

## Sessions the human keeps open

A persistent session the human runs belongs to the human; message it only with their agreement. In Claude Code, ListAgents lists Claude sessions that SendMessage can reach: other local sessions and, when connected, sessions on other machines and in the cloud. A successful send means delivery, not action: a session in a different permission mode may hold the message for its user's approval (**tool description**).

Terminal keystrokes, such as tmux `send-keys`, are a last resort. Capture the pane first, and send nothing while a permission, trust, or confirmation prompt is showing, because a keypress there answers the prompt. Output parsing is unreliable, and keys can land in the wrong pane.

## Nesting a CLI inside a sandboxed orchestrator

An agent CLI needs network access to its model provider and write access to its own state directory. Your sandbox can block both, and the builder then reports something that looks unrelated. On 2026-09-17, a nested `claude -p` run under the Claude Code shell sandbox failed with a credential-helper login message and `terminal_reason: api_error`, while the sandbox's violation log showed network access to the model gateway denied. The same command shape outside the sandbox succeeded (**exercised**). Check your sandbox's log before sending the human to re-authenticate.

In Claude Code, `$TMPDIR` names different directories inside and outside the shell sandbox. In one orchestration run, a brief written under `$TMPDIR` by a sandboxed command was missing when the builder ran outside the sandbox (**exercised**). Write briefs and reports to an absolute path that both modes can reach.

Running a builder outside your sandbox is a permission decision in its own right. It lifts all of your sandbox's limits for the builder's process, including reads, writes, and network. The builder's own sandbox restores only what it covers, and a builder with no sandbox of its own gets none of them back; see what a workspace-write Codex builder could read and write above. Ask for the narrowest approval, say what you have observed or read in help about what the builder's own sandbox restricts and leaves open, label what came only from help, name what you have not checked, and keep that sandbox narrow.

## Relay

Always available, whatever else the environment lacks.
