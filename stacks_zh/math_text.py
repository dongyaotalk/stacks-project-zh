"""Typed plain-text leaves inside otherwise byte-locked math.

No translation is generated here. Git witnesses are resolved by extraction;
immutable source-container replay supplies the authority for adopted units.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from typing import Any

TOKEN = re.compile(r'<([A-Z][A-Z0-9]*_[0-9]{4})>')
COMMAND = re.compile(r'\\(?:[A-Za-z@]+|[\s\S])')
USAGES = {'quad-connector', 'matrix-condition', 'set-description'}
MATH_ENVIRONMENTS = {'equation', 'equation*', 'align', 'align*', 'aligned',
                     'eqnarray', 'eqnarray*', 'matrix'}


def digest(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return 'sha256:' + hashlib.sha256(text.encode('utf-8')).hexdigest()


def plain_text(text: str) -> bool:
    return (isinstance(text, str) and bool(text.strip())
            and not re.search(r'[\\%${}#_&^~<>]', text)
            and not any(unicodedata.category(c).startswith('C') for c in text))


def policy_rules(text: str, notations: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Strict, JSON-valued subset of the macro policy's explicit registry."""
    rules, active, seen, entry = {}, False, False, None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if not line.startswith(' '):
            active = line == 'translatable_math_text:'
            if line.partition(':')[0] == 'translatable_math_text':
                if not active or seen:
                    raise ValueError('invalid or duplicate natural math-text policy section')
                seen = True
            entry = None
        elif active:
            match = re.fullmatch(r'  ([a-z][a-z0-9-]*):', line)
            if match:
                entry = match[1]
                if entry in rules:
                    raise ValueError('duplicate natural math-text policy entry')
                rules[entry] = {}
            else:
                field = re.fullmatch(r'    ([a-z_]+): (.+)', line)
                if field is None or entry is None or field[1] in rules[entry]:
                    raise ValueError('invalid or duplicate natural math-text policy field')
                rules[entry][field[1]] = json.loads(field[2])
    seen_literals = set()
    for rule in rules.values():
        if set(rule) != {'literal', 'command', 'usage', 'source_label', 'witness_kind', 'witness_ordinal'}:
            raise ValueError('incomplete natural math-text policy')
        literal = rule['literal']
        if (not isinstance(literal, str) or not re.fullmatch(r'[A-Za-z][A-Za-z -]*', literal)
                or not re.search(r'[A-Za-z]{2,}', literal) or literal in seen_literals):
            raise ValueError('invalid or duplicate natural math-text literal')
        if literal in notations:
            raise ValueError('math text cannot be both notation and natural language')
        seen_literals.add(literal)
        if (rule['command'] != 'text' or not isinstance(rule['usage'], str)
                or rule['usage'] not in USAGES):
            raise ValueError('unsupported natural math-text command or usage')
        if (not isinstance(rule['source_label'], str)
                or not re.fullmatch(r'[a-z][a-z0-9_-]*-[A-Za-z][A-Za-z0-9_-]*', rule['source_label'])
                or not isinstance(rule['witness_kind'], str)
                or rule['witness_kind'] not in {'section', 'lemma', 'proof'}
                or type(rule['witness_ordinal']) is not int or rule['witness_ordinal'] < 1):
            raise ValueError('invalid natural math-text source witness')
    return rules


def _argument(source: str, start: int) -> int:
    depth, i = 1, start + 1
    while i < len(source):
        if source[i] == '%':
            end = source.find('\n', i)
            i = len(source) if end < 0 else end + 1
            continue
        command = COMMAND.match(source, i)
        if command:
            i = command.end()
            continue
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if not depth:
                return i + 1
        i += 1
    raise ValueError('unclosed math command argument')


def nodes(source: str) -> list[dict[str, Any]]:
    """Non-executing lexical structure; text/metadata arguments stay opaque."""
    output, environments, groups, i = [], [], [], 0
    while i < len(source):
        if source[i].isspace():
            i += 1
            continue
        if source[i] == '%':
            end = source.find('\n', i)
            i = len(source) if end < 0 else end + 1
            continue
        start = i
        command = COMMAND.match(source, i)
        node = {'start': start, 'depth': len(groups), 'environments': list(environments)}
        if command:
            name = command.group()[1:]
            i = command.end()
            opening = i
            while opening < len(source) and source[opening].isspace():
                opening += 1
            if name in {'verb', 'Verb'}:
                if source[i:i + 1] == '*':
                    i += 1
                delimiter = source[i:i + 1]
                ending = source.find(delimiter, i + 1) if delimiter and not delimiter.isspace() else -1
                if ending < 0:
                    raise ValueError('unclosed literal inside math')
                i = ending + 1
            elif name in {'begin', 'end', 'text', 'textit', 'textbf',
                        'label', 'ref', 'eqref', 'pageref', 'cite', 'url'} and source[opening:opening + 1] == '{':
                i = _argument(source, opening)
                value = source[opening + 1:i - 1]
                if name in {'begin', 'end'}:
                    if name == 'begin':
                        environments.append(value)
                    elif not environments or environments.pop() != value:
                        raise ValueError('unbalanced math environment')
                elif name in {'text', 'textit', 'textbf'}:
                    node.update(command=name, parameter_start=opening + 1,
                                parameter_end=i - 1, value=value)
            node['token'] = source[start:i]
        else:
            node['token'] = source[i]
            if source[i] in '{[':
                groups.append(source[i])
            elif source[i] in '}]':
                if not groups or groups.pop() != {'}': '{', ']': '['}[source[i]]:
                    raise ValueError('unbalanced math group')
            i += 1
        node['end'] = i
        output.append(node)
    if groups or environments:
        raise ValueError('unclosed math group or environment')
    return output


def delimiter_kind(source: str) -> str:
    for opening, closing, kind in [('$$', '$$', 'display-dollar'), ('$', '$', 'inline-dollar'),
                                   (r'\(', r'\)', 'inline-paren'), (r'\[', r'\]', 'display-bracket')]:
        if not source.startswith(opening):
            continue
        i = len(opening)
        while i < len(source):
            if source[i] == '%':
                end = source.find('\n', i)
                i = len(source) if end < 0 else end + 1
                continue
            if source.startswith(closing, i):
                if i + len(closing) == len(source):
                    return kind
                raise ValueError('math region contains bytes outside its first closing delimiter')
            command = COMMAND.match(source, i)
            i = command.end() if command else i + 1
        raise ValueError('math region lacks its closing delimiter')
    stream = nodes(source)
    begin = re.fullmatch(r'\\begin\{([A-Za-z][A-Za-z0-9*_-]*)\}', stream[0]['token']) if stream else None
    if begin and begin[1] in MATH_ENVIRONMENTS and stream[-1]['token'] == r'\end{' + begin[1] + '}' and stream[-1]['end'] == len(source):
        return 'environment'
    raise ValueError('typed math region is not a complete original math node')


def usage(source: str, stream: list[dict[str, Any]], index: int, kind: str):
    node = stream[index]
    if (node['depth'] != 0 or index == 0 or index + 1 >= len(stream)
            or set(node['environments']) - MATH_ENVIRONMENTS):
        return None
    before, after = stream[index - 1], stream[index + 1]
    if kind == 'quad-connector':
        valid = before['token'] == after['token'] == r'\quad'
    elif kind == 'matrix-condition':
        valid = (before['token'] == after['token'] == '&'
                 and node['environments'] and node['environments'][-1] == 'matrix')
    elif kind == 'set-description':
        valid = (before['token'] == r'\{' and re.fullmatch(r'[A-Z]', after['token'])
                 and any(n['token'] == r'\}' and n['depth'] == 0 for n in stream[index + 2:]))
    else:
        return None
    if not valid:
        return None
    return {'before': source[before['start']:node['start']],
            'after': source[node['end']:after['end']], 'environments': node['environments']}


def find_slots(source: str, rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    stream = nodes(source)
    if not _known_environments(stream):
        return []
    accepted = []
    for index, node in enumerate(stream):
        if node.get('command') != 'text' or not plain_text(node.get('value', '')):
            continue
        for key, rule in rules.items():
            if node['value'] != rule['literal'] or node['command'] != rule['command']:
                continue
            witness = usage(source, stream, index, rule['usage'])
            if witness is not None:
                accepted.append({**node, 'policy_entry': key, 'usage': rule['usage'], 'usage_source': witness})
    return accepted


def _known_environments(stream: list[dict[str, Any]]) -> bool:
    for node in stream:
        match = re.fullmatch(r'\\(?:begin|end)\{([^{}]+)\}', node['token'])
        if match and match[1] not in MATH_ENVIRONMENTS:
            return False
    return True


def restore(unit: dict[str, Any], text: str) -> str:
    return TOKEN.sub(lambda m: unit['placeholders'][m[1]], text)


def complete_math_nodes(unit: dict[str, Any]) -> list[str]:
    regions = {r['pieces'][0]['placeholder']: r for r in unit.get('math_text_regions', [])}
    return [unit['placeholders'][name] if name.startswith('MATH_') else regions[name]['source']
            for name in TOKEN.findall(unit['source_text']) if name.startswith('MATH_') or name in regions]


def skeleton(unit: dict[str, Any]) -> list[Any]:
    regions = {r['pieces'][0]['placeholder']: r for r in unit['math_text_regions']}
    output = []
    for name in TOKEN.findall(unit['source_text']):
        if name.startswith('MATH_'):
            output.append({'kind': 'math', 'source': unit['placeholders'][name]})
        elif name in regions:
            region = regions[name]
            slots = {s['slot_id']: s for s in region['slots']}
            pieces = []
            for piece in region['pieces']:
                if piece['kind'] == 'locked':
                    pieces.append({'locked': unit['placeholders'][piece['placeholder']]})
                else:
                    slot = slots[piece['slot_id']]
                    pieces.append({'slot': slot['slot_id'], 'command': slot['command'],
                                   'usage': slot['classification_witness']['usage'],
                                   'boundaries': slot['boundary_placeholders']})
            output.append({'kind': 'typed-math', 'region_id': region['region_id'],
                           'delimiter_kind': region['delimiter_kind'], 'pieces': pieces})
    return output


def bind_regions(unit: dict[str, Any], proposed: list[dict[str, Any]]) -> dict[str, Any]:
    """Bind renamed tokens to complete fact/IR source coordinates."""
    if not proposed:
        return unit
    unit = copy.deepcopy(unit)
    ordered = sorted(proposed, key=lambda r: unit['source_text'].index('<' + r['pieces'][0]['placeholder'] + '>'))
    regions = []
    for index, original in enumerate(ordered, 1):
        region = copy.deepcopy(original)
        region['region_id'] = f'math/{index:04d}'
        first = '<' + region['pieces'][0]['placeholder'] + '>'
        start = len((unit['render']['prefix'] + restore(unit, unit['source_text'].partition(first)[0])).encode('utf-8'))
        region['source_byte_span'] = {'start': start, 'end': start + len(region['source'].encode('utf-8'))}
        renaming = {}
        for ordinal, slot in enumerate(region['slots'], 1):
            new = f"{region['region_id']}/text/{ordinal:04d}"
            renaming[slot['slot_id']] = new
            slot['slot_id'] = new
        for piece in region['pieces']:
            if piece['kind'] == 'text':
                piece['slot_id'] = renaming[piece['slot_id']]
        regions.append(region)
    unit.update(schema_version=2, risk_level='R3', math_text_regions=regions)
    unit['source_math_skeleton_hash'] = digest(skeleton(unit))
    return unit


def validate_regions(unit: dict[str, Any]) -> list[str]:
    if type(unit.get('schema_version')) is not int or unit['schema_version'] not in {1, 2}:
        return ['unsupported mathematical unit schema version']
    if unit['schema_version'] == 1:
        return ['unit-v1 cannot contain split math tokens'] if any(
            name.startswith('MATHSEG_') for name in unit.get('placeholders', {})) else []
    try:
        from .schema_validation import validate_named_schema
        regions = unit['math_text_regions']
        errors = validate_named_schema(regions, 'math-text-regions.schema.json', 'math_text_regions')
        if errors:
            return errors
        if not regions or unit['risk_level'] != 'R3':
            raise ValueError('unit-v2 requires nonempty math regions and R3 risk')
        full = (unit['render']['prefix'] + restore(unit, unit['source_text']) + unit['render']['suffix']).encode('utf-8')
        used, last_end = [], -1
        for index, region in enumerate(regions, 1):
            if region['region_id'] != f'math/{index:04d}':
                raise ValueError('math region IDs/order differ from source')
            source = region['source']
            span = region['source_byte_span']
            if (span['start'] < max(0, last_end) or span['end'] != span['start'] + len(source.encode('utf-8'))
                    or span['end'] > len(full) or full[span['start']:span['end']] != source.encode('utf-8')):
                raise ValueError('math region has incorrect UTF-8 source span/order')
            last_end = span['end']
            if digest(source) != region['source_hash']:
                raise ValueError('complete original math region hash differs')
            if delimiter_kind(source) != region['delimiter_kind']:
                raise ValueError('math region delimiter kind differs from its complete source')
            pieces, slots = region['pieces'], region['slots']
            if not slots or len(pieces) != 2 * len(slots) + 1:
                raise ValueError('math pieces must alternate locked/text/locked without gaps')
            rebuilt, protected = '', ''
            stream = nodes(source)
            if not _known_environments(stream):
                raise ValueError('typed math region contains an unsupported environment')
            for part, piece in enumerate(pieces):
                if part % 2 == 0:
                    if piece['kind'] != 'locked' or not re.fullmatch(r'MATHSEG_[0-9]{4}', piece['placeholder']):
                        raise ValueError('invalid locked math piece')
                    name = piece['placeholder']
                    value = unit['placeholders'][name]
                    if not value:
                        raise ValueError('empty locked math piece')
                    used.append(name)
                    rebuilt += value
                    protected += '<' + name + '>'
                else:
                    slot = slots[part // 2]
                    if (piece['kind'] != 'text' or piece['slot_id'] != slot['slot_id']
                            or slot['slot_id'] != f"{region['region_id']}/text/{part // 2 + 1:04d}"):
                        raise ValueError('math text slot ID/order differs')
                    bounds = [pieces[part - 1]['placeholder'], pieces[part + 1]['placeholder']]
                    if slot['boundary_placeholders'] != bounds or not plain_text(slot['source']):
                        raise ValueError('math text slot has invalid boundaries or plain source')
                    a = len(rebuilt.encode('utf-8')); b = a + len(slot['source'].encode('utf-8'))
                    if slot['slot_byte_span'] != {'start': a, 'end': b}:
                        raise ValueError('math slot UTF-8 byte span differs')
                    matches = [(i, n) for i, n in enumerate(stream) if n.get('command') == slot['command']
                               and len(source[:n['parameter_start']].encode('utf-8')) == a
                               and len(source[:n['parameter_end']].encode('utf-8')) == b]
                    if len(matches) != 1 or matches[0][1]['value'] != slot['source']:
                        raise ValueError('math slot is not a complete real text command parameter')
                    witness = slot['classification_witness']
                    anchor = witness['anchor']
                    if (anchor['source_commit'] != unit['source_commit']
                            or anchor['owner_label'] != witness['source_label'] or not anchor['matches']
                            or anchor['ordinal'] < 1):
                        raise ValueError('math text witness lacks a consistent locked source anchor')
                    for match in anchor['matches']:
                        container, command = match['container_byte_span'], match['command_byte_span']
                        if not (0 <= container['start'] <= command['start'] < command['end'] <= container['end']):
                            raise ValueError('math text witness command span is outside its real container')
                    actual = usage(source, stream, matches[0][0], witness['usage'])
                    if actual is None or actual != witness['usage_source']:
                        raise ValueError('math text syntax witness differs from original structure')
                    rebuilt += slot['source']; protected += slot['source']
            if rebuilt != source or protected not in unit['source_text']:
                raise ValueError('math region pieces do not exactly cover contiguous protected source')
        if len(used) != len(set(used)) or set(used) != {n for n in unit['placeholders'] if n.startswith('MATHSEG_')}:
            raise ValueError('math segments are repeated, missing or outside all declared regions')
        if any(TOKEN.findall(unit['source_text']).count(name) != 1 for name in used):
            raise ValueError('each math segment must occur exactly once in protected source')
        if digest(skeleton(unit)) != unit['source_math_skeleton_hash']:
            raise ValueError('original mathematical skeleton hash differs')
        return []
    except (ValueError, KeyError, TypeError, IndexError) as exc:
        return ['invalid typed math source: ' + str(exc)]


def validate_translation(unit: dict[str, Any], translation: str) -> list[str]:
    errors = validate_regions(unit)
    if errors or unit.get('schema_version') != 2:
        return errors
    if not isinstance(translation, str):
        return ['typed math translation must be a string']
    if TOKEN.findall(translation) != TOKEN.findall(unit['source_text']):
        return ['typed math translation changed protected token sequence']
    try:
        for region in unit['math_text_regions']:
            original_nodes = nodes(region['source'])
            identities = {}
            for slot in region['slots']:
                before, after = ('<' + n + '>' for n in slot['boundary_placeholders'])
                text = translation.split(before, 1)[1].split(after, 1)[0]
                if not plain_text(text) or TOKEN.search(text):
                    raise ValueError('math text translation must be nonempty plain text in its original slot')
                index = next(i for i, n in enumerate(original_nodes) if n.get('command') == slot['command']
                             and len(region['source'][:n['parameter_start']].encode('utf-8')) == slot['slot_byte_span']['start'])
                identities[index] = slot
            before = '<' + region['pieces'][0]['placeholder'] + '>'
            after = '<' + region['pieces'][-1]['placeholder'] + '>'
            start = translation.index(before)
            end = translation.index(after, start) + len(after)
            actual = restore(unit, translation[start:end])

            def projection(source):
                stream, pieces, cursor = nodes(source), [], 0
                if len(stream) != len(original_nodes):
                    raise ValueError('translated mathematical node sequence differs')
                for index, slot in identities.items():
                    node = stream[index]
                    if (node.get('command') != slot['command'] or not plain_text(node.get('value', ''))
                            or usage(source, stream, index, slot['classification_witness']['usage']) is None):
                        raise ValueError('translated slot lost its original command/role')
                    pieces.extend([{'locked': source[cursor:node['parameter_start']]},
                                   {'slot': slot['slot_id'], 'command': slot['command'],
                                    'usage': slot['classification_witness']['usage']}])
                    cursor = node['parameter_end']
                pieces.append({'locked': source[cursor:]})
                return pieces

            if projection(actual) != projection(region['source']):
                raise ValueError('translated mathematical skeleton differs outside typed text leaves')
        return []
    except (ValueError, KeyError, IndexError, StopIteration) as exc:
        return ['invalid typed math translation: ' + str(exc)]
