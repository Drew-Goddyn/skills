#!/usr/bin/env python3
"""Check evidence.json structure/references, not media or publication fitness (stdlib only)."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re


SCOPE = 'evidence_structure_and_consistency_only'


class Invalid(ValueError):
    pass


def require(condition, where, message):
    if not condition:
        raise Invalid(f'{where}: {message}')


def obj(value, where, fields):
    require(isinstance(value, dict), where, 'expected an object')
    for field in fields.split():
        require(field in value, f'{where}.{field}', 'required field is missing')
    return value


def text(value, where):
    require(isinstance(value, str) and bool(value.strip()), where, 'expected nonempty text')
    return value


def choice(value, where, choices):
    require(isinstance(value, str) and value in choices.split(), where, f'expected one of: {choices}')
    return value


def number(value, where, minimum=0):
    require(type(value) in (int, float) and math.isfinite(value) and value >= minimum,
            where, f'expected a finite number >= {minimum}')
    return value


def items(value, where, nonempty=False):
    require(isinstance(value, list), where, 'expected an array')
    require(not nonempty or bool(value), where, 'must not be empty')
    return value


def strings(value, where, nonempty=False):
    for i, item in enumerate(items(value, where, nonempty)):
        text(item, f'{where}[{i}]')


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, key, 'duplicate JSON key')
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(), object_pairs_hook=strict_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(Invalid(f'nonfinite JSON number: {value}')))


class Evidence:
    def __init__(self, path):
        self.path = path
        self.root = path.parent.resolve()
        self.check_results = []

    def file(self, value, where, as_json=False):
        text(value, where)
        path = Path(value)
        require(not path.is_absolute() and '..' not in path.parts and '\\' not in value,
                where, 'use a relative path inside this delivery folder')
        path = (self.root / path).resolve()
        require(path.is_relative_to(self.root), where, 'reference escapes delivery folder')
        require(path.is_file(), where, f'referenced file is missing: {value}')
        if as_json:
            try:
                return read_json(path)
            except (ValueError, OSError) as exc:
                raise Invalid(f'{where}: cannot read JSON: {exc}') from exc
        return path

    def media(self, value, where):
        obj(value, where, 'path sha256 duration_seconds size_bytes')
        path = self.file(value['path'], where + '.path')
        digest = value['sha256']
        require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), where + '.sha256', 'expected SHA-256 hex')
        actual = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                actual.update(chunk)
        require(actual.hexdigest() == digest,
                where + '.sha256', 'does not match referenced media bytes')
        number(value['duration_seconds'], where + '.duration_seconds')
        require(type(value['size_bytes']) is int and value['size_bytes'] == path.stat().st_size,
                where + '.size_bytes', 'must equal referenced file size in bytes')

    def time_range(self, value, where, duration):
        items(value, where)
        require(len(value) == 2, where, 'expected [start, end] seconds')
        start, end = [number(v, where) for v in value]
        require(start <= end <= duration, where, 'range is reversed or outside the encoded video span')
        return start, end

    def coverage(self, value, where):
        obj(value, where, 'status coverage evidence')
        status = choice(value['status'], where + '.status', 'performed not_performed unavailable not_applicable')
        text(value['coverage'], where + '.coverage')
        for i, ref in enumerate(items(value['evidence'], where + '.evidence', status == 'performed')):
            self.file(ref, f'{where}.evidence[{i}]')

    def run(self):
        require(self.path.name == 'evidence.json', 'filename', 'use evidence.json beside one reel in its own delivery folder')
        d = obj(read_json(self.path), '$', 'schema_version reel brief environment source production takes beats checks review privacy limitations toolkit reproduction')
        require(type(d['schema_version']) is int and d['schema_version'] == 1,
                'schema_version', 'expected version 1; legacy records need explicit mapping, not a video-quality verdict')
        self.media(d['reel'], 'reel')
        require(Path(d['reel']['path']).parent == Path('.'), 'reel.path', 'reel must be beside evidence.json')
        duration = d['reel']['duration_seconds']
        brief = obj(d['brief'], 'brief', 'record audience takeaway decisive_moments duration_seconds sound_policy')
        self.file(brief['record'], 'brief.record')
        for key in ('audience', 'takeaway'):
            text(brief[key], 'brief.' + key)
        strings(brief['decisive_moments'], 'brief.decisive_moments', True)
        bounds = obj(brief['duration_seconds'], 'brief.duration_seconds', 'min max')
        for key in bounds:
            if key in ('min', 'max') and bounds[key] is not None:
                number(bounds[key], 'brief.duration_seconds.' + key)
        require(bounds['min'] is None or bounds['max'] is None or bounds['min'] <= bounds['max'],
                'brief.duration_seconds', 'minimum exceeds maximum')
        choice(brief['sound_policy'], 'brief.sound_policy', 'forbid allow require')
        env = obj(d['environment'], 'environment', 'kind url signed_in_account_kind conditions')
        for key in ('kind', 'signed_in_account_kind', 'conditions'):
            text(env[key], 'environment.' + key)
        if env['url'] is not None:
            text(env['url'], 'environment.url')
        source = obj(d['source'], 'source', 'revision revision_note record')
        if source['revision'] is not None:
            text(source['revision'], 'source.revision')
        text(source['revision_note'], 'source.revision_note')
        self.file(source['record'], 'source.record')
        production = obj(d['production'], 'production', 'mode capture edit')
        mode = choice(production['mode'], 'production.mode', 'capture edit_only capture_and_edit')
        require((production['capture'] is None) == (mode == 'edit_only'), 'production.capture', 'edit_only has no new capture; capture modes require capture settings')
        if production['capture'] is not None:
            capture = obj(production['capture'], 'production.capture', 'settings context')
            self.file(capture['settings'], 'production.capture.settings')
            text(capture['context'], 'production.capture.context')
        require((production['edit'] is None) == (mode == 'capture'), 'production.edit', 'capture has no edit; edit modes require edit settings and timeline')
        if production['edit'] is not None:
            self.edit(production['edit'], duration)
        takes = {}
        for i, take in enumerate(items(d['takes'], 'takes')):
            w = f'takes[{i}]'
            obj(take, w, 'id role record')
            tid = text(take['id'], w + '.id')
            require(tid not in takes, w + '.id', 'duplicate take id')
            choice(take['role'], w + '.role', 'new_capture source_capture')
            require(mode != 'edit_only' or take['role'] == 'source_capture', w + '.role', 'edit-only work cannot claim a new take')
            takes[tid] = obj(self.file(take['record'], w + '.record', True), w + '.record', '')
        require(mode == 'edit_only' or any(t['role'] == 'new_capture' for t in d['takes']), 'takes', 'new capture must reference its existing take record')
        ids = set()
        for i, beat in enumerate(items(d['beats'], 'beats', True)):
            w = f'beats[{i}]'
            obj(beat, w, 'id kind label decisive driver_time video_time alignment timing_note')
            bid = text(beat['id'], w + '.id')
            require(bid not in ids, w + '.id', 'duplicate beat id'); ids.add(bid)
            for key in ('kind', 'label', 'timing_note'):
                text(beat[key], w + '.' + key)
            require(type(beat['decisive']) is bool, w + '.decisive', 'expected a boolean')
            if beat['driver_time'] is not None:
                driver = obj(beat['driver_time'], w + '.driver_time', 'take event_index')
                tid = text(driver['take'], w + '.driver_time.take')
                require(tid in takes, w + '.driver_time.take', 'unknown take id')
                events = obj(takes[tid], w + '.referenced_take', 'events')['events']
                idx = driver['event_index']
                require(isinstance(events, list) and type(idx) is int and 0 <= idx < len(events), w + '.driver_time.event_index', 'event index is outside referenced take')
                event = obj(events[idx], w + '.referenced_event', 'at')
                number(event['at'], w + '.referenced_event.at')
            if beat['video_time'] is not None:
                timing = obj(beat['video_time'], w + '.video_time', 'seconds precision basis')
                self.time_range(timing['seconds'], w + '.video_time.seconds', duration)
                choice(timing['precision'], w + '.video_time.precision', 'exact sampled approximate')
                text(timing['basis'], w + '.video_time.basis')
            alignment = choice(beat['alignment'], w + '.alignment', 'unknown approximate verified')
            require(alignment == 'unknown' or (beat['driver_time'] is not None and beat['video_time'] is not None), w + '.alignment', 'non-unknown alignment needs both clocks and its basis in timing_note')
        self.checks(d['checks'], d['reel'], brief)
        review = obj(d['review'], 'review', 'agent_frames continuous_watch listening human watch_list')
        for key in ('agent_frames', 'continuous_watch', 'listening', 'human'):
            self.coverage(review[key], 'review.' + key)
        require(brief['sound_policy'] != 'require' or review['listening']['status'] != 'not_applicable',
                'review.listening.status', 'required sound needs listening review or an explicit missing-coverage state')
        for i, watch in enumerate(items(review['watch_list'], 'review.watch_list', True)):
            w = f'review.watch_list[{i}]'
            obj(watch, w, 'label video_seconds note')
            text(watch['label'], w + '.label'); text(watch['note'], w + '.note')
            if watch['video_seconds'] is not None:
                self.time_range(watch['video_seconds'], w + '.video_seconds', duration)
            if 'beat_id' in watch or 'precision' in watch:
                obj(watch, w, 'beat_id precision')
                beat = next((b for b in d['beats'] if b['id'] == watch['beat_id']), None)
                require(beat is not None, w + '.beat_id', 'unknown beat id')
                timing = beat['video_time']
                require(watch['video_seconds'] == (timing['seconds'] if timing else None)
                        and watch['precision'] == (timing['precision'] if timing else None),
                        w, 'watch target must preserve the beat final-output range and precision, including unknown timing')
        if 'beat_findings' in review:
            self.beat_findings(review['beat_findings'], d)
        privacy = obj(d['privacy'], 'privacy', 'status coverage evidence findings')
        self.coverage(privacy, 'privacy')
        for i, finding in enumerate(items(privacy['findings'], 'privacy.findings')):
            w = f'privacy.findings[{i}]'
            obj(finding, w, 'description video_seconds timing_note')
            text(finding['description'], w + '.description'); text(finding['timing_note'], w + '.timing_note')
            if finding['video_seconds'] is not None:
                self.time_range(finding['video_seconds'], w + '.video_seconds', duration)
        strings(d['limitations'], 'limitations')
        self.toolkit(d['toolkit'])
        reproduction = obj(d['reproduction'], 'reproduction', 'setup created_records cleanup')
        text(reproduction['setup'], 'reproduction.setup')
        strings(reproduction['created_records'], 'reproduction.created_records')
        self.coverage(reproduction['cleanup'], 'reproduction.cleanup')

    def beat_findings(self, findings, data):
        """Optional v1 extension: truthful incomplete findings remain structurally valid."""
        beats = {b['id']: b for b in data['beats']}
        seen = set()
        for i, finding in enumerate(items(findings, 'review.beat_findings')):
            w = f'review.beat_findings[{i}]'
            obj(finding, w, 'beat_id status author relay observation coverage samples sheets')
            bid = text(finding['beat_id'], w + '.beat_id')
            require(bid in beats and bid not in seen, w + '.beat_id', 'unknown or duplicate beat id')
            seen.add(bid)
            state = choice(finding['status'], w + '.status', 'supported not_visible unresolved unreviewed')
            for key in ('observation', 'coverage'):
                text(finding[key], w + '.' + key)
            for key in ('author', 'relay'):
                actor = finding[key]
                if actor is not None:
                    obj(actor, w + '.' + key, 'kind name')
                    choice(actor['kind'], w + '.' + key + '.kind', 'agent human')
                    text(actor['name'], w + '.' + key + '.name')
            require((finding['author'] is None) == (state == 'unreviewed'), w + '.author',
                    'reviewed findings need their author; unreviewed findings have no reviewing author')
            require(state != 'unreviewed' or finding['relay'] is None, w + '.relay', 'unreviewed has no relayed finding')
            samples = items(finding['samples'], w + '.samples')
            sheets = items(finding['sheets'], w + '.sheets')
            if state == 'unreviewed':
                require(not samples and not sheets, w, 'unreviewed cannot claim inspected samples or sheets')
            if state in ('supported', 'not_visible'):
                require(beats[bid]['video_time'] is not None, w, 'unknown beat timing needs an unresolved finding, not a visibility verdict')
                require(bool(samples) and bool(sheets), w, 'visibility findings need inspected samples and sheets')
                coverage_key = 'agent_frames' if finding['author']['kind'] == 'agent' else 'human'
                require(data['review'][coverage_key]['status'] == 'performed', w + '.author',
                        f'visibility finding contradicts review.{coverage_key} coverage status')
            for j, ref in enumerate(samples):
                sample = self.frame_sample(ref, f'{w}.samples[{j}]', data['reel'])
                if state in ('supported', 'not_visible'):
                    require(sample['status'] == 'extracted', w, 'visibility findings need actual extracted frames, not placeholders')
                    index = self.file(ref['index'], w + '.index', True)
                    index_dir = Path(ref['index']).parent
                    matching_sheets = [(index_dir / s['path']).as_posix()
                                       for s in items(index.get('contact_sheets'), w + '.index.contact_sheets')
                                       if isinstance(s, dict) and isinstance(s.get('path'), str)
                                       and any(isinstance(c, dict) and c.get('sample_id') == ref['sample_id']
                                               for c in items(s.get('cells'), w + '.index.sheet.cells'))]
                    require(any(s in sheets for s in matching_sheets), w + '.sheets',
                            'an inspected sheet must include each supporting sample')
            for j, sheet in enumerate(sheets):
                self.file(sheet, f'{w}.sheets[{j}]')

    def frame_sample(self, ref, where, reel):
        """Resolve an index reference without copying another version of its timestamps."""
        obj(ref, where, 'index sample_id')
        text(ref['sample_id'], where + '.sample_id')
        index_path = self.file(ref['index'], where + '.index')
        index = obj(self.file(ref['index'], where + '.index', True), where + '.index',
                    'schema_version scope source samples status')
        require(type(index['schema_version']) is int and index['schema_version'] == 1
                and index['scope'] == 'encoded_frame_extraction_only', where, 'expected encoded-frame index version 1')
        source = obj(index['source'], where + '.index.source', 'reel_sha256')
        require(source['reel_sha256'] == reel['sha256'], where, 'frame index belongs to a different reel')
        choice(index['status'], where + '.index.status', 'complete partial error')
        matches = [s for s in items(index['samples'], where + '.index.samples')
                   if isinstance(s, dict) and s.get('sample_id') == ref['sample_id']]
        require(len(matches) == 1, where + '.sample_id', 'sample is missing or ambiguous in frame index')
        sample = obj(matches[0], where, 'status frame')
        state = choice(sample['status'], where + '.status', 'extracted missing unresolved')
        require((sample['frame'] is None) == (state != 'extracted'), where, 'sample status contradicts frame presence')
        if state == 'extracted':
            frame = obj(sample['frame'], where + '.frame', 'path sha256 video_seconds')
            relative = Path(text(frame['path'], where + '.frame.path'))
            require(not relative.is_absolute() and '..' not in relative.parts, where + '.frame.path', 'use a relative path inside the index folder')
            path = self.file((index_path.parent.relative_to(self.root) / relative).as_posix(), where + '.frame.path')
            require(hashlib.sha256(path.read_bytes()).hexdigest() == frame['sha256'], where, 'frame hash does not match indexed bytes')
            at = number(frame['video_seconds'], where + '.frame.video_seconds')
            require(at < reel['duration_seconds'], where, 'frame timestamp is outside delivered picture')
        return sample

    def edit(self, edit, duration):
        obj(edit, 'production.edit', 'settings inputs timeline')
        self.file(edit['settings'], 'production.edit.settings')
        inputs = {}
        for i, media in enumerate(items(edit['inputs'], 'production.edit.inputs', True)):
            w = f'production.edit.inputs[{i}]'
            obj(media, w, 'id')
            mid = text(media['id'], w + '.id')
            require(mid not in inputs, w + '.id', 'duplicate input id')
            self.media(media, w); inputs[mid] = media
        timeline = obj(edit['timeline'], 'production.edit.timeline', 'status basis segments')
        state = choice(timeline['status'], 'production.edit.timeline.status', 'known unknown')
        text(timeline['basis'], 'production.edit.timeline.basis')
        segments = items(timeline['segments'], 'production.edit.timeline.segments', state == 'known')
        require(state != 'unknown' or not segments, 'production.edit.timeline.segments', 'unknown mapping must not invent segments')
        previous_end = 0
        for i, seg in enumerate(segments):
            w = f'production.edit.timeline.segments[{i}]'
            obj(seg, w, 'input source_seconds output_seconds speed')
            mid = text(seg['input'], w + '.input')
            require(mid in inputs, w + '.input', 'unknown input id')
            a, b = self.time_range(seg['source_seconds'], w + '.source_seconds', inputs[mid]['duration_seconds'])
            c, e = self.time_range(seg['output_seconds'], w + '.output_seconds', duration)
            speed = number(seg['speed'], w + '.speed')
            require(speed > 0 and b > a and e > c, w, 'segments need positive spans and speed')
            require(c >= previous_end, w + '.output_seconds', 'segments must be ordered and nonoverlapping; use unknown for unsupported mappings')
            # Only arithmetic representation error, not a media/codec timing allowance.
            require(math.isclose((b-a)/speed, e-c, rel_tol=1e-9, abs_tol=1e-9), w, 'source/output spans disagree with speed')
            previous_end = e

    def checks(self, checks, reel, brief):
        ids = set()
        for i, check in enumerate(items(checks, 'checks', True)):
            w = f'checks[{i}]'
            obj(check, w, 'id kind status report context')
            cid = text(check['id'], w + '.id')
            require(cid not in ids, w + '.id', 'duplicate check id'); ids.add(cid)
            text(check['kind'], w + '.kind'); text(check['context'], w + '.context')
            state = choice(check['status'], w + '.status', 'performed not_run unavailable')
            require((check['report'] is None) == (state != 'performed'), w + '.report', 'performed needs a raw report; unperformed cannot claim a result')
            if state != 'performed':
                continue
            report = self.file(check['report'], w + '.report', True)
            self.check_results.append({'id': cid, 'kind': check['kind'], 'result': report})
            if check['kind'] != 'media':
                continue
            obj(report, w + '.report', 'status')
            choice(report['status'], w + '.report.status', 'pass fail error')
            if report['status'] == 'error':
                obj(report, w + '.report', 'error')
                text(report['error'], w + '.report.error')
                continue
            obj(report, w + '.report', 'video violations duration_seconds file_size_bytes')
            text(report['video'], w + '.report.video')
            require(Path(report['video']).name == Path(reel['path']).name, w + '.report.video', 'checker names a different reel')
            items(report['violations'], w + '.report.violations')
            require((report['status'] == 'pass') == (len(report['violations']) == 0), w + '.report', 'status contradicts violations')
            # Reports are copied intact; never collapse warnings or failed results into a pass.
            picture = report.get('picture', {})
            obj(picture, w + '.report.picture', '')
            span = picture.get('duration_seconds')
            if span is None:
                span = report['duration_seconds']
            number(span, w + '.report.duration_seconds')
            require(type(report['file_size_bytes']) is int, w + '.report.file_size_bytes', 'expected integer bytes')
            require(span == reel['duration_seconds'] and report['file_size_bytes'] == reel['size_bytes'], w + '.report', 'measurements disagree with delivered reel record')
            if 'audio_policy' in report:
                require(report['audio_policy'] == brief['sound_policy'], w + '.report.audio_policy', 'checker policy differs from brief')
        require(any(c['kind'] == 'media' for c in checks), 'checks', 'include media check or explicitly record why it was not run')

    def toolkit(self, value):
        obj(value, 'toolkit', 'status friction owner scope result')
        state = choice(value['status'], 'toolkit.status', 'pending running improved no_change blocked')
        text(value['owner'], 'toolkit.owner'); text(value['scope'], 'toolkit.scope')
        for i, friction in enumerate(items(value['friction'], 'toolkit.friction')):
            w = f'toolkit.friction[{i}]'
            obj(friction, w, 'issue evidence')
            text(friction['issue'], w + '.issue')
            self.file(friction['evidence'], w + '.evidence')
        result = obj(value['result'], 'toolkit.result', 'reason changed_files checks tool_version discovery next_action')
        text(result['reason'], 'toolkit.result.reason')
        strings(result['changed_files'], 'toolkit.result.changed_files', state == 'improved')
        for ref in items(result['checks'], 'toolkit.result.checks', state == 'improved'):
            self.file(ref, 'toolkit.result.checks')
        for key in ('tool_version', 'discovery', 'next_action'):
            if result[key] is not None:
                text(result[key], 'toolkit.result.' + key)
        if state == 'improved':
            require(result['tool_version'] is not None and result['discovery'] is not None, 'toolkit.result', 'improved needs verified version and normal discovery route')
        if state in ('pending', 'running', 'blocked'):
            require(result['next_action'] is not None, 'toolkit.result.next_action', 'unfinished work needs a next action')


def validate(path):
    evidence = Evidence(Path(path))
    try:
        evidence.run()
    except (ValueError, OSError) as exc:
        return {'status': 'fail', 'scope': SCOPE, 'violations': [str(exc)]}
    return {'status': 'pass', 'scope': SCOPE, 'violations': [],
            'check_results': evidence.check_results,
            'limitations': ['No media decoding or visual, listening, privacy, or publication-fitness review is performed.',
                            'References and stated consistency are checked; assertions of review and source provenance are not independently verified.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    result = validate(args.evidence)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
