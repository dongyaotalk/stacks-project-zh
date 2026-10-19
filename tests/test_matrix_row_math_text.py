"""Literal synthetic source/translation fixtures; no actual generation is claimed."""
import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from test_math_text import BASE_POLICY
from test_source_containers import fixture as english_fixture, selector
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots, validate_regions, validate_translation
from stacks_zh.records import RecordError, expected_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import source_tex
from stacks_zh.source_terms import source_projection, source_inventory, validate_source_terms

MATRIX = (r'$$\left\{\begin{matrix}\text{the 2-category of categories}\\'
          r'\text{fibred in sets over }\mathcal{C}\end{matrix}\right\}$$')
SUFFIX = r'$$\Mor(A,B)\Big/2\text{-isomorphism}=\Mor(C,D)$$'


def policy_text():
    text = BASE_POLICY + '\ntranslatable_math_text:\n'
    for key, literal, role in [
        ('matrix-category', 'the 2-category of categories', 'matrix-row-text'),
        ('matrix-over', 'fibred in sets over ', 'matrix-row-prefix'),
        ('quotient-isomorphism', '-isomorphism', 'numeric-isomorphism-suffix'),
    ]:
        text += (f'  {key}:\n    literal: {json.dumps(literal)}\n    command: "text"\n'
                 f'    usage: "{role}"\n    source_label: "test-lemma-one"\n'
                 '    witness_kind: "proof"\n    witness_ordinal: 1\n')
    return text


def fixture(base):
    proof = '\\begin{proof}\n' + MATRIX + '\n' + SUFFIX + '\n\\end{proof}'
    root, harvest, _ = english_fixture(base, proof=proof)
    (root/'config/macro-policy.yml').write_text(policy_text())
    native = Containers(root, harvest)
    selected = native.select(selector())
    unit = lower_container(selected, native.policy)[0]
    return root, harvest, unit, proof


def named_policy():
    entry = ('  can:\n    commands: ["text"]\n    usages: ["named-arrow"]\n'
             '    source_label: test-lemma-one\n')
    # This fixture owns its literal registry independently of later production
    # policy activation; it must not duplicate a future production can entry.
    base=re.sub(r'(?ms)^locked_math_text_notations:\n.*?(?=^[A-Za-z_][A-Za-z0-9_-]*:|\Z)',
                '',BASE_POLICY)
    return base+'\nlocked_math_text_notations:\n'+entry


class MatrixRowTextTests(unittest.TestCase):
    def test_complete_rows_and_numeric_qualification_have_literal_expected_slots(self):
        rules = Policy(policy_text()).math_text_rules
        self.assertEqual([(s['value'],s['usage']) for s in find_slots(MATRIX,rules)],
            [('the 2-category of categories','matrix-row-text'),
             ('fibred in sets over ','matrix-row-prefix')])
        slots = find_slots(SUFFIX,rules)
        self.assertEqual([(s['value'],s['usage']) for s in slots],
                         [('-isomorphism','numeric-isomorphism-suffix')])
        self.assertIn(r'\mathcal{C}\end{matrix}',find_slots(MATRIX,rules)[1]['usage_source']['after'])

    def test_wrong_matrix_positions_objects_environments_and_parameters_are_rejected(self):
        rules=Policy(policy_text()).math_text_rules
        cases = [
            r'$\text{the 2-category of categories}$',
            r'$\begin{matrix}x\text{the 2-category of categories}\\\end{matrix}$',
            r'$\begin{matrix}&\text{the 2-category of categories}\\\end{matrix}$',
            r'$\begin{matrix}\text{the 2-category of categories}+x\\\end{matrix}$',
            r'$\begin{matrix}\text{the 2-category of categories}&x\end{matrix}$',
            r'$\begin{matrix}\textit{the 2-category of categories}\\\end{matrix}$',
            r'$\begin{matrix}\text{The 2-category of categories}\\\end{matrix}$',
            r'$\begin{matrix}\text{fibred in sets over}\mathcal{C}\end{matrix}$',
            r'$\begin{matrix}\text{fibred in sets over }\mathcal C\end{matrix}$',
            r'$\begin{matrix}\text{fibred in sets over }\mathbf{C}\end{matrix}$',
            r'$\begin{matrix}\text{fibred in sets over }\mathcal{c}\end{matrix}$',
            r'$\begin{matrix}\text{fibred in sets over }\mathcal{ C }\end{matrix}$',
            r'$\begin{matrix}\text{fibred in sets over }\mathcal{C}_i\end{matrix}$',
            r'$\begin{matrix}\text{fibred in sets over }\mathcal{C}+D\end{matrix}$',
            r'$\begin{unknown}\begin{matrix}\text{the 2-category of categories}\\\end{matrix}\end{unknown}$',
            r'$\foo{\begin{matrix}\text{the 2-category of categories}\\\end{matrix}}$',
            r'$\foo\begin{matrix}\text{the 2-category of categories}\\\end{matrix}$',
            r'$x^{\begin{matrix}\text{the 2-category of categories}\\\end{matrix}}$',
            r'$\verb|\begin{matrix}\text{the 2-category of categories}\\\end{matrix}|$',
            '$x % \\begin{matrix}\\text{the 2-category of categories}\\\\\n y$',
        ]
        for source in cases:
            with self.subTest(source=source):
                try: slots=find_slots(source,rules)
                except ValueError: slots=[]
                self.assertEqual(slots,[])

    def test_numeric_suffix_rejects_other_digits_words_positions_and_missing_quotient(self):
        rules=Policy(policy_text()).math_text_rules
        for source in [SUFFIX.replace('/2','/3'),SUFFIX.replace('/2','/12'),
                       SUFFIX.replace(r'\Big/','/'),SUFFIX.replace(r'\Big/',''),
                       SUFFIX.replace('2\\text','2 \\text'),SUFFIX.replace('}=','}+'),
                       SUFFIX.replace('-isomorphism','isomorphism'),
                       SUFFIX.replace('-isomorphism','-other'),
                       r'$x^{\Big/2\text{-isomorphism}=y}$']:
            with self.subTest(source=source): self.assertEqual(find_slots(source,rules),[])

    def test_full_git_lowering_schema_hashes_and_english_self_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            _,_,unit,proof=fixture(Path(temp))
            self.assertEqual(unit['schema_version'],2)
            self.assertEqual(source_tex(unit),proof)
            self.assertEqual(validate_named_schema(unit,'unit.schema.json','synthetic'),[])
            self.assertEqual(validate_regions(unit),[])
            self.assertEqual(validate_translation(unit,unit['source_text']),[])
            self.assertTrue(all(unit[k]==v for k,v in expected_unit_hashes(unit).items()))
            changed=copy.deepcopy(unit)
            changed['math_text_regions'][-1]['slots'][0]['source']='-other'
            self.assertTrue(validate_regions(changed))

    def test_complete_qualified_term_is_required_without_changing_source_or_math(self):
        with tempfile.TemporaryDirectory() as temp:
            _,_,unit,_=fixture(Path(temp));before=copy.deepcopy(unit)
            text,declared=source_projection(unit)
            self.assertIn('2-isomorphism',text);self.assertIn('2-isomorphism',declared)
            self.assertEqual(unit,before)
            catalog={'terms':[],'nonmathematical_declarations':{}}
            inv=source_inventory(unit,catalog)
            self.assertEqual([x['source_term'] for x in inv['occurrences']],['2-isomorphism'])
            target=unit['source_text'].replace('-isomorphism','-同构（2-isomorphism）')
            self.assertEqual(validate_translation(unit,target),[])
            candidate={'translation':target,'term_status':'DECISION_REQUIRED',
                'term_occurrences':[{'source_term':'2-isomorphism','target_term':'-同构'}],
                'unknown_terms':[{'source_term':'2-isomorphism','target_term':'-同构','context':'Synthetic only.'}]}
            self.assertEqual(validate_source_terms(unit,candidate,catalog),[])
            generic=copy.deepcopy(candidate)
            generic['translation']=target.replace('2-isomorphism','isomorphism')
            for row in generic['term_occurrences']+generic['unknown_terms']:row['source_term']='isomorphism'
            self.assertTrue(validate_source_terms(unit,generic,catalog))
            self.assertTrue(validate_translation(unit,target.replace('-同构','同构')))
            self.assertTrue(validate_translation(unit,target.replace('-同构',r'-\alpha')))

    def test_old_literal_roles_keep_digit_and_leading_hyphen_rejection(self):
        for old_role in ['root-phrase','quad-connector','matrix-condition']:
            for literal in ['the 2-category of categories','-isomorphism']:
                text=policy_text().replace('usage: "matrix-row-text"','usage: "'+old_role+'"')
                if literal.startswith('-'):
                    text=policy_text().replace('usage: "numeric-isomorphism-suffix"','usage: "'+old_role+'"')
                with self.subTest(role=old_role,literal=literal),self.assertRaises(RecordError):Policy(text)


class NamedArrowNotationTests(unittest.TestCase):
    def test_only_complete_root_can_morphism_declaration_is_locked_notation(self):
        self.assertEqual(set(Policy(named_policy()).math_text_notations),{'can'})
        source=r"$\text{can} : \mathcal{S} \to \mathcal{S}'$"
        scanner=Scanner(source,Policy(named_policy()))
        protected,tokens,problems=scanner.protect(0,len(source))
        self.assertEqual(protected,'<MATH_0001>');self.assertEqual(tokens,{'MATH_0001':source})
        self.assertEqual(problems,[])
        self.assertEqual([x['usage'] for x in scanner.math_text_classifications],['named-arrow'])

    def test_ordinary_can_missing_type_scripts_unknown_arguments_and_trailing_math_stay_blocked(self):
        good=r"$\text{can} : \mathcal{S} \to \mathcal{S}'$"
        cases=[r'$x\quad\text{can}\quad y$',r'$\text{can}$',
               good.replace(r'\to',r'\leftarrow'),good.replace(r'\mathcal{S}',r'\mathbf{S}',1),
               good.replace(':','='),good.replace("'$","'+x$"),
               r'$\foo{\text{can} : \mathcal{S} \to \mathcal{S}}$',
               r'$x^{\text{can} : \mathcal{S} \to \mathcal{S}}$']
        for source in cases:
            with self.subTest(source=source):
                scanner=Scanner(source,Policy(named_policy()));_,_,problems=scanner.protect(0,len(source))
                self.assertTrue(any(x['kind']=='math-text' for x in problems))
                self.assertEqual(scanner.math_text_classifications,[])

    def test_named_arrow_does_not_mix_symbol_usage_or_other_words_fonts(self):
        for before,after in [('usages: ["named-arrow"]','usages: ["named-arrow", "symbol"]'),
                             ('  can:','  other:'),
                             ('  can:\n    commands: ["text"]','  can:\n    commands: ["textit"]')]:
            with self.subTest(after=after),self.assertRaises(RecordError):Policy(named_policy().replace(before,after,1))


if __name__=='__main__':unittest.main()
