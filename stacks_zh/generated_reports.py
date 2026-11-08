"""Only deterministic reports over unchanged accepted inputs; no data QA receipt."""
from pathlib import Path
import hashlib
import time
import tomllib

from . import progress, planning
from .chapter_validation import Base, git, inventory
from .current_qa import InputSnapshot
from .records import RecordError, load_upstream_commit
from .validation_io import InputReads, read_bytes, glob_paths

REPORT_FILES = frozenset({'README.md', 'docs/translation-progress.md', 'docs/translation-plan.md'})


def readme_outside(text):
    """Reuse the generators' exact marker handling, rejecting overlapping pairs."""
    markers = [(module.README_START, module.README_END) for module in (progress, planning)]
    for start, end in markers:
        if text.count(start) != 1 or text.count(end) != 1 or text.index(start) >= text.index(end):
            raise RecordError('README generated markers must be unique, complete and ordered')
    spans = sorted((text.index(start), text.index(end) + len(end)) for start, end in markers)
    if spans[0][1] > spans[1][0]:
        raise RecordError('README generated marker pairs overlap or nest')
    return planning._replace_readme_block(progress._replace_readme_block(text, ''), '')


def report_scope(root, ref):
    """Shape classification only. Output validity still requires both real checks."""
    root = root.resolve()
    snapshot = InputSnapshot(root)
    base = Base(root, ref, snapshot)
    if not base.changed or not base.changed <= REPORT_FILES:
        return None
    for entry in base.change_identity[0].split(b'\0'):
        if entry.startswith(b':'):
            fields = entry.split()
            if fields[0][1:] != b'100644' or fields[1] != b'100644':
                return None
    for name in REPORT_FILES:
        entry = base.entries.get(name)
        path = snapshot._safe(root / name)
        if (entry is None or entry[:2] != ('100644', 'blob') or not path.is_file()
                or path.stat().st_mode & 0o111):
            return None
    before = git(root, 'show', base.commit + ':README.md', raw=True).decode('utf-8')
    after = snapshot.read(root / 'README.md').decode('utf-8')
    if readme_outside(before) != readme_outside(after):
        return None
    snapshot.assert_identity()
    base.assert_unchanged()
    return snapshot, base


def _source_identity(harvest):
    return (git(harvest, 'rev-parse', '--show-toplevel', 'HEAD'),
            git(harvest, 'remote', 'get-url', 'origin'),
            git(harvest, 'status', '--porcelain', '--untracked-files=no'))


def check_generated_reports(root, harvest, ref, *, report=print):
    started = time.monotonic()
    root, harvest = root.resolve(), harvest.resolve()
    main_identity = git(root, 'for-each-ref', '--format=%(refname) %(objectname)',
                        'refs/remotes/origin/main', 'refs/heads/main')
    reads = InputReads()
    with reads.activate():
        scope = report_scope(root, ref)
        if scope is None:
            raise RecordError('generated-report scope changed or requires broad validation')
        snapshot, base = scope
        source = _source_identity(harvest)
        commit = load_upstream_commit(root / 'upstream.lock')
        repository = tomllib.loads(read_bytes(root / 'upstream.lock').decode('utf-8'))['repository']
        if (source[0].splitlines() != [str(harvest), commit] or source[2]
                or source[1].removesuffix('.git').rstrip('/') != repository.removesuffix('.git').rstrip('/')):
            raise RecordError('generated reports require the clean locked English source')
        english_entries = {}
        english_format = git(harvest, 'rev-parse', '--show-object-format')
        for entry in filter(None, git(harvest, 'ls-tree', '-r', '-z', commit, raw=True).split(b'\0')):
            metadata, name = entry.split(b'\t', 1)
            english_entries[name.decode()] = tuple(metadata.decode().split())
        # Read only consumed facts, but bind their directory inventory too.
        inventory(root, reads)
        tools = Path(__file__).resolve().parents[1]
        tools_snapshot = InputSnapshot(tools)
        implementation = list(glob_paths(tools / 'stacks_zh', '*.py')) + [tools / 'scripts/ci-current.py']
        for path in implementation:
            relative = path.relative_to(tools).as_posix()
            entry = base.entries.get(relative)
            raw = read_bytes(path)
            digest = hashlib.new(base.object_format, b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            if (entry is None or entry != ('100644', 'blob', digest) or path.stat().st_mode & 0o111):
                raise RecordError('report validator implementation differs from trusted base: ' + relative)
        stages = {}
        for target, check in [
            ('progress-check', lambda: progress.update_progress_report(
                root, harvest / 'tags/tags', root / 'README.md', root / 'docs/translation-progress.md', check=True)),
            ('plan-check', lambda: planning.update_translation_plan(
                root, root / 'README.md', root / 'docs/translation-plan.md', check=True)),
        ]:
            report(target + ': running trusted generator --check')
            tick = time.monotonic()
            count, errors = check()
            if errors:
                raise RecordError('; '.join(errors))
            stages[target] = dict(seconds=time.monotonic() - tick, chapters=count, exit_status=0)
            report(target + ': PASS')
        # Consumed non-report facts must still be the accepted Git inputs. This
        # also rejects ignored/untracked inputs that a generator actually read.
        for path in tuple(reads.hashes):
            if path.is_relative_to(root):
                relative = path.relative_to(root).as_posix()
                if relative not in REPORT_FILES and not base.accepted(relative):
                    raise RecordError('report input differs from accepted main: ' + relative)
            elif path.is_relative_to(tools):
                relative = path.relative_to(tools).as_posix()
                raw = read_bytes(path)
                digest = hashlib.new(base.object_format, b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
                mode = '100755' if path.stat().st_mode & 0o111 else '100644'
                if base.entries.get(relative) != (mode, 'blob', digest):
                    raise RecordError('consumed trusted tool input differs from base: ' + relative)
            elif path.is_relative_to(harvest):
                relative = path.relative_to(harvest).as_posix()
                raw = read_bytes(path)
                digest = hashlib.new(english_format, b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
                mode = '100755' if path.stat().st_mode & 0o111 else '100644'
                if english_entries.get(relative) != (mode, 'blob', digest):
                    raise RecordError('consumed English source differs from locked Git: ' + relative)
        if _source_identity(harvest) != source:
            raise RecordError('English source identity changed during report checks')
        if (git(root, 'rev-parse', '--verify', ref + '^{commit}') != base.commit or
                git(root, 'for-each-ref', '--format=%(refname) %(objectname)',
                    'refs/remotes/origin/main', 'refs/heads/main') != main_identity):
            raise RecordError('trusted comparison identity changed during report checks')
        snapshot.assert_identity()
        tools_snapshot.assert_identity()
        base.assert_unchanged()
        reads.assert_unchanged()
        return dict(scope='generated-reports', input_view='worktree', base=base.commit, head=snapshot.head, tree=base.tree,
                    source_commit=commit, paths=sorted(base.changed), stages=stages,
                    input_binding=reads.binding(), input_count=len(reads.hashes),
                    seconds=time.monotonic() - started, exit_status=0,
                    data_qa='not_run', history_audit='not_run', tool_tests='not_run')
