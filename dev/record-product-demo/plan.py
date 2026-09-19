#!/usr/bin/env python3
"""Validate, query, and update the record-product-demo improvement plan."""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

TASK_STATUSES = {'pending', 'in_progress', 'blocked', 'done', 'dropped'}
DECISION_STATUSES = {'open', 'answered', 'withdrawn', 'not_triggered'}
TASK_FIELDS = ('id', 'iteration', 'title', 'why', 'depends_on', 'status', 'acceptance', 'evidence', 'note')
FINISHED = ('done', 'dropped')
HOME_PATH = re.compile(r'(?<![\w.-])/(?:Users|home)/[^/\s"\'`]+|~[\w.-]*/|\$\{?HOME\b')


def load(path):
    return json.loads(path.read_text())


def save(path, plan):
    issues = problems(plan)
    if issues:
        raise SystemExit('Refusing to save an invalid plan:\n' + '\n'.join(issues))
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n')


def strings(value, where=''):
    if isinstance(value, str):
        yield where, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from strings(item, f'{where}.{key}' if where else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from strings(item, f'{where}[{index}]')


def problems(plan):
    issues = []
    tasks = plan.get('tasks', [])
    ids = [task.get('id') for task in tasks]
    issues += [f'duplicate task id {i}' for i in sorted({i for i in ids if ids.count(i) > 1})]
    by_id = {task.get('id'): task for task in tasks}
    order = [str(iteration.get('id')) for iteration in plan.get('iterations', [])]
    decisions = {decision.get('id'): decision for decision in plan.get('decisions', [])}
    decision_ids = set(decisions)
    issues += [f'{where}: contains a home-folder path' for where, text in strings(plan) if HOME_PATH.search(text)]
    for task in tasks:
        tid = task.get('id')
        issues += [f'{tid}: missing {field}' for field in TASK_FIELDS if field not in task]
        iteration = str(task.get('iteration'))
        if iteration not in order:
            issues.append(f'{tid}: unknown iteration {task.get("iteration")!r}')
        if task.get('status') not in TASK_STATUSES:
            issues.append(f'{tid}: unknown status {task.get("status")!r}')
        for dep in task.get('depends_on', []):
            if dep not in by_id:
                issues.append(f'{tid}: unknown dependency {dep}')
            elif iteration in order and str(by_id[dep].get('iteration')) in order \
                    and order.index(str(by_id[dep].get('iteration'))) > order.index(iteration):
                issues.append(f'{tid}: depends on {dep}, which is in a later iteration')
        issues += [f'{tid}: requires unknown decision {d}' for d in task.get('requires_decisions', []) if d not in decision_ids]
        if not task.get('acceptance'):
            issues.append(f'{tid}: no acceptance criteria')
        if task.get('status') == 'done' and not task.get('evidence'):
            issues.append(f'{tid}: done without evidence')
        if task.get('status') in ('blocked', 'dropped') and not task.get('note'):
            issues.append(f'{tid}: {task.get("status")} without a note')
        if task.get('status') in ('in_progress', 'done'):
            unfinished = [d for d in task.get('depends_on', []) if by_id.get(d, {}).get('status') not in FINISHED]
            if unfinished:
                issues.append(f'{tid}: {task.get("status")} while dependencies are unfinished: {unfinished}')
            holding = [d for d in task.get('requires_decisions', []) if decisions.get(d, {}).get('status') != 'answered']
            holding += [d for d, decision in decisions.items() if decision.get('status') == 'open' and tid in decision.get('blocks', [])]
            if holding:
                issues.append(f'{tid}: {task.get("status")} while held by decisions {holding}')
    graph = {task.get('id'): task.get('depends_on', []) for task in tasks}
    state = {}

    def visit(node, trail):
        if state.get(node) == 'active':
            issues.append('dependency cycle: ' + ' -> '.join(trail + [node]))
        elif state.get(node) is None:
            state[node] = 'active'
            for dep in graph.get(node, []):
                if dep in graph:
                    visit(dep, trail + [node])
            state[node] = 'visited'

    for node in graph:
        visit(node, [])
    for decision in plan.get('decisions', []):
        did = decision.get('id')
        if decision.get('status') not in DECISION_STATUSES:
            issues.append(f'decision {did}: unknown status {decision.get("status")!r}')
        if decision.get('status') == 'answered' and not decision.get('answer'):
            issues.append(f'decision {did}: answered without an answer')
        issues += [f'decision {did}: blocks unknown task {t}' for t in decision.get('blocks', []) if t not in by_id]
    return issues


def held_by(plan, task):
    decisions = {decision['id']: decision for decision in plan.get('decisions', [])}
    held = [d for d in decisions.values() if d.get('status') == 'open' and task['id'] in d.get('blocks', [])]
    held += [decisions[d] for d in task.get('requires_decisions', []) if decisions[d].get('status') != 'answered']
    return held


def next_step(plan):
    for iteration in plan['iterations']:
        members = [t for t in plan['tasks'] if str(t['iteration']) == str(iteration['id'])]
        if all(t['status'] in FINISHED for t in members):
            continue
        finished = {t['id'] for t in plan['tasks'] if t['status'] in FINISHED}
        candidates = [t for t in members if t['status'] in ('in_progress', 'pending')
                      and all(dep in finished for dep in t['depends_on'])]
        candidates.sort(key=lambda t: t['status'] != 'in_progress')
        free = [t for t in candidates if not held_by(plan, t)]
        return {
            'iteration': {'id': iteration['id'], 'title': iteration['title']},
            'task': free[0] if free else None,
            'other_ready_tasks': [t['id'] for t in free[1:]],
            'held_tasks': [{'task': t['id'], 'decisions': [{'id': d['id'], 'status': d['status'], 'question': d['question']}
                                                            for d in held_by(plan, t)]}
                           for t in candidates if held_by(plan, t)],
            'blocked_tasks': [{'task': t['id'], 'note': t['note']} for t in members if t['status'] == 'blocked'],
        }
    return {'iteration': None, 'task': None, 'other_ready_tasks': [], 'held_tasks': [], 'blocked_tasks': []}


def command_next(plan, _args):
    print(json.dumps(next_step(plan), indent=2, ensure_ascii=False))


def command_status(plan, _args):
    print(plan['goal'])
    for iteration in plan['iterations']:
        members = [t for t in plan['tasks'] if str(t['iteration']) == str(iteration['id'])]
        finished = sum(t['status'] in FINISHED for t in members)
        print(f'\nIteration {iteration["id"]}: {iteration["title"]} ({finished}/{len(members)} finished)')
        for task in members:
            print(f'  [{task["status"]}] {task["id"]} {task["title"]}')
    step = next_step(plan)
    if step['task']:
        print(f'\nNext: {step["task"]["id"]} {step["task"]["title"]}')
    elif step['iteration'] is None:
        print('\nNext: nothing, every iteration is finished')
    else:
        print(f'\nNext: nothing ready in iteration {step["iteration"]["id"]}')
    for held in step['held_tasks']:
        for decision in held['decisions']:
            print(f'  {held["task"]} waits on {decision["id"]}: {decision["question"]}')
    for blocked in step['blocked_tasks']:
        print(f'  {blocked["task"]} is blocked: {blocked["note"]}')
    open_decisions = [d for d in plan.get('decisions', []) if d['status'] == 'open']
    if open_decisions:
        print('Open decisions:')
        for decision in open_decisions:
            print(f'  {decision["id"]}: {decision["question"]}')
    print('\nRecent log:')
    for entry in plan.get('log', [])[-3:]:
        print(f'  {entry["at"]} {entry["entry"]}')


def append_log(plan, text):
    plan.setdefault('log', []).append({'at': datetime.datetime.now().isoformat(timespec='seconds'), 'entry': text})


def dependents(plan, task_id):
    found, frontier = [], [task_id]
    while frontier:
        current = frontier.pop()
        for task in plan['tasks']:
            if current in task['depends_on'] and task['id'] not in found:
                found.append(task['id'])
                frontier.append(task['id'])
    return found


def retire_evidence(task):
    task.setdefault('prior_evidence', []).extend(task['evidence'])
    task['evidence'] = []


def command_update(plan, args):
    task = next((t for t in plan['tasks'] if t['id'] == args.id), None)
    if task is None:
        raise SystemExit(f'Unknown task {args.id}')
    reopening = task['status'] in FINISHED and args.status in ('pending', 'in_progress', 'blocked')
    resets = []
    if reopening:
        by_id = {t['id']: t for t in plan['tasks']}
        resets = [by_id[d] for d in dependents(plan, task['id']) if by_id[d]['status'] in ('in_progress', 'done')]
        later = [t['id'] for t in resets if str(t['iteration']) != str(task['iteration'])]
        if later and not args.reset_later_iterations:
            raise SystemExit(f'Reopening {task["id"]} would reset finished work in other iterations: {later}. '
                             'Surface this to the owner, then rerun with --reset-later-iterations.')
        retire_evidence(task)
    if args.status:
        task['status'] = args.status
    task['evidence'] += args.evidence or []
    if args.note:
        task['note'] = args.note
    append_log(plan, f'{task["id"]} -> {task["status"]}' + (f': {args.note}' if args.note else ''))
    for dependent in resets:
        dependent['status'] = 'pending'
        retire_evidence(dependent)
        append_log(plan, f'{dependent["id"]} -> pending: {task["id"]} was reopened')
    print(json.dumps({'task': task['id'], 'status': task['status'], 'reset': [t['id'] for t in resets]}))


def command_decide(plan, args):
    decision = next((d for d in plan.get('decisions', []) if d['id'] == args.id), None)
    if decision is None:
        raise SystemExit(f'Unknown decision {args.id}')
    decision['status'] = args.status
    if args.answer:
        decision['answer'] = args.answer
    append_log(plan, f'decision {decision["id"]} -> {decision["status"]}' + (f': {args.answer}' if args.answer else ''))
    if args.status in ('answered', 'withdrawn'):
        for task in plan['tasks']:
            if task['id'] in decision.get('blocks', []) and task['status'] == 'blocked':
                task['status'] = 'pending'
                append_log(plan, f'{task["id"]} -> pending: decision {decision["id"]} is {args.status}')
    if args.status == 'withdrawn':
        for task in plan['tasks']:
            if decision['id'] in task.get('requires_decisions', []) and task['status'] not in FINISHED:
                task['status'] = 'dropped'
                task['note'] = f'decision {decision["id"]} was withdrawn'
                append_log(plan, f'{task["id"]} -> dropped: decision {decision["id"]} was withdrawn')


def command_log(plan, args):
    append_log(plan, args.text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, default=Path(__file__).with_name('plan.json'))
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate', help='Check structure, dependencies, decisions, and evidence rules')
    commands.add_parser('next', help='Print the next task in the current iteration as JSON, or what holds it')
    commands.add_parser('status', help='Print a human-readable summary')
    update = commands.add_parser('update', help='Change a task, reset dependents when reopening it, and append to the log')
    update.add_argument('id')
    update.add_argument('--status', choices=sorted(TASK_STATUSES))
    update.add_argument('--evidence', action='append', help='Repository-relative evidence path or short proof; repeatable')
    update.add_argument('--note')
    update.add_argument('--reset-later-iterations', action='store_true',
                        help='Allow reopening to reset finished tasks in other iterations, after surfacing the list to the owner')
    decide = commands.add_parser('decide', help='Change a decision, release or drop the tasks it governs, and append to the log')
    decide.add_argument('id')
    decide.add_argument('--status', choices=sorted(DECISION_STATUSES), required=True)
    decide.add_argument('--answer')
    log = commands.add_parser('log', help='Append a log entry')
    log.add_argument('text')
    args = parser.parse_args()

    plan = load(args.plan)
    if args.command == 'validate':
        issues = problems(plan)
        print(json.dumps({'status': 'fail' if issues else 'pass', 'problems': issues}, indent=2))
        return 1 if issues else 0
    if args.command in ('next', 'status'):
        {'next': command_next, 'status': command_status}[args.command](plan, args)
        return 0
    {'update': command_update, 'decide': command_decide, 'log': command_log}[args.command](plan, args)
    save(args.plan, plan)
    return 0


if __name__ == '__main__':
    sys.exit(main())
