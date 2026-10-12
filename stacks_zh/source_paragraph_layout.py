"""Narrow, replayable historical math layout witnesses, never normalization."""
from __future__ import annotations

import re

from .extraction import Scanner
from .records import RecordError, sha256_value
from .source_container_boundaries import (
    SPACE, _complete_statement_signature, _item_tags, native_statement, paragraph_signature)
from .source_integrity import STATEMENTS
from .source_reextractions import byte_hash, source_tex

VERSION = 'source-container-v9'
# These are the entire accepted lexical language of this historical witness,
# not additions to the extraction/macro policy. Unknown atoms remain blocked.
ATOM = re.compile(r'\\mathcal\{[A-Z]\}|\\(?:Ob|to|phi|psi|circ)(?![A-Za-z])|[A-Za-z]+|[0-9]|[():=]')


def _math_node(fragment, policy):
    scanner = Scanner(fragment, policy)
    text, tokens, errors = scanner.protect(0, len(fragment))
    if (errors or scanner.math_text_regions or text != '<MATH_0001>'
            or tokens != {'MATH_0001': fragment}):
        raise RecordError('paragraph layout needs one complete untyped dollar math node')
    delimiter = '$$' if fragment.startswith('$$') else '$'
    if not fragment.startswith('$') or not fragment.endswith(delimiter):
        raise RecordError('paragraph layout supports only complete dollar math')
    body = fragment[len(delimiter):-len(delimiter)]
    cursor, depth, newline_positions = 0, 0, set()
    while cursor < len(body):
        character = body[cursor]
        if character in ' \t\n\r':
            width = 2 if body.startswith('\r\n', cursor) else 1
            if character == '\r' and width != 2:
                raise RecordError('paragraph layout does not accept a bare CR')
            if (character in '\r\n' and depth == 0 and cursor > 0
                    and cursor + width < len(body) and body[cursor - 1] not in SPACE
                    and body[cursor + width] not in SPACE):
                newline_positions.add(cursor)
            cursor += width
            continue
        match = ATOM.match(body, cursor)
        if match is None or (match[0].isalpha() and len(match[0]) != 1):
            raise RecordError('paragraph layout has unknown syntax or mathematical text')
        atom = match[0]
        if atom == '(':
            depth += 1
        elif atom == ')':
            depth -= 1
            if depth < 0:
                raise RecordError('paragraph layout has unbalanced parentheses')
        cursor = match.end()
    if depth or not body.strip(SPACE):
        raise RecordError('paragraph layout has empty math or unbalanced parentheses')
    return delimiter, body, newline_positions


def _math_difference(old, native, policy, ordinal):
    old_delimiter, old_body, _ = _math_node(old, policy)
    delimiter, body, positions = _math_node(native, policy)
    if delimiter == '$' and body != body.strip(SPACE):
        raise RecordError('paragraph layout needs an inline body without outer whitespace')
    prefix = suffix = ''
    operations = []
    if old_delimiter != delimiter:
        if delimiter != '$' or old_delimiter != '$$' or body != body.strip(SPACE):
            raise RecordError('paragraph layout is not a supported inline-to-display history')
        prefix = old_body[:len(old_body) - len(old_body.lstrip(' '))]
        suffix = old_body[len(old_body.rstrip(' ')):]
        old_body = old_body[len(prefix):len(old_body) - len(suffix) if suffix else None]
        operations.append('inline-to-display')
    offsets = []
    cursor = previous = 0
    while cursor < len(body):
        width = 2 if body.startswith('\r\n', cursor) else 1
        value = body[cursor:cursor + width]
        if old_body.startswith(value, previous):
            previous += width
        elif cursor in positions and old_body[previous:previous + 1] == ' ':
            offsets.append({'native_byte_offset': len(delimiter) + cursor, 'source': value})
            previous += 1
        else:
            raise RecordError('paragraph layout changes math bytes outside witnessed operations')
        cursor += width
    if previous != len(old_body):
        raise RecordError('paragraph layout has extra historical math bytes')
    if offsets:
        operations.append('linebreak-to-space')
    if not operations:
        if old != native:
            raise RecordError('paragraph layout changes unwitnessed math bytes')
        return None
    return {'math_ordinal': ordinal, 'historical_math': old, 'native_math': native,
            'historical_math_hash': byte_hash(old), 'native_math_hash': byte_hash(native),
            'operations': operations, 'display_prefix_spaces': prefix,
            'display_suffix_spaces': suffix, 'linebreaks': offsets}


def paragraph_layout_pair(old, native, policy, *, require_difference=True):
    """Compare full signatures; replay only two explicit native-to-old edits."""
    old_signature = paragraph_signature(old, policy)
    signature = paragraph_signature(native, policy)
    if len(old_signature) != len(signature):
        raise RecordError('paragraph layout changes the complete node count')
    differences, ordinal = [], 0
    for prior, current in zip(old_signature, signature):
        if prior[0] == current[0] == 'protected' and current[1].startswith('$'):
            ordinal += 1
            difference = _math_difference(prior[1], current[1], policy, ordinal)
            if difference:
                differences.append(difference)
        elif prior != current:
            raise RecordError('paragraph layout changes prose or non-math protected bytes')
        elif current[0] == 'protected':
            # Comments, literals and environments are never evidence here;
            # accepted ordinary commands still passed the original Scanner.
            if (current[1].startswith(('%', r'\verb', r'\begin', r'\end', r'\(', r'\['))
                    or '$' in current[1]):
                raise RecordError('paragraph layout includes unsupported opaque syntax')
    if require_difference and not differences:
        raise RecordError('paragraph layout needs an actual supported math difference')
    return {'historical_paragraph_signature_hash': sha256_value(old_signature),
            'native_paragraph_signature_hash': sha256_value(signature),
            'math_layout_differences': differences}


def paragraph_math_layout_witness(containers, units, groups, group, selected):
    ids, selector = group['input_unit_ids'], selected['selector']
    if (len(ids) != 1 or group['kind'] != 'paragraph' or group['ordinal'] is not None
            or selector['kind'] != 'paragraph' or selector['owner_tag'] != selector['parent_tag']):
        raise RecordError('paragraph layout needs one complete old Section-owned paragraph')
    by_id = {unit['unit_id']: unit for unit in units}
    old = by_id[ids[0]]
    if (old['schema_version'] != 1 or selected['inventory_unit']['schema_version'] != 1
            or old['node_kind'] != 'paragraph'
            or re.fullmatch(r'[ \t\r\n]*\\noindent[ \t\r\n]*', old['render']['prefix']) is None
            or old['render']['suffix'].strip(SPACE)):
        raise RecordError('paragraph layout requires the original plain unit-v1 noindent wrapper')
    index = groups.index(group)
    if index == 0 or groups[index - 1]['kind'] not in STATEMENTS:
        raise RecordError('paragraph layout lacks a complete immediately preceding statement')
    preceding = groups[index - 1]
    members = [by_id[identifier] for identifier in preceding['input_unit_ids']]
    order = [unit['unit_id'] for unit in units]
    start = order.index(old['unit_id'])
    if (order[start - len(members):start] != preceding['input_unit_ids']
            or any(unit['parent_tag'] != old['parent_tag'] for unit in members)
            or group['file'] != selector['file']):
        raise RecordError('paragraph layout crosses its full frozen preceding statement')
    kind = re.escape(preceding['kind'])
    if (re.fullmatch(r'\s*\\begin\{' + kind + r'\}\s*\\label\{[^{}\n]+\}\s*',
                     members[0]['render']['prefix']) is None
            or re.fullmatch(r'\s*\\end\{' + kind + r'\}\s*', members[-1]['render']['suffix']) is None):
        raise RecordError('paragraph layout needs a complete plain labelled preceding statement')
    statement = native_statement(containers, preceding)
    old_statement = ''.join(source_tex(unit) for unit in members)
    _item_tags(old_statement, containers.policy, containers.english.tags, old['chapter'])
    signature = _complete_statement_signature(old_statement, containers.policy,
                                             containers.english.tags, old['chapter'])
    if signature != _complete_statement_signature(statement['fragment'], containers.policy,
                                                 containers.english.tags, old['chapter']):
        raise RecordError('paragraph layout preceding statement changes complete source bytes')
    if statement['selector']['parent_tag'] != selector['parent_tag']:
        raise RecordError('paragraph layout and preceding statement have different real Sections')
    raw, rows, _ = containers.documents[selector['file'][:-4]]
    positions = [i for i, row in enumerate(rows) if row['location'] == selected['location']]
    if (len(positions) != 1 or positions[0] == 0
            or rows[positions[0] - 1]['location'] != statement['location']
            or raw[statement['location']['byte_end']:selected['location']['byte_start']].strip(b' \t\r\n')):
        raise RecordError('paragraph layout is not immediately after the same native statement')
    historical = source_tex(old)
    witness = paragraph_layout_pair(historical, selected['fragment'], containers.policy)
    count = 0
    for row in rows:
        if row['unit']['node_kind'] != 'paragraph':
            continue
        location = row['location']
        fragment = raw[location['byte_start']:location['byte_end']].decode('utf-8')
        try:
            paragraph_layout_pair(historical, fragment, containers.policy, require_difference=False)
        except RecordError:
            continue
        count += 1
    if count != 1:
        raise RecordError('paragraph layout source correspondence is ambiguous in the locked chapter')
    return {'paragraph_input_unit_id': old['unit_id'], 'historical_parent_tag': old['parent_tag'],
            'preceding_statement_input_unit_ids': preceding['input_unit_ids'],
            'preceding_statement_selector': statement['selector'],
            'preceding_statement_fragment_hash': statement['location']['fragment_hash'],
            'preceding_statement_signature_hash': sha256_value(signature), **witness}
