"""Independent source-only notation fixtures; no actual model runs or facts."""
from pathlib import Path
import re
import unittest

from stacks_zh.extraction import Policy, Scanner, chapter_inventory
from stacks_zh.records import RecordError
from stacks_zh.source_reextractions import source_tex


RAW = (Path(__file__).resolve().parents[1] / 'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0]
POLICY = Policy(RAW)
ENTRY = ('  -Sets:\n    commands: ["textit"]\n    usages: ["prefixed-symbol"]\n'
         '    prefix: "G"\n    source_label: sets-section-sets-with-group-action\n')


def scan(math, policy=POLICY):
    scanner = Scanner(math, policy)
    text, placeholders, errors = scanner.protect(0, len(math))
    return scanner.math_text_classifications, text, placeholders, errors


class PrefixedNotationTests(unittest.TestCase):
    def test_actual_forms_keep_all_math_locked(self):
        for math in [r'$G\textit{-Sets}$', r'$G\textit{-Sets}_\alpha$',
                     r'$\Ob(G\textit{-Sets}_\alpha)$',
                     r'$F:\mathcal I \to G\textit{-Sets}_\alpha$',
                     r'$F:\mathcal{I} \to G\textit{-Sets}_\alpha$',
                     r'$x_i + G\textit{-Sets}$', r'$x_{i}\to G\textit{-Sets}$',
                     r'$S_0 \cup \{{}_GG\} \subset \Ob(G\textit{-Sets}_\alpha)$',
                     r"$S' \in \Ob(G\textit{-Sets}_\alpha)$",
                     r'${G\textit{-Sets}}$', r'$x + {G\textit{-Sets}}$']:
            with self.subTest(math=math):
                items, text, placeholders, errors = scan(math)
                self.assertFalse(errors)
                self.assertEqual(text, '<MATH_0001>')
                self.assertEqual(placeholders, {'MATH_0001': math})
                self.assertEqual(len(items), 1)
                self.assertEqual(items[0]['usage'], 'prefixed-symbol')
                self.assertEqual(items[0]['usage_source'], 'G')
                self.assertEqual(items[0]['source'], r'\textit{-Sets}')
                self.assertEqual(items[0]['source_label'], 'sets-section-sets-with-group-action')

    def test_prefix_whitespace_and_comments_are_original_witness_bytes(self):
        math = '$G \t% H and \\textit{fake}\n  \\textit{-Sets}_0$'
        items, _, placeholders, errors = scan(math)
        self.assertFalse(errors)
        self.assertEqual(items[0]['usage_source'], 'G \t% H and \\textit{fake}\n  ')
        self.assertEqual(placeholders['MATH_0001'], math)

    def test_wrong_or_escaped_prefixes_and_inexact_suffixes_stay_blocked(self):
        for expression in [r'H\textit{-Sets}', r'g\textit{-Sets}', r'HG\textit{-Sets}',
                           r'GG\textit{-Sets}', r'\G\textit{-Sets}',
                           r'\\G\textit{-Sets}', r'1G\textit{-Sets}', 'αG\\textit{-Sets}',
                           r'\textit{-Sets}', r'G\text{-Sets}', r'G\textbf{-Sets}',
                           r'G\textit{-sets}', r'G\textit{-SETS}', r'G\textit{ -Sets}',
                           r'G\textit{-Sets }', r'G\textit{-Sets and more}',
                           r'G\ \textit{-Sets}', r'G{\textit{-Sets}}',
                           r'G + \textit{-Sets}', r'G\textit{\textit{-Sets}}']:
            with self.subTest(expression=expression):
                items, _, _, errors = scan('$' + expression + '$')
                self.assertTrue(any(e['kind'] == 'math-text' for e in errors))
                self.assertFalse(any(i['notation'] == '-Sets' for i in items))

    def test_command_text_script_and_literal_arguments_cannot_supply_prefix(self):
        for expression in [r'\text{G\textit{-Sets}}', r'\textbf{G\textit{-Sets}}',
                           r'\unknown{G\textit{-Sets}}', r'\unknown{{G\textit{-Sets}}}',
                           r'\unknown{x}{G\textit{-Sets}}',
                           r'\unknown[x]{G\textit{-Sets}}', r'\unknown G\textit{-Sets}',
                           r'\unknown*G\textit{-Sets}', r'\unknown*{G\textit{-Sets}}',
                           r'\unknown\to G\textit{-Sets}',
                           r'\unknown{a}\to G\textit{-Sets}',
                           r'\unknown\mathcal{I}\to G\textit{-Sets}',
                           r'\unknown{a}_0\to G\textit{-Sets}',
                           r'\unknown x G\textit{-Sets}', r'\unknown(G\textit{-Sets})',
                           r'x_{G\textit{-Sets}}', r'x^G\textit{-Sets}',
                           r'\verb|G\textit{-Sets}|', r'\verb*|G\textit{-Sets}|',
                           r'\begin{verbatim}x + G\textit{-Sets}\end{verbatim}',
                           '% G\n\\textit{-Sets}', '% G\\textit{-Sets}\n\\textit{-Sets}']:
            with self.subTest(expression=expression):
                items, _, _, errors = scan('$' + expression + '$')
                self.assertTrue(any(e['kind'] == 'math-text' for e in errors))
                self.assertFalse(any(i['notation'] == '-Sets' for i in items))

    def test_current_bare_size_and_subscripted_cov_preserve_applied_priority(self):
        math = r'$\text{size} + \text{size}(S) + \text{Cov}_0 + \text{Cov}_{i+1} + \text{Cov}(C)$'
        items, _, placeholders, errors = scan(math)
        self.assertFalse(errors)
        self.assertEqual([i['usage'] for i in items], ['symbol', 'applied', 'subscripted', 'subscripted', 'applied'])
        self.assertEqual([i['usage_source'] for i in items], ['', '(', '_0', '_{i+1}', '('])
        self.assertEqual(placeholders['MATH_0001'], math)

    def test_cov_without_nonempty_subscript_and_natural_words_stay_blocked(self):
        for expression in [r'\text{Cov}', r'\text{Cov}_{}', r'\text{Cov}_{% empty' + '\n}',
                           r'\text{Cov}_', r'\text{cov}_0', r'\textit{Cov}_0',
                           r'\text{Size}', r'\text{ size}', r'\text{and}',
                           r'\text{if}', r'\text{affine opens of }']:
            with self.subTest(expression=expression):
                _, _, _, errors = scan('$' + expression + '$')
                self.assertTrue(errors)

    def test_explicit_historical_policy_blocks_new_forms_and_preserves_old_uses(self):
        # Exact old declarations, rather than accepting whatever the current
        # policy helper happens to produce for these three entries.
        old = re.sub(r'^  (?:size|Cov|-Sets):\n(?:    .+\n)+', '', RAW, flags=re.M)
        old += ('\n  size:\n    commands: ["text"]\n    usages: ["applied"]\n'
                '    source_label: sets-section-categories-schemes\n'
                '  Cov:\n    commands: ["text"]\n    usages: ["applied"]\n'
                '    source_label: sets-section-coverings-site\n')
        policy = Policy(old)
        items, _, _, errors = scan(r'$\text{size} + \text{Cov}_0 + G\textit{-Sets}$', policy)
        self.assertEqual([e['source'] for e in errors], ['size', 'Cov', '-Sets'])
        self.assertFalse(items)
        math = r'$\text{size}(S) + \text{Cov}(C)$'
        self.assertEqual(scan(math, policy), scan(math))

    def test_prefixed_usage_can_be_declared_for_an_identifier_without_aliases(self):
        policy = Policy(RAW.replace(ENTRY, ENTRY.replace('-Sets:', 'Things:').replace('"G"', '"H"')))
        items, _, _, errors = scan(r'$H\textit{Things}$', policy)
        self.assertFalse(errors)
        self.assertEqual(items[0]['usage_source'], 'H')
        self.assertTrue(scan(r'$G\textit{Things}$', policy)[-1])

    def test_policy_fields_prefix_and_usage_are_strict(self):
        self.assertIn(ENTRY, RAW)
        invalid = [ENTRY.replace('    prefix: "G"\n', ''),
                   ENTRY + '    prefix: "G"\n',
                   ENTRY.replace('    prefix:', '    unknown:'),
                   ENTRY.replace('["prefixed-symbol"]', '["prefixed-symbol", "symbol"]'),
                   ENTRY.replace('["prefixed-symbol"]', '["symbol"]'),
                   ENTRY.replace('["textit"]', '["text"]'),
                   ENTRY.replace('["textit"]', '["textit", "textbf"]'),
                   ENTRY.replace('-Sets:', '-Things:'), ENTRY.replace('-Sets:', 'Sets-and:'),
                   ENTRY.replace('-Sets:', 'Ｇroups:')]
        for value in ['null', '1', '["G"]', '""', '"GG"', '"g"', '"Γ"', '"G "', '"\\\\G"']:
            invalid.append(ENTRY.replace('"G"', value))
        for entry in invalid:
            with self.subTest(entry=entry), self.assertRaises(RecordError):
                Policy(RAW.replace(ENTRY, entry))
        with self.assertRaises(RecordError):
            Policy(RAW.replace('  size:\n', '  size:\n    prefix: "G"\n'))

    def test_inventory_locations_roundtrip_and_pure_math_segments(self):
        for prose in ['Café δ uses ', '']:
            math = '$G% original\n\\textit{-Sets}$'
            source = '\\begin{document}\n\\section{First}\\label{section-first}\n' + prose + math + '\n\\end{document}\n'
            raw = source.encode()
            rows, segments, errors = chapter_inventory('alpha', raw, 'a' * 40,
                {'alpha-section-first': 'AAAA'}, POLICY)
            self.assertFalse(errors)
            locations = rows if prose else segments
            classified = [r for r in locations if r.get('math_text_classifications')]
            self.assertEqual(len(classified), 1)
            item = classified[0]['math_text_classifications'][0]
            loc = item['location']
            self.assertEqual(raw[loc['byte_start']:loc['byte_end']], b'\\textit{-Sets}')
            self.assertEqual(item['usage_source'], 'G% original\n')
            if prose:
                self.assertIn(math, source_tex(classified[0]['unit']))
            else:
                self.assertIn(math, classified[0]['source'])


if __name__ == '__main__':
    unittest.main()
