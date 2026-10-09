"""Lossless, non-executing source inventory, separate from adopted translations.

Every byte belongs to a proposed unit or a locked segment. Unsupported syntax
is retained and reported; writing an inventory does not make it adoptable.
"""
from __future__ import annotations

import ast
import bisect
import collections
import json
import re
import shutil
import subprocess
import tempfile
from array import array
from pathlib import Path
from typing import Any

from .chapter_templates import manifest_chapters
from .records import RecordError, stamp_unit_hashes
from .source_reextractions import LockedEnglish, _git_bytes, byte_hash, source_tex

VERSION = 'source-extraction-v3'
COMMAND = re.compile(r'\\(?:[A-Za-z@]+|[\s\S])')
ENVIRONMENT = re.compile(r'\\(begin|end)\{([A-Za-z][A-Za-z0-9*_-]*)\}')
WORD = re.compile(r'[A-Za-z]{2,}')
STATEMENTS = {'definition', 'lemma', 'proposition', 'theorem', 'corollary',
              'remark', 'remarks', 'example', 'exercise', 'situation'}
SCAFFOLD = {'item', 'noindent', 'medskip', 'smallskip', 'bigskip', 'par',
            'maketitle', 'phantomsection', 'tableofcontents',
            'bibliography', 'bibliographystyle'}


class SyntaxProblem(RecordError):
    def __init__(self, message: str, offset: int):
        super().__init__(message)
        self.offset = offset


class Policy:
    """Read the current explicit YAML subset; never infer unknown macro policy."""
    def __init__(self, text: str, *, natural_text_enabled: bool = True):
        if not all(re.search(r'(?m)^' + name + r': block\s*$', text)
                   for name in ('default_command_policy', 'default_environment_policy')):
            raise RecordError('extraction requires explicit blocking defaults in macro policy')
        self.commands: dict[str, str] = {}
        self.math: set[str] = set()
        self.literal: set[str] = set()
        self.metadata: set[str] = set()
        self.body: set[str] = set()
        self.accents: set[str] = set()
        self.special: set[str] = set()
        self.math_text_notations: dict[str, dict[str, Any]] = {}
        self.raw = text
        self.math_text_witnesses: dict[str, dict[str, Any]] = {}
        notation_section_seen = False
        section = group = command = ''
        for line in text.splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            if not line.startswith(' '):
                section = line.partition(':')[0]
                group = command = ''
                if section == 'locked_math_text_notations':
                    if notation_section_seen or line != 'locked_math_text_notations:':
                        raise RecordError('invalid or duplicate math-text notation policy section')
                    notation_section_seen = True
            elif section == 'locked_math_text_notations':
                if re.fullmatch(r'  (?:[A-Za-z]{2,}|-Sets):', line):
                    group = line.strip()[:-1]
                    if group in self.math_text_notations:
                        raise RecordError('duplicate math-text notation policy entry')
                    self.math_text_notations[group] = {}
                else:
                    field = re.fullmatch(r'    (commands|usages|source_label|prefix): (.+)', line)
                    if not field or not group or field[1] in self.math_text_notations[group]:
                        raise RecordError('invalid or duplicate math-text notation policy field')
                    try:
                        value = json.loads(field[2]) if field[1] != 'source_label' else field[2]
                    except json.JSONDecodeError as exc:
                        raise RecordError('invalid math-text notation policy value') from exc
                    self.math_text_notations[group][field[1]] = value
            elif section == 'commands' and re.match(r'^  \S', line):
                key = line.strip().removesuffix(':')
                command = ast.literal_eval(key) if key[:1] in {'"', "'"} else key
            elif section == 'commands' and line.startswith('    policy:'):
                self.commands[command] = line.partition(':')[2].strip()
            elif section == 'locked_environment_groups' and re.match(r'^  \S', line):
                group = line.strip().removesuffix(':')
            elif section == 'locked_environment_groups' and line.strip().startswith('- '):
                if group not in {'math', 'literal', 'editorial_metadata'}:
                    raise RecordError('unsupported locked environment policy group')
                destination = {'math': self.math, 'literal': self.literal,
                               'editorial_metadata': self.metadata}[group]
                destination.add(line.strip()[2:])
            elif section == 'translatable_body_environments' and line.strip().startswith('- '):
                self.body.add(line.strip()[2:])
            elif section == 'special_environments' and re.match(r'^  \S', line):
                self.special.add(line.strip().removesuffix(':'))
            elif section == 'text_accent_commands' and line.strip().startswith('- '):
                self.accents.add(ast.literal_eval(line.strip()[2:]))
        supported = {'locked', 'mixed', 'translate_arguments',
                     'preserve_wrapper_translate_children',
                     'preserve_scoped_declaration_translate_children',
                     'special_index_record', 'lock_structure_translate_explicit_text_nodes'}
        if not self.commands or set(self.commands.values()) - supported:
            raise RecordError('unsupported extraction command policy')
        for notation, rule in self.math_text_notations.items():
            prefixed = rule.get('usages') == ['prefixed-symbol']
            fields = {'commands', 'usages', 'source_label'} | ({'prefix'} if prefixed else set())
            if set(rule) != fields:
                raise RecordError('incomplete math-text notation policy')
            for key, allowed in [('commands', {'text', 'textit', 'textbf'}),
                                 ('usages', {'symbol', 'applied', 'subscripted', 'prefixed-symbol'})]:
                values = rule[key]
                if (not isinstance(values, list) or not values or
                        any(not isinstance(v, str) or v not in allowed for v in values) or
                        len(values) != len(set(values))):
                    raise RecordError('unsupported math-text notation policy ' + key)
            if 'prefixed-symbol' in rule['usages'] and not prefixed:
                raise RecordError('prefixed math-text notation cannot mix usages')
            if prefixed and (not isinstance(rule['prefix'], str) or
                             not re.fullmatch(r'[A-Z]', rule['prefix'])):
                raise RecordError('invalid math-text notation prefix')
            if notation == '-Sets' and (not prefixed or rule['commands'] != ['textit']):
                raise RecordError('unsupported -Sets notation policy')
            if not re.fullmatch(r'[a-z][a-z0-9_-]*-[A-Za-z][A-Za-z0-9_-]*', rule['source_label']):
                raise RecordError('invalid math-text notation source label')
        from .math_text import policy_rules
        try:
            self.math_text_rules = policy_rules(text, self.math_text_notations) if natural_text_enabled else {}
        except (ValueError, TypeError) as exc:
            raise RecordError('invalid natural math-text policy: ' + str(exc)) from exc


class Scanner:
    def __init__(self, text: str, policy: Policy):
        self.text, self.policy = text, policy
        self.math_text_classifications: list[dict[str, Any]] = []
        self.math_text_regions: list[dict[str, Any]] = []

    def comment_end(self, offset: int) -> int:
        end = self.text.find('\n', offset)
        return len(self.text) if end < 0 else end + 1

    def skip_space(self, offset: int) -> int:
        while offset < len(self.text):
            if self.text[offset].isspace():
                offset += 1
            elif self.text[offset] == '%':
                offset = self.comment_end(offset)
            else:
                break
        return offset

    def math_end(self, start: int) -> int:
        text = self.text
        opening = text[start:start + 2]
        if opening not in {'$$', r'\[', r'\('}:
            opening = '$'
        closing = {'$$': '$$', '$': '$', r'\[': r'\]', r'\(': r'\)'}[opening]
        i = start + len(opening)
        while i < len(text):
            if text.startswith(closing, i):
                if closing == '$' and text.startswith('$$', i):
                    raise SyntaxProblem('ambiguous dollar math', i)
                return i + len(closing)
            if text[i] == '%':
                i = self.comment_end(i)
            elif text[i] == '\\':
                match = COMMAND.match(text, i)
                i = match.end() if match else i + 1
            else:
                i += 1
        raise SyntaxProblem('unclosed math', start)

    def argument_end(self, start: int) -> int:
        opening = self.text[start]
        closing = {'{': '}', '[': ']'}[opening]
        depth, brace_depth, i = 1, 0, start + 1
        while i < len(self.text):
            c = self.text[i]
            if c == '%':
                i = self.comment_end(i)
            elif c == '$' or self.text.startswith((r'\[', r'\('), i):
                i = self.math_end(i)
            elif c == '\\':
                match = COMMAND.match(self.text, i)
                i = match.end() if match else i + 1
            else:
                if opening == '[':
                    brace_depth += (c == '{') - (c == '}')
                    if brace_depth < 0:
                        raise SyntaxProblem('unbalanced group in optional argument', i)
                if not brace_depth and c == opening:
                    depth += 1
                elif not brace_depth and c == closing:
                    depth -= 1
                    if depth == 0:
                        return i + 1
                i += 1
        raise SyntaxProblem('unclosed command argument', start)

    def environment_end(self, start: int) -> int:
        first = ENVIRONMENT.match(self.text, start)
        if first is None or first[1] != 'begin':
            raise SyntaxProblem('expected environment opening', start)
        name = first[2]
        if name in self.policy.literal:
            end = self.text.find(r'\end{' + name + '}', first.end())
            if end < 0:
                raise SyntaxProblem('unclosed literal environment', start)
            return end + len(name) + 6
        stack, i = [name], first.end()
        while i < len(self.text):
            if self.text[i] == '%':
                i = self.comment_end(i)
            elif self.text[i] == '$' or self.text.startswith((r'\[', r'\('), i):
                i = self.math_end(i)
            elif self.text[i] == '\\':
                match = ENVIRONMENT.match(self.text, i)
                if match:
                    action, child = match[1], match[2]
                    if action == 'begin' and child in self.policy.literal:
                        i = self.environment_end(i)
                        continue
                    if action == 'begin':
                        stack.append(child)
                    elif not stack or stack.pop() != child:
                        raise SyntaxProblem('mismatched environment closing', i)
                    if not stack:
                        return match.end()
                    i = match.end()
                else:
                    command = COMMAND.match(self.text, i)
                    i = command.end() if command else i + 1
            else:
                i += 1
        raise SyntaxProblem('unclosed environment', start)

    def command_arguments(self, start: int, count: int = 1, optional: bool = False) -> tuple[int, list[tuple[int, int]]]:
        match = COMMAND.match(self.text, start)
        if match is None:
            raise SyntaxProblem('incomplete command', start)
        i, args = match.end(), []
        if self.text[i:i + 1] == '*':
            i += 1
        if optional:
            while self.text[self.skip_space(i):self.skip_space(i) + 1] == '[':
                i = self.argument_end(self.skip_space(i))
        for _ in range(count):
            opening = self.skip_space(i)
            if self.text[opening:opening + 1] != '{':
                raise SyntaxProblem('missing command argument: ' + match.group(), start)
            i = self.argument_end(opening)
            args.append((opening, i))
        return i, args

    def preceding_math_prefix(self, command_start: int, prefix: str) -> str | None:
        """Recognize a bare letter outside command arguments, without TeX expansion.

        Unknown commands keep their following arguments ineligible. Only explicit
        zero-argument math operators/spacing may introduce an unbraced prefix.
        Ordinary math groups are eligible; text, literal and scripted arguments
        are not. Comments are lexically skipped but retained in the witness.
        """
        zero_argument = {'Ob', 'alpha', 'to', 'rightarrow', 'leftarrow', 'longrightarrow',
                         'in', 'notin', 'subset', 'subseteq', 'supset', 'supseteq',
                         'times', 'cap', 'cup', 'cong', 'simeq', 'leq', 'geq',
                         'neq', 'colon', 'quad', 'qquad', 'left', 'right',
                         'big', 'Big', 'bigl', 'Bigl', 'biggl', 'Biggl',
                         ' ', ',', ';', ':', '!', '{', '}'}
        single_argument = {'mathcal', 'mathbb', 'mathbf', 'mathrm', 'mathsf',
                           'mathtt', 'operatorname', 'text', 'textit', 'textbf'}
        # Each frame stores its closing token, inherited block, and whether it
        # is a command/script argument. Closing an argument keeps later arguments
        # of the same unknown command blocked (including optional arguments).
        frames: list[tuple[str, bool, str]] = []
        blocked, pending_argument, candidate, i = False, '', None, 0
        while i < command_start:
            c = self.text[i]
            if c.isspace():
                i += 1
                continue
            if c == '%':
                stop = self.comment_end(i)
                if stop > command_start:
                    return None
                i = stop
                continue
            candidate = None
            if c == '\\':
                match = COMMAND.match(self.text, i)
                if not match or match.end() > command_start:
                    return None
                name = match.group()[1:]
                i = match.end()
                if name not in zero_argument and self.text[i:i + 1] == '*':
                    i += 1
                if name == 'verb':
                    if i >= command_start or self.text[i].isspace():
                        return None
                    stop = self.text.find(self.text[i], i + 1)
                    if stop < 0 or stop >= command_start:
                        return None
                    i = stop + 1
                if name == 'begin':
                    opening = self.skip_space(i)
                    if self.text[opening:opening + 1] == '{':
                        stop = self.argument_end(opening)
                        environment = self.text[opening + 1:stop - 1]
                        if environment in self.policy.literal:
                            stop = self.environment_end(match.start())
                            if stop > command_start:
                                return None
                            i = stop
                if pending_argument != 'unknown':
                    pending_argument = ('single' if name in single_argument else
                                        '' if name in zero_argument else 'unknown')
            elif c == '{' or (c == '[' and pending_argument):
                frames.append(('}' if c == '{' else ']', blocked, pending_argument))
                blocked = blocked or bool(pending_argument)
                pending_argument = ''
                i += 1
            elif c in '}]' and frames and c == frames[-1][0]:
                _, blocked, pending_argument = frames.pop()
                if pending_argument == 'single':
                    pending_argument = ''
                i += 1
            elif c == '}':
                return None
            elif c in '_^':
                if pending_argument != 'unknown':
                    pending_argument = 'single'
                i += 1
            elif c.isascii() and c.isalpha():
                stop = i + 1
                while stop < command_start and self.text[stop].isascii() and self.text[stop].isalpha():
                    stop += 1
                if not blocked and not pending_argument and self.text[i:stop] == prefix:
                    candidate = i
                if pending_argument == 'single':
                    pending_argument = ''
                i = stop
            else:
                # Explicit math punctuation ends an unknown command's argument
                # sequence. Whitespace alone never supplies that boundary.
                if c in ',=+*/<>|&;:$':
                    pending_argument = ''
                elif c not in "()[]'":
                    pending_argument = '' if c.isdigit() and pending_argument == 'single' else 'unknown'
                i += 1
        return self.text[candidate:command_start] if candidate is not None else None

    def notation_usage(self, command: str, value: str, closing: int, *, command_start: int | None = None):
        """Match an explicit notation rule and its original following tokens."""
        rule = self.policy.math_text_notations.get(value)
        if rule is None or command not in rule['commands']:
            return None
        cursor = self.skip_space(closing)
        for usage in rule['usages']:
            if usage == 'prefixed-symbol' and command_start is not None:
                preceding = self.preceding_math_prefix(command_start, rule['prefix'])
                if preceding is not None:
                    return usage, preceding, rule['source_label']
            if usage == 'symbol':
                return usage, '', rule['source_label']
            if usage == 'applied':
                paren = cursor
                size = COMMAND.match(self.text, paren)
                if size and size.group()[1:] in {'left', 'big', 'Big', 'bigl', 'Bigl', 'biggl', 'Biggl'}:
                    paren = self.skip_space(size.end())
                if self.text[paren:paren + 1] == '(':
                    return usage, self.text[closing:paren + 1], rule['source_label']
            if usage == 'subscripted' and self.text[cursor:cursor + 1] == '_':
                token = self.skip_space(cursor + 1)
                if self.text[token:token + 1] == '{':
                    stop = self.argument_end(token)
                    if self.skip_space(token + 1) >= stop - 1:
                        continue
                elif token < len(self.text) and self.text[token].isalnum():
                    stop = token + 1
                else:
                    subscript = COMMAND.match(self.text, token)
                    if not subscript or subscript.group()[1:] in {')', ']', 'end'}:
                        continue
                    stop = subscript.end()
                return usage, self.text[closing:stop], rule['source_label']
        return None

    def protect(self, start: int, end: int) -> tuple[str, dict[str, str], list[dict[str, Any]]]:
        self.math_text_classifications = []
        self.math_text_regions = []
        placeholders: dict[str, str] = {}
        counts: collections.Counter[str] = collections.Counter()
        diagnostics: list[dict[str, Any]] = []

        def lock(role: str, a: int, b: int) -> str:
            counts[role] += 1
            if counts[role] > 9999:
                raise SyntaxProblem('unit exceeds protected token capacity', a)
            name = f'{role}_{counts[role]:04d}'
            placeholders[name] = self.text[a:b]
            return '<' + name + '>'

        def issue(kind: str, a: int, b: int, message: str):
            diagnostics.append({'kind': kind, 'start': a, 'end': b, 'message': message,
                                'source': self.text[a:b], 'severity': 'BLOCKED'})

        def math(a: int, b: int) -> str:
            # Only exact notation or witnessed plain-text classifications are
            # accepted. Every other textual parameter remains a blocker.
            fragment = self.text[a:b]
            child = Scanner(fragment, self.policy)
            from .math_text import find_slots, delimiter_kind
            try:
                slots = find_slots(fragment, self.policy.math_text_rules) if self.policy.math_text_witnesses else []
            except ValueError:
                slots = []
            slots_by_parameter = {s['parameter_start']: s for s in slots}
            i = 0
            while i < len(fragment):
                if fragment[i] == '%':
                    i = child.comment_end(i)
                    continue
                match = COMMAND.match(fragment, i) if fragment[i] == '\\' else None
                if match:
                    opening = child.skip_space(match.end())
                    if match.group()[1:] in {'text', 'textit', 'textbf'} and fragment[opening:opening + 1] == '{':
                        try:
                            close = child.argument_end(opening)
                        except SyntaxProblem:
                            close = opening + 1
                        value = fragment[opening + 1:close - 1]
                        if WORD.search(value):
                            notation = child.notation_usage(match.group()[1:], value, close, command_start=i)
                            if notation is None and opening + 1 not in slots_by_parameter:
                                issue('math-text', a + opening + 1, a + close - 1,
                                      'explicit text inside locked math requires classification before adoption')
                            elif notation is not None:
                                usage, usage_source, source_label = notation
                                self.math_text_classifications.append({
                                    'start': a + i, 'end': a + close, 'source': fragment[i:close],
                                    'notation': value, 'command': match.group()[1:], 'usage': usage,
                                    'usage_source': usage_source, 'source_label': source_label})
                    i = match.end()
                else:
                    i += 1
            if not slots:
                return lock('MATH', a, b)
            pieces, text_slots, protected, cursor = [], [], [], 0
            for ordinal, slot in enumerate(slots, 1):
                before = lock('MATHSEG', a + cursor, a + slot['parameter_start'])
                name = before[1:-1]
                pieces.append({'kind': 'locked', 'placeholder': name})
                identifier = f'temporary/{ordinal:04d}'
                pieces.append({'kind': 'text', 'slot_id': identifier})
                text_slots.append({'slot_id': identifier, 'source': slot['value'], 'command': 'text',
                    'policy_entry': slot['policy_entry'],
                    'slot_byte_span': {'start': len(fragment[:slot['parameter_start']].encode('utf-8')),
                                       'end': len(fragment[:slot['parameter_end']].encode('utf-8'))},
                    'boundary_placeholders': [name],
                    'classification_witness': {'usage': slot['usage'], 'usage_source': slot['usage_source'],
                        'source_label': self.policy.math_text_rules[slot['policy_entry']]['source_label'],
                        'policy_hash': byte_hash(self.policy.raw),
                        'anchor': self.policy.math_text_witnesses[slot['policy_entry']]}})
                protected.extend([before, slot['value']])
                cursor = slot['parameter_end']
            after = lock('MATHSEG', a + cursor, b)
            pieces.append({'kind': 'locked', 'placeholder': after[1:-1]})
            protected.append(after)
            for index, slot in enumerate(text_slots):
                slot['boundary_placeholders'].append(pieces[2 * index + 2]['placeholder'])
            self.math_text_regions.append({'region_id': 'temporary', 'delimiter_kind': delimiter_kind(fragment),
                'source': fragment, 'source_hash': byte_hash(fragment), 'source_byte_span': {'start': 0, 'end': 0},
                'pieces': pieces, 'slots': text_slots})
            return ''.join(protected)

        def walk(a: int, b: int) -> str:
            out: list[str] = []
            i = a
            while i < b:
                c = self.text[i]
                if c == '%':
                    stop = min(self.comment_end(i), b)
                    out.append(lock('COMMENT', i, stop)); i = stop
                elif c == '$' or self.text.startswith((r'\[', r'\('), i):
                    stop = self.math_end(i)
                    if stop > b:
                        raise SyntaxProblem('math crosses source unit boundary', i)
                    out.append(math(i, stop)); i = stop
                elif c == '{':
                    stop = self.argument_end(i)
                    inner = self.skip_space(i + 1)
                    declaration = COMMAND.match(self.text, inner)
                    name = declaration.group()[1:] if declaration else ''
                    scoped = name in {'it', 'bf'} or (
                        name == 'em' and self.policy.commands.get(name)
                        == 'preserve_scoped_declaration_translate_children')
                    if declaration and scoped:
                        role = {'it': 'TEXTIT', 'bf': 'TEXTBF', 'em': 'EMPH'}[name]
                        opening_end = declaration.end()
                        if self.text[opening_end:opening_end + 1].isspace():
                            opening_end += 1
                        out.append(lock(role + 'OPEN', i, opening_end))
                        out.append(walk(opening_end, stop - 1))
                        out.append(lock(role + 'CLOSE', stop - 1, stop))
                    else:
                        out.extend([lock('GROUPOPEN', i, i + 1), walk(i + 1, stop - 1), lock('GROUPCLOSE', stop - 1, stop)])
                    i = stop
                elif c == '\\':
                    environment = ENVIRONMENT.match(self.text, i)
                    if environment:
                        action, name = environment[1], environment[2]
                        if action == 'begin' and name in self.policy.math:
                            stop = self.environment_end(i); out.append(math(i, stop)); i = stop; continue
                        if action == 'begin' and name in self.policy.literal | self.policy.metadata:
                            stop = self.environment_end(i); out.append(lock('LOCKED', i, stop)); i = stop; continue
                        if name not in self.policy.body:
                            stop = self.environment_end(i) if action == 'begin' else environment.end()
                            issue('unknown-environment', i, stop, 'environment is not a supported translatable body')
                            out.append(lock('UNKNOWN', i, stop)); i = stop; continue
                        out.append(lock('STRUCT', i, environment.end())); i = environment.end()
                        if action == 'begin' and self.text[self.skip_space(i):self.skip_space(i) + 1] == '[':
                            opening = self.skip_space(i); stop = self.argument_end(opening)
                            out.extend([lock('ENVARGOPEN', i, opening + 1), walk(opening + 1, stop - 1), lock('ENVARGEND', stop - 1, stop)])
                            i = stop
                        continue
                    match = COMMAND.match(self.text, i)
                    if not match:
                        raise SyntaxProblem('incomplete command', i)
                    name, stop = match.group()[1:], match.end()
                    if name in self.policy.accents:
                        token = self.skip_space(stop)
                        stop = self.argument_end(token) if self.text[token:token + 1] == '{' else token + 1
                        if stop > b:
                            raise SyntaxProblem('incomplete text accent', i)
                        out.append(lock('ACCENT', i, stop))
                    elif name in {' ', '\t', '\r', '\n', ',', ';', ':', '!', '/', '\\', '%', '#', '$', '&', '_', '{', '}'}:
                        out.append(lock('SPACE' if name.isspace() else 'STRUCT', i, stop))
                    elif name in SCAFFOLD:
                        if name in {'bibliography', 'bibliographystyle'}:
                            stop, _ = self.command_arguments(i)
                        elif name == 'item' and self.text[self.skip_space(stop):self.skip_space(stop) + 1] == '[':
                            opening = self.skip_space(stop); stop = self.argument_end(opening)
                            out.extend([lock('ITEMOPEN', i, opening + 1), walk(opening + 1, stop - 1), lock('ITEMCLOSE', stop - 1, stop)])
                            i = stop; continue
                        out.append(lock('STRUCT', i, stop))
                    elif self.policy.commands.get(name) == 'locked':
                        stop, _ = self.command_arguments(i, optional=True)
                        out.append(lock('REF' if name in {'ref', 'eqref', 'pageref', 'cite'} else 'LOCKED', i, stop))
                    elif self.policy.commands.get(name) in {'translate_arguments', 'preserve_wrapper_translate_children', 'mixed'}:
                        stop, args = self.command_arguments(i, 2 if name == 'href' else 1)
                        opening, closing = args[-1]
                        role = {'footnote': 'FOOTNOTE', 'textit': 'TEXTIT', 'textbf': 'TEXTBF', 'emph': 'EMPH'}.get(name, 'TEXT')
                        out.extend([lock(role + 'OPEN', i, opening + 1), walk(opening + 1, closing - 1), lock(role + 'CLOSE', closing - 1, stop)])
                    elif self.policy.commands.get(name) == 'special_index_record':
                        stop, _ = self.command_arguments(i)
                        issue('index-record', i, stop, 'index entry needs the separate index-record translation contract')
                        out.append(lock('INDEX', i, stop))
                    else:
                        if name in {'verb', 'Verb'}:
                            delimiter = self.text[stop:stop + 1]
                            close = self.text.find(delimiter, stop + 1) if delimiter else -1
                            stop = close + 1 if close >= 0 else b
                        else:
                            while self.text[self.skip_space(stop):self.skip_space(stop) + 1] == '{':
                                stop = self.argument_end(self.skip_space(stop))
                        issue('unknown-command', i, stop, 'unknown command or unsupported scoped command: ' + name)
                        out.append(lock('UNKNOWN', i, stop))
                    i = stop
                elif c == '}':
                    raise SyntaxProblem('unexpected closing text group', i)
                elif c in '&_#^~':
                    out.append(lock('STRUCT', i, i + 1)); i += 1
                elif c in '<>':
                    out.append(lock('LITERAL', i, i + 1)); i += 1
                else:
                    stop = i + 1
                    while stop < b and self.text[stop] not in '%$\\{}&_#^~<>':
                        stop += 1
                    out.append(self.text[i:stop]); i = stop
            return ''.join(out)

        return walk(start, end), placeholders, diagnostics


def chapter_inventory(chapter: str, raw: bytes, commit: str, tags: dict[str, str],
                      policy: Policy, existing: dict[tuple[str, str], list[dict[str, Any]]] | None = None):
    text = raw.decode('utf-8')
    scanner = Scanner(text, policy)
    byte_offsets = array('Q', [0])
    for char in text:
        byte_offsets.append(byte_offsets[-1] + len(char.encode('utf-8')))
    newlines = [i for i, c in enumerate(text) if c == '\n']
    units, segments, diagnostics = [], [], []
    section = tags.get(chapter + '-section-phantom')
    previous_statement = None
    ordinals: collections.Counter[tuple[str | None, str]] = collections.Counter()

    def location(a: int, b: int):
        return {'file': chapter + '.tex', 'byte_start': byte_offsets[a], 'byte_end': byte_offsets[b],
                'line_start': bisect.bisect_left(newlines, a) + 1,
                'line_end': bisect.bisect_left(newlines, max(a, b - 1)) + 1,
                'fragment_hash': byte_hash(text[a:b])}

    def locked(a: int, b: int, kind: str, classifications=None):
        if a < b:
            segment = {'chapter': chapter, 'kind': kind, 'location': location(a, b), 'source': text[a:b]}
            if classifications:
                segment['math_text_classifications'] = classifications
            segments.append(segment)

    def emit(a: int, b: int, kind: str, owner: str | None, syntax: SyntaxProblem | None = None):
        if a >= b:
            return
        try:
            if syntax:
                raise syntax
            protected, placeholders, problems = scanner.protect(a, b)
            classifications = [{**{k: v for k, v in item.items() if k not in {'start', 'end'}},
                                'location': location(item['start'], item['end'])}
                               for item in scanner.math_text_classifications]
        except SyntaxProblem as exc:
            classifications = []
            scanner.math_text_regions = []
            protected, placeholders = '<UNKNOWN_0001>', {'UNKNOWN_0001': text[a:b]}
            problems = [{'kind': 'syntax', 'start': a, 'end': b, 'severity': 'BLOCKED',
                         'message': str(exc), 'source': text[a:b]}]
        natural = re.sub(r'<[A-Z][A-Z0-9]*_[0-9]{4}>', '', protected)
        if not WORD.search(natural) and not problems:
            locked(a, b, 'structure-or-math', classifications)
            return
        ordinals[(owner, kind)] += 1
        path = f'{kind}/{ordinals[(owner, kind)]:04d}'
        identifier = f'inventory:{chapter}:{owner or "untagged"}:{path}'
        if owner is None:
            problems.append({'kind': 'ownership', 'start': a, 'end': b, 'severity': 'BLOCKED',
                             'message': 'no unique locked permanent Tag owner; explicit scope mapping required',
                             'source': text[a:b]})
        from .math_text import bind_regions, nodes
        unit = stamp_unit_hashes(bind_regions({'schema_version': 1, 'unit_id': identifier,
            'parent_tag': section or 'UNASSIGNED', 'chapter': chapter, 'node_kind': kind,
            'risk_level': 'R3' if kind in STATEMENTS | {'proof'} else 'R1',
            'source_commit': commit, 'source_text': protected, 'source_status': 'CURRENT',
            'placeholders': placeholders, 'render': {'prefix': '', 'suffix': ''}}, scanner.math_text_regions))
        assert source_tex(unit) == text[a:b], 'extraction roundtrip defect'
        natural_classifications = []
        for region in unit.get('math_text_regions', []):
            stream = nodes(region['source'])
            for slot in region['slots']:
                node = next(n for n in stream if n.get('command') == slot['command'] and
                            len(region['source'][:n['parameter_start']].encode('utf-8')) == slot['slot_byte_span']['start'])
                first = byte_offsets[a] + region['source_byte_span']['start'] + len(region['source'][:node['start']].encode('utf-8'))
                last = byte_offsets[a] + region['source_byte_span']['start'] + len(region['source'][:node['end']].encode('utf-8'))
                natural_classifications.append({'source': region['source'][node['start']:node['end']],
                    'literal': slot['source'], 'command': slot['command'], 'policy_entry': slot['policy_entry'],
                    'classification_witness': slot['classification_witness'],
                    'location': location(bisect.bisect_left(byte_offsets, first), bisect.bisect_left(byte_offsets, last))})
        matches = (existing or {}).get((chapter, byte_hash(text[a:b])), [])
        matches = [u['unit_id'] for u in matches if u.get('_owner') == owner]
        record = {'inventory_id': identifier, 'source_commit': commit, 'owner_tag': owner,
                  'parent_tag': section, 'semantic_path': path, 'location': location(a, b),
                  'state': 'BLOCKED' if problems else 'READY', 'word_count': len(WORD.findall(natural)),
                  'existing_unit_id': matches[0] if len(matches) == 1 else None,
                  'unit': unit, 'diagnostic_count': len(problems),
                  'math_text_classifications': classifications,
                  'natural_math_text_classifications': natural_classifications}
        units.append(record)
        segments.append({'chapter': chapter, 'kind': 'unit', 'location': location(a, b), 'inventory_id': identifier})
        for problem in problems:
            start, end = problem.pop('start'), problem.pop('end')
            diagnostics.append({**problem, 'inventory_id': identifier, 'chapter': chapter,
                                'owner_tag': owner, 'location': location(start, end)})

    def own_label(offset: int):
        offset = scanner.skip_space(offset)
        if text[offset:offset + 1] == '[':
            offset = scanner.skip_space(scanner.argument_end(offset))
        label = re.match(r'\\label\{([^{}\n]+)\}', text[offset:])
        return tags.get(chapter + '-' + label[1]) if label else None

    # Locate the real opening from the permitted preamble, not a global regex:
    # coding.tex contains literal document examples in verbatim environments.
    opening = scanner.skip_space(0)
    if text.startswith(r'\input{preamble}', opening):
        opening = scanner.skip_space(opening + len(r'\input{preamble}'))
    document = ENVIRONMENT.match(text, opening)
    if document is None or document.group() != r'\begin{document}':
        emit(0, len(text), 'document', None, SyntaxProblem('no unique document boundary', 0))
        if not raw:
            diagnostics.append({'kind': 'syntax', 'chapter': chapter, 'severity': 'BLOCKED',
                                'message': 'empty source document', 'source': '', 'location': location(0, 0)})
    else:
        cursor = document.end()
        closed_document = False
        locked(0, cursor, 'preamble')
        while cursor < len(text):
            start = scanner.skip_space(cursor)
            locked(cursor, start, 'whitespace-or-comments')
            if start >= len(text):
                break
            try:
                env = ENVIRONMENT.match(text, start)
                command = COMMAND.match(text, start)
                if env and env[1] == 'end' and env[2] == 'document':
                    closed_document = True
                    locked(start, len(text), 'document-footer')
                    footer = scanner.skip_space(env.end())
                    if text.startswith(r'\input{chapters}', footer):
                        footer = scanner.skip_space(footer + len(r'\input{chapters}'))
                    if footer < len(text):
                        diagnostics.append({'kind': 'document-footer', 'chapter': chapter, 'severity': 'BLOCKED',
                            'message': 'unsupported content after the document closing',
                            'source': text[footer:], 'location': location(footer, len(text))})
                    break
                if env and env[1] == 'begin':
                    end = scanner.environment_end(start)
                    kind = env[2]
                    if kind in policy.literal | policy.metadata:
                        locked(start, end, kind); previous_statement = None
                    else:
                        owner = own_label(env.end()) if kind in STATEMENTS else previous_statement if kind == 'proof' else section
                        emit(start, end, kind, owner)
                        previous_statement = owner if kind in STATEMENTS | {'proof'} else None
                    cursor = end
                    continue
                if command and command.group()[1:] in {'title', 'section', 'subsection', 'subsubsection'}:
                    name = command.group()[1:]
                    end, _ = scanner.command_arguments(start)
                    tail = scanner.skip_space(end)
                    label = re.match(r'\\label\{([^{}\n]+)\}', text[tail:])
                    owner = tags.get(chapter + '-' + label[1]) if label else None
                    if name == 'title':
                        owner = tags.get(chapter + '-section-phantom')
                    if label:
                        end = tail + len(label.group())
                    if name == 'section':
                        section = owner
                    emit(start, end, name + '_title', owner)
                    previous_statement = None; cursor = end
                    continue
                # Infrastructure is inventoried separately, never sent as prose.
                if command and command.group()[1:] in {'maketitle', 'phantomsection', 'tableofcontents', 'bibliography', 'bibliographystyle', 'input', 'label'}:
                    name = command.group()[1:]; end = command.end()
                    if name in {'bibliography', 'bibliographystyle', 'input', 'label'}:
                        end, _ = scanner.command_arguments(start)
                    if name == 'input' and text[start:end] != r'\input{chapters}':
                        emit(start, end, 'external-input', section)
                    else:
                        locked(start, end, 'document-infrastructure')
                    cursor = end; previous_statement = None
                    continue
                i = start
                while i < len(text):
                    if text[i] == '%':
                        i = scanner.comment_end(i)
                    elif text[i] == '$' or text.startswith((r'\[', r'\('), i):
                        i = scanner.math_end(i)
                    elif text[i] == '{':
                        i = scanner.argument_end(i)
                    elif text[i] == '\\':
                        env = ENVIRONMENT.match(text, i)
                        cmd = COMMAND.match(text, i)
                        if env or (cmd and cmd.group()[1:] in {'title', 'section', 'subsection', 'subsubsection'}):
                            if i > start:
                                break
                            raise SyntaxProblem('unexpected structural closing', i)
                        if not cmd:
                            raise SyntaxProblem('incomplete command', i)
                        i = cmd.end()
                        # Consume complete arguments, including multiline footnotes;
                        # paragraph separators inside them cannot split the wrapper.
                        while text[scanner.skip_space(i):scanner.skip_space(i) + 1] in {'{', '['}:
                            i = scanner.argument_end(scanner.skip_space(i))
                    elif text[i] == '\n' and re.match(r'\n[ \t\r]*\n', text[i:]):
                        break
                    else:
                        i += 1
                if i <= start:
                    raise SyntaxProblem('source scanner made no progress', start)
                emit(start, i, 'paragraph', section)
                cursor = i; previous_statement = None
            except SyntaxProblem as exc:
                # Keep every remaining byte and its cause, never silently drop a
                # malformed tail or claim a partially scanned document is READY.
                emit(start, len(text), 'unsupported-tail', section, exc)
                break
        if not closed_document and not any(d['kind'] == 'syntax' for d in diagnostics):
            diagnostics.append({'kind': 'syntax', 'chapter': chapter, 'severity': 'BLOCKED',
                'message': 'missing document closing', 'source': text,
                'location': location(0, len(text))})
            for row in units:
                row['state'] = 'BLOCKED'
                row['diagnostic_count'] += 1
    by_id = {row['inventory_id']: row['unit'] for row in units}
    restored = ''.join(source_tex(by_id[s['inventory_id']]) if s['kind'] == 'unit' else s['source'] for s in segments)
    if restored.encode('utf-8') != raw:
        raise RecordError(chapter + ': full Git byte roundtrip failed')
    offset = 0
    for segment in segments:
        if segment['location']['byte_start'] != offset:
            raise RecordError(chapter + ': source byte coverage has a gap or overlap')
        offset = segment['location']['byte_end']
    if offset != len(raw):
        raise RecordError(chapter + ': source byte coverage is incomplete')
    return units, segments, diagnostics


def _current_index(root: Path, tags: dict[str, str]):
    from .source_integrity import permanent_tag_mapping
    result: dict[tuple[str, str], list[dict[str, Any]]] = collections.defaultdict(list)
    snapshots = []
    for path in sorted((root / 'translation-data/units').glob('*.jsonl')):
        raw = path.read_bytes()
        snapshots.append([path.relative_to(root).as_posix(), byte_hash(raw)])
        units = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
        mapping = permanent_tag_mapping(units, tags)
        for unit in units:
            mapped = mapping[unit['unit_id']]
            tag = re.match(r'tag:([0-9A-Z]+):', mapped)
            result[(unit['chapter'], byte_hash(source_tex(unit)))].append({**unit, '_owner': tag[1] if tag else None})
    return result, byte_hash(json.dumps(snapshots, ensure_ascii=False, separators=(',', ':')))


def resolve_natural_math_witnesses(policy: Policy, english: LockedEnglish) -> None:
    """Validate source anchors independently of natural-text acceptance/cache."""
    if not policy.math_text_rules:
        return
    from .math_text import find_slots, restore
    legacy = Policy(policy.raw, natural_text_enabled=False)
    tree = subprocess.run(['git', '-C', str(english.harvest), 'ls-tree', '--name-only', english.commit],
                          capture_output=True, text=True, check=True).stdout.splitlines()
    documents = {}
    verified = {}
    for key, rule in policy.math_text_rules.items():
        label = rule['source_label']
        owner = english.tags.get(label)
        files = [name for name in tree if name.endswith('.tex') and label.startswith(name[:-4] + '-')]
        if not owner or sum(t == owner for t in english.tags.values()) != 1 or not files:
            raise RecordError('natural math-text witness has no unique real Tag/file: ' + key)
        file = max(files, key=len)
        chapter = file[:-4]
        if file not in documents:
            raw = _git_bytes(english.harvest, english.commit, file)
            documents[file] = chapter_inventory(chapter, raw, english.commit, english.tags, legacy)[0]
        rows = documents[file]
        anchors = [r for r in rows if r['owner_tag'] == owner and
                   (r['unit']['node_kind'] in STATEMENTS or r['unit']['node_kind'] == 'section_title')]
        if len(anchors) != 1:
            raise RecordError('natural math-text witness lacks its unique real labelled semantic anchor: ' + key)
        kind, ordinal = rule['witness_kind'], rule['witness_ordinal']
        if kind == 'section':
            if anchors[0]['unit']['node_kind'] != 'section_title' or ordinal != 1:
                raise RecordError('natural math-text Section witness has incorrect kind/ordinal')
            selected = [r for r in rows if r['parent_tag'] == owner]
        else:
            selected = [r for r in rows if r['owner_tag'] == owner and
                        r['semantic_path'] == f'{kind}/{ordinal:04d}']
            if len(selected) != 1 or anchors[0]['unit']['node_kind'] not in STATEMENTS:
                raise RecordError('natural math-text statement/proof witness has incorrect kind/ordinal')
        matches = []
        for row in selected:
            unit = row['unit']
            for name in re.findall(r'<(MATH_[0-9]{4})>', unit['source_text']):
                math = unit['placeholders'][name]
                try:
                    slots = find_slots(math, {key: rule})
                except ValueError:
                    slots = []
                prefix = unit['render']['prefix'] + restore(unit, unit['source_text'].partition('<' + name + '>')[0])
                start = row['location']['byte_start'] + len(prefix.encode('utf-8'))
                for slot in slots:
                    first = start + len(math[:slot['start']].encode('utf-8'))
                    last = start + len(math[:slot['end']].encode('utf-8'))
                    matches.append({'container_byte_span': {'start': row['location']['byte_start'], 'end': row['location']['byte_end']},
                        'container_hash': row['location']['fragment_hash'],
                        'command_byte_span': {'start': first, 'end': last},
                        'command_hash': byte_hash(math[slot['start']:slot['end']])})
        if not matches:
            raise RecordError('natural math-text rule has no real syntax/literal witness: ' + key)
        verified[key] = {'source_commit': english.commit, 'file': file, 'owner_tag': owner,
                         'owner_label': label, 'kind': kind, 'ordinal': ordinal, 'matches': matches}
    policy.math_text_witnesses = verified


def build_inventory(root: Path, harvest: Path, chapters: list[str] | None = None):
    english = LockedEnglish(root, harvest)
    policy_raw = (root / 'config/macro-policy.yml').read_bytes()
    policy = Policy(policy_raw.decode('utf-8'))
    resolve_natural_math_witnesses(policy, english)
    manifest_raw = _git_bytes(harvest, english.commit, 'chapters.tex')
    listed = manifest_chapters(manifest_raw.decode('utf-8'))
    if chapters:
        unknown = set(chapters) - {name for name, _ in listed}
        if unknown or len(chapters) != len(set(chapters)):
            raise RecordError('unknown or duplicate chapter selector: ' + ', '.join(sorted(unknown)))
        listed = [(name, title) for name, title in listed if name in chapters]
    current, current_hash = _current_index(root, english.tags)
    units, segments, diagnostics, summaries = [], [], [], []
    # Missing a blob is different from a Git access failure. Establish the tree
    # once, so errors cannot be falsely described as generated/missing chapters.
    tree = subprocess.run(['git', '-C', str(harvest), 'ls-tree', '--name-only', english.commit], capture_output=True, text=True)
    if tree.returncode:
        raise RecordError('locked English Git tree unavailable')
    paths = set(tree.stdout.splitlines())
    for chapter, title in listed:
        if chapter + '.tex' not in paths:
            summaries.append({'chapter': chapter, 'title': title, 'state': 'SOURCE_UNAVAILABLE',
                              'reason': 'no independent TeX blob in locked Git tree'})
            diagnostics.append({'kind': 'source-unavailable', 'chapter': chapter, 'severity': 'BLOCKED',
                                'message': 'no independent TeX blob in locked Git tree'})
            continue
        raw = _git_bytes(harvest, english.commit, chapter + '.tex')
        rows, parts, problems = chapter_inventory(chapter, raw, english.commit, english.tags, policy, current)
        units.extend(rows); segments.extend(parts); diagnostics.extend(problems)
        summaries.append({'chapter': chapter, 'title': title, 'state': 'INVENTORIED',
                          'source_hash': byte_hash(raw), 'source_bytes': len(raw),
                          'unit_count': len(rows), 'ready': sum(u['state'] == 'READY' for u in rows),
                          'blocked': sum(u['state'] == 'BLOCKED' for u in rows),
                          'diagnostics': len(problems), 'roundtrip': 'BYTE_EXACT',
                          'classified_math_text': sum(len(r.get('math_text_classifications', []))
                                                      for r in [*rows, *parts]),
                          'natural_math_text_slots': sum(len(r['natural_math_text_classifications']) for r in rows),
                          'natural_math_text_regions': sum(len(r['unit'].get('math_text_regions', [])) for r in rows)})
    manifest = {'schema_version': 1, 'extractor_version': VERSION, 'source_commit': english.commit,
                'macro_policy_hash': byte_hash(policy_raw), 'chapter_manifest_hash': byte_hash(manifest_raw),
                'chapter_count': len(summaries), 'chapters': summaries, 'unit_count': len(units),
                'ready': sum(u['state'] == 'READY' for u in units),
                'blocked': sum(u['state'] == 'BLOCKED' for u in units), 'diagnostic_count': len(diagnostics),
                'source_unavailable': [s['chapter'] for s in summaries if s['state'] == 'SOURCE_UNAVAILABLE'],
                'diagnostics_by_kind': dict(sorted(collections.Counter(p['kind'] for p in diagnostics).items())),
                'classified_math_text': sum(s.get('classified_math_text', 0) for s in summaries),
                'natural_math_text_slots': sum(s.get('natural_math_text_slots', 0) for s in summaries),
                'natural_math_text_regions': sum(s.get('natural_math_text_regions', 0) for s in summaries),
                'roundtrip_files': sum(s['state'] == 'INVENTORIED' for s in summaries),
                'translation_ready': not diagnostics, 'adopted': False}
    manifest['current_units_hash'] = current_hash
    current_english = LockedEnglish(root, harvest)
    if (current_english.commit != english.commit or current_english.tags != english.tags
            or policy_raw != (root / 'config/macro-policy.yml').read_bytes()
            or _current_index(root, english.tags)[1] != current_hash):
        raise RecordError('macro policy/current facts changed during source extraction')
    return manifest, units, segments, diagnostics


def write_inventory(root: Path, harvest: Path, output: Path, *, chapters: list[str] | None = None, check: bool = False):
    if any(p.is_symlink() for p in [output, *output.parents]
           if p.absolute().is_relative_to(root.absolute())):
        raise RecordError('extraction destination must not be a symlink')
    root, output = root.resolve(), output.resolve()
    allowed = any(output.is_relative_to(root / name) and output != root / name for name in ('source-ir', 'build'))
    if not allowed or output.is_symlink():
        raise RecordError('extraction output must be a dedicated ignored source-ir/ or build/ subdirectory')
    if output.exists() and not check:
        marker = output / 'manifest.json'
        previous = json.loads(marker.read_text(encoding='utf-8')) if marker.is_file() and not marker.is_symlink() else {}
        if (not output.is_dir() or not marker.is_file() or marker.is_symlink() or not isinstance(previous, dict)
                or previous.get('schema_version') != 1
                or previous.get('extractor_version') not in {VERSION, 'source-extraction-v1', 'source-extraction-v2'}):
            raise RecordError('refusing to replace a directory not owned by the source extractor')
        if {p.name for p in output.iterdir()} != {'units.jsonl', 'segments.jsonl', 'diagnostics.jsonl', 'report.md', 'manifest.json'}:
            raise RecordError('refusing to replace an inventory containing unrelated files')
        if any(p.is_symlink() for p in output.iterdir()):
            raise RecordError('refusing to replace an inventory containing symlinks')
        files = previous.get('files', {})
        if (not isinstance(files, dict) or set(files) != {'units.jsonl', 'segments.jsonl', 'diagnostics.jsonl', 'report.md'}
                or any(byte_hash((output / name).read_bytes()) != expected for name, expected in files.items())):
            raise RecordError('refusing to regenerate an invalid source inventory')
    manifest, units, segments, diagnostics = build_inventory(root, harvest, chapters)

    def jsonl(rows):
        return ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for row in rows).encode('utf-8')

    payloads = {'units.jsonl': jsonl(units), 'segments.jsonl': jsonl(segments), 'diagnostics.jsonl': jsonl(diagnostics)}
    lines = ['# 全库来源库存', '', f"锁定英文：`{manifest['source_commit']}`；抽取器：`{VERSION}`。", '',
             f"{manifest['chapter_count']}章；{manifest['roundtrip_files']}个Git文件逐字回放通过。",
             f"提议单元{manifest['unit_count']}：READY {manifest['ready']}，BLOCKED {manifest['blocked']}；诊断{manifest['diagnostic_count']}。", '',
             f"明确数学记号分类{manifest['classified_math_text']}次；原公式字节保持不变。", '',
             f"已核实数学自然文字{manifest['natural_math_text_slots']}个slot、{manifest['natural_math_text_regions']}个完整region；其余数学字节锁定。", '',
             'READY仅表示该来源片段被已知语法抽取，不是事实采用、模型译文、人工审校或发布批准。', '',
             '| Chapter | State | Units | Ready | Blocked |', '| --- | --- | ---: | ---: | ---: |']
    for chapter in manifest['chapters']:
        lines.append(f"| {chapter['chapter']} | {chapter['state']} | {chapter.get('unit_count', 0)} | {chapter.get('ready', 0)} | {chapter.get('blocked', 0)} |")
    lines.extend(['', '诊断分类：', ''] + [f'- {kind}: {count}' for kind, count in manifest['diagnostics_by_kind'].items()])
    payloads['report.md'] = ('\n'.join(lines) + '\n').encode('utf-8')
    manifest['files'] = {name: byte_hash(raw) for name, raw in payloads.items()}
    payloads['manifest.json'] = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    if check:
        if not output.is_dir() or {p.name for p in output.iterdir()} != set(payloads):
            raise RecordError('source inventory files missing, extra or stale')
        for name, raw in payloads.items():
            if (output / name).is_symlink() or (output / name).read_bytes() != raw:
                raise RecordError('source inventory out of date: ' + name)
        return manifest
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.extract-', dir=output.parent))
    backup = None
    try:
        for name, raw in payloads.items():
            (temporary / name).write_bytes(raw)
        current = LockedEnglish(root, harvest)
        if (current.commit != manifest['source_commit']
                or byte_hash((root / 'config/macro-policy.yml').read_bytes()) != manifest['macro_policy_hash']
                or _current_index(root, current.tags)[1] != manifest['current_units_hash']):
            raise RecordError('locked source, macro policy or facts changed before installing inventory')
        if output.exists():
            if not output.is_dir():
                raise RecordError('extraction destination is not a directory')
            backup = Path(tempfile.mkdtemp(prefix='.extract-backup-', dir=output.parent))
            backup.rmdir(); output.rename(backup)
        try:
            temporary.rename(output)
        except OSError:
            if backup is not None:
                backup.rename(output); backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup); backup = None
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return manifest
