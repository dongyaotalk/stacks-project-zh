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
from .source_containers import clean, load_source_containers, safe_path
from .source_integrity import STATEMENTS
from .source_reextractions import byte_hash, source_tex


def container_tag_coverage(
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
