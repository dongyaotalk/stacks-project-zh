"""Independent source-only positive and negative chapter-59 syntax fixtures."""
import unittest
import subprocess
from pathlib import Path

ACCEPTED_TOOL_POLICY = "5400f3d19bf86fc59807e8dfa3d69d4429910ad3"

def accepted_tool_policy():
    """Preserve the pre-registration tool fixture; production policy has separate tests."""
    return subprocess.check_output(["git", "show", ACCEPTED_TOOL_POLICY + ":config/macro-policy.yml"],
                                   cwd=Path(__file__).resolve().parents[1], text=True)

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

    def test_same_pairs_literal_keeps_root_and_exact_cohomology_context(self):
        from pathlib import Path
        from stacks_zh.extraction import Policy
        from stacks_zh.records import RecordError
        base = accepted_tool_policy()
        root = ('  etale59-pairs-root:\n'
                '    literal: " up to isomorphism as above"\n'
                '    command: "text"\n    usage: "root-phrase"\n'
                '    source_label: "test-section-one"\n'
                '    witness_kind: "section"\n    witness_ordinal: 1\n')
        context = ('  etale59-pairs-context:\n'
                   '    base_rule: "etale59-pairs-root"\n'
                   '    usage: "etale-scheme-diagrams"\n'
                   '    source_label: "test-section-one"\n'
                   '    witness_kind: "section"\n    witness_ordinal: 1\n')
        text = base.replace('translatable_math_text:\n', 'translatable_math_text:\n'+root, 1)
        text = text.replace('translatable_math_text_contexts:\n',
                            'translatable_math_text_contexts:\n'+context, 1)
        policy = Policy(text)
        slots = find_slots(PAIRS, policy.math_text_rules)
        self.assertEqual([s['policy_entry'] for s in slots], ['etale59-pairs-context'])
        fppf = PAIRS.replace('H_\\etale', 'H_{fppf}').replace('above}\n', 'above}.\n')
        self.assertEqual([s['policy_entry'] for s in find_slots(fppf, policy.math_text_rules)],
                         ['etale59-pairs-root'])
        self.assertEqual(find_slots(PAIRS+'x', policy.math_text_rules), [])
        with self.assertRaises(RecordError):
            Policy(text.replace('    base_rule: "etale59-pairs-root"',
                                '    base_rule: "categories-remaining-there-exist"'))

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

    def test_new_component_parents_lower_restore_and_reject_forgery(self):
        import copy
        import json
        import tempfile
        from pathlib import Path
        from test_source_containers import fixture, selector
        from stacks_zh.source_containers import Containers, lower_container
        from stacks_zh.source_reextractions import source_tex
        from stacks_zh.schema_validation import validate_named_schema
        from stacks_zh.math_text import validate_regions, validate_translation
        for literal in set(etale.COHOMOLOGY_COMPONENT_LITERALS)-{etale.COMPONENT_LITERALS[0]}:
            frame=next(f for f in etale.COHOMOLOGY_FRAMES if literal in f)
            with self.subTest(literal=literal), tempfile.TemporaryDirectory() as temp:
                proof='\\begin{proof}\n'+frame+'\n\\end{proof}'
                root,harvest,_=fixture(Path(temp),proof=proof)
                path=root/'config/macro-policy.yml'
                fields={'translatable_math_text':[], 'translatable_math_text_components':[]}
                for number,value in enumerate(dict.fromkeys(n['value'] for n in nodes(frame) if n.get('command')=='text')):
                    component=value in etale.COMPONENT_LITERALS
                    d=dict(literal=value,command='text',usage=etale.COMPONENT_USAGE if component else 'etale-scheme-diagrams',source_label='test-section-basic',witness_kind='section',witness_ordinal=1)
                    if component:
                        contract=etale.component_contract(value)
                        d.update(components=contract['components'],separator=contract['separator'])
                    fields['translatable_math_text_components' if component else 'translatable_math_text'].append((number,d))
                text=path.read_text()
                for section,entries in fields.items():
                    text+='\n'+section+':\n'
                    for number,d in entries:
                        text+='  etale59-component-test-'+str(number)+':\n'
                        text+=''.join('    '+k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in d.items())
                path.write_text(text)
                c=Containers(root,harvest)
                unit=lower_container(c.select(selector()),c.policy)[0]
                self.assertEqual(unit['schema_version'],3)
                self.assertEqual(source_tex(unit),proof)
                self.assertEqual(validate_named_schema(unit,'unit.schema.json','unit'),[])
                self.assertEqual(validate_regions(unit),[])
                translation=unit['source_text']
                for region in unit['math_text_regions']:
                    for slot in region['slots']:
                        before,after=('<'+p+'>' for p in slot['boundary_placeholders'])
                        a=translation.index(before)+len(before);b=translation.index(after,a)
                        translation=translation[:a]+'中文'+translation[b:]
                self.assertEqual(validate_translation(unit,translation),[])
                self.assertTrue(validate_translation(unit,translation.replace('中文','',1)))
                for parent in [literal+'x',literal.replace(etale.SEPARATOR,r"\`e")]:
                    bad=copy.deepcopy(unit)
                    slot=next(s for r in bad['math_text_regions'] for s in r['slots'] if s.get('parameter_components',{}).get('parameter_source')==literal)
                    slot['parameter_components']['parameter_source']=parent
                    self.assertTrue(validate_named_schema(bad,'unit.schema.json','bad'))
                    self.assertTrue(validate_regions(bad))

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

class EtaleCohomologyItalicCategoryTests(unittest.TestCase):
    @staticmethod
    def policy_text():
        from pathlib import Path
        text = accepted_tool_policy()
        entry = ('  etale59-italic-category:\n'
                 '    literal: "Locally ringed topoi"\n'
                 '    command: "textit"\n'
                 '    usage: "etale-locally-ringed-topoi"\n'
                 '    source_label: "test-lemma-one"\n'
                 '    witness_kind: "proof"\n    witness_ordinal: 1\n')
        return text.replace('translatable_math_text:\n', 'translatable_math_text:\n'+entry, 1)

    def test_exact_font_complete_frame_and_literal_are_required(self):
        from stacks_zh.extraction import Policy
        from stacks_zh.records import RecordError
        text = self.policy_text()
        rules = Policy(text).math_text_rules
        slots = find_slots(etale.ITALIC_FRAME, rules)
        self.assertEqual([(s['command'],s['value']) for s in slots],
                         [('textit','Locally ringed topoi')])
        for changed in [etale.ITALIC_FRAME+'x',
                        etale.ITALIC_FRAME.replace('X_\\etale', 'Y_\\etale'),
                        etale.ITALIC_FRAME.replace('\\textit', '\\text'),
                        etale.ITALIC_FRAME.replace('\\textit', '\\textbf'),
                        etale.ITALIC_FRAME.replace('Locally ringed topoi', 'arbitrary topoi'),
                        r'$\textit{Locally ringed topoi}$']:
            self.assertEqual(find_slots(changed, rules), [])
        for changed in [text.replace('    command: "textit"', '    command: "text"', 1),
                        text.replace('    usage: "etale-locally-ringed-topoi"',
                                     '    usage: "root-phrase"', 1),
                        text.replace('    literal: "Locally ringed topoi"',
                                     '    literal: "arbitrary topoi"', 1)]:
            with self.assertRaises(RecordError):
                Policy(changed)

    def test_real_complete_unit_schema_translation_and_restoration(self):
        import copy
        import tempfile
        from pathlib import Path
        from test_source_containers import fixture, selector
        from stacks_zh.source_containers import Containers, lower_container
        from stacks_zh.source_reextractions import source_tex
        from stacks_zh.schema_validation import validate_named_schema
        from stacks_zh.math_text import validate_regions, validate_translation
        with tempfile.TemporaryDirectory() as temp:
            proof = '\\begin{proof}\n'+etale.ITALIC_FRAME+'\n\\end{proof}'
            root, harvest, _ = fixture(Path(temp), proof=proof)
            (root/'config/macro-policy.yml').write_text(
                self.policy_text().split('  categories-remaining-is-isomorphism:',1)[0])
            containers = Containers(root,harvest)
            selected = containers.select(selector())
            unit = lower_container(selected, containers.policy)[0]
            self.assertEqual(unit['schema_version'],2)
            self.assertEqual(source_tex(unit),proof)
            self.assertEqual(validate_named_schema(unit,'unit.schema.json','unit'),[])
            self.assertEqual(validate_regions(unit),[])
            translation = unit['source_text'].replace('Locally ringed topoi','局部赋环拓扑斯')
            self.assertEqual(validate_translation(unit,translation),[])
            self.assertTrue(validate_translation(unit,translation.replace('局部赋环拓扑斯','')))
            for field,value in [('command','text'),('source','arbitrary topoi')]:
                bad=copy.deepcopy(unit)
                bad['math_text_regions'][0]['slots'][0][field]=value
                self.assertTrue(validate_named_schema(bad,'unit.schema.json','bad'))
                self.assertTrue(validate_regions(bad))

class EtaleCohomologyNotationParserTests(unittest.TestCase):
    """Independent parser/Scanner assertions; policies below are synthetic only."""
    @staticmethod
    def context_policy(base, command, role):
        from pathlib import Path
        text = accepted_tool_policy()
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

    def test_projection_star_contexts_are_exact_and_keep_primary_roles(self):
        from stacks_zh.extraction import Policy
        policy = Policy(self.context_policy('pr', 'text', 'etale-projection'))
        sources = [r'$j_*R^qf_*\mathcal{F} = R^q\text{pr}_*i_*\mathcal{F}$',
                   '$$\n(R^q\\text{pr}_*\\mathcal{F})_{\\overline{y}} =\n'
                   'H^q(\\mathbf{A}^{n + m}_K \\times_{A^n_K} \\Spec(\\mathcal{O}_{Y, y}^{sh}),\n'
                   '\\mathcal{F}) =\nH^q(\\mathbf{A}^m_{\\mathcal{O}_{Y, y}^{sh}}, \\mathcal{F})\n$$']
        for source in sources:
            with self.subTest(source=source):
                self.assertEqual(self.usage(source, policy, 'pr', 'text')[0], 'etale-projection')
                for changed in [source+'x', source.replace('R^q', 'R^r', 1),
                                source.replace('\\text{pr}', '\\textit{pr}', 1)]:
                    command = 'textit' if '\\textit{pr}' in changed else 'text'
                    self.assertIsNone(self.usage(changed, policy, 'pr', command))
        self.assertEqual(self.usage(r'$\text{pr}_i$', policy, 'pr', 'text')[0], 'subscripted')
        self.assertIsNone(self.usage(r'$\text{pr}_*$', policy, 'pr', 'text'))

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
        base = accepted_tool_policy()
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
