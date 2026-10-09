"""Synthetic legacy boundaries; never production translation or model output."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_derivations import fixture as candidate_fixture
from test_group_derivations import commit, run_for, save, write
from test_source_containers import fixture as english_fixture, git, old_unit, selector, paragraph_inputs
from stacks_zh.records import RecordError, sha256_value, stamp_unit_hashes
from stacks_zh.schema_validation import validate_named_schema
from stacks_zh.source_containers import (Containers, load_source_containers, lower_container,
    verify_old_group, write_container_package)
from stacks_zh.source_reextractions import source_tex

PLAIN = '\\begin{lemma}\n\\label{lemma-one}\nA complete assertion.\n\\end{lemma}'
LIST = ('\\begin{lemma}\n\\label{lemma-one}\nChoose two objects.\n\\begin{enumerate}\n'
        '\\item\n\\label{item-first}\nFirst object.\n'
        '\\item\n\\label{item-second}\nSecond object.\n\\end{enumerate}\n\\end{lemma}')
INTRO = '\\noindent\nAn introductory\nparagraph with $x$.'


def fixture(base, family='secondary', *, statement=None, typed=False):
    native = LIST if family == 'secondary' else INTRO + '\n\n' + PLAIN
    kwargs = {}
    if typed:
        from test_math_text import PROOF, policy_text
        kwargs['proof'] = PROOF
    root, harvest, _ = english_fixture(base, statement=statement or native, **kwargs)
    if typed:
        (root / 'config/macro-policy.yml').write_text(policy_text())
    tags = harvest / 'tags/tags'
    tags.write_text(tags.read_text() + '0003,test-item-first\n0004,test-item-second\n')
    git(harvest, 'add', '.')
    git(harvest, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'synthetic labelled items')
    source = git(harvest, 'rev-parse', 'HEAD')
    (root / 'upstream.lock').write_text(f'commit = "{source}"\n')
    if family == 'secondary':
        units = [old_unit(source, 'tag:0001:statement', 'lemma', 'Choose two objects.',
                          '\\begin{lemma}\n\\label{test-lemma-one}\n', '\n\\begin{enumerate}\n'),
                 old_unit(source, 'tag:0003', 'list_item', 'First object.',
                          '\\item\n\\label{test-item-first}\n', '\n'),
                 old_unit(source, 'tag:0004', 'list_item', 'Second object.',
                          '\\item\n\\label{test-item-second}\n', '\n\\end{enumerate}\n\\end{lemma}\n')]
        for unit, parent in zip(units, ['0001', '0003', '0004'], strict=True):
            unit['parent_tag'] = parent
        groups = [('statement', units[:], selector('lemma'))]
    else:
        intro = paragraph_inputs(source)[1]
        intro.update(unit_id='label:test-lemma-one:intro', parent_tag='0002')
        statement_unit = old_unit(source, 'tag:0001:statement', 'lemma', 'A complete assertion.',
                                  '\\begin{lemma}\n\\label{test-lemma-one}\n', '\n\\end{lemma}')
        statement_unit['parent_tag'] = '0002'
        units = [intro, statement_unit]
        groups = [('intro', units[:1], selector('paragraph', owner='0000')),
                  ('statement', units[1:], selector('lemma'))]
    proof = [old_unit(source, 'tag:0001:proof-p001', 'proof', 'First old proof segment.', '\\begin{proof}\n'),
             old_unit(source, 'tag:0001:proof-p002', 'proof', 'Last old proof segment.', '', '\n\\end{proof}')]
    for unit in proof:
        unit['parent_tag'] = units[0]['parent_tag']
    units += proof
    groups.append(('proof', proof, selector()))
    units = [stamp_unit_hashes(unit) for unit in units]
    template = candidate_fixture()[2][0]
    candidates = []
    for unit in units:
        context = {'unit_id': unit['unit_id'], 'source_commit': source,
                   'prompt_version': 'fixture', 'policy_revision': 'fixture'}
        candidate = copy.deepcopy(template)
        candidate.update(unit_id=unit['unit_id'], source_commit=source,
            source_text_hash=unit['source_text_hash'], context=context, context_hash=sha256_value(context),
            run_id='fixture-boundary-run', translation='<MATH_0001>合成测试。' if unit['placeholders'] else '合成测试。',
            allowed_english=[], term_occurrences=[], unknown_terms=[], notes=['Synthetic fixture only.'],
            term_status='CLEAR', stage='TERM_OK', qa_status='PASS', publication_status='CANDIDATE')
        candidate['translation_hash'] = sha256_value(candidate['translation'])
        candidates.append(candidate)
    up = 'translation-data/units/test-boundary.jsonl'
    cp = 'translation-data/candidates/fixture/test-boundary.jsonl'
    save(root, up, units); save(root, cp, candidates)
    write(root / 'translation-data/runs/fixture-boundary-run.json',
          run_for(candidates, source, 'translation', 'fixture-boundary-run'))
    git(root, 'init', '-q'); commit(root)
    plan = {'derivation_id': 'fixture-boundary', 'created_at': '2026-10-10T00:00:00Z',
            'units_file': up, 'candidates_file': cp, 'groups': []}
    for name, members, coordinate in groups:
        ids = [unit['unit_id'] for unit in members]
        plan['groups'].append({'group_id': name, 'input_unit_ids': ids, 'identity_anchor': ids[0],
            'selector': coordinate, 'layout': 'whole', 'reason': 'Complete synthetic boundary; never adopted.'})
    plan_path = root / 'build/plan.json'; write(plan_path, plan)
    return root, harvest, units, plan_path, root / 'build/package'


class BoundaryTests(unittest.TestCase):
    def test_witnessed_typed_proof_keeps_complete_model_revision_and_approval_gates(self):
        from stacks_zh.group_derivations import FIELDS, replay_groups, revision_group
        from stacks_zh.records import load_jsonl, placeholder_names
        from test_math_text import synthetic_translation
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, old_units, plan, output = fixture(Path(tmp), typed=True)
            self.assertEqual(write_container_package(root, harvest, plan, output)['state'], 'PREPARED')
            records = json.loads((output / 'restorations.json').read_text())
            self.assertEqual({r['tool']['version'] for r in records}, {'source-container-v4'})
            self.assertTrue(any(u['schema_version'] == 2 for r in records for u in r['new_units']))
            for source in records:
                for role, name in [('input_units','input-units.jsonl'), ('input_candidates','input-candidates.jsonl')]:
                    path = root / source['files'][role]['path']; path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((output / name).read_bytes())
                write(root / f"translation-data/source-container-restorations/{source['restoration_id']}.json", source)
            restored, errors = load_source_containers(root, harvest)
            self.assertEqual(errors, [])
            old_candidates = load_jsonl(output / 'input-candidates.jsonl')
            record = {k: records[0][k] for k in ['derivation_id','source_commit','origin_commit','created_at','files']}
            record['unit_groups'] = []
            corrections = {}
            for source in records:
                group = {k:source[k] for k in ['group_id','input_unit_ids','output_unit_ids','reason']}
                group.update(identity_anchor=group['input_unit_ids'][0], output_units=source['new_units'],
                             source_container_restoration_id=source['restoration_id'], model_correction_id='synthetic-boundary-revision')
                record['unit_groups'].append(group)
                inputs = [u for u in old_units if u['unit_id'] in group['input_unit_ids']]
                candidates = [c for c in old_candidates if c['unit_id'] in group['input_unit_ids']]
                for unit in group['output_units']:
                    raw = copy.deepcopy(candidates[0])
                    context = {'revision_input':revision_group(record, group, inputs, candidates)}
                    raw.update(unit_id=unit['unit_id'], context=context, context_hash=sha256_value(context),
                        translation=synthetic_translation(unit).replace('Café δ.', '合成测试。') if unit['schema_version'] == 2 else
                            ''.join('<'+name+'>' for name in placeholder_names(unit['source_text']))+'合成测试。')
                    raw['translation_hash'] = sha256_value(raw['translation'])
                    if unit['schema_version'] == 2:
                        raw.update(term_occurrences=[{'source_term':'affine opens','target_term':'仿射开集'}]*2,
                            unknown_terms=[{'source_term':'affine opens','target_term':'仿射开集','context':'Synthetic pending term.'}],
                            term_status='DECISION_REQUIRED', stage='STRUCTURE_OK')
                    corrections[(group['model_correction_id'], unit['unit_id'])] = {'unit':unit,'candidate':raw,
                        'record':{'derivation_ids':{unit['unit_id']:record['derivation_id']},'source_commit':record['source_commit']}}
            tags = Containers(root, harvest).english.tags
            revised, candidates = replay_groups(record, old_units, old_candidates, corrections, None, restored, tags)
            self.assertEqual(len(revised), 2)
            self.assertTrue(all(c['publication_status']=='CANDIDATE' for c in candidates))
            key = next(k for k,v in corrections.items() if v['unit']['schema_version']==2)
            for fault in [*sorted(FIELDS), 'missing-revision', 'partial-old-context', 'human-approval', 'old-container']:
                changed, sources = copy.deepcopy(corrections), copy.deepcopy(restored)
                if fault in FIELDS: changed[key]['candidate'].pop(fault)
                if fault=='missing-revision': changed.pop(key)
                if fault=='partial-old-context': changed[key]['candidate']['context']['revision_input']['source_units'].pop()
                if fault=='human-approval': changed[key]['candidate']['stage']='MATH_REVIEWED'
                if fault=='old-container':
                    source_id=record['unit_groups'][-1]['source_container_restoration_id']
                    sources[source_id]['record']['tool']['version']='source-container-v2'
                with self.subTest(fault=fault), self.assertRaises((RecordError, KeyError)):
                    replay_groups(record, old_units, old_candidates, changed, None, sources, tags)

    def test_complete_secondary_statement_and_proof_need_independent_native_witness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, _, _ = fixture(Path(tmp))
            containers = Containers(root, harvest)
            for coordinate, members in [(selector('lemma'), units[:3]), (selector(), units[3:])]:
                selected = containers.select(coordinate)
                ids = [unit['unit_id'] for unit in members]
                with self.assertRaises(RecordError):
                    verify_old_group(units, containers.english.tags, ids, selected, allow_outer_whitespace=True)
                witness = verify_old_group(units, containers.english.tags, ids, selected,
                                           native_containers=containers)
                self.assertEqual(witness['secondary_statements'][0]['native_item_tags'], ['0003', '0004'])
                self.assertEqual(witness['secondary_statements'][0]['statement_input_unit_ids'],
                                 [unit['unit_id'] for unit in units[:3]])
                self.assertEqual(source_tex(lower_container(selected, containers.policy)[0]), selected['fragment'])

    def test_secondary_rejects_arbitrary_scope_fake_labels_and_partial_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, original, _, _ = fixture(Path(tmp))
            containers = Containers(root, harvest); selected = containers.select(selector('lemma'))
            for fault in ['parent', 'chapter', 'source', 'kind', 'fake-item', 'math-label', 'borrow-label',
                          'reorder', 'duplicate', 'unclosed', 'nested-owner', 'comment-close', 'math-close']:
                units = copy.deepcopy(original)
                if fault == 'parent': units[1]['parent_tag'] = '0002'
                if fault == 'chapter': units[1]['chapter'] = 'other'
                if fault == 'source': units[1]['source_commit'] = '1' * 40
                if fault == 'kind': units[1]['node_kind'] = 'paragraph'
                if fault == 'fake-item': units[1]['render']['prefix'] = '\\footnote{\\item\\label{test-item-first}}'
                if fault == 'math-label': units[1]['render']['prefix'] = '$\\item\\label{test-item-first}$'
                if fault == 'borrow-label':
                    units[1].update(parent_tag='0002', render={'prefix':'\\item\\label{test-lemma-two}', 'suffix':'\n'})
                if fault == 'reorder': units[1], units[2] = units[2], units[1]
                if fault == 'duplicate': units[2]['unit_id'] = units[1]['unit_id']
                if fault == 'unclosed': units[2]['render']['suffix'] = '\n'
                if fault == 'nested-owner': units[1]['render']['prefix'] += '\\begin{lemma}\\label{test-lemma-two}'
                if fault == 'comment-close': units[2]['render']['suffix'] = '\n\\end{enumerate}\n%\\end{lemma}\n'
                if fault == 'math-close': units[2]['render']['suffix'] = '\n\\end{enumerate}\n$\\end{lemma}$\n'
                with self.subTest(fault=fault), self.assertRaises(RecordError):
                    verify_old_group(units, containers.english.tags, [unit['unit_id'] for unit in units[:3]],
                                     selected, native_containers=containers)
            for ids in [[u['unit_id'] for u in original[:2]], [u['unit_id'] for u in original[:3]][::-1]]:
                with self.assertRaises(RecordError):
                    verify_old_group(original, containers.english.tags, ids, selected, native_containers=containers)

    def test_math_comment_literal_and_parameter_labels_are_not_native_items(self):
        for fake in ['$\\item\\label{item-first}$', '%\\item\\label{item-first}\n',
                     '\\begin{verbatim}\\item\\label{item-first}\\end{verbatim}',
                     '\\footnote{\\item\\label{item-first}}']:
            native = LIST.replace('\\item\n\\label{item-first}', fake + '\\item')
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = fixture(Path(tmp), statement=native)
                containers = Containers(root, harvest)
                with self.subTest(fake=fake), self.assertRaises(RecordError):
                    selected = containers.select(selector('lemma'))
                    verify_old_group(units, containers.english.tags, [u['unit_id'] for u in units[:3]],
                                     selected, native_containers=containers)

    def test_complete_paragraph_can_bind_its_real_following_statement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, units, _, _ = fixture(Path(tmp), 'paragraph')
            containers = Containers(root, harvest); selected = containers.select(selector('paragraph', owner='0000'))
            with self.assertRaises(RecordError):
                verify_old_group(units, containers.english.tags, [units[0]['unit_id']], selected,
                                 allow_outer_whitespace=True)
            witness = verify_old_group(units, containers.english.tags, [units[0]['unit_id']], selected,
                                       native_containers=containers)
            self.assertEqual(witness['paragraph_anchor']['historical_parent_tag'], '0002')
            self.assertEqual(witness['paragraph_anchor']['following_statement_selector'], selector('lemma'))
            self.assertEqual(source_tex(lower_container(selected, containers.policy)[0]), INTRO)

    def test_paragraph_rejects_text_math_reference_command_unicode_and_scope_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, original, _, _ = fixture(Path(tmp), 'paragraph')
            containers = Containers(root, harvest); selected = containers.select(selector('paragraph', owner='0000'))
            for fault in ['words', 'slice', 'math', 'reference', 'command', 'unicode', 'blank', 'parent',
                          'owner', 'missing-statement', 'fake-statement', 'chapter', 'source']:
                units = copy.deepcopy(original); paragraph = units[0]
                if fault == 'words': paragraph['source_text'] += ' Added.'
                if fault == 'slice': paragraph['source_text'] = 'paragraph with <MATH_0001>.'
                if fault == 'math': paragraph['placeholders']['MATH_0001'] = '$y$'
                if fault == 'reference': paragraph['render']['suffix'] += '\\ref{test-lemma-one}'
                if fault == 'command': paragraph['render']['prefix'] = '\\medskip\n'
                if fault == 'unicode': paragraph['source_text'] = paragraph['source_text'].replace(' ', '\u00a0', 1)
                if fault == 'blank': paragraph['source_text'] = paragraph['source_text'].replace('paragraph', '\n\nparagraph')
                if fault == 'parent': paragraph['parent_tag'] = '0001'
                if fault == 'owner': units[1]['render']['prefix'] = '\\begin{lemma}\\label{test-lemma-two}'
                if fault == 'missing-statement': units.pop(1)
                if fault == 'fake-statement': units[1]['render']['prefix'] = '$\\begin{lemma}\\label{test-lemma-one}$'
                if fault == 'chapter': paragraph['chapter'] = 'other'
                if fault == 'source': paragraph['source_commit'] = '1' * 40
                with self.subTest(fault=fault), self.assertRaises(RecordError):
                    verify_old_group(units, containers.english.tags, [paragraph['unit_id']], selected,
                                     native_containers=containers)

    def test_repeated_paragraph_and_wrong_native_section_are_not_witnesses(self):
        for native in [INTRO + '\n\n' + INTRO + '\n\n' + PLAIN,
                       INTRO + '\n\n\\section{Other}\\label{lemma-two}\n' + PLAIN]:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, units, _, _ = fixture(Path(tmp), 'paragraph', statement=native)
                containers = Containers(root, harvest)
                with self.assertRaises(RecordError):
                    selected = containers.select(selector('paragraph', owner='0000'))
                    verify_old_group(units, containers.english.tags, [units[0]['unit_id']], selected,
                                     native_containers=containers)

    def test_packages_are_read_only_versioned_and_witnesses_are_rederived(self):
        for family in ['secondary', 'paragraph']:
            with tempfile.TemporaryDirectory() as tmp:
                root, harvest, _, plan, output = fixture(Path(tmp), family)
                before = {p.relative_to(root):p.read_bytes() for p in (root / 'translation-data').rglob('*') if p.is_file()}
                manifest = write_container_package(root, harvest, plan, output)
                self.assertEqual(manifest['state'], 'PREPARED')
                self.assertEqual(write_container_package(root, harvest, plan, output, check=True), manifest)
                self.assertEqual(before, {p.relative_to(root):p.read_bytes() for p in (root / 'translation-data').rglob('*') if p.is_file()})
                records = json.loads((output / 'restorations.json').read_text())
                boundary = next(record for record in records if record['tool']['version'] == 'source-container-v4')
                self.assertIn('legacy_boundary_witness', boundary)
                for record in records:
                    for role, name in [('input_units','input-units.jsonl'), ('input_candidates','input-candidates.jsonl')]:
                        path = root / record['files'][role]['path']; path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes((output / name).read_bytes())
                    write(root / f"translation-data/source-container-restorations/{record['restoration_id']}.json", record)
                self.assertEqual(load_source_containers(root, harvest)[1], [])
                path = root / f"translation-data/source-container-restorations/{boundary['restoration_id']}.json"
                for fault in ['missing', 'old-version', 'false-witness', 'unneeded-version']:
                    record = copy.deepcopy(boundary)
                    if fault == 'missing': record.pop('legacy_boundary_witness')
                    if fault == 'old-version':
                        record['tool']['version'] = 'source-container-v2'; record.pop('legacy_boundary_witness')
                    if fault == 'false-witness':
                        record['legacy_boundary_witness']['paragraph_anchor'] = None
                        record['legacy_boundary_witness']['secondary_statements'] = []
                    if fault == 'unneeded-version': record['legacy_boundary_witness']['unexpected'] = True
                    write(path, record)
                    with self.subTest(family=family, fault=fault):
                        self.assertTrue(load_source_containers(root, harvest)[1])
                        if fault in {'missing', 'unneeded-version'}:
                            self.assertTrue(validate_named_schema(record, 'source-container-restoration.schema.json', 'fixture'))
                corrupt = copy.deepcopy(boundary)
                witness = corrupt['legacy_boundary_witness']
                if family == 'secondary': witness['secondary_statements'][0]['native_item_tags'].reverse()
                else: witness['paragraph_anchor']['paragraph_signature_hash'] = 'sha256:' + '0' * 64
                self.assertFalse(validate_named_schema(corrupt, 'source-container-restoration.schema.json', 'fixture'))
                write(path, corrupt)
                self.assertTrue(any('boundary witness differs' in e for e in load_source_containers(root, harvest)[1]))


if __name__ == '__main__':
    unittest.main()
