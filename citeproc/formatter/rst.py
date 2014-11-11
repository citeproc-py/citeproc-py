
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *


def escape(text):
    text = text.replace('*', '\*')
    text = text.replace('`', '\`')
    return text


def preformat(text):
    return escape(str(text))

def str_passthrough(string, **kwargs): # for other formatters we might send keyword arguments, but the plain formatter ignores them and just returns str(x)
    return str(string)

class RoleWrapper(str):
    role = None

    @classmethod
    def _wrap(cls, text):
        return ':{role}:`{text}`'.format(role=cls.role, text=text)

    def __new__(cls, text):
        return super(RoleWrapper, cls).__new__(cls, cls._wrap(text))


class Italic(RoleWrapper):
    role = 'emphasis'


class Oblique(Italic):
    pass


class Bold(RoleWrapper):
    role = 'strong'


Light = str_passthrough
Underline = str_passthrough


class Superscript(RoleWrapper):
    role = 'superscript'


class Subscript(RoleWrapper):
    role = 'subscript'


SmallCaps = str_passthrough
Span = str_passthrough
