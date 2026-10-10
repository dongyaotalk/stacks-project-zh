"""Synthetic source/coverage fixtures; never production translation or approval."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_group_derivations import commit, save, write
from test_source_container_boundaries import LIST, fixture
from test_source_containers import old_unit
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


if __name__=='__main__':unittest.main()
