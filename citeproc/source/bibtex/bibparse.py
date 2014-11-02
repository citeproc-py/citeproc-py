
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *


import unicodedata

from collections import namedtuple


# http://maverick.inria.fr/~Xavier.Decoret/resources/xdkbibtex/bibtex_summary.html
# http://www.lsv.ens-cachan.fr/~markey/bibla.php?lang=en

class BibTeXEntry(dict):
    def __init__(self, document_type, attributes):
        super(BibTeXEntry, self).__init__(attributes)
        self.document_type = document_type


class BibTeXParser(dict):
    standard_variables = {'jan': 'January',
                          'feb': 'February',
                          'mar': 'March',
                          'apr': 'April',
                          'may': 'May',
                          'jun': 'June',
                          'jul': 'July',
                          'aug': 'August',
                          'sep': 'September',
                          'oct': 'October',
                          'nov': 'November',
                          'dec': 'December'}

    def __init__(self, file_or_filename):
        try:
            self.file = open(file_or_filename, 'rt', encoding='ascii')
        except TypeError:
            self.file = file_or_filename
        self.variables = {}
        self._macros = {}
        self._preamble = ''
        self._parse(self.file)
        self.file.close()

    def _parse(self, file):
        while True:
            try:
                entry = self._parse_entry(file)
                if entry is not None:
                    entry_type, key, attributes = entry
                    self[key] = BibTeXEntry(entry_type, attributes)
            except EOFError:
                break
        self._parse_preamble(self._preamble)
        for key, entry in self.items():
            for attribute, value in entry.items():
                if isinstance(value, str):
                    expanded = self._expand_macros(value)
                    entry[attribute] = self._substitute_ligatures(expanded)

    def _parse_entry(self, file):
        while True:
            char = file.read(1)
            if char == '@':
                break
            elif char == '':
                raise EOFError
        entry_type = ''
        while True:
            char = file.read(1)
            if char in '{(':
                sentinel = '}' if char == '{' else ')'
                break
            entry_type += char
            if entry_type.lower().startswith('comment'):
                self._jump_to_next_line(file)
                return None
        entry_type = entry_type.strip().lower()
        if entry_type == 'string':
            name = self._parse_name(file)
            value = self._parse_value(file)
            self.variables[name] = value
            assert self._eat_whitespace(file) == sentinel
            return None
        elif entry_type == 'preamble':
            self._preamble += self._parse_value(file, False)
            assert self._eat_whitespace(file) == sentinel
            return None
        key = self._parse_key(file)
        entry = {}
        while True:
            name = self._parse_name(file)
            value = self._parse_value(file)
            entry[name] = value
            char = self._eat_whitespace(file)
            if char != ',':
                if char != sentinel:
                    assert char in ' \t\n\r'
                    assert self._eat_whitespace(file) == sentinel
                break
            else:
                restore_point = file.tell()
                if self._eat_whitespace(file) == sentinel:
                    break
                file.seek(restore_point)
        return entry_type.strip().lower(), key, entry

    def _parse_key(self, file):
        key = ''
        char = file.read(1)
        while char != ',':
            key += char
            char = file.read(1)
        return key.strip().lower()

    def _parse_name(self, file):
        name = ''
        char = self._eat_whitespace(file)
        while True:
            if char == '=':
                break
            name += char
            char = file.read(1)
        return name.strip().lower()

    def _parse_value(self, file, expand_macros=True):
        char = self._eat_whitespace(file)
        if char in '{"':
            value = self._parse_string(file, char, expand_macros)
        elif char.isalpha():
            value = self._parse_variable(file, char)
        else:
            value = self._parse_integer(file, char)

        restore_position = file.tell()
        char = self._eat_whitespace(file)
        if char == '#':
            value += self._parse_value(file)
        else:
            file.seek(restore_position)
        return value

    def _parse_string(self, file, opening_character, expand_macros):
        closing_character = '"' if opening_character == '"' else '}'
        string = ''
        depth = 0
        while True:
            char = file.read(1)
            if char == '{':
                depth += 1
            elif depth == 0 and char == closing_character:
                break
            elif char == '}':
                depth -= 1
            string += char
        return string

    def _parse_variable(self, file, char):
        key = ''
        restore_point = file.tell()
        while char.isalnum() or char in '-_':
            key += char
            restore_point = file.tell()
            char = file.read(1)
        file.seek(restore_point)
        if key.lower() in self.variables:
            value = self.variables[key.lower()]
        else:
            value = self.standard_variables[key.lower()]
        return value

    def _parse_integer(self, file, char):
        integer = ''
        restore_point = file.tell()
        while char.isdigit():
            integer += char
            restore_point = file.tell()
            char = file.read(1)
        file.seek(restore_point)
        return int(integer)

    # TODO: rename to next_token?
    def _eat_whitespace(self, file):
        char = file.read(1)
        while char in ' \t\n\r':
            char = file.read(1)
        return char

    def _jump_to_next_line(self, file):
        char = ''
        while char != '\n':
            restore_point = file.tell()
            char = file.read(1)
        file.seek(restore_point)

    def _parse_preamble(self, preamble):
        self.macros = {}
        state = None
        for char in preamble:
            if state == 'MACRO':
                if char == '{':
                    state = 'MACRO-BODY'
                elif char in ' \t\n\r':
                    state = None
                else:
                    macro_name += char
            elif state == 'MACRO-BODY':
                if macro_name.lower() == 'newcommand':
                    state = 'NEWCOMMAND'
                    assert char == '\\'
                    command_name = ''
                else:
                    raise NotImplementedError
            elif state == 'NEWCOMMAND':
                if char == '}':
                    state = None
                    macro_name = None
                    state = 'NEWCOMMAND-ARGCOUNT'
                else:
                    command_name += char
            elif state == 'NEWCOMMAND-ARGCOUNT':
                if char == '[':
                    command_argcount = ''
                elif char == ']':
                    argument_index = None
                    state = 'NEWCOMMAND-BODY'
                else:
                    command_argcount += char
            elif state == 'NEWCOMMAND-BODY':
                if char == '{':
                    command_body = []
                elif char == '}':
                    if argument_index:
                        command_body.append(int(argument_index))
                    self.macros[command_name] = (int(command_argcount),
                                                 command_body)
                    state = None
                elif char == '#':
                    if argument_index:
                        command_body.append(int(argument_index))
                    argument_index = ''
                else:
                    argument_index += char
            elif char == '\\':
                state = 'MACRO'
                macro_name = ''

    def _expand_macros(self, string):
        Token = namedtuple('Token', ['type', 'value'])

        def tokenize(input_string):
            for char in input_string:
                if char == '\\':
                    yield Token('START-MACRO', char)
                elif char == '{':
                    yield Token('OPEN-SCOPE', char)
                elif char == '}':
                    yield Token('CLOSE-SCOPE', char)
                elif char in ' \t\n':
                    yield Token('WHITESPACE', char)
                elif char == '$':
                    yield Token('TOGGLE-MATH', char)
                else:
                    yield Token('CHAR', char)

        def peek(tokens):
            current_token = next(tokens)
            for next_token in tokens:
                yield current_token, next_token
                current_token = next_token
            yield current_token, (None, None)

        def dispatch(token, tokens, top_level=False):
            if token.type == 'OPEN-SCOPE':
                return handle_scope(tokens, top_level)
            elif token.type == 'START-MACRO':
                return handle_macro(tokens)
            elif token.type == 'TOGGLE-MATH':
                return handle_math(tokens)

        def handle_scope(tokens, top_level):
            output = ''
            for token, next_token in tokens:
                if token.type == 'CLOSE-SCOPE':
                    break
                result = dispatch(token, tokens) or token.value
                output += result
            if top_level:
                output = '<' + output + '>'
            return output

        def parse_argument(tokens):
            for token, next_token in tokens:
                if token.type != 'WHITESPACE':
                    break
            return dispatch(token, tokens) or token.value

        def handle_macro(tokens):
            token, next_token = next(tokens)
            if token.type == 'WHITESPACE':
                return ' '
            assert token.type in ('CHAR', 'TOGGLE-MATH')
            name = token.value
            if name.isalpha():
                while next_token.type == 'CHAR' and next_token.value.isalpha():
                    token, next_token = next(tokens)
                    name += token.value
                while next_token.type == 'WHITESPACE':
                    token, next_token = next(tokens)

            try:
                macro = MACROS[name]
                args = [parse_argument(tokens) for _ in range(macro.num_args)]
                return macro.expand(args)
            except KeyError:
                num_args, command_body = self.macros[name]
                args = [parse_argument(tokens) for _ in range(num_args)]
                result = ''
                for arg_index in command_body:
                    result += args[arg_index - 1]
                return result

        def handle_math(tokens):
            output = ''
            for token, next_token in tokens:
                if token.type == 'START-MACRO':
                    output += token.value
                    token, next_token = next(tokens)
                elif token.type == 'TOGGLE-MATH':
                    break
                output += token.value
            return '$' + output + '$'

        output = ''
        tokens = peek(tokenize(string))
        for token, next_token in tokens:
            result = dispatch(token, tokens, top_level=False)
            if result is None:
                assert token.type in ('CHAR', 'WHITESPACE')
                result = token.value
            output += result
        return output

    def _substitute_ligatures(self, string):
        for chars, ligature in CM_LIGATURES.items():
            string = string.replace(chars, unicodedata.lookup(ligature))
        return string

    def _split_name(self, name):
        pass


class Macro(object):
    def __init__(self, num_args, format_string):
        self.num_args = num_args
        self.format_string = format_string

    def expand(self, arguments):
        assert len(arguments) == self.num_args
        return self.format_string.format(*arguments)


class EscapeMacro(Macro):
    def __init__(self, escaped_character):
        super().__init__(0, escaped_character)


class SymbolMacro(Macro):
    def __init__(self, unicode_symbol_name):
        unicode_symbol = unicodedata.lookup(unicode_symbol_name)
        super().__init__(0, unicode_symbol)


class AccentMacro(Macro):
    def __init__(self, unicode_accent_name):
        unicode_accent = unicodedata.lookup('COMBINING ' + unicode_accent_name)
        super().__init__(1, '{0}' + unicode_accent)

    DOTTED_CHARS = {'ı': 'i',
                    'ȷ': 'j'}

    def expand(self, arguments):
        arguments = [self.DOTTED_CHARS.get(arg, arg) for arg in arguments]
        return unicodedata.normalize('NFC', super().expand(arguments))


MACROS = {# accents
          '`': AccentMacro('GRAVE ACCENT'),
          "'": AccentMacro('ACUTE ACCENT'),
          '^': AccentMacro('CIRCUMFLEX ACCENT'),
          '"': AccentMacro('DIAERESIS'),
          'H': AccentMacro('DOUBLE ACUTE ACCENT'),
          '~': AccentMacro('TILDE'),
          'c': AccentMacro('CEDILLA'),
          'k': AccentMacro('OGONEK'),
          '=': AccentMacro('MACRON'),
          'b': AccentMacro('MACRON BELOW'),
          '.': AccentMacro('DOT ABOVE'),
          'd': AccentMacro('DOT BELOW'),
          'r': AccentMacro('RING ABOVE'),
          'u': AccentMacro('BREVE'),
          'v': AccentMacro('CARON'),
          '|': AccentMacro('VERTICAL LINE ABOVE'),
          'h': AccentMacro('HOOK ABOVE'),
          'G': AccentMacro('DOUBLE GRAVE ACCENT'),
          'U': AccentMacro('DOUBLE VERTICAL LINE ABOVE'),

          # symbols
          'o': SymbolMacro('LATIN SMALL LETTER O WITH STROKE'),
          'O': SymbolMacro('LATIN CAPITAL LETTER O WITH STROKE'),
          'i': SymbolMacro('LATIN SMALL LETTER DOTLESS I'),
          'l': SymbolMacro('LATIN SMALL LETTER L WITH STROKE'),
          'L': SymbolMacro('LATIN CAPITAL LETTER L WITH STROKE'),
          'oe': SymbolMacro('LATIN SMALL LIGATURE OE'),
          'OE': SymbolMacro('LATIN CAPITAL LIGATURE OE'),
          'ae': SymbolMacro('LATIN SMALL LETTER AE'),
          'AE': SymbolMacro('LATIN CAPITAL LETTER AE'),
          'aa': SymbolMacro('LATIN SMALL LETTER A WITH RING ABOVE'),
          'AA': SymbolMacro('LATIN CAPITAL LETTER A WITH RING ABOVE'),
          'ss': SymbolMacro('LATIN SMALL LETTER SHARP S'),
          'dag': SymbolMacro('DAGGER'),
          'ddag': SymbolMacro('DOUBLE DAGGER'),
          'S': SymbolMacro('SECTION SIGN'),
          'copyright': SymbolMacro('COPYRIGHT SIGN'),
          'pounds': SymbolMacro('POUND SIGN'),

          'TeX': Macro(0, 'TeX'),
          't': Macro(1, '{0}\u0361{1}'),

          # escaped characters
          '&': EscapeMacro('&'),
          '$': EscapeMacro('$'),
          '{': EscapeMacro('{'),
          '}': EscapeMacro('}'),
          '%': EscapeMacro('%'),
          '#': EscapeMacro('#'),
          '_': EscapeMacro('_'),
}

            # '#$%&_{}' # special symbols

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


sample = r"""
@Article(py03,
     author = {Xavier D\'ecoret},
     title  = "PyBiTex",
     year   = 2003
)

@Article{key03,
  title = "A {bunch {of} braces {in}} title"
}

@Article{key01a,
  author = "Simon {"}the {saint"} Templar",
}

@Article{key01b,
  title = "The history of @ sign"
}

Some {{comments} with unbalanced braces
....and a "commented" entry...

Book{landru21,
  author =	 {Landru, Henri D\'esir\'e},
  title =	 {A hundred recipes for you wife},
  publisher =	 {Culinary Expert Series},
  year =	 1921
}

..some other comments..before a valid entry...

@Book{steward03a,
  author =	 { Martha Steward },
  title =	 {Cooking behind bars},
  publisher =	 {Culinary Expert Series},
  year =	 2003
}

...and finally an entry commented by the use of the special @Comment entry type.

@Comment{steward03b,
  author =	 {Martha Steward},
  title =	 {Cooking behind bars},
  publisher =	 {Culinary Expert Series},
  year =	 2003
}

@Comment{
  @Book{steward03c,
    author =	 {Martha Steward},
    title =	 {Cooking behind bars},
    publisher =	 {Culinary Expert Series},
    year =	 2003
  }
}

@String(mar = "march")

@Book{sweig42,
  Author =	 { Stefan Sweig },
  title =	 { The impossible book },
  publisher =	 { Dead Poet Society},
  year =	 1942,
  month =        mar
}


@String {firstname = "Xavier"}
@String {lastname  = "Decoret"}
@String {email      = firstname # "." # lastname # "@imag.fr"}

@preamble{ "\newcommand{\noopsort}[1]{} "
        # "\newcommand{\printfirst}[2]{#1} "
        # "\newcommand{\singleletter}[1]{#1} "
        # "\newcommand{\switchargs}[2]{#2#1} " }

@INBOOK{inbook-minimal,
   author = "Donald E. Knuth",
   title = "Fundamental Algorithms",
   publisher = "Addison-Wesley",
   year = "{\noopsort{1973b}}1973",
   chapter = "1.2",
}
"""


if __name__ == '__main__':
    from io import StringIO

    file = StringIO(sample)
    bib = BibTeXParser(file)
    for key, entry in bib.items():
        print(key)
        for name, value in entry.items():
            print('   {}: {}'.format(name, value))
    print(bib.macros)
    print(bib.variables)
