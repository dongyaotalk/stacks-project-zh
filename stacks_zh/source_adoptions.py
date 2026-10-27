"""Complete first Git adoption; raw generation and provisional history stay immutable.

This path never creates old candidates or changes a translator-owned field.
Ordinary assembly and all accepted derivation versions keep their guards.
"""
from __future__ import annotations

from .validation_io import isolated_inputs, current_inputs

from .validation_io import read_bytes as _input_bytes, glob_paths as _input_glob, read_text as _input_text

import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from weakref import WeakValueDictionary, finalize

from .current_qa import InputSnapshot
from .derivations import _git_origin_bytes
from .model_corrections import _first_addition_is_immutable
from .records import RecordError, sha256_value, validate_records
from .schema_validation import validate_named_schema
from .source_alignment import Corpus, align_batches, canonical_tokens
from .source_containers import Containers, clean, lower_container, safe_path
from .source_reextractions import byte_hash

VERSION = 'source-adoption-v1'
_REPLAY_TOKEN = object()
_REPLAY_RECEIPTS = WeakValueDictionary()
_REPLAY_BINDINGS = {}
_SOURCE_UNSPECIFIED = object()


class _ValidatedAdoptions(dict):
    """Private same-session replay receipt; never accepts a caller dictionary."""
    def __init__(self, token, root, values, snapshots, harvest=None, *, source=None, implementation=None, reads=None):
        if token is not _REPLAY_TOKEN:
            raise RecordError('adoption receipt requires an actual complete replay')
        super().__init__(values)
        self.root = root
        self.source = source
        self.implementation = implementation
        self.reads = reads
        self.harvest = (harvest if harvest is not None else root.parent / 'stacks-project').resolve()
        dependencies = InputSnapshot(root)
        for snapshot in snapshots:
            dependencies.include_dependencies(snapshot)
        dependencies.assert_unchanged()
        self.snapshots = (dependencies,)
        self.binding = self._binding()

    def _binding(self):
        # Bind every consumed value, including historical disclosure and the
        # effective parsed policy; retaining only current unit/candidate is not enough.
        values = {path + ':' + uid: {
            **value, 'files': {str(p): digest for p, digest in value['files'].items()},
            'policy': {key: sorted(item) if isinstance(item, set) else item
                       for key, item in vars(value['policy']).items()}}
            for (path, uid), value in self.items()}
        dependencies = [dict(root=str(snapshot.root), head=snapshot.head,
            hashes={str(p): digest for p, digest in snapshot.hashes.items()},
            trees={str(path) + ':' + pattern: sorted(str(p) for p in paths)
                   for (path, pattern), paths in snapshot.trees.items()})
            for snapshot in self.snapshots]
        source = self.source
        source_binding = None if source is None else dict(identity=id(source), path=str(source.path),
            exists=source.exists, files=sorted(source.source_files), repository=source.repository,
            head=source.snapshot.head if source.snapshot is not None else None,
            trees={str(path) + ':' + pattern: sorted(str(p) for p in paths)
                   for (path, pattern), paths in source.snapshot.trees.items()}
                  if source.snapshot is not None else {},
            git_paths=sorted(str(p) for p in source.snapshot.git_paths)
                      if source.snapshot is not None and source.snapshot.git_paths is not None else None,
            hashes={str(p): digest for p, digest in source.snapshot.hashes.items()}
                   if source.snapshot is not None else {})
        implementation = self.implementation
        payload = dict(root=str(self.root), harvest=str(self.harvest),
            values=values, dependencies=dependencies, source=source_binding,
            implementation=None if implementation is None else
                (id(implementation), implementation.binding()),
            reads=None if self.reads is None else (id(self.reads), self.reads.binding()))
        # Frozen inputs and policies are shared by all units in a package. Hash
        # their full object graph once per binding check, without expanding the
        # same large input once per unit. No digest survives this call.
        memo, visiting = {}, set()
        def digest(value):
            identity = id(value)
            if identity in memo:
                return memo[identity]
            if identity in visiting:
                raise RecordError('cyclic adoption receipt content')
            visiting.add(identity)
            if isinstance(value, dict):
                node = ['dict', sorted((digest(key), digest(item)) for key, item in value.items())]
            elif isinstance(value, (list, tuple)):
                node = [type(value).__name__, [digest(item) for item in value]]
            elif isinstance(value, (set, frozenset)):
                node = [type(value).__name__, sorted(digest(item) for item in value)]
            elif isinstance(value, Path):
                node = ['path', str(value)]
            elif value is None or isinstance(value, (str, int, float, bool)):
                node = [type(value).__name__, value]
            else:
                raise RecordError(f'unsupported adoption receipt content: {type(value).__name__}')
            result = sha256_value(node)
            visiting.remove(identity)
            memo[identity] = result
            return result
        return digest(payload)

    def assert_unchanged(self, root, harvest=_SOURCE_UNSPECIFIED):
        if _REPLAY_RECEIPTS.get(id(self)) is not self:
            raise RecordError('adoption receipt was not issued by a complete replay')
        if root.resolve() != self.root:
            raise RecordError('adoption replay belongs to another repository')
        # Keep the original one-argument private check compatible; consumers
        # that know their source explicitly bind it, including default None.
        source = (self.harvest if harvest is _SOURCE_UNSPECIFIED else
                  harvest if harvest is not None else root.resolve().parent / 'stacks-project')
        if source.is_symlink() or source.resolve() != self.harvest:
            raise RecordError('adoption replay belongs to another source identity')
        if self.binding != _REPLAY_BINDINGS.get(id(self)) or self.binding != self._binding():
            raise RecordError('adoption replay receipt changed')
        if self.source is None:
            raise RecordError('adoption receipt has no actual source identity')
        if self.implementation is None:
            raise RecordError('adoption receipt has no actual implementation identity')
        if self.reads is None:
            raise RecordError('adoption receipt has no actual input reads')
        self.implementation.assert_valid()
        self.reads.assert_unchanged()
        self.source.assert_valid(self.root, self.harvest)
        for snapshot in self.snapshots:
            snapshot.assert_unchanged()
FIELDS = ('translation', 'allowed_english', 'term_occurrences', 'unknown_terms', 'notes')
POLICIES = ('upstream.lock', 'config/workflow.yml', 'config/macro-policy.yml',
            'config/glossary.yml', 'config/source-terms.json', 'config/style-guide.md',
            'config/models.yml', 'config/harnesses.yml', 'prompts/translator-v2.md',
            'schema/unit.schema.json', 'schema/candidate.schema.json',
            'schema/source-adoption.schema.json', 'schema/source-adoption-input.schema.json',
            'schema/math-text-regions.schema.json', 'schema/math-text-components.schema.json',
            'schema/run-manifest.schema.json', 'schema/translator-output.schema.json',
            'schema/task-scope.schema.json')
EVIDENCE = r'(?:docs/evidence|translation-data/source-adoption-inputs|translation-data/retired/source-adoptions/[A-Za-z0-9._-]+)/[A-Za-z0-9._-]+\.(?:json|jsonl)'


def _time(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise RecordError('source adoption requires timezone-qualified actual times')
    return result


def _schema(value, name):
    errors = validate_named_schema(value, name, name)
    if errors:
        raise RecordError('\n'.join(errors))
    if (name == 'source-adoption-input.schema.json' and value.get('tool_version') == 'source-adoption-input-v1'
            and 'prior_adoptions' in value):
        raise RecordError('v1 schema cannot declare pre-Git adoption revisions')
    if (name == 'source-adoption-input.schema.json'
            and value.get('tool_version') != 'source-adoption-input-v3'
            and 'shared_run_histories' in value):
        raise RecordError('shared run histories require the independent v3 contract')
    if (name == 'source-adoption-input.schema.json'
            and value.get('tool_version') == 'source-adoption-input-v4'
            and ('prior_adoptions' in value
                 or any(batch['prior_attempts'] for batch in value['batches']))):
        raise RecordError('chapter-header v4 cannot declare generation ancestry')


def _relative_input(root, path):
    root = root.absolute()
    path = path if path.is_absolute() else root / path
    relative = path.absolute().relative_to(root).as_posix()
    safe_path(root, relative, EVIDENCE)
    return relative


def _task_scope(frozen, reads, input_entry, *, current):
    from .pr_contract import _scope_manifest
    task = frozen['task']
    if task['issue'] < 1:
        raise RecordError('first-source input must identify the actual claimed task Issue')
    body = '\n'.join([f"task_id: {frozen['task_id']}", f"owner: {task['owner']}",
        f"branch: {task['branch']}", f"source_commit: {frozen['source_commit']}",
        f"scope_manifest: {task['scope_manifest']}",
        f"scope_manifest_sha256: {task['scope_manifest_sha256']}"])
    scope = _scope_manifest(body, {task['scope_manifest']:task['scope_bytes']})
    if current:
        path = safe_path(reads.root, task['scope_manifest'], r'task-scopes/[A-Za-z0-9._-]+\.json')
        if reads.snapshot.read(path) != task['scope_bytes'].encode('utf-8'):
            raise RecordError('first-source task scope drifted since actual generation freeze')
        branch = subprocess.check_output(['git','-C',str(reads.root),'branch','--show-current'], text=True).strip()
        if branch != task['branch']:
            raise RecordError('first-source generation branch differs from its frozen task')
    aid = frozen['adoption_id']
    paths = {input_entry['path'], f'translation-data/source-adoptions/{aid}.json',
             f"translation-data/runs/{frozen['run_id']}.json"}
    for batch in frozen['batches']:
        paths.update((batch['units_path'],batch['candidates_path']))
        for prior in batch['prior_attempts']:
            paths.update(prior[role]['path'] for role in ('units','candidates'))
    for prior in frozen.get('prior_adoptions', []):
        paths.add(prior['record']['path'])
        for output in prior['outputs']:
            paths.update(output[role]['path'] for role in ('units', 'candidates'))
    for prior in frozen.get('shared_run_histories', []):
        paths.add(prior['record']['path'])
        for output in prior['outputs']:
            paths.update(output[role]['path'] for role in ('units', 'candidates'))
    owners = [child for child in scope['data_scopes'] if paths <= set(child['allowed_write_files'])
              and set(frozen['unit_ids']) <= set(child['output_unit_ids'])]
    if len(owners) != 1:
        raise RecordError('complete first-source outputs do not have one exact declared data scope')
    child = owners[0]
    identity = frozen['runtime']['model']
    if (frozen['run_id'] not in child['run_scope'] or child['chapter'] != frozen['chapter']
            or not set(frozen['parent_tags']) <= set(child['parent_tags'])
            or any(value not in child['model_scope'] for value in
                   [identity['record_id'],identity['requested_id'],identity['resolved_id']] if value is not None)):
        raise RecordError('first-source runtime or semantic coordinates escape the frozen task scope')
    return child


def _context_sources(frozen, native):
    """Context hashes bind real complete IR nodes or complete labelled math."""
    from .math_text import delimiter_kind
    observed = set()
    references = set()
    for item in frozen['contexts']:
        value = item['value']
        if value.get('kind') not in {'locked-English-neighbor', 'locked-English-reference', 'locked-English-math-reference'}:
            raise RecordError('first-source context must name actual locked English semantic input')
        location = value['location']
        if not re.fullmatch(r'[A-Za-z0-9_-]+\.tex', location['file']):
            raise RecordError('invalid English context file')
        chapter = location['file'][:-4]
        raw, rows, _ = native.document(chapter)
        start, end = location['byte_start'], location['byte_end']
        if (not 0 <= start < end <= len(raw) or value['source_commit'] != frozen['source_commit']
                or byte_hash(raw[start:end]) != location['fragment_hash']):
            raise RecordError('English context differs from locked Git bytes')
        if 'source_unit' in value:
            matches = [row for row in rows if row['location'] == location
                       and clean(row['unit']) == value['source_unit']]
            if len(matches) != 1 or any(value[key] != matches[0][key] for key in ('owner_tag', 'parent_tag')):
                raise RecordError('English context is not its complete real semantic IR node')
            observed.add((chapter, value['source_unit']['unit_id']))
        elif 'source_math_node' in value:
            if value['source_math_node'].encode('utf-8') != raw[start:end]:
                raise RecordError('math-reference context differs from its real complete node')
            delimiter_kind(value['source_math_node'])
        else:
            raise RecordError('English context lacks a complete source node')
        label = value.get('requested_label')
        if label:
            if native.english.tags.get(label) != value.get('requested_tag'):
                raise RecordError('English context has the wrong requested permanent Tag')
            from .source_reextractions import source_tex
            text = source_tex(value['source_unit']) if 'source_unit' in value else value['source_math_node']
            actual_labels = _source_references(text, native.policy)[1]
            qualified = {name if name in native.english.tags else chapter+'-'+name for name in actual_labels}
            if label not in qualified:
                raise RecordError('English reference context does not contain its actual requested anchor')
            references.add(label)
    return observed, references


def _source_references(text, policy):
    """Read real ref commands, keeping comments, metadata and literals opaque."""
    from .extraction import COMMAND, ENVIRONMENT, Scanner
    scanner, cursor, references, labels = Scanner(text, policy), 0, set(), set()
    while cursor < len(text):
        if text[cursor] == '%':
            cursor = scanner.comment_end(cursor); continue
        command = COMMAND.match(text, cursor)
        if command is None:
            cursor += 1; continue
        name = command[0][1:]
        environment = ENVIRONMENT.match(text, cursor)
        if environment and environment[1] == 'begin' and environment[2] in policy.literal | policy.metadata:
            cursor = scanner.environment_end(cursor); continue
        if name == 'verb':
            opening = command.end() + (text[command.end():command.end()+1] == '*')
            delimiter = text[opening:opening+1]
            closing = text.find(delimiter, opening+1) if delimiter else -1
            if closing < 0:
                raise RecordError('unclosed source context literal')
            cursor = closing+1; continue
        if name in {'ref', 'eqref', 'pageref', 'label'}:
            stop, args = scanner.command_arguments(cursor)
            a, b = args[0]
            (labels if name == 'label' else references).add(text[a+1:b-1])
            cursor = stop; continue
        if name in {'url', 'cite', 'index', 'input', 'bibliography', 'bibliographystyle'}:
            cursor, _ = scanner.command_arguments(cursor, optional=True); continue
        if name == 'href':
            _, args = scanner.command_arguments(cursor, count=2)
            cursor = args[1][0]+1; continue
        cursor = command.end()
    return references, labels


class Reads:
    def __init__(self, root, overrides=None):
        self.root = root
        self.snapshot = InputSnapshot(root)
        self.overrides = overrides or {}

    def output(self, relative):
        if relative in self.overrides:
            return self.read(self.overrides[relative], EVIDENCE)
        return self.snapshot.read(self.root / relative)

    def read(self, entry, pattern=EVIDENCE):
        path = safe_path(self.root, entry['path'], pattern)
        raw = self.output(entry['path']) if entry['path'] in self.overrides else self.snapshot.read(path)
        if byte_hash(raw) != entry['hash']:
            raise RecordError('source adoption file hash mismatch: ' + entry['path'])
        _first_addition_is_immutable(self.root, path)
        return raw

    def json(self, entry, pattern=EVIDENCE):
        return json.loads(self.read(entry, pattern))


def _rows(raw):
    rows = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise RecordError('source adoption requires nonempty object records')
    return rows


def _origin_units(root, origin):
    # Archive is parsed in memory. Never extract paths or execute source TeX.
    names = subprocess.check_output(['git', '-C', str(root), 'ls-tree', '--name-only', origin,
                                     '--', 'translation-data/units'])
    if not names:
        return {}
    raw = subprocess.check_output(['git', '-C', str(root), 'archive', origin, 'translation-data/units'])
    batches = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for item in archive:
            if item.isfile() and item.name.endswith('.jsonl'):
                batches[item.name] = _rows(archive.extractfile(item).read())
    return batches


def fresh_source_corpus(root, harvest, chapter):
    """Apply the accepted alignment window rule to one freshly read Git chapter.

    This is the same non-language frame construction used by verified_inventory:
    adjacent prose/math leaves are excluded, while legacy title/list/noindent
    wrappers retain their actual bytes. No cache or caller span is trusted.
    Other active sources use current policy; each adoption's own source lowering
    is separately replayed under its frozen origin policy.
    """
    from .source_reextractions import source_tex
    native = Containers(root, harvest)
    raw, rows, _ = native.document(chapter)
    windows = []
    for index, row in enumerate(rows):
        start, end = row['location']['byte_start'], row['location']['byte_end']
        if index:
            previous = rows[index-1]
            start = previous['location']['byte_end']
            if previous['owner_tag'] == row['owner_tag'] and row['owner_tag']:
                text = source_tex(previous['unit'])
                leaves = [token for token in canonical_tokens(text, chapter, native.english.tags, native.policy)
                          if token.key[0] in {'text','math','locked'}]
                if leaves:
                    start = previous['location']['byte_start'] + len(text[:leaves[-1].end].encode('utf-8'))
        if index+1 < len(rows):
            following = rows[index+1]
            end = following['location']['byte_start']
            if following['owner_tag'] == row['owner_tag'] and row['owner_tag']:
                text = source_tex(following['unit'])
                leaves = [token for token in canonical_tokens(text, chapter, native.english.tags, native.policy)
                          if token.key[0] in {'text','math','locked'}]
                if leaves:
                    end = following['location']['byte_start'] + len(text[:leaves[0].start].encode('utf-8'))
        window = raw[start:end].decode('utf-8')
        windows.append({**row, '_window_tex':window, '_window_location':{**row['location'],
            'byte_start':start, 'byte_end':end, 'line_start':raw[:start].count(b'\n')+1,
            'line_end':raw[:max(start,end-1)].count(b'\n')+1, 'fragment_hash':byte_hash(window)}})
    return Corpus(windows, native.english.tags, native.policy, source_containers=native), native


def _raw_records(reads, entries, expected_ids, allowed_paths):
    result, paths = {}, set()
    if not entries:
        raise RecordError('source adoption has no actual raw output')
    for entry in entries:
        if entry['path'] not in allowed_paths:
            raise RecordError('actual model output path escapes its exact frozen task scope')
        if entry['path'] in paths:
            raise RecordError('the same raw attempt is declared more than once')
        paths.add(entry['path'])
        rows = _rows(reads.read(entry))
        ids = [row.get('unit_id') for row in rows]
        if len(ids) != len(set(ids)) or not set(ids) <= set(expected_ids):
            raise RecordError('raw output duplicates or escapes complete declared units')
        if 'unit_ids' in entry and ids != entry['unit_ids']:
            raise RecordError('raw attempt unit order differs')
        for row in rows:
            _schema(row, 'translator-output.schema.json')
            result[row['unit_id']] = (row, entry)
    if set(result) != set(expected_ids):
        raise RecordError('raw output lacks a complete model record for every unit')
    return result


def _historical_attempt(reads, attempt, units, output_path, before):
    frozen_units = _rows(reads.read(attempt['units']))
    candidates = _rows(reads.read(attempt['candidates']))
    if frozen_units != units or [c['unit_id'] for c in candidates] != [u['unit_id'] for u in units]:
        raise RecordError('provisional generation must retain the complete ordered unchanged batch')
    if validate_records(units, candidates, units[0]['source_commit']):
        raise RecordError('provisional candidate does not independently pass structural replay')
    runs = {}
    for entry in attempt['runs']:
        run = reads.json(entry, r'translation-data/runs/[A-Za-z0-9._-]+\.json')
        _schema(run, 'run-manifest.schema.json')
        if (entry['path'] != 'translation-data/runs/' + run['run_id'] + '.json'
                or run['run_kind'] != 'translation' or run['run_id'] in runs
                or not _time(run['created_at']) < before):
            raise RecordError('provisional run identity, kind or actual time is invalid')
        runs[run['run_id']] = run
    inputs = {entry['path']: (entry, reads.json(entry)) for entry in attempt['generation_inputs']}
    raw_entries = {entry['path']: entry for entry in attempt['raw_outputs']}
    raw = {path: _rows(reads.read(entry)) for path, entry in raw_entries.items()}
    used_runs, used_inputs, used_raw = set(), set(), set()
    for candidate in candidates:
        _schema(candidate, 'candidate.schema.json')
        if any(candidate.get(k) for k in ('derivation_id', 'model_correction_id', 'unit_group_id', 'source_adoption_id')):
            raise RecordError('provisional first adoption cannot replace accepted or derived history')
        run = runs.get(candidate['run_id'])
        if run is None or candidate['unit_id'] not in run['unit_ids']:
            raise RecordError('provisional candidate has no complete original run')
        used_runs.add(candidate['run_id'])
        context = candidate['context']
        if sha256_value(context) != candidate['context_hash']:
            raise RecordError('provisional context hash differs')
        binding, output = context.get('input_freeze', {}), context.get('model_output', {})
        if binding.get('path') not in inputs or inputs[binding['path']][0] != binding:
            raise RecordError('provisional candidate lacks its exact original input freeze')
        original = inputs[binding['path']][1]
        if (original.get('immutable_generation_freeze') is not True
                or not _time(original['frozen_at']) <= _time(run['created_at'])
                or not all(u in original['complete_target_units'] for u in units)
                or original['run_id'] != run['run_id']):
            raise RecordError('provisional freeze does not bind its complete source and actual run')
        runtime = original['runtime']
        model = runtime['model']
        legacy = isinstance(model, str)
        expected = dict(model_id=model if legacy else model['resolved_id'] or model['requested_id'],
            model_record_id=runtime['model_record_id'] if legacy else model['record_id'],
            model_snapshot=runtime['snapshot'] if legacy else model['snapshot'],
            model_identity_confidence=runtime['identity_confidence'] if legacy else model['identity_confidence'],
            harness_id=runtime['harness_id'] if legacy else runtime['harness']['id'],
            harness_version=runtime['harness_version'] if legacy else runtime['harness']['version'],
            reasoning_effort=runtime['reasoning_effort'])
        if (any(candidate.get(key) != value for key, value in expected.items())
                or context.get('turn_id') != runtime['turn_id']
                or original['policy_revision'] != run['inputs']['policy_revision']):
            raise RecordError('provisional identity/turn/policy differs from its actual generation freeze')
        used_inputs.add(binding['path'])
        if output.get('path') not in raw or output.get('hash') != raw_entries[output['path']]['hash']:
            raise RecordError('provisional candidate lacks its unchanged raw attempt')
        matches = [row for row in raw[output['path']] if row['unit_id'] == candidate['unit_id']]
        if (len(matches) != 1 or sha256_value(matches[0]) != output.get('record_hash')
                or any(matches[0][key] != candidate[key] for key in FIELDS)):
            raise RecordError('provisional five fields differ from actual immutable output')
        used_raw.add(output['path'])
        if candidate.get('publication_status') != 'CANDIDATE' or candidate.get('review_claims'):
            raise RecordError('provisional source adoption cannot inherit approval')
    if set(runs) != used_runs or not used_inputs <= set(inputs) or not used_raw <= set(raw):
        raise RecordError('provisional evidence has orphan run or generation input')
    required_raw = {}
    for run in runs.values():
        attempts = run['inputs'].get('settings', {}).get('raw_attempts', [])
        if not attempts:
            raise RecordError('provisional history lacks its complete original raw-attempt list')
        for entry in attempts:
            required_raw[entry['path']] = entry['hash']
    if {path: entry['hash'] for path, entry in raw_entries.items()} != required_raw:
        raise RecordError('provisional history must retain all original run raw attempts')
    for path, (_, generation) in inputs.items():
        if (generation.get('immutable_generation_freeze') is not True
                or not all(unit in generation['complete_target_units'] for unit in units)
                or generation['run_id'] not in runs):
            raise RecordError('provisional generation input escapes its complete original batch/run')
        revision = generation['policy_revision']
        if not re.fullmatch(r'git:[0-9a-f]{40}', revision):
            raise RecordError('provisional policy origin is not immutable Git')
        for policy_path, policy in generation['policy_inputs'].items():
            payload = _git_origin_bytes(reads.root, revision[4:], policy_path)
            if byte_hash(payload) != policy['hash'] or payload.decode('utf-8') != policy['content']:
                raise RecordError('provisional policy bytes differ from the actual generation input')
        retry = generation.get('retry_of', {})
        if retry:
            if (required_raw.get(retry.get('raw_path')) != retry.get('raw_hash')
                    or retry.get('frozen_path') not in inputs
                    or inputs[retry['frozen_path']][0]['hash'] != retry.get('frozen_hash')):
                raise RecordError('provisional retry input binding differs from its original raw/freeze')
        retry2 = generation.get('earlier_attempts', generation.get('retry2_of', []))
        if generation.get('earlier_attempts') and generation.get('retry2_of'):
            raise RecordError('provisional retry cannot declare two competing predecessor lists')
        for earlier in retry2:
            expected = required_raw.get(earlier['path'])
            if expected is None and earlier['path'] in inputs:
                expected = inputs[earlier['path']][0]['hash']
            if expected is None or earlier['hash'] != expected:
                raise RecordError('provisional retry input binding differs from its full earlier attempts')
            reads.read(earlier)
        continuation = generation.get('generation_continuation_of', {})
        if continuation:
            predecessor = inputs.get(continuation.get('frozen_path'))
            if (predecessor is None or predecessor[0]['hash'] != continuation.get('frozen_hash')
                    or predecessor[1]['runtime'] != continuation.get('prior_runtime')
                    or continuation.get('prior_output_generated') is not False):
                raise RecordError('provisional generation continuation differs from its actual prior input')
        if path not in used_inputs:
            linked = any(value.get('generation_continuation_of', {}).get('frozen_path') == path
                         for _, value in inputs.values())
            retry2_linked = any(earlier['path'] in required_raw for earlier in retry2)
            if retry.get('raw_path') not in required_raw and not linked and not retry2_linked:
                raise RecordError('provisional history includes an unrelated generation input')
    # Original raw attempts may include earlier failures and other complete run
    # batches. They are retained in full; no output is edited or made current.
    return candidates


def _complete_prior_runs(reads, histories):
    """Validate every original run participant before installing replacements.

    A run may also own unchanged batches outside this adoption. Their exact
    original path/order still contributes to its immutable context-hash list.
    """
    prior = {(path, row['unit_id'], row['run_id']): row
             for path, groups in histories.items() for group in groups for row in group}
    for run_id in sorted({key[2] for key in prior}):
        path = safe_path(reads.root, f'translation-data/runs/{run_id}.json',
                         r'translation-data/runs/[A-Za-z0-9._-]+\.json')
        run = json.loads(reads.snapshot.read(path))
        accepted = run['inputs'].get('settings', {}).get('accepted_records', [])
        ids = [entry['unit_id'] for entry in accepted]
        if len(ids) != len(set(ids)) or set(ids) != set(run['unit_ids']):
            raise RecordError('prior run lacks its complete original accepted-record bindings')
        by_path = {}
        for entry in accepted:
            by_path.setdefault(entry['candidate_path'], []).append(entry)
        contexts, seen = [], []
        for relative in sorted(by_path):
            cp = safe_path(reads.root, relative,
                          r'translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl')
            current = _rows(reads.output(relative))
            expected_ids = {entry['unit_id'] for entry in by_path[relative]}
            rows = []
            for row in current:
                key = (relative, row['unit_id'], run_id)
                historical = prior.get(key)
                if historical is not None:
                    rows.append(historical)
                elif row.get('run_id') == run_id:
                    rows.append(row)
            if {row['unit_id'] for row in rows} != expected_ids:
                raise RecordError('prior run is missing a complete current or historical participant')
            units = _rows(reads.output('translation-data/units/' + cp.name))
            if validate_records(units, rows, run['source_commit']):
                raise RecordError('prior run participant fails complete source/structural replay')
            entries = {entry['unit_id']: entry for entry in by_path[relative]}
            for row in rows:
                entry = entries[row['unit_id']]
                output = row['context'].get('model_output', {})
                if (output.get('path') != entry['raw_path']
                        or output.get('record_hash') != entry['record_hash']
                        or row['context_hash'] != sha256_value(row['context'])):
                    raise RecordError('prior run accepted-record/context binding differs')
                raw = _rows(reads.read(dict(path=output['path'], hash=output['hash'])))
                matching = [value for value in raw if value['unit_id'] == row['unit_id']]
                if (len(matching) != 1 or sha256_value(matching[0]) != output['record_hash']
                        or any(row[key] != matching[0][key] for key in FIELDS)):
                    raise RecordError('prior run participant five fields differ from its immutable raw')
                expected = dict(source_commit=run['source_commit'], created_at=run['created_at'],
                    model_record_id=run['model']['record_id'], model_snapshot=run['model']['snapshot'],
                    model_identity_confidence=run['model']['identity_confidence'],
                    harness_id=run['harness']['id'], harness_version=run['harness']['version'],
                    prompt_version=run['inputs']['prompt_version'], glossary_revision=run['inputs']['glossary_revision'])
                if (any(row.get(key) != value for key, value in expected.items())
                        or row['model_id'] not in {run['model']['requested_id'], run['model']['resolved_id']}
                        or row['context'].get('policy_revision') != run['inputs']['policy_revision']):
                    raise RecordError('prior run participant identity differs from its actual manifest')
                contexts.append(row['context_hash']); seen.append(row['unit_id'])
        if len(seen) != len(set(seen)) or set(seen) != set(run['unit_ids']) or contexts != run['inputs']['context_hashes']:
            raise RecordError('prior run full context order/coverage differs from its original manifest')


def _prepare(root, input_entry, harvest=None, *, current=False, overrides=None, visiting=None):
    reads = Reads(root, overrides)
    frozen = reads.json(input_entry)
    _schema(frozen, 'source-adoption-input.schema.json')
    if input_entry['path'] != f"translation-data/source-adoption-inputs/{frozen['adoption_id']}.json":
        raise RecordError('first-source input must use its exact dedicated immutable path')
    _task_scope(frozen, reads, input_entry, current=current)
    reads.snapshot.watch_tree(root / 'translation-data/units')
    origin, source = frozen['origin_commit'], frozen['source_commit']
    if not frozen['batches'] or len(frozen['batches']) > 8:
        raise RecordError('first adoption requires one complete batch or 2-8 adjacent input files')
    if len(frozen['batches']) == 1 and not frozen['outside_preferred_reason']:
        raise RecordError('a single indivisible complete batch requires an explicit exception reason')
    policies = frozen['policies']
    if len(policies) != len(POLICIES) or {e['path'] for e in policies} != set(POLICIES):
        raise RecordError('source adoption must freeze the complete explicit policy set')
    policy_bytes = {}
    for entry in policies:
        payload = _git_origin_bytes(root, origin, entry['path'])
        if byte_hash(payload) != entry['hash']:
            raise RecordError('frozen policy differs from accepted origin: ' + entry['path'])
        policy_bytes[entry['path']] = payload
        if current and reads.snapshot.read(root / entry['path']) != payload:
            raise RecordError('generation policy drifted since its frozen origin')
    if frozen['tool_version'] == 'source-adoption-input-v4':
        for name, version in [('schema/source-adoption-input.schema.json', 'source-adoption-input-v4'),
                              ('schema/source-adoption.schema.json', 'source-adoption-v4')]:
            try:
                allowed = json.loads(policy_bytes[name])['properties']['tool_version']['enum']
            except (ValueError, KeyError, TypeError) as exc:
                raise RecordError('accepted origin lacks the chapter-header contract') from exc
            if version not in allowed:
                raise RecordError('accepted origin does not permit chapter-header adoption')
    if source not in policy_bytes['upstream.lock'].decode():
        raise RecordError('first adoption does not use the accepted English lock')
    seen_contexts = set()
    for item in frozen['contexts']:
        if item['context_id'] in seen_contexts or sha256_value(item['value']) != item['hash']:
            raise RecordError('frozen context is duplicated or has a different hash')
        seen_contexts.add(item['context_id'])
    native = Containers(root, harvest, policy_bytes=policy_bytes['config/macro-policy.yml'])
    if native.english.commit != source:
        raise RecordError('first adoption has a stale English source commit')
    context_nodes, context_references = _context_sources(frozen, native)
    all_units, paths, locations, histories = [], set(), [], {}
    for batch in frozen['batches']:
        up = safe_path(root, batch['units_path'], r'translation-data/units/[A-Za-z0-9._-]+\.jsonl')
        cp = safe_path(root, batch['candidates_path'], r'translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl')
        if up.name != cp.name or cp.parent.name != frozen['runtime']['model_lane'] or {str(up), str(cp)} & paths:
            raise RecordError('first adoption has duplicate or mismatched batch paths')
        paths.update((str(up), str(cp)))
        if _rows(reads.output(batch['units_path'])) != batch['units']:
            raise RecordError('active source units differ from the complete generation freeze')
        previous, batch_units = None, []
        for group in batch['containers']:
            selected = native.select(group['selector'])
            expected = [clean(u) for u in lower_container(selected, native.policy)]
            if selected != group['selected'] or [u['unit_id'] for u in expected] != group['unit_ids']:
                raise RecordError('first adoption container differs from its real complete Git selector')
            start, end = selected['location']['byte_start'], selected['location']['byte_end']
            if previous is not None and start < previous:
                raise RecordError('first adoption container order or boundaries overlap')
            previous = end
            locations.append((selected['selector']['file'][:-4], start, end))
            batch_units.extend(expected)
        if batch_units != batch['units'] or not batch_units:
            raise RecordError('first adoption requires exactly the complete canonical lowering')
        all_units.extend(batch_units)
        old = []
        before = _time(frozen['created_at'])
        for attempt in reversed(batch['prior_attempts']):
            candidates = _historical_attempt(reads, attempt, batch['units'], batch['candidates_path'], before)
            times = {_time(c['created_at']) for c in candidates}
            if len(times) != 1:
                raise RecordError('one complete provisional batch must have one actual generation time')
            before = next(iter(times))
            old.insert(0, candidates)
        histories[batch['candidates_path']] = old
        if current:
            if old:
                if reads.snapshot.read(cp) != reads.read(batch['prior_attempts'][-1]['candidates']):
                    raise RecordError('provisional active candidate changed before its complete replacement')
            elif cp.exists() and frozen['tool_version'] != 'source-adoption-input-v2':
                raise RecordError('first generation cannot overwrite an existing candidate')
        for relative in (batch['units_path'], batch['candidates_path']):
            found = subprocess.run(['git', '-C', str(root), 'ls-tree', origin, '--', relative], capture_output=True)
            if found.returncode or found.stdout:
                raise RecordError('first adoption batch already exists at its accepted origin')
    ids = [u['unit_id'] for u in all_units]
    ordered_locations = sorted(locations)
    if any(left[0] == right[0] and right[1] < left[2]
           for left, right in zip(ordered_locations, ordered_locations[1:])):
        raise RecordError('complete first-source package containers overlap across batches')
    if (frozen['unit_ids'] != ids or frozen['run_id'] != 'run-' + frozen['adoption_id']
            or frozen['chapter'] != all_units[0]['chapter']
            or frozen['parent_tags'] != list(dict.fromkeys(u['parent_tag'] for u in all_units))):
        raise RecordError('first-source complete IDs, coordinates or run differ from the frozen contract')
    if len(ids) != len(set(ids)) or len({u['chapter'] for u in all_units}) != 1:
        raise RecordError('first adoption duplicates units or crosses chapters')
    chapter = all_units[0]['chapter']
    chapter_rows = native.document(chapter)[1]
    from .source_reextractions import source_tex
    needed, internal = set(), set()
    for unit in all_units:
        refs, labels = _source_references(source_tex(unit), native.policy)
        needed.update(label if label in native.english.tags else chapter+'-'+label for label in refs)
        internal.update(label if label in native.english.tags else chapter+'-'+label for label in labels)
    if not needed - internal <= context_references:
        raise RecordError('first-source generation lacks complete referenced English contexts')
    for _, start, end in locations:
        before = [row for row in chapter_rows if row['location']['byte_end'] <= start]
        after = [row for row in chapter_rows if row['location']['byte_start'] >= end]
        neighbors = ([max(before, key=lambda row: row['location']['byte_end'])] if before else [])
        neighbors += ([min(after, key=lambda row: row['location']['byte_start'])] if after else [])
        if any((chapter, row['unit']['unit_id']) not in context_nodes for row in neighbors):
            raise RecordError('first-source generation lacks a complete neighboring English context')
    sections = [row['owner_tag'] for row in chapter_rows if row['unit']['node_kind'] == 'section_title']
    parents = [list(dict.fromkeys(u['parent_tag'] for u in batch['units'])) for batch in frozen['batches']]
    if frozen['tool_version'] == 'source-adoption-input-v4':
        headers = [row for row in chapter_rows if row['unit']['node_kind'] == 'title_title']
        groups = [group for batch in frozen['batches'] for group in batch['containers']]
        if (len(frozen['batches']) != 1 or len(groups) != 1 or len(headers) != 1
                or len(all_units) != 1 or all_units[0]['node_kind'] != 'chapter_title'):
            raise RecordError('chapter-header v4 requires one complete chapter title only')
        header, selector = headers[0], groups[0]['selector']
        if (header != chapter_rows[0]
                or selector['kind'] != 'title_title' or selector['ordinal'] != 1
                or selector['owner_tag'] != header['owner_tag']
                or selector['parent_tag'] != header['parent_tag']
                or header['owner_tag'] != header['parent_tag']
                or parents != [[header['parent_tag']]]):
            raise RecordError('chapter-header v4 requires its real canonical header owner')
    else:
        if any(len(tags) != 1 or tags[0] not in sections for tags in parents):
            raise RecordError('each complete first-source batch must have one actual Section parent')
        ordinals = [sections.index(tags[0]) for tags in parents]
        unique = list(dict.fromkeys(ordinals))
        if ordinals != sorted(ordinals) or unique != list(range(unique[0], unique[0] + len(unique))):
            raise RecordError('first-source package must follow adjacent Section order')
    from .batching import LIMIT_RE, _source_word_count
    limits = {match['key']:int(match['value']) for match in
              LIMIT_RE.finditer(policy_bytes['config/workflow.yml'].decode('utf-8'))}
    low, high = limits['preferred_min_source_words'], limits['preferred_max_source_words']
    if low < 1 or high < low:
        raise RecordError('frozen origin has invalid source package preferences')
    words = sum(_source_word_count(u['source_text']) for u in all_units)
    if not low <= words <= high and not frozen['outside_preferred_reason']:
        raise RecordError('a complete first-source package outside preferred word limits needs a reason')
    old_batches = _origin_units(root, origin)
    old_units = [u for rows in old_batches.values() for u in rows]
    if set(ids) & {u['unit_id'] for u in old_units}:
        raise RecordError('first adoption unit ID already exists in accepted origin')
    others, other_batches = [], {}
    unit_paths = {b['units_path'] for b in frozen['batches']}
    for path in sorted(_input_glob(root / 'translation-data/units', '*.jsonl')):
        if path.relative_to(root).as_posix() not in unit_paths:
            selected_rows = [clean(u) for u in reads.snapshot.jsonl(path) if u.get('chapter') == chapter]
            if selected_rows:
                other_batches['active:' + path.name] = selected_rows
                others.extend(selected_rows)
    if set(ids) & {u['unit_id'] for u in others}:
        raise RecordError('first adoption repeats an active unit ID')
    # Locate all other active and accepted-origin source through the existing
    # owner/proof-aware aligner. Cached caller spans cannot establish absence.
    corpus, alignment_native = fresh_source_corpus(root, harvest, chapter)
    relevant = {**other_batches, **{'origin:' + path: [u for u in group if u.get('chapter') == chapter]
                for path, group in old_batches.items() if any(u.get('chapter') == chapter for u in group)}}
    matches, _ = align_batches(relevant, corpus)
    for entry in matches:
        if entry['status'] not in {'BYTE_EXACT', 'PRESENTATION_EQUIVALENT'} or entry.get('extractor_state') != 'READY':
            raise RecordError('cannot prove first-source disjointness: ' + entry['unit_id'])
        span = entry['location']
        for _, start, end in locations:
            a, b = max(start, span['byte_start']), min(end, span['byte_end'])
            if a < b and native.document(chapter)[0][a:b].strip(b' \t\r\n'):
                raise RecordError('first adoption overlaps accepted or other active source')
    native.assert_unchanged()
    alignment_native.assert_unchanged()
    complete_histories = dict(histories)
    if frozen['tool_version'] == 'source-adoption-input-v3':
        shared = _shared_run_histories(root, frozen, reads, harvest, current, visiting or set(), histories)
        complete_histories.update(shared)
    _complete_prior_runs(reads, complete_histories)
    if frozen['tool_version'] == 'source-adoption-input-v2':
        prior_histories = _prior_adoptions(root, frozen, reads, harvest, current, visiting or set())
        for path, groups in prior_histories.items():
            histories[path].extend(groups)
    reads.snapshot.assert_unchanged()
    return frozen, reads, native, histories


def _shared_run_histories(root, frozen, reads, harvest, current, visiting, histories):
    """Verify complete external adoption records solely as original run witnesses."""
    identifier = frozen['adoption_id']
    if identifier in visiting:
        raise RecordError('cyclic shared ordinary-run history')
    visiting = visiting | {identifier}
    if (frozen.get('prior_adoptions') or not frozen['shared_run_histories']
            or any(not b['prior_attempts'] for b in frozen['batches'])):
        raise RecordError('v3 requires nonempty shared history and ordinary batch ancestors')
    required_runs = {c['run_id'] for groups in histories.values() for group in groups for c in group}
    if not required_runs:
        raise RecordError('shared history has no original ordinary run to validate')
    result, seen = {}, set()
    for witness in frozen['shared_run_histories']:
        record = reads.json(witness['record'], r'translation-data/source-adoptions/[A-Za-z0-9._-]+\.json')
        old_id = record['adoption_id']
        if (old_id in visiting or old_id in seen
                or witness['record']['path'] != f'translation-data/source-adoptions/{old_id}.json'
                or not _time(record['created_at']) < _time(frozen['created_at'])):
            raise RecordError('invalid, duplicate or cyclic shared adoption witness')
        seen.add(old_id)
        if len(record['outputs']) != len(witness['outputs']):
            raise RecordError('shared witness requires all complete original output batches')
        # The witness's original run also includes this new adoption's ordinary
        # ancestors. Supply their fully validated snapshots while replaying it.
        overrides = dict(reads.overrides)
        for batch in frozen['batches']:
            for attempt in batch['prior_attempts']:
                overrides[batch['candidates_path']] = attempt['candidates']
        for original, saved in zip(record['outputs'], witness['outputs'], strict=True):
            cp = original['candidates']['path']
            if cp in histories or cp in result:
                raise RecordError('shared witness overlaps new outputs or another witness')
            for role in ('units', 'candidates'):
                entry = saved[role]
                expected = (f'translation-data/retired/source-adoptions/{identifier}-shared-'
                            f'{old_id}-{Path(original[role]["path"]).stem}/{role}.jsonl')
                if entry['path'] != expected or entry['hash'] != original[role]['hash']:
                    raise RecordError('shared snapshot is not the complete original output bytes')
                reads.read(entry)
                overrides[original[role]['path']] = entry
        old_frozen, old_reads, native, old_histories = _prepare(root, record['input'], harvest,
            overrides=overrides, visiting=visiting)
        expected, _ = _replay_record(record, old_frozen, old_reads, native)
        used = False
        for cp, rows in expected.items():
            groups = [*old_histories[cp], rows]
            relevant = [group for group in groups if any(c['run_id'] in required_runs for c in group)]
            if relevant:
                result[cp] = relevant
                used = True
        if not used:
            raise RecordError('shared adoption witness has no required ordinary run participant')
        native.assert_unchanged()
        old_reads.snapshot.assert_unchanged()
        for path in old_reads.snapshot.hashes:
            reads.snapshot.read(path)
    return result


def _first_commit(root, relative):
    commits = subprocess.check_output(['git', '-C', str(root), 'log', '--diff-filter=A',
                                      '--format=%H', '--reverse', 'HEAD', '--', relative], text=True).splitlines()
    return commits[0] if commits else None


def _prior_adoptions(root, frozen, reads, harvest, current, visiting):
    """Replay complete pre-Git adoptions through their untouched output snapshots."""
    identifier = frozen['adoption_id']
    if identifier in visiting:
        raise RecordError('cyclic pre-Git source-adoption history')
    visiting = visiting | {identifier}
    batches = {b['candidates_path']: b for b in frozen['batches']}
    if not frozen['prior_adoptions']:
        raise RecordError('v2 requires nonempty complete prior adoptions')
    if any(b['prior_attempts'] for b in batches.values()):
        raise RecordError('v2 prior adoption already owns all ordinary generation ancestry')
    covered, histories = set(), {}
    current_commit = _first_commit(root, f'translation-data/source-adoption-inputs/{identifier}.json')
    for prior in frozen['prior_adoptions']:
        record = reads.json(prior['record'], r'translation-data/source-adoptions/[A-Za-z0-9._-]+\.json')
        if prior['record']['path'] != f'translation-data/source-adoptions/{record["adoption_id"]}.json':
            raise RecordError('prior adoption record filename differs from its actual ID')
        prior_commit = _first_commit(root, prior['record']['path'])
        if (record['adoption_id'] in visiting or not _time(record['created_at']) < _time(frozen['created_at'])
                or current and prior_commit is not None
                or not current and prior_commit is not None and prior_commit != current_commit):
            raise RecordError('prior adoption must be complete actual pre-Git history with strict time order')
        if len(record['outputs']) != len(prior['outputs']):
            raise RecordError('prior adoption requires every complete original output batch')
        overrides = dict(reads.overrides)
        for original, archive in zip(record['outputs'], prior['outputs'], strict=True):
            path = original['candidates']['path']
            if path in covered or path not in batches:
                raise RecordError('prior adoption outputs overlap or escape the complete new generation')
            covered.add(path)
            for role in ('units', 'candidates'):
                output_commit = _first_commit(root, original[role]['path'])
                if (current and output_commit is not None or not current and output_commit is not None
                        and output_commit != current_commit):
                    raise RecordError('prior adoption output already had an independent Git adoption')
                entry = archive[role]
                expected_path = (f'translation-data/retired/source-adoptions/{identifier}-'
                                 f'{record["adoption_id"]}-{Path(original[role]["path"]).stem}/{role}.jsonl')
                if entry['path'] != expected_path or entry['hash'] != original[role]['hash']:
                    raise RecordError('prior adoption snapshot is not its complete exact original bytes')
                reads.read(entry)
                overrides[original[role]['path']] = entry
        old_frozen, old_reads, native, old_histories = _prepare(root, record['input'], harvest,
            overrides=overrides, visiting=visiting)
        expected, manifest = _replay_record(record, old_frozen, old_reads, native)
        for path, rows in expected.items():
            old_batch = next(b for b in old_frozen['batches'] if b['candidates_path'] == path)
            if old_batch['units'] != batches[path]['units'] or old_batch['units_path'] != batches[path]['units_path']:
                raise RecordError('pre-Git adoption revision changes source or complete segmentation')
            if current and reads.snapshot.read(root / path) != reads.read(overrides[path]):
                raise RecordError('prior adoption active bytes drifted before complete replacement')
            histories[path] = [*old_histories[path], rows]
        native.assert_unchanged()
        old_reads.snapshot.assert_unchanged()
        for path in old_reads.snapshot.hashes:
            reads.snapshot.read(path)
    if covered != set(batches):
        raise RecordError('v2 must regenerate every unit of every complete previous adoption')
    return histories


def _generated(frozen, raw, input_entry):
    from .workflow import _candidate_records
    identity = frozen['runtime']
    model, harness = identity['model'], identity['harness']
    if (model['identity_confidence'] == 'unknown'
            or harness['version'].lower() in {'auto', 'unknown', 'unavailable'}
            or not (model['resolved_id'] or model['requested_id'])):
        raise RecordError('first adoption requires actual observed model and Harness identity')
    run_id = 'run-' + frozen['adoption_id']
    result = {}
    for batch in frozen['batches']:
        rows = _candidate_records(batch['units'], {uid: row for uid, (row, _) in raw.items()},
            frozen['source_commit'], model['resolved_id'] or model['requested_id'],
            identity['model_lane'], identity['reasoning_effort'], 'translator-v2',
            'git:' + frozen['origin_commit'], 'git:' + frozen['origin_commit'],
            frozen['created_at'], harness['id'], harness['version'], model['record_id'], run_id,
            model['snapshot'], model['identity_confidence'])
        for candidate in rows:
            row, entry = raw[candidate['unit_id']]
            candidate['source_adoption_id'] = frozen['adoption_id']
            candidate['context'].update(source_adoption_id=frozen['adoption_id'],
                input_freeze=input_entry, turn_id=identity['turn_id'],
                generation_contexts=frozen['contexts'], prior_generations=batch['prior_attempts'],
                model_output=dict(path=entry['path'], hash=entry['hash'], record_hash=sha256_value(row)))
            if frozen['tool_version'] == 'source-adoption-input-v2':
                candidate['context']['prior_source_adoptions'] = frozen['prior_adoptions']
            if frozen['tool_version'] == 'source-adoption-input-v3':
                candidate['context']['shared_run_histories'] = frozen['shared_run_histories']
            candidate['context_hash'] = sha256_value(candidate['context'])
        result[batch['candidates_path']] = rows
    manifest = dict(schema_version=1, run_id=run_id, run_kind='translation', task_id=frozen['task_id'],
        source_commit=frozen['source_commit'], unit_ids=[u['unit_id'] for b in frozen['batches'] for u in b['units']],
        harness=harness, model=model, inputs=dict(prompt_version='translator-v2',
            policy_revision='git:' + frozen['origin_commit'], glossary_revision='git:' + frozen['origin_commit'],
            context_hashes=[c['context_hash'] for path in sorted(result) for c in result[path]],
            settings=dict(reasoning_effort=identity['reasoning_effort'], turn_id=identity['turn_id'],
                          source_adoption_id=frozen['adoption_id'], input_freeze=input_entry)),
        created_at=frozen['created_at'], replayable=identity['replayable'], status='recorded',
        notes=['Complete first source adoption; candidate only, no review or publication approval.'])
    _schema(manifest, 'run-manifest.schema.json')
    for rows in result.values():
        for candidate in rows:
            _schema(candidate, 'candidate.schema.json')
    return result, manifest


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def _jsonl_bytes(rows):
    return ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows).encode('utf-8')


def _install(root, payloads, unchanged):
    """Stage all bytes, check again, and roll back every installed file on failure."""
    build = root / 'build'
    build.mkdir(exist_ok=True)
    previous = {path: _input_bytes(path) if path.exists() else None for path in payloads}
    with tempfile.TemporaryDirectory(prefix='.source-adoption-', dir=build) as folder:
        staged = {}
        for ordinal, (path, raw) in enumerate(payloads.items()):
            temp = Path(folder) / str(ordinal)
            temp.write_bytes(raw)
            staged[path] = temp
        unchanged()
        installed = []
        try:
            for path, temp in staged.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                os.replace(temp, path)
                installed.append(path)
        except BaseException:
            for path in reversed(installed):
                if previous[path] is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(previous[path])
            raise


def _assemble_source_adoption(root: Path, input_path: Path, raw_paths: list[Path],
                              harvest: Path | None = None):
    """Validate a complete actual generation, then install one immutable adoption."""
    from .current_qa import CurrentSourceQA, validate_current_records
    from .harness import resolve_harness
    from .provenance import _parse_registry_section, _registry_scalar
    relative = _relative_input(root, input_path)
    raw_relative = [_relative_input(root, path) for path in raw_paths]
    root = root.resolve()
    entry = dict(path=relative, hash=byte_hash(_input_bytes(root / relative)))
    frozen, reads, native, _ = _prepare(root, entry, harvest, current=True)
    identity = frozen['runtime']
    observed = resolve_harness(identity['harness']['id'], root / 'config/harnesses.yml')
    if observed.version != identity['harness']['version']:
        raise RecordError('Harness changed between actual generation freeze and assembly')
    records = _parse_registry_section(_input_text(root / 'config/models.yml'), 'model_records')
    lanes = _parse_registry_section(_input_text(root / 'config/models.yml'), 'lanes')
    registered = records.get(identity['model']['record_id'])
    lane = lanes.get(identity['model_lane'])
    harnesses = _parse_registry_section(_input_text(root / 'config/harnesses.yml'), 'harnesses')
    if harnesses.get(identity['harness']['id'], {}).get('adapter_version') != identity['harness']['adapter_version']:
        raise RecordError('first adoption Harness adapter differs from registry')
    if registered is None or lane is None:
        raise RecordError('first adoption model identity or lane is unregistered')
    if any(expected is not None and _registry_scalar(identity['model'].get(key)) != expected
           for key, expected in registered.items() if key in identity['model']):
        raise RecordError('first adoption model identity differs from registry')
    for key, actual in [('model_id', identity['model']['resolved_id'] or identity['model']['requested_id']),
                        ('model_record_id', identity['model']['record_id']),
                        ('harness_id', identity['harness']['id']), ('prompt_version', 'translator-v2')]:
        if lane.get(key) != actual:
            raise RecordError('first adoption runtime does not match its registered lane')
    attempts = []
    scope = _task_scope(frozen, reads, entry, current=False)
    for relative in raw_relative:
        if relative not in scope['allowed_write_files']:
            raise RecordError('actual model output path escapes its exact frozen task scope')
        payload = reads.snapshot.read(root / relative)
        attempts.append(dict(path=relative, hash=byte_hash(payload), unit_ids=[r['unit_id'] for r in _rows(payload)]))
    units = [u for b in frozen['batches'] for u in b['units']]
    raw = _raw_records(reads, attempts, [u['unit_id'] for u in units], scope['allowed_write_files'])
    candidates, manifest = _generated(frozen, raw, entry)
    qa = CurrentSourceQA(root, harvest, snapshot=reads.snapshot)
    for batch in frozen['batches']:
        errors = validate_current_records(batch['units'], candidates[batch['candidates_path']],
            frozen['source_commit'], qa.catalog, native.english.tags, qa.approved)
        if errors:
            raise RecordError('first adoption current QA rejected:\n' + '\n'.join(errors))
    aid = frozen['adoption_id']
    record_path = safe_path(root, f'translation-data/source-adoptions/{aid}.json',
                            r'translation-data/source-adoptions/[A-Za-z0-9._-]+\.json')
    run_path = safe_path(root, f"translation-data/runs/{manifest['run_id']}.json",
                         r'translation-data/runs/[A-Za-z0-9._-]+\.json')
    if record_path.exists() or run_path.exists():
        raise RecordError('first adoption cannot overwrite an existing record or actual run')
    payloads, outputs = {}, []
    for batch in frozen['batches']:
        path = root / batch['candidates_path']
        payloads[path] = _jsonl_bytes(candidates[batch['candidates_path']])
        outputs.append(dict(units=dict(path=batch['units_path'],
            hash=byte_hash(reads.snapshot.read(root / batch['units_path']))),
            candidates=dict(path=batch['candidates_path'], hash=byte_hash(payloads[path]))))
    payloads[run_path] = _json_bytes(manifest)
    record = dict(schema_version=1, tool_version=frozen['tool_version'].replace('-input', ''), adoption_id=aid,
        origin_commit=frozen['origin_commit'], source_commit=frozen['source_commit'],
        created_at=frozen['created_at'], input=entry, raw_attempts=attempts,
        unit_ids=manifest['unit_ids'], chapter=units[0]['chapter'],
        parent_tags=list(dict.fromkeys(u['parent_tag'] for u in units)), run_id=manifest['run_id'],
        run=dict(path=run_path.relative_to(root).as_posix(), hash=byte_hash(payloads[run_path])), outputs=outputs)
    _schema(record, 'source-adoption.schema.json')
    payloads[record_path] = _json_bytes(record)

    def unchanged():
        qa.assert_unchanged()
        native.assert_unchanged()
        reads.snapshot.assert_unchanged()
        if record_path.exists() or run_path.exists():
            raise RecordError('first adoption output appeared during validation')
    _install(root, payloads, unchanged)
    return record


def assemble_source_adoption(root: Path, input_path: Path, raw_paths: list[Path],
                             harvest: Path | None = None):
    """Reject malformed structured input before any candidate installation."""
    try:
        return _assemble_source_adoption(root, input_path, raw_paths, harvest)
    except (KeyError, TypeError, IndexError, UnicodeError) as exc:
        raise RecordError('invalid complete first-source adoption input: ' + str(exc)) from exc


@isolated_inputs
def load_repository_source_adoptions(root: Path, harvest: Path | None = None):
    """Replay all complete active first-adoption records, including every prior model."""
    root = root.resolve()
    adopted, errors, owned_ids = {}, [], set()
    directory = root / 'translation-data/source-adoptions'
    history = subprocess.run(['git', '-C', str(root), 'log', '--diff-filter=A', '--format=',
                              '--name-only', 'HEAD', '--', 'translation-data/source-adoptions'],
                             capture_output=True, text=True)
    retired = root / 'translation-data/retired/source-adoptions'
    if (not directory.exists() and not retired.exists() and not history.stdout.strip()
            and history.returncode):
        # Preserve the ordinary, adoption-free Python API for non-Git inputs.
        # A live repository session requires HEAD and never consumes this dict.
        return {}, []
    try:
        from .repository_validation import _SourceIdentity, _ImplementationIdentity
        implementation = _ImplementationIdentity()
        reads_session = current_inputs()
        reads_session.seed_implementation(implementation)
        reads_session.watch_root(root)
        source = _SourceIdentity(root, harvest)
        inventory = InputSnapshot(root)
        inventory.watch_tree(root / 'translation-data/source-adoptions')
        inventory.watch_tree(root / 'translation-data/retired/source-adoptions')
    except (OSError, ValueError) as exc:
        return {}, [str(exc)]
    snapshots = [inventory]
    if history.returncode and directory.exists():
        errors.append('first-adoption immutability requires readable Git history')
    for relative in set(history.stdout.splitlines()) - {''}:
        if not (root / relative).is_file():
            errors.append(relative + ': immutable first-adoption record disappeared')
    for path in sorted(_input_glob(directory, '*')):
        if path.suffix != '.json':
            errors.append(str(path) + ': unsupported first-adoption evidence')
    consumed = {}
    graph = {}
    for path in sorted(_input_glob(directory, '*.json')):
        try:
            record = json.loads(_input_bytes(path))
            frozen = json.loads(_input_bytes(root / record['input']['path']))
            graph[path.relative_to(root).as_posix()] = [p['record']['path'] for p in frozen.get('prior_adoptions', [])]
            for prior in frozen.get('prior_adoptions', []):
                relative = prior['record']['path']
                if relative in consumed:
                    raise RecordError('prior adoption has multiple current successors')
                consumed[relative] = path
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(str(path) + ': ' + str(exc))
    def visit(relative, chain):
        if relative in chain:
            raise RecordError('cyclic pre-Git source-adoption history')
        if relative not in graph:
            raise RecordError('prior adoption record disappeared')
        for prior in graph[relative]:
            visit(prior, chain | {relative})
    try:
        for relative in graph:
            visit(relative, set())
    except RecordError as exc:
        return {}, [*errors, str(exc)]
    shared_overrides = {}
    def replay_order(path):
        try:
            record = json.loads(_input_bytes(path))
            return record.get('tool_version') != 'source-adoption-v3', path.name
        except (OSError, ValueError):
            return True, path.name
    for path in sorted(_input_glob(directory, '*.json'), key=replay_order):
        if path.relative_to(root).as_posix() in consumed:
            continue
        try:
            safe_path(root, path.relative_to(root).as_posix(),
                      r'translation-data/source-adoptions/[A-Za-z0-9._-]+\.json')
            record = json.loads(_input_bytes(path))
            _schema(record, 'source-adoption.schema.json')
            if path.stem != record['adoption_id']:
                raise RecordError('first-adoption filename differs from its ID')
            _first_addition_is_immutable(root, path)
            input_value = json.loads(_input_bytes(root / record['input']['path']))
            own_paths = {b[role] for b in input_value['batches']
                         for role in ('units_path', 'candidates_path')}
            frozen, reads, native, histories = _prepare(root, record['input'], harvest,
                overrides={p:e for p,e in shared_overrides.items() if p not in own_paths})
            reads.snapshot.read(path)
            units = [u for b in frozen['batches'] for u in b['units']]
            expected, manifest = _replay_record(record, frozen, reads, native)
            for batch, output in zip(frozen['batches'], record['outputs'], strict=True):
                actual = _rows(reads.read(output['candidates'], r'translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl'))
                for index, candidate in enumerate(actual):
                    key = (batch['candidates_path'], candidate['unit_id'])
                    if key in adopted or candidate['unit_id'] in owned_ids:
                        raise RecordError('first source is claimed by multiple adoption records')
                    owned_ids.add(candidate['unit_id'])
                    adopted[key] = dict(record=record, input=frozen, unit=batch['units'][index],
                        candidate=candidate, prior_candidates=[group[index] for group in histories[batch['candidates_path']]],
                        policy=native.policy, files=dict(reads.snapshot.hashes))
            native.assert_unchanged()
            reads.snapshot.assert_unchanged()
            snapshots.append(reads.snapshot)
            if frozen['tool_version'] == 'source-adoption-input-v3':
                for batch in frozen['batches']:
                    relative = batch['candidates_path']
                    entry = batch['prior_attempts'][-1]['candidates']
                    if relative in shared_overrides and shared_overrides[relative] != entry:
                        raise RecordError('shared ordinary history has competing snapshots')
                    shared_overrides[relative] = entry
        except (OSError, ValueError, KeyError, TypeError, IndexError, subprocess.SubprocessError) as exc:
            errors.append(str(path) + ': ' + str(exc))
    used = {path for snapshot in snapshots[1:] for path in snapshot.hashes}
    retired = root / 'translation-data/retired/source-adoptions'
    for path in _input_glob(retired, '*', recursive=True):
        if path.is_file() and path not in used:
            errors.append(str(path) + ': orphaned source-adoption history snapshot')
    inventory.assert_unchanged()
    if errors:
        return adopted, errors
    source.assert_valid(root, harvest)
    implementation.assert_valid()
    result = _ValidatedAdoptions(_REPLAY_TOKEN, root, adopted, snapshots, harvest,
                                 source=source, implementation=implementation, reads=reads_session)
    _REPLAY_RECEIPTS[id(result)] = result
    _REPLAY_BINDINGS[id(result)] = result.binding
    finalize(result, _REPLAY_BINDINGS.pop, id(result), None)
    return result, []


def _replay_record(record, frozen, reads, native):
    _schema(record, 'source-adoption.schema.json')
    expected_version = frozen['tool_version'].replace('-input', '')
    if record['tool_version'] != expected_version:
        raise RecordError('first-adoption record/input version differs')
    for key in ('adoption_id', 'origin_commit', 'source_commit', 'created_at'):
        if frozen[key] != record[key]:
            raise RecordError('first-adoption record differs from its immutable input')
    units = [u for b in frozen['batches'] for u in b['units']]
    scope = _task_scope(frozen, reads, record['input'], current=False)
    raw = _raw_records(reads, record['raw_attempts'], [u['unit_id'] for u in units], scope['allowed_write_files'])
    expected, manifest = _generated(frozen, raw, record['input'])
    if (record['unit_ids'] != manifest['unit_ids'] or record['run_id'] != manifest['run_id']
            or record['chapter'] != units[0]['chapter']
            or record['parent_tags'] != list(dict.fromkeys(u['parent_tag'] for u in units))):
        raise RecordError('first-adoption declared complete scope differs from actual source/run')
    if reads.json(record['run'], r'translation-data/runs/[A-Za-z0-9._-]+\.json') != manifest:
        raise RecordError('first-adoption actual run differs from complete replay')
    if len(record['outputs']) != len(frozen['batches']):
        raise RecordError('first-adoption output batch coverage differs')
    for batch, output in zip(frozen['batches'], record['outputs'], strict=True):
        if output['units']['path'] != batch['units_path'] or output['candidates']['path'] != batch['candidates_path']:
            raise RecordError('first-adoption output order/paths differ')
        if _rows(reads.read(output['units'], r'translation-data/units/[A-Za-z0-9._-]+\.jsonl')) != batch['units']:
            raise RecordError('first-adoption source units differ from complete replay')
        actual = _rows(reads.read(output['candidates'], r'translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl'))
        if actual != expected[batch['candidates_path']]:
            raise RecordError('first-adoption candidate differs from all five fields or metadata replay')
    return expected, manifest


def source_adoption_provenance_hash(root, candidate):
    """Bind a decision after complete repository provenance has actually passed.

    Like the existing composite binding, this hash is not a source-validation
    entry point. The record and frozen input contain the complete file hashes.
    """
    root = root.resolve()
    identifier = candidate['source_adoption_id']
    path = safe_path(root, f'translation-data/source-adoptions/{identifier}.json',
                     r'translation-data/source-adoptions/[A-Za-z0-9._-]+\.json')
    _first_addition_is_immutable(root, path)
    reads = Reads(root)
    record = json.loads(reads.snapshot.read(path))
    _schema(record, 'source-adoption.schema.json')
    frozen = reads.json(record['input'])
    _schema(frozen, 'source-adoption-input.schema.json')
    matches = [row for output in record['outputs']
               for row in _rows(reads.read(output['candidates'],
                   r'translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl'))
               if row == clean(candidate)]
    if len(matches) != 1:
        raise RecordError('decision has no unique validated first source adoption')
    reads.snapshot.assert_unchanged()
    return sha256_value(dict(candidate=clean(candidate), record=record, input=frozen))
