"""Full provisional v4 replay before its first Git adoption, never a waiver."""
from __future__ import annotations

from .validation_io import read_bytes as _input_bytes, glob_paths as _input_glob, read_text as _input_text

import copy
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .model_corrections import _first_addition_is_immutable, _safe_path
from .records import RecordError, load_jsonl
from .schema_validation import validate_named_schema


def _read(root: Path, entry: dict, pattern: str) -> tuple[Path, bytes]:
    from .derivations import byte_hash
    path = _safe_path(root, entry['path'], pattern)
    payload = _input_bytes(path)
    if byte_hash(payload) != entry['hash']:
        raise RecordError('pre-adoption snapshot hash mismatch')
    _first_addition_is_immutable(root, path)
    return path, payload


def _first_adoption(root: Path, origin: str, record_path: str, manifest_path: str) -> None:
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True)
    if git('merge-base', '--is-ancestor', origin, 'HEAD').returncode:
        raise RecordError('pre-adoption origin must be a reachable ancestor')
    # rev-parse on the tree distinguishes absence from a broken Git repository.
    tree = git('ls-tree', origin, '--', record_path)
    if tree.returncode or tree.stdout:
        raise RecordError('pre-adoption derivation must be absent at its origin')
    history = git('log', '--reverse', '--diff-filter=A', '--format=%H', 'HEAD', '--', record_path)
    if history.returncode:
        raise RecordError('pre-adoption requires readable Git history')
    additions = history.stdout.decode().splitlines()
    if additions:
        manifest = json.loads(_input_text(root / manifest_path))
        paths = [manifest_path, *(entry['path'] for entry in manifest['files'].values())]
        for relative in paths:
            original = git('show', f'{additions[0]}:{relative}')
            if original.returncode or original.stdout != _input_bytes(root / relative):
                raise RecordError('pre-adoption evidence must accompany the first derivation addition')


def _prior_run_files(root: Path, evidence: dict) -> dict[str, str]:
    from .derivations import byte_hash
    record = evidence['record']
    paths = [f"translation-data/model-corrections/{record['correction_id']}.json",
             f"translation-data/runs/{record['run_id']}.json",
             *(record['files'][role]['path'] for role in ('units', 'candidates'))]
    return {path: byte_hash(_input_bytes(root / path)) for path in paths}


def validate_pre_adoption_replays(
    root: Path, records: dict, cache: dict, corrections: dict, used_corrections: set,
    restorations: dict, tags: dict | None,
) -> tuple[set, list[str]]:
    """Consume predecessor raw only after complete independent historical replay."""
    from .derivations import clean, jsonl_bytes, replay_derivation
    consumed, errors, claimed, seen_files = set(), [], set(), set()
    folder = root / 'translation-data/pre-adoption-replays'
    for path in sorted(_input_glob(folder, '*')):
        if path.suffix != '.json':
            errors.append(f'{path}: unsupported pre-adoption evidence file')
    for path in sorted(_input_glob(folder, '*.json')):
        try:
            manifest = json.loads(_input_text(path, encoding='utf-8'))
            schema_errors = validate_named_schema(manifest, 'pre-adoption-replay.schema.json', str(path))
            if schema_errors:
                raise RecordError('\n'.join(schema_errors))
            identifier = manifest['replay_id']
            _safe_path(root, path.relative_to(root).as_posix(),
                       rf'translation-data/pre-adoption-replays/{re.escape(identifier)}\.json')
            _first_addition_is_immutable(root, path)
            did = manifest['current_derivation_id']
            current = records.get(did)
            if did in claimed or did not in cache or current is None:
                raise RecordError('pre-adoption needs one complete validated current batch')
            claimed.add(did)
            if (current['tool']['version'] != '4' or current.get('previous_derivation_id')
                    or manifest['origin_commit'] != current['origin_commit']
                    or manifest['source_commit'] != current['source_commit']):
                raise RecordError('pre-adoption only supports the same initial v4 source/origin')
            snapshots, payloads = {}, {}
            for role, name in [('derivation', 'derivation.json'), ('units', 'units.jsonl'), ('candidates', 'candidates.jsonl')]:
                entry = manifest['files'][role]
                snapshot, payload = _read(root, entry,
                    rf'translation-data/retired/pre-adoption-replays/{re.escape(identifier)}/{re.escape(name)}')
                snapshots[role], payloads[role] = snapshot, payload
                seen_files.add(entry['path'])
            _first_adoption(root, manifest['origin_commit'], f'translation-data/derivations/{did}.json',
                            path.relative_to(root).as_posix())
            prior = json.loads(payloads['derivation'])
            old_units = [clean(row) for row in load_jsonl(snapshots['units'])]
            old_candidates = [clean(row) for row in load_jsonl(snapshots['candidates'])]
            prior_id, next_id = manifest['predecessor_correction_id'], manifest['successor_correction_id']
            if prior_id == next_id:
                raise RecordError('pre-adoption requires a distinct actual successor correction')
            equivalent = copy.deepcopy(prior)
            for group in equivalent['unit_groups']:
                if group['model_correction_id'] != prior_id:
                    raise RecordError('pre-adoption must cover every prior group')
                group['model_correction_id'] = next_id
            equivalent['files']['output_candidates']['hash'] = current['files']['output_candidates']['hash']
            if equivalent != current:
                raise RecordError('pre-adoption changes source, inputs, segmentation or identity')
            if (prior['files']['output_units']['hash'] != manifest['files']['units']['hash']
                    or prior['files']['output_candidates']['hash'] != manifest['files']['candidates']['hash']):
                raise RecordError('pre-adoption output bytes differ from the prior record')
            ids = [uid for group in prior['unit_groups'] for uid in group['output_unit_ids']]
            if (ids != manifest['output_unit_ids'] or len(set(ids)) != len(ids)
                    or [u['unit_id'] for u in old_units] != ids
                    or [c['unit_id'] for c in old_candidates] != ids
                    or jsonl_bytes(cache[did][0]) != payloads['units']):
                raise RecordError('pre-adoption requires exact complete ordered outputs and unchanged source')
            inputs = [[clean(row) for row in load_jsonl(root / prior['files'][role]['path'])]
                      for role in ('input_units', 'input_candidates')]
            replayed = replay_derivation(prior, *inputs, corrections,
                                        source_containers=restorations, tags=tags)
            if any(jsonl_bytes(rows) != payloads[role] for rows, role in zip(replayed, ['units', 'candidates'], strict=True)):
                raise RecordError('pre-adoption complete historical replay differs from snapshots')
            keys = {(prior_id, uid) for uid in ids}
            if keys & (used_corrections | consumed):
                raise RecordError('pre-adoption predecessor raw is consumed more than once')
            for unit, candidate in zip(old_units, old_candidates, strict=True):
                previous = corrections[(prior_id, unit['unit_id'])]
                successor = corrections[(next_id, unit['unit_id'])]
                if ((next_id, unit['unit_id']) not in used_corrections
                        or previous['unit'] != unit or successor['unit'] != unit):
                    raise RecordError('pre-adoption successor has no same-source current replay')
                context = successor['candidate']['context']
                expected = {'run_id': previous['record']['run_id'], 'correction_id': prior_id,
                    'run_manifest': previous['manifest'], 'correction_record': previous['record'],
                    'raw_candidate': previous['candidate'], 'current_derived_candidate': candidate,
                    'complete_original_actual_run_files': _prior_run_files(root, previous)}
                if (context.get('prior_actual_revision') != expected
                        or context['revision_input'] != previous['candidate']['context']['revision_input']):
                    raise RecordError('pre-adoption successor did not freeze the exact full prior revision')
                binding_keys = {'pre_adoption_snapshot_bindings', 'complete_prior_six_batch_snapshot_bindings'} & context.keys()
                if len(binding_keys) != 1:
                    raise RecordError('pre-adoption requires one complete prior snapshot binding map')
                bindings = context[next(iter(binding_keys))]
                required = {f'translation-data/derivations/{did}.json': manifest['files']['derivation']['hash'],
                            prior['files']['output_units']['path']: manifest['files']['units']['hash'],
                            prior['files']['output_candidates']['path']: manifest['files']['candidates']['hash']}
                if not isinstance(bindings, dict) or any(bindings.get(k) != v for k, v in required.items()):
                    raise RecordError('pre-adoption successor did not freeze complete prior batch bytes')
                dates = [datetime.fromisoformat(value.replace('Z', '+00:00')) for value in
                         [previous['record']['created_at'], successor['record']['created_at'], manifest['created_at']]]
                if not dates[0] < dates[1] <= dates[2]:
                    raise RecordError('pre-adoption actual revisions have invalid time order')
            consumed.update(keys)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f'{path}: {exc}')
    for path in sorted(_input_glob(root / 'translation-data/retired/pre-adoption-replays', '**/*')):
        if (path.is_file() or path.is_symlink()) and path.relative_to(root).as_posix() not in seen_files:
            errors.append(f'{path}: orphaned pre-adoption snapshot')
    return consumed, errors


def pre_adoption_history(root: Path, derivation_id: str) -> list[dict[str, Any]]:
    """Binding/disclosure data, called only after full repository validation."""
    result = []
    for path in sorted(_input_glob(root / 'translation-data/pre-adoption-replays', '*.json')):
        manifest = json.loads(_input_text(path, encoding='utf-8'))
        if manifest['current_derivation_id'] != derivation_id:
            continue
        snapshots = {}
        for role, name in [('derivation', 'derivation.json'), ('units', 'units.jsonl'), ('candidates', 'candidates.jsonl')]:
            snapshot, _ = _read(root, manifest['files'][role],
                rf"translation-data/retired/pre-adoption-replays/{re.escape(manifest['replay_id'])}/{re.escape(name)}")
            if role == 'derivation':
                snapshots[role] = json.loads(_input_text(snapshot))
            else:
                from .derivations import clean
                snapshots[role] = [clean(row) for row in load_jsonl(snapshot)]
        correction = json.loads(_input_text(root / f"translation-data/model-corrections/{manifest['predecessor_correction_id']}.json"))
        result.append({'manifest': manifest, 'snapshots': snapshots, 'correction': correction,
            'run': json.loads(_input_text(root / f"translation-data/runs/{correction['run_id']}.json"))})
    return result
