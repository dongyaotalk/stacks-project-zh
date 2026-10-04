from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .records import (RecordError, load_jsonl, load_upstream_commit, sha256_value,
                      validate_records, validate_tex_controls)
from .schema_validation import validate_named_schema
from .terminology import load_approved_term_pairs


def _clean(row: dict[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in row.items() if not key.startswith('_')}


def _hash(payload: bytes) -> str:
    return 'sha256:' + hashlib.sha256(payload).hexdigest()


def _safe_path(root: Path, value: str, pattern: str) -> Path:
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise RecordError('invalid model-correction snapshot path')
    path = root / value
    if not path.resolve().is_relative_to(root.resolve()) or any(
        part.is_symlink() for part in [path, *path.parents] if part.is_relative_to(root)
    ):
        raise RecordError('model-correction path escapes the repository or is a symlink')
    return path


def _first_addition_is_immutable(root: Path, path: Path) -> None:
    """New evidence may be uncommitted; once added it cannot be rehashed away."""
    relative = path.relative_to(root).as_posix()
    history = subprocess.run(
        ['git', '-C', str(root), 'log', '--reverse', '--diff-filter=A', '--format=%H', 'HEAD', '--', relative],
        capture_output=True, text=True,
    )
    if history.returncode:
        raise RecordError('model-correction evidence requires a readable Git history')
    commits = history.stdout.splitlines()
    if not commits:
        return
    original = subprocess.run(['git', '-C', str(root), 'show', f'{commits[0]}:{relative}'], capture_output=True)
    if original.returncode or original.stdout != path.read_bytes():
        raise RecordError(f'{relative}: immutable correction evidence differs from its first Git addition')


def load_repository_corrections(root: Path) -> tuple[dict[tuple[str, str], dict[str, Any]], list[str]]:
    """Validate frozen revision inputs/output; run identity is also checked by provenance."""
    corrections: dict[tuple[str, str], dict[str, Any]] = {}
    errors: list[str] = []
    snapshots: set[str] = set()
    runs: set[str] = set()
    for path in sorted((root / 'translation-data/model-corrections').glob('*.json')):
        try:
            record = json.loads(path.read_text(encoding='utf-8'))
            schema_errors = validate_named_schema(record, 'model-correction.schema.json', str(path))
            if schema_errors:
                raise RecordError('\n'.join(schema_errors))
            correction_id = record['correction_id']
            if path.stem != correction_id:
                raise RecordError('model-correction filename differs from ID')
            source_commit = load_upstream_commit(root / 'upstream.lock')
            if record['source_commit'] != source_commit:
                raise RecordError('model correction has a stale source commit')
            resolved: dict[str, Path] = {}
            for role in ('units', 'candidates'):
                entry = record['files'][role]
                pattern = rf'translation-data/retired/model-corrections/{re.escape(correction_id)}/{role}\.jsonl'
                resolved[role] = _safe_path(root, entry['path'], pattern)
                if entry['path'] in snapshots:
                    raise RecordError('model-correction snapshot is claimed twice')
                snapshots.add(entry['path'])
                if _hash(resolved[role].read_bytes()) != entry['hash']:
                    raise RecordError(f'{role}: correction snapshot hash mismatch')
            run_path = _safe_path(root, f"translation-data/runs/{record['run_id']}.json", r'translation-data/runs/[A-Za-z0-9._-]+\.json')
            manifest = json.loads(run_path.read_text(encoding='utf-8'))
            schema_errors = validate_named_schema(manifest, 'run-manifest.schema.json', str(run_path))
            if schema_errors:
                raise RecordError('\n'.join(schema_errors))
            if record['run_id'] in runs:
                raise RecordError('one revision run must have one complete correction record')
            runs.add(record['run_id'])
            if (manifest['run_id'] != record['run_id'] or manifest['run_kind'] != 'revision'
                    or manifest['source_commit'] != source_commit
                    or manifest['created_at'] != record['created_at']
                    or manifest.get('status', 'recorded') != 'recorded'):
                raise RecordError('correction must match a current, recorded revision run')
            if (manifest['model']['identity_confidence'] == 'unknown'
                    or manifest['harness']['version'].lower() in {'unknown', 'auto', 'unavailable'}):
                raise RecordError('model correction requires a known model identity and concrete Harness version')
            units = [_clean(row) for row in load_jsonl(resolved['units'])]
            candidates = [_clean(row) for row in load_jsonl(resolved['candidates'])]
            unit_ids = [row['unit_id'] for row in units]
            if (not unit_ids or len(set(unit_ids)) != len(unit_ids)
                    or unit_ids != record['unit_ids'] or unit_ids != manifest['unit_ids']
                    or [row['unit_id'] for row in candidates] != unit_ids
                    or set(record['derivation_ids']) != set(unit_ids)):
                raise RecordError('correction must cover exactly its ordered frozen units, run and outputs')
            if len({row['chapter'] for row in units}) != 1:
                raise RecordError('model correction cannot span chapters')
            qa_errors = validate_records(units, candidates, source_commit)
            for unit, candidate in zip(units, candidates, strict=True):
                qa_errors.extend(validate_tex_controls(unit, candidate))
                if 'derivation_id' in candidate or 'model_correction_id' in candidate:
                    qa_errors.append('revision output must be raw model output')
                if candidate['run_id'] != record['run_id'] or candidate['created_at'] != record['created_at']:
                    qa_errors.append('revision output run/time differs from frozen evidence')
                if candidate['qa_status'] != 'PASS' or candidate['stage'] not in {'STRUCTURE_OK', 'TERM_OK'}:
                    qa_errors.append('model correction requires passed structural QA')
                context = candidate['context']
                if context.get('source_unit') != unit:
                    qa_errors.append('revision context does not freeze the complete current source unit')
                revision_input = context.get('revision_input')
                if (not isinstance(revision_input, dict) or set(revision_input) != {'kind', 'candidate', 'source_unit'}
                        or revision_input.get('kind') != 'candidate-to-revise'
                        or not isinstance(revision_input.get('candidate'), dict)
                        or not isinstance(revision_input.get('source_unit'), dict)):
                    qa_errors.append('revision context must explicitly freeze its previous candidate as a revision object')
                pairs = {(item['source_term'], item['target_term']) for item in candidate['term_occurrences']}
                pending = {(item['source_term'], item['target_term']) for item in candidate['unknown_terms']}
                if pairs - pending:
                    approved = load_approved_term_pairs(root / 'config/glossary.yml')
                    if pairs - pending - approved:
                        qa_errors.append('revision output cannot confer unverified terminology approval')
            if manifest['inputs']['context_hashes'] != [row['context_hash'] for row in candidates]:
                qa_errors.append('revision run contexts differ from frozen output')
            if qa_errors:
                raise RecordError('\n'.join(qa_errors))
            for frozen in (path, run_path, *resolved.values()):
                _first_addition_is_immutable(root, frozen)
            for unit, candidate in zip(units, candidates, strict=True):
                corrections[(correction_id, unit['unit_id'])] = {
                    'record': record, 'unit': unit, 'candidate': candidate,
                    'manifest': manifest, 'candidate_path': resolved['candidates'],
                }
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f'{path}: {exc}')
    for path in sorted((root / 'translation-data/retired/model-corrections').glob('*/*.jsonl')):
        if path.relative_to(root).as_posix() not in snapshots:
            errors.append(f'{path}: orphaned raw model-correction snapshot')
    return corrections, errors


def candidate_provenance_hash(root: Path, candidate: dict[str, Any]) -> str:
    """Bind selection/review to all current content and both immutable run origins.

    Call only after repository provenance validation; this is a binding hash,
    not a replacement for validating the files or their identity.
    """
    correction_id = candidate['model_correction_id']
    derivation_id = candidate['derivation_id']
    for identifier in (correction_id, derivation_id, candidate['run_id']):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', identifier) or '..' in identifier:
            raise RecordError('invalid composite provenance ID')
    def read(relative: str) -> dict[str, Any]:
        return json.loads((root / relative).read_text(encoding='utf-8'))
    correction = read(f'translation-data/model-corrections/{correction_id}.json')
    return sha256_value({
        'candidate': _clean(candidate),
        'derivation': read(f'translation-data/derivations/{derivation_id}.json'),
        'correction': correction,
        'origin_run': read(f"translation-data/runs/{candidate['run_id']}.json"),
        'correction_run': read(f"translation-data/runs/{correction['run_id']}.json"),
    })
