"""Strict current-candidate checks, separate from versioned historical replay."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .records import RecordError, PLACEHOLDER_TOKEN_RE, load_upstream_commit, validate_records, validate_tex_controls
from .source_integrity import environment_title_errors, hidden_footnote_errors, permanent_tag_mapping
from .source_terms import load_catalog, validate_catalog_evidence, validate_source_terms
from .terminology import load_approved_term_pairs
from .validation_io import (read_bytes as _input_bytes, glob_paths as _input_glob,
    remember_tree, current_inputs, object_inputs)

CURRENT_POLICY_FLAGS = (
    'require_locked_git_source', 'require_permanent_tags', 'require_tex_controls',
    'require_expanded_natural_language', 'require_source_term_catalog_evidence',
    'require_source_term_occurrence_coverage', 'require_protected_token_order',
    'require_exact_trailing_whitespace', 'historical_replay_uses_versioned_contract',
)


class InputSnapshot:
    """Bind reads to actual bytes and reject changed files, paths or Git HEAD."""

    def __init__(self, root: Path):
        if root.is_symlink():
            raise RecordError('validation root is a symlink')
        self.root = root.resolve()
        self.hashes: dict[Path, str] = {}
        self.trees: dict[tuple[Path, str], set[Path]] = {}
        self.head = self._head()
        self.git_paths: set[Path] | None = None

    def _head(self) -> str:
        result = subprocess.run(['git', '-C', str(self.root), 'rev-parse', '--show-toplevel', 'HEAD'], capture_output=True, text=True)
        if result.returncode:
            raise RecordError('current validation requires a readable repository HEAD')
        identity = result.stdout.splitlines()
        if len(identity) != 2 or Path(identity[0]).resolve() != self.root:
            raise RecordError('validation root must be the actual Git worktree root')
        return identity[1]

    def _safe(self, path: Path) -> Path:
        path = path if path.is_absolute() else self.root / path
        if (not path.resolve().is_relative_to(self.root)
                or any(p.is_symlink() for p in [path, *path.parents] if p.resolve().is_relative_to(self.root))):
            raise RecordError(f'validation input escapes repository or is a symlink: {path}')
        return path.parent.resolve() / path.name

    def read(self, path: Path) -> bytes:
        path = self._safe(path)
        try:
            payload = _input_bytes(path)
        except OSError as exc:
            raise RecordError(f'cannot read {path}: {exc}') from exc
        digest = hashlib.sha256(payload).hexdigest()
        if path in self.hashes and self.hashes[path] != digest:
            raise RecordError(f'validation input changed: {path}')
        self.hashes[path] = digest
        return payload

    def jsonl(self, path: Path) -> list[dict[str, Any]]:
        path = self._safe(path)
        try:
            lines = self.read(path).decode('utf-8').splitlines()
        except UnicodeError as exc:
            raise RecordError(f'{path}: invalid UTF-8') from exc
        records = []
        for number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError as exc:
                raise RecordError(f'{path}:{number}: invalid JSON: {exc}') from exc
            if not isinstance(record, dict):
                raise RecordError(f'{path}:{number}: each JSONL row must be an object')
            record['_record_location'] = f'{path}:{number}'
            records.append(record)
        if not records:
            raise RecordError(f'{path}: no records')
        return records

    def watch_tree(self, directory: Path, pattern: str = "*") -> None:
        directory = self._safe(directory)
        if any(p.is_symlink() for p in directory.rglob("*")):
            raise RecordError(f"validation input is a symlink: {directory}")
        paths = {p for p in directory.rglob(pattern) if p.is_file()}
        key = directory, pattern
        if key in self.trees and self.trees[key] != paths:
            raise RecordError(f'validation input paths changed: {directory}')
        self.trees[key] = paths
        directories = {p for p in directory.rglob('*') if p.is_dir()}
        if directory.is_dir():
            directories.add(directory)
        remember_tree(directory, pattern, paths, directories)
        for path in sorted(paths):
            self.read(path)

    def _tracked_paths(self) -> set[Path]:
        result = subprocess.run(['git', '-C', str(self.root), 'ls-files', '-z'], capture_output=True)
        if result.returncode:
            raise RecordError('validation requires a readable tracked source file set')
        return {self._safe(self.root / p.decode('utf-8')) for p in result.stdout.split(b'\0') if p}

    def watch_git_worktree(self) -> None:
        self.git_paths = self._tracked_paths()
        for path in sorted(self.git_paths):
            self.read(path)

    def watch_provenance_inputs(self) -> None:
        """All allowed on-disk historical inputs, including nested raw/freeze evidence."""
        for directory in ['translation-data', 'review', 'config', 'schema', 'task-scopes',
                          'docs/evidence', 'prompts']:
            self.watch_tree(self.root / directory)
        self.watch_tree(self.root / 'stacks_zh', '*.py')
        self.read(self.root / 'upstream.lock')

    def include_dependencies(self, other: InputSnapshot) -> None:
        """Retain the actual reads from recursive adoption replay, not just directories."""
        if other.root != self.root or other.head != self.head:
            raise RecordError('validation dependencies belong to another repository or HEAD')
        # Transfer the original byte/path claims. The consuming boundary performs
        # one real assert_unchanged over the union, rather than re-reading shared
        # units once for every recursive witness.
        for path, digest in other.hashes.items():
            if path in self.hashes and self.hashes[path] != digest:
                raise RecordError(f'validation dependency changed: {path}')
            self.hashes[path] = digest
        for key, paths in other.trees.items():
            if key in self.trees and self.trees[key] != paths:
                raise RecordError(f'validation dependency paths changed: {key[0]}')
            self.trees[key] = set(paths)

    def watch_repository(self) -> None:
        self.watch_provenance_inputs()
        for name in ['Makefile', 'AGENTS.md', 'WORKFLOW.md', 'stacks_zh.py']:
            self.read(self.root / name)

    def assert_unchanged(self) -> None:
        if self._head() != self.head:
            raise RecordError('repository HEAD changed during validation')
        if self.git_paths is not None and self._tracked_paths() != self.git_paths:
            raise RecordError('tracked source input paths changed during validation')
        for (directory, pattern), paths in self.trees.items():
            self._safe(directory)
            if any(p.is_symlink() for p in directory.rglob('*')):
                raise RecordError(f'validation input is a symlink: {directory}')
            if {p for p in directory.rglob(pattern) if p.is_file()} != paths:
                raise RecordError(f'validation input paths changed: {directory}')
        for path in list(self.hashes):
            self.read(path)


def validate_current_records(units: list[dict[str, Any]], candidates: list[dict[str, Any]],
                             source_commit: str, catalog: dict[str, Any], tags: dict[str, str],
                             approved: set[tuple[str, str]]) -> list[str]:
    """Current structural/term policy only; callers also verify source and provenance."""
    errors = validate_records(units, candidates, source_commit)
    if errors:
        return errors
    if catalog.get('source_commit') != source_commit:
        return ['source term catalog uses a different locked source commit']
    if not tags:
        return ['current source validation requires locked permanent Tags']
    mapping = permanent_tag_mapping(units, tags)
    errors.extend(f'wrong permanent Tag: {old} -> {new}' for old, new in mapping.items() if old != new)
    by_id = {c['unit_id']: c for c in candidates}
    for unit in units:
        candidate = by_id[unit['unit_id']]
        errors.extend(validate_tex_controls(unit, candidate))
        errors.extend(environment_title_errors(unit))
        errors.extend(hidden_footnote_errors(unit))
        errors.extend(validate_source_terms(unit, candidate, catalog, approved))
        if PLACEHOLDER_TOKEN_RE.findall(unit['source_text']) != PLACEHOLDER_TOKEN_RE.findall(candidate['translation']):
            errors.append(f"{unit['unit_id']}: protected token order/count differs")
        if re.search(r'[ \t\r\n]*$', unit['source_text'])[0] != re.search(r'[ \t\r\n]*$', candidate['translation'])[0]:
            errors.append(f"{unit['unit_id']}: trailing whitespace differs")
    return errors


class CurrentSourceQA:
    """One live source/catalog context for one scoped or repository invocation."""

    @object_inputs
    def __init__(self, root: Path, harvest: Path | None = None, *, snapshot: InputSnapshot | None = None,
                 inventory: Path | None = None):
        from .source_containers import Containers
        self.root = root.resolve()
        from .repository_validation import _ImplementationIdentity
        self._implementation = _ImplementationIdentity()
        self._reads.seed_implementation(self._implementation)
        self.snapshot = snapshot or InputSnapshot(self.root)
        if self.snapshot.root != self.root:
            raise RecordError('validation snapshot belongs to another repository')
        for directory in ['config', 'schema', 'translation-data/units']:
            self.snapshot.watch_tree(self.root / directory)
        self.snapshot.watch_tree(self.root / 'stacks_zh', '*.py')
        self.snapshot.read(self.root / 'upstream.lock')
        policy = self.snapshot.read(self.root / 'config/workflow.yml').decode('utf-8')
        section = re.search(r'(?m)^current_candidate_qa:[ \t]*\n((?:[ \t]+[^\n]*\n|[ \t]*\n)*)', policy)
        if len(re.findall(r'(?m)^current_candidate_qa:', policy)) != 1 or section is None or any(re.findall(r'(?m)^  '+flag+r':[ \t]*(true|false)[ \t]*$', section[1]) != ['true']
                                  for flag in CURRENT_POLICY_FLAGS):
            raise RecordError('current_candidate_qa policy requires every strict gate enabled')
        self.source_commit = load_upstream_commit(self.root / 'upstream.lock')
        self.containers = Containers(self.root, harvest)
        self.harvest = self.containers.english.harvest
        self.catalog = load_catalog(self.root)
        if not self.catalog['terms']:
            raise RecordError('current source term catalog must not be empty')
        self.approved = load_approved_term_pairs(self.root / 'config/glossary.yml')
        self.units: dict[str, dict[str, Any]] = {}
        for path in sorted(_input_glob(self.root / 'translation-data/units', '*.jsonl')):
            for unit in self.snapshot.jsonl(path):
                if unit['unit_id'] in self.units:
                    raise RecordError(f"duplicate active source unit: {unit['unit_id']}")
                if unit['source_commit'] != self.source_commit:
                    raise RecordError(f"different source commit: {unit['unit_id']}")
                self.units[unit['unit_id']] = unit
        self.catalog_evidence, errors = validate_catalog_evidence(
            self.root, self.catalog, list(self.units.values()), self.harvest, containers=self.containers)
        if errors:
            raise RecordError('source catalog evidence failed:\n' + '\n'.join(errors))
        self.inventory = inventory or self.root / 'source-ir/extraction'
        if not self.inventory.is_absolute():
            self.inventory = self.root / self.inventory
        self._corpora: dict[tuple[str, ...], Any] = {}
        self._pair_locations = None
        self.snapshot.assert_unchanged()

    def _corpus(self, chapters: set[str]):
        from .extraction import write_inventory
        from .source_alignment import Corpus, verified_inventory
        key = tuple(sorted(chapters))
        if key not in self._corpora:
            if not self.inventory.exists():
                write_inventory(self.root, self.harvest, self.inventory)
            self.snapshot.watch_tree(self.inventory)
            english, policy, entries, _ = verified_inventory(self.root, self.harvest, self.inventory, chapters)
            self._corpora[key] = Corpus(entries, english.tags, policy, source_containers=self.containers)
        return self._corpora[key]

    @object_inputs
    def source_errors(self, batches: dict[str, list[dict[str, Any]]]) -> list[str]:
        from .source_alignment import align_batches
        chapters = {u['chapter'] for units in batches.values() for u in units}
        matches, _ = align_batches(batches, self._corpus(chapters))
        errors = [f"{m['unit_id']}: locked source {m['status']}: {m.get('reason', '')}"
                  for m in matches if m['status'] not in {'BYTE_EXACT', 'PRESENTATION_EQUIVALENT'}
                  or m.get('extractor_state') != 'READY']
        self._pair_locations = None if errors else tuple(
            (m['location']['file'], m['location']['byte_start'], m['location']['byte_end'])
            for m in matches)
        return errors

    def _assert_pair_order(self):
        """Use this actual alignment; repository QA intentionally has no batch-order gate."""
        if not self._pair_locations:
            raise RecordError('batch order requires successful current source QA alignment')
        previous = {}
        for file, start, end in self._pair_locations:
            if start < previous.get(file, -1):
                raise RecordError('batch pairs must follow locked source order without overlap')
            previous[file] = end

    @object_inputs
    def validate_pairs(self, unit_paths: Iterable[Path], candidate_paths: Iterable[Path],
                       *, chapter: str | None = None) -> tuple[int, list[str]]:
        unit_paths, candidate_paths = list(unit_paths), list(candidate_paths)
        self._pair_locations = None
        if not unit_paths or len(unit_paths) != len(candidate_paths):
            raise RecordError('current QA requires equally ordered nonempty unit/candidate paths')
        count, errors, batches = 0, [], {}
        for index, (up, cp) in enumerate(zip(unit_paths, candidate_paths, strict=True)):
            try:
                units = self.snapshot.jsonl(up)
                if chapter is not None:
                    chapters = {u['chapter'] for u in units}
                    if chapter not in chapters:
                        continue
                    if chapters != {chapter}:
                        raise RecordError('chapter QA cannot split a mixed-chapter batch')
                candidates = self.snapshot.jsonl(cp)
                problems = validate_current_records(units, candidates, self.source_commit, self.catalog,
                                                    self.containers.english.tags, self.approved)
                errors.extend(f'{cp}: {error}' for error in problems)
                batches[str(index)] = units
                count += len(candidates)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append(f'{cp}: {exc}')
        if not batches:
            errors.append('no current candidate batches selected')
        if not errors:
            errors.extend(self.source_errors(batches))
        self.assert_unchanged()
        return count, errors

    @object_inputs
    def validate_repository(self) -> tuple[int, list[str]]:
        directory = self.root / 'translation-data/candidates'
        self.snapshot.watch_tree(directory)
        candidates = sorted(_input_glob(directory, '*/*.jsonl'))
        if not candidates:
            raise RecordError('no candidate batches found for full repository QA')
        units = [self.root / 'translation-data/units' / path.name for path in candidates]
        covered = {path.stem for path in candidates}
        missing = {p.stem for p in _input_glob(self.root / 'translation-data/units', '*.jsonl')} - covered
        count, errors = self.validate_pairs(units, candidates)
        errors.extend(f'{name}: source batch has no candidate coverage' for name in sorted(missing))
        return len(candidates), errors

    @object_inputs
    def validate_drafts(self, unit_paths: Iterable[Path], draft_path: Path) -> list[str]:
        from .schema_validation import validate_named_schema
        batches = {str(i): self.snapshot.jsonl(p) for i, p in enumerate(unit_paths)}
        units = [u for rows in batches.values() for u in rows]
        drafts = self.snapshot.jsonl(draft_path)
        if len({u['unit_id'] for u in units}) != len(units) or len({d['unit_id'] for d in drafts}) != len(drafts):
            return ['translator outputs and source units require unique IDs']
        if Counter(u['unit_id'] for u in units) != Counter(d['unit_id'] for d in drafts):
            return ['translator outputs must exactly cover their current source units']
        by_id = {d['unit_id']: d for d in drafts}
        errors = self.source_errors(batches)
        mapping = permanent_tag_mapping(units, self.containers.english.tags)
        errors.extend(f'wrong permanent Tag: {old} -> {new}' for old, new in mapping.items() if old != new)
        for u in units:
            errors.extend(environment_title_errors(u))
            errors.extend(hidden_footnote_errors(u))
            d = {k: v for k, v in by_id[u['unit_id']].items() if not k.startswith('_')}
            schema_errors = validate_named_schema(d, 'translator-output.schema.json', u['unit_id'])
            errors.extend(schema_errors)
            if schema_errors:
                continue
            errors.extend(validate_tex_controls(u, d))
            errors.extend(validate_source_terms(u, {**d, 'term_status': 'DECISION_REQUIRED' if d['unknown_terms'] else 'CLEAR'}, self.catalog, self.approved))
            if PLACEHOLDER_TOKEN_RE.findall(u['source_text']) != PLACEHOLDER_TOKEN_RE.findall(d['translation']):
                errors.append(f"{u['unit_id']}: protected token order/count differs")
            if re.search(r'[ \t\r\n]*$', u['source_text'])[0] != re.search(r'[ \t\r\n]*$', d['translation'])[0]:
                errors.append(f"{u['unit_id']}: trailing whitespace differs")
        self.assert_unchanged()
        return errors

    def assert_unchanged(self) -> None:
        self._implementation.assert_valid()
        self._reads.assert_unchanged()
        self.containers.assert_unchanged()
        self.snapshot.assert_unchanged()
