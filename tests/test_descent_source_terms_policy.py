"""Synthetic exact source-term coverage; no model output or terminology approval."""
import copy
import json
import subprocess
import unittest
from pathlib import Path

from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.source_terms import load_catalog, source_inventory, source_tex_hash, validate_source_terms
from stacks_zh.source_reextractions import source_tex

ROOT = Path(__file__).resolve().parents[1]
CATALOG = load_catalog(ROOT)
FORMS = ['quasi-coherent module', 'quasi-coherent modules']
CONCEPT = 'source-phrase-quasi-coherent-module'
REGISTERED_CATALOG = json.loads(subprocess.check_output(
    ['git', 'show', '4313e71e494c0da379b163b8eaba2fa1fce225da:config/source-terms.json'], cwd=ROOT))


def unit(text, chapter='descent'):
    return stamp_unit_hashes(dict(schema_version=1, unit_id='fixture:descent-module',
        chapter=chapter, parent_tag='ABCD', node_kind='paragraph',
        source_commit=CATALOG['source_commit'], source_status='CURRENT',
        source_text=text, placeholders={}, render=dict(prefix='', suffix='\n')))


def candidate(forms):
    return dict(translation='，'.join('拟凝聚模（'+form+'）' for form in forms),
        term_occurrences=[dict(source_term=form, target_term='拟凝聚模') for form in forms],
        unknown_terms=[dict(source_term=form, target_term='拟凝聚模',
            context='Synthetic diagnostic; Chinese terminology remains pending.') for form in forms],
        term_status='DECISION_REQUIRED')


def words(row, catalog=CATALOG):
    return [item['source_term'] for item in source_inventory(row, catalog)['occurrences']]


class DescentSourceTermPolicyTests(unittest.TestCase):
    def test_exact_singular_plural_have_separate_locked_witnesses_and_original_descent_witnesses(self):
        entries=[item for item in CATALOG['terms'] if item['id']==CONCEPT]
        self.assertEqual(len(entries), 1)
        entry=entries[0]
        self.assertEqual(entry['forms'], FORMS)
        registered, = [item for item in REGISTERED_CATALOG['terms'] if item['id']==CONCEPT]
        self.assertEqual(registered['chapters'], ['descent', 'etale-cohomology'])
        self.assertTrue(set(registered['chapters']) <= set(entry['chapters']))
        self.assertTrue(all(e in entry['evidence'] for e in registered['evidence']))
        self.assertEqual([item['source_term'] for item in entry['evidence'][:2]], FORMS)
        for witness, tag, parent in zip(entry['evidence'][:2], ['0CDR','0GNB'], ['0CDQ','0GN9']):
            self.assertEqual(witness['kind'], 'locked-source-container')
            self.assertEqual(witness['source_commit'], CATALOG['source_commit'])
            self.assertEqual(witness['chapter'], 'descent')
            self.assertEqual(witness['selector']['owner_tag'], tag)
            self.assertEqual(witness['selector']['parent_tag'], parent)
            self.assertEqual(witness['selector']['kind'], 'lemma')
            self.assertEqual(witness['selector']['ordinal'], 1)

    def test_whole_compounds_replace_inner_coherent_forms_and_complete_pending_display_passes(self):
        row=unit('A quasi-coherent module and quasi-coherent modules.')
        output=candidate(FORMS)
        before=copy.deepcopy((row, output, CATALOG))
        original=source_tex(row)
        self.assertEqual(words(row), FORMS)
        self.assertEqual(validate_source_terms(row, output, CATALOG), [])
        self.assertEqual((row, output, CATALOG), before)
        self.assertEqual(source_tex(row), original)

    def test_omitting_either_exact_inflection_fails(self):
        row=unit('A quasi-coherent module and quasi-coherent modules.')
        for missing in FORMS:
            with self.subTest(missing=missing):
                errors=validate_source_terms(row, candidate([f for f in FORMS if f!=missing]), CATALOG)
                self.assertIn('fixture:descent-module: missing source-side term coverage (1): '+missing, errors)

    def test_case_and_plural_cannot_be_rewritten_or_reused(self):
        for text, declaration in [('A quasi-coherent module.', 'Quasi-coherent module'),
                                  ('Two quasi-coherent modules.', 'quasi-coherent module')]:
            with self.subTest(text=text):
                self.assertTrue(validate_source_terms(unit(text), candidate([declaration]), CATALOG))
        row=unit('A quasi-coherent module and another quasi-coherent module.')
        self.assertEqual(words(row), [FORMS[0], FORMS[0]])
        self.assertTrue(validate_source_terms(row, candidate([FORMS[0]]), CATALOG))
        self.assertEqual(validate_source_terms(row, candidate([FORMS[0], FORMS[0]]), CATALOG), [])

    def test_genuine_coherent_module_terms_remain_required(self):
        row=unit('A coherent module, coherent modules, a quasi-coherent module and quasi-coherent modules.')
        self.assertEqual(words(row), ['coherent module', 'coherent modules', *FORMS])
        errors=validate_source_terms(row, candidate(FORMS), CATALOG)
        self.assertTrue(any('coverage (1): coherent module' in error for error in errors))
        self.assertTrue(any('coverage (1): coherent modules' in error for error in errors))

    def test_other_chapters_keep_prior_inner_requirements(self):
        before=copy.deepcopy(CATALOG)
        before['terms']=[entry for entry in before['terms'] if entry['id']!=CONCEPT]
        for chapter in ['categories', 'sites', 'topologies', 'obsolete']:
            with self.subTest(chapter=chapter):
                row=unit('A quasi-coherent module and quasi-coherent modules.', chapter)
                self.assertEqual(words(row), words(row, before))
                self.assertEqual(words(row), ['coherent module', 'coherent modules'])

    def test_registration_is_necessary_and_does_not_approve_chinese(self):
        before=copy.deepcopy(CATALOG)
        before['terms']=[entry for entry in before['terms'] if entry['id']!=CONCEPT]
        row=unit('A quasi-coherent module and quasi-coherent modules.')
        self.assertTrue(validate_source_terms(row, candidate(FORMS), before))
        output=candidate(FORMS);output['unknown_terms']=[];output['term_status']='CLEAR'
        self.assertTrue(any('unapproved term' in error for error in validate_source_terms(row, output, CATALOG)))

    def test_exact_ordinary_occurrences_are_bound_and_do_not_exempt_other_source(self):
        declared=[x for x in CATALOG['nonmathematical_occurrences'] if x['chapter']=='descent']
        self.assertEqual({x['unit_id'] for x in declared}, {'tag:02W3:proof','tag:02YJ:prose-0001'})
        expected={'proper':'sha256:544ef527289a5c8d9547e9f80e4a7b84f89a1157c3e314c98d4c2967b904a552',
                  'large':'sha256:7e9c7e027cad77e48a8efc32be4af7aa44eb419d27831100d3e65f8747b328c8'}
        for entry in declared:
            self.assertEqual(entry['source_tex_hash'],expected[entry['source_term']])
            self.assertEqual(entry['occurrence_index'],0)
        for term,text,expected_words in [
                ('proper','Before the proof proper, consider a proper morphism.', ['proper','proper morphism']),
                ('proper','Before the proof proper, consider a morphism that is proper.', ['proper','morphism','proper']),
                ('large','There are a large number of properties of a large category.', ['large','large','category'])]:
            row=unit(text)
            original=copy.deepcopy(CATALOG)
            original['nonmathematical_occurrences']=[x for x in original['nonmathematical_occurrences'] if x['chapter']!='descent']
            prior_words=words(row,original)
            self.assertEqual(prior_words,expected_words)
            scoped=copy.deepcopy(original)
            scoped['nonmathematical_occurrences'].append(dict(chapter='descent',unit_id=row['unit_id'],source_term=term,
                source_tex_hash=source_tex_hash(row),
                occurrence_index=0,reason='Synthetic exact ordinary occurrence; second mathematical occurrence remains.'))
            after=words(row,scoped)
            self.assertEqual(after,expected_words[1:])
            self.assertEqual(source_tex(row),text+'\n')
            changed=unit(text+' Additional source.')
            self.assertEqual(words(changed,scoped),expected_words)
            other=unit(text,'categories')
            self.assertEqual(words(other,scoped),expected_words)
            bad=copy.deepcopy(scoped);bad['nonmathematical_occurrences'][-1]['occurrence_index']=2
            with self.assertRaises(RecordError):
                words(row,bad)


if __name__ == '__main__':
    unittest.main()
