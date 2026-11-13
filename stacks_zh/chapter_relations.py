"""Direct derivation replay, stopping at unchanged accepted parent outputs."""
import json
import re
import subprocess
from .records import RecordError, load_jsonl
from .source_containers import clean, safe_path, load_source_containers
from .source_reextractions import byte_hash, load_source_reextractions
from .model_corrections import load_repository_corrections
from .derivation_archives import load_derivation_archives
from .derivations import replay_derivation, jsonl_bytes, _git_origin_bytes
from .group_derivations import correction_bindings, restoration_bindings
from .schema_validation import validate_named_schema


def check_derivations(root, harvest, pairs, base, snapshot, tags):
    records, cache, visiting, histories, corrections = {}, {}, set(), {}, {}
    def path_for(identifier):
        return safe_path(root,'translation-data/derivations/'+identifier+'.json',r'translation-data/derivations/[A-Za-z0-9._-]+\.json')
    def visit(identifier, saved=None):
        if identifier in visiting:raise RecordError('cyclic direct derivation chain')
        if identifier in cache:return cache[identifier]
        visiting.add(identifier)
        path=path_for(identifier)
        record=json.loads(snapshot.read(path));records[identifier]=record
        errors=validate_named_schema(record,'derivation.schema.json',str(path))
        if errors:raise RecordError('\n'.join(errors))
        if record['derivation_id']!=identifier:raise RecordError('derivation ID/path mismatch')
        entries=record['files']
        outputs={}
        for role in ('output_units','output_candidates'):
            entry=entries[role]
            raw=snapshot.read(root/(saved[role] if saved else entry['path']))
            if byte_hash(raw)!=entry['hash']:raise RecordError('direct derivation output hash mismatch')
            outputs[role]=[clean(x) for x in load_jsonl(root/(saved[role] if saved else entry['path']))]
        if base.accepted(path.relative_to(root).as_posix()):
            # The accepted record binds these exact parent outputs. No recursive
            # history/context replay and no invented approval inheritance.
            value=(outputs['output_units'],outputs['output_candidates'])
            loaded,errors=load_repository_corrections(root,identifiers={key[0] for key in correction_bindings(record)})
            if errors:raise RecordError('\n'.join(errors))
            corrections.update(loaded)
            visiting.remove(identifier);cache[identifier]=value
            return value
        inputs={}
        for role,out_role in [('input_units','output_units'),('input_candidates','output_candidates')]:
            entry=entries[role]
            path=safe_path(root,entry['path'],rf'translation-data/retired/derivations/{re.escape(identifier)}/(?:units|candidates)\.jsonl')
            raw=snapshot.read(path)
            if (byte_hash(raw)!=entry['hash'] or raw!=_git_origin_bytes(root,record['origin_commit'],entries[out_role]['path'])):
                raise RecordError('direct derivation input differs from exact origin')
            inputs[role]=[clean(x) for x in load_jsonl(path)]
        previous=None
        for run_id in {c['run_id'] for c in inputs['input_candidates']}:
            relative='translation-data/runs/'+run_id+'.json'
            if snapshot.read(root/relative)!=_git_origin_bytes(root,record['origin_commit'],relative):
                raise RecordError('direct derivation origin run differs from exact origin')
        parent=record.get('previous_derivation_id')
        if parent:
            archives,errors=load_derivation_archives(root,identifiers={parent})
            if errors:raise RecordError('\n'.join(errors))
            archive=archives[parent]
            if archive['manifest']['successor_derivation_id']!=identifier:raise RecordError('direct parent has wrong successor')
            previous=visit(parent,{role:p.relative_to(root).as_posix() for role,p in archive['outputs'].items()})
        correction_ids={key[0] for key in correction_bindings(record)}
        loaded,errors=load_repository_corrections(root,identifiers=correction_ids)
        if errors:raise RecordError('\n'.join(errors))
        corrections.update(loaded)
        reids={op['source_reextraction_id'] for op in record.get('operations',[]) if op.get('source_reextraction_id')}
        reextractions,errors=load_source_reextractions(root,harvest,identifiers=reids)
        if errors:raise RecordError('\n'.join(errors))
        restorations,errors=load_source_containers(root,harvest,identifiers=set(restoration_bindings(record)))
        if errors:raise RecordError('\n'.join(errors))
        value=replay_derivation(record,inputs['input_units'],inputs['input_candidates'],loaded,previous,reextractions,restorations,tags)
        if value!=(outputs['output_units'],outputs['output_candidates']):raise RecordError('direct derivation replay differs from current output')
        # New model outputs must retain all five fields and actual raw bindings.
        from .source_adoptions import _complete_prior_runs, Reads
        for key,item in loaded.items():
            row=item['candidate']
            output=row['context'].get('model_output')
            if not output:raise RecordError('new correction has no immutable raw model output binding')
            raw=[json.loads(line) for line in snapshot.read(root/output['path']).decode().splitlines() if line.strip()]
            matches=[x for x in raw if x.get('unit_id')==row['unit_id']]
            from .records import sha256_value
            from .source_adoptions import FIELDS
            if (byte_hash(snapshot.read(root/output['path']))!=output['hash'] or len(matches)!=1
                    or sha256_value(matches[0])!=output['record_hash'] or any(row[f]!=matches[0][f] for f in FIELDS)):
                raise RecordError('new correction five fields differ from actual model raw')
        visiting.remove(identifier);cache[identifier]=value
        return value
    for up,cp in pairs:
        for c in snapshot.jsonl(cp):
            if c.get('derivation_id'):
                identifier=c['derivation_id']
                units,rows=visit(identifier)
                if [clean(x) for x in snapshot.jsonl(up)]!=units or [clean(x) for x in snapshot.jsonl(cp)]!=rows:
                    raise RecordError('derivation does not cover complete current pair')
                histories[identifier]=[dict(derivation=records[identifier],previous_archive=None)]
            elif c.get('model_correction_id'):
                raise RecordError('correction requires a validated derivation')
    return histories,corrections


def _assert_unadopted_preparation(root, frozen, snapshot):
    """Negative preparation diagnostics cannot belong to an installed identity."""
    aid, run_id = frozen['adoption_id'], frozen['run_id']
    if (frozen['tool_version'] not in {'source-adoption-input-v1','source-adoption-input-v4'}
            or 'prior_adoptions' in frozen or 'shared_run_histories' in frozen
            or any(b['prior_attempts'] for b in frozen['batches'])
            or (root/f'translation-data/source-adoptions/{aid}.json').exists()
            or (root/f'translation-data/runs/{run_id}.json').exists()):
        raise RecordError('rejected preparation must have no run/adoption or predecessor')
    task=frozen['task']
    sp=safe_path(root,task['scope_manifest'],r'task-scopes/[A-Za-z0-9._-]+\.json')
    if snapshot.read(sp)!=task['scope_bytes'].encode('utf-8'):
        raise RecordError('rejected preparation original scope bytes changed')
    for batch in frozen['batches']:
        cp=safe_path(root,batch['candidates_path'],r'translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl')
        if cp.exists() and any(c.get('run_id')==run_id or c.get('source_adoption_id')==aid
                              for c in snapshot.jsonl(cp)):
            raise RecordError('rejected preparation identity supplies a current candidate')
    accepted=any(all(subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',x,y],
                    capture_output=True).returncode==0
                    for x,y in ((frozen['origin_commit'],anchor),(anchor,'HEAD')))
                 for anchor in ('refs/remotes/origin/main','refs/heads/main'))
    if not accepted:raise RecordError('rejected preparation origin is not accepted main ancestry')


def _preparation_task_scope(root, frozen, entry, snapshot):
    """Keep a known rejected lane/model-ID mix-up as negative inventory only."""
    from . import source_adoptions as a
    try:
        return a._task_scope(frozen,a.Reads(root),entry,current=False), []
    except RecordError as exc:
        if str(exc) != 'first-source runtime or semantic coordinates escape the frozen task scope':
            raise
        original_error = str(exc)
    _assert_unadopted_preparation(root,frozen,snapshot)
    aid, run_id = frozen['adoption_id'], frozen['run_id']
    task = frozen['task']
    # The strict call already verified the complete manifest hash, structure,
    # unique files/units and one owner; preserve its original model_scope.
    scope=json.loads(task['scope_bytes'])
    paths={entry['path'],f'translation-data/source-adoptions/{aid}.json',f'translation-data/runs/{run_id}.json'}
    for batch in frozen['batches']:
        paths.update((batch['units_path'],batch['candidates_path']))
    owners=[c for c in scope['data_scopes'] if paths<=set(c['allowed_write_files'])
            and set(frozen['unit_ids'])<=set(c['output_unit_ids'])]
    if len(owners)!=1:raise RecordError(original_error)
    child=owners[0];model=frozen['runtime']['model'];lane=frozen['runtime']['model_lane']
    if (run_id not in child['run_scope'] or child['chapter']!=frozen['chapter']
            or not set(frozen['parent_tags'])<=set(child['parent_tags'])
            or set(child['model_scope']) not in ({lane},{lane,model['record_id']})
            or model['requested_id']!=model['resolved_id']
            or model['requested_id'] in child['model_scope']
            or model['identity_confidence']=='unknown'):
        raise RecordError(original_error)
    return child,[original_error]


def _rejected_preparation_registry(frozen, policy_bytes):
    from .provenance import _parse_registry_section, _registry_scalar
    runtime=frozen['runtime'];model=runtime['model'];harness=runtime['harness']
    text=policy_bytes['config/models.yml'].decode('utf-8')
    record=_parse_registry_section(text,'model_records').get(model['record_id'])
    lane=_parse_registry_section(text,'lanes').get(runtime['model_lane'])
    registered_harness=_parse_registry_section(policy_bytes['config/harnesses.yml'].decode('utf-8'),'harnesses').get(harness['id'])
    if (record is None or lane is None or registered_harness is None
            or harness['version'].lower() in {'auto','unknown','unavailable'}
            or registered_harness.get('adapter_version')!=harness['adapter_version']
            or any(expected is not None and _registry_scalar(model.get(key))!=expected
                   for key,expected in record.items() if key in model)
            or any(lane.get(key)!=actual for key,actual in [('model_id',model['resolved_id']),
                ('model_record_id',model['record_id']),('harness_id',harness['id']),('prompt_version','translator-v2')])):
        raise RecordError('rejected preparation identity differs from accepted registry')


def _preparation_policy_bytes(root, frozen, snapshot):
    from .source_adoptions import _SOURCE_SCHEMAS
    original={e['path']:_git_origin_bytes(root,frozen['origin_commit'],e['path']) for e in frozen['policies']}
    changed=[e['path'] for e in frozen['policies'] if byte_hash(original[e['path']])!=e['hash']]
    if not changed:return original,[],None
    _assert_unadopted_preparation(root,frozen,snapshot)
    if not set(changed)<=_SOURCE_SCHEMAS:
        raise RecordError('preparation policy differs from accepted origin')
    # A wrong origin is retained as a rejection, never repaired into authority.
    # Only the already-versioned source Schemas may differ, and one real later
    # accepted Git snapshot must match the complete frozen policy set exactly.
    for anchor in ('refs/remotes/origin/main','refs/heads/main'):
        if any(subprocess.run(['git','-C',str(root),'merge-base','--is-ancestor',x,y],capture_output=True).returncode
               for x,y in ((frozen['origin_commit'],anchor),(anchor,'HEAD'))):continue
        revisions=subprocess.check_output(['git','-C',str(root),'rev-list','--reverse',
            frozen['origin_commit']+'..'+anchor,'--',*changed],text=True).split()
        for revision in revisions:
            candidate={e['path']:_git_origin_bytes(root,revision,e['path']) for e in frozen['policies']}
            if all(byte_hash(candidate[e['path']])==e['hash'] for e in frozen['policies']):
                return candidate,['preparation policy differs from accepted origin'],revision
    raise RecordError('rejected preparation source Schemas lack one complete accepted policy snapshot')


_LEGACY_QUALIFIED_DECLARATION_SHA256='285702aa741be01ead31012ebcba1ea8fd3ea2f35e82b422b630bcef96383cae'


def _legacy_zeroth_preparation_projection(root, frozen, units, expected, observed, reserved, snapshot):
    """Compare the exact old pure-preparation caron-prefix projection as data."""
    import ast
    import copy
    import hashlib
    from .source_terms import source_projection
    if any(safe_path(root,p,r'docs/evidence/[A-Za-z0-9._-]+\.jsonl').exists() for p in reserved):return False
    _assert_unadopted_preparation(root,frozen,snapshot)
    text=_git_origin_bytes(root,frozen['origin_commit'],'stacks_zh/source_terms.py').decode('utf-8')
    functions=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='_qualified_declaration_parts']
    if len(functions)!=1 or hashlib.sha256(ast.get_source_segment(text,functions[0]).encode()).hexdigest()!=_LEGACY_QUALIFIED_DECLARATION_SHA256:return False
    comparison=copy.deepcopy(expected);changed=0
    for unit,inventory in zip(units,comparison):
        witnesses=list(re.finditer(r'zeroth <(GROUPOPEN_([0-9]{4}))><(ACCENT_[0-9]{4})><(GROUPCLOSE_\2)>ech cohomology group',unit['source_text']))
        if len(witnesses)!=1:continue
        witness=witnesses[0]
        if [unit['placeholders'].get(witness[i]) for i in (1,3,4)]!=['{',r'\v C','}']:continue
        projection=source_projection(unit)[0]
        for row in inventory['occurrences']:
            start,end=row['projection_start'],row['projection_end']
            if (row['rule']=='source-declaration' and row['source_term']==row['concept']=='cohomology group'
                    and start>=4 and projection[start-4:end]=='ech cohomology group'):
                row.update(source_term='ech cohomology group',concept='ech cohomology group',projection_start=start-4)
                changed+=1
    return changed==1 and comparison==observed


def _model_policy_matches(field, value, raw, expected_hash):
    """Accept an empty entry inventory only against the complete locked glossary."""
    if byte_hash(raw) != expected_hash:
        return False
    if value == raw.decode('utf-8'):
        return True
    if field != 'glossary' or not isinstance(value, list) or value:
        return False
    from .terminology import _yaml_entries
    try:
        return _yaml_entries(raw.decode('utf-8')) == []
    except ValueError:
        return False


def check_preparation_evidence(root, harvest, snapshot, changed, chapter, lane, reads, native):
    """Check actual model-input/runtime copies, including never-adopted preparation.

    A saved preparation is not a run or an adoption. It cannot supply a current
    candidate or an ancestor receipt; those remain subject to actual replay.
    """
    from . import source_adoptions as a
    diagnostics=[]
    for relative in sorted(changed):
        if not relative.startswith('docs/evidence/') or not relative.endswith('-model-input.json'):
            continue
        model_input=json.loads(snapshot.read(root/relative))
        required={'generation_freeze','runtime','scope_manifest','prompt','style','glossary',
                  'source_units','locked_english_contexts','policy_git_origin','policy_files',
                  'raw_output_paths_reserved','rules'}
        optional={'required_source_occurrences','previous_complete_candidates','regeneration_reason'}
        if not required <= model_input.keys() or model_input.keys()-required-optional:
            raise RecordError('unknown/incomplete model-input evidence: '+relative)
        entry=model_input['generation_freeze']
        frozen=json.loads(snapshot.read(safe_path(root,entry['path'],r'translation-data/source-adoption-inputs/[A-Za-z0-9._-]+\.json')))
        if frozen['chapter']!=chapter or frozen['runtime']['model_lane']!=lane:
            continue  # The joined CI/current-all scope must consume its actual owner.
        a._schema(frozen,'source-adoption-input.schema.json')
        if (entry['path'] != f"translation-data/source-adoption-inputs/{frozen['adoption_id']}.json"
                or relative != f"docs/evidence/{frozen['adoption_id']}-model-input.json"
                or frozen['run_id'] != 'run-'+frozen['adoption_id']
                or frozen['source_commit'] != native.english.commit):
            raise RecordError('preparation identity/path/locked source mismatch')
        if byte_hash(snapshot.read(root/entry['path']))!=entry['hash']:
            raise RecordError('model-input differs from actual generation freeze')
        scope,scope_errors=_preparation_task_scope(root,frozen,entry,snapshot)
        units=[u for b in frozen['batches'] for u in b['units']]
        if (model_input['runtime']!=frozen['runtime'] or model_input['source_units']!=units
                or model_input['locked_english_contexts']!=frozen['contexts']
                or model_input['policy_git_origin']!=frozen['origin_commit']
                or model_input['policy_files']!=frozen['policies']
                or model_input['scope_manifest']!=dict(path=frozen['task']['scope_manifest'],hash=frozen['task']['scope_manifest_sha256'])):
            raise RecordError('model-input evidence differs from its complete frozen inputs')
        policies={e['path']:e for e in frozen['policies']}
        required_policies = a.REFERENCE_POLICIES if frozen['tool_version'] == 'source-adoption-input-v6' else a.POLICIES
        if len(policies)!=len(required_policies) or set(policies)!=set(required_policies):
            raise RecordError('preparation lacks complete frozen policies')
        policy_bytes,policy_errors,schema_witness=_preparation_policy_bytes(root,frozen,snapshot)
        if frozen['source_commit'] not in policy_bytes['upstream.lock'].decode():
            raise RecordError('preparation differs from frozen English lock')
        if scope_errors or policy_errors:_rejected_preparation_registry(frozen,policy_bytes)
        from .source_terms import source_inventory
        legacy_projection=False
        if 'required_source_occurrences' in model_input:
            catalog=json.loads(policy_bytes['config/source-terms.json'])
            expected=[source_inventory(u,catalog) for u in units]
            if model_input['required_source_occurrences']!=expected:
                legacy_projection=_legacy_zeroth_preparation_projection(root,frozen,units,expected,
                    model_input['required_source_occurrences'],model_input['raw_output_paths_reserved'],snapshot)
                if not legacy_projection:raise RecordError('model-input term occurrences differ from frozen source')
        previous=model_input.get('previous_complete_candidates',[])
        if not isinstance(previous,list) or not isinstance(model_input.get('regeneration_reason',''),str):
            raise RecordError('malformed preparation revision metadata')
        for item in previous:
            path=safe_path(root,item['archive_path'],r'translation-data/retired/source-adoptions/.+/candidates\.jsonl')
            payload=snapshot.read(path)
            if (byte_hash(payload)!=item['hash'] or a._rows(payload)!=item['records']
                    or item['path'] not in {b['candidates_path'] for b in frozen['batches']}):
                raise RecordError('model-input previous candidates differ from immutable snapshot')
        for field,path in [('prompt','prompts/translator-v2.md'),('style','config/style-guide.md'),('glossary','config/glossary.yml')]:
            raw=_git_origin_bytes(root,frozen['origin_commit'],path)
            if not _model_policy_matches(field,model_input[field],raw,policies[path]['hash']):
                raise RecordError('model-input prompt/style/glossary differs from locked origin')
        runtime_path=relative.removesuffix('-model-input.json')+'-runtime.json'
        runtime=json.loads(snapshot.read(root/runtime_path))
        if (runtime.get('runtime')!=frozen['runtime'] or runtime.get('harness_check',{}).get('exit_code')!=0
                or runtime['harness_check'].get('observed_version')!=frozen['runtime']['harness']['version']):
            raise RecordError('runtime evidence differs from frozen actual runtime')
        metadata=runtime.get('turn_metadata',{})
        if (metadata.get('turn_id')!=frozen['runtime']['turn_id']
                or metadata.get('model')!=frozen['runtime']['model']['requested_id']
                or metadata.get('effort')!=frozen['runtime']['reasoning_effort']
                or runtime.get('provider','').lower()!=frozen['runtime']['model']['provider'].lower()):
            raise RecordError('runtime turn metadata differs from frozen identity')
        reserved=model_input['raw_output_paths_reserved']
        if (not isinstance(reserved,list) or len(reserved)!=len(set(reserved))
                or not isinstance(model_input['rules'],str) or not model_input['rules'].strip()):
            raise RecordError('malformed preparation raw reservations/rules')
        for p in [relative,runtime_path,*reserved]:
            if p not in scope['allowed_write_files']:
                raise RecordError('model-input/runtime/raw evidence escapes frozen task scope')
        aid=frozen['adoption_id']
        adopted=root/'translation-data/source-adoptions'/f'{aid}.json'
        run=root/'translation-data/runs'/f"{frozen['run_id']}.json"
        if adopted.exists() or run.exists():
            required=adopted if adopted.exists() else run
            if required.resolve() not in reads.hashes:
                raise RecordError('preparation references an unchecked adopted node; expand scope')
            diagnostics.append(dict(input=entry['path'],status='adopted-input-copy-verified' if adopted.exists() else 'recorded-failed-run-input-copy-verified'))
            continue
        # No run/adoption was created. Validate complete aggregate coverage with
        # the existing raw parser, including independently frozen shards/retries.
        # This inventory check does not claim actual accepted generation.
        attempts=[]
        for p in model_input['raw_output_paths_reserved']:
            path=safe_path(root,p,r'docs/evidence/[A-Za-z0-9._-]+\.jsonl')
            if not path.exists():continue
            raw=snapshot.read(path)
            rows=[json.loads(x) for x in raw.decode().splitlines() if x.strip()]
            attempts.append(dict(path=p,hash=byte_hash(raw),unit_ids=[row.get('unit_id') for row in rows]))
        if attempts:a._raw_records(a.Reads(root),attempts,frozen['unit_ids'],scope['allowed_write_files'])
        prep_native=a._daily_containers(root,harvest,policy_bytes['config/macro-policy.yml'])
        # Preparations are inventory, not successful generation. Check the
        # canonical lowered source and report non-native selector snapshots as
        # rejected preparation, never as usable ancestry or current evidence.
        source_errors=[]
        from .source_containers import lower_container
        for batch in frozen['batches']:
            lowered=[]
            for group in batch['containers']:
                selected=prep_native.select(group['selector'])
                lowered.extend(clean(u) for u in lower_container(selected,prep_native.policy))
                if selected!=group['selected']:
                    source_errors.append('first adoption container differs from its real complete Git selector')
            if lowered!=batch['units']:
                raise RecordError('unadopted preparation source lowering differs from locked English')
        from .records import sha256_value
        if (len({c['context_id'] for c in frozen['contexts']})!=len(frozen['contexts'])
                or any(sha256_value(c['value'])!=c['hash'] for c in frozen['contexts'])):
            raise RecordError('preparation context hash/identity differs')
        try:
            a._context_sources(frozen,prep_native)
        except RecordError as exc:
            if str(exc)!='English context is not its complete real semantic IR node':raise
            source_errors.append(str(exc))
        rejection=root/(relative.removesuffix('-model-input.json')+'-preparation-rejection.json')
        if rejection.exists():
            value=json.loads(snapshot.read(rejection))
            if (value.get('kind')!='rejected-unadopted-generation-preparation'
                    or value.get('adoption_id_requested')!=aid or value.get('run_id_requested')!=frozen['run_id']
                    or any(value.get(key) is not False for key in ['candidate_installed','run_manifest_created','source_adoption_created'])):
                raise RecordError('preparation rejection claims an installed run/adoption')
            for key,expected in [('input',entry),('runtime',dict(path=runtime_path,hash=byte_hash(snapshot.read(root/runtime_path)))),('model_input',dict(path=relative,hash=byte_hash(snapshot.read(root/relative))))]:
                if value.get(key)!=expected:raise RecordError('preparation rejection input binding differs')
            for item in value.get('raw_attempts',[]):
                if item['path'] not in model_input['raw_output_paths_reserved'] or byte_hash(snapshot.read(root/item['path']))!=item['hash']:
                    raise RecordError('preparation rejection raw binding differs')
            if (value.get('observed_assembly_exit_code')!=1
                    or value.get('failure_stage')!='complete-native-selector-freeze'
                    or not source_errors or value.get('observed_assembly_error')!='ERROR: '+source_errors[0]):
                raise RecordError('preparation rejection does not reproduce at native selector gate')
        diagnostics.append(dict(input=entry['path'],status='rejected-unadopted-preparation' if source_errors or scope_errors or policy_errors else 'unadopted-preparation',source_errors=sorted(set(source_errors)),scope_errors=scope_errors,policy_errors=policy_errors,source_schema_witness=schema_witness,legacy_zeroth_projection=legacy_projection,run_created=run.exists(),
                                generation_validation='not_claimed',history_audit='not_run'))
    return diagnostics
