"""Independent source-only fixtures; no model or human approval evidence."""
from pathlib import Path
import unittest
from stacks_zh.extraction import Policy, chapter_inventory
from stacks_zh.source_reextractions import source_tex

ROOT = Path(__file__).resolve().parents[1]
POLICY = Policy((ROOT / 'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0])
TAGS = {'test-section-first': '0000', 'test-lemma-first': '0001',
        'test-section-second': '0002', 'test-lemma-second': '0003'}
CLAIM = r'\begin{lemma}\label{lemma-first}First claim.\end{lemma}'
FIRST = r'\begin{proof}[First proof]Take $x$.\end{proof}'
SECOND = r'\begin{proof}[Second proof]Take $y$.\end{proof}'

def scan(middle, *, hierarchical=True):
    raw = ('\\begin{document}\n\\section{First}\\label{section-first}\n'
           + CLAIM + '\n' + middle + '\n' + FIRST + '\n' + SECOND
           + '\n\\end{document}\n').encode()
    rows, segments, errors = chapter_inventory('test', raw, 'a' * 40, TAGS, POLICY,
                                             hierarchical_prose=hierarchical)
    return raw, rows, segments, errors

class DeferredProofOwnerTests(unittest.TestCase):
    def test_complete_explanation_and_two_proofs_keep_owner_and_bytes(self):
        raw, rows, segments, errors = scan('\\noindent\nIn other words, $x=y$.\n\nWe give two proofs.')
        self.assertFalse(errors)
        proofs = [r for r in rows if r['unit']['node_kind'] == 'proof']
        self.assertEqual([(r['owner_tag'], r['parent_tag'], r['semantic_path']) for r in proofs],
                         [('0001', '0000', 'proof/0001'), ('0001', '0000', 'proof/0002')])
        self.assertEqual([source_tex(r['unit']) for r in proofs], [FIRST, SECOND])
        self.assertTrue(all(r['owner_tag'] == '0000' for r in rows if r['unit']['node_kind'] == 'paragraph'))
        by_id = {r['inventory_id']: r['unit'] for r in rows}
        self.assertEqual(''.join(source_tex(by_id[s['inventory_id']]) if s['kind'] == 'unit'
                                 else s['source'] for s in segments).encode(), raw)

    def test_flat_historical_inventory_keeps_unowned_proofs(self):
        _, rows, _, errors = scan('An explanation.', hierarchical=False)
        self.assertTrue(any(e['kind'] == 'ownership' for e in errors))
        self.assertTrue(all(r['owner_tag'] is None for r in rows if r['unit']['node_kind'] == 'proof'))

    def test_heading_literal_unknown_and_unlabelled_statement_break_chain(self):
        for middle in [r'\section{Second}\label{section-second}',
                       r'\begin{verbatim}example\end{verbatim}',
                       r'\unknown{explanation}',
                       r'\begin{lemma}Unlabelled new claim.\end{lemma}']:
            with self.subTest(middle=middle):
                _, rows, _, errors = scan(middle)
                self.assertTrue(any(e['kind'] == 'ownership' for e in errors))
                self.assertTrue(all(r['owner_tag'] is None for r in rows if r['unit']['node_kind'] == 'proof'))

    def test_new_labelled_statement_replaces_previous_owner(self):
        _, rows, _, errors = scan(r'\begin{lemma}\label{lemma-second}Next claim.\end{lemma}' + '\nExplanation.')
        self.assertFalse(errors)
        self.assertTrue(all(r['owner_tag'] == '0003' for r in rows if r['unit']['node_kind'] == 'proof'))
