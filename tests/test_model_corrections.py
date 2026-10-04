from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_derivations import save_fixture
from stacks_zh.decisions import validate_repository_decisions
from stacks_zh.derivations import (CANDIDATE_FIELDS, DerivationError, byte_hash,
                                   jsonl_bytes, load_repository_derivations, replay_derivation)
from stacks_zh.model_corrections import candidate_provenance_hash, load_repository_corrections
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import load_jsonl, sha256_value
from stacks_zh.workflow import render_batch


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def correction_fixture(root, translation='这是一个范畴（category）。'):
    record, derivation_path, _ = save_fixture(root)
    original_units = load_jsonl(root / record['files']['input_units']['path'])
    original_candidates = load_jsonl(root / record['files']['input_candidates']['path'])
    frozen = read(root / record['files']['output_units']['path'])
    original = {k: v for k, v in original_candidates[0].items() if not k.startswith('_')}
    original_unit = {k: v for k, v in original_units[0].items() if not k.startswith('_')}
    context = {'unit_id': frozen['unit_id'], 'source_unit': frozen,
               'revision_input': {'kind': 'candidate-to-revise', 'candidate': original, 'source_unit': original_unit},
               'prompt_version': 'fixture', 'policy_revision': 'fixture', 'source_commit': record['source_commit']}
    raw = {**copy.deepcopy(original), 'unit_id': frozen['unit_id'], 'source_text_hash': frozen['source_text_hash'],
           'model_id': 'revision-model', 'model_lane': 'revision', 'model_record_id': 'fixture:revision:declared',
           'run_id': 'revision-run', 'created_at': '2026-10-04T02:00:00Z',
           'context': context, 'context_hash': sha256_value(context),
           'translation': translation, 'stage': 'STRUCTURE_OK', 'term_status': 'DECISION_REQUIRED',
           'term_occurrences': [{'source_term': 'category', 'target_term': '范畴'}],
           'unknown_terms': [{'source_term': 'category', 'target_term': '范畴', 'context': 'fixture pending'}],
           'notes': ['Fixture revision, not real model output.']}
    raw['translation_hash'] = sha256_value(raw['translation'])
    correction = {'schema_version': 1, 'correction_id': 'fixture-correction',
                  'run_id': raw['run_id'], 'source_commit': record['source_commit'], 'created_at': raw['created_at'],
                  'unit_ids': [frozen['unit_id']], 'derivation_ids': {frozen['unit_id']: record['derivation_id']},
                  'files': {}}
    for role, rows in [('units', [frozen]), ('candidates', [raw])]:
        path = root / f'translation-data/retired/model-corrections/fixture-correction/{role}.jsonl'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(jsonl_bytes(rows))
        correction['files'][role] = {'path': path.relative_to(root).as_posix(), 'hash': byte_hash(path.read_bytes())}
    revision_manifest = {'schema_version': 1, 'run_id': raw['run_id'], 'run_kind': 'revision', 'task_id': 'fixture',
                         'source_commit': record['source_commit'], 'unit_ids': [frozen['unit_id']],
                         'harness': {'id': 'fixture', 'version': 'fixture', 'adapter_version': 'fixture'},
                         'model': {'record_id': raw['model_record_id'], 'provider': 'Fixture',
                                   'requested_id': raw['model_id'], 'resolved_id': raw['model_id'],
                                   'snapshot': None, 'identity_confidence': 'declared'},
                         'inputs': {'prompt_version': 'fixture', 'policy_revision': 'fixture',
                                    'glossary_revision': 'fixture', 'context_hashes': [raw['context_hash']]},
                         'created_at': raw['created_at'], 'replayable': False}
    run_path = root / 'translation-data/runs/revision-run.json'
    write(run_path, revision_manifest)
    correction_path = root / 'translation-data/model-corrections/fixture-correction.json'
    write(correction_path, correction)
    (root / 'upstream.lock').write_text(f'commit = "{record["source_commit"]}"\n')
    record['tool']['version'] = '2'
    operation = record['operations'][0]
    operation['kinds'].append('model-revision')
    operation['model_correction_id'] = correction['correction_id']
    operation['candidate_updates'] = {field: raw[field] for field in CANDIDATE_FIELDS}
    corrections, errors = load_repository_corrections(root)
    if errors:
        raise AssertionError(errors)
    units, candidates = replay_derivation(record, original_units, original_candidates, corrections)
    for role, rows in [('output_units', units), ('output_candidates', candidates)]:
        path = root / record['files'][role]['path']
        path.write_bytes(jsonl_bytes(rows))
        record['files'][role]['hash'] = byte_hash(path.read_bytes())
    write(derivation_path, record)
    return record, correction, raw, derivation_path, correction_path, run_path


def save_decisions(root, record, with_binding=True):
    candidate = read(root / record['files']['output_candidates']['path'])
    binding = {'provenance_hash': candidate_provenance_hash(root, candidate)} if with_binding else {}
    selection = {'schema_version': 1, 'selection_id': 'fixture-selection', 'unit_id': candidate['unit_id'],
                 'run_id': candidate['run_id'], 'source_commit': candidate['source_commit'],
                 'translation_hash': candidate['translation_hash'], 'decision': 'accept-candidate',
                 'decided_by': 'fixture-maintainer', 'decided_at': '2026-10-04T03:00:00Z', 'reason': 'fixture', **binding}
    review = {'schema_version': 1, 'review_id': 'fixture-review', 'unit_id': candidate['unit_id'],
              'run_id': candidate['run_id'], 'source_commit': candidate['source_commit'],
              'candidate_hash': candidate['translation_hash'], 'resulting_translation_hash': candidate['translation_hash'],
              'review_type': 'language', 'reviewer': 'fixture-human', 'reviewed_at': '2026-10-04T03:00:00Z',
              'decision': 'approved', 'issues_closed': [], 'notes': ['Synthetic test fixture.'], **binding}
    revision = {'schema_version': 1, 'revision_id': 'fixture-revision', 'unit_id': candidate['unit_id'],
                'origin_run_id': candidate['run_id'], 'source_commit': candidate['source_commit'],
                'source_text_hash': candidate['source_text_hash'], 'translation_hash': candidate['translation_hash'],
                'translation': candidate['translation'], 'selection_id': selection['selection_id'],
                'selected_by': selection['decided_by'], 'reason': 'Synthetic fixture adoption.',
                'review_ids': [review['review_id']], 'risk_level': 'R1', 'stage': 'PUBLISHED',
                'source_status': 'CURRENT', 'qa_status': 'PASS', 'term_status': 'CLEAR',
                'publication_status': 'RELEASED', 'status': 'current', 'supersedes_revision_id': None,
                'created_at': '2026-10-04T03:00:00Z', **binding}
    # Approvals exist only in this temporary fixture, never in repository data.
    write(root / 'config/glossary.yml', {'entries': [{'source_term': 'category', 'target_term': '范畴',
         'status': 'approved', 'definition_or_context': 'fixture', 'evidence': ['fixture']}]})
    paths = [root / 'translation-data/selections/fixture-selection.json', root / 'review/language/fixture-review.json',
             root / 'translation-data/reviewed/fixture-revision.json']
    for path, row in zip(paths, [selection, review, revision], strict=True):
        write(path, row)
    return paths


class ModelCorrectionTests(unittest.TestCase):
    def test_both_runs_validate_and_original_identity_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, _, raw, *_ = correction_fixture(root)
            self.assertEqual(validate_repository_provenance(root), [])
            active = read(root / record['files']['output_candidates']['path'])
            self.assertEqual(active['translation'], raw['translation'])
            self.assertEqual(active['run_id'], 'fixture-run')
            self.assertEqual(active['model_id'], 'fixture-model')
            self.assertEqual(active['model_correction_id'], 'fixture-correction')
            self.assertEqual(active['term_status'], 'DECISION_REQUIRED')

    def test_snapshot_hashes_source_context_scope_and_run_are_checked(self):
        for fault in ['hash', 'source', 'context', 'scope', 'run-kind']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                _, correction, raw, _, path, run = correction_fixture(root)
                if fault == 'hash': correction['files']['units']['hash'] = 'sha256:' + '0' * 64
                if fault == 'source': correction['source_commit'] = 'b' * 40
                if fault == 'scope': correction['unit_ids'].append('tag:MISSING:p001')
                if fault == 'run-kind':
                    manifest = read(run); manifest['run_kind'] = 'translation'; write(run, manifest)
                if fault == 'context':
                    raw['context']['source_unit']['source_text'] = 'A wrong category.'
                    raw['context_hash'] = sha256_value(raw['context'])
                    payload = jsonl_bytes([raw]); snapshot = root / correction['files']['candidates']['path']
                    snapshot.write_bytes(payload); correction['files']['candidates']['hash'] = byte_hash(payload)
                write(path, correction)
                self.assertTrue(load_repository_corrections(root)[1])

    def test_output_cannot_be_changed_even_when_active_hash_is_recomputed(self):
        for field in ['translation', 'notes', 'term_occurrences', 'unknown_terms', 'allowed_english']:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                record, _, _, path, *_ = correction_fixture(root)
                record['operations'][0]['candidate_updates'][field] = '篡改。' if field == 'translation' else ['forged'] if field == 'allowed_english' else []
                write(path, record)
                self.assertTrue(any('differs from frozen model output' in error for error in load_repository_derivations(root)[1]))

    def test_previous_candidate_and_derivation_must_be_exact(self):
        for fault in ['previous', 'derivation']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                record, correction, raw, _, correction_path, run_path = correction_fixture(root)
                if fault == 'previous':
                    raw['context']['revision_input']['candidate']['translation'] = '另一个旧候选。'
                    raw['context_hash'] = sha256_value(raw['context'])
                    payload = jsonl_bytes([raw]); (root / correction['files']['candidates']['path']).write_bytes(payload)
                    correction['files']['candidates']['hash'] = byte_hash(payload)
                    run = read(run_path); run['inputs']['context_hashes'] = [raw['context_hash']]; write(run_path, run)
                else:
                    correction['derivation_ids'][record['unit_id_map']['tag:OLD1:p001']] = 'another-derive'
                write(correction_path, correction)
                self.assertTrue(load_repository_derivations(root)[1])

    def test_version_one_cannot_enable_model_rewriting(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, *_ = correction_fixture(root)
            record['tool']['version'] = '1'
            with self.assertRaisesRegex(DerivationError, 'version 2'):
                replay_derivation(record, load_jsonl(root / record['files']['input_units']['path']),
                                  load_jsonl(root / record['files']['input_candidates']['path']))

    def test_additional_model_identity_is_validated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, _, _, _, run_path = correction_fixture(root)
            run = read(run_path); run['model']['record_id'] = 'forged:model'; write(run_path, run)
            self.assertTrue(any('model_record_id does not match' in error for error in validate_repository_provenance(root)))

    def test_unknown_identity_or_harness_cannot_create_a_correction(self):
        for fault in ['identity', 'harness']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                _, _, _, _, _, path = correction_fixture(root)
                run = read(path)
                if fault == 'identity': run['model']['identity_confidence'] = 'unknown'
                else: run['harness']['version'] = 'unknown'
                write(path, run)
                self.assertTrue(any('concrete Harness version' in error for error in load_repository_corrections(root)[1]))

    def test_one_revision_run_cannot_be_split_into_duplicate_records(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, correction, _, _, _, _ = correction_fixture(root)
            duplicate = copy.deepcopy(correction)
            duplicate['correction_id'] = 'duplicate-correction'
            for role, entry in duplicate['files'].items():
                source = root / entry['path']
                entry['path'] = entry['path'].replace('fixture-correction', 'duplicate-correction')
                target = root / entry['path']; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            write(root / 'translation-data/model-corrections/duplicate-correction.json', duplicate)
            self.assertTrue(any('one complete correction record' in error for error in load_repository_corrections(root)[1]))

    def test_empty_term_metadata_cannot_claim_approval_for_declared_terms(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, correction, raw, _, path, _ = correction_fixture(root)
            raw['unknown_terms'] = []; raw['term_status'] = 'CLEAR'; raw['stage'] = 'TERM_OK'
            snapshot = root / correction['files']['candidates']['path']
            snapshot.write_bytes(jsonl_bytes([raw])); correction['files']['candidates']['hash'] = byte_hash(snapshot.read_bytes())
            write(path, correction)
            write(root / 'config/glossary.yml', {'entries': []})
            self.assertTrue(any('unverified terminology approval' in error for error in load_repository_corrections(root)[1]))

    def test_real_glossary_approval_allows_a_clear_model_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, correction, raw, derivation_path, correction_path, _ = correction_fixture(root)
            write(root / 'config/glossary.yml', {'entries': [{'source_term': 'category', 'target_term': '范畴',
                  'status': 'approved', 'definition_or_context': 'fixture', 'evidence': ['fixture']}]})
            raw['unknown_terms'] = []; raw['term_status'] = 'CLEAR'; raw['stage'] = 'TERM_OK'
            snapshot = root / correction['files']['candidates']['path']
            snapshot.write_bytes(jsonl_bytes([raw])); correction['files']['candidates']['hash'] = byte_hash(snapshot.read_bytes())
            write(correction_path, correction)
            record['operations'][0]['candidate_updates']['unknown_terms'] = []
            corrections, errors = load_repository_corrections(root)
            self.assertEqual(errors, [])
            units, candidates = replay_derivation(record, load_jsonl(root / record['files']['input_units']['path']),
                                                   load_jsonl(root / record['files']['input_candidates']['path']), corrections)
            self.assertEqual(candidates[0]['term_status'], 'CLEAR')
            self.assertEqual(candidates[0]['stage'], 'TERM_OK')

    def test_rehashed_committed_correction_and_run_cannot_be_overwritten(self):
        for fault in ['output', 'run']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                _, correction, raw, _, correction_path, run_path = correction_fixture(root)
                subprocess.run(['git', '-C', str(root), 'add', '.'], check=True, capture_output=True)
                subprocess.run(['git', '-C', str(root), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                                'commit', '-qm', 'fixture frozen revision'], check=True, capture_output=True)
                self.assertEqual(validate_repository_provenance(root), [])
                if fault == 'output':
                    raw['notes'].append('forged')
                    payload = jsonl_bytes([raw]); (root / correction['files']['candidates']['path']).write_bytes(payload)
                    correction['files']['candidates']['hash'] = byte_hash(payload); write(correction_path, correction)
                else:
                    run = read(run_path); run['notes'] = ['forged']; write(run_path, run)
                self.assertTrue(any('first Git addition' in error for error in load_repository_corrections(root)[1]))

    def test_orphaned_frozen_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, _, path, *_ = correction_fixture(root)
            path.unlink()
            self.assertTrue(any('no active derived candidate' in error for error in load_repository_derivations(root)[1]))

    def test_existing_approvals_without_composite_binding_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, *_ = correction_fixture(root)
            save_decisions(root, record, False)
            errors = validate_repository_decisions(root)
            self.assertEqual(sum('provenance_hash' in error for error in errors), 3, errors)

    def test_unchanged_text_does_not_inherit_old_approvals_for_a_new_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            previous_translation = '一个范畴（category）。'
            record, *_ = correction_fixture(root, previous_translation)
            active = read(root / record['files']['output_candidates']['path'])
            self.assertEqual(active['translation_hash'], sha256_value(previous_translation))
            save_decisions(root, record, False)
            self.assertEqual(sum('provenance_hash' in error for error in validate_repository_decisions(root)), 3)

    def test_all_three_decisions_bind_the_complete_chain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, *_ = correction_fixture(root)
            paths = save_decisions(root, record)
            self.assertEqual(validate_repository_decisions(root), [])
            for path in paths:
                original = read(path)
                row = {**original, 'provenance_hash': 'sha256:' + '0' * 64}; write(path, row)
                self.assertTrue(any('provenance_hash' in error for error in validate_repository_decisions(root)))
                write(path, original)

    def test_preview_discloses_both_models_and_blocks_broken_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, _, _, _, correction_path, _ = correction_fixture(root)
            args = (root / record['files']['output_units']['path'], root / record['files']['output_candidates']['path'],
                    root / 'upstream.lock', root / 'preview', 'fixture', 'Fixture')
            render_batch(*args)
            metadata = (root / 'preview/metadata.tex').read_text()
            for text in ['fixture-model', 'revision-model', '复合来源', '修订运行=1']:
                self.assertIn(text, metadata)
            correction_path.unlink()
            with self.assertRaisesRegex(ValueError, 'composite provenance'):
                render_batch(*args)
