
import re
import unicodedata
import os

from functools import cmp_to_key
from glob import glob
from operator import itemgetter

from lxml import etree

from . import NAMES, DATES, NUMBERS, PRIMARY_DIALECTS, LANGUAGE_NAMES
from .source import VariableError, DateRange, LiteralDate
from .string import String, join


# Base class

class SomewhatObjectifiedElement(etree.ElementBase):
    nsmap = {'cs': 'http://purl.org/net/xbiblio/csl',
             'xml': 'http://www.w3.org/XML/1998/namespace'}

    # TODO: what about multiple instances of the same name?
    def __getattr__(self, name):
        return self.find('cs:' + name, self.nsmap)


class CitationStylesElement(SomewhatObjectifiedElement):
    _default_options = {# global options
                        'initialize-with-hyphen': 'true',
                        'page-range-format': None,
                        'demote-non-dropping-particle': 'display-and-sort',

                        # inheritable name(s) options
                        'and': None,
                        'delimiter-precedes-et-al': 'contextual',
                        'delimiter-precedes-last': 'contextual',
                        'et-al-min': 0,
                        'et-al-use-first': 1,
                        'et-al-subsequent-min': 0,
                        'et-al-subsequent-use-first': 1,
                        'et-al-use-last': 'false',
                        'initialize-with': None,
                        'name-as-sort-order': None,
                        'sort-separator': ', ',

                        'name-form': 'long',
                        'name-delimiter': ', ',
                        'names-delimiter': ''}

    def get_root(self):
        return self.getroottree().getroot()

    def xpath_search(self, expression):
        return self.xpath(expression, namespaces=self.nsmap)

    @property
    def loc(self):
        full_xpath = self.getroottree().getpath(self)
        xpath = ''
        tree = []
        for i, node in enumerate(full_xpath.split('/')[1:]):
            xpath += '/' + node
            element = self.xpath(xpath)[0]
            namespace, tag = element.tag.split('}', 1)
            attribs = ''.join(' {}="{}"'.format(key, value)
                               for key, value in element.attrib.items())
            tree.append('{:>4}: {}<{}{}>'.format(element.sourceline,
                                                 i * '  ', tag, attribs))
        print('\n'.join(tree))

    def get_option(self, name):
        return self.get(name, self._default_options[name])

    def get_macro(self, name):
        expression = "cs:macro[@name='{}'][1]".format(name)
        return self.get_root().xpath_search(expression)[0]

    def get_layout(self):
        return self.xpath_search('./ancestor-or-self::cs:layout[1]')[0]

    def get_formatter(self):
        if isinstance(self.get_root(), Locale):
            return self.get_root().style.formatter
        else:
            return self.get_root().formatter

    def preformat(self, text):
        return self.get_formatter().preformat(text)

    def unicode_character(self, name):
        return self.preformat(unicodedata.lookup(name))

    def render(self, *args, **kwargs):
        return self.markup(self.process(*args, **kwargs))

    # TODO: Locale methods
    def get_term(self, name, form=None):
        if isinstance(self.get_root(), Locale):
            return self.get_root().get_term(name, form)
        else:
            for locale in self.get_root().locales:
                try:
                    return locale.get_term(name, form)
                except IndexError: # TODO: create custom exception
                    continue

    def get_date(self, form):
        for locale in self.get_root().locales:
            try:
                return locale.get_date(form)
            except IndexError:
                continue

    def get_locale_option(self, name):
        for locale in self.get_root().locales:
            try:
                return locale.get_option(name)
            except IndexError:
                continue


# Top level elements

class Style(CitationStylesElement):
    def set_locale_list(self, output_locale, validate=True):
        """Set up list of locales in which to search for localizable units"""
        from .frontend import CitationStylesLocale

        self.locales = []
        system_locales_added = set()

        def add_instyle_locale(locale):
            expr = ('./cs:locale[@xml:lang="{}"]'.format(locale)
                    if locale else './cs:locale[not(@xml:lang)]')
            results = self.xpath_search(expr)
            if results:
                locale_element, = results
                self.locales.append(locale_element)

        def add_system_locale(locale):
            if locale not in system_locales_added:
                csl_locale = CitationStylesLocale(locale, validate=validate)
                self.locales.append(csl_locale.root)
                system_locales_added.add(locale)

        # 1) (in-style locale) chosen dialect
        add_instyle_locale(output_locale)
        # 2) (in-style locale) matching language
        language = output_locale.split('-')[0]
        add_instyle_locale(language)
        # 3) (in-style locale) no language set
        add_instyle_locale(None)
        # 4) (locale files) chosen or primary dialect
        if output_locale in LANGUAGE_NAMES:
            add_system_locale(output_locale)
        # 5) (locale files) fall back to primary language dialect
        if language in PRIMARY_DIALECTS:
            add_system_locale(PRIMARY_DIALECTS[language])
        # 6) (locale files) default locale (en-US)
        add_system_locale('en-US')
        for locale in self.locales:
            locale.style = self


class Locale(CitationStylesElement):
    _default_options = {'limit-day-ordinals-to-day-1': 'false',
                        'punctuation-in-quote': 'false'}

    def get_term(self, name, form=None):
        attributes = "@name='{}'".format(name)
        if form is not None:
            attributes += " and @form='{}'".format(form)
        else:
            attributes += " and not(@form)"
        expr = './cs:term[{}]'.format(attributes)
        try:
            return self.terms.xpath_search(expr)[0]
        except AttributeError:
            raise IndexError

    def get_date(self, form):
        expr = "./cs:date[@form='{}']".format(form)
        return self.xpath_search(expr)[0]

    def get_option(self, name):
        options = self.find('cs:style-options', self.nsmap)
        if options is None:
            raise IndexError
        return options.get(name, self._default_options[name])

    def get_formatter(self):
        return self.style.formatter


class FormattingInstructions(object):
    def get_option(self, name):
        if name in self._default_options:
            return self.get(name, self._default_options[name])
        else:
            return self.get(name, self.get_root().get_option(name))

    def render(self, reference):
        raise NotImplementedError


class Citation(FormattingInstructions, CitationStylesElement):
    _default_options = {# disambiguation
                        'disambiguate-add-names': False,
                        'disambiguate-add-givenname': False,
                        'givenname-disambiguation-rule': 'all-names',
                        'disambiguate-add-year-suffix': False,

                        # citation collapsing
                        'collapse': None,
                        'year-suffix-delimiter': None,
                        'after-collapse-delimiter': None,

                        # note distance
                        'near-note-distance': 5}

    def render(self, citation, cites, callback):
        self.cites = cites
        return self.layout.render_citation(citation, callback)


class Bibliography(FormattingInstructions, CitationStylesElement):
    _default_options = {# whitespace
                        'hanging-indent': False,
                        'second-field-align': None,
                        'line-spacing': 1,
                        'entry-spacing': 1,

                        # reference grouping
                        'subsequent-author-substitute': None}

    def sort(self, citation_items):
        return self.layout.sort_bibliography(citation_items)

    def render(self, citation_items):
        return self.layout.render_bibliography(citation_items)


# Style behavior

class Formatted(object):
    def format(self, string):
        if isinstance(string, (int, float)):
            string = str(string)
        text = self.font_style(string)
        text = self.font_variant(text)
        text = self.font_weight(text)
        text = self.text_decoration(text)
        text = self.vertical_align(text)
        return text

    def font_style(self, text):
        formatter = self.get_formatter()
        font_style = self.get('font-style', 'normal')
        if font_style == 'normal':
            formatted = text
        elif font_style == 'italic':
            formatted = formatter.Italic(text)
        elif font_style == 'oblique':
            formatted = formatter.Oblique(text)
        return formatted

    def font_variant(self, text):
        formatter = self.get_formatter()
        font_variant = self.get('font-variant', 'normal')
        if font_variant == 'normal':
            formatted = text
        elif font_variant == 'small-caps':
            formatted = formatter.SmallCaps(text)
        return formatted

    def font_weight(self, text):
        formatter = self.get_formatter()
        font_weight = self.get('font-weight', 'normal')
        if font_weight == 'normal':
            formatted = text
        elif font_weight == 'bold':
            formatted = formatter.Bold(text)
        elif font_weight == 'light':
            formatted = formatter.Light(text)
        return formatted

    def text_decoration(self, text):
        formatter = self.get_formatter()
        text_decoration = self.get('text-decoration', 'none')
        if text_decoration == 'none':
            formatted = text
        elif text_decoration == 'underline':
            formatted = formatter.Underline(text)
        return formatted

    def vertical_align(self, text):
        formatter = self.get_formatter()
        vertical_align = self.get('vertical-align', 'baseline')
        if vertical_align == 'baseline':
            formatted = text
        elif vertical_align == 'sup':
            formatted = formatter.Superscript(text)
        elif vertical_align == 'sub':
            formatted = formatter.Subscript(text)
        return formatted


class Affixed(object):
    def wrap(self, string):
        if string is not None:
            prefix = self.get('prefix', '')
            suffix = self.get('suffix', '')
            return prefix + string + suffix
        return None


class Delimited(object):
    def join(self, strings, default_delimiter=''):
        delimiter = self.get('delimiter', default_delimiter)
        try:
            text = join((s for s in strings if s is not None), delimiter)
        except:
            text = String('')
        return text


class Displayed(object):
    pass


class Quoted(object):
    def quote(self, string):
        piq = self.get_locale_option('punctuation-in-quote').lower() == 'true'
        if self.get('quotes', 'false').lower() == 'true':
            open_quote = self.get_term('open-quote').single
            close_quote = self.get_term('close-quote').single
            string = open_quote + string + close_quote
##            quoted_string = QuotedString(string, open_quote, close_quote, piq)
        return string


class StrippedPeriods(object):
    def strip_periods(self, string):
        strip_periods = self.get('strip-periods', 'false').lower() == 'true'
        if strip_periods:
            string = string.replace('.', '')
        return string


class TextCased(object):
    _stop_words = ['a', 'an', 'and', 'as', 'at', 'but', 'by', 'down', 'for',
                   'from', 'in', 'into', 'nor', 'of', 'on', 'onto', 'or',
                   'over', 'so', 'the', 'till', 'to', 'up', 'via', 'with',
                   'yet']

    def case(self, text, language=None):
        text_case = self.get('text-case')
        if text_case is not None:
            if language != 'en' and text_case == 'title':
                text_case = 'sentence'
            if text_case == 'lowercase':
                text = text.lower()
            elif text_case == 'uppercase':
                text = text.upper()
            elif text_case == 'capitalize-first':
                text = text.capitalize_first()
            elif text_case == 'capitalize-all':
                output = []
                for word in text.words():
                    word = word.capitalize_first()
                    output.append(word)
                text = ' '.join(output)
            elif text_case == 'title':
                output = []
                prev = ':'
                for word in text.words():
                    if not text.isupper() and not word.isupper():
                        word = word.soft_lower()
                        if (str(word) not in self._stop_words or
                            prev in (':', '.')):
                            word = word.capitalize_first()
                    prev = word[-1]
                    output.append(word)
                text = ' '.join(output)
            elif text_case == 'sentence':
                output = []
                for i, word in enumerate(text.words()):
                    if not text.isupper() and not word.isupper():
                        word = word.soft_lower()
                    if i == 0:
                        word = word.capitalize_first()
                    output.append(word)
                text = ' '.join(output)
        return text


# Locale elements

class Term(CitationStylesElement):
    @property
    def single(self):
        try:
            text = self.find('cs:single', self.nsmap).text
        except AttributeError:
            text = self.text
        text = self.preformat(text or '')
        return String(text)

    @property
    def multiple(self):
        try:
            text = self.find('cs:multiple', self.nsmap).text
        except AttributeError:
            text = self.text
        text = self.preformat(text or '')
        return String(text)


# Sorting elements

class Sort(CitationStylesElement):
    def sort(self, items, context):
        # custom sort function to push items with None keys to bottom
        def multi_key_sort(items, keys, descending):
            lst = zip(items, *keys)
            comparers = [(itemgetter(i + 1), descending[i])
                         for i in range(len(keys))]
            def mycmp(left, right):
                for getter, desc in comparers:
                    left_key, right_key = getter(left), getter(right)
                    if left_key is not None and right_key is not None:
                        try:
                            left_key = str(left_key.lower())
                            right_key = str(right_key.lower())
                        except AttributeError:
                            pass
                        try:
                            left_key, right_key = (int(str(left_key)),
                                                   int(str(right_key)))
                        except ValueError:
                            pass
                        result = (left_key > right_key) - (left_key < right_key)
                        if result:
                            return -1 * result if desc else result
                    elif left_key is not None:
                        return -1
                    elif right_key is not None:
                        return 1
                    else:
                        continue
                else:
                    return 0

            sorted_lst = sorted(lst, key=cmp_to_key(mycmp))
            return [item[0] for item in sorted_lst]

        sort_descending = []
        sort_keys = []
        for key in self.findall('cs:key', self.nsmap):
            descending = key.get('sort', 'ascending').lower() == 'descending'
            sort_descending.append(descending)
            sort_keys.append(key.sort_keys(items, context))

        return multi_key_sort(items, sort_keys, sort_descending)


class Key(CitationStylesElement):
    def sort_keys(self, items, context):
        if 'variable' in self.attrib:
            variable = self.get('variable').replace('-', '_')
            if variable in NAMES:
                sort_keys = [self._format_name(item, variable)
                             for item in items]
            elif variable in DATES:
                sort_keys = []
                for item in items:
                    date = item.reference.get(variable)
                    if date is not None:
                        sort_keys.append(date.sort_key())
                    else:
                        sort_keys.append(None)
            elif variable in NUMBERS:
                sort_keys = [self._format_number(item, variable)
                             for item in items]
            elif variable == 'citation_number':
                sort_keys = [item.number for item in items]
            else:
                sort_keys = [item.get_field(variable) for item in items]
        elif 'macro' in self.attrib:
            layout = context.get_layout()
            # override name options
            sort_options = {'name-as-sort-order': 'all'}
            for option in ('names-min', 'names-use-first', 'names-use-last'):
                if option in self.attrib:
                    name = option.replace('names', 'et-al')
                    sort_options[name] = self.get(option)
            macro = self.get_macro(self.get('macro'))
            sort_keys = []
            for item in items:
                layout.repressed = {}
                sort_key = macro.render(item, context=context,
                                        sort_options=sort_options)
                sort_keys.append(sort_key)

        return sort_keys

    def _format_name(self, item, variable):
        names = item.reference.get(variable)
        if names is not None:
            output = []
            for name in names:
                demote_ndp = self.get_root().get('demote-non-dropping-particle',
                                                 'display-and-sort').lower()
                sort_separator = self._default_options['sort-separator']

                # TODO: encapsulate in function (to share with Name)
                given, family, dp, ndp, suffix = name.parts()
                if demote_ndp in ('sort-only', 'display-and-sort'):
                    given = ' '.join([n for n in (given, dp, ndp) if n])
                else:
                    family = ' '.join([n for n in (ndp, family) if n])
                    given = ' '.join([n for n in (given, dp) if n])

                order = family, given, suffix
                output.append(sort_separator.join([n for n in order if n]))
            return ';'.join(output)
        else:
            return None

    def _format_number(self, item, variable):
        date = item.reference.get(variable)
        if date is not None:
            try:
                return str(Number.re_numeric.match(date).group(1))
            except AttributeError:
                return date
        else:
            return None


# Rendering elements

class Parent(object):
    def calls_variable(self):
        return any([child.calls_variable() for child in self.getchildren()])

    def process_children(self, item, **kwargs):
        output = []
        for child in self.iterchildren():
            try:
                text = child.process(item, **kwargs)
                if text is not None:
                    output.append(text)
            except VariableError:
                pass
        if output:
            return ''.join(output)
        else:
            return None

    def render_children(self, item, **kwargs):
        output = []
        for child in self.iterchildren():
            try:
                text = child.render(item, **kwargs)
                if text is not None:
                    output.append(text)
            except VariableError:
                pass
        if output:
            return join(output)
        else:
            return None


class Macro(CitationStylesElement, Parent):
    def process(self, item, context=None, sort_options=None):
        return self.process_children(item, context=context,
                                    sort_options=sort_options)

    def render(self, item, context=None, sort_options=None):
        return self.render_children(item, context=context,
                                    sort_options=sort_options)


class Layout(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    def render_citation(self, citation, callback):
        # first sort citation items according to bibliography order
        bibliography = citation.bibliography
        good_cites = [cite for cite in citation.cites if not cite.is_bad()]
        bad_cites = [cite for cite in citation.cites if cite.is_bad()]
        good_cites.sort(key=lambda item: bibliography.keys.index(item.key))
        # sort using citation/sort element
        if self.getparent().sort is not None:
            good_cites = self.getparent().sort.sort(good_cites, self)
        out = []
        for item in good_cites:
            self.repressed = {}
            prefix = item.get('prefix', '')
            suffix = item.get('suffix', '')
            try:
                output = self.render_children(item)
                if output is not None:
                    text = prefix + output + suffix
                    out.append(text)
                    self.getparent().cites.append(item)
            except VariableError:
                pass
        for item in bad_cites:
            callback_value = callback(item)
            out.append(callback_value or '{}?'.format(item.key))
        return self.format(self.wrap(self.join(out)))

    def sort_bibliography(self, citation_items):
        sort = self.getparent().find('cs:sort', self.nsmap)
        if sort is not None:
            citation_items = sort.sort(citation_items, self)
        return citation_items

    def render_bibliography(self, citation_items):
        output_items = []
        for item in citation_items:
            self.repressed = {}
            text = self.format(self.wrap(self.render_children(item)))
            if text is not None:
                output_items.append(text)
        return output_items


class FormatNumber(object):
    def _process(self, value, variable):
        page_range_delimiter = (self.get_term('page-range-delimiter').single
                                if variable.startswith('page') else None)
        range_delimiter = (page_range_delimiter
                           or self.unicode_character('EN DASH'))

        en_dash = unicodedata.lookup('EN DASH')
        def format_number_or_range(item):
            try:
                first, last = (number.strip() for number
                               in item.replace(en_dash, '-').split('-'))
            except ValueError:
                return self.format_number(item.strip())
            first = self.format_number(first)
            if variable == 'page-first':
                return first
            last = self.format_number(self._format_last_page(first, last)
                                      if variable == 'page' else last)
            return join((first, last), range_delimiter)

        amp_delimiter = ' ' + self.unicode_character('AMPERSAND') + ' '
        return join((join((format_number_or_range(item)
                           for item in comma_item.split('&')), amp_delimiter)
                     for comma_item in value.split(',')), delimiter=', ')

    def _format_last_page(self, first, last):
        def find_common(first, last):
            count = 0
            for count, (f, l) in enumerate(zip(first, last)):
                if f != l:
                    return count
            return count + 1

        range_format = self.get_root().get_option('page-range-format')
        common = find_common(first, last)
        if range_format == 'chicago':
            m = re.search(r'\d+', first)
            first_number = int(m.group())
            if first_number < 100 or first_number % 100 == 0:
                range_format = 'expanded'
            elif len(first) >= 4 and common < 2:
                range_format = 'expanded'
            elif first_number % 100 in range(1, 10):
                range_format = 'minimal'
            elif first_number % 100 in range(10, 100):
                range_format = 'minimal-two'
        if range_format in ('expanded', None):
            index = 0
        elif range_format == 'minimal':
            index = common
        elif range_format == 'minimal-two':
            index = min(common, len(first) - 2)
        return last[index:]

    def format_number(self, number):
        return str(number)


class Text(CitationStylesElement, FormatNumber, Formatted, Affixed, Quoted,
           TextCased, StrippedPeriods):
    generated_variables = ('year-suffix', 'citation-number')

    def calls_variable(self):
        if 'variable' in self.attrib:
            return self.get('variable') not in self.generated_variables
        elif 'macro' in self.attrib:
            return self.get_macro(self.get('macro')).calls_variable()
        else:
            return False

    def render(self, *args, **kwargs):
        text, language = self.process(*args, **kwargs)
        return self.markup(text, language)

    def process(self, item, context=None, **kwargs):
        if context is None:
            context = self

        try:
            language = item.reference.language[:2]
        except VariableError:
            language = self.get_root().get('default-locale', 'en')[:2]
        if 'variable' in self.attrib:
            text = self._variable(item, context)
        elif 'macro' in self.attrib:
            text = self.get_macro(self.get('macro')).render(item, context)
        elif 'term' in self.attrib:
            text = self._term(item)
        elif 'value' in self.attrib:
            text = String(self.preformat(self.get('value')))

        return text, language

    def _variable(self, item, context):
        variable = self.get('variable')
        repressed = context.get_layout().repressed
        if self.tag in repressed and variable in repressed[self.tag]:
            return None

        if self.get('form') == 'short':
            short_variable = variable + '-short'
            if short_variable.replace('-', '_') in item.reference:
                variable = short_variable

        if variable.startswith('page'):
            text = self._process(item.reference.page, variable)
        elif variable == 'citation-number':
            text = item.number
        elif variable == 'locator':
            en_dash = self.unicode_character('EN DASH')
            text = str(item.locator.identifier).replace('-', en_dash)
        else:
            text = item.reference[variable.replace('-', '_')]

        return text

    def _term(self, item):
        form = self.get('form', 'long')
        plural = self.get('plural', 'false').lower() == 'true'
        if form == 'long':
            form = None
        term = self.get_term(self.get('term'), form)

        if plural:
            text = term.multiple
        else:
            text = term.single

        return text

    def markup(self, text, language):
        if text:
            tmp = self.format(self.case(self.strip_periods(text), language))
            return self.wrap(self.quote(tmp))
        else:
            return None


class Date(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    def calls_variable(self):
        return True

    def is_locale_date(self):
        expr = './ancestor::cs:locale[1]'
        try:
            self.xpath_search(expr)[0]
            return True
        except IndexError:
            return False

    def render_single_date(self, date, show_parts=None, context=None):
        form = self.get('form')
        if context != self:
            parts = self.parts(date, show_parts, context)
        else:
            parts = self.parts(date, show_parts)
        if parts:
            style_context = context if self.is_locale_date() else self
            return style_context.join(parts)
        else:
            return None

    def render_date_range(self, date_range, show_parts=None, context=None):
        same_show_parts = []
        if date_range.end.is_nil():
            same = None
            diff_begin = self.render_single_date(date_range.begin, show_parts,
                                                 context)
            diff_end = ''
        else:
            if date_range.begin.year == date_range.end.year:
                show_parts.remove('year')
                same_show_parts.append('year')
                try:
                    if ('month' in show_parts and
                        date_range.begin.month == date_range.end.month):
                        show_parts.remove('month')
                        same_show_parts.append('month')
                        try:
                            if ('day' in show_parts and
                                date_range.begin.day == date_range.end.day):
                                show_parts.remove('day')
                                same_show_parts.append('day')
                        except AttributeError:
                            show_parts.remove('day')
                except AttributeError:
                    show_parts.remove('month')

            same = self.render_single_date(date_range.end, same_show_parts,
                                           context)
            diff_begin = self.render_single_date(date_range.begin, show_parts,
                                                 context)
            diff_end = self.render_single_date(date_range.end, show_parts,
                                               context)

        if not (diff_begin and diff_begin):
            return None

        diff = (diff_begin.rstrip() + self.unicode_character('EN DASH') +
                diff_end)
        if same:
            text = context.join([diff, same.rstrip()])
        else:
            text = diff

        return text

    def process(self, item, variable=None, show_parts=None, context=None,
                **kwargs):
        if variable is None:
            variable = self.get('variable')
        if show_parts is None:
            show_parts = ['year', 'month', 'day']
        if context is None:
            context = self

        form = self.get('form')
        date_parts = self.get('date-parts')
        if not self.is_locale_date() and form is not None:
            localized_date = self.get_date(form)
            if date_parts is not None:
                show_parts = date_parts.split('-')
            return localized_date.render(item, variable,
                                         show_parts=show_parts, context=self)
        else:
            date_or_range = item.reference[variable.replace('-', '_')]
            if not date_or_range:
                text = None
            elif isinstance(date_or_range, LiteralDate):
                text = date_or_range.text
            elif isinstance(date_or_range, DateRange):
                text = self.render_date_range(date_or_range, show_parts,
                                              context)
            else:
                text = self.render_single_date(date_or_range, show_parts,
                                               context)
            if text is not None:
                style_context = context if self.is_locale_date() else self
                return style_context.wrap(text)
            else:
                return None

    def parts(self, date, show_parts, context=None):
        output = []
        for part in self.iterchildren():
            if part.get('name') in show_parts:
                try:
                    part_text = part.render(date, context)
                    if part_text is not None:
                        output.append(part_text)
                except VariableError:
                    pass
        return output

    def markup(self, text):
        # TODO: fix
        return text


class Date_Part(CitationStylesElement, Formatted, Affixed, TextCased,
                StrippedPeriods):
    def process(self, date, context=None):
        name = self.get('name')
        range_delimiter = self.get('range-delimiter', '-')
        attrib = self.attrib

        if context is None:
            context = self
        try:
            expr = './cs:date-part[@name="{}"]'.format(name)
            attrib.update(dict(context.xpath_search(expr)[0].attrib))
        except (AttributeError, IndexError):
            pass

        if name == 'day':
            form = self.get('form', 'numeric')
            if (form == 'ordinal'
                and self.get_locale_option('limit-day-ordinals-to-day-1')
                    .lower() == 'true'
                and date.day > 1):
                form = 'numeric'

            if form == 'numeric':
                text = date.day
            elif form == 'numeric-leading-zeros':
                text = '{:02}'.format(date.day)
            elif form == 'ordinal':
                text = to_ordinal(date.day, context)
        elif name == 'month':
            form = self.get('form', 'long')
            strip_periods = self.get('form', False)
            try:
                index = date.month
                term = 'month'
            except VariableError:
                index = date.season
                term = 'season'

            if form == 'long':
                text = context.get_term('{}-{:02}'.format(term, index)).single
            elif form == 'short':
                term = context.get_term('{}-{:02}'.format(term, index), 'short')
                text = term.single
            else:
                assert term == 'month'
                if form == 'numeric':
                    text = '{}'.format(index)
                elif form == 'numeric-leading-zeros':
                    text = '{:02}'.format(index)
        elif name == 'year':
            form = self.get('form', 'long')
            if form == 'long':
                text = str(abs(date.year))
                if date.year < 0:
                    text += context.get_term('bc').single
                elif date.year < 1000:
                    text += context.get_term('ad').single
            elif form == 'short':
                text = str(date.year)[-2:]

        return text

    def markup(self, text):
        if text:
            return self.wrap(self.format(self.case(self.strip_periods(text))))
        else:
            return None


class Number(CitationStylesElement, FormatNumber, Formatted, Affixed, Displayed,
             TextCased, StrippedPeriods):
    def calls_variable(self):
        return True

    def process(self, item, context=None, **kwargs):
        variable = self.get('variable')
        if variable == 'locator':
            try:
                variable = item.locator.label
                value = item.locator.identifier
            except KeyError:
                return None
        elif variable == 'page-first':
            value = item.reference.page
        else:
            value = item.reference[variable]
        return self._process(value, variable)

    def format_number(self, number):
        form = self.get('form', 'numeric')
        try:
            number = int(number)
        except ValueError:
            return number
        if form == 'numeric':
            text = str(number)
        elif form == 'ordinal' or form == 'long-ordinal' and number > 10:
            text = to_ordinal(number, self)
        elif form == 'long-ordinal':
            text = self.get_term('long-ordinal-{:02}'.format(number)).single
        elif form == 'roman':
            text = romanize(number).lower()
        return text

    def markup(self, text):
        if text:
            return self.wrap(self.format(self.case(self.strip_periods(text))))
        else:
            return None


class Names(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    def calls_variable(self):
        return True

    def get_parent_delimiter(self, context=None):
        expr = './ancestor::*[self::cs:citation or self::cs:bibliography][1]'
        if context is None:
            context = self
        parent = context.xpath_search(expr)[0]
        return parent.get_option('names-delimiter')

    def substitute(self):
        expr = './cs:substitute[1]'
        try:
            result = self.xpath_search(expr)[0]
        except IndexError:
            result = None
        return result

    def process(self, item, names_context=None, context=None, **kwargs):
        if context is None:
            context = self
        if names_context is None:
            names_context = self

        roles = self.get('variable').split()
        try:
            ed_trans = (set(roles) == set(['editor', 'translator']) and
                        item.reference.editor == item.reference.translator and
                        self.get_term('editortranslator').getchildren())
            if ed_trans:
                roles = ['editor']
        except VariableError:
            ed_trans = False

        output = []
        for role in roles:
            if role in item.reference:
                name_elem = names_context.name
                if name_elem is None:
                    name_elem = Name()
                    names_context.insert(0, name_elem)
                text = name_elem.render(item, role, context=context, **kwargs)
                plural = len(item.reference[role]) > 1
                try:
                    if ed_trans:
                        role = 'editortranslator'
                    label_element = names_context.label
                    label = label_element.render(item, role, plural, **kwargs)
                    if label is not None:
                        if label_element is names_context.getchildren()[0]:
                            text = label + text
                        else:
                            text = text + label
                except AttributeError:
                    pass
                output.append(text)

        if output:
            try:
                total = sum(output)
            except TypeError:
                is_int = False
            else:
                is_int = isinstance(total, int)
            if is_int:
                text = str(total) if total > 0 else None
            else:
                text = self.join(output, self.get_parent_delimiter(context))
        else:
            substitute = self.substitute()
            if substitute is not None:
                text = substitute.render(item, context=context, **kwargs)

        try:
            return text
        except NameError:
            raise VariableError

    def markup(self, text):
        if text:
            return self.wrap(self.format(text))
        else:
            return None


class Name(CitationStylesElement, Formatted, Affixed, Delimited):
    def get_option(self, name, context=None, sort_options=None):
        try:
            value = sort_options[name]
        except (TypeError, KeyError):
            expr = ('./ancestor::*[self::cs:citation or '
                                  'self::cs:bibliography][1]')
            if context is None:
                context = self
            parent = context.xpath_search(expr)[0]
            if name in ('form', 'delimiter'):
                value = self.get(name, parent.get_option('name-' + name))
            else:
                value = self.get(name, parent.get_option(name))

        if name in ('initialize-with-hyphen', 'et-al-use-last'):
            value = value.lower() == 'true'
        elif name.startswith('et-al'):
            value = int(value)

        return value

    def et_al(self):
        expr = './following-sibling::cs:et-al[1]'
        try:
            result = self.xpath_search(expr)[0].render()
        except IndexError:
            result = self.get_term('et-al').single
        return result

    def process(self, item, variable, context=None, sort_options=None, **kwargs):
        def get_option(name):
            return self.get_option(name, context, sort_options)

        and_ = get_option('and')
        delimiter = get_option('delimiter')
        delimiter_precedes_et_al = get_option('delimiter-precedes-et-al')
        delimiter_precedes_last = get_option('delimiter-precedes-last')

        et_al_min = get_option('et-al-min')
        et_al_use_first = get_option('et-al-use-first')
        et_al_subseq_min = get_option('et-al-subsequent-min')
        et_al_subseq_use_first = get_option('et-al-subsequent-use-first')
        et_al_use_last = get_option('et-al-use-last')

        initialize_with = get_option('initialize-with')
        name_as_sort_order = get_option('name-as-sort-order')
        sort_separator = get_option('sort-separator')

        form = get_option('form')
        demote_ndp = get_option('demote-non-dropping-particle')

        def format_name_parts(given, family):
            for part in self.findall('cs:name-part', self.nsmap):
                given, family = part.format_part(given, family)
            return given, family

        names = item.reference.get(variable, [])

        if and_ == 'text':
            and_term = self.get_term('and').single
        elif and_ == 'symbol':
            and_term = self.preformat('&')

        et_al = self.et_al()
        output = []
        if form == 'count':
            count = min(len(names), et_al_use_first)
            output.append(count)
            return sum(output)
        else:
            et_al_truncate = (len(names) > 1 and et_al_min and
                              len(names) >= et_al_min)
            et_al_last = et_al_use_last and et_al_use_first <= et_al_min - 2
            if et_al_truncate:
                if et_al_last:
                    names = names[:et_al_use_first] + [names[-1]]
                else:
                    names = names[:et_al_use_first]
            for i, name in enumerate(names):
                given, family, dp, ndp, suffix = name.parts()

                if given is not None and initialize_with is not None:
                    given = self.initialize(given, initialize_with, context)

                if form == 'long':
                    if (name_as_sort_order == 'all' or
                            (name_as_sort_order == 'first' and i == 0)):
                        if demote_ndp in ('never', 'sort-only'):
                            family = ' '.join([n for n in (ndp, family) if n])
                            given = ' '.join([n for n in (given, dp) if n])
                        else:
                            given = ' '.join([n for n in (given, dp, ndp) if n])

                        given, family = format_name_parts(given, family)
                        order = family, given, suffix
                        text = sort_separator.join([n for n in order if n])
                    else:
                        family = ' '.join([n for n in (dp, ndp, family) if n])
                        given, family = format_name_parts(given, family)
                        order = given, family, suffix
                        text = ' '.join([n for n in order if n])
                elif form == 'short':
                    family = ' '.join([n for n in (ndp, family) if n])
                    given, family = format_name_parts(given, family)
                    text = family

                output.append(text)

            if et_al_truncate and et_al:
                if et_al_last:
                    ellipsis = self.unicode_character('horizontal ellipsis')
                    output[-1] = ellipsis + ' ' + output[-1]
                    text = self.join(output, delimiter)
                elif (delimiter_precedes_et_al == 'always' or
                      (delimiter_precedes_et_al == 'contextual' and
                     len(output) >= 2)):
                    output.append(et_al)
                    text = self.join(output, delimiter)
                else:
                    text = self.join(output, delimiter) + ' ' + et_al
            elif and_ is not None and len(output) > 1:
                text = self.join(output[:-1], ', ')
                if (delimiter_precedes_last == 'always' or
                    (delimiter_precedes_last == 'contextual' and
                     len(output) > 2)):
                        text = self.join([text, ''])
                else:
                    text += ' '
                text += '{} '.format(and_term) + output[-1]
            else:
                text = self.join(output, delimiter)

            return text

    def initialize(self, given, mark, context):
        if self.get_option('initialize-with-hyphen', context):
            hyphen_parts = given.split('-')
        else:
            hyphen_parts = [given.replace('-', ' ')]

        result_parts = []
        for hyphen_part in hyphen_parts:
            parts = hyphen_part.replace('.', ' ').split()
            hyphen_result = ''
            group = []
            for part in parts:
                if part[0].isupper():
                    group.append(part[0])
                else:
                    # don't initialize particles (which aren't capitalized)
                    hyphen_result += mark.join(group) + mark + ' ' + part + ' '
                    group = []
            hyphen_result += mark.join(group) + mark
            # remove double spaces
            hyphen_result = ' '.join(hyphen_result.split())
            result_parts.append(hyphen_result)
        return '-'.join(result_parts)

    def markup(self, text):
        if text:
            return self.wrap(self.format(text))
        else:
            return None


class Name_Part(CitationStylesElement, Formatted, Affixed, TextCased):
    def format_part(self, given, family):
        if self.get('name') == 'given':
            given = self.wrap(self.format(self.case(given)))
        elif self.get('name') == 'family':
            family = self.wrap(self.format(self.case(family)))
        return given, family


class Et_Al(CitationStylesElement, Formatted, Affixed):
    def process(self):
        variable = self.get('term', 'et-al')
        term = self.get_term('variable')
        return term

    def markup(self, text):
        if text:
            return self.wrap(self.format(text))
        else:
            return None


class Substitute(CitationStylesElement, Parent):
    def render(self, item, context=None, **kwargs):
        for child in self.getchildren():
            try:
                if isinstance(child, Names) and child.name is None:
                    names = self.xpath_search('./parent::cs:names[1]')[0]
                    text = child.render(item, names_context=names,
                                        context=context, **kwargs)
                else:
                    text = child.render(item, context=context, **kwargs)
            except VariableError:
                continue
            if text:
                self.add_to_repressed_list(child, context)
                break
        try:
            return text
        except NameError:
            return None

    def add_to_repressed_list(self, child, context):
        layout = context.get_layout()
        tag_list = layout.repressed.get(child.tag, [])
        tag_list.append(child.get('variable'))
        layout.repressed[child.tag] = tag_list


class Label(CitationStylesElement, Formatted, Affixed, StrippedPeriods,
            TextCased):
    def calls_variable(self):
        return self.get('variable') == 'locator'

    def process(self, item, variable=None, plural=None, context=None, **kwargs):
        if variable is None:
            variable = self.get('variable')
        form = self.get('form', 'long')
        plural_option = self.get('plural', 'contextual')
        if plural is None:
            plural = self._is_plural(item)

        if variable == 'locator' and item.has_locator:
            variable = item.locator.label

        if form == 'long':
            term = self.get_term(variable)
        else:
            term = self.get_term(variable, form)

        if (plural_option == 'contextual' and plural or
            plural_option == 'always'):
            text = term.multiple
        else:
            text = term.single

        return text

    def markup(self, text):
        if text:
            return self.wrap(self.format(self.case(self.strip_periods(text))))
        else:
            return None

    RE_MULTIPLE_NUMBERS = re.compile(r'\d+[^\d]+\d+')

    def _is_plural(self, item):
        variable = self.get('variable')
        if variable == 'locator':
            value = item.locator.identifier
        else:
            try:
                value = item.reference[variable.replace('-', '_')]
            except VariableError:
                return False

        if variable.startswith('number-of') and int(item[variable]) > 1:
            return True
        else:
            return self.RE_MULTIPLE_NUMBERS.search(str(value)) is not None


class Group(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    def calls_variable(self):
        return True

    def process(self, item, context=None, **kwargs):
        output = []
        variable_called = False
        variable_rendered = False
        for child in self.iterchildren():
            variable_called = variable_called or child.calls_variable()
            try:
                child_text = child.render(item, context=context, **kwargs)
                if child_text is not None:
                    output.append(child_text)
                    variable_rendered = (variable_rendered or
                                         child.calls_variable())
            except VariableError:
                pass
        output = [item for item in output if item is not None]
        success = not variable_called or (variable_called and variable_rendered)
        if output and success:
            return self.join(output)
        else:
            raise VariableError

    def markup(self, text):
        if text:
            return self.wrap(self.format(text))
        else:
            return None


class ConditionFailed(Exception):
    pass


class Choose(CitationStylesElement, Parent):
    def render(self, item, context=None, **kwargs):
        for child in self.getchildren():
            try:
                return child.render(item, context=context, **kwargs)
            except ConditionFailed:
                continue

        return None


class If(CitationStylesElement, Parent):
    def render(self, item, context=None, **kwargs):
        # TODO self.get('disambiguate')
        results = []
        if 'type' in self.attrib:
            results += self._type(item)
        if 'variable' in self.attrib:
            results += self._variable(item)
        if 'is-numeric' in self.attrib:
            results += self._is_numeric(item)
        if 'is-uncertain-date' in self.attrib:
            results += self._is_uncertain_date(item)
        if 'locator' in self.attrib:
            results += self._locator(item)
        if 'position' in self.attrib:
            results += self._position(item, context)

        # TODO: 'match' also applies to individual tests above!
        if self.get('match') == 'any':
            result = any(results)
        elif self.get('match') == 'none':
            result = not any(results)
        else:
            result = all(results)

        if not result:
            raise ConditionFailed

        return self.render_children(item, context=context, **kwargs)

    def _type(self, item):
        return [typ.lower() == item.reference.type
                for typ in self.get('type').split()]

    def _variable(self, item):
        variables = [var.replace('-', '_')
                     for var in self.get('variable').split()]
        output = []
        for variable in variables:
            if variable == 'locator':
                output.append('locator' in item)
            else:
                output.append(variable in item.reference)
        return output

    re_numeric = re.compile(r'^([A-Z]*\d+[A-Z]*)$', re.I)

    def _is_numeric(self, item):
        numeric_match = self.re_numeric.match
        return [var.replace('-', '_') in item.reference and
                numeric_match(str(item.reference[var.replace('-', '_')]))
                for var in self.get('is-numeric').split()]

    def _is_uncertain_date(self, item):
        result = []
        for date in self.get('is-uncertain-date').split():
            date_variable = date.replace('-', '_')
            try:
                circa = item.reference[date_variable].get('circa', False)
            except VariableError:
                circa = False
            result.append(circa)
        return result

    def _locator(self, item):
        return [var.replace('-', ' ') == item.locator.label
                for var in self.get('locator').split()]

    def _position(self, item, context):
        if context is None:
            context = self
        if context.xpath_search('./ancestor::*[self::cs:bibliography]'):
            return [False]
        # citation node
        cites = context.get_layout().getparent().cites
        last_cite = cites[-1] if cites else None
        already_cited = item.key in (cite.key for cite in cites)
        possibly_ibid = (already_cited
                         and item.key == last_cite.key
                         and (item.citation is last_cite.citation
                              or len(last_cite.citation.cites) == 1))
        results = []
        for position in self.get('position').split():
            result = False
            if position == 'first':
                result = not already_cited
            elif position == 'subsequent':
                result = already_cited
            elif possibly_ibid and position == 'ibid':
                result = item.has_locator or not last_cite.has_locator
            elif possibly_ibid and position == 'ibid-with-locator':
                result = (item.has_locator and not last_cite.has_locator
                          or (item.has_locator and last_cite.has_locator
                              and item.locator != last_cite.locator))
            elif already_cited and position == 'near-note':
                max_distance = self.get_root().get_option('near-note-distance')
                citations = 1
                last_citation = None
                for cite in reversed(cites):
                    if item.key == cite.key and citations <= max_distance:
                        result = True
                        break
                    elif cite.citation is not last_citation:
                        citations += 1
                        last_citation = cite.citation
            results.append(result)
        return results


class Else_If(If, CitationStylesElement):
    pass


class Else(CitationStylesElement, Parent):
    def render(self, item, context=None, **kwargs):
        return self.render_children(item, context=context, **kwargs)


# utility functions

def to_ordinal(number, context):
    number = str(number)
    last_digit = int(number[-1])
    if last_digit in (1, 2, 3) and not (len(number) > 1 and number[-2] == '1'):
        ordinal_term = 'ordinal-{:02}'.format(last_digit)
    else:
        ordinal_term = 'ordinal-04'
    return number + context.get_term(ordinal_term).single


def romanize(n):
    # by Kay Schluehr - from http://billmill.org/python_roman.html
    numerals = (('M', 1000), ('CM', 900), ('D', 500), ('CD', 400),
                ('C', 100),('XC', 90),('L', 50),('XL', 40), ('X', 10),
                ('IX', 9), ('V', 5), ('IV', 4), ('I', 1))
    roman = []
    for ltr, num in numerals:
        (k, n) = divmod(n, num)
        roman.append(ltr * k)
    return ''.join(roman)
