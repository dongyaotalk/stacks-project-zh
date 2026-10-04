from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from stacks_zh.derivations import (
    DerivationError, byte_hash, jsonl_bytes, load_repository_derivations, replay_derivation,
)
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import sha256_value, stamp_unit_hashes
from stacks_zh.workflow import render_batch

COMMIT = 'a' * 40


def fixture():
    unit = stamp_unit_hashes({
        'schema_version': 1, 'unit_id': 'tag:OLD1:p001', 'parent_tag': 'OLD1',
        'chapter': 'test', 'node_kind': 'paragraph', 'risk_level': 'R1',
        'source_commit': COMMIT, 'source_text': 'A category.', 'source_status': 'CURRENT',
        'placeholders': {}, 'render': {'prefix': '', 'suffix': '\n'},
    })
    context = {'unit_id': unit['unit_id'], 'neighbor_unit_ids': [unit['unit_id'], 'tag:OTHER:p001'],
               'prompt_version': 'fixture', 'policy_revision': 'fixture', 'source_commit': COMMIT}
    candidate = {
        'schema_version': 2, 'unit_id': unit['unit_id'], 'source_commit': COMMIT,
        'source_text_hash': unit['source_text_hash'], 'model_id': 'fixture-model',
        'model_lane': 'fixture', 'harness_id': 'fixture', 'harness_version': 'fixture',
        'model_record_id': 'fixture:model:declared', 'model_snapshot': None,
        'model_identity_confidence': 'declared', 'run_id': 'fixture-run',
        'reasoning_effort': 'fixture', 'prompt_version': 'fixture', 'glossary_revision': 'fixture',
        'context': context, 'context_hash': sha256_value(context), 'translation': '一个范畴。',
        'translation_hash': sha256_value('一个范畴。'), 'allowed_english': [],
        'term_occurrences': [], 'unknown_terms': [], 'notes': [], 'stage': 'TERM_OK',
        'source_status': 'CURRENT', 'qa_status': 'PASS', 'term_status': 'CLEAR',
        'publication_status': 'CANDIDATE', 'created_at': '2026-10-04T00:00:00Z',
    }
    mapping = {unit['unit_id']: 'tag:NEW1:p001'}
    record = {
        'schema_version': 1, 'derivation_id': 'fixture-derive', 'source_commit': COMMIT, 'origin_commit': COMMIT,
        'created_at': '2026-10-04T01:00:00Z', 'tool': {'id': 'stacks-zh-derive', 'version': '1'},
        'files': {role: {'path': path, 'hash': 'sha256:' + '0' * 64} for role, path in (
            ('input_units', 'translation-data/retired/derivations/fixture-derive/units.jsonl'),
            ('input_candidates', 'translation-data/retired/derivations/fixture-derive/candidates.jsonl'),
            ('output_units', 'translation-data/units/test.jsonl'),
            ('output_candidates', 'translation-data/candidates/fixture/test.jsonl'),
        )},
        'unit_id_map': mapping,
        'operations': [{'unit_id': unit['unit_id'], 'kinds': ['coordinates', 'term-display'],
                        'reason': 'fixture mechanical correction', 'unit_updates': {},
                        'candidate_updates': {
                            'translation': '一个范畴（category）。',
                            'term_occurrences': [{'source_term': 'category', 'target_term': '范畴'}],
                            'unknown_terms': [{'source_term': 'category', 'target_term': '范畴', 'context': 'fixture pending'}],
                        }}],
    }
    return record, [unit], [candidate]


def save_fixture(root):
    record, units, candidates = fixture()
    new_units, new_candidates = replay_derivation(record, units, candidates)
    for role, rows in [('input_units', units), ('input_candidates', candidates),
                       ('output_units', new_units), ('output_candidates', new_candidates)]:
        path = root / record['files'][role]['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = jsonl_bytes(rows)
        if role.startswith('input_'):
            # Preserve noncanonical raw bytes as well as the original row values.
            payload = ('\n'.join(json.dumps(row, ensure_ascii=False) for row in rows) + '\n\n').encode()
        path.write_bytes(payload)
        record['files'][role]['hash'] = byte_hash(payload)
    manifest = {
        'schema_version': 1, 'run_id': 'fixture-run', 'run_kind': 'translation',
        'task_id': 'fixture', 'source_commit': COMMIT, 'unit_ids': [units[0]['unit_id']],
        'harness': {'id': 'fixture', 'version': 'fixture', 'adapter_version': 'fixture'},
        'model': {'record_id': 'fixture:model:declared', 'provider': 'Fixture',
                  'requested_id': 'fixture-model', 'resolved_id': 'fixture-model',
                  'snapshot': None, 'identity_confidence': 'declared'},
        'inputs': {'prompt_version': 'fixture', 'policy_revision': 'fixture',
                   'glossary_revision': 'fixture', 'context_hashes': [candidates[0]['context_hash']]},
        'created_at': candidates[0]['created_at'], 'replayable': False,
    }
    run = root / 'translation-data/runs/fixture-run.json'
    run.parent.mkdir(parents=True)
    run.write_text(json.dumps(manifest))
    active_units = root / record['files']['output_units']['path']
    active_candidates = root / record['files']['output_candidates']['path']
    derived_unit_bytes, derived_candidate_bytes = active_units.read_bytes(), active_candidates.read_bytes()
    active_units.write_bytes((root / record['files']['input_units']['path']).read_bytes())
    active_candidates.write_bytes((root / record['files']['input_candidates']['path']).read_bytes())
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout.decode().strip()
    git('init', '-q')
    git('add', record['files']['output_units']['path'], record['files']['output_candidates']['path'], 'translation-data/runs/fixture-run.json')
    git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture origin')
    record['origin_commit'] = git('rev-parse', 'HEAD')
    active_units.write_bytes(derived_unit_bytes)
    active_candidates.write_bytes(derived_candidate_bytes)
    derivation = root / 'translation-data/derivations/fixture-derive.json' 
    derivation.parent.mkdir(parents=True)
    derivation.write_text(json.dumps(record))
    return record, derivation, run


class DerivationTests(unittest.TestCase):
    def test_replay_remaps_context_and_preserves_origin_identity_and_bytes(self):
        record, units, candidates = fixture()
        before = copy.deepcopy((units, candidates))
        new_units, new_candidates = replay_derivation(record, units, candidates)
        self.assertEqual((units, candidates), before)
        self.assertEqual(new_units[0]['unit_id'], 'tag:NEW1:p001')
        self.assertEqual(new_candidates[0]['context']['neighbor_unit_ids'], ['tag:NEW1:p001', 'tag:OTHER:p001'])
        self.assertEqual(new_candidates[0]['created_at'], candidates[0]['created_at'])
        self.assertEqual(new_candidates[0]['term_status'], 'DECISION_REQUIRED')
        self.assertEqual(new_candidates[0]['stage'], 'STRUCTURE_OK')

    def test_raw_run_context_is_checked_after_coordinate_migration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, path, run = save_fixture(root)
            before = run.read_bytes()
            self.assertEqual(validate_repository_provenance(root), [])
            self.assertEqual(run.read_bytes(), before)
            manifest = json.loads(before)
            manifest['inputs']['context_hashes'] = ['sha256:' + 'f' * 64]
            run.write_text(json.dumps(manifest))
            self.assertTrue(any('original run bytes' in e for e in validate_repository_provenance(root)))

    def test_every_input_and_output_byte_hash_is_checked(self):
        for role in ['input_units', 'input_candidates', 'output_units', 'output_candidates']:
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                record, _, _ = save_fixture(root)
                path = root / record['files'][role]['path']
                path.write_bytes(path.read_bytes() + b'\n')
                self.assertTrue(any('hash mismatch' in e for e in load_repository_derivations(root)[1]))

    def test_rehashed_output_tampering_still_fails_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, manifest, _ = save_fixture(root)
            path = root / record['files']['output_candidates']['path']
            path.write_bytes(path.read_bytes().replace('一个'.encode(), '两个'.encode()))
            record['files']['output_candidates']['hash'] = byte_hash(path.read_bytes())
            manifest.write_text(json.dumps(record))
            self.assertTrue(any('match replay' in e for e in load_repository_derivations(root)[1]))

    def test_rehashed_raw_snapshot_tampering_fails_git_origin(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, manifest, _ = save_fixture(root)
            path = root / record['files']['input_candidates']['path']
            raw = json.loads(path.read_text())
            raw['notes'] = ['forged origin']
            path.write_text(json.dumps(raw))
            record['files']['input_candidates']['hash'] = byte_hash(path.read_bytes())
            manifest.write_text(json.dumps(record))
            self.assertTrue(any('original Git bytes' in e for e in load_repository_derivations(root)[1]))

    def test_unreachable_origin_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, manifest, _ = save_fixture(root)
            record['origin_commit'] = 'f' * 40
            manifest.write_text(json.dumps(record))
            self.assertTrue(any('reachable ancestor' in e for e in load_repository_derivations(root)[1]))

    def test_identity_and_approval_fields_cannot_be_changed(self):
        for field in ['model_id', 'run_id', 'created_at', 'source_commit', 'stage', 'term_status', 'review_claims']:
            with self.subTest(field=field):
                record, units, candidates = fixture()
                record['operations'][0]['candidate_updates'][field] = 'forged'
                with self.assertRaisesRegex(DerivationError, 'immutable'):
                    replay_derivation(record, units, candidates)

    def test_free_retranslation_is_rejected(self):
        record, units, candidates = fixture()
        record['operations'][0]['candidate_updates']['translation'] = '两个范畴（category）。'
        with self.assertRaisesRegex(DerivationError, 'freely rewrites'):
            replay_derivation(record, units, candidates)

    def test_control_characters_cannot_hide_a_derived_translation(self):
        for control in ['%', '{', '#', '&', '_', '^', '~', '\\ ', '\\\\']:
            with self.subTest(control=control):
                record, units, candidates = fixture()
                record['operations'][0]['candidate_updates']['translation'] = control + '一个范畴（category）。'
                with self.assertRaisesRegex(DerivationError, 'unprotected TeX'):
                    replay_derivation(record, units, candidates)

    def test_source_tex_cannot_be_changed(self):
        record, units, candidates = fixture()
        record['operations'][0]['kinds'].append('protected-extraction')
        record['operations'][0]['unit_updates']['source_text'] = 'Two categories.'
        with self.assertRaisesRegex(DerivationError, 'source TeX'):
            replay_derivation(record, units, candidates)

    def test_missing_map_reason_or_declared_operation_is_rejected(self):
        for change in ['map', 'reason', 'kind', 'operation']:
            with self.subTest(change=change):
                record, units, candidates = fixture()
                if change == 'map': record['unit_id_map'] = {}
                if change == 'reason': record['operations'][0]['reason'] = ' '
                if change == 'kind': record['operations'][0]['kinds'] = ['term-display']
                if change == 'operation': record['operations'] = []
                with self.assertRaises(DerivationError): replay_derivation(record, units, candidates)

    def test_tool_cannot_grant_terminology_approval(self):
        record, units, candidates = fixture()
        record['operations'][0]['candidate_updates']['unknown_terms'] = []
        with self.assertRaisesRegex(DerivationError, 'pending evidence'):
            replay_derivation(record, units, candidates)

    def test_absolute_parent_and_symlink_paths_are_rejected(self):
        for unsafe in ['/tmp/input.jsonl', 'translation-data/units/../test.jsonl', 'symlink']:
            with self.subTest(path=unsafe), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                record, manifest, _ = save_fixture(root)
                if unsafe == 'symlink':
                    path = root / record['files']['input_units']['path']
                    payload = path.read_bytes()
                    path.unlink()
                    target = root / 'saved.jsonl'
                    target.write_bytes(payload)
                    path.symlink_to(target)
                else:
                    record['files']['input_units']['path'] = unsafe
                    manifest.write_text(json.dumps(record))
                self.assertTrue(load_repository_derivations(root)[1])

    def test_orphaned_snapshot_and_unbacked_candidate_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, manifest, _ = save_fixture(root)
            manifest.unlink()
            errors = load_repository_derivations(root)[1]
            self.assertTrue(any('orphaned' in e for e in errors))
            self.assertTrue(any('no valid replay' in e for e in errors))

    def test_duplicate_active_file_and_wrong_filename_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, manifest, _ = save_fixture(root)
            other = manifest.with_name('other.json')
            other.write_bytes(manifest.read_bytes())
            self.assertTrue(any('filename' in e for e in load_repository_derivations(root)[1]))

    def test_duplicate_active_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, manifest, _ = save_fixture(root)
            other = copy.deepcopy(record)
            other['derivation_id'] = 'other'
            for role in ['input_units', 'input_candidates']:
                old_path = root / other['files'][role]['path']
                new_path = root / other['files'][role]['path'].replace('fixture-derive', 'other')
                new_path.parent.mkdir(parents=True, exist_ok=True)
                new_path.write_bytes(old_path.read_bytes())
                other['files'][role]['path'] = new_path.relative_to(root).as_posix()
            manifest.with_name('other.json').write_text(json.dumps(other))
            self.assertTrue(any('multiple derivations' in e for e in load_repository_derivations(root)[1]))

    def test_preview_discloses_tool_derivation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record, _, _ = save_fixture(root)
            lock = root / 'upstream.lock'
            lock.write_text(f'commit = "{COMMIT}"\n')
            output = root / 'preview'
            render_batch(root / record['files']['output_units']['path'],
                         root / record['files']['output_candidates']['path'], lock, output,
                         'fixture', 'Fixture')
            self.assertIn('工具派生修复记录', (output / 'metadata.tex').read_text())


if __name__ == '__main__':
    unittest.main()
