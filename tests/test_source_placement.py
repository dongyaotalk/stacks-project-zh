"""Synthetic Git fixtures only; these are not translations or model runs."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stacks_zh.records import (ASCII_WORD_RE, PLACEHOLDER_TOKEN_RE, RecordError,
                               stamp_unit_hashes, term_display_text, write_jsonl)
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_placement import complete_prose_positions
from stacks_zh.workflow import _order_unit_batches_by_chapter_source, render_batch
from test_source_containers import fixture, selector
from test_workflow import make_batch_candidate


class CompleteProsePlacementTests(unittest.TestCase):
    def fixture(self, base):
        body = ('\\noindent\nFirst paragraph café $X$.\n\n'
                'Second paragraph.\\footnote{Complete note $Y$.}\n'
                '\\begin{enumerate}\n\\item One condition $Z$.\n\\end{enumerate}\n'
                '\nLast paragraph.\n')
        root, harvest, sha = fixture(base, statement=body +
            '\\begin{lemma}\\label{lemma-one}A claim.\\end{lemma}',
            proof='\\begin{proof}Omitted.\\end{proof}')
        native = Containers(root, harvest)
        chosen = native.select(selector('prose_block', owner='0000'))
        prose = lower_container(chosen, native.policy)[0]
        heading = lower_container(native.select(selector('section_title', owner='0000')), native.policy)[0]
        lemma = lower_container(native.select(selector('lemma')), native.policy)[0]
        return root, harvest, sha, native, chosen, prose, heading, lemma

    def test_complete_multi_paragraph_list_note_placed_between_separate_batches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, selected, prose, heading, lemma = self.fixture(Path(tmp))
            batches = [[lemma], [prose], [heading]]
            snapshot = copy.deepcopy(batches)
            raw = (harvest / 'test.tex').read_bytes()
            positions = complete_prose_positions(batches, {1}, root, harvest, 'test', raw)
            self.assertEqual(positions[1], selected['location']['byte_start'])
            self.assertNotEqual(raw.index(b'\\begin{lemma}'), len(raw[:raw.index(b'\\begin{lemma}')].decode()))
            ordered = _order_unit_batches_by_chapter_source(batches, harvest, root=root)
            self.assertEqual(ordered, [heading, prose, lemma])
            self.assertEqual(batches, snapshot)

    def test_complete_lowering_identity_text_math_note_list_and_outer_bytes_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _, prose, heading, lemma = self.fixture(Path(tmp))
            variants = []
            for key, value in [('unit_id', 'tag:0001:prose-0001'),
                ('unit_id', 'tag:0000:prose-0002'), ('parent_tag', '0001'),
                ('source_commit', 'f' * 40), ('schema_version', 2),
                ('node_kind', 'proof'), ('risk_level', 'R1')]:
                changed = copy.deepcopy(prose); changed[key] = value; variants.append(changed)
            for field, old, new in [('source_text', 'First', 'Changed'),
                ('source_text', 'Complete note', 'Truncated note'),
                ('source_text', 'One condition', 'Different condition')]:
                changed = copy.deepcopy(prose); self.assertIn(old, changed[field])
                changed[field] = changed[field].replace(old, new); variants.append(changed)
            changed = copy.deepcopy(prose); changed['source_text'] = changed['source_text'].strip(); variants.append(changed)
            changed = copy.deepcopy(prose); changed['placeholders']['MATH_0001'] = '$Q$'; variants.append(changed)
            changed = copy.deepcopy(prose); changed['render']['prefix'] = '\\label{test-lemma-one}'; variants.append(changed)
            for changed in variants:
                with self.subTest(changed=changed):
                    with self.assertRaises(RecordError):
                        checked = stamp_unit_hashes(changed) if changed['schema_version'] == 1 else changed
                        complete_prose_positions([[heading], [checked], [lemma]],
                            {1}, root, harvest, 'test', (harvest / 'test.tex').read_bytes())

    def test_arbitrary_unlabeled_mixed_batch_and_duplicate_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _, prose, heading, lemma = self.fixture(Path(tmp))
            for batches, indices in [([[{**prose, 'unit_id': 'tag:0000:p001'}]], {0}),
                    ([[prose, prose]], {0}), ([[prose], [copy.deepcopy(prose)]], {0, 1})]:
                with self.subTest(indices=indices):
                    with self.assertRaises(RecordError):
                        complete_prose_positions(batches, indices, root, harvest, 'test',
                            (harvest / 'test.tex').read_bytes())
            with self.assertRaisesRegex(RecordError, 'repository and locked Git'):
                _order_unit_batches_by_chapter_source([[heading], [prose], [lemma]], harvest)

    def test_overlap_with_old_paragraph_and_interleaving_old_batch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, native, _, prose, heading, lemma = self.fixture(Path(tmp))
            paragraph = lower_container(native.select(selector('paragraph', owner='0000')), native.policy)[0]
            with self.assertRaisesRegex(RecordError, 'overlaps'):
                complete_prose_positions([[prose], [heading, paragraph]], {0}, root, harvest,
                    'test', (harvest / 'test.tex').read_bytes())
            with self.assertRaisesRegex(RecordError, 'interleave'):
                complete_prose_positions([[prose], [heading, lemma]], {0}, root, harvest,
                    'test', (harvest / 'test.tex').read_bytes())

    def test_worktree_cannot_replace_locked_source_and_policy_drift_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _, _, prose, heading, lemma = self.fixture(Path(tmp))
            path = harvest / 'test.tex'; raw = path.read_bytes(); path.write_bytes(raw + b'% dirty\n')
            with self.assertRaisesRegex(RecordError, 'locked Git chapter bytes'):
                _order_unit_batches_by_chapter_source([[heading], [prose], [lemma]], harvest, root=root)
            path.write_bytes(raw)
            original = Containers.assert_unchanged
            def drift(instance):
                policy = root / 'config/macro-policy.yml'
                policy.write_bytes(policy.read_bytes() + b'\n# drift\n')
                original(instance)
            with patch.object(Containers, 'assert_unchanged', drift):
                with self.assertRaisesRegex(RecordError, 'macro policy changed'):
                    complete_prose_positions([[heading], [prose], [lemma]], {1}, root,
                        harvest, 'test', raw)

    def test_invalid_placement_writes_no_output_and_preserves_previous_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, sha, _, _, prose, _, _ = self.fixture(Path(tmp))
            prose['source_text'] = prose['source_text'].strip()
            prose = stamp_unit_hashes(prose)
            up, cp, output = root / 'units.jsonl', root / 'candidates.jsonl', root / 'preview'
            candidate = make_batch_candidate(prose)
            candidate.update(source_commit=sha, translation=prose['source_text'],
                allowed_english=sorted(set(ASCII_WORD_RE.findall(PLACEHOLDER_TOKEN_RE.sub('',
                    term_display_text(prose['source_text'], prose['placeholders']))))))
            write_jsonl(up, [prose]); write_jsonl(cp, [candidate])
            output.mkdir(); previous = output / 'previous.tex'; previous.write_text('previous preview')
            with self.assertRaisesRegex(RecordError, 'complete canonical'):
                render_batch(up, cp, root / 'upstream.lock', output, 'test', 'Synthetic fixture',
                             chapter_source_dir=harvest)
            self.assertEqual(list(output.iterdir()), [previous])
            self.assertEqual(previous.read_text(), 'previous preview')

    def test_file_drift_after_placement_is_rejected_before_preview_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, sha, _, _, prose, _, _ = self.fixture(Path(tmp))
            up, cp, output = root / 'units.jsonl', root / 'candidates.jsonl', root / 'preview'
            candidate = make_batch_candidate(prose)
            candidate.update(source_commit=sha, translation=prose['source_text'],
                allowed_english=sorted(set(ASCII_WORD_RE.findall(PLACEHOLDER_TOKEN_RE.sub('',
                    term_display_text(prose['source_text'], prose['placeholders']))))))
            write_jsonl(up, [prose]); write_jsonl(cp, [candidate])
            original = _order_unit_batches_by_chapter_source
            def drift(*args, **kwargs):
                result = original(*args, **kwargs)
                cp.write_bytes(cp.read_bytes() + b'\n')
                return result
            with patch('stacks_zh.workflow._order_unit_batches_by_chapter_source', drift):
                with self.assertRaisesRegex(RecordError, 'files changed during validation'):
                    render_batch(up, cp, root / 'upstream.lock', output, 'test', 'Synthetic fixture',
                                 chapter_source_dir=harvest)
            self.assertFalse(output.exists())

    def test_public_renderer_installs_complete_prose_in_source_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, sha, _, _, prose, heading, lemma = self.fixture(Path(tmp))
            units, candidates = [], []
            for index, unit in enumerate([lemma, prose, heading]):
                up, cp = root / f'units-{index}.jsonl', root / f'candidates-{index}.jsonl'
                candidate = make_batch_candidate(unit)
                candidate.update(source_commit=sha, translation=unit['source_text'],
                    allowed_english=sorted(set(ASCII_WORD_RE.findall(PLACEHOLDER_TOKEN_RE.sub('',
                        term_display_text(unit['source_text'], unit['placeholders']))))))
                write_jsonl(up, [unit]); write_jsonl(cp, [candidate])
                units.append(up); candidates.append(cp)
            output = root / 'preview'
            render_batch(units, candidates, root / 'upstream.lock', output, 'test',
                'Synthetic fixture', chapter_source_dir=harvest, tags_path=harvest / 'tags/tags')
            text = (output / 'chapters/test.tex').read_text()
            self.assertLess(text.index('Basics'), text.index('First paragraph'))
            self.assertLess(text.index('Last paragraph'), text.index('A claim'))
            self.assertEqual(text.count('Complete note'), 1)
            self.assertEqual(text.count('One condition'), 1)


if __name__ == '__main__':
    unittest.main()
