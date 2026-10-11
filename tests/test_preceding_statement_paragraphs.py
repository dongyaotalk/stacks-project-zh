"""Independent synthetic Git for after-statement paragraphs; no model output."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_source_container_boundaries import fixture, INTRO, PLAIN
from test_source_containers import selector
from test_group_derivations import commit, save, write
from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import (Containers, load_source_containers,
    lower_container, verify_old_group, write_container_package)
from stacks_zh.source_reextractions import source_tex


def after_fixture(base, *, native=None, split=False):
    root, harvest, units, plan, output = fixture(
        base, 'paragraph', statement=native or PLAIN + '\n\n' + INTRO)
    paragraph, statement = units[:2]
    units = [statement, paragraph]
    data = json.loads(plan.read_text())
    data['groups'] = [data['groups'][1], data['groups'][0]]
    if split:
        first = copy.deepcopy(statement)
        first['source_text'] = 'A complete'
        first['render']['suffix'] = ''
        last = copy.deepcopy(statement)
        last.update(unit_id='tag:0001:p001', node_kind='paragraph', source_text=' assertion.')
        last['render']['prefix'] = ''
        units[:1] = [stamp_unit_hashes(first), stamp_unit_hashes(last)]
        data['groups'][0]['input_unit_ids'] = [first['unit_id'], last['unit_id']]
    original_candidates = {c['unit_id']: c for c in map(json.loads, (root / data['candidates_file']).read_text().splitlines())}
    candidates = []
    for unit in units:
        candidate = copy.deepcopy(original_candidates.get(unit['unit_id'], original_candidates[statement['unit_id']]))
        candidate.update(unit_id=unit['unit_id'], source_text_hash=unit['source_text_hash'])
        # Synthetic package tests need each original candidate's input binding;
        # none of these fixtures assert an actual translation generation.
        candidate['context']['unit_id'] = unit['unit_id']
        from stacks_zh.records import sha256_value
        candidate['context_hash'] = sha256_value(candidate['context'])
        candidates.append(candidate)
    save(root, data['units_file'], units); save(root, data['candidates_file'], candidates)
    from test_group_derivations import run_for
    source = units[0]['source_commit']
    write(root / 'translation-data/runs/fixture-boundary-run.json',
          run_for(candidates, source, 'translation', 'fixture-boundary-run'))
    write(plan, data); commit(root)
    return root, harvest, units, plan, output


class PrecedingParagraphTests(unittest.TestCase):
    def witness(self, containers, units, selected=None, ids=None):
        selected = selected or containers.select(selector('paragraph', owner='0000'))
        paragraph = next(u for u in units if u['unit_id']=='label:test-lemma-one:intro')
        return verify_old_group(units, containers.english.tags, ids or [paragraph['unit_id']], selected,
            native_containers=containers, allow_preceding_paragraph=True)

    def test_complete_ordered_statement_and_whole_paragraph_are_required(self):
        for split in [False, True]:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = after_fixture(Path(tmp), split=split)
                containers = Containers(root, harvest); selected = containers.select(selector('paragraph', owner='0000'))
                paragraph = next(u for u in units if u['unit_id']=='label:test-lemma-one:intro')
                with self.assertRaises(RecordError):
                    verify_old_group(units, containers.english.tags, [paragraph['unit_id']], selected,
                                     native_containers=containers)
                witness = self.witness(containers, units, selected)['paragraph_anchor']
                self.assertEqual(witness['preceding_statement_input_unit_ids'],
                                 [u['unit_id'] for u in units[:2 if split else 1]])
                self.assertEqual(witness['preceding_statement_selector'], selector('lemma'))
                self.assertEqual(source_tex(lower_container(selected, containers.policy)[0]), selected['fragment'])

    def test_text_protected_bytes_and_full_old_scope_cannot_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, original, _, _ = after_fixture(Path(tmp), split=True)
            containers = Containers(root, harvest)
            for fault in ['words','slice','math','reference','command','unicode','blank','parent',
                          'owner','missing-statement','fake-prefix','fake-close','trailing-prose',
                          'chapter','source','order','duplicate','missing-tail','partial-paragraph','unknown']:
                units = copy.deepcopy(original); paragraph = units[2]; selected = None; ids = None
                if fault=='words': paragraph['source_text'] += ' Added.'
                if fault=='slice': paragraph['source_text'] = 'paragraph with <MATH_0001>.'
                if fault=='math': paragraph['placeholders']['MATH_0001'] = '$y$'
                if fault=='reference': paragraph['render']['suffix'] += '\\ref{test-lemma-one}'
                if fault=='command': paragraph['render']['prefix'] = '\\medskip\n'
                if fault=='unicode': paragraph['source_text'] = paragraph['source_text'].replace(' ', '\u00a0',1)
                if fault=='blank': paragraph['source_text'] = paragraph['source_text'].replace('paragraph','\n\nparagraph')
                if fault=='parent': paragraph['parent_tag']='0001'
                if fault=='owner': units[0]['render']['prefix']='\\begin{lemma}\\label{test-lemma-two}'
                if fault=='missing-statement': units=units[2:]
                if fault=='fake-prefix': units[0]['render']['prefix']='$\\begin{lemma}\\label{test-lemma-one}$'
                if fault=='fake-close': units[1]['render']['suffix']='$\\end{lemma}$'
                if fault=='trailing-prose': units[1]['render']['suffix']+=' Smuggled.'
                if fault=='chapter': paragraph['chapter']='other'
                if fault=='source': paragraph['source_commit']='1'*40
                if fault=='order': units[:2]=units[:2][::-1]
                if fault=='duplicate': units.insert(0,copy.deepcopy(units[0]))
                if fault=='missing-tail': units.pop(1)
                if fault=='partial-paragraph': ids=[units[0]['unit_id'],paragraph['unit_id']]
                if fault=='unknown': paragraph['render']['prefix']='\\unknownCommand '
                with self.subTest(fault=fault), self.assertRaises(RecordError):
                    self.witness(containers,units,selected,ids)

    def test_native_repeat_section_intervening_node_and_typed_math_are_rejected(self):
        variants=[PLAIN+'\n\n'+INTRO+'\n\n'+INTRO,
                  PLAIN+'\n\\section{Other}\\label{lemma-two}\n'+INTRO,
                  PLAIN+'\n\\begin{proof}An intervening proof.\\end{proof}\n'+INTRO,
                  PLAIN+'\n% Non-whitespace boundary.\n'+INTRO,
                  PLAIN+'\n\n'+INTRO.replace('$x$', '$\\text{unclassified prose}$')]
        for native in variants:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = after_fixture(Path(tmp), native=native)
                containers=Containers(root,harvest)
                with self.subTest(native=native), self.assertRaises(RecordError):
                    self.witness(containers,units)

    def test_v5_package_replays_and_rejects_schema_version_or_witness_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, plan, output = after_fixture(Path(tmp), split=True)
            before={p.relative_to(root):p.read_bytes() for p in (root/'translation-data').rglob('*') if p.is_file()}
            manifest=write_container_package(root,harvest,plan,output)
            self.assertEqual(manifest['state'],'PREPARED')
            stamps={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir() if p.is_file()}
            self.assertEqual(write_container_package(root,harvest,plan,output,check=True),manifest)
            self.assertEqual(stamps,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir() if p.is_file()})
            self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in (root/'translation-data').rglob('*') if p.is_file()})
            records=json.loads((output/'restorations.json').read_text())
            boundary=next(r for r in records if r['tool']['version']=='source-container-v5')
            self.assertEqual(boundary['input_unit_ids'],[units[2]['unit_id']])
            for record in records:
                for role,name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                    path=root/record['files'][role]['path'];path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes((output/name).read_bytes())
                write(root/f"translation-data/source-container-restorations/{record['restoration_id']}.json",record)
            self.assertEqual(load_source_containers(root,harvest)[1],[])
            path=root/f"translation-data/source-container-restorations/{boundary['restoration_id']}.json"
            for fault in ['missing','old-version','false-hash','wrong-selector','reorder','unexpected','typed-unit']:
                record=copy.deepcopy(boundary);anchor=record['legacy_boundary_witness']['paragraph_anchor']
                if fault=='missing': record.pop('legacy_boundary_witness')
                if fault=='old-version': record['tool']['version']='source-container-v4'
                if fault=='false-hash': anchor['paragraph_signature_hash']='sha256:'+'0'*64
                if fault=='wrong-selector': anchor['preceding_statement_selector']['owner_tag']='0002'
                if fault=='reorder': anchor['preceding_statement_input_unit_ids'].reverse()
                if fault=='unexpected': anchor['following_statement_selector']=selector('lemma')
                if fault=='typed-unit': record['new_units'][0]['schema_version']=2
                write(path,record)
                with self.subTest(fault=fault):
                    self.assertTrue(load_source_containers(root,harvest)[1])
                    if fault in {'missing','old-version','unexpected','typed-unit'}:
                        self.assertTrue(validate_named_schema(record,'source-container-restoration.schema.json','fixture'))

    def test_original_schema_branches_and_v4_direction_remain_unchanged(self):
        # Exercise the old after-paragraph statement contract independently.
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp),'paragraph')
            containers=Containers(root,harvest);selected=containers.select(selector('paragraph',owner='0000'))
            old=verify_old_group(units,containers.english.tags,[units[0]['unit_id']],selected,native_containers=containers)
            self.assertEqual(old,self.witness(containers,units,selected))
            self.assertIn('following_statement_selector',old['paragraph_anchor'])
            self.assertNotIn('preceding_statement_selector',old['paragraph_anchor'])

    def test_grouped_revision_requires_all_five_fields_and_full_old_inputs(self):
        from stacks_zh.group_derivations import FIELDS, replay_groups, revision_group
        from stacks_zh.records import load_jsonl, placeholder_names, sha256_value
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,plan,output=after_fixture(Path(tmp),split=True)
            self.assertEqual(write_container_package(root,harvest,plan,output)['state'],'PREPARED')
            records=json.loads((output/'restorations.json').read_text())
            for source in records:
                for role,name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                    path=root/source['files'][role]['path'];path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes((output/name).read_bytes())
                write(root/f"translation-data/source-container-restorations/{source['restoration_id']}.json",source)
            restored,errors=load_source_containers(root,harvest);self.assertEqual(errors,[])
            candidates=load_jsonl(output/'input-candidates.jsonl')
            record={k:records[0][k] for k in ['derivation_id','source_commit','origin_commit','created_at','files']}
            record['unit_groups']=[];corrections={}
            for source in records:
                group={k:source[k] for k in ['group_id','input_unit_ids','output_unit_ids','reason']}
                group.update(identity_anchor=group['input_unit_ids'][0],output_units=source['new_units'],
                    source_container_restoration_id=source['restoration_id'],model_correction_id='synthetic-after-revision')
                record['unit_groups'].append(group)
                old=[u for u in units if u['unit_id'] in group['input_unit_ids']]
                oldc=[c for c in candidates if c['unit_id'] in group['input_unit_ids']]
                for unit in group['output_units']:
                    raw=copy.deepcopy(oldc[0]);context={'revision_input':revision_group(record,group,old,oldc)}
                    raw.update(unit_id=unit['unit_id'],context=context,context_hash=sha256_value(context),
                        translation=''.join('<'+name+'>' for name in placeholder_names(unit['source_text']))+'合成测试。',
                        allowed_english=[],term_occurrences=[],unknown_terms=[],notes=['Synthetic test, never model output.'])
                    raw['translation_hash']=sha256_value(raw['translation'])
                    corrections[(group['model_correction_id'],unit['unit_id'])]={'unit':unit,'candidate':raw,
                        'record':{'derivation_ids':{unit['unit_id']:record['derivation_id']},'source_commit':record['source_commit']}}
            tags=Containers(root,harvest).english.tags
            new,newc=replay_groups(record,units,candidates,corrections,None,restored,tags)
            self.assertEqual(len(new),2);self.assertTrue(all(c['publication_status']=='CANDIDATE' for c in newc))
            key=next(k for k,v in corrections.items() if v['unit']['node_kind']=='paragraph')
            for fault in [*sorted(FIELDS),'missing-revision','partial-old-context','human-approval']:
                changed=copy.deepcopy(corrections)
                if fault in FIELDS:changed[key]['candidate'].pop(fault)
                if fault=='missing-revision':changed.pop(key)
                if fault=='partial-old-context':changed[key]['candidate']['context']['revision_input']['candidates'].clear()
                if fault=='human-approval':changed[key]['candidate']['stage']='MATH_REVIEWED'
                with self.subTest(fault=fault),self.assertRaises((RecordError,KeyError)):
                    replay_groups(record,units,candidates,changed,None,restored,tags)


if __name__=='__main__':
    unittest.main()
