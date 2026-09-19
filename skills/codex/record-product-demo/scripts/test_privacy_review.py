#!/usr/bin/env python3
"""Browser-free supplied-finding tests and invented media; no automatic privacy detection."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw, ImageFont

import beat_frames as bf
from check_evidence import validate
from review_delivery import assess, build, handoff
from test_beat_frames import beat, check_fixture_timing
from test_check_evidence import example, save
from test_review_delivery import VIEWER_QUESTIONS
from fractions import Fraction

HERE = Path(__file__).resolve().parent
SUPPLIED_AUTHOR = {'kind': 'agent', 'name': 'Supplied-finding test fixture; not visual inspection'}


def make_case(root, scenario):
    """Three small edited encodes. The fake notification is at output 2s or 3s."""
    root.mkdir(parents=True)
    data = example(root, edit=True)
    for path in ('reel.mp4', 'input.mp4', 'facts/capture.json', 'facts/take.json'):
        (root / path).unlink()
    images = root / 'facts/inputs'; images.mkdir()
    frames, commands = [], []
    font = ImageFont.load_default(size=24)
    small = ImageFont.load_default(size=18)
    for n in range(32):
        output = n / 4 - 2
        notification = (scenario == 'sampled_flag' and n == 16) or (scenario == 'gap' and n == 20)
        image = Image.new('RGB', (800, 450), '#f0f3f8')
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 800, 72), fill='#173553')
        draw.text((22, 23), 'INVENTED DATA / PRIVACY TEST', font=font, fill='white')
        draw.text((25, 100), 'Marin Testworks (invented)', font=font, fill='#173553')
        draw.text((25, 151), 'Amount: $248.00', font=font, fill='#173553')
        state = 'Saved invoice INV-DEMO-042' if output >= 5 else 'Amount entered' if output >= 1 else 'Draft invoice'
        draw.text((25, 310), state, font=font, fill='#173553')
        if notification:
            draw.rectangle((365, 145, 780, 270), fill='#ffcf70', outline='#8b3800', width=3)
            draw.text((382, 159), 'TEST NOTIFICATION', font=font, fill='#582000')
            draw.text((382, 204), 'DEMO_TOKEN_NOT_A_SECRET', font=small, fill='#582000')
            draw.text((382, 239), 'Synthetic test content only', font=small, fill='#582000')
        draw.text((25, 398), f'Source {n/4:.2f}s | output {output:.2f}s | frame {n:02d}', font=small, fill='#173553')
        image.save(images / f'{n:02d}.png')
        frames.append({'source_frame': n, 'source_seconds': n/4, 'output_seconds': output,
                       'notification': notification, 'rgb_sha256': hashlib.sha256(image.tobytes()).hexdigest()})
    encode = [bf.tool('ffmpeg'), '-hide_banner', '-nostdin', '-v', 'error', '-n']
    for argv in [encode + ['-framerate', '4', '-i', str(images/'%02d.png'), '-c:v', 'ffv1', '-pix_fmt', 'bgr0', '-threads', '1', str(root/'source.mkv')],
                 encode + ['-i', str(root/'source.mkv'), '-vf', 'trim=start_frame=8:end_frame=32,setpts=PTS-STARTPTS,fps=4',
                           '-fps_mode', 'passthrough', '-c:v', 'ffv1', '-pix_fmt', 'bgr0', '-threads', '1', str(root/'reel.mkv')]]:
        result = subprocess.run(argv, capture_output=True, text=True)
        commands.append({'argv': argv, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        save(root/'facts/generation.json', commands)
        if result.returncode:
            raise RuntimeError(result.stderr)
    check_fixture_timing(root/'reel.mkv', [Fraction(n,4) for n in range(24)], root/'facts/timing')
    truth = {'scenario': scenario, 'source_seconds': 8, 'output_seconds': 6, 'fps': 4, 'size': [800,450],
             'source_to_output': 'Source [2,8) -> output [0,6) at 1x; no browser or driver clock.', 'frames': frames}
    save(root/'facts/truth.json', truth)
    data['reel'] = {'path': 'reel.mkv', 'sha256': bf.digest(root/'reel.mkv'), 'duration_seconds': 6,
                    'size_bytes': (root/'reel.mkv').stat().st_size}
    data['brief'].update(takeaway='Show the invented amount and saved invoice; inspect for unintended overlays.',
                         decisive_moments=['Amount entered', 'Saved invoice'], duration_seconds={'min':6, 'max':6})
    (root/'facts/brief.txt').write_text('Invented synthetic privacy-review fixture, not an application recording. Marin Testworks is an intended invented client. Amount $248.00 and invoice INV-DEMO-042 are intended. Notifications and token-like overlays are unintended. Inspect the six-second delivered edit. No real data or credentials.\n')
    data['environment'].update(kind='synthetic images', signed_in_account_kind='none', url=None,
                               conditions='Generated locally with Pillow/FFmpeg; no browser, login or new capture. All content is invented.')
    data['source'].update(revision=None, revision_note='Generated image/encode provenance in facts/truth.json; no application or capture revision.', record='facts/truth.json')
    save(root/'facts/edit.json', {'operation':'trim', 'source_seconds':[2,8], 'output_seconds':[0,6], 'speed':1})
    data['production']['edit'].update(inputs=[{'id':'source', 'path':'source.mkv', 'sha256':bf.digest(root/'source.mkv'),
                                               'duration_seconds':8, 'size_bytes':(root/'source.mkv').stat().st_size}],
        timeline={'status':'known', 'basis':truth['source_to_output'],
                  'segments':[{'input':'source','source_seconds':[2,8],'output_seconds':[0,6],'speed':1}]})
    data['takes'] = []
    data['beats'] = [beat('amount', [1,1]), beat('saved', [5,5])]
    for b, label in zip(data['beats'], data['brief']['decisive_moments']): b['label'] = label
    data['review']['watch_list'] = [{'beat_id':b['id'], 'label':b['label'], 'video_seconds':b['video_time']['seconds'],
                                    'precision':'sampled', 'note':'Final-output point, not source time or completed viewing.'} for b in data['beats']]
    data['limitations'] = ['Synthetic still-frame sequence; no application behavior, continuous viewing, listening, human review or privacy clearance established.']
    data['reproduction'].update(setup='Generate invented PNGs, encode source, trim two-second leader, check media and extract existing beat/interval frames.', created_records=[])
    command = [sys.executable, str(HERE/'check_video.py'), str(root/'reel.mkv'), '--expected-size','800x450',
               '--expected-fps','4','--audio-policy','forbid','--min-duration','6','--max-duration','6']
    result = subprocess.run(command, capture_output=True, text=True)
    save(root/'facts/media-command.json', {'argv':command, 'returncode':result.returncode, 'stderr':result.stderr})
    if result.returncode: raise RuntimeError(result.stdout + result.stderr)
    report = json.loads(result.stdout); report['video'] = 'reel.mkv'
    save(root/'facts/media.json', report)
    data['checks'][0].update(status='performed', report='facts/media.json', context='Actual local synthetic media check; argv in facts/media-command.json. Only video path normalized.')
    save(root/'evidence.json', data)
    (root/'facts/extraction-input.json').write_bytes((root/'evidence.json').read_bytes())
    index = bf.build(root/'evidence.json', root/'frames')
    if index['status'] != 'complete': raise RuntimeError(index['errors'])
    for sample in index['samples']:
        f = sample['frame']; expected = frames[8 + f['decode_index']]
        with Image.open(root/'frames'/f['path']) as image:
            assert hashlib.sha256(image.convert('RGB').tobytes()).hexdigest() == expected['rgb_sha256']
    save(root/'facts/pixel-check.json', {'status':'pass','scope':'Lossless selected-frame RGB equality to invented inputs, not privacy detection.',
                                      'checked_samples':len(index['samples'])})
    return data


def supplied_review(root, data, with_finding=False):
    """Test inputs only. Real agent inspection is recorded separately in review examples."""
    index = json.loads((root/'frames/frames.index.json').read_text())
    refs = [{'index':'frames/frames.index.json', 'sample_id':s['sample_id']} for s in index['samples']]
    save(root/'facts/supplied-review.json', {'author':SUPPLIED_AUTHOR, 'basis':'Supplied observations exercise structure/handoff, not live recognition or agent visual review.'})
    data['review']['agent_frames'].update(status='performed', coverage='Supplied synthetic findings for automated tests only.', evidence=['facts/supplied-review.json'])
    data['review']['beat_findings'] = [{'beat_id':b['id'], 'status':'supported', 'author':SUPPLIED_AUTHOR.copy(), 'relay':None,
        'observation':b['label'] + ' is supplied as visible for this decision test.', 'coverage':'Supplied finding; generated pixels checked separately.',
        'samples':[refs[i]], 'sheets':['frames/beats-01.png']} for i,b in enumerate(data['beats'])]
    data['privacy'].update(status='performed', coverage='Two beat frames at 1/5s and interval frames at 0/2/4s. Supplied findings only; gaps remain.',
                           evidence=['facts/supplied-review.json'], author=SUPPLIED_AUTHOR.copy(), relay=None,
                           samples=refs, sheets=['frames/beats-01.png','frames/intervals-01.png'], findings=[])
    if with_finding:
        data['privacy']['findings'] = [{'description':'Unintended fake token notification in upper-right overlay; value omitted.',
            'video_seconds':[2,2], 'timing_note':'Observed sample time only; onset/end not established.', 'samples':[refs[3]]}]
    save(root/'evidence.json', data)
    return data


class PrivacyReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); cls.root = Path(cls.tmp.name)
        cls.fixtures = {}
        for scenario in ('clean','sampled_flag','gap'):
            root=cls.root/scenario; data=make_case(root,scenario); supplied_review(root,data,scenario=='sampled_flag')
            cls.fixtures[scenario]=root

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def setUp(self):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.folder=Path(tmp.name)/'delivery'; shutil.copytree(self.fixtures['clean'],self.folder)
        self.path=self.folder/'evidence.json'; self.data=json.loads(self.path.read_text())

    def check(self, error=None):
        save(self.path,self.data); result=validate(self.path)
        self.assertEqual(result['status'],'fail' if error else 'pass',result)
        if error: self.assertIn(error,result['violations'][0])
        return result

    def test_known_interval_finding_is_diagnostic_with_final_output_time_and_reference(self):
        path=self.fixtures['sampled_flag']/'evidence.json'
        self.assertEqual(validate(path)['status'],'pass')
        result=assess(path); rendered=handoff(result)
        self.assertEqual(result['status'],'diagnostic_only')
        for text in ('PRIVACY FINDINGS','00:02.000','interval-0002','upper-right','value omitted'):
            self.assertIn(text,rendered)
        self.assertNotIn('DEMO_TOKEN_NOT_A_SECRET',rendered)
        self.assertEqual(result['privacy']['findings'][0]['video_seconds'],[2,2])
        self.assertEqual(json.loads(path.read_text())['production']['edit']['timeline']['segments'][0]['source_seconds'],[2,8])

    def test_clean_invented_client_is_ready_for_review_without_clearance(self):
        self.check(); result=assess(self.path)
        self.assertEqual(result['status'],'ready_for_review')
        rendered=handoff(result)
        self.assertIn('no findings in inspected samples',rendered)
        self.assertIn('Content between inspected samples can be missed',rendered)
        self.assertIn('not privacy clearance or publication approval',rendered)
        self.assertEqual(result['acceptance'],'not_established_by_this_tool')

    def test_between_sample_notification_is_outside_coverage_not_cleared(self):
        path=self.fixtures['gap']/'evidence.json'; data=json.loads(path.read_text())
        truth=json.loads((path.parent/'facts/truth.json').read_text())
        index=json.loads((path.parent/'frames/frames.index.json').read_text())
        self.assertEqual([x['output_seconds'] for x in truth['frames'] if x['notification']],[3])
        self.assertNotIn(3,[x['frame']['video_seconds'] for x in index['samples']])
        self.assertEqual(data['privacy']['findings'],[])
        result=assess(path); self.assertEqual(result['status'],'ready_for_review')
        self.assertIn('Content between inspected samples can be missed',handoff(result))
        self.assertFalse(index['coverage']['complete_frame_coverage'])

    def test_missing_review_is_prominent_even_with_empty_findings(self):
        for status in ('not_performed','unavailable','not_applicable'):
            with self.subTest(status=status):
                self.data['privacy'].update(status=status, coverage='No inspection result collected.', evidence=[],author=None,relay=None,samples=[],sheets=[],findings=[])
                self.check(); result=assess(self.path); rendered=handoff(result)
                self.assertEqual(result['status'],'ready_for_review')
                self.assertIn('PRIVACY UNREVIEWED',rendered)
                self.assertIn(status,rendered)
                self.assertNotIn('no findings in inspected samples',rendered)

    def test_legacy_performed_without_attributed_samples_is_not_upgraded(self):
        for field in ('author','relay','samples','sheets'): self.data['privacy'].pop(field)
        self.check(); self.assertIn('PRIVACY UNREVIEWED',handoff(assess(self.path)))
        self.assertIn('recorded status: performed',handoff(assess(self.path)))

    def test_unknown_timing_finding_remains_valid_and_diagnostic(self):
        self.data['privacy'].update(status='unavailable', coverage='Relayed concern; original location and inspecting author unavailable.', evidence=[],author=None,relay=None,samples=[],sheets=[],
            findings=[{'description':'Reported notification; location unresolved.', 'video_seconds':None,'timing_note':'No encoded alignment was supplied.','samples':[]}])
        self.check(); result=assess(self.path)
        self.assertEqual(result['status'],'diagnostic_only')
        self.assertIn('time unresolved',handoff(result))
        self.assertIn('PRIVACY UNREVIEWED',handoff(result))

    def test_finding_references_must_exist_belong_to_reviewed_material_and_time_span(self):
        ref={'index':'frames/frames.index.json','sample_id':'interval-0002'}
        f={'description':'Supplied concern.', 'video_seconds':[2,2],'timing_note':'Sample point only.','samples':[ref]}
        self.data['privacy']['findings']=[f]; self.check()
        f['video_seconds']=[4,4]; self.check('supporting frame time')
        f['video_seconds']=[2,2]; ref['sample_id']='nonexistent'; self.check('sample is missing')
        ref['sample_id']='interval-0002'; self.data['privacy']['samples'].remove(ref)
        self.check('inspected privacy samples')

    def test_reviewed_samples_need_author_real_frames_and_matching_sheets(self):
        original=copy.deepcopy(self.data)
        self.data['privacy']['author']=None; self.check('inspecting author')
        self.data=copy.deepcopy(original); self.data['privacy']['sheets']=['frames/beats-01.png']; self.check('sheet must include')
        self.data=copy.deepcopy(original); self.data['privacy']['samples']=[]; self.check('inspected samples and sheets')
        self.data=copy.deepcopy(original)
        p=self.folder/'frames/frames.index.json'; index=json.loads(p.read_text()); index['samples'][2].update(status='unresolved',frame=None); save(p,index)
        self.check('actual extracted frames')

    def test_unperformed_inspection_cannot_claim_author_or_samples(self):
        self.data['privacy']['status']='not_performed'; self.check('unperformed privacy review')

    def test_bad_frame_hash_or_reel_identity_is_rejected(self):
        p=self.folder/'frames/frames.index.json'; index=json.loads(p.read_text())
        original=copy.deepcopy(index)
        index['source']['reel_sha256']='0'*64; save(p,index); self.check('different reel')
        index=original
        index['samples'][3]['frame']['sha256']='0'*64; save(p,index); self.check('frame hash')

    def test_legacy_finding_blocks_clean_claim_without_requiring_new_fields(self):
        for key in ('author','relay','samples','sheets'): self.data['privacy'].pop(key)
        self.data['privacy']['findings']=[{'description':'Historical reported concern; original inspector uncollected.',
                                         'video_seconds':None,'timing_note':'Unknown final-output location.'}]
        self.check(); result=assess(self.path)
        self.assertEqual(result['status'],'diagnostic_only')
        self.assertIn('PRIVACY UNREVIEWED',handoff(result))
        self.assertIn('time unresolved',handoff(result))

    def test_partial_extension_and_duplicate_samples_are_rejected(self):
        original=copy.deepcopy(self.data)
        del self.data['privacy']['relay']; self.check('required field')
        self.data=original
        self.data['privacy']['samples'].append(copy.deepcopy(self.data['privacy']['samples'][0]))
        self.check('duplicate inspected sample')

    def test_generated_handoffs_preserve_warnings_optional_questions_and_relay(self):
        self.data['privacy']['relay']={'kind':'human','name':'Fixture relay'}
        self.data['review']['human'].update(status='unavailable',coverage='No direct human viewing result collected.')
        rp=self.folder/'facts/media.json'; report=json.loads(rp.read_text()); report['warnings']=['Supplied warning preservation control']; save(rp,report)
        for flagged in (False,True):
            with self.subTest(flagged=flagged):
                if flagged: self.data['privacy']['findings']=[{'description':'Concern with unknown extent.', 'video_seconds':None,'timing_note':'Unknown timing.','samples':[]}]
                self.check(); before=self.path.read_bytes()
                out=self.folder/str(flagged); result=build(self.path,out); rendered=(out/'HANDOFF.md').read_text()
                self.assertEqual(result['status'],'diagnostic_only' if flagged else 'ready_for_review')
                self.assertEqual(result['check_results'][0]['result'],report)
                for text in (*VIEWER_QUESTIONS,'relayed by human Fixture relay','agent author:','Supplied warning preservation control',
                             'human: unavailable. No direct human viewing result collected.','continuous_watch: not_performed','listening: not_performed'):
                    self.assertIn(text,rendered)
                self.assertEqual(self.path.read_bytes(),before)
                self.assertEqual(set(p.name for p in out.iterdir()),{'HANDOFF.md','review-readiness.json'})
                self.assertEqual(json.loads((out/'review-readiness.json').read_text())['privacy'],self.data['privacy'])

    def test_cli_known_finding_is_nonzero_and_unreviewed_record_remains_structurally_valid(self):
        result=subprocess.run([sys.executable,str(HERE/'review_delivery.py'),str(self.fixtures['sampled_flag']/'evidence.json'),str(self.folder/'cli')],capture_output=True,text=True)
        self.assertEqual(result.returncode,1,result.stdout)
        self.assertEqual(json.loads(result.stdout)['status'],'diagnostic_only')


if __name__=='__main__': unittest.main()
