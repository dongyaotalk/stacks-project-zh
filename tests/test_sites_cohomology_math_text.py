"""Synthetic fixtures and read-only locked Git witnesses; no model facts."""
import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from test_math_text import BASE_POLICY
from test_source_containers import fixture as english_fixture, selector, git
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots, nodes, validate_regions, validate_translation
from stacks_zh.math_text_sites_cohomology import MATRICES, CUP, PAB, REFERENCE, REFERENCE_LITERAL
from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import source_tex, byte_hash
from stacks_zh.source_adoptions import (REFERENCE_POLICIES, POLICIES, assemble_source_adoption,
    load_repository_source_adoptions, _reference_origin)
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import write_jsonl, sha256_value
from stacks_zh.workflow import render_batch

ROOT = Path(__file__).resolve().parents[1]


def registry(label='test-lemma-one'):
    """Separate opt-in fixture policy; production policy is untouched."""
    plain = '''
translatable_math_text:
  naive:
    literal: "naive cup product"
    command: "text"
    usage: "sites-naive-cup-arrow"
    source_label: "LABEL"
    witness_kind: "lemma"
    witness_ordinal: 1
'''
    ref = '''
translatable_math_text_references:
  remark-reference:
    literal: "Remark \\ref{remark-cup-product}"
    prefix: "Remark "
    reference: "\\ref{remark-cup-product}"
    command: "text"
    usage: "sites-cup-remark-reference"
    source_label: "LABEL"
    witness_kind: "lemma"
    witness_ordinal: 1
'''
    # YAML fields are JSON-valued, so backslashes need JSON escaping.
    ref = ref.replace('\\ref', '\\\\ref')
    return (plain + ref).replace('LABEL', label)


def synthetic_policy():
    return BASE_POLICY + '''
  Tot:
    commands: ["text"]
    usages: ["applied"]
    source_label: test-lemma-one
''' + registry()


def reference_fixture(base):
    root, harvest, _ = english_fixture(base,
        statement='\\begin{lemma}\\label{lemma-one}A synthetic claim.\n' + CUP + '\n\\end{lemma}',
        proof='\\begin{proof}A synthetic proof.\\end{proof}')
    (root/'config/macro-policy.yml').write_text(synthetic_policy())
    native = Containers(root, harvest)
    selected = native.select(selector('lemma'))
    unit = lower_container(selected, native.policy)[0]
    return root, harvest, native, selected, unit


class FrameTests(unittest.TestCase):
    def test_precise_cup_roles_and_protected_reference_metadata(self):
        slots = find_slots(CUP, Policy(synthetic_policy()).math_text_rules)
        self.assertEqual([s['value'] for s in slots], ['Remark ', 'naive cup product'])
        reference = slots[0]['parameter_reference']
        self.assertEqual(reference['reference_source'], REFERENCE)
        self.assertEqual(CUP.encode()[reference['reference_byte_span']['start']:
                                    reference['reference_byte_span']['end']], REFERENCE.encode())
        self.assertEqual(reference['parameter_source'], REFERENCE_LITERAL)

    def test_complete_formula_arrow_reference_and_boundary_mutations_fail_closed(self):
        rules = Policy(synthetic_policy()).math_text_rules
        mutations = [CUP.replace('\\ar[d]^{', '\\ar[r]^{', 1),
            CUP.replace('remark-cup-product', 'other-reference'),
            CUP.replace('\\ref{', '\\eqref{'),
            CUP.replace('\\mathbf{L}', '\\mathbf{M}', 1),
            CUP.replace('\\text{Tot}', '\\text{Other}', 1),
            CUP.replace('\\text{Remark ', '\\textit{Remark '),
            CUP.replace('\\ref{remark-cup-product}', '\\ref{remark-cup-product} '),
            CUP.replace('\\text{naive cup product}', '\\text{}'),
            '$x_{\\text{naive cup product}}$',
            CUP.replace('\\text{naive cup product}', '\\text{naive cup product}\\text{naive cup product}')]
        for source in mutations:
            with self.subTest(source=source):
                self.assertEqual(find_slots(source, rules), [])

    def test_reference_policy_cannot_borrow_plain_or_component_roles(self):
        text = synthetic_policy()
        for replacement in [text.replace('translatable_math_text_references:', 'translatable_math_text_components:'),
            text.replace('sites-cup-remark-reference', 'arrow-label-prefix'),
            text.replace('prefix: "Remark "', 'prefix: "Lemma "'),
            text.replace('witness_kind: "lemma"', 'witness_kind: "proof"')]:
            with self.subTest(policy=replacement), self.assertRaises(RecordError):
                Policy(replacement)

    def test_matrix_roles_require_all_original_operands(self):
        rules = {str(i):dict(literal=literal, command='text', usage='sites-invertible-sheaf-matrices')
            for i,literal in enumerate(['set of invertible sheaves on ', 'set of ', '-torsors'])}
        self.assertEqual([s['value'] for s in find_slots(MATRICES, rules)],
                         ['set of invertible sheaves on ', 'set of ', '-torsors'])
        for source in [MATRICES.replace('\\longrightarrow', '\\longleftarrow'),
            MATRICES.replace('\\mathcal{O}^*', '\\mathcal{O}'),
            MATRICES.replace('\\mathcal{C}', '\\mathcal{D}'),
            MATRICES.replace('\\begin{matrix}', '\\begin{aligned}', 1).replace('\\end{matrix}', '\\end{aligned}', 1),
            MATRICES.replace(' up to isomorphism', '')]:
            with self.subTest(source=source):
                self.assertEqual(find_slots(source, rules), [])

    def test_pab_shriek_is_a_single_whole_pattern_context(self):
        policy = Policy(BASE_POLICY + '''
locked_math_text_contexts:
  pab-shriek:
    base_notation: "PAb"
    commands: ["textit"]
    usages: ["sites-pab-shriek"]
    source_label: "test-lemma-one"
''')
        def usage(source):
            start=source.index('\\textit{PAb}')
            return Scanner(source, policy).notation_usage('textit','PAb',start+len('\\textit{PAb}'),command_start=start)
        self.assertEqual(usage(PAB)[0], 'sites-pab-shriek')
        for source in [PAB.replace("U'!", 'U!'), PAB.replace('\\mathbf{Z}', '\\mathbf{Q}'),
                       PAB.replace("\\mathcal{F}_{U'} = ", ''), '$j^{\\textit{PAb}}$']:
            with self.subTest(source=source): self.assertIsNone(usage(source))


class ReferenceUnitTests(unittest.TestCase):
    def test_source_schema_roundtrip_and_translated_reference_skeleton(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,_,selected,unit=reference_fixture(Path(tmp))
            self.assertEqual(unit['schema_version'],4)
            self.assertEqual(source_tex(unit),selected['fragment'])
            self.assertEqual(validate_named_schema(unit,'unit.schema.json','synthetic unit'),[])
            self.assertEqual(validate_regions(unit),[])
            translated=unit['source_text'].replace('Remark ', '注释 ').replace('naive cup product','朴素杯积')
            self.assertEqual(validate_translation(unit,translated),[])
            for target in [translated.replace('注释 ',''), translated.replace('注释 ',r'\ref{bad}'),
                           translated.replace('<MATHSEG_0001>','<MATHSEG_0002>')]:
                with self.subTest(target=target):self.assertTrue(validate_translation(unit,target))
            # Recompute hashes: internal self-consistency cannot forgive source changes.
            for mutate in ['reference', 'span', 'command', 'label', 'version', 'parent']:
                bad=copy.deepcopy(unit); slot=bad['math_text_regions'][0]['slots'][0]
                if mutate=='reference':slot['parameter_reference']['reference_source']=r'\ref{bad}'
                elif mutate=='span':slot['parameter_reference']['reference_byte_span']['start']+=1
                elif mutate=='command':slot['parameter_reference']['reference_command']='eqref'
                elif mutate=='label':slot['parameter_reference']['reference_label']='bad'
                elif mutate=='parent':slot['parameter_reference']['parameter_source']='Remark '+r'\ref{bad}'
                else:bad['schema_version']=2
                bad=stamp_unit_hashes(bad)
                with self.subTest(mutate=mutate):self.assertTrue(validate_regions(bad))

    def test_no_reference_or_component_downgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            unit=reference_fixture(Path(tmp))[-1]
            for version in [1,2,3]:
                bad=copy.deepcopy(unit);bad['schema_version']=version
                with self.subTest(version=version):self.assertTrue(validate_regions(bad))
            bad=copy.deepcopy(unit);del bad['math_text_regions'][0]['slots'][0]['parameter_reference']
            self.assertTrue(validate_regions(bad))

    def test_rehashed_formula_change_and_ordinary_assembly_still_fail(self):
        from stacks_zh.workflow import _assemble_candidates_with_harness_version
        from stacks_zh.group_derivations import replay_groups
        with tempfile.TemporaryDirectory() as tmp:
            root,_,_,_,unit=reference_fixture(Path(tmp))
            bad=copy.deepcopy(unit);region=bad['math_text_regions'][0]
            region['source']=region['source'].replace('\\mathbf{L}','\\mathbf{M}',1)
            region['source_hash']=byte_hash(region['source'])
            bad['placeholders']['MATHSEG_0001']=bad['placeholders']['MATHSEG_0001'].replace('\\mathbf{L}','\\mathbf{M}',1)
            bad=stamp_unit_hashes(bad)
            self.assertTrue(validate_regions(bad))
            up=root/'units.jsonl';write_jsonl(up,[unit])
            with self.assertRaisesRegex(RecordError,'ordinary assembly'):
                _assemble_candidates_with_harness_version(up,root/'absent.jsonl',root/'out.jsonl',root/'upstream.lock',
                    'synthetic','synthetic','synthetic','translator-v2','synthetic','synthetic',
                    '2026-11-09T00:00:00Z','synthetic','synthetic','synthetic',None,None,'declared')
            with self.assertRaisesRegex(RecordError,'unit-v4 protected references'):
                replay_groups(dict(unit_groups=[dict(output_units=[unit])]),[],[],None,None,None,None)


def adoption_fixture(base):
    """A complete synthetic v6 freeze and literal six-field fixture output."""
    from test_source_adoptions import synthetic_fixture, write
    root,harvest,fp,rp,frozen,raw=synthetic_fixture(base,typed=False)
    text=(harvest/'test.tex').read_text().replace('A claim.\n', 'A synthetic claim.\n'+CUP+'\n')
    text=text.replace('\\end{document}', '\\begin{remark}\\label{remark-cup-product}Synthetic reference.\\end{remark}\n\\end{document}')
    (harvest/'test.tex').write_text(text)
    with (harvest/'tags/tags').open('a') as f:f.write('0003,test-remark-cup-product\n')
    git(harvest,'add','.')
    git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic protected reference source')
    source=git(harvest,'rev-parse','HEAD')
    (root/'upstream.lock').write_text('commit = "'+source+'"\n')
    (root/'config/macro-policy.yml').write_text(synthetic_policy())
    shutil.copyfile(ROOT/'schema/math-text-references.schema.json',root/'schema/math-text-references.schema.json')
    native=Containers(root,harvest)
    groups=[native.select(selector('prose_block',owner='0000')),native.select(selector('lemma'))]
    units=[lower_container(g,native.policy)[0] for g in groups]
    catalog=json.loads((root/'config/source-terms.json').read_text());catalog['source_commit']=source
    catalog['terms'][0]['evidence'][0]['source_tex_hash']=byte_hash(source_tex(units[0]))
    write(root/'config/source-terms.json',catalog)
    git(root,'add','config','schema','upstream.lock')
    git(root,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic accepted v6 policy origin; no facts')
    frozen.update(tool_version='source-adoption-input-v6',source_commit=source,origin_commit=git(root,'rev-parse','HEAD'),
        policies=[dict(path=p,hash=byte_hash((root/p).read_bytes())) for p in REFERENCE_POLICIES])
    for batch,group,unit in zip(frozen['batches'],groups,units,strict=True):
        batch.update(units=[unit],containers=[dict(selector=group['selector'],selected=group,unit_ids=[unit['unit_id']])])
        write_jsonl(root/batch['units_path'],[unit])
    contexts=[]
    for row in native.document('test')[1]:
        value=dict(kind='locked-English-neighbor',location=row['location'],source_commit=source,
            source_unit=row['unit'],owner_tag=row['owner_tag'],parent_tag=row['parent_tag'])
        if row['owner_tag']=='0003':value.update(requested_label='test-remark-cup-product',requested_tag='0003',kind='locked-English-reference')
        contexts.append(dict(context_id=row['unit']['unit_id'],value=value,hash=sha256_value(value)))
    frozen['contexts']=contexts
    scope_path=root/frozen['task']['scope_manifest'];scope=json.loads(scope_path.read_text());scope['source_commit']=source
    write(scope_path,scope);frozen['task'].update(scope_bytes=scope_path.read_text(),scope_manifest_sha256=byte_hash(scope_path.read_bytes()))
    write(fp,frozen)
    raw[1]=dict(unit_id=units[1]['unit_id'],translation='合成断言。\n<MATHSEG_0001>注释 <MATHSEG_0002>朴素杯积<MATHSEG_0003>\n',
        allowed_english=[],term_occurrences=[],unknown_terms=[],notes=['Literal synthetic fixture; no model generation.'])
    write_jsonl(rp,raw)
    return root,harvest,fp,rp,frozen,raw


class ReferenceAdoptionTests(unittest.TestCase):
    def test_complete_v6_raw_freeze_provenance_and_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,fp,rp,frozen,raw=adoption_fixture(Path(tmp))
            record=assemble_source_adoption(root,fp,[rp],harvest)
            self.assertEqual(record['tool_version'],'source-adoption-v6')
            adopted,errors=load_repository_source_adoptions(root,harvest)
            self.assertEqual(errors,[])
            self.assertEqual(validate_repository_provenance(root,harvest),[])
            candidate=adopted[(frozen['batches'][1]['candidates_path'],raw[1]['unit_id'])]['candidate']
            self.assertEqual(candidate['translation'],raw[1]['translation'])
            render_batch([root/b['units_path'] for b in frozen['batches']],
                [root/b['candidates_path'] for b in frozen['batches']], root/'upstream.lock',
                root/'preview','synthetic','Synthetic test fixture',chapter_source_dir=harvest,tags_path=harvest/'tags/tags')
            text=(root/'preview/chapters/test.tex').read_text()
            self.assertIn(r'\text{注释 \href{https://stacks.math.columbia.edu/tag/0003}{Tag 0003（待译）}}',text)
            self.assertIn(r'\text{朴素杯积}',text)

    def test_old_adoption_versions_and_incomplete_freezes_write_no_candidates(self):
        from test_source_adoptions import write
        for mutation in ['v1','v2','v3','v4','v5','missing-policy','wrong-raw','missing-reference-context']:
            with tempfile.TemporaryDirectory() as tmp:
                root,harvest,fp,rp,frozen,raw=adoption_fixture(Path(tmp))
                if mutation.startswith('v'):
                    frozen['tool_version']='source-adoption-input-'+mutation
                    frozen['policies']=[e for e in frozen['policies'] if e['path'] in POLICIES]
                elif mutation=='missing-policy':frozen['policies'].pop()
                elif mutation=='missing-reference-context':
                    frozen['contexts']=[c for c in frozen['contexts'] if c['value']['owner_tag']!='0003']
                else:
                    raw[1]['translation']=raw[1]['translation'].replace('<MATHSEG_0002>','<MATHSEG_0001>');write_jsonl(rp,raw)
                write(fp,frozen)
                with self.subTest(mutation=mutation),self.assertRaises(RecordError):
                    assemble_source_adoption(root,fp,[rp],harvest)
                self.assertFalse(any((root/b['candidates_path']).exists() for b in frozen['batches']))
                self.assertFalse((root/'translation-data/runs/run-synthetic-first.json').exists())

    def test_accepted_origin_has_separate_reference_capability(self):
        policies={p:(ROOT/p).read_bytes() for p in REFERENCE_POLICIES}
        _reference_origin(policies)
        old=copy.deepcopy(policies);schema=json.loads(old['schema/unit.schema.json'])
        schema['oneOf']=[b for b in schema['oneOf'] if b['properties']['schema_version']['const']!=4]
        old['schema/unit.schema.json']=json.dumps(schema).encode()
        with self.assertRaisesRegex(RecordError,'accepted origin'):_reference_origin(old)

    def test_v6_rejects_an_origin_without_explicit_adoption_permission(self):
        from test_source_adoptions import write
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,fp,rp,frozen,_=adoption_fixture(Path(tmp))
            path=root/'schema/source-adoption-input.schema.json';schema=json.loads(path.read_text())
            schema['properties']['tool_version']['enum'].remove('source-adoption-input-v6')
            schema['oneOf']=[b for b in schema['oneOf'] if b['properties']['tool_version']['const']!='source-adoption-input-v6']
            write(path,schema);git(root,'add','schema/source-adoption-input.schema.json')
            git(root,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic old accepted capability')
            frozen['origin_commit']=git(root,'rev-parse','HEAD')
            frozen['policies']=[dict(path=p,hash=byte_hash((root/p).read_bytes())) for p in REFERENCE_POLICIES]
            write(fp,frozen)
            with self.assertRaisesRegex(RecordError,'accepted origin does not permit source-adoption-input-v6'):
                assemble_source_adoption(root,fp,[rp],harvest)
            self.assertFalse(any((root/b['candidates_path']).exists() for b in frozen['batches']))


class LockedSourceWitnessTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires read-only locked English harvest')
    def test_real_complete_containers_schema_hashes_and_unchanged_source_bytes(self):
        report=json.loads((ROOT/'tests/fixtures/sites-cohomology21-source-text-tool-20261109.json').read_text())
        native=Containers(ROOT,Path(os.environ['HARVEST_DIR']),policy_bytes=report['policy_probe'].encode())
        self.assertEqual(native.english.commit,report['source_commit'])
        for witness in report['math_text']['witnesses']:
            actual=native.select(witness['selected']['selector'])
            self.assertEqual(actual,witness['selected'])
            units=lower_container(actual,native.policy)
            self.assertEqual(units,witness['units'])
            self.assertEqual(''.join(source_tex(u) for u in units),actual['fragment'])
            for unit in units:
                self.assertEqual(validate_regions(unit),[])
                self.assertEqual(validate_named_schema(unit,'unit.schema.json',unit['unit_id']),[])
        _,rows,diagnostics=native.document('sites-cohomology')
        self.assertEqual(len(rows),report['math_text']['summary']['containers'])
        self.assertFalse(any(d['kind']=='math-text' for d in diagnostics))

    def test_actual_existing_assignment_witnesses_keep_every_other_term(self):
        from stacks_zh.source_terms import load_catalog,source_inventory
        report=json.loads((ROOT/'tests/fixtures/sites-cohomology21-source-text-tool-20261109.json').read_text())
        words=load_catalog(ROOT)
        for change in report['source_terms']['changed_current']:
            self.assertEqual(source_inventory(change['unit'],words),change['after'])
            removed=[o for o in change['before']['occurrences'] if o not in change['after']['occurrences']]
            self.assertEqual([o['source_term'].casefold() for o in removed],['set'])
            self.assertFalse(any(o not in change['before']['occurrences'] for o in change['after']['occurrences']))


class ReferencePreparationCurrentTests(unittest.TestCase):
    def test_complete_v6_preparation_copies_reach_current_acceptance(self):
        from test_chapter_validation import preparation_copy
        from test_source_adoptions import write
        from stacks_zh.chapter_validation import check_chapter
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,fp,rp,frozen,raw=adoption_fixture(Path(tmp))
            mp,rt=preparation_copy(root,frozen,fp,rp)
            assemble_source_adoption(root,fp,[rp],harvest)
            result=check_chapter(root,harvest,'test','synthetic',frozen['origin_commit'],current_all=True)
            self.assertEqual(result.report['preparations'][0]['status'],'adopted-input-copy-verified')
            self.assertEqual(result.report['exit_status'],0)
            original=mp.read_bytes();value=json.loads(original)
            value['policy_files']=[e for e in value['policy_files'] if e['path']!='schema/math-text-references.schema.json']
            write(mp,value)
            with self.assertRaisesRegex(RecordError,'model-input evidence differs from its complete frozen inputs'):
                check_chapter(root,harvest,'test','synthetic',frozen['origin_commit'],current_all=True)
            mp.write_bytes(original)
            runtime=json.loads(rt.read_bytes());runtime['turn_metadata']['model']='other-synthetic-model'
            write(rt,runtime)
            with self.assertRaisesRegex(RecordError,'runtime turn metadata differs from frozen identity'):
                check_chapter(root,harvest,'test','synthetic',frozen['origin_commit'],current_all=True)


if __name__=='__main__':unittest.main()
