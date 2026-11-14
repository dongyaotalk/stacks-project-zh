"""Independent locked-source and synthetic Git tests; no actual model data."""
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from stacks_zh import math_text_groupoids as wave
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots, nodes, validate_regions, validate_translation
from stacks_zh.records import RecordError, load_jsonl, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import byte_hash, source_tex
from test_source_containers import fixture, git, selector

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT/'tests/fixtures/groupoids-wave-math-frames.json').read_text())
BASELINE_COMMIT = '3d26f0ba0a2c87d681f40811fb405ffdc9cbd23b'
BEFORE = subprocess.check_output(
    ['git', 'show', BASELINE_COMMIT+':config/macro-policy.yml'], cwd=ROOT, text=True)
FRAMES = tuple(FIXTURE['natural_frames'] + FIXTURE['italic_frames']
               + FIXTURE['spaces_frames'] + FIXTURE['cqc_frames'])
PROOF = '\\begin{proof}\n'+'\n'.join(FRAMES)+'\n\\end{proof}'


def synthetic_policy():
    text = BEFORE.split('\ntranslatable_math_text:')[0]
    text = re.sub(r'(?ms)^locked_math_text_contexts:\n.*?(?=^[A-Za-z_][A-Za-z0-9_-]*:|\Z)', '', text)
    text = re.sub(r'(?m)^(    source_label:) .+$', r'\1 test-lemma-one', text)
    text = text.replace('locked_math_text_notations:\n',
        'locked_math_text_notations:\n  CQC:\n    commands: ["textit"]\n'
        '    usages: ["groupoids-cqc-category"]\n    source_label: test-lemma-one\n', 1)
    text += '\ntranslatable_math_text:\n'
    literals = dict.fromkeys(n['value'] for f in FIXTURE['natural_frames']
                             for n in nodes(f) if n.get('command') == 'text')
    for i, literal in enumerate(literals):
        text += f'  source-only-{i}:\n'
        role = ('root-phrase' if literal == ' such that '
                else 'numeric-isomorphism-suffix' if literal == '-isomorphism'
                else 'matrix-numeric-category-prefix' if literal in
                     {'-category of algebraic','-category of pairs '} else wave.USAGE)
        rule = dict(literal=literal, command='text', usage=role,
                    source_label='test-lemma-one', witness_kind='proof', witness_ordinal=1)
        text += ''.join('    '+k+': '+json.dumps(v)+'\n' for k,v in rule.items())
    text += '  source-only-italic:\n'
    rule = dict(literal=wave.ITALIC_LITERAL, command='textit', usage=wave.ITALIC_USAGE,
                source_label='test-lemma-one', witness_kind='proof', witness_ordinal=1)
    text += ''.join('    '+k+': '+json.dumps(v)+'\n' for k,v in rule.items())
    base = list(literals).index(' such that ')
    text += ('\ntranslatable_math_text_contexts:\n  source-only-such-that:\n'
             f'    base_rule: "source-only-{base}"\n'
             '    usage: "groupoids-wave-source-frames"\n'
             '    source_label: "test-lemma-one"\n'
             '    witness_kind: "proof"\n    witness_ordinal: 1\n')
    return text


def synthetic_fields(unit):
    # Literal test leaves are synthetic; no real candidate or review is claimed.
    text = unit['source_text']
    terms=[]
    for region in unit.get('math_text_regions', []):
        for slot in region['slots']:
            left,right = ('<'+p+'>' for p in slot['boundary_placeholders'])
            a=text.index(left)+len(left); b=text.index(right,a)
            role=slot['classification_witness']['usage']
            term=('2-isomorphism','同构') if role=='numeric-isomorphism-suffix' else (
                 ('2-category','范畴') if role=='matrix-numeric-category-prefix' else (
                 ('algebraic stack','代数栈') if slot['source']=='algebraic stack ' else None))
            target='合成测试文字'
            if term:
                english,chinese=term
                target=('-' if english.startswith('2-') else '')+chinese+'（'+english+'）'+target
                terms.append(dict(source_term=english,target_term=chinese))
            text=text[:a]+target+text[b:]
    if not unit.get('math_text_regions'):
        text=re.sub(r'<[A-Z][A-Z0-9]*_[0-9]{4}>|[A-Za-z]+',
                    lambda m: m[0] if m[0].startswith('<') else '合成', text)
    return dict(translation=text,allowed_english=[],term_occurrences=terms,
                unknown_terms=[dict(**t,context='Synthetic pending term, no approval.') for t in terms],
                notes=['Synthetic fixture, no actual model generation or approval.'])


def synthetic_history_fields(unit):
    fields = synthetic_fields(unit)
    fields.update(term_status='DECISION_REQUIRED' if fields['unknown_terms'] else 'CLEAR',
                  stage='STRUCTURE_OK' if fields['unknown_terms'] else 'TERM_OK')
    return fields


def locked_trial_policy(native):
    """Source-only opt-in experiment, never written to production config."""
    from stacks_zh.math_text import usage
    base=Policy(BEFORE)
    text=BEFORE
    registered=set()
    for c in FIXTURE['containers']:
        coordinate=c['selector']
        label=coordinate['owner_label']
        kind=coordinate['kind']
        if kind not in {'proof','lemma'}:
            label=next(k for k,v in native.english.tags.items() if v==coordinate['parent_tag'])
            kind='section'
        for frame in c['frames']:
            stream=nodes(frame)
            for index,node in enumerate(stream):
                command,literal=node.get('command'),node.get('value')
                if command not in {'text','textit'} or literal in {'id','pr','Cat','Sets','Spaces','CQC'}:
                    continue
                old=[(key,rule) for key,rule in base.math_text_rules.items()
                     if rule['literal']==literal and rule['command']==command]
                if old and any(usage(frame,stream,index,r['usage']) is not None for _,r in old):
                    continue
                pair=(command,literal)
                if pair in registered:continue
                registered.add(pair)
                witness=dict(source_label=label,witness_kind=kind,witness_ordinal=1)
                if old:
                    key,rule=next(((k,r) for k,r in old if r['usage']=='root-phrase'),old[0])
                    section='translatable_math_text_contexts'
                    fields=dict(base_rule=key,usage=wave.USAGE,**witness)
                else:
                    section='translatable_math_text'
                    role=(wave.ITALIC_USAGE if command=='textit'
                          else 'matrix-numeric-category-prefix' if literal=='-category of algebraic'
                          else wave.USAGE)
                    fields=dict(literal=literal,command=command,usage=role,**witness)
                entry='  independent-trial-'+str(len(registered))+':\n'
                entry+=''.join('    '+k+': '+json.dumps(v)+'\n' for k,v in fields.items())
                marker='\n'+section+':\n'
                if marker in text:text=text.replace(marker,marker+entry,1)
                else:text+=marker+entry
    text=text.replace('locked_math_text_notations:\n',
        'locked_math_text_notations:\n  CQC:\n    commands: ["textit"]\n'
        '    usages: ["groupoids-cqc-category"]\n'
        '    source_label: spaces-groupoids-section-crystals\n',1)
    return text


class GroupoidsWaveMathFramesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root,cls.harvest,_ = fixture(Path(cls.temp.name),proof=PROOF)
        (cls.root/'config/macro-policy.yml').write_text(synthetic_policy())
        with (cls.harvest/'tags/tags').open('a') as out:
            out.write('0003,test-equation-morphisms-schemes\n0004,test-equation-morphisms-spaces\n')
        git(cls.harvest,'add','tags/tags')
        git(cls.harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid',
            'commit','-qm','Independent synthetic frame labels')
        (cls.root/'upstream.lock').write_text('commit = "'+git(cls.harvest,'rev-parse','HEAD')+'"\n')
        cls.native=Containers(cls.root,cls.harvest)
        cls.policy=cls.native.policy

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_exact_frame_inventory_matches_independent_locked_source_fixture(self):
        self.assertEqual(byte_hash(BEFORE),FIXTURE['baseline_macro_hash'])
        self.assertTrue(FIXTURE['source_only']);self.assertFalse(FIXTURE['actual_model_data'])
        for name,expected in [('natural_frames',12),('italic_frames',4),('spaces_frames',4),('cqc_frames',2)]:
            self.assertEqual(tuple(FIXTURE[name]),getattr(wave,name.upper()))
            self.assertEqual(len(FIXTURE[name]),expected)
        self.assertEqual(len(FIXTURE['containers']),17)
        self.assertTrue(all(c['baseline_selection_error'] for c in FIXTURE['containers']))

    def test_all_parameters_are_typed_without_changing_locked_math(self):
        for frame in FIXTURE['natural_frames']+FIXTURE['italic_frames']:
            with self.subTest(frame=frame):
                slots=find_slots(frame,self.policy.math_text_rules)
                expected=[n['value'] for n in nodes(frame)
                          if n.get('command')=='text' or n.get('command')=='textit' and n['value']==wave.ITALIC_LITERAL]
                self.assertEqual([s['value'] for s in slots],expected)
                scanner=Scanner(frame,self.policy)
                self.assertFalse(scanner.protect(0,len(frame))[2])
                self.assertEqual(len(slots),sum(len(r['slots']) for r in scanner.math_text_regions))

    def test_complete_synthetic_git_proof_roundtrips_schema_and_skeleton(self):
        unit=lower_container(self.native.select(selector()),self.policy)[0]
        self.assertEqual(unit['schema_version'],2)
        self.assertEqual(source_tex(unit),PROOF)
        self.assertEqual(validate_named_schema(unit,'unit.schema.json','synthetic'),[])
        self.assertEqual(validate_regions(unit),[])
        self.assertEqual(validate_translation(unit,synthetic_fields(unit)['translation']),[])
        from stacks_zh.source_terms import source_projection
        projected,declarations=source_projection(unit)
        self.assertIn('2-isomorphism',declarations)
        self.assertIn('2-category',declarations)
        self.assertEqual(projected.count('2-isomorphism'),2)
        self.assertEqual(projected.count('2-category'),2)
        damaged=copy.deepcopy(unit);damaged['math_text_regions'][0]['source']+='x'
        damaged=stamp_unit_hashes(damaged)
        self.assertTrue(validate_regions(damaged))

    def test_changed_math_depth_command_gap_label_and_unknown_text_do_not_gain_finite_roles(self):
        for frame in FIXTURE['natural_frames']+FIXTURE['italic_frames']:
            stream=nodes(frame)
            first=next(n for n in stream if n.get('command')=='text' or n.get('value')==wave.ITALIC_LITERAL)
            unknown=frame[:first['parameter_start']]+'unknown prose'+frame[first['parameter_end']:]
            self.assertFalse(any(s['value']=='unknown prose' for s in find_slots(unknown,self.policy.math_text_rules)))
            self.assertTrue(Scanner(unknown,self.policy).protect(0,len(unknown))[2])
            variants=[frame+'x',frame.replace('\\text{','\\textbf{',1) if '\\text{' in frame
                      else frame.replace('\\textit{','\\textbf{',1),
                      '{'+frame+'}',frame.replace('\n','\n ',1) if '\n' in frame else frame.replace('$','$ ',1)]
            operand=next(n for n in stream if re.fullmatch('[A-Za-z]',n['token']))
            variants.append(frame[:operand['start']]+'Z'+frame[operand['end']:])
            if '\\label{' in frame:variants.append(frame.replace('equation-morphisms','equation-altered',1))
            for variant in variants:
                if variant==frame:continue
                with self.subTest(variant=variant):
                    try:slots=find_slots(variant,self.policy.math_text_rules)
                    except ValueError:slots=[]
                    self.assertFalse(any(s['usage'] in wave.USAGES for s in slots))

    def test_italic_pair_schema_and_policy_remain_closed(self):
        source=FIXTURE['italic_frames'][0]
        unit=lower_container(self.native.select(selector()),self.policy)[0]
        slot=next(s for r in unit['math_text_regions'] for s in r['slots'] if s['command']=='textit')
        for key,value in [('source','Other-Stacks'),('command','textbf')]:
            bad=copy.deepcopy(unit)
            target=next(s for r in bad['math_text_regions'] for s in r['slots'] if s['command']=='textit')
            target[key]=value
            self.assertTrue(validate_named_schema(bad,'unit.schema.json','synthetic'))
            self.assertTrue(validate_regions(bad))
        for change in [('"Algebraic-Stacks"','"Other-Stacks"'),
                       ('"algebraic-stack-category-phrase"','"groupoids-wave-source-frames"')]:
            with self.assertRaises(RecordError):Policy(synthetic_policy().replace(*change))
        for f in [r'$\textit{Algebraic-Stacks}$',r'$A+\textit{Algebraic-Stacks}/S$',
                  source.replace('/S','/Z'),source.replace('textit','text')]:
            self.assertTrue(Scanner(f,self.policy).protect(0,len(f))[2])

    def test_notation_only_accepts_exact_cqc_spaces_frames(self):
        for f in FIXTURE['spaces_frames']+FIXTURE['cqc_frames']:
            text,ph,errors=Scanner(f,self.policy).protect(0,len(f))
            self.assertFalse(errors);self.assertEqual(text,'<MATH_0001>');self.assertEqual(ph,{'MATH_0001':f})
            for changed in [f.replace('textit','text'),f.replace('CQC','CQCx').replace('Spaces','Spacesx'),
                            f.replace('(X)','(Y)').replace('/B','/Z').replace('/S','/Z')]:
                if changed!=f:self.assertTrue(Scanner(changed,self.policy).protect(0,len(changed))[2], changed)
        for f in [r'$\textit{CQC}$',r'$\textit{CQC}(Y)$',r'$A+\textit{CQC}(X)$']:
            self.assertTrue(Scanner(f,self.policy).protect(0,len(f))[2])
        for change in [('usages: ["groupoids-cqc-category"]','usages: ["applied"]'),
                       ('commands: ["textit"]\n    usages: ["groupoids-cqc-category"]',
                        'commands: ["text"]\n    usages: ["groupoids-cqc-category"]')]:
            with self.assertRaises(RecordError):Policy(synthetic_policy().replace(*change))

    def test_existing_ordinary_role_has_priority_and_context_is_finite(self):
        source=FIXTURE['natural_frames'][4]
        # The source set with root such-that is already supported by its old role.
        source=next(f for f in FIXTURE['natural_frames'] if '\\overline{u}' in f and '\\text{ such that }' in f)
        slots=find_slots(source,self.policy.math_text_rules)
        self.assertEqual(len(slots),1);self.assertEqual(slots[0]['usage'],'root-phrase')
        invalid=synthetic_policy().replace('usage: "root-phrase"','usage: "matrix-row-text"',1)
        with self.assertRaises(RecordError):Policy(invalid)
        baseline=Policy(BEFORE)
        for source in FIXTURE['natural_frames']+FIXTURE['italic_frames']:
            self.assertFalse(any(s['usage'] in wave.USAGES for s in find_slots(source,baseline.math_text_rules)))

    def test_two_complete_synthetic_histories_replay_render_and_reject_tampering(self):
        from test_group_derivations import fixture as history_fixture, read, write
        from stacks_zh.provenance import validate_repository_provenance
        from stacks_zh.schema_validation import validate_repository_schemas
        from stacks_zh.source_containers import load_source_containers
        from stacks_zh.workflow import render_batch
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,records=history_fixture(Path(tmp),count=2,proof=PROOF,
                math_policy=synthetic_policy(),synthetic_fields=synthetic_history_fields)
            self.assertEqual(validate_repository_schemas(root),[])
            self.assertEqual(validate_repository_provenance(root,harvest),[])
            current=records[-1]
            pending = [c for c in load_jsonl(root/current['files']['output_candidates']['path'])
                       if c['unknown_terms']]
            self.assertTrue(pending)
            self.assertTrue(all(c['term_status'] == 'DECISION_REQUIRED'
                                and c['stage'] == 'STRUCTURE_OK' for c in pending))
            paths=render_batch(root/current['files']['output_units']['path'],
                root/current['files']['output_candidates']['path'],root/'upstream.lock',
                root/'preview','fixture','Synthetic fixture',chapter_source_dir=harvest)
            rendered=''.join(p.read_text() for p in paths)
            self.assertIn('合成测试文字',rendered)
            self.assertNotIn('MATHSEG_',rendered)
            evidence=root/'translation-data/source-container-restorations/fixture-group-2-proof.json'
            value=read(evidence)
            value['new_units'][-1]['math_text_regions'][0]['source']+='x'
            write(evidence,value)
            self.assertTrue(load_source_containers(root,harvest)[1])
            self.assertTrue(validate_repository_provenance(root,harvest))

    def test_first_adoption_binds_full_source_raw_context_schema_and_render(self):
        import shutil
        from test_source_adoptions import synthetic_fixture, write
        from stacks_zh.harness import resolve_harness
        from stacks_zh.provenance import validate_repository_provenance
        from stacks_zh.records import write_jsonl, sha256_value
        from stacks_zh.schema_validation import validate_repository_schemas
        from stacks_zh.source_adoptions import POLICIES, assemble_source_adoption, load_repository_source_adoptions
        from stacks_zh.workflow import render_batch
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,fp,rp,previous,_=synthetic_fixture(Path(tmp),typed=False)
            for directory in ['translation-data','task-scopes','docs/evidence']:
                shutil.rmtree(root/directory)
            statement=r'\begin{lemma}\label{lemma-one}A claim.\end{lemma}'
            (harvest/'test.tex').write_text('\\begin{document}\n\\section{Basics}\n'
                '\\label{section-basic}\n'+statement+'\n'+PROOF+'\n\\end{document}\n')
            (harvest/'tags/tags').write_text('0000,test-section-basic\n0001,test-lemma-one\n'
                '0003,test-equation-morphisms-schemes\n0004,test-equation-morphisms-spaces\n')
            git(harvest,'add','test.tex','tags/tags')
            git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid',
                'commit','-qm','Independent complete groupoid frames')
            source=git(harvest,'rev-parse','HEAD')
            (root/'upstream.lock').write_text('commit = "'+source+'"\n')
            (root/'config/macro-policy.yml').write_text(synthetic_policy())
            native=Containers(root,harvest)
            groups=[native.select(selector('section_title',owner='0000')),
                    native.select(selector('lemma')),native.select(selector())]
            units=[lower_container(g,native.policy)[0] for g in groups]
            from stacks_zh.source_terms import source_tex_hash
            write(root/'config/source-terms.json',dict(schema_version=1,source_commit=source,
                nonmathematical_declarations={},terms=[dict(id='synthetic-stack',forms=['algebraic stack'],
                chapters=[],evidence=[dict(chapter='test',unit_id=units[2]['unit_id'],
                    source_term='algebraic stack',source_tex_hash=source_tex_hash(units[2]))])]))
            git(root,'add','config','upstream.lock')
            git(root,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid',
                'commit','-qm','Synthetic accepted frame policy, no model facts')
            origin=git(root,'rev-parse','HEAD')
            batches=[]
            for name,gs,us in [('title',groups[:1],units[:1]),('lemma-proof',groups[1:],units[1:])]:
                up=f'translation-data/units/test-{name}.jsonl'
                cp=f'translation-data/candidates/synthetic/test-{name}.jsonl'
                write_jsonl(root/up,us)
                batches.append(dict(units_path=up,candidates_path=cp,units=us,prior_attempts=[],
                    containers=[dict(selector=g['selector'],selected=g,unit_ids=[u['unit_id']])
                                for g,u in zip(gs,us)]))
            runtime=copy.deepcopy(previous['runtime'])
            runtime['harness']['version']=resolve_harness('synthetic',root/'config/harnesses.yml').version
            ids=[u['unit_id'] for u in units]
            frozen=dict(schema_version=1,tool_version='source-adoption-input-v1',
                adoption_id='synthetic-first',origin_commit=origin,source_commit=source,
                task_id='synthetic-only',created_at='2026-10-19T00:00:00Z',runtime=runtime,
                policies=[dict(path=p,hash=byte_hash((root/p).read_bytes())) for p in POLICIES],
                contexts=[],batches=batches,outside_preferred_reason='Independent synthetic full frames.',
                unit_ids=ids,chapter='test',parent_tags=['0000'],run_id='run-synthetic-first')
            for row in native.document('test')[1]:
                value=dict(kind='locked-English-neighbor',location=row['location'],source_commit=source,
                    source_unit=row['unit'],owner_tag=row['owner_tag'],parent_tag=row['parent_tag'])
                frozen['contexts'].append(dict(context_id=row['unit']['unit_id'],value=value,hash=sha256_value(value)))
            scope_path='task-scopes/synthetic-first.json'
            files=[scope_path,fp.relative_to(root).as_posix(),rp.relative_to(root).as_posix(),
                   'translation-data/runs/run-synthetic-first.json',
                   'translation-data/source-adoptions/synthetic-first.json']
            files += [b[role] for b in batches for role in ['units_path','candidates_path']]
            branch=git(root,'branch','--show-current')
            scope=dict(schema_version=1,task_id='synthetic-only',owner='synthetic',branch=branch,
                source_commit=source,allowed_write_files=files,data_scopes=[dict(scope_id='synthetic',
                chapter='test',parent_tags=['0000'],historical_parent_tags=[],unit_ids=ids,
                input_unit_ids=ids,output_unit_ids=ids,allowed_write_files=files[1:],
                run_scope=['run-synthetic-first'],model_scope=['synthetic','synthetic:fixture:declared'])])
            write(root/scope_path,scope)
            frozen['task']=dict(issue=1,owner='synthetic',branch=branch,scope_manifest=scope_path,
                scope_manifest_sha256=byte_hash((root/scope_path).read_bytes()),
                scope_bytes=(root/scope_path).read_text())
            write(fp,frozen)
            write_jsonl(rp,[dict(unit_id=u['unit_id'],**synthetic_fields(u)) for u in units])
            assemble_source_adoption(root,fp,[rp],harvest)
            self.assertEqual(load_repository_source_adoptions(root,harvest)[1],[])
            self.assertEqual(validate_repository_schemas(root),[])
            self.assertEqual(validate_repository_provenance(root,harvest),[])
            paths=render_batch([root/b['units_path'] for b in batches],
                [root/b['candidates_path'] for b in batches],root/'upstream.lock',root/'preview',
                'synthetic','Synthetic fixture',chapter_source_dir=harvest)
            self.assertIn('合成测试文字',''.join(p.read_text() for p in paths))
            broken=copy.deepcopy(frozen);broken['contexts']=[];write(fp,broken)
            self.assertTrue(load_repository_source_adoptions(root,harvest)[1])


@unittest.skipUnless(os.environ.get('HARVEST_DIR'),'requires explicit read-only locked harvest')
class LockedGroupoidsWaveMathFramesTests(unittest.TestCase):
    def test_all_17_containers_lower_and_roundtrip_under_isolated_trial_policy(self):
        harvest=Path(os.environ['HARVEST_DIR'])
        current_before=(ROOT/'config/macro-policy.yml').read_bytes()
        baseline=Containers(ROOT,harvest,policy_bytes=BEFORE.encode())
        native=Containers(ROOT,harvest,policy_bytes=locked_trial_policy(baseline).encode())
        for c in FIXTURE['containers']:
            with self.subTest(selector=c['selector']):
                selected=native.select(c['selector'])
                self.assertEqual(selected['fragment'],c['fragment'])
                units=lower_container(selected,native.policy)
                self.assertEqual(''.join(source_tex(u) for u in units),c['fragment'])
                for u in units:
                    self.assertEqual(validate_named_schema(u,'unit.schema.json','source-only'),[])
                    if u.get('math_text_regions'):
                        self.assertEqual(validate_regions(u),[])
                        self.assertEqual(validate_translation(u,synthetic_fields(u)['translation']),[])
        self.assertEqual((ROOT/'config/macro-policy.yml').read_bytes(),current_before)

    def test_all_complete_original_containers_match_locked_git_and_old_blockers(self):
        native=Containers(ROOT,Path(os.environ['HARVEST_DIR']),policy_bytes=BEFORE.encode())
        self.assertEqual(native.english.commit,FIXTURE['source_commit'])
        for c in FIXTURE['containers']:
            raw=native.document(c['chapter'])[0];span=c['source_byte_span']
            self.assertEqual(byte_hash(raw),c['source_blob_hash'])
            self.assertEqual(raw[span['start']:span['end']].decode(),c['fragment'])
            self.assertEqual(byte_hash(c['fragment']),c['fragment_hash'])
            for f in c['frames']:self.assertIn(f,c['fragment'])
            # New Spaces shapes reuse a previously registered finite notation;
            # no unregistered natural/CQC/italic rule receives permission.
            textual = [n for f in c['frames'] for n in nodes(f)
                       if n.get('command') in {'text','textit'}]
            if any(n['value'] not in {'Spaces','Sets','Cat','pr','id','-isomorphism'} for n in textual):
                with self.assertRaises(RecordError, msg=str(c['selector'])):native.select(c['selector'])
            else:
                selected=native.select(c['selector'])
                self.assertEqual(selected['fragment'],c['fragment'])


if __name__=='__main__':unittest.main()
