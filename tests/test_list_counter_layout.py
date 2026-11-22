import json
import os
from pathlib import Path
import unittest

from stacks_zh.list_counter_layout import CHAPTER, COMMAND, LABEL, parse_policy, token_end
from stacks_zh.records import RecordError
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import source_tex

ROOT = Path(__file__).resolve().parents[1]
POLICY = ('\nlocked_enumerate_continuation:\n'
          + '  source_label: ' + json.dumps(LABEL) + '\n'
          + '  literal: ' + json.dumps(COMMAND) + '\n')
SELECTOR = dict(file='algebraization.tex', kind='lemma', ordinal=1,
                owner_label=LABEL, owner_tag='0EIY', parent_tag='0EIW')


class ListCounterLayoutTests(unittest.TestCase):
    def test_policy_is_explicit_and_finite(self):
        self.assertFalse(parse_policy(''))
        self.assertTrue(parse_policy(POLICY))
        with self.assertRaises(RecordError):
            parse_policy(POLICY.replace('{6}', '{7}'))
        with self.assertRaises(RecordError):
            parse_policy(POLICY + POLICY)

    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit read-only locked harvest')
    def test_only_actual_complete_lemma_can_use_the_token(self):
        harvest = Path(os.environ['HARVEST_DIR'])
        raw = (ROOT/'config/macro-policy.yml').read_text().split('\nlocked_enumerate_continuation:\n')[0]
        base = Containers(ROOT, harvest, policy_bytes=raw.encode())
        with self.assertRaisesRegex(RecordError, 'unsupported scoped command: setcounter'):
            base.select(SELECTOR)
        current = Containers(ROOT, harvest, policy_bytes=(raw+POLICY).encode())
        selected = current.select(SELECTOR)
        units = lower_container(selected, current.policy)
        self.assertEqual(''.join(map(source_tex, units)),selected['fragment'])
        value, = [value for unit in units for value in unit['placeholders'].values() if value==COMMAND]
        self.assertEqual(value,COMMAND)
        proof = current.policy.list_counter_witness
        start = proof.index(COMMAND)
        self.assertEqual(token_end(proof,start,len(proof),CHAPTER,['enumerate'],proof),start+len(COMMAND))
        self.assertIsNone(token_end(proof,start,len(proof),CHAPTER,[],proof))
        self.assertIsNone(token_end(proof,start,len(proof),'artin',['enumerate'],proof))
        self.assertIsNone(token_end(proof.replace('{6}','{7}'),start,len(proof),CHAPTER,['enumerate'],proof))
        self.assertIsNone(token_end(COMMAND,0,len(COMMAND),CHAPTER,['enumerate'],proof))
        current.assert_unchanged()
        base.assert_unchanged()
