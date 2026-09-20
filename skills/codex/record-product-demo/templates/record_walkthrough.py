#!/usr/bin/env python3
"""Starter: prepare a form, enter one value, submit, and reveal its new result.

Copy into task scratch to adapt prepare()/perform() for a different flow. Import
shared helpers from --skill; keep the selected skill unchanged during recording.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
from uuid import uuid4


def save(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def load_helpers(skill):
    """Explicit file import avoids an unrelated installed/cached 'demo' module."""
    spec = importlib.util.spec_from_file_location('selected_demo', skill / 'scripts/demo.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs(path):
    c = json.loads(path.read_text())
    def text(value, field):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(field + ' needs nonempty text')
    for key in ('url',): text(c[key], key)
    if c['environment'].get('url') != c['url']:
        raise ValueError('environment.url must match the supplied application URL, including setup/reset parameters')
    for key in ('ready', 'open', 'action', 'submit', 'results', 'identity_attribute', 'blur'):
        text(c['selectors'][key], 'selectors.' + key)
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]*', c['selectors']['identity_attribute']):
        raise ValueError('identity_attribute must be an attribute name, not a selector expression')
    text(c['values']['action'], 'values.action')
    for item in c['values']['prefill']:
        text(item['selector'], 'prefill.selector'); text(item['value'], 'prefill.value')
        if item['selector'] == c['selectors']['action']:
            raise ValueError('Keep the decisive action field out of prefill')
    if not c['values']['result_contains']: raise ValueError('result_contains needs expected result text')
    for value in c['values']['result_contains']: text(value, 'result_contains')
    for key in ('context', 'action', 'submit', 'result'): text(c['labels'][key], 'labels.' + key)
    for value in c['holds'].values():
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError('holds must be finite nonnegative seconds')
    for key in ('context', 'action', 'result'): c['holds'][key]
    if len(c['viewport']) != 2 or any(type(v) is not int or v <= 0 for v in c['viewport']):
        raise ValueError('viewport needs two positive integer dimensions')
    for key in ('text', 'audience', 'takeaway'): text(c['brief'][key], 'brief.' + key)
    if c['brief']['sound_policy'] not in ('forbid', 'allow', 'require'): raise ValueError('Unknown sound policy')
    low, high = c['brief']['min_seconds'], c['brief']['max_seconds']
    for value in (low, high):
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
            raise ValueError('Duration bounds must be null or finite nonnegative seconds')
    if low is not None and high is not None and low > high: raise ValueError('Minimum duration exceeds maximum')
    text(c['source']['revision_note'], 'source.revision_note')
    if c['source']['revision'] is not None: text(c['source']['revision'], 'source.revision')
    return c


def rows(demo, selectors):
    result = demo.js('Array.from(document.querySelectorAll(%s), e => ({id:e.getAttribute(%s), text:e.innerText}))' %
                     (json.dumps(selectors['results']), json.dumps(selectors['identity_attribute'])))
    ids = [row['id'] for row in result]
    if any(not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Result collection must have stable, unique, nonempty identities')
    return result


def prepare(demo, c):
    """Task-local adaptation point; setup occurs only after environment eligibility."""
    demo.open(c['url'])
    demo.run('set', 'viewport', *c['viewport'], 1)
    demo.run('wait', c['selectors']['ready'])
    before = rows(demo, c['selectors'])
    demo.click(c['selectors']['open'])
    for field in c['values']['prefill']:
        demo.run('fill', field['selector'], field['value'])
        demo.assert_value(field['selector'], field['value'])
    demo.click(c['selectors']['blur'])
    demo.assert_value(c['selectors']['action'], '')
    return before


def perform(demo, c, before):
    """One fixed starter flow, not a browser action language."""
    def beat(name): demo.event('beat', beat_id=name, label=c['labels'][name])
    beat('context'); demo.hold(c['holds']['context'], c['labels']['context'])
    beat('action'); demo.type(c['selectors']['action'], c['values']['action'], decisive=True)
    demo.click(c['selectors']['blur'])
    demo.hold(c['holds']['action'], c['labels']['action'])
    beat('submit'); demo.click(c['selectors']['submit'])
    ids = [row['id'] for row in before]
    demo.ready('Array.from(document.querySelectorAll(%s)).some(e => !%s.includes(e.getAttribute(%s)))' %
               (json.dumps(c['selectors']['results']), json.dumps(ids), json.dumps(c['selectors']['identity_attribute'])))
    created = [row for row in rows(demo, c['selectors']) if row['id'] not in ids]
    if len(created) != 1: raise AssertionError('Expected exactly one newly identified result')
    result = created[0]
    if not all(value in result['text'] for value in c['values']['result_contains']):
        raise AssertionError('New result does not contain the expected values')
    escaped = demo.js('CSS.escape(%s)' % json.dumps(result['id']))
    selector = c['selectors']['results'] + '[' + c['selectors']['identity_attribute'] + '=' + escaped + ']'
    demo.scroll_to(selector)
    beat('result'); demo.hold(c['holds']['result'], c['labels']['result'])
    return result


def media_check(skill, output, c):
    command = [sys.executable, str(skill/'scripts/check_video.py'), 'reel.mp4',
               '--expected-size', '%dx%d' % tuple(c['viewport']), '--expected-fps', '30',
               '--audio-policy', c['brief']['sound_policy']]
    for key, flag in (('min_seconds', '--min-duration'), ('max_seconds', '--max-duration')):
        if c['brief'][key] is not None: command += [flag, str(c['brief'][key])]
    result = subprocess.run(command, cwd=output, text=True, capture_output=True)
    (output/'facts/media.stdout.txt').write_text(result.stdout)
    (output/'facts/media.stderr.txt').write_text(result.stderr)
    save(output/'facts/media-command.json', {'argv':command, 'cwd':'delivery folder', 'returncode':result.returncode})
    # The existing checker emits startup errors on stderr. Preserve both channels.
    report = json.loads(result.stdout or result.stderr)
    save(output/'facts/media.json', report)
    return report


def evidence(skill, output, c, phase, report):
    d = json.loads((skill/'templates/evidence.json').read_text())
    take = json.loads((output/'reel.take.json').read_text())
    video = output/'reel.mp4'
    duration = report.get('picture', {}).get('duration_seconds')
    if duration is None: raise ValueError('Picture duration unestablished; retain the take/check diagnostic without inventing reel evidence')
    d['reel'].update(sha256=hashlib.sha256(video.read_bytes()).hexdigest(), size_bytes=video.stat().st_size, duration_seconds=duration)
    d['brief'].update(audience=c['brief']['audience'], takeaway=c['brief']['takeaway'],
                      decisive_moments=[c['labels'][v] for v in ('action','submit','result')],
                      duration_seconds={'min':c['brief']['min_seconds'],'max':c['brief']['max_seconds']}, sound_policy=c['brief']['sound_policy'])
    d['environment'] = c['environment']
    d['source'].update(revision=c['source']['revision'], revision_note=c['source']['revision_note'])
    d['production']['capture']['context'] = phase + ': direct browser capture; no edit. Application assertions are not encoded-frame review.'
    d['takes'] = [{'id':phase,'role':'new_capture','record':'reel.take.json'}]
    d['beats'] = [{'id':e['beat_id'],'kind':'result' if e['beat_id']=='result' else 'action',
                   'label':e['label'],'decisive':e['beat_id']!='context',
                   'driver_time':{'take':phase,'event_index':i}, 'video_time':None,'alignment':'unknown',
                   'timing_note':'Driver event only. Recorder startup is asynchronous; no encoded-video offset established.'}
                  for i,e in enumerate(take['events']) if e['action']=='beat']
    d['checks'] = [{'id':'media','kind':'media','status':'performed','report':'facts/media.json',
                    'context':'Selected skill checker; full command, return code and both raw channels in facts/media-command.json and media.*.txt.'}]
    for key in ('agent_frames','continuous_watch','listening','human'):
        d['review'][key] = {'status':'unavailable' if key=='human' else 'not_performed',
                            'coverage':'No '+key.replace('_',' ')+' result collected by this driver. Mechanical assertions are not viewing evidence.', 'evidence':[]}
    d['review']['watch_list'] = [{'beat_id':b['id'],'label':b['label'],'video_seconds':None,'precision':None,
                                 'note':'Final-output time unresolved. Inspect interval sheets/native frames to locate this moment.'} for b in d['beats'] if b['decisive']]
    d['review']['beat_findings'] = []
    d['privacy'].update(coverage='No output privacy inspection performed. Environment eligibility and empty findings are not clearance.')
    d['limitations'] = ['Initial generated record: decisive-frame, privacy and continuous-viewing review remain unperformed; direct human result uncollected.',
                        'All encoded beat times and driver/video alignment remain unknown. Inspect the delivered encode; preserve this initial record when adding later findings.']
    d['toolkit']['scope'] = 'Ordinary recording with existing helpers; task-local driver only.'
    d['toolkit']['result'].update(reason='This completed flow made no shared-toolkit changes. Record later reusable friction separately if encountered.',
                                 tool_version='Exact selected helper and driver identities in facts/toolkit-source.json.',
                                 discovery='Explicit --skill input; no installed-skill replacement.')
    d['reproduction'].update(setup='Inputs in facts/inputs.json; same prepare/perform flow for rehearsal and take. Preflight is separate and does not establish target-app eligibility.',
                             created_records=[json.loads((output/'facts/application.json').read_text())['id']],
                             cleanup=json.loads((output/'facts/cleanup.json').read_text()))
    save(output/'evidence.json', d)
    return d


def capture(skill, input_path, output, phase, *, helpers=None, check=media_check):
    skill = skill.resolve(); c = inputs(input_path)
    helpers = helpers or load_helpers(skill)
    output = output.resolve(); output.mkdir(parents=True, exist_ok=False); (output/'facts').mkdir()
    save(output/'facts/inputs.json', c); save(output/'facts/source.json', c['source'])
    (output/'facts/brief.txt').write_text(c['brief']['text']+'\n')
    shutil.copy2(__file__, output/'facts/driver.py')
    names = ('SKILL.md','scripts/demo.py','scripts/emphasis.js','scripts/check_video.py','scripts/check_evidence.py','templates/evidence.json')
    save(output/'facts/toolkit-source.json', {'selected_skill':str(skill),'driver_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'selected_files_sha256':{n:hashlib.sha256((skill/n).read_bytes()).hexdigest() for n in names},
         'basis':'Exact bytes at explicit --skill path. Hashes identify uncommitted/copied source without claiming installation or a clean Git revision.'})
    save(output/'facts/capture.json', {'phase':phase,'viewport':c['viewport'],'fps':30,'format':'mp4','input_method':'existing Demo.type native keyboard events',
         'environment':c['environment'],'preflight':'Separate operation; does not clear this application.', 'helper_identity':'facts/toolkit-source.json'})
    demo = helpers.Demo('starter-'+uuid4().hex[:10], output)
    opened = False; error = None
    try:
        try:
            if helpers.capture_environment(c['environment'])['status'] != 'allowed':
                # Preserve the existing blocked-take record without opening the app.
                with demo.record('reel.mp4', environment=c['environment']): pass
                raise RuntimeError('Environment was blocked; capture must not proceed')
            opened = True  # Our unique session only, including partially failed startup.
            before = prepare(demo, c)
            with demo.record('reel.mp4', environment=c['environment']):
                result = perform(demo, c, before)
            save(output/'facts/application.json', result)
        except BaseException as exc:
            error = exc
            raise
        finally:
            cleanup = {'status':'not_applicable','coverage':'No browser session opened; no service is owned by this driver.','evidence':[]}
            try:
                if opened:
                    demo.close()
                    cleanup.update(status='performed',coverage='Closed only this driver\'s unique browser session. Application server remains caller-owned.',evidence=['facts/cleanup-result.json'])
            except BaseException as exc:
                cleanup.update(status='unavailable',coverage='Owned-session close failed: '+str(exc),evidence=['facts/cleanup-result.json'])
                if error is None: raise
            finally:
                save(output/'facts/cleanup-result.json', cleanup)
                save(output/'facts/cleanup.json', cleanup)
        report = check(skill, output, c)
        evidence(skill, output, c, phase, report)
        result = subprocess.run([sys.executable,str(skill/'scripts/check_evidence.py'),'evidence.json'],cwd=output,capture_output=True,text=True)
        (output/'facts/evidence-check.json').write_text(result.stdout or result.stderr)
        if result.returncode: raise RuntimeError('Generated evidence validation failed; see facts/evidence-check.json')
        if report['status'] != 'pass': raise RuntimeError('Media check failed; see preserved facts/media.json and evidence.json')
        save(output/'run.json', {'status':'recorded_pending_review','phase':phase,'evidence':'evidence.json',
                                'limits':'Capture and media checks passed; decisive-frame, privacy and viewing review not performed.'})
    except BaseException as exc:
        save(output/'run.json', {'status':'failed','phase':phase,'error':{'type':type(exc).__name__,'message':str(exc)},
                                'take_record':'reel.take.json' if (output/'reel.take.json').exists() else None,
                                'limits':'No successful delivery claim. Preserve partial output and original helper diagnostics.'})
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--skill',type=Path,required=True,help='Explicit recording-skill directory, unchanged by this driver')
    p.add_argument('--inputs',type=Path,required=True,help='Task-supplied JSON; see recording-driver.md')
    p.add_argument('--output',type=Path,required=True,help='New delivery directory, never overwritten')
    p.add_argument('--phase',choices=('rehearsal','take'),required=True)
    a=p.parse_args()
    try: capture(a.skill,a.inputs,a.output,a.phase)
    except Exception as exc:
        print(json.dumps({'status':'failed','error':str(exc),'diagnostics':str(a.output)}));return 1
    print(json.dumps({'status':'recorded_pending_review','evidence':str(a.output/'evidence.json')}));return 0


if __name__=='__main__':raise SystemExit(main())
