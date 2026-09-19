#!/usr/bin/env python3
"""Browser-free evidence tests. Dummy media tests structure, never video quality."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_evidence import validate

HERE = Path(__file__).resolve().parent


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def example(root, edit=False):
    """Small complete invented record; referenced bytes deliberately are not video."""
    d = json.loads((HERE.parent / 'templates/evidence.json').read_text())
    (root / 'facts').mkdir()
    media = root / 'reel.mp4'
    media.write_bytes(b'Structure-only test bytes; not a playable video.\n')
    d['reel'].update(sha256=hashlib.sha256(media.read_bytes()).hexdigest(), duration_seconds=2.0, size_bytes=media.stat().st_size)
    (root / 'facts/brief.txt').write_text('Show an invented value saved in a silent 1–3 second clip.')
    d['brief'].update(audience='Test reviewers',takeaway='Value saved',decisive_moments=['Save result'],duration_seconds={'min':1,'max':3})
    d['environment'].update(kind='invented fixture',signed_in_account_kind='none',conditions='No application is opened.')
    d['source'].update(revision_note='No Git revision; generated test-only fixture.')
    save(root / 'facts/source.json', {'kind':'generated test data'})
    save(root / 'facts/capture.json', {'fps':30, 'viewport':[640,360]})
    save(root / 'facts/take.json', {'status':'recorded','video':'historical/path.mp4','events':[{'at':0.25,'action':'save'}],'playback_review':'pending'})
    d['production']['capture']['context']='Simulated capture record; no browser needed.'
    d['beats'][0].update(label='Saved value', driver_time={'take':'take-1','event_index':0}, video_time={'seconds':[0.5,1.0],'precision':'sampled','basis':'Invented test sample; no offset inferred.'}, timing_note='Driver/video offset unknown; clocks are independent.')
    report={'status':'pass','video':'reel.mp4','violations':[],'duration_seconds':2.0,'file_size_bytes':media.stat().st_size,'audio_policy':'forbid','compatibility_findings':[{'code':'full_range_h264','severity':'warning','message':'Policy warning, not an observed color defect'}]}
    save(root / 'facts/media.json', report)
    d['checks'][0].update(status='performed',report='facts/media.json',context='Synthetic report; testing record consistency only.')
    for coverage in d['review'].values():
        if isinstance(coverage,dict): coverage['coverage']='Not performed in this structural test.'
    d['review']['watch_list'][0].update(label='Saved value',video_seconds=[0.5,1.0],note='Suggested review target, not a completed watch.')
    d['privacy']['coverage']='No privacy review performed; empty findings is not a pass.'
    d['limitations']=['This fixture cannot establish video quality.']
    d['toolkit']['scope']='Test fixture only';d['toolkit']['result']['reason']='No maintenance action in this fixture.'
    d['reproduction'].update(setup='Generate these test files.',created_records=['invented-value-1'])
    d['reproduction']['cleanup'].update(status='not_applicable',coverage='No browser or services started.')
    if edit:
        source=root/'input.mp4';source.write_bytes(b'Another nonvideo test fixture.\n')
        d['production']={'mode':'edit_only','capture':None,'edit':{'settings':'facts/edit.json','inputs':[{'id':'source','path':'input.mp4','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'size_bytes':source.stat().st_size,'duration_seconds':4.0}],'timeline':{'status':'known','basis':'Invented one-second trim at 1x. Encoded clocks only.','segments':[{'input':'source','source_seconds':[1.0,3.0],'output_seconds':[0.0,2.0],'speed':1.0}]}}}
        save(root/'facts/edit.json',{'operation':'trim'})
        d['takes'][0]['role']='source_capture'
    save(root/'evidence.json',d)
    return d


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.data=example(self.root)

    def check(self, data=None, contains=None):
        save(self.root/'evidence.json', self.data if data is None else data)
        result=validate(self.root/'evidence.json')
        self.assertEqual(result['status'], 'fail' if contains else 'pass', result)
        if contains: self.assertIn(contains, result['violations'][0])
        return result

    def test_capture_references_take_and_keeps_unknown_alignment(self):
        original=(self.root/'facts/take.json').read_bytes()
        self.check()
        self.assertEqual((self.root/'facts/take.json').read_bytes(),original)

    def test_failed_start_take_is_referenced_without_invented_timing(self):
        failed={'status':'failed','failure_stage':'recorder_start','capture_request':{'fps':30},
                'video':'failed.mp4','flow_seconds':None,'wall_seconds':None,'recorder':{},
                'events':[],'errors':[{'type':'RuntimeError','message':'start failed'}]}
        save(self.root/'facts/failed.take.json',failed)
        original=(self.root/'facts/failed.take.json').read_bytes()
        self.data['takes'].append({'id':'failed','role':'new_capture','record':'facts/failed.take.json'})
        self.check();self.assertEqual((self.root/'facts/failed.take.json').read_bytes(),original)

    def test_required_sound_cannot_call_listening_not_applicable(self):
        self.data['brief']['sound_policy']='require'
        self.data['checks'][0].update(status='unavailable',report=None,context='Media tools unavailable.')
        self.data['review']['listening'].update(status='not_applicable',coverage='No listening was done.')
        self.check(contains='required sound')
        self.data['review']['listening'].update(status='unavailable',coverage='Listening tool unavailable.')
        self.check()

    def test_edit_only_does_not_need_fictitious_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);example(root,edit=True)
            self.assertEqual(validate(root/'evidence.json')['status'],'pass')

    def test_edit_rejects_new_take_and_impossible_timeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=example(root,edit=True)
            d['takes'][0]['role']='new_capture';save(root/'evidence.json',d)
            self.assertIn('cannot claim a new take',validate(root/'evidence.json')['violations'][0])
            d['takes'][0]['role']='source_capture';d['production']['edit']['timeline']['segments'][0]['speed']=2
            save(root/'evidence.json',d)
            self.assertIn('spans disagree',validate(root/'evidence.json')['violations'][0])

    def test_unknown_edit_mapping_has_no_invented_segments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=example(root,edit=True)
            d['production']['edit']['timeline'].update(status='unknown',basis='Original edit map unavailable.',segments=[])
            save(root/'evidence.json',d);self.assertEqual(validate(root/'evidence.json')['status'],'pass')

    def test_incomplete_and_legacy_records_fail_as_records(self):
        del self.data['brief']['audience'];self.check(contains='brief.audience')
        result=self.check({'status':'recorded','events':[]},contains='schema_version')
        self.assertEqual(result['scope'],'evidence_structure_and_consistency_only')

    def test_version_filename_and_duplicate_keys(self):
        self.data['schema_version']=2;self.check(contains='version 1')
        self.assertIn('filename',validate(self.root/'other.json')['violations'][0])
        (self.root/'evidence.json').write_text('{"schema_version":1,"schema_version":1}')
        self.assertIn('duplicate JSON key',validate(self.root/'evidence.json')['violations'][0])

    def test_media_hash_size_and_measurement_consistency(self):
        original=copy.deepcopy(self.data)
        self.data['reel']['sha256']='0'*64;self.check(contains='does not match')
        self.data=copy.deepcopy(original);self.data['reel']['size_bytes']+=1;self.check(contains='size_bytes')
        self.data=original;self.data['reel']['duration_seconds']=3;self.check(contains='measurements disagree')

    def test_missing_file_and_path_escape(self):
        self.data['brief']['record']='facts/missing.txt';self.check(contains='file is missing')
        self.data['brief']['record']='../outside.txt';self.check(contains='relative path inside')
        (self.root/'escape').symlink_to(self.root.parent,target_is_directory=True)
        self.data['brief']['record']='escape/outside.txt';self.check(contains='escapes delivery')

    def test_clock_references_and_encoded_bounds(self):
        original=copy.deepcopy(self.data)
        self.data['beats'][0]['driver_time']['event_index']=99;self.check(contains='event index')
        self.data=copy.deepcopy(original);self.data['beats'][0]['video_time']['seconds']=[1,3];self.check(contains='outside')
        self.data=original;self.data['beats'][0].update(driver_time=None,alignment='verified');self.check(contains='both clocks')

    def test_nonfinite_boolean_and_wrong_types_fail_usefully(self):
        self.data['reel']['duration_seconds']=True;self.check(contains='finite number')
        self.data['reel']['duration_seconds']=float('nan');self.check(contains='nonfinite')
        self.data['reel']['duration_seconds']=2.0;self.data['review']=[];self.check(contains='expected an object')

    def test_warnings_and_failing_checker_results_are_preserved(self):
        report=json.loads((self.root/'facts/media.json').read_text())
        self.assertEqual(self.check()['check_results'][0]['result'],report)
        report.update(status='fail',violations=['video decode failed']);save(self.root/'facts/media.json',report)
        # A faithful failure record can be structurally valid; that never makes the reel pass.
        self.assertEqual(self.check()['check_results'][0]['result'],report)

    def test_checker_error_and_unknown_picture_span_stay_honest(self):
        report={'status':'error','error':'ffprobe could not read input'}
        save(self.root/'facts/media.json',report)
        self.assertEqual(self.check()['check_results'][0]['result'],report)
        report={'status':'fail','video':'reel.mp4','violations':['no picture timing'],'duration_seconds':2.0,
                'picture':{'duration_seconds':None},'file_size_bytes':self.data['reel']['size_bytes']}
        save(self.root/'facts/media.json',report);self.check()
        report['picture']=[];save(self.root/'facts/media.json',report);self.check(contains='report.picture')

    def test_duplicate_ids_reversed_bounds_and_empty_explanations(self):
        original=copy.deepcopy(self.data)
        self.data['beats'].append(copy.deepcopy(self.data['beats'][0]));self.check(contains='duplicate beat')
        self.data=copy.deepcopy(original);self.data['brief']['duration_seconds']={'min':3,'max':1};self.check(contains='minimum exceeds')
        self.data=original;self.data['review']['human']['coverage']='';self.check(contains='nonempty text')

    def test_checker_contradiction_and_wrong_sound_policy(self):
        report=json.loads((self.root/'facts/media.json').read_text())
        report['violations']=['broken'];save(self.root/'facts/media.json',report);self.check(contains='contradicts')
        report['violations']=[];report['audio_policy']='allow';save(self.root/'facts/media.json',report);self.check(contains='policy differs')
        report['audio_policy']='forbid';report['video']='another.mp4';save(self.root/'facts/media.json',report);self.check(contains='different reel')

    def test_not_run_check_cannot_claim_report(self):
        self.data['checks'][0]['status']='not_run';self.check(contains='unperformed')
        self.data['checks'][0]['report']=None;self.check()

    def test_unperformed_reviews_are_explicit_and_empty_findings_prove_nothing(self):
        self.check()
        for section in ['agent_frames','continuous_watch','human']:
            d=copy.deepcopy(self.data);d['review'][section]['status']='performed';self.check(d,contains='must not be empty')
        self.data['privacy']['status']='performed';self.check(contains='must not be empty')

    def test_relayed_agent_review_fixture_does_not_claim_human_viewing(self):
        fixture=json.loads((HERE/'fixtures/relayed-agent-review.json').read_text())
        self.data['review']['human']=fixture['human']
        self.data['review']['agent_frames']=fixture['agent_frames']
        save(self.root/'facts/recording-agent.json',fixture['recording_agent_report'])
        save(self.root/'facts/independent-agent.json',fixture['independent_agent_report'])
        save(self.root/'facts/sample-selection.json',fixture['sample_selection'])
        self.check()
        # Assertions about this known fixture, not a classifier for arbitrary review prose.
        self.assertEqual(self.data['review']['human']['status'],'unavailable')
        self.assertEqual(self.data['review']['human']['evidence'],[])
        recording=fixture['recording_agent_report']
        independent=fixture['independent_agent_report']
        self.assertEqual(recording['role'],'recording_agent')
        self.assertEqual(independent['role'],'independent_reviewer')
        self.assertNotEqual(recording['author'],independent['author'])
        self.assertEqual(independent['author'],{'kind':'agent','name':'ChatGPT review partner'})
        self.assertEqual(independent['relay'],{'kind':'human','name':'Drew'})
        self.assertNotIn('facts/sample-selection.json',self.data['review']['human']['evidence'])
        self.assertNotIn('facts/sample-selection.json',self.data['review']['agent_frames']['evidence'])

    def test_privacy_timing_and_watch_list_bounds(self):
        self.data['privacy']['findings']=[{'description':'Invented name','video_seconds':[0,4],'timing_note':'Test sample'}]
        self.check(contains='outside')
        self.data['privacy']['findings']=[];self.data['review']['watch_list'][0]['video_seconds']=[-1,1];self.check(contains='finite number')

    def test_toolkit_states_require_explanation_and_recoverable_work(self):
        self.data['toolkit']['status']='blocked';self.check(contains='next_action')
        self.data['toolkit']['result']['next_action']='Wait for independent review.';self.check()
        self.data['toolkit']['status']='improved';self.check(contains='changed_files')

    def test_cli_returns_structured_failure_without_traceback(self):
        self.data['beats'][0]['driver_time']['take']='missing';save(self.root/'evidence.json',self.data)
        r=subprocess.run([sys.executable,str(HERE/'check_evidence.py'),str(self.root/'evidence.json')],capture_output=True,text=True)
        self.assertEqual(r.returncode,1);self.assertEqual(r.stderr,'')
        self.assertIn('unknown take id',json.loads(r.stdout)['violations'][0])


if __name__ == '__main__':
    unittest.main()
