
import re

from warnings import warn

from ...types import (ARTICLE, ARTICLE_JOURNAL, BOOK, CHAPTER, MANUSCRIPT,
                      PAMPHLET, PAPER_CONFERENCE, REPORT, THESIS)
from ...string import String, MixedString, NoCase
from .. import BibliographySource, Reference, Name, Date, DateRange
from .bibparse import BibTeXParser


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
             'proceedings': BOOK,
             'techreport': REPORT,
             'unpublished': MANUSCRIPT}

    def __init__(self, filename):
        for key, entry in BibTeXParser(filename).items():
            self.add(self.create_reference(key, entry))

    def _bibtex_to_csl(self, bibtex_entry):
        csl_dict = {}
        for field, value in bibtex_entry.items():
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
                try:
                    value = self._parse_title(value)
                except TypeError:
                    value = str(value)
            csl_dict[csl_field] = value
        return csl_dict

    def _bibtex_to_csl_date(self, bibtex_entry):
        is_range = False
        if 'month' in bibtex_entry:
            begin_dict, end_dict = self._parse_month(bibtex_entry['month'])
        else:
            begin_dict, end_dict = {}, {}
        if 'year' in bibtex_entry:
            begin_dict['year'], end_dict['year'] \
                = self._parse_year(bibtex_entry['year'])
        if not begin_dict:
            return None
        if begin_dict == end_dict:
            return Date(**begin_dict)
        else:
            return DateRange(begin=Date(**begin_dict), end=Date(**end_dict))

    def _parse_year(self, year):
        year = str(year).replace('--', '-')
        if '-' in year:
            begin_year, end_year = year.split('-')
            begin_len, end_len = len(begin_year), len(end_year)
            if end_len < begin_len:
                end_year = begin_year[:begin_len - end_len] + end_year
        else:
            begin_year = end_year = int(year)
        return begin_year, end_year

    months = ('jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep',
              'oct', 'nov', 'dec')

    def _parse_month(self, month):
        begin = {}
        end = {}
        month = month.strip()
        month = month.replace(', ', '-')
        if month.replace('-', '').isalpha():
            if '-' in month:
                begin['month'], end['month'] = month.split('-')
            else:
                begin['month'] = end['month'] = month
        else:
            m = re.match('(?P<day>\d+)[ ~]*(?P<month>\w+)', month)
            begin['day'] = end['day'] = m.group('day')
            begin['month'] = end['month'] = m.group('month')
        begin['month'] = self.months.index(begin['month'][:3].lower())
        end['month'] = self.months.index(end['month'][:3].lower())
        return begin, end

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
                        string += char
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
        csl_type = self.types[bibtex_entry.document_type]
        csl_fields = self._bibtex_to_csl(bibtex_entry)
        csl_date = self._bibtex_to_csl_date(bibtex_entry)
        if csl_date:
            csl_fields['issued'] = csl_date
        return Reference(key, csl_type, **csl_fields)
