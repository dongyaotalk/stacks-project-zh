from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stacks_zh.records import RecordError, restore_placeholders, stamp_unit_hashes, validate_tex_controls
from stacks_zh.source_integrity import (
    audit_repository_source, environment_title_errors, expose_environment_title,
    expand_fixed_footnotes, hidden_footnote_errors, load_tags, permanent_tag_mapping,
    protect_fragments, require_audit_output,
)
from stacks_zh.workflow import render_batch

COMMIT = 'b' * 40
ROOT = Path(__file__).resolve().parents[1]


def unit(uid='tag:SECT:statement', kind='lemma', prefix='\\begin{lemma}\n\\label{lemma-test}\n', suffix='\n\\end{lemma}\n'):
    return stamp_unit_hashes({'schema_version': 1, 'unit_id': uid, 'chapter': 'test',
        'parent_tag': 'SECT', 'node_kind': kind, 'risk_level': 'R3', 'source_commit': COMMIT,
        'source_status': 'CURRENT', 'source_text': 'Source.', 'placeholders': {},
        'render': {'prefix': prefix, 'suffix': suffix}})


class SourceIntegrityTests(unittest.TestCase):
    def test_existing_separate_environment_titles_keep_their_source_and_ownership(self):
        title = unit('tag:OWN1:title', 'environment_title', '\\begin{remark}[', ']\n\\label{remark-test}\n')
        title['source_text'] = 'Construction of <MATH_0001> obstruction class'
        title['placeholders'] = {'MATH_0001': r'$x\label{equation-test}$'}
        title = stamp_unit_hashes(title)
        body = unit('tag:OWN1:p001', 'paragraph', '', '\n\\end{remark}\n')
        proof = unit('tag:OWN1:proof-p001', 'proof', '\\begin{proof}\n', '\n\\end{proof}\n')
        before = copy.deepcopy(title)
        self.assertEqual(environment_title_errors(title), [])
        self.assertEqual(expose_environment_title(title), before)
        self.assertEqual(title, before)
        mapping = permanent_tag_mapping([title, body, proof], {'test-remark-test': 'OWN1', 'test-equation-test': 'EQ01'})
        self.assertEqual(mapping, {row['unit_id']: row['unit_id'] for row in [title, body, proof]})
        title['render']['suffix'] = ']\n$x\\label{equation-test}$\n'
        self.assertTrue(environment_title_errors(title))

    def test_named_title_extraction_preserves_source_bytes_and_inputs(self):
        from stacks_zh.source_terms import source_projection, source_tex_hash
        for title, environment in [('Yoneda lemma', 'lemma'), ('Adjoint functor theorem', 'theorem')]:
            with self.subTest(title=title):
                row = unit(kind=environment, prefix=f'\\begin{{{environment}}}[{title}]\n\\label{{lemma-test}}\n')
                before = copy.deepcopy(row)
                self.assertEqual(len(environment_title_errors(row)), 1)
                extracted = expose_environment_title(row)
                self.assertEqual(row, before)
                self.assertEqual(source_tex_hash(extracted), source_tex_hash(row))
                self.assertEqual(extracted['unit_id'], row['unit_id'])
                self.assertEqual(extracted['source_math_hash'], row['source_math_hash'])
                self.assertTrue(source_projection(extracted)[0].startswith(title))
                self.assertEqual(environment_title_errors(extracted), [])
                self.assertEqual(expose_environment_title(extracted), extracted)

    def test_named_title_and_body_have_separate_source_term_occurrences(self):
        from stacks_zh.source_terms import source_inventory, source_tex_hash, validate_source_terms
        row = unit(prefix='\\begin{lemma}[Yoneda lemma]\n\\label{lemma-test}\n')
        row['source_text'] = 'Use the Yoneda lemma.'
        row = expose_environment_title(stamp_unit_hashes(row))
        catalog = {'schema_version': 1, 'source_commit': COMMIT, 'nonmathematical_declarations': {},
                   'terms': [{'id': 'yoneda-lemma', 'forms': ['yoneda lemma'], 'chapters': [],
                              'evidence': [{'chapter': 'test', 'unit_id': row['unit_id'],
                                            'source_term': 'Yoneda lemma', 'source_tex_hash': source_tex_hash(row)}]}]}
        self.assertEqual([item['source_term'] for item in source_inventory(row, catalog)['occurrences']], ['Yoneda lemma'] * 2)
        term = {'source_term': 'Yoneda lemma', 'target_term': '米田引理'}
        candidate = {'unit_id': row['unit_id'], 'translation': '米田引理（Yoneda lemma）<ENVARGEND_0001>使用米田引理（Yoneda lemma）。',
                     'term_occurrences': [term] * 2, 'unknown_terms': [{**term, 'context': 'Synthetic pending'}] * 2,
                     'term_status': 'DECISION_REQUIRED'}
        self.assertEqual(validate_source_terms(row, candidate, catalog), [])
        candidate['term_occurrences'].pop()
        self.assertTrue(validate_source_terms(row, candidate, catalog))

    def test_extracted_own_label_controls_proof_and_ignores_nested_labels(self):
        row = unit(prefix='\\begin{lemma}[Yoneda lemma]\n\\label{lemma-test}\n')
        row['source_text'] = 'Source <MATH_0001>.'
        row['placeholders']['MATH_0001'] = r'$x\label{equation-test}$'
        row = expose_environment_title(stamp_unit_hashes(row))
        proof = unit('tag:SECT:proof-p001', 'proof', '\\begin{proof}\n', '\n\\end{proof}\n')
        tags = {'test-lemma-test': 'OWN1', 'test-equation-test': 'EQ01'}
        mapping = permanent_tag_mapping([row, proof], tags)
        self.assertEqual(mapping[row['unit_id']], 'tag:OWN1:statement')
        self.assertEqual(mapping[proof['unit_id']], 'tag:OWN1:proof-p001')
        with self.assertRaisesRegex(RecordError, 'no permanent Tag'):
            permanent_tag_mapping([row], {'test-equation-test': 'EQ01'})
        row['render']['suffix'] += '\\label{second}\n'
        with self.assertRaisesRegex(RecordError, 'multiple permanent Tags'):
            permanent_tag_mapping([row], {**tags, 'test-second': 'OWN2'})

    def test_missing_moved_duplicate_and_forged_title_boundaries_fail(self):
        for fault in ['missing', 'moved', 'duplicate', 'fake-prefix', 'nested-label', 'wrong-kind', 'extra-token', 'missing-payload', 'orphan-token']:
            with self.subTest(fault=fault):
                row = expose_environment_title(unit(prefix='\\begin{lemma}[Yoneda lemma]\n\\label{lemma-test}\n'))
                if fault == 'missing': row['source_text'] = row['source_text'].replace('<ENVARGEND_0001>', '')
                if fault == 'moved': row['source_text'] = 'Source.<ENVARGEND_0001>Yoneda lemma'
                if fault == 'duplicate': row['source_text'] += '<ENVARGEND_0001>'
                if fault == 'fake-prefix': row['render']['prefix'] = '\\begin{lemma}\n'
                if fault == 'nested-label': row['placeholders']['ENVARGEND_0001'] = ']\n$x\\label{equation-test}$\n'
                if fault == 'wrong-kind': row['node_kind'] = 'display_math'
                if fault == 'extra-token': row['placeholders']['ENVARGEND_0002'] = ']'
                if fault == 'missing-payload': row['placeholders'].pop('ENVARGEND_0001')
                if fault == 'orphan-token':
                    row['placeholders'].pop('ENVARGEND_0001'); row['render']['prefix'] = '\\begin{lemma}\n'
                self.assertTrue(environment_title_errors(row))
                with self.assertRaises(RecordError):
                    permanent_tag_mapping([row], {'test-lemma-test': 'OWN1', 'test-equation-test': 'EQ01'})

    def test_complex_or_ambiguous_named_wrappers_require_explicit_extraction(self):
        for title in [r'Yoneda $x$', r'\emph{Yoneda lemma}', 'Nested [title]', '', 'Leading. sentence']:
            with self.subTest(title=title):
                row = unit(prefix=f'\\begin{{lemma}}[{title}]\n\\label{{lemma-test}}\n')
                self.assertTrue(environment_title_errors(row))
                with self.assertRaisesRegex(RecordError, 'explicit extraction'):
                    expose_environment_title(row)
        for prefix in ['\\begin{unknown}[Title]\n\\label{lemma-test}\n',
                       '\\begin{lemma}[Title]\n',
                       '\\begin{lemma}[Title]\n\\label{first}\n\\label{second}\n',
                       '\\begin{proof}\n\\begin{lemma}[Title]\n\\label{lemma-test}\n']:
            with self.subTest(prefix=prefix), self.assertRaisesRegex(RecordError, 'explicit extraction'):
                expose_environment_title(unit(prefix=prefix))

    def test_source_audit_counts_hidden_titles_and_accepts_exposed_ones(self):
        from stacks_zh.records import write_jsonl
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); path = root / 'translation-data/units/test.jsonl'
            row = unit('tag:OWN1:statement', prefix='\\begin{lemma}[Yoneda lemma]\n\\label{lemma-test}\n')
            write_jsonl(path, [row]); (root / 'upstream.lock').write_text(f'commit = "{COMMIT}"\n')
            tags = root / 'tags'; tags.write_text('OWN1,test-lemma-test\n')
            report, errors = audit_repository_source(root, tags)
            self.assertEqual(report['hidden_environment_titles'], 1)
            self.assertTrue(any('hidden in render.prefix' in error for error in errors))
            write_jsonl(path, [expose_environment_title(row)])
            report, errors = audit_repository_source(root, tags)
            self.assertEqual(errors, []); self.assertEqual(report['hidden_environment_titles'], 0)

    def test_render_restores_translated_named_argument_and_original_own_label(self):
        from test_workflow import make_batch_candidate
        from stacks_zh.records import write_jsonl
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            row = expose_environment_title(unit('tag:OWN1:statement', prefix='\\begin{lemma}[Yoneda lemma]\n\\label{lemma-test}\n'))
            candidate = make_batch_candidate(row)
            candidate['translation'] = '米田引理（Yoneda lemma）<ENVARGEND_0001>正文。'
            candidate['term_occurrences'] = [{'source_term': 'Yoneda lemma', 'target_term': '米田引理'}]
            candidate['unknown_terms'] = [{'source_term': 'Yoneda lemma', 'target_term': '米田引理', 'context': 'Synthetic pending'}]
            candidate.update(term_status='DECISION_REQUIRED', stage='STRUCTURE_OK')
            units, candidates = root / 'units.jsonl', root / 'candidates.jsonl'
            write_jsonl(units, [row]); write_jsonl(candidates, [candidate])
            lock = root / 'upstream.lock'; lock.write_text(f'commit = "{COMMIT}"\n')
            render_batch(units, candidates, lock, root / 'preview', 'test', 'Fixture')
            tex = (root / 'preview/chapters/test.tex').read_text()
            self.assertIn('\\begin{lemma}[米田引理（Yoneda lemma）]\n\\label{lemma-test}\n正文。', tex)
            self.assertIn('\\end{lemma}', tex)

    def test_statement_and_its_proof_get_own_permanent_tag(self):
        statement = unit()
        proof = unit('tag:SECT:proof-p001', 'proof', '\\begin{proof}\n', '\n\\end{proof}\n')
        self.assertEqual(permanent_tag_mapping([statement, proof], {'test-lemma-test': 'OWN1'}),
                         {'tag:SECT:statement': 'tag:OWN1:statement', 'tag:SECT:proof-p001': 'tag:OWN1:proof-p001'})

    def test_own_label_not_nested_equation_gives_statement_identity(self):
        row = unit()
        row['placeholders'] = {'LABEL_0001': '\\label{equation-test}'}
        row['source_text'] = 'Source <LABEL_0001>.'
        self.assertEqual(permanent_tag_mapping([row], {'test-lemma-test': 'OWN1', 'test-equation-test': 'EQ01'})[row['unit_id']], 'tag:OWN1:statement')

    def test_fragmented_statement_preserves_owner_across_list_and_display(self):
        statement = unit(suffix='\n\\begin{enumerate}\n')
        child = unit('tag:SECT:item001', 'list_item', '\\item ', '\n\\end{enumerate}\n\\end{lemma}\n')
        proof = unit('tag:SECT:proof-p001', 'proof', '\\begin{proof}\n', '\n\\end{proof}\n')
        mapping = permanent_tag_mapping([statement, child, proof], {'test-lemma-test': 'OWN1'})
        self.assertEqual(mapping[proof['unit_id']], 'tag:OWN1:proof-p001')
        self.assertEqual(mapping[child['unit_id']], 'tag:OWN1:item001')

    def test_proof_cannot_inherit_owner_from_another_chapter_or_parent(self):
        for field in ['chapter', 'parent_tag']:
            with self.subTest(field=field):
                proof = unit('tag:SECT:proof-p001', 'proof', '\\begin{proof}\n', '\n\\end{proof}\n')
                proof[field] = 'OTHER'
                with self.assertRaisesRegex(RecordError, 'crosses'):
                    permanent_tag_mapping([unit(), proof], {'test-lemma-test': 'OWN1'})

    def test_every_proof_child_inherits_the_statement_tag(self):
        rows = [unit(), unit('tag:SECT:proof-p001', 'proof', '\\begin{proof}\n', '\n')]
        for index, kind in enumerate(['list_item', 'display_math', 'proof_paragraph', 'paragraph']):
            rows.append(unit(f'tag:SECT:proof-child{index}', kind, '', '\n'))
        rows.append(unit('tag:SECT:proof-last', 'proof_paragraph', '', '\n\\end{proof}\n'))
        mapping = permanent_tag_mapping(rows, {'test-lemma-test': 'OWN1'})
        for row in rows:
            self.assertEqual(mapping[row['unit_id']], row['unit_id'].replace('tag:SECT:', 'tag:OWN1:'))

    def test_proof_child_scope_and_own_label_are_checked(self):
        opening = unit('tag:SECT:proof-p001', 'proof', '\\begin{proof}\n', '\n')
        child = unit('tag:SECT:proof-item', 'list_item', '', '\n\\end{proof}\n')
        for field in ['chapter', 'parent_tag']:
            with self.subTest(field=field):
                foreign = copy.deepcopy(child)
                foreign[field] = 'OTHER'
                with self.assertRaisesRegex(RecordError, 'crosses'):
                    permanent_tag_mapping([unit(), opening, foreign], {'test-lemma-test': 'OWN1'})
        child['render']['prefix'] = '\\item\\label{item-test}\n'
        child['parent_tag'] = 'ITEM'
        mapping = permanent_tag_mapping([unit(), opening, child], {'test-lemma-test': 'OWN1', 'test-item-test': 'ITEM'})
        self.assertEqual(mapping[child['unit_id']], 'tag:ITEM:proof-item')

    def test_proof_wrappers_on_nonproof_nodes_open_and_close_ownership(self):
        opening = unit('tag:SECT:proof-item', 'list_item', '\\begin{proof}\n\\item ', '\n\\end{proof}\n')
        paragraph = unit('tag:SECT:p002', 'paragraph', '', '\n')
        mapping = permanent_tag_mapping([unit(), opening, paragraph], {'test-lemma-test': 'OWN1'})
        self.assertEqual(mapping[opening['unit_id']], 'tag:OWN1:proof-item')
        self.assertEqual(mapping[paragraph['unit_id']], paragraph['unit_id'])
        another_proof = unit('tag:SECT:proof-second', 'proof', '\\begin{proof}\n', '\n\\end{proof}\n')
        with self.assertRaisesRegex(RecordError, 'no adjacent'):
            permanent_tag_mapping([unit(), opening, paragraph, another_proof], {'test-lemma-test': 'OWN1'})

    def test_statement_wrapper_around_slogan_can_own_proof(self):
        slogan = unit('tag:OWN1:slogan', 'slogan', '\\begin{lemma}\n\\label{lemma-test}\n\\begin{slogan}\n', '\n\\end{slogan}\n')
        body = unit('tag:OWN1:statement', 'lemma', '', '\n\\end{lemma}\n')
        proof = unit('tag:OWN1:proof-p001', 'proof', '\\begin{proof}\n', '\n\\end{proof}\n')
        self.assertEqual(permanent_tag_mapping([slogan, body, proof], {'test-lemma-test': 'OWN1'})[proof['unit_id']], proof['unit_id'])

    def test_statement_child_with_own_tag_is_not_remapped_to_its_parent(self):
        statement = unit(suffix='\n\\begin{enumerate}\n')
        child = unit('tag:ITEM:item001', 'list_item', '\\item\\label{item-test}\n', '\n\\end{enumerate}\n\\end{lemma}\n')
        child['parent_tag'] = 'ITEM'
        mapping = permanent_tag_mapping([statement, child], {'test-lemma-test': 'OWN1', 'test-item-test': 'ITEM'})
        self.assertEqual(mapping[child['unit_id']], child['unit_id'])

    def test_bare_tag_and_legacy_label_children_keep_semantic_suffix(self):
        row = unit('tag:OWN1', 'paragraph', '', '\n')
        self.assertEqual(permanent_tag_mapping([row], {}), {'tag:OWN1': 'tag:OWN1'})
        legacy = unit('label:test-lemma-test:intro', 'paragraph', '', '\n')
        self.assertEqual(permanent_tag_mapping([legacy], {'test-lemma-test': 'OWN1'})[legacy['unit_id']], 'tag:OWN1:intro')

    def test_unknown_owned_label_and_multiple_owned_tags_fail(self):
        with self.assertRaisesRegex(RecordError, 'no permanent Tag'):
            permanent_tag_mapping([unit()], {})
        row = unit(prefix='\\begin{lemma}\n\\label{first}\n\\label{second}\n')
        with self.assertRaisesRegex(RecordError, 'multiple permanent Tags'):
            permanent_tag_mapping([row], {'test-first': 'OWN1', 'test-second': 'OWN2'})

    def test_orphan_or_nonadjacent_proof_fails(self):
        proof = unit('tag:OWN1:proof-p001', 'proof', '\\begin{proof}\n', '\n\\end{proof}\n')
        with self.assertRaisesRegex(RecordError, 'no adjacent'):
            permanent_tag_mapping([proof], {})
        paragraph = unit('tag:SECT:p001', 'paragraph', '', '\n')
        with self.assertRaisesRegex(RecordError, 'no adjacent'):
            permanent_tag_mapping([unit(), paragraph, proof], {'test-lemma-test': 'OWN1'})

    def test_duplicate_output_coordinate_fails(self):
        one, two = unit('tag:OLD1:statement'), unit('tag:OLD2:statement')
        with self.assertRaisesRegex(RecordError, 'duplicate'):
            permanent_tag_mapping([one, two], {'test-lemma-test': 'OWN1'})

    def test_all_unprotected_tex_controls_fail_in_source_or_translation(self):
        for control in ['%', '{', '}', '#', '&', '_', '^', '~', '$', '\\ ', '\\\\', '\\ref{x}']:
            with self.subTest(control=control):
                row = unit()
                self.assertTrue(validate_tex_controls(row, {'translation': control + '译文。'}))
                row['source_text'] = control + 'Source.'
                self.assertTrue(validate_tex_controls(row, {'translation': '译文。'}))

    def test_protected_control_symbols_are_legal(self):
        row = unit()
        row['source_text'] = 'A <SPACE_0001> B <PERCENT_0001>.'
        row['placeholders'] = {'SPACE_0001': '\\ ', 'PERCENT_0001': '\\%'}
        self.assertEqual(validate_tex_controls(row, {'translation': '甲<SPACE_0001>乙<PERCENT_0001>。'}), [])

    def test_fixed_footnote_exposes_prose_and_reference_with_source_unchanged(self):
        row = unit()
        row['source_text'] = 'Source<FOOTNOTE_0001>.'
        row['placeholders'] = {'FOOTNOTE_0001': '\\footnote{See Remark \\ref{remark-test}.}'}
        candidate = {'translation': '正文<FOOTNOTE_0001>。'}
        original = copy.deepcopy((row, candidate))
        derived, translated = expand_fixed_footnotes(row, candidate)
        self.assertEqual((row, candidate), original)
        self.assertEqual(restore_placeholders(row, row['source_text']), restore_placeholders(derived, derived['source_text']))
        self.assertIn('See Remark', derived['source_text'])
        self.assertIn('见注', translated['translation'])
        self.assertFalse(hidden_footnote_errors(derived))
        self.assertTrue(any(v == '\\ref{remark-test}' for v in derived['placeholders'].values()))

    def test_expanded_footnote_render_uses_translated_qualified_target(self):
        from test_workflow import make_batch_candidate, make_batch_unit
        from stacks_zh.records import write_jsonl
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            row = make_batch_unit('tag:OWN1:p001')
            row['source_text'] = 'Source<FOOTNOTE_0001>.'
            row['placeholders'] = {'FOOTNOTE_0001': r'\footnote{See Remark \ref{remark-test}.}'}
            row = stamp_unit_hashes(row)
            candidate = make_batch_candidate(row)
            candidate['translation'] = '正文<FOOTNOTE_0001>。'
            derived, translated = expand_fixed_footnotes(row, candidate)
            translated['source_text_hash'] = derived['source_text_hash']
            target = make_batch_unit('tag:OWN2:p001')
            target['render']['prefix'] = r'\label{test-remark-test}' + '\n'
            target = stamp_unit_hashes(target)
            unit_path, candidate_path = root / 'units.jsonl', root / 'candidates.jsonl'
            write_jsonl(unit_path, [derived, target])
            write_jsonl(candidate_path, [translated, make_batch_candidate(target)])
            lock = root / 'upstream.lock'
            lock.write_text(f'commit = "{COMMIT}"\n')
            tags = root / 'tags'
            tags.write_text('OWN2,test-remark-test\n')
            render_batch(unit_path, candidate_path, lock, root / 'preview', 'test', 'Test', tags_path=tags)
            tex = (root / 'preview/chapters/test.tex').read_text()
            self.assertIn(r'\footnote{见注 \ref{test-remark-test}.}', tex)
            self.assertNotIn('See Remark', tex)
            self.assertNotIn('待译', tex)

    def test_nonfixed_hidden_footnote_requires_translation_task(self):
        row = unit()
        row['source_text'] = 'Source<FOOTNOTE_0001>.'
        row['placeholders'] = {'FOOTNOTE_0001': '\\footnote{This is substantial prose.}'}
        self.assertTrue(hidden_footnote_errors(row))
        with self.assertRaisesRegex(RecordError, 'explicit translation task'):
            expand_fixed_footnotes(row, {'translation': '正文<FOOTNOTE_0001>。'})

    def test_explicit_protection_spans_keep_tex_and_translated_prose(self):
        row = unit()
        row['source_text'] = 'A {word}.'
        candidate = {'translation': '一个词。'}
        fragments = [
            {'source_start': 2, 'source_end': 3, 'target_start': 2, 'target_end': 2,
             'source_literal': '{', 'target_literal': '', 'placeholder': 'GROUP_0001'},
            {'source_start': 7, 'source_end': 8, 'target_start': 3, 'target_end': 3,
             'source_literal': '}', 'target_literal': '', 'placeholder': 'GROUP_0002'},
        ]
        derived, translated = protect_fragments(row, candidate, fragments)
        self.assertEqual(restore_placeholders(derived, derived['source_text']), row['source_text'])
        self.assertEqual(restore_placeholders(derived, translated['translation']), '一个{词}。')
        self.assertEqual(validate_tex_controls(derived, translated), [])

    def test_span_tampering_overlap_and_hiding_chinese_fail(self):
        row = unit()
        row['source_text'] = 'A {word}.'
        candidate = {'translation': '一个词。'}
        fragment = {'source_start': 2, 'source_end': 3, 'target_start': 2, 'target_end': 2,
                    'source_literal': '{', 'target_literal': '', 'placeholder': 'GROUP_0001'}
        wrong = dict(fragment, source_literal='}')
        with self.assertRaisesRegex(RecordError, 'declared input'):
            protect_fragments(row, candidate, [wrong])
        hidden = dict(fragment, target_end=3, target_literal='词')
        with self.assertRaisesRegex(RecordError, 'natural language'):
            protect_fragments(row, candidate, [hidden])
        with self.assertRaisesRegex(RecordError, 'overlap'):
            protect_fragments(row, candidate, [fragment, dict(fragment, placeholder='GROUP_0002')])

    def test_audit_output_cannot_overwrite_facts_or_history(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for path in ['translation-data/units/test.jsonl', 'README.md', 'migration/unit-id-map.json', 'upstream.lock']:
                with self.assertRaises(RecordError): require_audit_output(root, root / path)
            require_audit_output(root, root / 'build/audit.json')

    def test_tag_reader_rejects_conflicts(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'tags'
            path.write_text('OWN1,test-label\nOWN2,test-label\n')
            with self.assertRaisesRegex(RecordError, 'conflicting'):
                load_tags(path)

    def test_legacy_migration_is_read_only_even_when_source_has_defects(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'translation-data/units').mkdir(parents=True)
            (root / 'translation-data/runs').mkdir()
            record_path = root / 'translation-data/units/test.jsonl'
            record_path.write_text(json.dumps(unit()) + '\n')
            run = root / 'translation-data/runs/original.json'
            run.write_bytes(b'{"original":true}\n')
            (root / 'upstream.lock').write_text(f'commit = "{COMMIT}"\n')
            tags = root / 'tags'
            tags.write_text('OWN1,test-lemma-test\n')
            before = record_path.read_bytes(), run.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/migrate_permanent_tags.py'), '--root', str(root), '--tags', str(tags), '--map', str(root / 'build/map.json')], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual((record_path.read_bytes(), run.read_bytes()), before)
            self.assertEqual(json.loads((root / 'build/map.json').read_text())['count'], 1)


if __name__ == '__main__':
    unittest.main()
