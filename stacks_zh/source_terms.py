from __future__ import annotations

from .validation_io import glob_paths as _input_glob, read_text as _input_text

import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from .records import RecordError, PLACEHOLDER_TOKEN_RE, expected_unit_hashes, is_font_wrapper, load_jsonl, load_upstream_commit, restore_placeholders, sha256_value, term_display_text
from .schema_validation import validate_named_schema
from .terminology import load_approved_term_pairs


def _space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def source_tex_hash(unit: dict[str, Any]) -> str:
    return sha256_value(unit["render"]["prefix"] + restore_placeholders(unit, unit["source_text"], _source_replay=True) + unit["render"]["suffix"])


def _qualified_declaration_parts(body: str, unit: dict[str, Any]) -> list[str] | None:
    """Recognize complete witnessed phrases, never arbitrary prose fragments.

    A protected ordinal/object can split an italic noun phrase into articles,
    suffixes and connectors. Those fragments are not independently named terms.
    Keep the real lexical cores; all other declarations retain the old parser.
    """
    text = _space(body)
    math = r'<MATH_[0-9]{4}>'
    names = PLACEHOLDER_TOKEN_RE.findall(text)
    if names and all(name in unit['placeholders'] for name in names):
        if re.fullmatch(r'(?:the )?' + math + r'th cohomology group of the abelian sheaf '
                        + math + r' over the object ' + math, text):
            return ['cohomology group', 'abelian sheaf', 'object']
        if re.fullmatch(r'(?:the )?' + math + r'th cohomology group of ' + math
                        + r' (?:on|over) ' + math, text):
            return ['cohomology group']
        if re.fullmatch(r'(?:the )?' + math + r'th higher direct image of ' + math, text):
            return ['higher direct image']
        if re.fullmatch(r'morphism of pseudo ' + math + r'-torsors', text):
            return ['morphism', 'pseudo', 'torsors']
    # The caron and its group stay opaque in the source projection. Only this
    # verified proper name prefix may precede these two named lexical cores.
    accent = re.fullmatch(r'<(GROUPOPEN_([0-9]{4}))><(ACCENT_[0-9]{4})>'
                          r'<(GROUPCLOSE_\2)>ech (complex|cohomology groups)', text)
    if accent and [unit['placeholders'].get(accent[i]) for i in (1, 3, 4)] == ['{', r'\v C', '}']:
        return [accent[5]]
    zeroth = re.fullmatch(r'zeroth <(GROUPOPEN_([0-9]{4}))><(ACCENT_[0-9]{4})>'
                         r'<(GROUPCLOSE_\2)>ech cohomology group', text)
    if zeroth and [unit['placeholders'].get(zeroth[i]) for i in (1, 3, 4)] == ['{', r'\v C', '}']:
        return ['zeroth', 'cohomology group']
    return None


def source_projection(unit: dict[str, Any]) -> tuple[str, list[str]]:
    """Expose prose through formatting wrappers without reading protected math."""
    source = unit["source_text"]
    pieces: list[str] = []
    declarations: list[str] = []
    qualified = [slot for region in unit.get('math_text_regions', []) for slot in region['slots']
                 if slot['classification_witness']['usage'] in
                    {'numeric-isomorphism-suffix', 'matrix-numeric-category-prefix'}]
    if qualified:
        from .math_text import validate_regions
        errors = validate_regions(unit)
        if errors:
            raise RecordError('qualified math terminology requires complete typed source: ' + '\n'.join(errors))
        for slot in qualified:
            left, right = ('<' + name + '>' for name in slot['boundary_placeholders'])
            original = left + slot['source'] + right
            if source.count(original) != 1:
                raise RecordError('qualified math terminology has no unique complete source slot')
            # The numeral stays in its locked math piece. Only the terminology
            # projection exposes the validated complete lexical qualification.
            source = source.replace(original, left + '2' + slot['source'] + right, 1)
            declarations.append('2' + slot['source'].split()[0])
    opened: dict[tuple[str, str], tuple[int, str]] = {}
    cursor = 0
    for match in PLACEHOLDER_TOKEN_RE.finditer(source):
        pieces.append(source[cursor:match.start()])
        name, number = match.group(1).rsplit("_", 1)
        if name.endswith("OPEN") or name.endswith("CLOSE"):
            base = name.removesuffix("OPEN").removesuffix("CLOSE")
            if base in {"TEXTIT", "EMPH"}:
                key = (base, number)
                if name.endswith("OPEN") and is_font_wrapper(match.group(0), unit["placeholders"]):
                    prefix = "".join(pieces)
                    opened[key] = (len(prefix), prefix)
                elif name.endswith("CLOSE") and key in opened and is_font_wrapper(match.group(0), unit["placeholders"]):
                    start, prefix = opened.pop(key)
                    body = "".join(pieces)[start:]
                    # A complete restored paragraph can contain several
                    # sentences. A later "is defined" must not retroactively
                    # turn an earlier editorial emphasis into a named concept.
                    # Structural item/paragraph and footnote boundaries also
                    # prevent a following bibliographic description from
                    # declaring the preceding italic paper title as a term.
                    boundary = r"[.!?;]|<(?:STRUCT|FOOTNOTEOPEN|FOOTNOTECLOSE)_[0-9]{4}>"
                    before = re.split(boundary, prefix)[-1]
                    after = re.split(boundary, source[match.end():])[0]
                    introduced = (unit.get("node_kind") == "definition"
                                  or bool(re.search(r"\b(?:call|calls|called|calling|say|says|said|define|defines|defined|defining)\b",
                                                    before + " " + after, re.IGNORECASE)))
                    # An italic imperative with mathematical arguments quotes
                    # wording to use, rather than naming a lexical concept.
                    # Its prose remains visible to the ordinary catalog scan.
                    visible_body = term_display_text(body, unit["placeholders"], unit=unit)
                    usage_clause = (re.match(r"^(?:let|assume|suppose)\b", _space(visible_body), re.IGNORECASE)
                                    and PLACEHOLDER_TOKEN_RE.search(visible_body))
                    qualified_parts = (_qualified_declaration_parts(visible_body, unit)
                                       if introduced and not usage_clause else None)
                    if qualified_parts is not None:
                        declarations.extend(qualified_parts)
                    # Math-qualified declarations still expose their prose parts.
                    for phrase in ([] if usage_clause or not introduced or qualified_parts is not None
                                   else PLACEHOLDER_TOKEN_RE.split(visible_body)[::2]):
                        phrase = _space(phrase).strip(" -.,:;`'\"()")
                        if PLACEHOLDER_TOKEN_RE.search(visible_body):
                            # A formula can leave a connector as a whole prose
                            # part, with no lexical concept before it.
                            phrase = re.sub(r"(?:^|\s+)(?:of|over|in|between|with|to|on|from)$", "", phrase, flags=re.IGNORECASE)
                        if phrase and re.search(r"[A-Za-z]", phrase):
                            declarations.append(phrase)
            if not is_font_wrapper(match.group(0), unit["placeholders"]):
                # Footnotes and other semantic wrappers are boundaries; their
                # prose is scanned, but phrases cannot bridge those boundaries.
                pieces.append(match.group(0))
        else:
            pieces.append(match.group(0))
        cursor = match.end()
    pieces.append(source[cursor:])
    text = _space(term_display_text("".join(pieces), unit["placeholders"], unit=unit))
    # Articles and trailing connectors belong to the surrounding sentence;
    # protected formulas supply qualifiers outside the exposed lexical core.
    declarations = [re.sub(r"^(?:a|an|the)\s+", "", phrase, flags=re.IGNORECASE) for phrase in declarations]
    return text, sorted(set(declarations))


@lru_cache(maxsize=8192)
def _term_pattern(phrase: str, ignore_case: bool):
    expression = r"(?<![\w])" + re.escape(_space(phrase)) + r"(?![\w])"
    return re.compile(expression, re.IGNORECASE if ignore_case else 0)


def _matches(text: str, phrase: str, *, ignore_case: bool = False):
    return list(_term_pattern(phrase, ignore_case).finditer(text))


def _literal_mailto_spans(unit: dict[str, Any], projected_text: str) -> list[tuple[int, int]]:
    """Locate exact protected address labels without changing source projection."""
    source = unit["source_text"]
    placeholders = unit["placeholders"]
    labels: dict[str, set[tuple[int, int]]] = {}
    email = (r"[A-Za-z0-9_%+-]+(?:\.[A-Za-z0-9_%+-]+)*@"
             r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
             r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+")
    for match in re.finditer(r"<TEXTOPEN_([0-9]{4})>([^<>]+)<TEXTCLOSE_\1>", source):
        number, address = match.groups()
        left, right = f"TEXTOPEN_{number}", f"TEXTCLOSE_{number}"
        if (placeholders.get(left) != "\\href{mailto:" + address + "}{"
                or placeholders.get(right) != "}"
                or not re.fullmatch(email, address, flags=re.ASCII)
                or source.count("<" + left + ">") != 1
                or source.count("<" + right + ">") != 1):
            continue
        labels.setdefault(address, set()).add(match.span(2))
    spans = []
    for address, protected in labels.items():
        original = list(re.finditer(re.escape(address), source))
        projected = list(re.finditer(re.escape(address), projected_text))
        # Projection may remove formatting or expose typed lexical qualifiers.
        # Only an unchanged ordered occurrence set gives an unambiguous map;
        # bare repetitions elsewhere cannot borrow a protected label's span.
        if len(original) != len(projected):
            continue
        spans.extend(after.span() for before, after in zip(original, projected)
                     if before.span() in protected)
    return spans


def _assignment_set(text: str, match: re.Match[str], unit: dict[str, Any] | None = None) -> bool:
    if match.group(0).casefold() != "set":
        return False
    before = text[:match.start()].rstrip()
    after = text[match.end():]
    # The two locked Topologies proofs put the parameter before the assigned
    # pullback. Keep every frame word and all three opaque math boundaries.
    if (re.search(r"\bwe$", before, re.IGNORECASE)
            and re.match(r"\s+(?i:for)\s+<MATH_[0-9]{4}>\s+(?i:the\s+pullback)\s+"
                         r"<MATH_[0-9]{4}>\s+(?i:equal\s+to)\s+<MATH_[0-9]{4}>", after)):
        return True
    if not re.match(r"\s+<MATH_[0-9]{4}>", after):
        return False
    if (re.search(r'(?:^|[.!?]\s+)namely,$', before, re.IGNORECASE)
            or re.search(r'(?:^|[.!?]\s+)in the situation of lemma <REF_[0-9]{4}>$',
                         before, re.IGNORECASE)):
        return True
    paragraph = re.search(r'<(STRUCT_[0-9]{4})>\s*<(STRUCT_[0-9]{4})>$', before)
    if (paragraph and unit is not None
            and [unit['placeholders'].get(paragraph[i]) for i in (1, 2)] == [r'\medskip', r'\noindent']):
        return True
    return (not before or before[-1] in ".!?"
            or bool(re.search(r"\b(?:us|can|could|may|must|shall|will|and)\s*$", before, re.IGNORECASE))
            or bool(re.search(r"\bwe(?:\s+(?:now|first|then|finally|similarly))*\s*$", before, re.IGNORECASE))
            or bool(re.search(r"\bwe\s+can\s+now$", before, re.IGNORECASE))
            or bool(re.search(r"(?:^|[.!?]\)?\s+)(?:now,|to see \([0-9]+\) just)$", before, re.IGNORECASE))
            or bool(re.search(r"(?:^|[.!?]\s+)(?:to prove existence, just|then)$", before, re.IGNORECASE))
            or bool(re.search(r"(?:^|[.!?]\s+)(?:for (?:every|each)\b[^.!?]*|finally|similarly),$", before, re.IGNORECASE)))


def load_catalog(root: Path) -> dict[str, Any]:
    path = root / "config/source-terms.json"
    try:
        value = json.loads(_input_text(path, encoding="utf-8"))
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
    scopes = value.get("nonmathematical_chapters", [])
    if len({scope["chapter"] for scope in scopes}) != len(scopes):
        raise RecordError("duplicate nonmathematical chapter scope")
    uses = value.get("nonmathematical_occurrences", [])
    if any(use["occurrence_index"] < 0 for use in uses):
        raise RecordError("nonmathematical occurrence index must be nonnegative")
    keys = {(use["chapter"], use["source_tex_hash"], use["source_term"], use["occurrence_index"]) for use in uses}
    if len(keys) != len(uses):
        raise RecordError("duplicate nonmathematical source occurrence")
    return value


def source_inventory(unit: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    """Requirements depend only on source nodes and the explicit catalog scope."""
    if any(unit.get(key) != expected for key, expected in expected_unit_hashes(unit).items()):
        raise RecordError(f"{unit['unit_id']}: source inventory refuses stale unit hashes")
    text, declarations = source_projection(unit)
    literal_spans = _literal_mailto_spans(unit, text)
    matches = []
    nonmathematical = unit["chapter"] in {scope["chapter"] for scope in catalog.get("nonmathematical_chapters", [])}
    excluded_spans = set()
    uses = [use for use in catalog.get("nonmathematical_occurrences", [])
            if use["chapter"] == unit["chapter"] and use["unit_id"] == unit["unit_id"]]
    tex_hash = source_tex_hash(unit) if uses else None
    for use in uses:
        if use["source_tex_hash"] == tex_hash:
            occurrences = _matches(text, use["source_term"])
            if use["occurrence_index"] < 0 or use["occurrence_index"] >= len(occurrences):
                raise RecordError("nonmathematical source occurrence no longer exists")
            excluded_spans.add(occurrences[use["occurrence_index"]].span())
    for entry in ([] if nonmathematical else catalog["terms"]):
        if entry["chapters"] and unit["chapter"] not in entry["chapters"]:
            continue
        for form in entry["forms"]:
            for match in _matches(text, form, ignore_case=True):
                if (match.span() in excluded_spans or _assignment_set(text, match, unit)
                        or any(start <= match.start() and match.end() <= stop
                               for start, stop in literal_spans)):
                    continue
                matches.append((match.start(), match.end(), entry["id"], "catalog"))
    exclusions = {phrase.casefold() for phrase in catalog["nonmathematical_declarations"]}
    for declaration in ([] if nonmathematical else declarations):
        if declaration.casefold() in exclusions:
            continue
        for match in _matches(text, declaration):
            if (match.span() in excluded_spans
                    or any(start <= match.start() and match.end() <= stop
                           for start, stop in literal_spans)):
                continue
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
        literal = term_display_text(f"{chinese}（{english}）", unit["placeholders"], unit=unit)
        position = term_display_text(translation, unit["placeholders"], unit=unit).find(literal, target_cursor)
        if position < 0:
            errors.append(f"{uid}: missing or repeated bilingual display: {literal}")
        else:
            target_cursor = position + len(literal)
        valid.append((index, _space(term_display_text(english, unit["placeholders"], unit=unit))))
    # Longer phrases receive source spans first, so a later short word cannot
    # consume the source of an earlier compound. Counts and case stay exact.
    assigned: list[tuple[int, int, str]] = []
    for index, english in sorted(valid, key=lambda item: (-len(item[1]), item[0])):
        available = [match for match in _matches(source, english)
                     if not any(match.start() < stop and start < match.end() for start, stop, _ in assigned)]
        # An ordinary use may precede the same mathematical word. Allocate the
        # required source occurrence first, while allowing optional displays
        # for the remaining ordinary uses without reusing any source span.
        core = re.sub(r"^(?:a|an|the) ", "", english, flags=re.IGNORECASE)
        available.sort(key=lambda match: not any(match.start() <= item["projection_start"] and item["projection_end"] <= match.end()
                                                and core == item["source_term"] for item in inventory["occurrences"]))
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


def _ordinary_container_selector(containers, chapter: str, unit_id: str) -> dict[str, Any]:
    """Resolve only a unique canonical unit in a complete native container."""
    from .chapter_preflight import _selectors
    from .source_integrity import STATEMENTS

    if not re.fullmatch(r'[A-Za-z0-9_-]+', chapter):
        raise RecordError('ordinary evidence has an invalid chapter')
    coordinates = []
    for entry in _selectors(containers.document(chapter)[1], chapter, containers.english.tags):
        coordinate = entry['selector']
        kind, ordinal = coordinate['kind'], coordinate['ordinal']
        if kind == 'proof':
            suffix = 'proof' + (f'-{ordinal:03d}' if ordinal != 1 else '')
        elif kind in STATEMENTS:
            suffix = 'statement'
        elif kind.endswith('_title'):
            suffix = 'title'
        elif kind == 'prose_block':
            suffix = f'prose-{ordinal:04d}'
        else:
            continue
        if unit_id == f"tag:{coordinate['owner_tag']}:{suffix}":
            coordinates.append(coordinate)
    if len(coordinates) != 1:
        raise RecordError('ordinary evidence has no unique complete canonical coordinate')
    return coordinates[0]


def validate_catalog_evidence(root: Path, catalog: dict[str, Any],
                              units: list[dict[str, Any]], harvest: Path | None = None,
                              *, containers=None) -> tuple[list[dict[str, Any]], list[str]]:
    """Verify every English witness; reuse only real selections in this invocation."""
    source_commit = load_upstream_commit(root / "upstream.lock")
    if catalog["source_commit"] != source_commit:
        raise RecordError("source term catalog uses a different locked source commit")
    # Evidence is English source, never a candidate's term metadata.
    errors = []
    by_tex = {}
    for row in units:
        by_tex.setdefault((row["chapter"], source_tex_hash(row)), []).append(row)
    selections = {}
    locked_evidence = []
    for entry in catalog["terms"]:
        for evidence in entry["evidence"]:
            if evidence.get("kind") == "locked-source-container":
                check = {"concept": entry["id"], **evidence, "status": "FAIL"}
                try:
                    if (evidence["source_commit"] != source_commit
                            or evidence["selector"]["file"] != evidence["chapter"] + ".tex"):
                        raise RecordError("catalog evidence commit/chapter differs from locked source")
                    if evidence["source_term"].casefold() not in {form.casefold() for form in entry["forms"]}:
                        raise RecordError("catalog evidence word is not a declared form")
                    if containers is None:
                        from .source_containers import Containers
                        containers = Containers(root, harvest)
                    key = json.dumps(evidence["selector"], sort_keys=True)
                    if key not in selections:
                        selections[key] = containers.select(evidence["selector"])
                    selected = selections[key]
                    if evidence["fragment_hash"] != selected["location"]["fragment_hash"]:
                        raise RecordError("catalog evidence full locked-Git fragment hash differs")
                    if not _matches(source_projection(selected["inventory_unit"])[0], evidence["source_term"]):
                        raise RecordError("catalog evidence word is absent from exposed locked-Git prose")
                    check.update(status="PASS", blob_oid=selected["blob_oid"],
                                 blob_hash=selected["blob_hash"], location=selected["location"])
                except (RecordError, OSError) as exc:
                    check["error"] = str(exc)
                    errors.append(f"{entry['id']}: locked catalog evidence: {exc}")
                locked_evidence.append(check)
                continue
            rows = by_tex.get((evidence["chapter"], evidence["source_tex_hash"]), [])
            if (not any(_matches(source_projection(row)[0], evidence["source_term"]) for row in rows)
                    or evidence["source_term"].casefold() not in {form.casefold() for form in entry["forms"]}):
                errors.append(f"{entry['id']}: catalog evidence is absent from current English source")
    for scope in catalog.get("nonmathematical_chapters", []):
        evidence = scope["title_evidence"]
        rows = by_tex.get((scope["chapter"], evidence["source_tex_hash"]), [])
        if not any(row["node_kind"] == "chapter_title" and source_projection(row)[0] == evidence["source_title"] for row in rows):
            errors.append(f"{scope['chapter']}: nonmathematical chapter lacks its locked English title evidence")
    for use in catalog.get("nonmathematical_occurrences", []):
        current = [row for row in units if row['chapter'] == use['chapter'] and row['unit_id'] == use['unit_id']]
        check = {"kind": "locked-nonmathematical-occurrence", **use, "status": "FAIL"}
        try:
            index = use['occurrence_index']
            if not isinstance(index, int) or isinstance(index, bool) or index < 0:
                raise RecordError('ordinary evidence occurrence index must be nonnegative')
            if current:
                if len(current) != 1:
                    raise RecordError('ordinary evidence current unit is not unique')
                row = current[0]
            else:
                from .source_containers import Containers, lower_container
                if containers is None:
                    containers = Containers(root, harvest)
                if containers.english.commit != source_commit:
                    raise RecordError('ordinary evidence containers use a different locked commit')
                coordinate = _ordinary_container_selector(containers, use['chapter'], use['unit_id'])
                key = json.dumps(coordinate, sort_keys=True)
                if key not in selections:
                    selections[key] = containers.select(coordinate)
                selected = selections[key]
                rows = lower_container(selected, containers.policy)
                if len(rows) != 1 or rows[0]['unit_id'] != use['unit_id']:
                    raise RecordError('ordinary evidence lacks its complete canonical unit')
                row = rows[0]
                check.update(selector=coordinate, blob_oid=selected['blob_oid'],
                             blob_hash=selected['blob_hash'], location=selected['location'])
            if row['source_commit'] != source_commit or source_tex_hash(row) != use['source_tex_hash']:
                raise RecordError('ordinary evidence source commit or complete TeX hash differs')
            if len(_matches(source_projection(row)[0], use['source_term'])) <= index:
                raise RecordError('ordinary evidence word/index is absent from exposed source prose')
            check.update(status='PASS', path='current-unit' if current else 'locked-source-container')
        except (RecordError, OSError) as exc:
            check['error'] = str(exc)
            errors.append(f"{use['chapter']}: nonmathematical occurrence lacks its locked English source evidence: {exc}")
        locked_evidence.append(check)
    if containers is not None:
        containers.assert_unchanged()
    return locked_evidence, errors


def audit_repository_terms(root: Path, harvest: Path | None = None) -> tuple[dict[str, Any], list[str]]:
    catalog = load_catalog(root)
    approved = load_approved_term_pairs(root / "config/glossary.yml")
    source_commit = load_upstream_commit(root / "upstream.lock")
    if catalog["source_commit"] != source_commit:
        raise RecordError("source term catalog uses a different locked source commit")
    units = {}
    batches = {}
    for path in sorted(_input_glob(root / "translation-data/units", "*.jsonl")):
        rows = load_jsonl(path)
        for row in rows:
            if row["unit_id"] in units:
                raise RecordError(f"duplicate active source unit: {row['unit_id']}")
            if row["source_commit"] != source_commit:
                raise RecordError(f"different source commit: {row['unit_id']}")
            units[row["unit_id"]] = row
        batches[path.stem] = rows
    locked_evidence, errors = validate_catalog_evidence(root, catalog, list(units.values()), harvest)
    report = {"schema_version": 1, "source_commit": source_commit,
              "catalog_hash": sha256_value(catalog), "unit_count": len(units),
              "batch_count": len(batches), "required_occurrences": 0, "units": [], "candidates": [],
              "locked_catalog_evidence": locked_evidence}
    for row in units.values():
        inventory = source_inventory(row, catalog)
        report["units"].append(inventory)
        report["required_occurrences"] += len(inventory["occurrences"])
    for path in sorted(_input_glob(root / "translation-data/candidates", "*/*.jsonl")):
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
    candidate_stems = {path.stem for path in _input_glob(root / "translation-data/candidates", "*/*.jsonl")}
    for stem in sorted(set(batches) - candidate_stems):
        errors.append(f"{stem}: source batch has no candidate coverage")
    return report, errors
