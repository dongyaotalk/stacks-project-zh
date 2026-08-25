#!/usr/bin/env python3
"""Promote label-based units to their permanent Stacks Project Tag IDs.

The first unit import predates the permanent-tag index for a handful of
lemmas.  This migration changes only stable coordinates and the hashes that
contain those coordinates; it never changes source text or translations.
It also refreshes each affected run manifest's ordered context-hash list. It is
intentionally idempotent so it can be rerun after a failed checkout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Allow direct execution as ``python scripts/migrate_permanent_tags.py``.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stacks_zh.records import RecordError, load_jsonl, sha256_value, write_jsonl


LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
UNIT_ID_RE = re.compile(r"^label:(.+):([^:]+)$")


def load_tag_map(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RecordError(f"cannot read Tag index {path}: {exc}") from exc
    result: dict[str, str] = {}
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = [part.strip() for part in stripped.split(",", 1)]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise RecordError(f"{path}:{line_number}: expected TAG,full_label")
        tag, label = parts
        previous = result.get(label)
        if previous is not None and previous != tag:
            raise RecordError(
                f"{path}:{line_number}: {label!r} maps to both {previous!r} and {tag!r}"
            )
        result[label] = tag
    if not result:
        raise RecordError(f"{path}: no permanent Tags")
    return result


def labels_in_unit(unit: dict[str, Any]) -> list[str]:
    render = unit.get("render")
    placeholders = unit.get("placeholders")
    values: list[str] = []
    if isinstance(render, dict):
        values.extend(str(render.get(key, "")) for key in ("prefix", "suffix"))
    if isinstance(placeholders, dict):
        values.extend(str(value) for value in placeholders.values())
    return [label for value in values for label in LABEL_RE.findall(value)]


def build_mapping(root: Path, tags: dict[str, str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in sorted((root / "translation-data" / "units").glob("*.jsonl")):
        for unit in load_jsonl(path):
            old_id = unit.get("unit_id")
            if not isinstance(old_id, str) or not old_id.startswith("label:"):
                continue
            labels = [label for label in labels_in_unit(unit) if label in tags]
            if not labels:
                continue
            if len(set(labels)) != 1:
                raise RecordError(
                    f"{path}: {old_id}: multiple permanent Tags in one unit: {labels}"
                )
            match = UNIT_ID_RE.fullmatch(old_id)
            if match is None:
                raise RecordError(f"{path}: unsupported label unit ID {old_id!r}")
            label, suffix = match.groups()
            if label != labels[0]:
                raise RecordError(
                    f"{path}: {old_id}: rendered Tag label {labels[0]!r} does not "
                    f"match unit label {label!r}"
                )
            new_id = f"tag:{tags[label]}:{suffix}"
            previous = mapping.get(old_id)
            if previous is not None and previous != new_id:
                raise RecordError(f"conflicting mapping for {old_id}: {previous} / {new_id}")
            mapping[old_id] = new_id
    return mapping


def remap_value(value: Any, mapping: dict[str, str]) -> Any:
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, list):
        return [remap_value(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: remap_value(item, mapping) for key, item in value.items()}
    return value


def migrate_jsonl(path: Path, mapping: dict[str, str]) -> bool:
    records = load_jsonl(path)
    changed = False
    output: list[dict[str, Any]] = []
    for record in records:
        before = json.dumps(record, ensure_ascii=False, sort_keys=True)
        record = remap_value(record, mapping)
        # Context hashes cover unit and neighbor IDs, so recalculate after remap.
        if isinstance(record.get("context"), dict):
            record["context_hash"] = sha256_value(record["context"])
        after = json.dumps(record, ensure_ascii=False, sort_keys=True)
        changed = changed or before != after
        output.append(record)
    if changed:
        write_jsonl(path, output)
    return changed


def migrate_manifests(
    root: Path,
    mapping: dict[str, str],
    run_context_hashes: dict[str, list[str]],
) -> int:
    changed_count = 0
    for path in sorted((root / "translation-data" / "runs").glob("*.json")):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise RecordError(f"cannot read run manifest {path}: {exc}") from exc
        if not isinstance(manifest, dict):
            raise RecordError(f"{path}: run manifest must be an object")
        before = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        manifest = remap_value(manifest, mapping)
        run_id = manifest.get("run_id")
        inputs = manifest.get("inputs")
        if isinstance(run_id, str) and isinstance(inputs, dict) and run_id in run_context_hashes:
            inputs["context_hashes"] = run_context_hashes[run_id]
        after = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        if before == after:
            continue
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed_count += 1
    return changed_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--tags", type=Path, required=True)
    parser.add_argument("--map", dest="map_path", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    tags = load_tag_map(args.tags)
    mapping = build_mapping(root, tags)
    args.map_path.parent.mkdir(parents=True, exist_ok=True)
    args.map_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "migration_kind": "permanent-tag-unit-id",
                "source_tag_index": str(args.tags),
                "mapping": mapping,
                "count": len(mapping),
                "policy": "Only a unit whose own rendered label has exactly one permanent Tag is remapped.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    changed_jsonl = 0
    run_context_hashes: dict[str, list[str]] = {}
    for path in sorted((root / "translation-data" / "units").glob("*.jsonl")):
        changed_jsonl += int(migrate_jsonl(path, mapping))
    for path in sorted((root / "translation-data" / "candidates").glob("*/*.jsonl")):
        changed_jsonl += int(migrate_jsonl(path, mapping))
        for candidate in load_jsonl(path):
            run_id = candidate.get("run_id")
            context_hash = candidate.get("context_hash")
            if isinstance(run_id, str) and isinstance(context_hash, str):
                run_context_hashes.setdefault(run_id, []).append(context_hash)
    changed_manifests = migrate_manifests(root, mapping, run_context_hashes)
    print(
        f"Permanent Tag migration: {len(mapping)} mapping(s), "
        f"{changed_jsonl} JSONL file(s), {changed_manifests} run manifest(s) changed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
