import json
import os
from pathlib import Path
import unittest

from stacks_zh.extraction import Policy
from stacks_zh.math_text import find_slots, nodes
from stacks_zh.math_text_p0 import PLAIN_USAGE, natural_rules, notation, usage
from stacks_zh.math_text_p0_catalog import SOURCE_HASHES
from stacks_zh.records import RecordError
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import source_tex

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/fixtures/p1-finite-math-selectors.json').read_bytes())
CHAPTERS = tuple(FIXTURE['chapters'])


class P1FiniteMathFrames(unittest.TestCase):
    def test_italic_text_requires_original_complete_frame(self):
        text = r'$\mathcal{F}(\emptyset) = \textit{a final object}$'
        rules = natural_rules(CHAPTERS)
        slots = find_slots(text, rules, p0_chapter='sheaves')
        self.assertEqual([(s['command'], s['value']) for s in slots], [('textit', 'a final object')])
        self.assertEqual(find_slots(text, rules, p0_chapter='schemes'), [])
        self.assertEqual(find_slots(text.replace('emptyset', 'infty'), rules, p0_chapter='sheaves'), [])
        translated = text.replace('a final object', '一个终对象')
        stream = nodes(translated)
        index = next(i for i,node in enumerate(stream) if node.get('command') == 'textit')
        self.assertIsNotNone(usage(translated, stream, index, PLAIN_USAGE))
        self.assertIsNone(usage(translated + ' ', nodes(translated + ' '), index, PLAIN_USAGE))

    def test_proj_is_a_protected_symbol_in_its_exact_frame(self):
        text = r'$\text{Proj}(S)$'
        self.assertIsNotNone(notation(text, 1, 'constructions', 'text', 'Proj'))
        self.assertIsNone(notation(text, 1, 'schemes', 'text', 'Proj'))
        self.assertIsNone(notation(text.replace('(S)', '(B)'), 1, 'constructions', 'text', 'Proj'))
        self.assertEqual(find_slots(text, natural_rules(CHAPTERS), p0_chapter='constructions'), [])

    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit locked English harvest')
    def test_every_original_blocked_container_replays_after_local_opt_in(self):
        harvest = Path(os.environ['HARVEST_DIR'])
        raw = (ROOT / 'config/macro-policy.yml').read_text()
        base = raw.split('\np0_locked_math_frames:\n', 1)[0]
        prior = Containers(ROOT, harvest, policy_bytes=base.encode())
        opt_in = '\np0_locked_math_frames:\n' + ''.join(
            f'  {chapter}: "{SOURCE_HASHES[chapter]}"\n' for chapter in CHAPTERS
        )
        updated = Containers(ROOT, harvest, policy_bytes=(base + opt_in).encode())
        self.assertEqual(updated.english.commit, FIXTURE['source_commit'])
        self.assertEqual(updated.policy.p0_verified_chapters, frozenset(CHAPTERS))
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
