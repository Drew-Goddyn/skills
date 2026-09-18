#!/usr/bin/env python3
"""Browser-free frame selection tests with lossless, numbered/color-coded media."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFont

import beat_frames as bf
from test_check_evidence import example, save
from check_evidence import validate

HERE = Path(__file__).resolve().parent
COLORS = [(210, 45, 45), (35, 170, 75), (45, 85, 210), (210, 165, 30),
          (175, 50, 180), (20, 170, 180), (235, 105, 35), (85, 65, 185),
          (120, 165, 45), (205, 65, 120), (40, 125, 155), (115, 100, 75)]


def check_fixture_timing(video, expected_times, output):
    """Require the positive fixture's declared timing before exercising selection."""
    output.mkdir(parents=True, exist_ok=False)
    report = {'fixture':video.name, 'status':'error',
              'expected_raw_seconds':[str(t) for t in expected_times]}
    try:
        frames, starts, ends, info = bf.probe_frames(video, output)
        actual_times = [f['pts'] * Fraction(f['time_base']) for f in frames]
        if actual_times != expected_times:
            raise ValueError(f'Expected raw frame times {expected_times}; got {actual_times}')
        # This is a generator assertion about known inputs, never a runtime fallback.
        duration = ends[-1] - starts[-1]
        if duration != Fraction(1, 4):
            raise ValueError(f'Expected an explicit final frame duration of 1/4 s; got {duration}')
        report.update(status='pass', decoded_frames=len(frames), time_base=info['time_base'],
                      raw_seconds=[str(t) for t in actual_times],
                      final_decoded_duration_seconds=float(duration))
    except (ValueError, RuntimeError, OSError, KeyError) as exc:
        message = (f'Positive fixture {video.name} failed timing sanity: {exc}. '
                   f'Fix fixture generation; do not infer the endpoint. See {output}/probe.json')
        report['error'] = message
        raise RuntimeError(message) from exc
    finally:
        save(output/'check.json', report)
    return report


def make_media(root):
    """Keep these tiny inputs, truth table and encodes for independent reproduction."""
    root.mkdir(parents=True, exist_ok=False)
    (root/'inputs').mkdir()
    truth = []
    font = ImageFont.load_default(size=30)
    for n, color in enumerate(COLORS):
        image = Image.new('RGB', (320, 180), color)
        draw = ImageDraw.Draw(image)
        draw.rectangle((65, 65, 255, 115), fill='black')
        draw.text((78, 72), f'FRAME {n:02d}', font=font, fill='white')
        path = root/'inputs'/f'{n:02d}.png'; image.save(path)
        truth.append({'frame':n, 'seconds':n/4, 'rgb':list(color),
                      'rgb_sha256':hashlib.sha256(image.tobytes()).hexdigest(),
                      'input':path.relative_to(root).as_posix()})
    save(root/'truth.json', {'size':[320,180], 'fps':4, 'end_exclusive_seconds':3,
                            'frames':truth, 'offset_seconds':5,
                            'vfr_input_frames':[0,2,3,7], 'edit_input_frames':[8,9,10,11]})
    commands = []
    # FFmpeg 7's setpts can clear duration/rate metadata. These two positive
    # fixtures have a known 4 fps cadence: fps restores explicit frame durations.
    # Keep passthrough output and the variable-spacing recipe unchanged.
    for name, filters in [('cfr',None), ('offset','setpts=PTS+5/TB,fps=4'),
                          ('vfr',r'select=eq(n\,0)+eq(n\,2)+eq(n\,3)+eq(n\,7)'),
                          ('edit','trim=start_frame=8:end_frame=12,setpts=PTS-STARTPTS,fps=4')]:
        command = [bf.tool('ffmpeg'), '-hide_banner', '-nostdin', '-v', 'error', '-n',
                   '-framerate', '4', '-i', str(root/'inputs/%02d.png')]
        if filters:
            command += ['-vf',filters]
        command += ['-fps_mode','passthrough','-c:v','ffv1','-pix_fmt','bgr0',
                    '-threads','1',str(root/f'{name}.mkv')]
        result = subprocess.run(command, capture_output=True, text=True)
        commands.append({'argv':command, 'returncode':result.returncode,
                         'stdout':result.stdout, 'stderr':result.stderr})
        save(root/'generation.json', commands)
        if result.returncode:
            raise RuntimeError(result.stderr)
        indices = [0,2,3,7] if name=='vfr' else range(4 if name=='edit' else 12)
        expected = [Fraction(n, 4) + (5 if name=='offset' else 0) for n in indices]
        check_fixture_timing(root/f'{name}.mkv', expected, root/'timing'/name)
    return root


def beat(bid, span, driver=None, precision='sampled'):
    return {'id':bid, 'kind':'result', 'label':f'Inspect {bid}', 'decisive':True,
            'driver_time':driver,
            'video_time':None if span is None else {'seconds':span, 'precision':precision,
                                                   'basis':'Synthetic output clock; no driver offset inferred.'},
            'alignment':'unknown', 'timing_note':'Independent encoded and driver clocks.'}


def delivery(root, media, beats):
    """Reuse the evidence test's structural fixture; replace dummy reel with real media."""
    root.mkdir()
    data = example(root)
    (root/'reel.mp4').unlink()
    shutil.copyfile(media, root/'reel.mkv')
    duration = 1 if media.stem=='edit' else (2 if media.stem=='vfr' else 3)
    data['reel'].update(path='reel.mkv', sha256=bf.digest(root/'reel.mkv'),
                        size_bytes=media.stat().st_size, duration_seconds=duration)
    data['brief']['duration_seconds']={'min':0, 'max':3}
    data['beats']=beats
    data['review']['watch_list']=[{'label':'Inspect synthetic frame labels', 'video_seconds':None,
                                 'note':'No viewing performed; targets are supplied by each test.'}]
    # No invented checker pass: extraction is the experiment here.
    data['checks'][0].update(status='not_run', report=None,
                            context='Media-check suite not run for this frame selection fixture.')
    data['source']['revision_note']='Generated numbered/color-coded frames; see synthetic truth.json.'
    save(root/'evidence.json', data)
    return data


class BeatFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_tmp = tempfile.TemporaryDirectory()
        cls.media = make_media(Path(cls.fixture_tmp.name)/'media')
        cls.truth = json.loads((cls.media/'truth.json').read_text())['frames']

    @classmethod
    def tearDownClass(cls):
        cls.fixture_tmp.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def run_case(self, beats, media='cfr', mode='beats', interval=Fraction(2)):
        delivery(self.root/'delivery', self.media/f'{media}.mkv', beats)
        result = bf.build(self.root/'delivery/evidence.json', self.root/'output', mode, interval)
        return result

    def assertFrame(self, entry, expected):
        self.assertEqual(entry['status'],'extracted',entry)
        frame = entry['frame']
        with Image.open(self.root/'output'/frame['path']) as image:
            self.assertEqual(image.size,(320,180))
            self.assertEqual(hashlib.sha256(image.convert('RGB').tobytes()).hexdigest(),
                             self.truth[expected]['rgb_sha256'])
        self.assertEqual(frame['sha256'],bf.digest(self.root/'output'/frame['path']))

    def test_midpoint_and_exact_frame_boundary_select_actual_pixels(self):
        result = self.run_case([beat('midpoint',[.25,.75]), beat('boundary',[.25,.25]),
                                beat('just-before',[.249999,.249999]), beat('first',[0,0])])
        self.assertEqual(result['status'],'complete',result['errors'])
        for entry, expected in zip(result['samples'], [2,1,0,0]):
            self.assertFrame(entry,expected)
            self.assertEqual(entry['frame']['video_seconds'],expected/4)
        self.assertEqual(result['samples'][0]['requested_seconds'],.5)
        self.assertEqual(result['samples'][2]['requested_seconds'],.249999)

    def test_picture_end_is_exclusive_and_never_clamped(self):
        spans = [[2.999,2.999],[3,3],[3.01,3.01],[-.01,-.01],[-.1,.5],[2.5,3.1],[2.5,3]]
        result = self.run_case([beat(str(i),span) for i,span in enumerate(spans)])
        self.assertEqual(result['status'],'partial')
        self.assertFrame(result['samples'][0],11)
        self.assertFrame(result['samples'][-1],11)
        for entry in result['samples'][1:-1]:
            self.assertEqual(entry['status'],'missing')
            self.assertIsNone(entry['frame'])
            self.assertEqual(entry['reason'],'outside_decoded_picture_span')
        self.assertEqual(len(result['contact_sheets']),2)

    def test_unknown_timing_stays_unresolved_and_inputs_unchanged(self):
        data = delivery(self.root/'delivery',self.media/'cfr.mkv',
                        [beat('unknown',None,{'take':'take-1','event_index':0})])
        before = {p: p.read_bytes() for p in (self.root/'delivery').rglob('*') if p.is_file()}
        result = bf.build(self.root/'delivery/evidence.json',self.root/'output','beats')
        entry = result['samples'][0]
        self.assertEqual(result['status'],'partial')
        self.assertEqual(entry['status'],'unresolved')
        self.assertIsNone(entry['requested_seconds']); self.assertIsNone(entry['frame'])
        self.assertEqual(entry['driver_time'],data['beats'][0]['driver_time'])
        self.assertEqual(entry['alignment'],'unknown')
        self.assertEqual({p:p.read_bytes() for p in before}, before)
        self.assertFalse((self.root/'output/frames').exists())

    def test_approximate_timing_is_not_upgraded_by_exact_frame_timestamp(self):
        result = self.run_case([beat('approximate',[.4,.7],precision='approximate')])
        self.assertFrame(result['samples'][0],2)
        self.assertEqual(result['samples'][0]['video_time']['precision'],'approximate')
        self.assertEqual(result['samples'][0]['alignment'],'unknown')

    def test_two_second_default_explicit_coverage_without_privacy_claim(self):
        result = self.run_case([],mode='both')
        self.assertEqual(result['status'],'complete',result['errors'])
        self.assertEqual(result['coverage']['interval_requested_seconds'],[0,2])
        for entry, expected in zip(result['samples'],[0,8]): self.assertFrame(entry,expected)
        self.assertEqual(result['coverage']['unique_extracted_frames'],2)
        self.assertEqual(result['coverage']['decoded_frames_not_extracted'],10)
        self.assertFalse(result['coverage']['complete_frame_coverage'])
        self.assertEqual(result['review_judgments'],'not_performed')
        self.assertEqual(result['coverage']['privacy_clearance'],'not_established')

    def test_custom_intervals_do_not_force_last_frame(self):
        result = self.run_case([],mode='intervals',interval=Fraction(1,2))
        self.assertEqual(result['coverage']['interval_requested_seconds'],[0,.5,1,1.5,2,2.5])
        for entry, expected in zip(result['samples'],range(0,12,2)): self.assertFrame(entry,expected)

    def test_variable_frame_spacing_uses_presented_frame_not_nominal_fps(self):
        result = self.run_case([beat('held',[.4,.4]), beat('next',[.5,.5]),
                               beat('held-later',[1.5,1.5]),beat('tail',[1.99,1.99])],media='vfr')
        self.assertEqual(result['status'],'complete',result['errors'])
        for entry, expected, time in zip(result['samples'],[0,2,3,7],[0,.5,.75,1.75]):
            self.assertFrame(entry,expected)
            self.assertEqual(entry['frame']['video_seconds'],time)
        self.assertEqual(result['video']['duration_seconds'],2)

    def test_nonzero_stream_origin_retains_raw_and_relative_timestamps(self):
        result = self.run_case([beat('offset',[.25,.25])],media='offset')
        self.assertEqual(result['status'],'complete',result)
        self.assertEqual(result['video']['origin_seconds'],5)
        self.assertFrame(result['samples'][0],1)
        self.assertEqual(result['samples'][0]['frame']['video_seconds'],.25)
        self.assertEqual(result['samples'][0]['frame']['timestamp_seconds'],5.25)

    def test_edit_uses_output_times_without_reinterpreting_driver_or_map(self):
        data=delivery(self.root/'delivery',self.media/'edit.mkv',
                      [beat('edited',[.25,.25],{'take':'take-1','event_index':0})])
        source=self.root/'delivery/input.mkv'; shutil.copyfile(self.media/'cfr.mkv',source)
        save(self.root/'delivery/facts/edit.json',{'trim_source_seconds':[2,3]})
        data['production']={'mode':'edit_only','capture':None,'edit':{
            'settings':'facts/edit.json', 'inputs':[{'id':'source','path':'input.mkv',
                'sha256':bf.digest(source),'size_bytes':source.stat().st_size,'duration_seconds':3}],
            'timeline':{'status':'known','basis':'Keep source frames 8 through 11, at 1x.',
                        'segments':[{'input':'source','source_seconds':[2,3],
                                     'output_seconds':[0,1],'speed':1}]}}}
        data['takes'][0]['role']='source_capture'
        save(self.root/'delivery/evidence.json',data)
        validation=validate(self.root/'delivery/evidence.json')
        self.assertEqual(validation['status'],'pass',validation)
        before=(self.root/'delivery/evidence.json').read_bytes()
        result=bf.build(self.root/'delivery/evidence.json',self.root/'output','beats')
        self.assertEqual(result['status'],'complete',result)
        self.assertFrame(result['samples'][0],9)
        self.assertEqual(result['samples'][0]['frame']['video_seconds'],.25)
        self.assertEqual(result['samples'][0]['alignment'],'unknown')
        self.assertEqual((self.root/'delivery/evidence.json').read_bytes(),before)

    def test_fixture_sanity_names_missing_duration_before_selection(self):
        # Exercise the missing metadata reported by independent review, without
        # pretending this stub is a second FFmpeg toolchain.
        def durationless_probe(command, **kwargs):
            return subprocess.CompletedProcess(command,0,json.dumps({
                'streams':[{'index':0,'time_base':'1/1000'}],
                'frames':[{'pts':5000},{'pts':5250}]}),'')
        with patch.object(bf.subprocess,'run',side_effect=durationless_probe):
            with self.assertRaisesRegex(RuntimeError,
                    r'Positive fixture offset.mkv failed timing sanity: Last decoded frame duration is unknown'):
                check_fixture_timing(self.media/'offset.mkv', [Fraction(5),Fraction(21,4)], self.root/'sanity')
        report=json.loads((self.root/'sanity/check.json').read_text())
        self.assertEqual(report['status'],'error')
        self.assertIn('do not infer the endpoint',report['error'])

    def test_generated_fixtures_retain_every_numbered_rgb_frame(self):
        for name, indices in [('cfr',range(12)),('offset',range(12)),
                              ('vfr',[0,2,3,7]),('edit',range(8,12))]:
            with self.subTest(fixture=name):
                command=[bf.tool('ffmpeg'),'-hide_banner','-nostdin','-v','error','-i',
                         str(self.media/f'{name}.mkv'),'-map','0:v:0','-fps_mode','passthrough',
                         '-f','rawvideo','-pix_fmt','rgb24','pipe:1']
                result=subprocess.run(command,capture_output=True)
                self.assertEqual(result.returncode,0,result.stderr.decode())
                size=320*180*3
                self.assertEqual(len(result.stdout),len(indices)*size)
                for output_frame, source_frame in enumerate(indices):
                    pixels=result.stdout[output_frame*size:(output_frame+1)*size]
                    self.assertEqual(hashlib.sha256(pixels).hexdigest(),self.truth[source_frame]['rgb_sha256'])

    def test_contact_sheet_contains_selected_pixels_at_declared_boxes(self):
        beats=[beat(str(n),[n/4,n/4]) for n in range(7)]
        beats[0]['label']='Long label '*30
        result=self.run_case(beats)
        self.assertEqual(len(result['contact_sheets']),2)
        for sheet in result['contact_sheets']:
            with Image.open(self.root/'output'/sheet['path']) as image:
                self.assertEqual(image.size,(sheet['width'],sheet['height']))
                for cell in sheet['cells']:
                    n=int(cell['sample_id'].split('-')[1])-1
                    x,y,w,h=cell['image_box_xywh']
                    self.assertEqual((w,h),(320,180))
                    self.assertEqual(image.getpixel((x+2,y+2)),COLORS[n])
                    self.assertLessEqual(y+h,image.height)

    def test_missing_extracted_png_never_gets_another_frames_path(self):
        delivery(self.root/'delivery',self.media/'cfr.mkv',[beat('a',[0,0]),beat('b',[1,1])])
        run=subprocess.run
        def remove_one_after_real_extraction(command, **kwargs):
            result=run(command,**kwargs)
            if Path(command[0]).name=='ffmpeg':
                (self.root/'output/frames/frame-000001.png').unlink()
            return result
        with patch.object(bf.subprocess,'run',side_effect=remove_one_after_real_extraction):
            result=bf.build(self.root/'delivery/evidence.json',self.root/'output','beats')
        self.assertEqual(result['status'],'error')
        self.assertIn('count mismatch',result['errors'][0])
        for entry in result['samples']:
            self.assertEqual(entry['status'],'missing'); self.assertIsNone(entry['frame'])

    def test_probe_without_final_duration_fails_without_guessed_endpoint(self):
        def incomplete_probe(command, **kwargs):
            return subprocess.CompletedProcess(command,0,json.dumps({
                'streams':[{'index':0,'time_base':'1/4'}], 'frames':[{'pts':0}]}),'')
        delivery(self.root/'delivery',self.media/'cfr.mkv',[beat('a',[0,0])])
        with patch.object(bf.subprocess,'run',side_effect=incomplete_probe):
            result=bf.build(self.root/'delivery/evidence.json',self.root/'output','beats')
        self.assertEqual(result['status'],'error')
        self.assertIn('duration is unknown',result['errors'][0])
        self.assertEqual(result['samples'],[])

    def test_extraction_timestamp_mismatch_is_not_success(self):
        delivery(self.root/'delivery',self.media/'cfr.mkv',[beat('a',[0,0])])
        run=subprocess.run
        def changed_diagnostic_after_real_extraction(command, **kwargs):
            result=run(command,**kwargs)
            if Path(command[0]).name=='ffmpeg':
                result.stderr=bf.re.sub(r'(\bn:\s*0\s+pts:\s*)0(\s+pts_time:)',
                                        r'\g<1>1\g<2>',result.stderr)
            return result
        with patch.object(bf.subprocess,'run',side_effect=changed_diagnostic_after_real_extraction):
            result=bf.build(self.root/'delivery/evidence.json',self.root/'output','beats')
        self.assertEqual(result['status'],'error')
        self.assertIn('timestamps differ',result['errors'][0])
        self.assertIsNone(result['samples'][0]['frame'])

    def test_cli_partial_exit_and_refuses_overwrite(self):
        delivery(self.root/'delivery',self.media/'cfr.mkv',[beat('outside',[4,4])])
        command=[sys.executable,str(HERE/'beat_frames.py'),str(self.root/'delivery/evidence.json'),
                 str(self.root/'output'),'--mode','beats']
        result=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'partial')
        before=(self.root/'output/frames.index.json').read_bytes()
        repeat=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(repeat.returncode,2)
        self.assertEqual((self.root/'output/frames.index.json').read_bytes(),before)

    def test_invalid_records_and_intervals_fail_without_success_claim(self):
        data=delivery(self.root/'delivery',self.media/'cfr.mkv',[beat('a',[0,0])])
        for n,interval in enumerate([0,-1,'nan','inf']):
            result=bf.build(self.root/'delivery/evidence.json',self.root/f'bad-{n}',interval=interval)
            self.assertEqual(result['status'],'error')
            self.assertTrue(result['errors'])
        data['reel']['sha256']='0'*64;save(self.root/'delivery/evidence.json',data)
        result=bf.build(self.root/'delivery/evidence.json',self.root/'bad-hash')
        self.assertIn('does not match',result['errors'][0])


if __name__=='__main__':
    unittest.main()
