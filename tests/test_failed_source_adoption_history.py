"""Synthetic rejected generation history; no actual model or approval claims."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_source_adoptions import followup_fixture, write
from test_source_containers import git
from stacks_zh.records import RecordError, write_jsonl
from stacks_zh.source_adoptions import assemble_source_adoption, load_repository_source_adoptions
from stacks_zh.source_reextractions import byte_hash


def failed_fixture(base, *, malformed=False):
    root, harvest, fp, rp, frozen, first = followup_fixture(base)
    rows = [json.loads(line) for line in rp.read_text().splitlines()]
    if malformed:
        rows[0]['notes'] = [{'synthetic': 'wrong type'}]
    else:
        rows = rows[:1]
    write_jsonl(rp, rows)
    try:
        assemble_source_adoption(root, fp, [rp], harvest)
    except ValueError as exc:
        failure = str(exc)
    else:
        raise AssertionError('synthetic invalid output was accepted')
    manifest = json.loads((root / first['run']['path']).read_bytes())
    manifest.update(run_id=frozen['run_id'], created_at=frozen['created_at'], unit_ids=frozen['unit_ids'])
    manifest['inputs']['context_hashes'] = []
    manifest['inputs']['settings'] = dict(
        reasoning_effort=frozen['runtime']['reasoning_effort'], turn_id=frozen['runtime']['turn_id'],
        frozen_generation_input=dict(path=str(fp.relative_to(root)), hash=byte_hash(fp.read_bytes())),
        generation_context_hashes=[c['hash'] for c in frozen['contexts']],
        raw_attempts=[dict(path=str(rp.relative_to(root)), hash=byte_hash(rp.read_bytes()),
                           unit_ids=[r['unit_id'] for r in rows])],
        accepted_records=[], observed_assembly_exit_code=1, observed_assembly_error='ERROR: ' + failure)
    mp = root / ('translation-data/runs/' + frozen['run_id'] + '.json')
    write(mp, manifest)
    return root.resolve(), harvest.resolve(), fp.resolve(), rp.resolve(), mp.resolve(), frozen, manifest, first


class FailedSourceAdoptionHistoryTests(unittest.TestCase):
    def test_failed_freeze_snapshots_are_validated_without_adopting_failure(self):
        for malformed in [False, True]:
            with self.subTest(malformed=malformed), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, mp, frozen, manifest, first = failed_fixture(Path(temp), malformed=malformed)
                before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
                adopted, errors = load_repository_source_adoptions(root, harvest)
                self.assertEqual(errors, [])
                self.assertEqual(len(adopted), 2)
                self.assertTrue(all(v['record']['adoption_id'] == first['adoption_id'] for v in adopted.values()))
                adopted.assert_unchanged(root, harvest)
                self.assertEqual(before, {p: p.read_bytes() for p in before})
                dependencies = set(adopted.snapshots[0].hashes)
                self.assertTrue({fp, rp, mp}.issubset(dependencies))
                for output in frozen['prior_adoptions'][0]['outputs']:
                    self.assertTrue({root / output[r]['path'] for r in ['units', 'candidates']}.issubset(dependencies))

    def test_same_first_git_addition_replays_and_rehashed_tampering_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, mp, frozen, manifest, first = failed_fixture(Path(temp))
            git(root, 'add', '.')
            git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'Synthetic retained failed generation')
            self.assertEqual(load_repository_source_adoptions(root, harvest)[1], [])
            rows = [json.loads(line) for line in rp.read_text().splitlines()]
            rows[0]['notes'].append('synthetic tamper'); write_jsonl(rp, rows)
            manifest['inputs']['settings']['raw_attempts'][0]['hash'] = byte_hash(rp.read_bytes()); write(mp, manifest)
            self.assertTrue(load_repository_source_adoptions(root, harvest)[1])

    def test_false_failure_cannot_hide_valid_complete_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, first = followup_fixture(Path(temp))
            valid_raw = rp.read_bytes()
            # Build a genuine failed witness, then replace its raw by valid full output.
            root, harvest, fp, rp, mp, frozen, manifest, first = failed_fixture(Path(temp) / 'other')
            rp.write_bytes(valid_raw)
            attempt = manifest['inputs']['settings']['raw_attempts'][0]
            attempt.update(hash=byte_hash(valid_raw), unit_ids=[r['unit_id'] for r in map(json.loads, valid_raw.decode().splitlines())])
            write(mp, manifest)
            errors = load_repository_source_adoptions(root, harvest)[1]
            self.assertTrue(any('complete valid assembly' in e for e in errors), errors)

    def test_failed_run_identity_context_and_rejection_are_exact(self):
        for field in ['model', 'turn', 'effort', 'accepted', 'contexts', 'error', 'exit']:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, mp, frozen, manifest, first = failed_fixture(Path(temp))
                settings = manifest['inputs']['settings']
                if field == 'model': manifest['model']['resolved_id'] = 'other-synthetic'
                elif field == 'turn': settings['turn_id'] = 'other-synthetic'
                elif field == 'effort': settings['reasoning_effort'] = 'other-synthetic'
                elif field == 'accepted': settings['accepted_records'] = [{}]
                elif field == 'contexts': settings['generation_context_hashes'] = []
                elif field == 'error': settings['observed_assembly_error'] = 'ERROR: fabricated'
                elif field == 'exit': settings['observed_assembly_exit_code'] = 0
                write(mp, manifest)
                self.assertTrue(load_repository_source_adoptions(root, harvest)[1])

    def test_missing_marker_or_unrelated_orphan_remains_rejected(self):
        for marker in [False, True]:
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, mp, frozen, manifest, first = failed_fixture(Path(temp))
                if not marker:
                    del manifest['inputs']['settings']['frozen_generation_input']; write(mp, manifest)
                else:
                    extra = root / 'translation-data/retired/source-adoptions/synthetic-orphan/units.jsonl'
                    extra.parent.mkdir(); extra.write_text('{}\n')
                self.assertTrue(any('orphaned' in e for e in load_repository_source_adoptions(root, harvest)[1]))

    def test_raw_hash_scope_and_all_attempt_bytes_remain_required(self):
        for field in ['hash', 'scope', 'later']:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, mp, frozen, manifest, first = failed_fixture(Path(temp), malformed=True)
                attempts = manifest['inputs']['settings']['raw_attempts']
                if field == 'hash': attempts[0]['hash'] = 'sha256:' + '0' * 64
                elif field == 'scope': attempts[0]['path'] = 'docs/evidence/outside-synthetic-scope.jsonl'
                else:
                    later = copy.deepcopy(attempts[0]); later['hash'] = 'sha256:' + '0' * 64
                    attempts.append(later)
                write(mp, manifest)
                self.assertTrue(load_repository_source_adoptions(root, harvest)[1])

    def test_failed_raw_change_after_replay_is_not_certified(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, mp, frozen, manifest, first = failed_fixture(Path(temp))
            from stacks_zh import source_adoptions as module
            original = module._raw_records
            def changed(reads, entries, *args):
                if entries[0]['path'] == str(rp.relative_to(root)):
                    try: return original(reads, entries, *args)
                    finally: rp.write_bytes(rp.read_bytes() + b'\n')
                return original(reads, entries, *args)
            with patch('stacks_zh.source_adoptions._raw_records', side_effect=changed):
                with self.assertRaisesRegex(RecordError, 'validation input changed'):
                    load_repository_source_adoptions(root, harvest)


if __name__ == '__main__':
    unittest.main()
