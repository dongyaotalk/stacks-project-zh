"""Real labelled heading scopes and versioned complete legacy ownership."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_source_containers import fixture as english_fixture, git, old_unit
from stacks_zh.extraction import Policy, Scanner, chapter_inventory
from stacks_zh.records import RecordError
from stacks_zh.source_containers import Containers, lower_container, verify_old_group
from stacks_zh.source_reextractions import source_tex

ROOT=Path(__file__).resolve().parents[1]
RAW=(ROOT/'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0]
TAGS={'test-section-phantom':'0005','test-section-basic':'0000','test-subsection-one':'0001','test-subsubsection-two':'0002',
      'test-subsection-three':'0003','test-section-next':'0004'}
BODY=('\\section{Basics}\\label{section-basic}\n\\noindent Root.\n\n'
      '\\subsection{First}\\label{subsection-one}\n\\noindent First body.\n\n'
      '\\subsubsection{Deep}\\label{subsubsection-two}\n\\noindent Deep body.\n\n'
      '\\subsection{Second}\\label{subsection-three}\n\\noindent Second body.\n\n'
      '\\section{Next}\\label{section-next}\n\\noindent Next body.\n')


def inventory(body=BODY, enabled=True):
    raw=('\\begin{document}\n'+body+'\\end{document}\n').encode()
    rows,parts,errors=chapter_inventory('test',raw,'a'*40,TAGS,Policy(RAW),hierarchical_prose=enabled)
    return raw,rows,parts,errors


def fixture(base):
    root,harvest,_=english_fixture(base,statement='',proof='')
    (harvest/'test.tex').write_text('\\begin{document}\n'+BODY+'\\end{document}\n')
    (harvest/'tags/tags').write_text(''.join(tag+','+label+'\n' for label,tag in TAGS.items()))
    git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','independent heading tree')
    source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
    return root,harvest,source


def coordinate(kind='prose_block',owner='0001',parent='0000'):
    return dict(file='test.tex',owner_tag=owner,owner_label=next(k for k,v in TAGS.items() if v==owner),
                parent_tag=parent,kind=kind,ordinal=1)


def legacy(source):
    title=old_unit(source,'tag:0001:title','section_title','First','\\subsection{',
                   '}\\label{test-subsection-one}\n\\noindent\n')
    body=old_unit(source,'tag:0001:p001','paragraph','First body.','','\n\n')
    for u in [title,body]:u['parent_tag']='0001'
    return [title,body]


class HeadingHierarchyTests(unittest.TestCase):
    def test_zero_argument_locked_commands_do_not_consume_following_prose(self):
        from stacks_zh.source_alignment import canonical_tokens,_labels
        for source in [r'Copyright \copyright 2002.',r'{\bf\large Preamble}']:
            scanner=Scanner(source,Policy(RAW));text,protected,errors=scanner.protect(0,len(source))
            self.assertFalse(errors)
            self.assertEqual(source,source_tex(dict(source_text=text,placeholders=protected,render={'prefix':'','suffix':''})))
            self.assertTrue('2002.' in text or 'Preamble' in text)
            tokens=canonical_tokens(source,'test',TAGS,Policy(RAW))
            self.assertTrue(any(t.key[0]=='text' and t.key[1] in {'2002','.','Preamble'} for t in tokens))
            self.assertEqual(_labels(source+r'\label{section-basic}','test',TAGS,Policy(RAW)),{'0000'})
        source=r'Copyright \unknown 2002.';scanner=Scanner(source,Policy(RAW))
        self.assertTrue(scanner.protect(0,len(source))[2])

    def test_complete_phantom_header_center_and_preamble_origin_replay(self):
        from test_derivations import fixture as candidate_fixture
        from test_group_derivations import commit,run_for,save,write
        from stacks_zh.records import placeholder_names,sha256_value
        from stacks_zh.source_containers import write_container_package,load_source_containers
        notice='\\begin{center}\nCopyright \\copyright 2002.\n\\bigskip\nNotice.\n\\end{center}\n'
        heading='\\begin{center}\n{\\bf\\large Preamble}\n\\end{center}\n'
        paragraph='A complete preamble.\n\n'
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_=fixture(Path(tmp));header='\\title{Book}\\maketitle\\phantomsection\\label{section-phantom}\n'
            (harvest/'test.tex').write_text('\\begin{document}\n'+header+notice+heading+paragraph+BODY+'\\end{document}\n')
            git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','independent complete front matter')
            source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
            title=old_unit(source,'tag:0005:title','chapter_title','Book','\\chapter{','}\\phantomsection\\label{test-section-phantom}\n')
            units=[title]
            for i,(kind,fragment) in enumerate([('notice',notice),('heading',heading),('paragraph',paragraph)]):
                scanner=Scanner(fragment,Policy(RAW));text,protected,errors=scanner.protect(0,len(fragment));self.assertFalse(errors)
                u=old_unit(source,'tag:0005:p00'+str(i),kind,text);u['placeholders']=protected;units.append(u)
            from stacks_zh.records import stamp_unit_hashes
            for u in units:u['parent_tag']='0005'
            units=[stamp_unit_hashes(u) for u in units]
            c=Containers(root,harvest);sel=coordinate('prose_block','0005','0005');selected=c.select(sel);ids=[u['unit_id'] for u in units[1:]]
            self.assertEqual(selected['fragment'],notice+heading+paragraph)
            witness=verify_old_group(units,c.english.tags,ids,selected,native_containers=c,allow_native_prose=True)['native_prose_anchor']
            self.assertIn('document_header',witness['frozen_anchor'])
            for fault in ['title','label','member','owner','body']:
                bad=copy.deepcopy(units)
                if fault=='title':bad[0]['source_text']='Other'
                if fault=='label':bad[0]['render']['suffix']='}\\label{test-section-basic}'
                if fault=='member':bad.pop(1)
                if fault=='owner':bad[-1]['parent_tag']='0000'
                if fault=='body':bad[-1]['source_text']='Changed body.'
                with self.subTest(fault=fault),self.assertRaises(RecordError):
                    verify_old_group(bad,c.english.tags,[u['unit_id'] for u in bad[1:]],selected,native_containers=c,allow_native_prose=True)
            template=candidate_fixture()[2][0];candidates=[]
            for u in units:
                candidate=copy.deepcopy(template);ctx=dict(unit_id=u['unit_id'],source_commit=source,prompt_version='fixture',policy_revision='fixture')
                candidate.update(unit_id=u['unit_id'],source_commit=source,source_text_hash=u['source_text_hash'],context=ctx,context_hash=sha256_value(ctx),
                    run_id='synthetic-front-matter',translation=''.join('<'+n+'>' for n in placeholder_names(u['source_text']))+' synthetic.',
                    allowed_english=[],term_occurrences=[],unknown_terms=[],notes=['Synthetic only.'],term_status='CLEAR',stage='TERM_OK',qa_status='PASS',publication_status='CANDIDATE')
                candidate['translation_hash']=sha256_value(candidate['translation']);candidates.append(candidate)
            up='translation-data/units/test-front.jsonl';cp='translation-data/candidates/fixture/test-front.jsonl'
            save(root,up,units);save(root,cp,candidates);write(root/'translation-data/runs/synthetic-front-matter.json',run_for(candidates,source,'translation','synthetic-front-matter'))
            git(root,'init','-q');commit(root)
            plan=dict(derivation_id='synthetic-front-matter',created_at='2026-10-14T00:00:00Z',units_file=up,candidates_file=cp,groups=[
                dict(group_id='title',input_unit_ids=[title['unit_id']],identity_anchor=title['unit_id'],selector=coordinate('title_title','0005','0005'),layout='whole',reason='Synthetic complete front header.'),
                dict(group_id='preamble',input_unit_ids=ids,identity_anchor=ids[0],selector=sel,layout='whole',reason='Synthetic whole phantom preamble.')])
            path=root/'build/plan.json';write(path,plan);output=root/'build/package';manifest=write_container_package(root,harvest,path,output)
            self.assertEqual(manifest['state'],'PREPARED',(output/'diagnostics.json').read_text())
            self.assertEqual(write_container_package(root,harvest,path,output,check=True),manifest)
            records=json.loads((output/'restorations.json').read_text())
            for record in records:
                for role,name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                    dest=root/record['files'][role]['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((output/name).read_bytes())
                write(root/f"translation-data/source-container-restorations/{record['restoration_id']}.json",record)
            self.assertFalse(load_source_containers(root,harvest)[1])
            target=next(r for r in records if 'native_prose_anchor' in r.get('legacy_boundary_witness', {}))
            self.assertEqual(target['tool']['version'],'source-container-v13')
            target['legacy_boundary_witness']['native_prose_anchor']['frozen_anchor']['document_header']['historical_title_signature_hash']='sha256:'+'0'*64
            write(root/f"translation-data/source-container-restorations/{target['restoration_id']}.json",target)
            self.assertTrue(load_source_containers(root,harvest)[1])

    def test_real_deepest_owner_and_real_section_parent_with_exact_byte_roundtrip(self):
        raw,rows,parts,errors=inventory();self.assertFalse(errors)
        self.assertEqual([(r['owner_tag'],r['parent_tag']) for r in rows if r['unit']['node_kind']=='paragraph'],
                         [('0000','0000'),('0001','0000'),('0002','0000'),('0003','0000'),('0004','0004')])
        by_id={r['inventory_id']:r['unit'] for r in rows}
        rebuilt=''.join(source_tex(by_id[p['inventory_id']]) if p['kind']=='unit' else p['source'] for p in parts)
        self.assertEqual(rebuilt.encode(),raw)
        _,old,_,_=inventory(enabled=False)
        self.assertEqual([r['owner_tag'] for r in old if r['unit']['node_kind']=='paragraph'],['0000']*4+['0004'])

    def test_unlabelled_sibling_clears_old_deeper_owner_and_literal_labels_are_not_anchors(self):
        body=BODY.replace('\\subsection{Second}\\label{subsection-three}',
             '\\begin{verbatim}\n\\subsection{Fake}\\label{subsection-three}\n\\end{verbatim}\n\\subsection{Unlabelled}')
        _,rows,_,errors=inventory(body)
        last=next(r for r in rows if 'Second body.' in r['unit']['source_text'])
        self.assertEqual(last['owner_tag'],'0000')
        self.assertTrue(any(e['kind']=='ownership' for e in errors))
        self.assertFalse(any(r['owner_tag']=='0003' for r in rows))

    def test_new_subsection_lowering_preserves_kind_owner_parent_and_complete_prose(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,source=fixture(Path(tmp));c=Containers(root,harvest)
            heading=c.select(coordinate('subsection_title'));out=lower_container(heading,c.policy)[0]
            self.assertEqual((out['unit_id'],out['node_kind'],out['parent_tag']),('tag:0001:title','subsection_title','0000'))
            self.assertEqual(source_tex(out),heading['fragment'])
            selected=c.select(coordinate());units=legacy(source)
            w=verify_old_group(units,c.english.tags,[units[1]['unit_id']],selected,native_containers=c,allow_native_prose=True)
            self.assertEqual(w['native_prose_anchor']['frozen_anchor']['selector']['kind'],'subsection_title')
            self.assertEqual(w['native_prose_anchor']['frozen_anchor']['detached_layout'],[r'\noindent'])
            self.assertEqual(source_tex(lower_container(selected,c.policy)[0]),selected['fragment'])
            with self.assertRaises(RecordError):Containers(root,harvest,hierarchical_prose=False).select(coordinate())

    def test_misreported_old_kind_requires_new_evidence_and_original_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,source=fixture(Path(tmp));c=Containers(root,harvest);units=legacy(source)
            heading=c.select(coordinate('subsection_title'))
            with self.assertRaises(RecordError):verify_old_group(units,c.english.tags,[units[0]['unit_id']],heading,native_containers=c)
            w=verify_old_group(units,c.english.tags,[units[0]['unit_id']],heading,native_containers=c,allow_native_prose=True)['native_heading_anchor']
            self.assertEqual(w['historical_node_kind'],'section_title')
            self.assertEqual(w['historical_parent_tag'],'0001')
            self.assertEqual(w['native_selector']['parent_tag'],'0000')
            for fault in ['wrapper','label','parent','title','tail']:
                bad=copy.deepcopy(units)
                if fault=='wrapper':bad[0]['render']['prefix']='\\section{'
                if fault=='label':bad[0]['render']['suffix']=bad[0]['render']['suffix'].replace('test-subsection-one','test-subsection-three')
                if fault=='parent':bad[0]['parent_tag']='9999'
                if fault=='title':bad[0]['source_text']='Changed'
                if fault=='tail':bad[0]['render']['suffix']+='extra'
                with self.subTest(fault=fault),self.assertRaises(RecordError):verify_old_group(bad,c.english.tags,[bad[0]['unit_id']],heading,native_containers=c,allow_native_prose=True)

    def test_literal_copyright_header_has_real_phantom_label_and_versioned_witness(self):
        literal='\\begin{verbatim}\nCopyright 2025.\n\\label{section-phantom}\n\\section{Fake}\n\\end{verbatim}\n'
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_=fixture(Path(tmp));raw=(harvest/'test.tex').read_text()
            header='\\title{Book}\n\\maketitle\n\\phantomsection\\label{section-phantom}\n'+literal+'\\tableofcontents\n'
            (harvest/'test.tex').write_text(raw.replace('\\begin{document}\n','\\begin{document}\n'+header))
            git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','inert copyright header')
            source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
            c=Containers(root,harvest);sel=coordinate('title_title',owner='0005',parent='0005');selected=c.select(sel)
            self.assertIn(literal,selected['fragment']);self.assertEqual(len(selected['_document_header_literals']),1)
            out=lower_container(selected,c.policy)[0];self.assertEqual(source_tex(out),selected['fragment'])
            unit=old_unit(source,'tag:0005:title','chapter_title','Book','\\chapter{','}\\phantomsection\\label{test-section-phantom}\n');unit['parent_tag']='0005'
            witness=verify_old_group([unit],c.english.tags,[unit['unit_id']],selected,native_containers=c,allow_native_prose=True)
            self.assertEqual(witness['native_document_header_anchor']['literal_environments'],selected['_document_header_literals'])
            with self.assertRaises(RecordError):Containers(root,harvest,hierarchical_prose=False).select(sel)
            bad=copy.deepcopy(unit);bad['source_text']='Other title'
            with self.assertRaises(RecordError):verify_old_group([bad],c.english.tags,[bad['unit_id']],selected,native_containers=c,allow_native_prose=True)

    def test_only_real_contiguous_footer_infrastructure_is_excluded_from_prose(self):
        literal='\\begin{verbatim}\n\\input{chapters}\n\\end{verbatim}\n'
        tail='\\input{chapters}\n\\bibliography{my}\n\\bibliographystyle{amsalpha}\n'
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_=fixture(Path(tmp));body='\\section{Basics}\\label{section-basic}\n\\noindent Body.\n\n'+literal+tail
            (harvest/'test.tex').write_text('\\begin{document}\n'+body+'\\end{document}\n')
            git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','footer and literal')
            source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
            c=Containers(root,harvest);selected=c.select(coordinate(owner='0000'))
            self.assertIn(literal,selected['fragment']);self.assertNotIn('\\bibliography',selected['fragment'])
            self.assertEqual(selected['fragment'].count('\\input{chapters}'),1)
            with self.assertRaises(RecordError):Containers(root,harvest,hierarchical_prose=False).select(coordinate(owner='0000'))
        for extra in ['\\input{unknown}\n','\\bibliography{my}\nUnexpected body.\n']:
            with tempfile.TemporaryDirectory() as tmp:
                root,harvest,_=fixture(Path(tmp));(harvest/'test.tex').write_text('\\begin{document}\n\\section{Basics}\\label{section-basic}\n\\noindent Body.\n\n'+extra+'\\end{document}\n')
                git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','unsupported footer')
                source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
                with self.subTest(extra=extra),self.assertRaises(RecordError):Containers(root,harvest).select(coordinate(owner='0000'))

    def test_full_header_heading_body_package_and_origin_replay_reject_changed_witnesses(self):
        from test_derivations import fixture as candidate_fixture
        from test_group_derivations import commit, run_for, save, write
        from stacks_zh.records import placeholder_names,sha256_value
        from stacks_zh.source_containers import write_container_package,load_source_containers
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_=fixture(Path(tmp));raw=(harvest/'test.tex').read_text()
            header='\\title{Book}\n\\maketitle\\phantomsection\\label{section-phantom}\n\\begin{verbatim}\nCopyright 2025.\n\\end{verbatim}\n\\tableofcontents\n'
            (harvest/'test.tex').write_text(raw.replace('\\begin{document}\n','\\begin{document}\n'+header))
            git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','complete immutable header')
            source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
            title=old_unit(source,'tag:0005:title','chapter_title','Book','\\chapter{','}\\phantomsection\\label{test-section-phantom}\n');title['parent_tag']='0005'
            units=[title,*legacy(source)];template=candidate_fixture()[2][0];candidates=[]
            for u in units:
                c=copy.deepcopy(template);ctx=dict(unit_id=u['unit_id'],source_commit=source,prompt_version='fixture',policy_revision='fixture')
                c.update(unit_id=u['unit_id'],source_commit=source,source_text_hash=u['source_text_hash'],context=ctx,context_hash=sha256_value(ctx),
                         run_id='synthetic-hierarchy',translation=''.join('<'+n+'>' for n in placeholder_names(u['source_text']))+' synthetic.',
                         allowed_english=[],term_occurrences=[],unknown_terms=[],notes=['Synthetic only.'],term_status='CLEAR',stage='TERM_OK',qa_status='PASS',publication_status='CANDIDATE')
                c['translation_hash']=sha256_value(c['translation']);candidates.append(c)
            up='translation-data/units/test-heading.jsonl';cp='translation-data/candidates/fixture/test-heading.jsonl'
            save(root,up,units);save(root,cp,candidates);write(root/'translation-data/runs/synthetic-hierarchy.json',run_for(candidates,source,'translation','synthetic-hierarchy'))
            git(root,'init','-q');commit(root)
            selectors=[coordinate('title_title','0005','0005'),coordinate('subsection_title'),coordinate()]
            plan=dict(derivation_id='synthetic-hierarchy',created_at='2026-10-14T00:00:00Z',units_file=up,candidates_file=cp,
                groups=[dict(group_id='node-'+str(i),input_unit_ids=[u['unit_id']],identity_anchor=u['unit_id'],selector=sel,layout='whole',reason='Synthetic complete heading scope only.') for i,(u,sel) in enumerate(zip(units,selectors))])
            path=root/'build/plan.json';write(path,plan);out=root/'build/package';manifest=write_container_package(root,harvest,path,out)
            self.assertEqual(manifest['state'],'PREPARED');self.assertEqual(write_container_package(root,harvest,path,out,check=True),manifest)
            records=json.loads((out/'restorations.json').read_text());self.assertEqual([r['tool']['version'] for r in records],['source-container-v13']*3)
            for record in records:
                for role,name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                    dest=root/record['files'][role]['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((out/name).read_bytes())
                write(root/f"translation-data/source-container-restorations/{record['restoration_id']}.json",record)
            self.assertFalse(load_source_containers(root,harvest)[1])
            for record in records:
                destination=root/f"translation-data/source-container-restorations/{record['restoration_id']}.json"
                bad=copy.deepcopy(record);key=next(iter(bad['legacy_boundary_witness']));w=bad['legacy_boundary_witness'][key]
                if key=='native_document_header_anchor':w['literal_environments'][0]['source_hash']='sha256:'+'0'*64
                elif key=='native_heading_anchor':w['following_body_prefix_hash']='sha256:'+'0'*64
                else:w['projected_signature_hash']='sha256:'+'0'*64
                write(destination,bad)
                with self.subTest(kind=key):self.assertTrue(load_source_containers(root,harvest)[1])
                write(destination,record)

    def test_complete_quote_and_detached_display_members_keep_every_node(self):
        body='\\begin{quote}\nA quoted sentence.\n\\end{quote}\n\\[x=y\\]\n\\section{Next}\\label{section-next}\n'
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,_=fixture(Path(tmp));(harvest/'test.tex').write_text('\\begin{document}\n\\section{Basics}\\label{section-basic}\n'+body+'\\end{document}\n')
            git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','quote and math nodes')
            source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
            units=[old_unit(source,'tag:0000:title','section_title','Basics','\\section{','}\\label{test-section-basic}\n'),
                   old_unit(source,'tag:0000:quote001','quote','A quoted sentence.','\\begin{quote}\n','\n\\end{quote}\n'),
                   old_unit(source,'tag:0000:display001','display_math','<MATH_0001>','','\n')]
            units[-1]['placeholders']={'MATH_0001':r'\[x=y\]'}
            from stacks_zh.records import stamp_unit_hashes
            units=[stamp_unit_hashes(u) for u in units]
            c=Containers(root,harvest);selected=c.select(coordinate(owner='0000'));ids=[u['unit_id'] for u in units[1:]]
            self.assertIn('native_prose_anchor',verify_old_group(units,c.english.tags,ids,selected,native_containers=c,allow_native_prose=True))
            for fault in ['quote','math','unknown-kind']:
                bad=copy.deepcopy(units)
                if fault=='quote':bad[1]['source_text']='Changed quote.'
                if fault=='math':bad[-1]['placeholders']['MATH_0001']=r'\[x=z\]'
                if fault=='unknown-kind':bad[1]['node_kind']='unknown_environment'
                with self.subTest(fault=fault),self.assertRaises(RecordError):verify_old_group(bad,c.english.tags,ids,selected,native_containers=c,allow_native_prose=True)
