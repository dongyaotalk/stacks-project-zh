"""Source-only finite compounds: complete witnesses, exact scoped catalog delta."""
import copy,hashlib,json,os,subprocess,unittest
from pathlib import Path
from stacks_zh.source_terms import load_catalog,source_projection,source_inventory,validate_catalog_evidence,_matches
from stacks_zh.source_containers import Containers,lower_container
from stacks_zh.records import stamp_unit_hashes
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=json.loads((ROOT/'tests/fixtures/deformations-compound-source-policy.json').read_text())
ORIGINAL=json.loads(subprocess.check_output(['git','show',FIXTURE['accepted_base']+':config/source-terms.json'],cwd=ROOT))
CATALOG=load_catalog(ROOT)
EVIDENCE_FIELDS=('kind','chapter','source_term','source_commit','selector','fragment_hash')
class DeformationsCompoundSourcePolicyTests(unittest.TestCase):
 def test_exact_catalog_delta_preserves_all_previous_entries(self):
  expected=copy.deepcopy(ORIGINAL)
  for case in FIXTURE['decisions']:
   if case['operation']=='new_scoped_source_phrase':
    entry={'id':case['concept'],'forms':[],'chapters':[case['chapter']],'evidence':[]};expected['terms'].append(entry)
   else:
    self.assertEqual(case['operation'],'extend_existing_scope_or_witnessed_form')
    entry=next(e for e in expected['terms'] if e['id']==case['concept'])
    if entry['chapters'] and case['chapter'] not in entry['chapters']:entry['chapters'].append(case['chapter'])
   for form,witness in zip(case['forms'],case['independent_locked_source_witnesses']):
    if form.casefold() not in {f.casefold() for f in entry['forms']}:entry['forms'].append(form)
    evidence={k:witness[k] for k in EVIDENCE_FIELDS}
    if evidence not in entry['evidence']:entry['evidence'].append(evidence)
   self.assertFalse(case['translation_or_glossary_approval'])
  payload=(json.dumps(expected,ensure_ascii=False,indent=2)+'\n').encode()
  self.assertEqual(CATALOG,expected);self.assertEqual((ROOT/'config/source-terms.json').read_bytes(),payload)
  self.assertEqual('sha256:'+hashlib.sha256(payload).hexdigest(),FIXTURE['proposal_catalog_hash'])
  self.assertEqual(len(FIXTURE['decisions']),56)
  self.assertEqual(sum(len(c['forms']) for c in FIXTURE['decisions']),70)
  self.assertFalse(FIXTURE['facts_changed']);self.assertFalse(FIXTURE['human_review_claimed'])
 def test_descriptive_clauses_are_not_registered_as_terms(self):
  excluded={'Noetherian complete local','equivalent to','presentation by a smooth prorepresentable groupoid in functors'}
  self.assertEqual(set(FIXTURE['actual_model_retry_required']),excluded)
  self.assertTrue(excluded.isdisjoint({f for e in CATALOG['terms'] for f in e['forms']}))
 def test_added_concepts_keep_chapter_scope_and_protected_math_boundaries(self):
  for case in FIXTURE['decisions']:
   if case['operation']!='new_scoped_source_phrase':continue
   form=case['forms'][0]
   unit=stamp_unit_hashes(dict(schema_version=1,chapter='algebraic',unit_id='fixture:finite-compound',parent_tag='001M',node_kind='paragraph',source_commit=CATALOG['source_commit'],source_status='CURRENT',source_text=form+'\n',placeholders={},render=dict(prefix='',suffix='')))
   before=source_inventory(unit,ORIGINAL);after=source_inventory(unit,CATALOG)
   self.assertNotEqual(before.pop('catalog_hash'),after.pop('catalog_hash'))
   self.assertEqual(after,before)
   unit['chapter']=case['chapter'];unit['source_text']='<MATH_0001>\n';unit['placeholders']={'MATH_0001':'$\\text{'+form+'}$'};unit=stamp_unit_hashes(unit)
   self.assertFalse(any(o['concept']==case['concept'] for o in source_inventory(unit,CATALOG)['occurrences']))
 @unittest.skipUnless(os.environ.get('HARVEST_DIR'),'requires explicit locked read-only harvest')
 def test_complete_locked_git_evidence_and_only_witnessed_inventory_replacements(self):
  native=Containers(ROOT,Path(os.environ['HARVEST_DIR']));selected={}
  for case in FIXTURE['decisions']:
   for form,w in zip(case['forms'],case['independent_locked_source_witnesses']):
    key=json.dumps(w['selector'],sort_keys=True)
    if key not in selected:selected[key]=native.select(w['selector'])
    container=selected[key]
    self.assertEqual(container['location']['fragment_hash'],w['fragment_hash'])
    self.assertTrue(_matches(source_projection(container['inventory_unit'])[0],w['source_term']))
    unit=next(u for u in lower_container(container,native.policy) if u['unit_id']==w['unit_id'])
    self.assertEqual(unit['source_text_hash'],w['source_text_hash'])
    before=source_inventory(unit,ORIGINAL)['occurrences'];after=source_inventory(unit,CATALOG)['occurrences']
    self.assertTrue(any(o['concept']==case['concept'] for o in after))
    additions=[o for o in after if o not in before]
    removed=[o for o in before if o not in after]
    self.assertTrue(all(any(n['projection_start']<=o['projection_start']<o['projection_end']<=n['projection_end'] for n in additions) for o in removed))
  delta=[];old={e['id']:e for e in ORIGINAL['terms']}
  for e in CATALOG['terms']:
   added=[w for w in e['evidence'] if w not in old.get(e['id'],{}).get('evidence',[])]
   if added:delta.append({**e,'evidence':added})
  checks,errors=validate_catalog_evidence(ROOT,{'source_commit':CATALOG['source_commit'],'terms':delta},[],containers=native)
  self.assertEqual(errors,[]);self.assertEqual(len(checks),70)
if __name__=='__main__':unittest.main()
