# coding: utf-8

import unicodedata

from . import (parse_argument, eat_whitespace, parse_macro_name,
               OPEN_SCOPE, CLOSE_SCOPE, START_MACRO)


__all__ = ['MACROS', 'NewCommand', 'Macro']


class MacroBase(object):
    def parse_arguments(self, tokens):
        raise NotImplementedError

    def parse_arguments_and_expand(self, tokens):
        raise NotImplementedError



class NewCommand(MacroBase):
    r""" \newcommand{cmd}[args]{def} """

    def __init__(self, macros):
        self.macros = macros

    @staticmethod
    def _parse_macro_name(tokens):
        eat_whitespace(tokens)
        token = next(tokens)
        in_group = token.type == OPEN_SCOPE
        if in_group:
            eat_whitespace(tokens)
            token = next(tokens)
        assert token.type == START_MACRO
        name = parse_macro_name(tokens)
        if in_group:
            eat_whitespace(tokens)
            assert next(tokens).type == CLOSE_SCOPE
        return name

    @staticmethod
    def _parse_optional_arguments(tokens, macros):
        eat_whitespace(tokens)
        if tokens.peek().value == '[':
            next(tokens)
            num_args = ''
            for token in tokens:
                if token.value == ']':
                    break
                num_args += token.value
        else:
            num_args = 0
        return int(num_args)

    def parse_arguments_and_expand(self, tokens, macros):
        name = self._parse_macro_name(tokens)
        num_args = self._parse_optional_arguments(tokens, macros)
        definition = parse_argument(tokens, macros)
        for i in range(10):
            definition = definition.replace('#{}'.format(i + 1),
                                            '{' + str(i) + '}')
        self.macros[name] = Macro(num_args, definition)
        return ''


class Macro(object):
    def __init__(self, num_args, format_string):
        self.num_args = num_args
        self.format_string = format_string

    def parse_arguments_and_expand(self, tokens, macros):
        args = [parse_argument(tokens, macros) for _ in range(self.num_args)]
        return self.expand(args)

    def expand(self, arguments):
        assert len(arguments) == self.num_args
        return self.format_string.format(*arguments)


class Symbol(Macro):
    def __init__(self, symbol):
        super(Symbol, self).__init__(0, symbol)


class SymbolByName(Macro):
    def __init__(self, unicode_symbol_name):
        unicode_symbol = unicodedata.lookup(unicode_symbol_name)
        super(SymbolByName, self).__init__(0, unicode_symbol)


class Combining(Macro):
    def __init__(self, unicode_accent_name):
        unicode_accent = unicodedata.lookup('COMBINING ' + unicode_accent_name)
        super(Combining, self).__init__(1, '{0}' + unicode_accent)

    DOTTED_CHARS = {'ı': 'i',
                    'ȷ': 'j'}

    def expand(self, arguments):
        assert len(arguments) == self.num_args
        accented, rest = arguments[0][0], arguments[0][1:]
        accented = self.DOTTED_CHARS.get(accented, accented)
        expanded = super(Combining, self).expand([accented])
        return unicodedata.normalize('NFC', expanded) + rest


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
    # '|': Combining('VERTICAL LINE ABOVE'),
    # 'h': Combining('HOOK ABOVE'),
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
    'textquotesingle': Symbol("'"),  # from the textcomp package
    'textquotedbl': Symbol('"'),
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
    ' ': Symbol(' '),
    '&': Symbol('&'),
    '$': Symbol('$'),
    '{': Symbol('{'),
    '}': Symbol('}'),
    '%': Symbol('%'),
    '#': Symbol('#'),
    '_': Symbol('_'),
}
