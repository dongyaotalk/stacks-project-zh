from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stacks_zh.records import RecordError, sha256_value, stamp_unit_hashes, write_jsonl
from stacks_zh.workflow import (
    _validate_title_permanent_tags,
    assemble_candidates,
    render_batch,
)


SOURCE_COMMIT = "b" * 40


class RenderTests(unittest.TestCase):
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

    def test_render_combines_multiple_batches(self) -> None:
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
                "前一章。\n",
            )
            self.assertEqual(
                (output / "chapters" / "later.tex").read_text(encoding="utf-8"),
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
