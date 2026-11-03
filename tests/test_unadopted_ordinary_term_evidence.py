"""Ordinary wording in independent locked Git; no model or adopted data."""
from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_source_containers import fixture, selector
from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_terms import source_inventory, source_tex_hash, validate_catalog_evidence


class UnadoptedOrdinaryEvidenceTests(unittest.TestCase):
    PROOF = '\\begin{proof}\nWe now begin the proof proper. The proper morphism exists.\n\\end{proof}'
    PROSE = 'A large number of properties.\n\nAnother paragraph with $x$.\n\n'

    def evidence(self, base, *, proof=None, prose=False):
        from test_source_containers import NAMED
        root, harvest, commit = fixture(base, proof=self.PROOF if proof is None else proof,
                                      statement=(self.PROSE if prose else '') + NAMED)
        native = Containers(root, harvest)
        coordinate = selector('prose_block', owner='0000') if prose else selector()
        selected = native.select(coordinate)
        row = lower_container(selected, native.policy)[0]
        use = dict(chapter='test', unit_id=row['unit_id'], source_term='large' if prose else 'proper',
                   source_tex_hash=source_tex_hash(row), occurrence_index=0, reason='Ordinary wording fixture.')
        catalog = dict(source_commit=commit, terms=[], nonmathematical_occurrences=[use])
        return root, harvest, catalog, row, coordinate

    def test_unadopted_proof_and_complete_multi_paragraph_block(self):
        for prose in [False, True]:
            with self.subTest(prose=prose), tempfile.TemporaryDirectory() as tmp:
                root, harvest, catalog, _, coordinate = self.evidence(Path(tmp), prose=prose)
                checks, errors = validate_catalog_evidence(root, catalog, [], harvest)
                self.assertEqual(errors, [])
                self.assertEqual(checks[0]['path'], 'locked-source-container')
                self.assertEqual(checks[0]['selector'], coordinate)
                self.assertEqual(checks[0]['status'], 'PASS')
                self.assertIn('fragment_hash', checks[0]['location'])

    def test_full_block_hash_cannot_be_replaced_by_first_paragraph_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, catalog, row, _ = self.evidence(Path(tmp), prose=True)
            native = Containers(root, harvest)
            short = native.select(selector('paragraph', owner='0000'))['inventory_unit']
            self.assertNotEqual(source_tex_hash(row), source_tex_hash(short))
            catalog['nonmathematical_occurrences'][0]['source_tex_hash'] = source_tex_hash(short)
            self.assertTrue(validate_catalog_evidence(root, catalog, [], harvest)[1])

    def test_exact_identity_commit_hash_word_and_occurrence_required(self):
        faults = [('unit_id', 'tag:0002:proof'), ('unit_id', 'tag:0001:proof-002'),
                  ('unit_id', 'tag:0001:paragraph-0001'), ('chapter', 'other'),
                  ('chapter', '../test'), ('source_tex_hash', 'sha256:' + '0' * 64),
                  ('source_term', 'Proper'), ('source_term', 'prop'),
                  ('occurrence_index', 2), ('occurrence_index', -1), ('occurrence_index', True)]
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, catalog, _, _ = self.evidence(Path(tmp))
            for field, value in faults:
                with self.subTest(field=field, value=value):
                    altered = copy.deepcopy(catalog)
                    altered['nonmathematical_occurrences'][0][field] = value
                    self.assertTrue(validate_catalog_evidence(root, altered, [], harvest)[1])
            altered = copy.deepcopy(catalog); altered['source_commit'] = '0' * 40
            with self.assertRaisesRegex(RecordError, 'different locked source commit'):
                validate_catalog_evidence(root, altered, [], harvest)

    def test_word_in_math_reference_or_comment_does_not_witness_prose(self):
        for body in ['Only $proper$.', 'Only \\ref{proper}.', 'Words.\n% proper']:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as tmp:
                root, harvest, catalog, _, _ = self.evidence(Path(tmp), proof='\\begin{proof}\n' + body + '\n\\end{proof}')
                self.assertTrue(validate_catalog_evidence(root, catalog, [], harvest)[1])

    def test_unknown_macro_remains_blocked_without_raw_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, catalog, _, _ = self.evidence(Path(tmp))
            # Rebuild the independent Git fixture, then use the previous expected
            # coordinate/hash. Selection must stop at the unknown macro itself.
            from test_source_containers import fixture as make_fixture
            other = Path(tmp) / 'other'; other.mkdir()
            changed_root, changed_harvest, commit = make_fixture(other,
                proof='\\begin{proof}\nA \\unclassified{proper}.\n\\end{proof}')
            catalog['source_commit'] = commit
            checks, errors = validate_catalog_evidence(changed_root, catalog, [], changed_harvest)
            self.assertTrue(any('blocked' in error for error in errors), errors)
            self.assertEqual(checks[0]['status'], 'FAIL')

    def test_current_path_is_exact_and_cannot_fall_back_after_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, catalog, row, _ = self.evidence(Path(tmp))
            checks, errors = validate_catalog_evidence(root, catalog, [row], harvest)
            self.assertEqual(errors, [])
            self.assertEqual(checks[0]['path'], 'current-unit')
            for fault in ['commit', 'hash', 'duplicate']:
                altered = copy.deepcopy(row)
                if fault == 'commit': altered['source_commit'] = '0' * 40
                if fault == 'hash': altered['source_text'] += ' Changed.'
                altered = stamp_unit_hashes(altered)
                rows = [altered, altered] if fault == 'duplicate' else [altered]
                with self.subTest(fault=fault):
                    self.assertTrue(validate_catalog_evidence(root, catalog, rows, harvest)[1])

    def test_two_same_words_have_exact_independent_indices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, catalog, _, _ = self.evidence(Path(tmp))
            second = copy.deepcopy(catalog['nonmathematical_occurrences'][0]); second['occurrence_index'] = 1
            catalog['nonmathematical_occurrences'].append(second)
            checks, errors = validate_catalog_evidence(root, catalog, [], harvest)
            self.assertEqual(errors, [])
            self.assertEqual([c['occurrence_index'] for c in checks], [0, 1])

    def test_ambiguous_canonical_coordinates_and_duplicate_real_anchors_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, catalog, _, coordinate = self.evidence(Path(tmp))
            entry = dict(selector=coordinate)
            with patch('stacks_zh.chapter_preflight._selectors', return_value=[entry, entry]):
                self.assertTrue(validate_catalog_evidence(root, catalog, [], harvest)[1])
            other = Path(tmp) / 'other'; other.mkdir()
            from test_source_containers import NAMED
            changed_root, changed_harvest, commit = fixture(other, proof=self.PROOF, other=NAMED)
            catalog['source_commit'] = commit
            self.assertTrue(validate_catalog_evidence(changed_root, catalog, [], changed_harvest)[1])

    def test_dirty_worktree_never_replaces_locked_git_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, catalog, _, _ = self.evidence(Path(tmp))
            (harvest / 'test.tex').write_text('Untrusted replacement.')
            (harvest / 'tags/tags').write_text('Untrusted tags.')
            self.assertEqual(validate_catalog_evidence(root, catalog, [], harvest)[1], [])

    def test_changed_policy_or_locked_source_during_selection_fails(self):
        for fault in ['policy', 'commit']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as tmp:
                root, harvest, catalog, _, _ = self.evidence(Path(tmp))
                native = Containers(root, harvest)
                original = native.select
                def changing(coordinate):
                    result = original(coordinate)
                    if fault == 'policy':
                        with (root / 'config/macro-policy.yml').open('a') as f: f.write('\n# Changed\n')
                    else:
                        (root / 'upstream.lock').write_text('commit = "' + '0' * 40 + '"\n')
                    return result
                with patch.object(native, 'select', side_effect=changing), self.assertRaises(RecordError):
                    validate_catalog_evidence(root, catalog, [], harvest, containers=native)

    def test_legacy_term_and_chapter_exemptions_do_not_gain_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, catalog, row, _ = self.evidence(Path(tmp))
            catalog['terms'] = [dict(id='proper', forms=['proper'], evidence=[dict(
                chapter='test', unit_id=row['unit_id'], source_term='proper', source_tex_hash=source_tex_hash(row))])]
            catalog['nonmathematical_chapters'] = [dict(chapter='test', title_evidence=dict(
                unit_id='tag:0000:title', source_title='Basics', source_tex_hash=source_tex_hash(row)))]
            _, errors = validate_catalog_evidence(root, catalog, [], harvest)
            self.assertTrue(any('catalog evidence is absent' in e for e in errors))
            self.assertTrue(any('title evidence' in e for e in errors))

    def test_another_id_cannot_borrow_an_identical_tex_ordinary_exception(self):
        from test_source_terms import unit, catalog
        row = unit('A category and another category.')
        scope = catalog(row)
        scope['nonmathematical_occurrences'] = [dict(chapter=row['chapter'], unit_id=row['unit_id'],
            source_term='category', source_tex_hash=source_tex_hash(row), occurrence_index=0)]
        self.assertEqual(len(source_inventory(row, scope)['occurrences']), 1)
        other = copy.deepcopy(row); other['unit_id'] = 'tag:DIFF:p001'; other = stamp_unit_hashes(other)
        self.assertEqual(source_tex_hash(other), source_tex_hash(row))
        self.assertEqual(len(source_inventory(other, scope)['occurrences']), 2)

    def test_unrelated_ordinary_record_does_not_restore_malformed_negative_fixture(self):
        from test_source_terms import unit, catalog
        row = unit('A category <TEXTCLOSE_0002>.')
        scope = catalog()
        scope['nonmathematical_occurrences'] = [dict(chapter=row['chapter'], unit_id='tag:DIFF:p001',
            source_term='category', source_tex_hash='sha256:' + '0' * 64, occurrence_index=0)]
        with patch('stacks_zh.source_terms.source_tex_hash', side_effect=AssertionError('unrelated restoration')):
            result = source_inventory(row, scope)
        self.assertEqual([x['source_term'] for x in result['occurrences']], ['category'])

    def test_matching_id_cannot_hide_broken_protected_structure(self):
        from test_source_terms import unit, catalog
        row = unit('A category <TEXTCLOSE_0002>.')
        scope = catalog()
        scope['nonmathematical_occurrences'] = [dict(chapter=row['chapter'], unit_id=row['unit_id'],
            source_term='category', source_tex_hash='sha256:' + '0' * 64, occurrence_index=0)]
        with self.assertRaises(KeyError):
            source_inventory(row, scope)


if __name__ == '__main__':
    unittest.main()
