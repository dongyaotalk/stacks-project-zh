"""One live repository acceptance session; no persistent pass cache or skip flag."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .current_qa import InputSnapshot, CurrentSourceQA
from .records import RecordError
from .provenance import validate_repository_provenance
from .schema_validation import validate_repository_schemas

_ISSUER = object()


@dataclass(frozen=True)
class _ProvenancePass:
    """Internal capability issued only after this invocation actually validates."""
    root: Path
    snapshot: InputSnapshot
    _issuer: object

    def assert_valid(self, root: Path) -> None:
        if self._issuer is not _ISSUER or self.root != root.resolve() or self.snapshot.root != self.root:
            raise RecordError('provenance result is not from this live repository session')
        self.snapshot.assert_unchanged()


def _require_live_provenance(result: object, root: Path) -> None:
    if not isinstance(result, _ProvenancePass):
        raise RecordError('decision validation requires an actual live provenance result')
    result.assert_valid(root)


def validate_repository(root: Path, harvest: Path | None = None, *,
                        report: Callable[[str], None] | None = None) -> tuple[int, list[str]]:
    """Run complete schemas/provenance/decisions/current source QA once each."""
    # Import before the snapshot: Python bytecode caches are generated output,
    # while every .py input and all policy/fact paths remain watched.
    from .decisions import validate_repository_decisions
    root = root.resolve()
    snapshot = InputSnapshot(root)
    snapshot.watch_repository()
    emit = report or (lambda _: None)
    errors = validate_repository_schemas(root)
    snapshot.assert_unchanged()
    if errors:
        return 0, errors
    emit('Repository JSON Schema: PASS')
    errors = validate_repository_provenance(root, harvest)
    snapshot.assert_unchanged()
    if errors:
        return 0, errors
    proof = _ProvenancePass(root, snapshot, _ISSUER)
    emit('Model provenance: PASS (one complete historical replay in this invocation)')
    errors = validate_repository_decisions(root, harvest, _provenance=proof)
    snapshot.assert_unchanged()
    if errors:
        return 0, errors
    emit('Selection and revision linkage: PASS')
    current = CurrentSourceQA(root, harvest, snapshot=snapshot)
    count, errors = current.validate_repository()
    current.assert_unchanged()
    if not errors:
        emit(f'Current locked source, Tags, protected structures and source terminology: PASS ({count} batches)')
    return count, errors
