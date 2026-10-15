# Gemini web private API

How `scripts/gemini_web.py` talks to gemini.google.com, and how to repair it.
Captured October 2026 against web build `boq_gemini-web-uiserver_20261012`.

## Requests

All requests carry the Google cookies saved from the Chrome profile
(`__Secure-1PSID`, `__Secure-1PSIDTS` and the rest of the `gemini.google.com`
jar).

1. `GET https://gemini.google.com/app` and read three values from the page's
   embedded config: `SNlM0e` (the `at` anti-forgery token), `cfb2h` (build
   label, sent as `bl`) and `FdrFJe` (session id, sent as `f.sid`). A missing
   `SNlM0e` means Google rejected the cookies.
2. `POST /_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate?bl=…&f.sid=…&hl=en&rt=c`
   as a form with `at` and
   `f.req = [null, json([[prompt,0,null,null,null,null,0], ["en"], ["","",""]])]`,
   plus headers `X-Same-Domain: 1` and
   `x-goog-ext-525001261-jspb: [1,null,null,null,"<model id>",null,null,0,[4]]`.
   The browser also sends a long BotGuard token and a dozen more fields; image
   generation works without them.
3. The response is `)]}'` followed by length-prefixed lines of
   `[["wrb.fr", null, "<json payload>"]]`. The last payload with a non-empty fifth
   element holds the reply. Image URLs match
   `https://lh3.googleusercontent.com/gg-dl/…`; the image model's name
   ("Nano Banana …") appears next to the model id.
4. `GET <gg-dl url>=s0?alr=yes` answers with the next URL as `text/plain`.
   Follow until the body is the image. The middle hop, on
   `work.fife.usercontent.google.com`, needs the Google cookies; the
   `googleusercontent.com` hops work without them. The script sends cookies only
   to `*.google.com` hosts, as a browser does. `s0` gives original resolution
   (1376–1408 px wide); the web UI shows `s1024`.

Model ids come from `POST /_/BardChatUi/data/batchexecute?rpcids=otAQ7b` with
`f.req=[[["otAQ7b","[1]",null,"generic"]]]`. Element 15 of the payload lists
`[id, name, …]` for each chat model.

Known quirk: when Gemini replies in text instead of drawing, StreamGenerate
sometimes takes several minutes to finish. The script gives up at two.

A 400, 401 or 403 from either POST means the session was rejected. The script
then reloads Gemini in the hidden profile browser to renew the cookies and
retries once.

## Repairing

1. Run `uv run scripts/gemini_web.py --login` and retry. Most failures are an
   expired sign-in.
2. Record what the web app sends now:
   `uv run scripts/capture_traffic.py "$TMPDIR/gemini.har"`. It drives one image
   prompt through the real UI and saves a HAR and a screenshot beside it.
3. Compare the StreamGenerate request and response in the HAR with the shapes
   above, update the script, and confirm it saves an image. Delete the HAR
   afterwards: it contains session cookies.
