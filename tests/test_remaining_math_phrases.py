"""Literal independent English/Git examples for each new natural-text role."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_source_containers import fixture as english_fixture, git, old_unit, selector
from test_derivations import fixture as candidate_fixture
from test_group_derivations import commit, run_for, save, write
from stacks_zh.extraction import Policy
from stacks_zh.math_text import find_slots, validate_regions, validate_translation
from stacks_zh.records import RecordError, placeholder_names, sha256_value, stamp_unit_hashes
from stacks_zh.source_containers import Containers, load_source_containers, lower_container, verify_old_group, write_container_package
from stacks_zh.source_native_prose_boundaries import prose_signature
from stacks_zh.source_reextractions import source_tex

BASE=(Path(__file__).resolve().parents[1]/'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0]
CASES=[
    ('membership',' in ','root-phrase',r'$i\text{ in }I$'),
    ('conjunction',' and ','root-phrase',r'$i\leq j\text{ and }j\leq i$'),
    ('composition',' composes to ','root-phrase',r'$$\xymatrix{A\ar[r]&B}\text{ composes to }\xymatrix{A\ar[r]&C}$$'),
    ('gives',' gives ','root-phrase',r'$A\text{ gives }B$'),
    ('unit','unit','root-phrase',r'$\eta:F\to G\quad(\text{unit})$'),
    ('counit','counit','root-phrase',r'$\epsilon:G\to F\quad(\text{counit})$'),
    ('in-prefix','in ','root-phrase',r'$x\quad\text{in }X$'),
    ('lying-over',' lying over ','root-phrase',r'$x\text{ lying over }y$'),
    ('annotation',' monomorphism','root-phrase',r'$\{x\to X\text{ monomorphism}\}$'),
    ('condition','if ','matrix-prefix-condition',r'$$\begin{matrix}0 & \text{if }i>0\\ F & \text{if }i=0\end{matrix}$$'),
    ('arrow','restriction of ','arrow-label-prefix',r'$x\xrightarrow{\text{restriction of }f}y$'),
]


def policy_text():
    text=BASE+'\ntranslatable_math_text:\n'
    for name,literal,usage,_ in CASES:
        text+=('  '+name+':\n    literal: '+json.dumps(literal)+'\n    command: "text"\n'
               '    usage: '+json.dumps(usage)+'\n    source_label: "test-lemma-one"\n'
               '    witness_kind: "proof"\n    witness_ordinal: 1\n')
    return text


class RemainingMathPhrasesTests(unittest.TestCase):
    def test_exact_complete_parameters_and_roles(self):
        rules=Policy(policy_text()).math_text_rules
        for name,literal,usage,source in CASES:
            with self.subTest(name=name):
                found=find_slots(source,rules)
                self.assertEqual([s['value'] for s in found],[literal]*(2 if name=='condition' else 1))
                self.assertTrue(all(s['usage']==usage for s in found))
                for slot in found:self.assertEqual(source[slot['parameter_start']:slot['parameter_end']],literal)

    def test_wrong_syntax_spacing_command_and_hidden_text_stay_blocked(self):
        rules=Policy(policy_text()).math_text_rules
        for source in [r'$\text{ in }$',r'$x\text{in}X$',r'$x\text{  in }X$',r'$x\textit{ in }X$',
                       r'$x^{\text{ in }}$',r'$x\foo{\text{ in }}y$',r'$A & \text{if }i$',
                       r'$\begin{matrix}A\text{if }i\end{matrix}$',r'$x\to{\text{restriction of }f}y$',
                       r'$x\xrightarrow{f\text{restriction of }g}y$',r'$\verb|x\text{ in }X|$',
                       r'$x% \text{ in }\nX$',r'$x\text{ irred.\ comp. with }y$']:
            with self.subTest(source=source):self.assertEqual(find_slots(source,rules),[])

    def test_real_git_witnesses_whole_regions_math_protection_and_plain_translation(self):
        proof='\\begin{proof}\n'+ '\n'.join(x[3] for x in CASES)+'\n\\end{proof}'
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_=english_fixture(Path(tmp),proof=proof)
            (root/'config/macro-policy.yml').write_text(policy_text())
            c=Containers(root,harvest);selected=c.select(selector('proof'))
            unit=lower_container(selected,c.policy)[0]
            self.assertEqual(unit['schema_version'],2)
            self.assertEqual(source_tex(unit),selected['fragment'])
            self.assertEqual(validate_regions(unit),[])
            self.assertEqual(len(unit['math_text_regions']),11)
            self.assertEqual(sum(len(r['slots']) for r in unit['math_text_regions']),12)
            self.assertEqual(validate_translation(unit,unit['source_text']),[])
            changed=unit['source_text'].replace('restriction of ',r'\evil ',1)
            self.assertTrue(validate_translation(unit,changed))
            source_sig=prose_signature(selected['fragment'],c,'test')
            self.assertIn(['protected',CASES[0][3]],source_sig)
            self.assertNotEqual(source_sig,prose_signature(selected['fragment'].replace('$i\\text{ in }I$', '$j\\text{ in }I$'),c,'test'))
            bad=copy.deepcopy(unit);bad['math_text_regions'][0]['slots'][0]['classification_witness']['usage']='arrow-label-prefix'
            self.assertTrue(validate_regions(bad))
            c.assert_unchanged()

    def test_v13_compares_complete_original_math_from_old_v1_to_new_v2(self):
        body='\\noindent\nA diagram $i\\text{ in }I$.\n'
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,source=english_fixture(Path(tmp),statement=body+'\\section{Next}\\label{lemma-two}\n',proof='')
            # The independent witness is a real proof, rather than a forged
            # occurrence inside a comment or the paragraph being authorized.
            raw=(harvest/'test.tex').read_text();raw=raw.replace('\\end{document}',
                '\\begin{lemma}\\label{lemma-one}Witness.\\end{lemma}\n'+
                '\\begin{proof}\n'+'\n'.join(x[3] for x in CASES)+'\n\\end{proof}\n\\end{document}')
            (harvest/'test.tex').write_text(raw);git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','independent witnesses')
            source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
            (root/'config/macro-policy.yml').write_text(policy_text())
            heading=old_unit(source,'tag:0000:title','section_title','Basics','\\section{','}\\label{test-section-basic}\n')
            paragraph=old_unit(source,'tag:0000:p001','paragraph','A diagram <MATH_0001>.','\\noindent\n','\n\n')
            paragraph['placeholders']={'MATH_0001':r'$i\text{ in }I$'};paragraph=stamp_unit_hashes(paragraph)
            c=Containers(root,harvest);selected=c.select(selector('paragraph',owner='0000'))
            witness=verify_old_group([heading,paragraph],c.english.tags,[paragraph['unit_id']],selected,native_containers=c,allow_native_prose=True)
            self.assertIn('native_prose_anchor',witness)
            self.assertEqual(selected['inventory_unit']['schema_version'],2)
            bad=copy.deepcopy(paragraph);bad['placeholders']['MATH_0001']=r'$j\text{ in }I$'
            with self.assertRaises(RecordError):verify_old_group([heading,bad],c.english.tags,[bad['unit_id']],selected,native_containers=c,allow_native_prose=True)

    def test_v13_typed_package_and_origin_loader_preserve_full_old_inputs(self):
        from test_native_prose_boundaries import INTRO,MIDDLE,NEXT
        proof='\\begin{proof}\n'+'\n'.join(x[3] for x in CASES)+'\n\\end{proof}\n'
        body=INTRO+MIDDLE+proof+'\\noindent\nLast paragraph with $i\\text{ in }I$.\n'+NEXT
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,source=english_fixture(Path(tmp),statement=body,proof='')
            (root/'config/macro-policy.yml').write_text(policy_text())
            units=[old_unit(source,'tag:0000:title','section_title','Basics','\\section{','}\\label{test-section-basic}\n'),
                   old_unit(source,'tag:0000:p001','paragraph','First paragraph with <MATH_0001>.','\\noindent\n','\n\n'),
                   old_unit(source,'tag:0000:p002','paragraph','Last paragraph with <MATH_0001>.','\\noindent\n','\n\n')]
            units[1]['placeholders']={'MATH_0001':'$x$'};units[2]['placeholders']={'MATH_0001':r'$i\text{ in }I$'}
            units=[stamp_unit_hashes(u) for u in units];template=candidate_fixture()[2][0];candidates=[]
            for u in units:
                c=copy.deepcopy(template);context=dict(unit_id=u['unit_id'],source_commit=source,prompt_version='fixture',policy_revision='fixture')
                c.update(unit_id=u['unit_id'],source_commit=source,source_text_hash=u['source_text_hash'],context=context,
                    context_hash=sha256_value(context),run_id='synthetic-typed-boundary',translation=''.join('<'+n+'>' for n in placeholder_names(u['source_text']))+' synthetic.',
                    allowed_english=[],term_occurrences=[],unknown_terms=[],notes=['Synthetic only.'],term_status='CLEAR',stage='TERM_OK',qa_status='PASS',publication_status='CANDIDATE')
                c['translation_hash']=sha256_value(c['translation']);candidates.append(c)
            up='translation-data/units/test-typed.jsonl';cp='translation-data/candidates/fixture/test-typed.jsonl'
            save(root,up,units);save(root,cp,candidates);write(root/'translation-data/runs/synthetic-typed-boundary.json',run_for(candidates,source,'translation','synthetic-typed-boundary'))
            git(root,'init','-q');commit(root)
            plan=dict(derivation_id='synthetic-typed-boundary',created_at='2026-10-14T00:00:00Z',units_file=up,candidates_file=cp,groups=[])
            for index,u in enumerate(units):
                plan['groups'].append(dict(group_id='node-'+str(index),input_unit_ids=[u['unit_id']],identity_anchor=u['unit_id'],
                    selector=selector('section_title' if index==0 else 'paragraph',ordinal=max(1,index),owner='0000'),layout='whole',reason='Synthetic full typed boundary only.'))
            path=root/'build/plan.json';write(path,plan);output=root/'build/package';manifest=write_container_package(root,harvest,path,output)
            self.assertEqual(manifest['state'],'PREPARED')
            self.assertEqual(write_container_package(root,harvest,path,output,check=True),manifest)
            records=json.loads((output/'restorations.json').read_text());target=next(r for r in records if r['tool']['version']=='source-container-v13')
            self.assertEqual(target['new_units'][0]['schema_version'],2)
            for record in records:
                for role,name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                    dest=root/record['files'][role]['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((output/name).read_bytes())
                write(root/f"translation-data/source-container-restorations/{record['restoration_id']}.json",record)
            self.assertFalse(load_source_containers(root,harvest)[1])
            bad=copy.deepcopy(target);bad['new_units'][0]['math_text_regions'][0]['slots'][0]['classification_witness']['usage']='arrow-label-prefix'
            write(root/f"translation-data/source-container-restorations/{target['restoration_id']}.json",bad)
            self.assertTrue(load_source_containers(root,harvest)[1])
