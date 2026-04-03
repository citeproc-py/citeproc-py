# coding: utf-8
import io
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

# A minimal harvard1-like style with an embedded <locale xml:lang="en"> that
# defines non-ordinal terms only (simulating chicago-author-date).  Without the
# fix in to_ordinal() this style would produce "2th", "3th" etc. for en-US.
HARVARD1_WITH_EMBEDDED_EN_LOCALE = """\
<?xml version="1.0" encoding="utf-8"?>
<style xmlns="http://purl.org/net/xbiblio/csl" class="in-text" version="1.0"
       demote-non-dropping-particle="sort-only">
  <info>
    <title>Harvard1 with embedded en locale (test)</title>
    <id>http://example.com/test-embedded-locale</id>
    <link href="http://example.com/test-embedded-locale" rel="self"/>
    <updated>2024-01-01T00:00:00+00:00</updated>
    <rights license="http://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</rights>
  </info>
  <locale xml:lang="en">
    <terms>
      <term name="anonymous">unsigned</term>
    </terms>
  </locale>
  <macro name="author">
    <names variable="author">
      <name name-as-sort-order="all" and="symbol" sort-separator=", "
            initialize-with="." delimiter-precedes-last="never" delimiter=", "/>
      <substitute>
        <text value="Anon."/>
      </substitute>
    </names>
  </macro>
  <macro name="year-date">
    <date variable="issued">
      <date-part name="year"/>
    </date>
  </macro>
  <macro name="edition">
    <choose>
      <if is-numeric="edition">
        <group delimiter=" ">
          <number variable="edition" form="ordinal"/>
          <text term="edition" form="short" suffix="." strip-periods="true"/>
        </group>
      </if>
      <else>
        <text variable="edition" suffix="."/>
      </else>
    </choose>
  </macro>
  <citation et-al-min="3" et-al-use-first="1">
    <layout prefix="(" suffix=")" delimiter="; ">
      <group delimiter=", ">
        <text macro="author"/>
        <text macro="year-date"/>
      </group>
    </layout>
  </citation>
  <bibliography>
    <sort>
      <key macro="author"/>
    </sort>
    <layout>
      <text macro="author" suffix=","/>
      <date variable="issued" prefix=" " suffix=".">
        <date-part name="year"/>
      </date>
      <group prefix=" " delimiter=" " suffix=".">
        <text variable="title" font-style="italic"/>
        <text macro="edition"/>
      </group>
      <group prefix=" " delimiter=": " suffix=".">
        <text variable="publisher-place"/>
        <text variable="publisher"/>
      </group>
    </layout>
  </bibliography>
</style>
"""


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
            bib_style = CitationStylesStyle("harvard1", lg, validate=False)
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
        """Styles with an embedded locale that defines no ordinal terms must still
        produce correct ordinals by falling back to the file-based locale data.
        Regression test for https://github.com/citeproc-py/citeproc-py/issues/183."""
        style_xml = io.BytesIO(HARVARD1_WITH_EMBEDDED_EN_LOCALE.encode("utf-8"))
        bib_style = CitationStylesStyle(style_xml, "en-US", validate=False)

        entries = []
        for edition in range(1, 5):
            entry = template.copy()
            entry["id"] = str(edition)
            entry["edition"] = edition
            entries.append(entry)

        bib = source.json.CiteProcJSON(entries)
        bibliography = CitationStylesBibliography(bib_style, bib, formatter.plain)
        citations = [CitationItem(str(x)) for x in range(1, 5)]
        bibliography.register(Citation(citations))
        rendered = bibliography.style.render_bibliography(citations)

        # Extract the ordinal token (6th whitespace-delimited word)
        ordinals = [r.split()[5] for r in rendered]
        assert ordinals[0] == "1st", f"Expected '1st', got '{ordinals[0]}'"
        assert ordinals[1] == "2nd", f"Expected '2nd', got '{ordinals[1]}'"
        assert ordinals[2] == "3rd", f"Expected '3rd', got '{ordinals[2]}'"
        assert ordinals[3] == "4th", f"Expected '4th', got '{ordinals[3]}'"
