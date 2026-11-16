"""Source policy regressions; synthetic text does not constitute translation data."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest

from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import validate_regions, validate_translation
from stacks_zh.records import RecordError
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import source_tex

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT/'tests/fixtures/deformations-source-policy.json').read_bytes())
SOURCE_PATH = ROOT/'tests/fixtures/deformations-math-frames.json'
SOURCE = json.loads(SOURCE_PATH.read_bytes())
BEFORE = subprocess.check_output(['git','show',FIXTURE['accepted_base']+':config/macro-policy.yml'],cwd=ROOT)

def digest(value):
    return hashlib.sha256(value).hexdigest()

class DeformationsSourcePolicyTests(unittest.TestCase):
    def test_exact_policy_delta_and_immutable_implementation_fixture(self):
        self.assertEqual(digest(BEFORE), FIXTURE['before_policy_sha256'])
        self.assertEqual(digest((ROOT/'config/macro-policy.yml').read_bytes()), FIXTURE['after_policy_sha256'])
        self.assertEqual(digest(SOURCE_PATH.read_bytes()), FIXTURE['implementation_fixture_sha256'])
        self.assertEqual(SOURCE['source_commit'], FIXTURE['source_commit'])
        self.assertTrue(SOURCE['source_only'])
        self.assertFalse(SOURCE['actual_model_data'])
        subprocess.run(['git','merge-base','--is-ancestor',FIXTURE['accepted_base'],'HEAD'],cwd=ROOT,check=True)
        old, current = Policy(BEFORE.decode()), Policy((ROOT/'config/macro-policy.yml').read_text())
        for attr in ['math_text_rules','math_text_notations','math_text_contexts','math_text_notation_contexts']:
            if not hasattr(old,attr):continue
            for key,value in getattr(old,attr).items():
                self.assertIn(key,getattr(current,attr))
                self.assertEqual(value,getattr(current,attr)[key])
        self.assertEqual(len(FIXTURE['selectors']), 88)
        self.assertEqual(FIXTURE['selectors'], [c['selector'] for c in SOURCE['containers']])

    def test_real_complete_containers_lowering_and_protected_math(self):
        harvest=Path(os.environ['HARVEST_DIR'])
        current=Containers(ROOT,harvest)
        before=Containers(ROOT,harvest,policy_bytes=BEFORE)
        self.assertEqual(current.english.commit,FIXTURE['source_commit'])
        for case in SOURCE['containers']:
            with self.subTest(selector=case['selector']):
                with self.assertRaises(RecordError) as rejected:before.select(case['selector'])
                self.assertEqual(str(rejected.exception),case['baseline_selection_error'])
                self.assertFalse(case.get('remaining_trial_error'))
                selected=current.select(case['selector'])
                self.assertEqual(selected['fragment'],case['trial_fragment'])
                self.assertEqual(selected['location'],case['trial_location'])
                units=lower_container(selected,current.policy)
                self.assertEqual([(u['unit_id'],source_tex(u)) for u in units],
                                 [(u['unit_id'],source_tex(u)) for u in case['trial_units']])
                for unit in units:
                    self.assertFalse(validate_named_schema(unit,'unit.schema.json',unit['unit_id']))
                    self.assertFalse(validate_regions(unit))
                    translated=unit['source_text']
                    for region in unit.get('math_text_regions',[]):
                        for slot in region['slots']:
                            left,right=('<'+p+'>' for p in slot['boundary_placeholders'])
                            start=translated.index(left)+len(left)
                            end=translated.index(right,start)
                            translated=translated[:start]+'合成测试文字'+translated[end:]
                    self.assertFalse(validate_translation(unit,translated))
                    regions=unit.get('math_text_regions',[])
                    if regions and regions[0]['slots']:
                        token='<'+regions[0]['slots'][0]['boundary_placeholders'][0]+'>'
                        changed=translated.replace(token,'<DAMAGED>',1)
                        self.assertTrue(validate_translation(unit,changed))

    def test_excluded_reference_and_numeric_syntax_still_blocked(self):
        native=Containers(ROOT,Path(os.environ['HARVEST_DIR']))
        for frame in SOURCE['excluded_reference_frames']:
            with self.subTest(frame=frame):
                self.assertTrue(Scanner(frame,native.policy).protect(0,len(frame))[2])
        selector=dict(file='defos.tex',owner_tag='0DIT',owner_label='defos-lemma-lift-complex',
                      parent_tag='0DIS',kind='lemma',ordinal=1)
        with self.assertRaises(RecordError) as error:native.select(selector)
        self.assertIn('romannumeral',str(error.exception))
        self.assertNotIn('locked_numeric_item_labels',native.policy.raw)
        self.assertNotIn('translatable_math_text_internal_references',native.policy.raw)

    def test_unknown_math_prose_and_changed_operator_frames_remain_locked(self):
        native=Containers(ROOT,Path(os.environ['HARVEST_DIR']))
        for frame in [r'$f\text{unknown source phrase}g$',r'$\text{Res}(Q)$',r'$\text{Cof}$',r'$\text{CofSet}$']:
            with self.subTest(frame=frame):
                self.assertTrue(Scanner(frame,native.policy).protect(0,len(frame))[2])
        for frame in [r'$S\text{-Alg}/R$',r'$\text{Mod}_R \to S\text{-Alg}/R$']:
            self.assertFalse(Scanner(frame,native.policy).protect(0,len(frame))[2])
