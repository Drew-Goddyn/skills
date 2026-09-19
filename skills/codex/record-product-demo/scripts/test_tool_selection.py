"""Check executable selection and diagnostics without tools at simulated paths."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from check_video import tool
from demo import Demo
from test_helpers import TEST_ENVIRONMENT, check_record_failures


class ToolSelection(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='demo-tool-check-')
        self.addCleanup(self.temp.cleanup)
        self.scratch = Path(self.temp.name).resolve()

    def test_explicit_browser_override_precedes_path(self):
        for override in ('/custom tools/browser', 'alternate-browser'):
            with self.subTest(override=override), patch.dict(os.environ, {'DEMO_BROWSER': override}), \
                    patch('demo.shutil.which', return_value='/path/browser') as lookup:
                self.assertEqual(Demo('test', self.scratch).command[0], override)
                lookup.assert_not_called()

    def test_browser_path_discovery_including_homebrew_is_preserved(self):
        for found in ('/simulated/bin/agent-browser', '/opt/homebrew/bin/agent-browser'):
            with self.subTest(found=found), patch.dict(os.environ, {}, clear=True), \
                    patch('demo.shutil.which', return_value=found):
                self.assertEqual(Demo('test', self.scratch).command[0], found)

    def test_browser_without_path_defers_lookup_by_command_name(self):
        # Construction must not require a browser for the deterministic recorder stubs.
        with patch.dict(os.environ, {}, clear=True), patch('demo.shutil.which', return_value=None):
            self.assertEqual(Demo('test', self.scratch).command[0], 'agent-browser')

    def test_missing_browser_has_an_actionable_error(self):
        missing = FileNotFoundError('simulated missing browser')
        with patch.dict(os.environ, {}, clear=True), patch('demo.shutil.which', return_value=None), \
                patch('demo.subprocess.run', side_effect=missing) as launch:
            with self.assertRaisesRegex(RuntimeError, 'agent-browser.*PATH.*DEMO_BROWSER') as caught:
                Demo('test', self.scratch).run('open', 'about:blank')
            self.assertIs(caught.exception.__cause__, missing)
            launch.assert_called_once()

    def test_bad_override_does_not_silently_select_another_browser(self):
        with patch.dict(os.environ, {'DEMO_BROWSER': '/custom/missing-browser'}), \
                patch('demo.shutil.which', return_value='/path/browser') as lookup, \
                patch('demo.subprocess.run', side_effect=FileNotFoundError('missing override')) as launch:
            with self.assertRaisesRegex(RuntimeError, '/custom/missing-browser.*DEMO_BROWSER'):
                Demo('test', self.scratch).run('open', 'about:blank')
            lookup.assert_not_called()
            self.assertEqual(launch.call_args.args[0][0], '/custom/missing-browser')
            launch.assert_called_once()

    def test_non_executable_browser_has_an_actionable_error(self):
        with patch.dict(os.environ, {'DEMO_BROWSER': '/custom/not-executable'}), \
                patch('demo.subprocess.run', side_effect=PermissionError('permission denied')):
            with self.assertRaisesRegex(RuntimeError, 'permissions.*DEMO_BROWSER'):
                Demo('test', self.scratch).run('open', 'about:blank')

    def test_missing_browser_start_still_leaves_the_accepted_failure_record(self):
        with patch.dict(os.environ, {}, clear=True), patch('demo.shutil.which', return_value=None), \
                patch('demo.subprocess.run', side_effect=FileNotFoundError('simulated missing browser')):
            with self.assertRaisesRegex(RuntimeError, 'PATH.*DEMO_BROWSER') as caught:
                with Demo('test', self.scratch).record('missing.webm', environment=TEST_ENVIRONMENT):
                    self.fail('recording body entered after missing browser')
        report = json.loads((self.scratch / 'missing.take.json').read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['failure_stage'], 'recorder_start')
        self.assertEqual(report['errors'], [{'type': 'RuntimeError', 'message': str(caught.exception)}])
        self.assertIsNone(report['wall_seconds'])
        self.assertIsNone(report['flow_seconds'])
        self.assertEqual(report['events'], [])
        self.assertEqual(report['recorder'], {})

    def test_accepted_record_checks_do_not_require_browser_installation(self):
        with patch.dict(os.environ, {}, clear=True), patch('demo.shutil.which', return_value=None):
            self.assertEqual(len(check_record_failures(self.scratch)), 7)

    def test_media_path_discovery_including_homebrew_is_preserved(self):
        for name in ('ffmpeg', 'ffprobe'):
            for directory in ('/simulated/bin', '/opt/homebrew/bin'):
                found = f'{directory}/{name}'
                with self.subTest(found=found), patch('check_video.shutil.which', return_value=found), \
                        patch('check_video.Path.is_file', return_value=True):
                    self.assertEqual(tool(name), found)

    def test_missing_media_tool_has_an_actionable_error(self):
        for name in ('ffmpeg', 'ffprobe'):
            with self.subTest(name=name), patch('check_video.shutil.which', return_value=None), \
                    patch('check_video.Path.is_file', return_value=False):
                with self.assertRaisesRegex(RuntimeError, name + '.*PATH'):
                    tool(name)

    def test_media_does_not_search_homebrew_outside_path(self):
        with patch('check_video.shutil.which', return_value=None), \
                patch('check_video.Path.is_file', return_value=True):
            with self.assertRaisesRegex(RuntimeError, 'ffmpeg.*PATH'):
                tool('ffmpeg')


if __name__ == '__main__':
    unittest.main()
