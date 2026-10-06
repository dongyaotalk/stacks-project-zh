"""Complete locked-Git containers and deterministic lowering into fact units.

This module never authors a translation or writes adopted facts. Inventory IDs,
cached spans and current unit IDs are not authority for selecting English.
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from .extraction import ENVIRONMENT, Policy, Scanner, chapter_inventory
from .model_corrections import _first_addition_is_immutable
from .records import RecordError, load_jsonl, stamp_unit_hashes, sha256_value
from .schema_validation import validate_named_schema
from .source_integrity import STATEMENTS, _own_tag, permanent_tag_mapping
from .source_reextractions import LockedEnglish, _git_bytes, byte_hash, proof_groups, source_tex

VERSION = 'source-container-v1'
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*\Z')


def clean(row: dict[str, Any]) -> dict[str, Any]:
    return {k: copy.deepcopy(v) for k, v in row.items() if not k.startswith('_')}


def safe_path(root: Path, relative: str, pattern: str) -> Path:
    if not isinstance(relative, str) or not re.fullmatch(pattern, relative) or '..' in Path(relative).parts:
        raise RecordError('invalid source-container evidence path')
    path = root / relative
    if (not path.resolve().is_relative_to(root.resolve()) or any(
            p.is_symlink() for p in [path, *path.parents] if p.is_relative_to(root))):
        raise RecordError('source-container path escapes repository or is a symlink')
    return path


class Containers:
    """Re-scan actual Git blobs; selection always includes kind and ordinal."""
    def __init__(self, root: Path, harvest: Path | None = None, *, policy_bytes: bytes | None = None):
        self.root = root
        self.english = LockedEnglish(root, harvest)
        self.current_policy_bytes = (root / 'config/macro-policy.yml').read_bytes()
        self.policy_bytes = self.current_policy_bytes if policy_bytes is None else policy_bytes
        self.policy = Policy(self.policy_bytes.decode('utf-8'))
        self.documents: dict[str, tuple[bytes, list[dict[str, Any]], list[dict[str, Any]]]] = {}
        self.closings: dict[str, int] = {}

    def select(self, selector: dict[str, Any]) -> dict[str, Any]:
        if set(selector) != {'file', 'owner_tag', 'owner_label', 'parent_tag', 'kind', 'ordinal'}:
            raise RecordError('container selector requires an explicit full semantic coordinate')
        file, kind = selector['file'], selector['kind']
        ordinal = selector['ordinal']
        if (not isinstance(file, str) or not re.fullmatch(r'[A-Za-z0-9_-]+\.tex', file)
                or not isinstance(kind, str) or not isinstance(ordinal, int)
                or isinstance(ordinal, bool) or ordinal < 1):
            raise RecordError('invalid container file, kind or ordinal')
        chapter = file[:-4]
        label = selector['owner_label']
        if (not isinstance(label, str) or not label.startswith(chapter + '-')
                or self.english.tags.get(label) != selector['owner_tag']
                or sum(tag == selector['owner_tag'] for tag in self.english.tags.values()) != 1):
            raise RecordError('container selector owner Tag/label/chapter is wrong or ambiguous')
        if chapter not in self.documents:
            raw = _git_bytes(self.english.harvest, self.english.commit, file)
            rows, segments, diagnostics = chapter_inventory(chapter, raw, self.english.commit,
                                                      self.english.tags, self.policy)
            self.documents[chapter] = raw, rows, diagnostics
            closing = [s['location']['byte_start'] for s in segments if s['kind'] == 'document-footer']
            if len(closing) == 1:
                self.closings[chapter] = closing[0]
        raw, rows, diagnostics = self.documents[chapter]
        for tag in {selector['owner_tag'], selector['parent_tag']}:
            anchors = [row for row in rows if row['owner_tag'] == tag and
                       (row['unit']['node_kind'] in STATEMENTS or row['unit']['node_kind'].endswith('_title'))]
            if len(anchors) > 1:
                raise RecordError('container owner/Section has duplicate real labelled semantic anchors')
        boundary_witness = None
        if kind == 'prose_block':
            # A complete prose interval lies between real labelled semantic
            # anchors. It includes all paragraphs, lists and non-language gaps,
            # never a hand-picked byte cut in a long footnote or list.
            blocks, active = [], []
            for index, row in enumerate(rows):
                row_kind = row['unit']['node_kind']
                eligible = (row['owner_tag'] == selector['owner_tag'] and row['parent_tag'] == selector['parent_tag']
                            and row_kind not in STATEMENTS | {'proof'} and not row_kind.endswith('_title'))
                if eligible:
                    active.append(index)
                elif active:
                    blocks.append(active)
                    active = []
            if active:
                blocks.append(active)
            if ordinal > len(blocks):
                raise RecordError('prose-block selector has no unique complete semantic interval')
            indices = blocks[ordinal - 1]
            before = rows[indices[0] - 1] if indices[0] else None
            after = rows[indices[-1] + 1] if indices[-1] + 1 < len(rows) else None

            def anchor(row):
                if row is None:
                    return None
                return {'kind': row['unit']['node_kind'], 'owner_tag': row['owner_tag'],
                        'ordinal': int(row['semantic_path'].rsplit('/', 1)[1])}

            # A Section title or labelled statement/proof is required at each
            # internal boundary; a real document closing supplies the last one.
            if before is None:
                raise RecordError('prose block has no real leading semantic anchor')
            start = before['location']['byte_end']
            if after is None and chapter not in self.closings:
                raise RecordError('prose block has no real document closing boundary')
            end = after['location']['byte_start'] if after else self.closings[chapter]
            fragment = raw[start:end].decode('utf-8')
            scanner = Scanner(fragment, self.policy)
            text, tokens, local_problems = scanner.protect(0, len(fragment))
            if local_problems:
                raise RecordError('prose-block adoption blocked: ' + '; '.join(p['message'] for p in local_problems))
            if any(value.startswith(r'\label{') for value in tokens.values()):
                raise RecordError('prose block contains an unclassified real labelled boundary')
            location = {'file': file, 'byte_start': start, 'byte_end': end,
                'line_start': raw[:start].count(b'\n') + 1,
                'line_end': raw[:max(start, end - 1)].count(b'\n') + 1, 'fragment_hash': byte_hash(fragment)}
            boundary_witness = {'before': anchor(before), 'after': anchor(after)}
            row = {'location': location, 'state': 'READY', 'unit': stamp_unit_hashes({
                **rows[indices[0]]['unit'], 'source_text': text, 'placeholders': tokens,
                'node_kind': 'paragraph', 'render': {'prefix': '', 'suffix': ''}})}
            problems = [d for d in diagnostics if d['location']['byte_start'] < end
                        and d['location']['byte_end'] > start]
            matches = [row]
        else:
            matches = [row for row in rows if row['owner_tag'] == selector['owner_tag']
                   and row['parent_tag'] == selector['parent_tag']
                   and row['semantic_path'] == f'{kind}/{ordinal:04d}']
        if len(matches) != 1:
            raise RecordError('container selector has no unique locked-Git semantic owner')
        row = copy.deepcopy(matches[0])
        if kind != 'prose_block':
            problems = [d for d in diagnostics if d.get('inventory_id') == row['inventory_id']]
        if kind == 'title_title':
            # The chapter's own phantom label belongs to the document header,
            # after maketitle, rather than to the title argument itself. Keep
            # that complete header through the next real semantic boundary.
            index = rows.index(matches[0])
            start = row['location']['byte_start']
            end = (rows[index + 1]['location']['byte_start'] if index + 1 < len(rows)
                   else self.closings.get(chapter))
            if end is None:
                raise RecordError('chapter title has no complete document header boundary')
            header = raw[start:end].decode('utf-8')
            scanner = Scanner(header, self.policy)
            cursor, _ = scanner.command_arguments(0)
            labels = []
            while (cursor := scanner.skip_space(cursor)) < len(header):
                command = re.match(r'\\(maketitle|phantomsection|tableofcontents|label)\b', header[cursor:])
                if command is None:
                    raise RecordError('chapter title contains unsupported document header content')
                if command[1] == 'label':
                    stop, args = scanner.command_arguments(cursor)
                    labels.append(header[args[0][0] + 1:args[0][1] - 1])
                    cursor = stop
                else:
                    cursor += len(command.group())
            if labels != [label.removeprefix(chapter + '-')]:
                raise RecordError('chapter title lacks its unique real phantom label')
            old_end = row['location']['byte_end']
            row['unit']['render']['suffix'] += raw[old_end:end].decode('utf-8')
            row['unit'] = stamp_unit_hashes(row['unit'])
            row['location'].update(byte_end=end, line_end=raw[:end - 1].count(b'\n') + 1,
                                   fragment_hash=byte_hash(header))
            problems += [d for d in diagnostics if d['location']['byte_start'] < end
                         and d['location']['byte_end'] > old_end]
        if row['state'] != 'READY' or problems:
            raise RecordError('container adoption blocked: ' + '; '.join(d['message'] for d in problems))
        location = row['location']
        fragment = raw[location['byte_start']:location['byte_end']].decode('utf-8')
        if source_tex(row['unit']) != fragment or byte_hash(fragment) != location['fragment_hash']:
            raise RecordError('container scanner did not preserve its complete Git fragment')
        # A Git object ID is distinct from the SHA256 used for file bindings.
        object_id = subprocess.run(['git', '-C', str(self.english.harvest), 'rev-parse',
                                    f'{self.english.commit}:{file}'], check=True,
                                   capture_output=True, text=True).stdout.strip()
        math_counts = Counter(value for source_row in rows
                              for name, value in source_row['unit']['placeholders'].items()
                              if name.startswith('MATH_'))
        return {'selector': copy.deepcopy(selector), 'fragment': fragment,
                'location': location, 'blob_oid': object_id, 'blob_hash': byte_hash(raw),
                'source_commit': self.english.commit, 'macro_policy_hash': byte_hash(self.policy_bytes),
                'inventory_unit': row['unit'], 'boundary_witness': boundary_witness,
                '_chapter_math_counts': {value: math_counts[value]
                    for name, value in row['unit']['placeholders'].items() if name.startswith('MATH_')},
                '_chapter_math_text_counts': {value: raw.count(value.encode('utf-8'))
                    for name, value in row['unit']['placeholders'].items() if name.startswith('MATH_')}}

    def assert_unchanged(self) -> None:
        if (self.root / 'config/macro-policy.yml').read_bytes() != self.current_policy_bytes:
            raise RecordError('macro policy changed during container generation')
        current = LockedEnglish(self.root, self.english.harvest)
        if current.commit != self.english.commit or current.tags != self.english.tags:
            raise RecordError('locked source or permanent Tags changed during container generation')
        for chapter, (raw, _, _) in self.documents.items():
            if _git_bytes(self.english.harvest, self.english.commit, chapter + '.tex') != raw:
                raise RecordError('locked Git blob changed during container generation')


def _protected(scanner: Scanner, a: int, b: int, used: dict[str, str]) -> str:
    text, tokens, problems = scanner.protect(a, b)
    if problems:
        raise RecordError('container lowering blocked: ' + '; '.join(p['message'] for p in problems))
    # Separate title/body walks share one deterministic token namespace.
    replacements = {}
    for old, value in tokens.items():
        role = old.rsplit('_', 1)[0]
        if role == 'ENVARGEND':
            role = 'BODYARGCLOSE'  # Only the outer owned title may claim a label.
        index = 1
        while f'{role}_{index:04d}' in used:
            index += 1
        name = f'{role}_{index:04d}'
        used[name] = value
        replacements[old] = name
    return re.sub(r'<([A-Z][A-Z0-9]*_[0-9]{4})>',
                  lambda m: '<' + replacements[m[1]] + '>', text)


def lower_container(selected: dict[str, Any], policy: Policy, *, layout: str = 'whole') -> list[dict[str, Any]]:
    """Split only at the named-title boundary, otherwise keep the whole body.

    Opening/closing wrappers and own labels live in native render fields. All
    nested lists, displays, footnotes and natural title text stay lossless.
    """
    if layout not in {'whole', 'split-title'}:
        raise RecordError('unsupported semantic container layout')
    selector, fragment = selected['selector'], selected['fragment']
    chapter = selector['file'][:-4]
    owner, parent, kind, ordinal = (selector[k] for k in ('owner_tag', 'parent_tag', 'kind', 'ordinal'))
    if not owner or not parent:
        raise RecordError('container requires real owner and Section parent Tags')
    scanner = Scanner(fragment, policy)
    env = ENVIRONMENT.match(fragment, 0)
    title = None
    if kind in STATEMENTS | {'proof'}:
        if env is None or env.group() != f'\\begin{{{kind}}}':
            raise RecordError('container kind does not match its complete opening')
        close = len(fragment) - len(f'\\end{{{kind}}}')
        if close <= env.end() or fragment[close:] != f'\\end{{{kind}}}':
            raise RecordError('container is missing its complete closing')
        body_start = scanner.skip_space(env.end())
        if fragment[body_start:body_start + 1] == '[':
            ending = scanner.argument_end(body_start)
            title = body_start + 1, ending - 1
            body_start = scanner.skip_space(ending)
        if kind in STATEMENTS:
            label = re.match(r'\\label\{([^{}\n]+)\}', fragment[body_start:])
            if label is None:
                raise RecordError('statement lacks its leading own label')
            body_start = scanner.skip_space(body_start + len(label.group()))
        prefix, suffix = fragment[:body_start], fragment[close:]
        a, b = body_start, close
        suffix_id = 'proof' + (f'-{ordinal:03d}' if ordinal != 1 else '') if kind == 'proof' else 'statement'
    elif kind in {'title_title', 'section_title', 'subsection_title', 'subsubsection_title'}:
        command_end, args = scanner.command_arguments(0)
        a, b = args[0][0] + 1, args[0][1] - 1
        if command_end > len(fragment):
            raise RecordError('title argument crosses container boundary')
        prefix, suffix = fragment[:a], fragment[b:]
        kind = 'chapter_title' if kind == 'title_title' else kind
        suffix_id = 'title'
    elif kind in {'paragraph', 'prose_block'}:
        a, b, prefix, suffix = 0, len(fragment), '', ''
        suffix_id = f'prose-{ordinal:04d}' if kind == 'prose_block' else f'paragraph-{ordinal:04d}'
        kind = 'paragraph'
    else:
        raise RecordError('container kind needs a separately specified fact lowering: ' + kind)
    if layout == 'split-title' and (title is None or kind not in STATEMENTS):
        raise RecordError('split-title requires a labelled named statement')

    def unit(identifier, node_kind, text, placeholders, opening, closing):
        return stamp_unit_hashes({'schema_version': 1, 'unit_id': f'tag:{owner}:{identifier}',
            'parent_tag': parent, 'chapter': chapter, 'node_kind': node_kind,
            'risk_level': 'R3' if kind in STATEMENTS | {'proof'} else 'R2' if kind == 'paragraph' else 'R1',
            'source_commit': selected['source_commit'], 'source_text': text,
            'source_status': 'CURRENT', 'placeholders': placeholders,
            'render': {'prefix': opening, 'suffix': closing}})

    tokens: dict[str, str] = {}
    if title is not None and kind in STATEMENTS:
        ta, tb = title
        title_text = _protected(scanner, ta, tb, tokens)
        if layout == 'split-title':
            first = unit('environment-title', 'environment_title', title_text, tokens,
                         fragment[:ta], fragment[tb:a])
            body_tokens: dict[str, str] = {}
            body_text = _protected(scanner, a, b, body_tokens)
            rows = [first, unit(suffix_id, kind, body_text, body_tokens, '', suffix)]
        else:
            body_text = _protected(scanner, a, b, tokens)
            index = 1
            while f'OWNARGEND_{index:04d}' in tokens:
                index += 1
            boundary = f'OWNARGEND_{index:04d}'
            tokens[boundary] = fragment[tb:a]
            rows = [unit(suffix_id, kind, title_text + f'<{boundary}>' + body_text,
                         tokens, fragment[:ta], suffix)]
    else:
        # A proof's optional title is part of the translatable body; its square
        # brackets and original whitespace remain protected.
        if title is not None:
            ta, tb = title
            title_text = _protected(scanner, ta, tb, tokens)
            text = title_text + '<PROOFARGEND_0001>' + _protected(scanner, a, b, tokens)
            tokens['PROOFARGEND_0001'] = fragment[tb:a]
            prefix = fragment[:ta]
        else:
            text = _protected(scanner, a, b, tokens)
        rows = [unit(suffix_id, kind, text, tokens, prefix, suffix)]
    if any(not row['source_text'].strip() for row in rows):
        raise RecordError('lowering cannot create an empty natural-language unit')
    if ''.join(source_tex(row) for row in rows) != fragment:
        raise RecordError('fact lowering changed or lost locked source bytes')
    for row in rows:
        errors = validate_named_schema(row, 'unit.schema.json', 'lowered unit')
        if errors:
            raise RecordError('\n'.join(errors))
    return rows


def old_container_groups(units: list[dict[str, Any]], tags: dict[str, str]) -> list[dict[str, Any]]:
    """Recover full legacy wrapper chains before allowing replacement.

    Permanent coordinates are independently derived from native wrappers. A
    paragraph with no wrapper has no authority to replace an arbitrary proof.
    """
    mapping = permanent_tag_mapping(units, tags)
    proofs, errors = proof_groups(units, tags)
    if errors:
        raise RecordError('invalid frozen proof ownership: ' + '; '.join(errors))
    output = []
    proof_by_first = {g['units'][0]['unit_id']: g for g in proofs}
    cursor = 0
    while cursor < len(units):
        u = units[cursor]
        group = proof_by_first.get(u['unit_id'])
        if group is not None:
            selector = group['selector']
            if not selector:
                raise RecordError('old complete proof has no real adjacent statement owner')
            ids = [row['unit_id'] for row in group['units']]
            output.append({'input_unit_ids': ids, 'file': selector['file'],
                           'owner_tag': selector['statement_tag'], 'kind': 'proof',
                           'ordinal': selector['proof_index']})
            cursor += len(ids)
            continue
        opening = re.search(r'\\begin\{(' + '|'.join(sorted(STATEMENTS)) + r')\}', u['render']['prefix'])
        if opening:
            kind = opening[1]
            owner = _own_tag(u, tags)
            ids, end = [], cursor
            while end < len(units):
                member = units[end]
                if member['chapter'] != u['chapter'] or member['parent_tag'] != u['parent_tag']:
                    raise RecordError('old statement crosses batch source scope')
                if end != cursor and re.search(r'\\begin\{(?:proof|' + '|'.join(sorted(STATEMENTS)) + r')\}', member['render']['prefix']):
                    raise RecordError('old statement wrapper is incomplete or overlaps another container')
                ids.append(member['unit_id'])
                if f'\\end{{{kind}}}' in member['render']['suffix']:
                    break
                end += 1
            else:
                raise RecordError('unclosed frozen statement wrapper')
            if not owner:
                raise RecordError('old statement has no permanent own label')
            output.append({'input_unit_ids': ids, 'file': u['chapter'] + '.tex',
                           'owner_tag': owner, 'kind': kind, 'ordinal': 1})
            cursor = end + 1
            continue
        coordinate = re.fullmatch(r'tag:([0-9A-Z]+)(?::.*)?', mapping[u['unit_id']])
        if coordinate is None:
            raise RecordError('old container has no permanent semantic coordinate')
        output.append({'input_unit_ids': [u['unit_id']], 'file': u['chapter'] + '.tex',
                       'owner_tag': coordinate[1], 'kind': u['node_kind'], 'ordinal': None})
        cursor += 1
    # Add whole prose blocks while retaining exact single-unit unchanged
    # witnesses. Ownership comes from the real Section wrapper, not an old ID.
    blocks, section_owner, active_owner, active = [], None, None, []
    for index, group in enumerate(output):
        anchor_kind = group['kind'] in STATEMENTS | {'proof'} or group['kind'].endswith('_title')
        if not anchor_kind:
            if not active:
                active_owner = section_owner
            active.append(index)
        elif active:
            blocks.append((active, active_owner))
            active = []
        if group['kind'] in {'section_title', 'chapter_title'}:
            section_owner = group['owner_tag']
    if active:
        blocks.append((active, active_owner))

    def anchor(group):
        if group is None:
            return None
        return {'kind': 'title_title' if group['kind'] == 'chapter_title' else group['kind'],
                'owner_tag': group['owner_tag'], 'ordinal': group['ordinal'] or 1}

    counts, prose_groups = {}, []
    for indices, owner in blocks:
        if not owner:
            continue
        ids = [i for index in indices for i in output[index]['input_unit_ids']]
        members = [u for u in units if u['unit_id'] in ids]
        if any(u['parent_tag'] != owner for u in members):
            continue
        key = members[0]['chapter'], owner
        counts[key] = counts.get(key, 0) + 1
        before = output[indices[0] - 1] if indices[0] else None
        after = output[indices[-1] + 1] if indices[-1] + 1 < len(output) else None
        output_group = {'input_unit_ids': ids, 'file': members[0]['chapter'] + '.tex',
            'owner_tag': owner, 'kind': 'prose_block', 'ordinal': counts[key],
            'boundary_witness': {'before': anchor(before), 'after': anchor(after)}}
        # Append after iterating the original native groups.
        prose_groups.append(output_group)
    return output + prose_groups


def _proof_with_detached_displays(units: list[dict[str, Any]], groups: list[dict[str, Any]],
                                 ids: list[str], selected: dict[str, Any]) -> dict[str, Any] | None:
    """A complete native proof, plus adjacent math with independent Git ownership.

    The old display ID does not establish its owner. The complete wrapper chain
    and a unique real protected Git math node establish the relationship.
    """
    selector = selected['selector']
    if selector['kind'] != 'proof':
        return None
    cores = [g for g in groups if g['kind'] == 'proof'
             and all(g[k] == selector[k] for k in ('file', 'owner_tag', 'ordinal'))
             and all(i in ids for i in g['input_unit_ids'])]
    failure = 'restoration must cover one complete old wrapper chain with verified adjacent display nodes'
    if len(cores) != 1:
        return None
    core = cores[0]
    all_ids = [u['unit_id'] for u in units]
    if (not ids or len(set(all_ids)) != len(all_ids) or len(set(ids)) != len(ids)
            or any(i not in all_ids for i in ids)):
        raise RecordError(failure)
    start, end = all_ids.index(ids[0]), all_ids.index(ids[-1])
    if ids != all_ids[start:end + 1]:
        raise RecordError(failure + ': inputs are not a continuous ordered full-batch interval')
    core_ids = core['input_unit_ids']
    position = ids.index(core_ids[0])
    if ids[position:position + len(core_ids)] != core_ids:
        raise RecordError(failure + ': proof input chain is partial or reordered')
    by_id = {u['unit_id']: u for u in units}
    proof_units = [by_id[i] for i in core_ids]
    members = [by_id[i] for i in ids]
    anchor = proof_units[0]
    if any(u['chapter'] != selector['file'][:-4] or u['parent_tag'] != anchor['parent_tag']
           or u['source_commit'] != selected['source_commit'] for u in members):
        raise RecordError(failure + ': detached nodes cross the frozen chapter, parent or source')
    extras = [u for u in members if u['unit_id'] not in core_ids]
    if not extras:
        return None
    target_math = Counter(value for name, value in selected['inventory_unit']['placeholders'].items()
                          if name.startswith('MATH_'))
    prior_math = Counter(value for u in proof_units for name, value in u['placeholders'].items()
                         if name.startswith('MATH_'))
    used = set()
    for unit in extras:
        placeholders = unit['placeholders']
        if len(placeholders) != 1:
            raise RecordError(failure + ': detached input must contain exactly one math node')
        name, value = next(iter(placeholders.items()))
        if (unit['node_kind'] != 'display_math' or not re.fullmatch(r'MATH_[0-9]{4}', name)
                or unit['source_text'].strip() != '<' + name + '>'
                or any(part.strip() for part in unit['render'].values())
                or not (value.startswith(('$$', r'\['))
                        or value.startswith(r'\begin{') and not value.startswith(r'\begin{math}'))):
            raise RecordError(failure + ': detached input has prose, wrappers or non-display math')
        if (target_math[value] != 1 or selected.get('_chapter_math_counts', {}).get(value) != 1
                or selected.get('_chapter_math_text_counts', {}).get(value) != 1
                or prior_math[value] or value in used):
            raise RecordError(failure + ': display is absent, ambiguous, repeated or already inside the old proof')
        used.add(value)
    return core


def verify_old_group(units: list[dict[str, Any]], tags: dict[str, str],
                     ids: list[str], selected: dict[str, Any]) -> None:
    groups = old_container_groups(units, tags)
    selector = selected['selector']
    if selector['kind'] == 'proof':
        cores = [g for g in groups if g['kind'] == 'proof'
                 and all(g[k] == selector[k] for k in ('file', 'owner_tag', 'ordinal'))]
        if len(cores) == 1:
            all_ids = [u['unit_id'] for u in units]
            core_ids = cores[0]['input_unit_ids']
            before, after = all_ids.index(core_ids[0]) - 1, all_ids.index(core_ids[-1]) + 1
            neighbors = []
            while before >= 0 and units[before]['node_kind'] == 'display_math':
                neighbors.append(units[before])
                before -= 1
            while after < len(units) and units[after]['node_kind'] == 'display_math':
                neighbors.append(units[after])
                after += 1
            target_math = {value for name, value in selected['inventory_unit']['placeholders'].items()
                           if name.startswith('MATH_')}
            required = [u['unit_id'] for u in neighbors
                        if any(value in target_math for name, value in u['placeholders'].items()
                               if name.startswith('MATH_'))]
            if any(identifier not in ids for identifier in required):
                raise RecordError('restoration must cover one complete old wrapper chain including its adjacent detached display nodes')
    matches = [group for group in groups if group['input_unit_ids'] == ids and
               ('title_title' if group['kind'] == 'chapter_title' else group['kind']) == selected['selector']['kind']]
    if not matches:
        extended = _proof_with_detached_displays(units, groups, ids, selected)
        if extended is not None:
            matches = [extended]
    if len(matches) != 1:
        raise RecordError('restoration must cover one complete old wrapper chain')
    group, selector = matches[0], selected['selector']
    old_kind = 'title_title' if group['kind'] == 'chapter_title' else group['kind']
    if (group['file'] != selector['file'] or group['owner_tag'] != selector['owner_tag']
            or old_kind != selector['kind'] or group['ordinal'] is not None
            and group['ordinal'] != selector['ordinal']):
        raise RecordError('old/new source containers have a different owner, kind or proof index')
    if group['ordinal'] is None:
        old = next(u for u in units if u['unit_id'] == ids[0])
        # Standalone prose has no label to prove a defective source location.
        # Exact unique provenance is needed, otherwise adoption remains blocked.
        if old_kind == 'paragraph' and source_tex(old) != selected['fragment']:
            raise RecordError('unlabelled paragraph cannot authorize a different English fragment')
    if old_kind == 'prose_block' and group['boundary_witness'] != selected['boundary_witness']:
        raise RecordError('complete prose block has different real preceding/following semantic anchors')


def load_source_containers(root: Path, harvest: Path | None = None):
    """Validate immutable evidence; replay verifies full-batch/group use next."""
    evidence, errors = {}, []
    paths = sorted((root / 'translation-data/source-container-restorations').glob('*.json'))
    if not paths:
        return evidence, errors
    try:
        containers = Containers(root, harvest)
    except (OSError, ValueError) as exc:
        return {}, [f'source-container initialization: {exc}']
    historical_containers = {}
    for path in paths:
        try:
            safe_path(root, path.relative_to(root).as_posix(),
                      r'translation-data/source-container-restorations/[A-Za-z0-9._-]+\.json')
            record = json.loads(path.read_text(encoding='utf-8'))
            problems = validate_named_schema(record, 'source-container-restoration.schema.json', str(path))
            if problems:
                raise RecordError('\n'.join(problems))
            if record['restoration_id'] != path.stem or not ID.fullmatch(path.stem) or '..' in path.stem:
                raise RecordError('source-container evidence filename differs from its safe ID')
            _first_addition_is_immutable(root, path)
            # Historical policy is frozen by the real origin Git revision;
            # a later policy task cannot reinterpret or invalidate old output
            # merely by changing today's macro registry.
            from .derivations import _git_origin_bytes
            origin = record['origin_commit']
            if origin not in historical_containers:
                historical_containers[origin] = Containers(root, harvest,
                    policy_bytes=_git_origin_bytes(root, origin, 'config/macro-policy.yml'))
            historical = historical_containers[origin]
            selected = historical.select(record['selector'])
            for key in ('source_commit', 'fragment', 'location', 'blob_oid', 'blob_hash', 'macro_policy_hash', 'boundary_witness'):
                if record[key] != selected[key]:
                    raise RecordError('source-container evidence differs from locked Git: ' + key)
            if record['tool'] != {'id': 'stacks-zh-source-container', 'version': VERSION}:
                raise RecordError('unsupported container extraction/lowering version')
            frozen = {}
            for role, name in [('input_units', 'units'), ('input_candidates', 'candidates')]:
                entry = record['files'][role]
                pattern = rf"translation-data/retired/derivations/{re.escape(record['derivation_id'])}/{name}\.jsonl"
                frozen_path = safe_path(root, entry['path'], pattern)
                if byte_hash(frozen_path.read_bytes()) != entry['hash']:
                    raise RecordError('source-container full-batch snapshot hash mismatch')
                _first_addition_is_immutable(root, frozen_path)
                frozen[role] = [clean(u) for u in load_jsonl(frozen_path)]
            units, candidates = frozen['input_units'], frozen['input_candidates']
            if (not units or len({u['unit_id'] for u in units}) != len(units)
                    or [c['unit_id'] for c in candidates] != [u['unit_id'] for u in units]):
                raise RecordError('source-container full frozen batch has inconsistent IDs/order')
            verify_old_group(units, historical.english.tags, record['input_unit_ids'], selected)
            expected = lower_container(selected, historical.policy, layout=record['layout'])
            if record['new_units'] != expected or record['output_unit_ids'] != [u['unit_id'] for u in expected]:
                raise RecordError('source-container new units differ from deterministic complete lowering')
            evidence[path.stem] = {'record': record, 'selected': selected,
                                   'units': units, 'candidates': candidates, 'tags': containers.english.tags}
        except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
            errors.append(f'{path}: {exc}')
    try:
        containers.assert_unchanged()
        for historical in historical_containers.values():
            historical.assert_unchanged()
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    return evidence, errors


def prepare_containers(root: Path, harvest: Path, plan: dict[str, Any]):
    """Prepare every declared group against the exact current Git batch.

    A blocked group remains in the full input and diagnostic package. No
    correction ID, run, approval or adopted derivation is manufactured here.
    """
    from .provenance import validate_repository_provenance
    from .derivations import _git_origin_bytes

    def repository_state():
        paths = [root / 'upstream.lock', *sorted((root / 'config').glob('*')),
                 *sorted((root / 'translation-data').rglob('*.json')),
                 *sorted((root / 'translation-data').rglob('*.jsonl')),
                 *sorted((root / 'review').rglob('*.json'))]
        state = {}
        for path in paths:
            if not path.is_file() or path.name == 'local.mk':
                continue
            safe_path(root, path.relative_to(root).as_posix(), r'[A-Za-z0-9._/-]+')
            state[path.relative_to(root).as_posix()] = byte_hash(path.read_bytes())
        return state

    frozen_state = repository_state()
    expected = {'derivation_id', 'created_at', 'units_file', 'candidates_file', 'groups'}
    if not isinstance(plan, dict) or set(plan) != expected:
        raise RecordError('container plan needs exact identity, full-batch files and groups')
    identifier = plan['derivation_id']
    if not isinstance(identifier, str) or not ID.fullmatch(identifier) or '..' in identifier:
        raise RecordError('unsafe proposed derivation ID')
    unit_path = safe_path(root, plan['units_file'], r'translation-data/units/[A-Za-z0-9._-]+\.jsonl')
    candidate_path = safe_path(root, plan['candidates_file'], r'translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl')
    if unit_path.name != candidate_path.name:
        raise RecordError('container plan must name one paired complete logical batch')
    origin_commit = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], check=True,
                                   capture_output=True, text=True).stdout.strip()
    frozen = {p: p.read_bytes() for p in (unit_path, candidate_path)}
    for path, raw in frozen.items():
        original = _git_origin_bytes(root, origin_commit, path.relative_to(root).as_posix())
        if raw != original:
            raise RecordError('container preparation requires the exact committed current complete batch')
    provenance_errors = validate_repository_provenance(root, harvest)
    if provenance_errors:
        raise RecordError('container preparation blocked by provenance:\n' + '\n'.join(provenance_errors))
    units = [clean(u) for u in load_jsonl(unit_path)]
    candidates = [clean(c) for c in load_jsonl(candidate_path)]
    old_ids = [u['unit_id'] for u in units]
    if (not old_ids or len(set(old_ids)) != len(old_ids)
            or [c['unit_id'] for c in candidates] != old_ids
            or len({u['chapter'] for u in units}) != 1):
        raise RecordError('container preparation needs unique equally ordered full inputs in one chapter')
    groups = plan['groups']
    if (not isinstance(groups, list) or not groups or any(not isinstance(g, dict) for g in groups)
            or any(set(g) != {'group_id', 'input_unit_ids', 'identity_anchor', 'selector', 'layout', 'reason'} for g in groups)
            or [i for g in groups for i in g['input_unit_ids']] != old_ids
            or len({g['group_id'] for g in groups}) != len(groups)):
        raise RecordError('container plan must partition every old ID once in complete source order')
    containers = Containers(root, harvest)
    if any(row['source_commit'] != containers.english.commit for row in units + candidates):
        raise RecordError('complete container batch source revision differs from the English lock')
    if containers.policy_bytes != _git_origin_bytes(root, origin_commit, 'config/macro-policy.yml'):
        raise RecordError('container macro policy must match the committed preparation origin')
    mapping = permanent_tag_mapping(units, containers.english.tags)
    previous_ids = {c.get('derivation_id') for c in candidates}
    if len(previous_ids) != 1:
        raise RecordError('container current batch must have one exact validated predecessor or raw origin')
    previous_id = next(iter(previous_ids))
    snapshot_files = {role: {'path': f'translation-data/retired/derivations/{identifier}/{name}.jsonl',
                             'hash': byte_hash(frozen[path])}
                      for role, name, path in [('input_units', 'units', unit_path),
                                               ('input_candidates', 'candidates', candidate_path)]}
    by_id = {u['unit_id']: u for u in units}
    proposals, restored, diagnostics, lowered = [], [], [], []
    seen_outputs, last_location = set(), {}
    for group in groups:
        group_id, ids = group['group_id'], group['input_unit_ids']
        if (not isinstance(group_id, str) or not ID.fullmatch(group_id) or '..' in group_id
                or not ids or group['identity_anchor'] not in ids or not isinstance(group['reason'], str)
                or not group['reason'].strip()):
            raise RecordError('container group needs a safe ID, complete inputs, reason and old identity anchor')
        proposed = {**copy.deepcopy(group), 'state': 'BLOCKED', 'output_unit_ids': [], 'output_units': []}
        try:
            if group['selector'] is None:
                if len(ids) != 1 or group['layout'] != 'whole':
                    raise RecordError('source-preserving group must be one complete unchanged unit')
                new_units = [stamp_unit_hashes({**by_id[ids[0]], 'unit_id': mapping[ids[0]]})]
                restoration_id = None
            else:
                selected = containers.select(group['selector'])
                verify_old_group(units, containers.english.tags, ids, selected)
                file, location = selected['selector']['file'], selected['location']
                if location['byte_start'] < last_location.get(file, 0):
                    raise RecordError('selected source containers overlap or reverse complete source order')
                last_location[file] = location['byte_end']
                new_units = lower_container(selected, containers.policy, layout=group['layout'])
                restoration_id = identifier + '-' + group_id
                evidence = {k: copy.deepcopy(selected[k]) for k in (
                    'source_commit', 'selector', 'fragment', 'location', 'blob_oid', 'blob_hash', 'macro_policy_hash', 'boundary_witness')}
                evidence.update(schema_version=1, restoration_id=restoration_id, derivation_id=identifier,
                    group_id=group_id, created_at=plan['created_at'], origin_commit=origin_commit,
                    tool={'id': 'stacks-zh-source-container', 'version': VERSION}, layout=group['layout'],
                    input_unit_ids=ids, output_unit_ids=[u['unit_id'] for u in new_units], new_units=new_units,
                    reason=group['reason'], files=snapshot_files)
                problems = validate_named_schema(evidence, 'source-container-restoration.schema.json', 'proposed evidence')
                if problems:
                    raise RecordError('\n'.join(problems))
                restored.append(evidence)
            new_ids = [u['unit_id'] for u in new_units]
            if seen_outputs.intersection(new_ids) or len(set(new_ids)) != len(new_ids):
                raise RecordError('proposed output groups collide')
            seen_outputs.update(new_ids)
            proposed.update(state='PREPARED', output_unit_ids=new_ids, output_units=new_units,
                            source_container_restoration_id=restoration_id)
            lowered.extend(new_units)
        except RecordError as exc:
            diagnostics.append({'group_id': group_id, 'input_unit_ids': ids, 'severity': 'BLOCKED', 'message': str(exc)})
        proposals.append(proposed)
    for path in sorted((root / 'translation-data/units').glob('*.jsonl')):
        if path != unit_path:
            for row in load_jsonl(path):
                if row['unit_id'] in seen_outputs:
                    raise RecordError('proposed output ID collides with another active fact batch: ' + row['unit_id'])
    other_lanes = [p for p in (root / 'translation-data/candidates').glob('*/' + unit_path.name) if p != candidate_path]
    if other_lanes and lowered != units:
        raise RecordError('source changes affect other active model lanes; declare their full adoption separately')
    manifest = {'schema_version': 1, 'generator': VERSION, 'source_commit': containers.english.commit,
        'origin_commit': origin_commit, 'derivation_id': identifier, 'previous_derivation_id': previous_id,
        'plan_hash': sha256_value(plan), 'macro_policy_hash': byte_hash(containers.policy_bytes),
        'input_repository_hash': sha256_value(frozen_state),
        'input_unit_count': len(units), 'proposed_output_unit_count': len(lowered),
        'group_count': len(groups), 'blocked_group_count': len(diagnostics),
        'state': 'BLOCKED' if diagnostics else 'PREPARED', 'files': {}}

    def current_inputs():
        containers.assert_unchanged()
        if repository_state() != frozen_state:
            raise RecordError('repository facts, history or policy changed during source-container preparation')
        for path, raw in frozen.items():
            if path.read_bytes() != raw:
                raise RecordError('current full batch changed during source-container preparation')
        if subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'], check=True,
                          capture_output=True, text=True).stdout.strip() != origin_commit:
            raise RecordError('Chinese origin Git revision changed during source-container preparation')

    current_inputs()
    return manifest, proposals, restored, diagnostics, lowered, frozen, current_inputs


def write_container_package(root: Path, harvest: Path, plan_path: Path, output: Path, *, check: bool = False):
    """Write a dedicated ignored review package, or compare without writing."""
    supplied_root = root.absolute()
    output = output.absolute()
    if not output.is_relative_to(supplied_root):
        raise RecordError('container output escapes the supplied repository')
    for path in [output, *output.parents]:
        if path != supplied_root and path.is_relative_to(supplied_root) and path.is_symlink():
            raise RecordError('container package output or parent is a symlink')
    root = root.resolve()
    output = output.resolve()
    if not any(output.is_relative_to(root / d) and output != root / d for d in ('build', 'source-ir')):
        raise RecordError('container package needs a dedicated ignored build/ or source-ir/ subdirectory')
    names = {'manifest.json', 'groups.json', 'restorations.json', 'diagnostics.json', 'units.jsonl',
             'input-units.jsonl', 'input-candidates.jsonl', 'report.md'}
    previous = None
    if output.exists():
        if not output.is_dir() or {p.name for p in output.iterdir()} != names:
            raise RecordError('container package destination contains unrelated or incomplete files')
        if any(p.is_symlink() or not p.is_file() for p in output.iterdir()):
            raise RecordError('container package destination contains unsafe files')
        previous = {p.name: p.read_bytes() for p in output.iterdir()}
        previous_manifest = json.loads(previous['manifest.json'])
        if previous_manifest.get('generator') != VERSION:
            raise RecordError('container package destination is not owned by this generator')
        if (set(previous_manifest.get('files', {})) != names - {'manifest.json'}
                or any(byte_hash(previous[name]) != value for name, value in previous_manifest['files'].items())):
            raise RecordError('container package has stale or tampered file hashes')
    raw_plan = plan_path.read_bytes()
    plan = json.loads(raw_plan)
    manifest, groups, restorations, diagnostics, units, frozen, assert_inputs = prepare_containers(root, harvest, plan)
    json_bytes = lambda value: (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    payloads = {'groups.json': json_bytes(groups), 'restorations.json': json_bytes(restorations),
        'diagnostics.json': json_bytes(diagnostics),
        'units.jsonl': ''.join(json.dumps(u, ensure_ascii=False, sort_keys=True) + '\n' for u in units).encode(),
        'input-units.jsonl': next(raw for path, raw in frozen.items() if path.parent.name == 'units'),
        'input-candidates.jsonl': next(raw for path, raw in frozen.items() if path.parent.name != 'units')}
    report = ['# 完整来源容器待审包', '', f"英文锁：`{manifest['source_commit']}`；工具：`{VERSION}`。", '',
        f"完整旧输入 {manifest['input_unit_count']} 个；提议新输入 {manifest['proposed_output_unit_count']} 个；"
        f"{manifest['group_count']} 组，其中 {manifest['blocked_group_count']} 组 BLOCKED。", '',
        'PREPARED 仅表示来源准备，不是事实采用、模型输出、术语/人审或发布批准。',
        '每个新单元仍需实际模型五字段完整修订；完整旧批次和全部历史必须保存。', '',
        '| Group | State | Old | New |', '| --- | --- | ---: | ---: |']
    report.extend(f"| {g['group_id']} | {g['state']} | {len(g['input_unit_ids'])} | {len(g['output_unit_ids'])} |" for g in groups)
    report.extend(['', '诊断：', ''] + [f"- {d['group_id']}: {d['message']}" for d in diagnostics])
    payloads['report.md'] = ('\n'.join(report) + '\n').encode()
    manifest['files'] = {name: byte_hash(raw) for name, raw in payloads.items()}
    payloads['manifest.json'] = json_bytes(manifest)

    def unchanged():
        assert_inputs()
        if (not output.resolve().is_relative_to(root) or any(
                path.is_symlink() for path in [output, *output.parents] if path.is_relative_to(root))):
            raise RecordError('container output or parent changed to a symlink during generation')
        if plan_path.read_bytes() != raw_plan:
            raise RecordError('container plan changed during generation')
        if output.exists() != (previous is not None) or (previous is not None and (
                {p.name for p in output.iterdir()} != names or any(p.is_symlink() for p in output.iterdir())
                or {p.name: p.read_bytes() for p in output.iterdir()} != previous)):
            raise RecordError('container output changed concurrently')

    unchanged()
    if check:
        if previous != payloads:
            raise RecordError('source-container review package missing or stale')
        return manifest
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.containers-', dir=output.parent))
    backup = None
    try:
        for name, raw in payloads.items():
            (temporary / name).write_bytes(raw)
        unchanged()
        if previous is not None:
            backup = Path(tempfile.mkdtemp(prefix='.containers-backup-', dir=output.parent))
            backup.rmdir()
            output.rename(backup)
        try:
            temporary.rename(output)
        except OSError:
            if backup is not None:
                backup.rename(output)
                backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup)
            backup = None
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return manifest
