
from __future__ import unicode_literals

import sys

try:
    from html import escape
except ImportError:
    from cgi import escape


if sys.version_info[0] < 3:
    str = unicode


def preformat(text):
    return escape(str(text))


class TagWrapper(str):
    tag = None
    attributes = None

    @classmethod
    def _wrap(cls, text):
        if cls.attributes:
            attrib = ' ' + ' '.join(['{}="{}"'.format(key, value)
                                     for key, value in cls.attributes.items()])
        else:
            attrib = ''
        return '<{tag}{attrib}>{text}</{tag}>'.format(tag=cls.tag,
                                                      attrib=attrib,text=text)

    def __new__(cls, text):
        return super(TagWrapper, cls).__new__(cls, cls._wrap(text))


class Italic(TagWrapper):
    tag = 'i'


class Oblique(Italic):
    pass


class Bold(TagWrapper):
    tag = 'b'


class Light(TagWrapper):
    tag = 'l'


class Underline(TagWrapper):
    tag = 'u'


class Superscript(TagWrapper):
    tag = 'sup'


class Subscript(TagWrapper):
    tag = 'sub'


class SmallCaps(TagWrapper):
    tag = 'span'
    attributes = {'style': 'font-variant:small-caps;'}


class Bibliography(str):
    bib_prefix = '<div class="csl-bib-body">'
    bib_suffix = '</div>'
    item_prefix = '  <div class="csl-entry">'
    item_suffix = '</div>'

    def __new__(cls, items):
        output = [cls.bib_prefix]
        for text in items:
            text = cls.item_prefix + str(text) + cls.item_suffix
            output.append(text)
        output.append(cls.bib_suffix)
        return super(Bibliography, cls).__new__(cls, '\n'.join(output))
