
import re

from html.entities import codepoint2name, name2codepoint
from operator import itemgetter

from lxml import etree


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

    def get_option(self, name):
        return self.get(name, __class__._default_options[name])

    def get_citation(self):
        return self.get_root().citation

    def get_bibliography(self):
        return self.get_root().bibliography

    def get_macro(self, name):
        expression = "cs:macro[@name='{}'][1]".format(name)
        return self.get_root().xpath_search(expression)[0]

    def get_layout(self):
        return self.xpath_search('./ancestor-or-self::cs:layout[1]')[0]

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
    def set_locale_list(self, system_locale):
        from . import CitationStylesLocale

        def search_locale(locale):
            return self.xpath_search('./cs:locale[@xml:lang="{}"]'
                                     .format(locale))[0]

        self.locales = []
        try:
            self.locales.append(search_locale(system_locale))
        except IndexError:
            pass

        language = system_locale.split('-')[0]
        try:
            self.locales.append(search_locale(language))
        except IndexError:
            pass

        try:
            expr = './cs:locale[not(@xml:lang)]'
            self.locales.append(self.xpath_search(expr)[0])
        except IndexError:
            pass

        self.locales.append(CitationStylesLocale(system_locale).root)
        if system_locale != 'en-US':
            # TODO: add other locales with same locale
            self.locales.append(CitationStylesLocale('en-US').root)


class Locale(CitationStylesElement):
    _default_options = {'punctuation-in-quote': 'false'}

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
        return options.get(name, __class__._default_options[name])


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

    def render(self, citation):
        return self.layout.render_citation(citation)


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
        text = self.font_style(string)
        text = self.font_variant(text)
        text = self.font_weight(text)
        text = self.text_decoration(text)
        text = self.vertical_align(text)
        return text

    def font_style(self, text):
        font_style = self.get('font-style', 'normal')
        if font_style == 'normal':
            wrappers = '', ''
        elif font_style == 'italic':
            wrappers = '<i>', '</i>'
        elif font_style == 'oblique':
            wrappers = '<i>', '</i>'
        return '{1}{0}{2}'.format(text, *wrappers)

    def font_variant(self, text):
        font_variant = self.get('font-variant', 'normal')
        if font_variant == 'normal':
            wrappers = '', ''
        elif font_variant == 'small-caps':
            wrappers = '<span style="font-variant:small-caps;">', '</span>'
        return '{1}{0}{2}'.format(text, *wrappers)

    def font_weight(self, text):
        font_weight = self.get('font-weight', 'normal')
        if font_weight == 'normal':
            wrappers = '', ''
        elif font_weight == 'bold':
            wrappers = '<b>', '</b>'
        elif font_weight == 'light':
            wrappers = '<l>', '</l>'
        return '{1}{0}{2}'.format(text, *wrappers)

    def text_decoration(self, text):
        text_decoration = self.get('text-decoration', 'none')
        if text_decoration == 'none':
            wrappers = '', ''
        elif text_decoration == 'underline':
            wrappers = '<u>', '</u>'
        return '{1}{0}{2}'.format(text, *wrappers)

    def vertical_align(self, text):
        vertical_align = self.get('vertical-align', 'baseline')
        if vertical_align == 'baseline':
            wrappers = '', ''
        elif vertical_align == 'sup':
            wrappers = '<sup>', '</sup>'
        elif vertical_align == 'sub':
            wrappers = '<sub>', '</sub>'
        return '{1}{0}{2}'.format(text, *wrappers)


class Affixed(object):
    def wrap(self, string):
        prefix = self.get('prefix', '')
        suffix = self.get('suffix', '')
        return prefix + string + suffix


class Delimited(object):
    def join(self, strings, default_delimiter=''):
        delimiter = self.get('delimiter', default_delimiter)
        return delimiter.join([item for item in strings if item is not None])


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
    def case(self, text):
        text_case = self.get('text-case')
        if text_case is not None:
            if text_case == 'lowercase':
                text = text.lower()
            elif text_case == 'uppercase':
                text = text.upper()
            elif text_case == 'capitalize-first':
                text = text.capitalize()
            elif text_case == 'capitalize-all':
                text = text.title()
            elif text_case == 'title':
                text = text.title()
            elif text_case == 'sentence':
                text = text.capitalize()
        return text


# Tests

class PluralTest(object):
    def is_plural(self, item):
        from ...bibliography import VariableError
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
            return Number.re_range.match(str(value))


# Locale elements

class Term(CitationStylesElement):
    @property
    def single(self):
        try:
            return self.find('cs:single', self.nsmap).text
        except AttributeError:
            return self.text or ''

    @property
    def multiple(self):
        try:
            return self.find('cs:multiple', self.nsmap).text
        except AttributeError:
            return self.text or ''


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
                            left_key = left_key.lower()
                            right_key = right_key.lower()
                        except AttributeError:
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
        from ..csl import NAMES, DATES, NUMBERS
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
                sort_keys = [item.reference.get(variable) for item in items]
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

    def render_children(self, item, **kwargs):
        from ...bibliography import VariableError
        output = []
        for child in self.iterchildren():
            try:
                text = child.render(item, **kwargs)
                if text is not None:
                    output.append(text)
            except VariableError:
                pass
        if output:
            return ''.join(output)
        else:
            return None


class Macro(CitationStylesElement, Parent):
    def render(self, item, context=None, sort_options=None):
        return self.render_children(item, context=context,
                                    sort_options=sort_options)


class Layout(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    def render_citation(self, citation):
        from ...bibliography import VariableError
        # first sort citation items according to bibliography order
        bibliography = citation.cites[0]._bibliography
        citation.cites.sort(key=lambda x: bibliography.keys.index(x.key))
        # sort using citation/sort element
        if self.getparent().sort is not None:
            citation.cites = self.getparent().sort.sort(citation.cites, self)
        out = []
        for item in citation.cites:
            self.repressed = {}
            prefix = item.get('prefix', '')
            suffix = item.get('suffix', '')
            try:
                output = self.render_children(item)
                if output is not None:
                    text = prefix + output + suffix
                    out.append(text)
            except VariableError:
                pass
        return self.format(self.wrap(self.join(out)))

    def sort_bibliography(self, citation_items):
        sort = self.getparent().find('cs:sort', self.nsmap)
        if sort is not None:
            citation_items = sort.sort(citation_items, self)
        return citation_items

    def render_bibliography(self, citation_items):
        item_prefix = '  <div class="csl-entry">'
        item_suffix = '</div>'
        output = ['<div class="csl-bib-body">']
        for item in citation_items:
            self.repressed = {}
            text = self.render_children(item)
            if text is not None:
                text = item_prefix + self.wrap(self.format(text)) + item_suffix
                output.append(text)
        output.append('</div>')
        return '\n'.join(output)


class Text(CitationStylesElement, Formatted, Affixed, Quoted, TextCased,
           StrippedPeriods, PluralTest):
    generated_variables = ('year-suffix', 'citation-number')

    def calls_variable(self):
        if 'variable' in self.attrib:
            return self.get('variable') not in self.generated_variables
        elif 'macro' in self.attrib:
            return self.get_macro(self.get('macro')).calls_variable()
        else:
            return False

    def render(self, item, context=None, **kwargs):
        if context is None:
            context = self

        if 'variable' in self.attrib:
            text = self._variable(item, context)
        elif 'macro' in self.attrib:
            text = self.get_macro(self.get('macro')).render(item, context)
        elif 'term' in self.attrib:
            text = self._term(item)
        elif 'value' in self.attrib:
            text = self.get('value')

        if text:
            tmp = self.format(self.case(self.strip_periods(text)))
            return self.wrap(self.quote(tmp))
        else:
            return None

    def _variable(self, item, context):
        variable = self.get('variable')
        repressed = context.get_layout().repressed
        if self.tag in repressed and variable in repressed[self.tag]:
            return None

        if self.get('form') == 'short':
            short_variable = variable + '-short'
            if short_variable.replace('-', '_') in item.reference:
                variable = short_variable

        if variable == 'citation-number':
            text = item.number
        elif variable == 'locator':
            text = str(item.locator.identifier)
        elif variable == 'page-first' and variable not in item.reference:
            page = item.reference.page
            text = Number.re_range.match(page).group(1)
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
        date_parts = self.get('date-parts')

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

        diff = chr(name2codepoint['ndash']).join([diff_begin.rstrip(),
                                                  diff_end])
        if same:
            text = context.join([diff, same.rstrip()])
        else:
            text = diff

        return text


    def render(self, item, variable=None, show_parts=None, context=None,
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
            from ...bibliography import DateRange
            date_or_range = item.reference[variable.replace('-', '_')]
            if isinstance(date_or_range, DateRange):
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
        from ...bibliography import VariableError
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


class Date_Part(CitationStylesElement, Formatted, Affixed, TextCased,
                StrippedPeriods):
    def render(self, date, context=None):
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
            if form == 'numeric':
                text = date.day
            elif form == 'numeric-leading-zeros':
                text = '{:02}'.format(date.day)
            elif form == 'ordinal':
                text = to_ordinal(number, context)
        elif name == 'month':
            form = self.get('form', 'long')
            strip_periods = self.get('form', False)
            if form == 'long':
                text = context.get_term('month-{:02}'.format(date.month)).single
            elif form == 'short':
                term = context.get_term('month-{:02}'.format(date.month), 'short')
                text = term.single
            elif form == 'numeric':
                text = '{}'.format(date.month)
            elif form == 'numeric-leading-zeros':
                text = '{:02}'.format(date.month)
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

        return self.wrap(self.format(self.case(self.strip_periods(text))))


class Number(CitationStylesElement, Formatted, Affixed, Displayed, TextCased,
             StrippedPeriods, PluralTest):
    re_numeric = re.compile(r'^(\d+).*')
    re_range = re.compile(r'^(\d+)\s*-\s*(\d+)$')

    def calls_variable(self):
        return True

    def render(self, item, context=None, **kwargs):
        form = self.get('form', 'numeric')
        variable = self.get('variable')
        if variable == 'locator':
            try:
                variable = item.locator.identifier
            except KeyError:
                return None
        else:
            variable = item.reference[variable]

        try:
            first, last = map(int, self.re_range.match(variable).groups())
            first = self.format_number(first, form)
            last = self.format_number(last, form)
            text = first + chr(name2codepoint['ndash']) + last
        except AttributeError:
            try:
                number = int(self.re_numeric.match(variable).group(1))
                text = self.format_number(number, form)
            except AttributeError:
                text = variable
        except TypeError:
            text = str(variable)

        return self.wrap(self.format(self.case(self.strip_periods(text))))

    def format_number(self, number, form):
        if form == 'numeric':
            text = str(number)
        elif form == 'ordinal' or form == 'long-ordinal' and number > 10:
            text = to_ordinal(number, self)
        elif form == 'long-ordinal':
            text = self.get_term('long-ordinal-{:02}'.format(number)).single
        elif form == 'roman':
            text = romanize(number).lower()

        return text


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

    def render(self, item, names_context=None, context=None, **kwargs):
        from ...bibliography import VariableError
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
            if isinstance(output[0], int):
                total = sum(output)
                text = str(total) if total > 0 else ''
            else:
                text = self.join(output, self.get_parent_delimiter(context))
        else:
            substitute = self.substitute()
            if substitute is not None:
                text = substitute.render(item, context=context, **kwargs)

        try:
            if text is not None:
                return self.wrap(self.format(text))
            else:
                return None
        except NameError:
            from ...bibliography import VariableError
            raise VariableError


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

    def render(self, item, variable, context=None, sort_options=None, **kwargs):
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
            and_term = '&' + codepoint2name[ord('&')] + ';'

        et_al = self.et_al()
        output = []
        if form == 'count':
            count = min(len(names), et_al_use_first)
            output.append(count)
            return sum(output)
        else:
            et_al_truncate = et_al_min and len(names) >= et_al_min
            et_al_last = et_al_use_last and et_al_use_first <= et_al_min - 2
            if et_al_truncate:
                if et_al_last:
                    names = names[:et_al_use_first] + [names[-1]]
                else:
                    names = names[:et_al_use_first]
            for i, name in enumerate(names):
                given, family, dp, ndp, suffix = name.parts()

                if initialize_with is not None:
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
                    ellipsis = chr(name2codepoint['hellip'])
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

            return self.wrap(self.format(text))

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


class Name_Part(CitationStylesElement, Formatted, Affixed, TextCased):
    def format_part(self, given, family):
        if self.get('name') == 'given':
            given = self.wrap(self.format(self.case(given)))
        elif self.get('name') == 'family':
            family = self.wrap(self.format(self.case(family)))
        return given, family


class Et_Al(CitationStylesElement, Formatted, Affixed):
    def render(self):
        variable = self.get('term', 'et-al')
        term = self.get_term('variable')
        if term:
            return self.wrap(self.format(text))
        else:
            return None


class Substitute(CitationStylesElement, Parent):
    def render(self, item, context=None, **kwargs):
        from ...bibliography import VariableError
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

    def plural(self, item):
        expr = './parent::*/*[self::cs:text or self::cs:number]'
        try:
            element = self.xpath_search(expr)[0]
            return element.is_plural(item)
        except IndexError:
            return False

    def render(self, item, variable=None, plural=None, context=None, **kwargs):
        if variable is None:
            variable = self.get('variable')
        if plural is None:
            plural = self.plural(item)
        form = self.get('form', 'long')
        plural_option = self.get('plural', 'contextual')

        if variable == 'locator':
            try:
                variable = item.locator.label
            except KeyError:
                return None

        if form == 'long':
            term = self.get_term(variable)
        else:
            term = self.get_term(variable, form)

        if (plural_option == 'contextual' and plural or
            plural_option == 'always'):
            text = term.multiple
        else:
            text = term.single

        if text is None:
            return None
        else:
            return self.wrap(self.format(self.case(self.strip_periods(text))))


class Group(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    def render(self, item, context=None, **kwargs):
        from ...bibliography import VariableError
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
            return self.wrap(self.format(self.join(output)))
        else:
            raise VariableError


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
            results += self._position(item)

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

    def _is_numeric(self, item):
        numeric_match = Number.re_numeric.match
        return [var.replace('-', '_') in item.reference and
                numeric_match(str(item.reference[var.replace('-', '_')]))
                for var in self.get('is-numeric').split()]

    def _is_uncertain_date(self, item):
        dates = self.get('is-uncertain-date').split()
        return [item.reference[date.replace('-', '_')].get('circa', False)
                for date in dates]

    def _locator(self, item):
        return [var.replace('-', ' ') == item.locator.label
                for var in self.get('locator').split()]

    def _position(self, item):
        raise NotImplementedError


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


def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K
