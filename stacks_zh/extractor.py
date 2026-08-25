from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any

from .records import (
    RecordError,
    load_upstream_commit,
    stamp_unit_hashes,
    validate_units,
    write_jsonl,
)


SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
TAG_RE = re.compile(r"^[0-9A-Z]+$")
TAG_LABEL_RE = re.compile(r"^[A-Za-z0-9._:+-]+$")
SECTION_RE = re.compile(
    r"(?m)^\\section\{(?P<title>[^{}\n]+)\}\s*\n"
    r"\\label\{(?P<label>[^{}\n]+)\}\s*(?:\n|$)"
)
LOCKED_COMMANDS = {
    "cite": "CITE",
    "eqref": "EQREF",
    "pageref": "PAGEREF",
    "ref": "REF",
    "url": "URL",
}
BOOK_LOCAL_LABEL_PREFIXES = (
    "definition-",
    "equation-",
    "example-",
    "exercise-",
    "item-",
    "lemma-",
    "proposition-",
    "remark-",
    "remarks-",
    "section-",
    "situation-",
    "subsection-",
    "subsubsection-",
    "theorem-",
)
STRUCTURAL_PREFIX_RE = re.compile(
    r"(?:(?:\\medskip|\\smallskip|\\bigskip)\s*)?(?:\\noindent)\s*"
)
TRANSLATABLE_WRAPPERS = (
    ("{\\it ", "TEXTITOPEN", "TEXTITCLOSE"),
    ("{\\em ", "EMOPEN", "EMCLOSE"),
    ("\\footnote{", "FOOTNOTEOPEN", "FOOTNOTECLOSE"),
)


def extract_section(
    harvest_dir: Path,
    chapter: str,
    tag: str,
    lock_path: Path,
    output_path: Path,
) -> int:
    """Extract one unlabelled Section body from the locked English harvest."""
    if not SAFE_NAME_RE.fullmatch(chapter) or ".." in chapter:
        raise RecordError(f"invalid chapter name {chapter!r}")
    if not TAG_RE.fullmatch(tag):
        raise RecordError(f"invalid permanent Tag {tag!r}")
    if output_path.exists():
        raise RecordError(f"refusing to overwrite existing unit batch {output_path}")

    _validate_locked_harvest(harvest_dir, lock_path)
    source_path = harvest_dir / f"{chapter}.tex"
    tags_path = harvest_dir / "tags" / "tags"
    try:
        source_text = source_path.read_text(encoding="utf-8")
        tags_text = tags_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordError(f"cannot read locked extraction input: {exc}") from exc

    source_commit = load_upstream_commit(lock_path)
    units = extract_section_units(source_text, tags_text, source_commit, chapter, tag)
    errors = validate_units(units, source_commit)
    if errors:
        raise RecordError("extracted unit validation failed:\n" + "\n".join(errors))
    write_jsonl(output_path, units)
    return len(units)


def extract_tag(
    harvest_dir: Path,
    chapter: str,
    tag: str,
    lock_path: Path,
    output_path: Path,
) -> int:
    """Extract one supported permanent-Tag scope from the locked harvest."""
    if not SAFE_NAME_RE.fullmatch(chapter) or ".." in chapter:
        raise RecordError(f"invalid chapter name {chapter!r}")
    if not TAG_RE.fullmatch(tag):
        raise RecordError(f"invalid permanent Tag {tag!r}")
    if output_path.exists():
        raise RecordError(f"refusing to overwrite existing unit batch {output_path}")

    _validate_locked_harvest(harvest_dir, lock_path)
    source_path = harvest_dir / f"{chapter}.tex"
    tags_path = harvest_dir / "tags" / "tags"
    try:
        source_text = source_path.read_text(encoding="utf-8")
        tags_text = tags_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RecordError(f"cannot read locked extraction input: {exc}") from exc

    source_commit = load_upstream_commit(lock_path)
    units = extract_tag_units(source_text, tags_text, source_commit, chapter, tag)
    errors = validate_units(units, source_commit)
    if errors:
        raise RecordError("extracted unit validation failed:\n" + "\n".join(errors))
    write_jsonl(output_path, units)
    return len(units)


def extract_tag_units(
    source_text: str,
    tags_text: str,
    source_commit: str,
    chapter: str,
    tag: str,
) -> list[dict[str, Any]]:
    """Dispatch a permanent Tag to one of the explicitly supported extractors."""
    full_label = _full_label_for_tag(tags_text, chapter, tag)
    local_label = full_label.removeprefix(f"{chapter}-")
    section_labels = {match.group("label") for match in SECTION_RE.finditer(source_text)}
    if local_label in section_labels or full_label in section_labels:
        return extract_section_units(
            source_text, tags_text, source_commit, chapter, tag
        )
    definition_matches = _labeled_environment_matches(
        source_text, "definition", local_label, full_label
    )
    if definition_matches:
        definition_body = definition_matches[0].group("body")
        if (
            "\\begin{enumerate}" not in definition_body
            and "\\end{enumerate}" not in definition_body
        ):
            return _extract_tagged_statement_units(
                source_text,
                source_commit,
                chapter,
                tag,
                full_label,
                local_label,
                "definition",
                include_adjacent_proof=False,
            )
        return _extract_enumerated_environment_units(
            source_text,
            source_commit,
            chapter,
            tag,
            full_label,
            local_label,
            "definition",
            include_adjacent_proof=False,
        )
    lemma_matches = _labeled_environment_matches(
        source_text, "lemma", local_label, full_label
    )
    if lemma_matches:
        lemma_body = lemma_matches[0].group("body")
        if "\\begin{enumerate}" in lemma_body or "\\end{enumerate}" in lemma_body:
            return _extract_enumerated_environment_units(
                source_text,
                source_commit,
                chapter,
                tag,
                full_label,
                local_label,
                "lemma",
                include_adjacent_proof=True,
            )
        return _extract_tagged_statement_units(
            source_text,
            source_commit,
            chapter,
            tag,
            full_label,
            local_label,
            "lemma",
            include_adjacent_proof=True,
        )
    raise RecordError(
        f"Tag {tag} does not select a supported Section, definition, "
        f"or lemma ({local_label!r})"
    )


def extract_section_units(
    source_text: str,
    tags_text: str,
    source_commit: str,
    chapter: str,
    tag: str,
) -> list[dict[str, Any]]:
    """Return stamped units for a deliberately narrow, policy-safe Section scope."""
    full_label = _full_label_for_tag(tags_text, chapter, tag)
    local_label = full_label.removeprefix(f"{chapter}-")

    sections = list(SECTION_RE.finditer(source_text))
    matching = [
        (index, match)
        for index, match in enumerate(sections)
        if match.group("label") in {local_label, full_label}
    ]
    if len(matching) != 1:
        raise RecordError(
            f"expected exactly one Section label for Tag {tag} ({local_label!r}); "
            f"found {len(matching)}"
        )
    section_index, section_match = matching[0]
    body_end = (
        sections[section_index + 1].start()
        if section_index + 1 < len(sections)
        else len(source_text)
    )
    body = source_text[section_match.end() : body_end]
    nested_label_matches = list(re.finditer(r"(?m)^\\label\{([^{}]+)\}[ \t]*$", body))
    truncated_for_nested_scope = bool(nested_label_matches)
    if nested_label_matches:
        body = _section_prologue_before_nested_scope(
            body, nested_label_matches[0], tag
        )
    if _contains_unescaped_comment(body):
        raise RecordError("Section extraction blocks TeX comments in the selected body")

    units: list[dict[str, Any]] = []
    title_text, title_placeholders = _protect_natural_text(
        section_match.group("title"), chapter
    )
    units.append(
        _make_unit(
            unit_id=f"tag:{tag}:title",
            parent_tag=tag,
            chapter=chapter,
            node_kind="section_title",
            risk_level="R1",
            source_commit=source_commit,
            source_text=title_text,
            placeholders=title_placeholders,
            prefix="\\section{",
            suffix=f"}}\n\\label{{{full_label}}}\n\n",
        )
    )

    paragraph_count = 0
    display_count = 0
    for kind, value, prefix in _split_section_body(body):
        if kind == "paragraph":
            paragraph_count += 1
            protected_text, placeholders = _protect_natural_text(value, chapter)
            units.append(
                _make_unit(
                    unit_id=f"tag:{tag}:p{paragraph_count:03d}",
                    parent_tag=tag,
                    chapter=chapter,
                    node_kind="paragraph",
                    risk_level="R2",
                    source_commit=source_commit,
                    source_text=protected_text,
                    placeholders=placeholders,
                    prefix=prefix,
                    suffix="\n",
                )
            )
        elif kind == "display":
            display_count += 1
            units.append(
                _make_unit(
                    unit_id=f"tag:{tag}:display{display_count:03d}",
                    parent_tag=tag,
                    chapter=chapter,
                    node_kind="display_math",
                    risk_level="R2",
                    source_commit=source_commit,
                    source_text="<MATH_0001>",
                    placeholders={"MATH_0001": value},
                    prefix=prefix,
                    suffix="\n",
                )
            )
        else:  # pragma: no cover - internal invariant
            raise AssertionError(kind)
    if len(units) == 1 and not truncated_for_nested_scope:
        raise RecordError(f"Section Tag {tag} has no extractable body")
    if len(units) > 1:
        units[-1]["render"]["suffix"] = "\n\n"
    return [stamp_unit_hashes(unit) for unit in units]


def _section_prologue_before_nested_scope(
    body: str,
    label_match: re.Match[str],
    tag: str,
) -> str:
    environment_starts = list(
        re.finditer(
            r"(?m)^\\begin\{[A-Za-z*]+\}(?:\[[^\n]*\])?[ \t]*\n",
            body[: label_match.start()],
        )
    )
    if not environment_starts:
        raise RecordError(
            f"Section Tag {tag} has nested label {label_match.group(1)!r} "
            "outside an identifiable child environment"
        )
    environment_start = environment_starts[-1]
    between = body[environment_start.end() : label_match.start()]
    if between.strip():
        raise RecordError(
            f"Section Tag {tag} has unsupported content before nested label "
            f"{label_match.group(1)!r}"
        )
    return body[: environment_start.start()]


def _extract_enumerated_environment_units(
    source_text: str,
    source_commit: str,
    chapter: str,
    tag: str,
    full_label: str,
    local_label: str,
    environment: str,
    *,
    include_adjacent_proof: bool,
) -> list[dict[str, Any]]:
    matches = _labeled_environment_matches(
        source_text, environment, local_label, full_label
    )
    if len(matches) != 1:
        raise RecordError(
            f"expected exactly one enumerated {environment} for Tag {tag} "
            f"({local_label!r}); found {len(matches)}"
        )
    match = matches[0]
    body = match.group("body")
    _validate_simple_environment_body(body, environment)
    if body.count("\\begin{enumerate}") != 1 or body.count("\\end{enumerate}") != 1:
        raise RecordError(
            f"tagged {environment} extraction currently requires exactly one enumerate"
        )
    before, remainder = body.split("\\begin{enumerate}", 1)
    item_text, after = remainder.split("\\end{enumerate}", 1)
    before_blocks = _split_section_body(before)
    after_blocks = _split_section_body(after)
    if len(before_blocks) != 1 or before_blocks[0][0] != "paragraph":
        raise RecordError(f"enumerated {environment} requires one leading text node")
    if len(after_blocks) > 1 or (
        after_blocks and after_blocks[0][0] != "paragraph"
    ):
        raise RecordError(
            f"enumerated {environment} permits at most one trailing text node"
        )

    units: list[dict[str, Any]] = []
    leading_text, leading_prefix = before_blocks[0][1], before_blocks[0][2]
    if leading_prefix:
        raise RecordError(f"{environment} leading text cannot have a structural prefix")
    protected, placeholders = _protect_natural_text(leading_text, chapter)
    units.append(
        _make_unit(
            unit_id=f"tag:{tag}:statement",
            parent_tag=tag,
            chapter=chapter,
            node_kind=environment,
            risk_level="R3",
            source_commit=source_commit,
            source_text=protected,
            placeholders=placeholders,
            prefix=f"\\begin{{{environment}}}\n\\label{{{full_label}}}\n",
            suffix="\n\\begin{enumerate}\n",
        )
    )

    item_matches = list(re.finditer(r"(?m)^\\item[ \t]+", item_text))
    if not item_matches:
        raise RecordError("enumerate has no list items")
    if item_text[: item_matches[0].start()].strip():
        raise RecordError("enumerate contains text before its first list item")
    for index, item_match in enumerate(item_matches, start=1):
        item_end = (
            item_matches[index].start()
            if index < len(item_matches)
            else len(item_text)
        )
        raw_item = item_text[item_match.end() : item_end].strip()
        if not raw_item:
            raise RecordError(f"enumerate item {index} is empty")
        units.extend(
            _extract_enumerated_item_units(
                raw_item, source_commit, chapter, tag, index
            )
        )
    units[-1]["render"]["suffix"] += "\\end{enumerate}\n"

    if after_blocks:
        trailing_text, trailing_prefix = after_blocks[0][1], after_blocks[0][2]
        if trailing_prefix:
            raise RecordError(
                f"{environment} trailing text cannot have a structural prefix"
            )
        protected, placeholders = _protect_natural_text(trailing_text, chapter)
        units.append(
            _make_unit(
                unit_id=f"tag:{tag}:p001",
                parent_tag=tag,
                chapter=chapter,
                node_kind="paragraph",
                risk_level="R3",
                source_commit=source_commit,
                source_text=protected,
                placeholders=placeholders,
                prefix="",
                suffix=f"\n\\end{{{environment}}}\n\n",
            )
        )
    else:
        units[-1]["render"]["suffix"] += f"\\end{{{environment}}}\n\n"
    if include_adjacent_proof:
        units.extend(
            _extract_adjacent_simple_proof_units(
                source_text[match.end() :], source_commit, chapter, tag
            )
        )
    return [stamp_unit_hashes(unit) for unit in units]


def _extract_enumerated_item_units(
    raw_item: str,
    source_commit: str,
    chapter: str,
    tag: str,
    item_index: int,
) -> list[dict[str, Any]]:
    blocks = _split_section_body(raw_item)
    if not blocks or blocks[0][0] != "paragraph":
        raise RecordError(f"enumerate item {item_index} requires leading text")

    units: list[dict[str, Any]] = []
    paragraph_count = 0
    display_count = 0
    item_id = f"item{item_index:03d}"
    for block_index, (kind, value, structural_prefix) in enumerate(blocks):
        if kind == "paragraph":
            protected, placeholders = _protect_natural_text(value, chapter)
            if block_index == 0:
                if structural_prefix:
                    raise RecordError(
                        f"enumerate item {item_index} leading text cannot have "
                        "a structural prefix"
                    )
                unit_id = f"tag:{tag}:{item_id}"
                node_kind = "list_item"
                prefix = "\\item "
            else:
                paragraph_count += 1
                unit_id = f"tag:{tag}:{item_id}-p{paragraph_count:03d}"
                node_kind = "list_item_paragraph"
                prefix = structural_prefix
            units.append(
                _make_unit(
                    unit_id=unit_id,
                    parent_tag=tag,
                    chapter=chapter,
                    node_kind=node_kind,
                    risk_level="R3",
                    source_commit=source_commit,
                    source_text=protected,
                    placeholders=placeholders,
                    prefix=prefix,
                    suffix="\n",
                )
            )
        elif kind == "display":
            display_count += 1
            units.append(
                _make_unit(
                    unit_id=f"tag:{tag}:{item_id}-display{display_count:03d}",
                    parent_tag=tag,
                    chapter=chapter,
                    node_kind="display_math",
                    risk_level="R3",
                    source_commit=source_commit,
                    source_text="<MATH_0001>",
                    placeholders={"MATH_0001": value},
                    prefix=structural_prefix,
                    suffix="\n",
                )
            )
        else:  # pragma: no cover - internal invariant
            raise AssertionError(kind)
    return units


def _extract_tagged_statement_units(
    source_text: str,
    source_commit: str,
    chapter: str,
    tag: str,
    full_label: str,
    local_label: str,
    environment: str,
    *,
    include_adjacent_proof: bool,
) -> list[dict[str, Any]]:
    matches = _labeled_environment_matches(
        source_text, environment, local_label, full_label
    )
    if len(matches) != 1:
        raise RecordError(
            f"expected exactly one {environment} for Tag {tag} "
            f"({local_label!r}); found {len(matches)}"
        )
    match = matches[0]
    body = match.group("body")
    _validate_simple_environment_body(body, environment)
    blocks = _split_section_body(body)
    if not blocks or blocks[0][0] != "paragraph":
        raise RecordError(f"tagged {environment} requires leading natural-language text")

    units: list[dict[str, Any]] = []
    paragraph_count = 0
    display_count = 0
    for block_index, (kind, value, structural_prefix) in enumerate(blocks):
        if kind == "paragraph":
            protected, placeholders = _protect_natural_text(value, chapter)
            if block_index == 0:
                if structural_prefix:
                    raise RecordError(
                        f"tagged {environment} leading text cannot have a structural prefix"
                    )
                unit_id = f"tag:{tag}:statement"
                node_kind = environment
                prefix = (
                    f"\\begin{{{environment}}}\n"
                    f"\\label{{{full_label}}}\n"
                )
            else:
                paragraph_count += 1
                unit_id = f"tag:{tag}:p{paragraph_count:03d}"
                node_kind = "paragraph"
                prefix = structural_prefix
            units.append(
                _make_unit(
                    unit_id=unit_id,
                    parent_tag=tag,
                    chapter=chapter,
                    node_kind=node_kind,
                    risk_level="R3",
                    source_commit=source_commit,
                    source_text=protected,
                    placeholders=placeholders,
                    prefix=prefix,
                    suffix="\n",
                )
            )
        elif kind == "display":
            display_count += 1
            units.append(
                _make_unit(
                    unit_id=f"tag:{tag}:display{display_count:03d}",
                    parent_tag=tag,
                    chapter=chapter,
                    node_kind="display_math",
                    risk_level="R3",
                    source_commit=source_commit,
                    source_text="<MATH_0001>",
                    placeholders={"MATH_0001": value},
                    prefix=structural_prefix,
                    suffix="\n",
                )
            )
        else:  # pragma: no cover - internal invariant
            raise AssertionError(kind)
    units[-1]["render"]["suffix"] = f"\n\\end{{{environment}}}\n\n"
    if include_adjacent_proof:
        units.extend(
            _extract_adjacent_simple_proof_units(
                source_text[match.end() :], source_commit, chapter, tag
            )
        )
    return [stamp_unit_hashes(unit) for unit in units]


def _extract_adjacent_simple_proof_units(
    tail: str,
    source_commit: str,
    chapter: str,
    tag: str,
) -> list[dict[str, Any]]:
    proof_re = re.compile(
        r"(?ms)\A[ \t\n]*\\begin\{proof\}[ \t]*\n"
        r"(?P<body>.*?)^\\end\{proof\}[ \t]*(?:\n|$)"
    )
    match = proof_re.match(tail)
    if match is None:
        return []
    body = match.group("body")
    _validate_simple_environment_body(body, "proof")
    blocks = _split_section_body(body)
    if not blocks or blocks[0][0] != "paragraph":
        raise RecordError("adjacent proof requires leading natural-language text")

    units: list[dict[str, Any]] = []
    paragraph_count = 0
    display_count = 0
    for block_index, (kind, value, structural_prefix) in enumerate(blocks):
        if kind == "paragraph":
            paragraph_count += 1
            protected, placeholders = _protect_natural_text(value, chapter)
            units.append(
                _make_unit(
                    unit_id=f"tag:{tag}:proof-p{paragraph_count:03d}",
                    parent_tag=tag,
                    chapter=chapter,
                    node_kind="proof" if block_index == 0 else "proof_paragraph",
                    risk_level="R3",
                    source_commit=source_commit,
                    source_text=protected,
                    placeholders=placeholders,
                    prefix=("\\begin{proof}\n" if block_index == 0 else "")
                    + structural_prefix,
                    suffix="\n",
                )
            )
        elif kind == "display":
            display_count += 1
            units.append(
                _make_unit(
                    unit_id=f"tag:{tag}:proof-display{display_count:03d}",
                    parent_tag=tag,
                    chapter=chapter,
                    node_kind="display_math",
                    risk_level="R3",
                    source_commit=source_commit,
                    source_text="<MATH_0001>",
                    placeholders={"MATH_0001": value},
                    prefix=structural_prefix,
                    suffix="\n",
                )
            )
        else:  # pragma: no cover - internal invariant
            raise AssertionError(kind)
    units[-1]["render"]["suffix"] = "\n\\end{proof}\n\n"
    return units


def _validate_simple_environment_body(body: str, environment: str) -> None:
    if re.search(r"\\label\{", body):
        raise RecordError(f"{environment} contains a nested label")
    if _contains_unescaped_comment(body):
        raise RecordError(f"{environment} extraction blocks TeX comments")


def _labeled_environment_matches(
    source_text: str,
    environment: str,
    local_label: str,
    full_label: str,
) -> list[re.Match[str]]:
    labels = "|".join(
        re.escape(label) for label in dict.fromkeys((local_label, full_label))
    )
    pattern = re.compile(
        rf"(?ms)^\\begin\{{{re.escape(environment)}\}}[ \t]*\n"
        rf"\\label\{{(?:{labels})\}}[ \t]*\n"
        rf"(?P<body>.*?)^\\end\{{{re.escape(environment)}\}}[ \t]*(?:\n|$)"
    )
    return list(pattern.finditer(source_text))


def _split_section_body(body: str) -> list[tuple[str, str, str]]:
    blocks: list[tuple[str, str, str]] = []
    position = 0
    pending_prefix = ""
    while position < len(body):
        while position < len(body) and body[position].isspace():
            position += 1
        if position >= len(body):
            break

        structural_match = STRUCTURAL_PREFIX_RE.match(body, position)
        if structural_match and structural_match.end() > position:
            if pending_prefix:
                raise RecordError("multiple structural prefixes before one text node")
            raw_prefix = structural_match.group(0).rstrip()
            if not raw_prefix.startswith("\\"):
                raise RecordError("invalid structural prefix")
            pending_prefix = re.sub(r"\s+", "", raw_prefix) + "\n"
            position = structural_match.end()
            continue

        if body.startswith("$$", position):
            end = body.find("$$", position + 2)
            if end < 0:
                raise RecordError("unterminated display math in selected Section")
            if pending_prefix:
                raise RecordError("structural prefix before display math is unsupported")
            blocks.append(("display", body[position : end + 2], ""))
            position = end + 2
            continue

        end, separator_end = _find_paragraph_end(body, position)
        paragraph = body[position:end].strip()
        if not paragraph:
            raise RecordError("empty natural-language paragraph in selected Section")
        blocks.append(("paragraph", paragraph, pending_prefix))
        pending_prefix = ""
        position = separator_end

    if pending_prefix:
        raise RecordError("dangling structural prefix at end of selected Section")
    return blocks


def _find_paragraph_end(body: str, start: int) -> tuple[int, int]:
    position = start
    inline_math = False
    while position < len(body):
        if body.startswith("$$", position) and not inline_math:
            return position, position
        character = body[position]
        if character == "$" and (position == 0 or body[position - 1] != "\\"):
            inline_math = not inline_math
            position += 1
            continue
        if character == "\n" and not inline_math:
            separator = re.match(r"\n[ \t]*\n+", body[position:])
            if separator:
                return position, position + separator.end()
        position += 1
    if inline_math:
        raise RecordError("unterminated inline math in selected Section")
    return len(body), len(body)


def _protect_natural_text(
    text: str, chapter: str
) -> tuple[str, dict[str, str]]:
    output: list[str] = []
    placeholders: dict[str, str] = {}
    counters: dict[str, int] = {}
    _protect_natural_fragment(text, chapter, output, placeholders, counters)
    normalized = " ".join("".join(output).split())
    if not normalized:
        raise RecordError("natural-language node became empty after protection")
    return normalized, placeholders


def _protect_natural_fragment(
    text: str,
    chapter: str,
    output: list[str],
    placeholders: dict[str, str],
    counters: dict[str, int],
) -> None:
    position = 0
    while position < len(text):
        if text.startswith("$$", position):
            raise RecordError("display math must be a separate extraction node")
        wrapper = next(
            (
                (prefix, open_kind, close_kind)
                for prefix, open_kind, close_kind in TRANSLATABLE_WRAPPERS
                if text.startswith(prefix, position)
            ),
            None,
        )
        if wrapper is not None:
            prefix, open_kind, close_kind = wrapper
            group_start = (
                position if prefix.startswith("{") else position + len(prefix) - 1
            )
            group_end = _find_balanced_brace(text, group_start)
            output.append(
                _add_placeholder(
                    placeholders, counters, open_kind, prefix
                )
            )
            _protect_natural_fragment(
                text[position + len(prefix) : group_end],
                chapter,
                output,
                placeholders,
                counters,
            )
            output.append(
                _add_placeholder(placeholders, counters, close_kind, "}")
            )
            position = group_end + 1
            continue
        character = text[position]
        if character == "$":
            end = _find_unescaped(text, "$", position + 1)
            if end < 0:
                raise RecordError("unterminated inline math in natural-language node")
            value = text[position : end + 1]
            token = _add_placeholder(placeholders, counters, "MATH", value)
            output.append(token)
            position = end + 1
            continue
        if character == "\\":
            if text.startswith("\\ ", position):
                output.append(
                    _add_placeholder(
                        placeholders, counters, "TEXSPACE", "\\ "
                    )
                )
                position += 2
                continue
            command_match = re.match(r"\\([A-Za-z@]+)", text[position:])
            if command_match is None:
                raise RecordError(
                    f"unsupported TeX control sequence near {text[position:position + 20]!r}"
                )
            command = command_match.group(1)
            placeholder_kind = LOCKED_COMMANDS.get(command)
            if placeholder_kind is None:
                raise RecordError(f"unknown or unsupported text command \\{command}")
            argument_start = position + command_match.end()
            if argument_start >= len(text) or text[argument_start] != "{":
                raise RecordError(f"\\{command} requires one braced argument")
            argument_end = _find_balanced_brace(text, argument_start)
            value = text[position : argument_end + 1]
            if command in {"eqref", "pageref", "ref"}:
                argument = text[argument_start + 1 : argument_end]
                if argument.startswith(BOOK_LOCAL_LABEL_PREFIXES):
                    value = f"\\{command}{{{chapter}-{argument}}}"
            token = _add_placeholder(
                placeholders, counters, placeholder_kind, value
            )
            output.append(token)
            position = argument_end + 1
            continue
        if character in "{}":
            raise RecordError("unprotected TeX grouping in natural-language node")
        if character == "%" and (position == 0 or text[position - 1] != "\\"):
            raise RecordError("TeX comments are unsupported in natural-language nodes")
        output.append(character)
        position += 1


def _add_placeholder(
    placeholders: dict[str, str],
    counters: dict[str, int],
    kind: str,
    value: str,
) -> str:
    counters[kind] = counters.get(kind, 0) + 1
    name = f"{kind}_{counters[kind]:04d}"
    placeholders[name] = value
    return f"<{name}>"


def _find_unescaped(text: str, needle: str, start: int) -> int:
    position = start
    while True:
        position = text.find(needle, position)
        if position < 0:
            return -1
        backslashes = 0
        cursor = position - 1
        while cursor >= 0 and text[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            return position
        position += len(needle)


def _find_balanced_brace(text: str, start: int) -> int:
    depth = 0
    for position in range(start, len(text)):
        character = text[position]
        if character == "{" and (position == 0 or text[position - 1] != "\\"):
            depth += 1
        elif character == "}" and (position == 0 or text[position - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return position
    raise RecordError("unterminated braced argument in protected command")


def _load_tag_map(tags_text: str) -> dict[str, str]:
    tag_to_label: dict[str, str] = {}
    labels: set[str] = set()
    for line_number, line in enumerate(tags_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = [part.strip() for part in stripped.split(",")]
        if len(parts) != 2:
            raise RecordError(f"tags/tags:{line_number}: expected TAG,full_label")
        tag, label = parts
        if not TAG_RE.fullmatch(tag):
            raise RecordError(f"tags/tags:{line_number}: invalid Tag {tag!r}")
        if not TAG_LABEL_RE.fullmatch(label):
            raise RecordError(f"tags/tags:{line_number}: invalid label {label!r}")
        if tag in tag_to_label:
            raise RecordError(f"tags/tags:{line_number}: duplicate Tag {tag}")
        if label in labels:
            raise RecordError(f"tags/tags:{line_number}: duplicate label {label}")
        tag_to_label[tag] = label
        labels.add(label)
    if not tag_to_label:
        raise RecordError("tags/tags has no permanent Tag mappings")
    return tag_to_label


def _full_label_for_tag(tags_text: str, chapter: str, tag: str) -> str:
    tag_to_label = _load_tag_map(tags_text)
    full_label = tag_to_label.get(tag)
    if full_label is None:
        raise RecordError(f"permanent Tag {tag!r} is absent from tags/tags")
    chapter_prefix = f"{chapter}-"
    if not full_label.startswith(chapter_prefix):
        raise RecordError(
            f"permanent Tag {tag} maps to {full_label!r}, not chapter {chapter!r}"
        )
    return full_label


def _contains_unescaped_comment(text: str) -> bool:
    for position, character in enumerate(text):
        if character != "%":
            continue
        backslashes = 0
        cursor = position - 1
        while cursor >= 0 and text[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            return True
    return False


def _make_unit(
    *,
    unit_id: str,
    parent_tag: str,
    chapter: str,
    node_kind: str,
    risk_level: str,
    source_commit: str,
    source_text: str,
    placeholders: dict[str, str],
    prefix: str,
    suffix: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "unit_id": unit_id,
        "parent_tag": parent_tag,
        "chapter": chapter,
        "node_kind": node_kind,
        "risk_level": risk_level,
        "source_commit": source_commit,
        "source_text": source_text,
        "source_status": "CURRENT",
        "placeholders": placeholders,
        "render": {"prefix": prefix, "suffix": suffix},
    }


def _validate_locked_harvest(harvest_dir: Path, lock_path: Path) -> None:
    try:
        lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RecordError(f"cannot read upstream lock {lock_path}: {exc}") from exc
    expected = {
        "remote": lock.get("repository"),
        "commit": lock.get("commit"),
        "date": lock.get("commit_date"),
    }
    if not all(isinstance(value, str) and value for value in expected.values()):
        raise RecordError("upstream.lock requires repository, commit, and commit_date")
    if not (harvest_dir / "preamble.tex").is_file():
        raise RecordError(f"invalid harvest directory {harvest_dir}")

    commands = {
        "remote": ["git", "remote", "get-url", "origin"],
        "commit": ["git", "rev-parse", "HEAD"],
        "date": ["git", "show", "-s", "--format=%cs", "HEAD"],
        "dirty": ["git", "status", "--short", "--untracked-files=no"],
    }
    actual: dict[str, str] = {}
    for name, command in commands.items():
        try:
            result = subprocess.run(
                command,
                cwd=harvest_dir,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RecordError(f"cannot verify harvest with {' '.join(command)}: {exc}") from exc
        actual[name] = result.stdout.strip()
    for name in ("remote", "commit", "date"):
        if actual[name] != expected[name]:
            raise RecordError(
                f"harvest {name} mismatch: expected {expected[name]!r}, "
                f"found {actual[name]!r}"
            )
    if actual["dirty"]:
        raise RecordError("harvest has tracked modifications:\n" + actual["dirty"])
