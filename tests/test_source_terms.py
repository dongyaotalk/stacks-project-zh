from __future__ import annotations

import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.records import RecordError, stamp_unit_hashes, write_jsonl, term_display_text, validate_tex_controls
from stacks_zh.source_terms import audit_repository_terms, load_catalog, source_inventory, source_projection, source_tex_hash, validate_source_terms

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
    def test_verified_text_accents_expose_whole_words_without_changing_protected_bytes(self):
        for payload, visible in [(r"\'e", 'é'), (r"\'{e}", 'é'), (r"\'E", 'É'),
                                 (r'\"o', 'ö'), (r'\"e', 'ë'), (r"\'a", 'á'), (r'\`a', 'à')]:
            row = unit('An <ACCENT_0001>tale morphism.', {'ACCENT_0001': payload}, 'paragraph')
            words = catalog(row);words['terms'] = [{'id': 'accent-word', 'forms': [visible+'tale'], 'chapters': [], 'evidence': []}]
            output = candidate([(visible+'tale', '平展')]);output['translation']='平展（<ACCENT_0001>tale）。'
            before=copy.deepcopy((row,output,words))
            with self.subTest(payload=payload):
                self.assertEqual(source_projection(row)[0], 'An '+visible+'tale morphism.')
                self.assertTrue(validate_source_terms(row, candidate([]), words))
                self.assertEqual(validate_source_terms(row,output,words), [])
                self.assertEqual(validate_tex_controls(row,output), [])
                self.assertEqual((row,output,words), before)

    def test_legacy_token_spelling_of_a_text_accent_keeps_pending_source_coverage(self):
        row=unit('An <ACCENT_0001>tale morphism.', {'ACCENT_0001': r"\'e"}, 'paragraph')
        words=catalog(row);words['terms']=[{'id':'etale','forms':['étale'],'chapters':[],'evidence':[]}]
        output=candidate([('<ACCENT_0001>tale','平展')])
        self.assertEqual(validate_source_terms(row,output,words), [])
        self.assertEqual(term_display_text(output['translation'],row['placeholders']),'平展（étale）')

    def test_unverified_accents_and_math_nodes_remain_opaque(self):
        for payload in [r"\'ef", r"\'{ef}", r"\'e\input{x}", r"\unknown{e}", '$e$', r"\'{$e$}"]:
            row=unit('<ACCENT_0001>tale.', {'ACCENT_0001':payload}, 'paragraph')
            with self.subTest(payload=payload):
                self.assertEqual(source_projection(row)[0],'<ACCENT_0001>tale.')
                self.assertEqual(term_display_text(row['source_text'],row['placeholders']),row['source_text'])
        row=unit('<MATH_0001>.', {'MATH_0001':r"$\text{\'etale}$"}, 'paragraph')
        self.assertEqual(source_projection(row)[0],'<MATH_0001>.')

    def test_equivalence_class_requires_the_whole_singular_and_plural_concept(self):
        row = unit('An equivalence class, equivalence classes, a class and an equivalence.', kind='paragraph')
        entry = copy.deepcopy(next(item for item in json.loads(
            (Path(__file__).resolve().parents[1] / 'config/source-terms.json').read_text())['terms']
            if item['id'] == 'equivalence-class'))
        self.assertEqual(entry['forms'], ['equivalence class', 'equivalence classes'])
        self.assertEqual(entry['chapters'], [])
        words = catalog(row)
        words['terms'] = [{'id': term, 'forms': forms, 'chapters': [],
            'evidence': [{'chapter': 'test', 'unit_id': row['unit_id'],
                          'source_term': term, 'source_tex_hash': source_tex_hash(row)}]}
            for term, forms in [('equivalence', ['equivalence']), ('class', ['class', 'classes'])]]
        partial = candidate([('equivalence', '等价'), ('class', '类'),
                             ('equivalence', '等价'), ('classes', '类'),
                             ('class', '类'), ('equivalence', '等价')])
        self.assertEqual(validate_source_terms(row, partial, words), [])
        words['terms'].append(entry)
        self.assertEqual([x['source_term'] for x in source_inventory(row, words)['occurrences']],
                         ['equivalence class', 'equivalence classes', 'class', 'equivalence'])
        errors = validate_source_terms(row, partial, words)
        self.assertTrue(any('coverage' in x and 'equivalence class' in x for x in errors))
        complete = candidate([('equivalence class', '等价类'), ('equivalence classes', '等价类'),
                              ('class', '类'), ('equivalence', '等价')])
        before = copy.deepcopy((row, complete, words))
        self.assertEqual(validate_source_terms(row, complete, words), [])
        self.assertEqual((row, complete, words), before)
        title = unit('Equivalence classes', kind='section_title')
        self.assertEqual(validate_source_terms(title, candidate([('Equivalence classes', '等价类')]), words), [])

    def test_equivalence_class_preserves_case_multiplicity_pending_and_math_opacity(self):
        row = unit('Equivalence classes and equivalence class and equivalence classes.', kind='paragraph')
        entry = copy.deepcopy(next(item for item in json.loads(
            (Path(__file__).resolve().parents[1] / 'config/source-terms.json').read_text())['terms']
            if item['id'] == 'equivalence-class'))
        words = catalog(row)
        words['terms'] = [entry]
        good = [('Equivalence classes', '等价类'), ('equivalence class', '等价类'),
                ('equivalence classes', '等价类')]
        self.assertEqual(validate_source_terms(row, candidate(good), words), [])
        for terms in [good[1:], [good[0], good[1]], [*good, good[2]],
                      [('equivalence classes', '等价类'), *good[1:]],
                      [good[0], ('equivalence classes', '等价类'), good[2]],
                      [('Equivalence classes and equivalence class and equivalence classes', '一整句')]]:
            with self.subTest(terms=terms):
                self.assertTrue(validate_source_terms(row, candidate(terms), words))
        missing_pending = candidate(good)
        missing_pending['unknown_terms'].pop(0)
        self.assertTrue(any('pending' in x for x in validate_source_terms(row, missing_pending, words)))
        hidden = unit('An equivalence class and <MATH_0001>.',
                      {'MATH_0001': r'$\text{equivalence classes}$'}, kind='paragraph')
        self.assertEqual([x['source_term'] for x in source_inventory(hidden, words)['occurrences']],
                         ['equivalence class'])

    def test_functor_of_points_title_and_plain_prose_require_the_complete_compound(self):
        row = unit('Functor of points. A functor of points is a functor.', kind='paragraph')
        entry = copy.deepcopy(next(item for item in json.loads(
            (Path(__file__).resolve().parents[1] / 'config/source-terms.json').read_text())['terms']
            if item['id'] == 'functor-of-points'))
        self.assertEqual(entry['forms'], ['functor of points'])
        self.assertEqual(entry['chapters'], [])
        words = catalog(row)
        words['terms'] = [{'id': 'functor', 'forms': ['functor'], 'chapters': [],
            'evidence': [{'chapter': 'test', 'unit_id': row['unit_id'],
                          'source_term': 'functor', 'source_tex_hash': source_tex_hash(row)}]}]
        partial = candidate([('Functor', '函子'), ('functor', '函子'), ('functor', '函子')])
        self.assertEqual(validate_source_terms(row, partial, words), [])
        words['terms'].append(entry)
        self.assertEqual([item['source_term'] for item in source_inventory(row, words)['occurrences']],
                         ['Functor of points', 'functor of points', 'functor'])
        errors = validate_source_terms(row, partial, words)
        self.assertTrue(any('coverage' in error and 'Functor of points' in error for error in errors))
        self.assertTrue(any('coverage' in error and 'functor of points' in error for error in errors))
        complete = candidate([('Functor of points', '点的函子'),
                              ('functor of points', '点的函子'), ('functor', '函子')])
        values = copy.deepcopy((row, complete, words))
        self.assertEqual(validate_source_terms(row, complete, words), [])
        self.assertEqual((row, complete, words), values)

    def test_complete_functor_of_points_keeps_case_counts_pending_and_math_opacity(self):
        row = unit('Functor of points. A functor of points is a functor.', kind='paragraph')
        entry = copy.deepcopy(next(item for item in json.loads(
            (Path(__file__).resolve().parents[1] / 'config/source-terms.json').read_text())['terms']
            if item['id'] == 'functor-of-points'))
        words = catalog(row)
        words['terms'] = [entry, {'id': 'functor', 'forms': ['functor'], 'chapters': [],
            'evidence': [{'chapter': 'test', 'unit_id': row['unit_id'],
                          'source_term': 'functor', 'source_tex_hash': source_tex_hash(row)}]}]
        good = [('Functor of points', '点的函子'), ('functor of points', '点的函子'), ('functor', '函子')]
        for terms in [[('functor of points', '点的函子'), *good[1:]], good[1:],
                      [good[0], good[0], good[2]],
                      [('A functor of points is a functor', '一整句')]]:
            with self.subTest(terms=terms):
                self.assertTrue(validate_source_terms(row, candidate(terms), words))
        missing_pending = candidate(good)
        missing_pending['unknown_terms'].pop(0)
        self.assertTrue(any('pending' in error for error in validate_source_terms(row, missing_pending, words)))
        hidden = unit('A functor of points and <MATH_0001>.',
                      {'MATH_0001': r'$\text{functor of points}$'}, kind='paragraph')
        self.assertEqual([item['source_term'] for item in source_inventory(hidden, words)['occurrences']],
                         ['functor of points'])

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

    def test_scoped_emphasis_defines_terms_and_requires_every_occurrence(self):
        for opening in [r'{\em ', '{ \n\t\\em\n']:
            with self.subTest(opening=opening):
                row = unit('It is called <EMPHOPEN_0001>frobulator<EMPHCLOSE_0001>. '
                           'Another frobulator has <MATH_0001>.',
                           {'EMPHOPEN_0001': opening, 'EMPHCLOSE_0001': '}',
                            'MATH_0001': r'$\text{hidden objects}$'}, 'proof')
                self.assertEqual(source_projection(row)[1], ['frobulator'])
                self.assertEqual([x['source_term'] for x in source_inventory(row, catalog(row))['occurrences']],
                                 ['frobulator', 'frobulator'])
                self.assertTrue(validate_source_terms(row, candidate([('frobulator', '新概念')]), catalog(row)))
                output = candidate([('frobulator', '新概念')] * 2)
                output['translation'] = ('<EMPHOPEN_0001>新概念（frobulator）<EMPHCLOSE_0001>；'
                                         '新概念（frobulator）<MATH_0001>。')
                self.assertEqual(validate_source_terms(row, output, catalog(row)), [])

    def test_scoped_emphasis_catalog_phrase_remains_visible(self):
        row = unit('It is called <EMPHOPEN_0001>finitely generated<EMPHCLOSE_0001>. '
                   'It is finitely generated.',
                   {'EMPHOPEN_0001': r'{\em ', 'EMPHCLOSE_0001': '}'}, 'proof')
        words = catalog(row)
        words['terms'] = [{'id': 'finitely-generated', 'forms': ['finitely generated'],
                          'chapters': [], 'evidence': [{'chapter': 'test', 'unit_id': row['unit_id'],
                          'source_term': 'finitely generated', 'source_tex_hash': source_tex_hash(row)}]}]
        self.assertEqual([x['source_term'] for x in source_inventory(row, words)['occurrences']],
                         ['finitely generated'] * 2)
        self.assertTrue(validate_source_terms(row, candidate([]), words))
        self.assertEqual(validate_source_terms(row, candidate([('finitely generated', '有限生成')] * 2), words), [])

    def test_fake_emphasis_payload_cannot_define_or_join_a_term(self):
        for opening in [r'\em ', r'{\emfoo ', r'{\em \input{x}', r'$x$']:
            with self.subTest(opening=opening):
                row = unit('It is called <EMPHOPEN_0001>frobulator<EMPHCLOSE_0001>.',
                           {'EMPHOPEN_0001': opening, 'EMPHCLOSE_0001': '}'}, 'proof')
                self.assertEqual(source_projection(row)[1], [])
                self.assertIn('<EMPHOPEN_0001>', source_projection(row)[0])
                self.assertEqual(source_inventory(row, catalog(row))['occurrences'], [])

    def test_new_definition_declaration_requires_coverage_without_catalog_entry(self):
        row = unit("A <TEXTITOPEN_0001>frobulator<TEXTITCLOSE_0001> is defined here. The frobulator is unique.",
                   {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}"})
        self.assertEqual([x["source_term"] for x in source_inventory(row, catalog(row))["occurrences"]], ["frobulator"] * 2)
        self.assertTrue(validate_source_terms(row, candidate([]), catalog(row)))
        self.assertEqual(validate_source_terms(row, candidate([("frobulator", "新概念")] * 2), catalog(row)), [])

    def test_editorial_italics_are_not_automatically_math_definitions(self):
        row = unit("Read <EMPHOPEN_0001>The Book<EMPHCLOSE_0001>.", {"EMPHOPEN_0001": r"\emph{", "EMPHCLOSE_0001": "}"}, "paragraph")
        self.assertEqual(source_inventory(row, catalog(row))["occurrences"], [])

    def test_later_definition_does_not_turn_an_earlier_emphasized_convention_into_a_term(self):
        row = unit('It is customary to take <TEXTITOPEN_0001>only colimits of systems over <MATH_0001><TEXTITCLOSE_0001>. '
                   'The colimit of the system is defined as <MATH_0002>.',
                   {'TEXTITOPEN_0001': r'{\it ', 'TEXTITCLOSE_0001': '}',
                    'MATH_0001': '$I$', 'MATH_0002': '$L$'}, 'paragraph')
        self.assertEqual(source_projection(row)[1], [])
        words = catalog(row)
        words['terms'] = [{'id': term, 'forms': forms, 'chapters': [], 'evidence': []}
                          for term, forms in [('colimit', ['colimit', 'colimits']), ('system', ['system', 'systems'])]]
        self.assertEqual([o['source_term'] for o in source_inventory(row, words)['occurrences']],
                         ['colimits', 'systems', 'colimit', 'system'])
        self.assertTrue(validate_source_terms(row, candidate([]), words))
        self.assertEqual(validate_source_terms(row, candidate([('colimits', '余极限'), ('systems', '系'),
                               ('colimit', '余极限'), ('system', '系')]), words), [])

    def test_another_sentence_call_does_not_define_an_editorial_title(self):
        row = unit('Read <EMPHOPEN_0001>The Book<EMPHCLOSE_0001>. '
                   'We call <EMPHOPEN_0002>frobulator<EMPHCLOSE_0002> a new concept.',
                   {'EMPHOPEN_0001': r'\emph{', 'EMPHCLOSE_0001': '}',
                    'EMPHOPEN_0002': r'\emph{', 'EMPHCLOSE_0002': '}'}, 'paragraph')
        self.assertEqual(source_projection(row)[1], ['frobulator'])
        self.assertEqual([o['source_term'] for o in source_inventory(row, catalog(row))['occurrences']], ['frobulator'])
        self.assertTrue(validate_source_terms(row, candidate([]), catalog(row)))

    def test_definition_signal_after_the_name_in_its_own_sentence_is_kept(self):
        row = unit('A <EMPHOPEN_0001>frobulator<EMPHCLOSE_0001> is defined by this condition. '
                   'Read <EMPHOPEN_0002>The Book<EMPHCLOSE_0002>.',
                   {'EMPHOPEN_0001': r'\emph{', 'EMPHCLOSE_0001': '}',
                    'EMPHOPEN_0002': r'\emph{', 'EMPHCLOSE_0002': '}'}, 'paragraph')
        self.assertEqual(source_projection(row)[1], ['frobulator'])

    def test_bibliography_item_description_cannot_define_the_italic_title(self):
        row = unit('<EMPHOPEN_0001>Lecture notes on stacks<EMPHCLOSE_0001> <REF_0001> '
                   '<STRUCT_0001>This course introduces stacks, first defined in its later lectures.',
                   {'EMPHOPEN_0001': r'\emph{', 'EMPHCLOSE_0001': '}',
                    'REF_0001': r'\cite{notes}', 'STRUCT_0001': r'\item'}, 'paragraph')
        self.assertEqual(source_projection(row)[1], [])

    def test_real_local_define_and_call_inflections_still_introduce_unknown_terms(self):
        for sentence in ['This paper defines a', 'We define a', 'It is defining a',
                         'The author calls it a', 'The author says it is a', 'It is said to be a']:
            row=unit(sentence+' <EMPHOPEN_0001>frobulator<EMPHCLOSE_0001>.',
                     {'EMPHOPEN_0001':r'\emph{','EMPHCLOSE_0001':'}'},'paragraph')
            with self.subTest(sentence=sentence):
                self.assertEqual(source_projection(row)[1],['frobulator'])
                self.assertTrue(validate_source_terms(row,candidate([]),catalog(row)))

    def test_definition_signals_remain_local_across_paragraph_and_footnote_boundaries(self):
        for marker, payload in [('STRUCT_0001', r'\noindent'),
                                ('FOOTNOTEOPEN_0001', r'\footnote{'),
                                ('FOOTNOTECLOSE_0001', '}')]:
            row = unit('We call this a construction. <EMPHOPEN_0001>Book title<EMPHCLOSE_0001>'
                       f'<{marker}>It is defined elsewhere.',
                       {'EMPHOPEN_0001': r'\emph{', 'EMPHCLOSE_0001': '}', marker: payload}, 'paragraph')
            with self.subTest(marker=marker):
                self.assertEqual(source_projection(row)[1], [])

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

    def test_isolated_connectors_in_math_qualified_declarations_are_not_concepts(self):
        for connector in ["of", "over", "in", "between", "with", "to", "on", "from", "OVER"]:
            with self.subTest(connector=connector):
                row = unit(f"A <TEXTITOPEN_0001>frobulator <MATH_0001> {connector} <MATH_0002><TEXTITCLOSE_0001> is defined. Another frobulator.",
                           {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}", "MATH_0001": "$X$", "MATH_0002": "$Y$"})
                before = copy.deepcopy(row)
                self.assertEqual(source_projection(row)[1], ["frobulator"])
                self.assertEqual([o["source_term"] for o in source_inventory(row, catalog(row))["occurrences"]], ["frobulator"] * 2)
                self.assertEqual(validate_source_terms(row, candidate([("frobulator", "新概念")] * 2), catalog(row)), [])
                self.assertTrue(validate_source_terms(row, candidate([]), catalog(row)))
                self.assertEqual(row, before)

    def test_relative_inertia_math_qualifiers_keep_both_real_declarations(self):
        row = unit("<TEXTITOPEN_0001>relative inertia of <MATH_0001> over <MATH_0002><TEXTITCLOSE_0001> and <TEXTITOPEN_0002>inertia fibred category <MATH_0003> of <MATH_0004><TEXTITCLOSE_0002>. Ordinary of and over are grammar.",
                   {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}", "TEXTITOPEN_0002": r"{\it ", "TEXTITCLOSE_0002": "}",
                    "MATH_0001": "$S$", "MATH_0002": "$T$", "MATH_0003": "$I$", "MATH_0004": "$S$"})
        self.assertEqual(source_projection(row)[1], ["inertia fibred category", "relative inertia"])
        expected = ["relative inertia", "inertia fibred category"]
        self.assertEqual([o["source_term"] for o in source_inventory(row, catalog(row))["occurrences"]], expected)
        self.assertTrue(validate_source_terms(row, candidate([("relative inertia", "相对惯性")]), catalog(row)))

    def test_connector_suffix_does_not_strip_internal_words_or_unlisted_prepositions(self):
        for phrase in ["leftover", "fromage", "over category", "lies under", "category of objects"]:
            with self.subTest(phrase=phrase):
                row = unit(f"We call <TEXTITOPEN_0001>{phrase} <MATH_0001><TEXTITCLOSE_0001> a name.",
                           {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}", "MATH_0001": "$X$"})
                self.assertEqual(source_projection(row)[1], [phrase])
                self.assertTrue(validate_source_terms(row, candidate([]), catalog(row)))

    def test_bare_unqualified_declaration_is_not_globally_filtered(self):
        row = unit("We say <TEXTITOPEN_0001>over<TEXTITCLOSE_0001> here.",
                   {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}"})
        self.assertEqual(source_projection(row)[1], ["over"])
        self.assertTrue(validate_source_terms(row, candidate([]), catalog(row)))

    def test_explicit_catalog_word_still_requires_coverage_after_connector_removal(self):
        row = unit("<TEXTITOPEN_0001>frobulator <MATH_0001> over <MATH_0002><TEXTITCLOSE_0001>.",
                   {"TEXTITOPEN_0001": r"{\it ", "TEXTITCLOSE_0001": "}", "MATH_0001": "$X$", "MATH_0002": "$Y$"})
        scope = catalog(row)
        scope["terms"].append({"id": "explicit-over", "forms": ["over"], "chapters": [], "evidence": []})
        self.assertEqual([o["source_term"] for o in source_inventory(row, scope)["occurrences"]], ["frobulator", "over"])
        self.assertTrue(validate_source_terms(row, candidate([("frobulator", "新概念")]), scope))

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

    def test_assignment_set_is_not_a_collection_but_nouns_are_required(self):
        forms = ["Set <MATH_0001>.", "Then we set <MATH_0001>.", "We can set <MATH_0001>.",
                 "Let us set <MATH_0001>.", "For every element <MATH_0002>, set <MATH_0001>.",
                 "Finally, set <MATH_0001>."]
        for text in forms:
            with self.subTest(text=text):
                row = unit(text, {"MATH_0001": "$S$", "MATH_0002": "$x$"})
                scope = catalog(row); scope["terms"] = [{"id":"set", "forms":["set"], "chapters":[], "evidence":[]}]
                self.assertEqual(source_inventory(row, scope)["occurrences"], [])
        row = unit("A set <MATH_0001> and the set <MATH_0002>.", {"MATH_0001":"$S$", "MATH_0002":"$T$"})
        scope = catalog(row); scope["terms"] = [{"id":"set", "forms":["set"], "chapters":[], "evidence":[]}]
        self.assertEqual([o["source_term"] for o in source_inventory(row, scope)["occurrences"]], ["set", "set"])
        self.assertTrue(validate_source_terms(row, candidate([("set", "集合")]), scope))

    def test_assignment_set_after_modal_adverb_now_and_numbered_reference(self):
        # These are the three witnessed introductions, with a genuine noun
        # immediately afterwards so skipping all occurrences cannot pass.
        introductions = ["We can now", "Now,", "To see (3) just",
                         "A sentence.) To see (3) just"]
        for introduction in introductions:
            with self.subTest(introduction=introduction):
                row = unit(introduction + " set <MATH_0001>. A set <MATH_0002>.",
                           {"MATH_0001": "$x=0$", "MATH_0002": "$S$"}, "paragraph")
                scope = catalog(row)
                scope["terms"] = [{"id":"set", "forms":["set"], "chapters":[], "evidence":[]}]
                self.assertEqual([o["source_term"] for o in source_inventory(row, scope)["occurrences"]], ["set"])
                self.assertTrue(validate_source_terms(row, candidate([]), scope))

    def test_assignment_set_new_introductions_keep_nouns_and_unsupported_syntax(self):
        texts = ["We can now consider a set <MATH_0001>.",
                 "Now, a set <MATH_0001>.",
                 "To see (3) just consider a set <MATH_0001>.",
                 "just set <MATH_0001>.", "Now set <MATH_0001>.",
                 "To see (x) just set <MATH_0001>.",
                 "We can now set <REF_0001>.",
                 "Now, set <MATH_BAD>.", "We can now set a value.",
                 "We can now sets <MATH_0001>."]
        for text in texts:
            with self.subTest(text=text):
                row = unit(text, {"MATH_0001":"$S$", "REF_0001":r"\ref{x}"}, "paragraph")
                scope = catalog(row)
                scope["terms"] = [{"id":"set", "forms":["set", "sets"], "chapters":[], "evidence":[]}]
                expected = "sets" if " sets " in text else "set"
                self.assertEqual([o["source_term"] for o in source_inventory(row, scope)["occurrences"]], [expected])

    def test_evidence_bound_exclusion_only_removes_the_named_occurrence(self):
        row = unit("A category and another category.")
        scope = catalog(row)
        scope["nonmathematical_occurrences"] = [{"chapter":"test", "unit_id":row["unit_id"], "source_term":"category",
            "source_tex_hash":source_tex_hash(row), "occurrence_index":0, "reason":"First usage is editorial in this fixture."}]
        self.assertEqual([o["source_term"] for o in source_inventory(row, scope)["occurrences"]], ["category"])
        self.assertTrue(validate_source_terms(row, candidate([]), scope))
        scope["nonmathematical_occurrences"][0]["occurrence_index"] = 2
        with self.assertRaisesRegex(RecordError, "no longer exists"):
            source_inventory(row, scope)
        scope["nonmathematical_occurrences"][0]["occurrence_index"] = -1
        with self.assertRaisesRegex(RecordError, "no longer exists"):
            source_inventory(row, scope)

    def test_exclusion_does_not_disable_mathematical_coding_examples(self):
        row = unit("Consider a category and its objects."); row["chapter"] = "coding"; row = stamp_unit_hashes(row)
        scope = catalog(row)
        scope["nonmathematical_occurrences"] = [{"chapter":"coding", "unit_id":"tag:OTHER:item", "source_term":"category",
            "source_tex_hash":"sha256:"+"0"*64, "occurrence_index":0, "reason":"Different English source."}]
        self.assertEqual([o["source_term"] for o in source_inventory(row, scope)["occurrences"]], ["category", "objects"])
        self.assertTrue(validate_source_terms(row, candidate([]), scope))

    def test_nonmathematical_chapter_keeps_literal_and_pending_candidate_checks(self):
        row = unit("A category has objects and morphisms.")
        scope = catalog(row); scope["nonmathematical_chapters"] = [{"chapter":"test", "reason":"License fixture.",
            "title_evidence":{"unit_id":"tag:TITLE:title", "source_title":"License", "source_tex_hash":"sha256:"+"0"*64}}]
        self.assertEqual(source_inventory(row, scope)["occurrences"], [])
        changed = candidate(); changed["term_status"] = "CLEAR"; changed["unknown_terms"] = []
        self.assertTrue(validate_source_terms(row, changed, scope))
        self.assertTrue(validate_source_terms(row, candidate([("invented", "伪词")]), scope))

    def test_math_splitting_remains_required_after_an_editorial_exclusion(self):
        row = unit("The proof needs splitting; a splitting of the category is defined.")
        scope = catalog(row); scope["terms"].append({"id":"splitting", "forms":["splitting"], "chapters":[], "evidence":[]})
        scope["nonmathematical_occurrences"] = [{"chapter":"test", "unit_id":row["unit_id"], "source_term":"splitting",
            "source_tex_hash":source_tex_hash(row), "occurrence_index":0, "reason":"Editorial first usage."}]
        self.assertEqual([o["source_term"] for o in source_inventory(row, scope)["occurrences"]], ["splitting", "category"])
        self.assertTrue(validate_source_terms(row, candidate([("category", "范畴")]), scope))
        self.assertEqual(validate_source_terms(row, candidate([("splitting", "分裂"), ("category", "范畴")]), scope), [])

    def test_context_classifications_reject_duplicates_negative_indices_and_missing_reasons(self):
        scope = catalog()
        scope["nonmathematical_chapters"] = [{"chapter":"test", "reason":"License fixture.",
            "title_evidence":{"unit_id":"tag:TITLE:title", "source_title":"License", "source_tex_hash":"sha256:"+"0"*64}}]
        scope["nonmathematical_occurrences"] = [{"chapter":"test", "unit_id":unit()["unit_id"], "source_term":"category",
            "source_tex_hash":source_tex_hash(unit()), "occurrence_index":0, "reason":"Editorial fixture."}]
        cases=[]
        for key in ["nonmathematical_chapters", "nonmathematical_occurrences"]:
            changed=copy.deepcopy(scope); changed[key].append(copy.deepcopy(changed[key][0])); cases.append(changed)
        changed=copy.deepcopy(scope); changed["nonmathematical_occurrences"][0]["occurrence_index"]=-1; cases.append(changed)
        changed=copy.deepcopy(scope); del changed["nonmathematical_occurrences"][0]["reason"]; cases.append(changed)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/"config").mkdir()
            for changed in cases:
                with self.subTest(changed=changed):
                    (root/"config/source-terms.json").write_text(json.dumps(changed))
                    with self.assertRaises(RecordError):load_catalog(root)

    def test_repository_rejects_stale_title_and_occurrence_classification_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "config").mkdir()
            title = unit("License", kind="chapter_title"); title["unit_id"] = "tag:TITLE:title"
            body = unit(); scope = catalog(body)
            scope["nonmathematical_chapters"] = [{"chapter":"test", "reason":"License fixture.",
                "title_evidence":{"unit_id":title["unit_id"], "source_title":"License", "source_tex_hash":source_tex_hash(title)}}]
            scope["nonmathematical_occurrences"] = [{"chapter":"test", "unit_id":body["unit_id"], "source_term":"category",
                "source_tex_hash":source_tex_hash(body), "occurrence_index":0, "reason":"Editorial fixture."}]
            (root / "config/source-terms.json").write_text(json.dumps(scope))
            (root / "config/glossary.yml").write_text("entries: []\n")
            (root / "upstream.lock").write_text(f'commit = "{COMMIT}"\n')
            write_jsonl(root / "translation-data/units/test.jsonl", [title, body])
            heading = candidate([]); heading["unit_id"] = title["unit_id"]; heading["translation"] = "许可"
            write_jsonl(root / "translation-data/candidates/lane/test.jsonl", [heading, candidate([])])
            self.assertEqual(audit_repository_terms(root)[1], [])
            for field, value in [("source_title", "Other title"), ("source_tex_hash", "sha256:"+"0"*64)]:
                changed = copy.deepcopy(scope); changed["nonmathematical_chapters"][0]["title_evidence"][field] = value
                (root / "config/source-terms.json").write_text(json.dumps(changed))
                self.assertTrue(any("title evidence" in e for e in audit_repository_terms(root)[1]))
            changed = copy.deepcopy(scope); changed["nonmathematical_occurrences"][0]["source_tex_hash"] = "sha256:"+"0"*64
            (root / "config/source-terms.json").write_text(json.dumps(changed))
            self.assertTrue(any("occurrence lacks" in e for e in audit_repository_terms(root)[1]))

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


class LockedCatalogEvidenceTests(unittest.TestCase):
    """Independent English Git fixtures; no fixture claims model authorship."""

    PROOF = "\\begin{proof}\nA category.\n\\end{proof}"

    def fixture(self, base, proof=None):
        from test_source_containers import fixture, selector
        from stacks_zh.source_reextractions import byte_hash
        proof = self.PROOF if proof is None else proof
        root, harvest, sha = fixture(base, proof=proof)
        row = unit("A category.")
        row["source_commit"] = sha
        row = stamp_unit_hashes(row)
        scope = {"schema_version": 1, "source_commit": sha,
                 "nonmathematical_declarations": {}, "terms": [{
                     "id": "category", "forms": ["category"], "chapters": [],
                     "evidence": [{"kind": "locked-source-container", "chapter": "test",
                                   "source_term": "category", "source_commit": sha,
                                   "selector": selector(), "fragment_hash": byte_hash(proof)}]}]}
        (root / "config/source-terms.json").write_text(json.dumps(scope))
        (root / "config/glossary.yml").write_text("entries: []\n")
        write_jsonl(root / "translation-data/units/test.jsonl", [row])
        write_jsonl(root / "translation-data/candidates/lane/test.jsonl", [candidate([("category", "范畴")])])
        return root, harvest, scope, row

    def test_locked_source_survives_current_segmentation_and_coordinate_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, scope, row = self.fixture(Path(tmp))
            report, errors = audit_repository_terms(root, harvest)
            self.assertEqual(errors, [])
            check = report["locked_catalog_evidence"][0]
            self.assertEqual(check["status"], "PASS")
            self.assertEqual(check["fragment_hash"], scope["terms"][0]["evidence"][0]["fragment_hash"])
            other = copy.deepcopy(row)
            other["unit_id"] = "tag:NEW1:p001"
            other["source_text"] = "Unrelated narration."
            other = stamp_unit_hashes(other)
            output = candidate([]); output["unit_id"] = other["unit_id"]
            write_jsonl(root / "translation-data/units/test.jsonl", [other])
            write_jsonl(root / "translation-data/candidates/lane/test.jsonl", [output])
            self.assertEqual(audit_repository_terms(root, harvest)[1], [])

    def test_dirty_worktree_and_tags_do_not_replace_locked_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _ = self.fixture(Path(tmp))
            (harvest / "test.tex").write_text("Untrusted working-tree replacement.")
            (harvest / "tags/tags").write_text("This is not the locked Tag map.")
            report, errors = audit_repository_terms(root, harvest)
            self.assertEqual(errors, [])
            self.assertEqual(report["locked_catalog_evidence"][0]["status"], "PASS")

    def test_commit_hash_chapter_word_and_each_semantic_coordinate_must_match(self):
        changes = [("source_commit", "0" * 40), ("fragment_hash", "sha256:" + "0" * 64),
                   ("chapter", "other"), ("source_term", "Category"),
                   ("owner_tag", "0002"), ("owner_label", "test-lemma-two"),
                   ("parent_tag", "0002"), ("kind", "lemma"), ("ordinal", 0),
                   ("ordinal", 3), ("file", "other.tex")]
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, scope, _ = self.fixture(Path(tmp))
            for key, value in changes:
                with self.subTest(key=key, value=value):
                    changed = copy.deepcopy(scope)
                    evidence = changed["terms"][0]["evidence"][0]
                    target = evidence if key in {"source_commit", "fragment_hash", "chapter", "source_term"} else evidence["selector"]
                    target[key] = value
                    (root / "config/source-terms.json").write_text(json.dumps(changed))
                    report, errors = audit_repository_terms(root, harvest)
                    self.assertTrue(any("locked catalog evidence" in error for error in errors))
                    self.assertEqual(report["locked_catalog_evidence"][0]["status"], "FAIL")

    def test_math_comment_and_reference_arguments_cannot_supply_lexical_evidence(self):
        for body in ["Only $category$.", "Only a citation \\ref{category}.", "Ordinary words.\n% category"]:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as tmp:
                proof = "\\begin{proof}\n" + body + "\n\\end{proof}"
                root, harvest, _, _ = self.fixture(Path(tmp), proof)
                _, errors = audit_repository_terms(root, harvest)
                self.assertTrue(any("absent from exposed locked-Git prose" in error for error in errors), errors)

    def test_unknown_macro_blocks_evidence_instead_of_falling_back_to_raw_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            proof = "\\begin{proof}\nA \\unclassified{category}.\n\\end{proof}"
            root, harvest, _, _ = self.fixture(Path(tmp), proof)
            _, errors = audit_repository_terms(root, harvest)
            self.assertTrue(any("blocked" in error for error in errors), errors)

    def test_new_evidence_and_legacy_fields_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, scope, _ = self.fixture(Path(tmp))
            for key, value in [("unit_id", "tag:ABCD:definition"),
                               ("source_tex_hash", "sha256:" + "0" * 64), ("unexpected", "value")]:
                with self.subTest(key=key):
                    changed = copy.deepcopy(scope)
                    changed["terms"][0]["evidence"][0][key] = value
                    (root / "config/source-terms.json").write_text(json.dumps(changed))
                    with self.assertRaises(RecordError):
                        load_catalog(root)

    def test_legacy_evidence_still_requires_current_exact_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, scope, row = self.fixture(Path(tmp))
            scope["terms"][0]["evidence"] = [{"chapter": "test", "unit_id": row["unit_id"],
                "source_term": "category", "source_tex_hash": source_tex_hash(row)}]
            (root / "config/source-terms.json").write_text(json.dumps(scope))
            self.assertEqual(audit_repository_terms(root, harvest)[1], [])
            other = copy.deepcopy(row); other["source_text"] = "Unrelated narration."
            write_jsonl(root / "translation-data/units/test.jsonl", [stamp_unit_hashes(other)])
            write_jsonl(root / "translation-data/candidates/lane/test.jsonl", [candidate([])])
            self.assertTrue(any("catalog evidence is absent" in error for error in audit_repository_terms(root, harvest)[1]))

    def test_cli_uses_explicit_harvest_without_default_checkout(self):
        from stacks_zh.cli import main
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, _ = self.fixture(Path(tmp))
            self.assertFalse((root.parent / "stacks-project").exists())
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["audit-terms", "--root", str(root), "--harvest", str(harvest)]), 0)
                self.assertEqual(main(["audit-terms", "--root", str(root)]), 1)
