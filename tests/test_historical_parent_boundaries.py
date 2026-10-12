"""Synthetic Git witnesses only; no production model generation or approval."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_derivations import fixture as candidate_fixture
from test_group_derivations import commit, run_for, save, write
from test_source_containers import fixture as english_fixture, git, old_unit, paragraph_inputs, selector
from test_source_container_boundaries import INTRO, PLAIN
from stacks_zh.records import RecordError, sha256_value, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import (Containers, load_source_containers, lower_container,
    old_container_groups, verify_old_group, write_container_package)
from stacks_zh.source_historical_parent_boundaries import historical_parent_paragraph_witness
from stacks_zh.source_reextractions import source_tex

BEFORE = '\\begin{lemma}\n\\label{lemma-two}\nA preceding assertion.\n\\end{lemma}'


def fixture(base, *, split=False, native=None, other=''):
    root, harvest, source = english_fixture(base,
        statement=native or BEFORE + '\n\n' + INTRO + '\n\n' + PLAIN, other=other)
    if native and 'section-other' in native:
        tags = harvest / 'tags/tags'; tags.write_text(tags.read_text() + '0005,test-section-other\n')
        git(harvest, 'add', '.'); git(harvest, '-c', 'user.name=Synthetic', '-c',
            'user.email=fixture@example.invalid', 'commit', '-qm', 'synthetic distinct Section')
        source = git(harvest, 'rev-parse', 'HEAD')
        (root / 'upstream.lock').write_text(f'commit = "{source}"\n')
    paragraph = paragraph_inputs(source)[1]
    paragraph.update(unit_id='tag:0002:p001', parent_tag='0002')
    statement = old_unit(source, 'tag:0001:statement', 'lemma',
        'A complete assertion.', '\\begin{lemma}\n\\label{test-lemma-one}\n', '\n\\end{lemma}\n')
    statement['parent_tag'] = '0001'
    units = [paragraph, statement]
    if split:
        first = copy.deepcopy(statement); first['source_text'] = 'A complete'; first['render']['suffix'] = ''
        last = copy.deepcopy(statement); last.update(unit_id='tag:0001:p001', node_kind='paragraph', source_text=' assertion.')
        last['render']['prefix'] = ''; units[1:] = [first, last]
    units = [stamp_unit_hashes(u) for u in units]
    candidates = []
    for unit in units:
        candidate = copy.deepcopy(candidate_fixture()[2][0])
        context = {'unit_id': unit['unit_id'], 'source_commit': source,
                   'prompt_version': 'fixture', 'policy_revision': 'fixture'}
        candidate.update(unit_id=unit['unit_id'], source_commit=source,
            source_text_hash=unit['source_text_hash'], context=context, context_hash=sha256_value(context),
            run_id='fixture-historical-run', translation='<MATH_0001>合成测试。' if unit['placeholders'] else '合成测试。',
            allowed_english=[], term_occurrences=[], unknown_terms=[], notes=['Synthetic only.'],
            term_status='CLEAR', stage='TERM_OK', qa_status='PASS', publication_status='CANDIDATE')
        candidate['translation_hash'] = sha256_value(candidate['translation']); candidates.append(candidate)
    up = 'translation-data/units/test-historical.jsonl'; cp = 'translation-data/candidates/fixture/test-historical.jsonl'
    save(root, up, units); save(root, cp, candidates)
    write(root / 'translation-data/runs/fixture-historical-run.json', run_for(candidates, source, 'translation', 'fixture-historical-run'))
    git(root, 'init', '-q'); commit(root)
    plan = {'derivation_id': 'fixture-historical', 'created_at': '2026-10-13T00:00:00Z',
            'units_file': up, 'candidates_file': cp, 'groups': []}
    for name, members, coordinate in [('intro', units[:1], selector('paragraph', owner='0000')),
                                       ('statement', units[1:], selector('lemma'))]:
        ids = [u['unit_id'] for u in members]
        plan['groups'].append({'group_id': name, 'input_unit_ids': ids, 'identity_anchor': ids[0],
            'selector': coordinate, 'layout': 'whole', 'reason': 'Complete synthetic witness, never adopted.'})
    plan_path = root / 'build/plan.json'; write(plan_path, plan)
    return root, harvest, units, plan_path, root / 'build/package'


class HistoricalParentTests(unittest.TestCase):
    def witness(self, containers, units, selected=None, ids=None):
        selected = selected or containers.select(selector('paragraph', owner='0000'))
        return verify_old_group(units, containers.english.tags, ids or [units[0]['unit_id']], selected,
            native_containers=containers, allow_historical_parent_paragraph=True)

    def test_complete_same_batch_successor_and_two_real_native_owners_are_required(self):
        for split in [False, True]:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = fixture(Path(tmp), split=split)
                containers = Containers(root, harvest); selected = containers.select(selector('paragraph', owner='0000'))
                with self.assertRaises(RecordError):
                    verify_old_group(units, containers.english.tags, [units[0]['unit_id']], selected,
                        native_containers=containers, allow_preceding_paragraph=True,
                        allow_nested_preceding_paragraph=True, allow_section_title_paragraph=True,
                        allow_split_preceding_paragraph=True, allow_paragraph_math_layout=True)
                anchor = self.witness(containers, units, selected)['paragraph_anchor']
                self.assertEqual(anchor['historical_parent_tag'], '0002')
                self.assertEqual(anchor['following_statement_historical_parent_tag'], '0001')
                self.assertEqual(anchor['preceding_native_statement_selector'], selector('lemma', owner='0002'))
                self.assertEqual(anchor['following_statement_selector'], selector('lemma'))
                self.assertEqual(anchor['following_statement_input_unit_ids'], [u['unit_id'] for u in units[1:]])
                self.assertEqual(source_tex(lower_container(selected, containers.policy)[0]), selected['fragment'])

    def test_full_old_scope_prose_math_and_historical_owners_cannot_be_forged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, original, _, _ = fixture(Path(tmp), split=True)
            containers = Containers(root, harvest)
            for fault in ['paragraph-words','slice','math','reference','command','unicode','blank',
                          'same-parent','arbitrary-parent','section-parent','noncanonical-id',
                          'following-parent','wrong-following-label','missing-following','missing-tail',
                          'order','duplicate','partial-paragraph','fake-prefix','fake-close',
                          'following-words','following-reference','following-unknown','unknown','chapter','source']:
                units = copy.deepcopy(original); selected = None; ids = None
                if fault == 'paragraph-words': units[0]['source_text'] += ' Added.'
                if fault == 'slice': units[0]['source_text'] = 'paragraph with <MATH_0001>.'
                if fault == 'math': units[0]['placeholders']['MATH_0001'] = '$y$'
                if fault == 'reference': units[0]['render']['suffix'] += '\\ref{test-lemma-one}'
                if fault == 'command': units[0]['render']['prefix'] = '\\medskip\n'
                if fault == 'unicode': units[0]['source_text'] = units[0]['source_text'].replace(' ', '\u00a0', 1)
                if fault == 'blank': units[0]['source_text'] = units[0]['source_text'].replace('paragraph', '\n\nparagraph')
                if fault == 'same-parent': units[0].update(parent_tag='0001', unit_id='tag:0001:p002')
                if fault == 'arbitrary-parent': units[0].update(parent_tag='9999', unit_id='tag:9999:p002')
                if fault == 'section-parent': units[0].update(parent_tag='0000', unit_id='tag:0000:p002')
                if fault == 'noncanonical-id': units[0]['unit_id'] = 'tag:0002:statement'
                if fault == 'following-parent': units[2]['parent_tag'] = '0002'
                if fault == 'wrong-following-label': units[1]['render']['prefix'] = '\\begin{lemma}\\label{test-lemma-two}'
                if fault == 'missing-following': units = units[:1]
                if fault == 'missing-tail': units = units[:2]
                if fault == 'order': units = [units[0], units[2], units[1]]
                if fault == 'duplicate': units.append(copy.deepcopy(units[0]))
                if fault == 'partial-paragraph': ids = [units[0]['unit_id'], units[1]['unit_id']]
                if fault == 'fake-prefix': units[1]['render']['prefix'] = '$\\begin{lemma}\\label{test-lemma-one}$'
                if fault == 'fake-close': units[-1]['render']['suffix'] = '$\\end{lemma}$'
                if fault == 'following-words': units[1]['source_text'] += ' Changed.'
                if fault == 'following-reference': units[-1]['render']['suffix'] += '\\ref{test-lemma-two}'
                if fault == 'following-unknown': units[-1]['source_text'] += r' \mystery{hidden}'
                if fault == 'unknown': units[0]['source_text'] += r' \mystery{hidden}'
                if fault == 'chapter': units[1]['chapter'] = 'other'
                if fault == 'source': units[1]['source_commit'] = 'f' * 40
                if fault == 'same-parent':
                    # This remains legitimate old v4 evidence; it cannot be
                    # represented as a new distinct-parent witness.
                    self.assertNotIn('following_statement_historical_parent_tag',
                                     self.witness(containers, units)['paragraph_anchor'])
                    selected = containers.select(selector('paragraph', owner='0000'))
                    groups = old_container_groups(units, containers.english.tags, native_containers=containers)
                    with self.assertRaises(RecordError):
                        historical_parent_paragraph_witness(containers, units, groups, groups[0], selected)
                    continue
                with self.subTest(fault=fault), self.assertRaises(RecordError):
                    self.witness(containers, units, selected, ids)

    def test_native_ambiguity_nonadjacent_gaps_and_different_sections_remain_blocked(self):
        for native, other in [
            (BEFORE + '\n% Not mere whitespace\n' + INTRO + '\n\n' + PLAIN, ''),
            (BEFORE + '\n\n' + INTRO + '\n% Not mere whitespace\n' + PLAIN, ''),
            (INTRO + '\n\n' + PLAIN, ''),
            (BEFORE + '\n\n' + INTRO + '\n\n' + PLAIN, INTRO),
            (BEFORE + '\n\\section{Another}\\label{section-basic}\n' + INTRO + '\n\n' + PLAIN, '')]:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = fixture(Path(tmp), native=native, other=other)
                with self.subTest(native=native, other=other), self.assertRaises(RecordError):
                    self.witness(Containers(root, harvest), units)

    def test_actual_distinct_sections_and_typed_math_do_not_gain_permission(self):
        native = BEFORE + '\n\\section{Other}\\label{section-other}\n' + INTRO + '\n\n' + PLAIN
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, _, _ = fixture(Path(tmp), native=native)
            containers = Containers(root, harvest)
            selected = containers.select({'file':'test.tex', 'owner_tag':'0005',
                'owner_label':'test-section-other', 'parent_tag':'0005', 'kind':'paragraph', 'ordinal':1})
            with self.assertRaises(RecordError): self.witness(containers, units, selected)
        math = r'$x\quad\text{and}\quad y$'
        for role in ['paragraph', 'following']:
            native = (BEFORE.replace('assertion.', 'assertion. ' + math) + '\n\n'
                      + INTRO.replace('$x$', math) + '\n\n' + PLAIN if role == 'paragraph'
                      else BEFORE + '\n\n' + INTRO + '\n\n' + PLAIN.replace('assertion.', 'assertion. ' + math))
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = fixture(Path(tmp), native=native)
                label = 'test-lemma-two' if role == 'paragraph' else 'test-lemma-one'
                p = root / 'config/macro-policy.yml'
                p.write_text(p.read_text() + '\ntranslatable_math_text:\n  connective-and:\n'
                    '    literal: "and"\n    command: "text"\n    usage: "quad-connector"\n'
                    + f'    source_label: "{label}"\n    witness_kind: "lemma"\n    witness_ordinal: 1\n')
                if role == 'paragraph': units[0]['placeholders']['MATH_0001'] = math
                else:
                    units[1]['source_text'] += ' <MATH_0001>'
                    units[1]['placeholders'] = {'MATH_0001': math}
                with self.subTest(role=role), self.assertRaises(RecordError):
                    self.witness(Containers(root, harvest), units)

    def test_complete_v4_replay_requires_all_original_inputs_and_all_five_fields(self):
        from stacks_zh.group_derivations import FIELDS, replay_groups, revision_group
        from stacks_zh.records import load_jsonl, placeholder_names
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, plan, output = fixture(Path(tmp), split=True)
            self.assertEqual(write_container_package(root, harvest, plan, output)['state'], 'PREPARED')
            records = json.loads((output / 'restorations.json').read_text())
            for source in records:
                for role, name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                    path = root / source['files'][role]['path']; path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((output / name).read_bytes())
                write(root / f"translation-data/source-container-restorations/{source['restoration_id']}.json", source)
            restored, errors = load_source_containers(root, harvest); self.assertFalse(errors)
            old = load_jsonl(output / 'input-candidates.jsonl')
            record = {k:records[0][k] for k in ['derivation_id','source_commit','origin_commit','created_at','files']}
            record['unit_groups'] = []; corrections = {}
            for source in records:
                group = {k:source[k] for k in ['group_id','input_unit_ids','output_unit_ids','reason']}
                group.update(identity_anchor=group['input_unit_ids'][0], output_units=source['new_units'],
                    source_container_restoration_id=source['restoration_id'], model_correction_id='synthetic-historical-revision')
                record['unit_groups'].append(group)
                inputs = [u for u in units if u['unit_id'] in group['input_unit_ids']]
                candidates = [c for c in old if c['unit_id'] in group['input_unit_ids']]
                for unit in source['new_units']:
                    raw = copy.deepcopy(candidates[0]); context = {'revision_input':revision_group(record, group, inputs, candidates)}
                    raw.update(unit_id=unit['unit_id'], context=context, context_hash=sha256_value(context),
                        translation=''.join('<'+name+'>' for name in placeholder_names(unit['source_text']))+'合成测试。')
                    raw['translation_hash'] = sha256_value(raw['translation'])
                    corrections[(group['model_correction_id'],unit['unit_id'])] = {'unit':unit,'candidate':raw,
                        'record':{'derivation_ids':{unit['unit_id']:record['derivation_id']},'source_commit':record['source_commit']}}
            tags = Containers(root, harvest).english.tags
            revised, candidates = replay_groups(record, units, old, corrections, None, restored, tags)
            self.assertEqual(len(revised), 2)
            self.assertTrue(all(c['publication_status']=='CANDIDATE' for c in candidates))
            for key in corrections:
                for field in [*sorted(FIELDS), 'revision', 'whole-old-group', 'human-approval']:
                    changed = copy.deepcopy(corrections)
                    if field in FIELDS: changed[key]['candidate'].pop(field)
                    if field == 'revision': changed.pop(key)
                    if field == 'whole-old-group': changed[key]['candidate']['context']['revision_input']['candidates'].pop()
                    if field == 'human-approval': changed[key]['candidate']['stage'] = 'MATH_REVIEWED'
                    with self.subTest(key=key, field=field), self.assertRaises((RecordError, KeyError)):
                        replay_groups(record, units, old, changed, None, restored, tags)

    def test_preparation_check_schema_and_actual_loader_recompute_every_witness_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, plan, output = fixture(Path(tmp), split=True)
            manifest = write_container_package(root, harvest, plan, output)
            self.assertEqual(manifest['state'], 'PREPARED')
            before = {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()}
            write_container_package(root, harvest, plan, output, check=True)
            self.assertEqual(before, {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in output.iterdir()})
            records = json.loads((output / 'restorations.json').read_text())
            source = next(r for r in records if r['tool']['version'] == 'source-container-v10')
            self.assertEqual(source['new_units'][0]['schema_version'], 1)
            self.assertFalse(validate_named_schema(source, 'source-container-restoration.schema.json', 'fixture'))
            for record in records:
                for role, name in [('input_units','input-units.jsonl'),('input_candidates','input-candidates.jsonl')]:
                    path = root / record['files'][role]['path']; path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((output / name).read_bytes())
                write(root / f"translation-data/source-container-restorations/{record['restoration_id']}.json", record)
            loaded, errors = load_source_containers(root, harvest)
            self.assertFalse(errors); self.assertEqual(len(loaded), 2)
            path = root / f"translation-data/source-container-restorations/{source['restoration_id']}.json"
            for field in source['legacy_boundary_witness']['paragraph_anchor']:
                bad = copy.deepcopy(source); value = bad['legacy_boundary_witness']['paragraph_anchor'][field]
                if isinstance(value, list): value.pop()
                elif isinstance(value, dict): value['owner_tag'] = '9999'
                else: bad['legacy_boundary_witness']['paragraph_anchor'][field] = 'sha256:' + '0' * 64 if field.endswith('hash') else '9999'
                self.assertFalse(validate_named_schema(bad, 'source-container-restoration.schema.json', 'valid-shaped tamper'))
                write(path, bad)
                with self.subTest(field=field):
                    self.assertTrue(any('legacy boundary witness differs' in error
                                        for error in load_source_containers(root, harvest)[1]))
            for version in [f'source-container-v{n}' for n in range(1,10)]:
                bad = copy.deepcopy(source); bad['tool']['version'] = version
                write(path, bad)
                with self.subTest(version=version): self.assertTrue(load_source_containers(root, harvest)[1])
            write(path, source); self.assertFalse(load_source_containers(root, harvest)[1])
