from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.progress import update_progress_report


SOURCE_COMMIT = "a" * 40


def write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def write_jsonl(path: Path, values: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(value) + "\n" for value in values), encoding="utf-8"
    )


class ProgressReportTests(unittest.TestCase):
    def test_generates_and_checks_tag_based_chapter_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tags = root / "harvest/tags/tags"
            tags.parent.mkdir(parents=True)
            tags.write_text(
                "NAV0,book-part-example\n"
                "AAAA,alpha-section-first\n"
                "AAAB,alpha-lemma-second\n"
                "BBBB,beta-section-only\n",
                encoding="utf-8",
            )
            (root / "upstream.lock").write_text(
                f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8"
            )
            write_json(
                root / "config/chapter-titles.json",
                {"schema_version": 1, "titles": {"alpha": "甲", "beta": "乙"}},
            )
            write_json(
                root / "translation-data/chapter-templates/alpha.json",
                {
                    "chapter": "alpha",
                    "chapter_ordinal": 1,
                    "source_commit": SOURCE_COMMIT,
                    "source_state": "CURRENT",
                },
            )
            write_json(
                root / "translation-data/chapter-templates/beta.json",
                {
                    "chapter": "beta",
                    "chapter_ordinal": 2,
                    "source_commit": SOURCE_COMMIT,
                    "source_state": "CURRENT",
                },
            )
            units = [
                {
                    "unit_id": "tag:AAAA:title",
                    "parent_tag": "AAAA",
                    "chapter": "alpha",
                    "source_commit": SOURCE_COMMIT,
                    "source_status": "CURRENT",
                },
                {
                    "unit_id": "tag:AAAA:p001",
                    "parent_tag": "AAAA",
                    "chapter": "alpha",
                    "source_commit": SOURCE_COMMIT,
                    "source_status": "CURRENT",
                },
                {
                    "unit_id": "tag:AAAB:statement",
                    "parent_tag": "AAAB",
                    "chapter": "alpha",
                    "source_commit": SOURCE_COMMIT,
                    "source_status": "CURRENT",
                },
            ]
            write_jsonl(root / "translation-data/units/alpha.jsonl", units)
            candidates = [
                {
                    "unit_id": unit_id,
                    "source_commit": SOURCE_COMMIT,
                    "source_status": "CURRENT",
                }
                for unit_id in ("tag:AAAA:title", "tag:AAAA:p001")
            ]
            candidates.append(dict(candidates[0]))
            write_jsonl(
                root / "translation-data/candidates/model/alpha.jsonl", candidates
            )
            for index, unit_id in enumerate(("tag:AAAA:title", "tag:AAAA:p001"), 1):
                write_json(
                    root / f"translation-data/reviewed/alpha/revision-{index}.json",
                    {
                        "unit_id": unit_id,
                        "source_commit": SOURCE_COMMIT,
                        "source_status": "CURRENT",
                        "status": "current",
                        "stage": "LANGUAGE_REVIEWED",
                        "publication_status": "INTERNAL",
                    },
                )
            readme = root / "README.md"
            readme.write_text(
                "# Test\n\n<!-- translation-progress:start -->\nold\n"
                "<!-- translation-progress:end -->\n",
                encoding="utf-8",
            )
            report = root / "docs/translation-progress.md"

            count, errors = update_progress_report(
                root, tags, readme, report, check=False
            )
            self.assertEqual(count, 2)
            self.assertEqual(errors, [])
            readme_text = readme.read_text(encoding="utf-8")
            self.assertIn("模型候选译文覆盖 | 1 / 3（33.3%）", readme_text)
            self.assertIn("人工审校译文覆盖 | 1 / 3（33.3%）", readme_text)
            self.assertIn("| 1 | 甲（`alpha`） | 1 / 2（50.0%）", readme_text)
            self.assertNotIn("`beta`", readme_text)
            report_text = report.read_text(encoding="utf-8")
            self.assertIn("| 2 | 乙（`beta`） | 0 / 1（0.0%）", report_text)
            self.assertIn("另有 1 个 `book-part-*` 导航 Tag", report_text)

            checked_count, check_errors = update_progress_report(
                root, tags, readme, report, check=True
            )
            self.assertEqual(checked_count, 2)
            self.assertEqual(check_errors, [])
            report.write_text(report_text + "stale\n", encoding="utf-8")
            _, stale_errors = update_progress_report(
                root, tags, readme, report, check=True
            )
            self.assertTrue(any("out of date" in error for error in stale_errors))


if __name__ == "__main__":
    unittest.main()
