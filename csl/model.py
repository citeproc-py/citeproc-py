
import re

from html.entities import codepoint2name, name2codepoint

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
                        'delimiter-precedes-last': 'contextual',
                        'et-al-min': 0,
                        'et-al-use-first': 0,
                        'et-al-subsequent-min': 0,
                        'et-al-subsequent-use-first': 0,
                        'initialize-with': None,
                        'name-as-sort-order': None,
                        'sort-separator': ', ',

                        'name-form': 'long',
                        'name-delimiter': ', ',
                        'names-delimiter': ', '}

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
        return self.xpath_search('./ancestor::cs:layout[1]')[0]

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

    def render(self, reference):
        return self.layout.render_bibliography(reference)


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
        if self.get('quotes', False):
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


# Locale

class Term(CitationStylesElement):
    @property
    def single(self):
        try:
            return self.find('cs:single', self.nsmap).text
        except AttributeError:
            return self.text

    @property
    def multiple(self):
        try:
            return self.find('cs:multiple', self.nsmap).text
        except AttributeError:
            return self.text


# Rendering elements

class Parent(object):
    def render_children(self, item, *args, **kwargs):
        output = []
        for child in self.iterchildren():
            output.append(child.render(item, *args, **kwargs))
        return output


class Sort(CitationStylesElement):
    def sort(self, items):
        raise NotImplementedError
        sort_keys = []
        for key in self.key:
            try:
                descending = key.attrib['sort'] == 'descending'
            except KeyError:
                descending = False
            # names-min, names-use-first
            sort_keys.append((key.variable, descending))


class Macro(CitationStylesElement, Parent):
    def render(self, item, context):
        # TODO: replace explicit context passing with xpath search for macro
        #       ancestor
        output = self.render_children(item, context=context)
        return ''.join([item for item in output if item is not None])


class Layout(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    def render_citation(self, citation):
        # TODO: formatting
        self.repressed = {}
        out = []
        for item in citation.items:
            prefix = item.get('prefix', '')
            suffix = item.get('suffix', '')
            output = [item for item in self.render_children(item)
                      if item is not None]
            text = prefix + ''.join(output) + suffix
            out.append(text)
            self.repressed = {}
        return self.format(self.wrap(self.join(out)))

    def render_bibliography(self, references):
        from ...bibliography import CitationItem
        self.repressed = {}
        output = ['<div class="csl-bib-body">']
        items = [CitationItem(reference) for reference in references]
        for item in items:
            out = [item for item in self.render_children(item)
                   if item is not None]
            text = '  <div class="csl-entry">'
            text += self.wrap(''.join(out))
            text += '</div>'
            output.append(text)
            self.repressed = {}
        output.append('</div>')
        return '\n'.join(output)


class Text(CitationStylesElement, Formatted, Affixed, TextCased,
           StrippedPeriods):
    def render(self, item, context=None):
        if context is None:
            context = self

        if 'variable' in self.attrib:
            variable = self.get('variable')
            repressed = context.get_layout().repressed
            if self.tag in repressed and variable in repressed[self.tag]:
                return None

            short = self.get('form') == 'short' # TODO: do something with this
            try:
                text = item.reference[variable.replace('-', '_')]
            except KeyError:
                if variable == 'page-first' and 'page' in item.reference:
                    page = item.reference['page']
                    text = Number.re_range.match(page).group(1)
                else:
                    return None
        elif 'macro' in self.attrib:
            text = self.get_macro(self.get('macro')).render(item, context)
        elif 'term' in self.attrib:
            form = self.get('form', 'long')
            plural = self.get('plural', 'false').lower() == 'true'
            if form == 'long':
                form = None
            term = self.get_term(self.get('term'), form)

            if plural:
                text = term.multiple
            else:
                text = term.single
        elif 'value' in self.attrib:
            text = self.get('value')

        # TODO: display, formatting, quotes, strip-periods, text-case
        return self.wrap(self.case(self.strip_periods(text)))


class Date(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
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
        if self.is_locale_date():
            return context.join(parts)
        else:
            return self.join(parts)

    def render_date_range(self, date_range, show_parts=None, context=None):
        same_show_parts = []

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

        same = self.render_single_date(date_range.end, same_show_parts, context)
        diff_begin = self.render_single_date(date_range.begin, show_parts,
                                             context)
        diff_end = self.render_single_date(date_range.end, show_parts, context)

        diff = chr(name2codepoint['ndash']).join([diff_begin.rstrip(),
                                                  diff_end])

        return context.join([diff, same.rstrip()])

    def render(self, item, variable=None, show_parts=None, context=None):
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
            if self.is_locale_date():
                return context.wrap(text)
            else:
                return self.wrap(text)

    def parts(self, date, show_parts, context=None):
        output = []
        for part in self.iterchildren():
            if part.get('name') in show_parts:
                output.append(part.render(date, context))
        return output


class Date_Part(CitationStylesElement, Formatted, Affixed, TextCased,
                StrippedPeriods):
    def render(self, date, context=None):
        name = self.get('name')
        range_delimiter = self.get('range-delimiter', '-')
        attrib = self.attrib
        if name not in date:
            return None

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
             StrippedPeriods):
    re_numeric = re.compile(r'^(\d+).*')
    re_range = re.compile(r'^(\d+)\s*-\s*(\d+)$')

    def is_plural(self, item):
        variable = self.get('variable')
        if variable.startswith('number-of') and int(item[variable]) > 1:
            return True
        elif (variable == 'locator'
              and self.re_range.match(item.locator.identifier)):
            return True
        else:
            return False

    def render(self, item, context=None):
        form = self.get('form', 'numeric')
        try:
            variable = self.get('variable')
            if variable == 'locator':
                variable = item.locator.identifier
            else:
                variable = item.reference[variable]
        except KeyError:
            return None

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

    def render(self, item, context=None):
        # if this instance substitutes another
        if context is None:
            names_context = context = self
        elif isinstance(context, Names):
            names_context = context
        else:
            names_context = self

        output = []
        for role in self.get('variable').split(' '):
            if role in item.reference:
                name_elem = names_context.name
                if name_elem is None:
                    name_elem = Name()
                    names_context.insert(0, name_elem)
                text = name_elem.render(item, role, context=context)
                plural = len(item.reference[role]) > 1
                try:
                    text += names_context.label.render(item, role, plural)
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
                text = substitute.render(item, context)
        try:
            return self.wrap(self.format(text))
        except NameError:
            return None


class Name(CitationStylesElement, Formatted, Affixed, Delimited):
    def get_option(self, name, context=None):
        expr = './ancestor::*[self::cs:citation or self::cs:bibliography][1]'
        if context is None:
            context = self
        parent = context.xpath_search(expr)[0]
        if name in ('form', 'delimiter'):
            value = self.get(name, parent.get_option('name-' + name))
        else:
            value = self.get(name, parent.get_option(name))
            if name.startswith('et-al'):
                value = int(value)
            elif name in ('initialize-with-hyphen', ):
                value = value.lower() == 'true'
        return value

    def et_al(self):
        expr = './following-sibling::cs:et-al[1]'
        try:
            result = self.xpath_search(expr)[0].render()
        except IndexError:
            result = self.get_term('et-al').single
        return result

    def render(self, item, variable, context=None):
        and_ = self.get_option('and', context)
        delimiter_precedes_last = self.get_option('delimiter-precedes-last',
                                                  context)

        et_al_min = self.get_option('et-al-min', context)
        et_al_use_first = self.get_option('et-al-use-first', context)
        et_al_subseq_min = self.get_option('et-al-subsequent-min', context)
        et_al_subseq_use_first = self.get_option('et-al-subsequent-use-first',
                                                 context)

        initialize_with = self.get_option('initialize-with', context)
        name_as_sort_order = self.get_option('name-as-sort-order', context)
        sort_separator = self.get_option('sort-separator', context)

        form = self.get('form', 'long')
        demote_ndp = self.get_option('demote-non-dropping-particle', context)

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
            if et_al_truncate:
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
                    given, family = format_name_parts(given, family)
                    text = family

                output.append(text)
            if et_al_truncate and et_al:
                if (delimiter_precedes_last == 'always' or
                    (delimiter_precedes_last == 'contextual' and
                     len(output) >= 2)):
                    output.append(et_al)
                    text = self.join(output, ', ')
                else:
                    text = self.join(output, ', ') + ' ' + et_al
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
                text = self.join(output, ', ')
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


class Substitute(CitationStylesElement):
    def render(self, item, context=None):
        for child in self.getchildren():
            if isinstance(child, Names) and child.name is None:
                names = self.xpath_search('./parent::cs:names[1]')[0]
                text = child.render(item, context=names)
            else:
                text = child.render(item, context=context)
            if text:
                self.add_to_repressed_list(child, context)
                break
        return text

    def add_to_repressed_list(self, child, context):
        layout = context.get_layout()
        tag_list = layout.repressed.get(child.tag, [])
        tag_list.append(child.get('variable'))
        layout.repressed[child.tag] = tag_list


class Label(CitationStylesElement, Formatted, Affixed, StrippedPeriods,
            TextCased):
    def render(self, item, variable=None, plural=None, context=None):
        if variable is None:
            variable = self.get('variable')
        if plural is None:
            try:
                number = self.xpath_search('./parent::*/cs:number[1]')[0]
                plural = number.is_plural(item)
            except IndexError:
                plural = False
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
    # TODO: Note that cs:group implicitly acts as a conditional: cs:group and
    # its child elements are suppressed if
    #  a) at least one rendering element in cs:group calls a variable (either
    #     directly or via a macro), and
    #  b) all variables that are called are empty. This behavior exists to
    #     accommodate descriptive cs:text elements.
    def render(self, item, context=None):
        return self.wrap(self.join(self.render_children(item, context=context)))


class ConditionFailed(Exception):
    pass


class Choose(CitationStylesElement):
    def render(self, item, context=None):
        try:
            return self.find('cs:if', self.nsmap).render(item, context)
        except ConditionFailed:
            pass

        try:
            for else_if in self.find('cs:else-if', self.nsmap):
                try:
                    return else_if.render(item, context)
                except ConditionFailed:
                    continue
        except TypeError:
            pass

        try:
            return self.find('cs:else', self.nsmap).render(item, context)
        except (AttributeError, ConditionFailed):
            return None


class If(CitationStylesElement, Parent):
    def render(self, item, context=None):
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

        output = self.render_children(item, context=context)
        return ''.join([item for item in output if item is not None])

    def _type(self, item):
        return [typ.lower() == item.reference.type
                for typ in self.get('type').split()]

    def _variable(self, item):
        return [var in item.reference for var in self.get('variable').split()]

    def _is_numeric(self, item):
        return [var in item.reference and
                Number.re_numeric.match(str(item.reference[var]))
                for var in self.get('is-numeric').split()]

    def _is_uncertain_date(self, item):
        dates = self.get('is-uncertain-date').split()
        return [item.reference[date].get('circa', False) for date in dates]

    def _locator(self, item):
        raise NotImplementedError

    def _position(self, item):
        raise NotImplementedError


class Else_If(If):
    pass


class Else(CitationStylesElement, Parent):
    def render(self, item, context=None):
        output = self.render_children(item, context=context)
        return ''.join([item for item in output if item is not None])


# utility functions

def to_ordinal(number, context):
    number = str(number)
    if number.endswith('1') and not number.endswith('11'):
        ordinal_term = 'ordinal-01'
    elif number.endswith('2') and not number.endswith('12'):
        ordinal_term = 'ordinal-02'
    elif number.endswith('3') and not number.endswith('13'):
        ordinal_term = 'ordinal-03'
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
