#!/usr/bin/env python3
"""Browser-free starter tests: real helper lifecycle with explicit stubbed browser/media."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from demo import Demo, capture_environment
from check_evidence import validate
from review_delivery import assess

SKILL=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('starter',SKILL/'templates/record_walkthrough.py')
starter=importlib.util.module_from_spec(spec);spec.loader.exec_module(starter)


def config():
    return {'url':'http://127.0.0.1:8123/?reset=1',
        'environment':{'kind':'local','url':'http://127.0.0.1:8123/?reset=1','signed_in_account_kind':'none',
                       'conditions':'Supplied invented fixture, no login; caller-verified task profile, no production indicators.',
                       'authorized_for_capture':True,'data_provenance':'invented','browser_profile_mode':'task_only','production_indicators':[]},
        'viewport':[1440,900],'selectors':{'ready':'#ready','open':'#open','action':'#value','submit':'#submit','results':'.result','identity_attribute':'data-key','blur':'h1'},
        'values':{'prefill':[{'selector':'#name','value':'Invented Label'}],'action':'42','result_contains':['Invented Label','42']},
        'labels':{'context':'Context','action':'Enter value','submit':'Submit','result':'New result'},
        'holds':{'context':0,'action':0,'result':0},
        'brief':{'text':'Supplied structure test, not a playable recording.','audience':'Test reviewer','takeaway':'Exercise the starter contract.','min_seconds':1,'max_seconds':3,'sound_policy':'forbid'},
        'source':{'revision':None,'revision_note':'Test-only supplied observations; browser and media are stubbed.'}}


class Stub(Demo):
    instances=[];start_error=None;stop_error=None;close_error=None
    def __init__(self,*args):
        super().__init__(*args);self.calls=[];self.__class__.instances.append(self)
    def run(self,*args):
        self.calls.append(args)
        if args[:2]==('record','start'):
            if self.start_error:raise self.start_error
            Path(args[2]).write_bytes(b'Structure-only test bytes, not video.')
        if args[:2]==('record','stop') and self.stop_error:raise self.stop_error
        return {}
    def clear(self):pass
    def close(self):
        self.calls.append(('close',))
        if self.close_error:raise self.close_error


class StarterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.path=self.root/'inputs.json';self.output=self.root/'delivery';self.c=config()
        Stub.instances=[];Stub.start_error=Stub.stop_error=Stub.close_error=None
        self.addCleanup(setattr,Stub,'start_error',None);self.addCleanup(setattr,Stub,'stop_error',None);self.addCleanup(setattr,Stub,'close_error',None)
    def run_capture(self,phase='take',perform=None,check=None):
        # Let the input reader, not the fixture writer, reject nonfinite values.
        self.path.write_text(json.dumps(self.c)+'\n')
        def flow(d,c,b):
            for key in ('context','action','submit','result'):d.event('beat',beat_id=key,label=c['labels'][key])
            return {'id':'new-1','text':'Invented Label 42'}
        def media(skill,out,c):
            value={'status':'pass','video':'reel.mp4','audio_policy':c['brief']['sound_policy'],'duration_seconds':2.0,
                   'picture':{'duration_seconds':2.0},'file_size_bytes':(out/'reel.mp4').stat().st_size,
                   'violations':[],'compatibility_findings':[{'code':'full_range_h264','severity':'warning','message':'Supplied policy warning'}]}
            starter.save(out/'facts/media.json',value);return value
        with patch.object(starter,'prepare',lambda d,c:d.run('open',c['url']) or []),patch.object(starter,'perform',perform or flow):
            starter.capture(SKILL,self.path,self.output,phase,helpers=SimpleNamespace(Demo=Stub,capture_environment=capture_environment),check=check or media)
    def test_inputs_and_explicit_helper_import(self):
        starter.save(self.path,self.c);self.assertEqual(starter.inputs(self.path),self.c)
        with patch.dict(sys.modules,{'demo':SimpleNamespace(Demo='wrong installed module')}):
            selected=starter.load_helpers(SKILL)
            self.assertEqual(Path(selected.__file__),SKILL/'scripts/demo.py');self.assertNotEqual(selected.Demo,'wrong installed module')
    def test_wrong_url_empty_action_prefill_and_bad_numbers_reject_before_browser(self):
        for mutation in (lambda c:c['environment'].update(url='http://elsewhere/'),lambda c:c['values'].update(action=''),
                         lambda c:c['values']['prefill'].append({'selector':'#value','value':'42'}),
                         lambda c:c['holds'].update(context=float('nan')),lambda c:c.update(viewport=[True,900])):
            with self.subTest(mutation=mutation):
                self.c=config();mutation(self.c)
                with self.assertRaises((ValueError,KeyError)):self.run_capture()
                self.assertEqual(Stub.instances,[]);self.assertFalse(self.output.exists())
    def test_environment_blocked_for_rehearsal_and_take_before_any_browser_call(self):
        for phase in ('rehearsal','take'):
            for change in ({'production_indicators':['PRODUCTION']},{'signed_in_account_kind':'unknown'},
                           {'data_provenance':None},{'browser_profile_mode':'personal'}):
                with self.subTest(phase=phase,change=change):
                    self.c=config();self.c['environment'].update(change);self.output=self.root/(phase+str(len(Stub.instances)))
                    with self.assertRaisesRegex(RuntimeError,'Please clarify'):self.run_capture(phase)
                    self.assertEqual(Stub.instances[-1].calls,[])
                    take=json.loads((self.output/'reel.take.json').read_text())
                    self.assertEqual(take['failure_stage'],'environment_check');self.assertIsNone(take['wall_seconds'])
                    self.assertEqual(take['events'],[]);self.assertFalse((self.output/'reel.mp4').exists());self.assertFalse((self.output/'evidence.json').exists())
    def test_recorder_start_failure_identity_and_owned_cleanup(self):
        error=RuntimeError('deterministic start failure');Stub.start_error=error
        with self.assertRaises(RuntimeError) as caught:self.run_capture()
        self.assertIs(caught.exception,error)
        t=json.loads((self.output/'reel.take.json').read_text());self.assertEqual(t['failure_stage'],'recorder_start')
        self.assertEqual(t['events'],[]);self.assertEqual(t['recorder'],{});self.assertIsNone(t['flow_seconds'])
        self.assertIn(('close',),Stub.instances[-1].calls);self.assertFalse((self.output/'evidence.json').exists())
    def test_flow_failure_retains_failed_take_and_primary_exception(self):
        error=AssertionError('result mismatched');Stub.close_error=RuntimeError('close failed')
        def fail(*args):raise error
        with self.assertRaises(AssertionError) as caught:self.run_capture(perform=fail)
        self.assertIs(caught.exception,error)
        self.assertEqual(json.loads((self.output/'reel.take.json').read_text())['status'],'failed')
        self.assertEqual(json.loads((self.output/'facts/cleanup.json').read_text())['status'],'unavailable')
        self.assertFalse((self.output/'evidence.json').exists())
    def test_stop_and_cleanup_failures_are_not_success(self):
        for stage in ('stop_error','close_error'):
            with self.subTest(stage=stage):
                self.output=self.root/stage;setattr(Stub,stage,RuntimeError(stage))
                with self.assertRaisesRegex(RuntimeError,stage):self.run_capture()
                self.assertEqual(json.loads((self.output/'run.json').read_text())['status'],'failed')
                self.assertFalse((self.output/'evidence.json').exists());setattr(Stub,stage,None)
    def test_generated_evidence_is_valid_but_not_reviewed_or_aligned(self):
        self.run_capture('rehearsal');d=json.loads((self.output/'evidence.json').read_text())
        self.assertEqual(validate(self.output/'evidence.json')['status'],'pass')
        self.assertEqual(d['takes'],[{'id':'rehearsal','role':'new_capture','record':'reel.take.json'}])
        self.assertTrue(all(b['video_time'] is None and b['alignment']=='unknown' and b['driver_time'] for b in d['beats']))
        self.assertEqual(d['review']['beat_findings'],[]);self.assertEqual(d['privacy']['status'],'not_performed')
        for key in ('agent_frames','continuous_watch','listening','human'):self.assertNotEqual(d['review'][key]['status'],'performed')
        self.assertEqual(assess(self.output/'evidence.json')['status'],'diagnostic_only')
        t=json.loads((self.output/'reel.take.json').read_text());self.assertEqual(t['status'],'recorded');self.assertEqual(t['playback_review'],'pending')
        self.assertEqual(t['capture_request']['environment'],self.c['environment'])
        source=json.loads((self.output/'facts/toolkit-source.json').read_text())
        self.assertEqual(source['selected_files_sha256']['scripts/demo.py'],hashlib.sha256((SKILL/'scripts/demo.py').read_bytes()).hexdigest())
    def test_media_failure_keeps_raw_warning_and_truthful_evidence(self):
        def check(skill,out,c):
            value={'status':'fail','video':'reel.mp4','audio_policy':'forbid','duration_seconds':2.0,'picture':{'duration_seconds':2},'file_size_bytes':(out/'reel.mp4').stat().st_size,
                   'violations':['Supplied media mismatch'],'warnings':['Keep me']};starter.save(out/'facts/media.json',value);return value
        with self.assertRaisesRegex(RuntimeError,'Media check failed'):self.run_capture(check=check)
        result=validate(self.output/'evidence.json');self.assertEqual(result['status'],'pass')
        self.assertEqual(result['check_results'][0]['result']['warnings'],['Keep me']);self.assertEqual(assess(self.output/'evidence.json')['status'],'diagnostic_only')
    def test_unknown_picture_measurement_never_invents_duration(self):
        def check(skill,out,c):return {'status':'error','error':'Probe failed'}
        with self.assertRaisesRegex(ValueError,'Picture duration'):self.run_capture(check=check)
        self.assertFalse((self.output/'evidence.json').exists());self.assertEqual(json.loads((self.output/'run.json').read_text())['status'],'failed')
    def test_existing_delivery_is_never_overwritten(self):
        self.run_capture();before=(self.output/'reel.take.json').read_bytes()
        with self.assertRaises(FileExistsError):self.run_capture()
        self.assertEqual(before,(self.output/'reel.take.json').read_bytes());self.assertEqual(len(Stub.instances),1)
    def test_duplicate_result_identities_fail_instead_of_guessing(self):
        for rows in ([{'id':None,'text':'42'}],[{'id':'one','text':'a'},{'id':'one','text':'b'}]):
            with self.subTest(rows=rows),self.assertRaisesRegex(ValueError,'stable, unique'):
                starter.rows(SimpleNamespace(js=lambda expr:rows),self.c['selectors'])
    def test_media_command_preserves_required_sound_and_duration_limits(self):
        self.output.mkdir();(self.output/'facts').mkdir();self.c['brief']['sound_policy']='require'
        report={'status':'error','error':'Supplied missing media diagnostic'}
        result=SimpleNamespace(returncode=2,stdout='',stderr=json.dumps(report))
        with patch.object(starter.subprocess,'run',return_value=result) as command:
            self.assertEqual(starter.media_check(SKILL,self.output,self.c),report)
        args=command.call_args.args[0]
        for flag,value in (('--audio-policy','require'),('--min-duration','1'),('--max-duration','3'),('--expected-fps','30')):
            self.assertEqual(args[args.index(flag)+1],value)
        self.assertEqual((self.output/'facts/media.stderr.txt').read_text(),result.stderr)
    def test_source_helper_files_unchanged_and_no_default_session_closed(self):
        path=SKILL/'scripts/demo.py';before=path.read_bytes();self.run_capture()
        self.assertEqual(path.read_bytes(),before)
        instance=Stub.instances[-1];self.assertTrue(instance.command[2].startswith('starter-'))
        self.assertNotIn(('close','--all'),instance.calls)


if __name__=='__main__':unittest.main()
