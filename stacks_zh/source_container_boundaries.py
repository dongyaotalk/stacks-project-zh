"""Independently witnessed legacy boundaries; never an owner/parent waiver."""
from __future__ import annotations

import re

from .extraction import ENVIRONMENT, Scanner
from .records import RecordError, sha256_value
from .source_integrity import STATEMENTS, _own_tag
from .source_reextractions import source_tex

VERSION = 'source-container-v4'
SPACE = ' \t\r\n'
TOKEN = re.compile(r'<([A-Z]+_[0-9]{4})>')


def native_statement(containers, group):
    """Find the actual labelled statement, deriving its Section from Git."""
    chapter = group['file'][:-4]
    _, rows, _ = containers.documents[chapter]
    matches = [row for row in rows if row['owner_tag'] == group['owner_tag']
               and row['semantic_path'] == f"{group['kind']}/{group['ordinal']:04d}"
               and row['unit']['node_kind'] in STATEMENTS]
    labels = [label for label, tag in containers.english.tags.items()
              if tag == group['owner_tag'] and label.startswith(chapter + '-')]
    if len(matches) != 1 or len(labels) != 1:
        raise RecordError('legacy boundary has no unique native labelled statement')
    return containers.select({'file': group['file'], 'owner_tag': group['owner_tag'],
        'owner_label': labels[0], 'parent_tag': matches[0]['parent_tag'],
        'kind': group['kind'], 'ordinal': group['ordinal']})


def _item_tags(fragment, policy, tags, chapter):
    scanner = Scanner(fragment, policy)
    text, tokens, errors = scanner.protect(0, len(fragment))
    if errors:
        raise RecordError('native item labels have unsupported source syntax')
    stack, depth, pending, result, cursor, opened, closed = [], 0, False, [], 0, False, False
    for match in TOKEN.finditer(text):
        prose = text[cursor:match.start()].strip(SPACE)
        if prose:
            if not opened or closed:
                raise RecordError('legacy boundary contains prose outside its complete statement')
            pending = False
        name = match[1]
        value = tokens[name]
        role = name.rsplit('_', 1)[0]
        if role == 'COMMENT':
            cursor = match.end()
            continue
        if closed:
            raise RecordError('legacy boundary contains a node after the real statement closing')
        if role.endswith('OPEN'):
            depth += 1
        elif role.endswith('CLOSE') or role in {'ENVARGEND', 'ITEMCLOSE'}:
            depth -= 1
        environment = ENVIRONMENT.fullmatch(value) if role == 'STRUCT' else None
        if environment and depth == 0:
            action, kind = environment[1], environment[2]
            if action == 'begin':
                if not opened:
                    if kind not in STATEMENTS:
                        raise RecordError('legacy boundary does not start with a real statement')
                    opened = True
                stack.append(kind)
            elif not stack or stack.pop() != kind:
                raise RecordError('native item labels have unbalanced structural ownership')
            elif not stack:
                closed = True
        label = re.fullmatch(r'\\label\{([^{}\n]+)\}', value) if role == 'LOCKED' else None
        if label and pending and depth == 0:
            tag = tags.get(label[1], tags.get(chapter + '-' + label[1]))
            if tag is None:
                raise RecordError('native list item has no permanent Tag')
            result.append(tag)
        pending = (value == r'\item' and role == 'STRUCT' and depth == 0
                   and bool(stack) and stack[0] in STATEMENTS
                   and stack[-1] in {'enumerate', 'itemize'})
        cursor = match.end()
    if not opened or not closed or stack or depth or text[cursor:].strip(SPACE):
        raise RecordError('legacy boundary does not cover one complete real statement wrapper')
    return result


def secondary_statement_witness(containers, units, group):
    """Bind every secondary Tag to its actual native list position."""
    by_id = {unit['unit_id']: unit for unit in units}
    members = [by_id[identifier] for identifier in group['input_unit_ids']]
    first, tags = members[0], containers.english.tags
    primary = re.fullmatch(r'\s*\\begin\{' + re.escape(group['kind'])
                          + r'\}\s*\\label\{[^{}\n]+\}\s*', first['render']['prefix'])
    if primary is None or _own_tag(first, tags) != group['owner_tag']:
        raise RecordError('legacy secondary labels lack their plain native statement opening')
    old_tags = []
    for member in members[1:]:
        own = _own_tag(member, tags)
        if own is None:
            if member['parent_tag'] != first['parent_tag']:
                raise RecordError('legacy secondary child has an arbitrary parent')
            continue
        if (member['node_kind'] != 'list_item' or own != member['parent_tag']
                or re.fullmatch(r'\s*\\item\s*\\label\{[^{}\n]+\}\s*',
                                member['render']['prefix']) is None):
            raise RecordError('legacy secondary Tag is not the real adjacent item label')
        old_tags.append(own)
    selected = native_statement(containers, group)
    native_tags = _item_tags(selected['fragment'], containers.policy, tags, first['chapter'])
    original_tags = _item_tags(''.join(source_tex(u) for u in members), containers.policy, tags, first['chapter'])
    if (not old_tags or len(set(old_tags)) != len(old_tags)
            or old_tags != native_tags or old_tags != original_tags):
        raise RecordError('legacy secondary item Tags differ from the complete native list order')
    return {'statement_input_unit_ids': group['input_unit_ids'],
        'historical_parent_tags': list(dict.fromkeys(u['parent_tag'] for u in members)),
        'native_item_tags': native_tags, 'statement_selector': selected['selector'],
        'statement_fragment_hash': selected['location']['fragment_hash']}


def paragraph_signature(fragment, policy):
    """Only ordinary ASCII prose wrapping differs; protected bytes stay exact."""
    fragment = fragment.strip(SPACE)
    if re.search(r'\n[ \t\r]*\n', fragment):
        raise RecordError('adjacent paragraph boundary does not support internal blank paragraphs')
    scanner = Scanner(fragment, policy)
    text, tokens, errors = scanner.protect(0, len(fragment))
    if errors or scanner.math_text_regions:
        raise RecordError('adjacent paragraph boundary has unsupported source syntax or typed math text')
    signature, cursor = [], 0

    def prose(value):
        normalized = re.sub(r'[ \t\r\n]+', ' ', value).strip(' ')
        if normalized:
            signature.append(['text', normalized])

    for match in TOKEN.finditer(text):
        prose(text[cursor:match.start()])
        if match[1] not in tokens:
            raise RecordError('adjacent paragraph has a forged protected token')
        signature.append(['protected', tokens[match[1]]])
        cursor = match.end()
    prose(text[cursor:])
    return signature


def adjacent_paragraph_witness(containers, units, groups, group, selected):
    ids = group['input_unit_ids']
    if len(ids) != 1 or group['kind'] != 'paragraph' or group['ordinal'] is not None:
        raise RecordError('adjacent paragraph boundary requires one complete old paragraph')
    by_id = {unit['unit_id']: unit for unit in units}
    old = by_id[ids[0]]
    index = groups.index(group)
    if index + 1 >= len(groups) or groups[index + 1]['kind'] not in STATEMENTS:
        raise RecordError('adjacent paragraph has no complete following old statement')
    following = groups[index + 1]
    members = [by_id[identifier] for identifier in following['input_unit_ids']]
    order = [unit['unit_id'] for unit in units]
    start = order.index(old['unit_id'])
    if (order[start + 1:start + 1 + len(members)] != following['input_unit_ids']
            or any(u['parent_tag'] != old['parent_tag'] for u in members)
            or group['file'] != selected['selector']['file']):
        raise RecordError('adjacent paragraph crosses its full frozen statement scope')
    first = members[0]
    if re.fullmatch(r'\s*\\begin\{' + re.escape(following['kind'])
                   + r'\}\s*\\label\{[^{}\n]+\}\s*', first['render']['prefix']) is None:
        raise RecordError('adjacent paragraph lacks a real following statement wrapper')
    native = native_statement(containers, following)
    _item_tags(''.join(source_tex(u) for u in members), containers.policy,
               containers.english.tags, old['chapter'])
    selector = selected['selector']
    if (selector['owner_tag'] != selector['parent_tag']
            or native['selector']['parent_tag'] != selector['parent_tag']):
        raise RecordError('adjacent paragraph and native statement have different real Section ownership')
    raw, rows, _ = containers.documents[selector['file'][:-4]]
    matches = [i for i, row in enumerate(rows) if row['location'] == selected['location']]
    if len(matches) != 1 or matches[0] + 1 >= len(rows):
        raise RecordError('adjacent paragraph has no unique complete native position')
    next_row = rows[matches[0] + 1]
    if (next_row['location'] != native['location']
            or raw[selected['location']['byte_end']:native['location']['byte_start']].strip(b' \t\r\n')):
        raise RecordError('adjacent paragraph is not immediately before the same native statement')
    signature = paragraph_signature(source_tex(old), containers.policy)
    if signature != paragraph_signature(selected['fragment'], containers.policy):
        raise RecordError('adjacent paragraph changes prose or protected bytes')
    count = 0
    for row in rows:
        if row['unit']['node_kind'] != 'paragraph':
            continue
        location = row['location']
        fragment = raw[location['byte_start']:location['byte_end']].decode('utf-8')
        try:
            count += paragraph_signature(fragment, containers.policy) == signature
        except RecordError:
            continue
    if count != 1:
        raise RecordError('adjacent paragraph source signature is ambiguous in the locked chapter')
    return {'paragraph_input_unit_id': old['unit_id'], 'historical_parent_tag': old['parent_tag'],
        'following_statement_input_unit_ids': following['input_unit_ids'],
        'following_statement_selector': native['selector'],
        'following_statement_fragment_hash': native['location']['fragment_hash'],
        'paragraph_signature_hash': sha256_value(signature)}
