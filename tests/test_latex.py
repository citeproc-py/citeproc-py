# coding: utf-8

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *

from unittest import TestCase

from citeproc.source.bibtex.latex import parse_latex, substitute_ligatures


class TestLatex(TestCase):
    # from "A TEX Primer for Scientists" (sections 5.2 and 5.3)
    # by Stanley A. Sawyer, Steven G. Krantz
    MACROS = [("Æsop's fables", r"\AE sop's fables"),
              ('Æ is a Latin ligature', r"\AE\ is a Latin ligature"),
              ('A TeX expert is a TeXnician.',
                    r"A \TeX\ expert is a \TeX nician."),
              ('This book is ©ed.', r"This book is \copyright ed."),
              ('Umeå, Sweden', r"Ume\aa, Sweden"),
              ('Your serial number is Å1102.',
                    r"Your serial number is \AA1102."),
              ('Your serial number is Å1102.',
                    r"Your serial number is \AA  1102."),
              ('$22.50 plus $ 4.07 tax.', r"\$22.50 plus \$ 4.07 tax."),
              ('Crève Cœur, Missouri', r"Cr\`eve C\oe ur, Missouri"),
              ('Pëtr, meet Françoise', r"P\"etr, meet Fran\c coise"),

              ('Pëtr Pëtr Pëtr', r'P\" etr P\"  etr ' 'P\\"\tetr'),
              ]

    ACCENT_MACROS = [('très élevé', r"tr\`es \'elev\'e"),
                     ('übel Föhn', r'\"ubel F\"ohn'),
                     ('Andō Tokutarō', r"And\=o Tokutar\=o"),
                     ('García Lorca', r"Garc\'\i a Lorca"),
                     ('naïve', r'na\"\i ve'),

                     ('hát hàt hȧt hät hāt', r"h\'at h\`at h\.at h\"at h\=at"),
                     ('hãt  hât  ha̧t  ha̱t', r"h\~at  h\^at  h\c at  h\b at"),
                     ('hạt  hǎt  ha̋t', "h\\d at  h\\v at  h\\H at"),
                     ('hăt  ha͡at', "h\\u at  h\\t aat"),

                     ('øre', r"\o re"),
                     ('Øre', r"\O re"),
                     ('łódka', r"\l\'odka"),
                     ('Łodz', r"\L odz"),
                     ('Altstraße', r"Altstra\ss e"),
                     ('æsthete', r"\ae sthete"),
                     ('Ålm', r"\AA lm"),
                     # ('', r"{\it\$}5"),
                     ('Œuvre', r"\OE uvre"),
                     ]

    # assorted string with macros
    ASSORTED = [('Escobar, María José', r"Escobar, Mar{\'\i}a Jos{\'e}"),
                ('Escobar, María-José', r"Escobar, Mar\'{\i}a-Jos\'{e}"),
                ('Åke José Édouard Gödel',      # unbalanced parenthesis
                      r"\AA{ke} {Jos{\'{e}} {\'{E}douard} G{\"o}del")]

    MATH = [(r'An $O(n \log n / \! \log\log n)$ Sorting Algorithm',
                  r"An $O(n \log n / \! \log\log n)$ Sorting Algorithm")]

    def test_parse_latex(self):
        for reference, string in self.MACROS:
            self.assertEqual(reference, parse_latex(string))
        for reference, string in self.ACCENT_MACROS:
            self.assertEqual(reference, parse_latex(string))
        for reference, string in self.ASSORTED:
            self.assertEqual(reference, parse_latex(string))
        for reference, string in self.MATH:
            self.assertEqual(reference, parse_latex(string))

    LIGATURES = [('¿Que pasa?', "?`Que pasa?"),
                 ('¡Que!', "!`Que!")]

    def test_substitute_ligatures(self):
        for reference, string in self.LIGATURES:
            self.assertEqual(reference, substitute_ligatures(string))
