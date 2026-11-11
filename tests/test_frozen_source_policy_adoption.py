"""Synthetic frozen/raw fixtures only; no real model generation or approval."""
import json
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_source_adoptions import synthetic_fixture, write, git
from stacks_zh.source_adoptions import assemble_source_adoption, load_repository_source_adoptions
from stacks_zh.records import RecordError, write_jsonl
from stacks_zh.source_reextractions import byte_hash
from stacks_zh.source_containers import Containers, lower_container, canonical_proof_file_mapping
from test_source_containers import fixture as english_fixture, selector
from test_math_text import BASE_POLICY


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
    def test_consecutive_complete_proofs_borrow_their_own_locked_statement(self):
        other = ('\\begin{lemma}\\label{lemma-two}Take $z$.\\end{lemma}\n'
                 '\\begin{proof}Use $z$.\\end{proof}')
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = english_fixture(Path(temp), other=other)
            native = Containers(root, harvest)
            first = lower_container(native.select(selector()), native.policy)[0]
            second = lower_container(native.select(selector(owner='0002')), native.policy)[0]
            before = copy.deepcopy([first, second])
            self.assertEqual(canonical_proof_file_mapping([first, second], native.english.tags, native),
                             {u['unit_id']: u['unit_id'] for u in before})
            self.assertEqual([first, second], before)
            # Also cover a wrong inherited owner that does not yet collide.
            statement = lower_container(native.select(selector('lemma')), native.policy)
            self.assertEqual(canonical_proof_file_mapping([*statement, second], native.english.tags, native),
                             {u['unit_id']: u['unit_id'] for u in [*statement, second]})
            for field, value in [('source_text', second['source_text'] + ' Added.'),
                                 ('unit_id', 'tag:0002:proof-002'),
                                 ('parent_tag', '0001')]:
                changed = copy.deepcopy(second); changed[field] = value
                with self.assertRaises(RecordError):
                    canonical_proof_file_mapping([first, changed], native.english.tags, native)
            with self.assertRaises(RecordError):
                canonical_proof_file_mapping([first, second, copy.deepcopy(second)], native.english.tags, native)

    def owner_fixture(self, base, *, previous=False, unknown=False):
        statement = ('\\begin{lemma}\n\\label{lemma-one}\n'
                     'Take $x\\quad\\text{and}\\quad y$.'
                     + ('\\unsupported{value}' if unknown else '') + '\n\\end{lemma}')
        proof = ('\\begin{proof}Use $u\\quad\\text{or}\\quad v$.\\end{proof}'
                 if previous else '\\begin{proof}Use $u$.\\end{proof}')
        root, harvest, _ = english_fixture(base, statement=statement, proof=proof)
        (root / 'config/macro-policy.yml').write_text(BASE_POLICY)
        git(root, 'init', '-q'); git(root, 'add', '.')
        git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
            'commit', '-qm', 'Synthetic original owner policy')
        old = Containers(root, harvest)
        unit = lower_container(old.select(selector(ordinal=2 if previous else 1)), old.policy)[0]
        policy = BASE_POLICY + '''
translatable_math_text:
  owner-and:
    literal: "and"
    command: "text"
    usage: "quad-connector"
    source_label: "test-lemma-one"
    witness_kind: "lemma"
    witness_ordinal: 1
'''
        if previous:
            policy += '''
  previous-and:
    literal: "or"
    command: "text"
    usage: "quad-connector"
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
'''
        accepted_update(root, content=policy.encode())
        # Old containers retain original policy while watching current file bytes.
        old = Containers(root, harvest, policy_bytes=BASE_POLICY.encode())
        return root, harvest, old, Containers(root, harvest), unit

    def test_accepted_owner_and_previous_proof_are_read_only_context(self):
        for previous in (False, True):
            with self.subTest(previous=previous), tempfile.TemporaryDirectory() as temp:
                root, harvest, old, current, unit = self.owner_fixture(Path(temp), previous=previous)
                before = copy.deepcopy(unit)
                with self.assertRaisesRegex(RecordError, 'classification'):
                    canonical_proof_file_mapping([unit], old.english.tags, old)
                self.assertEqual(canonical_proof_file_mapping([unit], old.english.tags, old,
                    ownership_native=current), {unit['unit_id']: unit['unit_id']})
                self.assertEqual(unit, before)
                with self.assertRaisesRegex(RecordError, 'classification'):
                    old.select(selector('lemma'))
                self.assertFalse((root / 'translation-data').exists())

    def test_unaccepted_or_missing_owner_classification_remains_blocked(self):
        for failure in ('branch-only', 'dirty', 'missing'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root, harvest, old, current, unit = self.owner_fixture(Path(temp))
                if failure == 'branch-only':
                    git(root, 'update-ref', 'refs/remotes/origin/main', git(root, 'rev-parse', 'HEAD^'))
                    git(root, 'branch', '-m', 'synthetic-unaccepted')
                elif failure == 'dirty':
                    p = root / 'config/macro-policy.yml'; p.write_bytes(p.read_bytes() + b'\n# dirty\n')
                    current = Containers(root, harvest)
                else:
                    accepted_update(root, content=BASE_POLICY.encode())
                    current = Containers(root, harvest)
                with self.assertRaises(RecordError):
                    canonical_proof_file_mapping([unit], old.english.tags, old, ownership_native=current)

    def test_unknown_owner_syntax_and_tampered_proof_remain_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, old, current, unit = self.owner_fixture(Path(temp), unknown=True)
            with self.assertRaises(RecordError):
                canonical_proof_file_mapping([unit], old.english.tags, old, ownership_native=current)
        with tempfile.TemporaryDirectory() as temp:
            _, _, old, current, unit = self.owner_fixture(Path(temp))
            for field, value in [('source_text', unit['source_text'] + ' Extra.'),
                                 ('parent_tag', '0002'), ('unit_id', 'tag:0001:proof-002')]:
                changed = copy.deepcopy(unit); changed[field] = value
                with self.assertRaises(RecordError):
                    canonical_proof_file_mapping([changed], old.english.tags, old, ownership_native=current)

    def test_current_owner_fragment_or_location_forgery_is_rejected(self):
        for field in ('fragment', 'location'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                _, _, old, current, unit = self.owner_fixture(Path(temp))
                original = current.select
                def forged(coord):
                    selected = original(coord)
                    if field == 'fragment': selected[field] += 'extra'
                    else: selected[field]['byte_end'] -= 1
                    return selected
                with patch.object(current, 'select', side_effect=forged), self.assertRaisesRegex(
                        RecordError, 'changed complete English context'):
                    canonical_proof_file_mapping([unit], old.english.tags, old, ownership_native=current)

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
