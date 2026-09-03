from __future__ import annotations

import json
import shlex
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from stacks_zh.records import RecordError, sha256_value, stamp_unit_hashes, write_jsonl
from stacks_zh.workflow import (
    _validate_title_permanent_tags,
    assemble_candidates,
    assemble_candidates_many,
    render_batch,
    validate_batches,
)


SOURCE_COMMIT = "b" * 40


def make_batch_unit(unit_id: str) -> dict[str, object]:
    return stamp_unit_hashes(
        {
            "schema_version": 1,
            "unit_id": unit_id,
            "parent_tag": "TEST",
            "chapter": "test",
            "node_kind": "paragraph",
            "risk_level": "R1",
            "source_commit": SOURCE_COMMIT,
            "source_text": f"Source text for {unit_id}.",
            "source_status": "CURRENT",
            "placeholders": {},
            "render": {"prefix": "", "suffix": "\n"},
        }
    )


def make_batch_candidate(
    unit: dict[str, object],
    *,
    model_id: str = "test/model",
    model_lane: str = "test",
    harness_id: str = "codex",
    run_id: str = "run-test",
) -> dict[str, object]:
    context = {"unit_ids": [unit["unit_id"]]}
    return {
        "schema_version": 1,
        "unit_id": unit["unit_id"],
        "source_commit": SOURCE_COMMIT,
        "source_text_hash": unit["source_text_hash"],
        "model_id": model_id,
        "model_lane": model_lane,
        "harness_id": harness_id,
        "run_id": run_id,
        "reasoning_effort": "not_exposed",
        "prompt_version": "translator-v1",
        "glossary_revision": "git:test",
        "context": context,
        "context_hash": sha256_value(context),
        "translation": "这是一条译文。",
        "allowed_english": [],
        "term_occurrences": [],
        "unknown_terms": [],
        "notes": [],
        "stage": "TERM_OK",
        "source_status": "CURRENT",
        "qa_status": "PASS",
        "term_status": "CLEAR",
        "publication_status": "CANDIDATE",
        "created_at": "2026-08-25T00:00:00+08:00",
    }


class BatchValidationTests(unittest.TestCase):
    def write_pair(
        self,
        root: Path,
        name: str,
        unit: dict[str, object],
        candidate: dict[str, object],
    ) -> tuple[Path, Path]:
        unit_path = root / f"units-{name}.jsonl"
        candidate_path = root / f"candidates-{name}.jsonl"
        write_jsonl(unit_path, [unit])
        write_jsonl(candidate_path, [candidate])
        return unit_path, candidate_path

    def test_validates_multiple_aligned_pairs_in_one_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            pairs = []
            for index in (1, 2):
                unit = make_batch_unit(f"tag:TEST:p00{index}")
                pairs.append(
                    self.write_pair(
                        root, str(index), unit, make_batch_candidate(unit)
                    )
                )

            count, errors = validate_batches(
                [pair[0] for pair in pairs],
                [pair[1] for pair in pairs],
                lock,
            )

            self.assertEqual((count, errors), (2, []))

    def test_rejects_unaligned_file_lists_and_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            unit = make_batch_unit("tag:TEST:p001")
            unit_path, candidate_path = self.write_pair(
                root, "one", unit, make_batch_candidate(unit)
            )

            with self.assertRaisesRegex(RecordError, "same number"):
                validate_batches([unit_path], [candidate_path, candidate_path], lock)

            count, errors = validate_batches(
                [unit_path], [root / "missing-candidates.jsonl"], lock
            )
            self.assertEqual(count, 0)
            self.assertTrue(any("cannot read" in error for error in errors))

    def test_rejects_duplicates_across_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            first = make_batch_unit("tag:TEST:p001")
            first_pair = self.write_pair(
                root, "one", first, make_batch_candidate(first)
            )
            duplicate_unit = dict(first)
            duplicate_unit_pair = self.write_pair(
                root, "two", duplicate_unit, make_batch_candidate(first)
            )

            _, errors = validate_batches(
                [first_pair[0], duplicate_unit_pair[0]],
                [first_pair[1], duplicate_unit_pair[1]],
                lock,
            )

            self.assertTrue(any("duplicate unit_id" in error for error in errors))
            self.assertTrue(any("duplicate candidate" in error for error in errors))

    def test_rejects_mixed_model_harness_and_run_metadata(self) -> None:
        for key in ("model_lane", "model_id", "harness_id", "run_id"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                lock = root / "upstream.lock"
                lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
                first = make_batch_unit("tag:TEST:p001")
                second = make_batch_unit("tag:TEST:p002")
                first_pair = self.write_pair(
                    root, "one", first, make_batch_candidate(first)
                )
                changed = make_batch_candidate(second)
                changed[key] = f"other-{key}"
                second_pair = self.write_pair(root, "two", second, changed)

                _, errors = validate_batches(
                    [first_pair[0], second_pair[0]],
                    [first_pair[1], second_pair[1]],
                    lock,
                )

                self.assertTrue(any(f"mismatch for {key}" in error for error in errors))


class RenderTests(unittest.TestCase):
    def test_render_closes_split_definition_list_before_definition(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            specs = [
                (
                    "tag:TEST:statement",
                    "definition",
                    "Definition statement.",
                    "\\begin{definition}\n",
                    "\\begin{enumerate}\n",
                    "定义：",
                ),
                (
                    "tag:TEST:item001",
                    "list_item",
                    "Definition item.",
                    "\\item ",
                    "\n",
                    "条目。",
                ),
                (
                    "tag:TEST:item002",
                    "list_item",
                    "Definition item two.",
                    "\\item ",
                    "\n",
                    "第二条目。",
                ),
                (
                    "tag:TEST:p001",
                    "paragraph",
                    "Definition conclusion.",
                    "",
                    "\n\\end{enumerate}\n\\end{definition}\n",
                    "结论。",
                ),
            ]
            units = []
            candidates = []
            for unit_id, node_kind, source_text, prefix, suffix, translation in specs:
                unit = stamp_unit_hashes(
                    {
                        "schema_version": 1,
                        "unit_id": unit_id,
                        "parent_tag": "TEST",
                        "chapter": "test",
                        "node_kind": node_kind,
                        "risk_level": "R1",
                        "source_commit": SOURCE_COMMIT,
                        "source_text": source_text,
                        "source_status": "CURRENT",
                        "placeholders": {},
                        "render": {"prefix": prefix, "suffix": suffix},
                    }
                )
                candidate = make_batch_candidate(unit)
                candidate["translation"] = translation
                units.append(unit)
                candidates.append(candidate)

            units_path = root / "units.jsonl"
            candidates_path = root / "candidates.jsonl"
            write_jsonl(units_path, units)
            write_jsonl(candidates_path, candidates)
            output = root / "rendered"
            render_batch(
                units_path,
                candidates_path,
                lock,
                output,
                "test",
                "测试候选",
            )

            chapter = (output / "chapters" / "test.tex").read_text(encoding="utf-8")
            self.assertLess(
                chapter.index("\\end{enumerate}"), chapter.index("\\end{definition}")
            )

    def test_render_closes_split_lemma_list_before_lemma(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            specs = [
                (
                    "tag:TEST:statement",
                    "lemma",
                    "Lemma statement.",
                    "\\begin{lemma}\n",
                    "\\begin{enumerate}\n",
                    "引理：",
                ),
                (
                    "tag:TEST:item001",
                    "list_item",
                    "Lemma item.",
                    "\\item ",
                    "\n",
                    "条目。",
                ),
                (
                    "tag:TEST:p001",
                    "paragraph",
                    "Lemma conclusion.",
                    "",
                    "\n\\end{enumerate}\n\\end{lemma}\n",
                    "结论。",
                ),
            ]
            units = []
            candidates = []
            for unit_id, node_kind, source_text, prefix, suffix, translation in specs:
                unit = stamp_unit_hashes(
                    {
                        "schema_version": 1,
                        "unit_id": unit_id,
                        "parent_tag": "TEST",
                        "chapter": "test",
                        "node_kind": node_kind,
                        "risk_level": "R1",
                        "source_commit": SOURCE_COMMIT,
                        "source_text": source_text,
                        "source_status": "CURRENT",
                        "placeholders": {},
                        "render": {"prefix": prefix, "suffix": suffix},
                    }
                )
                candidate = make_batch_candidate(unit)
                candidate["translation"] = translation
                units.append(unit)
                candidates.append(candidate)

            units_path = root / "units.jsonl"
            candidates_path = root / "candidates.jsonl"
            write_jsonl(units_path, units)
            write_jsonl(candidates_path, candidates)
            output = root / "rendered"
            render_batch(
                units_path,
                candidates_path,
                lock,
                output,
                "test",
                "测试候选",
            )

            chapter = (output / "chapters" / "test.tex").read_text(encoding="utf-8")
            self.assertLess(
                chapter.index("\\end{enumerate}"), chapter.index("\\end{lemma}")
            )

    @staticmethod
    def proof_title_units(kind: str = "lemma") -> list[dict[str, object]]:
        common = {
            "schema_version": 1,
            "parent_tag": "0CXY",
            "chapter": "obsolete",
            "risk_level": "R3",
            "source_commit": SOURCE_COMMIT,
            "source_status": "CURRENT",
            "placeholders": {},
        }
        pieces = [
            ("statement", kind, "A claim.", f"\\begin{{{kind}}}\n\\label{{lemma-claim}}\n", f"\n\\end{{{kind}}}\n\n"),
            ("proof-title", "environment_title", "Proof (sketch)", "\\begin{proof}[", "]\n"),
            ("proof-p001", "proof", "A proof.", "", "\n\\end{proof}\n"),
        ]
        return [
            stamp_unit_hashes({
                **common,
                "unit_id": f"tag:09DQ:{suffix}",
                "node_kind": node_kind,
                "source_text": text,
                "render": {"prefix": prefix, "suffix": end},
            })
            for suffix, node_kind, text, prefix, end in pieces
        ]

    def test_unlabeled_proof_title_inherits_adjacent_statement_tag(self) -> None:
        for kind in ("lemma", "proposition", "theorem", "corollary"):
            with self.subTest(kind=kind):
                _validate_title_permanent_tags(
                    self.proof_title_units(kind),
                    {"obsolete-lemma-claim": "09DQ"},
                    Path("tags/tags"),
                )

    def test_unlabeled_proof_title_rejects_missing_or_mismatched_neighbors(self) -> None:
        for case in (
            "no_owner", "no_body", "owner_tag", "body_tag", "owner_chapter",
            "body_chapter", "owner_parent", "body_parent", "owner_kind", "body_kind",
            "owner_opening", "owner_closing", "owner_label", "body_opening",
            "title_id", "title_kind", "title_opening", "title_closing", "title_closing_prefix",
        ):
            with self.subTest(case=case):
                units = self.proof_title_units()
                owner, title, body = units
                if case == "no_owner":
                    units = units[1:]
                elif case == "no_body":
                    units = units[:2]
                elif case in {"owner_tag", "body_tag"}:
                    node = owner if case == "owner_tag" else body
                    node["unit_id"] = str(node["unit_id"]).replace("09DQ", "09DR")
                elif case.endswith("_chapter") or case.endswith("_parent"):
                    node = owner if case.startswith("owner") else body
                    node["chapter" if case.endswith("_chapter") else "parent_tag"] = "other"
                elif case in {"owner_kind", "body_kind"}:
                    (owner if case == "owner_kind" else body)["node_kind"] = "paragraph"
                elif case in {"owner_opening", "owner_label"}:
                    owner["render"]["prefix"] = "" if case == "owner_opening" else "\\begin{lemma}\n"
                elif case == "owner_closing":
                    owner["render"]["suffix"] = "\n"
                elif case == "body_opening":
                    body["render"]["prefix"] = "\\begin{proof}\n"
                elif case == "title_id":
                    title["unit_id"] = "tag:09DQ:title"
                elif case == "title_kind":
                    title["node_kind"] = "section_title"
                elif case == "title_opening":
                    title["render"]["prefix"] = "\\begin{remark}["
                elif case == "title_closing":
                    title["render"]["suffix"] = "]\n\\end{proof}\n"
                elif case == "title_closing_prefix":
                    title["render"]["suffix"] = " ]\n"
                with self.assertRaisesRegex(RecordError, "no rendered label"):
                    _validate_title_permanent_tags(units, {"obsolete-lemma-claim": "09DQ"}, Path("tags/tags"))

    def test_unlabeled_proof_title_requires_owner_label_to_resolve_to_its_tag(self) -> None:
        for tags in ({}, {"obsolete-lemma-claim": "09DR"}):
            with self.subTest(tags=tags), self.assertRaises(RecordError):
                _validate_title_permanent_tags(self.proof_title_units(), tags, Path("tags/tags"))

    def test_render_proof_title_preserves_wrapper_and_rejects_cross_batch_owner(self) -> None:
        for split_owner in (False, True):
            with self.subTest(split_owner=split_owner), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                lock = root / "upstream.lock"
                lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
                tags = root / "tags"
                tags.write_text("09DQ,obsolete-lemma-claim\n", encoding="utf-8")
                units = self.proof_title_units()
                candidates = []
                for unit, translation in zip(units, ("一个陈述。", "证明提纲", "一个论证。")):
                    context = {"instructions": "translator-v1", "unit_ids": [unit["unit_id"]]}
                    candidates.append({
                        "schema_version": 1,
                        "unit_id": unit["unit_id"],
                        "source_commit": SOURCE_COMMIT,
                        "source_text_hash": unit["source_text_hash"],
                        "model_id": "test/model",
                        "model_lane": "test",
                        "reasoning_effort": "not_exposed",
                        "prompt_version": "translator-v1",
                        "glossary_revision": "git:test",
                        "context": context,
                        "context_hash": sha256_value(context),
                        "translation": translation,
                        "allowed_english": [],
                        "term_occurrences": [],
                        "unknown_terms": [],
                        "notes": [],
                        "stage": "TERM_OK",
                        "source_status": "CURRENT",
                        "qa_status": "PASS",
                        "term_status": "CLEAR",
                        "publication_status": "CANDIDATE",
                        "created_at": "2026-08-25T00:00:00+08:00",
                    })
                unit_paths = []
                for index, batch in enumerate(([units[0]], units[1:]) if split_owner else (units,)):
                    path = root / f"units-{index}.jsonl"
                    write_jsonl(path, batch)
                    unit_paths.append(path)
                candidate_path = root / "candidates.jsonl"
                write_jsonl(candidate_path, candidates)
                output = root / "rendered"
                if split_owner:
                    with self.assertRaisesRegex(RecordError, "no rendered label"):
                        render_batch(unit_paths, candidate_path, lock, output, "test", "测试", tags_path=tags)
                else:
                    render_batch(unit_paths, candidate_path, lock, output, "test", "测试", tags_path=tags)
                    rendered = (output / "chapters/obsolete.tex").read_text(encoding="utf-8")
                    self.assertIn("\\begin{proof}[证明提纲]\n一个论证。\n\\end{proof}", rendered)
                    self.assertEqual(rendered.count("\\label{lemma-claim}"), 1)
                    self.assertEqual(rendered.count("\\label{"), 1)

    @classmethod
    def numbered_proof_units(cls, kind: str = "lemma") -> list[dict[str, object]]:
        owner = cls.proof_title_units(kind)[0]
        pieces = [
            ("001-title", "environment_title", "First proof <REF_0001>", "\\begin{proof}[", "]\n"),
            ("001-p001", "proof", "First paragraph.", "", "\n\n"),
            ("001-p002", "proof", "Second paragraph.", "\\medskip\\noindent\n", "\n\\end{proof}\n\n"),
            ("002-title", "environment_title", "Second proof <REF_0001>", "\\begin{proof}[", "]\n"),
            ("002-p001", "proof", "Another argument.", "", "\n\\end{proof}\n"),
        ]
        return [owner] + [
            stamp_unit_hashes({
                **owner,
                "unit_id": f"tag:09DQ:proof-{suffix}",
                "node_kind": node_kind,
                "source_text": text,
                "placeholders": {"REF_0001": "\\ref{lemma-claim}"} if node_kind.endswith("_title") else {},
                "render": {"prefix": prefix, "suffix": end},
            })
            for suffix, node_kind, text, prefix, end in pieces
        ]

    def test_numbered_proof_titles_accept_complete_groups_for_each_statement_kind(self) -> None:
        for kind in ("lemma", "proposition", "theorem", "corollary"):
            with self.subTest(kind=kind):
                units = self.numbered_proof_units(kind)
                _validate_title_permanent_tags(units, {"obsolete-lemma-claim": "09DQ"}, Path("tags"))

    def test_numbered_proof_titles_accept_three_groups_and_separate_owners(self) -> None:
        units = self.numbered_proof_units()
        third = self.numbered_proof_units()[4:]
        for unit in third:
            unit["unit_id"] = str(unit["unit_id"]).replace("proof-002-", "proof-003-")
        units.extend(third)
        other = self.numbered_proof_units()
        for unit in other:
            unit["unit_id"] = str(unit["unit_id"]).replace("09DQ", "09DR")
        other[0]["render"]["prefix"] = "\\begin{lemma}\n\\label{lemma-other}\n"
        units.extend(other)
        _validate_title_permanent_tags(
            units, {"obsolete-lemma-claim": "09DQ", "obsolete-lemma-other": "09DR"}, Path("tags"),
        )

    def test_numbered_proof_titles_reject_incomplete_or_malformed_chains(self) -> None:
        cases = (
            "no_owner", "no_body", "one_group", "owner_tag", "owner_kind", "owner_label",
            "owner_opening", "owner_closing", "owner_extra_proof", "owner_chapter", "owner_parent",
            "title_tag", "title_kind", "title_chapter", "title_parent", "title_label",
            "title_opening", "title_closing", "title_closing_prefix", "title_embedded_proof",
            "body_tag", "body_kind", "body_chapter", "body_parent", "body_opening",
            "body_separator", "body_closing", "body_missing_closing", "body_early_closing",
            "body_embedded_opening", "body_embedded_closing", "group_zero", "group_unpadded",
            "group_gap", "group_duplicate", "group_reordered", "paragraph_gap",
            "paragraph_duplicate", "paragraph_unpadded", "paragraph_zero", "first_paragraph_gap",
            "intervening_unit", "repeated_owner", "mixed_legacy", "renamed_tail",
        )
        for case in cases:
            with self.subTest(case=case):
                units = self.numbered_proof_units()
                owner, title, body, last, second, tail = units
                if case == "no_owner":
                    units = units[1:]
                elif case == "no_body":
                    units.pop()
                elif case == "one_group":
                    units = units[:4]
                elif case in {"owner_tag", "title_tag", "body_tag"}:
                    node = {"owner_tag": owner, "title_tag": second, "body_tag": tail}[case]
                    node["unit_id"] = str(node["unit_id"]).replace("09DQ", "09DR")
                elif case.endswith("_chapter") or case.endswith("_parent"):
                    node = {"owner": owner, "title": second, "body": tail}[case.split("_")[0]]
                    node["chapter" if case.endswith("_chapter") else "parent_tag"] = "other"
                elif case.endswith("_kind"):
                    {"owner_kind": owner, "title_kind": second, "body_kind": tail}[case]["node_kind"] = "paragraph"
                elif case == "owner_label":
                    owner["render"]["prefix"] = "\\begin{lemma}\n"
                elif case == "owner_opening":
                    owner["render"]["prefix"] = "\\label{lemma-claim}\n"
                elif case == "owner_closing":
                    owner["render"]["suffix"] = "\n"
                elif case == "owner_extra_proof":
                    owner["render"]["prefix"] += "\\begin{proof}"
                elif case == "title_label":
                    second["placeholders"]["LABEL_0001"] = "\\label{lemma-claim}"
                elif case == "title_opening":
                    second["render"]["prefix"] = "\\begin{remark}["
                elif case == "title_closing":
                    second["render"]["suffix"] = "]\n\\end{proof}\n"
                elif case == "title_closing_prefix":
                    second["render"]["suffix"] = " ]\n"
                elif case == "title_embedded_proof":
                    second["source_text"] += "\\end{proof}"
                elif case == "body_opening":
                    body["render"]["prefix"] = "\\begin{proof}\n"
                elif case == "body_separator":
                    last["render"]["prefix"] = "\\begin{proof}\n"
                elif case == "body_closing":
                    tail["render"]["suffix"] = "\\end{proof}\\end{proof}"
                elif case == "body_missing_closing":
                    tail["render"]["suffix"] = "\n"
                elif case == "body_early_closing":
                    body["render"]["suffix"] = "\\end{proof}"
                elif case == "body_embedded_opening":
                    tail["placeholders"]["FORMAT_0001"] = "\\begin{proof}"
                elif case == "body_embedded_closing":
                    tail["source_text"] += "\\end{proof}"
                elif case.startswith("group_") and case != "group_reordered":
                    number = {"group_zero": "000", "group_unpadded": "2", "group_gap": "003", "group_duplicate": "001"}[case]
                    second["unit_id"] = f"tag:09DQ:proof-{number}-title"
                elif case == "group_reordered":
                    units = [owner, second, tail, title, body, last]
                elif case.startswith("paragraph_"):
                    number = {"paragraph_gap": "003", "paragraph_duplicate": "001", "paragraph_unpadded": "2", "paragraph_zero": "000"}[case]
                    last["unit_id"] = f"tag:09DQ:proof-001-p{number}"
                elif case == "first_paragraph_gap":
                    tail["unit_id"] = "tag:09DQ:proof-002-p002"
                elif case == "intervening_unit":
                    units.insert(4, self.proof_title_units()[2])
                elif case == "repeated_owner":
                    units.insert(4, self.proof_title_units()[0])
                elif case == "mixed_legacy":
                    second["unit_id"] = "tag:09DQ:proof-title"
                elif case == "renamed_tail":
                    tail["unit_id"] = "tag:09DQ:p001"
                    tail["node_kind"] = "paragraph"
                else:
                    self.fail(f"unhandled mutation {case}")
                with self.assertRaisesRegex(RecordError, "invalid numbered proof group"):
                    _validate_title_permanent_tags(units, {"obsolete-lemma-claim": "09DQ"}, Path("tags"))

    def test_numbered_proof_titles_require_permanent_owner_tag(self) -> None:
        for tags in ({}, {"obsolete-lemma-claim": "09DR"}):
            with self.subTest(tags=tags), self.assertRaises(RecordError):
                _validate_title_permanent_tags(self.numbered_proof_units(), tags, Path("tags"))

    def test_render_numbered_proof_titles_preserves_references_and_batch_boundary(self) -> None:
        for split_at in (None, 1, 4, 5):
            with self.subTest(split_at=split_at), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                lock = root / "upstream.lock"
                lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
                tags = root / "tags"
                tags.write_text("09DQ,obsolete-lemma-claim\n", encoding="utf-8")
                units = self.numbered_proof_units()
                translations = (
                    "一个陈述。", "第一份证明 <REF_0001>", "第一段。", "第二段。",
                    "第二份证明 <REF_0001>", "另一个论证。",
                )
                candidates = []
                for unit, translation in zip(units, translations):
                    context = {"instructions": "translator-v1", "unit_ids": [unit["unit_id"]]}
                    candidates.append({
                        "schema_version": 1, "unit_id": unit["unit_id"],
                        "source_commit": SOURCE_COMMIT, "source_text_hash": unit["source_text_hash"],
                        "model_id": "test/model", "model_lane": "test", "reasoning_effort": "not_exposed",
                        "prompt_version": "translator-v1", "glossary_revision": "git:test",
                        "context": context, "context_hash": sha256_value(context), "translation": translation,
                        "allowed_english": [], "term_occurrences": [], "unknown_terms": [], "notes": [],
                        "stage": "TERM_OK", "source_status": "CURRENT", "qa_status": "PASS",
                        "term_status": "CLEAR", "publication_status": "CANDIDATE",
                        "created_at": "2026-08-31T00:00:00+08:00",
                    })
                batches = (units,) if split_at is None else (units[:split_at], units[split_at:])
                paths = []
                for index, batch in enumerate(batches):
                    path = root / f"units-{index}.jsonl"
                    write_jsonl(path, batch)
                    paths.append(path)
                candidate_path = root / "candidates.jsonl"
                write_jsonl(candidate_path, candidates)
                output = root / "rendered"
                if split_at is not None:
                    with self.assertRaisesRegex(RecordError, "invalid numbered proof group"):
                        render_batch(paths, candidate_path, lock, output, "test", "测试", tags_path=tags)
                    self.assertFalse(output.exists())
                else:
                    render_batch(paths, candidate_path, lock, output, "test", "测试", tags_path=tags)
                    rendered = (output / "chapters/obsolete.tex").read_text(encoding="utf-8")
                    self.assertIn("\\begin{proof}[第一份证明 \\ref{lemma-claim}]\n第一段。", rendered)
                    self.assertIn("\\medskip\\noindent\n第二段。\n\\end{proof}", rendered)
                    self.assertIn("\\begin{proof}[第二份证明 \\ref{lemma-claim}]\n另一个论证。\n\\end{proof}", rendered)
                    self.assertEqual(rendered.count("\\begin{proof}"), 2)
                    self.assertEqual(rendered.count("\\end{proof}"), 2)
                    self.assertEqual(rendered.count("\\label{lemma-claim}"), 1)
                    self.assertEqual(rendered.count("\\label{"), 1)
                    self.assertEqual(rendered.count("\\ref{lemma-claim}"), 2)

    def test_title_local_label_resolves_to_chapter_prefixed_permanent_tag(self) -> None:
        unit = {
            "unit_id": "tag:02BL:title",
            "parent_tag": "02BL",
            "chapter": "desirables",
            "node_kind": "section_title",
            "placeholders": {},
            "render": {
                "prefix": "\\section{",
                "suffix": "}\\label{section-examples-stacks}",
            },
        }

        _validate_title_permanent_tags(
            [unit],
            {"desirables-section-examples-stacks": "02BL"},
            Path("tags/tags"),
        )

    def test_environment_title_uses_unit_tag_not_enclosing_parent_tag(self) -> None:
        unit = {
            "unit_id": "tag:01DE:title",
            "parent_tag": "088X",
            "chapter": "obsolete",
            "node_kind": "environment_title",
            "placeholders": {},
            "render": {
                "prefix": "\\begin{remark}[",
                "suffix": "]\n\\label{remark-projective-resolution}\n",
            },
        }

        _validate_title_permanent_tags(
            [unit],
            {"obsolete-remark-projective-resolution": "01DE"},
            Path("tags/tags"),
        )

    def test_title_unit_tag_must_match_rendered_label(self) -> None:
        unit = {
            "unit_id": "tag:0007:title",
            "parent_tag": "0007",
            "chapter": "conventions",
            "node_kind": "section_title",
            "placeholders": {},
            "render": {
                "prefix": "\\section{",
                "suffix": "}\\label{conventions-section-notation}",
            },
        }

        with self.assertRaisesRegex(
            RecordError,
            "unit Tag '0007' does not match rendered title permanent Tag",
        ):
            _validate_title_permanent_tags(
                [unit],
                {"conventions-section-notation": "055X"},
                Path("tags/tags"),
            )

    def test_render_uses_tag_placeholder_until_reference_target_is_present(self) -> None:
        for target_is_present in (False, True):
            with self.subTest(target_is_present=target_is_present), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                lock = root / "upstream.lock"
                lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
                tags = root / "tags"
                tags.write_text("ABCD,target-section\n", encoding="utf-8")
                unit = stamp_unit_hashes(
                    {
                        "schema_version": 1,
                        "unit_id": "tag:TEST:p001",
                        "parent_tag": "TEST",
                        "chapter": "test",
                        "node_kind": "paragraph",
                        "risk_level": "R1",
                        "source_commit": SOURCE_COMMIT,
                        "source_text": "See <REF_0001>.",
                        "source_status": "CURRENT",
                        "placeholders": {"REF_0001": "\\ref{target-section}"},
                        "render": {
                            "prefix": "",
                            "suffix": "\\label{target-section}\n" if target_is_present else "\n",
                        },
                    }
                )
                context = {"instructions": "translator-v1", "unit_ids": [unit["unit_id"]]}
                candidate = {
                    "schema_version": 1,
                    "unit_id": unit["unit_id"],
                    "source_commit": SOURCE_COMMIT,
                    "source_text_hash": unit["source_text_hash"],
                    "model_id": "test/model",
                    "model_lane": "test",
                    "reasoning_effort": "not_exposed",
                    "prompt_version": "translator-v1",
                    "glossary_revision": "git:test",
                    "context": context,
                    "context_hash": sha256_value(context),
                    "translation": "见 <REF_0001>。",
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
                units_path = root / "units.jsonl"
                candidates_path = root / "candidates.jsonl"
                write_jsonl(units_path, [unit])
                write_jsonl(candidates_path, [candidate])

                output = root / "rendered"
                render_batch(
                    units_path,
                    candidates_path,
                    lock,
                    output,
                    "test",
                    "测试候选",
                    tags_path=tags,
                )

                chapter = (output / "chapters" / "test.tex").read_text(encoding="utf-8")
                if target_is_present:
                    self.assertIn("见 \\ref{target-section}。", chapter)
                    self.assertNotIn("Tag ABCD（待译）", chapter)
                else:
                    self.assertIn(
                        "见 \\href{https://stacks.math.columbia.edu/tag/ABCD}"
                        "{Tag ABCD（待译）}。",
                        chapter,
                    )
                    self.assertNotIn("\\ref{target-section}", chapter)

    def test_render_rejects_unmapped_unresolved_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            tags = root / "tags"
            tags.write_text("ABCD,a-different-section\n", encoding="utf-8")
            unit = stamp_unit_hashes(
                {
                    "schema_version": 1,
                    "unit_id": "tag:TEST:p001",
                    "parent_tag": "TEST",
                    "chapter": "test",
                    "node_kind": "paragraph",
                    "risk_level": "R1",
                    "source_commit": SOURCE_COMMIT,
                    "source_text": "See <REF_0001>.",
                    "source_status": "CURRENT",
                    "placeholders": {"REF_0001": "\\ref{missing-section}"},
                    "render": {"prefix": "", "suffix": "\n"},
                }
            )
            context = {"instructions": "translator-v1", "unit_ids": [unit["unit_id"]]}
            candidate = {
                "schema_version": 1,
                "unit_id": unit["unit_id"],
                "source_commit": SOURCE_COMMIT,
                "source_text_hash": unit["source_text_hash"],
                "model_id": "test/model",
                "model_lane": "test",
                "reasoning_effort": "not_exposed",
                "prompt_version": "translator-v1",
                "glossary_revision": "git:test",
                "context": context,
                "context_hash": sha256_value(context),
                "translation": "见 <REF_0001>。",
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
            units_path = root / "units.jsonl"
            candidates_path = root / "candidates.jsonl"
            write_jsonl(units_path, [unit])
            write_jsonl(candidates_path, [candidate])

            with self.assertRaisesRegex(RecordError, "has no permanent Tag"):
                render_batch(
                    units_path,
                    candidates_path,
                    lock,
                    root / "rendered",
                    "test",
                    "测试候选",
                    tags_path=tags,
                )

    def test_render_restores_protected_tex(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            unit = stamp_unit_hashes(
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
            context = {"instructions": "translator-v1", "unit_ids": [unit["unit_id"]]}
            candidate = {
                "schema_version": 1,
                "unit_id": unit["unit_id"],
                "source_commit": SOURCE_COMMIT,
                "source_text_hash": unit["source_text_hash"],
                "model_id": "test/model",
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
            units_path = root / "units.jsonl"
            candidates_path = root / "candidates.jsonl"
            write_jsonl(units_path, [unit])
            write_jsonl(candidates_path, [candidate])

            output = root / "rendered"
            written = render_batch(
                units_path, candidates_path, lock, output, "test", "测试候选"
            )

            chapter = (output / "chapters" / "test.tex").read_text(encoding="utf-8")
            self.assertIn("见 \\cite{test}。", chapter)
            self.assertNotIn("<CITE_0001>", chapter)
            self.assertIn(output / "metadata.tex", written)
            self.assertTrue(json.loads(units_path.read_text(encoding="utf-8")))

    def test_render_combines_multiple_batches_and_scaffolds_partial_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            unit_paths = []
            candidate_paths = []
            for index, translation, chapter_name in (
                (1, "后一章。", "later"),
                (2, "前一章。", "earlier"),
            ):
                unit = stamp_unit_hashes(
                    {
                        "schema_version": 1,
                        "unit_id": f"tag:TEST:p{index:03d}",
                        "parent_tag": "TEST",
                        "chapter": chapter_name,
                        "node_kind": "paragraph",
                        "risk_level": "R1",
                        "source_commit": SOURCE_COMMIT,
                        "source_text": f"Paragraph {index}.",
                        "source_status": "CURRENT",
                        "placeholders": {},
                        "render": {"prefix": "", "suffix": "\n"},
                    }
                )
                context = {"instructions": "translator-v1", "unit_ids": [unit["unit_id"]]}
                candidate = {
                    "schema_version": 1,
                    "unit_id": unit["unit_id"],
                    "source_commit": SOURCE_COMMIT,
                    "source_text_hash": unit["source_text_hash"],
                    "model_id": "test/model",
                    "model_lane": "test",
                    "reasoning_effort": "not_exposed",
                    "prompt_version": "translator-v1",
                    "glossary_revision": "git:test",
                    "context": context,
                    "context_hash": sha256_value(context),
                    "translation": translation,
                    "allowed_english": [],
                    "term_occurrences": [],
                    "unknown_terms": [],
                    "notes": [],
                    "stage": "TERM_OK",
                    "source_status": "CURRENT",
                    "qa_status": "PASS",
                    "term_status": "CLEAR",
                    "publication_status": "CANDIDATE",
                    "created_at": "2026-08-25T00:00:00+08:00",
                }
                unit_path = root / f"units-{index}.jsonl"
                candidate_path = root / f"candidates-{index}.jsonl"
                write_jsonl(unit_path, [unit])
                write_jsonl(candidate_path, [candidate])
                unit_paths.append(unit_path)
                candidate_paths.append(candidate_path)

            output = root / "rendered"
            manifest = root / "chapters.tex"
            manifest.write_text(
                "\\item \\hyperref[earlier-section-phantom]{Earlier}\n"
                "\\item \\hyperref[later-section-phantom]{Later}\n",
                encoding="utf-8",
            )
            render_batch(
                unit_paths,
                candidate_paths,
                lock,
                output,
                "test",
                "测试候选",
                manifest,
            )

            contents = (output / "contents.tex").read_text(encoding="utf-8")
            self.assertLess(contents.index("chapters/earlier"), contents.index("chapters/later"))
            self.assertEqual(
                (output / "chapters" / "earlier.tex").read_text(encoding="utf-8"),
                "% Generated chapter scaffold; do not edit this preview file.\n"
                "\\chapter{Earlier}\n"
                "\\phantomsection\n"
                "\\label{earlier-section-phantom}\n\n"
                "前一章。\n",
            )
            self.assertEqual(
                (output / "chapters" / "later.tex").read_text(encoding="utf-8"),
                "% Generated chapter scaffold; do not edit this preview file.\n"
                "\\chapter{Later}\n"
                "\\phantomsection\n"
                "\\label{later-section-phantom}\n\n"
                "后一章。\n",
            )

    def test_render_initializes_untranslated_manifest_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            unit = stamp_unit_hashes(
                {
                    "schema_version": 1,
                    "unit_id": "tag:TEST:title",
                    "parent_tag": "TEST",
                    "chapter": "translated",
                    "node_kind": "chapter_title",
                    "risk_level": "R1",
                    "source_commit": SOURCE_COMMIT,
                    "source_text": "Translated",
                    "source_status": "CURRENT",
                    "placeholders": {},
                    "render": {
                        "prefix": "\\chapter{",
                        "suffix": "}\n\\phantomsection\n\\label{translated-section-phantom}\n",
                    },
                }
            )
            context = {"instructions": "translator-v1", "unit_ids": [unit["unit_id"]]}
            candidate = {
                "schema_version": 1,
                "unit_id": unit["unit_id"],
                "source_commit": SOURCE_COMMIT,
                "source_text_hash": unit["source_text_hash"],
                "model_id": "test/model",
                "model_lane": "test",
                "reasoning_effort": "not_exposed",
                "prompt_version": "translator-v1",
                "glossary_revision": "git:test",
                "context": context,
                "context_hash": sha256_value(context),
                "translation": "已翻译",
                "allowed_english": [],
                "term_occurrences": [],
                "unknown_terms": [],
                "notes": [],
                "stage": "TERM_OK",
                "source_status": "CURRENT",
                "qa_status": "PASS",
                "term_status": "CLEAR",
                "publication_status": "CANDIDATE",
                "created_at": "2026-08-25T00:00:00+08:00",
            }
            units_path = root / "units.jsonl"
            candidates_path = root / "candidates.jsonl"
            write_jsonl(units_path, [unit])
            write_jsonl(candidates_path, [candidate])
            manifest = root / "chapters.tex"
            manifest.write_text(
                "\\item \\hyperref[translated-section-phantom]{Translated}\n"
                "\\item \\hyperref[pending-section-phantom]{Pending {Nested}}\n",
                encoding="utf-8",
            )
            title_map = root / "chapter-titles.json"
            title_map.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "titles": {"translated": "已翻译", "pending": "待填章节"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            output = root / "rendered"
            render_batch(
                units_path,
                candidates_path,
                lock,
                output,
                "test",
                "测试候选",
                manifest,
                chapter_title_path=title_map,
            )

            contents = (output / "contents.tex").read_text(encoding="utf-8")
            self.assertLess(
                contents.index("chapters/translated"), contents.index("chapters/pending")
            )
            pending = (output / "chapters" / "pending.tex").read_text(encoding="utf-8")
            self.assertIn("\\chapter{待填章节（Pending {Nested}）}", pending)
            self.assertIn("\\label{pending-section-phantom}", pending)
            self.assertNotIn("待译", pending)
            self.assertNotIn("正文", pending)
            translated = (output / "chapters" / "translated.tex").read_text(
                encoding="utf-8"
            )
            self.assertEqual(translated.count("\\chapter{"), 1)
            self.assertNotIn("Generated chapter scaffold", translated)

    def test_render_orders_same_chapter_batches_by_harvest_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            unit_paths = []
            candidate_paths = []
            for tag, label, source_title, title_translation, paragraph_translation in (
                ("SECOND", "section-second", "Second", "第二节", "第二段。"),
                ("FIRST", "section-first", "First", "第一节", "第一段。"),
            ):
                units = []
                unit_specs = [
                    (
                        f"tag:{tag}:title",
                        tag,
                        "section_title",
                        source_title,
                        title_translation,
                        {
                            "prefix": "\\section{",
                            "suffix": f"}}\n\\label{{test-{label}}}\n",
                        },
                    ),
                    (
                        f"tag:{tag}:p001",
                        tag,
                        "paragraph",
                        f"{source_title} paragraph.",
                        paragraph_translation,
                        {"prefix": "", "suffix": "\n"},
                    ),
                ]
                if tag == "FIRST":
                    unit_specs.extend(
                        [
                            (
                                "tag:NESTED:lemma",
                                "NESTED",
                                "lemma",
                                "Nested lemma.",
                                "嵌套引理。",
                                {
                                    "prefix": "\\begin{lemma}\n",
                                    "suffix": "\n\\label{test-lemma-nested}\n\\end{lemma}\n",
                                },
                            ),
                            (
                                "tag:FIRST:p002",
                                "FIRST",
                                "paragraph",
                                "First trailing paragraph.",
                                "第一尾段。",
                                {"prefix": "", "suffix": "\n"},
                            ),
                        ]
                    )
                for unit_id, parent_tag, node_kind, source_text, translation, render in unit_specs:
                    unit = stamp_unit_hashes(
                        {
                            "schema_version": 1,
                            "unit_id": unit_id,
                            "parent_tag": parent_tag,
                            "chapter": "test",
                            "node_kind": node_kind,
                            "risk_level": "R1",
                            "source_commit": SOURCE_COMMIT,
                            "source_text": source_text,
                            "source_status": "CURRENT",
                            "placeholders": {},
                            "render": render,
                        }
                    )
                    context = {"instructions": "translator-v1", "unit_ids": [unit_id]}
                    candidate = {
                        "schema_version": 1,
                        "unit_id": unit_id,
                        "source_commit": SOURCE_COMMIT,
                        "source_text_hash": unit["source_text_hash"],
                        "model_id": "test/model",
                        "model_lane": "test",
                        "reasoning_effort": "not_exposed",
                        "prompt_version": "translator-v1",
                        "glossary_revision": "git:test",
                        "context": context,
                        "context_hash": sha256_value(context),
                        "translation": translation,
                        "allowed_english": [],
                        "term_occurrences": [],
                        "unknown_terms": [],
                        "notes": [],
                        "stage": "TERM_OK",
                        "source_status": "CURRENT",
                        "qa_status": "PASS",
                        "term_status": "CLEAR",
                        "publication_status": "CANDIDATE",
                        "created_at": "2026-08-25T00:00:00+08:00",
                    }
                    units.append((unit, candidate))
                unit_path = root / f"units-{tag}.jsonl"
                candidate_path = root / f"candidates-{tag}.jsonl"
                write_jsonl(unit_path, (pair[0] for pair in units))
                write_jsonl(candidate_path, (pair[1] for pair in units))
                unit_paths.append(unit_path)
                candidate_paths.append(candidate_path)

            (root / "test.tex").write_text(
                "\\section{First}\n\\label{section-first}\n"
                "\\begin{lemma}\n\\label{lemma-nested}\n\\end{lemma}\n"
                "\\section{Second}\n\\label{section-second}\n",
                encoding="utf-8",
            )
            output = root / "rendered"
            render_batch(
                unit_paths,
                candidate_paths,
                lock,
                output,
                "test",
                "测试候选",
                chapter_source_dir=root,
            )

            chapter = (output / "chapters" / "test.tex").read_text(encoding="utf-8")
            self.assertLess(chapter.index("第一节"), chapter.index("第二节"))
            self.assertLess(chapter.index("第一段"), chapter.index("第二段"))
            self.assertLess(chapter.index("嵌套引理"), chapter.index("第一尾段"))


class AssemblyTests(unittest.TestCase):
    def test_assemble_many_splits_combined_drafts_and_resolves_harness_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            unit_paths: list[Path] = []
            output_paths: list[Path] = []
            drafts: list[dict[str, object]] = []
            for index in range(2):
                unit = make_batch_unit(f"tag:TEST{index}:p001")
                unit["parent_tag"] = f"TEST{index}"
                unit = stamp_unit_hashes(unit)
                unit_path = root / f"units-{index}.jsonl"
                output_path = root / "candidates" / f"batch-{index}.jsonl"
                write_jsonl(unit_path, [unit])
                unit_paths.append(unit_path)
                output_paths.append(output_path)
                drafts.append(
                    {
                        "unit_id": unit["unit_id"],
                        "translation": f"第 {index + 1} 个译文。",
                        "allowed_english": [],
                        "term_occurrences": [],
                        "unknown_terms": [],
                        "notes": [],
                    }
                )
            draft_path = root / "combined-drafts.jsonl"
            write_jsonl(draft_path, reversed(drafts))

            with mock.patch(
                "stacks_zh.workflow.resolve_harness_version", return_value="7.8.9"
            ) as resolver:
                count = assemble_candidates_many(
                    unit_paths,
                    draft_path,
                    output_paths,
                    lock,
                    "test/model",
                    "test-lane",
                    "not_exposed",
                    "translator-v2",
                    "git:policy",
                    "git:glossary",
                    "2026-09-03T00:00:00+08:00",
                    "codex",
                    model_record_id="test:model:declared",
                    run_id="run-test-batch",
                    model_identity_confidence="declared",
                    harness_config_path=root / "harnesses.yml",
                )

            self.assertEqual(count, 2)
            resolver.assert_called_once()
            for index, output_path in enumerate(output_paths):
                candidate = json.loads(output_path.read_text(encoding="utf-8"))
                self.assertEqual(candidate["unit_id"], f"tag:TEST{index}:p001")
                self.assertEqual(candidate["harness_version"], "7.8.9")
                self.assertEqual(candidate["run_id"], "run-test-batch")

    def test_assemble_many_rejects_coverage_before_replacing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            unit_paths = [root / "one.jsonl", root / "two.jsonl"]
            output_paths = [root / "one-output.jsonl", root / "two-output.jsonl"]
            for index, path in enumerate(unit_paths):
                write_jsonl(path, [make_batch_unit(f"tag:TEST:p00{index + 1}")])
            draft_path = root / "drafts.jsonl"
            write_jsonl(
                draft_path,
                [
                    {
                        "unit_id": "tag:TEST:p001",
                        "translation": "译文。",
                        "allowed_english": [],
                        "term_occurrences": [],
                        "unknown_terms": [],
                        "notes": [],
                    }
                ],
            )
            for path in output_paths:
                path.write_text("unchanged\n", encoding="utf-8")

            with mock.patch("stacks_zh.workflow.resolve_harness_version") as resolver:
                with self.assertRaisesRegex(RecordError, "draft coverage mismatch"):
                    assemble_candidates_many(
                        unit_paths,
                        draft_path,
                        output_paths,
                        lock,
                        "test/model",
                        "test-lane",
                        "not_exposed",
                        "translator-v2",
                        "git:policy",
                        "git:glossary",
                        "2026-09-03T00:00:00+08:00",
                        "codex",
                    )
            resolver.assert_not_called()
            self.assertEqual(
                [path.read_text(encoding="utf-8") for path in output_paths],
                ["unchanged\n", "unchanged\n"],
            )

    def test_assemble_many_rejects_cross_chapter_and_input_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            first = make_batch_unit("tag:FIRST:p001")
            second = make_batch_unit("tag:SECOND:p001")
            second["chapter"] = "other"
            second = stamp_unit_hashes(second)
            unit_paths = [root / "first.jsonl", root / "second.jsonl"]
            write_jsonl(unit_paths[0], [first])
            write_jsonl(unit_paths[1], [second])
            drafts = root / "drafts.jsonl"
            write_jsonl(drafts, [{"unit_id": "unused"}])

            with self.assertRaisesRegex(RecordError, "must not overwrite inputs"):
                assemble_candidates_many(
                    unit_paths,
                    drafts,
                    [unit_paths[0], root / "output.jsonl"],
                    lock,
                    "model",
                    "lane",
                    "not_exposed",
                    "translator-v2",
                    "git:policy",
                    "git:glossary",
                    "2026-09-03T00:00:00Z",
                    "codex",
                )

            with self.assertRaisesRegex(RecordError, "cannot cross chapters"):
                assemble_candidates_many(
                    unit_paths,
                    drafts,
                    [root / "first-output.jsonl", root / "second-output.jsonl"],
                    lock,
                    "model",
                    "lane",
                    "not_exposed",
                    "translator-v2",
                    "git:policy",
                    "git:glossary",
                    "2026-09-03T00:00:00Z",
                    "codex",
                )

    def test_assemble_attaches_provenance_and_promotes_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            unit = stamp_unit_hashes(
                {
                    "schema_version": 1,
                    "unit_id": "tag:TEST:p001",
                    "parent_tag": "TEST",
                    "chapter": "test",
                    "node_kind": "paragraph",
                    "risk_level": "R1",
                    "source_commit": SOURCE_COMMIT,
                    "source_text": "An algebraic stack.",
                    "source_status": "CURRENT",
                    "placeholders": {},
                    "render": {"prefix": "", "suffix": "\n"},
                }
            )
            draft = {
                "unit_id": unit["unit_id"],
                "translation": "一个代数栈（algebraic stack）。",
                "allowed_english": [],
                "term_occurrences": [
                    {"source_term": "algebraic stack", "target_term": "代数栈"}
                ],
                "unknown_terms": [
                    {
                        "source_term": "algebraic stack",
                        "target_term": "代数栈",
                        "context": "test",
                    }
                ],
                "notes": [],
            }
            units_path = root / "units.jsonl"
            drafts_path = root / "drafts.jsonl"
            output_path = root / "candidates.jsonl"
            harness_config = root / "harnesses.yml"
            harness_config.write_text(
                "schema: 1\n\nharnesses:\n"
                "  codex:\n"
                "    version_command: "
                + shlex.join([sys.executable, "-c", "print('codex-cli 7.8.9')"])
                + "\n",
                encoding="utf-8",
            )
            write_jsonl(units_path, [unit])
            write_jsonl(drafts_path, [draft])

            count = assemble_candidates(
                units_path,
                drafts_path,
                output_path,
                lock,
                "test/model",
                "test",
                "not_exposed",
                "translator-v2",
                "git:policy",
                "git:glossary",
                "2026-08-25T00:00:00+08:00",
                harness_id="codex",
                harness_version="auto",
                harness_config_path=harness_config,
            )
            self.assertEqual(
                json.loads(output_path.read_text(encoding="utf-8"))["harness_version"],
                "7.8.9",
            )

            candidate = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(count, 1)
            self.assertEqual(candidate["stage"], "STRUCTURE_OK")
            self.assertEqual(candidate["qa_status"], "PASS")
            self.assertEqual(candidate["term_status"], "DECISION_REQUIRED")

    def test_assemble_rejects_legacy_prompt_for_new_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            lock = root / "upstream.lock"
            lock.write_text(f'commit = "{SOURCE_COMMIT}"\n', encoding="utf-8")
            units = root / "units.jsonl"
            drafts = root / "drafts.jsonl"
            write_jsonl(units, [{"unit_id": "unused"}])
            write_jsonl(drafts, [{"unit_id": "unused"}])
            with self.assertRaisesRegex(RecordError, "requires translator-v2"):
                assemble_candidates(
                    units,
                    drafts,
                    root / "candidates.jsonl",
                    lock,
                    "test/model",
                    "test",
                    "not_exposed",
                    "translator-v1",
                    "git:policy",
                    "git:glossary",
                    "2026-08-25T00:00:00+08:00",
                )


if __name__ == "__main__":
    unittest.main()
