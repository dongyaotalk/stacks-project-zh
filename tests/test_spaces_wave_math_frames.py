"""Independent source fixtures; no model outputs, adoption or production policy."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots, nodes, validate_regions, validate_translation
from stacks_zh import math_text_spaces as spaces
from stacks_zh.math_text_descent import RELATIVE_PROJ
from stacks_zh.records import RecordError
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import source_tex
from test_source_containers import fixture, selector

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT/'tests/fixtures/spaces-wave-math-frames.json').read_text())
BASELINE_COMMIT = 'f9367dd6619828a8b1612cfdff71c887d62dbf44'
BEFORE = subprocess.check_output(
    ['git', 'show', BASELINE_COMMIT+':config/macro-policy.yml'], cwd=ROOT, text=True)


def synthetic_policy():
    # Isolate new finite capabilities from all previously registered literals.
    text = BEFORE.split('\ntranslatable_math_text:')[0]
    text = re.sub(r'(?ms)^locked_math_text_contexts:\n.*?(?=^[A-Za-z_][A-Za-z0-9_-]*:|\Z)', '', text)
    text += '\ntranslatable_math_text:\n'
    literals = dict.fromkeys(n['value'] for frame in spaces.FRAMES for n in nodes(frame)
                             if n.get('command') == 'text')
    for i, literal in enumerate(literals):
        text += f'  synthetic-{i}:\n'
        rule = dict(literal=literal, command='text', usage=spaces.USAGE,
                    source_label='test-lemma-one', witness_kind='proof', witness_ordinal=1)
        text += ''.join('    '+k+': '+json.dumps(v)+'\n' for k,v in rule.items())
    # The notation role is opt-in; no generic symbol permission.
    text = text.replace('locked_math_text_notations:\n',
        'locked_math_text_notations:\n  Spaces:\n    commands: ["textit"]\n'
        '    usages: ["spaces-category"]\n    source_label: test-lemma-one\n',1)
    return text


class SpacesWaveMathFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.proof = '\\begin{proof}\n'+'\n'.join(spaces.FRAMES)+'\n\\end{proof}'
        cls.root,cls.harvest,_ = fixture(Path(cls.temp.name),proof=cls.proof)
        (cls.root/'config/macro-policy.yml').write_text(synthetic_policy())
        cls.native = Containers(cls.root,cls.harvest)
        cls.policy = cls.native.policy

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_independent_fixture_equals_exact_finite_frame_inventory(self):
        self.assertEqual('sha256:'+hashlib.sha256(BEFORE.encode()).hexdigest(),
                         FIXTURE['baseline_macro_hash'])
        natural, category = [], []
        for c in FIXTURE['containers']:
            for frame in c['frames']:
                if 'Spaces' in frame:
                    category.append(frame)
                elif c['selector']['owner_tag'] in {'02Z8','04SG','06ER','0ADK','0ADT'} and not frame.startswith('$\\text{pr}'):
                    natural.append(frame)
        self.assertEqual(tuple(dict.fromkeys(natural)), spaces.FRAMES)
        self.assertEqual(tuple(dict.fromkeys(category)), spaces.CATEGORY_FRAMES)
        self.assertEqual(len(spaces.FRAMES),5)
        self.assertEqual(len(spaces.CATEGORY_FRAMES),34)

    def test_all_natural_leaves_are_typed_and_every_other_byte_is_locked(self):
        policy = self.policy
        for frame in spaces.FRAMES:
            with self.subTest(frame=frame):
                slots = find_slots(frame,policy.math_text_rules)
                self.assertEqual([s['value'] for s in slots],
                                 [n['value'] for n in nodes(frame) if n.get('command')=='text'])
                scanner = Scanner(frame,policy)
                protected, placeholders, errors = scanner.protect(0,len(frame))
                self.assertFalse(errors)
                self.assertTrue(scanner.math_text_regions)
                self.assertEqual(len(slots),sum(len(r['slots']) for r in scanner.math_text_regions))

    def test_full_synthetic_git_proof_lowers_and_roundtrips(self):
        for native,proof in [(self.native,self.proof)]:
                unit=lower_container(native.select(selector()),native.policy)[0]
                self.assertEqual(source_tex(unit),proof)
                self.assertEqual(validate_named_schema(unit,'unit.schema.json','unit'),[])
                self.assertEqual(validate_regions(unit),[])
                # Independent fixture text is not a generated candidate.
                translated=unit['source_text']
                for region in unit['math_text_regions']:
                    for slot in region['slots']:
                        left,right=('<'+p+'>' for p in slot['boundary_placeholders'])
                        a=translated.index(left)+len(left);b=translated.index(right,a)
                        translated=translated[:a]+'source-only fixture'+translated[b:]
                self.assertEqual(validate_translation(unit,translated),[])
                damaged=copy.deepcopy(unit)
                damaged['math_text_regions'][0]['source']+='x'
                self.assertTrue(validate_regions(damaged))

    def test_changed_math_group_command_gap_wrapper_and_unknown_text_stay_closed(self):
        policy=self.policy
        for frame in spaces.FRAMES:
            variants=[frame+'x',frame.replace('\\text{','\\textit{',1),
                      frame.replace('\\text{','{\\text{',1)+'}',
                      frame.replace('\n','\n ',1)]
            first=next(n for n in nodes(frame) if n.get('command')=='text')
            unknown=frame[:first['parameter_start']]+'unknown prose'+frame[first['parameter_end']:]
            self.assertTrue(Scanner(unknown,policy).protect(0,len(unknown))[2])
            self.assertFalse(any(s['value']=='unknown prose' for s in find_slots(unknown,policy.math_text_rules)))
            mathematical=next(n for n in nodes(frame) if re.fullmatch('[A-Za-z]',n['token']))
            variants.append(frame[:mathematical['start']]+'Z'+frame[mathematical['end']:])
            for variant in variants:
                with self.subTest(variant=variant):
                    try:
                        slots=find_slots(variant,policy.math_text_rules)
                    except ValueError:
                        slots=[]
                    self.assertEqual(slots,[])

    def test_spaces_category_is_only_an_exact_frame_not_generic_prose(self):
        policy=Policy(synthetic_policy())
        for frame in spaces.CATEGORY_FRAMES:
            protected,placeholders,errors=Scanner(frame,policy).protect(0,len(frame))
            self.assertFalse(errors,frame)
            self.assertEqual(protected,'<MATH_0001>')
            self.assertEqual(placeholders,{'MATH_0001':frame})
            for variant in [frame.replace('Spaces','Spacesx'),frame.replace('Spaces','spaces'),frame.replace('textit','text'),
                            frame.replace('Spaces',' Spaces'),frame.replace('/S','/Z').replace('/X','/Z').replace('/Y','/Z')]:
                if variant!=frame:
                    self.assertTrue(Scanner(variant,policy).protect(0,len(variant))[2],variant)
        for source in [r'$\textit{Spaces}$',r'$\textit{Spaces}/Z$',r'$A+\textit{Spaces}$']:
            self.assertTrue(Scanner(source,policy).protect(0,len(source))[2])
        for change in [('usages: ["spaces-category"]','usages: ["symbol"]'),
                       ('commands: ["textit"]\n    usages: ["spaces-category"]','commands: ["text"]\n    usages: ["spaces-category"]')]:
            with self.assertRaises(RecordError):Policy(synthetic_policy().replace(*change))

    def test_proj_preserves_old_s_and_exact_new_y_and_rejects_other_bases(self):
        policy=Policy(BEFORE)
        for source in [RELATIVE_PROJ,RELATIVE_PROJ.replace('_S(','_Y(')]:
            text,ph,errors=Scanner(source,policy).protect(0,len(source))
            self.assertFalse(errors)
            self.assertEqual(text,'<MATH_0001>')
            self.assertEqual(ph,{'MATH_0001':source})
        for source in [RELATIVE_PROJ.replace('_S(','_Z('),RELATIVE_PROJ.replace(' : ','  : '),
                       RELATIVE_PROJ.replace('\\text{Proj}','\\textit{Proj}')]:
            self.assertTrue(Scanner(source,policy).protect(0,len(source))[2])

    def test_context_pairs_are_finite_and_do_not_relax_other_literals(self):
        text=BEFORE.replace('translatable_math_text_contexts:\n',
            'translatable_math_text_contexts:\n  synthetic-context:\n'
            '    base_rule: "descent-has-property"\n    usage: "spaces-source-frames"\n'
            '    source_label: "test-lemma-one"\n    witness_kind: "proof"\n    witness_ordinal: 1\n',1)
        Policy(text)
        with self.assertRaises(RecordError):
            Policy(text.replace('base_rule: "descent-has-property"','base_rule: "descent-as-module"'))
        self.assertEqual(find_slots(r'$x\text{ has }y$',Policy(text).math_text_rules)[0]['policy_entry'],
                         'descent-has-property')


@unittest.skipUnless(os.environ.get('HARVEST_DIR'),'requires explicit read-only locked harvest')
class LockedSpacesWaveMathFramesTests(unittest.TestCase):
    def test_all_original_container_and_frame_bytes_match_locked_git(self):
        # These negative witnesses predate production registration. Current
        # positive capabilities are exercised independently above.
        native=Containers(ROOT,Path(os.environ['HARVEST_DIR']), policy_bytes=BEFORE.encode())
        self.assertEqual(native.english.commit,FIXTURE['source_commit'])
        for c in FIXTURE['containers']:
            raw=native.document(c['selector']['file'][:-4])[0];loc=c['location']
            self.assertEqual(raw[loc['byte_start']:loc['byte_end']].decode(),c['fragment'])
            for frame in c['frames']:self.assertIn(frame,c['fragment'])
            if c['selector']['owner_tag']!='0D3C':
                with self.assertRaises(RecordError):native.select(c['selector'])
