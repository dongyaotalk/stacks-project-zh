"""Synthetic source fixtures only; no model generation or human approval."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from test_group_derivations import commit, save, write
from test_progress_coverage import adoption_setup, current_units
from test_source_containers import git
from stacks_zh.extraction import Policy
from stacks_zh.progress_coverage import container_tag_coverage, native_container_tag_coverage
from stacks_zh.records import RecordError
from stacks_zh.source_adoptions import POLICIES, REFERENCE_POLICIES, load_repository_source_adoptions
from stacks_zh.source_containers import Containers, clean, lower_container
from stacks_zh.source_reextractions import byte_hash

ROOT = Path(__file__).resolve().parents[1]
TAGS = {'test-remarks-one':'0001', 'test-item-first':'0003', 'test-item-second':'0004'}
LIST = (r'\begin{enumerate}\item First \label{item-first} object.'
        r'\item\label{item-second} Second object.\end{enumerate}')


def selected(kind, text):
    return {'selector': {'file':'test.tex', 'kind':kind}, 'fragment':text}


def native_adoption(base, *, reference=False):
    root, harvest, record, frozen, path = adoption_setup(base)
    text = ('\\begin{document}\n\\section{Basics}\\label{section-basic}\n'
            '\\begin{remarks}\\label{remarks-one}Notes.\n' + LIST +
            '\n\\end{remarks}\n\\noindent\n'
            + LIST.replace('item-first', 'item-third').replace('item-second', 'item-fourth') +
            '\n\\begin{lemma}\\label{lemma-two}Claim.\\end{lemma}\n\\end{document}')
    (harvest/'test.tex').write_text(text)
    (harvest/'tags/tags').write_text(
        '0000,test-section-basic\n0001,test-remarks-one\n0002,test-lemma-two\n'
        '0003,test-item-first\n0004,test-item-second\n0005,test-item-third\n0006,test-item-fourth\n')
    commit(harvest)
    source = git(harvest, 'rev-parse', 'HEAD')
    (root/'upstream.lock').write_text(f'commit = "{source}"\n')
    # Prose's accepted selector requires labels immediately after real items.
    value = (harvest/'test.tex').read_text().replace(
        r'\item First \label{item-third} object.', r'\item\label{item-third} First object.')
    if reference:
        from test_sites_cohomology_math_text import CUP, synthetic_policy
        value = value.replace('Claim.', 'Claim.\n' + CUP).replace('\\end{document}',
            '\\begin{remark}\\label{remark-cup-product}Reference.\\end{remark}\n\\end{document}')
        with (harvest/'tags/tags').open('a') as stream:
            stream.write('0007,test-remark-cup-product\n')
        (root/'config/macro-policy.yml').write_text(synthetic_policy().replace('test-lemma-one', 'test-lemma-two'))
        shutil.copyfile(ROOT/'schema/math-text-references.schema.json', root/'schema/math-text-references.schema.json')
    (harvest/'test.tex').write_text(value); commit(harvest)
    source = git(harvest, 'rev-parse', 'HEAD')
    (root/'upstream.lock').write_text(f'commit = "{source}"\n')
    native = Containers(root, harvest)
    coordinates = [
        dict(file='test.tex', owner_tag='0001', owner_label='test-remarks-one',
             parent_tag='0000', kind='remarks', ordinal=1),
        dict(file='test.tex', owner_tag='0000', owner_label='test-section-basic',
             parent_tag='0000', kind='prose_block', ordinal=1)]
    if reference:
        coordinates.append(dict(file='test.tex', owner_tag='0002', owner_label='test-lemma-two',
                                parent_tag='0000', kind='lemma', ordinal=1))
    groups = []
    for coordinate in coordinates:
        fragment = native.select(coordinate)
        units = [clean(u) for u in lower_container(fragment, native.policy)]
        groups.append(dict(selector=coordinate, selected=fragment, unit_ids=[u['unit_id'] for u in units]))
    units = [clean(u) for group in groups for u in lower_container(group['selected'], native.policy)]
    batch = frozen['batches'][0]
    (root/batch['units_path']).unlink()
    (root/batch['candidates_path']).unlink()
    batch.update(units=units, containers=groups,
        units_path='translation-data/units/test-native.jsonl',
        candidates_path='translation-data/candidates/synthetic/test-native.jsonl')
    output = record['outputs'][0]
    output['units'] = save(root, batch['units_path'], units)
    output['candidates'] = save(root, batch['candidates_path'],
        [dict(unit_id=u['unit_id'], source_commit=source, source_status='CURRENT') for u in units])
    # Commit only the independent source/policies, before adding new immutable evidence.
    (root/record['input']['path']).unlink()
    path.unlink()
    commit(root)
    frozen.update(origin_commit=git(root,'rev-parse','HEAD'), source_commit=source,
        unit_ids=[u['unit_id'] for u in units], parent_tags=['0000'], contexts=[],
        policies=[dict(path=p,hash=byte_hash((root/p).read_bytes()))
                  for p in (REFERENCE_POLICIES if reference else POLICIES)])
    if reference:
        frozen['tool_version'] = 'source-adoption-input-v6'
        record['tool_version'] = 'source-adoption-v6'
    scope_path = root/frozen['task']['scope_manifest']
    scope = json.loads(scope_path.read_text())
    scope['source_commit'] = source
    scope['allowed_write_files'] += [batch['units_path'],batch['candidates_path']]
    scope['data_scopes'][0]['allowed_write_files'] += [batch['units_path'],batch['candidates_path']]
    scope['data_scopes'][0].update(unit_ids=frozen['unit_ids'], input_unit_ids=frozen['unit_ids'],
        output_unit_ids=frozen['unit_ids'], parent_tags=['0000'])
    write(scope_path, scope)
    frozen['task'].update(scope_bytes=scope_path.read_text(), scope_manifest_sha256=byte_hash(scope_path.read_bytes()))
    write(root/record['input']['path'], frozen)
    record.update(origin_commit=frozen['origin_commit'],source_commit=source,
                  unit_ids=frozen['unit_ids'],parent_tags=['0000'])
    record['input']['hash'] = byte_hash((root/record['input']['path']).read_bytes())
    write(path, record)
    return root, harvest, record, frozen, path


class NativeListTagTests(unittest.TestCase):
    def setUp(self):
        self.policy = Policy((ROOT/'config/macro-policy.yml').read_text())

    def test_mid_item_remarks_and_plain_prose_tags(self):
        remarks = r'\begin{remarks}\label{remarks-one}Notes.'+LIST+r'\end{remarks}'
        for kind, text in [('remarks',remarks), ('prose_block',LIST)]:
            with self.subTest(kind=kind):
                self.assertEqual(native_container_tag_coverage(selected(kind,text), self.policy,TAGS),
                                 {'0003','0004'})

    def test_fake_labels_inside_opaque_or_argument_nodes_never_count(self):
        fake = [r'$\item\label{item-second}$', '%\\item\\label{item-second}\n',
                r'\footnote{\item\label{item-second}}', r'\textit{\label{item-second}}',
                r'{\item\label{item-second}}', r'\ref{item-second}',
                r'\begin{verbatim}\item\label{item-second}\end{verbatim}']
        for value in fake:
            text = r'\begin{enumerate}\item\label{item-first}First.'+value+r'\end{enumerate}'
            with self.subTest(value=value):
                self.assertEqual(native_container_tag_coverage(selected('prose_block',text),
                                 self.policy,TAGS), {'0003'})

    def test_partial_duplicate_unknown_and_cross_chapter_labels_fail(self):
        cases = [
            ('remarks',r'\begin{remarks}'+LIST),
            ('remarks',r'Prefix.\begin{remarks}'+LIST+r'\end{remarks}'),
            ('remarks',r'\begin{remarks}'+LIST+r'\end{remarks}Suffix.'),
            ('prose_block',LIST.replace(r'\end{enumerate}','')),
            ('prose_block',LIST.replace('item-second','item-first')),
            ('prose_block',LIST.replace('item-second','missing')),
            ('prose_block',LIST.replace('item-second','other-item'))]
        tags = {**TAGS,'other-item':'0005'}
        for kind,text in cases:
            with self.subTest(text=text), self.assertRaises(RecordError):
                native_container_tag_coverage(selected(kind,text),self.policy,tags)
        with self.assertRaises(RecordError):
            native_container_tag_coverage(selected('prose_block',LIST),self.policy,
                                          {**TAGS,'other-alias':'0003'})

    def test_complete_first_adoption_binds_both_kinds_without_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,harvest,record,_,_=native_adoption(Path(tmp))
            coverage = container_tag_coverage(root,harvest,current_units(root))
            self.assertEqual(set().union(*coverage.values()), {'0003','0004','0005','0006'})
            (root/record['outputs'][0]['candidates']['path']).unlink()
            self.assertEqual(coverage,container_tag_coverage(root,harvest,current_units(root)))
            self.assertTrue(load_repository_source_adoptions(root,harvest)[1])

    def test_v6_list_source_binds_complete_reference_policy_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _, frozen, _ = native_adoption(Path(tmp), reference=True)
            self.assertTrue(any(u['schema_version'] == 4 for u in frozen['batches'][0]['units']))
            coverage = container_tag_coverage(root, harvest, current_units(root))
            self.assertEqual(set().union(*coverage.values()), {'0003', '0004', '0005', '0006'})
        for failure in ('missing', 'extra', 'duplicate'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as tmp:
                root, harvest, record, frozen, path = native_adoption(Path(tmp), reference=True)
                if failure == 'missing':
                    frozen['policies'] = [p for p in frozen['policies']
                                          if p['path'] != 'schema/math-text-references.schema.json']
                elif failure == 'extra':
                    frozen['policies'].append(dict(path='docs/progress.md', hash='sha256:' + '0' * 64))
                else:
                    frozen['policies'].append(frozen['policies'][-1])
                write(root / record['input']['path'], frozen)
                record['input']['hash'] = byte_hash((root / record['input']['path']).read_bytes())
                write(path, record)
                with self.assertRaises(RecordError):
                    container_tag_coverage(root, harvest, current_units(root))

    def test_rehashed_incomplete_current_source_and_frozen_bindings_fail(self):
        for fault in ['fragment','partial','source','bytes','order']:
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
                root,harvest,record,frozen,path=native_adoption(Path(tmp))
                batch=frozen['batches'][0]
                if fault=='fragment': batch['containers'][0]['selected']['fragment']+='Extra.'
                if fault=='partial': batch['units']=batch['units'][1:]
                if fault=='source': record['source_commit']=frozen['source_commit']='a'*40
                if fault=='order': batch['containers'].reverse()
                if fault=='partial': record['outputs'][0]['units']=save(root,batch['units_path'],batch['units'])
                if fault=='bytes':
                    with (root/batch['units_path']).open('ab') as stream: stream.write(b'\n')
                write(root/record['input']['path'],frozen)
                record['input']['hash']=byte_hash((root/record['input']['path']).read_bytes())
                write(path,record)
                with self.assertRaises(RecordError):
                    container_tag_coverage(root,harvest,current_units(root))
