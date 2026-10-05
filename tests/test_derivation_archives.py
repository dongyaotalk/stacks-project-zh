from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_derivations import fixture
from test_model_corrections import read, save_decisions, write
from stacks_zh.derivation_archives import derivation_history, load_derivation_archives
from stacks_zh.derivations import (CANDIDATE_FIELDS, DerivationError, byte_hash, clean,
                                   jsonl_bytes, load_repository_derivations, replay_derivation)
from stacks_zh.model_corrections import candidate_provenance_hash, load_repository_corrections
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import load_jsonl, sha256_value, stamp_unit_hashes
from stacks_zh.schema_validation import validate_repository_schemas
from stacks_zh.workflow import render_batch


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout.decode().strip()


def commit(root):
    git(root, 'add', '.')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'Synthetic fixture evidence')
    return git(root, 'rev-parse', 'HEAD')


def save_rows(root, relative, rows):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(jsonl_bytes(rows))
    return {'path': relative, 'hash': byte_hash(path.read_bytes())}


def create_revision(root, previous, number, archive=True, same_text=False):
    """Synthetic model output only; never write these fixtures into project data."""
    units = [clean(row) for row in load_jsonl(root / previous['files']['output_units']['path'])]
    candidates = [clean(row) for row in load_jsonl(root / previous['files']['output_candidates']['path'])]
    origin = git(root, 'rev-parse', 'HEAD')
    record = copy.deepcopy(previous)
    identifier = f'fixture-derive-{number}'
    record.update(derivation_id=identifier, origin_commit=origin, created_at=f'2026-10-04T0{number}:00:00Z')
    record['tool']['version'] = '3' if archive else '2'
    if archive:
        record['previous_derivation_id'] = previous['derivation_id']
        manifest = {'schema_version': 1, 'prior_derivation_id': previous['derivation_id'],
                    'successor_derivation_id': identifier, 'source_commit': record['source_commit'],
                    'origin_commit': origin, 'created_at': record['created_at'],
                    'record': {'path': f"translation-data/derivations/{previous['derivation_id']}.json",
                               'hash': byte_hash((root / f"translation-data/derivations/{previous['derivation_id']}.json").read_bytes())},
                    'files': {}}
        for role in ['output_units', 'output_candidates']:
            path = f"translation-data/retired/derivations/{previous['derivation_id']}/{role.replace('_', '-')}.jsonl"
            destination = root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((root / previous['files'][role]['path']).read_bytes())
            manifest['files'][role] = {'path': path, 'hash': byte_hash(destination.read_bytes())}
        write(root / f"translation-data/derivation-archives/{previous['derivation_id']}.json", manifest)
    record['unit_id_map'] = {row['unit_id']: row['unit_id'] if archive else row['unit_id'].replace('OLD', 'NEW') for row in units}
    frozen = [stamp_unit_hashes({**unit, 'unit_id': record['unit_id_map'][unit['unit_id']]}) for unit in units]
    raw = []
    for unit, candidate, current_unit in zip(units, candidates, frozen, strict=True):
        context = {'unit_id': current_unit['unit_id'], 'source_unit': current_unit,
                   'revision_input': {'kind': 'candidate-to-revise', 'candidate': candidate, 'source_unit': unit},
                   'prompt_version': 'fixture', 'policy_revision': 'fixture', 'source_commit': record['source_commit']}
        row = {key: value for key, value in copy.deepcopy(candidate).items() if key not in {'derivation_id', 'model_correction_id'}}
        row.update(unit_id=current_unit['unit_id'], source_text_hash=current_unit['source_text_hash'],
                   model_id=f'revision-model-{number}', model_lane=f'revision-{number}',
                   model_record_id=f'fixture:revision-{number}:declared', run_id=f'revision-run-{number}',
                   created_at=record['created_at'], context=context, context_hash=sha256_value(context),
                   translation=candidate['translation'] if same_text else f'这是第{number}次范畴（category）修订。',
                   allowed_english=[], term_occurrences=[{'source_term': 'category', 'target_term': '范畴'}],
                   unknown_terms=[{'source_term': 'category', 'target_term': '范畴', 'context': 'Synthetic fixture pending'}],
                   notes=['Synthetic fixture, not actual model output.'], stage='STRUCTURE_OK', term_status='DECISION_REQUIRED')
        row['translation_hash'] = sha256_value(row['translation'])
        raw.append(row)
    correction_id = f'fixture-correction-{number}'
    correction = {'schema_version': 1, 'correction_id': correction_id, 'run_id': raw[0]['run_id'],
                  'source_commit': record['source_commit'], 'created_at': record['created_at'],
                  'unit_ids': [unit['unit_id'] for unit in frozen],
                  'derivation_ids': {unit['unit_id']: identifier for unit in frozen}, 'files': {}}
    for role, rows in [('units', frozen), ('candidates', raw)]:
        correction['files'][role] = save_rows(root, f'translation-data/retired/model-corrections/{correction_id}/{role}.jsonl', rows)
    write(root / f'translation-data/model-corrections/{correction_id}.json', correction)
    run = {'schema_version': 1, 'run_id': raw[0]['run_id'], 'run_kind': 'revision', 'task_id': 'synthetic-fixture',
           'source_commit': record['source_commit'], 'unit_ids': correction['unit_ids'],
           'harness': {'id': 'fixture', 'version': 'fixture', 'adapter_version': 'fixture'},
           'model': {'record_id': raw[0]['model_record_id'], 'provider': 'Fixture',
                     'requested_id': raw[0]['model_id'], 'resolved_id': raw[0]['model_id'],
                     'snapshot': None, 'identity_confidence': 'declared'},
           'inputs': {'prompt_version': 'fixture', 'policy_revision': 'fixture', 'glossary_revision': 'fixture',
                      'context_hashes': [row['context_hash'] for row in raw]},
           'created_at': record['created_at'], 'replayable': False}
    write(root / f"translation-data/runs/{run['run_id']}.json", run)
    for role, rows in [('input_units', units), ('input_candidates', candidates)]:
        name = 'units' if role == 'input_units' else 'candidates'
        record['files'][role] = save_rows(root, f'translation-data/retired/derivations/{identifier}/{name}.jsonl', rows)
    record['operations'] = [{'unit_id': unit['unit_id'], 'kinds': ['model-revision'] + ([] if archive else ['coordinates']),
                             'reason': 'Synthetic fixture revision', 'unit_updates': {}, 'model_correction_id': correction_id,
                             'candidate_updates': {field: row[field] for field in CANDIDATE_FIELDS}}
                            for unit, row in zip(units, raw, strict=True)]
    corrections, errors = load_repository_corrections(root)
    if errors:
        raise AssertionError(errors)
    outputs = replay_derivation(record, units, candidates, corrections, (units, candidates) if archive else None)
    for role, rows in zip(['output_units', 'output_candidates'], outputs, strict=True):
        record['files'][role] = save_rows(root, record['files'][role]['path'], rows)
    write(root / f'translation-data/derivations/{identifier}.json', record)
    return record


def archive_fixture(root, revisions=2):
    record, units, candidates = fixture()
    second_unit = stamp_unit_hashes({**copy.deepcopy(units[0]), 'unit_id': 'tag:OLD2:p001', 'parent_tag': 'OLD2'})
    second_candidate = copy.deepcopy(candidates[0])
    second_candidate.update(unit_id=second_unit['unit_id'], source_text_hash=second_unit['source_text_hash'])
    second_candidate['context']['unit_id'] = second_unit['unit_id']
    second_candidate['context_hash'] = sha256_value(second_candidate['context'])
    units.append(second_unit); candidates.append(second_candidate)
    for role, rows in [('output_units', units), ('output_candidates', candidates)]:
        save_rows(root, record['files'][role]['path'], rows)
    manifest = {'schema_version': 1, 'run_id': 'fixture-run', 'run_kind': 'translation', 'task_id': 'synthetic-fixture',
                'source_commit': record['source_commit'], 'unit_ids': [unit['unit_id'] for unit in units],
                'harness': {'id': 'fixture', 'version': 'fixture', 'adapter_version': 'fixture'},
                'model': {'record_id': 'fixture:model:declared', 'provider': 'Fixture', 'requested_id': 'fixture-model',
                          'resolved_id': 'fixture-model', 'snapshot': None, 'identity_confidence': 'declared'},
                'inputs': {'prompt_version': 'fixture', 'policy_revision': 'fixture', 'glossary_revision': 'fixture',
                           'context_hashes': [row['context_hash'] for row in candidates]},
                'created_at': candidates[0]['created_at'], 'replayable': False}
    write(root / 'translation-data/runs/fixture-run.json', manifest)
    (root / 'upstream.lock').write_text(f'commit = "{record["source_commit"]}"\n')
    git(root, 'init', '-q'); commit(root)
    records = []
    for number in range(1, revisions + 1):
        record = create_revision(root, record, number, archive=number > 1)
        records.append(record)
        if number < revisions:
            commit(root)
    return records


class DerivationArchiveTests(unittest.TestCase):
    def test_single_level_approval_binding_retains_its_existing_format(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); record = archive_fixture(root, revisions=1)[0]
            candidate = clean(load_jsonl(root / record['files']['output_candidates']['path'])[0])
            correction = read(root / 'translation-data/model-corrections/fixture-correction-1.json')
            expected = sha256_value({
                'candidate': candidate, 'derivation': record, 'correction': correction,
                'origin_run': read(root / 'translation-data/runs/fixture-run.json'),
                'correction_run': read(root / 'translation-data/runs/revision-run-1.json'),
            })
            self.assertEqual(candidate_provenance_hash(root, candidate), expected)

    def test_complete_two_unit_history_validates_without_duplicate_origins(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); records = archive_fixture(root)
            self.assertEqual(validate_repository_schemas(root), [])
            self.assertEqual(validate_repository_provenance(root), [])
            origins, errors = load_repository_derivations(root)
            self.assertEqual(errors, []); self.assertEqual(len(origins), 2)
            self.assertEqual({row['unit_id'] for row in origins.values()}, {'tag:OLD1:p001', 'tag:OLD2:p001'})
            active = load_jsonl(root / records[-1]['files']['output_candidates']['path'])
            self.assertEqual({row['derivation_id'] for row in active}, {'fixture-derive-2'})
            self.assertEqual({row['model_id'] for row in active}, {'fixture-model'})
            self.assertTrue(all(row['stage'] == 'STRUCTURE_OK' and row['term_status'] == 'DECISION_REQUIRED' for row in active))

    def test_third_revision_preserves_every_prior_git_blob(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); records = archive_fixture(root, revisions=3)
            self.assertEqual(validate_repository_provenance(root), [])
            history = derivation_history(root, records[-1]['derivation_id'])
            self.assertEqual([entry['derivation']['derivation_id'] for entry in history], [row['derivation_id'] for row in records])
            for entry in history[1:]:
                archive = entry['previous_archive']
                for role, file in archive['files'].items():
                    original = subprocess.run(['git', '-C', str(root), 'show',
                                               f"{archive['origin_commit']}:{read(root / archive['record']['path'])['files'][role]['path']}"],
                                              check=True, capture_output=True).stdout
                    self.assertEqual((root / file['path']).read_bytes(), original)

    def test_preview_discloses_original_and_all_revision_models(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); record = archive_fixture(root, revisions=3)[-1]
            render_batch(root / record['files']['output_units']['path'], root / record['files']['output_candidates']['path'],
                         root / 'upstream.lock', root / 'preview', 'fixture', 'Fixture')
            metadata = (root / 'preview/metadata.tex').read_text()
            for text in ['fixture-model', 'revision-model-1', 'revision-model-2', 'revision-model-3', '修订运行=3']:
                self.assertIn(text, metadata)
            (root / 'translation-data/derivation-archives/fixture-derive-1.json').unlink()
            with self.assertRaisesRegex(ValueError, 'composite provenance'):
                render_batch(root / record['files']['output_units']['path'], root / record['files']['output_candidates']['path'],
                             root / 'upstream.lock', root / 'preview', 'fixture', 'Fixture')

    def test_identical_text_requires_a_new_complete_approval_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); record = archive_fixture(root, revisions=1)[0]
            previous = clean(load_jsonl(root / record['files']['output_candidates']['path'])[0])
            previous_hash = candidate_provenance_hash(root, previous)
            commit(root)
            successor = create_revision(root, record, 2, same_text=True)
            current = clean(load_jsonl(root / successor['files']['output_candidates']['path'])[0])
            self.assertEqual(current['translation_hash'], previous['translation_hash'])
            self.assertNotEqual(candidate_provenance_hash(root, current), previous_hash)
            # The normal decision test helper has a single-row input contract.
            single = copy.deepcopy(successor)
            single['files']['output_candidates']['path'] = 'one-row.json'
            write(root / 'one-row.json', current)
            paths = save_decisions(root, single)
            for path in paths:
                value = read(path); value['provenance_hash'] = previous_hash; write(path, value)
            from stacks_zh.decisions import validate_repository_decisions
            errors = validate_repository_decisions(root)
            self.assertEqual(sum('provenance_hash' in error for error in errors), 3, errors)

    def test_binding_includes_each_ancestor_archive_correction_and_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); record = archive_fixture(root, revisions=3)[-1]
            candidate = clean(load_jsonl(root / record['files']['output_candidates']['path'])[0])
            binding = candidate_provenance_hash(root, candidate)
            for relative in ['translation-data/derivations/fixture-derive-1.json',
                             'translation-data/derivations/fixture-derive-2.json',
                             'translation-data/derivation-archives/fixture-derive-1.json',
                             'translation-data/derivation-archives/fixture-derive-2.json',
                             'translation-data/model-corrections/fixture-correction-1.json',
                             'translation-data/model-corrections/fixture-correction-2.json',
                             'translation-data/runs/revision-run-1.json',
                             'translation-data/runs/revision-run-2.json', 'translation-data/runs/fixture-run.json']:
                with self.subTest(relative=relative):
                    path = root / relative; before = path.read_bytes(); value = read(path)
                    value['created_at'] = '2026-10-05T00:00:00Z'; write(path, value)
                    self.assertNotEqual(candidate_provenance_hash(root, candidate), binding)
                    path.write_bytes(before)

    def test_archive_rejects_bad_source_origin_record_hash_roles_and_missing_output(self):
        for fault in ['source', 'origin', 'record-hash', 'role', 'missing', 'rehashed-output', 'record-bytes']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); records = archive_fixture(root)
                path = root / 'translation-data/derivation-archives/fixture-derive-1.json'; archive = read(path)
                if fault == 'source': archive['source_commit'] = 'b' * 40
                if fault == 'origin': archive['origin_commit'] = 'b' * 40
                if fault == 'record-hash': archive['record']['hash'] = 'sha256:' + '0' * 64
                if fault == 'role': archive['files']['output_units'] = archive['files']['output_candidates']
                if fault == 'missing': (root / archive['files']['output_units']['path']).unlink()
                if fault == 'rehashed-output':
                    frozen = root / archive['files']['output_candidates']['path']; frozen.write_bytes(frozen.read_bytes() + b'\n')
                    archive['files']['output_candidates']['hash'] = byte_hash(frozen.read_bytes())
                    prior_path = root / archive['record']['path']; prior = read(prior_path)
                    prior['files']['output_candidates']['hash'] = archive['files']['output_candidates']['hash']; write(prior_path, prior)
                    archive['record']['hash'] = byte_hash(prior_path.read_bytes())
                if fault == 'record-bytes':
                    prior_path = root / archive['record']['path']; prior_path.write_bytes(prior_path.read_bytes() + b'\n')
                    archive['record']['hash'] = byte_hash(prior_path.read_bytes())
                write(path, archive)
                self.assertTrue(load_derivation_archives(root)[1])

    def test_rehashed_evidence_cannot_overwrite_its_first_git_addition(self):
        for role in ['manifest', 'output_units', 'output_candidates', 'successor-record', 'successor-input']:
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); records = archive_fixture(root); commit(root)
                manifest_path = root / 'translation-data/derivation-archives/fixture-derive-1.json'; archive = read(manifest_path)
                if role == 'manifest':
                    archive['created_at'] = '2026-10-05T00:00:00Z'; write(manifest_path, archive)
                elif role.startswith('output_'):
                    path = root / archive['files'][role]['path']; path.write_bytes(path.read_bytes() + b'\n')
                    archive['files'][role]['hash'] = byte_hash(path.read_bytes()); write(manifest_path, archive)
                elif role == 'successor-record':
                    path = root / 'translation-data/derivations/fixture-derive-2.json'; value = read(path)
                    value['created_at'] = '2026-10-05T00:00:00Z'; write(path, value)
                else:
                    entry = records[-1]['files']['input_units']; path = root / entry['path']; path.write_bytes(path.read_bytes() + b'\n')
                    records[-1]['files']['input_units']['hash'] = byte_hash(path.read_bytes())
                    write(root / 'translation-data/derivations/fixture-derive-2.json', records[-1])
                self.assertTrue(any('first Git addition' in error for error in load_repository_derivations(root)[1]))

    def test_wrong_git_origin_is_rejected_even_when_reachable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); record = archive_fixture(root)[-1]
            initial = git(root, 'rev-list', '--max-parents=0', 'HEAD')
            path = root / 'translation-data/derivation-archives/fixture-derive-1.json'; archive = read(path)
            archive['origin_commit'] = initial; write(path, archive)
            record['origin_commit'] = initial; write(root / 'translation-data/derivations/fixture-derive-2.json', record)
            self.assertTrue(load_derivation_archives(root)[1])

    def test_paths_reject_escape_symlink_and_role_substitution(self):
        for fault in ['escape', 'symlink', 'parent-symlink']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); archive_fixture(root)
                path = root / 'translation-data/derivation-archives/fixture-derive-1.json'; archive = read(path)
                frozen = root / archive['files']['output_units']['path']
                if fault == 'escape':
                    archive['files']['output_units']['path'] = '../output-units.jsonl'; write(path, archive)
                elif fault == 'symlink':
                    target = root / 'target'; target.write_bytes(frozen.read_bytes()); frozen.unlink(); frozen.symlink_to(target)
                else:
                    directory = path.parent; target = root / 'archive-target'; directory.rename(target); directory.symlink_to(target, target_is_directory=True)
                self.assertTrue(load_derivation_archives(root)[1])

    def test_v3_requires_previous_archive_matching_successor_and_origin(self):
        for fault in ['missing', 'predecessor', 'successor', 'origin', 'version']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); record = archive_fixture(root)[-1]
                path = root / 'translation-data/derivation-archives/fixture-derive-1.json'; archive = read(path)
                if fault == 'missing': path.unlink()
                if fault == 'predecessor': record['previous_derivation_id'] = 'nonexistent'
                if fault == 'successor': archive['successor_derivation_id'] = 'different'; write(path, archive)
                if fault == 'origin': record['origin_commit'] = git(root, 'rev-list', '--max-parents=0', 'HEAD')
                if fault == 'version': record['tool']['version'] = '2'
                write(root / 'translation-data/derivations/fixture-derive-2.json', record)
                self.assertTrue(load_repository_derivations(root)[1])

    def test_v3_cannot_drop_a_unit_operation_or_actual_revision(self):
        for fault in ['map', 'operation', 'correction', 'batch-path', 'empty-previous', 'missing-field']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); record = archive_fixture(root)[-1]
                if fault == 'map': del record['unit_id_map']['tag:NEW2:p001']
                if fault == 'operation': record['operations'].pop()
                if fault == 'correction':
                    operation = record['operations'][1]; operation.pop('model_correction_id'); operation['kinds'] = ['term-display']
                if fault == 'batch-path': record['files']['output_units']['path'] = 'translation-data/units/other.jsonl'
                if fault == 'empty-previous': record.pop('previous_derivation_id')
                if fault == 'missing-field': record['operations'][1]['candidate_updates'].pop('allowed_english')
                write(root / 'translation-data/derivations/fixture-derive-2.json', record)
                self.assertTrue(load_repository_derivations(root)[1])

    def test_fork_and_orphan_history_are_rejected(self):
        for fault in ['fork', 'successor-removed', 'extra-snapshot', 'extra-archive']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); record = archive_fixture(root)[-1]
                if fault == 'fork':
                    fork = copy.deepcopy(record); fork['derivation_id'] = 'fork'
                    for role, name in [('input_units', 'units'), ('input_candidates', 'candidates')]:
                        payload = load_jsonl(root / fork['files'][role]['path'])
                        fork['files'][role] = save_rows(root, f'translation-data/retired/derivations/fork/{name}.jsonl', payload)
                    write(root / 'translation-data/derivations/fork.json', fork)
                if fault == 'successor-removed': (root / 'translation-data/derivations/fixture-derive-2.json').unlink()
                if fault == 'extra-snapshot': save_rows(root, 'translation-data/retired/derivations/orphan/output-units.jsonl', [])
                if fault == 'extra-archive':
                    archive = read(root / 'translation-data/derivation-archives/fixture-derive-1.json')
                    archive['prior_derivation_id'] = 'orphan'; write(root / 'translation-data/derivation-archives/orphan.json', archive)
                self.assertTrue(load_repository_derivations(root)[1])

    def test_history_cycles_and_self_reference_fail_without_recursion_error(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); records = archive_fixture(root, revisions=3)
            first_path = root / 'translation-data/derivations/fixture-derive-1.json'; first = read(first_path)
            first['previous_derivation_id'] = records[-1]['derivation_id']; write(first_path, first)
            with self.assertRaisesRegex(ValueError, 'cyclic'):
                derivation_history(root, records[-1]['derivation_id'])
            self.assertTrue(load_repository_derivations(root)[1])
            record = records[-1]; record['previous_derivation_id'] = record['derivation_id']
            write(root / f"translation-data/derivations/{record['derivation_id']}.json", record)
            self.assertTrue(load_repository_derivations(root)[1])

    def test_exact_previous_input_source_and_origin_identity_are_preserved(self):
        for fault in ['context', 'source', 'identity']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); record = archive_fixture(root)[-1]
                units = load_jsonl(root / record['files']['input_units']['path'])
                candidates = load_jsonl(root / record['files']['input_candidates']['path'])
                corrections, _ = load_repository_corrections(root)
                if fault == 'context':
                    candidates[0]['context']['prompt_version'] = 'forged'
                if fault == 'identity': candidates[0]['model_id'] = 'forged-model'
                if fault == 'source': record['operations'][0]['unit_updates'] = {'source_text': 'A changed source.'}; record['operations'][0]['kinds'].append('protected-extraction')
                with self.assertRaises(DerivationError):
                    replay_derivation(record, units, candidates, corrections,
                                      (load_jsonl(root / record['files']['input_units']['path']),
                                       load_jsonl(root / record['files']['input_candidates']['path'])))

    def test_schema_check_covers_archives_and_historical_outputs(self):
        for relative in ['translation-data/derivation-archives/fixture-derive-1.json',
                         'translation-data/retired/derivations/fixture-derive-1/output-units.jsonl',
                         'translation-data/retired/derivations/fixture-derive-1/output-candidates.jsonl']:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); archive_fixture(root); path = root / relative
                if relative.endswith('.json'): write(path, {})
                else: path.write_text('{}\n')
                self.assertTrue(any(relative in error for error in validate_repository_schemas(root)))
