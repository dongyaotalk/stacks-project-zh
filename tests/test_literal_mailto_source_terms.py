"""Literal protected mailto labels are addresses, while surrounding words remain terms."""
import copy
import unittest
from pathlib import Path

from stacks_zh.records import stamp_unit_hashes
from stacks_zh.source_terms import load_catalog, source_inventory, source_projection
from stacks_zh.source_reextractions import source_tex

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(ROOT)


def unit(text, opening=r'\href{mailto:stacks.project@gmail.com}{', closing='}'):
    return stamp_unit_hashes(dict(schema_version=1, unit_id='fixture:mailto',
        chapter='descent', parent_tag='AAAA', node_kind='paragraph',
        source_commit=CATALOG['source_commit'], source_status='CURRENT',
        source_text=text, placeholders={'TEXTOPEN_0001': opening, 'TEXTCLOSE_0001': closing},
        render={'prefix':'','suffix':'\n'}))


def words(row):
    return [o['source_term'] for o in source_inventory(row, CATALOG)['occurrences']]


class LiteralMailtoSourceTermsTests(unittest.TestCase):
    def test_only_the_address_word_is_excluded_and_all_source_bytes_remain(self):
        row = unit('Stacks <TEXTOPEN_0001>stacks.project@gmail.com<TEXTCLOSE_0001> stacks.')
        before = copy.deepcopy(row)
        tex = source_tex(row)
        projection = source_projection(row)
        self.assertEqual(words(row), ['Stacks', 'stacks'])
        self.assertEqual(row, before)
        self.assertEqual(source_tex(row), tex)
        self.assertEqual(source_projection(row), projection)
        self.assertIn('stacks.project@gmail.com', projection[0])

    def test_same_literal_address_elsewhere_cannot_borrow_the_protected_label(self):
        row = unit('stacks.project@gmail.com; <TEXTOPEN_0001>stacks.project@gmail.com<TEXTCLOSE_0001>; stacks.project@gmail.com.')
        result = source_inventory(row, CATALOG)['occurrences']
        self.assertEqual([o['source_term'] for o in result], ['stacks','stacks'])
        text = source_projection(row)[0]
        self.assertEqual([text[o['projection_start']:o['projection_end']] for o in result], ['stacks','stacks'])

    def test_multiple_known_mailto_labels_are_independently_matched(self):
        row = unit('<TEXTOPEN_0001>stacks.project@gmail.com<TEXTCLOSE_0001> stacks <TEXTOPEN_0002>stacks.project@gmail.com<TEXTCLOSE_0002>')
        row['placeholders'].update(TEXTOPEN_0002=row['placeholders']['TEXTOPEN_0001'], TEXTCLOSE_0002='}')
        row = stamp_unit_hashes(row)
        self.assertEqual(words(row), ['stacks'])

    def test_matching_case_domains_and_plus_addresses_are_literal(self):
        for address in ['Stacks.project@math.example', 'stacks+test@math.example',
                        'stacks@math.example', 'stacks@morphisms.example']:
            with self.subTest(address=address):
                row = unit('<TEXTOPEN_0001>'+address+'<TEXTCLOSE_0001>', '\\href{mailto:'+address+'}{')
                self.assertEqual(words(row), [])

    def test_unknown_mismatched_or_nonliteral_wrappers_do_not_exempt_terms(self):
        cases = [
            ('<TEXTOPEN_0001>stacks.project@gmail.com<TEXTCLOSE_0001>', r'\href{https://math.example}{','}'),
            ('<TEXTOPEN_0001>Stacks.project@gmail.com<TEXTCLOSE_0001>', r'\href{mailto:stacks.project@gmail.com}{','}'),
            ('<TEXTOPEN_0001>stacks<TEXTCLOSE_0001>', r'\href{mailto:stacks.project@gmail.com}{','}'),
            ('<TEXTOPEN_0001>stacks.project@gmail.com <TEXTCLOSE_0001>', r'\href{mailto:stacks.project@gmail.com}{','}'),
            ('<TEXTOPEN_0001>stacks.project@gmail.com<TEXTCLOSE_0002>', r'\href{mailto:stacks.project@gmail.com}{','}'),
            ('<TEXTOPEN_0001>stacks.project@gmail.com<TEXTCLOSE_0001>', r'\unknown{mailto:stacks.project@gmail.com}{','}'),
            ('<TEXTOPEN_0001>stacks.project@gmail.com<TEXTCLOSE_0001>', r'\href{mailto:stacks.project@gmail.com}{',r'}\unknown'),
            ('<TEXTOPEN_0001>stacks..project@gmail.com<TEXTCLOSE_0001>', r'\href{mailto:stacks..project@gmail.com}{','}'),
            ('<TEXTOPEN_0001>stacks@localhost<TEXTCLOSE_0001>', r'\href{mailto:stacks@localhost}{','}'),
            ('<TEXTOPEN_0001>stacks@math.example.<TEXTCLOSE_0001>', r'\href{mailto:stacks@math.example.}{','}'),
        ]
        for text, opening, closing in cases:
            with self.subTest(text=text,opening=opening,closing=closing):
                self.assertEqual(len(words(unit(text,opening,closing))),1)

    def test_address_declaration_is_excluded_without_hiding_a_later_mathematical_word(self):
        row = unit('<TEXTITOPEN_0002><TEXTOPEN_0001>stacks.project@gmail.com<TEXTCLOSE_0001><TEXTITCLOSE_0002> is defined; stacks.')
        row['node_kind'] = 'definition'
        row['placeholders'].update(TEXTITOPEN_0002=r'\textit{', TEXTITCLOSE_0002='}')
        row = stamp_unit_hashes(row)
        self.assertIn('stacks.project@gmail.com', source_projection(row)[1])
        self.assertEqual(words(row), ['stacks'])

    def test_projection_that_constructs_an_extra_address_does_not_exempt_any_occurrence(self):
        row = unit('<TEXTOPEN_0001>stacks.project@gmail.com<TEXTCLOSE_0001>; st<EMPHOPEN_0002>acks<EMPHCLOSE_0002>.project@gmail.com.')
        row['placeholders'].update(EMPHOPEN_0002=r'\emph{', EMPHCLOSE_0002='}')
        row = stamp_unit_hashes(row)
        self.assertEqual(source_projection(row)[0].count('stacks.project@gmail.com'), 2)
        self.assertEqual(words(row), ['stacks', 'stacks'])

    def test_repeated_boundary_tokens_are_not_a_unique_protected_label(self):
        address = '<TEXTOPEN_0001>stacks.project@gmail.com<TEXTCLOSE_0001>'
        self.assertEqual(words(unit(address+'; '+address)), ['stacks', 'stacks'])

    def test_ordinary_stack_terms_and_math_tokens_are_unchanged(self):
        row = unit('A category of stacks and morphisms.')
        self.assertEqual(words(row),['category','stacks','morphisms'])


if __name__ == '__main__':
    unittest.main()
