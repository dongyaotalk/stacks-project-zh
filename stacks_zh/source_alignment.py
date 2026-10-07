"""Read-only correspondence and repair planning; never adopts source or text."""
from __future__ import annotations

import collections
import difflib
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .extraction import COMMAND, ENVIRONMENT, Policy, Scanner, VERSION as EXTRACTION_VERSION, chapter_inventory
from .records import RecordError, load_jsonl
from .source_integrity import audit_repository_source, permanent_tag_mapping
from .source_reextractions import LockedEnglish, _git_bytes, _comparison, byte_hash, proof_groups, source_tex, audit_repository_proofs
from .source_terms import audit_repository_terms

VERSION = 'source-alignment-v2'
OWNED_VERSIONS = {'source-alignment-v1', VERSION}
WORDS = re.compile(r'[^\W_]+|[^\s]', re.UNICODE)
REFERENCE = re.compile(r'\\(label|ref|eqref|pageref)\{([^{}\n]+)\}')


@dataclass(frozen=True)
class Token:
    key: tuple[str, ...]
    start: int
    end: int


def canonical_tokens(text: str, chapter: str, tags: dict[str, str], policy: Policy) -> list[Token]:
    """Locate equivalent presentation only; opaque math/literal bytes stay exact.

    Comments join text without their end-of-line. Text word boundaries remain
    significant, so removing whitespace cannot turn ``a b`` into ``ab``.
    """
    scanner, result, buffer, positions = Scanner(text, policy), [], [], []

    def flush():
        value = ''.join(buffer)
        for match in WORDS.finditer(value):
            result.append(Token(('text', match.group()), positions[match.start()], positions[match.end() - 1] + 1))
        buffer.clear(); positions.clear()

    i = 0
    while i < len(text):
        char = text[i]
        if char == '%':
            i = scanner.comment_end(i)
        elif char == '$' or text.startswith((r'\[', r'\('), i):
            flush(); end = scanner.math_end(i)
            result.append(Token(('math', text[i:end]), i, end)); i = end
        elif char == '\\':
            flush()
            env = ENVIRONMENT.match(text, i)
            ref = REFERENCE.match(text, i)
            command = COMMAND.match(text, i)
            if env:
                if env[1] == 'begin' and env[2] in policy.math | policy.literal | policy.metadata:
                    end = scanner.environment_end(i)
                    result.append(Token(('math' if env[2] in policy.math else 'locked', text[i:end]), i, end)); i = end
                else:
                    result.append(Token(('environment', env[1], env[2]), i, env.end())); i = env.end()
            elif ref:
                label = ref[2]
                qualified = label if label in tags else chapter + '-' + label
                target = tags.get(qualified)
                key = ('reference', ref[1], target) if target else ('reference-raw', ref.group())
                result.append(Token(key, i, ref.end())); i = ref.end()
            elif command:
                name, end = command.group()[1:], command.end()
                if name in {'verb', 'Verb'}:
                    if text[end:end + 1] == '*':
                        end += 1
                    delimiter = text[end:end + 1]
                    closing = text.find(delimiter, end + 1) if delimiter and not delimiter.isspace() else -1
                    if closing < 0:
                        raise RecordError('unclosed inline literal')
                    end = closing + 1
                    kind = 'locked'
                elif (policy.commands.get(name) == 'locked' and name != ' '
                      or name in {'index', 'xymatrix'}):
                    end, _ = scanner.command_arguments(i, optional=True)
                    kind = 'locked'
                elif name == 'href':
                    _, args = scanner.command_arguments(i, count=2)
                    end = args[0][1]
                    kind = 'locked'
                elif name in policy.accents:
                    end = scanner.skip_space(end)
                    if end >= len(text):
                        raise RecordError('missing accent argument')
                    end = scanner.argument_end(end) if text[end] == '{' else end + 1
                    kind = 'locked'
                else:
                    kind = 'command'
                result.append(Token((kind, text[i:end]), i, end)); i = end
            else:
                raise RecordError('incomplete source control sequence')
        else:
            buffer.append(char); positions.append(i); i += 1
    flush()
    return result


def _occurrences(haystack: list[Token], needle: list[Token]):
    if not needle:
        return []
    keys = [t.key for t in needle]
    result = []
    for i, token in enumerate(haystack):
        if token.key == keys[0] and i + len(keys) <= len(haystack):
            if all(haystack[i + k].key == key for k, key in enumerate(keys)):
                result.append((haystack[i].start, haystack[i + len(keys) - 1].end))
    return result


def _labels(text: str, chapter: str, tags: dict[str, str], policy: Policy):
    """Literal and metadata examples cannot witness a secondary owner."""
    scanner, found, i = Scanner(text, policy), set(), 0
    while i < len(text):
        if text[i] == '%':
            i = scanner.comment_end(i); continue
        if text[i] == '\\':
            env = ENVIRONMENT.match(text, i)
            if env and env[1] == 'begin' and env[2] in policy.literal | policy.metadata:
                i = scanner.environment_end(i); continue
            ref = REFERENCE.match(text, i)
            if ref:
                if ref[1] == 'label':
                    label = ref[2] if ref[2] in tags else chapter + '-' + ref[2]
                    if label in tags:
                        found.add(tags[label])
                i = ref.end(); continue
            command = COMMAND.match(text, i)
            if command and command.group()[1:] in {'verb', 'Verb'}:
                end = command.end() + (text[command.end():command.end() + 1] == '*')
                delimiter = text[end:end + 1]
                close = text.find(delimiter, end + 1) if delimiter and not delimiter.isspace() else -1
                if close < 0:
                    raise RecordError('unclosed inline literal')
                i = close + 1; continue
            if command:
                name = command.group()[1:]
                if (policy.commands.get(name) == 'locked' and name != ' ') or name == 'index':
                    i, _ = scanner.command_arguments(i, optional=True)
                    continue
                if name == 'href':
                    _, args = scanner.command_arguments(i, count=2)
                    i = args[0][1]; continue
            i = command.end() if command else i + 1
        else:
            i += 1
    return found


class Corpus:
    def __init__(self, entries: list[dict[str, Any]], tags: dict[str, str], policy: Policy,
                 *, source_containers=None):
        self.tags, self.policy, self.entries = tags, policy, {}
        self.source_containers = source_containers
        self.owners: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
        self.proofs: dict[tuple[str, str, int], list[str]] = collections.defaultdict(list)
        for row in entries:
            identifier = row['inventory_id']
            if identifier in self.entries:
                raise RecordError('duplicate inventory container')
            tex = row.get('_window_tex', source_tex(row['unit']))
            item = {**row, 'location': row.get('_window_location', row['location']),
                    'unit_location': row['location'],
                    'tex': tex, 'tokens': canonical_tokens(tex, row['unit']['chapter'], tags, policy)}
            self.entries[identifier] = item
            owners = _labels(tex, row['unit']['chapter'], tags, policy)
            if row['owner_tag']:
                owners.add(row['owner_tag'])
            for owner in owners:
                self.owners[(row['unit']['chapter'], owner)].append(identifier)
            if row['unit']['node_kind'] == 'proof' and row['owner_tag']:
                number = int(row['semantic_path'].split('/')[-1])
                self.proofs[(row['unit']['chapter'], row['owner_tag'], number)].append(identifier)

    def match(self, unit: dict[str, Any], mapped_id: str, proof: dict[str, Any] | None = None):
        tex = source_tex(unit)
        result = {'unit_id': unit['unit_id'], 'proposed_unit_id': mapped_id,
                  'chapter': unit['chapter'], 'current_source_tex_hash': byte_hash(tex)}
        tag = re.match(r'tag:([0-9A-Z]+)(?::|$)', mapped_id)
        if proof:
            owner = proof.get('statement_tag')
            identifiers = self.proofs.get((unit['chapter'], owner, proof['proof_index']), [])
        else:
            owner = tag[1] if tag else None
            identifiers = [identifier for identifier in self.owners.get((unit['chapter'], owner), [])
                           if self.entries[identifier]['unit']['node_kind'] != 'proof']
        result['owner_tag'] = owner
        result['source_containers'] = [
            {'inventory_id': identifier, 'location': self.entries[identifier]['location'],
             'container_location': self.entries[identifier]['unit_location'],
             'semantic_path': self.entries[identifier]['semantic_path'],
             'extractor_state': self.entries[identifier]['state'],
             'source_excerpt': self.entries[identifier]['tex'][:400]}
            for identifier in identifiers]
        prose = re.fullmatch(r'tag:([0-9A-Z]+):prose-([0-9]{4})', unit['unit_id'])
        if prose:
            result['containers'] = identifiers
            try:
                if (unit['node_kind'] != 'paragraph' or proof is not None
                        or mapped_id != unit['unit_id'] or owner != prose[1]):
                    raise RecordError('canonical prose identity requires its real paragraph owner')
                if self.source_containers is None:
                    raise RecordError('complete prose correspondence requires locked-Git containers')
                native = self.source_containers
                if unit['source_commit'] != native.english.commit or self.tags != native.english.tags:
                    raise RecordError('complete prose commit/Tag index differs from locked Git')
                labels = [label for label, tag in native.english.tags.items()
                          if tag == owner and label.startswith(unit['chapter'] + '-')]
                if len(labels) != 1:
                    raise RecordError('complete prose owner has no unique real chapter label')
                selector = {'file': unit['chapter'] + '.tex', 'owner_tag': owner,
                    'owner_label': labels[0], 'parent_tag': unit['parent_tag'],
                    'kind': 'prose_block', 'ordinal': int(prose[2])}
                selected = native.select(selector)
                evidence = {key: selected[key] for key in ('source_commit', 'selector',
                    'location', 'blob_oid', 'blob_hash', 'macro_policy_hash', 'boundary_witness')}
                if tex != selected['fragment']:
                    return {**result, 'status': 'SOURCE_DIFFERENCE', 'matches': [],
                        'native_container': evidence,
                        'reason': 'complete prose TeX differs from the full locked-Git fragment'}
                return {**result, 'status': 'BYTE_EXACT', 'location': selected['location'],
                    'native_container': evidence, 'extractor_state': 'READY',
                    'note': 'complete Git location evidence only; no adoption or audit waiver'}
            except RecordError as exc:
                return {**result, 'status': 'UNSUPPORTED', 'reason': str(exc), 'matches': []}
        if not identifiers:
            return {**result, 'status': 'UNSUPPORTED', 'reason': 'no verified source container for this owner/proof', 'containers': []}
        try:
            needle = canonical_tokens(tex, unit['chapter'], self.tags, self.policy)
        except RecordError as exc:
            return {**result, 'status': 'UNSUPPORTED', 'reason': str(exc), 'containers': identifiers}
        matches = []
        for identifier in identifiers:
            container = self.entries[identifier]
            for start, end in _occurrences(container['tokens'], needle):
                fragment = container['tex'][start:end]
                location = container['location']
                byte_start = location['byte_start'] + len(container['tex'][:start].encode('utf-8'))
                matches.append({'inventory_id': identifier, 'location': {'file': location['file'],
                    'byte_start': byte_start, 'byte_end': byte_start + len(fragment.encode('utf-8')),
                    'fragment_hash': byte_hash(fragment)},
                    'status': 'BYTE_EXACT' if tex == fragment else 'PRESENTATION_EQUIVALENT',
                    'extractor_state': container['state']})
        # Adjacent containers may share a verified structural frame. Two
        # witnesses of the same physical source span are still one location.
        unique = {}
        for match in matches:
            loc = match['location']
            key = (loc['file'], loc['byte_start'], loc['byte_end'])
            unique.setdefault(key, {**match, 'container_witnesses': []})['container_witnesses'].append(match['inventory_id'])
        matches = list(unique.values())
        if len(matches) != 1:
            return {**result, 'status': 'AMBIGUOUS' if matches else 'SOURCE_DIFFERENCE',
                    'reason': 'multiple continuous matches' if matches else 'no continuous match with exact mathematics and text order',
                    'containers': identifiers, 'matches': matches}
        return {**result, **matches[0], 'containers': identifiers,
                'note': 'location evidence only; no adoption or audit waiver'}


def verified_inventory(root: Path, harvest: Path, inventory: Path, chapters: set[str]):
    if inventory.is_symlink() or (inventory / 'manifest.json').is_symlink():
        raise RecordError('source inventory must not be a symlink')
    english = LockedEnglish(root, harvest)
    raw_policy = (root / 'config/macro-policy.yml').read_bytes()
    policy = Policy(raw_policy.decode('utf-8'))
    manifest_bytes = (inventory / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    if (not isinstance(manifest, dict) or manifest.get('extractor_version') != EXTRACTION_VERSION
            or manifest.get('source_commit') != english.commit
            or manifest.get('macro_policy_hash') != byte_hash(raw_policy)):
        raise RecordError('source inventory version/commit/macro policy mismatch')
    expected_files = {'units.jsonl', 'segments.jsonl', 'diagnostics.jsonl', 'report.md'}
    if not isinstance(manifest.get('files'), dict) or set(manifest['files']) != expected_files:
        raise RecordError('source inventory manifest has invalid paths')
    for name, expected in manifest['files'].items():
        path = inventory / name
        if path.is_symlink() or byte_hash(path.read_bytes()) != expected:
            raise RecordError('source inventory file hash mismatch: ' + name)
    rows = []
    with (inventory / 'units.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row['unit']['chapter'] in chapters:
                rows.append(row)
    by_id = {}
    for row in rows:
        if row['inventory_id'] in by_id:
            raise RecordError('duplicate cached inventory ID')
        by_id[row['inventory_id']] = row
    validated = []
    fields = {'inventory_id', 'source_commit', 'owner_tag', 'parent_tag', 'semantic_path',
              'location', 'state', 'word_count', 'unit', 'diagnostic_count', 'math_text_classifications'}
    for chapter in sorted(chapters):
        raw = _git_bytes(harvest, english.commit, chapter + '.tex')
        actual, _, _ = chapter_inventory(chapter, raw, english.commit, english.tags, policy)
        for index, row in enumerate(actual):
            cached = by_id.pop(row['inventory_id'], None)
            if cached is None or any(k not in cached or cached[k] != row[k] for k in fields):
                raise RecordError('cached source differs from locked Git extraction: ' + row['inventory_id'])
            # Old render wrappers can carry adjacent, non-language frame bytes
            # (noindent, list opening/closing, chapter infrastructure). Preserve
            # those exact bytes without borrowing another owner's prose.
            start, end = row['location']['byte_start'], row['location']['byte_end']
            if index:
                previous = actual[index - 1]
                start = previous['location']['byte_end']
                if previous['owner_tag'] == row['owner_tag'] and row['owner_tag']:
                    previous_tex = source_tex(previous['unit'])
                    previous_tokens = canonical_tokens(previous_tex, chapter, english.tags, policy)
                    leaves = [t for t in previous_tokens if t.key[0] in {'text', 'math', 'locked'}]
                    if leaves:
                        start = previous['location']['byte_start'] + len(previous_tex[:leaves[-1].end].encode('utf-8'))
            if index + 1 < len(actual):
                following = actual[index + 1]
                end = following['location']['byte_start']
                if following['owner_tag'] == row['owner_tag'] and row['owner_tag']:
                    following_tex = source_tex(following['unit'])
                    following_tokens = canonical_tokens(following_tex, chapter, english.tags, policy)
                    leaves = [t for t in following_tokens if t.key[0] in {'text', 'math', 'locked'}]
                    if leaves:
                        end = following['location']['byte_start'] + len(following_tex[:leaves[0].start].encode('utf-8'))
            window = raw[start:end].decode('utf-8')
            validated.append({**row, '_window_tex': window,
                '_window_location': {**row['location'], 'byte_start': start, 'byte_end': end,
                    'line_start': raw[:start].count(b'\n') + 1,
                    'line_end': raw[:max(start, end - 1)].count(b'\n') + 1,
                    'fragment_hash': byte_hash(window)}})
    if by_id:
        raise RecordError('source inventory contains extra current-chapter containers')
    return english, policy, validated, byte_hash(manifest_bytes)


def _read_facts(root: Path):
    batches, hashes, seen = {}, {}, set()
    for path in sorted((root / 'translation-data/units').glob('*.jsonl')):
        rows = load_jsonl(path)
        for row in rows:
            if row['unit_id'] in seen:
                raise RecordError('duplicate current source unit: ' + row['unit_id'])
            seen.add(row['unit_id'])
        batches[path.stem] = rows
        hashes[path.relative_to(root).as_posix()] = byte_hash(path.read_bytes())
    if not batches:
        raise RecordError('no current source units')
    for path in sorted((root / 'translation-data/candidates').glob('*/*.jsonl')):
        hashes[path.relative_to(root).as_posix()] = byte_hash(path.read_bytes())
    for name in ('upstream.lock', 'config/macro-policy.yml', 'config/source-terms.json', 'config/glossary.yml'):
        path = root / name
        if path.is_file():
            hashes[name] = byte_hash(path.read_bytes())
    return batches, hashes


def align_batches(batches: dict[str, list[dict[str, Any]]], corpus: Corpus):
    result, maps = [], {}
    for batch, units in batches.items():
        try:
            mapping = permanent_tag_mapping(units, corpus.tags)
            groups, group_errors = proof_groups(units, corpus.tags)
            if group_errors:
                raise RecordError('; '.join(group_errors))
            selectors = {}
            for group in groups:
                if group['selector'] is None:
                    raise RecordError('current proof has no verified statement owner')
                for unit in group['units']:
                    selectors[unit['unit_id']] = group['selector']
        except RecordError as exc:
            result.extend({'batch': batch, 'unit_id': u['unit_id'], 'proposed_unit_id': None,
                'status': 'UNSUPPORTED', 'reason': str(exc), 'chapter': u['chapter'],
                'current_source_tex_hash': byte_hash(source_tex(u))} for u in units)
            continue
        maps[batch] = mapping
        previous: dict[str, int] = {}
        for unit in units:
            entry = corpus.match(unit, mapping[unit['unit_id']], selectors.get(unit['unit_id']))
            entry['batch'] = batch
            if entry['status'] in {'BYTE_EXACT', 'PRESENTATION_EQUIVALENT'}:
                location = entry['location']
                if location['byte_start'] < previous.get(location['file'], -1):
                    entry.update(status='AMBIGUOUS', reason='source span overlaps or precedes a prior current unit')
                else:
                    previous[location['file']] = location['byte_end']
            result.append(entry)
    return result, maps


def _proof_diagnostics(root: Path, english: LockedEnglish, policy: Policy, proof_report: dict[str, Any]):
    details = []
    by_batch = {}
    for entry in proof_report['proofs']:
        if entry['status'] != 'mismatch':
            continue
        batch = entry['batch']
        if batch not in by_batch:
            by_batch[batch] = {u['unit_id']: u for u in load_jsonl(root / 'translation-data/units' / (batch + '.jsonl'))}
        current = ''.join(source_tex(by_batch[batch][identifier]) for identifier in entry['unit_ids'])
        original = english.select(entry['selector'])
        old_nodes, old_prose = _comparison(current)
        new_nodes, new_prose = _comparison(original)
        changes = []
        for action, a, b, c, d in difflib.SequenceMatcher(None, old_nodes, new_nodes, autojunk=False).get_opcodes():
            if action != 'equal':
                changes.append({'action': action, 'current_nodes': old_nodes[a:b], 'english_nodes': new_nodes[c:d],
                                'current_range': [a, b], 'english_range': [c, d]})
        chapter = by_batch[batch][entry['unit_ids'][0]]['chapter']
        presentation_equal = ([t.key for t in canonical_tokens(current, chapter, english.tags, policy)]
            == [t.key for t in canonical_tokens(original, chapter, english.tags, policy)])
        details.append({'batch': batch, 'unit_ids': entry['unit_ids'], 'selector': entry['selector'],
                        'classification': 'PRESENTATION_EQUIVALENT' if presentation_equal else 'SOURCE_DIFFERENCE',
                        'node_changes': changes, 'natural_prose_diff': list(difflib.unified_diff(old_prose.splitlines(), new_prose.splitlines(), lineterm='')),
                        'audit_status': 'mismatch', 'waived': False})
    return details


def build_alignment(root: Path, harvest: Path, inventory: Path):
    batches, inputs = _read_facts(root)
    chapters = {u['chapter'] for rows in batches.values() for u in rows}
    english, policy, entries, inventory_hash = verified_inventory(root, harvest, inventory, chapters)
    if any(u['source_commit'] != english.commit for rows in batches.values() for u in rows):
        raise RecordError('current unit source differs from locked English commit')
    from .source_containers import Containers
    native = Containers(root, harvest)
    corpus = Corpus(entries, english.tags, policy, source_containers=native)
    matches, maps = align_batches(batches, corpus)
    terms, term_errors = audit_repository_terms(root, harvest)
    # The standalone audit accepts a tags path. Supply immutable Git bytes,
    # keeping dirty harvest files out of the combined report as well.
    with tempfile.TemporaryDirectory(prefix='stacks-zh-alignment-tags-') as temporary:
        tags_path = Path(temporary) / 'tags'
        tags_path.write_bytes(_git_bytes(harvest, english.commit, 'tags/tags'))
        source, source_errors = audit_repository_source(root, tags_path)
    proofs, proof_errors = audit_repository_proofs(root, harvest)
    proof_details = _proof_diagnostics(root, english, policy, proofs)
    report = {'schema_version': 1, 'version': VERSION, 'source_commit': english.commit,
              'inventory_manifest_hash': inventory_hash, 'input_hashes': inputs,
              'batch_count': len(batches), 'unit_count': len(matches),
              'match_counts': dict(sorted(collections.Counter(m['status'] for m in matches).items())),
              'matches': matches, 'coordinates_to_remap': sum(old != new for m in maps.values() for old, new in m.items()),
              'term_candidate_failures': sum(bool(c['errors']) for c in terms['candidates']),
              'term_error_count': len(term_errors), 'source_error_count': len(source_errors),
              'proof_mismatches': proofs['mismatched'], 'proof_details': proof_details,
              'adopted': False, 'all_translation_repairs_complete': False}
    term_by_batch: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for candidate in terms['candidates']:
        if candidate['errors']:
            term_by_batch[Path(candidate['path']).stem].append(candidate)
    by_batch: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for match in matches:
        by_batch[match['batch']].append(match)
    queue = []
    for batch, units in batches.items():
        mapping = maps.get(batch, {})
        local = by_batch[batch]
        paths = {p:h for p,h in inputs.items() if Path(p).stem == batch}
        local_proofs = [p for p in proof_details if p['batch'] == batch]
        actions = []
        if any(m['status'] not in {'BYTE_EXACT', 'PRESENTATION_EQUIVALENT'} for m in local):
            actions.append('VERIFY_OR_RESTORE_SOURCE')
        if local_proofs:
            actions.append('RESOLVE_PROOF_SOURCE_DIFFERENCES')
        if any(old != new for old, new in mapping.items()):
            actions.append('REMAP_PERMANENT_TAGS')
        if term_by_batch[batch]:
            actions.append('ACTUAL_MODEL_TERM_REVISION')
        errors = [e for e in source_errors if batch + '.jsonl' in e or
                  any(re.search(r'(?<![\w:.-])' + re.escape(u['unit_id']) + r'(?=$|[^\w:.-]|:\s)', e) for u in units)]
        if errors:
            actions.append('RESOLVE_SOURCE_STRUCTURE_OR_DISPLAY')
        queue.append({'batch': batch, 'chapter': units[0]['chapter'], 'unit_ids': [u['unit_id'] for u in units],
                      'current_parent_tags': sorted({u['parent_tag'] for u in units}),
                      'input_hashes': paths, 'proposed_unit_id_map': mapping, 'actions': actions,
                      'source_matches': local, 'term_findings': term_by_batch[batch],
                      'source_findings': errors, 'proof_findings': local_proofs,
                      'adoption_or_review_approval': False})
    # Audits reread facts; never combine observations from different revisions.
    if _read_facts(root)[1] != inputs:
        raise RecordError('current facts changed while preparing the repair queue')
    if byte_hash((inventory / 'manifest.json').read_bytes()) != inventory_hash:
        raise RecordError('source inventory changed while preparing the repair queue')
    manifest = json.loads((inventory / 'manifest.json').read_bytes())
    if any(byte_hash((inventory / name).read_bytes()) != expected for name, expected in manifest['files'].items()):
        raise RecordError('source inventory changed while preparing the repair queue')
    native.assert_unchanged()
    return report, queue, {'term-audit.json': {**terms, 'errors': term_errors},
                          'source-audit.json': {**source, 'errors': source_errors},
                          'proof-audit.json': {**proofs, 'errors': proof_errors}}


def write_alignment(root: Path, harvest: Path, inventory: Path, output: Path, *, check: bool = False):
    if output.is_symlink():
        raise RecordError('alignment output must not be a symlink')
    root, output = root.resolve(), output.resolve()
    if output == root / 'build' or not output.is_relative_to(root / 'build'):
        raise RecordError('alignment output must use a dedicated ignored build subdirectory')
    expected_names = {'alignment.json', 'repair-queue.jsonl', 'report.md', 'term-audit.json', 'source-audit.json', 'proof-audit.json'}
    def require_owned():
        if output.is_symlink():
            raise RecordError('alignment output must not be a symlink')
        if not output.exists():
            return
        marker = output / 'alignment.json'
        if (not output.is_dir() or not marker.is_file() or marker.is_symlink()
                or json.loads(marker.read_text()).get('version') not in OWNED_VERSIONS
                or {p.name for p in output.iterdir()} != expected_names
                or any(p.is_symlink() for p in output.iterdir())):
            raise RecordError('refusing to replace an unrelated alignment directory')
    if not check:
        require_owned()
    report, queue, audits = build_alignment(root, harvest, inventory)
    payloads = {name: (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode() for name, obj in audits.items()}
    payloads['alignment.json'] = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    payloads['repair-queue.jsonl'] = ''.join(json.dumps(job, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for job in queue).encode()
    lines = ['# 当前来源对应与统一修订队列', '', f"锁定英文：`{report['source_commit']}`。", '',
             f"覆盖{report['unit_count']}个当前单元、{report['batch_count']}个事实batch；未采用任何新来源或译文。", '',
             '| 对应分类 | 数量 |', '| --- | ---: |']
    lines.extend(f'| {name} | {count} |' for name, count in report['match_counts'].items())
    lines.extend(['', f"待迁移坐标{report['coordinates_to_remap']}；术语不合格候选{report['term_candidate_failures']}（{report['term_error_count']}条诊断）；来源{report['source_error_count']}条诊断；证明差异{report['proof_mismatches']}组。", '',
        '排版/引用别名定位结果只作证据，原proof/source审计结论完整保留；队列成功不表示修订、词条、批评或人工审校通过。', '',
        '| Batch | Units | 待办 |', '| --- | ---: | --- |'])
    lines.extend(f"| {j['batch']} | {len(j['unit_ids'])} | {', '.join(j['actions']) or 'NO_DETERMINISTIC_FINDINGS'} |" for j in queue)
    payloads['report.md'] = ('\n'.join(lines) + '\n').encode()
    if check:
        if not output.is_dir() or {p.name for p in output.iterdir()} != expected_names:
            raise RecordError('alignment files missing, extra or stale')
        for name, raw in payloads.items():
            if (output / name).is_symlink() or (output / name).read_bytes() != raw:
                raise RecordError('alignment output out of date: ' + name)
        return report
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.alignment-', dir=output.parent))
    backup = None
    try:
        for name, raw in payloads.items():
            (temporary / name).write_bytes(raw)
        require_owned()
        if output.exists():
            backup = Path(tempfile.mkdtemp(prefix='.alignment-backup-', dir=output.parent)); backup.rmdir()
            output.rename(backup)
        try:
            temporary.rename(output)
        except OSError:
            if backup is not None:
                backup.rename(output); backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return report
