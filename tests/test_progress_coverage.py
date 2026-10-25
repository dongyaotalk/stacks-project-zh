"""Synthetic source/coverage fixtures; never production translation or approval."""
from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_group_derivations import commit, save, write
from test_source_container_boundaries import LIST, fixture
from test_source_containers import old_unit
from test_source_containers import git
from stacks_zh.progress import collect_progress
from stacks_zh.progress_coverage import container_tag_coverage
from stacks_zh.records import RecordError, load_jsonl
from stacks_zh.source_containers import load_source_containers, write_container_package


def setup(base, *, named=False, extra=''):
    statement = LIST.replace('Choose two objects.', 'Choose two objects.' + extra)
    if named:
        statement = statement.replace('\\begin{lemma}', '\\begin{lemma}[Named assertion]', 1)
    root, harvest, old, plan, package = fixture(base, statement=statement)
    if named:
        value = json.loads(plan.read_text()); value['groups'][0]['layout'] = 'split-title'; write(plan, value)
    write_container_package(root, harvest, plan, package)
    restorations = json.loads((package / 'restorations.json').read_text())
    record = {k:copy.deepcopy(restorations[0][k]) for k in (
        'schema_version','derivation_id','source_commit','origin_commit','created_at','files')}
    record.update(tool={'id':'stacks-zh-derive','version':'4'}, unit_groups=[])
    for restored in restorations:
        for role, name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
            path = root / restored['files'][role]['path']; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((package/name).read_bytes())
        write(root / f"translation-data/source-container-restorations/{restored['restoration_id']}.json", restored)
        group = {k:copy.deepcopy(restored[k]) for k in ('group_id','input_unit_ids','output_unit_ids','reason')}
        group.update(identity_anchor=group['input_unit_ids'][0], output_units=restored['new_units'],
            source_container_restoration_id=restored['restoration_id'], model_correction_id='synthetic-only')
        record['unit_groups'].append(group)
    units = [u for g in record['unit_groups'] for u in g['output_units']]
    up='translation-data/units/test-boundary.jsonl'; cp='translation-data/candidates/fixture/test-boundary.jsonl'
    record['files']['output_units']=save(root, up, units)
    candidates=[{'unit_id':u['unit_id'],'source_commit':u['source_commit'],'source_status':'CURRENT',
                 'translation':'合成测试，非模型运行。'} for u in units]
    record['files']['output_candidates']=save(root, cp, candidates)
    path=root/f"translation-data/derivations/{record['derivation_id']}.json";write(path,record)
    heading=old_unit(record['source_commit'],'tag:0000:title','section_title','Basics','\\section{','}\\label{test-section-basic}')
    save(root,'translation-data/units/test-heading.jsonl',[heading])
    save(root,'translation-data/candidates/fixture/test-heading.jsonl',[
        {'unit_id':heading['unit_id'],'source_commit':heading['source_commit'],'source_status':'CURRENT'}])
    write(root/'config/chapter-titles.json',{'titles':{'test':'测试'}})
    write(root/'translation-data/chapter-templates/test.json',{
        'chapter':'test','chapter_ordinal':1,'source_commit':record['source_commit'],'source_state':'CURRENT',
        'source_file':'test.tex','sections':[{'ordinal':1,'source_title':'Basics','source_label':'test-section-basic','parent_tag':'0000'}]})
    return root,harvest,old,record,path


def current_units(root):
    return {p.relative_to(root).as_posix():load_jsonl(p) for p in (root/'translation-data/units').glob('*.jsonl')}


def section(root,harvest):
    return collect_progress(root,harvest/'tags/tags').chapters[0].sections[0]


class ContainerProgressTests(unittest.TestCase):
    def test_segmented_and_complete_container_have_equal_native_scope_without_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,old,record,path=setup(Path(tmp))
            complete=section(root,harvest)
            self.assertEqual((complete.required_tags,complete.prepared_tags),(4,4))
            self.assertTrue(complete.candidate_complete)
            self.assertFalse(complete.reviewed_complete);self.assertFalse(complete.published_complete)
            path.unlink()
            save(root,record['files']['output_units']['path'],old)
            save(root,record['files']['output_candidates']['path'],[
                {'unit_id':u['unit_id'],'source_commit':u['source_commit'],'source_status':'CURRENT'} for u in old])
            segmented=section(root,harvest)
            self.assertEqual((segmented.required_tags,segmented.prepared_tags),(4,4))
            self.assertTrue(segmented.candidate_complete)
            self.assertGreater(segmented.total_units,complete.total_units)

    def test_named_split_title_requires_the_whole_current_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_,record,path=setup(Path(tmp),named=True)
            self.assertTrue(section(root,harvest).candidate_complete)
            units=current_units(root);up=record['files']['output_units']['path']
            units[up]=units[up][1:]
            record['files']['output_units']=save(root,up,units[up]);write(path,record)
            with self.assertRaises(RecordError):container_tag_coverage(root,harvest,units)

    def test_candidate_absence_does_not_change_preparation_or_grant_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_,record,_=setup(Path(tmp))
            cp=root/record['files']['output_candidates']['path'];rows=load_jsonl(cp)
            save(root,record['files']['output_candidates']['path'],rows[1:])
            result=section(root,harvest)
            self.assertEqual(result.prepared_tags,4)
            self.assertFalse(result.candidate_complete)
            self.assertFalse(result.reviewed_complete);self.assertFalse(result.published_complete)

    def test_candidate_strings_ordinary_units_and_archived_records_cannot_add_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_,record,path=setup(Path(tmp))
            cp=record['files']['output_candidates']['path'];rows=load_jsonl(root/cp)
            rows[0]['translation']=r'\\item\\label{test-lemma-two} arbitrary candidate'
            save(root,cp,rows)
            archive=root/f"translation-data/derivation-archives/{record['derivation_id']}.json"
            write(archive,{'synthetic':'retired output is never current coverage'})
            retired=section(root,harvest);self.assertEqual(retired.prepared_tags,2)
            self.assertFalse(retired.candidate_complete)
            archive.unlink();path.unlink()
            ordinary=section(root,harvest);self.assertEqual(ordinary.prepared_tags,2)
            self.assertFalse(ordinary.candidate_complete)

    def test_fake_labels_inside_math_comments_footnotes_references_and_literals_are_excluded(self):
        fake=['$\\item\\label{lemma-two}$','%\\item\\label{lemma-two}\n',
              '\\footnote{\\item\\label{lemma-two}}','\\ref{lemma-two}',
              '\\begin{verbatim}\\item\\label{lemma-two}\\end{verbatim}']
        for text in fake:
            with self.subTest(text=text),tempfile.TemporaryDirectory() as tmp:
                root,harvest,_,record,_=setup(Path(tmp),extra=text)
                covered=container_tag_coverage(root,harvest,current_units(root))
                self.assertEqual(covered[record['unit_groups'][0]['output_unit_ids'][0]],frozenset({'0003','0004'}))

    def test_changed_source_group_order_hash_and_binding_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_,record,path=setup(Path(tmp))
            original={p:p.read_bytes() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
            for fault in ['source','stale-unit','stale-status','bytes','group-unit','group-order','input-order','evidence-binding',
                          'missing-evidence','evidence-fragment','wrong-native-owner','duplicate-output']:
                altered=copy.deepcopy(record);up=altered['files']['output_units']['path']
                ep=root/f"translation-data/source-container-restorations/{altered['unit_groups'][0]['source_container_restoration_id']}.json"
                if fault=='source':altered['source_commit']='a'*40
                if fault in {'stale-unit','stale-status'}:
                    altered['unit_groups'][0]['output_units'][0][
                        'source_commit' if fault=='stale-unit' else 'source_status']='a'*40 if fault=='stale-unit' else 'STALE'
                    rows=[u for g in altered['unit_groups'] for u in g['output_units']]
                    altered['files']['output_units']=save(root,up,rows)
                if fault=='bytes':(root/up).write_bytes((root/up).read_bytes()+b'\n')
                if fault=='group-unit':altered['unit_groups'][0]['output_units'][0]['source_text']='Missing native prose.'
                if fault=='group-order':altered['unit_groups'].reverse()
                if fault=='input-order':altered['unit_groups'][0]['input_unit_ids'].reverse()
                if fault=='evidence-binding':altered['unit_groups'][0]['source_container_restoration_id']=altered['unit_groups'][1]['source_container_restoration_id']
                if fault=='missing-evidence':ep.unlink()
                if fault=='evidence-fragment':
                    value=json.loads(ep.read_text());value['fragment']+=' Changed.';write(ep,value)
                if fault=='wrong-native-owner':
                    value=json.loads(ep.read_text());value['selector']['owner_tag']='0002';write(ep,value)
                if fault=='duplicate-output':altered['unit_groups'].append(copy.deepcopy(altered['unit_groups'][0]))
                write(path,altered)
                with self.subTest(fault=fault),self.assertRaises(RecordError):
                    container_tag_coverage(root,harvest,current_units(root))
                for p,raw in original.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)

    def test_rehashed_current_and_embedded_unit_cannot_hide_incomplete_native_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_,record,path=setup(Path(tmp))
            record['unit_groups'][0]['output_units'][0]['source_text']='Only part of the statement.'
            units=[u for g in record['unit_groups'] for u in g['output_units']]
            record['files']['output_units']=save(root,record['files']['output_units']['path'],units)
            write(path,record)
            with self.assertRaisesRegex(RecordError,'complete current v4 group'):
                container_tag_coverage(root,harvest,current_units(root))

    def test_added_evidence_and_derivation_cannot_be_mutated_after_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_,record,path=setup(Path(tmp));commit(root)
            record['unit_groups'][0]['reason']='Rehashed replacement.';write(path,record)
            with self.assertRaisesRegex(RecordError,'first Git addition'):
                container_tag_coverage(root,harvest,current_units(root))

    def test_exact_query_is_strict_and_default_validation_still_checks_all_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_,record,_=setup(Path(tmp))
            identifier=record['unit_groups'][0]['source_container_restoration_id']
            write(root/'translation-data/source-container-restorations/unrelated.json',{'bad':'fixture'})
            self.assertTrue(load_source_containers(root,harvest)[1])
            selected,errors=load_source_containers(root,harvest,identifiers={identifier})
            self.assertEqual(errors,[]);self.assertEqual(set(selected),{identifier})
            for ids in [{identifier,'absent'},{'../escape'},'not-a-set']:
                with self.subTest(ids=ids):self.assertTrue(load_source_containers(root,harvest,identifiers=ids)[1])
            self.assertEqual(load_source_containers(root,harvest,identifiers=set()),({},[]))

    def test_progress_query_revalidates_only_relevant_complete_containers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_,record,_=setup(Path(tmp))
            with patch('stacks_zh.progress_coverage.load_source_containers',wraps=load_source_containers) as loader:
                section(root,harvest)
            loader.assert_called_once_with(root,harvest,identifiers={record['unit_groups'][0]['source_container_restoration_id']})
            self.assertEqual(len(record['unit_groups']),2)


def adoption_setup(base, *, named=False, extra=''):
    """Real Git/source bindings; synthetic metadata is not a valid model run."""
    from test_source_adoptions import synthetic_fixture
    from stacks_zh.source_adoptions import POLICIES
    from stacks_zh.source_containers import Containers, lower_container, clean
    from stacks_zh.source_reextractions import byte_hash

    seed, _, _, _, frozen, _ = synthetic_fixture(base / 'seed', typed=False)
    root, harvest, _, derived, path = setup(base / 'adopted', named=named, extra=extra)
    path.unlink()
    native = Containers(root, harvest)
    groups = []
    for group in derived['unit_groups']:
        restoration = json.loads((root / ('translation-data/source-container-restorations/'
            + group['source_container_restoration_id'] + '.json')).read_text())
        selected = native.select(restoration['selector'])
        units = [clean(u) for u in lower_container(selected, native.policy)]
        groups.append(dict(selector=selected['selector'], selected=selected,
                           unit_ids=[u['unit_id'] for u in units]))
    units = [clean(u) for g in groups for u in lower_container(g['selected'], native.policy)]
    candidates = [{'unit_id':u['unit_id'], 'source_commit':u['source_commit'],
                   'source_status':'CURRENT'} for u in units]
    (root / derived['files']['output_units']['path']).unlink()
    (root / derived['files']['output_candidates']['path']).unlink()
    up = 'translation-data/units/test-first.jsonl'
    cp = 'translation-data/candidates/synthetic/test-first.jsonl'
    unit_entry = save(root, up, units); candidate_entry = save(root, cp, candidates)
    for name in POLICIES:
        if name in {'upstream.lock', 'config/macro-policy.yml'}:
            continue
        target = root / name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(seed / name, target)
    commit(root)
    frozen.update(origin_commit=git(root,'rev-parse','HEAD'),
        source_commit=units[0]['source_commit'], unit_ids=[u['unit_id'] for u in units],
        parent_tags=list(dict.fromkeys(u['parent_tag'] for u in units)),
        policies=[{'path':name,'hash':byte_hash((root/name).read_bytes())} for name in POLICIES],
        batches=[dict(units_path=up,candidates_path=cp,units=units,containers=groups,prior_attempts=[])])
    frozen['contexts'] = []
    identifier = frozen['adoption_id']
    ip = f'translation-data/source-adoption-inputs/{identifier}.json'
    ap = f'translation-data/source-adoptions/{identifier}.json'
    rp = f'docs/evidence/{identifier}-raw.jsonl'
    run = f'translation-data/runs/{frozen["run_id"]}.json'
    scope_path = 'task-scopes/synthetic-first.json'
    files = [ip,ap,up,cp,rp,run]
    scope = dict(schema_version=1,task_id=frozen['task_id'],owner='synthetic',
        branch=git(root,'branch','--show-current'),source_commit=frozen['source_commit'],
        allowed_write_files=[scope_path,*files],data_scopes=[dict(scope_id='synthetic',chapter='test',
        parent_tags=frozen['parent_tags'],historical_parent_tags=[],unit_ids=frozen['unit_ids'],
        input_unit_ids=frozen['unit_ids'],output_unit_ids=frozen['unit_ids'],allowed_write_files=files,
        run_scope=[frozen['run_id']],model_scope=['synthetic','synthetic:fixture:declared'])])
    write(root/scope_path,scope)
    frozen['task'].update(branch=scope['branch'],scope_manifest=scope_path,
        scope_manifest_sha256=byte_hash((root/scope_path).read_bytes()),scope_bytes=(root/scope_path).read_text())
    write(root/ip,frozen)
    record={k:copy.deepcopy(frozen[k]) for k in ('schema_version','adoption_id','origin_commit',
        'source_commit','created_at','unit_ids','chapter','parent_tags','run_id')}
    record.update(tool_version='source-adoption-v1',input={'path':ip,'hash':byte_hash((root/ip).read_bytes())},
        raw_attempts=[dict(path=rp,hash='sha256:'+'0'*64,unit_ids=frozen['unit_ids'])],
        run=dict(path=run,hash='sha256:'+'0'*64),outputs=[dict(units=unit_entry,candidates=candidate_entry)])
    write(root/ap,record)
    return root,harvest,record,frozen,root/ap


class FirstAdoptionProgressTests(unittest.TestCase):
    def test_complete_native_adoption_adds_scope_without_model_or_review_approval(self):
        from stacks_zh.source_adoptions import load_repository_source_adoptions
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,record,_,_=adoption_setup(Path(tmp))
            result=section(root,harvest)
            self.assertEqual((result.required_tags,result.prepared_tags),(4,4))
            self.assertTrue(result.candidate_complete)
            self.assertFalse(result.reviewed_complete);self.assertFalse(result.published_complete)
            # The source-only fixture deliberately has no model raw/run. Full
            # provenance still rejects it; progress cannot approve a model run.
            self.assertTrue(load_repository_source_adoptions(root,harvest)[1])

    def test_named_split_group_and_candidate_absence_preserve_preparation_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,record,_,_=adoption_setup(Path(tmp),named=True)
            self.assertTrue(section(root,harvest).candidate_complete)
            (root/record['outputs'][0]['candidates']['path']).unlink()
            result=section(root,harvest)
            self.assertEqual(result.prepared_tags,4)
            self.assertFalse(result.candidate_complete)
            self.assertFalse(result.reviewed_complete);self.assertFalse(result.published_complete)

    def test_candidate_text_and_unbound_units_do_not_supply_native_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,record,_,path=adoption_setup(Path(tmp))
            cp=root/record['outputs'][0]['candidates']['path'];rows=load_jsonl(cp)
            rows[0]['translation']=r'\\item\\label{item-first} arbitrary candidate'
            save(root,cp.relative_to(root).as_posix(),rows)
            path.unlink()
            self.assertEqual(section(root,harvest).prepared_tags,2)
            self.assertFalse(section(root,harvest).candidate_complete)

    def test_fake_nested_labels_are_excluded_for_first_adoptions(self):
        fake=['$\\item\\label{lemma-two}$','%\\item\\label{lemma-two}\n',
              '\\footnote{\\item\\label{lemma-two}}','\\ref{lemma-two}',
              '\\begin{verbatim}\\item\\label{lemma-two}\\end{verbatim}']
        for text in fake:
            with self.subTest(text=text),tempfile.TemporaryDirectory() as tmp:
                root,harvest,_,_,_=adoption_setup(Path(tmp),extra=text)
                covered=container_tag_coverage(root,harvest,current_units(root))
                self.assertEqual(set().union(*covered.values()),{'0003','0004'})

    def test_rehashed_incomplete_or_changed_source_bindings_are_rejected(self):
        from stacks_zh.source_reextractions import byte_hash
        faults=['source','policy','fragment','unit','partial','order','output-path','input-hash','stale','bytes']
        for fault in faults:
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
                root,harvest,record,frozen,path=adoption_setup(Path(tmp),named=True)
                batch=frozen['batches'][0];up=batch['units_path']
                if fault=='source':record['source_commit']=frozen['source_commit']='a'*40
                if fault=='policy':frozen['policies'][0]['hash']='sha256:'+'0'*64
                if fault=='fragment':batch['containers'][0]['selected']['fragment']+=' Incomplete.'
                if fault=='unit':batch['units'][0]['source_text']='Only part of the source.'
                if fault=='stale':batch['units'][0]['source_status']='STALE'
                if fault=='partial':
                    batch['units']=batch['units'][1:]
                    batch['containers'][0]['unit_ids']=batch['containers'][0]['unit_ids'][1:]
                    frozen['unit_ids']=record['unit_ids']=[u['unit_id'] for u in batch['units']]
                if fault=='order':batch['units'].reverse()
                if fault=='output-path':record['outputs'][0]['units']['path']='translation-data/units/absent.jsonl'
                if fault in {'unit','partial','order','stale'}:
                    record['outputs'][0]['units']=save(root,up,batch['units'])
                if fault=='bytes':
                    with (root/up).open('ab') as stream:stream.write(b'\n')
                write(root/record['input']['path'],frozen)
                record['input']['hash']=byte_hash((root/record['input']['path']).read_bytes())
                if fault=='input-hash':record['input']['hash']='sha256:'+'0'*64
                write(path,record)
                with self.assertRaises(RecordError):container_tag_coverage(root,harvest,current_units(root))

    def test_immutable_record_and_file_set_changes_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,record,_,path=adoption_setup(Path(tmp));commit(root)
            record['created_at']='2026-10-20T00:00:00Z';write(path,record)
            with self.assertRaisesRegex(RecordError,'first Git addition'):
                container_tag_coverage(root,harvest,current_units(root))

    def test_source_query_checks_only_relevant_adoptions_and_never_model_history(self):
        from stacks_zh.source_containers import Containers
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_,frozen,_=adoption_setup(Path(tmp))
            write(root/'translation-data/source-adoptions/unrelated.json',{'not':'a current source owner'})
            original=Containers.select;seen=[]
            def observe(native,selector):
                seen.append(selector)
                return original(native,selector)
            with patch.object(Containers,'select',observe), \
                    patch('stacks_zh.source_adoptions.load_repository_source_adoptions',side_effect=AssertionError('full replay')), \
                    patch('stacks_zh.source_adoptions._replay_record',side_effect=AssertionError('model replay')):
                self.assertEqual(section(root,harvest).prepared_tags,4)
            self.assertEqual(seen,[g['selector'] for b in frozen['batches'] for g in b['containers']])

    def test_consumed_adoption_is_not_a_second_current_source_owner(self):
        from stacks_zh.source_reextractions import byte_hash
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,record,frozen,path=adoption_setup(Path(tmp))
            child=copy.deepcopy(frozen);child_record=copy.deepcopy(record)
            child.update(tool_version='source-adoption-input-v2',adoption_id='synthetic-next',
                run_id='run-synthetic-next',created_at='2026-10-20T00:00:00Z',
                prior_adoptions=[dict(record=dict(path=path.relative_to(root).as_posix(),
                    hash=byte_hash(path.read_bytes())),outputs=copy.deepcopy(record['outputs']))])
            ip='translation-data/source-adoption-inputs/synthetic-next.json'
            ap='translation-data/source-adoptions/synthetic-next.json'
            raw='docs/evidence/synthetic-next-raw.jsonl';run='translation-data/runs/run-synthetic-next.json'
            scope=json.loads(frozen['task']['scope_bytes'])
            extra=[ip,ap,raw,run]
            scope['allowed_write_files']+=extra;scope['data_scopes'][0]['allowed_write_files']+=extra
            scope['data_scopes'][0]['run_scope'].append(child['run_id'])
            sp='task-scopes/synthetic-next.json';scope['allowed_write_files'].append(sp)
            write(root/sp,scope);child['task'].update(scope_manifest=sp,
                scope_manifest_sha256=byte_hash((root/sp).read_bytes()),scope_bytes=(root/sp).read_text())
            write(root/ip,child)
            child_record.update(tool_version='source-adoption-v2',adoption_id=child['adoption_id'],
                run_id=child['run_id'],created_at=child['created_at'],
                input=dict(path=ip,hash=byte_hash((root/ip).read_bytes())),
                raw_attempts=[dict(path=raw,hash='sha256:'+'0'*64,unit_ids=child['unit_ids'])],
                run=dict(path=run,hash='sha256:'+'0'*64))
            write(root/ap,child_record)
            self.assertEqual(section(root,harvest).prepared_tags,4)
            duplicate=copy.deepcopy(child);duplicate_record=copy.deepcopy(child_record)
            ip2='translation-data/source-adoption-inputs/synthetic-other.json'
            duplicate['adoption_id']='synthetic-other';write(root/ip2,duplicate)
            duplicate_record.update(adoption_id='synthetic-other',input=dict(path=ip2,hash=byte_hash((root/ip2).read_bytes())))
            write(root/'translation-data/source-adoptions/synthetic-other.json',duplicate_record)
            with self.assertRaisesRegex(RecordError,'multiple current successors'):
                container_tag_coverage(root,harvest,current_units(root))
        from stacks_zh.source_containers import Containers
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_,_,_=adoption_setup(Path(tmp));original=Containers.select
            def change(native,selector):
                selected=original(native,selector)
                write(root/'translation-data/source-adoptions/added.json',{'changed':'during source query'})
                return selected
            with patch.object(Containers,'select',change),self.assertRaisesRegex(RecordError,'paths changed'):
                container_tag_coverage(root,harvest,current_units(root))


if __name__=='__main__':unittest.main()
