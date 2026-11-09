"""Exact source-only project-name classification; no generated translation."""
import copy
import hashlib
import json
import subprocess
import unittest
from pathlib import Path
from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.source_reextractions import source_tex
from stacks_zh.source_terms import load_catalog, source_inventory, source_tex_hash, validate_source_terms
ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(ROOT)
# Immutable accepted four-classification catalog, not the moving full catalog.
REGISTERED_COMMIT = '036c698422f981167cef3285c881546cf40b21c3'
REGISTERED = json.loads(subprocess.check_output(
    ['git', 'show', REGISTERED_COMMIT + ':config/source-terms.json'], cwd=ROOT))
EVIDENCE = json.loads((ROOT/'docs/evidence/etale41-project-name-20261105.json').read_text())
ENTRY = EVIDENCE['entry']
DECLARATIONS = json.loads((ROOT/'docs/evidence/etale41-declaration-source-policy-20261105.json').read_text())
NEW_ENTRIES = [ENTRY, *DECLARATIONS['entries']]

def words(unit, catalog):
    return [item['source_term'] for item in source_inventory(unit, catalog)['occurrences']]

class EtaleProjectNamePolicyTests(unittest.TestCase):
    def test_only_four_exact_classifications_were_added(self):
        registered_raw=(json.dumps(REGISTERED,ensure_ascii=False,indent=2)+'\n').encode()
        self.assertEqual('sha256:'+hashlib.sha256(registered_raw).hexdigest(),
                         DECLARATIONS['catalog_four_classifications_hash'])
        before=copy.deepcopy(REGISTERED)
        for entry in NEW_ENTRIES:
            self.assertEqual(before['nonmathematical_occurrences'].count(entry),1)
            before['nonmathematical_occurrences'].remove(entry)
        raw=(json.dumps(before,ensure_ascii=False,indent=2)+'\n').encode()
        self.assertEqual('sha256:'+hashlib.sha256(raw).hexdigest(),EVIDENCE['catalog_before_sha256'])
        self.assertEqual((ENTRY['chapter'],ENTRY['unit_id'],ENTRY['source_term'],ENTRY['occurrence_index']),
                         ('etale','tag:024K:prose-0001','Stacks',0))
        self.assertEqual(ENTRY['source_tex_hash'],'sha256:52b67923c9f9767319e7c54a945167665032cd1ce58cf13b1eef79d6f3b89b63')

    def test_current_catalog_retains_each_exact_registered_classification(self):
        for entry in NEW_ENTRIES:
            with self.subTest(unit=entry['unit_id'],term=entry['source_term']):
                self.assertEqual(CATALOG['nonmathematical_occurrences'].count(entry),1)

    def test_complete_real_canonical_source_is_the_witness(self):
        unit=EVIDENCE['canonical_unit']
        self.assertEqual(source_tex(unit),EVIDENCE['source_tex'])
        self.assertEqual(source_tex_hash(unit),ENTRY['source_tex_hash'])
        self.assertEqual(EVIDENCE['source_commit'],CATALOG['source_commit'])
        self.assertEqual(EVIDENCE['selector'],dict(file='etale.tex',owner_tag='024K',parent_tag='024K',
            owner_label='etale-section-introduction',kind='prose_block',ordinal=1))
        self.assertIn('chapters of the Stacks project',source_tex(unit))
        witness,=EVIDENCE['independent_unadopted_source_evidence']
        self.assertEqual((witness['status'],witness['path']),('PASS','locked-source-container'))

    def test_only_the_project_name_requirement_is_removed(self):
        unit=EVIDENCE['canonical_unit'];before=copy.deepcopy(CATALOG)
        before['nonmathematical_occurrences'].remove(ENTRY)
        old=words(unit,before)
        self.assertEqual(old.count('Stacks'),1)
        self.assertEqual(words(unit,CATALOG),[word for word in old if word!='Stacks'])
        output=dict(translation='Synthetic source-only diagnostic.',term_occurrences=[],unknown_terms=[],term_status='CLEAR')
        self.assertTrue(any('coverage (1): Stacks' in error for error in validate_source_terms(unit,output,before)))
        errors=validate_source_terms(unit,output,CATALOG)
        self.assertFalse(any('coverage (1): Stacks' in error for error in errors))
        self.assertTrue(any('coverage' in error for error in errors))

    def test_changed_chapter_unit_source_hash_or_index_does_not_gain_exemption(self):
        original=EVIDENCE['canonical_unit']
        for field,value in [('chapter','categories'),('unit_id','tag:024K:prose-0002'),
                            ('source_text',original['source_text']+' More source.')]:
            unit=copy.deepcopy(original);unit[field]=value;unit=stamp_unit_hashes(unit)
            with self.subTest(field=field):self.assertIn('Stacks',words(unit,CATALOG))
        bad=copy.deepcopy(CATALOG);next(e for e in bad['nonmathematical_occurrences'] if e==ENTRY)['occurrence_index']=1
        with self.assertRaises(RecordError):words(original,bad)

    def test_later_mathematical_stack_occurrences_remain_required_and_unapproved(self):
        unit=stamp_unit_hashes(dict(schema_version=1,unit_id='synthetic:stack-precision',chapter='etale',
            parent_tag='ABCD',node_kind='paragraph',source_status='CURRENT',source_commit=CATALOG['source_commit'],
            source_text='The Stacks project studies a stack and stacks.',placeholders={},render=dict(prefix='',suffix='\n')))
        scoped=copy.deepcopy(CATALOG)
        scoped['nonmathematical_occurrences'].append(dict(ENTRY,unit_id=unit['unit_id'],source_tex_hash=source_tex_hash(unit),
            reason='Explicit synthetic occurrence precision fixture.'))
        self.assertEqual(words(unit,scoped),['stack','stacks'])
        output=dict(translation='合成栈（stack）与栈（stacks）。',term_occurrences=[dict(source_term='stack',target_term='栈'),
            dict(source_term='stacks',target_term='栈')],unknown_terms=[],term_status='CLEAR')
        self.assertTrue(any('unapproved term' in error for error in validate_source_terms(unit,output,scoped)))

    def test_grouped_alternative_preserves_both_real_mathematical_requirements(self):
        row=DECLARATIONS['rows'][0];unit=row['canonical_unit'];entry=row['entry']
        before=copy.deepcopy(CATALOG);before['nonmathematical_occurrences'].remove(entry)
        old,new=words(unit,before),words(unit,CATALOG)
        self.assertIn('flat (resp. faithfully flat',old)
        self.assertNotIn('flat (resp. faithfully flat',new)
        expected=[]
        for term in old:expected.extend(['flat','faithfully flat'] if term==entry['source_term'] else [term])
        self.assertEqual(new,expected)
        self.assertEqual(new.count('flat'),2);self.assertEqual(new.count('faithfully flat'),2)
        self.assertEqual(source_tex_hash(unit),entry['source_tex_hash'])
        self.assertEqual(source_tex(unit),row['source_tex'])

    def test_only_standalone_at_is_exempt_and_complete_flat_at_remains_required(self):
        row=DECLARATIONS['rows'][1];unit=row['canonical_unit'];entry=row['entry']
        before=copy.deepcopy(CATALOG);before['nonmathematical_occurrences'].remove(entry)
        old,new=words(unit,before),words(unit,CATALOG)
        self.assertEqual(new,[term for term in old if term!='at'])
        self.assertEqual(new.count('flat at'),2)
        bad=copy.deepcopy(CATALOG)
        next(e for e in bad['nonmathematical_occurrences'] if e==entry)['occurrence_index']=1
        self.assertIn('at',words(unit,bad))
        self.assertEqual(source_tex_hash(unit),entry['source_tex_hash'])
        self.assertEqual(source_tex(unit),row['source_tex'])

    def test_declaration_exceptions_are_bound_to_original_coordinates_and_bytes(self):
        for row in DECLARATIONS['rows']:
            original=row['canonical_unit'];entry=row['entry']
            for field,value in [('chapter','categories'),('unit_id',original['unit_id']+'-other'),
                                ('source_text',original['source_text']+' More source.')]:
                unit=copy.deepcopy(original);unit[field]=value;unit=stamp_unit_hashes(unit)
                with self.subTest(unit=original['unit_id'],field=field):self.assertIn(entry['source_term'],words(unit,CATALOG))
        witnesses=DECLARATIONS['all_three_unadopted_source_witnesses']
        self.assertEqual(len(witnesses),3)
        self.assertTrue(all(w['status']=='PASS' and w['path']=='locked-source-container' for w in witnesses))

    def test_parenthetical_assignment_set_is_not_a_mathematical_set(self):
        row=DECLARATIONS['rows'][2];unit=row['canonical_unit'];entry=row['entry']
        before=copy.deepcopy(CATALOG);before['nonmathematical_occurrences'].remove(entry)
        old,new=words(unit,before),words(unit,CATALOG)
        self.assertEqual(old.count('Set'),1)
        self.assertEqual(new,[term for term in old if term!='Set'])
        self.assertEqual(source_tex_hash(unit),entry['source_tex_hash'])
        self.assertEqual(source_tex(unit),row['source_tex'])
        self.assertIn('.)\nSet <MATH_0001>.',unit['source_text'])
        self.assertTrue(any('coverage (1): Set' in error for error in row['observed_source_term_errors']))
        self.assertFalse(any('coverage (1): Set' in error for error in row['proposed_source_term_errors']))
        witnesses=DECLARATIONS['all_four_unadopted_source_witnesses']
        self.assertEqual(len(witnesses),4)
        self.assertTrue(all(w['status']=='PASS' and w['path']=='locked-source-container' for w in witnesses))
        noun=stamp_unit_hashes(dict(schema_version=1,unit_id='synthetic:set-noun',chapter='etale',
            parent_tag='ABCD',node_kind='paragraph',source_status='CURRENT',source_commit=CATALOG['source_commit'],
            source_text='The set of sections is finite.',placeholders={},render=dict(prefix='',suffix='\n')))
        self.assertIn('set',words(noun,CATALOG))

if __name__=='__main__':unittest.main()
