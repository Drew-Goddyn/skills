"""Exercise input and emphasis against a real browser without application data."""
import json
import tempfile
from pathlib import Path
from urllib.parse import quote
from demo import Demo


def check_record_failures(scratch):
    results = []
    class FailingRecorder(Demo):
        def run(self, *args):
            if args[:2] == ('record', 'stop'):
                self.stopped = True
                if self.failure == 'stop':
                    raise RuntimeError('simulated stop failure')
            return {}
        def clear(self):
            if self.failure == 'clear':
                raise RuntimeError('simulated cleanup failure')
    for failure in ('body', 'clear', 'stop'):
        recorder = FailingRecorder('unused', scratch)
        recorder.failure, recorder.stopped = failure, False
        try:
            with recorder.record(f'{failure}.webm'):
                if failure == 'body':
                    raise RuntimeError('simulated flow failure')
        except RuntimeError:
            pass
        report = json.loads((scratch / f'{failure}.take.json').read_text())
        if report['status'] != 'failed' or not report['errors'] or not recorder.stopped:
            raise AssertionError(f'{failure} failure did not leave recovery evidence')
        results.append(f'{failure} failure attempts stop and preserves failed evidence')
    return results


def main():
    scratch = Path(tempfile.mkdtemp(prefix='demo-check-', dir='/tmp'))
    b = Demo('helpers', scratch)
    checks = check_record_failures(scratch)
    def check(name, expression):
        if b.js(expression) is not True:
            raise AssertionError(name)
        checks.append(name)
    try:
        b.run('open', 'about:blank')
        b.run('set', 'viewport', 1440, 900)
        b.open('data:text/html,' + quote('<body><input id="plain"><button id="behind">Open</button><dialog><input id="decisive"><button id="save" onclick="window.saved=true">Save</button></dialog><div style="height:1400px"></div><button id="last">Last</button></body>'))
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
            with b.record('failed.webm'):
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
