"""Independent synthetic English; none of these records claim model authorship."""
from __future__ import annotations

import copy
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from stacks_zh.extraction import Policy
from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.source_containers import Containers, lower_container, old_container_groups, verify_old_group, write_container_package
from stacks_zh.source_integrity import environment_title_errors, permanent_tag_mapping
from stacks_zh.source_reextractions import source_tex

ROOT = Path(__file__).resolve().parent.parent
NAMED = ('\\begin{lemma}[A $k$-linear {\\it category}]\n\\label{lemma-one}\n'
         'Let $x$ be an object.\\footnote{First paragraph with $x$.\n\n'
         'Second paragraph with $x \\to y$.} Then:\n\\begin{enumerate}\n'
         '\\item Choose $x$.\n\\item Choose $y$.\n\\end{enumerate}\n'
         'This sentence is outside the list.\n\\end{lemma}')
PROOF = ('\\begin{proof}\nTake $x$.\n\n% Keep this comment.\n'
         '\\[x \\to y \\to z\\]\n\nUse {\\bf a category}.\n'
         '\\begin{enumerate}\n\\item First step.\n\\item Second step.\n'
         '\\end{enumerate}\nThus the claim follows.\n\\end{proof}')
SECOND_PROOF = '\\begin{proof}[Another argument]\nChoose $y$.\n\\end{proof}'


def git(path, *args):
    return subprocess.run(['git', '-C', str(path), *args], check=True, capture_output=True, text=True).stdout.strip()


def fixture(base, *, statement=NAMED, proof=PROOF, other=''):
    root, harvest = base / 'chinese', base / 'english'
    (root / 'config').mkdir(parents=True)
    harvest.mkdir()
    policy = (ROOT / 'config/macro-policy.yml').read_bytes()
    (root / 'config/macro-policy.yml').write_bytes(policy)
    (harvest / 'tags').mkdir()
    (harvest / 'tags/tags').write_text('0000,test-section-basic\n0001,test-lemma-one\n0002,test-lemma-two\n')
    text = ('\\begin{document}\n\\section{Basics}\n\\label{section-basic}\n' + statement +
            '\n' + proof + '\n' + SECOND_PROOF + '\n' + other + '\n\\end{document}\n')
    (harvest / 'test.tex').write_text(text)
    git(harvest, 'init', '-q')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid', 'add', '.')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'synthetic English')
    sha = git(harvest, 'rev-parse', 'HEAD')
    (root / 'upstream.lock').write_text(f'commit = "{sha}"\n')
    return root, harvest, sha


def selector(kind='proof', ordinal=1, owner='0001'):
    label = {'0000':'test-section-basic', '0001':'test-lemma-one', '0002':'test-lemma-two'}[owner]
    return {'file': 'test.tex', 'owner_tag': owner, 'owner_label': label, 'parent_tag': '0000', 'kind': kind, 'ordinal': ordinal}


def old_unit(sha, identifier, kind, text, prefix='', suffix=''):
    return stamp_unit_hashes({'schema_version': 1, 'unit_id': identifier, 'parent_tag': '0000',
        'chapter': 'test', 'node_kind': kind, 'risk_level': 'R3', 'source_commit': sha,
        'source_status': 'CURRENT', 'source_text': text, 'placeholders': {},
        'render': {'prefix': prefix, 'suffix': suffix}})


class SourceContainerTests(unittest.TestCase):
    def test_chapter_title_owns_complete_real_header_and_native_label(self):
        header = '\\title{Test categories}\n\n\\maketitle\n\\phantomsection\n\\label{section-phantom}\n\n\\tableofcontents\n\n'
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = fixture(Path(tmp))
            path = harvest / 'test.tex'
            path.write_text(path.read_text().replace('\\begin{document}\n', '\\begin{document}\n' + header))
            tags = harvest / 'tags/tags'
            tags.write_text(tags.read_text() + '0003,test-section-phantom\n')
            git(harvest, 'add', 'test.tex', 'tags/tags')
            git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'synthetic header')
            (root / 'upstream.lock').write_text('commit = "' + git(harvest, 'rev-parse', 'HEAD') + '"\n')
            containers = Containers(root, harvest)
            coordinate = {'file':'test.tex', 'owner_tag':'0003', 'owner_label':'test-section-phantom',
                          'parent_tag':'0003', 'kind':'title_title', 'ordinal':1}
            selected = containers.select(coordinate)
            self.assertEqual(selected['fragment'], header)
            rows = lower_container(selected, containers.policy)
            self.assertEqual(source_tex(rows[0]), header)
            self.assertEqual(rows[0]['node_kind'], 'chapter_title')
            self.assertEqual(permanent_tag_mapping(rows, containers.english.tags), {'tag:0003:title':'tag:0003:title'})
            # A label in a comment cannot supply the actual chapter boundary.
            path.write_text(path.read_text().replace('\\label{section-phantom}', '% \\label{section-phantom}'))
            git(harvest, 'add', 'test.tex')
            git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'synthetic missing label')
            (root / 'upstream.lock').write_text('commit = "' + git(harvest, 'rev-parse', 'HEAD') + '"\n')
            with self.assertRaisesRegex(RecordError, 'unique real phantom label'):
                Containers(root, harvest).select(coordinate)

    def test_book_projection_qualifies_real_commands_and_keeps_opaque_bytes(self):
        from stacks_zh.workflow import _project_container_tex
        policy = Policy((ROOT / 'config/macro-policy.yml').read_text())
        tags = {'test-lemma-one':'0001', 'other-lemma-one':'0002', 'test-section-phantom':'0003'}
        opaque = ('% \\label{fake} \\ref{fake}\n'
                  '\\verb|\\label{fake} \\ref{fake}|\n'
                  '\\begin{verbatim}\\ref{fake}\\label{fake}\\end{verbatim}\n'
                  '\\url{https://example.invalid/\\ref{fake}}\\cite{key-ref}\n')
        text = (opaque + '\\label{lemma-one}\\label{eq-one}$\\eqref{eq-one}$\n'
                '\\footnote{See \\ref{lemma-one} and \\pageref{other-lemma-one}.}\n'
                '\\href{https://example.invalid/\\ref{fake}}{See \\ref{lemma-one}.}')
        before = text
        _, labels = _project_container_tex(text, 'test', policy, tags)
        self.assertEqual(labels, {'test-lemma-one', 'test-eq-one'})
        projected, _ = _project_container_tex(text, 'test', policy, tags, labels)
        self.assertTrue(projected.startswith(opaque))
        self.assertIn('$\\eqref{test-eq-one}$', projected)
        self.assertIn('See \\ref{test-lemma-one}', projected)
        self.assertIn('https://stacks.math.columbia.edu/tag/0002', projected)
        self.assertIn('https://example.invalid/\\ref{fake}', projected)
        self.assertEqual(text, before)
        header = '\\title{测试（Test）}\n\\maketitle\n\\phantomsection\n\\label{section-phantom}\n\\tableofcontents\n'
        book, _ = _project_container_tex(header, 'test', policy, tags, {'test-section-phantom'}, chapter_title=True)
        self.assertEqual(book, '\\chapter{测试（Test）}\n\n\n\\label{test-section-phantom}\n\n')

    def test_independent_full_display_list_comment_and_footnote_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = fixture(Path(tmp))
            containers = Containers(root, harvest)
            for coordinate, expected in [(selector('lemma'), NAMED), (selector(), PROOF),
                                         (selector(ordinal=2), SECOND_PROOF)]:
                selected = containers.select(coordinate)
                self.assertEqual(selected['fragment'], expected)
                rows = lower_container(selected, containers.policy)
                self.assertEqual(''.join(source_tex(row) for row in rows), expected)
                self.assertEqual(rows[0]['risk_level'], 'R3')
                self.assertEqual(rows[0]['parent_tag'], '0000')
            named = lower_container(containers.select(selector('lemma')), containers.policy)[0]
            self.assertIn('Second paragraph', named['source_text'])
            self.assertIn('A <MATH_0001>-linear', named['source_text'])
            self.assertIn('category', named['source_text'])
            self.assertEqual(environment_title_errors(named), [])
            self.assertEqual(named['unit_id'], 'tag:0001:statement')
            containers.assert_unchanged()

    def test_semantic_one_to_two_title_and_body_with_native_ownership(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = fixture(Path(tmp))
            containers = Containers(root, harvest)
            selected = containers.select(selector('lemma'))
            rows = lower_container(selected, containers.policy, layout='split-title')
            self.assertEqual([row['node_kind'] for row in rows], ['environment_title', 'lemma'])
            self.assertEqual(''.join(source_tex(row) for row in rows), NAMED)
            self.assertEqual(environment_title_errors(rows[0]), [])
            self.assertEqual(permanent_tag_mapping(rows, containers.english.tags),
                             {row['unit_id']: row['unit_id'] for row in rows})
            proof = lower_container(containers.select(selector()), containers.policy)
            self.assertEqual(len(old_container_groups(rows + proof, containers.english.tags)), 2)
            self.assertEqual(permanent_tag_mapping(rows + proof, containers.english.tags),
                             {row['unit_id']: row['unit_id'] for row in rows + proof})

    def test_complete_prose_block_restores_lists_and_long_footnote_with_real_anchors(self):
        prose = ('\n\nAn introduction.\n\nLet $x$ be given.\n'
                 '\\begin{enumerate}\n\\item Choose $x$.\n\\end{enumerate}\n'
                 'They are isomorphisms\\footnote{First paragraph.\n\n'
                 'The full second paragraph with $x \\to y$.}\n\nThe final sentence.\n\n')
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, sha = fixture(Path(tmp), statement=prose + NAMED)
            containers = Containers(root, harvest)
            selected = containers.select(selector('prose_block', owner='0000'))
            self.assertEqual(selected['fragment'], '\n' + prose)
            self.assertEqual(selected['boundary_witness'], {
                'before': {'kind':'section_title', 'owner_tag':'0000', 'ordinal':1},
                'after': {'kind':'lemma', 'owner_tag':'0001', 'ordinal':1}})
            units = [old_unit(sha, 'tag:0000:title', 'section_title', 'Basics', '\\section{', '}\n\\label{section-basic}'),
                     old_unit(sha, 'tag:0000:p001', 'paragraph', 'Legacy paragraph.'),
                     old_unit(sha, 'tag:0000:p002', 'paragraph', 'Legacy list and footnote summary.'),
                     old_unit(sha, 'tag:0001:statement', 'lemma', 'An old statement.',
                              '\\begin{lemma}\n\\label{test-lemma-one}\n', '\n\\end{lemma}')]
            verify_old_group(units, containers.english.tags, [u['unit_id'] for u in units[1:3]], selected)
            new = lower_container(selected, containers.policy)
            self.assertEqual(len(new), 1)
            self.assertEqual(source_tex(new[0]), '\n' + prose)
            self.assertIn('The full second paragraph', new[0]['source_text'])
            self.assertIn('The final sentence', new[0]['source_text'])
            self.assertEqual(new[0]['unit_id'], 'tag:0000:prose-0001')
            self.assertEqual(new[0]['node_kind'], 'paragraph')
            with self.assertRaisesRegex(RecordError, 'complete old wrapper'):
                verify_old_group(units, containers.english.tags, [units[2]['unit_id']], selected)

    def test_prose_block_cannot_borrow_another_statement_or_fake_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, sha = fixture(Path(tmp), statement='A real paragraph.\n\n' + NAMED)
            containers = Containers(root, harvest)
            selected = containers.select(selector('prose_block', owner='0000'))
            units = [old_unit(sha, 'tag:0000:title', 'section_title', 'Basics', '\\section{', '}\n\\label{section-basic}'),
                     old_unit(sha, 'tag:0000:p001', 'paragraph', 'Legacy prose.'),
                     old_unit(sha, 'tag:0002:statement', 'lemma', 'Another statement.',
                              '\\begin{lemma}\n\\label{test-lemma-two}\n', '\n\\end{lemma}')]
            with self.assertRaisesRegex(RecordError, 'different real preceding/following'):
                verify_old_group(units, containers.english.tags, [units[1]['unit_id']], selected)
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = fixture(Path(tmp), statement='A paragraph \\label{lemma-two}.\n\n' + NAMED)
            with self.assertRaisesRegex(RecordError, 'real labelled boundary'):
                Containers(root, harvest).select(selector('prose_block', owner='0000'))

    def test_complete_many_old_to_one_proof_and_partial_cross_owner_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, sha = fixture(Path(tmp))
            containers = Containers(root, harvest)
            units = [old_unit(sha, 'tag:OLD1:statement', 'lemma', 'An old statement.',
                              '\\begin{lemma}\n\\label{test-lemma-one}\n', '\n\\end{lemma}'),
                     old_unit(sha, 'tag:OLD1:proof-p001', 'proof', 'First legacy segment.', '\\begin{proof}\n'),
                     old_unit(sha, 'tag:OLD1:proof-p002', 'paragraph', 'Second legacy segment.', '', '\n\\end{proof}')]
            ids = [u['unit_id'] for u in units[1:]]
            selected = containers.select(selector())
            verify_old_group(units, containers.english.tags, ids, selected)
            rows = lower_container(selected, containers.policy)
            self.assertEqual(len(rows), 1)
            self.assertEqual(source_tex(rows[0]), PROOF)
            for rejected in [ids[:1], ids[::-1], [units[0]['unit_id'], *ids], ids + ids[:1]]:
                with self.assertRaisesRegex(RecordError, 'complete old wrapper chain'):
                    verify_old_group(units, containers.english.tags, rejected, selected)
            other = copy.deepcopy(selected)
            other['selector']['owner_tag'] = '0002'
            with self.assertRaisesRegex(RecordError, 'different owner'):
                verify_old_group(units, containers.english.tags, ids, other)

    def test_wrong_real_selector_fake_label_and_ambiguous_ordinal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = fixture(Path(tmp), other='A fake $\\label{lemma-two}$ in math.')
            containers = Containers(root, harvest)
            bad = [selector(owner='0002'), selector(ordinal=3), selector('definition'),
                   {**selector(), 'parent_tag': '0002'}, {**selector(), 'ordinal': True},
                   {**selector(), 'file': '../test.tex'}, {**selector(), 'byte_start': 0}]
            for coordinate in bad:
                with self.subTest(coordinate=coordinate), self.assertRaises(RecordError):
                    containers.select(coordinate)

    def test_repeated_real_own_label_is_ambiguous_despite_an_ordinal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = fixture(Path(tmp), other=NAMED)
            with self.assertRaisesRegex(RecordError, 'duplicate real labelled'):
                Containers(root, harvest).select(selector('lemma'))

    def test_unknown_syntax_and_unclassified_math_text_remain_blocked(self):
        for body in ['\\mystery{A category}', '\\begin{mystery}A category.\\end{mystery}',
                     '$\\text{a natural phrase}$', '$\\text{Hom}$']:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as tmp:
                proof = '\\begin{proof}\nTake ' + body + '.\n\\end{proof}'
                root, harvest, _ = fixture(Path(tmp), proof=proof)
                with self.assertRaisesRegex(RecordError, 'adoption blocked'):
                    Containers(root, harvest).select(selector())

    def test_dirty_harvest_inventory_not_authority_and_policy_change_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = fixture(Path(tmp))
            (harvest / 'test.tex').write_text('DIRTY FALSE SOURCE')
            containers = Containers(root, harvest)
            self.assertEqual(containers.select(selector())['fragment'], PROOF)
            policy = root / 'config/macro-policy.yml'
            policy.write_text(policy.read_text() + '\n# changed\n')
            with self.assertRaisesRegex(RecordError, 'policy changed'):
                containers.assert_unchanged()

    def test_no_arbitrary_split_or_empty_proof_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = fixture(Path(tmp))
            containers = Containers(root, harvest)
            selected = containers.select(selector())
            for layout in ['split-title', 'every-paragraph', 'legacy']:
                with self.assertRaises(RecordError):
                    lower_container(selected, containers.policy, layout=layout)
            corrupt = copy.deepcopy(selected)
            corrupt['fragment'] = corrupt['fragment'][:-len('\\end{proof}')]
            with self.assertRaisesRegex(RecordError, 'complete closing'):
                lower_container(corrupt, containers.policy)

    def test_utf8_span_is_bytes_and_exact_fragment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = fixture(Path(tmp), other='An exposé about categories.')
            containers = Containers(root, harvest)
            selected = containers.select(selector('paragraph', owner='0000'))
            raw = subprocess.run(['git', '-C', str(harvest), 'show', f'{containers.english.commit}:test.tex'],
                                 check=True, capture_output=True).stdout
            a, b = (selected['location'][k] for k in ('byte_start', 'byte_end'))
            self.assertEqual(raw[a:b].decode(), 'An exposé about categories.\n')
            self.assertEqual(source_tex(lower_container(selected, containers.policy)[0]), 'An exposé about categories.\n')


class ContainerPackageTests(unittest.TestCase):
    def test_parent_replaced_by_symlink_during_preparation_cannot_write_outside(self):
        import stacks_zh.source_containers as module
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plan, _ = self.prepared_fixture(Path(tmp))
            parent = root / 'build/isolated-parent'
            parent.mkdir()
            outside = Path(tmp) / 'outside'
            outside.mkdir()
            marker = outside / 'keep.txt'
            marker.write_text('Unrelated file')
            original = module.prepare_containers
            def replace_parent(*args):
                result = original(*args)
                parent.rename(root / 'build/previous-parent')
                parent.symlink_to(outside, target_is_directory=True)
                return result
            with patch.object(module, 'prepare_containers', side_effect=replace_parent):
                with self.assertRaisesRegex(RecordError, 'changed to a symlink'):
                    write_container_package(root, harvest, plan, parent / 'package')
            self.assertEqual({p.name for p in outside.iterdir()}, {'keep.txt'})
            self.assertEqual(marker.read_text(), 'Unrelated file')

    def prepared_fixture(self, base):
        from test_group_derivations import fixture, commit, write
        root, harvest, records = fixture(base)
        commit(root)
        record = records[-1]
        groups = []
        for group in record['unit_groups']:
            groups.append({'group_id': group['group_id'], 'input_unit_ids': group['output_unit_ids'],
                'identity_anchor': group['output_unit_ids'][0], 'reason': 'Synthetic complete package.',
                'layout': 'whole', 'selector': None if group['group_id'] == 'heading' else
                selector('lemma') if group['group_id'] == 'statement' else selector()})
        plan = {'derivation_id': 'fixture-prepared', 'created_at': '2026-10-06T08:00:00Z',
            'units_file': record['files']['output_units']['path'],
            'candidates_file': record['files']['output_candidates']['path'], 'groups':groups}
        plan_path = root / 'build/plan.json'
        write(plan_path, plan)
        output = root / 'build/complete-container-package'
        return root, harvest, plan_path, output

    def test_full_package_is_deterministic_check_readonly_and_does_not_adopt(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plan, output = self.prepared_fixture(Path(tmp))
            before = {p.relative_to(root):p.read_bytes() for p in (root / 'translation-data').rglob('*') if p.is_file()}
            report = write_container_package(root, harvest, plan, output)
            self.assertEqual(report['state'], 'PREPARED')
            self.assertEqual(report['input_unit_count'], 4)
            self.assertEqual(report['proposed_output_unit_count'], 3)
            stamp = {p:p.stat().st_mtime_ns for p in output.iterdir()}
            self.assertEqual(write_container_package(root, harvest, plan, output, check=True), report)
            self.assertEqual(stamp, {p:p.stat().st_mtime_ns for p in output.iterdir()})
            self.assertEqual(before, {p.relative_to(root):p.read_bytes() for p in (root / 'translation-data').rglob('*') if p.is_file()})
            self.assertEqual(json.loads((output / 'restorations.json').read_text())[0]['input_unit_ids'],
                             ['tag:0001:environment-title', 'tag:0001:statement'])

    def test_output_tamper_stale_check_symlink_and_foreign_file_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plan, output = self.prepared_fixture(Path(tmp))
            write_container_package(root, harvest, plan, output)
            (output / 'units.jsonl').write_text('tamper')
            with self.assertRaisesRegex(RecordError, 'stale'):
                write_container_package(root, harvest, plan, output, check=True)
            (output / 'personal-note.txt').write_text('do not discard')
            with self.assertRaisesRegex(RecordError, 'unrelated'):
                write_container_package(root, harvest, plan, output)
            (output / 'personal-note.txt').unlink()
            (output / 'units.jsonl').unlink()
            (output / 'units.jsonl').symlink_to(plan)
            with self.assertRaisesRegex(RecordError, 'unsafe'):
                write_container_package(root, harvest, plan, output)
            link = root / 'build/link'
            link.symlink_to(output, target_is_directory=True)
            with self.assertRaisesRegex(RecordError, 'symlink'):
                write_container_package(root, harvest, plan, link / 'child')

    def test_failed_atomic_replace_preserves_previous_whole_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plan, output = self.prepared_fixture(Path(tmp))
            write_container_package(root, harvest, plan, output)
            before = {p.name:p.read_bytes() for p in output.iterdir()}
            original = Path.rename
            def failed(path, target):
                if (path.name.startswith('.containers-') and not path.name.startswith('.containers-backup-')
                        and Path(target).resolve() == output.resolve()):
                    raise OSError('synthetic failed rename')
                return original(path, target)
            with patch.object(Path, 'rename', failed), self.assertRaisesRegex(OSError, 'synthetic failed'):
                write_container_package(root, harvest, plan, output)
            self.assertEqual(before, {p.name:p.read_bytes() for p in output.iterdir()})
            self.assertEqual(list(output.parent.glob('.containers-*')), [])

    def test_source_fact_concurrent_change_does_not_replace_old_package(self):
        import json
        from stacks_zh import source_containers
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plan, output = self.prepared_fixture(Path(tmp))
            write_container_package(root, harvest, plan, output)
            before = {p.name:p.read_bytes() for p in output.iterdir()}
            source = root / json.loads(plan.read_text())['units_file']
            original_bytes = source.read_bytes()
            original = source_containers.lower_container
            calls = [0]
            def changed(*args, **kwargs):
                rows = original(*args, **kwargs)
                calls[0] += 1
                if calls[0] > 2:  # After validating the two existing evidence records.
                    source.write_bytes(original_bytes + b'\n')
                return rows
            with patch.object(source_containers, 'lower_container', changed), self.assertRaisesRegex(RecordError, 'changed during'):
                write_container_package(root, harvest, plan, output)
            self.assertEqual(before, {p.name:p.read_bytes() for p in output.iterdir()})

    def test_plan_partial_inputs_or_outside_output_never_discards_fact_units(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plan, output = self.prepared_fixture(Path(tmp))
            data = json.loads(plan.read_text())
            data['groups'].pop()
            plan.write_text(json.dumps(data))
            with self.assertRaisesRegex(RecordError, 'partition every old'):
                write_container_package(root, harvest, plan, output)
            self.assertFalse(output.exists())
            with self.assertRaisesRegex(RecordError, 'ignored'):
                write_container_package(root, harvest, plan, root / 'translation-data/package')


if __name__ == '__main__':
    unittest.main()
