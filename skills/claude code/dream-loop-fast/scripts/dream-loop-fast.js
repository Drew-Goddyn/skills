export const meta = {
  name: 'dream-loop-fast',
  description: 'Dream-loop on Sonnet and Haiku with a few Opus director calls: Opus plans, one Sonnet builder per round, a Sonnet judge, Opus course corrections',
  whenToUse: 'Build a game, app, or 3D scene to high visual fidelity (dream-loop) with cheap builders steered by a few strong-model decisions. args: { request, ...options }',
  phases: [
    { title: 'Setup', detail: 'repo, capture and compare tool', model: 'claude-sonnet-5-5' },
    { title: 'Dream', detail: 'generate the target screenshot', model: 'claude-sonnet-5-5' },
    { title: 'Direct', detail: 'Opus plan, then course corrections after the first build and when progress slows', model: 'claude-opus-5-5' },
    { title: 'Assets', detail: 'shared textures, backdrops, and models, built in parallel' },
    { title: 'Build', detail: 'one Sonnet builder per round', model: 'claude-sonnet-5-5' },
    { title: 'Capture', detail: 'clean capture, numbers, secret check', model: 'claude-haiku-5-5' },
    { title: 'Judge', detail: 'rubric score and gaps', model: 'claude-sonnet-5-5' },
    { title: 'Finish', detail: 'best branch and run log' },
  ],
}

// Version 3 of dream-loop-fast, a re-implementation of dream-loop's Pro workflow
// (github.com/achimala/dream-loop): dream a target screenshot, build toward it, have a
// fresh judge score the live screenshot against the target, feed the gaps back, repeat.
//
// dream-loop's strength is one strong model holding the whole scene in one context. This
// version keeps that coherence without paying for it: one Sonnet builder per round, a
// short scene file (SCENE.md) on the branch that carries the plan and what each round
// learned, and an Opus director at the few moments where judgment decides the outcome:
// the plan before anything is built, a review of the first build, and a diagnosis when
// progress slows. Haiku does the mechanical work (image batches, captures, secret checks).
//
// Why, from earlier runs: version 1's builders were 99% of the cost and the parallel
// candidates never changed the winner. Version 2 cut cost but its area split and short
// passes fragmented the scene, and its first build scored lower than version 1's. So this
// version drops the area split, merge, candidate race, rankers, and multi-pass reviews,
// and keeps shared assets built once, the compare sheet and numbers, and the keep-the-best
// gate: a candidate replaces the current best when the judge rules it no further from the
// target overall and it scores within half a point of the best score so far.
//
// Supports static web apps (index.html served from a folder).
//
// args (a bare string is treated as { request }):
//   request        required. The build prompt.
//   repo           project root (default: the session's working directory). Must be the top
//                  level of a clean git repo, or an empty or missing folder.
//   appDir         app folder inside the repo (default '.')
//   target         image to build toward; skips the dream step. To compare with another run, pass its target.
//   codexModel     model that drives Codex's image tool ('gpt-6-astra'); if Codex refuses it, the account default runs
//   maxRounds      (12)                                 doneScore   judge score that ends the run (9 of 10)
//   fps            frame-rate floor, 0 to skip (55)     viewport    capture size [w, h] ([1280, 720])
//   maxAssets      shared assets built from the plan before round 1 (12)
//   assetRequests  asset requests from builders and the director built per round (4)
//   falRelay       URL of a local fal relay that holds the key (e.g. 'http://127.0.0.1:4791')
//   falJobs        image-to-3D jobs for the whole run, for organic hero objects only (6)
//   tag            branch and folder namespace; change it to run again in the same repo ('dream')
// A "+Nk" token budget on the request is enforced between rounds. It counts output tokens
// only, so compare true cost with another system from gateway usage, not from this budget.

const SONNET = 'claude-sonnet-5-5' // if your gateway rejects pinned IDs, use 'sonnet', 'haiku', and 'opus'
const HAIKU = 'claude-haiku-5-5'
const OPUS = 'claude-opus-5-5'

const A = typeof args === 'string' ? { request: args } : { ...args }
if (!A.request) throw new Error('args.request is required: the build prompt')
const TAG = A.tag ?? 'dream'
const APP = A.appDir ?? '.'
const MAX_ROUNDS = A.maxRounds ?? 12
const DONE = A.doneScore ?? 9 // upstream stops at 8; cheap rounds let the loop push further
const FPS = A.fps ?? 55 // headless Chromium paces frames at 60 Hz, so a floor of 60 fails on one dropped frame
const MAX_ASSETS = A.maxAssets ?? 12
const REQUESTS_PER_ROUND = A.assetRequests ?? 4
const FAL_RELAY = A.falRelay ?? ''
const FAL_JOBS = A.falJobs ?? 6
const CODEX_MODEL = A.codexModel ?? 'gpt-6-astra'
const TOLERANCE = 0.5 // absolute scores drift between judge calls; the judge's side-by-side regressed flag is the main gate
const STALL_ROUNDS = 4 // rounds without a gain before the run ends as stalled; the director gets a turn at two
const FIRST_CALLS = 100, ROUND_CALLS = 60 // tool-call guidance per builder; the first build has the most to do
const RESERVE = 200_000, FINISH_RESERVE = 60_000 // output tokens, only used with a "+Nk" budget
const [VW, VH] = A.viewport ?? [1280, 720]
const KEY_NAMES = ['FAL_KEY', 'FAL_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY']

const S = { type: 'string' }, N = { type: 'number' }, B = { type: 'boolean' }
const obj = props => ({ type: 'object', properties: props, required: Object.keys(props) })
const ROUTE = { type: 'string', enum: ['codex', 'blender', 'fal'] }
const WANT = obj({ id: S, route: ROUTE, description: S })
const SETUP = obj({ ok: B, reason: S, repo: S, width: N, height: N, target: S, baselineShot: S, baselineFps: N, gpu: S, fpsReliable: B, codex: B, blender: S, falKey: B })
const DREAM = obj({ ok: B, reason: S, path: S, prompt: S, generator: S })
const PLAN = obj({ plan: S, assets: { type: 'array', items: WANT } })
const COURSE = obj({ diagnosis: S, focus: S, plan: S, assets: { type: 'array', items: WANT } })
const MADE = obj({ id: S, ok: B, files: { type: 'array', items: S }, notes: S })
const BATCH = obj({ items: { type: 'array', items: MADE } })
const BUILD = obj({ ok: B, summary: S, assetRequests: { type: 'array', items: WANT } })
const CAPTURE = obj({ ok: B, screenshot: S, compare: S, fps: N, metrics: S, errors: { type: 'array', items: S }, leftovers: B, leak: B })
const VERDICT = obj({
  composition: N, lighting: N, materials: N, details: N, regressed: B, regressions: S,
  gaps: { type: 'array', items: obj({ gap: S, fix: S }) },
})

const clamp = (x, hi) => Math.max(0, Math.min(hi, Number(x) || 0))
const scoreOf = v => Math.round((clamp(v.composition, 3) + clamp(v.lighting, 3) + clamp(v.materials, 3) + clamp(v.details, 1)) * 100) / 100
const slug = s => String(s).toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40) || 'asset'
const stem = shot => shot.endsWith('.png') ? shot.slice(0, -4) : shot
const compareOf = shot => `${stem(shot)}-compare.png`
const metricsOf = shot => `${stem(shot)}-metrics.json`

// agent() throws once a "+Nk" budget is spent. Treat that like any failed agent so the
// loop's own checks end the run and the wrap-up still happens.
const call = (prompt, opts) => agent(prompt, opts).catch(e => { log(`${opts.label}: ${e.message}`); return null })

// Every screenshot and comparison in a run comes from this tool, written verbatim by setup.
// Tested live: measure, compare, and a full capture of a real build.
const CAPTURE_JS = `// node capture.mjs <appDir> <out.png> <width> <height> [target.png]
//   Renders appDir (served as static files) in Chromium and saves out.png. With a target, also saves
//   <out>-compare.png (target, product, 50% overlay, difference map) and <out>-metrics.json.
// node capture.mjs --compare <target.png> <image.png>   writes <image>-compare.png and <image>-metrics.json
// node capture.mjs --measure <image.png>
// Every mode prints one JSON line.
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { chromium } from 'playwright'

const argv = process.argv.slice(2)
const LAUNCH = { channel: 'chromium', args: ['--ignore-gpu-blocklist', '--enable-gpu-rasterization'] }
const MIME = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp' }
const dataUrl = file => 'data:' + (MIME[path.extname(file).toLowerCase()] || 'image/png') + ';base64,' + fs.readFileSync(file).toString('base64')
const stem = file => file.toLowerCase().endsWith('.png') ? file.slice(0, -4) : file

// Runs in the page: numbers for one image, or for two images their differences and a 2x2 compare sheet.
function analyze(input) {
  return (async () => {
    const load = src => new Promise((ok, fail) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => fail(new Error('cannot decode image')); i.src = src })
    const pixels = (img, w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); x.drawImage(img, 0, 0, w, h); return x.getImageData(0, 0, w, h).data }
    const W = 320, H = 180
    const hex = (r, g, b) => '#' + [r, g, b].map(v => Math.round(v).toString(16).padStart(2, '0')).join('')
    const stats = d => {
      const n = d.length / 4
      let r = 0, g = 0, b = 0, sat = 0
      const lum = new Float32Array(n)
      const grid = Array.from({ length: 9 }, () => [0, 0])
      for (let i = 0; i < n; i++) {
        const R = d[i * 4], G = d[i * 4 + 1], B = d[i * 4 + 2]
        r += R; g += G; b += B
        const mx = Math.max(R, G, B), mn = Math.min(R, G, B)
        sat += mx ? (mx - mn) / mx : 0
        const y = 0.2126 * R + 0.7152 * G + 0.0722 * B
        lum[i] = y
        const cell = Math.min(2, Math.floor(Math.floor(i / W) * 3 / H)) * 3 + Math.min(2, Math.floor((i % W) * 3 / W))
        grid[cell][0] += y; grid[cell][1]++
      }
      const sorted = Array.from(lum).sort((p, q) => p - q)
      return {
        meanColor: hex(r / n, g / n, b / n),
        brightness: Math.round(sorted.reduce((s, v) => s + v, 0) / n),
        darkP10: Math.round(sorted[Math.floor(n * 0.1)]),
        brightP90: Math.round(sorted[Math.floor(n * 0.9)]),
        warmth: Math.round((r - b) / n),
        saturation: Math.round(sat / n * 100),
        brightnessGrid3x3: grid.map(c => Math.round(c[0] / c[1])),
      }
    }
    const a = await load(input.a)
    const pa = pixels(a, W, H)
    const sa = stats(pa)
    if (!input.b) return { stats: sa }
    const b = await load(input.b)
    const pb = pixels(b, W, H)
    const sb = stats(pb)
    let diff = 0
    for (let i = 0; i < pa.length; i += 4) diff += (Math.abs(pa[i] - pb[i]) + Math.abs(pa[i + 1] - pb[i + 1]) + Math.abs(pa[i + 2] - pb[i + 2])) / 3
    const delta = {
      brightness: sb.brightness - sa.brightness,
      darkP10: sb.darkP10 - sa.darkP10,
      brightP90: sb.brightP90 - sa.brightP90,
      warmth: sb.warmth - sa.warmth,
      saturation: sb.saturation - sa.saturation,
      brightnessGrid3x3: sb.brightnessGrid3x3.map((v, i) => v - sa.brightnessGrid3x3[i]),
      meanPixelDifference: Math.round(diff / (pa.length / 4)),
    }
    // Compare sheet: target and product on top, 50% overlay and difference map below.
    const TW = 640, TH = 360
    const sheet = document.createElement('canvas')
    sheet.width = TW * 2; sheet.height = TH * 2
    const x = sheet.getContext('2d')
    x.drawImage(a, 0, 0, TW, TH)
    x.drawImage(b, TW, 0, TW, TH)
    x.drawImage(a, 0, TH, TW, TH)
    x.globalAlpha = 0.5
    x.drawImage(b, 0, TH, TW, TH)
    x.globalAlpha = 1
    // Difference map scaled to this pair's 95th percentile, so the worst areas stand out.
    const ia = pixels(a, TW, TH), ib = pixels(b, TW, TH), heat = x.createImageData(TW, TH)
    const dd = new Float32Array(ia.length / 4)
    for (let i = 0; i < ia.length; i += 4) dd[i / 4] = (Math.abs(ia[i] - ib[i]) + Math.abs(ia[i + 1] - ib[i + 1]) + Math.abs(ia[i + 2] - ib[i + 2])) / 3
    const p95 = Math.max(1, Array.from(dd).sort((p, q) => p - q)[Math.floor(dd.length * 0.95)])
    for (let i = 0; i < dd.length; i++) {
      const t = Math.min(1, dd[i] / p95)
      heat.data[i * 4] = 255 * Math.min(1, t * 1.5); heat.data[i * 4 + 1] = 255 * Math.max(0, t * 1.5 - 0.5); heat.data[i * 4 + 2] = 255 * Math.max(0, t * 3 - 2); heat.data[i * 4 + 3] = 255
    }
    x.putImageData(heat, TW, TH)
    x.font = '16px sans-serif'; x.fillStyle = '#fff'; x.strokeStyle = '#000'; x.lineWidth = 3
    for (const [label, px, py] of [['target', 8, 22], ['product', TW + 8, 22], ['overlay', 8, TH + 22], ['difference', TW + 8, TH + 22]]) { x.strokeText(label, px, py); x.fillText(label, px, py) }
    return { target: sa, product: sb, delta, sheet: sheet.toDataURL('image/png') }
  })()
}

async function inPage(browser, input) {
  const page = await browser.newPage()
  try {
    await page.setContent('<html><body></body></html>')
    return await page.evaluate(analyze, input)
  } finally { await page.close() }
}

// Writes <image>-compare.png and <image>-metrics.json next to the image.
async function compare(browser, targetFile, imageFile) {
  const r = await inPage(browser, { a: dataUrl(targetFile), b: dataUrl(imageFile) })
  fs.writeFileSync(stem(imageFile) + '-compare.png', Buffer.from(r.sheet.split(',')[1], 'base64'))
  delete r.sheet
  fs.writeFileSync(stem(imageFile) + '-metrics.json', JSON.stringify(r, null, 1))
  return { compare: path.resolve(stem(imageFile) + '-compare.png'), metrics: path.resolve(stem(imageFile) + '-metrics.json'), delta: r.delta }
}

const browser = await chromium.launch(LAUNCH)
try {
  if (argv[0] === '--measure') {
    const r = await inPage(browser, { a: dataUrl(argv[1]) })
    console.log(JSON.stringify({ ok: true, image: path.resolve(argv[1]), ...r.stats }))
  } else if (argv[0] === '--compare') {
    console.log(JSON.stringify({ ok: true, ...(await compare(browser, argv[1], argv[2])) }))
  } else {
    const [dir, out, w, h, target] = argv
    const root = path.resolve(dir)
    const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.ktx2': 'image/ktx2', '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.wasm': 'application/wasm' }
    const server = http.createServer((req, res) => {
      if (req.url === '/favicon.ico') { res.writeHead(204); return res.end() }
      let file = path.join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname))
      if (!file.startsWith(root)) { res.writeHead(403); return res.end() }
      if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html')
      fs.readFile(file, (err, buf) => {
        if (err) { res.writeHead(404); return res.end() }
        res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream' })
        res.end(buf)
      })
    })
    await new Promise(r => server.listen(0, '127.0.0.1', r))
    const errors = []
    try {
      const page = await browser.newPage({ viewport: { width: Number(w), height: Number(h) } })
      page.on('pageerror', e => errors.push(String(e.message || e)))
      page.on('console', m => { if (m.type() === 'error') errors.push(m.text()) })
      page.on('requestfailed', r => errors.push('request failed: ' + r.url()))
      await page.goto('http://127.0.0.1:' + server.address().port + '/', { waitUntil: 'load', timeout: 60000 })
      // Apps set window.__dreamReady = true once assets are loaded and a frame is drawn.
      await page.waitForFunction(() => window.__dreamReady === true, null, { timeout: 20000 }).catch(() => errors.push('window.__dreamReady was never set'))
      await page.waitForTimeout(2000)
      const stats = await page.evaluate(() => new Promise(done => {
        const gl = document.createElement('canvas').getContext('webgl2')
        const ext = gl && gl.getExtension('WEBGL_debug_renderer_info')
        const gpu = gl ? String(gl.getParameter(ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER)) : 'no-webgl'
        let frames = 0
        const t0 = performance.now()
        const tick = () => { frames++; performance.now() - t0 < 3000 ? requestAnimationFrame(tick) : done({ gpu, fps: frames * 1000 / (performance.now() - t0) }) }
        requestAnimationFrame(tick)
      }))
      fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true })
      await page.screenshot({ path: out })
      await page.close()
      const result = {
        ok: errors.length === 0,
        screenshot: path.resolve(out),
        fps: Math.round(stats.fps),
        gpu: stats.gpu,
        fpsReliable: !/swiftshader|llvmpipe|software|no-webgl/i.test(stats.gpu),
        errors: errors.slice(0, 20),
      }
      if (target) Object.assign(result, await compare(browser, target, out))
      console.log(JSON.stringify(result))
    } finally { server.close() }
  }
} finally {
  await browser.close()
}
`

// Every image in a run is made through this helper, so all agents call Codex the same way.
// Tested live, including three concurrent runs.
const IMAGEGEN_JS = `// node imagegen.mjs <outDir> <messageFile> [inputImage ...]
// Generates images with the Codex CLI's built-in image tool (no API keys) and copies them into outDir.
// The model comes from DREAM_CODEX_MODEL; if Codex refuses it, the account's default model is used.
// Prints one JSON line: { ok, model, images, reply, error }.
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const [outArg, msgFile, ...inputs] = process.argv.slice(2)
const out = path.resolve(outArg)
fs.mkdirSync(out, { recursive: true })
const t0 = Date.now()
const message = fs.readFileSync(msgFile, 'utf8') +
  '\\n\\nUse your built-in image_gen tool for every image, not an API key or a script. Copy each image you keep from $CODEX_HOME/generated_images into ' + out +
  ' under the file names requested above. Reply with the prompt you used for each image.'
const replyFile = path.join(os.tmpdir(), 'codex-reply-' + process.pid + '.txt')
const run = model => {
  const r = spawnSync('codex', [
    'exec', ...(model ? ['-m', model] : []), '--skip-git-repo-check', '--ephemeral', '-s', 'workspace-write', '-C', out,
    ...inputs.flatMap(f => ['-i', path.resolve(f)]), '-o', replyFile, '-',
  ], { input: message, encoding: 'utf8', timeout: 570000, env: { ...process.env, PATH: process.env.PATH + ':/opt/homebrew/bin' } })
  return { status: r.status, log: (r.stdout || '') + (r.stderr || '') + (r.error ? String(r.error) : '') }
}
let r = run(process.env.DREAM_CODEX_MODEL || '')
if (r.status !== 0 && /not supported|not available|unknown model/i.test(r.log)) r = run('')
const model = (r.log.match(/^model: (.+)$/m) || [])[1] || 'unknown'
const images = fs.readdirSync(out).map(f => path.join(out, f))
  .filter(f => /\\.(png|jpe?g|webp)$/i.test(f) && fs.statSync(f).mtimeMs >= t0)
let reply = ''
try { reply = fs.readFileSync(replyFile, 'utf8'); fs.unlinkSync(replyFile) } catch {}
const errors = r.log.split('\\n').filter(l => /error/i.test(l) && !/rmcp::transport/.test(l)).slice(-3).join(' | ')
console.log(JSON.stringify({ ok: r.status === 0 && images.length > 0, model, images, reply: reply.slice(0, 4000), error: r.status === 0 ? '' : errors || 'codex exited ' + r.status }))
`

// ---------------------------------------------------------------- setup

const setup = await call(`Prepare a project for an automated dream-loop run. Do these steps and nothing else; do not start building the product.

The product will be: ${A.request}

1. Repo: the project root is ${A.repo ?? 'your current working directory'}; return its absolute path as repo. Make every check in this step before changing anything.
   - If it does not exist, create it.
   - If it is not inside a git repo: when it is empty, git init it and make an empty first commit; when it has any files, return ok=false with reason "not a git repo; git init and commit the existing product first" and change nothing.
   - If it is inside a git repo but is not the repo's top level, return ok=false and name the top level.
   - If the repo has uncommitted changes, return ok=false with reason "working tree is dirty; commit or stash first".
   - If <repo>/${APP}/index.html exists but the product needs a build step or dev server rather than static files, return ok=false with reason "existing product is not a static site".
   - If any ${TAG}/* branch other than ${TAG}/r0 exists, return ok=false and name them. If ${TAG}/r0 exists and points at HEAD, an earlier run stopped before building; reuse it. If it points anywhere else, return ok=false.
   - Add .dream-loop/ to .git/info/exclude (not .gitignore, so nothing needs committing). Create branch ${TAG}/r0 at HEAD without checking it out, unless it already exists.
2. Capture tool: write the script between the markers verbatim to <repo>/.dream-loop/harness/capture.mjs. Then in <repo>/.dream-loop/harness run npm init -y, npm install playwright, and npx playwright install chromium, skipping whatever is already installed.
<<<capture.mjs
${CAPTURE_JS}
capture.mjs>>>
3. Smoke test, run outside the sandbox because Chromium cannot start inside it: write <repo>/.dream-loop/harness/smoke/index.html, a page whose full-window WebGL canvas clears to solid orange and then sets window.__dreamReady = true. Run node "<repo>/.dream-loop/harness/capture.mjs" "<repo>/.dream-loop/harness/smoke" "<repo>/.dream-loop/harness/smoke/out.png" ${VW} ${VH}; it must print ok=true and out.png must be orange. Then run it with --measure on out.png (meanColor must be orange) and with --compare out.png out.png (meanPixelDifference must be 0). If Chromium fails to launch or gpu names a software renderer (SwiftShader, llvmpipe), you may change only the LAUNCH options in the script, for example adding --use-angle=metal on macOS. If hardware rendering cannot be made to work, keep a working software setup. Return gpu and fpsReliable from the final smoke run.
4. Image helper and tools: write the script between the markers verbatim to <repo>/.dream-loop/harness/imagegen.mjs. Do not run it. Set codex=true if the Codex CLI is found (command -v codex, then again with PATH="/opt/homebrew/bin:$PATH") and codex login status reports a login; otherwise codex=false. Set blender to the absolute path of the Blender executable if one exists (command -v blender, or /Applications/Blender.app/Contents/MacOS/Blender), else "". Set falKey=true if FAL_KEY or FAL_API_KEY is set in the environment; never print its value.
<<<imagegen.mjs
${IMAGEGEN_JS}
imagegen.mjs>>>
5. Target: ${A.target
    ? `copy ${A.target} to <repo>/.dream-loop/runs/${TAG}/target.png, converting it to PNG if needed, and return that path as target. Return width=${VW} and the height that matches the target's aspect ratio.`
    : `none was supplied. Return target="" and width=${VW}, height=${VH}.`}
6. Baseline: if <repo>/${APP}/index.html exists, this run improves an existing product. Capture it, outside the sandbox, to <repo>/.dream-loop/runs/${TAG}/shots/r0.png at the returned width and height, and return that path as baselineShot and its fps as baselineFps. Otherwise return baselineShot="" and baselineFps=0.`,
  { model: SONNET, effort: 'medium', label: 'setup', phase: 'Setup', schema: SETUP })
if (!setup?.ok) throw new Error(`Setup stopped: ${setup?.reason ?? 'no result'}`)

const repo = setup.repo
const RUN = `${repo}/.dream-loop/runs/${TAG}`
const HARNESS = `${repo}/.dream-loop/harness`
const vw = setup.width, vh = setup.height
const falAvailable = setup.codex && Boolean(FAL_RELAY || setup.falKey)
// With the target as the last argument, the tool also writes a compare sheet and numbers.
const capture = (dir, out) => `node "${HARNESS}/capture.mjs" "${dir}" "${out}" ${vw} ${vh} "${target}"`
const OUTSIDE = 'Run it outside the sandbox from the first attempt; Chromium cannot start inside it.'
// Shell lines that print the name of each set API key whose value appears in a git log range. Never prints a value.
const leakScan = range => KEY_NAMES.map(k => `[ -n "$${k}" ] && git -C "${repo}" log -p ${range} | grep -qF -- "$${k}" && echo ${k}`).join('\n')
const imagegen = (out, msg, inputs = []) => `DREAM_CODEX_MODEL=${CODEX_MODEL} node "${HARNESS}/imagegen.mjs" "${out}" "${msg}"${inputs.map(f => ` "${f}"`).join('')}`
const IMAGEGEN_RULES = 'Run it outside the sandbox (it needs network access and writes Codex state under ~/.codex), with the longest command timeout, and use absolute paths rather than $TMPDIR. It prints one JSON line listing the images it saved. Each image takes about a minute, so put up to 6 images in one request. If it reports a rate limit, wait a minute and retry.'
if (!setup.fpsReliable) log(`Captures render in software (${setup.gpu}), so measured FPS means nothing; the FPS floor is not enforced`)
if (!setup.codex && !setup.target) throw new Error('No target image: the Codex CLI is missing or not logged in. Run codex login, or pass args.target.')
if (!setup.codex) log('Codex CLI is missing or not logged in: no generated textures, backdrops, or cutouts this run')

// ---------------------------------------------------------------- dream

let target = setup.target, dreamPrompt = '', dreamGenerator = ''
if (!target) {
  const dreams = `${RUN}/dreams`
  const d = await call(`Produce the target image for a dream-loop build: a real in-engine screenshot of the finished product, which will later be built to match it pixel for pixel.

1. Write this request to ${dreams}/brief.txt:
---
A real in-engine screenshot of the finished product described below. Landscape, ${vw}x${vh} aspect ratio. It must read as an actual frame from a real-time engine, not concept art, a cinematic shot, a photo, or a painting. ${setup.baselineShot ? 'The attached image is a screenshot of the current product; produce a refined version of it that delivers the request: the same product improved, not a different one. ' : ''}Make 3 distinct variants, saved as candidate-1.png, candidate-2.png, and candidate-3.png.

Product: ${A.request}
---
2. Run the image helper, which drives the Codex CLI's built-in image tool:
   ${imagegen(dreams, `${dreams}/brief.txt`, setup.baselineShot ? [setup.baselineShot] : [])}
   ${IMAGEGEN_RULES}
3. Open every candidate and save the most impressive one that still reads as a believable real-time frame to ${RUN}/target.png at exactly ${vw}x${vh}; if it is another size, center-crop to that aspect ratio and resize.
Return the image prompt from the helper's reply as prompt and "codex " plus its model as generator. If no candidate was produced, return ok=false with the helper's error as the reason. Do not fall back to any image API.`,
    { model: SONNET, effort: 'medium', label: 'dream', phase: 'Dream', schema: DREAM })
  if (!d?.ok) throw new Error(`No target image: ${d?.reason ?? 'dream failed'}. Check that codex login works, or pass args.target.`)
  target = d.path
  dreamPrompt = d.prompt
  dreamGenerator = d.generator
  log(`Target generated by ${d.generator}`)
}


const ROUTES = [
  setup.codex && 'codex for images (seamless flat unlit textures, backdrop layers for the far distance, sprites, decals)',
  setup.blender && 'blender for architecture, props, and repeated kit pieces',
  falAvailable && `fal for at most ${FAL_JOBS} organic hero objects, such as a character, that Blender cannot make convincingly`,
].filter(Boolean)
const GIT_RULE = wt => `Your shell resets to another folder between commands, which may be the user's own checkout: start every command with cd "${wt}" && or use absolute paths. Run every git command with -C: git -C "${wt}" for your work, and git -C "${repo}" only for worktree add and remove and branch commands. Never run git without -C, so nothing lands on the user's checked-out branch.`

// ---------------------------------------------------------------- director's plan

// One strong-model call before anything is built: the judgment the first run took four rounds to reach.
const plan = await call(`You direct a dream-loop build: a real-time scene built to match a target screenshot. Cheaper builders carry out your plan one round at a time, each starting fresh with only your plan and a short scene file, so the plan has to carry the whole picture. Make it specific, measurable, and practical for the stack the request asks for.

Target: ${target}
Request: ${A.request}

1. Run node "${HARNESS}/capture.mjs" --measure "${target}" (${OUTSIDE}) for the target's brightness, contrast (darkP10 and brightP90), warmth, saturation, and 3x3 brightness grid, row by row from the top left.
2. Write the plan in markdown with these sections:
   - Camera: projection; pitch, yaw, and field of view in degrees; where the player sits in the frame as percent from left and top; what each frame edge cuts off.
   - Layout: every major element with its position in the frame, depth layer (foreground, midground, background, far), and rough real-world size in meters.
   - Depth and atmosphere: how to build the far distance cheaply (backdrop image layers, cards, fog per layer), with fog colors as hex and densities.
   - Lighting: each light source with its hex color and relative intensity; exposure, contrast, and warmth targets from the measurements.
   - Materials: each surface with hex color, pattern, real-world scale, roughness, and wetness, and which shared asset covers it.
   - Motion: what moves and how.
   - Build order: camera first, then blockout, lighting, materials, and detail, each with what done looks like.
   - Pitfalls: the specific ways a build of this scene tends to go wrong, and how to avoid each.
3. ${ROUTES.length ? `List the shared assets worth making once, at most ${MAX_ASSETS}, most important first, each with a short lowercase id, a route (${ROUTES.join('; ')}), and a description detailed enough to make it without seeing the target.` : 'No asset tools are available this run; return an empty asset list.'}
Save the plan to ${RUN}/plan.md and return it with the asset list.`,
  { model: OPUS, effort: 'high', label: 'direct plan', phase: 'Direct', schema: PLAN })
if (!plan) throw new Error('The director\'s plan failed; resume the run to retry it')
let opusCalls = 1

// ---------------------------------------------------------------- shared assets

const library = [] // { id, route, files, notes }
let falUsed = 0
const librarySummary = () => library.length
  ? library.map(a => `- ${a.id} (${a.route}): ${a.files.join(', ')}${a.notes ? `. ${a.notes}` : ''}`).join('\n')
  : '(none)'

const codexBatch = (items, name) => call(`Make shared images for a dream-loop build with the image helper, which drives the Codex CLI's built-in image tool.
Target image, to attach as an input image so the results match it: ${target}
The director's plan, for colors and scale: ${RUN}/plan.md

Images:
${items.map(a => `- ${a.id}.png: ${a.description}`).join('\n')}

1. Write one request to ${RUN}/requests/${name}.txt (create the folder if needed) naming every image with its exact file name, size or aspect ratio, whether it must tile seamlessly, and whether its background must be transparent. Textures are flat, evenly lit, and orthographic, with no baked lighting or perspective.
2. Run: ${imagegen(`${RUN}/assets/${name}`, `${RUN}/requests/${name}.txt`, [target])}
   ${IMAGEGEN_RULES}
3. Open each image once. If one is missing or clearly wrong for its description, request it again once.
Return one item per image: id (the name without .png), ok, files (absolute paths), and a one-line note on what it shows.`,
  { model: HAIKU, effort: 'medium', label: `assets ${name}`, phase: 'Assets', schema: BATCH })
  .then(r => r?.items ?? null)

const blenderAsset = a => call(`Model one shared asset for a dream-loop build in Blender, through its Python API: "${setup.blender}" --background --python <script>.
Asset ${a.id}: ${a.description}
Reference: the target image ${target}, and the Layout and Materials sections of ${RUN}/plan.md for size, colors, and scale.
Your shell may start in the user's own checkout, so use absolute paths for every file you write, and keep your script and scratch files under ${RUN}/assets/${a.id}/. Use real-world scale in meters with the origin at the base center, and export with the glTF exporter's default +Y up. Split the model into parts by material and name each material after its surface (stone, trim, wood, metal, and so on) so the scene can apply shared textures. Keep it lean enough for a real-time scene.
Export to ${RUN}/assets/${a.id}/${a.id}.glb and render a preview to ${RUN}/assets/${a.id}/${a.id}-preview.png. Open the preview, fix anything clearly wrong once, and return ok, files (both paths), and a note on its size in meters and its material names.`,
  { model: SONNET, effort: 'medium', label: `asset ${a.id}`, phase: 'Assets', schema: MADE })
  .then(r => r && { ...r, id: a.id })

const falAsset = a => call(`Make one hero 3D model for a dream-loop build with fal.ai image-to-3D. Submit exactly one job. Your shell may start in the user's own checkout, so use absolute paths for every file you write, and keep scripts and scratch files under ${RUN}/assets/${a.id}/.
Asset ${a.id}: ${a.description}
1. Cut a clean image of the object out of the target with the image helper: the object alone on a plain or transparent background, hidden parts completed, so the model matches the target instead of being reimagined. Write that request, naming the file ${a.id}-cutout.png, to ${RUN}/requests/${a.id}-cutout.txt, then run:
   ${imagegen(`${RUN}/assets/${a.id}`, `${RUN}/requests/${a.id}-cutout.txt`, [target])}
   ${IMAGEGEN_RULES}
2. ${FAL_RELAY
    ? `Send fal requests to the local relay at ${FAL_RELAY} in place of https://queue.fal.run, with the same paths and bodies and no key or Authorization header; the relay adds it. The queue URLs it returns already point back at the relay, and finished model files download without a key. If the sandbox blocks the relay, allow ${FAL_RELAY.replace(/^https?:\/\//, '')} as a network destination. A 429 reply means the run's fal jobs are used up; stop and return ok=false.`
    : 'Read FAL_KEY or FAL_API_KEY from the environment inside the shell command that calls fal; never print it or write it to a file.'} Submit the cutout to a strong image-to-3D model; check fal's docs for the current endpoint and parameters. Jobs are async: submit, then poll.
3. Download the GLB to ${RUN}/assets/${a.id}/${a.id}.glb.${setup.blender ? ` Import it in Blender, fix its orientation and scale (meters, +Y up, origin at the base), re-export to the same path, and render a preview to ${RUN}/assets/${a.id}/${a.id}-preview.png.` : ''}
Return ok, files, and a note on its size, orientation, and triangle count.`,
  { model: SONNET, effort: 'medium', label: `asset ${a.id}`, phase: 'Assets', schema: MADE })
  .then(r => r && { ...r, id: a.id })

let assetNews = '' // what happened to builders' last requests, told to the next builders
// Builds wanted assets that are not in the library yet, in parallel, and adds the ones that worked.
async function buildAssets(wanted, name) {
  const items = [], dropped = []
  for (const w of wanted) {
    const id = slug(w.id)
    if (library.some(a => a.id === id) || items.some(i => i.id === id)) continue
    let route = w.route
    if (route === 'fal' && (!falAvailable || falUsed >= FAL_JOBS)) route = 'blender'
    if ((route === 'codex' && !setup.codex) || (route === 'blender' && !setup.blender)) { dropped.push(id); continue }
    if (route === 'fal') falUsed++ // reserved before the job runs, so the run cannot exceed falJobs
    items.push({ ...w, id, route })
  }
  if (dropped.length) log(`${name}: skipped ${dropped.join(', ')}; the tool each needs is unavailable`)
  if (!items.length) return { built: [], dropped, failed: [] }
  const codexItems = items.filter(i => i.route === 'codex')
  const batches = []
  for (let i = 0; i < codexItems.length; i += 6) batches.push(codexItems.slice(i, i + 6))
  const made = (await parallel([
    ...batches.map((batch, n) => () => codexBatch(batch, `${name}-${n + 1}`)),
    ...items.filter(i => i.route === 'blender').map(i => () => blenderAsset(i)),
    ...items.filter(i => i.route === 'fal').map(i => () => falAsset(i)),
  ])).filter(Boolean).flat()
  for (const m of made) {
    const src = items.find(i => i.id === slug(String(m.id).replace(/\.png$/i, '')))
    if (src && m.ok && m.files?.length && !library.some(a => a.id === src.id)) library.push({ id: src.id, route: src.route, files: m.files, notes: m.notes })
  }
  const built = items.filter(i => library.some(a => a.id === i.id)).map(i => i.id)
  const failed = items.filter(i => !built.includes(i.id)).map(i => i.id)
  log(`${name}: ${built.length} of ${items.length} assets built${failed.length ? `; failed: ${failed.join(', ')}` : ''}`)
  return { built, dropped, failed }
}


if (plan.assets.length > MAX_ASSETS) log(`The plan listed ${plan.assets.length} assets; building the first ${MAX_ASSETS}`)
await buildAssets(plan.assets.slice(0, MAX_ASSETS), 'assets')

// ---------------------------------------------------------------- agents

const critique = (cap, prev, label) => call(`You judge how close a live product screenshot is to a target image.

Target: ${target}
Current product: ${cap.screenshot}
Compare sheet: ${cap.compare} (top left target, top right product, bottom left 50% overlay, bottom right difference map)
Measured, product minus target: ${cap.metrics}
${prev?.verdict ? `Previous product: ${prev.shot}\nPrevious verdict: ${JSON.stringify(prev.verdict)}` : ''}
Measured frame rate: ${cap.fps} fps${FPS ? ` (floor ${FPS})` : ''}.${cap.errors?.length ? `\nRuntime errors: ${cap.errors.join('; ')}` : ''}

Score each category; fractions are fine:
- composition 0-3: camera, framing, layout; position and scale of every major element
- lighting 0-3: palette, exposure, shadows, contrast, atmosphere, reflections, glows; overall brightness against the target
- materials 0-3: texture, roughness, translucency, and wetness of every surface; anything blocky, plasticky, too smooth, or fake unless the target looks that way too
- details 0-1: every small element, compared with a fine-toothed comb

List every gap between the product and a perfect score, ordered by impact. Each gap names what in the image causes the mismatch and how to fix it, with numbers where they help (degrees, hex colors, percent of the frame, meters). "The tree looks fake" is not acceptable; "the canopy is one smooth sphere with no leaf clusters or alpha-cut foliage" is. If a model, the lighting, or the whole scene needs to be redone, say so. The goal is for the two images to be identical.

${prev?.verdict
    ? 'Compare the current product with the previous one side by side. Set regressed=true only if the current product is further from the target overall; a large change that loses some details but gets closer overall is not a regression. Either way, list everything that got worse in regressions. Stay consistent with the previous verdict, but do not raise scores out of courtesy.'
    : 'This is the first verdict: set regressed=false and regressions="".'}`,
  { model: SONNET, effort: 'high', label, phase: 'Judge', schema: VERDICT })

const directive = mode => mode === 'optimize'
  ? `The judge is satisfied with the visuals, but the product runs at ${best.fps} fps against a floor of ${FPS}. This round, optimize: lossless wins first, then changes with minimal visual impact. Do not trade away visual quality.`
  : ''

function builderPrompt(c, mode, round, first) {
  const gaps = best.verdict?.gaps ?? []
  return `You are the builder for round ${round} of a dream-loop run: make the live product match the target screenshot. ${first
    ? (best.shot ? 'This round improves an existing product and starts its scene file.' : 'There is no product yet; this round builds the first version.')
    : 'Earlier rounds built the current product; continue from it.'}

Workspace: run git -C "${repo}" worktree add "${c.wt}" -b ${c.branch} ${best.branch}. If that branch or worktree already exists from an interrupted attempt, remove both (git -C "${repo}" worktree remove --force, then git -C "${repo}" branch -D) and run the command again. If git reports a lock, wait a few seconds and retry. Work only inside ${c.wt}. ${GIT_RULE(c.wt)}

The app lives at ${c.wt}/${APP} and is served as static files from that folder, with index.html at its root. Every round starts from a fresh checkout, and untracked files such as node_modules do not carry over, so anything the app loads at runtime must be committed or come from a CDN. If you use npm, create package.json in the app folder first. Once the scene has loaded its assets and drawn a frame, set window.__dreamReady = true.

The scene file: ${first
    ? 'create SCENE.md at the root of your worktree with four sections: Plan (the director\'s plan below, verbatim), Built (what exists, where it lives in the code, which assets it uses), Techniques (the approaches you chose and why), and Tried and dropped. Keep the last three short enough to read in a minute; later builders start from this file with no other memory.'
    : `read SCENE.md at the root of your worktree first; it is the only memory earlier builders left. Keep Built and Techniques current, and add anything you tried and dropped. ${planChanged ? 'The director has revised the plan: replace the Plan section with the revised plan below, verbatim.' : 'Leave the Plan section as it is.'}`}

User request: ${A.request}

Target image: ${target}
${best.shot ? `Current product compared with the target: ${compareOf(best.shot)} (top left target, top right product, bottom left 50% overlay, bottom right difference map). Measured differences: ${metricsOf(best.shot)}.` : ''}${best.errors?.length ? `\nRuntime errors in the current product: ${best.errors.join('; ')}` : ''}
${first || planChanged ? `\nThe director's ${first ? '' : 'revised '}plan:\n${planText}\n` : ''}${focus ? `\nThe director's top priority for this round: ${focus}\n` : ''}${gaps.length ? `\nJudge's gaps on the current product (${best.score}/10), ordered by impact:\n${gaps.map(g => `- ${g.gap} Fix: ${g.fix}`).join('\n')}\n` : ''}${rejected ? `\nLast round's attempt was discarded. ${rejected}\n` : ''}
${directive(mode)}

Shared assets, already made; use these rather than making your own. They live outside the app, so copy the files you use into ${c.wt}/${APP}/assets/ and commit them:
${librarySummary()}${assetNews ? `\n${assetNews}` : ''}

How to work: ${mode === 'optimize'
    ? 'follow the optimize instruction above and change nothing else.'
    : first
      ? 'start with the camera. Match the plan\'s projection, pitch, yaw, field of view, and where the player sits in the frame, checking against the overlay in the compare sheet, before you build anything else. Then follow the plan\'s build order.'
      : `${focus ? 'start with the director\'s priority, then work' : 'work'} the judge's gaps, most impactful first.`} This round can run to about ${first ? FIRST_CALLS : ROUND_CALLS} tool calls; spend them on visible progress.${FPS ? ` Keep the frame rate at or above ${FPS} fps.` : ''}

Check your work with this command. ${OUTSIDE}
${capture(`${c.wt}/${APP}`, c.shot)}
It saves the screenshot, a compare sheet, and numbers against the target. Use the numbers for brightness, warmth, and contrast, and the 3x3 grid and the overlay for layout. The averages can match while the picture is still wrong, so look at the compare sheet too, and open only the latest one. Nothing else renders while you work, so its fps reading is reliable. Fix anything that breaks the app: console errors, failed requests, a blank frame, assets at the wrong orientation or scale. Before you finish, compare your final frame with where you started; if your last changes made it worse, revert them so you hand back your best state.

${ROUTES.length ? `If you need a new image or model, add it to assetRequests: a short lowercase id, a route (${ROUTES.join('; ')}), and a description detailed enough to make it without seeing the target. Up to ${REQUESTS_PER_ROUND} new requests are built before the next round, and the next builder is told what was built.` : 'No asset tools are available this run, so build what you need in code.'}${setup.codex ? ` Make an image yourself only if this round cannot proceed without it: write the request to ${RUN}/requests/r${round}-own.txt, then run ${imagegen(`${c.wt}/${APP}/assets/gen`, `${RUN}/requests/r${round}-own.txt`, [target])}. ${IMAGEGEN_RULES}` : ''} Never call fal or any image-to-3D service yourself; request it. Never write an API key into any file.

Commit all work, including the updated SCENE.md, to ${c.branch}. Return a summary and any assetRequests.`
}

const verify = (c, base, name) => call(`Re-capture a dream-loop candidate on its own, check it, and tidy up. Never run git without -C.
1. If git -C "${c.wt}" status --porcelain shows changes, commit them with git -C "${c.wt}" add -A and git -C "${c.wt}" commit -m "dream-loop: uncommitted leftovers", and set leftovers=true; otherwise leftovers=false.
2. Secrets: run these lines exactly as written. They print the name of any API key whose value appears in this branch's new commits, and never print a value.
${leakScan(`${base}..${c.branch}`)}
   If any name was printed, set leak=true and add "secret committed: <name>" to errors; otherwise leak=false.
3. Run this. ${OUTSIDE}
   ${capture(`${c.wt}/${APP}`, `${RUN}/shots/${name}-final.png`)}
4. Remove the worktree with git -C "${repo}" worktree remove --force "${c.wt}"; the branch stays.
Return the printed screenshot, compare, fps, and errors, plus leftovers and leak. For metrics, return the printed "delta" object itself as a JSON string, not the path in the printed "metrics" field. If the capture command itself failed, return ok=false, screenshot="", compare="", fps=0, metrics="", and the error in errors.`,
  { model: HAIKU, effort: 'low', label: `capture ${name}`, phase: 'Capture', schema: CAPTURE })

// The director checks in after the first build and when progress slows. Read-only except for its plan file.
const course = (round, why, attempt) => call(`You direct a dream-loop build that cheaper builders carry out one round at a time; each starts fresh with only a short scene file and your plan. Round ${round} just finished, and you are checking in because ${why}. Change nothing except writing your revised plan to ${RUN}/plan-r${round}.md. Read code with git -C "${repo}" show ${best.branch}:<path>, and list files with git -C "${repo}" ls-tree -r --name-only ${best.branch}.

Target: ${target}
Best product so far, compared with the target: ${compareOf(best.shot)} (top left target, top right product, bottom left 50% overlay, bottom right difference map); numbers in ${metricsOf(best.shot)}.
The judge's verdict on that best product: ${JSON.stringify(best.verdict)}${attempt ? `\nThis round's attempt was discarded: ${attempt}` : ''}
Score history: ${history.map(h => `round ${h.round}: ${h.score ?? 'no verdict'}${h.picked ? ' kept' : h.score != null ? ' discarded' : ''}`).join('; ')}
${started ? `Scene file: git -C "${repo}" show ${best.branch}:SCENE.md` : 'There is no scene file yet; no builder version has been kept.'}
Current plan:
${planText}

Diagnose the few root causes holding the score back: causes, not symptoms. For example: a camera that cannot produce the target's framing, a technique that cannot produce a look, assets at the wrong scale, a lighting model fighting the palette. Read the code that matters before deciding. Then return:
- diagnosis: the root causes, briefly;
- focus: the single change that would move the score most next round, specific enough to act on (values, files, technique);
- plan: the full plan in the same sections, revised where it was wrong or missing something;
- assets: ${ROUTES.length ? `up to 3 new shared assets worth making, if any (routes: ${ROUTES.join('; ')})` : 'an empty list; no asset tools are available'}.`,
  { model: OPUS, effort: 'high', label: `direct r${round}`, phase: 'Direct', schema: COURSE })

// ---------------------------------------------------------------- loop

let best = { branch: `${TAG}/r0`, shot: setup.baselineShot, fps: setup.baselineFps, errors: [], score: -1, verdict: null }
if (best.shot) {
  // The baseline needs a compare sheet like every later candidate. Images only; the main checkout is never touched.
  const cmp = await call(`Run node "${HARNESS}/capture.mjs" --compare "${target}" "${best.shot}". ${OUTSIDE} Return ok, the printed compare path, and, as metrics, the printed "delta" object itself as a JSON string (not the path in the printed "metrics" field).`,
    { model: HAIKU, effort: 'low', label: 'compare baseline', phase: 'Capture', schema: obj({ ok: B, compare: S, metrics: S }) })
  const v = cmp?.ok && await critique({ screenshot: best.shot, compare: cmp.compare, metrics: cmp.metrics, fps: best.fps, errors: [] }, null, 'judge baseline')
  if (v) best = { ...best, verdict: v, score: scoreOf(v) }
}
const fpsOk = () => !FPS || !setup.fpsReliable || best.fps >= FPS
log(`Target ${target}; plan ready; ${library.length} shared assets; up to ${MAX_ROUNDS} rounds; stop at ${DONE}/10${FPS && setup.fpsReliable ? ` and ${FPS} fps` : ''}`)

const history = []
const bests = [] // best score after each round
let peak = { score: best.score, branch: best.branch } // the keep rule's tolerance is measured from here, so scores cannot slide
let mode = best.shot && best.score >= DONE ? 'optimize' : 'normal', rejected = ''
let planText = plan.plan, planChanged = false, focus = '' // a revised plan and priority stay until a builder that carries them is kept
let started = false, reviewed = false, lastCourse = 0, sinceGain = 0
let dead = 0 // consecutive rounds that produced no verdict
let pending = [] // asset requests, built before the next round
let status = best.shot && best.score >= DONE && fpsOk() ? 'done' : null
let roundCost = RESERVE, spentAtStart = budget.spent(), lastCost = 0

const failStatus = () => (budget.total && budget.remaining() <= 0 ? 'budget' : 'failing')
const planFiles = [`${RUN}/plan.md`]
for (let round = 1; !status && round <= MAX_ROUNDS; round++) {
  if (round > 1) lastCost = budget.spent() - spentAtStart // everything the last round spent, director and assets included
  if (lastCost) roundCost = Math.max(RESERVE, lastCost)
  if (budget.total && budget.remaining() < roundCost + FINISH_RESERVE) { status = 'budget'; break }
  spentAtStart = budget.spent()
  const entry = { round, mode }
  history.push(entry)
  const skip = why => { entry.note = why; log(`r${round}: ${why}`); bests.push(best.score); sinceGain++; return ++dead >= 2 }

  // Drop requests for assets that exist or were asked for twice, then cap what is left.
  const wanted = pending.filter((w, i) => !library.some(a => a.id === slug(w.id)) && pending.findIndex(x => slug(x.id) === slug(w.id)) === i)
  pending = []
  if (wanted.length) {
    if (wanted.length > REQUESTS_PER_ROUND) log(`r${round}: ${wanted.length} new asset requests; building the first ${REQUESTS_PER_ROUND}`)
    const res = await buildAssets(wanted.slice(0, REQUESTS_PER_ROUND), `r${round}-assets`)
    const notBuilt = [...wanted.slice(REQUESTS_PER_ROUND).map(w => slug(w.id)), ...res.dropped, ...res.failed]
    assetNews = `Asset requests from last round: built ${res.built.join(', ') || 'none'}${notBuilt.length ? `; not built: ${notBuilt.join(', ')} (build those in code or request them again)` : ''}.`
    if (budget.total && budget.remaining() < roundCost + FINISH_RESERVE) { entry.note = 'budget ran low after asset builds'; status = 'budget'; break }
  } else assetNews = ''

  const first = !started
  const c = { id: `r${round}`, branch: `${TAG}/r${round}`, wt: `${RUN}/wt/r${round}`, shot: `${RUN}/shots/r${round}.png` }
  const b = await call(builderPrompt(c, mode, round, first),
    { model: SONNET, effort: first ? 'high' : 'medium', label: `build r${round}`, phase: 'Build', schema: BUILD })
  if (!b?.ok) { if (skip('the builder failed')) { status = failStatus(); break } continue }
  pending.push(...(b.assetRequests ?? []))

  const cap = await verify(c, best.branch, c.id)
  if (cap?.leak) { if (skip(`${c.branch} committed an API key and was discarded`)) { status = failStatus(); break } continue }
  if (!cap?.screenshot) { if (skip(`re-capture of ${c.id} failed`)) { status = failStatus(); break } continue }
  const v = await critique(cap, best, `judge ${c.id}`)
  if (!v) { if (skip('judge failed')) { status = failStatus(); break } continue }
  dead = 0

  const score = scoreOf(v)
  const prevScore = best.score
  const accepted = mode === 'optimize'
    ? !v.regressed && score >= Math.max(DONE, peak.score - TOLERANCE) && cap.fps > best.fps
    : !v.regressed && score >= peak.score - TOLERANCE
  const gained = accepted && (mode === 'optimize' || score > prevScore)
  Object.assign(entry, { score, fps: cap.fps, picked: accepted ? c.id : null, leftovers: cap.leftovers, summary: b.summary })
  if (accepted) {
    best = { branch: c.branch, shot: cap.screenshot, fps: cap.fps, errors: cap.errors, score, verdict: v }
    if (score > peak.score) peak = { score, branch: c.branch }
    started = true
    planChanged = false
    focus = ''
    rejected = ''
  } else {
    // The discarded branch's SCENE.md notes are not on the best branch, so carry its summary forward.
    rejected = `Judge's note: ${v.regressions || (mode === 'optimize'
      ? `it ran at ${cap.fps} fps against ${best.fps} and scored ${score}`
      : `it scored ${score} against a best of ${peak.score}`)} What that builder tried: ${b.summary}`
  }
  sinceGain = gained ? 0 : sinceGain + 1
  bests.push(best.score)
  log(`r${round} ${mode}: judge ${score}, ${accepted ? 'kept' : 'discarded'}; best ${best.score} at ${best.fps} fps`)

  if (best.score >= DONE && fpsOk()) { status = 'done'; break }
  if (mode === 'optimize' && !gained) { status = 'stalled'; break }
  if (best.score >= DONE) { mode = 'optimize'; continue }
  if (sinceGain >= STALL_ROUNDS) { status = 'stalled'; break }

  // The director checks in after the first kept build, and when the best score has gained
  // less than a point over two rounds (at most every other round).
  const twoAgo = bests.length >= 3 ? bests[bests.length - 3] : null
  const slow = twoAgo !== null && best.score - twoAgo < 1 && round - lastCourse >= 2
  const why = started && !reviewed ? 'the first build is in and sets the trajectory for every later round'
    : slow ? `the best score has gained less than a point over the last two rounds (${twoAgo} to ${best.score})`
    : ''
  const roomForAnother = round < MAX_ROUNDS && !(budget.total && budget.remaining() < roundCost + FINISH_RESERVE)
  if (why && best.shot && roomForAnother) {
    const r = await course(round, why, accepted ? '' : rejected)
    opusCalls++
    lastCourse = round
    entry.director = r ? r.focus : 'director call failed'
    if (r) {
      if (started) reviewed = true
      planText = r.plan
      planChanged = true
      focus = r.focus
      planFiles.push(`${RUN}/plan-r${round}.md`)
      pending.unshift(...r.assets)
      log(`r${round}: director's priority: ${r.focus}`)
    } else log(`r${round}: the director call failed; it will be tried again next round`)
  }
}
status ??= 'max-rounds'

// ---------------------------------------------------------------- finish

const result = {
  status,
  score: best.score,
  peak, // highest judge score seen; can sit up to TOLERANCE above the final score
  fps: best.fps,
  fpsMeasured: setup.fpsReliable,
  branch: best.shot ? `${TAG}/best` : null,
  checkout: best.shot ? `${RUN}/best` : null,
  screenshot: best.shot,
  target,
  dreamGenerator,
  dreamPrompt,
  plans: planFiles,
  library: library.map(a => `${a.id} (${a.route})`),
  falJobsUsed: falUsed,
  opusCalls,
  rounds: history.length,
  topGaps: (best.verdict?.gaps ?? []).slice(0, 5),
  history,
}

const fin = await call(`Wrap up a dream-loop run in ${repo}. Do not check out another branch in the main checkout or change its files; work only with git refs, worktrees, and files under ${repo}/.dream-loop. Never run git without -C.
1. Remove any worktrees under ${RUN}/wt/ and any worktree at ${RUN}/best with git -C "${repo}" worktree remove --force <path>.
2. ${best.shot ? `git -C "${repo}" branch -f ${TAG}/best ${best.branch}, then git -C "${repo}" worktree add "${RUN}/best" ${TAG}/best. Set branchCreated=true if both succeed.` : 'No candidate was kept; skip this step and set branchCreated=false.'}
3. Secrets: run this loop exactly as written. It prints "<branch> <key name>" for any API key value found in a run branch, and never prints a value. Return every branch it names as leaks.
git -C "${repo}" for-each-ref --format='%(refname:short)' refs/heads/${TAG}/ | while read BRANCH; do
${leakScan(`${TAG}/r0..$BRANCH`).split('\n').map(l => `  ${l.replace(/ && echo (\w+)$/, ' && echo "$BRANCH $1"')}`).join('\n')}
done
4. Write the JSON between the markers to ${RUN}/run.json using a quoted heredoc so nothing is interpolated, and write {"leaks": [...]} from step 3 to ${RUN}/leaks.json. Confirm both parse with node -e "JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))" <file>. Return ok=true only if they do.
<<<json
${JSON.stringify(result)}
json>>>`,
  { model: HAIKU, effort: 'low', label: 'finish', phase: 'Finish', schema: obj({ ok: B, branchCreated: B, leaks: { type: 'array', items: S } }) })

if (!fin?.branchCreated) Object.assign(result, { branch: null, checkout: null })
result.leaks = fin?.leaks ?? null
result.logWritten = Boolean(fin?.ok)
if (result.leaks?.length) log(`API key values found in ${result.leaks.join(', ')}; delete those branches before pushing anything`)
return result
