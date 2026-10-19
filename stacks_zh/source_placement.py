"""Read-only placement of complete canonical prose in a locked Git chapter."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .records import RecordError
from .source_alignment import align_batches
from .source_containers import Containers, clean, lower_container


def complete_prose_positions(batches: list[list[dict]], indices: set[int],
                             root: Path, harvest: Path, chapter: str,
                             chapter_bytes: bytes) -> dict[int, int]:
    """Require canonical complete lowering, then reject overlap and interleaving.

    Other units are located through the existing owner/proof-aware source
    correspondence. No text-search fallback or caller-supplied span is accepted.
    """
    before = json.dumps(batches, sort_keys=True)
    native = Containers(root, harvest)
    raw, rows, _ = native.document(chapter)
    if raw != chapter_bytes:
        raise RecordError('unlabeled prose placement requires the locked Git chapter bytes')
    ids = [u['unit_id'] for batch in batches for u in batch]
    if len(ids) != len(set(ids)):
        raise RecordError('duplicate render source unit ID')
    adopted = {}
    if any(u.get('schema_version') in {2,3} for i in indices for u in batches[i]):
        from .source_adoptions import load_repository_source_adoptions
        adopted, errors = load_repository_source_adoptions(root, harvest)
        if errors:
            raise RecordError('typed prose has no complete first-source replay:\n' + '\n'.join(errors))
    selected = {}
    for index in sorted(indices):
        batch = batches[index]
        if len(batch) != 1:
            raise RecordError('unlabeled prose requires one complete canonical unit per batch')
        unit = batch[0]
        match = re.fullmatch(r'tag:([0-9A-Z]+):prose-([0-9]{4})', unit['unit_id'])
        if (match is None or unit.get('schema_version') not in {1,2,3}
                or unit.get('node_kind') != 'paragraph' or unit['chapter'] != chapter):
            raise RecordError('unlabeled batch is not a canonical complete ordinary prose unit')
        unit_policy = native.policy
        if unit.get('schema_version') in {2,3}:
            matches = [entry for entry in adopted.values() if entry['unit'] == clean(unit)]
            if len(matches) != 1:
                raise RecordError('typed prose requires its validated complete first-source adoption')
            unit_policy = matches[0]['policy']
        labels = [label for label, tag in native.english.tags.items()
                  if tag == match[1] and label.startswith(chapter + '-')]
        if len(labels) != 1:
            raise RecordError('unlabeled prose has no unique locked owner label')
        item = native.select(dict(file=chapter + '.tex', owner_tag=match[1],
            owner_label=labels[0], parent_tag=unit['parent_tag'],
            kind='prose_block', ordinal=int(match[2])))
        expected, actual = clean(lower_container(item, unit_policy)[0]), clean(unit)
        # CURRENT is optional in unit-v1; all actual source/structure fields
        # still have to equal the canonical complete lowering exactly.
        if 'source_status' not in actual:
            expected.pop('source_status', None)
        if actual != expected:
            raise RecordError(unit['unit_id'] + ': not the complete canonical locked prose lowering')
        selected[index] = item['location']

    from .source_adoptions import fresh_source_corpus
    corpus, alignment_native = fresh_source_corpus(root, harvest, chapter)
    matches, _ = align_batches({str(i): batch for i, batch in enumerate(batches)}, corpus)
    for entry in matches:
        if (entry['status'] not in {'BYTE_EXACT', 'PRESENTATION_EQUIVALENT'}
                or entry.get('extractor_state') != 'READY'):
            raise RecordError(entry['unit_id'] + ': cannot verify render source: '
                              + entry.get('reason', entry['status']))
    for index, location in selected.items():
        start, end = location['byte_start'], location['byte_end']
        other_batches = {}
        for entry in matches:
            other = int(entry['batch'])
            if other == index:
                continue
            span = entry['location']
            a, b = span['byte_start'], span['byte_end']
            left, right = max(start, a), min(end, b)
            if left < right and raw[left:right].strip(b' \t\r\n'):
                raise RecordError('unlabeled prose overlaps another rendered source unit')
            other_batches.setdefault(other, []).append((a, b))
        for spans in other_batches.values():
            if min(a for a, _ in spans) < start and max(b for _, b in spans) > end:
                raise RecordError('unlabeled prose would interleave an existing render batch')
    native.assert_unchanged()
    alignment_native.assert_unchanged()
    if json.dumps(batches, sort_keys=True) != before:
        raise RecordError('render source units changed during placement validation')
    return {index: location['byte_start'] for index, location in selected.items()}
