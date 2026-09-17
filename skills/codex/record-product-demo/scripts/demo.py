"""Small agent-browser helpers. Import into a task-specific Python driver."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


class Demo:
    def __init__(self, session, scratch):
        self.scratch = Path(scratch).resolve()
        self.scratch.mkdir(parents=True, exist_ok=True)
        self.env = dict(os.environ, AGENT_BROWSER_SOCKET_DIR=os.environ.get('AGENT_BROWSER_SOCKET_DIR', str(self.scratch / 'browser')))
        executable = os.environ.get('DEMO_BROWSER') or shutil.which('agent-browser') or '/opt/homebrew/bin/agent-browser'
        self.command = [executable, '--session', session, '--json']
        self.events = []
        self.started = None

    def run(self, *args):
        result = subprocess.run(self.command + list(map(str, args)), env=self.env,
                                text=True, capture_output=True, timeout=45)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        payload = json.loads(result.stdout)
        if not payload.get('success'):
            raise RuntimeError(payload.get('error', 'Browser command failed'))
        return payload.get('data', {})

    def event(self, action, **fields):
        if self.started is not None:
            self.events.append(dict(at=round(time.monotonic() - self.started, 3), action=action, **fields))

    def js(self, expression):
        return self.run('eval', expression).get('result')

    def open(self, url):
        self.clear()
        self.run('open', url)

    def ready(self, expression):
        self.run('wait', '--fn', expression)

    def hold(self, seconds, target):
        if not target.strip():
            raise ValueError('A hold needs a reading target')
        self.event('hold', seconds=seconds, target=target)
        time.sleep(seconds)

    def focus(self, selector, color=None):
        self.run('wait', selector)
        self.ready(f'(() => {{ let e=document.querySelector({json.dumps(selector)}); if(!e?.checkVisibility({{visibilityProperty:true,opacityProperty:true}})) return false; for(;e;e=e.parentElement) if(e.getAnimations().some(a=>a.playState==="running" && a.effect.getComputedTiming().iterations!==Infinity)) return false; return true; }})()')
        self.js(Path(__file__).with_name('emphasis.js').read_text())
        self.js(f'window.__productDemo.focus({json.dumps(selector)}, {json.dumps(color)})')
        self.ready('!!document.querySelector("[data-product-demo=focus]") && getComputedStyle(document.querySelector("[data-product-demo=focus]")).opacity === "1"')
        self.event('focus', selector=selector)

    def clear(self):
        self.js('window.__productDemo?.remove()')

    def click(self, selector):
        self.event('click', selector=selector)
        self.run('click', selector)

    def type(self, selector, text, decisive=False):
        self.event('type', selector=selector, characters=len(text), decisive=decisive)
        self.run('click', selector)
        self.run('fill', selector, '')
        interval = .09 if decisive else .025
        for character in text:
            start = time.monotonic()
            self.run('keyboard', 'type', character)
            time.sleep(max(0, interval - (time.monotonic() - start)))
        self.assert_value(selector, text)

    def assert_value(self, selector, expected):
        actual = self.run('get', 'value', selector).get('value')
        if actual != expected:
            raise AssertionError(f'Unexpected value in {selector}')

    def scroll_to(self, selector):
        self.clear()
        self.event('scroll', selector=selector)
        self.js(f'document.querySelector({json.dumps(selector)}).scrollIntoView({{behavior:"smooth",block:"center"}})')
        self.ready(f'(() => {{ const r=document.querySelector({json.dumps(selector)}).getBoundingClientRect(); return r.top>=0 && r.bottom<=innerHeight; }})()')
        self.js(f'new Promise(resolve => {{ const target=document.querySelector({json.dumps(selector)}); let last=target.getBoundingClientRect().top, stable=0; function tick(){{const top=target.getBoundingClientRect().top;stable=top===last?stable+1:0;last=top;if(stable>5)resolve();else requestAnimationFrame(tick)}} requestAnimationFrame(tick) }})')

    @contextmanager
    def record(self, name):
        output = self.scratch / name
        if output.exists():
            raise FileExistsError(output)
        self.run('record', 'start', output, '--fps', 30)
        self.started = time.monotonic()
        self.events = []
        errors = []
        facts = {}
        try:
            yield self
        except BaseException as error:
            errors.append(error)
        finally:
            flow_seconds = time.monotonic() - self.started
            try:
                self.clear()
            except BaseException as error:
                errors.append(error)
            try:
                facts = self.run('record', 'stop')
            except BaseException as error:
                errors.append(error)
            elapsed = round(time.monotonic() - self.started, 3)
            self.started = None
            output.with_suffix('.take.json').write_text(json.dumps({
                'status': 'failed' if errors else 'recorded',
                'video': str(output), 'wall_seconds': elapsed,
                'flow_seconds': round(flow_seconds, 3),
                'recorder': facts, 'events': self.events,
                'errors': [{'type': type(error).__name__, 'message': str(error)} for error in errors],
                'playback_review': 'pending',
            }, indent=2) + '\n')
        if errors:
            raise errors[0]

    def close(self):
        self.run('close')
