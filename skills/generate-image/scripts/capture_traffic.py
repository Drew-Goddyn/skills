# /// script
# requires-python = ">=3.10"
# dependencies = ["patchright>=1.50"]
# ///
"""Maintenance only: drive one image prompt through the Gemini UI and record a HAR.

  uv run capture_traffic.py out.har ["prompt"]

Use when gemini_web.py breaks, to see what the web app sends now.
The HAR holds session cookies; delete it when done.
"""
import os
import sys
from pathlib import Path

from patchright.sync_api import sync_playwright

PROFILE = Path(os.environ.get("GEMINI_WEB_HOME", Path.home() / ".local/share/generate-image")) / "gemini-profile"
out = Path(sys.argv[1])
prompt = sys.argv[2] if len(sys.argv) > 2 else "Generate an image of a red apple on a wooden table"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(PROFILE), channel="chrome", headless=False, no_viewport=True,
        record_har_path=str(out), record_har_content="embed",
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://gemini.google.com/app")
    try:
        box = page.get_by_role("textbox", name="Enter a prompt for Gemini")
        box.wait_for(timeout=30000)
        box.click()
        page.keyboard.type(prompt)
        page.keyboard.press("Enter")
        page.locator("model-response img[src*='googleusercontent']").first.wait_for(timeout=180000)
        page.wait_for_timeout(8000)
    finally:
        page.screenshot(path=str(out.with_suffix(".png")))
        ctx.close()
