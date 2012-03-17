

class String(str):
    def __radd__(self, other):
        return MixedString([other]).__add__(self)

    def __add__(self, other):
        return MixedString([self]).__add__(other)

    def __iadd__(self, other):
        return self.__add__(other)

    def lower(self):
        return self.__class__(super().lower())

    def upper(self):
        return self.__class__(super().upper())

    def soft_lower(self):
        return self.lower()

    def soft_upper(self):
        return self.upper()

    def capitalize_first(self):
        string = str(self)
        result = string[0].upper()
        if len(string) > 1:
            result += string[1:]
        return self.__class__(result)

    def words(self):
        for word in self.split():
            yield self.__class__(word)


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

    def __getitem__(self, index):
        return str(self)[index]

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

    def split(self, sep=None, maxsplit=-1):
        return str(self).split(sep, maxsplit)

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
