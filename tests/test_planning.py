from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.planning import (
    build_translation_plan,
    render_task_selection_json,
    select_next_task,
    update_translation_plan,
)
from stacks_zh.records import RecordError


SOURCE_COMMIT = "a" * 40


def write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(value) + "\n" for value in values), encoding="utf-8"
    )


def priority_config(chapters: dict[str, dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "method_revision": "test-v1",
        "selection_order": [
            "explicit_user_scope",
            "priority_rank",
            "wave",
            "chapter_order",
            "section_order",
            "workflow_action",
        ],
        "levels": {
            name: {
                "rank": rank,
                "label": f"Level {name}",
                "description": f"Description {name}",
            }
            for rank, name in enumerate(("P0", "P1", "P2", "P3", "P4"))
        },
        "chapters": chapters,
    }


def chapter_policy(priority: str, order: int) -> dict[str, object]:
    return {
        "priority": priority,
        "wave": 1,
        "order": order,
        "tracks": ["test"],
        "reason": "test policy",
    }


def section(
    ordinal: int,
    tag: str | None,
    state: str,
    unit_files: list[str] | None = None,
) -> dict[str, object]:
    batch = f"test-{tag}" if tag is not None else None
    return {
        "ordinal": ordinal,
        "source_title": f"Section {ordinal}",
        "source_label": f"test-section-{ordinal}",
        "parent_tag": tag,
        "suggested_batch": batch,
        "suggested_unit_file": (
            f"translation-data/units/{batch}.jsonl" if batch is not None else None
        ),
        "unit_files": unit_files or [],
        "state": state,
    }


class PlanningTests(unittest.TestCase):
    def initialize_root(self, root: Path) -> None:
        (root / "upstream.lock").write_text(
            f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8"
        )
        for directory in (
            "translation-data/units",
            "translation-data/candidates/model",
            "translation-data/selections",
            "translation-data/reviewed",
        ):
            (root / directory).mkdir(parents=True, exist_ok=True)

    def test_explicit_selection_overrides_automatic_priority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize_root(root)
            write_json(
                root / "config/chapter-titles.json",
                {"schema_version": 1, "titles": {"alpha": "甲", "beta": "乙"}},
            )
            write_json(
                root / "config/translation-priorities.json",
                priority_config(
                    {
                        "alpha": chapter_policy("P1", 1),
                        "beta": chapter_policy("P0", 1),
                    }
                ),
            )
            write_json(
                root / "translation-data/chapter-templates/alpha.json",
                {
                    "source_commit": SOURCE_COMMIT,
                    "chapter": "alpha",
                    "chapter_ordinal": 1,
                    "source_title": "Alpha",
                    "source_state": "CURRENT",
                    "sections": [
                        section(
                            1,
                            "AAAA",
                            "READY",
                            ["translation-data/units/alpha-AAAA.jsonl"],
                        )
                    ],
                },
            )
            write_json(
                root / "translation-data/chapter-templates/beta.json",
                {
                    "source_commit": SOURCE_COMMIT,
                    "chapter": "beta",
                    "chapter_ordinal": 2,
                    "source_title": "Beta",
                    "source_state": "CURRENT",
                    "sections": [section(1, "BBBB", "UNPREPARED")],
                },
            )
            write_jsonl(
                root / "translation-data/units/alpha-AAAA.jsonl",
                [
                    {
                        "unit_id": "tag:AAAA:p001",
                        "source_commit": SOURCE_COMMIT,
                        "source_status": "CURRENT",
                        "risk_level": "R1",
                    }
                ],
            )

            plan = build_translation_plan(root)
            automatic = select_next_task(plan)
            self.assertEqual(automatic.mode, "automatic")
            self.assertEqual(automatic.task.chapter, "beta")
            self.assertEqual(automatic.task.action, "PREPARE_SCOPE")

            explicit = select_next_task(plan, chapter="1", tag="aaaa")
            self.assertEqual(explicit.mode, "explicit")
            self.assertEqual(explicit.task.chapter, "alpha")
            self.assertEqual(explicit.task.action, "TRANSLATE")
            payload = json.loads(render_task_selection_json(explicit))
            self.assertEqual(payload["selection"]["mode"], "explicit")
            self.assertEqual(payload["task"]["parent_tag"], "AAAA")

            with self.assertRaisesRegex(RecordError, "--tag requires --chapter"):
                select_next_task(plan, tag="AAAA")

            readme = root / "README.md"
            readme.write_text(
                "# Test\n\n<!-- translation-plan:start -->\nold\n"
                "<!-- translation-plan:end -->\n",
                encoding="utf-8",
            )
            report = root / "docs/translation-plan.md"
            count, errors = update_translation_plan(
                root, readme, report, check=False
            )
            self.assertEqual(count, 2)
            self.assertEqual(errors, [])
            self.assertIn("第 2 章 乙", readme.read_text(encoding="utf-8"))
            self.assertIn("全部 2 章", report.read_text(encoding="utf-8"))
            _, check_errors = update_translation_plan(
                root, readme, report, check=True
            )
            self.assertEqual(check_errors, [])

    def test_workflow_state_resolves_to_specific_action(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize_root(root)
            write_json(
                root / "config/chapter-titles.json",
                {"schema_version": 1, "titles": {"alpha": "甲"}},
            )
            write_json(
                root / "config/translation-priorities.json",
                priority_config({"alpha": chapter_policy("P0", 1)}),
            )
            sections = [
                section(1, None, "BLOCKED_NO_TAG"),
                section(2, "A002", "UNPREPARED"),
            ]
            units: list[dict[str, object]] = []
            candidates: list[dict[str, object]] = []
            revisions: list[dict[str, object]] = []
            specifications = {
                3: (["R1"], 0, []),
                4: (["R1", "R1"], 1, []),
                5: (["R1"], 1, []),
                6: (["R1", "R1"], 2, [(0, "LANGUAGE_REVIEWED", "INTERNAL")]),
                7: (["R3"], 1, [(0, "LANGUAGE_REVIEWED", "INTERNAL")]),
                8: (["R3"], 1, [(0, "MATH_REVIEWED", "INTERNAL")]),
                9: (["R1"], 1, [(0, "PUBLISHED", "RELEASED")]),
            }
            for ordinal, (risks, candidate_count, review_specs) in specifications.items():
                tag = f"A{ordinal:03d}"
                unit_file = f"translation-data/units/alpha-{tag}.jsonl"
                sections.append(section(ordinal, tag, "READY", [unit_file]))
                file_units: list[dict[str, object]] = []
                for index, risk in enumerate(risks, start=1):
                    unit = {
                        "unit_id": f"tag:{tag}:p{index:03d}",
                        "source_commit": SOURCE_COMMIT,
                        "source_status": "CURRENT",
                        "risk_level": risk,
                    }
                    units.append(unit)
                    file_units.append(unit)
                write_jsonl(root / unit_file, file_units)
                candidates.extend(
                    {
                        "unit_id": unit["unit_id"],
                        "source_commit": SOURCE_COMMIT,
                        "source_status": "CURRENT",
                    }
                    for unit in file_units[:candidate_count]
                )
                for unit_index, stage, publication in review_specs:
                    unit_id = str(file_units[unit_index]["unit_id"])
                    revisions.append(
                        {
                            "unit_id": unit_id,
                            "source_commit": SOURCE_COMMIT,
                            "source_status": "CURRENT",
                            "status": "current",
                            "stage": stage,
                            "publication_status": publication,
                        }
                    )
            write_jsonl(
                root / "translation-data/candidates/model/alpha.jsonl", candidates
            )
            for index, revision in enumerate(revisions, start=1):
                write_json(
                    root / f"translation-data/reviewed/revision-{index}.json", revision
                )
            write_json(
                root / "translation-data/chapter-templates/alpha.json",
                {
                    "source_commit": SOURCE_COMMIT,
                    "chapter": "alpha",
                    "chapter_ordinal": 1,
                    "source_title": "Alpha",
                    "source_state": "CURRENT",
                    "sections": sections,
                },
            )

            plan = build_translation_plan(root)
            self.assertEqual(
                [task.action for task in plan.chapters[0].tasks],
                [
                    "RESOLVE_TAG",
                    "PREPARE_SCOPE",
                    "TRANSLATE",
                    "CONTINUE_TRANSLATION",
                    "REVIEW",
                    "CONTINUE_REVIEW",
                    "MATHEMATICS_REVIEW",
                    "PUBLISH_PREPARATION",
                    "DONE",
                ],
            )
            completed = select_next_task(plan, chapter="alpha", tag="A009")
            self.assertIsNone(completed.task)
            fallback = select_next_task(
                plan, chapter="alpha", tag="A009", fallback=True
            )
            self.assertEqual(fallback.mode, "fallback")
            self.assertEqual(fallback.task.action, "RESOLVE_TAG")

    def test_mathematics_review_uses_risk_and_selection_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.initialize_root(root)
            write_json(
                root / "config/chapter-titles.json",
                {"schema_version": 1, "titles": {"alpha": "甲"}},
            )
            write_json(
                root / "config/translation-priorities.json",
                priority_config({"alpha": chapter_policy("P0", 1)}),
            )
            sections = []
            candidates = []
            cases = (
                ("A001", "R2", ["language", "mathematics"], "MATHEMATICS_REVIEW"),
                ("A002", "R3", ["language"], "MATHEMATICS_REVIEW"),
                ("A003", "R2", ["language"], "PUBLISH_PREPARATION"),
            )
            for ordinal, (tag, risk, reviews, _) in enumerate(cases, start=1):
                unit_id = f"tag:{tag}:p001"
                unit_file = f"translation-data/units/alpha-{tag}.jsonl"
                sections.append(section(ordinal, tag, "READY", [unit_file]))
                write_jsonl(
                    root / unit_file,
                    [
                        {
                            "unit_id": unit_id,
                            "source_commit": SOURCE_COMMIT,
                            "source_status": "CURRENT",
                            "risk_level": risk,
                        }
                    ],
                )
                candidates.append(
                    {
                        "unit_id": unit_id,
                        "source_commit": SOURCE_COMMIT,
                        "source_status": "CURRENT",
                    }
                )
                selection_id = f"selection-{tag.lower()}"
                write_json(
                    root / f"translation-data/selections/{selection_id}.json",
                    {
                        "selection_id": selection_id,
                        "review_required": reviews,
                    },
                )
                write_json(
                    root / f"translation-data/reviewed/revision-{tag.lower()}.json",
                    {
                        "unit_id": unit_id,
                        "source_commit": SOURCE_COMMIT,
                        "source_status": "CURRENT",
                        "status": "current",
                        "stage": "LANGUAGE_REVIEWED",
                        "publication_status": "INTERNAL",
                        "selection_id": selection_id,
                    },
                )
            write_jsonl(
                root / "translation-data/candidates/model/alpha.jsonl", candidates
            )
            write_json(
                root / "translation-data/chapter-templates/alpha.json",
                {
                    "source_commit": SOURCE_COMMIT,
                    "chapter": "alpha",
                    "chapter_ordinal": 1,
                    "source_title": "Alpha",
                    "source_state": "CURRENT",
                    "sections": sections,
                },
            )

            plan = build_translation_plan(root)
            self.assertEqual(
                [task.action for task in plan.chapters[0].tasks],
                [expected for _, _, _, expected in cases],
            )

    def test_repository_policy_prioritizes_active_chapters_112_through_117(self) -> None:
        root = Path(__file__).resolve().parents[1]
        plan = build_translation_plan(root)
        active_order = (115, 116, 117, 112, 113, 114)
        active = {
            chapter.ordinal: chapter
            for chapter in plan.chapters
            if chapter.ordinal in active_order
        }
        self.assertEqual(set(active), set(active_order))
        self.assertEqual(
            tuple(
                chapter.ordinal
                for chapter in sorted(
                    active.values(), key=lambda chapter: chapter.policy.order
                )
            ),
            active_order,
        )
        self.assertTrue(
            all(
                chapter.policy.priority == "P0"
                and chapter.policy.wave == 1
                and chapter.policy.order <= len(active_order)
                for chapter in active.values()
            )
        )
        other_p0_wave1 = [
            chapter
            for chapter in plan.chapters
            if chapter.ordinal not in active_order
            and chapter.policy.priority == "P0"
            and chapter.policy.wave == 1
        ]
        self.assertTrue(
            all(chapter.policy.order > len(active_order) for chapter in other_p0_wave1)
        )
        active_tasks = [
            task
            for chapter in active.values()
            for task in chapter.tasks
            if task.actionable
        ]
        if active_tasks:
            selected = select_next_task(plan)
            self.assertIsNotNone(selected.task)
            self.assertIn(selected.task.chapter_ordinal, active_order)


if __name__ == "__main__":
    unittest.main()
