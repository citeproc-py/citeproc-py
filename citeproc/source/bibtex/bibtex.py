
import re
import unicodedata

from warnings import warn

from ...types import (ARTICLE, ARTICLE_JOURNAL, BOOK, CHAPTER, MANUSCRIPT,
                      PAMPHLET, PAPER_CONFERENCE, REPORT, THESIS)
from ...string import String, MixedString, NoCase
from .. import BibliographySource, Reference, Name, Date, DateRange
from .bibparse import BibTeXParser
from .latex import parse_latex
from .latex.macro import NewCommand, Macro


class BibTeX(BibliographySource):
    fields = {'abstract': 'abstract',
              'address': 'publisher_place',
              'annote': 'annote',
              'author': 'author',
              'booktitle': 'container_title',
              'chapter': 'chapter_number',
              'doi': 'DOI',
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
              'pmid': 'PMID',
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

    types = {# standard entry types
             'article': ARTICLE_JOURNAL,
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
             'unpublished': MANUSCRIPT,

             # non-standard entry types
             'thesis': THESIS,
             'report': REPORT,
             }

    def __init__(self, filename, encoding='ascii'):
        bibtex_database = BibTeXParser(filename, encoding)
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
                value = value.strip()
            except AttributeError:
                pass
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
                value = self._bibtex_to_csl_pages(value)
            elif field in ('author', 'editor'):
                value = [name for name in self._parse_author(value)]
            else:
                try:
                    value = self._parse_string(value)
                except TypeError:
                    value = str(value)
            csl_dict[csl_field] = value
        return csl_dict

    @staticmethod
    def _bibtex_to_csl_pages(value):
        value = value.replace(' ', '')
        if '-' in value:
            try:
                first, last = value.split('--')
            except ValueError:
                first, last = value.split('-')
            pages = '-'.join((first, last))
        else:
            pages = value[:-1] if value.endswith('+') else value
        return pages

    def _bibtex_to_csl_date(self, bibtex_entry):
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

    MONTHS = ('jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    RE_DAY = r'(?P<day>\d+)'
    RE_MONTH = r'(?P<month>\w+)'

    @staticmethod
    def _parse_month(month):
        def month_name_to_index(name):
            try:
                return BibTeX.MONTHS.index(name[:3].lower()) + 1
            except ValueError:
                return int(name)

        begin = {}
        end = {}
        month = month.strip()
        month = month.replace(', ', '-')
        if month.isdecimal():
            begin['month'] = end['month'] = month
        elif month.replace('-', '').isalpha():
            if '-' in month:
                begin['month'], end['month'] = month.split('-')
            else:
                begin['month'] = end['month'] = month
        else:
            m = re.match(BibTeX.RE_DAY + '[ ~]*' + BibTeX.RE_MONTH, month)
            if m is None:
                m = re.match(BibTeX.RE_MONTH + '[ ~]*' + BibTeX.RE_DAY, month)
            begin['day'] = end['day'] = int(m.group('day'))
            begin['month'] = end['month'] = m.group('month')
        begin['month'] = month_name_to_index(begin['month'])
        end['month'] = month_name_to_index(end['month'])
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
        csl_authors = []
        for author in split_names(authors):
            first, von, last, jr = parse_name(author)
            csl_parts = {}
            for part, csl_label in [(first, 'given'),
                                    (von, 'non-dropping-particle'),
                                    (last, 'family'),
                                    (jr, 'suffix')]:
                if part is not None:
                    csl_parts[csl_label] = parse_latex(part,
                                                       self.preamble_macros)
            name = Name(**csl_parts)
            csl_authors.append(name)
        return csl_authors

    def create_reference(self, key, bibtex_entry):
        csl_type = self.types[bibtex_entry.document_type]
        csl_fields = self._bibtex_to_csl(bibtex_entry)
        csl_date = self._bibtex_to_csl_date(bibtex_entry)
        if csl_date:
            csl_fields['issued'] = csl_date
        return Reference(key, csl_type, **csl_fields)


# BibTeX name handling
#
# references
#  - BibTeXing by Oren Patashnik (Feb 8, 1988), 4. Helpful Hints, item 18
#    (BibTeX 0.99d - http://www.ctan.org/tex-archive/biblio/bibtex/base/btxdoc.pdf)
#  - A summary of BibTex by Xavier Décoret
#    (http://maverick.inria.fr/~Xavier.Decoret/resources/xdkbibtex/bibtex_summary.html)
#  - Tame the BeaST by Nicolas Markey
#    (http://tug.ctan.org/info/bibtex/tamethebeast/ttb_en.pdf)

AND = ' and '

def split_names(string):
    """Split a string of names separated by 'and' into a list of names."""
    brace_level = 0
    names = []
    last_index = 0
    for i in range(len(string)):
        char = string[i]
        if brace_level == 0 and string[i:].startswith(AND):
            names.append(string[last_index:i])
            last_index = i + len(AND)
        elif char == '{':
            brace_level += 1
        elif char == '}':
            brace_level -= 1
    last_name = string[last_index:]
    if last_name:
        names.append(last_name)
    return names


def parse_name(name):
    """Parse a BibTeX name string and split it into First, von, Last and Jr
    parts.
    """
    parts = split_name(name)
    if len(parts) == 1:       # First von Last
        first_von_last, = parts
        index = 0
        first, jr = [], []
        for word in first_von_last[:-1]:
            if is_capitalized(word) not in (True, None):
                break
            first.append(word)
            index += 1
        von_last = first_von_last[index:]
    elif len(parts) == 2:     # von Last, First
        jr = []
        von_last, first = parts
    elif len(parts) == 3:     # von Last, Jr, First
        von_last, jr, first = parts
    von, last = split_von_last(von_last)
    join = ' '.join
    return join(first) or None, join(von) or None, join(last), join(jr) or None


def split_name(name):
    """Split a name in into parts delimited by commas (at brace-level 0), and
    each part into words.

    Returns a list of of lists of words.
    """
    brace_level = 0
    parts = []
    current_part = []
    word = ''
    for char in name:
        if char in ' \t,':
            if brace_level == 0:
                if word:
                    current_part.append(word)
                    word = ''
                if char == ',':
                    parts.append(current_part)
                    current_part = []
                continue
        elif char == '{':
            brace_level += 1
        elif char == '}':
            brace_level -= 1
        word += char
    if word:
        current_part.append(word)
        parts.append(current_part)
    return parts


def is_capitalized(string):
    """Check if a BibTeX substring is capitalized.

    A string can be "case-less", in which case `None` is returned.
    """
    brace_level = 0
    special_char = False
    for char, next_char in lookahead_iter(string):
        if (brace_level == 0 or special_char) and char.isalpha():
            return char.isupper()
        elif char == '{':
            brace_level += 1
            if brace_level == 1 and next_char == '\\':
                special_char = True
        elif char == '}':
            brace_level -= 1
            if brace_level == 0:
                special_char = False
    return None  # case-less


def split_von_last(words):
    """Split "von Last" name into von and Last parts."""
    if len(words) > 1 and is_capitalized(words[0]) is False:
        for j, word in enumerate(reversed(words[:-1])):
            if is_capitalized(word) not in (True, None):
                return words[:-j - 1], words[-j - 1:]
    return [], words


def lookahead_iter(iterable):
    """Iterator that also yields the next item along with each item. The next
    item is `None` when yielding the last item.
    """
    items = iter(iterable)
    item = next(items)
    for next_item in items:
        yield item, next_item
        item = next_item
    yield item, None


EN_DASH = unicodedata.lookup('EN DASH')
