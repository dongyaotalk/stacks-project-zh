"""Source-only finite policy regressions; synthetic fields are never model output."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import unittest

from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import nodes, validate_regions
from stacks_zh.source_containers import Containers, clean, lower_container
from stacks_zh.source_reextractions import source_tex
from stacks_zh.source_terms import load_catalog, source_inventory
from test_descent_policy_registration import entries
from test_descent_source_terms_policy import unit, candidate, words, FORMS, CONCEPT

ROOT = Path(__file__).resolve().parents[1]
BASE = '3630df1919a161fb292d44cb893ac94942368ba9'
FIXTURE = json.loads((ROOT / 'tests/fixtures/etale-cohomology59-source-policy.json').read_text())
BEFORE = subprocess.check_output(['git','show',BASE+':config/macro-policy.yml'],cwd=ROOT,text=True)
CURRENT = (ROOT / 'config/macro-policy.yml').read_text()


class EtaleCohomologySourcePolicyTests(unittest.TestCase):
    def test_exact_declared_entries_reconstruct_all_original_policy_bytes(self):
        self.assertEqual(hashlib.sha256(BEFORE.encode()).hexdigest(), FIXTURE['baseline_macro_hash'][7:])
        self.assertEqual(hashlib.sha256(CURRENT.encode()).hexdigest(), FIXTURE['proposed_macro_hash'][7:])
        restored = CURRENT
        sections = {'locked_math_text_notations','locked_math_text_contexts',
                    'translatable_math_text','translatable_math_text_components','translatable_math_text_contexts'}
        self.assertEqual(len(FIXTURE['new_rules']), 69)
        for section in sections:
            old, new = entries(BEFORE,section), entries(CURRENT,section)
            added = {w['policy_key'] for w in FIXTURE['new_rules'] if w['policy_section']==section}
            self.assertEqual(set(new)-set(old),added)
            for key in added:
                self.assertEqual(restored.count(new[key]),1)
                restored = restored.replace(new[key],'',1)
            for key in old:
                expected = old[key]
                if section=='locked_math_text_notations' and key=='Mat':
                    expected = expected.replace('["applied"]','["applied", "subscripted"]')
                    restored = restored.replace(new[key],old[key],1)
                self.assertEqual(new[key],expected,(section,key))
        self.assertEqual(restored,BEFORE)

    def test_named_operators_are_locked_not_translatable_prose(self):
        p=Policy(CURRENT)
        for name,role,source in [('Div','applied',r'$\text{Div}(X)$'),
                                ('Maps','subscripted',r'$\text{Maps}_{cont}(G,M)$')]:
            self.assertNotIn(name,{r['literal'] for r in p.math_text_rules.values()})
            scanner=Scanner(source,p);protected,placeholders,diagnostics=scanner.protect(0,len(source))
            self.assertFalse(diagnostics)
            self.assertEqual(protected,'<MATH_0001>')
            self.assertEqual(placeholders,{'MATH_0001':source})
            self.assertEqual(scanner.math_text_classifications[0]['usage'],role)
        self.assertFalse(Scanner(r'$\text{Mat}_n$',p).protect(0,len(r'$\text{Mat}_n$'))[2])
        for source in [r'$\text{Div}_n$',r'$\textit{Div}(X)$',r'$\text{Maps}(G,M)$']:
            self.assertTrue(Scanner(source,p).protect(0,len(source))[2])

    def test_ordinary_text_variants_do_not_gain_slots(self):
        p=Policy(CURRENT)
        for source in [r'$A\text{equal To}B$',r'$A\text{ is the colimit Of}B$',
                       r'$A\textbf{equal to}B$',r'$\text{Locally ringed topoi}$',
                       r'$A\text{Zariski locally constant map}B$']:
            self.assertTrue(Scanner(source,p).protect(0,len(source))[2],source)

    def test_module_chapter_scope_retains_original_witnesses_and_terms(self):
        c=load_catalog(ROOT)
        actual=next(x for x in c['terms'] if x['id']==CONCEPT)
        old=FIXTURE['module_concept_before']
        self.assertEqual(actual['chapters'],['descent','etale-cohomology'])
        self.assertEqual(actual['forms'],old['forms'])
        self.assertEqual(actual['evidence'][:2],old['evidence'])
        self.assertEqual(words(unit('A quasi-coherent module and quasi-coherent modules.','etale-cohomology')),FORMS)
        self.assertEqual(words(unit('A quasi-coherent module and quasi-coherent modules.','descent')),FORMS)
        self.assertEqual(words(unit('A coherent module and coherent modules.','etale-cohomology')),['coherent module','coherent modules'])
        self.assertEqual(words(unit('A quasi-coherent module.','other')),['coherent module'])

    def test_existing_current_inventory_changes_only_catalog_hash(self):
        before=json.loads(subprocess.check_output(['git','show',BASE+':config/source-terms.json'],cwd=ROOT))
        after=load_catalog(ROOT)
        count=0
        for path in sorted((ROOT/'translation-data/units').glob('*.jsonl')):
            for line in path.read_text().splitlines():
                u=json.loads(line);a=source_inventory(u,before);b=source_inventory(u,after)
                a.pop('catalog_hash');b.pop('catalog_hash');self.assertEqual(a,b,u['unit_id']);count+=1
        self.assertGreater(count,3000)


@unittest.skipUnless(os.environ.get('HARVEST_DIR'),'requires explicit read-only locked harvest')
class LockedEtaleCohomologyPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=Containers(ROOT,Path(os.environ['HARVEST_DIR']))
        cls.raw,cls.rows,cls.diagnostics=cls.native.document('etale-cohomology')

    def test_locked_math_parameters_and_real_policy_witnesses(self):
        self.assertEqual(self.native.english.commit,FIXTURE['source_commit'])
        self.assertFalse(self.diagnostics)
        for w in FIXTURE['new_rules']:
            e=w['entry'];loc=e['old']['location'];literal=e['old']['source']
            self.assertEqual(self.raw[loc['byte_start']:loc['byte_end']].decode(),literal)
            m=e['matched_math'];self.assertEqual(nodes(m['math'])[m['math_node_index']],m['node'])
            self.assertIn(m['math'].encode(),self.raw)
            if w['policy_section'].startswith('translatable_math_text'):
                self.assertIn(w['policy_key'],self.native.policy.math_text_rules)
                self.assertIn(w['policy_key'],self.native.policy.math_text_witnesses)

    def test_module_complete_containers_roundtrip_and_full_compounds(self):
        catalog=load_catalog(ROOT)
        for w in FIXTURE['module_witnesses']:
            selected=self.native.select(w['evidence']['selector'])
            self.assertEqual(clean(selected),w['selected'])
            units=lower_container(selected,self.native.policy)
            self.assertEqual([clean(u) for u in units],[w['unit']])
            self.assertEqual(''.join(source_tex(u) for u in units),selected['fragment'])
            self.assertIn(w['evidence']['source_term'],[x['source_term'] for x in source_inventory(units[0],catalog)['occurrences']])
            self.assertEqual(validate_regions(units[0]),[])


if __name__=='__main__':
    unittest.main()
