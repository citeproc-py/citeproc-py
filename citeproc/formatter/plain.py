
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *


def preformat(text):
    return text


Italic = str
Oblique = str
Bold = str
Light = str
Underline = str
Superscript = str
Subscript = str
SmallCaps = str


class Bibliography(str):
    def __new__(cls, items):
        items = map(str, items)
        return super(Bibliography, cls).__new__(cls, '\n'.join(items))
