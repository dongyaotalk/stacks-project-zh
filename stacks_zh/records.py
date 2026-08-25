from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping

from .schema_validation import validate_named_schema


HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PLACEHOLDER_NAME_RE = re.compile(r"^[A-Z][A-Z0-9]*_[0-9]{4}$")
PLACEHOLDER_TOKEN_RE = re.compile(r"<([A-Z][A-Z0-9]*_[0-9]{4})>")
ASCII_WORD_RE = re.compile(r"(?<![A-Za-z])[A-Za-z][A-Za-z.-]*(?![A-Za-z])")
MODEL_LANE_RE = re.compile(r"^[A-Za-z0-9._-]+$")
STAGES = (
    "AI_DRAFT",
    "STRUCTURE_OK",
    "TERM_OK",
    "CRITIC_OK",
    "LANGUAGE_REVIEWED",
    "MATH_REVIEWED",
    "PUBLISHED",
)
MODEL_MAX_STAGE = STAGES.index("CRITIC_OK")


class RecordError(ValueError):
    """Raised when structured translation data violates a hard constraint."""


def normalize_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return unicodedata.normalize("NFC", value).strip()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_value(value: Any) -> str:
    payload = value if isinstance(value, str) else canonical_json(value)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def expected_unit_hashes(unit: dict[str, Any]) -> dict[str, str]:
    source_text = normalize_text(_require_string(unit, "source_text"))
    structure = {
        "node_kind": unit.get("node_kind"),
        "parent_tag": unit.get("parent_tag"),
        "placeholders": unit.get("placeholders", {}),
        "render": unit.get("render", {}),
    }
    math_nodes = {
        key: value
        for key, value in sorted(unit.get("placeholders", {}).items())
        if key.startswith("MATH_")
    }
    return {
        "source_text_hash": sha256_value(source_text),
        "source_structure_hash": sha256_value(structure),
        "source_math_hash": sha256_value(math_nodes),
    }


def stamp_unit_hashes(unit: dict[str, Any]) -> dict[str, Any]:
    stamped = dict(unit)
    stamped.update(expected_unit_hashes(stamped))
    return stamped


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RecordError(f"cannot read {path}: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RecordError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise RecordError(f"{path}:{line_number}: each JSONL row must be an object")
        value["_record_location"] = f"{path}:{line_number}"
        records.append(value)
    if not records:
        raise RecordError(f"{path}: no records")
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    rows = []
    for record in records:
        clean = {key: value for key, value in record.items() if not key.startswith("_")}
        rows.append(json.dumps(clean, ensure_ascii=False, sort_keys=True))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def load_upstream_commit(path: Path) -> str:
    try:
        import tomllib

        value = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RecordError(f"cannot read upstream lock {path}: {exc}") from exc
    commit = value.get("commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RecordError(f"{path}: commit must be a full lowercase Git SHA-1")
    return commit


def validate_records(
    units: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    source_commit: str,
) -> list[str]:
    errors: list[str] = []
    unit_by_id: dict[str, dict[str, Any]] = {}
    for unit in units:
        unit_id = unit.get("unit_id")
        location = unit.get("_record_location", "unit")
        if not isinstance(unit_id, str) or not unit_id:
            errors.append(f"{location}: missing non-empty unit_id")
            continue
        if unit_id in unit_by_id:
            errors.append(f"{location}: duplicate unit_id {unit_id}")
            continue
        unit_by_id[unit_id] = unit
        errors.extend(_validate_unit(unit, source_commit))

    candidate_ids: set[str] = set()
    for candidate in candidates:
        unit_id = candidate.get("unit_id")
        location = candidate.get("_record_location", "candidate")
        if not isinstance(unit_id, str) or not unit_id:
            errors.append(f"{location}: missing non-empty unit_id")
            continue
        if unit_id in candidate_ids:
            errors.append(f"{location}: duplicate candidate unit_id {unit_id}")
            continue
        candidate_ids.add(unit_id)
        unit = unit_by_id.get(unit_id)
        if unit is None:
            errors.append(f"{location}: candidate references unknown unit {unit_id}")
            continue
        errors.extend(_validate_candidate(candidate, unit, source_commit))

    missing = sorted(set(unit_by_id) - candidate_ids)
    if missing:
        errors.append("candidate file does not cover units: " + ", ".join(missing))
    return errors


def validate_units(
    units: list[dict[str, Any]], source_commit: str
) -> list[str]:
    errors: list[str] = []
    unit_ids: set[str] = set()
    for unit in units:
        unit_id = unit.get("unit_id")
        location = unit.get("_record_location", "unit")
        if not isinstance(unit_id, str) or not unit_id:
            errors.append(f"{location}: missing non-empty unit_id")
            continue
        if unit_id in unit_ids:
            errors.append(f"{location}: duplicate unit_id {unit_id}")
            continue
        unit_ids.add(unit_id)
        errors.extend(_validate_unit(unit, source_commit))
    return errors


def restore_placeholders(
    unit: dict[str, Any],
    translation: str,
    overrides: Mapping[str, str] | None = None,
) -> str:
    rendered = translation
    for name in placeholder_names(unit.get("source_text", "")):
        value = (
            overrides.get(name, unit["placeholders"][name])
            if overrides
            else unit["placeholders"][name]
        )
        rendered = rendered.replace(f"<{name}>", value, 1)
    return rendered


def placeholder_names(text: str) -> list[str]:
    return PLACEHOLDER_TOKEN_RE.findall(text)


def _validate_unit(unit: dict[str, Any], source_commit: str) -> list[str]:
    errors: list[str] = []
    location = unit.get("_record_location", "unit")
    schema_value = {key: value for key, value in unit.items() if not key.startswith("_")}
    errors.extend(validate_named_schema(schema_value, "unit.schema.json", str(location)))
    required_strings = (
        "unit_id",
        "parent_tag",
        "chapter",
        "node_kind",
        "risk_level",
        "source_commit",
        "source_text",
        "source_text_hash",
        "source_structure_hash",
        "source_math_hash",
        "source_status",
    )
    for key in required_strings:
        if not isinstance(unit.get(key), str) or not unit[key]:
            errors.append(f"{location}: {key} must be a non-empty string")
    if unit.get("schema_version") != 1:
        errors.append(f"{location}: schema_version must be 1")
    if unit.get("source_commit") != source_commit:
        errors.append(f"{location}: source_commit does not match upstream.lock")
    if unit.get("source_status") != "CURRENT":
        errors.append(f"{location}: pilot validator only accepts source_status CURRENT")
    if unit.get("risk_level") not in {"R0", "R1", "R2", "R3"}:
        errors.append(f"{location}: invalid risk_level {unit.get('risk_level')!r}")
    placeholders = unit.get("placeholders")
    if not isinstance(placeholders, dict):
        errors.append(f"{location}: placeholders must be an object")
        placeholders = {}
    for key, value in placeholders.items():
        if not isinstance(key, str) or not PLACEHOLDER_NAME_RE.fullmatch(key):
            errors.append(f"{location}: invalid placeholder name {key!r}")
        if not isinstance(value, str) or not value:
            errors.append(f"{location}: placeholder {key!r} must have non-empty TeX")
    source_placeholders = placeholder_names(str(unit.get("source_text", "")))
    if len(source_placeholders) != len(set(source_placeholders)):
        errors.append(f"{location}: source_text repeats a placeholder name")
    if set(source_placeholders) != set(placeholders):
        errors.append(
            f"{location}: placeholder object keys must match source_text tokens "
            f"({sorted(placeholders)!r} != {sorted(set(source_placeholders))!r})"
        )
    render = unit.get("render")
    if not isinstance(render, dict):
        errors.append(f"{location}: render must be an object")
    else:
        for key in ("prefix", "suffix"):
            if not isinstance(render.get(key), str):
                errors.append(f"{location}: render.{key} must be a string")
    if all(isinstance(unit.get(key), str) for key in (
        "source_text_hash",
        "source_structure_hash",
        "source_math_hash",
    )):
        expected = expected_unit_hashes(unit)
        for key, value in expected.items():
            if unit.get(key) != value:
                errors.append(f"{location}: {key} mismatch; run stamp-units")
            elif not HASH_RE.fullmatch(value):
                errors.append(f"{location}: malformed {key}")
    return errors


def _validate_candidate(
    candidate: dict[str, Any], unit: dict[str, Any], source_commit: str
) -> list[str]:
    errors: list[str] = []
    location = candidate.get("_record_location", "candidate")
    required_strings = (
        "unit_id",
        "source_commit",
        "source_text_hash",
        "model_id",
        "model_lane",
        "reasoning_effort",
        "prompt_version",
        "glossary_revision",
        "context_hash",
        "translation",
        "stage",
        "source_status",
        "qa_status",
        "term_status",
        "publication_status",
        "created_at",
    )
    for key in required_strings:
        if not isinstance(candidate.get(key), str) or not candidate[key]:
            errors.append(f"{location}: {key} must be a non-empty string")
    schema_version = candidate.get("schema_version")
    if schema_version not in {1, 2}:
        errors.append(f"{location}: schema_version must be 1 or 2")
    if schema_version == 2:
        schema_value = {
            key: value for key, value in candidate.items() if not key.startswith("_")
        }
        errors.extend(
            validate_named_schema(schema_value, "candidate.schema.json", str(location))
        )
        provenance_strings = (
            "harness_id",
            "harness_version",
            "model_record_id",
            "run_id",
            "model_identity_confidence",
        )
        for key in provenance_strings:
            if not isinstance(candidate.get(key), str) or not candidate[key]:
                errors.append(f"{location}: {key} must be a non-empty string for schema v2")
        if "model_snapshot" not in candidate:
            errors.append(f"{location}: model_snapshot is required for schema v2")
        if candidate.get("model_identity_confidence") not in {
            "runtime-resolved",
            "owner-confirmed",
            "declared",
            "unknown",
        }:
            errors.append(f"{location}: invalid model_identity_confidence")
        translation = candidate.get("translation")
        if isinstance(translation, str):
            expected_translation_hash = sha256_value(translation)
            if candidate.get("translation_hash") != expected_translation_hash:
                errors.append(f"{location}: translation_hash mismatch")
    elif "translation_hash" in candidate and candidate.get("translation_hash") != sha256_value(candidate.get("translation", "")):
        errors.append(f"{location}: translation_hash mismatch")
    if candidate.get("source_commit") != source_commit:
        errors.append(f"{location}: source_commit does not match upstream.lock")
    if candidate.get("source_text_hash") != unit.get("source_text_hash"):
        errors.append(f"{location}: source_text_hash does not match unit")
    lane = candidate.get("model_lane")
    if not isinstance(lane, str) or not MODEL_LANE_RE.fullmatch(lane) or ".." in lane:
        errors.append(f"{location}: invalid model_lane {lane!r}")
    context = candidate.get("context")
    if not isinstance(context, dict):
        errors.append(f"{location}: context must be an object")
    elif candidate.get("context_hash") != sha256_value(context):
        errors.append(f"{location}: context_hash mismatch")
    unknown_terms = candidate.get("unknown_terms")
    if not isinstance(unknown_terms, list):
        errors.append(f"{location}: unknown_terms must be an array")
        unknown_terms = []
    else:
        for index, term in enumerate(unknown_terms):
            if not isinstance(term, dict) or not all(
                isinstance(term.get(key), str) and term[key]
                for key in ("source_term", "target_term", "context")
            ):
                errors.append(
                    f"{location}: unknown_terms[{index}] requires source_term, "
                    "target_term, and context"
                )
    notes = candidate.get("notes")
    if not isinstance(notes, list) or not all(isinstance(note, str) for note in notes):
        errors.append(f"{location}: notes must be an array of strings")
    term_occurrences = candidate.get("term_occurrences")
    valid_term_occurrences: list[dict[str, str]] = []
    if not isinstance(term_occurrences, list):
        errors.append(f"{location}: term_occurrences must be an array")
    else:
        for index, occurrence in enumerate(term_occurrences):
            if not isinstance(occurrence, dict) or not all(
                isinstance(occurrence.get(key), str) and occurrence[key]
                for key in ("source_term", "target_term")
            ):
                errors.append(
                    f"{location}: term_occurrences[{index}] requires source_term "
                    "and target_term"
                )
                continue
            source_term = occurrence["source_term"]
            target_term = occurrence["target_term"]
            if "（" in source_term or "）" in source_term or "（" in target_term or "）" in target_term:
                errors.append(
                    f"{location}: term_occurrences[{index}] values must not contain "
                    "full-width parentheses"
                )
                continue
            valid_term_occurrences.append(occurrence)
    source_tokens = placeholder_names(str(unit.get("source_text", "")))
    translation = candidate.get("translation")
    if isinstance(translation, str):
        target_tokens = placeholder_names(translation)
        if target_tokens != source_tokens:
            errors.append(
                f"{location}: protected placeholders changed or reordered "
                f"({target_tokens!r} != {source_tokens!r})"
            )
        without_tokens = PLACEHOLDER_TOKEN_RE.sub("", translation)
        if re.search(r"\\[A-Za-z@]+|\$", without_tokens):
            errors.append(f"{location}: translation contains raw protected TeX")
        term_literals = [
            f"{occurrence['target_term']}（{occurrence['source_term']}）"
            for occurrence in valid_term_occurrences
        ]
        cursor = 0
        for index, literal in enumerate(term_literals):
            position = translation.find(literal, cursor)
            if position < 0:
                errors.append(
                    f"{location}: term_occurrences[{index}] is missing or out of order: {literal}"
                )
                break
            cursor = position + len(literal)
        for literal in set(term_literals):
            expected_count = term_literals.count(literal)
            actual_count = translation.count(literal)
            if actual_count != expected_count:
                errors.append(
                    f"{location}: bilingual term count mismatch for {literal}: "
                    f"recorded {expected_count}, found {actual_count}"
                )
        residue_text = translation
        for literal in term_literals:
            residue_text = residue_text.replace(literal, "", 1)
        residue_text = PLACEHOLDER_TOKEN_RE.sub("", residue_text)
        allowed = candidate.get("allowed_english", [])
        if not isinstance(allowed, list) or not all(isinstance(word, str) for word in allowed):
            errors.append(f"{location}: allowed_english must be an array of strings")
            allowed = []
        residue = sorted({word for word in ASCII_WORD_RE.findall(residue_text) if word not in allowed})
        if residue:
            errors.append(f"{location}: unexplained English residue: {', '.join(residue)}")
    stage = candidate.get("stage")
    if stage not in STAGES:
        errors.append(f"{location}: invalid stage {stage!r}")
    elif stage == "CRITIC_OK":
        errors.append(
            f"{location}: CRITIC_OK is unavailable until critic records and validation are implemented"
        )
    elif STAGES.index(stage) > MODEL_MAX_STAGE:
        errors.append(f"{location}: model candidate cannot claim stage {stage}")
    if candidate.get("source_status") != "CURRENT":
        errors.append(f"{location}: candidate source_status must be CURRENT")
    if candidate.get("qa_status") not in {"NOT_RUN", "PASS", "FAIL"}:
        errors.append(f"{location}: invalid qa_status")
    if stage in {"STRUCTURE_OK", "TERM_OK", "CRITIC_OK"} and candidate.get("qa_status") != "PASS":
        errors.append(f"{location}: stage {stage} requires qa_status PASS")
    term_status = candidate.get("term_status")
    if term_status not in {"CLEAR", "DECISION_REQUIRED"}:
        errors.append(f"{location}: invalid term_status")
    if unknown_terms and term_status != "DECISION_REQUIRED":
        errors.append(f"{location}: unknown terms require DECISION_REQUIRED")
    if unknown_terms and stage in {"TERM_OK", "CRITIC_OK"}:
        errors.append(f"{location}: unresolved terms prevent stage {stage}")
    if not unknown_terms and term_status == "DECISION_REQUIRED":
        errors.append(f"{location}: DECISION_REQUIRED needs at least one unknown term")
    occurrence_pairs = {
        (occurrence["source_term"], occurrence["target_term"])
        for occurrence in valid_term_occurrences
    }
    for term in unknown_terms:
        if isinstance(term, dict) and all(
            isinstance(term.get(key), str) for key in ("source_term", "target_term")
        ) and (term["source_term"], term["target_term"]) not in occurrence_pairs:
            errors.append(
                f"{location}: unknown term {term['target_term']}（{term['source_term']}） "
                "has no matching term_occurrences entry"
            )
    if candidate.get("publication_status") not in {"INTERNAL", "CANDIDATE"}:
        errors.append(f"{location}: model candidate cannot be RELEASED")
    if candidate.get("review_claims") not in (None, []):
        errors.append(f"{location}: candidate must not contain human review claims")
    return errors


def _require_string(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise RecordError(f"{key} must be a string")
    return value
