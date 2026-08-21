
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
    def _wrap(cls, text):
        if cls.attributes:
            attrib = ' ' + ' '.join([f'{key}="{value}"'
                                     for key, value in cls.attributes.items()])
        else:
            attrib = ''
        return f'<{cls.tag}{attrib}>{text}</{cls.tag}>'

    def __new__(cls, text):
        return super().__new__(cls, cls._wrap(text))


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
