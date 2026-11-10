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

# Exact complete locked-English frames for chapter 59; no wildcard math.
COHOMOLOGY_FRAMES = (
    '$$\nH_\\etale^q (\\mathbf{A}^1_\\mathbf{C} \\setminus \\{0\\}, \\Lambda) = \\left\\{\n\\begin{matrix}\n\\Lambda & \\text{ if }q = 1\\text{, and} \\\\\n0 & \\text{ for }q \\geq 2.\n\\end{matrix}\n\\right.\n$$',
    "\\begin{eqnarray*}\nH_\\etale^1 (X, \\mathbf{Z}/n\\mathbf{Z}) = \\left\\{\n\\begin{matrix}\n\\text{sheaves of sets }\\mathcal{F}\\text{ on the \\'etale site }X_\\etale\n\\text{ endowed with an} \\\\\n\\text{action }\\mathbf{Z}/n\\mathbf{Z} \\times \\mathcal{F} \\to \\mathcal{F}\n\\text{ such that }\\mathcal{F}\\text{ is a }\\mathbf{Z}/n\\mathbf{Z}\\text{-torsor.}\n\\end{matrix}\n\\right\\}\n\\Big/ \\cong\n\\\\\n = \\left\\{\n\\begin{matrix}\n\\text{morphisms }Y \\to X\\text{ which are finite \\'etale together} \\\\\n\\text{ with a free }\\mathbf{Z}/n\\mathbf{Z}\\text{ action such that }\nX = Y/(\\mathbf{Z}/n\\mathbf{Z}).\n\\end{matrix}\n\\right\\}\n\\Big/ \\cong.\n\\end{eqnarray*}",
    '$$\nU \\mapsto \\mathcal{F}^+(U) :=\n\\colim_{\\mathcal{U} \\text{ covering of }U}\n\\check H^0(\\mathcal{U}, \\mathcal{F})\n$$',
    '\\begin{eqnarray*}\nb & \\mapsto & 1 \\otimes b - b \\otimes 1, \\\\\nb_0 \\otimes b_1 & \\mapsto & 1 \\otimes b_0 \\otimes b_1 - b_0 \\otimes 1 \\otimes\nb_1 + b_0 \\otimes b_1 \\otimes 1, \\\\\n& \\text{etc.}\n\\end{eqnarray*}',
    "\\begin{equation}\n\\label{equation-isomorphisms-pairs}\n\\mathit{Isom}_S((\\mathcal{L}, \\alpha), (\\mathcal{L}', \\alpha'))\n=\n\\left\\{\n\\begin{matrix}\n\\emptyset & \\text{if} & \\text{they are not isomorphic} \\\\\nH^0(S, \\mu_{n, S})\\cdot \\varphi & \\text{if} &\n\\varphi \\text{ isomorphism of pairs}\n\\end{matrix}\n\\right.\n\\end{equation}",
    '$$\nH_\\etale^1(S, \\mu_n) =\n\\text{group of pairs }(\\mathcal{L}, \\alpha)\\text{ up to isomorphism as above}\n$$',
    "\\begin{align*}\nu : S_\\etale & \\longrightarrow \\textit{Sets}, \\\\\nU & \\longmapsto\n|U_{\\overline{s}}|\n=\n\\{\\overline{u} \\text{ such that }(U, \\overline{u})\n\\text{ is an \\'etale neighbourhood of }\\overline{s}\\}.\n\\end{align*}",
    '$u(\\text{final object}) = \\text{final object}$',
    "\\begin{equation}\n\\label{equation-descent-etale-forget}\n\\begin{matrix}\n\\text{descent data }(X', \\varphi')\\text{ relative to }S'/S \\\\\n\\text{ with }X'\\text{ \\'etale over }S'\n\\end{matrix}\n\\longrightarrow\n\\text{schemes }X'\\text{ \\'etale over }S'\n\\end{equation}",
    "\\begin{equation}\n\\label{equation-descent-etale}\n\\text{schemes }X\\text{ \\'etale over }S \\longrightarrow\n\\begin{matrix}\n\\text{descent data }(X', \\varphi')\\text{ relative to }S'/S \\\\\n\\text{ with }X'\\text{ \\'etale over }S'\n\\end{matrix}\n\\end{equation}",
    "\\begin{equation}\n\\label{equation-affine-etale}\n\\{\n\\text{affine schemes }V\\text{ \\'etale over }Y\n\\}\n\\leftrightarrow\n\\{\n\\text{affine schemes }U\\text{ \\'etale over }X\n\\}\n\\end{equation}",
    '$$\n\\left\\{\n\\begin{matrix}\n\\text{finite locally constant}\\\\\n\\text{sheaves of sets on }X_\\etale\n\\end{matrix}\n\\right\\}\n\\longleftrightarrow\n\\left\\{\n\\begin{matrix}\n\\text{finite }\\pi_1(X, \\overline{x})\\text{-sets}\n\\end{matrix}\n\\right\\}\n$$',
    '$$\n\\left\\{\n\\begin{matrix}\n\\text{finite locally constant}\\\\\n\\text{sheaves of abelian groups on }X_\\etale\n\\end{matrix}\n\\right\\}\n\\longleftrightarrow\n\\left\\{\n\\begin{matrix}\n\\text{finite }\\pi_1(X, \\overline{x})\\text{-modules}\n\\end{matrix}\n\\right\\}\n$$',
    '$$\n\\left\\{\n\\begin{matrix}\n\\text{finite type, locally constant}\\\\\n\\text{sheaves of }\\Lambda\\text{-modules on }X_\\etale\n\\end{matrix}\n\\right\\}\n\\longleftrightarrow\n\\left\\{\n\\begin{matrix}\n\\text{finite }\\pi_1(X, \\overline{x})\\text{-modules endowed}\\\\\n\\text{with commuting }\\Lambda\\text{-module structure}\n\\end{matrix}\n\\right\\}\n$$',
    '$$\n\\left\\{\n\\begin{matrix}\n\\text{finite type, locally constant}\\\\\n\\text{sheaves of }\\Lambda\\text{-modules on }X_\\etale\n\\end{matrix}\n\\right\\}\n\\longleftrightarrow\n\\left\\{\n\\begin{matrix}\n\\text{finite }\\Lambda\\text{-modules }M\\text{ endowed}\\\\\n\\text{with a continuous }\\pi_1(X, \\overline{x})\\text{-action}\n\\end{matrix}\n\\right\\}\n$$',
    '$$\n\\xymatrix{\n\\text{finite locally constant sheaves of sets on }Y_\\etale\n\\ar[r] &\n\\text{finite }\\pi_1(Y, \\overline{y})\\text{-sets} \\\\\n\\text{finite locally constant sheaves of sets on }X_\\etale\n\\ar[r] \\ar[u]_{f^{-1}} &\n\\text{finite }\\pi_1(X, \\overline{x})\\text{-sets} \\ar[u]\n}\n$$',
    '\\begin{eqnarray*}\n(R^q j_*\\mathbf{G}_{m, \\eta})_{\\bar \\eta}\n& = &\nH_\\etale^q(\\Spec(\\kappa(\\eta)^{sep}) \\times_X \\eta, \\mathbf{G}_m) \\\\\n& = & H_\\etale^q (\\Spec(\\kappa(\\eta)^{sep}), \\mathbf{G}_m) \\\\\n& = & 0 \\ \\ \\text{ for } q \\geq 1\n\\end{eqnarray*}',
    "$\\emptyset = \\bigcap_{I' \\subset I\\text{ finite}} T_{I'}$",
    '$$\n\\Sh(Y_\\etale) \\longrightarrow\n\\left\\{\n(\\mathcal{G}, \\mathcal{H}, \\alpha)\n\\middle|\n\\begin{matrix}\n\\mathcal{G} \\in \\Sh(X_\\etale),\\ \\mathcal{H} \\in \\Sh((\\Sch/Y)_{fppf}), \\\\\n\\alpha : a_X^{-1}\\mathcal{G} \\to f_{big, fppf}^{-1}\\mathcal{H}\n\\text{ an isomorphism}\n\\end{matrix}\n\\right\\}\n$$',
    "$$\n\\{\n\\text{schemes }V\\text{ \\'etale over }Y\n\\}\n\\leftrightarrow\n\\{\n\\text{schemes }U\\text{ \\'etale over }X\n\\}\n$$",
    "$$\n\\Sh(Y_\\etale)\n\\longrightarrow\n\\text{descent data for \\'etale sheaves wrt }\\{X \\to Y\\}\n$$",
    "$$\n\\Sh(Z_\\etale)\n\\longrightarrow\n\\text{descent data for \\'etale sheaves wrt }\\{X \\times_Y Z \\to Z\\}\n$$",
    "$$\n\\Sh((Z \\times_Y Z)_\\etale)\n\\longrightarrow\n\\text{descent data for \\'etale sheaves wrt }\n\\{X \\times_Y (Z \\times_Y Z) \\to Z \\times_Y Z\\}\n$$",
    "$$\n\\Sh(X_\\etale)\n\\longrightarrow\n\\text{descent data for \\'etale sheaves wrt }\\{f_i : X_i \\to X\\}\n$$",
    '$\\text{Aut}_{L\\text{-Algebras}}(\\text{Mat}_d(L))$',
)
COHOMOLOGY_COMPONENT_LITERALS = (" on the \\'etale site ", " which are finite \\'etale together", " is an \\'etale neighbourhood of ", " \\'etale over ", "descent data for \\'etale sheaves wrt ")
COHOMOLOGY_EXISTING_ROLES = {' such that ': ['root-phrase'], ' relative to ': ['descent-data-matrices'], 'descent data ': ['descent-sheaf-set-matrices'], ' for ': ['root-phrase']}
COHOMOLOGY_LITERAL_EXCEPTIONS = frozenset({' up to isomorphism as above', 'action ', ' endowed with an', 'etc.', 'sheaves of abelian groups on ', 'descent data ', ' with ', ' relative to ', 'with a continuous ', ' isomorphism of pairs', '-modules endowed', 'finite type, locally constant', '-modules', ' if ', 'they are not isomorphic', '-modules on ', 'finite ', " which are finite \\'etale together", 'sheaves of sets on ', " \\'etale over ", 'morphisms ', 'sheaves of sets ', 'group of pairs ', 'schemes ', '-torsor.', ' covering of ', ' action such that ', ' for ', '-module structure', ' is a ', " is an \\'etale neighbourhood of ", '-action', ', and', 'with commuting ', 'final object', '-sets', '-modules ', 'finite locally constant sheaves of sets on ', " on the \\'etale site ", 'finite locally constant', ' with a free ', 'affine schemes ', 'sheaves of ', ' an isomorphism', ' endowed', "descent data for \\'etale sheaves wrt ", ' finite', ' such that '})
COHOMOLOGY_LITERAL_EXCEPTIONS = COHOMOLOGY_LITERAL_EXCEPTIONS | {'-Algebras'}
SCHEME_FRAMES += COHOMOLOGY_FRAMES
COMPONENT_LITERALS += tuple(x for x in COHOMOLOGY_COMPONENT_LITERALS if x not in COMPONENT_LITERALS)
CONTEXTS['etale-scheme-diagrams'].update((role, literal) for literal, roles in COHOMOLOGY_EXISTING_ROLES.items() for role in roles)


def component_contract(literal):
    return dict(literal=literal if literal in COMPONENT_LITERALS else None,
        usage=COMPONENT_USAGE, components=literal.split(SEPARATOR)
        if literal in COMPONENT_LITERALS else [], separator=SEPARATOR)


def literal_exception(literal, role):
    return role == 'etale-scheme-diagrams' and (literal == 'schemes quasi-compact,'
        or literal in COHOMOLOGY_LITERAL_EXCEPTIONS)


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
        if frame in COHOMOLOGY_FRAMES and kind == 'etale-scheme-diagrams':
            # Context fallback must not compete with an already valid role.
            from .math_text import usage as ordinary_usage
            if any(ordinary_usage(source, stream, index, role) is not None
                   for role in COHOMOLOGY_EXISTING_ROLES.get(target['value'], ())):
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


# Finite original notation contexts; changes to any byte remain blocked.
COHOMOLOGY_NOTATION_FRAMES = {'pr': ['$$\n\\xymatrix{\nX \\ar[d]_f \\ar[r]_i & \\mathbf{A}^{n + m}_K \\ar[d]^{\\text{pr}} \\\\\nY \\ar[r]^j & \\mathbf{A}^n_K\n}\n$$', '$\\text{pr} : \\mathbf{A}^{n + m}_K \\to \\mathbf{A}^n_K$'], 'can': ["$$\n\\begin{matrix}\n\\varphi_\\text{can}: & N' \\otimes_A B & \\to & B \\otimes_A N' \\\\\n& b_0 \\otimes m \\otimes b_1 & \\mapsto & b_0 \\otimes b_1 \\otimes m.\n\\end{matrix}\n$$", '$(N, \\varphi) \\cong (B \\otimes_A M,\n\\varphi_\\text{can})$'], '-Sets': ['$$\n\\begin{matrix}\n\\rho : & G^{opp} & \\longrightarrow & \\text{Aut}_{G\\textit{-Sets}}({}_G G) \\\\\n& g & \\longmapsto & (h \\mapsto hg).\n\\end{matrix}\n$$', '$$\n\\begin{matrix}\n\\Sh(\\mathcal{T}_G) & \\longrightarrow & G\\textit{-Sets} \\\\\n\\mathcal{F} & \\longmapsto & \\mathcal{F}({}_G G)\n\\end{matrix}\n$$', '$$\n\\Sh(S_\\etale) \\longrightarrow\n\\text{Gal}_{\\kappa(s)}\\textit{-Sets},\n\\quad\n\\mathcal{F} \\longmapsto \\mathcal{F}_{\\overline{s}}\n$$', '\\begin{eqnarray*}\n\\Gamma(S, \\mathcal{F}) & = &\n\\Mor_{\\Sh(S_\\etale)}(h_{\\Spec(K)},  \\mathcal{F})\n\\\\\n& = & \\Mor_{G\\textit{-Sets}}(\\{*\\}, M) \\\\\n& = & M^G\n\\end{eqnarray*}']}

def notation_context(source, stream, index, value, kind):
    roles = {"pr": "etale-projection", "can": "etale-canonical-map",
             "-Sets": "etale-set-category", "F\\'Et": "etale-finite-etale-category",
             "red": "etale-reduced-norm", "PAb": "etale-pab-category"}
    if (roles.get(value) != kind or not 0 <= index < len(stream)
            or stream[index].get("value") != value
            or stream[index].get("command") != ("textit" if value in {"-Sets", "F\\'Et", "PAb"} else "text")
            or source not in COHOMOLOGY_NOTATION_FRAMES.get(value, ())):
        return None
    return source[:stream[index]["start"]] + source[stream[index]["end"]:]

COHOMOLOGY_NOTATION_FRAMES.update({
    "F\\'Et": (r"$\textit{F\'Et}_S$",),
    'red': ("$$\n\\det = N_\\text{red} : D \\longrightarrow K\n$$",
            r'$N_\text{red}(x) = 0$'),
    'PAb': (r'$\textit{PAb}$',),
})
