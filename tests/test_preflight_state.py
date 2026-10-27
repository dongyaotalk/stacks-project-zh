"""Actual process/lock recovery tests, independent of translation facts."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from stacks_zh.preflight_state import PreparationRun, process_identity, same_process
from stacks_zh.records import RecordError

ROOT=Path(__file__).resolve().parents[1]
FP='1'*64


class PreparationStateTests(unittest.TestCase):
    def test_actual_identity_requires_start_command_and_cwd_not_pid_alone(self):
        identity=process_identity(os.getpid());self.assertIsNotNone(identity)
        self.assertTrue(same_process(identity))
        self.assertFalse(same_process({**identity,'started':'stale PID identity'}))
        self.assertFalse(same_process({**identity,'cwd':'/not-the-working-directory'}))

    def test_live_child_is_observed_without_duplicate_and_dead_owner_can_resume(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);state=root/'build/state'
            code='''import sys,time\nfrom pathlib import Path\nfrom stacks_zh.preflight_state import PreparationRun\nroot=Path(sys.argv[1])\nwith PreparationRun(root,Path('build/state'),'1'*64) as run:\n run.checkpoint('one',{'source':'verified fixture'})\n print('checkpoint-durable',flush=True)\n time.sleep(30)\n'''
            child=subprocess.Popen([sys.executable,'-c',code,str(root)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(),'checkpoint-durable')
                with PreparationRun(root,state,FP,resume=True) as observed:
                    self.assertEqual(observed.active['process']['pid'],child.pid)
                self.assertEqual(len(list((state/'attempts').glob('*.json'))),1)
                child.terminate();actual=child.wait(timeout=10);self.assertNotEqual(actual,0)
                with PreparationRun(root,state,FP,resume=True) as resumed:
                    self.assertIsNone(resumed.active)
                    self.assertEqual(resumed.results,{'one':{'source':'verified fixture'}})
                    resumed.finish({'state':'READY'},root/'build/result')
                attempts=[json.loads(p.read_text()) for p in sorted((state/'attempts').glob('*.json'))]
                self.assertEqual(len(attempts),2);self.assertEqual(attempts[-1]['exit_code'],0)
                self.assertEqual(attempts[0]['stage'],'RUNNING')  # Do not invent an exit code for a lost process.
                events=[json.loads(line) for line in (state/'events.jsonl').read_text().splitlines()]
                self.assertTrue(any(e.get('previous_owner_interrupted') for e in events))
            finally:
                if child.poll() is None:child.kill();child.wait(timeout=10)
                child.stdout.close();child.stderr.close()

    def test_nonzero_failure_keeps_evidence_and_inputs_changed_cannot_resume(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);state=root/'build/state'
            with self.assertRaisesRegex(RecordError,'actual fixture failure'):
                with PreparationRun(root,state,FP) as run:
                    run.checkpoint('one',{'source':'verified fixture'})
                    raise RecordError('actual fixture failure')
            previous=(state/'attempts/000001.json').read_bytes()
            self.assertEqual(json.loads(previous)['exit_code'],1)
            with self.assertRaisesRegex(RecordError,'inputs changed'):
                with PreparationRun(root,state,'2'*64,resume=True):pass
            self.assertEqual((state/'attempts/000001.json').read_bytes(),previous)
            with PreparationRun(root,state,FP,resume=True) as resumed:
                self.assertEqual(len(resumed.results),1)
                resumed.finish({'state':'READY'},root/'build/result')
            self.assertEqual((state/'attempts/000001.json').read_bytes(),previous)

    def test_symlink_alias_to_an_owned_state_is_still_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);state=root/'build/state'
            with PreparationRun(root,state,FP) as run:
                run.finish({'state':'READY'},root/'build/result')
            alias=root/'build/alias';alias.symlink_to(state,target_is_directory=True)
            with self.assertRaises(RecordError):
                PreparationRun(root,alias,FP)

    def test_state_parent_swap_never_writes_to_foreign_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'root';root.mkdir();state=root/'build/state';outside=Path(d)/'foreign';outside.mkdir();(outside/'notes').write_text('user data')
            with self.assertRaises(RecordError):
                with PreparationRun(root,state,FP) as run:
                    state.rename(root/'build/original-state')
                    state.symlink_to(outside,target_is_directory=True)
                    run.checkpoint('one',{'source':'verified fixture'})
            self.assertEqual({p.name for p in outside.iterdir()},{'notes'})
            self.assertEqual((outside/'notes').read_text(),'user data')

    def test_foreign_output_symlink_fingerprint_and_corrupt_checkpoint_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);foreign=root/'build/foreign';foreign.mkdir(parents=True);(foreign/'notes').write_text('user data')
            with self.assertRaisesRegex(RecordError,'unrelated'):
                with PreparationRun(root,foreign,FP):pass
            with self.assertRaisesRegex(RecordError,'fingerprint'):PreparationRun(root,root/'build/state','../../bad')
            state=root/'build/state'
            with PreparationRun(root,state,FP) as run:
                run.checkpoint('one',{'source':'verified fixture'});run.finish({'state':'READY'},root/'build/result')
            checkpoint=next((state/'checkpoints'/FP).glob('*.json'));value=json.loads(checkpoint.read_text());value['entries']['one']['hash']='changed';checkpoint.write_text(json.dumps(value))
            with self.assertRaisesRegex(RecordError,'checkpoint contents changed'):
                with PreparationRun(root,state,FP,resume=True):pass
            # A rejected __enter__ must release its lock, allowing a fresh explicit preparation.
            with PreparationRun(root,state,FP) as fresh:
                fresh.finish({'state':'READY'},root/'build/result')
            self.assertEqual((foreign/'notes').read_text(),'user data')


if __name__=='__main__':unittest.main()
