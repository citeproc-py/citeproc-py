
import os
from lxml import etree, objectify

from . import type
from ...util import DATA_PATH



NAMES = ['author', 'collection_editor', 'composer', 'container_author',
         'editor', 'editorial_director', 'illustrator', 'interviewer',
         'original_author', 'recipient', 'translator']

DATES = ['accessed', 'container', 'event_date', 'issued', 'original_date',
         'submitted']

NUMBERS = ['chapter_number', 'collection_number', 'edition', 'issue', 'number',
           'number_of_pages', 'number_of_volumes', 'volume']

VARIABLES = (['abstract', 'annote', 'archive', 'archive_location',
              'archive_place', 'authority', 'call_number', 'citation_label'
              'citation_number', 'collection_title', 'container_title',
              'container_title_short', 'dimensions', 'doi', 'event',
              'event_place', 'first_reference_note_number', 'genre', 'isbn',
              'issn', 'jurisdiction', 'keyword', 'locator', 'medium', 'note',
              'original_publisher', 'original_publisher_place', 'original_title',
              'page', 'page_first', 'pmid', 'pmcid', 'publisher',
              'publisher_place', 'references', 'section', 'source', 'status',
              'title', 'title_short', 'URL', 'version', 'year_suffix'] +
             NAMES + DATES + NUMBERS)


SCHEMA_PATH = os.path.join(DATA_PATH, 'csl', 'schema', 'csl.rng')
LOCALES_PATH = os.path.join(DATA_PATH, 'csl', 'locales')
STYLES_PATH = os.path.join(DATA_PATH, 'csl', 'styles')


class LocalizedSimpleTerm(object):
    def __init__(self, string):
        self.string = string


class LocalizedCompoundTerm(object):
    def __init__(self, single, multiple):
        self.single = single
        self.multiple = multiple


class LocalizedDate(object):
    def __init__(self, parts):
        self.parts = parts


class Formatted(object):
    def __init__(self, font_style=None, font_variant=None, font_weight=None,
                 text_decoration=None, vertical_align=None):
        self.font_style = font_style
        self.font_variant = font_variant
        self.font_weight = font_weight
        self.text_decoration = text_decoration
        self.vertical_align = vertical_align


class DatePart(Formatted):
    def __init__(self, form=None, text_case=None, prefix=None, suffix=None,
                 **kwargs):
        self.form = form
        self.text_case = text_case
        super().__init__(**kwargs)


class Day(DatePart):
    pass


class Month(DatePart):
    def __init__(self, form=None, text_case=None, strip_periods=False, **kwargs):
        self.strip_periods = strip_periods
        super().__init__(form, text_case, **kwargs)


class Year(DatePart):
    pass


class Locale(object):
    def __init__(self, locale):
        locale_path = os.path.join(LOCALES_PATH, 'locales-{}.xml'.format(locale))
##        lookup = etree.ElementNamespaceClassLookup()
##        namespace = lookup.get_namespace('http://purl.org/net/xbiblio/csl')
##        namespace[None] = CustomElement
##        namespace.update(dict([(cls.__name__.lower(), cls)
##                               for cls in CustomElement.__subclasses__()]))

        self.parser = objectify.makeparser(remove_comments=True,
                                           no_network=True)
##        self.parser.set_element_class_lookup(lookup)
        self.schema = etree.RelaxNG(etree.parse(SCHEMA_PATH))
        try:
            self.xml = objectify.parse(locale_path, self.parser)#, base_url=".")
        except IOError:
            raise ValueError("'{}' is not a known locale".format(locale))
        if not self.schema.validate(self.xml):
            err = self.schema.error_log
            raise Exception("XML file didn't pass schema validation:\n%s" % err)
            # TODO: proper error reporting
        self.root = self.xml.getroot()

        self.terms = {}
        for term in self.root.terms.term:
            name = term.get('name')
            try:
                self.terms[name] = LocalizedCompoundTerm(term.single,
                                                         term.multiple)
            except AttributeError:
                self.terms[name] = LocalizedSimpleTerm(term.text)

        for date in self.root.date:
            parts = []
            for date_part in date['date-part']:
                attributes = {}
                for key, value in date_part.attrib.items():
                    if key == 'name':
                        if value == 'day':
                            cls = Day
                        elif value == 'month':
                            cls = Month
                        elif value == 'year':
                            cls = Year
                    else:
                        attributes[key.replace('-', '_')] = value
                parts.append(cls(**attributes))
            if date.get('form') == 'text':
                self.date_text = LocalizedDate(parts)
            elif date.get('form') == 'numeric':
                self.date_numeric = LocalizedDate(parts)

        punct = self.root['style-options'].get('punctuation-in-quote')
        self.options = {}
        self.options['punctuation-in-quote'] = punct.lower() == 'true'
        # TODO: use ObjectifiedElements to do the parsing?
