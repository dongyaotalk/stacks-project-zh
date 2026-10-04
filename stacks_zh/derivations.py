from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .records import (
    RecordError, load_jsonl, restore_placeholders, sha256_value,
    stamp_unit_hashes, validate_records, PLACEHOLDER_TOKEN_RE,
)
from .schema_validation import validate_named_schema
from .model_corrections import load_repository_corrections

TOOL_ID = "stacks-zh-derive"
TOOL_VERSION = "1"
UNIT_FIELDS = {"source_text", "placeholders", "render"}
CANDIDATE_FIELDS = {"translation", "allowed_english", "term_occurrences", "unknown_terms", "notes"}


class DerivationError(RecordError):
    """A tool correction lacks reproducible, immutable evidence."""


def byte_hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def jsonl_bytes(records: list[dict[str, Any]]) -> bytes:
    return ("\n".join(json.dumps(clean(row), ensure_ascii=False, sort_keys=True)
                       for row in records) + "\n").encode("utf-8")


def clean(row: dict[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in row.items() if not key.startswith("_")}


def _path(root: Path, value: str, pattern: str) -> Path:
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise DerivationError(f"invalid derivation path: {value!r}")
    if any(part in {".", ".."} for part in Path(value).parts):
        raise DerivationError(f"unsafe derivation path: {value!r}")
    path = root / value
    if not path.resolve().is_relative_to(root.resolve()):
        raise DerivationError(f"derivation path escapes repository: {value}")
    if any(part.is_symlink() for part in [path, *path.parents] if part.is_relative_to(root)):
        raise DerivationError(f"derivation path is a symlink: {value}")
    return path


def _source_tex(unit: dict[str, Any]) -> str:
    return unit["render"]["prefix"] + restore_placeholders(unit, unit["source_text"]) + unit["render"]["suffix"]


def _git_origin_bytes(root: Path, commit: str, path: str) -> bytes:
    ancestry = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", commit, "HEAD"], capture_output=True)
    if ancestry.returncode:
        raise DerivationError("origin_commit must be a reachable ancestor of HEAD")
    result = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{path}"], capture_output=True)
    if result.returncode:
        raise DerivationError(f"origin_commit has no original file: {path}")
    return result.stdout


def _display_projection(unit: dict[str, Any], text: str) -> str:
    # Only bilingual English insertions, source structural controls, and the
    # explicitly fixed short footnote phrase may change in a tool derivation.
    text = restore_placeholders(unit, text)
    text = re.sub(r"（[\x20-\x7e]+）", "", text)
    text = text.replace("See Remark", "见注")
    text = re.sub(r"\\(?:[A-Za-z@]+|.)|[%#$&_^~{}]", "", text)
    return re.sub(r"\s+", "", text)


def _remap(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [_remap(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: _remap(item, mapping) for key, item in value.items()}
    return value


def replay_derivation(
    record: dict[str, Any], units: list[dict[str, Any]], candidates: list[dict[str, Any]],
    corrections: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Replay explicit corrections without mutating origin rows or run facts."""
    errors = validate_named_schema(record, "derivation.schema.json", "derivation")
    if errors:
        raise DerivationError("\n".join(errors))
    if record["tool"]["id"] != TOOL_ID or record["tool"]["version"] not in {TOOL_VERSION, "2"}:
        raise DerivationError("unsupported derivation tool/version")
    units = [clean(row) for row in units]
    candidates = [clean(row) for row in candidates]
    ids = [row["unit_id"] for row in units]
    if len(ids) != len(set(ids)) or [row["unit_id"] for row in candidates] != ids:
        raise DerivationError("origin unit/candidate IDs must be unique and ordered equally")
    if any("derivation_id" in row or "model_correction_id" in row for row in candidates):
        raise DerivationError("origin snapshot must contain raw model output, not another derivation")
    if any(row["source_commit"] != record["source_commit"] for row in units + candidates):
        raise DerivationError("derivation source_commit differs from origin")
    mapping = record["unit_id_map"]
    if set(mapping) != set(ids) or len(set(mapping.values())) != len(ids):
        raise DerivationError("unit_id_map must cover exactly the origin IDs without collisions")
    operations: dict[str, dict[str, Any]] = {}
    for op in record["operations"]:
        old_id = op["unit_id"]
        if old_id not in ids or old_id in operations:
            raise DerivationError("operation must name one unique origin unit")
        operations[old_id] = op
        if not op["kinds"] or not op["reason"].strip():
            raise DerivationError("operation needs a nonempty kind and reason")
        if not set(op["unit_updates"]) <= UNIT_FIELDS or not set(op["candidate_updates"]) <= CANDIDATE_FIELDS:
            raise DerivationError("operation changes immutable identity, status or approval fields")
        if bool(op.get("model_correction_id")) != ("model-revision" in op["kinds"]):
            raise DerivationError("model revision needs both a declared operation and correction ID")
        if op.get("model_correction_id") and record["tool"]["version"] != "2":
            raise DerivationError("model revision requires derivation tool version 2")
        if mapping[old_id] != old_id and "coordinates" not in op["kinds"]:
            raise DerivationError("coordinate change lacks a declared coordinate operation")
        if op["unit_updates"] and not set(op["kinds"]) & {"protected-extraction", "footnote-display"}:
            raise DerivationError("source extraction change lacks a declared operation")
        if op["candidate_updates"] and not set(op["kinds"]) & {"protected-extraction", "term-display", "footnote-display", "model-revision"}:
            raise DerivationError("candidate display change lacks a declared operation")
    if any(mapping[old_id] != old_id and old_id not in operations for old_id in ids):
        raise DerivationError("coordinate change has no operation/reason")
    new_units, new_candidates = [], []
    for old_unit, old_candidate in zip(units, candidates, strict=True):
        old_id = old_unit["unit_id"]
        op = operations.get(old_id, {"unit_updates": {}, "candidate_updates": {}})
        unit, candidate = copy.deepcopy(old_unit), copy.deepcopy(old_candidate)
        unit.update(copy.deepcopy(op["unit_updates"]))
        candidate.update(copy.deepcopy(op["candidate_updates"]))
        for field, text in (("source_text", unit["source_text"]), ("translation", candidate["translation"])):
            if re.search(r"\\(?:[A-Za-z@]+|.)|[%#$&_^~{}]", PLACEHOLDER_TOKEN_RE.sub("", text)):
                raise DerivationError(f"{old_id}: derived {field} has unprotected TeX controls")
        try:
            if _source_tex(unit) != _source_tex(old_unit):
                raise DerivationError(f"{old_id}: tool operation changes source TeX")
            correction_id = op.get("model_correction_id")
            if correction_id:
                current_unit = stamp_unit_hashes({**unit, "unit_id": mapping[old_id]})
                evidence = (corrections or {}).get((correction_id, current_unit["unit_id"]))
                if evidence is None:
                    raise DerivationError(f"{old_id}: model revision has no validated frozen output")
                correction, raw = evidence["record"], evidence["candidate"]
                if (correction["derivation_ids"].get(current_unit["unit_id"]) != record["derivation_id"]
                        or correction["source_commit"] != record["source_commit"]
                        or evidence["unit"] != current_unit):
                    raise DerivationError(f"{old_id}: correction has a different source, unit or derivation")
                if raw["context"].get("revision_input") != {"kind": "candidate-to-revise", "candidate": old_candidate, "source_unit": old_unit}:
                    raise DerivationError(f"{old_id}: model revision did not freeze this exact original candidate")
                if any(candidate[field] != raw[field] for field in CANDIDATE_FIELDS):
                    raise DerivationError(f"{old_id}: current text/metadata differs from frozen model output")
                candidate["model_correction_id"] = correction_id
                candidate["term_status"] = raw["term_status"]
            elif _display_projection(unit, candidate["translation"]) != _display_projection(old_unit, old_candidate["translation"]):
                raise DerivationError(f"{old_id}: tool operation freely rewrites translation")
        except (KeyError, TypeError) as exc:
            raise DerivationError(f"{old_id}: malformed extraction/display correction") from exc
        if candidate.get("unknown_terms"):
            candidate["term_status"] = "DECISION_REQUIRED"
        # Never confer a term approval or a critic/human-review stage.
        if candidate.get("term_occurrences") and not candidate.get("unknown_terms") and not correction_id:
            raise DerivationError(f"{old_id}: declared terms need pending evidence in a tool derivation")
        candidate["stage"] = "STRUCTURE_OK" if candidate["term_status"] == "DECISION_REQUIRED" else "TERM_OK"
        candidate["qa_status"] = "PASS"
        unit["unit_id"] = mapping[old_id]
        unit = stamp_unit_hashes(unit)
        candidate["unit_id"] = unit["unit_id"]
        candidate["source_text_hash"] = unit["source_text_hash"]
        candidate["context"] = _remap(candidate["context"], mapping)
        candidate["context_hash"] = sha256_value(candidate["context"])
        candidate["translation_hash"] = sha256_value(candidate["translation"])
        candidate["derivation_id"] = record["derivation_id"]
        new_units.append(unit)
        new_candidates.append(candidate)
    errors = validate_records(new_units, new_candidates, record["source_commit"])
    if errors:
        raise DerivationError("derived QA failed:\n" + "\n".join(errors))
    return new_units, new_candidates


def load_repository_derivations(
    root: Path, corrections: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[str]]:
    """Return original candidates for run validation after checking every replay."""
    origins: dict[tuple[str, str], dict[str, Any]] = {}
    errors: list[str] = []
    if corrections is None:
        corrections, correction_errors = load_repository_corrections(root)
        errors.extend(correction_errors)
    used_corrections: set[tuple[str, str]] = set()
    seen_outputs: set[str] = set()
    seen_snapshots: set[str] = set()
    for path in sorted((root / "translation-data/derivations").glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            schema_errors = validate_named_schema(record, "derivation.schema.json", str(path))
            if schema_errors:
                raise DerivationError("\n".join(schema_errors))
            derivation_id = record["derivation_id"]
            if path.stem != derivation_id:
                raise DerivationError("derivation filename differs from ID")
            input_pattern = rf"translation-data/retired/derivations/{re.escape(derivation_id)}/(?:units|candidates)\.jsonl"
            entries = record["files"]
            resolved = {}
            for key, pattern in (
                ("input_units", input_pattern), ("input_candidates", input_pattern),
                ("output_units", r"translation-data/units/[A-Za-z0-9._-]+\.jsonl"),
                ("output_candidates", r"translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl"),
            ):
                entry = entries[key]
                resolved[key] = _path(root, entry["path"], pattern)
                if byte_hash(resolved[key].read_bytes()) != entry["hash"]:
                    raise DerivationError(f"{key}: file hash mismatch")
            if resolved["input_units"].name != "units.jsonl" or resolved["input_candidates"].name != "candidates.jsonl":
                raise DerivationError("snapshot roles are reversed")
            if resolved["output_units"].name != resolved["output_candidates"].name:
                raise DerivationError("active unit/candidate batch names differ")
            for key in ("output_units", "output_candidates"):
                value = entries[key]["path"]
                if value in seen_outputs:
                    raise DerivationError("active file belongs to multiple derivations")
                seen_outputs.add(value)
            for key in ("input_units", "input_candidates"):
                value = entries[key]["path"]
                if value in seen_snapshots:
                    raise DerivationError("snapshot belongs to multiple derivations")
                seen_snapshots.add(value)
            units = load_jsonl(resolved["input_units"])
            raw_candidates = load_jsonl(resolved["input_candidates"])
            for input_role, output_role in (("input_units", "output_units"), ("input_candidates", "output_candidates")):
                if resolved[input_role].read_bytes() != _git_origin_bytes(root, record["origin_commit"], entries[output_role]["path"]):
                    raise DerivationError(f"{input_role}: snapshot differs from original Git bytes")
            for run_id in {candidate.get("run_id") for candidate in raw_candidates}:
                if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", run_id) or ".." in run_id:
                    raise DerivationError("origin candidate has invalid run ID")
                run_path = f"translation-data/runs/{run_id}.json"
                if (root / run_path).read_bytes() != _git_origin_bytes(root, record["origin_commit"], run_path):
                    raise DerivationError(f"{run_path}: original run bytes have changed")
            derived_units, derived_candidates = replay_derivation(record, units, raw_candidates, corrections)
            for key, rows in (("output_units", derived_units), ("output_candidates", derived_candidates)):
                if jsonl_bytes(rows) != resolved[key].read_bytes():
                    raise DerivationError(f"{key}: active output does not match replay")
            for raw, derived in zip(raw_candidates, derived_candidates, strict=True):
                key = (entries["output_candidates"]["path"], derived["unit_id"])
                origins[key] = clean(raw)
                if derived.get("model_correction_id"):
                    correction_key = (derived["model_correction_id"], derived["unit_id"])
                    if correction_key in used_corrections:
                        raise DerivationError("frozen model correction is applied more than once")
                    used_corrections.add(correction_key)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{path}: {exc}")
    for path in sorted((root / "translation-data/retired/derivations").glob("*/*.jsonl")):
        if path.relative_to(root).as_posix() not in seen_snapshots:
            errors.append(f"{path}: orphaned raw derivation snapshot")
    for correction_key in corrections.keys() - used_corrections:
        errors.append(f"model correction {correction_key}: frozen output has no active derived candidate")
    for path in sorted((root / "translation-data/candidates").glob("*/*.jsonl")):
        try:
            for row in load_jsonl(path):
                key = (path.relative_to(root).as_posix(), row["unit_id"])
                if "derivation_id" in row and key not in origins:
                    errors.append(f"{path}: {row['unit_id']}: derivation has no valid replay")
                if "model_correction_id" in row and (key not in origins or not row.get("derivation_id")):
                    errors.append(f"{path}: {row['unit_id']}: model correction has no valid derivation")
        except (RecordError, KeyError) as exc:
            errors.append(str(exc))
    return origins, errors
