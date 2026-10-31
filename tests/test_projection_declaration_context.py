"""Production registration and independent synthetic syntax/Git fixtures."""
import copy
import tempfile
import unittest
from pathlib import Path

from test_source_containers import fixture as english_fixture, selector
from test_stacks_matrix_categories import MATRIX, ROOT_OVER, policy_text as natural_policy
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import validate_regions, validate_translation
from stacks_zh.records import RecordError, expected_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_alignment import Corpus
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import source_tex


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = (ROOT / 'config/macro-policy.yml').read_text()
LEGACY = (ROOT / 'tests/fixtures/macro-policy-before-projection-declaration.yml').read_text()
PRODUCTION_ENTRY = '''  stacks-projection-declaration:
    base_notation: "pr"
    commands: ["text"]
    usages: ["projection-declaration"]
    source_label: "stacks-lemma-adjointness-pullback-pushforward"
'''
DECLARATION = r'$\text{pr} : u^p\mathcal{T} \to \mathcal{T}$'
ENTRY = '''  projection-declaration:
    base_notation: "pr"
    commands: ["text"]
    usages: ["projection-declaration"]
    source_label: "test-lemma-one"
'''


def experimental_policy(base=LEGACY):
    # Synthetic sources own their own witness label. Strip only the exact
    # real production registration before adding that synthetic witness.
    base = base.replace(PRODUCTION_ENTRY, "", 1)
    header = 'locked_math_text_contexts:\n'
    return base.replace(header, header + ENTRY, 1) if header in base else base + '\n' + header + ENTRY


def scan(source, text):
    scanner = Scanner(source, Policy(text))
    protected = scanner.protect(0, len(source))
    return protected, scanner.math_text_classifications, scanner.math_text_regions


def git_fixture(base, *, typed=False, component=False, tail=''):
    proof = '\\begin{proof}\nCafé δ. ' + DECLARATION + '\n' + r'$\text{pr}(H(x))$'
    if typed:
        proof += '\n' + ROOT_OVER + '\n' + MATRIX
    if component:
        proof += '\n' + r'$$\bigcup\nolimits_{W\subset D\text{ irred.\ comp. with }\dim(W)=d}W$$'
    proof += tail + '\n\\end{proof}'
    root, harvest, _ = english_fixture(base, proof=proof)
    policy = natural_policy() if typed else (root / 'config/macro-policy.yml').read_text()
    if component:
        from test_math_text_components import RULE
        policy += RULE
    (root / 'config/macro-policy.yml').write_text(experimental_policy(policy))
    native = Containers(root, harvest)
    return root, harvest, native, proof


class ProjectionDeclarationTests(unittest.TestCase):
    def test_production_registration_is_exact_and_preserves_primary_rules(self):
        self.assertEqual(PRODUCTION.count(PRODUCTION_ENTRY), 1)
        self.assertEqual(PRODUCTION.replace(PRODUCTION_ENTRY, '', 1), LEGACY)
        old, new = Policy(LEGACY), Policy(PRODUCTION)
        self.assertEqual(old.math_text_notations, new.math_text_notations)
        self.assertEqual(old.math_text_rules, new.math_text_rules)
        (text, protected, errors), classified, regions = scan(DECLARATION, PRODUCTION)
        self.assertEqual((text, protected, errors), ('<MATH_0001>', {'MATH_0001': DECLARATION}, []))
        self.assertEqual(regions, [])
        self.assertEqual(classified, [dict(start=1, end=10, source=r'\text{pr}', notation='pr',
            command='text', usage='projection-declaration', usage_source=DECLARATION[10:-1],
            source_label='stacks-lemma-adjointness-pullback-pushforward')])

    def test_explicit_context_locks_complete_math_and_records_full_suffix(self):
        (text, protected, errors), classified, regions = scan(DECLARATION, experimental_policy())
        self.assertEqual((text, protected, errors), ('<MATH_0001>', {'MATH_0001': DECLARATION}, []))
        self.assertEqual(regions, [])
        self.assertEqual(classified, [dict(start=1, end=10, source=r'\text{pr}', notation='pr',
            command='text', usage='projection-declaration',
            usage_source=r' : u^p\mathcal{T} \to \mathcal{T}', source_label='test-lemma-one')])

    def test_explicit_opt_in_and_primary_registry_stay_separate(self):
        (text, protected, errors), classified, _ = scan(DECLARATION, LEGACY)
        self.assertEqual((text, protected), ('<MATH_0001>', {'MATH_0001': DECLARATION}))
        self.assertEqual(len(errors), 1)
        self.assertEqual(classified, [])
        old, new = Policy(LEGACY), Policy(experimental_policy())
        self.assertEqual(old.math_text_notations, new.math_text_notations)
        self.assertEqual(old.math_text_rules, new.math_text_rules)
        for name, rules in old.math_text_notation_contexts.items():
            self.assertEqual([r for r in new.math_text_notation_contexts[name]
                              if r['usages'] != ['projection-declaration']], rules)
        primary = LEGACY.replace('usages: ["subscripted", "superscripted", "applied"]',
                                     'usages: ["projection-declaration"]', 1)
        with self.assertRaises(RecordError):
            Policy(primary)

    def test_only_four_original_declaration_separators_allow_ascii_whitespace(self):
        cases = [r'$\text{pr}:u^p\mathcal{T}\to\mathcal{T}$',
                 '$\\text{pr}\t:\nu^p\\mathcal{T}\r\n\\to\t\\mathcal{T}$']
        for source in cases:
            with self.subTest(source=source):
                (_, protected, errors), classified, _ = scan(source, experimental_policy())
                self.assertEqual(errors, [])
                self.assertEqual(protected, {'MATH_0001': source})
                self.assertEqual(classified[0]['usage_source'], source[10:-1])

    def test_complete_frame_negative_boundaries(self):
        cases = [
            r'$\text{pr}$', r'$\text{pr}(x)$', r'$\text{pr}^*$', r'$\text{pr}^*_i(x)$',
            DECLARATION.replace(r'\text{pr}', r'\textit{pr}'),
            DECLARATION.replace(r'\text{pr}', r'\textbf{pr}'),
            DECLARATION.replace('{pr}', '{Pr}'), DECLARATION.replace('{pr}', '{pr }'),
            DECLARATION.replace('{pr}', '{ pr}'), DECLARATION.replace(r'\text{', r'\text {'),
            DECLARATION.replace(r'\text{pr}', r'\text{{pr}}'),
            DECLARATION.replace(' : ', ' '), DECLARATION.replace(r'\to', ''),
            DECLARATION.replace(r'\to', r'\rightarrow'), DECLARATION.replace(' : ', ' = '),
            DECLARATION.replace('u^p', 'u'), DECLARATION.replace('u^p', 'u^{p}'),
            DECLARATION.replace('u^p', 'u^q'), DECLARATION.replace('u^p', 'v^p'),
            DECLARATION.replace('u^p', 'u ^p'), DECLARATION.replace('u^p', 'u^ p'),
            DECLARATION.replace('u^p', r'u^p '),
            DECLARATION.replace(r'\mathcal{T}', r'\mathcal{S}'),
            DECLARATION.replace(r'\mathcal{T}', r'\mathcal{ T}'),
            DECLARATION.replace(r'\mathcal{T}', r'\mathcal{T }'),
            DECLARATION.replace(r'\mathcal{T}', r'\mathcal {T}'),
            DECLARATION.replace(r'\mathcal{T}', r'\mathbf{T}'),
            DECLARATION.replace(' : ', '\u00a0: '),
            DECLARATION.replace(' : ', ' % hidden\n: '),
            '$ ' + DECLARATION[1:], DECLARATION[:-1] + ' $',
            '$x+' + DECLARATION[1:], DECLARATION[:-1] + '+x$',
            '$x={' + DECLARATION[1:-1] + '}$',
            '$\\foo ' + DECLARATION[1:], '$\\foo{' + DECLARATION[1:-1] + '}$',
            '$x_{' + DECLARATION[1:-1] + '}$',
            '$\\text{' + DECLARATION[1:-1] + '}$',
            '$\\verb|' + DECLARATION[1:-1] + '|$',
            '$$' + DECLARATION[1:-1] + '$$',
            r'\(' + DECLARATION[1:-1] + r'\)',
            r'\[' + DECLARATION[1:-1] + r'\]',
            r'\begin{equation}' + DECLARATION[1:-1] + r'\end{equation}',
            '$\\xymatrix{' + DECLARATION[1:-1] + '}$',
            DECLARATION[:-1] + "'$", DECLARATION[:-1] + ' : Z$',
        ]
        for source in cases:
            with self.subTest(source=source):
                # Existing explicit applied/subscripted roles may accept their
                # own forms; none may acquire the new declaration witness.
                (_, _, errors), classified, _ = scan(source, experimental_policy())
                self.assertNotIn('projection-declaration', [r['usage'] for r in classified])
                if source != r'$\text{pr}(x)$':
                    self.assertTrue(errors)

    def test_legacy_classifications_witnesses_and_rejections_are_identical(self):
        cases = [r'$\text{pr}_i$', r'$\text{pr}^{(i,j)}_i$', r'$\text{pr}(H(x))$',
                 r'$\phi^*\text{pr}(H(x))$', r'$\text{pr}^*_i$', r'$\text{pr}^*$',
                 r'$\text{pr}^*_i(x)$', r'$\text{pr}^{*}_i$',
                 r'$\foo\text{pr}^*_i$', r'$\textit{pr}^*_i$',
                 r'$\text{Eq}(x)$', r'$\Mor_{\textit{Stacks}/C}(A,B)$',
                 r'$\Mor_{G\textit{-Sets}}(U,S)$', r'$H\textit{-Sets}$',
                 r'$K\textit{-Sets}$', r'$\text{can}:\mathcal{S}\to\mathcal{S}$']
        for source in cases:
            with self.subTest(source=source):
                self.assertEqual(scan(source, LEGACY), scan(source, experimental_policy()))
                self.assertEqual(scan(source, LEGACY), scan(source, PRODUCTION))
        starred = scan(r'$\text{pr}^*_i$', experimental_policy())[1][0]
        self.assertEqual((starred['usage'], starred['source_label']),
                         ('starred-subscripted', 'sites-section-sheaves'))

    def test_invalid_duplicate_conflicting_or_borrowed_policy_fails_closed(self):
        text = experimental_policy()
        cases = [
            text.replace(ENTRY, ENTRY.replace('"pr"', '"id"')),
            text.replace(ENTRY, ENTRY.replace('"pr"', '"missing"')),
            text.replace(ENTRY, ENTRY.replace('"pr"', '"-Sets"')),
            text.replace(ENTRY, ENTRY.replace('["text"]', '["textit"]')),
            text.replace(ENTRY, ENTRY.replace('["projection-declaration"]', '["symbol"]')),
            text.replace(ENTRY, ENTRY.replace('["projection-declaration"]', '["applied"]')),
            text.replace(ENTRY, ENTRY.replace('["projection-declaration"]', '[]')),
            text.replace(ENTRY, ENTRY.replace('["projection-declaration"]', '"projection-declaration"')),
            text.replace(ENTRY, ENTRY.replace('["projection-declaration"]', '["projection-declaration", "starred-subscripted"]')),
            text.replace(ENTRY, ENTRY.replace('["projection-declaration"]', '["projection-declaration", "projection-declaration"]')),
            text.replace(ENTRY, ENTRY.replace('"test-lemma-one"', '"../fake"')),
            text.replace(ENTRY, ENTRY.replace('    source_label: "test-lemma-one"\n', '')),
            text.replace(ENTRY, ENTRY + '    prefix: "G"\n'),
            text.replace(ENTRY, ENTRY + '    source_label: "test-lemma-two"\n'),
            text + '\nlocked_math_text_contexts:\n' + ENTRY,
            text + ENTRY.replace('  projection-declaration:', '  duplicate:'),
            text.replace('usages: ["subscripted", "superscripted", "applied"]',
                         'usages: ["subscripted", "superscripted", "applied", "symbol"]', 1),
        ]
        for source in cases:
            with self.subTest(source=source[-180:]), self.assertRaises(RecordError):
                Policy(source)

    def test_rejected_primary_symbol_reproduction_is_not_a_legacy_rewrite(self):
        unsafe = LEGACY.replace('usages: ["subscripted", "superscripted", "applied"]',
                                    'usages: ["subscripted", "superscripted", "applied", "symbol"]', 1)
        for source in [r'$\text{pr}^*_i$', r'$\text{pr}^*$', r'$\text{pr}^*_i(x)$']:
            (_, _, errors), classified, _ = scan(source, unsafe)
            self.assertEqual(errors, [])
            self.assertEqual(classified[0]['usage'], 'symbol')
        with self.assertRaises(RecordError):
            Policy(experimental_policy(unsafe))

    def test_complete_synthetic_git_lowering_schema_and_rehashed_math_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            _, _, native, proof = git_fixture(Path(temp))
            selected = native.select(selector())
            unit = lower_container(selected, native.policy)[0]
            self.assertEqual(source_tex(unit), proof)
            self.assertEqual(unit['schema_version'], 1)
            self.assertFalse(validate_named_schema(unit, 'unit.schema.json', 'synthetic projection'))
            _, rows, _ = native.document('test')
            corpus = Corpus(rows, native.english.tags, native.policy, source_containers=native)
            proof_owner = {'statement_tag': '0001', 'proof_index': 1}
            self.assertEqual(corpus.match(unit, unit['unit_id'], proof_owner)['status'], 'BYTE_EXACT')
            for old, new in [(r'\to', r'\leftarrow'), ('u^p', 'u^q'), ('{T}', '{S}')]:
                changed = copy.deepcopy(unit)
                changed['placeholders'] = {k: v.replace(old, new) for k, v in changed['placeholders'].items()}
                changed.update(expected_unit_hashes(changed))
                with self.subTest(change=new):
                    self.assertNotIn(corpus.match(changed, changed['unit_id'], proof_owner)['status'],
                                     {'BYTE_EXACT', 'PRESENTATION_EQUIVALENT'})

    def test_declared_notation_coexists_with_typed_v2_and_v3_without_becoming_a_slot(self):
        for component in [False, True]:
            with self.subTest(component=component), tempfile.TemporaryDirectory() as temp:
                _, _, native, proof = git_fixture(Path(temp), typed=True, component=component)
                unit = lower_container(native.select(selector()), native.policy)[0]
                self.assertEqual(unit['schema_version'], 3 if component else 2)
                self.assertEqual(source_tex(unit), proof)
                self.assertIn(DECLARATION, unit['placeholders'].values())
                self.assertFalse(validate_named_schema(unit, 'unit.schema.json', 'synthetic typed projection'))
                self.assertFalse(validate_regions(unit))
                self.assertFalse(validate_translation(unit, unit['source_text']))
                self.assertTrue(all(slot['source'] != 'pr' for region in unit['math_text_regions'] for slot in region['slots']))
                text = unit['source_text']
                for region in unit['math_text_regions']:
                    for slot in region['slots']:
                        before, after = ('<' + p + '>' for p in slot['boundary_placeholders'])
                        text = text.replace(before + slot['source'] + after, before + r'\alpha' + after)
                self.assertTrue(validate_translation(unit, text))

    def test_unknown_neighbor_blocks_complete_container_despite_known_declaration(self):
        for tail in ['\n' + r'$\text{unknown}$', '\n' + r'\unknown{x}']:
            with self.subTest(tail=tail), tempfile.TemporaryDirectory() as temp:
                _, _, native, _ = git_fixture(Path(temp), tail=tail)
                with self.assertRaises(RecordError):
                    native.select(selector())
