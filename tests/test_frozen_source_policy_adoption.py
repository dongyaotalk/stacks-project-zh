"""Synthetic frozen/raw fixtures only; no real model generation or approval."""
import json
import tempfile
import unittest
from pathlib import Path

from test_source_adoptions import synthetic_fixture, write, git
from stacks_zh.source_adoptions import assemble_source_adoption, load_repository_source_adoptions
from stacks_zh.records import RecordError, write_jsonl
from stacks_zh.source_reextractions import byte_hash


def frozen_fixture(base):
    root, harvest, fp, rp, frozen, raw = synthetic_fixture(base)
    git(root, 'update-ref', 'refs/remotes/origin/main', frozen['origin_commit'])
    git(root, 'switch', '-qc', 'synthetic-data')
    scope_path = root / frozen['task']['scope_manifest']
    scope = json.loads(scope_path.read_bytes())
    scope['branch'] = frozen['task']['branch'] = 'synthetic-data'
    write(scope_path, scope)
    frozen['task'].update(scope_bytes=scope_path.read_text(), scope_manifest_sha256=byte_hash(scope_path.read_bytes()))
    write(fp, frozen)
    return root, harvest, fp, rp, frozen, raw


def accepted_update(root, path='config/macro-policy.yml', content=None):
    target = root / path
    target.write_bytes(content if content is not None else target.read_bytes() + (b'\n' if path.endswith('.json') else b'\n# accepted synthetic update\n'))
    git(root, 'add', path)
    git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'Synthetic accepted source policy update')
    git(root, 'update-ref', 'refs/remotes/origin/main', git(root, 'rev-parse', 'HEAD'))


class FrozenSourcePolicyAdoptionTests(unittest.TestCase):
    def test_complete_public_assembly_keeps_original_freeze_units_and_raw(self):
        for path in ['config/macro-policy.yml', 'config/source-terms.json']:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, raw = frozen_fixture(Path(temp))
                before = {p: p.read_bytes() for p in [fp, rp, *[root / b['units_path'] for b in frozen['batches']]]}
                accepted_update(root, path)
                result = assemble_source_adoption(root, fp, [rp], harvest)
                self.assertEqual(result['tool_version'], 'source-adoption-v1')
                self.assertTrue(all(p.read_bytes() == payload for p, payload in before.items()))
                rows, errors = load_repository_source_adoptions(root, harvest)
                self.assertEqual(errors, [])
                self.assertEqual(len(rows), 2)
                for b in frozen['batches']:
                    candidate = json.loads((root / b['candidates_path']).read_text())
                    original = next(r for r in raw if r['unit_id'] == candidate['unit_id'])
                    for key in ('translation', 'allowed_english', 'term_occurrences', 'unknown_terms', 'notes'):
                        self.assertEqual(candidate[key], original[key])
                with self.assertRaises(RecordError):
                    assemble_source_adoption(root, fp, [rp], harvest)

    def test_accepted_source_schema_extension_requires_both_original_and_current_contracts(self):
        for tightening in [False, True]:
            with self.subTest(tightening=tightening), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = frozen_fixture(Path(temp))
                path = root / 'schema/unit.schema.json'
                schema = json.loads(path.read_bytes())
                if tightening:
                    schema['oneOf'][0]['properties']['source_text']['const'] = 'not the actual source'
                else:
                    schema['description'] = 'Synthetic accepted source schema extension; existing objects unchanged.'
                accepted_update(root, 'schema/unit.schema.json', (json.dumps(schema)+'\n').encode())
                if tightening:
                    with self.assertRaisesRegex(RecordError, 'original or accepted current Schema'):
                        assemble_source_adoption(root, fp, [rp], harvest)
                else:
                    assemble_source_adoption(root, fp, [rp], harvest)

    def test_unaccepted_dirty_or_branch_only_policy_is_rejected(self):
        for mode in ['dirty', 'branch', 'after-main']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = frozen_fixture(Path(temp))
                if mode == 'after-main':
                    accepted_update(root)
                path = root / 'config/macro-policy.yml'
                path.write_bytes(path.read_bytes() + b'\n# unaccepted\n')
                if mode == 'branch':
                    git(root, 'add', 'config/macro-policy.yml')
                    git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'Synthetic branch only policy')
                with self.assertRaisesRegex(RecordError, 'exact accepted main policy'):
                    assemble_source_adoption(root, fp, [rp], harvest)
                self.assertFalse((root / 'translation-data/source-adoptions').exists())

    def test_other_accepted_policy_drift_remains_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, _ = frozen_fixture(Path(temp))
            accepted_update(root, 'config/style-guide.md')
            with self.assertRaisesRegex(RecordError, 'generation policy drifted'):
                assemble_source_adoption(root, fp, [rp], harvest)

    def test_changed_classification_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, _ = frozen_fixture(Path(temp))
            content = (root / 'config/macro-policy.yml').read_bytes().replace(b'usage: "quad-connector"', b'usage: "other"')
            accepted_update(root, content=content)
            with self.assertRaises(RecordError):
                assemble_source_adoption(root, fp, [rp], harvest)
            self.assertFalse((root / 'translation-data/source-adoptions').exists())

    def test_current_terminology_and_full_raw_fields_remain_required(self):
        for failure in ['terms', 'raw']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, raw = frozen_fixture(Path(temp))
                if failure == 'terms':
                    p = root / 'config/source-terms.json'
                    catalog = json.loads(p.read_bytes())
                    catalog['terms'].append(dict(id='claim', forms=['claim'], chapters=['test'], evidence=[]))
                    accepted_update(root, 'config/source-terms.json', (json.dumps(catalog)+'\n').encode())
                else:
                    accepted_update(root)
                    del raw[0]['notes']
                    write_jsonl(rp, raw)
                with self.assertRaises(RecordError):
                    assemble_source_adoption(root, fp, [rp], harvest)
                self.assertFalse((root / 'translation-data/source-adoptions').exists())

    def test_frozen_source_and_policy_forgery_remain_rejected(self):
        for mutation in ['body', 'math', 'coordinate', 'policy']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = frozen_fixture(Path(temp))
                accepted_update(root)
                if mutation == 'body': frozen['batches'][0]['units'][0]['source_text'] += 'extra'
                elif mutation == 'math': frozen['batches'][0]['units'][0]['placeholders']['MATHSEG_0001'] += 'z'
                elif mutation == 'coordinate': frozen['batches'][0]['containers'][0]['selector']['ordinal'] = 2
                else: frozen['policies'][0]['hash'] = 'sha256:' + '0' * 64
                write(fp, frozen)
                with self.assertRaises(RecordError):
                    assemble_source_adoption(root, fp, [rp], harvest)
                self.assertFalse((root / 'translation-data/source-adoptions').exists())


if __name__ == '__main__':
    unittest.main()
