
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


class Symbol(Macro):
    def __init__(self, symbol):
        super().__init__(0, symbol)


class SymbolByName(Macro):
    def __init__(self, unicode_symbol_name):
        unicode_symbol = unicodedata.lookup(unicode_symbol_name)
        super().__init__(0, unicode_symbol)


class Combining(Macro):
    def __init__(self, unicode_accent_name):
        unicode_accent = unicodedata.lookup('COMBINING ' + unicode_accent_name)
        super().__init__(1, '{0}' + unicode_accent)

    DOTTED_CHARS = {'ı': 'i',
                    'ȷ': 'j'}

    def expand(self, arguments):
        assert len(arguments) == self.num_args
        accented, rest = arguments[0][0], arguments[0][1:]
        accented = self.DOTTED_CHARS.get(accented, accented)
        return unicodedata.normalize('NFC', super().expand([accented])) + rest


MACROS = {
    # accents
    '`': Combining('GRAVE ACCENT'),
    "'": Combining('ACUTE ACCENT'),
    '^': Combining('CIRCUMFLEX ACCENT'),
    '"': Combining('DIAERESIS'),
    'H': Combining('DOUBLE ACUTE ACCENT'),
    '~': Combining('TILDE'),
    'c': Combining('CEDILLA'),
    'k': Combining('OGONEK'),
    '=': Combining('MACRON'),
    'b': Combining('MACRON BELOW'),
    '.': Combining('DOT ABOVE'),
    'd': Combining('DOT BELOW'),
    'r': Combining('RING ABOVE'),
    'u': Combining('BREVE'),
    'v': Combining('CARON'),
    '|': Combining('VERTICAL LINE ABOVE'),
    'h': Combining('HOOK ABOVE'),
    'G': Combining('DOUBLE GRAVE ACCENT'),
    'U': Combining('DOUBLE VERTICAL LINE ABOVE'),
    't': Combining('DOUBLE INVERTED BREVE'),
    'textcircled': Combining('ENCLOSING CIRCLE'),

    # symbols
    'o': SymbolByName('LATIN SMALL LETTER O WITH STROKE'),
    'O': SymbolByName('LATIN CAPITAL LETTER O WITH STROKE'),
    'i': SymbolByName('LATIN SMALL LETTER DOTLESS I'),
    'l': SymbolByName('LATIN SMALL LETTER L WITH STROKE'),
    'L': SymbolByName('LATIN CAPITAL LETTER L WITH STROKE'),
    'oe': SymbolByName('LATIN SMALL LIGATURE OE'),
    'OE': SymbolByName('LATIN CAPITAL LIGATURE OE'),
    'ae': SymbolByName('LATIN SMALL LETTER AE'),
    'AE': SymbolByName('LATIN CAPITAL LETTER AE'),
    'aa': SymbolByName('LATIN SMALL LETTER A WITH RING ABOVE'),
    'AA': SymbolByName('LATIN CAPITAL LETTER A WITH RING ABOVE'),
    'ss': SymbolByName('LATIN SMALL LETTER SHARP S'),
    'dh': SymbolByName('LATIN SMALL LETTER ETH'),
    'DH': SymbolByName('LATIN CAPITAL LETTER ETH'),
    'dj': SymbolByName('LATIN SMALL LETTER D WITH STROKE'),
    'DJ': SymbolByName('LATIN CAPITAL LETTER D WITH STROKE'),
    'ng': SymbolByName('LATIN SMALL LETTER ENG'),
    'NG': SymbolByName('LATIN CAPITAL LETTER ENG'),
    'th': SymbolByName('LATIN SMALL LETTER THORN'),
    'TH': SymbolByName('LATIN CAPITAL LETTER THORN'),
    'dag': SymbolByName('DAGGER'),
    'ddag': SymbolByName('DOUBLE DAGGER'),
    'dots': SymbolByName('HORIZONTAL ELLIPSIS'),
    'P': SymbolByName('PILCROW SIGN'),
    'S': SymbolByName('SECTION SIGN'),
    'copyright': SymbolByName('COPYRIGHT SIGN'),
    'pounds': SymbolByName('POUND SIGN'),
    'guillemotleft': SymbolByName('LEFT-POINTING DOUBLE ANGLE QUOTATION MARK'),
    'guillemotright': SymbolByName('RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK'),
    'guilsinglleft': SymbolByName('SINGLE LEFT-POINTING ANGLE QUOTATION MARK'),
    'guilsinglright': SymbolByName('SINGLE RIGHT-POINTING ANGLE QUOTATION MARK'),
    'quotedblbase': SymbolByName('DOUBLE LOW-9 QUOTATION MARK'),
    'quotesinglbase': SymbolByName('SINGLE LOW-9 QUOTATION MARK'),
    'textquotedbl': Symbol('"'),

    'textasciicircum': Symbol('^'),
    'textasciitilde': Symbol('~'),
    'textasteriskcentered': Symbol('*'),
    'textbackslash': Symbol('\\'),
    'textbar': Symbol('|'),
    'textbraceleft': Symbol('{'),
    'textbraceright': Symbol('}'),
    'textbullet': SymbolByName('BULLET'),
    'textcopyright': SymbolByName('COPYRIGHT SIGN'),
    'textdagger': SymbolByName('DAGGER'),
    'textdaggerdbl': SymbolByName('DOUBLE DAGGER'),
    'textdollar': Symbol('$'),
    'textellipsis': SymbolByName('HORIZONTAL ELLIPSIS'),
    'textemdash': SymbolByName('EM DASH'),
    'textendash': SymbolByName('EN DASH'),
    'textexclamdown': SymbolByName('INVERTED EXCLAMATION MARK'),
    'textgreater': Symbol('>'),
    'textless': Symbol('<'),
    'textordfeminine': SymbolByName('FEMININE ORDINAL INDICATOR'),
    'textordmasculine': SymbolByName('MASCULINE ORDINAL INDICATOR'),
    'textparagraph': SymbolByName('PILCROW SIGN'),
    'textperiodcentered': SymbolByName('MIDDLE DOT'),
    'textquestiondown': SymbolByName('INVERTED QUESTION MARK'),
    'textquotedblleft': SymbolByName('LEFT DOUBLE QUOTATION MARK'),
    'textquotedblright': SymbolByName('RIGHT DOUBLE QUOTATION MARK'),
    'textquoteleft': SymbolByName('LEFT SINGLE QUOTATION MARK'),
    'textquoteright': SymbolByName('RIGHT SINGLE QUOTATION MARK'),
    'textregistered': SymbolByName('REGISTERED SIGN'),
    'textsection': SymbolByName('SECTION SIGN'),
    'textsterling': SymbolByName('POUND SIGN'),
    'texttrademark': SymbolByName('TRADE MARK SIGN'),
    'textunderscore': Symbol('_'),
    'textvisiblespace': SymbolByName('OPEN BOX'),

    'TeX': Macro(0, 'TeX'),

    # escaped characters
    '&': Symbol('&'),
    '$': Symbol('$'),
    '{': Symbol('{'),
    '}': Symbol('}'),
    '%': Symbol('%'),
    '#': Symbol('#'),
    '_': Symbol('_'),
}
