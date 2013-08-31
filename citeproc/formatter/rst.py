from __future__ import print_function, unicode_literals

import sys

if sys.version_info[0] < 3:
    str = unicode


def escape(text):
    text = text.replace('*', '\*')
    text = text.replace('`', '\`')
    return text


def preformat(text):
    return escape(str(text))


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
    role ='strong'


Light = str
Underline = str


class Superscript(RoleWrapper):
    role ='superscript'


class Subscript(RoleWrapper):
    role ='subscript'


SmallCaps = str


class Bibliography(str):
    def __new__(cls, items):
        items = map(str, items)
        return super(Bibliography, cls).__new__(cls, '\n'.join(items))
