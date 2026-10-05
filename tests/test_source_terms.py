from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.records import RecordError, stamp_unit_hashes, write_jsonl
from stacks_zh.source_terms import audit_repository_terms, load_catalog, source_inventory, source_tex_hash, validate_source_terms

COMMIT = "b" * 40


def unit(text="A category has objects and morphisms.", placeholders=None, kind="definition"):
    return stamp_unit_hashes({"schema_version": 1, "unit_id": "tag:ABCD:definition", "chapter": "test",
        "parent_tag": "ABCD", "node_kind": kind, "risk_level": "R3", "source_commit": COMMIT,
        "source_status": "CURRENT", "source_text": text, "placeholders": placeholders or {},
        "render": {"prefix": "", "suffix": "\n"}})


def catalog(row=None):
    row = row or unit()
    return {"schema_version": 1, "source_commit": COMMIT, "nonmathematical_declarations": {},
        "terms": [{"id": form, "forms": [form], "chapters": [],
                   "evidence": [{"chapter": "test", "unit_id": row["unit_id"], "source_term": form,
                                 "source_tex_hash": source_tex_hash(row)}]}
                  for form in ["category", "objects", "morphisms"]]}


def candidate(terms=None):
    terms = terms if terms is not None else [("category", "范畴"), ("objects", "对象"), ("morphisms", "态射")]
    return {"unit_id": "tag:ABCD:definition", "translation": "，".join(f"{zh}（{en}）" for en, zh in terms),
            "term_occurrences": [{"source_term": en, "target_term": zh} for en, zh in terms],
            "unknown_terms": [{"source_term": en, "target_term": zh, "context": "Source definition; proposed rendering pending glossary decision."} for en, zh in terms],
            "term_status": "DECISION_REQUIRED"}


class SourceTermsTests(unittest.TestCase):
    def test_inventory_ignores_candidate_metadata_and_binds_source(self):
        row = unit()
        inventory = source_inventory(row, catalog())
        self.assertEqual([x["source_term"] for x in inventory["occurrences"]], ["category", "objects", "morphisms"])
        self.assertEqual(inventory["source_text_hash"], row["source_text_hash"])
        self.assertTrue(inventory["catalog_hash"].startswith("sha256:"))
        self.assertTrue(validate_source_terms(row, candidate([]), catalog()))

    def test_full_pending_coverage_passes_without_mutation(self):
        values = (unit(), candidate(), catalog())
        before = copy.deepcopy(values)
        self.assertEqual(validate_source_terms(*values), [])
        self.assertEqual(values, before)

    def test_each_deleted_or_underreported_occurrence_fails(self):
        for index in range(3):
            changed = candidate()
            del changed["term_occurrences"][index]
            self.assertTrue(validate_source_terms(unit(), changed, catalog()))
        row = unit("A category and another category.")
        self.assertTrue(validate_source_terms(row, candidate([("category", "范畴")]), catalog(row)))
        self.assertEqual(validate_source_terms(row, candidate([("category", "范畴")] * 2), catalog(row)), [])

    def test_extra_claim_and_repeated_display_fail(self):
        changed = candidate()
        changed["term_occurrences"].append(changed["term_occurrences"][0])
        errors = validate_source_terms(unit(), changed, catalog())
        self.assertTrue(any("unused exact source" in error for error in errors))
        self.assertTrue(any("bilingual display" in error for error in errors))

    def test_malformed_candidate_fields_fail_without_crashing(self):
        for field, value in [("unknown_terms", None), ("translation", None),
                             ("term_occurrences", [None]),
                             ("unknown_terms", [{"source_term": [], "target_term": {}, "context": "fake"}])]:
            output = candidate(); output[field] = value
            self.assertTrue(validate_source_terms(unit(), output, catalog()))

    def test_source_case_plural_and_root_cannot_be_rewritten(self):
        for form in ["Objects", "object", "morphism"]:
            terms = [("category", "范畴"), (form, "对象"), ("morphisms", "态射")]
            self.assertTrue(validate_source_terms(unit(), candidate(terms), catalog()))

    def test_missing_display_and_fake_clear_fail(self):
        changed = candidate()
        changed["translation"] = "范畴、对象和态射。"
        self.assertTrue(validate_source_terms(unit(), changed, catalog()))
        changed = candidate()
        changed["term_status"] = "CLEAR"
        changed["unknown_terms"] = []
        self.assertTrue(validate_source_terms(unit(), changed, catalog()))

    def test_whole_sentence_cannot_stand_in_for_individual_terms(self):
        output = candidate([("A category has objects and morphisms", "一整句")])
        self.assertTrue(any("coverage" in error for error in validate_source_terms(unit(), output, catalog())))

    def test_only_actual_supplied_approvals_allow_clear(self):
        changed = candidate()
        changed["term_status"] = "CLEAR"
        changed["unknown_terms"] = []
        approved = {(t["source_term"], t["target_term"]) for t in changed["term_occurrences"]}
        self.assertEqual(validate_source_terms(unit(), changed, catalog(), approved), [])
        approved.remove(("objects", "对象"))
        self.assertTrue(validate_source_terms(unit(), changed, catalog(), approved))

    def test_formatting_is_transparent_but_formula_remains_opaque(self):
        row = unit("A <TEXTITOPEN_0001>category<TEXTITCLOSE_0001> <MATH_0001>.",
                   {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}", "MATH_0001": r"$\text{objects and morphisms}$"})
        self.assertEqual([x["source_term"] for x in source_inventory(row, catalog(row))["occurrences"]], ["category"])
        self.assertEqual(validate_source_terms(row, candidate([("category", "范畴")]), catalog(row)), [])

    def test_new_definition_declaration_requires_coverage_without_catalog_entry(self):
        row = unit("A <TEXTITOPEN_0001>frobulator<TEXTITCLOSE_0001> is defined here. The frobulator is unique.",
                   {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}"})
        self.assertEqual([x["source_term"] for x in source_inventory(row, catalog(row))["occurrences"]], ["frobulator"] * 2)
        self.assertTrue(validate_source_terms(row, candidate([]), catalog(row)))
        self.assertEqual(validate_source_terms(row, candidate([("frobulator", "新概念")] * 2), catalog(row)), [])

    def test_editorial_italics_are_not_automatically_math_definitions(self):
        row = unit("Read <EMPHOPEN_0001>The Book<EMPHCLOSE_0001>.", {"EMPHOPEN_0001": r"\emph{", "EMPHCLOSE_0001": "}"}, "paragraph")
        self.assertEqual(source_inventory(row, catalog(row))["occurrences"], [])

    def test_italic_imperatives_do_not_name_terms_but_catalog_coverage_is_required(self):
        for imperative in ["let", "Assume", "suppose"]:
            with self.subTest(imperative=imperative):
                row = unit(f"We will say ``<TEXTITOPEN_0001>{imperative} <MATH_0001> be the category associated to <MATH_0002><TEXTITCLOSE_0001>''.",
                           {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}",
                            "MATH_0001": "$C$", "MATH_0002": "$D$"}, "paragraph")
                self.assertEqual([x["source_term"] for x in source_inventory(row, catalog(row))["occurrences"]], ["category"])
                self.assertTrue(validate_source_terms(row, candidate([]), catalog(row)))
                self.assertEqual(validate_source_terms(row, candidate([("category", "范畴")]), catalog(row)), [])

    def test_quoted_usage_does_not_disable_other_new_definitions(self):
        row = unit("A <TEXTITOPEN_0001>frobulator<TEXTITCLOSE_0001> has a name. We say ``<TEXTITOPEN_0002>let <MATH_0001> be a category<TEXTITCLOSE_0002>''. The frobulator is unique.",
                   {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}",
                    "TEXTITOPEN_0002": r"{\it ", "TEXTITCLOSE_0002": "}", "MATH_0001": "$C$"})
        self.assertEqual([x["source_term"] for x in source_inventory(row, catalog(row))["occurrences"]], ["frobulator", "category", "frobulator"])
        self.assertTrue(validate_source_terms(row, candidate([("category", "范畴")]), catalog(row)))

    def test_say_still_introduces_a_short_uncatalogued_term(self):
        row = unit("We say <EMPHOPEN_0001>frobulator<EMPHCLOSE_0001> in this setting.",
                   {"EMPHOPEN_0001": r"\emph{", "EMPHCLOSE_0001": "}"}, "paragraph")
        self.assertEqual([x["source_term"] for x in source_inventory(row, catalog(row))["occurrences"]], ["frobulator"])
        self.assertTrue(validate_source_terms(row, candidate([]), catalog(row)))

    def test_nonfont_payload_cannot_create_an_italic_declaration(self):
        row = unit("We call <TEXTITOPEN_0001>frobulator<TEXTITCLOSE_0001> here.",
                   {"TEXTITOPEN_0001": "$x$", "TEXTITCLOSE_0001": "}"})
        self.assertEqual(source_inventory(row, catalog(row))["occurrences"], [])

    def test_relation_phrase_keeps_its_preposition_without_math_inside(self):
        row = unit("We say it <TEXTITOPEN_0001>lies over<TEXTITCLOSE_0001> the point.", {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}"})
        self.assertEqual([x["source_term"] for x in source_inventory(row, catalog(row))["occurrences"]], ["lies over"])

    def test_term_display_can_cross_font_wrapper_but_not_footnote_boundary(self):
        row = unit("<TEXTITOPEN_0001>Vertical<TEXTITCLOSE_0001> composition.", {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}"})
        output = candidate([("Vertical composition", "垂直复合")])
        output["translation"] = "<TEXTITOPEN_0001>垂直<TEXTITCLOSE_0001>复合（Vertical composition）。"
        scope = catalog(row); scope["terms"].append({"id": "vertical-composition", "forms": ["vertical composition"], "chapters": [], "evidence": []})
        self.assertEqual(validate_source_terms(row, output, scope), [])
        row = unit("Vertical<FOOTNOTEOPEN_0001>composition<FOOTNOTECLOSE_0001>.", {"FOOTNOTEOPEN_0001": r"\footnote{", "FOOTNOTECLOSE_0001": "}"})
        scope = catalog(row); scope["terms"].append({"id": "vertical-composition", "forms": ["vertical composition"], "chapters": [], "evidence": []})
        self.assertEqual(source_inventory(row, scope)["occurrences"], [])

    def test_articles_and_target_reordering_preserve_exact_english_source(self):
        self.assertEqual(validate_source_terms(unit(), candidate([("morphisms", "态射"), ("objects", "对象"), ("A category", "一个范畴")]), catalog()), [])

    def test_longest_compound_and_word_boundaries(self):
        row = unit("A fibre product and another product; categorylike is ordinary.")
        scope = catalog(row)
        scope["terms"] += [{"id": form.replace(" ", "-"), "forms": [form], "chapters": [], "evidence": []}
                           for form in ["product", "fibre product"]]
        self.assertEqual([x["source_term"] for x in source_inventory(row, scope)["occurrences"]], ["fibre product", "product"])
        self.assertEqual(validate_source_terms(row, candidate([("product", "积"), ("fibre product", "纤维积")]), scope), [])

    def test_changed_source_cannot_keep_inventory_hashes(self):
        row = unit()
        row["source_text"] += " More objects."
        with self.assertRaisesRegex(RecordError, "stale unit hashes"):
            source_inventory(row, catalog())

    def test_catalog_duplicates_and_missing_source_evidence_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            scope = catalog()
            scope["terms"].append(copy.deepcopy(scope["terms"][0]))
            (root / "config/source-terms.json").write_text(json.dumps(scope))
            with self.assertRaisesRegex(RecordError, "duplicate"):
                load_catalog(root)
            scope = catalog()
            scope["terms"][0]["evidence"] = []
            (root / "config/source-terms.json").write_text(json.dumps(scope))
            with self.assertRaisesRegex(RecordError, "evidence"):
                load_catalog(root)

    def test_repository_checks_source_evidence_and_full_candidate_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config/source-terms.json").write_text(json.dumps(catalog()))
            (root / "config/glossary.yml").write_text("entries: []\n")
            (root / "upstream.lock").write_text(f'commit = "{COMMIT}"\n')
            write_jsonl(root / "translation-data/units/test.jsonl", [unit()])
            write_jsonl(root / "translation-data/candidates/lane/test.jsonl", [candidate()])
            report, errors = audit_repository_terms(root)
            self.assertEqual(errors, [])
            self.assertEqual((report["unit_count"], report["batch_count"]), (1, 1))
            # Coordinates can change, while exact source TeX remains evidence.
            changed = unit(); changed["unit_id"] = "tag:NEW1:definition"
            output = candidate(); output["unit_id"] = changed["unit_id"]
            write_jsonl(root / "translation-data/units/test.jsonl", [changed])
            write_jsonl(root / "translation-data/candidates/lane/test.jsonl", [output])
            self.assertEqual(audit_repository_terms(root)[1], [])
            write_jsonl(root / "translation-data/candidates/lane/test.jsonl", [output, output])
            self.assertTrue(any("exactly cover" in error for error in audit_repository_terms(root)[1]))
            (root / "translation-data/candidates/lane/test.jsonl").unlink()
            self.assertTrue(any("no candidate coverage" in error for error in audit_repository_terms(root)[1]))
            changed = unit("An unrelated English sentence.")
            write_jsonl(root / "translation-data/units/test.jsonl", [changed])
            self.assertTrue(any("catalog evidence" in error for error in audit_repository_terms(root)[1]))
