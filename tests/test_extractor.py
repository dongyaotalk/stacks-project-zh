from __future__ import annotations

import unittest

from stacks_zh.extractor import extract_section_units
from stacks_zh.records import RecordError, restore_placeholders, validate_units


SOURCE_COMMIT = "b" * 40
TAGS = "ABCD,test-section-limit-sets\nEFGH,test-section-next\n"


class SectionExtractorTests(unittest.TestCase):
    def test_extracts_prose_displays_and_locked_references(self) -> None:
        source = r"""
\section{Limits and colimits in sets}
\label{section-limit-sets}

\noindent
Let $M : \mathcal{I} \to \textit{Sets}$ be a diagram.
The limit is
$$
\lim_\mathcal{I} M.
$$
Its elements are compatible families.

\medskip\noindent
The colimit is
$$
\colim_\mathcal{I} M.
$$
See Sections \ref{section-next} and \ref{other-section-next}.

\section{Next}
\label{section-next}
"""

        units = extract_section_units(
            source, TAGS, SOURCE_COMMIT, "test", "ABCD"
        )

        self.assertEqual(
            [unit["unit_id"] for unit in units],
            [
                "tag:ABCD:title",
                "tag:ABCD:p001",
                "tag:ABCD:display001",
                "tag:ABCD:p002",
                "tag:ABCD:p003",
                "tag:ABCD:display002",
                "tag:ABCD:p004",
            ],
        )
        self.assertEqual(units[0]["source_text"], "Limits and colimits in sets")
        self.assertEqual(
            units[0]["render"],
            {
                "prefix": "\\section{",
                "suffix": "}\n\\label{test-section-limit-sets}\n\n",
            },
        )
        self.assertEqual(
            units[1]["source_text"],
            "Let <MATH_0001> be a diagram. The limit is",
        )
        self.assertEqual(
            units[1]["placeholders"],
            {"MATH_0001": "$M : \\mathcal{I} \\to \\textit{Sets}$"},
        )
        self.assertEqual(units[1]["render"]["prefix"], "\\noindent\n")
        self.assertEqual(units[2]["source_text"], "<MATH_0001>")
        self.assertEqual(units[2]["placeholders"]["MATH_0001"], "$$\n\\lim_\\mathcal{I} M.\n$$")
        self.assertEqual(units[4]["render"]["prefix"], "\\medskip\\noindent\n")
        self.assertEqual(
            units[-1]["source_text"],
            "See Sections <REF_0001> and <REF_0002>.",
        )
        self.assertEqual(
            units[-1]["placeholders"],
            {
                "REF_0001": "\\ref{test-section-next}",
                "REF_0002": "\\ref{other-section-next}",
            },
        )
        self.assertEqual(units[-1]["render"]["suffix"], "\n\n")
        self.assertEqual(validate_units(units, SOURCE_COMMIT), [])
        self.assertEqual(
            restore_placeholders(units[1], units[1]["source_text"]),
            "Let $M : \\mathcal{I} \\to \\textit{Sets}$ be a diagram. The limit is",
        )

    def test_blocks_nested_labels_until_nested_units_are_supported(self) -> None:
        source = r"""
\section{Limits and colimits in sets}
\label{section-limit-sets}
\begin{lemma}
\label{lemma-nested}
Nested statement.
\end{lemma}
"""

        with self.assertRaisesRegex(RecordError, "nested labels: lemma-nested"):
            extract_section_units(source, TAGS, SOURCE_COMMIT, "test", "ABCD")

    def test_blocks_unknown_text_commands(self) -> None:
        source = r"""
\section{Limits and colimits in sets}
\label{section-limit-sets}
\noindent
An \unknown{command} is present.
"""

        with self.assertRaisesRegex(RecordError, r"unknown.*\\unknown"):
            extract_section_units(source, TAGS, SOURCE_COMMIT, "test", "ABCD")

    def test_blocks_comments_in_selected_scope(self) -> None:
        source = r"""
\section{Limits and colimits in sets}
\label{section-limit-sets}
\noindent
Text. % source comment
"""

        with self.assertRaisesRegex(RecordError, "blocks TeX comments"):
            extract_section_units(source, TAGS, SOURCE_COMMIT, "test", "ABCD")

    def test_rejects_tag_from_a_different_chapter(self) -> None:
        with self.assertRaisesRegex(RecordError, "not chapter"):
            extract_section_units(
                "\\section{X}\n\\label{x}\nText.\n",
                "ABCD,other-x\n",
                SOURCE_COMMIT,
                "test",
                "ABCD",
            )


if __name__ == "__main__":
    unittest.main()
