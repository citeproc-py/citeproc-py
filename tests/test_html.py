# coding: utf-8

from unittest import TestCase

from citeproc import (
    Citation,
    CitationItem,
    CitationStylesBibliography,
    CitationStylesStyle,
    formatter,
)
from citeproc.source.json import CiteProcJSON
from citeproc_styles import get_style_filepath


class TestHTMLParser(TestCase):
    def test_affixes(self):
        """Test that affixes are escaped correctly."""
        style = CitationStylesStyle(get_style_filepath("oxford-german-studies"))
        r = {
            "type": "article",
            "id": "ref0",
            "title": None,
            "DOI": "10.1271/kagakutoseibutsu.51.483",
            "author": [{"family": "Ikeda", "given": "Ikuo"}],
            "issued": {"date-parts": [[2013]]},
            "ISSN": "0453-073X",
            "publisher": "KAGAKU TO SEIBUTSU",
            "container_title": "KAGAKU TO SEIBUTSU",
            "issue": "7",
            "volume": "51",
            "page": "483-495",
        }
        bib = CitationStylesBibliography(style, CiteProcJSON([r]), formatter.html)
        bib.register(Citation([CitationItem("ref0")]))
        result = str(b.bibliography()[0])
        # We want to see that < and > are properly escaped to &lt; and &gt;.
        self.assertIn(
            "&lt;http://dx.doi.org/10.1271/kagakutoseibutsu.51.483&gt;", result
        )
