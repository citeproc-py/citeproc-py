
from ... import types
from ... import BibliographySource, Reference, Name, Date
from .bibparse import parse_bib



class BibTeX(BibliographySource):
    # TODO: these can probably be merged
    # see http://feedback.mendeley.com/forums/4941-mendeley-feedback/suggestions/281656-csl-documentation
    conversion_tables = {'article': [('title', 'title'),
                                     ('journal', 'container_title'),
                                     ('volume', 'volume'),
                                     ('number', 'number'),
                                     ('pages', 'page'),
                                     ('note', 'note')],
                         'book': [('title', 'title'),
                                  ('publisher', 'publisher'),
                                  ('volume', 'volume'),
                                  ('number', 'number'),
                                  ('address', 'publisher_place'),
                                  ('edition', 'edition'),
                                  ('note', 'note')],
                         'inproceedings': [('title', 'title'),
                                           ('booktitle', 'container_title'),
                                           ('volume', 'volume'),
                                           ('number', 'number'),
                                           ('pages', 'page'),
                                           ('series', 'collection_title'),
                                           #('organization', None),
                                           ('publisher', 'publisher'),
                                           ('address', 'publisher_place'),
                                           ('note', 'note')]}

    date_conversion = [('year', 'year'),
                       ('month', 'month')]

    def __init__(self, filename):
        for key, entry in parse_bib(filename).items():
            self.add(self.create_reference(key, entry))

    def _bibtex_to_csl(self, bibtex_entry):
        csl_dict = {}
        for bibtex_key, csl_key in self.conversion_tables[bibtex_entry.btype]:
            if bibtex_key in bibtex_entry.data:
                value = bibtex_entry.data[bibtex_key]
                if csl_key in ('number', 'volume'):
                    value = int(value)
                elif csl_key == 'page':
                    value = value.replace(' ', '').replace('--', '-')
                csl_dict[csl_key] = value
        return csl_dict

    def _bibtex_to_csl_date(self, bibtex_entry):
        date_dict = {}
        for bibtex_key, date_key in self.date_conversion:
            if bibtex_key in bibtex_entry.data:
                date_dict[date_key] = bibtex_entry.data[bibtex_key]
        return date_dict

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
        # TODO: merge or encapsulate
        if bibtex_entry.btype == 'article':
            csl_keys = self._bibtex_to_csl(bibtex_entry)
            date_keys = self._bibtex_to_csl_date(bibtex_entry)
            date = Date(**date_keys)
            authors = []
            for name in self._parse_author(bibtex_entry.data['author']):
                authors.append(name)
            return Reference(key, types.ARTICLE_JOURNAL, issued=date,
                             author=authors, **csl_keys)
        elif bibtex_entry.btype == 'book':
            csl_keys = self._bibtex_to_csl(bibtex_entry)
            date_keys = self._bibtex_to_csl_date(bibtex_entry)
            date = Date(**date_keys)
            authors = []
            for name in self._parse_author(bibtex_entry.data['author']):
                authors.append(name)
            if 'editor' in bibtex_entry.data:
                editors = []
                for name in self._parse_author(bibtex_entry.data['editor']):
                    editors.append(name)
                csl_keys['editor'] = editors
            return Reference(key, types.BOOK, issued=date, author=authors,
                             **csl_keys)
        elif bibtex_entry.btype == 'inproceedings':
            csl_keys = self._bibtex_to_csl(bibtex_entry)
            date_keys = self._bibtex_to_csl_date(bibtex_entry)
            date = Date(**date_keys)
            authors = []
            for name in self._parse_author(bibtex_entry.data['author']):
                authors.append(name)
            if 'editor' in bibtex_entry.data:
                editors = []
                for name in self._parse_author(bibtex_entry.data['editor']):
                    editors.append(name)
                csl_keys['editor'] = editors
            return Reference(key, types.ARTICLE_JOURNAL, issued=date,
                             author=authors, **csl_keys)
        else:
            raise NotImplementedError
