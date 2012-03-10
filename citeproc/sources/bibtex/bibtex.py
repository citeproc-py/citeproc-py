
from warnings import warn

from ...types import (ARTICLE, ARTICLE_JOURNAL, BOOK, PAPER_CONFERENCE, REPORT,
                      THESIS)
from ...source import BibliographySource, Reference, Name, Date
from .bibparse import parse_bib



class BibTeX(BibliographySource):
    fields = {'title': 'title',
              'author': 'author',
              'editor': 'editor',
              'journal': 'container_title',
              'volume': 'volume',
              'number': 'number',
              'pages': 'page',
              'note': 'note',
              'publisher': 'publisher',
              'address': 'publisher_place',
              'edition': 'edition',
              'booktitle': 'container_title',
              'series': 'collection_title',
              }

    types = {'article': ARTICLE_JOURNAL,
             'inproceedings': PAPER_CONFERENCE,
             'book': BOOK,
             'misc': ARTICLE,
             'phdthesis': THESIS,
             'conference': PAPER_CONFERENCE,
             'manual': BOOK,
             'techreport': REPORT,
             }

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
            if csl_field in ('number', 'volume'):
                try:
                    value = int(value)
                except ValueError:
                    pass
            elif csl_field == 'page':
                value = value.replace(' ', '').replace('--', '-')
            elif csl_field in ('author', 'editor'):
                value = [name for name in self._parse_author(value)]
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

    def _parse_author(self, authors):
        # TODO: implement proper parsing
        csl_authors = []
        for author in authors.split(' and '):
            try:
                family, given = map(str.strip, author.split(',', 1))
                name = Name(family=family, given=given)
            except:
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
