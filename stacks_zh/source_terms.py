from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .records import RecordError, PLACEHOLDER_TOKEN_RE, expected_unit_hashes, load_jsonl, load_upstream_commit, restore_placeholders, sha256_value
from .schema_validation import validate_named_schema
from .terminology import load_approved_term_pairs


def _space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def source_tex_hash(unit: dict[str, Any]) -> str:
    return sha256_value(unit["render"]["prefix"] + restore_placeholders(unit, unit["source_text"]) + unit["render"]["suffix"])


def source_projection(unit: dict[str, Any]) -> tuple[str, list[str]]:
    """Expose prose through formatting wrappers without reading protected math."""
    source = unit["source_text"]
    pieces: list[str] = []
    declarations: list[str] = []
    opened: dict[tuple[str, str], int] = {}
    cursor = 0
    for match in PLACEHOLDER_TOKEN_RE.finditer(source):
        pieces.append(source[cursor:match.start()])
        name, number = match.group(1).rsplit("_", 1)
        if name.endswith("OPEN") or name.endswith("CLOSE"):
            base = name.removesuffix("OPEN").removesuffix("CLOSE")
            if base in {"TEXTIT", "EMPH"}:
                key = (base, number)
                if name.endswith("OPEN"):
                    opened[key] = len("".join(pieces))
                elif key in opened:
                    body = "".join(pieces)[opened.pop(key):]
                    # Math-qualified declarations still expose their prose parts.
                    for phrase in PLACEHOLDER_TOKEN_RE.split(body)[::2]:
                        phrase = _space(phrase).strip(" -.,:;`'\"()")
                        if PLACEHOLDER_TOKEN_RE.search(body):
                            phrase = re.sub(r"\s+(?:of|over|in|between|with|to|on|from)$", "", phrase, flags=re.IGNORECASE)
                        if phrase and re.search(r"[A-Za-z]", phrase):
                            declarations.append(phrase)
            # Natural-language formatting and footnote wrappers are transparent.
        else:
            pieces.append(match.group(0))
        cursor = match.end()
    pieces.append(source[cursor:])
    text = _space("".join(pieces))
    if unit.get("node_kind") != "definition" and not re.search(r"\b(?:called|call|say|defined)\b", text, re.IGNORECASE):
        declarations = []
    # Articles and trailing connectors belong to the surrounding sentence;
    # protected formulas supply qualifiers outside the exposed lexical core.
    declarations = [re.sub(r"^(?:a|an|the)\s+", "", phrase, flags=re.IGNORECASE) for phrase in declarations]
    return text, sorted(set(declarations))


def _matches(text: str, phrase: str, *, ignore_case: bool = False):
    expression = r"(?<![\w])" + re.escape(_space(phrase)) + r"(?![\w])"
    return list(re.finditer(expression, text, re.IGNORECASE if ignore_case else 0))


def load_catalog(root: Path) -> dict[str, Any]:
    path = root / "config/source-terms.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RecordError(f"cannot read source term catalog: {exc}") from exc
    errors = validate_named_schema(value, "source-terms.schema.json", str(path))
    if errors:
        raise RecordError("\n".join(errors))
    seen_ids: set[str] = set()
    seen_forms: set[str] = set()
    for entry in value["terms"]:
        if not entry["forms"] or not entry["evidence"]:
            raise RecordError("source term catalog requires forms and source evidence")
        if entry["id"] in seen_ids:
            raise RecordError("duplicate source term concept ID")
        seen_ids.add(entry["id"])
        for form in entry["forms"]:
            key = _space(form).casefold()
            if key in seen_forms or form != _space(form):
                raise RecordError(f"duplicate or noncanonical source term form: {form}")
            if PLACEHOLDER_TOKEN_RE.search(form) or re.search(r"[\\{}$%]", form):
                raise RecordError("catalog forms must be exposed prose, not protected TeX")
            seen_forms.add(key)
    return value


def source_inventory(unit: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    """Requirements depend only on source nodes and the explicit catalog scope."""
    if any(unit.get(key) != expected for key, expected in expected_unit_hashes(unit).items()):
        raise RecordError(f"{unit['unit_id']}: source inventory refuses stale unit hashes")
    text, declarations = source_projection(unit)
    matches = []
    for entry in catalog["terms"]:
        if entry["chapters"] and unit["chapter"] not in entry["chapters"]:
            continue
        for form in entry["forms"]:
            for match in _matches(text, form, ignore_case=True):
                matches.append((match.start(), match.end(), entry["id"], "catalog"))
    exclusions = {phrase.casefold() for phrase in catalog["nonmathematical_declarations"]}
    for declaration in declarations:
        if declaration.casefold() in exclusions:
            continue
        for match in _matches(text, declaration):
            matches.append((match.start(), match.end(), declaration, "source-declaration"))
    # Longest phrases win; nested generic words are not double-counted.
    matches.sort(key=lambda item: (item[0], -(item[1] - item[0]), item[3], item[2]))
    occurrences = []
    end = -1
    for start, stop, concept, rule in matches:
        if start < end:
            continue
        occurrences.append({"source_term": text[start:stop], "projection_start": start,
                            "projection_end": stop, "concept": concept, "rule": rule})
        end = stop
    return {"unit_id": unit["unit_id"], "source_commit": unit["source_commit"],
            "source_text_hash": unit["source_text_hash"],
            "source_structure_hash": unit["source_structure_hash"],
            "catalog_hash": sha256_value(catalog), "occurrences": occurrences}


def validate_source_terms(unit: dict[str, Any], candidate: dict[str, Any], catalog: dict[str, Any], approved: set[tuple[str, str]] | None = None) -> list[str]:
    uid = unit["unit_id"]
    inventory = source_inventory(unit, catalog)
    source, _ = source_projection(unit)
    declarations = candidate.get("term_occurrences")
    if not isinstance(declarations, list):
        return [f"{uid}: term_occurrences must be an array"]
    errors: list[str] = []
    valid = []
    unknown = candidate.get("unknown_terms")
    translation = candidate.get("translation")
    if not isinstance(unknown, list) or not isinstance(translation, str):
        return [f"{uid}: unknown_terms must be an array and translation a string"]
    pending = {(item["source_term"], item["target_term"]) for item in unknown
               if isinstance(item, dict) and all(isinstance(item.get(field), str) and item[field].strip()
                                                for field in ("source_term", "target_term", "context"))}
    target_cursor = 0
    for index, declaration in enumerate(declarations):
        if not isinstance(declaration, dict) or any(not isinstance(declaration.get(field), str) or not declaration[field].strip() for field in ("source_term", "target_term")):
            errors.append(f"{uid}: malformed term occurrence {index}")
            continue
        english, chinese = declaration["source_term"], declaration["target_term"]
        if (english, chinese) not in (approved or set()):
            if (english, chinese) not in pending or candidate.get("term_status") != "DECISION_REQUIRED":
                errors.append(f"{uid}: unapproved term lacks pending contextual evidence: {english}")
        literal = f"{chinese}（{english}）"
        position = translation.find(literal, target_cursor)
        if position < 0:
            errors.append(f"{uid}: missing or repeated bilingual display: {literal}")
        else:
            target_cursor = position + len(literal)
        valid.append((index, _space(english)))
    # Longer phrases receive source spans first, so a later short word cannot
    # consume the source of an earlier compound. Counts and case stay exact.
    assigned: list[tuple[int, int, str]] = []
    for index, english in sorted(valid, key=lambda item: (-len(item[1]), item[0])):
        available = [match for match in _matches(source, english)
                     if not any(match.start() < stop and start < match.end() for start, stop, _ in assigned)]
        if not available:
            errors.append(f"{uid}: declared term has no unused exact source occurrence: {english}")
            continue
        match = available[0]
        assigned.append((match.start(), match.end(), english))
    missing = Counter(item["source_term"] for item in inventory["occurrences"]
                      if not any(start <= item["projection_start"] and item["projection_end"] <= stop
                                 and (english == item["source_term"] or re.sub(r"^(?:a|an|the) ", "", english, flags=re.IGNORECASE) == item["source_term"])
                                 for start, stop, english in assigned))
    for english, count in sorted(missing.items()):
        errors.append(f"{uid}: missing source-side term coverage ({count}): {english}")
    return errors


def audit_repository_terms(root: Path) -> tuple[dict[str, Any], list[str]]:
    catalog = load_catalog(root)
    approved = load_approved_term_pairs(root / "config/glossary.yml")
    source_commit = load_upstream_commit(root / "upstream.lock")
    if catalog["source_commit"] != source_commit:
        raise RecordError("source term catalog uses a different locked source commit")
    units = {}
    batches = {}
    for path in sorted((root / "translation-data/units").glob("*.jsonl")):
        rows = load_jsonl(path)
        for row in rows:
            if row["unit_id"] in units:
                raise RecordError(f"duplicate active source unit: {row['unit_id']}")
            if row["source_commit"] != source_commit:
                raise RecordError(f"different source commit: {row['unit_id']}")
            units[row["unit_id"]] = row
        batches[path.stem] = rows
    # Evidence is English source, never a candidate's term metadata.
    errors = []
    by_tex = {}
    for row in units.values():
        by_tex.setdefault((row["chapter"], source_tex_hash(row)), []).append(row)
    for entry in catalog["terms"]:
        for evidence in entry["evidence"]:
            rows = by_tex.get((evidence["chapter"], evidence["source_tex_hash"]), [])
            if (not any(_matches(source_projection(row)[0], evidence["source_term"]) for row in rows)
                    or evidence["source_term"].casefold() not in {form.casefold() for form in entry["forms"]}):
                errors.append(f"{entry['id']}: catalog evidence is absent from current English source")
    report = {"schema_version": 1, "source_commit": source_commit,
              "catalog_hash": sha256_value(catalog), "unit_count": len(units),
              "batch_count": len(batches), "required_occurrences": 0, "units": [], "candidates": []}
    for row in units.values():
        inventory = source_inventory(row, catalog)
        report["units"].append(inventory)
        report["required_occurrences"] += len(inventory["occurrences"])
    for path in sorted((root / "translation-data/candidates").glob("*/*.jsonl")):
        rows = load_jsonl(path)
        if path.stem not in batches or Counter(row["unit_id"] for row in rows) != Counter(row["unit_id"] for row in batches.get(path.stem, [])):
            errors.append(f"{path.relative_to(root)}: candidate batch does not exactly cover its source units")
        for candidate in rows:
            row = units.get(candidate["unit_id"])
            findings = ([f"unknown source unit: {candidate['unit_id']}"] if row is None
                        else validate_source_terms(row, candidate, catalog, approved))
            report["candidates"].append({"path": str(path.relative_to(root)),
                                         "unit_id": candidate["unit_id"], "errors": findings})
            errors.extend(findings)
    candidate_stems = {path.stem for path in (root / "translation-data/candidates").glob("*/*.jsonl")}
    for stem in sorted(set(batches) - candidate_stems):
        errors.append(f"{stem}: source batch has no candidate coverage")
    return report, errors
