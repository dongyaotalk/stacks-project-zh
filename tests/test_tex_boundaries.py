from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from test_workflow import make_batch_candidate, make_batch_unit
from stacks_zh.records import delimit_tex_control_word, restore_placeholders, sha256_value, stamp_unit_hashes, write_jsonl
from stacks_zh.workflow import render_batch


class TeXBoundaryTests(unittest.TestCase):
    def test_item_noindent_and_unicode_prose_are_delimited(self):
        for command in [r"\item", r"\noindent", r"\medskip"]:
            row = {"source_text": "<STRUCT_0001> text", "placeholders": {"STRUCT_0001": command}}
            for prose in ["对象", "δ", "Text"]:
                self.assertEqual(restore_placeholders(row, "<STRUCT_0001>" + prose, delimit_commands=True), command + " " + prose)

    def test_source_recovery_and_records_are_unchanged_by_default(self):
        row = {"source_text": "<STRUCT_0001> text", "placeholders": {"STRUCT_0001": r"\item"}}
        before = copy.deepcopy(row)
        self.assertEqual(restore_placeholders(row, row["source_text"]), r"\item text")
        restore_placeholders(row, "<STRUCT_0001>对象", delimit_commands=True)
        self.assertEqual(row, before)

    def test_adjacent_protected_nodes_preserve_math_and_reference(self):
        row = {"source_text": "<STRUCT_0001><STRUCT_0002><MATH_0001><REF_0001>",
               "placeholders": {"STRUCT_0001": r"\medskip", "STRUCT_0002": r"\noindent", "MATH_0001": "$x$", "REF_0001": r"\ref{test}"}}
        self.assertEqual(restore_placeholders(row, row["source_text"], delimit_commands=True), r"\medskip \noindent $x$\ref{test}")

    def test_existing_separator_and_optional_argument_remain_safe(self):
        for value in [r"\item ", "\\noindent\n", "\\noindent\r\n", "\\medskip\n\n"]:
            self.assertEqual(delimit_tex_control_word(value), value)
        row = {"source_text": "<STRUCT_0001>[A] text", "placeholders": {"STRUCT_0001": r"\item"}}
        self.assertEqual(restore_placeholders(row, row["source_text"], delimit_commands=True), r"\item [A] text")

    def test_control_symbols_and_complete_math_are_not_changed(self):
        for value in [r"\\item", r"\\", r"\%", r"\ ", r"$\alpha$", r"\ref{x}", r"\emph{x}", "plain"]:
            self.assertEqual(delimit_tex_control_word(value), value)
        self.assertEqual(delimit_tex_control_word(r"\\\item"), r"\\\item ")

    def test_render_pipeline_delimits_body_and_prefix_without_changing_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row = make_batch_unit("tag:ABCD:p001")
            row["source_text"] = "<STRUCT_0001> Source."
            row["placeholders"] = {"STRUCT_0001": r"\noindent"}
            row["render"]["prefix"] = r"\medskip"
            row = stamp_unit_hashes(row)
            output = make_batch_candidate(row)
            output["translation"] = "<STRUCT_0001>对象。"
            output["translation_hash"] = sha256_value(output["translation"])
            original = copy.deepcopy((row, output))
            write_jsonl(root / "units.jsonl", [row]); write_jsonl(root / "candidates.jsonl", [output])
            (root / "upstream.lock").write_text(f'commit = "{row["source_commit"]}"\n')
            render_batch(root / "units.jsonl", root / "candidates.jsonl", root / "upstream.lock", root / "preview", "test", "Test")
            tex = (root / "preview/chapters/test.tex").read_text()
            self.assertIn(r"\medskip \noindent 对象。", tex)
            self.assertEqual((row, output), original)
