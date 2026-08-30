"""Runtime Harness identity resolution.

Harness versions are properties of the executable that performs a run.  They
must therefore be read at run time instead of copied from a previous manifest
or supplied by an unverified conversation value.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class HarnessVersionError(ValueError):
    """Raised when a Harness version cannot be resolved unambiguously."""


@dataclass(frozen=True)
class HarnessResolution:
    harness_id: str
    version: str
    command: tuple[str, ...]


_RECORD_RE = re.compile(r"^  ([A-Za-z0-9][A-Za-z0-9_-]*):\s*$")
_FIELD_RE = re.compile(r"^    ([A-Za-z0-9_]+):\s*(.*?)\s*$")
_SEMVER_RE = re.compile(r"(?<![A-Za-z0-9])([0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?)")


def _scalar(value: str) -> str | None:
    value = value.strip()
    if value in {"", "null", "~"}:
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_harness_registry(config_path: Path) -> dict[str, dict[str, str | None]]:
    """Read the fixed-shape Harness registry without requiring PyYAML."""

    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HarnessVersionError(f"cannot read Harness registry {config_path}: {exc}") from exc

    records: dict[str, dict[str, str | None]] = {}
    in_section = False
    current: str | None = None
    for line in text.splitlines():
        if line and not line[0].isspace():
            in_section = line.strip() == "harnesses:"
            current = None
            continue
        if not in_section:
            continue
        record_match = _RECORD_RE.match(line)
        if record_match:
            current = record_match.group(1)
            records[current] = {}
            continue
        field_match = _FIELD_RE.match(line)
        if current and field_match:
            records[current][field_match.group(1)] = _scalar(field_match.group(2))
    return records


def _desktop_codex_command(environment: Mapping[str, str]) -> tuple[str, ...] | None:
    """Prefer the Codex binary embedded in the running ChatGPT desktop app."""

    configured = environment.get("CODEX_CLI_PATH")
    if configured:
        path = Path(configured)
        if path.is_file():
            return (str(path), "--version")

    # The desktop app exports CODEX_MCP_NODE_PATH to its tool processes.  Walk
    # back to the app's Resources directory so an installed standalone `codex`
    # on PATH cannot be mistaken for the active desktop Harness.  This path is
    # discovered at run time and is never written into a manifest or config.
    node_path = environment.get("CODEX_MCP_NODE_PATH")
    if node_path:
        for parent in Path(node_path).parents:
            if parent.name == "Resources":
                desktop_path = parent / "codex"
                if desktop_path.is_file():
                    return (str(desktop_path), "--version")
    return None


def _version_command(
    harness_id: str,
    spec: Mapping[str, str | None],
    environment: Mapping[str, str],
) -> tuple[str, ...]:
    key = re.sub(r"[^A-Za-z0-9]", "_", harness_id).upper()
    override = environment.get(f"STACKS_HARNESS_{key}_VERSION_COMMAND")
    if override is None:
        override = environment.get("STACKS_HARNESS_VERSION_COMMAND")
    if override:
        command = tuple(shlex.split(override))
    elif harness_id == "codex":
        configured = spec.get("version_command")
        if not configured:
            raise HarnessVersionError("Harness codex has no configured version command")
        configured_tokens = tuple(shlex.split(configured))
        # A custom test/deployment command must remain authoritative.  Desktop
        # discovery applies only to the registered Codex executable command.
        command = (
            _desktop_codex_command(environment)
            if configured_tokens and Path(configured_tokens[0]).name in {"codex", "codex-cli"}
            else None
        )
        command = command or configured_tokens
    else:
        configured = spec.get("version_command")
        if not configured:
            raise HarnessVersionError(
                f"Harness {harness_id!r} has no configured version command; "
                "provide STACKS_HARNESS_"
                f"{key}_VERSION_COMMAND for this runner"
            )
        command = tuple(shlex.split(configured))
    if not command:
        raise HarnessVersionError(f"Harness {harness_id!r} resolved an empty version command")
    return command


def _extract_version(output: str, pattern: str | None, harness_id: str) -> str:
    if pattern:
        try:
            match = re.search(pattern, output, flags=re.MULTILINE)
        except re.error as exc:
            raise HarnessVersionError(
                f"Harness {harness_id!r} has invalid version_pattern: {exc}"
            ) from exc
        if match:
            version = match.groupdict().get("version") or match.group(1)
            if version:
                return version.strip()
    match = _SEMVER_RE.search(output)
    if match:
        return match.group(1)
    raise HarnessVersionError(
        f"Harness {harness_id!r} version command produced no parseable version"
    )


def resolve_harness(
    harness_id: str,
    config_path: Path,
    *,
    environment: Mapping[str, str] | None = None,
    timeout_seconds: float = 10.0,
) -> HarnessResolution:
    """Execute the registry command and return the observed Harness version."""

    if environment is None:
        environment = os.environ
    registry = load_harness_registry(config_path)
    spec = registry.get(harness_id)
    if spec is None:
        raise HarnessVersionError(
            f"Harness {harness_id!r} is not registered in {config_path}"
        )
    command = _version_command(harness_id, spec, environment)
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HarnessVersionError(
            f"failed to execute Harness {harness_id!r} version command "
            f"{shlex.join(command)!r}: {exc}"
        ) from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise HarnessVersionError(
            f"Harness {harness_id!r} version command {shlex.join(command)!r} "
            f"failed with exit {completed.returncode}"
            + (f": {detail}" if detail else "")
        )
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    version = _extract_version(output, spec.get("version_pattern"), harness_id)
    if not version or version.lower() in {"unknown", "auto"}:
        raise HarnessVersionError(
            f"Harness {harness_id!r} returned an unusable version {version!r}"
        )
    return HarnessResolution(harness_id, version, command)


def resolve_harness_version(
    harness_id: str,
    config_path: Path,
    *,
    environment: Mapping[str, str] | None = None,
) -> str:
    return resolve_harness(harness_id, config_path, environment=environment).version
