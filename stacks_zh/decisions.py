from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .records import sha256_value
from .schema_validation import validate_named_schema


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: record must be a JSON object")
    return value


def _candidate_index(root: Path, errors: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for path in sorted((root / "translation-data" / "candidates").glob("*/*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            location = f"{path}:{line_number}"
            try:
                candidate = json.loads(line)
            except ValueError as exc:
                errors.append(f"{location}: invalid JSON: {exc}")
                continue
            if not isinstance(candidate, dict):
                errors.append(f"{location}: candidate must be an object")
                continue
            key = (
                str(candidate.get("unit_id", "")),
                str(candidate.get("run_id", "")),
                str(candidate.get("translation_hash", "")),
            )
            if key in result:
                errors.append(f"{location}: duplicate candidate identity {key!r}")
            result[key] = candidate
    return result


def _unit_facts(root: Path, errors: list[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for path in sorted((root / "translation-data" / "units").glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                unit = json.loads(line)
            except ValueError as exc:
                errors.append(f"{path}:{line_number}: invalid unit JSON: {exc}")
                continue
            if isinstance(unit, dict) and isinstance(unit.get("unit_id"), str):
                result[unit["unit_id"]] = {
                    "risk_level": str(unit.get("risk_level", "")),
                    "source_text_hash": str(unit.get("source_text_hash", "")),
                }
    return result


def validate_repository_decisions(root: Path) -> list[str]:
    """Validate candidate selection, human review and formal revision linkage."""
    errors: list[str] = []
    candidates = _candidate_index(root, errors)
    unit_facts = _unit_facts(root, errors)

    selections: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path in sorted((root / "translation-data" / "selections").glob("*.json")):
        try:
            selection = _read_json(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        errors.extend(
            validate_named_schema(selection, "selection.schema.json", str(path))
        )
        selection_id = selection.get("selection_id")
        if not isinstance(selection_id, str) or not selection_id:
            errors.append(f"{path}: selection_id is required")
            continue
        if selection_id in selections:
            errors.append(f"{path}: duplicate selection_id {selection_id!r}")
        selections[selection_id] = (path, selection)
        key = (
            str(selection.get("unit_id", "")),
            str(selection.get("run_id", "")),
            str(selection.get("translation_hash", "")),
        )
        candidate = candidates.get(key)
        if candidate is None:
            errors.append(f"{path}: selection does not reference an exact candidate {key!r}")
        elif selection.get("source_commit") != candidate.get("source_commit"):
            errors.append(f"{path}: source_commit does not match selected candidate")
        if selection.get("decision") not in {
            "accept-candidate",
            "reject-candidate",
            "request-changes",
        }:
            errors.append(f"{path}: invalid selection decision")
        for field in ("decided_by", "decided_at", "reason"):
            if not isinstance(selection.get(field), str) or not selection[field]:
                errors.append(f"{path}: {field} is required")

    reviews: dict[str, tuple[Path, dict[str, Any]]] = {}
    for review_type in ("language", "mathematics"):
        for path in sorted((root / "review" / review_type).rglob("*.json")):
            try:
                review = _read_json(path)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            errors.extend(validate_named_schema(review, "review.schema.json", str(path)))
            review_id = review.get("review_id")
            if not isinstance(review_id, str) or not review_id:
                errors.append(f"{path}: review_id is required")
                continue
            if review_id in reviews:
                errors.append(f"{path}: duplicate review_id {review_id!r}")
            reviews[review_id] = (path, review)
            if review.get("review_type") != review_type:
                errors.append(f"{path}: review_type must match its directory")
            matching = [
                candidate
                for (unit_id, run_id, translation_hash), candidate in candidates.items()
                if unit_id == review.get("unit_id")
                and run_id == review.get("run_id")
                and translation_hash == review.get("candidate_hash")
            ]
            if not matching:
                errors.append(f"{path}: candidate_hash/run_id/unit_id does not identify a candidate")
            elif review.get("source_commit") != matching[0].get("source_commit"):
                errors.append(f"{path}: source_commit does not match reviewed candidate")

    revisions: dict[str, tuple[Path, dict[str, Any]]] = {}
    current_by_unit: dict[str, str] = {}
    for path in sorted((root / "translation-data" / "reviewed").rglob("*.json")):
        try:
            revision = _read_json(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        errors.extend(
            validate_named_schema(
                revision, "translation-revision.schema.json", str(path)
            )
        )
        revision_id = revision.get("revision_id")
        if not isinstance(revision_id, str) or not revision_id:
            errors.append(f"{path}: revision_id is required")
            continue
        if revision_id in revisions:
            errors.append(f"{path}: duplicate revision_id {revision_id!r}")
        revisions[revision_id] = (path, revision)
        required_strings = (
            "unit_id",
            "source_commit",
            "source_text_hash",
            "translation",
            "translation_hash",
            "origin_run_id",
            "selection_id",
            "selected_by",
            "created_at",
            "reason",
            "risk_level",
            "stage",
            "source_status",
            "qa_status",
            "term_status",
            "publication_status",
            "status",
        )
        for field in required_strings:
            if not isinstance(revision.get(field), str) or not revision[field]:
                errors.append(f"{path}: {field} is required")
        if revision.get("translation_hash") != sha256_value(revision.get("translation", "")):
            errors.append(f"{path}: translation_hash does not match translation")
        selection_entry = selections.get(str(revision.get("selection_id", "")))
        if selection_entry is None:
            errors.append(f"{path}: selection_id does not exist")
        else:
            selection_path, selection = selection_entry
            if selection.get("decision") != "accept-candidate":
                errors.append(f"{path}: {selection_path} did not accept the candidate")
            for revision_field, selection_field in (
                ("unit_id", "unit_id"),
                ("source_commit", "source_commit"),
                ("origin_run_id", "run_id"),
                ("selected_by", "decided_by"),
            ):
                if revision.get(revision_field) != selection.get(selection_field):
                    errors.append(
                        f"{path}: {revision_field} does not match selection {selection_path}"
                    )
            selected_key = (
                str(selection.get("unit_id", "")),
                str(selection.get("run_id", "")),
                str(selection.get("translation_hash", "")),
            )
            selected_candidate = candidates.get(selected_key)
            if selected_candidate is None:
                errors.append(f"{path}: selection does not identify a candidate")
            else:
                if revision.get("translation_hash") != selected_candidate.get("translation_hash"):
                    errors.append(f"{path}: translation_hash does not match selected candidate")
                if revision.get("source_text_hash") != selected_candidate.get("source_text_hash"):
                    errors.append(f"{path}: source_text_hash does not match selected candidate")
        unit_fact = unit_facts.get(str(revision.get("unit_id", "")))
        if unit_fact is None:
            errors.append(f"{path}: revision references an unknown unit")
        else:
            if revision.get("source_text_hash") != unit_fact["source_text_hash"]:
                errors.append(f"{path}: source_text_hash does not match unit")
            if revision.get("risk_level") != unit_fact["risk_level"]:
                errors.append(f"{path}: risk_level does not match unit")
        if revision.get("source_status") != "CURRENT":
            errors.append(f"{path}: formal revision source_status must be CURRENT")
        if revision.get("qa_status") != "PASS":
            errors.append(f"{path}: formal revision qa_status must be PASS")
        if revision.get("term_status") != "CLEAR":
            errors.append(f"{path}: formal revision term_status must be CLEAR")
        if revision.get("stage") not in {"LANGUAGE_REVIEWED", "MATH_REVIEWED", "PUBLISHED"}:
            errors.append(f"{path}: invalid formal revision stage")
        if revision.get("status") == "current":
            unit_id = str(revision.get("unit_id", ""))
            if unit_id in current_by_unit:
                errors.append(f"{path}: unit already has current revision {current_by_unit[unit_id]}")
            current_by_unit[unit_id] = revision_id

    for revision_id, (path, revision) in revisions.items():
        review_ids = revision.get("review_ids")
        if not isinstance(review_ids, list) or not all(isinstance(item, str) for item in review_ids):
            errors.append(f"{path}: review_ids must be an array of strings")
            review_ids = []
        review_types: set[str] = set()
        selection_entry = selections.get(str(revision.get("selection_id", "")))
        selected_hash = selection_entry[1].get("translation_hash") if selection_entry else None
        for review_id in review_ids:
            entry = reviews.get(review_id)
            if entry is None:
                errors.append(f"{path}: review_id does not exist: {review_id}")
                continue
            review_path, review = entry
            review_types.add(str(review.get("review_type")))
            if review.get("decision") != "approved":
                errors.append(f"{path}: {review_path} is not approved")
            for field in ("unit_id", "source_commit"):
                if review.get(field) != revision.get(field):
                    errors.append(f"{path}: {review_path} has a different {field}")
            if review.get("run_id") != revision.get("origin_run_id"):
                errors.append(f"{path}: {review_path} has a different run_id")
            if review.get("candidate_hash") != selected_hash:
                errors.append(f"{path}: {review_path} does not review the selected candidate hash")
            if review.get("resulting_translation_hash") != revision.get("translation_hash"):
                errors.append(f"{path}: {review_path} does not approve this revision hash")
        risk = revision.get("risk_level")
        required_reviews = set()
        if selection_entry and isinstance(selection_entry[1].get("review_required"), list):
            required_reviews.update(selection_entry[1]["review_required"])
        if risk in {"R1", "R2", "R3"}:
            required_reviews.add("language")
        if risk == "R3":
            required_reviews.add("mathematics")
        for review_type in sorted(required_reviews - review_types):
            errors.append(f"{path}: selection/risk requires approved {review_type} review")
        stage = revision.get("stage")
        if "mathematics" in required_reviews and stage == "LANGUAGE_REVIEWED":
            errors.append(f"{path}: stage does not reflect required mathematics review")
        if stage == "MATH_REVIEWED" and "mathematics" not in review_types:
            errors.append(f"{path}: MATH_REVIEWED requires an approved mathematics review")
        publication_status = revision.get("publication_status")
        if publication_status == "RELEASED" and stage != "PUBLISHED":
            errors.append(f"{path}: RELEASED requires stage PUBLISHED")
        if stage == "PUBLISHED" and publication_status != "RELEASED":
            errors.append(f"{path}: PUBLISHED requires publication_status RELEASED")
        supersedes = revision.get("supersedes_revision_id")
        if supersedes is not None:
            previous = revisions.get(str(supersedes))
            if previous is None:
                errors.append(f"{path}: supersedes_revision_id does not exist")
            else:
                previous_path, previous_revision = previous
                if previous_revision.get("unit_id") != revision.get("unit_id"):
                    errors.append(f"{path}: superseded revision belongs to another unit")
                if previous_revision.get("status") != "superseded":
                    errors.append(f"{previous_path}: replaced revision must have status superseded")
        elif revision.get("status") != "retired":
            # A first revision has no predecessor; later revisions must declare one.
            same_unit = [
                item
                for item, (_, value) in revisions.items()
                if item != revision_id and value.get("unit_id") == revision.get("unit_id")
            ]
            if same_unit:
                errors.append(f"{path}: multiple revisions require an explicit supersedes link")
    return errors
