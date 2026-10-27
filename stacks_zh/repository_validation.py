"""One live repository acceptance session; no persistent pass cache or skip flag."""
from __future__ import annotations

from dataclasses import dataclass
import subprocess
from pathlib import Path
from typing import Callable, Iterable
from weakref import WeakValueDictionary, finalize

from .current_qa import InputSnapshot, CurrentSourceQA
from .records import RecordError, sha256_value
from .provenance import _validate_repository_provenance
from .schema_validation import validate_repository_schemas
from .validation_io import tracked_inputs, current_inputs, InputReads

# Bind the code actually imported, including Python callers validating another
# Git root. A later source edit requires a fresh invocation instead of silently
# certifying with already-loaded old Python functions.
_CODE_DIRECTORY = Path(__file__).resolve().parent
_LOADED_CODE = tuple((path, path.read_bytes()) for path in sorted(_CODE_DIRECTORY.rglob('*.py')))
_IMPLEMENTATIONS = WeakValueDictionary()
_IMPLEMENTATION_BINDINGS = {}


class _ImplementationIdentity:
    def __init__(self):
        from .schema_validation import SCHEMA_ROOT, load_schema
        self.schema_root = SCHEMA_ROOT.resolve()
        self.trees = ((_CODE_DIRECTORY, '*.py', frozenset(path for path, _ in _LOADED_CODE)),
                      (self.schema_root, '*.json', frozenset(self.schema_root.rglob('*.json'))))
        self.inputs = (*_LOADED_CODE, *((path, path.read_bytes()) for path in sorted(self.trees[1][2])))
        self._assert_inputs()
        _IMPLEMENTATIONS[id(self)] = self
        _IMPLEMENTATION_BINDINGS[id(self)] = self.binding()
        finalize(self, _IMPLEMENTATION_BINDINGS.pop, id(self), None)
        load_schema.cache_clear()

    def binding(self):
        from hashlib import sha256
        return sha256_value(dict(schema_root=str(self.schema_root),
            trees=[(str(directory), pattern, sorted(str(p) for p in paths))
                   for directory, pattern, paths in self.trees],
            files=[(str(path), sha256(raw).hexdigest()) for path, raw in self.inputs]))

    def assert_valid(self):
        if (_IMPLEMENTATIONS.get(id(self)) is not self
                or self.binding() != _IMPLEMENTATION_BINDINGS.get(id(self))):
            raise RecordError('implementation identity was not issued from actual loaded inputs')
        self._assert_inputs()

    def _assert_inputs(self):
        from .schema_validation import SCHEMA_ROOT
        if SCHEMA_ROOT.resolve() != self.schema_root:
            raise RecordError('validation implementation Schema location changed')
        for directory, pattern, paths in self.trees:
            if directory.is_symlink() or any(p.is_symlink() for p in directory.rglob('*')):
                raise RecordError('validation implementation input is a symlink')
            if frozenset(directory.rglob(pattern)) != paths:
                raise RecordError('validation implementation paths changed')
        for path, raw in self.inputs:
            if path.read_bytes() != raw:
                raise RecordError(f'validation implementation input changed: {path}')


_ISSUER = object()
_ISSUED = WeakValueDictionary()
_ISSUED_CLAIMS = {}


def _snapshot_claims(snapshot):
    return (id(snapshot), snapshot.root, snapshot.head, dict(snapshot.hashes),
            {key: frozenset(paths) for key, paths in snapshot.trees.items()},
            None if snapshot.git_paths is None else frozenset(snapshot.git_paths))


def _require_snapshot_claims(snapshot, claims):
    identity, root, head, hashes, trees, git_paths = claims
    if (id(snapshot) != identity or snapshot.root != root or snapshot.head != head
            or snapshot.git_paths != git_paths
            or any(snapshot.hashes.get(path) != digest for path, digest in hashes.items())
            or any(snapshot.trees.get(key) != paths for key, paths in trees.items())):
        raise RecordError('validation receipt dependency claims changed')


def _source_claims(source):
    return (id(source), source.path, source.exists, frozenset(source.source_files), source.repository,
            None if source.snapshot is None else _snapshot_claims(source.snapshot))


def _require_source_claims(source, claims):
    identity, path, exists, files, repository, snapshot = claims
    if (id(source) != identity or source.path != path or source.exists != exists
            or source.source_files != files or source.repository != repository
            or (source.snapshot is None) != (snapshot is None)):
        raise RecordError('validation receipt source claims changed')
    if snapshot is not None:
        _require_snapshot_claims(source.snapshot, snapshot)


def _issue(result, claims):
    _ISSUED[id(result)] = result
    _ISSUED_CLAIMS[id(result)] = claims
    finalize(result, _ISSUED_CLAIMS.pop, id(result), None)


class _SourceIdentity:
    """Bind the effective harvest and its tracked worktree, even for Git-only reads."""
    def __init__(self, root: Path, harvest: Path | None):
        self.path = (harvest if harvest is not None else root.parent / 'stacks-project').absolute()
        if self.path.is_symlink():
            raise RecordError('source harvest is a symlink')
        self.path = self.path.resolve()
        self.exists = self.path.exists()
        self.repository = self._repository() if self.exists else None
        self.source_files = {p.name for p in self.path.glob('*.tex')}
        self.snapshot = InputSnapshot(self.path) if self.exists else None
        if self.snapshot is not None:
            self.snapshot.watch_git_worktree()
            self.snapshot.watch_tree(self.path / 'tags')
            for path in self.path.glob('*.tex'):
                self.snapshot._safe(path)

    def _repository(self):
        result = subprocess.run(['git', '-C', str(self.path), 'remote', 'get-url', 'origin'],
                                capture_output=True, text=True)
        return result.returncode, result.stdout.strip()

    def assert_valid(self, root: Path, harvest: Path | None) -> None:
        path = (harvest if harvest is not None else root.parent / 'stacks-project').absolute()
        if path.is_symlink() or path.resolve() != self.path or self.path.exists() != self.exists:
            raise RecordError('source identity differs from this live validation session')
        if self.exists and self._repository() != self.repository:
            raise RecordError('source repository identity changed during validation')
        if {p.name for p in self.path.glob('*.tex')} != self.source_files:
            raise RecordError('source input paths changed during validation')
        if self.snapshot is not None:
            self.snapshot.assert_unchanged()


@dataclass(frozen=True)
class _ProvenancePass:
    """Internal capability issued only after this invocation actually validates."""
    root: Path
    snapshot: InputSnapshot
    _issuer: object
    source: _SourceIdentity | None = None
    adoptions: object = None
    implementation: object = None
    reads: object = None

    def assert_valid(self, root: Path, harvest: Path | None = None) -> None:
        if (_ISSUED.get(id(self)) is not self or self._issuer is not _ISSUER or self.root != root.resolve()
                or self.snapshot.root != self.root or self.source is None):
            raise RecordError('provenance result is not from this live repository session')
        snapshot, source, adoption, implementation, read_claims = _ISSUED_CLAIMS[id(self)]
        if type(self.reads) is not InputReads:
            raise RecordError('provenance requires an actual input read session')
        self.reads.require_claims(read_claims)
        _require_snapshot_claims(self.snapshot, snapshot)
        _require_source_claims(self.source, source)
        if id(self.adoptions) != adoption:
            raise RecordError('validation receipt adoption result changed')
        from .source_adoptions import _ValidatedAdoptions
        if type(self.adoptions) is not _ValidatedAdoptions:
            raise RecordError('provenance requires an actual complete adoption replay')
        if (self.implementation is None or id(self.implementation) != implementation[0]
                or self.implementation.binding() != implementation[1]):
            raise RecordError('validation receipt implementation claims changed')
        self.implementation.assert_valid()
        self.reads.assert_unchanged()
        self.snapshot.assert_unchanged()
        self.source.assert_valid(self.root, harvest)
        self.adoptions.assert_unchanged(self.root, harvest)


def _require_live_provenance(result: object, root: Path, harvest: Path | None = None) -> _ProvenancePass:
    if type(result) is not _ProvenancePass:
        raise RecordError('decision validation requires an actual live provenance result')
    result.assert_valid(root, harvest)
    return result


@tracked_inputs
def _complete_provenance(root: Path, harvest: Path | None = None, *,
                         snapshot: InputSnapshot | None = None,
                         _implementation=None) -> tuple[_ProvenancePass | None, list[str]]:
    """Only this real full replay can issue the private, same-invocation result."""
    if root.is_symlink():
        raise RecordError('validation root is a symlink')
    root = root.resolve()
    if snapshot is None:
        snapshot = InputSnapshot(root)
        # Independent Python render consumers need the historical inputs, not
        # unrelated Make/workflow metadata absent from minimal repositories.
        snapshot.watch_provenance_inputs()
    if snapshot.root != root:
        raise RecordError('validation snapshot belongs to another repository')
    if _implementation is not None and type(_implementation) is not _ImplementationIdentity:
        raise RecordError('provenance requires an actual implementation identity')
    implementation = _ImplementationIdentity() if _implementation is None else _implementation
    implementation.assert_valid()
    reads = current_inputs()
    reads.seed_implementation(implementation)
    reads.seed_snapshot(snapshot)
    reads.watch_root(root)
    source = _SourceIdentity(root, harvest)
    from .records import _validation_reads
    with _validation_reads(snapshot):
        adoptions, errors = _validate_repository_provenance(root, harvest)
    if errors:
        snapshot.assert_unchanged()
        source.assert_valid(root, harvest)
        return None, errors
    from .source_adoptions import _ValidatedAdoptions
    if type(adoptions) is not _ValidatedAdoptions:
        raise RecordError('provenance requires an actual complete adoption replay')
    for dependency in adoptions.snapshots:
        snapshot.include_dependencies(dependency)
    proof = _ProvenancePass(root, snapshot, _ISSUER, source, adoptions, implementation, reads)
    _issue(proof, (_snapshot_claims(snapshot), _source_claims(source), id(adoptions),
                   (id(implementation), implementation.binding()), reads.claims()))
    proof.assert_valid(root, harvest)
    return proof, []


@tracked_inputs
def _shared_checks(root: Path, harvest: Path | None, emit: Callable[[str], None]):
    from .decisions import validate_repository_decisions
    if root.is_symlink():
        raise RecordError('validation root is a symlink')
    root = root.resolve()
    implementation = _ImplementationIdentity()
    reads = current_inputs()
    reads.seed_implementation(implementation)
    reads.watch_root(root)
    snapshot = InputSnapshot(root)
    snapshot.watch_repository()
    errors = validate_repository_schemas(root)
    snapshot.assert_unchanged()
    if errors:
        return None, errors
    emit('Repository JSON Schema: PASS')
    proof, errors = _complete_provenance(root, harvest, snapshot=snapshot, _implementation=implementation)
    if errors:
        return None, errors
    emit('Model provenance: PASS (one complete historical replay in this invocation)')
    errors = validate_repository_decisions(root, harvest, _provenance=proof)
    proof.assert_valid(root, harvest)
    if errors:
        return None, errors
    emit('Selection and revision linkage: PASS')
    return proof, []


@dataclass(frozen=True)
class _BatchPass:
    """Current QA for exactly these ordered pairs; never a repository-wide QA claim."""
    provenance: _ProvenancePass
    current: CurrentSourceQA
    pairs: tuple[tuple[Path, Path], ...]
    count: int
    _issuer: object

    def assert_valid(self, root: Path, harvest: Path | None,
                     units: Iterable[Path], candidates: Iterable[Path]) -> None:
        if _ISSUED.get(id(self)) is not self or self._issuer is not _ISSUER:
            raise RecordError('batch result is not from this live validation session')
        provenance, current, pairs_claim, count, snapshot_claim, read_claims = _ISSUED_CLAIMS[id(self)]
        self.provenance.reads.require_claims(read_claims)
        if (id(self.provenance) != provenance or id(self.current) != current
                or self.pairs != pairs_claim or self.count != count):
            raise RecordError('batch receipt scope claims changed')
        _require_snapshot_claims(self.provenance.snapshot, snapshot_claim)
        # _safe checks the supplied paths before resolving, so symlink aliases fail.
        snapshot = self.provenance.snapshot
        units, candidates = list(units), list(candidates)
        if not units or len(units) != len(candidates):
            raise RecordError('batch result requires complete ordered pairs')
        pairs = tuple(zip((snapshot._safe(p) for p in units),
                          (snapshot._safe(p) for p in candidates), strict=True))
        if pairs != self.pairs:
            raise RecordError('batch result does not cover these ordered unit/candidate pairs')
        self.provenance.assert_valid(root, harvest)
        self.current.assert_unchanged()


def _require_batch_validation(result: object, root: Path, harvest: Path | None,
                               units: Iterable[Path], candidates: Iterable[Path]) -> _BatchPass:
    if type(result) is not _BatchPass:
        raise RecordError('render requires an actual live batch validation result')
    result.assert_valid(root, harvest, units, candidates)
    return result


def _active_provenance_pairs(snapshot: InputSnapshot, units: Iterable[Path],
                             candidates: Iterable[Path]) -> tuple[tuple[Path, Path], ...]:
    """The repository replay covers active inventory, never arbitrary caller files."""
    units, candidates = list(units), list(candidates)
    if not units or len(units) != len(candidates):
        raise RecordError('provenance consumption requires complete ordered pairs')
    pairs = tuple(zip((snapshot._safe(p) for p in units),
                      (snapshot._safe(p) for p in candidates), strict=True))
    if any(u.name != c.name for u, c in pairs):
        raise RecordError('batch validation requires matching unit/candidate filenames')
    root = snapshot.root
    if any(u.parent != root / 'translation-data/units' or u.suffix != '.jsonl'
           or c.parent.parent != root / 'translation-data/candidates' for u, c in pairs):
        raise RecordError('provenance consumption requires active files covered by repository provenance')
    return pairs


@tracked_inputs
def validate_batches_session(unit_paths: Iterable[Path], candidate_paths: Iterable[Path],
                              lock: Path, harvest: Path | None = None, *,
                              report: Callable[[str], None] | None = None) -> tuple[_BatchPass | None, list[str]]:
    """Full shared gates plus strict single-run current QA for selected complete pairs."""
    from .workflow import validate_batches
    root = lock.parent.resolve()
    if lock.is_symlink():
        raise RecordError('batch acceptance lock is a symlink')
    units, candidates = list(unit_paths), list(candidate_paths)
    if not units or len(units) != len(candidates):
        raise RecordError('batch validation requires the same nonzero number of unit and candidate files')
    current_inputs().watch_root(root)
    preliminary = InputSnapshot(root)
    _active_provenance_pairs(preliminary, units, candidates)
    for path in [lock, *units, *candidates]:
        preliminary.read(path)
    _, errors = validate_batches(units, candidates, lock)
    if errors:
        return None, errors
    proof, errors = _shared_checks(root, harvest, report or (lambda _: None))
    if errors:
        return None, errors
    preliminary.assert_unchanged()
    pairs = _active_provenance_pairs(proof.snapshot, units, candidates)
    proof.snapshot.read(lock)
    proof.assert_valid(root, harvest)
    positions = []
    for _, candidate_path in pairs:
        matches = [value for (path, _), value in proof.adoptions.items()
                   if path == candidate_path.relative_to(root).as_posix()]
        if matches:
            frozen = matches[0]['input']
            order = [batch['candidates_path'] for batch in frozen['batches']]
            positions.append((frozen['adoption_id'], order.index(candidate_path.relative_to(root).as_posix())))
    for adoption_id in {identifier for identifier, _ in positions}:
        selected = [index for identifier, index in positions if identifier == adoption_id]
        if selected != sorted(set(selected)):
            raise RecordError('batch pairs must follow the complete frozen package order')
    current = CurrentSourceQA(root, harvest, snapshot=proof.snapshot)
    count, errors = current.validate_pairs(units, candidates)
    proof.assert_valid(root, harvest)
    if errors:
        return None, errors
    current._assert_pair_order()
    result = _BatchPass(proof, current, pairs, count, _ISSUER)
    _issue(result, (id(proof), id(current), pairs, count, _snapshot_claims(proof.snapshot), proof.reads.claims()))
    return result, []


@tracked_inputs
def validate_repository(root: Path, harvest: Path | None = None, *,
                        report: Callable[[str], None] | None = None) -> tuple[int, list[str]]:
    """Run complete schemas/provenance/decisions/current source QA once each.

    All lanes and runs remain separate pairs; no single-run batch restriction.
    """
    if root.is_symlink():
        raise RecordError('validation root is a symlink')
    root = root.resolve()
    emit = report or (lambda _: None)
    proof, errors = _shared_checks(root, harvest, emit)
    if errors:
        return 0, errors
    current = CurrentSourceQA(root, harvest, snapshot=proof.snapshot)
    count, errors = current.validate_repository()
    current.assert_unchanged()
    proof.assert_valid(root, harvest)
    if not errors:
        emit(f'Current locked source, Tags, protected structures and source terminology: PASS ({count} batches)')
    return count, errors
