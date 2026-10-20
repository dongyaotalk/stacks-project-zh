"""Literal synthetic Git/model fixtures; no real generation or approval is claimed."""
import copy
import contextlib
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_source_containers import fixture as english_fixture, git, selector, old_unit
from test_math_text import BASE_POLICY
from stacks_zh.harness import resolve_harness
from stacks_zh.provenance import validate_repository_provenance
from stacks_zh.records import RecordError, write_jsonl, sha256_value
from stacks_zh.source_adoptions import (POLICIES, assemble_source_adoption,
    load_repository_source_adoptions, source_adoption_provenance_hash, fresh_source_corpus)
from stacks_zh.source_containers import Containers, lower_container
from stacks_zh.source_reextractions import byte_hash
from stacks_zh.source_terms import source_tex_hash
from stacks_zh.workflow import render_batch, _order_unit_batches_by_chapter_source

REPOSITORY = Path(__file__).resolve().parents[1]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def synthetic_fixture(base, *, typed=True, preferred_min=None):
    statement = ('\\noindent\nA category ' + ('$x\\quad\\text{and}\\quad y$' if typed else '$x$') + '.\n\n'
                 '\\begin{lemma}\\label{lemma-one}A claim.\n\\end{lemma}')
    proof = '\\begin{proof}Use $u\\quad\\text{and}\\quad v$.\\end{proof}'
    root, harvest, source = english_fixture(base, statement=statement, proof=proof)
    for name in POLICIES:
        destination = root / name
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPOSITORY / name, destination)
    if preferred_min is not None:
        path=root/'config/workflow.yml'
        path.write_text(re.sub(r'(?m)^(  preferred_min_source_words:) [0-9]+$',
            lambda match:match[1]+' '+str(preferred_min),path.read_text()))
    (root / 'config/macro-policy.yml').write_text(BASE_POLICY + '''
translatable_math_text:
  conjunction:
    literal: "and"
    command: "text"
    usage: "quad-connector"
    source_label: "test-lemma-one"
    witness_kind: "proof"
    witness_ordinal: 1
''')
    (root / 'config/models.yml').write_text('''schema: 2
lanes:
  synthetic:
    model_id: synthetic
    model_record_id: synthetic:fixture:declared
    harness_id: synthetic
    prompt_version: translator-v2
model_records:
  synthetic:fixture:declared:
    provider: Synthetic
    requested_id: synthetic
    resolved_id: synthetic
    snapshot: null
    identity_confidence: declared
''')
    (root / 'config/harnesses.yml').write_text('''schema: 1
harnesses:
  synthetic:
    display_name: Synthetic test fixture
    kind: agent_cli
    status: supported
    adapter_version: stacks-harness-v1
    version_required: true
    version_command: python3 --version
    version_pattern: '^Python\\s+(?P<version>\\S+)'
''')
    (root / 'config/glossary.yml').write_text('entries: []\n')
    native = Containers(root, harvest)
    groups = [native.select(selector('prose_block', owner='0000')), native.select(selector('lemma'))]
    units = [lower_container(group, native.policy)[0] for group in groups]
    write(root / 'config/source-terms.json', dict(schema_version=1, source_commit=source,
        nonmathematical_declarations={}, terms=[dict(id='category', forms=['category'], chapters=[],
        evidence=[dict(chapter='test', unit_id=units[0]['unit_id'], source_term='category',
                       source_tex_hash=source_tex_hash(units[0]))])]))
    git(root, 'init', '-q')
    git(root, 'add', '.')
    git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'Synthetic accepted policy origin; no translation facts')
    origin = git(root, 'rev-parse', 'HEAD')
    batches = []
    for name, group, unit in zip(['prose', 'lemma'], groups, units, strict=True):
        up, cp = f'translation-data/units/test-{name}.jsonl', f'translation-data/candidates/synthetic/test-{name}.jsonl'
        (root / up).parent.mkdir(parents=True, exist_ok=True)
        write_jsonl(root / up, [unit])
        batches.append(dict(units_path=up, candidates_path=cp, units=[unit],
            containers=[dict(selector=group['selector'], selected=group, unit_ids=[unit['unit_id']])],
            prior_attempts=[]))
    observed = resolve_harness('synthetic', root / 'config/harnesses.yml')
    contexts = []
    for row in native.document('test')[1]:
        value = dict(kind='locked-English-neighbor', location=row['location'], source_commit=source,
                     source_unit=row['unit'], owner_tag=row['owner_tag'], parent_tag=row['parent_tag'])
        contexts.append(dict(context_id=row['unit']['unit_id'], value=value, hash=sha256_value(value)))
    frozen = dict(schema_version=1, tool_version='source-adoption-input-v1', adoption_id='synthetic-first',
        origin_commit=origin, source_commit=source, task_id='synthetic-only', created_at='2026-10-19T00:00:00Z',
        runtime=dict(model_lane='synthetic', model=dict(record_id='synthetic:fixture:declared',
            provider='Synthetic', requested_id='synthetic', resolved_id='synthetic', snapshot=None,
            identity_confidence='declared'), harness=dict(id='synthetic', version=observed.version,
            adapter_version='stacks-harness-v1'), reasoning_effort='synthetic', turn_id='synthetic-only', replayable=False),
        policies=[dict(path=name, hash=byte_hash((root / name).read_bytes())) for name in POLICIES],
        contexts=contexts, batches=batches, outside_preferred_reason='Tiny independent synthetic fixture.')
    input_path = root / 'translation-data/source-adoption-inputs/synthetic-first.json'
    unit_ids = [u['unit_id'] for u in units]
    branch = git(root, 'branch', '--show-current')
    scope_path = 'task-scopes/synthetic-first.json'
    files = [scope_path, input_path.relative_to(root).as_posix(),
        'docs/evidence/synthetic-first-raw.jsonl', 'docs/evidence/synthetic-prior-raw.jsonl',
        'docs/evidence/synthetic-prior-input.json', 'translation-data/runs/synthetic-prior.json',
        'translation-data/runs/run-synthetic-first.json', 'translation-data/source-adoptions/synthetic-first.json']
    files += [b[role] for b in batches for role in ('units_path','candidates_path')]
    files += [f'translation-data/retired/source-adoptions/synthetic-first-prior-{i:03d}/{role}.jsonl'
              for i in [1,2] for role in ('units','candidates')]
    scope = dict(schema_version=1, task_id='synthetic-only', owner='synthetic', branch=branch,
        source_commit=source, allowed_write_files=files, data_scopes=[dict(scope_id='synthetic',
        chapter='test', parent_tags=['0000'], historical_parent_tags=[], unit_ids=unit_ids,
        input_unit_ids=unit_ids, output_unit_ids=unit_ids, allowed_write_files=files[1:],
        run_scope=['run-synthetic-first','synthetic-prior'], model_scope=['synthetic','synthetic:fixture:declared'])])
    write(root / scope_path, scope)
    frozen.update(unit_ids=unit_ids, chapter='test', parent_tags=['0000'], run_id='run-synthetic-first',
        task=dict(issue=1, owner='synthetic', branch=branch, scope_manifest=scope_path,
            scope_manifest_sha256=byte_hash((root / scope_path).read_bytes()),
            scope_bytes=(root / scope_path).read_text()))
    write(input_path, frozen)
    source_prefix = '\n<STRUCT_0001>\n'
    assert units[0]['source_text'] == source_prefix + ('A category <MATHSEG_0001>and<MATHSEG_0002>.\n\n' if typed else 'A category <MATH_0001>.\n\n')
    assert units[1]['source_text'] == 'A claim.\n'
    raw = [dict(unit_id=units[0]['unit_id'],
        translation=source_prefix + ('合成范畴（category）<MATHSEG_0001>且<MATHSEG_0002>。\n\n' if typed else '合成范畴（category）<MATH_0001>。\n\n'),
        allowed_english=[], term_occurrences=[dict(source_term='category', target_term='合成范畴')],
        unknown_terms=[dict(source_term='category', target_term='合成范畴', context='Synthetic fixture only.')],
        notes=['Literal synthetic test data; no actual model generation.']),
        dict(unit_id=units[1]['unit_id'], translation='合成断言。\n', allowed_english=[],
             term_occurrences=[], unknown_terms=[], notes=['Literal synthetic test data.'])]
    raw_path = root / 'docs/evidence/synthetic-first-raw.jsonl'
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(raw_path, raw)
    return root, harvest, input_path, raw_path, frozen, raw


def provisional_fixture(base):
    """A literal ordinary provisional run, retained before first Git adoption."""
    from stacks_zh.workflow import _candidate_records
    root, harvest, fp, rp, frozen, raw = synthetic_fixture(base, typed=False)
    old_raw = root / 'docs/evidence/synthetic-prior-raw.jsonl'
    write_jsonl(old_raw, raw)
    prior_input = root / 'docs/evidence/synthetic-prior-input.json'
    generation = dict(immutable_generation_freeze=True, frozen_at='2026-10-18T00:00:00Z',
        run_id='synthetic-prior', complete_target_units=[u for b in frozen['batches'] for u in b['units']],
        policy_revision='git:' + frozen['origin_commit'],
        policy_inputs={name:dict(hash=byte_hash((root/name).read_bytes()), content=(root/name).read_text())
                       for name in POLICIES}, runtime=frozen['runtime'])
    write(prior_input, generation)
    input_ref = dict(path=prior_input.relative_to(root).as_posix(), hash=byte_hash(prior_input.read_bytes()))
    raw_ref = dict(path=old_raw.relative_to(root).as_posix(), hash=byte_hash(old_raw.read_bytes()))
    candidates = {}
    for batch in frozen['batches']:
        rows = _candidate_records(batch['units'], {r['unit_id']:r for r in raw}, frozen['source_commit'],
            'synthetic', 'synthetic', 'synthetic', 'translator-v2', 'git:'+frozen['origin_commit'],
            'git:'+frozen['origin_commit'], '2026-10-18T00:00:00Z', 'synthetic',
            frozen['runtime']['harness']['version'], 'synthetic:fixture:declared', 'synthetic-prior', None, 'declared')
        for candidate in rows:
            actual = next(r for r in raw if r['unit_id'] == candidate['unit_id'])
            candidate['context'].update(input_freeze=input_ref, turn_id=frozen['runtime']['turn_id'],
                model_output={**raw_ref, 'record_hash':sha256_value(actual)})
            candidate['context_hash'] = sha256_value(candidate['context'])
        candidates[batch['candidates_path']] = rows
        (root / batch['candidates_path']).parent.mkdir(parents=True, exist_ok=True)
        write_jsonl(root / batch['candidates_path'], rows)
    manifest = dict(schema_version=1, run_id='synthetic-prior', run_kind='translation', task_id='synthetic-only',
        source_commit=frozen['source_commit'], unit_ids=[r['unit_id'] for r in raw],
        harness=frozen['runtime']['harness'], model=frozen['runtime']['model'],
        inputs=dict(prompt_version='translator-v2', policy_revision='git:'+frozen['origin_commit'],
            glossary_revision='git:'+frozen['origin_commit'],
            context_hashes=[c['context_hash'] for path in sorted(candidates) for c in candidates[path]],
            settings=dict(input_freeze=input_ref, raw_attempts=[{**raw_ref,'unit_ids':[r['unit_id'] for r in raw]}],
                accepted_records=[dict(unit_id=c['unit_id'],candidate_path=path,raw_path=raw_ref['path'],
                    record_hash=c['context']['model_output']['record_hash'],five_fields_equal=True)
                    for path,rows in candidates.items() for c in rows])),
        created_at='2026-10-18T00:00:00Z', replayable=False, status='recorded', notes=['Synthetic only.'])
    run_path = root / 'translation-data/runs/synthetic-prior.json'; write(run_path, manifest)
    for index, batch in enumerate(frozen['batches'], 1):
        folder = root / f'translation-data/retired/source-adoptions/synthetic-first-prior-{index:03d}'
        folder.mkdir(parents=True)
        write_jsonl(folder/'units.jsonl', batch['units'])
        (folder/'candidates.jsonl').write_bytes((root/batch['candidates_path']).read_bytes())
        batch['prior_attempts'] = [dict(units=dict(path=(folder/'units.jsonl').relative_to(root).as_posix(),
            hash=byte_hash((folder/'units.jsonl').read_bytes())), candidates=dict(
            path=(folder/'candidates.jsonl').relative_to(root).as_posix(),
            hash=byte_hash((folder/'candidates.jsonl').read_bytes())),
            runs=[dict(path=run_path.relative_to(root).as_posix(),hash=byte_hash(run_path.read_bytes()))],
            generation_inputs=[input_ref], raw_outputs=[raw_ref])]
    write(fp, frozen)
    raw[0]['translation'] = raw[0]['translation'].replace('合成范畴', '再次合成范畴')
    write_jsonl(rp, raw)
    return root, harvest, fp, rp, frozen, raw


class SourceAdoptionTests(unittest.TestCase):
    def test_complete_second_retry_inputs_replay_both_existing_predecessor_forms(self):
        for field in ['earlier_attempts','retry2_of']:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root,harvest,fp,rp,frozen,_=provisional_fixture(Path(temp))
                prior=frozen['batches'][0]['prior_attempts'][0]
                old_input=prior['generation_inputs'][0];old_raw=prior['raw_outputs'][0]
                retry_input=root/'docs/evidence/synthetic-prior-retry2-input.json'
                generation=json.loads((root/old_input['path']).read_text())
                generation[field]=[old_raw,old_input];write(retry_input,generation)
                retry_ref=dict(path=retry_input.relative_to(root).as_posix(),hash=byte_hash(retry_input.read_bytes()))
                retry_raw=root/'docs/evidence/synthetic-prior-retry2-raw.jsonl'
                retry_raw.write_bytes((root/old_raw['path']).read_bytes())
                raw_ref=dict(path=retry_raw.relative_to(root).as_posix(),hash=byte_hash(retry_raw.read_bytes()))
                run_path=root/'translation-data/runs/synthetic-prior.json'
                run=json.loads(run_path.read_text());updated={}
                for batch in frozen['batches']:
                    path=root/batch['candidates_path'];rows=[json.loads(line) for line in path.read_text().splitlines()]
                    for candidate in rows:
                        candidate['context']['model_output'].update(raw_ref)
                        candidate['context_hash']=sha256_value(candidate['context'])
                    write_jsonl(path,rows);updated[batch['candidates_path']]=rows
                    archive=batch['prior_attempts'][0]['candidates'];(root/archive['path']).write_bytes(path.read_bytes())
                    archive['hash']=byte_hash(path.read_bytes())
                    batch['prior_attempts'][0]['generation_inputs'].append(retry_ref)
                    batch['prior_attempts'][0]['raw_outputs'].append(raw_ref)
                for entry in run['inputs']['settings']['accepted_records']:entry['raw_path']=raw_ref['path']
                run['inputs']['settings']['raw_attempts'].append({**raw_ref,'unit_ids':run['unit_ids']})
                run['inputs']['context_hashes']=[c['context_hash'] for path in sorted(updated) for c in updated[path]]
                write(run_path,run)
                for batch in frozen['batches']:batch['prior_attempts'][0]['runs'][0]['hash']=byte_hash(run_path.read_bytes())
                write(fp,frozen)
                assemble_source_adoption(root,fp,[rp],harvest)
                self.assertEqual(validate_repository_provenance(root,harvest),[])

    def test_historical_package_uses_frozen_origin_preferences(self):
        with tempfile.TemporaryDirectory() as temp:
            root,harvest,fp,rp,frozen,_=synthetic_fixture(Path(temp),preferred_min=1)
            frozen['outside_preferred_reason']=None;write(fp,frozen)
            assemble_source_adoption(root,fp,[rp],harvest)
            path=root/'config/workflow.yml'
            path.write_text(re.sub(r'(?m)^(  preferred_max_source_words:) [0-9]+$',r'\1 1',path.read_text()))
            _,errors=load_repository_source_adoptions(root,harvest)
            self.assertEqual(errors,[])

    def test_accepted_header_frame_is_located_without_borrowing_neighbor_prose(self):
        from stacks_zh.source_alignment import align_batches
        header = ('\\title{Synthetic categories}\n\n\\maketitle\n\\phantomsection\n'
                  '\\label{section-phantom}\n\n\\tableofcontents\n\n')
        body = '\\noindent\nA complete paragraph.\n\n\\begin{lemma}\\label{lemma-one}A claim.\\end{lemma}'
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _ = english_fixture(Path(temp), statement=body)
            path = harvest/'test.tex';path.write_text(path.read_text().replace('\\begin{document}\n','\\begin{document}\n'+header))
            tags = harvest/'tags/tags';tags.write_text(tags.read_text()+'0003,test-section-phantom\n')
            git(harvest,'add','test.tex','tags/tags')
            git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic full header')
            source=git(harvest,'rev-parse','HEAD');(root/'upstream.lock').write_text('commit = "'+source+'"\n')
            title=old_unit(source,'tag:0003:title','chapter_title','Synthetic categories',
                '\\title{','}\n\n\\maketitle\n\\phantomsection\n\\label{section-phantom}\n\n\\tableofcontents\n\n')
            corpus,native=fresh_source_corpus(root,harvest,'test')
            matches,_=align_batches({'header':[title]},corpus)
            # The accepted matcher excludes trailing layout whitespace from
            # its token span; every header command and title byte remains.
            self.assertEqual(matches[0]['status'],'PRESENTATION_EQUIVALENT')
            location=matches[0]['location'];raw=path.read_bytes()
            self.assertEqual(raw[location['byte_start']:location['byte_end']],header.rstrip().encode())
            prose=lower_container(native.select(selector('prose_block',owner='0000')),native.policy)[0]
            heading=lower_container(native.select(selector('section_title',owner='0000')),native.policy)[0]
            lemma=lower_container(native.select(selector('lemma')),native.policy)[0]
            self.assertEqual(_order_unit_batches_by_chapter_source([[lemma],[prose],[title],[heading]],
                harvest,root=root),[title,heading,prose,lemma])
            changed=copy.deepcopy(title);changed['source_text']='Different categories'
            bad,_=align_batches({'header':[changed]},corpus)
            self.assertEqual(bad[0]['status'],'SOURCE_DIFFERENCE')

    def test_original_typed_policy_binding_survives_current_nonsemantic_policy_hash_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root,harvest,fp,rp,frozen,_=synthetic_fixture(Path(temp))
            assemble_source_adoption(root,fp,[rp],harvest)
            path=root/'config/macro-policy.yml';path.write_bytes(path.read_bytes()+b'\n# Synthetic metadata change.\n')
            adopted,errors=load_repository_source_adoptions(root,harvest)
            self.assertEqual(errors,[])
            self.assertEqual(len(adopted),2)
            render_batch([root/b['units_path'] for b in frozen['batches']],
                [root/b['candidates_path'] for b in frozen['batches']],root/'upstream.lock',
                root/'preview','synthetic','Synthetic fixture',chapter_source_dir=harvest,tags_path=harvest/'tags/tags')
            self.assertIn(r'$x\quad\text{且}\quad y$',(root/'preview/chapters/test.tex').read_text())

    def test_frozen_scope_owner_branch_ids_run_and_raw_paths_are_enforced(self):
        for failure in ['branch','ids','run','scope-bytes','raw-path']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp))
                if failure == 'branch': frozen['task']['branch'] = 'different-branch'
                elif failure == 'ids': frozen['unit_ids'].reverse()
                elif failure == 'run': frozen['run_id']='different-run'
                elif failure == 'scope-bytes': frozen['task']['scope_bytes'] += '\n'
                else:
                    other=root/'docs/evidence/outside-scope.jsonl';other.write_bytes(rp.read_bytes());rp=other
                write(fp,frozen)
                with self.assertRaises((RecordError,ValueError)):
                    assemble_source_adoption(root,fp,[rp],harvest)
                self.assertFalse((root/'translation-data/source-adoptions').exists())

    def test_public_cli_and_decision_binding_use_the_same_complete_replay(self):
        from stacks_zh.cli import main
        from stacks_zh.decisions import validate_repository_decisions
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['assemble-source-adoption', '--root', str(root),
                    '--input', str(fp), '--raw', str(rp), '--harvest', str(harvest)]), 0)
            adopted, errors = load_repository_source_adoptions(root, harvest)
            self.assertEqual(errors, [])
            candidate = next(iter(adopted.values()))['candidate']
            selection = dict(schema_version=1, selection_id='synthetic-selection',
                unit_id=candidate['unit_id'], source_commit=frozen['source_commit'],
                run_id=candidate['run_id'], translation_hash=candidate['translation_hash'],
                decision='request-changes', decided_by='Synthetic fixture, not a human reviewer',
                decided_at='2026-10-19T01:00:00Z', reason='Synthetic binding test; no actual approval.')
            path = root / 'translation-data/selections/synthetic-selection.json'; write(path, selection)
            self.assertTrue(any('provenance_hash' in error for error in validate_repository_decisions(root, harvest)))
            selection['provenance_hash'] = source_adoption_provenance_hash(root, candidate); write(path, selection)
            self.assertEqual(validate_repository_decisions(root, harvest), [])

    def test_ordinary_single_and_many_entry_points_still_reject_typed_without_package(self):
        from stacks_zh.workflow import assemble_candidates, assemble_candidates_many
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, _, rp, frozen, _ = synthetic_fixture(Path(temp))
            metadata = dict(model_id='synthetic', model_lane='synthetic', reasoning_effort='synthetic',
                prompt_version='translator-v2', policy_revision='synthetic', glossary_revision='synthetic',
                created_at=frozen['created_at'], harness_id='synthetic', model_record_id='synthetic:fixture:declared',
                run_id='synthetic-not-an-adoption', model_identity_confidence='declared',
                harness_config_path=root/'config/harnesses.yml')
            with self.assertRaisesRegex(RecordError, 'ordinary assembly is unavailable'):
                assemble_candidates(root/frozen['batches'][0]['units_path'], rp, root/'never.jsonl',
                    root/'upstream.lock', **metadata)
            with self.assertRaisesRegex(RecordError, 'ordinary assembly is unavailable'):
                assemble_candidates_many([root/b['units_path'] for b in frozen['batches']], rp,
                    [root/b['candidates_path'] for b in frozen['batches']], root/'upstream.lock', **metadata)
            self.assertFalse((root/'never.jsonl').exists())

    def test_original_input_symlink_is_rejected_before_resolving_its_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, _, _ = synthetic_fixture(Path(temp))
            alias = root/'translation-data/source-adoption-inputs/alias.json'; alias.symlink_to(fp)
            with self.assertRaisesRegex(RecordError, 'symlink'):
                assemble_source_adoption(root, alias, [rp], harvest)

    def test_missing_or_rehashed_false_english_context_is_rejected(self):
        for failure in ['missing', 'false', 'anchor']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp))
                if failure == 'missing': frozen['contexts'] = []
                elif failure == 'false':
                    item = frozen['contexts'][0]
                    item['value']['source_unit']['source_text'] = 'A forged context.'
                    item['hash'] = sha256_value(item['value'])
                else:
                    item = frozen['contexts'][0]
                    item['value'].update(kind='locked-English-reference', requested_label='test-lemma-one', requested_tag='0001')
                    item['hash'] = sha256_value(item['value'])
                write(fp, frozen)
                with self.assertRaisesRegex(RecordError, 'context'):
                    assemble_source_adoption(root, fp, [rp], harvest)
                self.assertFalse((root / 'translation-data/source-adoptions').exists())

    def test_other_active_source_overlap_cannot_be_hidden_by_a_new_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp))
            alias = copy.deepcopy(frozen['batches'][0]['units'][0]); alias['unit_id'] = 'tag:0000:p099'
            write_jsonl(root / 'translation-data/units/overlap.jsonl', [alias])
            with self.assertRaisesRegex(RecordError, 'overlaps|disjointness'):
                assemble_source_adoption(root, fp, [rp], harvest)
            self.assertFalse((root / 'translation-data/source-adoptions').exists())

    def test_package_cannot_adopt_overlapping_containers_under_distinct_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp), typed=False)
            native = Containers(root, harvest)
            group = native.select(selector('paragraph', owner='0000'))
            unit = lower_container(group, native.policy)[0]
            batch = frozen['batches'][1]
            batch.update(units=[unit], containers=[dict(selector=group['selector'],
                selected=group, unit_ids=[unit['unit_id']])])
            write_jsonl(root / batch['units_path'], [unit])
            frozen['unit_ids'] = [u['unit_id'] for b in frozen['batches'] for u in b['units']]
            scope_path = root / frozen['task']['scope_manifest']
            scope = json.loads(scope_path.read_text())
            child = scope['data_scopes'][0]
            for field in ('unit_ids', 'input_unit_ids', 'output_unit_ids'):
                child[field] = frozen['unit_ids']
            write(scope_path, scope)
            frozen['task'].update(scope_bytes=scope_path.read_text(),
                scope_manifest_sha256=byte_hash(scope_path.read_bytes()))
            write(fp, frozen)
            with self.assertRaisesRegex(RecordError, 'containers overlap across batches'):
                assemble_source_adoption(root, fp, [rp], harvest)
            self.assertFalse((root / 'translation-data/source-adoptions').exists())
            self.assertFalse((root / 'translation-data/runs').exists())
            self.assertTrue(all(not (root / b['candidates_path']).exists() for b in frozen['batches']))

    def test_prior_context_order_failure_is_rejected_before_replacing_any_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, _ = provisional_fixture(Path(temp))
            before = {b['candidates_path']:(root/b['candidates_path']).read_bytes() for b in frozen['batches']}
            path = root / 'translation-data/runs/synthetic-prior.json'
            run = json.loads(path.read_text()); run['inputs']['context_hashes'].reverse(); write(path, run)
            for batch in frozen['batches']:
                batch['prior_attempts'][0]['runs'][0]['hash'] = byte_hash(path.read_bytes())
            write(fp, frozen)
            with self.assertRaisesRegex(RecordError, 'full context order'):
                assemble_source_adoption(root, fp, [rp], harvest)
            self.assertTrue(all((root/path).read_bytes()==payload for path,payload in before.items()))

    def test_committed_first_adoption_cannot_be_deleted_or_rehashed(self):
        for failure in ['deleted', 'rehashed']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, _, _ = synthetic_fixture(Path(temp))
                assemble_source_adoption(root, fp, [rp], harvest)
                git(root, 'add', '.')
                git(root, '-c', 'user.name=Synthetic', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'Synthetic complete adoption, no actual model output')
                path = root / 'translation-data/source-adoptions/synthetic-first.json'
                if failure == 'deleted': path.unlink()
                else:
                    value = json.loads(fp.read_text()); value['runtime']['turn_id']='changed'; write(fp, value)
                    record=json.loads(path.read_text());record['input']['hash']=byte_hash(fp.read_bytes());write(path,record)
                _, errors = load_repository_source_adoptions(root, harvest)
                self.assertTrue(any('immutable' in error for error in errors), errors)

    def test_complete_provisional_ordinary_history_keeps_both_actual_runs(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, raw = provisional_fixture(Path(temp))
            old_bytes = (root / 'translation-data/runs/synthetic-prior.json').read_bytes()
            assemble_source_adoption(root, fp, [rp], harvest)
            adopted, errors = load_repository_source_adoptions(root, harvest)
            self.assertEqual(errors, [])
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            self.assertEqual((root / 'translation-data/runs/synthetic-prior.json').read_bytes(), old_bytes)
            self.assertEqual(len(adopted[(frozen['batches'][0]['candidates_path'], raw[0]['unit_id'])]['prior_candidates']), 1)

    def test_missing_provisional_raw_or_full_batch_is_not_a_waiver(self):
        for failure in ['missing-raw', 'missing-unit', 'wrong-time']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = provisional_fixture(Path(temp))
                before = {b['candidates_path']:(root/b['candidates_path']).read_bytes() for b in frozen['batches']}
                prior = frozen['batches'][0]['prior_attempts'][0]
                if failure == 'missing-raw': prior['raw_outputs'] = []
                elif failure == 'missing-unit': frozen['batches'][0]['units'] = []
                else: frozen['created_at'] = '2026-10-17T00:00:00Z'
                write(fp, frozen)
                with self.assertRaises((RecordError, ValueError)):
                    assemble_source_adoption(root, fp, [rp], harvest)
                self.assertTrue(all((root/path).read_bytes()==payload for path,payload in before.items()))

    def test_first_typed_adoption_replays_actual_raw_run_and_complete_git_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, raw = synthetic_fixture(Path(temp))
            record = assemble_source_adoption(root, fp, [rp], harvest)
            self.assertEqual(record['unit_ids'], [r['unit_id'] for r in raw])
            adopted, errors = load_repository_source_adoptions(root, harvest)
            self.assertEqual(errors, [])
            self.assertEqual(len(adopted), 2)
            self.assertEqual(validate_repository_provenance(root, harvest), [])
            candidate = adopted[(frozen['batches'][0]['candidates_path'], raw[0]['unit_id'])]['candidate']
            self.assertEqual(candidate['translation'], raw[0]['translation'])
            self.assertEqual(candidate['stage'], 'STRUCTURE_OK')
            self.assertTrue(source_adoption_provenance_hash(root, candidate).startswith('sha256:'))

    def test_real_renderer_uses_validated_first_typed_prose_and_keeps_math(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp))
            assemble_source_adoption(root, fp, [rp], harvest)
            render_batch([root / b['units_path'] for b in frozen['batches']],
                [root / b['candidates_path'] for b in frozen['batches']], root / 'upstream.lock',
                root / 'preview', 'synthetic', 'Synthetic fixture', chapter_source_dir=harvest,
                tags_path=harvest / 'tags/tags')
            text = (root / 'preview/chapters/test.tex').read_text()
            self.assertIn(r'$x\quad\text{且}\quad y$', text)
            self.assertLess(text.index('合成范畴'), text.index('合成断言'))

    def test_wrong_complete_selector_or_raw_token_writes_no_fact_outputs(self):
        for failure in ['ordinal', 'partial', 'math', 'raw']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, raw = synthetic_fixture(Path(temp))
                if failure == 'ordinal': frozen['batches'][0]['containers'][0]['selector']['ordinal'] = 2
                elif failure == 'partial': frozen['batches'][0]['units'][0]['source_text'] = 'Incomplete.'
                elif failure == 'math': frozen['batches'][0]['units'][0]['placeholders']['MATHSEG_0001'] = '$z'
                else: raw[0]['translation'] = raw[0]['translation'].replace('<MATHSEG_0001>', '')
                write(fp, frozen); write_jsonl(rp, raw)
                with self.assertRaises((RecordError, ValueError)):
                    assemble_source_adoption(root, fp, [rp], harvest)
                self.assertFalse((root / 'translation-data/source-adoptions').exists())
                self.assertFalse((root / 'translation-data/runs').exists())
                self.assertFalse((root / frozen['batches'][0]['candidates_path']).exists())

    def test_policy_drift_and_harness_drift_are_rejected(self):
        for failure in ['policy', 'harness']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temp:
                root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp))
                if failure == 'policy':
                    path = root / 'config/style-guide.md'; path.write_bytes(path.read_bytes() + b'\nChanged\n')
                else:
                    frozen['runtime']['harness']['version'] = 'synthetic-different'; write(fp, frozen)
                with self.assertRaisesRegex(RecordError, 'policy drifted|Harness changed'):
                    assemble_source_adoption(root, fp, [rp], harvest)

    def test_output_failure_rolls_back_all_prepared_candidates(self):
        with tempfile.TemporaryDirectory() as temp:
            root, harvest, fp, rp, frozen, _ = synthetic_fixture(Path(temp))
            import os
            original, calls = os.replace, []
            def fail_second(a, b):
                calls.append(b)
                if len(calls) == 2: raise OSError('Synthetic install failure')
                return original(a, b)
            with patch('stacks_zh.source_adoptions.os.replace', fail_second):
                with self.assertRaisesRegex(OSError, 'Synthetic install failure'):
                    assemble_source_adoption(root, fp, [rp], harvest)
            self.assertTrue(all(not (root / b['candidates_path']).exists() for b in frozen['batches']))
            self.assertFalse((root / 'translation-data/source-adoptions/synthetic-first.json').exists())


if __name__ == '__main__':
    unittest.main()


def followup_fixture(base):
    """Two complete synthetic generations before a first Git adoption."""
    root, harvest, fp, rp, frozen, raw = synthetic_fixture(base)
    record = assemble_source_adoption(root, fp, [rp], harvest)
    updated = copy.deepcopy(frozen)
    updated.update(adoption_id='synthetic-followup', run_id='run-synthetic-followup',
                   tool_version='source-adoption-input-v2', created_at='2026-10-20T00:00:00Z')
    archives = []
    for output in record['outputs']:
        saved = {}
        for role in ['units', 'candidates']:
            relative = (f'translation-data/retired/source-adoptions/synthetic-followup-'
                        f'synthetic-first-{Path(output[role]["path"]).stem}/{role}.jsonl')
            path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((root / output[role]['path']).read_bytes())
            saved[role] = dict(path=relative, hash=byte_hash(path.read_bytes()))
        archives.append(saved)
    prior_path = 'translation-data/source-adoptions/synthetic-first.json'
    updated['prior_adoptions'] = [dict(record=dict(path=prior_path,
        hash=byte_hash((root / prior_path).read_bytes())), outputs=archives)]
    new_fp = root / 'translation-data/source-adoption-inputs/synthetic-followup.json'
    new_rp = root / 'docs/evidence/synthetic-followup-raw.jsonl'
    scope_path = root / frozen['task']['scope_manifest']
    scope = json.loads(scope_path.read_text())
    extra = [new_fp.relative_to(root).as_posix(), new_rp.relative_to(root).as_posix(),
             'translation-data/source-adoptions/synthetic-followup.json',
             'translation-data/runs/run-synthetic-followup.json',
             *(o[r]['path'] for o in archives for r in ['units','candidates'])]
    scope['allowed_write_files'].extend(extra); scope['data_scopes'][0]['allowed_write_files'].extend(extra)
    scope['data_scopes'][0]['run_scope'].append('run-synthetic-followup')
    write(scope_path, scope)
    updated['task'].update(scope_bytes=scope_path.read_text(),scope_manifest_sha256=byte_hash(scope_path.read_bytes()))
    write(new_fp, updated)
    raw[0]['translation'] = raw[0]['translation'].replace('合成范畴','后续合成范畴')
    raw[0]['term_occurrences'][0]['target_term'] = '后续合成范畴'
    raw[0]['unknown_terms'][0]['target_term'] = '后续合成范畴'
    write_jsonl(new_rp,raw)
    return root, harvest, new_fp, new_rp, updated, record


class SourceAdoptionFollowupTests(unittest.TestCase):
    def test_complete_followup_preserves_both_runs_and_first_git_adoption(self):
        with tempfile.TemporaryDirectory() as temp:
            root,harvest,fp,rp,frozen,_=followup_fixture(Path(temp))
            assemble_source_adoption(root,fp,[rp],harvest)
            rows,errors=load_repository_source_adoptions(root,harvest)
            self.assertEqual(errors,[]);self.assertEqual(len(rows),2)
            self.assertTrue(all(len(v['prior_candidates'])==1 for v in rows.values()))
            self.assertEqual(validate_repository_provenance(root,harvest),[])
            git(root,'add','.')
            git(root,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic complete adoption')
            self.assertEqual(validate_repository_provenance(root,harvest),[])

    def test_rejects_incomplete_prior_outputs_and_unchanged_active_drift(self):
        for mutation,needle in [('partial','every complete original'),('drift','drifted'),('time','strict time order'),('v1','schema')]:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                root,harvest,fp,rp,frozen,_=followup_fixture(Path(temp))
                if mutation=='partial':frozen['prior_adoptions'][0]['outputs'].pop()
                elif mutation=='drift':
                    p=root/frozen['batches'][0]['candidates_path'];p.write_bytes(p.read_bytes()+b'\n')
                elif mutation=='time':frozen['created_at']='2026-10-18T00:00:00Z'
                else:frozen['tool_version']='source-adoption-input-v1'
                write(fp,frozen)
                with self.assertRaises(RecordError):assemble_source_adoption(root,fp,[rp],harvest)

    def test_rejects_already_git_adopted_predecessor(self):
        with tempfile.TemporaryDirectory() as temp:
            root,harvest,fp,rp,frozen,record=followup_fixture(Path(temp))
            git(root,'add',record['input']['path'],'translation-data/source-adoptions/synthetic-first.json')
            git(root,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic prior adopted')
            with self.assertRaisesRegex(RecordError,'pre-Git'):
                assemble_source_adoption(root,fp,[rp],harvest)

    def test_rejects_changed_prior_raw_even_after_rehash(self):
        with tempfile.TemporaryDirectory() as temp:
            root,harvest,fp,rp,frozen,record=followup_fixture(Path(temp))
            p=root/record['raw_attempts'][0]['path'];p.write_bytes(p.read_bytes()+b'\n')
            record['raw_attempts'][0]['hash']=byte_hash(p.read_bytes())
            record_path=root/frozen['prior_adoptions'][0]['record']['path'];write(record_path,record)
            frozen['prior_adoptions'][0]['record']['hash']=byte_hash(record_path.read_bytes());write(fp,frozen)
            with self.assertRaises(RecordError):assemble_source_adoption(root,fp,[rp],harvest)

    def test_snapshot_missing_changed_and_duplicate_successor_fail(self):
        for mutation in ['missing','changed','duplicate']:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                root,harvest,fp,rp,frozen,_=followup_fixture(Path(temp))
                if mutation=='duplicate':
                    assemble_source_adoption(root,fp,[rp],harvest)
                    record_path=root/'translation-data/source-adoptions/synthetic-followup.json'
                    (record_path.parent/'duplicate.json').write_bytes(record_path.read_bytes())
                    self.assertTrue(load_repository_source_adoptions(root,harvest)[1])
                    continue
                entry=frozen['prior_adoptions'][0]['outputs'][0]['candidates'];p=root/entry['path']
                if mutation=='missing':p.unlink()
                else:p.write_bytes(p.read_bytes()+b'\n');entry['hash']=byte_hash(p.read_bytes());write(fp,frozen)
                with self.assertRaises(RecordError):assemble_source_adoption(root,fp,[rp],harvest)

    def test_complete_owned_title_passes_public_provenance_and_fake_pointer_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root,harvest,fp,rp,frozen,raw=synthetic_fixture(Path(temp))
            english=harvest/'test.tex';english.write_text(english.read_text().replace('\\begin{lemma}\\label{lemma-one}A claim.',
                '\\begin{lemma}[A title]\\label{lemma-one}A claim.'))
            git(harvest,'add','.');git(harvest,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic named title')
            source=git(harvest,'rev-parse','HEAD')
            (root/'upstream.lock').write_text((root/'upstream.lock').read_text().replace(frozen['source_commit'],source))
            catalog=json.loads((root/'config/source-terms.json').read_text());catalog['source_commit']=source;write(root/'config/source-terms.json',catalog)
            git(root,'add','upstream.lock','config/source-terms.json');git(root,'-c','user.name=Synthetic','-c','user.email=fixture@example.invalid','commit','-qm','Synthetic updated source policy')
            frozen['origin_commit']=git(root,'rev-parse','HEAD');frozen['source_commit']=source
            native=Containers(root,harvest)
            for batch in frozen['batches']:
                selected=native.select(batch['containers'][0]['selector']);units=lower_container(selected,native.policy)
                batch['units']=units;batch['containers'][0].update(selected=selected,unit_ids=[u['unit_id'] for u in units])
                write_jsonl(root/batch['units_path'],units)
            frozen['contexts']=[]
            for row in native.document('test')[1]:
                value=dict(kind='locked-English-neighbor',location=row['location'],source_commit=source,
                    source_unit=row['unit'],owner_tag=row['owner_tag'],parent_tag=row['parent_tag'])
                frozen['contexts'].append(dict(context_id=row['unit']['unit_id'],value=value,hash=sha256_value(value)))
            frozen['policies']=[dict(path=p,hash=byte_hash((root/p).read_bytes())) for p in POLICIES]
            scope_path=root/frozen['task']['scope_manifest'];scope=json.loads(scope_path.read_text());scope['source_commit']=source;write(scope_path,scope)
            frozen['task'].update(scope_bytes=scope_path.read_text(),scope_manifest_sha256=byte_hash(scope_path.read_bytes()));write(fp,frozen)
            raw[1]['translation']='合成标题<OWNARGEND_0001>合成断言。\n';write_jsonl(rp,raw)
            assemble_source_adoption(root,fp,[rp],harvest)
            self.assertEqual(validate_repository_provenance(root,harvest),[])
            (root/'translation-data/source-adoptions/synthetic-first.json').unlink()
            self.assertTrue(any('owned title' in e for e in validate_repository_provenance(root,harvest)))
