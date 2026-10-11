from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from stacks_zh.records import RecordError, stamp_unit_hashes, write_jsonl
from stacks_zh.workflow import render_batch
from test_workflow import SOURCE_COMMIT, make_batch_candidate, make_batch_unit


class ChapterPreviewTests(unittest.TestCase):
    def prepare(self, root):
        lock = root / 'upstream.lock'
        lock.write_text(f'commit = "{SOURCE_COMMIT}"\n')
        manifest = root / 'chapters.tex'
        manifest.write_text('\\item \\hyperref[alpha-section-phantom]{Alpha}\n'
                            '\\item \\hyperref[beta-section-phantom]{Beta}\n')
        units, candidates = [], []
        for name, chapter in [('a', 'alpha'), ('b', 'beta'), ('c', 'beta')]:
            unit = make_batch_unit(f'tag:TEST:{name}')
            unit['chapter'] = chapter
            unit['source_text'] = 'See <REF_0001>.' if name == 'b' else 'Source.'
            unit['placeholders'] = {'REF_0001': '\\ref{alpha-target}'} if name == 'b' else {}
            if name == 'a':
                unit['render']['suffix'] += '\\label{alpha-target}\n'
            unit = stamp_unit_hashes(unit)
            candidate = make_batch_candidate(unit)
            candidate['translation'] = '见 <REF_0001>。' if name == 'b' else f'译文{name}。'
            if name != 'b':
                candidate['translation'] = '首段。' if name == 'a' else '末段。'
            up = root / 'units' / f'{name}.jsonl'
            cp = root / 'candidates' / f'{name}.jsonl'
            write_jsonl(up, [unit]); write_jsonl(cp, [candidate])
            units.append(up); candidates.append(cp)
        tags = root / 'tags'; tags.write_text('ABCD,alpha-target\n')
        return units, candidates, lock, manifest, tags

    def render(self, root, inputs, **kwargs):
        units, candidates, lock, manifest, tags = inputs
        return render_batch(units, candidates, lock, root / 'test-chapter-beta',
                            'test', '章预览', manifest, tags_path=tags,
                            chapter='beta', **kwargs)

    def test_whole_chapter_all_batches_original_number_and_cross_chapter_tag(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = self.prepare(root)
            full = root / 'full'
            render_batch(inputs[0], inputs[1], inputs[2], full, 'test', '整书',
                         inputs[3], tags_path=inputs[4])
            before = {p.relative_to(full): p.read_bytes() for p in full.rglob('*') if p.is_file()}
            self.render(root, inputs)
            out = root / 'test-chapter-beta'
            self.assertEqual(sorted(p.name for p in (out/'chapters').iterdir()), ['beta.tex'])
            text = (out/'chapters/beta.tex').read_text()
            self.assertIn('末段。', text)
            self.assertIn('Tag ABCD（待译）', text)
            self.assertNotIn('\\ref{alpha-target}', text)
            self.assertIn('\\ref{alpha-target}', (full/'chapters/beta.tex').read_text())
            self.assertEqual((out/'contents.tex').read_text(),
                             '% Generated from translation-data; do not edit.\n'
                             '\\setcounter{chapter}{1}\n'
                             '\\input{\\TranslationModelDirectory/chapters/beta}\n')
            self.assertIn('仅含 beta 章的开发预览', (out/'metadata.tex').read_text())
            self.assertEqual(before, {p.relative_to(full): p.read_bytes() for p in full.rglob('*') if p.is_file()})

    def test_rejects_last_batch_errors_and_mixed_chapter_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); inputs = self.prepare(root)
            unit = make_batch_unit('tag:TEST:bad'); unit['chapter'] = 'alpha'
            write_jsonl(inputs[0][-1], [make_batch_unit('tag:TEST:first'), unit])
            # Explicitly include beta in a mixed batch; never silently take only its rows.
            first = make_batch_unit('tag:TEST:first'); first['chapter'] = 'beta'
            write_jsonl(inputs[0][-1], [first, unit])
            with self.assertRaisesRegex(RecordError, 'mixed-chapter'):
                self.render(root, inputs)
            inputs = self.prepare(root)
            inputs[1][-1].write_text('{}\n')
            with self.assertRaisesRegex(RecordError, 'validation errors'):
                self.render(root, inputs)
            self.assertFalse((root/'test-chapter-beta').exists())

    def test_rejects_overwriting_full_lane_and_mispaired_or_missing_chapter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); u,c,lock,manifest,tags = self.prepare(root)
            for output, chapter, pairs, message in [
                (root/'test', 'beta', c, 'own model-chapter'),
                (root/'test-chapter-missing', 'missing', c, 'no candidate batches'),
                (root/'test-chapter-beta', 'beta', list(reversed(c)), 'names must match'),
                (root/'test-chapter-../beta', '../beta', c, 'invalid preview chapter'),
            ]:
                with self.subTest(chapter=chapter, message=message):
                    with self.assertRaisesRegex(RecordError, message):
                        render_batch(u,c if pairs is c else pairs,lock,output,'test','预览',
                                     manifest,tags_path=tags,chapter=chapter)

    def test_make_preview_recipe_has_distinct_model_aux_pdf_and_final_gate(self):
        result = subprocess.run(['make','-n','pdf-chapter','MODEL=openai-gpt-5.6-sol',
                                 'CHAPTER=categories'], cwd=Path(__file__).parents[1],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--chapter "categories"', result.stdout)
        self.assertIn('translations/openai-gpt-5.6-sol-chapter-categories', result.stdout)
        self.assertIn('build/chapter-preview/ajbook/openai-gpt-5.6-sol-chapter-categories', result.stdout)
        self.assertIn('output/pdf/chapter-preview/', result.stdout)
        self.assertIn('check-build-log', result.stdout)


if __name__ == '__main__':
    unittest.main()
