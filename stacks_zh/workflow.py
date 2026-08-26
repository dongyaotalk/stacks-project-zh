from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from .chapter_templates import manifest_chapters
from .records import (
    RecordError,
    load_jsonl,
    load_upstream_commit,
    restore_placeholders,
    sha256_value,
    stamp_unit_hashes,
    validate_records,
    write_jsonl,
)
from .schema_validation import validate_named_schema


SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
LABEL_RE = re.compile(r"\\label\{([^{}]+)\}")
REF_VALUE_RE = re.compile(r"^\\ref\{([^{}]+)\}$")
TAG_RE = re.compile(r"^[0-9A-Z]+$")
TAG_LABEL_RE = re.compile(r"^[A-Za-z0-9._:+-]+$")
CURRENT_TRANSLATOR_PROMPT = "translator-v2"


def stamp_units(input_path: Path, output_path: Path) -> int:
    units = load_jsonl(input_path)
    write_jsonl(output_path, (stamp_unit_hashes(unit) for unit in units))
    return len(units)


def validate_batch(unit_path: Path, candidate_path: Path, lock_path: Path) -> tuple[int, list[str]]:
    source_commit = load_upstream_commit(lock_path)
    units = load_jsonl(unit_path)
    candidates = load_jsonl(candidate_path)
    errors = validate_records(units, candidates, source_commit)
    return len(candidates), errors


def assemble_candidates(
    unit_path: Path,
    draft_path: Path,
    output_path: Path,
    lock_path: Path,
    model_id: str,
    model_lane: str,
    reasoning_effort: str,
    prompt_version: str,
    policy_revision: str,
    glossary_revision: str,
    created_at: str,
    harness_id: str = "unknown",
    harness_version: str = "unknown",
    model_record_id: str | None = None,
    run_id: str | None = None,
    model_snapshot: str | None = None,
    model_identity_confidence: str = "unknown",
) -> int:
    if not SAFE_NAME_RE.fullmatch(model_lane) or ".." in model_lane:
        raise RecordError(f"invalid model lane {model_lane!r}")
    if prompt_version != CURRENT_TRANSLATOR_PROMPT:
        raise RecordError(
            f"new candidate assembly requires {CURRENT_TRANSLATOR_PROMPT}; "
            f"{prompt_version!r} is not a current production prompt"
        )
    source_commit = load_upstream_commit(lock_path)
    model_record_id = model_record_id or f"legacy:{model_id}:unknown"
    run_id = run_id or f"run-{model_lane}-{source_commit[:12]}"
    units = load_jsonl(unit_path)
    drafts = load_jsonl(draft_path)
    draft_by_id: dict[str, dict[str, object]] = {}
    for draft in drafts:
        unit_id = draft.get("unit_id")
        location = draft.get("_record_location", str(draft_path))
        if not isinstance(unit_id, str) or not unit_id:
            raise RecordError(f"{location}: draft requires a non-empty unit_id")
        if unit_id in draft_by_id:
            raise RecordError(f"{location}: duplicate draft unit_id {unit_id}")
        schema_value = {
            key: value for key, value in draft.items() if not key.startswith("_")
        }
        schema_errors = validate_named_schema(
            schema_value, "translator-output.schema.json", str(location)
        )
        if schema_errors:
            raise RecordError("translator output schema failed:\n" + "\n".join(schema_errors))
        draft_by_id[unit_id] = draft
    unit_ids = [unit["unit_id"] for unit in units]
    if set(draft_by_id) != set(unit_ids):
        missing = sorted(set(unit_ids) - set(draft_by_id))
        extra = sorted(set(draft_by_id) - set(unit_ids))
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("unknown: " + ", ".join(extra))
        raise RecordError("draft coverage mismatch (" + "; ".join(details) + ")")

    candidates: list[dict[str, object]] = []
    translator_fields = (
        "translation",
        "allowed_english",
        "term_occurrences",
        "unknown_terms",
        "notes",
    )
    for index, unit in enumerate(units):
        unit_id = unit["unit_id"]
        draft = draft_by_id[unit_id]
        for field in translator_fields:
            if field not in draft:
                raise RecordError(f"{draft.get('_record_location')}: missing {field}")
        neighbors = []
        if index:
            neighbors.append(units[index - 1]["unit_id"])
        if index + 1 < len(units):
            neighbors.append(units[index + 1]["unit_id"])
        context = {
            "approved_glossary_entries": [],
            "neighbor_unit_ids": neighbors,
            "policy_revision": policy_revision,
            "prompt_version": prompt_version,
            "source_commit": source_commit,
            "style_guide_path": "config/style-guide.md",
            "unit_id": unit_id,
        }
        unknown_terms = draft["unknown_terms"]
        term_status = "DECISION_REQUIRED" if unknown_terms else "CLEAR"
        candidate: dict[str, object] = {
            "schema_version": 2,
            "unit_id": unit_id,
            "source_commit": source_commit,
            "source_text_hash": unit["source_text_hash"],
            "model_id": model_id,
            "model_lane": model_lane,
            "harness_id": harness_id,
            "harness_version": harness_version,
            "model_record_id": model_record_id,
            "model_snapshot": model_snapshot,
            "model_identity_confidence": model_identity_confidence,
            "run_id": run_id,
            "reasoning_effort": reasoning_effort,
            "prompt_version": prompt_version,
            "glossary_revision": glossary_revision,
            "context": context,
            "context_hash": sha256_value(context),
            "translation": draft["translation"],
            "allowed_english": draft["allowed_english"],
            "term_occurrences": draft["term_occurrences"],
            "unknown_terms": unknown_terms,
            "notes": draft["notes"],
            "stage": "AI_DRAFT",
            "source_status": "CURRENT",
            "qa_status": "NOT_RUN",
            "term_status": term_status,
            "publication_status": "CANDIDATE",
            "created_at": created_at,
            "translation_hash": sha256_value(draft["translation"]),
        }
        candidates.append(candidate)

    errors = validate_records(units, candidates, source_commit)
    if errors:
        raise RecordError("candidate assembly failed:\n" + "\n".join(errors))
    for candidate in candidates:
        candidate["qa_status"] = "PASS"
        candidate["stage"] = (
            "STRUCTURE_OK"
            if candidate["term_status"] == "DECISION_REQUIRED"
            else "TERM_OK"
        )
    errors = validate_records(units, candidates, source_commit)
    if errors:
        raise RecordError("assembled candidate promotion failed:\n" + "\n".join(errors))
    write_jsonl(output_path, candidates)
    return len(candidates)


def render_batch(
    unit_path: Path | Iterable[Path],
    candidate_path: Path | Iterable[Path],
    lock_path: Path,
    output_dir: Path,
    model_lane: str,
    display_name: str,
    chapter_manifest_path: Path | None = None,
    tags_path: Path | None = None,
    chapter_source_dir: Path | None = None,
) -> list[Path]:
    if not SAFE_NAME_RE.fullmatch(model_lane) or ".." in model_lane:
        raise RecordError(f"invalid model lane {model_lane!r}")
    source_commit = load_upstream_commit(lock_path)
    unit_paths = [unit_path] if isinstance(unit_path, Path) else list(unit_path)
    candidate_paths = [candidate_path] if isinstance(candidate_path, Path) else list(candidate_path)
    if not unit_paths or not candidate_paths:
        raise RecordError("render requires at least one unit and candidate file")
    unit_batches = [load_jsonl(path) for path in unit_paths]
    units = [record for batch in unit_batches for record in batch]
    candidates = [record for path in candidate_paths for record in load_jsonl(path)]
    errors = validate_records(units, candidates, source_commit)
    if errors:
        raise RecordError("render blocked by validation errors:\n" + "\n".join(errors))
    if {candidate["model_lane"] for candidate in candidates} != {model_lane}:
        raise RecordError("candidate model_lane does not match --model-lane")

    resolved_labels = {
        label
        for unit in units
        for render_part in (
            unit["render"]["prefix"],
            unit["render"]["suffix"],
            *unit["placeholders"].values(),
        )
        for label in LABEL_RE.findall(render_part)
    }
    tags_by_label = _load_tags(tags_path) if tags_path is not None else {}
    if tags_path is not None:
        _validate_title_permanent_tags(units, tags_by_label, tags_path)
    if chapter_source_dir is not None:
        units = _order_unit_batches_by_chapter_source(
            unit_batches, chapter_source_dir
        )
    candidate_by_id = {candidate["unit_id"]: candidate for candidate in candidates}
    candidate_model_ids = {candidate.get("model_id") for candidate in candidates}
    candidate_harness_ids = {candidate.get("harness_id", "legacy") for candidate in candidates}
    candidate_run_ids = {candidate.get("run_id", "legacy") for candidate in candidates}
    if len(candidate_model_ids) != 1 or len(candidate_harness_ids) != 1:
        raise RecordError("render requires one concrete model and one Harness per preview")
    model_id = next(iter(candidate_model_ids))
    harness_id = next(iter(candidate_harness_ids))
    run_summary = (
        next(iter(candidate_run_ids))
        if len(candidate_run_ids) == 1
        else f"{len(candidate_run_ids)} runs (see translation-data/runs)"
    )
    chapter_chunks: dict[str, list[str]] = {}
    chapter_order: list[str] = []
    for unit in units:
        chapter = unit["chapter"]
        if not SAFE_NAME_RE.fullmatch(chapter) or ".." in chapter:
            raise RecordError(f"invalid chapter name {chapter!r}")
        if chapter not in chapter_chunks:
            chapter_order.append(chapter)
            chapter_chunks[chapter] = []
        candidate = candidate_by_id[unit["unit_id"]]
        placeholder_overrides: dict[str, str] = {}
        for name, value in unit["placeholders"].items():
            reference_match = REF_VALUE_RE.fullmatch(value)
            if reference_match is None:
                continue
            label = reference_match.group(1)
            if label in resolved_labels:
                continue
            if tags_path is None:
                continue
            tag = tags_by_label.get(label)
            if tag is None:
                raise RecordError(
                    f"{unit['unit_id']}: unresolved reference {label!r} has no permanent "
                    f"Tag in {tags_path}"
                )
            placeholder_overrides[name] = (
                f"\\href{{https://stacks.math.columbia.edu/tag/{tag}}}"
                f"{{Tag {tag}（待译）}}"
            )
        translated = restore_placeholders(
            unit, candidate["translation"], placeholder_overrides
        )
        render = unit["render"]
        chapter_chunks[chapter].append(render["prefix"] + translated + render["suffix"])

    chapter_titles: dict[str, str] = {}
    if chapter_manifest_path is not None:
        try:
            manifest_text = chapter_manifest_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RecordError(f"cannot read chapter manifest {chapter_manifest_path}: {exc}") from exc
        canonical_chapters = manifest_chapters(manifest_text)
        canonical_order = [chapter for chapter, _ in canonical_chapters]
        chapter_titles = dict(canonical_chapters)
        order_index = {chapter: index for index, chapter in enumerate(canonical_order)}
        unknown_chapters = sorted(set(chapter_order) - set(order_index))
        if unknown_chapters:
            raise RecordError(
                f"{chapter_manifest_path}: rendered chapters absent from manifest: "
                + ", ".join(unknown_chapters)
            )
        chapter_order = canonical_order

    output_dir.mkdir(parents=True, exist_ok=True)
    chapters_dir = output_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for chapter in chapter_order:
        chapter_path = chapters_dir / f"{chapter}.tex"
        chunks = chapter_chunks.get(chapter)
        chapter_text = (
            "".join(chunks)
            if chunks
            else _pending_chapter_template(chapter, chapter_titles[chapter])
        )
        chapter_path.write_text(chapter_text, encoding="utf-8")
        written.append(chapter_path)

    metadata = output_dir / "metadata.tex"
    metadata.write_text(
        "% Generated from translation-data; do not edit.\n"
        f"\\renewcommand{{\\TranslationModelName}}{{{display_name} ({model_id})}}\n"
        "\\renewcommand{\\TranslationMaintainer}{OpenSSL}\n"
        "\\renewcommand{\\TranslationStatus}{未经人工审校的模型候选译文}\n"
        f"\\renewcommand{{\\TranslationNotice}}{{本预览依据英文源提交 {source_commit[:12]}；"
        f"Harness={harness_id}；模型={model_id}；运行={run_summary}；"
        "尚未完成人工语言或数学审校，不得作为正式译本发布。}\n",
        encoding="utf-8",
    )
    written.append(metadata)
    contents = output_dir / "contents.tex"
    contents.write_text(
        "% Generated from translation-data; do not edit.\n"
        + "".join(
            f"\\input{{\\TranslationModelDirectory/chapters/{chapter}}}\n"
            for chapter in chapter_order
        ),
        encoding="utf-8",
    )
    written.append(contents)
    return written


def _pending_chapter_template(chapter: str, source_title: str) -> str:
    return (
        "% Generated untranslated chapter scaffold; do not edit this preview file.\n"
        f"\\chapter{{{source_title}（待译）}}\n"
        "\\phantomsection\n"
        f"\\label{{{chapter}-section-phantom}}\n\n"
        "\\noindent\n"
        "\\emph{本章翻译模板已初始化，正文待翻译。}\n\n"
    )


def _load_tags(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RecordError(f"cannot read permanent Tag map {path}: {exc}") from exc
    tags_by_label: dict[str, str] = {}
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(",")
        if len(parts) != 2:
            raise RecordError(f"{path}:{line_number}: expected TAG,full_label")
        tag, label = (part.strip() for part in parts)
        if not TAG_RE.fullmatch(tag):
            raise RecordError(f"{path}:{line_number}: invalid permanent Tag {tag!r}")
        if not TAG_LABEL_RE.fullmatch(label):
            raise RecordError(f"{path}:{line_number}: invalid full label {label!r}")
        previous = tags_by_label.get(label)
        if previous is not None and previous != tag:
            raise RecordError(
                f"{path}:{line_number}: label {label!r} maps to both {previous} and {tag}"
            )
        tags_by_label[label] = tag
    if not tags_by_label:
        raise RecordError(f"{path}: no permanent Tags")
    return tags_by_label


def _validate_title_permanent_tags(
    units: list[dict[str, object]],
    tags_by_label: dict[str, str],
    tags_path: Path,
) -> None:
    for unit in units:
        node_kind = unit["node_kind"]
        if not isinstance(node_kind, str) or not node_kind.endswith("_title"):
            continue
        render = unit["render"]
        placeholders = unit["placeholders"]
        assert isinstance(render, dict)
        assert isinstance(placeholders, dict)
        labels = [
            label
            for render_part in (
                render["prefix"],
                render["suffix"],
                *placeholders.values(),
            )
            for label in LABEL_RE.findall(str(render_part))
        ]
        if not labels:
            raise RecordError(
                f"{unit['unit_id']}: title unit has no rendered label to verify "
                f"against {tags_path}"
            )
        mapped_tags: dict[str, str] = {}
        for label in labels:
            tag = tags_by_label.get(label)
            if tag is None:
                raise RecordError(
                    f"{unit['unit_id']}: rendered title label {label!r} has no "
                    f"permanent Tag in {tags_path}"
                )
            mapped_tags[label] = tag
        parent_tag = unit["parent_tag"]
        if parent_tag not in mapped_tags.values():
            mappings = ", ".join(
                f"{label}={tag}" for label, tag in mapped_tags.items()
            )
            raise RecordError(
                f"{unit['unit_id']}: parent_tag {parent_tag!r} does not match "
                f"rendered title permanent Tag ({mappings})"
            )


def _order_unit_batches_by_chapter_source(
    unit_batches: list[list[dict[str, object]]],
    chapter_source_dir: Path,
) -> list[dict[str, object]]:
    """Order batches by their first label while preserving each batch's AST order."""
    batches_by_chapter: dict[str, list[list[dict[str, object]]]] = {}
    chapter_order: list[str] = []
    for batch in unit_batches:
        if not batch:
            raise RecordError("render unit batch is empty")
        chapters = {str(unit["chapter"]) for unit in batch}
        if len(chapters) != 1:
            raise RecordError("render unit batch spans multiple chapters")
        chapter = chapters.pop()
        if chapter not in batches_by_chapter:
            chapter_order.append(chapter)
            batches_by_chapter[chapter] = []
        batches_by_chapter[chapter].append(batch)

    ordered: list[dict[str, object]] = []
    for chapter in chapter_order:
        source_path = chapter_source_dir / f"{chapter}.tex"
        try:
            source_text = source_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RecordError(f"cannot read chapter source {source_path}: {exc}") from exc
        source_labels = LABEL_RE.findall(source_text)
        if len(source_labels) != len(set(source_labels)):
            raise RecordError(f"{source_path}: duplicate source labels")
        source_index = {label: index for index, label in enumerate(source_labels)}

        batch_positions: list[tuple[int, list[dict[str, object]]]] = []
        for batch in batches_by_chapter[chapter]:
            matching_positions = []
            for unit in batch:
                for render_part in (
                    unit["render"]["prefix"],
                    unit["render"]["suffix"],
                    *unit["placeholders"].values(),
                ):
                    for label in LABEL_RE.findall(str(render_part)):
                        local_label = label.removeprefix(f"{chapter}-")
                        if local_label in source_index:
                            matching_positions.append(source_index[local_label])
                        elif label in source_index:
                            matching_positions.append(source_index[label])
            if not matching_positions:
                raise RecordError(
                    f"{batch[0]['unit_id']}: batch has no rendered label in {source_path}"
                )
            batch_positions.append((min(matching_positions), batch))
        for _, batch in sorted(batch_positions, key=lambda item: item[0]):
            ordered.extend(batch)
    return ordered
