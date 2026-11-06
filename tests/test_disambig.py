from io import BytesIO
from unittest import TestCase

from citeproc import CitationStylesBibliography, CitationStylesStyle
from citeproc.disambig import get_ambiguous_cite
from citeproc.formatter import plain
from citeproc.source import Citation, CitationItem
from citeproc.source.json import CiteProcJSON


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
    def test_incremental_registration_recomputes_disambiguation(self):
        """New references must be grouped against prior items' baseline forms."""
        style = CitationStylesStyle(BytesIO(b'''\
            <style xmlns="http://purl.org/net/xbiblio/csl" version="1.0">
              <info><title>Test</title><id>test</id></info>
              <citation disambiguate-add-names="true"
                         disambiguate-add-year-suffix="true">
                <layout delimiter="; ">
                  <names variable="author">
                    <name form="short" et-al-min="2" et-al-use-first="1"/>
                  </names>
                  <date variable="issued" prefix=" ">
                    <date-part name="year"/>
                  </date>
                </layout>
              </citation>
            </style>
        '''), validate=False)
        source = CiteProcJSON([
            {
                'id': 'a',
                'type': 'book',
                'author': [
                    {'family': 'Smith'},
                    {'family': 'Jones'},
                ],
                'issued': {'date-parts': [[1980]]},
            },
            {
                'id': 'b',
                'type': 'book',
                'author': [
                    {'family': 'Smith'},
                    {'family': 'Brown'},
                ],
                'issued': {'date-parts': [[1980]]},
            },
            {
                'id': 'c',
                'type': 'book',
                'author': [
                    {'family': 'Smith'},
                    {'family': 'Jones'},
                ],
                'issued': {'date-parts': [[1980]]},
            },
        ])
        bibliography = CitationStylesBibliography(style, source, formatter=plain)
        first_citation = Citation([CitationItem('a'), CitationItem('b')])
        later_citation = Citation([CitationItem('c')])

        def do_nothing(_item):
            pass

        bibliography.register(first_citation)
        initial_output = str(bibliography.cite(first_citation, do_nothing))

        bibliography.register(later_citation)
        later_output = str(bibliography.cite(later_citation, do_nothing))
        updated_first_output = str(bibliography.cite(first_citation, do_nothing))

        self.assertEqual(
            initial_output,
            'Smith, Jones 1980; Smith, Brown 1980',
        )
        self.assertEqual(
            (updated_first_output, later_output),
            (
                'Smith, Jones 1980a; Smith, Brown 1980',
                'Smith, Jones 1980b',
            ),
        )

    def test_reset_restores_input_year_suffix_values(self):
        style = CitationStylesStyle(BytesIO(b'''\
            <style xmlns="http://purl.org/net/xbiblio/csl" version="1.0">
              <info><title>Test</title><id>test</id></info>
              <citation disambiguate-add-year-suffix="true">
                <layout delimiter="; ">
                  <names variable="author"><name form="short"/></names>
                  <date variable="issued" prefix=" ">
                    <date-part name="year"/>
                  </date>
                </layout>
              </citation>
            </style>
        '''), validate=False)
        source = CiteProcJSON([
            {
                'id': item_id,
                'type': 'book',
                'author': [{'family': 'Smith'}],
                'issued': {'date-parts': [[1980]]},
                'year_suffix': original_suffix,
            }
            for item_id, original_suffix in [('a', 'input-a'), ('b', 'input-b')]
        ])
        bibliography = CitationStylesBibliography(style, source, formatter=plain)
        citation = Citation([CitationItem('a'), CitationItem('b')])
        bibliography.register(citation)

        def do_nothing(_item):
            pass

        bibliography.cite(citation, do_nothing)

        self.assertEqual(source['a']['year_suffix'], 'a')
        self.assertEqual(source['b']['year_suffix'], 'b')
        bibliography._reset_disambiguation_state()
        self.assertEqual(str(source['a']['year_suffix']), 'input-a')
        self.assertEqual(str(source['b']['year_suffix']), 'input-b')

    def test_get_ambiguous_cite_restores_disambiguation_request_on_error(self):
        root = _StyleRoot()
        previous_request = root.disambig_request
        layout = _Layout(root)

        with self.assertRaisesRegex(RuntimeError, 'probe render failed'):
            get_ambiguous_cite(object(), layout)

        self.assertIs(root.disambig_request, previous_request)
        self.assertFalse(root.just_looking)