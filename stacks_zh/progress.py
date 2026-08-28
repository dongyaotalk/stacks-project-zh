from __future__ import annotations

import json
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


@dataclass(frozen=True)
class ChapterProgress:
    ordinal: int
    slug: str
    title: str
    source_state: str
    total_tags: int
    prepared_tags: int
    candidate_tags: int
    reviewed_tags: int
    published_tags: int

    @property
    def status(self) -> str:
        if self.total_tags == 0:
            return "不适用"
        if self.published_tags == self.total_tags:
            return "已发布"
        if self.published_tags:
            return "发布中"
        if self.reviewed_tags == self.total_tags:
            return "人工审校完成，待发布"
        if self.reviewed_tags:
            return "人工审校中"
        if self.candidate_tags == self.total_tags:
            return "候选译文完成，待审校"
        if self.candidate_tags:
            return "翻译中"
        return "未开始"


@dataclass(frozen=True)
class ProgressSnapshot:
    source_commit: str
    chapters: tuple[ChapterProgress, ...]
    ignored_navigation_tags: int
    current_units: int
    candidate_units: int

    @property
    def content_chapters(self) -> tuple[ChapterProgress, ...]:
        return tuple(chapter for chapter in self.chapters if chapter.total_tags)

    @property
    def total_tags(self) -> int:
        return sum(chapter.total_tags for chapter in self.chapters)

    @property
    def prepared_tags(self) -> int:
        return sum(chapter.prepared_tags for chapter in self.chapters)

    @property
    def candidate_tags(self) -> int:
        return sum(chapter.candidate_tags for chapter in self.chapters)

    @property
    def reviewed_tags(self) -> int:
        return sum(chapter.reviewed_tags for chapter in self.chapters)

    @property
    def published_tags(self) -> int:
        return sum(chapter.published_tags for chapter in self.chapters)


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


def _load_chapter_tags(
    tags_path: Path, chapter_slugs: set[str]
) -> tuple[dict[str, set[str]], dict[str, str], int]:
    try:
        lines = tags_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RecordError(f"cannot read permanent Tag map {tags_path}: {exc}") from exc
    sorted_slugs = sorted(chapter_slugs, key=len, reverse=True)
    by_chapter: dict[str, set[str]] = defaultdict(set)
    chapter_by_tag: dict[str, str] = {}
    ignored_navigation_tags = 0
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "," not in line:
            raise RecordError(f"{tags_path}:{line_number}: expected TAG,label")
        tag, label = line.split(",", 1)
        if tag in chapter_by_tag:
            raise RecordError(f"{tags_path}:{line_number}: duplicate permanent Tag {tag}")
        chapter = next(
            (slug for slug in sorted_slugs if label.startswith(f"{slug}-")), None
        )
        if chapter is None:
            if label.startswith("book-part-"):
                ignored_navigation_tags += 1
                continue
            raise RecordError(
                f"{tags_path}:{line_number}: Tag {tag} is not assigned to a chapter"
            )
        by_chapter[chapter].add(tag)
        chapter_by_tag[tag] = chapter
    if not chapter_by_tag:
        raise RecordError(f"{tags_path}: no chapter permanent Tags")
    return by_chapter, chapter_by_tag, ignored_navigation_tags


def collect_progress(root: Path, tags_path: Path) -> ProgressSnapshot:
    source_commit = load_upstream_commit(root / "upstream.lock")
    templates = _load_chapters(root, source_commit)
    titles = _load_titles(root)
    chapter_slugs = {str(template["chapter"]) for template in templates}
    missing_titles = sorted(chapter_slugs - titles.keys())
    if missing_titles:
        raise RecordError(f"chapter title map is missing: {', '.join(missing_titles)}")
    tags_by_chapter, chapter_by_tag, ignored_tags = _load_chapter_tags(
        tags_path, chapter_slugs
    )

    units_by_tag: dict[str, set[str]] = defaultdict(set)
    unit_by_id: dict[str, tuple[str, str]] = {}
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
        mapped_chapter = chapter_by_tag.get(parent_tag)
        if mapped_chapter is None:
            raise RecordError(f"{path}:{line_number}: unknown parent_tag {parent_tag}")
        if chapter != mapped_chapter:
            raise RecordError(
                f"{path}:{line_number}: chapter {chapter!r} does not match Tag {parent_tag}"
            )
        unit_by_id[unit_id] = (parent_tag, chapter)
        units_by_tag[parent_tag].add(unit_id)

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

    prepared_tags = set(units_by_tag)
    candidate_tags = {
        tag for tag, unit_ids in units_by_tag.items() if unit_ids <= candidate_units
    }
    reviewed_tags = {
        tag for tag, unit_ids in units_by_tag.items() if unit_ids <= reviewed_units
    }
    published_tags = {
        tag for tag, unit_ids in units_by_tag.items() if unit_ids <= published_units
    }

    chapters = tuple(
        ChapterProgress(
            ordinal=int(template["chapter_ordinal"]),
            slug=str(template["chapter"]),
            title=titles[str(template["chapter"])],
            source_state=str(template.get("source_state", "")),
            total_tags=len(tags_by_chapter[str(template["chapter"])]),
            prepared_tags=len(tags_by_chapter[str(template["chapter"])] & prepared_tags),
            candidate_tags=len(tags_by_chapter[str(template["chapter"])] & candidate_tags),
            reviewed_tags=len(tags_by_chapter[str(template["chapter"])] & reviewed_tags),
            published_tags=len(tags_by_chapter[str(template["chapter"])] & published_tags),
        )
        for template in templates
    )
    return ProgressSnapshot(
        source_commit=source_commit,
        chapters=chapters,
        ignored_navigation_tags=ignored_tags,
        current_units=len(unit_by_id),
        candidate_units=len(candidate_units),
    )


def _scope_coverage(count: int, total: int) -> str:
    if total == 0:
        return "—"
    return f"{count:,} / {total:,}"


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


def _chapter_table(chapters: Iterable[ChapterProgress]) -> list[str]:
    lines = [
        "| 章 | 标题 | 当前阶段 | 候选译文范围 | 人工审校范围 |",
        "| ---: | --- | --- | ---: | ---: |",
    ]
    for chapter in chapters:
        title = chapter.title.replace("|", "\\|")
        lines.append(
            f"| {chapter.ordinal} | {title}（`{chapter.slug}`） | {chapter.status} | "
            f"{_scope_coverage(chapter.candidate_tags, chapter.total_tags)} | "
            f"{_scope_coverage(chapter.reviewed_tags, chapter.total_tags)} |"
        )
    return lines


def render_readme_progress(snapshot: ProgressSnapshot) -> str:
    content_chapters = snapshot.content_chapters
    non_content_chapters = tuple(
        chapter for chapter in snapshot.chapters if not chapter.total_tags
    )
    active = tuple(
        chapter
        for chapter in content_chapters
        if chapter.candidate_tags or chapter.reviewed_tags or chapter.published_tags
    )
    started = sum(chapter.candidate_tags > 0 for chapter in content_chapters)
    candidate_complete = sum(
        chapter.candidate_tags == chapter.total_tags for chapter in content_chapters
    )
    not_started = sum(chapter.status == "未开始" for chapter in content_chapters)
    lines = [
        f"英文来源 commit：`{snapshot.source_commit}`。",
        "",
        f"全书共 {len(snapshot.chapters)} 章，其中 {len(content_chapters)} 章有可翻译正文，",
        f"{_chapter_ranges(non_content_chapters)}为自动生成索引。目前 "
        f"{started} 章已有候选译文：{candidate_complete} 章候选译文覆盖全章，"
        f"{started - candidate_complete} 章仍在推进；{not_started} 章尚未开始。",
        "",
        "章节只归入一个当前阶段；模型候选、人工审校和正式发布严格分开：",
        "",
        *_status_table(snapshot.chapters),
        "",
        "当前已有译文的章节：",
        "",
        *_chapter_table(active),
        "",
        "[查看全部 117 章的逐章清单](docs/translation-progress.md)，可直接确认每章是已完成",
        "候选译文、正在翻译、进入人工审校，还是尚未开始。详细口径及更新约束见",
        "[进度快照规范](docs/progress.md)。",
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
        f"全书共 {len(snapshot.chapters)} 章，其中 {len(snapshot.content_chapters)} 章有可翻译正文。",
        "下表先按章节给出整本书状态，再逐章列出翻译进度；单纯准备 unit 不算已经",
        "开始翻译。模型候选、人工审校和正式发布是三个不同阶段。",
        "",
        "## 整本书状态",
        "",
        *_status_table(snapshot.chapters),
        "",
        "## 每章进度",
        "",
        *_chapter_table(snapshot.chapters),
        "",
        "## 统计说明",
        "",
        "- “候选译文范围”和“人工审校范围”的 `x / y` 以本章永久 Tag 为结构范围；它只",
        "  用来说明本章覆盖到哪里，不代表页数、字数或工作量百分比。",
        f"- 锁定英文源共有 {snapshot.total_tags:,} 个章节永久 Tag；另有 "
        f"{snapshot.ignored_navigation_tags} 个 `book-part-*` 导航 Tag 不属于任何章。",
        "- 全书概览按章节阶段统计，不把不同章节的 Tag 累加成一个看似精确的全书完成率。",
        "- 已准备 unit 数和候选 unit 数不作为公开翻译进度；准备数据本身不等于已有译文。",
        "- 第 117 章是自动生成索引，没有独立可翻译正文，因此显示为“不适用”。",
        "- 生成算法、状态定义和更新门禁见 [翻译进度快照规范](progress.md)。",
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
