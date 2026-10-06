from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from .records import (RecordError, load_jsonl, load_upstream_commit, placeholder_names,
                      sha256_value, stamp_unit_hashes, validate_tex_controls)

LABEL = re.compile(r"\\label\{([^{}]+)\}")
TAG_UNIT = re.compile(r"^tag:([0-9A-Z]+)(?::(.+))?$")
LABEL_UNIT = re.compile(r"^label:(.+):([^:]+)$")
STATEMENTS = {'definition', 'lemma', 'proposition', 'theorem', 'corollary', 'remark',
              'remarks', 'example', 'exercise', 'situation'}
FOOTNOTE = re.compile(r"^\\footnote\{See Remark (\\ref\{[^{}]+\})\.\}$")
STATEMENT_NAMES = '|'.join(sorted(STATEMENTS))
NAMED_BEGIN = re.compile(rf'\\begin\{{(?:{STATEMENT_NAMES})\}}\s*\[')
NAMED_OPEN = re.compile(rf'\s*\\begin\{{(?:{STATEMENT_NAMES})\}}\s*\[')
PLAIN_TITLE = r"[A-Za-z]+(?:[-'][A-Za-z]+)*(?:[ \t]+[A-Za-z]+(?:[-'][A-Za-z]+)*)*"
TITLE_END = re.compile(r'\]\s*\\label\{([A-Za-z0-9._:+-]+)\}\s*')


def _named_title_label(unit: dict[str, Any]) -> str | None:
    """Only a leading, validated named-argument closure can own a label."""
    names = sorted({name for name in [*unit['placeholders'], *placeholder_names(unit['source_text'])]
                    if name.startswith(('ENVARGEND_', 'OWNARGEND_'))})
    opening = NAMED_OPEN.fullmatch(unit['render']['prefix'])
    # Earlier extraction already gave some headings their own title unit. Its
    # suffix closes the argument and owns the label; no body token is needed.
    if opening and unit['node_kind'] == 'environment_title' and not names:
        ending = TITLE_END.fullmatch(unit['render']['suffix'])
        if ending is None or not unit['source_text'].strip() or validate_tex_controls(unit, {'translation': unit['source_text']}):
            raise RecordError(f"{unit['unit_id']}: invalid separate named environment title boundary")
        return ending.group(1)
    if not opening and not names:
        return None
    if not opening or unit['node_kind'] not in STATEMENTS or len(names) != 1:
        raise RecordError(f"{unit['unit_id']}: invalid named environment title boundary")
    name = names[0]
    if not re.fullmatch(r'(?:ENVARGEND|OWNARGEND)_[0-9]{4}', name) or name not in unit['placeholders']:
        raise RecordError(f"{unit['unit_id']}: invalid named environment title token")
    title_pattern = r'[\s\S]+?' if name.startswith('OWNARGEND_') else PLAIN_TITLE
    head = re.match(rf'({title_pattern})<{name}>', unit['source_text'])
    ending = TITLE_END.fullmatch(unit['placeholders'][name])
    if (head is None or ending is None or placeholder_names(unit['source_text']).count(name) != 1
            or not head[1].strip()
            or validate_tex_controls(unit, {'translation': unit['source_text']})):
        raise RecordError(f"{unit['unit_id']}: missing, moved or malformed named environment title closure")
    return ending.group(1)


def environment_title_errors(unit: dict[str, Any]) -> list[str]:
    try:
        if _named_title_label(unit) is not None:
            return []
    except RecordError as exc:
        return [str(exc)]
    return [f"{unit['unit_id']}: named environment title is hidden in render.prefix"
            for _ in NAMED_BEGIN.finditer(unit['render']['prefix'])]


def expose_environment_title(unit: dict[str, Any]) -> dict[str, Any]:
    """Expose a simple English title without translating or changing source TeX.

    This helper accepts one complete statement wrapper, its simple title and
    adjacent own label. Complex TeX titles need an explicit extraction task.
    """
    unit = copy.deepcopy(unit)
    if _named_title_label(unit) is not None:
        return unit
    prefix = unit['render']['prefix']
    opening = NAMED_OPEN.match(prefix)
    if opening is None or unit['node_kind'] not in STATEMENTS:
        raise RecordError(f"{unit['unit_id']}: named title needs an explicit extraction task")
    match = re.fullmatch(rf'({PLAIN_TITLE})(\]\s*\\label\{{[A-Za-z0-9._:+-]+\}}\s*)', prefix[opening.end():])
    if match is None:
        raise RecordError(f"{unit['unit_id']}: complex named title needs an explicit extraction task")
    name = 'ENVARGEND_0001'
    unit['render']['prefix'] = prefix[:opening.end()]
    unit['placeholders'][name] = match.group(2)
    unit['source_text'] = match.group(1) + f'<{name}>' + unit['source_text']
    _named_title_label(unit)
    return stamp_unit_hashes(unit)


def load_tags(path: Path) -> dict[str, str]:
    result = {}
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        parts = line.split(',')
        if len(parts) != 2 or not re.fullmatch(r'[0-9A-Z]+', parts[0].strip()):
            raise RecordError(f'{path}:{number}: malformed permanent Tag mapping')
        tag, label = (part.strip() for part in parts)
        if label in result and result[label] != tag:
            raise RecordError(f'{path}:{number}: conflicting permanent Tag mapping')
        result[label] = tag
    if not result:
        raise RecordError(f'{path}: no permanent Tags')
    return result


def _own_tag(unit: dict[str, Any], tags: dict[str, str]) -> str | None:
    # Only labels owned by this node's wrapper may give it an identity. Labels
    # nested in diagrams/equations are separate children, never statement Tags.
    wrapper = unit['render']['prefix'] + unit['render']['suffix']
    labels = LABEL.findall(wrapper)
    named_label = _named_title_label(unit)
    if named_label is not None and named_label not in labels:
        labels.append(named_label)
    if not labels:
        return None
    resolved = set()
    for label in labels:
        tag = tags.get(label, tags.get(f"{unit['chapter']}-{label}"))
        if tag is None:
            raise RecordError(f"{unit['unit_id']}: own label {label!r} has no permanent Tag")
        resolved.add(tag)
    if len(resolved) != 1:
        raise RecordError(f"{unit['unit_id']}: own wrapper contains multiple permanent Tags")
    return resolved.pop()


def permanent_tag_mapping(units: list[dict[str, Any]], tags: dict[str, str]) -> dict[str, str]:
    mapping = {}
    owner_tag = owner_kind = owner_scope = None
    statement_open = in_proof = False
    for unit in units:
        old_id = unit['unit_id']
        match = TAG_UNIT.fullmatch(old_id)
        legacy = LABEL_UNIT.fullmatch(old_id)
        if match is None and legacy is None:
            raise RecordError(f'{old_id}: unsupported persistent unit coordinate')
        own_tag = _own_tag(unit, tags)
        tag = own_tag
        suffix = match.group(2) if match else legacy.group(2)
        if legacy:
            tag = tag or tags.get(legacy.group(1)) or tags.get(f"{unit['chapter']}-{legacy.group(1)}")
        statement_wrapper = re.search(r'\\begin\{(lemma|definition|proposition|theorem|corollary|remark|example|exercise|situation)\}', unit['render']['prefix'])
        if own_tag and (unit['node_kind'] in STATEMENTS or statement_wrapper):
            owner_tag = tag
            owner_scope = (unit['chapter'], unit['parent_tag'])
            owner_kind = statement_wrapper.group(1) if statement_wrapper else unit['node_kind']
            statement_open = f"\\end{{{owner_kind}}}" not in unit['render']['suffix']
            in_proof = False
        elif unit['node_kind'].endswith('_title') and unit['node_kind'] != 'environment_title':
            owner_tag = owner_kind = owner_scope = None
            statement_open = in_proof = False
        # The wrapper, rather than the prose node kind, defines proof scope:
        # lists, displays and paragraphs can start, continue or close a proof.
        if r'\begin{proof}' in unit['render']['prefix']:
            if owner_tag is None:
                raise RecordError(f'{old_id}: proof has no adjacent labelled statement owner')
            in_proof = True
        if in_proof:
            if owner_scope[0] != unit['chapter'] or (owner_scope[1] != unit['parent_tag'] and own_tag != unit['parent_tag']):
                raise RecordError(f'{old_id}: proof crosses its owner chapter/parent Tag')
            tag = own_tag or owner_tag
        elif unit['node_kind'] == 'paragraph' and not statement_open:
            owner_tag = owner_kind = owner_scope = None
        elif statement_open:
            if owner_scope[0] != unit['chapter'] or (owner_scope[1] != unit['parent_tag'] and own_tag != unit['parent_tag']):
                raise RecordError(f'{old_id}: statement child crosses its owner chapter/parent Tag')
            tag = own_tag or owner_tag
        if r'\end{proof}' in unit['render']['suffix']:
            in_proof = False
        if statement_open and owner_kind and f"\\end{{{owner_kind}}}" in unit['render']['suffix']:
            statement_open = False
        mapping[old_id] = (f'tag:{tag}' + (f':{suffix}' if suffix else '')) if tag else old_id
    if len(set(mapping.values())) != len(mapping):
        raise RecordError('permanent-Tag migration creates duplicate unit IDs')
    return mapping


def hidden_footnote_errors(unit: dict[str, Any]) -> list[str]:
    return [f"{unit['unit_id']}: {name}: footnote natural language is hidden in a locked placeholder"
            for name, value in unit['placeholders'].items()
            if re.search(r'\\footnote\s*\{.+', value, re.S)]


def expand_fixed_footnotes(unit: dict[str, Any], candidate: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Expose only the two fixed 'See Remark' footnotes; never freely translate."""
    unit, candidate = copy.deepcopy(unit), copy.deepcopy(candidate)
    placeholders = unit['placeholders']
    for name, value in list(placeholders.items()):
        if not re.search(r'\\footnote\s*\{.+', value, re.S):
            continue
        match = FOOTNOTE.fullmatch(value)
        if match is None:
            raise RecordError(f"{unit['unit_id']}: footnote needs an explicit translation task")
        new_names = []
        for kind, tex in [('FOOTNOTEOPEN', r'\footnote{'), ('REF', match.group(1)), ('FOOTNOTECLOSE', '}')]:
            index = 1
            while f'{kind}_{index:04d}' in placeholders:
                index += 1
            new_name = f'{kind}_{index:04d}'
            placeholders[new_name] = tex
            new_names.append(new_name)
        opening, reference, closing = (f'<{n}>' for n in new_names)
        unit['source_text'] = unit['source_text'].replace(f'<{name}>', opening + 'See Remark ' + reference + '.' + closing)
        candidate['translation'] = candidate['translation'].replace(f'<{name}>', opening + '见注 ' + reference + '.' + closing)
        del placeholders[name]
    return stamp_unit_hashes(unit), candidate


def protect_fragments(unit: dict[str, Any], candidate: dict[str, Any], fragments: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply explicit, reviewable source/target span annotations, not guesses.

    Positions refer to the original placeholder text. Each protected source
    fragment is retained verbatim; a removed candidate fragment may contain only
    structural TeX/math, never natural-language text that needs translation.
    The derivation replay independently enforces source and prose preservation.
    """
    from .records import restore_placeholders
    unit, candidate = copy.deepcopy(unit), copy.deepcopy(candidate)
    source, target = unit['source_text'], candidate['translation']
    replacements = []
    for fragment in fragments:
        ss, se = fragment['source_start'], fragment['source_end']
        ts, te = fragment['target_start'], fragment['target_end']
        if not all(isinstance(n, int) and not isinstance(n, bool) for n in (ss, se, ts, te)) or not 0 <= ss < se <= len(source) or not 0 <= ts <= te <= len(target):
            raise RecordError('invalid protection span coordinates')
        if re.search(r'[\u3400-\u9fff]', target[ts:te]):
            raise RecordError('protection cannot hide translated natural language')
        if source[ss:se] != fragment['source_literal'] or target[ts:te] != fragment['target_literal']:
            raise RecordError('protection span text differs from declared input')
        name = fragment['placeholder']
        if not re.fullmatch(r'[A-Z][A-Z0-9]*_[0-9]{4}', name) or name in unit['placeholders']:
            raise RecordError('protection placeholder must have a new unique name')
        unit['placeholders'][name] = restore_placeholders(unit, source[ss:se])
        replacements.append((ss, se, ts, te, f'<{name}>'))
    for axis in [(0, 1), (2, 3)]:
        ordered = sorted(replacements, key=lambda span: span[axis[0]])
        if any(left[axis[1]] > right[axis[0]] for left, right in zip(ordered, ordered[1:])):
            raise RecordError('protection spans overlap')
    for ss, se, _, _, token in sorted(replacements, reverse=True):
        source = source[:ss] + token + source[se:]
    for _, _, ts, te, token in sorted(replacements, key=lambda span: span[2], reverse=True):
        target = target[:ts] + token + target[te:]
    unit['source_text'], candidate['translation'] = source, target
    used = set(placeholder_names(source))
    unit['placeholders'] = {name: value for name, value in unit['placeholders'].items() if name in used}
    if placeholder_names(source) != placeholder_names(target):
        raise RecordError('protection changed source/target placeholder order')
    return stamp_unit_hashes(unit), candidate


def require_audit_output(root: Path, output: Path) -> None:
    root = root.resolve()
    resolved = output.resolve()
    if resolved.is_relative_to(root) and not resolved.is_relative_to(root / 'build'):
        raise RecordError('audit output inside the repository must use the ignored build directory')


def audit_repository_source(root: Path, tags_path: Path) -> tuple[dict[str, Any], list[str]]:
    tags = load_tags(tags_path)
    source_commit = load_upstream_commit(root / 'upstream.lock')
    errors, proposals = [], []
    statements = raw_nodes = hidden = hidden_titles = 0
    for path in sorted((root / 'translation-data/units').glob('*.jsonl')):
        units = load_jsonl(path)
        for unit in units:
            if unit['source_commit'] != source_commit:
                errors.append(f"{path}: {unit['unit_id']}: source commit differs from upstream.lock")
        try:
            mapping = permanent_tag_mapping(units, tags)
        except RecordError as exc:
            errors.append(str(exc))
            mapping = {unit['unit_id']: unit['unit_id'] for unit in units}
        changes = {old: new for old, new in mapping.items() if old != new}
        for unit in units:
            if unit['unit_id'] in changes:
                errors.append(f"{path}: wrong permanent Tag: {unit['unit_id']} -> {changes[unit['unit_id']]}")
                if unit['node_kind'] in STATEMENTS and _own_tag(unit, tags):
                    statements += 1
            footnotes = hidden_footnote_errors(unit)
            hidden += len(footnotes)
            errors.extend(footnotes)
            title_errors = environment_title_errors(unit)
            hidden_titles += len(title_errors)
            errors.extend(title_errors)
        for candidate_path in sorted((root / 'translation-data/candidates').glob(f'*/{path.name}')):
            candidates = {c['unit_id']: c for c in load_jsonl(candidate_path)}
            for unit in units:
                candidate = candidates.get(unit['unit_id'])
                if candidate is None:
                    errors.append(f'{candidate_path}: incomplete unit coverage')
                    continue
                controls = validate_tex_controls(unit, candidate)
                if controls:
                    raw_nodes += 1
                    errors.extend(f'{path.name}: {error}' for error in controls)
        if changes:
            proposals.append({'unit_path': path.relative_to(root).as_posix(), 'input_hash': sha256_value(path.read_text()), 'unit_id_map': mapping})
    return {'schema_version': 1, 'source_commit': source_commit,
            'wrong_statement_tags': statements, 'unprotected_node_pairs': raw_nodes,
            'hidden_footnotes': hidden, 'hidden_environment_titles': hidden_titles,
            'coordinate_proposals': proposals}, errors
