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
                        "source_status": "CURRENT",
                        "qa_status": "PASS",
                        "stage": "TERM_OK",
                        "term_status": "CLEAR",
                        "term_occurrences": [],
                        "unknown_terms": [],
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


class DecisionGateRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in (
            "translation-data/units", "translation-data/candidates/model",
            "translation-data/selections", "translation-data/reviewed",
            "review/language", "config",
        ):
            (self.root / directory).mkdir(parents=True)

    def write(self, relative: str, value: dict, *, jsonl: bool = False) -> None:
        (self.root / relative).write_text(json.dumps(value) + ("\n" if jsonl else ""), encoding="utf-8")

    def add_revision(self, revision_id: str, *, predecessor: str | None = None,
                     status: str = "current", unit_id: str = "tag:TEST:statement",
                     terms: bool = False, published: bool = False) -> None:
        from stacks_zh.records import stamp_unit_hashes

        commit = "a" * 40
        timestamp = "2026-10-04T00:00:00Z"
        translation = "栈（stack）。" if terms else f"测试译文 {revision_id}。"
        translation_hash = sha256_value(translation)
        unit = stamp_unit_hashes({
            "schema_version": 1, "unit_id": unit_id, "parent_tag": "TEST", "chapter": "test",
            "node_kind": "paragraph", "risk_level": "R1", "source_commit": commit,
            "source_text": "A stack." if terms else "A sentence.", "source_status": "CURRENT",
            "placeholders": {}, "render": {"prefix": "", "suffix": "\n"},
        })
        self.write(f"translation-data/units/{unit_id.replace(':', '-')}.jsonl", unit, jsonl=True)
        pair = {"source_term": "stack", "target_term": "栈"}
        context = {"source_commit": commit, "unit_id": unit_id}
        candidate = {
            "schema_version": 2, "unit_id": unit_id, "run_id": f"run-{revision_id}",
            "source_commit": commit, "source_text_hash": unit["source_text_hash"],
            "translation": translation, "translation_hash": translation_hash,
            "model_id": "fixture-model", "model_lane": "model", "harness_id": "fixture",
            "harness_version": "1", "model_record_id": "fixture:model", "model_snapshot": None,
            "model_identity_confidence": "declared", "reasoning_effort": "not_exposed",
            "prompt_version": "translator-v2", "glossary_revision": "fixture:none",
            "context": context, "context_hash": sha256_value(context), "allowed_english": [revision_id],
            "term_occurrences": [pair] if terms else [],
            "unknown_terms": [{**pair, "context": "Temporary fixture"}] if terms else [],
            "notes": [], "stage": "STRUCTURE_OK" if terms else "TERM_OK",
            "source_status": "CURRENT", "qa_status": "PASS",
            "term_status": "DECISION_REQUIRED" if terms else "CLEAR",
            "publication_status": "CANDIDATE", "created_at": timestamp,
        }
        self.write(f"translation-data/candidates/model/{revision_id}.jsonl", candidate, jsonl=True)
        self.write(f"translation-data/selections/{revision_id}.json", {
            "schema_version": 1, "selection_id": f"selection-{revision_id}", "unit_id": unit_id,
            "run_id": candidate["run_id"], "source_commit": commit, "translation_hash": translation_hash,
            "decision": "accept-candidate", "decided_by": "fixture:maintainer",
            "decided_at": timestamp, "reason": "Temporary fixture",
        })
        self.write(f"review/language/{revision_id}.json", {
            "schema_version": 1, "review_id": f"review-{revision_id}", "unit_id": unit_id,
            "candidate_hash": translation_hash, "run_id": candidate["run_id"], "source_commit": commit,
            "review_type": "language", "reviewer": "fixture:reviewer", "reviewed_at": timestamp,
            "decision": "approved", "issues_closed": [], "resulting_translation_hash": translation_hash,
            "notes": ["Temporary fixture"],
        })
        self.write(f"translation-data/reviewed/{revision_id}.json", {
            "schema_version": 1, "revision_id": revision_id, "unit_id": unit_id,
            "source_commit": commit, "source_text_hash": unit["source_text_hash"],
            "translation": translation, "translation_hash": translation_hash,
            "origin_run_id": candidate["run_id"], "selection_id": f"selection-{revision_id}",
            "selected_by": "fixture:maintainer", "created_at": timestamp, "reason": "Temporary fixture",
            "supersedes_revision_id": predecessor, "review_ids": [f"review-{revision_id}"],
            "risk_level": "R1", "stage": "PUBLISHED" if published else "LANGUAGE_REVIEWED",
            "source_status": "CURRENT", "qa_status": "PASS", "term_status": "CLEAR",
            "publication_status": "RELEASED" if published else "INTERNAL", "status": status,
        })

    def glossary(self, status: str = "approved", target: str = "栈") -> None:
        self.write("config/glossary.yml", {"schema": 1, "entries": [{
            "source_term": "stack", "target_term": target, "status": status,
            "definition_or_context": "Temporary fixture",
            "evidence": [{"unit_id": "tag:TEST:statement", "source_commit": "a" * 40}],
        }]})

    def test_published_revision_cannot_clear_candidate_pending_terms_itself(self) -> None:
        self.add_revision("r001", terms=True, published=True)
        self.write("config/glossary.yml", {"entries": []})
        errors = validate_repository_decisions(self.root)
        self.assertTrue(any("has no approved glossary decision" in error for error in errors))

    def test_clear_candidate_cannot_hide_unapproved_term_occurrences(self) -> None:
        self.add_revision("r001", terms=True)
        path = self.root / "translation-data/candidates/model/r001.jsonl"
        candidate = json.loads(path.read_text())
        candidate.update(unknown_terms=[], term_status="CLEAR", stage="TERM_OK")
        self.write("translation-data/candidates/model/r001.jsonl", candidate, jsonl=True)
        self.glossary("proposed")
        self.assertTrue(any("has no approved glossary decision" in error for error in validate_repository_decisions(self.root)))

    def test_real_glossary_approval_resolves_immutable_candidate_pending_terms(self) -> None:
        self.add_revision("r001", terms=True, published=True)
        path = self.root / "translation-data/candidates/model/r001.jsonl"
        before = path.read_bytes()
        self.glossary()
        self.assertEqual(validate_repository_decisions(self.root), [])
        self.assertEqual(path.read_bytes(), before)

    def test_proposed_deprecated_wrong_translation_and_missing_glossary_do_not_approve(self) -> None:
        self.add_revision("r001", terms=True)
        for status, target in (("proposed", "栈"), ("deprecated", "栈"), ("approved", "错误译法")):
            with self.subTest(status=status, target=target):
                self.glossary(status, target)
                self.assertTrue(any("has no approved glossary decision" in error for error in validate_repository_decisions(self.root)))
        (self.root / "config/glossary.yml").unlink()
        self.assertTrue(any("cannot verify glossary approvals" in error for error in validate_repository_decisions(self.root)))

    def test_selected_candidate_must_really_have_passed_structure_and_source_qa(self) -> None:
        self.add_revision("r001")
        path = self.root / "translation-data/candidates/model/r001.jsonl"
        original = json.loads(path.read_text())
        for field, value in (("qa_status", "FAIL"), ("stage", "AI_DRAFT"), ("source_status", "STALE_TEXT")):
            with self.subTest(field=field):
                self.write("translation-data/candidates/model/r001.jsonl", {**original, field: value}, jsonl=True)
                self.assertTrue(validate_repository_decisions(self.root))

    def test_two_and_three_revision_chains_keep_the_original_root(self) -> None:
        self.add_revision("r001", status="superseded")
        self.add_revision("r002", predecessor="r001")
        self.assertEqual(validate_repository_decisions(self.root), [])
        self.add_revision("r002", predecessor="r001", status="superseded")
        self.add_revision("r003", predecessor="r002")
        self.assertEqual(validate_repository_decisions(self.root), [])

    def test_multiple_roots_are_rejected(self) -> None:
        self.add_revision("r001", status="superseded")
        self.add_revision("r002")
        self.assertTrue(any("multiple revision roots" in error for error in validate_repository_decisions(self.root)))

    def test_self_reference_is_rejected(self) -> None:
        self.add_revision("r001", predecessor="r001")
        errors = validate_repository_decisions(self.root)
        self.assertTrue(any("cannot supersede itself" in error for error in errors))
        self.assertTrue(any("replacement cycle" in error for error in errors))

    def test_cycle_is_rejected(self) -> None:
        self.add_revision("r001", predecessor="r003", status="superseded")
        self.add_revision("r002", predecessor="r001", status="superseded")
        self.add_revision("r003", predecessor="r002")
        self.assertTrue(any("replacement cycle" in error for error in validate_repository_decisions(self.root)))

    def test_revision_cannot_have_two_successors(self) -> None:
        self.add_revision("r001", status="superseded")
        self.add_revision("r002", predecessor="r001", status="superseded")
        self.add_revision("r003", predecessor="r001")
        self.assertTrue(any("multiple successors" in error for error in validate_repository_decisions(self.root)))

    def test_cross_unit_replacement_is_rejected(self) -> None:
        self.add_revision("r001", status="superseded")
        self.add_revision("r002", predecessor="r001", unit_id="tag:OTHER:statement")
        self.assertTrue(any("belongs to another unit" in error for error in validate_repository_decisions(self.root)))

    def test_superseded_revision_must_have_a_successor(self) -> None:
        self.add_revision("r001", status="superseded")
        self.assertTrue(any("has no successor" in error for error in validate_repository_decisions(self.root)))

    def test_retired_first_revision_can_remain_without_a_successor(self) -> None:
        self.add_revision("r001", status="retired")
        self.assertEqual(validate_repository_decisions(self.root), [])


if __name__ == "__main__":
    unittest.main()
