"""Source-only chapter policy regressions, with independent locked Git bytes.

The fixture contains preparation witnesses, never actual model output.
Production registration requires the separately accepted tool in Issue #924.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest

from stacks_zh.extraction import Policy, Scanner, resolve_natural_math_witnesses
from stacks_zh.math_text import validate_regions
from stacks_zh.records import RecordError
from stacks_zh.source_containers import Containers, clean, lower_container
from stacks_zh.source_reextractions import source_tex

ROOT = Path(__file__).resolve().parents[1]
BASE = '8038ce359f8ecb4268632379080022038ca3c5a7'
FIXTURE = ROOT / 'tests/fixtures/sites-cohomology21-math-text-policy-20261109.json'
EXPECTED_NOTATIONS = {
    'Comp': (['text'], ['superscripted']),
    'Tot': (['text'], ['applied', 'superscripted']),
    'PMod': (['textit'], ['applied']),
    'LC': (['textit'], ['symbol']),
    'Im': (['text'], ['applied']),
    'hocolim': (['text'], ['bare-symbol']),
    'pt': (['text'], ['symbol']),
}
EXPECTED_TEXT = {
    'cohomology-for': (' for ', 'root-phrase'),
    'cohomology-isomorphism-row': (' up to isomorphism', 'matrix-row-text'),
    'cohomology-euclidean-topology': ('euclidean topology', 'root-phrase'),
    'cohomology-for-all': (' and all ', 'root-phrase'),
    'cohomology-size-where': (' where ', 'root-phrase'),
    'cohomology-size-represents': (' represents ', 'root-phrase'),
    'sites-invertible-0': ('set of invertible sheaves on ', 'sites-invertible-sheaf-matrices'),
    'sites-invertible-1': ('set of ', 'sites-invertible-sheaf-matrices'),
    'sites-invertible-2': ('-torsors', 'sites-invertible-sheaf-matrices'),
    'sites-naive-cup': ('naive cup product', 'sites-naive-cup-arrow'),
    'sites-remark-reference': (r'Remark \ref{remark-cup-product}', 'sites-cup-remark-reference'),
}


class SitesMathTextPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = Policy((ROOT / 'config/macro-policy.yml').read_text())
        cls.baseline = Policy(subprocess.check_output(
            ['git', 'show', BASE + ':config/macro-policy.yml'], cwd=ROOT, text=True))
        cls.fixture = json.loads(FIXTURE.read_text())

    def test_exact_new_rules_and_existing_policy_preservation(self):
        current, baseline = self.current, self.baseline
        for name in ('commands', 'locked_noargs', 'math', 'literal', 'metadata',
                     'body', 'accents', 'special'):
            self.assertEqual(getattr(current, name), getattr(baseline, name), name)
        added = current.math_text_notations.keys() - baseline.math_text_notations.keys()
        self.assertEqual(added, EXPECTED_NOTATIONS.keys())
        for name, (commands, usages) in EXPECTED_NOTATIONS.items():
            self.assertEqual(current.math_text_notations[name]['commands'], commands)
            self.assertEqual(current.math_text_notations[name]['usages'], usages)
            self.assertTrue(current.math_text_notations[name]['source_label'].startswith('sites-cohomology-'))
        old_notations = copy.deepcopy(current.math_text_notations)
        for name in added:
            del old_notations[name]
        self.assertEqual(old_notations['Tor']['usages'],
                         baseline.math_text_notations['Tor']['usages'] + ['bare-symbol'])
        old_notations['Tor']['usages'].remove('bare-symbol')
        self.assertEqual(old_notations, baseline.math_text_notations)
        rules = copy.deepcopy(current.math_text_rules)
        self.assertEqual(rules.keys() - baseline.math_text_rules.keys(), EXPECTED_TEXT.keys())
        for key, (literal, usage) in EXPECTED_TEXT.items():
            rule = rules.pop(key)
            self.assertEqual((rule['literal'], rule['usage'], rule['command']), (literal, usage, 'text'))
            self.assertTrue(rule['source_label'].startswith('sites-cohomology-'))
        self.assertEqual(rules, baseline.math_text_rules)
        contexts = copy.deepcopy(current.math_text_notation_contexts)
        self.assertEqual(contexts.pop('PAb'), [{
            'commands': ['textit'], 'usages': ['sites-pab-shriek'],
            'source_label': 'sites-cohomology-lemma-compute-left-derived-pi-shriek'}])
        self.assertEqual(contexts, baseline.math_text_notation_contexts)
        self.assertEqual(current.math_text_notations['PAb'], baseline.math_text_notations['PAb'])
        self.assertFalse(self.fixture['actual_model_data'])

    def test_preparation_witnesses_cover_every_new_use(self):
        expected = {(name, command, usage) for name, (commands, usages) in EXPECTED_NOTATIONS.items()
                    for command in commands for usage in usages}
        expected |= {('Tor', 'text', 'bare-symbol'), ('PAb', 'textit', 'sites-pab-shriek')}
        actual = {(x['notation'], x['command'], x['usage']) for x in self.fixture['notation_witnesses']}
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 10)
        self.assertEqual({x['policy_entry'] for x in self.fixture['text_witnesses']}, EXPECTED_TEXT.keys())
        for witness in self.fixture['text_witnesses']:
            self.assertEqual(self.current.math_text_rules[witness['policy_entry']], witness['rule'])
            self.assertTrue(witness['containers'])
        self.assertEqual({x['usage']: x['occurrences'] for x in self.fixture['notation_witnesses']
                          if x['notation'] == 'Tot'}, {'applied': 102, 'superscripted': 4})

    def test_unwitnessed_notation_and_command_variants_stay_blocked(self):
        for source, command, value in [
                (r'$\text{Tot}_{n}$', 'text', 'Tot'),
                (r'$\textit{Tot}(K)$', 'textit', 'Tot'),
                (r'$j^{\textit{PAb}}$', 'textit', 'PAb'),
                (r'$\text{Comp}(K)$', 'text', 'Comp')]:
            token = '\\' + command + '{' + value + '}'
            start = source.index(token)
            self.assertIsNone(Scanner(source, self.current).notation_usage(
                command, value, start + len(token), command_start=start), source)


@unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit read-only locked harvest')
class LockedSitesMathPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.native = Containers(ROOT, Path(os.environ['HARVEST_DIR']))
        cls.raw, cls.rows, cls.diagnostics = cls.native.document('sites-cohomology')

    def test_locked_git_full_containers_and_typed_roundtrip(self):
        self.assertEqual(self.native.english.commit, self.fixture['source_commit'])
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), self.fixture['source_blob_sha256'])
        self.assertEqual(len(self.rows), 743)
        self.assertFalse([d for d in self.diagnostics if d['kind'] == 'math-text'])
        for frozen in self.fixture['containers'].values():
            selected = self.native.select(frozen['selector'])
            for key in ('fragment', 'location', 'source_commit', 'blob_oid', 'blob_hash'):
                self.assertEqual(selected[key], frozen[key])
            location = frozen['location']
            self.assertEqual(self.raw[location['byte_start']:location['byte_end']].decode(), frozen['fragment'])
            units = [clean(u) for u in lower_container(selected, self.native.policy)]
            self.assertEqual(units, frozen['units'])
            self.assertEqual(''.join(source_tex(u) for u in units), frozen['fragment'])
            for unit in units:
                self.assertEqual(validate_regions(unit), [])

    def test_exact_notation_counts_and_utf8_command_locations(self):
        for witness in self.fixture['notation_witnesses']:
            uses = [c for row in self.rows for c in row['math_text_classifications']
                    if (c['notation'], c['command'], c['usage']) ==
                       (witness['notation'], witness['command'], witness['usage'])]
            self.assertEqual(len(uses), witness['occurrences'])
            self.assertIn(witness['classification'], uses)
            location = witness['classification']['location']
            token = self.raw[location['byte_start']:location['byte_end']]
            self.assertEqual(token.decode(), witness['classification']['source'])
            self.assertEqual('sha256:' + hashlib.sha256(token).hexdigest(), location['fragment_hash'])
        totals = [c for row in self.rows for c in row['math_text_classifications'] if c['notation'] == 'Tot']
        self.assertEqual(len(totals), 106)
        self.assertEqual({x['usage'] for x in totals}, {'applied', 'superscripted'})

    def test_complete_text_anchors_and_wrong_real_owner_rejection(self):
        for witness in self.fixture['text_witnesses']:
            self.assertEqual(self.native.policy.math_text_witnesses[witness['policy_entry']], witness['anchor'])
            for match in witness['anchor']['matches']:
                for kind in ('container', 'command'):
                    span = match[kind + '_byte_span']
                    raw = self.raw[span['start']:span['end']]
                    self.assertEqual('sha256:' + hashlib.sha256(raw).hexdigest(), match[kind + '_hash'])
        # A valid real label with the wrong complete container cannot witness the rule.
        broken = Policy(self.native.policy.raw)
        broken.math_text_rules = {'cohomology-for': copy.deepcopy(broken.math_text_rules['cohomology-for'])}
        broken.math_text_rules['cohomology-for']['source_label'] = 'sites-cohomology-lemma-compute-left-derived-pi-shriek'
        with self.assertRaises(RecordError):
            resolve_natural_math_witnesses(broken, self.native.english)


if __name__ == '__main__':
    unittest.main()
