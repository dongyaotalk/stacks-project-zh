"""Synthetic public preparation fixtures; no actual model or approval evidence."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_source_adoptions import synthetic_fixture, write
from test_chapter_validation import preparation_copy
from stacks_zh.chapter_relations import check_preparation_evidence
from stacks_zh.current_qa import InputSnapshot
from stacks_zh.validation_io import InputReads
from stacks_zh.source_containers import Containers
from stacks_zh.harness import load_harness_registry, parse_harness_registry
from stacks_zh.records import RecordError


def fixture(base):
    root, harvest, fp, rp, frozen, raw = synthetic_fixture(base)
    mp, rt = preparation_copy(root, frozen, fp, rp)
    runtime = json.loads(rt.read_bytes())
    runtime['harness_check'].update(
        argv=['make', 'harness-check', 'HARNESS_ID=synthetic',
              'PYTHON=/synthetic/python', 'HARVEST_DIR=/synthetic/harvest'],
        stdout='synthetic: ' + frozen['runtime']['harness']['version'] + '\ncommand: python3 --version\n',
        stderr='')
    write(rt, runtime)
    return root, harvest, fp, rp, frozen, mp, rt, runtime


def check(root, harvest, mp):
    reads = InputReads()
    with reads.activate():
        result = check_preparation_evidence(root, harvest, InputSnapshot(root),
            [mp.relative_to(root).as_posix()], 'test', 'synthetic', reads, Containers(root, harvest))
        reads.assert_unchanged()
        return result


class RuntimeCopySummaryTests(unittest.TestCase):
    def test_existing_explicit_summaries_and_registry_parser_preserve_behavior(self):
        with tempfile.TemporaryDirectory() as directory:
            root, harvest, fp, rp, frozen, mp, rt, runtime = fixture(Path(directory))
            registry = root / 'config/harnesses.yml'
            self.assertEqual(load_harness_registry(registry), parse_harness_registry(registry.read_text()))
            binding = check(root, harvest, mp)[0]['runtime_copy_binding']
            self.assertEqual(binding['version_binding'], 'explicit-summary')
            self.assertEqual(binding['provider_binding'], 'explicit-summary')

    def test_absent_redundant_summaries_bind_original_capture_and_keep_all_bytes(self):
        for fields in [('observed_version',), ('provider',), ('observed_version', 'provider')]:
            with self.subTest(fields=fields), tempfile.TemporaryDirectory() as directory:
                root, harvest, fp, rp, frozen, mp, rt, runtime = fixture(Path(directory))
                for field in fields:
                    (runtime['harness_check'] if field == 'observed_version' else runtime).pop(field)
                write(rt, runtime)
                immutable = {p: p.read_bytes() for p in (fp, rp, mp, rt, root/frozen['task']['scope_manifest'])}
                result = check(root, harvest, mp)[0]
                self.assertEqual(result['runtime_copy_binding']['version_binding'],
                                 'original-make-capture' if 'observed_version' in fields else 'explicit-summary')
                self.assertEqual(result['runtime_copy_binding']['provider_binding'],
                                 'exact-frozen-runtime' if 'provider' in fields else 'explicit-summary')
                self.assertFalse(result['runtime_copy_binding']['runtime_changed'])
                self.assertEqual(result['generation_validation'], 'not_claimed')
                for path, payload in immutable.items():
                    self.assertEqual(path.read_bytes(), payload)
                self.assertFalse((root/f"translation-data/runs/{frozen['run_id']}.json").exists())
                self.assertFalse((root/f"translation-data/source-adoptions/{frozen['adoption_id']}.json").exists())

    def test_bad_or_incomplete_capture_never_supplies_a_missing_version(self):
        mutations = ['wrong-version', 'unknown-version', 'duplicate-version', 'missing-version',
                     'wrong-harness', 'missing-harness', 'duplicate-harness', 'extra-make-flag',
                     'empty-assignment', 'duplicate-python', 'missing-argv', 'missing-stdout',
                     'wrong-command', 'duplicate-command', 'missing-command', 'failed-exit']
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root, harvest, fp, rp, frozen, mp, rt, runtime = fixture(Path(directory))
                c = runtime['harness_check']; c.pop('observed_version')
                version = frozen['runtime']['harness']['version']
                if mutation == 'wrong-version': c['stdout'] = c['stdout'].replace(version, '9999.0.0')
                elif mutation == 'unknown-version': c['stdout'] = c['stdout'].replace(version, 'unknown')
                elif mutation == 'duplicate-version': c['stdout'] += 'synthetic: ' + version + '\n'
                elif mutation == 'missing-version': c['stdout'] = 'command: python3 --version\n'
                elif mutation == 'wrong-harness': c['argv'][2] = 'HARNESS_ID=wrong'
                elif mutation == 'missing-harness': c['argv'].pop(2)
                elif mutation == 'duplicate-harness': c['argv'].append('HARNESS_ID=synthetic')
                elif mutation == 'extra-make-flag': c['argv'].append('--eval=unexpected')
                elif mutation == 'empty-assignment': c['argv'].append('EXTRA=')
                elif mutation == 'duplicate-python': c['argv'].append('PYTHON=/another/python')
                elif mutation == 'missing-argv': c.pop('argv')
                elif mutation == 'missing-stdout': c.pop('stdout')
                elif mutation == 'wrong-command': c['stdout'] = c['stdout'].replace('python3 --version', 'other --version')
                elif mutation == 'duplicate-command': c['stdout'] += 'command: python3 --version\n'
                elif mutation == 'missing-command': c['stdout'] = 'synthetic: ' + version + '\n'
                else: c['exit_code'] = 1
                write(rt, runtime)
                with self.assertRaises(RecordError): check(root, harvest, mp)

    def test_contradictory_explicit_summaries_and_actual_identity_still_fail(self):
        for mutation in ['provider', 'provider-type', 'explicit-version', 'explicit-null',
                         'runtime', 'turn', 'model', 'effort']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root, harvest, fp, rp, frozen, mp, rt, runtime = fixture(Path(directory))
                if mutation == 'provider': runtime['provider'] = 'different'
                elif mutation == 'provider-type': runtime['provider'] = None
                elif mutation == 'explicit-version': runtime['harness_check']['observed_version'] = 'wrong'
                elif mutation == 'explicit-null': runtime['harness_check']['observed_version'] = None
                elif mutation == 'runtime': runtime['runtime'] = copy.deepcopy(runtime['runtime']); runtime['runtime']['model']['provider'] = 'different'
                elif mutation == 'turn': runtime['turn_metadata']['turn_id'] = 'different'
                elif mutation == 'model': runtime['turn_metadata']['model'] = 'different'
                else: runtime['turn_metadata']['effort'] = 'different'
                write(rt, runtime)
                with self.assertRaises(RecordError): check(root, harvest, mp)


if __name__ == '__main__':
    unittest.main()
