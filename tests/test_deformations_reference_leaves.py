"""Complete source/typed/adoption tests; every generated fixture is synthetic."""
import copy, json, os, re, subprocess, unittest
from pathlib import Path
from stacks_zh import math_text_deformations_references as refs
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import nodes
from stacks_zh.source_reextractions import byte_hash, source_tex, LockedEnglish
from stacks_zh.schema_validation import load_schema, validate_named_schema
ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/fixtures/deformations-reference-leaves.json').read_text())
FRAMES = tuple((v['frame'] for v in FIXTURE['frames']))

class DeformationsReferenceLeavesTests(unittest.TestCase):

    def schema_regions(self, frame):
        slots = []
        stream = nodes(frame)
        for index, node in enumerate(stream):
            if not refs.literal_contract(node.get('value')):
                continue
            witness = dict(usage=refs.REFERENCE_USAGE, usage_source=refs.usage(frame, stream, index, refs.REFERENCE_USAGE), source_label='defos-reference-shape-test', policy_hash=byte_hash('synthetic shape-only policy'), anchor=dict(source_commit=FIXTURE['source_commit'], file='defos.tex', owner_tag='08LB', owner_label='defos-reference-shape-test', kind='remark', ordinal=1, matches=[]))
            for leaf in refs.reference_leaves(frame, node):
                slots.append(dict(slot_id=f'math/0001/text/{len(slots) + 1:04d}', source=leaf['value'], command='text', policy_entry='deformations-reference-shape-test', classification_witness=copy.deepcopy(witness), slot_byte_span=dict(start=len(frame[:leaf['parameter_start']].encode()), end=len(frame[:leaf['parameter_end']].encode())), boundary_placeholders=['MATHSEG_0001', 'MATHSEG_0002'], parameter_reference_leaves=leaf['parameter_reference_leaves']))
        return [dict(region_id='math/0001', delimiter_kind='display-dollar', source=frame, source_hash=byte_hash(frame), source_byte_span=dict(start=0, end=len(frame.encode())), pieces=[], slots=slots)]

    def test_dormant_schema_with_native_repository_validator(self):
        load_schema('math-text-internal-references.schema.json')
        count = 0
        for frame in FRAMES:
            regions = self.schema_regions(frame)
            count += len(regions[0]['slots'])
            self.assertFalse(validate_named_schema(regions, 'math-text-internal-references.schema.json', 'shape-only'))
            self.assertTrue(validate_named_schema(regions, 'math-text-references.schema.json', 'legacy-rejection'))
        self.assertEqual(count, 20)

    def test_dormant_schema_rejects_role_leaf_and_reference_mismatch(self):
        baseline = self.schema_regions(FRAMES[0])
        mutations = (('source', ' with '), ('source', ' as in'), ('command', 'eqref'), ('unexpected', True))
        for field, value in mutations:
            changed = copy.deepcopy(baseline)
            changed[0]['slots'][0][field] = value
            self.assertTrue(validate_named_schema(changed, 'math-text-internal-references.schema.json', field))
        for field, value in (
            ('leaf_index', 2), ('leaf_index', 3), ('leaf_index', True),
            ('leaf_index', 1.0), ('leaf_count', 1), ('leaf_count', 2.0),
            ('reference_label', 'other'), ('reference_command', 'eqref'),
            ('separator', '\\ref{equation-extension}'),
            ('parameter_source', ' as in (\\ref{other}) with '),
        ):
            changed = copy.deepcopy(baseline)
            changed[0]['slots'][0]['parameter_reference_leaves'][field] = value
            self.assertTrue(validate_named_schema(changed, 'math-text-internal-references.schema.json', field))
        changed = copy.deepcopy(baseline)
        changed[0]['slots'][0]['classification_witness']['usage'] = refs.PLAIN_USAGE
        self.assertTrue(validate_named_schema(changed, 'math-text-internal-references.schema.json', 'wrong-role'))

    def test_exact_source_parameter_and_protected_separator(self):
        self.assertEqual(refs.FRAMES, FRAMES)
        self.assertEqual(len(FRAMES), 6)
        for label in ('equation-extension', 'equation-extension-ringed-topoi'):
            literal = ' as in (\\ref{' + label + '}) with '
            expected = dict(prefix=' as in ', separator='(\\ref{' + label + '})', suffix=' with ', reference_source='\\ref{' + label + '}', reference_command='ref', reference_label=label)
            self.assertEqual(refs.literal_contract(literal), expected)
            self.assertEqual(refs.split_parameter(literal), (' as in ', expected['separator'], ' with '))
            self.assertEqual(refs.split_parameter('如 ' + expected['separator'] + ' 且 '), ('如 ', expected['separator'], ' 且 '))
        for bad in ('as in (\\ref{equation-extension}) with ', ' as in (\\ref{other}) with ', ' as in \\ref{equation-extension} with ', ' as in (\\eqref{equation-extension}) with '):
            self.assertIsNone(refs.literal_contract(bad))
        for bad in ('(\\ref{equation-extension}) suffix', 'prefix(\\ref{equation-extension})', 'prefix(\\ref{equation-extension})(\\ref{equation-extension})suffix', 'prefix(\\ref{other})suffix', 'prefix(\\ref{equation-extension})suffix\\ref{other}', 'prefix(\\ref{equation-extension}){suffix}'):
            self.assertIsNone(refs.split_parameter(bad))

    def test_finite_roles_keep_all_other_frame_bytes(self):
        for frame in FRAMES:
            stream = nodes(frame)
            self.assertTrue(refs.matches(frame, stream, frame))
            for index, node in enumerate(stream):
                if node.get('command') != 'text':
                    continue
                kind = refs.REFERENCE_USAGE if refs.literal_contract(node['value']) else refs.PLAIN_USAGE
                self.assertIsNotNone(refs.usage(frame, stream, index, kind))
                self.assertIsNone(refs.usage(frame, stream, index, refs.PLAIN_USAGE if kind == refs.REFERENCE_USAGE else refs.REFERENCE_USAGE))
            changed = frame
            for node in reversed(stream):
                if node.get('command') != 'text':
                    continue
                contract = refs.literal_contract(node['value'])
                value = '如 ' + contract['separator'] + ' 且 ' if contract else '合成自然文字'
                changed = changed[:node['parameter_start']] + value + changed[node['parameter_end']:]
            self.assertTrue(refs.matches(changed, nodes(changed), frame))
            for bad in (frame + 'x', frame.replace('\\text{', '\\textbf{', 1), frame.replace('$$', '$$ ', 1), frame.replace('\\ref{equation-extension', '\\ref{other-extension', 1), frame.replace('\\mathcal{F}', '\\mathcal{Q}', 1), frame.replace('\\longrightarrow', '\\longleftarrow', 1)):
                if bad == frame:
                    continue
                try:
                    valid = refs.matches(bad, nodes(bad), frame)
                except ValueError:
                    valid = False
                self.assertFalse(valid, bad)

    def test_two_leaf_spans_preserve_reference_and_parentheses(self):
        for frame in FRAMES:
            for node in nodes(frame):
                if not refs.literal_contract(node.get('value')):
                    continue
                leaves = refs.reference_leaves(frame, node)
                self.assertEqual([s['value'] for s in leaves], [' as in ', ' with '])
                self.assertEqual([s['parameter_reference_leaves']['leaf_index'] for s in leaves], [1, 2])
                meta = leaves[0]['parameter_reference_leaves']
                span = meta['separator_byte_span']
                self.assertEqual(frame.encode()[span['start']:span['end']].decode(), meta['separator'])
                span = meta['reference_byte_span']
                self.assertEqual(frame.encode()[span['start']:span['end']].decode(), meta['reference_source'])
                start, end = (leaves[0]['parameter_end'], leaves[1]['parameter_start'])
                self.assertEqual(frame[start:end], meta['separator'])
                corrupt = copy.deepcopy(node)
                corrupt['parameter_start'] += 1
                with self.assertRaises(ValueError):
                    refs.reference_leaves(frame, corrupt)

    def test_absent_internal_policy_keeps_all_frames_blocked(self):
        text = (ROOT / 'config/macro-policy.yml').read_text()
        text = text.split('\ntranslatable_math_text_internal_references:')[0]
        policy = Policy(text)
        for frame in FRAMES:
            self.assertTrue(Scanner(frame, policy).protect(0, len(frame))[2])

    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit locked read-only harvest')
    def test_independent_full_locked_git_bytes(self):
        raw = subprocess.check_output(['git', 'show', FIXTURE['source_commit'] + ':defos.tex'], cwd=os.environ['HARVEST_DIR'])
        self.assertEqual(byte_hash(raw), FIXTURE['blob_hash'])
        self.assertTrue(FIXTURE['source_only'])
        self.assertFalse(FIXTURE['actual_model_data'])
        english = LockedEnglish(ROOT, Path(os.environ['HARVEST_DIR']))
        self.assertEqual(len(FIXTURE['containers']), 6)
        for container in FIXTURE['containers']:
            coordinate = container['selector']
            location = container['location']
            fragment = raw[location['byte_start']:location['byte_end']].decode()
            self.assertEqual(fragment, container['fragment'])
            self.assertEqual(byte_hash(fragment), location['fragment_hash'])
            self.assertEqual(source_tex(container['preparation_unit']), fragment)
            self.assertEqual(english.tags[coordinate['owner_label']], coordinate['owner_tag'])
            self.assertEqual(coordinate['kind'], 'remark')
            self.assertEqual(container['source_status'], 'BLOCKED')
        for witness in FIXTURE['frames']:
            span = witness['frame_byte_span']
            payload = raw[span['start']:span['end']]
            self.assertEqual(payload.decode(), witness['frame'])
            self.assertEqual(byte_hash(payload), witness['frame_hash'])
            self.assertEqual(raw.count(payload), 1)

# Actual public modules after integration; no build-only snapshots or monkey patches.
import shutil, tempfile
from stacks_zh import math_text as math, records, extraction, source_containers as containers
from stacks_zh import source_adoptions as adopt, provenance, group_derivations as groups, workflow
from stacks_zh import chapter_preflight as preflight
from stacks_zh.math_text_deformations_references import PREFIX, SUFFIX
from test_source_adoptions import synthetic_fixture, write
from test_source_containers import git, selector
R = ROOT
schemas = ROOT / 'schema'

def _internal_policy_entry(key, values):
    return '  ' + key + ':\n' + ''.join('    ' + k + ': ' + json.dumps(v) + '\n' for k, v in values.items())


def internal_probe_policy():
    # An explicit isolated opt-in probe; production literal adoption is separate.
    production = subprocess.check_output(['git', 'show',
        FIXTURE['accepted_base'] + ':config/macro-policy.yml'], cwd=ROOT).decode('utf-8')
    plain = _internal_policy_entry('internal-reference-extension-classes', dict(
        literal='isomorphism classes of extensions', command='text', usage=refs.PLAIN_USAGE,
        source_label='defos-remark-trivial-extension', witness_kind='remark', witness_ordinal=1))
    base = next(key for key, rule in Policy(production).math_text_rules.items()
                if rule['literal'] == ' and ' and rule['usage'] == 'root-phrase')
    context = _internal_policy_entry('internal-reference-and', dict(base_rule=base,
        usage=refs.PLAIN_USAGE, source_label='defos-remark-extension-functorial',
        witness_kind='remark', witness_ordinal=1))
    policy = production.replace('translatable_math_text:\n', 'translatable_math_text:\n' + plain)
    policy = policy.replace('translatable_math_text_contexts:\n', 'translatable_math_text_contexts:\n' + context)
    policy += '\ntranslatable_math_text_internal_references:\n'
    for index, (_, separator) in enumerate(refs.REFERENCES.items(), 1):
        source_label = ('defos-remark-trivial-extension' if index == 1
                        else 'defos-remark-trivial-extension-ringed-topoi')
        policy += _internal_policy_entry('internal-reference-' + str(index), dict(
            literal=PREFIX + separator + SUFFIX, command='text', usage=refs.REFERENCE_USAGE,
            source_label=source_label, witness_kind='remark', witness_ordinal=1))
    return policy


def internal_adoption_fixture(base):
 root,harvest,fp,rp,frozen,raw=synthetic_fixture(base,typed=False)
 src=(harvest/'test.tex').read_text().replace('\\begin{lemma}\\label{lemma-one}A claim.\n\\end{lemma}',
  '\\begin{remark}\\label{lemma-one}A claim.\n\\begin{equation}\\label{equation-extension}x=0\\end{equation}\n'+FRAMES[0]+'\n\\end{remark}')
 assert FRAMES[0] in src;(harvest/'test.tex').write_text(src)
 git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic internal reference source')
 source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
 policy=(R/'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0]+'''
translatable_math_text:
  extension-classes:
    literal: "isomorphism classes of extensions"
    command: "text"
    usage: "deformations-reference-frame-text"
    source_label: "test-lemma-one"
    witness_kind: "remark"
    witness_ordinal: 1
translatable_math_text_internal_references:
  extension-reference:
    literal: " as in (\\\\ref{equation-extension}) with "
    command: "text"
    usage: "deformations-extension-reference"
    source_label: "test-lemma-one"
    witness_kind: "remark"
    witness_ordinal: 1
'''
 (root/'config/macro-policy.yml').write_text(policy)
 for p in schemas.glob('*.json'):shutil.copyfile(p,root/'schema'/p.name)
 native=containers.Containers(root,harvest)
 selectors=[selector('prose_block',owner='0000'),{**selector('lemma'),'kind':'remark'}]
 selected=[native.select(s) for s in selectors];units=[containers.lower_container(s,native.policy)[0] for s in selected]
 assert [u['schema_version'] for u in units]==[1,5]
 catalog=json.loads((root/'config/source-terms.json').read_bytes());catalog['source_commit']=source
 catalog['terms'][0]['evidence'][0]['source_tex_hash']=byte_hash(source_tex(units[0]));write(root/'config/source-terms.json',catalog)
 git(root,'add','config','schema','upstream.lock');git(root,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic accepted v7 capability')
 frozen.update(tool_version='source-adoption-input-v7',source_commit=source,origin_commit=git(root,'rev-parse','HEAD'),policies=[dict(path=p,hash=adopt.byte_hash((root/p).read_bytes())) for p in adopt.INTERNAL_REFERENCE_POLICIES])
 for b,s,u in zip(frozen['batches'],selected,units,strict=True):
  b.update(units=[u],containers=[dict(selector=s['selector'],selected=s,unit_ids=[u['unit_id']])]);records.write_jsonl(root/b['units_path'],[u])
 contexts=[]
 for row in native.document('test')[1]:
  value=dict(kind='locked-English-neighbor',location=row['location'],source_commit=source,source_unit=row['unit'],owner_tag=row['owner_tag'],parent_tag=row['parent_tag'])
  contexts.append(dict(context_id=row['unit']['unit_id'],value=value,hash=records.sha256_value(value)))
 frozen['contexts']=contexts
 scope_path=root/frozen['task']['scope_manifest'];scope=json.loads(scope_path.read_bytes());scope['source_commit']=source
 ids=[u['unit_id'] for u in units]
 scope['data_scopes'][0].update(unit_ids=ids,input_unit_ids=ids,output_unit_ids=ids)
 write(scope_path,scope);frozen.update(unit_ids=ids)
 frozen['task'].update(scope_bytes=scope_path.read_text(),scope_manifest_sha256=adopt.byte_hash(scope_path.read_bytes()));write(fp,frozen)
 t=units[1]['source_text'].replace('A claim.','合成断言。')
 for reg in units[1]['math_text_regions']:
  for slot in reg['slots']:
   l,r=['<'+p+'>' for p in slot['boundary_placeholders']];a=t.index(l)+len(l);b=t.index(r,a)
   t=t[:a]+(' 如 ' if slot['source']==PREFIX else ' 其中 ' if slot['source']==SUFFIX else '合成扩张类')+t[b:]
 raw[1]=dict(unit_id=units[1]['unit_id'],translation=t,allowed_english=[],term_occurrences=[],unknown_terms=[],notes=['Synthetic fixture; no actual model run.']);records.write_jsonl(rp,raw)
 return root,harvest,fp,rp,frozen,raw,units

class InternalReferenceAdoptionTests(unittest.TestCase):
 def test_complete_first_v7_and_active_provenance(self):
  with tempfile.TemporaryDirectory() as tmp:
   root,harvest,fp,rp,frozen,raw,units=internal_adoption_fixture(Path(tmp))
   record=adopt.assemble_source_adoption(root,fp,[rp],harvest)
   self.assertEqual(record['tool_version'],'source-adoption-v7')
   validated,errors=adopt.load_repository_source_adoptions(root,harvest);self.assertEqual(errors,[])
   self.assertEqual(provenance.validate_repository_provenance(root,harvest),[])
   self.assertEqual(validated[(frozen['batches'][1]['candidates_path'],units[1]['unit_id'])]['candidate']['translation'],raw[1]['translation'])
   workflow.render_batch([root/b['units_path'] for b in frozen['batches']], [root/b['candidates_path'] for b in frozen['batches']],root/'upstream.lock',root/'preview','synthetic','Synthetic internal references',chapter_source_dir=harvest,tags_path=harvest/'tags/tags')
   text=(root/'preview/chapters/test.tex').read_text()
   self.assertIn(r'\text{ 如 (\ref{test-equation-extension}) 其中 }',text)
   self.assertEqual(text.count(r'\ref{test-equation-extension}'),1)
 def test_historical_preparation_rejects_complete_committed_v7_batch(self):
  with tempfile.TemporaryDirectory() as tmp:
   root,harvest,fp,rp,frozen,raw,units=internal_adoption_fixture(Path(tmp))
   adopt.assemble_source_adoption(root,fp,[rp],harvest)
   git(root,'add','.');git(root,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic v7 fixture facts only')
   b=frozen['batches'][1]
   for chosen in [None,b['containers'][0]['selector']]:
    plan=dict(derivation_id='synthetic-forbidden-restore',created_at='2026-11-16T00:00:00Z',units_file=b['units_path'],candidates_file=b['candidates_path'],groups=[dict(group_id='synthetic-refusal',input_unit_ids=[units[1]['unit_id']],identity_anchor=units[1]['unit_id'],selector=chosen,layout='whole',reason='Synthetic refusal witness')])
    with self.subTest(selector=chosen),self.assertRaisesRegex(records.RecordError,'historical source-container preparation cannot process unit-v5'):
     containers.prepare_containers(root,harvest,plan)
 def test_public_failures_leave_no_candidate_record_or_run(self):
  for case in ['old-v1','old-v6','prior-attempt','prior-adoption','shared-history','missing-policy','missing-context','bad-raw']:
   with self.subTest(case=case),tempfile.TemporaryDirectory() as tmp:
    root,harvest,fp,rp,frozen,raw,units=internal_adoption_fixture(Path(tmp))
    if case.startswith('old-'):
     frozen['tool_version']='source-adoption-input-'+case[4:]
     permitted=adopt.REFERENCE_POLICIES if case=='old-v6' else adopt.POLICIES
     frozen['policies']=[dict(path=p,hash=adopt.byte_hash((root/p).read_bytes())) for p in permitted]
    elif case=='prior-attempt':frozen['batches'][0]['prior_attempts']=[{}]
    elif case=='prior-adoption':frozen['prior_adoptions']=[]
    elif case=='shared-history':frozen['shared_run_histories']=[]
    elif case=='missing-policy':frozen['policies'].pop()
    elif case=='missing-context':frozen['contexts']=[]
    else:
     raw[1]['translation']=raw[1]['translation'].replace('<MATHSEG_0001>','',1);records.write_jsonl(rp,raw)
    write(fp,frozen)
    with self.assertRaises(records.RecordError):adopt.assemble_source_adoption(root,fp,[rp],harvest)
    self.assertFalse(any((root/b['candidates_path']).exists() for b in frozen['batches']))
    self.assertFalse((root/'translation-data/runs/run-synthetic-first.json').exists())
    self.assertFalse((root/'translation-data/source-adoptions/synthetic-first.json').exists())
 def test_old_versions_and_component_coexistence_refuse_new_unit(self):
  for v in range(1,7):
   with self.subTest(v=v),self.assertRaisesRegex(records.RecordError,'unit-v5'):
    adopt._first_reference_contract([dict(schema_version=5)],'source-adoption-input-v'+str(v))
  for v in [3,4]:
   with self.subTest(v=v),self.assertRaises(records.RecordError):adopt._first_reference_contract([dict(schema_version=5),dict(schema_version=v)],'source-adoption-input-v7')
 def test_origin_capability_and_schema_are_independent(self):
  data={p:(schemas/Path(p).name).read_bytes() if p.startswith('schema/') else (R/p).read_bytes() for p in adopt.INTERNAL_REFERENCE_POLICIES}
  adopt._internal_reference_origin(data)
  for case in ['unit','independent','input','record']:
   bad=copy.deepcopy(data)
   if case=='unit':
    p='schema/unit.schema.json';s=json.loads(bad[p]);s['oneOf']=[b for b in s['oneOf'] if b['properties']['schema_version']['const']!=5];bad[p]=json.dumps(s).encode()
   elif case=='independent':bad.pop('schema/math-text-internal-references.schema.json')
   else:
    p='schema/source-adoption-input.schema.json' if case=='input' else 'schema/source-adoption.schema.json';s=json.loads(bad[p]);s['properties']['tool_version']['enum'].pop();bad[p]=json.dumps(s).encode()
   with self.subTest(case=case),self.assertRaisesRegex(records.RecordError,'accepted origin'):adopt._internal_reference_origin(bad)
 def test_ordinary_assembly_and_historical_group_reject(self):
  with tempfile.TemporaryDirectory() as tmp:
   root,harvest,fp,rp,frozen,raw,units=internal_adoption_fixture(Path(tmp));unit=units[1]
   with self.assertRaisesRegex(records.RecordError,'ordinary assembly'):
    workflow._assemble_candidates_with_harness_version(root/frozen['batches'][1]['units_path'],root/'absent.jsonl',root/'out.jsonl',root/'upstream.lock','synthetic','synthetic','synthetic','translator-v2','synthetic','synthetic','2026-11-09T00:00:00Z','synthetic','synthetic','synthetic',None,None,'declared')
   with self.assertRaisesRegex(records.RecordError,'unit-v5 internal references'):
    groups.replay_groups(dict(unit_groups=[dict(output_units=[unit])]),[],[],None,None,None,None)

class InternalReferenceHistoricalEntryTests(unittest.TestCase):
 def test_second_ordinary_assembly_entry_rejects_complete_v5(self):
  with tempfile.TemporaryDirectory() as tmp:
   root,harvest,fp,rp,frozen,raw,units=internal_adoption_fixture(Path(tmp))
   with self.assertRaisesRegex(records.RecordError,'ordinary assembly'):
    workflow.assemble_candidates_many([root/b['units_path'] for b in frozen['batches']],rp,[root/b['candidates_path'] for b in frozen['batches']],root/'upstream.lock','synthetic','synthetic','synthetic','translator-v2','synthetic','synthetic','2026-11-16T00:00:00Z','synthetic',model_record_id='synthetic:fixture:declared',run_id='synthetic-forbidden-ordinary',harness_config_path=root/'config/harnesses.yml')
   self.assertFalse(any((root/b['candidates_path']).exists() for b in frozen['batches']))
 def test_historical_restoration_loader_rejects_after_full_source_and_snapshot_binding(self):
  with tempfile.TemporaryDirectory() as tmp:
   root,harvest,fp,rp,frozen,raw,units=internal_adoption_fixture(Path(tmp))
   adopt.assemble_source_adoption(root,fp,[rp],harvest)
   batch=frozen['batches'][1];selected=batch['containers'][0]['selected'];identifier='synthetic-historical-reference'
   files={}
   for role,content,name in [('input_units',[units[1]],'units'),('input_candidates',records.load_jsonl(root/batch['candidates_path']),'candidates')]:
    p=root/('translation-data/retired/derivations/'+identifier+'/'+name+'.jsonl');p.parent.mkdir(parents=True,exist_ok=True);records.write_jsonl(p,content)
    files[role]=dict(path=p.relative_to(root).as_posix(),hash=adopt.byte_hash(p.read_bytes()))
   e={k:copy.deepcopy(selected[k]) for k in ['source_commit','selector','fragment','location','blob_oid','blob_hash','macro_policy_hash','boundary_witness']}
   e.update(schema_version=1,restoration_id=identifier,derivation_id=identifier,group_id='synthetic-forbidden-reference',created_at='2026-11-16T00:00:00Z',origin_commit=frozen['origin_commit'],tool=dict(id='stacks-zh-source-container',version='source-container-v3'),layout='whole',input_unit_ids=[units[1]['unit_id']],output_unit_ids=[units[1]['unit_id']],new_units=[units[1]],files=files,reason='Synthetic historical refusal; not candidate adoption')
   write(root/('translation-data/source-container-restorations/'+identifier+'.json'),e)
   git(root,'add','.');git(root,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic forbidden historical record for refusal test')
   values,errors=containers.load_source_containers(root,harvest)
   self.assertEqual(values,{})
   self.assertEqual(len(errors),1,errors)
   self.assertIn('historical source-container restoration cannot adopt unit-v5 internal references',errors[0])

class InternalReferencePreflightTests(unittest.TestCase):
 def test_complete_section_owned_v5_selectors_report_first_v7_only(self):
  with tempfile.TemporaryDirectory() as tmp:
   root,harvest,fp,rp,frozen,raw,units=internal_adoption_fixture(Path(tmp));native=containers.Containers(root,harvest)
   selected=frozen['batches'][1]['containers'][0]['selected'];selector=selected['selector']
   row=next(r for r in native.document('test')[1] if r['owner_tag']=='0001' and r['unit']['node_kind']=='remark')
   item=preflight._prepared(dict(selector=selector,inventory_ids=[row['inventory_id']],inventory_states=[row['state']]),native,{'0000':1,'0001':1})
   self.assertEqual(item['state'],'READY',item.get('reasons'))
   self.assertEqual(item['source_contract'],'source-adoption-v7; complete first generation only, no historical restoration/revision permission')
   self.assertTrue(item['contract_support']['first_adoption_shape'])
   self.assertFalse(item['contract_support']['automatic_adoption_permission'])
   native.assert_unchanged()

@unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit locked read-only harvest')
class InternalReferenceFullSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = containers.Containers(
            ROOT, Path(os.environ['HARVEST_DIR']), policy_bytes=internal_probe_policy().encode())
        cls.units = []
        # Canonical selectors remain actual complete locked-Git containers.
        selectors = [c['selector'] for c in FIXTURE['containers']]
        for selector in selectors:
            selected = cls.native.select(selector)
            rows = containers.lower_container(selected, cls.native.policy)
            assert len(rows) == 1
            cls.units.append((selected, rows[0]))

    def test_six_complete_locked_containers_native_lower_and_twenty_leaves(self):
        self.assertEqual(len(self.units), 6)
        leaves = []
        for selected, unit in self.units:
            self.assertEqual(unit['schema_version'], 5)
            self.assertEqual(source_tex(unit), selected['fragment'])
            self.assertEqual(records._validate_unit(unit, selected['source_commit']), [])
            self.assertEqual(math.validate_regions(unit), [])
            leaves.extend(slot for region in unit['math_text_regions'] for slot in region['slots']
                          if 'parameter_reference_leaves' in slot)
        self.assertEqual(len(leaves), 20)
        self.assertEqual([s['parameter_reference_leaves']['leaf_index'] for s in leaves], [1, 2] * 10)
        self.native.assert_unchanged()

    def test_translation_varies_only_plain_leaves_and_retains_full_reference_bytes(self):
        for selected, unit in self.units:
            translation = unit['source_text']
            for region in unit['math_text_regions']:
                for slot in region['slots']:
                    before, after = ['<' + name + '>' for name in slot['boundary_placeholders']]
                    start = translation.index(before) + len(before)
                    stop = translation.index(after, start)
                    target = ' 如 ' if slot['source'] == PREFIX else ' 其中 ' if slot['source'] == SUFFIX else ' 合成文字 '
                    translation = translation[:start] + target + translation[stop:]
            self.assertEqual(math.validate_translation(unit, translation), [])
            restored = math.restore(unit, translation)
            for separator in refs.REFERENCES.values():
                self.assertEqual(restored.count(separator), selected['fragment'].count(separator))

    def test_ref_metadata_leaf_order_boolean_and_spans_cannot_be_forged(self):
        unit = self.units[0][1]
        original = next(slot for region in unit['math_text_regions'] for slot in region['slots']
                        if 'parameter_reference_leaves' in slot)
        faults = [('leaf_index', True), ('leaf_index', 2), ('leaf_count', 1),
                  ('reference_label', 'equation-other'), ('reference_source', r'\ref{equation-other}'),
                  ('separator', '(wrong)')]
        for field, value in faults:
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(unit)
                slot = next(s for r in changed['math_text_regions'] for s in r['slots']
                            if s['slot_id'] == original['slot_id'])
                slot['parameter_reference_leaves'][field] = value
                changed = records.stamp_unit_hashes(changed)
                self.assertTrue(math.validate_regions(changed))
        changed = copy.deepcopy(unit)
        slot = next(s for r in changed['math_text_regions'] for s in r['slots']
                    if 'parameter_reference_leaves' in s)
        slot['parameter_reference_leaves']['parameter_byte_span']['start'] += 1
        self.assertTrue(math.validate_regions(records.stamp_unit_hashes(changed)))

    def test_legacy_unit_versions_refuse_the_new_internal_reference_shape(self):
        for version in [1, 2, 3, 4]:
            changed = copy.deepcopy(self.units[0][1])
            changed['schema_version'] = version
            self.assertTrue(records._validate_unit(changed, changed['source_commit']))
        bad_policy = internal_probe_policy().replace('usage: \"deformations-reference-frame-text\"', 'usage: \"root-phrase\"', 1)
        with self.assertRaises(records.RecordError):
            extraction.Policy(bad_policy)

    def test_token_ref_bytes_and_unsupported_formula_mutations_are_rejected(self):
        unit = self.units[0][1]
        region = next(r for r in unit['math_text_regions'] if any('parameter_reference_leaves' in s for s in r['slots']))
        leaf = next(s for s in region['slots'] if 'parameter_reference_leaves' in s)
        first, last = ['<' + n + '>' for n in leaf['boundary_placeholders']]
        for translation in [unit['source_text'].replace(first, '', 1),
                            unit['source_text'].replace(first, first + first, 1),
                            unit['source_text'].replace(first, '<MATHSEG_9999>', 1)]:
            self.assertTrue(math.validate_translation(unit, translation))
        changed = copy.deepcopy(unit)
        key = next(k for k, value in changed['placeholders'].items() if '\\ref{equation-extension}' in value)
        changed['placeholders'][key] = changed['placeholders'][key].replace('equation-extension', 'equation-other')
        self.assertTrue(math.validate_regions(records.stamp_unit_hashes(changed)))
        for _, row in self.units:
            source = next(region['source'] for region in row['math_text_regions']
                          if any('parameter_reference_leaves' in slot for slot in region['slots']))
            self.assertIn(r'\mathcal{F}', source)
            mutated = source.replace(r'\mathcal{F}', r'\mathcal{G}', 1)
            self.assertNotEqual(source, mutated)
            scanner = extraction.Scanner(mutated, self.native.policy)
            _, _, errors = scanner.protect(0, len(mutated))
            self.assertTrue(errors)

if __name__ == '__main__':
    unittest.main()


class InternalReferenceContextSchemaTests(unittest.TestCase):
    """Source-only Schema probes; separate fixtures are not a complete adoption."""
    def context_probe(self):
        from test_sites_cohomology_math_text import reference_fixture
        with tempfile.TemporaryDirectory() as tmp:
            unit = reference_fixture(Path(tmp))[-1]
        self.assertEqual(unit['schema_version'], 4)
        frozen = dict(tool_version='source-adoption-input-v7', batches=[],
                      contexts=[dict(value=dict(source_unit=unit))])
        payloads = {'schema/' + path.name: path.read_bytes()
                    for path in schemas.glob('*.json')}
        return frozen, payloads

    def test_v7_validates_existing_v4_reference_context(self):
        frozen, payloads = self.context_probe()
        before = copy.deepcopy(frozen)
        adopt._validate_frozen_source_schemas(frozen, payloads, payloads)
        self.assertEqual(frozen, before)

    def test_v7_checks_reference_schema_in_both_original_and_current_inputs(self):
        frozen, payloads = self.context_probe()
        bad = dict(payloads)
        bad['schema/math-text-references.schema.json'] = json.dumps({'type': 'object'}).encode()
        for original, current in [(bad, payloads), (payloads, bad)]:
            with self.subTest(original_bad=original is bad), self.assertRaises(records.RecordError):
                adopt._validate_frozen_source_schemas(frozen, original, current)

    def test_legacy_mapping_and_v7_output_permissions_remain_unchanged(self):
        frozen, payloads = self.context_probe()
        frozen['tool_version'] = 'source-adoption-input-v6'
        with self.assertRaises(records.RecordError):
            adopt._validate_frozen_source_schemas(frozen, payloads, payloads)
        with self.assertRaises(records.RecordError):
            adopt._first_reference_contract([dict(schema_version=5), dict(schema_version=4)],
                                           'source-adoption-input-v7')
