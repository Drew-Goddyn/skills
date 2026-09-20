#!/usr/bin/env python3
"""Check criterion coverage and preserved requirements; does not certify evidence meaning."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess

STATUSES = {'verified', 'partial', 'untested', 'failed', 'deferred'}
ORIGINAL = '9f5daa464643a3392502d053b2e08654efda2a1e'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def git(repo, *args):
    return subprocess.check_output(['git', *args], cwd=repo)

def pointer(value, text):
    for token in text.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value

def check(repo, plan_path, archive_root=None, archive_receipts=None):
    plan = json.loads(plan_path.read_text())
    rec = plan['criterion_reconciliation']
    base = rec['as_of_revision']
    previous = json.loads(git(repo, 'show', base+':dev/record-product-demo/plan.json'))
    original = json.loads(git(repo, 'show', ORIGINAL+':dev/record-product-demo/plan.json'))
    requirements = lambda p: [(t['id'], t['acceptance']) for t in p['tasks']]
    assert requirements(original) == requirements(previous) == requirements(plan), 'Original acceptance wording/order changed'
    assert len(plan['tasks']) == 32
    old_notes = {v['task_id']: v['note'] for v in rec['historical_task_notes']}
    for before, after in zip(previous['tasks'], plan['tasks']):
        assert {k:v for k,v in before.items() if k!='note'} == {k:v for k,v in after.items() if k!='note'}, before['id']
        if before['note'] != after['note']:
            assert old_notes[before['id']] == before['note'], 'Prior note not preserved'
    for key in previous:
        if key not in ('tasks', 'decisions', 'resume', 'log'):
            assert plan[key] == previous[key], 'Original root field changed: '+key
    assert plan['log'][:len(previous['log'])] == previous['log'], 'Historical logs changed'
    assert len(plan['log']) > len(previous['log'])
    assert all(set(e)=={'at','entry'} and e['at'] and e['entry'] for e in plan['log'][len(previous['log']):])
    assert rec['prior_resume'] == previous['resume'] and plan['resume'][1:] == previous['resume']
    assert rec['prior_D1'] == previous['decisions'][0]
    assert {k:v for k,v in plan['decisions'][0].items() if k not in ('answer','continued_at')} == {k:v for k,v in previous['decisions'][0].items() if k!='answer'}
    assert plan['decisions'][1:len(previous['decisions'])] == previous['decisions'][1:]
    proposals = plan['decisions'][len(previous['decisions']):]
    assert [d['id'] for d in proposals] == ['D6','D7']
    assert all(d['status']=='open' and d['blocks']==[] and d['rationale'] and d['proposal'] for d in proposals)
    wanted = {(t['id'],i):s for t in plan['tasks'] for i,s in enumerate(t['acceptance'],1)}
    seen = set()
    for row in rec['criteria']:
        key = (row['task_id'], row['criterion'])
        assert key in wanted and key not in seen, ('Missing/duplicate/unknown criterion',key)
        seen.add(key)
        assert digest(wanted[key].encode()) == row['requirement_sha256'], ('Wrong requirement hash',key)
        assert row['status'] in STATUSES and row['merged_provides'].strip() and row['remaining'].strip()
        assert row['evidence'] and all(e in rec['evidence_sources'] for e in row['evidence']), ('Unknown evidence',key)
    assert seen == set(wanted) and len(seen)==95, 'Incomplete criterion coverage'
    counts = collections.Counter(c['status'] for c in rec['criteria'])
    assert rec['counts'] == {'tasks':32,'criteria':95,**dict(counts)}
    assert len(rec['task_closure'])==32
    for task, closure in zip(plan['tasks'],rec['task_closure']):
        own=[r for r in rec['criteria'] if r['task_id']==task['id']]
        assert closure['task_id']==task['id'] and closure['formal_status']==task['status']=='pending'
        assert closure['verified_criteria']==[r['criterion'] for r in own if r['status']=='verified']
        assert closure['own_remaining_criteria']==[r['criterion'] for r in own if r['status']!='verified']
        assert closure['unfinished_prerequisites']==task['depends_on']
    for d in proposals:
        assert all((x.rsplit(':',1)[0],int(x.rsplit(':',1)[1])) in wanted for x in d['closure_scope'])
    constraints=rec['current_constraints']
    assert (constraints['child_invocations_used'],constraints['child_invocations_remaining'],constraints['calibration_takes_used'],constraints['calibration_takes_remaining'])==(6,0,5,0)
    assert constraints['default_retry_allowance_active'] is False
    assert rec['current_state']['pr2_merged'] is True and rec['current_state']['installed'] is False
    timing=json.loads(git(repo,'show',base+':dev/record-product-demo/correspondence-validation.json'))
    assert timing['local_experiment']['passed_takes']==0 and len(timing['local_experiment']['attempts'])==5
    assert timing['closure']['target_error_seconds']==0.2
    receipts={} if archive_receipts is None else json.loads(archive_receipts.read_text())['references']
    checked=[]
    for sid, source in rec['evidence_sources'].items():
        assert all(source[k] for k in ('tested_source','builder','independent_review','fresh_agent_observations','limits'))
        tested=source['tested_source']
        for k in ('revision','base_revision','publication_equivalent','metadata_correction_publication','historical_plan_revision','later_runs'):
            revision=tested.get(k)
            if revision:
                git(repo,'cat-file','-e',revision+'^{commit}')
                subprocess.run(['git','merge-base','--is-ancestor',revision,base],cwd=repo,check=True)
        published = tested.get('publication_equivalent')
        if published:
            for name, expected in tested.get('recorded_source_sha256', {}).items():
                assert digest(git(repo,'show',published+':'+name))==expected, ('Publication-equivalent identity',sid,name)
        for ref in source['references']:
            relative=Path(ref['path'])
            assert not relative.is_absolute() and '..' not in relative.parts
            if ref['kind'].startswith('tracked'):
                data=git(repo,'show',ref['revision']+':'+ref['path'])
                assert digest(data)==ref['sha256'], ('Source reference hash',sid,ref['path'])
                if ref.get('pointer'):pointer(json.loads(data),ref['pointer'])
                state='verified_git_blob'
            elif archive_root:
                path=archive_root/relative
                assert path.exists(), ('Missing retained reference',sid,str(path))
                if path.is_file():assert digest(path.read_bytes())==ref['sha256'], ('Retained reference hash',sid,ref['path'])
                state='verified_local_archive' if path.is_file() else 'verified_local_directory'
            else:
                receipt=receipts[ref['path']]
                assert receipt['sha256']==ref.get('sha256') and receipt['kind']==ref['kind']
                state='recorded_receipt_only_original_archive_not_embedded'
            checked.append({'source':sid,'path':ref['path'],'sha256':ref.get('sha256'),'kind':ref['kind'],'state':state})
    # Reuse the actual sampled no-findings records, not an empty findings list alone.
    if archive_root:
        for n, name in [(1,'frame-review.json'),(2,'agent-frame-review.json')]:
            root=archive_root/f'dev/record-product-demo/runs/20260919-0006-two-s1-f383/review-package/children/run-{n}/invoice-walkthrough'
            e=json.loads((root/'evidence.json').read_text());review=json.loads((root/'facts'/name).read_text())
            assert e['privacy']['status']=='performed' and e['privacy']['findings']==[] and e['privacy']['coverage'] and e['privacy']['evidence']
            assert review['author']['kind']=='agent' and review['inspected_sheets'] and review['inspected_native_samples']
    expected_tree=rec['evidence_sources']['merged_source']['tested_source']['recording_skill_tree']
    assert git(repo,'rev-parse',base+':skills/codex/record-product-demo').decode().strip()==expected_tree
    published_files=git(repo,'ls-tree','-r','--name-only',base,'skills/codex/record-product-demo').decode().splitlines()
    actual_files=sorted(str(path.relative_to(repo)) for path in (repo/'skills/codex/record-product-demo').rglob('*')
                        if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc' and path.name!='.DS_Store')
    assert actual_files==sorted(published_files), 'Unpublished additions in supported skill'
    for path in published_files:
        assert (repo/path).read_bytes()==git(repo,'show',base+':'+path), 'Supported skill changed: '+path
    assert (repo/'dev/record-product-demo/plan.py').read_bytes()==git(repo,'show',base+':dev/record-product-demo/plan.py')
    return {'status':'pass','requirements':95,'tasks':32,'counts':dict(counts),'reference_count':len(checked),'references':checked,'original_requirements_revision':ORIGINAL,'base_revision':base,'whole_task_statuses_changed':False,'runtime_or_plan_py_changed':False,'reference_scope':'Original archives rehashed locally' if archive_root else 'Published source rechecked; excluded archives checked only against recorded receipts','limits':'Checks establish coverage, references and preservation, not semantic sufficiency of each proposed criterion assessment.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--plan',type=Path)
    parser.add_argument('--archive-root',type=Path)
    parser.add_argument('--archive-receipts',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert args.archive_root or args.archive_receipts, 'Supply local archive root or explicit recorded receipts for excluded archives'
    result=check(args.repo.resolve(),args.plan or args.repo/'dev/record-product-demo/plan.json',args.archive_root,args.archive_receipts)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='references'},indent=2))

if __name__=='__main__':main()
