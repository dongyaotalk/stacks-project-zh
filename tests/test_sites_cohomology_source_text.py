"""Synthetic boundary regressions; never actual model output or adopted data."""
import copy
import unittest
from pathlib import Path

from stacks_zh.records import stamp_unit_hashes
from stacks_zh.source_terms import load_catalog, source_inventory, source_projection, validate_source_terms


def protected_unit(text, placeholders, kind='paragraph'):
    return stamp_unit_hashes(dict(schema_version=1, unit_id='tag:ABCD:prose-0001',
        chapter='sites-cohomology', parent_tag='ABCD', node_kind=kind, risk_level='R3',
        source_commit='a' * 40, source_status='CURRENT', source_text=text,
        placeholders=placeholders, render=dict(prefix='', suffix='')))


class QualifiedDeclarationTests(unittest.TestCase):
    def test_complete_cohomology_description_requires_terms_without_grammar_fragments(self):
        row = protected_unit(
            'We define the <TEXTITOPEN_0001>the <MATH_0001>th cohomology group '
            'of the abelian sheaf <MATH_0002> over the object <MATH_0003>'
            '<TEXTITCLOSE_0001>.',
            dict(TEXTITOPEN_0001=r'\textit{', TEXTITCLOSE_0001='}',
                 MATH_0001='$p$', MATH_0002='$F$', MATH_0003='$U$'))
        before = copy.deepcopy(row)
        words = load_catalog(Path(__file__).resolve().parents[1])
        required = [x['source_term'] for x in source_inventory(row, words)['occurrences']]
        self.assertEqual(required, ['cohomology group', 'abelian sheaf', 'object'])
        self.assertEqual(row, before)
        candidate = dict(translation='第<MATH_0001>个上同调群（cohomology group），'
            '针对阿贝尔层（abelian sheaf）<MATH_0002>在对象（object）<MATH_0003>上',
            term_status='DECISION_REQUIRED',
            term_occurrences=[dict(source_term=en, target_term=zh) for en, zh in
                [('cohomology group', '上同调群'), ('abelian sheaf', '阿贝尔层'), ('object', '对象')]],
            unknown_terms=[dict(source_term=en, target_term=zh, context='Synthetic pending term.')
                for en, zh in [('cohomology group', '上同调群'), ('abelian sheaf', '阿贝尔层'), ('object', '对象')]])
        self.assertEqual(validate_source_terms(row, candidate, words), [])
        missing = copy.deepcopy(candidate)
        missing['term_occurrences'].pop(1)
        self.assertTrue(any('abelian sheaf' in e for e in validate_source_terms(row, missing, words)))

    def test_precise_math_qualified_ordered_descriptions(self):
        for body, expected in [
            ('<MATH_0001>th cohomology group of <MATH_0002> on <MATH_0003>', ['cohomology group']),
            ('the <MATH_0001>th cohomology group of <MATH_0002> over <MATH_0003>', ['cohomology group']),
            ('<MATH_0001>th higher direct image of <MATH_0002>', ['higher direct image']),
            ('morphism of pseudo <MATH_0001>-torsors', ['morphism', 'pseudo', 'torsors'])]:
            row = protected_unit('We define <TEXTITOPEN_0001>' + body + '<TEXTITCLOSE_0001>.',
                dict(TEXTITOPEN_0001=r'\textit{', TEXTITCLOSE_0001='}',
                     MATH_0001='$p$', MATH_0002='$F$', MATH_0003='$U$'))
            with self.subTest(body=body):
                self.assertEqual(source_projection(row)[1], sorted(expected))

    def test_other_qualifiers_and_nonmath_tokens_do_not_borrow_description_contract(self):
        bodies = ['<REF_0001>th cohomology group of <MATH_0002> on <MATH_0003>',
                  '<MATH_0001>th cohomology group assuming a special convention',
                  '<MATH_0001>th higher direct images of <MATH_0002>']
        for body in bodies:
            row = protected_unit('We define <TEXTITOPEN_0001>' + body + '<TEXTITCLOSE_0001>.',
                dict(TEXTITOPEN_0001=r'\textit{', TEXTITCLOSE_0001='}', REF_0001=r'\ref{x}',
                     MATH_0001='$p$', MATH_0002='$F$', MATH_0003='$U$'))
            with self.subTest(body=body):
                self.assertTrue(any('th ' in phrase for phrase in source_projection(row)[1]))

    def test_caron_name_preserves_bytes_and_requires_lexical_math_core(self):
        row = protected_unit('We define <TEXTITOPEN_0001><GROUPOPEN_0001>'
            '<ACCENT_0001><GROUPCLOSE_0001>ech cohomology groups<TEXTITCLOSE_0001>.',
            dict(TEXTITOPEN_0001=r'\textit{', TEXTITCLOSE_0001='}',
                 GROUPOPEN_0001='{', ACCENT_0001=r'\v C', GROUPCLOSE_0001='}'))
        before = copy.deepcopy(row)
        self.assertEqual(source_projection(row)[1], ['cohomology groups'])
        self.assertEqual(row, before)
        bad = copy.deepcopy(row)
        bad['placeholders']['ACCENT_0001'] = r'\v D'
        self.assertIn('ech cohomology groups', source_projection(bad)[1])


class AssignmentBoundaryTests(unittest.TestCase):
    def inventory(self, text, placeholders=None):
        row = protected_unit(text, placeholders or dict(MATH_0001='$x$'))
        return [x['source_term'] for x in source_inventory(row,
            load_catalog(Path(__file__).resolve().parents[1]))['occurrences']]

    def test_real_bounded_assignment_frames_do_not_turn_verb_into_set(self):
        for text, payloads in [
            ('Namely, set <MATH_0001>.', dict(MATH_0001='$x$')),
            ('A condition may fail. Namely, set <MATH_0001>.', dict(MATH_0001='$x$')),
            ('In the situation of Lemma <REF_0001> set <MATH_0001>.',
                dict(REF_0001=r'\ref{lemma-example}', MATH_0001='$x$')),
            ('Earlier text. <STRUCT_0001><STRUCT_0002> Set <MATH_0001>.',
                dict(STRUCT_0001=r'\medskip', STRUCT_0002=r'\noindent', MATH_0001='$x$'))]:
            with self.subTest(text=text):
                self.assertNotIn('set', [x.casefold() for x in self.inventory(text, payloads)])

    def test_sets_and_unknown_or_spoofed_boundaries_keep_requirements(self):
        for text, payloads in [
            ('Namely, the set <MATH_0001>.', dict(MATH_0001='$x$')),
            ('Namely set <MATH_0001>.', dict(MATH_0001='$x$')),
            ('We mention namely, set <MATH_0001>.', dict(MATH_0001='$x$')),
            ('Namely, set <REF_0001>.', dict(REF_0001=r'\ref{x}')),
            ('In the situation of Theorem <REF_0001> set <MATH_0001>.',
                dict(REF_0001=r'\ref{x}', MATH_0001='$x$')),
            ('<STRUCT_0001><STRUCT_0002> Set <MATH_0001>.',
                dict(STRUCT_0001=r'\item', STRUCT_0002=r'\noindent', MATH_0001='$x$'))]:
            with self.subTest(text=text):
                self.assertIn('set', [x.casefold() for x in self.inventory(text, payloads)])


if __name__ == '__main__':
    unittest.main()
