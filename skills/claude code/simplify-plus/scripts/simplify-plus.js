export const meta = {
  name: 'simplify-plus',
  description: '/simplify for any scope (commits, PR, branch, path, whole repo): chunked cleanup review, a cross-chunk duplication pass, a skeptic filter, then one checked local commit per chunk',
  whenToUse: 'Cleanup (not bug-hunting) at a scope too big for /simplify. Args: free text naming the target ("the last commit", "PR 1234", "tools/importer", "the whole repo"; add "review only" to skip edits), or { target, base, test, reviewOnly }. A scope over about 12,000 lines stops after one agent and proposes narrower targets.',
  phases: [
    { title: 'Split', detail: 'resolve the target and group its files into chunks of about 1,500 lines; too big for one run, propose narrower targets' },
    { title: 'Review', detail: 'the four /simplify angles on each chunk' },
    { title: 'Cross-chunk', detail: 'duplication and repeated patterns across chunks' },
    { title: 'Skeptic', detail: 'drop findings that are wrong, weak, or would change behavior' },
    { title: 'Fix', detail: 'one chunk at a time: checks green, commit; red, undo' },
  ],
}

// Model and effort for each stage. The report is built in script code, not by an agent.
const STAGES = {
  split:   { model: 'sonnet', effort: 'low' },  // only resolves the target and sorts files; every later step waits on it
  review:  { model: 'sonnet', effort: 'high' }, // many of them; the skeptic throws out their mistakes
  cross:   { model: 'opus',   effort: 'high' }, // one agent making the hardest call in the run
  skeptic: { model: 'opus',   effort: 'high' }, // decides what actually gets edited
  fix:     { model: 'sonnet', effort: 'high' }, // runs one chunk at a time; checks plus undo catch mistakes
}

// Agents for N > 1 chunks: 1 split + 2N review + 1 cross-chunk + up to N+1 skeptics + up to N+1 fixers = 4N + 4.
// 8 chunks is 36 agents, under 40. One chunk skips the cross-chunk pass: at most 1 + 4 + 1 + 1 = 7.
// A bigger scope is never cut short: the run stops after the split and proposes narrower targets.
const MAX_CHUNKS = 8
const CHUNK_LINES = 1500
const MAX_LINES = MAX_CHUNKS * CHUNK_LINES

// args: free text from the slash command, a JSON string, or { target, base, test, reviewOnly }.
let opts = args
if (typeof opts === 'string') { try { const parsed = JSON.parse(opts); if (parsed && typeof parsed === 'object') opts = parsed } catch {} }
if (!opts || typeof opts !== 'object') opts = { target: opts == null ? '' : String(opts) }
const TARGET = String(opts.target || '').trim()
const BASE = opts.base || 'main'
const ASKED_REVIEW_ONLY = Boolean(opts.reviewOnly) || /review[- ]only|\bno (edits|fixes)\b|\bdon'?t (edit|fix)\b/i.test(TARGET)
const READ_ONLY = 'Read only: do not edit files or change git state.'
const HOW_TO_TARGET = 'Pass a target, for example "the last commit", "abc123", "HEAD~3..HEAD", "PR 1234", "my-branch", "tools/importer", or "the whole repo". Add "review only" to skip edits.'

const S = { type: 'string' }
const BOOL = { type: 'boolean' }
const arr = (items) => ({ type: 'array', items })
const obj = (properties, required = Object.keys(properties)) => ({ type: 'object', properties, required })
const FINDING = obj({ file: S, line: { type: 'integer' }, angle: S, summary: S, cost: S, fix: S }, ['file', 'angle', 'summary', 'cost', 'fix'])
const SPLIT_SCHEMA = obj({
  dirty: arr(S), branch: S, scope: S, mode: { type: 'string', enum: ['diff', 'files'] }, range: S,
  fixable: BOOL, whyNotFixable: S, totalLines: { type: 'integer' }, files: arr(S),
  chunks: arr(obj({ name: S, files: arr(S), lines: { type: 'integer' } })),
  plan: arr(obj({ target: S, lines: { type: 'integer' }, covers: S })),
  ignored: arr(obj({ file: S, reason: S })),
  checks: S, test: S, reviewOnly: BOOL,
})
const REVIEW_SCHEMA = obj({
  findings: arr(FINDING),
  map: arr(obj({ file: S, does: S, functions: arr(obj({ name: S, does: S })) })),
}, ['findings'])
const VERDICT_SCHEMA = obj({ kept: arr(FINDING), dropped: arr(obj({ summary: S, reason: S })) })
const FIX_SCHEMA = obj({
  status: { type: 'string', enum: ['committed', 'reverted', 'nothing-applied', 'blocked'] },
  commit: S, checksRun: S, failure: S,
  applied: arr(obj({ id: S, change: S })),
  skipped: arr(obj({ id: S, reason: S })),
  files: arr(S), touchedTestsOrConfig: BOOL, treeClean: BOOL,
})

// The four /simplify angles. Cleanup only: none of them hunts for bugs.
const ANGLES = {
  reuse: 'Reuse: code that re-implements something the codebase already has. Grep shared and utility modules and nearby files, and name the existing helper to call instead.',
  quality: 'Quality: needless complexity: redundant or derivable state, copy-paste with slight variation, deep nesting, dead code. Name the simpler form that does the same job.',
  efficiency: 'Efficiency: wasted work: repeated computation or I/O, independent operations run one after another, blocking work on startup or hot paths, long-lived closures that keep a large enclosing scope alive. Name the cheaper alternative.',
  altitude: 'Altitude: code that patches a symptom instead of fixing the cause at the right depth. Special cases layered onto shared code are the usual sign. Name the simpler, more general change to the underlying mechanism.',
}

// Paths the report flags when a commit touches them: tests, and lint, type, or CI configuration.
const FLAG_PATHS = [
  /(^|\/)(tests?|specs?|__tests__|e2e)\//, /[._-](test|spec)s?\.\w+$/, /(^|\/)(test_[^/]+|conftest\.py)$/,
  /(^|\/)(\.github|\.buildkite|\.circleci|\.husky)\//, /(^|\/)(\.gitlab-ci\.yml|Jenkinsfile|\.pre-commit-config\.yaml|lefthook\.yml)$/,
  /(^|\/)(\.?eslint[^/]*|\.prettierrc[^/]*|\.rubocop[^/]*|\.stylelintrc[^/]*|biome\.jsonc?|\.golangci[^/]*|ruff\.toml|\.flake8|setup\.cfg|tox\.ini|pyproject\.toml|mypy\.ini|pytest\.ini|tsconfig[^/]*\.json|jsconfig\.json|(jest|vitest|playwright)\.config\.\w+|\.rspec|package\.json)$/,
]
const isFlagged = (path) => FLAG_PATHS.some((re) => re.test(path))

// ---- 1. Split: resolve the target, then group its files into chunks ----
const split = await agent(`Turn the user's target into a concrete review scope, then split it into chunks. ${READ_ONLY} The one exception: you may fetch a PR's commits. You do not need to read the code itself; paths and line counts are enough.

Target: ${TARGET ? `"${TARGET}"` : '(none given)'}

1. Return the lines of \`git status --porcelain\` as \`dirty\`, and the output of \`git branch --show-current\` as \`branch\` (empty on a detached HEAD).
2. Resolve the scope. The base branch is \`origin/${BASE}\` if that ref exists, otherwise \`${BASE}\`, unless the target names another.
   - No target: this branch's commits since the base, range \`<base>...HEAD\`. If there are none, return no chunks and set \`scope\` to "no commits ahead of <base>".
   - Commits ("the last commit", a SHA, "last 3 commits", a range): that range, such as \`<sha>^..<sha>\` or \`HEAD~3..HEAD\`.
   - A PR number or URL: read \`gh pr view <n> --json baseRefName,headRefOid\`. If that commit is missing locally, run \`git fetch origin pull/<n>/head\`. The range is \`origin/<baseRefName>...<headRefOid>\`.
   - A branch: range \`<base>...<branch>\`.
   - A path, directory, tool, or module name (find the matching directory), or the whole repo: files mode, covering \`git ls-files\` under those paths, or everywhere for the whole repo.
   - A mix, such as commits limited to a path: that range, keeping only the files under the path.
   Return \`mode\` ("diff" or "files"), \`range\` (empty in files mode), and \`scope\`: one line on what you resolved, like "3 commits, HEAD~3..HEAD" or "all files under tools/importer".
3. \`fixable\` is true in files mode, and in diff mode when the range ends at HEAD or at a commit HEAD contains (check with \`git merge-base --is-ancestor <end> HEAD\`). Otherwise set it false and say why in \`whyNotFixable\`.
4. Count lines per file: in diff mode use \`git diff --numstat --no-renames <range>\` (added plus deleted); in files mode use each file's length. Leave out lockfiles, generated, vendored, and binary files, and files the range only deletes; list them in \`ignored\` with a reason, one entry per directory or pattern where there are many. Set \`totalLines\` to the total for everything else.
5. If \`totalLines\` is over ${MAX_LINES}, the scope is too big for one run. Return no \`files\` and no chunks. Instead fill \`plan\` with narrower targets that together cover the scope: its main areas (top-level directories or features), each with its line count and one line on what it covers. Split any area over ${MAX_LINES} lines into its subdirectories, stopping at about 30 entries. Write each target so this workflow would accept it, such as "tools/importer/parsers", or "<range> in app/billing" in diff mode.
6. Otherwise return every path in \`files\`, and group them into at most ${MAX_CHUNKS} chunks of roughly ${CHUNK_LINES} lines. A chunk may run to about 2,000 lines to keep related files together: the same feature or directory, code with its tests. A file over ${CHUNK_LINES} lines gets a chunk to itself. A scope of about ${CHUNK_LINES} lines or fewer is one chunk. Every path in \`files\` goes in exactly one chunk. Name each chunk by what its code does.
7. ${opts.test ? 'Return an empty `checks`.' : "Set `checks` to the commands the repo's CLAUDE.md files (at the repo root and in directories of the files in scope) say to run to verify a change: tests, lint, type checks. Copy them exactly, one per line. Leave it empty if none are documented."}
7. Set \`reviewOnly\` to true if the target text asks for review only or no edits. If it names a check command to run, return that command as \`test\`; otherwise leave \`test\` empty.`,
  { ...STAGES.split, phase: 'Split', label: 'split', schema: SPLIT_SCHEMA })

if (!split) return { error: 'The split agent failed, so nothing was reviewed.' }
const chunks = split.chunks.filter((c) => c.files && c.files.length)
// Too big for one run: hand back narrower targets for the user to choose from instead of reviewing a slice.
if (split.plan.length || chunks.length > MAX_CHUNKS) {
  return {
    tooBig: `${split.scope} is about ${split.totalLines} lines. One run reviews at most about ${MAX_LINES} lines (${MAX_CHUNKS} chunks, under 40 agents). Rerun with a narrower target; areas marked fits can each be one run.`,
    plan: (split.plan.length ? split.plan : chunks.map((c) => ({ target: c.files.join(' '), lines: c.lines, covers: c.name })))
      .map((p) => ({ ...p, fits: p.lines <= MAX_LINES })),
    ignored: split.ignored,
  }
}
const reviewOnlyAsked = ASKED_REVIEW_ONLY || split.reviewOnly
if (split.dirty.length && !reviewOnlyAsked) return { refused: 'The working tree has uncommitted changes. Commit or stash them, or ask for review only, then rerun.', dirty: split.dirty }
if (!chunks.length) return { nothing: `Nothing to review: ${split.scope || 'empty scope'}.`, howToTarget: HOW_TO_TARGET, ignored: split.ignored }

const FILES_MODE = split.mode === 'files'
const CHECKS = opts.test || split.test || split.checks
// If this run cannot edit, say why before any review starts.
const cantFix = reviewOnlyAsked ? 'review only was requested'
  : !split.fixable ? `the target is not what is checked out (${split.whyNotFixable})`
  : !split.branch ? 'HEAD is detached, so commits could be lost'
  : !CHECKS ? 'no checks are documented in CLAUDE.md and no test command was given'
  : ''
if (cantFix) log(`Review only: ${cantFix}.`)

const chunked = new Set(chunks.flatMap((c) => c.files))
const leftOut = split.files.filter((f) => !chunked.has(f))
if (leftOut.length) log(`${leftOut.length} files in scope were left out of every chunk and will not be reviewed.`)
const single = chunks.length === 1
const tag = (i) => `c${i + 1}`
const notes = []

const fileList = (files) => files.map((f) => `- ${f}`).join('\n')
const show = (f) => `[${f.id || f.angle}] ${f.file}${f.line ? `:${f.line}` : ''}: ${f.summary}\n  cost: ${f.cost}\n  fix: ${f.fix}`
const readScope = FILES_MODE
  ? 'Read each of these files in full. All of their code is in scope.'
  : `Read the diff for these files with \`git diff ${split.range} -- <files>\`. Read every hunk carefully, and read the surrounding code where a hunk needs context. Only the changed code is in scope.`
const readCode = FILES_MODE ? 'the file itself' : `\`git diff ${split.range} -- <file>\` and the file itself`

// ---- 2. Review: four agents for a single chunk, two with paired angles per chunk otherwise ----
const GROUPS = single ? [['reuse'], ['quality'], ['efficiency'], ['altitude']] : [['reuse', 'quality'], ['efficiency', 'altitude']]

function reviewPrompt(chunk, i, angles, withMap) {
  return `Review part of a codebase for cleanup, not bugs. Do not report correctness bugs. ${READ_ONLY}

Scope: ${split.scope}. This is chunk ${tag(i)} of ${chunks.length} ("${chunk.name}"), files:
${fileList(chunk.files)}

${readScope}${single ? '' : ' Other agents review the other chunks; report findings only in these files.'}

Look only for:
${angles.map((a) => `- ${ANGLES[a]}`).join('\n')}

For each finding give the file, line, angle (${angles.join(' or ')}), a one-line summary, the cost (what is duplicated, wasted, or harder to maintain), and the fix: a specific edit that keeps behavior identical. Leave out anything you would not defend; a short list of real findings beats a long one.${withMap ? `

Also return \`map\`: for each file in this chunk, one line on what it does, plus every function, method, or class ${FILES_MODE ? 'it defines' : 'the change adds'}, each with one line on what it does. Another agent uses this map to find duplication across chunks.` : ''}`
}

async function review(chunk, i) {
  const results = await parallel(GROUPS.map((angles, g) => () => agent(reviewPrompt(chunk, i, angles, !single && g === 0), {
    ...STAGES.review, phase: 'Review', label: `review:${tag(i)}:${angles.join('+')}`, schema: REVIEW_SCHEMA,
  })))
  results.forEach((r, g) => { if (!r) notes.push(`${tag(i)}: the ${GROUPS[g].join('+')} reviewer returned nothing.`) })
  const ok = results.filter(Boolean)
  return { findings: ok.flatMap((r) => r.findings || []), map: ok.flatMap((r) => r.map || []) }
}

// ---- 4. Skeptic: one per chunk, plus one for the cross-chunk findings ----
async function skeptic(scope, label, findings) {
  if (!findings.length) return { kept: [], dropped: [] }
  const r = await agent(`You are the skeptic for ${scope}. Reviewers proposed the cleanup findings below. Whatever you keep gets edited into the user's code, so when in doubt, throw it out. ${READ_ONLY}

Read the code each finding points at (${readCode}). Throw a finding out if:
- it is wrong: the code does not do what the finding says, or the helper it suggests does not exist or does something different;
- it is weak: a style preference, a cost too small to matter, or a fix that needs changes well outside the scope under review;
- its fix would change behavior: return values, errors raised, side effects, ordering, or anything else a caller or user could observe.
Merge duplicates into one finding.

For each finding you keep, rewrite the fix so someone who has not seen the review can apply it exactly. For each one you drop, give a one-line reason.

Findings:
${findings.map(show).join('\n\n')}`, { ...STAGES.skeptic, phase: 'Skeptic', label: `skeptic:${label}`, schema: VERDICT_SCHEMA })
  return r || { kept: [], dropped: findings.map((f) => ({ summary: f.summary, reason: 'the skeptic returned nothing, so it was not applied' })) }
}

// ---- 3. Cross-chunk pass: only duplication or repeated patterns across chunks ----
async function crossChunk(reviews) {
  const map = reviews.map((r, i) => `## ${tag(i)} "${chunks[i].name}"\n` + (r.map.length
    ? r.map.map((m) => `- ${m.file}: ${m.does}${(m.functions || []).map((fn) => `\n    - ${fn.name}: ${fn.does}`).join('')}`).join('\n')
    : '(no map returned for this chunk)')).join('\n\n')
  const r = await agent(`Scope: ${split.scope}. It was split into ${chunks.length} chunks, and each chunk was reviewed on its own. Your one job is what those reviewers could not see: duplication or repeated patterns that span chunks. For example, two chunks contain near-identical helpers; the same validation, mapping, or error handling appears in files from different chunks; one chunk has a helper that another re-implements inline. Ignore anything contained within one chunk. Do not report bugs. ${READ_ONLY}

Map of the scope (files, what each does, and their functions):
${map}

Before reporting a candidate, read the code on every side of it (${readCode}) and confirm the pieces really do the same job. For each finding give the primary file and line, angle "cross-chunk", a summary that names every location, the cost, and the fix: where the shared version should live and which call sites change, with behavior unchanged.`,
    { ...STAGES.cross, phase: 'Cross-chunk', label: 'cross-chunk', schema: REVIEW_SCHEMA })
  if (!r) notes.push('The cross-chunk pass returned nothing, so duplication across chunks was not checked.')
  return skeptic('the cross-chunk findings', 'cross-chunk', r ? r.findings : [])
}

// Chunk skeptics start as each chunk's review finishes. The cross-chunk pass waits for every chunk's map.
// With one chunk its reviewers already saw the whole scope, so the cross-chunk pass is skipped.
const reviews = chunks.map((c, i) => review(c, i))
const [chunkVerdicts, crossVerdict] = await Promise.all([
  Promise.all(reviews.map((p, i) => p.then((r) => skeptic(`chunk ${tag(i)} ("${chunks[i].name}")`, tag(i), r.findings)))),
  single ? null : Promise.all(reviews).then(crossChunk),
])

const queue = chunkVerdicts.map((v, i) => ({ tag: tag(i), name: chunks[i].name, ...v }))
if (crossVerdict) queue.push({ tag: 'cross-chunk', name: 'duplication across chunks', ...crossVerdict })
queue.forEach((q) => q.kept.forEach((f, n) => { f.id = `${q.tag}-${n + 1}` }))
const skipped = queue.flatMap((q) => q.dropped.map((d) => ({ where: q.tag, finding: d.summary, reason: `skeptic: ${d.reason}` })))

// Unreviewed code is never reported as clean. At this point notes holds only review-phase failures.
const lines = chunks.reduce((n, c) => n + (c.lines || 0), 0)
const gaps = [leftOut.length ? `${leftOut.length} files the split left out` : '', ...notes].filter(Boolean)
const coverage = gaps.length
  ? `PARTIAL: reviewed ${chunks.length} chunks (about ${lines} lines), with gaps: ${gaps.join('; ')}`
  : `COMPLETE: every review angle covered every chunk (${chunks.length} of them, about ${lines} lines), apart from the ignored files.`

if (cantFix) {
  return {
    coverage, reviewOnly: true, stoppedBecause: cantFix, scope: split.scope,
    findings: queue.map((q) => ({ chunk: q.tag, name: q.name, kept: q.kept, dropped: q.dropped })),
    leftOut, ignored: split.ignored, notes,
  }
}

// ---- 5. Fix: one chunk at a time in the user's checkout, cross-chunk findings last ----
function fixPrompt(q) {
  return `Apply cleanup findings to the user's checkout, verify them, and commit. You are on branch ${split.branch}.

First run \`git status --porcelain\`. If it prints anything, stop without changing anything and return status "blocked".

Findings for ${q.tag} ("${q.name}"):
${q.kept.map(show).join('\n\n')}

Rules:
- Keep behavior identical. If a finding cannot be applied without changing behavior, or no longer applies because the code has changed since, skip it and say why.
- Never push, switch branches, stash, amend, rebase, reset commits, or commit with --no-verify.
- Never make checks pass by editing tests or check configuration (lint, type, or CI config). A finding that targets a test file may be applied as written; nothing else in tests or config changes.

Steps:
1. Apply the findings.
2. Run each check exactly as written, without narrowing it to fewer files or tests:
${CHECKS}
3. If every check passes, stage only the files you changed (\`git add <paths>\`) and make one commit with the subject "simplify-plus: ${q.tag} ${q.name}". If you applied nothing, make no commit.
   If any check fails, do not try to make it pass. Undo only your own edits: \`git restore --staged --worktree -- <each file you changed>\`, and delete the files you created. Never restore, reset, or clean the whole repo. Put the failing command and its key error lines in \`failure\`.
4. Delete untracked files that you or the checks created during this run; if you are not sure where a file came from, leave it. Then run \`git status --porcelain\` and set \`treeClean\` to true only if it prints nothing.

Return the status, the commit subject (empty if none), the commands you ran as \`checksRun\`, each applied finding's id with a one-line description of the edit, each skipped id with its reason, every file you changed, and \`touchedTestsOrConfig\`: whether you changed any test file or any lint, type, or CI configuration.`
}

const fixes = []
let halted = ''
const skipAll = (q, reason) => q.kept.forEach((f) => skipped.push({ where: q.tag, finding: f.summary, reason }))
for (const q of queue.filter((item) => item.kept.length)) {
  if (halted) { skipAll(q, `not attempted: ${halted}`); continue }
  let r = null
  try { r = await agent(fixPrompt(q), { ...STAGES.fix, phase: 'Fix', label: `fix:${q.tag}`, schema: FIX_SCHEMA }) } catch (e) { notes.push(`The ${q.tag} fixer threw: ${(e && e.message) || e}`) }
  if (!r || r.status === 'blocked') {
    halted = r ? `the checkout had uncommitted changes before ${q.tag} started; was it edited during the run?`
      : `the ${q.tag} fixer returned nothing, so the checkout's state is unknown; check git status before trusting it`
    skipAll(q, halted)
    continue
  }
  fixes.push({ q, r })
  const applied = new Set(r.status === 'committed' ? r.applied.map((a) => a.id) : [])
  const reasons = new Map(r.skipped.map((s) => [s.id, `fixer: ${s.reason}`]))
  q.kept.filter((f) => !applied.has(f.id)).forEach((f) => skipped.push({
    where: q.tag, finding: f.summary,
    reason: reasons.get(f.id) || (r.status === 'reverted' ? `checks failed, chunk undone: ${r.failure}` : 'the fixer did not apply it'),
  }))
  if (!r.treeClean) halted = `the ${q.tag} fixer left uncommitted changes in the checkout`
}

// ---- 6. Report, built from what the earlier steps returned ----
const commits = fixes.filter(({ r }) => r.status === 'committed').map(({ q, r }) => {
  const flaggedFiles = r.files.filter(isFlagged)
  return {
    chunk: `${q.tag} ${q.name}`, subject: r.commit, changes: r.applied.map((a) => a.change),
    files: r.files, checksRun: r.checksRun,
    touchesTestsOrConfig: r.touchedTestsOrConfig || flaggedFiles.length > 0, flaggedFiles,
  }
})
const reverted = fixes.filter(({ r }) => r.status === 'reverted').map(({ q, r }) => ({ chunk: `${q.tag} ${q.name}`, why: r.failure, checksRun: r.checksRun }))
log(`${commits.length} commits, ${reverted.length} chunks undone, ${skipped.length} findings skipped.`)

return {
  coverage, scope: split.scope, branch: split.branch, checks: CHECKS,
  commits,
  flagged: commits.filter((c) => c.touchesTestsOrConfig).map((c) => c.subject),
  reverted, skipped,
  halted: halted || null,
  leftOut, ignored: split.ignored, notes,
}
