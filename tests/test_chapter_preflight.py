"""Real synthetic Git/container preparation; no model authorship or approval."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_source_containers import fixture as english_fixture, git
from test_source_container_boundaries import LIST
from stacks_zh.chapter_preflight import run_chapter_preflight
from stacks_zh.chapter_templates import initialize_chapter_templates
from stacks_zh.cli import main
from stacks_zh.records import RecordError

ROOT=Path(__file__).resolve().parents[1]


def fixture(base, *, blocked=False, large=False):
    statement=LIST
    if blocked:
        statement=statement.replace('First object.', 'First \\unknown{object}.')
    if large:
        statement=statement.replace('Choose two objects.', ' '.join(['object']*1601)+'.')
    root,harvest,_=english_fixture(base,statement=statement)
    source=harvest/'test.tex'
    source.write_text(source.read_text().replace('\\begin{document}\n',
        '\\begin{document}\n\\title{Synthetic chapter}\n\\maketitle\n\\phantomsection\n\\label{section-phantom}\n\\tableofcontents\n'))
    tags=harvest/'tags/tags';tags.write_text(tags.read_text()+'0003,test-item-first\n0004,test-item-second\n000Z,test-section-phantom\n')
    (harvest/'chapters.tex').write_text('\\item \\hyperref[test-section-phantom]{Synthetic chapter}\n')
    git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic native header and item Tags')
    git(harvest,'remote','add','origin','https://example.invalid/synthetic-english.git')
    source_commit=git(harvest,'rev-parse','HEAD');date=git(harvest,'show','-s','--format=%cs','HEAD')
    (root/'upstream.lock').write_text(f'repository = "https://example.invalid/synthetic-english.git"\ncommit = "{source_commit}"\ncommit_date = "{date}"\n')
    shutil.copyfile(ROOT/'config/workflow.yml',root/'config/workflow.yml')
    (root/'.gitignore').write_text('build/\nsource-ir/\n')
    initialize_chapter_templates(root,harvest,root/'upstream.lock',root/'translation-data/units',root/'translation-data/chapter-templates',check=False)
    git(root,'init','-q');git(root,'add','.');git(root,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic preparation only')
    return root,harvest


def run(root,harvest,**kwargs):
    return run_chapter_preflight(root,harvest,'test',**kwargs)


def read_output(result):
    output=Path(result['output'])
    report=json.loads((output/'preflight.json').read_text())
    entries=[json.loads(line) for line in (output/'containers.jsonl').read_text().splitlines()]
    packages=json.loads((output/'packages.json').read_text())
    return output,report,entries,packages


class ChapterPreflightTests(unittest.TestCase):
    def test_complete_native_header_and_list_tags_are_ready_without_any_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d))
            initial=git(root,'status','--porcelain')
            result=run(root,harvest)
            _,report,entries,packages=read_output(result)
            self.assertEqual(report['state'],'READY')
            self.assertFalse(report['adopted'])
            self.assertEqual(report['candidates']['current_qa'],'NOT_RUN')
            self.assertEqual(report['candidates']['candidate_units'],0)
            tags={row['tag']:row for row in report['tags']}
            self.assertTrue(all(tags[tag]['source_ready'] for tag in ['0000','0001','0003','0004','000Z']))
            lemma=next(e for e in entries if e['selector']['kind']=='lemma')
            self.assertEqual(lemma['capabilities']['native_list_tags'],['0003','0004'])
            header=next(e for e in entries if e['selector']['kind']=='title_title')
            self.assertEqual(header['source_contract'],'source-adoption-v4')
            self.assertTrue(any(p['exceptions'] for p in packages['packages']))
            flattened=[key for f in packages['files'] for key in f['container_ids']]
            self.assertEqual(len(flattened),len(set(flattened)))
            self.assertEqual(set(flattened),{e['id'] for e in entries if e['state']=='READY'})
            ownership=[name for p in packages['packages'] for name in p['prospective_file_ownership']]
            self.assertEqual(len(ownership),len(set(ownership)))
            self.assertEqual(git(root,'status','--porcelain'),initial)
            self.assertFalse((root/'translation-data/candidates').exists())

    def test_unknown_macro_remains_blocked_and_require_ready_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d),blocked=True)
            result=run(root,harvest,require_ready=True)
            _,report,entries,_=read_output(result)
            self.assertEqual(result['exit_code'],1)
            self.assertEqual(report['state'],'BLOCKED')
            self.assertTrue(any('unknown' in reason.lower() for entry in entries for reason in entry['reasons']))
            tags={row['tag']:row for row in report['tags']}
            self.assertFalse(tags['0003']['source_ready'])
            self.assertTrue(tags['0000']['source_ready'])

    def test_repeat_is_byte_and_mtime_idempotent_and_check_is_readonly(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d));first=run(root,harvest)
            output=Path(first['output']);before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()}
            second=run(root,harvest)
            self.assertEqual(first['fingerprint'],second['fingerprint'])
            self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()})
            state=root/'build/chapter-preflight-state'
            state_before={str(p.relative_to(state)):(p.read_bytes(),p.stat().st_mtime_ns) for p in state.rglob('*') if p.is_file()}
            self.assertEqual(run(root,harvest,check=True)['stage'],'CHECKED')
            self.assertEqual(state_before,{str(p.relative_to(state)):(p.read_bytes(),p.stat().st_mtime_ns) for p in state.rglob('*') if p.is_file()})

    def test_input_drift_invalidates_resume_and_preserves_original_package(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d));first=run(root,harvest)
            output=Path(first['output']);old={p.name:p.read_bytes() for p in output.iterdir()}
            path=root/'config/workflow.yml';path.write_bytes(path.read_bytes()+b'\n# changed preparation input\n')
            with self.assertRaisesRegex(RecordError,'inputs changed'):
                run(root,harvest,resume=True)
            changed=run(root,harvest)
            self.assertNotEqual(first['fingerprint'],changed['fingerprint'])
            self.assertEqual(old,{p.name:p.read_bytes() for p in output.iterdir()})

    def test_interrupted_preparation_resumes_verified_source_without_lowering_twice(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d))
            def interrupt(event):
                if event['verified']==2:
                    raise KeyboardInterrupt('synthetic interruption after durable checkpoint')
            with self.assertRaises(KeyboardInterrupt):run(root,harvest,_observe=interrupt)
            from stacks_zh import chapter_preflight as module
            calls=[];actual=module.lower_container
            def lowering(selected,*args,**kwargs):
                calls.append(selected['selector']);return actual(selected,*args,**kwargs)
            reused=[]
            with patch.object(module,'lower_container',lowering):
                result=run(root,harvest,resume=True,_observe=lambda event:reused.append(event['reused']))
            self.assertEqual(reused[:2],[True,True])
            self.assertEqual(len(calls),len(reused)-2)
            self.assertEqual(result['report']['state'],'READY')
            attempts=list((root/'build/chapter-preflight-state/attempts').glob('*.json'))
            self.assertEqual(len(attempts),2)
            self.assertEqual(json.loads(attempts[0].read_text())['exit_code'],130)

    def test_indivisible_large_container_is_retained_and_exception_explained(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d),large=True)
            _,_,entries,packages=read_output(run(root,harvest))
            large=next(e for e in entries if e['selector']['kind']=='lemma')
            package=next(p for p in packages['packages'] if p['source_word_count']>1500)
            self.assertGreater(large['source_word_count'],1500)
            self.assertTrue(package['exceptions'])
            self.assertLessEqual(package['file_count'],8)

    def test_output_symlink_or_tamper_and_mid_preparation_drift_never_publish(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d));seen=[]
            def drift(event):
                if not seen:
                    seen.append(True);path=root/'config/workflow.yml';path.write_bytes(path.read_bytes()+b'\n# transient fixture drift\n')
            with self.assertRaisesRegex(RecordError,'changed'):
                run(root,harvest,_observe=drift)
            self.assertFalse(list((root/'build/chapter-preflight').glob('test/*/manifest.json')))
            result=run(root,harvest);output=Path(result['output']);target=output/'preflight.json'
            target.write_bytes(target.read_bytes()+b' ')
            with self.assertRaisesRegex(RecordError,'stale or changed'):run(root,harvest,check=True)

    def test_existing_bad_candidate_does_not_grant_approval_or_change_source_readiness(self):
        from test_validation_session import prepare
        from stacks_zh.extraction import write_inventory
        with tempfile.TemporaryDirectory() as d:
            root,harvest,_,candidates,_=prepare(Path(d))
            git(harvest,'remote','add','origin','https://example.invalid/synthetic-english.git')
            commit=git(harvest,'rev-parse','HEAD');date=git(harvest,'show','-s','--format=%cs','HEAD')
            (root/'upstream.lock').write_text(f'repository = "https://example.invalid/synthetic-english.git"\ncommit = "{commit}"\ncommit_date = "{date}"\n')
            initialize_chapter_templates(root,harvest,root/'upstream.lock',root/'translation-data/units',root/'translation-data/chapter-templates',check=False)
            write_inventory(root,harvest,root/'source-ir/extraction')
            rows=[json.loads(line) for line in candidates[0].read_text().splitlines()]
            rows[0]['translation']+=' extra unvalidated text'
            candidates[0].write_text('\n'.join(json.dumps(row,ensure_ascii=False) for row in rows)+'\n')
            with patch('stacks_zh.provenance._validate_repository_provenance',side_effect=AssertionError('preflight must not replay model history')):
                result=run(root,harvest)
            self.assertTrue(result['report']['source_ready'])
            self.assertEqual(result['report']['candidates']['current_qa'],'BLOCKED')
            self.assertTrue(result['report']['candidates']['current_qa_errors'])
            self.assertEqual(result['report']['candidates']['human_review_approval'],'NOT_GRANTED_BY_PREFLIGHT')

    def test_checkpoint_tamper_and_late_chapter_header_are_not_ready(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d))
            source=harvest/'test.tex';source.write_text(source.read_text().replace('\\title{Synthetic chapter}', 'Natural language before the header.\n\\title{Synthetic chapter}'))
            git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic unsupported late header')
            commit=git(harvest,'rev-parse','HEAD');date=git(harvest,'show','-s','--format=%cs','HEAD')
            (root/'upstream.lock').write_text(f'repository = "https://example.invalid/synthetic-english.git"\ncommit = "{commit}"\ncommit_date = "{date}"\n')
            initialize_chapter_templates(root,harvest,root/'upstream.lock',root/'translation-data/units',root/'translation-data/chapter-templates',check=False)
            _,report,entries,_=read_output(run(root,harvest))
            header=next(e for e in entries if e['selector']['kind']=='title_title')
            self.assertEqual(header['state'],'BLOCKED')
            self.assertTrue(any('first natural-language' in reason for reason in header['reasons']))
            self.assertEqual(report['state'],'BLOCKED')

    def test_progress_review_filters_and_nonsection_source_contract_are_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d))
            first=run(root,harvest);_,_,entries,_=read_output(first)
            unit=entries[0]['units'][0]
            path=root/'translation-data/units/header.jsonl';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(unit)+'\n')
            reviews=root/'translation-data/reviewed';reviews.mkdir()
            for name,commit,status in [('current',unit['source_commit'],'CURRENT'),('old','0'*40,'CURRENT'),('stale',unit['source_commit'],'STALE_TEXT')]:
                (reviews/(name+'.json')).write_text(json.dumps(dict(unit_id=unit['unit_id'],status='current',source_commit=commit,source_status=status,stage='LANGUAGE_REVIEWED')))
            result=run(root,harvest)
            records=result['report']['candidates']['declared_current_reviewed_records']
            self.assertEqual([row['path'] for row in records],['translation-data/reviewed/current.json'])
            source=harvest/'test.tex';source.write_text(source.read_text().replace('\\section{Basics}', 'Introductory source before the first Section.\n\n\\section{Basics}'))
            git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic chapter-parent source')
            commit=git(harvest,'rev-parse','HEAD');date=git(harvest,'show','-s','--format=%cs','HEAD')
            (root/'upstream.lock').write_text(f'repository = "https://example.invalid/synthetic-english.git"\ncommit = "{commit}"\ncommit_date = "{date}"\n')
            initialize_chapter_templates(root,harvest,root/'upstream.lock',root/'translation-data/units',root/'translation-data/chapter-templates',check=False)
            _,_,containers,packages=read_output(run(root,harvest))
            intro=next(e for e in containers if e['selector']['kind']=='prose_block' and e['selector']['parent_tag']=='000Z')
            self.assertEqual(intro['state'],'READY')
            self.assertFalse(intro['contract_support']['first_adoption_shape'])
            self.assertFalse(intro['contract_support']['automatic_adoption_permission'])
            self.assertIn('no first-adoption contract',intro['source_contract'])
            for file in packages['files']:
                parents={entry['selector']['parent_tag'] for entry in containers if entry['id'] in file['container_ids']}
                self.assertEqual(parents,{file['parent_tag']})

    def test_bound_git_template_identity_and_unregistered_actual_reads_fail_closed(self):
        from stacks_zh.validation_io import read_bytes
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d));path=root/'translation-data/chapter-templates/test.json'
            original=path.read_bytes();value=json.loads(original);value['sections'][0]['source_title']='Invented title';path.write_text(json.dumps(value))
            with self.assertRaisesRegex(RecordError,'Section metadata differs'):
                run(root,harvest)
            path.write_bytes(original)
            outside=root/'unregistered-source.json';outside.write_text('{}')
            with self.assertRaisesRegex(RecordError,'outside the bound dependency inventory'):
                run(root,harvest,_observe=lambda event:read_bytes(outside))
            self.assertFalse(list((root/'build/chapter-preflight').glob('test/*/manifest.json')))

    def test_output_symlink_cannot_write_into_english_harvest(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d));target=root/'build/source-alias';target.parent.mkdir(exist_ok=True);target.symlink_to(harvest,target_is_directory=True)
            before={str(p.relative_to(harvest)):p.read_bytes() for p in harvest.rglob('*') if p.is_file()}
            with self.assertRaises(RecordError):
                run(root,harvest,output=target)
            self.assertEqual(before,{str(p.relative_to(harvest)):p.read_bytes() for p in harvest.rglob('*') if p.is_file()})

    def test_locked_git_object_view_drift_without_head_or_worktree_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d));original=git(harvest,'rev-parse','HEAD')
            def input_git(args,raw,**kwargs):
                return subprocess.run(['git','-C',str(harvest),*args],input=raw,capture_output=True,check=True,**kwargs).stdout.decode().strip()
            blob=input_git(['hash-object','-w','--stdin'],(harvest/'test.tex').read_bytes()+b'\n% alternate Git object view\n')
            lines=[]
            for line in git(harvest,'ls-tree','HEAD').splitlines():
                if line.endswith('\ttest.tex'):
                    prefix,name=line.split('\t');mode,kind,_=prefix.split();line=f'{mode} {kind} {blob}\t{name}'
                lines.append(line)
            tree=input_git(['mktree'],('\n'.join(lines)+'\n').encode())
            date=git(harvest,'show','-s','--format=%cI','HEAD')
            replacement=input_git(['-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit-tree',tree],b'Synthetic alternate view\n',env=dict(os.environ,GIT_AUTHOR_DATE=date,GIT_COMMITTER_DATE=date))
            changed=[]
            def drift(event):
                if not changed:
                    git(harvest,'replace',original,replacement);changed.append(True)
            with self.assertRaisesRegex(RecordError,'Git blob changed'):
                run(root,harvest,_observe=drift)
            self.assertEqual(git(harvest,'rev-parse','HEAD'),original)
            self.assertFalse(list((root/'build/chapter-preflight').glob('test/*/manifest.json')))

    def test_cli_help_real_command_and_failure_exit(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out),self.assertRaises(SystemExit) as exit_:
            main(['chapter-preflight','--help'])
        self.assertEqual(exit_.exception.code,0);self.assertIn('--resume',out.getvalue())
        with tempfile.TemporaryDirectory() as d:
            root,harvest=fixture(Path(d),blocked=True)
            command=[sys.executable,str(ROOT/'stacks_zh.py'),'chapter-preflight','--root',str(root),
                     '--harvest',str(harvest),'--chapter','1','--require-ready','--json']
            process=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(process.returncode,1,process.stderr)
            self.assertEqual(json.loads(process.stdout)['report']['state'],'BLOCKED')
            attempts=list((root/'build/chapter-preflight-state/attempts').glob('*.json'))
            self.assertEqual(json.loads(attempts[0].read_text())['exit_code'],1)


if __name__=='__main__':unittest.main()
