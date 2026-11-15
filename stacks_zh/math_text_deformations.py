"""Opt-in plain leaves and five operators in complete locked source frames.

No production policy registration, translation or adoption occurs here. Only
plain natural parameters vary; every symbol, operand and other byte is exact.
"""
from .math_text_descent import _frame_nodes

USAGE = 'deformations-source-frames'
USAGES = {USAGE}
OPERATORS = {'Res', 'Cof', 'CofSet', 'Mod', 'Inf'}
SYMBOLS = OPERATORS | {'Aut', 'Der', 'Lift', 'id', 'Sets'}
NOTATION_USAGE = 'deformations-symbol-frame'
CONTEXTS = {USAGE: {
    ('etale-scheme-diagrams', ' finite'),
    ('root-phrase', ' is bijective'),
    ('quad-connector', 'and'),
    ('root-phrase', ' and '),
    ('root-phrase', ' lying over '),
    ('root-phrase', ' as above'),
    ('root-phrase', ' over '),
    ('root-phrase', ' for '),
}}
LITERAL_EXCEPTIONS = {'-Alg', '-dimensional algebras ', '-orbits.', 'resp.'}


def literal_exception(literal, role):
    return role == USAGE and literal in LITERAL_EXCEPTIONS


def _matches(source, stream, frame):
    """Only declared natural parameters vary, including during skeleton QA."""
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
        if target.get('command') == 'text' and target['value'] not in SYMBOLS:
            if (actual.get('command') != 'text' or not plain_text(actual['value'])
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
    if kind != USAGE or not 0 < index < len(stream) - 1:
        return None
    from .math_text import usage as ordinary_usage
    for frame in NATURAL_FRAMES:
        if not _matches(source, stream, frame):
            continue
        target = _frame_nodes(frame)[index]
        if target.get('command') != 'text' or target['value'] in SYMBOLS:
            continue
        if any(ordinary_usage(source, stream, index, role) is not None
               for role, literal in CONTEXTS[USAGE] if literal == target['value']):
            continue
        node = stream[index]
        return {'before': source[stream[index-1]['start']:node['start']],
                'after': source[node['end']:stream[index+1]['end']],
                'environments': node['environments']}
    return None


def notation_context(source, stream, index, value, kind):
    if (kind != NOTATION_USAGE or value not in OPERATORS
            or not 0 <= index < len(stream)
            or stream[index].get('command') != 'text'
            or stream[index].get('value') != value):
        return None
    for frame in NOTATION_FRAMES:
        if _matches(source, stream, frame):
            return source[:stream[index]['start']] + source[stream[index]['end']:]
    return None

NATURAL_FRAMES = ('$$\n'
 "U' \\longmapsto\n"
 "F(U') =\n"
 "\\{\\sigma : Z_{U'} \\to W_{U'}\\text{ section of }W_{U'} \\to Z_{U'}\\}\n"
 '$$',
 '\\begin{equation}\n'
 '\\label{equation-hom-functor}\n'
 '\\mathit{Mor}_B(Z, X) : (\\Sch/S)^{opp} \\longrightarrow \\textit{Sets},\n'
 '\\quad\n'
 'T \\longmapsto \\{(a, b)\\text{ as above}\\}\n'
 '\\end{equation}',
 '$$\n'
 '\\Mor_{\\Sh((\\Sch/S)_{fppf})}(T, \\mathit{Mor}_B(Z, X))\n'
 '=\n'
 '\\{(a, b)\\text{ as in }(\\ref{equation-hom})\\}\n'
 '$$',
 '$$\n'
 '\\coprod\\nolimits_{E \\subset I\\text{ finite}} F_E\n'
 '\\longrightarrow\n'
 '\\mathit{Mor}_B(Z, X)\n'
 '$$',
 '\\begin{equation}\n'
 '\\label{equation-restriction-of-scalars}\n'
 '\\text{Res}_{Z/B}(X) : (\\Sch/S)^{opp} \\longrightarrow \\textit{Sets},\n'
 '\\quad\n'
 'T \\longmapsto \\{(a, b)\\text{ as above}\\}\n'
 '\\end{equation}',
 '$$\n'
 '\\Mor_{\\Sh((\\Sch/S)_{fppf})}(T, \\text{Res}_{Z/B}(X))\n'
 '=\n'
 '\\{(a, b)\\text{ as in }(\\ref{equation-pairs})\\}\n'
 '$$',
 '$$\nX(T) = \\{\\text{free }d\\text{-dimensional algebras }m\\text{ over }R\\}\n$$',
 '\\begin{equation}\n'
 '\\label{equation-objects}\n'
 'X(T) = \\{\\text{free }d\\text{-dimensional algebras }\n'
 'm\\text{ over }\\Gamma(T, \\mathcal{O}_T)\\}\n'
 '\\end{equation}',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '           & x_2 \\ar[d] \\\\\n'
 'x_1 \\ar[r] & x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '           & A_2 \\ar[d] \\\\\n'
 'A_1 \\ar[r] & A\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r] \\ar[d] & x_2 \\ar[d] \\\\\n'
 'x_1 \\ar[r]      & x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A_1 \\times_A A_2 \\ar[r] \\ar[d] & A_2 \\ar[d] \\\\\n'
 'A_1 \\ar[r]      & A.\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r]_c \\ar[d]_a & x_\\epsilon \\ar[d]^e \\\\\n'
 'x \\ar[r]^d          & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{and}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "y' \\ar[r]_{c'} \\ar[d]_{a'} & x_\\epsilon \\ar[d]^e \\\\\n"
 'x \\ar[r]^d                 & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A \\times_k k[\\epsilon] \\ar[r] \\ar[d] & k[\\epsilon] \\ar[d] \\\\\n'
 'A  \\ar[r] & k\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '& x_V \\ar[d] \\\\\n'
 'x \\ar[r] & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '& k[V] \\ar[d] \\\\\n'
 'A \\ar[r] & k\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "y' \\ar[d] \\ar[r] & x_{V'} \\ar[d] \\\\\n"
 'x \\ar[r] & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "A \\times_k k[V'] \\ar[d] \\ar[r] & k[V'] \\ar[d] \\\\\n"
 'A \\ar[r] & k\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '& x_\\epsilon \\ar[d] \\\\\n'
 "y' \\ar[r] & x_0\n"
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '& k[\\epsilon] \\ar[d] \\\\\n'
 "A \\times_k k[V'] \\ar[r] & k\n"
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[d] \\ar[r] & x_\\epsilon \\ar[d] \\\\\n'
 "y' \\ar[r] & x_0\n"
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "(A \\times_k k[V']) \\times_k k[\\epsilon] \\ar[d] \\ar[r] & k[\\epsilon] \\ar[d] \\\\\n"
 "A \\times_k k[V'] \\ar[r] & k\n"
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r] \\ar[d] & x_V \\ar[d] \\\\\n'
 'x \\ar[r] & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A \\times_k k[V] \\ar[d] \\ar[r] & k[V] \\ar[d] \\\\\n'
 'A \\ar[r] & k\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r] \\ar[d] & x_V \\ar[d] \\\\\n'
 'x \\ar[r] & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{and}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "y' \\ar[r] \\ar[d] & x_V \\ar[d] \\\\\n"
 'x \\ar[r] & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A \\times_k k[V] \\ar[d] \\ar[r] & k[V] \\ar[d] \\\\\n'
 'A \\ar[r] & k\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "y_{V'} \\ar[r] \\ar[d] & x_{V'} \\ar[d] \\\\\n"
 'x \\ar[r] & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{and}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "y'_{V'} \\ar[r] \\ar[d] & x_{V'} \\ar[d] \\\\\n"
 'x \\ar[r] & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "A \\times_k k[V'] \\ar[d] \\ar[r] & k[V'] \\ar[d] \\\\\n"
 'A \\ar[r] & k\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r] \\ar[d] & x_\\epsilon \\ar[d] \\\\\n'
 "y'_{V'} \\ar[r] & x_0\n"
 '}\n'
 '}\n'
 '\\quad\\text{and}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "y' \\ar[r] \\ar[d] & x_\\epsilon \\ar[d] \\\\\n"
 "y'_{V'} \\ar[r] & x_0\n"
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A \\times_k k[\\epsilon] \\ar[d] \\ar[r] & k[\\epsilon] \\ar[d] \\\\\n'
 'A \\ar[r] & k\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r]_c \\ar[d]_a & x_\\epsilon \\ar[d]^e \\\\\n'
 'x \\ar[r]^d          & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{and}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "y' \\ar[r]_{c'} \\ar[d]_{a'} & x'_\\epsilon \\ar[d]^{e'} \\\\\n"
 "x' \\ar[r]^{d'}                 & x'_0\n"
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A \\times_k k[\\epsilon] \\ar[d] \\ar[r] & k[\\epsilon] \\ar[d] \\\\\n'
 'A \\ar[r] & k\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r] \\ar[d]_a & x_\\epsilon \\ar[d]_e \\\\\n'
 'x \\ar[r]^d        & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A \\times_k k[\\epsilon] \\ar[r] \\ar[d] & k[\\epsilon] \\ar[d] \\\\\n'
 'A \\ar[r] & k.\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r] \\ar[d] & x_2 \\ar[d]^{a_2} \\\\\n'
 'x_1 \\ar[r]^{a_1}        & x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A_1 \\times_A A_2 \\ar[r] \\ar[d] & A_2 \\ar[d]^{f_2} \\\\\n'
 'A_1 \\ar[r]^{f_1} & A\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r] \\ar[d] & g_*y \\ar[d] \\\\\n'
 'x_1 \\ar[r]        & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A_1 \\times_k k[\\epsilon] \\ar[r] \\ar[d] & k[\\epsilon] \\ar[d] \\\\\n'
 'A_1 \\ar[r] & k.\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '& \\text{Mod}_R \\ar[dr]^{\\text{forget}} &   \\\\\n'
 '\\text{Mod}^{fg}_R  \\ar[ur]^{\\widetilde{L}} \\ar[rr]^{L} &  &\n'
 '\\textit{Sets}\n'
 '}\n'
 '}\n'
 '\\quad\\text{resp.}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '& \\text{Mod}_R \\ar[dr]^{\\text{forget}} &   \\\\\n'
 '\\text{Mod}_R  \\ar[ur]^{\\widetilde{L}} \\ar[rr]^{L} &  &\n'
 '\\textit{Sets}\n'
 '}\n'
 '}\n'
 '$$',
 '$\\text{Mod}_R \\to S\\text{-Alg}/R$',
 '$S\\text{-Alg}/R$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '            &  y \\ar[d] \\\\\n'
 '\\xi \\ar[r]  &  x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '         &   B  \\ar[d]^{f} \\\\\n'
 'R \\ar[r] &   A\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'z  \\ar[r] \\ar[d]          &  y \\ar[d] \\\\\n'
 "y' \\ar[r]  &  x\n"
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'B \\times_A B \\ar[d] \\ar[r] &   B  \\ar[d]^{f} \\\\\n'
 'B \\ar[r]^{f} &   A .\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'z_1  \\ar[r] \\ar[d] & z \\ar[r] \\ar[d] & y \\ar[d] \\\\\n'
 "y_1 \\ar[r] & y' \\ar[r] &  x\n"
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'B_1 \\times_A B \\ar[d] \\ar[r] & B \\times_A B \\ar[r] \\ar[d] & B \\ar[d]^{f} \\\\\n'
 'B_1 \\ar[r]  & B \\ar[r] &  A .\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\mathcal{J} = \\{ J \\subset I \\mid\n'
 '\\text{there exists an }y \\to x\\text{ lying over }B/J \\to A\\}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '            &  y \\ar[d] \\\\\n'
 '\\xi \\ar[r]  &  x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '         &   B  \\ar[d]^{f} \\\\\n'
 '\\overline{S} \\ar[r] &   A\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '            &  y \\ar[d] \\\\\n'
 '\\xi_n \\ar[r]  &  x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '         &   B  \\ar[d]^{f} \\\\\n'
 'S/J_n \\ar[r] &   A .\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n(H1) + (H2) + (H3)\n\\Rightarrow\n\\text{ there exists a versal formal object}\n$$',
 "$$\n\\Ob(\\mathcal{S}_x) =\n\\{x' \\to x \\mid x' \\to x\\text{ lies over }A' \\subset A\\}\n$$",
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "y' \\ar[d] \\ar[r] & x' \\ar[d] \\\\\n"
 'y \\ar[r] & x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "B' \\ar[d] \\ar[r] & f(B') \\ar[d] \\\\\n"
 'B \\ar[r] & A\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "\\xi' \\ar[d] \\ar[r] & x' \\ar[d] \\\\\n"
 '\\xi \\ar[r] & x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "R' \\ar[d] \\ar[r] & f(R') \\ar[d] \\\\\n"
 'R \\ar[r] & A\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '& y \\ar[d] \\\\\n'
 '\\xi \\ar[r] \\ar@{..>}[ru] & x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '& S/\\mathfrak m_S^n \\ar[d] \\\\\n'
 'R \\ar[r] \\ar@{..>}[ru] & R/\\mathfrak m_R^n\n'
 '}\n'
 '}\n'
 '$$',
 '\\begin{equation}\n'
 '\\label{equation-bijective}\n'
 'd\\underline{\\xi} : \\text{Der}_\\Lambda(R, k) \\to T\\mathcal{F} \n'
 '\\text{ is bijective}\n'
 '\\end{equation}',
 '\\begin{equation}\n'
 '\\label{equation-bijective-orbits}\n'
 'd\\underline{\\xi} : \\text{Der}_\\Lambda(R, k) \\to T\\mathcal{F} \n'
 '\\text{ is bijective on }\\text{Der}_\\Lambda(k, k)\\text{-orbits.}\n'
 '\\end{equation}',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r] \\ar[d] & x_\\epsilon \\ar[d] \\\\\n'
 'x \\ar[r]   & x_0\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 "R'/\\mathfrak m_R^2 \\times_k k[\\epsilon] \\ar[r] \\ar[d] & k[\\epsilon] \\ar[d] \\\\\n"
 "R'/\\mathfrak m_R^2 \\ar[r] & k.\n"
 '}\n'
 '}\n'
 '$$',
 '$$\n(H1) + (H2) + (H3)\n\\Rightarrow\n\\text{ there exists a hull}\n$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'x_1 \\times_x x_2 \\ar[r] \\ar[d] & x_2 \\ar[d] \\\\\n'
 'x_1 \\ar[r]      & x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lies over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A_1 \\times_A A_2 \\ar[r] \\ar[d] & A_2 \\ar[d] \\\\\n'
 'A_1 \\ar[r]      & A.\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'y \\ar[r] \\ar[d] & x_2 \\ar[d]   \\\\\n'
 'x_1 \\ar[r]      & x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A_1 \\times_A A_2 \\ar[r] \\ar[d] & A_2 \\ar[d] \\\\\n'
 'A_1 \\ar[r]      & A.\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'x_1 \\times_x x_2 \\ar[r] \\ar[d] & x_2 \\ar[d] \\\\\n'
 'x_1 \\ar[r]      & x\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 'A_1 \\times_A A_2 \\ar[r] \\ar[d] & A_2 \\ar[d] \\\\\n'
 'A_1 \\ar[r]      & A.\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '           & (u_2, v_2, a_2) \\ar[d] \\\\\n'
 '(u_1, v_1, a_1) \\ar[r] & (u, v, a)\n'
 '}\n'
 '}\n'
 '\\quad\\text{lying over}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '           & A_2 \\ar[d] \\\\\n'
 'A_1 \\ar[r] & A\n'
 '}\n'
 '}\n'
 '$$',
 '$$\n'
 'F :\n'
 '\\left\\{\n'
 '\\begin{matrix}\n'
 '\\text{extensions of }f^{-1}\\mathcal{O}_B\\text{ algebras}\\\\\n'
 "0 \\to \\mathcal{F} \\to \\mathcal{O}' \\to \\mathcal{O}_X \\to 0\\\\\n"
 '\\text{where }\\mathcal{F}\\text{ is an ideal of square zero}\n'
 '\\end{matrix}\n'
 '\\right\\}\n'
 '\\longrightarrow\n'
 '\\left\\{\n'
 '\\begin{matrix}\n'
 '\\text{extensions of }f^{-1}\\mathcal{O}_B\\text{ algebras}\\\\\n'
 "0 \\to \\mathcal{G} \\to \\mathcal{O}' \\to \\mathcal{O}_X \\to 0\\\\\n"
 '\\text{where }\\mathcal{G}\\text{ is an ideal of square zero}\n'
 '\\end{matrix}\n'
 '\\right\\}\n'
 '$$',
 '$$\n'
 'FT :\n'
 '\\{\\text{solutions to }(\\ref{equation-to-solve-ringed-topoi})\n'
 '\\text{ for }\\mathcal{F}\\text{ and }c\\}\n'
 '\\longrightarrow\n'
 '\\{\\text{solutions to }(\\ref{equation-to-solve-ringed-topoi})\n'
 "\\text{ for }\\mathcal{G}\\text{ and }c'\\}\n"
 '$$')

NOTATION_FRAMES = ('\\begin{equation}\n'
 '\\label{equation-restriction-of-scalars}\n'
 '\\text{Res}_{Z/B}(X) : (\\Sch/S)^{opp} \\longrightarrow \\textit{Sets},\n'
 '\\quad\n'
 'T \\longmapsto \\{(a, b)\\text{ as above}\\}\n'
 '\\end{equation}',
 '$\\text{Res}_{Z/B}(X)$',
 '$$\n'
 '\\Mor_{\\Sh((\\Sch/S)_{fppf})}(T, \\text{Res}_{Z/B}(X))\n'
 '=\n'
 '\\{(a, b)\\text{ as in }(\\ref{equation-pairs})\\}\n'
 '$$',
 '$(a_i, b_i) \\in \\text{Res}_{Z/B}(X)(T_i)$',
 '$(a, b) \\in \\text{Res}_{Z/B}(X)(T)$',
 '$v : T \\to \\text{Res}_{Z/B}(X)$',
 '$v(p) \\in \\text{Res}_{Z/B}(X)(U)$',
 '$v : h_U \\to \\text{Res}_{Z/B}(X)$',
 '$T \\to \\text{Res}_{Z/B}(X)$',
 '$\\text{Res}_{Z/B}(X) \\to B$',
 "$$\n\\text{Res}_{Z'/B'}(X')\n=\nB' \\times_B \\text{Res}_{Z/B}(X)\n$$",
 "$\\text{Res}_{Z/B}(X') \\to \\text{Res}_{Z/B}(X)$",
 '$\\text{Res}_{Z/B}(X)(U)$',
 "$$\nh_U \\times_{\\xi, \\text{Res}_{Z/B}(X)} \\text{Res}_{Z/B}(X')\n$$",
 '$$\n'
 '\\xymatrix{\n'
 '\\mathit{Mor}_B(Z, X) \\ar[r] & \\mathit{Mor}_B(Z, Z) \\\\\n'
 '\\text{Res}_{Z/B}(X) \\ar[r] \\ar[u] & B \\ar[u]_{\\text{id}_Z}\n'
 '}\n'
 '$$',
 '$\\text{Res}_{Z/U}(I)$',
 '$\\text{Res}_{Z/U}(W)$',
 '$\\text{Cof}(\\mathcal{C})$',
 '$$\n'
 '\\widehat{~} :\n'
 '\\text{Cof}(\\mathcal{C}_\\Lambda)\n'
 '\\longrightarrow\n'
 '\\text{Cof}(\\widehat{\\mathcal{C}}_\\Lambda)\n'
 '$$',
 '$|_{\\mathcal{C}_\\Lambda} : \\text{Cof}(\\widehat{\\mathcal{C}}_\\Lambda)\n'
 '\\to \\text{Cof}(\\mathcal{C}_\\Lambda)$',
 '$\\mathcal{F} \\in \\Ob(\\text{Cof}(\\mathcal{C}_\\Lambda))$',
 '$\\mathcal{G} \\in \\Ob(\\text{Cof}(\\widehat{\\mathcal{C}}_\\Lambda))$',
 '$\\text{CofSet}(\\mathcal{C})$',
 '$\\widehat{~} : \\text{CofSet}(\\mathcal{C}_\\Lambda) \\to\n'
 '\\text{CofSet}(\\widehat{\\mathcal{C}}_\\Lambda)$',
 '$|_{\\mathcal{C}_\\Lambda} : \\text{CofSet}(\\widehat{\\mathcal{C}}_\\Lambda) \\to\n'
 '\\text{CofSet}(\\mathcal{C}_\\Lambda)$',
 '$F \\in \\Ob(\\text{CofSet}(\\mathcal{C}_\\Lambda))$',
 '$G \\in \\Ob(\\text{CofSet}(\\widehat{\\mathcal{C}}_\\Lambda))$',
 '$\\text{Mod}^{fg}_R$',
 '$L: \\text{Mod}^{fg}_R \\to \\text{Mod}_R$',
 '$\\text{Mod}^{fg}_R \\to \\textit{Sets}$',
 '$L: \\text{Mod}^{fg}_R \\to \\textit{Sets}$',
 '$\\widetilde{L} : \\text{Mod}^{fg}_R \\to \\text{Mod}_R$',
 '$$\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '& \\text{Mod}_R \\ar[dr]^{\\text{forget}} &   \\\\\n'
 '\\text{Mod}^{fg}_R  \\ar[ur]^{\\widetilde{L}} \\ar[rr]^{L} &  &\n'
 '\\textit{Sets}\n'
 '}\n'
 '}\n'
 '\\quad\\text{resp.}\\quad\n'
 '\\vcenter{\n'
 '\\xymatrix{\n'
 '& \\text{Mod}_R \\ar[dr]^{\\text{forget}} &   \\\\\n'
 '\\text{Mod}_R  \\ar[ur]^{\\widetilde{L}} \\ar[rr]^{L} &  &\n'
 '\\textit{Sets}\n'
 '}\n'
 '}\n'
 '$$',
 '$L_1, L_2: \\text{Mod}^{fg}_R \\to \\textit{Sets}$',
 '$M \\in \\Ob(\\text{Mod}^{fg}_R)$',
 '$L : \\text{Mod}^{fg}_K \\to \\text{Mod}_K$',
 '$L: \\text{Mod}^{fg}_K \\to\n\\text{Mod}_K$',
 '$L(K) \\otimes_K - : \\text{Mod}^{fg}_K \\to\n\\text{Mod}_K$',
 '$V \\in \\Ob(\\text{Mod}^{fg}_K)$',
 '$\\text{Mod}_R \\to S\\text{-Alg}/R$',
 '$M, N \\in\n\\Ob(\\text{Mod}^{fg}_R)$',
 '$M\n\\in \\Ob(\\text{Mod}^{fg}_R)$',
 '$\\text{Mod}^{fg}_R \\to \\mathcal{C}$',
 '$\\text{Mod}^{fg}_R \\to \\mathcal{C} \\to \\textit{Sets}$',
 "$$\n\\text{Inf}(x'/x) = \\Ker(\\text{Aut}_{A'}(x') \\to \\text{Aut}_A(x))\n$$",
 "$$\n\\text{Inf}_{x_0}(\\mathcal F) = \\text{Inf}(x'_0/x_0)\n$$",
 '$$\n\\text{Inf}(\\mathcal{F}) = \\text{Inf}_{x_0}(\\mathcal{F})\n$$',
 '$\\text{Inf}(\\mathcal{F}_{x_0}) = \\text{Inf}_{x_0}(\\mathcal{F})$',
 "$\\text{Inf}(x'/x)$",
 "$$\n\\text{Inf}(x'/x) = \\text{Lift}(\\text{id}_x, A')\n$$",
 "$\\text{Inf}(x'/x) = \\text{Lift}(\\text{id}_x, A')$",
 "$\\text{Inf}(x'/x) = 0$",
 '$\\text{Inf}(x/x_0) = 0$',
 '$\\text{Inf}(x/x_0)$',
 '$$\n'
 '0 \\to \\text{Inf}(\\mathcal{W})\n'
 '\\to \\text{Inf}(\\mathcal{H}) \\oplus \\text{Inf}(\\mathcal{G})\n'
 '\\to \\text{Inf}(\\mathcal{F}) \\to\n'
 'T\\mathcal{W} \\to T\\mathcal{H} \\oplus T\\mathcal{G} \\to T\\mathcal{F}\n'
 '$$',
 '$\\text{Inf}(\\mathcal{W}) = \\text{Inf}_{w_0}(\\mathcal{W})$',
 '$\\text{Inf}(\\mathcal{G}) \\to \\text{Inf}(\\mathcal{F})$',
 "$q : \\text{Inf}(p_2(x'_2)/p_2(x_2)) \\to \\text{Inf}(q(p_2(x'_2))/q(p_2(x_2)))$",
 '$\\text{CofSet}(\\mathcal{C}_\\Lambda)$',
 '$$\n\\text{Inf}([U/R]) =\n\\Ker(ds \\oplus dt : TR \\to TU \\oplus TU).\n$$',
 '$$\n'
 '0 \\to \\text{Inf}(\\mathcal{F}) \\to\n'
 'T(U \\times_{f, \\mathcal{F}, f} U) \\to TU \\oplus TU\n'
 '$$',
 '$\\text{Inf}(U) = (0)$',
 '$\\dim_k \\text{Inf}(\\mathcal{F}) < \\infty$',
 '$0 \\to \\text{Inf}(\\mathcal{F}) \\to TR \\to TU \\oplus TU$',
 '$\\dim_k \\text{Inf}(\\mathcal{F})$',
 '$$\n0 \\to \\text{Inf}([U/R]) \\to TR \\to TU \\oplus TU\n$$',
 '$$\n'
 '\\text{Inf}(\\mathcal{F}) \\otimes_k l\n'
 '\\longrightarrow\n'
 '\\text{Inf}(\\mathcal{F}_{l/k})\n'
 '$$',
 '$\\text{Inf}(\\mathcal{F}) = \\text{Inf}_{x_0}(\\mathcal{F})$',
 '$\\text{Inf}(\\mathcal{F}_{l/k}) = \\text{Inf}_{x_{l, 0}}(\\mathcal{F}_{l/k})$')
