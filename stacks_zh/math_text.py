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
USAGES = {'quad-connector', 'matrix-condition', 'set-description',
          'root-phrase', 'matrix-prefix-condition', 'arrow-label-prefix',
          'matrix-row-text', 'matrix-row-prefix', 'numeric-isomorphism-suffix',
          'root-condition', 'matrix-row-condition', 'root-hyphen-phrase'}
MATRIX_ROW_USAGES = {'matrix-row-text', 'matrix-row-prefix'}
COMPONENT_USAGE = 'indexed-component-description'
COMPONENT_LITERAL = r' irred.\ comp. with '
COMPONENT_SEPARATOR = '\\ '
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
    rules, active, seen, entry, components = {}, False, set(), None, False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if not line.startswith(' '):
            section = line.partition(':')[0]
            components = section == 'translatable_math_text_components'
            active = line in {'translatable_math_text:', 'translatable_math_text_components:'}
            if section in {'translatable_math_text', 'translatable_math_text_components'}:
                if not active or section in seen:
                    raise ValueError('invalid or duplicate natural math-text policy section')
                seen.add(section)
            entry = None
        elif active:
            match = re.fullmatch(r'  ([a-z][a-z0-9-]*):', line)
            if match:
                entry = match[1]
                if entry in rules:
                    raise ValueError('duplicate natural math-text policy entry')
                rules[entry] = {'slot_schema_version':3} if components else {}
            else:
                field = re.fullmatch(r'    ([a-z_]+): (.+)', line)
                if field is None or entry is None or field[1] in rules[entry]:
                    raise ValueError('invalid or duplicate natural math-text policy field')
                rules[entry][field[1]] = json.loads(field[2])
    seen_literals = set()
    for rule in rules.values():
        component = rule.get('slot_schema_version') == 3
        if set(rule) != ({'literal', 'command', 'usage', 'source_label', 'witness_kind', 'witness_ordinal'}
                         | ({'slot_schema_version','components','separator'} if component else set())):
            raise ValueError('incomplete natural math-text policy')
        literal = rule['literal']
        literal_pattern = (r' *[A-Za-z][A-Za-z0-9 -]*'
                           if rule.get('usage') in MATRIX_ROW_USAGES
                           else r'-[A-Za-z][A-Za-z -]*'
                           if rule.get('usage') == 'root-hyphen-phrase'
                           else r' *[A-Za-z][A-Za-z -]*')
        if (not isinstance(literal, str) or not (literal == COMPONENT_LITERAL if component else
                literal == '-isomorphism' if rule.get('usage') == 'numeric-isomorphism-suffix'
                else re.fullmatch(literal_pattern, literal))
                or not re.search(r'[A-Za-z]{2,}', literal) or literal in seen_literals):
            raise ValueError('invalid or duplicate natural math-text literal')
        if literal in notations:
            raise ValueError('math text cannot be both notation and natural language')
        seen_literals.add(literal)
        if (rule['command'] != 'text' or not isinstance(rule['usage'], str)
                or rule['usage'] not in ({COMPONENT_USAGE} if component else USAGES)):
            raise ValueError('unsupported natural math-text command or usage')
        if component and (rule['separator'] != COMPONENT_SEPARATOR
                          or rule['components'] != [' irred.','comp. with ']):
            raise ValueError('unsupported composite natural math-text leaves or separator')
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


def _description_matrix_root(stream, index):
    openings = [i for i, part in enumerate(stream[:index])
                if part['token'] == r'\begin{matrix}' and part['depth'] == 0]
    if not openings:
        return False
    start = openings[-1]
    if start >= 2 and [part['token'] for part in stream[start-2:start]] == [r'\left', r'\{']:
        start -= 2
    return (start == 0 or stream[start-1]['depth'] == 0
            and stream[start-1]['token'] in {'$', r'\[', r'\(', ':', '=',
                                            r'\leftrightarrow', r'\longrightarrow'})


_CONDITION_RELATIONS = {r'\Leftarrow', r'\Rightarrow', r'\Leftrightarrow'}
_CONDITION_SYMBOLS = {r'\to', r'\Spec', r'\QCoh', r'\subset',
                      r'\left', r'\right', r'\middle', r'\{', r'\}', r'\\'}
_BRACED_OBJECTS = {r'\mathcal', r'\mathbf', r'\mathbb', r'\mathrm', r'\mathsf'}


def _condition_math_context(source, stream):
    """Bound the new roles; do not infer arguments of ungrouped commands."""
    try:
        delimiter_kind(source)
    except ValueError:
        return False
    for index, part in enumerate(stream):
        token = part['token']
        if part['depth'] or not token.startswith('\\'):
            continue
        if (token in _CONDITION_SYMBOLS | _CONDITION_RELATIONS
                or token in {r'\(', r'\)', r'\[', r'\]',
                             r'\begin{matrix}', r'\end{matrix}'}
                or part.get('command') == 'text'):
            continue
        if (token in _BRACED_OBJECTS and index + 1 < len(stream)
                and stream[index + 1]['token'] == '{'):
            continue
        return False
    return True


def _condition_operand_end(part):
    return re.fullmatch(r"[A-Za-z0-9)\]}']", part['token']) is not None


def _condition_relation_object(stream, index):
    return (index + 2 < len(stream)
            and stream[index + 1]['token'] in _CONDITION_RELATIONS
            and re.fullmatch(r'[A-Za-z0-9]', stream[index + 2]['token']) is not None)


def _condition_matrix_root(stream, index):
    if _description_matrix_root(stream, index):
        return True
    openings = [i for i, part in enumerate(stream[:index])
                if part['token'] == r'\begin{matrix}' and part['depth'] == 0]
    if not openings:
        return False
    opening = openings[-1]
    body = [part['token'] for part in stream[:opening]]
    while body and body[0] in {'$', r'\[', r'\('}:
        body.pop(0)
    if len(body) >= 2 and re.fullmatch(r'[A-Z]', body[0]) and body[1] == '=':
        body = body[2:]
    if (body[:5] != [r'\left', r'\{', r'\left', '(', r'\begin{matrix}']
            or body[-5:] != [r'\end{matrix}', r'\right', ')', r'\middle', '|']):
        return False
    closings = [i for i in range(index + 1, len(stream))
                if stream[i]['token'] == r'\end{matrix}'
                and stream[i]['depth'] == 0 and stream[i]['environments'] == ['matrix']]
    return bool(closings and [part['token'] for part in stream[closings[0]+1:closings[0]+3]]
                == [r'\right', r'\}'])


def usage(source: str, stream: list[dict[str, Any]], index: int, kind: str):
    node = stream[index]
    depth = 1 if kind in {'arrow-label-prefix',COMPONENT_USAGE} else 0
    if (node['depth'] != depth or index == 0 or index + 1 >= len(stream)
            or set(node['environments']) - MATH_ENVIRONMENTS):
        return None
    before, after = stream[index - 1], stream[index + 1]
    after_end = after['end']
    if kind == 'quad-connector':
        valid = before['token'] == after['token'] == r'\quad'
    elif kind == 'matrix-condition':
        valid = (before['token'] == after['token'] == '&'
                 and node['environments'] and node['environments'][-1] == 'matrix')
    elif kind == 'set-description':
        valid = (before['token'] == r'\{' and re.fullmatch(r'[A-Z]', after['token'])
                 and any(n['token'] == r'\}' and n['depth'] == 0 for n in stream[index + 2:]))
    elif kind == 'root-phrase':
        valid = (not node['environments']
                 and before['token'] not in {'$', r'\[', r'\(', r'\begin{matrix}', r'\end{matrix}', '&'}
                 and after['token'] not in {'$', r'\]', r'\)', r'\begin{matrix}', r'\end{matrix}', '&'})
    elif kind == 'root-condition':
        tail = [part['token'] for part in stream[index + 1:]]
        valid = (not node['environments'] and _condition_operand_end(before)
                 and _condition_math_context(source, stream)
                 and (_condition_relation_object(stream, index)
                      or tail in [['$'], ['$', '$'], [r'\]'], [r'\)']]))
    elif kind == 'matrix-row-condition':
        starts = [i for i, part in enumerate(stream[:index])
                  if part['depth'] == 0 and (part['token'] == r'\begin{matrix}'
                      or part['token'] == r'\\' and part['environments'] == ['matrix'])]
        row = stream[starts[-1] + 1:index] if starts else []
        valid = (node['environments'] == ['matrix'] and _condition_operand_end(before)
                 and _condition_math_context(source, stream)
                 and _condition_matrix_root(stream, index) and bool(row)
                 and not any(part['token'] == '&' and part['depth'] == 0 for part in row)
                 and (after['token'] in {r'\\', r'\end{matrix}'}
                      or _condition_relation_object(stream, index)))
    elif kind == 'root-hyphen-phrase':
        valid = (not node['environments'] and _condition_math_context(source, stream)
                 and re.fullmatch(r'[A-Z]', before['token']) is not None
                 and re.fullmatch(r'[A-Z]', after['token']) is not None
                 and before['end'] == node['start'] and node['end'] == after['start']
                 and node.get('value', '').startswith('-')
                 and not node['value'].startswith('--'))
    elif kind == 'matrix-prefix-condition':
        valid = (before['token'] == '&' and node['environments']
                 and node['environments'][-1] == 'matrix'
                 and after['token'] not in {'&', r'\\', r'\end{matrix}'})
    elif kind == 'arrow-label-prefix':
        valid = (index >= 2 and before['token'] == '{' and before['depth'] == 0
                 and stream[index - 2]['token'] == r'\xrightarrow'
                 and stream[index - 2]['depth'] == 0
                 and after['token'] != '}')
    elif kind in MATRIX_ROW_USAGES:
        valid = (node['environments'] == ['matrix'] and before['depth'] == 0
                 and before['token'] in {r'\begin{matrix}', r'\\'}
                 and _description_matrix_root(stream, index))
        row_end = after
        if valid and kind == 'matrix-row-prefix':
            atoms = stream[index+1:index+5]
            valid = (len(atoms) == 4 and index+5 < len(stream)
                     and source[atoms[0]['start']:atoms[-1]['end']]
                         == r'\mathcal{' + atoms[2]['token'] + '}'
                     and re.fullmatch(r'[A-Z]', atoms[2]['token']) is not None
                     and [part['token'] for part in atoms] == [r'\mathcal', '{', atoms[2]['token'], '}'])
            if valid:
                row_end = stream[index+5]
        if valid:
            valid = (row_end['depth'] == 0 and row_end['environments'] == ['matrix']
                     and row_end['token'] in {r'\\', r'\end{matrix}'})
            after_end = row_end['end']
    elif kind == 'numeric-isomorphism-suffix':
        previous = stream[index-3:index]
        valid = (not node['environments'] and index >= 3
                 and [part['token'] for part in previous] == [r'\Big', '/', '2']
                 and all(part['depth'] == 0 and not part['environments'] for part in previous)
                 and before['end'] == node['start']
                 and node.get('value', '').startswith('-')
                 and after['token'] == '=' and after['depth'] == 0 and not after['environments'])
    elif kind == COMPONENT_USAGE:
        openings = [i for i,n in enumerate(stream[:index]) if n['token']=='{' and n['depth']==0]
        opening = openings[-1] if openings else -1
        valid = (not node['environments'] and opening >= 3
                 and [n['token'] for n in stream[opening-3:opening]] == [r'\bigcup',r'\nolimits','_']
                 and index > opening+1 and after['token'] == r'\dim' and after['depth'] == 1
                 and not any(n['token'] in {'}',']'} and n['depth']==1
                             for n in stream[opening+1:index])
                 and any(n['token']==r'\subset' for n in stream[opening+1:index])
                 and all(not n['token'].startswith('\\') or
                         COMMAND.match(n['token'])[0] in {r'\subset',r'\cap'}
                         for n in stream[opening+1:index])
                 and any(n['token']=='}' and n['depth']==1 for n in stream[index+1:]))
    else:
        return None
    if not valid:
        return None
    return {'before': source[before['start']:node['start']],
            'after': source[node['end']:after_end], 'environments': node['environments']}


def find_slots(source: str, rules: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    stream = nodes(source)
    if not _known_environments(stream):
        return []
    accepted = []
    for index, node in enumerate(stream):
        if node.get('command') != 'text':
            continue
        for key, rule in rules.items():
            if node['value'] != rule['literal'] or node['command'] != rule['command']:
                continue
            witness = usage(source, stream, index, rule['usage'])
            if witness is not None and rule.get('slot_schema_version') == 3:
                start = node['parameter_start']
                for ordinal,leaf in enumerate(rule['components'],1):
                    end = start+len(leaf)
                    accepted.append({**node,'parameter_start':start,'parameter_end':end,'value':leaf,
                        'policy_entry':key,'usage':rule['usage'],'usage_source':witness,
                        'parameter_components':dict(parameter_source=node['value'],
                            parameter_byte_span=dict(start=len(source[:node['parameter_start']].encode()),
                                                     end=len(source[:node['parameter_end']].encode())),
                            component_index=ordinal,component_count=2,separator=rule['separator'])})
                    start = end+len(rule['separator'])
            elif witness is not None and plain_text(node['value']):
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
    version = 3 if any('parameter_components' in s for r in regions for s in r['slots']) else 2
    unit.update(schema_version=version, risk_level='R3', math_text_regions=regions)
    unit['source_math_skeleton_hash'] = digest(skeleton(unit))
    return unit


def validate_regions(unit: dict[str, Any]) -> list[str]:
    if type(unit.get('schema_version')) is not int or unit['schema_version'] not in {1, 2, 3}:
        return ['unsupported mathematical unit schema version']
    if unit['schema_version'] == 1:
        return ['unit-v1 cannot contain split math tokens'] if any(
            name.startswith('MATHSEG_') for name in unit.get('placeholders', {})) else []
    try:
        from .schema_validation import validate_named_schema
        regions = unit['math_text_regions']
        version = unit['schema_version']
        schema = 'math-text-components.schema.json' if version == 3 else 'math-text-regions.schema.json'
        errors = validate_named_schema(regions, schema, 'math_text_regions')
        if errors:
            return errors
        if not regions or unit['risk_level'] != 'R3':
            raise ValueError('unit-v2 requires nonempty math regions and R3 risk')
        if version == 3 and not any('parameter_components' in s for r in regions for s in r['slots']):
            raise ValueError('unit-v3 requires at least one complete composite text parameter')
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
            rebuilt, protected, coverage = '', '', {}
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
                    node_index,node = _slot_node(source,stream,slot,version)
                    if 'parameter_components' in slot:
                        component = slot['parameter_components'];key = node['parameter_start']
                        ordinal = component['component_index'];seen = coverage.setdefault(key,[])
                        if ordinal in seen:
                            raise ValueError('composite parameter repeats a text component')
                        seen.append(ordinal)
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
                    actual = usage(source, stream, node_index, witness['usage'])
                    if actual is None or actual != witness['usage_source']:
                        raise ValueError('math text syntax witness differs from original structure')
                    rebuilt += slot['source']; protected += slot['source']
            if any(ordinals != [1,2] for ordinals in coverage.values()):
                raise ValueError('composite parameter lacks its complete ordered pure leaves')
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
    if errors or unit.get('schema_version') not in {2,3}:
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
                index,_ = _slot_node(region['source'],original_nodes,slot,unit['schema_version'])
                identities.setdefault(index,[]).append(slot)
            before = '<' + region['pieces'][0]['placeholder'] + '>'
            after = '<' + region['pieces'][-1]['placeholder'] + '>'
            start = translation.index(before)
            end = translation.index(after, start) + len(after)
            actual = restore(unit, translation[start:end])

            def projection(source):
                stream, pieces, cursor = nodes(source), [], 0
                if len(stream) != len(original_nodes):
                    raise ValueError('translated mathematical node sequence differs')
                for index, slots in identities.items():
                    node = stream[index]
                    first = slots[0]
                    component = 'parameter_components' in first
                    leaves = node.get('value','').split(COMPONENT_SEPARATOR) if component else [node.get('value','')]
                    if (node.get('command') != first['command'] or len(leaves) != len(slots)
                            or any(not plain_text(leaf) for leaf in leaves)
                            or usage(source, stream, index, first['classification_witness']['usage']) is None):
                        raise ValueError('translated slot lost its original command/role')
                    pieces.append({'locked':source[cursor:node['parameter_start']]})
                    for ordinal,slot in enumerate(slots):
                        if ordinal:
                            pieces.append({'locked':COMPONENT_SEPARATOR})
                        pieces.append({'slot':slot['slot_id'],'command':slot['command'],
                                       'usage':slot['classification_witness']['usage']})
                    cursor = node['parameter_end']
                pieces.append({'locked': source[cursor:]})
                return pieces

            if projection(actual) != projection(region['source']):
                raise ValueError('translated mathematical skeleton differs outside typed text leaves')
        return []
    except (ValueError, KeyError, IndexError, StopIteration) as exc:
        return ['invalid typed math translation: ' + str(exc)]


def _slot_node(source, stream, slot, version):
    component = slot.get('parameter_components')
    span = component['parameter_byte_span'] if component else slot['slot_byte_span']
    matches = [(i,n) for i,n in enumerate(stream) if n.get('command') == slot['command']
        and len(source[:n['parameter_start']].encode()) == span['start']
        and len(source[:n['parameter_end']].encode()) == span['end']]
    if len(matches) != 1:
        raise ValueError('math slot lacks its complete real parent parameter')
    index,node = matches[0]
    if not component:
        if node['value'] != slot['source']:
            raise ValueError('math slot is not a complete real text command parameter')
        if (slot['classification_witness']['usage'] == 'numeric-isomorphism-suffix'
                and slot['source'] != '-isomorphism'):
            raise ValueError('numeric suffix requires its exact complete isomorphism parameter')
    else:
        if (version != 3 or node['value'] != component['parameter_source']
                or component['parameter_source'] != COMPONENT_LITERAL
                or component['component_count'] != 2 or component['separator'] != COMPONENT_SEPARATOR
                or slot['classification_witness']['usage'] != COMPONENT_USAGE):
            raise ValueError('unsupported composite parent parameter or version')
        leaves = node['value'].split(COMPONENT_SEPARATOR)
        ordinal = component['component_index']-1
        if len(leaves) != 2 or ordinal not in {0,1} or any(not plain_text(v) for v in leaves):
            raise ValueError('invalid complete composite text leaves')
        start = span['start'] + (len((leaves[0]+COMPONENT_SEPARATOR).encode()) if ordinal else 0)
        if slot['source'] != leaves[ordinal] or slot['slot_byte_span'] != dict(start=start,end=start+len(leaves[ordinal].encode())):
            raise ValueError('composite pure leaf differs from its real parent source span')
    return index,node
