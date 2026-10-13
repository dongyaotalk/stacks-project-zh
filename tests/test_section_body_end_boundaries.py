"""Independent synthetic Git histories; these are never actual model outputs."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_derivations import fixture as candidate_fixture
from test_group_derivations import commit, run_for, save, write
from test_source_containers import fixture as english_fixture, git, old_unit, selector
from stacks_zh.records import RecordError, load_jsonl, placeholder_names, sha256_value, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, load_source_containers, lower_container, verify_old_group, write_container_package
from stacks_zh.source_reextractions import source_tex

BODY = ('\\noindent\nFirst paragraph with $x$.\n\n'
        '\\medskip\\noindent\nSecond paragraph.\n\\begin{enumerate}\n'
        '\\item First item.\n\\item Second item.\n\\end{enumerate}\n')
NEXT = '\\section{Next}\\label{lemma-one}\n'


def fixture(base, *, native=BODY + NEXT):
    root, harvest, source = english_fixture(base, statement=native, proof='')
    units = [old_unit(source, 'tag:0000:title', 'section_title', 'Basics', '\\section{',
                      '}\n\\label{test-section-basic}\n\n'),
             old_unit(source, 'tag:0000:p001', 'paragraph', 'First paragraph with <MATH_0001>.',
                      '\\noindent\n', '\n\n'),
             old_unit(source, 'tag:0000:p002', 'paragraph', 'Second paragraph.',
                      '\\medskip\\noindent\n', '\n\\begin{enumerate}\n'),
             old_unit(source, 'tag:0000:item001', 'list_item', 'First item.', '\\item ', '\n'),
             old_unit(source, 'tag:0000:item002', 'list_item', 'Second item.', '\\item ', '\n\\end{enumerate}\n')]
    units[1]['placeholders'] = {'MATH_0001': '$x$'}
    units = [stamp_unit_hashes(u) for u in units]
    template = candidate_fixture()[2][0]
    candidates = []
    for u in units:
        context = {'unit_id':u['unit_id'], 'source_commit':source, 'prompt_version':'fixture', 'policy_revision':'fixture'}
        c = copy.deepcopy(template)
        c.update(unit_id=u['unit_id'], source_commit=source, source_text_hash=u['source_text_hash'],
                 context=context, context_hash=sha256_value(context), run_id='synthetic-section-body',
                 translation=''.join('<'+n+'>' for n in placeholder_names(u['source_text']))+'合成测试。',
                 allowed_english=[], term_occurrences=[], unknown_terms=[], notes=['Synthetic fixture only.'],
                 term_status='CLEAR', stage='TERM_OK', qa_status='PASS', publication_status='CANDIDATE')
        c['translation_hash'] = sha256_value(c['translation']); candidates.append(c)
    up='translation-data/units/test-body.jsonl'; cp='translation-data/candidates/fixture/test-body.jsonl'
    save(root,up,units);save(root,cp,candidates)
    write(root/'translation-data/runs/synthetic-section-body.json',run_for(candidates,source,'translation','synthetic-section-body'))
    git(root,'init','-q');commit(root)
    plan={'derivation_id':'synthetic-section-body-end','created_at':'2026-10-14T00:00:00Z',
          'units_file':up,'candidates_file':cp,'groups':[]}
    for name,ids,kind in [('title',[units[0]['unit_id']],'section_title'),('body',[u['unit_id'] for u in units[1:]],'prose_block')]:
        plan['groups'].append({'group_id':name,'input_unit_ids':ids,'identity_anchor':ids[0],
            'selector':selector(kind,owner='0000'),'layout':'whole','reason':'Complete synthetic Section body; no actual generation.'})
    path=root/'build/plan.json';write(path,plan)
    return root,harvest,units,path,root/'build/package'


class SectionBodyEndTests(unittest.TestCase):
    def witness(self,c,units,ids=None,enabled=True):
        selected=c.select(selector('prose_block',owner='0000'))
        return verify_old_group(units,c.english.tags,ids or [u['unit_id'] for u in units[1:]],selected,
                                native_containers=c,allow_section_body_end=enabled)

    @staticmethod
    def install(root,output,records):
        for record in records:
            for role in ['input_units','input_candidates']:
                destination=root/record['files'][role]['path'];destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes((output/('input-units.jsonl' if role=='input_units' else 'input-candidates.jsonl')).read_bytes())
            write(root/f"translation-data/source-container-restorations/{record['restoration_id']}.json",record)

    def test_complete_body_and_verified_title_namespace_with_old_permission_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp));c=Containers(root,harvest)
            w=self.witness(c,units)['section_body_anchor']
            self.assertEqual(w['body_input_unit_ids'],[u['unit_id'] for u in units[1:]])
            self.assertEqual(w['historical_body_signature_hash'],w['native_body_signature_hash'])
            self.assertEqual(w['following_section_title_selector']['owner_tag'],'0001')
            with self.assertRaises(RecordError):self.witness(c,units,enabled=False)
            selected=c.select(selector('prose_block',owner='0000'));new=lower_container(selected,c.policy)
            self.assertEqual(''.join(source_tex(u) for u in new),selected['fragment'])

    def test_complete_old_batch_order_owner_title_and_every_protected_byte_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp));c=Containers(root,harvest)
            for fault in ['missing','reverse','duplicate','partial-ids','source','parent','title','label','math','prose','suffix','extra']:
                bad=copy.deepcopy(units);ids=None
                if fault=='missing':bad.pop()
                if fault=='reverse':bad[1:]=bad[:0:-1]
                if fault=='duplicate':bad[-1]=copy.deepcopy(bad[-2])
                if fault=='partial-ids':ids=[u['unit_id'] for u in bad[1:-1]]
                if fault=='source':bad[-1]['source_commit']='0'*40
                if fault=='parent':bad[-1]['parent_tag']='0001'
                if fault=='title':bad[0]['source_text']='Changed title'
                if fault=='label':bad[0]['render']['suffix']+='\\label{test-lemma-two}'
                if fault=='math':bad[1]['placeholders']['MATH_0001']='$y$'
                if fault=='prose':bad[2]['source_text']='Changed prose.'
                if fault=='suffix':bad[-1]['render']['suffix']+='extra'
                if fault=='extra':
                    extra=copy.deepcopy(bad[1]);extra['unit_id']='tag:0000:p003';bad.append(extra)
                with self.subTest(fault=fault),self.assertRaises(RecordError):self.witness(c,bad,ids)

    def test_native_full_interval_unique_sections_comments_and_unknown_math(self):
        variants=[BODY.replace('$x$','$y$')+NEXT,
                  BODY.replace('Second paragraph.','Second paragraph changed.')+NEXT,
                  BODY.replace('Second paragraph.','Second paragraph.\n% extra comment')+NEXT,
                  BODY.replace('$x$',r'$\unknown{x}$')+NEXT,
                  BODY.replace('$x$',r'$\text{unclassified}$')+NEXT,
                  BODY+'\\begin{lemma}\\label{lemma-two}Extra.\\end{lemma}\n'+NEXT,
                  BODY+NEXT+BODY+'\\section{Third}\\label{lemma-two}\n']
        for native in variants:
            with tempfile.TemporaryDirectory() as tmp:
                root,harvest,units,_,_=fixture(Path(tmp),native=native)
                with self.subTest(native=native),self.assertRaises(RecordError):self.witness(Containers(root,harvest),units)

    def test_package_readonly_history_and_each_schema_valid_witness_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,plan,output=fixture(Path(tmp))
            original={p.relative_to(root):p.read_bytes() for p in (root/'translation-data').rglob('*') if p.is_file()}
            manifest=write_container_package(root,harvest,plan,output);self.assertEqual(manifest['state'],'PREPARED')
            stamps={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()}
            self.assertEqual(write_container_package(root,harvest,plan,output,check=True),manifest)
            self.assertEqual(stamps,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()})
            self.assertEqual(original,{p.relative_to(root):p.read_bytes() for p in (root/'translation-data').rglob('*') if p.is_file()})
            records=json.loads((output/'restorations.json').read_text());self.install(root,output,records)
            record=next(r for r in records if r['tool']['version']=='source-container-v12')
            self.assertFalse(validate_named_schema(record,'source-container-restoration.schema.json','synthetic'))
            self.assertFalse(load_source_containers(root,harvest)[1])
            path=root/f"translation-data/source-container-restorations/{record['restoration_id']}.json"
            anchor=record['legacy_boundary_witness']['section_body_anchor']
            for key,value in anchor.items():
                bad=copy.deepcopy(record);changed=bad['legacy_boundary_witness']['section_body_anchor']
                if isinstance(value,dict):changed[key]['owner_tag']='9999'
                elif isinstance(value,list):changed[key][0]='tag:9999:p001'
                elif key.endswith('hash'):changed[key]='sha256:'+'0'*64
                elif key.endswith('input_unit_id'):changed[key]='tag:9999:title'
                else:changed[key]='9999'
                self.assertFalse(validate_named_schema(bad,'source-container-restoration.schema.json','valid-shaped tamper'))
                write(path,bad)
                with self.subTest(key=key):self.assertTrue(any('legacy boundary witness differs' in e for e in load_source_containers(root,harvest)[1]))
            for version in range(1,12):
                bad=copy.deepcopy(record);bad['tool']['version']=f'source-container-v{version}';write(path,bad)
                with self.subTest(version=version):self.assertTrue(load_source_containers(root,harvest)[1])
            write(path,record);self.assertFalse(load_source_containers(root,harvest)[1])

    def test_complete_v4_groups_and_all_five_synthetic_fields_cannot_be_omitted(self):
        from stacks_zh.group_derivations import FIELDS,replay_groups,revision_group
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,plan,output=fixture(Path(tmp));write_container_package(root,harvest,plan,output)
            records=json.loads((output/'restorations.json').read_text());self.install(root,output,records)
            restored,errors=load_source_containers(root,harvest);self.assertFalse(errors)
            old=load_jsonl(output/'input-candidates.jsonl')
            record={k:records[0][k] for k in ['derivation_id','source_commit','origin_commit','created_at','files']};record['unit_groups']=[];corrections={}
            for source in records:
                group={k:source[k] for k in ['group_id','input_unit_ids','output_unit_ids','reason']}
                group.update(identity_anchor=group['input_unit_ids'][0],output_units=source['new_units'],
                             source_container_restoration_id=source['restoration_id'],model_correction_id='synthetic-v12-revision')
                record['unit_groups'].append(group)
                inputs=[u for u in units if u['unit_id'] in group['input_unit_ids']];candidates=[c for c in old if c['unit_id'] in group['input_unit_ids']]
                for u in source['new_units']:
                    raw=copy.deepcopy(candidates[0]);context={'revision_input':revision_group(record,group,inputs,candidates)}
                    raw.update(unit_id=u['unit_id'],context=context,context_hash=sha256_value(context),
                               translation=''.join('<'+n+'>' for n in placeholder_names(u['source_text']))+'合成测试。')
                    raw['translation_hash']=sha256_value(raw['translation'])
                    corrections[(group['model_correction_id'],u['unit_id'])]={'unit':u,'candidate':raw,
                        'record':{'derivation_ids':{u['unit_id']:record['derivation_id']},'source_commit':record['source_commit']}}
            tags=Containers(root,harvest).english.tags
            new,newc=replay_groups(record,units,old,corrections,None,restored,tags)
            self.assertEqual(len(new),2);self.assertTrue(all(c['publication_status']=='CANDIDATE' for c in newc))
            for u,candidate in zip(new,newc):
                for field in FIELDS:
                    self.assertEqual(candidate[field],corrections[('synthetic-v12-revision',u['unit_id'])]['candidate'][field])
            for key in corrections:
                for field in sorted(FIELDS):
                    bad=copy.deepcopy(corrections);bad[key]['candidate'].pop(field)
                    # The public loader validates Schema before this internal replay API.
                    with self.subTest(unit=key,field=field),self.assertRaises((RecordError,KeyError)):replay_groups(record,units,old,bad,None,restored,tags)
                bad=copy.deepcopy(corrections);bad[key]['candidate']['publication_status']='PUBLISHED'
                _,candidates=replay_groups(record,units,old,bad,None,restored,tags)
                self.assertTrue(all(c['publication_status']=='CANDIDATE' for c in candidates))
                for fault in ['old-units','old-candidates','missing']:
                    bad=copy.deepcopy(corrections)
                    if fault=='missing':bad.pop(key)
                    else:
                        raw=bad[key]['candidate'];field='source_units' if fault=='old-units' else 'candidates'
                        raw['context']['revision_input'][field].pop()
                        raw['context_hash']=sha256_value(raw['context'])
                    with self.subTest(unit=key,fault=fault),self.assertRaises(RecordError):replay_groups(record,units,old,bad,None,restored,tags)
