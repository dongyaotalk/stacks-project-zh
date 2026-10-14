"""Independent composite-parameter fixtures; never production model output."""
import copy
import tempfile
import unittest
from pathlib import Path

from test_source_containers import fixture as english_fixture,selector
from test_group_derivations import fixture as history_fixture,read,write,commit
from stacks_zh.extraction import Policy
from stacks_zh.math_text import find_slots,validate_regions,validate_translation,complete_math_nodes
from stacks_zh.records import RecordError,restore_placeholders,stamp_unit_hashes,load_jsonl
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.schema_validation import validate_named_schema,validate_repository_schemas
from stacks_zh.source_containers import Containers,lower_container,load_source_containers,write_container_package
from stacks_zh.source_reextractions import source_tex
from stacks_zh.source_terms import source_inventory,source_tex_hash,validate_source_terms
from stacks_zh.workflow import render_batch

ROOT=Path(__file__).resolve().parents[1]
BASE=(ROOT/'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0]
RULE=r'''
translatable_math_text_components:
  component-description:
    literal: " irred.\\ comp. with "
    command: "text"
    usage: "indexed-component-description"
    components: [" irred.", "comp. with "]
    separator: "\\ "
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
'''
MATH=r"$$\text{Bad}(i,i')=\bigcup\nolimits_{W\subset D_{n,i}\cap D_{n,i'}\text{ irred.\ comp. with }\dim_\delta(W)=d-1}W$$"
OTHER=MATH.replace('Bad','Good').replace('d-1','d-2')
PROOF='\\begin{proof}\nCafé δ. '+MATH+'\n'+OTHER+'\n\\end{proof}'


def fixture(base):
    root,harvest,_=english_fixture(base,proof=PROOF)
    (root/'config/macro-policy.yml').write_text(BASE+RULE)
    c=Containers(root,harvest);selected=c.select(selector());unit=lower_container(selected,c.policy)[0]
    return root,harvest,c,selected,unit


def translated(unit):
    # Independent literal synthetic text; no real translation facts are written.
    return unit['source_text'].replace(' irred.',' 不可约（irred.）').replace('comp. with ','分支（comp.）且 ')


class CompositeMathTests(unittest.TestCase):
    def test_real_preparation_writes_v14_and_ordinary_assembly_cannot_bypass_it(self):
        from stacks_zh.workflow import _assemble_candidates_with_harness_version
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,records=history_fixture(Path(tmp),proof=PROOF,math_policy=BASE+RULE)
            current=records[-1];commit(root)
            units=load_jsonl(root/current['files']['output_units']['path'])
            groups=[dict(group_id='node-'+str(i),input_unit_ids=[u['unit_id']],identity_anchor=u['unit_id'],
                selector=selector() if u['node_kind']=='proof' else None,layout='whole',reason='Synthetic complete preparation.')
                for i,u in enumerate(units)]
            plan=dict(derivation_id='synthetic-component-prepare',created_at='2026-10-14T00:00:00Z',
                units_file=current['files']['output_units']['path'],candidates_file=current['files']['output_candidates']['path'],groups=groups)
            path=root/'build/plan.json';write(path,plan);output=root/'build/package'
            manifest=write_container_package(root,harvest,path,output)
            self.assertEqual(manifest['state'],'PREPARED',(output/'diagnostics.json').read_text())
            self.assertEqual(write_container_package(root,harvest,path,output,check=True),manifest)
            evidence=read(output/'restorations.json')[0]
            self.assertEqual(evidence['tool']['version'],'source-container-v14')
            self.assertEqual(evidence['new_units'][0]['schema_version'],3)
            with self.assertRaisesRegex(RecordError,'ordinary assembly is unavailable'):
                _assemble_candidates_with_harness_version(root/current['files']['output_units']['path'],root/'absent.jsonl',
                    root/'build/forbidden.jsonl',root/'upstream.lock','synthetic','fixture','low','fixture','fixture','fixture',
                    '2026-10-14T00:00:00Z','fixture','fixture','fixture:model','synthetic',None,'declared')
            self.assertFalse((root/'build/forbidden.jsonl').exists())

    def test_exact_parent_has_two_ordered_pure_leaves_and_a_locked_control_space(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,c,_,u=fixture(Path(tmp))
            self.assertEqual(u['schema_version'],3)
            self.assertFalse(validate_named_schema(u,'unit.schema.json','synthetic unit-v3'))
            self.assertEqual(validate_regions(u),[])
            self.assertEqual(source_tex(u),PROOF)
            self.assertEqual(complete_math_nodes(u),[MATH,OTHER])
            self.assertEqual(len(u['math_text_regions']),2)
            for region in u['math_text_regions']:
                self.assertEqual([s['source'] for s in region['slots']],[' irred.','comp. with '])
                self.assertEqual([s['parameter_components']['component_index'] for s in region['slots']],[1,2])
                self.assertEqual(u['placeholders'][region['pieces'][2]['placeholder']],'\\ ')
                for slot in region['slots']:
                    meta=slot['parameter_components'];span=meta['parameter_byte_span']
                    self.assertEqual(region['source'].encode()[span['start']:span['end']],b' irred.\\ comp. with ')
                    self.assertEqual(len(slot['classification_witness']['anchor']['matches']),2)
            self.assertEqual(validate_translation(u,translated(u)),[])
            restored=u['render']['prefix']+restore_placeholders(u,translated(u))+u['render']['suffix']
            self.assertEqual(restored,PROOF.replace(' irred.',' 不可约（irred.）').replace('comp. with ','分支（comp.）且 '))
            self.assertEqual(c.policy.math_text_rules['component-description']['slot_schema_version'],3)

    def test_wrong_role_unknown_macro_nested_text_other_separator_and_comments_are_blocked(self):
        rules=Policy(BASE+RULE).math_text_rules
        for source in [MATH.replace(r'\bigcup\nolimits_',r'\sum_'),
                       MATH.replace(r'\subset',r'\unknown'),
                       MATH.replace(r'\text{ irred.\ comp. with }',r'\text{\text{ irred.\ comp. with }}'),
                       MATH.replace(r'irred.\ ',r'irred.\quad '),
                       MATH.replace(r'\dim',r'\unknown'),
                       MATH.replace('irred.','irreducible'),
                       '$x+\\text{ irred.\\ comp. with }+y$',
                       r'$$\bigcup\nolimits_{W\subset D}[\text{ irred.\ comp. with }\dim(W)=1]$$',
                       r'$\verb|\bigcup\nolimits_{W\subset D\text{ irred.\ comp. with }\dim(W)=1}|$']:
            with self.subTest(source=source):
                try:slots=find_slots(source,rules)
                except ValueError:slots=[]
                self.assertEqual(slots,[])
        for before,after in [('components: [" irred.", "comp. with "]','components: [" irred."]'),
                             ('usage: "indexed-component-description"','usage: "root-phrase"'),
                             ('separator: "\\\\ "','separator: " "')]:
            with self.subTest(after=after),self.assertRaises(RecordError):Policy((BASE+RULE).replace(before,after))

    def test_tampering_and_version_downgrade_fail_after_restamping(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,_,_,original=fixture(Path(tmp))
            for fault in ['v2','parent','ordinal','separator','count','leaf','span','missing','duplicate','role','math']:
                u=copy.deepcopy(original);region=u['math_text_regions'][0];slot=region['slots'][0];meta=slot['parameter_components']
                if fault=='v2':u['schema_version']=2
                if fault=='parent':meta['parameter_source']=' different source '
                if fault=='ordinal':meta['component_index']=2
                if fault=='separator':meta['separator']=' '
                if fault=='count':meta['component_count']=3
                if fault=='leaf':slot['source']=' changed '
                if fault=='span':meta['parameter_byte_span']['start']+=1
                if fault=='missing':region['slots'].pop()
                if fault=='duplicate':region['slots'].append(copy.deepcopy(slot))
                if fault=='role':slot['classification_witness']['usage']='root-phrase'
                if fault=='math':u['placeholders'][region['pieces'][0]['placeholder']]=u['placeholders'][region['pieces'][0]['placeholder']].replace('d-1','d-2')+'x'
                try:u=stamp_unit_hashes(u)
                except (KeyError,IndexError):pass
                with self.subTest(fault=fault):self.assertTrue(validate_regions(u))
            text=translated(original)
            for value in ['',r'\alpha','a%b','a\nb','<MATHSEG_9999>']:
                with self.subTest(value=value):self.assertTrue(validate_translation(original,text.replace(' 不可约（irred.）',value,1)))
            middle=original['math_text_regions'][0]['pieces'][2]['placeholder']
            with self.assertRaises(RecordError):restore_placeholders(original,text,{middle:' '})

    def test_two_full_history_generations_validate_render_and_reject_v13_downgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,records=history_fixture(Path(tmp),count=2,proof=PROOF,math_policy=BASE+RULE)
            self.assertEqual(validate_repository_schemas(root),[])
            self.assertEqual(validate_repository_provenance(root,harvest),[])
            for n in [1,2]:
                evidence=read(root/f'translation-data/source-container-restorations/fixture-group-{n}-proof.json')
                self.assertEqual(evidence['tool']['version'],'source-container-v14')
            current=records[-1]
            paths=render_batch(root/current['files']['output_units']['path'],root/current['files']['output_candidates']['path'],
                root/'upstream.lock',root/'preview','fixture','Synthetic fixture',chapter_source_dir=harvest)
            text=''.join(p.read_text() for p in paths)
            self.assertIn(r'\text{ 不可约（irred.）\ 分支（comp.）且 }',text)
            self.assertNotIn('MATHSEG_',text)
            path=root/'translation-data/source-container-restorations/fixture-group-2-proof.json';evidence=read(path)
            evidence['tool']['version']='source-container-v13';write(path,evidence)
            self.assertTrue(load_source_containers(root,harvest)[1])
            self.assertTrue(validate_repository_provenance(root,harvest))

    def test_each_natural_leaf_remains_visible_to_pending_source_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,_,_,u=fixture(Path(tmp))
            terms=[{'id':identifier,'forms':[word],'chapters':[],
                    'evidence':[dict(chapter='test',unit_id=u['unit_id'],source_term=word,source_tex_hash=source_tex_hash(u))]}
                   for identifier,word in [('irreducible','irred.'),('component','comp.')]]
            catalog=dict(schema_version=1,source_commit=u['source_commit'],nonmathematical_declarations={},terms=terms)
            occurrences=source_inventory(u,catalog)['occurrences']
            self.assertEqual(len(occurrences),4)
            candidate=dict(unit_id=u['unit_id'],translation=translated(u),term_status='DECISION_REQUIRED',
                term_occurrences=[dict(source_term=word,target_term=target) for _ in range(2) for word,target in [('irred.','不可约'),('comp.','分支')]],
                unknown_terms=[dict(source_term=word,target_term=target,context='Synthetic pending term.') for word,target in [('irred.','不可约'),('comp.','分支')]])
            self.assertEqual(validate_source_terms(u,candidate,catalog),[])
