from __future__ import annotations

import unittest

from stacks_zh.extractor import extract_section_units, extract_tag_units
from stacks_zh.records import RecordError, restore_placeholders, validate_units


SOURCE_COMMIT = "b" * 40
TAGS = (
    "ABCD,test-section-limit-sets\n"
    "EFGH,test-section-next\n"
    "IJKL,test-definition-directed\n"
    "MNOP,test-lemma-directed-commutes\n"
    "QRST,test-lemma-split-into-directed\n"
)


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

    def test_extracts_prologue_before_nested_labeled_environment(self) -> None:
        source = r"""
\section{Limits and colimits in sets}
\label{section-limit-sets}
Introductory text.

\begin{lemma}
\label{lemma-nested}
Nested statement.
\end{lemma}
"""

        units = extract_section_units(
            source, TAGS, SOURCE_COMMIT, "test", "ABCD"
        )

        self.assertEqual(
            [unit["unit_id"] for unit in units],
            ["tag:ABCD:title", "tag:ABCD:p001"],
        )
        self.assertEqual(units[1]["source_text"], "Introductory text.")
        self.assertEqual(units[1]["render"]["suffix"], "\n\n")

    def test_blocks_nested_label_outside_child_environment(self) -> None:
        source = r"""
\section{Limits and colimits in sets}
\label{section-limit-sets}
Introductory text.
\label{lemma-nested}
"""

        with self.assertRaisesRegex(RecordError, "outside an identifiable"):
            extract_section_units(source, TAGS, SOURCE_COMMIT, "test", "ABCD")

    def test_title_only_prologue_keeps_section_label_rendering(self) -> None:
        source = r"""
\section{Limits and colimits in sets}
\label{section-limit-sets}
\begin{lemma}
\label{lemma-nested}
Nested statement.
\end{lemma}
"""

        units = extract_section_units(
            source, TAGS, SOURCE_COMMIT, "test", "ABCD"
        )

        self.assertEqual([unit["unit_id"] for unit in units], ["tag:ABCD:title"])
        self.assertEqual(
            units[0]["render"]["suffix"],
            "}\n\\label{test-section-limit-sets}\n\n",
        )

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


class TaggedDefinitionExtractorTests(unittest.TestCase):
    def test_extracts_enumerated_definition_and_text_declarations(self) -> None:
        source = r"""
\begin{definition}
\label{definition-directed}
We say that a diagram $M : \mathcal{I} \to \mathcal{C}$ is {\it directed},
or {\it filtered} if the following conditions hold:
\begin{enumerate}
\item the category $\mathcal{I}$ has at least one object,
\item for every pair of objects $x, y$ there exists an object $z$, and
\item for every pair of morphisms $a, b : x \to y$ there exists
$c : y \to z$ such that $M(c \circ a) = M(c \circ b)$.
\end{enumerate}
We say that $\mathcal{I}$ is {\it directed} if
$\text{id} : \mathcal{I} \to \mathcal{I}$ is filtered.
\end{definition}
"""

        units = extract_tag_units(
            source, TAGS, SOURCE_COMMIT, "test", "IJKL"
        )

        self.assertEqual(
            [unit["unit_id"] for unit in units],
            [
                "tag:IJKL:statement",
                "tag:IJKL:item001",
                "tag:IJKL:item002",
                "tag:IJKL:item003",
                "tag:IJKL:p001",
            ],
        )
        self.assertEqual(
            units[0]["source_text"],
            "We say that a diagram <MATH_0001> is "
            "<TEXTITOPEN_0001>directed<TEXTITCLOSE_0001>, or "
            "<TEXTITOPEN_0002>filtered<TEXTITCLOSE_0002> if the following "
            "conditions hold:",
        )
        self.assertEqual(
            units[0]["placeholders"],
            {
                "MATH_0001": "$M : \\mathcal{I} \\to \\mathcal{C}$",
                "TEXTITOPEN_0001": "{\\it ",
                "TEXTITCLOSE_0001": "}",
                "TEXTITOPEN_0002": "{\\it ",
                "TEXTITCLOSE_0002": "}",
            },
        )
        self.assertEqual(
            units[0]["render"],
            {
                "prefix": "\\begin{definition}\n"
                "\\label{test-definition-directed}\n",
                "suffix": "\n\\begin{enumerate}\n",
            },
        )
        self.assertEqual(units[3]["render"]["suffix"], "\n\\end{enumerate}\n")
        self.assertEqual(units[4]["render"]["suffix"], "\n\\end{definition}\n\n")
        self.assertEqual(validate_units(units, SOURCE_COMMIT), [])
        self.assertEqual(
            restore_placeholders(units[0], units[0]["source_text"]),
            "We say that a diagram $M : \\mathcal{I} \\to \\mathcal{C}$ is "
            "{\\it directed}, or {\\it filtered} if the following conditions hold:",
        )

    def test_blocks_definition_without_exactly_one_enumerate(self) -> None:
        source = r"""
\begin{definition}
\label{definition-directed}
Text before.

Text after.
\end{definition}
"""

        with self.assertRaisesRegex(RecordError, "exactly one enumerate"):
            extract_tag_units(source, TAGS, SOURCE_COMMIT, "test", "IJKL")

    def test_blocks_nested_labels(self) -> None:
        source = r"""
\begin{definition}
\label{definition-directed}
Text before.
\begin{enumerate}
\item Text. \label{item-nested}
\end{enumerate}
Text after.
\end{definition}
"""

        with self.assertRaisesRegex(RecordError, "nested label"):
            extract_tag_units(source, TAGS, SOURCE_COMMIT, "test", "IJKL")


class TaggedStatementExtractorTests(unittest.TestCase):
    def test_extracts_lemma_displays_trailing_text_and_adjacent_proof(self) -> None:
        source = r"""
\begin{lemma}
\label{lemma-directed-commutes}
Let $\mathcal{I}$ and $\mathcal{J}$ be index categories.
In this case
$$
\colim_i \lim_j M_{i,j} = \lim_j \colim_i M_{i,j}.
$$
In particular, filtered colimits commute with finite products.
\end{lemma}

\begin{proof}
Omitted. See Lemma \ref{lemma-other}.
\end{proof}
"""

        units = extract_tag_units(
            source, TAGS, SOURCE_COMMIT, "test", "MNOP"
        )

        self.assertEqual(
            [unit["unit_id"] for unit in units],
            [
                "tag:MNOP:statement",
                "tag:MNOP:display001",
                "tag:MNOP:p001",
                "tag:MNOP:proof-p001",
            ],
        )
        self.assertEqual(
            units[0]["render"],
            {
                "prefix": "\\begin{lemma}\n"
                "\\label{test-lemma-directed-commutes}\n",
                "suffix": "\n",
            },
        )
        self.assertEqual(units[1]["source_text"], "<MATH_0001>")
        self.assertEqual(
            units[2]["render"]["suffix"], "\n\\end{lemma}\n\n"
        )
        self.assertEqual(
            units[3]["source_text"], "Omitted. See Lemma <REF_0001>."
        )
        self.assertEqual(
            units[3]["placeholders"],
            {"REF_0001": "\\ref{test-lemma-other}"},
        )
        self.assertEqual(
            units[3]["render"],
            {
                "prefix": "\\begin{proof}\n",
                "suffix": "\n\\end{proof}\n\n",
            },
        )
        self.assertEqual(validate_units(units, SOURCE_COMMIT), [])

    def test_blocks_nested_environment_in_simple_lemma(self) -> None:
        source = r"""
\begin{lemma}
\label{lemma-directed-commutes}
Text before.
\begin{itemize}
\item Nested text.
\end{itemize}
\end{lemma}
"""

        with self.assertRaisesRegex(RecordError, r"unknown.*\\begin"):
            extract_tag_units(source, TAGS, SOURCE_COMMIT, "test", "MNOP")

    def test_extracts_enumerated_lemma_and_adjacent_proof(self) -> None:
        source = r"""
\begin{lemma}
\label{lemma-split-into-directed}
Let $\mathcal{I}$ be an index category. Assume
\begin{enumerate}
\item for every pair of morphisms $a, b$ there is an object $z$, and
\item for every pair of morphisms $c, d$ there is a morphism $e$.
\end{enumerate}
Then $\mathcal{I}$ is a union of filtered index categories.
\end{lemma}

\begin{proof}
If $\mathcal{I}$ is empty, the result is clear.
\end{proof}
"""

        units = extract_tag_units(
            source, TAGS, SOURCE_COMMIT, "test", "QRST"
        )

        self.assertEqual(
            [unit["unit_id"] for unit in units],
            [
                "tag:QRST:statement",
                "tag:QRST:item001",
                "tag:QRST:item002",
                "tag:QRST:p001",
                "tag:QRST:proof-p001",
            ],
        )
        self.assertEqual(units[0]["node_kind"], "lemma")
        self.assertEqual(
            units[0]["render"]["prefix"],
            "\\begin{lemma}\n\\label{test-lemma-split-into-directed}\n",
        )
        self.assertEqual(
            units[2]["render"]["suffix"], "\n\\end{enumerate}\n"
        )
        self.assertEqual(
            units[3]["render"]["suffix"], "\n\\end{lemma}\n\n"
        )
        self.assertEqual(
            units[4]["render"],
            {
                "prefix": "\\begin{proof}\n",
                "suffix": "\n\\end{proof}\n\n",
            },
        )
        self.assertEqual(validate_units(units, SOURCE_COMMIT), [])


if __name__ == "__main__":
    unittest.main()
