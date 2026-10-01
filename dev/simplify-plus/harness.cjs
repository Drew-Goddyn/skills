// Stub harness for the simplify-plus workflow. It runs the script with fake agents (no model calls,
// no git) through 24 scenarios and compares a one-line summary per scenario with expected.txt.
// Run from the repo root:  node dev/simplify-plus/harness.cjs
// Print the summaries instead of comparing:  node dev/simplify-plus/harness.cjs --print
// It checks the script's control flow (gates, coverage line, fix order, halts, models and effort per stage),
// not the quality of real reviews.
const fs = require('fs')
const path = require('path')
const SCRIPT = path.join(__dirname, '../../skills/claude code/simplify-plus/scripts/simplify-plus.js')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const body = fs.readFileSync(SCRIPT, 'utf8').replace(/^export const meta/m, 'const meta')
const wf = new AsyncFunction('agent', 'parallel', 'pipeline', 'log', 'phase', 'args', 'budget', body)
const parallel = (thunks) => Promise.all(thunks.map(t => t().catch(() => null)))
const F = (file) => ({ file, line: 3, angle: 'reuse', summary: `dup in ${file}`, cost: 'c', fix: 'x' })
function mk(scn) {
  const calls = [], prompts = {}, logs = []
  const agent = async (prompt, o) => {
    calls.push(`${o.label}|${o.model}|${o.effort}`); prompts[o.label] = prompt
    const L = o.label
    if (L === 'split') return scn.split
    if (L.startsWith('review:')) return { findings: [F(L)], map: [{ file: L, does: 'd', functions: [{ name: 'f', does: 'g' }] }] }
    if (L === 'cross-chunk') return scn.crossNull ? null : { findings: [F('cross')] }
    if (L.startsWith('skeptic:')) return { kept: [F(L)], dropped: [{ summary: 's', reason: 'weak' }] }
    if (L.startsWith('fix:')) {
      const id = (prompt.match(/\[(c\d+-\d+|cross-chunk-\d+)\]/) || [])[1]
      const f = scn.fix ? scn.fix(L, id) : null
      if (f === 'NULL') return null
      if (f === 'THROW') throw new Error('budget exhausted')
      return Object.assign({ status: 'committed', commit: `simplify-plus: ${L}`, checksRun: 'make test', failure: '', applied: [{ id, change: 'did it' }], skipped: [], files: ['app/x.rb'], touchedTestsOrConfig: false, treeClean: true }, f || {})
    }
    throw new Error('unknown ' + L)
  }
  return { agent, calls, prompts, logs, log: (m) => logs.push(m) }
}
const chunk = (n) => ({ name: `chunk${n}`, files: [`f${n}.rb`], lines: 1400 })
const base = (n, extra = {}) => {
  const chunks = Array.from({ length: n }, (_, i) => chunk(i + 1))
  return { dirty: [], branch: 'feat', scope: `${n} chunk scope`, mode: 'diff', range: 'origin/main...HEAD', fixable: true, whyNotFixable: '', totalLines: n * 1400, plan: [], files: chunks.flatMap(c => c.files), chunks, ignored: [], checks: 'make test', test: '', reviewOnly: false, ...extra }
}
const scenarios = {
  dirty:            { split: { ...base(1), dirty: [' M a.rb'] } },
  dirtyReviewOnly:  { split: { ...base(1), dirty: [' M a.rb'] }, args: 'tools/importer review only' },
  noTarget:         { split: { ...base(0), scope: 'no commits ahead of origin/main' } },
  single:           { split: base(1) },
  two:              { split: base(2) },
  tooBig:           { split: { ...base(0), scope: 'the whole repo', totalLines: 90000, plan: [{ target: 'app/billing', lines: 11000, covers: 'billing' }, { target: 'app/models', lines: 40000, covers: 'models' }] }, args: 'the whole repo' },
  tooBigDirty:      { split: { ...base(0), dirty: [' M a.rb'], totalLines: 90000, plan: [{ target: 'app', lines: 90000, covers: 'all' }] } },
  tooManyChunks:    { split: base(10) },
  reviewOnlyObj:    { split: base(3), args: { reviewOnly: true } },
  reviewOnlyJson:   { split: base(2), args: '{"reviewOnly":true,"target":"PR 12"}' },
  reviewOnlyBySplit:{ split: base(2, { reviewOnly: true }), args: 'PR 12, just look' },
  notFixable:       { split: base(2, { fixable: false, whyNotFixable: 'PR 12 head is not checked out' }), args: 'PR 12' },
  detached:         { split: base(2, { branch: '' }) },
  noChecks:         { split: base(2, { checks: '' }) },
  argsTest:         { split: base(2, { checks: '' }), args: { test: 'npm test' } },
  splitTest:        { split: base(2, { checks: '', test: 'pytest' }), args: 'tools/x run pytest' },
  filesMode:        { split: base(1, { mode: 'files', range: '', scope: 'all files under tools/importer' }), args: 'tools/importer' },
  leftOut:          { split: base(2, { files: ['f1.rb', 'f2.rb', 'orphan.rb'] }) },
  revertAndFlag:    { split: base(3), fix: (L) => L === 'fix:c1' ? { status: 'reverted', failure: 'rspec: 2 failures', applied: [] } : L === 'fix:c2' ? { files: ['spec/x_spec.rb', 'app/y.rb'] } : null },
  dirtyAfterFix:    { split: base(3), fix: (L) => L === 'fix:c2' ? { treeClean: false } : null },
  fixerDies:        { split: base(3), fix: (L) => L === 'fix:c1' ? 'NULL' : null },
  fixerThrows:      { split: base(3), fix: (L) => L === 'fix:c2' ? 'THROW' : null },
  blocked:          { split: base(3), fix: (L) => L === 'fix:c2' ? { status: 'blocked', applied: [], files: [] } : null },
  crossNull:        { split: base(2), crossNull: true },
}
;(async () => {
  const out_ = []
  const print = (line) => out_.push(line)
  for (const [name, scn] of Object.entries(scenarios)) {
    const m = mk(scn)
    const out = await wf(m.agent, parallel, null, m.log, () => {}, scn.args, null)
    const fixOrder = m.calls.filter(c => c.startsWith('fix:')).map(c => c.split('|')[0].slice(4))
    const s = { agents: m.calls.length }
    if (fixOrder.length) s.fixed = fixOrder.join(',')
    if (out.commits) Object.assign(s, { commits: out.commits.length, flagged: out.flagged, reverted: out.reverted.map(r => r.why), skipped: out.skipped.length, halted: out.halted })
    if (out.reviewOnly) Object.assign(s, { stoppedBecause: out.stoppedBecause, groups: out.findings.length })
    if (out.tooBig) Object.assign(s, { msg: out.tooBig, plan: out.plan.map(p => `${p.target}:${p.lines}:${p.fits}`) })
    if (out.coverage) s.coverage = out.coverage
    if (out.refused || out.nothing) Object.assign(s, { msg: out.refused || out.nothing, hint: out.howToTarget ? 'yes' : undefined })
    if (out.unreviewed && out.unreviewed.length) s.unreviewed = out.unreviewed.length
    if (out.leftOut && out.leftOut.length) s.leftOut = out.leftOut
    if (out.notes && out.notes.length) s.notes = out.notes
    if (name === 'filesMode') s.reviewReads = /in full/.test(m.prompts['review:c1:reuse']) && !/git diff/.test(m.prompts['review:c1:reuse'])
    if (name === 'two') s.diffReads = /git diff origin\/main\.\.\.HEAD/.test(m.prompts['review:c1:reuse+quality'])
    if (name === 'splitTest' || name === 'argsTest') s.fixCheck = (m.prompts['fix:c1'].match(/narrowing it to fewer files or tests:\n(.*)/) || [])[1]
    if (name === 'dirtyReviewOnly' || name === 'filesMode') s.splitTarget = (m.prompts.split.match(/Target: (.*)/) || [])[1]
    print(`${name.padEnd(18)} ${JSON.stringify(s)}`)
  }
  const m = mk(scenarios.two); await wf(m.agent, parallel, null, m.log, () => {}, undefined, null)
  print('models: ' + [...new Set(m.calls.map(c => c.replace(/:c\d+(:[a-z+]+)?/, '')))].join('  '))
  print('no-target split prompt says: ' + (m.prompts.split.match(/Target: (.*)/) || [])[1])
  const actual = out_.join('\n') + '\n'
  if (process.argv.includes('--print')) return process.stdout.write(actual)
  const expected = fs.readFileSync(path.join(__dirname, 'expected.txt'), 'utf8')
  const a = actual.split('\n'), e = expected.split('\n')
  const diffs = []
  for (let i = 0; i < Math.max(a.length, e.length); i++) if (a[i] !== e[i]) diffs.push(`expected: ${e[i]}\n  actual: ${a[i]}`)
  if (diffs.length) { console.error(diffs.join('\n')); console.error(`FAIL: ${diffs.length} lines differ from expected.txt`); process.exit(1) }
  console.log(`PASS: ${a.length - 1} lines match expected.txt`)
})().catch(e => { console.error('HARNESS ERROR', e); process.exit(1) })
