"""Finite category, operator and prose roles witnessed in cotangent.tex."""

from functools import lru_cache


USAGE = 'cotangent-source-frames'
NOTATION_USAGE = 'cotangent-symbol-frame'
NOTATION_COMMANDS = {'Alg': 'textit', '-Alg': 'textit', 'Tor': 'text', 'Sym': 'text'}
CONTEXTS = {
    USAGE: {
        ('descent-sheaf-set-matrices', ' on '),
        ('etale-scheme-diagrams', ' finite'),
        ('deformations-source-frames', 'resp.'),
    },
}
NATURAL_LITERALS = {' on ', ' finite', 'resp.', 'sections over '}


@lru_cache(maxsize=None)
def _natural_frames():
    from .math_text import nodes
    contracts = []
    for frame in NATURAL_FRAMES:
        expected = nodes(frame)
        fields = tuple(i for i, part in enumerate(expected)
                       if part.get('command') == 'text' and part['value'] in NATURAL_LITERALS)
        contracts.append((len(expected), fields, _protected_pieces(frame, expected, fields)))
    return tuple(contracts)


def usage(source, stream, index, kind):
    """Bind the complete math frame, allowing only its pure-text leaves to vary."""
    from .math_text import plain_text

    if kind != USAGE or not 0 < index < len(stream) - 1:
        return None
    node = stream[index]
    if node.get('command') != 'text' or not plain_text(node['value']):
        return None
    for node_count, fields, protected in _natural_frames():
        if len(stream) != node_count or index not in fields:
            continue
        if (all(stream[i].get('command') == 'text' and plain_text(stream[i]['value']) for i in fields)
                and _protected_pieces(source, stream, fields) == protected):
            return {'before': source[stream[index - 1]['start']:node['start']],
                    'after': source[node['end']:stream[index + 1]['end']],
                    'environments': node['environments']}
    return None


def _protected_pieces(source, stream, fields):
    start = 0
    pieces = []
    for i in fields:
        part = stream[i]
        pieces.append(source[start:part['parameter_start']])
        start = part['parameter_end']
    return (*pieces, source[start:])


def notation_context(source, stream, index, value, kind):
    """Classify only the witnessed operator, including its original command."""
    if kind != NOTATION_USAGE or source not in NOTATION_FRAMES.get(value, ()):
        return None
    part = stream[index]
    if part.get('command') == NOTATION_COMMANDS[value] and part.get('value') == value:
        return source[:part['start']] + source[part['end']:]
    return None


NATURAL_FRAMES = (
    (
        '$$\n'
        '\\begin{matrix}\n'
        '\\Omega_1 = \\Omega_{\\mathcal{O}/A} \\otimes_\\mathcal{O} \\underline{B}\n'
        '\\text{ on }\\mathcal{C}_{B/A} \\\\\n'
        '\\Omega_2 = \\Omega_{\\mathcal{O}/A} \\otimes_\\mathcal{O} \\underline{C}\n'
        '\\text{ on }\\mathcal{C}_{C/A} \\\\\n'
        '\\Omega_3 = \\Omega_{\\mathcal{O}/B} \\otimes_\\mathcal{O} \\underline{C}\n'
        '\\text{ on }\\mathcal{C}_{C/B}\n'
        '\\end{matrix}\n'
        '$$'
    ),
    (
        '$$\n'
        'R[E] =\n'
        '\\colim_{\\Sigma \\subset \\text{Map}(E, \\mathbf{Z}_{\\geq 0})\\text{ finite}}\n'
        '\\prod\\nolimits_{I \\in \\Sigma} R\n'
        '$$'
    ),
    (
        '$$\n'
        'L_{B^h/A^h} = L_{B^h/A} = L_{B/A} \\otimes_B^\\mathbf{L} B^h\n'
        '\\quad\\text{resp.}\\quad\n'
        'L_{B^{sh}/A^{sh}} = L_{B^{sh}/A} = L_{B/A} \\otimes_B^\\mathbf{L} B^{sh}\n'
        '$$'
    ),
    (
        '$$\n'
        '\\xymatrix{\n'
        '\\mathcal{A}\\textit{-Alg} \\ar[d]_{\\text{sections over }U} \\ar[r] &\n'
        '\\Sh(\\mathcal{C}) \\ar@<1ex>[l] \\ar[d]^{\\text{sections over }U} \\\\\n'
        '\\mathcal{A}(U)\\textit{-Alg} \\ar[r] & \\textit{Sets} \\ar@<1ex>[l]\n'
        '}\n'
        '$$'
    ),
)

NOTATION_FRAMES = {
    'Alg': {
        '$\\textit{Alg}_A$',
        '$V : \\textit{Alg}_A \\to \\textit{Sets}$',
        '$U : \\textit{Sets} \\to \\textit{Alg}_A$',
        '$\\text{Fun}(\\textit{Alg}_A, \\textit{Alg}_A)$',
        (
            '$$\n'
            '\\xymatrix{\n'
            '\\mathcal{A} \\ar[d] \\ar[r] & \\mathcal{S} \\ar@<1ex>[l] \\ar[d] \\\\\n'
            '\\textit{Alg}_A \\ar[r] & \\textit{Sets} \\ar@<1ex>[l]\n'
            '}\n'
            '$$'
        ),
    },
    '-Alg': {
        '$V : A\\textit{-Alg} \\to \\textit{Sets}$',
        '$U : \\textit{Sets} \\to A\\textit{-Alg}$',
        '$\\mathcal{A}\\textit{-Alg}$',
        '$V : \\mathcal{A}\\textit{-Alg} \\to \\Sh(\\mathcal{C})$',
        '$U : \\Sh(\\mathcal{C}) \\to \\mathcal{A}\\textit{-Alg}$',
        '$\\text{Fun}(\\mathcal{A}\\textit{-Alg}, \\mathcal{A}\\textit{-Alg})$',
        (
            '$$\n'
            '\\xymatrix{\n'
            '\\mathcal{A}\\textit{-Alg} \\ar[d]_{f^{-1}} \\ar[r] &\n'
            '\\Sh(\\mathcal{C}) \\ar@<1ex>[l] \\ar[d]^{f^{-1}} \\\\\n'
            'f^{-1}\\mathcal{A}\\textit{-Alg} \\ar[r] & \\Sh(\\mathcal{D}) \\ar@<1ex>[l]\n'
            '}\n'
            '$$'
        ),
        (
            '$$\n'
            '\\xymatrix{\n'
            '\\mathcal{A}\\textit{-Alg} \\ar[d]_{\\text{sections over }U} \\ar[r] &\n'
            '\\Sh(\\mathcal{C}) \\ar@<1ex>[l] \\ar[d]^{\\text{sections over }U} \\\\\n'
            '\\mathcal{A}(U)\\textit{-Alg} \\ar[r] & \\textit{Sets} \\ar@<1ex>[l]\n'
            '}\n'
            '$$'
        ),
    },
    'Tor': {
        '$\\text{Tor}_*^C(B, B)$',
    },
    'Sym': {
        '$H_l(\\mathcal{C}, \\text{Sym}_{\\underline{B}}^k(\\mathcal{F})) = 0$',
        (
            '$$\n'
            '\\ldots \\to\n'
            '\\wedge^2\\mathcal{F} \\otimes \\text{Sym}^{k - 2}\\mathcal{F} \\to\n'
            '\\mathcal{F} \\otimes \\text{Sym}^{k - 1}\\mathcal{F} \\to\n'
            '\\text{Sym}^k\\mathcal{F} \\to 0\n'
            '$$'
        ),
        '$\\text{Sym}^k\\mathcal{F}$',
        (
            '$$\n'
            'E_1^{p, q} =\n'
            'H_p(\\mathcal{C},\n'
            '\\wedge^{q + 1}\\mathcal{F} \\otimes \\text{Sym}^{k - q - 1}\\mathcal{F})\n'
            '\\Rightarrow\n'
            'H_{p + q}(\\mathcal{C}, \\text{Sym}^k(\\mathcal{F}))\n'
            '$$'
        ),
        (
            '$$\n'
            'L\\pi_!(\\wedge^{q + 1}\\mathcal{F} \\otimes \\text{Sym}^{k - q - 1}\\mathcal{F}) =\n'
            'L\\pi_!(\\wedge^{q + 1}\\mathcal{F}) \\otimes_B^\\mathbf{L}\n'
            'L\\pi_!(\\text{Sym}^{k - q - 1}\\mathcal{F}))\n'
            '$$'
        ),
        (
            '$H_k(\\mathcal{C}, \\text{Sym}^k(\\mathcal{F})) =\n'
            '\\wedge^k_B(H_1(\\mathcal{C}, \\mathcal{F}))$'
        ),
        '$H_k(\\mathcal{C}, \\text{Sym}^k(\\mathcal{F}))$',
        (
            '$$\n'
            'E_1^{p, q} =\n'
            'H_{- p - q}(\\mathcal{C}_{B/A}, \\text{Sym}^p_{\\underline{B}}(\\Omega))\n'
            '\\Rightarrow \\text{Tor}^A_{- p - q}(B, B)\n'
            '$$'
        ),
        '$H_i(\\mathcal{C}_{B/A}, \\text{Sym}^k_{\\underline{B}}(\\Omega)) = 0$',
        '$\\text{Sym}_B^k(\\Omega) = \\mathcal{K}^k/\\mathcal{K}^{k + 1}$',
        (
            '$$\n'
            'H_i(\\mathcal{C}_{B/A}, \\mathcal{K}^k/\\mathcal{K}^{k + 1}) =\n'
            'H_i(\\mathcal{C}_{B/A}, \\text{Sym}^k_{\\underline{B}}(\\Omega)) = 0\n'
            '$$'
        ),
        '$H_k(\\mathcal{C}_{B/A}, \\text{Sym}^k(\\Omega)) = \\wedge^k_B(I/I^2)$',
        (
            '$$\n'
            '\\begin{matrix}\n'
            'B \\\\\n'
            '0 \\\\\n'
            '0 & I/I^2 \\\\\n'
            '0 & H^{-2}(L_{B/A}) \\\\\n'
            '0 & H^{-3}(L_{B/A}) & \\wedge^2(I/I^2) \\\\\n'
            '0 & H^{-4}(L_{B/A}) & H_3(\\mathcal{C}_{B/A}, \\text{Sym}^2(\\Omega)) \\\\\n'
            '0 & H^{-5}(L_{B/A}) & H_4(\\mathcal{C}_{B/A}, \\text{Sym}^2(\\Omega)) &\n'
            '\\wedge^3(I/I^2)\n'
            '\\end{matrix}\n'
            '$$'
        ),
    },
}
