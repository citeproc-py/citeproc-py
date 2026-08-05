from unittest import TestCase

from citeproc.model import Affixed
from citeproc.string import String, join


class Affix(Affixed):
    """The smallest thing `Affixed.wrap` needs: something with a `get`."""

    def __init__(self, prefix='', suffix=''):
        self.values = {'prefix': prefix, 'suffix': suffix}

    def get(self, name, default=None):
        return self.values.get(name, default)


class TestStringSeams(TestCase):
    # A seam may hold either a str or a MixedString, and MixedString is a list
    # of segments whose == compares as a list. Compare str(result), or the
    # assertion silently stops being about the text.

    def test_join_normalizes_delimiter_at_each_seam(self):
        result = join(['Doe, J.', '(2001)', 'A book'], '. ')

        self.assertEqual(str(result), 'Doe, J. (2001). A book')

    def test_affixed_wrap_does_not_duplicate_suffix_punctuation(self):
        result = Affix(suffix='.').wrap(String('Doe, J.'))

        self.assertEqual(str(result), 'Doe, J.')

    # A String normalizes the seam in its own __add__, so join and wrap have to
    # defer to it rather than normalize a second time. Normalizing twice drops
    # two characters where one was meant to go, which eats real content.

    def test_join_drops_only_one_character_at_a_string_seam(self):
        result = join([String('a.'), String('..b')], '')

        self.assertEqual(str(result), 'a..b')

    def test_wrap_drops_only_one_character_at_a_string_seam(self):
        result = Affix(suffix='..').wrap(String('x.'))

        self.assertEqual(str(result), 'x..')
