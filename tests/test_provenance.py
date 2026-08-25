from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import sha256_value


class ProvenanceTests(unittest.TestCase):
    def test_candidate_must_match_run_manifest(self) -> None:
        source_commit = "a" * 40
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "translation-data" / "runs").mkdir(parents=True)
            (root / "translation-data" / "candidates" / "openai-gpt-5.6-sol").mkdir(parents=True)
            (root / "config").mkdir()
            (root / "config" / "models.yml").write_text(
                "lanes:\n"
                "  openai-gpt-5.6-sol:\n"
                "    model_id: gpt-5.6-sol\n"
                "    model_record_id: openai:gpt-5.6-sol:owner-confirmed\n"
                "    harness_id: codex\n"
                "    prompt_version: test\n"
                "model_records:\n"
                "  openai:gpt-5.6-sol:owner-confirmed:\n",
                encoding="utf-8",
            )
            run_id = "run-test"
            manifest = {
                "schema_version": 1,
                "run_id": run_id,
                "run_kind": "translation",
                "task_id": "test",
                "source_commit": source_commit,
                "unit_ids": ["tag:TEST:p001"],
                "harness": {"id": "codex", "version": "test", "adapter_version": "test"},
                "model": {
                    "record_id": "openai:gpt-5.6-sol:owner-confirmed",
                    "provider": "OpenAI",
                    "requested_id": "gpt-5.6-sol",
                    "resolved_id": "gpt-5.6-sol",
                    "snapshot": None,
                    "identity_confidence": "owner-confirmed",
                },
                "inputs": {
                    "prompt_version": "test",
                    "policy_revision": "test",
                    "glossary_revision": "test",
                    "context_hashes": ["sha256:" + "1" * 64],
                },
                "created_at": "2026-08-25T00:00:00+00:00",
                "replayable": False,
            }
            (root / "translation-data" / "runs" / f"{run_id}.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            candidate = {
                "schema_version": 2,
                "run_id": run_id,
                "source_commit": source_commit,
                "model_lane": "openai-gpt-5.6-sol",
                "model_record_id": "openai:gpt-5.6-sol:owner-confirmed",
                "model_id": "gpt-5.6-sol",
                "harness_id": "codex",
                "harness_version": "test",
                "model_snapshot": None,
                "model_identity_confidence": "owner-confirmed",
                "prompt_version": "test",
                "glossary_revision": "test",
                "context": {
                    "prompt_version": "test",
                    "policy_revision": "test",
                    "source_commit": source_commit,
                },
                "context_hash": "sha256:" + "1" * 64,
                "created_at": "2026-08-25T00:00:00+00:00",
                "translation": "测试。",
                "translation_hash": sha256_value("测试。"),
                "unit_id": "tag:TEST:p001",
            }
            path = root / "translation-data" / "candidates" / "openai-gpt-5.6-sol" / "test.jsonl"
            path.write_text(json.dumps(candidate), encoding="utf-8")
            self.assertEqual(validate_repository_provenance(root), [])
            candidate["model_id"] = "other-model"
            path.write_text(json.dumps(candidate), encoding="utf-8")
            self.assertTrue(validate_repository_provenance(root))

    def test_candidate_prompt_must_match_manifest_and_lane(self) -> None:
        source_commit = "a" * 40
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "translation-data/runs").mkdir(parents=True)
            (root / "translation-data/candidates/model").mkdir(parents=True)
            (root / "config").mkdir()
            (root / "config/models.yml").write_text(
                "lanes:\n"
                "  model:\n"
                "    model_id: concrete-model\n"
                "    model_record_id: provider:concrete-model:declared\n"
                "    harness_id: codex\n"
                "    prompt_version: translator-v2\n"
                "model_records:\n",
                encoding="utf-8",
            )
            manifest = {
                "schema_version": 1,
                "run_id": "run-test",
                "run_kind": "translation",
                "task_id": "test",
                "source_commit": source_commit,
                "unit_ids": ["tag:TEST:p001"],
                "harness": {"id": "codex", "version": "test", "adapter_version": "test"},
                "model": {
                    "record_id": "provider:concrete-model:declared",
                    "provider": "Provider",
                    "requested_id": "concrete-model",
                    "resolved_id": "concrete-model",
                    "snapshot": None,
                    "identity_confidence": "declared",
                },
                "inputs": {
                    "prompt_version": "translator-v2",
                    "policy_revision": "git:test",
                    "glossary_revision": "git:test",
                    "context_hashes": ["sha256:" + "1" * 64],
                },
                "created_at": "2026-08-25T00:00:00Z",
                "replayable": False,
            }
            (root / "translation-data/runs/run-test.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            candidate = {
                "schema_version": 2,
                "run_id": "run-test",
                "source_commit": source_commit,
                "model_lane": "model",
                "model_record_id": "provider:concrete-model:declared",
                "model_id": "concrete-model",
                "harness_id": "codex",
                "harness_version": "test",
                "model_snapshot": None,
                "model_identity_confidence": "declared",
                "prompt_version": "translator-v1",
                "glossary_revision": "git:test",
                "context": {
                    "prompt_version": "translator-v1",
                    "policy_revision": "git:test",
                    "source_commit": source_commit,
                },
                "context_hash": "sha256:" + "1" * 64,
                "created_at": "2026-08-25T00:00:00Z",
                "translation": "测试。",
                "translation_hash": sha256_value("测试。"),
                "unit_id": "tag:TEST:p001",
            }
            (root / "translation-data/candidates/model/test.jsonl").write_text(
                json.dumps(candidate), encoding="utf-8"
            )
            errors = validate_repository_provenance(root)
            self.assertTrue(any("prompt_version does not match" in error for error in errors))

    def test_manifest_must_follow_machine_readable_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "translation-data" / "runs").mkdir(parents=True)
            (root / "translation-data" / "candidates").mkdir(parents=True)
            (root / "translation-data" / "runs" / "invalid.json").write_text(
                json.dumps({"schema_version": 1, "run_id": "invalid"}),
                encoding="utf-8",
            )
            errors = validate_repository_provenance(root)
            self.assertTrue(any("missing required property 'run_kind'" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
