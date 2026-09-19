#!/usr/bin/env python3
"""Structure/wording tests with supplied records, not media QA or fresh-agent compliance."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_evidence import validate
from review_delivery import assess, build, handoff, VIEWER_CHECKPOINT_QUESTIONS
from test_check_evidence import example, save

HERE = Path(__file__).resolve().parent


def toolkit_record(root, scenario):
    """Representative supplied maintenance states, independent of reel readiness."""
    context = {'kind':'supplied_maintenance_example', 'scenario':scenario,
               'limits':'Illustrates record semantics only. No source fix, skill installation, maintenance agent or fresh recording is performed by this fixture.'}
    save(root/'facts/friction.json',context)
    base = {'status':'pending', 'friction':[{'issue':'Supplied example: a task-local selector adaptation exposed possible reusable friction; shared failure is not established.', 'evidence':'facts/friction.json'}],
            'owner':'current_task', 'scope':'Record friction only; maintenance is not assigned.',
            'result':{'reason':'Recording uses existing supported capabilities and authorized task-local adaptations. Shared source and loaded copies are unchanged; review/publication/installation are not performed.',
                      'changed_files':[], 'checks':[], 'tool_version':None,
                      'discovery':'Current pinned recording copy remains the active route; no toolkit improvement is claimed.',
                      'next_action':'Preserve the finding for a separate bounded maintenance assignment; continue the reel if its own checks permit.'}}
    if scenario == 'source_unavailable':
        base.update(status='blocked',scope='Explicitly authorized maintenance example; source checkout and sufficient original source basis are unavailable.')
        base['result'].update(reason='No verified source checkout or trustworthy source basis is available. Finding retained; no patch, applied improvement, publication or installation claimed.',
                              next_action='Obtain the intended source checkout or verified original source bytes/revision before proposing a fix.')
    elif scenario == 'portable_patch':
        # Tiny illustrative patch, deliberately never applied to an installed copy.
        (root/'facts/proposed.patch').write_text('--- a/helper.txt\n+++ b/helper.txt\n@@ -1 +1 @@\n-old illustrative wording\n+new illustrative wording\n')
        save(root/'facts/patch-basis.json',{'kind':'supplied_basis_example','base_revision':None,
                                         'original_sha256':hashlib.sha256(b'old illustrative wording\n').hexdigest(),
                                         'original_bytes':'old illustrative wording\n','patch':'facts/proposed.patch',
                                         'limits':'Illustrative patch format, not a fix to the real recording toolkit.'})
        base.update(status='blocked',scope='Authorized maintenance example with frozen original bytes but no source checkout.')
        base['friction'].append({'issue':'Portable proposal retained against the supplied original bytes; not applied.', 'evidence':'facts/patch-basis.json'})
        base['result'].update(reason='Proposed patch only, retained at facts/proposed.patch. No shared source change, runtime verification, review, publication or installation claimed.',
                              tool_version='Supplied original-byte identity in facts/patch-basis.json; repository revision unavailable.',
                              next_action='Locate and verify the intended source checkout, apply/review the proposal there, and run the relevant checks before publication.')
    elif scenario == 'authorized_source':
        base.update(status='running',scope='Explicitly authorized source-maintenance example; local source tested, required independent review pending.')
        save(root/'facts/source-checks.json',{'kind':'supplied_source_test_result','status':'pass',
                                           'limits':'Representative state, not an assertion that this fixture performed source maintenance.'})
        base['result'].update(reason='Supplied example: source change applied and locally tested in a verified checkout. Independent review pending; publication not performed; installed copy unchanged.',
                              changed_files=['scripts/example-helper.py'],checks=['facts/source-checks.json'],
                              tool_version='Supplied candidate source identity; installed identity is separate and unchanged.',
                              discovery='Candidate source entrypoint only. Normal installed recording route remains unchanged until a separately authorized installation.',
                              next_action='Hand off the bounded source diff and proof for independent review; publish only after acceptance under the assignment authority.')
    elif scenario != 'recording_friction':
        raise ValueError(scenario)
    return base


def structural_delivery(root):
    """Reuse the standard dummy record; refs test JSON contracts, not frame content."""
    data=example(root)
    frames=root/'frames';frames.mkdir()
    (frames/'frame.bin').write_bytes(b'Structure-only frame stand-in, not decoded media.\n')
    (frames/'sheet.bin').write_bytes(b'Structure-only sheet stand-in, not an image.\n')
    index={'schema_version':1,'scope':'encoded_frame_extraction_only','status':'complete',
           'source':{'reel_sha256':data['reel']['sha256']},
           'samples':[{'sample_id':'beat-0001','status':'extracted','frame':{'path':'frame.bin','sha256':hashlib.sha256((frames/'frame.bin').read_bytes()).hexdigest(),'video_seconds':.5}}],
           'contact_sheets':[{'path':'sheet.bin','cells':[{'sample_id':'beat-0001'}]}]}
    save(frames/'frames.index.json',index)
    (root/'facts/supplied-review.txt').write_text('Supplied structure-test finding, not visual inspection or real media verification.\n')
    data['review']['agent_frames'].update(status='performed',coverage='Supplied structural test only.',evidence=['facts/supplied-review.txt'])
    data['review']['human'].update(status='unavailable',coverage='No direct human viewing result collected.')
    data['review']['beat_findings']=[{'beat_id':'action','status':'supported',
        'author':{'kind':'agent','name':'Supplied record test; no visual inspection'},'relay':{'kind':'human','name':'Fixture relay'},
        'observation':'Supplied decisive-finding input for handoff decisions only.','coverage':'Structure-only stand-ins, no viewing claim.',
        'samples':[{'index':'frames/frames.index.json','sample_id':'beat-0001'}],'sheets':['frames/sheet.bin']}]
    data['review']['watch_list'][0].update(beat_id='action',precision='sampled')
    data['toolkit']=toolkit_record(root,'recording_friction');save(root/'evidence.json',data)
    return data


class ToolkitHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.path=self.root/'evidence.json'
        self.data=structural_delivery(self.root)

    def check(self):
        save(self.path,self.data);result=validate(self.path)
        self.assertEqual(result['status'],'pass',result)
        return assess(self.path)

    def test_pending_friction_is_visible_without_delaying_ready_record(self):
        result=self.check();self.assertEqual(result['status'],'ready_for_review')
        self.assertEqual(result.get('toolkit'),self.data['toolkit'])
        text=handoff(result)
        for value in ('Toolkit follow-up','pending','current_task',self.data['toolkit']['friction'][0]['issue'],self.data['toolkit']['result']['next_action']):
            self.assertIn(value,text)

    def test_unavailable_source_and_portable_proposal_remain_blocked_not_installed(self):
        for scenario in ('source_unavailable','portable_patch'):
            with self.subTest(scenario=scenario):
                self.data['toolkit']=toolkit_record(self.root,scenario);result=self.check()
                self.assertEqual(result['status'],'ready_for_review')
                self.assertEqual(result.get('toolkit'),self.data['toolkit'])
                self.assertEqual(result['toolkit']['status'],'blocked')
                self.assertEqual(result['toolkit']['result']['changed_files'],[])
                self.assertIn(self.data['toolkit']['result']['reason'],handoff(result))
                self.assertNotIn('installed_status',result['toolkit'])

    def test_source_candidate_pending_review_is_running_with_explicit_installation_gap(self):
        self.data['toolkit']=toolkit_record(self.root,'authorized_source');result=self.check()
        self.assertEqual(result.get('toolkit'),self.data['toolkit'])
        self.assertEqual(result['toolkit']['status'],'running')
        for key in ('reason','tool_version','discovery','next_action'):
            self.assertIn(self.data['toolkit']['result'][key],handoff(result))

    def test_maintenance_status_never_erases_actual_delivery_blockers(self):
        pristine=copy.deepcopy(self.data)
        for issue in ('media','decisive','privacy'):
            for state in ('pending','blocked','running','improved'):
                with self.subTest(issue=issue,state=state):
                    self.data=copy.deepcopy(pristine)
                    self.data['toolkit']=toolkit_record(self.root,'authorized_source')
                    self.data['toolkit']['status']=state
                    if state=='improved':
                        self.data['toolkit']['result']['reason']='Supplied completed source-maintenance state; required source review/publication complete; installed copy unchanged.'
                    if issue=='media':self.data['checks'][0].update(status='not_run',report=None,context='Supplied media-blocker control.')
                    elif issue=='decisive':self.data['review']['beat_findings'][0].update(status='unreviewed',author=None,relay=None,samples=[],sheets=[])
                    else:self.data['privacy']['findings']=[{'description':'Supplied privacy concern.', 'video_seconds':None,'timing_note':'Location unknown.'}]
                    result=self.check();self.assertEqual(result['status'],'diagnostic_only')
                    self.assertTrue(result['blockers']);self.assertEqual(result.get('toolkit'),self.data['toolkit'])
                    for blocker in result['blockers']: self.assertIn(blocker,handoff(result))

    def test_preserves_warnings_questions_attribution_and_review_gaps(self):
        result=self.check();before=copy.deepcopy(result);text=handoff(result)
        for s in (*VIEWER_CHECKPOINT_QUESTIONS,'Policy warning, not an observed color defect',
                  'agent author: Supplied record test; no visual inspection','relayed by human Fixture relay',
                  'human: unavailable. No direct human viewing result collected.','PRIVACY UNREVIEWED'):
            self.assertIn(s,text)
        self.assertEqual(result,before)

    def test_no_maintenance_status_is_automatically_promoted(self):
        self.data['toolkit']=toolkit_record(self.root,'authorized_source')
        for state in ('pending','running','blocked','improved','no_change'):
            self.data['toolkit']['status']=state
            if state=='improved':
                self.data['toolkit']['result']['reason']='Supplied completed source-maintenance state; installed copy unchanged.'
            result=self.check();self.assertEqual(result.get('toolkit'),self.data['toolkit'])
            self.assertEqual(result['acceptance'],'not_established_by_this_tool')

    def test_existing_validator_rejects_empty_improvement_and_missing_next_action(self):
        self.data['toolkit']['status']='improved';save(self.path,self.data)
        self.assertEqual(validate(self.path)['status'],'fail')
        self.data['toolkit']['status']='pending';self.data['toolkit']['result']['next_action']=None;save(self.path,self.data)
        self.assertEqual(validate(self.path)['status'],'fail')

    def test_cli_outputs_recorded_toolkit_without_mutation(self):
        self.check();before=self.path.read_bytes();dest=self.root/'handoff'
        p=subprocess.run([sys.executable,str(HERE/'review_delivery.py'),str(self.path),str(dest)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout)
        self.assertEqual(json.loads((dest/'review-readiness.json').read_text()).get('toolkit'),self.data['toolkit'])
        self.assertEqual((dest/'HANDOFF.md').read_text(),handoff(assess(self.path)))
        self.assertEqual(self.path.read_bytes(),before)


if __name__=='__main__':unittest.main()
