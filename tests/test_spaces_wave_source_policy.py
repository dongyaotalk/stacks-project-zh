"""Locked-source policy regressions, independent of candidate/model metadata."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import unittest

from stacks_zh.extraction import Policy, Scanner, resolve_natural_math_witnesses
from stacks_zh.math_text import find_slots, nodes, validate_regions
from stacks_zh.math_text_spaces import FRAMES, CATEGORY_FRAMES
from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_reextractions import source_tex
from stacks_zh.source_terms import load_catalog, source_inventory, source_tex_hash

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT/'tests/fixtures/spaces-wave-source-policy.json').read_text())
CATALOG = load_catalog(ROOT)
MACRO = (ROOT/'config/macro-policy.yml').read_text()


def words(unit, catalog=CATALOG):
    return [o['source_term'] for o in source_inventory(unit, catalog)['occurrences']]


class SpacesWaveSourceTermsPolicyTests(unittest.TestCase):
    def test_original_catalog_snapshot_and_exact_registered_fields(self):
        raw = (json.dumps(FIXTURE['catalog_before'], ensure_ascii=False, indent=2)+'\n').encode()
        self.assertEqual('sha256:'+hashlib.sha256(raw).hexdigest(), FIXTURE['catalog_before_hash'])
        self.assertEqual(FIXTURE['source_commit'], CATALOG['source_commit'])
        self.assertFalse(FIXTURE['actual_model_data'])
        self.assertEqual([t['forms'] for t in FIXTURE['catalog_added_terms']],
                         [['locally finite type'], ['locally finite presentation'], ['quasi-coherent']])
        for entry in FIXTURE['catalog_added_terms']:
            self.assertEqual(entry['chapters'], ['spaces-descent'])
            current, = [t for t in CATALOG['terms'] if t['id']==entry['id']]
            self.assertEqual(current, entry)
            self.assertEqual(set(entry), {'id', 'forms', 'chapters', 'evidence'})
        compound, = [t for t in CATALOG['terms'] if t['id']=='source-phrase-quasi-coherent-module']
        original = FIXTURE['compound_before']
        registered = FIXTURE['compound_after']
        self.assertEqual(registered['forms'], original['forms'])
        self.assertEqual(registered['chapters'], original['chapters']+['spaces-descent'])
        self.assertEqual(registered['evidence'][:-2], original['evidence'])
        self.assertTrue(set(registered['chapters']) <= set(compound['chapters']))
        self.assertTrue(all(e in compound['evidence'] for e in registered['evidence']))
        for entry in FIXTURE['added_ordinary']:
            self.assertEqual(CATALOG['nonmathematical_occurrences'].count(entry), 1)

    def test_full_property_names_replace_only_the_two_shorter_occurrences(self):
        unit = FIXTURE['term_source_witnesses']['spaces-descent:tag:06NR:statement']['canonical_unit']
        old = words(unit, FIXTURE['catalog_before'])
        self.assertEqual(old.count('locally finite'), 2)
        expected = old[:]
        position = expected.index('locally finite')
        expected[position:position+2] = ['locally finite type', 'locally finite presentation']
        self.assertEqual(words(unit), expected)
        other = copy.deepcopy(unit)
        other['chapter'] = 'descent'
        self.assertEqual(words(other), old)

    def test_complete_quasi_coherent_forms_and_standalone_property_are_distinct(self):
        unit = FIXTURE['term_source_witnesses']['spaces-descent:tag:0H04:proof']['canonical_unit']
        terms = words(unit)
        self.assertEqual(terms.count('quasi-coherent module'), 2)
        self.assertEqual(terms.count('quasi-coherent modules'), 1)
        self.assertEqual(terms.count('quasi-coherent'), 2)
        self.assertNotIn('coherent module', terms)
        self.assertNotIn('coherent modules', terms)
        self.assertIn('modules', terms)
        self.assertIn('tensor product', terms)
        other = copy.deepcopy(unit)
        other['chapter'] = 'categories'
        self.assertEqual(words(other), words(other, FIXTURE['catalog_before']))

    def test_only_four_exact_ordinary_occurrences_are_excluded(self):
        for entry in FIXTURE['added_ordinary']:
            unit = FIXTURE['term_source_witnesses'][entry['chapter']+':'+entry['unit_id']]['canonical_unit']
            before_ordinary = copy.deepcopy(CATALOG)
            before_ordinary['nonmathematical_occurrences'].remove(entry)
            old = words(unit, before_ordinary)
            expected = old[:]
            expected.remove(entry['source_term'])
            self.assertEqual(words(unit), expected)
            self.assertEqual(source_tex_hash(unit), entry['source_tex_hash'])
            if entry['source_term'] == 'point':
                self.assertEqual(words(unit).count('point'), 1)
                self.assertIn('At this point', source_tex(unit))
            elif entry['chapter'] == 'spaces-topologies':
                self.assertIn('then set <MATH_0006>', unit['source_text'])
            else:
                self.assertIn('Namely, for <MATH_0012> in <MATH_0013>, set <MATH_0014>', unit['source_text'])
            for field, value in [('chapter', 'categories'), ('unit_id', unit['unit_id']+'-other'),
                                 ('source_text', unit['source_text']+' Changed source.')]:
                changed = copy.deepcopy(unit)
                changed[field] = value
                changed = stamp_unit_hashes(changed)
                self.assertIn(entry['source_term'], words(changed))
        unit = stamp_unit_hashes(dict(schema_version=1, unit_id='synthetic:set-noun',
            chapter='spaces-topologies', parent_tag='ABCD', node_kind='paragraph',
            source_status='CURRENT', source_commit=CATALOG['source_commit'],
            source_text='The set of sections is finite.', placeholders={}, render=dict(prefix='', suffix='\n')))
        self.assertIn('set', words(unit))

    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit locked read-only harvest')
    def test_each_complete_original_source_matches_locked_git(self):
        from stacks_zh.source_containers import Containers, clean, lower_container
        native = Containers(ROOT, Path(os.environ['HARVEST_DIR']))
        self.assertEqual(native.english.commit, FIXTURE['source_commit'])
        for item in FIXTURE['term_source_witnesses'].values():
            selected = native.select(item['selector'])
            self.assertEqual(selected['fragment'], item['source_tex'])
            self.assertEqual(selected['location'], item['selected']['location'])
            self.assertEqual(selected['blob_oid'], item['selected']['blob_oid'])
            units = [clean(u) for u in lower_container(selected, native.policy)]
            unit, = [u for u in units if u['unit_id']==item['canonical_unit']['unit_id']]
            self.assertEqual(source_tex(unit), item['source_tex'])
            self.assertEqual(source_tex_hash(unit), item['source_tex_hash'])


class SpacesWaveMathPolicyTests(unittest.TestCase):
    def test_exact_registration_snapshot_reconstructs_original_git_bytes(self):
        from test_descent_policy_registration import entries
        from test_etale_policy_registration import fields
        before, after = FIXTURE['macro_before'], FIXTURE['macro_after']
        self.assertEqual(before, subprocess.check_output(
            ['git', 'show', FIXTURE['accepted_tool_main']+':config/macro-policy.yml'],
            cwd=ROOT, text=True))
        self.assertEqual('sha256:'+hashlib.sha256(before.encode()).hexdigest(),
                         FIXTURE['macro_before_hash'])
        self.assertEqual('sha256:'+hashlib.sha256(after.encode()).hexdigest(),
                         FIXTURE['macro_after_hash'])
        self.assertEqual([len(FIXTURE['macro_added'][s]) for s in
            ['locked_math_text_notations','translatable_math_text','translatable_math_text_contexts']],
            [1,13,12])
        restored = after
        for section, declared in FIXTURE['macro_added'].items():
            old, registered, current = [entries(t,section) for t in (before,after,MACRO)]
            self.assertEqual(set(registered)-set(old), set(declared))
            for key, rule in declared.items():
                self.assertEqual(fields(registered[key]), rule)
                self.assertEqual(current[key], registered[key])
                self.assertEqual(restored.count(registered[key]),1)
                restored=restored.replace(registered[key],'',1)
            for key in old:
                self.assertEqual(registered[key],old[key],(section,key))
        self.assertEqual(restored,before)

    def test_registered_frames_expose_all_natural_leaves_and_lock_category_formulas(self):
        policy = Policy(MACRO)
        for frame in FRAMES:
            self.assertEqual([s['value'] for s in find_slots(frame,policy.math_text_rules)],
                             [n['value'] for n in nodes(frame) if n.get('command')=='text'])
        for frame in CATEGORY_FRAMES:
            self.assertEqual(Scanner(frame,policy).protect(0,len(frame)),
                             ('<MATH_0001>', {'MATH_0001':frame}, []))
        self.assertFalse('Spaces' in {r['literal'] for r in policy.math_text_rules.values()})

    def test_original_fonts_literals_and_complete_frame_variants_remain_closed(self):
        policy=Policy(MACRO)
        for frame in FRAMES:
            first=next(n for n in nodes(frame) if n.get('command')=='text')
            changed=frame[:first['parameter_start']]+'unknown prose'+frame[first['parameter_end']:]
            self.assertTrue(Scanner(changed,policy).protect(0,len(changed))[2])
            # Old generic roles may remain valid in a changed frame. The newly
            # registered finite role must never grant a variant permission.
            for variant in [frame.replace('\\text{','\\textit{',1),
                            frame.replace('\n','\n ',1),frame+'x']:
                slots=find_slots(variant,policy.math_text_rules)
                self.assertFalse(any(s['usage']=='spaces-source-frames' for s in slots),variant)
        for frame in CATEGORY_FRAMES:
            for variant in [frame.replace('Spaces','spaces'),frame.replace('textit','text'),
                            frame.replace('Spaces',' Spaces')]:
                self.assertTrue(Scanner(variant,policy).protect(0,len(variant))[2],variant)
        for variant in [r'$\textit{Spaces}$',r'$\textit{Spaces}/Z$',r'$A+\textit{Spaces}$']:
            self.assertTrue(Scanner(variant,policy).protect(0,len(variant))[2])

    @unittest.skipUnless(os.environ.get('HARVEST_DIR'), 'requires explicit locked read-only harvest')
    def test_all_32_full_original_containers_are_ready_and_roundtrip_without_source_changes(self):
        from stacks_zh.source_containers import Containers, clean, lower_container
        harvest=Path(os.environ['HARVEST_DIR'])
        native=Containers(ROOT,harvest)
        before=Containers(ROOT,harvest,policy_bytes=FIXTURE['macro_before'].encode())
        self.assertEqual(len(FIXTURE['math_source_preparations']),32)
        counts={}
        for item in FIXTURE['math_source_preparations']:
            selected=native.select(item['selector'])
            self.assertEqual(clean(selected),clean(item['selected']))
            units=[clean(u) for u in lower_container(selected,native.policy)]
            self.assertEqual(units,item['units'])
            self.assertEqual(''.join(source_tex(u) for u in units),selected['fragment'])
            for unit in units:
                self.assertEqual(validate_named_schema(unit,'unit.schema.json','source-policy'),[])
                self.assertEqual(validate_regions(unit),[])
            chapter=item['selector']['file'][:-4]
            counts[chapter]=counts.get(chapter,0)+1
            if item['selector']['owner_tag'] != '0D3C':
                with self.assertRaises(RecordError):before.select(item['selector'])
        self.assertEqual(counts,{'spaces':4,'spaces-topologies':24,'spaces-descent':4})
        for section in ('translatable_math_text','translatable_math_text_contexts'):
            for name, rule in FIXTURE['macro_added'][section].items():
                self.assertIn(name,native.policy.math_text_witnesses)
                witness=native.policy.math_text_witnesses[name]
                self.assertEqual(witness['owner_label'],rule['source_label'])
                self.assertTrue(witness['matches'])
        self.assertEqual(native.policy.math_text_witnesses['spaces-wave-f05a8b353824']['owner_tag'],'02Z0')
        broken=Policy(MACRO)
        key='spaces-wave-f05a8b353824'
        broken.math_text_rules={key:copy.deepcopy(broken.math_text_rules[key])}
        broken.math_text_rules[key]['source_label']='spaces-section-definition'
        with self.assertRaises(RecordError):resolve_natural_math_witnesses(broken,native.english)


if __name__ == '__main__':
    unittest.main()
