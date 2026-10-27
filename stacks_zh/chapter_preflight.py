"""Read-only chapter capability preparation, separate from facts and approval."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import tempfile
import tomllib

from .batching import LIMIT_RE, MIN_BATCH_FILES, MAX_BATCH_FILES, _source_word_count
from .chapter_templates import manifest_chapters, _source_sections
from .current_qa import CurrentSourceQA, InputSnapshot
from .preflight_state import PreparationRun, canonical_bytes, generated_path, value_hash
from .progress import _chapter_source, _load_chapters, _load_tag_index
from .progress_coverage import native_container_tag_coverage
from .records import RecordError, PLACEHOLDER_TOKEN_RE
from .repository_validation import _ImplementationIdentity, _SourceIdentity
from .source_containers import Containers, clean, lower_container
from .source_integrity import STATEMENTS
from .source_reextractions import _git_bytes, byte_hash, source_tex
from .validation_io import current_inputs, tracked_inputs

VERSION = 'chapter-preflight-v1'
HEADINGS = {'title_title', 'section_title', 'subsection_title', 'subsubsection_title'}
OUTPUT_NAMES = {'manifest.json', 'preflight.json', 'containers.jsonl', 'packages.json', 'report.md'}


def _git(directory, *args):
    result = subprocess.run(['git', '-C', str(directory), *args], capture_output=True, text=True)
    if result.returncode:
        raise RecordError('preflight Git identity unavailable: ' + result.stderr.strip())
    return result.stdout.strip()


class _Inputs:
    def __init__(self, root, harvest, inventory):
        if root.is_symlink() or harvest.is_symlink():
            raise RecordError('preflight root/harvest is a symlink')
        self.root, self.harvest = root.resolve(), harvest.resolve()
        self.native = None
        self.snapshot = InputSnapshot(self.root)
        # Preparation consumes current source/candidates, not model raw/freeze
        # history. Independent full QA remains responsible for that history.
        for name in ['config', 'schema', 'prompts', 'task-scopes', 'review',
                     'translation-data/units', 'translation-data/candidates',
                     'translation-data/reviewed', 'translation-data/selections',
                     'translation-data/chapter-templates']:
            self.snapshot.watch_tree(self.root / name)
        self.snapshot.watch_tree(self.root / 'stacks_zh', '*.py')
        self.snapshot.read(self.root / 'upstream.lock')
        for name in ['AGENTS.md', 'WORKFLOW.md']:
            if (self.root / name).is_file():
                self.snapshot.read(self.root / name)
        self.implementation = _ImplementationIdentity()
        current_inputs().seed_implementation(self.implementation)
        current_inputs().seed_snapshot(self.snapshot)
        lock = tomllib.loads(self.snapshot.read(self.root / 'upstream.lock').decode('utf-8'))
        expected = (lock.get('repository'), lock.get('commit'), lock.get('commit_date'))
        if not all(isinstance(value, str) and value for value in expected):
            raise RecordError('preflight requires the complete locked repository/commit/date')
        actual = (_git(self.harvest, 'remote', 'get-url', 'origin'), _git(self.harvest, 'rev-parse', 'HEAD'),
                  _git(self.harvest, 'show', '-s', '--format=%cs', 'HEAD'))
        if actual != expected or _git(self.harvest, 'status', '--porcelain', '--untracked-files=no'):
            raise RecordError('preflight harvest identity differs from upstream.lock or is dirty')
        self.commit = lock['commit']
        self.source = _SourceIdentity(self.root, self.harvest)
        self.inventory = inventory if inventory.is_absolute() else self.root / inventory
        self.inventory_exists = self.inventory.exists()
        if self.inventory_exists:
            self.snapshot.watch_tree(self.inventory)
        self.identity = dict(kind=VERSION, root=str(self.root), head=self.snapshot.head,
            python=sys.version, executable=sys.executable,
            harvest=str(self.harvest), source_head=actual[1], source_origin=actual[0],
            implementation=self.implementation.binding(),
            files={str(path): value for path, value in sorted(self.snapshot.hashes.items())},
            trees=[dict(path=str(path), pattern=pattern, files=sorted(str(p) for p in paths))
                   for (path, pattern), paths in sorted(self.snapshot.trees.items())],
            source_files={} if self.source.snapshot is None else
                {str(path): value for path, value in sorted(self.source.snapshot.hashes.items())},
            inventory=str(self.inventory), inventory_exists=self.inventory_exists)

    def assert_unchanged(self):
        self.implementation.assert_valid()
        self.snapshot.assert_unchanged()
        self.source.assert_valid(self.root, self.harvest)
        if self.native is not None:
            self.native.assert_unchanged()
        if self.inventory.exists() != self.inventory_exists:
            raise RecordError('preflight inventory presence changed')
        reads = current_inputs()
        known = {**self.snapshot.hashes, **{path: hashlib.sha256(raw).hexdigest()
                 for path, raw in self.implementation.inputs}}
        if self.source.snapshot is not None:
            known.update(self.source.snapshot.hashes)
        for path, digest in reads.hashes.items():
            if known.get(path) != digest:
                raise RecordError(f'preflight actual read is outside the bound dependency inventory: {path}')
        reads.assert_unchanged()


def _selectors(rows, chapter, tags):
    """Enumerate the existing native complete containers, not another TeX parser."""
    labels = defaultdict(list)
    for label, tag in tags.items():
        if label.startswith(chapter + '-'):
            labels[tag].append(label)
    result, blocks, previous = [], defaultdict(int), None
    for row in rows:
        kind = row['unit']['node_kind']
        owner, parent = row['owner_tag'], row['parent_tag']
        if kind in STATEMENTS | {'proof'} or kind.endswith('_title'):
            previous = None
            selector_kind, ordinal = kind, int(row['semantic_path'].rsplit('/', 1)[1])
        else:
            key = owner, parent
            if key == previous:
                result[-1]['inventory_ids'].append(row['inventory_id'])
                result[-1]['inventory_states'].append(row['state'])
                continue
            blocks[key] += 1
            previous = key
            selector_kind, ordinal = 'prose_block', blocks[key]
        label = labels[owner][0] if len(labels[owner]) == 1 else None
        selector = dict(file=chapter + '.tex', owner_tag=owner, owner_label=label,
                        parent_tag=parent, kind=selector_kind, ordinal=ordinal)
        result.append(dict(id=value_hash(selector), selector=selector,
            inventory_ids=[row['inventory_id']], inventory_states=[row['state']]))
    return result


def _prepared(entry, native, section_by_tag):
    selector = entry['selector']
    base = dict(entry, section_ordinal=section_by_tag.get(selector['owner_tag']),
                state='BLOCKED', reasons=[], covered_tags=[], units=[],
                capabilities=dict(macros_environments='UNVERIFIED_OR_BLOCKED', math_text='UNVERIFIED_OR_BLOCKED',
                    titles_footnotes_lists='UNVERIFIED_OR_BLOCKED', protected_roundtrip=False,
                    candidate_token_qa_still_required=True))
    try:
        if selector['owner_tag'] is None or selector['owner_label'] is None:
            raise RecordError('complete container has no unique locked Tag owner/label')
        selected = native.select(selector)
        if selector['kind']=='title_title':
            first=native.document(selector['file'][:-4])[1][0]
            if first['inventory_id'] not in entry['inventory_ids'] or selector['ordinal']!=1:
                raise RecordError('chapter-header first adoption requires the unique first natural-language node')
        units = [clean(unit) for unit in lower_container(selected, native.policy)]
        items = native_container_tag_coverage(selected, native.policy, native.english.tags)
        covered = {selector['owner_tag'], *items}
        if any(section_by_tag.get(tag) != section_by_tag.get(selector['owner_tag']) for tag in items):
            raise RecordError('native item Tag crosses its actual Section')
        sections={row['owner_tag'] for row in native.document(selector['file'][:-4])[1]
                  if row['unit']['node_kind']=='section_title'}
        first_adoption=selector['kind']=='title_title' or selector['parent_tag'] in sections
        base.update(state='READY', selected=clean(selected), units=units,
                    contract_support=dict(first_adoption_shape=first_adoption,
                        existing_source_replacement='complete-v4-current-batch-and-history-required',
                        automatic_adoption_permission=False),
                    covered_tags=sorted(covered), source_word_count=sum(_source_word_count(u['source_text']) for u in units),
                    source_contract='source-adoption-v4' if selector['kind'] == 'title_title' else
                                    'source-adoption-v1/v2/v3; existing-source replacement requires complete v4 restoration' if first_adoption else
                                    'complete-v4-existing-source-restoration; no first-adoption contract for a non-Section prose parent',
                    capabilities=dict(complete_container=True, protected_roundtrip=True,
                        macros_environments='SUPPORTED_CURRENT_POLICY',
                        math_text='SUPPORTED_TYPED_OR_LOCKED_CURRENT_POLICY',
                        titles_footnotes_lists='SUPPORTED_FOR_THIS_COMPLETE_CONTAINER',
                        candidate_token_qa_still_required=True,
                        protected_token_sequence=[PLACEHOLDER_TOKEN_RE.findall(u['source_text']) for u in units],
                        trailing_whitespace=[re.search(r'[ \t\r\n]*$', u['source_text'])[0] for u in units],
                        typed_math=any(u.get('math_text_regions') for u in units),
                        native_list_tags=sorted(items),
                        title_present=selector['kind'] in HEADINGS, footnote_present='\\footnote' in selected['fragment']))
    except (RecordError, KeyError, TypeError, ValueError) as exc:
        base['reasons'] = [str(exc)]
        base['source_word_count'] = 0
        base['source_contract'] = 'BLOCKED: resolve the named tool/policy/source contract before generation'
    return base


def _candidate_state(inputs, chapter, current):
    root = inputs.root
    files = {path: inputs.snapshot.jsonl(path) for path in sorted((root / 'translation-data/units').glob('*.jsonl'))}
    selected = {path: rows for path, rows in files.items() if any(row.get('chapter') == chapter for row in rows)}
    pairs = [(root / 'translation-data/units' / path.name, path)
             for path in sorted((root / 'translation-data/candidates').glob('*/*.jsonl'))
             if root / 'translation-data/units' / path.name in selected]
    candidate_ids, declared = set(), []
    for _, path in pairs:
        rows = inputs.snapshot.jsonl(path)
        candidate_ids.update(row['unit_id'] for row in rows if row.get('source_commit') == inputs.commit and row.get('source_status') == 'CURRENT')
        declared.append(dict(path=path.relative_to(root).as_posix(), lane=path.parent.name,
                             unit_ids=[row['unit_id'] for row in rows], runs=sorted({row.get('run_id', '') for row in rows})))
    errors, checked, positions = [], False, defaultdict(list)
    if pairs and inputs.inventory_exists:
        _, errors = current.validate_pairs([up for up, _ in pairs], [cp for _, cp in pairs], chapter=chapter)
        checked = not errors
        if checked:
            flat = [(up, unit) for up, _ in pairs for unit in selected[up]]
            if len(flat) != len(current._pair_locations or ()):
                raise RecordError('preflight current-source alignment lost ordered scope')
            for (up, unit), (_, start, end) in zip(flat, current._pair_locations, strict=True):
                row = dict(path=up.relative_to(root).as_posix(), unit_id=unit['unit_id'], start=start, end=end,
                           candidate=unit['unit_id'] in candidate_ids)
                if row not in positions[unit['unit_id']]:
                    positions[unit['unit_id']].append(row)
    elif pairs:
        errors = ['existing candidate current QA not run: source inventory is unavailable; source capability is checked independently']
    reviewed = []
    unit_ids = {unit['unit_id'] for rows in selected.values() for unit in rows}
    for path in sorted((root / 'translation-data/reviewed').rglob('*.json')):
        value = json.loads(inputs.snapshot.read(path))
        if (value.get('unit_id') in unit_ids and value.get('status') == 'current'
                and value.get('source_commit') == inputs.commit and value.get('source_status') == 'CURRENT'):
            reviewed.append(dict(path=path.relative_to(root).as_posix(), unit_id=value['unit_id'],
                                 stage=value.get('stage'), publication_status=value.get('publication_status')))
    return dict(unit_files=[path.relative_to(root).as_posix() for path in selected],
                unit_count=sum(len(rows) for rows in selected.values()), candidate_units=len(candidate_ids),
                candidate_files=declared, current_qa='PASS' if checked else 'NOT_RUN' if not pairs else 'BLOCKED',
                current_qa_errors=errors, full_model_history='NOT_RUN_BY_PREFLIGHT',
                declared_current_reviewed_records=reviewed, human_review_approval='NOT_GRANTED_BY_PREFLIGHT'), positions


def _existing_coverage(entry, positions, raw):
    if entry['state'] != 'READY':
        return dict(state='BLOCKED_SOURCE', current_unit_files=[], unit_ids=[], complete_candidate_scope=False)
    start, end = entry['selected']['location']['byte_start'], entry['selected']['location']['byte_end']
    matches = { (row['path'], row['unit_id'], row['start'], row['end']): row
               for rows in positions.values() for row in rows if row['start'] < end and row['end'] > start}
    cursor = start
    for row in sorted(matches.values(), key=lambda r: (r['start'], r['end'])):
        if row['start'] > cursor and raw[cursor:row['start']].strip(b' \t\r\n'):
            break
        if row['candidate']:
            cursor = max(cursor, row['end'])
    complete = cursor >= end or not raw[min(cursor,end):end].strip(b' \t\r\n')
    return dict(state='EXISTING_CURRENT_CANDIDATES' if complete else 'NEEDS_SCOPED_SOURCE_OR_CANDIDATE_WORK',
                current_unit_files=sorted({r['path'] for r in matches.values()}),
                unit_ids=sorted({r['unit_id'] for r in matches.values()}), complete_candidate_scope=complete)


def _packages(containers, chapter, minimum, maximum):
    """Keep native containers indivisible; files stay in one actual Section."""
    files, pending = [], []
    segment = 0
    target = max(1, minimum // MIN_BATCH_FILES)
    def flush():
        if not pending:
            return
        digest = value_hash([entry['id'] for entry in pending])[:16]
        owner = pending[0]['selector']['parent_tag']
        identifier = f'{chapter}-preflight-{owner}-{digest}'
        retained = all(entry['existing']['complete_candidate_scope'] for entry in pending)
        files.append(dict(id=identifier, segment=segment, section_ordinal=pending[0]['section_ordinal'],
            parent_tag=owner, source_contracts=sorted({entry['source_contract'] for entry in pending}),
            first_adoption_shape=all(entry['contract_support']['first_adoption_shape'] for entry in pending),
            container_ids=[entry['id'] for entry in pending],
            unit_ids=[u['unit_id'] for entry in pending for u in entry['units']],
            source_word_count=sum(entry['source_word_count'] for entry in pending),
            header=pending[0]['selector']['kind']=='title_title',
            action='RETAIN_EXISTING' if retained else 'REQUIRES_SCOPED_DATA_TASK',
            prospective_unit_file=f'translation-data/units/{identifier}.jsonl',
            existing_files=sorted({p for entry in pending for p in entry['existing']['current_unit_files']})))
        pending.clear()
    previous_section = None
    for entry in containers:
        if entry['state'] != 'READY':
            flush(); previous_section = None; segment += 1
            continue
        section = entry['section_ordinal']
        header = entry['selector']['kind'] == 'title_title'
        if pending and (header or section != previous_section
                        or entry['selector']['parent_tag'] != pending[0]['selector']['parent_tag']
                        or sum(e['source_word_count'] for e in pending) >= target):
            flush()
        pending.append(entry); previous_section = section
        if header or entry['source_word_count'] > maximum:
            flush()
    flush()
    packages, group = [], []
    def emit():
        if not group:
            return
        identifier = value_hash([f['id'] for f in group])[:16]
        words = sum(f['source_word_count'] for f in group)
        exceptions = []
        if len(group) < MIN_BATCH_FILES:
            exceptions.append('single complete header' if group[0]['header'] else
                'complete semantic remainder; no adjacent whole file fits this package without crossing a blocker or preferred maximum')
        if not minimum <= words <= maximum:
            exceptions.append('indivisible complete container or final adjacent semantic remainder outside preferred word range')
        packages.append(dict(id=identifier, chapter=chapter, file_ids=[f['id'] for f in group],
            source_contracts=sorted({contract for f in group for contract in f['source_contracts']}),
            first_adoption_shape=all(f['first_adoption_shape'] for f in group),
            file_count=len(group), source_word_count=words,
            section_ordinals=list(dict.fromkeys(f['section_ordinal'] for f in group)), exceptions=exceptions,
            prospective_file_ownership={f['prospective_unit_file']: identifier for f in group},
            action='RETAIN_EXISTING' if all(f['action']=='RETAIN_EXISTING' for f in group) else 'REQUIRES_SCOPED_DATA_TASK'))
        group.clear()
    for file in files:
        ordinal = file['section_ordinal']
        previous = group[-1]['section_ordinal'] if group else None
        nonadjacent = group and ordinal is not None and previous is not None and ordinal > previous + 1
        if group and (file['header'] or group[0]['header'] or nonadjacent or file['segment'] != group[-1]['segment']
                      or len(group) == MAX_BATCH_FILES
                      or sum(f['source_word_count'] for f in group) + file['source_word_count'] > maximum):
            emit()
        group.append(file)
        if file['header'] or file['source_word_count'] > maximum:
            emit()
    emit()
    return dict(files=files, packages=packages, preferred_files=[MIN_BATCH_FILES,MAX_BATCH_FILES],
                preferred_source_words=[minimum,maximum], ownership='prospective only; existing files remain read-only; complete old batches need an explicit data/restoration scope')


def _report(inputs, template, native, current, run, *, observe=None):
    chapter = template['chapter']
    if template.get('source_state') == 'SOURCE_UNAVAILABLE':
        return dict(version=VERSION, source_commit=inputs.commit, chapter=chapter,
                    chapter_ordinal=template['chapter_ordinal'], state='BLOCKED',
                    blockers=['SOURCE_UNAVAILABLE'], sections=[], tags=[], containers=[], packages=dict(files=[],packages=[]),
                    candidates=dict(current_qa='NOT_RUN', human_review_approval='NOT_GRANTED_BY_PREFLIGHT'),
                    source_ready=False, adopted=False)
    raw = _git_bytes(inputs.harvest, inputs.commit, chapter + '.tex')
    if template.get('source_sha256') != byte_hash(raw):
        raise RecordError('chapter template source hash differs from locked Git')
    slugs = {value['chapter'] for value in _load_chapters(inputs.root, inputs.commit,
        templates=[json.loads(inputs.snapshot.read(p)) for p in sorted((inputs.root/'translation-data/chapter-templates').glob('*.json'))])}
    tags = _load_tag_index(inputs.harvest/'tags/tags', slugs,
                           tags_text=_git_bytes(inputs.harvest, inputs.commit, 'tags/tags').decode('utf-8'))
    actual_sections=_source_sections(raw.decode('utf-8'),chapter,native.english.tags,{})
    fields=('ordinal','source_title','source_label','parent_tag')
    if ([{key:row.get(key) for key in fields} for row in template['sections']]
            != [{key:row.get(key) for key in fields} for row in actual_sections]):
        raise RecordError('chapter template Section metadata differs from locked Git')
    source = _chapter_source(inputs.harvest, template, tags, source_text=raw.decode('utf-8'))
    clock=time.perf_counter()
    _, rows, diagnostics = native.document(chapter)
    run.phase('native_chapter_scan',time.perf_counter()-clock)
    clock=time.perf_counter()
    candidates, positions = _candidate_state(inputs, chapter, current)
    run.phase('current_candidate_qa',time.perf_counter()-clock)
    selections = _selectors(rows, chapter, native.english.tags)
    expected_keys = {entry['id'] for entry in selections}
    if set(run.results) - expected_keys:
        raise RecordError('checkpoint includes a container outside this complete chapter')
    containers = []
    clock=time.perf_counter()
    for entry in selections:
        cached = run.results.get(entry['id']) if run.resume and not run.check else None
        if cached is not None:
            if (cached.get('selector') != entry['selector'] or cached.get('inventory_ids') != entry['inventory_ids']
                    or cached.get('inventory_states') != entry['inventory_states']):
                raise RecordError('checkpoint selector/inventory scope changed')
            if cached.get('state') == 'READY':
                selected = cached.get('selected', {})
                location = selected.get('location', {})
                fragment = raw[location.get('byte_start', 0):location.get('byte_end', 0)].decode('utf-8')
                if (fragment != selected.get('fragment') or byte_hash(fragment) != location.get('fragment_hash')
                        or ''.join(source_tex(u) for u in cached.get('units', [])) != fragment):
                    raise RecordError('checkpoint no longer roundtrips its bound source')
            prepared = cached
        else:
            prepared = _prepared(entry, native, source.section_by_tag)
            run.checkpoint(entry['id'], prepared)
        containers.append({**prepared, 'existing': _existing_coverage(prepared, positions, raw)})
        if observe is not None:
            observe(dict(container_id=entry['id'], reused=cached is not None, verified=len(containers)))
    run.phase('source_prepare_and_checkpoints',time.perf_counter()-clock)
    clock=time.perf_counter()
    covered = {tag for entry in containers if entry['state']=='READY' for tag in entry['covered_tags']}
    by_tag = {tag: [entry['id'] for entry in containers if tag in entry['covered_tags']] for tag in covered}
    all_tags = sorted((tag for tag in tags.chapter_by_tag if tags.chapter_by_tag[tag] == chapter),
                      key=lambda tag: (raw.find(('\\label{'+tags.label_by_tag[tag].removeprefix(chapter+'-')+'}').encode()), tag))
    required_tags = set().union(*(section[3] for section in source.sections))
    tag_rows = [dict(tag=tag, label=tags.label_by_tag[tag], section_ordinal=source.section_by_tag.get(tag),
        required=tag in required_tags, current_source=tag in source.section_by_tag, source_ready=tag in covered,
        complete_containers=by_tag.get(tag, [])) for tag in all_tags]
    missing = [row['tag'] for row in tag_rows if row['required'] and row['section_ordinal'] is not None and not row['source_ready']]
    blocked = [entry['id'] for entry in containers if entry['state'] != 'READY']
    values = {match['key']: int(match['value']) for match in LIMIT_RE.finditer(inputs.snapshot.read(inputs.root/'config/workflow.yml').decode('utf-8'))}
    minimum, maximum = values.get('preferred_min_source_words'), values.get('preferred_max_source_words')
    if minimum is None or maximum is None or minimum < 1 or maximum < minimum:
        raise RecordError('invalid existing preferred source-word policy')
    packages = _packages(containers, chapter, minimum, maximum)
    run.phase('package_plan',time.perf_counter()-clock)
    sections = [dict(ordinal=ordinal, title=title, parent_tag=parent, required_tags=sorted(required),
        prepared_tags=sorted(required & covered), missing_tags=sorted(required-covered),
        state='READY' if required <= covered and not any(entry['state']!='READY' and entry['section_ordinal']==ordinal for entry in containers) else 'BLOCKED')
        for ordinal, title, parent, required in source.sections]
    return dict(version=VERSION, source_commit=inputs.commit, chapter=chapter,
        chapter_ordinal=template['chapter_ordinal'], state='BLOCKED' if missing or blocked else 'READY',
        source_ready=not missing and not blocked, adopted=False, blockers=dict(containers=blocked,missing_tags=missing),
        sections=sections, tags=tag_rows, containers=containers, packages=packages, candidates=candidates,
        source_word_count_ready=sum(entry['source_word_count'] for entry in containers),
        blocked_source_word_count='unavailable for unlowered containers',
        source_diagnostics=diagnostics, boundaries='source readiness is a capability simulation; candidate completion and human approval are separate',
        usage=dict(status='unavailable', reason='no model calls'),
        evidence_reuse=dict(inventory=str(inputs.inventory), inventory_present=inputs.inventory_exists,
                            rule='exact source/policy/implementation/input hashes; independent full QA and history remain mandatory'))


def _payloads(report, fingerprint, identity):
    containers = report['containers']
    main = {key:value for key,value in report.items() if key not in {'containers','packages'}}
    main.update(fingerprint=fingerprint, container_count=len(containers),
                package_count=len(report['packages']['packages']))
    rendered = ['# Chapter source preflight', '', f"{report['chapter']}: {report['state']}",
                f"Locked source: {report['source_commit']}", '',
                'Preparation only. No facts adopted, no model run, no human/publication approval.', '',
                f"Sections: {len(report['sections'])}; containers: {len(containers)}; packages: {main['package_count']}",
                f"Current candidates: {report['candidates'].get('current_qa', 'NOT_RUN')}", '',
                '| Section | State | Missing source Tags |', '| --- | --- | --- |']
    for section in report['sections']:
        rendered.append(f"| {section['ordinal']} {section['title']} | {section['state']} | {', '.join(section['missing_tags'])} |")
    payloads={'preflight.json':canonical_bytes(main), 'containers.jsonl':b''.join(
        (json.dumps(entry,ensure_ascii=False,sort_keys=True)+'\n').encode() for entry in containers),
        'packages.json':canonical_bytes(report['packages']), 'report.md':('\n'.join(rendered)+'\n').encode()}
    manifest=dict(kind=VERSION, fingerprint=fingerprint, chapter=report['chapter'], source_commit=report['source_commit'],
        dependencies=identity, files={name:hashlib.sha256(raw).hexdigest() for name,raw in payloads.items()})
    payloads['manifest.json']=canonical_bytes(manifest)
    return main, payloads


def _install(inputs, output, payloads, *, check=False):
    output = generated_path(inputs.root, output)
    inputs.assert_unchanged()
    if output.exists():
        if (not output.is_dir() or {p.name for p in output.iterdir()} != OUTPUT_NAMES
                or any(p.is_symlink() or not p.is_file() for p in output.iterdir())):
            raise RecordError('refusing an unrelated preflight output directory')
        if any((output/name).read_bytes()!=raw for name,raw in payloads.items()):
            raise RecordError('preflight output is stale or changed; preserve its original evidence')
        inputs.assert_unchanged()
        return
    if check:
        raise RecordError('preflight check output is missing')
    generated_path(inputs.root,output)
    output.parent.mkdir(parents=True,exist_ok=True)
    generated_path(inputs.root,output)
    with tempfile.TemporaryDirectory(prefix='.preflight-',dir=output.parent) as directory:
        stage=Path(directory)/'package';stage.mkdir()
        for name,raw in payloads.items():
            (stage/name).write_bytes(raw)
        inputs.assert_unchanged()
        generated_path(inputs.root,output)
        os.replace(stage,output)
        try:
            inputs.assert_unchanged()
        except BaseException:
            generated_path(inputs.root,output)
            for name,raw in payloads.items():
                path=output/name
                if path.is_file() and not path.is_symlink() and path.read_bytes()==raw:
                    path.unlink()
            if not any(output.iterdir()):
                output.rmdir()
            raise


@tracked_inputs
def run_chapter_preflight(root: Path, harvest: Path, chapter: str, *,
        output: Path=Path('build/chapter-preflight'), state_dir: Path=Path('build/chapter-preflight-state'),
        inventory: Path=Path('source-ir/extraction'), resume=False, check=False, require_ready=False,
        _observe=None):
    """Return preparation/current-QA information, never an adoption or PASS credential."""
    invocation_start=time.perf_counter()
    inputs = _Inputs(root,harvest,inventory)
    templates = _load_chapters(inputs.root,inputs.commit,templates=[json.loads(inputs.snapshot.read(p))
        for p in sorted((inputs.root/'translation-data/chapter-templates').glob('*.json'))])
    locked_order=[slug for slug,_ in manifest_chapters(_git_bytes(inputs.harvest,inputs.commit,'chapters.tex').decode('utf-8'))]
    if [template['chapter'] for template in templates]!=locked_order:
        raise RecordError('chapter ordinal/slug order differs from the locked manifest')
    selected=[template for template in templates if template['chapter']==chapter or str(template['chapter_ordinal'])==str(chapter)]
    if len(selected)!=1:
        raise RecordError('chapter must uniquely identify a locked ordinal or slug')
    template=selected[0];slug=template['chapter']
    if template.get('source_file')!=slug+'.tex' or template.get('source_state') not in {'CURRENT','SOURCE_UNAVAILABLE'}:
        raise RecordError('chapter template has an invalid source file/state')
    if template['source_state']=='SOURCE_UNAVAILABLE' and (inputs.harvest/(slug+'.tex')).exists():
        raise RecordError('chapter template incorrectly declares an available source unavailable')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',slug):
        raise RecordError('unsafe chapter slug')
    fingerprint=value_hash(dict(inputs=inputs.identity,chapter=slug))
    destination=generated_path(inputs.root,output)/slug/fingerprint
    with PreparationRun(inputs.root,state_dir,fingerprint,resume=resume,check=check) as run:
        if run.active is not None:
            inputs.assert_unchanged()
            return dict(stage='RUNNING',fingerprint=fingerprint,process=run.active['process'],exit_code=0,
                        note='Existing live preparation; no second job started.')
        chapter_files={p.name for p in (inputs.root/'translation-data/units').glob('*.jsonl')
                       if any(unit.get('chapter')==slug for unit in inputs.snapshot.jsonl(p))}
        run.phase('inputs_and_fingerprint',time.perf_counter()-invocation_start)
        context_start=time.perf_counter()
        pairs_present=any(p.name in chapter_files for p in (inputs.root/'translation-data/candidates').glob('*/*.jsonl'))
        # Real current-source validation is independent of saved preparation
        # checkpoints. Missing inventory never triggers an implicit full rebuild.
        current=CurrentSourceQA(inputs.root,inputs.harvest,inventory=inputs.inventory) if pairs_present else None
        native=current.containers if current is not None else Containers(inputs.root,inputs.harvest)
        inputs.native=native
        run.phase('current_source_context',time.perf_counter()-context_start)
        report=_report(inputs,template,native,current,run,observe=_observe)
        summary,payloads=_payloads(report,fingerprint,inputs.identity)
        install_start=time.perf_counter()
        _install(inputs,destination,payloads,check=check)
        run.phase('write_or_check',time.perf_counter()-install_start)
        code=1 if require_ready and report['state']!='READY' else 0
        run.finish(summary,destination,exit_code=code)
        inputs.assert_unchanged()
        return dict(stage='CHECKED' if check else 'COMPLETE',fingerprint=fingerprint,
                    output=str(destination),report=summary,exit_code=code,
                    invocation_seconds=time.perf_counter()-invocation_start)
