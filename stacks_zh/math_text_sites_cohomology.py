"""Opt-in locked chapter-21 frames, with a separate protected-reference leaf.

These are syntax witnesses, not policy registration or translation facts.
Only declared text leaves can vary; every other token and gap is exact.
"""
from functools import lru_cache

USAGES = {'sites-invertible-sheaf-matrices', 'sites-naive-cup-arrow'}
REFERENCE_USAGE = 'sites-cup-remark-reference'
REFERENCE_PREFIX = 'Remark '
REFERENCE_LABEL = 'remark-cup-product'
REFERENCE = r'\ref{remark-cup-product}'
REFERENCE_LITERAL = REFERENCE_PREFIX + REFERENCE
MATRICES = r"""$$
\begin{matrix}
\text{set of invertible sheaves on }(\mathcal{C}, \mathcal{O}) \\
\text{ up to isomorphism}
\end{matrix}
\longrightarrow
\begin{matrix}
\text{set of }\mathcal{O}^*\text{-torsors} \\
\text{ up to isomorphism}
\end{matrix}
$$"""
CUP = r"""$$
\xymatrix{
f_*\mathcal{K}^\bullet
\otimes_{\mathcal{O}_\mathcal{D}}^\mathbf{L}
f_*\mathcal{M}^\bullet \ar[r] \ar[d]
&
Rf_*\mathcal{K}^\bullet
\otimes_{\mathcal{O}_\mathcal{D}}^\mathbf{L}
Rf_*\mathcal{M}^\bullet \ar[d]^{\text{Remark \ref{remark-cup-product}}} \\
\text{Tot}(
f_*\mathcal{K}^\bullet
\otimes_{\mathcal{O}_\mathcal{D}}
f_*\mathcal{M}^\bullet) \ar[d]_{\text{naive cup product}} &
Rf_*(\mathcal{K}^\bullet
\otimes_{\mathcal{O}_\mathcal{C}}^\mathbf{L}
\mathcal{M}^\bullet) \ar[d] \\
f_*\text{Tot}(\mathcal{K}^\bullet
\otimes_{\mathcal{O}_\mathcal{C}}
\mathcal{M}^\bullet) \ar[r] &
Rf_*\text{Tot}(\mathcal{K}^\bullet
\otimes_{\mathcal{O}_\mathcal{C}}
\mathcal{M}^\bullet)
}
$$"""
PAB = r"$\mathcal{F}_{U'} = j_{U'!}^{\textit{PAb}}\mathbf{Z}_{U'}$"


def reference_prefix(value):
    from .math_text import plain_text
    if isinstance(value, str) and value.endswith(REFERENCE):
        prefix = value[:-len(REFERENCE)]
        if plain_text(prefix):
            return prefix
    return None


def literal_exception(literal, role):
    return role == 'sites-invertible-sheaf-matrices' and literal == '-torsors'


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
        variable = target.get('command') == 'text' and (
            frame == MATRICES or target['value'] in {REFERENCE_LITERAL, 'naive cup product'})
        if variable:
            if actual.get('command') != 'text':
                return False
            if not (reference_prefix(actual['value']) is not None
                    if target['value'] == REFERENCE_LITERAL else plain_text(actual['value'])):
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
    frame = MATRICES if kind == 'sites-invertible-sheaf-matrices' else CUP
    if not 0 < index < len(stream)-1 or not _matches(source, stream, frame):
        return None
    target = _frame_nodes(frame)[index]
    expected = ({'set of invertible sheaves on ', 'set of ', '-torsors'}
                if kind == 'sites-invertible-sheaf-matrices' else
                {'naive cup product'} if kind == 'sites-naive-cup-arrow' else
                {REFERENCE_LITERAL} if kind == REFERENCE_USAGE else set())
    if target.get('command') != 'text' or target['value'] not in expected:
        return None
    node = stream[index]
    return dict(before=source[stream[index-1]['start']:node['start']],
                after=source[node['end']:stream[index+1]['end']],
                environments=node['environments'])


def notation_context(source, stream, index, value):
    if source != PAB or value != 'PAb' or stream[index].get('command') != 'textit':
        return None
    return source[:stream[index]['start']] + source[stream[index]['end']:]


def reference_metadata(source, node):
    start = node['parameter_start']
    end = node['parameter_end']
    return dict(parameter_source=node['value'],
        parameter_byte_span=dict(start=len(source[:start].encode()), end=len(source[:end].encode())),
        reference_source=REFERENCE, reference_command='ref', reference_label=REFERENCE_LABEL,
        reference_byte_span=dict(start=len(source[:start+len(REFERENCE_PREFIX)].encode()),
                                 end=len(source[:end].encode())))
