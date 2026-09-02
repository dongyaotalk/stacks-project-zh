from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .records import RecordError, load_upstream_commit
from .schema_validation import validate_named_schema


README_START = "<!-- translation-plan:start -->"
README_END = "<!-- translation-plan:end -->"
ACTION_ORDER = (
    "RESOLVE_TAG",
    "PREPARE_SCOPE",
    "TRANSLATE",
    "CONTINUE_TRANSLATION",
    "REVIEW",
    "CONTINUE_REVIEW",
    "MATHEMATICS_REVIEW",
    "PUBLISH_PREPARATION",
    "DONE",
    "NOT_APPLICABLE",
)
ACTION_LABELS = {
    "RESOLVE_TAG": "补齐稳定 Tag/ID",
    "PREPARE_SCOPE": "准备稳定 unit",
    "TRANSLATE": "生成候选译文",
    "CONTINUE_TRANSLATION": "继续候选翻译",
    "REVIEW": "开始人工审校",
    "CONTINUE_REVIEW": "继续人工审校",
    "MATHEMATICS_REVIEW": "完成人工数学审校",
    "PUBLISH_PREPARATION": "准备发布",
    "DONE": "已完成",
    "NOT_APPLICABLE": "不适用",
}
TRANSLATION_ACTIONS = frozenset(
    {
        "RESOLVE_TAG",
        "PREPARE_SCOPE",
        "TRANSLATE",
        "CONTINUE_TRANSLATION",
    }
)
SELECTION_ORDER = [
    "explicit_user_scope",
    "priority_rank",
    "wave",
    "chapter_order",
    "section_order",
    "workflow_action",
]


@dataclass(frozen=True)
class PriorityLevel:
    name: str
    rank: int
    label: str
    description: str


@dataclass(frozen=True)
class ChapterPriority:
    priority: str
    wave: int
    order: int
    tracks: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class TranslationTask:
    chapter: str
    chapter_ordinal: int
    chapter_title: str
    source_chapter_title: str
    priority: str
    priority_rank: int
    priority_label: str
    wave: int
    chapter_order: int
    section_ordinal: int
    section_title: str
    parent_tag: str | None
    state: str
    action: str
    suggested_batch: str | None
    suggested_unit_file: str | None
    total_units: int
    candidate_units: int
    reviewed_units: int
    published_units: int

    @property
    def actionable(self) -> bool:
        return self.action not in {"DONE", "NOT_APPLICABLE"}

    @property
    def sort_key(self) -> tuple[int, int, int, int, int]:
        return (
            self.priority_rank,
            self.wave,
            self.chapter_order,
            self.chapter_ordinal,
            self.section_ordinal,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter,
            "chapter_ordinal": self.chapter_ordinal,
            "chapter_title": self.chapter_title,
            "source_chapter_title": self.source_chapter_title,
            "priority": self.priority,
            "priority_label": self.priority_label,
            "wave": self.wave,
            "chapter_order": self.chapter_order,
            "section_ordinal": self.section_ordinal,
            "section_title": self.section_title,
            "parent_tag": self.parent_tag,
            "state": self.state,
            "action": self.action,
            "suggested_batch": self.suggested_batch,
            "suggested_unit_file": self.suggested_unit_file,
            "progress": {
                "total_units": self.total_units,
                "candidate_units": self.candidate_units,
                "reviewed_units": self.reviewed_units,
                "published_units": self.published_units,
            },
        }


@dataclass(frozen=True)
class ChapterPlan:
    ordinal: int
    slug: str
    title: str
    source_title: str
    source_state: str
    policy: ChapterPriority
    tasks: tuple[TranslationTask, ...]

    @property
    def next_task(self) -> TranslationTask | None:
        return next((task for task in self.tasks if task.actionable), None)


@dataclass(frozen=True)
class TranslationPlan:
    source_commit: str
    method_revision: str
    levels: dict[str, PriorityLevel]
    chapters: tuple[ChapterPlan, ...]

    @property
    def tasks(self) -> tuple[TranslationTask, ...]:
        return tuple(
            sorted(
                (task for chapter in self.chapters for task in chapter.tasks),
                key=lambda task: task.sort_key,
            )
        )

    @property
    def actionable_tasks(self) -> tuple[TranslationTask, ...]:
        return tuple(task for task in self.tasks if task.actionable)


@dataclass(frozen=True)
class TaskSelection:
    mode: str
    task: TranslationTask | None
    requested_chapter: str | None = None
    requested_tag: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "selection": {
                "mode": self.mode,
                "requested_chapter": self.requested_chapter,
                "requested_tag": self.requested_tag,
            },
            "task": self.task.as_dict() if self.task is not None else None,
        }


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


def _load_templates(root: Path, source_commit: str) -> list[dict[str, Any]]:
    templates = [
        _read_json(path)
        for path in sorted((root / "translation-data/chapter-templates").glob("*.json"))
    ]
    if not templates:
        raise RecordError("translation-data/chapter-templates: no chapter templates")
    templates.sort(key=lambda item: item.get("chapter_ordinal", 0))
    ordinals = [item.get("chapter_ordinal") for item in templates]
    if ordinals != list(range(1, len(templates) + 1)):
        raise RecordError("chapter templates do not have contiguous unique ordinals")
    slugs = [item.get("chapter") for item in templates]
    if not all(isinstance(slug, str) and slug for slug in slugs):
        raise RecordError("chapter templates require non-empty chapter slugs")
    if len(slugs) != len(set(slugs)):
        raise RecordError("chapter templates do not have unique chapter slugs")
    for template in templates:
        if template.get("source_commit") != source_commit:
            raise RecordError(
                f"chapter template {template.get('chapter')!r} does not match upstream.lock"
            )
    return templates


def _load_titles(root: Path) -> dict[str, str]:
    titles = _read_json(root / "config/chapter-titles.json").get("titles")
    if not isinstance(titles, dict) or not all(
        isinstance(slug, str) and isinstance(title, str) and title
        for slug, title in titles.items()
    ):
        raise RecordError("config/chapter-titles.json: invalid titles map")
    return titles


def _load_priority_config(
    path: Path,
    chapter_slugs: set[str],
) -> tuple[str, dict[str, PriorityLevel], dict[str, ChapterPriority]]:
    value = _read_json(path)
    schema_errors = validate_named_schema(
        value, "translation-priorities.schema.json", str(path)
    )
    if schema_errors:
        raise RecordError("\n".join(schema_errors))
    if value["selection_order"] != SELECTION_ORDER:
        raise RecordError(
            f"{path}: selection_order must be {SELECTION_ORDER!r}"
        )
    levels_value = value["levels"]
    chapters_value = value["chapters"]
    levels = {
        name: PriorityLevel(
            name=name,
            rank=int(record["rank"]),
            label=str(record["label"]),
            description=str(record["description"]),
        )
        for name, record in levels_value.items()
    }
    ranks = sorted(level.rank for level in levels.values())
    if ranks != list(range(len(levels))):
        raise RecordError(f"{path}: priority ranks must be contiguous from zero")
    configured_slugs = set(chapters_value)
    missing = sorted(chapter_slugs - configured_slugs)
    extra = sorted(configured_slugs - chapter_slugs)
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing chapters: {', '.join(missing)}")
        if extra:
            details.append(f"unknown chapters: {', '.join(extra)}")
        raise RecordError(f"{path}: " + "; ".join(details))
    policies = {
        slug: ChapterPriority(
            priority=str(record["priority"]),
            wave=int(record["wave"]),
            order=int(record["order"]),
            tracks=tuple(str(track) for track in record["tracks"]),
            reason=str(record["reason"]),
        )
        for slug, record in chapters_value.items()
    }
    duplicate_positions: dict[tuple[str, int, int], list[str]] = defaultdict(list)
    for slug, policy in policies.items():
        if policy.wave < 1 or policy.order < 1:
            raise RecordError(f"{path}: {slug}: wave and order must be positive")
        if not policy.tracks:
            raise RecordError(f"{path}: {slug}: tracks must not be empty")
        duplicate_positions[(policy.priority, policy.wave, policy.order)].append(slug)
    collisions = [
        f"{priority}/wave {wave}/order {order}: {', '.join(slugs)}"
        for (priority, wave, order), slugs in duplicate_positions.items()
        if len(slugs) > 1
    ]
    if collisions:
        raise RecordError(f"{path}: duplicate chapter positions: {'; '.join(collisions)}")
    return str(value["method_revision"]), levels, policies


def _collect_repository_state(
    root: Path,
    source_commit: str,
) -> tuple[
    dict[str, set[str]],
    dict[str, str],
    set[str],
    dict[str, tuple[str, str, frozenset[str]]],
]:
    units_by_file: dict[str, set[str]] = defaultdict(set)
    risk_by_unit: dict[str, str] = {}
    unit_location: dict[str, str] = {}
    units_root = root / "translation-data/units"
    for path, line_number, unit in _read_jsonl(units_root.glob("*.jsonl")):
        if unit.get("source_commit") != source_commit or unit.get("source_status") != "CURRENT":
            continue
        unit_id = unit.get("unit_id")
        risk_level = unit.get("risk_level")
        if not isinstance(unit_id, str) or not unit_id:
            raise RecordError(f"{path}:{line_number}: current unit_id is required")
        if unit_id in risk_by_unit:
            raise RecordError(
                f"{path}:{line_number}: duplicate current unit_id {unit_id}; first at {unit_location[unit_id]}"
            )
        if risk_level not in {"R0", "R1", "R2", "R3"}:
            raise RecordError(f"{path}:{line_number}: invalid risk_level for {unit_id}")
        relative = path.relative_to(root).as_posix()
        units_by_file[relative].add(unit_id)
        risk_by_unit[unit_id] = str(risk_level)
        unit_location[unit_id] = f"{path}:{line_number}"

    candidate_units: set[str] = set()
    for path, line_number, candidate in _read_jsonl(
        (root / "translation-data/candidates").glob("*/*.jsonl")
    ):
        if (
            candidate.get("source_commit") == source_commit
            and candidate.get("source_status") == "CURRENT"
        ):
            unit_id = candidate.get("unit_id")
            if not isinstance(unit_id, str) or unit_id not in risk_by_unit:
                raise RecordError(
                    f"{path}:{line_number}: candidate references an unknown current unit"
                )
            candidate_units.add(unit_id)

    selection_reviews: dict[str, frozenset[str]] = {}
    for path in sorted((root / "translation-data/selections").glob("*.json")):
        selection = _read_json(path)
        selection_id = selection.get("selection_id")
        if not isinstance(selection_id, str) or not selection_id:
            raise RecordError(f"{path}: selection_id is required")
        if selection_id in selection_reviews:
            raise RecordError(f"{path}: duplicate selection_id {selection_id!r}")
        review_required = selection.get("review_required", [])
        if not isinstance(review_required, list) or not all(
            review in {"language", "mathematics"} for review in review_required
        ):
            raise RecordError(f"{path}: invalid review_required")
        selection_reviews[selection_id] = frozenset(
            str(review) for review in review_required
        )

    revisions: dict[str, tuple[str, str, frozenset[str]]] = {}
    for path in sorted((root / "translation-data/reviewed").rglob("*.json")):
        revision = _read_json(path)
        if (
            revision.get("source_commit") != source_commit
            or revision.get("source_status") != "CURRENT"
            or revision.get("status") != "current"
        ):
            continue
        unit_id = revision.get("unit_id")
        stage = revision.get("stage")
        publication_status = revision.get("publication_status")
        if not isinstance(unit_id, str) or unit_id not in risk_by_unit:
            raise RecordError(f"{path}: revision references an unknown current unit")
        if unit_id in revisions:
            raise RecordError(f"{path}: multiple current revisions for {unit_id}")
        if stage not in {"LANGUAGE_REVIEWED", "MATH_REVIEWED", "PUBLISHED"}:
            raise RecordError(f"{path}: invalid current revision stage")
        required_reviews = set(
            selection_reviews.get(str(revision.get("selection_id", "")), frozenset())
        )
        risk_level = risk_by_unit[unit_id]
        if risk_level in {"R1", "R2", "R3"}:
            required_reviews.add("language")
        if risk_level == "R3":
            required_reviews.add("mathematics")
        revisions[unit_id] = (
            str(stage),
            str(publication_status),
            frozenset(required_reviews),
        )
    return units_by_file, risk_by_unit, candidate_units, revisions


def _resolve_action(
    state: str,
    unit_ids: set[str],
    risk_by_unit: dict[str, str],
    candidate_units: set[str],
    revisions: dict[str, tuple[str, str, frozenset[str]]],
) -> tuple[str, int, int, int, int]:
    total = len(unit_ids)
    candidate_count = len(unit_ids & candidate_units)
    reviewed_ids = unit_ids & revisions.keys()
    reviewed_count = len(reviewed_ids)
    published_count = sum(
        revisions[unit_id][0:2] == ("PUBLISHED", "RELEASED")
        for unit_id in reviewed_ids
    )
    if state == "BLOCKED_NO_TAG":
        return "RESOLVE_TAG", total, candidate_count, reviewed_count, published_count
    if state == "UNPREPARED" or not unit_ids:
        return "PREPARE_SCOPE", total, candidate_count, reviewed_count, published_count
    if state != "READY":
        raise RecordError(f"unknown chapter-template Section state {state!r}")
    if candidate_count == 0:
        action = "TRANSLATE"
    elif candidate_count < total:
        action = "CONTINUE_TRANSLATION"
    elif reviewed_count == 0:
        action = "REVIEW"
    elif reviewed_count < total:
        action = "CONTINUE_REVIEW"
    elif published_count == total:
        action = "DONE"
    elif any(
        "mathematics" in revisions[unit_id][2]
        and revisions[unit_id][0] == "LANGUAGE_REVIEWED"
        for unit_id in unit_ids
    ):
        action = "MATHEMATICS_REVIEW"
    else:
        action = "PUBLISH_PREPARATION"
    return action, total, candidate_count, reviewed_count, published_count


def build_translation_plan(
    root: Path,
    priority_path: Path | None = None,
) -> TranslationPlan:
    root = root.resolve()
    source_commit = load_upstream_commit(root / "upstream.lock")
    templates = _load_templates(root, source_commit)
    titles = _load_titles(root)
    slugs = {str(template["chapter"]) for template in templates}
    missing_titles = sorted(slugs - titles.keys())
    if missing_titles:
        raise RecordError(f"chapter title map is missing: {', '.join(missing_titles)}")
    config_path = priority_path or Path("config/translation-priorities.json")
    if not config_path.is_absolute():
        config_path = root / config_path
    method_revision, levels, policies = _load_priority_config(config_path, slugs)
    units_by_file, risk_by_unit, candidate_units, revisions = _collect_repository_state(
        root, source_commit
    )

    chapter_plans: list[ChapterPlan] = []
    for template in templates:
        slug = str(template["chapter"])
        ordinal = int(template["chapter_ordinal"])
        policy = policies[slug]
        level = levels[policy.priority]
        raw_sections = template.get("sections")
        if not isinstance(raw_sections, list):
            raise RecordError(f"chapter template {slug!r}: sections must be an array")
        tasks: list[TranslationTask] = []
        for expected_ordinal, section in enumerate(raw_sections, start=1):
            if not isinstance(section, dict) or section.get("ordinal") != expected_ordinal:
                raise RecordError(f"chapter template {slug!r}: invalid Section order")
            unit_files = section.get("unit_files")
            if not isinstance(unit_files, list) or not all(
                isinstance(path, str) for path in unit_files
            ):
                raise RecordError(f"chapter template {slug!r}: invalid unit_files")
            unit_ids: set[str] = set()
            for unit_file in unit_files:
                unit_ids.update(units_by_file.get(unit_file, set()))
            action, total, candidates, reviewed, published = _resolve_action(
                str(section.get("state")),
                unit_ids,
                risk_by_unit,
                candidate_units,
                revisions,
            )
            tasks.append(
                TranslationTask(
                    chapter=slug,
                    chapter_ordinal=ordinal,
                    chapter_title=titles[slug],
                    source_chapter_title=str(template.get("source_title", slug)),
                    priority=policy.priority,
                    priority_rank=level.rank,
                    priority_label=level.label,
                    wave=policy.wave,
                    chapter_order=policy.order,
                    section_ordinal=expected_ordinal,
                    section_title=str(section.get("source_title", "")),
                    parent_tag=(
                        str(section["parent_tag"])
                        if isinstance(section.get("parent_tag"), str)
                        else None
                    ),
                    state=str(section.get("state")),
                    action=action,
                    suggested_batch=(
                        str(section["suggested_batch"])
                        if isinstance(section.get("suggested_batch"), str)
                        else None
                    ),
                    suggested_unit_file=(
                        str(section["suggested_unit_file"])
                        if isinstance(section.get("suggested_unit_file"), str)
                        else None
                    ),
                    total_units=total,
                    candidate_units=candidates,
                    reviewed_units=reviewed,
                    published_units=published,
                )
            )
        chapter_plans.append(
            ChapterPlan(
                ordinal=ordinal,
                slug=slug,
                title=titles[slug],
                source_title=str(template.get("source_title", slug)),
                source_state=str(template.get("source_state", "")),
                policy=policy,
                tasks=tuple(tasks),
            )
        )
    return TranslationPlan(
        source_commit=source_commit,
        method_revision=method_revision,
        levels=levels,
        chapters=tuple(chapter_plans),
    )


def _resolve_chapter(plan: TranslationPlan, value: str) -> ChapterPlan:
    normalized = value.strip()
    if not normalized:
        raise RecordError("chapter selection must not be empty")
    matches = [
        chapter
        for chapter in plan.chapters
        if chapter.slug == normalized
        or (normalized.isdigit() and chapter.ordinal == int(normalized))
    ]
    if not matches:
        raise RecordError(f"unknown chapter selection {value!r}")
    return matches[0]


def select_next_task(
    plan: TranslationPlan,
    chapter: str | None = None,
    tag: str | None = None,
    fallback: bool = False,
) -> TaskSelection:
    if tag is not None and chapter is None:
        raise RecordError("--tag requires --chapter")
    if chapter is None:
        task = next(iter(plan.actionable_tasks), None)
        return TaskSelection(mode="automatic", task=task)

    selected_chapter = _resolve_chapter(plan, chapter)
    tasks = selected_chapter.tasks
    normalized_tag = tag.strip().upper() if tag is not None else None
    if normalized_tag:
        tasks = tuple(task for task in tasks if task.parent_tag == normalized_tag)
        if not tasks:
            raise RecordError(
                f"chapter {selected_chapter.slug!r} has no Section with parent Tag {normalized_tag}"
            )
    task = next((item for item in tasks if item.actionable), None)
    if task is not None or not fallback:
        return TaskSelection(
            mode="explicit",
            task=task,
            requested_chapter=selected_chapter.slug,
            requested_tag=normalized_tag,
        )
    automatic = next(iter(plan.actionable_tasks), None)
    return TaskSelection(
        mode="fallback",
        task=automatic,
        requested_chapter=selected_chapter.slug,
        requested_tag=normalized_tag,
    )


def render_task_selection(selection: TaskSelection) -> str:
    if selection.task is None:
        if selection.mode == "explicit":
            scope = f"Chapter {selection.requested_chapter}"
            if selection.requested_tag:
                scope += f" / Tag {selection.requested_tag}"
            return f"{scope} has no remaining actionable work."
        return "The translation plan has no remaining actionable work."
    task = selection.task
    lines = [
        "Next translation task",
        "",
        f"Selection: {selection.mode}",
        f"Chapter: {task.chapter_ordinal} {task.chapter_title} ({task.chapter})",
        f"Priority: {task.priority} — {task.priority_label}",
        f"Wave / order: {task.wave} / {task.chapter_order}",
        f"Section: {task.section_ordinal} — {task.section_title}",
        f"Tag: {task.parent_tag or '待补 Tag'}",
        f"State: {task.state}",
        f"Action: {task.action}",
    ]
    if task.suggested_batch:
        lines.append(f"Suggested batch: {task.suggested_batch}")
    if task.suggested_unit_file:
        lines.append(f"Suggested unit file: {task.suggested_unit_file}")
    return "\n".join(lines)


def render_task_selection_json(selection: TaskSelection) -> str:
    return json.dumps(selection.as_dict(), ensure_ascii=False, indent=2) + "\n"


def _markdown(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _task_scope(task: TranslationTask | None) -> str:
    if task is None:
        return "—"
    tag = task.parent_tag or "待补 Tag"
    return f"Section {task.section_ordinal} / `{tag}`"


def _priority_distribution(plan: TranslationPlan) -> list[str]:
    counts = Counter(chapter.policy.priority for chapter in plan.chapters)
    lines = [
        "| 优先级 | 定义 | 章数 |",
        "| --- | --- | ---: |",
    ]
    for level in sorted(plan.levels.values(), key=lambda item: item.rank):
        lines.append(
            f"| {level.name}（{_markdown(level.label)}） | "
            f"{_markdown(level.description)} | {counts[level.name]} |"
        )
    return lines


def _recommended_table(tasks: Iterable[TranslationTask]) -> list[str]:
    lines = [
        "| 优先级 | 章 | 当前范围 | 准备状态 | 下一动作 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for task in tasks:
        lines.append(
            f"| {task.priority} | 第 {task.chapter_ordinal} 章 "
            f"{_markdown(task.chapter_title)}（`{task.chapter}`） | "
            f"{_task_scope(task)} | `{task.state}` | `{task.action}` |"
        )
    return lines


def _recommended_chapter_tasks(
    plan: TranslationPlan,
    limit: int,
    actions: frozenset[str] | None = None,
) -> tuple[TranslationTask, ...]:
    tasks = [
        (
            next((task for task in chapter.tasks if task.action in actions), None)
            if actions is not None
            else chapter.next_task
        )
        for chapter in plan.chapters
    ]
    return tuple(
        sorted(
            (
                task
                for task in tasks
                if task is not None
                and (actions is None or task.action in actions)
            ),
            key=lambda task: task.sort_key,
        )[:limit]
    )


def render_readme_plan(plan: TranslationPlan) -> str:
    tasks = _recommended_chapter_tasks(plan, 10, TRANSLATION_ACTIONS)
    lines = [
        f"优先级方法：`{plan.method_revision}`。用户显式指定的 Chapter/Tag 始终高于",
        "项目默认优先级；未指定时才按 P0 → P4、wave、章内 Section 顺序选择。",
        "",
        *_recommended_table(tasks),
        "",
        "运行 `make next-task` 获取当前自动任务；也可用",
        "`make next-task CHAPTER=4` 或 `make next-task CHAPTER=categories TAG=001L`",
        "锁定本次范围。完整政策和 117 章队列见",
        "[翻译优先级](docs/translation-priority.md)与",
        "[当前翻译计划](docs/translation-plan.md)。",
    ]
    return "\n".join(lines)


def render_translation_plan(plan: TranslationPlan) -> str:
    next_by_chapter = {chapter.slug: chapter.next_task for chapter in plan.chapters}
    chapters = sorted(
        plan.chapters,
        key=lambda chapter: (
            plan.levels[chapter.policy.priority].rank,
            chapter.policy.wave,
            chapter.policy.order,
            chapter.ordinal,
        ),
    )
    lines = [
        "# 当前翻译计划",
        "",
        "> 本文件由 `make plan` 确定性生成。不要手工修改。",
        "",
        f"英文来源 commit：`{plan.source_commit}`。",
        f"优先级方法：`{plan.method_revision}`。",
        "",
        "选择规则是：显式用户范围 > P0–P4 > wave > 章内 Section 顺序。",
        "Section 的当前状态决定动作，但不会为了选择一个更容易执行的低优先级任务而",
        "跳过更高价值章节所需的 scope preparation。",
        "",
        "## 优先级分布",
        "",
        *_priority_distribution(plan),
        "",
        "## 当前推荐任务",
        "",
        *_recommended_table(_recommended_chapter_tasks(plan, 20)),
        "",
        f"## 全部 {len(plan.chapters)} 章",
        "",
        "| 优先级 | wave / order | 章 | 轨道 | 当前下一范围 | 下一动作 | 原因 |",
        "| --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for chapter in chapters:
        task = next_by_chapter[chapter.slug]
        tracks = ", ".join(f"`{track}`" for track in chapter.policy.tracks)
        if task is not None:
            action = task.action
        elif chapter.tasks:
            action = "DONE"
        else:
            action = "NOT_APPLICABLE"
        lines.append(
            f"| {chapter.policy.priority} | {chapter.policy.wave} / "
            f"{chapter.policy.order} | 第 {chapter.ordinal} 章 "
            f"{_markdown(chapter.title)}（`{chapter.slug}`） | {tracks} | "
            f"{_task_scope(task)} | `{action}` | {_markdown(chapter.policy.reason)} |"
        )
    lines.extend(
        [
            "",
            "## 动作状态机",
            "",
            "| 动作 | 含义 |",
            "| --- | --- |",
        ]
    )
    for action in ACTION_ORDER:
        lines.append(f"| `{action}` | {ACTION_LABELS[action]} |")
    lines.extend(
        [
            "",
            "显式指定的范围如果已经完成，默认返回“没有剩余可执行工作”，不会悄悄切换",
            "到其他章节；只有显式传入 `--fallback`（Make 接口为 `FALLBACK=1`）才恢复",
            "自动选择。机器调用可使用 `next-task --json`（Make 接口为 `JSON=1`）。",
            "",
        ]
    )
    return "\n".join(lines)


def _replace_readme_block(text: str, body: str) -> str:
    if text.count(README_START) != 1 or text.count(README_END) != 1:
        raise RecordError("README translation-plan markers must each appear exactly once")
    start = text.index(README_START) + len(README_START)
    end = text.index(README_END)
    if start > end:
        raise RecordError("README translation-plan markers are out of order")
    return text[:start] + "\n" + body.rstrip() + "\n" + text[end:]


def update_translation_plan(
    root: Path,
    readme_path: Path,
    output_path: Path,
    priority_path: Path | None = None,
    check: bool = False,
) -> tuple[int, list[str]]:
    plan = build_translation_plan(root, priority_path)
    try:
        readme_text = readme_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordError(f"cannot read README {readme_path}: {exc}") from exc
    expected_readme = _replace_readme_block(readme_text, render_readme_plan(plan))
    expected_report = render_translation_plan(plan)
    errors: list[str] = []
    if check:
        if readme_text != expected_readme:
            errors.append(f"{readme_path}: translation plan is out of date; run make plan")
        try:
            actual_report = output_path.read_text(encoding="utf-8")
        except OSError:
            actual_report = ""
        if actual_report != expected_report:
            errors.append(f"{output_path}: out of date; run make plan")
    else:
        readme_path.write_text(expected_readme, encoding="utf-8")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(expected_report, encoding="utf-8")
    return len(plan.chapters), errors
