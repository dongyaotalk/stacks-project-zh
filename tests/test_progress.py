from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.progress import ChapterProgress, SectionProgress, update_progress_report


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
    def test_chapter_status_uses_translation_stage_not_preparation(self) -> None:
        def chapter(
            *, candidate: int = 0, reviewed: int = 0, published: int = 0
        ) -> ChapterProgress:
            section = SectionProgress(
                ordinal=1,
                source_title="第一节",
                parent_tag="AAAA",
                required_tags=2,
                prepared_tags=2,
                total_units=2,
                candidate_units=candidate,
                reviewed_units=reviewed,
                published_units=published,
            )
            return ChapterProgress(
                ordinal=1,
                slug="alpha",
                title="甲",
                source_state="CURRENT",
                sections=(section,),
            )

        self.assertEqual(chapter().status, "未开始")
        self.assertEqual(chapter(candidate=1).status, "翻译中")
        self.assertEqual(chapter(candidate=2).status, "候选译文完成，待审校")
        self.assertEqual(chapter(candidate=2, reviewed=1).status, "人工审校中")
        self.assertEqual(
            chapter(candidate=2, reviewed=2).status, "人工审校完成，待发布"
        )
        self.assertEqual(
            chapter(candidate=2, reviewed=2, published=1).status, "发布中"
        )
        self.assertEqual(
            chapter(candidate=2, reviewed=2, published=2).status, "已发布"
        )

    def test_generates_and_checks_section_based_chapter_progress(self) -> None:
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
                    "source_file": "alpha.tex",
                    "sections": [
                        {
                            "ordinal": 1,
                            "source_title": "First",
                            "source_label": "alpha-section-first",
                            "parent_tag": "AAAA",
                        }
                    ],
                },
            )
            write_json(
                root / "translation-data/chapter-templates/beta.json",
                {
                    "chapter": "beta",
                    "chapter_ordinal": 2,
                    "source_commit": SOURCE_COMMIT,
                    "source_state": "CURRENT",
                    "source_file": "beta.tex",
                    "sections": [
                        {
                            "ordinal": 1,
                            "source_title": "Only",
                            "source_label": "beta-section-only",
                            "parent_tag": "BBBB",
                        }
                    ],
                },
            )
            (root / "harvest/alpha.tex").write_text(
                "\\section{First}\n\\label{section-first}\n"
                "\\begin{lemma}\n\\label{lemma-second}\nText.\n\\end{lemma}\n",
                encoding="utf-8",
            )
            (root / "harvest/beta.tex").write_text(
                "\\section{Only}\n\\label{section-only}\nText.\n",
                encoding="utf-8",
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
                for unit_id in ("tag:AAAA:title", "tag:AAAA:p001", "tag:AAAB:statement")
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
            self.assertIn("1 个 Section 候选译文完成，0 个正在翻译", readme_text)
            self.assertIn("| 人工审校中 | 1 | 第 1 章 |", readme_text)
            self.assertIn("| 未开始 | 1 | 第 2 章 |", readme_text)
            self.assertIn(
                "| 1 | 甲（`alpha`） | 人工审校中 | 1 / 1（100.0%） | 0 | 0 | 0 | 0 |",
                readme_text,
            )
            self.assertNotIn("`beta`", readme_text)
            report_text = report.read_text(encoding="utf-8")
            self.assertIn(
                "| 2 | 乙（`beta`） | 未开始 | 0 / 1（0.0%） | 0 | 1 | 0 | 0 |",
                report_text,
            )
            self.assertIn("Section 来自锁定英文源", report_text)

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
