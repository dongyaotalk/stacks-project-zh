from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.chapter_templates import initialize_chapter_templates


SOURCE_COMMIT = "a" * 40


class ChapterTemplateTests(unittest.TestCase):
    def test_initializes_ready_unprepared_and_unavailable_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            harvest = root / "harvest"
            tags = harvest / "tags"
            units = root / "translation-data" / "units"
            output = root / "translation-data" / "chapter-templates"
            tags.mkdir(parents=True)
            units.mkdir(parents=True)
            (root / "upstream.lock").write_text(
                f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8"
            )
            (harvest / "chapters.tex").write_text(
                "\\item \\hyperref[alpha-section-phantom]{Alpha}\n"
                "\\item \\hyperref[generated-section-phantom]{Generated}\n",
                encoding="utf-8",
            )
            (tags / "tags").write_text(
                "ABCD,alpha-section-first\nEFGH,alpha-section-second\n",
                encoding="utf-8",
            )
            (harvest / "alpha.tex").write_text(
                "\\title{Alpha Source}\n"
                "\\section{First}\n\\label{section-first}\nText.\n"
                "\\section{Second {Nested}}\n\\label{section-second}\nText.\n"
                "\\section{No Tag}\n\\label{section-no-tag}\nText.\n",
                encoding="utf-8",
            )
            (units / "alpha-ABCD.jsonl").write_text(
                json.dumps({"chapter": "alpha", "parent_tag": "ABCD"}) + "\n",
                encoding="utf-8",
            )

            count, errors = initialize_chapter_templates(
                root,
                harvest,
                root / "upstream.lock",
                units,
                output,
                check=False,
            )
            self.assertEqual(count, 2)
            self.assertEqual(errors, [])
            alpha = json.loads((output / "alpha.json").read_text(encoding="utf-8"))
            self.assertEqual(alpha["chapter_ordinal"], 1)
            self.assertEqual(alpha["source_title"], "Alpha Source")
            self.assertEqual(alpha["sections"][0]["state"], "READY")
            self.assertEqual(alpha["sections"][0]["parent_tag"], "ABCD")
            self.assertEqual(alpha["sections"][1]["state"], "UNPREPARED")
            self.assertEqual(alpha["sections"][1]["source_title"], "Second {Nested}")
            self.assertEqual(alpha["sections"][2]["state"], "BLOCKED_NO_TAG")
            self.assertIsNone(alpha["sections"][2]["parent_tag"])
            generated = json.loads(
                (output / "generated.json").read_text(encoding="utf-8")
            )
            self.assertEqual(generated["chapter_ordinal"], 2)
            self.assertEqual(generated["source_state"], "SOURCE_UNAVAILABLE")
            self.assertEqual(generated["sections"], [])

            checked_count, check_errors = initialize_chapter_templates(
                root,
                harvest,
                root / "upstream.lock",
                units,
                output,
                check=True,
            )
            self.assertEqual(checked_count, 2)
            self.assertEqual(check_errors, [])

            (output / "alpha.json").write_text("{}\n", encoding="utf-8")
            _, stale_errors = initialize_chapter_templates(
                root,
                harvest,
                root / "upstream.lock",
                units,
                output,
                check=True,
            )
            self.assertTrue(any("out of date" in error for error in stale_errors))


if __name__ == "__main__":
    unittest.main()
