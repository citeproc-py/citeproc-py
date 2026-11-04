from unittest import TestCase

from citeproc.disambig import get_ambiguous_cite


class _StyleRoot:
    def __init__(self):
        self.disambig_request = object()
        self.just_looking = False


class _CitationElement:
    cites = None


class _Layout:
    def __init__(self, root):
        self.root = root
        self.citation = _CitationElement()

    def get_root(self):
        return self.root

    def getparent(self):
        return self.citation

    def render_children(self, item):
        raise RuntimeError('probe render failed')


class TestDisambiguation(TestCase):
    def test_get_ambiguous_cite_restores_disambiguation_request_on_error(self):
        root = _StyleRoot()
        previous_request = root.disambig_request
        layout = _Layout(root)

        with self.assertRaisesRegex(RuntimeError, 'probe render failed'):
            get_ambiguous_cite(object(), layout)

        self.assertIs(root.disambig_request, previous_request)
        self.assertFalse(root.just_looking)