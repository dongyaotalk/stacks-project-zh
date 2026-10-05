from __future__ import annotations

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stacks_zh.build_logs import validate_final_tex_log
from stacks_zh.cli import main


ROOT = Path(__file__).parents[1]
COMPLETE = "Output written on build/book.pdf (2 pages).\n"


class BuildLogTests(unittest.TestCase):
    def check(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.log"
            path.write_text(text, encoding="utf-8")
            before = path.read_bytes()
            errors = validate_final_tex_log(path)
            self.assertEqual(path.read_bytes(), before)
            return errors

    def test_clean_complete_log_and_wrapped_output_summary(self):
        self.assertEqual(self.check("This is XeTeX.\n" + COMPLETE), [])
        self.assertEqual(self.check("Output written on a long/path/book.p\ndf (45\n7 pages).\n"), [])

    def test_missing_unicode_glyph_fails_even_when_pdf_was_written(self):
        errors = self.check("Missing character: There is no δ (U+03B4) in font Example!\n" + COMPLETE)
        self.assertEqual(len(errors), 1)
        self.assertIn(":1: missing character", errors[0])

    def test_undefined_references_citations_and_summaries_fail(self):
        diagnostics = [
            "LaTeX Warning: Reference `foo' on page 1 undefined on input line 7.",
            "LaTeX Warning: Reference `very-long-target' on page 1 un\ndefined on input line 7.",
            "LaTeX Warning: Citation `paper' on page 1 undefined on input line 7.",
            "Package biblatex Warning: Citation 'paper' on page 1\n(biblatex) undefined on input line 7.",
            "Package biblatex Warning: Citation 'paper' on page 1 un\n(biblatex) defined on input line 7.",
            "LaTeX Warning: There were undefined references.",
            "LaTeX Warning: There were undefined citations.",
        ]
        for diagnostic in diagnostics:
            with self.subTest(diagnostic=diagnostic):
                errors = self.check(diagnostic + "\n\n" + COMPLETE)
                self.assertEqual(len(errors), 1)
                self.assertIn("undefined reference or citation", errors[0])

    def test_duplicate_labels_fail(self):
        for diagnostic in ["LaTeX Warning: Label `foo' multiply defined.",
                           "LaTeX Warning: There were multiply-defined labels."]:
            with self.subTest(diagnostic=diagnostic):
                errors = self.check(diagnostic + "\n\n" + COMPLETE)
                self.assertEqual(len(errors), 1)
                self.assertIn("duplicate label", errors[0])

    def test_font_fallbacks_bad_boxes_and_rerun_messages_are_not_reference_errors(self):
        text = """LaTeX Font Warning: Font shape `TU/FandolSong/bx/it' undefined
using `TU/FandolSong/bx/n' instead.

Overfull \\hbox (0.3pt too wide) in paragraph at lines 1--3
\\TU/Example Missing character: text discussed by the document

Package physics Warning: Other package undefined command settings retained.

LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.

"""
        self.assertEqual(self.check(text + COMPLETE), [])

    def test_missing_empty_or_incomplete_logs_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIn("cannot read", validate_final_tex_log(Path(directory) / "absent.log")[0])
        self.assertIn("empty", self.check(" \n")[0])
        self.assertIn("no completed PDF output summary", self.check("This is XeTeX.\n")[0])
        self.assertIn("no completed PDF output summary", self.check("Output written on fake.dvi (2 pages).\n")[0])

    def test_cli_returns_failure_with_location_and_success_for_complete_log(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.log"
            for text, expected in [("Missing character: δ\n" + COMPLETE, 1), (COMPLETE, 0)]:
                path.write_text(text)
                output, error = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    result = main(["check-build-log", "--log", str(path)])
                self.assertEqual(result, expected)
                if expected:
                    self.assertIn(f"{path}:1:", error.getvalue())
                    self.assertNotIn("PASS", output.getvalue())
                else:
                    self.assertEqual(error.getvalue(), "")
                    self.assertIn("Final TeX log: PASS", output.getvalue())


class BuildLogMakeTests(unittest.TestCase):
    def build(self, root: Path, mode: str) -> tuple[subprocess.CompletedProcess, Path, Path]:
        engine = root / "fake-engine.py"
        engine.write_text(f"#!{sys.executable}\n" + r'''
import sys
from pathlib import Path
args = sys.argv[1:]
output = Path(next(arg.split('=', 1)[1] for arg in args if arg.startswith('-output-directory=')))
job = next(arg.split('=', 1)[1] for arg in args if arg.startswith('-jobname='))
counter = output / 'passes'
count = int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(count))
mode = MODE
warning = ''
if mode == 'missing':
    warning = 'Missing character: There is no δ in font Example!\n'
elif mode == 'reference':
    warning = "LaTeX Warning: Reference `foo' undefined on input line 2.\n\n"
elif mode == 'citation':
    warning = "Package biblatex Warning: Citation 'paper' undefined on input line 2.\n\n"
elif mode == 'duplicate':
    warning = "LaTeX Warning: Label `foo' multiply defined.\n\n"
elif mode == 'early-warning' and count == 1:
    warning = "LaTeX Warning: Reference `foo' undefined on input line 2.\n\n"
(output / (job + '.log')).write_text(warning + 'Output written on ' + job + '.pdf (2 pages).\n')
(output / (job + '.aux')).write_text('')
(output / (job + '.pdf')).write_bytes(b'%PDF fake compiler output\n')
'''.replace("MODE", repr(mode)))
        engine.chmod(0o755)
        destination = root / "output spaced"
        destination.mkdir()
        final = destination / "stacks-project-zh-test-log.pdf"
        final.write_bytes(b"Existing PDF must survive a failed build.\n")
        # Skip only external toolchain/source setup in this isolated recipe
        # test. The real pdf recipe and final gate run, using a zero-exit mock.
        result = subprocess.run(
            ["make", "--no-print-directory", "-o", "check", "pdf", "MODEL=test-log",
             f"ENGINE={engine}", "BIB_PROCESSOR=unused", f"BUILD_ROOT={root / 'build'}",
             f"OUTPUT_DIR={destination}"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        return result, final, root / "build/ajbook/test-log/passes"

    def test_zero_exit_compiler_defects_block_copy_and_preserve_existing_pdf(self):
        for mode in ["missing", "reference", "citation", "duplicate"]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                result, final, passes = self.build(Path(directory), mode)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("ERROR:", result.stderr)
                self.assertEqual(passes.read_text(), "3")
                self.assertEqual(final.read_bytes(), b"Existing PDF must survive a failed build.\n")

    def test_clean_final_pass_can_copy_after_early_reference_warning(self):
        for mode in ["clean", "early-warning"]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                result, final, passes = self.build(Path(directory), mode)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("Final TeX log: PASS", result.stdout)
                self.assertEqual(passes.read_text(), "3")
                self.assertEqual(final.read_bytes(), b"%PDF fake compiler output\n")


if __name__ == "__main__":
    unittest.main()
