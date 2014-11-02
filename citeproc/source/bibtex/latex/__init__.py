
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *


import unicodedata

from collections import namedtuple

from .macro import MACROS


__all__ = ['parse_latex', 'substitute_ligatures']


def parse_latex(string, macros={}):
    output = ''
    tokens = Tokenizer(string)
    for token in tokens:
        result = dispatch(token, tokens, macros, top_level=False)
        if result is None:
            assert token.type in (CHARACTER, WHITESPACE)
            result = token.value
        output += result
    return substitute_ligatures(output)


Token = namedtuple('Token', ['type', 'value'])


TOGGLE_MATH = 'TOGGLE-MATH'
WHITESPACE = 'WHITESPACE'
CLOSE_SCOPE = 'CLOSE-SCOPE'
OPEN_SCOPE = 'OPEN-SCOPE'
START_MACRO = 'START-MACRO'
CHARACTER = 'CHARACTER'


class Tokenizer(object):
    def __init__(self, string):
        self._tokens = self.tokenize(string)
        self._next_token = None

    @staticmethod
    def tokenize(input_string):
        for char in input_string:
            if char == '\\':
                yield Token(START_MACRO, char)
            elif char == '{':
                yield Token(OPEN_SCOPE, char)
            elif char == '}':
                yield Token(CLOSE_SCOPE, char)
            elif char in ' \t\n':
                yield Token(WHITESPACE, char)
            elif char == '$':
                yield Token(TOGGLE_MATH, char)
            else:
                yield Token(CHARACTER, char)

    def __iter__(self):
        return self

    def __next__(self):
        if self._next_token:
            token = self._next_token
            self._next_token = None
        else:
            token = next(self._tokens)
        return token

    next = __next__

    def peek(self):
        if not self._next_token:
            self._next_token = next(self._tokens)
        return self._next_token


def dispatch(token, tokens, macros, top_level=False):
    if token.type == OPEN_SCOPE:
        return handle_scope(tokens, macros, top_level)
    elif token.type == START_MACRO:
        return handle_macro(tokens, macros)
    elif token.type == TOGGLE_MATH:
        return handle_math(tokens)


def handle_scope(tokens, macros, top_level):
    output = ''
    for token in tokens:
        if token.type == CLOSE_SCOPE:
            break
        result = dispatch(token, tokens, macros) or token.value
        output += result
    if top_level:
        output = '<' + output + '>'
    return output


def parse_argument(tokens, macros):
    for token in tokens:
        if token.type != WHITESPACE:
            break
    return dispatch(token, tokens, macros) or token.value


def handle_macro(tokens, macros):
    token = next(tokens)
    if token.type == WHITESPACE:
        return ' '
    assert token.type in (CHARACTER, TOGGLE_MATH)
    name = token.value

    if name.isalpha():
        while tokens.peek().type == CHARACTER and tokens.peek().value.isalpha():
            name += next(tokens).value
        while tokens.peek().type == WHITESPACE:
            next(tokens)

    try:
        macro = MACROS[name]
        args = [parse_argument(tokens, macros) for _ in range(macro.num_args)]
        return macro.expand(args)
    except KeyError:
        num_args, command_body = macros[name]
        args = [parse_argument(tokens, macros) for _ in range(num_args)]
        result = ''
        for arg_index in command_body:
            result += args[arg_index - 1]
        return result


def handle_math(tokens):
    output = ''
    for token in tokens:
        if token.type == START_MACRO:
            output += token.value
            token = next(tokens)
        elif token.type == TOGGLE_MATH:
            break
        output += token.value
    return '$' + output + '$'


def substitute_ligatures(string):
    for chars, ligature in CM_LIGATURES.items():
        string = string.replace(chars, unicodedata.lookup(ligature))
    return string


CM_LIGATURES = {"--": 'EN DASH',
                "---": 'EM DASH',
                "''": 'RIGHT DOUBLE QUOTATION MARK',
                "``": 'LEFT DOUBLE QUOTATION MARK',
                "!`": 'INVERTED EXCLAMATION MARK',
                "?`": 'INVERTED QUESTION MARK',
                ",,": 'DOUBLE LOW-9 QUOTATION MARK',
                "<<": 'LEFT-POINTING DOUBLE ANGLE QUOTATION MARK',
                ">>": 'RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK',
}
