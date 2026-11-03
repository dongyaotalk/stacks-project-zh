"""Synthetic public assembly/history tests; no real model output or approval."""
import copy
import tempfile
import unittest
from pathlib import Path

from test_source_adoptions import followup_fixture, write, git, POLICIES
from stacks_zh.records import RecordError, write_jsonl, sha256_value, stamp_unit_hashes
from stacks_zh.source_adoptions import (assemble_source_adoption,
    load_repository_source_adoptions, _policy_rebound_units)
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import byte_hash, source_tex
from stacks_zh.provenance import validate_repository_provenance


def fixture(base, version='source-adoption-input-v5'):
    root, harvest, fp, rp, frozen, prior = followup_fixture(base)
    old = copy.deepcopy([u for b in frozen['batches'] for u in b['units']])
    old_policy = byte_hash((root / 'config/macro-policy.yml').read_bytes())
    with (root / 'config/macro-policy.yml').open('a') as stream:
        stream.write('\n# Synthetic policy revision; all classification rules unchanged.\n')
    git(root, 'add', 'config/macro-policy.yml')
    git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'Synthetic accepted new policy; no facts')
    frozen.update(origin_commit=git(root, 'rev-parse', 'HEAD'), tool_version=version)
    frozen['policies'] = [dict(path=p, hash=byte_hash((root / p).read_bytes())) for p in POLICIES]
    native = Containers(root, harvest)
    for batch in frozen['batches']:
        units, groups = [], []
        for group in batch['containers']:
            selected = native.select(group['selector'])
            lowered = lower_container(selected, native.policy)
            units.extend(lowered)
            groups.append(dict(selector=selected['selector'], selected=selected,
                               unit_ids=[u['unit_id'] for u in lowered]))
        batch.update(units=units, containers=groups)
        write_jsonl(root / batch['units_path'], units)
    contexts = []
    for row in native.document('test')[1]:
        value = dict(kind='locked-English-neighbor', location=row['location'],
                     source_commit=frozen['source_commit'], source_unit=row['unit'],
                     owner_tag=row['owner_tag'], parent_tag=row['parent_tag'])
        contexts.append(dict(context_id=row['unit']['unit_id'], value=value, hash=sha256_value(value)))
    frozen['contexts'] = contexts
    write(fp, frozen)
    new = [u for b in frozen['batches'] for u in b['units']]
    assert [source_tex(u) for u in old] == [source_tex(u) for u in new]
    return root, harvest, fp, rp, frozen, old, new, old_policy, byte_hash(native.policy_bytes)


class PreGitPolicyWitnessTests(unittest.TestCase):
    def test_complete_public_assembly_replay_and_first_joint_git_adoption(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, old, new, old_hash, new_hash = fixture(Path(temp))
            self.assertNotEqual(old_hash, new_hash)
            self.assertEqual(old[0]['source_text'], new[0]['source_text'])
            self.assertEqual(old[0]['placeholders'], new[0]['placeholders'])
            self.assertNotEqual(old[0]['source_structure_hash'], new[0]['source_structure_hash'])
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()
                      and any(part in {'source-adoptions', 'source-adoption-inputs', 'runs', 'evidence', 'retired'}
                              for part in p.relative_to(root).parts)}
            result = assemble_source_adoption(root, fp, [rp], harvest)
            self.assertEqual(result['tool_version'], 'source-adoption-v5')
            self.assertTrue(all(p.read_bytes() == raw for p, raw in before.items()))
            rows, errors = load_repository_source_adoptions(root, harvest)
            self.assertEqual(errors, [])
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(len(value['prior_candidates']) == 1 for value in rows.values()))
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            git(root, 'add', '.')
            git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'Synthetic first joint adoption')
            self.assertEqual(validate_repository_provenance(root, harvest), [])

    def test_v2_retains_its_exact_unit_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, *_ = fixture(Path(temp), 'source-adoption-input-v2')
            with self.assertRaisesRegex(RecordError, 'changes source or complete segmentation'):
                assemble_source_adoption(root, fp, [rp], harvest)

    def test_v5_requires_a_real_policy_witness_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, _ = followup_fixture(Path(temp))
            frozen['tool_version'] = 'source-adoption-input-v5'
            write(fp, frozen)
            with self.assertRaisesRegex(RecordError, 'requires an actual'):
                assemble_source_adoption(root, fp, [rp], harvest)

    def test_changed_nodes_slots_coordinates_and_other_fields_are_rejected_even_with_new_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, _, _, _, old, new, old_hash, new_hash = fixture(Path(temp))
            for mutation in ['formula', 'slot', 'anchor', 'region', 'parent', 'body', 'placeholder', 'risk']:
                with self.subTest(mutation=mutation):
                    changed = copy.deepcopy(new)
                    unit = changed[0]
                    region = unit['math_text_regions'][0]
                    slot = region['slots'][0]
                    if mutation == 'formula': region['source'] = region['source'].replace('x', 'z')
                    elif mutation == 'slot': slot['source'] = 'or'
                    elif mutation == 'anchor': slot['classification_witness']['anchor']['ordinal'] += 1
                    elif mutation == 'region': region['source_byte_span']['start'] += 1
                    elif mutation == 'parent': unit['parent_tag'] = 'AAAA'
                    elif mutation == 'body': unit['source_text'] += 'Extra source.\n'
                    elif mutation == 'placeholder': unit['placeholders']['MATHSEG_0001'] += 'z'
                    else: unit['risk_level'] = 'R1' if unit['risk_level'] != 'R1' else 'R3'
                    changed[0] = stamp_unit_hashes(unit)
                    with self.assertRaisesRegex(RecordError, 'permits only'):
                        _policy_rebound_units(old, changed, old_hash, new_hash)

    def test_wrong_old_or_new_policy_digest_cannot_rebind_a_witness(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, _, _, _, old, new, old_hash, new_hash = fixture(Path(temp))
            with self.assertRaisesRegex(RecordError, 'replayed complete policy'):
                _policy_rebound_units(old, new, 'sha256:' + '0' * 64, new_hash)
            with self.assertRaisesRegex(RecordError, 'permits only'):
                _policy_rebound_units(old, new, old_hash, 'sha256:' + '0' * 64)

    def test_complete_snapshot_and_all_model_fields_remain_required(self):
        for mutation in ['partial', 'raw-field', 'archive']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, *_ = fixture(Path(temp))
                if mutation == 'partial':
                    frozen['prior_adoptions'][0]['outputs'].pop()
                    write(fp, frozen)
                elif mutation == 'raw-field':
                    import json
                    rows = [json.loads(line) for line in rp.read_text().splitlines()]
                    del rows[0]['notes']
                    write_jsonl(rp, rows)
                else:
                    entry = frozen['prior_adoptions'][0]['outputs'][0]['candidates']
                    (root / entry['path']).write_bytes(b'{}\n')
                with self.assertRaises(RecordError):
                    assemble_source_adoption(root, fp, [rp], harvest)

    def test_new_origin_must_actually_register_the_independent_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, *_ = fixture(Path(temp))
            import json
            for name, version in [('source-adoption-input.schema.json', 'source-adoption-input-v5'),
                                  ('source-adoption.schema.json', 'source-adoption-v5')]:
                path = root / 'schema' / name
                schema = json.loads(path.read_bytes())
                schema['properties']['tool_version']['enum'].remove(version)
                if 'oneOf' in schema:
                    schema['oneOf'] = [item for item in schema['oneOf']
                                       if item['properties']['tool_version']['const'] != version]
                write(path, schema)
            git(root, 'add', 'schema/source-adoption-input.schema.json', 'schema/source-adoption.schema.json')
            git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'Synthetic origin without v5 permission')
            frozen['origin_commit'] = git(root, 'rev-parse', 'HEAD')
            frozen['policies'] = [dict(path=p, hash=byte_hash((root / p).read_bytes())) for p in POLICIES]
            write(fp, frozen)
            with self.assertRaisesRegex(RecordError, 'accepted origin does not permit'):
                assemble_source_adoption(root, fp, [rp], harvest)


if __name__ == '__main__':
    unittest.main()
