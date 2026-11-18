"""Fail-closed change dispatch; use the event's base and the trusted base implementation."""
from pathlib import Path
import json
import re
from .records import RecordError
from .chapter_validation import git
from .validation_io import read_text

DATA = re.compile(r'(?:translation-data/(?:units/[^/]+\.jsonl|candidates/[^/]+/[^/]+\.jsonl|(?:runs|source-adoptions|source-adoption-inputs|derivations|model-corrections|source-container-restorations|derivation-archives|selections)/[^/]+\.json|reviewed/.+\.json|retired/.+\.(?:json|jsonl)|chapter-templates/[^/]+\.json)|docs/evidence/[^/]+\.(?:json|jsonl)|task-scopes/[^/]+\.json|review/(?:language|mathematics)/.+\.json)\Z')
# Only descriptive, non-contract documentation can bypass data verification.
DESCRIPTIVE = re.compile(r'(?:LICENSE(?:S/.*)?|CODE_OF_CONDUCT\.md|SECURITY\.md|docs/notes/[^/]+\.md)\Z')


def classify(root, base, *, paths=None):
    root = root.resolve()
    if paths is None:
        paths = list(filter(None,git(root,'diff','--name-only','--no-renames','-z',base,raw=True).decode().split('\0')))
    return _classify(root, base, sorted(set(paths)))


def _classify(root, base, paths, *, entries=None, units_by_id=None):
    from .generated_reports import REPORT_FILES, report_scope
    if paths and set(paths) <= REPORT_FILES:
        scope = report_scope(root, base)
        if scope is not None:
            return dict(kind='generated-reports', paths=sorted(scope[1].changed), chapters=[],
                        validation_state='requires_report_checks',
                        reason='only generated report regions; both trusted generator checks required')
        from .chapter_validation import Base
        from .current_qa import InputSnapshot
        paths = sorted(set(paths) | Base(root, base, InputSnapshot(root)).changed)
        return dict(kind='current-all', paths=paths, chapters=[],
                    reason='report filenames contain public/unsafe or mixed changes')
    if not paths or all(DESCRIPTIVE.fullmatch(p) for p in paths):
        return dict(kind='documentation',paths=paths,chapters=[],reason='only descriptive documents; data QA not run')
    broad = [p for p in paths if not DATA.fullmatch(p)]
    # Mode-only or staged type changes must also expand, even on repositories
    # whose local core.fileMode setting ignores executable changes.
    if entries is None:
        entries = {}
        for entry in filter(None, git(root,'ls-tree','-r','-z',base,raw=True).split(b'\0')):
            meta, path = entry.split(b'\t',1)
            entries[path.decode()] = meta.decode().split()
    for p in paths:
        if p in entries and (root/p).is_file():
            mode='100755' if (root/p).stat().st_mode & 0o111 else '100644'
            if entries[p][0]!=mode:broad.append(p)
    if broad:
        return dict(kind='current-all',paths=paths,chapters=[],reason='public implementation/policy/source or unknown paths: '+', '.join(broad))
    owners, chapters, unresolved = {}, set(), set()
    if units_by_id is None:
        # Standalone CI classification still uses its own trusted code and
        # directly inspects the target checkout. No caller-provided inventory.
        for up in (root/'translation-data/units').glob('*.jsonl'):
            for line in read_text(up).splitlines():
                if line.strip():
                    u=json.loads(line)
                    if u['unit_id'] in owners:
                        raise RecordError('duplicate unit ID during CI classification')
                    owners[u['unit_id']]=u['chapter']
    else:
        owners = {uid: u['chapter'] for uid, u in units_by_id.items()}
    def inspect(value):
        if not isinstance(value,dict):
            raise RecordError('structured change is not an object')
        if isinstance(value.get('chapter'),str):
            chapters.add(value['chapter'])
            return  # Frozen neighbor/reference contexts are inputs, not owners.
        if isinstance(value.get('unit_id'),str) and value['unit_id'] in owners:
            chapters.add(owners[value['unit_id']])
        elif isinstance(value.get('unit_id'),str):
            unresolved.add(value['unit_id'])
        for key in ('unit_ids','input_unit_ids','output_unit_ids'):
            if isinstance(value.get(key),list):
                chapters.update(owners[x] for x in value[key] if isinstance(x,str) and x in owners)
                unresolved.update(x for x in value[key] if isinstance(x,str) and x not in owners)
        for child in value.get('data_scopes',[]):inspect(child)
        for key in ('old_unit','new_unit'):
            if isinstance(value.get(key),dict):inspect(value[key])
    for p in paths:
        path=root/p
        # Deleted and mode/type-changed data never becomes a narrow green skip.
        if not path.is_file() or path.is_symlink():
            return dict(kind='current-all',paths=paths,chapters=[],reason='deleted or unsafe data path: '+p)
        try:
            if path.suffix=='.json':inspect(json.loads(read_text(path)))
            else:
                for line in read_text(path).splitlines():
                    if line.strip():inspect(json.loads(line))
        except (ValueError,KeyError,TypeError) as exc:
            raise RecordError('cannot classify structured changes: '+p) from exc
    if unresolved:
        return dict(kind='current-all',paths=paths,chapters=[],reason='unresolved direct unit ownership: '+', '.join(sorted(unresolved)))
    if not chapters:
        return dict(kind='current-all',paths=paths,chapters=[],reason='data has no resolvable chapter ownership')
    return dict(kind='chapter-current',paths=paths,chapters=sorted(chapters),reason='structured chapter changes; all direct inputs must be consumed')
