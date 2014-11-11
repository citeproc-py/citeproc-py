
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *


def preformat(text):
    return text

def str_passthrough(string, **kwargs): # for other formatters we might send keyword arguments, but the plain formatter ignores them and just returns str(x)
    return str(string)

Italic = str_passthrough
Oblique = str_passthrough
Bold = str_passthrough
Light = str_passthrough
Underline = str_passthrough
Superscript = str_passthrough
Subscript = str_passthrough
SmallCaps = str_passthrough
Span = str_passthrough
