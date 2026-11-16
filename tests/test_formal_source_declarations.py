"""Finite locked-source frames; connectors never become mathematical names."""
import copy
import hashlib
import json
import os
import subprocess
import unittest
from pathlib import Path

from stacks_zh.source_containers import Containers, clean, lower_container
from stacks_zh.source_terms import _qualified_declaration_parts, source_projection, source_tex_hash

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT/'tests/fixtures/formal-source-declarations.json').read_text())
ORIGINAL_MACRO = subprocess.check_output(
    ['git', 'show', FIXTURE['accepted_base'] + ':config/macro-policy.yml'], cwd=ROOT)


class FormalSourceDeclarationsTests(unittest.TestCase):
    def test_complete_source_projection_is_unchanged_and_exact_cores_survive(self):
        expected = {
            'tag:06H3:statement': ['category', 'formal object', 'formal objects', 'morphism'],
            'tag:06IK:statement': ['differential', 'tangent space'],
            'tag:06JE:statement': ['lift', 'morphism of lifts'],
            'tag:06K3:statement': ['category of groupoids in functors', 'groupoid in functors',
                                  'groupoids in functors', 'morphism'],
            'tag:06KX:statement': ['presentation'],
        }
        for case in FIXTURE['cases']:
            unit = case['unit']; original = copy.deepcopy(unit)
            text, declarations = source_projection(unit)
            self.assertEqual(text, case['before_projection'][0])
            self.assertEqual(declarations, expected[unit['unit_id']])
            self.assertEqual(unit, original)
            self.assertEqual(source_tex_hash(unit), case['selected']['location']['fragment_hash'])
            self.assertFalse(case['candidate_generation'])
        self.assertFalse(FIXTURE['candidate_generation'])

    def test_every_full_frame_and_parameter_kind_payload_and_unknown_wording(self):
        a, b, c = '<MATH_0001>', '<MATH_0002>', '<MATH_0003>'
        frames = [
            (f'category {a} of formal objects of {b}', ['category', 'formal objects']),
            (f'formal object {a} of {b}', ['formal object']),
            (f'morphism {a} of formal objects', ['morphism', 'formal objects']),
            (f'tangent space of {a} at {b}', ['tangent space']),
            (f'differential {a} of {b} at {c}', ['differential']),
            (f'lift of {a} along {b}', ['lift']),
            (f'category of groupoids in functors on {a}', ['category of groupoids in functors']),
            (f'groupoid in functors on {a}', ['groupoid in functors']),
            (f'morphism {a} of groupoids in functors on {b}', ['morphism', 'groupoids in functors']),
            (f'presentation of {a} by {b}', ['presentation']),
        ]
        unit = {'placeholders': {'MATH_0001': '$x$', 'MATH_0002': r'\(y\)', 'MATH_0003': '$z$'}}
        for body, cores in frames:
            with self.subTest(frame=body):
                self.assertEqual(_qualified_declaration_parts(body, unit), cores)
                self.assertEqual(_qualified_declaration_parts(body.replace(' ', '\n  '), unit), cores)
                for changed in [body+' extra', 'unknown '+body, body.replace(a, ''),
                                body.replace(a, '<REF_0001>'), body.replace(a, '<MATH_001>')]:
                    self.assertIsNone(_qualified_declaration_parts(changed, unit))
                for payload in ['x', '$x', '$x$ trailing', '$$x$$', r'\ref{x}', r'\(x']:
                    invalid = copy.deepcopy(unit); invalid['placeholders']['MATH_0001'] = payload
                    self.assertIsNone(_qualified_declaration_parts(body, invalid))
                missing = copy.deepcopy(unit); del missing['placeholders']['MATH_0001']
                self.assertIsNone(_qualified_declaration_parts(body, missing))

    def test_unrelated_names_and_previous_qualified_contract_remain(self):
        unit = {'placeholders': {'MATH_0001': '$i$', 'MATH_0002': '$F$', 'MATH_0003': '$U$'}}
        self.assertEqual(_qualified_declaration_parts(
            'the <MATH_0001>th cohomology group of the abelian sheaf <MATH_0002> over the object <MATH_0003>', unit),
            ['cohomology group', 'abelian sheaf', 'object'])
        self.assertEqual(_qualified_declaration_parts('morphism of pseudo <MATH_0001>-torsors', unit),
                         ['morphism', 'pseudo', 'torsors'])
        for body in ['at', 'along', 'by', 'of formal objects', 'of groupoids in functors',
                     'arbitrary name of <MATH_0001> at <MATH_0002>']:
            self.assertIsNone(_qualified_declaration_parts(body, unit))

    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit read-only locked harvest')
    def test_independent_locked_git_select_and_whole_canonical_lowering(self):
        native = Containers(ROOT, Path(os.environ['HARVEST_DIR']), policy_bytes=ORIGINAL_MACRO)
        self.assertEqual(native.english.commit, FIXTURE['source_commit'])
        for case in FIXTURE['cases']:
            self.assertEqual(case['selected']['macro_policy_hash'],
                             'sha256:' + hashlib.sha256(ORIGINAL_MACRO).hexdigest())
            selected = native.select(case['selected']['selector'])
            self.assertEqual(clean(selected), case['selected'])
            unit, = [u for u in lower_container(selected,native.policy,layout='whole')
                     if u['unit_id']==case['unit']['unit_id']]
            self.assertEqual(clean(unit), case['unit'])
        native.assert_unchanged()


if __name__ == '__main__':
    unittest.main()
