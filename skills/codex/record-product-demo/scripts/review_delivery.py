#!/usr/bin/env python3
"""Summarize recorded decisive-frame findings and a watch list; never perform review."""
import argparse
import json
from pathlib import Path

from check_evidence import Evidence, Invalid, read_json, validate


SCOPE = 'recorded_frame_review_readiness_only'


def assess(path):
    path = Path(path)
    structural = validate(path)
    if structural['status'] != 'pass':
        raise Invalid('; '.join(structural['violations']))
    data = read_json(path)
    evidence = Evidence(path)
    findings = {f['beat_id']: f for f in data['review'].get('beat_findings', [])}
    blockers, beats = [], []
    decisive = [b for b in data['beats'] if b['decisive']]
    if not decisive:
        blockers.append('No decisive beats are designated; map the brief before claiming frame-review coverage.')
    for beat in decisive:
        finding = findings.get(beat['id'])
        state = finding['status'] if finding else 'unreviewed'
        if state != 'supported':
            blockers.append(f"{beat['id']} ({beat['label']}): {state}; no supported decisive-moment finding.")
        if beat['video_time'] is None:
            blockers.append(f"{beat['id']}: encoded-video timing is unresolved; this is not evidence the action is absent.")
        if not any(w.get('beat_id') == beat['id'] for w in data['review']['watch_list']):
            blockers.append(f"{beat['id']}: missing linked watch-list target with preserved final-output timing/precision.")
        resolved = []
        for ref in finding['samples'] if finding else []:
            sample = evidence.frame_sample(ref, 'review sample', data['reel'])
            index = evidence.file(ref['index'], 'frame index', True)
            if index['status'] == 'error':
                blockers.append(f"{beat['id']}: extraction error in {ref['index']}; inspect its diagnostics.")
            resolved.append({'reference': ref, 'sample': sample})
        beats.append({'beat_id': beat['id'], 'label': beat['label'], 'video_time': beat['video_time'],
                      'alignment': beat['alignment'], 'status': state, 'finding': finding,
                      'resolved_samples': resolved})
    media = [c for c in data['checks'] if c['kind'] == 'media']
    for check in media:
        if check['status'] != 'performed':
            blockers.append(f"Media check {check['id']}: {check['status']}; no passing result.")
    for check in structural['check_results']:
        if check['kind'] == 'media' and check['result']['status'] != 'pass':
            blockers.append(f"Media check {check['id']}: {check['result']['status']}; see preserved raw result.")
    return {'schema_version': 1, 'scope': SCOPE,
            'status': 'diagnostic_only' if blockers else 'ready_for_review',
            'acceptance': 'not_established_by_this_tool', 'blockers': blockers,
            'reel': data['reel'], 'decisive_beats': beats,
            'watch_list': data['review']['watch_list'],
            'checks': data['checks'],
            'check_results': structural['check_results'],
            'review_coverage': {k: data['review'][k] for k in ('agent_frames', 'continuous_watch', 'listening', 'human')},
            'privacy': data['privacy'], 'limitations': data['limitations'],
            'boundary': 'Summarizes attributed findings, not an independent inspection. Ready for review is not successful delivery or publication approval. Frame inspection does not establish continuous viewing, listening, pacing, or privacy.'}


def timestamp(value):
    minutes, milliseconds = divmod(round(value * 1000), 60000)
    return f'{minutes:02d}:{milliseconds / 1000:06.3f}'


def handoff(result):
    """Short watch list plus the reasons this is a review or diagnostic handoff."""
    lines = [f"Review package: **{result['status']}**.", '', result['boundary'], '',
             f"Reel: {result['reel']['path']} — {result['reel']['duration_seconds']:.6f} seconds, {result['reel']['size_bytes']} bytes."]
    if result['blockers']:
        lines += ['', 'What prevents a supported handoff:']
        lines += ['- ' + b for b in result['blockers']]
    lines += ['', 'Watch list — final-output video clock. Display rounded to milliseconds; exact supplied values remain in evidence.json. These are review targets, not a claim of watching:', '']
    for watch in result['watch_list']:
        span = watch['video_seconds']
        time = 'time unresolved' if span is None else '–'.join(timestamp(s) for s in span)
        precision = watch.get('precision') or 'precision unrecorded'
        lines.append(f"- {time} ({precision}) — {watch['label']}: {watch['note']}")
    lines += ['', 'Recorded decisive-beat findings:', '']
    for beat in result['decisive_beats']:
        finding = beat['finding']
        attribution = 'no reviewing author'
        if finding and finding['author']:
            author = finding['author']
            attribution = f"{author['kind']} author: {author['name']}"
            if finding['relay']:
                relay = finding['relay']
                attribution += f"; relayed by {relay['kind']} {relay['name']}"
        lines.append(f"- {beat['label']}: **{beat['status']}** ({attribution}). " + (finding['observation'] if finding else 'No per-beat finding recorded.'))
        if finding:
            lines.append('  Coverage: ' + finding['coverage'])
            refs = []
            for resolved in beat['resolved_samples']:
                ref, sample = resolved['reference'], resolved['sample']
                frame = sample['frame']
                suffix = f" at {timestamp(frame['video_seconds'])}" if frame else f" ({sample['status']})"
                refs.append(f"{ref['index']}#{ref['sample_id']}{suffix}")
            if refs:
                lines.append('  Samples: ' + '; '.join(refs))
    lines += ['', 'Recorded checks (not rerun by this command) — original context and raw results, including warnings, remain in review-readiness.json and the evidence references:', '']
    for check in result['check_results']:
        report = check['result']
        if not isinstance(report, dict):
            lines.append(f"- {check['id']} ({check['kind']}): see raw result")
            continue
        lines.append(f"- {check['id']} ({check['kind']}): {report.get('status', 'see raw result')}")
        for key, value in report.items():
            if value and ('warn' in key or key in ('compatibility_findings', 'violations', 'error')):
                lines.append(f"  {key}: {json.dumps(value, ensure_ascii=False)}")
    lines += ['', 'Review coverage and remaining limits:', '']
    for key, coverage in dict(result['review_coverage'], privacy=result['privacy']).items():
        lines.append(f"- {key}: {coverage['status']}. {coverage['coverage']}")
    lines += ['- ' + limit for limit in result['limitations']]
    return '\n'.join(lines) + '\n'


def build(path, output):
    result = assess(path)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'review-readiness.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    (output / 'HANDOFF.md').write_text(handoff(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    parser.add_argument('output', type=Path, help='New output directory; does not overwrite evidence or earlier handoffs')
    args = parser.parse_args()
    try:
        result = build(args.evidence, args.output)
    except (ValueError, OSError) as exc:
        print(json.dumps({'status': 'error', 'error': str(exc)}))
        return 2
    print(json.dumps({'status': result['status'], 'scope': SCOPE, 'blockers': result['blockers']}, indent=2))
    return 0 if result['status'] == 'ready_for_review' else 1


if __name__ == '__main__':
    raise SystemExit(main())
