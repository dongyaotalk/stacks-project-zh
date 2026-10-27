"""Small local preparation ledger; never a candidate/provenance PASS cache."""
from __future__ import annotations

from contextlib import AbstractContextManager
import datetime
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from .records import RecordError

KIND = 'chapter-preflight-state-v1'


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def value_hash(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def generated_path(root: Path, path: Path) -> Path:
    """Only dedicated ignored build subdirectories, never source/fact paths."""
    root = root.resolve()
    path = path if path.is_absolute() else root / path
    if (not path.resolve().is_relative_to(root / 'build') or path.resolve() == root / 'build'
            or any(p.is_symlink() and (p == path or p.resolve().is_relative_to(root))
                   for p in [path, *path.parents])):
        raise RecordError('preflight output must be a safe dedicated build subdirectory')
    return path.resolve()


def atomic_json(path: Path, value, *, root=None):
    if root is not None:
        generated_path(root, path.parent)
    if path.is_symlink():
        raise RecordError('preflight state/output is a symlink')
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.preflight-', delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(canonical_bytes(value)); stream.flush(); os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        if root is not None:
            generated_path(root, path.parent)
        if path.is_symlink():
            raise RecordError('preflight state/output became a symlink')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def process_identity(pid: int):
    """An actual start/command/cwd probe prevents stale PID files from owning work."""
    if type(pid) is not int or pid <= 0:
        return None
    environment = dict(os.environ, LC_ALL='C')
    try:
        started = subprocess.run(['ps', '-p', str(pid), '-o', 'lstart='],
                                 capture_output=True, text=True, env=environment, check=False)
        command = subprocess.run(['ps', '-p', str(pid), '-o', 'command='],
                                 capture_output=True, text=True, env=environment, check=False)
        if started.returncode or command.returncode or not started.stdout.strip():
            return None
        if pid == os.getpid():
            cwd = str(Path.cwd().resolve())
        elif Path(f'/proc/{pid}/cwd').exists():
            cwd = str(Path(f'/proc/{pid}/cwd').resolve())
        else:
            executable = shutil.which('lsof') or '/usr/sbin/lsof'
            result = subprocess.run([executable, '-a', '-p', str(pid), '-d', 'cwd', '-Fn'],
                                    capture_output=True, text=True, check=False)
            names = [line[1:] for line in result.stdout.splitlines() if line.startswith('n')]
            cwd = str(Path(names[0]).resolve()) if result.returncode == 0 and len(names) == 1 else None
        return dict(pid=pid, started=started.stdout.strip(), command=command.stdout.strip(), cwd=cwd)
    except (OSError, ValueError):
        return None


def same_process(expected):
    if not isinstance(expected, dict):
        return False
    actual = process_identity(expected.get('pid'))
    return bool(actual and actual.get('cwd') and actual == expected)


class PreparationRun(AbstractContextManager):
    """Serialize a known preparation job and retain original attempts/checkpoints.

    Checkpoints are input-bound preparation evidence. They grant no permission to
    skip independent source adoption, candidate QA, full history, review or builds.
    """
    def __init__(self, root, directory, fingerprint, *, resume=False, check=False):
        self.root = root.resolve()
        self.directory = generated_path(self.root, directory)
        if not isinstance(fingerprint, str) or not re.fullmatch(r'[0-9a-f]{64}', fingerprint):
            raise RecordError('invalid preflight input fingerprint')
        self.fingerprint = fingerprint
        self.resume = resume
        self.check = check
        self.active = None
        self.lock = None
        self.owned = False
        self.status = None
        self.started = None
        self.results = {}
        self.references = {}
        self.attempt = None

    def _write(self, path, value):
        atomic_json(path, value, root=self.root)

    def _read(self, path):
        generated_path(self.root, path.parent)
        if path.is_symlink():
            raise RecordError('preflight state is a symlink')
        try:
            value = json.loads(path.read_bytes())
        except (OSError, ValueError) as exc:
            raise RecordError(f'invalid preflight state {path}: {exc}') from exc
        if not isinstance(value, dict):
            raise RecordError('preflight state must be an object')
        return value

    def __enter__(self):
        try:
            return self._enter()
        except BaseException:
            if self.lock is not None:
                if self.owned:
                    fcntl.flock(self.lock, fcntl.LOCK_UN)
                self.lock.close()
            raise

    def _enter(self):
        generated_path(self.root, self.directory)
        owner = self.directory / 'owner.json'
        expected = dict(kind=KIND, root=str(self.root))
        if self.directory.exists():
            if not owner.exists() or self._read(owner) != expected:
                raise RecordError('refusing an unrelated preflight state directory')
        elif self.check:
            raise RecordError('preflight check requires the original state/output')
        else:
            self.directory.mkdir(parents=True)
            self._write(owner, expected)
        if any(p.is_symlink() for p in self.directory.rglob('*')):
            raise RecordError('preflight state contains a symlink')
        allowed = {'owner.json', 'lock', 'status.json', 'handoff.md', 'events.jsonl', 'checkpoints', 'attempts'}
        if {p.name for p in self.directory.iterdir()} - allowed:
            raise RecordError('preflight state directory contains unrelated files')
        lock_path = self.directory / 'lock'
        if self.check and not lock_path.is_file():
            raise RecordError('preflight check has no original lock file')
        self.lock = lock_path.open('r+b' if lock_path.exists() else 'w+b')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.owned = True
        except BlockingIOError:
            previous = self._read(self.directory / 'status.json')
            if previous.get('fingerprint') != self.fingerprint:
                raise RecordError('another preparation is active with different inputs')
            if not same_process(previous.get('process')):
                raise RecordError('preflight lock is held; owner identity is not yet verifiable; wait, do not restart')
            if not self.resume:
                raise RecordError('preflight is already running; use --resume to observe the same process')
            self.active = previous
            return self
        previous_path = self.directory / 'status.json'
        previous = self._read(previous_path) if previous_path.exists() else None
        if previous and previous.get('stage') == 'RUNNING' and same_process(previous.get('process')):
            self.active = previous
            return self
        if self.resume and previous and previous.get('fingerprint') != self.fingerprint:
            raise RecordError('preflight inputs changed; old checkpoints are invalid; start a new preparation')
        if self.check:
            return self
        self.started = time.perf_counter()
        identity = process_identity(os.getpid())
        if identity is None or identity['cwd'] is None:
            raise RecordError('cannot establish actual preflight process identity')
        attempts = self.directory / 'attempts'
        generated_path(self.root, attempts)
        attempts.mkdir(exist_ok=True)
        existing = sorted(attempts.glob('*.json'))
        if any(not re.fullmatch(r'[0-9]{6}', path.stem) for path in existing):
            raise RecordError('invalid preparation attempt identity')
        self.attempt = max((int(path.stem) for path in existing), default=0) + 1
        self.status = dict(kind=KIND, root=str(self.root), fingerprint=self.fingerprint,
            stage='RUNNING', phase='PREFLIGHT', process=identity, cwd=str(Path.cwd()),
            attempt=self.attempt, started=utc_now(), verified=[], exit_code=None,
            usage=dict(status='unavailable', reason='preflight makes no model calls'),
            next_action='Wait this exact process; an observation timeout is not failure.')
        checkpoints = sorted((self.directory / 'checkpoints' / self.fingerprint).glob('*.json'))
        if self.resume and checkpoints:
            value = self._read(checkpoints[-1])
            if (value.get('fingerprint') != self.fingerprint or not isinstance(value.get('entries'), dict)
                    or value.get('entries_hash') != value_hash(value['entries'])):
                raise RecordError('preflight checkpoint contents changed')
            for key, entry in value['entries'].items():
                if (not isinstance(key, str) or not isinstance(entry, dict)
                        or set(entry) != {'file', 'hash'}
                        or not re.fullmatch(r'[0-9a-f]{64}\.json', entry.get('file', ''))
                        or entry['file'] != entry.get('hash', '') + '.json'):
                    raise RecordError('preflight checkpoint reference changed')
                record = self._read(self.directory / 'checkpoints' / self.fingerprint / 'records' / entry['file'])
                if (value_hash(record) != entry['hash'] or record.get('fingerprint') != self.fingerprint
                        or record.get('key') != key or 'result' not in record):
                    raise RecordError('preflight checkpoint contents changed')
                self.results[key] = record['result']
            self.references = value['entries']
            self.status['verified'] = sorted(self.results)
        self.event('started', previous_owner_interrupted=bool(previous and previous.get('stage') == 'RUNNING'))
        self._save()
        return self

    def event(self, event, **fields):
        if self.check:
            return
        value = dict(event=event, at=utc_now(), fingerprint=self.fingerprint, attempt=self.attempt, **fields)
        path = self.directory / 'events.jsonl'
        generated_path(self.root, path.parent)
        if path.is_symlink():
            raise RecordError('preflight event log is a symlink')
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n')

    def _save(self):
        self._write(self.directory / 'status.json', self.status)
        self._write(self.directory / 'attempts' / f'{self.attempt:06d}.json', self.status)
        handoff = (f"Preflight {self.status['stage']}; root={self.root}; input={self.fingerprint}; "
                   f"pid={self.status['process']['pid']}; verified={len(self.status['verified'])}; "
                   f"exit={self.status['exit_code']}; {self.status['next_action']}\n")
        path = self.directory / 'handoff.md'
        generated_path(self.root, path.parent)
        if path.is_symlink():
            raise RecordError('preflight handoff is a symlink')
        path.write_text(handoff, encoding='utf-8')

    def checkpoint(self, key, result):
        if self.check:
            return
        record = dict(fingerprint=self.fingerprint, key=key, result=result)
        digest = value_hash(record)
        path = self.directory / 'checkpoints' / self.fingerprint / 'records' / (digest + '.json')
        generated_path(self.root, path.parent)
        if path.exists():
            if path.is_symlink() or path.read_bytes() != canonical_bytes(record):
                raise RecordError('preflight checkpoint record changed')
        else:
            self._write(path, record)
        self.results[key] = result
        self.references[key] = dict(file=digest + '.json', hash=digest)
        self._write(self.directory / 'checkpoints' / self.fingerprint / f'{self.attempt:06d}.json',
                    dict(fingerprint=self.fingerprint, entries=self.references, entries_hash=value_hash(self.references)))
        self.status['verified'] = sorted(self.results)
        self.status['phase'] = 'SOURCE_READY_CHECK'
        self._save()

    def phase(self, name, seconds):
        if self.check:
            return
        self.status.setdefault('phase_seconds', {})[name] = seconds
        self.event('phase', name=name, seconds=seconds)
        self._save()

    def finish(self, report, output, *, exit_code=0):
        if self.check:
            return
        self.status.update(stage='COMPLETE', phase='SOURCE_READY' if report['state'] == 'READY' else 'PREFLIGHT_BLOCKED',
            report_state=report['state'], output=str(output), report_hash=value_hash(report),
            seconds=time.perf_counter() - self.started, finished=utc_now(), exit_code=exit_code,
            next_action='Preparation only; independent data authorization, QA and review gates remain required.')
        self.event('completed', exit_code=exit_code, seconds=self.status['seconds'])
        self._save()

    def __exit__(self, error_type, error, traceback):
        try:
            if error is not None and self.status is not None and not self.check:
                self.status.update(stage='INTERRUPTED' if issubclass(error_type, KeyboardInterrupt) else 'FAILED',
                    error=str(error), exit_code=130 if issubclass(error_type, KeyboardInterrupt) else 1,
                    finished=utc_now(), seconds=time.perf_counter() - self.started,
                    next_action='Inspect the failure, verify actual owner/inputs, then resume remaining verified preparation.')
                self.event('failed', exit_code=self.status['exit_code'], error=str(error))
                self._save()
        finally:
            if self.lock is not None:
                if self.owned:
                    fcntl.flock(self.lock, fcntl.LOCK_UN)
                self.lock.close()
        return False
