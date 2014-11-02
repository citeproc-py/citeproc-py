
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *


import unicodedata


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
          'dots': SymbolMacro('HORIZONTAL ELLIPSIS'),
          'P': SymbolMacro('PILCROW SIGN'),
          'S': SymbolMacro('SECTION SIGN'),
          'copyright': SymbolMacro('COPYRIGHT SIGN'),
          'pounds': SymbolMacro('POUND SIGN'),

          'textasciicircum': EscapeMacro('^'),
          'textasciitilde': EscapeMacro('~'),
          'textasteriskcentered': EscapeMacro('*'),
          'textbackslash': EscapeMacro('\\'),
          'textbar': EscapeMacro('|'),
          'textbraceleft': EscapeMacro('{'),
          'textbraceright': EscapeMacro('}'),
          'textbullet': SymbolMacro('BULLET'),
          'textcopyright': SymbolMacro('COPYRIGHT SIGN'),
          'textdagger': SymbolMacro('DAGGER'),
          'textdaggerdbl': SymbolMacro('DOUBLE DAGGER'),
          'textdollar': EscapeMacro('$'),
          'textellipsis': SymbolMacro('HORIZONTAL ELLIPSIS'),
          'textemdash': SymbolMacro('EM DASH'),
          'textendash': SymbolMacro('EN DASH'),
          'textexclamdown': SymbolMacro('INVERTED EXCLAMATION MARK'),
          'textgreater': EscapeMacro('>'),
          'textless': EscapeMacro('<'),
          'textordfeminine': SymbolMacro('FEMININE ORDINAL INDICATOR'),
          'textordmasculine': SymbolMacro('MASCULINE ORDINAL INDICATOR'),
          'textparagraph': SymbolMacro('PILCROW SIGN'),
          'textperiodcentered': SymbolMacro('MIDDLE DOT'),
          'textquestiondown': SymbolMacro('INVERTED QUESTION MARK'),
          'textquotedblleft': SymbolMacro('LEFT DOUBLE QUOTATION MARK'),
          'textquotedblright': SymbolMacro('RIGHT DOUBLE QUOTATION MARK'),
          'textquoteleft': SymbolMacro('LEFT SINGLE QUOTATION MARK'),
          'textquoteright': SymbolMacro('RIGHT SINGLE QUOTATION MARK'),
          'textregistered': SymbolMacro('REGISTERED SIGN'),
          'textsection': SymbolMacro('SECTION SIGN'),
          'textsterling': SymbolMacro('POUND SIGN'),
          'texttrademark': SymbolMacro('TRADE MARK SIGN'),
          'textunderscore': EscapeMacro('_'),
          'textvisiblespace': SymbolMacro('OPEN BOX'),

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
