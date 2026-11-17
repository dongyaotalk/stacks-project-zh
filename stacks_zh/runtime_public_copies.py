"""Project execution captures for publication without changing model identity."""
from __future__ import annotations

import copy
import json
import re
import shlex

from .records import RecordError, sha256_value
from .source_reextractions import byte_hash

PROJECTION = 'execution_capture_projection'
METHOD = 'omit-local-command-paths-v1'


def _capture_identity(frozen, capture, registry_bytes):
    from .harness import parse_harness_registry
    harness = frozen['runtime']['harness']
    identifier, version = harness['id'], harness['version']
    command = parse_harness_registry(registry_bytes.decode()).get(identifier, {}).get('version_command')
    if not command or not version or version.lower() in {'unknown', 'auto', 'unavailable'}:
        raise RecordError('public runtime copy requires a concrete registered Harness')
    command = ' '.join(shlex.split(command))
    argv = capture.get('argv')
    if (type(capture.get('exit_code')) is not int or capture['exit_code'] != 0
            or set(capture) - {'argv', 'stdout', 'stderr', 'exit_code', 'observed_version'}
            or not isinstance(argv, list) or len(argv) < 3
            or argv[:2] != ['make', 'harness-check']
            or any(not isinstance(item, str) for item in argv)):
        raise RecordError('public runtime copy requires the successful original Make capture')
    assignments = [item.partition('=') for item in argv[2:]]
    if (any(not sep or not value or key not in {'HARNESS_ID', 'PYTHON', 'HARVEST_DIR'}
            for key, sep, value in assignments)
            or len({key for key, _, _ in assignments}) != len(assignments)
            or [value for key, _, value in assignments if key == 'HARNESS_ID'] != [identifier]):
        raise RecordError('public runtime copy has unsupported or duplicate arguments')
    stdout = capture.get('stdout')
    if (not isinstance(stdout, str) or capture.get('stderr') != ''
            or re.findall(r'^' + re.escape(identifier) + r': (\S+)$', stdout, re.M) != [version]
            or re.findall(r'^command: (.+)$', stdout, re.M) != [command]):
        raise RecordError('public runtime copy differs from the original version/command output')
    expected_stdout = identifier + ': ' + version + '\ncommand: ' + command + '\n'
    if stdout != expected_stdout:
        python = next((value for key, _, value in assignments if key == 'PYTHON'), None)
        echo, separator, remaining = stdout.partition('\n')
        try:
            echo_argv = shlex.split(echo)
        except ValueError:
            echo_argv = []
        expected_echo = [python, 'stacks_zh.py', 'harness-version', '--harness-id',
                         identifier, '--config', 'config/harnesses.yml']
        if (not isinstance(python, str)
                or not re.match(r'^/(?!/)|^[A-Za-z]:[\\/]', python)
                or not separator or remaining != expected_stdout or echo_argv != expected_echo):
            raise RecordError('public runtime copy cannot omit unaccounted stdout')
    if 'observed_version' in capture and capture['observed_version'] != version:
        raise RecordError('public runtime copy has a contradictory version summary')
    return ['make', 'harness-check', 'HARNESS_ID=' + identifier], expected_stdout


def validate_public_capture(frozen, runtime, registry_bytes):
    projection = runtime.get(PROJECTION)
    required = {'version', 'method', 'source_capture_sha256', 'original_argv_sha256',
                'original_stdout_sha256', 'original_stderr_sha256'}
    if (not isinstance(projection, dict) or set(projection) != required
            or type(projection['version']) is not int or projection['version'] != 1
            or projection['method'] != METHOD
            or any(not isinstance(projection[key], str)
                   or not re.fullmatch(r'sha256:[0-9a-f]{64}', projection[key])
                   for key in required - {'version', 'method'})):
        raise RecordError('malformed public execution-capture projection')
    capture = runtime.get('harness_check', {})
    argv, stdout = _capture_identity(frozen, capture, registry_bytes)
    if (set(capture) - {'argv', 'stdout', 'stderr', 'exit_code', 'observed_version'}
            or capture['argv'] != argv or capture['stdout'] != stdout
            or runtime.get('runtime') != frozen['runtime']):
        raise RecordError('public execution capture changed retained evidence or identity')
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for item in value.values():
                yield from strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)
    if any(re.search(r'(?:^|[\s=])/(?!/)|\b[A-Za-z]:[\\/]', value) for value in strings(runtime)):
        raise RecordError('public execution capture still contains an absolute path')
    # Hashes disclose private captures; they are not proof of replay or generation.
    return dict(version_binding='public-make-capture-projection', capture_projection=METHOD,
                private_capture_replay='not_claimed')


def project_runtime_copy(frozen, original_bytes, registry_bytes):
    from .chapter_relations import _runtime_copy_binding
    original = json.loads(original_bytes)
    if PROJECTION in original:
        raise RecordError('cannot project an already public execution capture')
    _runtime_copy_binding(frozen, original, registry_bytes)
    metadata = original.get('turn_metadata', {})
    expected = frozen['runtime']
    if metadata != {key: value for key, value in [('turn_id', expected['turn_id']),
            ('model', expected['model']['requested_id']), ('effort', expected['reasoning_effort'])]}:
        raise RecordError('public runtime copy differs from actual turn metadata')
    capture = original['harness_check']
    argv, stdout = _capture_identity(frozen, capture, registry_bytes)
    result = copy.deepcopy(original)
    result['harness_check'] = dict(argv=argv, stdout=stdout, stderr='', exit_code=0)
    if 'observed_version' in capture:
        result['harness_check']['observed_version'] = capture['observed_version']
    result[PROJECTION] = dict(version=1, method=METHOD, source_capture_sha256=byte_hash(original_bytes),
        original_argv_sha256=sha256_value(capture['argv']),
        original_stdout_sha256=byte_hash(capture['stdout'].encode()),
        original_stderr_sha256=byte_hash(capture['stderr'].encode()))
    validate_public_capture(frozen, result, registry_bytes)
    _runtime_copy_binding(frozen, result, registry_bytes)
    return result
