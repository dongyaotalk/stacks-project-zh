from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ProvenanceError(ValueError):
    """Raised when a candidate cannot be tied to its immutable run manifest."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ProvenanceError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProvenanceError(f"{path}: manifest must be an object")
    return value


def validate_repository_provenance(root: Path) -> list[str]:
    runs_root = root / "translation-data" / "runs"
    candidates_root = root / "translation-data" / "candidates"
    manifests: dict[str, tuple[Path, dict[str, Any]]] = {}
    candidate_context_hashes: dict[str, list[str]] = {}
    errors: list[str] = []
    harness_registry = (root / "config" / "harnesses.yml").read_text(encoding="utf-8") if (root / "config" / "harnesses.yml").is_file() else ""
    model_registry = (root / "config" / "models.yml").read_text(encoding="utf-8") if (root / "config" / "models.yml").is_file() else ""
    for manifest_path in sorted(runs_root.glob("*.json")):
        try:
            manifest = _read_json(manifest_path)
        except ProvenanceError as exc:
            errors.append(str(exc))
            continue
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

    for candidate_path in sorted(candidates_root.glob("*/*.jsonl")):
        lane = candidate_path.parent.name
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
            if candidate.get("source_commit") != manifest.get("source_commit"):
                errors.append(f"{location}: source_commit does not match {manifest_path}")
            model = manifest.get("model")
            harness = manifest.get("harness")
            if not isinstance(model, dict) or not isinstance(harness, dict):
                errors.append(f"{manifest_path}: model and harness objects are required")
                continue
            for key in ("model_record_id", "harness_id"):
                expected = model.get("record_id") if key == "model_record_id" else harness.get("id")
                if candidate.get(key) != expected:
                    errors.append(f"{location}: {key} does not match {manifest_path}")
            if candidate.get("model_id") not in {model.get("requested_id"), model.get("resolved_id")}:
                errors.append(f"{location}: model_id does not match {manifest_path}")
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
    return errors
