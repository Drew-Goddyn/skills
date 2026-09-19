"""Supplied-observation policy proof; never open a browser or claim live recognition."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from demo import Demo, capture_environment
import preflight

FIXTURES = json.loads((Path(__file__).resolve().parent.parent / 'fixtures/capture-environments.json').read_text())


class Recorder(Demo):
    def __init__(self, scratch):
        super().__init__('stub', scratch)
        self.calls = []

    def run(self, *args):
        self.calls.append(args)
        return {'stub': True}

    def clear(self):
        self.calls.append(('clear',))


class CaptureEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.environment = deepcopy(FIXTURES['base'])

    def assert_blocked(self, observed, folder='blocked'):
        recorder = Recorder(self.root / folder)
        with self.assertRaisesRegex(RuntimeError, 'Capture blocked. Please clarify') as caught:
            with recorder.record('attempt.webm', environment=observed):
                self.fail('blocked capture reached the flow body')
        self.assertEqual(recorder.calls, [])
        self.assertIsNone(recorder.started)
        report = json.loads((recorder.scratch / 'attempt.take.json').read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['failure_stage'], 'environment_check')
        self.assertEqual(report['capture_request']['environment'], observed)
        self.assertEqual(report['capture_request']['environment_check']['status'], 'blocked')
        self.assertEqual(report['errors'], [{'type': 'RuntimeError', 'message': str(caught.exception)}])
        self.assertIsNone(report['wall_seconds']); self.assertIsNone(report['flow_seconds'])
        self.assertEqual(report['events'], []); self.assertEqual(report['recorder'], {})
        self.assertEqual(report['playback_review'], 'pending')
        self.assertFalse((recorder.scratch / 'attempt.webm').exists())
        self.assertFalse((recorder.scratch / 'evidence.json').exists())
        return report

    def test_supplied_cases_block_before_any_browser_or_recorder_call(self):
        for case in FIXTURES['cases']:
            with self.subTest(case=case['id']):
                observed = dict(self.environment, **case['changes'])
                self.assertEqual(capture_environment(observed)['status'], case['expected'])
                if case['expected'] == 'blocked':
                    self.assert_blocked(observed, case['id'])
                else:
                    recorder = Recorder(self.root / case['id'])
                    with recorder.record('attempt.webm', environment=observed):
                        recorder.event('stub-action')
                    self.assertEqual(recorder.calls[0][:2], ('record', 'start'))
                    self.assertEqual(recorder.calls[-1], ('record', 'stop'))
                    report = json.loads((recorder.scratch / 'attempt.take.json').read_text())
                    self.assertEqual(report['status'], 'recorded')
                    self.assertEqual(report['capture_request']['environment'], observed)
                    self.assertEqual(report['capture_request']['environment_check'], {'status': 'allowed', 'reasons': []})
                    self.assertEqual(report['playback_review'], 'pending')

    def test_missing_observations_never_default_to_allowed(self):
        self.assert_blocked(None, 'none')
        for key in self.environment:
            with self.subTest(key=key):
                observed = self.environment.copy(); del observed[key]
                self.assert_blocked(observed, key)

    def test_omitted_record_argument_is_a_diagnostic_not_a_typeerror(self):
        recorder = Recorder(self.root)
        with self.assertRaisesRegex(RuntimeError, 'Capture blocked'):
            with recorder.record('omitted.webm'):
                self.fail('missing context started capture')
        self.assertEqual(recorder.calls, [])
        self.assertEqual(json.loads((self.root / 'omitted.take.json').read_text())['failure_stage'], 'environment_check')

    def test_localhost_and_authorization_do_not_waive_production_indicator(self):
        observed = dict(self.environment, kind='local', production_indicators=['PRODUCTION - live billing'])
        report = self.assert_blocked(observed)
        self.assertIn('PRODUCTION - live billing', report['errors'][0]['message'])

    def test_no_login_and_known_invented_realistic_names_are_eligible(self):
        self.assertEqual(self.environment['signed_in_account_kind'], 'none')
        self.assertIn('Morgan Vale', self.environment['conditions'])
        self.assertEqual(capture_environment(self.environment)['status'], 'allowed')
        for account in ('test', 'demo'):
            self.assertEqual(capture_environment(dict(self.environment, signed_in_account_kind=account))['status'], 'allowed')

    def test_unknown_or_real_data_account_profile_and_missing_inspection_block(self):
        for field, value in [('kind', 'production'), ('kind', 'unknown'), ('signed_in_account_kind', 'personal'),
                             ('data_provenance', 'real'), ('data_provenance', None),
                             ('browser_profile_mode', 'unknown'), ('production_indicators', None),
                             ('conditions', ' '), ('authorized_for_capture', 'true')]:
            with self.subTest(field=field, value=value):
                self.assertEqual(capture_environment(dict(self.environment, **{field: value}))['status'], 'blocked')

    def test_snapshot_retains_the_observations_used_at_start(self):
        recorder = Recorder(self.root)
        original = deepcopy(self.environment)
        with recorder.record('allowed.webm', environment=self.environment):
            self.environment['conditions'] = 'Later caller mutation, not a new observation.'
        report = json.loads((self.root / 'allowed.take.json').read_text())
        self.assertEqual(report['capture_request']['environment'], original)

    def test_preflight_allowance_cannot_supply_an_implicit_app_decision(self):
        recorder = Recorder(self.root)
        observed = preflight.environment('task_only')
        self.assertEqual(capture_environment(observed)['status'], 'allowed')
        self.assertEqual(observed['url'], 'data:text/html,' + preflight.quote(preflight.HTML))
        with recorder.record('preflight.webm', environment=observed):
            recorder.event('stub-preflight')
        calls = recorder.calls[:]
        with self.assertRaisesRegex(RuntimeError, 'Capture blocked'):
            with recorder.record('app-rehearsal.webm'):
                self.fail('preflight silently authorized application capture')
        self.assertEqual(recorder.calls, calls)
        report = json.loads((self.root / 'app-rehearsal.take.json').read_text())
        self.assertEqual(report['events'], []); self.assertEqual(report['recorder'], {})

    def test_preflight_unknown_or_personal_profile_blocks_before_browser_open(self):
        for mode in ('unknown', 'personal', 'attached'):
            with self.subTest(mode=mode), patch.object(sys, 'argv', ['preflight.py', str(self.root / mode), '--browser-profile-mode', mode]), \
                    patch.object(Demo, 'run', side_effect=AssertionError('browser must not be called')) as browser:
                with self.assertRaisesRegex(RuntimeError, 'task-only browser profile'):
                    preflight.main()
                browser.assert_not_called()
                report = json.loads((self.root / mode / 'preflight.take.json').read_text())
                self.assertEqual(report['failure_stage'], 'environment_check')

    def test_preflight_task_profile_reaches_recorder_with_its_own_facts(self):
        stop = RuntimeError('Stop the stub after recorder startup; no media or browser.')
        def evaluate(_demo, expression):
            if expression == preflight.MOTION:
                raise stop
        with patch.object(sys, 'argv', ['preflight.py', str(self.root), '--browser-profile-mode', 'task_only']), \
                patch.object(Demo, 'run', return_value={'stub': True}) as browser, \
                patch.object(Demo, 'js', evaluate):
            with self.assertRaises(RuntimeError) as caught:
                preflight.main()
        self.assertIs(caught.exception, stop)
        self.assertTrue(any(call.args[:2] == ('record', 'start') for call in browser.call_args_list))
        report = json.loads((self.root / 'preflight.take.json').read_text())
        self.assertEqual(report['capture_request']['environment'], preflight.environment('task_only'))
        self.assertEqual(report['capture_request']['environment_check']['status'], 'allowed')
        self.assertEqual(report['errors'], [{'type': 'RuntimeError', 'message': str(stop)}])
        self.assertFalse((self.root / 'preflight.webm').exists())

    def test_unsavable_block_diagnostic_does_not_start_capture_or_hide_reason(self):
        recorder = Recorder(self.root)
        with self.assertRaisesRegex(RuntimeError, 'Capture blocked') as caught:
            with recorder.record('missing-parent/attempt.webm'):
                self.fail('flow entered')
        self.assertIsInstance(caught.exception.__cause__, OSError)
        self.assertEqual(recorder.calls, [])


if __name__ == '__main__':
    unittest.main()
