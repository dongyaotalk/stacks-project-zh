from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.batching import write_batch_package
from stacks_zh.records import RecordError, stamp_unit_hashes, write_jsonl


SOURCE_COMMIT = "c" * 40


def make_unit(tag: str, text: str, *, chapter: str = "test") -> dict[str, object]:
    return stamp_unit_hashes(
        {
            "schema_version": 1,
            "unit_id": f"tag:{tag}:p001",
            "parent_tag": tag,
            "chapter": chapter,
            "node_kind": "paragraph",
            "risk_level": "R1",
            "source_commit": SOURCE_COMMIT,
            "source_text": text,
            "source_status": "CURRENT",
            "placeholders": {"MATH_0001": "$x$"},
            "render": {"prefix": "\\begin{lemma}\n", "suffix": "\\end{lemma}\n"},
        }
    )


class BatchPackageTests(unittest.TestCase):
    def prepare_support_files(self, root: Path) -> tuple[Path, Path, Path, Path]:
        lock = root / "upstream.lock"
        prompt = root / "translator-v2.md"
        style = root / "style-guide.md"
        workflow = root / "workflow.yml"
        lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
        prompt.write_text("Translate all supplied units.\n", encoding="utf-8")
        style.write_text("Use concise mathematical Chinese.\n", encoding="utf-8")
        workflow.write_text(
            "unit:\n"
            "  preferred_min_source_words: 300\n"
            "  preferred_max_source_words: 1500\n",
            encoding="utf-8",
        )
        return lock, prompt, style, workflow

    def test_writes_one_protected_package_for_ordered_unit_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock, prompt, style, workflow = self.prepare_support_files(root)
            paths = [root / "first.jsonl", root / "second.jsonl"]
            source = " ".join(["word"] * 160) + " <MATH_0001>"
            write_jsonl(paths[0], [make_unit("FIRST", source)])
            write_jsonl(paths[1], [make_unit("SECOND", source)])
            output = root / "tmp" / "package.json"

            summary = write_batch_package(
                paths, output, lock, prompt, style, workflow
            )

            package = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(summary.source_word_count, 320)
            self.assertEqual(package["parent_tags"], ["FIRST", "SECOND"])
            self.assertEqual(package["unit_count"], 2)
            self.assertIn(
                "Return JSONL only", package["model_input"]["batch_instructions"]
            )
            self.assertEqual(
                package["output_contract"]["required_unit_ids"],
                ["tag:FIRST:p001", "tag:SECOND:p001"],
            )
            packaged_unit = package["model_input"]["units"][0]
            self.assertIn("<MATH_0001>", packaged_unit["source_text"])
            self.assertNotIn("placeholders", packaged_unit)
            self.assertNotIn("render", packaged_unit)

            with self.assertRaisesRegex(RecordError, "must not overwrite"):
                write_batch_package(paths, paths[0], lock, prompt, style, workflow)

    def test_rejects_bad_count_cross_chapter_and_unacknowledged_size(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock, prompt, style, workflow = self.prepare_support_files(root)
            first = root / "first.jsonl"
            second = root / "second.jsonl"
            short = "A short sentence."
            write_jsonl(first, [make_unit("FIRST", short)])
            write_jsonl(second, [make_unit("SECOND", short)])
            output = root / "package.json"

            with self.assertRaisesRegex(RecordError, "requires 2-8"):
                write_batch_package([first], output, lock, prompt, style, workflow)
            with self.assertRaisesRegex(RecordError, "preferred range"):
                write_batch_package(
                    [first, second], output, lock, prompt, style, workflow
                )
            self.assertFalse(output.exists())

            summary = write_batch_package(
                [first, second],
                output,
                lock,
                prompt,
                style,
                workflow,
                allow_outside_preferred_range=True,
            )
            self.assertLess(summary.source_word_count, 300)
            self.assertTrue(
                json.loads(output.read_text(encoding="utf-8"))[
                    "outside_preferred_range"
                ]
            )

            write_jsonl(second, [make_unit("SECOND", short, chapter="other")])
            with self.assertRaisesRegex(RecordError, "cannot cross chapters"):
                write_batch_package(
                    [first, second],
                    output,
                    lock,
                    prompt,
                    style,
                    workflow,
                    allow_outside_preferred_range=True,
                )

    def test_rejects_non_adjacent_sections_when_templates_are_supplied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock, prompt, style, workflow = self.prepare_support_files(root)
            first = root / "first.jsonl"
            third = root / "third.jsonl"
            write_jsonl(first, [make_unit("FIRST", " ".join(["word"] * 160))])
            write_jsonl(third, [make_unit("THIRD", " ".join(["word"] * 160))])
            templates = root / "templates"
            templates.mkdir()
            (templates / "test.json").write_text(
                json.dumps(
                    {
                        "chapter": "test",
                        "sections": [
                            {"ordinal": 1, "unit_files": [str(first)]},
                            {"ordinal": 2, "unit_files": [str(root / "second.jsonl")]},
                            {"ordinal": 3, "unit_files": [str(third)]},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RecordError, "adjacent Sections"):
                write_batch_package(
                    [first, third],
                    root / "package.json",
                    lock,
                    prompt,
                    style,
                    workflow,
                    chapter_templates_path=templates,
                )


if __name__ == "__main__":
    unittest.main()
