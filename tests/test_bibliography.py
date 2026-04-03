# coding: utf-8
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
        expected_ordinals = {
            "en-US": {0: "1st", 1: "2nd", 3: "4th", 19: "20th"},
            "de-DE": {0: "1.", 9: "10."},
            "es-ES": {0: "1.ª"},
            "fr-FR": {0: "1ʳᵉ", 9: "10ᵉ"},
            "hi-IN": {0: "1वाँ"},
            "it-IT": {0: "1º"}
        }

        for lg, ordinals in expected_ordinals.items():
            bib_style = CitationStylesStyle("harvard1", lg)
            entries = []
            for edition in range(1, 26):
                template["id"] = str(edition)
                template["edition"] = edition
                entries.append(template.copy())
            bib = source.json.CiteProcJSON(entries)
            bibliography = CitationStylesBibliography(bib_style, bib, formatter.plain)
            citations = [CitationItem(str(x)) for x in range(1, 26)]
            bibliography.register(Citation(citations))
            generated_ordinals = [_pp(x) for x in bibliography.style.render_bibliography(citations)]

            for index, expected_value in ordinals.items():
                assert generated_ordinals[index] == expected_value, f"Failed for {lg} at index {index}. Expected: {expected_value}, Got: {generated_ordinals[index]}"

    def test_ordinals_with_embedded_locale(self):
        """chicago-author-date has an embedded <locale xml:lang="en"> that defines
        editor/translator terms but no ordinal terms.  Ordinals must still be
        resolved from the file-based en-US locale data.
        Regression test for https://github.com/citeproc-py/citeproc-py/issues/183."""
        bib_style = CitationStylesStyle("chicago-author-date", "en-US")

        entries = [
            {
                "id": str(n),
                "type": "book",
                "title": "Some Book",
                "author": [{"family": "Smith", "given": "John"}],
                "issued": {"date-parts": [[2020]]},
                "publisher": "Publisher",
                "publisher-place": "New York",
                "edition": n,
            }
            for n in range(1, 5)
        ]

        bib = source.json.CiteProcJSON(entries)
        bibliography = CitationStylesBibliography(bib_style, bib, formatter.plain)
        citations = [CitationItem(str(x)) for x in range(1, 5)]
        bibliography.register(Citation(citations))
        rendered = bibliography.style.render_bibliography(citations)

        # The ordinal edition token is the 6th whitespace-delimited word, e.g.:
        # "Smith, John. 2020. Some Book. 2nd ed. New York: Publisher."
        ordinals = [r.split()[5] for r in rendered]
        assert ordinals[0] == "1st", f"Expected '1st', got '{ordinals[0]}'"
        assert ordinals[1] == "2nd", f"Expected '2nd', got '{ordinals[1]}'"
        assert ordinals[2] == "3rd", f"Expected '3rd', got '{ordinals[2]}'"
        assert ordinals[3] == "4th", f"Expected '4th', got '{ordinals[3]}'"
