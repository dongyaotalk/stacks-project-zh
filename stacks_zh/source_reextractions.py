"""Locked-Git proof selection, bounded extraction and independent coverage audit.

This is deliberately not a general TeX parser. Unsupported syntax is evidence
of missing coverage, never a successful comparison or permission to guess.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .model_corrections import _first_addition_is_immutable, _safe_path
from .records import RecordError, load_jsonl, load_upstream_commit, restore_placeholders, stamp_unit_hashes
from .schema_validation import validate_named_schema
from .source_integrity import STATEMENTS, permanent_tag_mapping

ID = r'[A-Za-z0-9][A-Za-z0-9._-]*'
LABEL = re.compile(r'\\label\{([A-Za-z0-9._:+-]+)\}')
ENV = re.compile(r'\\(begin|end)\{([A-Za-z][A-Za-z0-9*_-]*)\}')
UNSAFE_COMMANDS = {'def', 'gdef', 'edef', 'xdef', 'newcommand', 'renewcommand', 'input', 'include', 'catcode', 'verb'}


class UnsupportedSource(RecordError):
    """A source construct cannot be verified by this bounded parser."""


def byte_hash(value: str | bytes) -> str:
    return 'sha256:' + hashlib.sha256(value.encode('utf-8') if isinstance(value, str) else value).hexdigest()


def source_tex(unit: dict[str, Any]) -> str:
    return unit['render']['prefix'] + restore_placeholders(unit, unit['source_text']) + unit['render']['suffix']


def _git_bytes(harvest: Path, commit: str, path: str) -> bytes:
    if not re.fullmatch(r'[0-9a-f]{40}', commit) or not re.fullmatch(r'(?:[A-Za-z0-9_-]+\.tex|tags/tags)', path):
        raise RecordError('invalid locked English Git selector path/commit')
    result = subprocess.run(['git', '-C', str(harvest), 'show', f'{commit}:{path}'], capture_output=True)
    if result.returncode:
        raise RecordError(f'locked English Git object unavailable: {commit}:{path}')
    return result.stdout


class LockedEnglish:
    def __init__(self, root: Path, harvest: Path | None = None):
        self.harvest = harvest if harvest is not None else root.resolve().parent / 'stacks-project'
        self.commit = load_upstream_commit(root / 'upstream.lock')
        self.tags: dict[str, str] = {}
        for line in _git_bytes(self.harvest, self.commit, 'tags/tags').decode('utf-8').splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            parts = line.split(',')
            if len(parts) != 2 or not re.fullmatch(r'[0-9A-Z]+', parts[0].strip()):
                raise RecordError('invalid locked English permanent Tags')
            tag, label = (part.strip() for part in parts)
            if label in self.tags:
                raise RecordError('duplicate locked English permanent label')
            self.tags[label] = tag
        if not self.tags:
            raise RecordError('empty locked English permanent Tags')
        self.documents: dict[str, dict[str, Any]] = {}

    def document(self, chapter: str) -> dict[str, Any]:
        if chapter not in self.documents:
            text = _git_bytes(self.harvest, self.commit, chapter + '.tex').decode('utf-8')
            self.documents[chapter] = _proof_index(text)
        return self.documents[chapter]

    def select(self, selector: dict[str, Any]) -> str:
        chapter = selector['file'][:-4]
        label = selector['statement_label']
        if self.tags.get(chapter + '-' + label) != selector['statement_tag']:
            raise RecordError('English selector statement Tag/label/chapter mismatch')
        proofs = self.document(chapter)['proofs']
        matches = [proof for proof in proofs if proof['label'] == label and proof['proof_index'] == selector['proof_index']]
        if len(matches) != 1:
            raise UnsupportedSource('English selector has no unique adjacent proof')
        proof = matches[0]
        if proof['unsupported']:
            raise UnsupportedSource(proof['unsupported'])
        return proof['tex']


def _tokens(text: str, allow_footer: bool = False):
    """Lex data without expanding macros; comments and math cannot own labels."""
    i = 0
    while i < len(text):
        start = i
        char = text[i]
        if char == '%':
            end = text.find('\n', i)
            # A TeX comment consumes its end-of-line, not an inter-word space.
            i = len(text) if end < 0 else end + 1
            yield 'comment', start, i, text[start:i]
        elif char == '$' or text.startswith((r'\[', r'\('), i):
            opening = text[i:i + 2] if text[i:i + 2] in {'$$', r'\[', r'\('} else '$'
            closing = {'$$': '$$', '$': '$', r'\[': r'\]', r'\(': r'\)'}[opening]
            i += len(opening)
            while i < len(text):
                if text.startswith(closing, i):
                    i += len(closing)
                    break
                if text[i] == '%':
                    newline = text.find('\n', i)
                    if newline < 0:
                        raise UnsupportedSource('unclosed math after comment')
                    i = newline
                elif text[i] == '\\':
                    i += 2
                elif closing == '$' and text.startswith('$$', i):
                    raise UnsupportedSource('ambiguous dollar math')
                else:
                    i += 1
            else:
                raise UnsupportedSource('unclosed math')
            yield 'math', start, i, text[start:i]
        elif char == '\\':
            environment = ENV.match(text, i)
            reference = re.match(r'\\(?:label|ref|eqref|pageref|cite)\{[^{}\n]+\}', text[i:])
            command = re.match(r'\\(?:[A-Za-z@]+|[^\n])', text[i:])
            if environment:
                i = environment.end()
                yield 'environment', start, i, environment.group()
            elif reference:
                i += len(reference.group())
                yield 'reference', start, i, reference.group()
            elif command:
                i += len(command.group())
                if command.group()[1:] in UNSAFE_COMMANDS:
                    if not (allow_footer and command.group() == r'\input' and text[i:].startswith('{chapters}')):
                        raise UnsupportedSource(f'unsupported source command {command.group()}')
                yield 'command', start, i, command.group()
            else:
                raise UnsupportedSource('incomplete TeX command')
        elif char in '{}&#_^~':
            i += 1
            yield 'structure', start, i, char
        else:
            i += 1
            while i < len(text) and text[i] not in '%$\\{}&#_^~':
                i += 1
            yield 'text', start, i, text[start:i]


def _without_comments(text: str) -> str:
    return ''.join(value for kind, _, _, value in _tokens(text) if kind != 'comment')


def _proof_index(text: str) -> dict[str, Any]:
    # Ignore macro definitions in the preamble. The document boundary must be
    # a complete line, not a string inside a definition or a commented example.
    starts = list(re.finditer(r'(?m)^\\begin\{document\}\s*$', text))
    if len(starts) != 1:
        raise UnsupportedSource('English document has no unique literal document opening')
    offset = starts[0].start()
    preamble = text[:offset].replace(r'\input{preamble}', '')
    if _without_comments(preamble).strip():
        raise UnsupportedSource('unsupported English preamble/document boundary')
    body = text[offset:]
    stack, blocks, brace_depth = [], [], 0
    for kind, start, end, value in _tokens(body, allow_footer=True):
        if value == r'\input' and (len(stack) != 1 or stack[0][0] != 'document'):
            raise UnsupportedSource('footer input is nested in source content')
        if kind == 'structure' and value in '{}':
            brace_depth += 1 if value == '{' else -1
            if brace_depth < 0:
                raise UnsupportedSource('unbalanced English text group')
        if kind != 'environment':
            continue
        action, name = ENV.fullmatch(value).groups()
        if name in {*STATEMENTS, 'proof', 'document'} and brace_depth:
            raise UnsupportedSource('statement/proof environment nested in a text argument or group')
        if name in {'verbatim', 'lstlisting'}:
            raise UnsupportedSource('literal environment requires a dedicated parser')
        if action == 'begin':
            stack.append((name, start, end))
        else:
            if not stack or stack[-1][0] != name:
                raise UnsupportedSource('unbalanced English environment')
            _, opening, header_end = stack.pop()
            if len(stack) == 1 and stack[0][0] == 'document' and name in {*STATEMENTS, 'proof'}:
                blocks.append({'kind': name, 'start': opening, 'end': end, 'header_end': header_end})
    if stack or brace_depth:
        raise UnsupportedSource('unclosed English environment or text group')
    owner, previous_end, proof_index = None, 0, 0
    proofs, labels = [], set()
    for block in sorted(blocks, key=lambda row: row['start']):
        content = body[block['header_end']:block['end']]
        if block['kind'] != 'proof':
            header = _without_comments(content).lstrip()
            if header.startswith('['):
                # Only a simple title followed by the first own label is a
                # supported owner. Never use nested equation/body labels.
                title = re.match(r'\[[^\[\]{}\\$]*\]\s*', header)
                header = header[title.end():] if title else ''
            label = LABEL.match(header)
            owner = label.group(1) if label else None
            if owner in labels:
                raise UnsupportedSource('duplicate English statement label')
            if owner:
                labels.add(owner)
            proof_index = 0
        else:
            gap = _without_comments(body[previous_end:block['start']])
            if gap.strip():
                owner = None
            proof_index += 1
            fragment = body[block['start']:block['end']]
            proofs.append({'label': owner, 'proof_index': proof_index, 'tex': fragment,
                           'unsupported': '' if owner else 'proof has no supported adjacent labelled statement'})
        previous_end = block['end']
    return {'proofs': proofs}


def proof_groups(units: list[dict[str, Any]], tags: dict[str, str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Determine owners from complete frozen wrapper chains, never current IDs."""
    mapping = permanent_tag_mapping(units, tags)
    groups, errors, active = [], [], None
    owner = None
    statement_kind = None
    proof_index = 0
    assigned = set()
    for unit in units:
        prefix, suffix = unit['render']['prefix'], unit['render']['suffix']
        statement = re.search(r'\\begin\{(' + '|'.join(sorted(STATEMENTS)) + r')\}', prefix)
        if statement:
            statement_kind = statement.group(1)
            wrapper = prefix + suffix
            if prefix.rstrip().endswith('['):
                wrapper += ''.join(value for name, value in unit['placeholders'].items() if name.startswith(('ENVARGEND_', 'OWNARGEND_')))
            labels = LABEL.findall(wrapper)
            if len(labels) != 1:
                owner = None
            else:
                label = labels[0]
                qualified = label if label.startswith(unit['chapter'] + '-') else unit['chapter'] + '-' + label
                tag = tags.get(qualified)
                owner = {'file': unit['chapter'] + '.tex', 'statement_label': qualified[len(unit['chapter']) + 1:], 'statement_tag': tag} if tag else None
            proof_index = 0
        elif unit['node_kind'].endswith('_title') and unit['node_kind'] != 'environment_title':
            owner = None
        elif unit['node_kind'] == 'paragraph' and statement_kind is None and active is None and r'\begin{proof}' not in prefix:
            owner = None
        if r'\begin{proof}' in prefix:
            if active is not None:
                errors.append(f"{unit['unit_id']}: nested current proof group")
            proof_index += 1
            active = {'selector': {**owner, 'kind': 'proof', 'proof_index': proof_index} if owner else None,
                      'units': [], 'mapped_ids': [], 'tex': ''}
        if active is not None:
            active['units'].append(unit)
            active['mapped_ids'].append(mapping[unit['unit_id']])
            active['tex'] += source_tex(unit)
            assigned.add(unit['unit_id'])
            if r'\end{proof}' in suffix:
                groups.append(active)
                active = None
        if statement_kind and f'\\end{{{statement_kind}}}' in suffix:
            statement_kind = None
    if active is not None:
        groups.append(active)
        errors.append('unclosed current proof group')
    for unit in units:
        if (unit['node_kind'] == 'proof' or ':proof' in unit['unit_id']) and unit['unit_id'] not in assigned:
            errors.append(f"{unit['unit_id']}: unassigned declared proof node")
    return groups, errors


def extract_plain_proof(old_unit: dict[str, Any], fragment: str, new_id: str | None = None) -> dict[str, Any]:
    """Extract one complete untitled proof, natural text and inline $...$ only."""
    opening, closing = r'\begin{proof}', r'\end{proof}'
    if not fragment.startswith(opening) or not fragment.endswith(closing):
        raise UnsupportedSource('helper requires one complete proof')
    body = fragment[len(opening):-len(closing)]
    if body.lstrip().startswith('['):
        raise UnsupportedSource('proof title requires a dedicated extraction task')
    placeholders, parts = {}, []
    for kind, _, _, value in _tokens(body):
        if kind == 'text':
            if '<' in value or '>' in value:
                raise UnsupportedSource('literal angle brackets need explicit extraction')
            parts.append(value)
        elif kind == 'math' and value.startswith('$') and not value.startswith('$$') and '%' not in value:
            name = f'MATH_{len(placeholders) + 1:04d}'
            placeholders[name] = value
            parts.append(f'<{name}>')
        else:
            raise UnsupportedSource(f'plain proof helper cannot extract {kind}: {value[:60]!r}')
    unit = copy.deepcopy(old_unit)
    unit.update(unit_id=new_id or old_unit['unit_id'], source_text=''.join(parts), placeholders=placeholders,
                render={'prefix': opening, 'suffix': closing})
    return stamp_unit_hashes(unit)


def load_source_reextractions(root: Path, harvest: Path | None = None) -> tuple[dict[str, dict[str, Any]], list[str]]:
    records, errors, english = {}, [], None
    for path in sorted((root / 'translation-data/source-reextractions').rglob('*.json')):
        try:
            _safe_path(root, path.relative_to(root).as_posix(), rf'translation-data/source-reextractions/{ID}\.json')
            record = json.loads(path.read_text(encoding='utf-8'))
            problems = validate_named_schema(record, 'source-reextraction.schema.json', str(path))
            for role in ('old_unit', 'new_unit'):
                problems.extend(validate_named_schema(record.get(role), 'unit.schema.json', f'{path}:{role}'))
            if problems:
                raise RecordError('\n'.join(problems))
            if '..' in path.stem or record['source_reextraction_id'] != path.stem:
                raise RecordError('source re-extraction filename/ID mismatch')
            _first_addition_is_immutable(root, path)
            if english is None:
                english = LockedEnglish(root, harvest)
            if record['source_commit'] != english.commit or any(record[role]['source_commit'] != english.commit for role in ('old_unit', 'new_unit')):
                raise RecordError('source re-extraction differs from locked source commit')
            selector = record['selector']
            if selector['file'] != record['old_unit']['chapter'] + '.tex' or selector['proof_index'] < 1:
                raise RecordError('source re-extraction has a wrong chapter/proof index')
            fragment = english.select(selector)
            if fragment != record['fragment'] or byte_hash(fragment) != record['fragment_hash']:
                raise RecordError('source re-extraction fragment differs from locked English Git bytes')
            for role in ('old', 'new'):
                unit = record[role + '_unit']
                if stamp_unit_hashes(unit) != unit or byte_hash(source_tex(unit)) != record[role + '_source_tex_hash']:
                    raise RecordError(f'{role} source unit/hash mismatch')
            if record['new_unit'] != extract_plain_proof(record['old_unit'], fragment, record['new_unit']['unit_id']):
                raise RecordError('new source differs from deterministic complete English proof extraction')
            if source_tex(record['new_unit']) != fragment:
                raise RecordError('new source TeX differs from locked English proof')
            records[path.stem] = {'record': record, 'tags': english.tags}
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f'{path}: {exc}')
    return records, errors


def validate_reextraction_operation(evidence: dict[str, Any], derivation: dict[str, Any], units: list[dict[str, Any]], old_unit: dict[str, Any], new_unit: dict[str, Any]) -> None:
    record = evidence['record']
    if (record['derivation_id'] != derivation['derivation_id'] or record['source_commit'] != derivation['source_commit']
            or record['old_unit'] != old_unit or record['new_unit'] != new_unit):
        raise RecordError('source re-extraction does not bind this exact input/output/derivation')
    groups, errors = proof_groups(units, evidence['tags'])
    matches = [group for group in groups if any(unit['unit_id'] == old_unit['unit_id'] for unit in group['units'])]
    if (errors or len(matches) != 1 or matches[0]['selector'] != record['selector']
            or [unit['unit_id'] for unit in matches[0]['units']] != [old_unit['unit_id']]):
        raise RecordError('source re-extraction proof ownership/full frozen input chain mismatch or unsupported split proof')
    if derivation['unit_id_map'] != permanent_tag_mapping(units, evidence['tags']):
        raise RecordError('source re-extraction requires complete permanent-Tag mapping')


def _comparison(tex: str) -> tuple[list[str], str]:
    formal, parts = [], []
    for kind, _, _, value in _tokens(tex):
        if kind == 'comment':
            continue
        if kind == 'text':
            parts.append(re.sub(r'\s+', ' ', value))
        else:
            formal.append(value)
            parts.append(f'<NODE:{len(formal)}>')
    return formal, ''.join(parts).strip()


def audit_repository_proofs(root: Path, harvest: Path | None = None) -> tuple[dict[str, Any], list[str]]:
    english = LockedEnglish(root, harvest)
    entries, errors, unit_count = [], [], 0
    batches = sorted((root / 'translation-data/units').glob('*.jsonl'))
    for path in batches:
        try:
            units = load_jsonl(path)
            groups, group_errors = proof_groups(units, english.tags)
            errors.extend(f'{path.name}: {error}' for error in group_errors)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f'{path.name}: unable to inventory proof coverage: {exc}')
            entries.append({'batch': path.stem, 'status': 'unsupported', 'reason': str(exc), 'unit_ids': []})
            continue
        for group in groups:
            ids = [unit['unit_id'] for unit in group['units']]
            unit_count += len(ids)
            entry = {'batch': path.stem, 'unit_ids': ids, 'selector': group['selector']}
            try:
                if group['selector'] is None:
                    raise UnsupportedSource('current proof has no unambiguous statement owner')
                fragment = english.select(group['selector'])
                upstream_nodes, upstream_prose = _comparison(fragment)
                current_nodes, current_prose = _comparison(group['tex'])
                entry.update(english_fragment_hash=byte_hash(fragment), current_source_tex_hash=byte_hash(group['tex']),
                             english_nodes=upstream_nodes, current_nodes=current_nodes,
                             status='match' if (current_nodes, current_prose) == (upstream_nodes, upstream_prose) else 'mismatch')
                if entry['status'] == 'mismatch':
                    entry['reason'] = 'protected node/order differs' if current_nodes != upstream_nodes else 'natural-language source/order differs'
                    errors.append(f'{path.name}: {ids}: {entry["reason"]}')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                entry.update(status='unsupported', reason=str(exc))
                errors.append(f'{path.name}: {ids}: unable to verify: {exc}')
            entries.append(entry)
    report = {'schema_version': 1, 'source_commit': english.commit, 'batch_count': len(batches),
              'proof_group_count': sum(bool(entry['unit_ids']) for entry in entries), 'proof_unit_count': unit_count,
              'matched': sum(entry['status'] == 'match' for entry in entries),
              'mismatched': sum(entry['status'] == 'mismatch' for entry in entries),
              'unsupported': sum(entry['status'] == 'unsupported' for entry in entries),
              'proofs': entries, 'errors': errors}
    return report, errors
