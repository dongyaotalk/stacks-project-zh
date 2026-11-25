import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stacks_zh.candidate_book import prepare_candidate_book
from stacks_zh.records import RecordError
from stacks_zh.workflow import _chapter_scaffold


ROOT = Path(__file__).resolve().parents[1]
REVISION = "a" * 40
TITLES = {"alpha": "Alpha", "beta": "Beta", "gamma": "Gamma", "index": "Index"}
PRIMARY = "openai-gpt-6.1-sol"
FALLBACK = "openai-gpt-5.6-sol"


class CandidateBookTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.harvest = self.root / "english"
        (self.harvest / "tags").mkdir(parents=True)
        (self.harvest / "chapters.tex").write_text("".join(
            rf"\item \hyperref[{slug}-section-phantom]{{{title}}}" + "\n" for slug, title in TITLES.items()
        ))
        (self.harvest / "tags/tags").write_text("012A,alpha-lost\n")
        (self.root / "upstream.lock").write_text(f'commit = "{REVISION}"\n')
        config = self.root / "config"
        config.mkdir()
        for path in ("models.yml", "macro-policy.yml"):
            (config / path).write_bytes((ROOT / "config" / path).read_bytes())
        (config / "chapter-titles.json").write_text(json.dumps({"schema_version": 1, "titles": TITLES}))
        self.translations = self.root / "ajbook-template/translations"

    def write_lane(self, lane, chapters, revision=REVISION):
        directory = self.translations / lane
        chapter_dir = directory / "chapters"
        chapter_dir.mkdir(parents=True)
        (directory / "contents.tex").write_text("".join(
            rf"\input{{\TranslationModelDirectory/chapters/{slug}}}" + "\n" for slug in TITLES
        ))
        (directory / "metadata.tex").write_text(f"英文源提交 {revision[:12]}\n")
        for slug, title in TITLES.items():
            (chapter_dir / f"{slug}.tex").write_text(
                _chapter_scaffold(slug, title, title) + chapters.get(slug, "")
            )

    def test_selected_chapters_drive_source_index_and_cross_chapter_fallback(self):
        self.write_lane(PRIMARY, {"alpha": "First lane content.\n"})
        self.write_lane(FALLBACK, {
            "alpha": "Lower-priority content.\n" + r"\label{alpha-lost}" + "\n",
            "beta": r"Other lane content. $\ref{alpha-lost}$" + "\n",
        })

        output = prepare_candidate_book(self.root, self.harvest, [PRIMARY, FALLBACK])

        self.assertEqual(output.name, "candidate")
        self.assertIn("First lane content.", (output / "chapters/alpha.tex").read_text())
        beta = (output / "chapters/beta.tex").read_text()
        self.assertIn("Other lane content.", beta)
        self.assertIn(r"$\href{https://stacks.math.columbia.edu/tag/012A}{\text{Tag 012A（待译）}}$", beta)
        self.assertEqual((output / "chapters/gamma.tex").read_text(),
                         _chapter_scaffold("gamma", "Gamma", "Gamma"))
        frontmatter = (output / "frontmatter.tex").read_text()
        self.assertIn(r"\addcontentsline{toc}{chapter}{各章译文来源}", frontmatter)
        self.assertIn(r"\hyperref[alpha-section-phantom]{1} & \textcolor{blue!55!black}{gpt-6.1-sol}", frontmatter)
        self.assertIn(r"\hyperref[beta-section-phantom]{2} & \textcolor{teal!60!black}{gpt-5.6-sol}", frontmatter)
        self.assertIn(r"\hyperref[gamma-section-phantom]{3} & \textcolor{black!58}{待译}", frontmatter)
        self.assertIn(r"\hyperref[index-section-phantom]{4} & 索引", frontmatter)

    def test_rejects_a_manuscript_rendered_from_another_source(self):
        self.write_lane(PRIMARY, {}, revision="b" * 40)
        with self.assertRaisesRegex(RecordError, "locked English source"):
            prepare_candidate_book(self.root, self.harvest, [PRIMARY])
        self.assertFalse((self.translations / "candidate").exists())
