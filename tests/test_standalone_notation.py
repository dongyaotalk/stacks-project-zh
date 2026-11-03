"""Source-only tests for an explicitly registered root bare-symbol usage."""
from pathlib import Path
import unittest

from stacks_zh.extraction import Policy, Scanner, SyntaxProblem, chapter_inventory
from stacks_zh.records import RecordError
from stacks_zh.source_reextractions import source_tex

ROOT = Path(__file__).resolve().parents[1]
# Keep the pre-registration tool permission guards independent of later policy.
BEFORE_DESCENT = ROOT / 'tests/fixtures/macro-policy-before-descent.yml'
BASELINE = BEFORE_DESCENT if BEFORE_DESCENT.exists() else ROOT / 'config/macro-policy.yml'
RAW = BASELINE.read_text().split('\ntranslatable_math_text:')[0]
COV = '    usages: ["applied", "subscripted", "primed-applied"]\n'
NEW = COV.replace('"primed-applied"]', '"primed-applied", "bare-symbol"]')
assert RAW.count(COV) == 1
NEW_RAW = RAW.replace(COV, NEW)
OLD_POLICY = Policy(RAW)
NEW_POLICY = Policy(NEW_RAW)
BARE_POLICY = Policy(RAW.replace(COV, '    usages: ["bare-symbol"]\n'))


def scan(math, policy):
    scanner = Scanner(math, policy)
    result = scanner.protect(0, len(math))
    return result, scanner.math_text_classifications


class StandaloneNotationTests(unittest.TestCase):
    def test_two_descent_math_shapes_are_complete_and_byte_locked(self):
        for math, usages in [
                (r'$\text{Cov}$', ['bare-symbol']),
                (r'$\text{Cov} \subset \text{Cov}_\mathcal{C}$', ['bare-symbol', 'subscripted'])]:
            with self.subTest(math=math):
                self.assertTrue(scan(math, OLD_POLICY)[0][2])
                result, classified = scan(math, NEW_POLICY)
                self.assertEqual(result, ('<MATH_0001>', {'MATH_0001': math}, []))
                self.assertEqual([c['usage'] for c in classified], usages)
                self.assertTrue(all(c['source_label'] == 'sets-section-coverings-site' for c in classified))
                self.assertEqual(classified[0]['usage_source'], '')

    def test_original_space_comment_and_unicode_bytes_are_not_normalized(self):
        for math in ['$\\text{Cov}\t% original\n$', '$α + \\text{Cov} \\subset X$']:
            result, classified = scan(math, NEW_POLICY)
            self.assertEqual(result, ('<MATH_0001>', {'MATH_0001': math}, []))
            self.assertEqual([c['usage'] for c in classified], ['bare-symbol'])

    def test_empty_missing_and_wrong_script_forms_cannot_fall_back_to_bare(self):
        for expression in [r'\text{Cov}_{}', '\\text{Cov}_{% empty\n}',
                           r'\text{Cov}_', r'\text{Cov}^{}', r'\text{Cov}^',
                           r'\text{Cov}_\end',
                           r'\text{Cov}_\)', r'\text{Cov}_\]']:
            with self.subTest(expression=expression):
                result, classified = scan('$' + expression + '$', NEW_POLICY)
                self.assertTrue(result[2])
                self.assertFalse(classified)

    def test_ambiguous_math_delimiters_are_rejected_by_both_policies(self):
        for math in [r'$\text{Cov}_$$', r'$\text{Cov}^$$']:
            for policy in [OLD_POLICY, NEW_POLICY]:
                with self.subTest(math=math, policy=policy):
                    with self.assertRaises(SyntaxProblem):
                        scan(math, policy)

    def test_sized_applications_and_control_sequence_primes_are_not_bare(self):
        for size in ['left', 'big', 'Big', 'bigg', 'Bigg',
                     'bigl', 'Bigl', 'biggl', 'Biggl']:
            for opening in ['(', '[']:
                closing = ')' if opening == '(' else ']'
                right = '\\right' if size == 'left' else ''
                expression = '\\text{Cov}\\' + size + '% boundary\n' + opening + 'C' + right + closing
                with self.subTest(expression=expression):
                    self.assertTrue(scan('$' + expression + '$', BARE_POLICY)[0][2])
        for expression in [r'\text{Cov}\prime', r'\text{Cov}\lparen C',
                           r'\text{Cov}\lbrack C']:
            with self.subTest(expression=expression):
                self.assertTrue(scan('$' + expression + '$', BARE_POLICY)[0][2])

    def test_bare_only_permission_does_not_grant_scripts_primes_or_applications(self):
        for expression in [r'\text{Cov}_0', r'\text{Cov}^{2}', r"\text{Cov}'",
                           r"\text{Cov}''", r'\text{Cov}(C)', r'\text{Cov}[C]',
                           r'\text{Cov}\left(C\right)', r'\text{Cov}\Bigl(C\Bigr)',
                           '\\text{Cov}% original\n_0']:
            with self.subTest(expression=expression):
                self.assertTrue(scan('$' + expression + '$', BARE_POLICY)[0][2])

    def test_existing_nonempty_scripts_and_applications_keep_exact_priority_and_witnesses(self):
        for math in [r'$\text{Cov}_0$', r'$\text{Cov}_{i+1}$',
                     r'$\text{Cov}_\mathcal{C}$', r'$\text{Cov}(C)$',
                     r"$\text{Cov}'(C)$", r'$\text{Cov}\left(C\right)$']:
            with self.subTest(math=math):
                self.assertEqual(scan(math, NEW_POLICY), scan(math, OLD_POLICY))
        for math in [r'$\text{size}$', r'$G\textit{-Sets}$', r'$\text{pr}_i$',
                     r'$\textit{Mod}(R)$', r'$\text{Mod}_R$']:
            with self.subTest(math=math):
                self.assertEqual(scan(math, NEW_POLICY), scan(math, OLD_POLICY))

    def test_wrong_fonts_words_and_unknown_argument_contexts_remain_blocked(self):
        for expression in [r'\textit{Cov}', r'\textbf{Cov}', r'\text{cov}',
                           r'\text{ Cov}', r'\text{Cov }', r'\text{CovExtra}',
                           r'\text{and}', r'\text{if}', r'\unknown{\text{Cov}}',
                           r'x_{\text{Cov}}', r'\text{\text{Cov}}',
                           r'\unknown\text{Cov}', r'\unknown x \text{Cov}']:
            with self.subTest(expression=expression):
                self.assertTrue(scan('$' + expression + '$', NEW_POLICY)[0][2])

    def test_original_negative_cases_still_hold_under_the_unchanged_old_policy(self):
        for expression in [r'\text{Cov}', r'\text{Cov}_{}', '\\text{Cov}_{% empty\n}',
                           r'\text{Cov}_', r'\text{cov}_0', r'\textit{Cov}_0',
                           r'\text{Size}', r'\text{ size}', r'\text{and}',
                           r'\text{if}', r'\text{affine opens of }']:
            with self.subTest(expression=expression):
                self.assertTrue(scan('$' + expression + '$', OLD_POLICY)[0][2])

    def test_exact_font_usage_combinations_remain_enforced(self):
        old_entry = ('  Cov:\n    commands: ["text"]\n' + COV +
                     '    source_label: sets-section-coverings-site\n')
        new_entry = ('  Cov:\n    commands: ["text", "textit"]\n'
                     '    usages: ["applied", "bare-symbol"]\n'
                     '    source_label: sets-section-coverings-site\n'
                     '    contexts: ["text/applied", "textit/bare-symbol"]\n')
        policy = Policy(RAW.replace(old_entry, new_entry))
        self.assertFalse(scan(r'$\text{Cov}(C)$', policy)[0][2])
        self.assertFalse(scan(r'$\textit{Cov}$', policy)[0][2])
        self.assertTrue(scan(r'$\text{Cov}$', policy)[0][2])
        self.assertTrue(scan(r'$\textit{Cov}(C)$', policy)[0][2])
        with self.assertRaises(RecordError):
            Policy(NEW_RAW.replace('"bare-symbol"', '"bare-symbol", "bare-symbol"'))

    def test_complete_source_inventory_roundtrip_keeps_visible_prose_and_math(self):
        math = r'$\text{Cov} \subset \text{Cov}_\mathcal{C}$'
        body = r'\section{First}\label{section-first}' + '\nUse ' + math + '.\n'
        raw = ('\\begin{document}\n' + body + '\\end{document}\n').encode()
        rows, _, errors = chapter_inventory('alpha', raw, 'a' * 40,
                                           {'alpha-section-first': 'AAAA'}, NEW_POLICY)
        self.assertFalse(errors)
        row = rows[-1]
        loc = row['location']
        self.assertEqual(source_tex(row['unit']).encode(), raw[loc['byte_start']:loc['byte_end']])
        self.assertIn('Use ', row['unit']['source_text'])
        self.assertEqual(row['unit']['placeholders']['MATH_0001'], math)


if __name__ == '__main__':
    unittest.main()
