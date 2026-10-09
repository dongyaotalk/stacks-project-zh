"""Independent complete synthetic batches; no actual model output or adoption."""
from __future__ import annotations

import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stacks_zh import source_containers as module
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import RecordError, sha256_value, stamp_unit_hashes
from stacks_zh.source_reextractions import source_tex
from test_group_derivations import fixture, commit, write, save, run_for
from test_source_containers import NAMED, PROOF, selector, old_unit, git, fixture as english_fixture


def batches(base):
    root, harvest, _ = fixture(base, count=0)
    original = root / 'translation-data/units/test-0000.jsonl'
    candidate = root / 'translation-data/candidates/fixture/test-0000.jsonl'
    units = [json.loads(line) for line in original.read_text().splitlines()]
    candidates = [json.loads(line) for line in candidate.read_text().splitlines()]
    original.unlink()
    candidate.unlink()
    plans = []
    for name, rows, outputs in [('heading', units[:1], candidates[:1]),
                                ('body', units[1:], candidates[1:])]:
        slug = 'a-heading' if name == 'heading' else 'b-body'
        up = f'translation-data/units/test-{slug}.jsonl'
        cp = f'translation-data/candidates/fixture/test-{slug}.jsonl'
        save(root, up, rows)
        save(root, cp, outputs)
        groups = []
        declarations = [(name, rows, None)] if name == 'heading' else [
            ('statement', rows[:1], selector('lemma')), ('proof', rows[1:], selector())]
        for gid, inputs, coordinate in declarations:
            ids = [u['unit_id'] for u in inputs]
            groups.append({'group_id': gid, 'input_unit_ids': ids, 'identity_anchor': ids[0],
                           'selector': coordinate, 'layout': 'whole',
                           'reason': 'Complete independent synthetic batch; never adopted.'})
        plan = root / f'build/{name}.json'
        write(plan, {'derivation_id': 'many-fixture-' + name, 'created_at': '2026-10-09T00:00:00Z',
                     'units_file': up, 'candidates_file': cp, 'groups': groups})
        plans.append(plan)
    commit(root)
    return root, harvest, plans, root / 'build/many-package'


def files(path):
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob('*') if p.is_file()}


def cross_chapter_batches(base):
    from test_derivations import fixture as candidate_fixture
    root, harvest, _ = english_fixture(base)
    tags = harvest / 'tags/tags'
    tags.write_text(tags.read_text() + '0003,other-section-other\n')
    (harvest / 'other.tex').write_text('\\begin{document}\n\\section{Other}\n\\label{section-other}\n\\end{document}\n')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid', 'add', '.')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'two real chapters')
    source = git(harvest, 'rev-parse', 'HEAD')
    (root / 'upstream.lock').write_text(f'commit = "{source}"\n')
    template = candidate_fixture()[2][0]
    plans = []
    for chapter, tag, text, label in [('test', '0000', 'Basics', 'section-basic'),
                                      ('other', '0003', 'Other', 'section-other')]:
        unit = old_unit(source, f'tag:{tag}:title', 'section_title', text, '\\section{', '}\n\\label{' + label + '}')
        unit = stamp_unit_hashes({**unit, 'chapter': chapter, 'parent_tag': tag})
        context = {'unit_id': unit['unit_id'], 'source_commit': source,
                   'prompt_version': 'fixture', 'policy_revision': 'fixture'}
        candidate = copy.deepcopy(template)
        candidate.update(unit_id=unit['unit_id'], source_commit=source, source_text_hash=unit['source_text_hash'],
                         run_id='fixture-cross-' + chapter, context=context, context_hash=sha256_value(context),
                         notes=['Synthetic cross-chapter rejection fixture, never actual model output.'])
        up = f'translation-data/units/{chapter}-{tag}.jsonl'
        cp = f'translation-data/candidates/fixture/{chapter}-{tag}.jsonl'
        save(root, up, [unit]); save(root, cp, [candidate])
        write(root / f"translation-data/runs/{candidate['run_id']}.json",
              run_for([candidate], source, 'translation', candidate['run_id']))
        plan = root / f'build/{chapter}.json'
        write(plan, {'derivation_id': 'cross-' + chapter, 'created_at': '2026-10-09T00:00:00Z',
                     'units_file': up, 'candidates_file': cp, 'groups': [
                         {'group_id': 'heading', 'input_unit_ids': [unit['unit_id']],
                          'identity_anchor': unit['unit_id'], 'selector': None, 'layout': 'whole',
                          'reason': 'One complete real chapter heading, synthetic rejection fixture.'}]})
        plans.append(plan)
    git(root, 'init', '-q'); commit(root)
    return root, harvest, plans, root / 'build/cross-rejected'


def overlapping_batches(base, *, duplicate_output=False):
    from test_derivations import fixture as candidate_fixture
    root, harvest, _ = english_fixture(base)
    (harvest / 'test.tex').write_text('\\begin{document}\n\\section{Basics}\n\\label{section-basic}\n\n'
                                    'First complete paragraph.\n\nSecond complete paragraph.\n\n\\end{document}\n')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid', 'add', '.')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'complete prose interval')
    source = git(harvest, 'rev-parse', 'HEAD')
    (root / 'upstream.lock').write_text(f'commit = "{source}"\n')
    template = candidate_fixture()[2][0]; plans = []
    for name in ['a', 'b']:
        rows = [old_unit(source, 'tag:0000:heading-' + name, 'section_title', 'Basics',
                         '\\section{', '}\n\\label{section-basic}'),
                old_unit(source, 'tag:0000:old-first-' + name, 'paragraph', 'First complete paragraph.', '', '\n\n')]
        if name == 'a':
            rows.append(old_unit(source, 'tag:0000:old-second-a', 'paragraph', 'Second complete paragraph.', '', '\n\n'))
        candidates = []
        for unit in rows:
            context = {'unit_id': unit['unit_id'], 'source_commit': source,
                       'prompt_version': 'fixture', 'policy_revision': 'fixture'}
            candidate = copy.deepcopy(template)
            candidate.update(unit_id=unit['unit_id'], source_commit=source, source_text_hash=unit['source_text_hash'],
                             run_id='fixture-overlap-' + name, context=context, context_hash=sha256_value(context),
                             notes=['Synthetic overlapping legacy batches, never actual model output.'])
            candidates.append(candidate)
        up = 'translation-data/units/test-' + name + '.jsonl'
        cp = 'translation-data/candidates/fixture/test-' + name + '.jsonl'
        save(root, up, rows); save(root, cp, candidates)
        write(root / f"translation-data/runs/{candidates[0]['run_id']}.json",
              run_for(candidates, source, 'translation', candidates[0]['run_id']))
        declarations = [('heading', rows[:1], None)]
        if name == 'a' and not duplicate_output:
            declarations.append(('body', rows[1:], selector('prose_block', owner='0000')))
        else:
            declarations.append(('first', rows[1:2], selector('paragraph', owner='0000')))
            if name == 'a':
                declarations.append(('second', rows[2:], None))
        groups = [{'group_id': gid, 'input_unit_ids': [u['unit_id'] for u in inputs],
                   'identity_anchor': inputs[0]['unit_id'], 'selector': coordinate, 'layout': 'whole',
                   'reason': 'Independent complete synthetic source interval.'}
                  for gid, inputs, coordinate in declarations]
        plan = root / f'build/overlap-{name}.json'
        write(plan, {'derivation_id': 'overlap-' + name, 'created_at': '2026-10-09T00:00:00Z',
                     'units_file': up, 'candidates_file': cp, 'groups': groups})
        plans.append(plan)
    git(root, 'init', '-q'); commit(root)
    return root, harvest, plans, root / 'build/overlap-rejected'


class ManyContainerTests(unittest.TestCase):
    def test_single_packages_have_independent_complete_git_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plans, _ = batches(Path(tmp))
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            output = root / 'build/body-single'
            report = module.write_container_package(root, harvest, plans[1], output)
            self.assertEqual((report['state'], report['input_unit_count'], report['proposed_output_unit_count']),
                             ('PREPARED', 3, 2))
            rows = [json.loads(line) for line in (output / 'units.jsonl').read_text().splitlines()]
            self.assertEqual([source_tex(u) for u in rows], [NAMED, PROOF])

    def test_one_real_validation_per_call_byte_equivalence_and_readonly_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plans, output = batches(Path(tmp))
            before = files(root / 'translation-data')
            expected = {}
            for plan in plans:
                identifier = json.loads(plan.read_text())['derivation_id']
                single = root / 'build' / ('single-' + identifier)
                module.write_container_package(root, harvest, plan, single)
                expected[identifier] = files(single)
            with patch('stacks_zh.provenance.validate_repository_provenance',
                       wraps=validate_repository_provenance) as validate:
                report = module.write_container_packages(root, harvest, plans, output)
                self.assertEqual(validate.call_count, 1)
            self.assertEqual((report['state'], report['package_count'], report['input_unit_count'],
                              report['proposed_output_unit_count']), ('PREPARED', 2, 4, 3))
            for identifier, contents in expected.items():
                self.assertEqual(files(output / identifier), contents)
            stamps = {p: p.stat().st_mtime_ns for p in [output, *output.rglob('*')]}
            with patch('stacks_zh.provenance.validate_repository_provenance',
                       wraps=validate_repository_provenance) as validate:
                self.assertEqual(module.write_container_packages(root, harvest, plans, output, check=True), report)
                self.assertEqual(validate.call_count, 1)
            self.assertEqual(stamps, {p: p.stat().st_mtime_ns for p in stamps})
            self.assertEqual(files(root / 'translation-data'), before)

    def test_blocked_group_and_full_inputs_remain_in_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plans, output = batches(Path(tmp))
            data = json.loads(plans[1].read_text())
            data['groups'][-1]['selector']['ordinal'] = 99
            write(plans[1], data)
            report = module.write_container_packages(root, harvest, plans, output)
            self.assertEqual((report['state'], report['blocked_group_count'], report['input_unit_count']),
                             ('BLOCKED', 1, 4))
            self.assertEqual((output / data['derivation_id'] / 'input-units.jsonl').read_bytes(),
                             (root / data['units_file']).read_bytes())
            self.assertIn('BLOCKED', (output / 'report.md').read_text())
            from stacks_zh.cli import main
            args = ['prepare-source-containers-many', '--root', str(root), '--harvest', str(harvest),
                    '--output', str(output), '--require-prepared', '--check']
            for plan in plans:
                args += ['--plan', str(plan)]
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                self.assertEqual(main(args), 1)
            self.assertIn('1 blocked; state=BLOCKED. Adopted: false.', captured.getvalue())

    def test_duplicate_plans_batch_targets_derivation_ids_and_unknown_fields_refused(self):
        for change in ['same-plan', 'same-batch', 'same-id', 'skip-validation', 'reserved-id']:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root, harvest, plans, output = batches(Path(tmp))
                if change == 'same-plan':
                    plans[1] = plans[0]
                else:
                    data = json.loads(plans[1].read_text())
                    first = json.loads(plans[0].read_text())
                    if change == 'same-batch':
                        data.update(units_file=first['units_file'], candidates_file=first['candidates_file'])
                    elif change == 'same-id':
                        data['derivation_id'] = first['derivation_id']
                    elif change == 'reserved-id':
                        data['derivation_id'] = 'manifest.json'
                    else:
                        data['provenance_verified'] = True
                    write(plans[1], data)
                with self.assertRaises(RecordError):
                    module.write_container_packages(root, harvest, plans, output)
                self.assertFalse(output.exists())

    def test_two_valid_real_chapters_cannot_share_a_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plans, output = cross_chapter_batches(Path(tmp))
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            for n, plan in enumerate(plans):
                self.assertEqual(module.write_container_package(root, harvest, plan, root / f'build/single-{n}')['state'],
                                 'PREPARED')
            with self.assertRaisesRegex(RecordError, 'one chapter'):
                module.write_container_packages(root, harvest, plans, output)
            self.assertFalse(output.exists())

    def test_individually_valid_batches_cannot_repeat_source_spans_or_output_ids(self):
        for duplicate_output in [False, True]:
            with self.subTest(duplicate_output=duplicate_output), tempfile.TemporaryDirectory() as tmp:
                root, harvest, plans, output = overlapping_batches(Path(tmp), duplicate_output=duplicate_output)
                self.assertEqual(validate_repository_provenance(root, harvest), [])
                for n, plan in enumerate(plans):
                    report = module.write_container_package(root, harvest, plan, root / f'build/alone-{n}')
                    self.assertEqual(report['state'], 'PREPARED')
                with self.assertRaisesRegex(RecordError, 'overlapping old/new' if duplicate_output else 'overlaps locked source'):
                    module.write_container_packages(root, harvest, plans, output)
                self.assertFalse(output.exists())

    def test_output_parent_changed_to_symlink_cannot_write_outside(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plans, _ = batches(Path(tmp))
            parent = root / 'build/isolated'; parent.mkdir()
            outside = Path(tmp) / 'outside'; outside.mkdir(); (outside / 'keep').write_text('Unrelated')
            original = module.Containers.select; changed = [False]
            def swap(obj, coordinate):
                selected = original(obj, coordinate)
                if not changed[0]:
                    changed[0] = True; parent.rename(root / 'build/previous-parent')
                    parent.symlink_to(outside, target_is_directory=True)
                return selected
            with patch.object(module.Containers, 'select', swap), self.assertRaises(RecordError):
                module.write_container_packages(root, harvest, plans, parent / 'package')
            self.assertEqual(files(outside), {'keep': b'Unrelated'})

    def test_partial_batch_and_dirty_or_invalid_history_never_reuses_validation(self):
        for change in ['partial-plan', 'dirty-batch', 'invalid-history']:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root, harvest, plans, output = batches(Path(tmp))
                if change == 'partial-plan':
                    data = json.loads(plans[1].read_text()); data['groups'].pop(); write(plans[1], data)
                elif change == 'dirty-batch':
                    p = root / json.loads(plans[1].read_text())['units_file']; p.write_bytes(p.read_bytes() + b'\n')
                else:
                    p = next((root / 'translation-data/runs').glob('*.json'))
                    data = json.loads(p.read_text()); data['unit_ids'] = []; write(p, data)
                with self.assertRaises(RecordError):
                    module.write_container_packages(root, harvest, plans, output)
                self.assertFalse(output.exists())

    def test_mutation_during_shared_preparation_keeps_entire_previous_package(self):
        for change in ['policy', 'facts', 'plan', 'head', 'tracked-input', 'review-input', 'lock', 'output']:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root, harvest, plans, output = batches(Path(tmp))
                tracked = root / 'style.md'; tracked.write_text('Synthetic input'); commit(root)
                module.write_container_packages(root, harvest, plans, output)
                before = files(output)
                original = module.Containers.select
                changed = [False]
                def mutate(obj, coordinate):
                    result = original(obj, coordinate)
                    if not changed[0]:
                        changed[0] = True
                        if change == 'policy':
                            p = root / 'config/macro-policy.yml'; p.write_bytes(p.read_bytes() + b'\n# changed\n')
                        elif change == 'facts':
                            p = root / json.loads(plans[0].read_text())['units_file']; p.write_bytes(p.read_bytes() + b'\n')
                        elif change == 'plan':
                            plans[0].write_bytes(plans[0].read_bytes() + b'\n')
                        elif change == 'head':
                            tracked.write_text('New synthetic input'); commit(root)
                        elif change == 'tracked-input':
                            tracked.write_text('Changed during preparation')
                        elif change == 'review-input':
                            p = root / 'review/new.jsonl'; p.parent.mkdir(exist_ok=True)
                            p.write_text('{"synthetic": "Concurrent input, never approval"}\n')
                        elif change == 'lock':
                            p = root / 'upstream.lock'; p.write_bytes(p.read_bytes() + b'\n')
                        else:
                            (output / 'foreign.txt').write_text('Concurrent file, keep it')
                    return result
                with patch.object(module.Containers, 'select', mutate), self.assertRaises(RecordError):
                    module.write_container_packages(root, harvest, plans, output)
                actual = files(output)
                if change == 'output':
                    self.assertEqual(actual.pop('foreign.txt'), b'Concurrent file, keep it')
                self.assertEqual(actual, before)

    def test_tampered_extra_files_symlinks_and_unsafe_output_refused(self):
        for change in ['tamper', 'extra', 'nested-link', 'parent-link', 'plan-link', 'outside']:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root, harvest, plans, output = batches(Path(tmp))
                module.write_container_packages(root, harvest, plans, output)
                if change == 'tamper':
                    (output / 'many-fixture-body/units.jsonl').write_text('tamper')
                elif change == 'extra':
                    (output / 'many-fixture-body/foreign.txt').write_text('keep')
                elif change == 'nested-link':
                    p = output / 'many-fixture-body/units.jsonl'; p.unlink(); p.symlink_to(plans[0])
                elif change == 'parent-link':
                    link = root / 'build/alias'; link.symlink_to(output, target_is_directory=True); output = link / 'child'
                elif change == 'plan-link':
                    link = root / 'build/alias.json'; link.symlink_to(plans[0]); plans[0] = link
                else:
                    output = root / 'translation-data/forbidden'
                with self.assertRaises(RecordError):
                    module.write_container_packages(root, harvest, plans, output, check=True)

    def test_atomic_install_failure_rolls_back_all_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, plans, output = batches(Path(tmp))
            module.write_container_packages(root, harvest, plans, output)
            before = files(output); original = Path.rename
            def fail(path, target):
                if path.name.startswith('.containers-many-stage-') and Path(target).resolve() == output.resolve():
                    raise OSError('Synthetic aggregate install failure')
                return original(path, target)
            with patch.object(Path, 'rename', fail), self.assertRaisesRegex(OSError, 'aggregate install failure'):
                module.write_container_packages(root, harvest, plans, output)
            self.assertEqual(files(output), before)
            self.assertEqual(list(output.parent.glob('.containers-many-*')), [])


if __name__ == '__main__':
    unittest.main()
