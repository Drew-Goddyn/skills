"""Exercise input and emphasis against a real browser without application data."""
import argparse
import json
import tempfile
from pathlib import Path
from urllib.parse import quote
from demo import Demo, capture_environment

TEST_ENVIRONMENT = json.loads((Path(__file__).resolve().parent.parent /
                               'fixtures/capture-environments.json').read_text())['base']


def check_record_failures(scratch):
    results = []
    class FailingRecorder(Demo):
        def run(self, *args):
            if args[:2] == ('record', 'start') and self.failure == 'start':
                raise self.error
            if args[:2] == ('record', 'stop'):
                self.stopped = True
                if self.failure == 'stop':
                    raise self.error
                return {'stub': True, 'stopped': True}
            return {}
        def clear(self):
            self.cleared = True
            if self.failure == 'clear':
                raise self.error
    for failure in ('start', 'body', 'clear', 'stop'):
        recorder = FailingRecorder('unused', scratch)
        recorder.failure = failure
        recorder.error = RuntimeError(f'simulated {failure} failure')
        recorder.stopped = recorder.cleared = False
        entered = False
        try:
            with recorder.record(f'{failure}.webm', environment=TEST_ENVIRONMENT):
                entered = True
                if failure == 'body':
                    raise recorder.error
        except RuntimeError as error:
            if error is not recorder.error:
                raise AssertionError(f'{failure} failure replaced the original exception') from error
        else:
            raise AssertionError(f'{failure} failure was swallowed')
        report = json.loads((scratch / f'{failure}.take.json').read_text())
        if report['status'] != 'failed' or report['errors'] != [
                {'type': 'RuntimeError', 'message': str(recorder.error)}]:
            raise AssertionError(f'{failure} failure did not leave recovery evidence')
        if failure == 'start':
            if (entered or recorder.stopped or recorder.cleared or recorder.started is not None
                    or report.get('failure_stage') != 'recorder_start'
                    or report['capture_request']['fps'] != 30
                    or report['capture_request']['environment'] != TEST_ENVIRONMENT
                    or report['capture_request']['environment_check'] != {'status': 'allowed', 'reasons': []}
                    or report['video'] != str(scratch.resolve() / 'start.webm')
                    or report['wall_seconds'] is not None or report['flow_seconds'] is not None
                    or report['recorder'] != {} or report['events'] != []
                    or (scratch / 'start.webm').exists()):
                raise AssertionError('start failure invented capture state or lost request context')
            results.append('start failure records the request and error without inventing a take or swallowing the error')
        else:
            if not entered or not recorder.stopped or not recorder.cleared:
                raise AssertionError(f'{failure} failure did not attempt cleanup and stop')
            results.append(f'{failure} failure attempts stop and preserves failed evidence and original error')

    recorder = FailingRecorder('unused', scratch)
    recorder.failure = None
    recorder.stopped = recorder.cleared = False
    with recorder.record('success.webm', environment=TEST_ENVIRONMENT) as active:
        if active is not recorder:
            raise AssertionError('record yielded a different helper')
        recorder.event('stub-action', target='invented fixture')
    report = json.loads((scratch / 'success.take.json').read_text())
    if (set(report) != {'status', 'video', 'wall_seconds', 'flow_seconds', 'recorder', 'capture_request',
                       'events', 'errors', 'playback_review'}
            or report['status'] != 'recorded' or report['errors'] != []
            or report['recorder'] != {'stub': True, 'stopped': True}
            or [event['action'] for event in report['events']] != ['stub-action']
            or not 0 <= report['flow_seconds'] <= report['wall_seconds']
            or report['playback_review'] != 'pending'
            or report['capture_request']['environment_check'] != {'status': 'allowed', 'reasons': []}
            or not recorder.stopped or not recorder.cleared or recorder.started is not None):
        raise AssertionError('successful take changed its record or cleanup behavior')
    results.append('successful take preserves the existing schema, recorder facts, events, and cleanup')

    recorder.failure = 'start'
    recorder.error = RuntimeError('simulated start failure after a successful take')
    recorder.stopped = recorder.cleared = False
    try:
        with recorder.record('next.webm', environment=TEST_ENVIRONMENT):
            raise AssertionError('flow entered after start failure')
    except RuntimeError as error:
        if error is not recorder.error:
            raise AssertionError('reused helper replaced the startup error') from error
    else:
        raise AssertionError('reused helper swallowed the startup error')
    report = json.loads((scratch / 'next.take.json').read_text())
    if report['events'] != [] or report['recorder'] != {} or recorder.stopped or recorder.cleared:
        raise AssertionError('start failure reused stale events or claimed cleanup of a started recorder')
    results.append('start failure after success does not inherit previous events or recorder facts')

    try:
        with recorder.record('missing-parent/unsavable.webm', environment=TEST_ENVIRONMENT):
            raise AssertionError('flow entered after start failure')
    except RuntimeError as error:
        if error is not recorder.error or not isinstance(error.__cause__, OSError):
            raise AssertionError('diagnostic write failure obscured the startup error') from error
    else:
        raise AssertionError('unsavable diagnostic converted startup failure into success')
    results.append('unsavable diagnostic preserves the startup error with the file error as its cause')
    return results


def check_focus_colors(b, scratch):
    """Render the same invented page with and without an app accent and override."""
    b.run('set', 'viewport', 900, 520)
    b.open('data:text/html,' + quote('''<!doctype html><meta charset="utf-8">
<title>Focus ring portability fixture</title>
<style>body{margin:48px;background:#f4f6fa;color:#172333;font:22px system-ui}
h1{font-size:30px}p{font-size:18px}label{display:block;margin-top:36px}
input{display:block;margin-top:12px;padding:14px;width:480px;box-sizing:border-box;
font:24px system-ui;color:#172333;background:white;border:1px solid #708090;border-radius:4px}</style>
<h1>Focus ring portability</h1><p>Invented data. The field and its geometry stay the same.</p>
<p id="context"></p><label>Invoice amount<input id="amount" value="$125.00"></label>'''))
    cases = [
        ('default-no-accent', None, None, 'rgb(68, 143, 255)'),
        ('default-with-accent', '#e11d74', None, 'rgb(68, 143, 255)'),
        ('explicit-with-accent', '#e11d74', '#21a179', 'rgb(33, 161, 121)'),
    ]
    facts = []
    for name, accent, color, expected in cases:
        b.js('document.documentElement.style.removeProperty("--c-accent")' if accent is None else
             f'document.documentElement.style.setProperty("--c-accent", {json.dumps(accent)})')
        context = f'Application accent: {accent or "unset"}. Ring override: {color or "none"}.'
        b.js(f'document.querySelector("#context").textContent={json.dumps(context)}')
        b.focus('#amount', color=color)
        measured = b.js('''(() => {
            const ring = document.querySelector('[data-product-demo]');
            const style = getComputedStyle(ring);
            return {color: style.borderTopColor, border_width: style.borderTopWidth,
                    radius: style.borderTopLeftRadius, opacity: style.opacity,
                    pointer_events: style.pointerEvents,
                    ring: ring.getBoundingClientRect().toJSON(),
                    target: document.querySelector('#amount').getBoundingClientRect().toJSON()};
        })()''')
        b.run('screenshot', scratch / f'{name}.png')
        ring, target = measured['ring'], measured['target']
        geometry = all(abs(actual - expected_value) < 1 for actual, expected_value in (
            (ring['left'], target['left'] - 5), (ring['top'], target['top'] - 5),
            (ring['width'], target['width'] + 10), (ring['height'], target['height'] + 10)))
        passed = (measured['color'] == expected and geometry and measured['border_width'] == '2px'
                  and measured['radius'] == '8px' and measured['opacity'] == '1'
                  and measured['pointer_events'] == 'none')
        facts.append({'case': name, 'app_accent': accent, 'explicit_color': color,
                      'expected_color': expected, 'measured': measured, 'pass': passed,
                      'screenshot': f'{name}.png'})
    (scratch / 'focus-colors.json').write_text(json.dumps(facts, indent=2) + '\n')
    failures = [fact['case'] for fact in facts if not fact['pass']]
    if failures:
        raise AssertionError('Focus color/geometry check failed: ' + ', '.join(failures))
    b.clear()
    b.run('set', 'viewport', 1440, 900)
    return [f'{fact["case"]} preserves requested color, geometry, visibility, and pointer noninterference'
            for fact in facts]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-only', action='store_true',
                        help='Run deterministic take-record checks without a browser.')
    parser.add_argument('--browser-profile-mode', default='unknown',
                        help='For live checks, set task_only after verifying the task profile configuration.')
    args = parser.parse_args()
    scratch = Path(tempfile.mkdtemp(prefix='demo-check-', dir='/tmp'))
    checks = check_record_failures(scratch)
    if args.record_only:
        result = {'status': 'pass', 'checks': checks, 'scratch': str(scratch)}
        (scratch / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result, indent=2))
        return
    b = Demo('helpers', scratch)
    fixture_url = 'data:text/html,' + quote('<body><input id="plain"><button id="behind">Open</button><dialog><input id="decisive"><button id="save" onclick="window.saved=true">Save</button></dialog><div style="height:1400px"></div><button id="last">Last</button></body>')
    observed = dict(TEST_ENVIRONMENT, url=fixture_url, browser_profile_mode=args.browser_profile_mode,
                    conditions='Bundled helper-test HTML with invented inputs and no authentication or external records. '
                               'Caller supplies the verified task-profile mode; no profile inspection is automated.')
    if capture_environment(observed)['status'] == 'blocked':
        with b.record('failed.webm', environment=observed):
            pass
    def check(name, expression):
        if b.js(expression) is not True:
            raise AssertionError(name)
        checks.append(name)
    try:
        b.run('open', 'about:blank')
        b.run('set', 'viewport', 1440, 900)
        checks.extend(check_focus_colors(b, scratch))
        b.open(fixture_url)
        b.type('#plain', 'routine')
        b.type('#plain', 'replacement')
        checks.append('real input events replace existing text')
        b.js('document.querySelector("dialog").showModal()')
        b.focus('#decisive')
        b.type('#decisive', 'galaxy-brain', decisive=True)
        b.ready('getComputedStyle(document.querySelector("[data-product-demo]")).opacity === "1"')
        check('ring is above dialog without covering input', 'document.querySelector("dialog").contains(document.querySelector("[data-product-demo]")) && getComputedStyle(document.querySelector("[data-product-demo]")).pointerEvents === "none"')
        check('ring encloses the live target', '(() => {const a=document.querySelector("#decisive").getBoundingClientRect(),b=document.querySelector("[data-product-demo]").getBoundingClientRect();return Math.abs(a.left-b.left-5)<1 && Math.abs(a.width-b.width+10)<1})()')
        b.js('document.querySelector("#decisive").style.marginLeft="45px"')
        b.ready('Math.abs(document.querySelector("#decisive").getBoundingClientRect().left-document.querySelector("[data-product-demo]").getBoundingClientRect().left-5)<1')
        checks.append('ring follows layout changes')
        for property_name, hidden_value in [('visibility', 'hidden'), ('opacity', '0')]:
            b.js(f'document.querySelector("#decisive").style.{property_name}="{hidden_value}"')
            b.ready('!document.querySelector("[data-product-demo]")')
            checks.append(f'{property_name} hidden target cleans up ring')
            b.js(f'document.querySelector("#decisive").style.{property_name}=""')
            b.focus('#decisive')
        b.focus('#save')
        b.click('#save')
        check('emphasis preserves real button action', 'window.saved === true')
        b.js('document.querySelector("#save").remove()')
        b.ready('!document.querySelector("[data-product-demo]")')
        checks.append('detached target cleans up ring')
        b.focus('#decisive')
        b.js('document.querySelector("dialog").close()')
        b.ready('!document.querySelector("[data-product-demo]")')
        checks.append('closed dialog cleans up ring')
        b.scroll_to('#last')
        check('smooth scroll settles at visible target', 'document.querySelector("#last").getBoundingClientRect().bottom <= innerHeight')
        b.focus('#last')
        b.clear()
        check('explicit cleanup removes injected nodes', '!document.querySelector("[data-product-demo]")')
        try:
            b.focus('body, #plain')
            raise AssertionError('ambiguous focus accepted')
        except RuntimeError:
            checks.append('ambiguous focus fails visibly')
        try:
            with b.record('failed.webm', environment=observed):
                b.hold(.3, 'Failure-cleanup fixture')
                raise ValueError('intentional failure')
        except ValueError:
            pass
        report = json.loads((scratch / 'failed.take.json').read_text())
        if report['status'] != 'failed' or not (scratch / 'failed.webm').is_file():
            raise AssertionError('failed take was not flushed and marked failed')
        checks.append('failed flow flushes video and records failure')
        result = {'status':'pass', 'checks':checks, 'scratch':str(scratch)}
        (scratch / 'checks.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
    finally:
        b.close()


if __name__ == '__main__':
    main()
