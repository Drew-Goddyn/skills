"""Record motion, a six-second static hold, and renewed motion in the chosen format."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote
from uuid import uuid4
from check_video import tool
from demo import Demo, capture_environment


HTML = '''<!doctype html><meta charset="utf-8">
<title>Capture preflight</title>
<body style="margin:80px;background:#18212c;color:white;font:32px sans-serif">
<h1>Capture preflight</h1>
<p id="phase">Ready</p>
<p>Blue motion: 2 s → amber hold: 6 s → green motion: 2 s</p>
<div id="dot" style="position:absolute;left:80px;top:360px;width:60px;height:60px;
background:#448fff;border-radius:50%"></div>
<p style="position:absolute;top:500px">At normal speed, the green dot must move after the pause.</p>
</body>'''

MOTION = '''(() => {
  const dot = document.querySelector('#dot');
  const label = document.querySelector('#phase');
  const started = performance.now();
  window.preflight = {phases: [], done: false};
  function phase(name, color, text) {
    dot.style.background = color;
    label.textContent = text;
    window.preflight.phases.push({phase: name, at_ms: performance.now() - started});
  }
  function move(name, color, text, next) {
    phase(name, color, text);
    const beginning = performance.now();
    function tick(now) {
      const elapsed = Math.min(now - beginning, 2000);
      dot.style.transform = `translateX(${elapsed * .4}px)`;
      if (elapsed < 2000) requestAnimationFrame(tick);
      else next();
    }
    requestAnimationFrame(tick);
  }
  move('before', '#448fff', '1. Blue dot moving before the pause', () => {
    phase('hold', '#ffbb44', '2. Amber dot still for six seconds');
    // No frame loop or DOM updates during the hold: capture must resume from idle.
    setTimeout(() => move('after', '#38d996', '3. Green dot moving after the pause', () => {
      window.preflight.done = true;
    }), 6000);
  });
})()'''


def environment(profile_mode):
    return {'kind': 'test', 'url': 'data:text/html,' + quote(HTML),
            'signed_in_account_kind': 'none', 'authorized_for_capture': True,
            'data_provenance': 'invented', 'browser_profile_mode': profile_mode,
            'production_indicators': [],
            'conditions': 'Trusted bundled preflight HTML: no authentication, app records or external data. '
                          'Profile mode is supplied by the caller after checking the task configuration; '
                          'this fixture check does not establish the target application environment.'}


def check_motion(video):
    """Check this fixture's colored dot in decoded pixels, separately from cadence."""
    width, sample_fps = 1100, 10
    decoded = subprocess.run([
        tool('ffmpeg'), '-v', 'error', '-i', str(video), '-an',
        '-vf', f'fps={sample_fps},crop={width}:2:80:388,scale={width}:1',
        '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-',
    ], capture_output=True)
    if decoded.returncode:
        raise RuntimeError(decoded.stderr.decode(errors='replace') or 'Motion decode failed')
    phases = {name: [] for name in ('before', 'hold', 'after')}
    order = []
    frame_bytes = width * 3
    for frame_index, offset in enumerate(range(0, len(decoded.stdout), frame_bytes)):
        row = decoded.stdout[offset:offset + frame_bytes]
        pixels = {name: [] for name in phases}
        for x in range(len(row) // 3):
            red, green, blue = row[x * 3:x * 3 + 3]
            if blue > red + 80 and blue > green + 40:
                pixels['before'].append(x)
            elif red > blue + 100 and green > blue + 70:
                pixels['hold'].append(x)
            elif green > red + 80 and green > blue + 30:
                pixels['after'].append(x)
        for name, locations in pixels.items():
            if len(locations) >= 20:
                phases[name].append({'at_seconds': frame_index / sample_fps,
                                     'x': round(sum(locations) / len(locations), 2)})
                if not order or order[-1] != name:
                    order.append(name)
    facts = {}
    for name, samples in phases.items():
        positions = [sample['x'] for sample in samples]
        facts[name] = {'sampled_seconds': len(samples) / sample_fps,
                       'travel_pixels': round(max(positions) - min(positions), 2) if positions else 0,
                       'distinct_positions': len({round(x / 20) for x in positions}),
                       'samples': samples}
    violations = []
    if order != ['before', 'hold', 'after']:
        violations.append(f'expected blue motion, amber hold, green motion; found {order}')
    for name in ('before', 'after'):
        if facts[name]['travel_pixels'] < 300 or facts[name]['distinct_positions'] < 8:
            violations.append(f'{name} hold: expected moving dot, found {facts[name]["travel_pixels"]:g}px travel across {facts[name]["distinct_positions"]} positions')
    if not 5.8 <= facts['hold']['sampled_seconds'] <= 6.5:
        violations.append(f'expected six-second static hold, found {facts["hold"]["sampled_seconds"]:g}s')
    if facts['hold']['travel_pixels'] > 4:
        violations.append('amber dot moved during the static hold')
    return {'status': 'fail' if violations else 'pass', 'video': str(video),
            'sample_fps': sample_fps, 'phases': facts, 'violations': violations,
            'playback_review': 'pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scratch', type=Path)
    parser.add_argument('--format', choices=('webm', 'mp4'), default='webm',
                        help='Use the same format as the planned take (default: webm).')
    parser.add_argument('--browser-profile-mode', default='unknown',
                        help='Set task_only after verifying the task profile configuration; this does not configure or inspect a browser.')
    args = parser.parse_args()
    demo = Demo('pf-' + uuid4().hex[:8], args.scratch)
    video = demo.scratch / f'preflight.{args.format}'
    observed = environment(args.browser_profile_mode)
    if capture_environment(observed)['status'] == 'blocked':
        # Reuse the failed-take diagnostic before opening any browser session.
        with demo.record(video.name, environment=observed):
            pass
    try:
        demo.run('open', 'about:blank')
        demo.run('set', 'viewport', 1440, 900)
        demo.open('data:text/html,' + quote(HTML))
        with demo.record(video.name, environment=observed):
            demo.js(MOTION)
            demo.hold(10.2, 'Blue motion, six-second amber hold, then renewed green motion')
            demo.ready('window.preflight.done === true')
            fixture = demo.js('window.preflight')
        (demo.scratch / 'preflight.fixture.json').write_text(json.dumps(fixture, indent=2) + '\n')
        result = subprocess.run([
            sys.executable, str(Path(__file__).with_name('check_video.py')), str(video),
            '--expected-size', '1440x900', '--expected-fps', '30',
        ], text=True, capture_output=True)
        (demo.scratch / 'preflight.media.json').write_text(result.stdout)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout or 'Preflight media check failed')
        motion = check_motion(video)
        (demo.scratch / 'preflight.motion.json').write_text(json.dumps(motion, indent=2) + '\n')
        print(json.dumps({'media': json.loads(result.stdout), 'motion': motion}, indent=2))
        if motion['violations']:
            raise RuntimeError('Preflight motion check failed: ' + '; '.join(motion['violations']))
    finally:
        demo.close()


if __name__ == '__main__':
    main()
