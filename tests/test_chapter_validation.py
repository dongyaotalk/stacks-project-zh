"""Independent synthetic Git fixtures, real current/source/direct validators."""
import copy
import hashlib
import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from test_source_adoptions import synthetic_fixture, write
from test_source_containers import git
from stacks_zh.source_adoptions import assemble_source_adoption
from stacks_zh.source_containers import Containers, lower_container, clean
from stacks_zh.source_reextractions import byte_hash
from stacks_zh.records import write_jsonl, RecordError
from stacks_zh.chapter_validation import check_chapter
from stacks_zh.workflow import render_batch
from stacks_zh.ci_scope import classify


def fixture(base, *, interleaved=False):
    root,harvest,fp,rp,frozen,raw=synthetic_fixture(base)
    (root/'.gitignore').write_text('build/\npreview/\nsource-ir/\n')
    git(root,'add','.gitignore')
    git(root,'-c','user.name=Synthetic','-c','user.email=test@example.invalid','commit','-qm','Synthetic generated-output exclusions')
    origin=git(root,'rev-parse','HEAD');git(root,'update-ref','refs/heads/main',origin)
    native=Containers(root,harvest)
    selected={u['unit_id'] for b in frozen['batches'] for u in b['units']}
    for row in native.document('test')[1]:
        u=row['unit']
        span=row['location']
        if any(g['selected']['location']['byte_start'] <= span['byte_start'] and g['selected']['location']['byte_end'] >= span['byte_end'] for b in frozen['batches'] for g in b['containers']):continue
        # The native inventory ID is not the adopted unit ID. Re-select the
        # complete coordinate then lower through the actual accepted function.
        selector=dict(file='test.tex',owner_tag=row['owner_tag'],
                      owner_label=next(label for label,tag in native.english.tags.items() if tag==row['owner_tag']),
                      parent_tag=row['parent_tag'],kind=row['semantic_path'].rsplit('/',1)[0],
                      ordinal=int(row['semantic_path'].rsplit('/',1)[1]))
        group=native.select(selector);unit=clean(lower_container(group,native.policy)[0])
        if unit['unit_id'] in selected:continue
        selected.add(unit['unit_id'])
        if unit['node_kind']=='proof':
            b=next(b for b in frozen['batches'] if any(u['node_kind']=='lemma' for u in b['units']))
            b['units'].append(unit)
            b['containers'].append(dict(selector=selector,selected=group,unit_ids=[unit['unit_id']]))
        else:
            name='extra-'+str(len(frozen['batches']))
            up='translation-data/units/'+name+'.jsonl';cp='translation-data/candidates/synthetic/'+name+'.jsonl'
            frozen['batches'].append(dict(units_path=up,candidates_path=cp,units=[unit],containers=[dict(selector=selector,selected=group,unit_ids=[unit['unit_id']])],prior_attempts=[]))
        text=unit['source_text'].replace('Basics','基础').replace('Use ','使用').replace('Choose ','选择').replace('Another argument','另一论证').replace('and','且')
        raw.append(dict(unit_id=unit['unit_id'],translation=text,allowed_english=[],term_occurrences=[],unknown_terms=[],notes=['Synthetic literal only.']))
    # Keep packages in physical source order, with independent files per batch.
    frozen['batches'].sort(key=lambda b:b['containers'][0]['selected']['location']['byte_start'])
    if interleaved:
        last=frozen['batches'].pop()
        first=frozen['batches'][0]
        first['units'].extend(last['units'])
        first['containers'].extend(last['containers'])
        (root/last['units_path']).unlink(missing_ok=True)
    ids=[u['unit_id'] for b in frozen['batches'] for u in b['units']]
    raw.sort(key=lambda x:ids.index(x['unit_id']))
    frozen['unit_ids']=ids
    scope=json.loads(frozen['task']['scope_bytes'])
    files=[b[k] for b in frozen['batches'] for k in ('units_path','candidates_path')]
    scope['allowed_write_files']=list(dict.fromkeys(scope['allowed_write_files']+files))
    child=scope['data_scopes'][0]
    child['allowed_write_files']=list(dict.fromkeys(child['allowed_write_files']+files))
    for key in ('unit_ids','input_unit_ids','output_unit_ids'):child[key]=ids
    sp=root/frozen['task']['scope_manifest'];write(sp,scope)
    frozen['task'].update(scope_bytes=sp.read_text(),scope_manifest_sha256=byte_hash(sp.read_bytes()))
    for b in frozen['batches']:write_jsonl(root/b['units_path'],b['units'])
    write(fp,frozen);write_jsonl(rp,raw)
    assemble_source_adoption(root,fp,[rp],harvest)
    return root,harvest,origin,fp,rp,frozen


def preparation_copy(root, frozen, fp, rp):
    aid=frozen['adoption_id']
    mp=root/'docs/evidence'/f'{aid}-model-input.json'
    rt=root/'docs/evidence'/f'{aid}-runtime.json'
    scope=json.loads(frozen['task']['scope_bytes'])
    files=[p.relative_to(root).as_posix() for p in (mp,rt)]
    scope['allowed_write_files']=list(dict.fromkeys(scope['allowed_write_files']+files))
    scope['data_scopes'][0]['allowed_write_files']=list(dict.fromkeys(scope['data_scopes'][0]['allowed_write_files']+files))
    sp=root/frozen['task']['scope_manifest'];write(sp,scope)
    frozen['task'].update(scope_bytes=sp.read_text(),scope_manifest_sha256=byte_hash(sp.read_bytes()))
    write(fp,frozen)
    value=dict(generation_freeze=dict(path=fp.relative_to(root).as_posix(),hash=byte_hash(fp.read_bytes())),
        runtime=frozen['runtime'],scope_manifest=dict(path=frozen['task']['scope_manifest'],hash=frozen['task']['scope_manifest_sha256']),
        prompt=(root/'prompts/translator-v2.md').read_text(),style=(root/'config/style-guide.md').read_text(),
        glossary=(root/'config/glossary.yml').read_text(),source_units=[u for b in frozen['batches'] for u in b['units']],
        locked_english_contexts=frozen['contexts'],policy_git_origin=frozen['origin_commit'],policy_files=frozen['policies'],
        raw_output_paths_reserved=[rp.relative_to(root).as_posix()],rules='Synthetic preparation rules.')
    runtime=frozen['runtime']
    write(mp,value);write(rt,dict(runtime=runtime,provider=runtime['model']['provider'],
        turn_metadata=dict(turn_id=runtime['turn_id'],model=runtime['model']['requested_id'],effort=runtime['reasoning_effort']),
        harness_check=dict(exit_code=0,observed_version=runtime['harness']['version'])))
    return mp,rt


class ChapterTests(unittest.TestCase):
    def test_empty_glossary_inventory_is_bound_to_complete_locked_policy(self):
        from stacks_zh.chapter_relations import _model_policy_matches
        empty=b'entries: []\n'
        nonempty='entries:\n  - source_term: space\n    target_term: 空间\n    status: proposed\n'.encode('utf-8')
        # A proposed entry must not be discarded as though only approvals matter.
        for raw in (empty, nonempty):
            self.assertTrue(_model_policy_matches('glossary',raw.decode(),raw,byte_hash(raw)))
        self.assertTrue(_model_policy_matches('glossary',[],empty,byte_hash(empty)))
        for raw in (nonempty,b'entries:\n',b'entries: []\nentries: []\n',b'entries: {}\n'):
            with self.subTest(raw=raw):
                self.assertFalse(_model_policy_matches('glossary',[],raw,byte_hash(raw)))
        for field,value in [('prompt',[]),('style',[]),('glossary',{}),('glossary',None),
                            ('glossary','[]'),('glossary',[{}])]:
            with self.subTest(field=field,value=value):
                self.assertFalse(_model_policy_matches(field,value,empty,byte_hash(empty)))
        for value in ([],empty.decode()):
            self.assertFalse(_model_policy_matches('glossary',value,empty,byte_hash(nonempty)))

    def test_chapter_accepts_empty_glossary_copy_without_changing_generation(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            mp,rt=preparation_copy(root,frozen,fp,rp)
            for p in [root/'translation-data/source-adoptions/synthetic-first.json',root/'translation-data/runs/run-synthetic-first.json']:
                p.unlink()
            for b in frozen['batches']:(root/b['candidates_path']).unlink()
            value=json.loads(mp.read_text());value['glossary']=[];write(mp,value)
            assemble_source_adoption(root,fp,[rp],harvest)
            before={p:p.read_bytes() for p in (mp,rt,fp,rp)}
            result=check_chapter(root,harvest,'test','synthetic',base)
            self.assertEqual(result.report['preparations'][0]['status'],'adopted-input-copy-verified')
            self.assertEqual(before,{p:p.read_bytes() for p in before})

    def test_current_all_rejects_unpaired_unit_schema_and_missing_candidate(self):
        from stacks_zh.chapter_validation import check_current_repository
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            row=copy.deepcopy(frozen['batches'][0]['units'][0])
            row.update(unit_id='tag:ZZZZ:unpaired',chapter='unpaired',not_in_schema=True)
            path=root/'translation-data/units/unpaired.jsonl'
            write_jsonl(path,[row])
            with self.assertRaisesRegex(RecordError,'schema'):
                check_current_repository(root,harvest,base)
            del row['not_in_schema'];write_jsonl(path,[row])
            with self.assertRaisesRegex(RecordError,'no candidate pair'):
                check_current_repository(root,harvest,base)
            path.unlink()
            self.assertEqual(check_current_repository(root,harvest,base)['exit_status'],0)

    def test_preparation_copies_and_unadopted_inventory_do_not_confer_adoption(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            mp,rt=preparation_copy(root,frozen,fp,rp)
            for p in [root/'translation-data/source-adoptions/synthetic-first.json',root/'translation-data/runs/run-synthetic-first.json']:
                p.unlink()
            for b in frozen['batches']:(root/b['candidates_path']).unlink()
            assemble_source_adoption(root,fp,[rp],harvest)
            result=check_chapter(root,harvest,'test','synthetic',base)
            self.assertEqual(result.report['preparations'][0]['status'],'adopted-input-copy-verified')
            # A separate unadopted preparation cannot provide any current row.
            proposal=copy.deepcopy(frozen);proposal.update(adoption_id='synthetic-unused',run_id='run-synthetic-unused')
            scope=json.loads(proposal['task']['scope_bytes'])
            extra=['translation-data/source-adoption-inputs/synthetic-unused.json','translation-data/source-adoptions/synthetic-unused.json','translation-data/runs/run-synthetic-unused.json','docs/evidence/synthetic-unused-model-input.json','docs/evidence/synthetic-unused-runtime.json']
            scope['allowed_write_files']+=extra;scope['data_scopes'][0]['allowed_write_files']+=extra
            scope['data_scopes'][0]['run_scope'].append('run-synthetic-unused')
            sp=root/proposal['task']['scope_manifest'];write(sp,scope)
            proposal['task'].update(scope_bytes=sp.read_text(),scope_manifest_sha256=byte_hash(sp.read_bytes()))
            unused=root/extra[0]
            preparation_copy(root,proposal,unused,rp)
            result=check_chapter(root,harvest,'test','synthetic',base)
            status={Path(x['input']).stem:x for x in result.report['preparations']}
            self.assertEqual(status['synthetic-unused']['generation_validation'],'not_claimed')
            self.assertFalse(status['synthetic-unused']['run_created'])
            self.assertEqual(result.report['direct_nodes'],1)

    def test_preparation_copy_runtime_scope_and_terms_tampering(self):
        from stacks_zh.chapter_relations import check_preparation_evidence
        from stacks_zh.current_qa import InputSnapshot
        from stacks_zh.validation_io import InputReads
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            mp,rt=preparation_copy(root,frozen,fp,rp)
            (root/'translation-data/runs/run-synthetic-first.json').unlink()
            originals={p:p.read_bytes() for p in (mp,rt,fp,rp)}
            for mutation in ('model-input','runtime','freeze','raw','scope','terms'):
                with self.subTest(mutation=mutation):
                    for p,raw in originals.items():p.write_bytes(raw)
                    if mutation in ('model-input','scope','terms'):
                        v=json.loads(mp.read_text())
                        if mutation=='model-input':v['source_units']=[]
                        if mutation=='scope':v['raw_output_paths_reserved']=['docs/evidence/outside.jsonl']
                        if mutation=='terms':v['required_source_occurrences']=[]
                        write(mp,v)
                    if mutation=='runtime':
                        v=json.loads(rt.read_text());v['turn_metadata']['model']='wrong';write(rt,v)
                    if mutation=='freeze':fp.write_bytes(originals[fp]+b'\n')
                    if mutation=='raw':rp.write_text('{}\n')
                    reads=InputReads()
                    with reads.activate():
                        # Leave adoption absent so this exercises raw preparation.
                        adoption=root/'translation-data/source-adoptions/synthetic-first.json'
                        raw=adoption.read_bytes() if adoption.exists() else None
                        if raw is not None:adoption.unlink()
                        try:
                            with self.assertRaises((RecordError,KeyError)):
                                check_preparation_evidence(root,harvest,InputSnapshot(root),[mp.relative_to(root).as_posix()],'test','synthetic',reads,Containers(root,harvest))
                        finally:
                            if raw is not None:adoption.write_bytes(raw)

    def test_rejected_preparation_keeps_source_errors_and_rejection_bindings(self):
        from stacks_zh.chapter_relations import check_preparation_evidence
        from stacks_zh.current_qa import InputSnapshot
        from stacks_zh.validation_io import InputReads
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            (root/'translation-data/source-adoptions/synthetic-first.json').unlink()
            (root/'translation-data/runs/run-synthetic-first.json').unlink()
            frozen['batches'][0]['containers'][0]['selected']['saved_summary']='incomplete-native-view'
            mp,rt=preparation_copy(root,frozen,fp,rp)
            rejection=mp.with_name(mp.name.replace('-model-input','-preparation-rejection'))
            value=dict(kind='rejected-unadopted-generation-preparation',adoption_id_requested=frozen['adoption_id'],
                run_id_requested=frozen['run_id'],candidate_installed=False,run_manifest_created=False,source_adoption_created=False,
                failure_stage='complete-native-selector-freeze',observed_assembly_exit_code=1,
                observed_assembly_error='ERROR: first adoption container differs from its real complete Git selector',
                input=dict(path=fp.relative_to(root).as_posix(),hash=byte_hash(fp.read_bytes())),
                runtime=dict(path=rt.relative_to(root).as_posix(),hash=byte_hash(rt.read_bytes())),
                model_input=dict(path=mp.relative_to(root).as_posix(),hash=byte_hash(mp.read_bytes())),
                raw_attempts=[dict(path=rp.relative_to(root).as_posix(),hash=byte_hash(rp.read_bytes()))])
            write(rejection,value)
            def check():
                reads=InputReads()
                with reads.activate():
                    return check_preparation_evidence(root,harvest,InputSnapshot(root),[mp.relative_to(root).as_posix()],'test','synthetic',reads,Containers(root,harvest))
            result=check()
            self.assertEqual(result[0]['status'],'rejected-unadopted-preparation')
            self.assertTrue(result[0]['source_errors'])
            value['raw_attempts'][0]['hash']='sha256:'+'0'*64;write(rejection,value)
            with self.assertRaises(RecordError):check()

    def rejected_model_scope_fixture(self, directory):
        root,harvest,base,fp,rp,frozen=fixture(directory)
        (root/'translation-data/source-adoptions/synthetic-first.json').unlink()
        (root/'translation-data/runs/run-synthetic-first.json').unlink()
        for batch in frozen['batches']:(root/batch['candidates_path']).unlink()
        models=root/'config/models.yml'
        models.write_text(models.read_text().replace('model_id: synthetic\n','model_id: synthetic-model\n')
            .replace('requested_id: synthetic\n','requested_id: synthetic-model\n')
            .replace('resolved_id: synthetic\n','resolved_id: synthetic-model\n'))
        git(root,'add','config/models.yml')
        git(root,'-c','user.name=Synthetic','-c','user.email=test@example.invalid','commit','-qm','Synthetic accepted concrete model registry')
        origin=git(root,'rev-parse','HEAD');git(root,'update-ref','refs/heads/main',origin)
        frozen['origin_commit']=origin
        frozen['runtime']['model'].update(requested_id='synthetic-model',resolved_id='synthetic-model')
        frozen['policies']=[dict(path=e['path'],hash=byte_hash((root/e['path']).read_bytes())) for e in frozen['policies']]
        scope=json.loads(frozen['task']['scope_bytes']);scope['data_scopes'][0]['model_scope']=['synthetic']
        sp=root/frozen['task']['scope_manifest'];write(sp,scope)
        frozen['task'].update(scope_bytes=sp.read_text(),scope_manifest_sha256=byte_hash(sp.read_bytes()))
        mp,rt=preparation_copy(root,frozen,fp,rp)
        return root,harvest,fp,rp,frozen,mp,rt

    def test_rejected_unadopted_model_scope_is_negative_inventory_only(self):
        from stacks_zh.chapter_relations import check_preparation_evidence
        from stacks_zh.current_qa import InputSnapshot
        from stacks_zh.validation_io import InputReads
        from stacks_zh.source_adoptions import _task_scope,Reads
        with tempfile.TemporaryDirectory() as d:
            root,harvest,fp,rp,frozen,mp,rt=self.rejected_model_scope_fixture(Path(d))
            before={p:p.read_bytes() for p in (fp,rp,mp,rt,root/frozen['task']['scope_manifest'])}
            entry=json.loads(mp.read_text())['generation_freeze']
            with self.assertRaises(RecordError):_task_scope(frozen,Reads(root),entry,current=False)
            reads=InputReads()
            with reads.activate():
                result=check_preparation_evidence(root,harvest,InputSnapshot(root),[mp.relative_to(root).as_posix()],
                    'test','synthetic',reads,Containers(root,harvest))
            self.assertEqual(result[0]['status'],'rejected-unadopted-preparation')
            self.assertEqual(result[0]['generation_validation'],'not_claimed')
            self.assertEqual(result[0]['scope_errors'],['first-source runtime or semantic coordinates escape the frozen task scope'])
            self.assertEqual(before,{p:p.read_bytes() for p in before})
            self.assertFalse((root/'translation-data/runs/run-synthetic-first.json').exists())

    def test_other_rejected_preparation_scope_or_identity_defects_still_fail(self):
        from stacks_zh.chapter_relations import check_preparation_evidence
        from stacks_zh.current_qa import InputSnapshot
        from stacks_zh.validation_io import InputReads
        for mutation in ('parent','chapter','run','model_scope','scope_file','registry','unknown','runtime','raw','installed_run','installed_adoption','installed_candidate','unaccepted_origin'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                root,harvest,fp,rp,frozen,mp,rt=self.rejected_model_scope_fixture(Path(d))
                sp=root/frozen['task']['scope_manifest'];scope=json.loads(sp.read_text());child=scope['data_scopes'][0]
                if mutation=='parent':child['parent_tags']=['9999']
                elif mutation=='chapter':child['chapter']='wrong'
                elif mutation=='run':child['run_scope']=['wrong']
                elif mutation=='model_scope':child['model_scope']=['unrelated-model']
                elif mutation=='registry':frozen['runtime']['model'].update(requested_id='unregistered',resolved_id='unregistered')
                elif mutation=='unknown':frozen['runtime']['model']['identity_confidence']='unknown'
                if mutation in ('parent','chapter','run','model_scope'):
                    write(sp,scope);frozen['task'].update(scope_bytes=sp.read_text(),scope_manifest_sha256=byte_hash(sp.read_bytes()))
                mp,rt=preparation_copy(root,frozen,fp,rp)
                if mutation=='scope_file':sp.write_bytes(sp.read_bytes()+b'\n')
                elif mutation=='runtime':v=json.loads(rt.read_text());v['turn_metadata']['model']='wrong';write(rt,v)
                elif mutation=='raw':rp.write_text('{}\n')
                elif mutation=='installed_run':write(root/'translation-data/runs/run-synthetic-first.json',{})
                elif mutation=='installed_adoption':write(root/'translation-data/source-adoptions/synthetic-first.json',{})
                elif mutation=='installed_candidate':write_jsonl(root/frozen['batches'][0]['candidates_path'],[dict(run_id=frozen['run_id'])])
                elif mutation=='unaccepted_origin':git(root,'update-ref','-d','refs/heads/main')
                reads=InputReads()
                with reads.activate():
                    with self.assertRaises(RecordError):
                        check_preparation_evidence(root,harvest,InputSnapshot(root),[mp.relative_to(root).as_posix()],
                            'test','synthetic',reads,Containers(root,harvest))

    def test_unadopted_shards_and_partial_retries_keep_complete_raw_union_gates(self):
        from stacks_zh.chapter_relations import check_preparation_evidence
        from stacks_zh.current_qa import InputSnapshot
        from stacks_zh.validation_io import InputReads
        for mutation in ('valid','missing','duplicate','outside','schema'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                root,harvest,fp,rp,frozen,mp,rt=self.rejected_model_scope_fixture(Path(d))
                records=[json.loads(x) for x in rp.read_text().splitlines() if x.strip()]
                midpoint=len(records)//2
                second=rp.with_name('synthetic-second-raw.jsonl');retry=rp.with_name('synthetic-retry-raw.jsonl')
                write_jsonl(rp,records[:midpoint]);tail=copy.deepcopy(records[midpoint:])
                if mutation=='missing':tail=tail[:-1]
                elif mutation=='duplicate':tail.append(copy.deepcopy(tail[0]))
                elif mutation=='outside':tail[0]['unit_id']='tag:9999:statement'
                elif mutation=='schema':tail[0].pop('notes')
                write_jsonl(second,tail);write_jsonl(retry,[records[0]])
                scope=json.loads(frozen['task']['scope_bytes']);paths=[p.relative_to(root).as_posix() for p in (second,retry)]
                scope['allowed_write_files']+=paths;scope['data_scopes'][0]['allowed_write_files']+=paths
                sp=root/frozen['task']['scope_manifest'];write(sp,scope)
                frozen['task'].update(scope_bytes=sp.read_text(),scope_manifest_sha256=byte_hash(sp.read_bytes()))
                mp,rt=preparation_copy(root,frozen,fp,rp)
                model_input=json.loads(mp.read_text());model_input['raw_output_paths_reserved']+=paths;write(mp,model_input)
                reads=InputReads()
                with reads.activate():
                    def check():return check_preparation_evidence(root,harvest,InputSnapshot(root),[mp.relative_to(root).as_posix()],
                        'test','synthetic',reads,Containers(root,harvest))
                    if mutation=='valid':
                        result=check();self.assertEqual(result[0]['generation_validation'],'not_claimed')
                        self.assertEqual(result[0]['status'],'rejected-unadopted-preparation')
                    else:
                        with self.assertRaises(RecordError):check()

    def test_rejected_preparation_schema_origin_requires_complete_accepted_policy_set(self):
        from stacks_zh.chapter_relations import check_preparation_evidence
        from stacks_zh.current_qa import InputSnapshot
        from stacks_zh.validation_io import InputReads
        for mutation in ('valid','unsupported_policy','unaccepted_schema','unknown_hash','scope_file'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                root,harvest,fp,rp,frozen,mp,rt=self.rejected_model_scope_fixture(Path(d))
                origin=frozen['origin_commit']
                relative='config/glossary.yml' if mutation=='unsupported_policy' else 'schema/unit.schema.json'
                path=root/relative;path.write_bytes(path.read_bytes()+b'\n')
                if mutation!='unaccepted_schema':
                    git(root,'add',relative)
                    git(root,'-c','user.name=Synthetic','-c','user.email=test@example.invalid','commit','-qm','Synthetic accepted policy bytes')
                    git(root,'update-ref','refs/heads/main',git(root,'rev-parse','HEAD'))
                for e in frozen['policies']:
                    if e['path']==relative:e['hash']=byte_hash(path.read_bytes()) if mutation!='unknown_hash' else 'sha256:'+'0'*64
                mp,rt=preparation_copy(root,frozen,fp,rp)
                if mutation=='scope_file':
                    sp=root/frozen['task']['scope_manifest'];sp.write_bytes(sp.read_bytes()+b'\n')
                before=fp.read_bytes();reads=InputReads()
                with reads.activate():
                    def check():return check_preparation_evidence(root,harvest,InputSnapshot(root),[mp.relative_to(root).as_posix()],
                        'test','synthetic',reads,Containers(root,harvest))
                    if mutation=='valid':
                        result=check()[0]
                        self.assertEqual(result['policy_errors'],['preparation policy differs from accepted origin'])
                        self.assertEqual(result['source_schema_witness'],git(root,'rev-parse','HEAD'))
                        self.assertEqual(result['generation_validation'],'not_claimed')
                        self.assertEqual(json.loads(fp.read_text())['origin_commit'],origin)
                        self.assertEqual(fp.read_bytes(),before)
                    else:
                        with self.assertRaises(RecordError):check()

    def test_pure_legacy_zeroth_projection_needs_exact_prefix_code_and_metadata(self):
        from stacks_zh import chapter_relations as relations
        from stacks_zh.current_qa import InputSnapshot
        from stacks_zh.source_terms import source_inventory
        from test_source_terms import unit as term_unit, catalog as term_catalog
        function='def _qualified_declaration_parts(body, unit):\n    return None\n'
        fingerprint=hashlib.sha256(function.rstrip('\n').encode()).hexdigest()
        for mutation in ('valid','metadata','accent','unknown_code','raw_present','installed_run'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                root,harvest,fp,rp,frozen,mp,rt=self.rejected_model_scope_fixture(Path(d))
                (root/'stacks_zh').mkdir(exist_ok=True)
                (root/'stacks_zh/source_terms.py').write_text(function)
                git(root,'add','stacks_zh/source_terms.py')
                git(root,'-c','user.name=Synthetic','-c','user.email=test@example.invalid','commit','-qm','Synthetic recognized original projection code')
                frozen['origin_commit']=git(root,'rev-parse','HEAD');git(root,'update-ref','refs/heads/main',frozen['origin_commit'])
                if mutation!='raw_present':rp.unlink()
                row=term_unit('The <TEXTITOPEN_0001>zeroth <GROUPOPEN_0002><ACCENT_0003><GROUPCLOSE_0002>ech cohomology group<TEXTITCLOSE_0001>.',
                    dict(TEXTITOPEN_0001='{\\it ',TEXTITCLOSE_0001='}',GROUPOPEN_0002='{',ACCENT_0003=r'\v C',GROUPCLOSE_0002='}'))
                expected=[source_inventory(row,term_catalog(row))]
                observed=copy.deepcopy(expected)
                declaration=next(r for r in observed[0]['occurrences'] if r['source_term']=='cohomology group')
                declaration.update(source_term='ech cohomology group',concept='ech cohomology group',projection_start=declaration['projection_start']-4)
                if mutation=='metadata':observed[0]['source_text_hash']='sha256:'+'0'*64
                elif mutation=='accent':row['placeholders']['ACCENT_0003']=r'\v D'
                elif mutation=='installed_run':write(root/'translation-data/runs/run-synthetic-first.json',{})
                with patch.object(relations,'_LEGACY_QUALIFIED_DECLARATION_SHA256',fingerprint if mutation!='unknown_code' else '0'*64):
                    def check():return relations._legacy_zeroth_preparation_projection(root,frozen,[row],expected,observed,
                        [rp.relative_to(root).as_posix()],InputSnapshot(root))
                    if mutation=='installed_run':
                        with self.assertRaises(RecordError):check()
                    else:self.assertEqual(check(),mutation=='valid')

    def test_cached_input_bytes_still_reject_changed_and_restored_observed_reads(self):
        from stacks_zh.current_qa import InputSnapshot
        from stacks_zh.chapter_validation import AdoptionBoundary,Base
        from stacks_zh import source_adoptions
        from stacks_zh.validation_io import InputReads,read_bytes
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            snapshot=InputSnapshot(root);boundary=AdoptionBoundary(Base(root,base,snapshot),lambda x:None)
            reads=InputReads();token=source_adoptions._DAILY.set(boundary)
            try:
                with reads.activate():
                    original=snapshot.read(rp)
                    self.assertEqual(snapshot.read(rp),original)
                    try:
                        rp.write_bytes(original+b'\n')
                        with self.assertRaises(RecordError):read_bytes(rp)
                    finally:rp.write_bytes(original)
                snapshot.assert_unchanged()
            finally:source_adoptions._DAILY.reset(token)
            boundary.finish()

    def test_joined_current_check_has_no_early_render_receipt_and_rechecks_inputs(self):
        from stacks_zh import chapter_validation
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            seen=[]
            def observed(*args,**kwargs):
                result=check_chapter(*args,**kwargs)
                with self.assertRaisesRegex(RecordError,'live chapter check'):
                    result.assert_valid(root,harvest)
                seen.append(result)
                return result
            with patch.object(chapter_validation,'check_chapter',side_effect=observed):
                report=chapter_validation.check_current_repository(root,harvest,base)
            self.assertEqual(len(seen),1)
            self.assertEqual(report['scope'],'current-all')
            self.assertEqual(report['chapters'][0]['validation_state'],'validated_current')
            scoped=chapter_validation.check_current_repository(root,harvest,base,chapters={'test'})
            self.assertEqual(scoped['scope'],'chapter-current')
            def changed(*args,**kwargs):
                result=check_chapter(*args,**kwargs)
                rp.write_bytes(rp.read_bytes()+b'\n')
                return result
            with patch.object(chapter_validation,'check_chapter',side_effect=changed):
                with self.assertRaises(RecordError):
                    chapter_validation.check_current_repository(root,harvest,base)

    def test_current_decisions_enumerate_candidate_names_once_and_detect_other_lane_duplicate(self):
        from stacks_zh import decisions
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            pairs=[(root/b['units_path'],root/b['candidates_path']) for b in frozen['batches']]
            with patch.object(decisions,'_input_glob',wraps=decisions._input_glob) as paths:
                self.assertEqual(decisions.validate_current_decisions(root,harvest,pairs,base=None),[])
            queries=[call for call in paths.call_args_list if call.args[0]==root/'translation-data/candidates']
            self.assertEqual(len(queries),1)
            self.assertEqual(queries[0].args[1],'*/*.jsonl')
            cp=pairs[0][1];other=cp.parent.parent/'other-lane'/cp.name
            other.parent.mkdir();other.write_bytes(cp.read_bytes())
            errors=decisions.validate_current_decisions(root,harvest,pairs,base=None)
            self.assertTrue(any('duplicate candidate identity' in error for error in errors))

    def test_direct_context_reuse_requires_exact_actual_value(self):
        from stacks_zh import source_adoptions as a
        from stacks_zh.chapter_validation import Base,AdoptionBoundary
        from stacks_zh.current_qa import InputSnapshot
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            native=Containers(root,harvest)
            expected=a._context_sources(frozen,native)
            boundary=AdoptionBoundary(Base(root,base,InputSnapshot(root)),lambda x:None)
            token=a._DAILY.set(boundary)
            try:
                with patch.object(a,'_context_sources_full',wraps=a._context_sources_full) as replay:
                    self.assertEqual(a._context_sources(frozen,native),expected)
                    count=replay.call_count
                    self.assertEqual(a._context_sources(frozen,native),expected)
                    self.assertEqual(replay.call_count,count)
                    bad=copy.deepcopy(frozen)
                    bad['contexts'][0]['value']['location']['fragment_hash']='sha256:'+'0'*64
                    with self.assertRaises(RecordError):a._context_sources(bad,native)
            finally:a._DAILY.reset(token)

    def test_receipt_rechecks_shared_bytes_once_and_rejects_removed_claims(self):
        from stacks_zh.validation_io import InputReads
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            result=check_chapter(root,harvest,'test','synthetic',base)
            original=Path.read_bytes;calls=[]
            def observed(path):
                if path.resolve()==rp.resolve():calls.append(path)
                return original(path)
            with patch.object(Path,'read_bytes',observed):result.assert_valid(root,harvest)
            self.assertEqual(len(calls),1)
            path=next(iter(result.current._reads.hashes))
            result.current._reads.hashes.pop(path)
            with self.assertRaises(RecordError):result.assert_valid(root,harvest)
            a,b=InputReads(),InputReads();a.hashes[rp]='a';b.hashes[rp]='b'
            with self.assertRaises(RecordError):a.include(b)

    def test_interleaved_files_render_each_unit_in_actual_source_order(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d),interleaved=True)
            result=check_chapter(root,harvest,'test','synthetic',base)
            manifest=root/'build/chapters.tex';manifest.parent.mkdir(exist_ok=True)
            manifest.write_text('\\item \\hyperref[test-section-phantom]{Synthetic}\n')
            from stacks_zh import workflow
            original=workflow.restore_placeholders
            seen=[]
            def observed(unit,*args,**kwargs):
                seen.append(unit['unit_id'])
                return original(unit,*args,**kwargs)
            with patch('stacks_zh.workflow.restore_placeholders',side_effect=observed):
                render_batch([u for u,c in result.pairs],[c for u,c in result.pairs],root/'upstream.lock',root/'preview/synthetic-chapter-test','synthetic','Synthetic',chapter_manifest_path=manifest,chapter_source_dir=harvest,chapter='test',_validation=result,harvest=harvest)
            expected=[unit['unit_id'] for _,unit in sorted(zip(result.current._pair_locations,
                (u for up,cp in result.pairs for u in result.snapshot.jsonl(up)),strict=True),key=lambda x:x[0])]
            self.assertEqual(seen,expected)

    def test_complete_current_direct_and_one_render_no_history(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            from stacks_zh import chapter_relations, source_adoptions
            direct=chapter_relations.check_derivations
            def bounded_derivations(*args,**kwargs):
                self.assertIsNotNone(source_adoptions._DAILY.get())
                return direct(*args,**kwargs)
            with patch('stacks_zh.repository_validation._complete_provenance',side_effect=AssertionError('implicit history')),patch('stacks_zh.source_adoptions.load_repository_source_adoptions',side_effect=AssertionError('implicit history')):
                with patch.object(chapter_relations,'check_derivations',side_effect=bounded_derivations):
                    result=check_chapter(root,harvest,'test','synthetic',base)
                self.assertEqual(result.count,5)
                self.assertEqual(result.report['history_audit'],'not_run')
                manifest=root/'build/chapters.tex';manifest.parent.mkdir(exist_ok=True);manifest.write_text('\\item \\hyperref[test-section-phantom]{Synthetic}\n')
                render_batch([u for u,c in result.pairs],[c for u,c in result.pairs],root/'upstream.lock',root/'preview/synthetic-chapter-test','synthetic','Synthetic',chapter_manifest_path=manifest,chapter_source_dir=harvest,chapter='test',_validation=result,harvest=harvest)
                with self.assertRaises(RecordError):replace(result).assert_valid(root,harvest)
                object.__setattr__(result,'lane','fake')
                with self.assertRaisesRegex(RecordError,'changed'):result.assert_valid(root,harvest)

    def _reject_mutations(self, mutations):
        for mutation in mutations:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                root,harvest,base,fp,rp,frozen=fixture(Path(d))
                cp=root/frozen['batches'][-1]['candidates_path'];up=root/frozen['batches'][-1]['units_path']
                if mutation=='missing':cp.unlink()
                if mutation=='duplicate':(root/'translation-data/units/duplicate.jsonl').write_bytes(up.read_bytes())
                if mutation in ('lane','run','token','term'):
                    rows=[json.loads(x) for x in cp.read_text().splitlines()]
                    if mutation=='lane':rows[0]['model_lane']='wrong'
                    if mutation=='run':rows[0]['run_id']='wrong'
                    if mutation=='token':rows[0]['translation']+='<MATH_9999>'
                    if mutation=='term':rows[0]['term_occurrences']=[dict(source_term='category',target_term='bad')]
                    write_jsonl(cp,rows)
                if mutation=='raw':rp.write_text(rp.read_text()+'\n{}\n')
                if mutation=='freeze':fp.write_text(fp.read_text().replace('synthetic-only','tampered'))
                if mutation=='source':up.write_text(up.read_text().replace('source_text','bad_source_text'))
                if mutation=='hidden':(root/'translation-data/.hidden.json').write_text('{}')
                if mutation=='unknown':(root/'unknown-policy').write_text('unknown')
                if mutation=='base':base='0'*40
                with self.assertRaises((RecordError,KeyError,ValueError,OSError)):check_chapter(root,harvest,'test','synthetic',base)

    def test_missing_pair_duplicate_id_wrong_lane(self):
        self._reject_mutations(('missing','duplicate','lane'))

    def test_run_raw_freeze_tampering(self):
        self._reject_mutations(('run','raw','freeze'))

    def test_source_token_terminology_errors(self):
        self._reject_mutations(('source','token','term'))

    def test_hidden_unknown_inputs_and_wrong_base(self):
        self._reject_mutations(('hidden','unknown','base'))

    def test_accepted_immutable_mode_and_bytes_cannot_change(self):
        for mutation in ('bytes','mode','delete','rename','symlink'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as d:
                root,harvest,base,fp,rp,frozen=fixture(Path(d))
                git(root,'add','.');git(root,'-c','user.name=Synthetic','-c','user.email=test@example.invalid','commit','-qm','accepted fixture')
                base=git(root,'rev-parse','HEAD');git(root,'update-ref','refs/heads/main',base)
                if mutation=='bytes':rp.write_bytes(rp.read_bytes()+b'\n')
                if mutation=='mode':rp.chmod(0o755)
                if mutation=='delete':rp.unlink()
                if mutation=='rename':git(root,'mv',str(rp.relative_to(root)),str(rp.relative_to(root))+'.renamed')
                if mutation=='symlink':rp.unlink();rp.symlink_to(fp)
                with self.assertRaises(RecordError):check_chapter(root,harvest,'test','synthetic',base)

    def test_accepted_boundary_stops_but_current_leaf_changes_still_fail(self):
        from stacks_zh.records import sha256_value
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            git(root,'add','.');git(root,'-c','user.name=Synthetic','-c','user.email=test@example.invalid','commit','-qm','accepted complete fixture')
            base=git(root,'rev-parse','HEAD');git(root,'update-ref','refs/heads/main',base)
            with patch('stacks_zh.source_adoptions._prepare_full',side_effect=AssertionError('accepted ancestry replay')):
                result=check_chapter(root,harvest,'test','synthetic',base)
                self.assertEqual(result.report['direct_nodes'],0)
                self.assertEqual(result.report['accepted_boundaries'],1)
                cp=root/frozen['batches'][0]['candidates_path']
                rows=[json.loads(x) for x in cp.read_text().splitlines()];rows[0]['notes'].append('new current leaf')
                write_jsonl(cp,rows)
                with self.assertRaises(RecordError):check_chapter(root,harvest,'test','synthetic',base)

    def test_reachable_topic_commit_is_not_a_trusted_base(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            git(root,'switch','-qc','unaccepted-topic')
            git(root,'-c','user.name=Synthetic','-c','user.email=test@example.invalid','commit','--allow-empty','-qm','topic only')
            with self.assertRaisesRegex(RecordError,'confirmed main'):
                check_chapter(root,harvest,'test','synthetic',git(root,'rev-parse','HEAD'))

    def test_classifier_never_calls_context_a_changed_chapter(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            self.assertEqual(classify(root,base,paths=[fp.relative_to(root).as_posix()])['chapters'],['test'])
            for p in ('config/glossary.yml','.github/workflows/ci.yml','stacks_zh/ci_scope.py','new-unknown','schema/unit.schema.json','upstream.lock'):
                self.assertEqual(classify(root,base,paths=[p])['kind'],'current-all')

    def test_new_chain_and_shared_run_missing_participant_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            run=root/'translation-data/runs/run-synthetic-first.json'
            original=run.read_bytes();value=json.loads(original)
            value['inputs']['context_hashes'].pop();write(run,value)
            with self.assertRaises(RecordError):check_chapter(root,harvest,'test','synthetic',base)
            run.write_bytes(original)
            # A same-change missing/cyclic predecessor cannot be treated as base.
            value=json.loads(fp.read_bytes());value['tool_version']='source-adoption-input-v2'
            value['prior_adoptions']=[dict(record=dict(path='translation-data/source-adoptions/synthetic-first.json',hash=byte_hash((root/'translation-data/source-adoptions/synthetic-first.json').read_bytes())),outputs=[])]
            write(fp,value)
            with self.assertRaises(RecordError):check_chapter(root,harvest,'test','synthetic',base)

    def test_unrelated_accepted_bad_history_is_only_found_by_explicit_audit(self):
        from stacks_zh.provenance import validate_repository_provenance
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            bad=root/'translation-data/retired/derivations/unrelated/candidates.jsonl'
            bad.parent.mkdir(parents=True);bad.write_text('{"broken":true}\n')
            git(root,'add',str(bad.relative_to(root)));git(root,'-c','user.name=Synthetic','-c','user.email=test@example.invalid','commit','-qm','accepted unrelated bad history for audit test')
            base=git(root,'rev-parse','HEAD');git(root,'update-ref','refs/heads/main',base)
            result=check_chapter(root,harvest,'test','synthetic',base)
            self.assertEqual(result.report['history_audit'],'not_run')
            self.assertTrue(validate_repository_provenance(root,harvest))

    def test_transient_read_and_install_failure_preserve_outputs(self):
        from stacks_zh import workflow
        from stacks_zh.validation_io import read_bytes
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            result=check_chapter(root,harvest,'test','synthetic',base)
            out=root/'preview/synthetic-chapter-test';out.mkdir(parents=True)
            old=out/'metadata.tex';old.write_bytes(b'original preview')
            manifest=root/'build/chapters.tex';manifest.parent.mkdir(exist_ok=True);manifest.write_text('\\item \\hyperref[test-section-phantom]{Synthetic}\n')
            kwargs=dict(chapter_manifest_path=manifest,chapter_source_dir=harvest,chapter='test',_validation=result,harvest=harvest)
            pairs=result.pairs
            original=workflow.restore_placeholders
            def transient(*a,**k):
                raw=rp.read_bytes()
                try:
                    rp.write_bytes(raw+b'\n');read_bytes(rp)
                finally:rp.write_bytes(raw)
                return original(*a,**k)
            with patch.object(workflow,'restore_placeholders',side_effect=transient):
                with self.assertRaises(RecordError):render_batch([u for u,c in pairs],[c for u,c in pairs],root/'upstream.lock',out,'synthetic','Synthetic',**kwargs)
            self.assertEqual(old.read_bytes(),b'original preview')
            # A failed consumed session is not reused; run a fresh real check.
            result=check_chapter(root,harvest,'test','synthetic',base)
            kwargs['_validation']=result
            replace_original=os.replace;calls=[]
            def fail_once(src,dst):
                calls.append((src,dst))
                if len(calls)==2:raise OSError('synthetic install failure')
                return replace_original(src,dst)
            with patch.object(workflow.os,'replace',side_effect=fail_once):
                with self.assertRaisesRegex(OSError,'install failure'):render_batch([u for u,c in pairs],[c for u,c in pairs],root/'upstream.lock',out,'synthetic','Synthetic',**kwargs)
            self.assertEqual(old.read_bytes(),b'original preview')
            self.assertFalse((out/'chapters/test.tex').exists())

    def test_multiple_real_runs_are_checked_independently(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            raw=[json.loads(line) for line in rp.read_text().splitlines()]
            for path in [fp,rp,root/'translation-data/runs/run-synthetic-first.json',root/'translation-data/source-adoptions/synthetic-first.json']:
                path.unlink()
            for b in frozen['batches']:(root/b['candidates_path']).unlink()
            for ordinal,batches in enumerate([frozen['batches'][:1],frozen['batches'][1:]],1):
                value=copy.deepcopy(frozen);identifier=f'synthetic-run-{ordinal}'
                value.update(adoption_id=identifier,run_id='run-'+identifier,batches=batches,
                             unit_ids=[u['unit_id'] for b in batches for u in b['units']])
                input_path=root/'translation-data/source-adoption-inputs'/(identifier+'.json')
                raw_path=root/'docs/evidence'/(identifier+'.jsonl')
                sp=root/value['task']['scope_manifest'];scope=json.loads(sp.read_text())
                extra=[input_path.relative_to(root).as_posix(),raw_path.relative_to(root).as_posix(),'translation-data/source-adoptions/'+identifier+'.json','translation-data/runs/run-'+identifier+'.json']
                scope['allowed_write_files']+=extra;scope['data_scopes'][0]['allowed_write_files']+=extra
                scope['data_scopes'][0]['run_scope'].append('run-'+identifier);write(sp,scope)
                value['task'].update(scope_bytes=sp.read_text(),scope_manifest_sha256=byte_hash(sp.read_bytes()))
                write(input_path,value);write_jsonl(raw_path,[r for r in raw if r['unit_id'] in value['unit_ids']])
                assemble_source_adoption(root,input_path,[raw_path],harvest)
            result=check_chapter(root,harvest,'test','synthetic',base)
            self.assertEqual(result.count,5)
            self.assertEqual(result.report['direct_nodes'],2)

    def test_render_cli_discovers_whole_chapter_checks_once_and_rejects_omitted_result_pairs(self):
        import contextlib
        import io
        from stacks_zh.cli import main
        from stacks_zh import chapter_validation
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            manifest=root/'build/chapters.tex';manifest.parent.mkdir(exist_ok=True)
            manifest.write_text('\\hyperref[test-section-phantom]{Synthetic}\n')
            # Only one requested pair cannot hide the rest: CLI discovers them all.
            batch=frozen['batches'][0]
            args=['render','--units',str(root/batch['units_path']),'--candidates',str(root/batch['candidates_path']),
                  '--lock',str(root/'upstream.lock'),'--harvest',str(harvest),'--model-lane','synthetic',
                  '--chapter','test','--base-ref',base,'--display-name','Synthetic',
                  '--chapter-manifest',str(manifest),'--chapter-source-dir',str(harvest),
                  '--output-dir',str(root/'preview/synthetic-chapter-test')]
            with patch.object(chapter_validation,'check_chapter',wraps=check_chapter) as check, \
                    patch('stacks_zh.repository_validation._complete_provenance',side_effect=AssertionError('history')), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args),0)
                self.assertEqual(check.call_count,1)
            result=check_chapter(root,harvest,'test','synthetic',base)
            with self.assertRaisesRegex(RecordError,'complete ordered pairs'):
                result.assert_valid(root,harvest,[u for u,c in result.pairs[:-1]],[c for u,c in result.pairs[:-1]])
            result.current._pair_locations=(('test.tex',0,1),*result.current._pair_locations[1:])
            with self.assertRaisesRegex(RecordError,'content changed'):result.assert_valid(root,harvest)

    def test_changed_unknown_decision_cannot_be_read_then_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            write(root/'translation-data/selections/unknown.json',dict(unit_id='unknown'))
            with self.assertRaisesRegex(RecordError,'selection'):
                check_chapter(root,harvest,'test','synthetic',base,current_all=True)

    def test_input_mode_head_and_hidden_enumeration_change_after_check(self):
        from stacks_zh.validation_io import glob_paths
        with tempfile.TemporaryDirectory() as d:
            root,harvest,base,fp,rp,frozen=fixture(Path(d))
            result=check_chapter(root,harvest,'test','synthetic',base)
            with result.reads.activate(),patch.object(Path,'glob',return_value=iter(())):
                with self.assertRaisesRegex(RecordError,'enumerating'):
                    list(glob_paths(root/'translation-data/units','*.jsonl'))
            up=root/frozen['batches'][0]['units_path'];old=up.stat().st_mode
            up.chmod(0o755)
            # Git raw scope records executable changes for tracked entries; new
            # fact paths also retain filesystem mode through the read session.
            with self.assertRaises(RecordError):result.assert_valid(root,harvest)
            up.chmod(old)
            git(root,'add','.gitignore');git(root,'-c','user.name=Synthetic','-c','user.email=test@example.invalid','commit','--allow-empty','-qm','head changed')
            with self.assertRaises(RecordError):result.assert_valid(root,harvest)
