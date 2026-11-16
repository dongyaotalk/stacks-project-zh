"""Opt-in finite item-label tokens; never expand a TeX integer expression.

This helper grants no production policy or extraction permission by itself.
An explicit caller-owned whitelist and the complete item context are required.
"""
LABELS = tuple(r'\item[(\romannumeral' + str(i) + ')]' for i in range(1, 5))


def validate_literals(literals):
    if (not isinstance(literals, (list, tuple)) or not literals
            or any(not isinstance(v, str) or v not in LABELS for v in literals)
            or len(literals) != len(set(literals))):
        raise ValueError('numeric item labels require unique complete witnessed literals')
    return tuple(literals)


def label_end(text, start, *, end=None, allowed=()):
    if (not isinstance(text, str) or type(start) is not int
            or (end is not None and type(end) is not int)):
        return None
    stop = len(text) if end is None else end
    if not 0 <= start < stop <= len(text) or not allowed:
        return None
    for literal in validate_literals(allowed):
        finish = start + len(literal)
        if finish <= stop and text[start:finish] == literal:
            return finish
    return None


def label_metadata(text, start, finish):
    """Bind the entire token, including command, digit and optional argument."""
    literal = text[start:finish]
    if literal not in LABELS or label_end(text, start, end=finish, allowed=[literal]) != finish:
        raise ValueError('not a complete supported numeric item label')
    ordinal = LABELS.index(literal) + 1
    return dict(source=literal, command='romannumeral', integer_source=str(ordinal),
                source_byte_span=dict(start=len(text[:start].encode()), end=len(text[:finish].encode())),
                usage='finite-roman-item-label')


"""Unapplied finite policy and complete source-anchor integration.

This build-only draft grants no production extraction or candidate permission.
"""
import json
import re

from .records import RecordError

SECTION = 'locked_numeric_item_labels'
USAGE = 'finite-roman-item-label'


def policy_registry(text):
    entries = {}
    active = seen = False
    entry = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if line.lstrip().partition(':')[0].strip() == SECTION and line != SECTION + ':':
            raise RecordError('invalid numeric item policy section')
        if active and line.startswith('\t'):
            raise RecordError('invalid numeric item policy indentation')
        if not line.startswith(' '):
            active = line.partition(':')[0] == SECTION
            entry = None
            if active:
                if seen:
                    raise RecordError('duplicate numeric item policy section')
                seen = True
        elif active:
            match = re.fullmatch(r'  ([a-z][a-z0-9-]*):', line)
            if match:
                entry = match[1]
                if entry in entries:
                    raise RecordError('duplicate numeric item policy entry')
                entries[entry] = {}
            else:
                field = re.fullmatch(r'    (literals|usage|source_label): (.+)', line)
                if not field or entry is None or field[1] in entries[entry]:
                    raise RecordError('invalid or duplicate numeric item policy field')
                try:
                    entries[entry][field[1]] = json.loads(field[2])
                except json.JSONDecodeError as exc:
                    raise RecordError('numeric item policy fields require JSON values') from exc
    if seen and not entries:
        raise RecordError('empty numeric item policy section')
    if len(entries) > 1:
        raise RecordError('numeric item policy requires one finite declaration')
    for rule in entries.values():
        if set(rule) != {'literals', 'usage', 'source_label'} or rule['usage'] != USAGE:
            raise RecordError('incomplete or unsupported numeric item policy')
        if not isinstance(rule['literals'], list):
            raise RecordError('numeric item literals require an array')
        try:
            values = validate_literals(rule['literals'])
        except ValueError as exc:
            raise RecordError(str(exc)) from exc
        if values != LABELS:
            raise RecordError('numeric item policy requires the complete witnessed four-label order')
        if not isinstance(rule['source_label'], str) or not re.fullmatch(
                r'[a-z][a-z0-9_-]*-[A-Za-z][A-Za-z0-9_-]*', rule['source_label']):
            raise RecordError('numeric item source label invalid')
    return entries


def resolve_policy_witnesses(policy, english):
    """Independently bind a unique complete labelled locked-Git statement.

    Inventory diagnostics preserve the unsupported old labels while recovering
    their source bytes. Only the opt-in Scanner scaffold can subsequently lock
    those exact literals; this function never expands or executes source TeX.
    """
    from .extraction import Policy, chapter_inventory
    from .source_reextractions import _git_bytes, byte_hash, source_tex

    policy.numeric_item_witnesses = {}
    if not policy.numeric_item_rules:
        return
    legacy = Policy(policy.raw, natural_text_enabled=False)
    legacy.numeric_item_rules = {}
    legacy.numeric_item_witnesses = {}
    verified = {}
    for key, rule in policy.numeric_item_rules.items():
        label = rule['source_label']
        tag = english.tags.get(label)
        if not tag or sum(value == tag for value in english.tags.values()) != 1:
            raise RecordError('numeric item witness has no unique real permanent Tag')
        # This finite syntax contract is anchored to the one locked defos lemma.
        if label != 'defos-lemma-lift-complex' or tag != '0DIT':
            raise RecordError('numeric item witness is outside the finite labelled source contract')
        raw = _git_bytes(english.harvest, english.commit, 'defos.tex')
        rows = chapter_inventory('defos', raw, english.commit, english.tags, legacy)[0]
        anchors = [row for row in rows if row['owner_tag'] == tag
                   and row['unit']['node_kind'] == 'lemma'
                   and row['semantic_path'] == 'lemma/0001']
        if len(anchors) != 1:
            raise RecordError('numeric item witness lacks its unique complete labelled lemma')
        row = anchors[0]
        source = source_tex(row['unit'])
        location = row['location']
        if raw[location['byte_start']:location['byte_end']].decode('utf-8') != source:
            raise RecordError('numeric item witness does not replay its complete locked-Git container')
        witnesses = []
        for literal in LABELS:
            if source.count(literal) != 1:
                raise RecordError('numeric item witness requires every complete label exactly once')
            start = source.index(literal)
            finish = label_end(source, start, allowed=rule['literals'])
            metadata = label_metadata(source, start, finish)
            span = metadata['source_byte_span']
            first = location['byte_start'] + span['start']
            last = location['byte_start'] + span['end']
            if raw[first:last].decode('utf-8') != literal:
                raise RecordError('numeric item witness label span differs from locked Git')
            witnesses.append({'source': literal, 'source_hash': byte_hash(literal),
                              'git_byte_span': {'start': first, 'end': last}})
        if [w['git_byte_span']['start'] for w in witnesses] != sorted(
                w['git_byte_span']['start'] for w in witnesses):
            raise RecordError('numeric item witness complete labels are out of order')
        verified[key] = {'source_commit': english.commit, 'file': 'defos.tex',
                         'owner_tag': tag, 'owner_label': label,
                         'kind': 'lemma', 'ordinal': 1,
                         'blob_hash': byte_hash(raw), 'location': location,
                         'witnesses': witnesses}
    policy.numeric_item_witnesses = verified
