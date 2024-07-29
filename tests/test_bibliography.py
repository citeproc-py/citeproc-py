# coding: utf-8
import os
from citeproc import (
    Citation,
    CitationItem,
    CitationStylesBibliography,
    CitationStylesStyle,
    formatter,
    source,
)
from unittest import TestCase
from citeproc.source.bibtex.bibparse import BibTeXParser

BIB = [
    {
        "type": "book",
        "id": "1",
        "title": "La Rettorica",
        "author": [{"literal": "Brunetto Latini"}],
        "issued": {"date-parts": [[1968]]},
        "editor": [{"literal": "Francesco Maggini"}],
        "edition": 4,
        "publisher": "Le Monnier",
        "location": "Firenze",
    }
]


class TestBibliographyGeneration(TestCase):
    def test_generate(self):
        bib = source.json.CiteProcJSON(BIB)
        bib_style = CitationStylesStyle("harvard1")
        bibliography = CitationStylesBibliography(bib_style, bib, formatter.plain)
        citations = [CitationItem(item["id"]) for item in BIB]
        bibliography.register(Citation(citations))
        print(
            "\n".join(
                [str(x) for x in bibliography.style.render_bibliography(citations)]
            )
        )
