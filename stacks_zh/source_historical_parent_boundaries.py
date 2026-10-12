"""Full frozen groups and two native anchors, never an arbitrary parent waiver."""
from __future__ import annotations

import re

from .extraction import Scanner
from .records import RecordError, sha256_value
from .source_container_boundaries import (
    SPACE, _complete_statement_signature, _item_tags, native_statement, paragraph_signature)
from .source_integrity import STATEMENTS
from .source_reextractions import source_tex

VERSION = 'source-container-v10'


def historical_parent_paragraph_witness(containers, units, groups, group, selected):
    """Bind old preceding-owner prose to its complete same-batch successor."""
    ids, selector = group['input_unit_ids'], selected['selector']
    if (len(ids) != 1 or group['kind'] != 'paragraph' or group['ordinal'] is not None
            or selector['kind'] != 'paragraph' or selector['owner_tag'] != selector['parent_tag']):
        raise RecordError('historical parent witness needs one complete Section-owned paragraph')
    by_id = {unit['unit_id']: unit for unit in units}
    old = by_id[ids[0]]
    if (old['schema_version'] != 1 or selected['inventory_unit']['schema_version'] != 1
            or old['node_kind'] != 'paragraph'
            or re.fullmatch(r'tag:' + re.escape(old['parent_tag']) + r':p[0-9]{3}', old['unit_id']) is None
            or re.fullmatch(r'[ \t\r\n]*\\noindent[ \t\r\n]*', old['render']['prefix']) is None
            or old['render']['suffix'].strip(SPACE)):
        raise RecordError('historical parent witness requires the original canonical unit-v1 noindent paragraph')
    index = groups.index(group)
    if index + 1 >= len(groups) or groups[index + 1]['kind'] not in STATEMENTS:
        raise RecordError('historical parent paragraph lacks a complete same-batch following statement')
    following = groups[index + 1]
    members = [by_id[identifier] for identifier in following['input_unit_ids']]
    order = [unit['unit_id'] for unit in units]
    start = order.index(old['unit_id'])
    parent = following['owner_tag']
    if (order[start + 1:start + 1 + len(members)] != following['input_unit_ids']
            or old['parent_tag'] in {parent, selector['parent_tag']}
            or any(unit['schema_version'] != 1 or unit['parent_tag'] != parent for unit in members)
            or group['file'] != selector['file'] or following['file'] != selector['file']):
        raise RecordError('historical parents must identify two distinct real statement owners in the full frozen order')
    kind = re.escape(following['kind'])
    if (re.fullmatch(r'[ \t\r\n]*\\begin\{' + kind + r'\}[ \t\r\n]*\\label\{[^{}\n]+\}[ \t\r\n]*', members[0]['render']['prefix']) is None
            or re.fullmatch(r'[ \t\r\n]*\\end\{' + kind + r'\}[ \t\r\n]*', members[-1]['render']['suffix']) is None):
        raise RecordError('historical parent witness needs complete plain following statement wrappers')
    native = native_statement(containers, following)
    raw, rows, _ = containers.documents[selector['file'][:-4]]
    positions = [i for i, row in enumerate(rows) if row['location'] == selected['location']]
    if len(positions) != 1 or positions[0] == 0 or positions[0] + 1 >= len(rows):
        raise RecordError('historical parent paragraph lacks two complete native anchors')
    before, after = rows[positions[0] - 1], rows[positions[0] + 1]
    if (before['unit']['node_kind'] not in STATEMENTS
            or before['owner_tag'] != old['parent_tag']
            or before['parent_tag'] != selector['parent_tag']
            or after['location'] != native['location']
            or native['selector']['parent_tag'] != selector['parent_tag']
            or raw[before['location']['byte_end']:selected['location']['byte_start']].strip(b' \t\r\n')
            or raw[selected['location']['byte_end']:native['location']['byte_start']].strip(b' \t\r\n')):
        raise RecordError('historical parents differ from the immediately preceding/following native statement owners or real Section')
    labels = [label for label, tag in containers.english.tags.items()
              if tag == before['owner_tag'] and label.startswith(old['chapter'] + '-')]
    if len(labels) != 1:
        raise RecordError('historical preceding owner label is not unique')
    preceding = containers.select({'file': selector['file'], 'owner_tag': before['owner_tag'],
        'owner_label': labels[0], 'parent_tag': selector['parent_tag'],
        'kind': before['unit']['node_kind'], 'ordinal': int(before['semantic_path'].rsplit('/', 1)[1])})
    original = ''.join(source_tex(unit) for unit in members)
    old_items = _item_tags(original, containers.policy, containers.english.tags, old['chapter'])
    if old_items != _item_tags(native['fragment'], containers.policy, containers.english.tags, old['chapter']):
        raise RecordError('historical parent following statement changes permanent list item order')
    for fragment in [original, native['fragment']]:
        scanner = Scanner(fragment, containers.policy)
        _, _, errors = scanner.protect(0, len(fragment))
        if errors or scanner.math_text_regions:
            raise RecordError('historical parent following statement has unsupported or typed math text')
    following_signature = _complete_statement_signature(original, containers.policy, containers.english.tags, old['chapter'])
    if following_signature != _complete_statement_signature(native['fragment'], containers.policy, containers.english.tags, old['chapter']):
        raise RecordError('historical parent following statement changes its complete prose or protected bytes')
    signature = paragraph_signature(source_tex(old), containers.policy)
    if signature != paragraph_signature(selected['fragment'], containers.policy):
        raise RecordError('historical parent paragraph changes complete prose or protected bytes')
    count = 0
    for row in rows:
        if row['unit']['node_kind'] != 'paragraph':
            continue
        loc = row['location']
        try:
            count += paragraph_signature(raw[loc['byte_start']:loc['byte_end']].decode(), containers.policy) == signature
        except RecordError:
            continue
    if count != 1:
        raise RecordError('historical parent paragraph correspondence is ambiguous in the locked chapter')
    return {'paragraph_input_unit_id': old['unit_id'], 'historical_parent_tag': old['parent_tag'],
        'following_statement_input_unit_ids': following['input_unit_ids'],
        'following_statement_historical_parent_tag': parent,
        'preceding_native_statement_selector': preceding['selector'],
        'preceding_native_statement_fragment_hash': preceding['location']['fragment_hash'],
        'following_statement_selector': native['selector'],
        'following_statement_fragment_hash': native['location']['fragment_hash'],
        'following_statement_signature_hash': sha256_value(following_signature),
        'paragraph_signature_hash': sha256_value(signature)}
