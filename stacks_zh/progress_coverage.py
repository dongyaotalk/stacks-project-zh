"""Source coverage for current complete containers; never an approval check."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .model_corrections import _first_addition_is_immutable
from .extraction import ENVIRONMENT, Scanner
from .records import RecordError, load_upstream_commit
from .schema_validation import validate_named_schema
from .source_container_boundaries import _item_tags
from .source_containers import Containers, clean, load_source_containers, lower_container, safe_path
from .source_integrity import STATEMENTS
from .source_reextractions import byte_hash, source_tex


def _restored_container_tag_coverage(
    root: Path, harvest: Path, units_by_file: dict[str, list[dict[str, Any]]],
) -> dict[str, frozenset[str]]:
    """Confirm additional native item Tags against live v4 source bindings.

    Current units must equal the complete recorded output, not an arbitrary
    unit with matching labels. Source restoration replays locked Git and the
    frozen old ownership chain with its historical policy. Full model replay,
    candidate QA and review/publication gates remain separate requirements.
    """
    commit = load_upstream_commit(root / 'upstream.lock')
    owners, queries = {}, {}
    for path in sorted((root / 'translation-data/derivations').glob('*.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        if record.get('tool', {}).get('version') != '4':
            continue
        identifier = record.get('derivation_id')
        safe_path(root, path.relative_to(root).as_posix(),
                  r'translation-data/derivations/[A-Za-z0-9._-]+\.json')
        if identifier != path.stem or '..' in path.stem:
            raise RecordError('progress container derivation has an invalid identity')
        # An archived output is not a current preparation, even if its labels
        # or unit IDs happen to be present somewhere in today's data.
        if (root / 'translation-data/derivation-archives' / (identifier + '.json')).exists():
            continue
        relative = record.get('files', {}).get('output_units', {}).get('path')
        if relative not in units_by_file:
            continue
        problems = validate_named_schema(record, 'derivation.schema.json', str(path))
        if problems:
            raise RecordError('\n'.join(problems))
        if relative in owners:
            raise RecordError('progress container has multiple current derivation owners')
        owners[relative] = identifier
        groups = record['unit_groups']
        relevant = []
        for group in groups:
            restoration = group.get('source_container_restoration_id')
            if not restoration or not any(u['node_kind'] in STATEMENTS for u in group['output_units']):
                continue
            source_path = safe_path(root, f'translation-data/source-container-restorations/{restoration}.json',
                r'translation-data/source-container-restorations/[A-Za-z0-9._-]+\.json')
            try:
                source = json.loads(source_path.read_text(encoding='utf-8'))
                fragment = source['fragment']
                if not isinstance(fragment, str):
                    raise ValueError('fragment must be source text')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                raise RecordError(f'progress source coverage metadata: {source_path}: {exc}') from exc
            # Metadata selects a query, never grants coverage. Use the frozen
            # source rather than current prose so missing current content must
            # still pass the complete native binding checks below.
            current = ''.join(source_tex(u) for u in group['output_units'])
            if any(len(re.findall(r'\\label\{[^{}]+\}', text)) >= 2 for text in (fragment, current)):
                relevant.append((restoration, group))
        if not relevant:
            continue
        _first_addition_is_immutable(root, path)
        current_path = safe_path(root, relative, r'translation-data/units/[A-Za-z0-9._-]+\.jsonl')
        units = [clean(u) for u in units_by_file[relative]]
        outputs = [u for group in groups for u in group['output_units']]
        ids = [u['unit_id'] for u in units]
        if (record['source_commit'] != commit
                or byte_hash(current_path.read_bytes()) != record['files']['output_units']['hash']
                or outputs != units or len(set(ids)) != len(ids)
                or [i for g in groups for i in g['output_unit_ids']] != ids
                or len({g['group_id'] for g in groups}) != len(groups)
                or any(u['source_commit'] != commit or u['source_status'] != 'CURRENT' for u in units)):
            raise RecordError('progress container requires the exact complete current v4 output')
        for restoration, group in relevant:
            if restoration in queries:
                raise RecordError('progress source container is bound more than once')
            queries[restoration] = record, group
    if not queries:
        return {}
    evidence, errors = load_source_containers(root, harvest, identifiers=set(queries))
    if errors:
        raise RecordError('progress source coverage failed:\n' + '\n'.join(errors))
    coverage = {}
    for identifier, (derivation, group) in queries.items():
        restored = evidence[identifier]
        record = restored['record']
        if (any(record[k] != derivation[k] for k in (
                'derivation_id', 'source_commit', 'origin_commit', 'created_at'))
                or record['group_id'] != group['group_id']
                or record['input_unit_ids'] != group['input_unit_ids']
                or record['output_unit_ids'] != group['output_unit_ids']
                or record['new_units'] != group['output_units']
                or record['files'] != {k: derivation['files'][k] for k in ('input_units', 'input_candidates')}
                or [i for g in derivation['unit_groups'] for i in g['input_unit_ids']]
                   != [u['unit_id'] for u in restored['units']]
                or group['identity_anchor'] not in group['input_unit_ids']):
            raise RecordError('progress source container differs from its complete current v4 group')
        selected = restored['selected']
        if selected['selector']['kind'] not in STATEMENTS:
            raise RecordError('progress nested Tags require a complete statement container')
        fragment = selected['fragment']
        scanner = Scanner(fragment, restored['policy'])
        opening = ENVIRONMENT.match(fragment)
        position = scanner.skip_space(opening.end())
        if fragment[position:position + 1] == '[':
            # A named environment title is a parameter, not a native list.
            # It remains fully verified in the source/lowering above.
            fragment = fragment[:opening.end()] + fragment[scanner.argument_end(position):]
        tags = _item_tags(fragment, restored['policy'], restored['tags'],
                          selected['selector']['file'][:-4])
        if len(set(tags)) != len(tags):
            raise RecordError('progress source container has duplicate native item Tags')
        coverage[group['output_unit_ids'][0]] = frozenset(tags)
    return coverage


def _first_adoption_tag_coverage(root, harvest, units_by_file):
    """Verify source preparation only; candidate/history QA remains independent."""
    from .derivations import _git_origin_bytes
    from .source_adoptions import POLICIES, Reads, _schema, _task_scope

    directory = root / 'translation-data/source-adoptions'
    if not directory.exists():
        return {}
    reads = Reads(root)
    reads.snapshot.watch_tree(directory)
    records, consumed = {}, set()
    successors = {}
    current_ids = {u['unit_id'] for units in units_by_file.values() for u in units}
    for path in sorted(directory.glob('*.json')):
        safe_path(root, path.relative_to(root).as_posix(),
                  r'translation-data/source-adoptions/[A-Za-z0-9._-]+\.json')
        record = json.loads(reads.snapshot.read(path))
        if not isinstance(record, dict):
            raise RecordError('progress first-adoption metadata must be an object')
        if (not current_ids.intersection(record.get('unit_ids', []))
                and not any(output.get('units', {}).get('path') in units_by_file
                            for output in record.get('outputs', []))):
            continue
        frozen = reads.json(record['input'])
        _schema(record, 'source-adoption.schema.json')
        _schema(frozen, 'source-adoption-input.schema.json')
        _first_addition_is_immutable(root, path)
        records[path.relative_to(root).as_posix()] = path, record, frozen
        for prior in frozen.get('prior_adoptions', []):
            ancestor = prior['record']['path']
            reads.read(prior['record'], r'translation-data/source-adoptions/[A-Za-z0-9._-]+\.json')
            if ancestor in successors:
                raise RecordError('progress first adoption has multiple current successors')
            successors[ancestor] = path.relative_to(root).as_posix()
            consumed.add(ancestor)
    for relative in records:
        seen = set()
        while relative in successors:
            if relative in seen:
                raise RecordError('progress first adoption has cyclic consumption')
            seen.add(relative)
            relative = successors[relative]

    commit = load_upstream_commit(root / 'upstream.lock')
    coverage, owned = {}, set()
    for relative, (path, record, frozen) in records.items():
        if relative in consumed:
            continue
        relevant = [g for batch in frozen['batches'] for g in batch['containers']
                    if g['selector']['kind'] in STATEMENTS
                    and len(re.findall(r'\\label\{[^{}]+\}', g['selected']['fragment'])) >= 2]
        if not relevant:
            continue
        if (path.stem != record['adoption_id']
                or record['input']['path'] != f"translation-data/source-adoption-inputs/{path.stem}.json"
                or any(record[k] != frozen[k] for k in
                       ('adoption_id', 'origin_commit', 'source_commit', 'created_at', 'unit_ids', 'run_id', 'chapter', 'parent_tags'))
                or record['source_commit'] != commit
                or record['tool_version'] != frozen['tool_version'].replace('-input', '')):
            raise RecordError('progress first adoption has a different source identity')
        _task_scope(frozen, reads, record['input'], current=False)
        policies = frozen['policies']
        if len(policies) != len(POLICIES) or {p['path'] for p in policies} != set(POLICIES):
            raise RecordError('progress first adoption lacks its complete origin policy set')
        historical = {}
        for entry in policies:
            raw = _git_origin_bytes(root, frozen['origin_commit'], entry['path'])
            if byte_hash(raw) != entry['hash']:
                raise RecordError('progress first adoption origin policy hash differs')
            historical[entry['path']] = raw
        if commit not in historical['upstream.lock'].decode('utf-8'):
            raise RecordError('progress first adoption origin has a different English lock')
        native = Containers(root, harvest, policy_bytes=historical['config/macro-policy.yml'])
        if native.english.commit != commit or len(record['outputs']) != len(frozen['batches']):
            raise RecordError('progress first adoption has incomplete current source outputs')
        ids, locations = [], []
        for batch, output in zip(frozen['batches'], record['outputs'], strict=True):
            up = batch['units_path']
            if (up not in units_by_file or output['units']['path'] != up
                    or output['candidates']['path'] != batch['candidates_path']):
                raise RecordError('progress first adoption output paths differ')
            raw = reads.read(output['units'], r'translation-data/units/[A-Za-z0-9._-]+\.jsonl')
            actual = [clean(u) for u in units_by_file[up]]
            if ([json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()] != actual
                    or actual != batch['units']
                    or any(u['source_commit'] != commit or u['source_status'] != 'CURRENT'
                           or u['chapter'] != frozen['chapter'] for u in actual)):
                raise RecordError('progress first adoption requires its complete current unit file')
            expected = []
            for group in batch['containers']:
                selected = native.select(group['selector'])
                lowered = [clean(u) for u in lower_container(selected, native.policy)]
                if selected != group['selected'] or [u['unit_id'] for u in lowered] != group['unit_ids']:
                    raise RecordError('progress first adoption differs from its complete Git container')
                location = selected['location']
                interval = (group['selector']['file'], location['byte_start'], location['byte_end'])
                if (interval[0] != frozen['chapter'] + '.tex'
                        or any(interval[0] == old[0] and interval[1] < old[2] for old in locations)):
                    raise RecordError('progress first adoption source containers overlap or are out of order')
                locations.append(interval)
                expected.extend(lowered)
                if group not in relevant:
                    continue
                fragment = selected['fragment']
                scanner = Scanner(fragment, native.policy)
                opening = ENVIRONMENT.match(fragment)
                position = scanner.skip_space(opening.end())
                if fragment[position:position + 1] == '[':
                    fragment = fragment[:opening.end()] + fragment[scanner.argument_end(position):]
                tags = _item_tags(fragment, native.policy, native.english.tags,
                                  group['selector']['file'][:-4])
                if len(set(tags)) != len(tags) or owned.intersection(tags):
                    raise RecordError('progress first adoption has duplicate native item Tags')
                owned.update(tags)
                coverage[group['unit_ids'][0]] = frozenset(tags)
            if expected != actual:
                raise RecordError('progress first adoption requires complete canonical lowering')
            ids.extend(u['unit_id'] for u in actual)
        if ids != frozen['unit_ids'] or len(ids) != len(set(ids)):
            raise RecordError('progress first adoption complete unit order differs')
        native.assert_unchanged()
    reads.snapshot.assert_unchanged()
    return coverage


def container_tag_coverage(root, harvest, units_by_file):
    """Count native item Tags only from verified complete current source groups."""
    restored = _restored_container_tag_coverage(root, harvest, units_by_file)
    try:
        adopted = _first_adoption_tag_coverage(root, harvest, units_by_file)
    except RecordError:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        raise RecordError('progress first-adoption source metadata: ' + str(exc)) from exc
    if restored.keys() & adopted.keys():
        raise RecordError('progress complete container has multiple current source owners')
    return restored | adopted
