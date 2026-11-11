"""Synthetic locked Git/source/model fixtures; no actual generation or approval."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_source_containers import fixture, selector
from test_source_adoptions import synthetic_fixture, write
from stacks_zh.records import RecordError, stamp_unit_hashes, write_jsonl
from stacks_zh.source_containers import (Containers, lower_container,
    canonical_proof_file_context, canonical_proof_file_mapping)
from stacks_zh.source_integrity import permanent_tag_mapping, audit_repository_source
from stacks_zh.source_reextractions import proof_groups, audit_repository_proofs, byte_hash
from stacks_zh.source_adoptions import assemble_source_adoption, load_repository_source_adoptions, fresh_source_corpus
from stacks_zh.source_alignment import align_batches


class CanonicalProofFileOwnershipTests(unittest.TestCase):
    def test_complete_first_and_second_proofs_use_real_owner_and_ordinal(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = fixture(Path(temp))
            native = Containers(root, harvest)
            for index in (1, 2):
                unit = lower_container(native.select(selector(ordinal=index)), native.policy)[0]
                with self.assertRaisesRegex(RecordError, 'no adjacent labelled statement'):
                    permanent_tag_mapping([unit], native.english.tags)
                padded = canonical_proof_file_context([unit], native.english.tags, native)
                self.assertGreater(len(padded), 1)
                self.assertEqual(canonical_proof_file_mapping([unit], native.english.tags, native),
                                 {unit['unit_id']: unit['unit_id']})
                groups, errors = proof_groups([unit], native.english.tags, native_containers=native)
                self.assertEqual(errors, [])
                self.assertEqual(groups[0]['selector']['proof_index'], index)
                self.assertEqual(groups[0]['units'], [unit])
                corpus, _ = fresh_source_corpus(root, harvest, 'test')
                matches, _ = align_batches({'proof': [unit]}, corpus)
                self.assertIn(matches[0]['status'], {'BYTE_EXACT', 'PRESENTATION_EQUIVALENT'})

    def test_tampered_bytes_parent_owner_and_ordinal_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = fixture(Path(temp))
            native = Containers(root, harvest)
            unit = lower_container(native.select(selector()), native.policy)[0]
            for field, value in [('source_text', unit['source_text'] + ' Extra.'),
                                 ('parent_tag', '0002'), ('unit_id', 'tag:0002:proof'),
                                 ('unit_id', 'tag:0001:proof-002'), ('source_commit', 'a' * 40)]:
                with self.subTest(field=field, value=value):
                    changed = copy.deepcopy(unit)
                    changed[field] = value
                    changed = stamp_unit_hashes(changed)
                    with self.assertRaises(RecordError):
                        canonical_proof_file_mapping([changed], native.english.tags, native)

    def test_incomplete_or_legacy_wrapper_cannot_borrow_native_context(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = fixture(Path(temp))
            native = Containers(root, harvest)
            unit = lower_container(native.select(selector()), native.policy)[0]
            for operation in ('legacy', 'partial', 'closing'):
                changed = copy.deepcopy(unit)
                if operation == 'legacy':
                    changed['unit_id'] = 'tag:0001:p001'
                elif operation == 'partial':
                    changed['source_text'] = changed['source_text'][:20]
                else:
                    changed['render']['suffix'] = ''
                changed = stamp_unit_hashes(changed)
                with self.assertRaises(RecordError):
                    canonical_proof_file_mapping([changed], native.english.tags, native)

    def test_missing_native_authority_keeps_the_original_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = fixture(Path(temp))
            native = Containers(root, harvest)
            unit = lower_container(native.select(selector()), native.policy)[0]
            with self.assertRaisesRegex(RecordError, 'no adjacent labelled statement'):
                canonical_proof_file_mapping([unit], native.english.tags)
            with self.assertRaisesRegex(RecordError, 'locked Git Tags'):
                canonical_proof_file_mapping([unit], {}, native)

    def test_duplicate_and_reordered_batch_units_cannot_borrow_context(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = fixture(Path(temp))
            native = Containers(root, harvest)
            first = lower_container(native.select(selector()), native.policy)[0]
            second = lower_container(native.select(selector(ordinal=2)), native.policy)[0]
            statement_selector = {**selector(), 'kind': 'lemma'}
            statement = lower_container(native.select(statement_selector), native.policy)[0]
            for units in ([first, first], [second, first], [first, statement]):
                with self.subTest(ids=[u['unit_id'] for u in units]):
                    with self.assertRaisesRegex(RecordError, 'duplicate|reorder'):
                        canonical_proof_file_mapping(units, native.english.tags, native)

    def test_later_proof_cannot_inherit_an_unverified_temporary_owner(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = fixture(Path(temp))
            native = Containers(root, harvest)
            first = lower_container(native.select(selector()), native.policy)[0]
            second = lower_container(native.select(selector(ordinal=2)), native.policy)[0]
            expected = {u['unit_id']: u['unit_id'] for u in (first, second)}
            self.assertEqual(canonical_proof_file_mapping([first, second], native.english.tags, native), expected)
            for field, value in [('source_text', second['source_text'] + ' Extra.'),
                                 ('unit_id', 'tag:0001:p002')]:
                changed = copy.deepcopy(second)
                changed[field] = value
                changed = stamp_unit_hashes(changed)
                with self.subTest(field=field):
                    with self.assertRaisesRegex(RecordError, 'complete canonical Git lowering'):
                        canonical_proof_file_mapping([first, changed], native.english.tags, native)

    def test_public_first_adoption_replay_and_audits_keep_the_other_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, first, _ = synthetic_fixture(Path(temp), typed=False)
            assemble_source_adoption(root, fp, [rp], harvest)
            original = {b['candidates_path']: (root / b['candidates_path']).read_bytes()
                        for b in first['batches']}
            native = Containers(root, harvest)
            selected = native.select(selector())
            unit = lower_container(selected, native.policy)[0]
            fresh = copy.deepcopy(first)
            aid = 'synthetic-complete-proof'
            up = 'translation-data/units/test-complete-proof.jsonl'
            cp = 'translation-data/candidates/synthetic/test-complete-proof.jsonl'
            fp2 = root / f'translation-data/source-adoption-inputs/{aid}.json'
            rp2 = root / f'docs/evidence/{aid}-raw.jsonl'
            fresh.update(adoption_id=aid, run_id='run-' + aid, unit_ids=[unit['unit_id']],
                         created_at='2026-10-20T00:00:00Z',
                         batches=[dict(units_path=up, candidates_path=cp, units=[unit],
                             containers=[dict(selector=selected['selector'], selected=selected,
                                              unit_ids=[unit['unit_id']])], prior_attempts=[])])
            scope_path = f'task-scopes/{aid}.json'
            paths = [scope_path, up, cp, fp2.relative_to(root).as_posix(),
                     rp2.relative_to(root).as_posix(), f'translation-data/runs/run-{aid}.json',
                     f'translation-data/source-adoptions/{aid}.json']
            scope = json.loads(first['task']['scope_bytes'])
            scope['allowed_write_files'] = paths
            child = scope['data_scopes'][0]
            child.update(unit_ids=[unit['unit_id']], input_unit_ids=[unit['unit_id']],
                         output_unit_ids=[unit['unit_id']], allowed_write_files=paths[1:],
                         run_scope=['run-' + aid])
            write(root / scope_path, scope)
            fresh['task'].update(scope_manifest=scope_path,
                scope_manifest_sha256=byte_hash((root / scope_path).read_bytes()),
                scope_bytes=(root / scope_path).read_text())
            write(fp2, fresh)
            write_jsonl(root / up, [unit])
            raw = dict(unit_id=unit['unit_id'],
                translation='合成使用 <MATHSEG_0001>且<MATHSEG_0002>。', allowed_english=[],
                term_occurrences=[], unknown_terms=[], notes=['Literal synthetic model fixture.'])
            write_jsonl(rp2, [raw])
            assemble_source_adoption(root, fp2, [rp2], harvest)
            self.assertTrue((root / cp).is_file())
            self.assertEqual(original, {p: (root / p).read_bytes() for p in original})
            _, errors = load_repository_source_adoptions(root, harvest)
            self.assertEqual(errors, [])
            _, errors = audit_repository_source(root, harvest / 'tags/tags')
            self.assertEqual(errors, [])
            report, errors = audit_repository_proofs(root, harvest)
            self.assertEqual(errors, [])
            self.assertEqual(report['matched'], 1)


if __name__ == '__main__':
    unittest.main()
