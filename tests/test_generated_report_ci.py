"""Real generators and independent accepted Git fixtures, never caller PASS reports."""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stacks_zh import generated_reports as reports, progress, planning
from stacks_zh.ci_scope import classify
from stacks_zh.records import RecordError

TOOLS = Path(__file__).resolve().parents[1]


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def commit(root, message):
    git(root, 'add', '.')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', message)
    return git(root, 'rev-parse', 'HEAD')


class GeneratedReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'Chinese'
        self.english = Path(self.tmp.name) / 'English'
        self.root.mkdir(); self.english.mkdir()
        (self.root / '.gitignore').write_text('build/\n__pycache__/\n')
        git(self.english, 'init', '-q')
        git(self.english, 'remote', 'add', 'origin', 'https://github.com/stacks/stacks-project')
        (self.english / 'tags').mkdir()
        (self.english / 'tags/tags').write_text('AAAA,alpha-section-first\n')
        (self.english / 'alpha.tex').write_text('\\section{First}\n\\label{section-first}\nText.\n')
        (self.english / 'preamble.tex').write_text('% synthetic English\n')
        self.source = commit(self.english, 'synthetic locked source')
        for name in ['stacks_zh', 'schema', 'config']:
            shutil.copytree(TOOLS / name, self.root / name, ignore=shutil.ignore_patterns('__pycache__', 'local.mk'))
        (self.root / 'scripts').mkdir()
        shutil.copyfile(TOOLS / 'scripts/ci-current.py', self.root / 'scripts/ci-current.py')
        (self.root / 'upstream.lock').write_text('repository = "https://github.com/stacks/stacks-project"\ncommit = "' + self.source + '"\n')
        (self.root / 'README.md').write_text('# Non-generated contract\n' + progress.README_START + '\nold\n' + progress.README_END + '\nBetween\n' + planning.README_START + '\nold\n' + planning.README_END + '\nTail\n')
        (self.root / 'docs').mkdir()
        for name in ['translation-progress.md', 'translation-plan.md']:
            (self.root / 'docs' / name).write_text('old\n')
        def write(name, data):
            path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data) + '\n')
        write('config/chapter-titles.json', {'schema_version': 1, 'titles': {'alpha': '甲'}})
        policy = json.loads((self.root / 'config/translation-priorities.json').read_text())
        policy['chapters'] = {'alpha': {'priority': 'P0', 'wave': 1, 'order': 1, 'tracks': ['test'], 'reason': 'fixture'}}
        write('config/translation-priorities.json', policy)
        write('translation-data/chapter-templates/alpha.json', {'chapter': 'alpha', 'chapter_ordinal': 1, 'source_commit': self.source, 'source_state': 'CURRENT', 'source_file': 'alpha.tex', 'sections': [{'ordinal': 1, 'source_title': 'First', 'source_label': 'alpha-section-first', 'parent_tag': 'AAAA', 'state': 'READY', 'unit_files': ['translation-data/units/alpha.jsonl']}]})
        unit = {'unit_id': 'tag:AAAA:title', 'parent_tag': 'AAAA', 'chapter': 'alpha', 'source_commit': self.source, 'source_status': 'CURRENT', 'risk_level': 'R1'}
        write('translation-data/units/alpha.jsonl', unit)
        write('translation-data/candidates/model/alpha.jsonl', unit)
        git(self.root, 'init', '-q'); git(self.root, 'config', 'core.fileMode', 'true')
        self.base = commit(self.root, 'synthetic accepted facts with stale reports')
        git(self.root, 'update-ref', 'refs/remotes/origin/main', self.base)
        git(self.root, 'checkout', '-qb', 'tool/reports')
        progress.update_progress_report(self.root, self.english / 'tags/tags', self.root / 'README.md', self.root / 'docs/translation-progress.md', check=False)
        planning.update_translation_plan(self.root, self.root / 'README.md', self.root / 'docs/translation-plan.md', check=False)

    def test_real_combined_reports_pass_without_writing_or_data_qa(self):
        self.assertEqual(classify(self.root, self.base)['kind'], 'generated-reports')
        before = {p: (self.root / p).read_bytes() for p in reports.REPORT_FILES}
        result = reports.check_generated_reports(self.root, self.english, self.base)
        self.assertEqual(result['scope'], 'generated-reports')
        self.assertEqual(set(result['stages']), {'progress-check', 'plan-check'})
        self.assertEqual([result[x] for x in ['data_qa', 'history_audit', 'tool_tests']], ['not_run'] * 3)
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in reports.REPORT_FILES})

    def test_progress_only_and_plan_only_have_both_checks(self):
        valid = {p: (self.root / p).read_bytes() for p in reports.REPORT_FILES}
        stale = {p: subprocess.check_output(['git','-C',str(self.root),'show',self.base+':'+p]) for p in reports.REPORT_FILES}
        for module, doc in [(progress, 'translation-progress.md'), (planning, 'translation-plan.md')]:
            with self.subTest(doc=doc):
                # The other report is already current at this accepted base.
                for p, raw in valid.items(): (self.root / p).write_bytes(raw)
                name = 'docs/' + doc
                (self.root / name).write_bytes(stale[name])
                readme = (self.root / 'README.md').read_text()
                (self.root / 'README.md').write_text(module._replace_readme_block(readme, 'old'))
                base = commit(self.root, 'accepted fixture with one stale report')
                git(self.root, 'update-ref', 'refs/remotes/origin/main', base)
                if module is progress:
                    module.update_progress_report(self.root, self.english / 'tags/tags', self.root / 'README.md', self.root / 'docs' / doc, check=False)
                else:
                    module.update_translation_plan(self.root, self.root / 'README.md', self.root / 'docs' / doc, check=False)
                self.assertEqual(classify(self.root, base)['paths'], ['README.md', name])
                result = reports.check_generated_reports(self.root, self.english, base)
                self.assertEqual(set(result['stages']), {'progress-check', 'plan-check'})

    def test_readme_outside_changes_expand(self):
        p = self.root / 'README.md'
        p.write_text(p.read_text().replace('Non-generated contract', 'Changed policy'))
        self.assertEqual(classify(self.root, self.base)['kind'], 'current-all')

    def test_missing_duplicate_reversed_and_nested_markers_fail(self):
        p = self.root / 'README.md'; original = p.read_text()
        variants = [original.replace(progress.README_START, ''), original + planning.README_START,
                    original.replace(progress.README_START, 'temporary').replace(progress.README_END, progress.README_START).replace('temporary', progress.README_END),
                    progress.README_START + planning.README_START + progress.README_END + planning.README_END]
        for text in variants:
            with self.subTest(text=text[:60]):
                p.write_text(text)
                with self.assertRaises(RecordError): classify(self.root, self.base)

    def test_manual_numbers_stale_text_and_crlf_fail_without_overwrite(self):
        for name in ['docs/translation-progress.md', 'docs/translation-plan.md']:
            p = self.root / name; original = p.read_bytes()
            for raw in [original + b'forged statistics\n', b'old\n', original.replace(b'\n', b'\r\n')]:
                with self.subTest(path=name,raw=raw[:30]):
                    p.write_bytes(raw)
                    with self.assertRaises(RecordError): reports.check_generated_reports(self.root, self.english, self.base)
                    self.assertEqual(p.read_bytes(),raw)
            p.write_bytes(original)

    def test_public_unknown_and_fact_mixture_never_narrows(self):
        for name in ['config/glossary.yml','stacks_zh/progress.py','stacks_zh/ci_scope.py',
                     'scripts/ci-current.py','Makefile','WORKFLOW.md','unknown.md',
                     'translation-data/candidates/model/alpha.jsonl']:
            p = self.root / name; original = p.read_bytes() if p.exists() else None
            with self.subTest(path=name):
                p.write_bytes((original or b'') + b'\n')
                self.assertEqual(classify(self.root,self.base)['kind'],'current-all')
                self.assertEqual(classify(self.root,self.base,paths=['README.md'])['kind'],'current-all')
            if original is None: p.unlink()
            else: p.write_bytes(original)

    def test_delete_rename_and_mode_expand_and_symlink_fails(self):
        p = self.root / 'docs/translation-plan.md'; raw = p.read_bytes()
        p.unlink(); self.assertEqual(classify(self.root,self.base)['kind'],'current-all'); p.write_bytes(raw)
        p.rename(p.with_name('renamed.md')); self.assertEqual(classify(self.root,self.base)['kind'],'current-all'); p.with_name('renamed.md').rename(p)
        p.chmod(0o755); self.assertEqual(classify(self.root,self.base)['kind'],'current-all'); p.chmod(0o644)
        git(self.root,'config','core.fileMode','false');git(self.root,'update-index','--chmod=+x','docs/translation-plan.md')
        self.assertEqual(classify(self.root,self.base)['kind'],'current-all')
        git(self.root,'update-index','--chmod=-x','docs/translation-plan.md')
        p.unlink();p.symlink_to(self.english/'alpha.tex')
        self.assertEqual(classify(self.root,self.base)['kind'],'current-all')

    def test_missing_bad_untrusted_and_nonancestor_base_fail(self):
        for base in ['', 'not-a-ref']:
            with self.subTest(base=base),self.assertRaises(RecordError): classify(self.root,base)
        head = commit(self.root,'reports on unaccepted branch')
        with self.assertRaises(RecordError): classify(self.root,head,paths=['README.md'])
        parent = git(self.root,'rev-parse',self.base+'^{tree}')
        side = subprocess.check_output(['git','-C',str(self.root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit-tree',parent,'-p',self.base,'-m','sibling baseline'],text=True).strip()
        git(self.root,'update-ref','refs/remotes/origin/main',side)
        with self.assertRaises(RecordError): classify(self.root,side,paths=['README.md'])

    def test_transient_consumed_input_change_then_restore_is_detected(self):
        original_read = progress.read_text
        def changed(path,*args,**kwargs):
            path = Path(path)
            if 'candidates' not in path.parts: return original_read(path,*args,**kwargs)
            raw = path.read_bytes(); value=json.loads(raw);value['transient']=True
            path.write_text(json.dumps(value)+'\n')
            try: return original_read(path,*args,**kwargs)
            finally: path.write_bytes(raw)
        with patch.object(progress,'read_text',side_effect=changed),self.assertRaises(RecordError):
            reports.check_generated_reports(self.root,self.english,self.base)

    def test_transient_source_coverage_metadata_cannot_escape_binding(self):
        from stacks_zh import progress_coverage
        p=self.root/'translation-data/derivations/old-metadata.json'
        p.parent.mkdir(parents=True)
        p.write_text('{"tool":{"version":"3"}}\n')
        # The record is accepted but is skipped by the current v4 coverage query.
        for name in reports.REPORT_FILES:
            raw=subprocess.check_output(['git','-C',str(self.root),'show',self.base+':'+name])
            (self.root/name).write_bytes(raw)
        base=commit(self.root,'accepted non-current coverage metadata')
        git(self.root,'update-ref','refs/remotes/origin/main',base)
        progress.update_progress_report(self.root,self.english/'tags/tags',self.root/'README.md',self.root/'docs/translation-progress.md',check=False)
        planning.update_translation_plan(self.root,self.root/'README.md',self.root/'docs/translation-plan.md',check=False)
        original_read=progress_coverage.read_text
        def changed(path,*args,**kwargs):
            if Path(path).resolve()!=p.resolve():return original_read(path,*args,**kwargs)
            raw=p.read_bytes();p.write_text('{"tool":{"version":"2"}}\n')
            try:return original_read(path,*args,**kwargs)
            finally:p.write_bytes(raw)
        with patch.object(progress_coverage,'read_text',side_effect=changed),self.assertRaises(RecordError):
            reports.check_generated_reports(self.root,self.english,base)

    def test_transient_archive_membership_cannot_hide_current_coverage(self):
        from stacks_zh import progress_coverage
        real_glob=progress_coverage.glob_paths
        directory=self.root/'translation-data/derivation-archives'
        def changed(path,*args,**kwargs):
            if Path(path).resolve()!=directory.resolve():return real_glob(path,*args,**kwargs)
            directory.mkdir();p=directory/'transient.json';p.write_text('{}\n')
            try:return real_glob(path,*args,**kwargs)
            finally:p.unlink();directory.rmdir()
        with patch.object(progress_coverage,'glob_paths',side_effect=changed),self.assertRaises(RecordError):
            reports.check_generated_reports(self.root,self.english,self.base)

    def test_head_source_identity_and_input_inventory_changes_fail(self):
        real = planning.update_translation_plan
        for change in ['head','source','inventory','main']:
            with self.subTest(change=change):
                def changed(*args,**kwargs):
                    result=real(*args,**kwargs)
                    if change=='head': commit(self.root,'new HEAD during checks')
                    elif change=='source':
                        (self.english/'alpha.tex').write_text('changed\n');commit(self.english,'new English identity')
                    elif change=='main':
                        side=git(self.root,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                                 'commit-tree',self.base+'^{tree}','-p',self.base,'-m','anchor drift')
                        git(self.root,'update-ref','refs/remotes/origin/main',side)
                    else: (self.root/'translation-data/units/hidden.jsonl').write_text('{}\n')
                    return result
                with patch.object(planning,'update_translation_plan',side_effect=changed),self.assertRaises(RecordError):
                    reports.check_generated_reports(self.root,self.english,self.base)
                if change=='head': git(self.root,'reset','--soft',self.base)
                elif change=='source': git(self.english,'reset','--hard',self.source)
                elif change=='main': git(self.root,'update-ref','refs/remotes/origin/main',self.base)
                else: (self.root/'translation-data/units/hidden.jsonl').unlink()

    def test_inconsistent_generator_output_cannot_pass(self):
        real = progress.render_chapter_report
        with patch.object(progress,'render_chapter_report',side_effect=lambda value:real(value)+'unstable\n'),self.assertRaises(RecordError):
            reports.check_generated_reports(self.root,self.english,self.base)

    def test_changed_external_validator_cannot_self_certify(self):
        tools = Path(self.tmp.name)/'ChangedTools'
        shutil.copytree(self.root,tools)
        (tools/'stacks_zh/ci_scope.py').write_text('forged validator\n')
        with patch.object(reports,'__file__',str(tools/'stacks_zh/generated_reports.py')),self.assertRaises(RecordError):
            reports.check_generated_reports(self.root,self.english,self.base)

    def test_hidden_english_worktree_changes_still_require_locked_git_bytes(self):
        path=self.english/'alpha.tex';raw=path.read_bytes()
        git(self.english,'update-index','--assume-unchanged','alpha.tex')
        path.write_bytes(raw.replace(b'Text.',b'Hidden changed prose.'))
        self.assertEqual(git(self.english,'status','--porcelain','--untracked-files=no'),'')
        with self.assertRaisesRegex(RecordError,'English source differs from locked Git'):
            reports.check_generated_reports(self.root,self.english,self.base)

    def test_driver_report_path_runs_checks_once_and_no_broad_commands(self):
        spec=importlib.util.spec_from_file_location('generated_ci_driver',TOOLS/'scripts/ci-current.py')
        driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
        commands=[]; real_run=subprocess.run
        def called(command,**kwargs):
            if command[0]=='git':return real_run(command,**kwargs)
            commands.append(command);return subprocess.CompletedProcess(command,0)
        argv=['ci-current','--root',str(self.root),'--harvest',str(self.english),'--base-ref',self.base]
        with patch.object(sys,'argv',argv),patch.object(driver.subprocess,'run',side_effect=called),patch.object(progress,'update_progress_report',wraps=progress.update_progress_report) as pc,patch.object(planning,'update_translation_plan',wraps=planning.update_translation_plan) as lc,patch.object(driver,'check_current_repository',side_effect=AssertionError('data QA forbidden')):
            driver.run()
        self.assertEqual(pc.call_count,1);self.assertEqual(lc.call_count,1)
        self.assertEqual([x[1] for x in commands],['workflow-check','harvest-check'])
        payload=json.loads((self.root/'build/ci-current/reports.json').read_text())
        self.assertEqual(payload['scope'],'generated-reports')

    def test_pr_and_main_event_ranges_dispatch_equally(self):
        head=commit(self.root,'real generated report changes')
        identities=[]
        for event in ['pull_request','push']:
            with self.subTest(event=event):
                # These are the exact before/base and head identities installed
                # by the shared workflow shell for both kinds of event.
                base=git(self.root,'merge-base',self.base,head)
                git(self.root,'update-ref','refs/remotes/origin/main',self.base)
                identities.append(classify(self.root,base))
                result=reports.check_generated_reports(self.root,self.english,base)
                self.assertEqual(result['head'],head)
                self.assertEqual(result['base'],self.base)
        self.assertEqual(identities[0],identities[1])

    def test_forced_and_public_changes_keep_broad_make_contract(self):
        spec=importlib.util.spec_from_file_location('report_broad_driver',TOOLS/'scripts/ci-current.py')
        driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
        for force in [True,False]:
            with self.subTest(force=force):
                if not force: (self.root/'Makefile').write_text('# public build change\n')
                commands=[];real_run=subprocess.run
                def called(command,**kwargs):
                    if command[0]=='git': return real_run(command,**kwargs)
                    commands.append(command[1]);return subprocess.CompletedProcess(command,0)
                argv=['ci-current','--root',str(self.root),'--harvest',str(self.english),'--base-ref',self.base]
                if force: argv.append('--force-broad')
                with patch.object(sys,'argv',argv),patch.object(driver.subprocess,'run',side_effect=called),patch.object(driver,'check_generated_reports',side_effect=AssertionError('narrow check forbidden')):
                    driver.run()
                self.assertEqual(commands,['workflow-check','harvest-check','tool-test','qa-current-all',
                                           'upstream-index-check','chapter-template-check','progress-check','plan-check'])

    def test_failed_checks_remove_forged_previous_receipt(self):
        spec=importlib.util.spec_from_file_location('report_failed_driver',TOOLS/'scripts/ci-current.py')
        driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
        out=self.root/'build/ci-current/reports.json';out.parent.mkdir(parents=True)
        out.write_text('{"scope":"generated-reports","exit_status":0}')
        (self.root/'docs/translation-plan.md').write_text('forged report\n')
        argv=['ci-current','--root',str(self.root),'--harvest',str(self.english),'--base-ref',self.base]
        real_run=subprocess.run
        def called(command,**kwargs):
            if command[0]=='git':return real_run(command,**kwargs)
            return subprocess.CompletedProcess(command,0)
        with patch.object(sys,'argv',argv),patch.object(driver.subprocess,'run',side_effect=called),self.assertRaises(RecordError):
            driver.run()
        self.assertFalse(out.exists())
