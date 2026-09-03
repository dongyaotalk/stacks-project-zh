from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stacks_zh.cli import main
from stacks_zh.records import sha256_value, stamp_unit_hashes, write_jsonl


SOURCE_COMMIT = "c" * 40
REPOSITORY_ROOT = Path(__file__).parents[1]


def make_unit(unit_id: str) -> dict[str, object]:
    return stamp_unit_hashes(
        {
            "schema_version": 1,
            "unit_id": unit_id,
            "parent_tag": "TEST",
            "chapter": "test",
            "node_kind": "paragraph",
            "risk_level": "R1",
            "source_commit": SOURCE_COMMIT,
            "source_text": "A source sentence.",
            "source_status": "CURRENT",
            "placeholders": {},
            "render": {"prefix": "", "suffix": "\n"},
        }
    )


def make_candidate(unit: dict[str, object]) -> dict[str, object]:
    context = {"unit_ids": [unit["unit_id"]]}
    return {
        "schema_version": 1,
        "unit_id": unit["unit_id"],
        "source_commit": SOURCE_COMMIT,
        "source_text_hash": unit["source_text_hash"],
        "model_id": "test/model",
        "model_lane": "test",
        "harness_id": "codex",
        "run_id": "run-test",
        "reasoning_effort": "not_exposed",
        "prompt_version": "translator-v1",
        "glossary_revision": "git:test",
        "context": context,
        "context_hash": sha256_value(context),
        "translation": "一个源句。",
        "allowed_english": [],
        "term_occurrences": [],
        "unknown_terms": [],
        "notes": [],
        "stage": "TERM_OK",
        "source_status": "CURRENT",
        "qa_status": "PASS",
        "term_status": "CLEAR",
        "publication_status": "CANDIDATE",
        "created_at": "2026-08-25T00:00:00+08:00",
    }


class ValidateManyCliTests(unittest.TestCase):
    def write_pair(self, root: Path, name: str) -> tuple[Path, Path]:
        unit = make_unit(f"tag:TEST:{name}")
        unit_path = root / f"units-{name}.jsonl"
        candidate_path = root / f"candidates-{name}.jsonl"
        write_jsonl(unit_path, [unit])
        write_jsonl(candidate_path, [make_candidate(unit)])
        return unit_path, candidate_path

    def call_cli(self, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = main(list(arguments))
        return result, stdout.getvalue(), stderr.getvalue()

    def test_validate_many_accepts_aligned_paths_and_reports_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            first = self.write_pair(root, "one")
            second = self.write_pair(root, "two")

            result, stdout, stderr = self.call_cli(
                "validate-many",
                "--units",
                str(first[0]),
                str(second[0]),
                "--candidates",
                str(first[1]),
                str(second[1]),
                "--lock",
                str(lock),
            )

            self.assertEqual(result, 0)
            self.assertEqual(stderr, "")
            self.assertIn("Candidate batch QA: PASS (2 unit(s) across 2 batch(es))", stdout)

    def test_validate_many_returns_failure_for_bad_arguments_or_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            pair = self.write_pair(root, "one")

            result, stdout, stderr = self.call_cli(
                "validate-many",
                "--units",
                str(pair[0]),
                "--candidates",
                str(pair[1]),
                str(pair[1]),
                "--lock",
                str(lock),
            )
            self.assertEqual(result, 1)
            self.assertEqual(stdout, "")
            self.assertIn("same number", stderr)

            result, stdout, stderr = self.call_cli(
                "validate-many",
                "--units",
                str(pair[0]),
                "--candidates",
                str(root / "missing.jsonl"),
                "--lock",
                str(lock),
            )
            self.assertEqual(result, 1)
            self.assertEqual(stdout, "")
            self.assertIn("ERROR:", stderr)
            self.assertIn("cannot read", stderr)


class BatchWorkflowCliTests(unittest.TestCase):
    def call_cli(self, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = main(list(arguments))
        return result, stdout.getvalue(), stderr.getvalue()

    def test_assemble_many_rejects_unaligned_outputs(self) -> None:
        result, stdout, stderr = self.call_cli(
            "assemble-many",
            "--units",
            "one.jsonl",
            "two.jsonl",
            "--drafts",
            "drafts.jsonl",
            "--output",
            "one-output.jsonl",
            "--model-id",
            "test-model",
            "--model-lane",
            "test-lane",
            "--reasoning-effort",
            "not_exposed",
            "--prompt-version",
            "translator-v2",
            "--policy-revision",
            "git:policy",
            "--glossary-revision",
            "git:glossary",
            "--created-at",
            "2026-09-03T00:00:00Z",
            "--harness-id",
            "codex",
            "--model-record-id",
            "test:model:declared",
            "--run-id",
            "run-test",
            "--model-identity-confidence",
            "declared",
        )
        self.assertEqual(result, 1)
        self.assertEqual(stdout, "")
        self.assertIn("same number", stderr)


class BatchMakefileTests(unittest.TestCase):
    def test_batch_pack_and_assembly_targets_reuse_ordered_batches(self) -> None:
        pack = subprocess.run(
            ["make", "-n", "batch-pack", "BATCHES=alpha beta"],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(pack.returncode, 0, pack.stderr)
        self.assertIn("stacks_zh.py batch-pack", pack.stdout)
        self.assertLess(pack.stdout.index("alpha.jsonl"), pack.stdout.index("beta.jsonl"))

        assembly = subprocess.run(
            [
                "make",
                "-n",
                "assemble-batch",
                "BATCHES=alpha beta",
                "DRAFTS=tmp/drafts.jsonl",
                "MODEL=test-lane",
                "MODEL_ID=test-model",
                "MODEL_RECORD_ID=test:model:declared",
                "RUN_ID=run-test",
                "POLICY_REVISION=git:policy",
                "GLOSSARY_REVISION=git:glossary",
                "CREATED_AT=2026-09-03T00:00:00Z",
                "HARNESS_ID=codex",
                "MODEL_IDENTITY_CONFIDENCE=declared",
            ],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(assembly.returncode, 0, assembly.stderr)
        self.assertIn("stacks_zh.py assemble-many", assembly.stdout)
        self.assertIn("--drafts \"tmp/drafts.jsonl\"", assembly.stdout)
        self.assertIn("translation-data/candidates/test-lane/alpha.jsonl", assembly.stdout)
        self.assertIn("translation-data/candidates/test-lane/beta.jsonl", assembly.stdout)

    def test_batch_targets_expand_aligned_files(self) -> None:
        result = subprocess.run(
            [
                "make",
                "-n",
                "qa-batch",
                "BATCHES=alpha beta",
                "MODEL=test-lane",
            ],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("validate-many", result.stdout)
        self.assertIn("translation-data/units/alpha.jsonl", result.stdout)
        self.assertIn("translation-data/units/beta.jsonl", result.stdout)
        self.assertIn(
            "translation-data/candidates/test-lane/alpha.jsonl", result.stdout
        )
        self.assertIn(
            "translation-data/candidates/test-lane/beta.jsonl", result.stdout
        )

    def test_render_batch_target_uses_selected_output_directory(self) -> None:
        result = subprocess.run(
            [
                "make",
                "-n",
                "render-batch",
                "BATCHES=alpha beta",
                "MODEL=test-lane",
                "BATCH_RENDER_DIR=build/test-batch-render",
            ],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stacks_zh.py render", result.stdout)
        self.assertIn("--output-dir \"build/test-batch-render\"", result.stdout)


if __name__ == "__main__":
    unittest.main()
