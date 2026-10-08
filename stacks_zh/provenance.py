from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .derivations import load_repository_derivations
from .model_corrections import load_repository_corrections
from .schema_validation import validate_named_schema


class ProvenanceError(ValueError):
    """Raised when a candidate cannot be tied to its immutable run manifest."""


def _parse_registry_section(text: str, section: str) -> dict[str, dict[str, str]]:
    """Read a fixed-shape two-level registry without adding a YAML dependency."""
    records: dict[str, dict[str, str]] = {}
    in_section = False
    current: str | None = None
    for line in text.splitlines():
        if line and not line[0].isspace() and line.strip().endswith(":"):
            in_section = line.strip() == f"{section}:"
            current = None
            continue
        record_match = re.match(r"^  (.+):\s*$", line)
        if in_section and record_match:
            current = record_match.group(1)
            records[current] = {}
            continue
        field_match = re.match(r"^    ([A-Za-z0-9_]+):\s*(.*?)\s*$", line)
        if in_section and current and field_match:
            value = field_match.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            records[current][field_match.group(1)] = value
    return records


def _registry_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProvenanceError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProvenanceError(f"{path}: manifest must be an object")
    return value


def validate_repository_provenance(root: Path, harvest: Path | None = None) -> list[str]:
    runs_root = root / "translation-data" / "runs"
    candidates_root = root / "translation-data" / "candidates"
    manifests: dict[str, tuple[Path, dict[str, Any]]] = {}
    candidate_context_hashes: dict[str, list[str]] = {}
    corrections, errors = load_repository_corrections(root)
    origins, derivation_errors = load_repository_derivations(root, corrections, harvest)
    errors.extend(derivation_errors)
    typed_active = {}
    typed_seen = set()
    for unit_file in sorted((root / 'translation-data/units').glob('*.jsonl')):
        try:
            rows = [json.loads(line) for line in unit_file.read_text(encoding='utf-8').splitlines() if line.strip()]
            if any(not isinstance(row, dict) for row in rows):
                raise ProvenanceError('active unit records must be objects')
            typed_active[unit_file.name] = {u['unit_id'] for u in rows if u.get('schema_version') == 2}
            if typed_active[unit_file.name]:
                from .source_containers import safe_path
                safe_path(root, unit_file.relative_to(root).as_posix(),
                          r'translation-data/units/[A-Za-z0-9._-]+\.jsonl')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f'{unit_file}: cannot inspect typed math adoption: {exc}')
    harness_registry = (root / "config" / "harnesses.yml").read_text(encoding="utf-8") if (root / "config" / "harnesses.yml").is_file() else ""
    model_registry = (root / "config" / "models.yml").read_text(encoding="utf-8") if (root / "config" / "models.yml").is_file() else ""
    model_lanes = _parse_registry_section(model_registry, "lanes")
    model_records = _parse_registry_section(model_registry, "model_records")
    harness_records = _parse_registry_section(harness_registry, "harnesses")
    for manifest_path in sorted(runs_root.glob("*.json")):
        try:
            manifest = _read_json(manifest_path)
        except ProvenanceError as exc:
            errors.append(str(exc))
            continue
        errors.extend(
            validate_named_schema(
                manifest, "run-manifest.schema.json", str(manifest_path)
            )
        )
        run_id = manifest.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            errors.append(f"{manifest_path}: missing run_id")
            continue
        if manifest.get("schema_version") != 1:
            errors.append(f"{manifest_path}: schema_version must be 1")
        if manifest.get("run_kind") not in {"translation", "revision", "comparison", "historical-import"}:
            errors.append(f"{manifest_path}: invalid run_kind")
        if not isinstance(manifest.get("source_commit"), str) or len(manifest["source_commit"]) != 40:
            errors.append(f"{manifest_path}: source_commit must be a full SHA")
        if not isinstance(manifest.get("unit_ids"), list) or not manifest["unit_ids"]:
            errors.append(f"{manifest_path}: unit_ids must be a non-empty array")
        if not isinstance(manifest.get("inputs"), dict):
            errors.append(f"{manifest_path}: inputs object is required")
        if not isinstance(manifest.get("created_at"), str) or not manifest["created_at"]:
            errors.append(f"{manifest_path}: created_at is required")
        if not isinstance(manifest.get("replayable"), bool):
            errors.append(f"{manifest_path}: replayable must be boolean")
        if run_id in manifests:
            errors.append(f"duplicate run manifest: {run_id}")
        manifests[run_id] = (manifest_path, manifest)

    correction_paths = {entry['candidate_path']: entry['candidate']['model_lane'] for entry in corrections.values()}
    expanded = []
    seen_origins = set()
    for candidate_path in [*sorted(candidates_root.glob("*/*.jsonl")), *sorted(correction_paths)]:
        lane = correction_paths.get(candidate_path, candidate_path.parent.name)
        try:
            lines = candidate_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"cannot read {candidate_path}: {exc}")
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            location = f"{candidate_path}:{line_number}"
            try:
                candidate = json.loads(line)
            except ValueError as exc:
                errors.append(f"{location}: invalid JSON: {exc}")
                continue
            if not isinstance(candidate, dict):
                errors.append(f"{location}: candidate must be an object")
                continue
            if (candidate_path.parent.parent == candidates_root
                    and candidate.get('unit_id') in typed_active.get(candidate_path.name, set())):
                typed_seen.add((candidate_path.name, candidate['unit_id']))
                identifier = candidate.get('derivation_id')
                try:
                    from .source_containers import safe_path
                    safe_path(root, candidate_path.relative_to(root).as_posix(),
                              r'translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl')
                    if (not isinstance(identifier, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', identifier)
                            or '..' in identifier or (candidate_path.relative_to(root).as_posix(), candidate['unit_id']) not in origins
                            or _read_json(root / 'translation-data/derivations' / (identifier + '.json'))['tool']['version'] != '4'):
                        raise ProvenanceError('active unit-v2 requires validated v4/source-container-v3 adoption')
                except (ValueError, KeyError, TypeError) as exc:
                    errors.append(f'{location}: {exc}')
            if candidate.get("derivation_id"):
                origin = origins.get((candidate_path.relative_to(root).as_posix(), candidate.get("unit_id")))
                if origin is None:
                    errors.append(f"{location}: missing validated original candidate")
                    continue
                for original in origin.get('_all_origins', [origin]):
                    identity = (original.get('run_id'), original.get('unit_id'), original.get('context_hash'))
                    if identity not in seen_origins:
                        seen_origins.add(identity)
                        expanded.append((location, lane, original))
            else:
                expanded.append((location, lane, candidate))
    for location, lane, candidate in expanded:
        if candidate.get("schema_version") != 2:
            errors.append(f"{location}: candidate must use schema_version 2")
            continue
        run_id = candidate.get("run_id")
        if not isinstance(run_id, str) or run_id not in manifests:
            errors.append(f"{location}: run_id has no manifest: {run_id!r}")
            continue
        manifest_path, manifest = manifests[run_id]
        if candidate.get("model_lane") != lane:
            errors.append(f"{location}: model_lane does not match candidate directory")
        lane_config = model_lanes.get(lane)
        if model_lanes and lane_config is None:
            errors.append(f"{location}: model lane is not registered: {lane!r}")
        elif lane_config is not None:
            for field in ("model_id", "model_record_id", "harness_id", "prompt_version"):
                expected = lane_config.get(field)
                if expected and candidate.get(field) != expected:
                    errors.append(
                        f"{location}: {field} does not match config/models.yml lane {lane}"
                    )
        if candidate.get("source_commit") != manifest.get("source_commit"):
            errors.append(f"{location}: source_commit does not match {manifest_path}")
        model = manifest.get("model")
        harness = manifest.get("harness")
        if not isinstance(model, dict) or not isinstance(harness, dict):
            errors.append(f"{manifest_path}: model and harness objects are required")
            continue
        model_record = model_records.get(str(model.get("record_id", "")))
        if model_records and model_record is None:
            errors.append(f"{manifest_path}: model.record_id is not registered")
        elif model_record is not None:
            for field in (
                "provider",
                "requested_id",
                "resolved_id",
                "snapshot",
                "identity_confidence",
            ):
                expected = model_record.get(field)
                if expected is not None and _registry_scalar(model.get(field)) != expected:
                    errors.append(
                        f"{manifest_path}: model.{field} does not match config/models.yml"
                    )
        harness_record = harness_records.get(str(harness.get("id", "")))
        if harness_records and harness_record is None:
            errors.append(f"{manifest_path}: harness.id is not registered")
        elif harness_record is not None:
            expected_adapter = harness_record.get("adapter_version")
            if expected_adapter and harness.get("adapter_version") != expected_adapter:
                errors.append(
                    f"{manifest_path}: harness.adapter_version does not match config/harnesses.yml"
                )
        for key in ("model_record_id", "harness_id"):
            expected = model.get("record_id") if key == "model_record_id" else harness.get("id")
            if candidate.get(key) != expected:
                errors.append(f"{location}: {key} does not match {manifest_path}")
        for candidate_field, expected in (
            ("harness_version", harness.get("version")),
            ("model_snapshot", model.get("snapshot")),
            ("model_identity_confidence", model.get("identity_confidence")),
            ("created_at", manifest.get("created_at")),
        ):
            if candidate.get(candidate_field) != expected:
                errors.append(
                    f"{location}: {candidate_field} does not match {manifest_path}"
                )
        if candidate.get("model_id") not in {model.get("requested_id"), model.get("resolved_id")}:
            errors.append(f"{location}: model_id does not match {manifest_path}")
        inputs = manifest.get("inputs")
        if isinstance(inputs, dict):
            for field in ("prompt_version", "glossary_revision"):
                if candidate.get(field) != inputs.get(field):
                    errors.append(f"{location}: {field} does not match {manifest_path}")
        context = candidate.get("context")
        if isinstance(context, dict) and context.get("prompt_version") != candidate.get("prompt_version"):
            errors.append(f"{location}: context.prompt_version does not match candidate")
        if isinstance(context, dict) and isinstance(inputs, dict):
            for field in ("policy_revision", "source_commit"):
                expected = inputs.get(field) if field == "policy_revision" else manifest.get(field)
                if context.get(field) != expected:
                    errors.append(f"{location}: context.{field} does not match {manifest_path}")
        if harness_registry and f"{candidate.get('harness_id')}:" not in harness_registry:
            errors.append(f"{location}: harness_id is not registered: {candidate.get('harness_id')!r}")
        if model_registry and f"{candidate.get('model_record_id')}:" not in model_registry:
            errors.append(f"{location}: model_record_id is not registered: {candidate.get('model_record_id')!r}")
        unit_ids = manifest.get("unit_ids", [])
        if candidate.get("unit_id") not in unit_ids:
            errors.append(f"{location}: unit_id is absent from {manifest_path}")
        context_hash = candidate.get("context_hash")
        if isinstance(context_hash, str):
            candidate_context_hashes.setdefault(run_id, []).append(context_hash)
    for run_id, (manifest_path, manifest) in manifests.items():
        inputs = manifest.get("inputs")
        if not isinstance(inputs, dict) or "context_hashes" not in inputs:
            continue
        expected = inputs.get("context_hashes")
        if expected != candidate_context_hashes.get(run_id, []):
            errors.append(
                f"{manifest_path}: inputs.context_hashes does not match candidate records"
            )
    for batch, identifiers in typed_active.items():
        for identifier in sorted(identifiers):
            if (batch, identifier) not in typed_seen:
                errors.append(f'{batch}: active unit-v2 requires a validated candidate: {identifier}')
    return errors
