#!/usr/bin/env python3
"""Migrate the historical Codex candidate lane to precise model provenance.

The project owner confirmed that the existing Codex candidates used GPT-5.6-sol.
This script keeps every translation and timestamp, adds schema-v2 provenance, moves
the lane to a model-specific directory, and creates one immutable run manifest per
candidate batch.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


SOURCE_MODEL_ID = "gpt-5.6-sol"
MODEL_LANE = "openai-gpt-5.6-sol"
MODEL_RECORD_ID = "openai:gpt-5.6-sol:owner-confirmed"
HARNESS_ID = "codex"
HARNESS_VERSION = "unknown"
IDENTITY_CONFIDENCE = "owner-confirmed"


def sha256_value(value: str) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_run_id(batch: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", batch)
    return f"legacy-{value}-gpt56sol"


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def migrate(root: Path) -> tuple[int, int]:
    old_root = root / "translation-data" / "candidates" / "codex"
    new_root = root / "translation-data" / "candidates" / MODEL_LANE
    runs_root = root / "translation-data" / "runs"
    if not old_root.is_dir():
        raise SystemExit(f"missing historical candidate directory: {old_root}")
    if new_root.exists():
        raise SystemExit(f"refusing to overwrite existing directory: {new_root}")
    new_root.mkdir(parents=True)
    runs_root.mkdir(parents=True, exist_ok=True)

    file_count = 0
    record_count = 0
    for old_path in sorted(old_root.glob("*.jsonl")):
        batch = old_path.stem
        records = read_jsonl(old_path)
        if not records:
            continue
        run_id = safe_run_id(batch)
        migrated: list[dict[str, object]] = []
        context_hashes: set[str] = set()
        for record in records:
            migrated_record = dict(record)
            migrated_record["schema_version"] = 2
            migrated_record["model_id"] = SOURCE_MODEL_ID
            migrated_record["model_lane"] = MODEL_LANE
            migrated_record["harness_id"] = HARNESS_ID
            migrated_record["harness_version"] = HARNESS_VERSION
            migrated_record["model_record_id"] = MODEL_RECORD_ID
            migrated_record["model_snapshot"] = None
            migrated_record["model_identity_confidence"] = IDENTITY_CONFIDENCE
            migrated_record["run_id"] = run_id
            migrated_record["translation_hash"] = sha256_value(str(record["translation"]))
            context_hashes.add(str(record["context_hash"]))
            migrated.append(migrated_record)

        new_path = new_root / old_path.name
        write_jsonl(new_path, migrated)
        source_commit = str(migrated[0]["source_commit"])
        created_at = str(migrated[0]["created_at"])
        prompt_versions = sorted({str(record["prompt_version"]) for record in migrated})
        policy_revisions = sorted({str(record["context"]["policy_revision"]) for record in migrated})
        glossary_revisions = sorted({str(record["glossary_revision"]) for record in migrated})
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "run_kind": "historical-import",
            "task_id": f"legacy-{batch}",
            "source_commit": source_commit,
            "unit_ids": [str(record["unit_id"]) for record in migrated],
            "harness": {
                "id": HARNESS_ID,
                "version": HARNESS_VERSION,
                "adapter_version": "stacks-harness-v1",
            },
            "model": {
                "record_id": MODEL_RECORD_ID,
                "provider": "OpenAI",
                "requested_id": SOURCE_MODEL_ID,
                "resolved_id": SOURCE_MODEL_ID,
                "snapshot": None,
                "identity_confidence": IDENTITY_CONFIDENCE,
            },
            "inputs": {
                "prompt_version": prompt_versions[0] if len(prompt_versions) == 1 else "mixed:" + ",".join(prompt_versions),
                "policy_revision": policy_revisions[0] if len(policy_revisions) == 1 else "mixed",
                "glossary_revision": glossary_revisions[0] if len(glossary_revisions) == 1 else "mixed",
                "context_hashes": sorted(context_hashes),
            },
            "created_at": created_at,
            "replayable": False,
            "status": "recorded",
            "notes": [
                "Historical candidate import; model identity confirmed by project owner.",
                "The original Codex runtime did not expose a provider snapshot.",
            ],
        }
        (runs_root / f"{run_id}.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        file_count += 1
        record_count += len(migrated)

    shutil.rmtree(old_root)
    return file_count, record_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    files, records = migrate(args.root.resolve())
    print(f"Migrated {records} candidate record(s) in {files} batch(es).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
