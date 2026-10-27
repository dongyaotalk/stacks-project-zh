"""Tiny independent Git/source histories exercise real validators, never real model authorship."""
import contextlib
import copy
from dataclasses import replace
import os
import io
import inspect
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_source_adoptions import synthetic_fixture, shared_run_fixture, provisional_fixture, english_fixture
from test_source_containers import git
from stacks_zh import repository_validation as sessions, source_adoptions, decisions, workflow
from stacks_zh.cli import main
from stacks_zh.records import RecordError

REPOSITORY = Path(__file__).resolve().parents[1]


def with_manifest(base, **kwargs):
    root, harvest, _ = english_fixture(base, **kwargs)
    (harvest / 'chapters.tex').write_text('\\item \\hyperref[test-section-phantom]{Synthetic}\n')
    git(harvest, 'add', '.')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'Synthetic manifest')
    source = git(harvest, 'rev-parse', 'HEAD')
    (root / 'upstream.lock').write_text(f'commit = "{source}"\n')
    return root, harvest, source


def prepare(base, *, typed=True):
    with patch('test_source_adoptions.english_fixture', side_effect=with_manifest):
        root, harvest, fp, rp, frozen, _ = synthetic_fixture(base, typed=typed)
    source_adoptions.assemble_source_adoption(root, fp, [rp], harvest)
    for name in ['Makefile', 'AGENTS.md', 'WORKFLOW.md', 'stacks_zh.py']:
        shutil.copyfile(REPOSITORY / name, root / name)
    units = [root / b['units_path'] for b in frozen['batches']]
    candidates = [root / b['candidates_path'] for b in frozen['batches']]
    return root, harvest, units, candidates, rp


class ValidationSessionTests(unittest.TestCase):
    def test_caller_subclasses_cannot_bypass_private_receipt_checks(self):
        class CallerProvenance(sessions._ProvenancePass):
            def assert_valid(self, *args, **kwargs):
                pass
        class CallerBatch(sessions._BatchPass):
            def assert_valid(self, *args, **kwargs):
                pass
        class CallerAdoptions(source_adoptions._ValidatedAdoptions):
            def __init__(self):
                dict.__init__(self)
            def assert_unchanged(self, *args, **kwargs):
                pass
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            with self.subTest(receipt='provenance'):
                with self.assertRaisesRegex(RecordError, 'actual live provenance'):
                    sessions._require_live_provenance(CallerProvenance(root, None, object()), root)
            with self.subTest(receipt='batch'):
                with self.assertRaisesRegex(RecordError, 'actual live batch'):
                    sessions._require_batch_validation(CallerBatch(None, None, (), 0, object()), root, None, [], [])
        with tempfile.TemporaryDirectory() as d:
            root, harvest, _ = with_manifest(Path(d))
            from stacks_zh.source_placement import complete_prose_positions
            with self.subTest(receipt='adoptions'):
                with self.assertRaisesRegex(RecordError, 'actual complete adoption replay'):
                    complete_prose_positions([[{'unit_id': 'synthetic'}]], {0}, root, harvest,
                        'test', (harvest/'test.tex').read_bytes(), _source_adoptions=CallerAdoptions())

    def test_independent_decisions_cannot_skip_history_with_a_caller_subclass(self):
        class CallerProvenance(sessions._ProvenancePass):
            def assert_valid(self, *args, **kwargs):
                pass
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            candidate = root/'translation-data/candidates/synthetic/batch.jsonl'
            candidate.parent.mkdir(parents=True)
            candidate.write_text(json.dumps(dict(unit_id='tag:ABCD:statement', run_id='synthetic',
                translation_hash='synthetic', model_correction_id='nonexistent'))+'\n')
            self.assertTrue(decisions.validate_repository_decisions(root))
            with self.assertRaisesRegex(RecordError, 'actual live provenance'):
                decisions.validate_repository_decisions(root,
                    _provenance=CallerProvenance(root, None, object()))

    def test_actual_read_boundary_rejects_new_unread_symlink_aliases(self):
        from stacks_zh.validation_io import InputReads, glob_paths
        for mode in ['tree', 'glob']:
            for kind in ['file', 'directory', 'dangling']:
                with self.subTest(mode=mode, kind=kind), tempfile.TemporaryDirectory() as d:
                    root = Path(d).resolve()
                    directory = root/'config'; directory.mkdir()
                    original = directory/'original.yml'; original.write_bytes(b'policy: original\n')
                    empty = directory/'empty'; empty.mkdir()
                    reads = InputReads()
                    with reads.activate():
                        if mode == 'tree':
                            reads.watch_root(root)
                        else:
                            list(glob_paths(directory, '*'))
                    reads.assert_unchanged()
                    target = {'file': original, 'directory': empty, 'dangling': directory/'missing'}[kind]
                    alias = directory/'unread-alias'
                    alias.symlink_to(target, target_is_directory=kind == 'directory')
                    with self.assertRaisesRegex(RecordError, 'symlink'):
                        reads.assert_unchanged()
                    self.assertEqual(original.read_bytes(), b'policy: original\n')
                    self.assertTrue(alias.is_symlink())
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            empty = root/'empty'; empty.mkdir()
            foreign = root/'foreign'; foreign.mkdir()
            reads = InputReads()
            with reads.activate():
                self.assertEqual(list(glob_paths(empty, '*')), [])
            empty.rmdir(); empty.symlink_to(foreign, target_is_directory=True)
            with self.assertRaisesRegex(RecordError, 'symlink'):
                reads.assert_unchanged()

    def test_independent_decisions_rejects_unread_alias_added_during_real_validation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root/'config').mkdir()
            original = root/'config/original.yml'; original.write_bytes(b'policy: original\n')
            self.assertEqual(decisions.validate_repository_decisions(root), [])
            actual = decisions._candidate_index
            def add_alias(*args):
                result = actual(*args)
                (root/'config/unread-alias.yml').symlink_to(original)
                return result
            with patch.object(decisions, '_candidate_index', side_effect=add_alias):
                with self.assertRaisesRegex(RecordError, 'symlink'):
                    decisions.validate_repository_decisions(root)
            self.assertEqual(original.read_bytes(), b'policy: original\n')

    def test_real_shared_qa_decision_typed_placement_render_once_and_independent_again(self):
        with tempfile.TemporaryDirectory() as d:
            root, harvest, units, candidates, _ = prepare(Path(d))
            with patch.object(sessions, '_validate_repository_provenance', wraps=sessions._validate_repository_provenance) as provenance, \
                 patch.object(source_adoptions, 'load_repository_source_adoptions', wraps=source_adoptions.load_repository_source_adoptions) as adoption, \
                 patch.object(decisions, 'validate_repository_decisions', wraps=decisions.validate_repository_decisions) as decision:
                result, errors = sessions.validate_batches_session(units, candidates, root/'upstream.lock', harvest)
                self.assertEqual(errors, [])
                self.assertEqual(result.count, 2)
                self.assertIs(decision.call_args.kwargs['_provenance'], result.provenance)
                workflow.render_batch(units, candidates, root/'upstream.lock', root/'shared', 'synthetic', 'Synthetic',
                    chapter_source_dir=harvest, tags_path=harvest/'tags/tags', _validation=result)
                self.assertEqual(provenance.call_count, 1)
                self.assertEqual(adoption.call_count, 1)
                workflow.render_batch(units, candidates, root/'upstream.lock', root/'independent', 'synthetic', 'Synthetic',
                    chapter_source_dir=harvest, tags_path=harvest/'tags/tags')
                self.assertEqual(provenance.call_count, 2)
                self.assertEqual(adoption.call_count, 2)
                workflow.render_batch(units, candidates, root/'upstream.lock',
                    root/'synthetic-chapter-test', 'synthetic', 'Synthetic',
                    chapter_manifest_path=harvest/'chapters.tex', chapter_source_dir=harvest,
                    tags_path=harvest/'tags/tags', chapter='test')
                self.assertEqual(provenance.call_count, 3)
                self.assertEqual(adoption.call_count, 3)
                self.assertIn('仅含 test 章', (root/'synthetic-chapter-test/metadata.tex').read_text())
            for path in (root/'shared').rglob('*.tex'):
                self.assertEqual(path.read_bytes(), (root/'independent'/path.relative_to(root/'shared')).read_bytes())
            self.assertIn(r'$x\quad\text{且}\quad y$', (root/'shared/chapters/test.tex').read_text())

    def test_out_of_inventory_candidates_cannot_borrow_repository_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,units,candidates,_=prepare(Path(d),typed=False)
            foreign_units=[];foreign_candidates=[]
            for up,cp in zip(units,candidates,strict=True):
                foreign_u=root/'build/foreign-units'/up.name
                foreign_c=root/'build/foreign-candidates'/cp.name
                foreign_u.parent.mkdir(parents=True,exist_ok=True)
                foreign_c.parent.mkdir(parents=True,exist_ok=True)
                foreign_u.write_bytes(up.read_bytes())
                rows=[json.loads(line) for line in cp.read_text().splitlines()]
                for row in rows:row['run_id']='forged-not-in-runs'
                foreign_c.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows))
                foreign_units.append(foreign_u);foreign_candidates.append(foreign_c)
            for ups,cps in [(foreign_units,foreign_candidates),(units,foreign_candidates)]:
                with self.assertRaisesRegex(RecordError,'active files covered'):
                    sessions.validate_batches_session(ups,cps,root/'upstream.lock',harvest)
                with self.assertRaisesRegex(RecordError,'active files covered'):
                    workflow.render_batch(ups,cps,root/'upstream.lock',root/'never',
                        'synthetic','Synthetic',chapter_source_dir=harvest,tags_path=harvest/'tags/tags')
            self.assertFalse((root/'never').exists())

    def test_real_proof_binds_raw_freeze_retired_policy_candidate_run_and_file_set(self):
        with tempfile.TemporaryDirectory() as d:
            root, harvest, units, candidates, raw = prepare(Path(d))
            implementation = root/'stacks_zh/synthetic.py'
            implementation.parent.mkdir(exist_ok=True); implementation.write_text('synthetic = True\n')
            extra = root/'docs/dynamic-frozen.jsonl'
            extra.write_text('{"synthetic": true}\n')
            actual = sessions._validate_repository_provenance
            def replay(*args):
                from stacks_zh.records import load_jsonl
                load_jsonl(extra)
                return actual(*args)
            with patch.object(sessions, '_validate_repository_provenance', side_effect=replay):
                proof, errors = sessions._complete_provenance(root, harvest)
            self.assertEqual(errors, [])
            self.assertIn(extra.resolve(), proof.snapshot.hashes)
            paths = [raw, extra, implementation, root/'prompts/translator-v2.md', root/'translation-data/source-adoption-inputs/synthetic-first.json',
                     root/'config/workflow.yml', candidates[0],
                     root/'translation-data/runs/run-synthetic-first.json']
            for path in paths:
                original = path.read_bytes()
                with self.subTest(path=path):
                    path.write_bytes(original+b' ')
                    with self.assertRaisesRegex(RecordError, 'changed'): proof.assert_valid(root, harvest)
                    path.write_bytes(original)
            for path in [root/'docs/evidence/new-raw.jsonl', root/'translation-data/retired/new-history.jsonl']:
                missing = [parent for parent in path.parents if not parent.exists()]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{}\n')
                with self.assertRaisesRegex(RecordError, 'paths changed'): proof.assert_valid(root, harvest)
                path.unlink()
                for parent in missing:
                    parent.rmdir()
            original = raw.read_bytes(); raw.unlink()
            with self.assertRaises(RecordError): proof.assert_valid(root, harvest)
            raw.write_bytes(original)
            added = harvest/'new-source.tex'; added.write_text('Synthetic addition.\n')
            with self.assertRaisesRegex(RecordError, 'paths changed'): proof.assert_valid(root, harvest)
            added.unlink()
            proof.assert_valid(root, harvest)
            git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                'commit', '--allow-empty', '-qm', 'Synthetic changed HEAD')
            with self.assertRaisesRegex(RecordError, 'HEAD changed'): proof.assert_valid(root, harvest)

    def test_real_source_and_receipt_mutation_and_fake_results_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root, harvest, units, candidates, _ = prepare(Path(d))
            proof, errors = sessions._complete_provenance(root, harvest)
            self.assertEqual(errors, [])
            proof.adoptions.assert_unchanged(root)  # Original one-argument interface.
            with self.assertRaisesRegex(RecordError, 'live repository'): proof.assert_valid(root.parent, harvest)
            with self.assertRaisesRegex(RecordError, 'source identity'): proof.assert_valid(root, root/'other-harvest')
            other=Path(d)/'other-english';shutil.copytree(harvest,other)
            with self.assertRaisesRegex(RecordError,'harvest identity'):
                workflow.render_batch(units,candidates,root/'upstream.lock',root/'never',
                    'synthetic','Synthetic',chapter_source_dir=other,harvest=harvest)
            from stacks_zh.source_placement import complete_prose_positions
            with self.assertRaisesRegex(RecordError,'source identity'):
                complete_prose_positions([[proof.adoptions[next(iter(proof.adoptions))]['unit']]],
                    {0},root,other,'test',(other/'test.tex').read_bytes(),_source_adoptions=proof.adoptions)
            for fake in [{}, {'status':'PASS'}, object()]:
                with self.assertRaises(RecordError): sessions._require_live_provenance(fake, root, harvest)
                with self.assertRaises(RecordError): workflow.render_batch(units, candidates, root/'upstream.lock',
                    root/'never', 'synthetic', 'Synthetic', _validation=fake)
            for fake in [replace(proof), copy.copy(proof)]:
                with self.assertRaises(RecordError): sessions._require_live_provenance(fake, root, harvest)
            fake_adoptions = copy.copy(proof.adoptions)
            with self.assertRaisesRegex(RecordError, 'not issued'): fake_adoptions.assert_unchanged(root, harvest)
            for field, value in [('snapshots', ()), ('binding', 'forged binding')]:
                previous = getattr(proof.adoptions, field); setattr(proof.adoptions, field, value)
                with self.assertRaisesRegex(RecordError, 'receipt changed'): proof.assert_valid(root, harvest)
                setattr(proof.adoptions, field, previous)
            for fake in [object.__new__(sessions._ImplementationIdentity), copy.copy(proof.implementation)]:
                with self.assertRaisesRegex(RecordError, 'not issued'): fake.assert_valid()
                with self.assertRaisesRegex(RecordError, 'not issued'):
                    sessions._complete_provenance(root, harvest, _implementation=fake)
            with self.assertRaisesRegex(RecordError, 'actual implementation'):
                sessions._complete_provenance(root, harvest, _implementation={})
            implementation_file = Path(sessions.__file__).resolve()
            actual_read = Path.read_bytes
            def changed_implementation(path):
                raw = actual_read(path)
                return raw+b'\n# synthetic changed implementation' if path == implementation_file else raw
            with patch.object(Path, 'read_bytes', changed_implementation):
                with self.assertRaisesRegex(RecordError, 'implementation input changed'):
                    proof.assert_valid(root, harvest)
                with self.assertRaisesRegex(RecordError, 'implementation input changed'):
                    proof.adoptions.assert_unchanged(root, harvest)
            actual_paths = Path.rglob
            def changed_implementation_paths(path, pattern):
                yield from actual_paths(path, pattern)
                if path == sessions._CODE_DIRECTORY and pattern == '*.py':
                    yield path/'nested/synthetic-new.py'
            with patch.object(Path, 'rglob', changed_implementation_paths):
                with self.assertRaisesRegex(RecordError, 'implementation paths changed'):
                    proof.assert_valid(root, harvest)
            watched = root/'config/workflow.yml'
            original_claim = proof.snapshot.hashes.pop(watched.resolve())
            with self.assertRaisesRegex(RecordError, 'claims changed'): proof.assert_valid(root, harvest)
            proof.snapshot.hashes[watched.resolve()] = original_claim
            key = next(iter(proof.adoptions))
            entry = proof.adoptions[key]
            # This metadata is used for provenance disclosure and typed projection.
            for target, field, value in [(entry, 'prior_candidates', [{}]),
                                         (entry['input'], 'created_at', 'altered freeze'),
                                         (entry['record'], 'created_at', 'altered record'),
                                         (vars(entry['policy']), 'raw', 'altered policy')]:
                previous = target[field]; target[field] = value
                with self.assertRaisesRegex(RecordError, 'receipt changed'): proof.assert_valid(root, harvest)
                target[field] = previous
            git(harvest, 'remote', 'add', 'origin', 'https://example.invalid/synthetic.git')
            with self.assertRaisesRegex(RecordError, 'repository identity'): proof.assert_valid(root, harvest)
            with self.assertRaisesRegex(RecordError, 'repository identity'): proof.adoptions.assert_unchanged(root, harvest)
            git(harvest, 'remote', 'remove', 'origin')
            source = harvest/'test.tex'; original=source.read_bytes();source.write_bytes(original+b'\n')
            with self.assertRaisesRegex(RecordError, 'changed'): proof.assert_valid(root, harvest)
            with self.assertRaisesRegex(RecordError, 'changed'): proof.adoptions.assert_unchanged(root, harvest)
            source.write_bytes(original)
            git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                'commit', '--allow-empty', '-qm', 'Synthetic changed source HEAD')
            with self.assertRaisesRegex(RecordError, 'HEAD changed'): proof.assert_valid(root, harvest)

    def test_ordered_scope_symlinks_and_missing_pairs_fail_before_generation(self):
        with tempfile.TemporaryDirectory() as d:
            root, harvest, units, candidates, _ = prepare(Path(d))
            result, errors = sessions.validate_batches_session(units, candidates, root/'upstream.lock', harvest)
            self.assertEqual(errors, [])
            with self.assertRaisesRegex(RecordError, 'live validation'):
                sessions._require_batch_validation(replace(result), root, harvest, units, candidates)
            with self.assertRaisesRegex(RecordError, 'package order'):
                sessions.validate_batches_session(units[::-1], candidates[::-1], root/'upstream.lock', harvest)
            for ups, cps in [(units[::-1], candidates[::-1]), (units[:1], candidates[:1]), (units, candidates[::-1])]:
                with self.subTest(ups=ups), self.assertRaises(RecordError):
                    workflow.render_batch(ups,cps,root/'upstream.lock',root/'never','synthetic','Synthetic',
                                          chapter_source_dir=harvest,_validation=result)
            alias=root/'translation-data/units/alias.jsonl';alias.symlink_to(units[0])
            with self.assertRaisesRegex(RecordError,'symlink'):
                workflow.render_batch([alias,*units[1:]],candidates,root/'upstream.lock',root/'never',
                    'synthetic','Synthetic',chapter_source_dir=harvest,_validation=result)
            self.assertFalse((root/'never').exists())
            alias.unlink()
            for forbidden in [harvest, root/'translation-data/units']:
                with self.assertRaisesRegex(RecordError, 'cannot write'):
                    workflow.render_batch(units, candidates, root/'upstream.lock', forbidden,
                        'synthetic', 'Synthetic', chapter_source_dir=harvest, _validation=result)
            inventory=root/'source-ir/extraction/units.jsonl'
            original_claim = result.provenance.snapshot.hashes.pop(inventory.resolve())
            with self.assertRaisesRegex(RecordError, 'claims changed'):
                result.assert_valid(root, harvest, units, candidates)
            result.provenance.snapshot.hashes[inventory.resolve()] = original_claim
            original=inventory.read_bytes();inventory.write_bytes(original+b' ')
            with self.assertRaisesRegex(RecordError,'changed'):
                result.assert_valid(root,harvest,units,candidates)

    def test_precondition_failure_does_not_write_and_mid_render_change_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root, harvest, units, candidates, raw = prepare(Path(d))
            pair=['--units',*[str(p) for p in units],'--candidates',*[str(p) for p in candidates],
                  '--lock',str(root/'upstream.lock'),'--harvest',str(harvest),
                  '--chapter-source-dir',str(harvest),'--tags-file',str(harvest/'tags/tags'),
                  '--model-lane','synthetic','--display-name','Synthetic','--output-dir',str(root/'preview')]
            original=raw.read_bytes();raw.write_bytes(original+b'{}\n')
            out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                self.assertEqual(main(['check-and-render',*pair]),1)
            self.assertFalse((root/'preview').exists());self.assertNotIn('Rendered',out.getvalue())
            raw.write_bytes(original)
            result, errors = sessions.validate_batches_session(units, candidates, root/'upstream.lock', harvest)
            self.assertEqual(errors, [])
            preview = root/'preview'
            old = {preview/'chapters/test.tex': b'old chapter\n',
                   preview/'metadata.tex': b'old metadata\n', preview/'contents.tex': b'old contents\n'}
            for path, payload in old.items():
                path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload)
            def render():
                return workflow.render_batch(units, candidates, root/'upstream.lock', preview,
                    'synthetic', 'Synthetic', chapter_source_dir=harvest,
                    tags_path=harvest/'tags/tags', _validation=result)
            real_write = Path.write_bytes
            def change_during_staging(path, payload):
                value = real_write(path, payload)
                if path.name == 'new-0' and path.parent.name.startswith('.render-'):
                    real_write(raw, original+b' ')
                return value
            with patch.object(Path, 'write_bytes', change_during_staging):
                with self.assertRaisesRegex(RecordError, 'changed'): render()
            self.assertEqual({p:p.read_bytes() for p in old}, old)
            raw.write_bytes(original)
            real_replace = os.replace
            def change_during_install(source, destination):
                value = real_replace(source, destination)
                if Path(source).name == 'new-0' and Path(destination) == preview/'chapters/test.tex':
                    raw.write_bytes(original+b' ')
                return value
            with patch.object(workflow.os, 'replace', change_during_install):
                with self.assertRaisesRegex(RecordError, 'changed'): render()
            self.assertEqual({p:p.read_bytes() for p in old}, old)
            raw.write_bytes(original)
            def fail_during_install(source, destination):
                if Path(source).name == 'new-1':
                    raise OSError('synthetic output failure')
                return real_replace(source, destination)
            with patch.object(workflow.os, 'replace', fail_during_install):
                with self.assertRaisesRegex(OSError, 'synthetic output failure'): render()
            self.assertEqual({p:p.read_bytes() for p in old}, old)
            self.assertFalse(list(root.glob('.render-*')))

    def test_transient_candidate_parse_cannot_render_unvalidated_text_after_bytes_restore(self):
        with tempfile.TemporaryDirectory() as d:
            root, harvest, units, candidates, _ = prepare(Path(d))
            result, errors = sessions.validate_batches_session(units, candidates, root/'upstream.lock', harvest)
            self.assertEqual(errors, [])
            path = candidates[0]; original = path.read_bytes()
            rows = [json.loads(line) for line in original.decode().splitlines()]
            text = rows[0]['translation']; trailing = text[len(text.rstrip()):]
            rows[0]['translation'] = text.rstrip() + '额外译文' + trailing
            from stacks_zh.records import sha256_value
            rows[0]['translation_hash'] = sha256_value(rows[0]['translation'])
            changed = ('\n'.join(json.dumps(row, ensure_ascii=False) for row in rows)+'\n').encode()
            actual = Path.read_bytes
            def transient(target):
                raw = actual(target)
                if target == path and any(frame.function == 'load_jsonl' and frame.filename.endswith('/records.py')
                                          for frame in inspect.stack()):
                    return changed
                return raw
            preview = root/'preview'
            with patch.object(Path, 'read_bytes', transient):
                with self.assertRaisesRegex(RecordError, 'bytes changed while reading'):
                    workflow.render_batch(units, candidates, root/'upstream.lock', preview,
                        'synthetic', 'Synthetic', chapter_source_dir=harvest,
                        tags_path=harvest/'tags/tags', _validation=result)
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse(preview.exists())

    def test_transient_adoption_record_read_fails_even_when_final_disk_bytes_match(self):
        with tempfile.TemporaryDirectory() as d:
            root, harvest, _, _, _ = prepare(Path(d))
            path = (root/'translation-data/source-adoptions/synthetic-first.json').resolve()
            original = path.read_bytes(); actual = Path.read_bytes
            def transient(target):
                raw = actual(target)
                frames = inspect.stack() if target == path else ()
                if (target == path and any(frame.function == 'load_repository_source_adoptions' for frame in frames)
                        and not any(frame.function in {'watch_root', 'watch_tree', 'assert_unchanged'} for frame in frames)):
                    return raw+b' '
                return raw
            with patch.object(Path, 'read_bytes', transient):
                result, errors = sessions._complete_provenance(root, harvest)
            self.assertIsNone(result)
            self.assertTrue(any('bytes changed while reading' in error for error in errors), errors)
            self.assertEqual(path.read_bytes(), original)

    def test_transient_glob_cannot_hide_the_last_bad_other_lane(self):
        with tempfile.TemporaryDirectory() as d:
            root, harvest, _, candidates, _ = prepare(Path(d))
            directory = (root/'translation-data/candidates').resolve()
            bad = directory/'zz-last/last.jsonl'; bad.parent.mkdir(); bad.write_bytes(candidates[0].read_bytes())
            actual = Path.glob
            def hidden(path, pattern):
                values = list(actual(path, pattern))
                if ((path == directory and pattern == '*/*.jsonl')
                        or (path == root.resolve() and pattern == 'translation-data/candidates/*/*.jsonl')):
                    values = [value for value in values if value != bad]
                return iter(values)
            with patch.object(Path, 'glob', hidden):
                with self.assertRaisesRegex(RecordError, 'paths changed while enumerating'):
                    sessions.validate_repository(root, harvest)
            self.assertTrue(bad.is_file())

    def test_ordinary_run_pairs_use_actual_source_order_without_an_adoption_pointer(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('test_source_adoptions.english_fixture', side_effect=with_manifest):
                root, harvest, _, _, frozen, _ = provisional_fixture(Path(d))
            # Represent the ordinary state before provisional adoption archives existed.
            for path in (root/'translation-data/retired/source-adoptions').rglob('*.jsonl'):
                path.unlink()
            for name in ['Makefile', 'AGENTS.md', 'WORKFLOW.md', 'stacks_zh.py']:
                shutil.copyfile(REPOSITORY/name, root/name)
            units = [root/b['units_path'] for b in frozen['batches']]
            candidates = [root/b['candidates_path'] for b in frozen['batches']]
            result, errors = sessions.validate_batches_session(units, candidates, root/'upstream.lock', harvest)
            self.assertEqual(errors, [])
            self.assertFalse(result.provenance.adoptions)
            workflow.render_batch(units, candidates, root/'upstream.lock', root/'ordinary-preview',
                'synthetic', 'Synthetic', chapter_source_dir=harvest,
                tags_path=harvest/'tags/tags', _validation=result)
            with self.assertRaisesRegex(RecordError, 'locked source order'):
                sessions.validate_batches_session(units[::-1], candidates[::-1], root/'upstream.lock', harvest)
            self.assertFalse((root/'never').exists())

    def test_real_header_v4_joint_session_reuses_one_actual_adoption_replay(self):
        from test_stacks_introduction_source_prerequisites import header_fixture
        with tempfile.TemporaryDirectory() as d:
            with patch('test_source_adoptions.english_fixture', side_effect=with_manifest):
                root, harvest, fp, rp, frozen, _ = header_fixture(Path(d))
            source_adoptions.assemble_source_adoption(root, fp, [rp], harvest)
            for name in ['Makefile', 'AGENTS.md', 'WORKFLOW.md', 'stacks_zh.py']:
                shutil.copyfile(REPOSITORY/name, root/name)
            units = [root/b['units_path'] for b in frozen['batches']]
            candidates = [root/b['candidates_path'] for b in frozen['batches']]
            with patch.object(source_adoptions, 'load_repository_source_adoptions',
                              wraps=source_adoptions.load_repository_source_adoptions) as loader:
                result, errors = sessions.validate_batches_session(units, candidates, root/'upstream.lock', harvest)
                self.assertEqual(errors, [])
                workflow.render_batch(units, candidates, root/'upstream.lock', root/'header-preview',
                    'synthetic', 'Synthetic', chapter_source_dir=harvest,
                    tags_path=harvest/'tags/tags', _validation=result)
                self.assertEqual(loader.call_count, 1)
            self.assertIn(r'\chapter{合成章标题}', (root/'header-preview/chapters/test.tex').read_text())
            raw = rp.read_bytes(); rp.write_bytes(raw+b'{}\n')
            partial, errors = source_adoptions.load_repository_source_adoptions(root, harvest)
            self.assertTrue(errors)
            self.assertNotIsInstance(partial, source_adoptions._ValidatedAdoptions)

    def test_actual_whole_repository_keeps_multiple_runs_and_last_other_lane_errors(self):
        # Full accepted v3/ordinary/shared ancestry supplies multiple real fixture runs.
        with tempfile.TemporaryDirectory() as d:
            with patch('test_source_adoptions.english_fixture',side_effect=with_manifest):
                root,harvest,fp,rp,frozen=shared_run_fixture(Path(d),followup=True)
            source_adoptions.assemble_source_adoption(root,fp,[rp],harvest)
            for name in ['Makefile','AGENTS.md','WORKFLOW.md','stacks_zh.py']:
                shutil.copyfile(REPOSITORY/name,root/name)
            count,errors=sessions.validate_repository(root,harvest)
            self.assertEqual(errors,[]);self.assertGreater(count,1)
            candidates=sorted((root/'translation-data/candidates').glob('*/*.jsonl'))
            units=[root/'translation-data/units'/p.name for p in candidates]
            _,errors=sessions.validate_batches_session(units,candidates,root/'upstream.lock',harvest)
            self.assertTrue(any('mismatch for run_id' in e for e in errors),errors)
            proof,errors=sessions._complete_provenance(root,harvest)
            self.assertEqual(errors,[])
            ancestor=next((root/'translation-data/retired/source-adoptions').glob('*/candidates.jsonl'))
            original=ancestor.read_bytes();ancestor.write_bytes(original+b' ')
            with self.assertRaisesRegex(RecordError,'changed'):proof.assert_valid(root,harvest)
            ancestor.write_bytes(original)
            other=root/'translation-data/candidates/zz-last/last.jsonl'
            other.parent.mkdir();other.write_text('{}\n')
            _,errors=sessions.validate_repository(root,harvest)
            self.assertTrue(any('last.jsonl' in e for e in errors),errors)


if __name__=='__main__': unittest.main()
