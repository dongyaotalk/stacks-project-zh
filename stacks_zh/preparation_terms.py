"""Read-only original declaration inventories for unadopted preparations."""
from __future__ import annotations

import ast
import hashlib
import inspect
import re
import subprocess
from types import FunctionType
from typing import Any

from . import source_terms
from .derivations import _git_origin_bytes
from .source_containers import safe_path

KNOWN_QUALIFIED_SHA256 = '46d7c3d8a2d0186a84af33365e22d0160394465a70e0a3ea498215f1157f1d80'
UNCHANGED_READERS = ('source_projection', 'source_inventory', '_space',
                     'source_tex_hash', '_matches', '_term_pattern',
                     '_literal_mailto_spans', '_assignment_set')
_space = source_terms._space
PLACEHOLDER_TOKEN_RE = source_terms.PLACEHOLDER_TOKEN_RE


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


def _functions(text):
    nodes = [node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)]
    if len({node.name for node in nodes}) != len(nodes):
        return {}
    return {node.name: ast.get_source_segment(text, node) for node in nodes}


def original_inventory(root, frozen, units, catalog, observed, snapshot):
    """Return a binding only for a complete known original preparation inventory.

    The caller validates historical scope/policy before this comparison and
    continues its runtime, raw, native source and context gates afterwards.
    This never serves assembly, current candidates or adopted history.
    """
    aid, run_id = frozen['adoption_id'], frozen['run_id']
    if (frozen['tool_version'] not in {'source-adoption-input-v1', 'source-adoption-input-v4'}
            or 'prior_adoptions' in frozen or 'shared_run_histories' in frozen
            or any(batch['prior_attempts'] for batch in frozen['batches'])
            or (root / f'translation-data/source-adoptions/{aid}.json').exists()
            or (root / f'translation-data/runs/{run_id}.json').exists()):
        return None
    for batch in frozen['batches']:
        path = safe_path(root, batch['candidates_path'],
                         r'translation-data/candidates/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.jsonl')
        if path.exists() and any(row.get('run_id') == run_id
                                 or row.get('source_adoption_id') == aid
                                 for row in snapshot.jsonl(path)):
            return None
    accepted = any(all(subprocess.run(
        ['git', '-C', str(root), 'merge-base', '--is-ancestor', left, right],
        capture_output=True).returncode == 0
        for left, right in ((frozen['origin_commit'], anchor), (anchor, 'HEAD')))
        for anchor in ('refs/remotes/origin/main', 'refs/heads/main'))
    if not accepted:
        return None
    original = _functions(_git_origin_bytes(
        root, frozen['origin_commit'], 'stacks_zh/source_terms.py').decode('utf-8'))
    helper = original.get('_qualified_declaration_parts', '')
    if hashlib.sha256(helper.encode()).hexdigest() != KNOWN_QUALIFIED_SHA256:
        return None
    current = _functions(inspect.getsource(source_terms))
    if any(not original.get(name) or original[name] != current.get(name)
           for name in UNCHANGED_READERS):
        return None
    # Execute only the static reviewed helper above and the loaded current
    # readers whose source bytes just matched. Never execute old Git code.
    namespace = dict(source_terms.source_inventory.__globals__)
    namespace['_qualified_declaration_parts'] = FunctionType(
        _qualified_declaration_parts.__code__, namespace)
    for name in ('source_projection', 'source_inventory'):
        namespace[name] = FunctionType(getattr(source_terms, name).__code__, namespace)
    complete = [namespace['source_inventory'](unit, catalog) for unit in units]
    if complete != observed:
        return None
    return dict(disposition='original-preparation-term-inventory',
                origin_commit=frozen['origin_commit'],
                qualified_declaration_sha256=KNOWN_QUALIFIED_SHA256,
                unchanged_readers=list(UNCHANGED_READERS),
                generation_validation='not_claimed')
