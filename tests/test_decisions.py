from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.decisions import validate_repository_decisions
from stacks_zh.records import sha256_value


class DecisionTests(unittest.TestCase):
    def test_selection_review_and_revision_form_a_closed_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for directory in (
                "translation-data/units",
                "translation-data/candidates/model",
                "translation-data/selections",
                "translation-data/reviewed",
                "review/language",
            ):
                (root / directory).mkdir(parents=True)
            source_commit = "a" * 40
            source_text_hash = "sha256:" + "1" * 64
            translation = "测试译文。"
            translation_hash = sha256_value(translation)
            unit_id = "tag:TEST:statement"
            run_id = "run-test"
            (root / "translation-data/units/test.jsonl").write_text(
                json.dumps(
                    {
                        "unit_id": unit_id,
                        "risk_level": "R1",
                        "source_text_hash": source_text_hash,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "translation-data/candidates/model/test.jsonl").write_text(
                json.dumps(
                    {
                        "unit_id": unit_id,
                        "run_id": run_id,
                        "source_commit": source_commit,
                        "source_text_hash": source_text_hash,
                        "translation_hash": translation_hash,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "translation-data/selections/selection.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "selection_id": "selection-test",
                        "unit_id": unit_id,
                        "run_id": run_id,
                        "source_commit": source_commit,
                        "translation_hash": translation_hash,
                        "decision": "accept-candidate",
                        "decided_by": "github:maintainer",
                        "decided_at": "2026-08-25T00:00:00Z",
                        "reason": "通过。",
                    }
                ),
                encoding="utf-8",
            )
            (root / "review/language/review.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "review_id": "review-language",
                        "unit_id": unit_id,
                        "candidate_hash": translation_hash,
                        "run_id": run_id,
                        "source_commit": source_commit,
                        "review_type": "language",
                        "reviewer": "github:reviewer",
                        "reviewed_at": "2026-08-25T00:00:00Z",
                        "decision": "approved",
                        "issues_closed": [],
                        "resulting_translation_hash": translation_hash,
                        "notes": [],
                    }
                ),
                encoding="utf-8",
            )
            (root / "translation-data/reviewed/revision.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "revision_id": "revision-test",
                        "unit_id": unit_id,
                        "source_commit": source_commit,
                        "source_text_hash": source_text_hash,
                        "translation": translation,
                        "translation_hash": translation_hash,
                        "origin_run_id": run_id,
                        "selection_id": "selection-test",
                        "selected_by": "github:maintainer",
                        "created_at": "2026-08-25T00:00:00Z",
                        "reason": "采用。",
                        "supersedes_revision_id": None,
                        "review_ids": ["review-language"],
                        "risk_level": "R1",
                        "stage": "LANGUAGE_REVIEWED",
                        "source_status": "CURRENT",
                        "qa_status": "PASS",
                        "term_status": "CLEAR",
                        "publication_status": "INTERNAL",
                        "status": "current",
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(validate_repository_decisions(root), [])
            selection_path = root / "translation-data/selections/selection.json"
            selection = json.loads(selection_path.read_text(encoding="utf-8"))
            selection["review_required"] = ["language", "mathematics"]
            selection_path.write_text(json.dumps(selection), encoding="utf-8")
            errors = validate_repository_decisions(root)
            self.assertTrue(
                any("requires approved mathematics review" in error for error in errors)
            )
            selection.pop("review_required")
            selection_path.write_text(json.dumps(selection), encoding="utf-8")
            revision_path = root / "translation-data/reviewed/revision.json"
            revision = json.loads(revision_path.read_text(encoding="utf-8"))
            revision["translation"] = "被篡改。"
            revision_path.write_text(json.dumps(revision), encoding="utf-8")
            self.assertTrue(validate_repository_decisions(root))

    def test_selection_must_follow_machine_readable_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for directory in (
                "translation-data/units",
                "translation-data/candidates",
                "translation-data/selections",
                "translation-data/reviewed",
                "review/language",
                "review/mathematics",
            ):
                (root / directory).mkdir(parents=True)
            (root / "translation-data/selections/invalid.json").write_text(
                json.dumps({"schema_version": 1, "selection_id": "invalid"}),
                encoding="utf-8",
            )
            errors = validate_repository_decisions(root)
            self.assertTrue(any("missing required property 'unit_id'" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
