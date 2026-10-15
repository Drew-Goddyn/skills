// Stub harness for the dream-loop-fast workflow. It runs the script with fake agents (no model calls,
// no git, no Codex) through each scenario and compares a one-line summary per scenario with expected.txt.
// Run from the repo root:  node dev/dream-loop-fast/harness.cjs
// Print the summaries instead of comparing:  node dev/dream-loop-fast/harness.cjs --print
// It checks control flow and prompt wiring (director timing, plan persistence, keep/discard gate, stall
// and optimize rules, budget stops, failure paths), not the quality of real builds or judgments.
const fs = require('fs')
const path = require('path')
const SCRIPT = path.join(__dirname, '../../skills/claude code/dream-loop-fast/scripts/dream-loop-fast.js')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const wf = new AsyncFunction('agent', 'parallel', 'log', 'phase', 'budget', 'args', fs.readFileSync(SCRIPT, 'utf8').replace(/^export const meta/m, 'const meta'))
const parallel = thunks => Promise.all(thunks.map(t => t().catch(() => null)))

const SETUP = { ok: true, reason: '', repo: '/r', width: 1280, height: 720, target: '', baselineShot: '', baselineFps: 0, gpu: 'Apple M3', fpsReliable: true, codex: true, blender: '/usr/bin/blender', falKey: false }
const PLAN = { plan: 'PLAN-V1', assets: [
  { id: 'floor-pavers', route: 'codex', description: 'd' },
  { id: 'backdrop', route: 'codex', description: 'd' },
  { id: 'water-wheel', route: 'blender', description: 'd' },
  { id: 'hero', route: 'fal', description: 'd' },
] }
const verdict = (t, extra = {}) => ({ composition: t * 0.3, lighting: t * 0.3, materials: t * 0.3, details: t * 0.1, regressed: false, regressions: '', gaps: [{ gap: 'g1', fix: 'f1' }], ...extra })

async function run(scn) {
  const calls = [], prompts = {}, logs = []
  let judged = 0, courses = 0, spent = 0
  const total = scn.budget ?? null
  const agent = async (prompt, o) => {
    if (total && spent >= total) throw new Error('budget exhausted')
    const L = o.label
    spent += L.startsWith('build') ? 60000 : 3000
    calls.push(`${L}|${o.model}|${o.effort}|${o.phase}`); prompts[L] = prompt
    const forced = scn.override?.(L)
    if (forced !== undefined) return forced
    if (L === 'setup') return scn.setup ?? SETUP
    if (L === 'dream') return { ok: true, reason: '', path: '/r/.dream-loop/runs/dream/target.png', prompt: 'p', generator: 'codex gpt-6-astra' }
    if (L === 'direct plan') return scn.plan ?? PLAN
    if (L.startsWith('direct r')) { courses++; return { diagnosis: 'dx', focus: `FOCUS-${courses}`, plan: `PLAN-V${courses + 1}`, assets: scn.courseAssets ?? [] } }
    if (L.startsWith('assets ')) {
      const ids = [...prompt.matchAll(/^- ([a-z0-9-]+)\.png/gm)].map(m => m[1])
      return { items: ids.map(id => ({ id: `${id}.png`, ok: true, files: [`/r/.dream-loop/runs/dream/assets/${id}.png`], notes: 'n' })) }
    }
    if (L.startsWith('asset ')) return { id: 'ignored', ok: true, files: [`/r/assets/${L.slice(6)}.glb`], notes: 'n' }
    if (L.startsWith('build ')) {
      if (scn.buildFail?.(L)) return { ok: false, summary: '', assetRequests: [] }
      return { ok: true, summary: L, assetRequests: scn.requests?.(L) ?? [] }
    }
    if (L === 'compare baseline') return { ok: true, compare: '/r/shots/r0-compare.png', metrics: '{"brightness":0}' }
    if (L.startsWith('capture ')) { const n = L.slice(8); return { ok: true, screenshot: `/r/shots/${n}-final.png`, compare: `/r/shots/${n}-final-compare.png`, fps: scn.fps ? scn.fps(n) : 60, metrics: '{"brightness":1}', errors: [], leftovers: false, leak: scn.leak?.(n) ?? false } }
    if (L.startsWith('judge ')) {
      const s = scn.judges[judged++]
      if (s === undefined) throw new Error('ran out of scripted verdicts at ' + L)
      return typeof s === 'number' ? verdict(s) : verdict(s.t, s)
    }
    if (L === 'finish') return { ok: true, branchCreated: true, leaks: [] }
    throw new Error('unknown ' + L)
  }
  const budget = { total, spent: () => spent, remaining: () => total ? Math.max(0, total - spent) : Infinity }
  try { return { res: await wf(agent, parallel, m => logs.push(m), () => {}, budget, scn.args), calls, prompts, logs } }
  catch (e) { return { error: e.message, calls, prompts, logs } }
}

const A = extra => ({ request: 'demo', ...extra })
const R = (t) => ({ t, regressed: true })
const SCENARIOS = {
  climb: { args: A({ maxRounds: 5 }), judges: [3, 4.5, 6, 7.5, 9.1] },
  slowCallsDirector: { args: A({ maxRounds: 5 }), judges: [4, 4.3, 4.6, 5.8, 6.9] },
  planPersistsAfterDiscard: { args: A({ maxRounds: 4 }), judges: [4, R(3.8), 5, 6] },
  stalls: { args: A({}), judges: [4, R(3), R(3), R(3), R(3), R(3)] },
  firstBuildFails: { args: A({ maxRounds: 3 }), judges: [4, 5], buildFail: L => L === 'build r1' },
  baselineExisting: { args: A({ maxRounds: 1, target: '/t.png' }), setup: { ...SETUP, target: '/r/t.png', baselineShot: '/r/.dream-loop/runs/dream/shots/r0.png', baselineFps: 60 }, judges: [3, 4] },
  optimize: { args: A({}), judges: [7, 9.2, 9.1], fps: n => (n === 'r3' ? 58 : 40) },
  optimizeFails: { args: A({}), judges: [9.3, 9.4], fps: () => 40 },
  directorAssets: { args: A({ maxRounds: 2, assetRequests: 2 }), judges: [4, 5], courseAssets: [{ id: 'mist-cards', route: 'codex', description: 'd' }, { id: 'backdrop', route: 'codex', description: 'dup' }, { id: 'crane', route: 'blender', description: 'd' }], requests: L => L === 'build r1' ? [{ id: 'banner', route: 'codex', description: 'd' }] : [] },
  falWithRelay: { args: A({ maxRounds: 1, falRelay: 'http://127.0.0.1:4791', falJobs: 1 }), plan: { ...PLAN, assets: [...PLAN.assets, { id: 'statue', route: 'fal', description: 'd' }] }, judges: [4] },
  noBlender: { args: A({ maxRounds: 1 }), setup: { ...SETUP, blender: '' }, judges: [4] },
  noCodexWithTarget: { args: A({ maxRounds: 1, target: '/t.png' }), setup: { ...SETUP, codex: false, target: '/r/t.png' }, judges: [4] },
  noCodexNoTarget: { args: A({}), setup: { ...SETUP, codex: false }, judges: [] },
  directorFails: { args: A({ maxRounds: 2 }), judges: [4, 5], override: L => (L === 'direct r1' ? null : undefined) },
  leak: { args: A({ maxRounds: 3 }), judges: [4, 5], leak: n => n === 'r2' },
  buildersFailing: { args: A({}), judges: [4], buildFail: L => L !== 'build r1' },
  budget: { args: A({}), judges: [3, 4, 5, 6, 7, 8], budget: 400000 },
  planFails: { args: A({}), judges: [], override: L => (L === 'direct plan' ? null : undefined) },
  noDirectorAfterLastRound: { args: A({ maxRounds: 3 }), judges: [4, 4.3, 4.6] },
  directorAfterDiscard: { args: A({ maxRounds: 4 }), judges: [4, 4.4, R(3.9), 5] },
  baselineDoneSlow: { args: A({ maxRounds: 2, target: '/t.png' }), setup: { ...SETUP, target: '/r/t.png', baselineShot: '/r/.dream-loop/runs/dream/shots/r0.png', baselineFps: 40 }, judges: [9.4, 9.5], fps: n => (n === 'r1' ? 58 : 40) },
  setupRefuses: { args: A({}), setup: { ok: false, reason: 'working tree is dirty; commit or stash first' }, judges: [] },
  noRequest: { args: {}, judges: [] },
}

function summarize(name, r) {
  if (r.error) return { agents: r.calls.length, threw: r.error }
  const x = r.res, p = r.prompts
  const out = {
    agents: r.calls.length, status: x.status, score: x.score, peak: x.peak.score, rounds: x.rounds, opus: x.opusCalls,
    history: x.history.map(h => `${h.round}:${h.mode}:${h.picked ? 'kept' : h.score != null ? 'drop' : 'skip'}:${h.score ?? '-'}${h.director ? '+D' : ''}`).join(' '),
    library: x.library.length, falUsed: x.falJobsUsed,
  }
  if (name === 'climb') {
    const b1 = p['build r1'], b2 = p['build r2'], b3 = p['build r3']
    out.checks = {
      firstCameraFirst: b1.includes('start with the camera'),
      firstCreatesScene: b1.includes('create SCENE.md') && b1.includes('PLAN-V1'),
      firstHighEffort: r.calls.includes('build r1|claude-sonnet-5-5|high|Build'),
      afterReviewReplacesPlan: b2.includes('replace the Plan section') && b2.includes('PLAN-V2') && b2.includes('FOCUS-1'),
      laterReadsSceneAndKeepsPlan: b3.includes('read SCENE.md') && b3.includes('Leave the Plan section') && !b3.includes('PLAN-V2'),
      laterMedium: r.calls.includes('build r3|claude-sonnet-5-5|medium|Build'),
      directorOpusHigh: r.calls.includes('direct plan|claude-opus-5-5|high|Direct') && r.calls.includes('direct r1|claude-opus-5-5|high|Direct'),
      directorReadOnly: p['direct r1'].includes('Change nothing except writing your revised plan'),
      captureHaikuRemovesWorktree: r.calls.includes('capture r1|claude-haiku-5-5|low|Capture') && p['capture r1'].includes('worktree remove --force'),
      judgeSonnetHigh: r.calls.includes('judge r1|claude-sonnet-5-5|high|Judge'),
      codexBatchHaiku: r.calls.some(c => c.startsWith('assets assets-1|claude-haiku-5-5')),
      libraryInBuilder: b1.includes('floor-pavers (codex)'),
      gitRule: b2.includes('never run git without -C') || b2.includes('Never run git without -C'),
    }
  }
  if (name === 'planPersistsAfterDiscard') out.planStillPending = {
    r3HasRevisedPlan: p['build r3'].includes('PLAN-V2') && p['build r3'].includes('FOCUS-1'),
    r4Clean: !p['build r4'].includes('PLAN-V2') && p['build r4'].includes('Leave the Plan section'),
  }
  if (name === 'firstBuildFails') out.r2IsFirst = p['build r2'].includes('create SCENE.md') && r.calls.includes('build r2|claude-sonnet-5-5|high|Build')
  if (name === 'baselineExisting') out.baseline = p['build r1'].includes('improves an existing product') && r.calls.some(c => c.startsWith('judge baseline'))
  if (name === 'directorAfterDiscard') {
    const d = p['direct r3'] || ''
    out.director = { gotBestVerdict: d.includes("The judge's verdict on that best product") && !d.includes('"regressed":true'), gotAttempt: d.includes("This round's attempt was discarded") && d.includes('What that builder tried: build r3') }
    out.r4CarriesSummary = (p['build r4'] || '').includes('What that builder tried: build r3')
  }
  if (name === 'baselineDoneSlow') out.optimizeOnly = (p['build r1'] || '').includes('follow the optimize instruction above') && !(p['build r1'] || '').includes('start with the camera')
  if (name === 'directorAssets') out.libraryIds = x.library.join(',')
  if (name === 'falWithRelay') { out.libraryIds = x.library.join(','); out.relayInFalPrompt = Object.entries(p).some(([L, t]) => L.startsWith('asset ') && t.includes('http://127.0.0.1:4791')) }
  return out
}

;(async () => {
  const lines = []
  for (const [name, scn] of Object.entries(SCENARIOS)) lines.push(`${name.padEnd(26)} ${JSON.stringify(summarize(name, await run(scn)))}`)
  if (process.argv.includes('--print')) return console.log(lines.join('\n'))
  const expectedFile = path.join(__dirname, 'expected.txt')
  const expected = fs.readFileSync(expectedFile, 'utf8').trim().split('\n')
  let failed = 0
  lines.forEach((line, i) => { if (line !== expected[i]) { failed++; console.log(`MISMATCH\n  got:      ${line}\n  expected: ${expected[i]}`) } })
  if (expected.length !== lines.length) { failed++; console.log(`expected ${expected.length} scenarios, ran ${lines.length}`) }
  console.log(failed ? `${failed} scenario(s) differ` : `all ${lines.length} scenarios match`)
  process.exitCode = failed ? 1 : 0
})()
