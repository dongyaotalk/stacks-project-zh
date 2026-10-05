from __future__ import annotations

import copy
import unittest

from test_workflow import make_batch_candidate, make_batch_unit
from stacks_zh.records import sha256_value, stamp_unit_hashes, validate_records


def batch(two=False):
    row = make_batch_unit("tag:ABCD:definition")
    row["source_text"] = "<TEXTITOPEN_0001>Vertical<TEXTITCLOSE_0001> composition."
    row["placeholders"] = {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}"}
    if two:
        row["source_text"] += " <TEXTITOPEN_0002>Vertical<TEXTITCLOSE_0002> composition."
        row["placeholders"].update({"TEXTITOPEN_0002": r"{\it ", "TEXTITCLOSE_0002": "}"})
    row = stamp_unit_hashes(row)
    output = make_batch_candidate(row)
    output["translation"] = "<TEXTITOPEN_0001>垂直<TEXTITCLOSE_0001>复合（Vertical composition）。"
    if two:
        output["translation"] += "<TEXTITOPEN_0002>垂直<TEXTITCLOSE_0002>复合（Vertical composition）。"
    output["translation_hash"] = sha256_value(output["translation"])
    output["term_occurrences"] = [{"source_term": "Vertical composition", "target_term": "垂直复合"}]
    output["unknown_terms"] = [{"source_term": "Vertical composition", "target_term": "垂直复合", "context": "Proposed wording for this source definition."}]
    output["term_status"] = "DECISION_REQUIRED"
    output["stage"] = "STRUCTURE_OK"
    return row, output


class TermDisplayTests(unittest.TestCase):
    def test_bilingual_term_crossing_font_boundary_passes(self):
        row, output = batch()
        self.assertEqual(validate_records([row], [output], row["source_commit"]), [])

    def test_legacy_target_spelling_with_font_token_still_passes(self):
        row, output = batch()
        for item in output["term_occurrences"] + output["unknown_terms"]:
            item["target_term"] = "垂直<TEXTITCLOSE_0001>复合"
        self.assertEqual(validate_records([row], [output], row["source_commit"]), [])

    def test_missing_and_reordered_format_tokens_still_fail(self):
        row, output = batch()
        for text in [output["translation"].replace("<TEXTITCLOSE_0001>", ""),
                     "<TEXTITCLOSE_0001><TEXTITOPEN_0001>垂直复合（Vertical composition）。"]:
            changed = copy.deepcopy(output)
            changed["translation"] = text; changed["translation_hash"] = sha256_value(text)
            self.assertTrue(any("protected placeholders" in error for error in validate_records([row], [changed], row["source_commit"])))

    def test_duplicate_visible_occurrence_requires_two_records(self):
        row, output = batch(True)
        self.assertTrue(any("count mismatch" in error for error in validate_records([row], [output], row["source_commit"])))
        output["term_occurrences"] *= 2
        self.assertEqual(validate_records([row], [output], row["source_commit"]), [])

    def test_formula_reference_and_footnote_boundaries_are_not_transparent(self):
        for name, payload in [("MATH_0001", "$x$"), ("REF_0001", r"\ref{label}"),
                              ("FOOTNOTEOPEN_0001", r"\footnote{")]:
            row, output = batch()
            row["source_text"] += f" <{name}>"
            row["placeholders"][name] = payload; row = stamp_unit_hashes(row)
            output["source_text_hash"] = row["source_text_hash"]
            # The exact placeholder order remains valid, but the visible term
            # is interrupted by a semantically significant protected node.
            output["translation"] = f"<TEXTITOPEN_0001>垂直<TEXTITCLOSE_0001><{name}>复合（Vertical composition）。"
            output["translation_hash"] = sha256_value(output["translation"])
            self.assertTrue(any("missing or out of order" in error for error in validate_records([row], [output], row["source_commit"])))

    def test_unexplained_english_remains_a_hard_error(self):
        row, output = batch()
        output["translation"] += " omitted"
        output["translation_hash"] = sha256_value(output["translation"])
        self.assertTrue(any("unexplained English residue" in error for error in validate_records([row], [output], row["source_commit"])))

    def test_font_named_token_with_semantic_payload_is_not_ignored(self):
        for payload in ["$x$", r"\ref{label}", r"\footnote{", r"{\it $x$"]:
            row, output = batch()
            row["placeholders"]["TEXTITOPEN_0001"] = payload; row = stamp_unit_hashes(row)
            output["source_text_hash"] = row["source_text_hash"]
            output["translation"] = "垂直<TEXTITOPEN_0001><TEXTITCLOSE_0001>复合（Vertical composition）。"
            output["translation_hash"] = sha256_value(output["translation"])
            self.assertTrue(any("missing or out of order" in error for error in validate_records([row], [output], row["source_commit"])))
