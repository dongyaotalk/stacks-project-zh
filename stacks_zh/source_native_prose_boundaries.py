"""Complete prose correspondence, bound to native and frozen semantic anchors.

This version does not forgive source changes. It handles a batch ending before
the next native anchor, and a chapter header preceding a Section's full body.
"""
from __future__ import annotations

import re
import copy

from .extraction import Scanner
from .math_text import TOKEN, complete_math_nodes, delimiter_kind, nodes, validate_regions
from .records import RecordError, sha256_value
from .source_integrity import STATEMENTS, _own_tag
from .source_reextractions import byte_hash, source_tex

VERSION = 'source-container-v13'
HEADINGS = {'section_title', 'subsection_title', 'subsubsection_title'}
# The complete lexical language of the observed historical wrapping defects.
# An unknown macro cannot acquire a layout restoration through identical tokens.
WRAPPING_COMMANDS = {'xi', 'in', 'hat', 'mathfrak', 'to', 'mathcal', 'phi',
                     'CH', 'text', 'textit', 'textbf', 'rightarrow', 'varphi',
                     'alpha', 'sup', 'bigcup', '{', '}'}


def native_document_header_witness(containers, units, group, selected):
    if (selected['selector']['kind'] != 'title_title' or group['kind'] != 'chapter_title'
            or len(group['input_unit_ids']) != 1
            or any(u['source_commit'] != selected['source_commit']
                   or u['chapter'] + '.tex' != selected['selector']['file']
                   or u['schema_version'] not in {1, 2, 3} or validate_regions(u) for u in units)
            or len({u['unit_id'] for u in units}) != len(units)):
        raise RecordError('literal document header requires the complete frozen chapter title')
    unit = next(u for u in units if u['unit_id'] == group['input_unit_ids'][0])
    selector = selected['selector']
    if (unit['parent_tag'] != selector['owner_tag']
            or selector['parent_tag'] != selector['owner_tag']
            or _own_tag(unit, containers.english.tags) != selector['owner_tag']
            or re.fullmatch(r'[ \t\r\n]*\\(?:chapter|title)\{', unit['render']['prefix']) is None
            or not unit['render']['suffix'].startswith('}')):
        raise RecordError('literal document header has a different real phantom owner or title wrapper')
    original = source_tex(unit)
    core = original[len(unit['render']['prefix']):-len(unit['render']['suffix'])]
    scanner = Scanner(selected['fragment'], containers.policy)
    _, args = scanner.command_arguments(0)
    native_core = selected['fragment'][args[0][0]+1:args[0][1]-1]
    a, b = prose_signature(core, containers, unit['chapter']), prose_signature(native_core, containers, unit['chapter'])
    if a != b:
        raise RecordError('literal document header changes the complete chapter title')
    suffix = unit['render']['suffix'][1:]
    old_scanner, cursor, labels = Scanner(suffix, containers.policy), 0, []
    while (cursor := old_scanner.skip_space(cursor)) < len(suffix):
        command = re.match(r'\\(maketitle|phantomsection|tableofcontents|label)\b', suffix[cursor:])
        if command is None:
            raise RecordError('frozen chapter title has unsupported trailing metadata')
        if command[1] == 'label':
            end, arguments = old_scanner.command_arguments(cursor)
            labels.append(suffix[arguments[0][0]+1:arguments[0][1]-1]);cursor=end
        else:
            cursor += len(command.group())
    tags = containers.english.tags
    if len(labels) != 1 or tags.get(labels[0], tags.get(unit['chapter']+'-'+labels[0])) != selector['owner_tag']:
        raise RecordError('frozen chapter title lacks its unique actual phantom label')
    return dict(input_unit_id=unit['unit_id'], historical_parent_tag=unit['parent_tag'],
        native_selector=selector, native_fragment_hash=selected['location']['fragment_hash'],
        historical_title_signature_hash=sha256_value(a), native_title_signature_hash=sha256_value(b),
        literal_environments=selected.get('_document_header_literals', []))


def legacy_heading_kind(group, units):
    if group['kind'] == 'chapter_title':
        return 'title_title'
    if group['kind'] not in HEADINGS or len(group['input_unit_ids']) != 1:
        return group['kind']
    unit = next(u for u in units if u['unit_id'] == group['input_unit_ids'][0])
    match = re.fullmatch(r'[ \t\r\n]*\\(section|subsection|subsubsection)\{', unit['render']['prefix'])
    return match[1] + '_title' if match else group['kind']


def native_heading_witness(containers, units, group, selected):
    ids, selector = group['input_unit_ids'], selected['selector']
    if (len(ids) != 1 or selector['kind'] not in HEADINGS
            or legacy_heading_kind(group, units) != selector['kind']
            or group['owner_tag'] != selector['owner_tag']):
        raise RecordError('native heading requires its complete real old heading wrapper')
    unit = next(u for u in units if u['unit_id'] == ids[0])
    if (unit['parent_tag'] not in {selector['owner_tag'], selector['parent_tag']}
            or any(u['source_commit'] != selected['source_commit']
                   or u['chapter'] + '.tex' != selector['file']
                   or u['schema_version'] not in {1, 2, 3} or validate_regions(u) for u in units)
            or len({u['unit_id'] for u in units}) != len(units)):
        raise RecordError('native heading has a foreign frozen source or historical parent')
    original = source_tex(unit)
    native = prose_signature(selected['fragment'], containers, unit['chapter'])
    options = [(original, [])]
    # Only explicitly stored initial body structure can follow this old title.
    pattern = r'((?:[ \t\r\n]*\\(?:noindent|begin\{(?:itemize|enumerate)\})){1,2})[ \t\r\n]*\Z'
    tail = re.search(pattern, original)
    if tail:
        commands = re.findall(r'\\(?:noindent|begin\{(?:itemize|enumerate)\})', tail[1])
        if commands in [[r'\noindent'], [r'\begin{itemize}'], [r'\begin{enumerate}'],
                        [r'\noindent', r'\begin{itemize}'], [r'\noindent', r'\begin{enumerate}']]:
            options.append((original[:tail.start()], commands))
    raw, _, _ = containers.document(unit['chapter'])
    for core, detached in options:
        try:
            signature = prose_signature(core, containers, unit['chapter'])
        except RecordError:
            continue
        if signature != native:
            continue
        cursor = selected['location']['byte_end']
        start = cursor
        for command in detached:
            while cursor < len(raw) and raw[cursor] in b' \t\r\n':
                cursor += 1
            encoded = command.encode()
            if raw[cursor:cursor + len(encoded)] != encoded:
                break
            cursor += len(encoded)
        else:
            return dict(input_unit_id=unit['unit_id'], historical_node_kind=unit['node_kind'],
                historical_parent_tag=unit['parent_tag'], native_selector=selector,
                native_fragment_hash=selected['location']['fragment_hash'],
                historical_signature_hash=sha256_value(signature + [['protected', v] for v in detached]),
                native_signature_hash=sha256_value(native), detached_layout=detached,
                following_body_prefix_hash=sha256_value(raw[start:cursor].decode()))
    raise RecordError('native heading changes its complete text, wrapper or body boundary')


def prose_signature(fragment, containers, chapter):
    scanner = Scanner(fragment, containers.policy)
    text, tokens, errors = scanner.protect(0, len(fragment))
    if errors:
        raise RecordError('native prose has unsupported source syntax')
    # A classified text leaf is still part of the complete original English
    # mathematical node for this source comparison. Never normalize its bytes.
    for index, region in enumerate(scanner.math_text_regions, 1):
        slots = {s['slot_id']: s['source'] for s in region['slots']}
        protected = ''.join('<'+p['placeholder']+'>' if p['kind']=='locked' else slots[p['slot_id']]
                            for p in region['pieces'])
        name = f'ORIGINALMATH_{index:04d}'
        if text.count(protected) != 1 or name in tokens:
            raise RecordError('native prose has ambiguous complete original math')
        text = text.replace(protected, '<'+name+'>', 1)
        tokens[name] = region['source']
    signature, cursor = [], 0
    def prose(value):
        normalized = re.sub(r'[ \t\r\n]+', ' ', value).strip(' ')
        if normalized:
            signature.append(['text', normalized])
    for match in TOKEN.finditer(text):
        prose(text[cursor:match.start()])
        if match[1] not in tokens:
            raise RecordError('native prose has a forged protected token')
        signature.append(['protected', tokens[match[1]]])
        cursor = match.end()
    prose(text[cursor:])
    for node in signature:
        if node[0] != 'protected':
            continue
        reference = re.fullmatch(r'\\(label|ref|eqref|pageref)\{([^{}\n]+)\}', node[1])
        if reference is None:
            continue
        label = reference[2]
        tag = containers.english.tags.get(label, containers.english.tags.get(chapter + '-' + label))
        if tag is not None:
            node[:] = ['permanent-reference', reference[1], tag]
    return signature


def _selector(containers, chapter, row):
    labels = [k for k, v in containers.english.tags.items()
              if v == row['owner_tag'] and k.startswith(chapter + '-')]
    if len(labels) != 1:
        raise RecordError('native prose anchor has no unique permanent label')
    return dict(file=chapter + '.tex', owner_tag=row['owner_tag'], owner_label=labels[0],
                parent_tag=row['parent_tag'], kind=row['unit']['node_kind'],
                ordinal=int(row['semantic_path'].rsplit('/', 1)[1]))


def _quotation_projection(signature):
    projected, repairs, opened = copy.deepcopy(signature), [], False
    for index, node in enumerate(projected):
        if node[0] != 'text':
            continue
        output = []
        for offset, char in enumerate(node[1]):
            if char not in {'“', '”'}:
                output.append(char)
                continue
            if (char == '“') == opened:
                raise RecordError('legacy quotation projection requires balanced simple pairs')
            opened = char == '“'
            replacement = '``' if opened else "''"
            output.append(replacement)
            repairs.append(dict(kind='paired-double-quote', signature_index=index,
                                text_offset=offset, source=char, replacement=replacement))
        node[1] = ''.join(output)
    if opened:
        raise RecordError('legacy quotation projection has an unclosed pair')
    return projected, repairs


def _layout_projection(original, native, members):
    """Reconstruct only the two independently observed missing openings."""
    projected, repairs = copy.deepcopy(original), []
    if (native and native[0] == ['protected', r'\noindent']
            and projected and projected[0] != native[0]
            and not members[0]['render']['prefix'].strip(' \t\r\n')):
        projected.insert(0, native[0])
        repairs.append(dict(kind='initial-noindent', signature_index=0, text_offset=0,
                            source='', replacement=r'\noindent'))
    index = next((i for i in range(min(len(projected), len(native))) if projected[i] != native[i]), None)
    if index is not None:
        opening = native[index]
        kind = next((k for k in ['itemize', 'enumerate']
                     if opening == ['protected', '\\begin{'+k+'}']), None)
        if (kind and projected[index] == ['protected', r'\item']
                and any(u['node_kind']=='list_item' and source_tex(u).lstrip(' \t\r\n').startswith(r'\item')
                        for u in members)):
            depth, closed = 0, False
            for node in native[index:]:
                if node == ['protected', '\\begin{'+kind+'}']:
                    depth += 1
                elif node == ['protected', '\\end{'+kind+'}']:
                    depth -= 1
                    if depth == 0:
                        closed = True
                        break
            if closed:
                projected.insert(index, opening)
                repairs.append(dict(kind='initial-list-opening', signature_index=index, text_offset=0,
                                    source='', replacement=opening[1]))
    return projected, repairs


def _correspondence(original, native, members):
    choices = [(copy.deepcopy(original), [])]
    try:
        quoted, repairs = _quotation_projection(original)
        if repairs:
            choices.append((quoted, repairs))
    except RecordError:
        pass
    matches = []
    for candidate, repairs in choices:
        projected, layout = _layout_projection(candidate, native, members)
        projected, presentation = _source_presentation_projection(projected, native)
        if projected == native:
            matches.append((projected, repairs + layout + presentation))
    if len(matches) != 1:
        raise RecordError('native prose changes complete text or protected source nodes')
    return matches[0]


def _math_wrapping_changes(original, native):
    """Only replace existing root math whitespace runs, never opaque contents."""
    try:
        if delimiter_kind(original) != delimiter_kind(native):
            return None
        left, right = nodes(original), nodes(native)
    except ValueError:
        return None
    if len(left) != len(right) or any(a['token'] != b['token'] for a,b in zip(left,right)):
        return None
    if '%' in original or any(n['token'].startswith('\\')
            and re.match(r'\\([A-Za-z@]+|[\s\S])',n['token'])[1] not in WRAPPING_COMMANDS for n in left):
        return None
    changes, aend, bend = [], 0, 0
    for a,b in zip(left,right):
        before, after = original[aend:a['start']], native[bend:b['start']]
        if before != after:
            if (a['depth'] != 0 or b['depth'] != 0
                    or re.fullmatch(r'[ \t\r\n]+', before) is None
                    or re.fullmatch(r'[ \t\r\n]+', after) is None):
                return None
            changes.append((aend, before, after))
        aend, bend = a['end'], b['end']
    if original[aend:] != native[bend:]:
        return None
    return changes


def _source_presentation_projection(original, native):
    projected, repairs = copy.deepcopy(original), []
    if len(projected) != len(native):
        return projected, repairs
    for index, (old, target) in enumerate(zip(projected, native)):
        if old == target or old[0] != target[0]:
            continue
        changes = []
        if old[0] == 'protected':
            if old[1] == r'\emph{' and re.fullmatch(r'\{\\it[ \t\r\n]*', target[1]):
                changes = [('emphasis-wrapper', 0, old[1], target[1])]
            else:
                wrapping = _math_wrapping_changes(old[1], target[1])
                if wrapping is not None:
                    changes = [('math-root-wrapping', offset, source, replacement)
                               for offset,source,replacement in wrapping]
        elif old[0] == 'text':
            output = old[1]
            # These two typographic defects have independently observed full
            # native correspondences; no other punctuation is normalized.
            if '—' in output:
                changes += [('prose-em-dash', match.start(), '—', '---')
                            for match in re.finditer('—', output)]
                output = output.replace('—', '---')
            if re.search(r'(?<!\.)\.\.\Z', output):
                changes.append(('duplicated-terminal-period', len(old[1])-2, '..', '.'))
                output = output[:-1]
            if output != target[1]:
                changes = []
        if changes:
            old[1] = target[1]
            repairs.extend(dict(kind=kind,signature_index=index,text_offset=offset,
                                source=source,replacement=replacement)
                           for kind,offset,source,replacement in changes)
    return projected, repairs


def native_prose_witness(containers, units, groups, group, selected):
    selector = selected['selector']
    kind, parent, owner = selector['kind'], selector['parent_tag'], selector['owner_tag']
    ids, order = group['input_unit_ids'], [u['unit_id'] for u in units]
    chapter = selector['file'][:-4]
    if (kind not in {'paragraph', 'prose_block'} or group['kind'] != kind
            or len(set(order)) != len(order)
            or not ids or len(set(ids)) != len(ids) or any(i not in order for i in ids)):
        raise RecordError('native prose requires one complete real Section-owned group')
    start = order.index(ids[0])
    if order[start:start + len(ids)] != ids:
        raise RecordError('native prose inputs are not the complete ordered frozen interval')
    members = units[start:start + len(ids)]
    # Historical nested-list pieces are already supported unit kinds. At a
    # witnessed document footer they remain one complete prose block; the
    # signature below still verifies every original list/control/math byte.
    footer_list_kinds = ({'list_item_intro', 'nested_list_item', 'list_item_outro'}
                         if selected.get('_native_document_footer') and kind == 'prose_block'
                         else set())
    phantom = (owner == parent == containers.english.tags.get(chapter+'-section-phantom')
               and kind == 'prose_block')
    if (any(u['schema_version'] not in {1, 2, 3} or u['chapter'] != chapter
            or u['source_commit'] != selected['source_commit'] for u in units)
            or selected['inventory_unit']['schema_version'] not in {1, 2, 3}
            or any(u['node_kind'] not in ({'paragraph', 'list_item', 'display_math'} | footer_list_kinds
                | (containers.policy.body - STATEMENTS - {'proof'})
                | ({'notice', 'heading'} if phantom else set())) for u in members)):
        raise RecordError('native prose requires supported full-batch source nodes')
    if any(validate_regions(u) for u in [*units, selected['inventory_unit']]):
        raise RecordError('native prose has invalid original mathematical regions')
    # These signatures keep comments, math, references and every structural byte.
    # Only ordinary ASCII prose wrapping follows the existing v12 comparison.
    old_signature = prose_signature(''.join(source_tex(u) for u in members), containers, chapter)
    signature = prose_signature(selected['fragment'], containers, chapter)
    if not signature:
        raise RecordError('native prose has no complete source signature')
    projected_signature, presentation_repairs = _correspondence(old_signature, signature, members)

    raw, rows, _ = containers.documents[chapter]
    location = selected['location']
    semantic = [r for r in rows if r['unit']['node_kind'] in STATEMENTS | {'proof'}
                or r['unit']['node_kind'].endswith('_title')]
    before = [r for r in semantic if r['location']['byte_end'] <= location['byte_start']]
    after = [r for r in semantic if r['location']['byte_start'] >= location['byte_end']]
    if not before:
        raise RecordError('native prose lacks its real leading semantic anchor')
    preceding = containers.select(_selector(containers, chapter, before[-1]))
    following = containers.select(_selector(containers, chapter, after[0])) if after else None
    if kind == 'prose_block':
        ending = following['location']['byte_start'] if following else containers.closings.get(chapter)
        if (preceding['location']['byte_end'] != location['byte_start']
                or ending != location['byte_end']):
            raise RecordError('native prose block does not fill its entire semantic interval')
    elif not any(r['location'] == location and r['unit']['node_kind'] == 'paragraph'
                 and r['owner_tag'] == owner and r['parent_tag'] == parent for r in rows):
        raise RecordError('native paragraph is not one complete real source node')
    if (preceding['selector']['parent_tag'] != parent
            or any(r['unit']['node_kind'].endswith('_title')
                   for r in semantic if preceding['location']['byte_end'] < r['location']['byte_start']
                   < location['byte_start'])):
        raise RecordError('native prose crosses its actual Section boundary')

    # The complete frozen batch must itself supply a real matching anchor.
    # A historical parent or a unique unlabelled string is not that anchor.
    owner_headings = [r for r in semantic if r['owner_tag'] == owner
                      and r['parent_tag'] == parent and r['unit']['node_kind'] in
                      (HEADINGS | ({'title_title'} if phantom else set()))]
    if len(owner_headings) != 1:
        raise RecordError('native prose lacks its unique actual owning heading and Section')
    anchors = [g for g in groups if g['kind'] in STATEMENTS | {'proof'} | HEADINGS
               | ({'chapter_title'} if phantom else set())
               and g['input_unit_ids'] and all(i in order for i in g['input_unit_ids'])
               and order.index(g['input_unit_ids'][-1]) < start]
    bound = None
    for anchor in reversed(anchors):
        candidates = [r for r in semantic if r['owner_tag'] == anchor['owner_tag']
                      and r['unit']['node_kind'] == legacy_heading_kind(anchor, units)
                      and int(r['semantic_path'].rsplit('/', 1)[1]) == (anchor['ordinal'] or 1)
                      and r['parent_tag'] == parent]
        if len(candidates) != 1:
            continue
        native = containers.select(_selector(containers, chapter, candidates[0]))
        if native['location']['byte_end'] > location['byte_start']:
            continue
        original = ''.join(source_tex(units[order.index(i)]) for i in anchor['input_unit_ids'])
        b = prose_signature(native['fragment'], containers, chapter)
        initial = []
        for repair in sorted((r for r in presentation_repairs
                              if r['kind'] in {'initial-noindent', 'initial-list-opening'}),
                             key=lambda r: r['signature_index']):
            if repair['signature_index'] != len(initial):
                break
            initial.append(repair['replacement'])
        anchor_options = [(original, [])]
        for size in range(1, len(initial) + 1):
            suffix = r'[ \t\r\n]*' + r'[ \t\r\n]*'.join(re.escape(v) for v in initial[:size]) + r'[ \t\r\n]*\Z'
            match = re.search(suffix, original)
            if match:
                anchor_options.append((original[:match.start()], initial[:size]))
        found = None
        for core, detached in anchor_options:
            if detached and (anchor['kind'] not in HEADINGS
                    or raw[native['location']['byte_end']:location['byte_start']].strip(b' \t\r\n')):
                continue
            try:
                core_signature = prose_signature(core, containers, chapter)
            except RecordError:
                continue
            if core_signature == b:
                found = core_signature + [['protected', value] for value in detached], detached
                break
        header_witness = None
        if phantom and anchor['kind'] == 'chapter_title':
            header_witness = native_document_header_witness(containers, units, anchor, native)
            # Historical chapter wrappers are not part of the current source
            # macro grammar. The header witness verifies the complete title and
            # original suffix; bind its original bytes without reclassifying it.
            found = original, []
        if found and all(u['parent_tag'] in {parent, anchor['owner_tag']} for u in members):
            a, detached = found
            bound = dict(input_unit_ids=anchor['input_unit_ids'], selector=native['selector'],
                         fragment_hash=native['location']['fragment_hash'], signature_hash=sha256_value(a),
                         native_signature_hash=sha256_value(b), detached_layout=detached)
            if header_witness is not None:
                bound['document_header'] = header_witness
            break
    if bound is None:
        raise RecordError('native prose lacks a complete corresponding anchor in its frozen batch')

    count = 0
    def corresponds(fragment):
        try:
            candidate = prose_signature(fragment, containers, chapter)
            _correspondence(old_signature, candidate, members)
            return True
        except RecordError:
            return False
    if kind == 'paragraph':
        for row in rows:
            if row['unit']['node_kind'] != 'paragraph':
                continue
            loc = row['location']
            count += corresponds(raw[loc['byte_start']:loc['byte_end']].decode())
    else:
        for index, row in enumerate(semantic):
            end = (semantic[index + 1]['location']['byte_start'] if index + 1 < len(semantic)
                   else containers.closings.get(chapter))
            begin = row['location']['byte_end']
            if row['unit']['node_kind'] == 'title_title':
                begin = containers.select(_selector(containers,chapter,row))['location']['byte_end']
            if end is None or end <= begin:
                continue
            fragment = raw[begin:end].decode()
            count += corresponds(fragment)
    if count != 1:
        raise RecordError('native prose correspondence is not unique in the locked chapter')
    native_anchor = lambda value: None if value is None else dict(
        selector=value['selector'], fragment_hash=value['location']['fragment_hash'])
    return dict(input_unit_ids=ids, historical_parent_tags=list(dict.fromkeys(u['parent_tag'] for u in members)),
                frozen_anchor=bound, native_before=native_anchor(preceding), native_after=native_anchor(following),
                native_interval=dict(start=location['byte_start'], end=location['byte_end']),
                historical_signature_hash=sha256_value(old_signature), native_signature_hash=sha256_value(signature),
                projected_signature_hash=sha256_value(projected_signature), presentation_repairs=presentation_repairs)


def labelled_math_prose_groups(containers, units):
    """Propose a whole interval from its actual equation, never its old ID."""
    if (len(units) != 1 or units[0]['node_kind'] != 'paragraph'
            or units[0]['schema_version'] != 1 or validate_regions(units[0])):
        return []
    old = units[0]
    equations = [m for m in complete_math_nodes(old) if m.startswith(r'\begin{equation}')]
    if len(equations) != 1:
        return []
    historical = equations[0]
    try:
        stream = nodes(historical)
        if delimiter_kind(historical) != 'environment':
            return []
    except ValueError:
        return []
    labels = [n for n in stream if n['token'].startswith(r'\label{')]
    if (len(labels) != 1 or labels[0]['depth'] != 0
            or labels[0]['environments'] != ['equation']):
        return []
    label = labels[0]['token'][7:-1]
    chapter = old['chapter'];tags = containers.english.tags
    qualified = label if label.startswith(chapter+'-') else chapter+'-'+label
    if tags.get(qualified) != old['parent_tag']:
        return []
    local = qualified[len(chapter)+1:]
    native = historical[:labels[0]['start']] + r'\label{'+local+'}' + historical[labels[0]['end']:]
    raw,rows,_ = containers.document(chapter)
    if raw.count(native.encode()) != 1:
        return []
    position = raw.index(native.encode())
    headings = [r for r in rows if r['unit']['node_kind'] in HEADINGS
                and r['location']['byte_end'] <= position]
    if not headings:
        return []
    heading = headings[-1];result = []
    for ordinal in range(1,len(rows)+1):
        selector = {**_selector(containers,chapter,heading),'kind':'prose_block','ordinal':ordinal}
        try:
            selected = containers.select(selector)
        except RecordError as exc:
            if 'no unique complete semantic interval' in str(exc):
                break
            continue
        if complete_math_nodes(selected['inventory_unit']).count(native) != 1:
            continue
        result.append(dict(input_unit_ids=[old['unit_id']],file=chapter+'.tex',
            owner_tag=selector['owner_tag'],kind='prose_block',ordinal=ordinal,
            boundary_witness=selected['boundary_witness'], labelled_math=dict(
                tag=old['parent_tag'],historical_label=label,native_label=local,
                historical_math=historical,native_math=native)))
    return result


def native_labelled_math_prose_witness(containers, units, group, selected):
    old = units[0];equation = group['labelled_math'];selector = selected['selector']
    if (len(units) != 1 or old['source_commit'] != selected['source_commit']
            or old['chapter']+'.tex' != selector['file'] or group['input_unit_ids'] != [old['unit_id']]
            or any(group[k] != selector[k] for k in ['file','owner_tag','kind','ordinal'])
            or old['parent_tag'] != equation['tag']):
        raise RecordError('labelled mathematical prose requires its complete single frozen paragraph')
    original = source_tex(old)
    if original.count(equation['historical_math']) != 1:
        raise RecordError('labelled mathematical anchor is repeated or absent from old source')
    normalized = original.replace(equation['historical_math'],equation['native_math'],1)
    historical = prose_signature(original,containers,old['chapter'])
    projected,repairs = _correspondence(prose_signature(normalized,containers,old['chapter']),
        prose_signature(selected['fragment'],containers,old['chapter']),units)
    raw,rows,_ = containers.document(old['chapter']);location = selected['location']
    semantic = [r for r in rows if r['unit']['node_kind'] in STATEMENTS|{'proof'}
                or r['unit']['node_kind'].endswith('_title')]
    before = [r for r in semantic if r['location']['byte_end'] <= location['byte_start']]
    after = [r for r in semantic if r['location']['byte_start'] >= location['byte_end']]
    if not before or not after:
        raise RecordError('labelled mathematical prose requires two real semantic boundaries')
    preceding = containers.select(_selector(containers,old['chapter'],before[-1]))
    following = containers.select(_selector(containers,old['chapter'],after[0]))
    if (preceding['location']['byte_end'] != location['byte_start']
            or following['location']['byte_start'] != location['byte_end']
            or preceding['selector']['parent_tag'] != selector['parent_tag']
            or following['selector']['parent_tag'] != selector['parent_tag']):
        raise RecordError('labelled mathematical prose is not the whole actual Section interval')
    position = raw.index(equation['native_math'].encode())
    native_anchor = lambda s: dict(selector=s['selector'],fragment_hash=s['location']['fragment_hash'])
    return dict(input_unit_ids=[old['unit_id']],historical_parent_tags=[old['parent_tag']],
        frozen_anchor=dict(equation,historical_math_hash=byte_hash(equation['historical_math']),
            native_math_hash=byte_hash(equation['native_math']),
            native_byte_span=dict(start=position,end=position+len(equation['native_math'].encode()))),
        native_before=native_anchor(preceding),native_after=native_anchor(following),
        native_interval=dict(start=location['byte_start'],end=location['byte_end']),
        historical_signature_hash=sha256_value(historical),projected_signature_hash=sha256_value(projected),
        native_signature_hash=sha256_value(prose_signature(selected['fragment'],containers,old['chapter'])),
        presentation_repairs=repairs)
