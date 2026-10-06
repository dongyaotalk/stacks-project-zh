"""Synthetic complete history; outputs explicitly are fixture data, not model runs."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from test_derivations import fixture as candidate_fixture
from test_source_containers import fixture as english_fixture, git, old_unit, selector, PROOF
from stacks_zh.derivations import clean, jsonl_bytes, load_repository_derivations, replay_derivation
from stacks_zh.group_derivations import FIELDS, revision_group
from stacks_zh.model_corrections import candidate_provenance_hash, load_repository_corrections
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import RecordError, load_jsonl, sha256_value, stamp_unit_hashes, placeholder_names
from stacks_zh.schema_validation import validate_repository_schemas
from stacks_zh.source_containers import Containers, VERSION, load_source_containers, lower_container
from stacks_zh.source_reextractions import byte_hash, source_tex
from stacks_zh.workflow import render_batch


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def read(path):
    return json.loads(path.read_text())


def save(root, path, rows):
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(jsonl_bytes(rows))
    return {'path': path, 'hash': byte_hash(destination.read_bytes())}


def commit(root):
    git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid', 'add', '.')
    git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'synthetic Chinese history')
    return git(root, 'rev-parse', 'HEAD')


def run_for(rows, source, kind, identifier):
    row = rows[0]
    return {'schema_version': 1, 'run_id': identifier, 'run_kind': kind, 'task_id': 'synthetic-fixture',
        'source_commit': source, 'unit_ids': [r['unit_id'] for r in rows],
        'harness': {'id': row['harness_id'], 'version': row['harness_version'], 'adapter_version': 'fixture'},
        'model': {'record_id': row['model_record_id'], 'provider': 'Fixture', 'requested_id': row['model_id'],
                  'resolved_id': row['model_id'], 'snapshot': None, 'identity_confidence': 'declared'},
        'inputs': {'prompt_version': row['prompt_version'], 'policy_revision': 'fixture',
                   'glossary_revision': row['glossary_revision'], 'context_hashes': [r['context_hash'] for r in rows]},
        'created_at': row['created_at'], 'replayable': False}


def fixture(base, count=1, legacy=False, proof=None, detached=False):
    root, harvest, source = english_fixture(base, **({'proof':proof} if proof is not None else {}))
    _, _, candidate_template = candidate_fixture()
    template = candidate_template[0]
    units = [old_unit(source, 'tag:0000:title', 'section_title', 'Basics', '\\section{', '}\n\\label{section-basic}'),
             old_unit(source, 'tag:0001:statement', 'lemma', 'An old incomplete statement.',
                      '\\begin{lemma}\n\\label{test-lemma-one}\n', '\n\\end{lemma}'),
             old_unit(source, 'tag:0001:proof-p001', 'proof', 'First old segment.', '\\begin{proof}\n'),
             old_unit(source, 'tag:0001:proof-p002', 'paragraph', 'Second old segment.', '', '\n\\end{proof}')]
    if detached:
        display = old_unit(source, 'tag:0001:display001', 'display_math', '<MATH_0001>')
        display['placeholders'] = {'MATH_0001': r'\[x \to y \to z\]'}
        units.insert(2, stamp_unit_hashes(display))
    candidates = []
    for index, unit in enumerate(units):
        model = 'fixture-model-b' if index == 3 else 'fixture-model-a'
        context = {'unit_id': unit['unit_id'], 'prompt_version': 'fixture', 'policy_revision': 'fixture', 'source_commit': source}
        row = copy.deepcopy(template)
        row.update(unit_id=unit['unit_id'], source_commit=source, source_text_hash=unit['source_text_hash'],
                   model_id=model, model_lane='fixture', model_record_id='fixture:' + model + ':declared',
                   run_id=model + '-run', context=context, context_hash=sha256_value(context),
                   translation=''.join('<' + n + '>' for n in placeholder_names(unit['source_text'])) + '旧译文。',
                   allowed_english=[], term_occurrences=[], unknown_terms=[], notes=['Synthetic fixture only.'],
                   term_status='CLEAR', stage='TERM_OK', qa_status='PASS', publication_status='CANDIDATE')
        row['translation_hash'] = sha256_value(row['translation'])
        candidates.append(row)
    output_paths = {'output_units': 'translation-data/units/test-0000.jsonl',
                    'output_candidates': 'translation-data/candidates/fixture/test-0000.jsonl'}
    for role, rows in [('output_units', units), ('output_candidates', candidates)]:
        save(root, output_paths[role], rows)
    for run_id in {c['run_id'] for c in candidates}:
        rows = [c for c in candidates if c['run_id'] == run_id]
        write(root / f'translation-data/runs/{run_id}.json', run_for(rows, source, 'translation', run_id))
    git(root, 'init', '-q')
    commit(root)
    previous = None
    records = []
    for number in range(1, count + 1):
        old_units, old_candidates = units, candidates
        identifier, correction_id = f'fixture-group-{number}', f'fixture-revision-{number}'
        version = ('1' if legacy == '1' and number == 1 else
                   '2' if legacy and number == 1 else
                   '3' if legacy == '3' and number == 2 else '4')
        record = {'schema_version': 1, 'derivation_id': identifier, 'source_commit': source,
            'created_at': f'2026-10-06T0{number}:00:00Z', 'origin_commit': git(root, 'rev-parse', 'HEAD'),
            'tool': {'id': 'stacks-zh-derive', 'version': version}, 'files': {}}
        if previous:
            record['previous_derivation_id'] = previous['derivation_id']
            archive = {'schema_version': 1, 'prior_derivation_id': previous['derivation_id'],
                'successor_derivation_id': identifier, 'source_commit': source, 'origin_commit': record['origin_commit'],
                'created_at': record['created_at'], 'record': {'path': f"translation-data/derivations/{previous['derivation_id']}.json",
                    'hash': byte_hash((root / f"translation-data/derivations/{previous['derivation_id']}.json").read_bytes())}, 'files': {}}
            for role in ['output_units', 'output_candidates']:
                name = role.replace('_', '-')
                path = f"translation-data/retired/derivations/{previous['derivation_id']}/{name}.jsonl"
                archive['files'][role] = save(root, path, old_units if role == 'output_units' else old_candidates)
            write(root / f"translation-data/derivation-archives/{previous['derivation_id']}.json", archive)
        for role, rows in [('input_units', old_units), ('input_candidates', old_candidates)]:
            record['files'][role] = save(root, f'translation-data/retired/derivations/{identifier}/{"units" if role == "input_units" else "candidates"}.jsonl', rows)
        for role, path in output_paths.items():
            record['files'][role] = {'path': path, 'hash': 'sha256:' + '0' * 64}
        containers = Containers(root, harvest)
        if record['tool']['version'] == '4':
            groups = [{'group_id': 'heading', 'input_unit_ids': [old_units[0]['unit_id']],
                'output_unit_ids': [old_units[0]['unit_id']], 'output_units': [old_units[0]],
                'identity_anchor': old_units[0]['unit_id'], 'reason': 'Keep complete heading.',
                'model_correction_id': correction_id, 'source_container_restoration_id': None}]
            statement_ids = [u['unit_id'] for u in old_units if u['node_kind'] in {'lemma', 'environment_title'}]
            proof_ids = [u['unit_id'] for u in old_units if u['unit_id'] not in [old_units[0]['unit_id'], *statement_ids]]
            for group_id, ids, coordinate in [('statement', statement_ids, selector('lemma')), ('proof', proof_ids, selector())]:
                selected = containers.select(coordinate)
                layout = 'split-title' if group_id == 'statement' and number % 2 else 'whole'
                new_units = lower_container(selected, containers.policy, layout=layout)
                restoration_id = f'{identifier}-{group_id}'
                group = {'group_id': group_id, 'input_unit_ids': ids, 'output_unit_ids': [u['unit_id'] for u in new_units],
                    'output_units': new_units, 'identity_anchor': ids[0], 'reason': 'Complete synthetic Git container.',
                    'model_correction_id': correction_id, 'source_container_restoration_id': restoration_id}
                evidence = {k: copy.deepcopy(selected[k]) for k in ['selector', 'source_commit', 'fragment', 'location', 'blob_oid', 'blob_hash', 'macro_policy_hash', 'boundary_witness']}
                evidence.update(schema_version=1, restoration_id=restoration_id, derivation_id=identifier, group_id=group_id,
                    created_at=record['created_at'], origin_commit=record['origin_commit'],
                    tool={'id': 'stacks-zh-source-container', 'version': VERSION}, layout=layout,
                    input_unit_ids=ids, output_unit_ids=group['output_unit_ids'], new_units=new_units,
                    reason=group['reason'], files={k:record['files'][k] for k in ['input_units', 'input_candidates']})
                write(root / f'translation-data/source-container-restorations/{restoration_id}.json', evidence)
                groups.append(group)
            record['unit_groups'] = groups
            units = [u for g in groups for u in g['output_units']]
        else:
            units = copy.deepcopy(old_units)
            record['unit_id_map'] = {u['unit_id']: u['unit_id'] for u in old_units}
        if version == '1':
            record['operations'] = []
            units, candidates = replay_derivation(record, old_units, old_candidates)
            for role, rows in [('output_units', units), ('output_candidates', candidates)]:
                record['files'][role] = save(root, output_paths[role], rows)
            write(root / f'translation-data/derivations/{identifier}.json', record)
            records.append(record)
            previous = record
            if number < count:
                commit(root)
            continue
        raw = []
        for unit in units:
            if record['tool']['version'] == '4':
                group = next(g for g in groups if unit['unit_id'] in g['output_unit_ids'])
                old_group_units = [u for u in old_units if u['unit_id'] in group['input_unit_ids']]
                old_group_candidates = [c for c in old_candidates if c['unit_id'] in group['input_unit_ids']]
                revision = revision_group(record, group, old_group_units, old_group_candidates)
            else:
                old = next(u for u in old_units if u['unit_id'] == unit['unit_id'])
                candidate = next(c for c in old_candidates if c['unit_id'] == unit['unit_id'])
                revision = {'kind':'candidate-to-revise', 'source_unit':old, 'candidate':candidate}
            context = {'unit_id': unit['unit_id'], 'source_unit': unit, 'source_commit': source,
                       'prompt_version': 'fixture', 'policy_revision': 'fixture', 'revision_input': revision}
            row = copy.deepcopy(template)
            row.update(unit_id=unit['unit_id'], source_commit=source, source_text_hash=unit['source_text_hash'],
                context=context, context_hash=sha256_value(context), translation=''.join('<' + n + '>' for n in unit['placeholders']) + '合成测试。',
                model_id=f'fixture-revision-model-{number}', model_lane=f'revision-{number}',
                model_record_id=f'fixture:revision-{number}:declared', run_id=f'fixture-revision-run-{number}',
                created_at=record['created_at'], allowed_english=[], term_occurrences=[], unknown_terms=[],
                notes=['Synthetic fixture, never actual model output.'], term_status='CLEAR', stage='TERM_OK',
                qa_status='PASS', publication_status='CANDIDATE')
            # Placeholder order comes from the source, never dictionary order.
            row['translation'] = ''.join('<' + n + '>' for n in placeholder_names(unit['source_text'])) + '合成测试。'
            row['translation_hash'] = sha256_value(row['translation'])
            raw.append(row)
        if record['tool']['version'] != '4':
            record['operations'] = [{'unit_id': u['unit_id'], 'kinds':['model-revision'], 'reason':'Synthetic predecessor.',
                'unit_updates':{}, 'candidate_updates': {f:r[f] for f in FIELDS}, 'model_correction_id': correction_id}
                for u,r in zip(units,raw,strict=True)]
        correction = {'schema_version':1, 'correction_id':correction_id, 'source_commit':source,
            'created_at':record['created_at'], 'run_id':raw[0]['run_id'], 'unit_ids':[u['unit_id'] for u in units],
            'derivation_ids': {u['unit_id']:identifier for u in units}, 'files':{}}
        for role, rows in [('units', units), ('candidates', raw)]:
            correction['files'][role] = save(root, f'translation-data/retired/model-corrections/{correction_id}/{role}.jsonl', rows)
        write(root / f'translation-data/model-corrections/{correction_id}.json', correction)
        write(root / f"translation-data/runs/{raw[0]['run_id']}.json", run_for(raw, source, 'revision', raw[0]['run_id']))
        corrections, errors = load_repository_corrections(root)
        restored, source_errors = load_source_containers(root, harvest)
        assert not errors + source_errors, errors + source_errors
        units, candidates = replay_derivation(record, old_units, old_candidates, corrections,
            (old_units, old_candidates) if previous else None, source_containers=restored, tags=containers.english.tags)
        for role, rows in [('output_units', units), ('output_candidates', candidates)]:
            record['files'][role] = save(root, output_paths[role], rows)
        write(root / f'translation-data/derivations/{identifier}.json', record)
        records.append(record)
        previous = record
        if number < count:
            commit(root)
    return root, harvest, records


class GroupDerivationTests(unittest.TestCase):
    def test_detached_display_full_history_replays_without_separate_current_math_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp), count=2, detached=True)
            self.assertEqual(validate_repository_schemas(root), [])
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            first = records[0]
            group = next(g for g in first['unit_groups'] if g['group_id'] == 'proof')
            self.assertEqual(group['input_unit_ids'], ['tag:0001:display001', 'tag:0001:proof-p001', 'tag:0001:proof-p002'])
            self.assertEqual(group['output_unit_ids'], ['tag:0001:proof'])
            frozen = load_jsonl(root / first['files']['input_units']['path'])
            self.assertIn('tag:0001:display001', [u['unit_id'] for u in frozen])
            current = load_jsonl(root / records[-1]['files']['output_units']['path'])
            self.assertNotIn('tag:0001:display001', [u['unit_id'] for u in current])
            proof = next(u for u in current if u['node_kind'] == 'proof')
            self.assertEqual(source_tex(proof), PROOF)
            self.assertEqual(source_tex(proof).count(r'\[x \to y \to z\]'), 1)
            origins, errors = load_repository_derivations(root, harvest=harvest)
            self.assertEqual(errors, [])
            key = records[-1]['files']['output_candidates']['path'], 'tag:0001:proof'
            self.assertEqual({c['unit_id'] for c in origins[key]['_all_origins']},
                             {'tag:0001:display001', 'tag:0001:proof-p001', 'tag:0001:proof-p002'})

    def test_complete_split_merge_history_retains_non_anchor_origins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp), count=3)
            self.assertEqual(validate_repository_schemas(root), [])
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            origins, errors = load_repository_derivations(root, harvest=harvest)
            self.assertEqual(errors, [])
            key = records[-1]['files']['output_candidates']['path'], 'tag:0001:proof'
            self.assertEqual({c['model_id'] for c in origins[key]['_all_origins']}, {'fixture-model-a', 'fixture-model-b'})
            for number, count in [(1, 4), (2, 3), (3, 4)]:
                self.assertEqual(sum(len(g['output_unit_ids']) for g in records[number-1]['unit_groups']), count)
            current = clean(load_jsonl(root / key[0])[-1])
            self.assertEqual(current['model_id'], 'fixture-model-a')
            self.assertEqual(current['unit_group_id'], 'proof')
            self.assertIn('candidate-group-to-revise', json.dumps(current['context']))

    def test_legacy_v2_then_grouped_source_restoration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp), count=3, legacy=True)
            self.assertEqual(records[0]['tool']['version'], '2')
            self.assertEqual(validate_repository_provenance(root, harvest), [])

    def test_legacy_v1_and_v3_ancestors_then_grouped_restoration(self):
        for version in ['1', '3']:
            with self.subTest(version=version), tempfile.TemporaryDirectory() as tmp:
                root, harvest, records = fixture(Path(tmp), count=3, legacy=version)
                self.assertIn(version, [r['tool']['version'] for r in records])
                self.assertEqual(records[-1]['tool']['version'], '4')
                self.assertEqual(validate_repository_schemas(root), [])
                self.assertEqual(validate_repository_provenance(root, harvest), [])

    def test_every_raw_field_run_identity_and_approval_are_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp))
            path = root / 'translation-data/model-corrections/fixture-revision-1.json'
            correction = read(path)
            snapshot = root / correction['files']['candidates']['path']
            original = [clean(row) for row in load_jsonl(snapshot)]
            for fault in [*sorted(FIELDS), 'run_id', 'harness_version', 'model_id', 'source_commit', 'stage', 'term-approval']:
                rows = copy.deepcopy(original)
                if fault in FIELDS:
                    rows[-1].pop(fault)
                elif fault == 'stage':
                    rows[-1]['stage'] = 'LANGUAGE_REVIEWED'
                elif fault == 'term-approval':
                    rows[-1]['unknown_terms'] = [{'source_term':'category', 'target_term':'范畴', 'context':'Synthetic pending.'}]
                    rows[-1]['term_status'] = 'CLEAR'
                else:
                    rows[-1][fault] = 'unrelated'
                changed = copy.deepcopy(correction)
                changed['files']['candidates'] = save(root, snapshot.relative_to(root).as_posix(), rows)
                write(path, changed)
                with self.subTest(fault=fault):
                    self.assertTrue(load_repository_corrections(root)[1])
            save(root, snapshot.relative_to(root).as_posix(), original)
            write(path, correction)
            self.assertEqual(validate_repository_provenance(root, harvest), [])

    def test_rehashed_source_kind_risk_math_and_owner_tampering_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, _ = fixture(Path(tmp))
            path = root / 'translation-data/source-container-restorations/fixture-group-1-proof.json'
            original = read(path)
            for fault in ['kind', 'risk', 'math', 'fragment', 'owner', 'boundary']:
                record = copy.deepcopy(original)
                if fault == 'kind': record['new_units'][0]['node_kind'] = 'paragraph'
                if fault == 'risk': record['new_units'][0]['risk_level'] = 'R1'
                if fault == 'math':
                    name = next(n for n in record['new_units'][0]['placeholders'] if n.startswith('MATH_'))
                    record['new_units'][0]['placeholders'][name] += ' '
                if fault == 'fragment':
                    record['fragment'] = record['fragment'].replace('Take', 'Ignore')
                    record['location']['fragment_hash'] = byte_hash(record['fragment'])
                if fault == 'owner': record['selector']['owner_tag'] = '0002'
                if fault == 'boundary': record['location']['byte_start'] += 1
                from stacks_zh.records import stamp_unit_hashes
                record['new_units'] = [stamp_unit_hashes(u) for u in record['new_units']]
                write(path, record)
                with self.subTest(fault=fault):
                    self.assertTrue(load_source_containers(root, harvest)[1])
            write(path, original)
            self.assertEqual(validate_repository_provenance(root, harvest), [])

    def test_history_immutability_orphans_cycles_and_active_collision_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp), count=2)
            archive_path = root / 'translation-data/derivation-archives/fixture-group-1.json'
            archive_bytes = archive_path.read_bytes()
            archive = read(archive_path)
            archive['files']['output_units']['hash'] = 'sha256:' + '1' * 64
            write(archive_path, archive)
            self.assertTrue(validate_repository_provenance(root, harvest))
            archive_path.write_bytes(archive_bytes)
            first_path = root / 'translation-data/source-container-restorations/fixture-group-1-proof.json'
            first_bytes = first_path.read_bytes()
            first = read(first_path)
            first['reason'] = 'Rewritten history with otherwise equal source.'
            write(first_path, first)
            self.assertTrue(validate_repository_provenance(root, harvest))
            first_path.write_bytes(first_bytes)
            leaf_path = root / 'translation-data/derivations/fixture-group-2.json'
            leaf_bytes = leaf_path.read_bytes()
            leaf = read(leaf_path)
            leaf['previous_derivation_id'] = leaf['derivation_id']
            write(leaf_path, leaf)
            self.assertTrue(validate_repository_provenance(root, harvest))
            leaf_path.write_bytes(leaf_bytes)
            orphan = root / 'translation-data/retired/derivations/orphan/units.jsonl'
            orphan.parent.mkdir(parents=True)
            orphan.write_bytes((root / records[-1]['files']['output_units']['path']).read_bytes())
            self.assertTrue(validate_repository_provenance(root, harvest))
            orphan.unlink()
            collision = root / 'translation-data/units/other.jsonl'
            collision.write_bytes((root / records[-1]['files']['output_units']['path']).read_bytes())
            self.assertTrue(validate_repository_provenance(root, harvest))
            collision.unlink()
            self.assertEqual(validate_repository_provenance(root, harvest), [])

    def test_historical_policy_replay_and_owned_title_require_real_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp), count=2)
            policy = root / 'config/macro-policy.yml'
            policy.write_text(policy.read_text() + '\n# Later policy task, no historical rewriting.\n')
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            # New complex-title roles cannot be introduced as unproven raw facts.
            units = [clean(u) for u in load_jsonl(root / records[-1]['files']['output_units']['path'])]
            named = next(u for u in units if any(n.startswith('OWNARGEND_') for n in u['placeholders']))
            other = copy.deepcopy(named)
            other['unit_id'] = 'tag:0002:statement'
            save(root, 'translation-data/units/unproven.jsonl', [other])
            errors = validate_repository_provenance(root, harvest)
            self.assertTrue(any('owned title requires validated' in e for e in errors))

    def test_unchanged_chinese_cannot_reuse_source_approval_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp), count=2)
            first = [clean(c) for c in load_jsonl(root / 'translation-data/retired/derivations/fixture-group-1/output-candidates.jsonl')][-1]
            current = [clean(c) for c in load_jsonl(root / records[-1]['files']['output_candidates']['path'])][-1]
            self.assertEqual(first['translation_hash'], current['translation_hash'])
            self.assertNotEqual(candidate_provenance_hash(root, first), candidate_provenance_hash(root, current))
            from stacks_zh.decisions import validate_repository_decisions
            selection = {'schema_version':1, 'selection_id':'synthetic-stale', 'unit_id':current['unit_id'],
                'run_id':current['run_id'], 'source_commit':current['source_commit'],
                'translation_hash':current['translation_hash'], 'provenance_hash':candidate_provenance_hash(root, first),
                'decision':'accept-candidate', 'decided_by':'synthetic-maintainer',
                'decided_at':'2026-10-06T09:00:00Z', 'reason':'Synthetic stale approval, never human evidence.'}
            write(root / 'translation-data/selections/synthetic-stale.json', selection)
            errors = validate_repository_decisions(root)
            self.assertTrue(any('provenance' in e for e in errors), errors)

    def test_partial_group_duplicate_drop_wrong_anchor_or_run_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp))
            record = records[0]
            units = load_jsonl(root / record['files']['input_units']['path'])
            candidates = load_jsonl(root / record['files']['input_candidates']['path'])
            corrections, _ = load_repository_corrections(root)
            restored, _ = load_source_containers(root, harvest)
            mutations = [lambda r: r['unit_groups'].pop(),
                lambda r: r['unit_groups'][2]['input_unit_ids'].pop(),
                lambda r: r['unit_groups'][2]['input_unit_ids'].reverse(),
                lambda r: r['unit_groups'][2].update(identity_anchor='tag:0001:statement'),
                lambda r: r['unit_groups'][2].update(model_correction_id='missing'),
                lambda r: r['unit_groups'][2].update(source_container_restoration_id=None),
                lambda r: r['unit_groups'][2]['output_unit_ids'].append('tag:0001:proof')]
            for mutate in mutations:
                broken = copy.deepcopy(record)
                mutate(broken)
                with self.assertRaises(RecordError):
                    replay_derivation(broken, units, candidates, corrections,
                        source_containers=restored, tags=Containers(root, harvest).english.tags)

    def test_complete_context_not_just_anchor_and_new_five_fields_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp))
            record = records[0]
            units = load_jsonl(root / record['files']['input_units']['path'])
            candidates = load_jsonl(root / record['files']['input_candidates']['path'])
            corrections, _ = load_repository_corrections(root)
            restored, _ = load_source_containers(root, harvest)
            key = 'fixture-revision-1', 'tag:0001:proof'
            for field in ['source_units', 'candidates']:
                broken = copy.deepcopy(corrections)
                broken[key]['candidate']['context']['revision_input'][field].pop()
                with self.assertRaisesRegex(RecordError, 'every old group'):
                    replay_derivation(record, units, candidates, broken, source_containers=restored,
                                      tags=Containers(root, harvest).english.tags)

    def test_source_hash_binds_non_anchor_run_and_whole_new_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp), count=2)
            candidate = clean(load_jsonl(root / records[-1]['files']['output_candidates']['path'])[-1])
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            before = candidate_provenance_hash(root, candidate)
            path = root / 'translation-data/runs/fixture-model-b-run.json'
            manifest = read(path)
            manifest['inputs']['policy_revision'] = 'tampered'
            write(path, manifest)
            self.assertNotEqual(candidate_provenance_hash(root, candidate), before)
            self.assertTrue(validate_repository_provenance(root, harvest))

    def test_preview_discloses_all_original_and_actual_revision_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, harvest, records = fixture(Path(tmp), count=2)
            record = records[-1]
            render_batch(root / record['files']['output_units']['path'], root / record['files']['output_candidates']['path'],
                         root / 'upstream.lock', root / 'preview', 'fixture', 'Fixture', chapter_source_dir=harvest,
                         tags_path=harvest / 'tags/tags')
            text = (root / 'preview/metadata.tex').read_text()
            for value in ['fixture-model-a', 'fixture-model-b', 'fixture-revision-model-1', 'fixture-revision-model-2', '完整英文容器']:
                self.assertIn(value, text)
            book = (root / 'preview/chapters/test.tex').read_text()
            self.assertIn('\\label{test-lemma-one}', book)
            self.assertIn('\\label{test-section-basic}', book)
            self.assertNotIn('\\label{lemma-one}', book)

    def test_preview_uses_frozen_literal_policy_after_later_policy_changes(self):
        literal = '\\begin{verbatim}\\ref{fake}\\end{verbatim}'
        with tempfile.TemporaryDirectory() as tmp:
            proof = PROOF.replace('\n\\end{proof}', '\n' + literal + '\n\\end{proof}')
            root, harvest, records = fixture(Path(tmp), proof=proof)
            policy = root / 'config/macro-policy.yml'
            policy.write_text(policy.read_text().replace('    - verbatim\n', ''))
            record = records[0]
            render_batch(root / record['files']['output_units']['path'], root / record['files']['output_candidates']['path'],
                         root / 'upstream.lock', root / 'preview', 'fixture', 'Fixture', chapter_source_dir=harvest,
                         tags_path=harvest / 'tags/tags')
            self.assertIn(literal, (root / 'preview/chapters/test.tex').read_text())


if __name__ == '__main__':
    unittest.main()
