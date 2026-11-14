"""Complete synthetic adoption after a task extension; no real model data."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from test_source_adoptions import synthetic_fixture, write
from stacks_zh.records import RecordError
from stacks_zh.source_adoptions import assemble_source_adoption, load_repository_source_adoptions


class SourceAdoptionScopeExtensionTests(unittest.TestCase):
    def auxiliary(self, scope):
        paths = ['translation-data/source-adoption-inputs/synthetic-next.json',
                 'translation-data/source-adoptions/synthetic-next.json',
                 'translation-data/runs/run-synthetic-next.json',
                 'docs/evidence/synthetic-next-raw.jsonl']
        scope['allowed_write_files'] += paths
        scope['data_scopes'][0]['allowed_write_files'] += paths
        scope['data_scopes'][0]['run_scope'].append('run-synthetic-next')
        return paths

    def disjoint(self, scope):
        child = copy.deepcopy(scope['data_scopes'][0])
        child.update(scope_id='future-scope', parent_tags=['0002'],
                     unit_ids=['tag:0002:statement'], input_unit_ids=['tag:0002:statement'],
                     output_unit_ids=['tag:0002:statement'],
                     run_scope=['run-synthetic-future'], allowed_write_files=[
                         'translation-data/units/test-future.jsonl',
                         'translation-data/candidates/synthetic/test-future.jsonl',
                         'translation-data/source-adoption-inputs/synthetic-future.json',
                         'translation-data/source-adoptions/synthetic-future.json',
                         'translation-data/runs/run-synthetic-future.json',
                         'docs/evidence/synthetic-future-raw.jsonl'])
        scope['data_scopes'].append(child)
        scope['allowed_write_files'] += child['allowed_write_files']
        return child

    def test_extension_adopts_original_raw_and_replays_unchanged_freeze(self):
        for extension in ['auxiliary', 'disjoint', 'formatting', 'template']:
            with self.subTest(extension=extension), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp))
                before = {p:p.read_bytes() for p in [fp, rp]}
                path = root / frozen['task']['scope_manifest']
                scope = json.loads(path.read_text())
                if extension == 'auxiliary': self.auxiliary(scope)
                elif extension == 'disjoint': self.disjoint(scope)
                elif extension == 'template':
                    scope['allowed_write_files'].append('translation-data/chapter-templates/test.json')
                write(path, scope)
                if extension == 'formatting': path.write_text(json.dumps(scope))
                assemble_source_adoption(root, fp, [rp], harvest)
                record = json.loads((root/'translation-data/source-adoptions/synthetic-first.json').read_text())
                self.assertEqual(record['unit_ids'], frozen['unit_ids'])
                self.assertEqual(record['run_id'], frozen['run_id'])
                self.assertTrue(all(p.read_bytes() == data for p,data in before.items()))
                # Historical replay continues to read the frozen old scope.
                loaded, errors = load_repository_source_adoptions(root, harvest)
                self.assertEqual(errors, [])
                self.assertEqual(len(loaded), len(frozen['unit_ids']))
                for info in loaded.values():
                    self.assertEqual(info['record']['adoption_id'], 'synthetic-first')
                    self.assertEqual(info['input']['task']['scope_bytes'], frozen['task']['scope_bytes'])
                    self.assertEqual(info['candidate']['run_id'], frozen['run_id'])
                self.assertFalse((root/'translation-data/units/test-future.jsonl').exists())

    def test_mutation_or_overlapping_extension_writes_no_adoption(self):
        failures = ['task_id', 'owner', 'branch', 'source_commit', 'remove-file',
                    'remove-scope', 'unit_ids', 'input_unit_ids', 'output_unit_ids',
                    'parent_tags', 'historical_parent_tags', 'model_scope', 'remove-run',
                    'scope_id', 'chapter', 'old-data-path', 'unowned-policy-path',
                    'new-chapter', 'new-model', 'duplicate-output', 'duplicate-run',
                    'empty-output', 'new-policy-path', 'new-candidate-lane']
        for failure in failures:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp))
                path = root/frozen['task']['scope_manifest']
                scope = json.loads(path.read_text()); child=scope['data_scopes'][0]
                self.auxiliary(scope)
                if failure in ['task_id','owner','branch']: scope[failure]='changed'
                elif failure == 'source_commit': scope[failure]='0'*40
                elif failure == 'remove-file':
                    scope['allowed_write_files'].remove(rp.relative_to(root).as_posix())
                    child['allowed_write_files'].remove(rp.relative_to(root).as_posix())
                elif failure == 'remove-scope': scope['data_scopes']=[]
                elif failure in ['unit_ids','input_unit_ids','output_unit_ids']:
                    child[failure]=['tag:0002:statement']
                elif failure in ['parent_tags','historical_parent_tags']: child[failure]=['0002']
                elif failure == 'model_scope': child[failure].append('changed-model')
                elif failure == 'remove-run': child['run_scope'].remove(frozen['run_id'])
                elif failure in ['scope_id','chapter']: child[failure]='changed'
                elif failure == 'old-data-path':
                    extra='translation-data/candidates/synthetic/alternate.jsonl'
                    child['allowed_write_files'].append(extra);scope['allowed_write_files'].append(extra)
                elif failure == 'unowned-policy-path': scope['allowed_write_files'].append('config/glossary.yml')
                else:
                    added=self.disjoint(scope)
                    if failure == 'new-chapter': added['chapter']='other'
                    elif failure == 'new-model': added['model_scope'].append('other-model')
                    elif failure == 'duplicate-output':
                        for key in ['unit_ids','input_unit_ids','output_unit_ids']: added[key]=frozen['unit_ids']
                    elif failure == 'duplicate-run': added['run_scope']=[frozen['run_id']]
                    elif failure == 'empty-output': added['output_unit_ids']=[]
                    elif failure == 'new-policy-path':
                        added['allowed_write_files'].append('config/glossary.yml')
                        scope['allowed_write_files'].append('config/glossary.yml')
                    elif failure == 'new-candidate-lane':
                        extra='translation-data/candidates/another-model/test-future.jsonl'
                        added['allowed_write_files'].append(extra);scope['allowed_write_files'].append(extra)
                write(path,scope)
                with self.assertRaises(RecordError): assemble_source_adoption(root,fp,[rp],harvest)
                self.assertFalse((root/'translation-data/source-adoptions').exists())
                self.assertFalse((root/'translation-data/runs').exists())
                self.assertTrue(all(not (root/b['candidates_path']).exists() for b in frozen['batches']))

    def test_current_extra_raw_path_is_not_granted_to_the_old_model_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp))
            path=root/frozen['task']['scope_manifest'];scope=json.loads(path.read_text())
            paths=self.auxiliary(scope);write(path,scope)
            other=root/paths[-1];shutil.copyfile(rp,other)
            with self.assertRaisesRegex(RecordError,'raw|output path'):
                assemble_source_adoption(root,fp,[other],harvest)
            self.assertFalse((root/'translation-data/source-adoptions').exists())


if __name__ == '__main__': unittest.main()
