"""Independent source-only positive and negative chapter-59 syntax fixtures."""
import unittest
from unittest.mock import patch
from stacks_zh import math_text_etale as etale
from stacks_zh.math_text import nodes, find_slots

FINITE = r"$\emptyset = \bigcap_{I' \subset I\text{ finite}} T_{I'}$"
FINAL = r'$u(\text{final object}) = \text{final object}$'
PAIRS = r'''$$
H_\etale^1(S, \mu_n) =
\text{group of pairs }(\mathcal{L}, \alpha)\text{ up to isomorphism as above}
$$'''

def rule(literal):
    return dict(literal=literal, command='text', usage='etale-scheme-diagrams',
                source_label='test-section-first', witness_kind='section', witness_ordinal=1)

class EtaleCohomologyMathFramesTests(unittest.TestCase):
    def test_complete_subscript_condition_and_final_object(self):
        self.assertEqual([s['value'] for s in find_slots(FINITE, {'finite': rule(' finite')})], [' finite'])
        self.assertEqual([s['value'] for s in find_slots(FINAL, {'final': rule('final object')})],
                         ['final object', 'final object'])

    def test_math_operands_depth_wrapper_and_gap_are_locked(self):
        for source in [FINITE.replace("I' \\subset I", "I \\subset I'"),
                       FINITE.replace('T_{I\'}', 'S_{I\'}'),
                       FINITE.replace('\\text{ finite}', '{\\text{ finite}}'),
                       FINITE.replace(' = ', '  = '),
                       FINITE.replace('$', r'\(', 1),
                       FINITE.replace('\\text', '\\textit')]:
            with self.subTest(source=source):
                self.assertEqual(find_slots(source, {'finite': rule(' finite')}), [])

    def test_nonframe_natural_text_and_unknown_literal_stay_closed(self):
        self.assertEqual(find_slots(r'$I\text{ finite}$', {'finite': rule(' finite')}), [])
        self.assertEqual(find_slots(FINITE.replace(' finite', ' arbitrary'), {'finite': rule(' finite')}), [])
        self.assertEqual(find_slots(FINITE.replace(' finite', ' finite\\unknown{x}'), {'finite': rule(' finite')}), [])

    def test_context_fallback_does_not_compete_with_existing_root_role(self):
        rules={'root': {**rule('group of pairs '), 'usage':'root-phrase'},
               'context': rule('group of pairs ')}
        # Isolate fallback semantics with a synthetic registered root role.
        with patch.dict(etale.COHOMOLOGY_EXISTING_ROLES, {'group of pairs ': ['root-phrase']}):
            slots=find_slots(PAIRS,rules)
        self.assertEqual([s['policy_entry'] for s in slots], ['root'])

    def test_complete_accent_components_keep_exact_separator_and_two_leaves(self):
        literals=[r" on the \'etale site ", r" which are finite \'etale together",
                  r" is an \'etale neighbourhood of ", r"descent data for \'etale sheaves wrt "]
        for literal in literals:
            with self.subTest(literal=literal):
                contract=etale.component_contract(literal)
                self.assertEqual(contract['separator'], r"\'e")
                self.assertEqual(contract['components'], literal.split(r"\'e"))
                self.assertEqual(len(contract['components']),2)
                self.assertTrue(etale.component_values(literal))
                self.assertIsNone(etale.component_contract(literal.replace(r"\'e", r"\`e"))['literal'])

    def test_each_locked_frame_rejects_added_operand_and_nontext_command(self):
        for source in etale.COHOMOLOGY_FRAMES:
            with self.subTest(source=source):
                stream=nodes(source)
                indices=[i for i,n in enumerate(stream) if n.get('command')=='text']
                self.assertTrue(indices)
                changed=source.replace('\\text{', '\\textit{', 1)
                self.assertFalse(etale._matches(changed,nodes(changed),source))
                self.assertFalse(etale._matches(source+'x',nodes(source+'x'),source))

    def test_notation_contexts_require_exact_complete_frames(self):
        roles = {'pr':'etale-projection', 'can':'etale-canonical-map',
                 '-Sets':'etale-set-category', "F\\'Et":'etale-finite-etale-category',
                 'red':'etale-reduced-norm', 'PAb':'etale-pab-category'}
        for value, frames in etale.COHOMOLOGY_NOTATION_FRAMES.items():
            for source in frames:
                stream = nodes(source)
                index = next(i for i,n in enumerate(stream) if n.get('value') == value)
                with self.subTest(value=value, source=source):
                    self.assertIsNotNone(etale.notation_context(source,stream,index,value,roles[value]))
                    self.assertIsNone(etale.notation_context(source,stream,index,value,'unregistered'))
                    for changed in [source+'x', source.replace(' ', '  ',1),
                                    source.replace('\\text', '\\textbf',1)]:
                        if changed == source:
                            continue
                        changed_stream=nodes(changed)
                        self.assertIsNone(etale.notation_context(changed,changed_stream,index,value,roles[value]))

    def test_bare_words_cannot_borrow_notation_frames(self):
        for value, command, role in [('pr','text','etale-projection'),
                ('can','text','etale-canonical-map'),
                ('-Sets','textit','etale-set-category')]:
            source='$\\'+command+'{'+value+'}$'
            self.assertIsNone(etale.notation_context(source,nodes(source),1,value,role))

    def test_pab_sole_frame_cannot_change_font_symbol_or_argument(self):
        original = r'$\textit{PAb}$'
        stream = nodes(original)
        index = next(i for i,n in enumerate(stream) if n.get('value') == 'PAb')
        self.assertIsNotNone(etale.notation_context(original,stream,index,'PAb','etale-pab-category'))
        for source in [r'$\text{PAb}$', r'$\textit{PAb}(\mathcal{C})$',
                       r'$\textit{PAb}_X$', r'$\textit{PAb}^X$',
                       r'$\textit{PAb}\oplus X$', r'$\textit{PAb }$',
                       r'\(\textit{PAb}\)']:
            self.assertIsNone(etale.notation_context(source,nodes(source),index,'PAb','etale-pab-category'))

class EtaleCohomologyNotationParserTests(unittest.TestCase):
    """Independent parser/Scanner assertions; policies below are synthetic only."""
    @staticmethod
    def context_policy(base, command, role):
        from pathlib import Path
        text = (Path(__file__).resolve().parents[1] / 'config/macro-policy.yml').read_text()
        entry = ('  etale59-test:\n    base_notation: "' + base + '"\n'
                 '    commands: ["' + command + '"]\n'
                 '    usages: ["' + role + '"]\n'
                 '    source_label: "test-lemma-one"\n')
        return text.replace('locked_math_text_contexts:\n',
                            'locked_math_text_contexts:\n' + entry, 1)

    @staticmethod
    def usage(source, policy, value, command='textit'):
        from stacks_zh.extraction import Scanner
        start = source.index('\\' + command + '{' + value + '}')
        return Scanner(source, policy).notation_usage(
            command, value, start + len('\\' + command + '{' + value + '}'),
            command_start=start)

    def test_pab_context_preserves_primary_and_legacy_shriek(self):
        from stacks_zh.extraction import Policy
        policy = Policy(self.context_policy('PAb', 'textit', 'etale-pab-category'))
        self.assertEqual(self.usage(r'$\textit{PAb}$', policy, 'PAb')[0], 'etale-pab-category')
        self.assertEqual(self.usage(r'$\textit{PAb}(\mathcal{C})$', policy, 'PAb')[0], 'applied')
        original = r"$\mathcal{F}_{U'} = j_{U'!}^{\textit{PAb}}\mathbf{Z}_{U'}$"
        self.assertEqual(self.usage(original, policy, 'PAb')[0], 'sites-pab-shriek')
        for source in [r'$\textit{PAb}_X$', r'$\textit{PAb}^X$',
                       r'$\textit{PAb}\oplus X$', r'\(\textit{PAb}\)']:
            self.assertIsNone(self.usage(source, policy, 'PAb'))

    def test_new_contexts_cannot_mix_roles_fonts_or_unwitnessed_fields(self):
        from stacks_zh.extraction import Policy
        from stacks_zh.records import RecordError
        for base, command, role in [('PAb', 'textit', 'etale-pab-category'),
                ('pr', 'text', 'etale-projection'), ('can', 'text', 'etale-canonical-map'),
                ('-Sets', 'textit', 'etale-set-category')]:
            text = self.context_policy(base, command, role)
            Policy(text)
            changes = [text.replace('["' + role + '"]', '["' + role + '", "symbol"]'),
                       text.replace('    commands: ["' + command + '"]\n    usages: ["' + role,
                                    '    commands: ["textbf"]\n    usages: ["' + role),
                       text.replace('  etale59-test:\n', '  etale59-test:\n    prefix: "G"\n')]
            for changed in changes:
                with self.subTest(base=base, changed=changed), self.assertRaises(RecordError):
                    Policy(changed)

    def test_accent_notation_key_and_reduced_norm_are_exact_finite_roles(self):
        from pathlib import Path
        from stacks_zh.extraction import Policy
        from stacks_zh.records import RecordError
        base = (Path(__file__).resolve().parents[1] / 'config/macro-policy.yml').read_text()
        for key, command, role, source in [
                ("F\\'Et", 'textit', 'etale-finite-etale-category', r"$\textit{F\'Et}_S$"),
                ('red', 'text', 'etale-reduced-norm', r'$N_\text{red}(x) = 0$')]:
            entry = ('  ' + key + ':\n    commands: ["' + command + '"]\n'
                     '    usages: ["' + role + '"]\n    source_label: test-lemma-one\n')
            text = base.replace('locked_math_text_notations:\n', 'locked_math_text_notations:\n' + entry, 1)
            policy = Policy(text)
            self.assertEqual(self.usage(source, policy, key, command)[0], role)
            for changed in [text.replace('["' + role + '"]', '["symbol", "' + role + '"]'),
                            text.replace(entry, entry.replace('  ' + key + ':', '  Fake:')),
                            text.replace(entry, entry.replace('["' + command + '"]', '["textbf"]'))]:
                with self.subTest(key=key, changed=changed), self.assertRaises(RecordError):
                    Policy(changed)
            self.assertIsNone(self.usage(source.replace('= 0', '= 1') if key == 'red'
                                        else source.replace('_S', '_X'), policy, key, command))
