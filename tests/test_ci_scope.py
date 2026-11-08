"""Real Git diffs and structured ownership; no filename or caller PASS shortcut."""
import json
import importlib.util
import sys
from unittest.mock import patch
import subprocess
import tempfile
import unittest
from pathlib import Path
from stacks_zh.ci_scope import classify
from stacks_zh.records import RecordError


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

    def test_workflow_uses_actual_event_identity_and_base_driver(self):
        workflow=(Path(__file__).parents[1]/'.github/workflows/ci.yml').read_text()
        self.assertIn('ref: ${{ github.event.pull_request.head.sha || github.sha }}',workflow)
        self.assertIn('compare=$(git merge-base "$EVENT_BASE" "$EVENT_HEAD")',workflow)
        self.assertIn('driver=../ci-trusted-tools/scripts/ci-current.py',workflow)
        self.assertIn('--force-broad',workflow)
        self.assertNotIn('make qa-all',workflow)
        self.assertNotIn('pull_request_target',workflow)

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
