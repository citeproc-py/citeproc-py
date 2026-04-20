from pathlib import Path

import importlib.resources as resources

from warnings import warn

from lxml import etree

from . import SCHEMA_PATH, LOCALES, STYLES
from .model import CitationStylesElement
from .formatter import html


class CitationStylesXML(object):
    def __init__(self, f, validate=True):
        lookup = etree.ElementNamespaceClassLookup()
        namespace = lookup.get_namespace('http://purl.org/net/xbiblio/csl')
        namespace[None] = CitationStylesElement
        namespace.update(dict([(cls.__name__.replace('_', '-').lower(), cls)
                               for cls in CitationStylesElement.__subclasses__()]))

        self.parser = etree.XMLParser(remove_comments=True, encoding='UTF-8',
                                      no_network=True)
        self.parser.set_element_class_lookup(lookup)
        self.xml = etree.parse(f, self.parser)#, base_url=".")
        if validate:
            self.schema = etree.RelaxNG(etree.parse(SCHEMA_PATH))
            if not self.schema.validate(self.xml):
                err = self.schema.error_log
                #raise Exception("XML file didn't pass schema validation:\n%s" % err)
                warn("XML file didn't pass schema validation:\n%s" % err)
                # TODO: proper error reporting
        self.root = self.xml.getroot()


class CitationStylesLocale(CitationStylesXML):
    def __init__(self, locale, validate=True):
        locale_path = resources.files(LOCALES) / 'locales-{}.xml'.format(locale)
        try:
            super(CitationStylesLocale, self).__init__(locale_path,
                                                       validate=validate)
        except IOError:
            raise ValueError("'{}' is not a known locale".format(locale))


class CitationStylesStyle(CitationStylesXML):
    def __init__(self, style, locale=None, validate=True):
        style_src = None

        try:
            # lxml can take file-like objects, so check if we are dealing with
            # strings first
            if not isinstance(style, str):
                pass  # pass through for a generic handling below
            # It could still be a URL etc, first check if style is a path that exists
            elif os.path.exists(style):
                style_src = style
            else:
                # Try bundled styles
                bundled_path = os.path.join(STYLES_PATH, f'{style}.csl')
                if os.path.exists(bundled_path):
                    style_src = bundled_path
                else:
                    # Try to load from citeproc-py-styles if available
                    try:
                        import citeproc_styles
                    except ImportError:
                        # citeproc-py-styles not installed, raise with helpful message
                        raise ValueError(
                            f"'{style}' not found in bundled styles ({STYLES_PATH}). "
                            f"To access more styles, install the citeproc-py-styles package with: "
                            f"pip install citeproc-py-styles"
                        )
                    try:
                        from citeproc_styles import get_style_filepath
                        style_src = get_style_filepath(style)
                    except (KeyError, FileNotFoundError):
                        # Style not found in citeproc-py-styles
                        raise ValueError(
                            f"'{style}' not found in bundled styles ({bundled_path}) "
                            f"or in citeproc-py-styles package"
                        )
        except TypeError:
            pass

        if style_src is None:
            if style:
                # Assume it's a file-like object or string containing XML data
                style_src = style
            else:
                # If we couldn't find the style anywhere, raise an error
                raise ValueError(f"'{style}' is not a known style")

        try:
            super(CitationStylesStyle, self).__init__(
                style_src, validate=validate)
        except IOError:
            raise ValueError(f"'{style}' is not a known style")
        if locale is None:
            locale = self.root.get('default-locale', 'en-US')
        self.root.set_locale_list(locale, validate=validate)

    def has_bibliography(self):
        return self.root.bibliography is not None

    def render_citation(self, citation, cites, callback=None):
        return self.root.citation.render(citation, cites, callback)

    def sort_bibliography(self, citation_items):
        return self.root.bibliography.sort(citation_items)

    def render_bibliography(self, citation_items):
        return self.root.bibliography.render(citation_items)


class CitationStylesBibliography(object):
    def __init__(self, style, source, formatter=html):
        self.style = style
        self.source = source
        self.formatter = self.style.root.formatter = formatter
        self.keys = []
        self.items = []
        self._cites = []

    def register(self, citation, callback=None):
        citation.bibliography = self
        for item in citation.cites:
            if item.key in self.source:
                if item.key not in self.keys:
                    self.keys.append(item.key)
                    self.items.append(item)
            elif callback is not None:
                callback(item)

    def sort(self):
        self.items = self.style.sort_bibliography(self.items)
        self.keys = [item.key for item in self.items]

    def cite(self, citation, callback):
        return self.style.render_citation(citation, self._cites, callback)

    def bibliography(self):
        return self.style.render_bibliography(self.items)
