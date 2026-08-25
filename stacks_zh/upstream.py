from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path
from typing import Any

from .schema_validation import validate_named_schema


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_object(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        errors.append(f"{path}: cannot read JSON: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path}: JSON root must be an object")
        return None
    return value


def validate_upstream_index(root: Path, harvest: Path) -> list[str]:
    """Tie upstream.lock, the harvest index, sync report, and history together."""
    errors: list[str] = []
    lock_path = root / "upstream.lock"
    try:
        lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{lock_path}: cannot read lock: {exc}"]
    repository = lock.get("repository")
    commit = lock.get("commit")
    commit_date = lock.get("commit_date")
    if not all(isinstance(item, str) and item for item in (repository, commit, commit_date)):
        return [f"{lock_path}: repository, commit, and commit_date are required"]

    manifest_path = root / "upstream-index" / "manifests" / f"{commit}.json"
    manifest = _load_object(manifest_path, errors)
    if manifest is None:
        return errors
    errors.extend(
        validate_named_schema(
            manifest, "upstream-index-manifest.schema.json", str(manifest_path)
        )
    )
    for field, expected in (
        ("repository", repository),
        ("commit", commit),
        ("commit_date", commit_date),
    ):
        if manifest.get(field) != expected:
            errors.append(f"{manifest_path}: {field} does not match upstream.lock")

    tags_path = harvest / "tags" / "tags"
    chapters_path = harvest / "chapters.tex"
    for path, hash_field in (
        (tags_path, "tags_sha256"),
        (chapters_path, "chapters_sha256"),
    ):
        if not path.is_file():
            errors.append(f"{path}: locked upstream index input is missing")
            continue
        actual_hash = _sha256_file(path)
        if manifest.get(hash_field) != actual_hash:
            errors.append(f"{manifest_path}: {hash_field} does not match {path}")
    if tags_path.is_file():
        tag_count = sum(
            1
            for line in tags_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        if manifest.get("permanent_tag_count") != tag_count:
            errors.append(f"{manifest_path}: permanent_tag_count does not match {tags_path}")

    matching_reports: list[tuple[Path, dict[str, Any]]] = []
    for report_path in sorted((root / "sync-reports").glob("*.json")):
        report = _load_object(report_path, errors)
        if report is not None and report.get("new_commit") == commit:
            matching_reports.append((report_path, report))
    if not matching_reports:
        errors.append(f"sync-reports: no report records locked commit {commit}")
    for report_path, report in matching_reports:
        if report.get("qa_result") == "FAIL" or report.get("unresolved_mappings"):
            errors.append(f"{report_path}: locked commit has failed or unresolved mappings")

    history_path = root / "UPSTREAM_HISTORY.md"
    try:
        history = history_path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"{history_path}: cannot read history: {exc}")
    else:
        if commit not in history:
            errors.append(f"{history_path}: locked commit is not recorded")
        if matching_reports and not any(path.with_suffix(".md").name in history for path, _ in matching_reports):
            errors.append(f"{history_path}: matching sync report is not linked")
    return errors
