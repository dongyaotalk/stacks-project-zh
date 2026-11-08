"""Current chapter acceptance. Git objects bound history; no persistent PASS cache."""
from __future__ import annotations

import json
import hashlib
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from weakref import WeakValueDictionary, finalize

from .current_qa import CurrentSourceQA, InputSnapshot
from .records import RecordError
from .schema_validation import validate_named_schema
from .validation_io import InputReads, current_inputs, tracked_inputs, glob_paths, remember_tree

_ISSUED = WeakValueDictionary()
_CLAIMS = {}


def git(root, *args, raw=False):
    p = subprocess.run(['git', '-C', str(root), *args], capture_output=True)
    if p.returncode:
        raise RecordError('Git identity unavailable: ' + ' '.join(args[:2]))
    return p.stdout if raw else p.stdout.decode().strip()


def inventory(root, reads):
    """Freeze names including ignored/untracked facts, without reading old contexts."""
    for name in ('translation-data', 'review', 'docs/evidence', 'task-scopes'):
        directory = root / name
        paths = tuple(directory.rglob('*'))
        if any(p.is_symlink() for p in paths):
            raise RecordError('fact inventory contains a symlink: ' + name)
        remember_tree(directory, '*', {p for p in paths if p.is_file()},
                      {p for p in paths if p.is_dir()} | ({directory} if directory.is_dir() else set()))


class Base:
    def __init__(self, root, ref, snapshot):
        self.root, self.snapshot = root, snapshot
        if not ref:
            raise RecordError('BASE_REF is required; no change acceptance without an accepted main commit')
        self.commit = git(root, 'rev-parse', '--verify', ref + '^{commit}')
        # Trust is a local main tracking ref or the event base installed by CI.
        anchors = []
        for anchor in ('refs/remotes/origin/main', 'refs/heads/main'):
            p = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', anchor], capture_output=True, text=True)
            if p.returncode == 0:
                anchors.append(p.stdout.strip())
        if not any(subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', self.commit, a],
                                 capture_output=True).returncode == 0 for a in anchors):
            raise RecordError('base is not in confirmed main history')
        if subprocess.run(['git', '-C', str(root), 'merge-base', '--is-ancestor', self.commit, snapshot.head],
                          capture_output=True).returncode:
            raise RecordError('base is not an ancestor of HEAD')
        self.tree = git(root, 'rev-parse', 'HEAD^{tree}')
        self.object_format = git(root, 'rev-parse', '--show-object-format')
        entries = git(root, 'ls-tree', '-r', '-z', self.commit, raw=True).split(b'\0')
        self.entries = {}
        for entry in filter(None, entries):
            mode_type_oid, path = entry.split(b'\t', 1)
            mode, kind, oid = mode_type_oid.decode().split()
            self.entries[path.decode()] = (mode, kind, oid)
        self.changed = set(git(root, 'diff', '--name-only', '--no-renames', '-z', self.commit, raw=True).decode().split('\0')) - {''}
        # ls-files --others without excludes includes ignored new facts. Generated
        # trees outside facts remain generated, not undeclared translation inputs.
        extra = git(root, 'ls-files', '--others', '-z', raw=True).decode().split('\0')
        self.changed.update(p for p in extra if p.startswith(('translation-data/', 'review/', 'docs/evidence/', 'task-scopes/')))
        extra_visible = git(root, 'ls-files', '--others', '--exclude-standard', '-z', raw=True).decode().split('\0')
        self.changed.update(filter(None, extra_visible))
        self._accepted = {}
        self.change_identity = self._change_identity()

    def _change_identity(self):
        return (git(self.root, 'diff', '--raw', '--no-renames', '-z', self.commit, raw=True),
                git(self.root, 'ls-files', '--others', '--exclude-standard', '-z', raw=True))

    def assert_unchanged(self):
        if self._change_identity() != self.change_identity:
            raise RecordError('Git change scope/type/mode changed during chapter validation')

    def accepted(self, relative):
        if relative in self._accepted:
            self.snapshot.read(self.root / relative)
            return self._accepted[relative]
        entry = self.entries.get(relative)
        if entry is None:
            return False
        path = self.snapshot._safe(self.root / relative)
        raw = self.snapshot.read(path)
        mode = '100755' if path.stat().st_mode & 0o111 else '100644'
        # Compare the real Git blob identity from the accepted tree. Re-reading
        # large packed historical blobs for every direct input adds no evidence.
        digest = hashlib.new(self.object_format)
        digest.update(b'blob ' + str(len(raw)).encode('ascii') + b'\0')
        digest.update(raw)
        same = entry[0] == mode and entry[1] == 'blob' and digest.hexdigest() == entry[2]
        self._accepted[relative] = same
        return same

    def immutable_changes(self):
        prefixes = ('translation-data/runs/', 'translation-data/retired/', 'translation-data/source-adoptions/',
                    'translation-data/source-adoption-inputs/', 'translation-data/derivations/',
                    'translation-data/model-corrections/', 'translation-data/source-container-restorations/',
                    'translation-data/derivation-archives/', 'translation-data/source-reextractions/',
                    'docs/evidence/')
        for p in sorted(self.changed):
            if p.startswith(prefixes) and p in self.entries:
                raise RecordError('accepted immutable input changed/deleted/renamed/mode changed: ' + p)


class AdoptionBoundary:
    """One invocation memo, with explicit accepted-node stopping. Strict APIs ignore it."""
    def __init__(self, base, emit):
        self.base, self.emit = base, emit
        self.prepared, self.replayed, self.visiting = {}, {}, set()
        self.accepted_inputs = set()
        self.nodes = set()
        self.cache = {}
        self.snapshots = {}

    def finish(self):
        merged={}
        for snapshot in self.snapshots.values():
            if snapshot.root not in merged:
                merged[snapshot.root]=InputSnapshot(snapshot.root)
            merged[snapshot.root].include_dependencies(snapshot)
        for snapshot in merged.values():snapshot.assert_unchanged()

    def prepare(self, root, entry, harvest, overrides, visiting):
        from . import source_adoptions as a
        key = (entry['path'], entry['hash'])
        if key in self.visiting:
            raise RecordError('cyclic new adoption chain')
        if key in self.prepared:
            value = self.prepared[key]
            probe = a.Reads(root, overrides)
            if all(a.byte_hash(probe.output(p)) == h for p,h in value[1].logical.items()):
                return value
            raise RecordError('shared node has conflicting direct input views')
        self.visiting.add(key)
        reads = a.Reads(root, overrides)
        frozen = reads.json(entry)
        a._schema(frozen, 'source-adoption-input.schema.json')
        record_path = 'translation-data/source-adoptions/' + frozen['adoption_id'] + '.json'
        if self.base.accepted(record_path) and self.base.accepted(entry['path']):
            # Direct input and outputs still checked by replay(); do not enter
            # accepted context, prior_attempts or retired ancestry.
            native = a.Containers(root, harvest)
            result = frozen, reads, native, {}
            self.accepted_inputs.add(entry['path'])
        else:
            self.emit('direct node: ' + frozen['adoption_id'])
            result = a._prepare_full(root, entry, harvest, overrides=overrides, visiting=visiting)
            self.nodes.add(record_path)
        self.visiting.remove(key)
        self.prepared[key] = result
        return result

    def replay(self, record, frozen, reads, native):
        from . import source_adoptions as a
        key = (frozen['adoption_id'], id(reads))
        if key in self.replayed:
            return self.replayed[key]
        if ('translation-data/source-adoption-inputs/' + frozen['adoption_id'] + '.json') in self.accepted_inputs:
            result = {}
            for output in record['outputs']:
                for role in ('units', 'candidates'):
                    entry = output[role]
                    raw = reads.output(entry['path'])
                    if a.byte_hash(raw) != entry['hash']:
                        raise RecordError('accepted ancestor direct output differs: ' + entry['path'])
                result[output['candidates']['path']] = a._rows(reads.output(output['candidates']['path']))
            if not self.base.accepted(record['run']['path']):
                raise RecordError('accepted ancestor run changed')
            value = result, reads.json(record['run'], r'translation-data/runs/[A-Za-z0-9._-]+\.json')
        else:
            value = a._replay_record_full(record, frozen, reads, native)
        self.replayed[key] = value
        return value


@dataclass(frozen=True)
class ChapterCheckResult:
    root: Path
    harvest: Path
    chapter: str
    lane: str
    pairs: tuple
    count: int
    current: CurrentSourceQA
    base: Base
    reads: InputReads
    adoptions: dict
    report: dict
    derivations: dict
    corrections: dict

    @property
    def snapshot(self):
        return self.current.snapshot

    @property
    def source(self):
        return self._source

    def assert_valid(self, root, harvest, units=None, candidates=None):
        if type(self) is not ChapterCheckResult or _ISSUED.get(id(self)) is not self:
            raise RecordError('chapter result is not from a live chapter check')
        if self.root != root.resolve() or self.harvest != (harvest or root.parent/'stacks-project').resolve():
            raise RecordError('chapter result root/source mismatch')
        if units is not None and tuple(zip(map(Path.resolve, units), map(Path.resolve, candidates), strict=True)) != self.pairs:
            raise RecordError('chapter result does not cover complete ordered pairs')
        claims = _CLAIMS[id(self)]
        from .repository_validation import _require_snapshot_claims
        self.reads.require_claims(claims[1])
        if self._binding() != claims[0]:
            raise RecordError('chapter result content changed')
        _require_snapshot_claims(self.snapshot, claims[2])
        from .repository_validation import _require_source_claims
        self.current._reads.require_claims(claims[3])
        _require_source_claims(self._source,claims[4])
        source=self._source
        if (not source.exists or self.harvest.is_symlink() or self.harvest.resolve()!=source.path
                or source.path.exists()!=source.exists or source._repository()!=source.repository
                or {p.name for p in source.path.glob('*.tex')}!=source.source_files):
            raise RecordError('source identity differs from this live chapter session')
        merged=InputReads()
        merged.include(self.reads)
        merged.include(self.current._reads)
        merged.seed_snapshot(self.snapshot)
        merged.seed_snapshot(source.snapshot)
        merged.assert_unchanged()
        self.snapshot.assert_identity()
        source.snapshot.assert_identity()
        self.base.assert_unchanged()
        self.current._implementation.assert_valid()
        self.current.containers.assert_unchanged()

    def _binding(self):
        from .records import sha256_value
        return sha256_value(dict(root=str(self.root), harvest=str(self.harvest), chapter=self.chapter,
            lane=self.lane, pairs=[(str(u),str(c)) for u,c in self.pairs], count=self.count,
            current=id(self.current), source=id(self._source), snapshot=id(self.snapshot),
            locations=self.current._pair_locations, base=self.base.commit, head=self.snapshot.head,
            derivations=self.derivations, corrections={str(k):{n:str(v) if isinstance(v,Path) else v for n,v in item.items()} for k,item in self.corrections.items()}, adoptions=[(p, uid, value['unit'], value['candidate'], {k:sorted(v) if isinstance(v,set) else v for k,v in vars(value['policy']).items()})
                       for (p,uid),value in self.adoptions.items()], report=self.report))


def discover(snapshot, chapter, lane, *, partial=False):
    root = snapshot.root
    if not lane or '/' in lane or '..' in lane:
        raise RecordError('invalid model lane')
    units, ids, selected = {}, set(), []
    for up in sorted(glob_paths(root/'translation-data/units', '*.jsonl')):
        rows = snapshot.jsonl(up)
        chapters = {u['chapter'] for u in rows}
        for u in rows:
            if u['unit_id'] in ids:
                raise RecordError('duplicate global unit ID: ' + u['unit_id'])
            ids.add(u['unit_id'])
        units[up.name] = (up, rows)
        if chapter in chapters:
            if chapters != {chapter}:
                raise RecordError('chapter scope contains mixed chapter file')
            cp=root/'translation-data/candidates'/lane/up.name
            if not partial or cp.exists():selected.append((up,cp))
    for cp in glob_paths(root/'translation-data/candidates', '*/*.jsonl'):
        if cp.name not in units:
            raise RecordError('candidate has no matching unit file: ' + str(cp))
    if not selected:
        raise RecordError('no complete chapter pairs found')
    for up, cp in selected:
        if not cp.is_file():
            raise RecordError('complete chapter has missing candidate pair: ' + cp.name)
        if {row.get('model_lane') for row in snapshot.jsonl(cp)} != {lane}:
            raise RecordError('complete chapter candidate directory/lane mismatch')
    return selected


@tracked_inputs
def check_chapter(root, harvest, chapter, lane, base_ref, *, report=None, current_all=False, _current=None, _joined=False):
    """Check one complete chapter plus directly associated new records, once."""
    from . import source_adoptions as a
    from .repository_validation import _SourceIdentity, _ImplementationIdentity, _snapshot_claims
    from .source_containers import clean
    from .provenance import _candidate_manifest_errors
    started = time.monotonic()
    emit = report or (lambda _: None)
    root = root.resolve()
    if str(chapter).isdigit():
        from .source_reextractions import _git_bytes
        from .records import load_upstream_commit
        from .workflow import manifest_chapters
        ordered=manifest_chapters(_git_bytes(harvest,load_upstream_commit(root/'upstream.lock'),'chapters.tex').decode())
        ordinal=int(chapter)
        if not 1 <= ordinal <= len(ordered):raise RecordError('invalid chapter ordinal')
        chapter=ordered[ordinal-1][0]
    snapshot = _current.snapshot if _current is not None else InputSnapshot(root)
    reads = current_inputs()
    inventory(root, reads)
    implementation = _ImplementationIdentity()
    reads.seed_implementation(implementation)
    base = Base(root, base_ref, snapshot)
    base.immutable_changes()
    from .ci_scope import classify
    dispatch = classify(root,base.commit,paths=base.changed)
    if not current_all and dispatch['kind'] == 'current-all':
        raise RecordError('scope expansion required: qa-current-all; ' + dispatch['reason'])
    if not current_all and not _joined and set(dispatch['chapters']) - {chapter}:
        raise RecordError('scope expansion required for all changed chapters: ' + ', '.join(dispatch['chapters']))
    selected = discover(snapshot, chapter, lane, partial=current_all)
    if not current_all and not _joined:
        pair_paths={p.relative_to(root).as_posix() for pair in selected for p in pair}
        outside=[p for p in base.changed if p.startswith(('translation-data/units/','translation-data/candidates/'))
                 and p.endswith('.jsonl') and p not in pair_paths]
        if outside:raise RecordError('changed pairs require all chapters/lanes: qa-current-all; '+', '.join(sorted(outside)))
    emit('scope: %s/%s %d complete pairs; history_audit=not_run' % (chapter,lane,len(selected)))
    for up, cp in selected:
        for path, schema in ((up,'unit.schema.json'),(cp,'candidate.schema.json')):
            for row in snapshot.jsonl(path):
                errors = validate_named_schema(clean(row), schema, str(path))
                if errors:
                    raise RecordError('\n'.join(errors))
    schema_seconds = time.monotonic()-started
    current = _current or CurrentSourceQA(root, harvest, snapshot=snapshot, fresh_chapters=True)
    if _joined:
        # Keep this owner's reads active for its QA only; direct historical
        # dependencies belong to the enclosing union, not every future QA call.
        with current._reads.activate():
            count, errors = current.validate_pairs([u for u,c in selected], [c for u,c in selected])
    else:
        count, errors = current.validate_pairs([u for u,c in selected], [c for u,c in selected])
    if errors:
        raise RecordError('\n'.join(errors))
    locations = current._pair_locations
    raw, native_rows, diagnostics = current.containers.document(chapter)
    offset=0
    for up,cp in selected:
        size=len(snapshot.jsonl(up));spans=locations[offset:offset+size];offset+=size
        if any(a[0]!=b[0] or b[1]<a[2] for a,b in zip(spans,spans[1:])):
            raise RecordError('chapter pair units do not follow locked source order')
    # File batches can interleave in source order. Coverage and collision checks
    # concern actual unit spans, never the envelope between a batch's ends.
    ordered=sorted(locations)
    if not current_all and any(a[0]==b[0] and b[1]<a[2] for a,b in zip(ordered,ordered[1:])):
        raise RecordError('chapter units overlap locked source containers')
    for row in (native_rows if not current_all else []):
        span = row['location']
        if not any(file == span['file'] and start <= span['byte_start'] and end >= span['byte_end']
                   for file,start,end in locations):
            raise RecordError('complete chapter source coverage missing: '+row['inventory_id'])
    emit('current source/structure/terms: PASS (%d units)' % count)
    current_seconds = time.monotonic()-started-schema_seconds
    boundary = AdoptionBoundary(base, emit)
    # Reuse this invocation's actual current alignment for disjointness. The
    # key binds the complete batch bytes, not a disk PASS or caller locations.
    offset=0
    from .records import sha256_value
    for up,cp in selected:
        rows=[clean(u) for u in snapshot.jsonl(up)]
        entries=[]
        for row,(file,start,end) in zip(rows,locations[offset:offset+len(rows)],strict=True):
            entries.append(dict(unit_id=row['unit_id'],status='BYTE_EXACT',extractor_state='READY',
                                location=dict(file=file,byte_start=start,byte_end=end)))
        boundary.cache[('aligned-batch',sha256_value(rows))]=(entries,{})
        offset+=len(rows)
    boundary.cache[('containers',str(root),str(harvest),a.byte_hash(current.containers.policy_bytes))]=current.containers
    boundary.cache[('corpus',str(root),str(harvest),chapter)]=(current._corpora[(chapter,)],current.containers)
    adopted, candidates = {}, []
    for up, cp in selected:
        for c in snapshot.jsonl(cp):
            candidates.append((cp.relative_to(root).as_posix(),clean(c)))
    identifiers = {c['source_adoption_id'] for _,c in candidates if c.get('source_adoption_id')}
    token = a._DAILY.set(boundary)
    try:
        for identifier in sorted(identifiers):
            path = root/'translation-data/source-adoptions'/f'{identifier}.json'
            record = json.loads(snapshot.read(path))
            a._schema(record, 'source-adoption.schema.json')
            if record['adoption_id'] != identifier:
                raise RecordError('source adoption ID/path mismatch')
            frozen, used, native, histories = a._prepare(root, record['input'], harvest)
            expected, manifest = a._replay_record(record, frozen, used, native)
            snapshot.include_dependencies(used.snapshot)
            for batch in frozen['batches']:
                up, cp = root/batch['units_path'], root/batch['candidates_path']
                if (up,cp) not in selected:
                    # A shared generation extends validation, never silently skips participants.
                    raise RecordError('shared run extends chapter/lane; use qa-current-all: ' + str(cp))
                actual = [clean(c) for c in snapshot.jsonl(cp)]
                if actual != expected[batch['candidates_path']]:
                    raise RecordError('current candidate differs from direct raw/run relation')
                for unit,candidate in zip(batch['units'],actual,strict=True):
                    adopted[(batch['candidates_path'],unit['unit_id'])] = dict(unit=unit,candidate=candidate,policy=native.policy)
        for relative,c in candidates:
            if c.get('derivation_id') or c.get('model_correction_id'):
                continue  # Exact deterministic direct replay follows below.
            elif not c.get('source_adoption_id'):
                # Reuse the actual ordinary-run five-field, identity and complete order validator.
                pass
        ordinary = {}
        for relative,c in candidates:
            if (not c.get('source_adoption_id') and not c.get('derivation_id') and not c.get('model_correction_id')
                    and not (base.accepted(relative) and base.accepted('translation-data/units/'+Path(relative).name)
                             and base.accepted('translation-data/runs/'+c['run_id']+'.json'))):
                ordinary.setdefault(relative,[]).append(c)
        if ordinary:
            for run_id in {c['run_id'] for rows in ordinary.values() for c in rows}:
                manifest=json.loads(snapshot.read(root/'translation-data/runs'/f'{run_id}.json'))
                participants={e['candidate_path'] for e in manifest['inputs'].get('settings',{}).get('accepted_records',[])}
                if not current_all and participants - {c.relative_to(root).as_posix() for u,c in selected}:
                    raise RecordError('shared run requires all participating chapters/lanes: qa-current-all')
            a._complete_prior_runs(a.Reads(root), {p:[rows] for p,rows in ordinary.items()})
        manifests = {}
        for _,c in candidates:
            path = root/'translation-data/runs'/f"{c['run_id']}.json"
            if c['run_id'] not in manifests:
                manifest = json.loads(snapshot.read(path))
                errors = validate_named_schema(manifest, 'run-manifest.schema.json', str(path))
                if errors:
                    raise RecordError('\n'.join(errors))
                manifests[c['run_id']] = path, manifest
        errors = _candidate_manifest_errors(root, [(p,lane,c) for p,c in candidates], manifests,
                                            context_order=False, current_derivations=True)
        if errors:
            raise RecordError('\n'.join(errors))
    finally:
        a._DAILY.reset(token)
    from .chapter_relations import check_derivations
    token = a._DAILY.set(boundary)
    try:
        derivations,corrections=check_derivations(root,harvest,selected,base,snapshot,current.containers.english.tags)
    finally:
        a._DAILY.reset(token)
    # Newly recorded failed generation is still a real run/freeze/raw input.
    for relative in sorted(base.changed):
        if relative.startswith('translation-data/runs/') and relative.endswith('.json'):
            path = root/relative
            manifest = json.loads(snapshot.read(path))
            if 'frozen_generation_input' in manifest.get('inputs',{}).get('settings',{}):
                token = a._DAILY.set(boundary)
                try:
                    snapshot.include_dependencies(a._recorded_failed_generation(root,path,manifest,harvest))
                finally:
                    a._DAILY.reset(token)
        if relative.startswith(('task-scopes/','translation-data/chapter-templates/')) and relative.endswith('.json'):
            schema = 'task-scope.schema.json' if relative.startswith('task-scopes/') else 'chapter-template.schema.json'
            errors = validate_named_schema(json.loads(snapshot.read(root/relative)),schema,relative)
            if errors:raise RecordError('\n'.join(errors))
    from .chapter_relations import check_preparation_evidence
    token = a._DAILY.set(boundary)
    try:
        preparations=check_preparation_evidence(root,harvest,snapshot,base.changed,chapter,lane,reads,current.containers)
    finally:
        a._DAILY.reset(token)
    direct_seconds = time.monotonic()-started-schema_seconds-current_seconds
    # Decisions use their existing complete linkage checks with a scoped candidate
    # index. No disk success or fabricated historical provenance is supplied.
    from .decisions import validate_current_decisions
    token = a._DAILY.set(boundary)
    try:
        errors = validate_current_decisions(root, harvest, selected, changed=base.changed, base=base)
    finally:
        a._DAILY.reset(token)
    if _joined:
        boundary.finish()  # Collected into the enclosing current union.
    else:
        for dependency in boundary.snapshots.values():
            snapshot.include_dependencies(dependency)
    if errors:
        raise RecordError('\n'.join(errors))
    if not current_all and not _joined:
        unread = [p for p in base.changed if p.startswith(('translation-data/','review/','docs/evidence/','task-scopes/'))
                  and (root/p).resolve() not in reads.hashes]
        if unread:
            raise RecordError('changed inputs outside checked direct scope; expand/repair: '+', '.join(sorted(unread)))
    source = _SourceIdentity(root, harvest)
    result_report = dict(schema_version=1, scope='current-pairs' if current_all else 'chapter-current', history_audit='not_run',
        base=base.commit, head=snapshot.head, tree=base.tree, input_view='worktree',
        implementation=implementation.binding(), source_commit=current.source_commit, chapter=chapter, lane=lane,
        pairs=len(selected), units=count, extensions=[], complete_chapter_coverage='not_required' if current_all else 'PASS',
        stages=dict(schema=schema_seconds,current=current_seconds,direct=direct_seconds,
                    decisions=time.monotonic()-started-schema_seconds-current_seconds-direct_seconds),
        preparations=preparations, direct_nodes=len(boundary.nodes), accepted_boundaries=len(boundary.accepted_inputs),
        seconds=time.monotonic()-started, errors=[], exit_status=0)
    result = ChapterCheckResult(root,current.harvest.resolve(),chapter,lane,tuple(selected),count,current,base,reads,adopted,result_report,derivations,corrections)
    object.__setattr__(result, '_source', source)
    if _joined:
        # A joined current check uses these reports only. Do not issue a render
        # receipt or repeatedly bind/re-read all preceding scopes' inputs.
        result_report['validation_state'] = 'pending_union'
        emit('%s: checked; final input union pending (%.3fs)' % (result_report['scope'],result_report['seconds']))
        return result
    _ISSUED[id(result)] = result
    from .repository_validation import _source_claims
    _CLAIMS[id(result)] = (result._binding(), reads.claims(), _snapshot_claims(snapshot),
                           current._reads.claims(), _source_claims(source))
    finalize(result,_CLAIMS.pop,id(result),None)
    result.assert_valid(root,harvest)
    emit('%s: PASS; history_audit=not_run (%.3fs)' % (result_report['scope'],result_report['seconds']))
    return result


@tracked_inputs
def check_current_repository(root, harvest, base_ref, *, report=None, chapters=None):
    """All current pairs/direct inputs, retaining the same accepted-ancestor boundary."""
    root=root.resolve()
    reads=current_inputs()
    inventory(root,reads)
    snapshot=InputSnapshot(root)
    base=Base(root,base_ref,snapshot)
    base.immutable_changes()
    scopes=set()
    from .source_containers import clean
    candidates=list(glob_paths(root/'translation-data/candidates','*/*.jsonl'))
    paired_names={cp.name for cp in candidates}
    for up in glob_paths(root/'translation-data/units','*.jsonl'):
        rows=snapshot.jsonl(up)
        selected=chapters is None or any(u.get('chapter') in chapters for u in rows)
        if not selected:continue
        # Reading the global ID inventory is not Schema validation. A current
        # unit with no candidate must not disappear from the union's scopes.
        for row in rows:
            errors=validate_named_schema(clean(row),'unit.schema.json',str(up))
            if errors:raise RecordError('\n'.join(errors))
        if up.name not in paired_names:
            raise RecordError('current unit has no candidate pair: '+str(up))
    for cp in candidates:
        up=root/'translation-data/units'/cp.name
        rows=snapshot.jsonl(up)
        scopes.update((u['chapter'],cp.parent.name) for u in rows if chapters is None or u['chapter'] in chapters)
    current=CurrentSourceQA(root,harvest,snapshot=snapshot,fresh_chapters=True)
    reports=[]
    from . import source_adoptions as a
    boundary=AdoptionBoundary(base,report or (lambda line:None))
    token=a._DAILY.set(boundary)
    try:
        for chapter,lane in sorted(scopes):
            result=check_chapter(root,harvest,chapter,lane,base_ref,report=report,current_all=chapters is None,_current=current,_joined=True)
            reports.append(result.report)
    finally:
        a._DAILY.reset(token)
    boundary.finish()
    unread=[p for p in base.changed if p.startswith(('translation-data/','review/','docs/evidence/','task-scopes/'))
            and (root/p).resolve() not in reads.hashes]
    if unread:raise RecordError('changed inputs have no validated current relationship: '+', '.join(sorted(unread)))
    current.assert_unchanged()
    base.assert_unchanged()
    for result_report in reports:
        result_report['validation_state'] = 'validated_current'
    return dict(schema_version=1,scope='current-all' if chapters is None else 'chapter-current',history_audit='not_run',base=base.commit,
                head=snapshot.head,chapters=reports,exit_status=0)
