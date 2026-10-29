"""Literal synthetic fixtures, never model generation or production policy."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_math_text import BASE_POLICY
from test_source_containers import fixture as english_fixture, selector
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import (find_slots, validate_regions, validate_translation,
                                digest, skeleton)
from stacks_zh.records import RecordError, expected_unit_hashes, restore_placeholders
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import source_tex
from stacks_zh.source_terms import source_projection, source_inventory


MATRIX = r'''$$
\left\{
\begin{matrix}
2\text{-category of}\\
\text{stacks over }\mathcal{C}/U
\end{matrix}
\right\}
\leftrightarrow
\left\{
\begin{matrix}
2\text{-category of pairs }(\mathcal{T}, p)
\text{ consisting} \\
\text{of a stack }\mathcal{T}\text{ over }\mathcal{C}\text{ and a morphism} \\
p : \mathcal{T} \to \mathcal{C}/U\text{ of stacks over }\mathcal{C}
\end{matrix}
\right\}
$$'''
ROOT_OVER = r'$x\text{ over }Y$'
EXPECTED = [
    ('-category of', 'matrix-numeric-category-prefix'),
    ('stacks over ', 'matrix-category-description'),
    ('-category of pairs ', 'matrix-numeric-category-prefix'),
    (' consisting', 'matrix-category-description'),
    ('of a stack ', 'matrix-category-description'),
    (' over ', 'matrix-category-description'),
    (' and a morphism', 'matrix-category-description'),
    (' of stacks over ', 'matrix-category-description'),
]


def policy_text(base=BASE_POLICY, *, label='test-lemma-one', kind='proof',
                root_label=None, root_kind=None):
    """Explicit test/probe registry; never installed in real config."""
    text = ''
    for index, (literal, role) in enumerate(EXPECTED):
        if literal == ' over ':
            continue
        text += (f'  matrix-description-{index}:\n    literal: {json.dumps(literal)}\n'
                 f'    command: "text"\n    usage: "{role}"\n'
                 f'    source_label: "{label}"\n    witness_kind: "{kind}"\n'
                 '    witness_ordinal: 1\n')
    text += ('  stacks-root-over:\n    literal: " over "\n    command: "text"\n'
             '    usage: "root-phrase"\n'
             f'    source_label: "{root_label or label}"\n'
             f'    witness_kind: "{root_kind or kind}"\n    witness_ordinal: 1\n')
    header = 'translatable_math_text:\n'
    result = (base.replace(header, header + text, 1) if header in base
              else base + '\n' + header + text)
    header = 'translatable_math_text_contexts:\n'
    context = ('  stacks-matrix-over:\n    base_rule: "stacks-root-over"\n'
               '    usage: "matrix-category-description"\n'
               f'    source_label: "{label}"\n    witness_kind: "{kind}"\n'
               '    witness_ordinal: 1\n')
    return (result.replace(header, header + context, 1) if header in result
            else result + '\n' + header + context)


def unit_fixture(base):
    proof = '\\begin{proof}\nCafé δ. ' + ROOT_OVER + '\n' + MATRIX + '\n\\end{proof}'
    root, harvest, _ = english_fixture(base, proof=proof)
    (root / 'config/macro-policy.yml').write_text(policy_text())
    native = Containers(root, harvest)
    selected = native.select(selector())
    return root, harvest, native, selected, lower_container(selected, native.policy)[0], proof


class MatrixCategoryTests(unittest.TestCase):
    def test_eight_complete_parameters_have_independent_expected_roles(self):
        rules = Policy(policy_text()).math_text_rules
        slots = find_slots(MATRIX, rules)
        self.assertEqual([(s['value'], s['usage']) for s in slots], EXPECTED)
        for s in slots:
            self.assertEqual(MATRIX[s['parameter_start']:s['parameter_end']], s['value'])
        self.assertEqual(slots[5]['policy_entry'], 'stacks-matrix-over')

    def test_explicit_root_and_matrix_over_do_not_borrow_roles(self):
        new = Policy(policy_text()).math_text_rules
        old = Policy(policy_text().split('translatable_math_text_contexts:')[0]).math_text_rules
        self.assertEqual(find_slots(ROOT_OVER, old), find_slots(ROOT_OVER, new))
        self.assertEqual([s['value'] for s in find_slots(MATRIX, old)],
                         [v for v, _ in EXPECTED if v != ' over '])
        self.assertEqual(old['stacks-root-over'], new['stacks-root-over'])
        self.assertEqual([s['usage'] for s in find_slots(ROOT_OVER, new)], ['root-phrase'])

    def test_complete_delimiters_and_category_letters_are_structural(self):
        rules = Policy(policy_text()).math_text_rules
        for opening, closing in [('$', '$'), (r'\(', r'\)'), (r'\[', r'\]')]:
            source = opening + MATRIX[2:-2] + closing
            self.assertEqual([(s['value'], s['usage']) for s in find_slots(source, rules)], EXPECTED)
        source = MATRIX.replace(r'\mathcal{C}', r'\mathcal{D}').replace(
            r'\mathcal{T}', r'\mathcal{S}').replace('/U', '/V').replace(' p)', ' q)').replace('p :', 'q :')
        self.assertEqual([(s['value'], s['usage']) for s in find_slots(source, rules)], EXPECTED)

    def test_wrong_complete_frames_never_supply_partial_slots(self):
        rules = Policy(policy_text()).math_text_rules
        cases = [
            MATRIX.replace(r'\leftrightarrow', r'\longrightarrow'),
            MATRIX.replace(r'\left\{', r'\left('),
            MATRIX.replace(r'\right\}', r'\right)'),
            MATRIX.replace('matrix', 'aligned'),
            MATRIX.replace('2\\text', '3\\text'),
            MATRIX.replace('2\\text', '12\\text'),
            MATRIX.replace('2\\text', '2 \\text'),
            MATRIX.replace('/U', '/U_i'),
            MATRIX.replace(r'\mathcal{C}', r'\mathcal C'),
            MATRIX.replace(r'\mathcal{C}', r'\mathbf{C}'),
            MATRIX.replace(r'\mathcal{C}', r'\mathcal{CC}'),
            MATRIX.replace(r'\mathcal{C}', r'\mathcal{c}'),
            MATRIX.replace(r'\mathcal{C}', r'\mathcal{ C }'),
            MATRIX.replace(r'\to', r'\unknown'),
            MATRIX.replace(r'\to', r'\rightarrow'),
            MATRIX.replace('p :', 'pq :'),
            MATRIX.replace(' p)', ' P)'),
            MATRIX.replace(r'\text{stacks over }', r'&\text{stacks over }'),
            MATRIX.replace(r'\text{stacks over }', r'x\text{stacks over }'),
            MATRIX.replace(r'\text{stacks over }', r'\textit{stacks over }'),
            MATRIX.replace(r'\text{ over }', r'\text{\alpha over }'),
            MATRIX.replace(r'\text{ over }', r'\text{ }'),
            MATRIX.replace(r'\text{ over }', r'\text{ over }\\'),
            '$$x+' + MATRIX[2:],
            MATRIX[:-2] + '+x$$',
            '$$\\unknown ' + MATRIX[2:],
            '$$\\unknown{' + MATRIX[2:-2] + '}$$',
            '$$x^{' + MATRIX[2:-2] + '}$$',
            '$$\\begin{equation}' + MATRIX[2:-2] + '\\end{equation}$$',
            '$$\\label{' + MATRIX[2:-2] + '}$$',
            '$$\\verb|' + MATRIX[2:-2] + '|$$',
            MATRIX.replace(r'\leftrightarrow', '%\\leftrightarrow\n'),
            MATRIX.replace('\\text{ over }', '%\\text{ over }\n'),
            MATRIX.replace('-category of}', '--category of}'),
            MATRIX.replace('-category of}', 'category of}'),
        ]
        for source in cases:
            with self.subTest(source=source):
                try:
                    slots = find_slots(source, rules)
                except ValueError:
                    slots = []
                self.assertFalse(slots)

    def test_registry_keeps_exact_literals_and_context_reference_contract(self):
        original = policy_text()
        for changed in [
            original.replace('base_rule: "stacks-root-over"', 'base_rule: "missing"'),
            original.replace('base_rule: "stacks-root-over"', 'base_rule: "stacks-matrix-over"'),
            original.replace('literal: " over "', 'literal: "over "'),
            original.replace('usage: "matrix-category-description"\n    source_label:',
                             'usage: "root-phrase"\n    source_label:'),
            original.replace('base_rule: "stacks-root-over"', 'base_rule: "stacks-root-over"\n    literal: " over "'),
            original.replace('witness_ordinal: 1', 'witness_ordinal: true'),
            original + original[original.index('  stacks-matrix-over:'):].replace(
                'stacks-matrix-over:', 'duplicate-context:'),
        ]:
            with self.subTest(policy=changed[-200:]), self.assertRaises(RecordError):
                Policy(changed)
        duplicate = original.split('translatable_math_text_contexts:')[0]
        duplicate += ('  duplicate-over:\n    literal: " over "\n    command: "text"\n'
                      '    usage: "matrix-category-description"\n'
                      '    source_label: "test-lemma-one"\n    witness_kind: "proof"\n    witness_ordinal: 1\n')
        with self.assertRaises(RecordError):
            Policy(duplicate)

    def test_parameter_whitespace_case_and_old_usage_permissions_remain_exact(self):
        rules = Policy(policy_text()).math_text_rules
        for original, changed in [('stacks over ', 'Stacks over '),
                                  ('stacks over ', 'stacks over'),
                                  (' over ', '  over '), ('-category of', '-Category of')]:
            with self.subTest(changed=changed):
                self.assertNotIn(changed, [s['value'] for s in find_slots(MATRIX.replace(
                    '{' + original + '}', '{' + changed + '}'), rules)])
        for role in ['root-phrase', 'matrix-row-text', 'matrix-row-prefix', 'root-hyphen-phrase']:
            with self.subTest(role=role):
                text = policy_text().replace('usage: "matrix-numeric-category-prefix"', f'usage: "{role}"')
                if role != 'root-hyphen-phrase':
                    with self.assertRaises(RecordError):
                        Policy(text)
                else:
                    self.assertFalse(any(s['value'].startswith('-') for s in find_slots(MATRIX, Policy(text).math_text_rules)))

    def test_full_git_lowering_regions_schemas_utf8_and_english_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, native, selected, unit, proof = unit_fixture(Path(temp))
            self.assertEqual(unit['schema_version'], 2)
            self.assertEqual(source_tex(unit), proof)
            self.assertFalse(validate_regions(unit))
            self.assertFalse(validate_named_schema(unit, 'unit.schema.json', 'synthetic'))
            self.assertFalse(validate_translation(unit, unit['source_text']))
            self.assertTrue(all(unit[k] == v for k, v in expected_unit_hashes(unit).items()))
            self.assertEqual(sum(len(r['slots']) for r in unit['math_text_regions']), 9)
            self.assertEqual(selected['fragment'], proof)
            self.assertEqual(lower_container(selected, native.policy)[0], unit)
            self.assertEqual(unit['render']['prefix'] + restore_placeholders(unit, unit['source_text'])
                             + unit['render']['suffix'], proof)

    def test_synthetic_plain_leaf_values_preserve_hyphens_and_math_skeleton(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, _, _, unit, _ = unit_fixture(Path(temp))
            value = unit['source_text']
            for region in unit['math_text_regions']:
                for slot in region['slots']:
                    left, right = ('<' + p + '>' for p in slot['boundary_placeholders'])
                    sentinel = '-Synthetic' if slot['source'].startswith('-') else 'Synthetic'
                    value = value.replace(left + slot['source'] + right, left + sentinel + right)
            self.assertFalse(validate_translation(unit, value))
            for bad in [value.replace('-Synthetic', 'Synthetic'), value + '<MATHSEG_9999>',
                        value.replace('Synthetic', r'\alpha'), value.replace('Synthetic', ''),
                        value.replace('Synthetic', 'x%y'), value.replace('Synthetic', 'x\ny')]:
                with self.subTest(value=bad):
                    self.assertTrue(validate_translation(unit, bad))

    def test_qualified_category_terms_are_visible_without_mutating_source(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, _, _, unit, _ = unit_fixture(Path(temp))
            before = copy.deepcopy(unit)
            visible, declared = source_projection(unit)
            self.assertEqual(visible.count('2-category'), 2)
            self.assertEqual(declared.count('2-category'), 1)
            inventory = source_inventory(unit, {'terms': [], 'nonmathematical_declarations': {}})
            self.assertEqual([x['source_term'] for x in inventory['occurrences']], ['2-category'] * 2)
            self.assertEqual(unit, before)

    def test_recomputed_hashes_cannot_authorize_changed_math_or_roles(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, _, _, unit, _ = unit_fixture(Path(temp))
            for mutate in ['source', 'role', 'span', 'piece']:
                changed = copy.deepcopy(unit)
                region = changed['math_text_regions'][-1]
                if mutate == 'source':
                    region['source'] = region['source'].replace('/U', '/V')
                    region['source_hash'] = digest(region['source'])
                elif mutate == 'role':
                    region['slots'][0]['classification_witness']['usage'] = 'matrix-category-description'
                elif mutate == 'span':
                    region['slots'][0]['slot_byte_span']['start'] += 1
                else:
                    region['pieces'][0], region['pieces'][2] = region['pieces'][2], region['pieces'][0]
                changed['source_math_skeleton_hash'] = digest(skeleton(changed))
                changed.update(expected_unit_hashes(changed))
                with self.subTest(mutation=mutate):
                    self.assertTrue(validate_regions(changed))

    def test_missing_or_wrong_git_witness_does_not_authorize_slots(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _, _, _, _ = unit_fixture(Path(temp))
            for changed in [policy_text().replace('test-lemma-one', 'test-lemma-missing'),
                            policy_text().replace('witness_ordinal: 1', 'witness_ordinal: 2'),
                            policy_text().replace('witness_kind: "proof"', 'witness_kind: "lemma"')]:
                (root / 'config/macro-policy.yml').write_text(changed)
                with self.subTest(policy=changed[-180:]), self.assertRaises(RecordError):
                    Containers(root, harvest)

    def test_new_plain_leaves_coexist_with_unchanged_v3_components(self):
        from test_math_text_components import RULE
        component = r'$$\bigcup\nolimits_{W\subset D\text{ irred.\ comp. with }\dim(W)=d}W$$'
        proof = '\\begin{proof}\n' + ROOT_OVER + '\n' + MATRIX + '\n' + component + '\n\\end{proof}'
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = english_fixture(Path(temp), proof=proof)
            (root / 'config/macro-policy.yml').write_text(policy_text() + RULE)
            native = Containers(root, harvest)
            unit = lower_container(native.select(selector()), native.policy)[0]
            self.assertEqual(unit['schema_version'], 3)
            self.assertEqual(source_tex(unit), proof)
            self.assertFalse(validate_regions(unit))
            self.assertFalse(validate_named_schema(unit, 'unit.schema.json', 'synthetic v3'))
            self.assertFalse(validate_translation(unit, unit['source_text']))
            self.assertEqual(sum('parameter_components' in s for r in unit['math_text_regions']
                                 for s in r['slots']), 2)

    def test_production_policy_registers_exact_complete_parameters(self):
        root = Path(__file__).resolve().parents[1]
        policy = Policy((root / 'config/macro-policy.yml').read_text())
        slots = find_slots(MATRIX, policy.math_text_rules)
        self.assertEqual([(s['value'], s['usage']) for s in slots], EXPECTED)
        self.assertEqual([s['policy_entry'] for s in slots], [
            'stacks-category-of', 'stacks-stacks-over', 'stacks-category-of-pairs',
            'stacks-consisting', 'stacks-of-a-stack', 'stacks-matrix-over',
            'stacks-and-a-morphism', 'stacks-of-stacks-over'])
        self.assertEqual([s['policy_entry'] for s in find_slots(ROOT_OVER, policy.math_text_rules)],
                         ['stacks-root-over'])
        self.assertEqual(policy.math_text_rules['stacks-root-over']['source_label'],
                         'stacks-lemma-relative-sheaf-over-stack-is-stack')
        self.assertEqual(policy.math_text_rules['stacks-matrix-over']['source_label'],
                         'stacks-lemma-localize-stacks')

    def test_missing_explicit_registry_still_blocks_all_eight_parameters(self):
        # The old rejection is retained under an explicit policy with no new rules.
        policy = Policy(BASE_POLICY)
        self.assertEqual(find_slots(MATRIX, policy.math_text_rules), [])
        scanner = Scanner(MATRIX, policy)
        _, _, problems = scanner.protect(0, len(MATRIX))
        self.assertEqual(len(problems), 8)

    def test_production_notation_permissions_keep_primary_and_explicit_contexts(self):
        root = Path(__file__).resolve().parents[1]
        policy = Policy((root / 'config/macro-policy.yml').read_text(), natural_text_enabled=False)
        self.assertEqual(policy.math_text_notations['Stacks'], {
            'commands': ['textit'], 'usages': ['symbol'],
            'source_label': 'stacks-definition-stacks-over-C'})
        self.assertEqual(policy.math_text_notations['Eq'], {
            'commands': ['text'], 'usages': ['applied'],
            'source_label': 'stacks-lemma-fibred-category-pullback'})
        self.assertEqual(policy.math_text_notations['pr'], {
            'commands': ['text'], 'usages': ['subscripted', 'superscripted', 'applied'],
            'source_label': 'categories-lemma-representable-diagonal'})
        cases = [
            (r'$\Mor_{\textit{Stacks}/\mathcal{C}}(S,T)$', 'Stacks', 'symbol'),
            (r'$\text{Eq}(a_0,a_1)$', 'Eq', 'applied'),
            (r'$\phi^*\text{pr}(H(x))$', 'pr', 'applied'),
            (r'$\text{pr}_1$', 'pr', 'subscripted'),
            (r'$\text{pr}^{(i,j)}_i$', 'pr', 'superscripted'),
            (r'$\text{pr}^*_i$', 'pr', 'starred-subscripted'),
        ]
        for source, notation, usage in cases:
            with self.subTest(source=source):
                scanner = Scanner(source, policy)
                text, protected, problems = scanner.protect(0, len(source))
                self.assertEqual(problems, [])
                self.assertEqual((text, protected), ('<MATH_0001>', {'MATH_0001': source}))
                self.assertEqual([(x['notation'], x['usage']) for x in scanner.math_text_classifications],
                                 [(notation, usage)])
                if usage == 'starred-subscripted':
                    self.assertEqual(scanner.math_text_classifications[0]['source_label'],
                                     'sites-section-sheaves')
        for source in [r'$\text{Stacks}$', r'$\textit{stacks}$', r'$\text{Eq}$',
                       r'$\textit{Eq}(x)$', r'$\text{ Eq}(x)$', r'$\text{pr}$',
                       r'$\text{pr}^*$', r'$\text{pr}^*_i(x)$', r'$\textit{pr}(x)$']:
            with self.subTest(blocked=source):
                scanner = Scanner(source, policy)
                _, protected, problems = scanner.protect(0, len(source))
                self.assertTrue(any(p['kind'] == 'math-text' for p in problems))
                self.assertEqual(protected, {'MATH_0001': source})

    def test_unclassified_neighbor_still_blocks_complete_adoption(self):
        with tempfile.TemporaryDirectory() as temp:
            proof = ('\\begin{proof}\n' + ROOT_OVER + '\n' + MATRIX
                     + '\n$\\text{Unregistered}$\n\\end{proof}')
            root, harvest, _ = english_fixture(Path(temp), proof=proof)
            (root / 'config/macro-policy.yml').write_text(policy_text())
            native = Containers(root, harvest)
            with self.assertRaisesRegex(RecordError, 'classification before adoption'):
                native.select(selector())

    def test_ordinary_assembly_cannot_bypass_complete_typed_source_contract(self):
        from stacks_zh.records import write_jsonl
        from stacks_zh.workflow import _assemble_candidates_with_harness_version
        with tempfile.TemporaryDirectory() as temp:
            root, _, _, _, unit, _ = unit_fixture(Path(temp))
            write_jsonl(root / 'typed.jsonl', [unit])
            output = root / 'forbidden.jsonl'
            with self.assertRaisesRegex(RecordError, 'ordinary assembly is unavailable'):
                _assemble_candidates_with_harness_version(root / 'typed.jsonl', root / 'absent.jsonl',
                    output, root / 'upstream.lock', 'synthetic', 'fixture', 'low', 'fixture',
                    'fixture', 'fixture', '2026-10-28T00:00:00Z', 'fixture', 'fixture',
                    'fixture:model', 'synthetic-run', None, 'declared')
            self.assertFalse(output.exists())

    def test_complete_history_replays_new_leaves_under_frozen_origin_policy(self):
        from test_group_derivations import fixture as history_fixture
        from stacks_zh.provenance import validate_repository_provenance
        from stacks_zh.source_containers import load_source_containers
        proof = '\\begin{proof}\n' + ROOT_OVER + '\n' + MATRIX + '\n\\end{proof}'

        def literal_fields(unit):
            # Independent test-only leaf values, never actual model output.
            if unit['schema_version'] == 1:
                return {}
            text = unit['source_text']
            for region in unit['math_text_regions']:
                for slot in region['slots']:
                    left, right = ('<' + p + '>' for p in slot['boundary_placeholders'])
                    literal = '-合成（2-category）' if slot['source'].startswith('-') else '合成'
                    text = text.replace(left + slot['source'] + right, left + literal + right)
            return dict(translation=text, allowed_english=[],
                term_occurrences=[dict(source_term='2-category', target_term='-合成')] * 2,
                unknown_terms=[dict(source_term='2-category', target_term='-合成',
                    context='Literal synthetic fixture, never real generation.')],
                term_status='DECISION_REQUIRED', stage='STRUCTURE_OK',
                notes=['Literal synthetic fixture, never real generation.'])

        with tempfile.TemporaryDirectory() as temp:
            root, harvest, records = history_fixture(Path(temp), count=2,
                proof=proof, math_policy=policy_text(), synthetic_fields=literal_fields)
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            _, errors = load_source_containers(root, harvest)
            self.assertEqual(errors, [])
            for number in [1, 2]:
                evidence = json.loads((root / ('translation-data/source-container-restorations/'
                    f'fixture-group-{number}-proof.json')).read_bytes())
                self.assertEqual(evidence['tool']['version'], 'source-container-v3')
                self.assertEqual(evidence['new_units'][0]['schema_version'], 2)
            # Current policy cannot reinterpret the two immutable historical origins.
            (root / 'config/macro-policy.yml').write_text(BASE_POLICY)
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            self.assertEqual(len(records), 2)
