from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .records import RecordError, load_upstream_commit


README_START = "<!-- translation-progress:start -->"
README_END = "<!-- translation-progress:end -->"

CHAPTER_STATUS_ORDER = (
    "未开始",
    "翻译中",
    "候选译文完成，待审校",
    "人工审校中",
    "人工审校完成，待发布",
    "发布中",
    "已发布",
    "不适用",
)

LABEL_RE = re.compile(r"\\label\{(?P<label>[^{}\r\n]+)\}")
TAG_UNIT_RE = re.compile(r"^tag:(?P<tag>[0-9A-Z]+):")
LABEL_UNIT_RE = re.compile(r"^label:(?P<label>.+):[^:]+$")


@dataclass(frozen=True)
class SectionProgress:
    ordinal: int
    source_title: str
    parent_tag: str
    required_tags: int
    prepared_tags: int
    total_units: int
    candidate_units: int
    reviewed_units: int
    published_units: int

    @property
    def candidate_started(self) -> bool:
        return self.candidate_units > 0

    @property
    def candidate_complete(self) -> bool:
        return (
            self.total_units > 0
            and self.prepared_tags == self.required_tags
            and self.candidate_units == self.total_units
        )

    @property
    def reviewed_started(self) -> bool:
        return self.reviewed_units > 0

    @property
    def reviewed_complete(self) -> bool:
        return (
            self.total_units > 0
            and self.prepared_tags == self.required_tags
            and self.reviewed_units == self.total_units
        )

    @property
    def published_started(self) -> bool:
        return self.published_units > 0

    @property
    def published_complete(self) -> bool:
        return (
            self.total_units > 0
            and self.prepared_tags == self.required_tags
            and self.published_units == self.total_units
        )

    @staticmethod
    def _stage(started: bool, complete: bool) -> str:
        if complete:
            return "完成"
        if started:
            return "进行中"
        return "未开始"

    @property
    def candidate_stage(self) -> str:
        return self._stage(self.candidate_started, self.candidate_complete)

    @property
    def reviewed_stage(self) -> str:
        return self._stage(self.reviewed_started, self.reviewed_complete)

    @property
    def published_stage(self) -> str:
        return self._stage(self.published_started, self.published_complete)


@dataclass(frozen=True)
class ChapterProgress:
    ordinal: int
    slug: str
    title: str
    source_state: str
    sections: tuple[SectionProgress, ...]

    @property
    def total_sections(self) -> int:
        return len(self.sections)

    @property
    def candidate_complete_sections(self) -> int:
        return sum(section.candidate_complete for section in self.sections)

    @property
    def candidate_started_sections(self) -> int:
        return sum(section.candidate_started for section in self.sections)

    @property
    def candidate_active_sections(self) -> int:
        return sum(
            section.candidate_started and not section.candidate_complete
            for section in self.sections
        )

    @property
    def candidate_unstarted_sections(self) -> int:
        return sum(not section.candidate_started for section in self.sections)

    @property
    def reviewed_complete_sections(self) -> int:
        return sum(section.reviewed_complete for section in self.sections)

    @property
    def reviewed_started_sections(self) -> int:
        return sum(section.reviewed_started for section in self.sections)

    @property
    def published_complete_sections(self) -> int:
        return sum(section.published_complete for section in self.sections)

    @property
    def published_started_sections(self) -> int:
        return sum(section.published_started for section in self.sections)

    @property
    def status(self) -> str:
        if not self.sections:
            return "不适用"
        if self.published_complete_sections == self.total_sections:
            return "已发布"
        if self.published_started_sections:
            return "发布中"
        if self.reviewed_complete_sections == self.total_sections:
            return "人工审校完成，待发布"
        if self.reviewed_started_sections:
            return "人工审校中"
        if self.candidate_complete_sections == self.total_sections:
            return "候选译文完成，待审校"
        if self.candidate_started_sections:
            return "翻译中"
        return "未开始"


@dataclass(frozen=True)
class ProgressSnapshot:
    source_commit: str
    chapters: tuple[ChapterProgress, ...]
    current_units: int
    candidate_units: int

    @property
    def content_chapters(self) -> tuple[ChapterProgress, ...]:
        return tuple(chapter for chapter in self.chapters if chapter.total_sections)

    @property
    def sections(self) -> tuple[SectionProgress, ...]:
        return tuple(section for chapter in self.chapters for section in chapter.sections)


@dataclass(frozen=True)
class _TagIndex:
    chapter_by_tag: dict[str, str]
    label_by_tag: dict[str, str]
    tag_by_label: dict[str, str]


@dataclass(frozen=True)
class _ChapterSource:
    sections: tuple[tuple[int, str, str, frozenset[str]], ...]
    section_by_tag: dict[str, int]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RecordError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RecordError(f"{path}: JSON root must be an object")
    return value


def _read_jsonl(paths: Iterable[Path]) -> Iterable[tuple[Path, int, dict[str, Any]]]:
    for path in sorted(paths):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise RecordError(f"cannot read JSONL {path}: {exc}") from exc
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except ValueError as exc:
                raise RecordError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise RecordError(f"{path}:{line_number}: record must be an object")
            yield path, line_number, value


def _load_chapters(root: Path, source_commit: str) -> list[dict[str, Any]]:
    templates = [
        _read_json(path)
        for path in sorted((root / "translation-data/chapter-templates").glob("*.json"))
    ]
    if not templates:
        raise RecordError("translation-data/chapter-templates: no chapter templates")
    templates.sort(key=lambda item: item.get("chapter_ordinal", 0))
    expected_ordinals = list(range(1, len(templates) + 1))
    actual_ordinals = [item.get("chapter_ordinal") for item in templates]
    if actual_ordinals != expected_ordinals:
        raise RecordError("chapter templates do not have contiguous unique ordinals")
    slugs = [item.get("chapter") for item in templates]
    if not all(isinstance(slug, str) and slug for slug in slugs) or len(set(slugs)) != len(slugs):
        raise RecordError("chapter templates do not have unique non-empty chapter slugs")
    for template in templates:
        if template.get("source_commit") != source_commit:
            raise RecordError(
                f"chapter template {template.get('chapter')!r} does not match upstream.lock"
            )
    return templates


def _load_titles(root: Path) -> dict[str, str]:
    value = _read_json(root / "config/chapter-titles.json").get("titles")
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(title, str) and title
        for key, title in value.items()
    ):
        raise RecordError("config/chapter-titles.json: titles must map slugs to strings")
    return value


def _load_tag_index(tags_path: Path, chapter_slugs: set[str]) -> _TagIndex:
    try:
        lines = tags_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RecordError(f"cannot read permanent Tag map {tags_path}: {exc}") from exc
    sorted_slugs = sorted(chapter_slugs, key=len, reverse=True)
    chapter_by_tag: dict[str, str] = {}
    label_by_tag: dict[str, str] = {}
    tag_by_label: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "," not in line:
            raise RecordError(f"{tags_path}:{line_number}: expected TAG,label")
        tag, label = line.split(",", 1)
        if tag in chapter_by_tag or label in tag_by_label:
            raise RecordError(f"{tags_path}:{line_number}: duplicate permanent Tag or label")
        chapter = next(
            (slug for slug in sorted_slugs if label.startswith(f"{slug}-")), None
        )
        if chapter is None:
            if label.startswith("book-part-"):
                continue
            raise RecordError(
                f"{tags_path}:{line_number}: Tag {tag} is not assigned to a chapter"
            )
        chapter_by_tag[tag] = chapter
        label_by_tag[tag] = label
        tag_by_label[label] = tag
    if not chapter_by_tag:
        raise RecordError(f"{tags_path}: no chapter permanent Tags")
    return _TagIndex(chapter_by_tag, label_by_tag, tag_by_label)


def _full_label(chapter: str, label: str) -> str:
    return label if label.startswith(f"{chapter}-") else f"{chapter}-{label}"


def _requires_translation(chapter: str, full_label: str) -> bool:
    local_label = full_label.removeprefix(f"{chapter}-")
    return not local_label.startswith("equation-")


def _chapter_source(
    harvest_root: Path,
    template: dict[str, Any],
    tag_index: _TagIndex,
) -> _ChapterSource:
    chapter = str(template["chapter"])
    raw_sections = template.get("sections")
    if not isinstance(raw_sections, list):
        raise RecordError(f"chapter template {chapter!r}: sections must be an array")
    if not raw_sections:
        return _ChapterSource((), {})
    source_file = template.get("source_file")
    if not isinstance(source_file, str) or not source_file:
        raise RecordError(f"chapter template {chapter!r}: source_file is required")
    source_path = harvest_root / source_file
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordError(f"cannot read locked chapter source {source_path}: {exc}") from exc

    label_positions: dict[str, int] = {}
    for match in LABEL_RE.finditer(source_text):
        full_label = _full_label(chapter, match.group("label"))
        tag = tag_index.tag_by_label.get(full_label)
        if tag is None or tag_index.chapter_by_tag.get(tag) != chapter:
            continue
        if tag in label_positions:
            raise RecordError(f"{source_path}: duplicate current label {full_label}")
        label_positions[tag] = match.start()

    section_starts: list[tuple[int, int, str, str]] = []
    for expected_ordinal, raw_section in enumerate(raw_sections, start=1):
        if not isinstance(raw_section, dict):
            raise RecordError(f"chapter template {chapter!r}: invalid Section record")
        ordinal = raw_section.get("ordinal")
        source_title = raw_section.get("source_title")
        parent_tag = raw_section.get("parent_tag")
        source_label = raw_section.get("source_label")
        if (
            ordinal != expected_ordinal
            or not isinstance(source_title, str)
            or not source_title
            or not isinstance(source_label, str)
        ):
            raise RecordError(f"chapter template {chapter!r}: invalid Section identity")
        position = label_positions.get(parent_tag) if isinstance(parent_tag, str) else None
        if position is None:
            local_label = source_label.removeprefix(f"{chapter}-")
            label_match = re.search(
                rf"\\label\{{(?:{re.escape(local_label)}|{re.escape(source_label)})\}}",
                source_text,
            )
            position = label_match.start() if label_match is not None else None
        if position is None:
            raise RecordError(
                f"{source_path}: Section {ordinal} label {source_label} is missing"
            )
        section_starts.append((position, ordinal, source_title, parent_tag or "待补 Tag"))
    if section_starts != sorted(section_starts):
        raise RecordError(f"{source_path}: Section order does not match chapter template")

    ordered_tags = sorted((position, tag) for tag, position in label_positions.items())
    sections: list[tuple[int, str, str, frozenset[str]]] = []
    section_by_tag: dict[str, int] = {}
    for index, (start, ordinal, source_title, parent_tag) in enumerate(section_starts):
        scope_start = 0 if index == 0 else start
        end = section_starts[index + 1][0] if index + 1 < len(section_starts) else len(source_text)
        section_tags = {
            tag for position, tag in ordered_tags if scope_start <= position < end
        }
        required_tags = {
            tag
            for tag in section_tags
            if _requires_translation(chapter, tag_index.label_by_tag[tag])
        }
        if parent_tag == "待补 Tag":
            required_tags.add(f"missing-section-tag:{chapter}:{ordinal}")
        if parent_tag != "待补 Tag" and parent_tag not in required_tags:
            raise RecordError(
                f"{source_path}: Section {ordinal} does not define a translatable scope"
            )
        for tag in section_tags:
            section_by_tag[tag] = ordinal
        sections.append((ordinal, source_title, parent_tag, frozenset(required_tags)))
    return _ChapterSource(tuple(sections), section_by_tag)


def _unit_identity_tag(unit_id: str, parent_tag: str, tag_index: _TagIndex) -> str:
    tag_match = TAG_UNIT_RE.match(unit_id)
    if tag_match is not None and tag_match.group("tag") in tag_index.chapter_by_tag:
        return tag_match.group("tag")
    label_match = LABEL_UNIT_RE.match(unit_id)
    if label_match is not None:
        tag = tag_index.tag_by_label.get(label_match.group("label"))
        if tag is not None:
            return tag
    return parent_tag


def collect_progress(root: Path, tags_path: Path) -> ProgressSnapshot:
    source_commit = load_upstream_commit(root / "upstream.lock")
    templates = _load_chapters(root, source_commit)
    titles = _load_titles(root)
    chapter_slugs = {str(template["chapter"]) for template in templates}
    missing_titles = sorted(chapter_slugs - titles.keys())
    if missing_titles:
        raise RecordError(f"chapter title map is missing: {', '.join(missing_titles)}")
    tag_index = _load_tag_index(tags_path, chapter_slugs)
    harvest_root = tags_path.parent.parent
    chapter_sources = {
        str(template["chapter"]): _chapter_source(harvest_root, template, tag_index)
        for template in templates
    }

    unit_by_id: dict[str, tuple[str, int | None, str]] = {}
    units_by_section: dict[tuple[str, int], set[str]] = defaultdict(set)
    prepared_tags_by_section: dict[tuple[str, int], set[str]] = defaultdict(set)
    for path, line_number, unit in _read_jsonl(
        (root / "translation-data/units").glob("*.jsonl")
    ):
        if unit.get("source_commit") != source_commit or unit.get("source_status") != "CURRENT":
            continue
        unit_id = unit.get("unit_id")
        parent_tag = unit.get("parent_tag")
        chapter = unit.get("chapter")
        if not all(isinstance(value, str) and value for value in (unit_id, parent_tag, chapter)):
            raise RecordError(f"{path}:{line_number}: unit identity fields are required")
        if unit_id in unit_by_id:
            raise RecordError(f"{path}:{line_number}: duplicate current unit_id {unit_id}")
        mapped_chapter = tag_index.chapter_by_tag.get(parent_tag)
        if mapped_chapter is None:
            raise RecordError(f"{path}:{line_number}: unknown parent_tag {parent_tag}")
        if chapter != mapped_chapter:
            raise RecordError(
                f"{path}:{line_number}: chapter {chapter!r} does not match Tag {parent_tag}"
            )
        identity_tag = _unit_identity_tag(unit_id, parent_tag, tag_index)
        if tag_index.chapter_by_tag.get(identity_tag) != chapter:
            raise RecordError(
                f"{path}:{line_number}: unit identity Tag does not match chapter {chapter!r}"
            )
        section_ordinal = chapter_sources[chapter].section_by_tag.get(identity_tag)
        if section_ordinal is None:
            section_ordinal = chapter_sources[chapter].section_by_tag.get(parent_tag)
        unit_by_id[unit_id] = (chapter, section_ordinal, identity_tag)
        if section_ordinal is not None:
            key = (chapter, section_ordinal)
            units_by_section[key].add(unit_id)
            prepared_tags_by_section[key].add(identity_tag)

    candidate_units: set[str] = set()
    for path, line_number, candidate in _read_jsonl(
        (root / "translation-data/candidates").glob("*/*.jsonl")
    ):
        if (
            candidate.get("source_commit") != source_commit
            or candidate.get("source_status") != "CURRENT"
        ):
            continue
        unit_id = candidate.get("unit_id")
        if not isinstance(unit_id, str) or unit_id not in unit_by_id:
            raise RecordError(f"{path}:{line_number}: candidate references an unknown current unit")
        candidate_units.add(unit_id)

    reviewed_units: set[str] = set()
    published_units: set[str] = set()
    for path in sorted((root / "translation-data/reviewed").rglob("*.json")):
        revision = _read_json(path)
        if (
            revision.get("source_commit") != source_commit
            or revision.get("source_status") != "CURRENT"
            or revision.get("status") != "current"
        ):
            continue
        unit_id = revision.get("unit_id")
        if not isinstance(unit_id, str) or unit_id not in unit_by_id:
            raise RecordError(f"{path}: revision references an unknown current unit")
        reviewed_units.add(unit_id)
        if (
            revision.get("stage") == "PUBLISHED"
            and revision.get("publication_status") == "RELEASED"
        ):
            published_units.add(unit_id)

    chapters: list[ChapterProgress] = []
    for template in templates:
        chapter = str(template["chapter"])
        sections: list[SectionProgress] = []
        for ordinal, source_title, parent_tag, required_tags in chapter_sources[chapter].sections:
            key = (chapter, ordinal)
            unit_ids = units_by_section[key]
            prepared_tags = prepared_tags_by_section[key] & required_tags
            sections.append(
                SectionProgress(
                    ordinal=ordinal,
                    source_title=source_title,
                    parent_tag=parent_tag,
                    required_tags=len(required_tags),
                    prepared_tags=len(prepared_tags),
                    total_units=len(unit_ids),
                    candidate_units=len(unit_ids & candidate_units),
                    reviewed_units=len(unit_ids & reviewed_units),
                    published_units=len(unit_ids & published_units),
                )
            )
        chapters.append(
            ChapterProgress(
                ordinal=int(template["chapter_ordinal"]),
                slug=chapter,
                title=titles[chapter],
                source_state=str(template.get("source_state", "")),
                sections=tuple(sections),
            )
        )
    return ProgressSnapshot(
        source_commit=source_commit,
        chapters=tuple(chapters),
        current_units=len(unit_by_id),
        candidate_units=len(candidate_units),
    )


def _chapter_ranges(chapters: Iterable[ChapterProgress]) -> str:
    ordinals = sorted(chapter.ordinal for chapter in chapters)
    if not ordinals:
        return "—"
    ranges: list[str] = []
    start = previous = ordinals[0]
    for ordinal in ordinals[1:]:
        if ordinal == previous + 1:
            previous = ordinal
            continue
        ranges.append(str(start) if start == previous else f"{start}-{previous}")
        start = previous = ordinal
    ranges.append(str(start) if start == previous else f"{start}-{previous}")
    return f"第 {'、'.join(ranges)} 章"


def _status_table(chapters: Iterable[ChapterProgress]) -> list[str]:
    chapter_list = tuple(chapters)
    lines = [
        "| 当前阶段 | 章数 | 章节 |",
        "| --- | ---: | --- |",
    ]
    for status in CHAPTER_STATUS_ORDER:
        matching = tuple(chapter for chapter in chapter_list if chapter.status == status)
        lines.append(f"| {status} | {len(matching)} | {_chapter_ranges(matching)} |")
    return lines


def _pipeline_table(sections: Iterable[SectionProgress]) -> list[str]:
    section_list = tuple(sections)

    def counts(stage: str) -> tuple[int, int, int]:
        started = sum(getattr(section, f"{stage}_started") for section in section_list)
        complete = sum(getattr(section, f"{stage}_complete") for section in section_list)
        return complete, started - complete, len(section_list) - started

    candidate = counts("candidate")
    reviewed = counts("reviewed")
    published = counts("published")
    total = len(section_list)

    def coverage(complete: int) -> str:
        percentage = 100 * complete / total if total else 0
        return f"{complete:,} / {total:,}（{percentage:.1f}%）"

    return [
        "| 流程 | 完成 / 总数 | 进行中的 Section | 未开始的 Section |",
        "| --- | ---: | ---: | ---: |",
        f"| 模型候选译文 | {coverage(candidate[0])} | {candidate[1]:,} | {candidate[2]:,} |",
        f"| 人工审校 | {coverage(reviewed[0])} | {reviewed[1]:,} | {reviewed[2]:,} |",
        f"| 正式发布 | {coverage(published[0])} | {published[1]:,} | {published[2]:,} |",
    ]


def _chapter_table(chapters: Iterable[ChapterProgress]) -> list[str]:
    lines = [
        "| 章 | 标题 | 当前阶段 | 候选完成 / 总数 | 翻译中 | 未开始 | 审校完成 | 已发布 |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for chapter in chapters:
        title = chapter.title.replace("|", "\\|")
        if chapter.total_sections:
            percentage = 100 * chapter.candidate_complete_sections / chapter.total_sections
            values = (
                f"{chapter.candidate_complete_sections} / {chapter.total_sections}（{percentage:.1f}%）",
                str(chapter.candidate_active_sections),
                str(chapter.candidate_unstarted_sections),
                str(chapter.reviewed_complete_sections),
                str(chapter.published_complete_sections),
            )
        else:
            values = ("—",) * 5
        lines.append(
            f"| {chapter.ordinal} | {title}（`{chapter.slug}`） | {chapter.status} | "
            f"{values[0]} | {values[1]} | {values[2]} | {values[3]} | {values[4]} |"
        )
    return lines


def _section_detail(chapters: Iterable[ChapterProgress]) -> list[str]:
    lines: list[str] = []
    for chapter in chapters:
        if not chapter.candidate_started_sections:
            continue
        lines.extend(
            [
                f"### 第 {chapter.ordinal} 章 {chapter.title}（`{chapter.slug}`）",
                "",
                f"共 {chapter.total_sections} 个 Section：候选完成 "
                f"{chapter.candidate_complete_sections}，翻译中 "
                f"{chapter.candidate_active_sections}，未开始 "
                f"{chapter.candidate_unstarted_sections}。",
                "",
                "| Section | Tag | 英文标题 | 候选译文 | 人工审校 | 正式发布 |",
                "| ---: | --- | --- | --- | --- | --- |",
            ]
        )
        for section in chapter.sections:
            source_title = section.source_title.replace("|", "\\|")
            lines.append(
                f"| {section.ordinal} | `{section.parent_tag}` | {source_title} | "
                f"{section.candidate_stage} | {section.reviewed_stage} | "
                f"{section.published_stage} |"
            )
        lines.append("")
    return lines


def render_readme_progress(snapshot: ProgressSnapshot) -> str:
    content_chapters = snapshot.content_chapters
    non_content_chapters = tuple(
        chapter for chapter in snapshot.chapters if not chapter.total_sections
    )
    active = tuple(
        chapter for chapter in content_chapters if chapter.candidate_started_sections
    )
    sections = snapshot.sections
    candidate_complete = sum(section.candidate_complete for section in sections)
    candidate_started = sum(section.candidate_started for section in sections)
    lines = [
        f"英文来源 commit：`{snapshot.source_commit}`。",
        "",
        f"全书共 {len(snapshot.chapters)} 章，其中 {len(content_chapters)} 章、"
        f"{len(sections):,} 个 Section 有可翻译正文；",
        f"{_chapter_ranges(non_content_chapters)}为自动生成索引。当前有 "
        f"{candidate_complete:,} 个 Section 候选译文完成，"
        f"{candidate_started - candidate_complete:,} 个正在翻译，"
        f"{len(sections) - candidate_started:,} 个尚未开始。",
        "",
        "章节只归入一个当前阶段；模型候选、人工审校和正式发布严格分开：",
        "",
        *_status_table(snapshot.chapters),
        "",
        "按全书 Section 汇总：",
        "",
        *_pipeline_table(sections),
        "",
        "当前已开始翻译的章节（各数字均为 Section 数）：",
        "",
        *_chapter_table(active),
        "",
        f"[查看全部 {len(snapshot.chapters)} 章及已开始章节的逐节明细]"
        "(docs/translation-progress.md)。详细统计口径和强制更新约束见",
        "[进度报告规范](docs/progress.md)。",
    ]
    return "\n".join(lines) + "\n"


def render_chapter_report(snapshot: ProgressSnapshot) -> str:
    lines = [
        "# 全书逐章翻译进度",
        "",
        "<!-- 此文件由 `make progress` 生成，请勿手工修改表格。 -->",
        "",
        f"英文来源 commit：`{snapshot.source_commit}`。",
        "",
        f"全书共 {len(snapshot.chapters)} 章、{len(snapshot.sections):,} 个可翻译 Section。",
        "本页先列整本书和每章状态，再列所有已开始章节的逐节状态。没有出现在逐节",
        "明细中的正文章，其全部 Section 均为“未开始”。模型候选、人工审校和正式发布",
        "是三个不同阶段。",
        "",
        "## 整本书状态",
        "",
        *_status_table(snapshot.chapters),
        "",
        "## 全书 Section 状态",
        "",
        *_pipeline_table(snapshot.sections),
        "",
        "## 每章进度",
        "",
        "下表中的五个数字均为本章 Section 数，不是永久 Tag、unit、页数或字数。",
        "",
        *_chapter_table(snapshot.chapters),
        "",
        "## 已开始章节的逐节明细",
        "",
        *_section_detail(snapshot.chapters),
        "## 统计说明",
        "",
        "- Section 来自锁定英文源的 `\\section{}` 目录结构，是全书和逐章统一使用的",
        "  固定公开分母；不同 Section 长度不同，因此这里不声称是工作量百分比。",
        "- “候选完成”要求该 Section 内所有需要翻译的永久 Tag 范围都已有 current unit，",
        "  且每个 current unit 都有候选。只有部分候选时显示“翻译中”。纯公式的",
        "  `equation-*` Tag 没有自然语言，不作为翻译范围。",
        "- unit 和永久 Tag 只用于内部完整性校验，不再作为公开进度数字；准备 unit 本身",
        "  不会把 Section 标记为已经开始翻译。",
        "- “候选译文完成”不等于人工审校完成，更不等于可以发布。人工审校和发布只由",
        "  current reviewed revision 的状态决定。",
        "- 第 117 章是自动生成索引，没有独立可翻译 Section，因此显示为“不适用”。",
        "- 生成算法、状态定义和更新门禁见 [翻译进度报告规范](progress.md)。",
        "",
    ]
    return "\n".join(lines)


def _replace_readme_block(text: str, body: str) -> str:
    if text.count(README_START) != 1 or text.count(README_END) != 1:
        raise RecordError("README.md must contain exactly one translation progress marker pair")
    start_index = text.index(README_START) + len(README_START)
    end_index = text.index(README_END)
    if start_index > end_index:
        raise RecordError("README.md translation progress markers are reversed")
    return text[:start_index] + "\n" + body + text[end_index:]


def update_progress_report(
    root: Path,
    tags_path: Path,
    readme_path: Path,
    report_path: Path,
    *,
    check: bool,
) -> tuple[int, list[str]]:
    snapshot = collect_progress(root, tags_path)
    actual_readme = readme_path.read_text(encoding="utf-8")
    expected_readme = _replace_readme_block(actual_readme, render_readme_progress(snapshot))
    expected_report = render_chapter_report(snapshot)
    errors: list[str] = []
    if check:
        if actual_readme != expected_readme:
            errors.append(f"{readme_path}: translation progress block is out of date")
        try:
            actual_report = report_path.read_text(encoding="utf-8")
        except OSError:
            errors.append(f"{report_path}: chapter progress report is missing")
        else:
            if actual_report != expected_report:
                errors.append(f"{report_path}: chapter progress report is out of date")
        return len(snapshot.chapters), errors

    readme_path.write_text(expected_readme, encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(expected_report, encoding="utf-8")
    return len(snapshot.chapters), errors
