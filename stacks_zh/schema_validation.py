from __future__ import annotations

import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


SCHEMA_ROOT = Path(__file__).resolve().parent.parent / "schema"
SUPPORTED_SCHEMA_KEYS = {
    "$schema",
    "$id",
    "title",
    "description",
    "type",
    "additionalProperties",
    "required",
    "properties",
    "propertyNames",
    "const",
    "enum",
    "pattern",
    "format",
    "minLength",
    "maxItems",
    "items",
    "uniqueItems",
}


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_ROOT / name
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: schema root must be an object")
    unsupported = _unsupported_schema_keywords(value, str(path))
    if unsupported:
        raise ValueError("\n".join(unsupported))
    return value


def _unsupported_schema_keywords(schema: dict[str, Any], location: str) -> list[str]:
    errors = [
        f"{location}: unsupported JSON Schema keyword {key!r}"
        for key in schema
        if key not in SUPPORTED_SCHEMA_KEYS
    ]
    properties = schema.get("properties")
    if isinstance(properties, dict):
        for key, child in properties.items():
            if isinstance(child, dict):
                errors.extend(_unsupported_schema_keywords(child, f"{location}.properties.{key}"))
    for key in ("items", "propertyNames", "additionalProperties"):
        child = schema.get(key)
        if isinstance(child, dict):
            errors.extend(_unsupported_schema_keywords(child, f"{location}.{key}"))
    return errors


def validate_named_schema(
    value: Any,
    schema_name: str,
    location: str,
) -> list[str]:
    """Validate the JSON Schema subset used by this repository."""
    return _validate(value, load_schema(schema_name), location)


def validate_repository_schemas(root: Path) -> list[str]:
    """Validate every tracked structured-record family against its contract."""
    jsonl_families = (
        ("translation-data/units/*.jsonl", "unit.schema.json"),
        ("translation-data/candidates/*/*.jsonl", "candidate.schema.json"),
    )
    json_families = (
        ("config/translation-priorities.json", "translation-priorities.schema.json"),
        ("translation-data/chapter-templates/*.json", "chapter-template.schema.json"),
        ("translation-data/runs/*.json", "run-manifest.schema.json"),
        ("translation-data/selections/*.json", "selection.schema.json"),
        ("translation-data/reviewed/**/*.json", "translation-revision.schema.json"),
        ("review/language/**/*.json", "review.schema.json"),
        ("review/mathematics/**/*.json", "review.schema.json"),
        ("sync-reports/*.json", "upstream-sync-report.schema.json"),
        ("upstream-index/manifests/*.json", "upstream-index-manifest.schema.json"),
    )
    errors: list[str] = []
    for pattern, schema_name in jsonl_families:
        for path in sorted(root.glob(pattern)):
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError as exc:
                errors.append(f"{path}: cannot read file: {exc}")
                continue
            for line_number, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                location = f"{path}:{line_number}"
                try:
                    value = json.loads(line)
                except ValueError as exc:
                    errors.append(f"{location}: invalid JSON: {exc}")
                    continue
                errors.extend(validate_named_schema(value, schema_name, location))
    for pattern, schema_name in json_families:
        for path in sorted(root.glob(pattern)):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                errors.append(f"{path}: invalid JSON: {exc}")
                continue
            errors.extend(validate_named_schema(value, schema_name, str(path)))
    return errors


def _validate(value: Any, schema: dict[str, Any], location: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None:
        allowed_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_has_type(value, item) for item in allowed_types):
            return [f"{location}: expected {' or '.join(allowed_types)}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{location}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: must be one of {schema['enum']!r}")

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{location}: must contain at least {minimum} character(s)")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            errors.append(f"{location}: does not match {pattern!r}")
        if schema.get("format") == "date-time" and not _is_datetime(value):
            errors.append(f"{location}: must be an RFC 3339 date-time")

    if isinstance(value, list):
        maximum = schema.get("maxItems")
        if isinstance(maximum, int) and len(value) > maximum:
            errors.append(f"{location}: must contain at most {maximum} item(s)")
        if schema.get("uniqueItems") is True:
            fingerprints = [
                json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                for item in value
            ]
            if len(fingerprints) != len(set(fingerprints)):
                errors.append(f"{location}: array items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(_validate(item, item_schema, f"{location}[{index}]"))

    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    errors.append(f"{location}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{location}: unexpected property {key!r}")
        property_names = schema.get("propertyNames")
        if isinstance(property_names, dict):
            for key in value:
                errors.extend(_validate(key, property_names, f"{location} property {key!r}"))
        additional_schema = schema.get("additionalProperties")
        for key, item in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, dict):
                errors.extend(_validate(item, child_schema, f"{location}.{key}"))
            elif isinstance(additional_schema, dict):
                errors.extend(_validate(item, additional_schema, f"{location}.{key}"))
    return errors


def _has_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


def _is_datetime(value: str) -> bool:
    if "T" not in value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None
