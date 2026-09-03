from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Iterable

from .chapter_templates import manifest_chapters
from .harness import resolve_harness_version
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
TAG_UNIT_RE = re.compile(r"^tag:(?P<tag>[0-9A-Z]+):")
NUMBERED_PROOF_RE = re.compile(r"^tag:(?P<tag>[0-9A-Z]+):proof-[0-9]+-")
PROOF_ENV_RE = re.compile(r"\\(?:begin|end)\{proof\}")
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


def validate_batches(
    unit_paths: Iterable[Path],
    candidate_paths: Iterable[Path],
    lock_path: Path,
) -> tuple[int, list[str]]:
    """Validate several candidate batches in one process.

    Each unit/candidate path pair remains an independent fact boundary.  The
    batch wrapper adds only cross-pair checks needed for a single model run:
    no duplicate units and one model, Harness, and run across the batch.
    """
    unit_paths = list(unit_paths)
    candidate_paths = list(candidate_paths)
    if not unit_paths or not candidate_paths:
        raise RecordError("batch validation requires at least one unit/candidate pair")
    if len(unit_paths) != len(candidate_paths):
        raise RecordError(
            "batch validation requires the same number of unit and candidate files "
            f"(got {len(unit_paths)} and {len(candidate_paths)})"
        )

    source_commit = load_upstream_commit(lock_path)
    errors: list[str] = []
    seen_unit_ids: dict[str, Path] = {}
    seen_candidate_ids: dict[str, Path] = {}
    metadata: dict[str, object] = {}
    total_candidates = 0
    for index, (unit_path, candidate_path) in enumerate(
        zip(unit_paths, candidate_paths, strict=True), start=1
    ):
        try:
            units = load_jsonl(unit_path)
            candidates = load_jsonl(candidate_path)
        except RecordError as exc:
            errors.append(f"batch {index}: {exc}")
            continue

        pair_errors = validate_records(units, candidates, source_commit)
        errors.extend(
            f"batch {index} ({unit_path.name}): {error}" for error in pair_errors
        )
        total_candidates += len(candidates)
        for unit in units:
            unit_id = unit.get("unit_id")
            if not isinstance(unit_id, str) or not unit_id:
                continue
            previous = seen_unit_ids.get(unit_id)
            if previous is not None:
                errors.append(
                    f"batch {index} ({unit_path.name}): duplicate unit_id {unit_id} "
                    f"also present in {previous}"
                )
            else:
                seen_unit_ids[unit_id] = unit_path
        for candidate in candidates:
            unit_id = candidate.get("unit_id")
            if not isinstance(unit_id, str) or not unit_id:
                continue
            previous = seen_candidate_ids.get(unit_id)
            if previous is not None:
                errors.append(
                    f"batch {index} ({candidate_path.name}): duplicate candidate "
                    f"unit_id {unit_id} also present in {previous}"
                )
            else:
                seen_candidate_ids[unit_id] = candidate_path
            for key in ("model_lane", "model_id", "harness_id", "run_id"):
                value = candidate.get(key)
                if value is None:
                    continue
                expected = metadata.get(key)
                if expected is None:
                    metadata[key] = value
                elif expected != value:
                    errors.append(
                        f"batch {index} ({candidate_path.name}): batch metadata "
                        f"mismatch for {key}: expected {expected!r}, got {value!r}"
                    )
    return total_candidates, errors


def _load_translator_drafts(draft_path: Path) -> dict[str, dict[str, object]]:
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
    return draft_by_id


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
    harness_version: str = "auto",
    model_record_id: str | None = None,
    run_id: str | None = None,
    model_snapshot: str | None = None,
    model_identity_confidence: str = "unknown",
    harness_config_path: Path | None = None,
) -> int:
    if not SAFE_NAME_RE.fullmatch(model_lane) or ".." in model_lane:
        raise RecordError(f"invalid model lane {model_lane!r}")
    if prompt_version != CURRENT_TRANSLATOR_PROMPT:
        raise RecordError(
            f"new candidate assembly requires {CURRENT_TRANSLATOR_PROMPT}; "
            f"{prompt_version!r} is not a current production prompt"
        )
    if not harness_id or harness_id == "unknown":
        raise RecordError("new candidate assembly requires a registered harness_id")
    if harness_version != "auto":
        raise RecordError(
            "new candidate assembly resolves harness_version dynamically; "
            "use --harness-version auto"
        )
    config_path = harness_config_path or Path("config/harnesses.yml")
    try:
        harness_version = resolve_harness_version(harness_id, config_path)
    except ValueError as exc:
        raise RecordError(f"cannot resolve Harness version: {exc}") from exc
    return _assemble_candidates_with_harness_version(
        unit_path,
        draft_path,
        output_path,
        lock_path,
        model_id,
        model_lane,
        reasoning_effort,
        prompt_version,
        policy_revision,
        glossary_revision,
        created_at,
        harness_id,
        harness_version,
        model_record_id,
        run_id,
        model_snapshot,
        model_identity_confidence,
    )


def _assemble_candidates_with_harness_version(
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
    harness_id: str,
    harness_version: str,
    model_record_id: str | None,
    run_id: str | None,
    model_snapshot: str | None,
    model_identity_confidence: str,
) -> int:
    source_commit = load_upstream_commit(lock_path)
    model_record_id = model_record_id or f"legacy:{model_id}:unknown"
    run_id = run_id or f"run-{model_lane}-{source_commit[:12]}"
    units = load_jsonl(unit_path)
    draft_by_id = _load_translator_drafts(draft_path)
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


def assemble_candidates_many(
    unit_paths: Iterable[Path],
    draft_path: Path,
    output_paths: Iterable[Path],
    lock_path: Path,
    model_id: str,
    model_lane: str,
    reasoning_effort: str,
    prompt_version: str,
    policy_revision: str,
    glossary_revision: str,
    created_at: str,
    harness_id: str,
    harness_version: str = "auto",
    model_record_id: str | None = None,
    run_id: str | None = None,
    model_snapshot: str | None = None,
    model_identity_confidence: str = "unknown",
    harness_config_path: Path | None = None,
) -> int:
    """Assemble one combined translator JSONL into independent candidates atomically."""

    unit_paths = list(unit_paths)
    output_paths = list(output_paths)
    if len(unit_paths) != len(output_paths):
        raise RecordError(
            "batch assembly requires the same number of unit and output files"
        )
    if not 2 <= len(unit_paths) <= 8:
        raise RecordError(
            f"batch assembly requires 2-8 unit/output pairs (got {len(unit_paths)})"
        )
    normalized_outputs = [path.resolve() for path in output_paths]
    if len(set(normalized_outputs)) != len(normalized_outputs):
        raise RecordError("batch assembly output files must be unique")
    protected_inputs = {
        path.resolve() for path in (*unit_paths, draft_path, lock_path)
    }
    overlaps = sorted(str(path) for path in set(normalized_outputs) & protected_inputs)
    if overlaps:
        raise RecordError(
            "batch assembly outputs must not overwrite inputs: " + ", ".join(overlaps)
        )
    if not SAFE_NAME_RE.fullmatch(model_lane) or ".." in model_lane:
        raise RecordError(f"invalid model lane {model_lane!r}")
    if prompt_version != CURRENT_TRANSLATOR_PROMPT:
        raise RecordError(
            f"new candidate assembly requires {CURRENT_TRANSLATOR_PROMPT}; "
            f"{prompt_version!r} is not a current production prompt"
        )
    if not harness_id or harness_id == "unknown":
        raise RecordError("new candidate assembly requires a registered harness_id")
    if harness_version != "auto":
        raise RecordError(
            "new candidate assembly resolves harness_version dynamically; "
            "use --harness-version auto"
        )

    source_commit = load_upstream_commit(lock_path)
    units_by_path: list[list[dict[str, object]]] = []
    unit_owner: dict[str, int] = {}
    unit_ids: list[str] = []
    chapter: str | None = None
    for index, path in enumerate(unit_paths):
        units = load_jsonl(path)
        units_by_path.append(units)
        for unit in units:
            unit_id = unit.get("unit_id")
            if not isinstance(unit_id, str) or not unit_id:
                raise RecordError(f"{path}: unit requires a non-empty unit_id")
            if unit_id in unit_owner:
                raise RecordError(
                    f"{path}: duplicate unit_id {unit_id} also present in "
                    f"{unit_paths[unit_owner[unit_id]]}"
                )
            if unit.get("source_commit") != source_commit:
                raise RecordError(f"{path}: unit does not match upstream.lock")
            unit_chapter = unit.get("chapter")
            if not isinstance(unit_chapter, str) or not unit_chapter:
                raise RecordError(f"{path}: unit requires a non-empty chapter")
            if chapter is None:
                chapter = unit_chapter
            elif chapter != unit_chapter:
                raise RecordError(
                    f"{path}: batch assembly cannot cross chapters "
                    f"({chapter!r} and {unit_chapter!r})"
                )
            unit_owner[unit_id] = index
            unit_ids.append(unit_id)

    drafts_by_id = _load_translator_drafts(draft_path)
    missing = sorted(set(unit_ids) - set(drafts_by_id))
    extra = sorted(set(drafts_by_id) - set(unit_ids))
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("unknown: " + ", ".join(extra))
        raise RecordError("draft coverage mismatch (" + "; ".join(details) + ")")

    config_path = harness_config_path or Path("config/harnesses.yml")
    try:
        resolved_version = resolve_harness_version(harness_id, config_path)
    except ValueError as exc:
        raise RecordError(f"cannot resolve Harness version: {exc}") from exc

    temp_outputs: list[tuple[Path, Path]] = []
    temporary_paths: set[Path] = set()
    try:
        for index, (units, output_path) in enumerate(
            zip(units_by_path, output_paths, strict=True)
        ):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_name = tempfile.mkstemp(
                prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent
            )
            os.close(fd)
            temp_output = Path(temp_name)
            temp_draft = temp_output.with_suffix(".draft.jsonl")
            temporary_paths.update((temp_output, temp_draft))
            write_jsonl(temp_draft, (drafts_by_id[unit["unit_id"]] for unit in units))
            _assemble_candidates_with_harness_version(
                unit_paths[index],
                temp_draft,
                temp_output,
                lock_path,
                model_id,
                model_lane,
                reasoning_effort,
                prompt_version,
                policy_revision,
                glossary_revision,
                created_at,
                harness_id,
                resolved_version,
                model_record_id,
                run_id,
                model_snapshot,
                model_identity_confidence,
            )
            temp_draft.unlink(missing_ok=True)
            temporary_paths.discard(temp_draft)
            temp_outputs.append((temp_output, output_path))
        for temp_output, output_path in temp_outputs:
            os.replace(temp_output, output_path)
            temporary_paths.discard(temp_output)
    finally:
        for temporary_path in temporary_paths:
            temporary_path.unlink(missing_ok=True)
    return len(unit_ids)


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
    chapter_title_path: Path | None = None,
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
        for batch in unit_batches:
            _validate_title_permanent_tags(batch, tags_by_label, tags_path)
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
    chapters_with_rendered_titles: set[str] = set()
    chapter_order: list[str] = []
    for unit in units:
        chapter = unit["chapter"]
        if not SAFE_NAME_RE.fullmatch(chapter) or ".." in chapter:
            raise RecordError(f"invalid chapter name {chapter!r}")
        if chapter not in chapter_chunks:
            chapter_order.append(chapter)
            chapter_chunks[chapter] = []
        if unit["node_kind"] == "chapter_title":
            chapters_with_rendered_titles.add(chapter)
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
            resolved = _permanent_tag_for_label(label, chapter, tags_by_label)
            if resolved is None:
                raise RecordError(
                    f"{unit['unit_id']}: unresolved reference {label!r} has no permanent "
                    f"Tag in {tags_path}"
                )
            _, tag = resolved
            placeholder_overrides[name] = (
                f"\\href{{https://stacks.math.columbia.edu/tag/{tag}}}"
                f"{{Tag {tag}（待译）}}"
            )
        translated = restore_placeholders(
            unit, candidate["translation"], placeholder_overrides
        )
        render = unit["render"]
        chapter_chunks[chapter].append(render["prefix"] + translated + render["suffix"])

    chapter_titles: dict[str, tuple[str, str]] = {}
    if chapter_manifest_path is not None:
        try:
            manifest_text = chapter_manifest_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RecordError(f"cannot read chapter manifest {chapter_manifest_path}: {exc}") from exc
        canonical_chapters = manifest_chapters(manifest_text)
        canonical_order = [chapter for chapter, _ in canonical_chapters]
        source_titles = dict(canonical_chapters)
        translated_titles = (
            _load_chapter_title_translations(chapter_title_path, canonical_order)
            if chapter_title_path is not None
            else source_titles
        )
        chapter_titles = {
            chapter: (translated_titles[chapter], source_titles[chapter])
            for chapter in canonical_order
        }
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
        if chunks:
            chapter_text = "".join(chunks)
            if chapter_titles and chapter not in chapters_with_rendered_titles:
                chapter_text = (
                    _chapter_scaffold(chapter, *chapter_titles[chapter]) + chapter_text
                )
        else:
            chapter_text = _chapter_scaffold(chapter, *chapter_titles[chapter])
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


def _load_chapter_title_translations(path: Path, chapters: list[str]) -> dict[str, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RecordError(f"cannot read chapter title map {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RecordError(f"{path}: invalid chapter title JSON: {exc.msg}") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise RecordError(f"{path}: chapter title map requires schema_version 1")
    titles = value.get("titles")
    if not isinstance(titles, dict):
        raise RecordError(f"{path}: chapter title map requires a titles object")
    expected = set(chapters)
    actual = set(titles)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("extra: " + ", ".join(extra))
        raise RecordError(f"{path}: chapter title coverage mismatch ({'; '.join(details)})")
    for chapter, title in titles.items():
        if not isinstance(title, str) or not title.strip():
            raise RecordError(f"{path}: chapter {chapter!r} requires a non-empty title")
    return titles


def _chapter_scaffold(chapter: str, target_title: str, source_title: str) -> str:
    display_title = (
        source_title if target_title == source_title else f"{target_title}（{source_title}）"
    )
    return (
        "% Generated chapter scaffold; do not edit this preview file.\n"
        f"\\chapter{{{display_title}}}\n"
        "\\phantomsection\n"
        f"\\label{{{chapter}-section-phantom}}\n\n"
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


def _permanent_tag_for_label(
    label: str,
    chapter: str,
    tags_by_label: dict[str, str],
) -> tuple[str, str] | None:
    tag = tags_by_label.get(label)
    if tag is not None:
        return label, tag
    full_label = f"{chapter}-{label}"
    tag = tags_by_label.get(full_label)
    if tag is not None:
        return full_label, tag
    return None


def _rendered_unit_labels(unit: dict[str, object]) -> list[str]:
    render = unit["render"]
    placeholders = unit["placeholders"]
    assert isinstance(render, dict)
    assert isinstance(placeholders, dict)
    return [
        label
        for render_part in (render["prefix"], render["suffix"], *placeholders.values())
        for label in LABEL_RE.findall(str(render_part))
    ]


def _proof_title_owner_labels(units: list[dict[str, object]], index: int) -> list[str]:
    """Resolve a standalone proof title only through its adjacent statement."""
    title = units[index]
    render = title["render"]
    assert isinstance(render, dict)
    tag_match = TAG_UNIT_RE.match(str(title["unit_id"]))
    if (
        title["node_kind"] != "environment_title"
        or tag_match is None
        or title["unit_id"] != f"tag:{tag_match.group('tag')}:proof-title"
        or render["prefix"] != "\\begin{proof}["
        or str(render["suffix"]).rstrip() != "]"
        or index == 0
        or index + 1 == len(units)
    ):
        return []
    owner, body = units[index - 1], units[index + 1]
    tag = tag_match.group("tag")
    owner_kind = owner["node_kind"]
    owner_render, body_render = owner["render"], body["render"]
    assert isinstance(owner_render, dict)
    assert isinstance(body_render, dict)
    if (
        owner_kind not in {"lemma", "proposition", "theorem", "corollary"}
        or owner["unit_id"] != f"tag:{tag}:statement"
        or not str(owner_render["prefix"]).lstrip().startswith(f"\\begin{{{owner_kind}}}")
        or str(owner_render["suffix"]).strip() != f"\\end{{{owner_kind}}}"
        or body["node_kind"] != "proof"
        or body["unit_id"] != f"tag:{tag}:proof-p001"
        or str(body_render["prefix"]).strip()
        or any(
            neighbor[key] != title[key]
            for neighbor in (owner, body)
            for key in ("chapter", "parent_tag")
        )
    ):
        return []
    return _rendered_unit_labels(owner)


def _numbered_proof_title_owner_labels(
    units: list[dict[str, object]],
) -> dict[int, list[str]]:
    """Validate complete adjacent proof groups before borrowing their owner's labels."""
    labels_by_index: dict[int, list[str]] = {}
    seen_tags: set[str] = set()
    index = 0
    while index < len(units):
        match = NUMBERED_PROOF_RE.match(str(units[index]["unit_id"]))
        if match is None:
            index += 1
            continue
        first = units[index]
        tag = match.group("tag")

        def require(condition: bool, reason: str) -> None:
            if not condition:
                raise RecordError(f"{first['unit_id']}: invalid numbered proof group: {reason}")

        def same_owner(unit: dict[str, object]) -> bool:
            return all(unit[key] == first[key] for key in ("chapter", "parent_tag"))

        def has_embedded_proof(unit: dict[str, object]) -> bool:
            return any(
                PROOF_ENV_RE.search(str(part))
                for part in (unit["source_text"], *unit["placeholders"].values())
            )

        require(index > 0 and tag not in seen_tags, "missing or repeated owner")
        owner = units[index - 1]
        kind = owner["node_kind"]
        require(
            kind in {"lemma", "proposition", "theorem", "corollary"}
            and owner["unit_id"] == f"tag:{tag}:statement"
            and same_owner(owner)
            and str(owner["render"]["prefix"]).lstrip().startswith(f"\\begin{{{kind}}}")
            and str(owner["render"]["suffix"]).strip() == f"\\end{{{kind}}}"
            and not has_embedded_proof(owner)
            and not PROOF_ENV_RE.search(
                str(owner["render"]["prefix"]) + str(owner["render"]["suffix"])
            ),
            "expected an adjacent complete statement with matching coordinates",
        )
        labels = _rendered_unit_labels(owner)
        require(bool(labels), "owner has no rendered label")
        seen_tags.add(tag)
        group = 1
        while True:
            title = units[index]
            stem = f"tag:{tag}:proof-{group:03d}"
            require(
                group <= 999
                and title["unit_id"] == f"{stem}-title"
                and title["node_kind"] == "environment_title"
                and same_owner(title)
                and title["render"]["prefix"] == "\\begin{proof}["
                and str(title["render"]["suffix"]).rstrip() == "]"
                and not _rendered_unit_labels(title)
                and not has_embedded_proof(title),
                "expected a sequential unlabeled proof title with exact wrappers",
            )
            labels_by_index[index] = labels
            index += 1
            paragraph = 1
            while True:
                require(index < len(units), "missing proof body or closing wrapper")
                body = units[index]
                prefix = str(body["render"]["prefix"]).strip()
                suffix = str(body["render"]["suffix"]).strip()
                require(
                    paragraph <= 999
                    and body["unit_id"] == f"{stem}-p{paragraph:03d}"
                    and body["node_kind"] == "proof"
                    and same_owner(body)
                    and prefix in ({""} if paragraph == 1 else {"", "\\medskip\\noindent"})
                    and suffix in {"", "\\end{proof}"}
                    and not has_embedded_proof(body),
                    "expected a sequential proof paragraph with matching coordinates and wrappers",
                )
                index += 1
                paragraph += 1
                if suffix == "\\end{proof}":
                    break
            following = (
                NUMBERED_PROOF_RE.match(str(units[index]["unit_id"]))
                if index < len(units) else None
            )
            if following is None or following.group("tag") != tag:
                break
            group += 1
        require(group >= 2, "numbered proofs require at least two complete groups")
    return labels_by_index


def _validate_title_permanent_tags(
    units: list[dict[str, object]],
    tags_by_label: dict[str, str],
    tags_path: Path,
) -> None:
    numbered_labels = _numbered_proof_title_owner_labels(units)
    for index, unit in enumerate(units):
        node_kind = unit["node_kind"]
        if not isinstance(node_kind, str) or not node_kind.endswith("_title"):
            continue
        labels = numbered_labels.get(index) or _rendered_unit_labels(unit)
        if not labels:
            labels = _proof_title_owner_labels(units, index)
        if not labels:
            raise RecordError(
                f"{unit['unit_id']}: title unit has no rendered label to verify "
                f"against {tags_path}"
            )
        chapter = unit["chapter"]
        assert isinstance(chapter, str)
        mapped_tags: dict[str, str] = {}
        for label in labels:
            resolved = _permanent_tag_for_label(label, chapter, tags_by_label)
            if resolved is None:
                raise RecordError(
                    f"{unit['unit_id']}: rendered title label {label!r} has no "
                    f"permanent Tag in {tags_path}"
                )
            full_label, tag = resolved
            mapped_tags[full_label] = tag
        unit_id = unit["unit_id"]
        assert isinstance(unit_id, str)
        tag_match = TAG_UNIT_RE.match(unit_id)
        if tag_match is None:
            raise RecordError(
                f"{unit_id}: title unit_id does not encode a permanent Tag"
            )
        unit_tag = tag_match.group("tag")
        if unit_tag not in mapped_tags.values():
            mappings = ", ".join(
                f"{label}={tag}" for label, tag in mapped_tags.items()
            )
            raise RecordError(
                f"{unit_id}: unit Tag {unit_tag!r} does not match "
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
