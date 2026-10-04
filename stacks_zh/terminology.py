from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


STATUSES = {"proposed", "approved", "deprecated"}
FIELD_RE = re.compile(r"^([a-z_]+):(?:\s+(.*))?$")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate glossary field {key!r}")
        result[key] = value
    return result


def _without_comment(text: str) -> str:
    quote: str | None = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote == '"' and char == "\\":
            index += 2
            continue
        if quote == "'" and text[index : index + 2] == "''":
            index += 2
            continue
        if char == quote:
            quote = None
        elif quote is None and char in {"'", '"'} and (
            index == 0 or text[index - 1].isspace() or text[index - 1] in "[{:,"
        ):
            quote = char
        elif quote is None and char == "#" and (index == 0 or text[index - 1].isspace()):
            return text[:index].rstrip()
        index += 1
    return text.rstrip()


def _scalar(text: str) -> Any:
    text = _without_comment(text).strip()
    if text.startswith('"'):
        try:
            return json.loads(text, object_pairs_hook=_unique_object)
        except ValueError as exc:
            raise ValueError(f"invalid quoted glossary scalar: {text!r}") from exc
    if text.startswith("'"):
        if len(text) < 2 or not text.endswith("'"):
            raise ValueError(f"invalid quoted glossary scalar: {text!r}")
        inner = text[1:-1]
        if "'" in inner.replace("''", ""):
            raise ValueError(f"invalid quoted glossary scalar: {text!r}")
        return inner.replace("''", "'")
    if text in {"null", "~", ""}:
        return None
    if text in {"true", "false"}:
        return text == "true"
    if text.startswith(("[", "{")):
        try:
            return json.loads(text, object_pairs_hook=_unique_object)
        except ValueError as exc:
            raise ValueError("glossary flow values must use JSON syntax") from exc
    if text.startswith(("&", "*", "!")) or ": " in text:
        raise ValueError("unsupported glossary scalar; use a quoted string")
    return text


def _block_list(lines: list[str]) -> list[Any]:
    values: list[Any] = []
    mapping: dict[str, Any] | None = None
    for line in lines:
        if line == "-" or line.startswith("- "):
            content = line[1:].strip()
            match = FIELD_RE.fullmatch(content)
            if match:
                mapping = {match.group(1): _scalar(match.group(2) or "")}
                values.append(mapping)
            elif not content:
                mapping = {}
                values.append(mapping)
            else:
                mapping = None
                values.append(_scalar(content))
        else:
            match = FIELD_RE.fullmatch(line)
            if mapping is None or match is None or match.group(1) in mapping:
                raise ValueError("unsupported or duplicate glossary list-item field")
            mapping[match.group(1)] = _scalar(match.group(2) or "")
    return values


def _yaml_entries(text: str) -> list[dict[str, Any]]:
    """Read the documented block-list subset without executing YAML tags/aliases."""
    lines = [_without_comment(line) for line in text.splitlines()]
    starts = [index for index, line in enumerate(lines) if re.match(r"^entries:\s*", line)]
    if len(starts) != 1:
        raise ValueError("glossary must contain exactly one top-level entries field")
    start = starts[0]
    inline = lines[start].split(":", 1)[1].strip()
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line and not line[0].isspace() and not line.startswith("-"):
            break
        if line.strip():
            body.append(line)
    if inline:
        if inline != "[]" or body:
            raise ValueError("use entries: [] or a block list of glossary entries")
        return []
    if not body:
        raise ValueError("empty glossary must use entries: []")

    entries: list[dict[str, Any]] = []
    entry_indent = len(body[0]) - len(body[0].lstrip())
    field_indent = entry_indent + 2
    fields: dict[str, tuple[str, list[str]]] | None = None
    field: str | None = None

    def finish() -> None:
        if fields is None:
            return
        entry: dict[str, Any] = {}
        for key, (value, continuation) in fields.items():
            if value in {"|", ">"}:
                entry[key] = ("\n" if value == "|" else " ").join(continuation).strip()
            elif value == "" and continuation:
                if not continuation[0].startswith("-"):
                    raise ValueError(f"unsupported block for glossary field {key!r}")
                entry[key] = _block_list(continuation)
            elif continuation:
                raise ValueError(f"unexpected continuation for glossary field {key!r}")
            else:
                entry[key] = _scalar(value)
        entries.append(entry)

    for line in body:
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if indent == entry_indent and (stripped == "-" or stripped.startswith("- ")):
            finish()
            fields = {}
            field = None
            stripped = stripped[1:].strip()
            if not stripped:
                continue
        elif fields is None:
            raise ValueError("glossary entries must be a block list")
        elif indent > field_indent:
            if field is None:
                raise ValueError("glossary continuation has no field")
            fields[field][1].append(stripped)
            continue
        elif indent != field_indent:
            raise ValueError("inconsistent glossary entry indentation")
        match = FIELD_RE.fullmatch(stripped)
        if match is None:
            raise ValueError(f"unsupported glossary field syntax: {stripped!r}")
        field = match.group(1)
        assert fields is not None
        if field in fields:
            raise ValueError(f"duplicate glossary field {field!r}")
        fields[field] = (match.group(2) or "", [])
    finish()
    return entries


def load_approved_term_pairs(path: Path) -> set[tuple[str, str]]:
    """Return approvals from the authoritative glossary, failing closed on bad entries."""
    try:
        text = path.read_text(encoding="utf-8")
        if text.lstrip().startswith("{"):
            document = json.loads(text, object_pairs_hook=_unique_object)
            entries = document.get("entries") if isinstance(document, dict) else None
        else:
            entries = _yaml_entries(text)
        if not isinstance(entries, list):
            raise ValueError("glossary entries must be an array")
        approved: set[tuple[str, str]] = set()
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(f"entries[{index}] must be an object")
            for field in ("source_term", "target_term", "status", "definition_or_context"):
                if not isinstance(entry.get(field), str) or not entry[field].strip():
                    raise ValueError(f"entries[{index}].{field} must be a non-empty string")
            if entry["status"] not in STATUSES:
                raise ValueError(f"entries[{index}] has invalid status {entry['status']!r}")
            evidence = entry.get("evidence")
            if not isinstance(evidence, list) or not evidence or not all(evidence):
                raise ValueError(f"entries[{index}].evidence must be a non-empty array")
            if entry["status"] == "approved":
                approved.add((entry["source_term"], entry["target_term"]))
        return approved
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot verify glossary approvals in {path}: {exc}") from exc
