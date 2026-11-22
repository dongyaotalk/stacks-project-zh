from collections import defaultdict
import json
import os
from pathlib import Path
import unittest

from stacks_zh.extraction import Policy
from stacks_zh.math_text import find_slots, nodes
from stacks_zh.math_text_p0 import (
    COMPONENT_USAGE, ETALE_SEPARATOR, PLAIN_USAGE, notation, source_match, usage,
    natural_rules, policy_chapters,
)
from stacks_zh.math_text_p0_catalog import SOURCE_HASHES
from stacks_zh.records import RecordError
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import byte_hash, source_tex

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT/'tests/fixtures/p0-finite-math-frames.json').read_bytes())
OPT_IN = '\np0_locked_math_frames:\n' + ''.join(
    f'  {chapter}: "{digest}"\n' for chapter, digest in SOURCE_HASHES.items()
)


class P0FiniteMathFrames(unittest.TestCase):
    def test_explicit_policy_enables_only_exact_source_chapter(self):
        base = (ROOT/'config/macro-policy.yml').read_text().split('\np0_locked_math_frames:\n')[0]
        self.assertFalse(Policy(base).p0_frame_chapters)
        selected = policy_chapters(OPT_IN)
        self.assertEqual(selected, frozenset(SOURCE_HASHES))
        self.assertEqual(Policy(base+OPT_IN).p0_frame_chapters, selected)
        with self.assertRaises(ValueError):
            policy_chapters(OPT_IN.replace('sha256:', 'md5:', 1))
        with self.assertRaises(ValueError):
            policy_chapters(OPT_IN + OPT_IN)

    def test_roles_require_exact_source_and_distinguish_symbols_from_prose(self):
        all_rules = natural_rules(SOURCE_HASHES)
        for occurrence in FIXTURE['occurrences']:
            source, index, chapter = (occurrence[name] for name in ('frame', 'index', 'chapter'))
            role, command, literal = (occurrence[name] for name in ('role', 'command', 'literal'))
            with self.subTest(chapter=chapter, tag=occurrence['selector']['owner_tag'], symbol=literal):
                stream = nodes(source)
                parameter = stream[index]
                self.assertEqual(byte_hash(source), occurrence['sha256'])
                self.assertTrue(source_match(source, index, parameter, chapter, role))
                self.assertFalse(source_match(source, index, parameter, 'adequate', role))
                self.assertFalse(source_match(source+' ', index, parameter, chapter, role))
                model_slots = [slot for slot in find_slots(source, all_rules, p0_chapter=chapter)
                               if slot['start'] == parameter['start']]
                symbol = notation(source, parameter['start'], chapter, command, literal)
                if role == 'symbol':
                    self.assertIsNotNone(symbol)
                    self.assertFalse(model_slots)
                    continue
                self.assertIsNone(symbol)
                expected = 2 if role == 'component' else 1
                self.assertEqual(len(model_slots), expected)
                self.assertFalse(find_slots(source, all_rules, p0_chapter='adequate'))
                translated = '中文' if role == 'plain' else '中文'+ETALE_SEPARATOR+'文字'
                changed = source[:parameter['parameter_start']]+translated+source[parameter['parameter_end']:]
                kind = PLAIN_USAGE if role == 'plain' else COMPONENT_USAGE
                self.assertIsNotNone(usage(changed, nodes(changed), index, kind))
                self.assertIsNone(usage(changed+' ', nodes(changed+' '), index, kind))


@unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit read-only locked harvest')
class P0LockedMathFrames(unittest.TestCase):
    def test_locked_selectors_replay_all_witnessed_containers(self):
        harvest = Path(os.environ['HARVEST_DIR'])
        base = (ROOT/'config/macro-policy.yml').read_text().split('\np0_locked_math_frames:\n')[0]
        isolated = Containers(ROOT, harvest, policy_bytes=(base+OPT_IN).encode())
        self.assertEqual(isolated.english.commit, FIXTURE['source_commit'])
        grouped = defaultdict(list)
        for occurrence in FIXTURE['occurrences']:
            grouped[json.dumps(occurrence['selector'],sort_keys=True)].append(occurrence)
        self.assertEqual(len(grouped), 103)
        for encoded in grouped:
            selector = json.loads(encoded)
            with self.subTest(selector=selector):
                selected = isolated.select(selector)
                units = lower_container(selected, isolated.policy)
                self.assertEqual(''.join(map(source_tex,units)), selected['fragment'])
        self.assertEqual(isolated.policy.p0_verified_chapters,frozenset(SOURCE_HASHES))
        isolated.assert_unchanged()
