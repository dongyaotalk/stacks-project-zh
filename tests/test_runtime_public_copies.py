"""Synthetic captures only; no actual model or human approval evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from test_runtime_copy_summary import fixture, check
from test_source_adoptions import write
from stacks_zh.runtime_public_copies import project_runtime_copy, validate_public_capture, PROJECTION
from stacks_zh.records import RecordError
from stacks_zh.source_reextractions import byte_hash


class RuntimePublicCopyTests(unittest.TestCase):
    def test_public_copy_binds_original_identity_without_touching_private_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root, harvest, fp, rp, frozen, mp, rt, original = fixture(Path(directory))
            private = rt.read_bytes()
            registry = (root/'config/harnesses.yml').read_bytes()
            public = project_runtime_copy(frozen, private, registry)
            self.assertEqual(public, project_runtime_copy(frozen, private, registry))
            self.assertEqual(public['runtime'], original['runtime'])
            self.assertEqual(public[PROJECTION]['source_capture_sha256'], byte_hash(private))
            self.assertNotIn('/synthetic/', json.dumps(public))
            self.assertEqual(rt.read_bytes(), private)
            write(rt, public)  # Synthetic separate delivery view.
            binding = check(root, harvest, mp)[0]['runtime_copy_binding']
            self.assertEqual(binding['version_binding'], 'public-make-capture-projection')
            self.assertFalse(binding['runtime_changed'])
            self.assertEqual(binding['private_capture_replay'], 'not_claimed')

    def test_missing_summaries_use_original_registered_output_without_inventing_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root, harvest, fp, rp, frozen, mp, rt, original = fixture(Path(directory))
            original.pop('provider'); original['harness_check'].pop('observed_version')
            public = project_runtime_copy(frozen, json.dumps(original).encode(),
                                          (root/'config/harnesses.yml').read_bytes())
            self.assertNotIn('provider', public)
            self.assertNotIn('observed_version', public['harness_check'])
            write(rt, public)
            self.assertEqual(check(root, harvest, mp)[0]['runtime_copy_binding']['provider_binding'],
                             'exact-frozen-runtime')

    def test_bad_original_capture_cannot_be_hidden_by_projection(self):
        for mutation in ['exit', 'command', 'version', 'argv', 'stderr', 'turn', 'identity']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root, harvest, fp, rp, frozen, mp, rt, original = fixture(Path(directory))
                c = original['harness_check']
                if mutation == 'exit': c['exit_code'] = 1
                elif mutation == 'command': c['stdout'] = c['stdout'].replace('python3 --version', 'other --version')
                elif mutation == 'version': c['stdout'] += c['stdout']
                elif mutation == 'argv': c['argv'].append(c['argv'][-1])
                elif mutation == 'stderr': c['stderr'] = 'unaccounted output'
                elif mutation == 'turn': original['turn_metadata']['model'] = 'different'
                else: original['runtime']['harness']['version'] = 'different'
                with self.assertRaises(RecordError):
                    project_runtime_copy(frozen, json.dumps(original).encode(), (root/'config/harnesses.yml').read_bytes())

    def test_malformed_or_changed_public_receipt_is_rejected(self):
        for mutation in ['method', 'hash', 'extra', 'argv', 'stdout', 'path', 'runtime']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root, harvest, fp, rp, frozen, mp, rt, original = fixture(Path(directory))
                registry = (root/'config/harnesses.yml').read_bytes()
                public = project_runtime_copy(frozen, rt.read_bytes(), registry)
                if mutation == 'method': public[PROJECTION]['method'] = 'other'
                elif mutation == 'hash': public[PROJECTION]['source_capture_sha256'] = 'invalid'
                elif mutation == 'extra': public[PROJECTION]['extra'] = True
                elif mutation == 'argv': public['harness_check']['argv'].append('PYTHON=local')
                elif mutation == 'stdout': public['harness_check']['stdout'] += 'ignored\n'
                elif mutation == 'path': public['note'] = 'local ' + str(root)
                else: public['runtime']['turn_id'] = 'different'
                with self.assertRaises(RecordError): validate_public_capture(frozen, public, registry)

    def test_only_the_known_local_python_make_echo_is_omitted(self):
        with tempfile.TemporaryDirectory() as directory:
            root, harvest, fp, rp, frozen, mp, rt, original = fixture(Path(directory))
            echo = '/synthetic/python stacks_zh.py harness-version --harness-id "synthetic" --config "config/harnesses.yml"\n'
            original['harness_check']['stdout'] = echo + original['harness_check']['stdout']
            private = json.dumps(original).encode()
            public = project_runtime_copy(frozen, private, (root/'config/harnesses.yml').read_bytes())
            self.assertEqual(public['harness_check']['stdout'],
                             'synthetic: 3.12.6\ncommand: python3 --version\n')
            self.assertEqual(public[PROJECTION]['source_capture_sha256'], byte_hash(private))
            self.assertEqual(original['harness_check']['stdout'].encode(), json.loads(private)['harness_check']['stdout'].encode())

    def test_other_stdout_or_capture_fields_are_not_silently_discarded(self):
        echo = '/synthetic/python stacks_zh.py harness-version --harness-id synthetic --config config/harnesses.yml\n'
        for mutation in ['message', 'path', 'wrong-python', 'extra-argument', 'duplicate-echo',
                         'reordered-output', 'extra-field', 'boolean-exit', 'float-exit']:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root, harvest, fp, rp, frozen, mp, rt, original = fixture(Path(directory))
                c = original['harness_check']; stdout = c['stdout']
                if mutation == 'message': c['stdout'] += 'unaccounted non-path capture message\n'
                elif mutation == 'path': c['stdout'] += '/synthetic/unaccounted/path\n'
                elif mutation == 'wrong-python': c['stdout'] = echo.replace('/synthetic/python', '/other/python') + stdout
                elif mutation == 'extra-argument': c['stdout'] = echo.rstrip('\n') + ' --extra\n' + stdout
                elif mutation == 'duplicate-echo': c['stdout'] = echo + echo + stdout
                elif mutation == 'reordered-output': c['stdout'] = 'command: python3 --version\nsynthetic: 3.12.6\n'
                elif mutation == 'extra-field': c['unexpected_metadata'] = 'must not discard'
                elif mutation == 'boolean-exit': c['exit_code'] = False
                else: c['exit_code'] = 0.0
                with self.assertRaises(RecordError):
                    project_runtime_copy(frozen, json.dumps(original).encode(), (root/'config/harnesses.yml').read_bytes())

    def test_projection_version_requires_an_integer(self):
        with tempfile.TemporaryDirectory() as directory:
            root, harvest, fp, rp, frozen, mp, rt, original = fixture(Path(directory))
            registry = (root/'config/harnesses.yml').read_bytes()
            for version in [True, 1.0]:
                public = project_runtime_copy(frozen, rt.read_bytes(), registry)
                public[PROJECTION]['version'] = version
                with self.assertRaises(RecordError): validate_public_capture(frozen, public, registry)

    def test_public_receipts_cannot_be_projected_again(self):
        with tempfile.TemporaryDirectory() as directory:
            root, harvest, fp, rp, frozen, mp, rt, original = fixture(Path(directory))
            registry = (root/'config/harnesses.yml').read_bytes()
            public = project_runtime_copy(frozen, rt.read_bytes(), registry)
            with self.assertRaises(RecordError):
                project_runtime_copy(frozen, json.dumps(public).encode(), registry)


if __name__ == '__main__':
    unittest.main()
