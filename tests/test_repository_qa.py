from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from stacks_zh.cli import main
from stacks_zh.records import RecordError, write_jsonl
from stacks_zh.workflow import validate_all_candidates, validate_batch
from test_workflow import SOURCE_COMMIT, make_batch_candidate, make_batch_unit


class RepositoryQATests(unittest.TestCase):
    def prepare(self, root):
        lock = root/'upstream.lock'; lock.write_text(f'commit = "{SOURCE_COMMIT}"\n')
        pairs=[]
        for name, lane, run in [('first','a','run-first'),('last','z','run-last')]:
            unit=make_batch_unit(f'tag:TEST:{name}')
            candidate=make_batch_candidate(unit,model_lane=lane,model_id=f'model/{lane}',run_id=run)
            up=root/'translation-data/units'/f'{name}.jsonl'
            cp=root/'translation-data/candidates'/lane/f'{name}.jsonl'
            write_jsonl(up,[unit]); write_jsonl(cp,[candidate]); pairs.append((up,cp))
        return lock,pairs

    def test_all_lanes_and_runs_keep_per_pair_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); lock,pairs=self.prepare(root)
            self.assertEqual(validate_all_candidates(root,lock),(2,[]))
            self.assertTrue(all(validate_batch(u,c,lock)[1]==[] for u,c in pairs))
            before={p:p.read_bytes() for pair in pairs for p in pair}
            self.assertEqual(validate_all_candidates(root,lock),(2,[]))
            self.assertEqual(before,{p:p.read_bytes() for pair in pairs for p in pair})

    def test_last_lane_last_batch_corruption_matches_existing_qa_and_cli_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); lock,pairs=self.prepare(root)
            pairs[-1][1].write_text('{}\n')
            old=validate_batch(*pairs[-1],lock)[1]
            count,errors=validate_all_candidates(root,lock)
            self.assertEqual(count,2)
            self.assertEqual(errors,[f'{pairs[-1][1]}: {e}' for e in old])
            out,err=io.StringIO(),io.StringIO()
            with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                rc=main(['validate-all','--root',str(root)])
            self.assertEqual(rc,1); self.assertNotIn('PASS',out.getvalue())
            self.assertIn('last.jsonl',err.getvalue())

    def test_missing_unit_invalid_json_and_empty_repository_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); lock,pairs=self.prepare(root)
            pairs[0][0].unlink(); pairs[-1][1].write_text('invalid JSON\n')
            count,errors=validate_all_candidates(root,lock)
            self.assertEqual(count,2)
            self.assertEqual(len(errors),2)
            self.assertIn('cannot read',errors[0]); self.assertIn('invalid JSON',errors[1])
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with self.assertRaisesRegex(RecordError,'no candidate batches'):
                validate_all_candidates(root,root/'upstream.lock')


if __name__ == '__main__':
    unittest.main()
