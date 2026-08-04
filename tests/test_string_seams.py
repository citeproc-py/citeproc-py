from citeproc.model import Affixed
from citeproc.string import String, join


class _Affix(Affixed):
    def __init__(self, prefix='', suffix=''):
        self._values = {'prefix': prefix, 'suffix': suffix}

    def get(self, name, default=None):
        return self._values.get(name, default)


def test_join_normalizes_delimiter_at_each_seam():
    result = join(['Doe, J.', '(2001)', 'A book'], '. ')

    assert result == 'Doe, J. (2001). A book'


def test_affixed_wrap_does_not_duplicate_suffix_punctuation():
    result = _Affix(suffix='.').wrap(String('Doe, J.'))

    assert result == 'Doe, J.'
