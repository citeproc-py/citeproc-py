
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *

try:
    from html import escape
except ImportError:
    from cgi import escape


def preformat(text):
    return escape(str(text), quote=False)


class TagWrapper(str):
    tag = None
    attributes = None

    @classmethod
    def _wrap(cls, text, attributes=None):
        if attributes == None:
            attributes = {}
            
        if cls.attributes:
            attributes.update(cls.attributes)
        
        if attributes:
            attrib = ' ' + ' '.join(['{}="{}"'.format(key, value)
                                     for key, value in attributes.items()])
        else:
            attrib = ''
        
        tag = cls.tag or 'span'
        
        return '<{tag}{attrib}>{text}</{tag}>'.format(tag=tag,
                                                      attrib=attrib,text=text)

    def __new__(cls, text, attributes=None):
        return super(TagWrapper, cls).__new__(cls, cls._wrap(text, attributes))

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