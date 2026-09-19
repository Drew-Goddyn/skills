#!/usr/bin/env python3
"""Browser-free review-record tests; synthetic pixel assertions are not human review."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

import beat_frames as bf
from check_evidence import validate
from review_delivery import assess, build, handoff
from test_beat_frames import beat, delivery, make_media
from test_check_evidence import save

HERE = Path(__file__).resolve().parent
AUTHOR = {'kind': 'agent', 'name': 'Automated synthetic fixture: pixel assertions only'}


def finding(state='supported', observation='Numbered blue FRAME 02 is visible in the selected synthetic frame.'):
    return {'beat_id': 'value', 'status': state,
            'author': None if state == 'unreviewed' else AUTHOR.copy(), 'relay': None,
            'observation': observation, 'coverage': 'Synthetic selected-frame pixels and sheet cell only; no human viewing.',
            'samples': [] if state == 'unreviewed' else [{'index': 'frames/frames.index.json', 'sample_id': 'beat-0001'}],
            'sheets': [] if state == 'unreviewed' else ['frames/beats-01.png']}


def make_case(root, media, scenario='supported'):
    """Reuse the accepted numbered fixtures, extractor and checker; no browser/model."""
    span = None if scenario == 'unresolved' else ([3, 3] if scenario == 'missing_frame' else
                                                ([2.75, 2.75] if scenario == 'missing_result' else [.25, .75]))
    data = delivery(root, media / 'cfr.mkv', [beat('value', span, {'take': 'take-1', 'event_index': 0})])
    data['brief'].update(takeaway='Inspect a numbered synthetic frame.',
                         decisive_moments=['FRAME 12 result' if scenario == 'missing_result' else 'FRAME 02 result'])
    data['beats'][0]['label'] = data['brief']['decisive_moments'][0]
    command = [sys.executable, str(HERE / 'check_video.py'), str(root / 'reel.mkv'),
               '--expected-size', '320x180', '--expected-fps', '4', '--audio-policy', 'forbid', '--max-duration', '3']
    check = subprocess.run(command, capture_output=True, text=True)
    save(root / 'facts/media-command.json', {'argv': command, 'returncode': check.returncode, 'stderr': check.stderr})
    if check.returncode:
        raise RuntimeError(check.stdout + check.stderr)
    report = json.loads(check.stdout)
    # Only the file path is normalized for this portable fixture.
    report['video'] = 'reel.mkv'
    save(root / 'facts/media.json', report)
    data['checks'][0].update(status='performed', report='facts/media.json',
                            context='Actual local synthetic media check; command in facts/media-command.json. Only video path normalized.')
    save(root / 'evidence.json', data)
    index = bf.build(root / 'evidence.json', root / 'frames', mode='beats')
    if index['status'] == 'error':
        raise RuntimeError(index['errors'])
    (root / 'facts/extraction-input.json').write_bytes((root / 'evidence.json').read_bytes())
    f = finding()
    if scenario == 'unreviewed':
        f = finding('unreviewed', 'Frame extracted, but no inspection was recorded.')
    elif scenario in ('unresolved', 'missing_frame'):
        f = finding('unresolved', 'No usable encoded target.' if span is None else 'Target is at the exclusive picture end; the extractor reports missing, not a clamped frame.')
    elif scenario == 'missing_result':
        f = finding('not_visible', 'The final frame is brown FRAME 11; the expected FRAME 12 result is missing from this 00–11 fixture. This is a synthetic content assertion.')
    if scenario in ('supported', 'missing_result'):
        expected = 2 if scenario == 'supported' else 11
        truth = json.loads((media / 'truth.json').read_text())['frames'][expected]
        sample = index['samples'][0]['frame']
        with Image.open(root / 'frames' / sample['path']) as image:
            assert hashlib.sha256(image.convert('RGB').tobytes()).hexdigest() == truth['rgb_sha256']
            color = image.convert('RGB').getpixel((5, 5))
        cell = index['contact_sheets'][0]['cells'][0]['image_box_xywh']
        with Image.open(root / 'frames/beats-01.png') as sheet:
            assert sheet.convert('RGB').getpixel((cell[0]+5, cell[1]+5)) == color
        save(root / 'facts/pixel-assertions.json', {'expected_input_frame': expected, 'actual_rgb_sha256': truth['rgb_sha256'],
                                                  'native_pixels_equal_numbered_input': True, 'sheet_cell_rgb': list(color)})
        data['review']['agent_frames'].update(status='performed', coverage='Automated synthetic pixel assertions and sheet-cell RGB check only; no natural-language image inspection or human viewing.',
                                              evidence=['facts/pixel-assertions.json'])
    data['review']['beat_findings'] = [f]
    data['review']['watch_list'] = [{'beat_id': 'value', 'label': data['beats'][0]['label'], 'video_seconds': span,
                                    'precision': None if span is None else 'sampled',
                                    'note': 'Synthetic final-output target. Unknown alignment remains unknown; not a completed watch.'}]
    save(root / 'evidence.json', data)
    return data


class DeliveryReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.fixture_tmp.name)
        cls.media = make_media(cls.root / 'media')
        cls.fixtures = {}
        for scenario in ('supported', 'unreviewed', 'unresolved', 'missing_result', 'missing_frame'):
            cls.fixtures[scenario] = cls.root / scenario
            make_case(cls.fixtures[scenario], cls.media, scenario)

    @classmethod
    def tearDownClass(cls):
        cls.fixture_tmp.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name) / 'delivery'
        shutil.copytree(self.fixtures['supported'], self.folder)
        self.path = self.folder / 'evidence.json'
        self.data = json.loads(self.path.read_text())

    def check(self, error=None):
        save(self.path, self.data)
        result = validate(self.path)
        self.assertEqual(result['status'], 'fail' if error else 'pass', result)
        if error:
            self.assertIn(error, result['violations'][0])
        return result

    def test_supported_pixels_and_handoff_keep_exact_requested_and_decoded_times(self):
        self.check(); result = assess(self.path)
        self.assertEqual(result['status'], 'ready_for_review')
        self.assertEqual(result['decisive_beats'][0]['resolved_samples'][0]['sample']['frame']['video_seconds'], .5)
        self.assertEqual(result['watch_list'][0]['video_seconds'], [.25, .75])
        self.assertIn('00:00.250–00:00.750 (sampled)', handoff(result))
        self.assertIn('FRAME 02', handoff(result))
        self.assertIn('not successful delivery', handoff(result))

    def test_extracted_but_unreviewed_is_structurally_valid_diagnostic(self):
        path = self.fixtures['unreviewed'] / 'evidence.json'
        self.assertEqual(validate(path)['status'], 'pass')
        result = assess(path)
        self.assertEqual(result['status'], 'diagnostic_only')
        self.assertIn('unreviewed', ' '.join(result['blockers']))

    def test_legacy_missing_findings_remain_valid_but_cannot_pass_review_readiness(self):
        del self.data['review']['beat_findings']; self.check()
        self.assertEqual(assess(self.path)['status'], 'diagnostic_only')
        self.assertIn('No per-beat finding', handoff(assess(self.path)))

    def test_unresolved_timing_preserves_driver_and_never_claims_absence(self):
        path = self.fixtures['unresolved'] / 'evidence.json'
        original = path.read_bytes(); result = assess(path)
        self.assertEqual(validate(path)['status'], 'pass')
        self.assertEqual(result['status'], 'diagnostic_only')
        self.assertIsNone(result['watch_list'][0]['video_seconds'])
        self.assertIn('not evidence the action is absent', handoff(result))
        self.assertEqual(path.read_bytes(), original)

    def test_missing_result_content_verdict_is_valid_but_blocks_handoff(self):
        path = self.fixtures['missing_result'] / 'evidence.json'
        self.assertEqual(validate(path)['status'], 'pass')
        result = assess(path)
        self.assertEqual(result['status'], 'diagnostic_only')
        self.assertEqual(result['decisive_beats'][0]['status'], 'not_visible')
        self.assertIn('FRAME 11', handoff(result)); self.assertIn('FRAME 12', handoff(result))

    def test_missing_extraction_remains_unresolved_and_cannot_support_visibility(self):
        path = self.fixtures['missing_frame'] / 'evidence.json'
        self.assertEqual(validate(path)['status'], 'pass')
        result = assess(path)
        self.assertEqual(result['status'], 'diagnostic_only')
        self.assertIsNone(result['decisive_beats'][0]['resolved_samples'][0]['sample']['frame'])
        self.data['review']['beat_findings'][0]['samples'] = []
        self.check('inspected samples')
        self.data['review']['beat_findings'][0]['samples'] = finding()['samples']
        p = self.folder / 'frames/frames.index.json'; index = json.loads(p.read_text())
        index['samples'][0].update(status='missing', frame=None); save(p, index)
        self.check('actual extracted frames')

    def test_unknown_timing_cannot_be_supported_or_declared_not_visible(self):
        self.data['beats'][0]['video_time'] = None
        self.data['review']['watch_list'][0].update(video_seconds=None, precision=None)
        for state in ('supported', 'not_visible'):
            self.data['review']['beat_findings'][0]['status'] = state
            self.check('unknown beat timing')

    def test_attribution_keeps_agent_author_human_relay_and_uncollected_human_result(self):
        f = self.data['review']['beat_findings'][0]
        f['relay'] = {'kind': 'human', 'name': 'Fixture relay'}
        self.data['review']['human'].update(status='unavailable', coverage='No direct human result collected.')
        self.check(); result = assess(self.path); rendered = handoff(result)
        self.assertEqual(result['decisive_beats'][0]['finding']['author']['kind'], 'agent')
        self.assertIn('relayed by human Fixture relay', rendered)
        self.assertIn('human: unavailable', rendered)
        f['author'] = None; self.check('reviewed findings need their author')

    def test_references_reject_wrong_reel_corrupt_frame_and_unknown_sample(self):
        index_path = self.folder / 'frames/frames.index.json'
        original = json.loads(index_path.read_text()); changed = copy.deepcopy(original)
        changed['source']['reel_sha256'] = '0'*64; save(index_path, changed)
        self.check('different reel')
        changed = copy.deepcopy(original); changed['samples'][0]['frame']['sha256'] = '0'*64; save(index_path, changed)
        self.check('frame hash'); save(index_path, original)
        self.data['review']['beat_findings'][0]['samples'][0]['sample_id'] = 'missing'
        self.check('sample is missing')

    def test_sheet_must_cover_referenced_sample(self):
        self.data['review']['beat_findings'][0]['sheets'] = ['facts/brief.txt']
        self.check('sheet must include')

    def test_visibility_author_must_agree_with_recorded_review_coverage(self):
        self.data['review']['agent_frames']['status'] = 'not_performed'
        self.check('contradicts review.agent_frames')
        self.data['review']['agent_frames']['status'] = 'performed'
        self.data['review']['beat_findings'][0]['author']['kind'] = 'human'
        self.check('contradicts review.human')

    def test_watch_list_cannot_upgrade_precision_or_substitute_driver_or_source_times(self):
        watch = self.data['review']['watch_list'][0]
        watch['video_seconds'] = [.25, .25]; self.check('final-output range and precision')
        watch['video_seconds'] = [.25, .75]; watch['precision'] = 'exact'
        self.check('final-output range and precision')

    def test_no_linked_watch_target_is_diagnostic_not_structural_failure(self):
        del self.data['review']['watch_list'][0]['beat_id']
        del self.data['review']['watch_list'][0]['precision']; self.check()
        self.assertIn('missing linked watch-list', ' '.join(assess(self.path)['blockers']))

    def test_failed_errored_unperformed_checks_and_warnings_are_preserved(self):
        report_path = self.folder / 'facts/media.json'
        report = json.loads(report_path.read_text()); report['warnings'] = ['Synthetic warning preservation control']
        save(report_path, report); self.check()
        self.assertIn(report['warnings'][0], handoff(assess(self.path)))
        report.update(status='fail', violations=['Synthetic failed-check control']); save(report_path, report)
        self.check(); result = assess(self.path)
        self.assertEqual(result['status'], 'diagnostic_only')
        self.assertEqual(result['check_results'][0]['result'], report)
        save(report_path, {'status':'error', 'error':'Synthetic checker error'}); self.check()
        self.assertEqual(assess(self.path)['status'], 'diagnostic_only')
        self.data['checks'][0].update(status='not_run', report=None); self.check()
        self.assertEqual(assess(self.path)['status'], 'diagnostic_only')

    def test_readiness_does_not_upgrade_watch_listening_human_or_privacy(self):
        self.check(); result = assess(self.path)
        self.assertEqual(result['status'], 'ready_for_review')
        self.assertEqual(result['acceptance'], 'not_established_by_this_tool')
        for key in ('continuous_watch', 'listening', 'human'):
            self.assertEqual(result['review_coverage'][key], self.data['review'][key])
        self.assertEqual(result['privacy'], self.data['privacy'])

    def test_existing_nonmedia_json_result_shape_is_preserved(self):
        raw = [{'assertion': 'invented application state', 'passed': True}]
        save(self.folder/'facts/application.json', raw)
        self.data['checks'].append({'id':'application', 'kind':'application', 'status':'performed',
                                   'report':'facts/application.json', 'context':'Synthetic nonmedia raw-result shape.'})
        self.check(); result = assess(self.path)
        self.assertEqual(result['check_results'][-1]['result'], raw)
        self.assertIn('application (application): see raw result', handoff(result))

    def test_no_decisive_beats_and_extraction_error_cannot_be_ready(self):
        self.data['beats'][0]['decisive'] = False; self.check()
        self.assertEqual(assess(self.path)['status'], 'diagnostic_only')
        self.data['beats'][0]['decisive'] = True; self.check()
        p = self.folder / 'frames/frames.index.json'; index = json.loads(p.read_text())
        index.update(status='error', errors=['Synthetic downstream extraction failure']); save(p, index)
        self.assertIn('extraction error', ' '.join(assess(self.path)['blockers']))

    def test_cli_exit_codes_real_outputs_and_no_overwrite(self):
        output = self.folder / 'handoff'
        original = self.path.read_bytes()
        def run(path, dest):
            return subprocess.run([sys.executable, str(HERE/'review_delivery.py'), str(path), str(dest)], capture_output=True, text=True)
        result = run(self.path, output); self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual((output/'HANDOFF.md').read_text(), handoff(assess(self.path)))
        self.assertEqual(json.loads((output/'review-readiness.json').read_text())['watch_list'], self.data['review']['watch_list'])
        self.assertEqual(run(self.path, output).returncode, 2)
        self.assertEqual(run(self.fixtures['unreviewed']/'evidence.json', self.folder/'diagnostic').returncode, 1)
        self.assertEqual(self.path.read_bytes(), original)
        self.data['review']['beat_findings'][0]['author'] = None; save(self.path, self.data)
        invalid = run(self.path, self.folder/'invalid'); self.assertEqual(invalid.returncode, 2)
        self.assertNotIn('Traceback', invalid.stderr)


if __name__ == '__main__':
    unittest.main()
