"""Synthetic complete split-paragraph histories; never actual model output."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from test_preceding_statement_paragraphs import after_fixture
from test_source_container_boundaries import INTRO, PLAIN
from test_source_containers import selector
from test_group_derivations import commit, run_for, save, write
from stacks_zh.records import RecordError, load_jsonl, placeholder_names, sha256_value, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, load_source_containers, lower_container, verify_old_group, write_container_package
from stacks_zh.source_reextractions import source_tex


def split_fixture(base, *, count=2, native=None):
    root, harvest, units, plan, output = after_fixture(base, split=True, native=native)
    old = units[2]
    pieces = ['An introductory', 'paragraph with <MATH_0001>.'] if count == 2 else [
        'An', 'introductory', 'paragraph with <MATH_0001>.']
    paragraphs = []
    for index, text in enumerate(pieces):
        unit = copy.deepcopy(old)
        unit.update(unit_id=old['unit_id'] + f'-part{index + 1}', source_text=text,
                    placeholders=old['placeholders'] if index == len(pieces) - 1 else {},
                    render={'prefix': old['render']['prefix'] if index == 0 else '',
                            'suffix': '\n'})
        paragraphs.append(stamp_unit_hashes(unit))
    units[2:3] = paragraphs
    data = json.loads(plan.read_text())
    data['groups'][1]['input_unit_ids'] = [unit['unit_id'] for unit in paragraphs]
    data['groups'][1]['identity_anchor'] = paragraphs[0]['unit_id']
    originals = {row['unit_id']: row for row in load_jsonl(root / data['candidates_file'])}
    candidates = []
    for unit in units:
        candidate = copy.deepcopy(originals.get(unit['unit_id'], originals[old['unit_id']]))
        candidate.update(unit_id=unit['unit_id'], source_text_hash=unit['source_text_hash'],
                         translation=''.join('<' + name + '>' for name in placeholder_names(unit['source_text'])) + '合成测试。')
        candidate['context']['unit_id'] = unit['unit_id']
        candidate['context_hash'] = sha256_value(candidate['context'])
        candidate['translation_hash'] = sha256_value(candidate['translation'])
        candidates.append(candidate)
    save(root, data['units_file'], units)
    save(root, data['candidates_file'], candidates)
    write(root / 'translation-data/runs/fixture-boundary-run.json',
          run_for(candidates, units[0]['source_commit'], 'translation', 'fixture-boundary-run'))
    write(plan, data)
    commit(root)
    return root, harvest, units, plan, output


class SplitPrecedingParagraphTests(unittest.TestCase):
    def witness(self, containers, units, *, ids=None):
        chosen = containers.select(selector('paragraph', owner='0000'))
        ids = ids if ids is not None else [u['unit_id'] for u in units if '-part' in u['unit_id']]
        return verify_old_group(units, containers.english.tags, ids, chosen,
                                native_containers=containers, allow_split_preceding_paragraph=True)

    def test_two_or_three_whole_old_parts_have_an_exact_independent_witness(self):
        for count in [2, 3]:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = split_fixture(Path(tmp), count=count)
                containers = Containers(root, harvest)
                chosen = containers.select(selector('paragraph', owner='0000'))
                ids = [u['unit_id'] for u in units if '-part' in u['unit_id']]
                for flags in [{}, {'allow_preceding_paragraph': True},
                              {'allow_nested_preceding_paragraph': True}, {'allow_section_title_paragraph': True}]:
                    with self.assertRaises(RecordError):
                        verify_old_group(units, containers.english.tags, ids, chosen,
                                         native_containers=containers, **flags)
                anchor = self.witness(containers, units)['paragraph_anchor']
                self.assertEqual(anchor, {
                    'paragraph_input_unit_ids': ids, 'historical_parent_tag': '0002',
                    'preceding_statement_input_unit_ids': [u['unit_id'] for u in units[:2]],
                    'preceding_statement_selector': selector('lemma'),
                    'preceding_statement_fragment_hash': 'sha256:' + hashlib.sha256(PLAIN.encode()).hexdigest(),
                    'preceding_statement_signature_hash': sha256_value([
                        ['protected', r'\begin{lemma}'], ['permanent-label', '0001'],
                        ['text', 'A complete assertion.'], ['protected', r'\end{lemma}']]),
                    'paragraph_signature_hash': sha256_value([
                        ['protected', r'\noindent'], ['text', 'An introductory paragraph with'],
                        ['protected', '$x$'], ['text', '.']])})
                self.assertEqual(source_tex(lower_container(chosen, containers.policy)[0]), INTRO + '\n')

    def test_old_scope_order_all_parts_wrappers_and_every_source_byte_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, original, _, _ = split_fixture(Path(tmp), count=3)
            containers = Containers(root, harvest)
            for fault in ['words', 'math', 'unicode', 'internal-blank', 'extra-prefix', 'fake-noindent',
                          'extra-suffix', 'parent', 'chapter', 'source', 'kind', 'order', 'duplicate',
                          'missing-part', 'missing-statement', 'statement-words', 'statement-label',
                          'statement-prefix', 'statement-close', 'partial-ids', 'empty-ids',
                          'one-id', 'reordered-ids', 'duplicate-ids', 'unknown']:
                units = copy.deepcopy(original)
                first, middle, last = units[2:5]
                ids = None
                if fault == 'words': middle['source_text'] += ' Smuggled.'
                if fault == 'math': last['placeholders']['MATH_0001'] = '$y$'
                if fault == 'unicode': middle['source_text'] += '\u00a0'
                if fault == 'internal-blank': first['render']['suffix'] = '\n\n'
                if fault == 'extra-prefix': middle['render']['prefix'] = '\\noindent\n'
                if fault == 'fake-noindent': first['render']['prefix'] = '%\\noindent\n'
                if fault == 'extra-suffix': middle['render']['suffix'] = '\\ref{test-lemma-one}\n'
                if fault == 'parent': middle['parent_tag'] = '0001'
                if fault == 'chapter': middle['chapter'] = 'other'
                if fault == 'source': middle['source_commit'] = '1' * 40
                if fault == 'kind': middle['node_kind'] = 'display_math'
                if fault == 'order': units[2:5] = [middle, first, last]
                if fault == 'duplicate': units.insert(3, copy.deepcopy(first))
                if fault == 'missing-part': units.pop(3)
                if fault == 'missing-statement': units = units[2:]
                if fault == 'statement-words': units[0]['source_text'] += ' Smuggled.'
                if fault == 'statement-label': units[0]['render']['prefix'] = '\\begin{lemma}\\label{test-lemma-two}'
                if fault == 'statement-prefix': units[0]['render']['prefix'] = '$\\begin{lemma}\\label{test-lemma-one}$'
                if fault == 'statement-close': units[1]['render']['suffix'] = '$\\end{lemma}$'
                if fault == 'partial-ids': ids = [first['unit_id'], middle['unit_id']]
                if fault == 'empty-ids': ids = []
                if fault == 'one-id': ids = [first['unit_id']]
                if fault == 'reordered-ids': ids = [middle['unit_id'], first['unit_id'], last['unit_id']]
                if fault == 'duplicate-ids': ids = [first['unit_id'], first['unit_id'], last['unit_id']]
                if fault == 'unknown': middle['source_text'] += '\\unknownCommand '
                with self.subTest(fault=fault), self.assertRaises(RecordError):
                    self.witness(containers, units, ids=ids)

    def test_native_ambiguity_intervening_nodes_and_new_math_text_stay_blocked(self):
        for native in [PLAIN + '\n\n' + INTRO + '\n\n' + INTRO,
                       PLAIN + '\n% Extra boundary.\n' + INTRO,
                       PLAIN + '\n\\begin{proof}Intervening.\\end{proof}\n' + INTRO,
                       PLAIN + '\n\\section{Other}\\label{lemma-two}\n' + INTRO,
                       PLAIN + '\n\n' + INTRO.replace('$x$', '$\\text{unclassified prose}$')]:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = split_fixture(Path(tmp), native=native)
                with self.subTest(native=native), self.assertRaises(RecordError):
                    self.witness(Containers(root, harvest), units)

    def test_single_complete_paragraph_keeps_v5_and_plain_statements_keep_old_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, plan, output = after_fixture(Path(tmp), split=True)
            self.assertEqual(write_container_package(root, harvest, plan, output)['state'], 'PREPARED')
            records = json.loads((output / 'restorations.json').read_text())
            self.assertNotIn('source-container-v8', {row['tool']['version'] for row in records})
            self.assertIn('source-container-v5', {row['tool']['version'] for row in records})

    def install(self, root, output, records):
        for record in records:
            for role, name in [('input_units', 'input-units.jsonl'), ('input_candidates', 'input-candidates.jsonl')]:
                path = root / record['files'][role]['path']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((output / name).read_bytes())
            write(root / f"translation-data/source-container-restorations/{record['restoration_id']}.json", record)

    def test_v8_package_check_replay_and_every_witness_field_are_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, plan, output = split_fixture(Path(tmp))
            before = {p.relative_to(root): p.read_bytes() for p in (root / 'translation-data').rglob('*') if p.is_file()}
            manifest = write_container_package(root, harvest, plan, output)
            self.assertEqual(manifest['state'], 'PREPARED')
            stamps = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir() if p.is_file()}
            self.assertEqual(write_container_package(root, harvest, plan, output, check=True), manifest)
            self.assertEqual(stamps, {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in output.iterdir() if p.is_file()})
            self.assertEqual(before, {p.relative_to(root): p.read_bytes() for p in (root / 'translation-data').rglob('*') if p.is_file()})
            records = json.loads((output / 'restorations.json').read_text())
            boundary = next(row for row in records if row['tool']['version'] == 'source-container-v8')
            self.assertEqual(boundary['input_unit_ids'], [unit['unit_id'] for unit in units[2:4]])
            self.install(root, output, records)
            self.assertEqual(load_source_containers(root, harvest)[1], [])
            path = root / f"translation-data/source-container-restorations/{boundary['restoration_id']}.json"
            for fault in ['missing', 'v5', 'v7', 'empty', 'one', 'partial', 'reordered', 'duplicated',
                          'parent', 'selector', 'fragment-hash', 'statement-hash', 'paragraph-hash',
                          'old-scalar', 'typed-unit']:
                row = copy.deepcopy(boundary)
                anchor = row['legacy_boundary_witness']['paragraph_anchor']
                if fault == 'missing': row.pop('legacy_boundary_witness')
                if fault in {'v5', 'v7'}: row['tool']['version'] = 'source-container-' + fault
                if fault == 'empty': anchor['paragraph_input_unit_ids'] = []
                if fault == 'one': anchor['paragraph_input_unit_ids'] = anchor['paragraph_input_unit_ids'][:1]
                if fault == 'partial': row['input_unit_ids'] = row['input_unit_ids'][:1]
                if fault == 'reordered': anchor['paragraph_input_unit_ids'].reverse()
                if fault == 'duplicated': anchor['paragraph_input_unit_ids'][1] = anchor['paragraph_input_unit_ids'][0]
                if fault == 'parent': anchor['historical_parent_tag'] = '0001'
                if fault == 'selector': anchor['preceding_statement_selector']['parent_tag'] = '0001'
                if fault == 'fragment-hash': anchor['preceding_statement_fragment_hash'] = 'sha256:' + '0' * 64
                if fault == 'statement-hash': anchor['preceding_statement_signature_hash'] = 'sha256:' + '0' * 64
                if fault == 'paragraph-hash': anchor['paragraph_signature_hash'] = 'sha256:' + '0' * 64
                if fault == 'old-scalar': anchor['paragraph_input_unit_id'] = anchor['paragraph_input_unit_ids'][0]
                if fault == 'typed-unit': row['new_units'][0]['schema_version'] = 2
                write(path, row)
                with self.subTest(fault=fault):
                    self.assertTrue(load_source_containers(root, harvest)[1])
                    if fault in {'missing', 'v5', 'v7', 'duplicated', 'old-scalar', 'typed-unit'}:
                        self.assertTrue(validate_named_schema(row, 'source-container-restoration.schema.json', 'fixture'))

    def test_group_replay_requires_every_old_part_and_every_new_five_field_record(self):
        from stacks_zh.group_derivations import FIELDS, replay_groups, revision_group
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, plan, output = split_fixture(Path(tmp))
            self.assertEqual(write_container_package(root, harvest, plan, output)['state'], 'PREPARED')
            records = json.loads((output / 'restorations.json').read_text())
            self.install(root, output, records)
            restored, errors = load_source_containers(root, harvest)
            self.assertEqual(errors, [])
            candidates = load_jsonl(output / 'input-candidates.jsonl')
            record = {key: records[0][key] for key in ['derivation_id', 'source_commit', 'origin_commit', 'created_at', 'files']}
            record['unit_groups'] = []
            corrections = {}
            for source in records:
                group = {key: source[key] for key in ['group_id', 'input_unit_ids', 'output_unit_ids', 'reason']}
                group.update(identity_anchor=group['input_unit_ids'][0], output_units=source['new_units'],
                             source_container_restoration_id=source['restoration_id'], model_correction_id='synthetic-split-revision')
                record['unit_groups'].append(group)
                old = [u for u in units if u['unit_id'] in group['input_unit_ids']]
                oldc = [c for c in candidates if c['unit_id'] in group['input_unit_ids']]
                for unit in group['output_units']:
                    raw = copy.deepcopy(oldc[0])
                    context = {'revision_input': revision_group(record, group, old, oldc)}
                    raw.update(unit_id=unit['unit_id'], context=context, context_hash=sha256_value(context),
                               translation=''.join('<' + name + '>' for name in placeholder_names(unit['source_text'])) + '合成测试。',
                               allowed_english=[], term_occurrences=[], unknown_terms=[], notes=['Synthetic test; never model output.'])
                    raw['translation_hash'] = sha256_value(raw['translation'])
                    corrections[(group['model_correction_id'], unit['unit_id'])] = {'unit': unit, 'candidate': raw,
                        'record': {'derivation_ids': {unit['unit_id']: record['derivation_id']}, 'source_commit': record['source_commit']}}
            new, newc = replay_groups(record, units, candidates, corrections, None, restored, Containers(root, harvest).english.tags)
            self.assertEqual(len(new), 2)
            self.assertTrue(all(c['publication_status'] == 'CANDIDATE' for c in newc))
            key = next(k for k, v in corrections.items() if v['unit']['node_kind'] == 'paragraph')
            for fault in [*sorted(FIELDS), 'missing-record', 'partial-old-units', 'partial-old-candidates', 'approval']:
                changed = copy.deepcopy(corrections)
                if fault in FIELDS: changed[key]['candidate'].pop(fault)
                if fault == 'missing-record': changed.pop(key)
                if fault == 'partial-old-units': changed[key]['candidate']['context']['revision_input']['source_units'].pop()
                if fault == 'partial-old-candidates': changed[key]['candidate']['context']['revision_input']['candidates'].pop()
                if fault == 'approval': changed[key]['candidate']['stage'] = 'MATH_REVIEWED'
                with self.subTest(fault=fault), self.assertRaises((RecordError, KeyError)):
                    replay_groups(record, units, candidates, changed, None, restored, Containers(root, harvest).english.tags)


if __name__ == '__main__':
    unittest.main()
