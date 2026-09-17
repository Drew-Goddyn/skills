"""Verify that a healthy preflight passes and a decodable frozen tail is rejected."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from check_video import tool
from preflight import check_motion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path, help='A healthy capture from preflight.py')
    parser.add_argument('scratch', type=Path, help='A new directory for the negative control')
    args = parser.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=False)
    healthy = check_motion(args.video)
    if healthy['status'] != 'pass':
        raise AssertionError('Source preflight did not pass: ' + str(healthy['violations']))
    probe = subprocess.run([
        tool('ffprobe'), '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(args.video),
    ], capture_output=True, text=True, check=True)
    duration = float(json.loads(probe.stdout)['format']['duration'])
    # Freeze midway through the known static hold, preserving the original duration.
    cut = healthy['phases']['hold']['samples'][0]['at_seconds'] + 3
    frozen = args.scratch / 'frozen-tail.mp4'
    subprocess.run([
        tool('ffmpeg'), '-v', 'error', '-i', str(args.video), '-an',
        '-vf', f'trim=end={cut},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={duration-cut},fps=30',
        '-t', str(duration), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(frozen),
    ], capture_output=True, check=True)
    media = subprocess.run([
        sys.executable, str(Path(__file__).with_name('check_video.py')), str(frozen),
        '--expected-size', '1440x900', '--expected-fps', '30',
    ], capture_output=True, text=True, check=True)
    rejected = check_motion(frozen)
    if rejected['status'] != 'fail' or rejected['phases']['after']['travel_pixels'] != 0:
        raise AssertionError('Frozen tail was not rejected for missing resumed motion')
    result = {'status': 'pass', 'healthy': healthy, 'frozen_media': json.loads(media.stdout),
              'frozen_motion': rejected,
              'checks': ['healthy capture passes', 'frozen tail preserves decodable 30 fps media',
                         'frozen tail fails for missing post-hold motion']}
    (args.scratch / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': 'pass', 'checks': result['checks'],
                      'evidence': str(args.scratch / 'checks.json')}, indent=2))


if __name__ == '__main__':
    main()
