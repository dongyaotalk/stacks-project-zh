"""Source-only synthetic fixtures; no fixture claims an actual model run."""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stacks_zh.cli import main
from stacks_zh.extraction import Policy, Scanner, build_inventory, chapter_inventory, write_inventory
from stacks_zh.records import RecordError
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_reextractions import source_tex

POLICY_RAW = (Path(__file__).resolve().parents[1] / 'config/macro-policy.yml').read_text()
POLICY = Policy(POLICY_RAW)
TAGS = {'alpha-section-phantom': 'AAAA', 'alpha-section-first': 'BBBB',
        'alpha-lemma-one': 'CCCC', 'alpha-item-one': 'DDDD'}
COMMIT = 'a' * 40


def inventory(body):
    return chapter_inventory('alpha', ('\\begin{document}\n' + body + '\n\\end{document}\n').encode(), COMMIT, TAGS, POLICY)


class ExtractionTests(unittest.TestCase):
    def test_nested_footnotes_fonts_and_protected_math_roundtrip(self):
        body = (r'\section{First}\label{section-first}' + '\n'
                r'A {\it category} $x$ has a footnote\footnote{First $y$. ' + '\n\n'
                r'Second \textbf{part} with \ref{lemma-one}.} and \href{https://example.test/a_b}{a link}.' )
        rows, segments, errors = inventory(body)
        self.assertFalse(errors)
        prose = rows[-1]['unit']
        self.assertIn('First <MATH_', prose['source_text'])
        self.assertIn('Second <TEXTBFOPEN_', prose['source_text'])
        self.assertEqual(sum(p.startswith('FOOTNOTEOPEN_') for p in prose['placeholders']), 1)
        self.assertIn('https://example.test/a_b', ''.join(prose['placeholders'].values()))
        for row in rows:
            self.assertFalse(validate_named_schema(row['unit'], 'unit.schema.json', 'fixture'))
        self.assertTrue(all(row['state'] == 'READY' for row in rows))

    def test_statements_multiple_complete_proofs_lists_and_titles(self):
        body = (r'\section{First}\label{section-first}' + '\n'
                r'\begin{lemma}[A $1$ title]\label{lemma-one}Let $x$ be a set.'
                r'\begin{enumerate}\item One.\item Two.\end{enumerate}\end{lemma}' + '\n'
                r'\begin{proof}[First proof]First $x$.' + '\n\n'
                r'Second \footnote{An explanation.}\end{proof}' + '\n% comment\n'
                r'\begin{proof}[Second proof]Another proof.\end{proof}')
        rows, _, errors = inventory(body)
        self.assertFalse(errors)
        proofs = [r for r in rows if r['unit']['node_kind'] == 'proof']
        self.assertEqual(len(proofs), 2)
        self.assertEqual([r['owner_tag'] for r in proofs], ['CCCC', 'CCCC'])
        self.assertIn('First proof', proofs[0]['unit']['source_text'])
        self.assertIn('Second <FOOTNOTEOPEN_', proofs[0]['unit']['source_text'])
        self.assertNotEqual(proofs[0]['inventory_id'], proofs[1]['inventory_id'])
        lemma = [r for r in rows if r['unit']['node_kind'] == 'lemma'][0]
        self.assertEqual(lemma['owner_tag'], 'CCCC')
        self.assertIn('title', lemma['unit']['source_text'])
        self.assertIn('Two.', lemma['unit']['source_text'])

    def test_math_delimiters_environments_comments_and_escapes(self):
        body = (r'\section{First}\label{section-first}' + '\n'
                r'Use $x\$y$, $$z$$, \(u\), \[v\], and \% literal.' + '\n% hidden $ and }\n'
                r'Finish.\begin{align*}a & = b \\ c &= d\end{align*}')
        rows, _, errors = inventory(body)
        self.assertFalse(errors)
        payloads = [p for row in rows for k, p in row['unit']['placeholders'].items() if k.startswith('MATH_')]
        self.assertEqual(payloads[:4], [r'$x\$y$', '$$z$$', r'\(u\)', r'\[v\]'])
        self.assertTrue(any(r'\% literal' in source_tex(r['unit']) for r in rows))

    def test_locked_metadata_and_literal_cannot_create_fake_structure(self):
        body = (r'\section{First}\label{section-first}' + '\n'
                r'\begin{verbatim}\begin{foo}$unclosed \label{lemma-one}\end{verbatim}'
                r'\begin{reference}English metadata.\end{reference}'
                '\nA real paragraph.')
        rows, segments, errors = inventory(body)
        self.assertFalse(errors)
        self.assertIn('verbatim', {s['kind'] for s in segments})
        self.assertIn('reference', {s['kind'] for s in segments})
        self.assertNotIn('English metadata', ''.join(r['unit']['source_text'] for r in rows))

    def test_document_examples_in_verbatim_do_not_confuse_real_boundary(self):
        body = (r'\section{First}\label{section-first}' + '\n'
                '\\begin{verbatim}\n\\begin{document}\n\\end{document}\n\\end{verbatim}\n'
                'Actual prose.')
        rows, _, errors = inventory(body)
        self.assertFalse(errors)
        self.assertIn('Actual prose.', rows[-1]['unit']['source_text'])

    def test_missing_document_closing_and_extra_document_are_blocked(self):
        text = '\\begin{document}\n\\section{First}\\label{section-first}\nActual prose.'
        rows, _, errors = chapter_inventory('alpha', text.encode(), COMMIT, TAGS, POLICY)
        self.assertTrue(any(e['message'] == 'missing document closing' for e in errors))
        self.assertTrue(all(r['state'] == 'BLOCKED' for r in rows))
        extra = text + '\n\\end{document}\n\\begin{document}Other words.\\end{document}'
        _, _, errors = chapter_inventory('alpha', extra.encode(), COMMIT, TAGS, POLICY)
        self.assertTrue(any(e['kind'] == 'document-footer' for e in errors))

    def test_empty_source_is_not_a_ready_inventory(self):
        rows, segments, errors = chapter_inventory('alpha', b'', COMMIT, TAGS, POLICY)
        self.assertEqual(rows, [])
        self.assertEqual(segments, [])
        self.assertTrue(any(e['message'] == 'empty source document' for e in errors))

    def test_unknown_commands_math_text_and_index_are_explicit_blockers(self):
        body = (r'\section{First}\label{section-first}' + '\n'
                r'A \mystery{hidden words} $x\text{ and }y$\index{entry} end.')
        rows, _, errors = inventory(body)
        self.assertEqual(rows[-1]['state'], 'BLOCKED')
        self.assertEqual({e['kind'] for e in errors}, {'unknown-command', 'math-text', 'index-record'})
        self.assertIn('hidden words', ''.join(e['source'] for e in errors))
        self.assertTrue(any(e['source'] == ' and ' for e in errors))

    def test_math_text_inventory_ignores_comments_and_escaped_backslashes(self):
        body = (r'\section{First}\label{section-first}' + '\nA $x % \\text{comment}\n'
                r'\\text{literal} + \text{real words}$ end.')
        _, _, errors = inventory(body)
        self.assertEqual([e['source'] for e in errors if e['kind'] == 'math-text'], ['real words'])

    def test_invalid_syntax_preserves_tail_and_never_claims_ready(self):
        body = r'\section{First}\label{section-first}' + '\nA $unclosed.'
        rows, segments, errors = inventory(body)
        self.assertEqual(rows[-1]['state'], 'BLOCKED')
        self.assertTrue(any(e['kind'] == 'syntax' for e in errors))
        self.assertIn('A $unclosed.', source_tex(rows[-1]['unit']))

    def test_utf8_offsets_cover_exact_original_bytes(self):
        body = r'\section{First}\label{section-first}' + '\nCafé and δ words.'
        raw = ('\\begin{document}\n' + body + '\n\\end{document}\n').encode()
        rows, segments, errors = chapter_inventory('alpha', raw, COMMIT, TAGS, POLICY)
        self.assertFalse(errors)
        by_id = {r['inventory_id']: r['unit'] for r in rows}
        for segment in segments:
            source = source_tex(by_id[segment['inventory_id']]) if segment['kind'] == 'unit' else segment['source']
            loc = segment['location']
            self.assertEqual(raw[loc['byte_start']:loc['byte_end']], source.encode())
        self.assertEqual(segments[-1]['location']['byte_end'], len(raw))

    def fixture(self, base, missing=False):
        root, harvest = base / 'chinese', base / 'english'
        (root / 'config').mkdir(parents=True); (harvest / 'tags').mkdir(parents=True)
        (root / 'config/macro-policy.yml').write_text(POLICY_RAW)
        (harvest / 'chapters.tex').write_text(r'\item \hyperref[alpha-section-phantom]{Alpha}' + '\n' +
                    (r'\item \hyperref[index-section-phantom]{Index}' + '\n' if missing else ''))
        (harvest / 'alpha.tex').write_text('\\begin{document}\n\\section{First}\\label{section-first}\nA category.\n\\end{document}\n')
        (harvest / 'tags/tags').write_text(''.join(tag + ',' + label + '\n' for label, tag in TAGS.items()))
        subprocess.run(['git', 'init', '-q', str(harvest)], check=True)
        subprocess.run(['git', '-C', str(harvest), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(harvest), '-c', 'user.name=Synthetic Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Synthetic source fixture'], check=True)
        commit = subprocess.check_output(['git', '-C', str(harvest), 'rev-parse', 'HEAD'], text=True).strip()
        (root / 'upstream.lock').write_text(f'commit = "{commit}"\n')
        return root, harvest

    def test_reads_locked_git_not_dirty_worktree_and_reports_missing_blob(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest = self.fixture(Path(temp), missing=True)
            (harvest / 'alpha.tex').write_text('malicious dirty replacement')
            manifest, rows, _, _ = build_inventory(root, harvest)
            self.assertEqual(manifest['chapter_count'], 2)
            self.assertEqual(manifest['roundtrip_files'], 1)
            self.assertEqual(manifest['source_unavailable'], ['index'])
            self.assertIn('A category.', ''.join(r['unit']['source_text'] for r in rows))
            self.assertFalse(manifest['translation_ready'])

    def test_deterministic_check_detects_missing_extra_and_modified_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest = self.fixture(Path(temp)); output = root / 'source-ir/extraction'
            first = write_inventory(root, harvest, output)
            self.assertEqual(first, write_inventory(root, harvest, output, check=True))
            (output / 'extra').write_text('unrelated')
            with self.assertRaises(RecordError):write_inventory(root, harvest, output, check=True)
            with self.assertRaises(RecordError):write_inventory(root, harvest, output)
            (output / 'extra').unlink(); (output / 'units.jsonl').write_text('')
            with self.assertRaisesRegex(RecordError, 'out of date'):write_inventory(root, harvest, output, check=True)

    def test_output_safety_and_failed_write_preserve_existing_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest = self.fixture(Path(temp)); output = root / 'source-ir/extraction'
            write_inventory(root, harvest, output)
            before = {p.name:p.read_bytes() for p in output.iterdir()}
            with self.assertRaises(RecordError):write_inventory(root, harvest, root / 'translation-data/units')
            link = root / 'source-ir/link'; link.symlink_to(output, target_is_directory=True)
            with self.assertRaises(RecordError):write_inventory(root, harvest, link)
            with patch.object(Path, 'write_bytes', side_effect=OSError('synthetic write failure')):
                with self.assertRaises(OSError):write_inventory(root, harvest, output)
            self.assertEqual(before, {p.name:p.read_bytes() for p in output.iterdir()})

    def test_unique_exact_existing_source_match_and_owner_required(self):
        rows, _, _ = inventory(r'\section{First}\label{section-first}' + '\nA category.')
        row = rows[-1]; unit = {**row['unit'], 'unit_id': 'tag:BBBB:p001', '_owner': 'BBBB'}
        index = {('alpha', row['location']['fragment_hash']): [unit]}
        raw = ('\\begin{document}\n\\section{First}\\label{section-first}\nA category.\n\\end{document}\n').encode()
        result, _, _ = chapter_inventory('alpha', raw, COMMIT, TAGS, POLICY, index)
        self.assertEqual(result[-1]['existing_unit_id'], 'tag:BBBB:p001')
        unit['_owner'] = 'CCCC'
        result, _, _ = chapter_inventory('alpha', raw, COMMIT, TAGS, POLICY, index)
        self.assertIsNone(result[-1]['existing_unit_id'])
        unit['_owner'] = 'BBBB'; index[('alpha', row['location']['fragment_hash'])] = [unit, unit]
        result, _, _ = chapter_inventory('alpha', raw, COMMIT, TAGS, POLICY, index)
        self.assertIsNone(result[-1]['existing_unit_id'])

    def test_failed_directory_swap_restores_previous_complete_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest = self.fixture(Path(temp)); output = root / 'source-ir/extraction'
            write_inventory(root, harvest, output)
            before = {p.name:p.read_bytes() for p in output.iterdir()}
            original, calls = Path.rename, []
            def rename(path, target):
                calls.append(path)
                if len(calls) == 2:
                    raise OSError('synthetic swap failure')
                return original(path, target)
            with patch.object(Path, 'rename', rename):
                with self.assertRaises(OSError):write_inventory(root, harvest, output)
            self.assertEqual(before, {p.name:p.read_bytes() for p in output.iterdir()})

    def test_cli_complete_inventory_and_require_ready_have_distinct_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest = self.fixture(Path(temp), missing=True)
            args = ['extract-all', '--root', str(root), '--harvest', str(harvest)]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(args), 0)
                self.assertEqual(main(args + ['--require-ready']), 1)
                self.assertEqual(main(args + ['--chapter', 'alpha', '--output', 'build/selected']), 0)
                self.assertEqual(main(args + ['--chapter', 'absent']), 1)


if __name__ == '__main__':
    unittest.main()
