export const meta = {
  name: 'dream-loop-fast',
  description: 'Dream a target screenshot, then hill-climb toward it: parallel Sonnet builders, Haiku selection, Sonnet judge',
  whenToUse: 'Build a game, app, or 3D scene to high visual fidelity (dream-loop) with many cheap rounds instead of a few expensive ones. args: { request, ...options }',
  phases: [
    { title: 'Setup', detail: 'repo and capture harness', model: 'claude-sonnet-5-5' },
    { title: 'Dream', detail: 'generate the target screenshot', model: 'claude-sonnet-5-5' },
    { title: 'Build', detail: 'parallel builders, one git worktree each', model: 'claude-sonnet-5-5' },
    { title: 'Select', detail: 'rank candidates, re-capture and check the winner', model: 'claude-haiku-5-5' },
    { title: 'Judge', detail: 'rubric score and gap list', model: 'claude-sonnet-5-5' },
    { title: 'Finish', detail: 'best branch, run log, optional bake-off' },
  ],
}

// A re-implementation of dream-loop's Pro workflow (github.com/achimala/dream-loop):
// dream a target screenshot, build toward it, have a fresh judge score the live
// screenshot against the target, feed the gaps back, repeat until the score clears the
// bar or progress stalls.
//
// A frontier model running that loop stops after a few rounds because each pass is
// expensive. This version spends what Sonnet 5.5 and Haiku 5.5 save on search: each
// round runs several Sonnet builders in parallel git worktrees, a Haiku panel picks the
// best candidate, and a Sonnet judge compares it with the current best. A candidate is
// kept when the judge rules it no further from the target overall and it scores within
// half a point of the best score so far. Every candidate stays on its own branch, so any
// round can be inspected or resumed from.
//
// All image generation (the target, asset cutouts, textures, skyboxes) goes through the
// Codex CLI's built-in image tool, so no image API key is needed. 3D assets are made by
// object type: organic shapes through fal.ai image-to-3D (only if FAL_KEY or FAL_API_KEY is
// set), architecture and hard-edged pieces in Blender.
//
// Supports static web apps (index.html served from a folder), which covers the usual
// Three.js / WebGL demo.
//
// args (a bare string is treated as { request }):
//   request        required. The build prompt.
//   repo           project root (default: the session's working directory). Must be the top
//                  level of a clean git repo, or an empty or missing folder.
//   appDir         app folder inside the repo (default '.')
//   target         image to build toward; skips the dream step. For a fair bake-off, pass the rival run's target.
//   codexModel     model that drives Codex's image tool ('gpt-6-astra'); if Codex refuses it, the account default runs
//   width          builders per round, max 8 (3)        firstWidth  builders for the first build (1)
//   maxRounds      (12)                                 doneScore   judge score that ends the run (9 of 10)
//   fps            frame-rate floor, 0 to skip (55)     viewport    capture size [w, h] ([1280, 720])
//   firstAssetCap  image-to-3D jobs per first-build pass (12)
//   assetCap       image-to-3D jobs per later pass (3)
//   compareWith    screenshot from another run (e.g. Astra); adds a blind A/B judgment at the end
//   rankerModel    model for the selection panel (Haiku 5.5)
//   tag            branch and folder namespace; change it to run again in the same repo ('dream')

const SONNET = 'claude-sonnet-5-5' // if your gateway rejects pinned IDs, use 'sonnet' and 'haiku'
const HAIKU = 'claude-haiku-5-5'

const A = typeof args === 'string' ? { request: args } : { ...args }
if (!A.request) throw new Error('args.request is required: the build prompt')
const TAG = A.tag ?? 'dream'
const APP = A.appDir ?? '.'
const WIDTH = Math.min(A.width ?? 3, 8) // the ranking panel labels candidates A-H
const FIRST_WIDTH = Math.min(A.firstWidth ?? 1, 8) // first builds generate most assets; parallel first builds multiply that spend
const MAX_ROUNDS = A.maxRounds ?? 12
const DONE = A.doneScore ?? 9 // upstream stops at 8; cheap rounds let the loop push further
const FPS = A.fps ?? 55 // headless Chromium paces frames at 60 Hz, so a floor of 60 fails on one dropped frame
const FIRST_ASSETS = A.firstAssetCap ?? 12
const ASSET_CAP = A.assetCap ?? 3
const RANKER = A.rankerModel ?? HAIKU
const CODEX_MODEL = A.codexModel ?? 'gpt-6-astra'
const TOLERANCE = 0.5 // absolute scores drift between judge calls; the judge's side-by-side regressed flag is the main gate
const RESERVE = 200_000, FINISH_RESERVE = A.compareWith ? 100_000 : 30_000 // output tokens, only used with a "+Nk" budget
const [VW, VH] = A.viewport ?? [1280, 720]
const LETTERS = 'ABCDEFGH'
const KEY_NAMES = ['FAL_KEY', 'FAL_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY']
const KEYS = KEY_NAMES.join(', ')

const S = { type: 'string' }, N = { type: 'number' }, B = { type: 'boolean' }
const obj = props => ({ type: 'object', properties: props, required: Object.keys(props) })
const SETUP = obj({ ok: B, reason: S, repo: S, width: N, height: N, target: S, baselineShot: S, baselineFps: N, gpu: S, fpsReliable: B, codex: B, blender: S })
const DREAM = obj({ ok: B, reason: S, path: S, prompt: S, generator: S })
const BUILD = obj({ ok: B, summary: S })
const CAPTURE = obj({ ok: B, screenshot: S, fps: N, errors: { type: 'array', items: S }, leftovers: B, leak: B })
const VERDICT = obj({
  composition: N, lighting: N, materials: N, details: N,
  regressed: B, repeatedTopGap: B, regressions: S,
  gaps: { type: 'array', items: obj({ area: S, gap: S, fix: S }) },
})
const AB = { type: 'string', enum: ['A', 'B'] }
const PAIR = obj({ closer: AB, better: AB, why: S })

const clamp = (x, hi) => Math.max(0, Math.min(hi, Number(x) || 0))
const scoreOf = v => Math.round((clamp(v.composition, 3) + clamp(v.lighting, 3) + clamp(v.materials, 3) + clamp(v.details, 1)) * 100) / 100

// agent() throws once a "+Nk" budget is spent. Treat that like any failed agent so the
// loop's own checks end the run and the wrap-up still happens.
const call = (prompt, opts) => agent(prompt, opts).catch(e => { log(`${opts.label}: ${e.message}`); return null })

// The one piece of infrastructure every agent shares. Written verbatim by setup so that
// every screenshot in a run, and across runs, comes from the same renderer settings.
const CAPTURE_JS = `// node capture.mjs <appDir> <out.png> <width> <height>
// Serves appDir as static files, renders it in Chromium, prints one JSON line.
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { chromium } from 'playwright'

const [dir, out, w, h] = process.argv.slice(2)
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
const browser = await chromium.launch({ channel: 'chromium', args: ['--ignore-gpu-blocklist', '--enable-gpu-rasterization'] })
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
  console.log(JSON.stringify({
    ok: errors.length === 0,
    screenshot: path.resolve(out),
    fps: Math.round(stats.fps),
    gpu: stats.gpu,
    fpsReliable: !/swiftshader|llvmpipe|software|no-webgl/i.test(stats.gpu),
    errors: errors.slice(0, 20),
  }))
} finally {
  await browser.close()
  server.close()
}
`

// Every image in a run is made through this helper, so the dream step and all builders
// call Codex the same way. Tested live, including three concurrent runs.
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
2. Capture harness: write the script between the markers verbatim to <repo>/.dream-loop/harness/capture.mjs. Then in <repo>/.dream-loop/harness run npm init -y, npm install playwright, and npx playwright install chromium, skipping whatever is already installed.
<<<capture.mjs
${CAPTURE_JS}
capture.mjs>>>
3. Smoke test: write <repo>/.dream-loop/harness/smoke/index.html, a page whose full-window WebGL canvas clears to solid orange and then sets window.__dreamReady = true. Run node "<repo>/.dream-loop/harness/capture.mjs" "<repo>/.dream-loop/harness/smoke" "<repo>/.dream-loop/harness/smoke/out.png" ${VW} ${VH}. It must print ok=true and out.png must be orange. If Chromium fails to launch or gpu names a software renderer (SwiftShader, llvmpipe), you may change only the chromium.launch(...) options, for example adding --use-angle=metal on macOS. If hardware rendering cannot be made to work, keep a working software setup. Return gpu and fpsReliable from the final smoke run.
4. Image helper and tools: write the script between the markers verbatim to <repo>/.dream-loop/harness/imagegen.mjs. Do not run it. Set codex=true if the Codex CLI is found (command -v codex, then again with PATH="/opt/homebrew/bin:$PATH") and codex login status reports a login; otherwise codex=false. Set blender to the absolute path of the Blender executable if one exists (command -v blender, or /Applications/Blender.app/Contents/MacOS/Blender), else "".
<<<imagegen.mjs
${IMAGEGEN_JS}
imagegen.mjs>>>
5. Target: ${A.target
    ? `copy ${A.target} to <repo>/.dream-loop/runs/${TAG}/target.png, converting it to PNG if needed, and return that path as target. Return width=${VW} and the height that matches the target's aspect ratio.`
    : `none was supplied. Return target="" and width=${VW}, height=${VH}.`}
6. Baseline: if <repo>/${APP}/index.html exists, this run improves an existing product. Capture it to <repo>/.dream-loop/runs/${TAG}/shots/r0.png at the returned width and height, and return that path as baselineShot and its fps as baselineFps. Otherwise return baselineShot="" and baselineFps=0.`,
  { model: SONNET, effort: 'medium', label: 'setup', phase: 'Setup', schema: SETUP })
if (!setup?.ok) throw new Error(`Setup stopped: ${setup?.reason ?? 'no result'}`)

const repo = setup.repo
const RUN = `${repo}/.dream-loop/runs/${TAG}`
const vw = setup.width, vh = setup.height
const capture = (dir, out) => `node "${repo}/.dream-loop/harness/capture.mjs" "${dir}" "${out}" ${vw} ${vh}`
// Shell lines that print the name of each set API key whose value appears in a git log range. Never prints a value.
const leakScan = range => KEY_NAMES.map(k => `[ -n "$${k}" ] && git -C "${repo}" log -p ${range} | grep -qF -- "$${k}" && echo ${k}`).join('\n')
if (!setup.fpsReliable) log(`Captures render in software (${setup.gpu}), so measured FPS means nothing; the FPS floor is not enforced`)
if (!setup.codex && !setup.target) throw new Error('No target image: the Codex CLI is missing or not logged in. Run codex login, or pass args.target.')
if (!setup.codex) log('Codex CLI is missing or not logged in: builders cannot generate textures or asset cutouts this run')
// Codex needs network access and writes its state under ~/.codex, both of which the sandbox blocks.
const imagegen = (out, msg, inputs = []) => `DREAM_CODEX_MODEL=${CODEX_MODEL} node "${repo}/.dream-loop/harness/imagegen.mjs" "${out}" "${msg}"${inputs.map(f => ` "${f}"`).join('')}`
const IMAGEGEN_RULES = 'Run it outside the sandbox (it needs network access and writes Codex state under ~/.codex), with the longest command timeout, and use absolute paths rather than $TMPDIR. It prints one JSON line listing the images it saved. Each image takes about a minute, so put up to 6 images in one request rather than calling it once per image. If it reports a rate limit, wait a minute and retry.'

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

// ---------------------------------------------------------------- agents

const critique = (shot, fps, errors, prev, label) => call(`You judge how close a live product screenshot is to a target image.

Target: ${target}
Current product: ${shot}
${prev?.verdict ? `Previous product: ${prev.shot}\nPrevious verdict: ${JSON.stringify(prev.verdict)}` : ''}
Measured frame rate: ${fps} fps${FPS ? ` (floor ${FPS})` : ''}.${errors?.length ? `\nRuntime errors: ${errors.join('; ')}` : ''}

Score each category; fractions are fine:
- composition 0-3: camera, framing, layout; position and scale of every major element
- lighting 0-3: palette, exposure, shadows, contrast, atmosphere, reflections, glows; overall brightness against the target
- materials 0-3: texture, roughness, translucency, and wetness of every surface; anything blocky, plasticky, too smooth, or fake unless the target looks that way too
- details 0-1: every small element, compared with a fine-toothed comb

List every gap between the product and a perfect score, ordered by impact. Each gap names what in the image causes the mismatch and how to fix it. "The tree looks fake" is not acceptable; "the canopy is one smooth sphere with no leaf clusters or alpha-cut foliage" is. If a model, the lighting, or the whole scene needs to be redone, say so. The goal is for the two images to be identical.

${prev?.verdict
    ? 'Compare the current product with the previous one side by side. Set regressed=true only if the current product is further from the target overall; a large change that loses some details but gets closer overall is not a regression. Either way, list everything that got worse in regressions. Stay consistent with the previous verdict, but do not raise scores out of courtesy. Set repeatedTopGap=true if your top gap is substantially the same as the previous verdict\'s top gap.'
    : 'This is the first verdict: set regressed=false, repeatedTopGap=false, regressions="".'}`,
  { model: SONNET, effort: 'high', label, phase: 'Judge', schema: VERDICT })

const directive = mode => ({
  normal: '',
  bold: 'Scores have stalled and incremental tweaks are not closing the gap. Rethink your area from first principles and make a change big enough to move the score by several points.',
  optimize: `The judge is satisfied with the visuals, but the product runs at ${best.fps} fps against a floor of ${FPS}. Optimize: lossless wins first, then changes with minimal visual impact. Do not trade away visual quality.`,
}[mode])

const LENSES = {
  first: ['build a complete first version that matches the target as closely as you can'],
  normal: [
    'work the gap list top-down and fully fix the highest-impact gaps before smaller ones',
    'address every gap on the list in one pass, favoring breadth over depth',
    'find the single biggest structural reason the product does not look like the target (camera, lighting model, asset quality, material pipeline) and rebuild that part properly',
  ],
  bold: [
    'composition: camera, framing, scene layout, and the scale and placement of major elements',
    'lighting: light rig, shadows, exposure, atmosphere, reflections, and post-processing',
    'assets and materials: replace weak models, textures, and shaders with better-sourced ones',
  ],
  optimize: ['profile first, then cut the most expensive per-frame work'],
}

// How builders make 3D assets. Image-to-3D suits organic shapes; Blender suits architecture and hard-edged pieces.
const I23D = "image-to-3D through fal.ai when FAL_KEY or FAL_API_KEY is set: first use the image helper, with the target attached, to cut a clean image of the object alone on a plain or transparent background with its hidden parts completed, so the model matches the target instead of being reimagined; then submit it to a strong image-to-3D model for large or important objects or a cheaper one for small props. Check fal's docs for current endpoints and parameters. Jobs are async: submit them together and poll. Models come back static, so a character that has to move needs rigging in Blender or animation in code"
const BLENDER = setup.blender && `model them in Blender through its Python API ("${setup.blender}" --background --python <script>), split into parts by material so textures tile cleanly, and check a rendered preview before exporting to GLB`
const ORGANIC = setup.codex
  ? `${I23D}. Without a fal key, ${BLENDER ? 'model them in Blender as described in the next item' : 'build them in code'}`
  : `${BLENDER || 'build them in code'} (image-to-3D needs image cutouts, which are unavailable this run)`
const HARD = BLENDER || 'build them in code (Blender is not installed)'

const assets = c => `${setup.codex
  ? `Images: make every image you need with the image helper, which drives the Codex CLI's built-in image tool: asset cutouts, textures, normal and roughness maps, skyboxes, decals. Use it as often as the work needs. Never use an image API key, and never use fal for images.
   ${imagegen(`${c.wt}/${APP}/<folder for these images>`, `${RUN}/requests/${c.id}-<n>.txt`, ['<input image>', '...'])}
Write each request to its message file first, naming every image to make with its file name, size or aspect ratio, and whether the background must be transparent. Attach the target as an input image whenever the result has to match it. ${IMAGEGEN_RULES}`
  : 'Image generation is unavailable this run, so build textures in code.'}


Choose how to make each 3D asset by what it is, not by what is fastest:
- Organic or irregular objects (characters, creatures, trees and plants, statues, rubble, detailed props): ${ORGANIC}.
- Architecture and hard-edged objects (walls, arches, columns, floors, stairs, furniture, repeated modular pieces), and anything that needs exact proportions, tiling textures, or a tight polygon budget: ${HARD}.
- If the request allows downloads, a good free model can replace either route.
- Build in code only simple geometry (ground planes, water surfaces, particles) or objects that neither route can produce.
In every case, texture assets with generated images rather than procedural noise or flat colors when images are available, and correct the orientation and scale of imported models.`

const buildPrompt = (c, mode, lens, fresh, solo) => `You are a builder in a dream-loop run: make the live product match a target screenshot.

Workspace: run git -C "${repo}" worktree add "${c.wt}" -b ${c.branch} ${best.branch}. If that branch or worktree already exists from an interrupted attempt, remove both (git worktree remove --force, then git branch -D) and run the command again. If git reports a lock, wait a few seconds and retry. Work only inside ${c.wt}.

The app lives at ${c.wt}/${APP} and is served as static files from that folder, with index.html at its root. Every round starts from a fresh checkout of a branch, and untracked files such as node_modules do not carry over, so anything the app loads at runtime must be committed or come from a CDN. If you use npm, create package.json in the app folder first. Once the scene has loaded its assets and drawn a frame, set window.__dreamReady = true.

User request: ${A.request}

Target image: ${target}
${best.shot ? `Current product screenshot: ${best.shot}` : 'There is no product yet.'}
Open these images and study them before writing code.
${best.verdict ? `\nJudge's verdict on the current product (${best.score}/10), gaps ordered by impact:\n${JSON.stringify(best.verdict.gaps, null, 1)}` : ''}
${best.errors?.length ? `Runtime errors in the current product: ${best.errors.join('; ')}` : ''}
${rejected ? `Last round's best attempt was discarded. Judge's note: ${rejected}` : ''}

${directive(mode)}
Your approach this pass: ${lens}.${solo ? '' : ' Other builders are working on the same product in parallel with different approaches; only the best result is kept.'}

Close every gap you can between product and target: composition, layout, lighting, materials, texturing, reflections, fine details, shaders, animation, character behavior, controls.${FPS ? ` Keep the frame rate at or above ${FPS} fps.` : ''}

${assets(c)}
Spend limit for this pass: at most ${fresh ? FIRST_ASSETS : ASSET_CAP} new image-to-3D jobs; reuse committed models otherwise. Read API keys from the environment in the shell command that uses them. Never write a key into any file, script, or client code. Keep generated models and textures inside the app folder and commit them.

Before finishing, run:
${capture(`${c.wt}/${APP}`, c.shot)}
Fix whatever it reports: console errors, failed requests, a blank or black frame, assets at the wrong orientation or scale. ${solo ? 'Nothing else renders while you work, so its fps reading is reliable; use it to measure your changes.' : 'Its fps is unreliable because other builders render at the same time; ignore it.'} Do not grade your visuals against the target; an independent judge does that. Commit all work to ${c.branch}, then return.`

async function rank(cands, round) {
  if (cands.length === 1) return { pick: cands[0], points: { [cands[0].id]: 0 } }
  const n = cands.length
  const schema = obj({ order: { type: 'array', items: { type: 'string', enum: [...LETTERS.slice(0, n)] } } })
  const rankings = await parallel(cands.map((_, shift) => () => {
    const order = cands.map((_, p) => (p + shift) % n) // across the panel, each candidate sits in each position once
    const list = order.map((ci, p) => `${LETTERS[p]}: ${cands[ci].shot}`).join('\n')
    return call(`Target image: ${target}\n\nCandidate screenshots:\n${list}\n\nOpen the target and every candidate. Rank all ${n} candidates from closest to the target to furthest, weighing composition, lighting, materials, and fine detail together. A blank, black, or broken frame ranks last. Return the letters in order.`,
      { model: RANKER, effort: 'medium', label: `rank r${round} #${shift + 1}`, phase: 'Select', schema })
      .then(v => v && [...new Set(v.order)].map(l => order[LETTERS.indexOf(l)]))
  }))
  const cast = rankings.filter(Boolean)
  if (!cast.length) log(`r${round}: every ranker failed; taking ${cands[0].id}`)
  const points = cands.map(() => 0)
  for (const r of cast) r.forEach((ci, pos) => { points[ci] += n - 1 - pos })
  return { pick: cands[points.indexOf(Math.max(...points))], points: Object.fromEntries(cands.map((c, i) => [c.id, points[i]])) }
}

const verify = (c, base, round) => call(`Re-capture the winning candidate of a dream-loop round on its own, check it, then tidy up.
1. If git -C "${c.wt}" status --porcelain shows changes, commit them on ${c.branch} with message "dream-loop: uncommitted leftovers" and set leftovers=true; otherwise leftovers=false.
2. Secrets: run these lines exactly as written. They print the name of any API key whose value appears in this branch's new commits, and never print a value.
${leakScan(`${base}..${c.branch}`)}
   If any name was printed, set leak=true and add "secret committed: <name>" to errors; otherwise leak=false.
3. Run: ${capture(`${c.wt}/${APP}`, `${RUN}/shots/r${round}-pick.png`)}
   Nothing else is rendering now, so this run's fps is the one that counts.
4. Remove every worktree under ${RUN}/wt/ with git -C "${repo}" worktree remove --force <path>. Their branches stay.
Return the fields printed in step 3 plus leftovers and leak. If the capture command itself failed, return ok=false, screenshot="", fps=0, and the error in errors.`,
  { model: HAIKU, effort: 'low', label: `capture ${c.id}`, phase: 'Select', schema: CAPTURE })

// ---------------------------------------------------------------- loop

let best = { branch: `${TAG}/r0`, shot: setup.baselineShot, fps: setup.baselineFps, errors: [], score: -1, verdict: null }
if (best.shot) {
  const v = await critique(best.shot, best.fps, [], null, 'judge baseline')
  if (v) best = { ...best, verdict: v, score: scoreOf(v) }
}
const fpsOk = () => !FPS || !setup.fpsReliable || best.fps >= FPS
log(`Target ${target}; up to ${MAX_ROUNDS} rounds of ${WIDTH} builders; stop at ${DONE}/10${FPS && setup.fpsReliable ? ` and ${FPS} fps` : ''}. Image-to-3D jobs per builder pass: ${FIRST_ASSETS} on a first build, ${ASSET_CAP} after${setup.codex ? '' : '; no image generation'}`)

const history = []
const bests = [] // best score after each round, for stall detection
let peak = { score: best.score, branch: best.branch } // the keep rule's tolerance is measured from here, so scores cannot slide
let mode = best.shot && best.score >= DONE ? 'optimize' : 'normal', rejected = ''
let dead = 0 // consecutive rounds that produced no verdict
let status = best.shot && best.score >= DONE && fpsOk() ? 'done' : null
let roundCost = RESERVE, spentAtStart = budget.spent(), lastK = 0
const outOfBudget = () => budget.total && budget.remaining() <= 0

for (let round = 1; !status && round <= MAX_ROUNDS; round++) {
  const fresh = !best.shot
  const k = fresh ? FIRST_WIDTH : mode === 'optimize' ? 1 : WIDTH
  if (lastK) roundCost = Math.max(RESERVE, (budget.spent() - spentAtStart) / lastK * k) // scale by builder count
  if (budget.total && budget.remaining() < roundCost + FINISH_RESERVE) { status = 'budget'; break }
  spentAtStart = budget.spent()
  lastK = k

  const lenses = LENSES[fresh ? 'first' : mode]
  const entry = { round, mode, of: k }
  history.push(entry)
  const skip = why => { entry.note = why; log(`r${round}: ${why}`); bests.push(best.score); return ++dead >= 2 }

  const slots = Array.from({ length: k }, (_, i) => {
    const id = `r${round}-c${i + 1}`
    return { id, branch: `${TAG}/${id}`, wt: `${RUN}/wt/${id}`, shot: `${RUN}/shots/${id}.png` }
  })
  const built = await parallel(slots.map((c, i) => () =>
    call(buildPrompt(c, mode, lenses[i % lenses.length], fresh, k === 1),
      { model: SONNET, effort: fresh || mode === 'bold' ? 'high' : 'medium', label: `build ${c.id}`, phase: 'Build', schema: BUILD })
      .then(b => b?.ok ? { ...c, summary: b.summary } : null)))
  const cands = built.filter(Boolean)
  entry.built = cands.length
  if (!cands.length) { if (skip('every builder failed')) { status = outOfBudget() ? 'budget' : 'failing'; break } continue }

  const { pick, points } = await rank(cands, round)
  Object.assign(entry, { pick: pick.id, points, summary: pick.summary })
  const cap = await verify(pick, best.branch, round)
  if (cap?.leak) { if (skip(`${pick.branch} committed an API key and was discarded`)) { status = outOfBudget() ? 'budget' : 'failing'; break } continue }
  if (!cap?.screenshot) { if (skip(`re-capture of ${pick.id} failed`)) { status = outOfBudget() ? 'budget' : 'failing'; break } continue }

  const v = await critique(cap.screenshot, cap.fps, cap.errors, best, `judge ${pick.id}`)
  if (!v) { if (skip('judge failed')) { status = outOfBudget() ? 'budget' : 'failing'; break } continue }
  dead = 0
  const score = scoreOf(v)
  const prevScore = best.score
  const accepted = mode === 'optimize'
    ? !v.regressed && score >= DONE && cap.fps > best.fps
    : !v.regressed && score >= peak.score - TOLERANCE
  const gained = accepted && (mode === 'optimize' || score > prevScore)
  Object.assign(entry, { score, fps: cap.fps, regressed: v.regressed, accepted, leftovers: cap.leftovers })
  if (accepted) {
    best = { branch: pick.branch, shot: cap.screenshot, fps: cap.fps, errors: cap.errors, score, verdict: v }
    rejected = ''
    if (score > peak.score) peak = { score, branch: pick.branch }
  } else {
    rejected = v.regressions || (mode === 'optimize'
      ? `it ran at ${cap.fps} fps against ${best.fps} and scored ${score}`
      : `it scored ${score} against ${prevScore}`)
  }
  bests.push(best.score)
  log(`r${round} ${mode}: picked ${pick.id} of ${cands.length}, judge ${score}, ${accepted ? 'kept' : 'discarded'}; best ${best.score} at ${best.fps} fps`)

  if (best.score >= DONE && fpsOk()) { status = 'done'; break }
  // Stall rules: a bold or optimize round that fails ends the run. Otherwise go bold
  // when the best score has gained less than a point in two rounds, or the judge names
  // the same top gap twice.
  if (mode !== 'normal' && !gained) { status = 'stalled'; break }
  if (best.score >= DONE) { mode = 'optimize'; continue }
  const twoAgo = bests.length >= 3 ? bests[bests.length - 3] : -Infinity
  mode = best.score - twoAgo < 1 || v.repeatedTopGap ? 'bold' : 'normal'
}
status ??= 'max-rounds'

// ---------------------------------------------------------------- finish

let bakeoff = null
if (A.compareWith && status === 'budget') log('Skipping the bake-off: the remaining budget is kept for wrap-up')
if (A.compareWith && best.shot && status !== 'budget') {
  // Neutral file names, so the judges cannot tell which image came from this run.
  const pair = [`${RUN}/bakeoff/p.png`, `${RUN}/bakeoff/q.png`] // p is ours
  const copied = await call(`Copy ${best.shot} to ${pair[0]} and ${A.compareWith} to ${pair[1]}, converting to PNG if needed. Return ok=true once both files exist.`,
    { model: HAIKU, effort: 'low', label: 'bake-off prep', phase: 'Finish', schema: obj({ ok: B }) })
  if (copied?.ok) {
    const votes = await parallel([SONNET, HAIKU].flatMap(model => [0, 1].map(flip => () =>
      call(`Target image: ${target}\nAttempt A: ${pair[flip]}\nAttempt B: ${pair[1 - flip]}\nRequest both attempts were built from: ${A.request}\n\nOpen all three images. Which attempt is closer to the target, and which better delivers what the request asks for visually? Judge only what you see.`,
        { model, effort: 'high', label: `bake-off ${model === SONNET ? 'sonnet' : 'haiku'} ${flip ? 'BA' : 'AB'}`, phase: 'Finish', schema: PAIR })
        .then(v => v && {
          judge: model,
          closer: (v.closer === 'A') === (flip === 0) ? 'ours' : 'rival',
          better: (v.better === 'A') === (flip === 0) ? 'ours' : 'rival',
          why: v.why,
        }))))
    const cast = votes.filter(Boolean)
    bakeoff = {
      closer: `${cast.filter(x => x.closer === 'ours').length} of ${cast.length} for ours`,
      better: `${cast.filter(x => x.better === 'ours').length} of ${cast.length} for ours`,
      votes: cast,
    }
  }
}

const result = {
  status,
  score: best.score,
  fps: best.fps,
  fpsMeasured: setup.fpsReliable,
  branch: best.shot ? `${TAG}/best` : null,
  checkout: best.shot ? `${RUN}/best` : null,
  screenshot: best.shot,
  peak, // highest judge score seen; can sit up to TOLERANCE above the final score
  target,
  dreamGenerator,
  dreamPrompt,
  rounds: history.length,
  topGaps: (best.verdict?.gaps ?? []).slice(0, 5),
  bakeoff,
  history,
}

const fin = await call(`Wrap up a dream-loop run in ${repo}. Do not check out another branch in the main checkout or change its files; work only with git refs, worktrees, and files under ${repo}/.dream-loop.
1. Remove any worktrees under ${RUN}/wt/ and any worktree at ${RUN}/best with git -C "${repo}" worktree remove --force <path>.
2. ${best.shot ? `git -C "${repo}" branch -f ${TAG}/best ${best.branch}, then git -C "${repo}" worktree add "${RUN}/best" ${TAG}/best. Set branchCreated=true if both succeed.` : 'No candidate was kept; skip this step and set branchCreated=false.'}
3. Secrets: list branches with git -C "${repo}" for-each-ref --format='%(refname:short)' refs/heads/${TAG}/. For each one, run these lines with BRANCH replaced by its name. They print key names only, never values. Return every branch for which a name was printed as leaks.
${leakScan(`${TAG}/r0..BRANCH`)}
4. Write the JSON between the markers to ${RUN}/run.json using a quoted heredoc so nothing is interpolated, and write {"leaks": [...]} from step 3 to ${RUN}/leaks.json. Confirm both parse with node -e "JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))" <file>. Return ok=true only if they do.
<<<json
${JSON.stringify(result)}
json>>>`,
  { model: HAIKU, effort: 'low', label: 'finish', phase: 'Finish', schema: obj({ ok: B, branchCreated: B, leaks: { type: 'array', items: S } }) })

if (!fin?.branchCreated) Object.assign(result, { branch: null, checkout: null })
result.leaks = fin?.leaks ?? null
result.logWritten = !!fin?.ok
if (result.leaks?.length) log(`API key values found in ${result.leaks.join(', ')}; delete those branches before pushing anything`)
return result
