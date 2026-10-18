"""Synthetic current-policy regressions; never actual model translation evidence."""
import copy
import contextlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_derivations import COMMIT, fixture
from stacks_zh.current_qa import InputSnapshot, validate_current_records
from stacks_zh.records import RecordError, sha256_value, stamp_unit_hashes, validate_records
from stacks_zh.source_terms import source_tex_hash


class CurrentEntryPointTests(unittest.TestCase):
    """Real CLI checks against a tiny independent English Git repository."""

    def fixture(self, base):
        from test_source_alignment import AlignmentTests
        from test_workflow import make_batch_candidate
        from stacks_zh.records import write_jsonl
        root, harvest, _, _ = AlignmentTests().fixture(base)
        repository = Path(__file__).resolve().parents[1]
        shutil.copytree(repository / 'schema', root / 'schema')
        shutil.copyfile(repository / 'config/workflow.yml', root / 'config/workflow.yml')
        (root / 'config/glossary.yml').write_text('entries: []\n')
        up = root / 'translation-data/units/alpha-bbbb.jsonl'
        unit = stamp_unit_hashes(json.loads(up.read_text()))
        candidate = make_batch_candidate(unit, model_lane='synthetic')
        candidate.update(source_commit=unit['source_commit'],
            translation='一个范畴（category）。' + re.search(r'[ \t\r\n]*$', unit['source_text'])[0],
            term_occurrences=[dict(source_term='category', target_term='范畴')],
            unknown_terms=[dict(source_term='category', target_term='范畴', context='Synthetic fixture.')],
            term_status='DECISION_REQUIRED', stage='STRUCTURE_OK')
        candidate['translation_hash'] = sha256_value(candidate['translation'])
        catalog = dict(schema_version=1, source_commit=unit['source_commit'],
            nonmathematical_declarations={}, terms=[dict(id='category', forms=['category'], chapters=[],
                evidence=[dict(chapter='alpha', unit_id=unit['unit_id'], source_term='category',
                    source_tex_hash=source_tex_hash(unit))])])
        (root / 'config/source-terms.json').write_text(json.dumps(catalog))
        cp = root / 'translation-data/candidates/synthetic/alpha-bbbb.jsonl'
        write_jsonl(up, [unit]); write_jsonl(cp, [candidate])
        SnapshotTests().repository(root)
        return root, harvest, up, cp, candidate

    def invoke(self, arguments):
        from stacks_zh.cli import main
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(arguments)
        return code, out.getvalue(), err.getvalue()

    def test_all_six_cli_entry_points_reject_missing_source_term_before_writing(self):
        from stacks_zh.records import write_jsonl
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, up, cp, candidate = self.fixture(Path(temp))
            common = ['--lock', str(root / 'upstream.lock'), '--harvest', str(harvest)]
            pair = ['--units', str(up), '--candidates', str(cp)]
            self.assertEqual(self.invoke(['validate', *pair, *common])[0], 0)
            candidate.update(translation=candidate['translation'].replace('（category）', ''),
                term_occurrences=[], unknown_terms=[], term_status='CLEAR', stage='TERM_OK')
            candidate['translation_hash'] = sha256_value(candidate['translation'])
            write_jsonl(cp, [candidate])
            draft = root / 'draft.jsonl'
            write_jsonl(draft, [{k: candidate[k] for k in
                ['unit_id', 'translation', 'term_occurrences', 'unknown_terms', 'notes', 'allowed_english']}])
            assembly = ['--units', str(up), '--drafts', str(draft), '--output', str(root / 'never-created.jsonl'),
                '--model-id', 'synthetic', '--model-lane', 'synthetic', '--reasoning-effort', 'not_exposed',
                '--prompt-version', 'synthetic', '--policy-revision', 'synthetic', '--glossary-revision', 'synthetic',
                '--created-at', '2026-10-16T00:00:00Z', '--harness-id', 'codex', '--model-record-id', 'synthetic',
                '--run-id', 'synthetic', '--model-identity-confidence', 'declared']
            commands = [ ['validate', *pair], ['validate-many', *pair],
                ['validate-all', '--root', str(root)],
                ['render', *pair, '--model-lane', 'synthetic', '--display-name', 'Synthetic'],
                ['assemble', *assembly], ['assemble-many', *assembly] ]
            with mock.patch('stacks_zh.cli.assemble_candidates') as assemble, \
                 mock.patch('stacks_zh.cli.assemble_candidates_many') as many, \
                 mock.patch('stacks_zh.cli.render_batch') as render:
                for command in commands:
                    with self.subTest(command=command[0]):
                        code, out, err = self.invoke([*command, *common])
                        self.assertEqual(code, 1, err)
                        self.assertIn('missing source-side term coverage', err)
                        self.assertNotIn('PASS', out)
                assemble.assert_not_called(); many.assert_not_called(); render.assert_not_called()
            self.assertFalse((root / 'never-created.jsonl').exists())

    def test_disabled_policy_and_stale_inventory_cannot_bypass_actual_source(self):
        from stacks_zh.current_qa import CurrentSourceQA
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, up, cp, _ = self.fixture(Path(temp))
            policy = root / 'config/workflow.yml'; original = policy.read_text()
            policy.write_text(original.replace('require_source_term_occurrence_coverage: true',
                'require_source_term_occurrence_coverage: false'))
            with self.assertRaisesRegex(RecordError, 'every strict gate'):
                CurrentSourceQA(root, harvest)
            policy.write_text(original)
            inventory = root / 'source-ir/extraction/units.jsonl'
            inventory.write_text(inventory.read_text().replace('A category.', 'Changed source.'))
            with self.assertRaises(RecordError):
                CurrentSourceQA(root, harvest).validate_pairs([up], [cp])


def current_fixture():
    _, units, candidates = fixture()
    unit, candidate = units[0], candidates[0]
    unit['unit_id'] = 'tag:ABCD:paragraph-0001';unit['parent_tag'] = 'ABCD'
    unit = stamp_unit_hashes(unit)
    candidate.update(unit_id=unit['unit_id'], source_text_hash=unit['source_text_hash'],
        translation='一个范畴（category）。',
        term_occurrences=[dict(source_term='category', target_term='范畴')],
        unknown_terms=[dict(source_term='category', target_term='范畴', context='Synthetic pending term.')],
        term_status='DECISION_REQUIRED', stage='STRUCTURE_OK')
    candidate['translation_hash'] = sha256_value(candidate['translation'])
    catalog=dict(schema_version=1, source_commit=COMMIT, nonmathematical_declarations={}, terms=[
        dict(id='category', forms=['category'], chapters=[], evidence=[dict(chapter='test',
            unit_id=unit['unit_id'], source_term='category', source_tex_hash=source_tex_hash(unit))])])
    return unit, candidate, catalog, {'test-section': 'ABCD', 'test-definition': 'EFGH'}


class CurrentRecordTests(unittest.TestCase):
    def check(self, unit, candidate, catalog, tags):
        return validate_current_records([unit], [candidate], COMMIT, catalog, tags, set())

    def test_passes_pending_terms_without_mutation_or_approval(self):
        values=current_fixture();before=copy.deepcopy(values)
        self.assertEqual(self.check(*values), [])
        self.assertEqual(values,before)
        self.assertEqual(values[1]['term_status'],'DECISION_REQUIRED')

    def test_core_qa_pass_cannot_hide_missing_source_terms(self):
        unit,candidate,catalog,tags=current_fixture()
        candidate.update(translation='一个范畴。',term_occurrences=[],unknown_terms=[],term_status='CLEAR',stage='TERM_OK')
        candidate['translation_hash']=sha256_value(candidate['translation'])
        self.assertEqual(validate_records([unit],[candidate],COMMIT),[])
        self.assertTrue(any('missing source-side term coverage' in e for e in self.check(unit,candidate,catalog,tags)))
        candidate['allowed_english']=['category']
        self.assertTrue(any('missing source-side term coverage' in e for e in self.check(unit,candidate,catalog,tags)))

    def test_raw_tex_and_false_clear_are_rejected(self):
        for fault in ['percent','group','clear']:
            unit,candidate,catalog,tags=current_fixture()
            if fault=='percent':candidate['translation']+=' % hidden'
            elif fault=='group':candidate['translation']+=' {'
            else:candidate['term_status']='CLEAR'
            candidate['translation_hash']=sha256_value(candidate['translation'])
            with self.subTest(fault=fault):self.assertTrue(self.check(unit,candidate,catalog,tags))

    def test_tag_hidden_footnote_and_hidden_title_are_rejected(self):
        for fault in ['tag','footnote','title']:
            unit,candidate,catalog,tags=current_fixture()
            if fault=='tag':
                unit.update(node_kind='definition',render=dict(prefix='\\begin{definition}\\label{definition}\n',suffix='\\end{definition}\n'))
            elif fault=='title':
                unit.update(node_kind='definition',render=dict(prefix='\\begin{definition}[Named title]\\label{section}\n',suffix='\\end{definition}\n'))
            else:
                unit['source_text']+=' <FOOTNOTE_0001>'
                unit['placeholders']={'FOOTNOTE_0001':r'\footnote{See Remark \ref{section}.}'}
                candidate['translation']+=' <FOOTNOTE_0001>'
            unit=stamp_unit_hashes(unit);candidate['source_text_hash']=unit['source_text_hash'];candidate['translation_hash']=sha256_value(candidate['translation'])
            with self.subTest(fault=fault):self.assertTrue(self.check(unit,candidate,catalog,tags))

    def test_protected_order_and_trailing_whitespace_are_strict(self):
        unit,candidate,catalog,tags=current_fixture()
        unit['source_text']+=' <MATH_0001> <MATH_0002>\n';unit['placeholders']={'MATH_0001':'$x$','MATH_0002':'$y$'};unit=stamp_unit_hashes(unit)
        candidate['source_text_hash']=unit['source_text_hash'];candidate['translation']+=' <MATH_0002> <MATH_0001>\n';candidate['translation_hash']=sha256_value(candidate['translation'])
        self.assertTrue(any('order' in e for e in self.check(unit,candidate,catalog,tags)))
        candidate['translation']=candidate['translation'].replace('<MATH_0002> <MATH_0001>','<MATH_0001> <MATH_0002>').rstrip('\n');candidate['translation_hash']=sha256_value(candidate['translation'])
        self.assertTrue(any('whitespace' in e for e in self.check(unit,candidate,catalog,tags)))

    def test_catalog_commit_and_missing_tags_fail_closed(self):
        unit,candidate,catalog,tags=current_fixture();catalog['source_commit']='b'*40
        self.assertTrue(self.check(unit,candidate,catalog,tags))
        catalog['source_commit']=COMMIT
        self.assertTrue(self.check(unit,candidate,catalog,{}))


class SnapshotTests(unittest.TestCase):
    def repository(self, path):
        subprocess.run(['git','-C',str(path),'init','-q'],check=True,capture_output=True)
        (path/'initial').write_text('fixture')
        subprocess.run(['git','-C',str(path),'add','.'],check=True,capture_output=True)
        subprocess.run(['git','-C',str(path),'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True,capture_output=True)

    def test_actual_bytes_new_files_and_symlinks_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.repository(root);directory=root/'facts';directory.mkdir();path=directory/'one.jsonl';path.write_text('{"value":1}\n')
            snapshot=InputSnapshot(root);snapshot.watch_tree(directory)
            self.assertEqual(snapshot.jsonl(path)[0]['value'],1);snapshot.assert_unchanged()
            path.write_text('{"value":2}\n')
            with self.assertRaisesRegex(RecordError,'changed'):snapshot.assert_unchanged()
            path.write_text('{"value":1}\n');snapshot=InputSnapshot(root);snapshot.watch_tree(directory);(directory/'new').write_text('new')
            with self.assertRaisesRegex(RecordError,'paths changed'):snapshot.assert_unchanged()
            (directory/'new').unlink();path.unlink();path.symlink_to(root/'initial')
            with self.assertRaisesRegex(RecordError,'symlink'):InputSnapshot(root).watch_tree(directory)

    def test_git_head_changes_cannot_reuse_a_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.repository(root);snapshot=InputSnapshot(root)
            subprocess.run(['git','-C',str(root),'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','--allow-empty','-qm','later'],check=True,capture_output=True)
            with self.assertRaisesRegex(RecordError,'HEAD changed'):snapshot.assert_unchanged()


if __name__=='__main__':unittest.main()
