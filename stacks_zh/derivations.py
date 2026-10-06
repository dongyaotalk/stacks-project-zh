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
from .model_corrections import load_repository_corrections, _first_addition_is_immutable
from .derivation_archives import load_derivation_archives
from .source_reextractions import load_source_reextractions, validate_reextraction_operation

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
    previous_outputs: tuple[list[dict[str, Any]], list[dict[str, Any]]] | None = None,
    source_reextractions: dict[str, dict[str, Any]] | None = None,
    source_containers: dict[str, dict[str, Any]] | None = None,
    tags: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Replay explicit corrections without mutating origin rows or run facts."""
    errors = validate_named_schema(record, "derivation.schema.json", "derivation")
    if errors:
        raise DerivationError("\n".join(errors))
    version = record["tool"]["version"]
    if version == '4':
        from .group_derivations import replay_groups
        if tags is None:
            raise DerivationError('v4 replay requires independently locked permanent Tags')
        return replay_groups(record, units, candidates, corrections, previous_outputs, source_containers, tags)
    if record["tool"]["id"] != TOOL_ID or version not in {TOOL_VERSION, "2", "3"}:
        raise DerivationError("unsupported derivation tool/version")
    units = [clean(row) for row in units]
    candidates = [clean(row) for row in candidates]
    ids = [row["unit_id"] for row in units]
    if len(ids) != len(set(ids)) or [row["unit_id"] for row in candidates] != ids:
        raise DerivationError("origin unit/candidate IDs must be unique and ordered equally")
    if version == "3":
        previous = record.get("previous_derivation_id")
        if (not previous or previous == record["derivation_id"] or previous_outputs is None
                or units != [clean(row) for row in previous_outputs[0]]
                or candidates != [clean(row) for row in previous_outputs[1]]
                or any(row.get("derivation_id") != previous for row in candidates)):
            raise DerivationError("v3 requires exact validated previous derived output")
    elif record.get("previous_derivation_id") or previous_outputs is not None:
        raise DerivationError("v1/v2 cannot declare a previous derivation")
    elif any("derivation_id" in row or "model_correction_id" in row for row in candidates):
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
        if op.get("model_correction_id") and version not in {"2", "3"}:
            raise DerivationError("model revision requires derivation tool version 2 or 3")
        if op.get("source_reextraction_id") and (version not in {"2", "3"}
                or not op.get("model_correction_id") or "protected-extraction" not in op["kinds"]
                or set(op["candidate_updates"]) != CANDIDATE_FIELDS):
            raise DerivationError("source re-extraction requires v2/v3 protected extraction and a complete actual model revision")
        if mapping[old_id] != old_id and "coordinates" not in op["kinds"]:
            raise DerivationError("coordinate change lacks a declared coordinate operation")
        if op["unit_updates"] and not set(op["kinds"]) & {"protected-extraction", "footnote-display"}:
            raise DerivationError("source extraction change lacks a declared operation")
        if op["candidate_updates"] and not set(op["kinds"]) & {"protected-extraction", "term-display", "footnote-display", "model-revision"}:
            raise DerivationError("candidate display change lacks a declared operation")
    if version == "3" and (set(operations) != set(ids) or any(
            not operations[old_id].get("model_correction_id")
            or set(operations[old_id]["candidate_updates"]) != CANDIDATE_FIELDS for old_id in ids)):
        raise DerivationError("v3 requires a complete actual model revision for every previous unit")
    if any(mapping[old_id] != old_id and old_id not in operations for old_id in ids):
        raise DerivationError("coordinate change has no operation/reason")
    new_units, new_candidates = [], []
    for old_unit, old_candidate in zip(units, candidates, strict=True):
        old_id = old_unit["unit_id"]
        op = operations.get(old_id, {"unit_updates": {}, "candidate_updates": {}})
        unit, candidate = copy.deepcopy(old_unit), copy.deepcopy(old_candidate)
        candidate.pop('unit_group_id', None)
        unit.update(copy.deepcopy(op["unit_updates"]))
        candidate.update(copy.deepcopy(op["candidate_updates"]))
        for field, text in (("source_text", unit["source_text"]), ("translation", candidate["translation"])):
            if re.search(r"\\(?:[A-Za-z@]+|.)|[%#$&_^~{}]", PLACEHOLDER_TOKEN_RE.sub("", text)):
                raise DerivationError(f"{old_id}: derived {field} has unprotected TeX controls")
        try:
            reextraction_id = op.get("source_reextraction_id")
            if reextraction_id:
                source_evidence = (source_reextractions or {}).get(reextraction_id)
                if source_evidence is None:
                    raise DerivationError(f"{old_id}: source re-extraction has no validated locked-Git evidence")
                validate_reextraction_operation(source_evidence, record, units, old_unit,
                                               stamp_unit_hashes({**unit, "unit_id": mapping[old_id]}))
            elif _source_tex(unit) != _source_tex(old_unit):
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
    harvest: Path | None = None,
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[str]]:
    """Validate every historical replay and return ultimate origins of leaves."""
    origins, errors = {}, []
    if corrections is None:
        corrections, correction_errors = load_repository_corrections(root)
        errors.extend(correction_errors)
    archives, archive_errors = load_derivation_archives(root)
    errors.extend(archive_errors)
    reextractions, reextraction_errors = load_source_reextractions(root, harvest)
    errors.extend(reextraction_errors)
    from .source_containers import load_source_containers
    from .group_derivations import correction_bindings, restoration_bindings
    restorations, restoration_errors = load_source_containers(root, harvest)
    errors.extend(restoration_errors)
    records = {}
    for path in sorted((root / "translation-data/derivations").glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            schema_errors = validate_named_schema(record, "derivation.schema.json", str(path))
            if schema_errors:
                raise DerivationError("\n".join(schema_errors))
            if path.stem != record["derivation_id"] or ".." in path.stem:
                raise DerivationError("derivation filename differs from ID or is unsafe")
            _path(root, path.relative_to(root).as_posix(), r"translation-data/derivations/[A-Za-z0-9._-]+\.json")
            _first_addition_is_immutable(root, path)
            records[path.stem] = record
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{path}: {exc}")
    used_corrections = set()
    used_reextractions = set()
    used_restorations = set()
    tags = None
    if any(r['tool']['version'] == '4' for r in records.values()):
        from .source_reextractions import LockedEnglish
        try:
            tags = LockedEnglish(root, harvest).tags
        except (OSError, ValueError) as exc:
            errors.append(f'v4 locked permanent Tags: {exc}')
    seen_snapshots, seen_outputs = set(), set()
    cache, visiting, failed = {}, set(), set()

    def visit(identifier):
        if identifier in cache:
            return cache[identifier]
        if identifier in visiting:
            raise DerivationError("cyclic derivation history")
        if identifier in failed or identifier not in records:
            raise DerivationError("derivation has no valid predecessor record")
        visiting.add(identifier)
        record = records[identifier]
        try:
            entries, resolved = record["files"], {}
            input_pattern = rf"translation-data/retired/derivations/{re.escape(identifier)}/(?:units|candidates)\.jsonl"
            for role in ("input_units", "input_candidates"):
                entry = entries[role]
                resolved[role] = _path(root, entry["path"], input_pattern)
                if byte_hash(resolved[role].read_bytes()) != entry["hash"]:
                    raise DerivationError(f"{role}: file hash mismatch")
                _first_addition_is_immutable(root, resolved[role])
                if entry["path"] in seen_snapshots:
                    raise DerivationError("snapshot belongs to multiple derivations")
                seen_snapshots.add(entry["path"])
            if resolved["input_units"].name != "units.jsonl" or resolved["input_candidates"].name != "candidates.jsonl":
                raise DerivationError("snapshot roles are reversed")
            for role, pattern in [("output_units", r"translation-data/units/[A-Za-z0-9._-]+\.jsonl"),
                                  ("output_candidates", r"translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl")]:
                logical = _path(root, entries[role]["path"], pattern)
                if identifier in archives:
                    resolved[role] = archives[identifier]["outputs"][role]
                    seen_snapshots.add(resolved[role].relative_to(root).as_posix())
                else:
                    resolved[role] = logical
                    if entries[role]["path"] in seen_outputs:
                        raise DerivationError("active file belongs to multiple derivations")
                    seen_outputs.add(entries[role]["path"])
                if byte_hash(resolved[role].read_bytes()) != entries[role]["hash"]:
                    raise DerivationError(f"{role}: file hash mismatch")
            if Path(entries["output_units"]["path"]).name != Path(entries["output_candidates"]["path"]).name:
                raise DerivationError("active unit/candidate batch names differ")
            units = load_jsonl(resolved["input_units"])
            candidates = load_jsonl(resolved["input_candidates"])
            previous_outputs = parent_origins = None
            if record["tool"]["version"] == "3" or record.get('previous_derivation_id') and record['tool']['version'] == '4':
                previous = record.get("previous_derivation_id")
                if previous not in archives:
                    raise DerivationError("v3 predecessor has no validated archive")
                archive = archives[previous]["manifest"]
                if archive["successor_derivation_id"] != identifier or archive["origin_commit"] != record["origin_commit"]:
                    raise DerivationError("archive has a different successor/origin commit")
                parent = records.get(previous)
                if parent is None or any(parent["files"][role]["path"] != entries[role]["path"] for role in ("output_units", "output_candidates")):
                    raise DerivationError("v3 must replace the same complete logical batch")
                parent_units, parent_candidates, parent_origins = visit(previous)
                previous_outputs = (parent_units, parent_candidates)
            for input_role, output_role in [("input_units", "output_units"), ("input_candidates", "output_candidates")]:
                if resolved[input_role].read_bytes() != _git_origin_bytes(root, record["origin_commit"], entries[output_role]["path"]):
                    raise DerivationError(f"{input_role}: snapshot differs from original Git bytes")
            if parent_origins is None:
                raw_origins = {row["unit_id"]: clean(row) for row in candidates}
            else:
                raw_origins = parent_origins
            all_origins = [origin for candidate in raw_origins.values()
                           for origin in candidate.get('_all_origins', [candidate])]
            for run_id in {candidate.get("run_id") for candidate in all_origins}:
                if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", run_id) or ".." in run_id:
                    raise DerivationError("origin candidate has invalid run ID")
                run_path = f"translation-data/runs/{run_id}.json"
                if (root / run_path).read_bytes() != _git_origin_bytes(root, record["origin_commit"], run_path):
                    raise DerivationError(f"{run_path}: original run bytes have changed")
            output_units, output_candidates = replay_derivation(record, units, candidates, corrections,
                                                                previous_outputs, reextractions, restorations, tags)
            for role, rows in [("output_units", output_units), ("output_candidates", output_candidates)]:
                if jsonl_bytes(rows) != resolved[role].read_bytes():
                    raise DerivationError(f"{role}: active output does not match replay")
            mapped_origins = {}
            for operation in record.get('operations', []):
                identifier_used = operation.get('source_reextraction_id')
                if identifier_used:
                    if identifier_used in used_reextractions:
                        raise DerivationError('source re-extraction is applied more than once')
                    used_reextractions.add(identifier_used)
            if record['tool']['version'] == '4':
                for group in record['unit_groups']:
                    anchor = clean(raw_origins[group['identity_anchor']])
                    combined = {}
                    for old_id in group['input_unit_ids']:
                        prior_origin = raw_origins[old_id]
                        for origin in prior_origin.get('_all_origins', [prior_origin]):
                            origin = clean(origin)
                            combined[sha256_value(origin)] = origin
                    for new_id in group['output_unit_ids']:
                        mapped_origins[new_id] = {**copy.deepcopy(anchor), '_all_origins': list(combined.values())}
            else:
                for previous_candidate, output in zip(candidates, output_candidates, strict=True):
                    mapped_origins[output['unit_id']] = raw_origins[previous_candidate['unit_id']]
            for key in correction_bindings(record):
                if key in used_corrections:
                    raise DerivationError('frozen model correction is applied more than once')
                used_corrections.add(key)
            for restoration_id in restoration_bindings(record):
                if restoration_id in used_restorations:
                    raise DerivationError('source container is applied more than once')
                used_restorations.add(restoration_id)
            result = output_units, output_candidates, mapped_origins
            cache[identifier] = result
            return result
        except (OSError, ValueError, KeyError, TypeError):
            failed.add(identifier)
            raise
        finally:
            visiting.remove(identifier)

    for identifier in records:
        try:
            units, candidates, raw_origins = visit(identifier)
            if identifier not in archives:
                for candidate in candidates:
                    key = (records[identifier]["files"]["output_candidates"]["path"], candidate["unit_id"])
                    origins[key] = copy.deepcopy(raw_origins[candidate['unit_id']])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"translation-data/derivations/{identifier}.json: {exc}")
    for prior, entry in archives.items():
        successor = entry["manifest"]["successor_derivation_id"]
        if prior not in cache or successor not in cache or records[successor].get("previous_derivation_id") != prior:
            errors.append(f"archive {prior}: missing valid direct successor/replay")
    for path in sorted((root / "translation-data/retired/derivations").glob("*/*.jsonl")):
        if path.relative_to(root).as_posix() not in seen_snapshots:
            errors.append(f"{path}: orphaned raw derivation snapshot")
    for key in corrections.keys() - used_corrections:
        errors.append(f"model correction {key}: frozen output has no active derived candidate or validated historical replay")
    for identifier in reextractions.keys() - used_reextractions:
        errors.append(f"source re-extraction {identifier}: evidence has no validated historical replay")
    for identifier in restorations.keys() - used_restorations:
        errors.append(f'source-container restoration {identifier}: evidence has no validated historical replay')
    # OWNARGEND is the complete-container lowering's role, not a new permission
    # for raw historical units to claim an arbitrary complex title boundary.
    owned_units = [unit for identifier in used_restorations
                   for unit in restorations[identifier]['record']['new_units']]
    for path in sorted((root / 'translation-data/units').glob('*.jsonl')):
        try:
            for row in load_jsonl(path):
                if (any(name.startswith('OWNARGEND_') for name in row.get('placeholders', {}))
                        and clean(row) not in owned_units):
                    errors.append(f"{path}: {row['unit_id']}: owned title requires validated complete-container evidence")
        except (RecordError, KeyError) as exc:
            errors.append(str(exc))
    if any(r['tool']['version'] == '4' for r in records.values()):
        active_ids = {}
        for path in sorted((root / 'translation-data/units').glob('*.jsonl')):
            try:
                for row in load_jsonl(path):
                    if row['unit_id'] in active_ids:
                        errors.append(f"v4 active fact ID collision: {row['unit_id']} in {path} and {active_ids[row['unit_id']]}")
                    active_ids[row['unit_id']] = path
            except (OSError, ValueError, KeyError, TypeError) as exc:
                errors.append(f'{path}: {exc}')
    for path in sorted((root / "translation-data/candidates").glob("*/*.jsonl")):
        try:
            for row in load_jsonl(path):
                key = (path.relative_to(root).as_posix(), row["unit_id"])
                if "derivation_id" in row and key not in origins:
                    errors.append(f"{path}: {row['unit_id']}: derivation has no valid replay")
                if "model_correction_id" in row and (key not in origins or not row.get("derivation_id")):
                    errors.append(f"{path}: {row['unit_id']}: model correction has no valid derivation")
                if row.get('unit_group_id') and (key not in origins or not row.get('derivation_id')
                        or records.get(row['derivation_id'], {}).get('tool', {}).get('version') != '4'):
                    errors.append(f"{path}: {row['unit_id']}: unit group has no valid v4 derivation")
        except (RecordError, KeyError) as exc:
            errors.append(str(exc))
    return origins, errors
