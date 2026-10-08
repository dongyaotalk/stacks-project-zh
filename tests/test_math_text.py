"""Independent literal English/Git fixtures; no actual model output is asserted."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_source_containers import fixture as english_fixture, git, selector
from test_group_derivations import fixture as history_fixture, read, save, write
from stacks_zh.extraction import Policy, Scanner, build_inventory, write_inventory
from stacks_zh.math_text import (complete_math_nodes, delimiter_kind, digest,
                                find_slots, validate_regions, validate_translation)
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import (RecordError, expected_unit_hashes, load_jsonl,
                              restore_placeholders, stamp_unit_hashes, validate_records,
                              validate_tex_controls)
from stacks_zh.schema_validation import validate_named_schema, validate_repository_schemas
from stacks_zh.source_containers import Containers, load_source_containers, lower_container
from stacks_zh.source_reextractions import byte_hash, source_tex
from stacks_zh.source_terms import source_inventory, source_tex_hash, validate_source_terms
from stacks_zh.workflow import render_batch

ROOT = Path(__file__).resolve().parents[1]
CONNECTOR = r'$x\quad\text{and}\quad y$'
CONDITION = r'$$\left\{\begin{matrix}A & \text{if} & x \\ B & \text{if} & y\end{matrix}\right.$$'
DESCRIPTOR = r'$$\{\text{affine opens of }S_{i_1}\} + \{\text{affine opens of }T\}.$$'
PROOF = '\\begin{proof}\nCafé δ. ' + CONNECTOR + '\n' + CONDITION + '\n' + DESCRIPTOR + '\n\\end{proof}'
BASE_POLICY = (ROOT / 'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0]


def policy_text():
    # These anchors and roles are literal independent expectations, not the
    # real chapter registry or values synthesized by the implementation.
    return BASE_POLICY + '''
translatable_math_text:
  connective-and:
    literal: "and"
    command: "text"
    usage: "quad-connector"
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
  matrix-if:
    literal: "if"
    command: "text"
    usage: "matrix-condition"
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
  affine-opens-of:
    literal: "affine opens of "
    command: "text"
    usage: "set-description"
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
'''


def fixture(base, proof=PROOF, statement=None):
    kwargs = {'proof': proof}
    if statement is not None:
        kwargs['statement'] = statement
    root, harvest, _ = english_fixture(base, **kwargs)
    (root / 'config/macro-policy.yml').write_text(policy_text())
    (harvest / 'chapters.tex').write_text(r'\item \hyperref[test-section-phantom]{Test}' + '\n')
    git(harvest, 'add', '.')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'synthetic chapter manifest')
    sha = git(harvest, 'rev-parse', 'HEAD')
    (root / 'upstream.lock').write_text(f'commit = "{sha}"\n')
    containers = Containers(root, harvest)
    selected = containers.select(selector())
    unit = lower_container(selected, containers.policy)[0]
    return root, harvest, containers, selected, unit


def synthetic_translation(unit):
    # Only literal test strings; never copied to a real correction/run.
    return (unit['source_text'].replace('and', '且').replace('if', '若')
            .replace('affine opens of ', '的仿射开集（affine opens）'))


class ClassificationTests(unittest.TestCase):
    def test_three_exact_roles_have_independent_expected_parameters(self):
        rules = Policy(policy_text()).math_text_rules
        for source, words, roles in [
            (CONNECTOR, ['and'], ['quad-connector']),
            (CONDITION, ['if', 'if'], ['matrix-condition'] * 2),
            (DESCRIPTOR, ['affine opens of '] * 2, ['set-description'] * 2),
        ]:
            with self.subTest(source=source):
                slots = find_slots(source, rules)
                self.assertEqual([s['value'] for s in slots], words)
                self.assertEqual([s['usage'] for s in slots], roles)
                for slot in slots:
                    self.assertEqual(source[slot['parameter_start']:slot['parameter_end']], slot['value'])

    def test_wrong_words_commands_case_spacing_nested_or_roles_are_not_slots(self):
        rules = Policy(policy_text()).math_text_rules
        cases = [r'$x\text{and}y$', r'$x\quad\text{And}\quad y$',
                 r'$x\quad\text{ and }\quad y$', r'$x\quad\text{ands}\quad y$',
                 r'$x\quad\textit{and}\quad y$', r'$x\quad\textbf{and}\quad y$',
                 r'$x\quad\text{\text{and}}\quad y$', r'$x\quad\text{and% hidden}\quad y$',
                 r'$x\quad\text{if}\quad y$', r'$A & \text{if} & x$',
                 r'$\begin{aligned}A & \text{if} & x\end{aligned}$',
                 r'$\{\text{affine opens of}S\}$', r'$\{\text{affine opens of }s\}$',
                 r'$\{\text{affine opens of }S$', r'$\text{affine opens of }S\}$',
                 r'$\foo{\quad\text{and}\quad}$', r'$x^{\quad\text{and}\quad}$',
                 r'$\begin{unknown}\quad\text{and}\quad\end{unknown}$']
        cases.append(r'$x\quad\text{and}\quad y + \begin{unknown}z\end{unknown}$')
        for source in cases:
            with self.subTest(source=source):
                try:
                    actual = find_slots(source, rules)
                except ValueError:
                    actual = []
                self.assertEqual(actual, [])

    def test_comments_metadata_literals_and_escaped_backslash_are_not_witnesses(self):
        rules = Policy(policy_text()).math_text_rules
        for source in ['$x % \\quad\\text{and}\\quad\n y$',
                       r'$\verb|\quad\text{and}\quad|$',
                       r'$\begin{verbatim}\quad\text{and}\quad\end{verbatim}$',
                       r'$\label{\quad\text{and}\quad}$',
                       r'$\ref{\quad\text{and}\quad}$',
                       r'$\\quad\\text{and}\\quad$']:
            with self.subTest(source=source):
                self.assertEqual(find_slots(source, rules), [])

    def test_registry_is_strict_and_has_no_chinese_or_approval(self):
        original = policy_text()
        for before, after in [('literal: "and"', 'literal: "且"'),
                              ('command: "text"', 'command: "textit"'),
                              ('usage: "quad-connector"', 'usage: "guessed"'),
                              ('witness_ordinal: 1', 'witness_ordinal: true'),
                              ('source_label: "test-lemma-one"', 'source_label: "../test"'),
                              ('witness_kind: "proof"', 'witness_kind: "unknown"'),
                              ('literal: "and"', 'literal: "size"'),
                              ('literal: "if"', 'literal: "and"')]:
            with self.subTest(after=after), self.assertRaises(RecordError):
                Policy(original.replace(before, after, 1))
        for added in ['    target: "且"\n', '    approved: true\n', '    literal: "other"\n']:
            with self.subTest(added=added), self.assertRaises(RecordError):
                Policy(original + added)
        with self.assertRaises(RecordError):
            Policy(original + '\ntranslatable_math_text:\n')

    def test_unverified_registry_does_not_enable_scanner_slots(self):
        scanner = Scanner(CONNECTOR, Policy(policy_text()))
        text, tokens, problems = scanner.protect(0, len(CONNECTOR))
        self.assertEqual(text, '<MATH_0001>')
        self.assertEqual(tokens, {'MATH_0001': CONNECTOR})
        self.assertEqual(scanner.math_text_regions, [])
        self.assertTrue(any(p['kind'] == 'math-text' for p in problems))

    def test_all_original_delimiters_and_extra_bytes(self):
        for source, kind in [(CONNECTOR, 'inline-dollar'), (CONDITION, 'display-dollar'),
                             (r'\(x\quad\text{and}\quad y\)', 'inline-paren'),
                             (r'\[x\quad\text{and}\quad y\]', 'display-bracket'),
                             (r'\begin{equation}x\quad\text{and}\quad y\end{equation}', 'environment')]:
            with self.subTest(source=source):
                self.assertEqual(delimiter_kind(source), kind)
                with self.assertRaises(ValueError):
                    delimiter_kind(source + 'x')


class TypedSourceTests(unittest.TestCase):
    def test_full_git_replay_roles_utf8_and_independent_piece_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, containers, selected, unit = fixture(Path(tmp))
            self.assertEqual(source_tex(unit), PROOF)
            self.assertEqual(unit['schema_version'], 2)
            self.assertEqual(unit['risk_level'], 'R3')
            self.assertEqual(validate_named_schema(unit, 'unit.schema.json', 'fixture'), [])
            self.assertEqual(validate_regions(unit), [])
            self.assertEqual(complete_math_nodes(unit), [CONNECTOR, CONDITION, DESCRIPTOR])
            self.assertEqual(unit['source_math_hash'], digest([CONNECTOR, CONDITION, DESCRIPTOR]))
            self.assertEqual(len(unit['math_text_regions']), 3)
            self.assertEqual([len(r['slots']) for r in unit['math_text_regions']], [1, 2, 2])
            self.assertEqual([unit['placeholders'][p['placeholder']] for p in unit['math_text_regions'][0]['pieces']
                              if p['kind'] == 'locked'], [r'$x\quad\text{', r'}\quad y$'])
            self.assertEqual([unit['placeholders'][p['placeholder']] for p in unit['math_text_regions'][2]['pieces']
                              if p['kind'] == 'locked'], [r'$$\{\text{', r'}S_{i_1}\} + \{\text{', r'}T\}.$$'])
            raw = PROOF.encode()
            for region in unit['math_text_regions']:
                span = region['source_byte_span']
                self.assertEqual(raw[span['start']:span['end']], region['source'].encode())
                self.assertEqual(span['start'], raw.index(region['source'].encode()))
                for slot in region['slots']:
                    span = slot['slot_byte_span']
                    self.assertEqual(region['source'].encode()[span['start']:span['end']], slot['source'].encode())
                    anchor = slot['classification_witness']['anchor']
                    self.assertEqual((anchor['owner_tag'], anchor['owner_label'], anchor['kind'], anchor['ordinal']),
                                     ('0001', 'test-lemma-one', 'proof', 1))
                    git_bytes = subprocess.run(['git', '-C', str(harvest), 'show',
                        containers.english.commit + ':test.tex'], check=True, capture_output=True).stdout
                    for match in anchor['matches']:
                        command_span = match['command_byte_span']
                        command = git_bytes[command_span['start']:command_span['end']]
                        self.assertEqual(byte_hash(command), match['command_hash'])
                        self.assertEqual(command, ('\\text{' + slot['source'] + '}').encode())

    def test_multiple_regions_titles_and_namespace_renaming(self):
        statement = ('\\begin{lemma}[Title ' + CONNECTOR + ']\n\\label{lemma-one}\n'
                     'Body ' + CONNECTOR + '\n\\end{lemma}')
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, containers, _, _ = fixture(Path(tmp), statement=statement)
            selected = containers.select(selector('lemma'))
            for layout in ['whole', 'split-title']:
                with self.subTest(layout=layout):
                    units = lower_container(selected, containers.policy, layout=layout)
                    self.assertEqual(''.join(source_tex(u) for u in units), statement)
                    self.assertEqual(sum(len(u['math_text_regions']) for u in units), 2)
                    for unit in units:
                        self.assertEqual(validate_regions(unit), [])
                        self.assertEqual(len(unit['placeholders']), len(set(unit['placeholders'])))
                        self.assertEqual(unit['risk_level'], 'R3')

    def test_optional_proof_title_preserves_all_original_boundaries(self):
        proof = PROOF.replace('\\begin{proof}', '\\begin{proof}[Title ' + CONNECTOR + ']')
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, unit = fixture(Path(tmp), proof=proof)
            self.assertEqual(source_tex(unit), proof)
            self.assertEqual(len(unit['math_text_regions']), 4)
            self.assertEqual(validate_regions(unit), [])

    def test_old_policy_does_not_reinterpret_units_as_new_math(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            old = Containers(root, harvest, natural_text_enabled=False)
            with self.assertRaisesRegex(RecordError, 'blocked'):
                lower_container(old.select(selector()), old.policy)

    def test_actual_git_tags_witness_kind_ordinal_and_literal_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            original = policy_text()
            for before, after in [('test-lemma-one', 'test-lemma-two'),
                                  ('witness_kind: "proof"', 'witness_kind: "section"'),
                                  ('witness_ordinal: 1', 'witness_ordinal: 2'),
                                  ('literal: "and"', 'literal: "other"')]:
                (root / 'config/macro-policy.yml').write_text(original.replace(before, after, 1))
                with self.subTest(after=after), self.assertRaises(RecordError):
                    Containers(root, harvest)

    def test_dirty_english_worktree_is_not_a_source_or_witness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, unit = fixture(Path(tmp))
            (harvest / 'test.tex').write_text('Fake source bytes.')
            (harvest / 'tags/tags').write_text('Fake tags.')
            containers = Containers(root, harvest)
            self.assertEqual(lower_container(containers.select(selector()), containers.policy), [unit])

    def test_source_graph_tampering_is_rejected_even_with_recomputed_unit_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, original = fixture(Path(tmp))
            for fault in ['span', 'slot-span', 'slot-source', 'region-source', 'delimiter', 'pieces-order',
                          'slot-id', 'slot-boundary', 'role', 'usage-witness', 'extra-segment', 'risk', 'v1']:
                unit = copy.deepcopy(original)
                region = unit['math_text_regions'][0]
                slot = region['slots'][0]
                if fault == 'span': region['source_byte_span']['start'] -= 1
                if fault == 'slot-span': slot['slot_byte_span']['end'] += 1
                if fault == 'slot-source': slot['source'] = 'if'
                if fault == 'region-source': region['source'] = region['source'].replace('x', 'z')
                if fault == 'delimiter': region['delimiter_kind'] = 'display-dollar'
                if fault == 'pieces-order': region['pieces'].reverse()
                if fault == 'slot-id': slot['slot_id'] = 'math/0002/text/0001'
                if fault == 'slot-boundary': slot['boundary_placeholders'].reverse()
                if fault == 'role': slot['classification_witness']['usage'] = 'matrix-condition'
                if fault == 'usage-witness': slot['classification_witness']['usage_source']['before'] += 'x'
                if fault == 'extra-segment': unit['placeholders']['MATHSEG_9999'] = '$x$'
                if fault == 'risk': unit['risk_level'] = 'R1'
                if fault == 'v1': unit['schema_version'] = 1
                region['source_hash'] = digest(region['source'])
                try:
                    unit = stamp_unit_hashes(unit)
                except KeyError:
                    # A nonexistent slot cannot even be hashed as a graph.
                    pass
                with self.subTest(fault=fault):
                    self.assertTrue(validate_regions(unit))

    def test_missing_duplicate_or_reordered_regions_and_slots_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, original = fixture(Path(tmp))
            for fault in ['missing', 'duplicate', 'reorder', 'missing-slot', 'duplicate-slot']:
                unit = copy.deepcopy(original)
                regions = unit['math_text_regions']
                if fault == 'missing': regions.pop()
                if fault == 'duplicate': regions.append(copy.deepcopy(regions[-1]))
                if fault == 'reorder': regions.reverse()
                if fault == 'missing-slot': regions[-1]['slots'].pop()
                if fault == 'duplicate-slot': regions[-1]['slots'].append(copy.deepcopy(regions[-1]['slots'][0]))
                with self.subTest(fault=fault):
                    self.assertTrue(validate_regions(unit))

    def test_ordinary_v1_hash_algorithm_and_opaque_math_stay_exact(self):
        from test_source_containers import old_unit
        row = old_unit('a' * 40, 'tag:0001:statement', 'lemma', 'Take <MATH_0001>.')
        row['placeholders'] = {'MATH_0001': r'$\text{and} + x$'}
        row = stamp_unit_hashes(row)
        self.assertEqual(row['source_math_hash'], digest({'MATH_0001': r'$\text{and} + x$'}))
        self.assertNotIn('source_math_skeleton_hash', expected_unit_hashes(row))
        self.assertEqual(validate_regions(row), [])


class TranslationGuardTests(unittest.TestCase):
    def test_only_plain_text_leaves_change_and_math_restores_without_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, unit = fixture(Path(tmp))
            translated = synthetic_translation(unit)
            expected = (PROOF.replace('and', '且').replace('if', '若')
                        .replace('affine opens of ', '的仿射开集（affine opens）'))
            self.assertEqual(validate_translation(unit, translated), [])
            self.assertEqual(unit['render']['prefix'] + restore_placeholders(unit, translated) + unit['render']['suffix'], expected)
            self.assertEqual(source_tex(unit), PROOF)

    def test_each_slot_rejects_empty_tex_tokens_controls_and_newlines(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, unit = fixture(Path(tmp))
            translated = synthetic_translation(unit)
            for text in ['', ' ', r'\alpha', '$x$', '{若}', 'a%b', 'a&b', 'a_b', 'a^b', '#', '~',
                         '<MATHSEG_0001>', '若\n', '若\r', '若\x00', '若\u200b', '若\ud800']:
                with self.subTest(text=repr(text)):
                    bad = translated.replace('且', text, 1)
                    self.assertTrue(validate_translation(unit, bad))
                    with self.assertRaises(RecordError):
                        restore_placeholders(unit, bad)

    def test_token_removal_reorder_duplicates_and_slot_boundary_exchange_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, unit = fixture(Path(tmp))
            text = synthetic_translation(unit)
            for bad in [text.replace('<MATHSEG_0001>', '', 1),
                        text + '<MATHSEG_0001>',
                        text.replace('<MATHSEG_0001>', '<MATHSEG_9999>', 1),
                        text.replace('<MATHSEG_0001>且<MATHSEG_0002>', '<MATHSEG_0002>且<MATHSEG_0001>'),
                        text.replace('<MATHSEG_0001>且<MATHSEG_0002>', '且<MATHSEG_0001><MATHSEG_0002>')]:
                with self.subTest(bad=bad):
                    self.assertTrue(validate_translation(unit, bad))

    def test_slot_outside_tex_injection_still_fails_normal_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, unit = fixture(Path(tmp))
            for command in [r'\input{evil}', r'\newcommand{\x}{evil}', '$x$']:
                with self.subTest(command=command):
                    self.assertTrue(validate_tex_controls(unit, {'translation': synthetic_translation(unit) + command}))

    def test_restore_cannot_override_locked_formula_fragments(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, unit = fixture(Path(tmp))
            with self.assertRaisesRegex(RecordError, 'cannot be overridden'):
                restore_placeholders(unit, synthetic_translation(unit), {'MATHSEG_0001': r'$z\quad\text{'})
            self.assertEqual(restore_placeholders(unit, synthetic_translation(unit),
                {'MATHSEG_0001': unit['placeholders']['MATHSEG_0001']}, delimit_commands=True),
                restore_placeholders(unit, synthetic_translation(unit)))

    def test_both_affine_term_occurrences_remain_visible_and_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, _, unit = fixture(Path(tmp))
            catalog = {'schema_version': 1, 'source_commit': unit['source_commit'],
                'nonmathematical_declarations': {}, 'terms': [{'id': 'affine-opens', 'forms': ['affine opens'],
                'chapters': [], 'evidence': [{'chapter': 'test', 'unit_id': unit['unit_id'],
                    'source_term': 'affine opens', 'source_tex_hash': source_tex_hash(unit)}]}]}
            inventory = source_inventory(unit, catalog)
            self.assertEqual([o['source_term'] for o in inventory['occurrences']], ['affine opens'] * 2)
            candidate = {'unit_id': unit['unit_id'], 'translation': synthetic_translation(unit),
                'term_occurrences': [{'source_term': 'affine opens', 'target_term': '仿射开集'}] * 2,
                'unknown_terms': [{'source_term': 'affine opens', 'target_term': '仿射开集',
                    'context': 'Synthetic pending test term.'}], 'term_status': 'DECISION_REQUIRED'}
            self.assertEqual(validate_source_terms(unit, candidate, catalog), [])
            for fault in ['missing', 'english', 'clear']:
                bad = copy.deepcopy(candidate)
                if fault == 'missing': bad['term_occurrences'].pop()
                if fault == 'english': bad['translation'] = bad['translation'].replace('（affine opens）', '', 1)
                if fault == 'clear': bad.update(term_status='CLEAR', unknown_terms=[])
                with self.subTest(fault=fault):
                    self.assertTrue(validate_source_terms(unit, bad, catalog))


class InventoryTests(unittest.TestCase):
    def test_version_statistics_roundtrip_check_and_no_adoption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            output = root / 'source-ir/all'
            manifest = write_inventory(root, harvest, output)
            self.assertEqual(manifest['extractor_version'], 'source-extraction-v3')
            self.assertEqual((manifest['natural_math_text_slots'], manifest['natural_math_text_regions']), (5, 3))
            self.assertEqual(manifest['roundtrip_files'], 1)
            self.assertFalse(manifest['adopted'])
            self.assertFalse((root / 'translation-data').exists())
            self.assertEqual(write_inventory(root, harvest, output, check=True), manifest)
            rows = [json.loads(s) for s in (output / 'units.jsonl').read_text().splitlines()]
            proof = next(r for r in rows if r['unit']['node_kind'] == 'proof' and r['owner_tag'] == '0001')
            self.assertEqual(source_tex(proof['unit']), PROOF)
            self.assertEqual(len(proof['natural_math_text_classifications']), 5)
            for item in proof['natural_math_text_classifications']:
                span = item['location']
                self.assertEqual(git(harvest, 'show', 'HEAD:test.tex').encode()[span['byte_start']:span['byte_end']], item['source'].encode())

    def test_tampered_old_inventory_cannot_be_replaced_by_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            output = root / 'build/inventory'
            write_inventory(root, harvest, output)
            marker = read(output / 'manifest.json')
            for old in ['source-extraction-v1', 'source-extraction-v2']:
                marker['extractor_version'] = old
                write(output / 'manifest.json', marker)
                before = {p.name:p.read_bytes() for p in output.iterdir()}
                with self.assertRaises(RecordError):
                    write_inventory(root, harvest, output, check=True)
                self.assertEqual({p.name:p.read_bytes() for p in output.iterdir()}, before)
                write_inventory(root, harvest, output)
                marker = read(output / 'manifest.json')
            (output / 'units.jsonl').write_text('tampered')
            marker['extractor_version'] = 'source-extraction-v2'
            write(output / 'manifest.json', marker)
            before = {p.name:p.read_bytes() for p in output.iterdir()}
            with self.assertRaisesRegex(RecordError, 'invalid source inventory'):
                write_inventory(root, harvest, output)
            self.assertEqual({p.name:p.read_bytes() for p in output.iterdir()}, before)

    def test_unrelated_files_symlink_and_outside_output_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            output = root / 'build/inventory'
            write_inventory(root, harvest, output)
            (output / 'unrelated').write_text('user data')
            with self.assertRaisesRegex(RecordError, 'unrelated'):
                write_inventory(root, harvest, output)
            (output / 'unrelated').unlink()
            (root / 'build/link').symlink_to(output, target_is_directory=True)
            for path in [root / 'build/link', root / 'translation-data/inventory', root / 'build']:
                with self.subTest(path=path), self.assertRaises(RecordError):
                    write_inventory(root, harvest, path)
            (output / 'report.md').unlink()
            (output / 'report.md').symlink_to(output / 'units.jsonl')
            with self.assertRaisesRegex(RecordError, 'symlinks'):
                write_inventory(root, harvest, output)

    def test_policy_change_makes_check_stale_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            output = root / 'build/inventory'
            write_inventory(root, harvest, output)
            before = {p.name:p.read_bytes() for p in output.iterdir()}
            with (root / 'config/macro-policy.yml').open('a') as stream:
                stream.write('\n# policy revision\n')
            with self.assertRaisesRegex(RecordError, 'out of date'):
                write_inventory(root, harvest, output, check=True)
            self.assertEqual({p.name:p.read_bytes() for p in output.iterdir()}, before)

    def test_policy_mutation_during_extraction_aborts_before_any_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            from stacks_zh import extraction
            original = extraction.chapter_inventory

            def mutate(*args, **kwargs):
                result = original(*args, **kwargs)
                with (root / 'config/macro-policy.yml').open('a') as stream:
                    stream.write('\n# concurrent change\n')
                return result

            with patch('stacks_zh.extraction.chapter_inventory', side_effect=mutate):
                with self.assertRaisesRegex(RecordError, 'changed during'):
                    write_inventory(root, harvest, root / 'build/inventory')
            self.assertFalse((root / 'build/inventory').exists())

    def test_atomic_destination_failure_preserves_previous_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            output = root / 'build/inventory'
            write_inventory(root, harvest, output)
            before = {p.name:p.read_bytes() for p in output.iterdir()}
            original = Path.rename

            def fail(path, destination):
                if path.name.startswith('.extract-') and not path.name.startswith('.extract-backup-'):
                    raise OSError('synthetic atomic installation failure')
                return original(path, destination)

            with patch.object(Path, 'rename', fail), self.assertRaises(OSError):
                write_inventory(root, harvest, output)
            self.assertEqual({p.name:p.read_bytes() for p in output.iterdir()}, before)

    def test_late_source_policy_or_fact_change_preserves_previous_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            output = root / 'build/inventory'
            write_inventory(root, harvest, output)
            before = {p.name:p.read_bytes() for p in output.iterdir()}
            original = Path.write_bytes
            original_policy = (root / 'config/macro-policy.yml').read_bytes()
            original_lock = (root / 'upstream.lock').read_bytes()
            from test_source_containers import old_unit
            for fault in ['policy', 'source', 'facts']:
                def mutate(path, data):
                    result = original(path, data)
                    if path.name == 'manifest.json' and path.parent.name.startswith('.extract-'):
                        if fault == 'policy':
                            (root / 'config/macro-policy.yml').write_text(policy_text() + '\n# later\n')
                        if fault == 'source':
                            (root / 'upstream.lock').write_text('commit = "' + '0' * 40 + '"\n')
                        if fault == 'facts':
                            row = old_unit(read(output / 'manifest.json')['source_commit'],
                                           'tag:0000:p099', 'paragraph', 'Concurrent new fact.')
                            save(root, 'translation-data/units/concurrent.jsonl', [row])
                    return result
                with self.subTest(fault=fault), patch.object(Path, 'write_bytes', mutate), self.assertRaises(RecordError):
                    write_inventory(root, harvest, output)
                self.assertEqual({p.name:p.read_bytes() for p in output.iterdir()}, before)
                (root / 'config/macro-policy.yml').write_bytes(original_policy)
                (root / 'upstream.lock').write_bytes(original_lock)
                (root / 'translation-data/units/concurrent.jsonl').unlink(missing_ok=True)

    def test_parent_directory_alias_is_not_an_extraction_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            (root / 'build/real').mkdir(parents=True)
            (root / 'build/alias').symlink_to(root / 'build/real', target_is_directory=True)
            with self.assertRaisesRegex(RecordError, 'symlink'):
                write_inventory(root, harvest, root / 'build/alias/inventory')


class ProvenanceAndRenderingTests(unittest.TestCase):
    def test_ordinary_assembly_refuses_typed_units_before_drafts_or_outputs(self):
        from stacks_zh.workflow import _assemble_candidates_with_harness_version
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, unit = fixture(Path(tmp))
            entry = save(root, 'build/typed-units.jsonl', [unit])
            output = root / 'translation-data/candidates/fixture/ordinary.jsonl'
            with self.assertRaisesRegex(RecordError, 'ordinary assembly is unavailable'):
                _assemble_candidates_with_harness_version(root / entry['path'], root / 'missing-drafts.jsonl',
                    output, root / 'upstream.lock', 'synthetic', 'fixture', 'low', 'fixture', 'fixture', 'fixture',
                    '2026-10-08T00:00:00Z', 'fixture', 'fixture', 'fixture:model', 'synthetic-run', None, 'declared')
            self.assertFalse(output.exists())

    def test_complete_v4_v3_and_two_history_generations_validate_and_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = history_fixture(Path(tmp), count=2, proof=PROOF, math_policy=policy_text())
            self.assertEqual(validate_repository_schemas(root), [])
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            for number in [1, 2]:
                evidence = read(root / f'translation-data/source-container-restorations/fixture-group-{number}-proof.json')
                self.assertEqual(evidence['tool']['version'], 'source-container-v3')
            current = records[-1]
            paths = render_batch(root / current['files']['output_units']['path'],
                root / current['files']['output_candidates']['path'], root / 'upstream.lock',
                root / 'preview', 'fixture', 'Synthetic fixture', chapter_source_dir=harvest)
            rendered = ''.join(p.read_text() for p in paths)
            self.assertIn(r'$x\quad\text{且}\quad y$', rendered)
            self.assertIn(r'\{\text{的仿射开集（affine opens）}S_{i_1}\}', rendered)
            self.assertNotIn('MATHSEG_', rendered)
            self.assertIn('fixture-revision-model-1', rendered)
            self.assertIn('fixture-revision-model-2', rendered)

    def test_v3_origin_policy_is_frozen_and_today_policy_does_not_rewrite_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = history_fixture(Path(tmp), proof=PROOF, math_policy=policy_text())
            with (root / 'config/macro-policy.yml').open('a') as stream:
                stream.write('\n# later policy revision\n')
            self.assertEqual(validate_repository_provenance(root, harvest), [])

    def test_malformed_simple_proof_evidence_reports_failure_without_crashing(self):
        from stacks_zh.source_reextractions import load_source_reextractions
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _ = fixture(Path(tmp))
            write(root / 'translation-data/source-reextractions/synthetic-invalid.json',
                  {'old_unit': None, 'new_unit': None})
            self.assertTrue(load_source_reextractions(root, harvest)[1])

    def test_forged_witness_policy_or_locked_math_cannot_survive_origin_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = history_fixture(Path(tmp), proof=PROOF, math_policy=policy_text())
            path = root / 'translation-data/source-container-restorations/fixture-group-1-proof.json'
            original = read(path)
            for fault in ['anchor', 'empty-matches', 'policy', 'math', 'old-version']:
                evidence = copy.deepcopy(original)
                unit = evidence['new_units'][0]
                slot = unit['math_text_regions'][0]['slots'][0]
                if fault == 'anchor': slot['classification_witness']['anchor']['owner_tag'] = '0002'
                if fault == 'empty-matches': slot['classification_witness']['anchor']['matches'] = []
                if fault == 'policy': slot['classification_witness']['policy_hash'] = 'sha256:' + '0' * 64
                if fault == 'math': unit['placeholders']['MATHSEG_0001'] = r'$z\quad\text{'
                if fault == 'old-version': evidence['tool']['version'] = 'source-container-v2'
                evidence['new_units'][0] = stamp_unit_hashes(unit)
                write(path, evidence)
                with self.subTest(fault=fault):
                    self.assertTrue(load_source_containers(root, harvest)[1])
            write(path, original)
            self.assertEqual(load_source_containers(root, harvest)[1], [])

    def test_active_plain_assembly_without_v4_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = history_fixture(Path(tmp), proof=PROOF, math_policy=policy_text())
            path = root / records[-1]['files']['output_candidates']['path']
            rows = load_jsonl(path)
            for row in rows:
                for key in ['derivation_id', 'unit_group_id', 'model_correction_id', 'model_correction_hash']:
                    row.pop(key, None)
            save(root, path.relative_to(root).as_posix(), rows)
            self.assertTrue(any('unit-v2 requires' in e for e in validate_repository_provenance(root, harvest)))
            with self.assertRaisesRegex(RecordError, 'typed math rendering requires'):
                render_batch(root / records[-1]['files']['output_units']['path'], path,
                             root / 'upstream.lock', root / 'preview', 'fixture', 'Synthetic fixture', chapter_source_dir=harvest)
            self.assertFalse((root / 'preview').exists())

    def test_raw_correction_cannot_render_as_active_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = history_fixture(Path(tmp), proof=PROOF, math_policy=policy_text())
            units = root / 'translation-data/retired/model-corrections/fixture-revision-1/units.jsonl'
            candidates = root / 'translation-data/retired/model-corrections/fixture-revision-1/candidates.jsonl'
            with self.assertRaisesRegex(RecordError, 'active validated'):
                render_batch(units, candidates, root / 'upstream.lock', root / 'preview', 'revision-1', 'Synthetic fixture',
                             chapter_source_dir=harvest)
            self.assertFalse((root / 'preview').exists())

    def test_every_raw_model_field_and_full_context_are_still_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = history_fixture(Path(tmp), proof=PROOF, math_policy=policy_text())
            correction = read(root / 'translation-data/model-corrections/fixture-revision-1.json')
            path = root / correction['files']['candidates']['path']
            original = load_jsonl(path)
            for field in ['translation', 'allowed_english', 'term_occurrences', 'unknown_terms', 'notes', 'context']:
                rows = copy.deepcopy(original)
                rows[-1].pop(field)
                save(root, correction['files']['candidates']['path'], rows)
                with self.subTest(field=field):
                    self.assertTrue(validate_repository_provenance(root, harvest))
            save(root, correction['files']['candidates']['path'], original)
            self.assertEqual(validate_repository_provenance(root, harvest), [])

    def test_unpaired_typed_current_units_and_symlinks_cannot_skip_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = history_fixture(Path(tmp), proof=PROOF, math_policy=policy_text())
            current = records[-1]
            rows = load_jsonl(root / current['files']['output_units']['path'])
            typed = [u for u in rows if u['schema_version'] == 2]
            save(root, 'translation-data/units/unpaired.jsonl', typed)
            self.assertTrue(any('active unit-v2 requires a validated candidate' in e
                                for e in validate_repository_provenance(root, harvest)))
            (root / 'translation-data/units/unpaired.jsonl').unlink()
            (root / 'translation-data/units/unpaired.jsonl').write_text('null\n')
            self.assertTrue(any('active unit records must be objects' in e
                                for e in validate_repository_provenance(root, harvest)))
            (root / 'translation-data/units/unpaired.jsonl').unlink()
            path = root / current['files']['output_units']['path']
            original = path.read_bytes()
            elsewhere = root / 'build/aliased-units.jsonl'
            elsewhere.parent.mkdir(exist_ok=True)
            elsewhere.write_bytes(original)
            path.unlink(); path.symlink_to(elsewhere)
            self.assertTrue(any('symlink' in e for e in validate_repository_provenance(root, harvest)))
            with self.assertRaisesRegex(RecordError, 'active validated files'):
                render_batch(path, root / current['files']['output_candidates']['path'], root / 'upstream.lock',
                             root / 'preview', 'fixture', 'Synthetic fixture', chapter_source_dir=harvest)

    def test_legacy_derivation_and_v4_without_first_source_evidence_reject_typed_units(self):
        from stacks_zh.derivations import replay_derivation
        from stacks_zh.model_corrections import load_repository_corrections
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = history_fixture(Path(tmp), proof=PROOF, math_policy=policy_text())
            record = records[-1]
            typed = load_jsonl(root / record['files']['output_units']['path'])
            candidates = load_jsonl(root / record['files']['output_candidates']['path'])
            for version in ['1', '2', '3']:
                bad = copy.deepcopy(record)
                bad['tool']['version'] = version
                bad.pop('unit_groups')
                bad.update(unit_id_map={u['unit_id']: u['unit_id'] for u in typed}, operations=[])
                with self.subTest(version=version), self.assertRaisesRegex(ValueError, 'separate v4'):
                    replay_derivation(bad, typed, candidates)
            bad = copy.deepcopy(record)
            next(g for g in bad['unit_groups'] if g['group_id'] == 'proof')['source_container_restoration_id'] = None
            corrections, errors = load_repository_corrections(root)
            containers, source_errors = load_source_containers(root, harvest)
            self.assertEqual(errors + source_errors, [])
            with self.assertRaisesRegex(ValueError, 'first unit-v2'):
                replay_derivation(bad, load_jsonl(root / record['files']['input_units']['path']),
                    load_jsonl(root / record['files']['input_candidates']['path']), corrections,
                    source_containers=containers, tags=Containers(root, harvest).english.tags)

    def test_math_source_and_history_change_invalidate_stale_approval_even_with_equal_chinese(self):
        from stacks_zh.model_corrections import candidate_provenance_hash
        from stacks_zh.decisions import validate_repository_decisions
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = history_fixture(Path(tmp), count=2, proof=PROOF, math_policy=policy_text())
            first = load_jsonl(root / 'translation-data/retired/derivations/fixture-group-1/output-candidates.jsonl')[-1]
            current = load_jsonl(root / records[-1]['files']['output_candidates']['path'])[-1]
            self.assertEqual(first['translation_hash'], current['translation_hash'])
            original_hash = candidate_provenance_hash(root, current)
            self.assertNotEqual(candidate_provenance_hash(root, first), original_hash)
            path = root / 'translation-data/source-container-restorations/fixture-group-2-proof.json'
            original = read(path)
            changed = copy.deepcopy(original)
            changed['new_units'][0]['math_text_regions'][0]['slots'][0]['classification_witness']['anchor']['owner_tag'] = '0002'
            write(path, changed)
            self.assertNotEqual(candidate_provenance_hash(root, current), original_hash)
            write(path, original)
            selection = {'schema_version': 1, 'selection_id': 'synthetic-stale-math', 'unit_id': current['unit_id'],
                'run_id': current['run_id'], 'source_commit': current['source_commit'],
                'translation_hash': current['translation_hash'], 'provenance_hash': candidate_provenance_hash(root, first),
                'decision': 'accept-candidate', 'decided_by': 'synthetic-maintainer',
                'decided_at': '2026-10-06T09:00:00Z', 'reason': 'Synthetic stale approval test; never human evidence.'}
            write(root / 'translation-data/selections/synthetic-stale-math.json', selection)
            self.assertTrue(any('provenance' in e for e in validate_repository_decisions(root)))
