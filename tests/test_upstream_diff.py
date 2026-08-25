from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class UpstreamDiffTests(unittest.TestCase):
    def test_classifies_unit_changes_and_added_retired(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old = root / "old"
            new = root / "new"
            old.mkdir()
            new.mkdir()
            def unit(unit_id: str, text: str, math: str = "math-a") -> dict[str, str]:
                return {
                    "unit_id": unit_id,
                    "source_text_hash": text,
                    "source_math_hash": math,
                    "source_structure_hash": "structure-a",
                }

            (old / "batch.jsonl").write_text(
                "\n".join(
                    json.dumps(item)
                    for item in (
                        unit("tag:A:text", "text-a"),
                        unit("tag:A:math", "text-a", "math-a"),
                        unit("tag:A:retired", "text-a"),
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            (new / "batch.jsonl").write_text(
                "\n".join(
                    json.dumps(item)
                    for item in (
                        unit("tag:A:text", "text-b"),
                        unit("tag:A:math", "text-a", "math-b"),
                        unit("tag:A:added", "text-a"),
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            output_json = root / "report.json"
            output_md = root / "report.md"
            script = Path(__file__).parents[1] / "scripts" / "upstream_diff.py"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--old-units",
                    str(old),
                    "--new-units",
                    str(new),
                    "--old-commit",
                    "a" * 40,
                    "--new-commit",
                    "b" * 40,
                    "--output-json",
                    str(output_json),
                    "--output-md",
                    str(output_md),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output_json.read_text(encoding="utf-8"))
            statuses = {item["unit_id"]: item["status"] for item in report["unit_changes"]}
            self.assertEqual(statuses["tag:A:text"], "STALE_TEXT")
            self.assertEqual(statuses["tag:A:math"], "STALE_MATH")
            self.assertEqual(statuses["tag:A:added"], "UNTRANSLATED")
            self.assertEqual(statuses["tag:A:retired"], "RETIRED")
            self.assertEqual(report["qa_result"], "PASS")


if __name__ == "__main__":
    unittest.main()
