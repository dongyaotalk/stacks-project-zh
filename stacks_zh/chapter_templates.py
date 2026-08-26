from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterator

from .records import RecordError, load_upstream_commit


CHAPTER_LINK_RE = re.compile(
    r"\\hyperref\[(?P<label>[A-Za-z0-9._-]+-section-phantom)\]"
)
SECTION_START_RE = re.compile(r"(?m)^[ \t]*\\section[ \t]*\{")
TITLE_START_RE = re.compile(r"(?m)^[ \t]*\\title[ \t]*\{")
LABEL_AFTER_RE = re.compile(r"[ \t\r\n]*\\label\{(?P<label>[^{}\r\n]+)\}")
SAFE_CHAPTER_RE = re.compile(r"^[A-Za-z0-9._-]+$")
TAG_RE = re.compile(r"^[0-9A-Z]+$")
SOURCE_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
TEMPLATE_VERSION = "chapter-templates-v1"


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _braced_argument(text: str, opening_brace: int) -> tuple[str, int]:
    if opening_brace >= len(text) or text[opening_brace] != "{":
        raise RecordError("internal chapter-template parser error: expected opening brace")
    depth = 0
    escaped = False
    for index in range(opening_brace, len(text)):
        character = text[index]
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[opening_brace + 1 : index], index + 1
    raise RecordError("unterminated braced argument in locked chapter source")


def _command_arguments(text: str, pattern: re.Pattern[str]) -> Iterator[tuple[str, int]]:
    for match in pattern.finditer(text):
        opening_brace = text.find("{", match.start(), match.end())
        if opening_brace < 0:  # pragma: no cover - regex invariant
            raise AssertionError("command pattern omitted its opening brace")
        yield _braced_argument(text, opening_brace)


def _manifest_chapters(chapters_text: str) -> list[tuple[str, str]]:
    chapters: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in chapters_text.splitlines():
        match = CHAPTER_LINK_RE.search(line)
        if match is None:
            continue
        label = match.group("label")
        chapter = label.removesuffix("-section-phantom")
        if not SAFE_CHAPTER_RE.fullmatch(chapter):
            raise RecordError(f"invalid chapter slug in chapters.tex: {chapter!r}")
        if chapter in seen:
            raise RecordError(f"duplicate chapter in chapters.tex: {chapter}")
        opening_brace = line.find("{", match.end())
        if opening_brace < 0:
            raise RecordError(f"chapter link has no display title: {chapter}")
        title, _ = _braced_argument(line, opening_brace)
        chapters.append((chapter, title.strip()))
        seen.add(chapter)
    if not chapters:
        raise RecordError("chapters.tex contains no chapter links")
    return chapters


def _tag_by_label(tags_text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line_number, raw_line in enumerate(tags_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "," not in line:
            raise RecordError(f"tags/tags:{line_number}: expected TAG,label")
        tag, label = line.split(",", 1)
        if not TAG_RE.fullmatch(tag) or not label:
            raise RecordError(f"tags/tags:{line_number}: invalid TAG or label")
        if label in result:
            raise RecordError(f"tags/tags:{line_number}: duplicate label {label}")
        result[label] = tag
    if not result:
        raise RecordError("tags/tags contains no permanent Tags")
    return result


def _existing_unit_files(root: Path, units_dir: Path) -> dict[tuple[str, str], list[str]]:
    result: dict[tuple[str, str], list[str]] = {}
    if not units_dir.is_dir():
        return result
    for unit_path in sorted(units_dir.glob("*.jsonl")):
        try:
            lines = unit_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise RecordError(f"cannot read unit batch {unit_path}: {exc}") from exc
        seen_in_file: set[tuple[str, str]] = set()
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                unit = json.loads(line)
            except ValueError as exc:
                raise RecordError(
                    f"{unit_path}:{line_number}: invalid unit JSON: {exc}"
                ) from exc
            if not isinstance(unit, dict):
                raise RecordError(f"{unit_path}:{line_number}: unit must be an object")
            chapter = unit.get("chapter")
            parent_tag = unit.get("parent_tag")
            if not isinstance(chapter, str) or not isinstance(parent_tag, str):
                raise RecordError(
                    f"{unit_path}:{line_number}: chapter and parent_tag are required"
                )
            seen_in_file.add((chapter, parent_tag))
        try:
            relative_path = unit_path.relative_to(root).as_posix()
        except ValueError:
            relative_path = unit_path.as_posix()
        for key in seen_in_file:
            result.setdefault(key, []).append(relative_path)
    return result


def _source_sections(
    source_text: str,
    chapter: str,
    tags: dict[str, str],
    existing: dict[tuple[str, str], list[str]],
) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    seen_labels: set[str] = set()
    for ordinal, (title, end_offset) in enumerate(
        _command_arguments(source_text, SECTION_START_RE), start=1
    ):
        label_match = LABEL_AFTER_RE.match(source_text, end_offset)
        if label_match is None:
            raise RecordError(
                f"{chapter}.tex: Section {ordinal} ({title.strip()!r}) has no adjacent label"
            )
        local_label = label_match.group("label")
        full_label = (
            local_label
            if local_label.startswith(f"{chapter}-")
            else f"{chapter}-{local_label}"
        )
        if full_label in seen_labels:
            raise RecordError(f"{chapter}.tex: duplicate Section label {full_label}")
        seen_labels.add(full_label)
        parent_tag = tags.get(full_label)
        unit_files = existing.get((chapter, parent_tag), []) if parent_tag else []
        if parent_tag is None:
            state = "BLOCKED_NO_TAG"
            suggested_batch = None
            suggested_unit_file = None
        else:
            state = "READY" if unit_files else "UNPREPARED"
            suggested_batch = f"{chapter}-{parent_tag}"
            suggested_unit_file = (
                f"translation-data/units/{suggested_batch}.jsonl"
            )
        sections.append(
            {
                "ordinal": ordinal,
                "source_title": title.strip(),
                "source_label": full_label,
                "parent_tag": parent_tag,
                "suggested_batch": suggested_batch,
                "suggested_unit_file": suggested_unit_file,
                "unit_files": sorted(unit_files),
                "state": state,
            }
        )
    return sections


def build_chapter_templates(
    root: Path,
    harvest: Path,
    lock_path: Path,
    units_dir: Path,
) -> dict[str, dict[str, Any]]:
    """Build deterministic per-chapter task scaffolds from the locked harvest."""
    source_commit = load_upstream_commit(lock_path)
    if not SOURCE_COMMIT_RE.fullmatch(source_commit):  # pragma: no cover - loader invariant
        raise AssertionError(source_commit)
    chapters_path = harvest / "chapters.tex"
    tags_path = harvest / "tags" / "tags"
    try:
        chapters_text = chapters_path.read_text(encoding="utf-8")
        tags_text = tags_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordError(f"cannot read locked chapter-template input: {exc}") from exc
    chapters = _manifest_chapters(chapters_text)
    tags = _tag_by_label(tags_text)
    existing = _existing_unit_files(root, units_dir)

    templates: dict[str, dict[str, Any]] = {}
    for chapter_ordinal, (chapter, manifest_title) in enumerate(chapters, start=1):
        source_path = harvest / f"{chapter}.tex"
        if not source_path.is_file():
            templates[chapter] = {
                "schema_version": 1,
                "generator_version": TEMPLATE_VERSION,
                "source_commit": source_commit,
                "chapter": chapter,
                "chapter_ordinal": chapter_ordinal,
                "source_title": manifest_title,
                "source_file": f"{chapter}.tex",
                "source_sha256": None,
                "source_state": "SOURCE_UNAVAILABLE",
                "sections": [],
            }
            continue
        try:
            source_text = source_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RecordError(f"cannot read locked chapter source {source_path}: {exc}") from exc
        title_arguments = list(_command_arguments(source_text, TITLE_START_RE))
        source_title = title_arguments[0][0].strip() if title_arguments else manifest_title
        templates[chapter] = {
            "schema_version": 1,
            "generator_version": TEMPLATE_VERSION,
            "source_commit": source_commit,
            "chapter": chapter,
            "chapter_ordinal": chapter_ordinal,
            "source_title": source_title,
            "source_file": f"{chapter}.tex",
            "source_sha256": _sha256_file(source_path),
            "source_state": "CURRENT",
            "sections": _source_sections(source_text, chapter, tags, existing),
        }
    return templates


def _serialized(template: dict[str, Any]) -> str:
    return json.dumps(template, ensure_ascii=False, indent=2) + "\n"


def initialize_chapter_templates(
    root: Path,
    harvest: Path,
    lock_path: Path,
    units_dir: Path,
    output_dir: Path,
    *,
    check: bool,
) -> tuple[int, list[str]]:
    templates = build_chapter_templates(root, harvest, lock_path, units_dir)
    expected_names = {f"{chapter}.json" for chapter in templates}
    errors: list[str] = []
    if check:
        actual_names = (
            {path.name for path in output_dir.glob("*.json")}
            if output_dir.is_dir()
            else set()
        )
        for missing in sorted(expected_names - actual_names):
            errors.append(f"{output_dir / missing}: chapter template is missing")
        for stale in sorted(actual_names - expected_names):
            errors.append(f"{output_dir / stale}: stale chapter template")
        for chapter, template in templates.items():
            path = output_dir / f"{chapter}.json"
            if not path.is_file():
                continue
            try:
                actual = path.read_text(encoding="utf-8")
            except OSError as exc:
                errors.append(f"{path}: cannot read chapter template: {exc}")
                continue
            if actual != _serialized(template):
                errors.append(f"{path}: chapter template is out of date")
        return len(templates), errors

    output_dir.mkdir(parents=True, exist_ok=True)
    for chapter, template in templates.items():
        path = output_dir / f"{chapter}.json"
        path.write_text(_serialized(template), encoding="utf-8")
    return len(templates), errors
