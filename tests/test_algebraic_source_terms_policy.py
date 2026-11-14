"""Exact English ordinary-use exceptions; no candidate or glossary approval."""
import copy
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.source_terms import load_catalog, source_inventory, source_tex_hash

ROOT = Path(__file__).resolve().parents[1]
BASE = '3d26f0ba0a2c87d681f40811fb405ffdc9cbd23b'
SOURCE_HASH = 'sha256:f9c1c9a647904a3a486817b8d99256d02eb1106c101565c1caca5fccf5954126'
FIXTURE = json.loads((ROOT / 'tests/fixtures/algebraic-ordinary-source-policy.json').read_text())
CATALOG = load_catalog(ROOT)
ORIGINAL = json.loads(subprocess.check_output(['git', 'show', BASE + ':config/source-terms.json'], cwd=ROOT))

def occurrences(unit, catalog=CATALOG):
    return source_inventory(unit, catalog)['occurrences']

class AlgebraicSourceTermsPolicyTests(unittest.TestCase):
    def test_frozen_single_occurrence_proposal_and_exact_current_registration(self):
        expected = copy.deepcopy(ORIGINAL)
        expected['nonmathematical_occurrences'].append(FIXTURE['entry'])
        payload = (json.dumps(expected, ensure_ascii=False, indent=2) + '\n').encode()
        self.assertEqual('sha256:' + hashlib.sha256(payload).hexdigest(), FIXTURE['proposed_catalog_hash'])
        # The original proposal has one precise delta. Later independent
        # registrations may extend the current catalogue without rewriting it.
        self.assertEqual(CATALOG['nonmathematical_occurrences'].count(FIXTURE['entry']), 1)
        entry = FIXTURE['entry']
        self.assertEqual((entry['chapter'], entry['unit_id'], entry['source_term'],
                          entry['source_tex_hash'], entry['occurrence_index']),
                         ('algebraic', 'tag:0400:prose-0001', 'small', SOURCE_HASH, 0))
        self.assertEqual(FIXTURE['selector'], dict(file='algebraic.tex',
            owner_tag='0400', owner_label='algebraic-section-notation',
            parent_tag='0400', kind='prose_block', ordinal=1))
        self.assertFalse(FIXTURE['candidate_generation'])

    def test_complete_notation_paragraph_loses_only_typographical_small(self):
        unit = FIXTURE['unit']
        self.assertEqual(source_tex_hash(unit), SOURCE_HASH)
        self.assertIn('We use small case letters\n<MATH_0004>, <MATH_0005> for functors', unit['source_text'])
        before, after = occurrences(unit, ORIGINAL), occurrences(unit)
        self.assertEqual(before, FIXTURE['before'])
        self.assertEqual(after, FIXTURE['after'])
        self.assertEqual([item for item in before if item['source_term'] != 'small'], after)
        self.assertEqual(sum(item['source_term'] == 'small' for item in before), 1)
        self.assertTrue(any(item['source_term'] == 'categories' for item in after))
        self.assertTrue(any(item['source_term'] == 'functors' for item in after))

    def test_other_ids_chapters_hashes_and_occurrence_indices_cannot_borrow_exception(self):
        for field, value in [('unit_id', 'tag:0400:other'), ('chapter', 'categories'),
                             ('source_text', FIXTURE['unit']['source_text'] + 'A small category.\n')]:
            with self.subTest(field=field):
                changed = copy.deepcopy(FIXTURE['unit'])
                changed[field] = value
                changed = stamp_unit_hashes(changed)
                self.assertEqual(occurrences(changed), occurrences(changed, ORIGINAL))
                self.assertTrue(any(item['source_term'] == 'small' for item in occurrences(changed)))
        changed = copy.deepcopy(CATALOG)
        changed['nonmathematical_occurrences'][changed['nonmathematical_occurrences'].index(FIXTURE['entry'])]['occurrence_index'] = 1
        with self.assertRaisesRegex(RecordError, 'occurrence no longer exists'):
            occurrences(FIXTURE['unit'], changed)

    def test_mathematical_small_category_remains_required(self):
        unit = stamp_unit_hashes(dict(schema_version=1, chapter='algebraic',
            unit_id='fixture:algebraic-small-category', parent_tag='0400', node_kind='paragraph',
            source_commit=CATALOG['source_commit'], source_status='CURRENT',
            source_text='Let the category be small. A small category has a set of objects.\n',
            placeholders={}, render=dict(prefix='', suffix='')))
        self.assertEqual(occurrences(unit), occurrences(unit, ORIGINAL))
        self.assertIn('small', [item['source_term'] for item in occurrences(unit)])
        self.assertIn('small category', [item['source_term'] for item in occurrences(unit)])


    def test_complete_list_assignment_registration_is_exact(self):
        case = FIXTURE['additional_ordinary_uses'][0]
        expected = copy.deepcopy(ORIGINAL)
        expected['nonmathematical_occurrences'].extend([FIXTURE['entry'], case['entry']])
        payload = (json.dumps(expected, ensure_ascii=False, indent=2) + '\n').encode()
        self.assertEqual('sha256:' + hashlib.sha256(payload).hexdigest(), case['proposed_catalog_hash'])
        self.assertEqual(CATALOG['nonmathematical_occurrences'].count(case['entry']), 1)
        self.assertEqual(case['entry']['chapter'], 'spaces-groupoids')
        self.assertEqual(case['entry']['unit_id'], 'tag:06PB:statement')
        self.assertEqual(case['entry']['source_term'], 'set')
        self.assertEqual(case['entry']['occurrence_index'], 0)
        self.assertEqual(case['entry']['source_tex_hash'],
            'sha256:a10bd155084f1e75c29b18493b13f016fab2c77777c29d2101bfd91e5b15bd76')
        self.assertEqual(case['selected']['location']['fragment_hash'], source_tex_hash(case['unit']))
        self.assertEqual(case['selected']['source_commit'], ORIGINAL['source_commit'])
        self.assertEqual(case['selector'], dict(file='spaces-groupoids.tex', owner_tag='06PB',
            owner_label='spaces-groupoids-lemma-presentation-inertia', parent_tag='06PA',
            kind='lemma', ordinal=1))
        self.assertTrue(case['frozen_input_equality'])
        self.assertFalse(case['candidate_generation'])

    def test_complete_list_assignment_loses_only_one_ordinary_set(self):
        case = FIXTURE['additional_ordinary_uses'][0]
        unit = case['unit']
        self.assertIn('Set <MATH_0005> and set\n<STRUCT_0001>', unit['source_text'])
        before, after = occurrences(unit, ORIGINAL), occurrences(unit)
        self.assertEqual(before, case['before'])
        self.assertEqual(after, case['after'])
        self.assertEqual([v for v in before if v['source_term'] != 'set'], after)
        self.assertEqual(sum(v['source_term'] == 'set' for v in before), 1)
        self.assertEqual([unit['placeholders'][key] for key in
            ('STRUCT_0001', 'STRUCT_0002', 'STRUCT_0003', 'STRUCT_0004', 'STRUCT_0005')],
            [r'\begin{enumerate}', r'\item', r'\item', r'\item', r'\end{enumerate}'])
        self.assertTrue(any(v['source_term'] == 'quotient stack' for v in after))
        self.assertTrue(any(v['source_term'] == 'inertia stack' for v in after))

    def test_list_assignment_exception_cannot_be_borrowed(self):
        case = FIXTURE['additional_ordinary_uses'][0]
        for field, value in [('unit_id', 'tag:06PB:other'), ('chapter', 'categories'),
                             ('source_text', case['unit']['source_text'] + 'A set of objects.\n')]:
            with self.subTest(field=field):
                changed = copy.deepcopy(case['unit'])
                changed[field] = value
                changed = stamp_unit_hashes(changed)
                self.assertEqual(occurrences(changed), occurrences(changed, ORIGINAL))
                self.assertTrue(any(v['source_term'] == 'set' for v in occurrences(changed)))
        wrong = copy.deepcopy(CATALOG)
        index = wrong['nonmathematical_occurrences'].index(case['entry'])
        wrong['nonmathematical_occurrences'][index]['occurrence_index'] = 1
        with self.assertRaisesRegex(RecordError, 'occurrence no longer exists'):
            occurrences(case['unit'], wrong)

    def test_other_mathematical_set_nouns_remain_required(self):
        unit = stamp_unit_hashes(dict(schema_version=1, chapter='spaces-groupoids',
            unit_id='fixture:spaces-groupoids-set-nouns', parent_tag='06PA', node_kind='paragraph',
            source_commit=CATALOG['source_commit'], source_status='CURRENT',
            source_text='Let the set have a set of objects.\n', placeholders={},
            render=dict(prefix='', suffix='')))
        self.assertEqual(occurrences(unit), occurrences(unit, ORIGINAL))
        self.assertEqual(sum(v['source_term'] == 'set' for v in occurrences(unit)), 2)

if __name__ == '__main__':
    unittest.main()
