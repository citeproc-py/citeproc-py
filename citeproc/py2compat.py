import sys

PY2 = sys.version_info[0] < 3

if PY2:
    string_types = basestring,
    text_type = unicode
else:
    string_types = str,
    text_type = str
