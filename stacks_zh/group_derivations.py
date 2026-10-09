"""Grouped v4 replay, separate from the historical bijective v1-v3 contract."""
from __future__ import annotations

import copy
from typing import Any

from .records import RecordError, sha256_value, stamp_unit_hashes, validate_records, validate_tex_controls
from .source_containers import clean
from .source_integrity import permanent_tag_mapping
from .source_reextractions import source_tex

FIELDS = {'translation', 'allowed_english', 'term_occurrences', 'unknown_terms', 'notes'}


def revision_group(record: dict[str, Any], group: dict[str, Any],
                   units: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {'kind': 'candidate-group-to-revise', 'derivation_id': record['derivation_id'],
            'group_id': group['group_id'], 'identity_anchor': group['identity_anchor'],
            'source_units': [clean(u) for u in units], 'candidates': [clean(c) for c in candidates]}


def replay_groups(record, units, candidates, corrections, previous_outputs, restorations, tags):
    units, candidates = [clean(u) for u in units], [clean(c) for c in candidates]
    ids = [u['unit_id'] for u in units]
    if not ids or len(set(ids)) != len(ids) or [c['unit_id'] for c in candidates] != ids:
        raise RecordError('v4 requires unique equally ordered full-batch inputs')
    previous = record.get('previous_derivation_id')
    if previous:
        if (previous == record['derivation_id'] or previous_outputs is None
                or units != [clean(u) for u in previous_outputs[0]]
                or candidates != [clean(c) for c in previous_outputs[1]]
                or any(c.get('derivation_id') != previous for c in candidates)):
            raise RecordError('v4 requires the exact validated previous complete derived output')
    elif previous_outputs is not None or any(c.get('derivation_id') or c.get('model_correction_id') for c in candidates):
        raise RecordError('initial v4 must freeze raw model output with no predecessor')
    if any(u['source_commit'] != record['source_commit'] for u in units + candidates):
        raise RecordError('v4 full-batch inputs have a different source commit')
    groups = record['unit_groups']
    if (not groups or len({g['group_id'] for g in groups}) != len(groups)
            or [i for g in groups for i in g['input_unit_ids']] != ids):
        raise RecordError('v4 groups must cover every ordered old unit exactly once')
    output_ids = [i for g in groups for i in g['output_unit_ids']]
    if not output_ids or len(set(output_ids)) != len(output_ids):
        raise RecordError('v4 output groups need complete unique nonempty IDs')
    by_id = dict(zip(ids, zip(units, candidates, strict=True), strict=True))
    mapping = permanent_tag_mapping(units, tags)
    new_units, new_candidates = [], []
    last_location = {}
    used_restorations = set()
    for group in groups:
        inputs, outputs = group['input_unit_ids'], group['output_unit_ids']
        if (not inputs or not outputs or group['identity_anchor'] not in inputs
                or not group['reason'].strip() or '..' in group['group_id']):
            raise RecordError('v4 group needs nonempty old/new IDs, reason and an exact old identity anchor')
        old_units = [by_id[i][0] for i in inputs]
        old_candidates = [by_id[i][1] for i in inputs]
        output_units = [clean(u) for u in group['output_units']]
        if [u['unit_id'] for u in output_units] != outputs:
            raise RecordError('v4 output units must match the complete declared ordered output IDs')
        restoration_id = group['source_container_restoration_id']
        if restoration_id:
            evidence = (restorations or {}).get(restoration_id)
            if evidence is None or restoration_id in used_restorations:
                raise RecordError('v4 source container has no unique validated locked-Git evidence')
            used_restorations.add(restoration_id)
            source = evidence['record']
            if (any(u.get('schema_version') == 2 for u in output_units)
                    and source['tool']['version'] not in {'source-container-v3', 'source-container-v4'}):
                raise RecordError('typed math output requires source-container-v3 or witnessed v4 evidence')
            if (source['derivation_id'] != record['derivation_id'] or source['group_id'] != group['group_id']
                    or source['source_commit'] != record['source_commit']
                    or source['origin_commit'] != record['origin_commit']
                    or source['created_at'] != record['created_at']
                    or source['input_unit_ids'] != inputs or source['output_unit_ids'] != outputs
                    or source['new_units'] != output_units
                    or any(source['files'][role] != record['files'][role]
                           for role in ('input_units', 'input_candidates'))
                    or evidence['units'] != units or evidence['candidates'] != candidates):
                raise RecordError('v4 source evidence differs from the exact group and frozen whole batch')
            location = source['location']
            chapter = source['selector']['file']
            if location['byte_start'] < last_location.get(chapter, 0):
                raise RecordError('v4 selected containers overlap or change locked source order')
            last_location[chapter] = location['byte_end']
        else:
            if any(u.get('schema_version') == 2 for u in output_units) and not previous:
                raise RecordError('first unit-v2 output requires complete source-container-v3 evidence')
            # A source-preserving group is intentionally bijective. Segmentation
            # changes require complete semantic Git evidence, never concatenation
            # equality alone or a convenient existing inventory ID.
            if len(inputs) != 1 or len(outputs) != 1:
                raise RecordError('v4 segmentation changes require complete source-container evidence')
            expected = stamp_unit_hashes({**old_units[0], 'unit_id': mapping[inputs[0]]})
            if output_units != [expected] or source_tex(expected) != source_tex(old_units[0]):
                raise RecordError('v4 unchanged group differs from deterministic source-preserving coordinates')
        anchor = by_id[group['identity_anchor']][1]
        context = revision_group(record, group, old_units, old_candidates)
        for unit in output_units:
            key = group['model_correction_id'], unit['unit_id']
            correction = (corrections or {}).get(key)
            if correction is None:
                raise RecordError('v4 requires a complete actual model revision for every new unit')
            manifest, raw = correction['record'], correction['candidate']
            if (manifest['derivation_ids'].get(unit['unit_id']) != record['derivation_id']
                    or manifest['source_commit'] != record['source_commit']
                    or correction['unit'] != unit or raw['context'].get('revision_input') != context):
                raise RecordError('v4 revision output did not freeze the exact new source and every old group candidate')
            candidate = copy.deepcopy(anchor)
            candidate.pop('derivation_id', None)
            candidate.pop('model_correction_id', None)
            candidate.pop('unit_group_id', None)
            candidate.update({field: copy.deepcopy(raw[field]) for field in FIELDS})
            candidate.update(unit_id=unit['unit_id'], source_text_hash=unit['source_text_hash'],
                context=copy.deepcopy(raw['context']), context_hash=sha256_value(raw['context']),
                translation_hash=sha256_value(raw['translation']), derivation_id=record['derivation_id'],
                model_correction_id=group['model_correction_id'], unit_group_id=group['group_id'],
                term_status=raw['term_status'], stage=raw['stage'], qa_status='PASS',
                source_status='CURRENT', publication_status='CANDIDATE')
            if candidate['stage'] not in {'STRUCTURE_OK', 'TERM_OK'} or raw['qa_status'] != 'PASS':
                raise RecordError('v4 cannot inherit or confer critic, human or publication approval')
            problems = validate_tex_controls(unit, candidate)
            if problems:
                raise RecordError('\n'.join(problems))
            new_units.append(unit)
            new_candidates.append(candidate)
    problems = validate_records(new_units, new_candidates, record['source_commit'])
    if problems:
        raise RecordError('v4 derived QA failed:\n' + '\n'.join(problems))
    if permanent_tag_mapping(new_units, tags) != {u['unit_id']: u['unit_id'] for u in new_units}:
        raise RecordError('v4 new output coordinates disagree with native source ownership')
    return new_units, new_candidates


def correction_bindings(record):
    if record['tool']['version'] == '4':
        return [(g['model_correction_id'], i) for g in record['unit_groups'] for i in g['output_unit_ids']]
    return [(op['model_correction_id'], record['unit_id_map'][op['unit_id']])
            for op in record['operations'] if op.get('model_correction_id')]


def restoration_bindings(record):
    return [g['source_container_restoration_id'] for g in record.get('unit_groups', [])
            if g['source_container_restoration_id']]
