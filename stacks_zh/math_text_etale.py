"""Opt-in leaves in complete etale frames; no policy or translation adoption.

The literal frames are locked-English syntax witnesses. All non-text tokens,
their depth, environment and intervening bytes must remain exact. Registry
entries and their independent Git witnesses authorize each exposed parameter.
"""
from __future__ import annotations

from functools import lru_cache

USAGES = {'etale-unramified-condition', 'etale-sections-correspondence',
          'etale-scheme-diagrams'}
COMPONENT_USAGE = 'etale-scheme-component'
SEPARATOR = r"\'e"
COMPONENT_LITERALS = (
    r" \'etale over ",
    r"separated, \'etale over ",
    r" quasi-compact, separated, \'etale over ",
)
CONTEXTS = {
    'etale-sections-correspondence': {('root-phrase', ' is an isomorphism'),
        ('descent-sheaf-set-matrices', ' such that')},
    'etale-scheme-diagrams': {('descent-sheaf-set-matrices', 'descent data '),
                              ('descent-data-matrices', ' relative to ')},
}

UNRAMIFIED = r"""$$
R \to S\text{ is unramified at }\mathfrak q
\Leftrightarrow
\mathfrak pS_{\mathfrak q} = \mathfrak q S_{\mathfrak q}
\text{ and }
\kappa(\mathfrak p) \subset \kappa(\mathfrak q)\text{ finite separable}
$$"""
SECTIONS = r"""$$
\text{sections of }f
\leftrightarrow
\left\{
\begin{matrix}
\text{connected components }X'\text{ of }X\text{ such that}\\
\text{the induced map }X' \to Y\text{ is an isomorphism}
\end{matrix}
\right\}
$$"""
THICKENING = r"""$$
\{
\text{schemes }X\text{ \'etale over }S
\}
\leftrightarrow
\{
\text{schemes }X_0\text{ \'etale over }S_0
\}
$$"""
DESCENT = r"""\begin{equation}
\label{equation-descent-etale}
\text{schemes }U\text{ \'etale over }S \longrightarrow
\begin{matrix}
\text{descent data }(V, \varphi)\text{ relative to }X/S \\
\text{ with }V\text{ \'etale over }X
\end{matrix}
\end{equation}"""
EFFECTIVE = r"""$$
\begin{matrix}
\text{schemes quasi-compact,}\\
\text{separated, \'etale over }S
\end{matrix}
\longrightarrow
\begin{matrix}
\text{descent data }(V, \varphi)\text{ relative to }X/S\text{ with}\\
V\text{ quasi-compact, separated, \'etale over }X
\end{matrix}
$$"""
SCHEME_FRAMES = (THICKENING, DESCENT, EFFECTIVE)


def component_contract(literal):
    return dict(literal=literal if literal in COMPONENT_LITERALS else None,
        usage=COMPONENT_USAGE, components=literal.split(SEPARATOR)
        if literal in COMPONENT_LITERALS else [], separator=SEPARATOR)


def literal_exception(literal, role):
    return role == 'etale-scheme-diagrams' and literal == 'schemes quasi-compact,'


def source_leaf(slot):
    """Only the one original ASCII-space prefix of the exact accented word.

    Full parent span, complete-frame role and ordered coverage are independently
    checked by _slot_node/validate_regions. This never permits an empty target.
    """
    c = slot.get('parameter_components', {})
    return (slot.get('source') == ' '
        and slot.get('classification_witness', {}).get('usage') == COMPONENT_USAGE
        and c.get('parameter_source') == COMPONENT_LITERALS[0]
        and c.get('component_index') == 1 and c.get('component_count') == 2
        and c.get('separator') == SEPARATOR)


def component_values(value):
    from .math_text import plain_text
    leaves = value.split(SEPARATOR)
    return (len(leaves) == 2 and plain_text(leaves[1])
        and (plain_text(leaves[0]) or value == COMPONENT_LITERALS[0]))


@lru_cache(maxsize=None)
def _frame_nodes(frame):
    from .math_text import nodes
    return nodes(frame)


def _matches(source, stream, frame):
    from .math_text import plain_text
    expected = _frame_nodes(frame)
    if len(stream) != len(expected):
        return False
    previous = boundary = 0
    for actual, target in zip(stream, expected):
        if (actual['depth'] != target['depth']
                or actual['environments'] != target['environments']
                or source[previous:actual['start']] != frame[boundary:target['start']]):
            return False
        if target.get('command') == 'text':
            if actual.get('command') != 'text':
                return False
            value = actual['value']
            if not (component_values(value) if target['value'] in COMPONENT_LITERALS
                    else plain_text(value)):
                return False
            if (source[actual['start']:actual['parameter_start']]
                    != frame[target['start']:target['parameter_start']]
                    or source[actual['parameter_end']:actual['end']]
                    != frame[target['parameter_end']:target['end']]):
                return False
        elif actual['token'] != target['token']:
            return False
        previous, boundary = actual['end'], target['end']
    return source[previous:] == frame[boundary:]


def usage(source, stream, index, kind):
    frames = ((UNRAMIFIED,) if kind == 'etale-unramified-condition'
              else (SECTIONS,) if kind == 'etale-sections-correspondence'
              else SCHEME_FRAMES if kind in {'etale-scheme-diagrams', COMPONENT_USAGE}
              else ())
    if not 0 < index < len(stream)-1:
        return None
    for frame in frames:
        expected = _frame_nodes(frame)
        if not _matches(source, stream, frame):
            continue
        target = expected[index]
        if (target.get('command') != 'text'
                or (target['value'] in COMPONENT_LITERALS) != (kind == COMPONENT_USAGE)
                or kind == 'etale-unramified-condition' and target['value'] != ' finite separable'):
            continue
        node = stream[index]
        return {'before': source[stream[index-1]['start']:node['start']],
                'after': source[node['end']:stream[index+1]['end']],
                'environments': node['environments']}
    return None


def term_projection(unit, text):
    components = [s for r in unit.get('math_text_regions', []) for s in r['slots']
        if s.get('classification_witness', {}).get('usage') == COMPONENT_USAGE]
    if not components:
        return text
    from .math_text import validate_regions
    from .records import RecordError
    errors = validate_regions(unit)
    if errors:
        raise RecordError('etale accent projection requires complete typed source: ' + '\n'.join(errors))
    for slot in components:
        if slot['parameter_components']['component_index'] != 1:
            continue
        name = slot['boundary_placeholders'][1]
        if unit['placeholders'][name] != SEPARATOR:
            raise RecordError('etale accent projection lacks its original protected separator')
        text = text.replace('<'+name+'>', 'é')
    return text
