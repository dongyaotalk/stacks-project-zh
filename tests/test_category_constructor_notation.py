"""Source-only constructor syntax: no policy adoption, candidates or model runs."""
from pathlib import Path
import re
import unittest

from stacks_zh.extraction import Policy, Scanner, chapter_inventory
from stacks_zh.records import RecordError
from stacks_zh.source_reextractions import source_tex


RAW = (Path(__file__).resolve().parents[1] / 'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0]
RAW = re.sub(r'^  (?:Ind-|Pro-):\n(?:    .+\n)+', '', RAW, flags=re.M)
IND = ('  Ind-:\n    commands: ["text"]\n    usages: ["category-constructor"]\n'
       '    suffix: "\\\\mathcal{C}"\n    source_label: categories-remark-ind-category\n')
PRO = IND.replace('Ind-', 'Pro-').replace('remark-ind-category', 'remark-pro-category')
DECLARED = RAW + '\n' + IND + PRO


def scan(math, policy=None):
    scanner = Scanner(math, policy or Policy(DECLARED))
    text, placeholders, errors = scanner.protect(0, len(math))
    return scanner.math_text_classifications, text, placeholders, errors


class CategoryConstructorNotationTests(unittest.TestCase):
    def test_complete_atoms_and_braced_math_scripts_keep_every_math_byte(self):
        for expression in [r'\text{Ind-}\mathcal{C}', r'\text{Pro-}\mathcal{C}',
                           r'\mathcal{C}\to\text{Ind-}\mathcal{C}',
                           r'\Mor_{\text{Ind-}\mathcal{C}}(F,G)',
                           r'\Mor_{\text{Pro-}\mathcal{C}}(F,G)',
                           r'\colim_i\Mor_{\text{Pro-}\mathcal{C}}((M_{i,n}),N)',
                           r'x_i+{\text{Ind-}\mathcal{C}}',
                           r'x^{\text{Ind-}\mathcal{C}}',
                           r'\Ob(\text{Ind-}\mathcal{C})']:
            with self.subTest(expression=expression):
                math = '$' + expression + '$'
                items, text, placeholders, errors = scan(math)
                self.assertFalse(errors)
                self.assertEqual(text, '<MATH_0001>')
                self.assertEqual(placeholders, {'MATH_0001': math})
                self.assertEqual(len(items), 1)
                self.assertEqual(items[0]['usage'], 'category-constructor')
                self.assertEqual(items[0]['usage_source'], r'\mathcal{C}')
                self.assertEqual(items[0]['command'], 'text')
                self.assertEqual(items[0]['source'], r'\text{' + items[0]['notation'] + '}')

    def test_intervening_whitespace_and_comments_are_original_witness_bytes(self):
        witness = ' \t% original \\unknown{not executed}\n  \\mathcal{C}'
        math = '$\\text{Pro-}' + witness + '$'
        items, _, placeholders, errors = scan(math)
        self.assertFalse(errors)
        self.assertEqual(items[0]['usage_source'], witness)
        self.assertEqual(placeholders['MATH_0001'], math)

    def test_missing_changed_and_undeclared_atoms_remain_blocked(self):
        for expression in [r'\text{Ind-}', r'\text{Pro-}C', r'\text{Ind-}\mathcal C',
                           r'\text{Pro-}\mathcal{D}', r'\text{Pro-}\mathcal{c}',
                           r'\text{Pro-}\mathcal{ C}', r'\text{Pro-}\mathcal{C }',
                           r'\text{Pro-}\mathcal{CC}', r'\text{Pro-}\mathcal{{C}}',
                           r'\text{Pro-}\mathcal{C}at', r'\text{Pro-}\QCoh(C)',
                           r'\text{Pro-}D^b', r'\text{Ind-}{\mathcal{C}}',
                           r'\text{Ind-}+\mathcal{C}', r'\text{Ind-}\ \mathcal{C}',
                           r'\text{Ind-}\unknown\mathcal{C}',
                           r'\text{ Ind-}\mathcal{C}', r'\text{Ind- }\mathcal{C}',
                           r'\text{ind-}\mathcal{C}', r'\text{IND-}\mathcal{C}',
                           r'\textit{Ind-}\mathcal{C}', r'\textbf{Pro-}\mathcal{C}',
                           r'\text{Things-}\mathcal{C}', r'\text{and}\mathcal{C}',
                           r'\text{if}\mathcal{C}', r'\text{affine opens of}\mathcal{C}']:
            with self.subTest(expression=expression):
                items, _, _, errors = scan('$' + expression + '$')
                self.assertTrue(any(e['kind'] == 'math-text' for e in errors))
                self.assertFalse(any(i['usage'] == 'category-constructor' for i in items))

    def test_text_unknown_command_and_split_script_contexts_remain_blocked(self):
        atom = r'\text{Ind-}\mathcal{C}'
        for expression in [r'\text{' + atom + '}', r'\textit{' + atom + '}',
                           r'\textbf{' + atom + '}', r'\mathcal{' + atom + '}',
                           r'\unknown{' + atom + '}', r'\unknown{{' + atom + '}}',
                           r'\unknown{x}{' + atom + '}', r'\unknown[x]{' + atom + '}',
                           r'\unknown ' + atom, r'\unknown*' + atom,
                           r'\unknown\to ' + atom, r'\unknown{a}\Mor_{' + atom + '}',
                           r'x^' + atom, r'x_' + atom,
                           r'x_[' + atom + ']', r'x^[' + atom + ']',
                           r'x_{\text{Ind-}}\mathcal{C}',
                           r'{\text{Ind-}\mathcal{C}',
                           r'x_{\text{Ind-}\mathcal{C}',
                           r'\verb|' + atom + '|', r'\verb*|' + atom + '|',
                           r'\begin{verbatim}' + atom + r'\end{verbatim}']:
            with self.subTest(expression=expression):
                items, _, _, errors = scan('$' + expression + '$')
                self.assertTrue(errors)
                self.assertFalse(any(i['usage'] == 'category-constructor' for i in items))

    def test_old_policy_and_existing_symbols_keep_their_original_semantics(self):
        old = Policy(RAW)
        math = r'$\text{Ind-}\mathcal{C}+\text{Pro-}\mathcal{C}$'
        items, _, _, errors = scan(math, old)
        self.assertEqual([e['source'] for e in errors], ['Ind-', 'Pro-'])
        self.assertFalse(items)
        for math in [r'$G\textit{-Sets}$', r'$\text{Cov}_0+\text{size}(S)$',
                     r'$\textit{Cat}+\text{id}_C$']:
            self.assertEqual(scan(math, old), scan(math))
        # The old prefixed-letter contract still excludes math scripts.
        self.assertTrue(scan(r'$x_{G\textit{-Sets}}$')[-1])

    def test_exact_suffix_is_declared_per_entry(self):
        policy = Policy(DECLARED.replace(r'\\mathcal{C}', r'\\mathcal{D}'))
        self.assertFalse(scan(r'$\text{Pro-}\mathcal{D}$', policy)[-1])
        self.assertTrue(scan(r'$\text{Pro-}\mathcal{C}$', policy)[-1])

    def test_policy_fields_literals_commands_and_usage_fail_closed(self):
        invalid = [IND.replace('    suffix: "\\\\mathcal{C}"\n', ''),
                   IND + '    suffix: "\\\\mathcal{C}"\n',
                   IND.replace('    suffix:', '    prefix:'),
                   IND.replace('    suffix:', '    unexpected:'),
                   IND.replace('["text"]', '["textit"]'),
                   IND.replace('["text"]', '["text", "textbf"]'),
                   IND.replace('["category-constructor"]', '["symbol"]'),
                   IND.replace('["category-constructor"]', '["category-constructor", "symbol"]'),
                   IND.replace('Ind-:', 'Things-:'), IND.replace('Ind-:', 'Ind:'),
                   IND.replace('Ind-:', '-Ind:'), IND.replace('Ind-:', 'ind-:'),
                   IND.replace('Ind-:', 'Ind-and:')]
        for suffix in ['null', '1', '[]', '""', '"C"', '"\\\\mathcal C"',
                       '"\\\\mathcal{c}"', '"\\\\mathcal{CC}"', '"\\\\mathcal{{C}}"',
                       '"\\\\mathcal{ C}"', '"\\\\mathcal{C} "', '"\\\\QCoh(C)"',
                       '"\\\\mathcal{C}+x"']:
            invalid.append(IND.replace('"\\\\mathcal{C}"', suffix))
        for entry in invalid:
            with self.subTest(entry=entry), self.assertRaises(RecordError):
                Policy(RAW + '\n' + entry)
        with self.assertRaises(RecordError):
            Policy(RAW + '\n' + IND + IND)
        with self.assertRaises(RecordError):
            Policy(RAW.replace('  size:\n', '  size:\n    suffix: "\\\\mathcal{C}"\n'))

    def test_inventory_utf8_locations_roundtrip_and_pure_math_segments(self):
        for prose in ['Café 中文 uses ', '']:
            math = '$\\text{Ind-}% original\n\\mathcal{C}$'
            source = ('\\begin{document}\n\\section{First}\\label{section-first}\n' +
                      prose + math + '\n\\end{document}\n')
            raw = source.encode()
            rows, segments, errors = chapter_inventory('alpha', raw, 'a' * 40,
                                                       {'alpha-section-first': 'AAAA'}, Policy(DECLARED))
            self.assertFalse(errors)
            locations = rows if prose else segments
            classified = [r for r in locations if r.get('math_text_classifications')]
            self.assertEqual(len(classified), 1)
            item = classified[0]['math_text_classifications'][0]
            loc = item['location']
            self.assertEqual(raw[loc['byte_start']:loc['byte_end']], b'\\text{Ind-}')
            self.assertEqual(item['usage_source'], '% original\n\\mathcal{C}')
            if prose:
                self.assertIn(math, source_tex(classified[0]['unit']))
            else:
                self.assertIn(math, classified[0]['source'])


if __name__ == '__main__':
    unittest.main()
