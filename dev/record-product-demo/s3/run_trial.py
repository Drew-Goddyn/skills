#!/usr/bin/env python3
"""One explicitly selected S3 trial. No scheduling, retries or model fallback.

prepare freezes inputs without starting a browser/model. run makes exactly one
counted child invocation. The parent must assess it before selecting another.
"""
import argparse
import datetime
import fcntl
import functools
import hashlib
import http.server
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request

import recorder_audit as audit

BASELINE = 'f414875393139db9d0e44a07de9cef62d9114990'
PUBLISHED = '60b5d4e2ce47e4dc14ad104260f64f67b731e034'
SKILL = 'skills/codex/record-product-demo'
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(Path(root).rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc' and p.name != '.DS_Store'}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)


def support_files():
    return [HERE / 'recorder_audit.py', HERE / 'run_trial.py', HERE / 'test_s3.py',
            HERE / 'README.md', HERE.parent / 'experiment-setup.md',
            HERE.parent / 'fixtures/template-invoice.html']


def prepare(run):
    if (run / 'scope.json').exists():
        raise SystemExit('Refusing to replace a frozen trial scope.')
    run.mkdir(parents=True, exist_ok=True)
    assert git('rev-parse', 'HEAD').decode().strip() == PUBLISHED
    assert git('rev-parse', PUBLISHED + ':' + SKILL).decode().strip() == '03a7332dbeed3eb5af44489a8c906092b04e94de'
    for file in git('ls-tree', '-r', '--name-only', PUBLISHED, SKILL).decode().splitlines():
        assert (REPO / file).read_bytes() == git('show', PUBLISHED + ':' + file), file
    frozen = run / 'frozen'
    frozen.mkdir()
    fixture = HERE.parent / 'fixtures/template-invoice.html'
    shutil.copyfile(fixture, frozen / 'index.html')
    source = json.loads((HERE.parent / 'plan.json').read_text())
    brief = next(s['brief'] for s in source['scenarios'] if s['id'] == 'S1')
    (frozen / 'brief.txt').write_text(brief + '\nUse the task-local record-product-demo skill.\n')
    contract = (HERE.parent / 'experiment-setup.md').read_text().split('## Task-local contract\n', 1)[1].split('\n## What is isolated', 1)[0].strip()
    (frozen / 'AGENTS.md').write_text(contract + '\n\nThe selected skill revision and file identities are in source-identity.json.\nUse the configured DEMO_BROWSER executable for browser commands in this workspace. Task-local command logging forwards it and the PATH entry to the installed agent-browser unchanged. Keep .tools/ and capture-browser.json unchanged. Browser-internal chrome://version is allowed for task profile/sandbox diagnostics.\n')
    versions = {name: subprocess.check_output(command, text=True).strip() for name, command in {
        'codex': ['codex', '--version'], 'agent_browser': ['agent-browser', '--version'],
        'python': [sys.executable, '--version'], 'node': ['node', '--version']}.items()}
    scope = {'schema_version': 1, 'frozen_at': audit.stamp(), 'baseline_revision': BASELINE,
             'current_revision': PUBLISHED, 'historical_invocations': 6, 'new_invocation_cap': 4,
             'cumulative_cap': 10, 'direct_builder_captures': 0, 'calibration_budget_remaining': 0,
             'fixture_query': '?reset=1&env=production', 'fixture_sha256': sha(frozen / 'index.html'),
             'support_sha256': {str(p.relative_to(REPO)): sha(p) for p in support_files()},
             'frozen_files': tree(frozen), 'versions': versions, 'child_invocations': []}
    write(run / 'scope.json', scope)
    print(json.dumps(scope, indent=2))


def permitted_role(previous, requested, decisions):
    if not previous:
        return requested == 'baseline'
    last = previous[-1]
    decision = decisions.get(str(last['index']))
    if not decision or decision['infrastructure_blocker'] or not decision['audit_coverage_complete']:
        return False
    baselines = [r for r in previous if r['role'] == 'baseline']
    current = [r for r in previous if r['role'] == 'current']
    if len(baselines) == 1 and not current and decisions['1']['criterion_pass']:
        return requested == 'baseline'
    return requested == 'current' and len(current) < 2


def inventory(workspace):
    excluded = {'.git', 'browser-profile', 'capture-sockets', '.agents'}
    files = {}
    for p in sorted(workspace.rglob('*')):
        relative = p.relative_to(workspace)
        if any(part in excluded for part in relative.parts) or p.is_symlink() or not p.is_file():
            continue
        files[str(relative)] = {'bytes': p.stat().st_size, 'sha256': sha(p)}
    return {'files': files, 'excluded': sorted(excluded),
            'skill': 'Separately compared with before/after manifests; profile and sockets not read.'}


def run_one(run, role):
    with (run / 'invocation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        scope = json.loads((run / 'scope.json').read_text())
        previous = scope['child_invocations']
        if len(previous) >= 4 or any(v['status'] == 'started' for v in previous):
            raise SystemExit('Invocation cap or unfinished invocation blocks another call.')
        decisions_path = run / 'parent-decisions.json'
        decisions = json.loads(decisions_path.read_text()) if decisions_path.exists() else {}
        if not permitted_role(previous, role, decisions):
            raise SystemExit('Baseline/current order or unresolved evidence blocks this invocation.')
        for name, expected in scope['support_sha256'].items():
            assert sha(REPO / name) == expected, 'Frozen support changed: ' + name
        assert tree(run / 'frozen') == scope['frozen_files'], 'Frozen inputs changed'
        index = len(previous) + 1
        output = run / f'child-{index}'
        output.mkdir()
        workspace = Path(tempfile.mkdtemp(prefix='recording-task-', dir='/private/tmp'))
        revision = BASELINE if role == 'baseline' else PUBLISHED
        source = git('archive', revision, SKILL)
        (output / 'skill-source.tar').write_bytes(source)
        imported = workspace / '.import'
        with tarfile.open(fileobj=io.BytesIO(source)) as archive:
            archive.extractall(imported, filter='data')
        selected = workspace / '.agents/skills/record-product-demo'
        selected.parent.mkdir(parents=True)
        shutil.move(str(imported / SKILL), selected)
        shutil.rmtree(imported)
        skill_before = tree(selected)
        (workspace / 'fixture').mkdir()
        shutil.copyfile(run / 'frozen/index.html', workspace / 'fixture/index.html')
        shutil.copyfile(run / 'frozen/AGENTS.md', workspace / 'AGENTS.md')
        (workspace / 'output').mkdir()
        subprocess.run(['git', 'init', '-q'], cwd=workspace, check=True)
        tools = workspace / '.tools'
        tools.mkdir()
        shutil.copyfile(HERE / 'recorder_audit.py', tools / 'agent-browser')
        (tools / 'agent-browser').chmod(0o755)
        real_browser = shutil.which('agent-browser')
        assert real_browser and Path(real_browser).is_file()
        config = {'id': f'trial-{index}', 'real_executable': str(Path(real_browser).resolve()),
                  'log': str(output / 'audit/commands.jsonl')}
        write(tools / 'recorder-audit-config.json', config)
        browser_config = {'profile': str(workspace / 'browser-profile')}
        write(workspace / 'capture-browser.json', browser_config)
        identity = {'revision': revision, 'skill_git_tree': git('rev-parse', revision + ':' + SKILL).decode().strip(),
                    'skill_files': skill_before, 'skill_archive_sha256': hashlib.sha256(source).hexdigest(),
                    'fixture_sha256': scope['fixture_sha256']}
        write(workspace / 'source-identity.json', identity)
        write(output / 'identity-before.json', identity)
        write(output / 'workspace.json', {'path': str(workspace), 'skill': str(selected), 'role': role,
                                         'task_profile': browser_config['profile'], 'profile_initially_absent': not Path(browser_config['profile']).exists()})
        shutil.copyfile(workspace / 'AGENTS.md', output / 'setup-AGENTS.md')
        log = (output / 'fixture-server.log').open('w')

        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                log.write(self.log_date_time_string() + ' ' + format % args + '\n')
                log.flush()

        handler = functools.partial(Handler, directory=str(workspace / 'fixture'))
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}/' + scope['fixture_query']
        with urllib.request.urlopen(url, timeout=5) as response:
            body = response.read()
            assert response.status == 200 and hashlib.sha256(body).hexdigest() == scope['fixture_sha256']
        write(output / 'fixture-server.json', {'url': url, 'bind': '127.0.0.1', 'http_status': 200,
                                              'response_sha256': hashlib.sha256(body).hexdigest(),
                                              'scope': 'HTTP provenance, not rendered target recognition.'})
        prompt = (run / 'frozen/brief.txt').read_text().format(url=url, out=str(workspace / 'output'))
        command = ['codex', '--sandbox', 'danger-full-access', '--ask-for-approval', 'on-request',
                   'exec', '-C', str(workspace), '--json', '--ephemeral', '-o', str(output / 'final-response.md'),
                   '-m', 'gpt-6-astra', '-c', 'model_reasoning_effort="max"',
                   '-c', 'model_provider="openai"', '-c', 'forced_login_method="chatgpt"',
                   '-c', 'skills.config=[{path=' + json.dumps(str(Path.home() / '.codex/skills/record-product-demo/SKILL.md')) + ',enabled=false}]']
        for name in ('boss-mcp', 'unblocked', 'chrome-devtools', 'node_repl', 'computer-use', 'clio-llm-gateway'):
            command += ['-c', f'mcp_servers.{name}.enabled=false']
        command += ['-']
        env = dict(os.environ)
        removed = [name for name in env if name.startswith('AGENT_BROWSER_')]
        removed += ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'AZURE_OPENAI_API_KEY', 'GEMINI_API_KEY',
                    'GOOGLE_API_KEY', 'CODEX_API_KEY', 'AI_GATEWAY_API_KEY']
        for name in removed:
            env.pop(name, None)
        settings = {'AGENT_BROWSER_CONFIG': str(workspace / 'capture-browser.json'),
                    'AGENT_BROWSER_SOCKET_DIR': str(workspace / 'capture-sockets'),
                    'DEMO_BROWSER': str(tools / 'agent-browser'), 'PYTHONDONTWRITEBYTECODE': '1'}
        env.update(settings)
        env['PATH'] = str(tools) + ':/opt/homebrew/bin:' + env.get('PATH', '')
        (output / 'prompt.txt').write_text(prompt)
        write(output / 'command.json', command)
        write(output / 'environment-settings.json', {'set': settings, 'browser_config': browser_config,
              'removed_if_present': sorted(set(removed)), 'path_prefix': [str(tools), '/opt/homebrew/bin'],
              'account_home': 'Inherited, unchanged; existing ChatGPT account route.',
              'skill_isolation': 'Pinned recording copy; retained host/default guidance. Only global recording entry disabled.',
              'chrome_sandbox': 'Enabled; no disabling flags configured. Actual child observations remain separate.'})
        audit.initialize(config)
        invocation = {'index': index, 'cumulative_index': 6 + index, 'role': role, 'status': 'started',
                      'started_at': audit.stamp(), 'revision': revision, 'workspace': str(workspace),
                      'model': 'gpt-6-astra', 'reasoning_effort': 'max',
                      'account_route': 'openai / forced_login_method=chatgpt',
                      'sandbox': 'danger-full-access', 'approval_policy': 'on-request'}
        previous.append(invocation)
        write(run / 'scope.json', scope)  # Count before attempting the child, including failure.
        started = time.monotonic()
        code = None
        try:
            with (output / 'transcript.jsonl').open('w') as stdout, (output / 'stderr.txt').open('w') as stderr:
                result = subprocess.run(command, input=prompt, text=True, env=env, stdout=stdout, stderr=stderr)
            code = result.returncode
            invocation.update(status='completed' if code == 0 else 'failed', exit_code=code)
        except BaseException as error:
            invocation.update(status='failed', launcher_error=type(error).__name__ + ': ' + str(error))
            raise
        finally:
            invocation.update(wall_seconds=round(time.monotonic() - started, 3), finished_at=audit.stamp())
            audit.close(config, code)
            server.shutdown()
            server.server_close()
            log.close()
            write(output / 'audit-summary.json', audit.inspect(config))
            write(output / 'inventory.json', inventory(workspace))
            after = tree(selected)
            write(output / 'identity-after.json', {'skill_files': after, 'skill_copy_modified': after != skill_before,
                  'fixture_sha256': sha(workspace / 'fixture/index.html'),
                  'audit_wrapper_sha256': sha(tools / 'agent-browser'),
                  'source_fixture_and_skill_unchanged': after == skill_before and sha(workspace / 'fixture/index.html') == scope['fixture_sha256']})
            events = []
            transcript = output / 'transcript.jsonl'
            if transcript.exists():
                for number, line in enumerate(transcript.read_text().splitlines(), 1):
                    try:
                        event = json.loads(line)
                        if event.get('type') == 'turn.completed':
                            invocation['reported_usage'] = event.get('usage')
                        if event.get('type') in ('item.started', 'item.completed'):
                            item = event.get('item', {})
                            events.append({'line': number, 'event': event['type'], 'item_id': item.get('id'),
                                           'type': item.get('type'), 'command': item.get('command'),
                                           'exit_code': item.get('exit_code')})
                    except ValueError:
                        invocation.setdefault('transcript_parse_errors', []).append(number)
            write(output / 'transcript-index.json', events)
            write(run / 'scope.json', scope)
        print(json.dumps(invocation, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'run'])
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--role', choices=['baseline', 'current'])
    args = parser.parse_args()
    if args.operation == 'prepare':
        prepare(args.run.resolve())
    else:
        if not args.role:
            parser.error('run requires an explicitly selected --role')
        run_one(args.run.resolve(), args.role)


if __name__ == '__main__':
    main()
