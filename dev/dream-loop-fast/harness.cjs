// Stub harness for the dream-loop-fast workflow. It runs the script with fake agents (no model calls,
// no git, no Codex) through each scenario and compares a one-line summary per scenario with expected.txt.
// Run from the repo root:  node dev/dream-loop-fast/harness.cjs
// Print the summaries instead of comparing:  node dev/dream-loop-fast/harness.cjs --print
// It checks the script's control flow (keep/discard gate, stall and optimize rules, budget stops, failure
// paths, bake-off mapping, builder instructions), not the quality of real builds or judgments.
const fs = require('fs')
const path = require('path')
const SCRIPT = path.join(__dirname, '../../skills/claude code/dream-loop-fast/scripts/dream-loop-fast.js')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const body = fs.readFileSync(SCRIPT, 'utf8').replace(/^export const meta/m, 'const meta')
const wf = new AsyncFunction('agent', 'parallel', 'log', 'phase', 'budget', 'args', body)
const parallel = (thunks) => Promise.all(thunks.map(t => t().catch(() => null)))

const SETUP = { ok: true, reason: '', repo: '/r', width: 1280, height: 720, target: '', baselineShot: '', baselineFps: 0, gpu: 'Apple M3', fpsReliable: true, codex: true, blender: '/usr/bin/blender' }
// A verdict whose four rubric scores sum to t.
const verdict = (t, extra = {}) => ({ composition: t * 0.3, lighting: t * 0.3, materials: t * 0.3, details: t * 0.1, regressed: false, repeatedTopGap: false, regressions: '', gaps: [{ area: 'lighting', gap: 'g', fix: 'f' }], ...extra })

async function run(scn) {
  const calls = [], prompts = {}, logs = []
  let judged = 0, round = 0, spent = 0
  const total = scn.budget ?? null
  const agent = async (prompt, o) => {
    if (total && spent >= total) throw new Error('budget exhausted')
    const L = o.label
    spent += L.startsWith('build') ? 60000 : 5000
    calls.push(`${L}|${o.model}|${o.effort}`); prompts[L] = prompt
    if (L === 'setup') return scn.setup ?? SETUP
    if (L === 'dream') return { ok: true, reason: '', path: '/r/.dream-loop/runs/dream/target.png', prompt: 'p', generator: 'codex gpt-6-astra' }
    if (L.startsWith('build')) { round = +L.match(/r(\d+)/)[1]; return scn.buildFail?.(L) ? { ok: false, summary: '' } : { ok: true, summary: L } }
    if (L.startsWith('rank')) {
      // Prefers whichever candidate's screenshot path contains scn.prefer, wherever it is listed.
      const shown = [...prompt.matchAll(/^([A-H]): (.+)$/gm)].map(m => ({ letter: m[1], shot: m[2] }))
      const pref = scn.prefer ?? 'c2'
      shown.sort((a, b) => b.shot.includes(pref) - a.shot.includes(pref))
      return { order: shown.map(x => x.letter) }
    }
    if (L.startsWith('capture')) return { ok: true, screenshot: `/r/shots/${L.split(' ')[1]}-pick.png`, fps: scn.fps ? scn.fps(round) : 60, errors: [], leftovers: false, leak: scn.leak?.(round) ?? false }
    if (L.startsWith('judge')) {
      const s = scn.judges[judged++]
      if (s === undefined) throw new Error('ran out of scripted verdicts at ' + L)
      return typeof s === 'number' ? verdict(s) : verdict(s.t, s)
    }
    if (L === 'bake-off prep') return { ok: true }
    if (L.startsWith('bake-off')) {
      // Always says ours is closer and the rival is better, so a correct A/B mapping yields "all" and "none".
      const ours = prompt.match(/Attempt A: (.+)/)[1].endsWith('/p.png')
      return { closer: ours ? 'A' : 'B', better: ours ? 'B' : 'A', why: 'w' }
    }
    if (L === 'finish') return scn.finishFail ? null : { ok: true, branchCreated: true, leaks: [] }
    throw new Error('unknown ' + L)
  }
  const budget = { total, spent: () => spent, remaining: () => total ? Math.max(0, total - spent) : Infinity }
  try {
    const res = await wf(agent, parallel, m => logs.push(m), () => {}, budget, scn.args)
    return { res, calls, prompts, logs }
  } catch (e) { return { error: e.message, calls, prompts, logs } }
}

const SCENARIOS = {
  climb: { args: { request: 'demo' }, judges: [4, 6, 7.5, 8.5, 9.2] },
  tolerance: { args: { request: 'demo', maxRounds: 3 }, judges: [6, 5.7, { t: 7, regressed: true }] },
  slide: { args: { request: 'demo', maxRounds: 3 }, judges: [8, 7.6, 7.3] },
  stall: { args: { request: 'demo' }, judges: [5, 5.5, 5.75, { t: 5.5, regressed: true }], prefer: 'c3' },
  boldRecovers: { args: { request: 'demo', maxRounds: 6 }, judges: [5, 5.2, 5.4, 7.0, 7.1, 7.2] },
  optimize: { args: { request: 'demo', compareWith: '/rival.png' }, judges: [7, 9.1, 9.0], fps: r => (r < 3 ? 40 : 58) },
  optimizeFails: { args: { request: 'demo' }, judges: [9.5, 9.6, 9.7], fps: () => 40 },
  leak: { args: { request: 'demo', maxRounds: 3 }, judges: [6, 7], leak: r => r === 2 },
  baselineDone: { args: { request: 'demo', target: '/t.png' }, setup: { ...SETUP, target: '/r/t.png', baselineShot: '/r/b.png', baselineFps: 60 }, judges: [9.4] },
  baselineSlow: { args: { request: 'demo', target: '/t.png', maxRounds: 2 }, setup: { ...SETUP, target: '/r/t.png', baselineShot: '/r/b.png', baselineFps: 40 }, judges: [9.4, 9.3], fps: () => 58 },
  budget: { args: { request: 'demo' }, judges: [5, 6, 7, 8, 9], budget: 450000 },
  budgetBakeoff: { args: { request: 'demo', compareWith: '/rival.png' }, judges: [5, 6, 7, 8, 9], budget: 450000 },
  buildersFailing: { args: { request: 'demo' }, judges: [6], buildFail: L => !L.includes('r1-') },
  finishFails: { args: { request: 'demo', maxRounds: 1 }, judges: [6], finishFail: true },
  setupRefuses: { args: { request: 'demo' }, setup: { ok: false, reason: 'working tree is dirty; commit or stash first' }, judges: [] },
  noRequest: { args: {}, judges: [] },
  noCodexNoTarget: { args: { request: 'demo' }, setup: { ...SETUP, codex: false }, judges: [] },
  noCodexWithTarget: { args: { request: 'demo', target: '/t.png', maxRounds: 2 }, setup: { ...SETUP, codex: false, target: '/r/t.png', blender: '' }, judges: [6, 7] },
}

function summarize(name, r) {
  if (r.error) return { agents: r.calls.length, threw: r.error }
  const x = r.res
  const out = {
    agents: r.calls.length,
    status: x.status, score: x.score, peak: x.peak.score, rounds: x.rounds, branch: x.branch,
    history: x.history.map(h => `${h.round}:${h.mode}:${h.built}/${h.of}:${h.pick ?? '-'}:${h.score ?? '-'}:${h.accepted === undefined ? (h.note ? 'skip' : '-') : h.accepted ? 'keep' : 'drop'}`).join(' '),
  }
  if (x.bakeoff) out.bakeoff = `${x.bakeoff.closer} / ${x.bakeoff.better}`
  if (r.logs.some(l => l.startsWith('Skipping the bake-off'))) out.bakeoffSkipped = true
  if (name === 'optimize') {
    const solo = r.prompts['build r3-c1'], parallelBuild = r.prompts['build r2-c1'], first = r.prompts['build r1-c1']
    out.soloFpsReliable = solo.includes('fps reading is reliable')
    out.parallelFpsIgnored = parallelBuild.includes('ignore it')
    out.caps = [first.includes('at most 12 new'), parallelBuild.includes('at most 3 new')].join(',')
    out.bakeoffBlind = !Object.entries(r.prompts).some(([L, p]) => L.startsWith('bake-off ') && L !== 'bake-off prep' && p.includes('rival'))
    out.models = [...new Set(r.calls.map(c => c.split('|').slice(1).join('|')))].sort().join(' ')
  }
  if (name === 'climb') {
    const b = r.prompts['build r2-c1']
    out.assetRoutes = [b.includes('image-to-3D through fal.ai'), b.includes('"/usr/bin/blender" --background'), b.includes('never use fal for images')].join(',')
  }
  if (name === 'noCodexWithTarget') {
    const b = r.prompts['build r1-c1']
    out.noImages = b.includes('Image generation is unavailable') && b.includes('build them in code (image-to-3D needs image cutouts')
  }
  return out
}

;(async () => {
  const print = process.argv.includes('--print')
  const lines = []
  for (const [name, scn] of Object.entries(SCENARIOS)) lines.push(`${name.padEnd(18)} ${JSON.stringify(summarize(name, await run(scn)))}`)
  if (print) return console.log(lines.join('\n'))
  const expected = fs.readFileSync(path.join(__dirname, 'expected.txt'), 'utf8').trim().split('\n')
  let failed = 0
  lines.forEach((line, i) => { if (line !== expected[i]) { failed++; console.log(`MISMATCH\n  got:      ${line}\n  expected: ${expected[i]}`) } })
  if (expected.length !== lines.length) { failed++; console.log(`expected ${expected.length} scenarios, ran ${lines.length}`) }
  console.log(failed ? `${failed} scenario(s) differ` : `all ${lines.length} scenarios match`)
  process.exitCode = failed ? 1 : 0
})()
