"""Current English policy integration; synthetic literals are not model output."""
import unittest
from pathlib import Path

from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots
from test_sites_math_contexts import ALIGNED, COMPATIBILITY, DESCRIPTION, MEMBERSHIP


class SitesPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = Policy((Path(__file__).resolve().parents[1] / 'config/macro-policy.yml').read_text())

    def test_complete_natural_parameters_use_their_declared_policy_roles(self):
        cases = [
            (r'$x\text{  and  }y$', [('sites-double-and', '  and  ', 'root-phrase')]),
            (r'$x\text{infinite set}y$', [('sites-infinite-set', 'infinite set', 'root-phrase')]),
            (r'$x\quad\text{for presheaves and}\quad y$', [('sites-presheaves-and', 'for presheaves and', 'quad-connector')]),
            (r'$x\quad\text{where}\quad y$', [('sites-where', 'where', 'quad-connector')]),
            (r'$x\text{ is a right inverse to }y$', [('sites-right-inverse', ' is a right inverse to ', 'root-phrase')]),
            (r'$x\text{class of }y$', [('sites-class-of', 'class of ', 'root-phrase')]),
            (r'$x\quad\text{or}\quad y$', [('sites-or', 'or', 'quad-connector')]),
            (r'$x\text{ and correspondingly }y$', [('sites-correspondingly', ' and correspondingly ', 'root-phrase')]),
            (r'$x\text{ is sheaf theoretically empty}y$', [('sites-empty', ' is sheaf theoretically empty', 'root-phrase')]),
            (r'$x\quad\text{versus}\quad y$', [('sites-versus', 'versus', 'quad-connector')]),
            (MEMBERSHIP, [('sites-matrix-in', ' in ', 'matrix-membership')]),
            (DESCRIPTION, [('sites-collections', 'collections ', 'matrix-row-description'),
                           ('sites-matrix-in', ' in ', 'matrix-membership'),
                           ('sites-we-have', ' we have ', 'matrix-row-statement')]),
            (COMPATIBILITY, [('sites-compatible', ' is compatible with ', 'matrix-operator-compatibility')]),
            (ALIGNED, [('sites-aligned-and', ' and ', 'aligned-set-connector')]),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                slots = find_slots(source, self.policy.math_text_rules)
                self.assertEqual([(s['policy_entry'], s['value'], s['usage']) for s in slots], expected)
                for slot in slots:
                    self.assertEqual(source[slot['parameter_start']:slot['parameter_end']], slot['value'])

    def test_literal_case_whitespace_and_context_cannot_borrow_policy(self):
        for source in [
            r'$x\text{and  }y$', r'$x\text{Infinite set}y$',
            r'$x\text{is a right inverse to}y$', r'$x\text{Class of }y$',
            r'$x\text{correspondingly}y$', r'$x\text{is sheaf theoretically empty}y$',
            r'$x\text{for presheaves and}y$', r'$x\text{where}y$',
            r'$x\text{or}y$', r'$x\text{versus}y$',
            r'$x\text{collections }y$', r'$x\text{ we have }y$',
            r'$x\text{ is compatible with }y$',
        ]:
            with self.subTest(source=source):
                self.assertFalse(find_slots(source, self.policy.math_text_rules))

    def test_notation_additions_keep_complete_math_bytes_and_usage_identity(self):
        for source, notation, role in [
            (r'$\text{pr}^{(i,j)}_i$', 'pr', 'superscripted'),
            (r'$\text{pr}^{*}_i$', 'pr', 'superscripted'),
            (r"$\text{Cov}'(C)$", 'Cov', 'primed-applied'),
            (r'$\textit{PSh}$', 'PSh', 'symbol'),
            (r'$\text{Map}_G(H,S)$', 'Map', 'subscripted'),
            (r'$\text{inl}_{f,g}$', 'inl', 'subscripted'),
            (r'$\text{inr}_{f,g}$', 'inr', 'subscripted'),
            (r'$\text{pr}^*_i$', 'pr', 'starred-subscripted'),
            (r'$\Mor_{G\textit{-Sets}}(U,S)$', '-Sets', 'morphism-category-prefixed-symbol'),
            (r'$\Mor_{H\textit{-Sets}}(U,S)$', '-Sets', 'morphism-category-prefixed-symbol'),
            (r'$$\xymatrix{A & G\textit{-Sets}\ar[ld]\\ B & C}$$', '-Sets', 'diagram-category-prefixed-symbol'),
            (r'$H\textit{-Sets}$', '-Sets', 'prefixed-symbol'),
        ]:
            with self.subTest(source=source):
                scanner = Scanner(source, self.policy)
                _, protected, errors = scanner.protect(0, len(source))
                self.assertFalse(errors)
                self.assertEqual(list(protected.values()), [source])
                self.assertEqual([(x['notation'], x['usage']) for x in scanner.math_text_classifications], [(notation, role)])

    def test_notation_fonts_spelling_arguments_and_missing_context_still_block(self):
        for source in [
            r'$\textit{pr}^{(i,j)}$', r"$\textit{Cov}'(C)$",
            r'$\text{PSh}$', r'$\textit{ PSh}$', r'$\textit{PSh }$',
            r'$\textit{Map}_G(H,S)$', r'$\text{inl}$', r'$\text{inr}$',
            r'$\text{Inl}_{f,g}$', r'$\textit{inr}_{f,g}$',
            r'$K\textit{-Sets}$', r'$\Hom_{G\textit{-Sets}}(U,S)$',
        ]:
            with self.subTest(source=source):
                scanner = Scanner(source, self.policy)
                _, protected, errors = scanner.protect(0, len(source))
                self.assertEqual(list(protected.values()), [source])
                self.assertTrue(any(e['kind'] == 'math-text' for e in errors))
