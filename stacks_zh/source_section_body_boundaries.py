"""Complete Section bodies at frozen batch ends, with two locked Git anchors."""
from __future__ import annotations

import re

from .extraction import Scanner
from .records import RecordError, sha256_value
from .source_integrity import _own_tag
from .source_reextractions import source_tex
from .source_container_boundaries import _complete_statement_signature

VERSION = 'source-container-v12'
SPACE = ' \t\r\n'
TOKEN = re.compile(r'<([A-Z][A-Z0-9]*_[0-9]{4})>')


def complete_prose_signature(fragment, policy):
    """Normalize only ordinary ASCII prose whitespace, retaining every node."""
    scanner = Scanner(fragment, policy)
    text, tokens, errors = scanner.protect(0, len(fragment))
    if errors or scanner.math_text_regions:
        raise RecordError('Section body has unsupported syntax or typed math text')
    result, cursor = [], 0

    def prose(value):
        normalized = re.sub(r'[ \t\r\n]+', ' ', value).strip(' ')
        if normalized:
            result.append(['text', normalized])

    for match in TOKEN.finditer(text):
        prose(text[cursor:match.start()])
        if match[1] not in tokens:
            raise RecordError('Section body has a forged protected token')
        result.append(['protected', tokens[match[1]]])
        cursor = match.end()
    prose(text[cursor:])
    return result


def section_body_end_witness(containers, units, groups, group, selected):
    selector = selected['selector']
    parent = selector['parent_tag']
    ids = group['input_unit_ids']
    order = [u['unit_id'] for u in units]
    if (selector['kind'] != 'prose_block' or selector['owner_tag'] != parent
            or selector['ordinal'] != 1 or group['kind'] != 'prose_block'
            or len(units) < 2 or len(set(order)) != len(order)
            or ids != order[1:] or group['ordinal'] != 1
            or any(u['schema_version'] != 1 or u['parent_tag'] != parent
                   or u['chapter'] + '.tex' != selector['file']
                   or u['source_commit'] != selected['source_commit'] for u in units)
            or selected['inventory_unit']['schema_version'] != 1):
        raise RecordError('Section body end requires the complete ordered same-Section unit-v1 batch')
    heading = units[0]
    if (heading['node_kind'] != 'section_title' or heading['unit_id'] != f'tag:{parent}:title'
            or _own_tag(heading, containers.english.tags) != parent
            or re.fullmatch(r'[ \t\r\n]*\\section\{', heading['render']['prefix']) is None
            or any(u['node_kind'] not in {'paragraph', 'list_item'}
                   or re.fullmatch(r'tag:' + re.escape(parent) + r':(?:p|item)[0-9]{3}',
                                   u['unit_id']) is None for u in units[1:])):
        raise RecordError('Section body end needs its complete canonical title and all prose/list members')
    before = {'kind': 'section_title', 'owner_tag': parent, 'ordinal': 1}
    after = selected['boundary_witness']['after']
    if (group['boundary_witness'] != {'before': before, 'after': None}
            or selected['boundary_witness']['before'] != before or after is None
            or after['kind'] != 'section_title' or after['owner_tag'] == parent
            or after['ordinal'] != 1):
        raise RecordError('Section body end needs the old batch ending and two distinct native Sections')
    preceding = containers.select({**selector, 'kind': 'section_title'})
    labels = [label for label, tag in containers.english.tags.items()
              if tag == after['owner_tag'] and label.startswith(heading['chapter'] + '-')]
    if len(labels) != 1:
        raise RecordError('Section body end has no unique following Section label')
    following = containers.select({'file': selector['file'], 'owner_tag': after['owner_tag'],
        'owner_label': labels[0], 'parent_tag': after['owner_tag'],
        'kind': 'section_title', 'ordinal': 1})
    if (preceding['location']['byte_end'] != selected['location']['byte_start']
            or following['location']['byte_start'] != selected['location']['byte_end']):
        raise RecordError('Section body end is not the full interval between its two native titles')
    # The existing v7 title contract permits only this verified namespace mapping.
    spacing = r'[ \t\r\n]*'
    old_label = selector['owner_label']
    if re.fullmatch(r'\}' + spacing + r'\\label\{' + re.escape(old_label)
                    + r'\}' + spacing, heading['render']['suffix']) is None:
        raise RecordError('Section body end lacks its plain complete old labelled title')
    native_label = re.search(r'\\label\{([^{}\n]+)\}' + spacing + r'\Z', preceding['fragment'])
    if (native_label is None
            or native_label[1] not in {old_label, old_label.removeprefix(heading['chapter'] + '-')}
            or containers.english.tags.get(heading['chapter'] + '-' + native_label[1],
                                            containers.english.tags.get(native_label[1])) != parent):
        raise RecordError('Section body end has a different native permanent title label')
    old_title = source_tex(heading).strip(SPACE)
    old_label_tex = '\\label{' + old_label + '}'
    if (old_title.count(old_label_tex) != 1
            or old_title.replace(old_label_tex, '\\label{' + native_label[1] + '}')
            != preceding['fragment'].strip(SPACE)):
        raise RecordError('Section body end changes the complete original Section title')
    complete_prose_signature(old_title, containers.policy)
    heading_signature = _complete_statement_signature(
        old_title, containers.policy, containers.english.tags, heading['chapter'])
    original = ''.join(source_tex(unit) for unit in units[1:])
    old_signature = complete_prose_signature(original, containers.policy)
    native_signature = complete_prose_signature(selected['fragment'], containers.policy)
    if old_signature != native_signature:
        raise RecordError('Section body end changes complete prose or protected bytes')
    # Count all independently scanned complete Section intervals, not a cached match.
    raw, rows, _ = containers.documents[heading['chapter']]
    count = 0
    for index, row in enumerate(rows):
        if row['unit']['node_kind'] != 'section_title':
            continue
        end = index + 1
        while (end < len(rows) and rows[end]['owner_tag'] == row['owner_tag']
               and rows[end]['parent_tag'] == row['owner_tag']
               and rows[end]['unit']['node_kind'] in {'paragraph', 'enumerate', 'itemize', 'description'}):
            end += 1
        if end == index + 1 or end == len(rows) or rows[end]['unit']['node_kind'] != 'section_title':
            continue
        fragment = raw[row['location']['byte_end']:rows[end]['location']['byte_start']].decode()
        try:
            count += complete_prose_signature(fragment, containers.policy) == native_signature
        except RecordError:
            continue
    if count != 1:
        raise RecordError('Section body end correspondence is ambiguous in the locked chapter')
    return {'body_input_unit_ids': ids, 'historical_parent_tag': parent,
        'preceding_section_title_input_unit_id': heading['unit_id'],
        'preceding_section_title_selector': preceding['selector'],
        'preceding_section_title_fragment_hash': preceding['location']['fragment_hash'],
        'preceding_section_title_signature_hash': sha256_value(heading_signature),
        'following_section_title_selector': following['selector'],
        'following_section_title_fragment_hash': following['location']['fragment_hash'],
        'historical_body_signature_hash': sha256_value(old_signature),
        'native_body_signature_hash': sha256_value(native_signature)}
