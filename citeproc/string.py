
from functools import wraps


# Punctuation characters that should not be duplicated when two of them end up
# adjacent at a concatenation seam (e.g. a suffix '.' following text that
# already ends in '.').
SEAM_PUNCTUATION = frozenset('.,;:!?')


def normalize_seam(left, other):
    """Adjust the leading characters of `other` so that concatenating it onto
    `left` does not introduce a double space or a duplicated punctuation mark.

    `left` is the accumulated string so far and `other` the piece about to be
    appended. Only the boundary between them is considered; the interior of
    either side (e.g. an ellipsis inside a title) is never touched. Markup
    segments start with '<', so they are left alone. Returns `other`, possibly
    with its first character removed."""
    left = str(left)
    other_str = str(other)
    if not left or not other_str:
        return other
    last, first = left[-1], other_str[0]
    # collapse a double space
    if last == ' ' and first == ' ':
        return _strip_first_char(other)
    # drop a duplicated punctuation mark ('..' -> '.', ',,' -> ',', ...)
    if last == first and first in SEAM_PUNCTUATION:
        return _strip_first_char(other)
    return other


def _strip_first_char(other):
    """Return a copy of `other` with its first character removed, preserving
    the (Mixed)String segment structure."""
    if isinstance(other, MixedString):
        segments = list(other)
        head = segments[0]
        stripped = type(head)(str(head)[1:])
        segments[0:1] = [stripped] if stripped != '' else []
        return MixedString(segments)
    return type(other)(str(other)[1:])


def discard_empty_other(method):
    """Decorator for addition operator methods that returns the object itself if
    `other` is the empty string."""
    @wraps(method)
    def wrapper(obj, other):
        if other == '':
            return obj
        else:
            return method(obj, other)
    return wrapper


class String(str):
    @discard_empty_other
    def __radd__(self, other):
        return MixedString([other]).__add__(self)

    @discard_empty_other
    def __add__(self, other):
        return MixedString([self]).__add__(other)

    def __iadd__(self, other):
        return self.__add__(other)

    def replace(self, *args, **kwargs):
        return self.__class__(super(String, self).replace(*args, **kwargs))

    def rstrip(self, *args, **kwargs):
        return self.__class__(super(String, self).rstrip(*args, **kwargs))

    def lower(self):
        return self.__class__(super(String, self).lower())

    def upper(self):
        return self.__class__(super(String, self).upper())

    def soft_lower(self):
        return self.lower()

    def soft_upper(self):
        return self.upper()

    def capitalize_first(self):
        return self.__class__(self[0].upper() + self[1:])

    def words(self):
        for word in self.split():
            yield self.__class__(word)


class MixedString(list):
    @discard_empty_other
    def __add__(self, other):
        other = normalize_seam(self, other)
        if other == '' or other == []:
            return self
        super_obj = super(MixedString, self)
        try:
            return self.__class__(super_obj.__add__(other))
        except TypeError:
            return self.__class__(super_obj.__add__(MixedString([other])))

    @discard_empty_other
    def __radd__(self, other):
        return self.__class__([other]).__add__(self)

    def __iadd__(self, other):
        return self.__add__(other)

    def __str__(self):
        return ''.join(map(str, self))

    def __getitem__(self, index):
        return str(self)[index]

    def replace(self, *args):
        return self.__class__([string.replace(*args) for string in self])

    def translate(self, table):
        return self.__class__([string.translate(table) for string in self])

    def lower(self):
        return self.__class__([string.lower() for string in self])

    def upper(self):
        return self.__class__([string.upper() for string in self])

    def title(self):
        return self.__class__([string.title() for string in self])

    def capitalize_first(self):
        self_iter = iter(self)
        output = [next(self_iter).capitalize_first()]
        output += [string for string in self_iter]
        return self.__class__(output)

    def isupper(self):
        return all(string.isupper() for string in self)

    def split(self, *args, **kwargs):
        return str(self).split(*args, **kwargs)

    def rstrip(self, *args, **kwargs):
        rev_iter = reversed(self)
        output = [next(rev_iter).rstrip(*args, **kwargs)]
        output += [string for string in rev_iter]
        return self.__class__(reversed(output))

    def words(self):
        for string in self:
            for word in string.words():
                yield word


class NoCase(String):
    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))

    def soft_lower(self):
        return self

    def soft_upper(self):
        return self

    def capitalize_first(self):
        return self


def join(items, delimiter=''):
    items = iter(items)
    try:
        output = next(items)
    except StopIteration:
        return String('')

    for item in items:
        delimiter_part = normalize_seam(output, delimiter)
        output = output + delimiter_part
        output = output + normalize_seam(output, item)
    return output
