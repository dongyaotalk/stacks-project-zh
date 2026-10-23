"""Independent synthetic fixtures for the witnessed contexts, never model output."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_math_text import BASE_POLICY
from test_source_containers import fixture as english_fixture, selector
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots, validate_regions
from stacks_zh.records import RecordError, restore_placeholders
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import source_tex


MEMBERSHIP = r'''\begin{equation}
\begin{matrix}
\Mor_{\mathcal{I}}(U,U') &=&
\{f : U \to U' \text{ in }\mathcal{C}\mid f=f\}
\end{matrix}
\end{equation}'''
DESCRIPTION = r'''$$
{}_pu(\mathcal{F})(V)=\left\{\begin{matrix}
\text{collections }s_{(U,\psi)}\in\mathcal{F}(U)\\
\forall\beta:(U_1,\psi_1)\to(U_2,\psi_2)\text{ in }{}_V\mathcal{I}\\
\text{ we have }\beta^*s_{(U_2,\psi_2)}=s_{(U_1,\psi_1)}
\end{matrix}\right\}
$$'''
COMPATIBILITY = r'''$$
\Mor_{\textit{Ab}(\mathcal{C})}((\mathcal{F}_1,+,0,i),(\mathcal{F}_2,+,0,i))=
\left\{\begin{matrix}
\varphi\in\Mor_{\Sh(\mathcal{C})}(\mathcal{F}_1,\mathcal{F}_2)\\
\varphi\text{ is compatible with }+,0,i
\end{matrix}\right\}
$$'''
ALIGNED = r'''\begin{align*}
(a:W\to V)\longmapsto&\{s'\in\mathcal{H}'(W)\mid\varphi'(s')=a\}\\
=&\{(s,a')\in\mathcal{H}(W)\times h_V^\#(W)\mid
a'=a\text{ and }\varphi(s)=f\circ a'\}
\end{align*}'''


def natural_policy():
    ordinary = [
        ('root-in', ' in ', 'root-phrase'),
        ('root-and', ' and ', 'root-phrase'),
        ('collections', 'collections ', 'matrix-row-description'),
        ('we-have', ' we have ', 'matrix-row-statement'),
        ('compatible', ' is compatible with ', 'matrix-operator-compatibility'),
    ]
    text = BASE_POLICY + '\ntranslatable_math_text:\n'
    for key, literal, role in ordinary:
        text += ('  '+key+':\n    literal: '+json.dumps(literal)+'\n'
                 '    command: "text"\n    usage: '+json.dumps(role)+'\n'
                 '    source_label: "test-lemma-one"\n'
                 '    witness_kind: "proof"\n    witness_ordinal: 1\n')
    text += '''translatable_math_text_contexts:
  matrix-in:
    base_rule: "root-in"
    usage: "matrix-membership"
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
  aligned-and:
    base_rule: "root-and"
    usage: "aligned-set-connector"
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
'''
    return text


def notation_policy():
    # Isolate this context tool from the independently expanded Sites policy.
    # These original negative cases deliberately use subscripted-only pr.
    current = ('  pr:\n    commands: ["text"]\n'
               '    usages: ["subscripted", "superscripted"]\n')
    historical = current.replace('["subscripted", "superscripted"]', '["subscripted"]')
    assert current in BASE_POLICY
    text = BASE_POLICY.replace(current, historical) + '\nlocked_math_text_contexts:\n'
    for key, base, command, roles, prefix in [
        ('projection-pullback', 'pr', 'text', ['starred-subscripted'], None),
        ('g-morphisms', '-Sets', 'textit', ['morphism-category-prefixed-symbol'], 'G'),
        ('h-morphisms', '-Sets', 'textit', ['morphism-category-prefixed-symbol'], 'H'),
        ('g-diagram', '-Sets', 'textit', ['diagram-category-prefixed-symbol'], 'G'),
        ('h-object', '-Sets', 'textit', ['prefixed-symbol'], 'H'),
    ]:
        text += ('  '+key+':\n    base_notation: '+json.dumps(base)+'\n'
                 '    commands: '+json.dumps([command])+'\n'
                 '    usages: '+json.dumps(roles)+'\n'
                 '    source_label: "test-lemma-one"\n')
        if prefix is not None:
            text += '    prefix: '+json.dumps(prefix)+'\n'
    return text


class NaturalContextTests(unittest.TestCase):
    def test_actual_syntax_families_have_exact_complete_parameters(self):
        rules = Policy(natural_policy()).math_text_rules
        for source, expected in [
            (MEMBERSHIP, [(' in ', 'matrix-membership')]),
            (DESCRIPTION, [('collections ', 'matrix-row-description'),
                           (' in ', 'matrix-membership'), (' we have ', 'matrix-row-statement')]),
            (COMPATIBILITY, [(' is compatible with ', 'matrix-operator-compatibility')]),
            (ALIGNED, [(' and ', 'aligned-set-connector')]),
        ]:
            with self.subTest(source=source):
                slots = find_slots(source, rules)
                self.assertEqual([(s['value'], s['usage']) for s in slots], expected)
                for slot in slots:
                    self.assertEqual(source[slot['parameter_start']:slot['parameter_end']], slot['value'])

    def test_old_root_entries_and_permissions_remain_identical(self):
        text = natural_policy()
        old = Policy(text.split('translatable_math_text_contexts:')[0]).math_text_rules
        new = Policy(text).math_text_rules
        for key in old:
            self.assertEqual(old[key], new[key])
        for source in [r'$x\text{ in }C$', r'$x\text{ and }y$']:
            self.assertEqual(find_slots(source, old), find_slots(source, new))
        self.assertFalse(find_slots(MEMBERSHIP, old))
        self.assertFalse(find_slots(ALIGNED, old))

    def test_legacy_literal_duplicates_still_fail(self):
        text = natural_policy().split('translatable_math_text_contexts:')[0]
        entry = text[text.index('  root-in:'):text.index('  root-and:')]
        with self.assertRaises(RecordError):
            Policy(text + entry.replace('root-in:', 'duplicate-in:'))

    def test_context_reference_types_duplicates_and_witnesses_fail_closed(self):
        text = natural_policy()
        cases = [
            text.replace('base_rule: "root-in"', 'base_rule: "missing"'),
            text.replace('base_rule: "root-in"', 'base_rule: "matrix-in"'),
            text.replace('base_rule: "root-in"', 'base_rule: "root-and"'),
            text.replace('usage: "matrix-membership"', 'usage: "root-phrase"'),
            text.replace('base_rule: "root-in"', 'base_rule: []'),
            text.replace('base_rule: "root-in"', 'base_rule: "root-in"\n    literal: " in "'),
            text.replace('witness_ordinal: 1', 'witness_ordinal: true'),
            text.replace('source_label: "test-lemma-one"', 'source_label: "../fake"'),
            text + text[text.index('translatable_math_text_contexts:'):],
            text + text[text.index('  matrix-in:'):text.index('  aligned-and:')].replace('matrix-in:', 'duplicate-context:'),
        ]
        for source in cases:
            with self.subTest(source=source[-200:]), self.assertRaises(RecordError):
                Policy(source)

    def test_wrong_environments_groups_metadata_and_unknown_commands_are_rejected(self):
        rules = Policy(natural_policy()).math_text_rules
        for source in [
            MEMBERSHIP.replace('equation', 'aligned'),
            MEMBERSHIP.replace(r'\to', r'\unknown'),
            MEMBERSHIP.replace(r'\mid f=f', r' f=f'),
            MEMBERSHIP.replace(r'\text{ in }\mathcal{C}', r'\text{ in }\mathcal C'),
            DESCRIPTION.replace(r'\left\{', r'\left(').replace(r'\right\}', r'\right)'),
            ALIGNED.replace('align*', 'align'),
            ALIGNED.replace(r'\mid', r'\unknown'),
            ALIGNED.replace("a'=a", "a'+a"),
            ALIGNED.replace(r'\varphi(s)=', r'\varphi(s)+'),
            r'$\label{\begin{matrix}\text{collections }s\in F\end{matrix}}$',
            '$x% \\text{ and }\ny$',
            r'$\foo{\text{ in }}$',
        ]:
            with self.subTest(source=source):
                self.assertFalse(find_slots(source, rules))

    def test_row_shapes_and_operator_list_cannot_borrow_other_roles(self):
        rules = Policy(natural_policy()).math_text_rules
        for source, rejected in [
            (DESCRIPTION.replace(r'\text{collections }', r's\text{collections }'), 'collections '),
            (DESCRIPTION.replace(r'\text{ we have }', r's\text{ we have }'), ' we have '),
            (DESCRIPTION.replace(r'\forall\beta', r'\beta'), ' in '),
            (COMPATIBILITY.replace('+,0,i', '+,1,i'), ' is compatible with '),
            (COMPATIBILITY.replace(r'\varphi\text', r'x\text'), ' is compatible with '),
        ]:
            with self.subTest(source=source):
                self.assertNotIn(rejected, [s['value'] for s in find_slots(source, rules)])

    def test_ambiguous_caller_rule_dictionary_is_rejected(self):
        rules = Policy(natural_policy()).math_text_rules
        rules['second-root-in'] = copy.deepcopy(rules['root-in'])
        with self.assertRaises(ValueError):
            find_slots(r'$x\text{ in }C$', rules)

    def test_complete_git_container_lowering_schema_and_math_roundtrip(self):
        proof = ('\\begin{proof}\nCafé. $x\\text{ in }C$; $x\\text{ and }y$.\n'
                 + '\n'.join([MEMBERSHIP, DESCRIPTION, COMPATIBILITY, ALIGNED]) + '\n\\end{proof}')
        with tempfile.TemporaryDirectory() as directory:
            root, harvest, _ = english_fixture(Path(directory), proof=proof)
            (root / 'config/macro-policy.yml').write_text(natural_policy())
            native = Containers(root, harvest)
            selected = native.select(selector())
            unit = lower_container(selected, native.policy)[0]
            self.assertEqual(source_tex(unit), proof)
            self.assertEqual(unit['schema_version'], 2)
            self.assertFalse(validate_regions(unit))
            self.assertFalse(validate_named_schema(unit, 'unit.schema.json', 'synthetic context unit'))
            self.assertTrue(unit['math_text_regions'])
            self.assertEqual(unit['render']['prefix'] + restore_placeholders(unit, unit['source_text'])
                             + unit['render']['suffix'], proof)


class NotationContextTests(unittest.TestCase):
    def classify(self, source, policy=None):
        scanner = Scanner(source, policy or Policy(notation_policy()))
        _, protected, problems = scanner.protect(0, len(source))
        return scanner.math_text_classifications, protected, problems

    def test_exact_contexts_preserve_every_math_byte(self):
        for source, role, prefix in [
            (r'$\text{pr}^*_i$', 'starred-subscripted', None),
            (r'$$\Mor_{G\textit{-Sets}}(U,S)$$', 'morphism-category-prefixed-symbol', 'G'),
            (r'$$\Mor_{H\textit{-Sets}}(T,f_*S)$$', 'morphism-category-prefixed-symbol', 'H'),
            (r'$$\xymatrix{A & G\textit{-Sets}\ar[ld]\\ B & C}$$', 'diagram-category-prefixed-symbol', 'G'),
            (r'$H\textit{-Sets}$', 'prefixed-symbol', 'H'),
        ]:
            with self.subTest(source=source):
                items, protected, problems = self.classify(source)
                self.assertFalse(problems)
                self.assertEqual([v for k,v in protected.items() if k.startswith('MATH_')], [source])
                self.assertEqual([x['usage'] for x in items], [role])
                self.assertEqual(items[0]['source_label'], 'test-lemma-one')
                if prefix:
                    self.assertIn(prefix, items[0]['usage_source'])

    def test_existing_primary_rules_win_and_are_not_mutated(self):
        old = Policy(notation_policy().split('\nlocked_math_text_contexts:')[0])
        new = Policy(notation_policy())
        self.assertEqual(old.math_text_notations, new.math_text_notations)
        for source in [r'$\text{pr}_0$', r'$G\textit{-Sets}$']:
            self.assertEqual(self.classify(source, old), self.classify(source, new))
        for source in [r'$H\textit{-Sets}$', r'$\text{pr}^*_i$', r'$\Mor_{G\textit{-Sets}}(U,S)$']:
            self.assertTrue(self.classify(source, old)[2])

    def test_wrong_scripts_fonts_prefixes_nested_and_fake_positions_remain_blocked(self):
        cases = [
            r'$\text{pr}^*$', r'$\text{pr}^*_i(x)$', r'$\text{pr}^{*}_i$',
            r'$\foo\text{pr}^*_i$', r'$\textit{pr}^*_i$', r'$\text{ pr}^*_i$',
            r'$K\textit{-Sets}$', r'$\Mor_{K\textit{-Sets}}(U,S)$',
            r'$\Mor_{xG\textit{-Sets}}(U,S)$', r'$\Hom_{G\textit{-Sets}}(U,S)$',
            r'$\Mor_{G\textit{-Sets}}$', r'$\foo\Mor_{G\textit{-Sets}}(U,S)$',
            r'$\text{\Mor_{G\textit{-Sets}}(U,S)}$',
            r'$$\xymatrix{A & G\textit{-Sets}\foo[ld]\\ B & C}$$',
            r'$$\xymatrix{A & G\textit{-Sets}\ar[z]\\ B & C}$$',
            r'$$\foo{\xymatrix{A & G\textit{-Sets}\ar[ld]}}$$',
        ]
        for source in cases:
            with self.subTest(source=source):
                self.assertTrue(self.classify(source)[2])

    def test_context_policy_is_optional_and_invalid_declarations_fail_closed(self):
        text = notation_policy()
        cases = [
            text.replace('base_notation: "pr"', 'base_notation: "missing"'),
            text.replace('base_notation: "pr"', 'base_notation: "id"'),
            text.replace('base_notation: "pr"', 'base_notation: []'),
            text.replace('commands: ["text"]', 'commands: ["textit"]'),
            text.replace('prefix: "H"', 'prefix: "K"'),
            text.replace('prefix: "H"', 'prefix: []'),
            text.replace('source_label: "test-lemma-one"', 'source_label: "../fake"'),
            text + text[text.index('locked_math_text_contexts:'):],
            text + text[text.index('  projection-pullback:'):text.index('  g-morphisms:')].replace('projection-pullback:', 'duplicate-pullback:'),
        ]
        for source in cases:
            with self.subTest(source=source[-200:]), self.assertRaises(RecordError):
                Policy(source)
        self.assertEqual(Policy(BASE_POLICY).math_text_notation_contexts, {})
