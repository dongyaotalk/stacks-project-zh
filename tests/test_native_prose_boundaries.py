"""Independent native boundaries; synthetic records never claim model authorship."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_derivations import fixture as candidate_fixture
from test_group_derivations import commit, run_for, save, write
from test_source_containers import fixture as english_fixture, git, old_unit, selector
from stacks_zh.extraction import Scanner
from stacks_zh.records import RecordError, placeholder_names, sha256_value, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import Containers, load_source_containers, verify_old_group, write_container_package

INTRO = '\\noindent\nFirst paragraph with $x$.\n\n'
MIDDLE = '\\begin{definition}\\label{lemma-one}A complete definition.\\end{definition}\n\n'
LAST = '\\noindent\nLast paragraph with $y$.\n'
NEXT = '\\section{Next}\\label{lemma-two}\n'


def fixture(base, tail=LAST + NEXT):
    root, harvest, source = english_fixture(base, statement=INTRO + MIDDLE + tail, proof='')
    units = [old_unit(source, 'tag:0000:title', 'section_title', 'Basics', '\\section{',
                      '}\n\\label{test-section-basic}\n'),
             old_unit(source, 'tag:0000:p001', 'paragraph', 'First paragraph with <MATH_0001>.', '\\noindent\n', '\n\n'),
             old_unit(source, 'tag:0000:p002', 'paragraph', 'Last paragraph with <MATH_0001>.', '\\noindent\n', '\n\n')]
    units[1]['placeholders'] = {'MATH_0001': '$x$'}
    units[2]['placeholders'] = {'MATH_0001': '$y$'}
    units = [stamp_unit_hashes(u) for u in units]
    template = candidate_fixture()[2][0]
    candidates = []
    for unit in units:
        candidate = copy.deepcopy(template)
        context = dict(unit_id=unit['unit_id'], source_commit=source, prompt_version='fixture', policy_revision='fixture')
        candidate.update(unit_id=unit['unit_id'], source_commit=source, source_text_hash=unit['source_text_hash'],
            context=context, context_hash=sha256_value(context), run_id='synthetic-native-prose',
            translation=''.join('<'+n+'>' for n in placeholder_names(unit['source_text']))+'合成测试。',
            allowed_english=[], term_occurrences=[], unknown_terms=[], notes=['Synthetic fixture only.'],
            term_status='CLEAR', stage='TERM_OK', qa_status='PASS', publication_status='CANDIDATE')
        candidate['translation_hash'] = sha256_value(candidate['translation'])
        candidates.append(candidate)
    up='translation-data/units/test-native.jsonl'; cp='translation-data/candidates/fixture/test-native.jsonl'
    save(root, up, units); save(root, cp, candidates)
    write(root/'translation-data/runs/synthetic-native-prose.json', run_for(candidates,source,'translation','synthetic-native-prose'))
    git(root,'init','-q'); commit(root)
    plan=dict(derivation_id='synthetic-native-prose',created_at='2026-10-14T00:00:00Z',units_file=up,candidates_file=cp,groups=[])
    for index, unit in enumerate(units):
        coordinate=selector('section_title' if index == 0 else 'paragraph', ordinal=max(1,index), owner='0000')
        plan['groups'].append(dict(group_id='node-'+str(index),input_unit_ids=[unit['unit_id']],identity_anchor=unit['unit_id'],
                                   selector=coordinate,layout='whole',reason='Synthetic complete native prose; no actual generation.'))
    path=root/'build/plan.json';write(path,plan)
    return root,harvest,units,path,root/'build/package'


class NativeProseTests(unittest.TestCase):
    def test_complete_footer_prose_uses_native_version_and_replays_nested_history(self):
        body='\nIntro.\n\\begin{enumerate}\\item Outer.\n\\begin{enumerate}\\item Inner.\n\\end{enumerate}\nEnd outer.\n\\end{enumerate}\n'
        for nested in (False, True):
            with self.subTest(nested=nested), tempfile.TemporaryDirectory() as tmp:
                tail='\n\\section{Closing}\\label{lemma-two}'+body+'\\input{chapters}\n\\bibliography{mybib}\n'
                root,harvest,source=english_fixture(Path(tmp),statement='',proof='',other=tail)
                c=Containers(root,harvest)
                head=old_unit(source,'tag:0002:title','section_title','Closing','\\section{','}\\label{test-lemma-two}')
                if nested:
                    pieces=[('paragraph','Intro.','\n','\n'),
                            ('list_item_intro','Outer.','\\begin{enumerate}\\item ','\n\\begin{enumerate}'),
                            ('nested_list_item','Inner.','\\item ','\n\\end{enumerate}\n'),
                            ('list_item_outro','End outer.','','\n\\end{enumerate}\n')]
                    members=[old_unit(source,f'tag:0002:piece-{i}',kind,text,prefix,suffix)
                             for i,(kind,text,prefix,suffix) in enumerate(pieces)]
                else:
                    text,protected,errors=Scanner(body,c.policy).protect(0,len(body));self.assertFalse(errors)
                    member=old_unit(source,'tag:0002:body','paragraph',text)
                    member['placeholders']=protected;members=[stamp_unit_hashes(member)]
                units=[stamp_unit_hashes({**u,'parent_tag':'0002'}) for u in [head,*members]]
                template=candidate_fixture()[2][0];candidates=[]
                for u in units:
                    candidate=copy.deepcopy(template)
                    context=dict(unit_id=u['unit_id'],source_commit=source,prompt_version='fixture',policy_revision='fixture')
                    candidate.update(unit_id=u['unit_id'],source_commit=source,source_text_hash=u['source_text_hash'],
                        context=context,context_hash=sha256_value(context),run_id='synthetic-footer',
                        translation=''.join('<'+n+'>' for n in placeholder_names(u['source_text']))+' synthetic.',
                        allowed_english=[],term_occurrences=[],unknown_terms=[],notes=['Synthetic only.'],
                        term_status='CLEAR',stage='TERM_OK',qa_status='PASS',publication_status='CANDIDATE')
                    candidate['translation_hash']=sha256_value(candidate['translation']);candidates.append(candidate)
                up='translation-data/units/test-footer.jsonl';cp='translation-data/candidates/fixture/test-footer.jsonl'
                save(root,up,units);save(root,cp,candidates)
                write(root/'translation-data/runs/synthetic-footer.json',run_for(candidates,source,'translation','synthetic-footer'))
                git(root,'init','-q');commit(root)
                coordinate={**selector('prose_block',owner='0002'),'parent_tag':'0002'}
                selected=c.select(coordinate)
                self.assertTrue(selected['_native_document_footer']);self.assertNotIn('\\input',selected['fragment'])
                with self.assertRaisesRegex(RecordError,'footer.*v13'):
                    verify_old_group(units,c.english.tags,[u['unit_id'] for u in units[1:]],selected,allow_outer_whitespace=True)
                plan=dict(derivation_id='synthetic-footer',created_at='2026-10-16T00:00:00Z',units_file=up,candidates_file=cp,
                    groups=[dict(group_id='body',input_unit_ids=[u['unit_id'] for u in units[1:]],identity_anchor=units[1]['unit_id'],
                                 selector=coordinate,layout='whole',reason='Synthetic complete footer-bound prose.')])
                # Freeze the complete ordered batch, including the real heading.
                plan['groups'].insert(0,dict(group_id='heading',input_unit_ids=[units[0]['unit_id']],identity_anchor=units[0]['unit_id'],
                    selector={**coordinate,'kind':'section_title'},layout='whole',reason='Synthetic actual owning heading.'))
                path=root/'build/plan.json';write(path,plan);output=root/'build/package'
                manifest=write_container_package(root,harvest,path,output)
                self.assertEqual(manifest['state'],'PREPARED',(output/'diagnostics.json').read_text())
                self.assertEqual(write_container_package(root,harvest,path,output,check=True),manifest)
                records=json.loads((output/'restorations.json').read_text());record=records[-1]
                self.assertEqual(record['tool']['version'],'source-container-v13')
                self.assertIn('native_prose_anchor',record['legacy_boundary_witness'])
                for role,name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                    dest=root/record['files'][role]['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((output/name).read_bytes())
                destination=root/f"translation-data/source-container-restorations/{record['restoration_id']}.json";write(destination,record)
                self.assertFalse(load_source_containers(root,harvest)[1])
                bad=copy.deepcopy(record);bad['legacy_boundary_witness']['native_prose_anchor']['native_interval']['end']-=1
                write(destination,bad);self.assertTrue(load_source_containers(root,harvest)[1])
                bad=copy.deepcopy(record);bad['tool']['version']='source-container-v2';bad.pop('legacy_boundary_witness')
                write(destination,bad);self.assertTrue(any('input' in e for e in load_source_containers(root,harvest)[1]))
                bad_units=copy.deepcopy(units)
                if nested:
                    bad_units[-1]['render']['suffix']=''
                else:
                    token=next(k for k,v in bad_units[-1]['placeholders'].items() if v=='\\end{enumerate}')
                    bad_units[-1]['source_text']=bad_units[-1]['source_text'].replace('<'+token+'>','',1)
                    del bad_units[-1]['placeholders'][token]
                self.assertNotEqual(bad_units,units)
                with self.assertRaises(RecordError):
                    verify_old_group(bad_units,c.english.tags,[u['unit_id'] for u in bad_units[1:]],selected,
                                     native_containers=c,allow_outer_whitespace=True,allow_native_prose=True)
                raw=(harvest/'test.tex').read_text().replace('\\input{chapters}','\\input{other}')
                (harvest/'test.tex').write_text(raw);git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','unclassified footer')
                (root/'upstream.lock').write_text('commit = "'+git(harvest,'rev-parse','HEAD')+'"\n')
                with self.assertRaisesRegex(RecordError,'input'):
                    Containers(root,harvest).select(coordinate)

    def test_full_labelled_equation_paragraph_binds_actual_section_and_replays_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            tail='\\noindent\nWe choose $x$.\n\\begin{equation}\n\\label{equation-one}\nx=y.\n\\end{equation}\nThen use $y$.\n'
            next_statement='\\begin{lemma}\\label{lemma-two}Next statement.\\end{lemma}\n'
            root,harvest,_=english_fixture(Path(tmp),other=tail+next_statement)
            with (harvest/'tags/tags').open('a') as f:f.write('0003,test-equation-one\n')
            git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','independent labelled mathematical prose')
            source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
            c=Containers(root,harvest);old_source=tail.replace(r'\label{equation-one}',r'\label{test-equation-one}')
            scanner=Scanner(old_source,c.policy);text,protected,errors=scanner.protect(0,len(old_source));self.assertFalse(errors)
            old=old_unit(source,'tag:0003','paragraph',text);old.update(parent_tag='0003',placeholders=protected);old=stamp_unit_hashes(old)
            from stacks_zh.source_containers import old_container_groups
            groups=[g for g in old_container_groups([old],c.english.tags,native_containers=c) if 'labelled_math' in g]
            self.assertEqual(len(groups),1);group=groups[0]
            sel=selector('prose_block',owner='0000',ordinal=group['ordinal']);selected=c.select(sel)
            witness=verify_old_group([old],c.english.tags,[old['unit_id']],selected,native_containers=c,allow_native_prose=True)['native_labelled_math_prose_anchor']
            self.assertEqual(witness['frozen_anchor']['tag'],'0003')
            self.assertEqual(selected['selector']['parent_tag'],'0000')
            self.assertNotEqual(witness['historical_signature_hash'],witness['native_signature_hash'])
            for fault in ['parent','math','text','label','partial','duplicate']:
                bad=copy.deepcopy(old)
                if fault=='parent':bad['parent_tag']='0000'
                if fault=='math':bad['placeholders']={k:v.replace('x=y.','x=z.') for k,v in bad['placeholders'].items()}
                if fault=='text':bad['source_text']=bad['source_text'].replace('choose','discard')
                if fault=='label':bad['placeholders']={k:v.replace('test-equation-one','test-lemma-one') for k,v in bad['placeholders'].items()}
                if fault=='partial':bad['source_text']=bad['source_text'].replace('Then use <MATH_0003>.','')
                bads=[bad,bad] if fault=='duplicate' else [bad]
                with self.subTest(fault=fault),self.assertRaises(RecordError):
                    verify_old_group(bads,c.english.tags,[bad['unit_id']],selected,native_containers=c,allow_native_prose=True)
            template=candidate_fixture()[2][0];candidate=copy.deepcopy(template)
            ctx=dict(unit_id=old['unit_id'],source_commit=source,prompt_version='fixture',policy_revision='fixture')
            candidate.update(unit_id=old['unit_id'],source_commit=source,source_text_hash=old['source_text_hash'],context=ctx,context_hash=sha256_value(ctx),
                run_id='synthetic-labelled-prose',translation=''.join('<'+n+'>' for n in placeholder_names(old['source_text']))+' synthetic.',
                allowed_english=[],term_occurrences=[],unknown_terms=[],notes=['Synthetic only.'],term_status='CLEAR',stage='TERM_OK',qa_status='PASS',publication_status='CANDIDATE')
            candidate['translation_hash']=sha256_value(candidate['translation'])
            up='translation-data/units/test-equation.jsonl';cp='translation-data/candidates/fixture/test-equation.jsonl'
            save(root,up,[old]);save(root,cp,[candidate]);write(root/'translation-data/runs/synthetic-labelled-prose.json',run_for([candidate],source,'translation','synthetic-labelled-prose'))
            git(root,'init','-q');commit(root)
            plan=dict(derivation_id='synthetic-labelled-prose',created_at='2026-10-14T00:00:00Z',units_file=up,candidates_file=cp,groups=[dict(
                group_id='complete',input_unit_ids=[old['unit_id']],identity_anchor=old['unit_id'],selector=sel,layout='whole',reason='Synthetic complete labelled equation interval.')])
            path=root/'build/plan.json';write(path,plan);output=root/'build/package';manifest=write_container_package(root,harvest,path,output)
            self.assertEqual(manifest['state'],'PREPARED',(output/'diagnostics.json').read_text())
            self.assertEqual(write_container_package(root,harvest,path,output,check=True),manifest)
            record=json.loads((output/'restorations.json').read_text())[0]
            for role,name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                dest=root/record['files'][role]['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((output/name).read_bytes())
            destination=root/f"translation-data/source-container-restorations/{record['restoration_id']}.json";write(destination,record)
            self.assertFalse(load_source_containers(root,harvest)[1])
            record['legacy_boundary_witness']['native_labelled_math_prose_anchor']['frozen_anchor']['native_math_hash']='sha256:'+'0'*64
            write(destination,record);self.assertTrue(load_source_containers(root,harvest)[1])

    def witness(self,c,units,enabled=True):
        return verify_old_group(units,c.english.tags,[units[-1]['unit_id']],
            c.select(selector('paragraph',ordinal=2,owner='0000')),native_containers=c,allow_native_prose=enabled)

    def test_actual_native_anchors_and_complete_frozen_section_anchor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp)); c=Containers(root,harvest)
            with self.assertRaises(RecordError): self.witness(c,units,False)
            anchor=self.witness(c,units)['native_prose_anchor']
            self.assertEqual(anchor['native_before']['selector']['owner_tag'],'0001')
            self.assertEqual(anchor['native_after']['selector']['owner_tag'],'0002')
            self.assertEqual(anchor['frozen_anchor']['input_unit_ids'],['tag:0000:title'])
            self.assertEqual(anchor['historical_signature_hash'],anchor['native_signature_hash'])

    def test_text_math_comments_parent_order_and_real_frozen_anchor_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp)); c=Containers(root,harvest)
            for fault in ['text','math','comment','prefix','parent','source','chapter','duplicate','no-anchor','fake-title','extra-label']:
                bad=copy.deepcopy(units)
                if fault=='text':bad[-1]['source_text']='Changed paragraph with <MATH_0001>.'
                if fault=='math':bad[-1]['placeholders']['MATH_0001']='$z$'
                if fault=='comment':bad[-1]['render']['suffix']+='\n% added comment\n'
                if fault=='prefix':bad[-1]['render']['prefix']='\\medskip\\noindent\n'
                if fault=='parent':bad[-1]['parent_tag']='9999'
                if fault=='source':bad[-1]['source_commit']='0'*40
                if fault=='chapter':bad[-1]['chapter']='other'
                if fault=='duplicate':bad[1]=copy.deepcopy(bad[-1])
                if fault=='no-anchor':bad=bad[1:]
                if fault=='fake-title':bad[0]['source_text']='Other title'
                if fault=='extra-label':bad[0]['render']['suffix']+='\\label{test-lemma-one}'
                with self.subTest(fault=fault),self.assertRaises(RecordError):self.witness(c,bad)

    def test_duplicate_native_text_and_unclassified_math_stay_blocked(self):
        for tail in [LAST+NEXT+LAST, LAST.replace('$y$',r'$\text{unknown words}$')+NEXT]:
            with tempfile.TemporaryDirectory() as tmp:
                root,harvest,units,_,_=fixture(Path(tmp),tail)
                with self.assertRaises(RecordError):self.witness(Containers(root,harvest),units)

    def test_reference_namespace_requires_the_same_real_tag_and_never_changes_math(self):
        tail=LAST.replace('with $y$.',r'with $y$ and \ref{lemma-one}.')+NEXT
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp),tail)
            units[-1]['source_text']='Last paragraph with <MATH_0001> and <REF_0001>.'
            units[-1]['placeholders']['REF_0001']=r'\ref{test-lemma-one}'
            units[-1]=stamp_unit_hashes(units[-1]);c=Containers(root,harvest)
            self.assertIn('native_prose_anchor',self.witness(c,units))
            for reference in [r'\ref{test-lemma-two}',r'\ref{unknown}']:
                bad=copy.deepcopy(units);bad[-1]['placeholders']['REF_0001']=reference
                with self.subTest(reference=reference),self.assertRaises(RecordError):self.witness(c,bad)
        tail=LAST.replace('$y$',r'$y+\ref{lemma-one}$')+NEXT
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp),tail)
            units[-1]['placeholders']['MATH_0001']=r'$y+\ref{test-lemma-one}$'
            with self.assertRaises(RecordError):self.witness(Containers(root,harvest),units)

    def test_initial_noindent_is_recovered_and_old_title_tail_is_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,source=english_fixture(Path(tmp),statement=INTRO+NEXT,proof='')
            title=old_unit(source,'tag:0000:title','section_title','Basics','\\section{',
                '}\\label{test-section-basic}\n\\noindent\n')
            paragraph=old_unit(source,'tag:0000:p001','paragraph','First paragraph with <MATH_0001>.','','\n')
            paragraph['placeholders']={'MATH_0001':'$x$'};paragraph=stamp_unit_hashes(paragraph)
            c=Containers(root,harvest);selected=c.select(selector('paragraph',owner='0000'))
            w=verify_old_group([title,paragraph],c.english.tags,[paragraph['unit_id']],selected,native_containers=c,allow_native_prose=True)['native_prose_anchor']
            self.assertEqual(w['frozen_anchor']['detached_layout'],[r'\noindent'])
            self.assertEqual([r['kind'] for r in w['presentation_repairs']],['initial-noindent'])
            self.assertEqual(w['projected_signature_hash'],w['native_signature_hash'])
            self.assertNotEqual(w['historical_signature_hash'],w['native_signature_hash'])
            bad=copy.deepcopy(title);bad['render']['suffix']+='extra'
            with self.assertRaises(RecordError):verify_old_group([bad,paragraph],c.english.tags,[paragraph['unit_id']],selected,native_containers=c,allow_native_prose=True)

    def test_complete_list_opening_relocation_keeps_the_entire_old_list(self):
        body='\\begin{itemize}\n\\item First.\n\\item Second.\n\\end{itemize}\n'+NEXT
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,source=english_fixture(Path(tmp),statement=body,proof='')
            units=[old_unit(source,'tag:0000:title','section_title','Basics','\\section{','}\\label{test-section-basic}\n\\begin{itemize}\n'),
                   old_unit(source,'tag:0000:item001','list_item','First.','\\item ','\n'),
                   old_unit(source,'tag:0000:item002','list_item','Second.','\\item ','\n\\end{itemize}\n')]
            c=Containers(root,harvest);selected=c.select(selector('prose_block',owner='0000'));ids=[u['unit_id'] for u in units[1:]]
            w=verify_old_group(units,c.english.tags,ids,selected,native_containers=c,allow_native_prose=True)['native_prose_anchor']
            self.assertEqual(w['frozen_anchor']['detached_layout'],[r'\begin{itemize}'])
            self.assertEqual([r['kind'] for r in w['presentation_repairs']],['initial-list-opening'])
            self.assertEqual(w['projected_signature_hash'],w['native_signature_hash'])
            for fault in ['missing','reverse','closing','title-opening']:
                bad=copy.deepcopy(units);badids=ids
                if fault=='missing':bad.pop();badids=ids[:1]
                if fault=='reverse':bad[1:]=bad[:0:-1]
                if fault=='closing':bad[-1]['render']['suffix']='\n'
                if fault=='title-opening':bad[0]['render']['suffix']=bad[0]['render']['suffix'].replace('itemize','enumerate')
                with self.subTest(fault=fault),self.assertRaises(RecordError):verify_old_group(bad,c.english.tags,badids,selected,native_containers=c,allow_native_prose=True)

    def test_paired_prose_quotes_have_explicit_projection_and_math_is_opaque(self):
        tail=LAST.replace('with $y$.',"``with $y$''.")+NEXT
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp),tail)
            units[-1]['source_text']='Last paragraph “with <MATH_0001>”.'
            c=Containers(root,harvest);w=self.witness(c,units)['native_prose_anchor']
            self.assertEqual([r['source'] for r in w['presentation_repairs']],['“','”'])
            self.assertEqual(w['projected_signature_hash'],w['native_signature_hash'])
            self.assertNotEqual(w['historical_signature_hash'],w['native_signature_hash'])
            for text in ['Last paragraph “with <MATH_0001>.','Last paragraph ”with <MATH_0001>“.']:
                bad=copy.deepcopy(units);bad[-1]['source_text']=text
                with self.subTest(text=text),self.assertRaises(RecordError):self.witness(c,bad)
            bad=copy.deepcopy(units);bad[-1]['placeholders']['MATH_0001']='$“y”$'
            with self.assertRaises(RecordError):self.witness(c,bad)

    def test_projection_alternatives_are_included_in_native_uniqueness(self):
        tail=LAST.replace('with $y$.',"``with $y$''.")+NEXT+LAST.replace('with $y$.','“with $y$”.')
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp),tail)
            units[-1]['source_text']='Last paragraph “with <MATH_0001>”.'
            with self.assertRaisesRegex(RecordError,'not unique'):self.witness(Containers(root,harvest),units)

    def test_root_math_wrapping_has_exact_replay_records_and_no_token_changes(self):
        tail=LAST.replace('$y$', '$y +\nz$')+NEXT
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp),tail);c=Containers(root,harvest)
            units[-1]['placeholders']['MATH_0001']='$y + z$'
            w=self.witness(c,units)['native_prose_anchor']
            self.assertEqual(w['presentation_repairs'],[dict(kind='math-root-wrapping',
                signature_index=2,text_offset=4,source=' ',replacement='\n')])
            self.assertEqual(w['projected_signature_hash'],w['native_signature_hash'])
            for math in ['$y - z$','$y +z$','$y +  % comment\nz$','$y \\ z$']:
                bad=copy.deepcopy(units);bad[-1]['placeholders']['MATH_0001']=math
                with self.subTest(math=math),self.assertRaises(RecordError):self.witness(c,bad)

    def test_math_parameter_comments_literals_and_control_spaces_are_opaque(self):
        from stacks_zh.source_native_prose_boundaries import _math_wrapping_changes
        for a,b in [(r'$\text{id x}$',r'$\text{id  x}$'),
                    ('$x_{a b}$','$x_{a\nb}$'),
                    ('$x %one\ny$','$x %two\ny$'),
                    (r'$x\ y$',r'$x\  y$'),
                    ('$\\foo x + y$','$\\foo x +\ny$'),
                    (r'$\verb|a b|$',r'$\verb|a  b|$')]:
            with self.subTest(a=a,b=b):self.assertIsNone(_math_wrapping_changes(a,b))

    def test_complete_emphasis_and_prose_typography_have_explicit_evidence(self):
        tail=LAST.replace('with $y$.',r"with {\it $y$}---a value.")+NEXT
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp),tail);c=Containers(root,harvest)
            units[-1]['source_text']='Last paragraph with <EMPHOPEN_0001><MATH_0001><EMPHCLOSE_0001>—a value..'
            units[-1]['placeholders'].update(EMPHOPEN_0001=r'\emph{',EMPHCLOSE_0001='}')
            w=self.witness(c,units)['native_prose_anchor']
            self.assertEqual([x['kind'] for x in w['presentation_repairs']],
                ['emphasis-wrapper','prose-em-dash','duplicated-terminal-period'])
            for fault in ['ellipsis','wrapper','close','text','math']:
                bad=copy.deepcopy(units)
                if fault=='ellipsis':bad[-1]['source_text']+='.'
                if fault=='wrapper':bad[-1]['placeholders']['EMPHOPEN_0001']=r'\textbf{'
                if fault=='close':bad[-1]['placeholders']['EMPHCLOSE_0001']=''
                if fault=='text':bad[-1]['source_text']=bad[-1]['source_text'].replace('value','quantity')
                if fault=='math':bad[-1]['placeholders']['MATH_0001']='$z$'
                with self.subTest(fault=fault),self.assertRaises(RecordError):self.witness(c,bad)

    def test_title_tail_cannot_be_borrowed_across_an_intervening_container(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,_,_=fixture(Path(tmp))
            units[0]['render']['suffix']+='\\noindent\n';units[-1]['render']['prefix']=''
            with self.assertRaises(RecordError):self.witness(Containers(root,harvest),units)

    def test_package_and_origin_replay_reject_schema_valid_changed_witness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,units,plan,output=fixture(Path(tmp))
            manifest=write_container_package(root,harvest,plan,output)
            self.assertEqual(manifest['state'],'PREPARED')
            before={p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()}
            self.assertEqual(write_container_package(root,harvest,plan,output,check=True),manifest)
            self.assertEqual(before,{p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()})
            records=json.loads((output/'restorations.json').read_text())
            for record in records:
                for role,name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                    destination=root/record['files'][role]['path'];destination.parent.mkdir(parents=True,exist_ok=True)
                    destination.write_bytes((output/name).read_bytes())
                write(root/f"translation-data/source-container-restorations/{record['restoration_id']}.json",record)
            target=next(r for r in records if r['tool']['version']=='source-container-v13')
            self.assertFalse(validate_named_schema(target,'source-container-restoration.schema.json','synthetic'))
            self.assertFalse(load_source_containers(root,harvest)[1])
            path=root/f"translation-data/source-container-restorations/{target['restoration_id']}.json"
            for key in ['historical_signature_hash','native_signature_hash','projected_signature_hash']:
                bad=copy.deepcopy(target);bad['legacy_boundary_witness']['native_prose_anchor'][key]='sha256:'+'0'*64
                self.assertFalse(validate_named_schema(bad,'source-container-restoration.schema.json','synthetic tamper'))
                write(path,bad)
                self.assertTrue(any('legacy boundary witness differs' in e for e in load_source_containers(root,harvest)[1]))
            bad=copy.deepcopy(target)
            bad['legacy_boundary_witness']['native_prose_anchor']['presentation_repairs']=[dict(
                kind='initial-noindent',signature_index=0,text_offset=0,source='',replacement=r'\noindent')]
            self.assertFalse(validate_named_schema(bad,'source-container-restoration.schema.json','synthetic tamper'))
            write(path,bad)
            self.assertTrue(any('legacy boundary witness differs' in e for e in load_source_containers(root,harvest)[1]))
            write(path,target);self.assertFalse(load_source_containers(root,harvest)[1])
