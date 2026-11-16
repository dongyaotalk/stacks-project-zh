"""Witnessed source phrases and exact ordinary uses; no translation approval."""
import copy
import hashlib
import json
import os
import re
import subprocess
import unittest
from pathlib import Path

from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.source_terms import load_catalog, source_inventory, source_tex_hash, source_projection
from stacks_zh.source_containers import clean, lower_container

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/fixtures/criteria-source-terms-policy.json').read_text())
ORIGINAL = json.loads(subprocess.check_output(
    ['git', 'show', FIXTURE['accepted_base'] + ':config/source-terms.json'], cwd=ROOT))
CATALOG = load_catalog(ROOT)


def proposal_catalog():
    expected = copy.deepcopy(ORIGINAL)
    for case in FIXTURE['witnesses']:
        if not case['concept']:
            expected['nonmathematical_occurrences'].append(case['entry'])
        elif case.get('operation') == 'new-scoped-phrase':
            expected['terms'].append(copy.deepcopy(case['new_entry']))
            assert case['new_entry']['chapters'] == [case['unit']['chapter']]
        elif case.get('operation') == 'extend-scoped-phrase':
            entry = next(v for v in expected['terms'] if v['id'] == case['concept'])
            for field, values in case['additions'].items():
                entry[field].extend(values)
        else:
            entry = next(v for v in expected['terms'] if v['id'] == case['concept'])
            entry['forms'].append(case['source_term'])
            entry['evidence'].append(case['evidence'])
    return expected


PROPOSAL = proposal_catalog()


def occurrences(unit, catalog=CATALOG):
    return source_inventory(unit, catalog)['occurrences']


class CriteriaSourceTermsPolicyTests(unittest.TestCase):
    def test_exact_proposal_retains_all_older_forms_chapters_and_evidence(self):
        expected = proposal_catalog()
        for previous in expected['terms']:
            current = next(term for term in CATALOG['terms'] if term['id'] == previous['id'])
            for key, value in previous.items():
                if key in {'forms', 'chapters', 'evidence'}:
                    self.assertEqual(current[key][:len(value)], value)
                    if key == 'chapters' and not value:
                        self.assertEqual(current[key], value)
                else:
                    self.assertEqual(current[key], value)
        for entry in expected['nonmathematical_occurrences']:
            self.assertIn(entry, CATALOG['nonmathematical_occurrences'])
        payload = (json.dumps(expected, ensure_ascii=False, indent=2) + '\n').encode()
        self.assertEqual('sha256:' + hashlib.sha256(payload).hexdigest(), FIXTURE['proposed_catalog_hash'])
        self.assertFalse(FIXTURE['candidate_generation'])

    def test_complete_locked_witnesses_and_only_intended_inventory_delta(self):
        grouped = {}
        for case in FIXTURE['witnesses']:
            unit, selected = case['unit'], case['selected']
            self.assertEqual(source_tex_hash(unit), selected['location']['fragment_hash'])
            self.assertEqual(unit['source_commit'], FIXTURE['source_commit'])
            self.assertEqual(case['selector'], selected['selector'])
            self.assertTrue(case['frozen_input_equality'] or case.get('preparation_input_equality', False))
            self.assertFalse(case['candidate_generation'])
            self.assertEqual(occurrences(unit, ORIGINAL), case['before'])
            self.assertEqual(occurrences(unit, PROPOSAL), case['after'])
            grouped.setdefault(unit['unit_id'], []).append(case)
        for uid, cases in grouped.items():
            before, after = cases[0]['before'], cases[0]['after']
            chapter = cases[0]['unit']['chapter']
            authorised = {c['source_term'] for c in FIXTURE['witnesses'] if c['concept']
                          and (not next(t for t in PROPOSAL['terms'] if t['id'] == c['concept'])['chapters']
                               or chapter in next(t for t in PROPOSAL['terms'] if t['id'] == c['concept'])['chapters'])}
            replacements = [v for v in after if v['source_term'] in authorised]
            removed = [v for v in before if any(
                n['projection_start'] <= v['projection_start'] < v['projection_end'] <= n['projection_end']
                for n in replacements)]
            for case in cases:
                if not case['concept']:
                    projection, _ = source_projection(case['unit'])
                    matches = list(re.finditer(r'\b' + re.escape(case['source_term']) + r'\b', projection))
                    match = matches[case['entry']['occurrence_index']]
                    exact = [v for v in before if v['source_term'] == case['source_term']
                             and v['projection_start'] == match.start() and v['projection_end'] == match.end()]
                    self.assertEqual(len(exact), 1)
                    removed += exact
            with self.subTest(unit=uid):
                self.assertEqual([v for v in before if v not in removed],
                                 [v for v in after if v not in replacements])
                for case in cases:
                    if case['concept']:
                        self.assertTrue(any(v['source_term'] == case['source_term'] for v in replacements))
                    else:
                        self.assertEqual(len([v for v in removed if v['source_term'] == case['source_term']]), 1)

    def test_ordinary_uses_are_bound_to_complete_id_hash_and_index(self):
        cases = [c for c in FIXTURE['witnesses'] if not c['concept']]
        self.assertEqual([(c['unit']['unit_id'], c['source_term']) for c in cases],
                         [('tag:06PK:proof', 'small'), ('tag:06G8:prose-0001', 'Stacks'), ('tag:08LF:statement', 'Set'), ('tag:06SE:proof', 'Set'), ('tag:08U8:proof', 'Set'), ('tag:08MM:statement', 'Set'), ('tag:08UG:proof', 'Set'), ('tag:0DIT:proof', 'set')])
        for case in cases:
            entry = case['entry']
            self.assertEqual(entry['occurrence_index'], 1 if case['unit']['unit_id'] in {'tag:08LF:statement', 'tag:08MM:statement', 'tag:0DIT:proof'} else 0)
            for field, value in [('unit_id', 'fixture:other-id'), ('chapter', 'algebraic'),
                                 ('source_text', case['unit']['source_text'] + ' Changed source.\n')]:
                changed = copy.deepcopy(case['unit'])
                changed[field] = value
                changed = stamp_unit_hashes(changed)
                with self.subTest(term=case['source_term'], field=field):
                    self.assertTrue(any(v['source_term'] == case['source_term'] for v in occurrences(changed)))
            wrong = copy.deepcopy(CATALOG)
            wrong['nonmathematical_occurrences'][wrong['nonmathematical_occurrences'].index(entry)]['occurrence_index'] = 99
            with self.assertRaisesRegex(RecordError, 'occurrence no longer exists'):
                occurrences(case['unit'], wrong)

    def test_independent_terms_and_unwitnessed_spellings_keep_existing_rules(self):
        unit = stamp_unit_hashes(dict(schema_version=1, chapter='criteria',
            unit_id='fixture:criteria-independent-terms', parent_tag='06PI', node_kind='paragraph',
            source_commit=CATALOG['source_commit'], source_status='CURRENT',
            source_text='A sheaf, sheaves, a stack, stacks, a presheaf, presheaves, a Hilbert stack, '
                        'a small category and a small set.\n',
            placeholders={}, render=dict(prefix='', suffix='')))
        self.assertEqual(occurrences(unit), occurrences(unit, ORIGINAL))
        for case in FIXTURE['witnesses']:
            if case.get('operation') == 'new-scoped-phrase':
                other = copy.deepcopy(case['unit'])
                other['chapter'] = 'algebraic'
                other = stamp_unit_hashes(other)
                self.assertFalse(any(v['concept'] == case['concept'] for v in occurrences(other)))
        unit['source_text'] = 'A pre-sheaf and pre-sheafification.\n'
        unit = stamp_unit_hashes(unit)
        self.assertEqual(occurrences(unit), occurrences(unit, ORIGINAL))

    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit read-only locked harvest')
    def test_independent_locked_git_select_and_canonical_lowering(self):
        from stacks_zh.source_containers import Containers
        native = Containers(ROOT, Path(os.environ['HARVEST_DIR']))
        checked = {}
        for case in FIXTURE['witnesses']:
            key = json.dumps(case['selector'], sort_keys=True)
            if key not in checked:
                selected = native.select(case['selector'])
                self.assertEqual(clean(selected), clean(case['selected']))
                checked[key] = lower_container(selected, native.policy, layout='whole')
            unit, = [u for u in checked[key] if u['unit_id'] == case['unit']['unit_id']]
            self.assertEqual(clean(unit), case['unit'])


if __name__ == '__main__':
    unittest.main()
