"""Exact production policy delta and independent syntax examples."""
import re
import unittest
from pathlib import Path

from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots
from test_descent_math_text import CHAIN, DATA, ARROW, SETS, REFERENCES, PROJ, PROJECTIONS

ROOT = Path(__file__).resolve().parents[1]
BEFORE = (ROOT/'tests/fixtures/macro-policy-before-descent.yml').read_text()
CURRENT = (ROOT/'config/macro-policy.yml').read_text()
# Freeze the historical descent delta; later etale additions have their own
# exact-delta test. All compatibility cases below still use current production.
AFTER_DESCENT = (ROOT/'tests/fixtures/macro-policy-before-etale.yml').read_text()
ADDED = {
    'locked_math_text_notations': {'Proj', 'Rings', 'trdeg'},
    'translatable_math_text': {
        'descent-finite-free-fppf', 'descent-finite-free-on', 'descent-finite-free-zariski',
        'descent-category-data-family', 'descent-relative-family', 'descent-category-data-single',
        'descent-relative-single', 'descent-data-set', 'descent-such-that', 'descent-each',
        'descent-sheaves-set', 'descent-on-set', 'descent-representable', 'descent-lemma-reference',
        'descent-has-property', 'descent-as-module', 'descent-module-suffix', 'descent-with-points',
        'descent-exists-representative', 'descent-which-has', 'descent-is-flat',
        'descent-local-ring', 'descent-fibre-dimension', 'descent-data-arrow'},
    'translatable_math_text_components': {'descent-finite-free-etale-component'},
    'translatable_math_text_contexts': {'descent-each-set-context'},
    'locked_math_text_contexts': {'descent-projection-context'},
}


def entries(text, name):
    section = re.search(r'(?ms)^'+re.escape(name)+r':\n.*?(?=^[A-Za-z_][A-Za-z0-9_-]*:|\Z)', text)
    if not section:
        raise AssertionError(name)
    return {match.group(1): match.group() for match in
            re.finditer(r'(?m)^  ([^\s:]+):\n(?:^    .*\n)*', section.group())}


def scan(text, policy):
    scanner = Scanner(text, policy)
    result = scanner.protect(0, len(text))
    return result, scanner.math_text_classifications


class DescentPolicyRegistrationTests(unittest.TestCase):
    def test_only_declared_policy_entries_change_and_old_bytes_reconstruct(self):
        restored = AFTER_DESCENT
        for section, additions in ADDED.items():
            old, new = entries(BEFORE, section), entries(AFTER_DESCENT, section)
            self.assertEqual(set(new), set(old) | additions)
            for key in additions:
                self.assertEqual(restored.count(new[key]), 1)
                restored = restored.replace(new[key], '', 1)
            for key in old:
                if section == 'locked_math_text_notations' and key in {'Mod', 'Cov'}:
                    self.assertEqual(restored.count(new[key]), 1)
                    restored = restored.replace(new[key], old[key], 1)
                else:
                    self.assertEqual(new[key], old[key], (section, key))
        self.assertEqual(restored, BEFORE)
        old, new = Policy(BEFORE), Policy(AFTER_DESCENT)
        for key, rule in old.math_text_rules.items():
            self.assertEqual(new.math_text_rules[key], rule, key)
        for key, rule in old.math_text_notations.items():
            if key not in {'Mod', 'Cov'}:
                self.assertEqual(new.math_text_notations[key], rule, key)
        self.assertEqual(new.math_text_notations['Mod'], {
            'commands': ['text', 'textit'], 'usages': ['subscripted', 'applied'],
            'source_label': 'categories-remark-big-categories',
            'contexts': ['text/subscripted', 'textit/applied']})
        self.assertEqual(new.math_text_notations['Cov'], {
            'commands': ['text'], 'usages': ['applied', 'subscripted', 'primed-applied', 'bare-symbol'],
            'source_label': 'sets-section-coverings-site'})

    def test_legacy_notation_shapes_keep_identical_protection_and_witnesses(self):
        old, new = Policy(BEFORE), Policy(CURRENT)
        for text in [r'$\text{Mod}_R$', r'$\text{Cov}(S)$', r'$\text{Cov}()$',
                     r'$\text{Cov}_S$',
                     r"$\text{Cov}'(S)$", r'$\text{pr}(H(x))$',
                     r'$\text{pr}^*_i$', r'$\text{pr} : u^p\mathcal{T} \to \mathcal{T}$',
                     r'$G\textit{-Sets}$', r'$\textit{Aff}$',
                     r'$\text{pr}^*$', r'$\text{pr}$']:
            with self.subTest(text=text):
                self.assertEqual(scan(text, old), scan(text, new))

    def test_new_notation_shapes_lock_math_and_wrong_fonts_or_uses_reject(self):
        old, new = Policy(BEFORE), Policy(CURRENT)
        positives = [r'$\textit{Mod}(R)$', r'$\text{Cov}$', r'$\textit{Rings}$',
                     r'$\text{trdeg}_k$', PROJ, *PROJECTIONS]
        for text in positives:
            with self.subTest(text=text):
                self.assertTrue(scan(text, old)[0][2])
                (protected, classified) = scan(text, new)
                self.assertEqual(protected, ('<MATH_0001>', {'MATH_0001': text}, []))
                self.assertEqual(len(classified), 1)
        for text in [r'$\text{Mod}(R)$', r'$\textit{Mod}$', r'$\textit{Mod}_R$',
                     r'$\textit{Cov}$', r'$\text{cov}$',
                     r'$\text{Cov}_$', r'$\text{Cov}_{}$',
                     r"$\text{Cov}'$", r'$\text{Cov}\prime$',
                     r'$\text{Cov}\Bigg($', r'$\text{Cov}\lparen$',
                     r'$\text{Rings}$',
                     r'$\textit{rings}$', r'$\text{trdeg}$', r'$\textit{trdeg}_k$',
                     PROJ.replace('_S', '_T'), PROJECTIONS[0].replace('Y', 'X'),
                     PROJECTIONS[3].replace('f_Y', 'f_X')]:
            with self.subTest(text=text):
                protected, _ = scan(text, new)
                self.assertTrue(protected[2])

    def test_registered_natural_frames_and_absent_registration_or_changed_frame(self):
        old, new = Policy(BEFORE), Policy(CURRENT)
        for frame, count in [(CHAIN, 6), (DATA, 4), (ARROW, 2), (SETS, 8), (REFERENCES, 2)]:
            with self.subTest(frame=frame):
                self.assertEqual(find_slots(frame, old.math_text_rules), [])
                self.assertEqual(len(find_slots(frame, new.math_text_rules)), count)
        for frame in [ARROW.replace(r'\longrightarrow', r'\longleftarrow'),
                      ARROW.replace(r'\mathcal{V}', r'\mathcal{W}'),
                      DATA.replace('X/S', 'Y/S'), SETS.replace(r'\varphi', r'\psi'),
                      CHAIN.replace(r'\Leftrightarrow', r'\Rightarrow', 1),
                      REFERENCES.replace(r'\ref{lemma-family-is-one}', r'\ref{other}')]:
            with self.subTest(frame=frame):
                self.assertEqual(find_slots(frame, new.math_text_rules), [])


if __name__ == '__main__':
    unittest.main()
