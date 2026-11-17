"""Finite internal-reference parameters: no policy registration or data adoption.

Only two pure natural leaves vary. Reference command, key, parentheses and all
other frame bytes remain opaque. Public pipeline wiring is a later dependency
step in the same declared task; this module alone grants no extraction permission.
"""
from functools import lru_cache

REFERENCE_USAGE = 'deformations-extension-reference'
PLAIN_USAGE = 'deformations-reference-frame-text'
USAGES = {REFERENCE_USAGE, PLAIN_USAGE}
PRIMARY_LITERALS = {'isomorphism classes of extensions'}
CONTEXTS = {PLAIN_USAGE: {('root-phrase', ' and ')}}
REFERENCES = {
    key: '(\\ref{' + key + '})'
    for key in ('equation-extension', 'equation-extension-ringed-topoi')
}
PREFIX = ' as in '
SUFFIX = ' with '


def literal_contract(literal):
    for label, separator in REFERENCES.items():
        if literal == PREFIX + separator + SUFFIX:
            return dict(prefix=PREFIX, separator=separator, suffix=SUFFIX,
                        reference_source=separator[1:-1], reference_command='ref',
                        reference_label=label)
    return None


def split_parameter(value, separator=None):
    from .math_text import plain_text
    if not isinstance(value, str):
        return None
    choices = [separator] if separator in REFERENCES.values() else REFERENCES.values() if separator is None else []
    found = []
    for token in choices:
        if value.count(token) != 1:
            continue
        prefix, suffix = value.split(token)
        if plain_text(prefix) and plain_text(suffix):
            found.append((prefix, token, suffix))
    return found[0] if len(found) == 1 else None


@lru_cache(maxsize=None)
def _frame_nodes(frame):
    from .math_text import nodes
    return nodes(frame)


def matches(source, stream, frame):
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
            contract = literal_contract(target['value'])
            valid = (split_parameter(actual.get('value'), contract['separator']) is not None
                     if contract else plain_text(actual.get('value')))
            if (actual.get('command') != 'text' or not valid
                    or source[actual['start']:actual['parameter_start']]
                    != frame[target['start']:target['parameter_start']]
                    or source[actual['parameter_end']:actual['end']]
                    != frame[target['parameter_end']:target['end']]):
                return False
        elif actual['token'] != target['token']:
            return False
        previous, boundary = actual['end'], target['end']
    return source[previous:] == frame[boundary:]


def usage(source, stream, index, kind):
    if kind not in USAGES or not 0 < index < len(stream)-1:
        return None
    for frame in FRAMES:
        if not matches(source, stream, frame):
            continue
        target = _frame_nodes(frame)[index]
        reference = literal_contract(target.get('value')) is not None
        if (target.get('command') != 'text'
                or (kind == REFERENCE_USAGE) != reference):
            continue
        node = stream[index]
        return dict(before=source[stream[index-1]['start']:node['start']],
                    after=source[node['end']:stream[index+1]['end']],
                    environments=node['environments'])
    return None


def reference_leaves(source, node):
    """Return independently delimited leaves and immutable UTF-8 reference data."""
    contract = literal_contract(node.get('value'))
    if (contract is None or node.get('command') != 'text'
            or node not in _frame_nodes(source)):
        raise ValueError('not a complete declared source reference parameter')
    start, end = node['parameter_start'], node['parameter_end']
    prefix_end = start + len(contract['prefix'])
    suffix_start = prefix_end + len(contract['separator'])
    metadata = dict(parameter_source=node['value'],
                    parameter_byte_span=dict(start=len(source[:start].encode()), end=len(source[:end].encode())),
                    reference_source=contract['reference_source'], reference_command='ref',
                    reference_label=contract['reference_label'], separator=contract['separator'],
                    separator_byte_span=dict(start=len(source[:prefix_end].encode()),end=len(source[:suffix_start].encode())),
                    reference_byte_span=dict(start=len(source[:prefix_end+1].encode()),end=len(source[:suffix_start-1].encode())),
                    leaf_count=2)
    return [dict(value=value,parameter_start=a,parameter_end=b,
                 parameter_reference_leaves=dict(**metadata,leaf_index=index))
            for index,(value,a,b) in enumerate(((contract['prefix'],start,prefix_end),
                                               (contract['suffix'],suffix_start,end)),1)]

FRAMES = (
    r"""$$
\left\{
\begin{matrix}
\text{isomorphism classes of extensions}\\
\mathcal{F}'\text{ as in (\ref{equation-extension}) with }c = c_{\mathcal{F}'}
\end{matrix}
\right\}
\longrightarrow
\Ext^1_{\mathcal{O}_X}(\mathcal{F}, \mathcal{K})
$$""",
    r"""$$
\left\{
\begin{matrix}
\mathcal{F}'_2\text{ as in (\ref{equation-extension}) with }\\
c_2 = c_{\mathcal{F}'_2}\text{ and }\mathcal{K} = \mathcal{K}_2
\end{matrix}
\right\}
\longrightarrow
\left\{
\begin{matrix}
\mathcal{F}'_1\text{ as in (\ref{equation-extension}) with }\\
c_1 = c_{\mathcal{F}'_1}\text{ and }\mathcal{K} = \mathcal{K}_1
\end{matrix}
\right\}
$$""",
    r"""$$
\xymatrix{
\{\mathcal{F}'_2\text{ as in (\ref{equation-extension}) with }
c_2 = c_{\mathcal{F}'_2}\text{ and }\mathcal{K} = \mathcal{K}_2\}
\ar[d] \ar[rr] & &
\Ext^1_{\mathcal{O}_X}(\mathcal{F}, \mathcal{K}_2) \ar[d] \\
\{\mathcal{F}'_1\text{ as in (\ref{equation-extension}) with }
c_1 = c_{\mathcal{F}'_1}\text{ and }\mathcal{K} = \mathcal{K}_1\}
\ar[rr] & &
\Ext^1_{\mathcal{O}_X}(\mathcal{F}, \mathcal{K}_1)
}
$$""",
    r"""$$
\left\{
\begin{matrix}
\text{isomorphism classes of extensions}\\
\mathcal{F}'\text{ as in (\ref{equation-extension-ringed-topoi}) with }
c = c_{\mathcal{F}'}
\end{matrix}
\right\}
\longrightarrow
\Ext^1_\mathcal{O}(\mathcal{F}, \mathcal{K})
$$""",
    r"""$$
\left\{
\begin{matrix}
\mathcal{F}'_2\text{ as in (\ref{equation-extension-ringed-topoi}) with }\\
c_2 = c_{\mathcal{F}'_2}\text{ and }\mathcal{K} = \mathcal{K}_2
\end{matrix}
\right\}
\longrightarrow
\left\{
\begin{matrix}
\mathcal{F}'_1\text{ as in (\ref{equation-extension-ringed-topoi}) with }\\
c_1 = c_{\mathcal{F}'_1}\text{ and }\mathcal{K} = \mathcal{K}_1
\end{matrix}
\right\}
$$""",
    r"""$$
\xymatrix{
\{\mathcal{F}'_2\text{ as in (\ref{equation-extension-ringed-topoi}) with }
c_2 = c_{\mathcal{F}'_2}\text{ and }\mathcal{K} = \mathcal{K}_2\}
\ar[d] \ar[rr] & &
\Ext^1_\mathcal{O}(\mathcal{F}, \mathcal{K}_2) \ar[d] \\
\{\mathcal{F}'_1\text{ as in (\ref{equation-extension-ringed-topoi}) with }
c_1 = c_{\mathcal{F}'_1}\text{ and }\mathcal{K} = \mathcal{K}_1\}
\ar[rr] & &
\Ext^1_\mathcal{O}(\mathcal{F}, \mathcal{K}_1)
}
$$"""
)
