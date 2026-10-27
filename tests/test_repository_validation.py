"""Synthetic orchestration and race tests, not acceptance receipts for real data."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from stacks_zh.current_qa import InputSnapshot
from stacks_zh.decisions import validate_repository_decisions
from stacks_zh.source_adoptions import load_repository_source_adoptions
from stacks_zh.records import RecordError
from stacks_zh.repository_validation import _ProvenancePass, _require_live_provenance, validate_repository


class RepositoryValidationTests(unittest.TestCase):
    def repository(self, root):
        for name in ['upstream.lock','Makefile','AGENTS.md','WORKFLOW.md','stacks_zh.py']:
            (root/name).write_text('synthetic fixture\n')
        for directory in ['translation-data','review','config','schema','stacks_zh','task-scopes']:
            (root/directory).mkdir()
        subprocess.run(['git','-C',str(root),'init','-q'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(root),'add','.'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(root),'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True,capture_output=True)

    def test_one_actual_validator_call_and_live_object_reuse(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();self.repository(root);proofs=[]
            def decisions(path, harvest, *, _provenance):
                _require_live_provenance(_provenance,path,harvest);proofs.append(_provenance);return []
            with mock.patch('stacks_zh.repository_validation.validate_repository_schemas',return_value=[]) as schema, \
                 mock.patch('stacks_zh.repository_validation._validate_repository_provenance',return_value=load_repository_source_adoptions(root)) as provenance, \
                 mock.patch('stacks_zh.decisions.validate_repository_decisions',side_effect=decisions) as decision, \
                 mock.patch('stacks_zh.repository_validation.CurrentSourceQA', autospec=True) as current:
                current.return_value.validate_repository.return_value=(2,[])
                messages=[];self.assertEqual(validate_repository(root,report=messages.append),(2,[]))
                provenance.assert_called_once_with(root,None);schema.assert_called_once_with(root);decision.assert_called_once()
                self.assertEqual(len(proofs),1);self.assertEqual(len(messages),4)

    def test_no_decision_or_source_pass_after_failed_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.repository(root)
            with mock.patch('stacks_zh.repository_validation.validate_repository_schemas',return_value=[]), \
                 mock.patch('stacks_zh.repository_validation._validate_repository_provenance',return_value=({},['bad immutable raw'])), \
                 mock.patch('stacks_zh.decisions.validate_repository_decisions') as decision, \
                 mock.patch('stacks_zh.repository_validation.CurrentSourceQA', autospec=True) as current:
                self.assertEqual(validate_repository(root),(0,['bad immutable raw']));decision.assert_not_called();current.assert_not_called()

    def test_fact_change_during_validation_is_not_certified(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.repository(root)
            adoptions,_=load_repository_source_adoptions(root)
            def changed(*args):
                (root/'translation-data/injected.json').write_text('{}\n');return adoptions,[]
            with mock.patch('stacks_zh.repository_validation.validate_repository_schemas',return_value=[]), \
                 mock.patch('stacks_zh.repository_validation._validate_repository_provenance',side_effect=changed), \
                 mock.patch('stacks_zh.decisions.validate_repository_decisions') as decision:
                with self.assertRaisesRegex(RecordError,'paths changed'):validate_repository(root)
                decision.assert_not_called()

    def test_disk_dict_fake_issuer_and_other_root_cannot_replace_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.repository(root);snapshot=InputSnapshot(root)
            for fake in [{'status':'PASS'},object(),_ProvenancePass(root.resolve(),snapshot,object())]:
                with self.subTest(fake=type(fake).__name__),self.assertRaises(RecordError):_require_live_provenance(fake,root)
            with mock.patch('stacks_zh.decisions._candidate_index',return_value={}):
                with self.assertRaisesRegex(RecordError,'actual live'):validate_repository_decisions(root,_provenance={'status':'PASS'})

    def test_generated_bytecode_does_not_invalidate_watched_python_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.repository(root);source=root/'stacks_zh/example.py';source.write_text('value=1\n');snapshot=InputSnapshot(root);snapshot.watch_tree(root/'stacks_zh','*.py')
            cache=root/'stacks_zh/__pycache__';cache.mkdir();(cache/'example.pyc').write_bytes(b'synthetic cache');snapshot.assert_unchanged()
            source.write_text('value=2\n')
            with self.assertRaisesRegex(RecordError,'changed'):snapshot.assert_unchanged()

    def test_empty_watched_directory_replaced_with_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.repository(root)
            target=root/'review';snapshot=InputSnapshot(root);snapshot.watch_tree(target)
            target.rmdir();outside=root/'empty';outside.mkdir()
            target.symlink_to(outside,target_is_directory=True)
            with self.assertRaisesRegex(RecordError,'symlink'):snapshot.assert_unchanged()

    def test_subdirectory_cannot_inherit_parent_head_as_its_repository_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.repository(root);child=root/'child';child.mkdir()
            with self.assertRaisesRegex(RecordError,'actual Git worktree root'):InputSnapshot(child)

    def test_standalone_decision_command_still_replays_unselected_corrections(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);candidate=dict(unit_id='tag:ABCD:statement',run_id='synthetic',translation_hash='synthetic',model_correction_id='synthetic')
            with mock.patch('stacks_zh.decisions._candidate_index',return_value={('tag:ABCD:statement','synthetic','synthetic'):candidate}), \
                 mock.patch('stacks_zh.decisions._unit_facts',return_value={}), \
                 mock.patch('stacks_zh.decisions.validate_repository_provenance',return_value=[]) as provenance, \
                 mock.patch('stacks_zh.decisions.candidate_provenance_hash',side_effect=AssertionError('no decision references it')):
                self.assertEqual(validate_repository_decisions(root),[]);provenance.assert_called_once_with(root,None)


if __name__=='__main__':unittest.main()
