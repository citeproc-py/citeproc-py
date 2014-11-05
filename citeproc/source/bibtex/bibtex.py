
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *

import re
import unicodedata

from warnings import warn

from ...types import (ARTICLE, ARTICLE_JOURNAL, BOOK, CHAPTER, MANUSCRIPT,
                      PAMPHLET, PAPER_CONFERENCE, REPORT, THESIS)
from ...string import String, MixedString, NoCase
from .. import BibliographySource, Reference, Name, Date, DateRange, Pages
from .bibparse import BibTeXParser
from .latex import parse_latex
from .latex.macro import NewCommand, Macro


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
        bibtex_database = BibTeXParser(filename)
        self.preamble_macros = {}
        parse_latex(bibtex_database.preamble,
                    {'newcommand': NewCommand(self.preamble_macros),
                     'mbox': Macro(1, '{0}'),
                     'cite': Macro(1, 'CITE({0})')})
        for key, entry in bibtex_database.items():
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
                if value.endswith('+'):
                    value = Pages(first=int(value[:-1]))
                else:
                    first, last = value.replace(' ', '').split('--')
                    value = Pages(first=int(first), last=int(last))
            elif field in ('author', 'editor'):
                value = [name for name in self._parse_author(value)]
            else:
                try:
                    value = self._parse_string(value)
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
        try:
            year_str = parse_latex(year, self.preamble_macros)
        except TypeError:
            year_str = str(year)
        if EN_DASH in year_str:
            begin_year, end_year = year_str.split(EN_DASH)
            begin_len, end_len = len(begin_year), len(end_year)
            if end_len < begin_len:
                end_year = begin_year[:begin_len - end_len] + end_year
        else:
            begin_year = end_year = int(year_str)
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

    def _parse_string(self, title):
        def make_string(string, top_level_group=False):
            unlatexed = parse_latex(string, self.preamble_macros)
            fixed_case = top_level_group and not string.startswith('\\')
            string_cls = NoCase if fixed_case else String
            return string_cls(unlatexed)

        output = MixedString()
        level = 0
        string = ''
        for char in title:
            if char == '{':
                if level == 0:
                    if string:
                        output += make_string(string)
                        string = ''
                level += 1
            elif char == '}':
                level -= 1
                if level == 0:
                    output += make_string(string, True)
                    string = ''
            else:
                string += char
        if level != 0:
            raise SyntaxError('Non-matching braces in "{}"'.format(title))
        if string:
            output += make_string(string)
        return output

    def _parse_author(self, authors):
        # TODO: implement proper parsing
        csl_authors = []
        for author in authors.split(' and '):
            if ',' in author:
                family, given = [a.strip() for a in  author.split(',', 1)]
                name = Name(family=family, given=given)
            elif ' ' in author:
                given, family = [a.strip() for a in author.rsplit(' ', 1)]
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


EN_DASH = unicodedata.lookup('EN DASH')
