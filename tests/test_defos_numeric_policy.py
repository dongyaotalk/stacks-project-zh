"""Production source policy only; no model output or review authority."""
import json
import os
import subprocess
import unittest
from pathlib import Path

from stacks_zh.extraction import Policy
from stacks_zh.numeric_item_labels import LABELS
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import byte_hash, source_tex

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / 'tests/fixtures/defos-numeric-item-labels.json'
FIXTURE = json.loads(FIXTURE_PATH.read_bytes())


@unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit locked read-only harvest')
class DefosNumericPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = Containers(ROOT, Path(os.environ['HARVEST_DIR']))
        cls.selected = cls.native.select(FIXTURE['selector'])
        cls.units = lower_container(cls.selected, cls.native.policy)

    def test_production_has_only_the_complete_finite_source_declaration(self):
        self.assertEqual(byte_hash(FIXTURE_PATH.read_bytes()),
                         'sha256:c6503234c0374bb6aa4b70f9e13353a78169009cc3cf472afc6c0e2151c825fa')
        self.assertEqual(self.native.english.commit, FIXTURE['source_commit'])
        self.assertEqual(self.native.policy.numeric_item_rules,
            {'defos-lift-complex': {'literals': list(LABELS),
             'usage': 'finite-roman-item-label', 'source_label': 'defos-lemma-lift-complex'}})
        self.assertNotIn('romannumeral', self.native.policy.commands)
        witness = self.native.policy.numeric_item_witnesses['defos-lift-complex']
        self.assertEqual(witness['blob_hash'], FIXTURE['blob_hash'])
        self.assertEqual(witness['location'], FIXTURE['inventory_coordinate']['location'])
        self.assertEqual(witness['witnesses'],
            [{'source': item['source'], 'source_hash': byte_hash(item['source']),
              'git_byte_span': item['git_byte_span']} for item in FIXTURE['witnesses']])
        self.native.assert_unchanged()

    def test_complete_production_statement_preserves_all_locked_git_bytes_and_labels(self):
        self.assertEqual(len(self.units), 1)
        unit = self.units[0]
        self.assertEqual(unit['unit_id'], 'tag:0DIT:statement')
        self.assertEqual(source_tex(unit), FIXTURE['full_source_container'])
        raw = subprocess.check_output(['git', 'show', FIXTURE['source_commit'] + ':defos.tex'],
                                      cwd=self.native.english.harvest)
        loc = FIXTURE['inventory_coordinate']['location']
        self.assertEqual(raw[loc['byte_start']:loc['byte_end']].decode(), source_tex(unit))
        self.assertEqual([v for k, v in unit['placeholders'].items() if v in LABELS], list(LABELS))
        self.assertTrue(all(k.startswith('STRUCT_') for k, v in unit['placeholders'].items() if v in LABELS))
        self.native.assert_unchanged()

    def test_complete_associated_proof_is_independently_ready(self):
        selector = {**FIXTURE['selector'], 'kind': 'proof'}
        selected = self.native.select(selector)
        units = lower_container(selected, self.native.policy)
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0]['unit_id'], 'tag:0DIT:proof')
        self.assertEqual(units[0]['parent_tag'], '0DIS')
        raw = subprocess.check_output(['git', 'show', FIXTURE['source_commit'] + ':defos.tex'],
                                      cwd=self.native.english.harvest)
        loc = selected['location']
        self.assertEqual(raw[loc['byte_start']:loc['byte_end']].decode(), source_tex(units[0]))
        self.native.assert_unchanged()


if __name__ == '__main__':
    unittest.main()
