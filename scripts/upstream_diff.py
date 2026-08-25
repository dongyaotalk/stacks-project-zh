#!/usr/bin/env python3
"""Generate a deterministic old/new upstream unit and Tag diff report.

The unit directories are exported from the old and new locked harvest commits
by the importer.  This tool deliberately does not fetch, checkout, or modify
the harvest repository: synchronization remains an explicit, reviewable PR.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FULL_SHA = set("0123456789abcdef")


def require_sha(value: str, name: str) -> str:
    if len(value) != 40 or any(char not in FULL_SHA for char in value):
        raise ValueError(f"{name} must be a full lowercase Git SHA-1")
    return value


def file_hash(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def load_units(root: Path) -> dict[str, dict[str, Any]]:
    units: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(record, dict) or not isinstance(record.get("unit_id"), str):
                raise ValueError(f"{path}:{line_number}: unit_id is required")
            unit_id = record["unit_id"]
            if unit_id in units:
                raise ValueError(f"duplicate unit_id: {unit_id}")
            units[unit_id] = record
    if not units:
        raise ValueError(f"{root}: no unit records")
    return units


def load_tags(path: Path | None) -> tuple[dict[str, str], list[dict[str, str]]]:
    if path is None:
        return {}, []
    labels: dict[str, str] = {}
    tags: dict[str, str] = {}
    unresolved: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = [part.strip() for part in stripped.split(",", 1)]
        if len(parts) != 2 or not all(parts):
            unresolved.append({"kind": "invalid-tag-line", "path": f"{path}:{line_number}"})
            continue
        tag, label = parts
        if label in labels and labels[label] != tag:
            unresolved.append({"kind": "duplicate-label", "label": label})
        if tag in tags and tags[tag] != label:
            unresolved.append({"kind": "duplicate-tag", "tag": tag})
        labels[label] = tag
        tags[tag] = label
    return labels, unresolved


def load_id_map(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict) and isinstance(value.get("mapping"), dict):
        value = value["mapping"]
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise ValueError(f"{path}: expected an object mapping old unit IDs to new IDs")
    return value


def classify(old: dict[str, Any], new: dict[str, Any]) -> str:
    text_changed = old.get("source_text_hash") != new.get("source_text_hash")
    math_changed = old.get("source_math_hash") != new.get("source_math_hash")
    structure_changed = old.get("source_structure_hash") != new.get("source_structure_hash")
    if not (text_changed or math_changed or structure_changed):
        return "UNCHANGED"
    if math_changed:
        return "STALE_MATH"
    if structure_changed:
        return "PARTIAL_STALE"
    return "STALE_TEXT"


def tag_changes(old: dict[str, str], new: dict[str, str]) -> dict[str, list[dict[str, str]]]:
    added = [{"label": label, "tag": new[label]} for label in sorted(set(new) - set(old))]
    retired = [{"label": label, "tag": old[label]} for label in sorted(set(old) - set(new))]
    moved = [
        {"label": label, "old_tag": old[label], "new_tag": new[label]}
        for label in sorted(set(old) & set(new))
        if old[label] != new[label]
    ]
    old_by_tag = {tag: label for label, tag in old.items()}
    new_by_tag = {tag: label for label, tag in new.items()}
    remapped = [
        {"tag": tag, "old_label": old_by_tag[tag], "new_label": new_by_tag[tag]}
        for tag in sorted(set(old_by_tag) & set(new_by_tag))
        if old_by_tag[tag] != new_by_tag[tag]
    ]
    return {"added": added, "retired": retired, "moved": moved, "remapped": remapped}


def generate_report(args: argparse.Namespace) -> dict[str, Any]:
    old_commit = require_sha(args.old_commit, "old_commit") if args.old_commit else None
    new_commit = require_sha(args.new_commit, "new_commit")
    old_units = load_units(args.old_units)
    new_units = load_units(args.new_units)
    id_map = load_id_map(args.unit_id_map)

    remapped_old: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, Any]] = []
    for old_id, unit in old_units.items():
        new_id = id_map.get(old_id, old_id)
        if new_id in remapped_old:
            unresolved.append({"kind": "ambiguous-unit-map", "new_unit_id": new_id})
        remapped_old[new_id] = unit
        if new_id != old_id and new_id not in new_units:
            unresolved.append({"kind": "mapped-unit-missing", "old_unit_id": old_id, "new_unit_id": new_id})

    changes: list[dict[str, Any]] = []
    for unit_id in sorted(set(remapped_old) & set(new_units)):
        status = classify(remapped_old[unit_id], new_units[unit_id])
        if status != "UNCHANGED":
            changes.append({"unit_id": unit_id, "status": status})
    for unit_id in sorted(set(new_units) - set(remapped_old)):
        changes.append({"unit_id": unit_id, "status": "UNTRANSLATED"})
    for unit_id in sorted(set(remapped_old) - set(new_units)):
        changes.append({"unit_id": unit_id, "status": "RETIRED"})

    old_tags, old_tag_errors = load_tags(args.old_tags)
    new_tags, new_tag_errors = load_tags(args.new_tags)
    unresolved.extend(old_tag_errors)
    unresolved.extend(new_tag_errors)
    report: dict[str, Any] = {
        "schema_version": 1,
        "report_kind": "baseline" if old_commit is None else "synchronization",
        "old_commit": old_commit,
        "new_commit": new_commit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": {
            "parser_version": "unit-diff-v1",
            "normalization_version": args.normalization_version,
        },
        "index_snapshot": {
            "old": {
                "permanent_tag_count": len(old_tags),
                "tags_sha256": file_hash(args.old_tags),
                "chapters_sha256": file_hash(args.old_chapters),
            },
            "new": {
                "permanent_tag_count": len(new_tags),
                "tags_sha256": file_hash(args.new_tags),
                "chapters_sha256": file_hash(args.new_chapters),
            },
        },
        "upstream_commits": [],
        "tag_changes": tag_changes(old_tags, new_tags),
        "statistics": {
            "old_units": len(old_units),
            "new_units": len(new_units),
            "unchanged_units": len(set(remapped_old) & set(new_units)) - sum(
                1 for change in changes if change["status"] not in {"UNTRANSLATED", "RETIRED"}
            ),
            "changed_units": sum(
                1
                for change in changes
                if change["status"] in {"STALE_TEXT", "STALE_MATH", "PARTIAL_STALE"}
            ),
            "added_units": sum(1 for change in changes if change["status"] == "UNTRANSLATED"),
            "retired_units": sum(1 for change in changes if change["status"] == "RETIRED"),
        },
        "unit_changes": changes,
        "unresolved_mappings": unresolved,
        "qa_result": "BASELINE" if old_commit is None else ("FAIL" if unresolved else "PASS"),
        "notes": [
            "Unit hashes classify text, structure and protected LaTeX changes; semantic math AST equivalence is not inferred.",
            "A synchronization with unresolved mappings is a blocker and must not update upstream.lock.",
        ],
    }
    return report


def markdown(report: dict[str, Any], json_name: str) -> str:
    stats = report["statistics"]
    tags = report["tag_changes"]
    lines = [
        f"# 上游同步报告：{report['new_commit'][:8]}",
        "",
        f"- 报告类型：`{report['report_kind']}`",
        f"- old commit：`{report['old_commit'] or '（基线）'}`",
        f"- new commit：`{report['new_commit']}`",
        f"- QA：`{report['qa_result']}`",
        f"- 机器版本：[report]({json_name})",
        "",
        "## 单元统计",
        "",
        f"- 旧单元：{stats['old_units']}；新单元：{stats['new_units']}",
        f"- 未变化：{stats['unchanged_units']}；文本过期：{sum(c['status'] == 'STALE_TEXT' for c in report['unit_changes'])}",
        f"- 数学过期：{sum(c['status'] == 'STALE_MATH' for c in report['unit_changes'])}；结构/部分过期：{sum(c['status'] == 'PARTIAL_STALE' for c in report['unit_changes'])}",
        f"- 新增未译：{stats['added_units']}；上游删除：{stats['retired_units']}",
        "",
        "## Tag 变化",
        "",
        f"- 新增：{len(tags['added'])}；退休：{len(tags['retired'])}；移动：{len(tags['moved'])}；重映射：{len(tags['remapped'])}",
        "",
        "## 受影响单元",
        "",
    ]
    if report["unit_changes"]:
        lines.extend(f"- `{item['unit_id']}`：`{item['status']}`" for item in report["unit_changes"])
    else:
        lines.append("- 无")
    lines.extend(["", "## 未解决映射", ""])
    if report["unresolved_mappings"]:
        lines.extend(f"- `{json.dumps(item, ensure_ascii=False, sort_keys=True)}`" for item in report["unresolved_mappings"])
    else:
        lines.append("- 无")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-units", type=Path, required=True)
    parser.add_argument("--new-units", type=Path, required=True)
    parser.add_argument("--old-commit")
    parser.add_argument("--new-commit", required=True)
    parser.add_argument("--old-tags", type=Path)
    parser.add_argument("--new-tags", type=Path)
    parser.add_argument("--old-chapters", type=Path)
    parser.add_argument("--new-chapters", type=Path)
    parser.add_argument("--unit-id-map", type=Path)
    parser.add_argument("--normalization-version", default="latex-fragments-v1")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    if (args.old_tags is None) != (args.new_tags is None):
        parser.error("--old-tags and --new-tags must be provided together")
    report = generate_report(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(markdown(report, args.output_json.name), encoding="utf-8")
    print(f"Upstream diff: {report['qa_result']} ({len(report['unit_changes'])} affected unit(s))")
    return 0 if report["qa_result"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
