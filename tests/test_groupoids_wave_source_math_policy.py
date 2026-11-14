"""Locked English policy deltas and replay; no actual model or review data."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import unittest

from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import validate_regions, validate_translation, find_slots
from stacks_zh.records import stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, clean, lower_container
from stacks_zh.source_reextractions import byte_hash, source_tex

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT/'tests/fixtures/groupoids-wave-source-math-policy.json').read_text())
CURRENT = (ROOT/'config/macro-policy.yml').read_text()


def entries(text, section):
    body = re.search(r'(?ms)^'+section+r':\n(.*?)(?=^[A-Za-z_][A-Za-z0-9_-]*:|\Z)', text)
    return {m[1]: m[0] for m in re.finditer(
        r'(?ms)^  ([^\s:]+):\n.*?(?=^  [^\s:]+:|\Z)', body[1])}


class GroupoidsProductionPolicyTests(unittest.TestCase):
    def test_exact_policy_delta_reconstructs_accepted_original_bytes(self):
        before, after = FIXTURE['macro_before'], FIXTURE['macro_after']
        original = subprocess.check_output(['git','show',FIXTURE['accepted_tool_main']+
            ':config/macro-policy.yml'], cwd=ROOT).decode()
        self.assertEqual(before, original)
        self.assertEqual(byte_hash(before), FIXTURE['macro_before_hash'])
        self.assertEqual(byte_hash(after), FIXTURE['macro_after_hash'])
        self.assertFalse(FIXTURE['actual_model_data'])
        self.assertTrue(FIXTURE['source_only'])
        restored = after
        counts = {}
        for section, delta in FIXTURE['added_blocks'].items():
            old, new, current = [entries(t,section) for t in (before,after,CURRENT)]
            self.assertEqual(set(new)-set(old), set(delta))
            for key, value in old.items():
                self.assertEqual(new[key], value)
                self.assertEqual(current[key], value)
            for key, value in delta.items():
                self.assertEqual(new[key], value)
                self.assertEqual(current[key], value)
                self.assertEqual(restored.count(value), 1)
                restored = restored.replace(value,'',1)
            counts[section] = len(delta)
        self.assertEqual(counts, dict(locked_math_text_notations=1,
            translatable_math_text=15, translatable_math_text_contexts=5))
        self.assertEqual(restored, before)

    def test_new_roles_do_not_authorize_changed_fonts_or_complete_frames(self):
        frames = json.loads((ROOT/'tests/fixtures/groupoids-wave-math-frames.json').read_text())
        policy = Policy(CURRENT)
        for frame in frames['cqc_frames']:
            self.assertFalse(Scanner(frame,policy).protect(0,len(frame))[2])
            for variant in (frame.replace('textit','text'),frame.replace('(X)','(Y)')):
                self.assertTrue(Scanner(variant,policy).protect(0,len(variant))[2])
        for frame in frames['italic_frames']:
            self.assertTrue(any(s['value']=='Algebraic-Stacks'
                and s['usage']=='algebraic-stack-category-phrase'
                for s in find_slots(frame,policy.math_text_rules)))
            for variant in (frame.replace('textit','textbf'),frame.replace('/S','/Z')):
                self.assertTrue(Scanner(variant,policy).protect(0,len(variant))[2])
        for frame in frames['natural_frames']:
            for variant in (frame+'x',frame.replace('\n','\n ',1)):
                self.assertFalse(any(s['usage']=='groupoids-wave-source-frames'
                    for s in find_slots(variant,policy.math_text_rules)))


@unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit read-only locked harvest')
class LockedGroupoidsProductionPolicyTests(unittest.TestCase):
    def test_all_seventeen_complete_containers_roundtrip_schema_and_typed_guard(self):
        from test_groupoids_wave_math_frames import synthetic_fields
        native = Containers(ROOT, Path(os.environ['HARVEST_DIR']))
        self.assertEqual(native.english.commit, FIXTURE['source_commit'])
        counts = {}
        for case in FIXTURE['containers']:
            with self.subTest(selector=case['selector']):
                selected = native.select(case['selector'])
                self.assertEqual(selected['fragment'], case['fragment'])
                self.assertEqual(selected['location']['fragment_hash'],case['fragment_hash'])
                raw = native.document(case['chapter'])[0]
                self.assertEqual(byte_hash(raw),case['source_blob_hash'])
                a,b = [case['source_byte_span'][k] for k in ('start','end')]
                self.assertEqual(raw[a:b].decode(), case['fragment'])
                units = lower_container(selected, native.policy)
                self.assertEqual(''.join(source_tex(u) for u in units), case['fragment'])
                for unit in units:
                    self.assertEqual(validate_named_schema(unit,'unit.schema.json','source only'),[])
                    self.assertEqual(validate_regions(unit),[])
                    self.assertEqual(validate_translation(unit,synthetic_fields(unit)['translation']),[])
                counts[case['chapter']] = counts.get(case['chapter'],0)+1
        self.assertEqual(counts,{'spaces-groupoids':6,'groupoids-quotients':6,'algebraic':5})
        registered = {key for key in native.policy.math_text_witnesses if key.startswith('groupoids-wave-')}
        self.assertEqual(len(registered),20)

    def test_existing_spaces_sources_change_only_existing_policy_witness_hashes(self):
        old_fixture = json.loads((ROOT/'tests/fixtures/spaces-wave-source-policy.json').read_text())
        harvest = Path(os.environ['HARVEST_DIR'])
        historical = Containers(ROOT,harvest,policy_bytes=old_fixture['macro_after'].encode())
        current = Containers(ROOT,harvest)
        for case in old_fixture['math_source_preparations']:
            with self.subTest(selector=case['selector']):
                old = historical.select(case['selector'])
                new = current.select(case['selector'])
                self.assertEqual(new['fragment'],old['fragment'])
                previous = [clean(u) for u in lower_container(old,historical.policy)]
                actual = [clean(u) for u in lower_container(new,current.policy)]
                self.assertEqual(previous,case['units'])
                expected = copy.deepcopy(previous)
                for unit in expected:
                    for region in unit.get('math_text_regions',[]):
                        for slot in region['slots']:
                            slot['classification_witness']['policy_hash'] = byte_hash(CURRENT)
                    unit.update(stamp_unit_hashes(unit))
                self.assertEqual(actual,expected)
                self.assertEqual(''.join(source_tex(u) for u in actual),new['fragment'])


if __name__=='__main__':
    unittest.main()
