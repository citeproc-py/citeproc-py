from io import BytesIO
from unittest import TestCase

from citeproc import (
    Citation,
    CitationItem,
    CitationStylesBibliography,
    CitationStylesStyle,
    formatter,
)
from citeproc.source.json import CiteProcJSON


class TestSubstitute(TestCase):
    def render(self, bibliography):
        return [str(entry) for entry in bibliography.bibliography()]

    def bibliography(self, substitute, entries=None, macros='', following=None):
        if entries is None:
            entries = [{'id': 'ITEM-1', 'type': 'webpage', 'title': 'The title'}]
        if following is None:
            following = '<text variable="title"/>'
        style = f'''<style xmlns="http://purl.org/net/xbiblio/csl"
                           version="1.0" class="in-text">
          <info><title>Substitution test</title><id>https://example.org/substitute</id></info>
          <macro name="title"><text variable="title"/></macro>
          {macros}
          <citation><layout><text variable="title"/></layout></citation>
          <bibliography><layout><group delimiter=" | ">
            <names variable="author"><name/><substitute>{substitute}</substitute></names>
            {following}
          </group></layout></bibliography>
        </style>'''
        parsed = CitationStylesStyle(BytesIO(style.encode()), locale='en-US', validate=False)
        bibliography = CitationStylesBibliography(parsed, CiteProcJSON(entries), formatter.plain)
        for entry in entries:
            bibliography.register(Citation([CitationItem(entry['id'])]))
        return bibliography

    def test_title_substituted_through_a_macro_is_suppressed_later(self):
        bibliography = self.bibliography('<text macro="title"/>')

        self.assertEqual(self.render(bibliography), ['The title'])

    def test_title_substituted_through_a_group_is_suppressed_later(self):
        bibliography = self.bibliography('<group><text macro="title"/></group>')

        self.assertEqual(self.render(bibliography), ['The title'])

    def test_direct_substitution_still_suppresses_the_variable(self):
        bibliography = self.bibliography('<text variable="title"/>')

        self.assertEqual(self.render(bibliography), ['The title'])

    def test_a_missing_candidate_falls_through_to_the_next_one(self):
        bibliography = self.bibliography('<text variable="publisher"/><text macro="title"/>')

        self.assertEqual(self.render(bibliography), ['The title'])

    def test_only_the_selected_branch_is_suppressed(self):
        bibliography = self.bibliography(
            '<text macro="choose-title"/>',
            entries=[{
                'id': 'ITEM-1', 'type': 'webpage', 'title': 'The title',
                'container-title': 'The journal',
            }],
            macros='''<macro name="choose-title"><choose>
              <if type="webpage"><text variable="title"/></if>
              <else><text variable="container-title"/></else>
            </choose></macro>''',
            following='<text variable="title"/><text variable="container-title"/>',
        )

        self.assertEqual(self.render(bibliography), ['The title | The journal'])

    def test_repeated_variables_within_the_substitute_are_kept(self):
        bibliography = self.bibliography(
            '<group delimiter=" / "><text variable="title"/><text macro="title"/></group>',
        )

        self.assertEqual(self.render(bibliography), ['The title / The title'])

    def test_nested_substitutes_suppress_their_rendered_variables(self):
        bibliography = self.bibliography('''
          <names variable="editor"><name/><substitute>
            <text macro="title"/>
          </substitute></names>
        ''')

        self.assertEqual(self.render(bibliography), ['The title'])

    def test_a_substitution_does_not_affect_another_item_or_render(self):
        bibliography = self.bibliography('<text macro="title"/>', entries=[
            {'id': 'ITEM-1', 'type': 'webpage', 'title': 'The title'},
            {'id': 'ITEM-2', 'type': 'webpage', 'title': 'Another title',
             'author': [{'literal': 'An author'}]},
        ])

        expected = ['The title', 'An author | Another title']
        self.assertEqual(self.render(bibliography), expected)
        self.assertEqual(self.render(bibliography), expected)
        citation = Citation([CitationItem('ITEM-1')])
        bibliography.register(citation)
        self.assertEqual(str(bibliography.cite(citation, lambda _: None)), 'The title')

    def test_apa_bibliography_renders_an_authorless_title_once(self):
        cases = (
            ('article-journal', 'A study of things. (2019). <i>Journal of Things</i>.'),
            ('webpage', '<i>A study of things</i>. (2019). Journal of Things.'),
        )
        for item_type, expected in cases:
            for authors in ({}, {'author': []}):
                with self.subTest(item_type=item_type, authors=authors):
                    item = {
                        'id': 'ITEM-1', 'type': item_type,
                        'title': 'A study of things', 'container-title': 'Journal of Things',
                        'issued': {'date-parts': [[2019]]}, **authors,
                    }
                    style = CitationStylesStyle('apa', locale='en-US', validate=False)
                    bibliography = CitationStylesBibliography(style, CiteProcJSON([item]), formatter.html)
                    citation = Citation([CitationItem(item['id'])])
                    bibliography.register(citation)

                    text, = self.render(bibliography)
                    self.assertEqual(text, expected)
