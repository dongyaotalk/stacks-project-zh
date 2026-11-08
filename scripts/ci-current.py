#!/usr/bin/env python3
"""Run from trusted comparison checkout for data PRs; broad changes test HEAD tools."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stacks_zh.ci_scope import classify
from stacks_zh.chapter_validation import git, check_current_repository
from stacks_zh.records import RecordError
from stacks_zh.generated_reports import check_generated_reports


def run():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--harvest',type=Path,required=True)
    p.add_argument('--base-ref',required=True)
    p.add_argument('--force-broad',action='store_true')
    args=p.parse_args()
    root=args.root.resolve()
    out=root/'build/ci-current';out.mkdir(parents=True,exist_ok=True)
    # A failed rerun must not leave an earlier report receipt looking current.
    (out/'reports.json').unlink(missing_ok=True)
    dispatch=classify(root,args.base_ref)
    if args.force_broad:
        dispatch.update(kind='current-all',reason='trusted base lacks dispatcher; migration/full current check')
        dispatch.pop('validation_state',None)
    print(json.dumps(dispatch,ensure_ascii=False),flush=True)
    (out/'dispatch.json').write_text(json.dumps(dispatch,ensure_ascii=False,indent=2)+'\n')
    def make(*commands):
        for command in commands:
            subprocess.run(['make',command,'PYTHON='+sys.executable,'HARVEST_DIR='+str(args.harvest),
                            'BASE_REF='+args.base_ref],cwd=root,check=True)
    # Workflow validates repository policy, harvest and source-coordinate tables;
    # pr-contract independently verifies Issue/PR scope with its existing permissions.
    make('workflow-check','harvest-check')
    if dispatch['kind']=='generated-reports':
        payload=check_generated_reports(root,args.harvest,args.base_ref)
        subprocess.run(['git','diff','--check',args.base_ref],cwd=root,check=True)
        (out/'reports.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(payload,ensure_ascii=False),flush=True)
        return
    elif dispatch['kind']=='chapter-current':
        make('upstream-index-check','chapter-template-check')
        chapters=set(dispatch['chapters'])
        if len(chapters)>1:
            print('Expanding multi-chapter/shared participants to qa-current-all; pure data tool tests not run',flush=True)
            chapters=None
        payload=check_current_repository(root,args.harvest,args.base_ref,report=print,chapters=chapters)
        (out/'chapters.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    elif dispatch['kind']=='current-all':
        make('tool-test','qa-current-all','upstream-index-check','chapter-template-check')
    else:
        print('Data acceptance not run: '+dispatch['reason'],flush=True)
    paths=dispatch['paths']
    if any(x in paths for x in ['README.md','docs/progress.md','docs/translation-progress.md','stacks_zh/progress.py','tests/test_progress.py','Makefile']):make('progress-check')
    if any(x in paths for x in ['README.md','docs/translation-priority.md','docs/translation-plan.md','docs/task-allocation.md','docs/ci.md','config/translation-priorities.json','stacks_zh/planning.py','stacks_zh/schema_validation.py','stacks_zh/cli.py','tests/test_planning.py','Makefile','.github/workflows/ci.yml']):make('plan-check')
    subprocess.run(['git','diff','--check'],cwd=root,check=True)


if __name__=='__main__':
    try:run()
    except (RecordError,OSError,ValueError,subprocess.CalledProcessError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr);sys.exit(1)
