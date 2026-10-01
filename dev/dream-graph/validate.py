#!/usr/bin/env python3
"""Structural checks for the portable Dream Graph folder, not an agent benchmark."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


def check(skill: Path) -> list[str]:
    """Return structural errors without mutating the candidate."""
    errors: list[str] = []
    entry = skill / 'SKILL.md'
    if not entry.is_file():
        return ['Missing SKILL.md']
    text = entry.read_text(encoding='utf-8')
    front = re.match(r'\A---\n(.*?)\n---\n', text, re.S)
    if not front:
        errors.append('Missing frontmatter')
    else:
        fields = dict(re.findall(r'^([a-z_-]+):\s*(.+)$', front.group(1), re.M))
        if fields.get('name') != 'dream-graph':
            errors.append('Unexpected skill name')
        if not fields.get('description', '').strip('"\' '):
            errors.append('Empty description')
    if len(text.splitlines()) >= 500:
        errors.append('Entrypoint exceeds the skill-authoring line guideline')
    if len(list(skill.rglob('SKILL.md'))) != 1:
        errors.append('Portable folder must contain exactly one skill entrypoint')
    metadata = skill / 'agents/openai.yaml'
    if not metadata.is_file():
        errors.append('Missing agent metadata')
    else:
        data = metadata.read_text(encoding='utf-8')
        for key in ('display_name:', 'short_description:', 'default_prompt:'):
            if key not in data:
                errors.append(f'Missing metadata field {key}')
    for path in skill.rglob('*.md'):
        body = path.read_text(encoding='utf-8')
        for target in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', body):
            url = urlsplit(target)
            if url.scheme or url.netloc:
                continue
            resolved = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not resolved.is_relative_to(skill.resolve()):
                errors.append(f'{path.name}: dependency escapes skill folder: {target}')
            elif not resolved.is_file():
                errors.append(f'{path.name}: missing local reference: {target}')
        if re.search(r'/(?:Users|mnt/data|home/oai)/', body):
            errors.append(f'{path.name}: machine-specific path in portable instructions')
    license_path = skill / 'LICENSE'
    if not license_path.is_file():
        errors.append('Missing upstream license')
    else:
        content = license_path.read_bytes()
        sha = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        if sha != 'dd54a3e60d5fe9e2296c4745c5b826d74158c852':
            errors.append('Upstream MIT notice does not match inspected source')
    for decision in ('CONTINUE', 'READY', 'REJECT', 'PAUSE'):
        if f'| **{decision}** |' not in text:
            errors.append(f'Missing decision row: {decision}')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'skills/dream-graph')
    args = parser.parse_args()
    try:
        errors = check(args.skill.resolve())
    except (OSError, UnicodeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print('PASS: structure, local references, portability, metadata, license, and decision rows')
    print('This does not validate agent behavior or the quality of a generated experience.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
