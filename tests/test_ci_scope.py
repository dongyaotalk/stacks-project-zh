"""Real Git diffs and structured ownership; no filename or caller PASS shortcut."""
import json
import os
import textwrap
import importlib.util
import sys
from unittest.mock import patch
import subprocess
import tempfile
import unittest
from pathlib import Path
from stacks_zh.ci_scope import classify
from stacks_zh.records import RecordError

TOOLS = Path(__file__).resolve().parents[1]


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()


class CIScopeTests(unittest.TestCase):
    def prepare(self,root):
        git(root,'init','-q');git(root,'config','core.fileMode','true')
        for name,chapter,uid in [('misleading-etale','alpha','a'),('ordinary','beta','b')]:
            path=root/'translation-data/units'/(name+'.jsonl');path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(dict(unit_id=uid,chapter=chapter))+'\n')
        git(root,'add','.');git(root,'-c','user.name=Synthetic','-c','user.email=test@example.invalid','commit','-qm','synthetic accepted units')
        return git(root,'rev-parse','HEAD')

    def test_semantic_ownership_shared_run_and_unknown_participants(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=self.prepare(root)
            path=root/'translation-data/runs/shared.json';path.parent.mkdir(parents=True)
            path.write_text(json.dumps(dict(unit_ids=['a','b'])))
            self.assertEqual(classify(root,base,paths=[path.relative_to(root).as_posix()])['chapters'],['alpha','beta'])
            path.write_text(json.dumps(dict(unit_ids=['a','hidden'])))
            self.assertEqual(classify(root,base,paths=[path.relative_to(root).as_posix()])['kind'],'current-all')
            path.write_text(json.dumps(dict(chapter='alpha',context=dict(chapter='unrelated-old-context'))))
            self.assertEqual(classify(root,base,paths=[path.relative_to(root).as_posix()])['chapters'],['alpha'])

    def test_full_diff_mode_rename_delete_and_policy_mixture_expand(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=self.prepare(root);path=root/'translation-data/units/misleading-etale.jsonl'
            path.chmod(0o755)
            self.assertEqual(classify(root,base)['kind'],'current-all')
            path.chmod(0o644);git(root,'mv',str(path.relative_to(root)),'translation-data/units/renamed.jsonl')
            self.assertEqual(classify(root,base)['kind'],'current-all')
            self.assertEqual(classify(root,base,paths=['translation-data/units/ordinary.jsonl','config/glossary.yml'])['kind'],'current-all')
            self.assertEqual(classify(root,base,paths=['stacks_zh/ci_scope.py'])['kind'],'current-all')
            self.assertEqual(classify(root,base,paths=['docs/notes/description.md'])['kind'],'documentation')

    def test_bad_json_duplicate_id_unknown_and_unowned_input_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=self.prepare(root)
            path=root/'translation-data/runs/bad.json';path.parent.mkdir(parents=True);path.write_text('{bad')
            with self.assertRaises(RecordError):classify(root,base,paths=[path.relative_to(root).as_posix()])
            path.write_text('{}')
            self.assertEqual(classify(root,base,paths=[path.relative_to(root).as_posix()])['kind'],'current-all')
            self.assertEqual(classify(root,base,paths=['unknown/path'])['kind'],'current-all')
            (root/'translation-data/units/duplicate.jsonl').write_text('{"unit_id":"a","chapter":"beta"}\n')
            with self.assertRaises(RecordError):classify(root,base,paths=[path.relative_to(root).as_posix()])

    def workflow_script(self, path, step):
        step_body = (TOOLS / path).read_text().split(f'name: {step}\n', 1)[1]
        body = step_body.split('run: |\n', 1)[1]
        indent = len(body) - len(body.lstrip(' '))
        lines = []
        for line in body.splitlines():
            if line.strip() and not line.startswith(' ' * indent):
                break
            lines.append(line)
        return textwrap.dedent('\n'.join(lines)) + '\n'

    def test_workflow_uses_actual_event_identity_and_base_driver(self):
        workflow = (TOOLS / '.github/workflows/ci.yml').read_text()
        self.assertIn('ref: ${{ github.event.pull_request.head.sha || github.sha }}', workflow)
        self.assertEqual(workflow.count('- *checkout-chinese'), 2)
        self.assertIn('${{ github.event.pull_request.base.sha || github.event.before }}', workflow)
        self.assertIn('compare=$(git merge-base "$EVENT_BASE" "$EVENT_HEAD")', workflow)
        self.assertIn('"$TRUSTED_TOOLS/scripts/ci-current.py"', workflow)
        self.assertIn('needs: [classify, current-validation, tool-test]', workflow)
        self.assertEqual(workflow.count('needs: classify'), 2)
        self.assertIn('if: always()', workflow)
        self.assertNotIn('make qa-all', workflow)
        self.assertNotIn('pull_request_target', workflow)

    def test_required_summary_rejects_missing_cancelled_failed_and_unexpected_skips(self):
        script = self.workflow_script('.github/workflows/ci.yml',
                                      'Require all jobs selected by the trusted classification')
        for kind in ('current-all', 'chapter-current', 'generated-reports', 'documentation'):
            wanted = 'success' if kind == 'current-all' else 'skipped'
            valid = dict(CLASSIFICATION='success', KIND=kind, CURRENT='success', TOOLS=wanted)
            for change in ({}, *({field: status}
                                 for field in valid
                                 for status in ('failure', 'cancelled', 'skipped', '', 'success')
                                 if status != valid[field])):
                with self.subTest(kind=kind, change=change):
                    result = subprocess.run(['bash'], input=script, text=True,
                                            env=os.environ | valid | change, capture_output=True)
                    self.assertEqual(result.returncode == 0, not change, result.stdout + result.stderr)

    def test_pr_and_push_resolve_event_base_and_initial_push_selects_broad(self):
        resolve = self.workflow_script('.github/workflows/ci.yml',
                                       'Resolve the trusted event comparison')
        classify_script = self.workflow_script('.github/workflows/ci.yml',
                                                'Classify with the trusted comparison tools')
        for event in ('pull_request', 'push', 'initial-push'):
            with self.subTest(event=event), tempfile.TemporaryDirectory() as d:
                directory = Path(d)
                root = directory / 'repo'
                root.mkdir()
                base = self.prepare(root)
                p = root / 'translation-data/units/ordinary.jsonl'
                p.write_text(json.dumps(dict(unit_id='b', chapter='beta', changed=True))+'\n')
                git(root, 'add', '.')
                git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=test@example.invalid',
                    'commit', '-qm', 'event head')
                head = git(root, 'rev-parse', 'HEAD')
                output = directory / 'outputs'
                event_base = '0' * 40 if event == 'initial-push' else base
                env = os.environ | dict(EVENT_BASE=event_base, EVENT_HEAD=head, GITHUB_OUTPUT=str(output))
                subprocess.run(['bash'], cwd=root, input=resolve, text=True, env=env,
                               check=True, capture_output=True)
                values = dict(line.split('=', 1) for line in output.read_text().splitlines())
                self.assertEqual(values['compare'], head if event == 'initial-push' else base)
                self.assertEqual(git(root, 'rev-parse', 'origin/main'), values['compare'])
                self.assertEqual(values['trusted'], 'false' if event == 'initial-push' else 'true')
                if event == 'pull_request':
                    # Simulate a comparison with the legacy dispatcher. It
                    # contains the real classifier and must override HEAD.
                    trusted = directory / 'ci-trusted-tools'
                    git(root, 'worktree', 'add', '--detach', str(trusted), values['compare'])
                    (trusted / 'stacks_zh').symlink_to(TOOLS / 'stacks_zh', target_is_directory=True)
                    (trusted / 'scripts').mkdir()
                    (trusted / 'scripts/ci-current.py').touch()
                    (root / 'stacks_zh').mkdir()
                    (root / 'stacks_zh/ci_scope.py').write_text('raise AssertionError("HEAD classifier imported")')
                env.update(COMPARE=values['compare'], TRUSTED=values['trusted'],
                           PATH=str(Path(sys.executable).parent) + os.pathsep + env['PATH'])
                subprocess.run(['bash'], cwd=root, input=classify_script, text=True, env=env,
                               check=True, capture_output=True)
                expected = 'chapter-current' if event == 'pull_request' else 'current-all'
                self.assertIn('kind=' + expected, output.read_text().splitlines())

    def test_public_runner_requires_current_and_path_checks_without_tool_test(self):
        script = self.workflow_script('.github/workflows/ci.yml',
                                      'Run current validation and applicable checks')
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            base = self.prepare(root)
            for name in ('docs/progress.md', 'docs/translation-plan.md'):
                path = root / name
                path.parent.mkdir(exist_ok=True)
                path.write_text('Public change.\n')
            git(root, 'add', '.')
            git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=test@example.invalid',
                'commit', '-qm', 'broad fixture')
            # The shell runs the actual Make entry points on a runner. A log
            # executable isolates their scheduling from the heavyweight data.
            output = root / 'make.log'
            make = root / 'make'
            make.write_text('#!/bin/sh\nprintf "%s\\n" "$@" >> "$MAKE_LOG"\n')
            make.chmod(0o755)
            env = os.environ | dict(COMPARE=base, CLASSIFIED_COMPARE=base, KIND='current-all',
                                    MAKE_LOG=str(output), PATH=os.pathsep.join(
                                    [str(root), str(Path(sys.executable).parent), os.environ['PATH']]))
            subprocess.run(['bash'], cwd=root, input=script, text=True, env=env,
                           check=True, capture_output=True)
            commands = [arg for arg in output.read_text().splitlines() if '=' not in arg]
            self.assertEqual(commands, ['workflow-check', 'harvest-check', 'qa-current-all',
                                        'upstream-index-check', 'chapter-template-check',
                                        'progress-check', 'plan-check'])
            with (root / 'docs/progress.md').open('a') as stream:
                stream.write('Bad whitespace. \n')
            result = subprocess.run(['bash'], cwd=root, input=script, text=True, env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('trailing whitespace', result.stdout)

    def test_driver_widens_shared_chapters_without_unconditional_tool_tests(self):
        path=Path(__file__).parents[1]/'scripts/ci-current.py'
        spec=importlib.util.spec_from_file_location('ci_current_test',path)
        driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=self.prepare(root)
            for name in ('misleading-etale','ordinary'):
                p=root/'translation-data/units'/(name+'.jsonl')
                value=json.loads(p.read_text());value['changed']=True;p.write_text(json.dumps(value)+'\n')
            argv=['ci-current','--root',str(root),'--harvest',str(root/'English'),'--base-ref',base]
            commands=[]
            real_run=subprocess.run
            def called(command,**kwargs):
                if command[0]=='git':return real_run(command,**kwargs)
                commands.append(command)
                return subprocess.CompletedProcess(command,0)
            with patch.object(sys,'argv',argv),patch.object(driver.subprocess,'run',side_effect=called),patch.object(driver,'check_current_repository',return_value={'test_kind':'scheduling-only'}) as check:
                driver.run()
            self.assertIsNone(check.call_args.kwargs['chapters'])
            self.assertFalse(any('tool-test' in cmd for cmd in commands))
            dispatch=json.loads((root/'build/ci-current/dispatch.json').read_text())
            self.assertEqual(dispatch['chapters'],['alpha','beta'])
            (root/'translation-data/units/ordinary.jsonl').write_text(json.dumps(dict(unit_id='b',chapter='beta'))+'\n')
            with patch.object(sys,'argv',argv),patch.object(driver.subprocess,'run',side_effect=called),patch.object(driver,'check_current_repository',return_value={'test_kind':'scheduling-only'}) as check:
                driver.run()
            self.assertEqual(check.call_args.kwargs['chapters'],{'alpha'})


    def test_driver_tests_head_tools_when_pr_changes_dispatcher(self):
        path=Path(__file__).parents[1]/'scripts/ci-current.py'
        spec=importlib.util.spec_from_file_location('ci_current_changed_test',path)
        driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=self.prepare(root)
            p=root/'scripts/ci-current.py';p.parent.mkdir();p.write_text('print("forged green")')
            git(root,'add',str(p.relative_to(root)))
            argv=['ci-current','--root',str(root),'--harvest',str(root/'English'),'--base-ref',base]
            commands=[]
            real_run=subprocess.run
            def called(command,**kwargs):
                if command[0]=='git':return real_run(command,**kwargs)
                commands.append(command)
                return subprocess.CompletedProcess(command,0)
            with patch.object(sys,'argv',argv),patch.object(driver.subprocess,'run',side_effect=called),patch.object(driver,'check_current_repository') as narrow:
                driver.run()
            self.assertFalse(narrow.called)
            self.assertTrue(any('tool-test' in cmd for cmd in commands))
            self.assertTrue(any('qa-current-all' in cmd for cmd in commands))
