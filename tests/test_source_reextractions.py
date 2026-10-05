"""Synthetic Git repositories only; none of these rows are real model runs."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_derivations import fixture
from test_derivation_archives import commit, git, save_rows
from test_model_corrections import read, write, save_decisions
from stacks_zh.cli import main
from stacks_zh.decisions import validate_repository_decisions
from stacks_zh.derivations import CANDIDATE_FIELDS, clean, load_repository_derivations, replay_derivation
from stacks_zh.model_corrections import candidate_provenance_hash, load_repository_corrections
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import RecordError, load_jsonl, sha256_value, stamp_unit_hashes
from stacks_zh.schema_validation import validate_repository_schemas
from stacks_zh.source_reextractions import (LockedEnglish, UnsupportedSource, audit_repository_proofs,
    byte_hash, extract_plain_proof, load_source_reextractions, proof_groups, source_tex)
from stacks_zh.workflow import render_batch

PROOF = '\\begin{proof}\nTake $x$ and define $s$.\n\\end{proof}'
SELECTOR = {'file': 'test.tex', 'statement_tag': 'NEW1', 'statement_label': 'lemma-one', 'kind': 'proof', 'proof_index': 1}


def synthetic_fixture(base, revisions=1, restoration=1):
    root, harvest = base / 'chinese', base / 'locked-english'
    root.mkdir(); harvest.mkdir()
    write(harvest / 'fixture-note.json', {'synthetic': True})
    (harvest / 'test.tex').write_text('\\begin{document}\n\\begin{lemma}\n\\label{lemma-one}\nA category.\n\\end{lemma}\n' + PROOF +
        '\n\\begin{lemma}\n\\label{lemma-two}\nAnother category.\n\\end{lemma}\n' + PROOF + '\n\\end{document}\n')
    (harvest / 'tags').mkdir()
    (harvest / 'tags/tags').write_text('NEW1,test-lemma-one\nNEW2,test-lemma-two\n')
    git(harvest, 'init', '-q'); source_commit = commit(harvest)
    record, template_units, template_candidates = fixture()
    record['source_commit'] = source_commit
    statement = stamp_unit_hashes({**template_units[0], 'unit_id': 'tag:NEW1:statement', 'parent_tag': 'NEW1',
        'source_commit': source_commit, 'node_kind': 'lemma',
        'render': {'prefix': '\\begin{lemma}\n\\label{test-lemma-one}\n', 'suffix': '\n\\end{lemma}'}})
    proof = stamp_unit_hashes({**statement, 'unit_id': 'tag:NEW1:proof-p001', 'node_kind': 'proof',
        'source_text': '\nTake <MATH_0001> and define.\n', 'placeholders': {'MATH_0001': '$x$'},
        'render': {'prefix': r'\begin{proof}', 'suffix': r'\end{proof}'}})
    units, candidates = [statement, proof], []
    for unit in units:
        row = copy.deepcopy(template_candidates[0])
        context = {'unit_id': unit['unit_id'], 'prompt_version': 'fixture', 'policy_revision': 'fixture', 'source_commit': source_commit}
        row.update(unit_id=unit['unit_id'], source_commit=source_commit, source_text_hash=unit['source_text_hash'],
                   context=context, context_hash=sha256_value(context), translation='一个范畴。' if unit['node_kind'] == 'lemma' else '<MATH_0001>。')
        row['translation_hash'] = sha256_value(row['translation'])
        candidates.append(row)
    for role, rows in [('output_units', units), ('output_candidates', candidates)]:
        record['files'][role] = save_rows(root, record['files'][role]['path'], rows)
    run = {'schema_version': 1, 'run_id': 'fixture-run', 'run_kind': 'translation', 'task_id': 'synthetic-fixture',
        'source_commit': source_commit, 'unit_ids': [u['unit_id'] for u in units],
        'harness': {'id': 'fixture', 'version': 'fixture', 'adapter_version': 'fixture'},
        'model': {'record_id': 'fixture:model:declared', 'provider': 'Fixture', 'requested_id': 'fixture-model',
                  'resolved_id': 'fixture-model', 'snapshot': None, 'identity_confidence': 'declared'},
        'inputs': {'prompt_version': 'fixture', 'policy_revision': 'fixture', 'glossary_revision': 'fixture',
                   'context_hashes': [row['context_hash'] for row in candidates]},
        'created_at': candidates[0]['created_at'], 'replayable': False}
    write(root / 'translation-data/runs/fixture-run.json', run)
    (root / 'upstream.lock').write_text(f'commit = "{source_commit}"\n')
    git(root, 'init', '-q'); commit(root)
    records = []
    for number in range(1, revisions + 1):
        old_units, old_candidates = units, candidates
        previous = copy.deepcopy(record)
        record = copy.deepcopy(previous)
        identifier = f'fixture-derive-{number}'
        record.update(derivation_id=identifier, origin_commit=git(root, 'rev-parse', 'HEAD'), created_at=f'2026-10-05T0{number}:00:00Z')
        record['tool']['version'] = '2' if number == 1 else '3'
        if number > 1:
            record['previous_derivation_id'] = previous['derivation_id']
            manifest = {'schema_version': 1, 'prior_derivation_id': previous['derivation_id'],
                'successor_derivation_id': identifier, 'source_commit': source_commit, 'origin_commit': record['origin_commit'],
                'created_at': record['created_at'], 'record': {'path': f"translation-data/derivations/{previous['derivation_id']}.json",
                    'hash': byte_hash((root / f"translation-data/derivations/{previous['derivation_id']}.json").read_bytes())}, 'files': {}}
            for role in ['output_units', 'output_candidates']:
                relative = f"translation-data/retired/derivations/{previous['derivation_id']}/{role.replace('_', '-')}.jsonl"
                destination = root / relative; destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes((root / previous['files'][role]['path']).read_bytes())
                manifest['files'][role] = {'path': relative, 'hash': byte_hash(destination.read_bytes())}
            write(root / f"translation-data/derivation-archives/{previous['derivation_id']}.json", manifest)
        record['unit_id_map'] = {u['unit_id']: u['unit_id'] for u in old_units}
        units = copy.deepcopy(old_units)
        if number == restoration:
            units[1] = extract_plain_proof(old_units[1], PROOF)
            evidence = {'schema_version': 1, 'source_reextraction_id': 'fixture-source', 'derivation_id': identifier,
                'source_commit': source_commit, 'created_at': record['created_at'], 'old_unit': old_units[1], 'new_unit': units[1],
                'old_source_tex_hash': byte_hash(source_tex(old_units[1])), 'new_source_tex_hash': byte_hash(PROOF),
                'selector': SELECTOR, 'fragment': PROOF, 'fragment_hash': byte_hash(PROOF)}
            write(root / 'translation-data/source-reextractions/fixture-source.json', evidence)
        raw = []
        correction_id = f'fixture-correction-{number}'
        for old_unit, old_candidate, unit in zip(old_units, old_candidates, units, strict=True):
            context = {'unit_id': unit['unit_id'], 'source_unit': unit, 'source_commit': source_commit,
                'revision_input': {'kind': 'candidate-to-revise', 'source_unit': old_unit, 'candidate': old_candidate},
                'prompt_version': 'fixture', 'policy_revision': 'fixture'}
            row = {k: copy.deepcopy(v) for k, v in old_candidate.items() if k not in {'derivation_id', 'model_correction_id'}}
            # Always identical natural text after the first correction, so new
            # source/history bindings cannot rely on changed Chinese prose.
            row.update(source_text_hash=unit['source_text_hash'], model_id=f'revision-model-{number}',
                model_lane=f'revision-{number}', model_record_id=f'fixture:revision-{number}:declared', run_id=f'revision-run-{number}',
                created_at=record['created_at'], context=context, context_hash=sha256_value(context),
                translation='这是一个范畴（category）。' if unit['node_kind'] == 'lemma' else ''.join(f'<{name}>' for name in unit['placeholders']) + '。',
                allowed_english=[], term_occurrences=[{'source_term': 'category', 'target_term': '范畴'}] if unit['node_kind'] == 'lemma' else [],
                unknown_terms=[{'source_term': 'category', 'target_term': '范畴', 'context': 'Synthetic pending'}] if unit['node_kind'] == 'lemma' else [],
                notes=['Synthetic fixture, not actual model output.'], stage='STRUCTURE_OK' if unit['node_kind'] == 'lemma' else 'TERM_OK',
                term_status='DECISION_REQUIRED' if unit['node_kind'] == 'lemma' else 'CLEAR')
            row['translation_hash'] = sha256_value(row['translation']); raw.append(row)
        correction = {'schema_version': 1, 'correction_id': correction_id, 'run_id': raw[0]['run_id'],
            'source_commit': source_commit, 'created_at': record['created_at'], 'unit_ids': [u['unit_id'] for u in units],
            'derivation_ids': {u['unit_id']: identifier for u in units}, 'files': {}}
        for role, rows in [('units', units), ('candidates', raw)]:
            correction['files'][role] = save_rows(root, f'translation-data/retired/model-corrections/{correction_id}/{role}.jsonl', rows)
        write(root / f'translation-data/model-corrections/{correction_id}.json', correction)
        revision_run = copy.deepcopy(run)
        revision_run.update(run_id=raw[0]['run_id'], run_kind='revision', created_at=record['created_at'])
        revision_run['model'].update(record_id=raw[0]['model_record_id'], requested_id=raw[0]['model_id'], resolved_id=raw[0]['model_id'])
        revision_run['inputs']['context_hashes'] = [r['context_hash'] for r in raw]
        write(root / f"translation-data/runs/{raw[0]['run_id']}.json", revision_run)
        for role, rows in [('input_units', old_units), ('input_candidates', old_candidates)]:
            name = 'units' if role == 'input_units' else 'candidates'
            record['files'][role] = save_rows(root, f'translation-data/retired/derivations/{identifier}/{name}.jsonl', rows)
        record['operations'] = [{'unit_id': u['unit_id'], 'kinds': ['model-revision'], 'reason': 'Synthetic fixture revision',
            'unit_updates': {}, 'model_correction_id': correction_id,
            'candidate_updates': {f: r[f] for f in CANDIDATE_FIELDS}} for u, r in zip(old_units, raw, strict=True)]
        if number == restoration:
            op = record['operations'][1]
            op.update(source_reextraction_id='fixture-source', unit_updates={f: units[1][f] for f in ['source_text', 'placeholders', 'render']})
            op['kinds'].append('protected-extraction')
        corrections, errors = load_repository_corrections(root)
        reextractions, source_errors = load_source_reextractions(root, harvest)
        assert not errors + source_errors, errors + source_errors
        units, candidates = replay_derivation(record, old_units, old_candidates, corrections,
            (old_units, old_candidates) if number > 1 else None, reextractions)
        for role, rows in [('output_units', units), ('output_candidates', candidates)]:
            record['files'][role] = save_rows(root, record['files'][role]['path'], rows)
        write(root / f'translation-data/derivations/{identifier}.json', record)
        records.append(record)
        if number < revisions:
            commit(root)
    return root, harvest, records


class SourceReextractionTests(unittest.TestCase):
    def test_legal_first_and_archived_later_restoration_preserve_all_origins(self):
        for restoration in [1, 2]:
            with self.subTest(restoration=restoration), tempfile.TemporaryDirectory() as temp:
                root, harvest, records = synthetic_fixture(Path(temp), revisions=3, restoration=restoration)
                self.assertEqual(validate_repository_provenance(root, harvest), [])
                self.assertEqual(validate_repository_schemas(root), [])
                evidence = read(root / 'translation-data/source-reextractions/fixture-source.json')
                self.assertNotIn('$s$', source_tex(evidence['old_unit']))
                self.assertEqual(source_tex(evidence['new_unit']), PROOF)
                current = clean(load_jsonl(root / records[-1]['files']['output_candidates']['path'])[1])
                self.assertEqual(current['model_id'], 'fixture-model')
                self.assertEqual(current['run_id'], 'fixture-run')
                self.assertEqual(current['model_correction_id'], 'fixture-correction-3')
                original = root / 'translation-data/retired/derivations/fixture-derive-1/units.jsonl'
                original_bytes = original.read_bytes()
                self.assertIn(b'and define.', original_bytes)
                git_bytes = subprocess.run(['git', '-C', str(root), 'show',
                    f"{records[0]['origin_commit']}:{records[0]['files']['output_units']['path']}"], check=True, capture_output=True).stdout
                self.assertEqual(original_bytes, git_bytes)
                report, errors = audit_repository_proofs(root, harvest)
                self.assertEqual(errors, []); self.assertEqual(report['matched'], 1)

    def test_current_preview_discloses_ancestor_source_and_every_actual_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, records = synthetic_fixture(Path(temp), revisions=3)
            record = records[-1]
            # The temporary fixture's full English file orders two unit batches.
            render_batch(root / record['files']['output_units']['path'], root / record['files']['output_candidates']['path'],
                root / 'upstream.lock', root / 'preview', 'fixture', 'Fixture', chapter_source_dir=harvest)
            text = (root / 'preview/metadata.tex').read_text()
            for value in ['锁定英文 Git 来源恢复', '旧提取输入保留', 'fixture-model', 'revision-model-1', 'revision-model-2', 'revision-model-3']:
                self.assertIn(value, text)
            with self.assertRaises(ValueError):
                render_batch(root / record['files']['output_units']['path'], root / record['files']['output_candidates']['path'],
                    root / 'upstream.lock', root / 'preview', 'fixture', 'Fixture', chapter_source_dir=root)

    def test_binding_includes_ancestor_source_and_old_approval_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, records = synthetic_fixture(Path(temp), revisions=3)
            candidate = clean(load_jsonl(root / records[-1]['files']['output_candidates']['path'])[0])
            binding = candidate_provenance_hash(root, candidate)
            path = root / 'translation-data/source-reextractions/fixture-source.json'; original = path.read_bytes()
            value = read(path); value['created_at'] = '2026-10-05T12:00:00Z'; write(path, value)
            self.assertNotEqual(candidate_provenance_hash(root, candidate), binding)
            path.write_bytes(original)
            single = copy.deepcopy(records[-1]); single['files']['output_candidates']['path'] = 'one-row.json'
            write(root / 'one-row.json', candidate)
            paths = save_decisions(root, single)
            previous = clean(load_jsonl(root / 'translation-data/retired/derivations/fixture-derive-2/output-candidates.jsonl')[0])
            self.assertEqual(previous['translation_hash'], candidate['translation_hash'])
            previous_binding = candidate_provenance_hash(root, previous)
            self.assertNotEqual(previous_binding, binding)
            for path in paths:
                row = read(path); row['provenance_hash'] = previous_binding; write(path, row)
            errors = validate_repository_decisions(root, harvest)
            self.assertEqual(sum('provenance_hash' in error for error in errors), 3, errors)

    def test_evidence_rejects_forged_git_selector_source_and_math(self):
        for fault in ['commit', 'file', 'tag', 'label', 'index', 'fragment', 'fragment-hash', 'old-hash', 'new-hash', 'new-unit', 'omit', 'reorder', 'add']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root, harvest, _ = synthetic_fixture(Path(temp))
                path = root / 'translation-data/source-reextractions/fixture-source.json'; row = read(path)
                if fault == 'commit': row['source_commit'] = 'a' * 40
                if fault == 'file': row['selector']['file'] = '../test.tex'
                if fault == 'tag': row['selector']['statement_tag'] = 'BAD1'
                if fault == 'label': row['selector']['statement_label'] = 'no-such-lemma'
                if fault == 'index': row['selector']['proof_index'] = 0
                if fault == 'fragment': row['fragment'] += '\n'; row['fragment_hash'] = byte_hash(row['fragment'])
                if fault.endswith('-hash'): row[fault.replace('-', '_') if fault == 'fragment-hash' else fault[:3] + '_source_tex_hash'] = 'sha256:' + '0' * 64
                if fault in ['new-unit', 'omit', 'reorder', 'add']:
                    unit = row['new_unit']
                    if fault == 'new-unit': unit['source_text'] += 'Extra.'
                    if fault == 'omit': unit['source_text'] = unit['source_text'].replace('<MATH_0002>', '')
                    if fault == 'reorder': unit['placeholders']['MATH_0001'], unit['placeholders']['MATH_0002'] = unit['placeholders']['MATH_0002'], unit['placeholders']['MATH_0001']
                    if fault == 'add': unit['source_text'] += '<MATH_0003>'; unit['placeholders']['MATH_0003'] = '$z$'
                    row['new_unit'] = stamp_unit_hashes(unit); row['new_source_tex_hash'] = byte_hash(source_tex(unit))
                write(path, row)
                self.assertTrue(load_source_reextractions(root, harvest)[1])

    def test_operation_rejects_wrong_frozen_inputs_owner_revision_and_unused_evidence(self):
        for fault in ['old-unit', 'derivation', 'wrong-owner', 'foreign-valid-owner', 'duplicate', 'unused', 'missing-evidence', 'v1', 'no-correction', 'missing-field', 'wrong-new-source', 'split-proof']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root, harvest, records = synthetic_fixture(Path(temp))
                record = records[0]; path = root / 'translation-data/derivations/fixture-derive-1.json'
                evidence_path = root / 'translation-data/source-reextractions/fixture-source.json'; evidence = read(evidence_path)
                op = record['operations'][1]
                if fault == 'old-unit': evidence['old_unit']['source_text'] = 'Another old source.'; evidence['old_unit'] = stamp_unit_hashes(evidence['old_unit']); evidence['old_source_tex_hash'] = byte_hash(source_tex(evidence['old_unit']))
                if fault == 'derivation': evidence['derivation_id'] = 'different'
                if fault == 'foreign-valid-owner': evidence['selector'] = {**SELECTOR, 'statement_tag': 'NEW2', 'statement_label': 'lemma-two'}
                if fault == 'wrong-owner':
                    units = load_jsonl(root / record['files']['input_units']['path']); units[0]['render']['prefix'] = '\\begin{lemma}\n\\label{test-no-such-lemma}\n'
                    corrections, _ = load_repository_corrections(root); sources, _ = load_source_reextractions(root, harvest)
                    with self.assertRaises(ValueError): replay_derivation(record, units, load_jsonl(root / record['files']['input_candidates']['path']), corrections, source_reextractions=sources)
                    continue
                if fault == 'duplicate': record['operations'][0]['source_reextraction_id'] = 'fixture-source'; record['operations'][0]['kinds'].append('protected-extraction')
                if fault == 'unused': op.pop('source_reextraction_id'); op['unit_updates'] = {}
                if fault == 'missing-evidence': evidence_path.unlink()
                if fault == 'v1': record['tool']['version'] = '1'
                if fault == 'no-correction': op.pop('model_correction_id'); op['kinds'].remove('model-revision')
                if fault == 'missing-field': op['candidate_updates'].pop('notes')
                if fault == 'wrong-new-source': op['unit_updates']['source_text'] = 'Wrong.'
                if fault == 'split-proof':
                    units = [clean(row) for row in load_jsonl(root / record['files']['input_units']['path'])]
                    extra = copy.deepcopy(units[1]); extra['unit_id'] += '-extra'; extra['render']['prefix'] = ''; units[1]['render']['suffix'] = ''; units.append(extra)
                    corrections, _ = load_repository_corrections(root); sources, _ = load_source_reextractions(root, harvest)
                    from stacks_zh.source_reextractions import validate_reextraction_operation
                    with self.assertRaisesRegex(ValueError, 'chain mismatch'):
                        validate_reextraction_operation(sources['fixture-source'], record, units, evidence['old_unit'], evidence['new_unit'])
                    continue
                if fault != 'missing-evidence': write(evidence_path, evidence)
                write(path, record)
                self.assertTrue(load_repository_derivations(root, harvest=harvest)[1])

    def test_first_git_addition_rehash_and_symlink_are_rejected(self):
        for fault in ['rehash', 'symlink', 'parent-symlink', 'rename', 'nested-orphan']:
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root, harvest, _ = synthetic_fixture(Path(temp)); commit(root)
                path = root / 'translation-data/source-reextractions/fixture-source.json'
                if fault == 'rehash': row = read(path); row['created_at'] = '2026-10-05T23:00:00Z'; write(path, row)
                if fault == 'symlink': target = root / 'target.json'; target.write_bytes(path.read_bytes()); path.unlink(); path.symlink_to(target)
                if fault == 'parent-symlink': directory = path.parent; target = root / 'source-target'; directory.rename(target); directory.symlink_to(target, target_is_directory=True)
                if fault == 'rename': path.rename(path.with_name('other.json'))
                if fault == 'nested-orphan': nested = path.parent / 'nested'; nested.mkdir(); (nested / path.name).write_bytes(path.read_bytes())
                self.assertTrue(load_source_reextractions(root, harvest)[1])

    def test_plain_helper_blocks_commands_comments_math_structure_and_titles(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _, _ = synthetic_fixture(Path(temp)); evidence = read(root / 'translation-data/source-reextractions/fixture-source.json')
            for body in [r'\ref{lemma-one}', '$$x$$', r'\emph{Text}', '% comment\nText', '[Proof] Text', '$x', r'\input{chapters}', r'\begin{enumerate}Text\end{enumerate}']:
                with self.subTest(body=body), self.assertRaises(UnsupportedSource):
                    extract_plain_proof(evidence['old_unit'], r'\begin{proof}' + body + r'\end{proof}')

    def test_locked_git_is_used_when_english_worktree_has_changed(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = synthetic_fixture(Path(temp))
            (harvest / 'test.tex').write_text('Do not use worktree content.')
            (harvest / 'tags/tags').write_text('BAD1,test-lemma-one\n')
            self.assertEqual(LockedEnglish(root, harvest).select(SELECTOR), PROOF)
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            self.assertTrue(validate_repository_provenance(root))

    def test_audit_reports_every_group_mismatch_unsupported_and_ref_order(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, records = synthetic_fixture(Path(temp))
            units = [clean(row) for row in load_jsonl(root / records[0]['files']['output_units']['path'])]
            wrong = copy.deepcopy(units[1]); wrong['placeholders']['MATH_0002'] = '$z$'
            save_rows(root, records[0]['files']['output_units']['path'], [units[0], wrong])
            statement2 = copy.deepcopy(units[0]); statement2.update(unit_id='tag:NEW2:statement', parent_tag='NEW2')
            statement2['render']['prefix'] = '\\begin{lemma}\n\\label{test-lemma-two}\n'
            proof2 = copy.deepcopy(units[1]); proof2.update(unit_id='tag:NEW2:proof-p001', parent_tag='NEW2')
            proof3 = copy.deepcopy(proof2); proof3['unit_id'] = 'tag:NEW2:proof-p002'
            save_rows(root, 'translation-data/units/test-second.jsonl', [statement2, proof2, proof3])
            report, errors = audit_repository_proofs(root, harvest)
            self.assertEqual((report['proof_group_count'], report['proof_unit_count'], report['matched'], report['mismatched'], report['unsupported']), (3, 3, 1, 1, 1)); self.assertTrue(errors)
            from stacks_zh.source_reextractions import _comparison
            self.assertNotEqual(_comparison(r'\ref{a} then \ref{b}'), _comparison(r'\ref{b} then \ref{a}'))
            self.assertEqual(_comparison('a% comment\nb'), _comparison('ab'))
            self.assertNotEqual(_comparison('a% comment\nb'), _comparison('a b'))
            from stacks_zh.source_reextractions import _proof_index
            for text in ['\\begin{document}\n\\begin{lemma}\n\\label{x}Text\\end{lemma}\nUnrelated paragraph.\n' + PROOF + '\n\\end{document}',
                         '\\begin{document}\n' + PROOF + '\n\\end{document}']:
                self.assertTrue(_proof_index(text)['proofs'][0]['unsupported'])
            with self.assertRaises(UnsupportedSource): _proof_index('\\begin{document}\n\\verb|\\begin{proof}|\n\\end{document}')

    def test_nested_math_labels_comments_and_duplicate_owners_cannot_select_other_proofs(self):
        from stacks_zh.source_reextractions import _proof_index
        valid = '\\begin{document}\n\\begin{lemma}\n\\label{one}\n$x\\label{fake}$\n\\end{lemma}\n% \\begin{proof} ignored\n' + PROOF + '\n\\end{document}'
        self.assertEqual(_proof_index(valid)['proofs'][0]['label'], 'one')
        with self.assertRaisesRegex(UnsupportedSource, 'duplicate'):
            _proof_index(valid.replace('\\end{document}', '\\begin{lemma}\\label{one}Text\\end{lemma}\n\\end{document}'))
        invalid = valid.replace('\\label{one}\n', '')
        self.assertIsNone(_proof_index(invalid)['proofs'][0]['label'])
        with self.assertRaisesRegex(UnsupportedSource, 'text argument'):
            _proof_index('\\begin{document}\n\\texttt{' + PROOF + '}\n\\end{document}')

    def test_cli_threads_harvest_and_refuses_fact_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = synthetic_fixture(Path(temp))
            with patch('builtins.print'):
                for command in ['provenance-check', 'decision-check', 'audit-proof-source']:
                    self.assertEqual(main([command, '--root', str(root), '--harvest', str(harvest)]), 0)
                self.assertEqual(main(['audit-proof-source', '--root', str(root), '--harvest', str(harvest), '--output', str(root / 'translation-data/units/test.jsonl')]), 1)
            self.assertEqual(source_tex(clean(load_jsonl(root / 'translation-data/units/test.jsonl')[1])), PROOF)

    def test_schema_check_includes_source_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _, _ = synthetic_fixture(Path(temp)); write(root / 'translation-data/source-reextractions/fixture-source.json', {})
            self.assertTrue(any('source-reextractions' in error for error in validate_repository_schemas(root)))
