#!/usr/bin/env python3
"""Extract encoded-video beat/interval frames and contact sheets from evidence.json."""
import argparse
from bisect import bisect_right
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess

from check_evidence import Evidence, obj, text, choice, items, require, read_json
from check_video import tool


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def seconds(value):
    if type(value) not in (int, float, str):
        raise ValueError('time must be finite seconds')
    return Fraction(str(value))


def probe_frames(video, output):
    command = [tool('ffprobe'), '-v', 'error', '-err_detect', 'explode',
               '-select_streams', 'v:0', '-show_streams', '-show_frames', '-show_entries',
               'stream=index,time_base:frame=pts,best_effort_timestamp,duration,pkt_duration',
               '-of', 'json', str(video)]
    result = subprocess.run(command, capture_output=True, text=True)
    (output / 'probe.stderr.txt').write_text(result.stderr)
    (output / 'probe.json').write_text(result.stdout)
    if result.returncode or result.stderr.strip():
        raise RuntimeError('Frame probe failed; see probe.stderr.txt')
    data = json.loads(result.stdout)
    if not data.get('streams') or not data.get('frames'):
        raise ValueError('No decoded video frames')
    stream = data['streams'][0]
    time_base = Fraction(stream['time_base'])
    if time_base <= 0:
        raise ValueError('Video time base is not positive')
    frames = []
    for n, frame in enumerate(data['frames']):
        pts = frame.get('pts', frame.get('best_effort_timestamp'))
        if pts is None:
            raise ValueError(f'Decoded frame {n} has no presentation timestamp')
        frames.append({'decode_index': n, 'pts': int(pts)})
    origin = frames[0]['pts'] * time_base
    starts = [(f['pts'] * time_base - origin) for f in frames]
    if any(b <= a for a, b in zip(starts, starts[1:])):
        raise ValueError('Decoded frame timestamps must be strictly increasing; alignment cannot be inferred')
    last = data['frames'][-1]
    tail = int(last.get('duration', last.get('pkt_duration', 0))) * time_base
    if tail <= 0:
        raise ValueError('Last decoded frame duration is unknown; picture end cannot be bounded')
    ends = starts[1:] + [starts[-1] + tail]
    for frame, start, end in zip(frames, starts, ends):
        frame.update(video_seconds=float(start), timestamp_seconds=float(origin + start),
                     presentation_end_seconds=float(end), time_base=str(time_base))
    return frames, starts, ends, {'stream_index': stream['index'], 'time_base': str(time_base),
                                'origin_pts': frames[0]['pts'], 'origin_seconds': float(origin),
                                'duration_seconds': float(ends[-1]), 'decoded_frames': len(frames)}


def select_frame(target, starts, ends):
    """Half-open presentation intervals; no seek/clamp or fps-derived rounding."""
    if target < 0 or target >= ends[-1]:
        return None
    n = bisect_right(starts, target) - 1
    return n if n >= 0 and target < ends[n] else None


def requests(evidence, mode, interval, starts, ends):
    samples = []
    if mode in ('beats', 'both'):
        seen = set()
        for i, beat in enumerate(items(evidence.get('beats'), 'beats')):
            obj(beat, f'beats[{i}]', 'id label video_time alignment driver_time')
            bid = text(beat['id'], f'beats[{i}].id')
            require(bid not in seen, 'beats', 'duplicate beat id'); seen.add(bid)
            text(beat['label'], f'beats[{i}].label')
            entry = {'sample_id': f'beat-{i+1:04d}', 'kind': 'beat', 'beat_id': bid,
                     'label': beat['label'], 'video_time': beat['video_time'],
                     'alignment': beat['alignment'], 'driver_time': beat['driver_time'],
                     'requested_seconds': None, 'requested_range_seconds': None,
                     'status': 'unresolved', 'reason': 'encoded_video_time_unknown', 'frame': None}
            if beat['video_time'] is not None:
                timing = obj(beat['video_time'], f'beats[{i}].video_time', 'seconds precision basis')
                choice(timing['precision'], 'video_time.precision', 'exact sampled approximate')
                text(timing['basis'], 'video_time.basis')
                span = items(timing['seconds'], 'video_time.seconds')
                require(len(span) == 2, 'video_time.seconds', 'expected [start, end]')
                a, b = map(seconds, span)
                require(a <= b, 'video_time.seconds', 'range is reversed')
                target = (a + b) / 2
                entry.update(requested_seconds=float(target), requested_range_seconds=span)
                # A partly invalid range is also missing, even if its midpoint is in bounds.
                n = None if a < 0 or b > ends[-1] else select_frame(target, starts, ends)
                entry.update(status='selected' if n is not None else 'missing',
                             reason=None if n is not None else 'outside_decoded_picture_span',
                             selected_decode_index=n)
            samples.append(entry)
    if mode in ('intervals', 'both'):
        count = -(-ends[-1] // interval)
        for i in range(count):
            target = i * interval
            n = select_frame(target, starts, ends)
            samples.append({'sample_id': f'interval-{i+1:04d}', 'kind': 'interval', 'beat_id': None,
                            'label': f'Whole-reel sample {i+1}', 'requested_seconds': float(target),
                            'requested_range_seconds': None, 'status': 'selected' if n is not None else 'missing',
                            'reason': None if n is not None else 'no_decoded_frame_at_target',
                            'selected_decode_index': n, 'frame': None})
    return samples


def extract_selected(video, output, selected, frames):
    if not selected:
        return {}, None
    folder = output / 'frames'; folder.mkdir()
    expression = '+'.join(f'eq(n,{n})' for n in selected).replace(',', r'\,')
    command = [tool('ffmpeg'), '-hide_banner', '-nostdin', '-n', '-v', 'info', '-xerror',
               '-err_detect', 'explode', '-copyts', '-i', str(video), '-map', '0:v:0',
               '-an', '-sn', '-dn', '-vf', f'select={expression},showinfo',
               '-fps_mode', 'passthrough', str(folder / 'frame-%06d.png')]
    result = subprocess.run(command, capture_output=True, text=True)
    (output / 'extract.stderr.txt').write_text(result.stderr)
    files = sorted(folder.glob('frame-*.png'))
    bases = re.findall(r'config in time_base:\s*(\d+/\d+)', result.stderr)
    emitted = re.findall(r'\bn:\s*\d+\s+pts:\s*(-?\d+)\s+pts_time:', result.stderr)
    error = None
    if result.returncode:
        error = 'FFmpeg extraction failed; see extract.stderr.txt'
    elif len(files) != len(selected) or len(emitted) != len(selected) or len(set(bases)) != 1:
        error = 'Extracted image/timestamp count mismatch; cannot safely assign frame paths'
    elif any(Fraction(pts) * Fraction(bases[0]) != Fraction(frames[n]['pts']) * Fraction(frames[n]['time_base'])
             for n, pts in zip(selected, emitted)):
        error = 'FFmpeg extraction timestamps differ from probed frame timestamps'
    if error:
        return {}, error
    from PIL import Image
    result = {}
    for n, path in zip(selected, files):
        with Image.open(path) as image:
            width, height = image.size
            image.load()
        result[n] = dict(frames[n], path=path.relative_to(output).as_posix(), width=width,
                         height=height, sha256=digest(path),
                         timestamp_verified='ffprobe PTS matched FFmpeg showinfo PTS')
    return result, None


def wrap(text_value, draw, font, width):
    """Character wrapping also handles unbroken labels; no label text is discarded."""
    lines, line = [], ''
    for char in text_value:
        if char == '\n' or (line and draw.textlength(line + char, font=font) > width):
            lines.append(line); line = ''
            if char == '\n':
                continue
        line += char
    return lines + [line]


def contact_sheets(samples, output, name):
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.load_default(size=20)
    except TypeError as exc:
        raise RuntimeError('Contact sheets need Pillow >= 10.1 with its bundled scalable default font') from exc
    sheets = []
    for page, offset in enumerate(range(0, len(samples), 6), 1):
        entries = samples[offset:offset+6]
        labels = []
        scratch = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        for entry in entries:
            requested = entry['requested_seconds']
            actual = entry['frame']['video_seconds'] if entry['frame'] else None
            caption = f"{entry['sample_id']} | {entry.get('beat_id') or 'interval'} | {entry['label']}\n"
            caption += f"request {requested:.6f}s" if requested is not None else 'request UNKNOWN'
            caption += f" | decoded {actual:.6f}s" if actual is not None else f" | {entry['status'].upper()}: {entry['reason']}"
            labels.append(wrap(caption, scratch, font, 620))
        label_height = max(map(len, labels)) * 26 + 16
        cell_h = label_height + 400 + 12
        sheet = Image.new('RGB', (1280, 72 + ((len(entries)+1)//2)*cell_h), '#e8edf3')
        draw = ImageDraw.Draw(sheet)
        draw.text((12, 8), f'{name.upper()} - page {page} - encoded-video seconds', font=font, fill='#152638')
        draw.text((12, 36), 'Sampling only; visibility, viewing and privacy judgments remain separate.', font=font, fill='#152638')
        cells = []
        for i, (entry, lines) in enumerate(zip(entries, labels)):
            x, y = (i % 2)*640, 72 + (i//2)*cell_h
            for j, line in enumerate(lines):
                draw.text((x+10, y+8+j*26), line, font=font, fill='#152638')
            box = [x+10, y+label_height, 620, 400]
            if entry['frame']:
                with Image.open(output / entry['frame']['path']) as original:
                    thumb = original.convert('RGB')
                thumb.thumbnail((620, 400), Image.Resampling.LANCZOS)
                box = [x+10+(620-thumb.width)//2, y+label_height+(400-thumb.height)//2, thumb.width, thumb.height]
                sheet.paste(thumb, (box[0], box[1]))
            else:
                draw.rectangle((x+10,y+label_height,x+630,y+label_height+400), fill='#d1d9e2')
                draw.text((x+24,y+label_height+170), 'NO FRAME - ' + entry['status'].upper(), font=font, fill='#7d2d25')
            cells.append({'sample_id':entry['sample_id'], 'image_box_xywh':box})
        path = f'{name}-{page:02d}.png'; sheet.save(output/path)
        sheets.append({'path':path, 'width':sheet.width, 'height':sheet.height, 'cells':cells})
    return sheets


def build(evidence_path, output, mode='both', interval=Fraction(2)):
    evidence_path = Path(evidence_path).resolve(); output = Path(output).resolve()
    # Refuse reuse, including a delivery folder, before writing anything.
    output.mkdir(parents=True, exist_ok=False)
    index = {'schema_version':1, 'status':'error', 'scope':'encoded_frame_extraction_only', 'samples':[],
             'contact_sheets':[], 'errors':[], 'review_judgments':'not_performed',
             'limitations':['Extraction does not establish action visibility, a completed watch, or privacy clearance.',
                            'Driver alignment is not estimated. Evidence and reviewer attribution are not modified.']}
    try:
        interval = seconds(interval) if not isinstance(interval, Fraction) else interval
        require(interval > 0, 'interval', 'must be positive finite seconds')
        choice(mode, 'mode', 'beats intervals both')
        data = obj(read_json(evidence_path), 'evidence', 'schema_version reel beats')
        require(type(data['schema_version']) is int and data['schema_version']==1, 'schema_version', 'expected evidence version 1')
        evidence = Evidence(evidence_path); evidence.media(data['reel'], 'reel')
        video = evidence.file(data['reel']['path'], 'reel.path')
        index['source'] = {'evidence_name':evidence_path.name, 'evidence_sha256':digest(evidence_path),
                           'reel_name':video.name, 'reel_sha256':digest(video),
                           'recorded_duration_seconds':data['reel']['duration_seconds']}
        frames, starts, ends, info = probe_frames(video, output)
        index['video'] = dict(info, clock='seconds from first decoded presentation timestamp; raw PTS retained',
                              frame_intervals='Each frame persists until the next decoded PTS; final frame uses decoded duration. End is exclusive.')
        index['selection'] = {'mode':mode, 'beat_rule':'Midpoint of supplied encoded-video range; containing presentation interval [start,end). Never clamp.',
                              'interval_seconds':float(interval), 'interval_rule':'0, interval, 2*interval, ... strictly before decoded picture end; no forced tail sample.'}
        samples = requests(data, mode, interval, starts, ends); index['samples'] = samples
        selected = sorted({s['selected_decode_index'] for s in samples if s['status']=='selected'})
        extracted, error = extract_selected(video, output, selected, frames)
        if error:
            index['errors'].append(error)
        for entry in samples:
            if entry['status']=='selected':
                entry['frame'] = extracted.get(entry['selected_decode_index'])
                entry.update(status='extracted' if entry['frame'] else 'missing',
                             reason=None if entry['frame'] else 'extraction_failed_or_frame_missing')
        for kind, name in [('beat','beats'),('interval','intervals')]:
            index['contact_sheets'] += contact_sheets([s for s in samples if s['kind']==kind], output, name)
        interval_entries = [s for s in samples if s['kind']=='interval']
        unique = {s['frame']['decode_index'] for s in samples if s['frame']}
        index['coverage'] = {'decoded_frame_count':len(frames), 'unique_extracted_frames':len(unique),
                             'decoded_frames_not_extracted':len(frames)-len(unique),
                             'interval_requested_seconds':[s['requested_seconds'] for s in interval_entries],
                             'interval_frame_count':sum(s['frame'] is not None for s in interval_entries),
                             'last_interval_requested_seconds':interval_entries[-1]['requested_seconds'] if interval_entries else None,
                             'picture_end_seconds':float(ends[-1]), 'complete_frame_coverage':len(unique)==len(frames),
                             'privacy_clearance':'not_established'}
        index['status'] = 'error' if index['errors'] else ('partial' if any(s['status']!='extracted' for s in samples) else 'complete')
    except (ValueError, OSError, KeyError, ZeroDivisionError, RuntimeError, ImportError) as exc:
        index['errors'].append(str(exc))
    (output/'frames.index.json').write_text(json.dumps(index, indent=2, allow_nan=False)+'\n')
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    parser.add_argument('output', type=Path, help='New directory; existing paths are refused')
    parser.add_argument('--mode', choices=['beats','intervals','both'], default='both')
    parser.add_argument('--interval', default='2', help='Whole-reel spacing in seconds (default: 2)')
    args = parser.parse_args()
    try:
        index = build(args.evidence, args.output, args.mode, seconds(args.interval))
    except (ValueError, OSError, ZeroDivisionError) as exc:
        print(json.dumps({'status':'error','error':str(exc)})); return 2
    print(json.dumps({'status':index['status'], 'index':str(args.output/'frames.index.json'), 'errors':index['errors']}, indent=2))
    return {'complete':0,'partial':1,'error':2}[index['status']]


if __name__=='__main__':
    raise SystemExit(main())
