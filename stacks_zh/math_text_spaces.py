"""Opt-in roles for finite, byte-locked algebraic-space math frames.

Frame constants are source-only syntax fixtures. They grant no production
literal permission; independent macro policy and Git witnesses remain required.
"""
from .math_text_descent import _matches, _frame_nodes

USAGE = 'spaces-source-frames'
USAGES = {USAGE}


FRAMES = (
    r"""$$
I =
\{x = (x_n) \in A \mid \text{all but a finite number of }x_n\text{ are zero}\}
$$""",
    r"""$$
\left\{
\begin{matrix}
\text{category of algebraic}\\
\text{spaces over }S
\end{matrix}
\right\}
\leftrightarrow
\left\{
\begin{matrix}
\text{category of pairs }(F', F' \to S)\text{ consisting}\\
\text{of an algebraic space }F'\text{ over }S'\text{ and a}\\
\text{morphism }F' \to S\text{ of algebraic spaces over }S'
\end{matrix}
\right\}
$$""",
    r"""\begin{align*}
f \text{ has }\mathcal{P}_{spaces}
& \Leftrightarrow
U \to V \text{ has }\mathcal{P} \\
& \Leftrightarrow
\text{each }U_i \to V \text{ has }\mathcal{P} \\
& \Leftrightarrow
\text{each }X_i \to Y\text{ has }\mathcal{P}_{spaces}.
\end{align*}""",
    r"""$$
\begin{matrix}
\text{category of descent data } \\
\text{relative to the family } \{X_i \to X\}_{i \in I}
\end{matrix}
\longrightarrow
\begin{matrix}
\text{ category of descent data} \\
\text{ relative to } Y/X
\end{matrix}
$$""",
    r"""$$
\left\{
\begin{matrix}
\text{descent data }(V_i, \varphi_{ij})\\
\text{relative to }\{X_i \to X\}
\end{matrix}
\right\}
\leftrightarrow
\left\{
\begin{matrix}
\text{sheaves }F\text{ on }(\Sch/S)_{fppf}\text{ endowed}\\
\text{with a map }F \to X\text{ such that each}\\
X_i \times_X F\text{ is an algebraic space}
\end{matrix}
\right\}.
$$""",
)

CATEGORY_FRAMES = (
    r"""$\textit{Spaces}/S$""",
    r"""$\textit{Spaces}'/S$""",
    r"""$$
\textit{Spaces}/S \longrightarrow \textit{Spaces}'/S
$$""",
    r"""$X' \in \Ob(\textit{Spaces}'/S)$""",
    r"""$(\textit{Spaces}/S)_\tau$""",
    r"""$(\textit{Spaces}/X)_\tau$""",
    r"""$\textit{Spaces}/X$""",
    r"""$(\textit{Spaces}/X)_\etale$""",
    r"""$(\textit{Spaces}/X)_{smooth}$""",
    r"""$(\textit{Spaces}/S)_\etale$""",
    r"""$Y_{spaces, \etale} \to (\textit{Spaces}/X)_\etale$""",
    r"""$$
i_f :
\Sh(Y_\etale)
\longrightarrow
\Sh((\textit{Spaces}/X)_\etale)
$$""",
    r"""$u : Y_{spaces, \etale} \to (\textit{Spaces}/X)_\etale$""",
    r"""$X_{spaces, \etale} \to (\textit{Spaces}/X)_\etale$""",
    r"""$$
\pi_X :
(\textit{Spaces}/X)_\etale
\longrightarrow
X_{spaces, \etale}
$$""",
    r"""$$
i_X :
\Sh(X_\etale)
\longrightarrow
\Sh((\textit{Spaces}/X)_\etale)
$$""",
    r"""$u : X_{spaces, \etale} \to (\textit{Spaces}/X)_\etale$""",
    r"""\begin{align*}
\Mor_{\Sh(X_\etale)}(
\mathcal{F}|_{X_\etale},
\mathcal{G})
& =
\Mor_{\Sh((\textit{Spaces}/X)_\etale)}(
\mathcal{F},
i_{X, *}\mathcal{G}) \\
\Mor_{\Sh(X_\etale)}(
\mathcal{G},
\mathcal{F}|_{X_\etale})
& =
\Mor_{\Sh((\textit{Spaces}/X)_\etale)}(
\pi_X^{-1}\mathcal{G},
\mathcal{F})
\end{align*}""",
    r"""$$
u :
(\textit{Spaces}/Y)_\etale
\longrightarrow
(\textit{Spaces}/X)_\etale,
\quad
V/Y \longmapsto V/X
$$""",
    r"""$$
v :
(\textit{Spaces}/X)_\etale
\longrightarrow
(\textit{Spaces}/Y)_\etale,
\quad
(U \to X) \longmapsto (U \times_X Y \to Y).
$$""",
    r"""$$
f_{big} :
\Sh((\textit{Spaces}/Y)_\etale)
\longrightarrow
\Sh((\textit{Spaces}/X)_\etale)
$$""",
    r"""$$
\xymatrix{
Y_{spaces, \etale} \ar[d]_{f_{spaces, \etale}} &
(\textit{Spaces}/Y)_\etale \ar[d]^{f_{big}} \ar[l]^-{\pi_Y}\\
X_{spaces, \etale} &
(\textit{Spaces}/X)_\etale \ar[l]_-{\pi_X}
}
$$""",
    r"""$(\textit{Spaces}/Y)_\etale$""",
    r"""$(\textit{Spaces}/Y)_\etale \to (\textit{Spaces}/X)_\etale$""",
    r"""$(\textit{Spaces}/S)_{fppf}$""",
    r"""$(\textit{Spaces}/X)_{fppf}$""",
    r"""$$
u : (\textit{Spaces}/Y)_{fppf} \longrightarrow (\textit{Spaces}/X)_{fppf},
\quad
V/Y \longmapsto V/X
$$""",
    r"""$$
v : (\textit{Spaces}/X)_{fppf} \longrightarrow (\textit{Spaces}/Y)_{fppf},
\quad
(U \to Y) \longmapsto (U \times_X Y \to Y).
$$""",
    r"""$$
f_{big} :
\Sh((\textit{Spaces}/Y)_{fppf})
\longrightarrow
\Sh((\textit{Spaces}/X)_{fppf})
$$""",
    r"""$(\textit{Spaces}/S)_{ph}$""",
    r"""$(\textit{Spaces}/X)_{ph}$""",
    r"""$$
u : (\textit{Spaces}/Y)_{ph} \longrightarrow (\textit{Spaces}/X)_{ph},
\quad
V/Y \longmapsto V/X
$$""",
    r"""$$
v : (\textit{Spaces}/X)_{ph} \longrightarrow (\textit{Spaces}/Y)_{ph},
\quad
(U \to Y) \longmapsto (U \times_X Y \to Y).
$$""",
    r"""$$
f_{big} :
\Sh((\textit{Spaces}/Y)_{ph})
\longrightarrow
\Sh((\textit{Spaces}/X)_{ph})
$$""",
)

CONTEXTS = {USAGE: {('matrix-category-description', ' consisting'), ('etale-scheme-diagrams', 'descent data '), ('root-phrase', ' over '), ('descent-data-matrices', ' category of descent data'), ('descent-data-matrices', 'relative to the family '), ('root-phrase', ' has '), ('root-phrase', 'each '), ('descent-data-matrices', 'category of descent data '), ('descent-sheaf-set-matrices', 'each '), ('descent-sheaf-set-matrices', 'sheaves '), ('descent-sheaf-set-matrices', ' on '), ('etale-scheme-diagrams', ' endowed'), ('descent-sheaf-set-matrices', 'descent data '), ('matrix-category-description', ' over '), ('descent-data-matrices', ' relative to '), ('etale-scheme-diagrams', ' relative to ')}}


def usage(source, stream, index, kind):
    if kind != USAGE or not 0 < index < len(stream) - 1:
        return None
    from .math_text import usage as ordinary_usage
    for frame in FRAMES:
        expected = _frame_nodes(frame)
        if not _matches(source, stream, frame, natural=True):
            continue
        target = expected[index]
        if target.get('command') != 'text':
            continue
        # A new context never competes with a still-valid old role.
        if any(ordinary_usage(source, stream, index, role) is not None
               for role, literal in CONTEXTS[USAGE] if literal == target['value']):
            continue
        node = stream[index]
        return {'before': source[stream[index-1]['start']:node['start']],
                'after': source[node['end']:stream[index+1]['end']],
                'environments': node['environments']}
    return None


def notation_context(source, stream, index, value, kind):
    if (kind != 'spaces-category' or value != 'Spaces'
            or not 0 <= index < len(stream)
            or stream[index].get('command') != 'textit'
            or stream[index].get('value') != value
            or source not in CATEGORY_FRAMES):
        return None
    return source[:stream[index]['start']] + source[stream[index]['end']:]
