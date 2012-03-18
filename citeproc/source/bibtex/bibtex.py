
from warnings import warn

from ...types import (ARTICLE, ARTICLE_JOURNAL, BOOK, CHAPTER, MANUSCRIPT,
                      PAMPHLET, PAPER_CONFERENCE, REPORT, THESIS)
from ...string import String, MixedString, NoCase
from .. import BibliographySource, Reference, Name, Date
from .bibparse import parse_bib


class BibTeX(BibliographySource):
    fields = {'address': 'publisher_place',
              'annote': 'annote',
              'author': 'author',
              'booktitle': 'container_title',
              'chapter': 'chapter_number',
              'edition': 'edition',
              'editor': 'editor',
#              'howpublished': None,
#              'institution': None,
              'journal': 'container_title',
#              'month': None,
              'note': 'note',
              'number': 'issue',
#              'organization': None,
              'pages': 'page',
              'publisher': 'publisher',
#              'school': None,
              'series': 'collection_title',
              'title': 'title',
#              'type': None,
#              'year': None,
              'volume': 'volume',

              # non-standard fields
              'isbn': 'ISBN',
              'issn': 'ISSN'}

    types = {'article': ARTICLE_JOURNAL,
             'book': BOOK,
             'booklet': PAMPHLET,
             'conference': PAPER_CONFERENCE,
             'inbook': CHAPTER,
             'incollection': ARTICLE_JOURNAL,
             'inproceedings': PAPER_CONFERENCE,
             'manual': BOOK,
             'mastersthesis': THESIS,
             'misc': ARTICLE,
             'phdthesis': THESIS,
             'techreport': REPORT,
             'unpublished': MANUSCRIPT}

    def __init__(self, filename):
        for key, entry in parse_bib(filename).items():
            self.add(self.create_reference(key, entry))

    def _bibtex_to_csl(self, bibtex_entry):
        csl_dict = {}
        for field, value in bibtex_entry.data.items():
            try:
                csl_field = self.fields[field]
            except KeyError:
                if field not in ('year', 'month', 'filename'):
                    warn("Unsupported BibTeX field '{}'".format(field))
                continue
            if field in ('number', 'volume'):
                try:
                    value = int(value)
                except ValueError:
                    pass
            elif field == 'pages':
                value = value.replace(' ', '').replace('--', '-')
            elif field in ('author', 'editor'):
                value = [name for name in self._parse_author(value)]
            else:
                value = self._parse_title(value)
            csl_dict[csl_field] = value
        return csl_dict

    def _bibtex_to_csl_date(self, bibtex_entry):
        date_dict = {}
        if 'month' in bibtex_entry.data:
            date_dict['month'] = self._parse_month(bibtex_entry.data['month'])
        if 'year' in bibtex_entry.data:
            date_dict['year'] = bibtex_entry.data['year']
        return date_dict

    months = ('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep',
              'oct', 'nov', 'dec')

    def _parse_month(self, month):
        return self.months.index(month[:3].lower())

    math_map = {'mu': 'µ'}

    def _parse_title(self, title):
        output = MixedString()
        escape = False
        math = False
        math_escape = False
        math_escape_string = None
        level = 0
        string = ''
        for i, char in enumerate(title):
            if escape:
                string += char
                escape = False
            elif math:
                if char == ' ':
                    if math_escape_string:
                        string += self.math_map[math_escape_string]
                elif char == '$':
                    if math_escape_string:
                        string += self.math_map[math_escape_string]
                    math = False
                else:
                    if char == '\\':
                        if math_escape_string:
                            string += self.math_map[math_escape_string]
                        math_escape = True
                        math_escape_string = ''
                    else:
                        math_escape_string += char
            elif char == '$':
                math = True
                math_string = ''
            elif char == '\\':
                escape = True
            elif char == '{':
                if level == 0:
                    if string:
                        output += String(string)
                        string = ''
                level += 1
            elif char == '}':
                level -= 1
                if level == 0:
                    output += NoCase(string)
                    string = ''
            else:
                string += char
            prev_char = char
        if level != 0:
            raise SyntaxError('Non-matching braces in "{}"'.format(title))
        if string:
            output += String(string)
        return output

    def _parse_author(self, authors):
        # TODO: implement proper parsing
        csl_authors = []
        for author in authors.split(' and '):
            if ',' in author:
                family, given = map(str.strip, author.split(',', 1))
                name = Name(family=family, given=given)
            elif ' ' in author:
                given, family = map(str.strip, author.rsplit(' ', 1))
                name = Name(family=family, given=given)
            else:
                # TODO: handle 'others'
                name = Name(name=author)
            csl_authors.append(name)
        return csl_authors

    def create_reference(self, key, bibtex_entry):
        csl_type = self.types[bibtex_entry.btype]
        csl_fields = self._bibtex_to_csl(bibtex_entry)
        date_keys = self._bibtex_to_csl_date(bibtex_entry)
        if date_keys:
            csl_fields['issued'] = Date(**date_keys)
        return Reference(key, csl_type, **csl_fields)
