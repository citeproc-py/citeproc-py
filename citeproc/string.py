
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *

from functools import wraps


def soft_lower(string):
    try:
        return string.soft_lower()
    except AttributeError:
        assert type(string) == str
        return string.lower()


def soft_upper(string):
    try:
        return string.soft_upper()
    except AttributeError:
        assert type(string) == str
        return string.upper()


def capitalize_first(string):
    try:
        return string.capitalize_first()
    except AttributeError:
        assert type(string) == str
        return string[0].upper() + string[1:]


def words(string):
    try:
        return string.words()
    except AttributeError:
        assert type(string) == str
        for word in string.split():
            yield word


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


class StringBase(object):
    def __repr__(self):
        base_repr = super(StringBase, self).__repr__()
        return '{}({})'.format(self.__class__.__name__, base_repr)


class String(StringBase, str):
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


class MixedString(StringBase, list):
    @discard_empty_other
    def __add__(self, other):
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


if PY2:
    MixedString.__unicode__ = MixedString.__str__
    del MixedString.__str__


class NoCase(String):
    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))

    def soft_lower(self):
        return self

    def soft_upper(self):
        return self

    def capitalize_first(self):
        return self
