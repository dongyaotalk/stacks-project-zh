"""Synthetic v2 partial preparation inventory, never actual model or replay evidence."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_chapter_validation import fixture as accepted_fixture, preparation_copy
from test_source_adoptions import write
from stacks_zh.chapter_relations import check_preparation_evidence
from stacks_zh.current_qa import InputSnapshot
from stacks_zh.records import RecordError, write_jsonl
from stacks_zh.source_adoptions import assemble_source_adoption
from stacks_zh.source_containers import Containers
from stacks_zh.source_reextractions import byte_hash
from stacks_zh.validation_io import InputReads


def fixture(base):
    root, harvest, accepted, fp, rp, original = accepted_fixture(base)
    record_path = root / 'translation-data/source-adoptions/synthetic-first.json'
    record = json.loads(record_path.read_bytes())
    proposal = copy.deepcopy(original)
    aid = 'synthetic-unused-revision'
    proposal.update(adoption_id=aid, run_id='run-' + aid,
                    tool_version='source-adoption-input-v2', created_at='2026-10-20T00:00:00Z')
    archives, previous = [], []
    for output in record['outputs']:
        saved = {}
        for role in ('units', 'candidates'):
            path = root / (f'translation-data/retired/source-adoptions/{aid}-synthetic-first-'
                           f'{Path(output[role]["path"]).stem}/{role}.jsonl')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((root / output[role]['path']).read_bytes())
            saved[role] = dict(path=path.relative_to(root).as_posix(), hash=byte_hash(path.read_bytes()))
        archives.append(saved)
        previous.append(dict(path=output['candidates']['path'], archive_path=saved['candidates']['path'],
                             hash=saved['candidates']['hash'],
                             records=[json.loads(line) for line in
                                      (root / saved['candidates']['path']).read_bytes().splitlines()]))
    proposal['prior_adoptions'] = [dict(record=dict(path=record_path.relative_to(root).as_posix(),
                                                   hash=byte_hash(record_path.read_bytes())), outputs=archives)]
    fp = root / f'translation-data/source-adoption-inputs/{aid}.json'
    new_raw = root / f'docs/evidence/{aid}-raw.jsonl'
    rows = [json.loads(line) for line in rp.read_bytes().splitlines()]
    write_jsonl(new_raw, rows[:1])
    scope = json.loads(proposal['task']['scope_bytes'])
    extra = [fp.relative_to(root).as_posix(), new_raw.relative_to(root).as_posix(),
             f'translation-data/source-adoptions/{aid}.json', f'translation-data/runs/run-{aid}.json',
             *(entry[role]['path'] for entry in archives for role in ('units', 'candidates'))]
    scope['allowed_write_files'] += extra
    scope['data_scopes'][0]['allowed_write_files'] += extra
    scope['data_scopes'][0]['run_scope'].append('run-' + aid)
    sp = root / proposal['task']['scope_manifest']; write(sp, scope)
    proposal['task'].update(scope_bytes=sp.read_text(), scope_manifest_sha256=byte_hash(sp.read_bytes()))
    mp, rt = preparation_copy(root, proposal, fp, new_raw)
    model = json.loads(mp.read_bytes()); model['previous_complete_candidates'] = previous; write(mp, model)
    return root, harvest, fp, new_raw, proposal, mp, rt, record_path, rows


def check(root, harvest, mp):
    reads = InputReads()
    with reads.activate():
        result = check_preparation_evidence(root, harvest, InputSnapshot(root),
            [mp.relative_to(root).as_posix()], 'test', 'synthetic', reads, Containers(root, harvest))
        reads.assert_unchanged()
        return result


class PartialPriorPreparationTests(unittest.TestCase):
    def test_complete_union_keeps_existing_inventory_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root, harvest, fp, raw, frozen, mp, rt, prior, rows = fixture(Path(directory))
            write_jsonl(raw, rows)
            result = check(root, harvest, mp)[0]
            self.assertNotIn('raw_inventory', result)
            self.assertEqual(result['generation_validation'], 'not_claimed')
            self.assertFalse(result['run_created'])

    def test_complete_paired_predecessor_partial_v2_is_inventory_without_any_replay_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            root, harvest, fp, raw, frozen, mp, rt, prior, rows = fixture(Path(directory))
            immutable = {p: p.read_bytes() for folder in ('translation-data', 'docs/evidence')
                         for p in (root / folder).rglob('*') if p.is_file()}
            result = check(root, harvest, mp)[0]; inventory = result['raw_inventory']
            self.assertEqual(result['generation_validation'], 'not_claimed')
            self.assertEqual(result['source_errors'], [])
            self.assertEqual(inventory['predecessor_validation'], 'complete-paired-snapshot-inventory')
            self.assertEqual(inventory['present_unit_ids'], frozen['unit_ids'][:1])
            self.assertEqual(inventory['missing_unit_ids'], frozen['unit_ids'][1:])
            self.assertFalse(inventory['run_created']); self.assertFalse(inventory['adoption_created'])
            self.assertEqual(immutable, {p: p.read_bytes() for p in immutable})
            with self.assertRaisesRegex(RecordError, 'complete model record'):
                assemble_source_adoption(root, fp, [raw], harvest)
            self.assertFalse((root / f'translation-data/runs/{frozen["run_id"]}.json').exists())
            self.assertFalse((root / f'translation-data/source-adoptions/{frozen["adoption_id"]}.json').exists())

    def test_missing_or_contradictory_predecessor_and_raw_never_become_partial_inventory(self):
        for mutation in ('missing-prior', 'record-hash', 'partial-outputs', 'output-order', 'snapshot-hash',
                         'snapshot-path', 'pair-order', 'previous', 'source', 'time', 'version',
                         'run', 'adoption', 'own-candidate', 'raw-duplicate', 'raw-outside', 'raw-schema'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root, harvest, fp, raw, frozen, mp, rt, prior, rows = fixture(Path(directory))
                model = json.loads(mp.read_bytes())
                if mutation == 'missing-prior': frozen['prior_adoptions'] = []
                elif mutation == 'record-hash': frozen['prior_adoptions'][0]['record']['hash'] = 'sha256:' + '0' * 64
                elif mutation == 'partial-outputs': frozen['prior_adoptions'][0]['outputs'].pop()
                elif mutation == 'output-order': frozen['prior_adoptions'][0]['outputs'].reverse()
                elif mutation == 'snapshot-hash':
                    entry = frozen['prior_adoptions'][0]['outputs'][0]['units']; (root / entry['path']).write_bytes(b'{}\n')
                elif mutation == 'snapshot-path':
                    frozen['prior_adoptions'][0]['outputs'][0]['units']['path'] = 'translation-data/retired/source-adoptions/outside/units.jsonl'
                elif mutation == 'pair-order':
                    frozen['unit_ids'].reverse()
                elif mutation == 'previous': model['previous_complete_candidates'].pop()
                elif mutation == 'source': frozen['source_commit'] = '0' * 40
                elif mutation == 'time': frozen['created_at'] = '2000-01-01T00:00:00Z'
                elif mutation == 'version': frozen['tool_version'] = 'source-adoption-input-v5'
                elif mutation == 'run': write(root / f'translation-data/runs/{frozen["run_id"]}.json', {})
                elif mutation == 'adoption': write(root / f'translation-data/source-adoptions/{frozen["adoption_id"]}.json', {})
                elif mutation == 'own-candidate':
                    path = root / frozen['batches'][0]['candidates_path']; candidates = [json.loads(l) for l in path.read_bytes().splitlines()]
                    candidates[0]['run_id'] = frozen['run_id']; write_jsonl(path, candidates)
                elif mutation == 'raw-duplicate': write_jsonl(raw, [rows[0], rows[0]])
                elif mutation == 'raw-outside':
                    row = copy.deepcopy(rows[0]); row['unit_id'] = 'tag:9999:statement'; write_jsonl(raw, [row])
                else:
                    row = copy.deepcopy(rows[0]); row.pop('notes'); write_jsonl(raw, [row])
                previous = model['previous_complete_candidates']
                mp, rt = preparation_copy(root, frozen, fp, raw)
                model = json.loads(mp.read_bytes()); model['previous_complete_candidates'] = previous; write(mp, model)
                with self.assertRaises((RecordError, OSError)):
                    check(root, harvest, mp)


if __name__ == '__main__':
    unittest.main()
