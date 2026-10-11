"""Independent synthetic list-bearing boundaries; never translation facts."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_preceding_statement_paragraphs import after_fixture
from test_source_container_boundaries import INTRO, PLAIN
from test_source_containers import selector
from test_group_derivations import commit, run_for, save, write
from stacks_zh.records import RecordError, stamp_unit_hashes, sha256_value
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import (Containers, load_source_containers,
    lower_container, verify_old_group, write_container_package)
from stacks_zh.source_reextractions import source_tex


def nested_fixture(base, *, nested=False, native=None):
    tail = ('\\item\n\\begin{itemize}\n\\item Second object.\n\\end{itemize}'
            if nested else '\\item Second object.')
    statement = ('\\begin{lemma}\n\\label{lemma-one}\nChoose two objects.\n'
                 '\\begin{enumerate}\n\\item First object.\n' + tail +
                 '\n\\end{enumerate}\n\\end{lemma}')
    root, harvest, original, plan, output = after_fixture(
        base, native=native or statement + '\n\n' + INTRO)
    first = copy.deepcopy(original[0])
    first['source_text'] = 'Choose two objects.'
    first['render']['suffix'] = '\n\\begin{enumerate}\n'
    item1 = copy.deepcopy(first)
    item1.update(unit_id='tag:0001:item001', node_kind='list_item', source_text='First object.')
    item1['render'] = {'prefix':'\\item ', 'suffix':'\n'}
    item2 = copy.deepcopy(item1)
    item2.update(unit_id='tag:0001:item002', source_text='Second object.')
    item2['render'] = {
        'prefix':'\\item\n\\begin{itemize}\n\\item ' if nested else '\\item ',
        'suffix':('\n\\end{itemize}' if nested else '')+'\n\\end{enumerate}\n\\end{lemma}\n'}
    units = [stamp_unit_hashes(u) for u in [first,item1,item2,*original[1:]]]
    data = json.loads(plan.read_text())
    data['groups'][0]['input_unit_ids'] = [u['unit_id'] for u in units[:3]]
    oldc = {c['unit_id']:c for c in map(json.loads,(root/data['candidates_file']).read_text().splitlines())}
    candidates=[]
    for u in units:
        c=copy.deepcopy(oldc.get(u['unit_id'],oldc[first['unit_id']]))
        c.update(unit_id=u['unit_id'],source_text_hash=u['source_text_hash'])
        c['context']['unit_id']=u['unit_id'];c['context_hash']=sha256_value(c['context'])
        candidates.append(c)
    save(root,data['units_file'],units);save(root,data['candidates_file'],candidates)
    write(root/'translation-data/runs/fixture-boundary-run.json',
          run_for(candidates,units[0]['source_commit'],'translation','fixture-boundary-run'))
    write(plan,data);commit(root)
    return root,harvest,units,plan,output


class NestedPrecedingParagraphTests(unittest.TestCase):
    def witness(self,containers,units,*,nested=True,selected=None,ids=None):
        selected=selected or containers.select(selector('paragraph',owner='0000'))
        paragraph=next(u for u in units if u['unit_id']=='label:test-lemma-one:intro')
        return verify_old_group(units,containers.english.tags,ids or [paragraph['unit_id']],selected,
            native_containers=containers,allow_preceding_paragraph=True,
            allow_nested_preceding_paragraph=nested)

    def test_complete_single_and_nested_list_chains_use_separate_permission(self):
        for nested in [False,True]:
            with tempfile.TemporaryDirectory() as tmp:
                root,harvest,units,_,_=nested_fixture(Path(tmp),nested=nested)
                c=Containers(root,harvest)
                with self.assertRaises(RecordError):self.witness(c,units,nested=False)
                a=self.witness(c,units)['paragraph_anchor']
                self.assertEqual(a['preceding_statement_input_unit_ids'],[u['unit_id'] for u in units[:3]])
                self.assertEqual(a['preceding_statement_list_closings'],
                                 ['itemize','enumerate'] if nested else ['enumerate'])
                chosen=c.select(selector('paragraph',owner='0000'))
                self.assertEqual(source_tex(lower_container(chosen,c.policy)[0]),chosen['fragment'])

    def test_no_missing_reordered_cross_scope_or_forged_closing_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,original,_,_=nested_fixture(Path(tmp),nested=True);c=Containers(root,harvest)
            faults=['missing-item','order','duplicate','parent','chapter','source','wrong-label',
                    'math-close','comment-close','unknown-close','trailing-prose','wrong-list-close',
                    'missing-inner-close','extra-close','unicode-close','fake-opening','math-change','paragraph-slice',
                    'paragraph-words','paragraph-unicode','paragraph-blank','paragraph-command']
            for fault in faults:
                units=copy.deepcopy(original);p=units[3]
                if fault=='missing-item':units.pop(1)
                if fault=='order':units[1:3]=units[1:3][::-1]
                if fault=='duplicate':units.insert(1,copy.deepcopy(units[1]))
                if fault=='parent':units[1]['parent_tag']='0001'
                if fault=='chapter':units[1]['chapter']='other'
                if fault=='source':units[1]['source_commit']='1'*40
                if fault=='wrong-label':units[0]['render']['prefix']='\\begin{lemma}\\label{test-lemma-two}'
                if fault=='math-close':units[2]['render']['suffix']='$'+units[2]['render']['suffix']+'$'
                if fault=='comment-close':units[2]['render']['suffix']='% forged\n'+units[2]['render']['suffix']
                if fault=='unknown-close':units[2]['render']['suffix']='\\unknownCommand'+units[2]['render']['suffix']
                if fault=='trailing-prose':units[2]['render']['suffix']+=' Added.'
                if fault=='wrong-list-close':units[2]['render']['suffix']=units[2]['render']['suffix'].replace('itemize','enumerate')
                if fault=='missing-inner-close':units[2]['render']['suffix']=units[2]['render']['suffix'].replace('\\end{itemize}','')
                if fault=='extra-close':units[2]['render']['suffix']='\\end{itemize}'+units[2]['render']['suffix']
                if fault=='unicode-close':units[2]['render']['suffix']=units[2]['render']['suffix'].replace('\\end{lemma}','\u00a0\\end{lemma}')
                if fault=='fake-opening':units[0]['render']['prefix']='$'+units[0]['render']['prefix']+'$'
                if fault=='math-change':p['placeholders']['MATH_0001']='$y$'
                if fault=='paragraph-slice':p['source_text']='paragraph with <MATH_0001>.'
                if fault=='paragraph-words':p['source_text']+=' Added.'
                if fault=='paragraph-unicode':p['source_text']=p['source_text'].replace(' ','\u00a0',1)
                if fault=='paragraph-blank':p['source_text']=p['source_text'].replace('paragraph','\n\nparagraph')
                if fault=='paragraph-command':p['render']['prefix']='\\unknownCommand '
                with self.subTest(fault=fault),self.assertRaises(RecordError):self.witness(c,units)

    def test_native_adjacency_unique_paragraph_and_syntax_remain_required(self):
        native=('\\begin{lemma}\\label{lemma-one}Choose two objects.'
                '\\begin{enumerate}\\item First object.\\item Second object.'
                '\\end{enumerate}\\end{lemma}')
        variants=[native+'\n\n'+INTRO+'\n\n'+INTRO,
                  native+'\n% intervening comment\n'+INTRO,
                  native+'\n\\begin{proof}Intervening.\\end{proof}\n'+INTRO,
                  native+'\n\\section{Other}\\label{lemma-two}\n'+INTRO,
                  native+'\n\n'+INTRO.replace('$x$','$\\text{unclassified prose}$')]
        for variant in variants:
            with tempfile.TemporaryDirectory() as tmp:
                root,harvest,units,_,_=nested_fixture(Path(tmp),native=variant)
                with self.subTest(native=variant),self.assertRaises(RecordError):
                    self.witness(Containers(root,harvest),units)

    def test_v6_packages_are_readonly_replayable_and_witness_tampering_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,plan,out=nested_fixture(Path(tmp),nested=True)
            before={p.relative_to(root):p.read_bytes() for p in (root/'translation-data').rglob('*') if p.is_file()}
            m=write_container_package(root,harvest,plan,out);self.assertEqual(m['state'],'PREPARED')
            stamps={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in out.iterdir() if p.is_file()}
            self.assertEqual(write_container_package(root,harvest,plan,out,check=True),m)
            self.assertEqual(stamps,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in out.iterdir() if p.is_file()})
            self.assertEqual(before,{p.relative_to(root):p.read_bytes() for p in (root/'translation-data').rglob('*') if p.is_file()})
            records=json.loads((out/'restorations.json').read_text())
            boundary=next(x for x in records if x['tool']['version']=='source-container-v6')
            for record in records:
                for role,name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                    p=root/record['files'][role]['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((out/name).read_bytes())
                write(root/f"translation-data/source-container-restorations/{record['restoration_id']}.json",record)
            self.assertEqual(load_source_containers(root,harvest)[1],[])
            p=root/f"translation-data/source-container-restorations/{boundary['restoration_id']}.json"
            for fault in ['downgrade','downgrade-without-field','missing-closing','reorder-closing','empty-closing',
                          'unexpected-close','false-hash','statement-hash','wrong-selector','partial-input','typed-unit']:
                b=copy.deepcopy(boundary);a=b['legacy_boundary_witness']['paragraph_anchor']
                if fault.startswith('downgrade'):b['tool']['version']='source-container-v5'
                if fault in ['downgrade-without-field','missing-closing']:a.pop('preceding_statement_list_closings')
                if fault=='reorder-closing':a['preceding_statement_list_closings'].reverse()
                if fault=='empty-closing':a['preceding_statement_list_closings']=[]
                if fault=='unexpected-close':a['preceding_statement_list_closings']=['proof']
                if fault=='false-hash':a['paragraph_signature_hash']='sha256:'+'0'*64
                if fault=='statement-hash':a['preceding_statement_signature_hash']='sha256:'+'0'*64
                if fault=='wrong-selector':a['preceding_statement_selector']['owner_tag']='0002'
                if fault=='partial-input':a['preceding_statement_input_unit_ids'].pop()
                if fault=='typed-unit':b['new_units'][0]['schema_version']=2
                write(p,b)
                with self.subTest(fault=fault):
                    self.assertTrue(load_source_containers(root,harvest)[1])
                    if fault in ['downgrade','missing-closing','unexpected-close','typed-unit']:
                        self.assertTrue(validate_named_schema(b,'source-container-restoration.schema.json','fixture'))

    def test_plain_preceding_and_old_schema_permissions_are_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=after_fixture(Path(tmp),native=PLAIN+'\n\n'+INTRO)
            c=Containers(root,harvest);old=self.witness(c,units,nested=False)
            self.assertEqual(old,self.witness(c,units))
            self.assertNotIn('preceding_statement_list_closings',old['paragraph_anchor'])


    def test_grouped_revision_requires_all_five_fields_and_full_old_inputs(self):
        from stacks_zh.group_derivations import FIELDS, replay_groups, revision_group
        from stacks_zh.records import load_jsonl, placeholder_names, sha256_value
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,plan,output=nested_fixture(Path(tmp),nested=True)
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
                    source_container_restoration_id=source['restoration_id'],model_correction_id='synthetic-nested-after-revision')
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
