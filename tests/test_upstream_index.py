from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.upstream import validate_upstream_index


class UpstreamIndexTests(unittest.TestCase):
    def test_index_must_match_lock_harvest_report_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "zh"
            harvest = Path(temp_dir) / "en"
            (root / "upstream-index/manifests").mkdir(parents=True)
            (root / "sync-reports").mkdir()
            (harvest / "tags").mkdir(parents=True)
            commit = "a" * 40
            repository = "https://example.invalid/stacks.git"
            commit_date = "2026-08-26"
            (root / "upstream.lock").write_text(
                f'repository = "{repository}"\ncommit = "{commit}"\n'
                f'commit_date = "{commit_date}"\n',
                encoding="utf-8",
            )
            tags = b"0001,test-label\n"
            chapters = b"\\input{test}\n"
            (harvest / "tags/tags").write_bytes(tags)
            (harvest / "chapters.tex").write_bytes(chapters)
            manifest = {
                "schema_version": 1,
                "repository": repository,
                "commit": commit,
                "commit_date": commit_date,
                "permanent_tag_count": 1,
                "tags_sha256": "sha256:" + hashlib.sha256(tags).hexdigest(),
                "chapters_sha256": "sha256:" + hashlib.sha256(chapters).hexdigest(),
                "parser_version": "test",
                "normalization_version": "test",
            }
            (root / f"upstream-index/manifests/{commit}.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            report_name = "baseline-aaaaaaaa"
            report = {
                "new_commit": commit,
                "qa_result": "BASELINE",
                "unresolved_mappings": [],
            }
            (root / f"sync-reports/{report_name}.json").write_text(
                json.dumps(report), encoding="utf-8"
            )
            (root / "UPSTREAM_HISTORY.md").write_text(
                f"{commit}\n[{report_name}.md](sync-reports/{report_name}.md)\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_upstream_index(root, harvest), [])
            (harvest / "tags/tags").write_bytes(tags + b"0002,other-label\n")
            errors = validate_upstream_index(root, harvest)
            self.assertTrue(any("tags_sha256 does not match" in error for error in errors))
            self.assertTrue(any("permanent_tag_count does not match" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
