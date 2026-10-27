"""Actual input bytes and enumerations for one in-process operation, never a pass cache."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import fnmatch
import hashlib
import json
import locale
from pathlib import Path

_ACTIVE = ContextVar('actual_validation_inputs', default=())


def _error(message):
    from .records import RecordError
    raise RecordError(message)


def _matches(relative, pattern, recursive=False):
    parts = tuple(relative.parts)
    patterns = tuple(pattern.rstrip('/').split('/'))
    if recursive:
        patterns = ('**', *patterns)
    def match(items, masks):
        if not masks:
            return not items
        if masks[0] == '**':
            return any(match(items[i:], masks[1:]) for i in range(len(items) + 1))
        return bool(items) and fnmatch.fnmatchcase(items[0], masks[0]) and match(items[1:], masks[1:])
    return match(parts, patterns)


class InputReads:
    """All bytes actually supplied to parsers, plus the path sets they enumerated."""
    def __init__(self):
        self.hashes = {}
        self.globs = {}
        self.trees = {}
        self.roots = set()
        self.absent = set()
        self.watched = set()

    def _path(self, path):
        path = Path(path).absolute()
        # Keep platform aliases above a repository (e.g. macOS /var) compatible;
        # reject the file itself and every symlink inside a bound input root.
        roots = self.roots | {path.parent.resolve()}
        for part in [path, *path.parents]:
            if part.is_symlink() and (part == path or any(
                    part.is_relative_to(root) or part.resolve().is_relative_to(root) for root in roots)):
                _error(f'validation input is a symlink: {path}')
        return path.resolve()

    def observe(self, path, raw):
        path = self._path(path)
        digest = hashlib.sha256(raw).hexdigest()
        if path in self.absent or (path in self.hashes and self.hashes[path] != digest):
            _error(f'validation input bytes changed while reading: {path}')
        self.hashes[path] = digest
        self.roots.add(path.parent)

    def tree(self, directory, pattern, files, directories):
        directory = self._path(directory)
        self.roots.add(directory)
        paths = frozenset(Path(p).resolve() for p in files)
        if pattern == '*':
            paths |= frozenset(Path(p).resolve() for p in directories)
        key = directory, pattern
        if key in self.trees and self.trees[key] != paths:
            _error(f'validation input paths changed: {directory}')
        self.trees[key] = paths

    def _expected(self, directory, pattern, recursive):
        choices = [(root, mask, paths) for (root, mask), paths in self.trees.items()
                   if directory.is_relative_to(root) and (mask == '*' or mask == pattern)]
        if not choices:
            # Repository-relative patterns can begin above a watched subtree.
            # Only literal prefixes prove the entire requested glob is covered.
            masks = tuple(pattern.rstrip('/').split('/'))
            for (root, mask), paths in self.trees.items():
                if recursive or mask != '*' or not root.is_relative_to(directory):
                    continue
                prefix = root.relative_to(directory).parts
                if prefix and masks[:len(prefix)] == prefix:
                    return frozenset(p for p in paths if p != directory
                                     and _matches(p.relative_to(directory), pattern))
            return None
        root, mask, paths = max(choices, key=lambda row: len(row[0].parts))
        return frozenset(p for p in paths if p != directory and p.is_relative_to(directory)
                         and _matches(p.relative_to(directory), pattern, recursive))

    def enumeration(self, directory, pattern, recursive, paths):
        directory = self._path(directory)
        paths = frozenset(self._path(path) for path in paths)
        key = directory, pattern, recursive
        expected = self._expected(directory, pattern, recursive)
        if ((expected is not None and paths != expected)
                or (key in self.globs and paths != self.globs[key])):
            _error(f'validation input paths changed while enumerating: {directory}')
        self.globs[key] = paths

    def seed_snapshot(self, snapshot):
        for path, digest in snapshot.hashes.items():
            if path in self.hashes and self.hashes[path] != digest:
                _error(f'validation input bytes changed: {path}')
            self.hashes[path] = digest
        for (directory, pattern), files in snapshot.trees.items():
            # New snapshots call tree() while they capture. For an older caller's
            # snapshot, preserve file claims and derive its required parent paths.
            if (directory, pattern) not in self.trees:
                dirs = {directory} if directory.is_dir() else set()
                if pattern == '*':
                    dirs.update(p for file in files for p in file.parents if p.is_relative_to(directory))
                self.tree(directory, pattern, files, dirs)

    def seed_implementation(self, implementation):
        for path, raw in implementation.inputs:
            self.observe(path, raw)
        for directory, pattern, paths in implementation.trees:
            self.tree(directory, pattern, paths, ())

    def watch_root(self, root):
        root = root.resolve()
        if root in self.watched:
            return
        self.watched.add(root)
        self.roots.add(root)
        for name in ['translation-data', 'review', 'config', 'schema', 'task-scopes', 'docs/evidence', 'prompts']:
            directory = root/name
            entries = tuple(directory.rglob('*'))
            files = {p for p in entries if p.is_file()}
            dirs = {p for p in entries if p.is_dir()}
            if directory.is_dir():
                dirs.add(directory)
            self.tree(directory, '*', files, dirs)
            for path in sorted(files):
                read_bytes(path)
        for name in ['upstream.lock', 'Makefile', 'AGENTS.md', 'WORKFLOW.md', 'stacks_zh.py']:
            path = root/name
            if path.is_file():
                read_bytes(path)
            else:
                self.absent.add(path)

    @contextmanager
    def activate(self):
        active = _ACTIVE.get()
        if self in active:
            yield self
            return
        token = _ACTIVE.set((*active, self))
        try:
            yield self
        finally:
            _ACTIVE.reset(token)

    def claims(self):
        return (id(self), dict(self.hashes), dict(self.globs), dict(self.trees),
                frozenset(self.roots), frozenset(self.absent))

    def require_claims(self, claims):
        identity, hashes, globs, trees, roots, absent = claims
        if (id(self) != identity or not roots <= self.roots or not absent <= self.absent
                or any(self.hashes.get(p) != value for p, value in hashes.items())
                or any(self.globs.get(key) != value for key, value in globs.items())
                or any(self.trees.get(key) != value for key, value in trees.items())):
            _error('validation receipt actual-read claims changed')

    def binding(self):
        value = dict(files={str(p): value for p, value in self.hashes.items()},
            globs=[(str(p), pattern, recursive, sorted(str(x) for x in paths))
                   for (p, pattern, recursive), paths in sorted(self.globs.items())],
            trees=[(str(p), pattern, sorted(str(x) for x in paths))
                   for (p, pattern), paths in sorted(self.trees.items())],
            roots=sorted(str(p) for p in self.roots), absent=sorted(str(p) for p in self.absent))
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

    def assert_unchanged(self):
        for path, digest in self.hashes.items():
            self._path(path)
            try:
                raw = path.read_bytes()
            except OSError as exc:
                _error(f'validation input changed or unavailable: {path}: {exc}')
            if hashlib.sha256(raw).hexdigest() != digest:
                _error(f'validation input changed: {path}')
        if any(path.exists() or path.is_symlink() for path in self.absent):
            _error('validation input paths changed: previously absent input appeared')
        for (directory, pattern), expected in self.trees.items():
            self._path(directory)
            entries = tuple(directory.rglob('*'))
            if any(path.is_symlink() for path in entries):
                _error(f'validation input is a symlink: {directory}')
            actual = {p.resolve() for p in entries if p.is_file() and _matches(p.relative_to(directory), pattern, True)}
            if pattern == '*':
                actual.update(p.resolve() for p in entries if p.is_dir())
                if directory.is_dir():
                    actual.add(directory)
            if actual != expected:
                _error(f'validation input paths changed: {directory}')
        for (directory, pattern, recursive), expected in self.globs.items():
            self._path(directory)
            actual = frozenset(self._path(p) for p in (directory.rglob(pattern) if recursive else directory.glob(pattern)))
            if actual != expected:
                _error(f'validation input paths changed: {directory}')


def current_inputs():
    active = _ACTIVE.get()
    return active[-1] if active else None


def read_bytes(path):
    raw = Path(path).read_bytes()
    for reads in _ACTIVE.get():
        reads.observe(path, raw)
    return raw


def read_text(path, encoding=None, errors=None):
    return read_bytes(path).decode(encoding or locale.getpreferredencoding(False), errors or 'strict').replace('\r\n', '\n').replace('\r', '\n')


def glob_paths(directory, pattern, *, recursive=False):
    paths = tuple(Path(directory).rglob(pattern) if recursive else Path(directory).glob(pattern))
    for reads in _ACTIVE.get():
        reads.enumeration(directory, pattern, recursive, paths)
    return iter(paths)


def remember_tree(directory, pattern, files, directories):
    for reads in _ACTIVE.get():
        reads.tree(directory, pattern, files, directories)


def _tracked(function, separate=False, owner=False):
    @wraps(function)
    def call(*args, **kwargs):
        reads = getattr(args[0], '_reads', None) if owner else None
        if owner and reads is None:
            reads = InputReads();args[0]._reads = reads
        if reads is None:
            reads = InputReads() if separate else current_inputs() or InputReads()
        if type(reads) is not InputReads:
            _error('validation requires an actual input read session')
        outer = reads not in _ACTIVE.get()
        with reads.activate():
            result = function(*args, **kwargs)
            if outer:
                reads.assert_unchanged()
            return result
    return call


def tracked_inputs(function):
    return _tracked(function)


def isolated_inputs(function):
    return _tracked(function, separate=True)


def object_inputs(function):
    return _tracked(function, owner=True)


def render_inputs(function):
    @wraps(function)
    def call(*args, **kwargs):
        validation = kwargs.get('_validation')
        current = kwargs.get('_current')
        reads = None
        if validation is not None:
            from .repository_validation import _BatchPass
            if type(validation) is not _BatchPass:
                _error('render requires an actual live batch validation result')
            reads = validation.provenance.reads
        elif current is not None:
            from .current_qa import CurrentSourceQA
            if type(current) is not CurrentSourceQA:
                _error('render current QA must be an actual current-source session')
            reads = current._reads
        reads = reads or current_inputs() or InputReads()
        if type(reads) is not InputReads:
            _error('render requires an actual input read session')
        with reads.activate():
            return function(*args, **kwargs)
    return call
