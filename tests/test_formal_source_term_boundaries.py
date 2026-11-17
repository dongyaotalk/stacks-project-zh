"""Six complete source witnesses; finite catalogue delta, never glossary approval."""
import copy
import hashlib
import json
import os
import subprocess
import unittest
from pathlib import Path

from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.source_containers import Containers, clean, lower_container
from stacks_zh.source_terms import load_catalog, source_inventory, source_tex_hash

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/fixtures/formal-source-term-boundaries.json').read_bytes())
ORIGINAL_BYTES = subprocess.check_output(['git', 'show', FIXTURE['accepted_base'] + ':config/source-terms.json'], cwd=ROOT)
ORIGINAL = json.loads(ORIGINAL_BYTES)
PROPOSAL = copy.deepcopy(ORIGINAL)
for case in FIXTURE['cases']:
    if 'complete_phrase_entry' in case:
        PROPOSAL['terms'].append(case['complete_phrase_entry'])
    else:
        PROPOSAL['nonmathematical_occurrences'].append(case['ordinary_exclusion'])
CATALOG = load_catalog(ROOT)
EXPECTED = {
    'tag:06GK:statement': 'sha256:8b2f75316fe40a02ec53abddcd849018af2ec81b11ae6e9ad882382f4c78e7f0',
    'tag:06J2:statement': 'sha256:07a60748c9a19027b5cb346ba85c590f3483423ed0ad7968921584b4e2013669',
    'tag:06IU:proof': 'sha256:ad7723cdc18ad0e9deaa3cd4e173af55411c6cfac30fd6c3fce36efa3f7f8225',
    'tag:06T0:prose-0001': 'sha256:91ee6656194ccb542d74ee6912e5fc603f8eb8dbc859507864da52935cc5d67e',
    'tag:06KN:proof': 'sha256:68eda9a71a0466cdaed7c5c3341f99493069985b6021e886a3e3c20d572eda64',
    'tag:06HW:statement': 'sha256:5ea389a8d4b932bd6d4cbce5fedb5863c5a33a15549c9382906b64866e580f47',
}

def occurrences(unit, catalog):
    return source_inventory(unit, catalog)['occurrences']

class FormalSourceTermBoundariesTests(unittest.TestCase):
    def test_exact_frozen_increment_and_current_preservation(self):
        self.assertEqual('sha256:' + hashlib.sha256(ORIGINAL_BYTES).hexdigest(), FIXTURE['original_catalog_hash'])
        payload = (json.dumps(PROPOSAL, ensure_ascii=False, indent=2) + '\n').encode()
        self.assertEqual('sha256:' + hashlib.sha256(payload).hexdigest(), FIXTURE['proposal_catalog_hash'])
        self.assertEqual(PROPOSAL['terms'][:-2], ORIGINAL['terms'])
        self.assertEqual(PROPOSAL['nonmathematical_occurrences'][:-4], ORIGINAL['nonmathematical_occurrences'])
        self.assertEqual([entry['forms'] for entry in PROPOSAL['terms'][-2:]], [['condition (RS)'], ['conditions (S1) and (S2)']])
        self.assertTrue(all(entry['chapters'] == ['formal-defos'] for entry in PROPOSAL['terms'][-2:]))
        self.assertEqual({c['unit']['unit_id'] for c in FIXTURE['cases']}, set(EXPECTED))
        for old in PROPOSAL['terms']:
            current = next(c for c in CATALOG['terms'] if c['id'] == old['id'])
            for key, value in old.items():
                if key in {'forms', 'chapters', 'evidence'}:
                    self.assertEqual(current[key][:len(value)], value)
                    if key == 'chapters' and not value:
                        self.assertEqual(current[key], value)
                else:
                    self.assertEqual(current[key], value)
        for old in PROPOSAL['nonmathematical_occurrences']:
            self.assertIn(old, CATALOG['nonmathematical_occurrences'])
        self.assertFalse(FIXTURE['candidate_generation'])
        self.assertFalse(FIXTURE['human_approval'])

    def test_only_declared_occurrences_change(self):
        for c in FIXTURE['cases']:
            u = c['unit']
            self.assertEqual(source_tex_hash(u), EXPECTED[u['unit_id']])
            self.assertEqual(c['source_tex_hash'], EXPECTED[u['unit_id']])
            before, after = occurrences(u, ORIGINAL), occurrences(u, PROPOSAL)
            self.assertEqual(before, c['before_inventory']['occurrences'])
            self.assertEqual(after, c['proposed_inventory']['occurrences'])
            removed, added = [o for o in before if o not in after], [o for o in after if o not in before]
            self.assertEqual(len(removed), 1)
            if 'ordinary_exclusion' in c:
                self.assertEqual(removed[0]['source_term'], c['ordinary_exclusion']['source_term'])
                self.assertEqual(added, [])
                self.assertEqual(after, [o for o in before if o != removed[0]])
            else:
                self.assertEqual(len(added), 1)
                complete = c['complete_phrase_entry']['forms'][0]
                self.assertEqual(removed[0]['source_term'], complete[:-1])
                self.assertEqual(added[0]['source_term'], complete)
                self.assertEqual(added[0]['projection_start'], removed[0]['projection_start'])
                self.assertEqual(added[0]['projection_end'], removed[0]['projection_end'] + 1)
                self.assertEqual([o for o in before if o != removed[0]], [o for o in after if o != added[0]])

    def test_wrong_identity_hash_case_or_index_cannot_borrow_exclusion(self):
        for c in FIXTURE['cases']:
            if 'ordinary_exclusion' not in c:
                continue
            for key, value in [('chapter', 'algebraic'), ('unit_id', 'fixture:wrong'), ('source_tex_hash', 'sha256:' + '0' * 64), ('source_term', c['ordinary_exclusion']['source_term'].swapcase()), ('occurrence_index', 9)]:
                catalog = copy.deepcopy(ORIGINAL)
                entry = copy.deepcopy(c['ordinary_exclusion']); entry[key] = value
                catalog['nonmathematical_occurrences'].append(entry)
                with self.subTest(unit=c['unit']['unit_id'], key=key):
                    if key in {'source_term', 'occurrence_index'}:
                        with self.assertRaisesRegex(RecordError, 'nonmathematical source occurrence no longer exists'):
                            occurrences(c['unit'], catalog)
                    else:
                        self.assertEqual(occurrences(c['unit'], catalog), occurrences(c['unit'], ORIGINAL))

    def test_set_nouns_and_other_chapters_keep_original_requirements(self):
        c = next(c for c in FIXTURE['cases'] if c['unit']['unit_id'] == 'tag:06GK:statement')
        self.assertEqual(sum(o['source_term'] == 'set' for o in occurrences(c['unit'], PROPOSAL)), 2)
        for c in FIXTURE['cases']:
            u = copy.deepcopy(c['unit']); u['chapter'] = 'algebraic'; u = stamp_unit_hashes(u)
            self.assertEqual(occurrences(u, PROPOSAL), occurrences(u, ORIGINAL))

    def test_complete_phrase_never_exposes_protected_math(self):
        for c in FIXTURE['cases']:
            if 'complete_phrase_entry' not in c:
                continue
            with self.subTest(unit=c['unit']['unit_id']):
                phrase = c['complete_phrase_entry']['forms'][0]
                u = copy.deepcopy(c['unit']); u['unit_id'] = 'fixture:protected-condition'
                u['schema_version'] = 1
                for key in ('math_text_regions', 'math_text_components'):
                    u.pop(key, None)
                u['source_text'] = '<MATH_0001>\n'; u['placeholders'] = {'MATH_0001': '$\\text{' + phrase + '}$'}
                u['render'] = {'prefix': '', 'suffix': ''}; u = stamp_unit_hashes(u)
                self.assertEqual(occurrences(u, PROPOSAL), occurrences(u, ORIGINAL))

    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit locked read-only harvest')
    def test_complete_locked_git_selection_and_lowering_equal_frozen_units(self):
        native = Containers(ROOT, Path(os.environ['HARVEST_DIR']))
        self.assertEqual(native.english.commit, FIXTURE['source_commit'])
        for c in FIXTURE['cases']:
            selected = native.select(c['selector'])
            self.assertEqual(clean(selected), c['selected'])
            self.assertEqual(selected['location']['fragment_hash'], EXPECTED[c['unit']['unit_id']])
            actual = next(u for u in lower_container(selected, native.policy) if u['unit_id'] == c['unit']['unit_id'])
            self.assertEqual(clean(actual), c['unit'])
        native.assert_unchanged()

if __name__ == '__main__':
    unittest.main()
