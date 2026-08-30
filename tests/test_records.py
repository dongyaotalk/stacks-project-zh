from __future__ import annotations

import unittest

from stacks_zh.records import (
    restore_placeholders,
    sha256_value,
    stamp_unit_hashes,
    validate_records,
)
from stacks_zh.schema_validation import validate_named_schema


SOURCE_COMMIT = "a" * 40


def make_unit() -> dict[str, object]:
    return stamp_unit_hashes(
        {
            "schema_version": 1,
            "unit_id": "tag:TEST:p001",
            "parent_tag": "TEST",
            "chapter": "test",
            "node_kind": "paragraph",
            "risk_level": "R1",
            "source_commit": SOURCE_COMMIT,
            "source_text": "See <CITE_0001>.",
            "source_status": "CURRENT",
            "placeholders": {"CITE_0001": "\\cite{test}"},
            "render": {"prefix": "\\noindent\n", "suffix": "\n"},
        }
    )


def make_candidate(unit: dict[str, object]) -> dict[str, object]:
    context = {"instructions": "translator-v1", "unit_ids": [unit["unit_id"]]}
    return {
        "schema_version": 1,
        "unit_id": unit["unit_id"],
        "source_commit": SOURCE_COMMIT,
        "source_text_hash": unit["source_text_hash"],
        "model_id": "test/model-snapshot",
        "model_lane": "test",
        "reasoning_effort": "not_exposed",
        "prompt_version": "translator-v1",
        "glossary_revision": "git:test",
        "context": context,
        "context_hash": sha256_value(context),
        "translation": "见 <CITE_0001>。",
        "allowed_english": [],
        "term_occurrences": [],
        "unknown_terms": [],
        "notes": [],
        "stage": "STRUCTURE_OK",
        "source_status": "CURRENT",
        "qa_status": "PASS",
        "term_status": "CLEAR",
        "publication_status": "CANDIDATE",
        "created_at": "2026-08-25T00:00:00+08:00",
    }


def make_grouped_bold_unit() -> dict[str, object]:
    unit = make_unit()
    unit["source_text"] = (
        "There does <FORMAT_0001>not<FORMAT_0002> exist <MATH_0001>."
    )
    unit["placeholders"] = {
        "FORMAT_0001": "{\\bf ",
        "FORMAT_0002": "}",
        "MATH_0001": "$x$",
    }
    return stamp_unit_hashes(unit)


class RecordValidationTests(unittest.TestCase):
    def test_grouped_bold_negation_restores_without_changing_scope(self) -> None:
        unit = make_grouped_bold_unit()
        candidate = make_candidate(unit)
        candidate["translation"] = "<FORMAT_0001>不<FORMAT_0002>存在<MATH_0001>。"

        self.assertEqual(validate_records([unit], [candidate], SOURCE_COMMIT), [])
        self.assertEqual(
            restore_placeholders(unit, unit["source_text"]),
            "There does {\\bf not} exist $x$.",
        )
        self.assertEqual(
            restore_placeholders(unit, candidate["translation"]),
            "{\\bf 不}存在$x$。",
        )

    def test_grouped_bold_missing_wrapper_is_rejected(self) -> None:
        unit = make_grouped_bold_unit()
        for translation in (
            "不<FORMAT_0002>存在<MATH_0001>。",
            "<FORMAT_0001>不存在<MATH_0001>。",
        ):
            with self.subTest(translation=translation):
                candidate = make_candidate(unit)
                candidate["translation"] = translation
                errors = validate_records([unit], [candidate], SOURCE_COMMIT)
                self.assertTrue(any("placeholders changed" in error for error in errors))

    def test_grouped_bold_reordered_wrapper_or_adjacent_math_is_rejected(self) -> None:
        unit = make_grouped_bold_unit()
        for translation in (
            "<FORMAT_0002>不<FORMAT_0001>存在<MATH_0001>。",
            "<FORMAT_0001>不存在<MATH_0001><FORMAT_0002>。",
        ):
            with self.subTest(translation=translation):
                candidate = make_candidate(unit)
                candidate["translation"] = translation
                errors = validate_records([unit], [candidate], SOURCE_COMMIT)
                self.assertTrue(
                    any("placeholders changed or reordered" in error for error in errors)
                )

    def test_candidate_schema_rejects_unknown_fields(self) -> None:
        unit = make_unit()
        candidate = make_candidate(unit)
        candidate.update(
            {
                "schema_version": 2,
                "harness_id": "test",
                "harness_version": "test",
                "model_record_id": "provider:model:declared",
                "model_snapshot": None,
                "model_identity_confidence": "declared",
                "run_id": "run-test",
                "translation_hash": sha256_value(candidate["translation"]),
                "unexpected": True,
            }
        )
        errors = validate_records([unit], [candidate], SOURCE_COMMIT)
        self.assertTrue(any("unexpected property 'unexpected'" in error for error in errors))

    def test_translator_output_schema_rejects_missing_term_occurrences(self) -> None:
        errors = validate_named_schema(
            {
                "unit_id": "tag:TEST:p001",
                "translation": "测试。",
                "allowed_english": [],
                "unknown_terms": [],
                "notes": [],
            },
            "translator-output.schema.json",
            "draft",
        )
        self.assertTrue(any("missing required property 'term_occurrences'" in error for error in errors))

    def test_valid_candidate_passes(self) -> None:
        unit = make_unit()
        self.assertEqual(validate_records([unit], [make_candidate(unit)], SOURCE_COMMIT), [])

    def test_placeholder_change_fails(self) -> None:
        unit = make_unit()
        candidate = make_candidate(unit)
        candidate["translation"] = "见 <REF_0001>。"
        errors = validate_records([unit], [candidate], SOURCE_COMMIT)
        self.assertTrue(any("placeholders changed" in error for error in errors))

    def test_placeholder_map_key_order_is_not_semantic(self) -> None:
        unit = stamp_unit_hashes(
            {
                "schema_version": 1,
                "unit_id": "tag:TEST:p002",
                "parent_tag": "TEST",
                "chapter": "test",
                "node_kind": "paragraph",
                "risk_level": "R1",
                "source_commit": SOURCE_COMMIT,
                "source_text": "See <REF_0002> and <REF_0001>.",
                "source_status": "CURRENT",
                "placeholders": {
                    "REF_0001": "\\ref{one}",
                    "REF_0002": "\\ref{two}",
                },
                "render": {"prefix": "", "suffix": "\n"},
            }
        )
        context = {"instructions": "translator-v1", "unit_ids": [unit["unit_id"]]}
        candidate = make_candidate(unit)
        candidate["context"] = context
        candidate["context_hash"] = sha256_value(context)
        candidate["translation"] = "见 <REF_0002> 和 <REF_0001>。"
        self.assertEqual(validate_records([unit], [candidate], SOURCE_COMMIT), [])

    def test_unknown_term_blocks_term_ok(self) -> None:
        unit = make_unit()
        candidate = make_candidate(unit)
        candidate["stage"] = "TERM_OK"
        candidate["term_status"] = "DECISION_REQUIRED"
        candidate["translation"] = "栈（stack）见 <CITE_0001>。"
        candidate["term_occurrences"] = [
            {"source_term": "stack", "target_term": "栈"}
        ]
        candidate["unknown_terms"] = [
            {"source_term": "stack", "target_term": "栈", "context": "test"}
        ]
        errors = validate_records([unit], [candidate], SOURCE_COMMIT)
        self.assertTrue(any("unresolved terms prevent" in error for error in errors))

    def test_bilingual_term_is_removed_from_english_residue(self) -> None:
        unit = make_unit()
        candidate = make_candidate(unit)
        candidate["translation"] = "代数栈（algebraic stack）见 <CITE_0001>。"
        candidate["term_occurrences"] = [
            {"source_term": "algebraic stack", "target_term": "代数栈"}
        ]
        self.assertEqual(validate_records([unit], [candidate], SOURCE_COMMIT), [])

    def test_repeated_term_requires_repeated_record(self) -> None:
        unit = make_unit()
        candidate = make_candidate(unit)
        candidate["translation"] = (
            "代数栈（algebraic stack）与代数栈（algebraic stack）见 <CITE_0001>。"
        )
        candidate["term_occurrences"] = [
            {"source_term": "algebraic stack", "target_term": "代数栈"}
        ]
        errors = validate_records([unit], [candidate], SOURCE_COMMIT)
        self.assertTrue(any("bilingual term count mismatch" in error for error in errors))

    def test_bilingual_term_may_contain_protected_accent_placeholder(self) -> None:
        unit = stamp_unit_hashes(
            {
                "schema_version": 1,
                "unit_id": "tag:TEST:p003",
                "parent_tag": "TEST",
                "chapter": "test",
                "node_kind": "paragraph",
                "risk_level": "R1",
                "source_commit": SOURCE_COMMIT,
                "source_text": "<LATIN_0001> morphisms, see <CITE_0001>.",
                "source_status": "CURRENT",
                "placeholders": {
                    "LATIN_0001": "\\'etale",
                    "CITE_0001": "\\cite{test}",
                },
                "render": {"prefix": "", "suffix": "\n"},
            }
        )
        candidate = make_candidate(unit)
        context = {"instructions": "translator-v2", "unit_ids": [unit["unit_id"]]}
        candidate["context"] = context
        candidate["context_hash"] = sha256_value(context)
        candidate["translation"] = "平展态射（<LATIN_0001> morphisms），见 <CITE_0001>。"
        candidate["term_occurrences"] = [
            {"source_term": "<LATIN_0001> morphisms", "target_term": "平展态射"}
        ]
        self.assertEqual(validate_records([unit], [candidate], SOURCE_COMMIT), [])

    def test_model_cannot_claim_human_review(self) -> None:
        unit = make_unit()
        candidate = make_candidate(unit)
        candidate["stage"] = "LANGUAGE_REVIEWED"
        errors = validate_records([unit], [candidate], SOURCE_COMMIT)
        self.assertTrue(any("cannot claim stage" in error for error in errors))

    def test_candidate_cannot_claim_unimplemented_critic_gate(self) -> None:
        unit = make_unit()
        candidate = make_candidate(unit)
        candidate["stage"] = "CRITIC_OK"
        errors = validate_records([unit], [candidate], SOURCE_COMMIT)
        self.assertTrue(any("CRITIC_OK is unavailable" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
