from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .model_corrections import _first_addition_is_immutable
from .records import RecordError, load_upstream_commit
from .schema_validation import validate_named_schema


def _hash(payload: bytes) -> str:
    return 'sha256:' + hashlib.sha256(payload).hexdigest()


def _path(root: Path, value: str, expected: str) -> Path:
    if value != expected:
        raise RecordError('archive path differs from its declared role/derivation')
    path = root / value
    if (not path.resolve().is_relative_to(root.resolve()) or any(
            part.is_symlink() for part in [path, *path.parents] if part.is_relative_to(root))):
        raise RecordError('archive path escapes the repository or is a symlink')
    return path


def _git_bytes(root: Path, commit: str, path: str) -> bytes:
    ancestry = subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', commit, 'HEAD'], capture_output=True)
    if ancestry.returncode:
        raise RecordError('archive origin_commit must be a reachable ancestor of HEAD')
    result = subprocess.run(['git', '-C', str(root), 'show', f'{commit}:{path}'], capture_output=True)
    if result.returncode:
        raise RecordError(f'archive origin_commit has no file: {path}')
    return result.stdout


def load_derivation_archives(root: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Verify archive storage/Git bindings; replay and successor checks follow.

    Archives retain the earlier record's logical active paths. They redirect
    only that record's output reads to immutable historical bytes, never its
    inputs or the new current record's output.
    """
    archives, errors = {}, []
    for path in sorted((root / 'translation-data/derivation-archives').glob('*.json')):
        try:
            _path(root, path.relative_to(root).as_posix(), path.relative_to(root).as_posix())
            archive = json.loads(path.read_text(encoding='utf-8'))
            schema_errors = validate_named_schema(archive, 'derivation-archive.schema.json', str(path))
            if schema_errors:
                raise RecordError('\n'.join(schema_errors))
            _first_addition_is_immutable(root, path)
            prior = archive['prior_derivation_id']
            successor = archive['successor_derivation_id']
            if (path.stem != prior or prior == successor or '..' in prior or '..' in successor):
                raise RecordError('invalid archive prior/successor IDs')
            if archive['source_commit'] != load_upstream_commit(root / 'upstream.lock'):
                raise RecordError('archive has a stale source commit')
            record_path = _path(root, archive['record']['path'], f'translation-data/derivations/{prior}.json')
            record_bytes = record_path.read_bytes()
            if _hash(record_bytes) != archive['record']['hash']:
                raise RecordError('archive prior record hash mismatch')
            if record_bytes != _git_bytes(root, archive['origin_commit'], archive['record']['path']):
                raise RecordError('archive prior record differs from original Git bytes')
            record = json.loads(record_bytes)
            if record['derivation_id'] != prior or record['source_commit'] != archive['source_commit']:
                raise RecordError('archive prior record has a different identity/source')
            outputs = {}
            for role, name in [('output_units', 'output-units'), ('output_candidates', 'output-candidates')]:
                entry = archive['files'][role]
                frozen = _path(root, entry['path'], f'translation-data/retired/derivations/{prior}/{name}.jsonl')
                _first_addition_is_immutable(root, frozen)
                payload = frozen.read_bytes()
                if _hash(payload) != entry['hash'] or entry['hash'] != record['files'][role]['hash']:
                    raise RecordError(f'{role}: archive output hash mismatch')
                logical = record['files'][role]['path']
                expected = (r'translation-data/units/[A-Za-z0-9._-]+\.jsonl' if role == 'output_units'
                            else r'translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl')
                if not re.fullmatch(expected, logical) or '..' in logical:
                    raise RecordError('archive prior record has an invalid logical output path')
                if payload != _git_bytes(root, archive['origin_commit'], logical):
                    raise RecordError(f'{role}: archive output differs from original Git bytes')
                outputs[role] = frozen
            archives[prior] = {'manifest': archive, 'record': record, 'outputs': outputs}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f'{path}: {exc}')
    return archives, errors


def derivation_history(root: Path, derivation_id: str) -> list[dict[str, Any]]:
    """Return the chronological archive/record chain after provenance passes."""
    history, visiting = [], set()
    def visit(identifier: str) -> None:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', identifier) or '..' in identifier or identifier in visiting:
            raise RecordError('invalid or cyclic derivation history')
        visiting.add(identifier)
        record = json.loads((root / f'translation-data/derivations/{identifier}.json').read_text())
        previous = record.get('previous_derivation_id')
        if previous:
            visit(previous)
            archive = json.loads((root / f'translation-data/derivation-archives/{previous}.json').read_text())
            if archive['successor_derivation_id'] != identifier:
                raise RecordError('derivation history has a different successor')
        else:
            archive = None
        history.append({'derivation': record, 'previous_archive': archive})
        visiting.remove(identifier)
    visit(derivation_id)
    return history
