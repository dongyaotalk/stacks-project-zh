"""Opt-in complete math frames from the five 2026-07-28 locked P0 chapters."""
from functools import lru_cache
import json
import re

from .math_text_p0_catalog import SOURCE_COMMIT, SOURCE_FRAMES, SOURCE_HASHES, SOURCE_WITNESSES, TRANSLATED_ROLES
from .records import RecordError
from .source_reextractions import _git_bytes, byte_hash

PLAIN_USAGE = 'p0-locked-math-frame'
COMPONENT_USAGE = 'p0-etale-frame-component'
SYMBOL_USAGE = 'p0-locked-math-symbol'
USAGES = {'plain': PLAIN_USAGE, 'component': COMPONENT_USAGE}
SECTION = 'p0_locked_math_frames'
ETALE_LITERAL = r" is \'etale"
ETALE_SEPARATOR = r"\'e"
ETALE_COMPONENTS = [' is ', 'tale']


def policy_chapters(text):
    chapters = set()
    active = seen = False
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if not line.startswith(' '):
            active = line.partition(':')[0] == SECTION
            if active:
                if seen or line != SECTION + ':':
                    raise ValueError('invalid or duplicate P0 math-frame policy section')
                seen = True
        elif active:
            match = re.fullmatch(r'  ([a-z-]+): "(sha256:[0-9a-f]{64})"', line)
            if not match or SOURCE_HASHES.get(match[1]) != match[2] or match[1] in chapters:
                raise ValueError('P0 math-frame policy requires unique exact locked chapter bytes')
            chapters.add(match[1])
    if seen and not chapters:
        raise ValueError('empty P0 math-frame policy section')
    return frozenset(chapters)


def natural_rules(chapters):
    rules = {}
    for chapter in sorted(chapters):
        for n, (role, witness) in enumerate(SOURCE_WITNESSES[chapter].items(), 1):
            kind, command, literal = role
            label, container, ordinal = witness
            rule = dict(usage=USAGES[kind], command=command, literal=literal,
                        source_label=label, witness_kind=container, witness_ordinal=ordinal,
                        p0_chapter=chapter)
            if kind == 'component':
                rule.update(slot_schema_version=3, components=ETALE_COMPONENTS, separator=ETALE_SEPARATOR)
            rules[f'p0-frame-{chapter}-{n:02d}'] = rule
    return rules


def verify_chapters(chapters, english):
    if chapters and english.commit != SOURCE_COMMIT:
        raise RecordError('P0 math frames require their recorded English commit')
    for chapter in chapters:
        if byte_hash(_git_bytes(english.harvest, english.commit, chapter + '.tex')) != SOURCE_HASHES[chapter]:
            raise RecordError('P0 math-frame chapter differs from its recorded locked bytes: ' + chapter)
        labels = {role[3] for roles in SOURCE_FRAMES[chapter].values() for role in roles.values()}
        if any(not english.tags.get(label) for label in labels):
            raise RecordError('P0 math-frame source label is missing from locked Tags: ' + chapter)
    return chapters


@lru_cache(maxsize=256)
def _source_roles(source, chapter):
    return SOURCE_FRAMES.get(chapter, {}).get(byte_hash(source), {})


def source_match(source, index, node, chapter, kind):
    role = _source_roles(source, chapter).get(index)
    return role is not None and role[:3] == (kind, node.get('command'), node.get('value'))


def notation(source, start, chapter, command, value):
    if not _source_roles(source, chapter):
        return None
    from .math_text import nodes
    stream = nodes(source)
    for index, node in enumerate(stream):
        if node['start'] == start and source_match(source, index, node, chapter, 'symbol'):
            if (node['command'], node['value']) != (command, value):
                return None
            label = _source_roles(source, chapter)[index][3]
            return SYMBOL_USAGE, source[:start] + source[node['end']:], label
    return None


def _shape(source, stream):
    # Full skeleton projection performs the final byte comparison. This
    # fingerprint permits the same role lookup after independently typed
    # parameters in a mixed frame have been translated.
    pieces, cursor = [], 0
    for node in stream:
        if node.get('command') not in {'text', 'textit'}:
            continue
        pieces.append(source[cursor:node['parameter_start']])
        cursor = node['parameter_end']
    pieces.append(source[cursor:])
    return byte_hash(json.dumps(pieces, ensure_ascii=False, separators=(',', ':')))


def usage(source, stream, index, kind):
    from .math_text import plain_text
    node = stream[index]
    if not 0 < index < len(stream) - 1 or node.get('command') != 'text':
        return None
    resolved = next((role for role, value in USAGES.items() if value == kind), None)
    value = node['value']
    if resolved == 'plain':
        valid = plain_text(value)
    elif resolved == 'component':
        leaves = value.split(ETALE_SEPARATOR)
        valid = len(leaves) == 2 and all(plain_text(leaf) for leaf in leaves)
    else:
        return None
    if not valid or (index, resolved) not in TRANSLATED_ROLES.get(_shape(source, stream), ()):
        return None
    return {'before': source[stream[index-1]['start']:node['start']],
            'after': source[node['end']:stream[index+1]['end']], 'environments': node['environments']}
