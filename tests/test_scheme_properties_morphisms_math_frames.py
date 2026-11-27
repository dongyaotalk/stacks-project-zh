import json
import os
from pathlib import Path
import unittest

from stacks_zh.math_text import find_slots
from stacks_zh.math_text_p0 import natural_rules, notation
from stacks_zh.math_text_p0_catalog import SOURCE_HASHES
from stacks_zh.records import RecordError
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import source_tex

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads(
    (ROOT / 'tests/fixtures/scheme-properties-morphisms-math-selectors.json').read_bytes()
)
CHAPTERS = tuple(FIXTURE['chapters'])


class SchemePropertiesMorphismsMathFrames(unittest.TestCase):
    def test_rank_stays_protected_in_the_exact_formula(self):
        frame = r'$$' + '\n' + r'\text{rank}_x(\Omega_{X/S}) = \dim_x(X_{f(x)})' + '\n$$'
        start = frame.index(r'\text')
        self.assertIsNotNone(notation(frame, start, 'morphisms', 'text', 'rank'))
        self.assertIsNone(notation(frame, start, 'properties', 'text', 'rank'))
        self.assertIsNone(notation(frame.replace('Omega', 'omega'), start, 'morphisms', 'text', 'rank'))
        self.assertEqual(find_slots(frame, natural_rules(CHAPTERS), p0_chapter='morphisms'), [])

    def test_multiple_natural_language_parameters_are_independent(self):
        frame = ('$$\n' + r'\begin{matrix}'
                 '\n' + r'\text{Schemes affine} \\'
                 '\n' + r'\text{over }S'
                 '\n' + r'\end{matrix}'
                 '\n' + r'\longleftrightarrow'
                 '\n' + r'\begin{matrix}'
                 '\n' + r'\text{quasi-coherent sheaves} \\'
                 '\n' + r'\text{of }\mathcal{O}_S\text{-algebras}'
                 '\n' + r'\end{matrix}' + '\n$$')
        rules = natural_rules(CHAPTERS)
        slots = find_slots(frame, rules, p0_chapter='morphisms')
        self.assertEqual([slot['value'] for slot in slots],
                         ['Schemes affine', 'over ', 'quasi-coherent sheaves', 'of ', '-algebras'])
        self.assertEqual(find_slots(frame.replace('mathcal', 'mathrm'), rules, p0_chapter='morphisms'), [])
        self.assertEqual(find_slots(frame, rules, p0_chapter='properties'), [])

    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit locked English harvest')
    def test_locked_source_containers_replay_with_explicit_registration(self):
        harvest = Path(os.environ['HARVEST_DIR'])
        raw = (ROOT / 'config/macro-policy.yml').read_text()
        registered = ''.join(f'  {chapter}: "{SOURCE_HASHES[chapter]}"\n' for chapter in CHAPTERS)
        unregistered = raw
        for registration in registered.splitlines(keepends=True):
            unregistered = unregistered.replace(registration, '')
        header = 'p0_locked_math_frames:\n'
        policy = unregistered.replace(header, header + registered)
        prior = Containers(ROOT, harvest, policy_bytes=unregistered.encode())
        updated = Containers(ROOT, harvest, policy_bytes=policy.encode())
        self.assertEqual(updated.english.commit, FIXTURE['source_commit'])
        self.assertTrue(set(CHAPTERS) <= updated.policy.p0_verified_chapters)
        for chapter, group in FIXTURE['chapters'].items():
            for selector in group['selectors']:
                with self.subTest(chapter=chapter, tag=selector['owner_tag'], kind=selector['kind']):
                    with self.assertRaisesRegex(RecordError, 'text inside locked math'):
                        lower_container(prior.select(selector), prior.policy)
                    selected = updated.select(selector)
                    units = lower_container(selected, updated.policy)
                    self.assertEqual(''.join(map(source_tex, units)), selected['fragment'])
        prior.assert_unchanged()
        updated.assert_unchanged()
