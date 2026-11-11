"""Actual TeX regression for long bilingual diagram text and local compatibility."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from stacks_zh.build_logs import validate_final_tex_log


class DiagramLayoutTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('xelatex'), 'XeLaTeX is required for the template regression')
    def test_long_text_short_dimensions_options_and_local_restore(self):
        root=Path(__file__).resolve().parents[1]
        fixture=root/'tests/fixtures/xymatrix-long-text.tex'
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            env=dict(os.environ,TEXINPUTS=str(root/'ajbook-template/styles')+os.pathsep)
            result=subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error',
                '-file-line-error','-output-directory='+str(out),str(fixture)],
                env=env,capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            log=out/'xymatrix-long-text.log'
            self.assertIn('STACKS-LAYOUT-REGRESSION-PASS',log.read_text())
            self.assertEqual(validate_final_tex_log(log),[])
            self.assertTrue((out/'xymatrix-long-text.pdf').stat().st_size)

    @unittest.skipUnless(shutil.which('xelatex'), 'XeLaTeX is required for the template regression')
    def test_unsupported_nested_matrix_retains_original_failure(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            env=dict(os.environ,TEXINPUTS=str(root/'ajbook-template/styles')+os.pathsep)
            for name,setup in [('original',r'\let\xymatrix\StacksOriginalXymatrix'),('wrapped','')]:
                tex=out/(name+'.tex')
                tex.write_text(r'\documentclass{article}\usepackage{stacks-project-macros}'
                    +setup+r'\begin{document}$$\xymatrix"outer"{A&\xymatrix"inner"{B&C}}$$\end{document}')
                result=subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error',
                    '-output-directory='+str(out),str(tex)],env=env,capture_output=True,text=True,timeout=60)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('Xy-pic error: <pos> "inner1,1" not defined',result.stdout)
