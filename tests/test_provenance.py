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
                    "requested_id": "gpt-5.6-sol",
                    "resolved_id": "gpt-5.6-sol",
                },
                "inputs": {
                    "prompt_version": "test",
                    "policy_revision": "test",
                    "glossary_revision": "test",
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


if __name__ == "__main__":
    unittest.main()
