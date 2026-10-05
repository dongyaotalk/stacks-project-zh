from __future__ import annotations

import re
from pathlib import Path


WARNING = re.compile(r"^\s*(?:LaTeX|Package\s+[\w.-]+)\s+Warning:")
PDF_OUTPUT = re.compile(r"Output written on\s+.+?\.pdf\s*\([^)]*\bpages?\b[^)]*\)\.")
REFERENCE = re.compile(r"Warning:\s*(?:Reference|Citation)\b.*\bun\s*defined\b", re.I)
UNDEFINED = re.compile(r"Warning:\s*There were undefined (?:references|citations)\b", re.I)
LABEL = re.compile(r"Warning:\s*(?:Label\b.*\bmultiply defined\b|There were multiply-defined labels\b)", re.I)


def validate_final_tex_log(path: Path) -> list[str]:
    """Check the completed final pass, without changing any build artifact.

    TeX wraps lines at max_print_line, including inside words and filenames.
    Join warning continuations without inserting text; retain their first line
    numbers. Font-shape fallbacks are different diagnostics from references.
    This validates the supplied log, not its source revision or freshness.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: cannot read final TeX log: {exc}"]
    if not text.strip():
        return [f"{path}: final TeX log is empty"]

    errors = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"\s*Missing character\s*:", line, re.I):
            errors.append(f"{path}:{index + 1}: missing character: {line.strip()}")
        if not WARNING.match(line):
            continue
        continuation = [line]
        for following in lines[index + 1:]:
            if not following.strip() or WARNING.match(following):
                break
            continuation.append(re.sub(r"^\s*\([\w.-]+\)", "", following))
        warning = "".join(continuation)
        if REFERENCE.search(warning) or UNDEFINED.search(warning):
            errors.append(f"{path}:{index + 1}: undefined reference or citation: {warning.strip()}")
        elif LABEL.search(warning):
            errors.append(f"{path}:{index + 1}: duplicate label: {warning.strip()}")

    compact = "".join(lines)
    if not PDF_OUTPUT.search(compact):
        errors.append(f"{path}: final TeX log has no completed PDF output summary")
    return errors
