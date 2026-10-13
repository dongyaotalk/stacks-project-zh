"""Independent synthetic full histories; no production translation or approval."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_preceding_statement_paragraphs import after_fixture
from test_nested_preceding_statement_paragraphs import nested_fixture
from test_source_container_boundaries import INTRO, PLAIN
from test_source_containers import old_unit, selector
from test_group_derivations import commit, run_for, save, write
from stacks_zh.records import RecordError, load_jsonl, placeholder_names, sha256_value, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import (Containers, load_source_containers, lower_container,
    verify_old_group, write_container_package)
from stacks_zh.source_reextractions import source_tex

TARGET = '\\medskip\\noindent\nA second paragraph with $y$ and \\ref{lemma-one}.'
NESTED = ('\\begin{lemma}\n\\label{lemma-one}\nChoose two objects.\n'
          '\\begin{enumerate}\n\\item First object.\n\\item Second object.\n'
          '\\end{enumerate}\n\\end{lemma}')


def fixture(base, *, nested=False, count=2, native=None):
    text = native or (NESTED if nested else PLAIN) + '\n\n' + INTRO + '\n\n' + TARGET
    if nested:
        root, harvest, original, plan, output = nested_fixture(base, native=text)
    else:
        root, harvest, original, plan, output = after_fixture(base, native=text, split=True)
    units = copy.deepcopy(original)
    oldc = load_jsonl(root / json.loads(plan.read_text())['candidates_file'])
    if not nested: units[1]['unit_id'] = 'tag:0001:p000'
    units[-1]['unit_id'] = 'tag:0001:p001'
    pieces = ['A second', 'paragraph with <MATH_0001> and <REF_0001>.'] if count == 2 else [
        'A', 'second', 'paragraph with <MATH_0001> and <REF_0001>.']
    for i, text in enumerate(pieces):
        u = old_unit(units[0]['source_commit'], f'tag:0001:p{i+2:03d}', 'paragraph', text,
                     '\\medskip\\noindent\n' if i == 0 else '', '\n')
        if i == len(pieces)-1: u['placeholders'] = {'MATH_0001':'$y$', 'REF_0001':r'\ref{lemma-one}'}
        units.append(u)
    for u in units: u['parent_tag'] = '0001'
    units = [stamp_unit_hashes(u) for u in units]
    candidates = []
    for u in units:
        c = copy.deepcopy(oldc[0]); c['context']['unit_id'] = u['unit_id']
        c.update(unit_id=u['unit_id'], source_text_hash=u['source_text_hash'],
                 context_hash=sha256_value(c['context']),
                 translation=''.join('<'+n+'>' for n in placeholder_names(u['source_text']))+'合成测试。',
                 allowed_english=[], term_occurrences=[], unknown_terms=[], notes=['Synthetic only.'])
        c['translation_hash'] = sha256_value(c['translation']); candidates.append(c)
    data = json.loads(plan.read_text()); data['derivation_id'] = 'synthetic-split-after-paragraph'
    data['groups'] = []
    for name, members, coordinate in [
        ('statement', units[:-count-1], selector('lemma')),
        ('previous', units[-count-1:-count], selector('paragraph', owner='0000')),
        ('target', units[-count:], selector('paragraph', owner='0000', ordinal=2))]:
        ids = [u['unit_id'] for u in members]
        data['groups'].append(dict(group_id=name, input_unit_ids=ids, identity_anchor=ids[0],
                                  selector=coordinate, layout='whole', reason='Synthetic complete source; no adoption.'))
    save(root, data['units_file'], units); save(root, data['candidates_file'], candidates)
    write(root/'translation-data/runs/fixture-boundary-run.json',
          run_for(candidates, units[0]['source_commit'], 'translation', 'fixture-boundary-run'))
    write(plan, data); commit(root)
    return root, harvest, units, plan, output


class SplitAfterParagraphTests(unittest.TestCase):
    def witness(self, containers, units, *, ids=None, selected=None):
        ids = ids if ids is not None else [u['unit_id'] for u in units if u['unit_id'].startswith('tag:0001:p') and int(u['unit_id'][-3:]) >= 2]
        selected = selected or containers.select(selector('paragraph', owner='0000', ordinal=2))
        return verify_old_group(units, containers.english.tags, ids, selected,
            native_containers=containers, allow_split_after_paragraph=True)

    def install(self, root, output, records):
        for record in records:
            for role, name in [('input_units','input-units.jsonl'), ('input_candidates','input-candidates.jsonl')]:
                path = root / record['files'][role]['path']; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((output/name).read_bytes())
            write(root/f"translation-data/source-container-restorations/{record['restoration_id']}.json", record)

    def test_complete_two_or_three_parts_after_plain_or_list_statement_and_whole_paragraph(self):
        for nested in [False, True]:
            for count in [2, 3]:
                with tempfile.TemporaryDirectory() as tmp:
                    root, harvest, units, _, _ = fixture(Path(tmp), nested=nested, count=count)
                    containers = Containers(root, harvest)
                    chosen = containers.select(selector('paragraph', owner='0000', ordinal=2))
                    ids = [u['unit_id'] for u in units[-count:]]
                    with self.assertRaises(RecordError):
                        verify_old_group(units, containers.english.tags, ids, chosen, native_containers=containers,
                            allow_preceding_paragraph=True, allow_nested_preceding_paragraph=True,
                            allow_section_title_paragraph=True, allow_split_preceding_paragraph=True,
                            allow_paragraph_math_layout=True, allow_historical_parent_paragraph=True)
                    anchor = self.witness(containers, units)['paragraph_anchor']
                    self.assertEqual(anchor['paragraph_input_unit_ids'], ids)
                    self.assertEqual(anchor['preceding_paragraph_input_unit_id'], 'tag:0001:p001')
                    self.assertEqual(anchor['preceding_paragraph_selector'], selector('paragraph', owner='0000'))
                    self.assertEqual(anchor['preceding_paragraph_anchor']['preceding_statement_input_unit_ids'],
                                     [u['unit_id'] for u in units[:-count-1]])
                    self.assertEqual('preceding_statement_list_closings' in anchor['preceding_paragraph_anchor'], nested)
                    self.assertEqual(anchor['paragraph_signature_hash'], sha256_value([
                        ['protected', r'\medskip'], ['protected',r'\noindent'],
                        ['text','A second paragraph with'], ['protected','$y$'], ['text','and'],
                        ['protected',r'\ref{lemma-one}'], ['text','.']]))
                    self.assertEqual(source_tex(lower_container(chosen, containers.policy)[0]), chosen['fragment'])

    def test_partial_reordered_foreign_wrapped_changed_or_unclassified_old_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, original, _, _ = fixture(Path(tmp), count=3)
            containers = Containers(root, harvest)
            original_ids = [u['unit_id'] for u in original[-3:]]
            faults = ['words','math','reference','unicode','blank','prefix','suffix','no-medskip',
                      'fake-prefix','unknown','typed-target','parent','chapter','source','schema','kind',
                      'noncanonical','previous-id','previous-schema','previous-prefix','previous-suffix',
                      'previous-words','previous-math','previous-unknown','statement-words',
                      'statement-unknown','statement-prefix','statement-close','statement-parent',
                      'missing-statement','missing-tail','missing-previous','missing-part','order','duplicate',
                      'partial-ids','empty-ids','one-id','reverse-ids','duplicate-ids','absent-id','extra-part']
            for fault in faults:
                units = copy.deepcopy(original); ids = original_ids[:]
                previous, first, middle, last = units[-4:]
                if fault == 'words': middle['source_text'] += ' extra'
                if fault == 'math': last['placeholders']['MATH_0001'] = '$z$'
                if fault == 'reference': last['placeholders']['REF_0001'] = r'\ref{lemma-two}'
                if fault == 'unicode': middle['source_text'] += '\u00a0'
                if fault == 'blank': first['render']['suffix'] = '\n\n'
                if fault == 'prefix': middle['render']['prefix'] = '\\noindent'
                if fault == 'suffix': middle['render']['suffix'] += '\\noindent'
                if fault == 'no-medskip': first['render']['prefix'] = '\\noindent\n'
                if fault == 'fake-prefix': first['render']['prefix'] = '%\\medskip\\noindent\n'
                if fault == 'unknown': middle['source_text'] += r' \mystery{hidden}'
                if fault == 'typed-target': last['placeholders']['MATH_0001'] = r'$\text{unclassified}$'
                if fault == 'parent': middle['parent_tag'] = '0002'
                if fault == 'chapter': middle['chapter'] = 'other'
                if fault == 'source': middle['source_commit'] = 'f'*40
                if fault == 'schema': middle['schema_version'] = 2
                if fault == 'kind': middle['node_kind'] = 'display_math'
                if fault == 'noncanonical': middle['unit_id'] = ids[1] = 'tag:0001:partial'
                if fault == 'previous-id': previous['unit_id'] = 'tag:0001:previous'
                if fault == 'previous-schema': previous['schema_version'] = 2
                if fault == 'previous-prefix': previous['render']['prefix'] = '\\medskip\\noindent\n'
                if fault == 'previous-suffix': previous['render']['suffix'] += '\\medskip'
                if fault == 'previous-words': previous['source_text'] += ' Extra.'
                if fault == 'previous-math': previous['placeholders']['MATH_0001'] = '$z$'
                if fault == 'previous-unknown': previous['source_text'] += r' \mystery{hidden}'
                if fault == 'statement-words': units[0]['source_text'] += ' Extra.'
                if fault == 'statement-unknown': units[0]['source_text'] += r' \mystery{hidden}'
                if fault == 'statement-prefix': units[0]['render']['prefix'] = '$'+units[0]['render']['prefix']+'$'
                if fault == 'statement-close': units[1]['render']['suffix'] = '$'+units[1]['render']['suffix']+'$'
                if fault == 'statement-parent': units[0]['parent_tag'] = '0002'
                if fault == 'missing-statement': units = units[2:]
                if fault == 'missing-tail': units.pop(1)
                if fault == 'missing-previous': units.pop(2)
                if fault == 'missing-part': units.pop(-2); ids.pop(1)
                if fault == 'order': units[-3:] = units[-3:][::-1]
                if fault == 'duplicate': units.append(copy.deepcopy(first))
                if fault == 'partial-ids': ids.pop()
                if fault == 'empty-ids': ids = []
                if fault == 'one-id': ids = ids[:1]
                if fault == 'reverse-ids': ids.reverse()
                if fault == 'duplicate-ids': ids[1] = ids[0]
                if fault == 'absent-id': ids[1] = 'tag:0001:p099'
                if fault == 'extra-part':
                    extra = copy.deepcopy(last); extra.update(unit_id='tag:0001:p005', source_text='An extra paragraph.')
                    units.append(extra)
                with self.subTest(fault=fault), self.assertRaises(RecordError): self.witness(containers, units, ids=ids)

    def test_native_two_adjacencies_uniqueness_and_real_section_are_required(self):
        variants = [PLAIN+'\n% gap\n'+INTRO+'\n\n'+TARGET,
                    PLAIN+'\n\n'+INTRO+'\n% gap\n'+TARGET,
                    PLAIN+'\n\n'+INTRO+'\n\\begin{lemma}\\label{lemma-two}Extra.\\end{lemma}\n'+TARGET,
                    PLAIN+'\n\n'+INTRO+'\n\n'+TARGET+'\n\n'+TARGET,
                    PLAIN+'\n\n'+INTRO+'\n\n'+TARGET+'\n\n'+INTRO,
                    PLAIN+'\n\n'+INTRO+'\n\\section{Other}\\label{lemma-two}\n'+TARGET]
        for native in variants:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = fixture(Path(tmp), native=native)
                with self.subTest(native=native), self.assertRaises(RecordError):
                    self.witness(Containers(root, harvest), units)

    def test_schema_loader_recomputes_every_nested_field_and_old_versions_still_reject(self):
        for nested in [False, True]:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, plan, output = fixture(Path(tmp), nested=nested)
                before = {p.relative_to(root):p.read_bytes() for p in (root/'translation-data').rglob('*') if p.is_file()}
                manifest = write_container_package(root, harvest, plan, output)
                self.assertEqual(manifest['state'], 'PREPARED')
                stamps = {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()}
                self.assertEqual(write_container_package(root, harvest, plan, output, check=True), manifest)
                self.assertEqual(stamps, {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()})
                self.assertEqual(before, {p.relative_to(root):p.read_bytes() for p in (root/'translation-data').rglob('*') if p.is_file()})
                records = json.loads((output/'restorations.json').read_text())
                record = next(r for r in records if r['tool']['version']=='source-container-v11')
                self.assertFalse(validate_named_schema(record, 'source-container-restoration.schema.json', 'synthetic'))
                self.install(root, output, records); self.assertFalse(load_source_containers(root, harvest)[1])
                path = root/f"translation-data/source-container-restorations/{record['restoration_id']}.json"
                anchor = record['legacy_boundary_witness']['paragraph_anchor']
                paths = [(key,) for key in anchor if key!='preceding_paragraph_anchor'] + [
                    ('preceding_paragraph_anchor', key) for key in anchor['preceding_paragraph_anchor']]
                for keys in paths:
                    bad = copy.deepcopy(record); current = bad['legacy_boundary_witness']['paragraph_anchor']
                    for key in keys[:-1]: current = current[key]
                    key = keys[-1]; value = current[key]
                    if isinstance(value, dict): value['owner_tag'] = '9999'
                    elif isinstance(value, list): value[0] = 'itemize' if key.endswith('closings') else 'tag:9999:p001'
                    else: current[key] = 'sha256:'+'0'*64 if key.endswith('hash') else '9999'
                    self.assertFalse(validate_named_schema(bad,'source-container-restoration.schema.json','valid-shaped tamper'))
                    write(path, bad)
                    with self.subTest(nested=nested, keys=keys):
                        self.assertTrue(any('legacy boundary witness differs' in e for e in load_source_containers(root,harvest)[1]))
                for ids in [[], record['input_unit_ids'][:1], record['input_unit_ids'][::-1]]:
                    bad = copy.deepcopy(record); bad['input_unit_ids'] = ids; write(path, bad)
                    with self.subTest(input_ids=ids): self.assertTrue(load_source_containers(root,harvest)[1])
                for version in range(1,11):
                    bad = copy.deepcopy(record); bad['tool']['version'] = f'source-container-v{version}'; write(path,bad)
                    with self.subTest(version=version): self.assertTrue(load_source_containers(root,harvest)[1])
                write(path,record); self.assertFalse(load_source_containers(root,harvest)[1])

    def test_v4_replay_keeps_all_old_groups_and_requires_each_complete_five_field_revision(self):
        from stacks_zh.group_derivations import FIELDS, replay_groups, revision_group
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, plan, output = fixture(Path(tmp), nested=True)
            self.assertEqual(write_container_package(root, harvest, plan, output)['state'],'PREPARED')
            records=json.loads((output/'restorations.json').read_text()); self.install(root, output, records)
            restored, errors = load_source_containers(root, harvest); self.assertFalse(errors)
            old=load_jsonl(output/'input-candidates.jsonl')
            record={k:records[0][k] for k in ['derivation_id','source_commit','origin_commit','created_at','files']}
            record['unit_groups']=[]; corrections={}
            for source in records:
                group={k:source[k] for k in ['group_id','input_unit_ids','output_unit_ids','reason']}
                group.update(identity_anchor=group['input_unit_ids'][0],output_units=source['new_units'],
                    source_container_restoration_id=source['restoration_id'],model_correction_id='synthetic-v11-revision')
                record['unit_groups'].append(group)
                inputs=[u for u in units if u['unit_id'] in group['input_unit_ids']]
                candidates=[c for c in old if c['unit_id'] in group['input_unit_ids']]
                for u in source['new_units']:
                    raw=copy.deepcopy(candidates[0]); context={'revision_input':revision_group(record,group,inputs,candidates)}
                    raw.update(unit_id=u['unit_id'],context=context,context_hash=sha256_value(context),
                        translation=''.join('<'+n+'>' for n in placeholder_names(u['source_text']))+'合成测试。')
                    raw['translation_hash']=sha256_value(raw['translation'])
                    corrections[(group['model_correction_id'],u['unit_id'])]={'unit':u,'candidate':raw,
                        'record':{'derivation_ids':{u['unit_id']:record['derivation_id']},'source_commit':record['source_commit']}}
            tags=Containers(root,harvest).english.tags
            new,newc=replay_groups(record,units,old,corrections,None,restored,tags)
            self.assertEqual(len(new),3); self.assertTrue(all(c['publication_status']=='CANDIDATE' for c in newc))
            for key in corrections:
                for fault in [*sorted(FIELDS),'missing','old-units','old-candidates','approval']:
                    changed=copy.deepcopy(corrections)
                    if fault in FIELDS: changed[key]['candidate'].pop(fault)
                    if fault=='missing': changed.pop(key)
                    if fault=='old-units': changed[key]['candidate']['context']['revision_input']['source_units'].pop()
                    if fault=='old-candidates': changed[key]['candidate']['context']['revision_input']['candidates'].pop()
                    if fault=='approval': changed[key]['candidate']['stage']='MATH_REVIEWED'
                    with self.subTest(key=key,fault=fault), self.assertRaises((RecordError,KeyError)):
                        replay_groups(record,units,old,changed,None,restored,tags)
