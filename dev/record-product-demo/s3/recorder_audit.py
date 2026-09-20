#!/usr/bin/env python3
"""Task-local transparent agent-browser command audit for the bounded S3 trial.

This observes the configured executable route; it is not a recording gate or a
claim of coverage of other routes. Transcript/source inspection completes that
coverage separately. A start command is not evidence of successful capture.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def append(log, event):
    with Path(log).open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.write(json.dumps(event, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def initialize(config):
    log = Path(config['log'])
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('x'):
        pass
    append(log, {'event': 'audit_open', 'at': stamp(), 'id': config['id'],
                 'real_executable': config['real_executable'],
                 'scope': 'Only commands routed through this task-local executable.'})


def close(config, child_exit_code):
    append(config['log'], {'event': 'audit_close', 'at': stamp(),
                          'id': config['id'], 'child_exit_code': child_exit_code})


def start_command(argv):
    # Exact CLI tokens only. Batch/eval/other routes need separate inspection.
    return any(argv[i:i + 2] in (['record', 'start'], ['record', 'restart'])
               for i in range(len(argv) - 1))


def forward(config, argv):
    ident = uuid.uuid4().hex
    began = time.monotonic()
    directory = Path(config['log']).parent / 'commands'
    audit_errors = []

    def observe(event):
        try:
            append(config['log'], event)
        except OSError as error:
            # Observation failure must not prevent the requested operation.
            audit_errors.append(str(error))
            print('Recorder audit write failed; coverage is incomplete: ' + str(error), file=sys.stderr)

    observe({'event': 'command_start', 'at': stamp(), 'id': config['id'],
             'command_id': ident, 'pid': os.getpid(), 'argv': argv,
             'record_start_command': start_command(argv)})
    try:
        result = subprocess.run([config['real_executable'], *argv], capture_output=True)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
        launch_error = None
    except OSError as error:
        code, stdout, stderr = 127, b'', (str(error) + '\n').encode()
        launch_error = type(error).__name__ + ': ' + str(error)
    files = {}
    try:
        directory.mkdir(exist_ok=True)
        for kind, data in [('stdout', stdout), ('stderr', stderr)]:
            name = ident + '.' + kind
            (directory / name).write_bytes(data)
            files[kind] = {'path': 'commands/' + name, 'bytes': len(data),
                           'sha256': hashlib.sha256(data).hexdigest()}
    except OSError as error:
        audit_errors.append(str(error))
    observe({'event': 'command_end', 'at': stamp(), 'id': config['id'],
             'command_id': ident, 'exit_code': code, 'launch_error': launch_error,
             'elapsed_seconds': round(time.monotonic() - began, 6),
             'outputs': files, 'audit_errors': audit_errors})
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    return code if code >= 0 else 128 - code


def inspect(config):
    """Summarize route integrity; never infer global absence of recorder-start commands."""
    gaps = []
    log = Path(config['log'])
    events = []
    try:
        for line in log.read_text().splitlines():
            events.append(json.loads(line))
    except (OSError, ValueError) as error:
        gaps.append('Unreadable or incomplete log: ' + str(error))
    opened = [e for e in events if e.get('event') == 'audit_open']
    closed = [e for e in events if e.get('event') == 'audit_close']
    if len(opened) != 1 or not events or events[0].get('event') != 'audit_open':
        gaps.append('One initial audit_open is required.')
    if len(closed) != 1 or not events or events[-1].get('event') != 'audit_close':
        gaps.append('One final audit_close is required.')
    if any(e.get('id') != config['id'] for e in events):
        gaps.append('Audit identity mismatch.')
    starts = [e for e in events if e.get('event') == 'command_start']
    ends = [e for e in events if e.get('event') == 'command_end']
    if len({e['command_id'] for e in starts}) != len(starts):
        gaps.append('Duplicate command start.')
    for event in starts:
        matching = [e for e in ends if e['command_id'] == event['command_id']]
        if len(matching) != 1:
            gaps.append('Missing or duplicate command outcome: ' + event['command_id'])
            continue
        outcome = matching[0]
        if events.index(outcome) < events.index(event):
            gaps.append('Outcome precedes command start.')
        if outcome.get('audit_errors') or set(outcome.get('outputs', {})) != {'stdout', 'stderr'}:
            gaps.append('Incomplete command output: ' + event['command_id'])
        for output in outcome.get('outputs', {}).values():
            path = log.parent / output['path']
            try:
                data = path.read_bytes()
                if len(data) != output['bytes'] or hashlib.sha256(data).hexdigest() != output['sha256']:
                    gaps.append('Changed command output: ' + output['path'])
            except OSError:
                gaps.append('Missing command output: ' + output['path'])
    if {e['command_id'] for e in starts} != {e['command_id'] for e in ends}:
        gaps.append('Unmatched command outcomes.')
    attempts = [e for e in starts if e['record_start_command']]
    return {'schema_version': 1, 'route_log_complete': not gaps, 'gaps': gaps,
            'command_count': len(starts), 'start_attempts': attempts,
            'global_recorder_start_command': True if attempts else None,
            'successful_capture': None,
            'alternative_routes_review': 'required',
            'limits': 'Complete zero-command history establishes only this route. Inspect the full child transcript, task scripts and outputs for other recorder routes. Commands and success codes alone do not establish a completed capture.'}


def main():
    if Path(sys.argv[0]).name == 'agent-browser':
        config = json.loads(Path(__file__).with_name('recorder-audit-config.json').read_text())
        raise SystemExit(forward(config, sys.argv[1:]))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['open', 'close', 'inspect'])
    parser.add_argument('config', type=Path)
    parser.add_argument('--child-exit-code', type=int)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.operation == 'open':
        initialize(config)
    elif args.operation == 'close':
        close(config, args.child_exit_code)
    else:
        print(json.dumps(inspect(config), indent=2))


if __name__ == '__main__':
    main()
