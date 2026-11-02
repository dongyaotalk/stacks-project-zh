"""Opt-in text roles in finite, complete descent mathematical frames.

These are syntax witnesses, not adopted source or translated text. Every
non-text token, its grouping and every inter-token gap must match the complete
frame. The registry and locked-Git witness still authorize each source literal.
"""
from __future__ import annotations

from functools import lru_cache

ETALE_LITERAL = r" finite locally free in \'etale topology"
ETALE_SEPARATOR = r"\'e"
ETALE_COMPONENTS = [' finite locally free in ', 'tale topology']
COMPONENT_USAGE = 'descent-etale-component'
USAGES = {'descent-finite-free-chain', 'descent-data-matrices',
          'descent-sheaf-set-matrices', 'descent-lemma-reference', 'descent-data-arrow'}

FINITE_FREE = r"""\begin{align*}
\mathcal{F}\text{ finite locally free in fppf topology}
& \Leftrightarrow
\mathcal{H}\text{ finite locally free on }S \\
& \Leftrightarrow
\mathcal{F}\text{ finite locally free in \'etale topology} \\
& \Leftrightarrow
\mathcal{H}\text{ finite locally free on }S \\
& \Leftrightarrow
\mathcal{F}\text{ finite locally free in Zariski topology}
\end{align*}"""

DATA_MATRICES = r"""$$
\begin{matrix}
\text{category of descent data } \\
\text{relative to the family } \{X_i \to S\}_{i \in I}
\end{matrix}
\longrightarrow
\begin{matrix}
\text{ category of descent data} \\
\text{ relative to } X/S
\end{matrix}
$$"""

DATA_ARROW = r"""$$
\text{descent data relative to }
\mathcal{V}
\longrightarrow
\text{descent data relative to }
\mathcal{U}
$$"""

SHEAF_SET_MATRICES = r"""$$
\left\{
\begin{matrix}
\text{descent data }(X_i, \varphi_{ii'})\text{ such that}\\
\text{each }X_i \in \Ob((\Sch/S)_\tau)
\end{matrix}
\right\}
\leftrightarrow
\left\{
\begin{matrix}
\text{sheaves }F\text{ on }(\Sch/S)_\tau\text{ such that}\\
\text{each }h_{S_i} \times F\text{ is representable}
\end{matrix}
\right\}.
$$"""

LEMMA_REFERENCE = r"""$$
\xymatrix{
DD(Y/S) \ar[r] & DD(X/S) \\
DD(\mathcal{V}) \ar[u]^{\text{Lemma }\ref{lemma-family-is-one}} \ar[r] &
DD(\mathcal{U}) \ar[u]_{\text{Lemma }\ref{lemma-family-is-one}}
}
$$"""

RELATIVE_PROJ = r"""$$
r_{\mathcal{L}, \psi} : X \longrightarrow \underline{\text{Proj}}_S(\mathcal{A})
$$"""

PROJECTION_FRAMES = (
    r"$\text{pr} : Y \times_Z Y \to Y$",
    r"$\text{pr}|_{\Delta(Y)} : \Delta(Y) \to Y$",
    r"$\text{pr}|_{Y'} : Y' \to Y$",
    r"$\text{pr} \circ f_Y$",
    r"""$$
\xymatrix{
X \times_Z Y \ar[d] \ar[r]_{f_Y} &
Y \times_Z Y \ar[d] \ar[r]_-{\text{pr}} &
Y \ar[d] \\
X \ar[r]^f &
Y \ar[r]^g &
Z
}
$$""",
    r"""$$
\xymatrix{
X \amalg X' \ar@{=}[d] \ar[r]_-{f \amalg f'} &
\Delta(Y) \amalg Y' \ar@{=}[d] \ar[r] &
Y \ar@{=}[d] \\
X \times_Z Y \ar[r]^{f_Y} &
Y \times_Z Y \ar[r]^-{\text{pr}} &
Y
}
$$""",
)


@lru_cache(maxsize=None)
def _frame_nodes(frame):
    from .math_text import nodes
    return nodes(frame)


def _matches(source, stream, frame, *, natural):
    from .math_text import plain_text
    expected = _frame_nodes(frame)
    if len(stream) != len(expected):
        return False
    previous_end = expected_end = 0
    for actual, target in zip(stream, expected):
        if (actual['depth'] != target['depth']
                or actual['environments'] != target['environments']
                or source[previous_end:actual['start']] != frame[expected_end:target['start']]):
            return False
        if natural and target.get('command') == 'text':
            if actual.get('command') != 'text':
                return False
            value = actual['value']
            if target['value'] == ETALE_LITERAL:
                leaves = value.split(ETALE_SEPARATOR)
                if len(leaves) != 2 or any(not plain_text(v) for v in leaves):
                    return False
            elif not plain_text(value):
                return False
            # The command and its braces remain original, including spacing.
            if (source[actual['start']:actual['parameter_start']]
                    != frame[target['start']:target['parameter_start']]
                    or source[actual['parameter_end']:actual['end']]
                    != frame[target['parameter_end']:target['end']]):
                return False
        elif actual['token'] != target['token']:
            return False
        previous_end, expected_end = actual['end'], target['end']
    return source[previous_end:] == frame[expected_end:]


def usage(source, stream, index, kind):
    frames = {'descent-finite-free-chain': FINITE_FREE,
              COMPONENT_USAGE: FINITE_FREE,
              'descent-data-matrices': DATA_MATRICES,
              'descent-data-arrow': DATA_ARROW,
              'descent-sheaf-set-matrices': SHEAF_SET_MATRICES,
              'descent-lemma-reference': LEMMA_REFERENCE}
    frame = frames.get(kind)
    if frame is None or not 0 < index < len(stream)-1:
        return None
    expected = _frame_nodes(frame)
    if (not _matches(source, stream, frame, natural=True)
            or expected[index].get('command') != 'text'
            or (expected[index]['value'] == ETALE_LITERAL) != (kind == COMPONENT_USAGE)):
        return None
    node = stream[index]
    return {'before': source[stream[index-1]['start']:node['start']],
            'after': source[node['end']:stream[index+1]['end']],
            'environments': node['environments']}


def notation_context(source, stream, index, value, kind):
    if kind == 'descent-relative-proj' and value == 'Proj':
        frames = (RELATIVE_PROJ,)
    elif kind == 'descent-projection' and value == 'pr':
        frames = PROJECTION_FRAMES
    else:
        return None
    if (not 0 <= index < len(stream) or stream[index].get('command') != 'text'
            or stream[index].get('value') != value):
        return None
    if any(_matches(source, stream, frame, natural=False) for frame in frames):
        return source[stream[index]['end']:]
    return None


def term_projection(unit, text):
    """Expose only the verified accent between the two natural text leaves.

    This is lexical QA input, never rendered/source TeX. No other MATHSEG
    payload becomes visible and no historical text projection is generalized.
    """
    components = [slot for region in unit.get('math_text_regions', [])
                  for slot in region['slots']
                  if slot.get('classification_witness', {}).get('usage') == COMPONENT_USAGE]
    if not components:
        return text
    from .math_text import validate_regions
    from .records import RecordError
    errors = validate_regions(unit)
    if errors:
        raise RecordError('accent term projection requires complete typed source: ' + '\n'.join(errors))
    for slot in components:
        if slot['parameter_components']['component_index'] != 1:
            continue
        name = slot['boundary_placeholders'][1]
        if unit['placeholders'][name] != ETALE_SEPARATOR:
            raise RecordError('accent projection lacks its exact protected accent separator')
        text = text.replace('<' + name + '>', 'é')
    return text
