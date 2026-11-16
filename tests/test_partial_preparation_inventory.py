"""Synthetic complete Git fixtures; partial output confers no generation authority."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_source_adoptions import synthetic_fixture, write
import test_chapter_validation as chapter_tests
from test_chapter_validation import preparation_copy
from test_source_containers import git
from stacks_zh import source_adoptions as a
from stacks_zh.chapter_relations import check_preparation_evidence, _partial_unadopted_raw_inventory
from stacks_zh.current_qa import InputSnapshot
from stacks_zh.validation_io import InputReads
from stacks_zh.source_containers import Containers
from stacks_zh.records import RecordError, write_jsonl
from stacks_zh.source_reextractions import byte_hash


def fixture(base):
    root,harvest,fp,rp,frozen,raw=synthetic_fixture(base)
    git(root,'update-ref','refs/heads/main',git(root,'rev-parse','HEAD'))
    mp,rt=preparation_copy(root,frozen,fp,rp)
    write_jsonl(rp,raw[:1])
    return root,harvest,fp,rp,frozen,raw,mp,rt


def check(root,harvest,mp):
    reads=InputReads()
    with reads.activate():
        result=check_preparation_evidence(root,harvest,InputSnapshot(root),
            [mp.relative_to(root).as_posix()],'test','synthetic',reads,Containers(root,harvest))
        reads.assert_unchanged()
        return result


class PartialPreparationInventoryTests(unittest.TestCase):
    def test_complete_source_partial_inventory_has_exact_missing_ids_and_no_authority(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,fp,rp,frozen,raw,mp,rt=fixture(Path(d))
            immutable={p:p.read_bytes() for p in (fp,rp,mp,rt,root/frozen['task']['scope_manifest'])}
            result=check(root,harvest,mp)[0]
            inventory=result['raw_inventory']
            self.assertEqual(result['source_errors'],[])
            self.assertEqual(result['generation_validation'],'not_claimed')
            self.assertEqual(inventory['disposition'],'partial-output-inventory')
            self.assertEqual(inventory['expected_unit_ids'],frozen['unit_ids'])
            self.assertEqual(inventory['present_unit_ids'],[raw[0]['unit_id']])
            self.assertEqual(inventory['missing_unit_ids'],frozen['unit_ids'][1:])
            self.assertFalse(inventory['run_created']);self.assertFalse(inventory['adoption_created'])
            self.assertEqual(inventory['raw_attempts'][0]['hash'],byte_hash(rp.read_bytes()))
            for p,b in immutable.items():self.assertEqual(p.read_bytes(),b)
            self.assertFalse((root/f"translation-data/source-adoptions/{frozen['adoption_id']}.json").exists())
            self.assertFalse((root/f"translation-data/runs/{frozen['run_id']}.json").exists())
            with self.assertRaisesRegex(RecordError,'complete model record'):
                a.assemble_source_adoption(root,fp,[rp],harvest)
            self.assertTrue(all(not (root/b['candidates_path']).exists() for b in frozen['batches']))

    def test_full_union_retains_existing_complete_inventory_behavior(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,fp,rp,frozen,raw,mp,rt=fixture(Path(d))
            write_jsonl(rp,raw)
            result=check(root,harvest,mp)[0]
            self.assertNotIn('raw_inventory',result)
            self.assertEqual(result['generation_validation'],'not_claimed')

    def test_shards_and_retry_hashes_preserve_original_attempt_order(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,fp,rp,frozen,raw,mp,rt=fixture(Path(d))
            retry=rp.with_name('synthetic-retry.jsonl');write_jsonl(retry,raw[:1])
            scope=json.loads(frozen['task']['scope_bytes'])
            relative=retry.relative_to(root).as_posix()
            scope['allowed_write_files'].append(relative);scope['data_scopes'][0]['allowed_write_files'].append(relative)
            sp=root/frozen['task']['scope_manifest'];write(sp,scope)
            frozen['task'].update(scope_bytes=sp.read_text(),scope_manifest_sha256=byte_hash(sp.read_bytes()))
            mp,rt=preparation_copy(root,frozen,fp,rp)
            model_input=json.loads(mp.read_bytes());model_input['raw_output_paths_reserved'].append(relative);write(mp,model_input)
            inventory=check(root,harvest,mp)[0]['raw_inventory']
            self.assertEqual([x['path'] for x in inventory['raw_attempts']],
                             [rp.relative_to(root).as_posix(),relative])
            self.assertEqual(inventory['present_unit_ids'],[raw[0]['unit_id']])

    def test_malformed_raw_runtime_scope_and_policy_still_fail(self):
        for mutation in ('duplicate','outside','schema','runtime','reservation','policy','hash'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                root,harvest,fp,rp,frozen,raw,mp,rt=fixture(Path(d))
                if mutation=='duplicate':write_jsonl(rp,[raw[0],raw[0]])
                elif mutation=='outside':
                    row=copy.deepcopy(raw[0]);row['unit_id']='tag:9999:statement';write_jsonl(rp,[row])
                elif mutation=='schema':
                    row=copy.deepcopy(raw[0]);row.pop('notes');write_jsonl(rp,[row])
                elif mutation=='runtime':
                    value=json.loads(rt.read_bytes());value['turn_metadata']['effort']='altered';write(rt,value)
                elif mutation=='reservation':
                    value=json.loads(mp.read_bytes());value['raw_output_paths_reserved']=['docs/evidence/outside.jsonl'];write(mp,value)
                elif mutation=='policy':
                    frozen['policies'][0]['hash']='sha256:'+'0'*64;mp,rt=preparation_copy(root,frozen,fp,rp)
                else:
                    value=json.loads(mp.read_bytes());value['generation_freeze']['hash']='sha256:'+'0'*64;write(mp,value)
                with self.assertRaises(RecordError):check(root,harvest,mp)

    def test_installed_identity_or_predecessor_never_uses_partial_helper(self):
        for mutation in ('run','adoption','candidate','prior','version','origin'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                root,harvest,fp,rp,frozen,raw,mp,rt=fixture(Path(d))
                if mutation=='run':write(root/f"translation-data/runs/{frozen['run_id']}.json",{})
                elif mutation=='adoption':write(root/f"translation-data/source-adoptions/{frozen['adoption_id']}.json",{})
                elif mutation=='candidate':write_jsonl(root/frozen['batches'][0]['candidates_path'],[dict(run_id=frozen['run_id'])])
                elif mutation=='prior':frozen['batches'][0]['prior_attempts']=[{}]
                elif mutation=='version':frozen['tool_version']='source-adoption-input-v2'
                else:frozen['origin_commit']='0'*40
                attempts=[dict(path=rp.relative_to(root).as_posix(),hash=byte_hash(rp.read_bytes()),unit_ids=[raw[0]['unit_id']])]
                with self.assertRaises(RecordError):
                    _partial_unadopted_raw_inventory(root,frozen,attempts,json.loads(frozen['task']['scope_bytes']),InputSnapshot(root),[],[])

    def test_historical_frozen_scope_survives_later_authorized_expansion(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,fp,rp,frozen,raw,mp,rt=fixture(Path(d))
            original=fp.read_bytes()
            sp=root/frozen['task']['scope_manifest'];scope=json.loads(sp.read_bytes())
            scope['allowed_write_files'].append('docs/evidence/later-scope-note.json')
            write(sp,scope)
            result=check(root,harvest,mp)[0]
            self.assertEqual(result['raw_inventory']['missing_unit_ids'],frozen['unit_ids'][1:])
            self.assertEqual(fp.read_bytes(),original)

    def test_complete_assembly_protected_token_failure_remains_strict(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,fp,rp,frozen,raw,mp,rt=fixture(Path(d))
            changed=copy.deepcopy(raw)
            unit=frozen['batches'][0]['units'][0]
            token=next(iter(unit['placeholders']))
            changed[0]['translation']=changed[0]['translation'].replace('<'+token+'>','',1)
            write_jsonl(rp,changed)
            with self.assertRaises(RecordError):a.assemble_source_adoption(root,fp,[rp],harvest)

    def test_original_rejected_model_scope_missing_union_remains_rejected(self):
        # The existing negative fixture deliberately has an invalid lane/model scope.
        with tempfile.TemporaryDirectory() as d:
            root,harvest,fp,rp,frozen,mp,rt=chapter_tests.ChapterTests().rejected_model_scope_fixture(Path(d))
            rows=[json.loads(x) for x in rp.read_text().splitlines() if x.strip()]
            write_jsonl(rp,rows[:1])
            with self.assertRaises(RecordError):check(root,harvest,mp)

    def test_attempt_metadata_hash_path_and_order_are_checked_by_original_parser(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,fp,rp,frozen,raw,mp,rt=fixture(Path(d))
            original=dict(path=rp.relative_to(root).as_posix(),hash=byte_hash(rp.read_bytes()),unit_ids=[raw[0]['unit_id']])
            for mutation in ('hash','path','ids','duplicate-file'):
                entry=copy.deepcopy(original)
                if mutation=='hash':entry['hash']='sha256:'+'0'*64
                elif mutation=='path':entry['path']='docs/evidence/outside.jsonl'
                elif mutation=='ids':entry['unit_ids']=frozen['unit_ids'][1:]
                attempts=[entry,entry] if mutation=='duplicate-file' else [entry]
                with self.subTest(mutation=mutation),self.assertRaises(RecordError):
                    _partial_unadopted_raw_inventory(root,frozen,attempts,json.loads(frozen['task']['scope_bytes']),InputSnapshot(root),[],[])


if __name__=='__main__':unittest.main()
