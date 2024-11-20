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

template = {
        "type": "book",
        "title": "La Rettorica",
        "author": [{"literal": "Brunetto Latini"}],
        "issued": {"date-parts": [[1968]]},
        "editor": [{"literal": "Francesco Maggini"}],
        "publisher": "Le Monnier",
        "location": "Firenze",
    }

def _pp(string):
    return string.split(" ")[5]

class TestBibliographyGeneration(TestCase):
    def test_generate(self):
        # for lg in ["en-US", "de-DE"]:
        for lg in ["en-US", "de-DE", "nl-NL", "fr-FR", "es-ES", "it-IT", "hi-IN"]:
            print(lg)
            bib_style = CitationStylesStyle("harvard1", lg)
            entries = []
            for edition in range(1,26):
                template["id"] = str(edition)
                template["edition"] = edition
                entries.append(template.copy())
            bib = source.json.CiteProcJSON(entries)
            bibliography = CitationStylesBibliography(bib_style, bib, formatter.plain)
            citations = [CitationItem(str(x)) for x in range(1,26)]
            bibliography.register(Citation(citations))
            ordinals = [_pp(x) for x in bibliography.style.render_bibliography(citations)]
            # print(ordinals)
            if lg == "en-US":
                assert ordinals[0] == "1st"
            if lg == "de-DE":
                assert ordinals[0] == "1."
            if lg == "es-ES":
                assert ordinals[0] == "1.ª"
            if lg == "fr-FR":
                assert ordinals[0] == "1ʳᵉ"
            if lg == "hi-IN":
                assert ordinals[0] == "1"
            if lg == "it-IT":
                assert ordinals[0] == "1º"
            # print(lg,
            #     "\n".join(
            #         ordinals
            #     )
            # )
