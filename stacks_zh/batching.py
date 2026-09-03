from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .records import PLACEHOLDER_TOKEN_RE, RecordError, load_jsonl, load_upstream_commit
from .workflow import CURRENT_TRANSLATOR_PROMPT


SOURCE_WORD_RE = re.compile(r"[A-Za-z]+(?:[.'-][A-Za-z]+)*")
LIMIT_RE = re.compile(
    r"^  (?P<key>preferred_(?:min|max)_source_words): (?P<value>[0-9]+)$",
    re.MULTILINE,
)
MIN_BATCH_FILES = 2
MAX_BATCH_FILES = 8


@dataclass(frozen=True)
class BatchPackageSummary:
    output_path: Path
    batch_count: int
    unit_count: int
    source_word_count: int
    preferred_min_source_words: int
    preferred_max_source_words: int


def _load_preferred_limits(config_path: Path) -> tuple[int, int]:
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordError(f"cannot read workflow config {config_path}: {exc}") from exc
    values = {match["key"]: int(match["value"]) for match in LIMIT_RE.finditer(text)}
    minimum = values.get("preferred_min_source_words")
    maximum = values.get("preferred_max_source_words")
    if minimum is None or maximum is None or minimum < 1 or maximum < minimum:
        raise RecordError(
            f"{config_path}: invalid preferred_min_source_words/"
            "preferred_max_source_words"
        )
    return minimum, maximum


def _source_word_count(source_text: str) -> int:
    return len(SOURCE_WORD_RE.findall(PLACEHOLDER_TOKEN_RE.sub("", source_text)))


def _check_adjacent_sections(
    unit_paths: list[Path], chapter_templates_path: Path | None
) -> list[int] | None:
    if chapter_templates_path is None:
        return None
    try:
        templates = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(chapter_templates_path.glob("*.json"))
        ]
    except (OSError, ValueError) as exc:
        raise RecordError(
            f"cannot read chapter templates {chapter_templates_path}: {exc}"
        ) from exc
    locations: dict[Path, tuple[str, int]] = {}
    for template in templates:
        chapter = template.get("chapter")
        for section in template.get("sections", []):
            ordinal = section.get("ordinal")
            for raw_path in section.get("unit_files", []):
                path = Path(raw_path)
                locations[path] = (str(chapter), int(ordinal))
    resolved: list[tuple[str, int]] = []
    for path in unit_paths:
        relative = path.as_posix()
        match = locations.get(path) or locations.get(Path(relative))
        if match is None:
            try:
                relative_path = path.resolve().relative_to(Path.cwd().resolve())
            except ValueError:
                relative_path = path
            match = locations.get(relative_path)
        if match is None:
            raise RecordError(
                f"{path}: unit file is not listed in chapter templates; "
                "cannot verify adjacent Section order"
            )
        resolved.append(match)
    chapters = {chapter for chapter, _ in resolved}
    if len(chapters) != 1:
        raise RecordError("batch package cannot cross chapters")
    ordinals = [ordinal for _, ordinal in resolved]
    if ordinals != sorted(ordinals):
        raise RecordError("batch package unit files must follow Section order")
    unique_ordinals = list(dict.fromkeys(ordinals))
    if unique_ordinals != list(
        range(unique_ordinals[0], unique_ordinals[0] + len(unique_ordinals))
    ):
        raise RecordError(
            "batch package unit files must be adjacent Sections in the supplied order"
        )
    return ordinals


def write_batch_package(
    unit_paths: Iterable[Path],
    output_path: Path,
    lock_path: Path,
    prompt_path: Path,
    style_guide_path: Path,
    workflow_config_path: Path,
    *,
    allow_outside_preferred_range: bool = False,
    chapter_templates_path: Path | None = None,
) -> BatchPackageSummary:
    """Write one protected, multi-file input package for a model request."""

    paths = list(unit_paths)
    if not MIN_BATCH_FILES <= len(paths) <= MAX_BATCH_FILES:
        raise RecordError(
            f"batch package requires {MIN_BATCH_FILES}-{MAX_BATCH_FILES} unit files "
            f"(got {len(paths)})"
        )
    normalized_inputs = {path.resolve() for path in paths}
    if len(paths) != len(normalized_inputs):
        raise RecordError("batch package unit files must be unique")
    if output_path.resolve() in normalized_inputs:
        raise RecordError("batch package output must not overwrite a unit file")
    section_ordinals = _check_adjacent_sections(paths, chapter_templates_path)

    source_commit = load_upstream_commit(lock_path)
    minimum, maximum = _load_preferred_limits(workflow_config_path)
    try:
        prompt_text = prompt_path.read_text(encoding="utf-8")
        style_guide_text = style_guide_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordError(f"cannot read batch package instructions: {exc}") from exc

    chapter: str | None = None
    parent_tags: list[str] = []
    batch_scopes: list[dict[str, object]] = []
    seen_unit_ids: dict[str, Path] = {}
    packaged_units: list[dict[str, object]] = []
    source_word_count = 0
    for path in paths:
        units = load_jsonl(path)
        file_tags = list(dict.fromkeys(unit.get("parent_tag") for unit in units))
        if not all(isinstance(parent_tag, str) and parent_tag for parent_tag in file_tags):
            raise RecordError(f"{path}: batch package requires non-empty parent_tag values")
        for parent_tag in file_tags:
            assert isinstance(parent_tag, str)
            if parent_tag not in parent_tags:
                parent_tags.append(parent_tag)
        batch_scopes.append({"unit_file": str(path), "parent_tags": file_tags})

        unit_ids = [unit.get("unit_id") for unit in units]
        for index, unit in enumerate(units):
            location = str(unit.get("_record_location", path))
            unit_id = unit.get("unit_id")
            unit_chapter = unit.get("chapter")
            source_text = unit.get("source_text")
            if unit.get("source_commit") != source_commit:
                raise RecordError(f"{location}: unit does not match upstream.lock")
            if unit.get("source_status") != "CURRENT":
                raise RecordError(f"{location}: batch package requires CURRENT units")
            if not isinstance(unit_id, str) or not unit_id:
                raise RecordError(f"{location}: unit_id is required")
            previous = seen_unit_ids.get(unit_id)
            if previous is not None:
                raise RecordError(
                    f"{location}: duplicate unit_id {unit_id} also present in {previous}"
                )
            seen_unit_ids[unit_id] = path
            if not isinstance(unit_chapter, str) or not unit_chapter:
                raise RecordError(f"{location}: chapter is required")
            if chapter is None:
                chapter = unit_chapter
            elif chapter != unit_chapter:
                raise RecordError(
                    f"{location}: batch package cannot cross chapters "
                    f"({chapter!r} and {unit_chapter!r})"
                )
            if not isinstance(source_text, str):
                raise RecordError(f"{location}: source_text is required")
            source_word_count += _source_word_count(source_text)
            neighbors: list[object] = []
            if index:
                neighbors.append(unit_ids[index - 1])
            if index + 1 < len(units):
                neighbors.append(unit_ids[index + 1])
            packaged_units.append(
                {
                    "unit_id": unit_id,
                    "chapter": unit_chapter,
                    "parent_tag": unit.get("parent_tag"),
                    "node_kind": unit.get("node_kind"),
                    "risk_level": unit.get("risk_level"),
                    "source_text": source_text,
                    "neighbor_unit_ids": neighbors,
                }
            )

    outside_range = not minimum <= source_word_count <= maximum
    if outside_range and not allow_outside_preferred_range:
        raise RecordError(
            f"batch package has {source_word_count} source words; preferred range is "
            f"{minimum}-{maximum}. Change the batch or pass "
            "--allow-outside-preferred-range for an indivisible semantic scope"
        )

    package = {
        "schema_version": 1,
        "package_kind": "translation-batch",
        "source_commit": source_commit,
        "prompt_version": CURRENT_TRANSLATOR_PROMPT,
        "chapter": chapter,
        "parent_tags": parent_tags,
        "batch_scopes": batch_scopes,
        "section_ordinals": section_ordinals,
        "unit_files": [str(path) for path in paths],
        "batch_count": len(paths),
        "unit_count": len(packaged_units),
        "source_word_count": source_word_count,
        "preferred_source_words": {"min": minimum, "max": maximum},
        "outside_preferred_range": outside_range,
        "model_input": {
            "batch_instructions": (
                "Apply the translator instructions independently to every unit below. "
                "Return JSONL only: exactly one JSON object per required unit_id, with "
                "no Markdown fence or surrounding commentary."
            ),
            "instructions": prompt_text,
            "style_guide": style_guide_text,
            "approved_glossary_entries": [],
            "units": packaged_units,
        },
        "output_contract": {
            "format": "jsonl",
            "schema": "schema/translator-output.schema.json",
            "required_unit_ids": [unit["unit_id"] for unit in packaged_units],
            "one_record_per_unit": True,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return BatchPackageSummary(
        output_path=output_path,
        batch_count=len(paths),
        unit_count=len(packaged_units),
        source_word_count=source_word_count,
        preferred_min_source_words=minimum,
        preferred_max_source_words=maximum,
    )
