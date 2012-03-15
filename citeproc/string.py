

class String(str):
    def __radd__(self, other):
        return MixedString([other]).__add__(self)

    def __add__(self, other):
        return MixedString([self]).__add__(other)

    def __iadd__(self, other):
        return self.__add__(other)


class MixedString(list):
    def __add__(self, other):
        try:
            return self.__class__(super().__add__(other))
        except TypeError:
            return self.__class__(super().__add__(__class__([other])))

    def __radd__(self, other):
        return self.__class__([other]).__add__(self)

    def __iadd__(self, other):
        return self.__add__(other)

    def __str__(self):
        return ''.join(map(str, self))

    def lower(self):
        return self.__class__([string.lower() for string in self])

    def upper(self):
        return self.__class__([string.upper() for string in self])


class NoCase(String):
    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(self))

    def lower(self):
        return self
