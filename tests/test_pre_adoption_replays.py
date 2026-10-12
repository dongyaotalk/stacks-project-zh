"""Synthetic two-run fixtures; never production model output."""
from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from test_group_derivations import fixture, read, write, save, run_for, commit
from test_source_containers import git
from stacks_zh.derivations import byte_hash, clean, jsonl_bytes, load_repository_derivations, replay_derivation
from stacks_zh.group_derivations import revision_group
from stacks_zh.model_corrections import candidate_provenance_hash, load_repository_corrections
from stacks_zh.pre_adoption_replays import pre_adoption_history
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import load_jsonl, sha256_value
from stacks_zh.schema_validation import validate_repository_schemas
from stacks_zh.source_containers import Containers, load_source_containers
from stacks_zh.workflow import render_batch


def two_runs(base):
    root, harvest, records = fixture(base, count=1)
    prior = records[0]
    did = prior['derivation_id']
    prior_id = prior['unit_groups'][0]['model_correction_id']
    prior_corrections, errors = load_repository_corrections(root)
    assert not errors, errors
    old_units = [clean(u) for u in load_jsonl(root / prior['files']['output_units']['path'])]
    old_candidates = [clean(c) for c in load_jsonl(root / prior['files']['output_candidates']['path'])]
    bindings = {f'translation-data/derivations/{did}.json': byte_hash((root / f'translation-data/derivations/{did}.json').read_bytes()),
                **{prior['files'][role]['path']: prior['files'][role]['hash'] for role in ['output_units', 'output_candidates']}}
    manifest = dict(schema_version=1, tool_version='pre-adoption-replay-v1', replay_id='fixture-pre-adoption',
        current_derivation_id=did, predecessor_correction_id=prior_id, successor_correction_id='fixture-followup',
        source_commit=prior['source_commit'], origin_commit=prior['origin_commit'], created_at='2026-10-06T03:00:00Z',
        output_unit_ids=[u['unit_id'] for u in old_units], files={})
    for role, rows in [('units', old_units), ('candidates', old_candidates)]:
        manifest['files'][role] = save(root, f"translation-data/retired/pre-adoption-replays/{manifest['replay_id']}/{role}.jsonl", rows)
    snapshot = f"translation-data/retired/pre-adoption-replays/{manifest['replay_id']}/derivation.json"
    (root / snapshot).write_bytes((root / f'translation-data/derivations/{did}.json').read_bytes())
    manifest['files']['derivation'] = {'path': snapshot, 'hash': byte_hash((root / snapshot).read_bytes())}
    raw = []
    for unit, candidate in zip(old_units, old_candidates, strict=True):
        previous = prior_corrections[(prior_id, unit['unit_id'])]
        p_record = previous['record']
        paths = [f'translation-data/model-corrections/{prior_id}.json', f"translation-data/runs/{p_record['run_id']}.json",
                 *(p_record['files'][r]['path'] for r in ['units','candidates'])]
        row = copy.deepcopy(previous['candidate'])
        context = row['context']
        context['prior_actual_revision'] = {'run_id': p_record['run_id'], 'correction_id': prior_id,
            'run_manifest': previous['manifest'], 'correction_record': p_record, 'raw_candidate': previous['candidate'],
            'current_derived_candidate': candidate,
            'complete_original_actual_run_files': {p:byte_hash((root / p).read_bytes()) for p in paths}}
        context['pre_adoption_snapshot_bindings'] = bindings
        row.update(run_id='fixture-followup-run', created_at='2026-10-06T02:00:00Z',
                   model_id='fixture-followup-model', model_record_id='fixture:followup:declared',
                   context_hash=sha256_value(context), notes=['Synthetic followup fixture, not actual model output.'])
        raw.append(row)
    correction = dict(schema_version=1, correction_id='fixture-followup', source_commit=prior['source_commit'],
        created_at=raw[0]['created_at'], run_id=raw[0]['run_id'], unit_ids=[u['unit_id'] for u in old_units],
        derivation_ids={u['unit_id']:did for u in old_units}, files={})
    for role, rows in [('units',old_units), ('candidates',raw)]:
        correction['files'][role] = save(root, f'translation-data/retired/model-corrections/fixture-followup/{role}.jsonl', rows)
    write(root / 'translation-data/model-corrections/fixture-followup.json', correction)
    write(root / 'translation-data/runs/fixture-followup-run.json', run_for(raw, prior['source_commit'], 'revision', raw[0]['run_id']))
    current = copy.deepcopy(prior)
    for group in current['unit_groups']:
        group['model_correction_id'] = 'fixture-followup'
    corrections, errors = load_repository_corrections(root)
    assert not errors, errors
    restorations, errors = load_source_containers(root, harvest)
    assert not errors, errors
    inputs = [[clean(row) for row in load_jsonl(root / prior['files'][role]['path'])]
              for role in ['input_units', 'input_candidates']]
    outputs = replay_derivation(current, *inputs, corrections, source_containers=restorations, tags=Containers(root,harvest).english.tags)
    for role, rows in zip(['output_units','output_candidates'], outputs, strict=True):
        current['files'][role] = save(root, current['files'][role]['path'], rows)
    write(root / f'translation-data/derivations/{did}.json', current)
    write(root / 'translation-data/pre-adoption-replays/fixture-pre-adoption.json', manifest)
    return root, harvest, current, manifest


class PreAdoptionReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root, self.harvest, self.current, self.manifest = two_runs(Path(self.tmp.name))
        self.path = self.root / 'translation-data/pre-adoption-replays/fixture-pre-adoption.json'

    def errors(self):
        return load_repository_derivations(self.root, harvest=self.harvest)[1]

    def assertRejected(self, needle):
        errors = self.errors()
        self.assertTrue(any(needle in e for e in errors), errors)

    def save_manifest(self):
        write(self.path, self.manifest)

    def mutate_raw_context(self, change):
        cid = 'fixture-followup'
        path = self.root / f'translation-data/retired/model-corrections/{cid}/candidates.jsonl'
        rows = [clean(r) for r in load_jsonl(path)]
        change(rows[0]['context'])
        rows[0]['context_hash'] = sha256_value(rows[0]['context'])
        correction_path = self.root / f'translation-data/model-corrections/{cid}.json'
        correction = read(correction_path)
        correction['files']['candidates'] = save(self.root, str(path.relative_to(self.root)), rows)
        write(correction_path, correction)
        run_path = self.root / 'translation-data/runs/fixture-followup-run.json'
        run = read(run_path)
        run['inputs']['context_hashes'] = [r['context_hash'] for r in rows]
        write(run_path, run)
        corrections, errors = load_repository_corrections(self.root)
        self.assertEqual(errors, [])
        restorations, errors = load_source_containers(self.root,self.harvest)
        self.assertEqual(errors, [])
        inputs = [[clean(r) for r in load_jsonl(self.root / self.current['files'][role]['path'])]
                  for role in ['input_units','input_candidates']]
        outputs = replay_derivation(self.current,*inputs,corrections,source_containers=restorations,
                                    tags=Containers(self.root,self.harvest).english.tags)
        for role, values in zip(['output_units','output_candidates'],outputs,strict=True):
            self.current['files'][role] = save(self.root,self.current['files'][role]['path'],values)
        write(self.root / f"translation-data/derivations/{self.current['derivation_id']}.json",self.current)

    def test_full_batch_replay_and_first_adoption_remain_valid(self):
        self.assertEqual(self.errors(), [])
        self.assertEqual(validate_repository_schemas(self.root), [])
        self.assertEqual(validate_repository_provenance(self.root,self.harvest), [])
        self.assertEqual(len(self.manifest['output_unit_ids']), 4)
        self.assertEqual(len(pre_adoption_history(self.root,self.current['derivation_id'])), 1)
        commit(self.root)
        self.assertEqual(self.errors(), [])

    def test_no_sidecar_does_not_waive_unused_raw(self):
        self.path.unlink()
        self.assertRejected('frozen output has no active')

    def test_rejects_partial_and_reordered_outputs(self):
        for ids in [self.manifest['output_unit_ids'][:-1], list(reversed(self.manifest['output_unit_ids']))]:
            with self.subTest(ids=ids):
                self.manifest['output_unit_ids'] = ids
                self.save_manifest()
                self.assertRejected('exact complete ordered')

    def test_rejects_changed_prior_record_even_after_rehash(self):
        path = self.root / self.manifest['files']['derivation']['path']
        record = read(path)
        record['unit_groups'][0]['reason'] += ' changed'
        write(path,record)
        self.manifest['files']['derivation']['hash'] = byte_hash(path.read_bytes())
        self.save_manifest()
        self.assertRejected('changes source, inputs, segmentation')

    def test_rejects_old_five_fields_without_actual_raw(self):
        path = self.root / self.manifest['files']['candidates']['path']
        rows = [clean(r) for r in load_jsonl(path)]
        rows[0]['notes'].append('fabricated field')
        self.manifest['files']['candidates'] = save(self.root,str(path.relative_to(self.root)),rows)
        self.save_manifest()
        self.assertRejected('output bytes differ')

    def test_rejects_missing_prior_source_unit(self):
        path = self.root / self.manifest['files']['units']['path']
        rows = [clean(r) for r in load_jsonl(path)][:-1]
        self.manifest['files']['units'] = save(self.root,str(path.relative_to(self.root)),rows)
        self.save_manifest()
        self.assertRejected('output bytes differ')

    def test_rejects_fabricated_old_fields_even_after_snapshot_and_record_rehash(self):
        path = self.root / self.manifest['files']['candidates']['path']
        rows = [clean(r) for r in load_jsonl(path)]
        rows[0]['notes'].append('fabricated historical field')
        self.manifest['files']['candidates'] = save(self.root,str(path.relative_to(self.root)),rows)
        record_path = self.root / self.manifest['files']['derivation']['path']
        record = read(record_path)
        record['files']['output_candidates']['hash'] = self.manifest['files']['candidates']['hash']
        write(record_path,record)
        self.manifest['files']['derivation']['hash'] = byte_hash(record_path.read_bytes())
        self.save_manifest()
        self.assertRejected('complete historical replay differs')

    def test_rejects_raw_context_hash_rewrite(self):
        self.mutate_raw_context(lambda c: c['prior_actual_revision']['raw_candidate']['notes'].append('fabricated'))
        self.assertRejected('freeze the exact full prior revision')

    def test_rejects_incomplete_prior_run_file_bindings(self):
        self.mutate_raw_context(lambda c: c['prior_actual_revision']['complete_original_actual_run_files'].pop(next(iter(c['prior_actual_revision']['complete_original_actual_run_files']))))
        self.assertRejected('freeze the exact full prior revision')

    def test_rejects_absent_or_conflicting_frozen_batch_hashes(self):
        self.mutate_raw_context(lambda c: c['pre_adoption_snapshot_bindings'].pop(next(iter(c['pre_adoption_snapshot_bindings']))))
        self.assertRejected('freeze complete prior batch bytes')

    def test_legacy_actual_context_key_is_equally_strict(self):
        self.mutate_raw_context(lambda c: c.update(complete_prior_six_batch_snapshot_bindings=c.pop('pre_adoption_snapshot_bindings')))
        self.assertEqual(self.errors(), [])

    def test_rejects_ambiguous_context_binding_maps(self):
        self.mutate_raw_context(lambda c: c.update(complete_prior_six_batch_snapshot_bindings=c['pre_adoption_snapshot_bindings']))
        self.assertRejected('one complete prior snapshot')

    def test_rejects_fake_origin(self):
        self.manifest['origin_commit'] = 'f' * 40
        self.save_manifest()
        self.assertRejected('same initial v4 source/origin')

    def test_rejects_sidecar_added_after_current_derivation_adoption(self):
        payload = self.path.read_bytes()
        self.path.unlink()
        commit(self.root)
        self.path.write_bytes(payload)
        self.assertRejected('accompany the first derivation addition')

    def test_snapshots_must_also_accompany_the_first_adoption(self):
        path = self.root / self.manifest['files']['units']['path']
        payload = path.read_bytes()
        path.unlink()
        commit(self.root)
        path.write_bytes(payload)
        self.assertRejected('accompany the first derivation addition')

    def test_later_normal_git_archive_keeps_the_pre_adoption_history(self):
        origin = commit(self.root)
        previous = self.current
        did = previous['derivation_id']
        units = [clean(u) for u in load_jsonl(self.root / previous['files']['output_units']['path'])]
        candidates = [clean(c) for c in load_jsonl(self.root / previous['files']['output_candidates']['path'])]
        record = dict(schema_version=1,derivation_id='fixture-later-v4',source_commit=previous['source_commit'],
            origin_commit=origin,created_at='2026-10-06T04:00:00Z',tool=previous['tool'],
            previous_derivation_id=did,files={},unit_groups=[])
        archive = dict(schema_version=1,prior_derivation_id=did,successor_derivation_id=record['derivation_id'],
            source_commit=record['source_commit'],origin_commit=origin,created_at=record['created_at'],
            record={'path':f'translation-data/derivations/{did}.json','hash':byte_hash((self.root / f'translation-data/derivations/{did}.json').read_bytes())},files={})
        for role,rows in [('output_units',units),('output_candidates',candidates)]:
            archive['files'][role] = save(self.root,f"translation-data/retired/derivations/{did}/{role.replace('_','-')}.jsonl",rows)
            record['files'][role] = copy.deepcopy(previous['files'][role])
        write(self.root / f'translation-data/derivation-archives/{did}.json',archive)
        for role,rows in [('input_units',units),('input_candidates',candidates)]:
            record['files'][role] = save(self.root,f"translation-data/retired/derivations/{record['derivation_id']}/{'units' if role == 'input_units' else 'candidates'}.jsonl",rows)
        raw = []
        for index,(unit,candidate) in enumerate(zip(units,candidates,strict=True)):
            group = dict(group_id=f'unit-{index}',input_unit_ids=[unit['unit_id']],output_unit_ids=[unit['unit_id']],
                output_units=[unit],identity_anchor=unit['unit_id'],reason='Synthetic later complete batch.',
                model_correction_id='fixture-later-correction',source_container_restoration_id=None)
            record['unit_groups'].append(group)
            row = {k:copy.deepcopy(v) for k,v in candidate.items() if k not in ['derivation_id','model_correction_id','unit_group_id']}
            context = dict(unit_id=unit['unit_id'],source_unit=unit,source_commit=record['source_commit'],
                prompt_version='fixture',policy_revision='fixture',revision_input=revision_group(record,group,[unit],[candidate]))
            row.update(context=context,context_hash=sha256_value(context),run_id='fixture-later-run',
                       created_at=record['created_at'],notes=['Synthetic third revision only.'])
            raw.append(row)
        correction = dict(schema_version=1,correction_id='fixture-later-correction',source_commit=record['source_commit'],
            created_at=record['created_at'],run_id='fixture-later-run',unit_ids=[u['unit_id'] for u in units],
            derivation_ids={u['unit_id']:record['derivation_id'] for u in units},files={})
        for role,rows in [('units',units),('candidates',raw)]:
            correction['files'][role] = save(self.root,f'translation-data/retired/model-corrections/fixture-later-correction/{role}.jsonl',rows)
        write(self.root / 'translation-data/model-corrections/fixture-later-correction.json',correction)
        write(self.root / 'translation-data/runs/fixture-later-run.json',run_for(raw,record['source_commit'],'revision','fixture-later-run'))
        corrections,errors = load_repository_corrections(self.root)
        self.assertEqual(errors, [])
        outputs = replay_derivation(record,units,candidates,corrections,(units,candidates),tags=Containers(self.root,self.harvest).english.tags)
        for role,rows in zip(['output_units','output_candidates'],outputs,strict=True):
            record['files'][role] = save(self.root,record['files'][role]['path'],rows)
        write(self.root / f"translation-data/derivations/{record['derivation_id']}.json",record)
        self.assertEqual(self.errors(), [])
        self.assertEqual(validate_repository_provenance(self.root,self.harvest), [])
        self.assertTrue(pre_adoption_history(self.root,did))

    def test_rejects_invalid_current_replay(self):
        path = self.root / self.current['files']['output_candidates']['path']
        path.write_bytes(path.read_bytes() + b'\n')
        self.assertRejected('one complete validated current batch')

    def test_rejects_duplicate_history_consumer(self):
        another = copy.deepcopy(self.manifest)
        another['replay_id'] = 'another'
        write(self.root / 'translation-data/pre-adoption-replays/another.json',another)
        self.assertRejected('one complete validated current batch')

    def test_rejects_snapshot_symlink(self):
        path = self.root / self.manifest['files']['units']['path']
        target = path.with_suffix('.saved')
        path.rename(target)
        path.symlink_to(target.name)
        self.assertRejected('symlink')

    def test_rejects_orphan_snapshot(self):
        path = self.root / 'translation-data/retired/pre-adoption-replays/orphan/unused.json'
        write(path,{})
        self.assertRejected('orphaned pre-adoption snapshot')

    def test_rejects_invalid_actual_run_time(self):
        self.manifest['created_at'] = '2026-10-06T00:00:00Z'
        self.save_manifest()
        self.assertRejected('invalid time order')

    def test_first_added_history_cannot_be_rehashed(self):
        commit(self.root)
        self.manifest['created_at'] = '2026-10-06T04:00:00Z'
        self.save_manifest()
        self.assertRejected('immutable evidence differs')

    def test_history_changes_source_binding_and_preview_discloses_both_runs(self):
        candidate = clean(load_jsonl(self.root / self.current['files']['output_candidates']['path'])[0])
        original = candidate_provenance_hash(self.root,candidate)
        self.manifest['created_at'] = '2026-10-06T04:00:00Z'
        self.save_manifest()
        self.assertEqual(self.errors(), [])
        self.assertNotEqual(candidate_provenance_hash(self.root,candidate),original)
        out = self.root / 'preview'
        render_batch(self.root / self.current['files']['output_units']['path'],
                     self.root / self.current['files']['output_candidates']['path'], self.root / 'upstream.lock',
                     out,'fixture','Synthetic fixture',tags_path=self.harvest / 'tags/tags',chapter_source_dir=self.harvest)
        self.assertIn('修订运行=2', (out / 'translation-progress.tex').read_text() if (out / 'translation-progress.tex').exists()
                      else '\n'.join(p.read_text() for p in out.glob('*.tex')))

    def test_existing_no_sidecar_binding_and_provenance_are_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,records = fixture(Path(tmp),count=1)
            candidate = clean(load_jsonl(root / records[0]['files']['output_candidates']['path'])[0])
            before = candidate_provenance_hash(root,candidate)
            self.assertEqual(validate_repository_provenance(root,harvest), [])
            (root / 'translation-data/pre-adoption-replays').mkdir()
            self.assertEqual(candidate_provenance_hash(root,candidate),before)
            self.assertEqual(pre_adoption_history(root,records[0]['derivation_id']), [])


if __name__ == '__main__':
    unittest.main()
