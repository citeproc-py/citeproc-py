
import os
import json

from . import types, formatter


DATA_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')

SCHEMA_PATH = os.path.join(DATA_PATH, 'schema', 'csl.rng')
LOCALES_PATH = os.path.join(DATA_PATH, 'locales')
STYLES_PATH = os.path.join(DATA_PATH, 'styles')


NAMES = ['author', 'collection_editor', 'composer', 'container_author',
         'editor', 'editorial_director', 'illustrator', 'interviewer',
         'original_author', 'recipient', 'translator']

DATES = ['accessed', 'container', 'event_date', 'issued', 'original_date',
         'submitted']

NUMBERS = ['chapter_number', 'collection_number', 'edition', 'issue', 'number',
           'number_of_pages', 'number_of_volumes', 'volume']

VARIABLES = (['abstract', 'annote', 'archive', 'archive_location',
              'archive_place', 'authority', 'call_number', 'citation_label',
              'citation_number', 'collection_title', 'container_title',
              'container_title_short', 'dimensions', 'DOI', 'event',
              'event_place', 'first_reference_note_number', 'genre', 'ISBN',
              'ISSN', 'jurisdiction', 'keyword', 'language', 'locator',
              'medium', 'note', 'original_publisher',
              'original_publisher_place', 'original_title', 'page',
              'page_first', 'PMCID', 'PMID', 'publisher', 'publisher_place',
              'references', 'section', 'source', 'status', 'title',
              'title_short', 'URL', 'version', 'year_suffix'] +
             NAMES + DATES + NUMBERS)

with open(os.path.join(LOCALES_PATH, 'locales.json'),
          encoding='utf-8') as file:
    locales_json = json.load(file)
    PRIMARY_DIALECTS = locales_json['primary-dialects']
    LANGUAGE_NAMES = locales_json['language-names']


from .frontend import CitationStylesStyle, CitationStylesBibliography
from .source import Citation, CitationItem, Locator
