from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.terminology import load_approved_term_pairs


class GlossaryApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "glossary.yml"

    def test_current_empty_yaml_glossary_is_supported(self) -> None:
        self.path.write_text("schema: 1\nlanguage: zh-CN\nentries: []\n", encoding="utf-8")
        self.assertEqual(load_approved_term_pairs(self.path), set())

    def test_block_yaml_quotes_comments_and_evidence_do_not_change_approval(self) -> None:
        self.path.write_text('''schema: 1
entries:
  - source_term: "stack #1"
    target_term: '栈''一'
    status: approved # an actual top-level approval
    definition_or_context: >
      Temporary
      fixture
    evidence:
      - chapter: test
        status: deprecated
    alternatives:
      - 另一译法
  - source_term: another stack
    target_term: 另一栈
    status: proposed
    definition_or_context: Temporary fixture
    evidence: ["test"]
''', encoding="utf-8")
        self.assertEqual(load_approved_term_pairs(self.path), {("stack #1", "栈'一")})

    def test_json_document_is_a_supported_yaml_subset(self) -> None:
        self.path.write_text(json.dumps({"entries": [{
            "source_term": "stack", "target_term": "栈", "status": "approved",
            "definition_or_context": "test", "evidence": ["test"],
        }]}), encoding="utf-8")
        self.assertEqual(load_approved_term_pairs(self.path), {("stack", "栈")})

    def test_malformed_entries_fail_closed(self) -> None:
        base = {"source_term": "stack", "target_term": "栈", "status": "approved",
                "definition_or_context": "test", "evidence": ["test"]}
        for field, value in (("status", "approved-ish"), ("status", True), ("evidence", []),
                             ("evidence", "test"), ("definition_or_context", ""), ("target_term", None)):
            with self.subTest(field=field, value=value):
                self.path.write_text(json.dumps({"entries": [{**base, field: value}]}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "cannot verify glossary approvals"):
                    load_approved_term_pairs(self.path)

    def test_duplicate_approval_fields_and_aliases_are_rejected(self) -> None:
        for status in ("status: proposed\n    status: approved", "status: *approval", "status: !custom approved"):
            with self.subTest(status=status):
                self.path.write_text(f'''entries:
  - source_term: stack
    target_term: 栈
    {status}
    definition_or_context: test
    evidence: ["test"]
''', encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_approved_term_pairs(self.path)

    def test_nested_status_is_not_an_approval(self) -> None:
        self.path.write_text('''entries:
  - source_term: stack
    target_term: 栈
    status: proposed
    definition_or_context: test
    evidence:
      - status: approved
''', encoding="utf-8")
        self.assertEqual(load_approved_term_pairs(self.path), set())

    def test_duplicate_entries_sections_are_rejected(self) -> None:
        self.path.write_text("entries: []\nentries: []\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            load_approved_term_pairs(self.path)

    def test_plain_english_apostrophe_does_not_hide_an_inline_comment(self) -> None:
        self.path.write_text("""entries:
  - source_term: Johan's stacks # inline comment
    target_term: 约翰的栈
    status: approved
    definition_or_context: test
    evidence: ["test"]
""", encoding="utf-8")
        self.assertEqual(load_approved_term_pairs(self.path), {("Johan's stacks", "约翰的栈")})

    def test_null_or_empty_yaml_evidence_items_cannot_support_approval(self) -> None:
        for item in ("null", "false", "[]", "{}", ""):
            with self.subTest(item=item):
                self.path.write_text(f'''entries:
  - source_term: stack
    target_term: 栈
    status: approved
    definition_or_context: test
    evidence:
      - {item}
''', encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_approved_term_pairs(self.path)

    def test_duplicate_json_approval_fields_fail_closed(self) -> None:
        self.path.write_text('''{"entries": [{"source_term": "stack", "target_term": "栈",
"status": "proposed", "status": "approved", "definition_or_context": "test", "evidence": ["test"]}]}''', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate glossary field"):
            load_approved_term_pairs(self.path)


if __name__ == "__main__":
    unittest.main()
