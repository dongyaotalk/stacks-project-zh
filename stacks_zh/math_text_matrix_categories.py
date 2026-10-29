"""Finite two-matrix category descriptions; no literal policy or translation.

The entire delimited expression must match, including the two/three row frame.
This is deliberately not a general permission for prose in a matrix.
"""
from __future__ import annotations

import re


def category_description_roles(source, stream):
    from .math_text import delimiter_kind, plain_text

    try:
        kind = delimiter_kind(source)
        width = 2 if kind == 'display-dollar' else 1
        if kind == 'environment':
            return {}
        first, stop = width, len(stream) - width
        cursor, roles = first, {}

        def take(token=None, *, environment=(), depth=0, pattern=None):
            nonlocal cursor
            if cursor >= stop:
                raise ValueError('incomplete category description')
            node = stream[cursor]
            if (node['depth'] != depth or node['environments'] != list(environment)
                    or token is not None and node['token'] != token
                    or pattern is not None and re.fullmatch(pattern, node['token']) is None):
                raise ValueError('outside finite category description grammar')
            cursor += 1
            return node

        def body(token=None, **kwargs):
            return take(token, environment=('matrix',), **kwargs)

        def category():
            first = body(r'\mathcal')
            body('{')
            body(pattern='[A-Z]', depth=1)
            last = body('}', depth=1)
            if re.fullmatch(r'\\mathcal\{[A-Z]\}', source[first['start']:last['end']]) is None:
                raise ValueError('category needs its exact explicitly braced atom')

        def text(*, numeric=False):
            index = cursor
            node = body()
            if node.get('command') != 'text' or not plain_text(node.get('value', '')):
                raise ValueError('description needs a complete pure text parameter')
            if numeric and (not node['value'].startswith('-') or node['value'].startswith('--')
                            or stream[index - 1]['end'] != node['start']):
                raise ValueError('numeric description needs its adjacent single hyphen')
            roles[index] = ('matrix-numeric-category-prefix' if numeric
                            else 'matrix-category-description')

        def opening():
            take(r'\left')
            take(r'\{')
            take(r'\begin{matrix}')

        def closing():
            body(r'\end{matrix}')
            take(r'\right')
            take(r'\}')

        opening()
        body('2')
        text(numeric=True)
        body(r'\\')
        text()
        category()
        body('/')
        body(pattern='[A-Z]')
        closing()
        take(r'\leftrightarrow')
        opening()
        body('2')
        text(numeric=True)
        body('(')
        category()
        body(',')
        body(pattern='[a-z]')
        body(')')
        text()
        body(r'\\')
        text()
        category()
        text()
        category()
        text()
        body(r'\\')
        body(pattern='[a-z]')
        body(':')
        category()
        body(r'\to')
        category()
        body('/')
        body(pattern='[A-Z]')
        text()
        category()
        closing()
        if cursor != stop:
            raise ValueError('extra expression outside category description')
        return roles
    except (ValueError, KeyError, IndexError):
        return {}
