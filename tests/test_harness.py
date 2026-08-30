from __future__ import annotations

import os
import shlex
import stat
import sys
import tempfile
import unittest
from pathlib import Path

from stacks_zh.harness import HarnessVersionError, resolve_harness


def _registry(path: Path, command: str, pattern: str | None = None) -> None:
    pattern_line = f"    version_pattern: '{pattern}'\n" if pattern else ""
    path.write_text(
        "schema: 1\n\nharnesses:\n"
        "  codex:\n"
        "    display_name: Codex\n"
        "    kind: agent_cli\n"
        "    status: supported\n"
        "    adapter_version: stacks-harness-v1\n"
        "    version_required: true\n"
        f"    version_command: {command}\n"
        f"{pattern_line}",
        encoding="utf-8",
    )


class HarnessVersionTests(unittest.TestCase):
    def test_resolves_and_parses_registered_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "harnesses.yml"
            command = shlex.join(
                [sys.executable, "-c", "print('codex-cli 9.8.7-alpha.1')"]
            )
            _registry(config, command, r"^codex-cli\s+(?P<version>\S+)")
            resolution = resolve_harness("codex", config, environment={})
            self.assertEqual(resolution.version, "9.8.7-alpha.1")
            self.assertEqual(resolution.command[0], sys.executable)

    def test_desktop_codex_path_override_is_resolved_at_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = root / "harnesses.yml"
            _registry(config, "codex --version")
            executable = root / "codex"
            executable.write_text("#!/bin/sh\nprintf '%s\\n' 'codex-cli 1.2.3'\n", encoding="utf-8")
            executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
            resolution = resolve_harness(
                "codex", config, environment={"CODEX_CLI_PATH": str(executable)}
            )
            self.assertEqual(resolution.version, "1.2.3")
            self.assertEqual(resolution.command[0], str(executable))

    def test_nonzero_command_is_a_hard_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "harnesses.yml"
            command = shlex.join(
                [sys.executable, "-c", "import sys; sys.exit(3)"]
            )
            _registry(config, command)
            with self.assertRaisesRegex(HarnessVersionError, "exit 3"):
                resolve_harness("codex", config, environment={})

    def test_unknown_output_is_a_hard_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "harnesses.yml"
            command = shlex.join([sys.executable, "-c", "print('unknown')"])
            _registry(config, command)
            with self.assertRaisesRegex(HarnessVersionError, "no parseable version"):
                resolve_harness("codex", config, environment={})

    def test_missing_custom_api_command_is_a_hard_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "harnesses.yml"
            config.write_text(
                "schema: 1\n\nharnesses:\n"
                "  custom-api:\n"
                "    display_name: API\n"
                "    kind: api_runner\n"
                "    status: supported\n"
                "    adapter_version: stacks-harness-v1\n"
                "    version_required: true\n"
                "    version_command: null\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(HarnessVersionError, "no configured version command"):
                resolve_harness("custom-api", config, environment={})


if __name__ == "__main__":
    unittest.main()
