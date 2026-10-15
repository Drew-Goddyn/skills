---
name: generate-image
description: Generate an image from a text prompt and save it to a file. Use when a task needs a new picture, illustration, mockup asset, or concept art. Uses Drew's paid Gemini web subscription; requires uv and Google Chrome.
---

# Generate image

Each provider is one script in `scripts/`. Run it from this skill's directory with `uv run`, which installs
its dependencies on first use.

| Provider | Script | Account |
| --- | --- | --- |
| Gemini web (Nano Banana) | [`scripts/gemini_web.py`](scripts/gemini_web.py) | Google account with a Gemini subscription, signed in once |

## Gemini web

```sh
uv run scripts/gemini_web.py "Generate an image of <subject, style, composition>" -o out/name.jpg
```

- Start the prompt with "Generate an image of". Gemini answers some phrasings in
  text instead, and the script exits with "no image" and the reply, or after two
  minutes if the reply is slow.
- It prints the saved path on stdout and the image model on stderr. When Gemini
  returns several images, the extras are saved as `name-2.jpg`, `name-3.jpg`.
- `-m` picks the Gemini chat model. The default, `Flash`, produces images with
  the full image model (Nano Banana 2.1 as of October 2026); `Flash-Lite`
  drops to a lighter one. `--list-models` shows the current names, and an
  unknown name is an error.
- One image takes 10 to 25 seconds. Each one also appears as a chat in the
  account's Gemini history.

Signing in is a one-time human step. When the script exits with "run with
--login", ask Drew to run this and sign in to Google in the Chrome window it
opens, then close the window:

```sh
uv run scripts/gemini_web.py --login
```

The script keeps the sign-in in a dedicated Chrome profile under
`~/.local/share/generate-image/` (override with `GEMINI_WEB_HOME`) and renews
Google's cookies from it automatically, using a hidden browser.

Generation calls Gemini's private web API, which Google can change without
notice. When it breaks in a way a fresh `--login` does not fix, follow
[references/gemini-web-api.md](references/gemini-web-api.md).

## Adding a provider

Add one script per provider to `scripts/` with the same interface: a prompt
argument, `-o` for the output path, the saved path on stdout. Then add a row to
the table and a section to this file.
