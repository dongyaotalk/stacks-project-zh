"""Cotangent source roles. Trial registration is confined to tests."""
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import unittest

from stacks_zh import math_text_cotangent as frames
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots, validate_regions, validate_translation
from stacks_zh.progress_coverage import native_container_tag_coverage
from stacks_zh.records import RecordError
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, canonical_proof_file_mapping, lower_container
from stacks_zh.source_reextractions import byte_hash, source_tex

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/fixtures/cotangent-source-frames.json').read_bytes())
BASELINE = subprocess.check_output(
    ['git', 'show', FIXTURE['base'] + ':config/macro-policy.yml'], cwd=ROOT, text=True
)


def trial_policy(base=BASELINE):
    entries = {
        'locked_math_text_notations': {
            'Alg': dict(commands=['textit'], usages=[frames.NOTATION_USAGE],
                        source_label='cotangent-section-cotangent-ring-map'),
            'Sym': dict(commands=['text'], usages=[frames.NOTATION_USAGE],
                        source_label='cotangent-lemma-vanishing-symmetric-powers'),
        },
        'locked_math_text_contexts': {
            'cotangent-algebra-category': dict(base_notation='-Alg', commands=['textit'],
                usages=[frames.NOTATION_USAGE], source_label='cotangent-section-cotangent-complex'),
            'cotangent-graded-tor': dict(base_notation='Tor', commands=['text'],
                usages=[frames.NOTATION_USAGE], source_label='cotangent-section-smooth'),
        },
        'translatable_math_text': {
            'cotangent-sections-over': dict(literal='sections over ', command='text', usage=frames.USAGE,
                source_label='cotangent-lemma-compute-L-morphism-sheaves-rings',
                witness_kind='proof', witness_ordinal=1),
        },
        'translatable_math_text_contexts': {
            'cotangent-triangle-on': dict(base_rule='descent-on-set', usage=frames.USAGE,
                source_label='cotangent-lemma-triangle-ses', witness_kind='lemma', witness_ordinal=1),
            'cotangent-finite-multi-index': dict(base_rule='etale-cohomology-8295b1e9910f', usage=frames.USAGE,
                source_label='cotangent-lemma-polynomial-on-top', witness_kind='proof', witness_ordinal=1),
            'cotangent-henselization-resp': dict(base_rule='deformations-natural-11', usage=frames.USAGE,
                source_label='cotangent-lemma-cotangent-complex-henselization',
                witness_kind='lemma', witness_ordinal=1),
        },
    }
    for section, rules in entries.items():
        marker = '\n' + section + ':\n'
        block = ''.join(f'  {name}:\n' + ''.join(
            f'    {key}: {value if key == "source_label" and section == "locked_math_text_notations" else json.dumps(value)}\n'
            for key, value in rule.items()) for name, rule in rules.items())
        base = base.replace(marker, marker + block, 1)
    return base


class CotangentFiniteFrameTests(unittest.TestCase):
    def setUp(self):
        self.trial = Policy(trial_policy())

    def test_operators_stay_locked_only_in_their_exact_frames(self):
        for notation, formulas in frames.NOTATION_FRAMES.items():
            for formula in sorted(formulas):
                with self.subTest(notation=notation, formula=formula):
                    scanner = Scanner(formula, self.trial, source_chapter='cotangent')
                    diagnostics = scanner.protect(0, len(formula))[2]
                    # Scanner alone has no resolved Git witnesses for natural slots.
                    self.assertEqual([d['source'] for d in diagnostics],
                                     ['sections over '] * formula.count(r'\text{sections over }'))
                    self.assertIn(notation, [r['notation'] for r in scanner.math_text_classifications
                                             if r['usage'] == frames.NOTATION_USAGE])
                    mutated = formula[:1] + ' ' + formula[1:] if not formula.startswith('$$') else (
                        '$$ ' + formula[2:])
                    scanner = Scanner(mutated, self.trial, source_chapter='cotangent')
                    scanner.protect(0, len(mutated))
                    self.assertFalse(any(r['usage'] == frames.NOTATION_USAGE
                                         for r in scanner.math_text_classifications))
        for bad in (r'$\text{Alg}_A$', r'$\textit{Alg}_B$', r'$\text{Sym}^k X$',
                    r'$X\text{Tor}_*^C(B,B)$', r'$A\textit{-Alg} + X$'):
            self.assertTrue(Scanner(bad, self.trial, source_chapter='cotangent').protect(0, len(bad))[2], bad)

    def test_identical_algebra_notation_needs_its_source_chapter(self):
        formula = r'$\textit{Alg}_A$'
        for chapter in (None, 'adequate', 'simplicial'):
            with self.subTest(chapter=chapter):
                scanner = Scanner(formula, self.trial, source_chapter=chapter)
                self.assertEqual([d['source'] for d in scanner.protect(0, len(formula))[2]], ['Alg'])

    def test_only_the_seven_pure_text_slots_are_exposed(self):
        counts = Counter()
        for formula in frames.NATURAL_FRAMES:
            slots = [slot for slot in find_slots(formula, self.trial.math_text_rules)
                     if slot['usage'] == frames.USAGE]
            self.assertTrue(slots)
            counts.update(slot['value'] for slot in slots)
            start = 2 if formula.startswith('$$') else 1
            for changed in (formula[:start] + ' ' + formula[start:],
                            formula.replace(r'\text{', r'\textbf{', 1)):
                self.assertFalse(any(slot['usage'] == frames.USAGE
                                     for slot in find_slots(changed, self.trial.math_text_rules)))
        self.assertEqual(counts, {' on ': 3, ' finite': 1, 'resp.': 1, 'sections over ': 2})

    def test_registry_rejects_widened_operators(self):
        for before, after in [
            ('commands: ["textit"]\n    usages: ["cotangent-symbol-frame"]',
             'commands: ["text"]\n    usages: ["cotangent-symbol-frame"]'),
            ('usages: ["cotangent-symbol-frame"]', 'usages: ["symbol"]'),
            ('base_notation: "-Alg"', 'base_notation: "Inf"'),
            ('literal: "sections over "', 'literal: "arbitrary prose "'),
        ]:
            with self.subTest(after=after), self.assertRaises((RecordError, ValueError)):
                Policy(trial_policy().replace(before, after, 1))


@unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit read-only locked harvest')
class CotangentLockedSourceTests(unittest.TestCase):
    def test_all_eighteen_selectors_preserve_complete_source_and_proof_owner(self):
        harvest = Path(os.environ['HARVEST_DIR'])
        baseline = Containers(ROOT, harvest, policy_bytes=BASELINE.encode())
        trial = Containers(ROOT, harvest, policy_bytes=trial_policy().encode())
        raw, _, diagnostics = baseline.document('cotangent')
        self.assertEqual(baseline.english.commit, FIXTURE['source_commit'])
        self.assertEqual(byte_hash(raw), FIXTURE['source_hash'])
        self.assertEqual(byte_hash(baseline.policy_bytes), FIXTURE['macro_policy_hash'])
        self.assertEqual(len(diagnostics), 44)
        self.assertEqual(trial.document('cotangent')[2], [])
        for unrelated in ('adequate', 'simplicial'):
            self.assertEqual(trial.document(unrelated)[2], baseline.document(unrelated)[2])

        for case in FIXTURE['selectors']:
            selector = case['selector']
            with self.subTest(selector=selector):
                if case['original_diagnostics']:
                    with self.assertRaisesRegex(RecordError, 'explicit text inside locked math'):
                        baseline.select(selector)
                else:
                    old = lower_container(baseline.select(selector), baseline.policy)
                    with self.assertRaisesRegex(RecordError, 'explicit text inside locked math'):
                        canonical_proof_file_mapping(old, baseline.english.tags, baseline)
                selected = trial.select(selector)
                units = lower_container(selected, trial.policy)
                native_container_tag_coverage(selected, trial.policy, trial.english.tags)
                span = selected['location']
                self.assertEqual(''.join(map(source_tex, units)).encode(),
                                 raw[span['byte_start']:span['byte_end']])
                mapping = canonical_proof_file_mapping(units, trial.english.tags, trial)
                self.assertEqual(mapping, {unit['unit_id']: unit['unit_id'] for unit in units})
                literals = []
                for unit in units:
                    self.assertEqual(validate_named_schema(unit, 'unit.schema.json', unit['unit_id']), [])
                    if not unit.get('math_text_regions'):
                        continue
                    self.assertEqual(validate_regions(unit), [])
                    translated = unit['source_text']
                    for region in unit['math_text_regions']:
                        for slot in region['slots']:
                            if slot['classification_witness']['usage'] == frames.USAGE:
                                literals.append(slot['source'])
                            left, right = map(lambda p: f'<{p}>', slot['boundary_placeholders'])
                            start = translated.index(left) + len(left)
                            end = translated.index(right, start)
                            translated = translated[:start] + '测试文字' + translated[end:]
                    self.assertEqual(validate_translation(unit, translated), [])
                self.assertEqual(literals, case['natural_literals'])
        baseline.assert_unchanged()
        trial.assert_unchanged()
