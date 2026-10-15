// Local fal.ai relay for one dream-loop-fast run.
// Start it with the key injected by 1Password, so the key lives only in this process:
//   FAL_KEY='op://vault/item/field' op run -- node relay.mjs
// It forwards requests to queue.fal.run only, adding the key, and rewrites the queue URLs fal
// returns to point back here, so callers never need the key. Paid submissions are capped for the
// whole run, and each one is appended to the ledger (no key, no payloads).
import http from 'node:http'
import fs from 'node:fs'

const KEY = process.env.FAL_KEY
const PORT = Number(process.env.RELAY_PORT || 4791)
const CAP = Number(process.env.RELAY_CAP || 9)
const LEDGER = process.env.RELAY_LEDGER || ''
if (!KEY) { console.error('FAL_KEY is missing; start the relay through op run'); process.exit(1) }

const SELF = 'http://127.0.0.1:' + PORT
let used = 0
const record = entry => { if (LEDGER) fs.appendFileSync(LEDGER, JSON.stringify({ at: new Date().toISOString(), ...entry }) + '\n') }
const reply = (res, status, obj) => { res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify(obj)) }

http.createServer(async (req, res) => {
  const url = new URL(req.url, SELF)
  if (url.pathname === '/_status') return reply(res, 200, { used, cap: CAP })
  const chunks = []
  for await (const c of req) chunks.push(c)
  const body = Buffer.concat(chunks)
  // A submission is a POST to a model endpoint; status, result, and cancel calls live under /requests/.
  const submit = req.method === 'POST' && !url.pathname.includes('/requests/')
  if (submit) {
    if (used >= CAP) {
      record({ refused: url.pathname, used })
      return reply(res, 429, { detail: `This run's fal budget of ${CAP} image-to-3D jobs is used up. Model the object in Blender or reuse a committed model.` })
    }
    used++ // reserved before forwarding so concurrent submissions cannot overshoot the cap
  }
  try {
    const r = await fetch('https://queue.fal.run' + url.pathname + url.search, {
      method: req.method,
      headers: { Authorization: 'Key ' + KEY, ...(body.length ? { 'Content-Type': req.headers['content-type'] || 'application/json' } : {}) },
      body: body.length ? body : undefined,
      redirect: 'error',
    })
    const text = await r.text()
    if (submit) {
      if (!r.ok) used--
      record({ submit: url.pathname, status: r.status, used })
    }
    res.writeHead(r.status, { 'content-type': r.headers.get('content-type') || 'application/json' })
    res.end(text.replaceAll('https://queue.fal.run', SELF))
  } catch (e) {
    if (submit) used--
    reply(res, 502, { detail: 'relay could not reach fal: ' + e.message })
  }
}).listen(PORT, '127.0.0.1', () => console.log(`fal relay listening on ${SELF}, cap ${CAP} jobs`))
