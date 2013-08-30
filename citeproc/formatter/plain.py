from __future__ import print_function, unicode_literals

import sys

if sys.version_info[0] < 3:
    str = unicode


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


if sys.version_info[0] < 3:
    Bibliography.__str__ = lambda self: self.encode('utf-8')
