"""Exact production delta, independent source literals, and locked-Git evidence."""
import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path

from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots, validate_regions, validate_translation
from stacks_zh.records import validate_tex_controls
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_integrity import environment_title_errors
from stacks_zh.source_reextractions import source_tex
from test_descent_policy_registration import entries, scan
from test_descent_math_text import CHAIN, DATA, ARROW, SETS, REFERENCES, PROJ, PROJECTIONS
from test_etale_math_text import FRAMES, UNRAMIFIED, SECTIONS, THICKENING, DESCENT, EFFECTIVE, synthetic_fields

ROOT = Path(__file__).resolve().parents[1]
BEFORE = (ROOT/'tests/fixtures/macro-policy-before-etale.yml').read_text()
CURRENT = (ROOT/'config/macro-policy.yml').read_text()
# Accepted etale registration, independent of later chapter policy additions.
REGISTERED_COMMIT = 'a141a53c5114b26ab6b39c2884ea223945b490a1'
REGISTERED = subprocess.check_output(
    ['git', 'show', REGISTERED_COMMIT + ':config/macro-policy.yml'], cwd=ROOT, text=True)
EVIDENCE = json.loads((ROOT/'docs/evidence/etale41-math-text-policy-20261106.json').read_text())
BEFORE_HASH = '2762bd3987f6da68e373928da96eb653423d86d2bb52a1fb1599c98eec53a4ff'
TEXT = {
    'etale-local-unramified-at': (' is unramified at ', 'root-phrase', 'etale-section-unramified-definition'),
    'etale-finite-separable-condition': (' finite separable', 'etale-unramified-condition', 'etale-section-unramified-definition'),
    'etale-sections-of': ('sections of ', 'etale-sections-correspondence', 'etale-section-topological-unramified'),
    'etale-connected-components': ('connected components ', 'etale-sections-correspondence', 'etale-section-topological-unramified'),
    'etale-components-of': (' of ', 'etale-sections-correspondence', 'etale-section-topological-unramified'),
    'etale-induced-map': ('the induced map ', 'etale-sections-correspondence', 'etale-section-topological-unramified'),
    'etale-schemes': ('schemes ', 'etale-scheme-diagrams', 'etale-section-topological-invariance'),
    'etale-with-spaced': (' with ', 'etale-scheme-diagrams', 'etale-section-descending-etale'),
    'etale-with': (' with', 'etale-scheme-diagrams', 'etale-section-descending-etale'),
    'etale-quasi-compact-schemes': ('schemes quasi-compact,', 'etale-scheme-diagrams', 'etale-section-descending-etale'),
    'etale-for-some': (' for some ', 'root-phrase', 'etale-lemma-characterize-normal-crossings-normalization'),
}
COMPONENTS = {
    'etale-schemes-etale-component': (r" \'etale over ", [' ', 'tale over '], 'etale-section-topological-invariance'),
    'etale-separated-etale-component': (r"separated, \'etale over ", ['separated, ', 'tale over '], 'etale-section-descending-etale'),
    'etale-quasi-compact-etale-component': (r" quasi-compact, separated, \'etale over ", [' quasi-compact, separated, ', 'tale over '], 'etale-section-descending-etale'),
}
CONTEXTS = {
    'etale-sections-such-that': ('descent-such-that', 'etale-sections-correspondence', 'etale-section-topological-unramified'),
    'etale-sections-isomorphism': ('categories-remaining-is-isomorphism', 'etale-sections-correspondence', 'etale-section-topological-unramified'),
    'etale-descent-data-context': ('descent-data-set', 'etale-scheme-diagrams', 'etale-section-descending-etale'),
    'etale-relative-context': ('descent-relative-single', 'etale-scheme-diagrams', 'etale-section-descending-etale'),
}
ADDED = {'locked_math_text_notations': {'Mat'}, 'translatable_math_text': set(TEXT),
         'translatable_math_text_components': set(COMPONENTS), 'translatable_math_text_contexts': set(CONTEXTS)}


def fields(block):
    result = {}
    for match in re.finditer(r'(?m)^    ([a-z_]+): (.+)$', block):
        try:
            result[match[1]] = json.loads(match[2])
        except json.JSONDecodeError:
            result[match[1]] = match[2]
    return result


def protected(text, raw=CURRENT):
    scanner = Scanner(text, Policy(raw))
    return scanner.protect(0, len(text)), scanner.math_text_classifications


class EtalePolicyRegistrationTests(unittest.TestCase):
    def test_exact_only_declared_delta_reconstructs_accepted_policy_bytes(self):
        self.assertEqual(hashlib.sha256(BEFORE.encode()).hexdigest(), BEFORE_HASH)
        restored = REGISTERED
        for section, added in ADDED.items():
            old, new = entries(BEFORE, section), entries(REGISTERED, section)
            self.assertEqual(set(new), set(old) | added)
            for key in added:
                self.assertEqual(restored.count(new[key]), 1)
                restored = restored.replace(new[key], '', 1)
            for key in old:
                if section == 'locked_math_text_notations' and key == 'depth':
                    expected = old[key].replace('usages: ["subscripted"]', 'usages: ["subscripted", "applied"]')
                    self.assertNotEqual(expected, old[key])
                    self.assertEqual(new[key], expected)
                    restored = restored.replace(new[key], old[key], 1)
                else:
                    self.assertEqual(new[key], old[key], (section, key))
        self.assertEqual(restored, BEFORE)

    def test_literal_role_and_real_witness_fields_are_exact(self):
        ordinary = entries(CURRENT, 'translatable_math_text')
        for key, (literal, usage, label) in TEXT.items():
            kind = 'lemma' if key == 'etale-for-some' else 'section'
            self.assertEqual(fields(ordinary[key]), dict(literal=literal, command='text', usage=usage,
                source_label=label, witness_kind=kind, witness_ordinal=1))
        components = entries(CURRENT, 'translatable_math_text_components')
        for key, (literal, leaves, label) in COMPONENTS.items():
            self.assertEqual(fields(components[key]), dict(literal=literal, command='text',
                usage='etale-scheme-component', components=leaves, separator=r"\'e",
                source_label=label, witness_kind='section', witness_ordinal=1))
        contexts = entries(CURRENT, 'translatable_math_text_contexts')
        for key, (base, usage, label) in CONTEXTS.items():
            self.assertEqual(fields(contexts[key]), dict(base_rule=base, usage=usage,
                source_label=label, witness_kind='section', witness_ordinal=1))
        self.assertEqual(Policy(REGISTERED).math_text_notations['Mat'], dict(commands=['text'],
            usages=['applied'], source_label='etale-example-standard-etale'))

    def test_operator_applications_are_locked_and_bad_shapes_still_reject(self):
        for source in [r'$\text{Mat}(n \times m, \kappa(\mathfrak q))$',
                       r'$\text{depth}(A) = \text{depth}(B)$', r'$\dim(A) = \text{depth}(A)$',
                       r'$\text{Mat}()$', r'$\text{depth}()$']:
            with self.subTest(source=source):
                self.assertTrue(protected(source, BEFORE)[0][2])
                result, classifications = protected(source)
                self.assertEqual(result, ('<MATH_0001>', {'MATH_0001': source}, []))
                self.assertTrue(classifications)
                self.assertTrue(all(c['usage'] == 'applied' for c in classifications))
        # Accepted applied syntax classifies the following opening parenthesis;
        # it does not validate function arity. Preserve that existing contract.
        self.assertEqual(protected(r'$\text{Cov}()$', BEFORE), protected(r'$\text{Cov}()$'))
        for source in [r'$\textit{Mat}(n,k)$', r'$\text{Mat}$',
                       r'$\text{Mat}_{}$', r'$\text{mat}(n,k)$', r"$\text{Mat}'(n,k)$",
                       r'$\text{depth}$', r'$\textit{depth}(A)$',
                       r'$\text{depth}_{}$', r'$\text{depth }(A)$',
                       r'$\text{Mat}(n,k)\text{ unregistered annotation}$',
                       r'$\text{depth}(A)\text{ unregistered annotation}$']:
            with self.subTest(source=source):
                self.assertTrue(protected(source)[0][2])

    def test_old_notation_and_descent_permissions_are_unchanged(self):
        old, new = Policy(BEFORE), Policy(REGISTERED)
        for source in [r'$\text{depth}_R(M)$', r'$\text{Mod}_R$', r'$\textit{Mod}(R)$',
                       r'$\text{Cov}$', r"$\text{Cov}'(S)$", r'$\textit{Aff}$',
                       PROJ, *PROJECTIONS, CHAIN, DATA, ARROW, SETS, REFERENCES]:
            with self.subTest(source=source):
                self.assertEqual(scan(source, old), scan(source, new))
        for key, rule in old.math_text_rules.items():
            self.assertEqual(new.math_text_rules[key], rule, key)
        for key, rule in old.math_text_notations.items():
            if key != 'depth':
                self.assertEqual(new.math_text_notations[key], rule, key)

    def test_current_policy_retains_registered_rules_and_notation_permissions(self):
        registered, current = Policy(REGISTERED), Policy(CURRENT)
        for key, rule in registered.math_text_rules.items():
            self.assertEqual(current.math_text_rules[key], rule, key)
        for key, rule in registered.math_text_notations.items():
            actual = dict(current.math_text_notations[key])
            # Later witnessed registrations may add usages; old permissions and
            # every other field remain intact. Their exact delta has its own test.
            self.assertTrue(set(rule['usages']) <= set(actual['usages']), key)
            actual['usages'] = rule['usages']
            self.assertEqual(actual, rule, key)
        for key, contexts in registered.math_text_notation_contexts.items():
            self.assertTrue(all(context in current.math_text_notation_contexts[key]
                                for context in contexts), key)

    def test_each_registered_rule_and_context_is_required_in_its_frame(self):
        # Exercise actual slot membership. A bare Policy has no resolved Git
        # witness anchors, so Scanner rejection alone cannot test this delta.
        def count(frame, raw):
            return len(find_slots(frame, Policy(raw).math_text_rules))

        cases = {
            'etale-local-unramified-at': UNRAMIFIED, 'etale-finite-separable-condition': UNRAMIFIED,
            'etale-sections-of': SECTIONS, 'etale-connected-components': SECTIONS,
            'etale-components-of': SECTIONS, 'etale-induced-map': SECTIONS,
            'etale-schemes': THICKENING, 'etale-with-spaced': DESCENT,
            'etale-with': EFFECTIVE, 'etale-quasi-compact-schemes': EFFECTIVE,
            'etale-for-some': r'$p_i = p_j\text{ for some }i\not = j$',
        }
        for key, frame in cases.items():
            with self.subTest(key=key):
                block = entries(CURRENT, 'translatable_math_text')[key]
                self.assertGreater(count(frame, CURRENT), 0)
                self.assertLess(count(frame, CURRENT.replace(block, '', 1)), count(frame, CURRENT))
        for key in CONTEXTS:
            frame = SECTIONS if key.startswith('etale-sections') else DESCENT
            with self.subTest(context=key):
                block = entries(CURRENT, 'translatable_math_text_contexts')[key]
                self.assertLess(count(frame, CURRENT.replace(block, '', 1)), count(frame, CURRENT))
        for key in COMPONENTS:
            frame = THICKENING if key == 'etale-schemes-etale-component' else EFFECTIVE
            with self.subTest(component=key):
                block = entries(CURRENT, 'translatable_math_text_components')[key]
                self.assertLess(count(frame, CURRENT.replace(block, '', 1)), count(frame, CURRENT))

    def test_production_registration_keeps_complete_frame_boundaries(self):
        rules = Policy(CURRENT).math_text_rules
        self.assertEqual([len(find_slots(frame, rules)) for frame in FRAMES], [3, 6, 6, 8, 8])
        for source in [SECTIONS.replace(r'\leftrightarrow', r'\to'),
                       SECTIONS.replace("X'", 'Z', 1), THICKENING.replace('X_0', 'X_1'),
                       DESCENT.replace('equation-descent-etale', 'other'),
                       DESCENT.replace(r'\longrightarrow', r'\longleftarrow'),
                       EFFECTIVE.replace('X/S', 'Y/S'), EFFECTIVE.replace(r'\varphi', r'\psi')]:
            with self.subTest(source=source):
                self.assertEqual([s for s in find_slots(source, rules) if s['usage'].startswith('etale-')], [])

    def test_nine_actual_git_fragments_schema_and_source_roundtrip(self):
        self.assertEqual(EVIDENCE['chinese_origin'], '7e3988b59a81027796b776a9238a061368c81fd2')
        self.assertEqual(EVIDENCE['source_commit'], 'a04446e57ec1fbc252a871afcec7752fb2807b14')
        self.assertEqual(EVIDENCE['before_policy_sha256'], BEFORE_HASH)
        self.assertEqual(EVIDENCE['production_policy_sha256'], hashlib.sha256(REGISTERED.encode()).hexdigest())
        expected = {'024L': 3, '024U': 6, '024Y': 0, '039R': 6, '039T': 0,
                    '025Q': 0, '0BTH': 8, '0BTP': 8, '0CBR': 1}
        self.assertEqual({r['selector']['owner_tag'] for r in EVIDENCE['after']}, set(expected))
        self.assertEqual(len(EVIDENCE['before']), 9)
        self.assertTrue(all(r['state'] == 'BLOCKED' and 'requires classification before adoption' in r['error']
                            for r in EVIDENCE['before']))
        for record in EVIDENCE['after']:
            with self.subTest(owner=record['selector']['owner_tag']):
                self.assertEqual(record['state'], 'READY')
                self.assertEqual(record['typed_slots'], expected[record['selector']['owner_tag']])
                self.assertEqual(record['location']['fragment_hash'],
                    'sha256:'+hashlib.sha256(record['full_fragment'].encode()).hexdigest())
                for unit in record['units']:
                    self.assertEqual(validate_named_schema(unit, 'unit.schema.json', 'policy-source'), [])
                    self.assertEqual(validate_regions(unit), [])
                    self.assertEqual(source_tex(unit), record['full_fragment'])

    def test_named_source_title_accepts_the_original_blank_accent_leaves(self):
        record = next(row for row in EVIDENCE['after'] if row['selector']['owner_tag'] == '039R')
        unit, = record['units']
        self.assertEqual(source_tex(unit), record['full_fragment'])
        self.assertEqual(environment_title_errors(unit), [])
        original_as_candidate = {'translation': unit['source_text']}
        self.assertTrue(any('nonempty plain text' in error
                            for error in validate_tex_controls(unit, original_as_candidate)))
        self.assertEqual(validate_tex_controls(unit, synthetic_fields(unit)), [])
        injected = dict(unit, source_text=unit['source_text'].replace('Une ', r'\input{bad} ', 1))
        self.assertTrue(environment_title_errors(injected))
        missing_closure = dict(unit, source_text=unit['source_text'].replace('<OWNARGEND_0001>', '', 1))
        self.assertTrue(environment_title_errors(missing_closure))

    def test_registered_blank_accent_source_is_distinct_from_nonempty_target(self):
        for record in EVIDENCE['after']:
            if record['selector']['owner_tag'] not in {'039R', '0BTH'}:
                continue
            unit = record['units'][0]
            with self.subTest(owner=record['selector']['owner_tag']):
                blank = [s for r in unit['math_text_regions'] for s in r['slots']
                         if s.get('parameter_components') and s['source'] == ' ']
                self.assertEqual(len(blank), 2)
                self.assertTrue(all(s['parameter_components']['component_index'] == 1 for s in blank))
                self.assertEqual(source_tex(unit), record['full_fragment'])
                self.assertTrue(validate_translation(unit, unit['source_text']))
                # Explicit synthetic test scaffolding; never a model candidate.
                self.assertEqual(validate_translation(unit, synthetic_fields(unit)['translation']), [])


if __name__ == '__main__':
    unittest.main()
