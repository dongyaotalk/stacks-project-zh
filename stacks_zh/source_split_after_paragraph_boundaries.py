"""Complete split prose after an independently anchored whole paragraph."""
from __future__ import annotations

import re

from .extraction import Scanner
from .records import RecordError, sha256_value
from .source_container_boundaries import (
    SPACE, _complete_statement_signature, _item_tags, native_statement,
    nested_preceding_statement_paragraph_witness, paragraph_signature,
    preceding_statement_paragraph_witness)
from .source_integrity import STATEMENTS
from .source_reextractions import source_tex

VERSION = 'source-container-v11'


def split_after_paragraph_witness(containers, units, groups, ids, selected):
    """Recompute three whole adjacent containers from the full frozen batch."""
    selector = selected['selector']
    if (selector['kind'] != 'paragraph' or selector['owner_tag'] != selector['parent_tag']
            or selected['inventory_unit']['schema_version'] != 1
            or len(ids) < 2 or len(set(ids)) != len(ids)):
        raise RecordError('split after paragraph needs distinct complete unit-v1 parts and a Section-owned target')
    by_id = {unit['unit_id']: unit for unit in units}
    order = [unit['unit_id'] for unit in units]
    if (len(by_id) != len(units) or any(identifier not in by_id for identifier in ids)
            or any(unit['chapter'] + '.tex' != selector['file']
                   or unit['source_commit'] != selected['source_commit'] for unit in units)):
        raise RecordError('split after paragraph requires one unique complete batch in the locked chapter/source')
    start = order.index(ids[0])
    positions = [i for i, group in enumerate(groups)
                 if group['input_unit_ids'] == [ids[0]] and group['kind'] == 'paragraph'
                 and group['ordinal'] is None]
    if order[start:start + len(ids)] != ids or len(positions) != 1 or positions[0] < 2:
        raise RecordError('split after paragraph lacks its complete ordered interval and two old anchors')
    index = positions[0]
    previous, statement = groups[index - 1], groups[index - 2]
    if (previous['kind'] != 'paragraph' or previous['ordinal'] is not None
            or len(previous['input_unit_ids']) != 1 or statement['kind'] not in STATEMENTS):
        raise RecordError('split after paragraph requires a whole preceding paragraph and its whole statement')
    chain = []
    for group in groups[index:]:
        if group['kind'] != 'paragraph' or group['ordinal'] is not None:
            break
        if len(group['input_unit_ids']) != 1 or group['file'] != selector['file']:
            raise RecordError('split after paragraph includes a foreign or non-singleton container')
        chain.extend(group['input_unit_ids'])
    if chain != ids:
        raise RecordError('split after paragraph must consume its maximal complete old paragraph chain')
    old_previous = by_id[previous['input_unit_ids'][0]]
    parts = [by_id[identifier] for identifier in ids]
    members = [by_id[identifier] for identifier in statement['input_unit_ids']]
    parent = parts[0]['parent_tag']
    preceding_ids = statement['input_unit_ids'] + previous['input_unit_ids']
    if (start < len(preceding_ids) or order[start - len(preceding_ids):start] != preceding_ids
            or statement['owner_tag'] != parent
            or any(unit['schema_version'] != 1 or unit['parent_tag'] != parent
                   for unit in [*members, old_previous, *parts])):
        raise RecordError('split after paragraph crosses its complete same-parent unit-v1 anchors')
    for unit in [old_previous, *parts]:
        if (unit['node_kind'] != 'paragraph'
                or re.fullmatch(r'tag:' + re.escape(parent) + r':p[0-9]{3}', unit['unit_id']) is None
                or unit['render']['suffix'].strip(SPACE)):
            raise RecordError('split after paragraph requires canonical whole old paragraphs with whitespace suffixes')
    if (re.fullmatch(r'[ \t\r\n]*\\noindent[ \t\r\n]*', old_previous['render']['prefix']) is None
            or re.fullmatch(r'[ \t\r\n]*\\medskip[ \t\r\n]*\\noindent[ \t\r\n]*',
                            parts[0]['render']['prefix']) is None
            or any(unit['render']['prefix'].strip(SPACE) for unit in parts[1:])):
        raise RecordError('split after paragraph requires original noindent and medskip/noindent boundaries')
    raw, rows, _ = containers.documents[selector['file'][:-4]]
    native_positions = [i for i, row in enumerate(rows) if row['location'] == selected['location']]
    if len(native_positions) != 1 or native_positions[0] < 2:
        raise RecordError('split after paragraph lacks two complete preceding native containers')
    row = rows[native_positions[0] - 1]
    if (row['unit']['node_kind'] != 'paragraph' or row['owner_tag'] != selector['owner_tag']
            or row['parent_tag'] != selector['parent_tag']):
        raise RecordError('split after paragraph has a different real preceding paragraph or Section')
    native_previous = containers.select({**selector, 'ordinal': int(row['semantic_path'].rsplit('/', 1)[1])})
    if (native_previous['location'] != row['location']
            or raw[row['location']['byte_end']:selected['location']['byte_start']].strip(b' \t\r\n')):
        raise RecordError('split after paragraph is not immediately after the same complete native paragraph')
    # Preserve the old v5/v6 permissions. Their independent whole-paragraph
    # witness establishes the first adjacency and chapter-wide uniqueness.
    try:
        anchor = preceding_statement_paragraph_witness(containers, units, groups, previous, native_previous)
    except RecordError:
        anchor = nested_preceding_statement_paragraph_witness(containers, units, groups, previous, native_previous)
    native = native_statement(containers, statement)
    original = ''.join(source_tex(unit) for unit in members)
    for fragment in [original, native['fragment']]:
        scanner = Scanner(fragment, containers.policy)
        _, _, errors = scanner.protect(0, len(fragment))
        if errors or scanner.math_text_regions:
            raise RecordError('split after paragraph statement contains unsupported or typed math text')
    if (_item_tags(original, containers.policy, containers.english.tags, parts[0]['chapter'])
            != _item_tags(native['fragment'], containers.policy, containers.english.tags, parts[0]['chapter'])):
        raise RecordError('split after paragraph changes permanent statement item order')
    statement_signature = _complete_statement_signature(original, containers.policy, containers.english.tags, parts[0]['chapter'])
    if statement_signature != _complete_statement_signature(native['fragment'], containers.policy, containers.english.tags, parts[0]['chapter']):
        raise RecordError('split after paragraph changes its complete preceding statement or protected bytes')
    # Direct original byte concatenation: no separator, trimming, synthetic
    # merged unit, or guessed boundary may complete a partial old group.
    signature = paragraph_signature(''.join(source_tex(unit) for unit in parts), containers.policy)
    if signature != paragraph_signature(selected['fragment'], containers.policy):
        raise RecordError('split after paragraph changes complete target prose or protected bytes')
    count = 0
    for row in rows:
        if row['unit']['node_kind'] != 'paragraph':
            continue
        location = row['location']
        try:
            count += paragraph_signature(raw[location['byte_start']:location['byte_end']].decode(), containers.policy) == signature
        except RecordError:
            continue
    if count != 1:
        raise RecordError('split after paragraph target correspondence is ambiguous in the locked chapter')
    return {'paragraph_input_unit_ids': ids, 'historical_parent_tag': parent,
        'preceding_paragraph_input_unit_id': old_previous['unit_id'],
        'preceding_paragraph_selector': native_previous['selector'],
        'preceding_paragraph_fragment_hash': native_previous['location']['fragment_hash'],
        'preceding_paragraph_anchor': anchor,
        'preceding_statement_signature_hash': sha256_value(statement_signature),
        'paragraph_signature_hash': sha256_value(signature)}
