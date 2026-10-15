# /// script
# requires-python = ">=3.10"
# dependencies = ["patchright>=1.50"]
# ///
"""Generate images with a signed-in Gemini web account over its private HTTP API.

  uv run gemini_web.py --login                       # one-time: sign in with a visible browser
  uv run gemini_web.py "a red apple" -o apple.jpg    # generate
  uv run gemini_web.py --list-models

Chrome (via patchright) is used only to sign in and to refresh cookies when Google
rejects the saved ones; generation itself is two plain HTTPS requests.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOME = Path(os.environ.get("GEMINI_WEB_HOME", Path.home() / ".local/share/generate-image"))
PROFILE = HOME / "gemini-profile"
COOKIES = HOME / "gemini-cookies.json"
BASE = "https://gemini.google.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"


class AuthError(Exception):
    pass


def open_profile(headless: bool):
    from patchright.sync_api import sync_playwright

    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(str(PROFILE), channel="chrome", headless=headless, no_viewport=True)
    return pw, ctx, (ctx.pages[0] if ctx.pages else ctx.new_page())


def login() -> None:
    PROFILE.mkdir(parents=True, exist_ok=True)
    pw, ctx, page = open_profile(headless=False)
    page.goto(f"{BASE}/app")
    print(f"Profile: {PROFILE}\nSign in to Google in the browser window, then close it.", file=sys.stderr)
    page.wait_for_event("close", timeout=0)
    ctx.close()
    pw.stop()
    refresh_cookies()
    print("Signed in.", file=sys.stderr)


def refresh_cookies() -> dict:
    """Load Gemini in the profile so Chrome rotates its Google cookies, then save them."""
    if not PROFILE.exists():
        raise AuthError("no browser profile; run with --login")
    pw, ctx, page = open_profile(headless=True)
    page.goto(f"{BASE}/app", wait_until="domcontentloaded")
    jar = {c["name"]: c["value"] for c in ctx.cookies(BASE)}
    ctx.close()
    pw.stop()
    if "__Secure-1PSID" not in jar:
        raise AuthError("the profile is signed out; run with --login")
    fd = os.open(COOKIES, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        os.fchmod(fd, 0o600)  # also tighten a file that already existed
        json.dump(jar, f)
    return jar


def saved_cookies() -> dict:
    try:
        return json.loads(COOKIES.read_text())
    except (OSError, ValueError):
        return refresh_cookies()


def is_google(url: str) -> bool:
    host = urllib.parse.urlsplit(url).hostname or ""
    return host == "google.com" or host.endswith(".google.com")


class ScopedRedirect(urllib.request.HTTPRedirectHandler):
    """Follow redirects like a browser would: Google cookies never leave *.google.com."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and not is_google(newurl):
            new.remove_header("Cookie")
        return new


opener = urllib.request.build_opener(ScopedRedirect)


def http(url: str, jar: dict, form: dict | None = None, headers: dict | None = None, timeout: int = 60) -> str | bytes:
    h = {"User-Agent": UA, **(headers or {})}
    if is_google(url):
        h["Cookie"] = "; ".join(f"{k}={v}" for k, v in jar.items())
    data = None
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        h |= {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8", "X-Same-Domain": "1",
              "Origin": BASE, "Referer": f"{BASE}/"}
    deadline = time.monotonic() + timeout
    with opener.open(urllib.request.Request(url, data=data, headers=h), timeout=timeout) as r:
        body = b""
        while chunk := r.read1(1 << 16):  # enforce a total deadline, not just a per-read one
            body += chunk
            if time.monotonic() > deadline:
                raise TimeoutError(f"response took longer than {timeout}s")
        return body.decode() if r.headers.get_content_type().startswith(("text/", "application/json")) else body


class Gemini:
    def __init__(self, jar: dict):
        self.jar = jar
        page = http(f"{BASE}/app", jar)
        tokens = {k: re.search(rf'"{k}":"(.*?)"', page) for k in ("SNlM0e", "cfb2h", "FdrFJe")}
        if not tokens["SNlM0e"]:
            raise AuthError("Google rejected the saved cookies")
        self.at, self.bl, self.sid = (m.group(1) if m else "" for m in tokens.values())

    def _call(self, path: str, freq, headers=None, timeout: int = 60) -> list:
        q = urllib.parse.urlencode({"bl": self.bl, "f.sid": self.sid, "hl": "en", "rt": "c"})
        try:
            raw = http(f"{BASE}/_/BardChatUi/data/{path}{'&' if '?' in path else '?'}{q}", self.jar,
                       {"f.req": json.dumps(freq), "at": self.at}, headers, timeout)
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403):
                raise AuthError(f"Google rejected the request (HTTP {e.code})") from e
            raise
        frames = []  # response is ")]}'" then length-prefixed JSON chunks of ["wrb.fr", rpc, payload]
        for line in raw.splitlines():
            if line.startswith("[["):
                frames += [json.loads(f[2]) for f in json.loads(line) if f[0] == "wrb.fr" and f[2]]
        return frames

    def models(self) -> dict[str, str]:
        listing = self._call("batchexecute?rpcids=otAQ7b", [[["otAQ7b", "[1]", None, "generic"]]])[0][15]
        return {m[1]: m[0] for m in listing}

    def resolve_model(self, name: str) -> str:
        models = self.models()
        by_name = {n.lower(): i for n, i in models.items()}
        if name.lower() in by_name:
            return by_name[name.lower()]
        if name in models.values() or re.fullmatch(r"[0-9a-f]{16}", name):
            return name
        raise RuntimeError(f"unknown model {name!r}; choose one of: {', '.join(models)}")

    def generate(self, prompt: str, model: str) -> tuple[list[str], str]:
        inner = [[prompt, 0, None, None, None, None, 0], ["en"], ["", "", ""]]
        try:
            frames = self._call(
                "assistant.lamda.BardFrontendService/StreamGenerate", [None, json.dumps(inner)],
                {"x-goog-ext-525001261-jspb": json.dumps([1, None, None, None, model, None, None, 0, [4]])},
                timeout=120,
            )
        except TimeoutError as e:
            # Text replies can take minutes over this endpoint; images arrive in under 30s.
            raise RuntimeError("no image after 120s. Gemini probably answered in text or declined; "
                               "phrase the prompt as an explicit image request") from e
        candidates = [f for f in frames if len(f) > 4 and f[4]]
        final = json.dumps(candidates[-1] if candidates else frames)
        urls = list(dict.fromkeys(re.findall(r"https://lh3\.googleusercontent\.com/gg-dl/[\w-]+", final)))
        image_model = re.findall(r'"(Nano Banana[^"]*)"', final)
        if not urls:
            reply = candidates[-1][4][0][1][0] if candidates else final[-500:]
            raise RuntimeError(f"Gemini returned no image. Reply: {reply}")
        return urls, (image_model[-1] if image_model else "unknown")

    def download(self, url: str) -> bytes:
        url = f"{url}=s0?alr=yes"  # s0 = original resolution
        for _ in range(5):  # each hop answers with the next URL as text until the image itself
            body = http(url, self.jar)
            if isinstance(body, bytes):
                return body
            if not body.startswith("https://"):
                raise RuntimeError(f"unexpected image download response: {body[:200]}")
            url = body.strip()
        raise RuntimeError("image download redirect chain did not end")


def with_session(work):
    """Run work(Gemini) with saved cookies; on rejection refresh them from the profile and retry once."""
    try:
        return work(Gemini(saved_cookies()))
    except AuthError:
        pass
    try:
        return work(Gemini(refresh_cookies()))
    except AuthError as e:
        if "--login" in str(e):
            raise
        raise AuthError(f"{e} even after refreshing cookies; run with --login") from e


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("-o", "--out", default="gemini.jpg", help="output path; extra images get -2, -3 suffixes")
    ap.add_argument("-m", "--model", default="Flash", help="Gemini chat model name or id (default: Flash)")
    ap.add_argument("--login", action="store_true", help="sign in with a visible browser")
    ap.add_argument("--list-models", action="store_true")
    a = ap.parse_args()
    if a.login:
        return login()
    if a.list_models:
        models = with_session(lambda g: g.models())
        return print("\n".join(f"{n}\t{i}" for n, i in models.items()))
    if not a.prompt:
        ap.error("prompt is required")

    def work(g: Gemini) -> list[Path]:
        urls, image_model = g.generate(a.prompt, g.resolve_model(a.model))
        print(f"image model: {image_model}", file=sys.stderr)
        images = [g.download(u) for u in urls]
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        paths = [out if i == 0 else out.with_stem(f"{out.stem}-{i + 1}") for i in range(len(images))]
        for p, data in zip(paths, images):
            p.write_bytes(data)
        return paths

    for p in with_session(work):
        print(p)


if __name__ == "__main__":
    try:
        main()
    except (AuthError, RuntimeError, OSError) as e:  # OSError covers network and HTTP errors
        sys.exit(f"error: {e}")
    except (ValueError, LookupError, TypeError) as e:
        sys.exit(f"error: unexpected response from Gemini ({type(e).__name__}: {e}). "
                 "Its private API may have changed; see references/gemini-web-api.md")
