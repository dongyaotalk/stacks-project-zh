"""Witnessed English chapter scope; no translation or glossary approval."""
import copy
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

from stacks_zh.records import stamp_unit_hashes
from stacks_zh.source_terms import load_catalog, source_inventory, source_tex_hash

ROOT = Path(__file__).resolve().parents[1]
BASE = '3d26f0ba0a2c87d681f40811fb405ffdc9cbd23b'
FIXTURE = json.loads((ROOT / 'tests/fixtures/groupoids-quasi-coherent-source-policy.json').read_text())
ORIGINAL = json.loads(subprocess.check_output(['git', 'show', BASE + ':config/source-terms.json'], cwd=ROOT))
CATALOG = load_catalog(ROOT)


def occurrences(unit, catalog=CATALOG):
    return source_inventory(unit, catalog)['occurrences']


class GroupoidsQuasiCoherentSourcePolicyTests(unittest.TestCase):
    def test_only_existing_concept_chapter_and_two_witnesses_are_extended(self):
        expected = copy.deepcopy(ORIGINAL)
        entry = next(v for v in expected['terms'] if v['id'] == FIXTURE['concept'])
        entry['chapters'].append('spaces-groupoids')
        entry['evidence'].extend(v['evidence'] for v in FIXTURE['witnesses'])
        payload = (json.dumps(expected, ensure_ascii=False, indent=2) + '\n').encode()
        self.assertEqual('sha256:' + hashlib.sha256(payload).hexdigest(), FIXTURE['proposed_catalog_hash'])
        # Freeze this proposal, while retaining accepted independent extensions
        # to the current production catalogue in future policy tasks.
        current = next(v for v in CATALOG['terms'] if v['id'] == FIXTURE['concept'])
        self.assertEqual(current['forms'], entry['forms'])
        self.assertTrue(set(entry['chapters']) <= set(current['chapters']))
        self.assertTrue(all(e in current['evidence'] for e in entry['evidence']))
        for witness in FIXTURE['witnesses']:
            self.assertEqual(current['evidence'].count(witness['evidence']), 1)
        self.assertFalse(FIXTURE['candidate_generation'])
        self.assertEqual([v['evidence']['source_term'] for v in FIXTURE['witnesses']],
                         ['quasi-coherent module', 'quasi-coherent modules'])

    def test_complete_lemma_witnesses_replace_only_nested_coherent_occurrence(self):
        for witness in FIXTURE['witnesses']:
            with self.subTest(selector=witness['evidence']['selector']):
                unit, = witness['units']
                evidence = witness['evidence']
                self.assertEqual(source_tex_hash(unit), evidence['fragment_hash'])
                self.assertEqual(evidence['selector'], witness['selected']['selector'])
                self.assertEqual(evidence['source_commit'], unit['source_commit'])
                before, after = occurrences(unit, ORIGINAL), occurrences(unit)
                self.assertEqual([before], witness['before'])
                self.assertEqual([after], witness['after'])
                old = [v for v in before if v['source_term'] in ('coherent module', 'coherent modules')]
                new = [v for v in after if v['concept'] == FIXTURE['concept']]
                self.assertEqual(len(old), 1)
                self.assertEqual(len(new), 1)
                self.assertEqual(new[0]['source_term'], evidence['source_term'])
                self.assertEqual(new[0]['projection_start'] + len('quasi-'), old[0]['projection_start'])
                self.assertEqual(new[0]['projection_end'], old[0]['projection_end'])
                self.assertEqual([v for v in before if v not in old],
                                 [v for v in after if v not in new])

    def test_other_chapters_do_not_borrow_new_scope(self):
        for chapter in ('algebraic', 'groupoids-quotients', 'categories', 'spaces-descent'):
            with self.subTest(chapter=chapter):
                unit = copy.deepcopy(FIXTURE['witnesses'][0]['units'][0])
                unit['chapter'] = chapter
                unit = stamp_unit_hashes(unit)
                self.assertEqual(occurrences(unit), occurrences(unit, ORIGINAL))

    def test_standalone_coherent_forms_keep_original_meaning_and_inventory(self):
        unit = stamp_unit_hashes(dict(schema_version=1, chapter='spaces-groupoids',
            unit_id='fixture:groupoids-coherent', parent_tag='0440', node_kind='paragraph',
            source_commit=CATALOG['source_commit'], source_status='CURRENT',
            source_text='A coherent module and coherent modules.\n',
            placeholders={}, render=dict(prefix='', suffix='')))
        self.assertEqual(occurrences(unit), occurrences(unit, ORIGINAL))
        self.assertEqual([v['source_term'] for v in occurrences(unit)],
                         ['coherent module', 'coherent modules'])


if __name__ == '__main__':
    unittest.main()
