"""Independent literal frames and synthetic Git, never real model output."""
import copy
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from test_source_containers import fixture as english_fixture, selector, git
from test_group_derivations import fixture as history_fixture, read, write
from stacks_zh.extraction import Policy, Scanner
from stacks_zh.math_text import find_slots, validate_regions, validate_translation, complete_math_nodes
from stacks_zh.records import RecordError, stamp_unit_hashes, term_display_text, restore_placeholders, write_jsonl, sha256_value
from stacks_zh.schema_validation import validate_named_schema, validate_repository_schemas
from stacks_zh.source_containers import Containers, lower_container, load_source_containers
from stacks_zh.source_reextractions import source_tex
from stacks_zh.source_terms import source_projection, source_inventory, validate_source_terms
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.workflow import render_batch

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT/'config/macro-policy.yml').read_text().split('\ntranslatable_math_text:')[0]
BASE = re.sub(r'(?ms)^locked_math_text_notations:\n.*?(?=^[A-Za-z_][A-Za-z0-9_-]*:|\Z)', '', BASE)
# Independently transcribed complete expected English/Git strings, not imported
# from the classifier and not synthesized by a scanner or frame helper.
UNRAMIFIED = r"""$$
R \to S\text{ is unramified at }\mathfrak q
\Leftrightarrow
\mathfrak pS_{\mathfrak q} = \mathfrak q S_{\mathfrak q}
\text{ and }
\kappa(\mathfrak p) \subset \kappa(\mathfrak q)\text{ finite separable}
$$"""
SECTIONS = r"""$$
\text{sections of }f
\leftrightarrow
\left\{
\begin{matrix}
\text{connected components }X'\text{ of }X\text{ such that}\\
\text{the induced map }X' \to Y\text{ is an isomorphism}
\end{matrix}
\right\}
$$"""
THICKENING = r"""$$
\{
\text{schemes }X\text{ \'etale over }S
\}
\leftrightarrow
\{
\text{schemes }X_0\text{ \'etale over }S_0
\}
$$"""
DESCENT = r"""\begin{equation}
\label{equation-descent-etale}
\text{schemes }U\text{ \'etale over }S \longrightarrow
\begin{matrix}
\text{descent data }(V, \varphi)\text{ relative to }X/S \\
\text{ with }V\text{ \'etale over }X
\end{matrix}
\end{equation}"""
EFFECTIVE = r"""$$
\begin{matrix}
\text{schemes quasi-compact,}\\
\text{separated, \'etale over }S
\end{matrix}
\longrightarrow
\begin{matrix}
\text{descent data }(V, \varphi)\text{ relative to }X/S\text{ with}\\
V\text{ quasi-compact, separated, \'etale over }X
\end{matrix}
$$"""
FRAMES = [UNRAMIFIED, SECTIONS, THICKENING, DESCENT, EFFECTIVE]
ORDINARY = [
    (' is unramified at ', 'root-phrase'), (' and ', 'root-phrase'),
    (' finite separable', 'etale-unramified-condition'),
    ('sections of ', 'etale-sections-correspondence'),
    ('connected components ', 'etale-sections-correspondence'),
    (' of ', 'etale-sections-correspondence'), (' such that', 'etale-sections-correspondence'),
    ('the induced map ', 'etale-sections-correspondence'),
    (' is an isomorphism', 'etale-sections-correspondence'),
    ('schemes ', 'etale-scheme-diagrams'), ('descent data ', 'etale-scheme-diagrams'),
    (' relative to ', 'etale-scheme-diagrams'), (' with ', 'etale-scheme-diagrams'),
    (' with', 'etale-scheme-diagrams'), ('schemes quasi-compact,', 'etale-scheme-diagrams'),
]
COMPONENTS = [(r" \'etale over ", [' ', 'tale over ']),
    (r"separated, \'etale over ", ['separated, ', 'tale over ']),
    (r" quasi-compact, separated, \'etale over ", [' quasi-compact, separated, ', 'tale over '])]


def policy_text():
    text = BASE+'\ntranslatable_math_text:\n'
    for i,(literal,role) in enumerate(ORDINARY):
        text += (f'  source-{i}:\n    literal: {json.dumps(literal)}\n'
            f'    command: "text"\n    usage: "{role}"\n'
            '    source_label: "test-lemma-one"\n    witness_kind: "proof"\n    witness_ordinal: 1\n')
    text += 'translatable_math_text_components:\n'
    for i,(literal,components) in enumerate(COMPONENTS):
        text += (f'  accent-{i}:\n    literal: {json.dumps(literal)}\n'
            '    command: "text"\n    usage: "etale-scheme-component"\n'
            f'    components: {json.dumps(components)}\n    separator: "\\\\\'e"\n'
            '    source_label: "test-lemma-one"\n    witness_kind: "proof"\n    witness_ordinal: 1\n')
    return text


PROOF = '\\begin{proof}\nCafé δ.\n'+'\n'.join(FRAMES)+'\n\\end{proof}'


def fixture(base, *, policy=None, proof=PROOF):
    root,harvest,_ = english_fixture(base,proof=proof)
    (root/'config/macro-policy.yml').write_text(policy or policy_text())
    native = Containers(root,harvest)
    selected = native.select(selector())
    unit = lower_container(selected,native.policy)[0]
    return root,harvest,native,selected,unit


def synthetic_fields(unit):
    """Literal test output scaffolding, never used for a production candidate."""
    if not unit.get('math_text_regions'):
        tokens=re.findall(r'<[A-Z][A-Z0-9]*_[0-9]{4}>',unit['source_text'])
        return dict(translation=''.join(tokens)+'合成测试。'+re.search(r'\s*$',unit['source_text'])[0],
            allowed_english=[],term_occurrences=[],unknown_terms=[],term_status='CLEAR',
            notes=['Literal synthetic fixture; no actual model generation.'])
    text=unit['source_text'];spans=[];terms=[]
    for region in unit['math_text_regions']:
        for slot in region['slots']:
            a,b=('<'+x+'>' for x in slot['boundary_placeholders'])
            start=text.index(a)+len(a);end=text.index(b,start)
            component=slot.get('parameter_components')
            if component:
                target='平展（' if component['component_index']==1 else 'tale）合成'
                if component['component_index']==1:terms.append(dict(source_term='étale',target_term='平展'))
            else:target='合成'
            spans.append((start,end,target))
    for start,end,target in sorted(spans,reverse=True):text=text[:start]+target+text[end:]
    text=text.replace('Café δ.','合成测试。')
    return dict(translation=text,allowed_english=[],term_occurrences=terms,
        unknown_terms=[dict(**t,context='Synthetic pending term, never approved.') for t in terms],
        term_status='DECISION_REQUIRED' if terms else 'CLEAR',
        notes=['Literal synthetic fixture; no actual model generation or approval.'])


class EtaleMathTextTests(unittest.TestCase):
    def test_complete_independent_frames_have_exact_leaf_counts(self):
        rules=Policy(policy_text()).math_text_rules
        self.assertEqual([len(find_slots(frame,rules)) for frame in FRAMES],[3,6,6,8,8])
        self.assertEqual(find_slots(SECTIONS,Policy(BASE).math_text_rules),[])

    def test_only_the_exact_complete_math_frames_authorize_new_positions(self):
        rules=Policy(policy_text()).math_text_rules
        variants=[SECTIONS.replace("X'",'Z',1),SECTIONS.replace(r'\leftrightarrow',r'\to'),
            'x'+SECTIONS,SECTIONS+'x',SECTIONS.replace(r'\begin{matrix}',r'\begin{aligned}'),
            SECTIONS.replace(r'\right\}',r'\right\} + 1'),
            SECTIONS.replace(r"X'\text{ of }",r"X' + \foo\text{ of }"),
            SECTIONS.replace("f\n", "f% hidden\n",1),SECTIONS.replace('X\'','X\' ',1),
            THICKENING.replace('X_0','X_1'),DESCENT.replace('equation-descent-etale','other-label'),
            DESCENT.replace(r'\longrightarrow',r'\longleftarrow'),
            EFFECTIVE.replace(r'\varphi',r'\psi'),EFFECTIVE.replace(r'X/S',r'Y/S'),
            EFFECTIVE.replace('$$\n', '$\n',1)]
        for value in variants:
            with self.subTest(source=value):
                try:slots=find_slots(value,rules)
                except ValueError:slots=[]
                self.assertEqual([s for s in slots if s['usage'].startswith('etale-')],[])

    def test_contexts_inherit_only_four_explicit_old_literal_role_pairs(self):
        text=policy_text()
        mapping={8:'root-phrase',6:'descent-sheaf-set-matrices',
                 10:'descent-sheaf-set-matrices',11:'descent-data-matrices'}
        for index,role in mapping.items():
            literal=ORDINARY[index][0]
            text=text.replace(f'literal: {json.dumps(literal)}\n    command: "text"\n    usage: "{ORDINARY[index][1]}"',
                              f'literal: {json.dumps(literal)}\n    command: "text"\n    usage: "{role}"')
        text+='translatable_math_text_contexts:\n'
        for i in mapping:
            role='etale-sections-correspondence' if i in {6,8} else 'etale-scheme-diagrams'
            text+=(f'  finite-context-{i}:\n    base_rule: "source-{i}"\n    usage: "{role}"\n'
                '    source_label: "test-lemma-one"\n    witness_kind: "proof"\n    witness_ordinal: 1\n')
        rules=Policy(text).math_text_rules
        self.assertEqual([len(find_slots(f,rules)) for f in [SECTIONS,DESCENT,EFFECTIVE]],[6,8,8])
        for before,after in [('base_rule: "source-8"','base_rule: "source-0"'),
                ('base_rule: "source-8"','base_rule: "finite-context-8"'),
                ('base_rule: "source-10"','base_rule: "accent-0"')]:
            with self.subTest(after=after),self.assertRaises(RecordError):Policy(text.replace(before,after))

    def test_component_registry_does_not_generalize_literal_or_whitespace(self):
        for before,after in [('"etale-scheme-component"','"indexed-component-description"'),
                ('[" ", "tale over "]','["", "tale over "]'),
                ('"schemes quasi-compact,"','"other, punctuation"')]:
            with self.subTest(after=after),self.assertRaises(RecordError):Policy(policy_text().replace(before,after))
        value=THICKENING.replace(r" \'etale over ",r"\'etale over ")
        self.assertEqual([s for s in find_slots(value,Policy(policy_text()).math_text_rules)
                          if s['usage']=='etale-scheme-component'],[])

    def test_locked_git_lowering_utf8_schema_source_and_blank_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,_,_,unit=fixture(Path(tmp))
            self.assertEqual(unit['schema_version'],3)
            self.assertEqual(validate_named_schema(unit,'unit.schema.json','synthetic'),[])
            self.assertEqual(validate_regions(unit),[])
            self.assertEqual(source_tex(unit),PROOF)
            self.assertEqual(complete_math_nodes(unit),FRAMES)
            self.assertEqual([len(r['slots']) for r in unit['math_text_regions']],[3,6,6,8,8])
            self.assertEqual(sum(s['source']==' ' for r in unit['math_text_regions'] for s in r['slots']),4)
            for r in unit['math_text_regions']:
                for s in r['slots']:
                    a=s['slot_byte_span'];self.assertEqual(r['source'].encode()[a['start']:a['end']],s['source'].encode())
            translated=synthetic_fields(unit)['translation']
            self.assertEqual(validate_translation(unit,translated),[])
            self.assertEqual(term_display_text(translated,unit['placeholders'],unit=unit).count('平展（étale）'),6)

    def test_every_verified_accent_is_visible_and_pending_term_coverage_is_real(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,_,_,unit=fixture(Path(tmp))
            catalog=dict(terms=[dict(id='etale',forms=['étale'],chapters=[],evidence=[])],nonmathematical_declarations={})
            self.assertEqual(source_projection(unit)[0].count('étale'),6)
            self.assertEqual(len(source_inventory(unit,catalog)['occurrences']),6)
            candidate=synthetic_fields(unit);self.assertEqual(validate_source_terms(unit,candidate,catalog),[])
            candidate['term_occurrences'].pop();self.assertTrue(validate_source_terms(unit,candidate,catalog))
            self.assertEqual(term_display_text('<MATHSEG_0001>tale',{'MATHSEG_0001':r"\'e"}),'<MATHSEG_0001>tale')

    def test_blank_source_prefix_never_permits_a_blank_or_injected_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,_,_,unit=fixture(Path(tmp));text=synthetic_fields(unit)['translation']
            for value in ['', ' ',r'\alpha','x%y','x\ny','<MATHSEG_9999>']:
                with self.subTest(value=value):self.assertTrue(validate_translation(unit,text.replace('平展（',value,1)))

    def test_changed_parent_role_span_math_or_component_count_rejects_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,_,_,original=fixture(Path(tmp))
            for fault in ['version','separator','parent','index','span','role','math','blank-parent']:
                unit=copy.deepcopy(original);r=unit['math_text_regions'][2];s=r['slots'][1];c=s['parameter_components']
                if fault=='version':unit['schema_version']=2
                if fault=='separator':c['separator']=r'\ '
                if fault=='parent':c['parameter_source']='other'
                if fault=='index':c['component_index']=2
                if fault=='span':c['parameter_byte_span']['start']+=1
                if fault=='role':s['classification_witness']['usage']='descent-etale-component'
                if fault=='math':unit['placeholders'][r['pieces'][0]['placeholder']]+='x'
                if fault=='blank-parent':c['parameter_source']=COMPONENTS[1][0]
                try:unit=stamp_unit_hashes(unit)
                except (KeyError,IndexError):pass
                self.assertTrue(validate_regions(unit),fault)

    def test_unregistered_text_neighbor_and_false_source_owner_remain_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,native,_,_=fixture(Path(tmp))
            text=SECTIONS.replace('sections of ','unregistered prose ',1)
            scanner=Scanner(text,native.policy);_,_,ds=scanner.protect(0,len(text))
            self.assertEqual([d['source'] for d in ds],['unregistered prose '])
        for before,after in [('"test-lemma-one"','"test-lemma-two"'),
                ('witness_ordinal: 1','witness_ordinal: 2')]:
            with tempfile.TemporaryDirectory() as tmp,self.assertRaises(RecordError):fixture(Path(tmp),policy=policy_text().replace(before,after))

    def test_two_complete_histories_replay_and_render_without_changing_math(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,records=history_fixture(Path(tmp),count=2,proof=PROOF,
                math_policy=policy_text(),synthetic_fields=synthetic_fields)
            self.assertEqual(validate_repository_schemas(root),[])
            self.assertEqual(validate_repository_provenance(root,harvest),[])
            current=records[-1]
            paths=render_batch(root/current['files']['output_units']['path'],root/current['files']['output_candidates']['path'],
                root/'upstream.lock',root/'preview','fixture','Synthetic fixture',chapter_source_dir=harvest)
            text=''.join(p.read_text() for p in paths)
            self.assertEqual(text.count(r"平展（\'etale）"),6)
            self.assertNotIn('MATHSEG_',text)
            evidence=root/'translation-data/source-container-restorations/fixture-group-2-proof.json'
            value=read(evidence);value['tool']['version']='source-container-v13';write(evidence,value)
            self.assertTrue(load_source_containers(root,harvest)[1])
            self.assertTrue(validate_repository_provenance(root,harvest))


    def test_source_replay_is_explicit_and_never_a_target_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            _,_,_,_,unit=fixture(Path(tmp))
            self.assertEqual(restore_placeholders(unit,unit['source_text'],_source_replay=True),
                             PROOF[len(unit['render']['prefix']):len(PROOF)-len(unit['render']['suffix'])])
            with self.assertRaises(RecordError):restore_placeholders(unit,unit['source_text'])
            for options in [dict(delimit_commands=True),dict(overrides={'MATHSEG_0001':'x'})]:
                with self.subTest(options=options),self.assertRaises(RecordError):
                    restore_placeholders(unit,unit['source_text'],_source_replay=True,**options)
            with self.assertRaises(RecordError):
                restore_placeholders(unit,synthetic_fields(unit)['translation'],_source_replay=True)
            broken=copy.deepcopy(unit);broken['math_text_regions'][2]['slots'][1]['parameter_components']['separator']='x'
            with self.assertRaises(RecordError):
                restore_placeholders(broken,broken['source_text'],_source_replay=True)

    def test_first_adoption_validates_complete_v3_raw_context_qa_and_render(self):
        from test_source_adoptions import synthetic_fixture
        from stacks_zh.source_adoptions import (POLICIES, assemble_source_adoption,
                                               load_repository_source_adoptions)
        from stacks_zh.source_reextractions import byte_hash
        from stacks_zh.harness import resolve_harness
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, fp, rp, previous, _ = synthetic_fixture(Path(tmp), typed=False)
            # Retain the independent fixture's runtime/policy scaffolding only;
            # its uncommitted data is replaced by this explicit source scope.
            for name in ['translation-data', 'task-scopes', 'docs/evidence']:
                shutil.rmtree(root/name)
            statement = r'\begin{lemma}\label{lemma-one}A claim.\end{lemma}'
            referenced = r'\begin{lemma}\label{lemma-family-is-one}A referenced claim.\end{lemma}'
            (harvest/'test.tex').write_text('\\begin{document}\n\\section{Basics}\n'
                '\\label{section-basic}\n'+statement+'\n'+PROOF+'\n'+referenced+'\n\\end{document}\n')
            (harvest/'tags/tags').write_text('0000,test-section-basic\n0001,test-lemma-one\n'
                                           '0002,test-lemma-family-is-one\n')
            git(harvest, 'add', 'test.tex', 'tags/tags')
            git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'Independent complete etale frames')
            source = git(harvest, 'rev-parse', 'HEAD')
            (root/'upstream.lock').write_text(f'commit = "{source}"\n')
            (root/'config/macro-policy.yml').write_text(policy_text())
            native = Containers(root, harvest)
            groups = [native.select(selector('section_title', owner='0000')),
                      native.select(selector('lemma')), native.select(selector('proof'))]
            units = [lower_container(group, native.policy)[0] for group in groups]
            from stacks_zh.source_terms import source_tex_hash
            write(root/'config/source-terms.json', dict(schema_version=1, source_commit=source,
                nonmathematical_declarations={}, terms=[dict(id='etale', forms=['étale'], chapters=[],
                    evidence=[dict(chapter='test', unit_id=units[2]['unit_id'], source_term='étale',
                                   source_tex_hash=source_tex_hash(units[2]))])]))
            git(root, 'add', 'config', 'upstream.lock')
            git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                'commit', '-qm', 'Synthetic accepted etale frame policy; no facts')
            origin = git(root, 'rev-parse', 'HEAD')
            batches = []
            for name, owned_groups, owned_units in [('title', groups[:1], units[:1]),
                                                    ('lemma-proof', groups[1:], units[1:])]:
                up = f'translation-data/units/test-{name}.jsonl'
                cp = f'translation-data/candidates/synthetic/test-{name}.jsonl'
                write_jsonl(root/up, owned_units)
                batches.append(dict(units_path=up, candidates_path=cp, units=owned_units,
                    containers=[dict(selector=group['selector'], selected=group, unit_ids=[unit['unit_id']])
                                for group, unit in zip(owned_groups, owned_units)],
                    prior_attempts=[]))
            runtime = copy.deepcopy(previous['runtime'])
            runtime['harness']['version'] = resolve_harness('synthetic', root/'config/harnesses.yml').version
            ids = [unit['unit_id'] for unit in units]
            frozen = dict(schema_version=1, tool_version='source-adoption-input-v1',
                adoption_id='synthetic-first', origin_commit=origin, source_commit=source,
                task_id='synthetic-only', created_at='2026-10-19T00:00:00Z', runtime=runtime,
                policies=[dict(path=name, hash=byte_hash((root/name).read_bytes())) for name in POLICIES],
                contexts=[], batches=batches, outside_preferred_reason='Complete independent synthetic frames.',
                unit_ids=ids, chapter='test', parent_tags=['0000'], run_id='run-synthetic-first')
            for row in native.document('test')[1]:
                value = dict(kind='locked-English-neighbor', location=row['location'], source_commit=source,
                    source_unit=row['unit'], owner_tag=row['owner_tag'], parent_tag=row['parent_tag'])
                if row['owner_tag'] == '0002' and row['unit']['node_kind'] == 'lemma':
                    value.update(kind='locked-English-reference', requested_label='test-lemma-family-is-one',
                                 requested_tag='0002')
                frozen['contexts'].append(dict(context_id=row['unit']['unit_id'], value=value, hash=sha256_value(value)))
            scope_path = 'task-scopes/synthetic-first.json'
            files = [scope_path, fp.relative_to(root).as_posix(), rp.relative_to(root).as_posix(),
                     'translation-data/runs/run-synthetic-first.json',
                     'translation-data/source-adoptions/synthetic-first.json']
            files += [batch[role] for batch in batches for role in ['units_path', 'candidates_path']]
            branch = git(root, 'branch', '--show-current')
            scope = dict(schema_version=1, task_id='synthetic-only', owner='synthetic', branch=branch,
                source_commit=source, allowed_write_files=files, data_scopes=[dict(scope_id='synthetic',
                    chapter='test', parent_tags=['0000'], historical_parent_tags=[], unit_ids=ids,
                    input_unit_ids=ids, output_unit_ids=ids, allowed_write_files=files[1:],
                    run_scope=['run-synthetic-first'], model_scope=['synthetic', 'synthetic:fixture:declared'])])
            write(root/scope_path, scope)
            frozen['task'] = dict(issue=1, owner='synthetic', branch=branch, scope_manifest=scope_path,
                scope_manifest_sha256=byte_hash((root/scope_path).read_bytes()), scope_bytes=(root/scope_path).read_text())
            write(fp, frozen)
            raw = [dict(unit_id=unit['unit_id'], **synthetic_fields(unit)) for unit in units]
            for item in raw: item.pop('term_status')
            write_jsonl(rp, raw)
            assemble_source_adoption(root, fp, [rp], harvest)
            self.assertEqual(load_repository_source_adoptions(root, harvest)[1], [])
            self.assertEqual(validate_repository_schemas(root), [])
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            paths = render_batch([root/b['units_path'] for b in batches],
                [root/b['candidates_path'] for b in batches], root/'upstream.lock', root/'preview',
                'synthetic', 'Synthetic fixture', chapter_source_dir=harvest)
            self.assertEqual(''.join(path.read_text() for path in paths).count(r"平展（\'etale）合成"), 6)
            # Frozen source/context and immutable raw cannot be omitted later.
            broken = copy.deepcopy(frozen)
            broken['contexts'] = []
            write(fp, broken)
            self.assertTrue(load_repository_source_adoptions(root, harvest)[1])


if __name__=='__main__':unittest.main()
