"""Independent finite-frame tests; all target text is synthetic, never candidate data."""
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from stacks_zh import math_text_deformations as wave
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots, nodes, usage, validate_regions, validate_translation
from stacks_zh.records import RecordError, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import byte_hash, source_tex
from test_source_containers import fixture, selector

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT/'tests/fixtures/deformations-math-frames.json').read_text())
BASELINE = '11b8d45dfa1a9acd72ede2d34264c25d363f1ae8'
BEFORE = subprocess.check_output(['git','show',BASELINE+':config/macro-policy.yml'],cwd=ROOT,text=True)
FRAMES = tuple(dict.fromkeys(FIXTURE['natural_frames']+FIXTURE['notation_frames']))
PRIMARY_FINITE_FRAME = r"$\emptyset = \bigcap_{I' \subset I\text{ finite}} T_{I'}$"
PRIMARY_ROOT_FRAMES = tuple('$f\\text{'+literal+'}g$' for role,literal in sorted(wave.CONTEXTS[wave.USAGE])
                            if role=='root-phrase')
PROOF = '\\begin{proof}\n'+'\n'.join(FRAMES+(PRIMARY_FINITE_FRAME,)+PRIMARY_ROOT_FRAMES)+'\n\\end{proof}'


def add_entry(text, section, name, fields):
    entry='  '+name+':\n'+''.join('    '+k+': '+
        (v if k=='source_label' and section=='locked_math_text_notations' else json.dumps(v))
        +'\n' for k,v in fields.items())
    marker='\n'+section+':\n'
    return text.replace(marker,marker+entry,1) if marker in text else text+marker+entry


def trial_policy(tags=None):
    """Isolated source-only experiment; production macro-policy is unchanged."""
    baseline=Policy(BEFORE)
    text=BEFORE if tags is not None else BEFORE.split('\ntranslatable_math_text:')[0]
    if tags is None:
        text=re.sub(r'(?m)^(    source_label:) (.+)$',
            lambda m:m[1]+' '+('"test-lemma-one"' if m[2].startswith('"') else 'test-lemma-one'),text)
    registered=set()
    for w in FIXTURE['witnesses']:
        frame=w['complete_math_frame'];stream=nodes(frame)
        coord=w['inventory_coordinate'];kind=coord['semantic_path'].split('/')[0]
        if tags is None:
            label,kind='test-lemma-one','proof'
        else:
            tag=coord['owner_tag'] if kind in {'lemma','proof'} else coord['parent_tag']
            label=next(k for k,v in tags.items() if v==tag)
            kind=kind if kind in {'lemma','proof'} else 'section'
        witness=dict(source_label=label,witness_kind=kind,witness_ordinal=1)
        for index,node in enumerate(stream):
            command,literal=node.get('command'),node.get('value')
            if command!='text' or literal in wave.SYMBOLS or literal in registered:continue
            registered.add(literal)
            old=[(k,r) for k,r in baseline.math_text_rules.items()
                 if r['literal']==literal and r['command']==command]
            if old:
                # Keep the old primary; add only the witnessed finite fallback.
                key,rule=next(((k,r) for k,r in old if (r['usage'],literal) in wave.CONTEXTS[wave.USAGE]),old[0])
                if (rule['usage'],literal) not in wave.CONTEXTS[wave.USAGE]:
                    raise AssertionError('Undeclared inherited context: '+repr((rule['usage'],literal)))
                if tags is None:
                    text=add_entry(text,'translatable_math_text',key,
                        {**rule,**witness})
                needs_fallback=any(not any(usage(f,nodes(f),i,r['usage']) for _,r in old)
                    for f in FRAMES for i,n in enumerate(nodes(f))
                    if n.get('command')=='text' and n['value']==literal)
                if not needs_fallback:continue
                section='translatable_math_text_contexts'
                fields=dict(base_rule=key,usage=wave.USAGE,**witness)
            else:
                section='translatable_math_text'
                fields=dict(literal=literal,command='text',usage=wave.USAGE,**witness)
            text=add_entry(text,section,'source-only-natural-'+str(len(registered)),fields)
    for name in sorted(wave.OPERATORS):
        label='test-lemma-one' if tags is None else next(
            k for k,v in tags.items() if v==next(w['inventory_coordinate']['parent_tag']
                for w in FIXTURE['witnesses'] if any(n['value']==name for n in w['text_nodes'])))
        fields=dict(commands=['text'],usages=[wave.NOTATION_USAGE],source_label=label)
        if name in baseline.math_text_notations:
            fields=dict(base_notation=name,**fields)
            section='locked_math_text_contexts'
        else:section='locked_math_text_notations'
        text=add_entry(text,section,'source-only-'+name.lower() if name in baseline.math_text_notations else name,fields)
    return text


def synthetic_translation(unit):
    text=unit['source_text']
    for region in unit.get('math_text_regions',[]):
        for slot in region['slots']:
            left,right=('<'+p+'>' for p in slot['boundary_placeholders'])
            a=text.index(left)+len(left);b=text.index(right,a)
            text=text[:a]+'合成测试文字'+text[b:]
    return text


class DeformationsMathFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.root,cls.harvest,_=fixture(Path(cls.temp.name),proof=PROOF)
        (cls.root/'config/macro-policy.yml').write_text(trial_policy())
        cls.policy=Containers(cls.root,cls.harvest).policy

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_exact_independent_source_frame_inventory(self):
        self.assertEqual(byte_hash(BEFORE),FIXTURE['baseline_macro_hash'])
        self.assertTrue(FIXTURE['source_only']);self.assertFalse(FIXTURE['actual_model_data'])
        self.assertEqual(tuple(FIXTURE['natural_frames']),wave.NATURAL_FRAMES)
        self.assertEqual(tuple(FIXTURE['notation_frames']),wave.NOTATION_FRAMES)
        self.assertEqual((len(FRAMES),len(wave.NATURAL_FRAMES),len(wave.NOTATION_FRAMES)),(112,45,70))
        self.assertEqual(len(set(wave.NATURAL_FRAMES) & set(wave.NOTATION_FRAMES)),3)
        self.assertEqual(len(FIXTURE['excluded_reference_frames']),6)
        self.assertEqual(len(FIXTURE['excluded_reference_literals']),2)
        self.assertEqual(len(FIXTURE['excluded_macro_diagnostics']),4)
        self.assertEqual(len(FIXTURE['containers']),88)

    def test_plain_leaves_do_not_unlock_symbols(self):
        for f in FRAMES:
            with self.subTest(frame=f):
                expected=[n['value'] for n in nodes(f) if n.get('command')=='text' and n['value'] not in wave.SYMBOLS]
                slots=find_slots(f,self.policy.math_text_rules)
                self.assertEqual([s['value'] for s in slots],expected)
                self.assertFalse(Scanner(f,self.policy).protect(0,len(f))[2])
                self.assertFalse(any(s['value'] in wave.SYMBOLS for s in slots))

    def test_complete_synthetic_proof_schema_replay_and_math_skeleton(self):
        native=Containers(self.root,self.harvest)
        unit=lower_container(native.select(selector()),native.policy)[0]
        self.assertEqual(source_tex(unit),PROOF)
        self.assertEqual(validate_named_schema(unit,'unit.schema.json','source-only'),[])
        self.assertEqual(validate_regions(unit),[])
        self.assertEqual(validate_translation(unit,synthetic_translation(unit)),[])
        from stacks_zh.source_terms import source_projection
        projected,_=source_projection(unit)
        self.assertIn(' section of ',projected)
        self.assertIn(' there exists a hull',projected)
        self.assertNotIn('Res',projected)
        damaged=copy.deepcopy(unit);damaged['math_text_regions'][0]['source']+='x'
        self.assertTrue(validate_regions(stamp_unit_hashes(damaged)))

    def test_changed_math_font_gap_structure_or_unknown_text_is_not_granted_new_role(self):
        for f in FRAMES:
            stream=nodes(f)
            operand=next((n for n in stream if re.fullmatch('[A-Za-z]',n['token'])),None)
            variants=[f+'x','{'+f+'}',f.replace('\\text{','\\textbf{',1),
                      f.replace('$','$ ',1) if f.startswith('$') else f.replace('\n','\n ',1)]
            if operand:variants.append(f[:operand['start']]+'Q'+f[operand['end']:])
            for changed in variants:
                if changed==f or changed in FRAMES:continue
                with self.subTest(changed=changed):
                    try:
                        slots=find_slots(changed,self.policy.math_text_rules)
                        modified=nodes(changed)
                    except ValueError:
                        slots=[];modified=[]
                    self.assertFalse(any(s['usage']==wave.USAGE for s in slots))
                    self.assertFalse(any(wave.notation_context(changed,modified,i,n.get('value'),wave.NOTATION_USAGE)
                                         for i,n in enumerate(modified)))
            for n in stream:
                if n.get('command')!='text' or n['value'] in wave.SYMBOLS:continue
                changed=f[:n['parameter_start']]+'unknown source phrase'+f[n['parameter_end']:]
                self.assertFalse(any(s['value']=='unknown source phrase' for s in find_slots(changed,self.policy.math_text_rules)))
                self.assertTrue(Scanner(changed,self.policy).protect(0,len(changed))[2])

    def test_operator_policy_is_exact_and_old_roles_are_unchanged(self):
        baseline=Policy(BEFORE)
        for name in ('Mod','Inf'):
            self.assertEqual(self.policy.math_text_notations[name],
                             {**baseline.math_text_notations[name],'source_label':'test-lemma-one'})
        for bad in [trial_policy().replace('usages: ["deformations-symbol-frame"]','usages: ["applied"]',1),
                    trial_policy().replace('base_notation: "Inf"','base_notation: "Aut"',1),
                    trial_policy().replace('commands: ["text"]\n    usages: ["deformations-symbol-frame"]',
                                           'commands: ["textit"]\n    usages: ["deformations-symbol-frame"]',1)]:
            with self.assertRaises(RecordError):Policy(bad)
        for f in FIXTURE['excluded_reference_frames']:
            self.assertTrue(Scanner(f,self.policy).protect(0,len(f))[2])
        for f in [r'$\text{Res}(Q)$',r'$\text{Cof}$',r'$\text{CofSet}$']:
            self.assertTrue(Scanner(f,self.policy).protect(0,len(f))[2])

    def test_alg_category_suffix_has_no_translatable_leaf(self):
        from stacks_zh.source_terms import source_projection
        frames=(r'$S\text{-Alg}/R$',r'$\text{Mod}_R \to S\text{-Alg}/R$')
        for frame in frames:
            with self.subTest(frame=frame):
                self.assertEqual(find_slots(frame,self.policy.math_text_rules),[])
                text,protected,errors=Scanner(frame,self.policy).protect(0,len(frame))
                self.assertFalse(errors)
                self.assertEqual(len(protected),1)
                self.assertEqual(list(protected.values()),[frame])
                self.assertNotIn('-Alg',text)
        unit=lower_container(Containers(self.root,self.harvest).select(selector()),self.policy)[0]
        self.assertNotIn('-Alg',source_projection(unit)[0])
        self.assertIn(frames[0],source_tex(unit))
        for frame in frames:
            for changed in (frame.replace('S','T'),frame.replace('/R','/Q'),
                            frame.replace('text{','textit{'),frame.replace('-Alg','-ALG'),
                            frame.replace('-Alg','-Algebras'),frame.replace('/R',' /R')):
                self.assertTrue(Scanner(changed,self.policy).protect(0,len(changed))[2])
                self.assertFalse(any(wave.notation_context(changed,nodes(changed),i,n.get('value'),wave.NOTATION_USAGE)
                                     for i,n in enumerate(nodes(changed))))
        for name in ('-ALG','-Other'):
            with self.assertRaises(RecordError):
                Policy(trial_policy().replace('  -Alg:\n','  '+name+':\n',1))

    def test_locked_git_native_source_witnesses_and_full_container_trials(self):
        harvest=Path(os.environ.get('HARVEST_DIR',str(ROOT.parent/'stacks-project')))
        if not (harvest/'.git').exists():self.skipTest('locked harvest unavailable')
        native=Containers(ROOT,harvest)
        blobs={}
        for w in FIXTURE['witnesses']:
            chapter=w['chapter']
            if chapter not in blobs:
                blobs[chapter]=subprocess.check_output(['git','show',FIXTURE['source_commit']+':'+chapter+'.tex'],cwd=harvest)
            raw=blobs[chapter];self.assertEqual(byte_hash(raw),w['blob_hash'])
            span=w['frame_byte_span'];self.assertEqual(raw[span['start']:span['end']].decode(),w['complete_math_frame'])
            self.assertEqual(byte_hash(w['complete_math_frame']),w['frame_hash'])
            loc=w['inventory_coordinate']['location']
            self.assertEqual(raw[loc['byte_start']:loc['byte_end']].decode(),w['inventory_fragment'])
        trial=Containers(ROOT,harvest,policy_bytes=trial_policy(native.english.tags).encode())
        for name in ('Mod','Inf'):
            self.assertEqual(trial.policy.math_text_notations[name],native.policy.math_text_notations[name])
        for c in FIXTURE['containers']:
            with self.subTest(selector=c['selector']):
                with self.assertRaises(RecordError) as error:native.select(c['selector'])
                self.assertEqual(str(error.exception),c['baseline_selection_error'])
                if c.get('remaining_trial_error'):
                    with self.assertRaises(RecordError) as remaining:trial.select(c['selector'])
                    self.assertEqual(str(remaining.exception),c['remaining_trial_error'])
                else:
                    selected=trial.select(c['selector']);units=lower_container(selected,trial.policy)
                    self.assertEqual(selected['fragment'],c['trial_fragment'])
                    self.assertEqual(units,c['trial_units'])
                    self.assertTrue(all(not validate_regions(u) for u in units))
                    self.assertTrue(all(not validate_named_schema(u,'unit.schema.json','source-only') for u in units))
