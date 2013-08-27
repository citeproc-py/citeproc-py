from ..py2compat import text_type

def preformat(text):
    return text


Italic = text_type
Oblique = text_type
Bold = text_type
Light = text_type
Underline = text_type
Superscript = text_type
Subscript = text_type
SmallCaps = text_type

class Bibliography(text_type):
    def __new__(cls, items):
        items = map(text_type, items)
        return super(Bibliography, cls).__new__(cls, '\n'.join(items))
