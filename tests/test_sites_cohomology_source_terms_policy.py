"""Chapter-scoped source policy and locked Git witnesses; no translation facts.

Candidates below are synthetic term-display lists used only by the validator.
"""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import unittest

from stacks_zh.records import expected_unit_hashes
from stacks_zh.source_terms import (load_catalog, source_inventory,
    validate_catalog_evidence, validate_source_terms)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/sites-cohomology21-source-terms-policy.json'
BASE = '8038ce359f8ecb4268632379080022038ca3c5a7'
ACCEPTED_SITES_BOUNDARY = '5400f3d19bf86fc59807e8dfa3d69d4429910ad3'


def normalized_inventory(unit, catalog):
    result = source_inventory(unit, catalog)
    result.pop('catalog_hash')
    return result


def synthetic_display(unit, catalog):
    terms = [{'source_term': x['source_term'], 'target_term': '合成测试术语'}
             for x in source_inventory(unit, catalog)['occurrences']]
    return dict(translation=' '.join(f"{x['target_term']}（{x['source_term']}）" for x in terms),
                term_occurrences=terms,
                unknown_terms=[dict(**x, context='Synthetic validator fixture; not a translation.') for x in terms],
                term_status='DECISION_REQUIRED')


class SitesSourceTermsPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.current = load_catalog(ROOT)
        cls.baseline = json.loads(subprocess.check_output(
            ['git', 'show', BASE + ':config/source-terms.json'], cwd=ROOT, text=True))

    def test_only_appended_scoped_entries(self):
        # The accepted sites delta is immutable; later scoped extensions retain it.
        original = json.loads(subprocess.check_output(
            ['git', 'show', ACCEPTED_SITES_BOUNDARY + ':config/source-terms.json'], cwd=ROOT, text=True))
        current_by_id = {term['id']: term for term in self.current['terms']}
        for entry in self.fixture['entries']:
            self.assertEqual(current_by_id[entry['id']], entry)
        added = original['terms'][len(self.baseline['terms']):]
        self.assertEqual(added, self.fixture['entries'])
        self.assertEqual(len(added), 5)
        self.assertTrue(all(x['chapters'] == ['sites-cohomology'] for x in added))
        del original['terms'][len(self.baseline['terms']):]
        self.assertEqual(original, self.baseline)
        self.assertFalse(self.fixture['actual_model_data'])

    def test_accepted_base_2947_unit_inventories_unchanged(self):
        count = 0
        archive = subprocess.check_output(['git', 'archive', BASE, 'translation-data/units'], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(archive)) as files:
            for member in files:
                if not member.isfile() or not member.name.endswith('.jsonl'):
                    continue
                for line in files.extractfile(member).read().splitlines():
                    if not line.strip():
                        continue
                    unit = json.loads(line)
                    count += 1
                    self.assertEqual(normalized_inventory(unit, self.current),
                                     normalized_inventory(unit, self.baseline), unit['unit_id'])
        self.assertEqual(count, 2947)

    def test_new_full_words_cover_real_source_without_splitting(self):
        for witness in self.fixture['witnesses']:
            unit = witness['unit']
            with self.subTest(form=witness['form']):
                required = [x['source_term'] for x in source_inventory(unit, self.current)['occurrences']]
                self.assertIn(witness['actual'], required)
                display = synthetic_display(unit, self.current)
                self.assertEqual(validate_source_terms(unit, display, self.current), [])
                self.assertTrue(any('missing source-side term coverage' in x
                                    for x in validate_source_terms(unit, display, self.baseline)))
                missing = copy.deepcopy(display)
                index = next(i for i,x in enumerate(missing['term_occurrences'])
                             if x['source_term'] == witness['actual'])
                del missing['term_occurrences'][index]
                self.assertTrue(any('missing source-side term coverage' in x
                                    for x in validate_source_terms(unit, missing, self.current)))

    def test_other_chapters_keep_old_requirements(self):
        for witness in self.fixture['witnesses']:
            unit = copy.deepcopy(witness['unit'])
            unit['chapter'] = 'categories'  # Synthetic scope comparison only.
            self.assertEqual(normalized_inventory(unit, self.current),
                             normalized_inventory(unit, self.baseline))

    def test_full_chapter_reference_retains_mathematical_algebra_elsewhere(self):
        witness = next(x for x in self.fixture['witnesses'] if x['form'] == 'More on Algebra')
        unit = witness['unit']
        required = [x['source_term'] for x in source_inventory(unit, self.current)['occurrences']]
        self.assertIn('More on Algebra', required)
        self.assertEqual(unit['placeholders']['REF_0001'], r'\ref{more-algebra-section-sign-rules}')
        synthetic = copy.deepcopy(unit)
        synthetic['unit_id'] = 'synthetic:source-term-algebra'
        synthetic['source_text'] = 'Let <MATH_0001> be an algebra. More on Algebra, Section <REF_0001>.'
        synthetic.update(expected_unit_hashes(synthetic))
        required = [x['source_term'] for x in source_inventory(synthetic, self.current)['occurrences']]
        self.assertEqual(required, ['algebra', 'More on Algebra'])

    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit read-only locked harvest')
    def test_independent_complete_locked_source_witnesses_and_negatives(self):
        from stacks_zh.source_containers import Containers
        harvest = Path(os.environ['HARVEST_DIR'])
        native = Containers(ROOT, harvest)
        subset = copy.deepcopy(self.current)
        subset['terms'] = copy.deepcopy(self.fixture['entries'])
        subset.pop('nonmathematical_chapters', None)
        subset.pop('nonmathematical_occurrences', None)
        for witness in self.fixture['witnesses']:
            selected = native.select(witness['selector'])
            self.assertEqual(selected['fragment'], witness['fragment'])
            self.assertEqual(selected['location'], witness['location'])
            self.assertEqual(selected['blob_oid'], witness['blob_oid'])
            self.assertEqual(selected['blob_hash'], witness['blob_hash'])
        _, errors = validate_catalog_evidence(ROOT, subset, [], harvest, containers=native)
        self.assertEqual(errors, [])
        for change in ('hash', 'selector', 'word'):
            broken = copy.deepcopy(subset)
            evidence = broken['terms'][0]['evidence'][0]
            if change == 'hash':
                evidence['fragment_hash'] = 'sha256:' + '0' * 64
            elif change == 'selector':
                evidence['selector']['owner_tag'] = '0000'
            else:
                evidence['source_term'] = 'unwitnessed source compound'
            _, errors = validate_catalog_evidence(ROOT, broken, [], harvest, containers=native)
            self.assertTrue(errors, change)


if __name__ == '__main__':
    unittest.main()
